FROM python:3.10-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mcp_server.py .
COPY entrypoint.sh .

# Copy static files if they exist
COPY static/ ./static/ 

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create directories for documentation and search index
RUN mkdir -p /workspace/docs /workspace/search_index

# Expose port
EXPOSE 8011

# Set entrypoint
ENTRYPOINT ["/workspace/entrypoint.sh"]