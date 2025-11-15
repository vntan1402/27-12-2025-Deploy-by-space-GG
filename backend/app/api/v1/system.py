"""
System Endpoints
"""
import logging
from datetime import datetime
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/current-datetime")
async def get_current_datetime():
    """
    Get current server date and time for debugging
    Migrated from backend-v1
    """
    now = datetime.now()
    return {
        "current_date": now.date().isoformat(),
        "current_datetime": now.isoformat(),
        "current_timestamp": now.timestamp(),
        "timezone": str(now.astimezone().tzinfo),
        "timezone_offset": now.astimezone().strftime('%z'),
        "formatted": now.strftime('%d/%m/%Y %H:%M:%S')
    }
