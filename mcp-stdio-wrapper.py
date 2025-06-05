#!/usr/bin/env python3
"""
Simple STDIO wrapper for MCP SSE endpoint
Connects to the SSE endpoint and translates to STDIO for Claude Code
"""

import sys
import json
import asyncio
import httpx
from typing import AsyncIterator, Optional
import logging

# Configure logging to stderr only
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)

SSE_URL = "http://localhost:8000/sse"

async def read_stdin() -> AsyncIterator[str]:
    """Read lines from stdin asynchronously"""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        line = await reader.readline()
        if not line:
            break
        yield line.decode().strip()

async def write_stdout(data: str):
    """Write data to stdout with flush"""
    sys.stdout.write(data + "\n")
    sys.stdout.flush()

async def handle_sse_message(message: str) -> Optional[dict]:
    """Parse SSE message and return JSON data if valid"""
    if message.startswith("data: "):
        data = message[6:].strip()
        if data and data != "[DONE]":
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                pass
    return None

async def main():
    """Main STDIO <-> SSE bridge"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Establish SSE connection
        async with client.stream("GET", SSE_URL) as response:
            if response.status_code != 200:
                sys.stderr.write(f"Failed to connect to SSE endpoint: {response.status_code}\n")
                sys.exit(1)
            
            # Create tasks for reading stdin and SSE
            stdin_task = asyncio.create_task(read_stdin().__anext__())
            sse_buffer = ""
            
            while True:
                # Check for stdin input
                if stdin_task.done():
                    try:
                        line = stdin_task.result()
                        if line:
                            # Parse and forward request to SSE endpoint
                            request = json.loads(line)
                            
                            # For now, we'll need to implement proper SSE -> STDIO protocol translation
                            # This is a simplified version that shows the concept
                            await write_stdout(json.dumps({
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "result": {"status": "not_implemented"}
                            }))
                        
                        # Start reading next line
                        stdin_task = asyncio.create_task(read_stdin().__anext__())
                    except StopAsyncIteration:
                        break
                    except Exception as e:
                        sys.stderr.write(f"Error processing stdin: {e}\n")
                
                # Check for SSE data
                try:
                    chunk = await asyncio.wait_for(response.aiter_bytes().__anext__(), timeout=0.1)
                    sse_buffer += chunk.decode('utf-8')
                    
                    # Process complete SSE messages
                    while '\n\n' in sse_buffer:
                        message, sse_buffer = sse_buffer.split('\n\n', 1)
                        for line in message.split('\n'):
                            data = await handle_sse_message(line)
                            if data:
                                # Forward SSE data to stdout if relevant
                                pass
                except asyncio.TimeoutError:
                    continue
                except StopAsyncIteration:
                    break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"Fatal error: {e}\n")
        sys.exit(1)