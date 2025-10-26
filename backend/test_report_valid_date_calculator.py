"""
Test Report Valid Date Calculator
Based on IMO MSC.1/Circ.1432 and SOLAS requirements for LSA/FFA maintenance intervals
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import re
import logging

logger = logging.getLogger(__name__)

# Equipment maintenance intervals based on IMO MSC.1/Circ.1432 and SOLAS
EQUIPMENT_INTERVALS = {
    # Lifesaving Equipment - Annual service
    "life raft": {"months": 12, "description": "Annual service (can extend to 17 months)"},
    "liferaft": {"months": 12, "description": "Annual service"},
    "life jacket": {"months": 12, "description": "Annual inspection"},
    "lifejacket": {"months": 12, "description": "Annual inspection"},
    "life vest": {"months": 12, "description": "Annual inspection"},
    "immersion suit": {"months": 12, "description": "Annual service"},
    "survival suit": {"months": 12, "description": "Annual service"},
    "epirb": {"months": 12, "description": "Annual service"},
    "sart": {"months": 12, "description": "Annual service"},
    "hru": {"months": 12, "description": "Annual inspection"},
    "hydrostatic release": {"months": 12, "description": "Annual inspection"},
    
    # Lifeboats - Annual with 5-year major overhaul
    "lifeboat": {"months": 12, "description": "Annual inspection (5-year overhaul required)"},
    "rescue boat": {"months": 12, "description": "Annual inspection (5-year overhaul required)"},
    "davit": {"months": 12, "description": "Annual survey (5-year thorough examination)"},
    "launching appliance": {"months": 12, "description": "Annual survey (5-year thorough examination)"},
    
    # Breathing Apparatus - Annual service
    "eebd": {"months": 12, "description": "Annual maintenance"},
    "emergency escape breathing device": {"months": 12, "description": "Annual maintenance"},
    "scba": {"months": 12, "description": "Annual maintenance"},
    "self contained breathing apparatus": {"months": 12, "description": "Annual maintenance"},
    "breathing apparatus": {"months": 12, "description": "Annual maintenance"},
    "fireman outfit": {"months": 12, "description": "Annual inspection"},
    "fireman's outfit": {"months": 12, "description": "Annual inspection"},
    
    # Fire Extinguishers
    "portable fire extinguisher": {"months": 12, "description": "Annual inspection (5-year maintenance, 10-year hydrostatic test)"},
    "fire extinguisher": {"months": 12, "description": "Annual inspection (5-year maintenance)"},
    "wheeled fire extinguisher": {"months": 60, "description": "5-year maintenance (10-year hydrostatic test)"},
    
    # Fire Fighting Equipment
    "portable foam applicator": {"months": 12, "description": "Annual comprehensive inspection"},
    "foam applicator": {"months": 12, "description": "Annual comprehensive inspection"},
    "fire hose": {"months": 12, "description": "Annual inspection"},
    "fire fighting hose": {"months": 12, "description": "Annual inspection"},
    
    # Fixed Systems - Annual inspection
    "co2 system": {"months": 12, "description": "Annual inspection"},
    "carbon dioxide system": {"months": 12, "description": "Annual inspection"},
    "fire detection system": {"months": 12, "description": "Annual inspection"},
    "fire alarm system": {"months": 12, "description": "Annual inspection"},
    "sprinkler system": {"months": 12, "description": "Annual inspection"},
    "fire pump": {"months": 12, "description": "Annual inspection"},
    "emergency fire pump": {"months": 12, "description": "Annual inspection"},
    "gas detector": {"months": 12, "description": "Annual calibration and service"},
    "gas detection system": {"months": 12, "description": "Annual calibration and service"},
}

def calculate_valid_date(
    test_report_name: str,
    issued_date: str,
    note: str = ""
) -> Optional[str]:
    """
    Calculate valid date based on equipment type and issued date
    
    Args:
        test_report_name: Name of equipment (e.g., "EEBD", "Life Raft")
        issued_date: Date when inspection/maintenance was performed (YYYY-MM-DD)
        note: Additional notes that might contain certificate references
        
    Returns:
        Valid date in YYYY-MM-DD format or None if cannot calculate
    """
    try:
        if not issued_date or not test_report_name:
            return None
        
        # Parse issued date
        try:
            issued_dt = datetime.strptime(issued_date, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid issued_date format: {issued_date}")
            return None
        
        # Normalize equipment name to lowercase for matching
        equipment_key = test_report_name.lower().strip()
        
        # Find matching equipment interval
        interval_data = None
        for key, data in EQUIPMENT_INTERVALS.items():
            if key in equipment_key or equipment_key in key:
                interval_data = data
                logger.info(f"✅ Matched equipment '{test_report_name}' with interval: {data['description']}")
                break
        
        if not interval_data:
            # Default to 12 months for unknown equipment
            logger.warning(f"⚠️ No specific interval found for '{test_report_name}', defaulting to 12 months")
            interval_data = {"months": 12, "description": "Annual service (default)"}
        
        # Calculate valid date
        months_to_add = interval_data["months"]
        valid_dt = issued_dt + timedelta(days=30 * months_to_add)  # Approximate
        
        # Format as YYYY-MM-DD
        valid_date = valid_dt.strftime("%Y-%m-%d")
        
        logger.info(f"📅 Calculated valid date: {valid_date} (Issued: {issued_date} + {months_to_add} months)")
        return valid_date
        
    except Exception as e:
        logger.error(f"❌ Error calculating valid date: {e}")
        return None


def parse_certificate_reference_from_note(note: str) -> Optional[str]:
    """
    Parse note to find certificate references like:
    "The next due date for testing is within 3 months before or after 
     the anniversary date of the cargo ship safety radio certificate"
    
    Returns certificate name if found (e.g., "cargo ship safety radio certificate")
    """
    if not note:
        return None
    
    try:
        # Pattern to match certificate references in notes
        patterns = [
            r"anniversary date of the (.+?)(?:certificate|cert\.?)",
            r"anniversary date of (.+?)(?:\.|$)",
            r"due date.+?(?:of|for) the (.+?)certificate",
            r"certificate.+?(.+?)(?:\(|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, note, re.IGNORECASE)
            if match:
                cert_name = match.group(1).strip()
                # Clean up common words
                cert_name = cert_name.replace(" the ", " ").strip()
                logger.info(f"📋 Found certificate reference in note: '{cert_name}'")
                return cert_name
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error parsing certificate reference: {e}")
        return None


def get_certificate_abbreviations() -> Dict[str, list]:
    """
    Map common certificate names to their abbreviations
    Used to match note references with certificate list
    """
    return {
        "cargo ship safety radio certificate": ["CSSR", "Safety Radio Certificate", "Radio Safety Certificate"],
        "cargo ship safety equipment certificate": ["CSSE", "Safety Equipment Certificate"],
        "cargo ship safety construction certificate": ["CSSC", "Safety Construction Certificate"],
        "cargo ship safety certificate": ["CSS", "Safety Certificate"],
        "international load line certificate": ["ILLC", "Load Line Certificate", "Loadline"],
        "international oil pollution prevention certificate": ["IOPPC", "Oil Pollution Certificate"],
        "passenger ship safety certificate": ["PSSC", "Passenger Safety Certificate"],
    }
