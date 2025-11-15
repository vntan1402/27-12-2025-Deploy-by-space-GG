"""Script to generate all document type API routes"""

DOCUMENT_TYPES = [
    ("survey-reports", "survey_reports", "Survey Report", True),
    ("test-reports", "test_reports", "Test Report", True),
    ("drawings-manuals", "drawings_manuals", "Drawing/Manual", False),
    ("other-documents", "other_documents", "Other Document", False),
    ("ism-documents", "ism_documents", "ISM Document", False),
    ("isps-documents", "isps_documents", "ISPS Document", False),
    ("mlc-documents", "mlc_documents", "MLC Document", False),
    ("supply-documents", "supply_documents", "Supply Document", False),
]

template = '''import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query

from app.models.document import DocumentCreate, DocumentUpdate, DocumentResponse, BulkDeleteDocumentRequest
from app.models.user import UserResponse, UserRole
from app.services.document_service import GenericDocumentService
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service for this document type
service = GenericDocumentService("{collection}", "{name}")

def check_editor_permission(current_user: UserResponse = Depends(get_current_user)):
    """Check if user has editor or higher permission"""
    if current_user.role not in [UserRole.EDITOR, UserRole.MANAGER, UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.SYSTEM_ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user

@router.get("", response_model=List[DocumentResponse])
async def get_documents(
    ship_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get {name}s, optionally filtered by ship_id"""
    try:
        return await service.get_documents(ship_id, current_user)
    except Exception as e:
        logger.error(f"❌ Error fetching {name}s: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to fetch {name}s")

@router.get("/{{doc_id}}", response_model=DocumentResponse)
async def get_document_by_id(
    doc_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific {name} by ID"""
    try:
        return await service.get_document_by_id(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching {name} {{doc_id}}: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to fetch {name}")

@router.post("", response_model=DocumentResponse)
async def create_document(
    doc_data: DocumentCreate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Create new {name} (Editor+ role required)"""
    try:
        return await service.create_document(doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating {name}: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to create {name}")

@router.put("/{{doc_id}}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    doc_data: DocumentUpdate,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Update {name} (Editor+ role required)"""
    try:
        return await service.update_document(doc_id, doc_data, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating {name}: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to update {name}")

@router.delete("/{{doc_id}}")
async def delete_document(
    doc_id: str,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Delete {name} (Editor+ role required)"""
    try:
        return await service.delete_document(doc_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting {name}: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to delete {name}")

@router.post("/bulk-delete")
async def bulk_delete_documents(
    request: BulkDeleteDocumentRequest,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Bulk delete {name}s (Editor+ role required)"""
    try:
        return await service.bulk_delete_documents(request, current_user)
    except Exception as e:
        logger.error(f"❌ Error bulk deleting {name}s: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to bulk delete {name}s")

@router.post("/check-duplicate")
async def check_duplicate_document(
    ship_id: str,
    doc_name: str,
    doc_no: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check if {name} is duplicate"""
    try:
        return await service.check_duplicate(ship_id, doc_name, doc_no, current_user)
    except Exception as e:
        logger.error(f"❌ Error checking duplicate: {{e}}")
        raise HTTPException(status_code=500, detail="Failed to check duplicate")
{analyze_endpoint}
'''

analyze_template = '''
@router.post("/analyze-file")
async def analyze_document_file(
    file: UploadFile = File(...),
    ship_id: Optional[str] = None,
    current_user: UserResponse = Depends(check_editor_permission)
):
    """Analyze {name} file using AI (Editor+ role required)"""
    try:
        return await service.analyze_file(file, ship_id, current_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing {name} file: {{e}}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze {name}: {{str(e)}}")
'''

for route_name, collection, doc_name, has_analyze in DOCUMENT_TYPES:
    filename = f"/app/backend/app/api/v1/{route_name.replace('-', '_')}.py"
    
    analyze_code = analyze_template.format(name=doc_name) if has_analyze else ""
    
    content = template.format(
        collection=collection,
        name=doc_name,
        analyze_endpoint=analyze_code
    )
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"✅ Created: {filename}")

print("\n🎉 All document route files created!")
