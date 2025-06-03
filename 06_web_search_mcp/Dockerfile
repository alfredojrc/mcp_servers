FROM python:3.12-slim

WORKDIR /workspace

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mcp_server.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8006

# Run the server
ENTRYPOINT ["/workspace/entrypoint.sh"]