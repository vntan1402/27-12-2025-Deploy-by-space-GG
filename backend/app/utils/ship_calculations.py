"""
Ship maritime calculations utilities
Handles anniversary dates, docking schedules, and special survey cycles
"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from app.models.ship import AnniversaryDate, SpecialSurveyCycle, DryDockCycle
from app.repositories.certificate_repository import CertificateRepository

logger = logging.getLogger(__name__)

async def calculate_anniversary_date_from_certificates(ship_id: str) -> Optional[AnniversaryDate]:
    """
    Calculate anniversary date from Class and Statutory certificates.
    
    Logic:
    1. Filter certificates: Class, CSSC (SC), CSSE (SE), IOPP, IAPP, LLC (Loadline), CSSR (SR)
    2. Get all valid_dates from these certificates
    3. Find the day/month combination that appears most frequently
    4. Use that as the Anniversary Date
    """
    try:
        # Get all certificates for the ship
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # Keywords to identify Class and Statutory certificates
        statutory_keywords = [
            'CLASS', 'CLASSIFICATION',
            'CSSC', 'SC', 'SAFETY CONSTRUCTION',
            'CSSE', 'SE', 'SAFETY EQUIPMENT', 
            'CSSR', 'SR', 'SAFETY RADIO',
            'IOPP', 'OIL POLLUTION',
            'IAPP', 'AIR POLLUTION',
            'LLC', 'LOAD LINE', 'LOADLINE'
        ]
        
        # Filter Full Term Class/Statutory certificates with valid dates
        relevant_certs = []
        for cert in certificates:
            if cert.get('cert_type') != 'Full Term' or not cert.get('valid_date'):
                continue
            
            cert_name = (cert.get('cert_name') or '').upper()
            cert_abbr = (cert.get('cert_abbreviation') or '').upper()
            
            # Check if certificate matches any keyword
            is_relevant = any(
                keyword in cert_name or keyword in cert_abbr 
                for keyword in statutory_keywords
            )
            
            if is_relevant:
                relevant_certs.append(cert)
        
        if not relevant_certs:
            logger.info(f"No Class/Statutory certificates found for ship {ship_id}")
            return None
        
        # Count occurrences of each day/month combination
        date_counts = {}
        for cert in relevant_certs:
            valid_date = cert.get('valid_date')
            if isinstance(valid_date, str):
                try:
                    valid_date = datetime.fromisoformat(valid_date.replace('Z', '+00:00'))
                except:
                    continue
            
            if valid_date:
                key = (valid_date.day, valid_date.month)
                if key not in date_counts:
                    date_counts[key] = {
                        'count': 0,
                        'certs': []
                    }
                date_counts[key]['count'] += 1
                date_counts[key]['certs'].append(cert.get('cert_abbreviation') or cert.get('cert_name'))
        
        if not date_counts:
            logger.info(f"No valid dates found in Class/Statutory certificates for ship {ship_id}")
            return None
        
        # Find the most common day/month combination
        most_common = max(date_counts.items(), key=lambda x: x[1]['count'])
        anniversary_day, anniversary_month = most_common[0]
        count = most_common[1]['count']
        source_certs = most_common[1]['certs']
        
        anniversary = AnniversaryDate(
            day=anniversary_day,
            month=anniversary_month,
            auto_calculated=True,
            source_certificate_type=f"Most common ({count} certs): {', '.join(source_certs[:3])}{'...' if len(source_certs) > 3 else ''}",
            manual_override=False
        )
        
        logger.info(f"✅ Calculated anniversary date for ship {ship_id}: {anniversary_day}/{anniversary_month} (from {count} certificates)")
        return anniversary
        
    except Exception as e:
        logger.error(f"❌ Error calculating anniversary date for ship {ship_id}: {e}")
        return None

async def calculate_special_survey_cycle_from_certificates(ship_id: str) -> Optional[SpecialSurveyCycle]:
    """
    Calculate Special Survey cycle from Full Term Class certificates
    Following IMO/Classification Society standards (SOLAS, MARPOL, HSSC)
    
    UPDATED LOGIC (Backend-V1 compliant):
    - Filter Full Term certificates only
    - Filter Class certificates using comprehensive keywords
    - To Date = Latest valid_date (current cycle endpoint)
    - From Date = To Date - 5 years (IMO 5-year standard)
    """
    try:
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # Filter Full Term Class certificates (comprehensive keywords from backend-v1)
        class_keywords = [
            'class', 'classification', 'safety construction', 'safety equipment',
            'safety radio', 'cargo ship safety', 'passenger ship safety'
        ]
        
        full_term_class_certs = []
        for cert in certificates:
            cert_type = (cert.get('cert_type') or '').strip()
            cert_name = (cert.get('cert_name') or '').lower()
            
            # Only Full Term certificates
            if cert_type != 'Full Term':
                continue
            
            # Check if it's a Class certificate
            is_class_cert = any(keyword in cert_name for keyword in class_keywords)
            
            if is_class_cert and cert.get('valid_date'):
                full_term_class_certs.append(cert)
        
        if not full_term_class_certs:
            logger.info(f"No Full Term Class certificates found for ship {ship_id}")
            return None
        
        # Find certificate with latest valid_date (current cycle endpoint)
        latest_cert = None
        latest_date = None
        
        for cert in full_term_class_certs:
            valid_date_str = cert.get('valid_date')
            if valid_date_str:
                if isinstance(valid_date_str, str):
                    valid_date = datetime.fromisoformat(valid_date_str.replace('Z', '+00:00'))
                else:
                    valid_date = valid_date_str
                
                if latest_date is None or valid_date > latest_date:
                    latest_date = valid_date
                    latest_cert = cert
        
        if not latest_cert or not latest_date:
            logger.info(f"No valid certificate dates found for Special Survey cycle")
            return None
        
        # Calculate Special Survey Cycle: IMO 5-year standard
        to_date = latest_date  # End of current 5-year cycle
        
        # From Date: same day/month, 5 years earlier (BACKEND-V1 LOGIC)
        try:
            from_date = to_date.replace(year=to_date.year - 5)
        except ValueError:
            # Handle leap year edge case (Feb 29th)
            from_date = to_date.replace(year=to_date.year - 5, month=2, day=28)
        
        # Determine cycle type
        cert_name = latest_cert.get('cert_name', 'Class Certificate')
        cycle_type = "Class Survey Cycle"
        
        if "safety construction" in cert_name.lower():
            cycle_type = "SOLAS Safety Construction Survey Cycle"
        elif "safety equipment" in cert_name.lower():
            cycle_type = "SOLAS Safety Equipment Survey Cycle"
        elif "safety radio" in cert_name.lower():
            cycle_type = "SOLAS Safety Radio Survey Cycle"
        
        cycle = SpecialSurveyCycle(
            from_date=from_date,
            to_date=to_date,
            intermediate_required=True,  # IMO requirement
            cycle_type=cycle_type
        )
        
        logger.info(f"✅ Calculated Special Survey cycle for ship {ship_id}: {from_date.strftime('%d/%m/%Y')} - {to_date.strftime('%d/%m/%Y')} from {cert_name}")
        return cycle
        
    except Exception as e:
        logger.error(f"❌ Error calculating Special Survey cycle for ship {ship_id}: {e}")
        return None

async def calculate_next_docking(ship_id: str, last_docking: Optional[datetime]) -> Optional[datetime]:
    """
    Calculate next docking date based on last docking
    UPDATED 2025: 36 months from last docking (extended from old 30 months)
    """
    try:
        if not last_docking:
            logger.info(f"No last docking date provided for ship {ship_id}")
            return None
        
        if isinstance(last_docking, str):
            last_docking = datetime.fromisoformat(last_docking.replace('Z', '+00:00'))
        
        # Next docking: 36 months (3 years) from last docking - ENHANCED LOGIC 2025
        next_docking = last_docking + relativedelta(months=36)
        
        logger.info(f"✅ Calculated next docking for ship {ship_id}: {next_docking} (Last Docking + 36 months)")
        return next_docking
        
    except Exception as e:
        logger.error(f"❌ Error calculating next docking for ship {ship_id}: {e}")
        return None

def format_anniversary_date_display(anniversary: AnniversaryDate) -> str:
    """Format anniversary date for display"""
    if not anniversary or not anniversary.day or not anniversary.month:
        return "Not set"
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_name = months[anniversary.month - 1] if 1 <= anniversary.month <= 12 else "Unknown"
    
    return f"{anniversary.day} {month_name}"

def parse_date(date_value) -> Optional[datetime]:
    """Parse date from various formats"""
    if not date_value:
        return None
    
    if isinstance(date_value, datetime):
        return date_value
    
    if isinstance(date_value, str):
        # Try ISO format first
        try:
            # Handle ISO with Z
            if date_value.endswith('Z'):
                return datetime.fromisoformat(date_value[:-1]).replace(tzinfo=None)
            return datetime.fromisoformat(date_value).replace(tzinfo=None)
        except:
            pass
        
        # Try DD/MM/YYYY format
        try:
            if '/' in date_value:
                parts = date_value.split('/')
                if len(parts) == 3:
                    day, month, year = parts
                    return datetime(int(year), int(month), int(day))
        except:
            pass
    
    return None

def calculate_next_survey_info(certificate_data: dict, ship_data: dict) -> dict:
    """
    Calculate Next Survey and Next Survey Type based on IMO regulations
    Migrated from backend-v1
    
    Logic:
    1. Determine Special Survey Cycle and Anniversary Date
    2. In 5-year Special Survey Cycle, Anniversary Date each year = Annual Survey
    3. Annual Surveys: 1st, 2nd, 3rd, 4th Annual Survey
    4. Next Survey = nearest future Annual Survey date (dd/MM/yyyy format) with ±3 months window
    5. Condition certificates: Next Survey = valid_date
    6. Next Survey Type = nearest future Annual Survey type with Intermediate Survey considerations
    
    Args:
        certificate_data: Certificate information
        ship_data: Ship information
        
    Returns:
        dict with next_survey, next_survey_type, and reasoning
    """
    try:
        # Extract certificate information
        cert_name = (certificate_data.get('cert_name') or '').upper()
        cert_type = (certificate_data.get('cert_type') or '').upper()
        cert_abbreviation = (certificate_data.get('cert_abbreviation') or '').upper()
        valid_date = certificate_data.get('valid_date')
        last_endorse = certificate_data.get('last_endorse')
        has_annual_survey = certificate_data.get('has_annual_survey')  # ⭐ NEW: Get flag from AI analysis
        current_date = datetime.now()
        
        # Parse valid date
        valid_dt = parse_date(valid_date)
        
        # Rule 1: No valid date = no Next Survey
        if not valid_dt:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'No valid date available'
            }
        
        # Rule 2: If certificate is expired, no Next Survey
        today = datetime.now()
        if valid_dt < today:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'Certificate expired - no next survey scheduled'
            }
        
        # Rule 3: Condition certificates = valid_date with -3M window
        if 'CONDITION' in cert_type:
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'Condition Certificate Expiry',
                'reasoning': 'Condition certificate uses valid date as next survey with -3M window',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': -3
            }
        
        # Rule 3a: Interim certificates = valid_date with -3M window, Type = "FT Issue"
        if 'INTERIM' in cert_type:
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'FT Issue',
                'reasoning': 'Interim certificate: Full Term Issue before valid date with -3M window',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': -3
            }
        
        # Rule 3b: Statement certificates = valid_date with -3M window
        if 'STATEMENT' in cert_type or 'STATEMENT' in cert_name:
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'Statement Expiry',
                'reasoning': 'Statement certificate uses valid date as next survey with -3M window',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': -3
            }
        
        # ⭐ Rule 4: Check has_annual_survey flag from AI analysis (PRIORITY)
        # If AI analyzed the document and determined it has no annual survey sections
        if has_annual_survey is False:
            logger.info(f"⭐ Certificate '{cert_name}' ({cert_abbreviation}) has no annual survey (AI flag: has_annual_survey=false)")
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'Renewal',
                'reasoning': 'AI analysis: Certificate does not have annual survey endorsement sections',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': -3
            }
        
        # ⭐ Rule 5: Fallback - Certificates WITHOUT annual surveys (only Renewal)
        # For certificates that don't have has_annual_survey flag set (legacy data)
        # Use hardcoded list as fallback
        renewal_only_certs = [
            'ISPP', 'SEWAGE', 'INTERNATIONAL SEWAGE',
            'AFSC', 'ANTI-FOULING', 'ANTI FOULING',
            'TONNAGE',
            'CSR', 'CONTINUOUS SYNOPSIS',
            'REGISTRY', 'CERTIFICATE OF REGISTRY',
            # Insurance certificates - no annual surveys
            'P&I', 'P & I', 'PROTECTION AND INDEMNITY', 'PROTECTION & INDEMNITY',
            'INSURANCE', 'CIVIL LIABILITY', 'CLC',
            'BUNKER', 'BUNKERING',
            'WRECK REMOVAL', 'WRECK',
            'WAR RISK', 'WAR',
            'HULL', 'H&M', 'HULL & MACHINERY', 'HULL AND MACHINERY',
            'LIABILITY', 'INDEMNITY',
            'BLUE CARD', 'BLUE-CARD'
        ]
        
        # Check if certificate is renewal-only type based on cert_name or cert_abbreviation
        # Only apply if has_annual_survey is None (not set by AI)
        is_renewal_only = any(keyword in cert_name or keyword in cert_abbreviation for keyword in renewal_only_certs)
        
        if has_annual_survey is None and is_renewal_only:
            logger.info(f"⭐ Certificate '{cert_name}' ({cert_abbreviation}) is renewal-only type (fallback list)")
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'Renewal',
                'reasoning': 'Certificate type in renewal-only list - no annual survey required',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': -3
            }
        
        # Get ship anniversary date and special survey cycle
        ship_anniversary = ship_data.get('anniversary_date', {})
        special_survey_cycle = ship_data.get('special_survey_cycle', {})
        
        # Determine anniversary day/month
        anniversary_day = None
        anniversary_month = None
        
        if isinstance(ship_anniversary, dict):
            anniversary_day = ship_anniversary.get('day')
            anniversary_month = ship_anniversary.get('month')
        
        # If no ship anniversary, try to derive from certificate valid_date
        if not anniversary_day or not anniversary_month:
            if valid_dt:
                anniversary_day = valid_dt.day
                anniversary_month = valid_dt.month
            else:
                return {
                    'next_survey': '-',
                    'next_survey_type': '-',
                    'reasoning': 'Cannot determine anniversary date'
                }
        
        # Determine certificate's survey window (±3 months for all certificates)
        window_months = 3
        
        # Calculate 5-year cycle based on valid_date or special survey cycle
        cycle_start = None
        cycle_end = None
        
        # Priority 1: Use ship's special_survey_cycle if exists
        if isinstance(special_survey_cycle, dict):
            cycle_from = special_survey_cycle.get('from_date')
            cycle_to = special_survey_cycle.get('to_date')
            
            if cycle_from and cycle_to:
                cycle_start = parse_date(cycle_from)
                cycle_end = parse_date(cycle_to)
                logger.info(f"Using ship's Special Survey Cycle: {cycle_start.strftime('%Y-%m-%d') if cycle_start else 'None'} to {cycle_end.strftime('%Y-%m-%d') if cycle_end else 'None'}")
        
        # Priority 2: If no cycle in ship data, derive from certificate valid_date
        if not cycle_start or not cycle_end:
            if valid_dt:
                # Assume certificate valid_date is part of current 5-year cycle
                years_from_valid = (current_date.year - valid_dt.year)
                if years_from_valid >= 0:
                    # If valid_date is in the past, it might be from previous cycle
                    cycle_start = datetime(
                        valid_dt.year - (years_from_valid % 5),
                        anniversary_month, 
                        anniversary_day
                    )
                    cycle_end = datetime(
                        cycle_start.year + 5, 
                        anniversary_month, 
                        anniversary_day
                    )
                else:
                    # Valid_date is in future
                    cycle_start = datetime(
                        current_date.year,
                        anniversary_month, 
                        anniversary_day
                    )
                    cycle_end = datetime(
                        cycle_start.year + 5, 
                        anniversary_month, 
                        anniversary_day
                    )
        
        if not cycle_start or not cycle_end:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'Cannot determine survey cycle'
            }
        
        # Generate Annual Survey dates for the 5-year cycle
        annual_surveys = []
        for i in range(1, 5):  # 1st, 2nd, 3rd, 4th Annual Survey
            survey_date = datetime(cycle_start.year + i, anniversary_month, anniversary_day)
            annual_surveys.append({
                'date': survey_date,
                'type': f'{i}{"st" if i == 1 else "nd" if i == 2 else "rd" if i == 3 else "th"} Annual Survey',
                'number': i
            })
        
        # Add Special Survey at the end of cycle
        annual_surveys.append({
            'date': cycle_end,
            'type': 'Special Survey',
            'number': 5
        })
        
        # ⭐ FIXED LOGIC: Use last_endorse to determine which surveys are completed
        last_endorse = certificate_data.get('last_endorse')
        last_endorse_dt = parse_date(last_endorse)
        
        # ⭐ IMPORTANT: If no last_endorse at all, NO surveys are completed
        # This means the 1st Annual Survey is still pending
        
        # Determine which surveys are completed based on last_endorse
        incomplete_surveys = []
        for survey in annual_surveys:
            survey_date = survey['date']
            survey_completed = False
            
            # Calculate survey window
            if survey['type'] == 'Special Survey':
                # Special Survey only has -3M window
                window_open = survey_date - relativedelta(months=window_months)
                window_close = survey_date
            else:
                # Annual Survey has ±3M window
                window_open = survey_date - relativedelta(months=window_months)
                window_close = survey_date + relativedelta(months=window_months)
            
            if last_endorse_dt:
                # Survey is completed if:
                # 1. Last Endorse is within survey window, OR
                # 2. Last Endorse is after the window_close (survey already done)
                if window_open <= last_endorse_dt <= window_close:
                    survey_completed = True
                    logger.info(f"✅ {survey['type']} ({survey_date.strftime('%d/%m/%Y')}): COMPLETED (Last Endorse {last_endorse_dt.strftime('%d/%m/%Y')} within window)")
                elif last_endorse_dt > window_close:
                    survey_completed = True
                    logger.info(f"✅ {survey['type']} ({survey_date.strftime('%d/%m/%Y')}): COMPLETED (Last Endorse {last_endorse_dt.strftime('%d/%m/%Y')} after window_close)")
            else:
                # ⭐ No last_endorse means NO surveys are completed
                survey_completed = False
                logger.info(f"⏳ {survey['type']} ({survey_date.strftime('%d/%m/%Y')}): NOT COMPLETED (No Last Endorse)")
            
            if not survey_completed:
                incomplete_surveys.append(survey)
        
        # ⭐ FIXED: Include surveys where window is still open (not just future surveys)
        # A survey is "actionable" if:
        # 1. Its window_close is in the future (can still complete it), OR
        # 2. Its date is in the future
        actionable_surveys = []
        for survey in incomplete_surveys:
            survey_date = survey['date']
            
            # Calculate window_close
            if survey['type'] == 'Special Survey':
                window_close = survey_date
            else:
                window_close = survey_date + relativedelta(months=window_months)
            
            # Survey is actionable if window_close is in the future
            if window_close >= current_date:
                actionable_surveys.append(survey)
                logger.info(f"📋 {survey['type']}: Actionable (window_close {window_close.strftime('%d/%m/%Y')} >= today)")
        
        if not actionable_surveys:
            # If no actionable surveys in current cycle, start next cycle
            next_cycle_start = cycle_end
            next_annual_date = datetime(next_cycle_start.year + 1, anniversary_month, anniversary_day)
            actionable_surveys = [{
                'date': next_annual_date,
                'type': '1st Annual Survey',
                'number': 1
            }]
            logger.info(f"🔄 No actionable surveys in current cycle, moving to next cycle: 1st Annual Survey on {next_annual_date.strftime('%d/%m/%Y')}")
        
        # Get the nearest actionable survey (by survey date, not window)
        next_survey_info = min(actionable_surveys, key=lambda x: x['date'])
        next_survey_date = next_survey_info['date']
        next_survey_type = next_survey_info['type']
        
        logger.info(f"⭐ Next Survey: {next_survey_type} on {next_survey_date.strftime('%d/%m/%Y')}")
        
        # Check for Intermediate Survey considerations
        if next_survey_info['number'] in [2, 3]:  # 2nd or 3rd Annual Survey
            # Check if intermediate survey is required
            ship_last_intermediate = ship_data.get('last_intermediate_survey')
            
            if next_survey_info['number'] == 2:
                # 2nd Annual Survey can be Intermediate Survey
                next_survey_type = '2nd Annual Survey/Intermediate Survey'
            elif next_survey_info['number'] == 3:
                # 3rd Annual Survey logic
                if ship_last_intermediate:
                    last_intermediate_dt = parse_date(ship_last_intermediate)
                    if last_intermediate_dt and last_intermediate_dt < next_survey_date:
                        next_survey_type = '3rd Annual Survey'
                    else:
                        next_survey_type = 'Intermediate Survey'
                else:
                    # No last intermediate info = intermediate survey needed
                    next_survey_type = 'Intermediate Survey'
        
        # ⚠️ CRITICAL VALIDATION: Next Survey cannot exceed Valid Date
        # If next survey is after valid date, the certificate expires before survey date
        # This is an invalid state - adjust to use valid_date as next_survey
        if next_survey_date > valid_dt:
            logger.warning(f"⚠️ Next Survey ({next_survey_date.strftime('%d/%m/%Y')}) > Valid Date ({valid_dt.strftime('%d/%m/%Y')})")
            logger.warning(f"   Adjusting Next Survey to Valid Date to prevent invalid state")
            next_survey_date = valid_dt
            next_survey_type = 'Certificate Expiry (Before Anniversary)'
            window_months = 0  # No window when using valid_date
        
        # Format next survey date with window
        next_survey_formatted = next_survey_date.strftime('%d/%m/%Y')
        
        # Add window information
        if window_months == 0:
            # No window for adjusted surveys
            next_survey_with_window = next_survey_formatted
        elif next_survey_type == 'Special Survey':
            window_text_en = f'-{window_months}M'
            next_survey_with_window = f'{next_survey_formatted} ({window_text_en})'
        else:
            window_text_en = f'±{window_months}M'
            next_survey_with_window = f'{next_survey_formatted} ({window_text_en})'
        
        return {
            'next_survey': next_survey_with_window,
            'next_survey_type': next_survey_type,
            'reasoning': f'Based on {anniversary_day}/{anniversary_month} anniversary date and 5-year survey cycle',
            'raw_date': next_survey_formatted,
            'window_months': window_months
        }
        
    except Exception as e:
        logger.error(f"Error calculating next survey info: {e}")
        return {
            'next_survey': '-',
            'next_survey_type': '-',
            'reasoning': f'Error in calculation: {str(e)}'
        }

def calculate_audit_certificate_next_survey(certificate_data: dict) -> dict:
    """
    Calculate Next Survey and Next Survey Type for Audit Certificates (ISM/ISPS/MLC)
    Migrated from backend-v1
    
    Logic:
    1. Interim: Next Survey = Valid Date - 3M, Type = "Initial"
    2. Short Term: Next Survey = N/A, Type = N/A
    3. Full Term:
       - If has Last Endorse: Next Survey = Valid Date - 3M, Type = "Renewal"
       - If no Last Endorse: Next Survey = Valid Date - 2 years, Type = "Intermediate"
    4. Special documents (DMLC I, DMLC II, SSP): Next Survey = N/A, Type = N/A
    """
    try:
        # Extract certificate information
        cert_name = (certificate_data.get('cert_name') or '').upper()
        cert_type = (certificate_data.get('cert_type') or '').upper()
        valid_date = certificate_data.get('valid_date')
        last_endorse = certificate_data.get('last_endorse')
        current_date = datetime.now()
        
        # Parse valid_date
        valid_dt = parse_date(valid_date)
        
        # Rule: No valid date = no Next Survey
        if not valid_dt:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'No valid date available'
            }
        
        # ⭐ NEW RULE: If certificate is expired, no Next Survey
        today = datetime.now()
        if valid_dt < today:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'Certificate expired - no next survey scheduled'
            }
        
        # Rule 4: Special documents (DMLC I, DMLC II, SSP) = N/A
        special_docs = ['DMLC I', 'DMLC II', 'DMLC PART I', 'DMLC PART II', 'SSP', 'SHIP SECURITY PLAN']
        if any(doc in cert_name for doc in special_docs):
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': f'{cert_name} does not require Next Survey calculation'
            }
        
        # Rule 2: Short Term = N/A
        if 'SHORT' in cert_type or 'SHORT TERM' in cert_type:
            return {
                'next_survey': '-',
                'next_survey_type': '-',
                'reasoning': 'Short Term certificates do not require Next Survey'
            }
        
        # Rule 1: Interim = Valid Date - 3M, Type = "FT Issue" (Full Term Issue)
        if 'INTERIM' in cert_type:
            next_survey_date = valid_dt - relativedelta(months=3)
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'FT Issue',
                'reasoning': 'Interim certificate: Next Survey = Valid Date - 3 months (Full Term Issue)',
                'raw_date': next_survey_date.strftime('%d/%m/%Y'),
                'window_months': 3
            }
        
        # Rule 3: Full Term certificates
        if 'FULL' in cert_type or 'FULL TERM' in cert_type or cert_type == 'FULL TERM':
            # Parse last_endorse if exists
            last_endorse_dt = parse_date(last_endorse)
            
            # Priority 1: Check Last Endorse
            if last_endorse_dt:
                # Has Last Endorse → Renewal
                next_survey_date = valid_dt - relativedelta(months=3)
                return {
                    'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                    'next_survey_type': 'Renewal',
                    'reasoning': 'Full Term with Last Endorse: Next Survey = Valid Date - 3 months (Renewal)',
                    'raw_date': next_survey_date.strftime('%d/%m/%Y'),
                    'window_months': 3
                }
            else:
                # No Last Endorse → Intermediate
                intermediate_date = valid_dt - relativedelta(months=30)
                return {
                    'next_survey': intermediate_date.strftime('%d/%m/%Y') + ' (±6M)',
                    'next_survey_type': 'Intermediate',
                    'reasoning': 'Full Term without Last Endorse: Next Survey = Valid Date - 30 months (Intermediate)',
                    'raw_date': intermediate_date.strftime('%d/%m/%Y'),
                    'window_months': 6
                }
        
        # Default: Cannot determine
        return {
            'next_survey': '-',
            'next_survey_type': '-',
            'reasoning': f'Cannot determine Next Survey for cert_type: {cert_type}'
        }
        
    except Exception as e:
        logger.error(f"Error calculating audit certificate next survey: {e}")
        return {
            'next_survey': '-',
            'next_survey_type': '-',
            'reasoning': f'Error in calculation: {str(e)}'
        }

def calculate_next_docking_enhanced(
    last_docking: Optional[datetime],
    last_docking_2: Optional[datetime],
    special_survey_to_date: Optional[datetime],
    ship_age: Optional[int] = None,
    class_society: Optional[str] = None
) -> dict:
    """
    Calculate Next Docking date using ENHANCED LOGIC (2025)
    Migrated from backend-v1
    
    NEW LOGIC:
    1. Get Last Docking (nearest: last_docking or last_docking_2)
    2. Calculate: Last Docking + 36 months
    3. Get Special Survey Cycle To Date
    4. Choose whichever is NEARER: Last Docking + 36 months OR Special Survey To Date
    """
    try:
        # Step 1: Find nearest (most recent) Last Docking
        reference_docking = None
        docking_source = None
        
        if last_docking and last_docking_2:
            if last_docking >= last_docking_2:
                reference_docking = last_docking
                docking_source = "Last Docking 1"
            else:
                reference_docking = last_docking_2
                docking_source = "Last Docking 2"
        elif last_docking:
            reference_docking = last_docking
            docking_source = "Last Docking 1"
        elif last_docking_2:
            reference_docking = last_docking_2
            docking_source = "Last Docking 2"
        
        if not reference_docking:
            return {
                'next_docking': None,
                'calculation_method': None,
                'reasoning': 'No docking dates available'
            }
        
        logger.info(f"Using nearest Last Docking from {docking_source}: {reference_docking.strftime('%d/%m/%Y')}")
        
        # Step 2: Calculate Last Docking + 36 months
        docking_plus_36_months = reference_docking + relativedelta(months=36)
        logger.info(f"Last Docking + 36 months: {reference_docking.strftime('%d/%m/%Y')} + 36M = {docking_plus_36_months.strftime('%d/%m/%Y')}")
        
        # Step 3: If no Special Survey To Date, use Last Docking + 36 months
        if not special_survey_to_date:
            logger.info("No Special Survey To Date, using Last Docking + 36 months")
            return {
                'next_docking': docking_plus_36_months,
                'calculation_method': 'Last Docking + 36 months',
                'reasoning': f'{docking_source} ({reference_docking.strftime("%d/%m/%Y")}) + 36 months',
                'docking_source': docking_source,
                'reference_docking': reference_docking.strftime('%d/%m/%Y')
            }
        
        # Step 4: Compare both dates and choose NEARER (earlier) one
        logger.info(f"Special Survey To Date: {special_survey_to_date.strftime('%d/%m/%Y')}")
        
        if docking_plus_36_months <= special_survey_to_date:
            # Last Docking + 36 months is nearer (earlier)
            next_docking = docking_plus_36_months
            calculation_method = "Last Docking + 36 months"
            reasoning = f'{docking_source} ({reference_docking.strftime("%d/%m/%Y")}) + 36 months = {docking_plus_36_months.strftime("%d/%m/%Y")} (earlier than Special Survey To Date)'
        else:
            # Special Survey To Date is nearer (earlier)
            next_docking = special_survey_to_date
            calculation_method = "Special Survey Cycle To Date"
            reasoning = f'Special Survey To Date ({special_survey_to_date.strftime("%d/%m/%Y")}) is earlier than {docking_source} + 36 months'
        
        logger.info(f"Next Docking chosen: {next_docking.strftime('%d/%m/%Y')} (Method: {calculation_method})")
        
        return {
            'next_docking': next_docking,
            'calculation_method': calculation_method,
            'reasoning': reasoning,
            'docking_source': docking_source,
            'reference_docking': reference_docking.strftime('%d/%m/%Y'),
            'docking_plus_36_months': docking_plus_36_months.strftime('%d/%m/%Y'),
            'special_survey_to_date': special_survey_to_date.strftime('%d/%m/%Y') if special_survey_to_date else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating next docking: {e}")
        return {
            'next_docking': None,
            'calculation_method': None,
            'reasoning': f'Error: {str(e)}'
        }




def calculate_survey_report_expiry(issued_date, ship_data: dict) -> dict:
    """
    Calculate expiry date and status for Survey Report.
    
    Logic (UPDATED v2):
    1. Find the Anniversary Date window for the issued year
       - Window Open = Anniversary - 3 months
       - Window Close = Anniversary + 3 months
    
    2. If issued_date is WITHIN the window (Anniversary ± 3 months):
       - Survey for that year is COMPLETED
       - Next survey = Anniversary of NEXT year + 3 months
    
    3. If issued_date is BEFORE window_open (< Anniversary - 3 months):
       - This survey belongs to PREVIOUS year's cycle
       - Survey for current year is NOT yet completed  
       - Next survey = Anniversary of CURRENT year + 3 months
    
    Example (Anniversary = 20 Dec):
    - Window 2025: 20/09/2025 → 20/03/2026
    - issued = 29/12/2025 (in window) → Survey 2025 done → Next = 20/12/2026 + 3M = 20/03/2027
    - issued = 01/06/2025 (before window) → Survey 2024 → Next = 20/12/2025 + 3M = 20/03/2026
    
    Args:
        issued_date: Survey Report issued date (str or datetime)
        ship_data: Ship data containing anniversary_date and special_survey_cycle
        
    Returns:
        dict with expiry_date, status, reasoning
    """
    try:
        current_date = datetime.now()
        
        # Parse issued_date
        issued_dt = parse_date(issued_date)
        if not issued_dt:
            logger.warning("No issued_date provided for survey report expiry calculation")
            return {
                'expiry_date': None,
                'status': 'Valid',
                'reasoning': 'No issued date - cannot calculate expiry'
            }
        
        # Calculate issued_date + 18 months
        issued_plus_18_months = issued_dt + relativedelta(months=18)
        logger.info(f"Survey Report issued: {issued_dt.strftime('%d/%m/%Y')}, +18 months = {issued_plus_18_months.strftime('%d/%m/%Y')}")
        
        # Get ship anniversary date
        ship_anniversary = ship_data.get('anniversary_date', {})
        
        # Determine anniversary day/month
        anniversary_day = None
        anniversary_month = None
        
        if isinstance(ship_anniversary, dict):
            anniversary_day = ship_anniversary.get('day')
            anniversary_month = ship_anniversary.get('month')
        
        # If no ship anniversary, use issued_date + 12 months as fallback
        if not anniversary_day or not anniversary_month:
            # Fallback: expiry = issued_date + 18 months
            logger.info(f"No ship anniversary date, using issued_date + 18 months as expiry")
            expiry_date = issued_plus_18_months
            
            days_until_expiry = (expiry_date - current_date).days
            if days_until_expiry < 0:
                status = 'Expired'
            elif days_until_expiry <= 30:
                status = 'Due Soon'
            else:
                status = 'Valid'
            
            return {
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'status': status,
                'reasoning': f'No anniversary date - using issued+18M={expiry_date.strftime("%d/%m/%Y")}',
                'days_until_expiry': days_until_expiry
            }
        
        # Calculate the Anniversary Date of the issued year
        try:
            anniversary_of_issued_year = datetime(issued_dt.year, anniversary_month, anniversary_day)
        except ValueError:
            # Handle invalid date (e.g., Feb 30)
            anniversary_of_issued_year = datetime(issued_dt.year, anniversary_month, min(anniversary_day, 28))
        
        # Calculate window boundaries for the issued year
        # Window Open = Anniversary - 3 months
        # Window Close = Anniversary + 3 months
        window_open = anniversary_of_issued_year - relativedelta(months=3)
        window_close = anniversary_of_issued_year + relativedelta(months=3)
        
        logger.info(f"Anniversary {issued_dt.year}: {anniversary_of_issued_year.strftime('%d/%m/%Y')}")
        logger.info(f"Window: {window_open.strftime('%d/%m/%Y')} → {window_close.strftime('%d/%m/%Y')}")
        
        # Determine which survey cycle this report belongs to
        if issued_dt >= window_open:
            # issued_date is WITHIN or AFTER the window
            # Survey for issued_year is COMPLETED
            # Next survey = Anniversary of NEXT year
            next_survey_year = issued_dt.year + 1
            logger.info(f"issued_date ({issued_dt.strftime('%d/%m/%Y')}) >= window_open ({window_open.strftime('%d/%m/%Y')}) → Survey {issued_dt.year} COMPLETED")
        else:
            # issued_date is BEFORE window_open
            # This survey belongs to PREVIOUS year's cycle
            # Survey for issued_year is NOT yet completed
            # Next survey = Anniversary of issued_year
            next_survey_year = issued_dt.year
            logger.info(f"issued_date ({issued_dt.strftime('%d/%m/%Y')}) < window_open ({window_open.strftime('%d/%m/%Y')}) → Survey {issued_dt.year} NOT YET, next survey is {issued_dt.year}")
        
        # Calculate next survey date
        try:
            next_survey_date = datetime(next_survey_year, anniversary_month, anniversary_day)
        except ValueError:
            next_survey_date = datetime(next_survey_year, anniversary_month, min(anniversary_day, 28))
        
        # Add 3 months window
        window_months = 3
        next_survey_window_close = next_survey_date + relativedelta(months=window_months)
        
        logger.info(f"Next Survey: {next_survey_date.strftime('%d/%m/%Y')}, window_close (+3M) = {next_survey_window_close.strftime('%d/%m/%Y')}")
        
        # Calculate expiry_date = MIN(issued + 18 months, next_survey_window_close)
        expiry_date = min(issued_plus_18_months, next_survey_window_close)
        
        logger.info(f"Expiry calculation: MIN({issued_plus_18_months.strftime('%d/%m/%Y')}, {next_survey_window_close.strftime('%d/%m/%Y')}) = {expiry_date.strftime('%d/%m/%Y')}")
        
        # Calculate status based on expiry_date
        days_until_expiry = (expiry_date - current_date).days
        
        if days_until_expiry < 0:
            status = 'Expired'
        elif days_until_expiry <= 30:
            status = 'Due Soon'
        else:
            status = 'Valid'
        
        logger.info(f"Survey Report status: {status} (days until expiry: {days_until_expiry})")
        
        return {
            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
            'status': status,
            'reasoning': f'MIN(issued+18M={issued_plus_18_months.strftime("%d/%m/%Y")}, next_survey={next_survey_date.strftime("%d/%m/%Y")}+3M={next_survey_window_close.strftime("%d/%m/%Y")})',
            'days_until_expiry': days_until_expiry
        }
        
    except Exception as e:
        logger.error(f"Error calculating survey report expiry: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'expiry_date': None,
            'status': 'Valid',
            'reasoning': f'Error in calculation: {str(e)}'
        }