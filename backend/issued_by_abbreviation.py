"""
Issued By Abbreviation Logic
Standardizes company names to consistent abbreviations
"""

from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

# Company name to abbreviation mapping
COMPANY_ABBREVIATIONS = {
    # Chau Giang variations
    "chau giang maritime": "CGM",
    "chau giang marine": "CGM",
    "chau giang": "CGM",
    "cgm": "CGM",
    
    # Classification Societies
    "lloyd's register": "LR",
    "lloyds register": "LR",
    "lr": "LR",
    
    "bureau veritas": "BV",
    "bv": "BV",
    
    "det norske veritas": "DNV",
    "dnv gl": "DNV",
    "dnv": "DNV",
    
    "american bureau of shipping": "ABS",
    "abs": "ABS",
    
    "nippon kaiji kyokai": "NK",
    "class nk": "NK",
    "nk": "NK",
    
    "korean register": "KR",
    "kr": "KR",
    
    "china classification society": "CCS",
    "ccs": "CCS",
    
    "russian maritime register of shipping": "RS",
    "rs": "RS",
    
    "indian register of shipping": "IRS",
    "irs": "IRS",
    
    # Common Vietnamese Companies
    "viet tech": "VITECH",
    "vitech": "VITECH",
    
    "vietnam register": "VR",
    "vr": "VR",
    
    # Add more as needed
}


def normalize_issued_by(issued_by: str) -> str:
    """
    Normalize issued_by company name to standard abbreviation
    
    Args:
        issued_by: Company name (e.g., "Chau Giang Maritime", "Lloyd's Register")
        
    Returns:
        Abbreviated company name (e.g., "CGM", "LR")
    """
    if not issued_by:
        return ""
    
    try:
        # Convert to lowercase for matching
        issued_by_lower = issued_by.lower().strip()
        
        # Remove special characters for better matching
        issued_by_clean = re.sub(r'[^\w\s]', '', issued_by_lower)
        
        # Direct match
        if issued_by_lower in COMPANY_ABBREVIATIONS:
            abbreviation = COMPANY_ABBREVIATIONS[issued_by_lower]
            logger.info(f"✅ Normalized '{issued_by}' → '{abbreviation}' (direct match)")
            return abbreviation
        
        # Check with cleaned version
        if issued_by_clean in COMPANY_ABBREVIATIONS:
            abbreviation = COMPANY_ABBREVIATIONS[issued_by_clean]
            logger.info(f"✅ Normalized '{issued_by}' → '{abbreviation}' (cleaned match)")
            return abbreviation
        
        # Partial match - check if any known company name is contained
        for company_name, abbreviation in COMPANY_ABBREVIATIONS.items():
            if company_name in issued_by_lower or issued_by_lower in company_name:
                logger.info(f"✅ Normalized '{issued_by}' → '{abbreviation}' (partial match: {company_name})")
                return abbreviation
        
        # No match found - return original but cleaned up
        # Capitalize first letter of each word
        original_capitalized = ' '.join(word.capitalize() for word in issued_by.split())
        logger.info(f"ℹ️ No abbreviation found for '{issued_by}', keeping as '{original_capitalized}'")
        return original_capitalized
        
    except Exception as e:
        logger.error(f"❌ Error normalizing issued_by '{issued_by}': {e}")
        return issued_by


def add_custom_abbreviation(company_name: str, abbreviation: str):
    """
    Add a custom company abbreviation at runtime
    
    Args:
        company_name: Full company name (case-insensitive)
        abbreviation: Abbreviated form
    """
    COMPANY_ABBREVIATIONS[company_name.lower().strip()] = abbreviation.upper()
    logger.info(f"✅ Added custom abbreviation: '{company_name}' → '{abbreviation}'")


def get_all_abbreviations() -> dict:
    """
    Get all registered company abbreviations
    
    Returns:
        Dictionary of company names to abbreviations
    """
    return COMPANY_ABBREVIATIONS.copy()
