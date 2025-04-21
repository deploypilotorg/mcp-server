"""
Test script for MCP client integration with LLM and tools.
"""

import asyncio

from mcp_client import MCPBackendClient


async def test_mcp_client():
    # Initialize the client
    client = MCPBackendClient(server_url="http://localhost:8000")

    try:
        # Connect to the server and get available tools
        print("Connecting to MCP server...")
        tools = await client.connect()
        print(
            f"Connected successfully! Available tools: {[tool['name'] for tool in tools]}"
        )

        # Test queries that should use different tools
        test_queries = [
            "Clone the repo at https://github.com/deploypilotorg/example-repo.git, create a venv, install the requirements and run 'streamlit run streamlit_app.py' and tell me if it runs successfully",
        ]

        for query in test_queries:
            print(f"\nTesting query: {query}")
            try:
                response = await client.process_query(query)
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error processing query: {str(e)}")

            # Add a small delay between queries
            await asyncio.sleep(1)

    except Exception as e:
        print(f"Error during testing: {str(e)}")
    finally:
        # Clean up
        await client.close()
        print("\nTest completed. Connection closed.")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_mcp_client())
