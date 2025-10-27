#!/usr/bin/env python3
"""
Direct Other Documents Upload Endpoint Testing
Testing the endpoints directly to see what happens without full configuration
"""

import requests
import json
import os
import tempfile
import time
from datetime import datetime

# Configuration
BACKEND_URL = 'https://shipdoclists.preview.emergentagent.com/api'

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] [{level}] {message}")

def authenticate():
    """Authenticate and get token"""
    try:
        log("🔐 Authenticating with admin1/123456...")
        
        login_data = {
            "username": "admin1",
            "password": "123456",
            "remember_me": False
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
        log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user", {})
            
            log("✅ Authentication successful")
            log(f"   User ID: {user.get('id')}")
            log(f"   User Role: {user.get('role')}")
            log(f"   Company: {user.get('company')}")
            
            return token
        else:
            log(f"❌ Authentication failed: {response.text}", "ERROR")
            return None
            
    except Exception as e:
        log(f"❌ Authentication error: {str(e)}", "ERROR")
        return None

def get_ship_id(token):
    """Get BROTHER 36 ship ID"""
    try:
        log("🚢 Getting ship ID for BROTHER 36...")
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/ships", headers=headers)
        
        if response.status_code == 200:
            ships = response.json()
            for ship in ships:
                if ship.get("name") == "BROTHER 36":
                    ship_id = ship.get("id")
                    log(f"✅ Found BROTHER 36: {ship_id}")
                    return ship_id
            
            log("❌ BROTHER 36 not found", "ERROR")
            return None
        else:
            log(f"❌ Failed to get ships: {response.status_code}", "ERROR")
            return None
            
    except Exception as e:
        log(f"❌ Error getting ship ID: {str(e)}", "ERROR")
        return None

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        log("📄 Creating test PDF file...")
        
        # Simple PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Other Document Test) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(pdf_content)
            file_path = f.name
        
        log(f"✅ Test PDF created: {file_path} ({len(pdf_content)} bytes)")
        return file_path
        
    except Exception as e:
        log(f"❌ Error creating test PDF: {str(e)}", "ERROR")
        return None

def test_upload_file_only_endpoint(token, ship_id, file_path):
    """Test /api/other-documents/upload-file-only endpoint"""
    try:
        log("📤 Testing /api/other-documents/upload-file-only endpoint...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(file_path, "rb") as f:
            files = {
                "file": ("test_other_document.pdf", f, "application/pdf")
            }
            data = {
                "ship_id": ship_id
            }
            
            log(f"   POST {BACKEND_URL}/other-documents/upload-file-only")
            log(f"   Ship ID: {ship_id}")
            
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/other-documents/upload-file-only",
                files=files,
                data=data,
                headers=headers,
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            log(f"⏱️ Processing time: {processing_time:.1f} seconds")
        
        log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                log("✅ Upload file only endpoint successful")
                log(f"📊 Response: {json.dumps(result, indent=2)}")
                return True, result
            except json.JSONDecodeError as e:
                log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                log(f"   Raw response: {response.text}")
                return False, None
        else:
            log(f"❌ Upload file only endpoint failed: {response.status_code}", "ERROR")
            try:
                error_data = response.json()
                log(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                log(f"   Raw response: {response.text}")
            return False, None
            
    except Exception as e:
        log(f"❌ Error testing upload file only endpoint: {str(e)}", "ERROR")
        return False, None

def test_upload_with_metadata_endpoint(token, ship_id, file_path):
    """Test /api/other-documents/upload endpoint with metadata"""
    try:
        log("📋 Testing /api/other-documents/upload endpoint with metadata...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(file_path, "rb") as f:
            files = {
                "file": ("test_other_document_with_metadata.pdf", f, "application/pdf")
            }
            data = {
                "ship_id": ship_id,
                "document_name": "Test Other Document with Metadata",
                "date": "2024-01-15T10:30:00Z",
                "status": "Valid",
                "note": "This is a test document for Other Documents upload functionality"
            }
            
            log(f"   POST {BACKEND_URL}/other-documents/upload")
            log(f"   Ship ID: {ship_id}")
            log(f"   Document Name: {data['document_name']}")
            
            start_time = time.time()
            response = requests.post(
                f"{BACKEND_URL}/other-documents/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=120
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            log(f"⏱️ Processing time: {processing_time:.1f} seconds")
        
        log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                log("✅ Upload with metadata endpoint successful")
                log(f"📊 Response: {json.dumps(result, indent=2)}")
                return True, result
            except json.JSONDecodeError as e:
                log(f"❌ Invalid JSON response: {str(e)}", "ERROR")
                log(f"   Raw response: {response.text}")
                return False, None
        else:
            log(f"❌ Upload with metadata endpoint failed: {response.status_code}", "ERROR")
            try:
                error_data = response.json()
                log(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                log(f"   Raw response: {response.text}")
            return False, None
            
    except Exception as e:
        log(f"❌ Error testing upload with metadata endpoint: {str(e)}", "ERROR")
        return False, None

def check_backend_logs():
    """Check backend logs for relevant patterns"""
    try:
        log("📋 Checking backend logs...")
        
        log_files = [
            "/var/log/supervisor/backend.out.log",
            "/var/log/supervisor/backend.err.log"
        ]
        
        patterns_to_find = [
            "📤 Uploading other document",
            "📡 Calling Company Apps Script for other document upload",
            "✅ Company Apps Script response received",
            "✅ Other document file uploaded successfully",
            "Company Apps Script URL not configured",
            "AttributeError.*company_id",
            "DualAppsScriptManager",
            "upload_other_document_file"
        ]
        
        all_log_content = ""
        
        for log_file in log_files:
            if os.path.exists(log_file):
                log(f"📄 Checking {log_file}...")
                try:
                    result = os.popen(f"tail -n 100 {log_file}").read()
                    all_log_content += result
                    if result.strip():
                        log(f"   Found {len(result.strip().split(chr(10)))} lines")
                except Exception as e:
                    log(f"   Error reading {log_file}: {e}")
        
        log("🔍 Searching for relevant patterns:")
        for pattern in patterns_to_find:
            if pattern in all_log_content:
                log(f"   ✅ Found: {pattern}")
            else:
                log(f"   ❌ Not found: {pattern}")
        
        # Show recent relevant log lines
        log("\n📋 Recent relevant log lines:")
        lines = all_log_content.split('\n')
        for line in lines[-50:]:  # Last 50 lines
            if any(keyword in line.lower() for keyword in ['other document', 'apps script', 'upload', 'error', 'dual']):
                log(f"   {line}")
        
        return True
        
    except Exception as e:
        log(f"❌ Error checking backend logs: {str(e)}", "ERROR")
        return False

def main():
    """Main test function"""
    try:
        log("🚀 STARTING DIRECT OTHER DOCUMENTS UPLOAD TEST")
        log("=" * 80)
        
        # Step 1: Authentication
        token = authenticate()
        if not token:
            log("❌ Authentication failed - stopping tests")
            return False
        
        # Step 2: Get ship ID
        ship_id = get_ship_id(token)
        if not ship_id:
            log("❌ Ship ID not found - stopping tests")
            return False
        
        # Step 3: Create test file
        file_path = create_test_pdf()
        if not file_path:
            log("❌ Test file creation failed - stopping tests")
            return False
        
        # Step 4: Test upload-file-only endpoint
        success1, result1 = test_upload_file_only_endpoint(token, ship_id, file_path)
        
        # Step 5: Test upload endpoint with metadata
        success2, result2 = test_upload_with_metadata_endpoint(token, ship_id, file_path)
        
        # Step 6: Check backend logs
        check_backend_logs()
        
        # Cleanup
        try:
            os.unlink(file_path)
            log(f"✅ Cleaned up test file: {file_path}")
        except:
            pass
        
        # Summary
        log("\n" + "=" * 80)
        log("📊 TEST SUMMARY")
        log("=" * 80)
        log(f"Upload file only endpoint: {'✅ SUCCESS' if success1 else '❌ FAILED'}")
        log(f"Upload with metadata endpoint: {'✅ SUCCESS' if success2 else '❌ FAILED'}")
        
        if success1 or success2:
            log("✅ At least one endpoint is working")
        else:
            log("❌ Both endpoints failed")
        
        log("=" * 80)
        
        return success1 or success2
        
    except Exception as e:
        log(f"❌ Unexpected error: {str(e)}", "ERROR")
        return False

if __name__ == "__main__":
    main()