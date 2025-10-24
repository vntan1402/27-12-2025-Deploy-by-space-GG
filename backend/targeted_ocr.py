"""
Targeted OCR for Header/Footer Extraction
Improves accuracy of Report No. and Report Form extraction from Survey Reports
"""
import logging
import re
import io
from typing import Dict, Optional, Tuple
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Try to import pytesseract, handle if not available
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("✅ Tesseract OCR available")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("⚠️ Tesseract OCR not available")

# Try to import pdf2image
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
    logger.info("✅ pdf2image available")
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("⚠️ pdf2image not available")


class TargetedOCRProcessor:
    """
    Targeted OCR processor for extracting Report No. and Report Form
    from header/footer regions of Survey Reports
    """
    
    def __init__(self, header_percent: float = 0.15, footer_percent: float = 0.15):
        """
        Initialize OCR processor
        
        Args:
            header_percent: Percentage of page height for header (default: 15%)
            footer_percent: Percentage of page height for footer (default: 15%)
        """
        self.header_percent = header_percent
        self.footer_percent = footer_percent
        
        # Configure Tesseract path explicitly
        if TESSERACT_AVAILABLE:
            # Try to set tesseract command path
            import shutil
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                logger.info(f"✅ Tesseract path configured: {tesseract_path}")
            else:
                # Try common paths
                common_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract']
                for path in common_paths:
                    import os
                    if os.path.exists(path):
                        pytesseract.pytesseract.tesseract_cmd = path
                        logger.info(f"✅ Tesseract path configured: {path}")
                        break
                else:
                    logger.warning("⚠️ Tesseract command not found in common paths")
        
        # Check if Tesseract is available
        if not TESSERACT_AVAILABLE:
            logger.warning("⚠️ Tesseract OCR not installed. OCR functionality will be disabled.")
        
        # Check if pdf2image is available
        if not PDF2IMAGE_AVAILABLE:
            logger.warning("⚠️ pdf2image not installed. Cannot convert PDF to images.")
    
    def is_available(self) -> bool:
        """Check if OCR is available"""
        return TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE
    
    def extract_from_pdf(self, pdf_content: bytes, page_num: int = 0) -> Dict[str, Optional[str]]:
        """
        Extract report_form and survey_report_no from PDF header/footer
        
        Args:
            pdf_content: PDF file content as bytes
            page_num: Page number to process (default: first page)
        
        Returns:
            Dict with extracted fields and metadata:
            {
                'report_form': str or None,
                'survey_report_no': str or None,
                'header_text': str,
                'footer_text': str,
                'ocr_success': bool,
                'ocr_error': str or None
            }
        """
        result = {
            'report_form': None,
            'survey_report_no': None,
            'header_text': '',
            'footer_text': '',
            'ocr_success': False,
            'ocr_error': None
        }
        
        if not self.is_available():
            result['ocr_error'] = "OCR not available (Tesseract or pdf2image not installed)"
            logger.warning(f"⚠️ {result['ocr_error']}")
            return result
        
        try:
            logger.info(f"🔍 Starting targeted OCR extraction for page {page_num}")
            
            # Convert PDF to images
            images = convert_from_bytes(
                pdf_content,
                first_page=page_num + 1,
                last_page=page_num + 1,
                dpi=300  # High DPI for better OCR accuracy
            )
            
            if not images:
                result['ocr_error'] = "Failed to convert PDF to image"
                logger.error(f"❌ {result['ocr_error']}")
                return result
            
            page_image = images[0]
            logger.info(f"📄 Page image size: {page_image.size}")
            
            # Extract header and footer text
            header_text = self._extract_header(page_image)
            footer_text = self._extract_footer(page_image)
            
            result['header_text'] = header_text
            result['footer_text'] = footer_text
            
            logger.info(f"📋 Header text length: {len(header_text)} chars")
            logger.info(f"📋 Footer text length: {len(footer_text)} chars")
            
            # Extract fields using pattern matching
            combined_text = header_text + "\n" + footer_text
            
            # Extract report_form
            report_form = self._extract_report_form(combined_text)
            if report_form:
                result['report_form'] = report_form
                logger.info(f"✅ Extracted report_form: '{report_form}'")
            
            # Extract survey_report_no
            survey_report_no = self._extract_report_no(combined_text)
            if survey_report_no:
                result['survey_report_no'] = survey_report_no
                logger.info(f"✅ Extracted survey_report_no: '{survey_report_no}'")
            
            result['ocr_success'] = True
            logger.info(f"✅ Targeted OCR completed successfully")
            
        except Exception as e:
            result['ocr_error'] = str(e)
            logger.error(f"❌ Targeted OCR failed: {e}")
        
        return result
    
    def _extract_header(self, image: Image.Image) -> str:
        """Extract text from header region (top 15%)"""
        width, height = image.size
        header_height = int(height * self.header_percent)
        
        # Crop header region
        header_region = image.crop((0, 0, width, header_height))
        
        # Preprocess for better OCR
        header_region = self._preprocess_image(header_region)
        
        # OCR
        text = pytesseract.image_to_string(
            header_region,
            lang='eng',
            config='--psm 6 --oem 3'  # Assume uniform block of text
        )
        
        return text.strip()
    
    def _extract_footer(self, image: Image.Image) -> str:
        """Extract text from footer region (bottom 15%)"""
        width, height = image.size
        footer_height = int(height * self.footer_percent)
        footer_y = height - footer_height
        
        # Crop footer region
        footer_region = image.crop((0, footer_y, width, height))
        
        # Preprocess for better OCR
        footer_region = self._preprocess_image(footer_region)
        
        # OCR
        text = pytesseract.image_to_string(
            footer_region,
            lang='eng',
            config='--psm 6 --oem 3'  # Assume uniform block of text
        )
        
        return text.strip()
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy
        - Convert to grayscale
        - Denoise
        - Threshold (binarization)
        """
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Threshold (Otsu's method)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(thresh)
        
        return processed_image
    
    def _extract_report_form(self, text: str) -> Optional[str]:
        """
        Extract Report Form using pattern matching
        
        Common patterns:
        - Form SDS
        - P&I Form
        - Form A
        - Form No.: XXX
        - Form Type: XXX
        """
        patterns = [
            r'Form\s*No[.:]\s*([A-Z0-9\-/\s]+)',
            r'Form\s*Type[.:]\s*([A-Z0-9\-/\s]+)',
            r'Form[:\s]+([A-Z0-9\-/\s]+)',
            r'Report\s*Form[.:]\s*([A-Z0-9\-/\s]+)',
            r'Survey\s*Form[.:]\s*([A-Z0-9\-/\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                form = match.group(1).strip()
                # Clean up - remove excessive whitespace
                form = re.sub(r'\s+', ' ', form)
                # Validate - should not be too long
                if len(form) <= 50:
                    return form
        
        return None
    
    def _extract_report_no(self, text: str) -> Optional[str]:
        """
        Extract Survey Report No. using pattern matching
        
        Common patterns:
        - Report No.: A/25/772
        - Report #: XXX
        - No.: XXX
        - Reference No.: XXX
        - Survey Report No.: XXX
        - Authorization No.: XXX (NEW - often contains report number)
        """
        patterns = [
            r'Survey\s*Report\s*No[.:]\s*([A-Z0-9\-/]+)',
            r'Report\s*No[.:]\s*([A-Z0-9\-/]+)',
            r'Authorization\s*No[.:]\s*([A-Z0-9\-/]+)',  # NEW: Check Authorization No.
            r'Authorization\s*Number[.:]\s*([A-Z0-9\-/]+)',  # NEW: Alternative format
            r'Report\s*#[:\s]*([A-Z0-9\-/]+)',
            r'No[.:]\s*([A-Z0-9\-/]+)',
            r'Reference\s*No[.:]\s*([A-Z0-9\-/]+)',
            r'Ref[.:]\s*([A-Z0-9\-/]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                report_no = match.group(1).strip()
                # Validate - should not be too long and have reasonable format
                if len(report_no) <= 30 and re.search(r'[A-Z0-9]', report_no):
                    return report_no
        
        return None
    
    def merge_with_document_ai(
        self,
        doc_ai_result: Dict,
        ocr_result: Dict
    ) -> Dict:
        """
        Merge Document AI and OCR results with priority and confidence
        
        Priority:
        1. If both agree -> High confidence
        2. If only one has result -> Use that one (Medium confidence)
        3. If both differ -> Use Document AI (Low confidence, show warning)
        4. If both empty -> None (Show manual review warning)
        
        Args:
            doc_ai_result: Results from Document AI
            ocr_result: Results from Targeted OCR
        
        Returns:
            Merged result with confidence flags
        """
        merged = {
            'report_form': None,
            'survey_report_no': None,
            'report_form_source': 'none',
            'survey_report_no_source': 'none',
            'report_form_confidence': 'none',
            'survey_report_no_confidence': 'none',
            'needs_manual_review': False,
            'ocr_attempted': ocr_result.get('ocr_success', False)
        }
        
        # BUG FIX: Handle None values properly before calling .strip()
        doc_form = (doc_ai_result.get('report_form') or '').strip()
        ocr_form = (ocr_result.get('report_form') or '').strip()
        
        doc_no = (doc_ai_result.get('survey_report_no') or '').strip()
        ocr_no = (ocr_result.get('survey_report_no') or '').strip()
        
        # Merge report_form
        if doc_form and ocr_form:
            if doc_form.lower() == ocr_form.lower():
                # Both agree - High confidence
                merged['report_form'] = doc_form
                merged['report_form_source'] = 'both'
                merged['report_form_confidence'] = 'high'
            else:
                # Both differ - Use Document AI, Low confidence
                merged['report_form'] = doc_form
                merged['report_form_source'] = 'document_ai'
                merged['report_form_confidence'] = 'low'
                merged['needs_manual_review'] = True
                logger.warning(f"⚠️ report_form mismatch: Document AI='{doc_form}' vs OCR='{ocr_form}'")
        elif doc_form:
            merged['report_form'] = doc_form
            merged['report_form_source'] = 'document_ai'
            merged['report_form_confidence'] = 'medium'
        elif ocr_form:
            merged['report_form'] = ocr_form
            merged['report_form_source'] = 'ocr'
            merged['report_form_confidence'] = 'medium'
        else:
            # Both empty
            merged['needs_manual_review'] = True
        
        # Merge survey_report_no
        if doc_no and ocr_no:
            if doc_no.lower() == ocr_no.lower():
                # Both agree - High confidence
                merged['survey_report_no'] = doc_no
                merged['survey_report_no_source'] = 'both'
                merged['survey_report_no_confidence'] = 'high'
            else:
                # Both differ - Use Document AI, Low confidence
                merged['survey_report_no'] = doc_no
                merged['survey_report_no_source'] = 'document_ai'
                merged['survey_report_no_confidence'] = 'low'
                merged['needs_manual_review'] = True
                logger.warning(f"⚠️ survey_report_no mismatch: Document AI='{doc_no}' vs OCR='{ocr_no}'")
        elif doc_no:
            merged['survey_report_no'] = doc_no
            merged['survey_report_no_source'] = 'document_ai'
            merged['survey_report_no_confidence'] = 'medium'
        elif ocr_no:
            merged['survey_report_no'] = ocr_no
            merged['survey_report_no_source'] = 'ocr'
            merged['survey_report_no_confidence'] = 'medium'
        else:
            # Both empty
            merged['needs_manual_review'] = True
        
        return merged


# Singleton instance
_ocr_processor = None

def get_ocr_processor() -> TargetedOCRProcessor:
    """Get singleton OCR processor instance"""
    global _ocr_processor
    if _ocr_processor is None:
        _ocr_processor = TargetedOCRProcessor()
    return _ocr_processor
