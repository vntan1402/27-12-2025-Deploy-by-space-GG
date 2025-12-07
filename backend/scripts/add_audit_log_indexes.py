#!/usr/bin/env python3
"""
Add indexes for crew_audit_logs collection
Run this script after implementing audit log system
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


async def create_audit_log_indexes():
    """Create all indexes for crew_audit_logs collection"""
    
    mongo_url = os.getenv('MONGO_URL')
    if not mongo_url:
        print("❌ MONGO_URL not found in environment variables")
        return False
    
    print("🔗 Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    collection = db.crew_audit_logs
    
    try:
        # Test connection
        await db.command('ping')
        print("✅ Connected to MongoDB\n")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False
    
    indexes_created = 0
    indexes_existed = 0
    
    print("=" * 80)
    print("CREATING AUDIT LOG INDEXES")
    print("=" * 80)
    print()
    
    # Define indexes
    index_definitions = [
        {
            'name': 'company_id_1_performed_at_-1',
            'keys': [('company_id', 1), ('performed_at', -1)],
            'description': 'Multi-tenant + timeline sorting'
        },
        {
            'name': 'entity_id_1_performed_at_-1',
            'keys': [('entity_id', 1), ('performed_at', -1)],
            'description': 'Crew lookup + timeline'
        },
        {
            'name': 'company_id_1_performed_by_1_performed_at_-1',
            'keys': [('company_id', 1), ('performed_by', 1), ('performed_at', -1)],
            'description': 'User activity filter'
        },
        {
            'name': 'company_id_1_action_1_performed_at_-1',
            'keys': [('company_id', 1), ('action', 1), ('performed_at', -1)],
            'description': 'Action type filter'
        },
        {
            'name': 'company_id_1_ship_name_1_performed_at_-1',
            'keys': [('company_id', 1), ('ship_name', 1), ('performed_at', -1)],
            'description': 'Ship filter'
        },
        {
            'name': 'expires_at_1_ttl',
            'keys': [('expires_at', 1)],
            'description': 'TTL index for 3-year retention',
            'options': {'expireAfterSeconds': 0}
        }
    ]
    
    for idx_def in index_definitions:
        name = idx_def['name']
        keys = idx_def['keys']
        description = idx_def['description']
        options = idx_def.get('options', {})
        
        try:
            # Check if index exists
            existing_indexes = await collection.list_indexes().to_list(None)
            index_exists = any(idx.get('name') == name for idx in existing_indexes)
            
            if index_exists:
                print(f"⏭️  {name}")
                print(f"   Already exists - skipping")
                print(f"   📝 {description}")
                print()
                indexes_existed += 1
            else:
                # Create index
                if options:
                    await collection.create_index(keys, name=name, **options)
                else:
                    await collection.create_index(keys, name=name)
                
                print(f"✅ {name}")
                print(f"   Created successfully")
                print(f"   📝 {description}")
                if options:
                    print(f"   ⚙️  Options: {options}")
                print()
                indexes_created += 1
                
        except Exception as e:
            print(f"❌ {name}")
            print(f"   Failed: {str(e)}")
            print()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Indexes created:  {indexes_created}")
    print(f"⏭️  Indexes existed:  {indexes_existed}")
    print(f"📊 Total processed: {indexes_created + indexes_existed}")
    print()
    
    # Verify final state
    print("=" * 80)
    print("FINAL INDEX STATE")
    print("=" * 80)
    
    all_indexes = await collection.list_indexes().to_list(None)
    print(f"📁 crew_audit_logs: {len(all_indexes)} indexes")
    for idx in all_indexes:
        name = idx.get('name', 'unknown')
        keys = idx.get('key', {})
        ttl = idx.get('expireAfterSeconds', None)
        
        key_str = ', '.join([f'{k}: {v}' for k, v in keys.items()])
        ttl_str = f' [TTL: {ttl}s]' if ttl is not None else ''
        print(f"   • {name}{ttl_str}")
        print(f"     ({key_str})")
    
    print()
    
    client.close()
    return True


async def main():
    """Main execution"""
    print("\n🚀 Starting audit log index creation...\n")
    
    success = await create_audit_log_indexes()
    
    if success:
        print("✅ All audit log indexes created successfully!")
        print("\n💡 Next steps:")
        print("   1. Restart backend: sudo supervisorctl restart backend")
        print("   2. Test audit log API endpoints")
        print("   3. Integrate logging into crew operations")
        return 0
    else:
        print("⚠️  Failed to create indexes")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
