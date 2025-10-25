# Document Processing Tests
import pytest
from httpx import AsyncClient
import io


@pytest.mark.asyncio
class TestDocumentProcessing:
    async def test_upload_document(self, client: AsyncClient):
        """Test document upload"""
        # Create a test file
        file_content = b"This is a test legal document for processing."
        files = {"file": ("test_document.txt", io.BytesIO(file_content), "text/plain")}
        
        # First need to register and login to get token
        user_data = {
            "username": "doctest",
            "email": "doc@example.com",
            "full_name": "Doc Test",
            "password": "DocPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.post("/documents/upload", files=files, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test_document.txt"
        assert data["status"] == "uploaded"
    
    async def test_process_document(self, client: AsyncClient):
        """Test document processing"""
        # Register user and get token
        user_data = {
            "username": "processtest",
            "email": "process@example.com",
            "full_name": "Process Test", 
            "password": "ProcessPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Upload document first
        file_content = b"This contract contains obligations and responsibilities."
        files = {"file": ("contract.txt", io.BytesIO(file_content), "text/plain")}
        upload_response = await client.post("/documents/upload", files=files, headers=headers)
        document_id = upload_response.json()["document_id"]
        
        # Process document
        response = await client.post(f"/documents/{document_id}/process", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert "analysis" in data
    
    async def test_unauthorized_upload(self, client: AsyncClient):
        """Test unauthorized document upload"""
        file_content = b"This should not be uploaded without auth."
        files = {"file": ("unauthorized.txt", io.BytesIO(file_content), "text/plain")}
        
        response = await client.post("/documents/upload", files=files)
        assert response.status_code == 401