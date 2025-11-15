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
  "last_docking": "Most recent dry docking date - FORMAT: dd/MM/yyyy if full date available (e.g., '28/07/2025'), OR MM/yyyy if only month/year (e.g., '07/2025')",
  "last_docking_2": "Second most recent dry docking date - FORMAT: dd/MM/yyyy if full date available, OR MM/yyyy if only month/year",
  "next_docking": "Next docking due date - FORMAT: dd/MM/yyyy if full date available, OR MM/yyyy if only month/year",
  "special_survey_from_date": "Special survey period start date in DD/MM/YYYY format",
  "special_survey_to_date": "Special survey period end date in DD/MM/YYYY format"
}}

CRITICAL EXTRACTION RULES:
1. **Ship Type**: If you see a list format like "Type of ship 2)\\nBulk carrier\\nOil tanker", the FIRST item (right after 'Type of ship') is the selected type. Map text to exact format: 'Bulk carrier' → 'Bulk Carrier', 'Oil tanker' → 'Oil Tanker', etc.

2. **Docking Dates**: Search for phrase "the last two inspections of the outside of the ship's bottom took place on [DATE_A] and [DATE_B]". Extract DATE_A for last_docking, DATE_B for last_docking_2. NORMALIZE FORMAT:
   - If full date (e.g., "28 July 2025", "July 28, 2025"): Convert to dd/MM/yyyy (e.g., "28/07/2025")
   - If only month/year (e.g., "JUL 2025", "July 2025"): Convert to MM/yyyy (e.g., "07/2025")
   - Month names: January=01, February=02, March=03, April=04, May=05, June=06, July=07, August=08, September=09, October=10, November=11, December=12

3. **Built Year**: PRIORITY ORDER: (1) Extract year from delivery_date if available, (2) Look for "Year Built", "Built Year". Return 4-digit year only.

4. **Dates Format**: 
   - For keel_laid and delivery_date: preserve EXACT format from document
   - For special survey dates: use dd/MM/yyyy format
   - For docking dates (last_docking, last_docking_2, next_docking): 
     * Full date → dd/MM/yyyy (e.g., "28/07/2025")
     * Month/year only → MM/yyyy (e.g., "07/2025")

5. **Tonnage/Dimensions**: Extract numeric values ONLY, no units like "MT", "m", "tonnes".

6. **If field not found**: Use null (not empty string)

Return ONLY the JSON object, no markdown code blocks, no explanation.

EXAMPLE OUTPUT FORMAT:
{{
  "ship_name": "M.V. SUNSHINE EXPRESS",
  "imo_number": "9876543",
  "flag": "PANAMA",
  "class_society": "Lloyd's Register",
  "built_year": "2019",
  "ship_owner": "ABC Shipping Co., Ltd.",
  "ship_type": "Bulk Carrier",
  "gross_tonnage": "25000",
  "deadweight": "45000",
  "length_overall": "180",
  "breadth": "32",
  "depth": "18",
  "keel_laid": "MAY 04, 2018",
  "delivery_date": "JANUARY 15, 2019",
  "place_of_build": "Hyundai Heavy Industries",
  "last_docking": "28/07/2025",
  "last_docking_2": "09/08/2023",
  "next_docking": "07/2027",
  "special_survey_from_date": "15/01/2024",
  "special_survey_to_date": "15/01/2029"
}}
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
            
            # Clean and validate data - include ALL ship fields
            cleaned_data = {
                # Classification
                "category": data.get("category"),
                "confidence": data.get("confidence"),
                "text_content": data.get("text_content"),
                
                # Ship identification
                "ship_name": data.get("ship_name"),
                "imo_number": data.get("imo_number"),
                "flag": data.get("flag"),
                "class_society": data.get("class_society"),
                "ship_owner": data.get("ship_owner"),
                "ship_type": data.get("ship_type"),
                
                # Ship specifications
                "built_year": data.get("built_year"),
                "gross_tonnage": data.get("gross_tonnage"),
                "deadweight": data.get("deadweight"),
                "length_overall": data.get("length_overall"),
                "breadth": data.get("breadth"),
                "depth": data.get("depth"),
                
                # Build/construction dates
                "keel_laid": data.get("keel_laid"),
                "delivery_date": data.get("delivery_date"),
                "place_of_build": data.get("place_of_build"),
                
                # Docking and survey dates
                "last_docking": data.get("last_docking"),
                "last_docking_2": data.get("last_docking_2"),
                "next_docking": data.get("next_docking"),
                "special_survey_from_date": data.get("special_survey_from_date"),
                "special_survey_to_date": data.get("special_survey_to_date"),
                
                # Certificate fields
                "cert_name": data.get("cert_name"),
                "cert_type": data.get("cert_type"),
                "cert_no": data.get("cert_no"),
                "issue_date": data.get("issue_date"),
                "valid_date": data.get("valid_date"),
                "last_endorse": data.get("last_endorse"),
                "issued_by": data.get("issued_by")
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
        
        # Optional fields - ALL ship and certificate fields
        for field in ["cert_type", "last_endorse", "issued_by", "ship_name", 
                     "imo_number", "flag", "class_society", "built_year",
                     "gross_tonnage", "deadweight",
                     # Ship-specific fields
                     "ship_type", "ship_owner", "delivery_date", "keel_laid",
                     "place_of_build", "length_overall", "breadth", "depth",
                     # Docking and survey fields
                     "last_docking", "last_docking_2", "next_docking",
                     "special_survey_from_date", "special_survey_to_date"]:
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
