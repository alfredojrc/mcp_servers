FROM python:3.12-slim

WORKDIR /workspace

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x /workspace/entrypoint.sh

# Expose the MCP host port
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/workspace/entrypoint.sh"] 