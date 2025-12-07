#!/usr/bin/env python3
"""
Add missing database indexes for optimal query performance
Run this script to add critical indexes for multi-tenant architecture
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


async def create_indexes():
    """Create all missing indexes for the maritime system"""
    
    mongo_url = os.getenv('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL not found in environment variables")
        return False
    
    print("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    
    try:
        # Test connection
        await db.command('ping')
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    
    indexes_created = 0
    indexes_existed = 0
    indexes_failed = 0
    
    print("=" * 80)
    print("ADDING MISSING INDEXES")
    print("=" * 80)
    print()
    
    # Define indexes to create
    index_definitions = [
        # PRIORITY P0 - CRITICAL
        {
            "collection": "crew",
            "name": "company_id_1",
            "keys": [("company_id", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Filter crews by company (90% of queries)"
        },
        {
            "collection": "crew",
            "name": "company_id_1_status_1",
            "keys": [("company_id", 1), ("status", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Crew list with status filter (Sign on/Standby/Leave)"
        },
        {
            "collection": "crew",
            "name": "company_id_1_ship_sign_on_1",
            "keys": [("company_id", 1), ("ship_sign_on", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Get all crew on a specific ship"
        },
        {
            "collection": "crew_certificates",
            "name": "company_id_1_crew_id_1",
            "keys": [("company_id", 1), ("crew_id", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Get all certificates for a crew member"
        },
        {
            "collection": "crew_assignment_history",
            "name": "company_id_1_crew_id_1",
            "keys": [("company_id", 1), ("crew_id", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Get assignment history for a crew member"
        },
        {
            "collection": "audit_certificates",
            "name": "ship_id_1",
            "keys": [("ship_id", 1)],
            "priority": "P0 - CRITICAL",
            "description": "Get audit certificates for a ship"
        },
        
        # PRIORITY P1 - HIGH
        {
            "collection": "crew",
            "name": "company_id_1_passport_1",
            "keys": [("company_id", 1), ("passport", 1)],
            "priority": "P1 - HIGH",
            "description": "Search crew by passport number"
        },
        {
            "collection": "crew",
            "name": "company_id_1_created_at_-1",
            "keys": [("company_id", 1), ("created_at", -1)],
            "priority": "P1 - HIGH",
            "description": "Crew list sorted by creation date (newest first)"
        },
        {
            "collection": "crew_certificates",
            "name": "company_id_1_cert_expiry_1",
            "keys": [("company_id", 1), ("cert_expiry", 1)],
            "priority": "P1 - HIGH",
            "description": "Monitor expiring certificates"
        },
        {
            "collection": "crew_assignment_history",
            "name": "company_id_1_crew_id_1_action_date_-1",
            "keys": [("company_id", 1), ("crew_id", 1), ("action_date", -1)],
            "priority": "P1 - HIGH",
            "description": "Assignment history timeline (newest first)"
        },
        {
            "collection": "ships",
            "name": "company_1_standalone",
            "keys": [("company", 1)],
            "priority": "P1 - HIGH",
            "description": "Filter ships by company (standalone index)"
        },
        
        # PRIORITY P2 - MEDIUM
        {
            "collection": "crew_certificates",
            "name": "company_id_1_status_1",
            "keys": [("company_id", 1), ("status", 1)],
            "priority": "P2 - MEDIUM",
            "description": "Filter certificates by status (Valid/Expired)"
        },
        {
            "collection": "certificates",
            "name": "ship_id_1_valid_date_1",
            "keys": [("ship_id", 1), ("valid_date", 1)],
            "priority": "P2 - MEDIUM",
            "description": "Ship certificates sorted by expiry"
        },
        {
            "collection": "audit_certificates",
            "name": "ship_id_1_valid_date_1",
            "keys": [("ship_id", 1), ("valid_date", 1)],
            "priority": "P2 - MEDIUM",
            "description": "Audit certificates sorted by expiry"
        },
    ]
    
    # Group by priority
    priorities = {}
    for idx_def in index_definitions:
        priority = idx_def["priority"]
        if priority not in priorities:
            priorities[priority] = []
        priorities[priority].append(idx_def)
    
    # Create indexes by priority
    for priority in ["P0 - CRITICAL", "P1 - HIGH", "P2 - MEDIUM"]:
        if priority not in priorities:
            continue
        
        print(f"\n{'=' * 80}")
        print(f"🔴 {priority}")
        print(f"{'=' * 80}\n")
        
        for idx_def in priorities[priority]:
            collection_name = idx_def["collection"]
            index_name = idx_def["name"]
            keys = idx_def["keys"]
            description = idx_def["description"]
            
            try:
                collection = db[collection_name]
                
                # Check if index already exists
                existing_indexes = await collection.list_indexes().to_list(None)
                index_exists = any(idx.get('name') == index_name for idx in existing_indexes)
                
                if index_exists:
                    print(f"⏭️  {collection_name}.{index_name}")
                    print(f"   Already exists - skipping")
                    print(f"   📝 {description}")
                    print()
                    indexes_existed += 1
                else:
                    # Create index
                    await collection.create_index(keys, name=index_name)
                    print(f"✅ {collection_name}.{index_name}")
                    print(f"   Created successfully")
                    print(f"   📝 {description}")
                    print()
                    indexes_created += 1
                    
            except Exception as e:
                print(f"❌ {collection_name}.{index_name}")
                print(f"   Failed: {str(e)}")
                print()
                indexes_failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Indexes created:  {indexes_created}")
    print(f"⏭️  Indexes existed:  {indexes_existed}")
    print(f"❌ Indexes failed:   {indexes_failed}")
    print(f"📊 Total processed: {indexes_created + indexes_existed + indexes_failed}")
    print()
    
    # Verify final state
    print("=" * 80)
    print("FINAL INDEX COUNT PER COLLECTION")
    print("=" * 80)
    
    collections_to_check = [
        "crew", "crew_certificates", "crew_assignment_history",
        "ships", "certificates", "audit_certificates"
    ]
    
    for coll_name in collections_to_check:
        try:
            collection = db[coll_name]
            indexes = await collection.list_indexes().to_list(None)
            print(f"📁 {coll_name}: {len(indexes)} indexes")
        except Exception as e:
            print(f"📁 {coll_name}: Error - {str(e)}")
    
    print()
    
    client.close()
    
    return indexes_failed == 0


async def main():
    """Main execution"""
    print("\n🚀 Starting index creation process...\n")
    
    success = await create_indexes()
    
    if success:
        print("✅ All indexes created successfully!")
        print("\n💡 Next steps:")
        print("   1. Run query performance tests")
        print("   2. Monitor slow query log")
        print("   3. Verify index usage with .explain()")
        return 0
    else:
        print("⚠️  Some indexes failed to create")
        print("   Check the error messages above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
