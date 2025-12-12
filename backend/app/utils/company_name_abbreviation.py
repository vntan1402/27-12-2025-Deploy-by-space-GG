"""
Company Name Abbreviation Utility
Abbreviate common company name patterns for display
"""
import logging
import re

logger = logging.getLogger(__name__)


def abbreviate_company_name(company_name: str) -> str:
    """
    Abbreviate company name for display in tables
    
    Rules:
    - "COMPANY LIMITED" → "Co., Ltd"
    - "JOINT STOCK COMPANY" → "JSC"
    - Case insensitive
    - Preserves original name in database
    
    Args:
        company_name: Full company name
        
    Returns:
        Abbreviated company name for display
        
    Examples:
        "HAI AN CONTAINER TRANSPORT COMPANY LIMITED" 
        → "HAI AN CONTAINER TRANSPORT Co., Ltd"
        
        "ANH DUONG PRODUCTION TRADING GROUP JOINT STOCK COMPANY"
        → "ANH DUONG PRODUCTION TRADING GROUP JSC"
    """
    if not company_name:
        return ""
    
    abbreviated = company_name
    
    # Rule 1: COMPANY LIMITED → Co., Ltd
    # Match: "COMPANY LIMITED" (case insensitive, at end of string preferred)
    abbreviated = re.sub(
        r'\bCOMPANY\s+LIMITED\b',
        'Co., Ltd',
        abbreviated,
        flags=re.IGNORECASE
    )
    
    # Rule 2: JOINT STOCK COMPANY → JSC
    # Match: "JOINT STOCK COMPANY" (case insensitive)
    abbreviated = re.sub(
        r'\bJOINT\s+STOCK\s+COMPANY\b',
        'JSC',
        abbreviated,
        flags=re.IGNORECASE
    )
    
    # Log if abbreviation occurred
    if abbreviated != company_name:
        logger.debug(f"📝 Company name abbreviated: '{company_name}' → '{abbreviated}'")
    
    return abbreviated
