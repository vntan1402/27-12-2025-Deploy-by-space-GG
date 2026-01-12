"""
Backend API Tests for Ship Management System
Tests authentication and basic API functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://marineapp.preview.emergentagent.com').rstrip('/')


class TestAuthAPI:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin1", "password": "123456"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["username"] == "admin1", "Username should match"
        assert data["user"]["role"] == "admin", "Role should be admin"
        assert len(data["access_token"]) > 0, "Token should not be empty"
        
        print(f"✅ Login successful for admin1")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "invalid_user", "password": "wrong_password"},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid credentials correctly rejected")
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "", "password": ""},
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 401 or 422 (validation error)
        assert response.status_code in [401, 422], f"Expected 401 or 422, got {response.status_code}"
        print(f"✅ Empty credentials correctly rejected")


class TestVerifyToken:
    """Token verification tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin1", "password": "123456"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_verify_token_valid(self, auth_token):
        """Test token verification with valid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/verify-token",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("valid") == True, "Token should be valid"
        assert "user" in data, "Response should contain user info"
        print(f"✅ Token verification successful")
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/verify-token",
            headers={
                "Authorization": "Bearer invalid_token_here",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Invalid token correctly rejected")


class TestCompaniesAPI:
    """Companies endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin1", "password": "123456"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_companies(self, auth_token):
        """Test getting companies list"""
        response = requests.get(
            f"{BASE_URL}/api/companies",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ Companies API returned {len(data)} companies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
