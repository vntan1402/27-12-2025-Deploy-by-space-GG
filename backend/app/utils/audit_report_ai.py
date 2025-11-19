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
        # Backend V1 lines 7176-7232
        if filename:
            filename_form_patterns = [
                r'\((\d{2}[-/]\d{2,3})\)',           # (07-23), (02-19)
                r'[A-Z]{2,4}\s*\((\d{2}[-/]\d{2,3})\)',  # CG (02-19), ISM (07-23)
                r'Form[_\s]+([A-Z0-9\-\.]+)',        # Form 7.10, Form_ISM-01
                r'[_\-\s](\d{2}[-/]\d{2,3})[_\-\.\s]'    # _07-23_, -02-19.
            ]
            
            filename_form = None
            for pattern in filename_form_patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    filename_form = match.group(1)
                    break
            
            # Override AI extraction if filename has clear pattern
            if filename_form and (not extracted_data.get('report_form') or len(extracted_data.get('report_form', '')) < 5):
                logger.info(f"✅ Extracted report_form from filename: '{filename_form}' (overriding AI: '{extracted_data.get('report_form', '')}')")
                extracted_data['report_form'] = filename_form
        
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
    "audit_report_name": "Main title or name of audit report",
    "audit_type": "Type of audit - MUST be one of: ISM, ISPS, MLC, or CICA",
    "report_form": "**CRITICAL** - Form code/number (e.g., '07-23', 'CG (02-19)', 'ISM-AUD-01')",
    "audit_report_no": "Report number or reference",
    "issued_by": "**IMPORTANT** - Organization that issued/conducted the audit",
    "audit_date": "Date of audit (YYYY-MM-DD format)",
    "auditor_name": "Name(s) of auditor(s) - NOT the organization",
    "ship_name": "Name of ship being audited",
    "ship_imo": "IMO number (7 digits only, no 'IMO:' prefix)",
    "note": "Any important notes or observations"
}}

**CRITICAL INSTRUCTIONS FOR REPORT_FORM**:
- **LOOK IN FOOTER/HEADER SECTIONS FIRST** (bottom and top of pages)
- May appear as: "(07-23)", "Form 7.10", "CG (02-19)", "ISM (05-22)", etc.
- Often repeats on every page in header/footer
- Check "ADDITIONAL INFORMATION FROM HEADER/FOOTER (OCR Extraction)" section
- Filename hint: {filename}
- This is the MOST IMPORTANT field - spend extra effort to find it

**CRITICAL INSTRUCTIONS FOR ISSUED_BY**:
- **LOOK IN LETTERHEAD/HEADER FIRST** (top of first page)
- Check for company logo, name, address at the top
- May also be in footer with contact information
- Look near phrases: "Issued by", "Audited by", "Conducted by", "Authority"
- Common organizations: DNV GL, Lloyd's Register, Bureau Veritas, PMDS, Class NK, ABS, American Bureau of Shipping
- Extract FULL organization name (e.g., "Det Norske Veritas GL" not just "DNV")
- **DO NOT extract individual auditor names here** (use auditor_name field for that)

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
