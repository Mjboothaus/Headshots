# ==============================================================================
# Build Stage: Install dependencies and build the application
# ==============================================================================
FROM python:3.13-slim AS builder

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install build dependencies (including build tools for compiling packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install --root-user-action=ignore uv

# Copy dependency files first (for better layer caching)
COPY pyproject.toml README.md ./

# Create a virtual environment using UV for isolation
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies in the virtual environment
RUN uv pip install --python /opt/venv/bin/python -e .

# Copy source code
COPY src/ ./src/
COPY config.toml headshot_app.py instructions.md ./

# ==============================================================================
# Runtime Stage: Create the final lightweight image
# ==============================================================================
FROM python:3.13-slim AS runtime

# Set runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=10000 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create a non-root user for the application
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code from the builder stage
COPY --from=builder /app /app

# Create logs directory for application logs
RUN mkdir -p logs

# Change ownership of the app directory to the app user
RUN chown -R appuser:appuser /app /opt/venv

# Switch to the non-root user
USER appuser

# Expose port 10000 (Render.com standard port)
EXPOSE 10000

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:10000/_stcore/health || exit 1

# Run the Streamlit application
CMD ["streamlit", "run", "headshot_app.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true"]
