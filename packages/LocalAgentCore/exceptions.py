"""
Custom Exceptions for LocalAgentCore
===================================

This module defines custom exceptions used throughout the LocalAgentCore package
for proper error handling and debugging.
"""


class LocalAgentCoreError(Exception):
    """Base exception class for LocalAgentCore package"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "CORE_ERROR"
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class AnalysisError(LocalAgentCoreError):
    """Exception raised during document analysis"""
    
    def __init__(self, message: str, analyzer_type: str = None, **kwargs):
        super().__init__(message, error_code="ANALYSIS_ERROR", **kwargs)
        self.analyzer_type = analyzer_type


class ClassificationError(LocalAgentCoreError):
    """Exception raised during document classification"""
    
    def __init__(self, message: str, document_type: str = None, **kwargs):
        super().__init__(message, error_code="CLASSIFICATION_ERROR", **kwargs)
        self.document_type = document_type


class DetectionError(LocalAgentCoreError):
    """Exception raised during contradiction/issue detection"""
    
    def __init__(self, message: str, detection_type: str = None, **kwargs):
        super().__init__(message, error_code="DETECTION_ERROR", **kwargs)
        self.detection_type = detection_type


class ConfigurationError(LocalAgentCoreError):
    """Exception raised for configuration issues"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_key = config_key


class ValidationError(LocalAgentCoreError):
    """Exception raised for input validation errors"""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        self.field = field


class ModelError(LocalAgentCoreError):
    """Exception raised for ML model errors"""
    
    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, error_code="MODEL_ERROR", **kwargs)
        self.model_name = model_name


class ProcessingTimeoutError(LocalAgentCoreError):
    """Exception raised when processing times out"""
    
    def __init__(self, message: str, timeout_seconds: float = None, **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        self.timeout_seconds = timeout_seconds


class ResourceError(LocalAgentCoreError):
    """Exception raised for resource-related errors (memory, disk, etc.)"""
    
    def __init__(self, message: str, resource_type: str = None, **kwargs):
        super().__init__(message, error_code="RESOURCE_ERROR", **kwargs)
        self.resource_type = resource_type


class DependencyError(LocalAgentCoreError):
    """Exception raised when required dependencies are missing"""
    
    def __init__(self, message: str, dependency: str = None, **kwargs):
        super().__init__(message, error_code="DEPENDENCY_ERROR", **kwargs)
        self.dependency = dependency