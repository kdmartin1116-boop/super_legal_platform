


import os

import json



"""

Document Processing Service

=========================



Orchestrates the document processing workflow, from upload to analysis and result retrieval.

"""



from sqlalchemy.ext.asyncio import AsyncSession

from typing import Dict, Any, Optional

import uuid

from datetime import datetime



from .database_enhanced import database_manager, DocumentRecord, AnalysisResultRecord, LegalIssueRecord, RemedyRecord

from packages.LocalAgentCore.document_analyzer import DocumentAnalyzer

from packages.LocalAgentCore.base import AnalysisResult
from .prompt_templates import get_prompt



# Define the upload directory at the module level

UPLOAD_DIRECTORY = "uploads"

if not os.path.exists(UPLOAD_DIRECTORY):

    os.makedirs(UPLOAD_DIRECTORY)



class DocumentProcessingService:

    """Service for handling document processing logic."""



    def __init__(self):

        self.document_analyzer = DocumentAnalyzer()

        self.supported_formats = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]

        self.max_file_size = 10 * 1024 * 1024  # 10MB

        self.processing_timeout = 300 # 5 minutes



    async def upload_document(

        self, 

        file_content: bytes, 

        filename: str, 

        content_type: str, 

        user_id: str, 

        db: AsyncSession, 

        metadata: Optional[Dict[str, Any]] = None

    ) -> DocumentRecord:

        """Uploads and saves a document record."""

        

        if content_type not in self.supported_formats:

            raise ValueError(f"Unsupported file format: {content_type}")



        if len(file_content) > self.max_file_size:

            raise ValueError(f"File size exceeds the {self.max_file_size / (1024*1024)}MB limit")



        document_id = str(uuid.uuid4())

        file_extension = os.path.splitext(filename)[1]

        new_filename = f"{document_id}{file_extension}"

        file_path = os.path.join(UPLOAD_DIRECTORY, new_filename)



        with open(file_path, "wb") as f:

            f.write(file_content)



        text_content = ""

        if content_type == "text/plain":

            text_content = file_content.decode("utf-8")

        # TODO: Implement text extraction for PDF and Word documents



        new_document = DocumentRecord(

            id=document_id,

            filename=filename,

            content_type=content_type,

            file_size=len(file_content),

            file_path=file_path,

            text_content=text_content,

            uploaded_by=user_id,

            processing_status="uploaded",

            upload_timestamp=datetime.utcnow(),

            metadata_json=json.dumps(metadata) if metadata else "{}"

        )

        

        db.add(new_document)

        await db.commit()

        await db.refresh(new_document)

        

        return new_document



    async def process_document(

        self, 

        document_id: str, 

        user_id: str, 

        db: AsyncSession, 

        analysis_options: Optional[Dict[str, Any]] = None

    ) -> AnalysisResult:

        """Processes a document using the DocumentAnalyzer."""

        

        document = await db.get(DocumentRecord, document_id)

        

        if not document or document.uploaded_by != user_id:

            raise ValueError("Document not found or access denied")



        document.processing_status = "processing"

        await db.commit()



        try:

            analysis_result = await self.document_analyzer.analyze(

                document_text=document.text_content,

                metadata=analysis_options

            )



            await self._save_analysis_results(db, document_id, analysis_result)



            document.processing_status = "completed"

            document.last_analyzed = datetime.utcnow()

            await db.commit()



            return analysis_result



        except Exception as e:

            document.processing_status = "failed"

            await db.commit()

            raise e



    async def _save_analysis_results(self, db: AsyncSession, document_id: str, result: AnalysisResult):

        """Saves the analysis results to the database."""

        

        analysis_record = AnalysisResultRecord(

            id=str(uuid.uuid4()),

            document_id=document_id,

            confidence_score=result.confidence_score,

            processing_time=result.processing_time,

            document_type=result.classification.document_type.value if result.classification else None,

            metadata_json=json.dumps(result.metadata)

        )

        db.add(analysis_record)

        await db.flush()



        for issue in result.issues:

            issue_record = LegalIssueRecord(

                id=str(uuid.uuid4()),

                analysis_id=analysis_record.id,

                issue_type=issue.issue_type,

                severity=issue.severity.value,

                title=issue.title,

                description=issue.description,

                confidence=issue.confidence,

                location_json=json.dumps(issue.location),

                suggestions_json=json.dumps(issue.suggestions)

            )

            db.add(issue_record)



        for remedy in result.remedies:

            remedy_record = RemedyRecord(

                id=str(uuid.uuid44()),

                analysis_id=analysis_record.id,

                title=remedy.title,

                description=remedy.description,

                category=remedy.category,

                priority=remedy.priority.value,

                implementation_steps_json=json.dumps(remedy.implementation_steps),

                legal_basis_json=json.dumps(remedy.legal_basis),

                estimated_impact=remedy.estimated_impact

            )

            db.add(remedy_record)



        await db.commit()



    async def get_analysis_results(

        self, 

        document_id: str, 

        user_id: str, 

        db: AsyncSession

    ) -> Dict[str, Any]:

        """Retrieves the analysis results for a document."""

        

        document = await db.get(DocumentRecord, document_id)

        

        if not document or document.uploaded_by != user_id:

            raise ValueError("Document not found or access denied")



        analysis_record = await db.execute(

            AnalysisResultRecord.select().where(AnalysisResultRecord.document_id == document_id).order_by(AnalysisResultRecord.created_at.desc()).limit(1)

        )

        analysis = analysis_record.scalar_one_or_none()



        if not analysis:

            return {"document_id": document_id, "status": document.processing_status, "analysis_summary": {}}



        issues = await db.execute(LegalIssueRecord.select().where(LegalIssueRecord.analysis_id == analysis.id))

        remedies = await db.execute(RemedyRecord.select().where(RemedyRecord.analysis_id == analysis.id))



        return {

            "document_id": document_id,

            "status": document.processing_status,

            "analysis_summary": {

                "document_type": analysis.document_type,

                "confidence_score": analysis.confidence_score,

                "contradiction_count": len(issues.scalars().all()),

                "remedy_count": len(remedies.scalars().all())

            },

            "contradictions": [issue.to_dict() for issue in issues.scalars().all()],

            "remedies": [remedy.to_dict() for remedy in remedies.scalars().all()]

        }



    async def delete_document(

        self, 

        document_id: str, 

        user_id: str, 

        db: AsyncSession

    ) -> bool:

        """Deletes a document and its analysis results."""

        

        document = await db.get(DocumentRecord, document_id)

        

        if not document or document.uploaded_by != user_id:

            raise ValueError("Document not found or access denied")


    async def render_prompt_with_analysis(
        self,
        document_id: str,
        user_id: str,
        db: AsyncSession,
        template_name: str,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Fetch latest analysis for a document and render a prompt template.

        The resulting context will include:
        - document_text: the stored text_content
        - previous_analysis: a short summary compiled from analysis results
        - issues: list of issue summaries
        - remedies: list of remedy summaries
        - analysis_summary: document_type, confidence_score, processing_time

        This method is async because it reads from the DB.
        """
        # Validate document ownership
        document = await db.get(DocumentRecord, document_id)
        if not document or document.uploaded_by != user_id:
            raise ValueError("Document not found or access denied")

        # Get latest analysis
        analysis_q = await db.execute(
            AnalysisResultRecord.select()
            .where(AnalysisResultRecord.document_id == document_id)
            .order_by(AnalysisResultRecord.created_at.desc())
            .limit(1)
        )
        analysis = analysis_q.scalar_one_or_none()

        # Build context
        context: Dict[str, Any] = extra_context.copy() if extra_context else {}
        context.setdefault("document_text", document.text_content or "")

        if analysis:
            # basic analysis_summary
            context.setdefault("analysis_summary", {
                "document_type": analysis.document_type,
                "confidence_score": analysis.confidence_score,
                "processing_time": analysis.processing_time,
            })

            # fetch issues and remedies
            issues_q = await db.execute(LegalIssueRecord.select().where(LegalIssueRecord.analysis_id == analysis.id))
            remedies_q = await db.execute(RemedyRecord.select().where(RemedyRecord.analysis_id == analysis.id))

            issues = [
                {
                    "id": str(i.id),
                    "title": i.title,
                    "severity": i.severity,
                    "description": i.description,
                    "confidence": i.confidence,
                }
                for i in issues_q.scalars().all()
            ]

            remedies = [
                {
                    "id": str(r.id),
                    "title": r.title,
                    "category": r.category,
                    "priority": r.priority,
                    "implementation_steps": json.loads(r.implementation_steps_json) if r.implementation_steps_json else [],
                }
                for r in remedies_q.scalars().all()
            ]

            context.setdefault("previous_analysis", json.dumps(context["analysis_summary"]))
            context.setdefault("issues", issues)
            context.setdefault("remedies", remedies)
        else:
            context.setdefault("analysis_summary", {})
            context.setdefault("previous_analysis", "")
            context.setdefault("issues", [])
            context.setdefault("remedies", [])

        # Render using synchronous render_prompt
        return self.render_prompt(template_name, context)


        if os.path.exists(document.file_path):

            os.remove(document.file_path)



        await db.delete(document)

        await db.commit()

        

        return True



def get_document_processing_service() -> DocumentProcessingService:

    """Factory function to get the document processing service."""

    return DocumentProcessingService()


