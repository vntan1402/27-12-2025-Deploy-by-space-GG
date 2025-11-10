"""
Export MongoDB data for production deployment
This script exports all important collections to JSON files
"""
import asyncio
from mongodb_database import mongo_db
import json
from datetime import datetime
from pathlib import Path

async def export_all_data():
    """Export all collections to JSON files"""
    await mongo_db.connect()
    
    # Create export directory
    export_dir = Path("production_data_export")
    export_dir.mkdir(exist_ok=True)
    
    # Collections to export
    collections = [
        'companies',
        'users', 
        'ships',
        'ship_certificates',
        'crew_list',
        'audit_certificates',
        'class_survey_reports',
        'drawings_manuals',
        'test_reports',
        'approval_documents',
        'system_settings'
    ]
    
    export_summary = {
        'export_date': datetime.now().isoformat(),
        'collections': {}
    }
    
    print("=" * 60)
    print("📦 EXPORTING DATABASE FOR PRODUCTION")
    print("=" * 60)
    
    for collection_name in collections:
        try:
            # Get all documents
            documents = await mongo_db.find_all(collection_name, {})
            
            # Convert datetime objects to strings for JSON serialization
            serializable_docs = []
            for doc in documents:
                serializable_doc = {}
                for key, value in doc.items():
                    if isinstance(value, datetime):
                        serializable_doc[key] = value.isoformat()
                    else:
                        serializable_doc[key] = value
                serializable_docs.append(serializable_doc)
            
            # Save to JSON file
            file_path = export_dir / f"{collection_name}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_docs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {collection_name:30s} → {len(documents):4d} records")
            export_summary['collections'][collection_name] = {
                'count': len(documents),
                'file': str(file_path)
            }
            
        except Exception as e:
            print(f"⚠️  {collection_name:30s} → Error: {str(e)}")
            export_summary['collections'][collection_name] = {
                'error': str(e)
            }
    
    # Save export summary
    summary_path = export_dir / "export_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(export_summary, f, indent=2)
    
    print("=" * 60)
    print(f"✅ Export completed!")
    print(f"📁 Location: {export_dir.absolute()}")
    print(f"📄 Summary: {summary_path}")
    print("=" * 60)
    
    await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(export_all_data())
