"""
AI extraction utilities for Approval Documents
- Extract fields from Document AI summary using System AI
"""
import logging
import json
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)


async def extract_approval_document_fields_from_summary(
    summary_text: str,
    ai_provider: str,
    ai_model: str,
    use_emergent_key: bool
) -> Dict:
    """
    Extract approval document fields from Document AI summary using System AI
    
    Fields to extract:
    - approval_document_name
    - approval_document_no
    - approved_by
    - approved_date
    - note
    
    Args:
        summary_text: Document AI summary text
        ai_provider: AI provider (google, emergent)
        ai_model: AI model name (e.g., gemini-2.0-flash-exp)
        use_emergent_key: Whether to use Emergent LLM key
    
    Returns:
        dict: Extracted fields or empty dict on failure
    """
    try:
        logger.info("🤖 Extracting approval document fields from summary")
        
        # Create extraction prompt
        prompt = create_approval_document_extraction_prompt(summary_text)
        
        if not prompt:
            logger.error("Failed to create approval document extraction prompt")
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
                    session_id=f"approval_document_extraction_{int(time.time())}",
                    system_message="You are a maritime regulatory documentation analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    content = ai_response.strip()
                    logger.info("🤖 Approval Document AI response received")
                    
                    # Parse JSON response
                    try:
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
                        
                        logger.info("✅ Successfully extracted approval document fields")
                        return extracted_data
                        
                    except json.JSONDecodeError as json_error:
                        logger.error(f"Failed to parse AI response as JSON: {json_error}")
                        return {}
                else:
                    logger.warning("AI response is empty")
                    return {}
                    
            except Exception as ai_error:
                logger.error(f"System AI extraction failed: {ai_error}")
                return {}
        else:
            logger.warning(f"Unsupported AI provider or configuration: {ai_provider}")
            return {}
            
    except Exception as e:
        logger.error(f"Error in extract_approval_document_fields_from_summary: {e}")
        return {}


def create_approval_document_extraction_prompt(summary_text: str) -> str:
    """
    Create extraction prompt for approval document fields
    
    Args:
        summary_text: Document AI summary text
    
    Returns:
        str: Formatted prompt for System AI
    """
    try:
        prompt = f"""
You are a maritime regulatory documentation analysis expert. Extract the following information from the approval document summary below.

=== FIELDS TO EXTRACT ===

**approval_document_name**: 
- Extract the name/title of the approval document
- Look for phrases like "Document Title", "Approval Title", "Subject", "Certificate Name"
- Common types: "Safety Management System Approval", "Security Plan Approval", "ISM Code Compliance", "ISPS Approval Certificate", "MLC Declaration of Maritime Labour Compliance"
- Be specific and include the type of approval (ISM, ISPS, MLC, DOC, SMC, etc.)

**approval_document_no**: 
- Extract the document number, approval number, or certificate number
- Look for "Document No.", "Approval No.", "Certificate No.", "Reference No.", "DOC No.", "SMC No."
- May contain letters, numbers, dashes, slashes (e.g., "ISM-2024-001", "DOC-123456", "SMC/2024/789")
- Include any prefix or suffix codes

**approved_by**: 
- Extract who approved or issued this document
- Look for "Approved By", "Issued By", "Certified By", "Authority", "Administration", "Flag State"
- Common approvers: Classification societies (DNV, LR, ABS, BV, etc.), Flag administrations, Port State Control, RO (Recognized Organization)
- May include full organization names or abbreviations

**approved_date**: 
- Extract the approval date, issue date, or certification date
- Look for "Approval Date", "Issue Date", "Date of Approval", "Certification Date", "Effective Date"
- Format: YYYY-MM-DD or any recognizable date format
- This is the date when the document was officially approved/issued

**note**: 
- Extract any important notes, remarks, conditions, or limitations
- Look for "Notes", "Remarks", "Conditions", "Limitations", "Special Requirements", "Validity Conditions"
- Include information about scope, limitations, or special conditions of approval
- Keep it concise but include important regulatory details

=== EXTRACTION RULES ===

1. **Be precise**: Extract exact values as they appear in the document
2. **Handle missing data**: If a field is not found, return an empty string ""
3. **Date formats**: Accept any date format, but prefer YYYY-MM-DD
4. **Document names**: Be specific and include the type (e.g., "DOC - Document of Compliance ISM Code" instead of just "DOC")
5. **Abbreviations**: Keep common maritime abbreviations (ISM, ISPS, MLC, DOC, SMC, etc.)
6. **Authority names**: Use full names when available (e.g., "Det Norske Veritas" instead of just "DNV")

=== DOCUMENT SUMMARY ===

{summary_text}

=== OUTPUT FORMAT ===

Respond ONLY with valid JSON in this EXACT format (no additional text or explanation):

{{
  "approval_document_name": "extracted document name or empty string",
  "approval_document_no": "extracted document number or empty string", 
  "approved_by": "extracted approver/issuer or empty string",
  "approved_date": "YYYY-MM-DD or empty string",
  "note": "extracted notes/remarks or empty string"
}}

IMPORTANT: Return ONLY the JSON object, nothing else.
"""
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating approval document extraction prompt: {e}")
        return ""
