"""
Enhanced authentication and authorization system with JWT tokens, role-based access control,
and session management.
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import uuid
from enum import Enum

from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token security
security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    PREMIUM = "premium"
    BASIC = "basic"
    GUEST = "guest"


class Permission(str, Enum):
    """System permissions"""
    # Document permissions
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"
    DOCUMENT_PROCESS = "document:process"
    
    # Generation permissions
    GENERATE_BASIC = "generate:basic"
    GENERATE_ADVANCED = "generate:advanced"
    GENERATE_BULK = "generate:bulk"
    
    # Education permissions
    EDUCATION_ACCESS = "education:access"
    EDUCATION_PROGRESS = "education:progress"
    
    # Research permissions
    RESEARCH_ACCESS = "research:access"
    RESEARCH_EXPORT = "research:export"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"


# Role-permission mapping
ROLE_PERMISSIONS = {
    UserRole.GUEST: [
        Permission.EDUCATION_ACCESS,
    ],
    UserRole.BASIC: [
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.GENERATE_BASIC,
        Permission.EDUCATION_ACCESS,
        Permission.EDUCATION_PROGRESS,
        Permission.RESEARCH_ACCESS,
    ],
    UserRole.PREMIUM: [
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.DOCUMENT_DELETE,
        Permission.DOCUMENT_PROCESS,
        Permission.GENERATE_BASIC,
        Permission.GENERATE_ADVANCED,
        Permission.GENERATE_BULK,
        Permission.EDUCATION_ACCESS,
        Permission.EDUCATION_PROGRESS,
        Permission.RESEARCH_ACCESS,
        Permission.RESEARCH_EXPORT,
    ],
    UserRole.ADMIN: [perm for perm in Permission],  # All permissions
}


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class AuthManager:
    """Enhanced authentication and authorization manager"""
    
    def __init__(self):
        self.algorithm = settings.jwt_algorithm
        self.secret_key = settings.jwt_secret_key
        self.access_token_expire_minutes = settings.jwt_expire_minutes
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # JWT ID for tracking
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token (longer-lived)"""
        data = {
            "sub": user_id,
            "type": "refresh",
        }
        expire = datetime.utcnow() + timedelta(days=30)  # 30 days
        data["exp"] = expire
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid token")
    
    def generate_api_key(self) -> str:
        """Generate API key for programmatic access"""
        return f"slp_{secrets.token_urlsafe(32)}"
    
    def has_permission(self, user_role: UserRole, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        return permission in ROLE_PERMISSIONS.get(user_role, [])
    
    def get_user_permissions(self, user_role: UserRole) -> List[Permission]:
        """Get all permissions for a user role"""
        return ROLE_PERMISSIONS.get(user_role, [])


# Global auth manager
auth_manager = AuthManager()


class CurrentUser:
    """Current user information"""
    def __init__(
        self,
        id: uuid.UUID,
        email: str,
        username: str,
        role: UserRole,
        is_active: bool = True,
        is_verified: bool = False,
        permissions: Optional[List[Permission]] = None,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.role = role
        self.is_active = is_active
        self.is_verified = is_verified
        self.permissions = permissions or auth_manager.get_user_permissions(role)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    try:
        payload = auth_manager.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # In a real implementation, you would fetch user from database
        # For now, we'll extract user info from the token
        user_data = payload.get("user_data", {})
        
        return CurrentUser(
            id=uuid.UUID(user_id),
            email=user_data.get("email", ""),
            username=user_data.get("username", ""),
            role=UserRole(user_data.get("role", "basic")),
            is_active=user_data.get("is_active", True),
            is_verified=user_data.get("is_verified", False),
        )
        
    except Exception as e:
        raise AuthenticationError(f"Authentication failed: {str(e)}")


async def get_current_active_user(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency to get current active user"""
    if not current_user.is_active:
        raise AuthenticationError("User account is deactivated")
    return current_user


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def permission_dependency(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        if not auth_manager.has_permission(current_user.role, permission):
            raise AuthorizationError(f"Missing required permission: {permission.value}")
        return current_user
    return permission_dependency


def require_role(role: UserRole):
    """Decorator to require specific role or higher"""
    role_hierarchy = {
        UserRole.GUEST: 0,
        UserRole.BASIC: 1,
        UserRole.PREMIUM: 2,
        UserRole.ADMIN: 3,
    }
    
    def role_dependency(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        if role_hierarchy.get(current_user.role, 0) < role_hierarchy.get(role, 0):
            raise AuthorizationError(f"Requires {role.value} role or higher")
        return current_user
    return role_dependency


async def get_optional_user(request: Request) -> Optional[CurrentUser]:
    """Get current user if authenticated, None otherwise (for optional auth)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = auth_manager.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id:
            user_data = payload.get("user_data", {})
            return CurrentUser(
                id=uuid.UUID(user_id),
                email=user_data.get("email", ""),
                username=user_data.get("username", ""),
                role=UserRole(user_data.get("role", "basic")),
                is_active=user_data.get("is_active", True),
                is_verified=user_data.get("is_verified", False),
            )
    except Exception:
        pass  # Silent failure for optional auth
    
    return None


class RateLimitByUser:
    """Rate limiting by user ID"""
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.user_calls: Dict[str, List[datetime]] = {}
    
    def __call__(self, current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        user_id = str(current_user.id)
        now = datetime.utcnow()
        
        # Clean old calls
        if user_id in self.user_calls:
            self.user_calls[user_id] = [
                call_time for call_time in self.user_calls[user_id]
                if (now - call_time).seconds < self.period
            ]
        else:
            self.user_calls[user_id] = []
        
        # Check rate limit
        if len(self.user_calls[user_id]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {self.calls} calls per {self.period} seconds"
            )
        
        # Record this call
        self.user_calls[user_id].append(now)
        return current_user