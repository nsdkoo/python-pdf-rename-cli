"""Core renaming logic."""

import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing/replacing invalid characters."""
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace multiple spaces with single space
    filename = re.sub(r"\s+", " ", filename)
    # Trim whitespace
    filename = filename.strip()
    # Limit length (leave room for extension)
    if len(filename) > 200:
        filename = filename[:200].rsplit(" ", 1)[0]
    return filename


def generate_zotero_style_filename(metadata: dict[str, str]) -> str | None:
    """Generate a Zotero-style filename from metadata."""
    if not metadata.get("title"):
        return None

    # Basic pattern: Author - Title (Year).pdf
    # or just Title (Year).pdf if no author

    parts: list[str] = []

    if metadata.get("author"):
        parts.append(metadata["author"])

    parts.append(metadata["title"])

    filename = " - ".join(parts)

    if metadata.get("year"):
        filename = f"{filename} ({metadata['year']})"

    # Sanitize the filename
    filename = sanitize_filename(filename)

    return f"{filename}.pdf" if filename else None


def is_generic_filename(filename: str) -> bool:
    """Check if a filename appears to be generic (like arXiv IDs)."""
    name = Path(filename).stem

    # Common patterns for generic filenames
    patterns = [
        r"^\d{4}\.\d{4,5}(?:v\d+)?$",  # arXiv ID (e.g., 1706.03762v7)
        r"^[a-f0-9]{32}$",  # MD5 hash
        r"^[a-f0-9]{40}$",  # SHA1 hash
        r"^[a-f0-9]{64}$",  # SHA-256 hash
        r"^\d+$",  # Just numbers
        r"^download$",  # Common download name
        r"^paper$",  # Generic paper name
        r"^article$",  # Generic article name
        r"^pdf$",  # Just 'pdf'
        r"^file$",  # Just 'file'
        r"^document$",  # Generic document
    ]

    for pattern in patterns:
        if re.match(pattern, name, re.IGNORECASE):
            return True

    return False


def should_rename_file(filepath: Path) -> bool:
    """Determine if a file should be renamed."""
    if not filepath.exists() or not filepath.is_file():
        return False

    if filepath.suffix.lower() != ".pdf":
        return False

    return is_generic_filename(filepath.name)

