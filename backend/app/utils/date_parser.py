"""Date parsing utilities"""
import re
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime object with enhanced error handling"""
    if not date_str or date_str in ['', 'null', 'None', 'N/A']:
        return None
    
    try:
        # Handle various date formats
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%m/%Y',  # Month/Year only (will default to day 1)
            '%b %Y',  # "NOV 2020"
            '%b. %Y', # "NOV. 2020"
            '%B %Y',  # "NOVEMBER 2020"
            '%d %B %Y',  # "28 July 2025"
            '%d %b %Y',  # "9 Aug 2023"
        ]
        
        # Clean the input string
        date_str_clean = str(date_str).strip()
        
        # Handle special cases for "DD MONTH YYYY" formats (most specific first)
        if re.match(r'^\d{1,2}\s+\w+\s+\d{4}$', date_str_clean):
            # "28 July 2025", "9 August 2023", "28 Jul 2025"
            for fmt in ['%d %B %Y', '%d %b %Y']:
                try:
                    parsed_date = datetime.strptime(date_str_clean, fmt)
                    return parsed_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        
        # Handle special cases for month/year formats
        if re.match(r'^\w{3,4}\.?\s+\d{4}$', date_str_clean):
            # "NOV 2020", "NOV. 2020", "DEC 2020" etc
            for fmt in ['%b %Y', '%b. %Y', '%B %Y']:
                try:
                    parsed_date = datetime.strptime(date_str_clean, fmt)
                    return parsed_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str_clean, fmt)
                return parsed_date.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        
        # If no format works, log and return None
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Date parsing error for '{date_str}': {e}")
        return None
