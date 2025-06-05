#!/usr/bin/env node
/**
 * Simple STDIO to SSE bridge for MCP
 * This replaces the non-existent @modelcontextprotocol/proxy
 */

const EventSource = require('eventsource');
const readline = require('readline');
const http = require('http');

const SSE_URL = process.argv[2] || 'http://localhost:8000/sse';

// Setup readline for STDIO
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

// Connect to SSE endpoint
const eventSource = new EventSource(SSE_URL);

let sessionId = null;
let pendingRequests = new Map();

eventSource.onopen = () => {
  console.error(`Connected to ${SSE_URL}`);
};

eventSource.onmessage = (event) => {
  const data = event.data.trim();
  
  // Handle session ID
  if (data.startsWith('/messages/?session_id=')) {
    sessionId = data.split('=')[1];
    console.error(`Session ID: ${sessionId}`);
    return;
  }
  
  // Handle JSON responses
  try {
    const message = JSON.parse(data);
    
    // Forward the message to stdout
    console.log(JSON.stringify(message));
    
    // Handle pending requests
    if (message.id && pendingRequests.has(message.id)) {
      pendingRequests.delete(message.id);
    }
  } catch (e) {
    // Not JSON, ignore
  }
};

eventSource.onerror = (error) => {
  console.error('SSE Error:', error);
  process.exit(1);
};

// Handle input from stdin
rl.on('line', async (line) => {
  try {
    const request = JSON.parse(line);
    
    // If we have a session ID, send via POST to /messages endpoint
    if (sessionId) {
      const postData = JSON.stringify(request);
      
      const options = {
        hostname: new URL(SSE_URL).hostname,
        port: new URL(SSE_URL).port || 80,
        path: `/messages/?session_id=${sessionId}`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(postData)
        }
      };
      
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          if (res.statusCode !== 200) {
            console.error(`POST failed: ${res.statusCode} ${data}`);
          }
        });
      });
      
      req.on('error', (e) => {
        console.error(`POST error: ${e.message}`);
      });
      
      req.write(postData);
      req.end();
      
      // Track pending request
      if (request.id) {
        pendingRequests.set(request.id, request);
      }
    } else {
      console.error('No session ID yet, waiting for connection...');
    }
  } catch (e) {
    console.error('Invalid JSON input:', e.message);
  }
});

// Handle shutdown
process.on('SIGINT', () => {
  eventSource.close();
  process.exit(0);
});