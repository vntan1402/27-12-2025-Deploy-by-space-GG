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
    Based on backend-v1 proven prompts
    
    Args:
        summary_text: Document summary text
        filename: Original filename (can help identify report form)
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
4. Normalize all dates to ISO format "YYYY-MM-DD".
5. Do not infer or fabricate any missing information.
6. **For survey_report_name**: Combine information from (a) document beginning, (b) report_form abbreviation, (c) frequently mentioned equipment/systems
7. **Cross-validation**: If report_form contains abbreviations (e.g., "CG", "BT", "CU"), use them to identify what equipment is being surveyed

=== FIELD EXTRACTION RULES ===

**survey_report_name**: 
- **CRITICAL FORMAT**: Extract ONLY the equipment/system being surveyed, NOT the survey type
- **REMOVE survey type words**: Do NOT include "Annual", "Special", "Intermediate", "Close-up", "Docking", "Survey", "Record", "Report"
- **ONLY extract the SUBJECT**: 
  * "survey record for cargo gear" → Extract: "cargo gear"
  * "close-up survey of ballast tanks" → Extract: "ballast tanks"
  * "annual survey of main engine" → Extract: "main engine"
  * "docking survey for hull structure" → Extract: "hull structure"
- **Look at first sentences** like:
  * "This document is a survey record... for cargo gear" → Extract: "cargo gear"
  * "This is a close-up survey of ballast tanks" → Extract: "ballast tanks"
  * "Annual survey report for main engine" → Extract: "main engine"
- **Cross-validate with report_form**: 
  * If form is "CG (02/19)", CG = Cargo Gear → extract "cargo gear"
  * If form is "BT (01/20)", BT = Ballast Tank → extract "ballast tanks"
  * If form is "ME (05/21)", ME = Main Engine → extract "main engine"
- **Check document content**: The equipment/system should appear FREQUENTLY throughout the document
- Common subjects: cargo gear, ballast tanks, hull structure, machinery, boilers, main engine, steering gear, cranes, derricks, lifts, tank coating, fire fighting equipment
- **DO NOT include**: "survey", "report", "record", "annual", "special", "close-up", "docking", etc.

**report_form**: 
- Extract the report form or form type/number used for this survey
- **CRITICAL 1**: Check the FILENAME first - often contains the report form
  * Example: Filename "CG (02-19).pdf" → Report Form is "CG (02-19)"
  * Example: Filename "CU 02-19.pdf" → Report Form is "CU (02-19)" or "CU 02-19"
  * If filename contains pattern like "[A-Z]+ \([0-9]{{2}}[-/][0-9]{{2}}\)", extract it as report_form
- **CRITICAL 2**: Often appears in HEADER or FOOTER sections
- **Common patterns**: Abbreviations of survey types followed by numbers/dates
  * Examples: "CU (02/19)", "AS (03/20)", "PS (01/21)", "DS 02-19", "CG (02-19)"
  * "CU" = Close-up, "AS" = Annual Survey, "PS" = Pre-Survey, "DS" = Docking Survey, "CG" = Cargo Gear
- **Look for**: "Report Form", "Form No.", "Form Type", "Survey Form", "Form Used"
- **Also check**: Abbreviations related to survey_report_name (e.g., if survey is "Close-up Survey", look for "CU")
- May contain codes like "P&I Form", "Class Form A", "Form 001", etc.
- Extract the complete form identifier as mentioned in the document
- **DO NOT confuse with dates**: Forms may look like dates (e.g., "CU (02/19)") but are form identifiers
- **PRIORITY**: Filename > Header/Footer > Document body

**survey_report_no**: 
- Extract the report number or reference number
- Look for "Report No.", "Report Number", "Reference No.", "Survey No."
- May contain letters, numbers, dashes, slashes (e.g., "SR-2024-001", "AS/2024/123", "A/25/772")

**issued_by**: 
- Extract the classification society or organization that issued this report
- Common societies: Lloyd's Register, DNV, ABS, BV, Class NK, RINA, Panama Maritime Documentation Services (PMDS)
- Look for "Classification Society", "Issued by", "Surveyor Society"

**issued_date**: 
- Extract the date when the report was issued/completed
- Look for "Issued Date", "Report Date", "Date of Survey", "Completion Date", "Completion", "Date"
- Convert to ISO format "YYYY-MM-DD"
- **IMPORTANT**: ONLY extract if it's clearly a DATE (e.g., "15 January 2024", "2024-01-15", "15/01/2024")
- **DO NOT extract** form codes or abbreviations that look like dates (e.g., "CU (02/19)" is a FORM, not a date)
- If uncertain whether something is a date or form code, leave issued_date EMPTY and put the value in report_form instead

**ship_name**: 
- Extract the ACTUAL VESSEL NAME mentioned in the report
- Look for fields labeled: "Vessel Name", "Ship Name", "Name of Vessel", "Name of Ship"
- **CRITICAL - DO NOT CONFUSE WITH SHIP TYPE**:
  * Ship types: "BULK CARRIER", "TANKER", "CONTAINER SHIP", "GENERAL CARGO", "OTHER CARGO", "OFFSHORE SUPPLY VESSEL"
  * These are NOT ship names - they describe the TYPE of vessel
  * If you see "Type of Ship: OTHER CARGO" → DO NOT use "OTHER CARGO" as ship_name
  * If you see "Type of Ship: BULK CARRIER" → DO NOT use "BULK CARRIER" as ship_name
- **What IS a ship name**: Proper nouns identifying specific vessels
  * Examples: "BROTHER 36", "PACIFIC STAR", "OCEAN GLORY", "MINH ANH 09", "LUCKY STAR"
  * May include prefixes like "M/V", "MT", "M.V.", "M.T."
- **If actual ship name is NOT found**: Return empty string ""
- **DO NOT make assumptions** - only extract if explicitly labeled as ship name

**ship_imo**: 
- Extract the IMO number (International Maritime Organization number)
- Look for "IMO Number", "IMO No.", "IMO:"
- Format: 7 digits (e.g., "9876543", "8743531", "IMO 9876543")
- Extract only the 7-digit number

**surveyor_name**: 
- Extract the name of the surveyor(s) who conducted the survey
- Look for "Surveyor", "Surveyor Name", "Inspected by", "Attended by"
- May be one or multiple names

**note**: 
- Extract any important findings, recommendations, or remarks
- Look for "Findings", "Remarks", "Recommendations", "Observations"
- Summarize key points if text is long (max 200 words)

=== EXTRACTION EXAMPLES ===

**Example 1: Cargo Gear Survey**
Document beginning: "This document is a survey record, authorization number A/25/772, from PMDS for cargo gear, derricks, cranes, ramps, and personal/cargo lifts"
Report form: "CG (02-19)"
Frequent terms: "cargo gear" mentioned 15+ times
→ survey_report_name: "cargo gear"  ✅ (NOT "survey record for cargo gear")
→ report_form: "CG (02-19)"

**Example 2: Close-up Survey**
Document beginning: "This is a close-up survey of ballast tanks and hull structure"
Report form: "CU (02/19)"
Frequent terms: "ballast tank", "close-up", "tank coating"
→ survey_report_name: "ballast tanks"  ✅ (NOT "close-up survey of ballast tanks")
→ report_form: "CU (02/19)"

**Example 3: Annual Survey**
Document beginning: "Annual survey report for main engine and auxiliary machinery"
Report form: "AS (03/20)"
Frequent terms: "main engine", "machinery", "annual"
→ survey_report_name: "main engine"  ✅ (NOT "annual survey of main engine")
→ report_form: "AS (03/20)"

=== OUTPUT FORMAT ===
Return ONLY a JSON object with these exact field names:
{{
  "survey_report_name": "",
  "report_form": "",
  "survey_report_no": "",
  "issued_by": "",
  "issued_date": "",
  "ship_name": "",
  "ship_imo": "",
  "surveyor_name": "",
  "note": "",
  "status": "Valid"
}}

=== DOCUMENT TEXT ===
{summary_text}

=== YOUR RESPONSE ===
Extract the fields and return ONLY the JSON object (no other text):"""
    
    return prompt
