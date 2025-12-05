"""
Name matching utility with support for Vietnamese name permutations
"""
import re
import unicodedata
from itertools import permutations
from typing import List, Tuple


def remove_vietnamese_accents(text: str) -> str:
    """
    Remove Vietnamese accents from text.
    Example: "CHƯƠNG SỸ HỌ" -> "CHUONG SY HO"
    """
    if not text:
        return ""
    
    # Normalize to NFD (decomposed form) to separate base characters from accents
    nfd_form = unicodedata.normalize('NFD', text)
    
    # Filter out combining characters (accents)
    # Category 'Mn' = Mark, Nonspacing (accents, diacritics)
    no_accents = ''.join(char for char in nfd_form if unicodedata.category(char) != 'Mn')
    
    # Handle special Vietnamese characters that don't decompose properly
    replacements = {
        'Đ': 'D', 'đ': 'd',
        'Ð': 'D', 'ð': 'd'  # Alternative forms
    }
    
    for viet_char, ascii_char in replacements.items():
        no_accents = no_accents.replace(viet_char, ascii_char)
    
    return no_accents


def normalize_name(name: str) -> str:
    """
    Normalize name for comparison:
    - Remove Vietnamese accents
    - Remove extra spaces
    - Convert to uppercase
    - Remove special characters but keep spaces
    """
    if not name:
        return ""
    
    # Remove Vietnamese accents first
    name = remove_vietnamese_accents(name)
    
    # Remove special characters except spaces
    name = re.sub(r'[^a-zA-Z\s]', '', name)
    
    # Convert to uppercase and remove extra spaces
    name = ' '.join(name.upper().split())
    
    return name


def generate_name_permutations(full_name: str) -> List[str]:
    """
    Generate all possible permutations of a Vietnamese full name.
    
    Vietnamese names typically have format: FAMILY_NAME MIDDLE_NAME GIVEN_NAME
    Example: "TRAN VAN A" can be:
    - TRAN VAN A (original)
    - A TRAN VAN
    - VAN A TRAN
    - TRAN A VAN
    - A VAN TRAN
    - VAN TRAN A
    
    Args:
        full_name: Full name string (e.g., "TRAN VAN A")
        
    Returns:
        List of all permutations
    """
    if not full_name:
        return []
    
    # Normalize the name first
    normalized = normalize_name(full_name)
    
    if not normalized:
        return []
    
    # Split name into parts
    name_parts = normalized.split()
    
    if len(name_parts) <= 1:
        # Single word name, no permutations
        return [normalized]
    
    # Generate all permutations
    perms = permutations(name_parts)
    
    # Join permutations back into strings
    result = [' '.join(perm) for perm in perms]
    
    # Remove duplicates and sort
    result = sorted(list(set(result)))
    
    return result


def check_name_match(
    extracted_name: str, 
    database_name: str,
    database_name_en: str = None
) -> Tuple[bool, float, str]:
    """
    Check if extracted name matches database name (with permutations support).
    
    Args:
        extracted_name: Name extracted from certificate by AI
        database_name: Full name from database (Vietnamese)
        database_name_en: Full name in English from database (optional)
        
    Returns:
        Tuple of (is_match, similarity_score, matched_variant)
        - is_match: True if name matches any permutation
        - similarity_score: 1.0 if exact match, 0.0 if no match
        - matched_variant: Which variant matched (empty if no match)
    """
    if not extracted_name:
        return False, 0.0, ""
    
    # Normalize extracted name
    extracted_normalized = normalize_name(extracted_name)
    
    if not extracted_normalized:
        return False, 0.0, ""
    
    # Generate permutations for database names
    db_permutations = []
    
    # Add Vietnamese name permutations
    if database_name:
        db_permutations.extend(generate_name_permutations(database_name))
    
    # Add English name permutations
    if database_name_en:
        db_permutations.extend(generate_name_permutations(database_name_en))
    
    # Remove duplicates
    db_permutations = list(set(db_permutations))
    
    # Check exact match with any permutation
    for perm in db_permutations:
        if extracted_normalized == perm:
            return True, 1.0, perm
    
    # No exact match found
    return False, 0.0, ""


def format_name_mismatch_message(
    extracted_name: str,
    database_name: str,
    database_name_en: str = None,
    language: str = 'en'
) -> str:
    """
    Format a user-friendly name mismatch message.
    
    Args:
        extracted_name: Name extracted from certificate
        database_name: Database name (Vietnamese)
        database_name_en: Database name (English)
        language: 'vi' or 'en'
        
    Returns:
        Formatted message string
    """
    if language == 'vi':
        msg = "⚠️ Tên trong chứng chỉ không khớp với cơ sở dữ liệu\n\n"
        msg += f"Tên trích xuất từ chứng chỉ: {extracted_name}\n"
        msg += f"Tên trong cơ sở dữ liệu: {database_name}"
        if database_name_en:
            msg += f" ({database_name_en})"
        msg += "\n\nVui lòng kiểm tra lại chứng chỉ."
    else:
        msg = "⚠️ Name mismatch detected\n\n"
        msg += f"Certificate name: {extracted_name}\n"
        msg += f"Database name: {database_name}"
        if database_name_en:
            msg += f" ({database_name_en})"
        msg += "\n\nPlease verify the certificate."
    
    return msg
