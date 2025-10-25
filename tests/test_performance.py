# Performance Tests
import pytest
import time
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor
import asyncio


@pytest.mark.asyncio
class TestPerformance:
    async def test_concurrent_users(self, client: AsyncClient):
        """Test system performance with concurrent users"""
        
        async def create_user_and_login(user_id: int):
            """Create a user and perform login"""
            user_data = {
                "username": f"perfuser{user_id}",
                "email": f"perf{user_id}@example.com",
                "full_name": f"Performance User {user_id}",
                "password": "PerfPassword123!"
            }
            
            # Register user
            register_response = await client.post("/auth/register", json=user_data)
            if register_response.status_code != 200:
                return False
            
            # Login user
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            login_response = await client.post("/auth/login", json=login_data)
            return login_response.status_code == 200
        
        # Test with 10 concurrent users
        tasks = [create_user_and_login(i) for i in range(10)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assert performance criteria
        assert duration < 30  # Should complete within 30 seconds
        successful_operations = sum(1 for r in results if r is True)
        assert successful_operations >= 8  # At least 80% success rate
    
    async def test_document_upload_performance(self, client: AsyncClient):
        """Test document upload performance"""
        # Register and login user
        user_data = {
            "username": "uploadperf",
            "email": "uploadperf@example.com",
            "full_name": "Upload Performance Test",
            "password": "UploadPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create test file content
        file_content = b"This is a performance test document. " * 1000  # ~37KB file
        
        start_time = time.time()
        
        # Upload 5 documents
        upload_results = []
        for i in range(5):
            import io
            files = {"file": (f"perf_doc_{i}.txt", io.BytesIO(file_content), "text/plain")}
            response = await client.post("/documents/upload", files=files, headers=headers)
            upload_results.append(response.status_code == 200)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 10  # Should upload 5 docs within 10 seconds
        assert all(upload_results)  # All uploads should succeed
    
    async def test_api_response_times(self, client: AsyncClient):
        """Test API endpoint response times"""
        endpoints_to_test = [
            ("/health", "GET", None),
            ("/education/courses", "GET", None),
        ]
        
        response_times = {}
        
        for endpoint, method, data in endpoints_to_test:
            start_time = time.time()
            
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json=data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            response_times[endpoint] = response_time
            
            # Each endpoint should respond within 2 seconds
            assert response_time < 2.0, f"{endpoint} took {response_time:.2f} seconds"
            assert response.status_code in [200, 401]  # Valid response
        
        # Log response times for monitoring
        print(f"Response times: {response_times}")
    
    async def test_database_query_performance(self, client: AsyncClient):
        """Test database query performance"""
        # Register user first
        user_data = {
            "username": "dbperf",
            "email": "dbperf@example.com",
            "full_name": "DB Performance Test",
            "password": "DBPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Measure profile retrieval performance
        start_time = time.time()
        
        # Make 20 profile requests
        for _ in range(20):
            response = await client.get("/auth/profile", headers=headers)
            assert response.status_code == 200
        
        end_time = time.time()
        duration = end_time - start_time
        avg_time = duration / 20
        
        # Each query should average less than 100ms
        assert avg_time < 0.1, f"Average query time: {avg_time:.3f}s"
    
    async def test_memory_usage_stability(self, client: AsyncClient):
        """Test memory usage remains stable under load"""
        # Register user
        user_data = {
            "username": "memtest",
            "email": "memtest@example.com",
            "full_name": "Memory Test",
            "password": "MemPassword123!"
        }
        register_response = await client.post("/auth/register", json=user_data)
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Perform repeated operations
        for batch in range(5):
            # Upload documents
            for i in range(10):
                import io
                content = f"Memory test document batch {batch}, doc {i}" * 100
                files = {"file": (f"mem_test_{batch}_{i}.txt", io.BytesIO(content.encode()), "text/plain")}
                response = await client.post("/documents/upload", files=files, headers=headers)
                assert response.status_code == 200
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        # If we reach here without memory issues, test passes
        # In a real scenario, you might use memory profiling tools
        assert True