import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class CertificateRepository:
    """Data access layer for certificates"""
    
    @staticmethod
    async def find_all(ship_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all certificates, optionally filtered by ship"""
        if ship_id:
            return await mongo_db.find_all("certificates", {"ship_id": ship_id})
        return await mongo_db.find_all("certificates")
    
    @staticmethod
    async def find_by_id(cert_id: str) -> Optional[Dict[str, Any]]:
        """Find certificate by ID"""
        return await mongo_db.find_one("certificates", {"id": cert_id})
    
    @staticmethod
    async def create(cert_data: Dict[str, Any]) -> str:
        """Create new certificate"""
        return await mongo_db.create("certificates", cert_data)
    
    @staticmethod
    async def update(cert_id: str, update_data: Dict[str, Any]) -> bool:
        """Update certificate"""
        return await mongo_db.update("certificates", {"id": cert_id}, update_data)
    
    @staticmethod
    async def delete(cert_id: str) -> bool:
        """Delete certificate"""
        return await mongo_db.delete("certificates", {"id": cert_id})
    
    @staticmethod
    async def bulk_delete(cert_ids: List[str]) -> int:
        """Delete multiple certificates"""
        deleted_count = 0
        for cert_id in cert_ids:
            success = await mongo_db.delete("certificates", {"id": cert_id})
            if success:
                deleted_count += 1
        return deleted_count
    
    @staticmethod
    async def check_duplicate(ship_id: str, cert_name: str, cert_no: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Check if certificate already exists"""
        query = {"ship_id": ship_id, "cert_name": cert_name}
        if cert_no:
            query["cert_no"] = cert_no
        return await mongo_db.find_one("certificates", query)
