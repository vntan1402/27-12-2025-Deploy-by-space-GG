import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.approval_document import ApprovalDocumentCreate, ApprovalDocumentUpdate, ApprovalDocumentResponse, BulkDeleteApprovalDocumentRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class ApprovalDocumentService:
    """Service for Approval Document operations"""
    
    collection_name = "approval_documents"
    
    @staticmethod
    async def get_approval_documents(ship_id: Optional[str], current_user: UserResponse) -> List[ApprovalDocumentResponse]:
        """Get approval documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(ApprovalDocumentService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("approval_document_name") and doc.get("doc_name"):
                doc["approval_document_name"] = doc.get("doc_name")
            
            if not doc.get("approval_document_no") and doc.get("doc_no"):
                doc["approval_document_no"] = doc.get("doc_no")
            
            if not doc.get("note") and doc.get("notes"):
                doc["note"] = doc.get("notes")
            
            if not doc.get("approval_document_name"):
                doc["approval_document_name"] = "Untitled Approval Document"
            
            if not doc.get("status"):
                doc["status"] = "Unknown"
            
            result.append(ApprovalDocumentResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_approval_document_by_id(doc_id: str, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Get approval document by ID"""
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        # Backward compatibility
        if not doc.get("approval_document_name") and doc.get("doc_name"):
            doc["approval_document_name"] = doc.get("doc_name")
        
        if not doc.get("approval_document_no") and doc.get("doc_no"):
            doc["approval_document_no"] = doc.get("doc_no")
        
        if not doc.get("note") and doc.get("notes"):
            doc["note"] = doc.get("notes")
        
        if not doc.get("approval_document_name"):
            doc["approval_document_name"] = "Untitled Approval Document"
        
        if not doc.get("status"):
            doc["status"] = "Unknown"
        
        return ApprovalDocumentResponse(**doc)
    
    @staticmethod
    async def create_approval_document(doc_data: ApprovalDocumentCreate, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Create new approval document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(ApprovalDocumentService.collection_name, doc_dict)
        
        logger.info(f"✅ Approval Document created: {doc_dict['approval_document_name']}")
        
        return ApprovalDocumentResponse(**doc_dict)
    
    @staticmethod
    async def update_approval_document(doc_id: str, doc_data: ApprovalDocumentUpdate, current_user: UserResponse) -> ApprovalDocumentResponse:
        """Update approval document"""
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(ApprovalDocumentService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("approval_document_name") and updated_doc.get("doc_name"):
            updated_doc["approval_document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Approval Document updated: {doc_id}")
        
        return ApprovalDocumentResponse(**updated_doc)
    
    @staticmethod
    async def delete_approval_document(doc_id: str, current_user: UserResponse) -> dict:
        """Delete approval document"""
        doc = await mongo_db.find_one(ApprovalDocumentService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Approval Document not found")
        
        await mongo_db.delete(ApprovalDocumentService.collection_name, {"id": doc_id})
        
        logger.info(f"✅ Approval Document deleted: {doc_id}")
        
        return {"message": "Approval Document deleted successfully"}
    
    @staticmethod
    async def bulk_delete_approval_documents(request: BulkDeleteApprovalDocumentRequest, current_user: UserResponse) -> dict:
        """Bulk delete approval documents"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await ApprovalDocumentService.delete_approval_document(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} approval documents")
        
        return {
            "message": f"Successfully deleted {deleted_count} approval documents",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, approval_document_name: str, approval_document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if approval document is duplicate"""
        filters = {
            "ship_id": ship_id,
            "approval_document_name": approval_document_name
        }
        
        if approval_document_no:
            filters["approval_document_no"] = approval_document_no
        
        existing = await mongo_db.find_one(ApprovalDocumentService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
