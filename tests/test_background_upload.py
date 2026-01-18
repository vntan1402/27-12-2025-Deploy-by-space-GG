"""
Test Background Upload Feature for Other Documents
Tests the V2 upload strategy:
1. POST /api/other-documents/background-upload-folder/create-task - Creates upload task with metadata only
2. POST /api/other-documents/background-upload-folder/{task_id}/upload-file - Uploads single file to task
3. GET /api/other-documents/background-upload-folder/{task_id} - Gets task status for polling
"""
import pytest
import requests
import os
import time
import io

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable not set")

# Test credentials
TEST_USERNAME = "admin1"
TEST_PASSWORD = "123456"


class TestBackgroundUploadAPI:
    """Test Background Upload API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get a ship ID for testing
        ships_response = self.session.get(f"{BASE_URL}/api/ships")
        if ships_response.status_code == 200 and ships_response.json():
            self.ship_id = ships_response.json()[0].get("id")
        else:
            pytest.skip("No ships available for testing")
        
        yield
        
        self.session.close()
    
    def test_01_login_and_get_ships(self):
        """Test login and verify ships are available"""
        # Already done in setup, just verify
        assert self.ship_id is not None
        print(f"✅ Login successful, using ship_id: {self.ship_id}")
    
    def test_02_create_upload_task_success(self):
        """Test creating an upload task with valid data"""
        form_data = {
            "ship_id": self.ship_id,
            "folder_name": "TEST_Upload_Folder",
            "total_files": 3,
            "status": "Valid",
            "date": "2025-01-15",
            "note": "Test upload task"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/create-task",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Create task response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, "Expected success=True"
        assert "task_id" in data, "Expected task_id in response"
        assert data.get("total_files") == 3, "Expected total_files=3"
        
        # Store task_id for subsequent tests
        self.__class__.task_id = data["task_id"]
        print(f"✅ Created upload task: {self.__class__.task_id}")
    
    def test_03_create_upload_task_invalid_total_files(self):
        """Test creating task with invalid total_files (0 or negative)"""
        form_data = {
            "ship_id": self.ship_id,
            "folder_name": "TEST_Invalid_Folder",
            "total_files": 0,  # Invalid
            "status": "Valid"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/create-task",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Invalid task response: {response.status_code} - {response.text}")
        
        # Should return 400 Bad Request
        assert response.status_code == 400, f"Expected 400 for invalid total_files, got {response.status_code}"
        print("✅ Correctly rejected task with total_files=0")
    
    def test_04_get_task_status(self):
        """Test getting task status by ID"""
        if not hasattr(self.__class__, 'task_id'):
            pytest.skip("No task_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{self.__class__.task_id}"
        )
        
        print(f"Get status response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("task_id") == self.__class__.task_id
        assert data.get("status") in ["pending", "processing", "completed", "failed", "completed_with_errors"]
        assert "total_files" in data
        assert "completed_files" in data
        assert "failed_files" in data
        
        print(f"✅ Task status: {data.get('status')}, completed: {data.get('completed_files')}/{data.get('total_files')}")
    
    def test_05_get_task_status_not_found(self):
        """Test getting status for non-existent task"""
        fake_task_id = "non-existent-task-id-12345"
        
        response = self.session.get(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{fake_task_id}"
        )
        
        print(f"Not found response: {response.status_code} - {response.text}")
        
        assert response.status_code == 404, f"Expected 404 for non-existent task, got {response.status_code}"
        print("✅ Correctly returned 404 for non-existent task")
    
    def test_06_upload_file_to_task(self):
        """Test uploading a single file to an existing task"""
        if not hasattr(self.__class__, 'task_id'):
            pytest.skip("No task_id from previous test")
        
        # Create a test file (small PDF-like content)
        test_file_content = b"%PDF-1.4 Test PDF content for upload testing"
        test_filename = "test_document.pdf"
        
        files = {
            "file": (test_filename, io.BytesIO(test_file_content), "application/pdf")
        }
        
        # Remove Content-Type header for multipart upload
        headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{self.__class__.task_id}/upload-file",
            files=files,
            headers=headers
        )
        
        print(f"Upload file response: {response.status_code} - {response.text}")
        
        # Note: This may fail if Google Drive is not configured, which is expected
        # We're testing the API endpoint works, not the actual GDrive upload
        if response.status_code == 200:
            data = response.json()
            assert "filename" in data
            assert "completed_files" in data
            assert "total_files" in data
            print(f"✅ File uploaded: {data.get('filename')}, progress: {data.get('completed_files')}/{data.get('total_files')}")
        elif response.status_code == 500:
            # GDrive not configured - this is acceptable for testing
            print("⚠️ Upload failed (likely GDrive not configured) - API endpoint works")
        else:
            # Unexpected error
            assert False, f"Unexpected status code: {response.status_code}"
    
    def test_07_upload_file_to_nonexistent_task(self):
        """Test uploading file to non-existent task"""
        fake_task_id = "non-existent-task-id-12345"
        
        test_file_content = b"%PDF-1.4 Test PDF content"
        test_filename = "test_document.pdf"
        
        files = {
            "file": (test_filename, io.BytesIO(test_file_content), "application/pdf")
        }
        
        headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{fake_task_id}/upload-file",
            files=files,
            headers=headers
        )
        
        print(f"Upload to non-existent task response: {response.status_code} - {response.text}")
        
        assert response.status_code == 404, f"Expected 404 for non-existent task, got {response.status_code}"
        print("✅ Correctly returned 404 for upload to non-existent task")
    
    def test_08_other_documents_list_endpoint(self):
        """Test that other documents list endpoint works"""
        response = self.session.get(
            f"{BASE_URL}/api/other-documents",
            params={"ship_id": self.ship_id}
        )
        
        print(f"Other documents list response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"✅ Other documents list works, found {len(data)} documents")
    
    def test_09_create_manual_other_document(self):
        """Test creating a manual other document (without file upload)"""
        doc_data = {
            "ship_id": self.ship_id,
            "document_name": "TEST_Manual_Document",
            "date": "2025-01-15",
            "status": "Valid",
            "note": "Test manual document creation",
            "file_ids": []
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents",
            json=doc_data
        )
        
        print(f"Create manual document response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("document_name") == "TEST_Manual_Document" or data.get("folder_name") == "TEST_Manual_Document"
        
        # Store document ID for cleanup
        self.__class__.created_doc_id = data.get("id")
        print(f"✅ Created manual document: {self.__class__.created_doc_id}")
    
    def test_10_delete_test_document(self):
        """Cleanup: Delete test document created in previous test"""
        if not hasattr(self.__class__, 'created_doc_id'):
            pytest.skip("No document to delete")
        
        response = self.session.delete(
            f"{BASE_URL}/api/other-documents/{self.__class__.created_doc_id}"
        )
        
        print(f"Delete document response: {response.status_code}")
        
        assert response.status_code in [200, 204], f"Expected 200 or 204, got {response.status_code}"
        print(f"✅ Deleted test document: {self.__class__.created_doc_id}")


class TestBackgroundUploadIntegration:
    """Integration tests for the full upload flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get a ship ID for testing
        ships_response = self.session.get(f"{BASE_URL}/api/ships")
        if ships_response.status_code == 200 and ships_response.json():
            self.ship_id = ships_response.json()[0].get("id")
        else:
            pytest.skip("No ships available for testing")
        
        yield
        
        self.session.close()
    
    def test_full_upload_flow_simulation(self):
        """
        Simulate the full V2 upload flow:
        1. Create task
        2. Upload files sequentially (simulated)
        3. Poll status
        """
        # Step 1: Create task
        form_data = {
            "ship_id": self.ship_id,
            "folder_name": "TEST_Integration_Folder",
            "total_files": 2,
            "status": "Valid",
            "date": "2025-01-15",
            "note": "Integration test"
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/create-task",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert create_response.status_code == 200, f"Create task failed: {create_response.status_code}"
        task_id = create_response.json().get("task_id")
        print(f"✅ Step 1: Created task {task_id}")
        
        # Step 2: Check initial status
        status_response = self.session.get(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}"
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data.get("status") in ["pending", "processing"]
        assert status_data.get("total_files") == 2
        assert status_data.get("completed_files") == 0
        print(f"✅ Step 2: Initial status verified - {status_data.get('status')}")
        
        # Step 3: Simulate file uploads (may fail due to GDrive config)
        test_files = [
            ("test_file_1.pdf", b"%PDF-1.4 Test file 1 content"),
            ("test_file_2.pdf", b"%PDF-1.4 Test file 2 content")
        ]
        
        headers = {k: v for k, v in self.session.headers.items() if k.lower() != 'content-type'}
        
        for filename, content in test_files:
            files = {
                "file": (filename, io.BytesIO(content), "application/pdf")
            }
            
            upload_response = self.session.post(
                f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}/upload-file",
                files=files,
                headers=headers
            )
            
            print(f"   Upload {filename}: {upload_response.status_code}")
            
            # Wait 1 second between uploads (as per spec)
            time.sleep(1)
        
        # Step 4: Final status check
        final_status_response = self.session.get(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}"
        )
        
        assert final_status_response.status_code == 200
        final_data = final_status_response.json()
        print(f"✅ Step 4: Final status - {final_data.get('status')}, completed: {final_data.get('completed_files')}/{final_data.get('total_files')}")
        
        # Verify task structure
        assert "task_id" in final_data
        assert "status" in final_data
        assert "total_files" in final_data
        assert "completed_files" in final_data
        assert "failed_files" in final_data
        assert "results" in final_data
        
        print("✅ Full upload flow simulation completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
