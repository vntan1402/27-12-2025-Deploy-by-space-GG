"""
PDF Text Layer Extraction Utility
Extracts native text layer from PDF files (non-OCR)
"""
import logging
import io
from typing import Dict, Any, Tuple, Optional
import pdfplumber

logger = logging.getLogger(__name__)

# Constants
TEXT_LAYER_THRESHOLD = 400  # Minimum characters to consider text layer valid


def parse_pdf_once(file_bytes: bytes, filename: str = "unknown.pdf") -> Dict[str, Any]:
    """
    Parse PDF một lần duy nhất và trả về tất cả thông tin cần thiết.
    Tối ưu memory bằng cách chỉ mở file 1 lần.
    
    Args:
        file_bytes: PDF file bytes
        filename: Original filename for logging
        
    Returns:
        Dict with:
        - page_count: int
        - text_content: str (full extracted text)
        - char_count: int
        - has_text_layer: bool (>= TEXT_LAYER_THRESHOLD chars)
        - success: bool
        - error: str (if failed)
    """
    result = {
        "page_count": 0,
        "text_content": "",
        "char_count": 0,
        "has_text_layer": False,
        "success": False,
        "error": None
    }
    
    try:
        logger.info(f"📄 Parsing PDF once: {filename}")
        
        pdf_file = io.BytesIO(file_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            result["page_count"] = page_count
            
            all_text = []
            
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        all_text.append(f"--- Page {i} ---\n{page_text}\n")
                except Exception as e:
                    logger.warning(f"⚠️ Error reading page {i}: {e}")
                    continue
            
            full_text = "\n".join(all_text)
            char_count = len(full_text.strip())
            
            result["text_content"] = full_text
            result["char_count"] = char_count
            result["has_text_layer"] = char_count >= TEXT_LAYER_THRESHOLD
            result["success"] = True
            
            logger.info(f"   ✅ Parsed: {page_count} pages, {char_count} chars, has_text_layer={result['has_text_layer']}")
            
    except Exception as e:
        logger.error(f"❌ PDF parse failed for {filename}: {e}")
        result["error"] = str(e)
    
    return result


def quick_check_text_layer(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Quick synchronous check if PDF has sufficient text layer
    This is a fast operation (~100ms) to decide fast/slow path
    
    Args:
        file_bytes: PDF file bytes
        filename: Original filename
        
    Returns:
        Dict with:
        - has_sufficient_text: bool (>= TEXT_LAYER_THRESHOLD chars)
        - text_content: str (extracted text if sufficient)
        - char_count: int
        - page_count: int
    """
    try:
        logger.info(f"⚡ Quick text layer check for: {filename}")
        
        pdf_file = io.BytesIO(file_bytes)
        
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            all_text = []
            
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        all_text.append(f"--- Page {i} ---\n{page_text}\n")
                except Exception as e:
                    logger.warning(f"⚠️ Error reading page {i}: {e}")
                    continue
            
            full_text = "\n".join(all_text)
            char_count = len(full_text.strip())
            has_sufficient = char_count >= TEXT_LAYER_THRESHOLD
            
            logger.info(f"   📊 Pages: {page_count}, Characters: {char_count}, Sufficient: {has_sufficient}")
            
            return {
                "has_sufficient_text": has_sufficient,
                "text_content": full_text if has_sufficient else None,
                "char_count": char_count,
                "page_count": page_count,
                "threshold": TEXT_LAYER_THRESHOLD
            }
            
    except Exception as e:
        logger.error(f"❌ Quick text check failed for {filename}: {e}")
        return {
            "has_sufficient_text": False,
            "text_content": None,
            "char_count": 0,
            "page_count": 0,
            "error": str(e)
        }


def format_text_layer_summary(text_content: str, filename: str, page_count: int, char_count: int, document_type: str = "certificate") -> str:
    """
    Format extracted text layer into summary format
    
    Args:
        text_content: Extracted text from PDF
        filename: Original filename
        page_count: Number of pages
        char_count: Character count
        document_type: Type of document ("certificate" or "survey_report")
        
    Returns:
        Formatted summary string
    """
    summary_parts = []
    
    # Determine title based on document type
    if document_type == "survey_report":
        title = "SURVEY REPORT SUMMARY - TEXT LAYER EXTRACTION"
    else:
        title = "CERTIFICATE SUMMARY - TEXT LAYER EXTRACTION"
    
    # Header
    summary_parts.append("=" * 80)
    summary_parts.append(title)
    summary_parts.append(f"File: {filename}")
    summary_parts.append(f"Processing: FAST PATH (Native PDF Text)")
    summary_parts.append("=" * 80)
    summary_parts.append("")
    
    # Content info
    summary_parts.append("=" * 80)
    summary_parts.append("TEXT LAYER CONTENT (Native PDF Text)")
    summary_parts.append(f"Source: Direct extraction from PDF text layer")
    summary_parts.append(f"Pages: {page_count}")
    summary_parts.append(f"Characters: {char_count}")
    summary_parts.append("=" * 80)
    summary_parts.append("")
    
    # Actual content
    summary_parts.append(text_content)
    summary_parts.append("")
    
    return "\n".join(summary_parts)


async def extract_text_layer_from_pdf(
    file_content: bytes,
    filename: str
) -> Dict[str, Any]:
    """
    Extract text layer from PDF file (non-OCR)
    
    Args:
        file_content: PDF file bytes
        filename: Original filename
        
    Returns:
        Dict with:
        - success: bool
        - text: str (full extracted text)
        - page_count: int
        - has_text_layer: bool
        - pages: list of dict (text per page)
    """
    try:
        logger.info(f"📝 Extracting text layer from: {filename}")
        
        # Open PDF with pdfplumber
        pdf_file = io.BytesIO(file_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            logger.info(f"   Total pages: {page_count}")
            
            # Extract text from each page
            pages_data = []
            all_text = []
            has_text = False
            
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                    
                    if page_text.strip():
                        has_text = True
                        
                    pages_data.append({
                        "page_number": i,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
                    
                    all_text.append(f"--- Page {i} ---\n{page_text}\n")
                    
                except Exception as page_error:
                    logger.warning(f"   ⚠️ Error extracting page {i}: {page_error}")
                    pages_data.append({
                        "page_number": i,
                        "text": "",
                        "char_count": 0,
                        "error": str(page_error)
                    })
            
            # Combine all text
            full_text = "\n".join(all_text)
            total_chars = len(full_text.strip())
            
            logger.info(f"✅ Text layer extraction complete:")
            logger.info(f"   - Pages: {page_count}")
            logger.info(f"   - Has text layer: {has_text}")
            logger.info(f"   - Total characters: {total_chars}")
            
            return {
                "success": True,
                "text": full_text,
                "page_count": page_count,
                "has_text_layer": has_text,
                "total_characters": total_chars,
                "pages": pages_data
            }
            
    except Exception as e:
        logger.error(f"❌ Failed to extract text layer from {filename}: {e}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "text": "",
            "page_count": 0,
            "has_text_layer": False,
            "total_characters": 0,
            "pages": [],
            "error": str(e)
        }


def extract_text_from_pdf_text_layer(file_content: bytes) -> str:
    """
    Extract text from PDF text layer (compatibility function)
    
    Args:
        file_content: PDF file bytes
        
    Returns:
        Extracted text string
    """
    try:
        pdf_file = io.BytesIO(file_content)
        
        with pdfplumber.open(pdf_file) as pdf:
            all_text = []
            
            for page in pdf.pages:
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        all_text.append(page_text)
                except Exception:
                    continue
            
            return "\n".join(all_text)
            
    except Exception as e:
        logger.error(f"❌ Failed to extract text layer: {e}")
        return ""


def create_summary_from_text_layer(text_content: str, filename: str) -> str:
    """
    Create summary from text layer content (compatibility function)
    
    Args:
        text_content: Extracted text content
        filename: Original filename
        
    Returns:
        Formatted summary string
    """
    return format_text_layer_summary(
        text_content=text_content,
        filename=filename,
        page_count=text_content.count("--- Page"),
        char_count=len(text_content),
        document_type="survey_report"
    )


def merge_text_layer_and_document_ai(
    text_layer_result: Dict[str, Any],
    document_ai_result: Dict[str, Any],
    filename: str
) -> str:
    """
    Merge text layer and Document AI results into a single summary
    
    Format:
    ===== TEXT LAYER CONTENT =====
    [Native PDF text if available]
    
    ===== DOCUMENT AI OCR CONTENT =====
    [Document AI extracted text]
    
    Args:
        text_layer_result: Result from extract_text_layer_from_pdf()
        document_ai_result: Result from Document AI
        filename: Original filename
        
    Returns:
        Merged summary text
    """
    try:
        logger.info(f"🔀 Merging text layer + Document AI for: {filename}")
        
        summary_parts = []
        
        # Header
        summary_parts.append("=" * 80)
        summary_parts.append("CERTIFICATE SUMMARY - ENHANCED EXTRACTION")
        summary_parts.append(f"File: {filename}")
        summary_parts.append("=" * 80)
        summary_parts.append("")
        
        # Part 1: Text Layer
        has_text_layer = text_layer_result.get("has_text_layer", False)
        text_layer_content = text_layer_result.get("text", "").strip()
        
        if has_text_layer and text_layer_content:
            summary_parts.append("=" * 80)
            summary_parts.append("PART 1: TEXT LAYER CONTENT (Native PDF Text)")
            summary_parts.append(f"Source: Direct extraction from PDF text layer")
            summary_parts.append(f"Pages: {text_layer_result.get('page_count', 0)}")
            summary_parts.append(f"Characters: {text_layer_result.get('total_characters', 0)}")
            summary_parts.append("=" * 80)
            summary_parts.append("")
            summary_parts.append(text_layer_content)
            summary_parts.append("")
            logger.info(f"   ✅ Text layer included: {len(text_layer_content)} chars")
        else:
            summary_parts.append("=" * 80)
            summary_parts.append("PART 1: TEXT LAYER CONTENT")
            summary_parts.append("Status: No text layer found (scanned/image PDF)")
            summary_parts.append("=" * 80)
            summary_parts.append("")
            logger.info(f"   ⚠️ No text layer found")
        
        # Part 2: Document AI
        doc_ai_success = document_ai_result.get("success", False)
        doc_ai_content = document_ai_result.get("data", {}).get("summary", "").strip()
        
        if doc_ai_success and doc_ai_content:
            summary_parts.append("=" * 80)
            summary_parts.append("PART 2: DOCUMENT AI OCR CONTENT")
            summary_parts.append("Source: Google Document AI (OCR + Layout Analysis)")
            summary_parts.append(f"Confidence: {document_ai_result.get('data', {}).get('confidence', 0.0)}")
            summary_parts.append("=" * 80)
            summary_parts.append("")
            summary_parts.append(doc_ai_content)
            summary_parts.append("")
            logger.info(f"   ✅ Document AI included: {len(doc_ai_content)} chars")
        else:
            summary_parts.append("=" * 80)
            summary_parts.append("PART 2: DOCUMENT AI OCR CONTENT")
            summary_parts.append("Status: Document AI processing failed or returned empty")
            summary_parts.append("=" * 80)
            summary_parts.append("")
            logger.info(f"   ⚠️ Document AI content not available")
        
        # Footer
        summary_parts.append("=" * 80)
        summary_parts.append("END OF SUMMARY")
        summary_parts.append("=" * 80)
        
        merged_text = "\n".join(summary_parts)
        
        logger.info(f"✅ Merge complete: {len(merged_text)} total characters")
        
        return merged_text
        
    except Exception as e:
        logger.error(f"❌ Error merging text layer and Document AI: {e}")
        
        # Fallback: return what we have
        fallback_parts = [
            "=" * 80,
            "CERTIFICATE SUMMARY (Fallback Mode)",
            f"File: {filename}",
            "=" * 80,
            ""
        ]
        
        if text_layer_result.get("text"):
            fallback_parts.append("TEXT LAYER:")
            fallback_parts.append(text_layer_result.get("text", ""))
            fallback_parts.append("")
        
        if document_ai_result.get("data", {}).get("summary"):
            fallback_parts.append("DOCUMENT AI:")
            fallback_parts.append(document_ai_result.get("data", {}).get("summary", ""))
        
        return "\n".join(fallback_parts)
