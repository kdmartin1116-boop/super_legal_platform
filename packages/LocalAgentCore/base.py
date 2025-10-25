"""
Base Classes and Types for LocalAgentCore
========================================

This module defines the base classes, interfaces, and common types used
throughout the LocalAgentCore package for consistent architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid


class DocumentType(Enum):
    """Enumeration of supported legal document types"""
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    AFFIDAVIT = "affidavit"
    LETTER = "letter"
    MOTION = "motion"
    BRIEF = "brief"
    COMPLAINT = "complaint"
    ANSWER = "answer"
    DISCOVERY = "discovery"
    SETTLEMENT = "settlement"
    MEMORANDUM = "memorandum"
    OPINION = "opinion"
    ORDER = "order"
    JUDGMENT = "judgment"
    UNKNOWN = "unknown"


class LegalIssueType(Enum):
    """Types of legal issues that can be detected"""
    CONTRADICTION = "contradiction"
    AMBIGUITY = "ambiguity"
    MISSING_CLAUSE = "missing_clause"
    COMPLIANCE_ISSUE = "compliance_issue"
    RISK_FACTOR = "risk_factor"
    INCONSISTENCY = "inconsistency"
    FORMATTING_ERROR = "formatting_error"
    REFERENCE_ERROR = "reference_error"


class SeverityLevel(Enum):
    """Severity levels for legal issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class LegalIssue:
    """Represents a legal issue found in a document"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: LegalIssueType = LegalIssueType.CONTRADICTION
    severity: SeverityLevel = SeverityLevel.MEDIUM
    title: str = ""
    description: str = ""
    location: Dict[str, Any] = field(default_factory=dict)  # page, paragraph, line, etc.
    confidence: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Classification:
    """Document classification result"""
    document_type: DocumentType = DocumentType.UNKNOWN
    confidence: float = 0.0
    sub_categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Remedy:
    """Legal remedy or suggestion"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: str = ""
    priority: SeverityLevel = SeverityLevel.MEDIUM
    applicable_issues: List[str] = field(default_factory=list)  # Issue IDs
    implementation_steps: List[str] = field(default_factory=list)
    legal_basis: List[str] = field(default_factory=list)  # Citations, precedents
    estimated_impact: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """Complete analysis result from any analyzer"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    analyzer_type: str = ""
    analyzer_version: str = ""
    
    # Core results
    classification: Optional[Classification] = None
    issues: List[LegalIssue] = field(default_factory=list)
    remedies: List[Remedy] = field(default_factory=list)
    
    # Analysis metadata
    confidence_score: float = 0.0
    processing_time: float = 0.0
    tokens_analyzed: int = 0
    
    # Status information
    status: str = "completed"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_issue(self, issue: LegalIssue) -> None:
        """Add a legal issue to the analysis result"""
        self.issues.append(issue)
    
    def add_remedy(self, remedy: Remedy) -> None:
        """Add a remedy to the analysis result"""
        self.remedies.append(remedy)
    
    def get_critical_issues(self) -> List[LegalIssue]:
        """Get all critical issues"""
        return [issue for issue in self.issues if issue.severity == SeverityLevel.CRITICAL]
    
    def get_high_priority_remedies(self) -> List[Remedy]:
        """Get high priority remedies"""
        return [remedy for remedy in self.remedies if remedy.priority in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]


class BaseAnalyzer(ABC):
    """Abstract base class for all analyzers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the analyzer with configuration"""
        pass
    
    @abstractmethod
    async def analyze(self, document_text: str, metadata: Optional[Dict[str, Any]] = None) -> AnalysisResult:
        """
        Analyze a document and return results
        
        Args:
            document_text: The text content of the document
            metadata: Optional metadata about the document
            
        Returns:
            AnalysisResult containing the analysis findings
        """
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get the version of this analyzer"""
        pass
    
    def validate_input(self, document_text: str) -> None:
        """Validate input document text"""
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        max_size = self.config.get("max_document_size", 10 * 1024 * 1024)
        if len(document_text.encode('utf-8')) > max_size:
            raise ValueError(f"Document size exceeds maximum limit of {max_size} bytes")
    
    def _create_base_result(self, document_id: str = "") -> AnalysisResult:
        """Create a base analysis result with common fields populated"""
        return AnalysisResult(
            document_id=document_id,
            analyzer_type=self.__class__.__name__,
            analyzer_version=self.get_version(),
            started_at=datetime.utcnow()
        )