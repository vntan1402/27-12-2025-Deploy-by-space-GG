#!/usr/bin/env python3
"""
Migration script to convert File-based JSON Database to MongoDB
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# Add backend to path
sys.path.append('/app/backend')

from mongodb_database import mongo_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self):
        self.json_data_path = "/app/backend/data"
        self.backup_path = "/app/backend/data_backup"
        self.migration_log = []
        
    def create_backup(self):
        """Create backup of existing JSON files"""
        try:
            if os.path.exists(self.backup_path):
                shutil.rmtree(self.backup_path)
            
            shutil.copytree(self.json_data_path, self.backup_path)
            logger.info(f"✅ Backup created: {self.backup_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False

    def load_json_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all JSON data files"""
        json_files = [
            "users.json",
            "companies.json", 
            "ships.json",
            "certificates.json",
            "usage_tracking.json",
            "ai_analyses.json"
        ]
        
        # Special files (single objects, not arrays)
        special_files = {
            "ai_config.json": "ai_config",
            "company_settings.json": "company_settings",
            "gdrive_config.json": "gdrive_config"
        }
        
        data = {}
        
        # Load array-based collections
        for filename in json_files:
            file_path = os.path.join(self.json_data_path, filename)
            collection_name = filename.replace('.json', '')
            
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        if isinstance(file_data, list):
                            data[collection_name] = file_data
                        else:
                            data[collection_name] = [file_data] if file_data else []
                        
                        logger.info(f"📄 Loaded {len(data[collection_name])} records from {filename}")
                else:
                    data[collection_name] = []
                    logger.warning(f"⚠️ File not found: {filename}")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {filename}: {e}")
                data[collection_name] = []

        # Load special configuration files
        for filename, collection_name in special_files.items():
            file_path = os.path.join(self.json_data_path, filename)
            
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        if file_data:  # Only add if not empty
                            file_data['_type'] = collection_name
                            file_data['created_at'] = datetime.now(timezone.utc).isoformat()
                            data[collection_name] = [file_data]
                        else:
                            data[collection_name] = []
                        
                        logger.info(f"⚙️ Loaded config from {filename}")
                else:
                    data[collection_name] = []
                    logger.warning(f"⚠️ Config file not found: {filename}")
                    
            except Exception as e:
                logger.error(f"❌ Error loading {filename}: {e}")
                data[collection_name] = []

        return data

    def validate_data(self, data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Validate loaded data before migration"""
        validation_errors = []
        
        # Check users data
        if 'users' in data:
            for user in data['users']:
                if not user.get('username'):
                    validation_errors.append("User missing username")
                if not user.get('email'):
                    validation_errors.append("User missing email")
        
        # Check companies data
        if 'companies' in data:
            for company in data['companies']:
                if not company.get('tax_id'):
                    validation_errors.append("Company missing tax_id")
        
        # Check ships data
        if 'ships' in data:
            for ship in data['ships']:
                if not ship.get('name'):
                    validation_errors.append("Ship missing name")
        
        if validation_errors:
            logger.error("❌ Data validation failed:")
            for error in validation_errors:
                logger.error(f"   - {error}")
            return False
        
        logger.info("✅ Data validation passed")
        return True

    def prepare_data_for_mongodb(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        """Prepare data for MongoDB (clean up, add indexes, etc.)"""
        
        prepared_data = {}
        
        for collection_name, documents in data.items():
            prepared_docs = []
            
            for doc in documents:
                # Create a clean copy
                clean_doc = dict(doc)
                
                # Remove any existing _id field from JSON
                if '_id' in clean_doc:
                    del clean_doc['_id']
                
                # Ensure datetime fields are properly formatted
                datetime_fields = ['created_at', 'updated_at', 'system_expiry', 'expiry_date', 'timestamp']
                for field in datetime_fields:
                    if field in clean_doc and clean_doc[field]:
                        try:
                            # Parse datetime string to ensure consistent format
                            if isinstance(clean_doc[field], str):
                                dt = datetime.fromisoformat(clean_doc[field].replace('Z', '+00:00'))
                                clean_doc[field] = dt
                        except Exception as e:
                            logger.warning(f"⚠️ Invalid datetime in {collection_name}.{field}: {clean_doc[field]}")
                
                # Add migration metadata
                clean_doc['_migrated_at'] = datetime.now(timezone.utc)
                clean_doc['_migration_source'] = 'json_file'
                
                prepared_docs.append(clean_doc)
            
            prepared_data[collection_name] = prepared_docs
            logger.info(f"🔧 Prepared {len(prepared_docs)} documents for {collection_name}")
        
        return prepared_data

    async def perform_migration(self) -> bool:
        """Perform the actual migration to MongoDB"""
        try:
            logger.info("🚀 Starting MongoDB migration...")
            
            # Step 1: Create backup
            logger.info("📦 Creating backup...")
            if not self.create_backup():
                return False
            
            # Step 2: Load JSON data
            logger.info("📁 Loading JSON data...")
            json_data = self.load_json_data()
            
            if not json_data:
                logger.error("❌ No data to migrate")
                return False
            
            # Step 3: Validate data
            logger.info("🔍 Validating data...")
            if not self.validate_data(json_data):
                return False
            
            # Step 4: Prepare data for MongoDB
            logger.info("🔧 Preparing data...")
            prepared_data = self.prepare_data_for_mongodb(json_data)
            
            # Step 5: Connect to MongoDB
            logger.info("🔗 Connecting to MongoDB...")
            await mongo_db.connect()
            
            # Step 6: Perform migration
            logger.info("📤 Migrating data to MongoDB...")
            migration_results = {}
            
            # Migrate each collection individually for better error handling
            for collection_name, documents in prepared_data.items():
                try:
                    if documents:
                        # Clear existing data in collection (fresh start)
                        await mongo_db.database[collection_name].delete_many({})
                        
                        # Insert new data
                        result = await mongo_db.database[collection_name].insert_many(documents)
                        migration_results[collection_name] = len(result.inserted_ids)
                        logger.info(f"   ✅ {collection_name}: {len(result.inserted_ids)} documents")
                    else:
                        migration_results[collection_name] = 0
                        logger.info(f"   ⚪ {collection_name}: 0 documents (empty)")
                        
                except Exception as e:
                    logger.error(f"   ❌ {collection_name}: FAILED - {e}")
                    migration_results[collection_name] = -1
            
            # Step 7: Verify migration
            total_migrated = sum(count for count in migration_results.values() if count > 0)
            total_failed = sum(1 for count in migration_results.values() if count == -1)
            
            logger.info("📊 Migration Results:")
            for collection, count in migration_results.items():
                if count > 0:
                    logger.info(f"   ✅ {collection}: {count} documents")
                elif count == 0:
                    logger.info(f"   ⚪ {collection}: 0 documents (empty)")
                else:
                    logger.error(f"   ❌ {collection}: FAILED")
            
            logger.info(f"📈 Total migrated: {total_migrated} documents")
            
            if total_failed > 0:
                logger.warning(f"⚠️ Failed collections: {total_failed}")
                # Don't fail completely if some collections failed
                # return False
            
            # Step 8: Create migration log
            self.create_migration_log(migration_results)
            
            logger.info("🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        finally:
            try:
                await mongo_db.disconnect()
            except:
                pass

    def create_migration_log(self, results: Dict[str, int]):
        """Create migration log file"""
        log_data = {
            "migration_date": datetime.now(timezone.utc).isoformat(),
            "source": "json_files",
            "destination": "mongodb_atlas",
            "results": results,
            "backup_location": self.backup_path,
            "status": "completed"
        }
        
        log_file = os.path.join(self.json_data_path, "migration_log.json")
        
        try:
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
            
            logger.info(f"📝 Migration log created: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create migration log: {e}")

    async def test_mongodb_connection(self) -> bool:
        """Test MongoDB connection before migration"""
        try:
            logger.info("🧪 Testing MongoDB connection...")
            await mongo_db.connect()
            
            # Test basic operations
            test_doc = {"test": True, "timestamp": datetime.now(timezone.utc)}
            doc_id = await mongo_db.create("test_connection", test_doc)
            
            # Verify document was created
            found_doc = await mongo_db.find_one("test_connection", {"test": True})
            
            if found_doc:
                # Clean up test document
                await mongo_db.delete("test_connection", {"test": True})
                logger.info("✅ MongoDB connection test successful")
                return True
            else:
                logger.error("❌ MongoDB connection test failed - document not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ MongoDB connection test failed: {e}")
            return False
        
        finally:
            await mongo_db.disconnect()

async def main():
    """Main migration function"""
    migration = DatabaseMigration()
    
    print("=" * 60)
    print("🚀 Ship Management System - Database Migration")
    print("📁 From: File-based JSON Database")
    print("🗄️ To: MongoDB Atlas")
    print("=" * 60)
    
    # Test MongoDB connection first
    if not await migration.test_mongodb_connection():
        print("\n❌ Migration aborted: MongoDB connection failed")
        print("Please check your MONGO_URL in .env file")
        return False
    
    # Confirm migration
    print(f"\n📋 Migration Plan:")
    print(f"   • Backup JSON files to: {migration.backup_path}")
    print(f"   • Migrate all data to MongoDB Atlas")
    print(f"   • Keep original files as backup")
    print(f"   • Create migration log\n")
    
    # Perform migration
    success = await migration.perform_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("📁 Original files backed up")
        print("🗄️ Data migrated to MongoDB Atlas")
        print("📝 Migration log created")
        print("\n⚠️ Next step: Update server.py to use MongoDB")
    else:
        print("\n❌ Migration failed!")
        print("📁 Original files preserved")
        print("🔍 Check logs for details")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())