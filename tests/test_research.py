# Research Tests
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestResearch:
    async def test_search_cases(self, client: AsyncClient):
        """Test case law search"""
        # Register user and get token
        user_data = {
            "username": "researchtest",
            "email": "research@example.com",
            "full_name": "Research Test",
            "password": "ResearchPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        search_params = {
            "query": "contract breach damages",
            "jurisdiction": "federal",
            "date_range": {"start": "2020-01-01", "end": "2024-01-01"},
            "limit": 10
        }
        
        response = await client.post("/research/cases/search", json=search_params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total_count" in data
        assert isinstance(data["results"], list)
    
    async def test_search_statutes(self, client: AsyncClient):
        """Test statute search"""
        # Register user and get token
        user_data = {
            "username": "statutetest",
            "email": "statute@example.com",
            "full_name": "Statute Test",
            "password": "StatutePassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        search_params = {
            "query": "consumer protection",
            "jurisdiction": "california",
            "category": "commercial"
        }
        
        response = await client.post("/research/statutes/search", json=search_params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
    
    async def test_get_case_details(self, client: AsyncClient):
        """Test getting case details"""
        # Register user and get token
        user_data = {
            "username": "casedetailtest",
            "email": "casedetail@example.com",
            "full_name": "Case Detail Test",
            "password": "CaseDetailPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Mock case ID
        case_id = "case_123456"
        
        response = await client.get(f"/research/cases/{case_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert "title" in data
        assert "summary" in data
    
    async def test_save_research(self, client: AsyncClient):
        """Test saving research results"""
        # Register user and get token
        user_data = {
            "username": "savetest",
            "email": "save@example.com",
            "full_name": "Save Test",
            "password": "SavePassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        save_data = {
            "type": "case",
            "item_id": "case_123456",
            "notes": "Important precedent for breach of contract cases",
            "tags": ["contract", "breach", "damages"]
        }
        
        response = await client.post("/research/save", json=save_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert "saved_id" in data