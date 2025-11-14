#!/usr/bin/env python3
"""
Debug script to check MongoDB directly and understand the filtering
"""

import asyncio
import sys
import os
from datetime import datetime, date, timedelta

# Add the backend directory to the path
sys.path.append('/app/backend')

# Import MongoDB connection
from mongodb_database import mongo_db

async def debug_mongodb():
    """Debug MongoDB data directly"""
    
    print("🔍 Debugging MongoDB data directly...")
    
    # Get the company ID we're working with
    company_id = "0a6eaf96-0aaf-4793-89be-65d62cb7953c"
    print(f"🏢 Company ID: {company_id}")
    
    # Get ships for this company
    ships = await mongo_db.find_all("ships", {"company": company_id})
    print(f"🚢 Found {len(ships)} ships for company")
    
    ship_ids = [ship.get('id') for ship in ships if ship.get('id')]
    print(f"📋 Ship IDs: {ship_ids}")
    
    # Get all certificates for these ships
    all_certificates = []
    for ship_id in ship_ids:
        certs = await mongo_db.find_all("certificates", {"ship_id": ship_id})
        all_certificates.extend(certs)
    
    print(f"📄 Found {len(all_certificates)} total certificates")
    
    # Find the target certificate
    target_cert_id = "51d1c55a-81d4-4e68-9dd2-9fef7d8bf895"
    target_cert = None
    
    for cert in all_certificates:
        if cert.get('id') == target_cert_id:
            target_cert = cert
            break
    
    if not target_cert:
        print(f"❌ Target certificate {target_cert_id} not found in MongoDB")
        return
    
    print(f"✅ Found target certificate in MongoDB:")
    print(f"   📄 Name: {target_cert.get('cert_name')}")
    print(f"   🚢 Ship ID: {target_cert.get('ship_id')}")
    print(f"   📅 Next Survey: {target_cert.get('next_survey')}")
    print(f"   🔄 Survey Type: {target_cert.get('next_survey_type')}")
    
    # Simulate the exact backend logic
    print(f"\n🧮 Simulating exact backend logic:")
    
    current_date = datetime.now().date()
    print(f"📅 Current server date: {current_date}")
    
    upcoming_surveys = []
    
    for cert in all_certificates:
        cert_id = cert.get('id')
        next_survey_str = cert.get('next_survey')
        next_survey_type = cert.get('next_survey_type') or ''
        cert_name = (cert.get('cert_name') or '').upper()
        
        print(f"\n📋 Processing certificate: {cert_id}")
        print(f"   Name: {cert.get('cert_name')}")
        print(f"   Next Survey: {next_survey_str}")
        print(f"   Survey Type: {next_survey_type}")
        
        # Skip certificates without next survey date, EXCEPT for Initial SMC/ISSC/MLC certificates
        is_initial_smc_issc_mlc = ('Initial' in next_survey_type and 
                                   any(cert_type in cert_name for cert_type in ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC']))
        
        if not next_survey_str and not is_initial_smc_issc_mlc:
            print(f"   ⏭️ Skipping: No next_survey date and not Initial SMC/ISSC/MLC")
            continue
        
        try:
            # Parse next survey date
            next_survey_date = None
            if next_survey_str:
                if isinstance(next_survey_str, str):
                    if 'T' in next_survey_str:
                        next_survey_date = datetime.fromisoformat(next_survey_str.replace('Z', '')).date()
                    else:
                        if ' ' in next_survey_str:
                            next_survey_date = datetime.strptime(next_survey_str.split(' ')[0], '%Y-%m-%d').date()
                        else:
                            next_survey_date = datetime.strptime(next_survey_str, '%Y-%m-%d').date()
                elif hasattr(next_survey_str, 'date'):
                    next_survey_date = next_survey_str.date()
                else:
                    next_survey_date = next_survey_str
            
            print(f"   📅 Parsed date: {next_survey_date}")
            
            # Determine window based on survey type
            if 'Condition Certificate Expiry' in next_survey_type:
                print(f"   📋 Type: Condition Certificate")
                issue_date_str = cert.get('issue_date')
                valid_date_str = cert.get('valid_date')
                
                if not issue_date_str or not valid_date_str:
                    print(f"   ⏭️ Skipping: Missing required dates for condition certificate")
                    continue
                
                # Parse dates (simplified)
                window_open = datetime.fromisoformat(issue_date_str.replace('Z', '')).date()
                window_close = datetime.fromisoformat(valid_date_str.replace('Z', '')).date()
                
            elif 'Initial' in next_survey_type and any(cert_type in cert_name for cert_type in ['SAFETY MANAGEMENT', 'SHIP SECURITY', 'MARITIME LABOUR', 'SMC', 'ISSC', 'MLC']):
                print(f"   📋 Type: Initial SMC/ISSC/MLC")
                valid_date_str = cert.get('valid_date')
                
                if not valid_date_str:
                    print(f"   ⏭️ Skipping: Missing valid date for initial certificate")
                    continue
                
                valid_date = datetime.fromisoformat(valid_date_str.replace('Z', '')).date()
                window_open = valid_date - timedelta(days=90)
                window_close = valid_date
                
            elif 'Special Survey' in next_survey_type and next_survey_date:
                print(f"   📋 Type: Special Survey")
                window_open = next_survey_date - timedelta(days=90)
                window_close = next_survey_date
                
            elif next_survey_date:
                print(f"   📋 Type: Other surveys (±3M)")
                window_open = next_survey_date - timedelta(days=90)
                window_close = next_survey_date + timedelta(days=90)
                
            else:
                print(f"   ⏭️ Skipping: No next_survey_date and not Initial SMC/ISSC/MLC")
                continue
            
            print(f"   🪟 Window: {window_open} to {window_close}")
            
            # Check if current_date is within certificate's survey window
            if window_open <= current_date <= window_close:
                print(f"   ✅ Within window - SHOULD be included")
                
                # Find ship information
                ship_info = next((ship for ship in ships if ship.get('id') == cert.get('ship_id')), {})
                
                days_until_survey = (next_survey_date - current_date).days if next_survey_date else 0
                
                upcoming_survey = {
                    'certificate_id': cert.get('id'),
                    'ship_id': cert.get('ship_id'),
                    'ship_name': ship_info.get('name', ''),
                    'cert_name': cert.get('cert_name', ''),
                    'next_survey_date': next_survey_date.isoformat() if next_survey_date else None,
                    'next_survey_type': cert.get('next_survey_type', ''),
                    'days_until_survey': days_until_survey,
                    'window_open': window_open.isoformat(),
                    'window_close': window_close.isoformat(),
                }
                
                upcoming_surveys.append(upcoming_survey)
                
                if cert_id == target_cert_id:
                    print(f"   🎯 TARGET CERTIFICATE INCLUDED!")
                
            else:
                print(f"   ❌ Outside window - excluded")
                print(f"      Current: {current_date}")
                print(f"      Window: {window_open} to {window_close}")
        
        except Exception as date_error:
            print(f"   ❌ Error parsing dates: {date_error}")
            continue
    
    print(f"\n📊 Final Results:")
    print(f"   Total certificates processed: {len(all_certificates)}")
    print(f"   Certificates in upcoming surveys: {len(upcoming_surveys)}")
    
    target_found = False
    for survey in upcoming_surveys:
        if survey['certificate_id'] == target_cert_id:
            target_found = True
            print(f"   🎯 TARGET CERTIFICATE FOUND IN RESULTS!")
            break
    
    if not target_found:
        print(f"   ❌ Target certificate NOT in results")
    
    print(f"\n📋 All upcoming surveys:")
    for survey in upcoming_surveys:
        print(f"   - {survey['certificate_id']}: {survey['cert_name']} ({survey['days_until_survey']} days)")

if __name__ == "__main__":
    asyncio.run(debug_mongodb())