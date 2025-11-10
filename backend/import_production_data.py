"""
Import MongoDB data to production deployment
This script imports data from JSON files exported by export_production_data.py
"""
import asyncio
from mongodb_database import mongo_db
import json
from datetime import datetime
from pathlib import Path

async def import_all_data():
    """Import all collections from JSON files"""
    await mongo_db.connect()
    
    export_dir = Path("production_data_export")
    
    if not export_dir.exists():
        print("❌ Export directory not found!")
        print(f"Please run export_production_data.py first")
        return
    
    # Read summary
    summary_path = export_dir / "export_summary.json"
    if not summary_path.exists():
        print("❌ Export summary not found!")
        return
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    print("=" * 60)
    print("📥 IMPORTING DATA TO PRODUCTION")
    print(f"📅 Export Date: {summary['export_date']}")
    print("=" * 60)
    
    for collection_name, info in summary['collections'].items():
        if 'error' in info:
            print(f"⚠️  {collection_name:30s} → Skipped (export error)")
            continue
        
        file_path = Path(info['file'])
        if not file_path.exists():
            print(f"❌ {collection_name:30s} → File not found")
            continue
        
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            if not documents:
                print(f"⚠️  {collection_name:30s} → No data to import")
                continue
            
            # Convert ISO date strings back to datetime
            for doc in documents:
                for key, value in doc.items():
                    if isinstance(value, str) and 'T' in value and ':' in value:
                        try:
                            doc[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
            
            # Import to MongoDB
            # Check if collection already has data
            existing = await mongo_db.find_all(collection_name, {})
            
            if existing:
                print(f"⚠️  {collection_name:30s} → Already has {len(existing)} records")
                response = input(f"   Do you want to REPLACE all data in {collection_name}? (yes/no): ")
                if response.lower() != 'yes':
                    print(f"   Skipped {collection_name}")
                    continue
                
                # Delete all existing documents
                for doc in existing:
                    await mongo_db.delete(collection_name, {"id": doc.get("id")})
            
            # Insert all documents
            for doc in documents:
                await mongo_db.insert(collection_name, doc)
            
            print(f"✅ {collection_name:30s} → {len(documents):4d} records imported")
            
        except Exception as e:
            print(f"❌ {collection_name:30s} → Error: {str(e)}")
    
    print("=" * 60)
    print("✅ Import completed!")
    print("=" * 60)
    
    await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(import_all_data())
