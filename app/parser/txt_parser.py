"""
Resume Parser - Plain Text Handler

Handles plain text resume files (.txt).
Minimal processing needed, but includes cleanup for common issues.
"""

import re


def extract_text_from_txt(file_content: bytes, encoding: str = 'utf-8') -> str:
    """
    Extract text content from a plain text file.
    
    Handles various encodings and normalizes line endings.
    
    Args:
        file_content: Raw bytes of the text file
        encoding: Text encoding (default: utf-8)
        
    Returns:
        Cleaned text content as a string
        
    Raises:
        RuntimeError: If text decoding fails
    """
    # Try specified encoding first, then fall back to common encodings
    encodings_to_try = [encoding, 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    text = None
    for enc in encodings_to_try:
        try:
            text = file_content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    
    if text is None:
        raise RuntimeError(
            "Failed to decode text file. Tried encodings: " + 
            ", ".join(encodings_to_try)
        )
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Clean up the text
    text = _clean_text_file(text)
    
    return text


def _clean_text_file(text: str) -> str:
    """
    Clean up text content from a file.
    
    Handles common issues like:
    - BOM characters
    - Excessive whitespace
    - Control characters
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text
    """
    # Remove BOM if present
    if text.startswith('\ufeff'):
        text = text[1:]
    
    # Remove null bytes and other control characters (except newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Normalize multiple blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    # Clean up each line
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        # Normalize internal whitespace (but preserve intentional indentation)
        if line.strip():
            # Keep leading whitespace, clean up rest
            leading_space = len(line) - len(line.lstrip())
            line = ' ' * leading_space + re.sub(r' +', ' ', line.lstrip())
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
