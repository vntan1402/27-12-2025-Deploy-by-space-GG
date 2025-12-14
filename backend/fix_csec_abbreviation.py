"""
Fix CSEC -> CSSE abbreviation for all affected certificates
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def main():
    # Get MongoDB URL
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME', 'ship_management')
    
    if not mongo_url:
        print("Error: MONGO_URL not set")
        return
    
    print('=' * 80)
    print('FIXING CSEC -> CSSE ABBREVIATION')
    print('=' * 80)
    print()
    
    # Connect
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Find all certificates with this name
    cert_names_to_fix = [
        'CARGO SHIP SAFETY EQUIPMENT CERTIFICATE',
        'Cargo Ship Safety Equipment Certificate',
        'cargo ship safety equipment certificate',
    ]
    
    print(f'Searching for certificates with names: {cert_names_to_fix}')
    print()
    
    for cert_name in cert_names_to_fix:
        cursor = db.certificates.find({'cert_name': cert_name})
        certs = await cursor.to_list(length=1000)
        
        if certs:
            print(f'Found {len(certs)} certificate(s) with name: "{cert_name}"')
            
            for cert in certs:
                old_abbr = cert.get('cert_abbreviation')
                print(f'  ID: {cert.get("id")} | Old: "{old_abbr}" | New: "CSSE"')
                
                # Update
                result = await db.certificates.update_one(
                    {'id': cert.get('id')},
                    {
                        '$set': {
                            'cert_abbreviation': 'CSSE',
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f'    ✅ Updated')
                else:
                    print(f'    ⚠️ No changes (already correct?)')
            print()
    
    # Also search using regex
    print('Searching using regex...')
    cursor = db.certificates.find({
        'cert_name': {'$regex': 'CARGO.*SHIP.*SAFETY.*EQUIPMENT', '$options': 'i'}
    })
    regex_certs = await cursor.to_list(length=1000)
    
    if regex_certs:
        print(f'Found {len(regex_certs)} certificate(s) via regex')
        
        for cert in regex_certs:
            old_abbr = cert.get('cert_abbreviation')
            if old_abbr != 'CSSE':
                print(f'  ID: {cert.get("id")} | Name: "{cert.get("cert_name")}" | Old: "{old_abbr}" | New: "CSSE"')
                
                result = await db.certificates.update_one(
                    {'id': cert.get('id')},
                    {
                        '$set': {
                            'cert_abbreviation': 'CSSE',
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                if result.modified_count > 0:
                    print(f'    ✅ Updated')
    
    # Verify
    print()
    print('=' * 80)
    print('VERIFICATION')
    print('=' * 80)
    cursor = db.certificates.find({
        'cert_name': {'$regex': 'CARGO.*SHIP.*SAFETY.*EQUIPMENT', '$options': 'i'}
    })
    all_certs = await cursor.to_list(length=1000)
    
    correct_count = 0
    incorrect_count = 0
    
    for cert in all_certs:
        abbr = cert.get('cert_abbreviation')
        if abbr == 'CSSE':
            correct_count += 1
        else:
            incorrect_count += 1
            print(f'❌ Still incorrect: {cert.get("id")} -> "{abbr}"')
    
    print(f'\nTotal certificates: {len(all_certs)}')
    print(f'Correct (CSSE): {correct_count}')
    print(f'Incorrect: {incorrect_count}')
    
    if incorrect_count == 0:
        print('\n✅ ALL CERTIFICATES FIXED!')
    else:
        print(f'\n⚠️ {incorrect_count} certificates still need fixing')
    
    client.close()

if __name__ == '__main__':
    asyncio.run(main())
