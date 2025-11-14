"""
Export Company Database Script
Exports all data for a specific company to a JSON file for offline use
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import zipfile
from typing import Any, Dict, List

class CompanyDatabaseExporter:
    def __init__(self, mongo_url: str, db_name: str = "ship_management"):
        self.client = AsyncIOMotorClient(mongo_url)
        self.database = self.client[db_name]
        
    async def export_company_data(self, company_id: str, output_dir: str = "/tmp"):
        """
        Export all data for a specific company
        
        Args:
            company_id: Company UUID to export
            output_dir: Directory to save export file
            
        Returns:
            Path to the exported ZIP file
        """
        print(f"🔄 Starting export for company: {company_id}")
        
        # Get company info
        company = await self.database.companies.find_one({"id": company_id})
        if not company:
            raise Exception(f"Company {company_id} not found")
        
        company_name = company.get("name_en", "unknown")
        print(f"📦 Exporting data for: {company_name}")
        
        export_data = {
            "company_id": company_id,
            "company_name": company_name,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "format": "mongodb_json",
            "collections": {}
        }
        
        # Collections to export
        collections_config = [
            {
                "name": "companies",
                "filter": {"id": company_id},
                "description": "Company information"
            },
            {
                "name": "users",
                "filter": {"company": company_id},
                "description": "Company users"
            },
            {
                "name": "ships",
                "filter": {"company": company_id},
                "description": "Company ships"
            },
            {
                "name": "certificates",
                "filter": {"company_id": company_id},
                "description": "Ship certificates"
            },
            {
                "name": "crew_members",
                "filter": {"company_id": company_id},
                "description": "Crew members"
            },
            {
                "name": "crew_certificates",
                "filter": {"company_id": company_id},
                "description": "Crew certificates"
            },
            {
                "name": "audit_certificates",
                "filter": {"company_id": company_id},
                "description": "Audit certificates"
            },
            {
                "name": "survey_reports",
                "filter": {"company_id": company_id},
                "description": "Survey reports"
            },
            {
                "name": "test_reports",
                "filter": {"company_id": company_id},
                "description": "Test reports"
            },
            {
                "name": "drawings_manuals",
                "filter": {"company_id": company_id},
                "description": "Drawings & Manuals"
            },
            {
                "name": "approval_documents",
                "filter": {"company_id": company_id},
                "description": "Approval documents"
            }
        ]
        
        total_documents = 0
        
        for config in collections_config:
            collection_name = config["name"]
            filter_query = config["filter"]
            description = config["description"]
            
            print(f"  📋 Exporting {collection_name}...", end=" ")
            
            try:
                # Get documents from collection
                cursor = self.database[collection_name].find(filter_query)
                documents = await cursor.to_list(length=None)
                
                # Convert ObjectId and datetime to string for JSON serialization
                serialized_docs = []
                for doc in documents:
                    serialized_doc = self._serialize_document(doc)
                    serialized_docs.append(serialized_doc)
                
                export_data["collections"][collection_name] = {
                    "description": description,
                    "count": len(serialized_docs),
                    "documents": serialized_docs
                }
                
                total_documents += len(serialized_docs)
                print(f"✅ {len(serialized_docs)} documents")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                export_data["collections"][collection_name] = {
                    "description": description,
                    "count": 0,
                    "error": str(e),
                    "documents": []
                }
        
        # Add summary
        export_data["summary"] = {
            "total_collections": len(collections_config),
            "total_documents": total_documents,
            "exported_collections": list(export_data["collections"].keys())
        }
        
        # Create ZIP file with database JSON and metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"company_{company_id[:8]}_{timestamp}.zip"
        filepath = os.path.join(output_dir, filename)
        
        print(f"\n📦 Creating ZIP file: {filename}")
        
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add database JSON
            database_json = json.dumps(export_data, indent=2, ensure_ascii=False)
            zipf.writestr("database.json", database_json)
            
            # Add metadata
            metadata = {
                "company_id": company_id,
                "company_name": company_name,
                "exported_at": export_data["exported_at"],
                "version": "1.0",
                "total_documents": total_documents,
                "file_size_mb": len(database_json) / (1024 * 1024)
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
            
            # Add README
            readme = f"""
# Company Database Export

**Company:** {company_name}
**Company ID:** {company_id}
**Exported:** {export_data["exported_at"]}
**Total Documents:** {total_documents}

## Collections Included:

"""
            for coll_name, coll_data in export_data["collections"].items():
                readme += f"- **{coll_name}**: {coll_data['count']} documents - {coll_data['description']}\n"
            
            readme += """
## How to Import:

1. Upload this ZIP file to the system
2. Use the Import Database API endpoint
3. System will restore all data for this company

## Structure:

- `database.json`: Complete database dump
- `metadata.json`: Export metadata
- `README.txt`: This file
"""
            zipf.writestr("README.txt", readme)
        
        file_size = os.path.getsize(filepath) / (1024 * 1024)
        print(f"\n✅ Export completed successfully!")
        print(f"📁 File: {filepath}")
        print(f"📊 Size: {file_size:.2f} MB")
        print(f"📋 Total documents: {total_documents}")
        
        return filepath
    
    def _serialize_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to JSON-serializable format"""
        from bson import ObjectId
        
        serialized = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                serialized[key] = self._serialize_document(value)
            elif isinstance(value, list):
                serialized[key] = [
                    self._serialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                serialized[key] = value
        
        return serialized
    
    async def close(self):
        """Close database connection"""
        self.client.close()


async def main():
    """
    Example usage
    """
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    
    exporter = CompanyDatabaseExporter(mongo_url)
    
    try:
        # Example: Export company with ID
        company_id = "0a6eaf96-0aaf-4793-89be-65d62cb7953c"  # Replace with actual company ID
        
        output_path = await exporter.export_company_data(
            company_id=company_id,
            output_dir="/tmp"
        )
        
        print(f"\n🎉 Export completed: {output_path}")
        print(f"\n💡 Next steps:")
        print(f"   1. Download this file")
        print(f"   2. Set up local MongoDB")
        print(f"   3. Import this file to work offline")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await exporter.close()


if __name__ == "__main__":
    asyncio.run(main())
