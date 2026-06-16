"""Tests for file selection logic."""

from pathlib import Path

from pdf_renamer.__main__ import collect_files_to_process


class TestCollectFilesToProcess:
    """Test the file collection logic."""

    def test_direct_pdf_file_included(self, tmp_path: Path) -> None:
        """Test that directly specified PDF files are always included."""
        # Create PDF with descriptive name
        descriptive_pdf = tmp_path / "attention-paper.pdf"
        descriptive_pdf.write_text("dummy content")

        files = collect_files_to_process((str(descriptive_pdf),))

        assert len(files) == 1
        assert files[0] == descriptive_pdf

    def test_direct_generic_pdf_file_included(self, tmp_path: Path) -> None:
        """Test that directly specified generic PDF files are included."""
        # Create PDF with generic name
        generic_pdf = tmp_path / "1706.03762v7.pdf"
        generic_pdf.write_text("dummy content")

        files = collect_files_to_process((str(generic_pdf),))

        assert len(files) == 1
        assert files[0] == generic_pdf

    def test_directory_only_includes_generic_pdfs(self, tmp_path: Path) -> None:
        """Test that directory processing only includes generic PDFs."""
        # Create both generic and descriptive PDFs
        generic_pdf = tmp_path / "2310.01889v4.pdf"
        generic_pdf.write_text("dummy content")

        descriptive_pdf = tmp_path / "attention-paper.pdf"
        descriptive_pdf.write_text("dummy content")

        another_generic = tmp_path / "download.pdf"
        another_generic.write_text("dummy content")

        files = collect_files_to_process((str(tmp_path),))

        # Should only include generic files
        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "2310.01889v4.pdf" in file_names
        assert "download.pdf" in file_names
        assert "attention-paper.pdf" not in file_names

    def test_mixed_direct_and_directory_args(self, tmp_path: Path) -> None:
        """Test mixing direct file and directory arguments."""
        # Create directory with files
        subdir = tmp_path / "papers"
        subdir.mkdir()

        dir_generic = subdir / "1234.5678v1.pdf"
        dir_generic.write_text("dummy content")

        dir_descriptive = subdir / "good-name.pdf"
        dir_descriptive.write_text("dummy content")

        # Create direct file
        direct_file = tmp_path / "my-paper.pdf"
        direct_file.write_text("dummy content")

        files = collect_files_to_process((str(direct_file), str(subdir)))

        # Should include direct file + generic file from directory
        assert len(files) == 2
        file_names = {f.name for f in files}
        assert "my-paper.pdf" in file_names  # Direct file (descriptive name)
        assert "1234.5678v1.pdf" in file_names  # Generic from directory
        assert "good-name.pdf" not in file_names  # Descriptive from directory

    def test_non_pdf_files_excluded(self, tmp_path: Path) -> None:
        """Test that non-PDF files are excluded."""
        txt_file = tmp_path / "document.txt"
        txt_file.write_text("not a pdf")

        files = collect_files_to_process((str(txt_file),))

        assert len(files) == 0

    def test_nonexistent_paths_excluded(self) -> None:
        """Test that nonexistent paths are excluded."""
        files = collect_files_to_process(("/nonexistent/path.pdf",))

        assert len(files) == 0

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test that empty directories return no files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        files = collect_files_to_process((str(empty_dir),))

        assert len(files) == 0

    def test_directory_with_only_descriptive_pdfs(self, tmp_path: Path) -> None:
        """Test directory with only descriptive PDFs returns no files."""
        good_pdf1 = tmp_path / "well-named-paper.pdf"
        good_pdf1.write_text("dummy content")

        good_pdf2 = tmp_path / "another-good-name.pdf"
        good_pdf2.write_text("dummy content")

        files = collect_files_to_process((str(tmp_path),))

        assert len(files) == 0

    def test_multiple_direct_files(self, tmp_path: Path) -> None:
        """Test processing multiple directly specified files."""
        file1 = tmp_path / "paper1.pdf"
        file1.write_text("dummy content")

        file2 = tmp_path / "1234.5678.pdf"  # Generic
        file2.write_text("dummy content")

        file3 = tmp_path / "paper3.pdf"
        file3.write_text("dummy content")

        files = collect_files_to_process((str(file1), str(file2), str(file3)))

        # All should be included since they're direct files
        assert len(files) == 3
        file_names = {f.name for f in files}
        assert file_names == {"paper1.pdf", "1234.5678.pdf", "paper3.pdf"}

    def test_nested_directories_not_processed(self, tmp_path: Path) -> None:
        """Test that nested directories are not processed."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Generic PDF in main directory
        main_pdf = tmp_path / "download.pdf"
        main_pdf.write_text("dummy content")

        # Generic PDF in subdirectory (should NOT be processed)
        nested_pdf = subdir / "1234.5678.pdf"
        nested_pdf.write_text("dummy content")

        files = collect_files_to_process((str(tmp_path),))

        # Should only find the PDF in the main directory
        assert len(files) == 1
        assert files[0].name == "download.pdf"

    def test_case_insensitive_pdf_extension(self, tmp_path: Path) -> None:
        """Test that PDF extension matching is case insensitive for direct files."""
        pdf_upper = tmp_path / "test.PDF"
        pdf_upper.write_text("dummy content")

        pdf_mixed = tmp_path / "test2.Pdf"
        pdf_mixed.write_text("dummy content")

        files = collect_files_to_process((str(pdf_upper), str(pdf_mixed)))

        assert len(files) == 2

    def test_case_insensitive_pdf_extension_in_directory(self, tmp_path: Path) -> None:
        """Test that PDF extension matching is case insensitive for directories."""
        # Create generic PDF files with different case extensions
        pdf_upper = tmp_path / "download.PDF"
        pdf_upper.write_text("dummy content")

        pdf_mixed = tmp_path / "1234.5678v1.Pdf"
        pdf_mixed.write_text("dummy content")

        pdf_lower = tmp_path / "paper.pdf"
        pdf_lower.write_text("dummy content")

        files = collect_files_to_process((str(tmp_path),))

        # All three should be found despite different case extensions
        assert len(files) == 3
        file_names = {f.name for f in files}
        assert "download.PDF" in file_names
        assert "1234.5678v1.Pdf" in file_names
        assert "paper.pdf" in file_names

