"""
Document Processing Service - LocalAgentCore Integration
======================================================

This module provides the integration layer between LocalAgentCore package
and the FastAPI backend, handling document analysis workflows, result storage,
and API response formatting.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import tempfile
import mimetypes
from dataclasses import asdict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from fastapi import HTTPException
import aiofiles

# Import LocalAgentCore modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "packages"))

from LocalAgentCore import DocumentAnalyzer, ContradictionDetector, InstrumentClassifier, RemedyCompiler
from LocalAgentCore.base import AnalysisResult, LegalIssue, Remedy, Classification, DocumentType
from LocalAgentCore.exceptions import LocalAgentCoreError, AnalysisError

from .database_enhanced import DocumentRecord, AnalysisResultRecord, LegalIssueRecord, RemedyRecord
from .api_models import DocumentAnalysisRequest, DocumentAnalysisResponse, DocumentProcessingStatus


class DocumentProcessingService:
    """
    Service for processing documents using LocalAgentCore
    
    Handles:
    - Document upload and validation
    - Analysis workflow orchestration  
    - Result storage and retrieval
    - Error handling and status management
    - Caching and performance optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize LocalAgentCore components
        self._analyzer_config = {
            "enable_classification": True,
            "enable_contradiction_detection": True,
            "enable_remedy_generation": True,
            "parallel_processing": True,
            "enable_caching": True,
            **self.config.get("localagent_config", {})
        }
        
        self.document_analyzer = DocumentAnalyzer(self._analyzer_config)
        
        # File storage configuration
        self.upload_directory = Path(self.config.get("upload_directory", "/tmp/document_uploads"))
        self.upload_directory.mkdir(exist_ok=True)
        
        # Processing limits
        self.max_file_size = self.config.get("max_file_size", 10 * 1024 * 1024)  # 10MB
        self.supported_formats = self.config.get("supported_formats", [
            "text/plain", "application/pdf", "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ])
        
        # Performance settings
        self.processing_timeout = self.config.get("processing_timeout", 300)  # 5 minutes
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour
    
    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        user_id: str,
        db: AsyncSession,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentRecord:
        """
        Upload and validate document for processing
        
        Args:
            file_content: Raw file content bytes
            filename: Original filename
            content_type: MIME type
            user_id: ID of uploading user
            db: Database session
            metadata: Optional document metadata
            
        Returns:
            DocumentRecord: Created database record
        """
        try:
            # Validate file
            await self._validate_file(file_content, filename, content_type)
            
            # Extract text content
            text_content = await self._extract_text_content(file_content, content_type, filename)
            
            # Save file to storage
            file_path = await self._save_file(file_content, filename, user_id)
            
            # Create database record
            document = DocumentRecord(
                filename=filename,
                content_type=content_type,
                file_size=len(file_content),
                file_path=str(file_path),
                text_content=text_content,
                uploaded_by=user_id,
                upload_timestamp=datetime.utcnow(),
                processing_status=DocumentProcessingStatus.UPLOADED,
                metadata_json=json.dumps(metadata) if metadata else None
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            return document
            
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Document upload failed: {str(e)}"
            )
    
    async def process_document(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> AnalysisResultRecord:
        """
        Process document using LocalAgentCore analysis
        
        Args:
            document_id: Database document ID
            user_id: ID of requesting user
            db: Database session
            analysis_options: Optional analysis configuration
            
        Returns:
            AnalysisResultRecord: Analysis results database record
        """
        try:
            # Get document record
            result = await db.execute(
                select(DocumentRecord).where(DocumentRecord.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Verify user permissions
            if document.uploaded_by != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Check if already processing
            if document.processing_status == DocumentProcessingStatus.PROCESSING:
                raise HTTPException(status_code=409, detail="Document already processing")
            
            # Update status to processing
            await db.execute(
                update(DocumentRecord)
                .where(DocumentRecord.id == document_id)
                .values(processing_status=DocumentProcessingStatus.PROCESSING)
            )
            await db.commit()
            
            try:
                # Prepare analysis metadata
                metadata = {
                    "document_id": document_id,
                    "filename": document.filename,
                    "content_type": document.content_type,
                    "user_id": user_id,
                    **(json.loads(document.metadata_json) if document.metadata_json else {}),
                    **(analysis_options or {})
                }
                
                # Run analysis with timeout
                analysis_result = await asyncio.wait_for(
                    self.document_analyzer.analyze(document.text_content, metadata),
                    timeout=self.processing_timeout
                )
                
                # Store analysis results
                analysis_record = await self._store_analysis_results(
                    document_id, analysis_result, user_id, db
                )
                
                # Update document status to completed
                await db.execute(
                    update(DocumentRecord)
                    .where(DocumentRecord.id == document_id)
                    .values(
                        processing_status=DocumentProcessingStatus.COMPLETED,
                        last_analyzed=datetime.utcnow()
                    )
                )
                await db.commit()
                
                return analysis_record
                
            except asyncio.TimeoutError:
                # Update status to failed
                await db.execute(
                    update(DocumentRecord)
                    .where(DocumentRecord.id == document_id)
                    .values(
                        processing_status=DocumentProcessingStatus.FAILED,
                        error_message="Processing timeout exceeded"
                    )
                )
                await db.commit()
                
                raise HTTPException(
                    status_code=408,
                    detail="Document processing timeout"
                )
                
            except Exception as e:
                # Update status to failed
                error_message = f"Analysis failed: {str(e)}"
                await db.execute(
                    update(DocumentRecord)
                    .where(DocumentRecord.id == document_id)
                    .values(
                        processing_status=DocumentProcessingStatus.FAILED,
                        error_message=error_message
                    )
                )
                await db.commit()
                
                if isinstance(e, LocalAgentCoreError):
                    raise HTTPException(status_code=422, detail=str(e))
                else:
                    raise HTTPException(status_code=500, detail=error_message)
                
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {str(e)}"
            )
    
    async def get_analysis_results(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession
    ) -> DocumentAnalysisResponse:
        """
        Retrieve analysis results for a document
        
        Args:
            document_id: Database document ID
            user_id: ID of requesting user
            db: Database session
            
        Returns:
            DocumentAnalysisResponse: Formatted analysis results
        """
        try:
            # Get document and analysis records
            document_result = await db.execute(
                select(DocumentRecord).where(DocumentRecord.id == document_id)
            )
            document = document_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            if document.uploaded_by != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get latest analysis result
            analysis_result = await db.execute(
                select(AnalysisResultRecord)
                .where(AnalysisResultRecord.document_id == document_id)
                .order_by(AnalysisResultRecord.created_at.desc())
                .limit(1)
            )
            analysis = analysis_result.scalar_one_or_none()
            
            if not analysis:
                return DocumentAnalysisResponse(
                    document_id=document_id,
                    status=document.processing_status,
                    message="No analysis results available"
                )
            
            # Get related issues and remedies
            issues_result = await db.execute(
                select(LegalIssueRecord)
                .where(LegalIssueRecord.analysis_id == analysis.id)
            )
            issues = issues_result.scalars().all()
            
            remedies_result = await db.execute(
                select(RemedyRecord)
                .where(RemedyRecord.analysis_id == analysis.id)
            )
            remedies = remedies_result.scalars().all()
            
            return DocumentAnalysisResponse(
                document_id=document_id,
                status=document.processing_status,
                analysis_id=str(analysis.id),
                document_type=analysis.document_type,
                confidence_score=analysis.confidence_score,
                processing_time=analysis.processing_time,
                issues_found=len(issues),
                remedies_suggested=len(remedies),
                classification=json.loads(analysis.classification_json) if analysis.classification_json else None,
                issues=[self._format_issue(issue) for issue in issues],
                remedies=[self._format_remedy(remedy) for remedy in remedies],
                analysis_report=json.loads(analysis.analysis_report) if analysis.analysis_report else None,
                completed_at=analysis.completed_at,
                metadata=json.loads(analysis.metadata_json) if analysis.metadata_json else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve analysis results: {str(e)}"
            )
    
    async def delete_document(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete document and all associated analysis data"""
        try:
            # Get document record
            result = await db.execute(
                select(DocumentRecord).where(DocumentRecord.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            if document.uploaded_by != user_id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Delete file from storage
            if document.file_path and Path(document.file_path).exists():
                Path(document.file_path).unlink()
            
            # Delete database records (cascading deletes will handle related records)
            await db.execute(
                delete(DocumentRecord).where(DocumentRecord.id == document_id)
            )
            await db.commit()
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )
    
    async def _validate_file(self, content: bytes, filename: str, content_type: str) -> None:
        """Validate uploaded file"""
        # Check file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File size {len(content)} exceeds maximum {self.max_file_size}")
        
        # Check content type
        if content_type not in self.supported_formats:
            raise ValueError(f"Unsupported file type: {content_type}")
        
        # Basic content validation
        if len(content) == 0:
            raise ValueError("File is empty")
    
    async def _extract_text_content(self, content: bytes, content_type: str, filename: str) -> str:
        """Extract text content from file based on type"""
        if content_type == "text/plain":
            return content.decode('utf-8', errors='ignore')
        
        elif content_type == "application/pdf":
            # For now, return placeholder - would integrate PDF extraction library
            return f"[PDF Content from {filename}] - PDF text extraction would be implemented here"
        
        elif content_type in ["application/msword", 
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            # For now, return placeholder - would integrate Word document extraction
            return f"[Word Document Content from {filename}] - Word text extraction would be implemented here"
        
        else:
            # Attempt to decode as text
            try:
                return content.decode('utf-8', errors='ignore')
            except Exception:
                raise ValueError(f"Cannot extract text from {content_type}")
    
    async def _save_file(self, content: bytes, filename: str, user_id: str) -> Path:
        """Save file to storage and return path"""
        # Create user-specific directory
        user_dir = self.upload_directory / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        unique_filename = f"{timestamp}_{safe_filename}"
        
        file_path = user_dir / unique_filename
        
        # Write file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        return file_path
    
    async def _store_analysis_results(
        self,
        document_id: str,
        analysis_result: AnalysisResult,
        user_id: str,
        db: AsyncSession
    ) -> AnalysisResultRecord:
        """Store analysis results in database"""
        
        # Create main analysis record
        analysis_record = AnalysisResultRecord(
            document_id=document_id,
            analyzer_type=analysis_result.analyzer_type,
            analyzer_version=analysis_result.analyzer_version,
            document_type=analysis_result.classification.document_type.value if analysis_result.classification else None,
            confidence_score=analysis_result.confidence_score,
            processing_time=analysis_result.processing_time,
            tokens_analyzed=analysis_result.tokens_analyzed,
            status=analysis_result.status,
            classification_json=json.dumps(asdict(analysis_result.classification)) if analysis_result.classification else None,
            analysis_report=json.dumps(analysis_result.metadata.get("analysis_report")) if "analysis_report" in analysis_result.metadata else None,
            metadata_json=json.dumps(analysis_result.metadata),
            created_by=user_id,
            created_at=datetime.utcnow(),
            completed_at=analysis_result.completed_at
        )
        
        db.add(analysis_record)
        await db.flush()  # Get the ID
        
        # Store issues
        for issue in analysis_result.issues:
            issue_record = LegalIssueRecord(
                analysis_id=analysis_record.id,
                issue_type=issue.type.value,
                severity=issue.severity.value,
                title=issue.title,
                description=issue.description,
                confidence=issue.confidence,
                location_json=json.dumps(issue.location),
                suggestions_json=json.dumps(issue.suggestions),
                metadata_json=json.dumps(issue.metadata)
            )
            db.add(issue_record)
        
        # Store remedies
        for remedy in analysis_result.remedies:
            remedy_record = RemedyRecord(
                analysis_id=analysis_record.id,
                title=remedy.title,
                description=remedy.description,
                category=remedy.category,
                priority=remedy.priority.value,
                implementation_steps_json=json.dumps(remedy.implementation_steps),
                legal_basis_json=json.dumps(remedy.legal_basis),
                estimated_impact=remedy.estimated_impact,
                metadata_json=json.dumps(remedy.metadata)
            )
            db.add(remedy_record)
        
        await db.commit()
        await db.refresh(analysis_record)
        
        return analysis_record
    
    def _format_issue(self, issue: LegalIssueRecord) -> Dict[str, Any]:
        """Format issue record for API response"""
        return {
            "id": str(issue.id),
            "type": issue.issue_type,
            "severity": issue.severity,
            "title": issue.title,
            "description": issue.description,
            "confidence": issue.confidence,
            "location": json.loads(issue.location_json) if issue.location_json else {},
            "suggestions": json.loads(issue.suggestions_json) if issue.suggestions_json else [],
            "metadata": json.loads(issue.metadata_json) if issue.metadata_json else {}
        }
    
    def _format_remedy(self, remedy: RemedyRecord) -> Dict[str, Any]:
        """Format remedy record for API response"""
        return {
            "id": str(remedy.id),
            "title": remedy.title,
            "description": remedy.description,
            "category": remedy.category,
            "priority": remedy.priority,
            "implementation_steps": json.loads(remedy.implementation_steps_json) if remedy.implementation_steps_json else [],
            "legal_basis": json.loads(remedy.legal_basis_json) if remedy.legal_basis_json else [],
            "estimated_impact": remedy.estimated_impact,
            "metadata": json.loads(remedy.metadata_json) if remedy.metadata_json else {}
        }


# Global service instance
_document_service: Optional[DocumentProcessingService] = None

def get_document_processing_service(config: Optional[Dict[str, Any]] = None) -> DocumentProcessingService:
    """Get or create document processing service instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentProcessingService(config)
    return _document_service