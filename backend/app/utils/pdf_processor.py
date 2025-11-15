import logging
import io
import re
from typing import Optional, Tuple
from PIL import Image
import pytesseract
import PyPDF2

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Utility class for PDF text extraction and OCR"""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> Tuple[str, bool]:
        """
        Extract text from PDF file
        
        Returns:
            Tuple[str, bool]: (extracted_text, is_scanned)
                - extracted_text: The extracted text content
                - is_scanned: True if PDF appears to be scanned (low text content)
        """
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Check if PDF appears to be scanned (very little text)
            is_scanned = len(text.strip()) < 100
            
            logger.info(f"Extracted {len(text)} characters from PDF (scanned: {is_scanned})")
            return text, is_scanned
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return "", True
    
    @staticmethod
    def extract_text_with_ocr(file_content: bytes) -> str:
        """
        Extract text from PDF using OCR (for scanned documents)
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            str: Extracted text from OCR
        """
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    # Convert PDF page to image
                    # Note: PyPDF2 doesn't have direct image conversion
                    # This is a simplified approach - in production, use pdf2image
                    page_text = pytesseract.image_to_string(
                        page,
                        lang='eng',
                        config='--psm 6'
                    )
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue
            
            logger.info(f"OCR extracted {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {e}")
            return ""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and special characters
        
        Args:
            text: Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove multiple whitespaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters but keep newlines
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    @staticmethod
    async def process_pdf(file_content: bytes, use_ocr_fallback: bool = True) -> str:
        """
        Process PDF file and extract text (with OCR fallback if needed)
        
        Args:
            file_content: PDF file content as bytes
            use_ocr_fallback: Whether to use OCR if regular extraction fails
            
        Returns:
            str: Extracted and cleaned text
        """
        # Try regular text extraction first
        text, is_scanned = PDFProcessor.extract_text_from_pdf(file_content)
        
        # If PDF appears to be scanned and OCR fallback is enabled, try OCR
        if is_scanned and use_ocr_fallback:
            logger.info("PDF appears to be scanned, trying OCR...")
            ocr_text = PDFProcessor.extract_text_with_ocr(file_content)
            if len(ocr_text) > len(text):
                text = ocr_text
        
        # Clean the text
        text = PDFProcessor.clean_text(text)
        
        return text
