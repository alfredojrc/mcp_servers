#!/bin/bash

# Create necessary directories
mkdir -p logs static/docs static/api static/templates

# Fetch initial K8s documentation
echo "Fetching Kubernetes documentation..."
python -c "from main import fetch_k8s_docs; fetch_k8s_docs()"

# Generate templates
echo "Generating Kubernetes templates..."
python templates.py

# Start the server
echo "Starting Kubernetes MCP server..."
if [ "$FLASK_ENV" = "production" ]; then
    echo "Running in production mode with Gunicorn"
    gunicorn --bind 0.0.0.0:${WEBCONTROL_PORT:-5001} --workers 4 main:app
else
    echo "Running in development mode with Flask"
    python main.py
fi 