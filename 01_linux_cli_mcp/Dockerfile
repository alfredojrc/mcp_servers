FROM python:3.11-slim

# Install openssh-client
RUN apt-get update && apt-get install -y openssh-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Expose the MCP server port
EXPOSE 8001
# Expose the Prometheus metrics port
EXPOSE 9091

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 