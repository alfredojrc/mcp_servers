FROM python:3.12-slim

WORKDIR /workspace

# Assuming the build context is the '00_master_mcp' directory itself,
# and requirements.txt, mcp_host.py, entrypoint.sh are directly in it.

COPY requirements.txt /workspace/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /workspace/requirements.txt

# Copy the ultra-minimal mcp_host.py
COPY mcp_host.py /workspace/mcp_host.py

# Copy the entrypoint.sh
COPY entrypoint.sh /workspace/entrypoint.sh

# Ensure entrypoint script is executable
RUN chmod +x /workspace/entrypoint.sh

# Expose the MCP host port
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/workspace/entrypoint.sh"] 