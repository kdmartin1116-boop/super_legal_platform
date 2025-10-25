# Authentication Tests
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuth:
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_register_user(self, client: AsyncClient):
        """Test user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "TestPassword123!"
        }
        
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "access_token" in data
    
    async def test_login_user(self, client: AsyncClient):
        """Test user login"""
        # First register a user
        user_data = {
            "username": "logintest",
            "email": "login@example.com", 
            "full_name": "Login Test",
            "password": "LoginPassword123!"
        }
        await client.post("/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_invalid_login(self, client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", json=login_data)
        assert response.status_code == 401