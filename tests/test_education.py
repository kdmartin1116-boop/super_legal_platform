# Education Tests
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEducation:
    async def test_get_courses(self, client: AsyncClient):
        """Test getting available courses"""
        response = await client.get("/education/courses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_course_content(self, client: AsyncClient):
        """Test getting course content"""
        # Register user and get token
        user_data = {
            "username": "edutest",
            "email": "edu@example.com",
            "full_name": "Edu Test",
            "password": "EduPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/education/courses/contract-basics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "course_id" in data
        assert "title" in data
        assert "modules" in data
    
    async def test_track_progress(self, client: AsyncClient):
        """Test progress tracking"""
        # Register user and get token
        user_data = {
            "username": "progresstest",
            "email": "progress@example.com",
            "full_name": "Progress Test",
            "password": "ProgressPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        progress_data = {
            "course_id": "contract-basics",
            "module_id": "introduction",
            "completion_percentage": 75,
            "time_spent": 1800  # 30 minutes in seconds
        }
        
        response = await client.post("/education/progress", json=progress_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
    
    async def test_get_user_progress(self, client: AsyncClient):
        """Test getting user progress"""
        # Register user and get token
        user_data = {
            "username": "getprogresstest",
            "email": "getprogress@example.com",
            "full_name": "Get Progress Test",
            "password": "GetProgressPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await client.get("/education/progress", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)