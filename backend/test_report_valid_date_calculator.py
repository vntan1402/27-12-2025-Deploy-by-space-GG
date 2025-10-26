"""
Test Report Valid Date Calculator
Based on IMO MSC.1/Circ.1432 and SOLAS requirements for LSA/FFA maintenance intervals
Always calculates Valid Date from Issued Date + Equipment Interval
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Equipment maintenance intervals based on IMO MSC.1/Circ.1432 and SOLAS
# "next_annual_survey" means the valid date is calculated using Anniversary Date
EQUIPMENT_INTERVALS = {
    # Lifesaving Equipment - Annual service (12 months)
    "life raft": {"type": "months", "value": 12, "description": "Annual service"},
    "liferaft": {"type": "months", "value": 12, "description": "Annual service"},
    "life jacket": {"type": "months", "value": 12, "description": "Annual inspection"},
    "lifejacket": {"type": "months", "value": 12, "description": "Annual inspection"},
    "life vest": {"type": "months", "value": 12, "description": "Annual inspection"},
    
    # Electronic Equipment - Next Annual Survey
    "epirb": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "sart": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "ais": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "ssas": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    
    # Protective Equipment - Annual maintenance (12 months)
    "eebd": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "emergency escape breathing device": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "scba": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "self contained breathing apparatus": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "breathing apparatus": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "chemical suit": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "chemical protective suit": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "immersion suit": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "survival suit": {"type": "months", "value": 12, "description": "Annual maintenance"},
    "fireman outfit": {"type": "months", "value": 12, "description": "Annual inspection"},
    "fireman's outfit": {"type": "months", "value": 12, "description": "Annual inspection"},
    
    # Fire Extinguishers - Annual inspection (12 months)
    "portable fire extinguisher": {"type": "months", "value": 12, "description": "Annual inspection"},
    "fire extinguisher": {"type": "months", "value": 12, "description": "Annual inspection"},
    "wheeled fire extinguisher": {"type": "months", "value": 12, "description": "Annual inspection"},
    
    # Lifeboats - Next Annual Survey
    "lifeboat": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "rescue boat": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "davit": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    "launching appliance": {"type": "next_annual_survey", "description": "Next Annual Survey"},
    
    # Fixed Fire Fighting Systems - Annual inspection (12 months)
    "co2 system": {"type": "months", "value": 12, "description": "Annual inspection"},
    "carbon dioxide system": {"type": "months", "value": 12, "description": "Annual inspection"},
    "fire detection": {"type": "months", "value": 12, "description": "Annual inspection"},
    "fire detection system": {"type": "months", "value": 12, "description": "Annual inspection"},
    "fire alarm system": {"type": "months", "value": 12, "description": "Annual inspection"},
    
    # Gas Detection - Annual calibration (12 months)
    "gas detector": {"type": "months", "value": 12, "description": "Annual calibration"},
    "gas detection system": {"type": "months", "value": 12, "description": "Annual calibration"},
}


def get_certificate_abbreviations() -> Dict[str, list]:
    """
    Map common certificate names to their abbreviations
    Used to match note references with certificate list
    """
    return {
        "cargo ship safety radio certificate": ["CSSR", "cargo ship safety radio", "safety radio certificate", "radio safety certificate", "radio certificate"],
        "cargo ship safety equipment certificate": ["CSSE", "cargo ship safety equipment", "safety equipment certificate", "equipment certificate"],
        "cargo ship safety construction certificate": ["CSSC", "cargo ship safety construction", "safety construction certificate", "construction certificate"],
        "cargo ship safety certificate": ["CSS", "cargo ship safety", "safety certificate"],
        "international load line certificate": ["ILLC", "international load line", "load line certificate", "loadline", "load line"],
        "international oil pollution prevention certificate": ["IOPPC", "international oil pollution", "oil pollution certificate", "ioppc"],
        "passenger ship safety certificate": ["PSSC", "passenger ship safety", "passenger safety certificate"],
        "international ship security certificate": ["ISSC", "international ship security", "ship security certificate", "security certificate"],
        "international energy efficiency certificate": ["IEEC", "international energy efficiency", "energy efficiency certificate", "ieec"],
        "minimum safe manning certificate": ["SMC", "minimum safe manning", "safe manning certificate", "manning certificate"],
    }


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
            r"anniversary date of the (.+?)certificate",  # Most common pattern
            r"anniversary date of (.+?)(?:certificate|cert\.?)",  # With cert abbreviation
            r"anniversary date of (.+?)(?:\.|$|\n)",  # Without "certificate" word
            r"due date.+?(?:of|for) the (.+?)certificate",  # Alternative phrasing
            r"(?:before|after).+?anniversary.+?(?:of|for) the (.+?)certificate",  # Before/after patterns
        ]
        
        for pattern in patterns:
            match = re.search(pattern, note, re.IGNORECASE)
            if match:
                cert_name = match.group(1).strip()
                # Clean up common words
                cert_name = cert_name.replace(" the ", " ").strip()
                # Remove trailing punctuation
                cert_name = cert_name.rstrip(".,;:")
                logger.info(f"📋 Found certificate reference in note: '{cert_name}'")
                return cert_name
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error parsing certificate reference: {e}")
        return None


async def find_matching_certificate(cert_name_from_note: str, ship_id: str, mongo_db: Any) -> Optional[Dict]:
    """
    Find matching certificate in Certificate List based on name from note
    
    Args:
        cert_name_from_note: Certificate name extracted from note
        ship_id: Ship ID to filter certificates
        mongo_db: MongoDB instance
        
    Returns:
        Certificate document with next_survey date or None
    """
    try:
        if not cert_name_from_note or not ship_id:
            return None
        
        logger.info(f"🔍 Searching for certificate matching: '{cert_name_from_note}' for ship_id: {ship_id}")
        
        # Get certificate abbreviation mappings
        cert_abbrevs = get_certificate_abbreviations()
        
        # Normalize the search term
        search_term_normalized = cert_name_from_note.lower().strip()
        
        # Find all certificates for this ship
        certificates = await mongo_db.find("certificates", {
            "ship_id": ship_id
        })
        
        if not certificates:
            logger.warning(f"⚠️ No certificates found for ship_id: {ship_id}")
            return None
        
        logger.info(f"📊 Found {len(certificates)} certificates for ship")
        
        # Try to match certificate name
        for cert in certificates:
            cert_name = (cert.get("cert_name") or "").lower().strip()
            
            if not cert_name:
                continue
            
            # Direct match
            if search_term_normalized in cert_name or cert_name in search_term_normalized:
                if cert.get("next_survey"):
                    logger.info(f"✅ Direct match found: {cert.get('cert_name')} (Next Survey: {cert.get('next_survey')})")
                    return cert
            
            # Check against abbreviation mappings
            for full_name, abbrevs in cert_abbrevs.items():
                if search_term_normalized in full_name or full_name in search_term_normalized:
                    # Check if current cert matches any abbreviation
                    for abbrev in abbrevs:
                        if abbrev.lower() in cert_name or cert_name in abbrev.lower():
                            if cert.get("next_survey"):
                                logger.info(f"✅ Abbreviation match found: {cert.get('cert_name')} via '{abbrev}' (Next Survey: {cert.get('next_survey')})")
                                return cert
        
        logger.warning(f"⚠️ No matching certificate found for: '{cert_name_from_note}'")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error finding matching certificate: {e}")
        return None


async def get_ship_anniversary_date(ship_id: str, mongo_db: Any) -> Optional[datetime]:
    """
    Get ship's anniversary date from Detailed Ship Information
    
    Args:
        ship_id: Ship ID
        mongo_db: MongoDB instance
        
    Returns:
        Anniversary date for next year or None
    """
    try:
        if not ship_id:
            return None
        
        logger.info(f"🔍 Fetching anniversary date for ship_id: {ship_id}")
        
        # Get ship information
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        
        if not ship:
            logger.warning(f"⚠️ Ship not found: {ship_id}")
            return None
        
        # Get anniversary date from ship data
        anniversary_date = ship.get("anniversary_date")
        
        if not anniversary_date:
            logger.warning(f"⚠️ No anniversary date found for ship: {ship.get('name', 'Unknown')}")
            return None
        
        # Handle both dict and object formats
        if isinstance(anniversary_date, dict):
            day = anniversary_date.get("day")
            month = anniversary_date.get("month")
        else:
            day = getattr(anniversary_date, "day", None)
            month = getattr(anniversary_date, "month", None)
        
        if not day or not month:
            logger.warning(f"⚠️ Incomplete anniversary date for ship: day={day}, month={month}")
            return None
        
        # Calculate anniversary date for next year
        current_year = datetime.now().year
        next_year = current_year + 1
        
        try:
            anniversary_dt = datetime(next_year, month, day)
            logger.info(f"✅ Found anniversary date: {anniversary_dt.strftime('%Y-%m-%d')} ({day}/{month})")
            return anniversary_dt
        except ValueError as e:
            logger.error(f"❌ Invalid anniversary date values: day={day}, month={month}: {e}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error getting ship anniversary date: {e}")
        return None


async def calculate_valid_date_with_database(
    test_report_name: str,
    issued_date: str,
    note: str,
    ship_id: str,
    mongo_db: Any
) -> Optional[str]:
    """
    Calculate valid date with database integration for certificate references
    
    LOGIC FLOW:
    1. If Note contains certificate reference (e.g., "cargo ship safety radio certificate"):
       - Query Certificate List for matching certificate
       - Return the next_survey date from that certificate
    2. If no certificate found or no certificate reference:
       - Use IMO equipment intervals based on test_report_name
    3. If IMO calculation fails:
       - Fallback to Ship's anniversary_date + 1 year
    
    Args:
        test_report_name: Name of equipment (e.g., "EEBD", "Life Raft")
        issued_date: Date when inspection/maintenance was performed (YYYY-MM-DD)
        note: Additional notes that might contain certificate references
        ship_id: Ship ID for database queries
        mongo_db: MongoDB instance
        
    Returns:
        Valid date in YYYY-MM-DD format or None if cannot calculate
    """
    try:
        logger.info(f"🧮 Calculating Valid Date for: {test_report_name}")
        logger.info(f"   📅 Issued Date: {issued_date}")
        logger.info(f"   📝 Note: {note[:100]}..." if note and len(note) > 100 else f"   📝 Note: {note}")
        
        # STEP 1: Check if note contains certificate reference
        if note:
            cert_name_from_note = parse_certificate_reference_from_note(note)
            
            if cert_name_from_note:
                logger.info(f"🎯 Certificate reference found: '{cert_name_from_note}'")
                
                # Query Certificate List for matching certificate
                matching_cert = await find_matching_certificate(cert_name_from_note, ship_id, mongo_db)
                
                if matching_cert and matching_cert.get("next_survey"):
                    next_survey_date = matching_cert["next_survey"]
                    
                    # Convert to string if datetime object
                    if isinstance(next_survey_date, datetime):
                        valid_date_str = next_survey_date.strftime("%Y-%m-%d")
                    else:
                        valid_date_str = next_survey_date
                    
                    logger.info(f"✅ Valid Date from Certificate '{matching_cert.get('cert_name')}': {valid_date_str}")
                    return valid_date_str
                else:
                    logger.warning(f"⚠️ Certificate '{cert_name_from_note}' not found or has no Next Survey date")
        
        # STEP 2: Use IMO equipment intervals
        if issued_date and test_report_name:
            logger.info(f"🔧 Using IMO equipment interval calculation...")
            
            try:
                issued_dt = datetime.strptime(issued_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"Invalid issued_date format: {issued_date}")
                issued_dt = None
            
            if issued_dt:
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
                
                logger.info(f"✅ Calculated valid date from IMO intervals: {valid_date} (Issued: {issued_date} + {months_to_add} months)")
                return valid_date
        
        # STEP 3: Fallback to Ship's anniversary date + 1 year
        logger.info(f"🔄 Falling back to Ship anniversary date...")
        anniversary_dt = await get_ship_anniversary_date(ship_id, mongo_db)
        
        if anniversary_dt:
            valid_date_str = anniversary_dt.strftime("%Y-%m-%d")
            logger.info(f"✅ Valid Date from Ship anniversary date: {valid_date_str}")
            return valid_date_str
        
        # All methods failed
        logger.warning(f"⚠️ Unable to calculate Valid Date - all methods failed")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error calculating valid date with database: {e}")
        return None
