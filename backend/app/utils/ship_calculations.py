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
    Typically 2.5 years from last docking
    """
    try:
        if not last_docking:
            logger.info(f"No last docking date provided for ship {ship_id}")
            return None
        
        if isinstance(last_docking, str):
            last_docking = datetime.fromisoformat(last_docking.replace('Z', '+00:00'))
        
        # Next docking is typically 2.5 years (30 months) from last docking
        next_docking = last_docking + relativedelta(months=30)
        
        logger.info(f"✅ Calculated next docking for ship {ship_id}: {next_docking}")
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
