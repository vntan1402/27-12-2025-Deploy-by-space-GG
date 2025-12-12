"""
Company Certificate AI Analysis Utility
Extract: cert_name, cert_no, issue_date, valid_date, issued_by
"""
import logging
from typing import Dict, Optional
from emergentintegrations import ChatOpenAI

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
        ai_config: AI configuration
        
    Returns:
        Dict with extracted fields
    """
    try:
        llm = ChatOpenAI(
            api_key=ai_config.get('api_key'),
            model=ai_config.get('model', 'gpt-4o'),
            temperature=0.0
        )
        
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

        response = await llm.ainvoke(prompt)
        result_text = response.content.strip()
        
        # Clean JSON response
        if result_text.startswith('```json'):
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif result_text.startswith('```'):
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        import json
        extracted_data = json.loads(result_text)
        
        logger.info(f"✅ AI extracted fields: {list(extracted_data.keys())}")
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
