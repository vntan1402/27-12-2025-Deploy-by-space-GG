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
    Calculate anniversary date from Full Term Class/Statutory certificates
    Follows IMO maritime standards
    """
    try:
        # Get all certificates for the ship
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # Filter Full Term certificates with valid dates
        full_term_certs = [
            cert for cert in certificates
            if cert.get('cert_type') == 'Full Term' and cert.get('valid_date')
        ]
        
        if not full_term_certs:
            logger.info(f"No Full Term certificates found for ship {ship_id}")
            return None
        
        # Sort by valid_date to get the certificate with latest expiry
        full_term_certs.sort(key=lambda x: x.get('valid_date'), reverse=True)
        source_cert = full_term_certs[0]
        
        # Extract day and month from valid_date
        valid_date = source_cert.get('valid_date')
        if isinstance(valid_date, str):
            valid_date = datetime.fromisoformat(valid_date.replace('Z', '+00:00'))
        
        anniversary = AnniversaryDate(
            day=valid_date.day,
            month=valid_date.month,
            auto_calculated=True,
            source_certificate_type=source_cert.get('cert_name', 'Unknown'),
            manual_override=False
        )
        
        logger.info(f"✅ Calculated anniversary date for ship {ship_id}: {anniversary.day}/{anniversary.month}")
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
        valid_date = certificate_data.get('valid_date')
        current_date = datetime.now()
        
        # Parse valid date
        valid_dt = parse_date(valid_date)
        
        # Rule 4: No valid date = no Next Survey
        if not valid_dt:
            return {
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': 'No valid date available'
            }
        
        # Rule 2: Condition certificates = valid_date
        if 'CONDITION' in cert_type:
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y'),
                'next_survey_type': 'Condition Certificate Expiry',
                'reasoning': 'Condition certificate uses valid date as next survey',
                'raw_date': valid_dt.strftime('%d/%m/%Y'),
                'window_months': 0
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
                    'next_survey': None,
                    'next_survey_type': None,
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
                'next_survey': None,
                'next_survey_type': None,
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
        
        # Find next survey in the future
        future_surveys = [survey for survey in annual_surveys if survey['date'] > current_date]
        
        if not future_surveys:
            # If no future surveys in current cycle, start next cycle
            next_cycle_start = cycle_end
            next_annual_date = datetime(next_cycle_start.year + 1, anniversary_month, anniversary_day)
            future_surveys = [{
                'date': next_annual_date,
                'type': '1st Annual Survey',
                'number': 1
            }]
        
        # Get the nearest future survey
        next_survey_info = min(future_surveys, key=lambda x: x['date'])
        next_survey_date = next_survey_info['date']
        next_survey_type = next_survey_info['type']
        
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
        
        # Format next survey date with window
        next_survey_formatted = next_survey_date.strftime('%d/%m/%Y')
        
        # Add window information
        if next_survey_type == 'Special Survey':
            window_text_en = f'-{window_months}M'
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
            'next_survey': None,
            'next_survey_type': None,
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
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': 'No valid date available'
            }
        
        # Rule 4: Special documents (DMLC I, DMLC II, SSP) = N/A
        special_docs = ['DMLC I', 'DMLC II', 'DMLC PART I', 'DMLC PART II', 'SSP', 'SHIP SECURITY PLAN']
        if any(doc in cert_name for doc in special_docs):
            return {
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': f'{cert_name} does not require Next Survey calculation'
            }
        
        # Rule 2: Short Term = N/A
        if 'SHORT' in cert_type or 'SHORT TERM' in cert_type:
            return {
                'next_survey': None,
                'next_survey_type': None,
                'reasoning': 'Short Term certificates do not require Next Survey'
            }
        
        # Rule 1: Interim = Valid Date - 3M, Type = "Initial"
        if 'INTERIM' in cert_type:
            next_survey_date = valid_dt - relativedelta(months=3)
            return {
                'next_survey': valid_dt.strftime('%d/%m/%Y') + ' (-3M)',
                'next_survey_type': 'Initial',
                'reasoning': 'Interim certificate: Next Survey = Valid Date - 3 months',
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
                intermediate_date = valid_dt - relativedelta(years=2)
                return {
                    'next_survey': intermediate_date.strftime('%d/%m/%Y') + ' (±3M)',
                    'next_survey_type': 'Intermediate',
                    'reasoning': 'Full Term without Last Endorse: Next Survey = Valid Date - 2 years (Intermediate)',
                    'raw_date': intermediate_date.strftime('%d/%m/%Y'),
                    'window_months': 3
                }
        
        # Default: Cannot determine
        return {
            'next_survey': None,
            'next_survey_type': None,
            'reasoning': f'Cannot determine Next Survey for cert_type: {cert_type}'
        }
        
    except Exception as e:
        logger.error(f"Error calculating audit certificate next survey: {e}")
        return {
            'next_survey': None,
            'next_survey_type': None,
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
