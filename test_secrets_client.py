import httpx
import json
import asyncio

MCP_SERVER_URL = "http://localhost:8013/mcp"

async def call_mcp_tool(tool_name: str, params: dict):
    payload = {
        "version": "2024-11-05", # Or your MCP spec version
        "tool_name": tool_name,
        "parameters": params
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"Calling tool: {tool_name} with params: {params}")
            response = await client.post(MCP_SERVER_URL, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            # MCP over HTTP typically uses Server-Sent Events (SSE)
            # For a simple tool call that returns a single JSON response, 
            # it might also just return JSON directly or the first event is the result.
            # This client is simplified and assumes a direct JSON response or parsable SSE.
            
            print(f"Response status: {response.status_code}")
            print("Raw response text:")
            print(response.text)

            # Attempt to parse as JSON if possible, otherwise show as text
            try:
                # For SSE, we might get multiple events. Here we try to parse the whole thing
                # or look for a specific event structure.
                # A more robust SSE client would handle the event stream properly.
                
                # Simplistic SSE parsing: try to find a JSON object within the stream
                # This is NOT a proper SSE parser.
                data_lines = [line for line in response.text.split('\n') if line.startswith('data: ')]
                if data_lines:
                    full_data_str = "".join([line.split('data: ', 1)[1] for line in data_lines])
                    mcp_response = json.loads(full_data_str)
                else: # Try parsing as direct JSON
                    mcp_response = response.json()

                print("\nParsed MCP Response:")
                print(json.dumps(mcp_response, indent=2))
                
                if mcp_response.get("type") == "tool_result":
                    print(f"\nTool Result for {tool_name}:")
                    print(json.dumps(mcp_response.get("result"), indent=2))
                elif mcp_response.get("type") == "error":
                    print(f"\nTool Error for {tool_name}:")
                    print(json.dumps(mcp_response.get("error"), indent=2))
                else:
                    print("\nUnknown MCP response structure.")

            except json.JSONDecodeError:
                print("\nResponse was not valid JSON. This might be an SSE stream that needs full parsing or an error page.")
            except Exception as e:
                print(f"\nError processing response: {e}")

    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

async def main():
    # --- Test KeePass Entry Retrieval ---
    # IMPORTANT: Adjust 'entryPath' if "DB test user1" is inside a group.
    # For example, if it's in Root/MyGroup/DB test user1, path is "MyGroup/DB test user1"
    # If it's directly in Root, path is "DB test user1"
    entry_path_to_test = "DB test user1" 
    field_to_retrieve = "password" # or "username", "notes", or a custom property name

    print(f"--- Attempting to retrieve field '{field_to_retrieve}' from KeePass entry '{entry_path_to_test}' ---")
    await call_mcp_tool(
        tool_name="secrets.keepass.getEntry",
        params={"entryPath": entry_path_to_test, "field": field_to_retrieve}
    )

if __name__ == "__main__":
    asyncio.run(main()) 