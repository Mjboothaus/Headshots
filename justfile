# Headshots Project Justfile

# List available recipes (default)
default:
    @just --list

# Set up the project
setup:
    uv sync

# Run the headshot application
app:
    uv run streamlit run headshot_app.py

# Run the legacy headshot application
legacy_app:
    uv run streamlit run legacy_headshot_app.py

# Run tests
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ -v --cov=headshot_generator --cov-report=term-missing
