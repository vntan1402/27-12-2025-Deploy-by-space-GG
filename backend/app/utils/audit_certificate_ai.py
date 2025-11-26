"""
Audit Certificate AI Extraction Utilities
Handles AI-powered field extraction from audit certificates (ISM/ISPS/MLC/CICA)
Based on Backend V1 analyze_document_with_ai and Audit Report AI pattern
"""
import logging
import json
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# ⭐ EXPANDED: Certificate categories (ISM/ISPS/MLC/CICA)
AUDIT_CERTIFICATE_CATEGORIES = {
    "ism": [
        "SAFETY MANAGEMENT CERTIFICATE",
        "INTERIM SAFETY MANAGEMENT CERTIFICATE",
        "SMC",
        "DOCUMENT OF COMPLIANCE",
        "INTERIM DOCUMENT OF COMPLIANCE",
        "DOC",
    ],
    "isps": [
        "INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "INTERIM INTERNATIONAL SHIP SECURITY CERTIFICATE",
        "ISSC",
        "SHIP SECURITY PLAN",
        "SSP",
    ],
    "mlc": [
        "MARITIME LABOUR CERTIFICATE",
        "INTERIM MARITIME LABOUR CERTIFICATE",
        "MLC",
        "DECLARATION OF MARITIME LABOUR COMPLIANCE",
        "DMLC",
        "DMLC PART I",
        "DMLC PART II",
    ],
    # ⭐ NEW: CICA (Crew Accommodation)
    "cica": [
        "CERTIFICATE OF INSPECTION",
        "CREW ACCOMMODATION CERTIFICATE",
        "STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CERTIFICATE OF INSPECTION / STATEMENT OF COMPLIANCE OF CREW ACCOMMODATION",
        "CREW ACCOMMODATION INSPECTION",
        "CICA",
    ]
}

# Valid certificate types
VALID_CERTIFICATE_TYPES = [
    "Full Term",
    "Interim",
    "Provisional",
    "Short term",
    "Conditional",
    "Other"
]


async def extract_audit_certificate_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract audit certificate fields from Document AI summary using System AI
    
    Based on:
    - Backend V1: analyze_document_with_ai() lines 16143-16400
    - Audit Report: extract_audit_report_fields_from_summary()
    
    Fields to extract:
    - cert_name: Certificate name (REQUIRED)
    - cert_abbreviation: Abbreviation
    - cert_no: Certificate number (REQUIRED)
    - cert_type: Full Term, Interim, Provisional, etc.
    - issue_date: Issue date (YYYY-MM-DD)
    - valid_date: Expiry date (YYYY-MM-DD)
    - last_endorse: Last endorsement date
    - next_survey: Next survey date
    - next_survey_type: Initial, Intermediate, Renewal
    - issued_by: Organization that issued certificate
    - issued_by_abbreviation: Organization abbreviation
    - ship_name: Ship name
    - imo_number: IMO number (7 digits)
    - confidence_score: AI confidence
    
    Args:
        summary_text: Enhanced Document AI summary (with OCR)
        filename: Original filename (helps identify certificate type)
        ai_config: AI configuration dict with:
            - provider: "google", "emergent", etc.
            - model: Model name (e.g., "gemini-2.0-flash")
            - use_emergent_key: Whether to use Emergent LLM key
    
    Returns:
        dict: Extracted fields with post-processing applied
    """
    try:
        logger.info("🤖 Extracting audit certificate fields from summary")
        
        # Get AI config
        ai_provider = ai_config.get("provider", "google")
        ai_model = ai_config.get("model", "gemini-2.0-flash")
        use_emergent_key = ai_config.get("use_emergent_key", True)
        
        # Create extraction prompt
        prompt = create_audit_certificate_extraction_prompt(summary_text, filename)
        
        if not prompt:
            logger.error("Failed to create audit certificate extraction prompt")
            return {}
        
        # Use System AI for extraction
        if use_emergent_key and ai_provider in ["google", "emergent"]:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                from app.core.config import settings
                
                # Get Emergent LLM key
                emergent_key = settings.EMERGENT_LLM_KEY
                if not emergent_key:
                    logger.error("Emergent LLM key not configured")
                    return {}
                
                chat = LlmChat(
                    api_key=emergent_key,
                    session_id=f"cert_extraction_{int(time.time())}",
                    system_message="You are a maritime certificate analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info("🤖 Audit Certificate AI response received")
                    
                    # Parse JSON response
                    try:
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # POST-PROCESSING
                        extracted_data = _post_process_extracted_data(extracted_data, filename, summary_text)
                        
                        logger.info("✅ Audit certificate field extraction successful")
                        return extracted_data
                        
                    except json.JSONDecodeError as je:
                        logger.error(f"❌ JSON parse error: {je}")
                        logger.error(f"AI response content: {content[:500]}")
                        return {}
                else:
                    logger.error("Empty AI response")
                    return {}
                    
            except Exception as ai_error:
                logger.error(f"❌ System AI extraction error: {ai_error}")
                return {}
        else:
            logger.error(f"Unsupported AI provider: {ai_provider}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error extracting certificate fields: {e}")
        return {}


def _post_process_extracted_data(extracted_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Post-process extracted data from AI
    
    Logic:
    1. Validate and normalize dates (issue_date, valid_date, last_endorse, next_survey)
    2. Validate cert_type (must be valid option)
    3. Normalize issued_by abbreviations
    4. Validate IMO number format (7 digits)
    5. Determine certificate category (ISM/ISPS/MLC/CICA) ⭐
    
    Based on Backend V1 logic
    
    Returns:
        dict: Post-processed data
    """
    try:
        # 1. Normalize dates
        date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey']
        for field in date_fields:
            if extracted_data.get(field):
                normalized_date = _normalize_date(extracted_data[field])
                if normalized_date:
                    extracted_data[field] = normalized_date
                    logger.info(f"✅ Normalized {field}: {extracted_data[field]}")
        
        # 2. Validate and normalize cert_type
        if extracted_data.get('cert_type'):
            normalized_type = validate_certificate_type(extracted_data['cert_type'])
            if normalized_type:
                extracted_data['cert_type'] = normalized_type
                logger.info(f"✅ Normalized cert_type: '{normalized_type}'")
        
        # 3. Normalize issued_by abbreviations
        if extracted_data.get('issued_by'):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            original_issued_by = extracted_data['issued_by']
            normalized_issued_by = normalize_issued_by(original_issued_by)
            
            if normalized_issued_by != original_issued_by:
                logger.info(f"✅ Normalized issued_by: '{original_issued_by}' → '{normalized_issued_by}'")
                extracted_data['issued_by'] = normalized_issued_by
            
            # Generate abbreviation if not provided
            if not extracted_data.get('issued_by_abbreviation'):
                extracted_data['issued_by_abbreviation'] = normalized_issued_by
        
        # 4. Validate IMO number (7 digits)
        if extracted_data.get('imo_number'):
            imo = str(extracted_data['imo_number']).strip()
            # Extract only digits
            imo_digits = re.sub(r'\D', '', imo)
            if len(imo_digits) == 7:
                extracted_data['imo_number'] = imo_digits
                logger.info(f"✅ Valid IMO number: {imo_digits}")
            else:
                logger.warning(f"⚠️ Invalid IMO number format: {imo} (not 7 digits)")
                extracted_data['imo_number'] = None
        
        # 5. ⭐ Determine certificate category (ISM/ISPS/MLC/CICA)
        # Priority: filename > cert_name
        cert_category = None
        
        # Check filename first (CREW ACCOMMODATION → CICA)
        if filename:
            filename_upper = filename.upper()
            if 'CREW ACCOMMODATION' in filename_upper:
                cert_category = 'CICA'
                logger.info("✅ Detected 'CREW ACCOMMODATION' in filename → category = CICA")
            elif 'CICA' in filename_upper:
                cert_category = 'CICA'
                logger.info("✅ Detected 'CICA' in filename → category = CICA")
            elif 'ISM' in filename_upper and 'ISPS' not in filename_upper:
                cert_category = 'ISM'
            elif 'ISPS' in filename_upper:
                cert_category = 'ISPS'
            elif 'MLC' in filename_upper:
                cert_category = 'MLC'
        
        # Check cert_name if category not found from filename
        if not cert_category and extracted_data.get('cert_name'):
            cert_name_upper = extracted_data['cert_name'].upper()
            
            # PRIORITY: Check for CREW ACCOMMODATION first
            if 'CREW ACCOMMODATION' in cert_name_upper:
                cert_category = 'CICA'
                logger.info("✅ Detected 'CREW ACCOMMODATION' in cert_name → category = CICA")
            else:
                # Check against dictionary
                for category, cert_list in AUDIT_CERTIFICATE_CATEGORIES.items():
                    for valid_cert in cert_list:
                        if valid_cert in cert_name_upper or cert_name_upper in valid_cert:
                            cert_category = category.upper()
                            logger.info(f"✅ Matched certificate category: {cert_category}")
                            break
                    if cert_category:
                        break
        
        # Store detected category (for validation later)
        if cert_category:
            extracted_data['_detected_category'] = cert_category
        
        # 6. Generate cert_abbreviation if not provided
        if not extracted_data.get('cert_abbreviation') and extracted_data.get('cert_name'):
            extracted_data['cert_abbreviation'] = generate_certificate_abbreviation(
                extracted_data['cert_name']
            )
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error in post-processing: {e}")
        return extracted_data


def _normalize_date(date_str: str) -> Optional[str]:
    """
    Normalize date string to YYYY-MM-DD format
    
    Handles formats:
    - dd/mm/yyyy
    - mm/dd/yyyy
    - yyyy-mm-dd
    - Full text dates
    
    Returns:
        str: Date in YYYY-MM-DD format or None
    """
    try:
        if not date_str or date_str in ['-', '', 'None', 'N/A']:
            return None
        
        # Try parsing with dateutil
        parsed_date = date_parser.parse(str(date_str), dayfirst=True)
        return parsed_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        logger.warning(f"⚠️ Could not parse date '{date_str}': {e}")
        return None


def validate_certificate_type(cert_type: str) -> Optional[str]:
    """
    Validate and normalize certificate type
    
    Valid types:
    - Full Term
    - Interim
    - Provisional
    - Short term
    - Conditional
    - Other
    
    Returns:
        str: Normalized cert_type or None if invalid
    """
    if not cert_type:
        return None
    
    cert_type_lower = cert_type.lower().strip()
    
    # Mapping of variations to standard types
    type_mapping = {
        'full term': 'Full Term',
        'full': 'Full Term',
        'interim': 'Interim',
        'provisional': 'Provisional',
        'short term': 'Short term',
        'short': 'Short term',
        'conditional': 'Conditional',
        'other': 'Other',
    }
    
    for key, standard_type in type_mapping.items():
        if key in cert_type_lower:
            return standard_type
    
    # If no match, return "Other"
    logger.warning(f"⚠️ Unknown cert_type '{cert_type}', defaulting to 'Other'")
    return "Other"


def generate_certificate_abbreviation(cert_name: str) -> str:
    """
    Generate abbreviation from certificate name
    
    Examples:
    - "Safety Management Certificate" → "SMC"
    - "International Ship Security Certificate" → "ISSC"
    - "Maritime Labour Certificate" → "MLC"
    - "Certificate of Inspection" → "CICA"
    
    Returns:
        str: Generated abbreviation
    """
    if not cert_name:
        return ""
    
    # Known mappings
    known_abbreviations = {
        "SAFETY MANAGEMENT CERTIFICATE": "SMC",
        "DOCUMENT OF COMPLIANCE": "DOC",
        "INTERNATIONAL SHIP SECURITY CERTIFICATE": "ISSC",
        "SHIP SECURITY PLAN": "SSP",
        "MARITIME LABOUR CERTIFICATE": "MLC",
        "DECLARATION OF MARITIME LABOUR COMPLIANCE": "DMLC",
        "CERTIFICATE OF INSPECTION": "CICA",
        "CREW ACCOMMODATION": "CICA",
    }
    
    cert_name_upper = cert_name.upper()
    
    # Check known mappings first
    for full_name, abbrev in known_abbreviations.items():
        if full_name in cert_name_upper:
            return abbrev
    
    # Generate from first letters of words
    words = cert_name_upper.split()
    if len(words) >= 2:
        # Take first letter of each word (max 4 letters)
        abbrev = ''.join([word[0] for word in words if word and len(word) > 0])[:4]
        return abbrev
    
    # Fallback: use first 3 characters
    return cert_name[:3].upper()


def create_audit_certificate_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create structured prompt for audit certificate field extraction
    
    ⭐ EXPANDED: Now includes CICA certificate detection
    
    Based on Backend V1 prompt pattern and Audit Report prompt
    
    Args:
        summary_text: Document AI summary text (with OCR)
        filename: Original filename (provides hints)
    
    Returns:
        str: Formatted prompt for System AI
    """
    try:
        prompt = f"""You are an AI specialized in maritime audit certificate information extraction.

**INPUT**: Below is the Document AI text extraction from an audit certificate file.

**FILENAME**: {filename}
(Filename often contains hints about certificate type)

**TASK**: Extract the following fields and return as JSON:

{{
    "cert_name": "**REQUIRED** - Full certificate name (e.g., 'Safety Management Certificate', 'International Ship Security Certificate', 'Certificate of Inspection')",
    "cert_abbreviation": "Certificate abbreviation (e.g., 'SMC', 'ISSC', 'MLC', 'CICA')",
    "cert_no": "**REQUIRED** - Certificate number/reference",
    "cert_type": "Certificate type - MUST be one of: 'Full Term', 'Interim', 'Provisional', 'Short term', 'Conditional', 'Other'",
    "issue_date": "Issue date in FULL TEXT format (e.g., '15 November 2024' or 'November 15, 2024') - NOT numeric format",
    "valid_date": "Valid until / Expiry date in FULL TEXT format",
    "last_endorse": "Last endorsement date in FULL TEXT format (if any)",
    "next_survey": "Next survey date in FULL TEXT format (if any)",
    "next_survey_type": "Type of next survey - one of: 'Initial', 'Intermediate', 'Renewal', 'Annual', 'Other'",
    "issued_by": "**IMPORTANT** - Full organization name that issued the certificate (e.g., 'Bureau Veritas', 'Lloyd\\'s Register', 'Det Norske Veritas')",
    "issued_by_abbreviation": "Organization abbreviation (e.g., 'BV', 'LR', 'DNV')",
    "ship_name": "Name of the ship",
    "imo_number": "IMO number - 7 digits ONLY (e.g., '1234567')",
    "confidence_score": "Your confidence in the extraction accuracy (0.0 - 1.0)"
}}

**CRITICAL INSTRUCTIONS FOR CERTIFICATE CATEGORY**:

This certificate MUST belong to one of these categories:

1. **ISM (International Safety Management)**
   - Safety Management Certificate (SMC)
   - Document of Compliance (DOC)
   - Keywords: "ISM", "SAFETY MANAGEMENT", "SMC", "DOC"

2. **ISPS (International Ship and Port Facility Security)**
   - International Ship Security Certificate (ISSC)
   - Ship Security Plan (SSP)
   - Keywords: "ISPS", "SHIP SECURITY", "ISSC", "SSP"

3. **MLC (Maritime Labour Convention)**
   - Maritime Labour Certificate
   - Declaration of Maritime Labour Compliance (DMLC)
   - Keywords: "MLC", "MARITIME LABOUR", "DMLC"

4. **⭐ CICA (Certificate of Inspection for Crew Accommodation)** ⭐ NEW
   - Certificate of Inspection / Statement of Compliance of Crew Accommodation
   - Crew Accommodation Certificate
   - Keywords: "CREW ACCOMMODATION", "CICA", "CERTIFICATE OF INSPECTION"
   - **SPECIAL CASE**: If document contains "CREW ACCOMMODATION" → ALWAYS classify as CICA

**CATEGORY DETECTION PRIORITY**:
1. If "CREW ACCOMMODATION" appears in document → CICA ⭐
2. If "ISM" or "SAFETY MANAGEMENT" appears → ISM
3. If "ISPS" or "SHIP SECURITY" appears → ISPS
4. If "MLC" or "MARITIME LABOUR" appears → MLC

**CRITICAL VALIDATION**:
- If the certificate does NOT belong to ISM/ISPS/MLC/CICA, return an error
- cert_name and cert_no are REQUIRED fields
- Dates must be in FULL TEXT format, not DD/MM/YYYY or MM/DD/YYYY
- IMO number must be exactly 7 digits
- cert_type must be one of the specified options

**SPECIAL NOTES**:
- Look carefully for CREW ACCOMMODATION text (may appear in cert name or document body)
- Issued_by should be the full organization name (e.g., "Bureau Veritas", not just "BV")
- Next survey type: usually "Initial", "Intermediate", or "Renewal"
- If a field is not found, return empty string "" or null, but DO NOT skip the field

**OUTPUT FORMAT**: Return ONLY valid JSON, no extra text or explanations.

**DOCUMENT TEXT:**

{summary_text}
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        return ""
