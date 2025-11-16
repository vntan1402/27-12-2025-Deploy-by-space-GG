"""
Test Report AI Extraction Module
Handles System AI extraction for Test Reports
Port from backend-v1/server.py line 8162-8341
"""
import logging
import json
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def create_test_report_extraction_prompt(summary_text: str) -> str:
    """
    Create extraction prompt for test report fields
    
    Port from backend-v1/server.py line 8162-8341
    
    Args:
        summary_text: Document AI summary + OCR text
    
    Returns:
        Extraction prompt for System AI
    """
    try:
        prompt = f"""
You are a maritime test report data extraction expert. Extract the following information from the test report summary below.

=== FIELDS TO EXTRACT ===

**test_report_name**: 
- This report is about MAINTENANCE/TESTING of LIFESAVING and FIREFIGHTING EQUIPMENT on ships
- Extract the EQUIPMENT NAME that is being tested/maintained, NOT the test type
- Common equipment names to look for:
  * EEBD (Emergency Escape Breathing Device)
  * SCBA (Self-Contained Breathing Apparatus)
  * Portable Fire Extinguisher
  * Portable Foam Applicator
  * Life Raft / Liferaft
  * Lifeboat / Rescue Boat
  * CO2 System / Carbon Dioxide System
  * Fire Detection System / Fire Alarm System
  * Gas Detector / Gas Detection System
  * Immersion Suit / Survival Suit
  * Life Jacket / Lifejacket / Life Vest
  * Hydrostatic Release Unit (HRU)
  * EPIRB (Emergency Position Indicating Radio Beacon)
  * SART (Search and Rescue Transponder)
  * Fire Hose / Fire Fighting Hose
  * Fireman Outfit / Fireman's Outfit
  * Breathing Apparatus
  * Fixed Fire Extinguishing System
  * Sprinkler System
  * Emergency Fire Pump
  * Davit / Launching Appliance
  
- The equipment name will appear MULTIPLE TIMES in the summary text
- The equipment name may also appear in the FILENAME
- Return ONLY the equipment name (e.g., "EEBD", "Life Raft", "Portable Fire Extinguisher")
- Do NOT add "Test" or "Report" to the name
- Use the most common/standard name found in the document
- If multiple equipment mentioned, choose the PRIMARY one being tested

**report_form**: 
- Extract the SERVICE CHART or FORM used for this maintenance/inspection
- Look for patterns like:
  * "Service Chart [LETTER]" - e.g., "Service Chart A", "Service Chart K"
  * "Service Charts [LETTER]/[LETTER]" - e.g., "Service Charts H1/H2"
  * "SERVICE CHART [CODE]" - e.g., "SERVICE CHART B", "SERVICE CHART M"
  * "Chart [CODE]"
  * "Form [NUMBER/LETTER]"
  
- Common patterns:
  * Service Chart A, B, C, D, E, F, G, H, K, L, M, N, etc.
  * Service Charts H1/H2, K1/K2, etc. (combined charts)
  * May be in UPPERCASE or Title Case
  
- Also look for:
  * "Report Form [CODE]"
  * "Form No. [CODE]"
  * "Inspection Form [CODE]"
  
- Extract the complete chart/form identifier exactly as written
- Example outputs: "Service Chart A", "Service Charts H1/H2", "SERVICE CHART K"

**test_report_no**: 
- Extract the test report number or certificate number
- Look for these SPECIFIC phrases:
  * "Test Report No." or "Test Report Number"
  * "Certificate Number" or "Certificate No."
  * "Cert. No."
  * "Report No."
  * "Report Number"
  
- Common formats:
  * Numbers with dashes: "TR-2024-001", "CERT-123-456"
  * Numbers with slashes: "TEST/2024/123", "2024/TR/001"
  * Alphanumeric: "TR123456", "CERT001"
  * With prefixes: "REP-001", "TEST-2024-001"
  
- Extract the complete number/code exactly as written
- May contain letters, numbers, dashes, slashes, dots
- Example: "TR-2024-001", "CERT-123", "TEST/2024/456"

**issued_by**: 
- Extract who issued or conducted the test/maintenance
- **IMPORTANT: Extract ONLY the SHORT NAME, NOT the full legal company name**
- Look for phrases like:
  * "Issued By [COMPANY]"
  * "Tested By [COMPANY]"
  * "Surveyor: [COMPANY]"
  * "Inspector: [COMPANY]"
  * "Service Provider: [COMPANY]"
  * "Conducted by [COMPANY]"
  * "Performed by [COMPANY]"
  
- **Extract SHORT NAME rules:**
  * ✅ "VITECH" (NOT "VITECH Technologies and Services JSC")
  * ✅ "Lloyd's Register" or "LR" (NOT "Lloyd's Register of Shipping")
  * ✅ "DNV" (NOT "Det Norske Veritas")
  * ✅ "ABS" (NOT "American Bureau of Shipping")
  * ✅ "Bureau Veritas" or "BV"
  * ✅ Use the common/trade name, NOT the full legal entity name
  
- If the document mentions both short and full names, prefer the SHORT name
- Remove legal suffixes like: JSC, LLC, Inc., Co., Ltd., Corporation, etc.
- Keep only the core business/brand name

**issued_date**: 
- Extract the ACTUAL DATE when the inspection/maintenance was performed
- This is the date when the SERVICE PROVIDER conducted the test/maintenance on the equipment
- Look for phrases like:
  * "underwent inspection on [DATE]"
  * "The inspection took place on [DATE]"
  * "inspected on [DATE]"
  * "serviced on [DATE]"
  * "tested on [DATE]"
  * "maintenance performed on [DATE]"
  * "date of inspection: [DATE]"
  * "inspection date: [DATE]"
  * "service date: [DATE]"
  
- **IMPORTANT - DO NOT extract date from:**
  * "Rev XX, issued by [COMPANY] on [DATE]" - this is the form revision date, NOT the inspection date
  * "Form issued on [DATE]" - this is the form template date
  * Any date related to form/template issuance or revision
  
- Focus on the date when the ACTUAL WORK was performed on the equipment
- Format: YYYY-MM-DD or any recognizable date format

**valid_date**: 
- Extract the expiry date or next test due date
- Look for "Valid Until", "Expiry Date", "Next Test Due", "Valid Date", "Expires", "Next Service Due"
- This is the date when the test/certificate expires and needs renewal
- Format: YYYY-MM-DD or any recognizable date format

**ship_name**: 
- Extract the ship/vessel name
- Look for "Vessel Name", "Ship Name", "M/V", "MV"

**ship_imo**: 
- Extract the IMO number (7-digit number)
- Look for "IMO No.", "IMO Number"

**note**: 
- Extract any important notes, remarks, observations, or conditions
- Look for "Remarks", "Notes", "Observations", "Conditions", "Comments", "Test Results"
- Include test results, compliance status, special conditions, deficiencies found, or limitations

=== OUTPUT FORMAT ===
Return ONLY a JSON object with these exact field names:
{{
  "test_report_name": "",
  "report_form": "",
  "test_report_no": "",
  "issued_by": "",
  "issued_date": "",
  "valid_date": "",
  "ship_name": "",
  "ship_imo": "",
  "note": ""
}}

**IMPORTANT:**
- For test_report_name: Return ONLY the equipment name (e.g., "EEBD", "Life Raft"), NOT "EEBD Test" or "Life Raft Report"
- Return ONLY the JSON object, no additional text
- Use empty string "" if information is not found
- Dates should be in YYYY-MM-DD format if possible
- Extract verbatim text when possible

=== TEST REPORT SUMMARY ===
{summary_text}

=== YOUR JSON RESPONSE ===
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating test report extraction prompt: {e}")
        return ""


async def extract_test_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool,
    filename: str = ""
) -> Dict:
    """
    Extract test report fields from Document AI summary using System AI
    
    Port from backend-v1/server.py (similar to survey report extraction)
    
    Args:
        summary_text: Document AI summary + OCR text
        ai_provider: AI provider ("google", "openai", "emergent")
        ai_model: Model name ("gemini-2.0-flash-exp", etc.)
        use_emergent_key: Whether to use Emergent LLM key
        filename: Original filename (optional, for logging)
    
    Returns:
        Extracted fields dictionary
    """
    try:
        logger.info(f"🤖 Extracting test report fields from summary for: {filename}")
        
        # Create extraction prompt
        prompt = create_test_report_extraction_prompt(summary_text)
        
        if not prompt:
            logger.error("Failed to create test report extraction prompt")
            return {}
        
        # Use System AI for extraction
        if use_emergent_key and ai_provider in ["google", "emergent"]:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                from app.utils.emergent_key import get_emergent_llm_key
                
                emergent_key = get_emergent_llm_key()
                chat = LlmChat(
                    api_key=emergent_key,
                    session_id=f"test_report_extraction_{int(time.time())}",
                    system_message="You are a maritime test report analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info(f"📥 Test Report AI response received ({len(content)} chars)")
                    
                    # Parse JSON response
                    try:
                        # Clean markdown code blocks if present
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # Standardize date formats
                        for date_field in ['issued_date', 'valid_date']:
                            if extracted_data.get(date_field):
                                try:
                                    from dateutil import parser
                                    parsed_date = parser.parse(extracted_data[date_field])
                                    extracted_data[date_field] = parsed_date.strftime('%Y-%m-%d')
                                except Exception as date_error:
                                    logger.warning(f"Failed to parse {date_field}: {date_error}")
                        
                        logger.info(f"✅ Successfully extracted test report fields")
                        
                        # Log extracted fields for debugging
                        fields_found = [k for k, v in extracted_data.items() if v]
                        logger.info(f"📊 Fields extracted: {', '.join(fields_found)}")
                        
                        return extracted_data
                        
                    except json.JSONDecodeError as json_error:
                        logger.error(f"Failed to parse AI response as JSON: {json_error}")
                        logger.error(f"AI response: {content[:500]}...")
                        return {}
                else:
                    logger.warning("AI response is empty")
                    return {}
                    
            except Exception as ai_error:
                logger.error(f"System AI extraction failed: {ai_error}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {}
        else:
            logger.warning(f"Unsupported AI provider or configuration: {ai_provider}")
            return {}
            
    except Exception as e:
        logger.error(f"Error in extract_test_report_fields_from_summary: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}


def extract_report_form_from_filename(filename: str) -> Optional[str]:
    """
    Extract report form from filename
    
    Args:
        filename: PDF filename
    
    Returns:
        Report form or None
    """
    try:
        import re
        
        # Pattern for Service Chart [LETTER]
        patterns = [
            r'Service\s+Chart\s+([A-Z])',
            r'SERVICE\s+CHART\s+([A-Z])',
            r'Chart\s+([A-Z])',
            r'CHART\s+([A-Z])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                letter = match.group(1).upper()
                return f"Service Chart {letter}"
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting report form from filename: {e}")
        return None
