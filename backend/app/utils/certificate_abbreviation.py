"""
Certificate Abbreviation Generation Utilities
Generates abbreviations for certificate names with user-defined mapping support
"""
import re
import logging
from typing import Optional
from app.db.mongodb import mongo_db

logger = logging.getLogger(__name__)


async def get_user_defined_abbreviation(cert_name: str) -> Optional[str]:
    """Get user-defined certificate abbreviation from database mappings"""
    try:
        if not cert_name:
            return None
        
        # Normalize certificate name for lookup (uppercase, stripped)
        normalized_name = cert_name.upper().strip()
        
        # Look for existing mapping
        mapping = await mongo_db.find_one("certificate_abbreviation_mappings", 
                                        {"cert_name": normalized_name})
        
        if mapping:
            # Increment usage count
            await mongo_db.update("certificate_abbreviation_mappings", 
                                {"id": mapping["id"]}, 
                                {"usage_count": mapping.get("usage_count", 0) + 1})
            return mapping.get("abbreviation")
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting user-defined abbreviation: {e}")
        return None


def validate_certificate_type(cert_type: str) -> str:
    """
    Validate and normalize certificate type to one of the 6 allowed types
    Migrated from backend-v1
    """
    if not cert_type:
        return "Full Term"
    
    # Allowed certificate types (case insensitive)
    allowed_types = {
        "full term": "Full Term",
        "interim": "Interim", 
        "provisional": "Provisional",
        "short term": "Short term",
        "conditional": "Conditional",
        "other": "Other"
    }
    
    # Normalize input
    normalized = cert_type.lower().strip()
    
    # Direct match
    if normalized in allowed_types:
        return allowed_types[normalized]
    
    # Partial match for common variations
    if "full" in normalized or "term" in normalized:
        return "Full Term"
    elif "interim" in normalized or "temporary" in normalized:
        return "Interim"
    elif "provisional" in normalized:
        return "Provisional"  
    elif "short" in normalized:
        return "Short term"
    elif "conditional" in normalized:
        return "Conditional"
    else:
        return "Other"

def generate_doc_abbreviation(doc_type: Optional[str], cert_name: str) -> str:
    """
    Generate DOC abbreviation based on doc_type field
    
    Args:
        doc_type: DOC classification (full_term, short_term, interim)
        cert_name: Certificate name (fallback if doc_type not provided)
        
    Returns:
        DOC abbreviation (FT DOC, ST DOC, Int DOC, or DOC)
    """
    # Check if this is a DOC certificate
    cert_name_upper = cert_name.upper().strip() if cert_name else ""
    if 'DOCUMENT OF COMPLIANCE' not in cert_name_upper and cert_name_upper != 'DOC':
        return ""  # Not a DOC certificate
    
    # Use doc_type if provided (from AI extraction)
    if doc_type:
        doc_type_lower = doc_type.lower().strip()
        if doc_type_lower == "full_term":
            logger.info(f"✅ DOC type from AI: '{doc_type}' → 'FT DOC'")
            return "FT DOC"
        elif doc_type_lower == "short_term":
            logger.info(f"✅ DOC type from AI: '{doc_type}' → 'ST DOC'")
            return "ST DOC"
        elif doc_type_lower == "interim":
            logger.info(f"✅ DOC type from AI: '{doc_type}' → 'Int DOC'")
            return "Int DOC"
    
    # Fallback: analyze cert_name if doc_type not provided
    if 'FULL' in cert_name_upper or 'FULL TERM' in cert_name_upper:
        logger.info(f"✅ DOC type from name: '{cert_name}' → 'FT DOC'")
        return "FT DOC"
    elif 'SHORT' in cert_name_upper or 'SHORT TERM' in cert_name_upper:
        logger.info(f"✅ DOC type from name: '{cert_name}' → 'ST DOC'")
        return "ST DOC"
    elif 'INTERIM' in cert_name_upper or 'INTERRIM' in cert_name_upper:
        logger.info(f"✅ DOC type from name: '{cert_name}' → 'Int DOC'")
        return "Int DOC"
    else:
        # Default DOC if no specific type found
        logger.info(f"✅ DOC detected (no type specified): '{cert_name}' → 'DOC'")
        return "DOC"


async def generate_certificate_abbreviation(cert_name: str, doc_type: Optional[str] = None) -> str:
    """
    Generate certificate abbreviation from certificate name
    Priority: User-defined mappings → Special DOC handling → Auto-generation algorithm
    
    Args:
        cert_name: Full certificate name
        
    Returns:
        Abbreviated certificate name (e.g., "CSSC", "IOPP", "FT DOC", "ST DOC")
        
    Examples:
        "Cargo Ship Safety Construction Certificate" → "CSSC"
        "International Oil Pollution Prevention" → "IOPP"
        "Load Line Certificate" → "LLC"
        "Full Term Document of Compliance" → "FT DOC"
        "Short Term Document of Compliance" → "ST DOC"
        "Interim Document of Compliance" → "Int DOC"
    """
    if not cert_name:
        return ""
    
    # Priority 1: Check for user-defined mapping first
    user_abbreviation = await get_user_defined_abbreviation(cert_name)
    if user_abbreviation:
        logger.info(f"✅ Using user-defined abbreviation: '{cert_name}' → '{user_abbreviation}'")
        return user_abbreviation
    
    # Priority 2: Special handling for Document of Compliance (DOC)
    doc_abbr = generate_doc_abbreviation(doc_type, cert_name)
    if doc_abbr:
        return doc_abbr
    
    # Priority 3: Auto-generation algorithm
    # Remove common words and focus on key terms
    # Note: Kept 'of' to generate abbreviations like DOC (Document Of Compliance)
    common_words = {'the', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
    
    # Remove common maritime phrases first
    cert_name_cleaned = cert_name.upper()
    
    # Remove "Statement of Compliance" and variations
    phrases_to_remove = [
        'STATEMENT OF COMPLIANCE',
        'STATEMENT OF COMPIANCE',  # Handle typo version
        'SOC',  # Common abbreviation that might appear in full text
    ]
    
    for phrase in phrases_to_remove:
        cert_name_cleaned = cert_name_cleaned.replace(phrase, '')
    
    # Clean up extra spaces
    cert_name_cleaned = ' '.join(cert_name_cleaned.split())
    
    # Extract words using regex
    words = re.findall(r'\b[A-Za-z]+\b', cert_name_cleaned)
    
    # Filter out common words but keep all significant maritime terms
    significant_words = []
    for word in words:
        if word.lower() not in common_words:
            significant_words.append(word)
    
    # Handle special cases for maritime certificates
    if not significant_words:
        significant_words = words  # Fallback to all words
    
    # Generate abbreviation by taking first letter of each significant word
    abbreviation = ''.join([word[0] for word in significant_words[:6]])  # Max 6 letters
    
    # Remove trailing 'C' only if it's from the word "Certificate" (last word)
    if (abbreviation.endswith('C') and len(abbreviation) > 1 and 
        len(significant_words) > 0 and significant_words[-1].upper() == 'CERTIFICATE'):
        abbreviation = abbreviation[:-1]
    
    logger.info(f"✅ Auto-generated abbreviation: '{cert_name}' → '{abbreviation}'")
    return abbreviation


def generate_abbreviation_sync(cert_name: str) -> str:
    """
    Synchronous version for quick abbreviation generation without DB lookup
    Used for initial display before async enhancement
    
    Args:
        cert_name: Full certificate name
        
    Returns:
        Abbreviated certificate name (e.g., "FT DOC", "ST DOC", "Int DOC")
    """
    if not cert_name:
        return ""
    
    # Special handling for Document of Compliance (DOC)
    cert_name_upper = cert_name.upper().strip()
    if 'DOCUMENT OF COMPLIANCE' in cert_name_upper or cert_name_upper == 'DOC':
        # Check for specific DOC types
        if 'FULL' in cert_name_upper or 'FULL TERM' in cert_name_upper:
            return "FT DOC"
        elif 'SHORT' in cert_name_upper or 'SHORT TERM' in cert_name_upper:
            return "ST DOC"
        elif 'INTERIM' in cert_name_upper or 'INTERRIM' in cert_name_upper:
            return "Int DOC"
        else:
            # Default DOC if no specific type found
            return "DOC"
    
    # Remove common words and focus on key terms
    # Note: Kept 'of' to generate abbreviations like DOC (Document Of Compliance)
    common_words = {'the', 'and', 'a', 'an', 'for', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
    
    cert_name_cleaned = cert_name.upper()
    
    # Remove common phrases
    phrases_to_remove = [
        'STATEMENT OF COMPLIANCE',
        'STATEMENT OF COMPIANCE',
        'SOC',
    ]
    
    for phrase in phrases_to_remove:
        cert_name_cleaned = cert_name_cleaned.replace(phrase, '')
    
    cert_name_cleaned = ' '.join(cert_name_cleaned.split())
    
    words = re.findall(r'\b[A-Za-z]+\b', cert_name_cleaned)
    
    significant_words = []
    for word in words:
        if word.lower() not in common_words:
            significant_words.append(word)
    
    if not significant_words:
        significant_words = words
    
    abbreviation = ''.join([word[0] for word in significant_words[:6]])
    
    if (abbreviation.endswith('C') and len(abbreviation) > 1 and 
        len(significant_words) > 0 and significant_words[-1].upper() == 'CERTIFICATE'):
        abbreviation = abbreviation[:-1]
    
    return abbreviation
