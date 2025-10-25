"""
LocalAgentCore - Core Business Logic Package
===========================================

This package contains the core legal intelligence modules for the Sovereign Legal Platform:

- ContradictionDetector: Identifies contradictions and inconsistencies in legal documents
- InstrumentClassifier: Classifies document types and categorizes legal instruments  
- RemedyCompiler: Generates legal remedies and suggestions based on document analysis
- DocumentAnalyzer: Unified engine combining all analysis capabilities

Version: 1.0.0
Author: Sovereign Legal Platform Team
License: Proprietary
"""

from .contradiction_detector import ContradictionDetector
from .instrument_classifier import InstrumentClassifier  
from .remedy_compiler import RemedyCompiler
from .document_analyzer import DocumentAnalyzer
from .base import BaseAnalyzer, AnalysisResult, DocumentType, LegalIssue
from .exceptions import LocalAgentCoreError, AnalysisError, ClassificationError, DetectionError

__version__ = "1.0.0"
__author__ = "Sovereign Legal Platform Team"

__all__ = [
    # Core analyzers
    "ContradictionDetector",
    "InstrumentClassifier", 
    "RemedyCompiler",
    "DocumentAnalyzer",
    
    # Base classes and types
    "BaseAnalyzer",
    "AnalysisResult", 
    "DocumentType",
    "LegalIssue",
    
    # Exceptions
    "LocalAgentCoreError",
    "AnalysisError",
    "ClassificationError", 
    "DetectionError",
    
    # Version info
    "__version__",
    "__author__"
]

# Package-level configuration
DEFAULT_CONFIG = {
    "nlp_model": "en_core_web_sm",
    "confidence_threshold": 0.8,
    "max_document_size": 10 * 1024 * 1024,  # 10MB
    "enable_caching": True,
    "cache_ttl": 3600,  # 1 hour
    "debug_mode": False
}

def get_version() -> str:
    """Get package version"""
    return __version__

def get_config() -> dict:
    """Get default package configuration"""
    return DEFAULT_CONFIG.copy()