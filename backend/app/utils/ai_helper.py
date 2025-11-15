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
Analyze this maritime ship certificate document and extract ALL ship information.

Certificate Text:
{text}

Extract and return ONLY a valid JSON object with ALL of the following fields:

{{
  "ship_name": "Full name of the vessel (look for 'NAME OF SHIP', 'Ship Name', 'Vessel Name', 'M.V.', 'S.S.')",
  "imo_number": "IMO number (7 digits, may start with 8 or 9)",
  "flag": "Flag state/country (look for 'Port of Registry', 'Flag', 'Flag State', 'Government of')",
  "class_society": "Classification society or issuing authority FULL NAME (not abbreviation)",
  "built_year": "Year built (4-digit number, extract from delivery date if available)",
  "ship_owner": "Ship owner/registered owner name",
  "ship_type": "Vessel type - MUST be ONE OF: 'General Cargo', 'Bulk Carrier', 'Oil Tanker', 'Chemical Tanker', 'LPG/LNG Carrier', 'Container Ship', 'Passenger Ship', 'Ro-Ro Cargo', 'Fishing Vessel', 'Tug/Supply Vessel', 'Other'",
  "gross_tonnage": "Gross tonnage (numeric only, no units)",
  "deadweight": "Deadweight tonnage (numeric only, no units)",
  "length_overall": "Length overall (LOA) in meters (numeric only)",
  "breadth": "Breadth/width in meters (numeric only)",
  "depth": "Depth in meters (numeric only)",
  "keel_laid": "Date keel was laid - EXACT FORMAT from document (e.g., 'MAY 04, 2018' or '04/05/2018')",
  "delivery_date": "Date of delivery - EXACT FORMAT from document (e.g., 'JANUARY 15, 2019' or '15/01/2019')",
  "place_of_build": "Shipyard/place where ship was built",
  "last_docking": "Most recent dry docking date - EXTRACT EXACTLY AS WRITTEN (e.g., '28 July 2025' or 'JUL 2025')",
  "last_docking_2": "Second most recent dry docking date - EXTRACT EXACTLY AS WRITTEN",
  "next_docking": "Next docking due date - EXTRACT EXACTLY AS WRITTEN",
  "special_survey_from_date": "Special survey period start date in DD/MM/YYYY format",
  "special_survey_to_date": "Special survey period end date in DD/MM/YYYY format"
}}

CRITICAL EXTRACTION RULES:
1. **Ship Type**: If you see a list format like "Type of ship 2)\\nBulk carrier\\nOil tanker", the FIRST item (right after 'Type of ship') is the selected type. Map text to exact format: 'Bulk carrier' → 'Bulk Carrier', 'Oil tanker' → 'Oil Tanker', etc.

2. **Docking Dates**: Search for phrase "the last two inspections of the outside of the ship's bottom took place on [DATE_A] and [DATE_B]". Extract DATE_A for last_docking, DATE_B for last_docking_2. PRESERVE ORIGINAL FORMAT - do NOT convert.

3. **Built Year**: PRIORITY ORDER: (1) Extract year from delivery_date if available, (2) Look for "Year Built", "Built Year". Return 4-digit year only.

4. **Dates Format**: For keel_laid and delivery_date, preserve EXACT format from document. For special survey dates, use DD/MM/YYYY format.

5. **Tonnage/Dimensions**: Extract numeric values ONLY, no units like "MT", "m", "tonnes".

6. **If field not found**: Use null (not empty string)

Return ONLY the JSON object, no markdown code blocks, no explanation.
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
