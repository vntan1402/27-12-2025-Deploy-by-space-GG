import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.other_doc import OtherDocumentCreate, OtherDocumentUpdate, OtherDocumentResponse, BulkDeleteOtherDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class OtherDocumentService:
    """Service for Other Document operations"""
    
    collection_name = "other_documents"
    
    @staticmethod
    async def get_other_documents(ship_id: Optional[str], current_user: UserResponse) -> List[OtherDocumentResponse]:
        """Get other documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(OtherDocumentService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("document_name") and doc.get("doc_name"):
                doc["document_name"] = doc.get("doc_name")
            
            if not doc.get("document_no") and doc.get("doc_no"):
                doc["document_no"] = doc.get("doc_no")
            
            if not doc.get("document_name"):
                doc["document_name"] = "Untitled Document"
            
            result.append(OtherDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_other_document_by_id(doc_id: str, current_user: UserResponse) -> OtherDocumentResponse:
        """Get other document by ID"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("document_no") and doc.get("doc_no"):
            doc["document_no"] = doc.get("doc_no")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        return OtherDocumentResponse(**doc)
    
    @staticmethod
    async def create_other_document(doc_data: OtherDocumentCreate, current_user: UserResponse) -> OtherDocumentResponse:
        """Create new other document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(OtherDocumentService.collection_name, doc_dict)
        
        logger.info(f"✅ Other Document created: {doc_dict['document_name']}")
        
        return OtherDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_other_document(doc_id: str, doc_data: OtherDocumentUpdate, current_user: UserResponse) -> OtherDocumentResponse:
        """Update other document"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(OtherDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Other Document updated: {doc_id}")
        
        return OtherDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_other_document(doc_id: str, current_user: UserResponse) -> dict:
        """Delete other document"""
        doc = await mongo_db.find_one(OtherDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Other Document not found")
        
        await mongo_db.delete(OtherDocumentService.collection_name, {"id": doc_id})
        
        logger.info(f"✅ Other Document deleted: {doc_id}")
        
        return {"message": "Other Document deleted successfully"}
    
    @staticmethod
    async def bulk_delete_other_documents(request: BulkDeleteOtherDocumentRequest, current_user: UserResponse) -> dict:
        """Bulk delete other documents"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await OtherDocumentService.delete_other_document(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} other documents")
        
        return {
            "message": f"Successfully deleted {deleted_count} other documents",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if other document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        if document_no:
            filters["document_no"] = document_no
        
        existing = await mongo_db.find_one(OtherDocumentService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
