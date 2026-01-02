"""
Drawing & Manual AI Extraction Module
Handles System AI extraction for Drawings & Manuals
Based on backend-v1/server.py line 7862-8009 and test_report_ai.py pattern
"""
import logging
import json
import time
from typing import Dict

logger = logging.getLogger(__name__)


def create_drawings_manuals_extraction_prompt(summary_text: str) -> str:
    """
    Create extraction prompt for drawings & manuals fields
    
    Port from backend-v1/server.py line 7938-8009
    
    Args:
        summary_text: Document AI summary text
    
    Returns:
        Extraction prompt for System AI
    """
    try:
        prompt = f"""
You are a maritime technical documentation analysis expert. Extract the following information from the drawings/manual document summary below.

=== FIELDS TO EXTRACT ===

**document_name**: 
- Extract the name/title of the drawing or manual
- Look for phrases like "Drawing Title", "Manual Name", "Document Title", "Subject"
- Common types: "General Arrangement Plan", "Capacity Plan", "Shell Expansion", "Fire Control Plan", "Main Engine Manual", "Electrical System Diagram"
- Be specific and include the system/equipment name

**document_no**: 
- Extract the document number, drawing number, or reference number
- Look for "Drawing No.", "Document No.", "Reference No.", "DWG No.", "Manual No."
- May contain letters, numbers, dashes, slashes (e.g., "GA-001", "DWG-2024-123", "ME-502")
- Include revision numbers if present (e.g., "GA-001 Rev.2")

**approved_by**: 
- Extract who approved or certified this document
- Look for "Approved By", "Certified By", "Checked By", "Classification Society", "Surveyor"
- Common approvers: Lloyd's Register, DNV, ABS, Bureau Veritas, Class NK, shipyard names, naval architects
- May also include person names with titles (e.g., "Chief Engineer John Smith")

**approved_date**: 
- Extract the approval date, certification date, or last updated date
- Look for "Approved Date", "Date of Approval", "Certification Date", "Last Updated", "Issue Date"
- Format: YYYY-MM-DD or any recognizable date format
- This is the date when the document was officially approved/certified

**note**: 
- Extract any important notes, remarks, or additional information
- Look for "Notes", "Remarks", "Special Instructions", "Revision Notes", "Comments"
- Include information about revisions, amendments, or special conditions
- Keep it concise but include important details

=== EXTRACTION RULES ===

1. **Be precise**: Extract exact values as they appear in the document
2. **Handle missing data**: If a field is not found, return an empty string ""
3. **Date formats**: Accept any date format, but prefer YYYY-MM-DD
4. **Document names**: Be specific (e.g., "Main Engine Manual MAN B&W 6S50MC-C" instead of just "Manual")
5. **Abbreviations**: Keep common maritime abbreviations (GA, DWG, etc.)
6. **Revision info**: Include revision numbers in document_no if present

=== DOCUMENT SUMMARY ===

{summary_text}

=== OUTPUT FORMAT ===

Respond ONLY with valid JSON in this EXACT format (no additional text or explanation):

{{
  "document_name": "extracted document name or empty string",
  "document_no": "extracted document number or empty string", 
  "approved_by": "extracted approver or empty string",
  "approved_date": "YYYY-MM-DD or empty string",
  "note": "extracted notes/remarks or empty string"
}}

IMPORTANT: Return ONLY the JSON object, nothing else.
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating drawings & manuals extraction prompt: {e}")
        return ""


async def extract_drawings_manuals_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool,
    filename: str = ""
) -> Dict:
    """
    Extract drawings & manuals fields from Document AI summary using System AI
    
    Port from backend-v1/server.py line 7862-7936
    Based on test_report_ai.py pattern
    
    Args:
        summary_text: Document AI summary text
        ai_provider: AI provider ("google", "openai", "emergent")
        ai_model: Model name ("gemini-2.0-flash-exp", etc.)
        use_emergent_key: Whether to use Emergent LLM key
        filename: Original filename (optional, for logging)
    
    Returns:
        Extracted fields dictionary
    """
    try:
        logger.info(f"🤖 Extracting drawings & manuals fields from summary for: {filename}")
        
        # Create extraction prompt
        prompt = create_drawings_manuals_extraction_prompt(summary_text)
        
        if not prompt:
            logger.error("Failed to create drawings & manuals extraction prompt")
            return {}
        
        # Use System AI for extraction
        if use_emergent_key and ai_provider in ["google", "emergent"]:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                import os
                
                emergent_key = os.getenv("EMERGENT_LLM_KEY")
                if not emergent_key:
                    logger.error("EMERGENT_LLM_KEY not found in environment")
                    return {}
                
                chat = LlmChat(
                    api_key=emergent_key,
                    session_id=f"drawings_manuals_extraction_{int(time.time())}",
                    system_message="You are a maritime technical documentation analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info(f"📥 Drawings & Manuals AI response received ({len(content)} chars)")
                    
                    # Parse JSON response
                    try:
                        # Clean markdown code blocks if present
                        clean_content = content.replace('```json', '').replace('```', '').strip()
                        extracted_data = json.loads(clean_content)
                        
                        # Standardize date formats
                        if extracted_data.get('approved_date'):
                            try:
                                from dateutil import parser
                                parsed_date = parser.parse(extracted_data['approved_date'])
                                extracted_data['approved_date'] = parsed_date.strftime('%Y-%m-%d')
                            except Exception as date_error:
                                logger.warning(f"Failed to parse approved_date: {date_error}")
                        
                        logger.info(f"✅ Successfully extracted drawings & manuals fields")
                        
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
        logger.error(f"Error in extract_drawings_manuals_fields_from_summary: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}
