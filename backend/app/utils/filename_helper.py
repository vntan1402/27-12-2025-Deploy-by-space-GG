"""
Filename generation utilities for audit certificates
"""
import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

def generate_audit_certificate_filename(
    ship_name: Optional[str],
    cert_type: Optional[str],
    cert_abbreviation: Optional[str],
    issue_date: Optional[str],
    original_filename: str
) -> str:
    """
    Generate filename with pattern:
    {Shipname}_{CertType}_{CertAbbreviation}_{IssueDate_DDMMYYYY}.{ext}
    
    Example: VINASHIP_FullTerm_ISM-DOC_07052024.pdf
    
    Args:
        ship_name: Ship name (from extracted_ship_name or ship DB)
        cert_type: Certificate type (Full Term, Interim, etc.)
        cert_abbreviation: Certificate abbreviation (ISM-DOC, ISPS, etc.)
        issue_date: Issue date (various formats supported)
        original_filename: Original filename (to extract extension)
        
    Returns:
        str: Generated filename
    """
    try:
        # Extract file extension
        file_ext = original_filename.split('.')[-1] if '.' in original_filename else 'pdf'
        file_ext = file_ext.lower()
        
        # 1. Clean ship name (KEEP SPACES like Class & Flag Certificate)
        ship_name_clean = _clean_filename_component(ship_name or "Unknown", keep_spaces=True)
        
        # 2. Clean cert type (KEEP SPACES like Class & Flag Certificate)
        cert_type_clean = _clean_filename_component(cert_type or "Unknown", keep_spaces=True)
        
        # 3. Clean cert abbreviation (KEEP SPACES)
        cert_abbr_clean = _clean_filename_component(cert_abbreviation or "CERT", keep_spaces=True)
        
        # 4. Format issue date to DDMMYYYY
        date_str = _format_date_to_ddmmyyyy(issue_date)
        
        # 5. Combine components
        filename_parts = [
            ship_name_clean,
            cert_type_clean,
            cert_abbr_clean,
            date_str
        ]
        
        filename_base = "_".join(filename_parts)
        
        # 6. Smart truncate if too long (max 150 chars before extension)
        max_length = 150
        if len(filename_base) > max_length:
            logger.warning(f"Filename too long ({len(filename_base)} chars), truncating ship name")
            # Truncate ship name only to preserve important parts (cert type, abbr, date)
            other_parts_length = len(cert_type_clean) + len(cert_abbr_clean) + len(date_str) + 3  # 3 underscores
            available_for_ship = max_length - other_parts_length
            if available_for_ship > 20:  # Keep at least 20 chars for ship name
                ship_name_clean = ship_name_clean[:available_for_ship]
            filename_base = "_".join([ship_name_clean, cert_type_clean, cert_abbr_clean, date_str])
        
        # 7. Add extension
        new_filename = f"{filename_base}.{file_ext}"
        
        logger.info(f"Generated filename: {new_filename}")
        return new_filename
        
    except Exception as e:
        logger.error(f"Error generating filename: {e}")
        # Fallback to timestamp-based name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"audit_cert_{timestamp}.{file_ext}"


def _clean_filename_component(text: str, keep_spaces: bool = True) -> str:
    """
    Clean text for use in filename (matches Class & Flag Certificate logic)
    
    Rules:
    - Remove special characters except alphanumeric, spaces, underscores, hyphens, dots
    - Keep spaces if keep_spaces=True (default)
    - Normalize multiple spaces to single space
    - Strip leading/trailing spaces/underscores
    """
    if not text:
        return "Unknown"
    
    # Remove special characters but KEEP spaces, underscores, hyphens, dots
    # Only allow: letters, numbers, spaces, underscores, hyphens, and dots
    cleaned = re.sub(r'[^a-zA-Z0-9 ._-]', '', text)
    
    if keep_spaces:
        # Keep spaces, just normalize multiple spaces to single
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
    else:
        # Replace spaces with underscores (legacy behavior)
        cleaned = cleaned.replace(' ', '_')
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
    
    return cleaned if cleaned else "Unknown"


def _format_date_to_ddmmyyyy(date_str: Optional[str]) -> str:
    """
    Format date string to DDMMYYYY
    
    Supports various input formats:
    - ISO: 2024-05-07
    - Text: "15 November 2024"
    - DMY: 07/05/2024
    - MDY: 05/07/2024
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        str: Date in DDMMYYYY format (e.g., "07052024")
    """
    if not date_str or date_str in ['', 'null', 'None', 'N/A']:
        # Use current date as fallback
        return datetime.now().strftime("%d%m%Y")
    
    try:
        # Try various date formats
        date_formats = [
            '%Y-%m-%d',           # 2024-05-07
            '%d/%m/%Y',           # 07/05/2024
            '%m/%d/%Y',           # 05/07/2024
            '%Y-%m-%d %H:%M:%S',  # 2024-05-07 10:30:00
            '%d-%m-%Y',           # 07-05-2024
            '%Y/%m/%d',           # 2024/05/07
            '%d %B %Y',           # 7 May 2024
            '%d %b %Y',           # 7 May 2024
            '%B %d, %Y',          # May 7, 2024
        ]
        
        # Clean input
        date_str_clean = str(date_str).strip()
        
        # Handle "15 November 2024" format
        if re.match(r'^\d{1,2}\s+\w+\s+\d{4}$', date_str_clean):
            for fmt in ['%d %B %Y', '%d %b %Y']:
                try:
                    date_obj = datetime.strptime(date_str_clean, fmt)
                    return date_obj.strftime("%d%m%Y")
                except ValueError:
                    continue
        
        # Try all formats
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str_clean, fmt)
                return date_obj.strftime("%d%m%Y")
            except ValueError:
                continue
        
        # If all fails, try to extract date components with regex
        # Match YYYY-MM-DD or DD-MM-YYYY or DD/MM/YYYY
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str_clean)
        if match:
            year, month, day = match.groups()
            return f"{day}{month}{year}"
        
        match = re.search(r'(\d{2})[/-](\d{2})[/-](\d{4})', date_str_clean)
        if match:
            day, month, year = match.groups()
            return f"{day}{month}{year}"
        
        logger.warning(f"Could not parse date: {date_str}, using current date")
        return datetime.now().strftime("%d%m%Y")
        
    except Exception as e:
        logger.error(f"Date formatting error for '{date_str}': {e}")
        return datetime.now().strftime("%d%m%Y")
