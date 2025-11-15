"""
Background task utilities with retry mechanism for async operations
"""
import logging
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

# Retry decorator for background tasks
def with_retry(
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 10
):
    """
    Decorator to add retry logic to background tasks
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 2)
        max_wait: Maximum wait time in seconds (default: 10)
    """
    def decorator(func):
        @wraps(func)
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def delete_file_background(
    file_id: str,
    company_id: str,
    document_type: str,
    document_name: str,
    gdrive_service_class
):
    """
    Background task to delete file from Google Drive with retry logic
    
    Args:
        file_id: Google Drive file ID
        company_id: Company ID for Drive configuration
        document_type: Type of document (for logging)
        document_name: Name of document (for logging)
        gdrive_service_class: GDriveService class reference
    """
    try:
        logger.info(f"🔄 Starting background deletion for {document_type}: {file_id} ({document_name})")
        
        @with_retry(max_attempts=3, min_wait=2, max_wait=10)
        async def _delete_with_retry():
            result = await gdrive_service_class.delete_file(
                file_id=file_id,
                company_id=company_id,
                permanent_delete=False  # Move to trash by default
            )
            if not result.get("success"):
                raise Exception(f"Drive deletion failed: {result.get('message')}")
            return result
        
        result = await _delete_with_retry()
        logger.info(f"✅ Successfully deleted {document_type} file in background: {file_id} ({document_name})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to delete {document_type} file after retries: {file_id} ({document_name}) - Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}
