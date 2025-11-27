"""
Date parsing utilities with comprehensive format support
"""

from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def parse_date_flexible(date_value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse date from various formats with comprehensive error handling
    
    Supported formats:
    - YYYY-MM-DD (HTML date input): "2023-01-15"
    - DD/MM/YYYY (European/AI format): "15/01/2023"
    - MM/DD/YYYY (US format): "01/15/2023"
    - ISO 8601 with time: "2023-01-15T10:30:00Z"
    - ISO 8601 without Z: "2023-01-15T10:30:00"
    
    Args:
        date_value: Date in various formats
        
    Returns:
        datetime object with UTC timezone or None if parsing fails
        
    Examples:
        >>> parse_date_flexible("2023-01-15")
        datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)
        
        >>> parse_date_flexible("15/01/2023")
        datetime(2023, 1, 15, 0, 0, tzinfo=timezone.utc)
        
        >>> parse_date_flexible("2023-01-15T10:30:00Z")
        datetime(2023, 1, 15, 10, 30, tzinfo=timezone.utc)
    """
    if not date_value:
        return None
    
    # Already a datetime object
    if isinstance(date_value, datetime):
        if date_value.tzinfo is None:
            return date_value.replace(tzinfo=timezone.utc)
        return date_value
    
    # Not a string - cannot parse
    if not isinstance(date_value, str):
        logger.warning(f"⚠️ Invalid date type: {type(date_value)}")
        return None
    
    date_str = date_value.strip()
    
    if not date_str:
        return None
    
    try:
        # ISO format with time and timezone
        if 'T' in date_str:
            logger.debug(f"Parsing ISO format: {date_str}")
            
            if date_str.endswith('Z'):
                # Replace Z with +00:00 for proper parsing
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                parsed = datetime.fromisoformat(date_str)
                # Ensure UTC timezone
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
        
        # Date with slashes (DD/MM/YYYY or MM/DD/YYYY)
        if '/' in date_str:
            logger.debug(f"Parsing slash format: {date_str}")
            
            parts = date_str.split('/')
            if len(parts) != 3:
                raise ValueError(f"Invalid date format: {date_str}")
            
            # Try DD/MM/YYYY first (more common internationally)
            try:
                parsed = datetime.strptime(date_str, '%d/%m/%Y')
                logger.debug(f"✅ Parsed as DD/MM/YYYY: {parsed}")
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                # Fallback to MM/DD/YYYY (US format)
                try:
                    parsed = datetime.strptime(date_str, '%m/%d/%Y')
                    logger.debug(f"✅ Parsed as MM/DD/YYYY: {parsed}")
                    return parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    raise ValueError(f"Could not parse date with slashes: {date_str}")
        
        # Standard YYYY-MM-DD format (HTML date input)
        logger.debug(f"Parsing YYYY-MM-DD format: {date_str}")
        parsed = datetime.strptime(date_str, '%Y-%m-%d')
        logger.debug(f"✅ Parsed as YYYY-MM-DD: {parsed}")
        return parsed.replace(tzinfo=timezone.utc)
        
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Failed to parse date '{date_str}': {e}")
        return None


def convert_dates_in_dict(data: dict, date_fields: list) -> dict:
    """
    Convert all date fields in a dictionary to datetime objects
    
    Args:
        data: Dictionary containing date fields
        date_fields: List of field names that contain dates
        
    Returns:
        Modified dictionary with converted dates
    """
    for field in date_fields:
        if field in data and data[field]:
            parsed_date = parse_date_flexible(data[field])
            if parsed_date is None and data[field]:
                logger.warning(f"⚠️ Could not parse {field}: '{data[field]}' - setting to None")
            data[field] = parsed_date
    
    return data


# Common date field names
CREW_DATE_FIELDS = [
    'date_of_birth',
    'date_sign_on',
    'date_sign_off',
    'passport_issue_date',
    'passport_expiry_date'
]
