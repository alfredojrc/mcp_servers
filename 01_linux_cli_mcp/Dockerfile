FROM python:3.12-slim

WORKDIR /workspace

# Install potentially needed OS packages (e.g., for SSH or specific commands)
# RUN apt-get update && apt-get install -y --no-install-recommends openssh-client && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x /workspace/entrypoint.sh

# Expose the MCP server port
EXPOSE 5001
# Expose the Prometheus metrics port
EXPOSE 9091

# Set the entrypoint script
ENTRYPOINT ["/workspace/entrypoint.sh"] 