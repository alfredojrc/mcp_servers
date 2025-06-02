# Use an official Freqtrade image as the base
# This image already has Python, Freqtrade, and TA-Lib installed.
FROM freqtradeorg/freqtrade:stable

# Set working directory for our MCP server
WORKDIR /mcp_server

# Install our MCP server dependencies (FastMCP, etc.)
# The base image has pip.
# requirements.txt for the MCP server should contain fastmcp, uvicorn, python-json-logger etc.
# It should NOT contain freqtrade or TA-Lib as they are in the base.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy our MCP server code
COPY mcp_server.py .

# The Freqtrade source code is in /freqtrade in the base image.
# Our mcp_server.py tools that browse source will need to use this path.

# Expose the port the MCP server will run on
EXPOSE 8015

# CMD for our MCP server
# We override the base image's CMD.
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8015"] 