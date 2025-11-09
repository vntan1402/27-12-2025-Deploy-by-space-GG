"""
Migration script to rename system_expiry to software_expiry in companies collection
"""
import asyncio
import os
from mongodb_database import MongoDB

async def migrate_expiry_field():
    """Migrate system_expiry field to software_expiry in companies collection"""
    
    # Initialize MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db = MongoDB(mongo_url)
    await db.connect()
    
    try:
        print("Starting migration: system_expiry -> software_expiry")
        
        # Find all companies with system_expiry field
        companies = await db.find("companies", {"system_expiry": {"$exists": True}})
        
        if not companies:
            print("No companies found with system_expiry field")
            return
        
        print(f"Found {len(companies)} companies to migrate")
        
        migrated_count = 0
        for company in companies:
            company_id = company.get('id')
            system_expiry_value = company.get('system_expiry')
            
            if system_expiry_value is not None:
                # Update: rename system_expiry to software_expiry
                update_result = await db.update_one(
                    "companies",
                    {"id": company_id},
                    {
                        "$set": {"software_expiry": system_expiry_value},
                        "$unset": {"system_expiry": ""}
                    }
                )
                
                if update_result:
                    migrated_count += 1
                    print(f"✅ Migrated company: {company.get('name_en', company.get('name_vn', company_id))}")
                else:
                    print(f"❌ Failed to migrate company: {company_id}")
        
        print(f"\n✅ Migration completed successfully!")
        print(f"Total companies migrated: {migrated_count}/{len(companies)}")
        
    except Exception as e:
        print(f"❌ Migration failed with error: {str(e)}")
        raise
    
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(migrate_expiry_field())
