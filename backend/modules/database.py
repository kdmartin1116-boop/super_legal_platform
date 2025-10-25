from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Boolean, Integer
from datetime import datetime
from config import settings


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(Base):
    """Document model"""
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(50))
    file_size: Mapped[int] = mapped_column(Integer)
    document_type: Mapped[str] = mapped_column(String(100), nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis_results: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GeneratedDocument(Base):
    """Generated document model"""
    __tablename__ = "generated_documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    document_type: Mapped[str] = mapped_column(String(100))
    template_used: Mapped[str] = mapped_column(String(255))
    parameters: Mapped[str] = mapped_column(Text)
    generated_content: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EducationProgress(Base):
    """Education progress tracking"""
    __tablename__ = "education_progress"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    module_name: Mapped[str] = mapped_column(String(100))
    lesson_id: Mapped[str] = mapped_column(String(100))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[int] = mapped_column(Integer, nullable=True)
    time_spent: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    """Database management class"""
    
    def __init__(self):
        # Convert SQLite URL for async
        if settings.database_url.startswith("sqlite:"):
            database_url = settings.database_url.replace("sqlite:", "sqlite+aiosqlite:")
        else:
            database_url = settings.database_url
        
        self.engine = create_async_engine(
            database_url,
            echo=settings.debug,
            pool_pre_ping=True
        )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def connect(self):
        """Connect to database and create tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def disconnect(self):
        """Disconnect from database"""
        await self.engine.dispose()
    
    async def health_check(self):
        """Check database health"""
        async with self.async_session() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    
    def get_session(self) -> AsyncSession:
        """Get database session"""
        return self.async_session()


# Global database instance
database = Database()