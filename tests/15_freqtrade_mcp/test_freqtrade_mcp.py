import unittest
import httpx
import os

# Assuming the Freqtrade MCP will run on port 8015 as configured in docker-compose
FREQTRADE_MCP_URL = os.getenv("FREQTRADE_MCP_BASE_URL", "http://localhost:8015")

class TestFreqtradeMCPService(unittest.TestCase):

    def test_health_check(self):
        """Test the /health endpoint of the 15_freqtrade_mcp service."""
        try:
            response = httpx.get(f"{FREQTRADE_MCP_URL}/health")
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data.get("status") in ["healthy", "degraded"]) # Freqtrade health check can be degraded if API not reachable
            self.assertEqual(data.get("service"), "freqtrade-mcp") # Check service name
        except httpx.RequestError as e:
            self.fail(f"Request to /health failed: {e}")

    # Add more tests here for other tools, e.g.:
    # - test_get_bot_status (calls freqtrade.api.getStatus)
    # - test_get_balance (calls freqtrade.api.getBalance)
    # - test_hyperopt_knowledge_tool (calls freqtrade.knowledge.hyperoptBestPractices)
    # These would require the MCP server to be running and connected to a (mocked or real) Freqtrade instance.
    # For now, focusing on the health check which is self-contained to the MCP server.

if __name__ == '__main__':
    unittest.main() 