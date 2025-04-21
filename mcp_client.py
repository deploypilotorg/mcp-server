"""
MCP client that integrates with the MCP server backend.
"""
import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, List, Any

from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class MCPBackendClient:
    """Backend MCP client that integrates with the MCP server"""
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.anthropic = Anthropic()
        self.session = None
        self.tools = []
        self.conversation_history = []
    
    async def connect(self):
        """Connect to the MCP server"""
        self.session = aiohttp.ClientSession()
        
        try:
            # Initialize connection
            async with self.session.get(f"{self.server_url}/initialize") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to initialize connection: {error_text}")
                
                data = await response.json()
                if data.get('type') != 'initialize_result':
                    raise Exception(f"Unexpected response type: {data.get('type')}")
            
            # List available tools
            async with self.session.get(f"{self.server_url}/list_tools") as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to list tools: {error_text}")
                
                data = await response.json()
                if data.get('type') != 'list_tools_result':
                    raise Exception(f"Unexpected response type: {data.get('type')}")
                
                self.tools = data.get('tools', [])
                return self.tools
                
        except Exception as e:
            if self.session:
                await self.session.close()
                self.session = None
            raise e
    
    async def close(self):
        """Close the connection to the MCP server"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        try:
            # Prepare the request
            request_data = {
                "name": tool_name,
                "arguments": arguments
            }
            
            # Execute the tool
            async with self.session.post(
                f"{self.server_url}/execute_tool", 
                json=request_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Failed to execute tool: {error_text}")
                
                data = await response.json()
                if data.get('type') == 'error':
                    raise Exception(data.get('message', 'Unknown error'))
                
                return data
                
        except Exception as e:
            raise e
    
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        if not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")
        
        # Add the new query to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": query
        })

        available_tools = [
            {
                "name": tool.get("name"),
                "description": tool.get("description"),
                "input_schema": tool.get("inputSchema")
            } for tool in self.tools
        ]

        # Initial Claude API call with full conversation history
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=self.conversation_history,
            tools=available_tools
        )

        tool_results = []
        final_text = []
        max_iterations = 5  # Limit the number of iterations to prevent infinite loops
        current_iteration = 0

        while current_iteration < max_iterations:
            current_iteration += 1
            has_tool_use = False

            for content in response.content:
                if content.type == 'text':
                    final_text.append(content.text)
                    # Add the response to conversation history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": content.text
                    })
                elif content.type == 'tool_use':
                    has_tool_use = True
                    tool_name = content.name
                    tool_args = content.input

                    # Execute tool call
                    result = await self.call_tool(tool_name, tool_args)
                    tool_result = result.get('content', 'No content in response')
                    tool_results.append({"call": tool_name, "result": tool_result})
                    
                    final_text.append(f"[Called tool {tool_name}]")

                    # Add tool use and result to conversation history
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": content.id,
                                "name": tool_name,
                                "input": tool_args
                            }
                        ]
                    })
                    
                    self.conversation_history.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": content.id,
                                "content": tool_result
                            }
                        ]
                    })

            # If no tool was used in this iteration, we're done
            if not has_tool_use:
                break

            # Get next response from Claude with updated conversation history
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                messages=self.conversation_history,
                tools=available_tools
            )

        return "\n\n".join(final_text)

# Example usage in a FastAPI route
"""
from fastapi import FastAPI, HTTPException
from mcp_client import MCPBackendClient

app = FastAPI()
client = MCPBackendClient()

@app.on_event("startup")
async def startup_event():
    await client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await client.close()

@app.post("/query")
async def process_query(query: str):
    try:
        response = await client.process_query(query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
""" 