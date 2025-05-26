FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install aider-mcp-server
RUN pip install --no-cache-dir mseep-aider-mcp-server

# Expose the default MCP port for this service (can be overridden)
EXPOSE 8014

# Environment variable for the repository Aider will work on
ENV REPO_PATH=/workspace
ENV MCP_PORT=8014
# ENV OPENAI_API_KEY="" # Optional: Set via docker-compose
# ENV ANTHROPIC_API_KEY="" # Optional: Set via docker-compose

# Command to run the Aider MCP server
# It will listen on 0.0.0.0 inside the container on MCP_PORT
# The --repo-path will use the REPO_PATH environment variable
CMD ["aider-mcp", "--repo-path", "$REPO_PATH"] 