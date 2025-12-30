"""
Resume Parser - PDF Handler

Extracts text content from PDF resume files using pdfplumber.
Handles both well-formatted and messy PDF layouts.
"""

import io
import re
from typing import Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    This function handles various PDF layouts and attempts to preserve
    the reading order of text. It works with:
    - Text-based PDFs (directly selectable text)
    - Simple layouts with columns
    
    Note: OCR is not performed for image-based PDFs (would require additional
    dependencies like tesseract). These cases are flagged in the output.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        Extracted text content as a string
        
    Raises:
        ValueError: If pdfplumber is not installed
        RuntimeError: If PDF parsing fails
    """
    if pdfplumber is None:
        raise ValueError(
            "pdfplumber is required for PDF parsing. "
            "Install it with: pip install pdfplumber"
        )
    
    try:
        # Create a file-like object from bytes
        pdf_stream = io.BytesIO(file_content)
        
        all_text_parts = []
        
        with pdfplumber.open(pdf_stream) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from the page
                page_text = page.extract_text()
                
                if page_text:
                    # Clean up the extracted text
                    page_text = _clean_pdf_text(page_text)
                    all_text_parts.append(page_text)
                else:
                    # Page might be image-based or empty
                    # We add a note for the analyzer to consider
                    if page.images:
                        all_text_parts.append(
                            f"\n[Note: Page {page_num} appears to contain images/graphics "
                            "that may affect ATS parsing]\n"
                        )
        
        if not all_text_parts:
            return "[Warning: No text could be extracted from this PDF. " \
                   "The file may be image-based or empty.]"
        
        return "\n\n".join(all_text_parts)
    
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF: {str(e)}") from e


def _clean_pdf_text(text: str) -> str:
    """
    Clean up extracted PDF text.
    
    PDF extraction often produces artifacts like:
    - Excessive whitespace
    - Broken lines
    - Special characters
    
    This function normalizes the text while preserving structure.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Replace multiple spaces with single space (but preserve newlines)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove excessive internal whitespace
        line = re.sub(r' +', ' ', line)
        # Remove leading/trailing whitespace from each line
        line = line.strip()
        cleaned_lines.append(line)
    
    # Join lines, removing empty lines that occur more than twice in a row
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{4,}', '\n\n\n', result)
    
    return result


def has_tables(file_content: bytes) -> bool:
    """
    Check if a PDF contains tables.
    
    Tables can affect ATS parsing, so this is useful for ATS analysis.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        True if tables are detected, False otherwise
    """
    if pdfplumber is None:
        return False
    
    try:
        pdf_stream = io.BytesIO(file_content)
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                tables = page.find_tables()
                if tables:
                    return True
        return False
    except Exception:
        return False


def has_images(file_content: bytes) -> bool:
    """
    Check if a PDF contains images/graphics.
    
    Heavy use of images can affect ATS parsing.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        True if images are detected, False otherwise
    """
    if pdfplumber is None:
        return False
    
    try:
        pdf_stream = io.BytesIO(file_content)
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                if page.images:
                    return True
        return False
    except Exception:
        return False


def get_pdf_metadata(file_content: bytes) -> dict:
    """
    Extract metadata from a PDF file.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        Dictionary containing metadata (author, title, etc.)
    """
    if pdfplumber is None:
        return {}
    
    try:
        pdf_stream = io.BytesIO(file_content)
        with pdfplumber.open(pdf_stream) as pdf:
            return pdf.metadata or {}
    except Exception:
        return {}
