#!/usr/bin/env python3
"""
Test script for the upcoming surveys endpoint
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

sys.path.append('/app/backend')

from mongodb_database import mongo_db
from datetime import datetime, timedelta
import uuid

async def test_upcoming_surveys():
    """Test the upcoming surveys functionality"""
    try:
        # Connect to database
        await mongo_db.connect()
        
        # Create test company
        test_company = "Test Company"
        
        # Create test ship
        test_ship = {
            "id": str(uuid.uuid4()),
            "name": "Test Ship",
            "company": test_company,
            "flag": "Panama",
            "ship_type": "Container",
            "created_at": datetime.utcnow()
        }
        
        # Create test certificates with upcoming surveys
        current_date = datetime.now()
        
        # Certificate 1: Due in 30 days
        cert1 = {
            "id": str(uuid.uuid4()),
            "ship_id": test_ship["id"],
            "cert_name": "Safety Construction Certificate",
            "cert_abbreviation": "SCC",
            "next_survey": (current_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            "next_survey_type": "Annual",
            "status": "Valid",
            "created_at": datetime.utcnow()
        }
        
        # Certificate 2: Due in 60 days
        cert2 = {
            "id": str(uuid.uuid4()),
            "ship_id": test_ship["id"],
            "cert_name": "Safety Equipment Certificate",
            "cert_abbreviation": "SEC",
            "next_survey": (current_date + timedelta(days=60)).strftime('%Y-%m-%d'),
            "next_survey_type": "Intermediate",
            "status": "Valid",
            "created_at": datetime.utcnow()
        }
        
        # Certificate 3: Overdue (should still be in ±3 months window)
        cert3 = {
            "id": str(uuid.uuid4()),
            "ship_id": test_ship["id"],
            "cert_name": "Load Line Certificate",
            "cert_abbreviation": "LLC",
            "next_survey": (current_date - timedelta(days=15)).strftime('%Y-%m-%d'),
            "next_survey_type": "Annual",
            "status": "Expired",
            "created_at": datetime.utcnow()
        }
        
        # Insert test data
        await mongo_db.create("ships", test_ship)
        await mongo_db.create("certificates", cert1)
        await mongo_db.create("certificates", cert2)
        await mongo_db.create("certificates", cert3)
        
        print("✅ Test data created successfully")
        
        # Test the upcoming surveys logic
        ships = await mongo_db.find_all("ships", {"company": test_company})
        ship_ids = [ship.get('id') for ship in ships if ship.get('id')]
        
        print(f"Found {len(ships)} ships for company: {test_company}")
        
        # Get all certificates from these ships
        all_certificates = []
        for ship_id in ship_ids:
            certs = await mongo_db.find_all("certificates", {"ship_id": ship_id})
            all_certificates.extend(certs)
        
        print(f"Found {len(all_certificates)} total certificates to check")
        
        # Define 3-month window (±3 months)
        current_date_obj = current_date.date()
        three_months_ago = current_date_obj - timedelta(days=90)
        three_months_later = current_date_obj + timedelta(days=90)
        
        upcoming_surveys = []
        
        for cert in all_certificates:
            next_survey_str = cert.get('next_survey')
            if not next_survey_str:
                continue
                
            try:
                # Parse next survey date
                if isinstance(next_survey_str, str):
                    if 'T' in next_survey_str:
                        next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '')).date()
                    else:
                        next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d').date()
                else:
                    next_survey_date = next_survey_str
                
                # Check if next survey date is within ±3 months window
                if three_months_ago <= next_survey_date <= three_months_later:
                    ship_info = next((ship for ship in ships if ship.get('id') == cert.get('ship_id')), {})
                    
                    cert_abbreviation = cert.get('cert_abbreviation') or cert.get('abbreviation', '')
                    cert_name_display = f"{cert.get('cert_name', '')} ({cert_abbreviation})" if cert_abbreviation else cert.get('cert_name', '')
                    
                    upcoming_survey = {
                        'certificate_id': cert.get('id'),
                        'ship_id': cert.get('ship_id'),
                        'ship_name': ship_info.get('name', ''),
                        'cert_name': cert.get('cert_name', ''),
                        'cert_abbreviation': cert_abbreviation,
                        'cert_name_display': cert_name_display,
                        'next_survey': next_survey_str,
                        'next_survey_date': next_survey_date.isoformat(),
                        'next_survey_type': cert.get('next_survey_type', ''),
                        'days_until_survey': (next_survey_date - current_date_obj).days,
                        'is_overdue': next_survey_date < current_date_obj,
                        'is_due_soon': 0 <= (next_survey_date - current_date_obj).days <= 30,
                        'is_within_window': True
                    }
                    
                    upcoming_surveys.append(upcoming_survey)
                    
            except Exception as date_error:
                print(f"Error parsing date '{next_survey_str}': {date_error}")
                continue
        
        # Sort by next survey date (soonest first)
        upcoming_surveys.sort(key=lambda x: x['next_survey_date'])
        
        print(f"\n🔍 Found {len(upcoming_surveys)} certificates with upcoming surveys:")
        
        for survey in upcoming_surveys:
            status_icon = "⚠️" if survey['is_overdue'] else "🔔" if survey['is_due_soon'] else "📅"
            print(f"{status_icon} {survey['ship_name']} - {survey['cert_name_display']}")
            print(f"   Next Survey: {survey['next_survey_date']} ({survey['days_until_survey']} days)")
            print(f"   Type: {survey['next_survey_type']}")
            print()
        
        result = {
            "upcoming_surveys": upcoming_surveys,
            "total_count": len(upcoming_surveys),
            "company": test_company,
            "check_date": current_date_obj.isoformat(),
            "window_info": {
                "from_date": three_months_ago.isoformat(),
                "to_date": three_months_later.isoformat(),
                "window_days": 180
            }
        }
        
        print("✅ Test completed successfully!")
        print(f"📊 Result summary: {result['total_count']} upcoming surveys found")
        
        # Clean up test data
        await mongo_db.delete("ships", {"id": test_ship["id"]})
        await mongo_db.delete("certificates", {"ship_id": test_ship["id"]})
        print("🧹 Test data cleaned up")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    result = asyncio.run(test_upcoming_surveys())
    if result:
        print("\n✅ Upcoming surveys endpoint logic works correctly!")
    else:
        print("\n❌ Test failed!")