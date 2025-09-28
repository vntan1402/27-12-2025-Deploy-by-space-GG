#!/usr/bin/env python3
import asyncio
import sys
import os
import json
from datetime import datetime, timezone

# Add backend to path
sys.path.append('/app/backend')

from mongodb_database import mongo_db

async def analyze_certificate_patterns():
    """Analyze certificate patterns to improve survey type determination"""
    
    try:
        # Connect to database
        await mongo_db.connect()
        
        # Get all certificates
        certificates = await mongo_db.find_all('certificates', {})
        print(f'📊 Total certificates found: {len(certificates)}')
        
        if not certificates:
            print("❌ No certificates found in database")
            return
        
        # Print detailed information about first few certificates to understand structure
        print(f"\n🔍 DETAILED CERTIFICATE STRUCTURE (First 3 certificates):")
        for i, cert in enumerate(certificates[:3]):
            print(f"\nCertificate {i+1}:")
            for key, value in cert.items():
                if key not in ['_id']:  # Skip MongoDB internal ID
                    print(f"   {key}: {value}")
            print("-" * 50)
        
        # Analyze certificate patterns
        patterns = {
            'cert_types': {},
            'survey_types': {},
            'certificate_names': {},
            'status_distribution': {},
            'date_patterns': [],
            'ships_with_multiple_certs': {}
        }
        
        # Group certificates by ship for pattern analysis
        ships_certs = {}
        
        for cert in certificates:
            # Certificate type analysis
            cert_type = cert.get('cert_type', 'Unknown')
            patterns['cert_types'][cert_type] = patterns['cert_types'].get(cert_type, 0) + 1
            
            # Survey type analysis
            survey_type = cert.get('next_survey_type', 'Unknown')
            patterns['survey_types'][survey_type] = patterns['survey_types'].get(survey_type, 0) + 1
            
            # Certificate name analysis (check both cert_name and certificate_name fields)
            cert_name = cert.get('cert_name') or cert.get('certificate_name', 'Unknown')
            if cert_name not in patterns['certificate_names']:
                patterns['certificate_names'][cert_name] = {
                    'count': 0,
                    'cert_types': set(),
                    'survey_types': set()
                }
            patterns['certificate_names'][cert_name]['count'] += 1
            patterns['certificate_names'][cert_name]['cert_types'].add(cert_type)
            patterns['certificate_names'][cert_name]['survey_types'].add(survey_type)
            
            # Status analysis
            status = cert.get('status', 'Unknown')
            patterns['status_distribution'][status] = patterns['status_distribution'].get(status, 0) + 1
            
            # Date pattern analysis
            issue_date = cert.get('issue_date')
            expiry_date = cert.get('expiry_date') 
            valid_date = cert.get('valid_date')
            
            if issue_date or expiry_date or valid_date:
                patterns['date_patterns'].append({
                    'cert_name': cert_name,
                    'cert_type': cert_type,
                    'issue_date': str(issue_date) if issue_date else None,
                    'expiry_date': str(expiry_date) if expiry_date else None,
                    'valid_date': str(valid_date) if valid_date else None,
                    'current_survey_type': survey_type
                })
            
            # Group by ship
            ship_id = cert.get('ship_id')
            if ship_id:
                if ship_id not in ships_certs:
                    ships_certs[ship_id] = []
                ships_certs[ship_id].append(cert)
        
        # Analyze ships with multiple certificates
        for ship_id, ship_certificates in ships_certs.items():
            if len(ship_certificates) > 1:
                patterns['ships_with_multiple_certs'][ship_id] = {
                    'cert_count': len(ship_certificates),
                    'cert_types': list(set([c.get('cert_type', 'Unknown') for c in ship_certificates])),
                    'survey_types': list(set([c.get('next_survey_type', 'Unknown') for c in ship_certificates if c.get('next_survey_type')]))
                }
        
        # Convert sets to lists for JSON serialization
        for name_data in patterns['certificate_names'].values():
            name_data['cert_types'] = list(name_data['cert_types'])
            name_data['survey_types'] = list(name_data['survey_types'])
        
        # Print analysis results
        print("\n🏷️  CERTIFICATE TYPES DISTRIBUTION:")
        for cert_type, count in sorted(patterns['cert_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {cert_type}: {count}")
        
        print("\n📅 SURVEY TYPES DISTRIBUTION:")
        for survey_type, count in sorted(patterns['survey_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {survey_type}: {count}")
        
        print("\n📋 TOP CERTIFICATE NAMES:")
        top_cert_names = sorted(patterns['certificate_names'].items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        for cert_name, data in top_cert_names:
            print(f"   {cert_name}: {data['count']} certificates")
            print(f"      Types: {', '.join(data['cert_types'])}")
            print(f"      Survey Types: {', '.join([st for st in data['survey_types'] if st != 'Unknown'])}")
        
        print("\n📊 STATUS DISTRIBUTION:")
        for status, count in sorted(patterns['status_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {status}: {count}")
        
        print(f"\n🚢 SHIPS WITH MULTIPLE CERTIFICATES: {len(patterns['ships_with_multiple_certs'])}")
        
        # Sample some ships with multiple certificates
        sample_ships = list(patterns['ships_with_multiple_certs'].items())[:5]
        for ship_id, data in sample_ships:
            print(f"   Ship {ship_id}: {data['cert_count']} certificates")
            print(f"      Types: {', '.join(data['cert_types'])}")
            print(f"      Survey Types: {', '.join(data['survey_types'])}")
        
        # Save detailed analysis to file
        with open('/app/certificate_patterns_analysis.json', 'w') as f:
            json.dump(patterns, f, indent=2, default=str)
        
        print(f"\n✅ Detailed analysis saved to /app/certificate_patterns_analysis.json")
        
        # Get sample certificates for specific analysis
        print(f"\n📋 SAMPLE CERTIFICATES WITH DATE INFORMATION:")
        sample_certs_with_dates = [cert for cert in patterns['date_patterns'][:10] if cert['issue_date'] or cert['expiry_date'] or cert['valid_date']]
        
        for cert in sample_certs_with_dates:
            print(f"   Certificate: {cert['cert_name']}")
            print(f"      Type: {cert['cert_type']}")
            print(f"      Issue Date: {cert['issue_date']}")
            print(f"      Expiry Date: {cert['expiry_date']}")
            print(f"      Valid Date: {cert['valid_date']}")
            print(f"      Current Survey Type: {cert['current_survey_type']}")
            print()
        
        return patterns
        
    except Exception as e:
        print(f"❌ Error analyzing certificates: {e}")
        return None
    finally:
        await mongo_db.disconnect()

if __name__ == "__main__":
    asyncio.run(analyze_certificate_patterns())