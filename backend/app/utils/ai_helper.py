import logging
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class AIHelper:
    """Utility class for AI-related operations"""
    
    @staticmethod
    def create_certificate_analysis_prompt(text: str, ship_id: Optional[str] = None) -> str:
        """
        Create prompt for AI to analyze certificate
        
        Args:
            text: Certificate text content
            ship_id: Optional ship ID if analyzing for specific ship
            
        Returns:
            str: Formatted prompt for AI
        """
        prompt = f"""
You are a maritime document expert. Analyze the following ship certificate and extract key information.

Certificate Text:
{text}

Please extract and return ONLY a valid JSON object with the following fields:
{{
  "cert_name": "Full certificate name/title (e.g., CARGO SHIP SAFETY CONSTRUCTION CERTIFICATE)",
  "cert_type": "Certificate type: Full Term, Interim, Provisional, Short Term, or null if not found",
  "cert_no": "Certificate number",
  "issue_date": "Issue date in DD/MM/YYYY format",
  "valid_date": "Valid until/expiry date in DD/MM/YYYY format",
  "last_endorse": "Last endorsement date in DD/MM/YYYY format or null",
  "issued_by": "Issuing authority/organization",
  "ship_name": "Ship name from certificate",
  "imo_number": "IMO number (7 digits) or null",
  "flag": "Flag state/country or null",
  "class_society": "Classification society or null",
  "built_year": "Year built (YYYY format) or null",
  "gross_tonnage": "Gross tonnage (numeric value) or null",
  "deadweight": "Deadweight tonnage (numeric value) or null"
}}

IMPORTANT:
- Return ONLY the JSON object, no additional text or explanation
- Use DD/MM/YYYY format for all dates
- If a field is not found or unclear, use null
- For cert_type, identify if it's Full Term, Interim, Provisional, or Short Term
- Extract numeric values without units for tonnage fields
- IMO number should be exactly 7 digits
"""
        return prompt
    
    @staticmethod
    def parse_ai_response(response_text: str) -> Dict[str, Any]:
        """
        Parse AI response and extract certificate data
        
        Args:
            response_text: Raw AI response text
            
        Returns:
            Dict: Parsed certificate data
        """
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
            else:
                # If no JSON found, try to parse the whole response
                data = json.loads(response_text)
            
            # Clean and validate data
            cleaned_data = {
                "cert_name": data.get("cert_name"),
                "cert_type": data.get("cert_type"),
                "cert_no": data.get("cert_no"),
                "issue_date": data.get("issue_date"),
                "valid_date": data.get("valid_date"),
                "last_endorse": data.get("last_endorse"),
                "issued_by": data.get("issued_by"),
                "ship_name": data.get("ship_name"),
                "imo_number": data.get("imo_number"),
                "flag": data.get("flag"),
                "class_society": data.get("class_society"),
                "built_year": data.get("built_year"),
                "gross_tonnage": data.get("gross_tonnage"),
                "deadweight": data.get("deadweight")
            }
            
            return cleaned_data
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"Response text: {response_text}")
            return {}
    
    @staticmethod
    def validate_certificate_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean certificate data
        
        Args:
            data: Raw certificate data from AI
            
        Returns:
            Dict: Validated and cleaned data
        """
        validated = {}
        
        # Required fields
        for field in ["cert_name", "cert_no", "issue_date", "valid_date"]:
            validated[field] = data.get(field)
        
        # Optional fields
        for field in ["cert_type", "last_endorse", "issued_by", "ship_name", 
                     "imo_number", "flag", "class_society", "built_year",
                     "gross_tonnage", "deadweight"]:
            value = data.get(field)
            validated[field] = value if value and str(value).lower() not in ["null", "none", ""] else None
        
        # Validate IMO number format (7 digits)
        if validated.get("imo_number"):
            imo = str(validated["imo_number"]).strip()
            if not re.match(r'^\d{7}$', imo):
                # Try to extract 7 digits
                imo_match = re.search(r'\d{7}', imo)
                validated["imo_number"] = imo_match.group(0) if imo_match else None
        
        # Convert numeric fields
        for field in ["built_year", "gross_tonnage", "deadweight"]:
            if validated.get(field):
                try:
                    # Extract numeric value
                    num_str = str(validated[field])
                    num_match = re.search(r'[\d,]+\.?\d*', num_str)
                    if num_match:
                        num_val = float(num_match.group(0).replace(',', ''))
                        validated[field] = int(num_val) if field == "built_year" else num_val
                    else:
                        validated[field] = None
                except:
                    validated[field] = None
        
        return validated
    
    @staticmethod
    def calculate_confidence_score(data: Dict[str, Any], text_length: int) -> float:
        """
        Calculate confidence score for AI extraction
        
        Args:
            data: Extracted certificate data
            text_length: Length of source text
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        score = 0.0
        
        # Check required fields (40% of score)
        required_fields = ["cert_name", "cert_no", "issue_date", "valid_date"]
        required_count = sum(1 for f in required_fields if data.get(f))
        score += (required_count / len(required_fields)) * 0.4
        
        # Check optional important fields (30% of score)
        important_fields = ["issued_by", "ship_name", "cert_type"]
        important_count = sum(1 for f in important_fields if data.get(f))
        score += (important_count / len(important_fields)) * 0.3
        
        # Check text quality (30% of score)
        if text_length > 500:
            score += 0.3
        elif text_length > 200:
            score += 0.2
        elif text_length > 100:
            score += 0.1
        
        return min(score, 1.0)
