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
            "github": {
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    "-e",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server",
                ],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")},
            }
        }
    }

    # Create MCPClient from configuration dictionary
    client = MCPClient.from_dict(config)

    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        max_tokens=64000
    )

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, verbose=True, max_steps=100)

    # Run the query with more specific instructions
    result = await agent.run(
        """Please open a pull request from the 'test-branch' branch to the 'main' branch in the repository https://github.com/deploypilotorg/example-repo.git. Make sure you are calling the appropriate tools at every single step, use the minimum number of tools possible"""
    )
    print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
