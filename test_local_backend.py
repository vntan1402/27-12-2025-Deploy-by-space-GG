#!/usr/bin/env python3
import requests
import json

# Test local backend connection
try:
    print("Testing local backend connection...")
    
    # Test sidebar structure endpoint
    response = requests.get("http://127.0.0.1:8001/api/sidebar-structure", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Sidebar structure endpoint working!")
        print(f"Structure has {len(data.get('structure', {}))} categories")
        
        # Check for dynamic structure
        structure = data.get('structure', {})
        document_portfolio = structure.get("Document Portfolio", [])
        
        if "Class Survey Report" in document_portfolio and "Test Report" in document_portfolio:
            print("✅ Dynamic structure detected!")
        else:
            print("❌ Fallback structure detected!")
            
        print(f"Document Portfolio: {document_portfolio}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Connection error: {e}")