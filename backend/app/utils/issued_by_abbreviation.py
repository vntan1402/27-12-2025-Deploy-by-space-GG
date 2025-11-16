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
    
    # Panama Companies
    "panama maritime documentation services": "PMDS",
    "panama maritime documentation services inc": "PMDS",
    "pmds": "PMDS",
    
    # Panama Recognized Organizations (RO)
    "cr classification society": "CRCLASS",
    "croatian register of shipping": "CRS",
    "dromon bureau of shipping": "DBS",
    "dromon bureau of shipping limited": "DBS",
    "emirates classification society": "TASNEEF",
    "tasneef": "TASNEEF",
    "intermaritime certification services": "ICS",
    "intermaritime certification services sa": "ICS",
    "international maritime register": "IMR",
    "international maritime register panama": "IMR",
    "international naval surveys bureau": "INSB",
    "insb class": "INSB",
    "international register of shipping": "IRSCLASS",
    "international register of shipping panama": "IRSCLASS",
    "isthmus bureau of shipping": "IBS",
    "macosnar corporation": "MACOSNAR",
    "national shipping adjuster": "NSA",
    "national shipping adjuster inc": "NSA",
    "new united international marine services": "NUIMS",
    "new united marine services": "NUIMS",
    "overseas marine certification services": "OMCS",
    "overseas marine certification services inc": "OMCS",
    "omcs": "OMCS",
    "panama classification bureau": "PCB",
    "panama classification bureau inc": "PCB",
    "panama shipping registrar": "PSR",
    "panama shipping registrar inc": "PSR",
    "phoenix register of shipping": "PHOENIX",
    "phoenix register of shipping sa": "PHOENIX",
    "polski rejestr statkow": "PRS",
    "polski rejestr": "PRS",
    "prs": "PRS",
    "qualitas register of shipping": "QUALITAS",
    "qualitas register of shipping sa": "QUALITAS",
    "rs classification services": "RSCLASS",
    "rina services": "RINA",
    "rina": "RINA",
    "turk loydu": "TURKLOYDU",
    "türk loydu": "TURKLOYDU",
}


def generate_organization_abbreviation(org_name: str) -> str:
    """
    Generate organization abbreviation for display purposes
    This is different from normalize_issued_by which standardizes the stored value.
    
    Args:
        org_name: Organization name (can be full name or abbreviation)
        
    Returns:
        Display abbreviation (e.g., "PMDS", "DNV", "LR")
        
    Examples:
        "Panama Maritime Documentation Services" → "PMDS"
        "DNV" → "DNV" (already abbreviated)
        "American Bureau of Shipping" → "ABS"
        "NK" → "NK" (already abbreviated, 2 letters)
    """
    if not org_name:
        return ""
    
    # Clean and normalize
    org_name_stripped = org_name.strip()
    org_name_upper = org_name_stripped.upper()
    org_name_lower = org_name_stripped.lower()
    
    # PRIORITY 1: Check if already in mapping (handles "nk" → "NK", "dnv" → "DNV", etc.)
    if org_name_lower in COMPANY_ABBREVIATIONS:
        abbreviation = COMPANY_ABBREVIATIONS[org_name_lower]
        logger.debug(f"✅ Found in mapping: '{org_name_stripped}' → '{abbreviation}'")
        return abbreviation
    
    # PRIORITY 2: Check if value is already an abbreviation (2-8 uppercase letters)
    # This handles user input like "NK", "DNV", "ABS", "PMDS" that aren't in lowercase mapping
    if re.match(r'^[A-Z]{2,8}$', org_name_stripped):
        logger.debug(f"✅ Detected manual abbreviation: '{org_name_stripped}'")
        return org_name_stripped
    
    # Exact mappings for well-known maritime organizations
    exact_mappings = {
        # Panama Maritime Organizations
        'PANAMA MARITIME DOCUMENTATION SERVICES': 'PMDS',
        'PANAMA MARITIME DOCUMENTATION SERVICES INC': 'PMDS',
        'PANAMA MARITIME AUTHORITY': 'PMA',
        
        # Major Classification Societies (IACS Members)
        'DET NORSKE VERITAS': 'DNV',
        'DNV GL': 'DNV',
        'AMERICAN BUREAU OF SHIPPING': 'ABS',
        "LLOYD'S REGISTER": 'LR',
        'LLOYDS REGISTER': 'LR',
        "LLOYD'S REGISTER OF SHIPPING": 'LR',
        'BUREAU VERITAS': 'BV',
        'CHINA CLASSIFICATION SOCIETY': 'CCS',
        'NIPPON KAIJI KYOKAI': 'ClassNK',
        'CLASS NK': 'ClassNK',
        'KOREAN REGISTER OF SHIPPING': 'KR',
        'REGISTRO ITALIANO NAVALE': 'RINA',
        'RUSSIAN MARITIME REGISTER OF SHIPPING': 'RS',
        'CROATIAN REGISTER OF SHIPPING': 'CRS',
        'POLISH REGISTER OF SHIPPING': 'PRS',
        'TURKISH LLOYD': 'TL',
        'INDIAN REGISTER OF SHIPPING': 'IRClass',
        
        # Other Flag State Authorities
        'LIBERIA MARITIME AUTHORITY': 'LISCR',
        'MARSHALL ISLANDS MARITIME AUTHORITY': 'MIMA',
        'SINGAPORE MARITIME AND PORT AUTHORITY': 'MPA',
        'MALAYSIA MARINE DEPARTMENT': 'MMD',
        'HONG KONG MARINE DEPARTMENT': 'MARDEP',
        
        # Government Maritime Administrations
        'MARITIME SAFETY ADMINISTRATION': 'MSA',
        'COAST GUARD': 'CG',
        'PORT STATE CONTROL': 'PSC',
        'INTERNATIONAL MARITIME ORGANIZATION': 'IMO',
    }
    
    # Check for exact matches first
    for full_name, abbreviation in exact_mappings.items():
        if full_name in org_name_upper:
            return abbreviation
    
    # Pattern-based matching for common variations
    if 'PANAMA MARITIME' in org_name_upper and 'DOCUMENTATION' in org_name_upper:
        return 'PMDS'
    elif 'PANAMA MARITIME' in org_name_upper and 'AUTHORITY' in org_name_upper:
        return 'PMA'
    elif 'DNV' in org_name_upper and ('GL' in org_name_upper or 'VERITAS' in org_name_upper):
        return 'DNV'
    elif 'AMERICAN BUREAU' in org_name_upper and 'SHIPPING' in org_name_upper:
        return 'ABS'
    elif 'LLOYD' in org_name_upper and 'REGISTER' in org_name_upper:
        return 'LR'
    elif 'BUREAU VERITAS' in org_name_upper:
        return 'BV'
    elif 'CHINA CLASSIFICATION' in org_name_upper:
        return 'CCS'
    elif 'NIPPON KAIJI' in org_name_upper or 'CLASS NK' in org_name_upper:
        return 'ClassNK'
    elif 'KOREAN REGISTER' in org_name_upper:
        return 'KR'
    elif 'RINA' in org_name_upper and ('ITALIANO' in org_name_upper or 'NAVALE' in org_name_upper):
        return 'RINA'
    elif 'RUSSIAN MARITIME' in org_name_upper or 'RMRS' in org_name_upper:
        return 'RS'
    elif 'LIBERIA' in org_name_upper and 'MARITIME' in org_name_upper:
        return 'LISCR'
    elif 'MARSHALL ISLANDS' in org_name_upper:
        return 'MIMA'
    
    # Fallback: Generate abbreviation from significant words
    common_org_words = {
        'the', 'of', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were',
        'inc', 'ltd', 'llc', 'corp', 'corporation', 'company', 'co', 'limited', 'services',
        'international', 'group', 'holdings', 'management', 'administration', 'department'
    }
    
    # Clean the name and split into words
    words = re.findall(r'\b[A-Za-z]+\b', org_name_upper)
    
    # Filter out common words but keep important maritime terms
    significant_words = []
    for word in words:
        word_lower = word.lower()
        if word_lower not in common_org_words:
            significant_words.append(word)
        elif word_lower in ['authority', 'maritime', 'classification', 'society', 'register', 'bureau', 'class']:
            # Keep important maritime organization words
            significant_words.append(word)
    
    # Handle special cases for empty result
    if not significant_words:
        significant_words = words[:3]  # Take first 3 words as fallback
    
    # Generate abbreviation by taking first letter of each significant word
    abbreviation = ''.join([word[0] for word in significant_words[:4]])  # Max 4 letters for organizations
    
    return abbreviation if abbreviation else org_name[:4].upper()


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
            logger.debug(f"✅ Normalized '{issued_by}' → '{abbreviation}' (direct match)")
            return abbreviation
        
        # Check with cleaned version
        if issued_by_clean in COMPANY_ABBREVIATIONS:
            abbreviation = COMPANY_ABBREVIATIONS[issued_by_clean]
            logger.debug(f"✅ Normalized '{issued_by}' → '{abbreviation}' (cleaned match)")
            return abbreviation
        
        # Partial match - check if any known company name is contained
        for company_name, abbreviation in COMPANY_ABBREVIATIONS.items():
            if company_name in issued_by_lower or issued_by_lower in company_name:
                logger.debug(f"✅ Normalized '{issued_by}' → '{abbreviation}' (partial match: {company_name})")
                return abbreviation
        
        # No match found - return original but cleaned up
        # Capitalize first letter of each word
        original_capitalized = ' '.join(word.capitalize() for word in issued_by.split())
        logger.debug(f"ℹ️ No abbreviation found for '{issued_by}', keeping as '{original_capitalized}'")
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
