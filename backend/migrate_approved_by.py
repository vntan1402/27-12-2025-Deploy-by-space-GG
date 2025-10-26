"""
Migration Script: Normalize Approved By for Existing Drawings & Manuals
This script updates all existing drawings_manuals records to normalize the approved_by field
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongodb_database import MongoDatabase
from issued_by_abbreviation import normalize_issued_by
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_drawings_manuals_approved_by():
    """
    Migrate all existing drawings_manuals records to normalize approved_by field
    """
    try:
        # Initialize database
        db = MongoDatabase()
        await db.connect()
        
        logger.info("🔍 Starting migration for Drawings & Manuals - Approved By normalization...")
        
        # Get all drawings_manuals records
        all_documents = await db.find_all("drawings_manuals", {})
        
        if not all_documents:
            logger.info("✅ No documents found to migrate")
            return
        
        logger.info(f"📊 Found {len(all_documents)} documents to process")
        
        updated_count = 0
        skipped_count = 0
        
        for doc in all_documents:
            document_id = doc.get('id')
            approved_by = doc.get('approved_by')
            
            if not approved_by:
                logger.info(f"⏭️  Skipping document {document_id} - No approved_by value")
                skipped_count += 1
                continue
            
            # Normalize approved_by
            original_approved_by = approved_by
            normalized_approved_by = normalize_issued_by(original_approved_by)
            
            # Only update if different
            if normalized_approved_by != original_approved_by:
                # Update in database
                await db.update_one(
                    "drawings_manuals",
                    {"id": document_id},
                    {"$set": {"approved_by": normalized_approved_by}}
                )
                
                logger.info(f"✅ Updated document {document_id}: '{original_approved_by}' → '{normalized_approved_by}'")
                updated_count += 1
            else:
                logger.info(f"ℹ️  Document {document_id}: '{original_approved_by}' (no change needed)")
                skipped_count += 1
        
        logger.info(f"\n📊 Migration Summary:")
        logger.info(f"   Total documents processed: {len(all_documents)}")
        logger.info(f"   ✅ Updated: {updated_count}")
        logger.info(f"   ⏭️  Skipped: {skipped_count}")
        logger.info(f"\n✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_drawings_manuals_approved_by())
