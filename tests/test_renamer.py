"""Tests for PDF renaming logic."""

from pathlib import Path

from pdf_renamer.renamer import (
    generate_zotero_style_filename,
    is_generic_filename,
    sanitize_filename,
    should_rename_file,
)


class TestGenerateZoteroStyleFilename:
    """Test filename generation with various metadata combinations."""

    def test_full_metadata(self) -> None:
        """Test with complete metadata (author, title, year)."""
        metadata = {
            "author": "Smith",
            "title": "A Study of Machine Learning",
            "year": "2023",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Smith - A Study of Machine Learning (2023).pdf"

    def test_title_and_author_no_year(self) -> None:
        """Test with title and author but no year."""
        metadata = {
            "author": "Johnson",
            "title": "Deep Learning Fundamentals",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Johnson - Deep Learning Fundamentals.pdf"

    def test_title_only(self) -> None:
        """Test with title only."""
        metadata = {
            "title": "Artificial Intelligence in Healthcare",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Artificial Intelligence in Healthcare.pdf"

    def test_title_and_year_no_author(self) -> None:
        """Test with title and year but no author."""
        metadata = {
            "title": "Natural Language Processing",
            "year": "2022",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Natural Language Processing (2022).pdf"

    def test_no_title_returns_none(self) -> None:
        """Test that missing title returns None."""
        metadata: dict[str, str] = {
            "author": "Brown",
            "year": "2021",
        }
        result = generate_zotero_style_filename(metadata)
        assert result is None

    def test_empty_metadata_returns_none(self) -> None:
        """Test that empty metadata returns None."""
        metadata: dict[str, str] = {}
        result = generate_zotero_style_filename(metadata)
        assert result is None

    def test_title_with_special_characters(self) -> None:
        """Test that special characters are sanitized."""
        metadata = {
            "author": "Wilson",
            "title": "AI: The Future? A <Comprehensive> Study",
            "year": "2024",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Wilson - AI The Future A Comprehensive Study (2024).pdf"

    def test_very_long_title_is_truncated(self) -> None:
        """Test that very long titles are truncated."""
        long_title = "A" * 250  # Very long title
        metadata = {
            "author": "Davis",
            "title": long_title,
            "year": "2023",
        }
        result = generate_zotero_style_filename(metadata)
        assert result is not None
        assert len(result) <= 204  # 200 + ".pdf"
        assert "Davis" in result
        assert result.endswith(".pdf")

    def test_multiple_spaces_normalized(self) -> None:
        """Test that multiple spaces are normalized to single spaces."""
        metadata = {
            "author": "Miller",
            "title": "Machine    Learning     with    Python",
            "year": "2023",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Miller - Machine Learning with Python (2023).pdf"


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_removes_invalid_characters(self) -> None:
        """Test that invalid filename characters are removed."""
        filename = 'file<>:"/\\|?*name'
        result = sanitize_filename(filename)
        assert result == "filename"

    def test_normalizes_spaces(self) -> None:
        """Test that multiple spaces are normalized."""
        filename = "file   with    many     spaces"
        result = sanitize_filename(filename)
        assert result == "file with many spaces"

    def test_strips_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        filename = "  filename with spaces  "
        result = sanitize_filename(filename)
        assert result == "filename with spaces"

    def test_truncates_long_filenames(self) -> None:
        """Test that very long filenames are truncated."""
        long_filename = "a" * 250
        result = sanitize_filename(long_filename)
        assert len(result) <= 200


class TestIsGenericFilename:
    """Test generic filename detection."""

    def test_arxiv_id_patterns(self) -> None:
        """Test that arXiv ID patterns are detected as generic."""
        assert is_generic_filename("1706.03762v7.pdf")
        assert is_generic_filename("2310.01889v4.pdf")
        assert is_generic_filename("1234.5678.pdf")
        assert is_generic_filename("0901.2345v1.pdf")

    def test_hash_patterns(self) -> None:
        """Test that hash-like patterns are detected as generic."""
        # MD5 (32 chars)
        assert is_generic_filename("a1b2c3d4e5f678901234567890123456.pdf")
        # SHA1 (40 chars)
        assert is_generic_filename("a1b2c3d4e5f6789012345678901234567890abcd.pdf")
        # SHA-256 (64 chars)
        assert is_generic_filename(
            "a1b2c3d4e5f6789012345678901234567890abcdef1234567890123456789012.pdf"
        )

    def test_generic_names(self) -> None:
        """Test that common generic names are detected."""
        assert is_generic_filename("download.pdf")
        assert is_generic_filename("paper.pdf")
        assert is_generic_filename("article.pdf")
        assert is_generic_filename("document.pdf")
        assert is_generic_filename("file.pdf")
        assert is_generic_filename("pdf.pdf")
        assert is_generic_filename("123456.pdf")

    def test_case_insensitive(self) -> None:
        """Test that detection is case insensitive."""
        assert is_generic_filename("DOWNLOAD.PDF")
        assert is_generic_filename("Paper.PDF")
        assert is_generic_filename("DOCUMENT.pdf")

    def test_descriptive_names_not_generic(self) -> None:
        """Test that descriptive filenames are not considered generic."""
        assert not is_generic_filename("attention-is-all-you-need.pdf")
        assert not is_generic_filename("smith-2023-machine-learning.pdf")
        assert not is_generic_filename("my-research-paper.pdf")
        assert not is_generic_filename("thesis-final.pdf")


class TestShouldRenameFile:
    """Test file renaming decision logic."""

    def test_should_rename_generic_pdf(self, tmp_path: Path) -> None:
        """Test that generic PDF files should be renamed."""
        pdf_file = tmp_path / "1706.03762v7.pdf"
        pdf_file.write_text("dummy content")

        assert should_rename_file(pdf_file)

    def test_should_not_rename_descriptive_pdf(self, tmp_path: Path) -> None:
        """Test that descriptive PDF files should not be renamed."""
        pdf_file = tmp_path / "attention-paper.pdf"
        pdf_file.write_text("dummy content")

        assert not should_rename_file(pdf_file)

    def test_should_not_rename_non_pdf(self, tmp_path: Path) -> None:
        """Test that non-PDF files should not be renamed."""
        txt_file = tmp_path / "download.txt"
        txt_file.write_text("dummy content")

        assert not should_rename_file(txt_file)

    def test_should_not_rename_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that nonexistent files should not be renamed."""
        nonexistent = tmp_path / "nonexistent.pdf"

        assert not should_rename_file(nonexistent)

    def test_should_not_rename_directory(self, tmp_path: Path) -> None:
        """Test that directories should not be renamed."""
        directory = tmp_path / "download.pdf"
        directory.mkdir()

        assert not should_rename_file(directory)


class TestMetadataCombinations:
    """Test realistic metadata combinations from different sources."""

    def test_crossref_metadata(self) -> None:
        """Test metadata from CrossRef API."""
        metadata = {
            "title": "Attention Is All You Need",
            "author": "Vaswani",
            "year": "2017",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Vaswani - Attention Is All You Need (2017).pdf"

    def test_arxiv_metadata(self) -> None:
        """Test metadata from arXiv API."""
        metadata = {
            "title": "Ring Attention with Blockwise Transformers for Near-Infinite Context",
            "author": "Liu",
            "year": "2023",
        }
        result = generate_zotero_style_filename(metadata)
        expected = (
            "Liu - Ring Attention with Blockwise Transformers for Near-Infinite Context (2023).pdf"
        )
        assert result == expected

    def test_parsed_text_metadata_complete(self) -> None:
        """Test metadata parsed from PDF text with complete info."""
        metadata = {
            "title": "Deep Learning for Natural Language Processing",
            "author": "Zhang",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Zhang - Deep Learning for Natural Language Processing.pdf"

    def test_parsed_text_metadata_title_only(self) -> None:
        """Test metadata parsed from PDF text with title only."""
        metadata = {
            "title": "A Survey of Machine Learning Techniques",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "A Survey of Machine Learning Techniques.pdf"

    def test_metadata_with_complex_author_name(self) -> None:
        """Test metadata with complex author names."""
        metadata = {
            "title": "Advanced Neural Networks",
            "author": "van der Berg",  # Complex last name
            "year": "2022",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "van der Berg - Advanced Neural Networks (2022).pdf"

    def test_metadata_with_unicode_characters(self) -> None:
        """Test metadata with Unicode characters."""
        metadata = {
            "title": "R茅sum茅 of AI Research",
            "author": "Garc铆a",
            "year": "2023",
        }
        result = generate_zotero_style_filename(metadata)
        assert result == "Garc铆a - R茅sum茅 of AI Research (2023).pdf"

