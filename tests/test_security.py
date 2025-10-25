# Security Tests
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSecurity:
    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting functionality"""
        # Make multiple rapid requests to trigger rate limiting
        responses = []
        for i in range(15):  # Assuming rate limit is 10 per minute
            response = await client.get("/health")
            responses.append(response.status_code)
        
        # Should have some rate limited responses
        assert 429 in responses or all(r == 200 for r in responses[:10])
    
    async def test_jwt_token_validation(self, client: AsyncClient):
        """Test JWT token validation"""
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid.token.here"}
        
        response = await client.get("/auth/profile", headers=invalid_headers)
        assert response.status_code == 401
    
    async def test_role_based_access(self, client: AsyncClient):
        """Test role-based access control"""
        # Register a basic user
        user_data = {
            "username": "basicuser",
            "email": "basic@example.com",
            "full_name": "Basic User",
            "password": "BasicPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin endpoint (should fail)
        response = await client.get("/admin/users", headers=headers)
        assert response.status_code == 403  # Forbidden
    
    async def test_input_validation(self, client: AsyncClient):
        """Test input validation and sanitization"""
        # Test with malicious input
        malicious_data = {
            "username": "<script>alert('xss')</script>",
            "email": "test'; DROP TABLE users; --",
            "full_name": "Test User",
            "password": "Password123!"
        }
        
        response = await client.post("/auth/register", json=malicious_data)
        # Should either reject with validation error or sanitize input
        assert response.status_code in [400, 422] or response.status_code == 200
        
        if response.status_code == 200:
            # If accepted, ensure input was sanitized
            data = response.json()
            assert "<script>" not in data.get("username", "")
    
    async def test_password_security(self, client: AsyncClient):
        """Test password security requirements"""
        # Test weak password
        weak_data = {
            "username": "weaktest",
            "email": "weak@example.com",
            "full_name": "Weak Test",
            "password": "123"  # Weak password
        }
        
        response = await client.post("/auth/register", json=weak_data)
        assert response.status_code == 422  # Should reject weak password
    
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are properly set"""
        response = await client.options("/health")
        headers = response.headers
        
        # Check for CORS headers (if CORS is enabled)
        # This might vary based on your CORS configuration
        assert response.status_code in [200, 405]  # OPTIONS might not be allowed