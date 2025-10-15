#!/usr/bin/env python3
"""
Simple test of the normalize_issued_by function
"""

import sys
import os
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_issued_by(extracted_data: dict) -> dict:
    """
    Normalize 'issued_by' field to standard maritime authority names
    
    Examples:
    - "the RERL Maritime Authority of the Republic of Panama" → "Panama Maritime Authority"
    - "Socialist Republic of Vietnam Maritime Administration" → "Vietnam Maritime Administration"
    - "The Government of Marshall Islands" → "Marshall Islands Maritime Administrator"
    """
    try:
        issued_by = extracted_data.get('issued_by', '').strip()
        
        if not issued_by:
            return extracted_data
        
        issued_by_upper = issued_by.upper()
        
        # Dictionary of maritime authorities with multiple variations
        MARITIME_AUTHORITIES = {
            'Panama Maritime Authority': [
                'PANAMA MARITIME AUTHORITY',
                'AUTORIDAD MARÍTIMA DE PANAMÁ',
                'AUTORIDAD MARITIMA DE PANAMA',
                'MARITIME AUTHORITY OF PANAMA',
                'REPUBLIC OF PANAMA MARITIME',
                'PANAMA MARITIME',
                'AMP PANAMA',
                'RERL MARITIME AUTHORITY OF THE REPUBLIC OF PANAMA'
            ],
            'Vietnam Maritime Administration': [
                'VIETNAM MARITIME ADMINISTRATION',
                'VIETNAM MARITIME',
                'SOCIALIST REPUBLIC OF VIETNAM MARITIME',
                'CỤC HÀNG HẢI VIỆT NAM',
                'DIRECTORATE OF VIETNAM MARITIME',
                'VIETNAMESE MARITIME ADMINISTRATION',
                'SOCIALIST REPUBLIC OF VIETNAM MARITIME ADMINISTRATION'
            ],
            'Marshall Islands Maritime Administrator': [
                'MARSHALL ISLANDS MARITIME',
                'MARSHALL ISLANDS ADMINISTRATOR',
                'REPUBLIC OF MARSHALL ISLANDS',
                'MARSHALL ISLANDS SHIPPING',
                'RMI MARITIME',
                'THE GOVERNMENT OF MARSHALL ISLANDS'
            ],
            'Liberia Maritime Authority': [
                'LIBERIA MARITIME AUTHORITY',
                'LIBERIAN MARITIME',
                'LIBERIA SHIPPING',
                'REPUBLIC OF LIBERIA MARITIME'
            ],
            'Philippines Coast Guard': [
                'PHILIPPINES COAST GUARD',
                'PHILIPPINE COAST GUARD',
                'PCG PHILIPPINES',
                'COAST GUARD PHILIPPINES'
            ],
            'Singapore Maritime and Port Authority': [
                'SINGAPORE MARITIME AND PORT AUTHORITY',
                'SINGAPORE MPA',
                'MPA SINGAPORE',
                'MARITIME AND PORT AUTHORITY OF SINGAPORE'
            ],
            'Hong Kong Marine Department': [
                'HONG KONG MARINE DEPARTMENT',
                'MARINE DEPARTMENT HONG KONG',
                'HKMD',
                'HONG KONG MARITIME'
            ],
            'United Kingdom Maritime and Coastguard Agency': [
                'UK MARITIME AND COASTGUARD AGENCY',
                'UNITED KINGDOM MARITIME',
                'UK MCA',
                'MARITIME AND COASTGUARD AGENCY',
                'BRITISH MARITIME'
            ],
            'United States Coast Guard': [
                'UNITED STATES COAST GUARD',
                'US COAST GUARD',
                'USCG',
                'U.S. COAST GUARD'
            ],
            'Japan Coast Guard': [
                'JAPAN COAST GUARD',
                'JAPANESE COAST GUARD',
                'JCG'
            ],
            'India Directorate General of Shipping': [
                'INDIA DIRECTORATE GENERAL OF SHIPPING',
                'DIRECTORATE GENERAL OF SHIPPING',
                'DG SHIPPING INDIA',
                'INDIA MARITIME'
            ],
            'China Maritime Safety Administration': [
                'CHINA MARITIME SAFETY ADMINISTRATION',
                'MSA CHINA',
                'CHINESE MARITIME',
                'PEOPLE\'S REPUBLIC OF CHINA MARITIME'
            ],
            'Indonesia Directorate General of Sea Transportation': [
                'INDONESIA DIRECTORATE',
                'INDONESIA MARITIME',
                'DIRECTORATE GENERAL OF SEA TRANSPORTATION'
            ],
            'Malaysia Marine Department': [
                'MALAYSIA MARINE DEPARTMENT',
                'MARINE DEPARTMENT MALAYSIA',
                'MALAYSIA MARITIME'
            ],
            'Thailand Marine Department': [
                'THAILAND MARINE DEPARTMENT',
                'MARINE DEPARTMENT THAILAND',
                'THAILAND MARITIME'
            ],
            'Norway Maritime Authority': [
                'NORWAY MARITIME AUTHORITY',
                'NORWEGIAN MARITIME AUTHORITY',
                'NORWAY MARITIME'
            ],
            'Greece Ministry of Maritime Affairs': [
                'GREECE MARITIME',
                'GREEK MARITIME',
                'MINISTRY OF MARITIME AFFAIRS AND INSULAR POLICY'
            ],
            'Cyprus Department of Merchant Shipping': [
                'CYPRUS SHIPPING',
                'CYPRUS MARITIME',
                'DEPARTMENT OF MERCHANT SHIPPING CYPRUS'
            ],
            'Malta Transport': [
                'MALTA TRANSPORT',
                'TRANSPORT MALTA',
                'MALTA MARITIME'
            ],
            'Bahamas Maritime Authority': [
                'BAHAMAS MARITIME AUTHORITY',
                'BAHAMAS MARITIME',
                'COMMONWEALTH OF BAHAMAS'
            ]
        }
        
        # Check for matches
        for standard_name, variations in MARITIME_AUTHORITIES.items():
            for variation in variations:
                if variation in issued_by_upper:
                    logger.info(f"✅ Normalized issued_by: '{issued_by}' → '{standard_name}'")
                    extracted_data['issued_by'] = standard_name
                    return extracted_data
        
        # If no match found, clean up common prefixes/suffixes
        cleaned = issued_by
        
        # Remove common unnecessary prefixes
        prefixes_to_remove = [
            'the ', 'The ', 'THE ',
            'of the ', 'Of the ', 'OF THE ',
            'Republic of ', 'REPUBLIC OF ',
            'Socialist Republic of ', 'SOCIALIST REPUBLIC OF ',
            'Government of ', 'GOVERNMENT OF '
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        
        # If cleaned version is different, log it
        if cleaned != issued_by:
            logger.info(f"ℹ️ Cleaned issued_by: '{issued_by}' → '{cleaned}'")
            extracted_data['issued_by'] = cleaned
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error normalizing issued_by: {e}")
        return extracted_data

def test_normalize_function():
    """Test the normalize_issued_by function directly"""
    
    print("🔍 Testing normalize_issued_by function directly...")
    
    # Test cases
    test_cases = [
        {
            "input": {"issued_by": "RERL Maritime Authority of the Republic of Panama"},
            "expected": "Panama Maritime Authority"
        },
        {
            "input": {"issued_by": "Socialist Republic of Vietnam Maritime Administration"},
            "expected": "Vietnam Maritime Administration"
        },
        {
            "input": {"issued_by": "The Government of Marshall Islands"},
            "expected": "Marshall Islands Maritime Administrator"
        },
        {
            "input": {"issued_by": "Panama Maritime Authority"},
            "expected": "Panama Maritime Authority"  # Should remain the same
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}:")
        print(f"   Input: {test_case['input']['issued_by']}")
        
        # Call the normalization function
        result = normalize_issued_by(test_case['input'].copy())
        
        print(f"   Output: {result.get('issued_by', 'NOT FOUND')}")
        print(f"   Expected: {test_case['expected']}")
        
        if result.get('issued_by') == test_case['expected']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
    
    print("\n🔍 Testing with empty/missing issued_by...")
    
    # Test with empty issued_by
    empty_test = normalize_issued_by({"issued_by": ""})
    print(f"   Empty string result: {empty_test}")
    
    # Test with missing issued_by
    missing_test = normalize_issued_by({})
    print(f"   Missing field result: {missing_test}")
    
    print("\n✅ Direct normalization function test completed")

if __name__ == "__main__":
    test_normalize_function()