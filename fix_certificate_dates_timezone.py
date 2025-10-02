#!/usr/bin/env python3
"""
Migration Script: Add UTC Timezone to All Certificate Dates in MongoDB

PROBLEM: Dates stored in MongoDB are naive datetime objects (no timezone info).
When FastAPI serializes them, they get incorrectly converted causing 1-day shift.

SOLUTION: Add UTC timezone to all date fields in certificates collection.

SAFETY: This script only ADDS timezone info, doesn't change the date values.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone

async def fix_certificate_dates():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client['ship_management']
    
    print("\n" + "="*70)
    print("CERTIFICATE DATES TIMEZONE FIX MIGRATION")
    print("="*70 + "\n")
    
    # Get all certificates
    certificates = await db.certificates.find({}).to_list(length=None)
    total_certs = len(certificates)
    
    print(f"Found {total_certs} certificates in database\n")
    
    updated_count = 0
    skipped_count = 0
    
    date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey', 'created_at', 'updated_at']
    
    for i, cert in enumerate(certificates, 1):
        cert_id = cert.get('id')
        cert_name = cert.get('cert_name', 'Unknown')
        ship_name = cert.get('ship_name', 'Unknown')
        
        print(f"[{i}/{total_certs}] Processing: {cert_name} ({ship_name})")
        
        needs_update = False
        update_doc = {}
        
        # Check each date field
        for field in date_fields:
            value = cert.get(field)
            
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    # Naive datetime - add UTC timezone
                    utc_datetime = value.replace(tzinfo=timezone.utc)
                    update_doc[field] = utc_datetime
                    needs_update = True
                    print(f"  → {field}: {value} → {utc_datetime}")
        
        if needs_update:
            # Update in MongoDB
            result = await db.certificates.update_one(
                {"id": cert_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"  ✅ Updated {len(update_doc)} date fields\n")
            else:
                print(f"  ⚠️ Update failed\n")
        else:
            skipped_count += 1
            print(f"  ⏭️  All dates already have timezone\n")
    
    print("\n" + "="*70)
    print("MIGRATION SUMMARY")
    print("="*70)
    print(f"Total Certificates: {total_certs}")
    print(f"Updated: {updated_count}")
    print(f"Skipped (already correct): {skipped_count}")
    print("="*70 + "\n")
    
    # Verify a sample certificate
    print("Verifying CSSC Certificate (PM242308)...")
    cssc = await db.certificates.find_one({"cert_no": "PM242308"})
    if cssc:
        print(f"Issue Date: {cssc.get('issue_date')}")
        print(f"Valid Date: {cssc.get('valid_date')}")
        print(f"Last Endorse: {cssc.get('last_endorse')}")
        
        issue_date = cssc.get('issue_date')
        if isinstance(issue_date, datetime) and issue_date.tzinfo is not None:
            print("\n✅ Verification PASSED - Dates now have UTC timezone!")
        else:
            print("\n❌ Verification FAILED - Dates still missing timezone!")
    else:
        print("Certificate not found")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_certificate_dates())
