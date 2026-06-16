# List available commands
default:
    @just --list

# Install dependencies
setup:
    uv sync

# Run all quality checks
check: lint format typecheck test

# Format code
format:
    uv run ruff format src tests

# Run linting checks
lint:
    uv run ruff check src tests

# Auto-fix linting and formatting issues
fix:
    uv run ruff check --fix src tests
    uv run ruff format src tests

# Run type checking
typecheck:
    uv run pyright src tests

# Run tests
test:
    uv run pytest

# Run the CLI tool
run *args:
    uv run python -m pdf_renamer {{args}}

# Build for distribution
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist build *.egg-info .pytest_cache .ruff_cache