"""
Audit Report AI Extraction Utilities
Handles AI-powered field extraction from audit reports (ISM/ISPS/MLC)
Based on Backend V1 logic and Approval Document pattern
"""
import logging
import json
import re
import time
from typing import Dict, Any, Optional
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


async def extract_audit_report_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract audit report fields from Document AI summary using System AI
    
    Based on Backend V1: extract_audit_report_fields_from_summary()
    Location: /app/backend-v1/server.py lines 7031-7273
    
    Fields to extract:
    - audit_report_name: Main title/name of audit report
    - audit_type: ISM, ISPS, MLC, or CICA
    - report_form: Form code (e.g., "07-23", "CG (02-19)")
    - audit_report_no: Report number/reference
    - issued_by: Organization that issued/conducted audit
    - audit_date: Date of audit (YYYY-MM-DD)
    - auditor_name: Name(s) of auditor(s)
    - ship_name: Ship name
    - ship_imo: IMO number (7 digits)
    - note: Important notes
    
    Args:
        summary_text: Enhanced Document AI summary (with OCR)
        filename: Original filename (helps identify report_form and audit_type)
        ai_config: AI configuration dict with:
            - provider: "google", "emergent", etc.
            - model: Model name (e.g., "gemini-2.0-flash")
            - use_emergent_key: Whether to use Emergent LLM key
    
    Returns:
        dict: Extracted fields with post-processing applied
    """
    try:
        logger.info("🤖 Extracting audit report fields from summary")
        
        # Get AI config
        ai_provider = ai_config.get("provider", "google")
        ai_model = ai_config.get("model", "gemini-2.0-flash")
        use_emergent_key = ai_config.get("use_emergent_key", True)
        
        # Create extraction prompt
        prompt = create_audit_report_extraction_prompt(summary_text, filename)
        
        if not prompt:
            logger.error("Failed to create audit report extraction prompt")
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
                    session_id=f"audit_extraction_{int(time.time())}",
                    system_message="You are a maritime audit report analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info("🤖 Audit Report AI response received")
                    
                    # Parse JSON response
                    try:
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # POST-PROCESSING (from Backend V1 lines 7078-7273)
                        extracted_data = _post_process_extracted_data(extracted_data, filename)
                        
                        logger.info("✅ Audit report field extraction successful")
                        logger.info(f"   📋 Audit Name: '{extracted_data.get('audit_report_name', '')}'")
                        logger.info(f"   📝 Audit Type: '{extracted_data.get('audit_type', '')}'")
                        logger.info(f"   📄 Report Form: '{extracted_data.get('report_form', '')}'")
                        logger.info(f"   🔢 Audit No: '{extracted_data.get('audit_report_no', '')}'")
                        logger.info(f"   🏛️ Issued By: '{extracted_data.get('issued_by', '')}'")
                        
                        return extracted_data
                        
                    except json.JSONDecodeError as json_error:
                        logger.error(f"Failed to parse AI response as JSON: {json_error}")
                        logger.error(f"AI response: {content[:500]}")
                        return {}
                else:
                    logger.warning("AI response is empty")
                    return {}
                    
            except Exception as ai_error:
                logger.error(f"System AI extraction failed: {ai_error}")
                import traceback
                logger.error(traceback.format_exc())
                return {}
        else:
            logger.warning(f"Unsupported AI provider or configuration: {ai_provider}")
            return {}
            
    except Exception as e:
        logger.error(f"Error in extract_audit_report_fields_from_summary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {}


def _post_process_extracted_data(extracted_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
    """
    Post-process extracted data with logic from Backend V1
    
    Based on Backend V1 lines 7078-7273:
    1. Parse and validate audit_date (check if it's actually a report_form)
    2. Determine audit_type from multiple sources (filename > report_form > name > AI)
    3. Extract report_form from filename patterns
    4. Normalize issued_by abbreviations
    
    Args:
        extracted_data: Raw extracted data from AI
        filename: Original filename
    
    Returns:
        dict: Post-processed data
    """
    try:
        # 1. Parse audit_date (check if it looks like a Report Form)
        # Backend V1 lines 7079-7105
        if extracted_data.get('audit_date'):
            audit_date_raw = extracted_data['audit_date'].strip()
            
            # Pattern: Check if audit_date looks like a Report Form
            # Examples: "CG (02-19)", "(07-23)", "ISM 05-22"
            form_pattern = r'^[A-Z]{1,3}\s*\([0-9]{2}[/-][0-9]{2,3}\)$|^[A-Z]{1,3}\s+[0-9]{2}[/-][0-9]{2,3}$|^\([0-9]{2}[/-][0-9]{2,3}\)$'
            
            if re.match(form_pattern, audit_date_raw, re.IGNORECASE):
                logger.warning(f"⚠️ audit_date '{audit_date_raw}' looks like a Report Form, moving to report_form")
                # Move to report_form if empty
                if not extracted_data.get('report_form'):
                    extracted_data['report_form'] = audit_date_raw
                extracted_data['audit_date'] = ''
            else:
                try:
                    # Parse and convert to ISO format
                    parsed_date = date_parser.parse(audit_date_raw)
                    extracted_data['audit_date'] = parsed_date.strftime('%Y-%m-%d')
                except Exception as date_error:
                    logger.warning(f"Failed to parse audit_date '{audit_date_raw}': {date_error}")
                    # If parse fails, might be a form code - move to report_form if empty
                    if not extracted_data.get('report_form') and len(audit_date_raw) < 20:
                        logger.warning("⚠️ Moving unparseable audit_date to report_form")
                        extracted_data['report_form'] = audit_date_raw
                    extracted_data['audit_date'] = ''
        
        # 2. Determine audit_type from multiple sources
        # Backend V1 lines 7116-7174
        # Priority: filename > report_form > audit_report_name > AI extraction
        audit_type = extracted_data.get('audit_type', '')
        
        # Check filename first (Priority 1)
        if filename:
            filename_upper = filename.upper()
            if re.search(r'^ISM[-\s]|ISM[-\s]CODE', filename_upper):
                audit_type = 'ISM'
            elif 'ISPS' in filename_upper:
                audit_type = 'ISPS'
            elif 'MLC' in filename_upper:
                audit_type = 'MLC'
            elif 'CICA' in filename_upper:
                audit_type = 'CICA'
        
        # Check report_form if audit_type still empty (Priority 2)
        if not audit_type and extracted_data.get('report_form'):
            report_form_upper = extracted_data['report_form'].upper()
            if 'ISM' in report_form_upper and 'ISPS' not in report_form_upper:
                audit_type = 'ISM'
            elif 'ISPS' in report_form_upper:
                audit_type = 'ISPS'
            elif 'MLC' in report_form_upper:
                audit_type = 'MLC'
            elif 'CICA' in report_form_upper:
                audit_type = 'CICA'
        
        # Check audit_report_name if still empty (Priority 3)
        if not audit_type and extracted_data.get('audit_report_name'):
            name_upper = extracted_data['audit_report_name'].upper()
            if 'ISM' in name_upper and 'ISPS' not in name_upper:
                audit_type = 'ISM'
            elif 'ISPS' in name_upper:
                audit_type = 'ISPS'
            elif 'MLC' in name_upper:
                audit_type = 'MLC'
            elif 'CICA' in name_upper:
                audit_type = 'CICA'
        
        # Normalize AI extraction if exists but not standard (Priority 4)
        if not audit_type and extracted_data.get('audit_type'):
            ai_type_upper = extracted_data['audit_type'].upper()
            if 'ISM' in ai_type_upper and 'ISPS' not in ai_type_upper:
                audit_type = 'ISM'
            elif 'ISPS' in ai_type_upper:
                audit_type = 'ISPS'
            elif 'MLC' in ai_type_upper:
                audit_type = 'MLC'
            elif 'CICA' in ai_type_upper:
                audit_type = 'CICA'
        
        # Update with normalized value
        if audit_type:
            extracted_data['audit_type'] = audit_type
            logger.info(f"✅ Determined audit_type: '{audit_type}'")
        else:
            logger.warning("⚠️ Could not determine audit_type from any source")
        
        # 3. Extract report_form from filename (PRIORITY 1)
        # Backend V1 lines 7176-7232 - EXACT IMPLEMENTATION
        if filename:
            filename_form_patterns = [
                # Pattern 1: Long form names with parentheses (NEW - Priority)
                # e.g., "ISPS-Code-Interim-Check List (06-23) TRUONG MINH LUCKY" → "ISPS-Code-Interim-Check List (06-23)"
                r'([A-Z][A-Za-z0-9\-\s]+)\s*\(([0-9]{2}[-/][0-9]{2,3})\)',
                
                # Pattern 2: Short abbreviation with parentheses
                # e.g., "CG (02-19).pdf" → "CG (02-19)"
                r'([A-Z]{1,3})\s*\(([0-9]{2}[-/][0-9]{2,3})\)',
                
                # Pattern 3: Short abbreviation with space
                # e.g., "CG 02-19" → "CG (02-19)"
                r'([A-Z]{1,3})\s+([0-9]{2}[-/][0-9]{2,3})',
                
                # Pattern 4: Short abbreviation with dash/underscore
                # e.g., "CG-02-19" → "CG (02-19)"
                r'([A-Z]{1,3})[-_]([0-9]{2}[-/][0-9]{2,3})',
                
                # Pattern 5: Just parentheses (Audit-specific)
                # e.g., "(07-230)" → "(07-230)"
                r'\(([0-9]{2}[-/][0-9]{2,3})\)',
            ]
            
            filename_extracted_form = None
            for pattern in filename_form_patterns:
                match = re.search(pattern, filename)
                if match:
                    if len(match.groups()) > 1:
                        # Pattern with 2 groups
                        abbrev = match.group(1).strip()
                        date_part = match.group(2).replace('/', '-')
                        
                        # Clean up abbrev: capitalize properly and remove trailing spaces
                        # Handle both short (e.g., "CG") and long forms (e.g., "ISPS-Code-Interim-Check List")
                        abbrev_cleaned = abbrev.strip()
                        
                        # For long forms, remove common ship name patterns at the end
                        # e.g., "ISPS-Code-Interim-Check List TRUONG MINH" → "ISPS-Code-Interim-Check List"
                        ship_name_patterns = [
                            r'\s+[A-Z][A-Z\s]+$',  # All caps words at end (likely ship names)
                        ]
                        for ship_pattern in ship_name_patterns:
                            abbrev_cleaned = re.sub(ship_pattern, '', abbrev_cleaned)
                        
                        abbrev_cleaned = abbrev_cleaned.strip()
                        filename_extracted_form = f"{abbrev_cleaned} ({date_part})"
                    else:
                        # Pattern with 1 group - just parentheses (e.g., (07-230))
                        date_part = match.group(1).replace('/', '-')
                        filename_extracted_form = f"({date_part})"
                    
                    # PRIORITY 1: Filename overrides AI extraction
                    extracted_data['report_form'] = filename_extracted_form
                    logger.info(f"✅ [PRIORITY 1] Extracted report_form from filename: '{filename_extracted_form}'")
                    break
            else:
                # No pattern matched in filename
                pass
                logger.info(f"   Using AI extracted report_form: '{extracted_data.get('report_form', 'none')}'")
        
        
        # Decide which report_form to use
        ai_report_form = extracted_data.get('report_form', '')
        
        if filename_extracted_form:
            # Filename has highest priority
            extracted_data['report_form'] = filename_extracted_form
            if ai_report_form and ai_report_form != filename_extracted_form:
                logger.info(f"   ℹ️ Overriding AI extracted: '{ai_report_form}' → Using filename: '{filename_extracted_form}'")
        elif ai_report_form:
            # Use AI extraction if filename didn't find anything
            logger.info(f"✅ [PRIORITY 2] Using AI extracted report_form: '{ai_report_form}'")
        else:
            # Neither filename nor AI found report_form
            logger.warning("⚠️ No report_form found in filename or AI extraction")
            logger.warning(f"   Filename: {filename}")
            logger.warning("   AI result: empty or None")
        # 4. Normalize issued_by abbreviations
        # Backend V1 lines 7234-7273
        if extracted_data.get('issued_by'):
            from app.utils.issued_by_abbreviation import normalize_issued_by
            original_issued_by = extracted_data['issued_by']
            normalized_issued_by = normalize_issued_by(original_issued_by)
            
            if normalized_issued_by != original_issued_by:
                logger.info(f"✅ Normalized issued_by: '{original_issued_by}' → '{normalized_issued_by}'")
                extracted_data['issued_by'] = normalized_issued_by
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error in post-processing: {e}")
        return extracted_data


def create_audit_report_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create structured prompt for audit report field extraction
    
    Based on Backend V1: create_audit_report_extraction_prompt()
    Location: /app/backend-v1/server.py lines 7274-7450
    
    Args:
        summary_text: Document AI summary text (with OCR)
        filename: Original filename (provides hints)
    
    Returns:
        str: Formatted prompt for System AI
    """
    try:
        prompt = f"""You are an AI specialized in maritime audit report information extraction.

**INPUT**: Below is the Document AI text extraction from an audit report file.

**FILENAME**: {filename}
(Filename often contains hints about audit type and report form)

**TASK**: Extract the following fields and return as JSON:

{{
    "audit_report_name": "**CRITICAL** - Main title that MUST include document type (Plan/Checklist/Verification/Report/NCR/Minutes)",
    "audit_type": "Type of audit - MUST be one of: ISM, ISPS, MLC, or CICA",
    "report_form": "**CRITICAL** - Form code/number (e.g., '07-23', 'CG (02-19)', 'ISM-AUD-01')",
    "audit_report_no": "**IMPORTANT** - Report number, reference, or authorization number",
    "issued_by": "**IMPORTANT** - Organization that issued/conducted the audit",
    "audit_date": "Date of audit (YYYY-MM-DD format)",
    "auditor_name": "Name(s) of auditor(s) - NOT the organization",
    "ship_name": "Name of ship being audited",
    "ship_imo": "IMO number (7 digits only, no 'IMO:' prefix)",
    "note": "Any important notes or observations"
}}

**CRITICAL INSTRUCTIONS FOR AUDIT_REPORT_NAME**:
- **MUST IDENTIFY DOCUMENT TYPE** - The name MUST clearly indicate what type of document this is
- **DOCUMENT TYPES** (identify and include in name):
  1. **Audit Plan** - "ISM Audit Plan", "ISPS Code Audit Plan"
     - Keywords: "plan", "audit plan", "planning"
  2. **Audit Checklist / Check List** - "ISM Code Checklist", "ISPS Verification Checklist"
     - Keywords: "checklist", "check list", "check-list", "verification checklist"
  3. **Verification Report** - "ISM Code Verification Report", "Ship Safety Verification"
     - Keywords: "verification", "verification report", "verification audit"
  4. **Audit Report** - "ISM Annual Audit Report", "ISPS Compliance Audit"
     - Keywords: "audit report", "audit", "compliance audit", "assessment report"
  5. **NCR (Non-Conformity Report)** - "ISM Code NCR", "Non-Conformity Report"
     - Keywords: "NCR", "non-conformity", "non conformity", "deficiency"
  6. **Meeting Minutes** - "Audit Opening Meeting Minutes", "Closing Meeting Record"
     - Keywords: "meeting", "minutes", "opening meeting", "closing meeting"
  7. **Certificate/Certification** - "ISM Interim Certification", "DOC Certification"
     - Keywords: "certificate", "certification", "certified"
- **FORMAT RULES**:
  - Start with audit type: "ISM", "ISPS", "MLC", or "CICA"
  - Add "Code" if applicable: "ISM Code", "ISPS Code"
  - Add document type: "Audit Plan", "Checklist", "Verification Report"
  - Add timing if relevant: "Annual", "Interim", "Initial", "Renewal"
  - Examples:
    * "ISM Code Audit Plan"
    * "ISPS Code Verification Checklist"
    * "MLC Annual Audit Report"
    * "ISM Code NCR"
    * "ISM Audit Opening Meeting Minutes"
- **DO NOT use generic/vague names** like:
  - ❌ "Record of opening and closing meetings, along with the audit plan"
  - ❌ "International Safety Management audit"
  - ✅ Use: "ISM Code Audit Plan and Meeting Minutes"
  - ✅ Use: "ISM Code Annual Audit Report"

**CRITICAL INSTRUCTIONS FOR REPORT_FORM**:
- **THIS IS THE HIGHEST PRIORITY FIELD - SEARCH EXTENSIVELY**
- **PRIMARY SEARCH LOCATIONS** (in order):
  1. **PAGE FOOTERS** - Bottom of every page (most common location)
  2. **PAGE HEADERS** - Top of every page (second most common)
  3. **DOCUMENT TITLE AREA** - Near the main title/heading
  4. **FIRST PAGE** - Anywhere on the first page, especially corners
  5. **DOCUMENT METADATA SECTION** - "Form:", "Form No:", "Form Number:" labels
- **SEARCH PATTERNS** - Look for these formats:
  - Parentheses format: "(07-23)", "(02-19)", "(05-22)", "(09-25)"
  - Form with text: "Form 7.10", "Form A-123", "Form CG-719"
  - Code with parentheses: "ISM (07-23)", "ISPS-Code (06-23)", "MLC-AUD (05-22)"
  - Hyphenated codes: "ISM-07-23", "ISPS-06-23", "MLC-AUD-05-22"
  - Slash format: "07/23", "02/19" (convert to "07-23", "02-19")
- **FILENAME CLUE**: {filename} (may contain the form code)
- **REPEATING PATTERN**: Form codes often appear on EVERY page in footer/header
- **OCR SECTION**: Check "ADDITIONAL INFORMATION FROM HEADER/FOOTER" carefully
- **IF NOT FOUND**: Return empty string "" (do NOT guess or make up a form code)
- **EXTRACTION RULE**: Extract the COMPLETE form code including prefix and year
  - Examples: 
    * If you see "ISM-Code Audit Plan (07-23)" → Extract "(07-23)" or "ISM-Code Audit Plan (07-23)"
    * If you see "Form 7.10" → Extract "Form 7.10"
    * If you see only "(05-22)" → Extract "(05-22)"

**CRITICAL INSTRUCTIONS FOR ISSUED_BY**:
- **LOOK IN LETTERHEAD/HEADER FIRST** (top of first page)
- Check for company logo, name, address at the top
- May also be in footer with contact information
- Look near phrases: "Issued by", "Audited by", "Conducted by", "Authority"
- Common organizations: DNV GL, Lloyd's Register, Bureau Veritas, PMDS, Class NK, ABS, American Bureau of Shipping
- Extract FULL organization name (e.g., "Det Norske Veritas GL" not just "DNV")
- **DO NOT extract individual auditor names here** (use auditor_name field for that)

**CRITICAL INSTRUCTIONS FOR AUDIT_REPORT_NO**:
- **SEARCH MULTIPLE LABELS** - This field can appear under various names:
  - "Report No:", "Report Number:", "Reference No:", "Ref No:", "Ref:"
  - "Document No:", "Doc No:", "Document Reference:"
  - "Authorization No:", "Authorization Number:", "Auth No:"
  - "Certificate No:", "Cert No:" (for audit certificates)
  - "Audit No:", "Audit Number:", "Audit Reference:"
  - "File No:", "File Number:", "File Reference:"
  - "Serial No:", "Serial Number:"
- **COMMON LOCATIONS**:
  - Document header (top right or left corner)
  - Document footer (bottom of pages)
  - First page near title or letterhead
  - In "Document Information" or "Reference Details" sections
  - Near date or issued_by information
- **FORMAT PATTERNS**:
  - Alphanumeric codes: "AUD-2024-001", "AR-123", "REP-12345"
  - Slash separated: "A/25/1573", "2024/ISM/001", "ISM/2025/123"
  - Dot separated: "REP.2024.001", "AUD.123.456"
  - Hyphen separated: "ISM-2024-001", "AUTH-12345"
  - Simple numbers: "252495874", "PM252495874"
  - Mixed format: "A/25/1573", "PM/2024/001"
- **PRIORITY ORDER**:
  1. Authorization Number (if exists)
  2. Report Number / Reference Number
  3. Document Number
  4. Audit Number
  5. Any other unique identifier
- **IMPORTANT**: If multiple numbers exist, prefer the most specific audit/report/authorization number
- Extract the COMPLETE number including all parts (e.g., "A/25/1573" not just "1573")

**CRITICAL INSTRUCTIONS FOR AUDIT_TYPE**:
- Must be EXACTLY one of: ISM, ISPS, MLC, or CICA
- Check report_form for hints (e.g., "ISM-AUD-01" → ISM)
- Check filename: {filename}
- Check audit_report_name for type indicators
- Normalize variations:
  - "ISM CODE" → ISM
  - "ISPS Code" → ISPS
  - "Maritime Labour Convention" → MLC
  - If unsure, leave empty string

**CRITICAL INSTRUCTIONS FOR AUDITOR_NAME**:
- Extract the name(s) of the individual auditor(s)
- Look for "Auditor:", "Lead Auditor:", "Auditor Name:", "Conducted by (person name)"
- May be listed at the end of the report or in signature sections
- **DO NOT confuse with organization name** (that goes in issued_by)
- Format: "John Smith" or "John Smith, Jane Doe" for multiple auditors

**CRITICAL INSTRUCTIONS FOR SHIP_IMO**:
- Extract ONLY the 7-digit number
- Remove any prefix like "IMO:", "IMO ", "IMO Number:"
- Example: If you see "IMO: 9876543", extract "9876543"

**OUTPUT FORMAT**: Return ONLY valid JSON, no extra text or explanation.

---

**DOCUMENT TEXT:**

{summary_text}
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating audit report extraction prompt: {e}")
        return ""


def extract_report_form_from_filename(filename: str) -> Optional[str]:
    """
    Extract report_form from filename using patterns
    
    Args:
        filename: Original filename
    
    Returns:
        str: Extracted report_form or None
    """
    if not filename:
        return None
    
    patterns = [
        r'\((\d{2}[-/]\d{2,3})\)',                # (07-23), (02-19)
        r'[A-Z]{2,4}\s*\((\d{2}[-/]\d{2,3})\)',  # CG (02-19), ISM (07-23)
        r'Form[_\s]+([A-Z0-9\-\.]+)',            # Form 7.10, Form_ISM-01
        r'[_\-\s](\d{2}[-/]\d{2,3})[_\-\.\s]'    # _07-23_, -02-19.
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None
