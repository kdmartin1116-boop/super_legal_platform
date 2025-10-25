"""
Enhanced database module with connection pooling, health checks, and migration support.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, pool
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    async_sessionmaker,
    create_async_engine,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models with common fields"""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )


class User(Base):
    """Enhanced user model with additional fields"""
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Profile information
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Preferences
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Subscription info
    subscription_plan: Mapped[str] = mapped_column(String(50), default="free")
    subscription_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Last activity
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Document(Base):
    """Enhanced document model with processing status"""
    __tablename__ = "documents"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256
    
    # Document classification
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Processing status
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processing_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Analysis results
    analysis_results: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contradictions_found: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Storage information
    storage_provider: Mapped[str] = mapped_column(String(20), default="local")
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class GeneratedDocument(Base):
    """Enhanced generated document model"""
    __tablename__ = "generated_documents"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    document_type: Mapped[str] = mapped_column(String(100))
    template_used: Mapped[str] = mapped_column(String(255))
    template_version: Mapped[str] = mapped_column(String(20), default="1.0")
    
    # Generation parameters
    parameters: Mapped[dict] = mapped_column(JSON)
    generated_content: Mapped[str] = mapped_column(Text)
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_format: Mapped[str] = mapped_column(String(10), default="pdf")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    generation_status: Mapped[str] = mapped_column(String(50), default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit trail
    generated_by: Mapped[str] = mapped_column(String(100))  # system/user identifier


class EducationProgress(Base):
    """Enhanced education progress tracking"""
    __tablename__ = "education_progress"
    
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    lesson_id: Mapped[str] = mapped_column(String(100))
    
    # Progress tracking
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    
    # Time tracking
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # seconds
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Detailed progress
    progress_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AuditLog(Base):
    """Audit log for tracking user actions"""
    __tablename__ = "audit_logs"
    
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Request details
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Action details
    action_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DatabaseManager:
    """Enhanced database manager with connection pooling and health checks"""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        
    def _get_database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        if settings.environment == "production" and settings.database_url.startswith("postgresql"):
            return settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        elif settings.database_url.startswith("sqlite:"):
            return settings.database_url.replace("sqlite:", "sqlite+aiosqlite:")
        else:
            return settings.database_url

    @property
    def engine(self) -> AsyncEngine:
        """Get or create the database engine"""
        if self._engine is None:
            database_url = self._get_database_url()
            
            # Engine configuration
            engine_kwargs = {
                "url": database_url,
                "echo": settings.debug,
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # 1 hour
            }
            
            # Add connection pool settings for PostgreSQL
            if "postgresql" in database_url:
                engine_kwargs.update({
                    "pool_size": settings.database_pool_size,
                    "max_overflow": settings.database_max_overflow,
                    "poolclass": pool.QueuePool,
                })
            
            self._engine = create_async_engine(**engine_kwargs)
            
            # Add connection event listeners
            @event.listens_for(self._engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                if "sqlite" in database_url:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            
            logger.info(f"Database engine created for: {database_url}")
        
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """Get or create the session factory"""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
        return self._session_factory

    async def create_tables(self):
        """Create all database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")

    async def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")

    async def health_check(self) -> dict:
        """Comprehensive database health check"""
        try:
            async with self.session_factory() as session:
                # Test basic connectivity
                result = await session.execute("SELECT 1")
                scalar_result = result.scalar()
                
                # Check if tables exist
                tables_exist = await self._check_tables_exist(session)
                
                # Get connection pool status
                pool_status = self._get_pool_status()
                
                return {
                    "status": "healthy" if scalar_result == 1 and tables_exist else "unhealthy",
                    "connection_test": scalar_result == 1,
                    "tables_exist": tables_exist,
                    "pool_status": pool_status,
                    "database_url": self._get_database_url().split("@")[-1] if "@" in self._get_database_url() else "local"
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_test": False,
                "tables_exist": False
            }

    async def _check_tables_exist(self, session: AsyncSession) -> bool:
        """Check if required tables exist"""
        try:
            # Try to query each main table
            from sqlalchemy import text
            tables = ["users", "documents", "generated_documents", "education_progress"]
            
            for table in tables:
                await session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            
            return True
        except Exception:
            return False

    def _get_pool_status(self) -> dict:
        """Get connection pool status"""
        if hasattr(self.engine.pool, 'size'):
            return {
                "pool_size": self.engine.pool.size(),
                "checked_in": self.engine.pool.checkedin(),
                "checked_out": self.engine.pool.checkedout(),
                "overflow": getattr(self.engine.pool, 'overflow', 0),
            }
        return {"status": "pool_info_unavailable"}

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close all database connections"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")

    async def execute_raw_sql(self, sql: str, params: dict = None) -> any:
        """Execute raw SQL (use carefully!)"""
        async with self.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result


# Global database instance
database_manager = DatabaseManager()