import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.drawing_manual import DrawingManualCreate, DrawingManualUpdate, DrawingManualResponse, BulkDeleteDrawingManualRequest
from app.models.user import UserResponse
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class DrawingManualService:
    """Service for Drawing & Manual operations"""
    
    collection_name = "drawings_manuals"
    
    @staticmethod
    async def get_drawings_manuals(ship_id: Optional[str], current_user: UserResponse) -> List[DrawingManualResponse]:
        """Get drawings/manuals with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        docs = await mongo_db.find_all(DrawingManualService.collection_name, filters)
        
        # Handle backward compatibility
        result = []
        for doc in docs:
            if not doc.get("document_name") and doc.get("doc_name"):
                doc["document_name"] = doc.get("doc_name")
            
            if not doc.get("document_no") and doc.get("doc_no"):
                doc["document_no"] = doc.get("doc_no")
            
            if not doc.get("document_name"):
                doc["document_name"] = "Untitled Document"
            
            result.append(DrawingManualResponse(**doc))
        
        return result
    
    @staticmethod
    async def get_drawing_manual_by_id(doc_id: str, current_user: UserResponse) -> DrawingManualResponse:
        """Get drawing/manual by ID"""
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        if not doc.get("document_name") and doc.get("doc_name"):
            doc["document_name"] = doc.get("doc_name")
        
        if not doc.get("document_no") and doc.get("doc_no"):
            doc["document_no"] = doc.get("doc_no")
        
        if not doc.get("document_name"):
            doc["document_name"] = "Untitled Document"
        
        return DrawingManualResponse(**doc)
    
    @staticmethod
    async def create_drawing_manual(doc_data: DrawingManualCreate, current_user: UserResponse) -> DrawingManualResponse:
        """Create new drawing/manual"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(DrawingManualService.collection_name, doc_dict)
        
        logger.info(f"✅ Drawing/Manual created: {doc_dict['document_name']}")
        
        return DrawingManualResponse(**doc_dict)
    
    @staticmethod
    async def update_drawing_manual(doc_id: str, doc_data: DrawingManualUpdate, current_user: UserResponse) -> DrawingManualResponse:
        """Update drawing/manual"""
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(DrawingManualService.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        
        if not updated_doc.get("document_name") and updated_doc.get("doc_name"):
            updated_doc["document_name"] = updated_doc.get("doc_name")
        
        logger.info(f"✅ Drawing/Manual updated: {doc_id}")
        
        return DrawingManualResponse(**updated_doc)
    
    @staticmethod
    async def delete_drawing_manual(doc_id: str, current_user: UserResponse) -> dict:
        """Delete drawing/manual"""
        doc = await mongo_db.find_one(DrawingManualService.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Drawing/Manual not found")
        
        await mongo_db.delete(DrawingManualService.collection_name, {"id": doc_id})
        
        logger.info(f"✅ Drawing/Manual deleted: {doc_id}")
        
        return {"message": "Drawing/Manual deleted successfully"}
    
    @staticmethod
    async def bulk_delete_drawings_manuals(request: BulkDeleteDrawingManualRequest, current_user: UserResponse) -> dict:
        """Bulk delete drawings/manuals"""
        deleted_count = 0
        for doc_id in request.document_ids:
            try:
                await DrawingManualService.delete_drawing_manual(doc_id, current_user)
                deleted_count += 1
            except:
                continue
        
        logger.info(f"✅ Bulk deleted {deleted_count} drawings/manuals")
        
        return {
            "message": f"Successfully deleted {deleted_count} drawings/manuals",
            "deleted_count": deleted_count
        }
    
    @staticmethod
    async def check_duplicate(ship_id: str, document_name: str, document_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if drawing/manual is duplicate"""
        filters = {
            "ship_id": ship_id,
            "document_name": document_name
        }
        
        if document_no:
            filters["document_no"] = document_no
        
        existing = await mongo_db.find_one(DrawingManualService.collection_name, filters)
        
        return {
            "is_duplicate": existing is not None,
            "existing_id": existing.get("id") if existing else None
        }
