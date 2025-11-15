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
    Follows IMO 5-year cycle standards
    """
    try:
        certificates = await CertificateRepository.find_all(ship_id=ship_id)
        
        # Filter Full Term Class certificates
        class_certs = [
            cert for cert in certificates
            if cert.get('cert_type') == 'Full Term' 
            and 'CLASS' in cert.get('cert_name', '').upper()
            and cert.get('issue_date') and cert.get('valid_date')
        ]
        
        if not class_certs:
            logger.info(f"No Full Term Class certificates found for ship {ship_id}")
            return None
        
        # Get the latest certificate
        class_certs.sort(key=lambda x: x.get('valid_date'), reverse=True)
        source_cert = class_certs[0]
        
        # Parse dates
        issue_date = source_cert.get('issue_date')
        valid_date = source_cert.get('valid_date')
        
        if isinstance(issue_date, str):
            issue_date = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
        if isinstance(valid_date, str):
            valid_date = datetime.fromisoformat(valid_date.replace('Z', '+00:00'))
        
        # Special Survey cycle is typically 5 years
        cycle = SpecialSurveyCycle(
            from_date=issue_date,
            to_date=valid_date,
            intermediate_required=True,
            cycle_type=source_cert.get('cert_name', 'Class Certificate')
        )
        
        logger.info(f"✅ Calculated Special Survey cycle for ship {ship_id}")
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
