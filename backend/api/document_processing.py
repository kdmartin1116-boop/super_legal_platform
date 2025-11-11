"""
Document Processing API Endpoints - LocalAgentCore Integration
============================================================

FastAPI endpoints for document upload, analysis, and result retrieval
using LocalAgentCore AI capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import json
import uuid
from datetime import datetime

from ..modules.auth_enhanced import get_current_user, require_permission
from ..modules.database_enhanced import database_manager
from ..modules.document_processing import get_document_processing_service, DocumentProcessingService
from ..modules.api_models import (
    DocumentAnalysisRequest, DocumentAnalysisResponse, DocumentListResponse,
    DocumentUploadRequest, DocumentProcessingStatus, ContradictionDetail,
    RemedyDetail, AnalysisStatsResponse, BulkAnalysisRequest, BulkAnalysisResponse,
    AnalysisExportRequest, BaseResponse, DataResponse, ErrorResponse
)

router = APIRouter(prefix="/api/v1/documents", tags=["Document Processing"])


@router.post("/upload", response_model=DataResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Document file to upload"),
    metadata: Optional[str] = Form(None, description="Document metadata as JSON string"),
    auto_analyze: bool = Form(True, description="Automatically start analysis after upload"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Upload a document for analysis
    
    Supported formats: PDF, Word, Plain Text
    Maximum file size: 10MB
    """
    try:
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Upload document
        document = await doc_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type,
            user_id=str(current_user.id),
            db=db,
            metadata=parsed_metadata
        )
        
        response_data = {
            "document_id": str(document.id),
            "filename": document.filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "status": document.processing_status,
            "uploaded_at": document.upload_timestamp.isoformat()
        }
        
        # Start analysis in background if requested
        if auto_analyze:
            background_tasks.add_task(
                _background_analysis,
                str(document.id),
                str(current_user.id),
                doc_service
            )
            response_data["analysis_started"] = True
        
        return DataResponse(
            data=response_data,
            message="Document uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/{document_id}/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    document_id: str,
    analysis_request: DocumentAnalysisRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Analyze a previously uploaded document using LocalAgentCore
    
    Analysis includes:
    - Document classification
    - Contradiction detection
    - Legal remedy suggestions
    """
    try:
        # Prepare analysis options
        analysis_options = {
            "enable_classification": analysis_request.enable_classification,
            "enable_contradiction_detection": analysis_request.enable_contradiction_detection,
            "enable_remedy_generation": analysis_request.enable_remedy_generation,
            **(analysis_request.analysis_options or {}),
            **(analysis_request.metadata or {})
        }
        
        # Process document
        analysis_result = await doc_service.process_document(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db,
            analysis_options=analysis_options
        )
        
        # Get formatted results
        results = await doc_service.get_analysis_results(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{document_id}/results", response_model=DocumentAnalysisResponse)
async def get_analysis_results(
    document_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Get analysis results for a document
    """
    try:
        results = await doc_service.get_analysis_results(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.post("/prompts/render", response_model=DataResponse)
async def render_prompt(
    payload: Dict[str, Any],
    current_user = Depends(get_current_user),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """Render a named prompt template with context supplied in the request body.

    Request JSON shape:
    {
        "template_name": "credit_analysis",
        "context": { "document_text": "...", "previous_analysis": "..." }
    }
    """
    try:
        template_name = payload.get("template_name")
        context = payload.get("context", {})

        if not template_name:
            raise HTTPException(status_code=400, detail="'template_name' is required")

        rendered = doc_service.render_prompt(template_name, context)

        return DataResponse(data={"rendered": rendered}, message="Prompt rendered successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render prompt: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[DocumentProcessingStatus] = Query(None, description="Filter by status"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search term for filtering by filename"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session)
):
    """
    List user's documents with optional filtering
    """
    try:
        from sqlalchemy.future import select
        from sqlalchemy import and_, func
        from ..modules.database_enhanced import DocumentRecord
        
        # Build query
        query = select(DocumentRecord).where(DocumentRecord.uploaded_by == str(current_user.id))
        
        if status:
            query = query.where(DocumentRecord.processing_status == status.value)

        if search:
            query = query.where(DocumentRecord.filename.ilike(f"%{search}%"))
        
        # Count total items
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()
        
        # Get paginated results
        query = query.order_by(DocumentRecord.upload_timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        document_list = []
        for doc in documents:
            document_list.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "processing_status": doc.processing_status,
                "uploaded_at": doc.upload_timestamp.isoformat(),
                "last_analyzed": doc.last_analyzed.isoformat() if doc.last_analyzed else None,
                "metadata": json.loads(doc.metadata_json) if doc.metadata_json else {}
            })
        
        return DocumentListResponse(
            documents=document_list,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=page * page_size < total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/{document_id}", response_model=BaseResponse)
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session),
    doc_service: DocumentProcessingService = Depends(get_document_processing_service)
):
    """
    Delete a document and all associated analysis data
    """
    try:
        success = await doc_service.delete_document(
            document_id=document_id,
            user_id=str(current_user.id),
            db=db
        )
        
        if success:
            return BaseResponse(message="Document deleted successfully")
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/{document_id}/contradictions", response_model=DataResponse)
async def get_contradictions(
    document_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session)
):
    """
    Get contradictions found in a document
    """
    try:
        from sqlalchemy.future import select
        from ..modules.database_enhanced import AnalysisResultRecord, LegalIssueRecord
        
        # Get latest analysis for document
        analysis_query = select(AnalysisResultRecord).where(
            AnalysisResultRecord.document_id == document_id
        ).order_by(AnalysisResultRecord.created_at.desc()).limit(1)
        
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="No analysis found for document")
        
        # Get issues
        issues_query = select(LegalIssueRecord).where(
            LegalIssueRecord.analysis_id == analysis.id
        )
        
        if severity:
            issues_query = issues_query.where(LegalIssueRecord.severity == severity)
        
        issues_result = await db.execute(issues_query)
        issues = issues_result.scalars().all()
        
        contradictions = []
        for issue in issues:
            contradictions.append({
                "id": str(issue.id),
                "type": issue.issue_type,
                "severity": issue.severity,
                "title": issue.title,
                "description": issue.description,
                "confidence": issue.confidence,
                "location": json.loads(issue.location_json) if issue.location_json else {},
                "suggestions": json.loads(issue.suggestions_json) if issue.suggestions_json else [],
                "metadata": json.loads(issue.metadata_json) if issue.metadata_json else {}
            })
        
        return DataResponse(
            data={"contradictions": contradictions, "count": len(contradictions)},
            message=f"Found {len(contradictions)} contradictions"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contradictions: {str(e)}")


@router.get("/{document_id}/remedies", response_model=DataResponse)
async def get_remedies(
    document_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session)
):
    """
    Get remedies suggested for a document
    """
    try:
        from sqlalchemy.future import select
        from ..modules.database_enhanced import AnalysisResultRecord, RemedyRecord
        
        # Get latest analysis for document
        analysis_query = select(AnalysisResultRecord).where(
            AnalysisResultRecord.document_id == document_id
        ).order_by(AnalysisResultRecord.created_at.desc()).limit(1)
        
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="No analysis found for document")
        
        # Get remedies
        remedies_query = select(RemedyRecord).where(
            RemedyRecord.analysis_id == analysis.id
        )
        
        if category:
            remedies_query = remedies_query.where(RemedyRecord.category == category)
        
        if priority:
            remedies_query = remedies_query.where(RemedyRecord.priority == priority)
        
        remedies_result = await db.execute(remedies_query)
        remedies = remedies_result.scalars().all()
        
        remedy_list = []
        for remedy in remedies:
            remedy_list.append({
                "id": str(remedy.id),
                "title": remedy.title,
                "description": remedy.description,
                "category": remedy.category,
                "priority": remedy.priority,
                "implementation_steps": json.loads(remedy.implementation_steps_json) if remedy.implementation_steps_json else [],
                "legal_basis": json.loads(remedy.legal_basis_json) if remedy.legal_basis_json else [],
                "estimated_impact": remedy.estimated_impact,
                "metadata": json.loads(remedy.metadata_json) if remedy.metadata_json else {}
            })
        
        return DataResponse(
            data={"remedies": remedy_list, "count": len(remedy_list)},
            message=f"Found {len(remedy_list)} remedies"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get remedies: {str(e)}")


@router.get("/stats", response_model=AnalysisStatsResponse)
@require_permission(["view_analytics"])
async def get_analysis_stats(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(database_manager.get_session)
):
    """
    Get analysis statistics for the current user
    """
    try:
        from sqlalchemy import func
        from sqlalchemy.future import select
        from ..modules.database_enhanced import DocumentRecord, AnalysisResultRecord, LegalIssueRecord, RemedyRecord
        
        user_id = str(current_user.id)
        
        # Total documents
        total_docs_result = await db.execute(
            select(func.count()).select_from(DocumentRecord)
            .where(DocumentRecord.uploaded_by == user_id)
        )
        total_documents = total_docs_result.scalar()
        
        # Documents by type
        docs_by_type_result = await db.execute(
            select(AnalysisResultRecord.document_type, func.count())
            .join(DocumentRecord, DocumentRecord.id == AnalysisResultRecord.document_id)
            .where(DocumentRecord.uploaded_by == user_id)
            .where(AnalysisResultRecord.document_type.isnot(None))
            .group_by(AnalysisResultRecord.document_type)
        )
        
        documents_by_type = {row[0]: row[1] for row in docs_by_type_result}
        
        # Issues by severity - placeholder implementation
        issues_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        # Remedies by category - placeholder implementation  
        remedies_by_category = {}
        
        # Average confidence
        avg_confidence_result = await db.execute(
            select(func.avg(AnalysisResultRecord.confidence_score))
            .join(DocumentRecord, DocumentRecord.id == AnalysisResultRecord.document_id)
            .where(DocumentRecord.uploaded_by == user_id)
        )
        average_confidence = avg_confidence_result.scalar() or 0.0
        
        # Average processing time
        avg_time_result = await db.execute(
            select(func.avg(AnalysisResultRecord.processing_time))
            .join(DocumentRecord, DocumentRecord.id == AnalysisResultRecord.document_id)
            .where(DocumentRecord.uploaded_by == user_id)
        )
        average_processing_time = avg_time_result.scalar() or 0.0
        
        return AnalysisStatsResponse(
            total_documents=total_documents,
            documents_by_type=documents_by_type,
            issues_by_severity=issues_by_severity,
            remedies_by_category=remedies_by_category,
            average_confidence=average_confidence,
            average_processing_time=average_processing_time,
            processing_success_rate=0.95  # Placeholder
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


async def _background_analysis(
    document_id: str,
    user_id: str,
    doc_service: DocumentProcessingService
):
    """Background task for document analysis"""
    try:
        async with database_manager.get_session() as db:
            await doc_service.process_document(
                document_id=document_id,
                user_id=user_id,
                db=db
            )
    except Exception as e:
        # Log error - in production would use proper logging
        print(f"Background analysis failed for document {document_id}: {str(e)}")


# Health check endpoint for document processing
@router.get("/health", response_model=DataResponse)
async def document_processing_health():
    """
    Health check for document processing services
    """
    try:
        doc_service = get_document_processing_service()
        capabilities = doc_service.document_analyzer.get_analysis_capabilities()
        cache_stats = doc_service.document_analyzer.get_cache_stats()
        
        health_data = {
            "status": "healthy",
            "capabilities": capabilities,
            "cache_stats": cache_stats,
            "supported_formats": doc_service.supported_formats,
            "max_file_size": doc_service.max_file_size,
            "processing_timeout": doc_service.processing_timeout
        }
        
        return DataResponse(
            data=health_data,
            message="Document processing service is healthy"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Document processing service unhealthy: {str(e)}"
        )