"""
OCR Processing Module for Maritime Certificate Documents
Enhanced with Google Vision API for handling scanned/image-based PDFs
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

# PDF and image processing
import pdf2image
from PIL import Image, ImageEnhance, ImageFilter

# Google Vision API
from google.cloud import vision
from emergentintegrations import setup_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    """Enhanced OCR processor with Google Vision API for maritime certificates"""
    
    def __init__(self):
        self.vision_client = None
        self.dpi = 300  # High DPI for better OCR accuracy
        self.initialize_vision_client()
    
    def initialize_vision_client(self):
        """Initialize Google Vision API client"""
        try:
            # Set up Google Cloud Vision API using service account key from environment
            # Note: In production, use proper service account authentication
            # For now, we'll use the default authentication method
            
            self.vision_client = vision.ImageAnnotatorClient()
            logger.info("✅ Google Vision API client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Vision API client: {str(e)}")
            self.vision_client = None
    
    async def process_pdf_with_ocr(self, pdf_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process PDF with OCR capabilities for scanned/image-based documents
        """
        result = {
            "success": False,
            "text_content": "",
            "page_count": 0,
            "pages": [],
            "confidence_score": 0.0,
            "processing_method": "unknown",
            "error": None
        }
        
        try:
            logger.info(f"🔍 Starting OCR processing for: {filename}")
            
            # First try to extract text directly from PDF
            text_content = self.extract_text_from_pdf(pdf_content)
            
            if text_content and len(text_content.strip()) > 100:
                # PDF has readable text, no OCR needed
                result.update({
                    "success": True,
                    "text_content": text_content,
                    "confidence_score": 0.95,
                    "processing_method": "direct_text_extraction"
                })
                logger.info(f"✅ Direct text extraction successful for {filename}")
                return result
            
            # PDF appears to be image-based, use OCR
            logger.info(f"📄 PDF appears to be image-based, converting to images for OCR: {filename}")
            
            # Convert PDF to images
            images = await self.convert_pdf_to_images(pdf_content)
            result["page_count"] = len(images)
            
            # Process each page with OCR
            all_text = []
            all_confidences = []
            page_results = []
            
            for i, image_bytes in enumerate(images):
                logger.info(f"🔍 Processing page {i+1}/{len(images)} with OCR")
                
                page_result = await self.extract_text_from_image_with_vision(image_bytes)
                
                if page_result["success"]:
                    all_text.append(page_result["text"])
                    all_confidences.append(page_result["confidence"])
                    page_results.append({
                        "page_number": i + 1,
                        "text": page_result["text"],
                        "confidence": page_result["confidence"],
                        "word_count": len(page_result["text"].split())
                    })
                else:
                    logger.warning(f"⚠️ OCR failed for page {i+1}: {page_result.get('error', 'Unknown error')}")
                    page_results.append({
                        "page_number": i + 1,
                        "text": "",
                        "confidence": 0.0,
                        "error": page_result.get("error", "OCR failed")
                    })
            
            # Combine results
            combined_text = "\n\n".join([text for text in all_text if text.strip()])
            average_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            result.update({
                "success": len(combined_text.strip()) > 0,
                "text_content": combined_text,
                "pages": page_results,
                "confidence_score": average_confidence,
                "processing_method": "google_vision_ocr"
            })
            
            if result["success"]:
                logger.info(f"✅ OCR processing completed successfully for {filename}. "
                          f"Extracted {len(combined_text)} characters with {average_confidence:.2f} confidence")
            else:
                logger.warning(f"⚠️ OCR processing completed but no text extracted from {filename}")
            
            return result
            
        except Exception as e:
            error_msg = f"OCR processing failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result.update({
                "success": False,
                "error": error_msg
            })
            return result
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Try to extract text directly from PDF (for text-based PDFs)"""
        try:
            import PyPDF2
            
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_content = ""
            
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
            
        except Exception as e:
            logger.info(f"Direct PDF text extraction failed (expected for image PDFs): {str(e)}")
            return ""
    
    async def convert_pdf_to_images(self, pdf_content: bytes) -> List[bytes]:
        """Convert PDF pages to images for OCR processing"""
        try:
            # Create temporary file for PDF processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                temp_pdf.write(pdf_content)
                temp_pdf_path = temp_pdf.name
            
            # Convert PDF pages to images
            logger.info(f"📄 Converting PDF to images at {self.dpi} DPI")
            
            images = pdf2image.convert_from_path(
                temp_pdf_path,
                dpi=self.dpi,
                output_folder=None,
                first_page=None,
                last_page=None,
                fmt='JPEG',
                jpegopt={"quality": 95, "progressive": True, "optimize": True},
                thread_count=2
            )
            
            # Process and convert images to bytes
            processed_images = []
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self.preprocess_image_for_ocr(image)
                
                # Convert to bytes
                image_bytes = self.image_to_bytes(processed_image)
                processed_images.append(image_bytes)
                
                logger.info(f"✅ Processed page {i+1} - Image size: {len(image_bytes)} bytes")
            
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
    
    def preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance contrast for better text recognition
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness for clearer text
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            # Apply slight sharpening filter
            image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
            
            return image
            
        except Exception as e:
            logger.warning(f"⚠️ Image preprocessing failed: {str(e)}")
            return image
    
    def image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to bytes"""
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95, optimize=True)
        return img_byte_arr.getvalue()
    
    async def extract_text_from_image_with_vision(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract text from image using Google Vision API"""
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
            
            # Configure features - use DOCUMENT_TEXT_DETECTION for better structure preservation
            features = [
                vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
            ]
            
            # Create request
            request = vision.AnnotateImageRequest(
                image=image,
                features=features
            )
            
            # Execute OCR request
            response = self.vision_client.annotate_image(request=request, timeout=60)
            
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
                
                average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.8
                
                result.update({
                    "success": True,
                    "text": extracted_text,
                    "confidence": average_confidence
                })
                
                logger.info(f"✅ Vision API extracted {len(extracted_text)} characters with {average_confidence:.2f} confidence")
            else:
                result["error"] = "No text detected in image"
            
            return result
            
        except Exception as e:
            error_msg = f"Vision API text extraction failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            result["error"] = error_msg
            return result
    
    async def analyze_maritime_certificate_text(self, text_content: str) -> Dict[str, Any]:
        """
        Analyze extracted text to identify maritime certificate information
        Enhanced pattern matching for scanned documents
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
            "confidence": 0.0
        }
        
        try:
            # Clean and normalize text
            text = self.clean_ocr_text(text_content)
            
            # Detect certificate type
            cert_type = self.detect_certificate_type(text)
            analysis["certificate_type"] = cert_type
            
            # Extract certificate information based on type
            if "stcw" in cert_type.lower() or "competency" in cert_type.lower():
                analysis.update(self.extract_stcw_info(text))
            elif "documentation" in cert_type.lower():
                analysis.update(self.extract_cod_info(text))
            elif "safety" in cert_type.lower():
                analysis.update(self.extract_safety_cert_info(text))
            else:
                # Generic maritime certificate extraction
                analysis.update(self.extract_generic_cert_info(text))
            
            # Calculate confidence based on extracted fields
            analysis["confidence"] = self.calculate_extraction_confidence(analysis)
            
            logger.info(f"📋 Certificate analysis completed. Type: {cert_type}, Confidence: {analysis['confidence']:.2f}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Certificate text analysis failed: {str(e)}")
            return analysis
    
    def clean_ocr_text(self, text: str) -> str:
        """Clean and normalize OCR text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors
        text = text.replace('|', 'I')  # Common OCR mistake
        text = text.replace('0', 'O', text.count('0') // 3)  # Fix some O/0 confusion
        
        # Normalize line breaks
        text = re.sub(r'[\r\n]+', '\n', text)
        
        return text.strip()
    
    def detect_certificate_type(self, text: str) -> str:
        """Detect maritime certificate type from text"""
        text_upper = text.upper()
        
        if any(keyword in text_upper for keyword in ['STCW', 'STANDARDS OF TRAINING', 'COMPETENCY']):
            if 'COMPETENCY' in text_upper:
                return 'STCW Certificate of Competency'
            elif 'PROFICIENCY' in text_upper:
                return 'STCW Certificate of Proficiency'
            else:
                return 'STCW Certificate'
        
        if any(keyword in text_upper for keyword in ['CERTIFICATE OF DOCUMENTATION', 'OFFICIAL NUMBER']):
            return 'Certificate of Documentation'
        
        if any(keyword in text_upper for keyword in ['SAFETY MANAGEMENT', 'ISM', 'INTERNATIONAL SAFETY']):
            return 'Safety Management Certificate'
        
        if any(keyword in text_upper for keyword in ['MEDICAL CERTIFICATE', 'MEDICAL FITNESS']):
            return 'Medical Certificate'
        
        return 'Maritime Certificate'
    
    def extract_stcw_info(self, text: str) -> Dict[str, Any]:
        """Extract STCW certificate specific information"""
        info = {}
        
        # Certificate number patterns
        cert_patterns = [
            r'(?:Certificate\s+No\.?|Cert\.?\s+No\.?|Number)[:\s]+([A-Z0-9\-/]{6,25})',
            r'(?:Ref\.?\s+No\.?|Reference)[:\s]+([A-Z0-9\-/]{6,25})'
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['certificate_number'] = match.group(1).strip()
                break
        
        # Holder name
        name_match = re.search(r'(?:Name|Holder)[:\s]+([A-Z\s,\.]{10,50})', text, re.IGNORECASE)
        if name_match:
            info['holder_name'] = name_match.group(1).strip()
        
        # Dates
        info.update(self.extract_dates(text))
        
        # Rank/Capacity
        rank_match = re.search(r'(?:Rank|Capacity|Position)[:\s]+([A-Z\s]{5,40})', text, re.IGNORECASE)
        if rank_match:
            info['rank'] = rank_match.group(1).strip()
        
        # Tonnage limitations
        tonnage_match = re.search(r'(?:Tonnage|GT|Gross\s+Tonnage)[:\s]+(?:Less\s+than\s+|<\s*)?(\d+,?\d*)', text, re.IGNORECASE)
        if tonnage_match:
            info['tonnage'] = tonnage_match.group(1).replace(',', '')
        
        # Issuing authority
        authority_match = re.search(r'(?:Issued\s+by|Authority|Administration)[:\s]+([A-Z\s,\.]{10,60})', text, re.IGNORECASE)
        if authority_match:
            info['issued_by'] = authority_match.group(1).strip()
        
        return info
    
    def extract_cod_info(self, text: str) -> Dict[str, Any]:
        """Extract Certificate of Documentation information"""
        info = {}
        
        # Official number
        official_match = re.search(r'(?:Official\s+Number|O\.N\.)[:\s]+(\d{6,10})', text, re.IGNORECASE)
        if official_match:
            info['certificate_number'] = official_match.group(1)
        
        # Vessel name
        vessel_match = re.search(r'(?:Vessel\s+Name|Name\s+of\s+Vessel)[:\s]+([A-Z0-9\s\-\'\"]{3,50})', text, re.IGNORECASE)
        if vessel_match:
            info['ship_name'] = vessel_match.group(1).strip()
        
        # Dates
        info.update(self.extract_dates(text))
        
        return info
    
    def extract_safety_cert_info(self, text: str) -> Dict[str, Any]:
        """Extract Safety Management Certificate information"""
        info = {}
        
        # Certificate name
        info['certificate_name'] = 'Safety Management Certificate'
        
        # Certificate number (often alphanumeric with special format)
        cert_match = re.search(r'(?:Certificate\s+No\.?|No\.?)[:\s]+([A-Z0-9\-/]{6,25})', text, re.IGNORECASE)
        if cert_match:
            info['certificate_number'] = cert_match.group(1).strip()
        
        # Company name
        company_match = re.search(r'(?:Company|Organization)[:\s]+([A-Z\s,\.]{10,60})', text, re.IGNORECASE)
        if company_match:
            info['issued_by'] = company_match.group(1).strip()
        
        # Dates
        info.update(self.extract_dates(text))
        
        return info
    
    def extract_generic_cert_info(self, text: str) -> Dict[str, Any]:
        """Extract generic certificate information"""
        info = {}
        
        # Generic certificate number patterns
        cert_patterns = [
            r'(?:Certificate\s+No\.?|Cert\.?\s+No\.?|No\.?)[:\s]+([A-Z0-9\-/]{4,25})',
            r'([A-Z]{2,}\d{6,})',  # Pattern like ABC123456
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['certificate_number'] = match.group(1).strip()
                break
        
        # Dates
        info.update(self.extract_dates(text))
        
        return info
    
    def extract_dates(self, text: str) -> Dict[str, Any]:
        """Extract various date formats from text"""
        dates_info = {}
        
        # Date patterns
        date_patterns = {
            'issue_date': [
                r'(?:Issue\s+Date|Issued|Date\s+of\s+Issue)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(?:Issue\s+Date|Issued)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
            ],
            'expiry_date': [
                r'(?:Expir[ey]\s+Date|Valid\s+Until|Expires)[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
                r'(?:Valid\s+Until|Expires)[:\s]+(\w+\s+\d{1,2},?\s+\d{4})',
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
    
    def calculate_extraction_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted information"""
        total_fields = 8  # Key fields we look for
        extracted_fields = 0
        
        key_fields = ['certificate_name', 'certificate_number', 'issue_date', 
                     'expiry_date', 'issued_by', 'ship_name', 'holder_name', 'rank']
        
        for field in key_fields:
            if analysis.get(field) and str(analysis[field]).strip():
                extracted_fields += 1
        
        # Base confidence
        base_confidence = extracted_fields / total_fields
        
        # Bonus for certificate number (critical field)
        if analysis.get('certificate_number'):
            base_confidence += 0.2
        
        # Bonus for dates
        if analysis.get('issue_date') or analysis.get('expiry_date'):
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

# Initialize global OCR processor
ocr_processor = OCRProcessor()