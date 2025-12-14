"""
Test certificate abbreviation in actual database
"""
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    # Get MongoDB URL from environment
    mongo_url = os.getenv('MONGO_URL')
    if not mongo_url:
        print("Error: MONGO_URL not set")
        return
    
    db_name = os.getenv('DB_NAME', 'ship_management')
    
    print('=' * 80)
    print('TRACING CERTIFICATE ABBREVIATION IN DATABASE')
    print('=' * 80)
    print(f'Database: {db_name}')
    print()
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # 1. Check user-defined mapping
    print('STEP 1: Check user-defined mapping')
    print('-' * 80)
    mapping = await db.certificate_abbreviation_mappings.find_one({
        'cert_name': 'CARGO SHIP SAFETY EQUIPMENT CERTIFICATE'
    })
    if mapping:
        print(f'✅ Found mapping:')
        print(f'   cert_name: {mapping.get("cert_name")}')
        print(f'   abbreviation: {mapping.get("abbreviation")}')
        print(f'   usage_count: {mapping.get("usage_count", 0)}')
    else:
        print('❌ No mapping found')
    print()
    
    # 2. Check actual certificates in database
    print('STEP 2: Check actual certificates with this name')
    print('-' * 80)
    cursor = db.certificates.find({
        'cert_name': {'$regex': 'CARGO.*SHIP.*SAFETY.*EQUIPMENT', '$options': 'i'}
    }).limit(10)
    
    certs = await cursor.to_list(length=10)
    
    if certs:
        print(f'Found {len(certs)} certificate(s):')
        print()
        for i, cert in enumerate(certs, 1):
            print(f'Certificate {i}:')
            print(f'  cert_name: {cert.get("cert_name")}')
            print(f'  cert_abbreviation: {cert.get("cert_abbreviation")}')  # ← KEY!
            print(f'  ship_id: {cert.get("ship_id")}')
            print(f'  created_at: {cert.get("created_at", "N/A")}')
            print()
    else:
        print('No certificates found')
    print()
    
    # 3. Test abbreviation generation logic
    print('STEP 3: Test abbreviation generation logic')
    print('-' * 80)
    
    # Import the function
    sys.path.insert(0, '/app/backend')
    from app.utils.certificate_abbreviation import generate_certificate_abbreviation
    
    cert_name = "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE"
    result = await generate_certificate_abbreviation(cert_name)
    
    print(f'Input: {cert_name}')
    print(f'Generated abbreviation: {result}')
    print()
    
    # Close connection
    client.close()
    
    print('=' * 80)
    print('CONCLUSION:')
    print('=' * 80)
    if mapping and result:
        print(f'User-defined mapping: {mapping.get("abbreviation")}')
        print(f'Auto-generated: {result}')
        print(f'Match: {mapping.get("abbreviation") == result}')

if __name__ == '__main__':
    asyncio.run(main())
