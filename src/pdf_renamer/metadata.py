"""Extract metadata from PDF files."""

import re
from pathlib import Path

import pymupdf  # type: ignore[import-untyped]
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def parse_author_name(author_str: str, multiple_authors: bool = False) -> str:
    """Parse author name and return last name, with 'et al.' if multiple authors.

    Args:
        author_str: The author name or names string
        multiple_authors: True if there are multiple authors

    Returns:
        Last name of first author, with 'et al.' appended if multiple_authors is True
    """
    # Get first author if multiple
    if multiple_authors:
        # Extract first author from list
        first_author = re.split(r"[;,]\s*|\s+and\s+", author_str)[0].strip()
        words = first_author.split()
        if words:
            return f"{words[-1]} et al"

    # Single author - just get last name
    words = author_str.split()
    if words:
        return words[-1]

    return author_str


def extract_xmp_metadata(pdf_path: Path) -> dict[str, str] | None:
    """Extract XMP metadata from a PDF file."""
    try:
        with open(pdf_path, "rb") as f:
            reader = PdfReader(f)
            if reader.metadata:
                metadata: dict[str, str] = {}
                if reader.metadata.title:
                    metadata["title"] = str(reader.metadata.title)
                if reader.metadata.author:
                    author_str = str(reader.metadata.author)
                    # Check if there are multiple authors
                    # Common separators in metadata: semicolon, comma, "and"
                    has_multiple = any(sep in author_str for sep in [";", ",", " and "])
                    metadata["author"] = parse_author_name(author_str, has_multiple)
                if hasattr(reader.metadata, "subject") and reader.metadata.subject:
                    metadata["subject"] = str(reader.metadata.subject)
                return metadata if metadata else None
    except (OSError, PdfReadError, ValueError, KeyError, AttributeError):
        # OSError: file doesn't exist or can't be read
        # PdfReadError: corrupted or invalid PDF
        # ValueError/KeyError/AttributeError: unexpected metadata structure
        pass
    return None


def extract_text_from_first_page(pdf_path: Path) -> str | None:
    """Extract text from the first page of a PDF."""
    try:
        doc = pymupdf.open(pdf_path)
        if len(doc) > 0:
            page = doc[0]
            text: str = page.get_text()  # type: ignore[attr-defined]
            doc.close()
            return text  # type: ignore[return-value]
        doc.close()
    except (OSError, RuntimeError, ValueError):
        # OSError: file doesn't exist or can't be read
        # RuntimeError: PyMuPDF errors (corrupted PDF, etc.)
        # ValueError: invalid PDF structure
        pass
    return None


def extract_doi_from_text(text: str) -> str | None:
    """Extract DOI from text."""
    doi_patterns = [
        r"10\.\d{4,}/[-._;()/:\w]+",
        r"doi:\s*10\.\d{4,}/[-._;()/:\w]+",
        r"DOI:\s*10\.\d{4,}/[-._;()/:\w]+",
        r"https?://doi\.org/(10\.\d{4,}/[-._;()/:\w]+)",
    ]

    for pattern in doi_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doi = match.group(0)
            if doi.lower().startswith("doi:"):
                doi = doi[4:].strip()
            elif "doi.org/" in doi:
                doi = doi.split("doi.org/")[-1]
            return doi
    return None


def extract_arxiv_id_from_text(text: str) -> str | None:
    """Extract arXiv ID from text."""
    arxiv_patterns = [
        r"arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)",
        r"(\d{4}\.\d{4,5}(?:v\d+)?)",
    ]

    for pattern in arxiv_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def parse_title_and_authors_from_text(text: str) -> dict[str, str]:
    """Try to extract title and authors from the first page text."""
    lines = text.strip().split("\n")
    metadata: dict[str, str] = {}

    # Look for large text at the beginning (likely title)
    # This is a simple heuristic; in practice, we'd need more sophisticated parsing
    title_candidates: list[str] = []
    author_candidates: list[str] = []

    for i, line in enumerate(lines[:20]):  # Look at first 20 lines
        line = line.strip()
        if not line:
            continue

        # Skip common headers
        if any(header in line.lower() for header in ["abstract", "introduction", "keywords"]):
            break

        # Potential title (usually comes first and is longer)
        if len(line) > 10 and not title_candidates and i < 5:
            title_candidates.append(line)
        # Potential authors (often contains commas or "and")
        elif ("," in line or " and " in line.lower()) and not author_candidates:
            author_candidates.append(line)

    if title_candidates:
        metadata["title"] = title_candidates[0]
    if author_candidates:
        # Parse all authors
        authors_line = author_candidates[0]
        # Split by common separators to check if multiple
        author_list = re.split(r"[,;]\s*|\s+and\s+", authors_line)

        if author_list:
            # Use first author string and indicate if multiple
            has_multiple = len(author_list) > 1
            metadata["author"] = parse_author_name(author_list[0].strip(), has_multiple)

    return metadata

