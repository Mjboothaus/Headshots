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
