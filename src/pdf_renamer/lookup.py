"""Look up paper metadata from online databases."""

import re
from json import JSONDecodeError
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException

# CrossRef API returns hyphenated keys which are hard to handle with TypedDict
# We'll use dict[str, Any] and validate at runtime


def lookup_crossref(doi: str) -> dict[str, str] | None:
    """Look up metadata from CrossRef using DOI."""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        headers = {"User-Agent": "Rename-Academic-PDF/1.0 (mailto:steele@.com)"}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data: dict[str, Any] = response.json()
            message: dict[str, Any] = data.get("message", {})

            metadata: dict[str, str] = {}

            # Extract title
            if "title" in message and message["title"]:
                metadata["title"] = message["title"][0]

            # Extract first author's family name
            if "author" in message and message["author"]:
                first_author = message["author"][0]
                if "family" in first_author:
                    metadata["author"] = first_author["family"]

            # Extract year
            if "published-print" in message:
                date_parts = message["published-print"].get("date-parts", [])
                if date_parts and date_parts[0]:
                    metadata["year"] = str(date_parts[0][0])
            elif "published-online" in message:
                date_parts = message["published-online"].get("date-parts", [])
                if date_parts and date_parts[0]:
                    metadata["year"] = str(date_parts[0][0])

            return metadata if metadata else None
    except (RequestException, JSONDecodeError, KeyError, ValueError):
        # RequestException: network errors, timeouts, connection issues
        # JSONDecodeError: invalid JSON response
        # KeyError/ValueError: unexpected response structure
        pass
    return None


def lookup_arxiv(arxiv_id: str) -> dict[str, str] | None:
    """Look up metadata from arXiv."""
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "xml")
            entry = soup.find("entry")

            if isinstance(entry, Tag):
                metadata: dict[str, str] = {}

                # Extract title
                title = entry.find("title")
                if isinstance(title, Tag):
                    metadata["title"] = title.get_text(strip=True)

                # Extract first author
                authors = entry.find_all("author")
                if authors:
                    first_author = authors[0]
                    if isinstance(first_author, Tag):
                        name_elem = first_author.find("name")
                        if isinstance(name_elem, Tag):
                            first_author_name = name_elem.get_text(strip=True)
                            # Extract last name
                            words = first_author_name.split()
                            if words:
                                metadata["author"] = words[-1]

                # Extract year from published date
                published = entry.find("published")
                if isinstance(published, Tag):
                    published_text = published.get_text(strip=True)
                    year_match = re.match(r"(\d{4})", published_text)
                    if year_match:
                        metadata["year"] = year_match.group(1)

                return metadata if metadata else None
    except (RequestException, ValueError, AttributeError):
        # RequestException: network errors, timeouts, connection issues
        # ValueError: XML parsing errors
        # AttributeError: unexpected XML structure
        pass
    return None


def lookup_paper_metadata(
    text: str, xmp_metadata: dict[str, str] | None = None
) -> dict[str, str] | None:
    """Try to look up paper metadata from various sources."""
    from .metadata import extract_arxiv_id_from_text, extract_doi_from_text

    # Try DOI first
    doi = extract_doi_from_text(text)
    if doi:
        metadata = lookup_crossref(doi)
        if metadata:
            return metadata

    # Try arXiv
    arxiv_id = extract_arxiv_id_from_text(text)
    if arxiv_id:
        metadata = lookup_arxiv(arxiv_id)
        if metadata:
            return metadata

    # Add more lookup methods here (PubMed, Google Scholar, etc.)
    # Note: Google Scholar doesn't have a public API and scraping is against TOS

    return None

