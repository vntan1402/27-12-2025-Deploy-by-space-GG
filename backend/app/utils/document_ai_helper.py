"""
Document AI Helper - Generic Implementation
Handles Google Document AI integration for all document types
"""
import logging
import aiohttp
import asyncio
import base64
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# GENERIC CORE FUNCTION
# ============================================================================

async def analyze_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any],
    document_type: str
) -> Dict[str, Any]:
    """
    Generic Document AI analysis for any document type
    
    Supported document types:
    - 'survey_report': Survey reports (class surveys, inspections)
    - 'test_report': Test reports (equipment maintenance, testing)
    - 'audit_report': Audit reports (ISM, ISPS, MLC)
    - 'drawings_manual': Technical drawings and manuals
    - 'other': Other maritime documents
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type (e.g., "application/pdf")
        document_ai_config: Config with project_id, processor_id, location, apps_script_url
        document_type: Type of document
    
    Returns:
        Dict with success status and summary text
    """
    try:
        # Validate document_type
        SUPPORTED_TYPES = [
            'survey_report',
            'test_report', 
            'audit_report',
            'drawings_manual',
            'other'
        ]
        
        if document_type not in SUPPORTED_TYPES:
            logger.warning(f"⚠️ Unsupported document_type: {document_type}, using 'other'")
            document_type = 'other'
        
        # Extract config
        project_id = document_ai_config.get("project_id")
        processor_id = document_ai_config.get("processor_id")
        location = document_ai_config.get("location", "us")
        
        if not project_id or not processor_id:
            logger.error("❌ Missing Document AI configuration")
            return {
                "success": False,
                "message": "Missing Document AI configuration (project_id or processor_id)"
            }
        
        logger.info(f"🤖 Calling Google Document AI for {document_type}: {filename}")
        logger.info(f"   Project: {project_id}, Processor: {processor_id}, Location: {location}")
        
        # Get Apps Script URL
        apps_script_url = document_ai_config.get("apps_script_url")
        
        if not apps_script_url:
            logger.error("❌ Apps Script URL not configured")
            return {
                "success": False,
                "message": "Apps Script URL not configured for Document AI"
            }
        
        # Encode file to base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        logger.info(f"📦 Encoded file to base64: {len(file_base64)} chars")
        
        # Build request payload
        payload = {
            "action": "analyze_maritime_document_ai",
            "file_content": file_base64,
            "filename": filename,
            "content_type": content_type,
            "project_id": project_id,
            "processor_id": processor_id,
            "location": location,
            "document_type": document_type  # Dynamic value
        }
        
        logger.info(f"📤 Sending request to Apps Script: {apps_script_url}")
        
        # Call Apps Script with timeout (180s for large PDFs >15 pages)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        summary = result.get("data", {}).get("summary", "")
                        confidence = result.get("data", {}).get("confidence", 0.0)
                        
                        logger.info(f"✅ Document AI completed for {document_type}")
                        logger.info(f"   Summary length: {len(summary)} characters")
                        logger.info(f"   Confidence: {confidence}")
                        
                        return {
                            "success": True,
                            "data": {
                                "summary": summary,
                                "confidence": confidence
                            }
                        }
                    else:
                        error_msg = result.get("message", "Unknown error")
                        logger.error(f"❌ Document AI failed for {document_type}: {error_msg}")
                        return {
                            "success": False,
                            "message": error_msg
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Apps Script HTTP error: {response.status}")
                    logger.error(f"   Response: {error_text[:500]}")
                    return {
                        "success": False,
                        "message": f"Apps Script HTTP error: {response.status}"
                    }
    
    except asyncio.TimeoutError:
        logger.error(f"❌ Document AI timed out for {document_type} after 120 seconds")
        return {
            "success": False,
            "message": "Document AI request timed out (>2 minutes)"
        }
    
    except aiohttp.ClientError as e:
        logger.error(f"❌ Network error for {document_type}: {e}")
        return {
            "success": False,
            "message": f"Network error: {str(e)}"
        }
    
    except Exception as e:
        logger.error(f"❌ Unexpected error for {document_type}: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Document AI error: {str(e)}"
        }


# ============================================================================
# TYPE-SPECIFIC WRAPPERS (Backward Compatibility)
# ============================================================================

async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze survey report using Google Document AI
    
    Wrapper for backward compatibility.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config dict
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Survey Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='survey_report'
    )


async def analyze_test_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze test report using Google Document AI
    
    Test reports are maintenance/testing records for lifesaving and firefighting equipment.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config dict
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Test Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='test_report'
    )


async def analyze_audit_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze audit report using Google Document AI
    
    Audit reports include ISM, ISPS, and MLC audits.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config dict
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Audit Report wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='audit_report'
    )


async def analyze_other_document_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze other/generic document using Google Document AI
    
    Fallback wrapper for document types not covered by specific wrappers.
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config dict
    
    Returns:
        Dict with success status and summary text
    """
    logger.info(f"🔄 Other Document wrapper called for: {filename}")
    
    return await analyze_document_with_document_ai(
        file_content=file_content,
        filename=filename,
        content_type=content_type,
        document_ai_config=document_ai_config,
        document_type='other'
    )


# ============================================================================
# PUBLIC API
# ============================================================================

__all__ = [
    'analyze_document_with_document_ai',
    'analyze_survey_report_with_document_ai',
    'analyze_test_report_with_document_ai',
    'analyze_audit_report_with_document_ai',
    'analyze_other_document_with_document_ai',
]
