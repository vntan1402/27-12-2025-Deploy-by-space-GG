"""
PDF Splitter Utility
Split large PDFs into processable chunks for Document AI
"""
import PyPDF2
import io
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PDFSplitter:
    """Utility to split large PDFs into processable chunks"""
    
    def __init__(self, max_pages_per_chunk: int = 12):
        """
        Args:
            max_pages_per_chunk: Maximum pages per chunk (default 12, safely under 15 limit)
        """
        self.max_pages_per_chunk = max_pages_per_chunk
    
    def get_page_count(self, pdf_content: bytes) -> int:
        """Get total page count of PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            raise ValueError(f"Invalid PDF file: {str(e)}")
    
    def needs_splitting(self, pdf_content: bytes) -> bool:
        """Check if PDF needs to be split (> 15 pages)"""
        page_count = self.get_page_count(pdf_content)
        return page_count > 15
    
    def split_pdf(self, pdf_content: bytes, filename: str) -> List[Dict]:
        """
        Split PDF into chunks
        
        Args:
            pdf_content: PDF file as bytes
            filename: Original filename
            
        Returns:
            List of chunks with metadata:
            [
                {
                    'content': bytes,
                    'chunk_num': 1,
                    'page_range': '1-12',
                    'start_page': 1,
                    'end_page': 12,
                    'filename': 'survey_report_chunk1.pdf',
                    'size_bytes': 12345
                },
                ...
            ]
        """
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        total_pages = len(pdf_reader.pages)
        
        if total_pages <= 15:
            # No splitting needed
            logger.info(f"PDF has {total_pages} pages, no splitting needed")
            return [{
                'content': pdf_content,
                'chunk_num': 1,
                'page_range': f'1-{total_pages}',
                'start_page': 1,
                'end_page': total_pages,
                'page_count': total_pages,  # Number of pages in this chunk
                'filename': filename,
                'size_bytes': len(pdf_content)
            }]
        
        logger.info(f"📄 Splitting PDF: {filename} ({total_pages} pages) into chunks of {self.max_pages_per_chunk}")
        
        chunks = []
        base_filename = filename.rsplit('.', 1)[0]  # Remove .pdf extension
        
        for start_page in range(0, total_pages, self.max_pages_per_chunk):
            end_page = min(start_page + self.max_pages_per_chunk, total_pages)
            chunk_num = len(chunks) + 1
            
            # Create new PDF for this chunk
            pdf_writer = PyPDF2.PdfWriter()
            
            for page_num in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Write to bytes
            chunk_bytes_io = io.BytesIO()
            pdf_writer.write(chunk_bytes_io)
            chunk_content = chunk_bytes_io.getvalue()
            
            chunk_info = {
                'content': chunk_content,
                'chunk_num': chunk_num,
                'page_range': f'{start_page + 1}-{end_page}',
                'start_page': start_page + 1,
                'end_page': end_page,
                'page_count': end_page - start_page,  # Number of pages in this chunk
                'filename': f'{base_filename}_chunk{chunk_num}.pdf',
                'size_bytes': len(chunk_content)
            }
            
            chunks.append(chunk_info)
            logger.info(f"  ✅ Chunk {chunk_num}: pages {chunk_info['page_range']}, size: {chunk_info['size_bytes']} bytes")
        
        logger.info(f"📦 Split complete: {len(chunks)} chunks created")
        return chunks


def merge_analysis_results(
    chunk_results: List[Dict],
    document_type: str = 'survey_report'
) -> Dict:
    """
    Intelligently merge results from multiple PDF chunks
    
    Generic function supporting multiple document types:
    - 'survey_report': Survey reports (class surveys, inspections)
    - 'test_report': Test reports (equipment maintenance, testing)
    - 'audit_report': Audit reports (ISM, ISPS, MLC)
    - Other document types
    
    Strategy:
    1. Document Name: Usually in first chunk (take from earliest chunk)
    2. Document Number: Take first non-empty or most common
    3. Issued By: Take most common value
    4. Issued Date: Take first valid date
    5. Additional fields: Merge based on document type
    6. Notes: Concatenate all notes with chunk indicators
    
    Args:
        chunk_results: List of analysis results from each chunk
        document_type: Type of document ('survey_report', 'test_report', etc.)
        
    Returns:
        Merged analysis result
    """
    
    # Define field mappings per document type
    FIELD_MAPPINGS = {
        'survey_report': {
            'name': 'survey_report_name',
            'no': 'survey_report_no',
            'additional_fields': ['surveyor_name']
        },
        'test_report': {
            'name': 'test_report_name',
            'no': 'test_report_no',
            'additional_fields': ['valid_date']
        },
        'audit_report': {
            'name': 'audit_report_name',
            'no': 'audit_report_no',
            'additional_fields': ['auditor_name']
        },
        'approval_document': {
            'name': 'approval_document_name',
            'no': 'approval_document_no',
            'issued_by_field': 'approved_by',
            'issued_date_field': 'approved_date',
            'additional_fields': []
        },
        'drawing_manual': {
            'name': 'document_name',
            'no': 'document_no',
            'issued_by_field': 'approved_by',
            'issued_date_field': 'approved_date',
            'additional_fields': []
        }
    }
    
    # Validate document_type
    if document_type not in FIELD_MAPPINGS:
        logger.warning(f"⚠️ Unsupported document_type: {document_type}, using 'survey_report'")
        document_type = 'survey_report'
    
    mapping = FIELD_MAPPINGS[document_type]
    name_field = mapping['name']
    no_field = mapping['no']
    
    # Check if all chunks succeeded
    successful_chunks = [cr for cr in chunk_results if cr.get('success')]
    
    if not successful_chunks:
        logger.error("❌ All chunks failed to process")
        return {
            'success': False,
            'error': 'All chunks failed to process'
        }
    
    logger.info(f"🔀 Merging {len(successful_chunks)}/{len(chunk_results)} successful chunks for {document_type}")
    
    # Initialize merged result with dynamic field names
    merged = {
        name_field: '',
        no_field: '',
        'issued_by': '',
        'issued_date': '',
        'note': '',
        'status': 'Valid'
    }
    
    # Add additional fields based on document type
    for field in mapping.get('additional_fields', []):
        merged[field] = ''
    
    # Collections for smart merging
    all_names = []
    all_report_nos = []
    all_issued_by = []
    all_dates = []
    all_additional_data = {}  # For document-specific fields
    all_notes = []
    
    # Initialize collections for additional fields
    for field in mapping.get('additional_fields', []):
        all_additional_data[field] = []
    
    # Collect data from all chunks
    for chunk_result in successful_chunks:
        extracted = chunk_result.get('extracted_fields', {})
        chunk_num = chunk_result.get('chunk_num', 0)
        page_range = chunk_result.get('page_range', '')
        
        # Collect name (dynamic field)
        if extracted.get(name_field):
            all_names.append({
                'value': extracted[name_field],
                'chunk': chunk_num,
                'pages': page_range
            })
        
        # Collect number (dynamic field)
        if extracted.get(no_field):
            all_report_nos.append({
                'value': extracted[no_field],
                'chunk': chunk_num
            })
        
        # Collect common fields
        if extracted.get('issued_by'):
            all_issued_by.append({
                'value': extracted['issued_by'],
                'chunk': chunk_num
            })
        
        if extracted.get('issued_date'):
            all_dates.append({
                'value': extracted['issued_date'],
                'chunk': chunk_num
            })
        
        # Collect additional fields (document-specific)
        for field in mapping.get('additional_fields', []):
            if extracted.get(field):
                all_additional_data[field].append({
                    'value': extracted[field],
                    'chunk': chunk_num
                })
        
        # Collect notes
        if extracted.get('note'):
            all_notes.append({
                'value': extracted['note'],
                'chunk': chunk_num,
                'pages': page_range
            })
    
    # Strategy 1: Document Name (prefer first chunk - usually cover page)
    if all_names:
        merged[name_field] = all_names[0]['value']
        logger.info(f"  📝 {name_field}: '{merged[name_field]}' (from chunk {all_names[0]['chunk']})")
    
    # Strategy 2: Report Number (take first non-empty or most common)
    if all_report_nos:
        # Count occurrences
        report_no_counts = {}
        for item in all_report_nos:
            val = item['value']
            report_no_counts[val] = report_no_counts.get(val, 0) + 1
        
        # Take most common
        merged[no_field] = max(report_no_counts, key=report_no_counts.get)
        logger.info(f"  🔢 {no_field}: '{merged[no_field]}' (appears in {report_no_counts[merged[no_field]]} chunk(s))")
    
    # Strategy 3: Issued By (take most common)
    if all_issued_by:
        issued_by_counts = {}
        for item in all_issued_by:
            val = item['value']
            issued_by_counts[val] = issued_by_counts.get(val, 0) + 1
        
        merged['issued_by'] = max(issued_by_counts, key=issued_by_counts.get)
        logger.info(f"  🏛️ Issued By: '{merged['issued_by']}'")
    
    # Strategy 4: Date (take first valid date)
    if all_dates:
        merged['issued_date'] = all_dates[0]['value']
        logger.info(f"  📅 Date: '{merged['issued_date']}'")
    
    # Strategy 5: Additional fields (document-specific merging)
    for field, values in all_additional_data.items():
        if values:
            # For surveyor_name or auditor_name: collect unique names
            if field in ['surveyor_name', 'auditor_name']:
                unique_values = list(set([v['value'] for v in values]))
                merged[field] = ', '.join(unique_values)
                logger.info(f"  👤 {field}: '{merged[field]}'")
            # For other fields (like valid_date): take first
            else:
                merged[field] = values[0]['value']
                logger.info(f"  ✅ {field}: '{merged[field]}'")
    
    # Strategy 6: Notes (concatenate with chunk indicators)
    if all_notes:
        formatted_notes = []
        for note_item in all_notes:
            formatted_notes.append(f"[Pages {note_item['pages']}] {note_item['value']}")
        merged['note'] = ' | '.join(formatted_notes)
        logger.info(f"  📋 Notes merged from {len(all_notes)} chunks")
    
    # Add metadata
    merged['success'] = True
    merged['merge_info'] = {
        'total_chunks_processed': len(successful_chunks),
        'failed_chunks': len(chunk_results) - len(successful_chunks),
        'merge_strategy': 'intelligent',
        'chunks_with_data': {
            'name': len(all_names),
            'report_no': len(all_report_nos),
            'issued_by': len(all_issued_by),
            'date': len(all_dates),
            'surveyor': len(all_surveyors),
            'notes': len(all_notes)
        }
    }
    
    logger.info(f"✅ Merge complete!")
    
    return merged


def create_enhanced_merged_summary(
    chunk_results: List[Dict],
    merged_data: Dict,
    original_filename: str,
    total_pages: int,
    document_type: str = 'survey_report'
) -> str:
    """
    Create a well-formatted merged summary document
    
    Generic function supporting multiple document types.
    
    Args:
        chunk_results: List of chunk processing results
        merged_data: Merged analysis data
        original_filename: Original PDF filename
        total_pages: Total page count
        document_type: Type of document ('survey_report', 'test_report', etc.)
        
    Returns:
        Formatted summary text
    """
    from datetime import datetime
    
    # Define label mappings per document type
    LABEL_MAPPINGS = {
        'survey_report': {
            'title': 'SURVEY REPORT ANALYSIS - MERGED SUMMARY',
            'name_label': 'Survey Report Name',
            'name_field': 'survey_report_name',
            'no_label': 'Report Number',
            'no_field': 'survey_report_no',
            'additional': [
                ('Surveyor Name', 'surveyor_name')
            ]
        },
        'test_report': {
            'title': 'TEST REPORT ANALYSIS - MERGED SUMMARY',
            'name_label': 'Test Report Name',
            'name_field': 'test_report_name',
            'no_label': 'Test Report Number',
            'no_field': 'test_report_no',
            'additional': [
                ('Valid Date', 'valid_date')
            ]
        },
        'audit_report': {
            'title': 'AUDIT REPORT ANALYSIS - MERGED SUMMARY',
            'name_label': 'Audit Report Name',
            'name_field': 'audit_report_name',
            'no_label': 'Report Number',
            'no_field': 'audit_report_no',
            'additional': [
                ('Auditor Name', 'auditor_name')
            ]
        }
    }
    
    # Validate and get mapping
    if document_type not in LABEL_MAPPINGS:
        logger.warning(f"⚠️ Unsupported document_type for summary: {document_type}, using 'survey_report'")
        document_type = 'survey_report'
    
    mapping = LABEL_MAPPINGS[document_type]
    
    summary_lines = []
    
    # Header (dynamic title)
    summary_lines.append("=" * 80)
    summary_lines.append(mapping['title'])
    summary_lines.append("=" * 80)
    summary_lines.append("")
    
    # Processing metadata
    summary_lines.append("PROCESSING INFORMATION:")
    summary_lines.append("-" * 80)
    summary_lines.append(f"Original File: {original_filename}")
    summary_lines.append(f"Total Pages: {total_pages}")
    summary_lines.append(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    summary_lines.append(f"Processing Method: Split PDF + Batch Processing")
    summary_lines.append(f"Document Type: {document_type}")
    summary_lines.append(f"Total Chunks: {len(chunk_results)}")
    summary_lines.append(f"Successful Chunks: {len([cr for cr in chunk_results if cr.get('success')])}")
    summary_lines.append(f"Failed Chunks: {len([cr for cr in chunk_results if not cr.get('success')])}")
    summary_lines.append("")
    
    # Merged extraction results (dynamic labels)
    summary_lines.append("EXTRACTED INFORMATION (MERGED):")
    summary_lines.append("-" * 80)
    summary_lines.append(f"{mapping['name_label']}: {merged_data.get(mapping['name_field'], 'N/A')}")
    summary_lines.append(f"{mapping['no_label']}: {merged_data.get(mapping['no_field'], 'N/A')}")
    summary_lines.append(f"Issued By: {merged_data.get('issued_by', 'N/A')}")
    summary_lines.append(f"Issued Date: {merged_data.get('issued_date', 'N/A')}")
    
    # Add document-specific fields
    for label, field in mapping.get('additional', []):
        if merged_data.get(field):
            summary_lines.append(f"{label}: {merged_data[field]}")
    
    summary_lines.append(f"Status: {merged_data.get('status', 'Valid')}")
    
    if merged_data.get('note'):
        summary_lines.append(f"\nNotes:")
        summary_lines.append(merged_data['note'])
    
    summary_lines.append("")
    summary_lines.append("")
    
    # Detailed chunk information
    summary_lines.append("DETAILED CHUNK ANALYSIS:")
    summary_lines.append("=" * 80)
    summary_lines.append("")
    
    successful_chunks = [cr for cr in chunk_results if cr.get('success')]
    
    for i, chunk_result in enumerate(successful_chunks):
        chunk_num = chunk_result.get('chunk_num', i + 1)
        page_range = chunk_result.get('page_range', 'Unknown')
        summary_text = chunk_result.get('summary_text', '')
        
        summary_lines.append(f"CHUNK {chunk_num} (Pages {page_range})")
        summary_lines.append("-" * 80)
        
        if summary_text:
            summary_lines.append(summary_text)
        else:
            summary_lines.append("[No summary available for this chunk]")
        
        summary_lines.append("")
        summary_lines.append("")
    
    # Footer
    summary_lines.append("=" * 80)
    summary_lines.append("END OF MERGED SUMMARY")
    summary_lines.append("=" * 80)
    
    return '\n'.join(summary_lines)



def merge_approval_document_results(chunk_results: List[Dict]) -> Dict:
    """
    Convenience wrapper for merging approval document results
    Calls merge_analysis_results with 'approval_document' type
    
    Args:
        chunk_results: List of chunk processing results
        
    Returns:
        Merged approval document data
    """
    return merge_analysis_results(chunk_results, document_type='approval_document')

