import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
import json

logger = logging.getLogger(__name__)

class MongoDatabase:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.connected = False
        
    async def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            mongo_url = os.getenv('MONGO_URL')
            if not mongo_url:
                raise Exception("MONGO_URL environment variable not set")
            
            self.client = AsyncIOMotorClient(mongo_url)
            
            # Test connection
            await self.client.admin.command('ismaster')
            
            db_name = os.getenv('DB_NAME', 'ship_management')
            self.database = self.client[db_name]
            
            # Create indexes for better performance
            await self.create_indexes()
            
            self.connected = True
            logger.info(f"Successfully connected to MongoDB: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.database.users.create_index("username", unique=True)
            await self.database.users.create_index("email", unique=True)
            await self.database.users.create_index([("role", 1), ("is_active", 1)])
            await self.database.users.create_index("company")
            
            # Companies collection indexes  
            await self.database.companies.create_index("tax_id", unique=True)
            await self.database.companies.create_index([("name_en", 1), ("name_vn", 1)])
            
            # Ships collection indexes
            # Create compound unique index on (imo, company) to allow same IMO for different companies
            await self.database.ships.create_index([("imo", 1), ("company", 1)], unique=True, sparse=True)
            await self.database.ships.create_index("name")
            
            # Certificates collection indexes
            await self.database.certificates.create_index([("ship_id", 1), ("type", 1)])
            await self.database.certificates.create_index("expiry_date")
            
            # Certificate abbreviation mappings collection indexes
            await self.database.certificate_abbreviation_mappings.create_index("cert_name", unique=True)
            await self.database.certificate_abbreviation_mappings.create_index("created_by")
            await self.database.certificate_abbreviation_mappings.create_index([("usage_count", -1)])
            
            # Usage tracking indexes
            await self.database.usage_tracking.create_index([("timestamp", -1)])
            await self.database.usage_tracking.create_index("user_id")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    # Generic CRUD operations
    async def create(self, collection: str, data: Dict[str, Any]) -> str:
        """Create a new document"""
        try:
            if 'created_at' not in data:
                data['created_at'] = datetime.now(timezone.utc)
            
            result = await self.database[collection].insert_one(data)
            logger.info(f"Created document in {collection}: {result.inserted_id}")
            return str(result.inserted_id)
        
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {collection}: {e}")
            raise Exception(f"Document with this key already exists in {collection}")
        except Exception as e:
            logger.error(f"Error creating document in {collection}: {e}")
            raise

    async def find_all(self, collection: str, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find all documents matching filter"""
        try:
            filter_dict = filter_dict or {}
            cursor = self.database[collection].find(filter_dict)
            documents = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return documents
        
        except Exception as e:
            logger.error(f"Error finding documents in {collection}: {e}")
            raise

    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document matching filter"""
        try:
            document = await self.database[collection].find_one(filter_dict)
            
            if document and '_id' in document:
                document['_id'] = str(document['_id'])
            
            return document
        
        except Exception as e:
            logger.error(f"Error finding document in {collection}: {e}")
            raise

    async def update(self, collection: str, filter_dict: Dict[str, Any], update_data: Dict[str, Any], upsert: bool = False) -> bool:
        """Update document(s) matching filter"""
        try:
            update_data['updated_at'] = datetime.now(timezone.utc)
            
            result = await self.database[collection].update_one(
                filter_dict, 
                {"$set": update_data},
                upsert=upsert
            )
            
            success = result.modified_count > 0 or (upsert and result.upserted_id is not None)
            if success:
                if result.upserted_id:
                    logger.info(f"Upserted document in {collection}: {result.upserted_id}")
                else:
                    logger.info(f"Updated document in {collection}")
            else:
                logger.warning(f"No document updated in {collection} with filter: {filter_dict}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error updating document in {collection}: {e}")
            raise

    async def delete(self, collection: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete document(s) matching filter"""
        try:
            result = await self.database[collection].delete_one(filter_dict)
            
            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted document from {collection}")
            else:
                logger.warning(f"No document deleted from {collection} with filter: {filter_dict}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error deleting document from {collection}: {e}")
            raise

    async def count(self, collection: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents matching filter"""
        try:
            filter_dict = filter_dict or {}
            count = await self.database[collection].count_documents(filter_dict)
            return count
        
        except Exception as e:
            logger.error(f"Error counting documents in {collection}: {e}")
            raise

    # Specialized methods for common operations
    async def find_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username"""
        return await self.find_one("users", {"username": username})

    async def find_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        return await self.find_one("users", {"email": email})

    async def find_users_by_company(self, company: str) -> List[Dict[str, Any]]:
        """Find all users belonging to a company"""
        return await self.find_all("users", {"company": company, "is_active": True})

    async def find_company_by_tax_id(self, tax_id: str) -> Optional[Dict[str, Any]]:
        """Find company by tax ID"""
        return await self.find_one("companies", {"tax_id": tax_id})

    async def find_ship_by_imo(self, imo: str) -> Optional[Dict[str, Any]]:
        """Find ship by IMO number"""
        return await self.find_one("ships", {"imo": imo})

    async def find_certificates_by_ship(self, ship_id: str) -> List[Dict[str, Any]]:
        """Find all certificates for a ship"""
        return await self.find_all("certificates", {"ship_id": ship_id})

    async def get_usage_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get usage statistics for the last N days"""
        from datetime import timedelta
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        return await self.find_all("usage_tracking", {
            "timestamp": {"$gte": start_date}
        })

    # Migration helpers
    async def migrate_from_json(self, json_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
        """Migrate data from JSON structure to MongoDB"""
        migration_results = {}
        
        for collection_name, documents in json_data.items():
            if not documents:
                migration_results[collection_name] = 0
                continue
                
            try:
                # Insert documents in batch
                if documents:
                    result = await self.database[collection_name].insert_many(documents)
                    migration_results[collection_name] = len(result.inserted_ids)
                    logger.info(f"Migrated {len(result.inserted_ids)} documents to {collection_name}")
                else:
                    migration_results[collection_name] = 0
                    
            except Exception as e:
                logger.error(f"Error migrating {collection_name}: {e}")
                migration_results[collection_name] = -1
        
        return migration_results

    async def export_to_json(self) -> Dict[str, List[Dict[str, Any]]]:
        """Export all data to JSON structure and save to files (for backup)"""
        import os
        import json
        
        collections = [
            "users", "companies", "ships", "certificates", 
            "ai_config", "usage_tracking", "ai_analyses"
        ]
        
        export_data = {}
        data_path = "/app/backend/data"
        
        # Create data directory if it doesn't exist
        os.makedirs(data_path, exist_ok=True)
        
        for collection in collections:
            try:
                documents = await self.find_all(collection)
                # Remove MongoDB _id field for clean export
                for doc in documents:
                    if '_id' in doc:
                        del doc['_id']
                
                export_data[collection] = documents
                
                # Save to JSON file
                json_file = os.path.join(data_path, f"{collection}.json")
                with open(json_file, 'w') as f:
                    json.dump(documents, f, indent=2, default=str)
                
                logger.info(f"Exported {len(documents)} documents from {collection} to {json_file}")
                
            except Exception as e:
                logger.error(f"Error exporting {collection}: {e}")
                export_data[collection] = []
        
        return export_data

    async def import_from_json(self) -> Dict[str, int]:
        """Import data from JSON files (for restore from backup)"""
        import os
        import json
        
        data_path = "/app/backend/data"
        collections = [
            "users", "companies", "ships", "certificates", 
            "ai_config", "usage_tracking", "ai_analyses"
        ]
        
        import_results = {}
        
        for collection in collections:
            try:
                json_file = os.path.join(data_path, f"{collection}.json")
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    if data:
                        # Clear existing data in collection
                        await self.database[collection].delete_many({})
                        
                        # Insert new data
                        if isinstance(data, list) and data:
                            await self.database[collection].insert_many(data)
                            import_results[collection] = len(data)
                            logger.info(f"Imported {len(data)} documents to {collection}")
                        else:
                            import_results[collection] = 0
                    else:
                        import_results[collection] = 0
                else:
                    logger.warning(f"JSON file not found for {collection}")
                    import_results[collection] = 0
                    
            except Exception as e:
                logger.error(f"Error importing {collection}: {e}")
                import_results[collection] = -1
        
        return import_results

# Global database instance
mongo_db = MongoDatabase()