FROM python:3.11-slim

# Install git (required by aider)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server implementation
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose the default MCP port for this service
EXPOSE 8014

# Environment variables
ENV REPO_PATH=/workspace
ENV MCP_PORT=8014

# Create workspace directory
RUN mkdir -p /workspace

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 