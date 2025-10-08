# Use Python 3.13 slim image for smaller size and faster builds
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=10000 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV and image processing
RUN apt-get update && apt-get install -y \
    curl \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/
COPY config.toml ./
COPY headshot_app.py ./
COPY instructions.md ./

# Install Python dependencies using UV
RUN uv pip install --system -e .

# Create logs directory for application logs
RUN mkdir -p logs

# Expose port 10000 (Render.com standard port)
EXPOSE 10000

# Health check to ensure the service is running
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:10000/_stcore/health || exit 1

# Run the Streamlit application
CMD ["streamlit", "run", "headshot_app.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true"]