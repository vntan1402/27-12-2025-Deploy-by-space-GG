import uuid
import logging
from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks

from app.models.other_audit_document import OtherAuditDocumentCreate, OtherAuditDocumentUpdate, OtherAuditDocumentResponse, BulkDeleteOtherAuditDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class OtherAuditDocumentService:
    """Service for Other Audit Document operations"""
    
    collection_name = "other_audit_documents"
    
    @staticmethod
    async def get_other_audit_documents(ship_id: Optional[str], current_user: UserResponse) -> List[OtherAuditDocumentResponse]:
        """Get other audit documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(OtherAuditDocumentService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("document_name") and doc.get("doc_name"):
                doc["document_name"] = doc.get("doc_name")
            
            if not doc.get("date") and doc.get("issue_date"):
                doc["date"] = doc.get("issue_date")
            
            if not doc.get("note") and doc.get("notes"):
                doc["note"] = doc.get("notes")
            
            if not doc.get("document_name"):
                doc["document_name"] = "Untitled Document"
            
            if not doc.get("status"):
                doc["status"] = "Valid"
            
            result.append(OtherAuditDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_other_audit_document_by_id(doc_id: str, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Get other audit document by ID"""
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        # Backward compatibility
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("date") and doc.get("issue_date"):
            doc["date"] = doc.get("issue_date")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        if not doc.get("status"):
            doc["status"] = "Valid"
        
        return OtherAuditDocumentResponse(**doc)
    
    @staticmethod
    async def create_other_audit_document(doc_data: OtherAuditDocumentCreate, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Create new other audit document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(OtherAuditDocumentService.collection_name, doc_dict)
        
        logger.info(f"✅ Other Audit Document created: {doc_dict['document_name']}")
        
        return OtherAuditDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_other_audit_document(doc_id: str, doc_data: OtherAuditDocumentUpdate, current_user: UserResponse) -> OtherAuditDocumentResponse:
        """Update other audit document"""
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(OtherAuditDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Other Audit Document updated: {doc_id}")
        
        return OtherAuditDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_other_audit_document(doc_id: str, current_user: UserResponse) -> dict:
        """Delete other audit document"""
        doc = await mongo_db.find_one(OtherAuditDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Audit Document not found")
        
        await mongo_db.delete(OtherAuditDocumentService.collection_name, {"id": doc_id})
        
        logger.info(f"✅ Other Audit Document deleted: {doc_id}")
        
        return {"message": "Other Audit Document deleted successfully"}
    
    @staticmethod
    async def bulk_delete_other_audit_documents(request: BulkDeleteOtherAuditDocumentRequest, current_user: UserResponse) -> dict:
        """Bulk delete other audit documents"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await OtherAuditDocumentService.delete_other_audit_document(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} other audit documents")
        
        return {
            "message": f"Successfully deleted {deleted_count} other audit documents",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, current_user: UserResponse) -> dict:
        """Check if other audit document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        existing = await mongo_db.find_one(OtherAuditDocumentService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
