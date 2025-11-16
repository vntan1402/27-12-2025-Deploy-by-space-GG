"""
Test Report Valid Date Calculator
Calculates valid_date based on equipment type and issued_date
Based on TEST_REPORT_MIGRATION_PLAN.md Task 2.2
"""
import logging
from datetime import datetime
from typing import Optional
from dateutil import parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

# Default maintenance intervals (in months) for each equipment type
# Based on maritime safety equipment maintenance standards
DEFAULT_INTERVALS = {
    # 12 months interval (annual)
    'eebd': 12,
    'emergency escape breathing device': 12,
    'scba': 12,
    'self-contained breathing apparatus': 12,
    'self contained breathing apparatus': 12,
    'portable fire extinguisher': 12,
    'fire extinguisher': 12,
    'portable foam applicator': 12,
    'life raft': 12,
    'liferaft': 12,
    'lifeboat': 12,
    'rescue boat': 12,
    'co2 system': 12,
    'carbon dioxide system': 12,
    'fire detection system': 12,
    'fire alarm system': 12,
    'gas detector': 12,
    'gas detection system': 12,
    'sart': 12,
    'search and rescue transponder': 12,
    'fire hose': 12,
    'fire fighting hose': 12,
    'fireman outfit': 12,
    "fireman's outfit": 12,
    'breathing apparatus': 12,
    'fixed fire extinguishing system': 12,
    'sprinkler system': 12,
    'emergency fire pump': 12,
    'hru': 12,
    'hydrostatic release unit': 12,
    
    # 24 months interval (biennial)
    'epirb': 24,
    'emergency position indicating radio beacon': 24,
    
    # 36 months interval (3 years)
    'immersion suit': 36,
    'survival suit': 36,
    'life jacket': 36,
    'lifejacket': 36,
    'life vest': 36,
    
    # 60 months interval (5 years)
    'davit': 60,
    'launching appliance': 60,
}


async def calculate_valid_date(
    test_report_name: str,
    issued_date: str,
    ship_id: str,
    mongo_db
) -> Optional[str]:
    """
    Calculate valid date based on equipment type and issued date
    
    Priority:
    1. Ship-specific interval (from ships.test_report_intervals)
    2. Default interval (from DEFAULT_INTERVALS)
    3. Fallback to 12 months
    
    Args:
        test_report_name: Equipment name (e.g., "EEBD", "Life Raft")
        issued_date: Issued date (ISO format or any parseable format)
        ship_id: Ship ID (to get ship-specific intervals)
        mongo_db: MongoDB instance
    
    Returns:
        Valid date in ISO format (YYYY-MM-DD) or None if calculation fails
    """
    try:
        logger.info(f"🧮 Calculating valid date for: '{test_report_name}', issued: {issued_date}")
        
        # Parse issued date
        try:
            issued_date_obj = parser.parse(issued_date)
            logger.info(f"📅 Parsed issued date: {issued_date_obj.strftime('%Y-%m-%d')}")
        except Exception as e:
            logger.error(f"Failed to parse issued_date '{issued_date}': {e}")
            return None
        
        # Normalize equipment name for lookup
        equipment_name_normalized = test_report_name.lower().strip()
        logger.info(f"🔍 Normalized equipment name: '{equipment_name_normalized}'")
        
        # Try to get ship-specific interval
        interval_months = None
        
        try:
            ship = await mongo_db.find_one("ships", {"id": ship_id})
            if ship:
                test_report_intervals = ship.get("test_report_intervals", {})
                
                if test_report_intervals:
                    logger.info(f"📋 Ship has custom intervals: {list(test_report_intervals.keys())}")
                    
                    # Try exact match first
                    if equipment_name_normalized in test_report_intervals:
                        interval_months = test_report_intervals[equipment_name_normalized]
                        logger.info(f"✅ Found ship-specific interval (exact match): {interval_months} months")
                    else:
                        # Try partial match
                        for key, value in test_report_intervals.items():
                            if key in equipment_name_normalized or equipment_name_normalized in key:
                                interval_months = value
                                logger.info(f"✅ Found ship-specific interval (partial match '{key}'): {interval_months} months")
                                break
                else:
                    logger.info("ℹ️ Ship has no custom test report intervals")
        except Exception as e:
            logger.warning(f"Could not fetch ship-specific intervals: {e}")
        
        # If no ship-specific interval, use default
        if interval_months is None:
            # Try exact match in default intervals
            if equipment_name_normalized in DEFAULT_INTERVALS:
                interval_months = DEFAULT_INTERVALS[equipment_name_normalized]
                logger.info(f"✅ Using default interval (exact match): {interval_months} months")
            else:
                # Try partial match in default intervals
                for key, value in DEFAULT_INTERVALS.items():
                    if key in equipment_name_normalized or equipment_name_normalized in key:
                        interval_months = value
                        logger.info(f"✅ Using default interval (partial match '{key}'): {interval_months} months")
                        break
                
                # If still not found, use default 12 months
                if interval_months is None:
                    interval_months = 12
                    logger.warning(f"⚠️ No interval found for '{test_report_name}', using default 12 months")
        
        # Calculate valid date using relativedelta for accurate month arithmetic
        valid_date_obj = issued_date_obj + relativedelta(months=interval_months)
        
        # Return in ISO format
        valid_date_str = valid_date_obj.strftime('%Y-%m-%d')
        logger.info(f"✅ Calculated valid date: {valid_date_str} ({interval_months} months from {issued_date_obj.strftime('%Y-%m-%d')})")
        
        return valid_date_str
        
    except Exception as e:
        logger.error(f"❌ Error calculating valid date: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None


def get_default_interval(equipment_name: str) -> int:
    """
    Get default interval for equipment type (utility function)
    
    Args:
        equipment_name: Equipment name
    
    Returns:
        Interval in months (default 12 if not found)
    """
    try:
        equipment_name_normalized = equipment_name.lower().strip()
        
        # Try exact match
        if equipment_name_normalized in DEFAULT_INTERVALS:
            return DEFAULT_INTERVALS[equipment_name_normalized]
        
        # Try partial match
        for key, value in DEFAULT_INTERVALS.items():
            if key in equipment_name_normalized or equipment_name_normalized in key:
                return value
        
        # Default
        return 12
        
    except Exception:
        return 12
