"""
Main MCP server file that runs over HTTP with a specified port.
"""
import os
import json
import asyncio
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any
from aiohttp import web

from mcp import Tool
from handlers.basic_handlers import TimeToolHandler, CalcToolHandler, WeatherToolHandler
from handlers.github_handler import GitHubCloneToolHandler, GitHubListFilesToolHandler
from handlers.command_handler import CommandExecutionToolHandler
from handlers.code_analysis_handler import CodeAnalysisToolHandler
from handlers.autodeploy_handler import AutoDeployToolHandler
from handlers.ui_generator_handler import UIGeneratorToolHandler
from utils.tool_base import ToolExecution

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPServer:
    """MCP Server that can run over HTTP or stdio"""
    def __init__(self, name="mcp-server"):
        self.name = name
        self.tools = []
        self.handlers = {}
        self._setup_handlers()
        self._setup_tools()
    
    def _setup_handlers(self):
        """Initialize all handlers"""
        # Create GitHub clone handler first
        github_clone_handler = GitHubCloneToolHandler()
        
        self.handlers = {
            'time': TimeToolHandler(),
            'calc': CalcToolHandler(),
            'weather': WeatherToolHandler(),
            'github_clone': github_clone_handler,
            'github_list_files': GitHubListFilesToolHandler(github_clone_handler),
            'command': CommandExecutionToolHandler(),
            'code_analysis': CodeAnalysisToolHandler(),
            'autodeploy': AutoDeployToolHandler(),
            'ui_generator': UIGeneratorToolHandler()
        }
    
    def _setup_tools(self):
        """Initialize all tools with their handlers"""
        self.tools = [
            Tool(
                name="get_time",
                description="Get the current time",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                handler=self.handlers['time']
            ),
            Tool(
                name="calculate",
                description="Perform a simple calculation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The expression to calculate"
                        }
                    },
                    "required": ["expression"]
                },
                handler=self.handlers['calc']
            ),
            Tool(
                name="get_weather",
                description="Get weather information for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for"
                        }
                    },
                    "required": ["location"]
                },
                handler=self.handlers['weather']
            ),
            Tool(
                name="github_clone",
                description="Clone a GitHub repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "URL of the GitHub repository to clone"
                        }
                    },
                    "required": ["repo_url"]
                },
                handler=self.handlers['github_clone']
            ),
            Tool(
                name="github_list_files",
                description="List files in a cloned GitHub repository",
                inputSchema={
                    "type": "object",
                    "properties": {}
                },
                handler=self.handlers['github_list_files']
            ),
            Tool(
                name="execute_command",
                description="Execute a command in the system shell",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute"
                        }
                    },
                    "required": ["command"]
                },
                handler=self.handlers['command']
            ),
            Tool(
                name="analyze_code",
                description="Analyze code in a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the code to analyze"
                        }
                    },
                    "required": ["path"]
                },
                handler=self.handlers['code_analysis']
            ),
            Tool(
                name="autodeploy",
                description="Automatically deploy a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "URL of the repository to deploy"
                        }
                    },
                    "required": ["repo_url"]
                },
                handler=self.handlers['autodeploy']
            ),
            Tool(
                name="ui_generator",
                description="Generate UI for a repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "URL of the repository to generate UI for"
                        }
                    },
                    "required": ["repo_url"]
                },
                handler=self.handlers['ui_generator']
            )
        ]
    
    def share_repo_info(self):
        """Share repository information between handlers"""
        github_clone_handler = self.handlers['github_clone']
        
        for handler_name, handler in self.handlers.items():
            if handler_name != 'github_clone' and hasattr(handler, 'repo_path'):
                handler.repo_path = github_clone_handler.repo_path
                handler.repo_name = github_clone_handler.repo_name
                handler.repo_url = github_clone_handler.repo_url
    
    async def handle_initialize(self, request=None):
        """Handle initialize request"""
        logger.debug("Handling initialize request")
        response = {
            "type": "initialize_result",
            "supportedVersions": ["0.1.0"],
            "tools": [{
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            } for tool in self.tools]
        }
        logger.debug(f"Initialize response: {json.dumps(response, indent=2)}")
        return response
    
    async def handle_list_tools(self, request=None):
        """Handle list_tools request"""
        logger.debug("Handling list_tools request")
        response = {
            "type": "list_tools_result",
            "tools": [{
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            } for tool in self.tools]
        }
        logger.debug(f"List tools response: {json.dumps(response, indent=2)}")
        return response
    
    async def handle_execute_tool(self, tool_name, arguments):
        """Handle execute_tool request"""
        logger.debug(f"Handling execute_tool request for tool: {tool_name}")
        logger.debug(f"Tool arguments: {json.dumps(arguments, indent=2)}")
        
        # Find the tool
        tool = next((t for t in self.tools if t.name == tool_name), None)
        
        if not tool:
            error_response = {
                "type": "error",
                "message": f"Tool '{tool_name}' not found"
            }
            logger.error(f"Tool not found response: {json.dumps(error_response, indent=2)}")
            return error_response
        
        try:
            # Execute the tool
            result = await tool.handler.execute(arguments)
            
            # Update shared repository information
            if tool_name == "github_clone":
                self.share_repo_info()
            
            response = {
                "type": "execute_tool_result",
                "content": result.content
            }
            logger.debug(f"Tool execution response: {json.dumps(response, indent=2)}")
            return response
        except Exception as e:
            error_response = {
                "type": "error",
                "message": f"Error executing tool: {str(e)}"
            }
            logger.error(f"Tool execution error response: {json.dumps(error_response, indent=2)}")
            return error_response
    
    # HTTP handlers
    async def http_initialize(self, request):
        """HTTP handler for initialize request"""
        logger.debug("Handling HTTP initialize request")
        response = await self.handle_initialize()
        logger.debug(f"Sending HTTP initialize response: {json.dumps(response, indent=2)}")
        return web.json_response(response)
    
    async def http_list_tools(self, request):
        """HTTP handler for list_tools request"""
        logger.debug("Handling HTTP list_tools request")
        response = await self.handle_list_tools()
        logger.debug(f"Sending HTTP list_tools response: {json.dumps(response, indent=2)}")
        return web.json_response(response)
    
    async def http_execute_tool(self, request):
        """HTTP handler for execute_tool request"""
        try:
            logger.debug("Received execute_tool request")
            raw_body = await request.text()
            logger.debug(f"Raw request body: {raw_body}")
            
            data = await request.json()
            logger.debug(f"Parsed JSON data: {data}")
            
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            logger.debug(f"Tool name: {tool_name}")
            logger.debug(f"Arguments: {arguments}")
            
            if not tool_name:
                error_response = {
                    "type": "error",
                    "message": "Tool name not provided"
                }
                logger.error(f"Sending error response: {json.dumps(error_response, indent=2)}")
                return web.json_response(error_response, status=400)
            
            response = await self.handle_execute_tool(tool_name, arguments)
            logger.debug(f"Sending HTTP execute_tool response: {json.dumps(response, indent=2)}")
            return web.json_response(response)
        except json.JSONDecodeError:
            error_response = {
                "type": "error",
                "message": "Invalid JSON in request body"
            }
            logger.error(f"Sending error response: {json.dumps(error_response, indent=2)}")
            return web.json_response(error_response, status=400)
    
    async def start_http_server(self, host='0.0.0.0', port=8000):
        """Start the MCP server over HTTP"""
        app = web.Application()
        
        # Add routes
        app.router.add_get('/initialize', self.http_initialize)
        app.router.add_get('/list_tools', self.http_list_tools)
        app.router.add_post('/execute_tool', self.http_execute_tool)
        
        # Add CORS middleware
        app.router.add_options('/{tail:.*}', self._preflight_handler)
        app.on_response_prepare.append(self._add_cors_headers)
        
        # Start the server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        
        logger.info(f"Starting MCP HTTP server on http://{host}:{port}")
        await site.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    
    async def _preflight_handler(self, request):
        """Handle CORS preflight requests"""
        return web.Response()
    
    async def _add_cors_headers(self, request, response):
        """Add CORS headers to all responses"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    async def start_stdio_server(self):
        """Start the MCP server over stdio"""
        logger.info("Starting MCP stdio server")
        
        # Implement a direct I/O approach compatible with the MCP protocol
        reader = asyncio.StreamReader()
        read_protocol = asyncio.StreamReaderProtocol(reader)
        
        # Get the event loop
        loop = asyncio.get_event_loop()
        
        # Connect pipes
        await loop.connect_read_pipe(lambda: read_protocol, os.fdopen(0, 'rb'))
        write_transport, _ = await loop.connect_write_pipe(asyncio.Protocol, os.fdopen(1, 'wb'))
        
        while True:
            try:
                # Read a line of input (a JSON-encoded request)
                line = await reader.readline()
                if not line:
                    break
                    
                # Decode and process the request
                request = json.loads(line.decode('utf-8'))
                logger.debug(f"Received stdio request: {json.dumps(request, indent=2)}")
                
                if request.get("type") == "initialize":
                    # Handle initialize request
                    response = await self.handle_initialize()
                    
                elif request.get("type") == "list_tools":
                    # Handle list_tools request
                    response = await self.handle_list_tools()
                    
                elif request.get("type") == "execute_tool":
                    # Handle execute_tool request
                    tool_name = request.get("name")
                    tool_args = request.get("arguments", {})
                    
                    response = await self.handle_execute_tool(tool_name, tool_args)
                else:
                    # Unknown request type
                    response = {
                        "type": "error",
                        "message": f"Unknown request type: {request.get('type')}"
                    }
                
                # Send response - write directly to transport to avoid drain_helper issue
                response_json = json.dumps(response).encode('utf-8') + b'\n'
                logger.debug(f"Sending stdio response: {response_json.decode('utf-8')}")
                write_transport.write(response_json)
                    
            except asyncio.CancelledError:
                # Handle cancellation
                break
            except json.JSONDecodeError as e:
                # Handle JSON decode error
                error_msg = json.dumps({
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}"
                }).encode('utf-8') + b'\n'
                logger.error(f"Sending error response: {error_msg.decode('utf-8')}")
                write_transport.write(error_msg)
            except Exception as e:
                # Handle other errors
                error_msg = json.dumps({
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                }).encode('utf-8') + b'\n'
                logger.error(f"Sending error response: {error_msg.decode('utf-8')}")
                write_transport.write(error_msg)
        
        # Clean up
        if write_transport:
            write_transport.close()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MCP Server')
    parser.add_argument('--http', action='store_true', help='Run as HTTP server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    args = parser.parse_args()
    
    # Create the MCP server
    server = MCPServer()
    
    if args.http:
        # Run as HTTP server
        await server.start_http_server(host=args.host, port=args.port)
    else:
        # Run as stdio server
        await server.start_stdio_server()

if __name__ == "__main__":
    asyncio.run(main()) 