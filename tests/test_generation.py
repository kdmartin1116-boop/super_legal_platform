# Generation Tests
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGeneration:
    async def test_generate_contract(self, client: AsyncClient):
        """Test contract generation"""
        # Register user and get token
        user_data = {
            "username": "gentest",
            "email": "gen@example.com",
            "full_name": "Gen Test",
            "password": "GenPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        generation_request = {
            "document_type": "contract",
            "parties": ["Party A", "Party B"],
            "terms": {
                "subject_matter": "Software Development Services",
                "duration": "6 months",
                "payment_terms": "Monthly payments of $5,000"
            },
            "jurisdiction": "New York"
        }
        
        response = await client.post("/generation/generate", json=generation_request, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "content" in data
        assert data["document_type"] == "contract"
    
    async def test_generate_template(self, client: AsyncClient):
        """Test template generation"""
        # Register user and get token
        user_data = {
            "username": "templatetest",
            "email": "template@example.com",
            "full_name": "Template Test",
            "password": "TemplatePassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        template_request = {
            "template_type": "nda",
            "customizations": {
                "company_name": "Tech Corp",
                "effective_period": "2 years",
                "governing_law": "California"
            }
        }
        
        response = await client.post("/generation/template", json=template_request, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "template_id" in data
        assert "content" in data
        assert data["template_type"] == "nda"
    
    async def test_invalid_generation_request(self, client: AsyncClient):
        """Test invalid generation request"""
        # Register user and get token
        user_data = {
            "username": "invalidtest",
            "email": "invalid@example.com",
            "full_name": "Invalid Test",
            "password": "InvalidPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Missing required fields
        invalid_request = {
            "document_type": "contract"
            # Missing parties and terms
        }
        
        response = await client.post("/generation/generate", json=invalid_request, headers=headers)
        assert response.status_code == 422  # Validation error