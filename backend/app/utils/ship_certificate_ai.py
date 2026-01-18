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
    "Statement",
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
                    
                    # Post-process extracted data (pass raw text for keyword detection)
                    processed_data = post_process_extracted_data(extracted_data, summary_text)
                    
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
    "cert_type": "Certificate type - MUST be one of: 'Full Term', 'Interim', 'Provisional', 'Short term', 'Conditional', 'Statement', 'Other'. ⚠️ CRITICAL RULES: (1) If cert_name contains 'INTERIM' → ALWAYS use 'Interim' (highest priority). Example: 'INTERIM STATEMENT OF COMPLIANCE' → 'Interim'. (2) If cert_name contains 'STATEMENT' but NOT 'INTERIM' → use 'Statement'. (3) Default to 'Full Term' for standard certificates.",
    "issue_date": "Issue date in FULL TEXT format (e.g., '15 November 2024' or 'November 15, 2024') - NOT numeric format",
    "valid_date": "Valid until / Expiry date in FULL TEXT format",
    "last_endorse": "**CRITICAL - SCAN ALL PAGES**: Find 'Annual surveys' or 'Endorsement' sections (often on LAST pages). Extract the MOST RECENT date from all Annual/Intermediate survey entries. Return in FULL TEXT format.",
    "has_annual_survey": "**CRITICAL** - Boolean (true/false). See detailed instructions below in 'HAS_ANNUAL_SURVEY DETECTION RULES' section.",
    "next_survey": "Next survey date in FULL TEXT format (if any)",
    "next_survey_type": "Type of next survey - one of: 'Initial', 'Intermediate', 'Renewal', 'Annual', 'Special', 'FT Issue', 'Other'",
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

**CERTIFICATE TYPE CLASSIFICATION RULES**:

1. **Statement**: If cert_name contains the word "Statement" (e.g., "Statement of Compliance", "Statement of Fact")
2. **Interim**: If the certificate is temporary/interim before Full Term issuance
3. **Provisional**: If the certificate is provisional
4. **Short term**: If the certificate is short term (typically < 5 months validity)
5. **Conditional**: If the certificate has conditions attached
6. **Full Term**: Standard certificates with full validity period (typically 5 years)

**CERTIFICATE CATEGORY LIST**:

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
   - International Oil Pollution Prevention Certificate (IOPP)
   - International Air Pollution Prevention Certificate (IAPP)
   - Ballast Water Management Certificate (BWMC)
   - International Sewage Pollution Prevention Certificate (ISPP)
   - Anti-Fouling System Certificate (AFSC)
   - Keywords: "POLLUTION", "IOPP", "IAPP", "MARPOL", "BALLAST WATER"

5. **Tonnage & Registry**
   - Tonnage Certificate, Certificate of Registry
   - Keywords: "TONNAGE", "REGISTRY"

6. **Statement Documents**
   - Statement of Compliance
   - Statement of Fact
   - Keywords: "STATEMENT"

7. **Other Certificates**
   - Minimum Safe Manning Certificate (MSMC)
   - Certificate of Fitness
   - Civil Liability Certificate
   - Continuous Synopsis Record (CSR)

8. **Dangerous Goods & Bulk Cargo Certificates**
   - Document of Compliance - Special Requirements for Ships Carrying Dangerous Goods (DG)
   - Document of Compliance for the Carriage of Solid Bulk Cargoes (IMSBC)
   - Keywords: "DANGEROUS GOODS", "IMDG", "IMSBC", "BULK CARGOES"

**⚠️ HOW TO DETERMINE IF CERTIFICATE REQUIRES ANNUAL SURVEYS**:
- DO NOT assume based on certificate type
- Instead, SCAN THE ENTIRE DOCUMENT SUMMARY to find "Annual Survey Endorsement" sections
- Look for section titles like:
  * "Annual surveys"
  * "Endorsement for annual and intermediate surveys"
  * "1st Annual survey", "2nd Annual survey", "3rd Annual survey", "4th Annual survey"
  * "Intermediate survey"
- If such sections EXIST with dates → Certificate requires annual surveys
- If NO such sections exist → Certificate only requires Renewal survey

**CERT_NAME EXTRACTION RULES**:
- Extract the EXACT certificate name from the document header
- Include full official name (e.g., "Cargo Ship Safety Construction Certificate" not just "Safety Certificate")
- If multiple certificate types appear, extract the PRIMARY certificate name from the top of the document
- Do NOT invent or modify certificate names

**CRITICAL VALIDATION**:
- cert_name and cert_no are REQUIRED fields
- Dates must be in FULL TEXT format, not DD/MM/YYYY or MM/DD/YYYY
- IMO number must be exactly 7 digits
- cert_type: If cert_name contains 'INTERIM' → use 'Interim'. If contains 'STATEMENT' (no INTERIM) → use 'Statement'. Otherwise use appropriate type.
- **issued_by**: ALWAYS prefer the clean text from Document AI OCR section over Text Layer (avoid duplicate characters like "PPaannaammaa")

**SPECIAL NOTES**:
- Issued_by could be a Classification Society (LR, DNV, ABS, BV, etc.) or a Flag State Authority
- **issued_by**: ALWAYS prefer the clean text from Document AI OCR section over Text Layer (avoid duplicate characters)
- Ship name: Look for "NAME OF SHIP", "VESSEL NAME", "M.V.", "M/V"
- IMO number: Look for "IMO NO", "IMO NUMBER", format like "IMO 9573945"
- If a field is not found, return empty string "" or null, but DO NOT skip the field

**⚠️ HAS_ANNUAL_SURVEY DETECTION RULES (VERY IMPORTANT)**:

The keyword "Annual Survey" alone is NOT sufficient to determine if a certificate requires annual endorsements.
You must look for a **STRUCTURED ENDORSEMENT SECTION** with the following characteristics:

**✅ SET has_annual_survey = TRUE if document has ALL of these:**
1. A dedicated section titled one of:
   - "Annual surveys"
   - "Periodical surveys" or "Periodical survey" (equivalent to Annual surveys)
   - "Endorsement for annual and intermediate surveys"
   - "Endorsement for annual survey"
   - "Endorsement for periodical surveys"
2. Multiple numbered entries like:
   - "1st Annual survey", "2nd Annual survey", "3rd Annual survey", "4th Annual survey"
   - "1st Periodical survey", "2nd Periodical survey", "3rd Periodical survey", "4th Periodical survey"
   - OR "Annual survey" / "Periodical survey" repeated multiple times
3. Each entry has a STRUCTURED FORMAT with:
   - "Signed:" or "Signature" field
   - "Place of survey:" or "Place:" field
   - "Date:" field
   - These fields may be empty (waiting to be filled) or filled with actual values

**Example of VALID Annual Survey Section (has_annual_survey = TRUE):**
```
Annual surveys
This is to certify that, at a survey, the ship was found to comply...

1st Annual survey
Signed: [signature or empty]
Place of survey: Vung Tau
Date: 30 August 2024

2nd Annual survey  
Signed: [signature or empty]
Place of survey: Vung Tau
Date: 16 July 2025

3rd Annual survey
Signed:
Place of survey:
Date:
```

**Example of VALID Periodical Survey Section (has_annual_survey = TRUE):**
```
Periodical surveys
This is to certify that, at a periodical survey...

1st Periodical survey
Signed: [signature]
Place of survey: Singapore
Date: 15 March 2024

2nd Periodical survey
Signed:
Place of survey:
Date:
```

**❌ SET has_annual_survey = FALSE if:**
1. Document has NO "Annual surveys" or "Periodical surveys" section
2. Document only has "Endorsement to extend the certificate" sections (these are extensions, NOT annual surveys)
3. The phrase "Annual Survey" or "Periodical Survey" appears only in general text (e.g., "subject to annual survey") but NOT in a structured endorsement section
4. Document is an insurance certificate, tonnage certificate, registry certificate, etc.

**Example of INVALID (has_annual_survey = FALSE):**
```
Endorsement to extend the certificate if valid for less than 5 years...
Signed:
Place of survey:
Date:

Endorsement where the renewal survey has been completed...
Signed:
Place of survey:
Date:
```
(This is extension endorsement, NOT annual survey endorsement)

**LAST_ENDORSE & NEXT_SURVEY EXTRACTION RULES (CRITICAL - READ CAREFULLY)**:

⚠️ **STEP 1: SCAN ENTIRE DOCUMENT FROM PAGE 1 TO LAST PAGE**
- You MUST read ALL pages, including the LAST pages
- Annual survey sections are often at the END of the document (e.g., page 6 of 6)
- DO NOT stop reading after finding issue_date and valid_date on page 1

⚠️ **STEP 2: CHECK IF DOCUMENT HAS "Annual Survey Endorsement" SECTIONS**
- Search the ENTIRE document for structured Annual Survey sections as described above
- Look for the PATTERN: numbered entries (1st, 2nd, 3rd, 4th) with Signed/Place/Date fields

⚠️ **STEP 3: DETERMINE EXTRACTION BASED ON WHAT YOU FOUND**

**CASE A - Document HAS structured "Annual Survey" endorsement section:**
- Set has_annual_survey = true
- Extract ALL dates from Annual/Intermediate survey entries
- Look for: "Date XX Month YYYY", "Credited by... on XX Month YYYY"
- IGNORE entries with empty Date fields or no signature
- Set last_endorse = MOST RECENT (latest) date found
- Set next_survey_type = "Annual" or "Intermediate" based on next due

**CASE B - Document has NO structured "Annual Survey" endorsement section:**
- Set has_annual_survey = false
- The document only has extension endorsements (e.g., "Endorsement to extend the certificate...")
- These extension sections are NOT annual surveys
- Set last_endorse = "" (empty string)
- Set next_survey = valid_date
- Set next_survey_type = "Renewal"

⚠️ **STEP 4: EXAMPLES**

**Example 1 - IAPP Certificate (has_annual_survey = TRUE):**
Document contains structured section:
```
Endorsement for annual and intermediate surveys
...
1st Annual survey
Signed: [signature]
Place of survey: Vung Tau
Date: 30 August 2024

2nd Annual survey
Signed: [signature]
Place of survey: Vung Tau  
Date: 16 July 2025
```
→ has_annual_survey = true (structured section with numbered entries + Signed/Place/Date)
→ last_endorse = "16 July 2025" (most recent date)
→ next_survey_type = "Annual"

**Example 2 - DG/IMSBC Certificate (has_annual_survey = TRUE):**
Document page 6 contains:
```
Annual surveys
This is to certify that, at a survey, the ship was found to comply...

1st Annual survey
Credited by the Losing Society on 30 August 2024
Signed:
Place of survey:
Date:

2nd Annual survey
Signed: Hoai Nguyen Van
Place of survey: Vung Tau (VN)
Date: 16 July 2025
```
→ has_annual_survey = true
→ last_endorse = "16 July 2025"
→ next_survey_type = "Annual"

**Example 3 - ISPP Certificate (has_annual_survey = FALSE):**
Document does NOT have "Annual surveys" section.
Page 2 only contains:
```
Endorsement to extend the certificate if valid for less than 5 years...
Signed:
Place of survey:
Date:

Endorsement where the renewal survey has been completed...
Signed:
Place of survey:
Date:
```
→ has_annual_survey = false (these are extension endorsements, NOT annual survey endorsements)
→ last_endorse = ""
→ next_survey = "28 June 2028" (same as valid_date)
→ next_survey_type = "Renewal"

**Example 4 - Insurance/P&I Certificate (has_annual_survey = FALSE):**
Document has no endorsement section at all, or only general terms.
→ has_annual_survey = false
→ last_endorse = ""
→ next_survey_type = "Renewal"
→ next_survey_type = "Renewal"

**OUTPUT FORMAT**: Return ONLY valid JSON, no extra text or explanations.

**DOCUMENT TEXT:**

{summary_text}
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        return ""


def post_process_extracted_data(extracted_data: Dict[str, Any], raw_text: str = "") -> Dict[str, Any]:
    """
    Post-process extracted data to normalize formats
    
    Based on audit_certificate_ai.py post_process_extracted_data()
    
    Args:
        extracted_data: Raw extraction from AI
        raw_text: Original document text for additional context
    
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
        
        # ===== AUTO-CLASSIFY CERT_TYPE BASED ON KEYWORDS =====
        cert_name = extracted_data.get('cert_name', '').upper()
        cert_no = extracted_data.get('cert_no', '').upper()
        raw_text_upper = raw_text.upper() if raw_text else ""
        
        # Priority 1: Check for INTERIM (highest priority)
        # If cert_name contains "INTERIM", it's an Interim certificate regardless of other keywords
        is_interim = False
        if 'INTERIM' in cert_name:  # INTERIM in cert_name has highest priority
            is_interim = True
            logger.info(f"Detected INTERIM in cert_name: {cert_name}")
        elif 'INTERIM CERTIFICATE' in raw_text_upper:
            is_interim = True
        elif 'INTERIM' in cert_no:
            is_interim = True
        elif raw_text_upper.count('INTERIM') >= 1 and 'INTERIM' in raw_text_upper[:500]:  # INTERIM appears prominently at top
            is_interim = True
            
        if is_interim:
            extracted_data['cert_type'] = 'Interim'
            logger.info(f"Auto-classified as Interim based on document keywords")
        # Priority 2: Check for STATEMENT (only if not Interim)
        elif 'STATEMENT' in cert_name:
            extracted_data['cert_type'] = 'Statement'
            logger.info(f"Auto-classified as Statement based on cert_name: {extracted_data.get('cert_name')}")
        # Priority 3: Check for CONDITION
        elif 'CONDITION' in cert_name or 'CONDITIONAL' in cert_name:
            extracted_data['cert_type'] = 'Conditional'
            logger.info(f"Auto-classified as Conditional based on cert_name: {extracted_data.get('cert_name')}")
        # Priority 4: Check for SHORT TERM
        elif 'SHORT TERM' in cert_name or 'SHORT-TERM' in cert_name:
            extracted_data['cert_type'] = 'Short term'
            logger.info(f"Auto-classified as Short term based on cert_name: {extracted_data.get('cert_name')}")
        
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
