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
    
    # FULL TERM DOC: 5-year audit cycle with annual audits
    if doc_type_lower == "full_term":
        if not valid_date:
            logger.warning("⚠️ Full Term DOC: valid_date required but not provided")
            return None, None
        
        # Step 1: Determine Anniversary date (day/month of valid_date)
        anniversary_day = valid_date.day
        anniversary_month = valid_date.month
        
        # Step 2: Determine 5-year Audit Cycle
        cycle_end_year = valid_date.year
        cycle_start_year = cycle_end_year - 5
        
        logger.info(f"📋 Full Term DOC:")
        logger.info(f"   Valid date: {valid_date.date()}")
        logger.info(f"   Anniversary: {anniversary_day}/{anniversary_month} (annually)")
        logger.info(f"   Audit Cycle: {cycle_start_year} - {cycle_end_year}")
        
        # Step 3: Define all audit dates in the cycle
        audits = []
        
        # Annual Audits (1st, 2nd, 3rd, 4th)
        for i in range(1, 5):
            year = cycle_start_year + i
            try:
                audit_date = datetime(year, anniversary_month, anniversary_day)
                audits.append({
                    'date': audit_date,
                    'type': f'{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"} Annual',
                    'window_type': '±3M'
                })
            except ValueError:
                # Handle Feb 29 in non-leap year
                audit_date = datetime(year, anniversary_month, 28)
                audits.append({
                    'date': audit_date,
                    'type': f'{i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"} Annual',
                    'window_type': '±3M'
                })
        
        # Renewal Audit (valid_date with -3M window)
        audits.append({
            'date': valid_date,
            'type': 'Renewal',
            'window_type': '-3M'
        })
        
        # Step 4: Determine Next Audit based on Last Endorse or Issue Date
        now = datetime.now()
        
        # Use Last Endorse if available, otherwise use Issue Date as fallback
        reference_date = last_endorse if last_endorse else issue_date
        
        if reference_date:
            logger.info(f"   📅 Reference Date: {reference_date.date()} ({'Last Endorse' if last_endorse else 'Issue Date'})")
            
            # Find the latest completed audit
            last_completed_audit_index = -1
            
            for i, audit in enumerate(audits):
                audit_date = audit['date']
                audit_type = audit['type']
                window_type = audit['window_type']
                
                # Check if this audit is completed based on reference date
                audit_completed = False
                
                if window_type == '±3M':
                    # For Annual audits: completed if reference_date is within window
                    window_start = audit_date - relativedelta(months=3)
                    window_end = audit_date + relativedelta(months=3)
                    if window_start <= reference_date <= window_end:
                        audit_completed = True
                        logger.info(f"   ✓ {audit_type} completed on {reference_date.date()} (within window)")
                        last_completed_audit_index = i
                
                elif window_type == '-3M':
                    # For Renewal: completed if reference_date is within window
                    window_start = audit_date - relativedelta(months=3)
                    if window_start <= reference_date <= audit_date:
                        audit_completed = True
                        logger.info(f"   ✓ {audit_type} completed on {reference_date.date()} (within window)")
                        last_completed_audit_index = i
            
            # Next Audit = audit after the last completed one
            if last_completed_audit_index >= 0:
                next_audit_index = last_completed_audit_index + 1
                if next_audit_index < len(audits):
                    next_audit = audits[next_audit_index]
                    logger.info(f"   → Next Audit: {next_audit['date'].date()} ({next_audit['type']})")
                    return next_audit['date'], next_audit['type']
                else:
                    # All audits completed, should renew certificate
                    logger.warning(f"   ⚠️ All audits completed. Certificate should be renewed.")
                    return valid_date, 'Renewal'
            else:
                # No completed audit found, return first audit
                first_audit = audits[0]
                logger.info(f"   → Next Audit: {first_audit['date'].date()} ({first_audit['type']}) [First audit]")
                return first_audit['date'], first_audit['type']
        
        else:
            # No reference date (no Last Endorse and no Issue Date)
            # Return the first audit that hasn't passed yet
            for audit in audits:
                audit_date = audit['date']
                audit_type = audit['type']
                window_type = audit['window_type']
                
                if window_type == '±3M':
                    window_end = audit_date + relativedelta(months=3)
                    if now < window_end:
                        logger.info(f"   → Next Audit: {audit_date.date()} ({audit_type}) [No reference date]")
                        return audit_date, audit_type
                elif window_type == '-3M':
                    if now < audit_date:
                        logger.info(f"   → Next Audit: {audit_date.date()} ({audit_type}) [No reference date]")
                        return audit_date, audit_type
            
            # If all audits have passed, return Renewal
            logger.warning(f"   ⚠️ All audits have passed. Returning Renewal audit.")
            return valid_date, 'Renewal'
    
    logger.warning(f"⚠️ Unknown doc_type: {doc_type}")
    return None, None


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
