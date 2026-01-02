"""
Text Layer Correction Utility
Uses Gemini AI to correct OCR errors in extracted text layers
"""
import logging
import os
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Prompt template for text correction - ENHANCED VERSION
TEXT_CORRECTION_PROMPT = """You are an expert OCR error correction specialist. Your task is to fix ALL OCR/scanning errors in the following maritime document text.

CRITICAL RULES - FIX ALL THESE ERROR TYPES:

1. CHARACTER SUBSTITUTION ERRORS:
   - "l" confused with "1", "I", "|"  
   - "0" confused with "O", "o"
   - "rN" → "IN", "wITH" → "WITH"
   - ":" or ";" appearing inside words (e.g., "Authoriz:tion" → "Authorization")
   - "Nnmber" → "Number", "MARITTME" → "MARITIME"
   - Random capital letters in middle of words

2. GARBLED TEXT - MUST FIX:
   - "du[y qiiiti6d aJditot" → "duly qualified auditor"
   - "I hcre is rcd th" → "I hereby certify that"
   - "lntcrim" → "Interim"
   - "Compctcnt" → "Competent"
   - Any text that doesn't make sense in English

3. COMMON MARITIME TERMS TO CORRECT:
   - MARITIME, LABOUR, CONVENTION, CERTIFICATE
   - AUTHORIZATION, VERIFICATION, INSPECTION
   - SEAFARER, SHIPOWNER, TONNAGE, REGISTRY
   - COMPLIANCE, REGULATION, AMENDMENT

4. PRESERVE EXACTLY (DO NOT CHANGE):
   - All numbers (IMO: 9544011, dates, certificate numbers)
   - Ship names (TRUONG MINH SEA)
   - Company names
   - Codes like MLC, SOLAS, ISM, ISPS
   - Table structure and formatting

5. OUTPUT RULES:
   - Fix ALL spelling errors aggressively
   - If a word is garbled beyond recognition, use context to determine correct word
   - Keep original document structure (headers, sections, tables)
   - Output ONLY the corrected text, no explanations

ORIGINAL TEXT WITH OCR ERRORS:
{text}

CORRECTED TEXT (fix ALL errors):"""

# Alternative shorter prompt for smaller texts
TEXT_CORRECTION_PROMPT_SHORT = """Fix ALL OCR errors in this maritime document. Be aggressive - fix every misspelled word, garbled text, character substitution error. Preserve numbers/codes exactly. Output only corrected text:

{text}

CORRECTED:"""


async def correct_text_layer_with_ai(
    text_content: str,
    filename: str,
    ai_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Use Gemini AI to correct OCR errors in extracted text layer
    
    Args:
        text_content: Raw text extracted from PDF text layer
        filename: Original filename for logging
        ai_config: AI configuration (optional)
        
    Returns:
        Dict with:
        - success: bool
        - corrected_text: str (corrected text if success)
        - original_text: str (original text for reference)
        - correction_applied: bool (whether corrections were made)
        - error: str (error message if failed)
    """
    import time
    
    start_time = time.time()
    logger.info(f"🔧 Starting text layer correction for: {filename}")
    logger.info(f"   📊 Original text length: {len(text_content)} characters")
    
    result = {
        "success": False,
        "corrected_text": None,
        "original_text": text_content,
        "correction_applied": False,
        "error": None,
        "processing_time": 0
    }
    
    try:
        # Get AI configuration
        provider = "google"
        model = "gemini-2.0-flash"
        
        if ai_config:
            provider = ai_config.get("provider", "google")
            model = ai_config.get("model", "gemini-2.0-flash")
        
        # Choose prompt based on text length
        if len(text_content) > 10000:
            # For very long texts, use shorter prompt to save tokens
            prompt = TEXT_CORRECTION_PROMPT_SHORT.format(text=text_content)
        else:
            prompt = TEXT_CORRECTION_PROMPT.format(text=text_content)
        
        logger.info(f"   🤖 Using {provider}/{model} for text correction")
        
        # Call AI using LlmChat - it handles API key selection automatically
        from app.utils.llm_wrapper import LlmChat, UserMessage
        
        # Initialize LlmChat with ai_config for proper API key selection
        chat = LlmChat(
            ai_config=ai_config,  # Pass config for API key selection
            session_id="text_layer_correction",
            system_message="You are an expert document OCR correction assistant."
        )
        
        # Set provider and model
        actual_model = model or "gemini-2.0-flash"
        if "gemini" in actual_model.lower() or provider.lower() in ["google", "gemini"]:
            chat = chat.with_model("gemini", actual_model)
        elif provider.lower() == "openai" or "gpt" in actual_model.lower():
            chat = chat.with_model("openai", actual_model)
        else:
            chat = chat.with_model("gemini", actual_model)
        
        # Send message
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Process response
        corrected_text = response if isinstance(response, str) else ""
        corrected_text = corrected_text.strip()
        
        # Validate response
        if not corrected_text or len(corrected_text) < len(text_content) * 0.5:
            # Response too short - likely an error or summary
            logger.warning(f"⚠️ Corrected text too short ({len(corrected_text)} vs {len(text_content)} original)")
            result["success"] = True
            result["corrected_text"] = text_content  # Use original
            result["correction_applied"] = False
            result["note"] = "AI response too short, using original text"
        else:
            # Success - use corrected text
            result["success"] = True
            result["corrected_text"] = corrected_text
            result["correction_applied"] = True
            
            # Log some stats
            original_words = len(text_content.split())
            corrected_words = len(corrected_text.split())
            logger.info(f"   ✅ Correction complete: {original_words} → {corrected_words} words")
        
        elapsed = time.time() - start_time
        result["processing_time"] = round(elapsed, 2)
        logger.info(f"⏱️ Text correction completed in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Text correction failed: {e}")
        result["error"] = str(e)
        result["corrected_text"] = text_content  # Fallback to original
        result["correction_applied"] = False
    
    return result


def detect_ocr_quality(text_content: str) -> Dict[str, Any]:
    """
    Analyze text quality to detect if it needs OCR correction
    
    Returns quality metrics:
    - quality_score: 0-100 (100 = perfect text)
    - needs_correction: bool
    - issues_detected: list of detected issues
    """
    if not text_content:
        return {
            "quality_score": 0,
            "needs_correction": True,
            "issues_detected": ["Empty text"]
        }
    
    issues = []
    
    # Check 1: Ratio of alphabetic vs non-alphabetic characters
    alpha_chars = sum(1 for c in text_content if c.isalpha())
    total_chars = len(text_content.replace(" ", "").replace("\n", ""))
    alpha_ratio = alpha_chars / max(total_chars, 1)
    
    if alpha_ratio < 0.6:
        issues.append(f"Low alphabetic ratio: {alpha_ratio:.2%}")
    
    # Check 2: Common OCR error patterns
    ocr_error_patterns = [
        r'[a-z]:[a-z]',  # Colon in middle of word like "Authoriz:tion"
        r'[A-Z]{2,}[a-z][A-Z]',  # Mixed caps like "MARITTME" 
        r'\b[a-z]{1,2}[A-Z][a-z]',  # Weird caps like "rN" or "wITH"
        r'[a-zA-Z]\d[a-zA-Z]',  # Number in middle of word
        r'[a-zA-Z][;:,][a-zA-Z]',  # Punctuation in middle of word
    ]
    
    error_count = 0
    for pattern in ocr_error_patterns:
        matches = re.findall(pattern, text_content)
        error_count += len(matches)
    
    if error_count > 10:
        issues.append(f"Many OCR error patterns detected: {error_count}")
    
    # Check 3: Common maritime words detection
    maritime_words = [
        'certificate', 'ship', 'vessel', 'maritime', 'tonnage', 'cargo',
        'safety', 'international', 'convention', 'inspection', 'survey',
        'class', 'registry', 'port', 'flag', 'imo', 'mlc', 'solas'
    ]
    
    text_lower = text_content.lower()
    found_words = sum(1 for word in maritime_words if word in text_lower)
    
    if found_words < 3:
        issues.append(f"Few maritime keywords found: {found_words}")
    
    # Calculate quality score
    quality_score = 100
    quality_score -= min(30, (1 - alpha_ratio) * 50)  # Up to -30 for low alpha ratio
    quality_score -= min(30, error_count * 2)  # Up to -30 for OCR errors
    quality_score += min(20, found_words * 3)  # Bonus for maritime words
    quality_score = max(0, min(100, quality_score))
    
    needs_correction = quality_score < 70 or error_count > 5
    
    return {
        "quality_score": round(quality_score),
        "needs_correction": needs_correction,
        "issues_detected": issues,
        "alpha_ratio": round(alpha_ratio, 2),
        "ocr_error_count": error_count,
        "maritime_words_found": found_words
    }
