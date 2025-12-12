"""
Company Certificate Analysis Service
Handles AI analysis and file processing
"""
import logging
import asyncio
from typing import Dict
from fastapi import HTTPException

from app.utils.pdf_text_extractor import extract_text_layer_from_pdf, merge_text_layer_and_document_ai
from app.utils.document_ai import analyze_document_with_document_ai
from app.utils.company_cert_ai import extract_company_cert_fields_from_summary

logger = logging.getLogger(__name__)

async def analyze_company_cert_file(
    file_content: bytes,
    filename: str,
    content_type: str,
    company_id: str,
    document_ai_config: Dict,
    ai_config: Dict
) -> Dict:
    """
    Analyze company certificate file with AI
    
    Returns:
        {
            "success": bool,
            "extracted_info": dict,
            "summary_text": str,
            "duplicate_warning": dict (optional)
        }
    """
    try:
        logger.info(f"🚀 Starting analysis for: {filename}")
        
        # ⭐ Parallel processing: Text Layer + Document AI
        text_layer_task = extract_text_layer_from_pdf(
            file_content=file_content,
            filename=filename
        )
        
        doc_ai_task = analyze_document_with_document_ai(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            document_ai_config=document_ai_config,
            document_type='company_certificate'
        )
        
        text_layer_result, doc_ai_result = await asyncio.gather(
            text_layer_task,
            doc_ai_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(text_layer_result, Exception):
            logger.warning(f"⚠️ Text layer extraction failed: {text_layer_result}")
            text_layer_result = {"success": False, "text": "", "has_text_layer": False}
        
        if isinstance(doc_ai_result, Exception):
            logger.error(f"❌ Document AI failed: {doc_ai_result}")
            doc_ai_result = {"success": False}
        
        # Merge results
        summary_text = merge_text_layer_and_document_ai(
            text_layer_result=text_layer_result,
            document_ai_result=doc_ai_result,
            filename=filename
        )
        
        if not summary_text or len(summary_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract sufficient text from document"
            )
        
        logger.info(f"✅ Merged summary: {len(summary_text)} chars")
        
        # Extract fields with AI
        extracted_info = await extract_company_cert_fields_from_summary(
            summary_text=summary_text,
            filename=filename,
            ai_config=ai_config
        )
        
        # Validate required fields
        if not extracted_info.get('cert_name') or not extracted_info.get('cert_no'):
            logger.warning(f"⚠️ Missing required fields in extraction")
        
        # Check for duplicates
        from app.db.mongodb import mongo_db
        duplicate_warning = None
        
        if extracted_info.get('cert_no'):
            existing_cert = await mongo_db.find_one(
                "company_certificates",
                {
                    "company": company_id,
                    "cert_no": extracted_info['cert_no']
                }
            )
            
            if existing_cert:
                duplicate_warning = {
                    "type": "duplicate",
                    "message": f"Certificate with number '{extracted_info['cert_no']}' already exists",
                    "existing_cert": {
                        "id": existing_cert.get('id'),
                        "cert_name": existing_cert.get('cert_name'),
                        "cert_no": existing_cert.get('cert_no')
                    }
                }
                logger.warning(f"⚠️ Duplicate found: {extracted_info['cert_no']}")
        
        return {
            "success": True,
            "extracted_info": extracted_info,
            "summary_text": summary_text,
            "duplicate_warning": duplicate_warning
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
