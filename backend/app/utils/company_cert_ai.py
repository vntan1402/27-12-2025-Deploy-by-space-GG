"""
Company Certificate AI Analysis Utility
Extract: cert_name, cert_no, issue_date, valid_date, issued_by
"""
import logging
import json
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

async def extract_company_cert_fields_from_summary(
    summary_text: str,
    filename: str,
    ai_config: Dict
) -> Dict:
    """
    Extract company certificate fields from summary text using AI
    
    Args:
        summary_text: Text content extracted from PDF
        filename: Original filename
        ai_config: AI configuration with provider, model, use_emergent_key
        
    Returns:
        Dict with extracted fields
    """
    try:
        logger.info("🤖 Extracting company cert fields from summary")
        
        # Get AI config
        ai_provider = ai_config.get("provider", "google")
        ai_model = ai_config.get("model", "gemini-2.0-flash")
        use_emergent_key = ai_config.get("use_emergent_key", True)
        
        # Create extraction prompt
        prompt = f"""You are a maritime document expert. Extract information from this company certificate.

DOCUMENT TEXT:
{summary_text}

FILENAME: {filename}

Extract the following fields in JSON format:
{{
    "cert_name": "Full certificate name",
    "cert_no": "Certificate number",
    "issue_date": "Issue date in DD/MM/YYYY format",
    "valid_date": "Valid/expiry date in DD/MM/YYYY format (or null if no expiry)",
    "issued_by": "Issuing authority/organization"
}}

IMPORTANT:
- cert_name and cert_no are REQUIRED
- Dates must be in DD/MM/YYYY format
- If a field cannot be found, use empty string ""
- If valid_date is not applicable (no expiry), use null
- Return ONLY valid JSON, no explanation

RESPOND WITH VALID JSON ONLY:"""

        # Use Emergent LLM integration
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
                    session_id=f"company_cert_extraction_{int(time.time())}",
                    system_message="You are a maritime document analysis expert."
                ).with_model("gemini", ai_model)
                
                logger.info(f"📤 Sending extraction prompt to {ai_model}...")
                
                # Send extraction request
                user_message = UserMessage(text=prompt)
                ai_response = await chat.send_message(user_message)
                
                if ai_response and ai_response.strip():
                    result_text = ai_response.strip()
                    logger.info("🤖 Company Cert AI response received")
                else:
                    logger.error("Empty AI response")
                    return {}
                
            except Exception as e:
                logger.error(f"❌ Emergent LLM error: {e}")
                return {}
        else:
            logger.error(f"Unsupported AI provider: {ai_provider}")
            return {}
        
        # Clean JSON response
        if result_text.startswith('```json'):
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif result_text.startswith('```'):
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        extracted_data = json.loads(result_text)
        
        logger.info(f"✅ AI extracted fields: {list(extracted_data.keys())}")
        logger.info(f"   📋 Cert Name: '{extracted_data.get('cert_name', '')}'")
        logger.info(f"   🔢 Cert No: '{extracted_data.get('cert_no', '')}'")
        logger.info(f"   📅 Issue Date: '{extracted_data.get('issue_date', '')}'")
        logger.info(f"   📅 Valid Date: '{extracted_data.get('valid_date', '')}'")
        logger.info(f"   🏛️ Issued By: '{extracted_data.get('issued_by', '')}'")
        return extracted_data
        
    except Exception as e:
        logger.error(f"❌ AI extraction error: {e}")
        return {
            "cert_name": "",
            "cert_no": "",
            "issue_date": "",
            "valid_date": "",
            "issued_by": ""
        }
