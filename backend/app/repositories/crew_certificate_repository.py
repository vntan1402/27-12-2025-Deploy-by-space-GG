import logging
from typing import Optional, List, Dict, Any
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class CrewCertificateRepository:
    """Data access layer for crew certificates"""
    
    @staticmethod
    async def find_all(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all crew certificates with optional filters"""
        if filters:
            return await mongo_db.find_all("crew_certificates", filters)
        return await mongo_db.find_all("crew_certificates")
    
    @staticmethod
    async def find_by_id(cert_id: str) -> Optional[Dict[str, Any]]:
        """Find crew certificate by ID"""
        return await mongo_db.find_one("crew_certificates", {"id": cert_id})
    
    @staticmethod
    async def find_by_crew_id(crew_id: str) -> List[Dict[str, Any]]:
        """Find all certificates for a crew member"""
        return await mongo_db.find_all("crew_certificates", {"crew_id": crew_id})
    
    @staticmethod
    async def create(cert_data: Dict[str, Any]) -> str:
        """Create new crew certificate"""
        return await mongo_db.create("crew_certificates", cert_data)
    
    @staticmethod
    async def update(cert_id: str, update_data: Dict[str, Any]) -> bool:
        """Update crew certificate"""
        return await mongo_db.update("crew_certificates", {"id": cert_id}, update_data)
    
    @staticmethod
    async def delete(cert_id: str) -> bool:
        """Delete crew certificate"""
        return await mongo_db.delete("crew_certificates", {"id": cert_id})
    
    @staticmethod
    async def bulk_delete(cert_ids: List[str]) -> int:
        """Delete multiple crew certificates"""
        deleted_count = 0
        for cert_id in cert_ids:
            success = await mongo_db.delete("crew_certificates", {"id": cert_id})
            if success:
                deleted_count += 1
        return deleted_count
    
    @staticmethod
    async def check_duplicate(crew_id: str, cert_name: Optional[str] = None, cert_no: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Check if crew certificate already exists
        - If cert_name is provided: checks crew_id + cert_name (+ optional cert_no)
        - If only crew_id + cert_no: checks crew_id + cert_no (V1 pattern)
        """
        query = {"crew_id": crew_id}
        
        if cert_name:
            query["cert_name"] = cert_name
            if cert_no:
                query["cert_no"] = cert_no
        elif cert_no:
            # V1 pattern: only crew_id + cert_no
            query["cert_no"] = cert_no
        else:
            # Need at least one of cert_name or cert_no
            return None
            
        return await mongo_db.find_one("crew_certificates", query)
