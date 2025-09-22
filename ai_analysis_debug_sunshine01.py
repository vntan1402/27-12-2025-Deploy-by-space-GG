#!/usr/bin/env python3
"""
Debug AI Analysis for SUNSHINE 01 Certificate
Detailed debugging of the AI Analysis response to understand why data extraction is failing.
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://continue-session.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

def authenticate():
    """Authenticate with the backend"""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    })
    
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Authentication failed: {response.status_code} - {response.text}")
        return None

def debug_ai_analysis():
    """Debug the AI analysis response"""
    token = authenticate()
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    pdf_path = "/app/SUNSHINE_01_CSSC_PM25385.pdf"
    
    print("🔍 Debugging AI Analysis Response")
    print("=" * 50)
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': ('SUNSHINE_01_CSSC_PM25385.pdf', f, 'application/pdf')}
            
            response = requests.post(
                f"{API_BASE}/analyze-ship-certificate",
                files=files,
                headers=headers
            )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Full Response Data:")
            print(json.dumps(data, indent=2, default=str))
            
            # Check specific fields
            success = data.get('success', False)
            print(f"\n✅ Success: {success}")
            
            if 'data' in data:
                data_section = data['data']
                print(f"📋 Data Section Keys: {list(data_section.keys())}")
                
                if 'analysis' in data_section:
                    analysis = data_section['analysis']
                    print(f"🔬 Analysis Keys: {list(analysis.keys()) if analysis else 'None'}")
                    print(f"🔬 Analysis Data: {analysis}")
                
                if 'fallback_reason' in data_section:
                    print(f"⚠️ Fallback Reason: {data_section['fallback_reason']}")
                
                if 'processing_method' in data_section:
                    print(f"🔧 Processing Method: {data_section['processing_method']}")
            
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def check_backend_logs():
    """Check backend logs for OCR processor status"""
    print("\n🔍 Checking Backend Logs")
    print("=" * 30)
    
    try:
        # Check supervisor logs for backend
        import subprocess
        result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.err.log'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("📋 Backend Error Logs (last 50 lines):")
            print(result.stdout)
        else:
            print("❌ Could not read backend error logs")
            
        # Also check stdout logs
        result = subprocess.run(['tail', '-n', '50', '/var/log/supervisor/backend.out.log'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n📋 Backend Output Logs (last 50 lines):")
            print(result.stdout)
        else:
            print("❌ Could not read backend output logs")
            
    except Exception as e:
        print(f"❌ Error checking logs: {e}")

if __name__ == "__main__":
    debug_ai_analysis()
    check_backend_logs()