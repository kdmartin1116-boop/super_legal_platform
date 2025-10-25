import logging
import traceback
import uuid
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from config import settings


class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        return str(uuid.uuid4())[:8]
    
    def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        error_id = self.generate_error_id()
        
        # Log the error
        self.logger.warning(
            f"HTTP Exception {error_id}: {exc.status_code} - {exc.detail} - {request.url}"
        )
        
        response_data = {
            "error": {
                "id": error_id,
                "type": "HTTP_ERROR",
                "status_code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if settings.debug:
            response_data["error"]["path"] = str(request.url)
            response_data["error"]["method"] = request.method
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions"""
        error_id = self.generate_error_id()
        
        # Log the full error with traceback
        self.logger.error(
            f"Unhandled Exception {error_id}: {str(exc)} - {request.url}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Don't expose internal errors in production
        if settings.debug:
            error_message = str(exc)
            error_type = type(exc).__name__
        else:
            error_message = "An internal error occurred. Please try again later."
            error_type = "INTERNAL_ERROR"
        
        response_data = {
            "error": {
                "id": error_id,
                "type": error_type,
                "status_code": 500,
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        if settings.debug:
            response_data["error"]["path"] = str(request.url)
            response_data["error"]["method"] = request.method
            response_data["error"]["traceback"] = traceback.format_exc().split('\n')
        
        return JSONResponse(
            status_code=500,
            content=response_data
        )
    
    def handle_validation_error(self, errors: list, error_context: str = "") -> HTTPException:
        """Handle validation errors"""
        error_id = self.generate_error_id()
        
        self.logger.warning(f"Validation Error {error_id}: {errors} - Context: {error_context}")
        
        return HTTPException(
            status_code=422,
            detail={
                "error_id": error_id,
                "type": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "errors": errors,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def handle_authentication_error(self, message: str = "Authentication failed") -> HTTPException:
        """Handle authentication errors"""
        error_id = self.generate_error_id()
        
        self.logger.warning(f"Authentication Error {error_id}: {message}")
        
        return HTTPException(
            status_code=401,
            detail={
                "error_id": error_id,
                "type": "AUTHENTICATION_ERROR",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def handle_authorization_error(self, message: str = "Insufficient permissions") -> HTTPException:
        """Handle authorization errors"""
        error_id = self.generate_error_id()
        
        self.logger.warning(f"Authorization Error {error_id}: {message}")
        
        return HTTPException(
            status_code=403,
            detail={
                "error_id": error_id,
                "type": "AUTHORIZATION_ERROR",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def handle_not_found_error(self, resource: str) -> HTTPException:
        """Handle not found errors"""
        error_id = self.generate_error_id()
        
        self.logger.info(f"Not Found Error {error_id}: {resource}")
        
        return HTTPException(
            status_code=404,
            detail={
                "error_id": error_id,
                "type": "NOT_FOUND_ERROR",
                "message": f"{resource} not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def handle_rate_limit_error(self, retry_after: int = 60) -> HTTPException:
        """Handle rate limit errors"""
        error_id = self.generate_error_id()
        
        self.logger.warning(f"Rate Limit Error {error_id}")
        
        return HTTPException(
            status_code=429,
            detail={
                "error_id": error_id,
                "type": "RATE_LIMIT_ERROR",
                "message": "Too many requests. Please try again later.",
                "retry_after": retry_after,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Global error handler instance
error_handler = ErrorHandler()