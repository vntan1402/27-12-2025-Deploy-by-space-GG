import uuid
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException, UploadFile

from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse, BulkDeleteDocumentRequest
from app.models.user import UserResponse, UserRole
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)

class GenericDocumentService:
    """Generic service for all document types"""
    
    def __init__(self, collection_name: str, doc_type_name: str):
        self.collection_name = collection_name
        self.doc_type_name = doc_type_name
    
    async def get_documents(self, ship_id: Optional[str], current_user: UserResponse) -> List[DocumentResponse]:
        """Get documents with optional ship filter"""
        filters = {}
        if ship_id:
            filters["ship_id"] = ship_id
        
        documents = await mongo_db.find_all(self.collection_name, filters)
        
        # Add default values for backward compatibility with old data
        result = []
        for doc in documents:
            # Set default doc_name if missing
            if not doc.get("doc_name"):
                doc["doc_name"] = doc.get("document_name") or "Untitled Document"
            
            # Set default category if missing
            if not doc.get("category"):
                doc["category"] = self.collection_name.replace("_", "-")
            
            result.append(DocumentResponse(**doc))
        
        return result
    
    async def get_document_by_id(self, doc_id: str, current_user: UserResponse) -> DocumentResponse:
        """Get document by ID"""
        doc = await mongo_db.find_one(self.collection_name, {"id": doc_id})
        
        if not doc:
            raise HTTPException(status_code=404, detail=f"{self.doc_type_name} not found")
        
        return DocumentResponse(**doc)
    
    async def create_document(self, doc_data: DocumentCreate, current_user: UserResponse) -> DocumentResponse:
        """Create new document"""
        doc_dict = doc_data.dict()
        doc_dict["id"] = str(uuid.uuid4())
        doc_dict["created_at"] = datetime.now(timezone.utc)
        
        await mongo_db.create(self.collection_name, doc_dict)
        
        logger.info(f"✅ {self.doc_type_name} created: {doc_dict['doc_name']}")
        
        return DocumentResponse(**doc_dict)
    
    async def update_document(self, doc_id: str, doc_data: DocumentUpdate, current_user: UserResponse) -> DocumentResponse:
        """Update document"""
        doc = await mongo_db.find_one(self.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"{self.doc_type_name} not found")
        
        update_data = doc_data.dict(exclude_unset=True)
        
        if update_data:
            await mongo_db.update(self.collection_name, {"id": doc_id}, update_data)
        
        updated_doc = await mongo_db.find_one(self.collection_name, {"id": doc_id})
        
        logger.info(f"✅ {self.doc_type_name} updated: {doc_id}")
        
        return DocumentResponse(**updated_doc)
    
    async def delete_document(self, doc_id: str, current_user: UserResponse) -> dict:
        """Delete document"""
        doc = await mongo_db.find_one(self.collection_name, {"id": doc_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"{self.doc_type_name} not found")
        
        await mongo_db.delete(self.collection_name, {"id": doc_id})
        
        logger.info(f"✅ {self.doc_type_name} deleted: {doc_id}")
        
        return {"message": f"{self.doc_type_name} deleted successfully"}
    
    async def bulk_delete_documents(self, request: BulkDeleteDocumentRequest, current_user: UserResponse) -> dict:
        """Bulk delete documents"""
        deleted_count = 0
        for doc_id in request.document_ids:
            success = await mongo_db.delete(self.collection_name, {"id": doc_id})
            if success:
                deleted_count += 1
        
        logger.info(f"✅ Bulk deleted {deleted_count} {self.doc_type_name}s")
        
        return {
            "message": f"Successfully deleted {deleted_count} {self.doc_type_name}s",
            "deleted_count": deleted_count
        }
    
    async def check_duplicate(self, ship_id: str, doc_name: str, doc_no: Optional[str], current_user: UserResponse) -> dict:
        """Check if document is duplicate"""
        query = {"ship_id": ship_id, "doc_name": doc_name}
        if doc_no:
            query["doc_no"] = doc_no
        
        existing = await mongo_db.find_one(self.collection_name, query)
        
        return {
            "is_duplicate": existing is not None,
            "existing_document": DocumentResponse(**existing).dict() if existing else None
        }
    
    async def analyze_file(self, file: UploadFile, ship_id: Optional[str], current_user: UserResponse) -> dict:
        """Analyze document file using AI (mock implementation)"""
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum 10MB")
        
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        logger.info(f"📄 Analyzing {self.doc_type_name} file: {file.filename}")
        
        return {
            "success": True,
            "message": f"{self.doc_type_name} analyzed successfully (mock data)",
            "analysis": {
                "doc_name": f"Sample {self.doc_type_name}",
                "doc_no": "DOC-2024-001",
                "issued_by": "Classification Society",
                "issue_date": "15/01/2024",
                "valid_date": "15/01/2029"
            }
        }
