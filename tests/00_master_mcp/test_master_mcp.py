#!/usr/bin/env python3
import unittest
import asyncio
import os
from fastmcp.client import Client # Only import Client
# from mcp.errors import MCPError # Removed for now
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get server details from environment or use defaults
MCP_HOST_URL = os.getenv("MCP_MASTER_HOST_URL", "http://localhost:8000")

# Construct full URL (now root)
BASE_URL = f"{MCP_HOST_URL.rstrip('/')}/"

class TestMasterMcp(unittest.TestCase):

    client: Client = None
    loop: asyncio.AbstractEventLoop = None

    @classmethod
    def setUpClass(cls):
        """Set up the event loop and connect the client once for all tests in this class."""
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        cls.client = cls.loop.run_until_complete(cls.connect_client())

        if not cls.client:
            raise unittest.SkipTest("Could not connect to MCP server, skipping tests.")

    @classmethod
    def tearDownClass(cls):
        """Disconnect the client and close the event loop after all tests."""
        if cls.client:
            cls.loop.run_until_complete(cls.disconnect_client())
        cls.loop.close()

    @classmethod
    async def connect_client(cls) -> Client | None:
        """Attempt to connect to the MCP server using default client behavior."""
        logger.info(f"Attempting to connect client using base URL: {BASE_URL}")
        try:
            # Provide the root URL to the client constructor
            client = Client(BASE_URL)
            await client.__aenter__() # Manually enter context to establish connection
            logger.info(f"Client connected successfully. Session ID: {client.session_id}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect MCP client: {e}", exc_info=True)
            return None

    @classmethod
    async def disconnect_client(cls):
        """Disconnect the client."""
        if cls.client:
            logger.info("Disconnecting client...")
            try:
                await cls.client.__aexit__(None, None, None)
                logger.info("Client disconnected.")
            except Exception as e:
                 logger.error(f"Error disconnecting client: {e}", exc_info=True)

    # Test methods
    def test_tool_hello_world(self):
        """Test the hello_world tool."""
        logger.info("Testing tool: hello_world")
        async def run_test():
            result = await self.client.call_tool("hello_world", {"name": "Unit Test"})
            self.assertEqual(result, "Hello, Unit Test!")
        self.loop.run_until_complete(run_test())

    def test_tool_add_numbers(self):
        """Test the add_numbers tool."""
        logger.info("Testing tool: add_numbers")
        async def run_test():
            result = await self.client.call_tool("add_numbers", {"a": 15, "b": 7})
            self.assertEqual(result, 22)
        self.loop.run_until_complete(run_test())

    def test_tool_get_server_info(self):
        """Test the get_server_info tool."""
        logger.info("Testing tool: get_server_info")
        async def run_test():
            result = await self.client.call_tool("get_server_info")
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("name"), "Master Orchestrator")
            self.assertEqual(result.get("port"), int(os.getenv("MCP_PORT", 8000)))
        self.loop.run_until_complete(run_test())

    def test_resource_status(self):
        """Test reading the orchestrator://status resource."""
        logger.info("Testing resource: orchestrator://status")
        async def run_test():
            result = await self.client.read_resource("orchestrator://status")
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "online")
            self.assertEqual(result.get("service"), "MCP Host")
        self.loop.run_until_complete(run_test())

    def test_prompt_greeting(self):
        """Test getting the greeting prompt template."""
        logger.info("Testing prompt: greeting_prompt")
        async def run_test():
            prompt_details = await self.client.get_prompt("greeting_prompt", {"user_name": "Tester"})
            self.assertEqual(prompt_details, "Hello Tester, I'm the MCP Host server. How can I help you today?")
        self.loop.run_until_complete(run_test())

if __name__ == '__main__':
    unittest.main() 