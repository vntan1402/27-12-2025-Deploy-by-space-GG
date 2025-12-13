"""
Migration script: Rename next_survey -> next_audit and next_survey_type -> next_audit_type
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def migrate_fields():
    """Migrate next_survey fields to next_audit in company_certificates collection"""
    
    # Get MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'ship_management')
    
    print(f"🔗 Connecting to MongoDB: {mongo_url}")
    print(f"📦 Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    collection = db['company_certificates']
    
    # Count documents
    total_docs = await collection.count_documents({})
    print(f"📊 Total documents in collection: {total_docs}")
    
    if total_docs == 0:
        print("✅ No documents to migrate")
        client.close()
        return
    
    # Find documents with old field names
    docs_to_update = await collection.count_documents({
        "$or": [
            {"next_survey": {"$exists": True}},
            {"next_survey_type": {"$exists": True}}
        ]
    })
    
    print(f"🔍 Documents with old field names: {docs_to_update}")
    
    if docs_to_update == 0:
        print("✅ All documents already migrated")
        client.close()
        return
    
    # Migrate documents
    print("\n🔄 Starting migration...")
    updated_count = 0
    
    cursor = collection.find({
        "$or": [
            {"next_survey": {"$exists": True}},
            {"next_survey_type": {"$exists": True}}
        ]
    })
    
    async for doc in cursor:
        update_ops = {}
        rename_ops = {}
        
        # Rename next_survey to next_audit
        if "next_survey" in doc:
            rename_ops["next_survey"] = "next_audit"
        
        # Rename next_survey_type to next_audit_type
        if "next_survey_type" in doc:
            rename_ops["next_survey_type"] = "next_audit_type"
        
        if rename_ops:
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$rename": rename_ops}
            )
            updated_count += 1
            
            if updated_count % 10 == 0:
                print(f"   ✅ Migrated {updated_count} documents...")
    
    print(f"\n✅ Migration complete! Updated {updated_count} documents")
    
    # Verify migration
    remaining = await collection.count_documents({
        "$or": [
            {"next_survey": {"$exists": True}},
            {"next_survey_type": {"$exists": True}}
        ]
    })
    
    print(f"🔍 Verification: {remaining} documents still have old field names")
    
    if remaining == 0:
        print("✅ All documents successfully migrated!")
    else:
        print(f"⚠️ Warning: {remaining} documents not migrated")
    
    client.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB Field Migration Script")
    print("next_survey -> next_audit")
    print("next_survey_type -> next_audit_type")
    print("=" * 60)
    print()
    
    asyncio.run(migrate_fields())
    
    print()
    print("=" * 60)
    print("Migration completed")
    print("=" * 60)
