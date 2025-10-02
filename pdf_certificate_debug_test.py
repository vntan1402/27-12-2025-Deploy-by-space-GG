#!/usr/bin/env python3
"""
PDF Certificate AI Analysis Debug Test
Create a proper PDF and test the analyze-ship-certificate endpoint
"""

import requests
import json
import os
import sys
import tempfile
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration
try:
    test_response = requests.get('http://0.0.0.0:8001/api/ships', timeout=5)
    if test_response.status_code in [200, 401]:
        BACKEND_URL = 'http://0.0.0.0:8001/api'
        print("Using internal backend URL: http://0.0.0.0:8001/api")
    else:
        raise Exception("Internal URL not working")
except:
    BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vesseldocs.preview.emergentagent.com') + '/api'
    print(f"Using external backend URL: {BACKEND_URL}")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def authenticate():
    """Authenticate and get token"""
    try:
        log("🔐 Authenticating...")
        response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "username": "admin1",
            "password": "123456"
        })
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            log("✅ Authentication successful")
            return token
        else:
            log(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        log(f"❌ Authentication error: {e}")
        return None

def create_test_certificate_pdf():
    """Create a test PDF certificate with specific data for debugging"""
    try:
        log("📄 Creating test CSSC certificate PDF...")
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create PDF with certificate content
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE")
        
        # Certificate details
        c.setFont("Helvetica", 12)
        y_pos = height - 100
        
        certificate_data = [
            "Certificate No: PM25385",
            "Ship Name: SUNSHINE 01",
            "IMO Number: 9415313",
            "Port of Registry: PANAMA",
            "Flag: PANAMA",
            "Gross Tonnage: 2959",
            "Deadweight: 45000",
            "Class Society: PMDS (Panama Maritime Documentation Services)",
            "Built Year: 2006",
            "Keel Laid: 20/10/2004",
            "Delivery Date: 01/08/2006",
            "Ship Owner: AMCSC",
            "Company: AMCSC",
            "",
            "ENDORSEMENTS:",
            "Annual Survey: 10 MAR 2024",
            "Last Docking Survey: NOV 2020",
            "Previous Docking: DEC 2022", 
            "Inspections of the outside of the ship's bottom: NOV 2020",
            "",
            "VALIDITY:",
            "Valid Until: 10/03/2026",
            "Issue Date: 10/03/2021",
            "",
            "SPECIAL SURVEY CYCLE:",
            "From: 10/03/2021",
            "To: 10/03/2026",
            "Type: SOLAS Safety Construction Survey Cycle",
            "",
            "This certificate is issued to verify that the ship has been",
            "surveyed and found to comply with the relevant provisions",
            "of the International Convention for the Safety of Life at Sea."
        ]
        
        for line in certificate_data:
            c.drawString(50, y_pos, line)
            y_pos -= 20
        
        c.save()
        
        log(f"✅ Test certificate PDF created: {temp_path}")
        log(f"   File size: {os.path.getsize(temp_path)} bytes")
        return temp_path
        
    except Exception as e:
        log(f"❌ PDF creation error: {e}")
        return None

def test_ai_analysis_detailed(token, cert_path):
    """Test AI certificate analysis with detailed debugging"""
    try:
        log("🔍 Testing AI Certificate Analysis with detailed debugging...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with PDF file
        with open(cert_path, 'rb') as cert_file:
            files = {'file': ('sunshine_01_cssc.pdf', cert_file, 'application/pdf')}
            
            log("   Uploading PDF for AI analysis...")
            response = requests.post(
                f"{BACKEND_URL}/analyze-ship-certificate",
                files=files,
                headers=headers,
                timeout=120
            )
        
        log(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            log("✅ AI Analysis successful")
            
            # Log complete response
            log("\n📋 COMPLETE AI RESPONSE:")
            log("=" * 80)
            log(json.dumps(data, indent=2, default=str))
            log("=" * 80)
            
            # Extract analysis data
            analysis = data.get('analysis', {})
            
            # Debug Issue 1: Last Docking Dates Format
            log("\n🔍 ISSUE 1 DEBUG: LAST DOCKING DATES FORMAT")
            log("=" * 60)
            log("   Expected: 'NOV 2020', 'DEC 2022' (month/year format)")
            log("   Problem: Full dates like '30/11/2020', '31/12/2022'")
            
            last_docking = analysis.get('last_docking')
            last_docking_2 = analysis.get('last_docking_2')
            
            log(f"\n   AI Extracted:")
            log(f"   last_docking: {last_docking}")
            log(f"   last_docking_2: {last_docking_2}")
            
            # Analyze the format
            issue_1_resolved = False
            if last_docking:
                if "NOV 2020" in str(last_docking) or "NOV. 2020" in str(last_docking):
                    log("   ✅ last_docking is in correct month/year format")
                    issue_1_resolved = True
                elif "/" in str(last_docking) and len(str(last_docking).split("/")) == 3:
                    log("   ❌ ISSUE 1 CONFIRMED: last_docking is in full date format")
                    log(f"      Expected: 'NOV 2020', Got: '{last_docking}'")
                else:
                    log(f"   ⚠️ Unexpected last_docking format: {last_docking}")
            else:
                log("   ⚠️ No last_docking extracted")
            
            if last_docking_2:
                if "DEC 2022" in str(last_docking_2) or "DEC. 2022" in str(last_docking_2):
                    log("   ✅ last_docking_2 is in correct month/year format")
                elif "/" in str(last_docking_2) and len(str(last_docking_2).split("/")) == 3:
                    log("   ❌ ISSUE 1 CONFIRMED: last_docking_2 is in full date format")
                    log(f"      Expected: 'DEC 2022', Got: '{last_docking_2}'")
                else:
                    log(f"   ⚠️ Unexpected last_docking_2 format: {last_docking_2}")
            else:
                log("   ⚠️ No last_docking_2 extracted")
            
            # Debug Issue 2: Special Survey From Date Calculation
            log("\n🔍 ISSUE 2 DEBUG: SPECIAL SURVEY FROM DATE CALCULATION")
            log("=" * 60)
            log("   Expected: special_survey_from_date auto-calculated from special_survey_to_date")
            log("   Problem: special_survey_from_date is null instead of calculated")
            
            special_survey_from = analysis.get('special_survey_from_date')
            special_survey_to = analysis.get('special_survey_to_date')
            
            log(f"\n   AI Extracted:")
            log(f"   special_survey_to_date: {special_survey_to}")
            log(f"   special_survey_from_date: {special_survey_from}")
            
            issue_2_resolved = False
            if special_survey_to and special_survey_from:
                # Check if calculation is correct (5 years difference, same day/month)
                if ("10/03/2026" in str(special_survey_to) and 
                    "10/03/2021" in str(special_survey_from)):
                    log("   ✅ ISSUE 2 RESOLVED: Special Survey From Date correctly calculated")
                    log("      ✅ To Date: 10/03/2026")
                    log("      ✅ From Date: 10/03/2021 (5 years prior, same day/month)")
                    issue_2_resolved = True
                else:
                    log("   ⚠️ Special Survey dates calculated but may be incorrect")
                    log(f"      Expected: from='10/03/2021', to='10/03/2026'")
                    log(f"      Got: from='{special_survey_from}', to='{special_survey_to}'")
            elif special_survey_to and not special_survey_from:
                log("   ❌ ISSUE 2 CONFIRMED: special_survey_from_date is null")
                log("      Post-processing logic is NOT working")
                log(f"      special_survey_to_date exists: {special_survey_to}")
                log("      Expected from_date calculation: 5 years prior with same day/month")
            else:
                log("   ⚠️ No special survey dates found in extraction")
            
            # Check Next Docking calculation (related to the fixes)
            log("\n🔍 NEXT DOCKING CALCULATION DEBUG")
            log("=" * 60)
            
            next_docking = analysis.get('next_docking')
            log(f"   next_docking: {next_docking}")
            
            if next_docking and next_docking not in ['null', 'None', '', 'dd/mm/yyyy']:
                log("   ✅ Next Docking calculated")
            else:
                log("   ⚠️ Next Docking not calculated or is placeholder")
            
            # Summary of debugging results
            log("\n📊 DEBUGGING SUMMARY")
            log("=" * 60)
            
            if issue_1_resolved:
                log("   ✅ ISSUE 1: Last Docking dates format - RESOLVED")
            else:
                log("   ❌ ISSUE 1: Last Docking dates format - NOT RESOLVED")
            
            if issue_2_resolved:
                log("   ✅ ISSUE 2: Special Survey From Date calculation - RESOLVED")
            else:
                log("   ❌ ISSUE 2: Special Survey From Date calculation - NOT RESOLVED")
            
            # Check all extracted fields
            log(f"\n📋 ALL EXTRACTED FIELDS:")
            for key, value in analysis.items():
                log(f"   {key}: {value}")
            
            return True
            
        else:
            log(f"❌ AI Analysis failed: {response.status_code}")
            try:
                error = response.json()
                log(f"   Error: {error}")
            except:
                log(f"   Error: {response.text[:500]}")
            return False
            
    except Exception as e:
        log(f"❌ AI Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup(cert_path):
    """Clean up temporary files"""
    try:
        if cert_path and os.path.exists(cert_path):
            os.unlink(cert_path)
            log("🧹 Cleanup completed")
    except Exception as e:
        log(f"⚠️ Cleanup error: {e}")

def main():
    log("🔍 PDF CERTIFICATE AI ANALYSIS DEBUG TEST")
    log("🎯 FOCUS: Debug Last Docking dates and Special Survey From Date issues")
    log("=" * 80)
    
    cert_path = None
    try:
        # Step 1: Authenticate
        token = authenticate()
        if not token:
            return False
        
        # Step 2: Create test PDF certificate
        cert_path = create_test_certificate_pdf()
        if not cert_path:
            return False
        
        # Step 3: Test AI analysis with detailed debugging
        success = test_ai_analysis_detailed(token, cert_path)
        
        # Step 4: Summary
        if success:
            log("\n✅ PDF CERTIFICATE DEBUG TEST COMPLETED")
        else:
            log("\n❌ PDF CERTIFICATE DEBUG TEST FAILED")
        
        return success
        
    finally:
        cleanup(cert_path)

if __name__ == "__main__":
    main()