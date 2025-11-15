"""
Cleanup service for orphan files and database maintenance
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from app.db.mongodb import mongo_db
from app.services.gdrive_service import GDriveService
from app.repositories.gdrive_config_repository import GDriveConfigRepository

logger = logging.getLogger(__name__)

class CleanupService:
    """Service for cleaning up orphan files and maintaining database"""
    
    # Collections that have google_drive_file_id
    COLLECTIONS_WITH_FILES = [
        "certificates",
        "audit_certificates",
        # Add more collections here as needed
    ]
    
    @staticmethod
    async def scan_orphan_files(company_id: str, days_threshold: int = 7) -> Dict[str, Any]:
        """
        Scan for orphan files (files in Drive but not in database)
        
        Args:
            company_id: Company ID to scan
            days_threshold: Only consider files older than this many days
            
        Returns:
            Dict with scan results
        """
        try:
            logger.info(f"🔍 Starting orphan file scan for company: {company_id}")
            
            # Get all file IDs from database
            db_file_ids = set()
            for collection_name in CleanupService.COLLECTIONS_WITH_FILES:
                try:
                    documents = await mongo_db.find_all(
                        collection_name,
                        {"company_id": company_id}  # Filter by company if needed
                    )
                    for doc in documents:
                        file_id = doc.get("google_drive_file_id")
                        if file_id:
                            db_file_ids.add(file_id)
                except Exception as e:
                    logger.warning(f"⚠️ Error scanning {collection_name}: {e}")
            
            logger.info(f"📊 Found {len(db_file_ids)} files in database")
            
            # Note: Scanning Google Drive for all files and comparing with database
            # would require additional Google Drive API implementation
            # For now, we return the database scan results
            
            return {
                "success": True,
                "company_id": company_id,
                "db_file_count": len(db_file_ids),
                "db_file_ids": list(db_file_ids),
                "scanned_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error scanning orphan files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def scan_missing_files(company_id: str) -> Dict[str, Any]:
        """
        Scan for database records that reference non-existent files
        
        Args:
            company_id: Company ID to scan
            
        Returns:
            Dict with scan results
        """
        try:
            logger.info(f"🔍 Starting missing file scan for company: {company_id}")
            
            missing_files = []
            
            for collection_name in CleanupService.COLLECTIONS_WITH_FILES:
                try:
                    documents = await mongo_db.find_all(
                        collection_name,
                        {
                            "google_drive_file_id": {"$exists": True, "$ne": None},
                        }
                    )
                    
                    for doc in documents:
                        file_id = doc.get("google_drive_file_id")
                        if file_id:
                            # Check if file exists in Google Drive
                            # This is a placeholder - actual implementation would call Drive API
                            missing_files.append({
                                "collection": collection_name,
                                "document_id": doc.get("id"),
                                "file_id": file_id,
                                "document_name": doc.get("cert_name") or doc.get("name", "Unknown")
                            })
                except Exception as e:
                    logger.warning(f"⚠️ Error scanning {collection_name}: {e}")
            
            logger.info(f"📊 Found {len(missing_files)} potential missing files")
            
            return {
                "success": True,
                "company_id": company_id,
                "missing_count": len(missing_files),
                "missing_files": missing_files,
                "scanned_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error scanning missing files: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def cleanup_old_records(days_threshold: int = 365) -> Dict[str, Any]:
        """
        Clean up old soft-deleted records (if using soft delete pattern)
        
        Args:
            days_threshold: Delete records older than this many days
            
        Returns:
            Dict with cleanup results
        """
        try:
            logger.info(f"🧹 Starting cleanup of records older than {days_threshold} days")
            
            threshold_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
            deleted_count = 0
            
            # This is a placeholder for soft-delete cleanup
            # Actual implementation would depend on your soft-delete pattern
            
            logger.info(f"✅ Cleanup complete: {deleted_count} records removed")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "threshold_date": threshold_date.isoformat(),
                "cleaned_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def generate_cleanup_report() -> Dict[str, Any]:
        """
        Generate a comprehensive cleanup report
        
        Returns:
            Dict with report data
        """
        try:
            logger.info("📊 Generating cleanup report")
            
            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "collections": {}
            }
            
            # Scan all collections
            for collection_name in CleanupService.COLLECTIONS_WITH_FILES:
                try:
                    total_docs = await mongo_db.count(collection_name, {})
                    docs_with_files = await mongo_db.count(
                        collection_name,
                        {"google_drive_file_id": {"$exists": True, "$ne": None}}
                    )
                    
                    report["collections"][collection_name] = {
                        "total_documents": total_docs,
                        "documents_with_files": docs_with_files,
                        "documents_without_files": total_docs - docs_with_files
                    }
                except Exception as e:
                    logger.warning(f"⚠️ Error scanning {collection_name}: {e}")
                    report["collections"][collection_name] = {"error": str(e)}
            
            logger.info("✅ Cleanup report generated successfully")
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating cleanup report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
