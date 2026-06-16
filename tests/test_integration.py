"""Integration tests with synthetic PDFs."""

from pathlib import Path

from pypdf import PdfWriter


def create_pdf_with_metadata(
    path: Path, title: str | None = None, author: str | None = None
) -> None:
    """Create a minimal PDF with embedded XMP metadata but no text.

    This simulates a scanned PDF with metadata.
    """
    writer = PdfWriter()
    # Add a blank page (no text layer)
    writer.add_blank_page(width=612, height=792)  # Standard letter size

    # Set metadata
    if title or author:
        metadata_dict: dict[str, str] = {}
        if title:
            metadata_dict["/Title"] = title
        if author:
            metadata_dict["/Author"] = author
        writer.add_metadata(metadata_dict)

    # Write to file
    with open(path, "wb") as f:
        writer.write(f)


class TestXMPOnlyRename:
    """Test that PDFs with XMP metadata but no text can be renamed."""

    def test_scanned_pdf_with_xmp_metadata(self, tmp_path: Path) -> None:
        """Test that a scanned PDF with XMP metadata can be renamed."""
        from pdf_renamer.metadata import extract_xmp_metadata
        from pdf_renamer.renamer import generate_zotero_style_filename

        # Create a PDF with metadata but no text (simulates scanned PDF)
        pdf_path = tmp_path / "download.pdf"
        create_pdf_with_metadata(pdf_path, title="Test Paper Title", author="John Smith")

        # Verify we can extract the metadata
        metadata = extract_xmp_metadata(pdf_path)
        assert metadata is not None
        assert metadata.get("title") == "Test Paper Title"
        assert metadata.get("author") == "Smith"  # Should extract last name

        # Verify we can generate a filename
        filename = generate_zotero_style_filename(metadata)
        assert filename == "Smith - Test Paper Title.pdf"

    def test_scanned_pdf_with_xmp_metadata_and_year(self, tmp_path: Path) -> None:
        """Test scanned PDF with full metadata including year."""
        from pypdf import PdfWriter

        from pdf_renamer.metadata import extract_xmp_metadata

        # Create PDF with complete metadata
        pdf_path = tmp_path / "1234.5678v1.pdf"
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)

        # Add metadata with year (using subject field as a workaround)
        writer.add_metadata(
            {
                "/Title": "Deep Learning Survey",
                "/Author": "Jane Doe",
                "/Subject": "2023",  # Store year in subject for testing
            }
        )

        with open(pdf_path, "wb") as f:
            writer.write(f)

        # Extract and verify
        metadata = extract_xmp_metadata(pdf_path)
        assert metadata is not None
        assert metadata.get("title") == "Deep Learning Survey"
        assert metadata.get("author") == "Doe"

        # Note: Year extraction from XMP is limited in current implementation
        # This test verifies the other fields work correctly

    def test_scanned_pdf_with_multiple_authors(self, tmp_path: Path) -> None:
        """Test scanned PDF with multiple authors."""
        from pdf_renamer.metadata import extract_xmp_metadata

        pdf_path = tmp_path / "paper.pdf"
        create_pdf_with_metadata(
            pdf_path,
            title="Multi-Author Paper",
            author="Alice Johnson, Bob Smith, Charlie Brown",
        )

        metadata = extract_xmp_metadata(pdf_path)
        assert metadata is not None
        assert metadata.get("title") == "Multi-Author Paper"
        # Should get first author's last name + "et al"
        assert metadata.get("author") == "Johnson et al"


class TestMetadataExtraction:
    """Test metadata extraction from various PDF types."""

    def test_pdf_with_no_metadata(self, tmp_path: Path) -> None:
        """Test that PDF with no metadata returns None."""
        from pdf_renamer.metadata import extract_xmp_metadata

        pdf_path = tmp_path / "blank.pdf"
        create_pdf_with_metadata(pdf_path)  # No title or author

        metadata = extract_xmp_metadata(pdf_path)
        # Should return None when no useful metadata
        assert metadata is None or not metadata.get("title")

    def test_pdf_with_title_only(self, tmp_path: Path) -> None:
        """Test PDF with title but no author."""
        from pdf_renamer.metadata import extract_xmp_metadata
        from pdf_renamer.renamer import generate_zotero_style_filename

        pdf_path = tmp_path / "download.pdf"
        create_pdf_with_metadata(pdf_path, title="Untitled Research Paper")

        metadata = extract_xmp_metadata(pdf_path)
        assert metadata is not None
        assert metadata.get("title") == "Untitled Research Paper"
        assert not metadata.get("author")

        # Should still generate filename without author
        filename = generate_zotero_style_filename(metadata)
        assert filename == "Untitled Research Paper.pdf"

