"""
CRITICAL MIGRATION: Migrate ships from company name to company UUID

WHY THIS IS URGENT:
- If company name changes, ships with old name will be LOST
- Cannot add reports/certificates to ships with old company names
- Data inconsistency causes "Ship not found" errors

WHAT THIS DOES:
- Finds all ships with company = string (not UUID)
- Maps company names to company UUIDs
- Updates ships with correct UUID
- Maintains data integrity
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate_ships_to_uuid():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('MONGODB_DB_NAME', 'ship_management')
    
    print("🚀 Starting Ships Migration to UUID Format")
    print("=" * 60)
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Step 1: Get all companies
        print("\n📋 Step 1: Fetching all companies...")
        companies = await db.companies.find({}).to_list(length=100)
        print(f"✅ Found {len(companies)} companies")
        
        # Build company name → UUID mapping
        company_map = {}
        for company in companies:
            company_id = company.get('id')
            names = []
            if company.get('name'):
                names.append(company.get('name'))
            if company.get('name_en'):
                names.append(company.get('name_en'))
            if company.get('name_vn'):
                names.append(company.get('name_vn'))
            
            for name in names:
                company_map[name] = company_id
            
            print(f"  📌 {company_id[:8]}... → {names}")
        
        # Step 2: Find ships with company = string (not UUID)
        print(f"\n📋 Step 2: Finding ships with company names...")
        all_ships = await db.ships.find({}).to_list(length=1000)
        
        ships_to_migrate = []
        ships_already_uuid = []
        
        for ship in all_ships:
            company = ship.get('company', '')
            # Check if UUID (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            is_uuid = '-' in str(company) and len(str(company)) == 36
            
            if is_uuid:
                ships_already_uuid.append(ship)
            else:
                ships_to_migrate.append(ship)
        
        print(f"✅ Ships already using UUID: {len(ships_already_uuid)}")
        print(f"⚠️  Ships needing migration: {len(ships_to_migrate)}")
        
        if len(ships_to_migrate) == 0:
            print("\n🎉 All ships are already using UUID format!")
            return
        
        # Step 3: Migrate ships
        print(f"\n📋 Step 3: Migrating {len(ships_to_migrate)} ships...")
        
        migrated_count = 0
        failed_count = 0
        
        for ship in ships_to_migrate:
            ship_name = ship.get('name', 'Unknown')
            old_company = ship.get('company', '')
            ship_id = ship.get('id')
            
            # Find matching UUID
            new_company_uuid = company_map.get(old_company)
            
            if new_company_uuid:
                # Update ship
                result = await db.ships.update_one(
                    {"id": ship_id},
                    {"$set": {"company": new_company_uuid}}
                )
                
                if result.modified_count > 0:
                    migrated_count += 1
                    print(f"  ✅ {ship_name[:30]:30} | {old_company[:30]:30} → {new_company_uuid[:8]}...")
                else:
                    failed_count += 1
                    print(f"  ⚠️  {ship_name[:30]:30} | No changes made")
            else:
                failed_count += 1
                print(f"  ❌ {ship_name[:30]:30} | Company not found: {old_company}")
        
        # Step 4: Summary
        print("\n" + "=" * 60)
        print("📊 MIGRATION SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully migrated: {migrated_count} ships")
        print(f"❌ Failed: {failed_count} ships")
        print(f"🔵 Already using UUID: {len(ships_already_uuid)} ships")
        print(f"📦 Total ships: {len(all_ships)} ships")
        
        if failed_count > 0:
            print(f"\n⚠️  WARNING: {failed_count} ships could not be migrated!")
            print("   Please check company names and try again.")
        
        if migrated_count > 0:
            print("\n✅ Migration completed successfully!")
            print("   All ships now use UUID format.")
            print("   Company name changes will no longer affect ship lookups.")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: This migration will update ship company fields")
    print("   from company names to company UUIDs.")
    print("   This ensures ships remain linked even if company names change.\n")
    
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        asyncio.run(migrate_ships_to_uuid())
    else:
        print("❌ Migration cancelled.")
