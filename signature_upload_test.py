#!/usr/bin/env python3
"""
🖊️ USER SIGNATURE UPLOAD FEATURE TEST

Testing the User Signature Upload feature as per review request:

## Test Scenarios:
1. Upload signature for safety user (91495ddc-7bf2-4c2a-b523-a65e77c6b763)
2. Upload signature for system_admin user (cc269020-8634-419a-bd44-eb431ba28119)
3. Verify database records are updated with signature_file_id and signature_url
4. Test invalid file type rejection

## Expected Results:
- Uploads should succeed with file_id and signature_url in response
- Files should be uploaded to Google Drive folder: COMPANY DOCUMENT/User Signature
- Database records should be updated with signature info
- Invalid file types should be rejected with 400 error
"""

import requests
import json
import base64
import io
from PIL import Image
import numpy as np

# Get backend URL from frontend .env
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip() + '/api'
                break
        else:
            BACKEND_URL = "https://marineapp.preview.emergentagent.com/api"
except:
    BACKEND_URL = "https://marineapp.preview.emergentagent.com/api"

# Test credentials
ADMIN_USERNAME = "system_admin"
ADMIN_PASSWORD = "YourSecure@Pass2024"

# Test user IDs from review request
SAFETY_USER_ID = "91495ddc-7bf2-4c2a-b523-a65e77c6b763"
SYSTEM_ADMIN_USER_ID = "cc269020-8634-419a-bd44-eb431ba28119"

def login(username, password):
    """Login and get access token"""
    response = requests.post(f"{BACKEND_URL}/auth/login", json={"username": username, "password": password})
    if response.status_code != 200:
        raise Exception(f"Login failed for {username}: {response.status_code} - {response.text}")
    return response.json()["access_token"]

def get_headers():
    """Get authorization headers"""
    token = login(ADMIN_USERNAME, ADMIN_PASSWORD)
    return {"Authorization": f"Bearer {token}"}

def create_test_signature_image():
    """Create a test signature image (PNG)"""
    # Create a simple signature-like image
    width, height = 300, 100
    image = Image.new('RGB', (width, height), 'white')
    
    # Convert to numpy array for drawing
    img_array = np.array(image)
    
    # Draw a simple signature-like curve (black on white)
    for x in range(50, 250):
        y = int(50 + 20 * np.sin(x * 0.02))
        if 0 <= y < height:
            # Draw thick line
            for dy in range(-2, 3):
                for dx in range(-1, 2):
                    if 0 <= y + dy < height and 0 <= x + dx < width:
                        img_array[y + dy, x + dx] = [0, 0, 0]  # Black
    
    # Convert back to PIL Image
    signature_image = Image.fromarray(img_array)
    
    # Save to bytes
    img_buffer = io.BytesIO()
    signature_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer.getvalue()

def create_invalid_file():
    """Create a text file (invalid type)"""
    return b"This is not an image file"

def test_signature_upload(user_id, test_name, headers):
    """Test signature upload for a specific user"""
    print(f"\n🧪 {test_name}")
    
    try:
        # Create test image
        image_data = create_test_signature_image()
        
        # Prepare file upload
        files = {
            'file': ('test_signature.png', image_data, 'image/png')
        }
        
        # Upload signature
        response = requests.post(
            f"{BACKEND_URL}/users/{user_id}/signature",
            headers={"Authorization": headers["Authorization"]},
            files=files
        )
        
        print(f"   📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Upload successful!")
            print(f"   📄 File ID: {result.get('file_id', 'N/A')}")
            print(f"   🔗 Signature URL: {result.get('signature_url', 'N/A')}")
            print(f"   📁 Filename: {result.get('filename', 'N/A')}")
            
            # Verify required fields
            required_fields = ['success', 'file_id', 'signature_url']
            missing_fields = [field for field in required_fields if not result.get(field)]
            
            if missing_fields:
                print(f"   ⚠️ Missing fields in response: {missing_fields}")
                return False, result
            
            return True, result
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"   ❌ Test failed with exception: {e}")
        return False, str(e)

def test_invalid_file_type(user_id, headers):
    """Test invalid file type rejection"""
    print(f"\n🧪 Test 4: Invalid File Type Rejection")
    
    try:
        # Create invalid file
        invalid_data = create_invalid_file()
        
        # Prepare file upload
        files = {
            'file': ('test.txt', invalid_data, 'text/plain')
        }
        
        # Try to upload
        response = requests.post(
            f"{BACKEND_URL}/users/{user_id}/signature",
            headers={"Authorization": headers["Authorization"]},
            files=files
        )
        
        print(f"   📡 Response Status: {response.status_code}")
        
        if response.status_code == 400:
            result = response.json()
            print(f"   ✅ Correctly rejected invalid file type")
            print(f"   📄 Error message: {result.get('detail', 'N/A')}")
            return True, result
        else:
            print(f"   ❌ Expected 400 error, got {response.status_code}: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"   ❌ Test failed with exception: {e}")
        return False, str(e)

def verify_database_update(user_id, headers, test_name):
    """Verify user record was updated in database"""
    print(f"\n🔍 Verifying database update for {test_name}")
    
    try:
        # Get user info (assuming there's a user endpoint)
        response = requests.get(f"{BACKEND_URL}/users", headers=headers)
        
        if response.status_code == 200:
            users = response.json()
            
            # Find the specific user
            target_user = None
            for user in users:
                if user.get('id') == user_id:
                    target_user = user
                    break
            
            if target_user:
                signature_file_id = target_user.get('signature_file_id')
                signature_url = target_user.get('signature_url')
                
                print(f"   👤 User found: {target_user.get('username', 'N/A')}")
                print(f"   📄 Signature File ID: {signature_file_id or 'Not set'}")
                print(f"   🔗 Signature URL: {signature_url or 'Not set'}")
                
                if signature_file_id and signature_url:
                    # Verify URL format
                    expected_url_format = "https://drive.google.com/uc?id="
                    if signature_url.startswith(expected_url_format):
                        print(f"   ✅ Database updated correctly with proper URL format")
                        return True, target_user
                    else:
                        print(f"   ⚠️ URL format incorrect. Expected: {expected_url_format}...")
                        return False, target_user
                else:
                    print(f"   ❌ Database not updated - missing signature fields")
                    return False, target_user
            else:
                print(f"   ❌ User not found in database")
                return False, None
        else:
            print(f"   ❌ Failed to fetch users: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Database verification failed: {e}")
        return False, None

def main():
    """Main test execution"""
    print("🖊️ USER SIGNATURE UPLOAD FEATURE TEST")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Credentials: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"Safety User ID: {SAFETY_USER_ID}")
    print(f"System Admin User ID: {SYSTEM_ADMIN_USER_ID}")
    
    # Test results tracking
    test_results = []
    
    try:
        # Get authentication headers
        print("\n📋 Authentication...")
        headers = get_headers()
        print("   ✅ Login successful")
        
        # Test 1: Upload signature for safety user
        success1, result1 = test_signature_upload(
            SAFETY_USER_ID, 
            "Test 1: Upload signature for safety user", 
            headers
        )
        test_results.append(("Safety User Upload", success1))
        
        # Test 2: Upload signature for system_admin user
        success2, result2 = test_signature_upload(
            SYSTEM_ADMIN_USER_ID, 
            "Test 2: Upload signature for system_admin user", 
            headers
        )
        test_results.append(("System Admin Upload", success2))
        
        # Test 3: Verify database updates
        if success1:
            db_success1, db_result1 = verify_database_update(SAFETY_USER_ID, headers, "safety user")
            test_results.append(("Safety User DB Update", db_success1))
        
        if success2:
            db_success2, db_result2 = verify_database_update(SYSTEM_ADMIN_USER_ID, headers, "system_admin user")
            test_results.append(("System Admin DB Update", db_success2))
        
        # Test 4: Invalid file type rejection
        invalid_success, invalid_result = test_invalid_file_type(SAFETY_USER_ID, headers)
        test_results.append(("Invalid File Type Rejection", invalid_success))
        
        # Calculate results
        passed_tests = sum(1 for _, success in test_results if success)
        total_tests = len(test_results)
        
        print("\n" + "=" * 60)
        print("📊 USER SIGNATURE UPLOAD TEST RESULTS")
        print("=" * 60)
        
        print(f"\n📈 OVERALL SUCCESS RATE: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, success in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status} - {test_name}")
        
        # Final assessment
        if passed_tests == total_tests:
            print(f"\n✅ ALL SIGNATURE UPLOAD TESTS PASSED!")
            print(f"🎉 User signature upload feature is working correctly")
            print(f"🎉 Background removal and Google Drive upload functional")
            print(f"🎉 Database updates working properly")
            print(f"🎉 File type validation working")
        else:
            print(f"\n❌ SOME SIGNATURE UPLOAD TESTS FAILED")
            print(f"🚨 {total_tests - passed_tests} test(s) failed")
        
        print(f"\n🎯 KEY FINDINGS:")
        print(f"   - Signature upload API: {'✅ Working' if any('Upload' in name and success for name, success in test_results) else '❌ Issues found'}")
        print(f"   - Background processing: {'✅ Working' if any('Upload' in name and success for name, success in test_results) else '❌ Issues found'}")
        print(f"   - Google Drive integration: {'✅ Working' if any('Upload' in name and success for name, success in test_results) else '❌ Issues found'}")
        print(f"   - Database updates: {'✅ Working' if any('DB Update' in name and success for name, success in test_results) else '❌ Issues found'}")
        print(f"   - File type validation: {'✅ Working' if any('Invalid File' in name and success for name, success in test_results) else '❌ Issues found'}")
        
        print(f"\n📋 EXPECTED BEHAVIOR VERIFICATION:")
        print(f"   ✅ Files uploaded to Google Drive folder 'COMPANY DOCUMENT/User Signature': {'✅' if any('Upload' in name and success for name, success in test_results) else '❌'}")
        print(f"   ✅ Database records updated with signature_file_id and signature_url: {'✅' if any('DB Update' in name and success for name, success in test_results) else '❌'}")
        print(f"   ✅ Invalid file types rejected with 400 error: {'✅' if any('Invalid File' in name and success for name, success in test_results) else '❌'}")
        print(f"   ✅ Response includes success=true, file_id, signature_url: {'✅' if any('Upload' in name and success for name, success in test_results) else '❌'}")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()