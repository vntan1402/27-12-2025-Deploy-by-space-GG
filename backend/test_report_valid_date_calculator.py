"""
Test Report Valid Date Calculator
Based on IMO MSC.1/Circ.1432 and SOLAS requirements for LSA/FFA maintenance intervals
Always calculates Valid Date from Issued Date + Equipment Interval
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import calendar

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


async def get_ship_anniversary_and_special_survey(ship_id: str, mongo_db: Any) -> Optional[Dict]:
    """
    Get ship's anniversary date and special survey cycle to date
    
    Args:
        ship_id: Ship ID
        mongo_db: MongoDB instance
        
    Returns:
        Dict with anniversary_date and special_survey_cycle_to or None
    """
    try:
        if not ship_id:
            return None
        
        logger.info(f"🔍 Fetching anniversary date and special survey for ship_id: {ship_id}")
        
        # Get ship information
        ship = await mongo_db.find_one("ships", {"id": ship_id})
        
        if not ship:
            logger.warning(f"⚠️ Ship not found: {ship_id}")
            return None
        
        # Get anniversary date from ship data
        anniversary_date = ship.get("anniversary_date")
        special_survey_cycle = ship.get("special_survey_cycle")
        
        if not anniversary_date:
            logger.warning(f"⚠️ No anniversary date found for ship: {ship.get('name', 'Unknown')}")
            return None
        
        # Handle both dict and object formats for anniversary_date
        if isinstance(anniversary_date, dict):
            day = anniversary_date.get("day")
            month = anniversary_date.get("month")
        else:
            day = getattr(anniversary_date, "day", None)
            month = getattr(anniversary_date, "month", None)
        
        if not day or not month:
            logger.warning(f"⚠️ Incomplete anniversary date for ship: day={day}, month={month}")
            return None
        
        # Get special_survey_cycle to_date
        special_survey_cycle_to = None
        if special_survey_cycle:
            if isinstance(special_survey_cycle, dict):
                special_survey_cycle_to = special_survey_cycle.get("to_date")
            else:
                special_survey_cycle_to = getattr(special_survey_cycle, "to_date", None)
        
        result = {
            "anniversary_day": day,
            "anniversary_month": month,
            "special_survey_cycle_to": special_survey_cycle_to
        }
        
        logger.info(f"✅ Found ship data: Anniversary={day}/{month}, Special Survey Cycle To={special_survey_cycle_to}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting ship anniversary and special survey: {e}")
        return None


async def calculate_next_annual_survey_date(ship_id: str, issued_date: str, mongo_db: Any) -> Optional[str]:
    """
    Calculate Next Annual Survey date based on Anniversary Date and Special Survey Cycle
    
    Logic:
    1. Get Anniversary Date (day/month) and Special Survey Cycle to (full date) from ship info
    2. Calculate Anniversary Date for next year (using year from issued_date + 1)
    3. If Anniversary Date (next year) == Special Survey Cycle to → Valid Date = Anniversary - 3 months
    4. If Anniversary Date (next year) != Special Survey Cycle to → Valid Date = Anniversary + 3 months
    
    Args:
        ship_id: Ship ID
        issued_date: Issued date in YYYY-MM-DD format
        mongo_db: MongoDB instance
        
    Returns:
        Valid date in YYYY-MM-DD format or None
    """
    try:
        ship_data = await get_ship_anniversary_and_special_survey(ship_id, mongo_db)
        
        if not ship_data:
            logger.warning("⚠️ Could not get ship anniversary data")
            return None
        
        day = ship_data["anniversary_day"]
        month = ship_data["anniversary_month"]
        special_survey_cycle_to = ship_data["special_survey_cycle_to"]
        
        # Parse issued_date to get the year
        try:
            issued_dt = datetime.strptime(issued_date, "%Y-%m-%d")
            issued_year = issued_dt.year
        except ValueError:
            logger.error(f"❌ Invalid issued_date format: {issued_date}")
            return None
        
        # Calculate anniversary date for next year (issued year + 1)
        next_year = issued_year + 1
        
        try:
            anniversary_next_year = datetime(next_year, month, day)
        except ValueError as e:
            logger.error(f"❌ Invalid anniversary date values: day={day}, month={month}: {e}")
            return None
        
        logger.info(f"📅 Issued Date Year: {issued_year}, Next Year: {next_year}")
        logger.info(f"📅 Anniversary Date (issued year + 1): {anniversary_next_year.strftime('%Y-%m-%d')}")
        
        # Parse special_survey_cycle_to if it exists
        if special_survey_cycle_to:
            try:
                # Handle different date formats
                if isinstance(special_survey_cycle_to, str):
                    # Try parsing YYYY-MM-DD format
                    special_survey_dt = datetime.strptime(special_survey_cycle_to, "%Y-%m-%d")
                elif isinstance(special_survey_cycle_to, datetime):
                    special_survey_dt = special_survey_cycle_to
                else:
                    logger.warning(f"⚠️ Unknown format for special_survey_cycle_to: {type(special_survey_cycle_to)}")
                    special_survey_dt = None
                
                if special_survey_dt:
                    logger.info(f"📅 Special Survey Cycle To: {special_survey_dt.strftime('%Y-%m-%d')}")
                    
                    # Compare dates (only compare date part, not time)
                    if (anniversary_next_year.year == special_survey_dt.year and 
                        anniversary_next_year.month == special_survey_dt.month and 
                        anniversary_next_year.day == special_survey_dt.day):
                        # Anniversary Date == Special Survey Cycle to → Subtract 3 months
                        valid_date = anniversary_next_year - timedelta(days=90)  # Approximately 3 months
                        logger.info(f"🎯 Anniversary matches Special Survey Cycle → Valid Date = Anniversary - 3M")
                    else:
                        # Anniversary Date != Special Survey Cycle to → Add 3 months
                        valid_date = anniversary_next_year + timedelta(days=90)  # Approximately 3 months
                        logger.info(f"🎯 Anniversary differs from Special Survey Cycle → Valid Date = Anniversary + 3M")
                else:
                    # No valid special survey date, default to +3 months
                    valid_date = anniversary_next_year + timedelta(days=90)
                    logger.info(f"🎯 No valid Special Survey Cycle → Valid Date = Anniversary + 3M")
                    
            except Exception as parse_error:
                logger.warning(f"⚠️ Could not parse special_survey_cycle_to: {parse_error}")
                # Default to +3 months
                valid_date = anniversary_next_year + timedelta(days=90)
                logger.info(f"🎯 Parse error → Valid Date = Anniversary + 3M")
        else:
            # No special survey cycle to, default to +3 months
            valid_date = anniversary_next_year + timedelta(days=90)
            logger.info(f"🎯 No Special Survey Cycle To → Valid Date = Anniversary + 3M")
        
        valid_date_str = valid_date.strftime("%Y-%m-%d")
        logger.info(f"✅ Calculated Next Annual Survey Valid Date: {valid_date_str}")
        return valid_date_str
        
    except Exception as e:
        logger.error(f"❌ Error calculating next annual survey date: {e}")
        return None


async def calculate_valid_date(
    test_report_name: str,
    issued_date: str,
    ship_id: str,
    mongo_db: Any
) -> Optional[str]:
    """
    Calculate valid date based ONLY on Issued Date + Equipment Interval
    Does NOT use AI extraction for valid_date
    
    LOGIC FLOW:
    1. Match test_report_name with EQUIPMENT_INTERVALS
    2. If interval type is "months": Valid Date = Issued Date + months
    3. If interval type is "next_annual_survey": Calculate based on Anniversary Date and Special Survey Cycle
    4. If no match found: Default to 12 months
    
    Args:
        test_report_name: Name of equipment (e.g., "EEBD", "Life Raft", "EPIRB")
        issued_date: Date when inspection/maintenance was performed (YYYY-MM-DD)
        ship_id: Ship ID for database queries
        mongo_db: MongoDB instance
        
    Returns:
        Valid date in YYYY-MM-DD format or None if cannot calculate
    """
    try:
        logger.info(f"🧮 Calculating Valid Date for: {test_report_name}")
        logger.info(f"   📅 Issued Date: {issued_date}")
        
        if not issued_date or not test_report_name:
            logger.warning("⚠️ Missing required fields: test_report_name or issued_date")
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
        matched_key = None
        for key, data in EQUIPMENT_INTERVALS.items():
            if key in equipment_key or equipment_key in key:
                interval_data = data
                matched_key = key
                logger.info(f"✅ Matched equipment '{test_report_name}' with '{key}': {data['description']}")
                break
        
        if not interval_data:
            # Default to 12 months for unknown equipment
            logger.warning(f"⚠️ No specific interval found for '{test_report_name}', defaulting to 12 months")
            interval_data = {"type": "months", "value": 12, "description": "Annual service (default)"}
        
        # Calculate valid date based on interval type
        if interval_data["type"] == "months":
            # Simple calculation: issued_date + months
            months_to_add = interval_data["value"]
            # More accurate month calculation
            new_month = issued_dt.month + months_to_add
            new_year = issued_dt.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            
            try:
                valid_dt = datetime(new_year, new_month, issued_dt.day)
            except ValueError:
                # Handle invalid date (e.g., Feb 31)
                import calendar
                last_day = calendar.monthrange(new_year, new_month)[1]
                valid_dt = datetime(new_year, new_month, min(issued_dt.day, last_day))
            
            valid_date = valid_dt.strftime("%Y-%m-%d")
            logger.info(f"✅ Calculated valid date (months): {valid_date} (Issued: {issued_date} + {months_to_add} months)")
            return valid_date
            
        elif interval_data["type"] == "next_annual_survey":
            # Calculate based on Anniversary Date and Special Survey Cycle
            logger.info(f"🎯 Equipment requires Next Annual Survey calculation")
            valid_date = await calculate_next_annual_survey_date(ship_id, mongo_db)
            
            if valid_date:
                logger.info(f"✅ Calculated valid date (Next Annual Survey): {valid_date}")
                return valid_date
            else:
                logger.warning(f"⚠️ Could not calculate Next Annual Survey, falling back to 12 months")
                # Fallback to 12 months
                valid_dt = issued_dt + timedelta(days=365)
                valid_date = valid_dt.strftime("%Y-%m-%d")
                return valid_date
        
        else:
            logger.warning(f"⚠️ Unknown interval type: {interval_data['type']}")
            return None
        
    except Exception as e:
        logger.error(f"❌ Error calculating valid date: {e}")
        return None
