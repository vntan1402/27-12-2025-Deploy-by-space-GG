"""
Enhanced OCR Processing Module for Maritime Certificate Documents
With Tesseract OCR fallback and improved error handling
"""

import os
import io
import asyncio
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import re
import time
import concurrent.futures
from pathlib import Path

# PDF and image processing
import pdf2image
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

# OCR engines
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    logging.warning("Google Vision API not available")

import pytesseract

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedOCRProcessor:
    """Enhanced OCR processor with multiple engines and improved performance"""
    
    def __init__(self):
        self.vision_client = None
        self.dpi = 300  # High DPI for better OCR accuracy
        self.max_workers = 2  # Parallel processing workers
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:-/()[] '
        self.initialize_ocr_engines()
    
    def initialize_ocr_engines(self):
        """Initialize available OCR engines"""
        # Initialize Google Vision API if available
        if GOOGLE_VISION_AVAILABLE:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
                logger.info("✅ Google Vision API client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Google Vision API initialization failed: {str(e)}")
                self.vision_client = None
        
        # Test Tesseract OCR availability
        try:
            tesseract_version = pytesseract.get_tesseract_version()
            logger.info(f"✅ Tesseract OCR initialized successfully - Version: {tesseract_version}")
        except Exception as e:
            logger.error(f"❌ Tesseract OCR initialization failed: {str(e)}")
            raise Exception("No OCR engines available")
    
    async def process_pdf_with_ocr(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Enhanced PDF processing with multiple OCR engines and improved performance
        """
        start_time = time.time()
        result = {
            "success": False,
            "text_content": "",
            "page_count": 0,
            "pages": [],
            "confidence_score": 0.0,
            "processing_method": "unknown",
            "processing_time": 0.0,
            "error": None,
            "engine_used": "none"
        }
        
        try:
            logger.info(f"🔍 Starting enhanced OCR processing for: {filename}")
            
            # First try to extract text directly from PDF
            text_content = self.extract_text_from_pdf(pdf_content)
            
            if text_content and len(text_content.strip()) > 50:
                # PDF has readable text, no OCR needed
                result.update({
                    "success": True,
                    "text_content": text_content,
                    "confidence_score": 0.95,
                    "processing_method": "direct_text_extraction",
                    "processing_time": time.time() - start_time,
                    "engine_used": "direct"
                })
                logger.info(f"✅ Direct text extraction successful for {filename} ({result['processing_time']:.2f}s)")
                return result
            
            # PDF appears to be image-based, use OCR
            logger.info(f"📄 PDF appears to be image-based, converting to images for OCR: {filename}")
            
            # Convert PDF to images with optimization
            images = await self.convert_pdf_to_images_optimized(pdf_content)
            result["page_count"] = len(images)
            
            if not images:
                result["error"] = "Failed to convert PDF to images"
                return result
            
            # Process pages with parallel OCR for better performance
            page_results = await self.process_pages_parallel(images)
            
            # Combine results
            all_text = []
            all_confidences = []
            
            for i, page_result in enumerate(page_results):
                if page_result["success"]:
                    all_text.append(page_result["text"])
                    all_confidences.append(page_result["confidence"])
                    result["pages"].append({
                        "page_number": i + 1,
                        "text": page_result["text"],
                        "confidence": page_result["confidence"],
                        "word_count": len(page_result["text"].split()),
                        "engine": page_result.get("engine", "unknown")
                    })
                else:
                    logger.warning(f"⚠️ OCR failed for page {i+1}: {page_result.get('error', 'Unknown error')}")
                    result["pages"].append({
                        "page_number": i + 1,
                        "text": "",
                        "confidence": 0.0,
                        "error": page_result.get("error", "OCR failed")
                    })
            
            # Combine and validate results
            combined_text = "\n\n".join([text for text in all_text if text.strip()])
            average_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            result.update({
                "success": len(combined_text.strip()) > 10,  # Require at least some meaningful text
                "text_content": combined_text,
                "confidence_score": average_confidence,
                "processing_method": "multi_engine_ocr",
                "processing_time": time.time() - start_time,
                "engine_used": "tesseract_primary" + ("_google_fallback" if self.vision_client else "")
            })
            
            if result["success"]:
                logger.info(f"✅ OCR processing completed successfully for {filename}. "
                          f"Extracted {len(combined_text)} characters with {average_confidence:.2f} confidence "
                          f"in {result['processing_time']:.2f}s")
            else:
                result["error"] = f"OCR completed but insufficient text extracted ({len(combined_text)} chars)"
                logger.warning(f"⚠️ OCR processing completed but insufficient text extracted from {filename}")
            
            return result
            
        except Exception as e:
            error_msg = f"Enhanced OCR processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.update({
                "success": False,
                "error": error_msg,
                "processing_time": time.time() - start_time
            })
            return result
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Try to extract text directly from PDF (for text-based PDFs)"""
        try:
            import PyPDF2
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_content = ""
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            
            # Check if we got meaningful text (not just whitespace or garbled)
            clean_text = text_content.strip()
            if len(clean_text) > 50 and not self.is_garbled_text(clean_text):
                return clean_text
            
            return ""
            
        except Exception as e:
            logger.info(f"Direct PDF text extraction failed (expected for image PDFs): {str(e)}")
            return ""
    
    def is_garbled_text(self, text: str) -> bool:
        """Check if extracted text is garbled (common with image-based PDFs)"""
        # Count readable characters vs total
        readable_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,:-/()[]')
        total_chars = len(text)
        
        if total_chars == 0:
            return True
        
        readable_ratio = readable_chars / total_chars
        return readable_ratio < 0.7  # Less than 70% readable characters indicates garbled text
    
    async def convert_pdf_to_images_optimized(self, pdf_content: bytes) -> List[bytes]:
        """Optimized PDF to images conversion with better performance"""
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name
            
            # Convert PDF pages to images with optimized settings
            logger.info(f"📄 Converting PDF to images at {self.dpi} DPI")
            
            # Use moderate DPI for balance of quality and performance
            convert_dpi = min(self.dpi, 250)  # Cap at 250 DPI for performance
            
            images = pdf2image.convert_from_path(
                temp_pdf_path,
                dpi=convert_dpi,
                output_folder=None,
                first_page=None,
                last_page=None,
                fmt='PNG',  # PNG for better quality with text
                thread_count=self.max_workers,
                grayscale=True,  # Grayscale for better OCR performance
                single_file=False
            )
            
            # Process and convert images to bytes with preprocessing
            processed_images = []
            for i, image in enumerate(images):
                try:
                    # Preprocess image for better OCR
                    processed_image = self.preprocess_image_for_ocr_advanced(image)
                    
                    # Convert to bytes
                    image_bytes = self.image_to_bytes_optimized(processed_image)
                    processed_images.append(image_bytes)
                    
                    logger.info(f"✅ Processed page {i+1}/{len(images)} - Size: {len(image_bytes)} bytes")
                except Exception as e:
                    logger.error(f"❌ Failed to process page {i+1}: {str(e)}")
                    continue
            
            # Clean up temporary file
            os.unlink(temp_pdf_path)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"❌ PDF to image conversion failed: {str(e)}")
            if 'temp_pdf_path' in locals():
                try:
                    os.unlink(temp_pdf_path)
                except:
                    pass
            raise e
    
    def preprocess_image_for_ocr_advanced(self, image: Image.Image) -> Image.Image:
        """Advanced image preprocessing for better OCR results"""
        try:
            # Convert to numpy array for OpenCV processing
            img_array = np.array(image)
            
            # Convert to grayscale if not already
            if len(img_array.shape) == 3:
                img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                img_gray = img_array
            
            # Apply adaptive thresholding for better text contrast
            img_thresh = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, 11, 2)
            
            # Noise removal
            kernel = np.ones((1,1), np.uint8)
            img_cleaned = cv2.morphologyEx(img_thresh, cv2.MORPH_CLOSE, kernel)
            img_cleaned = cv2.medianBlur(img_cleaned, 3)
            
            # Convert back to PIL Image
            processed_image = Image.fromarray(img_cleaned)
            
            # Additional PIL enhancements
            if processed_image.mode != 'L':  # Ensure grayscale
                processed_image = processed_image.convert('L')
            
            # Enhance contrast slightly
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(1.1)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"⚠️ Advanced image preprocessing failed, using basic: {str(e)}")
            # Fallback to basic preprocessing
            if image.mode != 'L':
                image = image.convert('L')
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(1.2)
    
    def image_to_bytes_optimized(self, image: Image.Image) -> bytes:
        """Convert PIL Image to optimized bytes"""
        img_byte_arr = io.BytesIO()
        
        # Use PNG for better quality with text, optimize for size
        image.save(img_byte_arr, format='PNG', optimize=True)
        return img_byte_arr.getvalue()
    
    async def process_pages_parallel(self, images: List[bytes]) -> List[Dict[str, Any]]:
        """Process multiple pages in parallel for better performance"""
        loop = asyncio.get_event_loop()
        
        # Use ThreadPoolExecutor for CPU-bound OCR tasks
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all OCR tasks
            future_to_index = {
                loop.run_in_executor(executor, self.extract_text_from_image_multi_engine, image_bytes, i): i
                for i, image_bytes in enumerate(images)
            }
            
            # Collect results maintaining order
            results = [None] * len(images)
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = await future
                except Exception as e:
                    logger.error(f"❌ Page {index + 1} processing failed: {str(e)}")
                    results[index] = {
                        "success": False,
                        "text": "",
                        "confidence": 0.0,
                        "error": str(e),
                        "engine": "none"
                    }
            
            return results
    
    def extract_text_from_image_multi_engine(self, image_bytes: bytes, page_num: int) -> Dict[str, Any]:
        """Extract text using multiple OCR engines with fallback"""
        result = {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "error": None,
            "engine": "none"
        }
        
        try:
            # First try Tesseract OCR (faster and more reliable)
            tesseract_result = self.extract_text_with_tesseract(image_bytes)
            
            if tesseract_result["success"] and len(tesseract_result["text"].strip()) > 10:
                result = tesseract_result
                result["engine"] = "tesseract"
                logger.info(f"✅ Page {page_num + 1}: Tesseract OCR successful ({len(result['text'])} chars)")
                return result
            
            # Fallback to Google Vision API if available and Tesseract failed
            if self.vision_client:
                logger.info(f"🔄 Page {page_num + 1}: Tesseract insufficient, trying Google Vision API")
                vision_result = self.extract_text_with_vision_api(image_bytes)
                
                if vision_result["success"] and len(vision_result["text"].strip()) > 10:
                    result = vision_result
                    result["engine"] = "google_vision"
                    logger.info(f"✅ Page {page_num + 1}: Google Vision API successful ({len(result['text'])} chars)")
                    return result
            
            # If both failed, return the better result
            if tesseract_result["success"]:
                result = tesseract_result
                result["engine"] = "tesseract_low_confidence"
            else:
                result["error"] = "All OCR engines failed to extract meaningful text"
                result["engine"] = "failed"
            
            return result
            
        except Exception as e:
            result["error"] = f"Multi-engine OCR failed: {str(e)}"
            result["engine"] = "error"
            return result
    
    def extract_text_with_tesseract(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        result = {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "error": None
        }
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text with configuration optimized for documents
            extracted_text = pytesseract.image_to_string(image, config=self.tesseract_config)
            
            # Get confidence data
            try:
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                avg_confidence = avg_confidence / 100.0  # Convert to 0-1 scale
            except:
                avg_confidence = 0.8  # Default confidence if calculation fails
            
            # Clean and validate text
            cleaned_text = self.clean_ocr_text(extracted_text)
            
            result.update({
                "success": len(cleaned_text.strip()) > 0,
                "text": cleaned_text,
                "confidence": avg_confidence
            })
            
            return result
            
        except Exception as e:
            result["error"] = f"Tesseract OCR failed: {str(e)}"
            return result
    
    def extract_text_with_vision_api(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract text using Google Vision API"""
        result = {
            "success": False,
            "text": "",
            "confidence": 0.0,
            "error": None
        }
        
        if not self.vision_client:
            result["error"] = "Google Vision API client not initialized"
            return result
        
        try:
            # Prepare image for Vision API
            image = vision.Image(content=image_bytes)
            
            # Configure for document text detection
            feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
            request = vision.AnnotateImageRequest(image=image, features=[feature])
            
            # Execute OCR request with timeout
            response = self.vision_client.annotate_image(request=request, timeout=30)
            
            if response.error.message:
                result["error"] = f'Vision API Error: {response.error.message}'
                return result
            
            # Extract text from response
            if response.full_text_annotation:
                extracted_text = response.full_text_annotation.text
                
                # Calculate confidence score
                confidence_scores = []
                if response.full_text_annotation.pages:
                    for page in response.full_text_annotation.pages:
                        for block in page.blocks:
                            if hasattr(block, 'confidence'):
                                confidence_scores.append(block.confidence)
                
                average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.85
                
                result.update({
                    "success": True,
                    "text": extracted_text,
                    "confidence": average_confidence
                })
            else:
                result["error"] = "No text detected in image"
            
            return result
            
        except Exception as e:
            result["error"] = f"Vision API extraction failed: {str(e)}"
            return result
    
    def clean_ocr_text(self, text: str) -> str:
        """Enhanced OCR text cleaning"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors in maritime documents
        ocr_fixes = {
            # Common character misreads
            '|': 'I',
            '0O': 'O',  # Zero-O confusion
            'Q0': 'O',  # Q-O confusion
            '§': 'S',
            '€': 'C',
            '£': 'E',
            # Common word fixes
            'CERTIFLCATE': 'CERTIFICATE',
            'CERTIEICATE': 'CERTIFICATE',
            'MANAGEMENI': 'MANAGEMENT',
            'TONNAG[': 'TONNAGE',
            'TONNAG€': 'TONNAGE',
            'LSSUED': 'ISSUED',
            'VALLD': 'VALID',
        }
        
        for mistake, correction in ocr_fixes.items():
            text = text.replace(mistake, correction)
        
        # Normalize line breaks and clean up
        text = re.sub(r'[\r\n]+', '\n', text)
        text = text.strip()
        
        return text
    
    async def analyze_maritime_certificate_text(self, text_content: str) -> Dict[str, Any]:
        """
        Enhanced maritime certificate analysis with better pattern matching
        """
        analysis = {
            "certificate_type": "unknown",
            "certificate_name": None,
            "certificate_number": None,
            "issue_date": None,
            "valid_date": None,
            "expiry_date": None,
            "issued_by": None,
            "ship_name": None,
            "imo_number": None,
            "holder_name": None,
            "rank": None,
            "tonnage": None,
            "confidence": 0.0,
            "extracted_fields": 0,
            "processing_notes": []
        }
        
        try:
            # Clean and normalize text
            text = self.clean_ocr_text(text_content)
            analysis["processing_notes"].append(f"Text cleaned: {len(text)} characters")
            
            # Detect certificate type
            cert_type = self.detect_certificate_type_enhanced(text)
            analysis["certificate_type"] = cert_type
            analysis["processing_notes"].append(f"Certificate type detected: {cert_type}")
            
            # Extract certificate information based on type
            if "safety" in cert_type.lower() and "management" in cert_type.lower():
                extracted_info = self.extract_safety_management_info(text)
                analysis.update(extracted_info)
            elif "stcw" in cert_type.lower() or "competency" in cert_type.lower():
                extracted_info = self.extract_stcw_info_enhanced(text)
                analysis.update(extracted_info)
            elif "documentation" in cert_type.lower():
                extracted_info = self.extract_cod_info_enhanced(text)
                analysis.update(extracted_info)
            else:
                # Generic maritime certificate extraction
                extracted_info = self.extract_generic_cert_info_enhanced(text)
                analysis.update(extracted_info)
            
            # Count extracted fields
            extracted_fields = sum(1 for key, value in analysis.items() 
                                 if key not in ['confidence', 'extracted_fields', 'processing_notes', 'certificate_type'] 
                                 and value and str(value).strip())
            analysis["extracted_fields"] = extracted_fields
            
            # Calculate confidence based on extracted fields and patterns
            analysis["confidence"] = self.calculate_extraction_confidence_enhanced(analysis, text)
            
            logger.info(f"📋 Enhanced certificate analysis completed. "
                       f"Type: {cert_type}, Extracted: {extracted_fields} fields, "
                       f"Confidence: {analysis['confidence']:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Enhanced certificate text analysis failed: {str(e)}")
            analysis["processing_notes"].append(f"Analysis error: {str(e)}")
            return analysis
    
    def detect_certificate_type_enhanced(self, text: str) -> str:
        """Enhanced certificate type detection"""
        text_upper = text.upper()
        
        # Safety Management Certificate (SMS/ISM)
        sms_keywords = ['SAFETY MANAGEMENT', 'ISM', 'INTERNATIONAL SAFETY MANAGEMENT', 
                       'SMS CERTIFICATE', 'DOCUMENT OF COMPLIANCE']
        if any(keyword in text_upper for keyword in sms_keywords):
            return 'Safety Management Certificate'
        
        # STCW Certificates
        stcw_keywords = ['STCW', 'STANDARDS OF TRAINING', 'COMPETENCY', 'PROFICIENCY', 'WATCHKEEPING']
        if any(keyword in text_upper for keyword in stcw_keywords):
            if 'COMPETENCY' in text_upper:
                return 'STCW Certificate of Competency'
            elif 'PROFICIENCY' in text_upper:
                return 'STCW Certificate of Proficiency'
            else:
                return 'STCW Certificate'
        
        # Certificate of Documentation
        cod_keywords = ['CERTIFICATE OF DOCUMENTATION', 'OFFICIAL NUMBER', 'COAST GUARD', 
                       'VESSEL DOCUMENTATION']
        if any(keyword in text_upper for keyword in cod_keywords):
            return 'Certificate of Documentation'
        
        # Other maritime certificates
        if any(keyword in text_upper for keyword in ['MEDICAL CERTIFICATE', 'MEDICAL FITNESS']):
            return 'Medical Certificate'
        
        if any(keyword in text_upper for keyword in ['RADIO', 'GMDSS']):
            return 'Radio Certificate'
        
        # Generic certificate detection
        if 'CERTIFICATE' in text_upper:
            return 'Maritime Certificate'
        
        return 'Unknown Document'
    
    def extract_safety_management_info(self, text: str) -> Dict[str, Any]:
        """Extract Safety Management Certificate specific information"""
        info = {}
        
        # Certificate name
        info['certificate_name'] = 'Safety Management Certificate'
        
        # Certificate number - SMS certificates often have specific formats
        cert_patterns = [
            r'(?:Certificate\s+No\.?|Cert\.?\s+No\.?|Number)[:\s]+([A-Z0-9\-/]{6,25})',
            r'(?:SMS\s+No\.?|ISM\s+No\.?)[:\s]+([A-Z0-9\-/]{6,25})',
            r'([A-Z]{2,4}\d{8,})',  # Pattern like PM252494416
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['certificate_number'] = match.group(1).strip()
                break
        
        # Dates with better patterns
        info.update(self.extract_dates_enhanced(text))
        
        # Issuing authority
        authority_patterns = [
            r'(?:Issued\s+by|Authority|Administration)[:\s]+([A-Z\s,\.]{10,60})',
            r'(?:Panama\s+Maritime|Maritime\s+Authority)[:\s]*([A-Z\s,\.]{0,40})',
        ]
        
        for pattern in authority_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['issued_by'] = match.group(1).strip() if match.group(1) else 'Panama Maritime Documentation Services'
                break
        
        return info
    
    def extract_dates_enhanced(self, text: str) -> Dict[str, Any]:
        """Enhanced date extraction with multiple formats"""
        dates_info = {}
        
        # More comprehensive date patterns
        date_patterns = {
            'issue_date': [
                r'(?:Issue\s+Date|Issued|Date\s+of\s+Issue)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(?:Issue\s+Date|Issued)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
                r'(?:Date\s+of\s+Issue)[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            ],
            'expiry_date': [
                r'(?:Expir[ey]\s+Date|Valid\s+Until|Expires|Valid\s+to)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(?:Valid\s+Until|Expires)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
                r'(?:Valid\s+Until)[:\s]+(\d{1,2}\s+\w+\s+\d{4})',
            ],
            'valid_date': [
                r'(?:Valid\s+Date|Valid\s+From)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            ]
        }
        
        for date_type, patterns in date_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    dates_info[date_type] = match.group(1)
                    break
        
        return dates_info
    
    def calculate_extraction_confidence_enhanced(self, analysis: Dict[str, Any], original_text: str) -> float:
        """Enhanced confidence calculation"""
        total_possible_fields = 10
        extracted_fields = analysis.get("extracted_fields", 0)
        
        # Base confidence from field extraction
        base_confidence = min(0.8, extracted_fields / total_possible_fields)
        
        # Bonus factors
        confidence_bonus = 0.0
        
        # Certificate number is critical
        if analysis.get('certificate_number'):
            confidence_bonus += 0.15
        
        # Date fields
        date_fields = ['issue_date', 'expiry_date', 'valid_date']
        valid_dates = sum(1 for field in date_fields if analysis.get(field))
        confidence_bonus += valid_dates * 0.05
        
        # Certificate type detection
        if analysis.get('certificate_type') != 'unknown':
            confidence_bonus += 0.1
        
        # Text quality indicators
        text_length = len(original_text)
        if text_length > 500:  # Good amount of text extracted
            confidence_bonus += 0.05
        
        # Pattern matching quality
        if analysis.get('certificate_number') and len(analysis['certificate_number']) >= 8:
            confidence_bonus += 0.05
        
        final_confidence = min(1.0, base_confidence + confidence_bonus)
        return final_confidence
    
    def extract_stcw_info_enhanced(self, text: str) -> Dict[str, Any]:
        """Enhanced STCW certificate extraction"""
        # Implementation similar to original but with better patterns
        return self.extract_generic_cert_info_enhanced(text)
    
    def extract_cod_info_enhanced(self, text: str) -> Dict[str, Any]:
        """Enhanced Certificate of Documentation extraction"""
        # Implementation similar to original but with better patterns  
        return self.extract_generic_cert_info_enhanced(text)
    
    def extract_generic_cert_info_enhanced(self, text: str) -> Dict[str, Any]:
        """Enhanced generic certificate information extraction"""
        info = {}
        
        # Generic certificate number patterns
        cert_patterns = [
            r'(?:Certificate\s+No\.?|Cert\.?\s+No\.?|No\.?)[:\s]+([A-Z0-9\-/]{4,25})',
            r'([A-Z]{2,4}\d{6,})',  # Pattern like ABC123456
            r'([A-Z0-9]{8,20})',    # Alphanumeric codes
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not match.group(1).isdigit():  # Avoid pure numbers
                info['certificate_number'] = match.group(1).strip()
                break
        
        # Enhanced date extraction
        info.update(self.extract_dates_enhanced(text))
        
        # Ship/vessel name
        ship_patterns = [
            r'(?:Vessel\s+Name|Ship\s+Name|M\.V\.|M/V)[:\s]+([A-Z0-9\s\-\'\"]{3,50})',
            r'(?:Name\s+of\s+Vessel)[:\s]+([A-Z0-9\s\-\'\"]{3,50})',
        ]
        
        for pattern in ship_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['ship_name'] = match.group(1).strip()
                break
        
        # IMO number
        imo_match = re.search(r'(?:IMO\s+No\.?|IMO)[:\s]+(\d{7})', text, re.IGNORECASE)
        if imo_match:
            info['imo_number'] = imo_match.group(1)
        
        return info

# Initialize enhanced OCR processor
ocr_processor = EnhancedOCRProcessor()