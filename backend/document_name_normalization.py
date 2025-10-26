"""
Document Name Normalization Logic
Standardizes ship drawings, manuals, and document names to consistent formats
"""

from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

# Document name to standardized format mapping
DOCUMENT_NAME_MAPPINGS = {
    # Ship Drawings
    "general arrangement": "General Arrangement (GA)",
    "general arrangement plan": "General Arrangement (GA)",
    "ga plan": "General Arrangement (GA)",
    "ga drawing": "General Arrangement (GA)",
    "general arrangement drawing": "General Arrangement (GA)",
    "g.a. plan": "General Arrangement (GA)",
    "g.a.": "General Arrangement (GA)",
    "ga": "General Arrangement (GA)",
    
    "capacity plan": "Capacity Plan",
    "tank capacity plan": "Capacity Plan",
    "capacity drawing": "Capacity Plan",
    
    "safety plan": "Safety Plan",
    "fire safety plan": "Safety Plan",
    
    "fire control plan": "Fire Control Plan",
    "fire fighting plan": "Fire Control Plan",
    "fire plan": "Fire Control Plan",
    
    "damage control plan": "Damage Control Plan",
    "damage control drawing": "Damage Control Plan",
    
    "shell expansion": "Shell Expansion",
    "shell expansion drawing": "Shell Expansion",
    "shell expansion plan": "Shell Expansion",
    
    "midship section": "Midship Section",
    "midship section drawing": "Midship Section",
    "mid-ship section": "Midship Section",
    
    "lines plan": "Lines Plan",
    "lines drawing": "Lines Plan",
    "body plan": "Lines Plan",
    
    "loading manual": "Loading Manual",
    "cargo loading manual": "Loading Manual",
    
    "stability booklet": "Stability Booklet",
    "stability manual": "Stability Booklet",
    
    # Manuals
    "operation manual": "Operation Manual (OM)",
    "operating manual": "Operation Manual (OM)",
    "operator manual": "Operation Manual (OM)",
    "operators manual": "Operation Manual (OM)",
    "om": "Operation Manual (OM)",
    "o.m.": "Operation Manual (OM)",
    
    "instruction manual": "Instruction Manual (IM)",
    "instructions manual": "Instruction Manual (IM)",
    "im": "Instruction Manual (IM)",
    "i.m.": "Instruction Manual (IM)",
    
    "maintenance manual": "Maintenance Manual (MM)",
    "maintenance instruction": "Maintenance Manual (MM)",
    "mm": "Maintenance Manual (MM)",
    "m.m.": "Maintenance Manual (MM)",
    
    "service manual": "Service Manual (SM)",
    "servicing manual": "Service Manual (SM)",
    "sm": "Service Manual (SM)",
    "s.m.": "Service Manual (SM)",
    
    "technical manual": "Technical Manual (TM)",
    "technical documentation": "Technical Manual (TM)",
    "tm": "Technical Manual (TM)",
    "t.m.": "Technical Manual (TM)",
    
    "installation manual": "Installation Manual",
    "installation guide": "Installation Manual",
    "installation instruction": "Installation Manual",
    
    "user manual": "User Manual",
    "users manual": "User Manual",
    "user guide": "User Manual",
    
    "spare parts catalog": "Spare Parts Catalog",
    "spare parts list": "Spare Parts Catalog",
    "parts catalog": "Spare Parts Catalog",
    "parts list": "Spare Parts Catalog",
    
    # Safety Documents
    "safety data sheet": "Safety Data Sheet (SDS)",
    "material safety data sheet": "Safety Data Sheet (SDS)",
    "msds": "Safety Data Sheet (SDS)",
    "sds": "Safety Data Sheet (SDS)",
    
    "safety manual": "Safety Manual",
    "safety instruction": "Safety Manual",
    
    "emergency procedure": "Emergency Procedure",
    "emergency procedures": "Emergency Procedure",
    "emergency response": "Emergency Procedure",
    
    # Certificates & Approvals
    "type approval": "Type Approval Certificate",
    "type approval certificate": "Type Approval Certificate",
    "certificate of approval": "Certificate of Approval",
    "approval certificate": "Certificate of Approval",
    
    # Engine & Machinery
    "engine manual": "Engine Manual",
    "main engine manual": "Engine Manual",
    
    "pump manual": "Pump Manual",
    "pump operation manual": "Pump Manual",
    
    "compressor manual": "Compressor Manual",
    "air compressor manual": "Compressor Manual",
    
    "generator manual": "Generator Manual",
    "diesel generator manual": "Generator Manual",
    
    "boiler manual": "Boiler Manual",
    "boiler operation manual": "Boiler Manual",
    
    # Navigation & Communication
    "radar manual": "Radar Manual",
    "navigation manual": "Navigation Manual",
    "gps manual": "GPS Manual",
    "ais manual": "AIS Manual",
    "vhf manual": "VHF Manual",
    "radio manual": "Radio Manual",
    
    # HVAC
    "hvac manual": "HVAC Manual",
    "air conditioning manual": "HVAC Manual",
    "ventilation manual": "HVAC Manual",
    
    # Electrical
    "electrical drawing": "Electrical Drawing",
    "electrical diagram": "Electrical Drawing",
    "wiring diagram": "Electrical Drawing",
    "circuit diagram": "Electrical Drawing",
    
    "electrical manual": "Electrical Manual",
    "electrical system manual": "Electrical Manual",
    
    # Piping
    "piping diagram": "Piping Diagram",
    "piping drawing": "Piping Diagram",
    "piping plan": "Piping Diagram",
    "p&id": "Piping Diagram",
    "p and id": "Piping Diagram",
    
    # Other
    "user guide": "User Guide",
    "quick start guide": "Quick Start Guide",
    "troubleshooting guide": "Troubleshooting Guide",
    "commissioning manual": "Commissioning Manual",
    "training manual": "Training Manual",
}


def normalize_document_name(document_name: str) -> str:
    """
    Normalize document name to standard format
    
    Args:
        document_name: Document name (e.g., "G.A. Plan", "Operating Manual", "MSDS")
        
    Returns:
        Standardized document name (e.g., "General Arrangement (GA)", "Operation Manual (OM)", "Safety Data Sheet (SDS)")
    """
    if not document_name:
        return ""
    
    try:
        # Convert to lowercase for matching
        doc_name_lower = document_name.lower().strip()
        
        # Remove special characters for better matching
        doc_name_clean = re.sub(r'[^\w\s]', ' ', doc_name_lower)
        doc_name_clean = ' '.join(doc_name_clean.split())  # Remove extra spaces
        
        # Direct match
        if doc_name_lower in DOCUMENT_NAME_MAPPINGS:
            normalized = DOCUMENT_NAME_MAPPINGS[doc_name_lower]
            logger.info(f"✅ Normalized '{document_name}' → '{normalized}' (direct match)")
            return normalized
        
        # Check with cleaned version
        if doc_name_clean in DOCUMENT_NAME_MAPPINGS:
            normalized = DOCUMENT_NAME_MAPPINGS[doc_name_clean]
            logger.info(f"✅ Normalized '{document_name}' → '{normalized}' (cleaned match)")
            return normalized
        
        # Partial match - check if any known document name is contained
        for doc_pattern, normalized_name in DOCUMENT_NAME_MAPPINGS.items():
            # Check if pattern is in the document name
            if doc_pattern in doc_name_lower or doc_pattern in doc_name_clean:
                logger.info(f"✅ Normalized '{document_name}' → '{normalized_name}' (partial match: {doc_pattern})")
                return normalized_name
        
        # Check if document name contains the pattern (reverse match)
        for doc_pattern, normalized_name in DOCUMENT_NAME_MAPPINGS.items():
            if doc_name_lower in doc_pattern or doc_name_clean in doc_pattern:
                logger.info(f"✅ Normalized '{document_name}' → '{normalized_name}' (reverse match: {doc_pattern})")
                return normalized_name
        
        # No match found - return original but cleaned up
        # Capitalize first letter of each word
        original_capitalized = ' '.join(word.capitalize() for word in document_name.split())
        logger.info(f"ℹ️ No normalization found for '{document_name}', keeping as '{original_capitalized}'")
        return original_capitalized
        
    except Exception as e:
        logger.error(f"❌ Error normalizing document_name '{document_name}': {e}")
        return document_name


def add_custom_document_mapping(pattern: str, normalized_name: str):
    """
    Add a custom document name mapping at runtime
    
    Args:
        pattern: Document name pattern (case-insensitive)
        normalized_name: Standardized format
    """
    DOCUMENT_NAME_MAPPINGS[pattern.lower().strip()] = normalized_name
    logger.info(f"✅ Added custom document mapping: '{pattern}' → '{normalized_name}'")


def get_all_document_mappings() -> dict:
    """
    Get all registered document name mappings
    
    Returns:
        Dictionary of document patterns to normalized names
    """
    return DOCUMENT_NAME_MAPPINGS.copy()


# Category helpers
def get_document_category(document_name: str) -> str:
    """
    Determine the category of a document
    
    Returns:
        "Drawing", "Manual", "Certificate", or "Other"
    """
    normalized = normalize_document_name(document_name)
    normalized_lower = normalized.lower()
    
    if any(word in normalized_lower for word in ['plan', 'drawing', 'diagram', 'expansion', 'section']):
        return "Drawing"
    elif any(word in normalized_lower for word in ['manual', 'guide', 'instruction', 'procedure']):
        return "Manual"
    elif any(word in normalized_lower for word in ['certificate', 'approval', 'sds', 'msds']):
        return "Certificate"
    else:
        return "Other"
