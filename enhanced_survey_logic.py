#!/usr/bin/env python3
"""
Enhanced Survey Type Determination Logic
Based on analysis of certificate patterns and maritime regulatory requirements
"""
import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Add backend to path
sys.path.append('/app/backend')

from mongodb_database import mongo_db

def parse_date_string(date_str):
    """Helper function to parse date strings"""
    if not date_str:
        return None
    if isinstance(date_str, datetime):
        return date_str
    try:
        return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
    except:
        return None

class EnhancedSurveyTypeDetermination:
    """Enhanced survey type determination based on ship's complete certificate portfolio"""
    
    def __init__(self):
        self.current_date = datetime.now()
        
        # Define certificate priority classes (higher priority certificates drive survey types)
        self.high_priority_certificates = {
            'CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE': 'SOLAS_CLASS',
            'CLASSIFICATION CERTIFICATE': 'CLASS',
            'SAFETY CONSTRUCTION CERTIFICATE': 'SOLAS_CLASS',
            'INTERNATIONAL LOAD LINE CERTIFICATE': 'LOAD_LINE',
            'ISM CERTIFICATE': 'ISM',
            'DOCUMENT OF COMPLIANCE': 'ISM',
            'ISPS CERTIFICATE': 'ISPS',
            'MARITIME LABOUR CERTIFICATE': 'MLC'
        }
        
        # Define survey cycles by certificate category
        self.survey_cycles = {
            'SOLAS_CLASS': {
                'full_cycle_years': 5,
                'intermediate_years': 2.5,
                'annual_required': True,
                'special_survey_required': True
            },
            'CLASS': {
                'full_cycle_years': 5,
                'intermediate_years': 2.5,
                'annual_required': True,
                'special_survey_required': True
            },
            'LOAD_LINE': {
                'full_cycle_years': 5,
                'intermediate_years': 2.5,
                'annual_required': True,
                'special_survey_required': False
            },
            'ISM': {
                'full_cycle_years': 5,
                'intermediate_years': 2.5,
                'annual_required': True,
                'special_survey_required': False
            },
            'ISPS': {
                'full_cycle_years': 5,
                'intermediate_years': 2.5,
                'annual_required': True,
                'special_survey_required': False
            },
            'MLC': {
                'full_cycle_years': 3,
                'intermediate_years': 1.5,
                'annual_required': False,
                'special_survey_required': False
            }
        }

    def categorize_certificate(self, cert_name: str) -> str:
        """Categorize certificate into regulatory category"""
        cert_name_upper = cert_name.upper()
        
        for cert_key, category in self.high_priority_certificates.items():
            if cert_key in cert_name_upper:
                return category
                
        # Additional pattern matching
        if any(keyword in cert_name_upper for keyword in ['SAFETY', 'CONSTRUCTION', 'SOLAS']):
            return 'SOLAS_CLASS'
        elif any(keyword in cert_name_upper for keyword in ['CLASS', 'CLASSIFICATION']):
            return 'CLASS'
        elif any(keyword in cert_name_upper for keyword in ['LOAD LINE', 'LOADLINE']):
            return 'LOAD_LINE'
        elif any(keyword in cert_name_upper for keyword in ['ISM', 'SAFETY MANAGEMENT']):
            return 'ISM'
        elif any(keyword in cert_name_upper for keyword in ['ISPS', 'SECURITY']):
            return 'ISPS'
        elif any(keyword in cert_name_upper for keyword in ['MLC', 'LABOUR', 'MARITIME LABOUR']):
            return 'MLC'
        elif any(keyword in cert_name_upper for keyword in ['RADIO', 'GMDSS']):
            return 'RADIO'
        elif any(keyword in cert_name_upper for keyword in ['POLLUTION', 'MARPOL']):
            return 'POLLUTION'
        else:
            return 'OTHER'

    def analyze_ship_certificates(self, ship_certificates: List[Dict]) -> Dict:
        """Analyze all certificates for a ship to understand the survey landscape"""
        
        analysis = {
            'full_term_certificates': [],
            'interim_certificates': [],
            'certificate_categories': defaultdict(list),
            'renewal_timeline': [],
            'survey_indicators': {
                'special_survey_due': False,
                'intermediate_survey_due': False,
                'annual_survey_due': False,
                'renewal_required': False
            }
        }
        
        for cert in ship_certificates:
            cert_name = cert.get('cert_name', 'Unknown')
            cert_type = cert.get('cert_type', 'Unknown')
            issue_date = parse_date_string(cert.get('issue_date'))
            valid_date = parse_date_string(cert.get('valid_date'))
            
            # Categorize certificate
            category = self.categorize_certificate(cert_name)
            cert_analysis = {
                'cert': cert,
                'category': category,
                'cert_name': cert_name,
                'cert_type': cert_type,
                'issue_date': issue_date,
                'valid_date': valid_date,
                'cert_age_months': None,
                'time_to_expiry_months': None,
                'validity_period_months': None
            }
            
            # Calculate time periods
            if issue_date:
                cert_analysis['cert_age_months'] = (self.current_date - issue_date).days / 30.44
            if valid_date:
                cert_analysis['time_to_expiry_months'] = (valid_date - self.current_date).days / 30.44
            if issue_date and valid_date:
                cert_analysis['validity_period_months'] = (valid_date - issue_date).days / 30.44
            
            # Categorize by type
            if cert_type == 'Full Term':
                analysis['full_term_certificates'].append(cert_analysis)
            elif cert_type == 'Interim':
                analysis['interim_certificates'].append(cert_analysis)
            
            # Categorize by regulatory category
            analysis['certificate_categories'][category].append(cert_analysis)
            
            # Check for renewal requirements
            if cert_analysis['time_to_expiry_months'] and cert_analysis['time_to_expiry_months'] <= 6:
                analysis['renewal_timeline'].append(cert_analysis)
        
        # Analyze survey indicators based on full term certificates
        self._analyze_survey_indicators(analysis)
        
        return analysis

    def _analyze_survey_indicators(self, analysis: Dict):
        """Analyze survey indicators based on certificate portfolio"""
        
        # Focus on Full Term certificates for major survey determination
        full_term_certs = analysis['full_term_certificates']
        
        for cert_analysis in full_term_certs:
            category = cert_analysis['category']
            cert_age_months = cert_analysis['cert_age_months']
            validity_period_months = cert_analysis['validity_period_months']
            time_to_expiry_months = cert_analysis['time_to_expiry_months']
            
            if category in self.survey_cycles:
                cycle_info = self.survey_cycles[category]
                
                # Special Survey indicators
                if (validity_period_months and validity_period_months >= 48 and
                    cycle_info.get('special_survey_required', False)):
                    analysis['survey_indicators']['special_survey_due'] = True
                
                # Intermediate Survey indicators
                if (cert_age_months and 
                    18 <= cert_age_months <= 42 and
                    cycle_info.get('intermediate_years')):
                    analysis['survey_indicators']['intermediate_survey_due'] = True
                
                # Annual Survey indicators
                if (cert_age_months and cert_age_months >= 10 and
                    cycle_info.get('annual_required', False)):
                    analysis['survey_indicators']['annual_survey_due'] = True
                
                # Renewal indicators
                if time_to_expiry_months and time_to_expiry_months <= 6:
                    analysis['survey_indicators']['renewal_required'] = True

    def determine_survey_type_enhanced(self, certificate_data: Dict, ship_certificates: List[Dict], ship_data: Dict) -> Tuple[str, str]:
        """
        Enhanced survey type determination considering ship's complete certificate portfolio
        
        Returns:
            Tuple[survey_type, reasoning]
        """
        
        # Analyze the ship's complete certificate portfolio
        ship_analysis = self.analyze_ship_certificates(ship_certificates)
        
        # Get current certificate details
        current_cert_name = certificate_data.get('cert_name', 'Unknown')
        current_cert_type = certificate_data.get('cert_type', 'Unknown')
        current_issue_date = parse_date_string(certificate_data.get('issue_date'))
        current_valid_date = parse_date_string(certificate_data.get('valid_date'))
        
        # Calculate current certificate time periods
        current_cert_age_months = None
        current_time_to_expiry_months = None
        current_validity_period_months = None
        
        if current_issue_date:
            current_cert_age_months = (self.current_date - current_issue_date).days / 30.44
        if current_valid_date:
            current_time_to_expiry_months = (current_valid_date - self.current_date).days / 30.44
        if current_issue_date and current_valid_date:
            current_validity_period_months = (current_valid_date - current_issue_date).days / 30.44
        
        # Categorize current certificate
        current_category = self.categorize_certificate(current_cert_name)
        
        # Ship context
        ship_age = None
        built_year = ship_data.get('built_year') or ship_data.get('year_built')
        if built_year:
            ship_age = self.current_date.year - built_year
        
        # Decision logic based on enhanced analysis
        
        # 1. RENEWAL SURVEY: If certificate is expiring soon or expired
        if current_time_to_expiry_months and current_time_to_expiry_months <= 3:
            if ship_analysis['survey_indicators']['renewal_required']:
                return "Renewal", f"Certificate expires in {current_time_to_expiry_months:.1f} months, portfolio analysis indicates renewal cycle"
            else:
                return "Renewal", f"Certificate expires in {current_time_to_expiry_months:.1f} months"
        
        # 2. INITIAL SURVEY: For new ships or very new certificates
        if ship_age and ship_age < 1:
            return "Initial", f"New ship ({ship_age:.1f} years old) requires initial survey"
        
        if current_cert_age_months and current_cert_age_months < 3:
            return "Initial", f"Recently issued certificate ({current_cert_age_months:.1f} months old)"
        
        # 3. SPECIAL SURVEY: For Full Term certificates with long validity periods
        if (current_cert_type == 'Full Term' and 
            current_validity_period_months and current_validity_period_months >= 48 and
            current_category in ['SOLAS_CLASS', 'CLASS'] and
            ship_analysis['survey_indicators']['special_survey_due']):
            return "Special", f"Full Term {current_category} certificate with {current_validity_period_months:.1f} month validity requires special survey"
        
        # 4. INTERMEDIATE SURVEY: For mid-cycle certificates
        if (current_cert_age_months and 18 <= current_cert_age_months <= 42 and
            current_cert_type == 'Full Term' and
            ship_analysis['survey_indicators']['intermediate_survey_due']):
            return "Intermediate", f"Mid-cycle certificate ({current_cert_age_months:.1f} months old) in intermediate survey period"
        
        # 5. ANNUAL SURVEY: For regular maintenance
        if (current_cert_age_months and current_cert_age_months >= 10 and
            ship_analysis['survey_indicators']['annual_survey_due']):
            return "Annual", f"Certificate age ({current_cert_age_months:.1f} months) indicates annual survey required"
        
        # 6. ADDITIONAL SURVEY: For interim certificates or special circumstances
        if current_cert_type == 'Interim':
            return "Additional", f"Interim certificate typically requires additional survey"
        
        # 7. Default based on certificate category and ship context
        if current_category in ['SOLAS_CLASS', 'CLASS']:
            if current_cert_age_months and current_cert_age_months < 12:
                return "Annual", f"Recent {current_category} certificate, annual survey appropriate"
            else:
                return "Intermediate", f"{current_category} certificate, intermediate survey appropriate"
        elif current_category in ['ISM', 'ISPS']:
            return "Annual", f"{current_category} certificate requires annual audit"
        elif current_category == 'MLC':
            return "Intermediate", f"MLC certificate requires intermediate inspection"
        else:
            return "Annual", f"Standard annual survey for {current_category} certificate"

async def test_enhanced_logic():
    """Test the enhanced survey logic against existing certificates"""
    
    try:
        # Connect to database
        await mongo_db.connect()
        
        # Get all certificates and ships
        certificates = await mongo_db.find_all('certificates', {})
        ships = await mongo_db.find_all('ships', {})
        
        # Create ship lookup
        ships_dict = {ship['id']: ship for ship in ships}
        
        # Group certificates by ship
        ship_certificates = defaultdict(list)
        for cert in certificates:
            ship_id = cert.get('ship_id')
            if ship_id:
                ship_certificates[ship_id].append(cert)
        
        # Initialize enhanced logic
        enhanced_logic = EnhancedSurveyTypeDetermination()
        
        print("🔬 TESTING ENHANCED SURVEY LOGIC")
        print("=" * 60)
        
        results = []
        
        # Test each certificate
        for cert in certificates[:10]:  # Test first 10 certificates
            ship_id = cert.get('ship_id')
            ship_data = ships_dict.get(ship_id, {}) if ship_id else {}
            ship_certs = ship_certificates.get(ship_id, [])
            
            # Get current survey type
            current_survey_type = cert.get('next_survey_type', 'Unknown')
            
            # Apply enhanced logic
            enhanced_survey_type, reasoning = enhanced_logic.determine_survey_type_enhanced(
                cert, ship_certs, ship_data
            )
            
            # Compare results
            result = {
                'cert_name': cert.get('cert_name', 'Unknown'),
                'cert_type': cert.get('cert_type', 'Unknown'),
                'ship_name': ship_data.get('name', 'Unknown'),
                'current_survey_type': current_survey_type,
                'enhanced_survey_type': enhanced_survey_type,
                'reasoning': reasoning,
                'changed': current_survey_type != enhanced_survey_type
            }
            results.append(result)
            
            print(f"\n📋 Certificate: {result['cert_name']}")
            print(f"   Ship: {result['ship_name']}")
            print(f"   Type: {result['cert_type']}")
            print(f"   Current: {result['current_survey_type']}")
            print(f"   Enhanced: {result['enhanced_survey_type']}")
            print(f"   Reasoning: {result['reasoning']}")
            if result['changed']:
                print(f"   ✨ CHANGED: {result['current_survey_type']} → {result['enhanced_survey_type']}")
        
        # Summary statistics
        total_tests = len(results)
        changed_count = sum(1 for r in results if r['changed'])
        
        print(f"\n📊 ENHANCEMENT SUMMARY")
        print(f"   Total certificates tested: {total_tests}")
        print(f"   Survey types changed: {changed_count}")
        print(f"   Improvement rate: {(changed_count/total_tests)*100:.1f}%")
        
        # Group changes by type
        changes_by_type = defaultdict(list)
        for result in results:
            if result['changed']:
                change_key = f"{result['current_survey_type']} → {result['enhanced_survey_type']}"
                changes_by_type[change_key].append(result)
        
        print(f"\n🔄 CHANGES BY TYPE:")
        for change_type, change_results in changes_by_type.items():
            print(f"   {change_type}: {len(change_results)} certificates")
            for change_result in change_results[:2]:  # Show first 2 examples
                print(f"      - {change_result['cert_name']} ({change_result['cert_type']})")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing enhanced logic: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_enhanced_logic())