# Test Utilities
"""
Common test utilities and fixtures for the Sovereign Legal Platform
"""

import jwt
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.auth_enhanced import create_access_token, get_password_hash
from backend.modules.models_enhanced import User, UserRole


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        email: str = "test@example.com",
        full_name: str = "Test User",
        password: str = "TestPassword123!",
        role: UserRole = UserRole.BASIC
    ) -> Dict[str, Any]:
        """Create user registration data"""
        return {
            "username": username,
            "email": email,
            "full_name": full_name,
            "password": password,
            "role": role
        }
    
    @staticmethod
    def create_document_data(
        filename: str = "test_document.txt",
        content: str = "This is a test legal document.",
        document_type: str = "contract"
    ) -> Dict[str, Any]:
        """Create document upload data"""
        return {
            "filename": filename,
            "content": content,
            "document_type": document_type,
            "metadata": {
                "size": len(content),
                "mime_type": "text/plain"
            }
        }
    
    @staticmethod
    def create_generation_request(
        document_type: str = "contract",
        parties: list = None,
        terms: Dict[str, str] = None,
        jurisdiction: str = "New York"
    ) -> Dict[str, Any]:
        """Create document generation request"""
        if parties is None:
            parties = ["Party A", "Party B"]
        
        if terms is None:
            terms = {
                "subject_matter": "Software Development Services",
                "duration": "6 months",
                "payment_terms": "Monthly payments of $5,000"
            }
        
        return {
            "document_type": document_type,
            "parties": parties,
            "terms": terms,
            "jurisdiction": jurisdiction
        }


class MockServices:
    """Mock external services for testing"""
    
    @staticmethod
    def mock_document_processing():
        """Mock document processing results"""
        return {
            "status": "processed",
            "analysis": {
                "key_terms": ["obligation", "responsibility", "payment"],
                "risk_factors": ["payment delay", "force majeure"],
                "compliance_score": 0.85,
                "suggestions": [
                    "Consider adding dispute resolution clause",
                    "Specify governing law more clearly"
                ]
            },
            "metadata": {
                "processing_time": 2.5,
                "confidence": 0.92
            }
        }
    
    @staticmethod
    def mock_legal_research():
        """Mock legal research results"""
        return {
            "results": [
                {
                    "case_id": "case_123456",
                    "title": "Smith v. Jones Contract Dispute",
                    "court": "Supreme Court of New York",
                    "date": "2023-01-15",
                    "relevance_score": 0.95,
                    "summary": "Court ruled on breach of contract damages calculation"
                },
                {
                    "case_id": "case_789012",
                    "title": "ABC Corp v. XYZ Ltd Performance Issues",
                    "court": "Court of Appeals",
                    "date": "2022-11-20",
                    "relevance_score": 0.87,
                    "summary": "Established precedent for service level agreements"
                }
            ],
            "total_count": 2,
            "search_metadata": {
                "query": "contract breach damages",
                "execution_time": 1.2
            }
        }
    
    @staticmethod
    def mock_document_generation():
        """Mock document generation results"""
        return {
            "document_id": "gen_doc_123",
            "content": """
            CONTRACT FOR SOFTWARE DEVELOPMENT SERVICES
            
            This Agreement is entered into between Party A and Party B
            for the provision of software development services.
            
            Term: 6 months
            Payment: Monthly payments of $5,000
            Governing Law: New York
            
            [Additional contract terms and conditions...]
            """,
            "document_type": "contract",
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "template_used": "standard_contract_v2",
                "word_count": 250
            }
        }


@pytest.fixture
def test_user_token():
    """Generate test JWT token"""
    user_data = {
        "sub": "testuser",
        "email": "test@example.com",
        "role": "basic",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return create_access_token(data=user_data)


@pytest.fixture
def admin_user_token():
    """Generate admin JWT token"""
    user_data = {
        "sub": "adminuser",
        "email": "admin@example.com",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return create_access_token(data=user_data)


@pytest.fixture
async def test_user_in_db(test_db: AsyncSession):
    """Create test user in database"""
    user = User(
        username="dbtest",
        email="dbtest@example.com",
        full_name="DB Test User",
        hashed_password=get_password_hash("TestPassword123!"),
        role=UserRole.BASIC,
        is_active=True
    )
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    return user


def assert_api_response(response, expected_status: int = 200, required_fields: list = None):
    """Helper function to assert API response format"""
    assert response.status_code == expected_status
    
    if expected_status == 200 and required_fields:
        data = response.json()
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"


def create_mock_file_upload(filename: str = "test.txt", content: str = "test content"):
    """Create mock file upload for testing"""
    import io
    return {
        "file": (filename, io.BytesIO(content.encode()), "text/plain")
    }