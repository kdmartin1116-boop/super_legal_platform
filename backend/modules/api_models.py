"""
Enhanced API structure with versioning, comprehensive documentation, and response models.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
import uuid


class ResponseStatus(str, Enum):
    """Standard response status values"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"


class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    )


class DataResponse(BaseResponse):
    """Response model with data payload"""
    data: Any = None
    meta: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    data: List[Any] = Field(default_factory=list)
    pagination: Dict[str, Any] = Field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        page: int = 1,
        page_size: int = 20,
        total_items: int = 0,
        **kwargs
    ):
        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 1
        
        return cls(
            data=items,
            pagination={
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
                "next_page": page + 1 if page < total_pages else None,
                "prev_page": page - 1 if page > 1 else None,
            },
            **kwargs
        )


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = ResponseStatus.ERROR
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    help_url: Optional[str] = None


# Request/Response Models for User Management
class UserCreateRequest(BaseModel):
    """User creation request"""
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, description="Full name")
    phone_number: Optional[str] = Field(None, description="Phone number")


class UserUpdateRequest(BaseModel):
    """User update request"""
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """User response model"""
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: str
    subscription_plan: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# Document Models
class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: uuid.UUID
    filename: str
    file_size: int
    document_type: Optional[str] = None
    processing_status: str = "pending"
    upload_url: Optional[str] = None


class DocumentAnalysisResponse(BaseModel):
    """Document analysis response"""
    document_id: uuid.UUID
    analysis_results: Dict[str, Any]
    contradictions_found: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None


# Generation Models  
class DocumentGenerationRequest(BaseModel):
    """Document generation request"""
    document_type: str = Field(..., description="Type of document to generate")
    template_id: Optional[str] = Field(None, description="Template identifier")
    parameters: Dict[str, Any] = Field(..., description="Generation parameters")
    format: str = Field(default="pdf", description="Output format")


class DocumentGenerationResponse(BaseModel):
    """Document generation response"""
    generation_id: uuid.UUID
    document_type: str
    status: str = "completed"
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    file_size: Optional[int] = None


# Education Models
class LessonProgressRequest(BaseModel):
    """Lesson progress update request"""
    lesson_id: str
    completed: bool = False
    score: Optional[int] = None
    time_spent: Optional[int] = None  # seconds
    progress_data: Optional[Dict[str, Any]] = None


class EducationStatsResponse(BaseModel):
    """Education statistics response"""
    total_lessons: int
    completed_lessons: int
    completion_percentage: float
    total_time_spent: int  # seconds
    average_score: Optional[float] = None
    streak_days: int
    achievements: List[Dict[str, Any]] = Field(default_factory=list)


# Legal Research Models
class LegalSearchRequest(BaseModel):
    """Legal search request"""
    query: str = Field(..., min_length=3, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class CaseSearchResult(BaseModel):
    """Case search result"""
    case_name: str
    citation: str
    court: str
    year: int
    summary: str
    relevance_score: float
    key_holdings: List[str] = Field(default_factory=list)
    full_text_url: Optional[str] = None


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    uptime: Optional[float] = None


# API Metadata
class APIInfo(BaseModel):
    """API information model"""
    title: str = "Sovereign Legal Platform API"
    version: str = "1.0.0"
    description: str = "Comprehensive legal technology platform API"
    
    contact: Dict[str, str] = Field(default_factory=lambda: {
        "name": "Support Team",
        "email": "support@sovereignlegal.com",
        "url": "https://sovereignlegal.com/support"
    })
    
    license: Dict[str, str] = Field(default_factory=lambda: {
        "name": "Commercial License",
        "url": "https://sovereignlegal.com/license"
    })


# Rate Limiting Models
class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None


# Webhook Models (for future use)
class WebhookEvent(BaseModel):
    """Webhook event model"""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
    user_id: Optional[uuid.UUID] = None


# Batch Operation Models
class BatchOperationRequest(BaseModel):
    """Batch operation request"""
    operation_type: str
    items: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None


class BatchOperationResponse(BaseModel):
    """Batch operation response"""
    batch_id: uuid.UUID
    operation_type: str
    total_items: int
    processed_items: int
    failed_items: int
    status: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# Export/Import Models
class ExportRequest(BaseModel):
    """Data export request"""
    export_type: str = Field(..., description="Type of data to export")
    format: str = Field(default="json", description="Export format")
    date_range: Optional[Dict[str, datetime]] = None
    filters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Data export response"""
    export_id: uuid.UUID
    download_url: str
    expires_at: datetime
    file_size: Optional[int] = None
    record_count: int


# API Key Models (for programmatic access)
class APIKeyCreateRequest(BaseModel):
    """API key creation request"""
    name: str = Field(..., description="API key name/description")
    permissions: List[str] = Field(default_factory=list, description="API key permissions")
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    key_id: uuid.UUID
    name: str
    key_prefix: str  # Only show first few characters
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


# Document Processing Models for LocalAgentCore Integration

class DocumentProcessingStatus(str, Enum):
    """Document processing status values"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentAnalysisRequest(BaseModel):
    """Document analysis request"""
    enable_classification: bool = Field(default=True, description="Enable document classification")
    enable_contradiction_detection: bool = Field(default=True, description="Enable contradiction detection")
    enable_remedy_generation: bool = Field(default=True, description="Enable remedy generation")
    analysis_options: Optional[Dict[str, Any]] = Field(default=None, description="Additional analysis options")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")


class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class DocumentAnalysisResponse(BaseModel):
    """Comprehensive document analysis response"""
    document_id: str
    status: DocumentProcessingStatus
    message: Optional[str] = None
    
    # Analysis results
    analysis_id: Optional[str] = None
    document_type: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time: Optional[float] = None
    
    # Counts
    issues_found: int = 0
    remedies_suggested: int = 0
    
    # Detailed results
    classification: Optional[Dict[str, Any]] = None
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    remedies: List[Dict[str, Any]] = Field(default_factory=list)
    analysis_report: Optional[Dict[str, Any]] = None
    
    # Timestamps
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentListResponse(BaseModel):
    """Document list response"""
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class ContradictionDetail(BaseModel):
    """Detailed contradiction information"""
    id: str
    type: str
    severity: str
    title: str
    description: str
    confidence: float
    location: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RemedyDetail(BaseModel):
    """Detailed remedy information"""
    id: str
    title: str
    description: str
    category: str
    priority: str
    implementation_steps: List[str] = Field(default_factory=list)
    legal_basis: List[str] = Field(default_factory=list)
    estimated_impact: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentClassificationResponse(BaseModel):
    """Document classification response"""
    document_type: str
    confidence: float
    sub_categories: List[str] = Field(default_factory=list)
    features_analyzed: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisStatsResponse(BaseModel):
    """Analysis statistics response"""
    total_documents: int = 0
    documents_by_type: Dict[str, int] = Field(default_factory=dict)
    issues_by_severity: Dict[str, int] = Field(default_factory=dict)
    remedies_by_category: Dict[str, int] = Field(default_factory=dict)
    average_confidence: float = 0.0
    average_processing_time: float = 0.0
    processing_success_rate: float = 0.0


class BulkAnalysisRequest(BaseModel):
    """Bulk document analysis request"""
    document_ids: List[str] = Field(..., description="List of document IDs to analyze")
    analysis_options: Optional[Dict[str, Any]] = Field(default=None, description="Analysis configuration")
    priority: str = Field(default="normal", description="Processing priority")


class BulkAnalysisResponse(BaseModel):
    """Bulk analysis response"""
    batch_id: str
    total_documents: int
    status: str = "initiated"
    estimated_completion: Optional[datetime] = None
    results_url: Optional[str] = None


class AnalysisExportRequest(BaseModel):
    """Analysis results export request"""
    document_ids: Optional[List[str]] = Field(default=None, description="Specific documents to export")
    format: str = Field(default="json", description="Export format (json, csv, pdf)")
    include_full_text: bool = Field(default=False, description="Include document full text")
    date_range: Optional[Dict[str, datetime]] = Field(default=None, description="Date range filter")


# Audit Models
class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    created_at: datetime
    action_data: Optional[Dict[str, Any]] = None