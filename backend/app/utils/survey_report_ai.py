"""
Survey Report AI Extraction Utilities
Handles AI-powered field extraction from survey reports
"""
import logging
import json
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def extract_survey_report_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool,
    filename: str = ""
) -> Dict[str, Any]:
    """
    Extract survey report fields from Document AI summary using System AI
    
    Args:
        summary_text: Enhanced summary text (with OCR)
        ai_provider: "google" or "openai"
        ai_model: Model name (e.g., "gemini-2.0-flash")
        use_emergent_key: Whether to use Emergent LLM key
        filename: Original filename (helps identify report form)
    
    Returns:
        Dict with extracted fields
    """
    try:
        if not use_emergent_key:
            logger.warning("AI extraction requires Emergent key configuration")
            return {}
        
        # Build extraction prompt
        prompt = create_survey_report_extraction_prompt(summary_text, filename)
        
        # Call AI based on provider
        if ai_provider in ["google", "emergent"]:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            from app.core.config import settings
            
            # Get Emergent LLM key
            emergent_key = settings.EMERGENT_LLM_KEY
            if not emergent_key:
                logger.error("EMERGENT_LLM_KEY not configured")
                return {}
            
            # Use LlmChat with correct initialization pattern
            chat = LlmChat(
                api_key=emergent_key,
                session_id="survey_report_analysis",
                system_message="You are an AI assistant specialized in maritime survey report information extraction."
            )
            
            # Set provider and model correctly
            actual_model = ai_model or "gemini-2.0-flash-exp"
            
            # Check if model is Gemini (regardless of provider value)
            if "gemini" in actual_model.lower() or ai_provider.lower() in ["google", "gemini", "emergent"]:
                # For Gemini models with Emergent key
                chat = chat.with_model("gemini", actual_model)
                logger.info(f"🔄 Using Gemini model: {actual_model} (provider: {ai_provider})")
            elif ai_provider.lower() == "openai" or "gpt" in actual_model.lower():
                chat = chat.with_model("openai", actual_model)
                logger.info(f"🔄 Using OpenAI model: {actual_model}")
            elif ai_provider.lower() == "anthropic" or "claude" in actual_model.lower():
                chat = chat.with_model("anthropic", actual_model)
                logger.info(f"🔄 Using Anthropic model: {actual_model}")
            else:
                # Default: try Gemini
                chat = chat.with_model("gemini", actual_model)
                logger.warning(f"⚠️ Unknown provider: {ai_provider}, defaulting to Gemini with model: {actual_model}")
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            if response:
                # LlmChat returns content directly
                content = response if isinstance(response, str) else ''
                
                if content:
                    # Parse JSON response
                    try:
                        # Extract JSON from markdown code blocks if present
                        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                        if json_match:
                            content = json_match.group(1)
                        
                        extracted_data = json.loads(content)
                        logger.info("✅ Survey report fields extracted successfully")
                        
                        # Try to extract report_form from filename if not found
                        if not extracted_data.get('report_form') and filename:
                            filename_form = extract_report_form_from_filename(filename)
                            if filename_form:
                                extracted_data['report_form'] = filename_form
                                logger.info(f"✅ Extracted report_form from filename: '{filename_form}'")
                        
                        return extracted_data
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse survey report extraction JSON: {e}")
                        logger.debug(f"AI Response: {content}")
                        return {}
                else:
                    logger.error("No content in survey report AI extraction response")
                    return {}
        else:
            logger.warning(f"AI provider '{ai_provider}' not yet supported for survey reports")
            return {}
            
    except Exception as e:
        logger.error(f"Survey report field extraction error: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        return {}


def extract_report_form_from_filename(filename: str) -> Optional[str]:
    """
    Extract report form from filename patterns
    
    Examples:
        "CG (02-19).pdf" → "CG (02-19)"
        "CU 02-19.pdf" → "CU (02-19)"
        "AS (03/20).pdf" → "AS (03/20)"
    """
    filename_form_patterns = [
        r'([A-Z]{1,3})\s*\(([0-9]{2}[-/][0-9]{2})\)',  # CG (02-19) or CG (02/19)
        r'([A-Z]{1,3})\s+([0-9]{2}[-/][0-9]{2})',      # CG 02-19 or CG 02/19
        r'([A-Z]{1,3})[-_]([0-9]{2}[-/][0-9]{2})',     # CG-02-19 or CG_02/19
    ]
    
    for pattern in filename_form_patterns:
        match = re.search(pattern, filename)
        if match:
            abbrev = match.group(1)
            date_part = match.group(2).replace('/', '-')
            extracted_form = f"{abbrev} ({date_part})"
            return extracted_form
    
    return None


def create_survey_report_extraction_prompt(summary_text: str, filename: str = "") -> str:
    """
    Create AI prompt for extracting survey report fields
    """
    prompt = f"""You are an AI specialized in maritime survey report information extraction.

Your task:
Analyze the following text summary of a maritime survey report and extract all key fields.

**IMPORTANT CONTEXT:**
- Original filename: {filename}
- The filename often contains the Report Form (e.g., "CG (02-19).pdf" → Report Form is "CG (02-19)")

=== INSTRUCTIONS ===
1. Extract only the survey report fields listed below.
2. Return the output strictly in valid JSON format.
3. If a field is not found, leave it as an empty string "".
4. Normalize all dates to format "DD/MM/YYYY" (e.g., "15/01/2024").
5. Do not infer or fabricate any missing information.

=== FIELD EXTRACTION RULES ===

**survey_report_name**: 
- Extract ONLY the equipment/system being surveyed, NOT the survey type
- REMOVE survey type words like: "Annual", "Special", "Intermediate", "Close-up", "Docking", "Survey", "Record", "Report"
- Examples:
  * "survey record for cargo gear" → Extract: "cargo gear"
  * "close-up survey of ballast tanks" → Extract: "ballast tanks"
  * "annual survey of main engine" → Extract: "main engine"
- Common subjects: cargo gear, ballast tanks, hull structure, machinery, boilers, main engine, steering gear

**report_form**: 
- Extract the report form identifier used for this survey
- **PRIORITY**: Check FILENAME first - often contains the report form
  * Example: Filename "CG (02-19).pdf" → Report Form is "CG (02-19)"
- Often appears in HEADER or FOOTER sections
- Common patterns: "CU (02/19)", "AS (03/20)", "PS (01/21)", "CG (02-19)"
  * "CU" = Close-up, "AS" = Annual Survey, "PS" = Pre-Survey, "CG" = Cargo Gear

**survey_report_no**: 
- Extract the report number or reference number
- Look for "Report No.", "Report Number", "Reference No.", "Survey No."
- May contain letters, numbers, dashes (e.g., "SR-2024-001")

**issued_by**: 
- Extract the classification society or organization
- Common: Lloyd's Register, DNV, ABS, BV, Class NK, RINA

**issued_date**: 
- Extract the date when the report was issued/completed
- Look for "Issued Date", "Report Date", "Date of Survey", "Completion Date"
- Convert to DD/MM/YYYY format
- **IMPORTANT**: ONLY extract if it's clearly a DATE
- DO NOT extract form codes that look like dates (e.g., "CU (02/19)" is a FORM, not a date)

**ship_name**: 
- Extract the vessel name mentioned in the report

**ship_imo**: 
- Extract IMO number (7 digits starting with 8 or 9)

**surveyor_name**: 
- Extract the name(s) of surveyor(s) who conducted the survey

**status**: 
- Determine if the survey passed or failed
- Return "Valid" if passed, "Expired" if failed or expired

**note**: 
- Extract any important notes, recommendations, or deficiencies found
- Keep concise (max 200 characters)

=== OUTPUT FORMAT ===

Return ONLY a valid JSON object with these exact fields:

{{
  "survey_report_name": "",
  "report_form": "",
  "survey_report_no": "",
  "issued_by": "",
  "issued_date": "",
  "ship_name": "",
  "ship_imo": "",
  "surveyor_name": "",
  "status": "Valid",
  "note": ""
}}

=== DOCUMENT TEXT TO ANALYZE ===

{summary_text[:8000]}

=== EXTRACTION RULES REMINDER ===
- survey_report_name: ONLY the equipment/system (NO "survey", "report", "annual", etc.)
- issued_date: DD/MM/YYYY format (e.g., "15/01/2024")
- status: "Valid" or "Expired"
- Return ONLY the JSON object, no markdown code blocks, no explanations.
"""
    
    return prompt
