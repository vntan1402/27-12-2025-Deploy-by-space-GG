"""
Next Audit Date Calculator
Automatically calculate next audit date based on certificate type and business rules
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
) -> tuple:
    """
    Calculate next audit date and type based on DOC type and business rules
    
    Args:
        doc_type: "full_term", "short_term", or "interim"
        valid_date: Certificate validity/expiry date
        issue_date: Certificate issue date (not used in current logic)
        last_endorse: Last endorsement date (not used in current logic)
        
    Returns:
        Tuple of (next_audit_date, next_audit_type) or (None, None)
        
    Business Rules:
    1. Full Term DOC:
       - Anniversary date = day/month of valid_date
       - Audit cycle 5 years = (valid_year - 5) to valid_year
       - Annual Audits: 1st/2nd/3rd/4th on each anniversary (±3M window)
       - Renewal Audit: Valid date (-3M window)
       - Next audit determined by current date position in cycle
       
    2. Short Term DOC:
       - Next audit = None, Type = None
       
    3. Interim DOC:
       - Next audit = Valid date, Type = "Initial"
    """
    if not doc_type:
        logger.warning("⚠️ No doc_type provided, cannot calculate next audit")
        return None, None
    
    doc_type_lower = doc_type.lower().strip() if doc_type else ""
    
    # SHORT TERM DOC: No audit needed
    if doc_type_lower == "short_term":
        logger.info("📋 Short Term DOC - No audit required")
        return None, None
    
    # INTERIM DOC: Next audit = Valid date, Type = Initial
    if doc_type_lower == "interim":
        if not valid_date:
            logger.warning("⚠️ Interim DOC: valid_date required but not provided")
            return None, None
        
        next_audit_date = valid_date
        audit_type = "Initial"
        logger.info(f"📋 Interim DOC: Next audit = {next_audit_date.date()} | Type: {audit_type}")
        return next_audit_date, audit_type
    
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
        logger.info(f"   Audit window: {(next_anniversary - relativedelta(months=3)).date()} to {(next_anniversary + relativedelta(months=3)).date()} (±3 months)")
        
        # Return the anniversary date (center of ±3 months window)
        return next_anniversary
    
    logger.warning(f"⚠️ Unknown doc_type: {doc_type}")
    return None


def format_next_survey_info(doc_type: str, next_audit: datetime) -> str:
    """
    Generate human-readable info about next audit
    
    Returns:
        Formatted string explaining the audit schedule
    """
    if not next_audit:
        return "No audit required"
    
    doc_type_lower = doc_type.lower().strip() if doc_type else ""
    
    if doc_type_lower == "full_term":
        window_start = (next_audit - relativedelta(months=3)).strftime("%d/%m/%Y")
        window_end = (next_audit + relativedelta(months=3)).strftime("%d/%m/%Y")
        return f"Annual audit: {next_audit.strftime('%d/%m/%Y')} (Window: {window_start} - {window_end})"
    
    if doc_type_lower == "interim":
        return f"Audit before expiry: {next_audit.strftime('%d/%m/%Y')}"
    
    return next_audit.strftime("%d/%m/%Y")
