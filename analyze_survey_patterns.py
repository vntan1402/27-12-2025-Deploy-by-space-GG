#!/usr/bin/env python3
import asyncio
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Add backend to path
sys.path.append('/app/backend')

from mongodb_database import mongo_db

async def analyze_survey_patterns():
    """Analyze patterns for enhanced survey type determination"""
    
    try:
        # Connect to database
        await mongo_db.connect()
        
        # Get all certificates and ships
        certificates = await mongo_db.find_all('certificates', {})
        ships = await mongo_db.find_all('ships', {})
        print(f'📊 Found {len(certificates)} certificates and {len(ships)} ships')
        
        # Create ship lookup dictionary
        ships_dict = {ship['id']: ship for ship in ships}
        
        # Analyze survey patterns
        survey_patterns = {
            'by_certificate_type': defaultdict(list),
            'by_cert_validity_period': defaultdict(list),
            'by_ship_age': defaultdict(list),
            'certificate_lifecycle_patterns': defaultdict(list),
            'renewal_patterns': [],
            'special_survey_indicators': [],
            'intermediate_survey_indicators': []
        }
        
        current_date = datetime.now()
        
        # Analyze each certificates
        for cert in certificates:
            cert_name = cert.get('cert_name', 'Unknown')
            cert_type = cert.get('cert_type', 'Unknown')
            ship_id = cert.get('ship_id')
            issue_date = cert.get('issue_date')
            valid_date = cert.get('valid_date')
            current_survey_type = cert.get('next_survey_type', 'Unknown')
            
            # Get ship data
            ship_data = ships_dict.get(ship_id, {}) if ship_id else {}
            built_year = ship_data.get('built_year')
            ship_age = current_date.year - built_year if built_year else None
            last_special_survey = ship_data.get('last_special_survey')
            last_docking = ship_data.get('last_docking')
            
            # Parse dates
            issue_dt = None
            valid_dt = None
            if issue_date:
                issue_dt = issue_date if isinstance(issue_date, datetime) else datetime.fromisoformat(str(issue_date).replace('Z', '+00:00'))
            if valid_date:
                valid_dt = valid_date if isinstance(valid_date, datetime) else datetime.fromisoformat(str(valid_date).replace('Z', '+00:00'))
                
            cert_analysis = {
                'cert_name': cert_name,
                'cert_type': cert_type,
                'current_survey_type': current_survey_type,
                'issue_date': issue_dt,
                'valid_date': valid_dt,
                'ship_age': ship_age,
                'validity_period_months': None,
                'cert_age_months': None,
                'time_to_expiry_months': None,
                'ship_id': ship_id,
                'ship_name': ship_data.get('name', 'Unknown')
            }
            
            # Calculate time periods
            if issue_dt and valid_dt:
                cert_analysis['validity_period_months'] = (valid_dt - issue_dt).days / 30.44
                cert_analysis['cert_age_months'] = (current_date - issue_dt).days / 30.44
                cert_analysis['time_to_expiry_months'] = (valid_dt - current_date).days / 30.44
            
            # Categorize by certificate type
            survey_patterns['by_certificate_type'][cert_name].append(cert_analysis)
            
            # Categorize by validity period
            if cert_analysis['validity_period_months']:
                if cert_analysis['validity_period_months'] <= 12:
                    period_category = '0-12 months'
                elif cert_analysis['validity_period_months'] <= 36:
                    period_category = '12-36 months'
                elif cert_analysis['validity_period_months'] <= 60:
                    period_category = '36-60 months'
                else:
                    period_category = '60+ months'
                
                survey_patterns['by_cert_validity_period'][period_category].append(cert_analysis)
            
            # Categorize by ship age
            if ship_age:
                if ship_age <= 5:
                    age_category = '0-5 years'
                elif ship_age <= 15:
                    age_category = '5-15 years'
                elif ship_age <= 25:
                    age_category = '15-25 years'
                else:
                    age_category = '25+ years'
                
                survey_patterns['by_ship_age'][age_category].append(cert_analysis)
            
            # Identify potential special survey indicators
            if (cert_analysis['validity_period_months'] and 
                cert_analysis['validity_period_months'] >= 48 and 
                cert_type == 'Full Term'):
                survey_patterns['special_survey_indicators'].append(cert_analysis)
            
            # Identify potential intermediate survey indicators  
            if (cert_analysis['cert_age_months'] and 
                18 <= cert_analysis['cert_age_months'] <= 42 and
                cert_type == 'Full Term'):
                survey_patterns['intermediate_survey_indicators'].append(cert_analysis)
            
            # Identify renewal patterns
            if cert_analysis['time_to_expiry_months'] and cert_analysis['time_to_expiry_months'] <= 6:
                survey_patterns['renewal_patterns'].append(cert_analysis)
        
        # Print analysis results
        print("\n🏷️  CERTIFICATE TYPE PATTERNS:")
        for cert_name, analyses in list(survey_patterns['by_certificate_type'].items())[:10]:
            print(f"\n   {cert_name} ({len(analyses)} certificates):")
            
            # Analyze survey type patterns for this certificate
            survey_types = [a['current_survey_type'] for a in analyses]
            cert_types = [a['cert_type'] for a in analyses]
            validity_periods = [a['validity_period_months'] for a in analyses if a['validity_period_months']]
            
            print(f"      Survey Types: {dict(zip(*np.unique(survey_types, return_counts=True)))}")
            print(f"      Cert Types: {dict(zip(*np.unique(cert_types, return_counts=True)))}")
            if validity_periods:
                print(f"      Avg Validity: {sum(validity_periods)/len(validity_periods):.1f} months")
        
        print(f"\n📅 VALIDITY PERIOD PATTERNS:")
        for period, analyses in survey_patterns['by_cert_validity_period'].items():
            print(f"   {period}: {len(analyses)} certificates")
            survey_types = [a['current_survey_type'] for a in analyses]
            survey_type_counts = {}
            for st in survey_types:
                survey_type_counts[st] = survey_type_counts.get(st, 0) + 1
            print(f"      Survey Types: {survey_type_counts}")
        
        print(f"\n🚢 SHIP AGE PATTERNS:")
        for age_cat, analyses in survey_patterns['by_ship_age'].items():
            print(f"   {age_cat}: {len(analyses)} certificates")
            survey_types = [a['current_survey_type'] for a in analyses]
            survey_type_counts = {}
            for st in survey_types:
                survey_type_counts[st] = survey_type_counts.get(st, 0) + 1
            print(f"      Survey Types: {survey_type_counts}")
        
        print(f"\n⚡ SPECIAL SURVEY INDICATORS: {len(survey_patterns['special_survey_indicators'])}")
        if survey_patterns['special_survey_indicators']:
            for indicator in survey_patterns['special_survey_indicators'][:3]:
                print(f"   - {indicator['cert_name']} ({indicator['cert_type']})")
                print(f"     Validity: {indicator['validity_period_months']:.1f} months, Current: {indicator['current_survey_type']}")
        
        print(f"\n🔄 INTERMEDIATE SURVEY INDICATORS: {len(survey_patterns['intermediate_survey_indicators'])}")
        if survey_patterns['intermediate_survey_indicators']:
            for indicator in survey_patterns['intermediate_survey_indicators'][:3]:
                print(f"   - {indicator['cert_name']} ({indicator['cert_type']})")
                print(f"     Age: {indicator['cert_age_months']:.1f} months, Current: {indicator['current_survey_type']}")
        
        print(f"\n🔄 RENEWAL PATTERNS: {len(survey_patterns['renewal_patterns'])}")
        if survey_patterns['renewal_patterns']:
            for renewal in survey_patterns['renewal_patterns'][:3]:
                print(f"   - {renewal['cert_name']} ({renewal['cert_type']})")
                print(f"     Expires in: {renewal['time_to_expiry_months']:.1f} months, Current: {renewal['current_survey_type']}")
        
        # Save detailed analysis
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Convert defaultdict to regular dict and serialize datetime objects
        serializable_patterns = {}
        for key, value in survey_patterns.items():
            if isinstance(value, defaultdict):
                serializable_patterns[key] = dict(value)
            else:
                serializable_patterns[key] = value
        
        with open('/app/survey_patterns_analysis.json', 'w') as f:
            json.dump(serializable_patterns, f, indent=2, default=serialize_datetime)
        
        print(f"\n✅ Detailed survey patterns saved to /app/survey_patterns_analysis.json")
        
        return survey_patterns
        
    except Exception as e:
        print(f"❌ Error analyzing survey patterns: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await mongo_db.disconnect()

# Simple alternative to numpy.unique for counting
def count_unique(items):
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts

# Override numpy usage
import builtins
class SimpleNumpy:
    @staticmethod
    def unique(arr, return_counts=False):
        unique_items = list(set(arr))
        if return_counts:
            counts = [arr.count(item) for item in unique_items]
            return unique_items, counts
        return unique_items

builtins.np = SimpleNumpy()

if __name__ == "__main__":
    asyncio.run(analyze_survey_patterns())