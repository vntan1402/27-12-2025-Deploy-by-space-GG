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
    "company_name": "Company name on the certificate",
    "doc_type": "DOC type classification (only for DOC certificates)",
    "issue_date": "Issue date in DD/MM/YYYY format",
    "valid_date": "Valid/expiry date in DD/MM/YYYY format",
    "last_endorse": "Last endorsement date in DD/MM/YYYY format",
    "issued_by": "Issuing authority/organization"
}}

IMPORTANT INSTRUCTIONS:
1. cert_name and cert_no are REQUIRED fields
2. company_name: Extract the company name (look for "Name of the Company:", "Company:", etc.)
3. doc_type: **CRITICAL - MANDATORY FOR ALL DOC CERTIFICATES** - You MUST classify every DOC:
   
   **Step 0: SPECIAL CASES - Full Term Indicators (HIGHEST PRIORITY):**
   a) If document contains BOTH "Full term Certificate No" AND "Interim Certificate No"
      OR contains BOTH "Full Term Document" AND "Interim Document"
      → **MUST return "full_term"**
   
   b) If document contains "Last Endorse" OR "Last Endorsed" OR "Endorsement date"
      → **MUST return "full_term"**
      (Only Full Term DOCs have endorsement dates)
   
   **Step 1: Search for "SHORT TERM" keywords:**
   - "Short Term Certificate No"
   - "SHORT TERM DOCUMENT OF COMPLIANCE"
   - "Short Term Document"
   - "SHORT TERM" (anywhere in text)
   - "short term"
   - If found ANY of above (and NO Last Endorse) → **MUST return "short_term"**
   
   **Step 2: If not Short Term, search for "INTERIM":**
   - "Interim Certificate No"
   - "Interim Document of Compliance"
   - "INTERIM DOCUMENT"
   - "Interim Certificate"
   - "INTERIM" (anywhere in text)
   - If found → **CHECK Step 0 first** (if has Last Endorse OR both Full Term + Interim, return "full_term")
   - If only Interim found (no Last Endorse) → **MUST return "interim"**
   
   **Step 3: If not Short Term or Interim, search for "FULL TERM":**
   - "Full term Certificate No"
   - "Full Term Document of Compliance"
   - "FULL TERM DOCUMENT"
   - "Full Term Certificate"
   - "FULL TERM" (anywhere in text)
   - If found ANY of above → **MUST return "full_term"**
   
   **Step 4: Default for DOC without keywords:**
   - If certificate IS "Document of Compliance" but no keywords found → return "full_term"
   - If NOT a Document of Compliance → return ""
   
   **CRITICAL RULES:**
   - READ THE ENTIRE TEXT CAREFULLY before deciding
   - Check for "Last Endorse" FIRST - if found, always return "full_term"
   - Check for BOTH "Full term Certificate No" AND "Interim Certificate No"
   - Keywords can appear ANYWHERE in the document (title, body, footer)
   - CASE INSENSITIVE search (SHORT TERM = short term)
   - NEVER return null or empty for a DOC certificate
   - Priority: (Has Last Endorse) > (Full Term + Interim together) > short_term > interim alone > full_term alone
4. ALL dates MUST be converted to DD/MM/YYYY format (e.g., "18/11/2024")
5. Look for dates with keywords:
   - issue_date: "Date of issue", "Issued", "Issue date"
   - valid_date: "Valid until", "Expiry", "This Document is valid until", "Date of expiry"
   - last_endorse: "Last endorsement", "Endorsed", "Last endorsed on", "Endorsement date"
6. If issue_date is "NOVEMBER 18, 2024", convert it to "18/11/2024"
7. If valid_date is "OCTOBER 7, 2029", convert it to "07/10/2029"
8. If last_endorse is "MARCH 15, 2023", convert it to "15/03/2023"
9. If a field cannot be found, use empty string ""
10. Return ONLY valid JSON, no markdown, no explanation

EXAMPLE OUTPUT:
{{
    "cert_name": "DOCUMENT OF COMPLIANCE",
    "cert_no": "PM242633",
    "company_name": "HAI AN CONTAINER TRANSPORT COMPANY LIMITED",
    "doc_type": "full_term",
    "issue_date": "18/11/2024",
    "valid_date": "07/10/2029",
    "last_endorse": "15/03/2023",
    "issued_by": "Panama Maritime Documentation Services, Inc."
}}

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
        logger.info(f"   🏢 Company Name: '{extracted_data.get('company_name', '')}'")
        logger.info(f"   📑 DOC Type: '{extracted_data.get('doc_type', '')}'")
        logger.info(f"   📅 Issue Date: '{extracted_data.get('issue_date', '')}'")
        logger.info(f"   📅 Valid Date: '{extracted_data.get('valid_date', '')}'")
        logger.info(f"   📝 Last Endorse: '{extracted_data.get('last_endorse', '')}'")
        logger.info(f"   🏛️ Issued By: '{extracted_data.get('issued_by', '')}'")
        return extracted_data
        
    except Exception as e:
        logger.error(f"❌ AI extraction error: {e}")
        return {
            "cert_name": "",
            "cert_no": "",
            "company_name": "",
            "doc_type": "",
            "issue_date": "",
            "valid_date": "",
            "last_endorse": "",
            "issued_by": ""
        }
