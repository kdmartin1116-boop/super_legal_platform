import re
import bleach
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
import validators
import magic
from pathlib import Path

from config import settings


class SecurityManager:
    """Security management and validation"""
    
    # Dangerous patterns to check in text inputs
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',   # Event handlers
        r'data:text\/html',  # Data URLs
        r'eval\s*\(',   # eval() calls
        r'setTimeout\s*\(',  # setTimeout calls
        r'setInterval\s*\(',  # setInterval calls
    ]
    
    # File type validation using magic numbers
    ALLOWED_MIME_TYPES = {
        'pdf': ['application/pdf'],
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'png': ['image/png'],
        'txt': ['text/plain'],
        'doc': ['application/msword'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }
    
    def __init__(self):
        self.file_type_detector = magic.Magic(mime=True)
    
    def sanitize_text(self, text: str) -> str:
        """Sanitize text input to prevent XSS"""
        if not text:
            return ""
        
        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Use bleach to clean HTML
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        clean_text = bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        return clean_text
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        return validators.email(email)
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        return validators.url(url)
    
    def validate_file_upload(self, file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        validation_result = {
            'valid': False,
            'errors': [],
            'file_info': {}
        }
        
        # Check file size
        if hasattr(file, 'size') and file.size > settings.max_content_length:
            validation_result['errors'].append(
                f"File size ({file.size}) exceeds maximum allowed size ({settings.max_content_length})"
            )
            return validation_result
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            if file_ext not in settings.allowed_extensions:
                validation_result['errors'].append(
                    f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
                )
                return validation_result
        else:
            validation_result['errors'].append("Filename is required")
            return validation_result
        
        # Validate MIME type using magic numbers
        try:
            file_content = file.file.read(1024)  # Read first 1KB for magic number detection
            file.file.seek(0)  # Reset file pointer
            
            detected_mime = self.file_type_detector.from_buffer(file_content)
            
            if file_ext in self.ALLOWED_MIME_TYPES:
                allowed_mimes = self.ALLOWED_MIME_TYPES[file_ext]
                if detected_mime not in allowed_mimes:
                    validation_result['errors'].append(
                        f"File content doesn't match extension. Expected: {allowed_mimes}, Got: {detected_mime}"
                    )
                    return validation_result
        except Exception as e:
            validation_result['errors'].append(f"Error validating file type: {str(e)}")
            return validation_result
        
        validation_result['valid'] = True
        validation_result['file_info'] = {
            'filename': file.filename,
            'extension': file_ext,
            'mime_type': detected_mime,
            'size': getattr(file, 'size', 0)
        }
        
        return validation_result
    
    def validate_coordinates(self, x: float, y: float, page_width: float = 612, page_height: float = 792) -> bool:
        """Validate PDF coordinates are within bounds"""
        return (0 <= x <= page_width) and (0 <= y <= page_height)
    
    def validate_text_length(self, text: str, max_length: int = 10000) -> bool:
        """Validate text length"""
        return len(text) <= max_length
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = Path(filename).name
        
        # Remove or replace dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[:255-len(ext)] + ext
        
        return filename
    
    def add_security_headers(self, response: Response):
        """Add security headers to response"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self'"
            )
    
    def validate_json_input(self, data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate JSON input data"""
        validation_result = {
            'valid': True,
            'errors': [],
            'sanitized_data': {}
        }
        
        # Check required fields
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Missing required fields: {', '.join(missing_fields)}")
            return validation_result
        
        # Sanitize text fields
        sanitized_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_data[key] = self.sanitize_text(value)
            elif isinstance(value, (int, float, bool, list, dict)):
                sanitized_data[key] = value
            else:
                sanitized_data[key] = str(value)
        
        validation_result['sanitized_data'] = sanitized_data
        return validation_result


# Global security manager instance
security_manager = SecurityManager()