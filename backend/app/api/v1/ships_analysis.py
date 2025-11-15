import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.models.user import UserResponse
from app.core.security import get_current_user
from app.services.certificate_service import CertificateService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/analyze-ship-certificate")
async def analyze_ship_certificate_endpoint(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze ship certificate PDF to extract ship information
    """
    try:
        logger.info(f"📄 Starting ship certificate analysis for: {file.filename}")
        
        # Use certificate analysis service (it's generic enough for ship certs)
        result = await CertificateService.analyze_certificate_file(file, None, current_user)
        
        logger.info(f"✅ Analysis service returned: {type(result)}")
        
        # Ensure we always return the expected format
        if result is None:
            logger.warning("⚠️ Analysis returned None")
            return {
                "success": False,
                "analysis": None,
                "message": "Analysis returned no data"
            }
        
        # If result doesn't have success field, wrap it
        if "success" not in result:
            logger.info("🔄 Wrapping result with success field")
            return {
                "success": True,
                "analysis": result,
                "message": "Ship certificate analyzed successfully"
            }
        
        logger.info(f"📤 Returning result with success={result.get('success')}")
        return result
        
    except HTTPException as http_exc:
        logger.error(f"❌ HTTP Exception: {http_exc.detail}")
        # Convert HTTPException to structured response
        return {
            "success": False,
            "analysis": None,
            "message": f"Error: {http_exc.detail}"
        }
    except Exception as e:
        logger.error(f"❌ Ship certificate analysis error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Always return structured response, never null
        return {
            "success": False,
            "analysis": None,
            "message": f"Analysis failed: {str(e)}"
        }
