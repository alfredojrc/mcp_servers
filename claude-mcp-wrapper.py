#!/usr/bin/env python3
"""
MCP wrapper that connects to the Docker container running the orchestrator
"""

import sys
import subprocess
import os

# The actual command to run inside the container
DOCKER_EXEC_CMD = [
    'docker', 'exec', '-i', 'mcp_servers_00_master_mcp_1',
    'python3', '/workspace/mcp_host_stdio_claude.py'
]

def main():
    """Simple passthrough to Docker container"""
    try:
        # Start the process
        process = subprocess.Popen(
            DOCKER_EXEC_CMD,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            bufsize=0  # Unbuffered
        )
        
        # Wait for process to complete
        return_code = process.wait()
        sys.exit(return_code)
        
    except KeyboardInterrupt:
        if process:
            process.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()