"""
Survey Calculation Service
Migrated from backend-v1 for Next Survey calculations
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SurveyCalculationService:
    """Service for calculating Next Survey dates based on IMO regulations"""
    
    @staticmethod
    def _parse_date(date_value: Any) -> Optional[datetime]:
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
                    return datetime.fromisoformat(date_value[:-1]).replace(tzinfo=timezone.utc)
                return datetime.fromisoformat(date_value).replace(tzinfo=timezone.utc)
            except:
                pass
            
            # Try other formats
            from app.services.certificate_multi_upload_service import CertificateMultiUploadService
            date_str = CertificateMultiUploadService._parse_date_to_iso(date_value)
            if date_str:
                try:
                    return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                except:
                    pass
        
        return None
    
    @staticmethod
    def calculate_next_survey_info(certificate_data: dict, ship_data: dict) -> dict:
        """
        Calculate Next Survey and Next Survey Type based on IMO regulations
        
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
            current_date = datetime.now(timezone.utc)
            
            # Parse valid date
            valid_dt = SurveyCalculationService._parse_date(valid_date)
            
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
            
            if isinstance(special_survey_cycle, dict):
                cycle_from = special_survey_cycle.get('from_date')
                cycle_to = special_survey_cycle.get('to_date')
                
                if cycle_from and cycle_to:
                    cycle_start = SurveyCalculationService._parse_date(cycle_from)
                    cycle_end = SurveyCalculationService._parse_date(cycle_to)
            
            # If no special survey cycle, create one based on valid_date
            if not cycle_start or not cycle_end:
                if valid_dt:
                    # Assume certificate valid_date is part of current 5-year cycle
                    years_from_valid = (current_date.year - valid_dt.year)
                    if years_from_valid >= 0:
                        # If valid_date is in the past, it might be from previous cycle
                        cycle_start = datetime(valid_dt.year - (years_from_valid % 5), anniversary_month, anniversary_day, tzinfo=timezone.utc)
                        cycle_end = datetime(cycle_start.year + 5, anniversary_month, anniversary_day, tzinfo=timezone.utc)
                    else:
                        # Valid_date is in future
                        cycle_start = datetime(current_date.year, anniversary_month, anniversary_day, tzinfo=timezone.utc)
                        cycle_end = datetime(cycle_start.year + 5, anniversary_month, anniversary_day, tzinfo=timezone.utc)
            
            if not cycle_start or not cycle_end:
                return {
                    'next_survey': None,
                    'next_survey_type': None,
                    'reasoning': 'Cannot determine survey cycle'
                }
            
            # Generate Annual Survey dates for the 5-year cycle
            annual_surveys = []
            for i in range(1, 5):  # 1st, 2nd, 3rd, 4th Annual Survey
                survey_date = datetime(cycle_start.year + i, anniversary_month, anniversary_day, tzinfo=timezone.utc)
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
                next_annual_date = datetime(next_cycle_start.year + 1, anniversary_month, anniversary_day, tzinfo=timezone.utc)
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
                        last_intermediate_dt = SurveyCalculationService._parse_date(ship_last_intermediate)
                        if last_intermediate_dt and last_intermediate_dt < next_survey_date:
                            next_survey_type = '3rd Annual Survey'
                        else:
                            next_survey_type = 'Intermediate Survey'
                    else:
                        # No last intermediate info = intermediate survey needed
                        next_survey_type = 'Intermediate Survey'
            
            # Format next survey date with window
            next_survey_formatted = next_survey_date.strftime('%d/%m/%Y')
            
            # Add window information based on survey type
            # Special Survey: only -3M (must be done before deadline)
            # Other surveys: ±3M (can be done before or after within window)
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
