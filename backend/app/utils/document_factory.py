"""
Generic document factory for creating document type modules
All document types follow same pattern: CRUD + bulk operations + file handling
"""
from typing import Type
from pydantic import BaseModel
from datetime import datetime

def create_document_models(doc_type_name: str):
    """
    Create pydantic models for a document type
    Returns: (BaseModel, CreateModel, UpdateModel, ResponseModel, BulkDeleteRequest)
    """
    
    class DocumentBase(BaseModel):
        ship_id: str
        doc_name: str
        doc_no: str | None = None
        issued_by: str | None = None
        issue_date: datetime | str | None = None
        valid_date: datetime | str | None = None
        category: str = doc_type_name.lower().replace(" ", "_")
        file_uploaded: bool = False
        file_name: str | None = None
        file_size: int | None = None
        notes: str | None = None
        
        class Config:
            from_attributes = True
    
    class DocumentCreate(DocumentBase):
        pass
    
    class DocumentUpdate(BaseModel):
        doc_name: str | None = None
        doc_no: str | None = None
        issued_by: str | None = None
        issue_date: datetime | str | None = None
        valid_date: datetime | str | None = None
        notes: str | None = None
        
        class Config:
            from_attributes = True
    
    class DocumentResponse(DocumentBase):
        id: str
        created_at: datetime
        
        class Config:
            from_attributes = True
    
    class BulkDeleteRequest(BaseModel):
        document_ids: list[str]
    
    return DocumentBase, DocumentCreate, DocumentUpdate, DocumentResponse, BulkDeleteRequest


# Document type configurations
DOCUMENT_TYPES = {
    "survey-reports": {
        "collection": "survey_reports",
        "name": "Survey Report",
        "has_analyze": True,
    },
    "test-reports": {
        "collection": "test_reports",
        "name": "Test Report",
        "has_analyze": True,
    },
    "drawings-manuals": {
        "collection": "drawings_manuals",
        "name": "Drawing/Manual",
        "has_analyze": False,
    },
    "other-documents": {
        "collection": "other_documents",
        "name": "Other Document",
        "has_analyze": False,
    },
    "ism-documents": {
        "collection": "ism_documents",
        "name": "ISM Document",
        "has_analyze": False,
    },
    "isps-documents": {
        "collection": "isps_documents",
        "name": "ISPS Document",
        "has_analyze": False,
    },
    "mlc-documents": {
        "collection": "mlc_documents",
        "name": "MLC Document",
        "has_analyze": False,
    },
    "supply-documents": {
        "collection": "supply_documents",
        "name": "Supply Document",
        "has_analyze": False,
    },
}
