"""
Next Survey Date Calculator
Automatically calculate next survey date based on certificate type and business rules
"""
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


def calculate_next_survey(
    doc_type: str, 
    valid_date: datetime = None,
    issue_date: datetime = None,
    last_endorse: datetime = None
) -> datetime:
    """
    Calculate next survey date based on DOC type and business rules
    
    Args:
        doc_type: "full_term", "short_term", or "interim"
        valid_date: Certificate validity/expiry date
        issue_date: Certificate issue date
        last_endorse: Last endorsement date
        
    Returns:
        Next survey date (datetime) or None
        
    Business Rules:
    1. Full Term DOC:
       - Anniversary date = day/month of valid_date (annually)
       - Next survey = Anniversary date next year ± 3 months window
       - Use most recent: last_endorse or issue_date
       
    2. Short Term DOC:
       - No annual survey (validity < 6 months)
       - Return None
       
    3. Interim DOC:
       - Next survey = Valid date - 3 months
    """
    if not doc_type:
        logger.warning("⚠️ No doc_type provided, cannot calculate next survey")
        return None
    
    doc_type_lower = doc_type.lower().strip()
    
    # SHORT TERM DOC: No survey needed
    if doc_type_lower == "short_term":
        logger.info("📋 Short Term DOC - No annual survey required")
        return None
    
    # INTERIM DOC: Valid date - 3 months
    if doc_type_lower == "interim":
        if not valid_date:
            logger.warning("⚠️ Interim DOC: valid_date required but not provided")
            return None
        
        next_survey = valid_date - relativedelta(months=3)
        logger.info(f"📋 Interim DOC: Next survey = Valid date ({valid_date.date()}) - 3 months = {next_survey.date()}")
        return next_survey
    
    # FULL TERM DOC: Anniversary date ± 3 months
    if doc_type_lower == "full_term":
        if not valid_date:
            logger.warning("⚠️ Full Term DOC: valid_date required but not provided")
            return None
        
        # Determine base date (most recent: last_endorse or issue_date)
        base_date = last_endorse or issue_date or datetime.now()
        
        # Anniversary date = day/month of valid_date
        # Next anniversary = same day/month in the year after base_date
        anniversary_day = valid_date.day
        anniversary_month = valid_date.month
        
        # Calculate next anniversary year
        next_anniversary_year = base_date.year + 1
        
        # Handle edge case: if we're before this year's anniversary, use this year
        try:
            this_year_anniversary = datetime(base_date.year, anniversary_month, anniversary_day)
            if base_date < this_year_anniversary:
                next_anniversary_year = base_date.year
        except ValueError:
            # Handle invalid dates (e.g., Feb 29 in non-leap year)
            pass
        
        try:
            next_anniversary = datetime(next_anniversary_year, anniversary_month, anniversary_day)
        except ValueError:
            # Handle Feb 29 in non-leap year -> use Feb 28
            next_anniversary = datetime(next_anniversary_year, anniversary_month, 28)
        
        logger.info(f"📋 Full Term DOC:")
        logger.info(f"   Valid date: {valid_date.date()}")
        logger.info(f"   Anniversary: {anniversary_day}/{anniversary_month} (annually)")
        logger.info(f"   Base date: {base_date.date()}")
        logger.info(f"   Next anniversary: {next_anniversary.date()}")
        logger.info(f"   Survey window: {(next_anniversary - relativedelta(months=3)).date()} to {(next_anniversary + relativedelta(months=3)).date()} (±3 months)")
        
        # Return the anniversary date (center of ±3 months window)
        return next_anniversary
    
    logger.warning(f"⚠️ Unknown doc_type: {doc_type}")
    return None


def format_next_survey_info(doc_type: str, next_survey: datetime) -> str:
    """
    Generate human-readable info about next survey
    
    Returns:
        Formatted string explaining the survey schedule
    """
    if not next_survey:
        return "No survey required"
    
    doc_type_lower = doc_type.lower().strip() if doc_type else ""
    
    if doc_type_lower == "full_term":
        window_start = (next_survey - relativedelta(months=3)).strftime("%d/%m/%Y")
        window_end = (next_survey + relativedelta(months=3)).strftime("%d/%m/%Y")
        return f"Annual survey: {next_survey.strftime('%d/%m/%Y')} (Window: {window_start} - {window_end})"
    
    if doc_type_lower == "interim":
        return f"Survey before expiry: {next_survey.strftime('%d/%m/%Y')}"
    
    return next_survey.strftime("%d/%m/%Y")
