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

# Ensure Docker Desktop is running (macOS)
ensure-docker:
    #!/bin/bash
    if ! docker info >/dev/null 2>&1; then
        echo "Docker is not running. Checking if Docker Desktop is available..."
        if [ -d "/Applications/Docker.app" ]; then
            echo "Starting Docker Desktop..."
            open -a Docker
            echo "Waiting for Docker Desktop to start..."
            # Wait up to 60 seconds for Docker to be ready
            for i in {1..12}; do
                if docker info >/dev/null 2>&1; then
                    echo "Docker Desktop is now running!"
                    break
                fi
                echo "Waiting... ($i/12)"
                sleep 5
            done
            # Final check
            if ! docker info >/dev/null 2>&1; then
                echo "ERROR: Docker Desktop failed to start within 60 seconds"
                echo "Please start Docker Desktop manually and try again"
                exit 1
            fi
        else
            echo "ERROR: Docker Desktop not found at /Applications/Docker.app"
            echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
            exit 1
        fi
    else
        echo "✓ Docker is running"
    fi

# Build Docker image for local testing
docker-build: ensure-docker
    echo "Building Docker image: headshot-generator"
    docker build -t headshot-generator .
    echo "✓ Docker image built successfully"

# Run Docker container locally
docker-run: ensure-docker
    echo "Running headshot-generator container on http://localhost:10000"
    docker run --rm -p 10000:10000 --name headshot-generator-local headshot-generator

# Run Docker container in detached mode
docker-run-detached: ensure-docker
    echo "Starting headshot-generator container in background on http://localhost:10000"
    docker run -d -p 10000:10000 --name headshot-generator-local headshot-generator
    echo "✓ Container started. Access at http://localhost:10000"
    echo "Stop with: just docker-stop"

# Stop running Docker container
docker-stop:
    echo "Stopping headshot-generator container..."
    docker stop headshot-generator-local || echo "Container not running"
    docker rm headshot-generator-local 2>/dev/null || true
    echo "✓ Container stopped"

# Build and run Docker container (full workflow)
docker-dev: docker-build docker-run-detached
    echo "✓ Development Docker environment ready at http://localhost:10000"
    echo "View logs with: docker logs -f headshot-generator-local"
    echo "Stop with: just docker-stop"

# View Docker container logs
docker-logs:
    docker logs -f headshot-generator-local

# Clean up Docker resources
docker-clean:
    echo "Cleaning up Docker resources..."
    docker stop headshot-generator-local 2>/dev/null || true
    docker rm headshot-generator-local 2>/dev/null || true
    docker rmi headshot-generator 2>/dev/null || true
    echo "✓ Docker cleanup complete"
