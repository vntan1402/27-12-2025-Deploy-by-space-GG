#!/usr/bin/env python3
"""
Detailed Passport Upload Response Analysis
"""

import requests
import json
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://fleet-cert-system.preview.emergentagent.com') + '/api'

def authenticate():
    """Authenticate and get token"""
    login_data = {
        "username": "admin1",
        "password": "123456",
        "remember_me": False
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=60)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    return None

def create_test_passport_pdf():
    """Create a test passport PDF"""
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "SOCIALIST REPUBLIC OF VIETNAM")
    c.drawString(100, height - 120, "PASSPORT / HỘ CHIẾU")
    
    # Passport details
    c.setFont("Helvetica", 12)
    y_pos = height - 180
    
    passport_data = [
        "Type/Loại: P",
        "Country code/Mã quốc gia: VNM",
        "Passport No./Số hộ chiếu: C1234567",
        "",
        "Surname/Họ: NGUYEN",
        "Given names/Tên: VAN MINH",
        "Nationality/Quốc tịch: VIETNAMESE",
        "Date of birth/Ngày sinh: 15/02/1985",
        "Sex/Giới tính: M",
        "Place of birth/Nơi sinh: HO CHI MINH",
        "",
        "Date of issue/Ngày cấp: 10/01/2020",
        "Date of expiry/Ngày hết hạn: 09/01/2030",
        "Authority/Cơ quan cấp: IMMIGRATION DEPARTMENT",
    ]
    
    for line in passport_data:
        c.drawString(100, y_pos, line)
        y_pos -= 20
    
    c.save()
    pdf_content = pdf_buffer.getvalue()
    pdf_buffer.close()
    return pdf_content

def main():
    print("🔐 Authenticating...")
    token = authenticate()
    if not token:
        print("❌ Authentication failed")
        return
    
    print("📄 Creating test passport PDF...")
    pdf_content = create_test_passport_pdf()
    
    print("📤 Testing passport upload...")
    
    headers = {"Authorization": f"Bearer {token}"}
    files = {
        'passport_file': ('test_passport.pdf', pdf_content, 'application/pdf')
    }
    data = {
        'ship_name': 'BROTHER 36'
    }
    
    response = requests.post(
        f"{BACKEND_URL}/crew/analyze-passport",
        files=files,
        data=data,
        headers=headers,
        timeout=120
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print("\n📋 DETAILED RESPONSE ANALYSIS:")
        print("=" * 60)
        print(json.dumps(response_data, indent=2, default=str))
        print("=" * 60)
        
        # Analyze specific fields
        print("\n🔍 FIELD ANALYSIS:")
        
        if 'files' in response_data:
            files_data = response_data['files']
            print(f"Files section: {json.dumps(files_data, indent=2, default=str)}")
            
            # Check for file IDs
            for key, value in files_data.items():
                if 'file_id' in key.lower():
                    print(f"Found file ID field '{key}': {value}")
                    if isinstance(value, str):
                        if value.startswith('maritime_file_'):
                            print(f"  ⚠️ This appears to be a FAKE file ID: {value}")
                        else:
                            print(f"  ✅ This appears to be a REAL file ID: {value}")
        
        if 'analysis' in response_data:
            analysis_data = response_data['analysis']
            print(f"Analysis section: {json.dumps(analysis_data, indent=2, default=str)}")
        
        # Check for SUMMARY folder indicators
        summary_indicators = []
        def find_summary_indicators(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if 'summary' in key.lower() or 'SUMMARY' in str(value):
                        summary_indicators.append(f"{current_path}: {value}")
                    find_summary_indicators(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_summary_indicators(item, f"{path}[{i}]")
        
        find_summary_indicators(response_data)
        
        if summary_indicators:
            print("\n📁 SUMMARY FOLDER INDICATORS FOUND:")
            for indicator in summary_indicators:
                print(f"  {indicator}")
        else:
            print("\n📁 NO SUMMARY FOLDER INDICATORS FOUND")
        
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON response: {response.text[:1000]}")

if __name__ == "__main__":
    main()