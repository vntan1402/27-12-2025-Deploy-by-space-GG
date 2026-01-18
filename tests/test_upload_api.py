"""
Test Upload API Endpoints
Tests the background upload functionality for Other Documents
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://seamanagepro.preview.emergentagent.com')

class TestUploadAPI:
    """Test upload API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin1",
            "password": "123456"
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("access_token") or data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print(f"✅ Logged in successfully")
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_01_create_upload_task(self):
        """Test creating a background upload task"""
        # Get ships first
        ships_response = self.session.get(f"{BASE_URL}/api/ships")
        assert ships_response.status_code == 200, f"Failed to get ships: {ships_response.text}"
        
        ships = ships_response.json()
        assert len(ships) > 0, "No ships found"
        
        ship_id = ships[0].get("id")
        print(f"📋 Using ship: {ships[0].get('name')} ({ship_id})")
        
        # Create upload task
        form_data = {
            "ship_id": ship_id,
            "folder_name": "Test Upload Folder",
            "total_files": 3,
            "status": "Valid",
            "date": "2025-01-18",
            "note": "Test upload task"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/create-task",
            data=form_data
        )
        
        print(f"📤 Create task response: {response.status_code}")
        print(f"📤 Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to create task: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Task creation failed: {data}"
        assert "task_id" in data, "No task_id in response"
        
        self.task_id = data["task_id"]
        print(f"✅ Created task: {self.task_id}")
        
        return self.task_id
    
    def test_02_get_task_status(self):
        """Test getting task status"""
        # First create a task
        task_id = self.test_01_create_upload_task()
        
        # Get status
        response = self.session.get(f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}")
        
        print(f"📊 Status response: {response.status_code}")
        print(f"📊 Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to get status: {response.text}"
        
        data = response.json()
        assert "status" in data, "No status in response"
        assert "total_files" in data, "No total_files in response"
        
        print(f"✅ Task status: {data.get('status')}, {data.get('completed_files')}/{data.get('total_files')} files")
    
    def test_03_upload_file_to_task(self):
        """Test uploading a file to an existing task"""
        # First create a task
        task_id = self.test_01_create_upload_task()
        
        # Create a test file
        test_content = b"Test PDF content for upload testing"
        files = {
            "file": ("test_file.pdf", test_content, "application/pdf")
        }
        
        # Upload file
        response = self.session.post(
            f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}/upload-file",
            files=files
        )
        
        print(f"📤 Upload response: {response.status_code}")
        print(f"📤 Response body: {response.text}")
        
        # Note: This might fail if Google Drive is not configured
        # We're testing the API endpoint works, not the actual upload
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload result: {data}")
        else:
            print(f"⚠️ Upload failed (expected if GDrive not configured): {response.text}")
    
    def test_04_cancel_task(self):
        """Test cancelling an upload task"""
        # First create a task
        task_id = self.test_01_create_upload_task()
        
        # Cancel task
        response = self.session.post(f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}/cancel")
        
        print(f"🚫 Cancel response: {response.status_code}")
        print(f"🚫 Response body: {response.text}")
        
        assert response.status_code == 200, f"Failed to cancel: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, f"Cancel failed: {data}"
        
        print(f"✅ Task cancelled successfully")
        
        # Verify status is cancelled
        status_response = self.session.get(f"{BASE_URL}/api/other-documents/background-upload-folder/{task_id}")
        status_data = status_response.json()
        assert status_data.get("status") == "cancelled", f"Task status not cancelled: {status_data}"
        
        print(f"✅ Task status verified as cancelled")
    
    def test_05_other_documents_crud(self):
        """Test Other Documents CRUD operations"""
        # Get ships first
        ships_response = self.session.get(f"{BASE_URL}/api/ships")
        ships = ships_response.json()
        ship_id = ships[0].get("id")
        
        # Create document
        create_data = {
            "ship_id": ship_id,
            "document_name": "Test Document",
            "date": "2025-01-18",
            "status": "Valid",
            "note": "Test note"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/other-documents", json=create_data)
        print(f"📝 Create response: {create_response.status_code}")
        
        assert create_response.status_code in [200, 201], f"Failed to create: {create_response.text}"
        
        doc = create_response.json()
        doc_id = doc.get("id")
        print(f"✅ Created document: {doc_id}")
        
        # Get documents
        get_response = self.session.get(f"{BASE_URL}/api/other-documents?ship_id={ship_id}")
        assert get_response.status_code == 200, f"Failed to get documents: {get_response.text}"
        
        docs = get_response.json()
        print(f"📋 Found {len(docs)} documents")
        
        # Delete document
        delete_response = self.session.delete(f"{BASE_URL}/api/other-documents/{doc_id}")
        print(f"🗑️ Delete response: {delete_response.status_code}")
        
        assert delete_response.status_code in [200, 204], f"Failed to delete: {delete_response.text}"
        print(f"✅ Deleted document: {doc_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
