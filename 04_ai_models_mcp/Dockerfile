FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Environment variables for non-interactive setup
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install system dependencies (if any are needed for the SDKs - usually not for these Python ones)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     some-dependency \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY mcp_server.py .
# Add other necessary files if your MCP server uses multiple Python modules

# Expose the port the MCP server will run on (e.g., 8016)
EXPOSE 8016

# CMD for the AI Models MCP server - run as Python script
CMD ["python", "mcp_server.py"] 