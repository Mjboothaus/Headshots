# Headshots Project Justfile
# Cross-platform recipes for development workflow

# List available recipes (default)
default:
    @just --list

# Set up the project environment
setup:
    uv sync
    @echo "✅ Project setup complete! Virtual environment created and dependencies installed."

# Run the Streamlit application
run:
    uv run streamlit run headshot_app.py

# Run the app with custom host and port
serve host="localhost" port="8501":
    uv run streamlit run headshot_app.py --server.address {{host}} --server.port {{port}}

# Add a new dependency
add package:
    uv add {{package}}
    @echo "✅ Added {{package}} to dependencies"

# Add a development dependency
add-dev package:
    uv add --dev {{package}}
    @echo "✅ Added {{package}} to development dependencies"

# Update dependencies
update:
    uv sync --upgrade
    @echo "✅ Dependencies updated"

# Show project info
info:
    @echo "📋 Project Information:"
    @echo "  Name: Headshots"
    @echo "  Python: $(uv run python --version)"
    @echo "  Dependencies:"
    @uv tree

# Clean up generated files and cache
clean:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🧹 Cleaning up..."
    # Remove Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    # Remove Streamlit cache
    rm -rf .streamlit 2>/dev/null || true
    # Remove any downloaded headshot files (but keep the structure)
    find images -name "*.jpg" -o -name "*.png" | grep -v ".gitkeep" | head -5 | while read file; do
        echo "  Removing: $file"
        rm -f "$file"
    done
    echo "✅ Cleanup complete"

# Check code formatting and style
lint:
    @echo "🔍 Checking code formatting..."
    -uv run ruff check headshot_app.py
    @echo "✅ Linting complete"

# Format code
format:
    @echo "🎨 Formatting code..."
    -uv run ruff format headshot_app.py
    @echo "✅ Code formatted"

# Check if all dependencies are properly installed
doctor:
    @echo "🏥 Running project health check..."
    @echo "Python version:"
    @uv run python --version
    @echo ""
    @echo "Testing critical imports:"
    @uv run python -c "import streamlit; print('✅ streamlit:', streamlit.__version__)"
    @uv run python -c "import cv2; print('✅ opencv-python:', cv2.__version__)"
    @uv run python -c "import PIL; print('✅ pillow:', PIL.__version__)"
    @uv run python -c "import numpy; print('✅ numpy:', numpy.__version__)"
    @uv run python -c "import toml; print('✅ toml: OK')"
    @echo ""
    @echo "Configuration files:"
    @test -f config.toml && echo "✅ config.toml exists" || echo "❌ config.toml missing"
    @test -f pyproject.toml && echo "✅ pyproject.toml exists" || echo "❌ pyproject.toml missing"
    @echo ""
    @echo "🎉 Health check complete!"

# Create a sample image directory structure
init-images:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📁 Creating image directory structure..."
    mkdir -p images/samples
    touch images/.gitkeep
    touch images/samples/.gitkeep
    echo "✅ Image directories created"
    echo "  📁 images/"
    echo "  📁 images/samples/"
    echo ""
    echo "💡 Place your images in the images/ or images/samples/ directory"

# Git workflow helpers
commit message:
    git add -A
    git commit -m "{{message}}"

# Push changes to GitHub
push:
    git push origin main

# Pull latest changes
pull:
    git pull origin main

# Show git status
status:
    @git status --short

# Create a new feature branch
branch name:
    git checkout -b feature/{{name}}
    @echo "✅ Created and switched to branch: feature/{{name}}"

# Development workflow - setup, install dev tools, and run
dev:
    @echo "🚀 Setting up development environment..."
    uv sync
    -uv add --dev ruff
    @echo "✅ Development environment ready!"
    @echo ""
    @echo "Available commands:"
    @just --list

# Quick start - setup and run
start:
    @just setup
    @echo ""
    @echo "🚀 Starting the application..."
    @just run