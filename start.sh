#!/bin/bash
set -euo pipefail

# Startup script for Render.com deployment
echo "Starting Headshot Generator on Render.com..."

# Set default port if not provided
PORT=${PORT:-10000}
echo "Using port: $PORT"

# Ensure logs directory exists
mkdir -p logs
echo "Logs directory created"

# Set Streamlit configuration for production
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_PORT=$PORT
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10
export STREAMLIT_SERVER_MAX_MESSAGE_SIZE=10

echo "Environment variables set"
echo "STREAMLIT_SERVER_PORT: $STREAMLIT_SERVER_PORT"
echo "STREAMLIT_SERVER_ADDRESS: $STREAMLIT_SERVER_ADDRESS"

# Health check function
health_check() {
    echo "Performing health check..."
    sleep 5  # Give the server time to start
    
    # Simple health check by attempting to connect to the server
    if curl -f "http://localhost:$PORT/_stcore/health" > /dev/null 2>&1; then
        echo "Health check passed"
        return 0
    else
        echo "Health check failed"
        return 1
    fi
}

# Start Streamlit in the background for health check
echo "Starting Streamlit application..."
streamlit run headshot_app.py \
    --server.port="$PORT" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.maxUploadSize=10 \
    --server.maxMessageSize=10 &

# Get the process ID
STREAMLIT_PID=$!
echo "Streamlit started with PID: $STREAMLIT_PID"

# Wait for the application to be ready
sleep 10

# Perform health check
if health_check; then
    echo "Application is ready and healthy"
    # Wait for the Streamlit process to complete
    wait $STREAMLIT_PID
else
    echo "Application health check failed, terminating..."
    kill $STREAMLIT_PID 2>/dev/null || true
    exit 1
fi