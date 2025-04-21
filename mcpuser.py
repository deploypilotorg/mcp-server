import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from mcp_use import MCPAgent, MCPClient
import mcp_use

mcp_use.set_debug(2)


async def main():
    # Load environment variables
    load_dotenv()

    # Create configuration dictionary
    config = {
        "mcpServers": {

                    "cli-mcp-server": {
                        "command": "uvx",
                        "args": ["cli-mcp-server"],
                        "env": {
                            "ALLOWED_DIR": "/Users/zaidalsaheb/projects/example-repo",
                            "ALLOWED_COMMANDS": "all",
                            "ALLOWED_FLAGS": "all",
                            "MAX_COMMAND_LENGTH": "1024",
                            "COMMAND_TIMEOUT": "30",
                        },
                    }
                }
            }


    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)

    llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", max_tokens=64000)

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, verbose=True, max_steps=100)

    # Run the query with more specific instructions
    result = await agent.run(
        """
        Can you go to the example-repo and run streamlit app.py, and tell me if it runs successfully?
        """
    )
    print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
