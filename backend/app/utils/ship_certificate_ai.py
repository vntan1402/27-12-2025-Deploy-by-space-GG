"""
Ship Certificate AI Extraction Utilities
Handles AI-powered field extraction from ship certificates (Class & Flag certificates)
Based on audit_certificate_ai.py pattern
"""
import logging
import json
import re
import time
from typing import Dict, Any, Optional
from datetime import datetime
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Ship Certificate Categories (Class & Flag Certificates)
SHIP_CERTIFICATE_CATEGORIES = {
    "class": [
        "CLASS CERTIFICATE",
        "CLASSIFICATION CERTIFICATE",
        "CERTIFICATE OF CLASS",
        "CLASS NOTATION",
    ],
    "safety": [
        "CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE",
        "CARGO SHIP SAFETY EQUIPMENT CERTIFICATE",
        "CARGO SHIP SAFETY RADIO CERTIFICATE",
        "PASSENGER SHIP SAFETY CERTIFICATE",
        "SAFETY CERTIFICATE",
        "SOLAS CERTIFICATE",
        "CSSC",
        "CSSE",
        "CSSR",
        "PSSC",
    ],
    "load_line": [
        "LOAD LINE CERTIFICATE",
        "INTERNATIONAL LOAD LINE CERTIFICATE",
        "LLC",
    ],
    "tonnage": [
        "TONNAGE CERTIFICATE",
        "INTERNATIONAL TONNAGE CERTIFICATE",
        "ITC",
    ],
    "registry": [
        "CERTIFICATE OF REGISTRY",
        "PROVISIONAL CERTIFICATE OF REGISTRY",
        "REGISTRY CERTIFICATE",
    ],
    "anti_fouling": [
        "ANTI-FOULING SYSTEM CERTIFICATE",
        "AFSC",
    ],
    "civil_liability": [
        "CIVIL LIABILITY CERTIFICATE",
        "CLC CERTIFICATE",
        "BUNKER CONVENTION CERTIFICATE",
    ],
    "ballast_water": [
        "BALLAST WATER MANAGEMENT CERTIFICATE",
        "BWMC",
    ],
    "iopp": [
        "INTERNATIONAL OIL POLLUTION PREVENTION CERTIFICATE",
        "IOPP CERTIFICATE",
        "IOPP",
    ],
    "iapp": [
        "INTERNATIONAL AIR POLLUTION PREVENTION CERTIFICATE",
        "IAPP CERTIFICATE",
        "IAPP",
    ],
    "ispp": [
        "INTERNATIONAL SEWAGE POLLUTION PREVENTION CERTIFICATE",
        "ISPP CERTIFICATE",
        "ISPP",
    ],
    "other": [
        "MINIMUM SAFE MANNING CERTIFICATE",
        "MSMC",
        "CERTIFICATE OF FITNESS",
        "CONTINUOUS SYNOPSIS RECORD",
        "CSR",
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


async def extract_ship_certificate_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any],
    raw_pdf_text: str = "",
    full_document_text: str = ""
) -> Dict[str, Any]:
    """
    Extract ship certificate fields from Document AI summary using System AI
    
    Based on extract_audit_certificate_fields_from_summary() pattern
    
    Fields to extract:
    - cert_name: Certificate name (REQUIRED)
    - cert_abbreviation: Abbreviation
    - cert_no: Certificate number (REQUIRED)
    - cert_type: Full Term, Interim, etc.
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
        filename: Original filename
        ai_config: AI configuration
    
    Returns:
        dict: Extracted fields with post-processing applied
    """
    try:
        logger.info("🤖 Extracting ship certificate fields from summary")
        
        # Get AI config
        ai_provider = ai_config.get("provider", "google")
        ai_model = ai_config.get("model", "gemini-2.0-flash")
        use_emergent_key = ai_config.get("use_emergent_key", True)
        
        # Create extraction prompt
        prompt = create_ship_certificate_extraction_prompt(summary_text, filename)
        
        if not prompt:
            logger.error("Failed to create ship certificate extraction prompt")
            return {}
        
        # Use AI for extraction (supports both Emergent key and custom API key)
        try:
            from app.utils.llm_wrapper import LlmChat, UserMessage
            
            # Create LlmChat with ai_config - it will automatically select the right API key
            chat = LlmChat(
                ai_config=ai_config,  # Pass full config for API key selection
                session_id=f"ship_cert_extraction_{int(time.time())}",
                system_message="You are a maritime certificate analysis expert."
            ).with_model("gemini", ai_model)
            
            logger.info(f"📤 Sending extraction prompt to {ai_model}...")
            
            user_message = UserMessage(text=prompt)
            ai_response = await chat.send_message(user_message)
            
            if ai_response and ai_response.strip():
                content = ai_response.strip()
                logger.info("🤖 Ship Certificate AI response received")
                
                # Parse JSON response
                try:
                    clean_content = content.replace('```json', '').replace('```', '').strip()
                    extracted_data = json.loads(clean_content)
                    
                    logger.info(f"✅ Parsed extracted data: {list(extracted_data.keys())}")
                    
                    # Post-process extracted data
                    processed_data = post_process_extracted_data(extracted_data)
                    
                    return processed_data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON parse error: {e}")
                    logger.error(f"Response content: {content[:500]}")
                    return {}
            else:
                logger.error("Empty AI response")
                return {}
                
        except Exception as e:
            logger.error(f"❌ AI extraction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error in extract_ship_certificate_fields_from_summary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def create_ship_certificate_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create structured prompt for ship certificate field extraction
    
    Based on create_audit_certificate_extraction_prompt() pattern
    
    Args:
        summary_text: Document AI summary text (with OCR)
        filename: Original filename (provides hints)
    
    Returns:
        str: Formatted prompt for System AI
    """
    try:
        prompt = f"""You are an AI specialized in maritime ship certificate information extraction.

**INPUT**: Below is the Document AI text extraction from a ship certificate file.
The document contains TWO SECTIONS:
1. **TEXT LAYER CONTENT** - Extracted directly from PDF (may have OCR errors like duplicate characters)
2. **DOCUMENT AI OCR CONTENT** - More accurate OCR from Google Document AI

**⚠️ CRITICAL - YOU MUST READ THE ENTIRE DOCUMENT FROM FIRST PAGE TO LAST PAGE**:
- Many certificates have endorsement sections at the END (last pages)
- For example: DG certificates often have "Annual surveys" on page 6 of 6
- DO NOT stop reading after page 1 - you will miss important endorsement dates!
- After reading ALL pages, then extract the required fields

**⚠️ IMPORTANT - DATA QUALITY PRIORITY**:
When extracting fields, ALWAYS compare both sections and choose the MOST ACCURATE value:
- If Text Layer has duplicate/repeated characters (e.g., "PPaannaammaa MMaarriittiimmee" instead of "Panama Maritime"), USE the Document AI OCR version instead
- Document AI OCR content is generally MORE RELIABLE for: issued_by, cert_name, organization names
- Text Layer may be more complete for: dates, certificate numbers, ship details
- **READ THE ENTIRE DOCUMENT** before selecting values - don't just pick from the first occurrence

**FILENAME**: {filename}
(Filename often contains hints about certificate type)

**TASK**: Extract the following fields and return as JSON:

{{
    "cert_name": "**REQUIRED** - Full certificate name (e.g., 'Cargo Ship Safety Construction Certificate', 'Load Line Certificate', 'Class Certificate')",
    "cert_abbreviation": "Certificate abbreviation (e.g., 'CSSC', 'LLC', 'IOPP', 'CC')",
    "cert_no": "**REQUIRED** - Certificate number/reference",
    "cert_type": "Certificate type - MUST be one of: 'Full Term', 'Interim', 'Provisional', 'Short term', 'Conditional', 'Other'",
    "issue_date": "Issue date in FULL TEXT format (e.g., '15 November 2024' or 'November 15, 2024') - NOT numeric format",
    "valid_date": "Valid until / Expiry date in FULL TEXT format",
    "last_endorse": "**CRITICAL - SCAN ALL PAGES**: Find 'Annual surveys' or 'Endorsement' sections (often on LAST pages). Extract the MOST RECENT date from all Annual/Intermediate survey entries. Return in FULL TEXT format.",
    "next_survey": "Next survey date in FULL TEXT format (if any)",
    "next_survey_type": "Type of next survey - one of: 'Initial', 'Intermediate', 'Renewal', 'Annual', 'Special', 'Other'",
    "issued_by": "**CRITICAL** - Full organization name that issued the certificate. MUST use CLEAN text from Document AI OCR section (e.g., 'Panama Maritime Documentation Services, Inc.', NOT 'PPaannaammaa MMaarriittiimmee...')",
    "issued_by_abbreviation": "Organization abbreviation (e.g., 'BV', 'LR', 'ABS', 'PMA', 'PMDS')",
    "ship_name": "Name of the ship/vessel",
    "imo_number": "IMO number - 7 digits ONLY (e.g., '9573945')",
    "flag": "Flag state / Port of registry",
    "gross_tonnage": "Gross tonnage (numeric only)",
    "deadweight": "Deadweight tonnage (numeric only)",
    "ship_type": "Ship type (e.g., 'Bulk Carrier', 'Container Ship', 'Oil Tanker')",
    "confidence_score": "Your confidence in the extraction accuracy (0.0 - 1.0)"
}}

**CERTIFICATE TYPE CATEGORIES**:

This certificate should belong to one of these categories:

1. **Class Certificates**
   - Class Certificate, Classification Certificate
   - Keywords: "CLASS", "CLASSIFICATION"

2. **Safety Certificates (SOLAS)**
   - Cargo Ship Safety Construction Certificate (CSSC)
   - Cargo Ship Safety Equipment Certificate (CSSE)
   - Cargo Ship Safety Radio Certificate (CSSR)
   - Passenger Ship Safety Certificate (PSSC)
   - Keywords: "SAFETY", "SOLAS", "CARGO SHIP"

3. **Load Line Certificates**
   - International Load Line Certificate (LLC)
   - Keywords: "LOAD LINE", "LLC"

4. **Pollution Prevention Certificates**
   - International Oil Pollution Prevention Certificate (IOPP) - HAS Annual/Intermediate surveys
   - International Air Pollution Prevention Certificate (IAPP) - HAS Annual/Intermediate surveys
   - Ballast Water Management Certificate (BWMC) - HAS Annual/Intermediate surveys
   - International Sewage Pollution Prevention Certificate (ISPP) - NO annual surveys, ONLY Renewal
   - Anti-Fouling System Certificate (AFSC) - NO annual surveys, ONLY Renewal
   - Keywords: "POLLUTION", "IOPP", "IAPP", "MARPOL", "BALLAST WATER"

5. **Tonnage & Registry** - NO annual surveys
   - Tonnage Certificate, Certificate of Registry
   - Keywords: "TONNAGE", "REGISTRY"

6. **Other Certificates** - Generally NO annual surveys
   - Minimum Safe Manning Certificate (MSMC)
   - Certificate of Fitness
   - Civil Liability Certificate
   - Continuous Synopsis Record (CSR)

7. **Dangerous Goods & Bulk Cargo Certificates (REQUIRE ANNUAL SURVEYS)**
   - Document of Compliance - Special Requirements for Ships Carrying Dangerous Goods (DG)
   - Document of Compliance for the Carriage of Solid Bulk Cargoes (IMSBC)
   - Keywords: "DANGEROUS GOODS", "IMDG", "IMSBC", "BULK CARGOES"
   - ⚠️ **IMPORTANT**: These certificates often have "Annual surveys" section at the END of document (last pages)
   - You MUST read ALL pages to find the Annual surveys endorsement section

**⚠️ SURVEY REQUIREMENTS BY CERTIFICATE TYPE**:

**CERTIFICATES WITH ANNUAL/INTERMEDIATE SURVEYS** (check for endorsement sections):
- IOPP, IAPP (Pollution Prevention - Oil & Air)
- CSSC, CSSE, CSSR, PSSC (Safety Certificates)
- LLC (Load Line Certificate)
- CC (Class Certificate)
- DG, IMSBC (Dangerous Goods, Bulk Cargoes)
→ These have "Annual survey" or "Intermediate survey" endorsement sections
→ Extract last_endorse from these sections

**CERTIFICATES WITH ONLY RENEWAL SURVEY** (NO annual endorsements):
- ISPP (Sewage Pollution Prevention)
- BWMC (Ballast Water Management)
- AFSC (Anti-Fouling System)
- Tonnage Certificate
- Certificate of Registry
- MSMC (Minimum Safe Manning)
- CSR (Continuous Synopsis Record)
→ These do NOT have Annual survey sections
→ last_endorse should be empty ""
→ next_survey = valid_date
→ next_survey_type = "Renewal"

**CERT_NAME EXTRACTION RULES**:
- Extract the EXACT certificate name from the document header
- Include full official name (e.g., "Cargo Ship Safety Construction Certificate" not just "Safety Certificate")
- If multiple certificate types appear, extract the PRIMARY certificate name from the top of the document
- Do NOT invent or modify certificate names

**CRITICAL VALIDATION**:
- cert_name and cert_no are REQUIRED fields
- Dates must be in FULL TEXT format, not DD/MM/YYYY or MM/DD/YYYY
- IMO number must be exactly 7 digits
- cert_type must be one of the specified options
- **issued_by**: ALWAYS prefer the clean text from Document AI OCR section over Text Layer (avoid duplicate characters like "PPaannaammaa")

**SPECIAL NOTES**:
- Issued_by could be a Classification Society (LR, DNV, ABS, BV, etc.) or a Flag State Authority
- **issued_by**: ALWAYS prefer the clean text from Document AI OCR section over Text Layer (avoid duplicate characters)
- Ship name: Look for "NAME OF SHIP", "VESSEL NAME", "M.V.", "M/V"
- IMO number: Look for "IMO NO", "IMO NUMBER", format like "IMO 9573945"
- If a field is not found, return empty string "" or null, but DO NOT skip the field

**LAST_ENDORSE & NEXT_SURVEY EXTRACTION RULES (CRITICAL - READ CAREFULLY)**:

⚠️ **STEP 1: DETERMINE IF CERTIFICATE REQUIRES ANNUAL SURVEYS**

First, identify the certificate type and check if it has Annual/Intermediate survey sections in the document:

**CERTIFICATES WITH ANNUAL SURVEYS** (look for endorsement sections):
- IOPP, IAPP (Oil & Air Pollution Prevention)
- CSSC, CSSE, CSSR (Safety Certificates)  
- LLC (Load Line)
- CC (Class Certificate)
- DG, IMSBC (Dangerous Goods, Bulk Cargoes)
→ If document has "Annual survey" or "Intermediate survey" sections with dates:
  - Extract last_endorse = MOST RECENT endorsement date
  - next_survey_type = "Annual" or "Intermediate" (based on schedule)

**CERTIFICATES WITHOUT ANNUAL SURVEYS** (only Renewal):
- ISPP (Sewage Pollution Prevention)
- BWMC (Ballast Water Management)
- AFSC (Anti-Fouling System)
- Tonnage Certificate
- MSMC (Minimum Safe Manning)
- CSR (Continuous Synopsis Record)
→ If document has NO "Annual survey" sections (only extension endorsements):
  - last_endorse = "" (empty)
  - next_survey = valid_date
  - next_survey_type = "Renewal"

⚠️ **STEP 2: SCAN ENTIRE DOCUMENT FROM PAGE 1 TO LAST PAGE**
- You MUST read ALL pages, including the LAST pages
- Many certificates have endorsement sections at the END of the document (e.g., page 6 of 6)
- DO NOT stop reading after finding issue_date and valid_date on page 1

⚠️ **STEP 3: CHECK IF "Annual surveys" OR "Endorsement for annual/intermediate surveys" SECTION EXISTS**
- Section titles to look for:
  * "Annual surveys"
  * "Endorsement for annual and intermediate surveys"
  * "1st Annual survey", "2nd Annual survey", "3rd Annual survey", "4th Annual survey"
  * "Intermediate survey"
  
**IF FOUND (certificate requires annual surveys)**:
- Extract ALL dates from endorsement entries
- Look for: "Date XX Month YYYY", "Credited by... on XX Month YYYY"
- IGNORE entries that have empty Date fields or no signature
- Return the MOST RECENT (latest) date as last_endorse

**IF NOT FOUND (certificate only requires renewal)**:
- The document only has extension endorsements (e.g., "Endorsement to extend the certificate...")
- These are NOT annual surveys
- Set: last_endorse = "", next_survey = valid_date, next_survey_type = "Renewal"

⚠️ **STEP 4: EXAMPLES**

**Example 1 - DG Certificate (HAS Annual surveys on page 6)**:
- Page 6 shows: "1st Annual survey - Credited... 30 August 2024"
- Page 6 shows: "2nd Annual survey - Date 16 July 2025"
→ last_endorse = "16 July 2025"
→ next_survey_type = "Annual"

**Example 2 - ISPP Certificate (NO Annual surveys)**:
- Document has NO "Annual surveys" section
- Page 2 only has "Endorsement to extend the certificate" (extension, not annual)
- valid_date = "28 June 2028"
→ last_endorse = ""
→ next_survey = "28 June 2028"
→ next_survey_type = "Renewal"

**OUTPUT FORMAT**: Return ONLY valid JSON, no extra text or explanations.

**DOCUMENT TEXT:**

{summary_text}
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        return ""


def post_process_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Post-process extracted data to normalize formats
    
    Based on audit_certificate_ai.py post_process_extracted_data()
    
    Args:
        extracted_data: Raw extraction from AI
    
    Returns:
        dict: Processed and normalized data
    """
    try:
        # Normalize dates (text format -> YYYY-MM-DD)
        date_fields = ['issue_date', 'valid_date', 'last_endorse', 'next_survey']
        for field in date_fields:
            if extracted_data.get(field):
                normalized_date = normalize_date_text(extracted_data[field])
                if normalized_date:
                    extracted_data[field] = normalized_date
        
        # Normalize IMO number (remove spaces, "IMO" prefix)
        if extracted_data.get('imo_number'):
            imo = str(extracted_data['imo_number']).replace(' ', '').replace('IMO', '').strip()
            if imo.isdigit() and len(imo) == 7:
                extracted_data['imo_number'] = imo
            else:
                extracted_data['imo_number'] = None
        
        # Clean text fields
        text_fields = ['cert_name', 'cert_no', 'issued_by', 'ship_name', 'flag']
        for field in text_fields:
            if extracted_data.get(field):
                extracted_data[field] = str(extracted_data[field]).strip()
        
        # Validate cert_type
        if extracted_data.get('cert_type') and extracted_data['cert_type'] not in VALID_CERTIFICATE_TYPES:
            logger.warning(f"Invalid cert_type: {extracted_data['cert_type']}, defaulting to 'Full Term'")
            extracted_data['cert_type'] = 'Full Term'
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error in post_process_extracted_data: {e}")
        return extracted_data


def normalize_date_text(date_text: str) -> Optional[str]:
    """
    Normalize date from various text formats to YYYY-MM-DD
    
    Examples:
    - "15 November 2024" -> "2024-11-15"
    - "November 15, 2024" -> "2024-11-15"
    - "15/11/2024" -> "2024-11-15"
    
    Args:
        date_text: Date in text format
    
    Returns:
        str: Date in YYYY-MM-DD format or None
    """
    try:
        if not date_text or not isinstance(date_text, str):
            return None
        
        date_text = date_text.strip()
        
        # Try parsing with dateutil (handles most formats)
        parsed_date = date_parser.parse(date_text, dayfirst=True)
        return parsed_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        logger.warning(f"Could not parse date: {date_text}, error: {e}")
        return None


def check_certificate_category(cert_name: str) -> Optional[str]:
    """
    Check which category a certificate belongs to
    
    Args:
        cert_name: Certificate name
    
    Returns:
        str: Category name or None
    """
    try:
        cert_name_upper = cert_name.upper()
        
        for category, keywords in SHIP_CERTIFICATE_CATEGORIES.items():
            for keyword in keywords:
                if keyword.upper() in cert_name_upper:
                    return category
        
        return "other"
        
    except Exception as e:
        logger.error(f"Error checking certificate category: {e}")
        return None
