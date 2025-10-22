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
                'filename': f'{base_filename}_chunk{chunk_num}.pdf',
                'size_bytes': len(chunk_content)
            }
            
            chunks.append(chunk_info)
            logger.info(f"  ✅ Chunk {chunk_num}: pages {chunk_info['page_range']}, size: {chunk_info['size_bytes']} bytes")
        
        logger.info(f"📦 Split complete: {len(chunks)} chunks created")
        return chunks


def merge_analysis_results(chunk_results: List[Dict]) -> Dict:
    """
    Intelligently merge results from multiple PDF chunks
    
    Strategy:
    1. Survey Report Name: Usually in first chunk (take from earliest chunk)
    2. Report Number: Take first non-empty
    3. Issued By: Take most common value
    4. Issued Date: Take first valid date
    5. Surveyor Name: Collect all unique names
    6. Notes: Concatenate all notes with chunk indicators
    
    Args:
        chunk_results: List of analysis results from each chunk
        
    Returns:
        Merged analysis result
    """
    
    # Check if all chunks succeeded
    successful_chunks = [cr for cr in chunk_results if cr.get('success')]
    
    if not successful_chunks:
        logger.error("❌ All chunks failed to process")
        return {
            'success': False,
            'error': 'All chunks failed to process'
        }
    
    logger.info(f"🔀 Merging {len(successful_chunks)}/{len(chunk_results)} successful chunks")
    
    # Initialize merged result
    merged = {
        'survey_report_name': '',
        'survey_report_no': '',
        'issued_by': '',
        'issued_date': '',
        'surveyor_name': '',
        'note': '',
        'status': 'Valid'
    }
    
    # Collections for smart merging
    all_names = []
    all_report_nos = []
    all_issued_by = []
    all_dates = []
    all_surveyors = []
    all_notes = []
    
    # Collect data from all chunks
    for chunk_result in successful_chunks:
        extracted = chunk_result.get('extracted_fields', {})
        chunk_num = chunk_result.get('chunk_num', 0)
        page_range = chunk_result.get('page_range', '')
        
        # Collect values
        if extracted.get('survey_report_name'):
            all_names.append({
                'value': extracted['survey_report_name'],
                'chunk': chunk_num,
                'pages': page_range
            })
        
        if extracted.get('survey_report_no'):
            all_report_nos.append({
                'value': extracted['survey_report_no'],
                'chunk': chunk_num
            })
        
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
        
        if extracted.get('surveyor_name'):
            all_surveyors.append({
                'value': extracted['surveyor_name'],
                'chunk': chunk_num
            })
        
        if extracted.get('note'):
            all_notes.append({
                'value': extracted['note'],
                'chunk': chunk_num,
                'pages': page_range
            })
    
    # Strategy 1: Survey Report Name (prefer first chunk - usually cover page)
    if all_names:
        merged['survey_report_name'] = all_names[0]['value']
        logger.info(f"  📝 Name: '{merged['survey_report_name']}' (from chunk {all_names[0]['chunk']})")
    
    # Strategy 2: Report Number (take first non-empty or most common)
    if all_report_nos:
        # Count occurrences
        report_no_counts = {}
        for item in all_report_nos:
            val = item['value']
            report_no_counts[val] = report_no_counts.get(val, 0) + 1
        
        # Take most common
        merged['survey_report_no'] = max(report_no_counts, key=report_no_counts.get)
        logger.info(f"  🔢 Report No: '{merged['survey_report_no']}' (appears in {report_no_counts[merged['survey_report_no']]} chunk(s))")
    
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
    
    # Strategy 5: Surveyor Name (collect unique names)
    if all_surveyors:
        unique_surveyors = list(set([s['value'] for s in all_surveyors]))
        merged['surveyor_name'] = ', '.join(unique_surveyors)
        logger.info(f"  👤 Surveyors: '{merged['surveyor_name']}'")
    
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
