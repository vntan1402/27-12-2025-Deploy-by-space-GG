"""
Document AI Helper for Survey Reports
Handles Google Document AI integration
"""
import logging
import aiohttp
import base64
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def analyze_survey_report_with_document_ai(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze survey report using Google Document AI
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        content_type: MIME type
        document_ai_config: Config with project_id, processor_id, location
    
    Returns:
        Dict with success status and summary text
    """
    try:
        # Extract config
        project_id = document_ai_config.get("project_id")
        processor_id = document_ai_config.get("processor_id")
        location = document_ai_config.get("location", "us")
        
        if not project_id or not processor_id:
            return {
                "success": False,
                "message": "Missing Document AI configuration"
            }
        
        logger.info(f"🤖 Calling Google Document AI for: {filename}")
        logger.info(f"   Project: {project_id}, Processor: {processor_id}, Location: {location}")
        
        # Get Apps Script URL from config
        apps_script_url = document_ai_config.get("apps_script_url")
        
        if not apps_script_url:
            return {
                "success": False,
                "message": "Apps Script URL not configured for Document AI"
            }
        
        # Encode file to base64
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Build request payload
        payload = {
            "action": "analyze_document",
            "file_content": file_base64,
            "filename": filename,
            "content_type": content_type,
            "document_ai": {
                "project_id": project_id,
                "processor_id": processor_id,
                "location": location
            }
        }
        
        # Call Apps Script
        async with aiohttp.ClientSession() as session:
            async with session.post(
                apps_script_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 min timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("success"):
                        summary = result.get("data", {}).get("summary", "")
                        
                        logger.info(f"✅ Document AI analysis completed ({len(summary)} chars)")
                        
                        return {
                            "success": True,
                            "data": {
                                "summary": summary,
                                "confidence": result.get("data", {}).get("confidence", 0.0)
                            }
                        }
                    else:
                        error_msg = result.get("message", "Unknown error")
                        logger.error(f"❌ Document AI failed: {error_msg}")
                        return {
                            "success": False,
                            "message": error_msg
                        }
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Apps Script request failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "message": f"Apps Script error: {response.status}"
                    }
    
    except asyncio.TimeoutError:
        logger.error("❌ Document AI request timed out")
        return {
            "success": False,
            "message": "Document AI request timed out (>2 minutes)"
        }
    except Exception as e:
        logger.error(f"❌ Document AI error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": f"Document AI error: {str(e)}"
        }
