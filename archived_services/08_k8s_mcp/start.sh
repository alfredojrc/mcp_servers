#!/bin/bash

# Create necessary directories
mkdir -p logs static/docs static/api static/templates

# Fetch initial K8s documentation
echo "Fetching Kubernetes documentation..."
python -c "from main import fetch_k8s_docs; fetch_k8s_docs()"

# Generate templates
echo "Generating Kubernetes templates..."
# python templates.py # Commented out as templates seem handled in main.py

# Start the server
echo "Starting Kubernetes MCP server..."
# if [ "$FLASK_ENV" = "production" ]; then # Force gunicorn for testing
echo "Running with Gunicorn (gevent workers)"
# gunicorn --bind 0.0.0.0:${WEBCONTROL_PORT:-5001} --workers 4 main:app # Original gunicorn command
gunicorn --bind 0.0.0.0:${WEBCONTROL_PORT:-5001} --worker-class gevent --workers 4 main:app # Use gevent worker class
# else
#     echo "Running in development mode with Flask"
#     # python main.py # Original command
# fi 