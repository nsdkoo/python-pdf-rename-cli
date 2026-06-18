"""Command-line interface for PDF renamer."""

import sys
import traceback
from pathlib import Path

import click

from .lookup import lookup_paper_metadata
from .metadata import (
    extract_text_from_first_page,
    extract_xmp_metadata,
    parse_title_and_authors_from_text,
)
from .renamer import generate_zotero_style_filename, resolve_unique_path, should_rename_file


def collect_files_to_process(paths: tuple[str, ...], recursive: bool = False) -> list[Path]:
    """Collect PDF files to process based on input paths.

    For direct files: processes all PDF files regardless of name.
    For directories: only processes PDFs with generic names.
    """
    files_to_process: list[Path] = []

    for path_str in paths:
        path = Path(path_str).resolve()

        if path.is_file():
            if path.suffix.lower() == ".pdf":
                files_to_process.append(path)
        elif path.is_dir():
            if recursive:
                candidates = (f for f in path.rglob("*.pdf") if f.is_file())
            else:
                candidates = (f for f in path.iterdir() if f.is_file() and f.suffix.lower() == ".pdf")
            for file in candidates:
                if should_rename_file(file):
                    files_to_process.append(file)

    return files_to_process


@click.command()
@click.version_option(version="1.0.0", prog_name="pdf-renamer")
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True))
@click.option("--dry-run", "-n", is_flag=True, help="Show what would be renamed without doing it")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed processing information")
@click.option("--recursive", "-R", is_flag=True, help="Recursively scan subdirectories for generic PDF names")
def main(paths: tuple[str, ...], dry_run: bool, verbose: bool, recursive: bool) -> None:
    """Rename PDF files to include author name and paper title, like Zotero.

    For directories, only renames directly nested PDF files with generic names
    like arXiv IDs (e.g., 1706.03762v7.pdf).
    """
    # Collect files and handle error cases
    files_to_process: list[Path] = []

    for path_str in paths:
        path = Path(path_str).resolve()

        if not path.exists():
            click.echo(f"Path does not exist: {path}", err=True)
            continue
        elif path.is_file() and path.suffix.lower() != ".pdf":
            click.echo(f"Skipping non-PDF file: {path}", err=True)
            continue

        # Use the extracted function for valid paths
        valid_files = collect_files_to_process((path_str,), recursive=recursive)
        files_to_process.extend(valid_files)

    if not files_to_process:
        click.echo("No suitable PDF files found to rename.")
        return

    # Process each file
    renamed_count = 0
    failed_count = 0

    for pdf_path in files_to_process:
        click.echo(f"\nProcessing: {pdf_path.name}")

        try:
            # Step 1: Try to extract XMP metadata
            if verbose:
                click.echo("  Checking XMP metadata...")
            metadata = extract_xmp_metadata(pdf_path)

            # Step 2: Extract text from first page
            if verbose:
                click.echo("  Extracting text from first page...")
            first_page_text = extract_text_from_first_page(pdf_path)

            # Only abort if we have no metadata AND no text
            # (scanned PDFs with XMP metadata should still be renamed)
            if not first_page_text and not metadata:
                click.echo(f"  Failed to extract text from {pdf_path.name}", err=True)
                failed_count += 1
                continue

            # Step 3: Try online lookup if we don't have good metadata
            if first_page_text and (not metadata or not metadata.get("title")):
                if verbose:
                    click.echo("  Looking up metadata online...")
                online_metadata = lookup_paper_metadata(first_page_text, metadata)
                if online_metadata:
                    metadata = online_metadata
                    if verbose:
                        click.echo("  Found metadata online!")

            # Step 4: Fall back to parsing text if still no metadata
            if first_page_text and (not metadata or not metadata.get("title")):
                if verbose:
                    click.echo("  Parsing title and authors from text...")
                parsed_metadata = parse_title_and_authors_from_text(first_page_text)
                if parsed_metadata:
                    metadata = parsed_metadata

            # Step 5: Generate new filename
            if metadata and metadata.get("title"):
                new_filename = generate_zotero_style_filename(metadata)
                if new_filename:
                    new_path = resolve_unique_path(pdf_path.parent, new_filename)

                    if dry_run:
                        click.echo(f"  Would rename to: {new_path.name}")
                    else:
                        pdf_path.rename(new_path)
                        click.echo(f"  Renamed to: {new_path.name}")
                    renamed_count += 1
                else:
                    click.echo(f"  Could not generate filename for {pdf_path.name}", err=True)
                    failed_count += 1
            else:
                click.echo(f"  No metadata found for {pdf_path.name}", err=True)
                failed_count += 1

        except Exception as e:
            click.echo(f"  Error processing {pdf_path.name}: {e}", err=True)
            if verbose:
                click.echo("  Traceback:", err=True)
                traceback.print_exc(file=sys.stderr)
            failed_count += 1

    # Summary
    click.echo(f"\n{'Would rename' if dry_run else 'Renamed'}: {renamed_count} file(s)")
    if failed_count:
        click.echo(f"Failed: {failed_count} file(s)")


if __name__ == "__main__":
    main()

