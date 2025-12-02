"""
Utility for normalizing dates for comparison
Handles various date formats and converts them to a standard comparable format
"""
import logging
from datetime import datetime
from typing import Union, Optional

logger = logging.getLogger(__name__)


def normalize_date_for_comparison(date_input: Union[str, datetime]) -> Optional[str]:
    """
    Normalize date to YYYY-MM-DD format for comparison
    
    Args:
        date_input: Can be string in various formats or datetime object
        
    Returns:
        Normalized date string in YYYY-MM-DD format, or None if parsing fails
        
    Supported input formats:
    - ISO format: "2024-01-15", "2024-01-15T00:00:00"
    - DD/MM/YYYY: "15/01/2024"
    - MM/DD/YYYY: "01/15/2024"
    - Datetime object
    """
    if not date_input:
        return None
    
    # If already datetime object
    if isinstance(date_input, datetime):
        return date_input.strftime('%Y-%m-%d')
    
    # If string, try various formats
    if isinstance(date_input, str):
        date_str = date_input.strip()
        
        # Try various date formats
        date_formats = [
            '%Y-%m-%d',           # 2024-01-15
            '%Y/%m/%d',           # 2024/01/15
            '%d/%m/%Y',           # 15/01/2024 (common in Vietnam)
            '%m/%d/%Y',           # 01/15/2024 (US format)
            '%d-%m-%Y',           # 15-01-2024
            '%m-%d-%Y',           # 01-15-2024
            '%Y-%m-%dT%H:%M:%S',  # ISO with time
            '%Y-%m-%d %H:%M:%S',  # SQL datetime
            '%d/%m/%Y %H:%M:%S',  # DD/MM/YYYY with time
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                normalized = parsed_date.strftime('%Y-%m-%d')
                logger.debug(f"✅ Parsed '{date_str}' with format '{fmt}' → {normalized}")
                return normalized
            except ValueError:
                continue
        
        # If all formats fail, log warning
        logger.warning(f"⚠️ Could not parse date: {date_str}")
        return None
    
    logger.warning(f"⚠️ Unsupported date input type: {type(date_input)}")
    return None


def are_dates_equal(date1: Union[str, datetime], date2: Union[str, datetime]) -> bool:
    """
    Compare two dates for equality after normalization
    
    Args:
        date1: First date (string or datetime)
        date2: Second date (string or datetime)
        
    Returns:
        True if dates are equal, False otherwise
    """
    normalized1 = normalize_date_for_comparison(date1)
    normalized2 = normalize_date_for_comparison(date2)
    
    if not normalized1 or not normalized2:
        return False
    
    return normalized1 == normalized2
