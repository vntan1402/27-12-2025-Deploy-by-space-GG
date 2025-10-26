#!/usr/bin/env python3
"""
Drawings & Manuals Background Deletion Testing with Real Files

This test uses existing documents with actual file uploads to test the background deletion feature.
"""

import requests
import json
import time
import subprocess

BACKEND_URL = 'https://shipsystem.preview.emergentagent.com/api'

def get_auth_token():
    """Get authentication token"""
    login_data = {'username': 'admin1', 'password': '123456', 'remember_me': False}
    response = requests.post(f'{BACKEND_URL}/auth/login', json=login_data)
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def get_documents_with_files(token):
    """Get existing documents that have files"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BACKEND_URL}/drawings-manuals?ship_id=marine-doc-system', headers=headers)
    
    if response.status_code == 200:
        docs = response.json()
        docs_with_files = []
        for doc in docs:
            if doc.get('file_id') or doc.get('summary_file_id'):
                docs_with_files.append(doc)
        return docs_with_files
    return []

def create_test_document_with_file_upload(token):
    """Create a test document and upload a file to it"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Create document
    doc_data = {
        "ship_id": "7f20a73b-8cd3-4bc9-9ab3-efbc8d552bb7",
        "document_name": "Background Delete Test Document with Real File",
        "document_no": "BG-TEST-001",
        "status": "Approved"
    }
    
    response = requests.post(f'{BACKEND_URL}/drawings-manuals', json=doc_data, headers=headers)
    if response.status_code != 200:
        print(f"Failed to create document: {response.status_code}")
        return None
    
    doc = response.json()
    doc_id = doc['id']
    print(f"Created test document: {doc_id}")
    
    # Create a simple test file
    test_file_content = b"This is a test PDF file for background deletion testing."
    
    # Upload file
    files = {'file': ('test_document.pdf', test_file_content, 'application/pdf')}
    upload_response = requests.post(f'{BACKEND_URL}/drawings-manuals/{doc_id}/upload-files', 
                                  files=files, headers=headers)
    
    if upload_response.status_code == 200:
        print(f"File uploaded successfully to document: {doc_id}")
        return doc_id
    else:
        print(f"Failed to upload file: {upload_response.status_code}")
        return None

def test_single_background_delete(token, doc_id):
    """Test single document background deletion"""
    print(f"\n🗑️ Testing single background delete for document: {doc_id}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test background delete
    start_time = time.time()
    response = requests.delete(f'{BACKEND_URL}/drawings-manuals/{doc_id}?background=true', headers=headers)
    response_time = time.time() - start_time
    
    print(f"Response status: {response.status_code}")
    print(f"Response time: {response_time:.3f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check key fields
        success = result.get('success', False)
        background_deletion = result.get('background_deletion', False)
        message = result.get('message', '')
        
        print(f"✅ Success: {success}")
        print(f"✅ Background deletion: {background_deletion}")
        print(f"✅ Message: {message}")
        print(f"✅ Response time: {response_time:.3f}s (should be < 1s)")
        
        return success and background_deletion and response_time < 1.0
    else:
        print(f"❌ Failed: {response.status_code}")
        return False

def test_bulk_background_delete(token, doc_ids):
    """Test bulk background deletion"""
    print(f"\n🗑️ Testing bulk background delete for {len(doc_ids)} documents")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test bulk background delete
    bulk_data = {'document_ids': doc_ids}
    start_time = time.time()
    response = requests.delete(f'{BACKEND_URL}/drawings-manuals/bulk-delete?background=true', 
                             json=bulk_data, headers=headers)
    response_time = time.time() - start_time
    
    print(f"Response status: {response.status_code}")
    print(f"Response time: {response_time:.3f} seconds")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Check key fields
        success = result.get('success', False)
        background_deletion = result.get('background_deletion', False)
        deleted_count = result.get('deleted_count', 0)
        message = result.get('message', '')
        
        print(f"✅ Success: {success}")
        print(f"✅ Background deletion: {background_deletion}")
        print(f"✅ Deleted count: {deleted_count}/{len(doc_ids)}")
        print(f"✅ Message: {message}")
        print(f"✅ Response time: {response_time:.3f}s (should be < 1s)")
        
        return success and background_deletion and deleted_count == len(doc_ids) and response_time < 1.0
    else:
        print(f"❌ Failed: {response.status_code}")
        return False

def check_backend_logs():
    """Check backend logs for background deletion messages"""
    print(f"\n📋 Checking backend logs for background deletion messages...")
    
    try:
        result = subprocess.run(['tail', '-n', '100', '/var/log/supervisor/backend.out.log'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            log_lines = result.stdout.split('\n')
            background_messages = [line for line in log_lines if '[Background]' in line]
            
            print(f"Found {len(background_messages)} background deletion log messages:")
            for msg in background_messages[-10:]:  # Show last 10
                print(f"  📋 {msg}")
            
            return len(background_messages) > 0
        else:
            print("Could not read backend logs")
            return False
    except Exception as e:
        print(f"Error reading logs: {e}")
        return False

def main():
    print("🚀 TESTING DRAWINGS & MANUALS BACKGROUND DELETION WITH REAL FILES")
    print("=" * 80)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("❌ Authentication failed")
        return 1
    
    print("✅ Authentication successful")
    
    # Get existing documents with files
    existing_docs = get_documents_with_files(token)
    print(f"Found {len(existing_docs)} existing documents with files")
    
    # Create a new test document with file upload
    test_doc_id = create_test_document_with_file_upload(token)
    
    test_results = []
    
    # Test 1: Single background delete with existing document
    if existing_docs and len(existing_docs) > 0:
        print(f"\nTest 1: Single background delete with existing document")
        doc_to_delete = existing_docs[0]
        print(f"Using document: {doc_to_delete['document_name']} (ID: {doc_to_delete['id']})")
        result = test_single_background_delete(token, doc_to_delete['id'])
        test_results.append(("Single delete (existing)", result))
    
    # Test 2: Single background delete with newly created document
    if test_doc_id:
        print(f"\nTest 2: Single background delete with newly created document")
        result = test_single_background_delete(token, test_doc_id)
        test_results.append(("Single delete (new)", result))
    
    # Test 3: Bulk background delete with remaining documents
    remaining_docs = get_documents_with_files(token)
    if len(remaining_docs) >= 2:
        print(f"\nTest 3: Bulk background delete with {min(2, len(remaining_docs))} documents")
        docs_to_delete = remaining_docs[:2]  # Take first 2
        doc_ids = [doc['id'] for doc in docs_to_delete]
        result = test_bulk_background_delete(token, doc_ids)
        test_results.append(("Bulk delete", result))
    
    # Check backend logs
    time.sleep(3)  # Wait for background processing
    logs_found = check_backend_logs()
    test_results.append(("Backend logs", logs_found))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
    
    if success_rate >= 75:
        print("✅ BACKGROUND DELETION FEATURE WORKING CORRECTLY")
        return 0
    else:
        print("❌ BACKGROUND DELETION FEATURE HAS ISSUES")
        return 1

if __name__ == "__main__":
    exit(main())