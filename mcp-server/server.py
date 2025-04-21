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
from handlers.github_handler import GitHubRepoToolHandler
from handlers.command_handler import CommandExecutionToolHandler
from handlers.code_analysis_handler import CodeAnalysisToolHandler
from handlers.autodeploy_handler import AutoDeployToolHandler
from handlers.ui_generator_handler import UIGeneratorToolHandler
from utils.tool_base import ToolExecution

# Setup logging
logging.basicConfig(
    level=logging.INFO,
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
        self.handlers = {
            'time': TimeToolHandler(),
            'calc': CalcToolHandler(),
            'weather': WeatherToolHandler(),
            'github': GitHubRepoToolHandler(),
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
                            "description": "The expression to calculate (e.g., 'add(3, 4)', 'subtract(5, 2)', 'multiply(3, 3)', 'divide(10, 2)')"
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
                            "description": "The location to get weather for (e.g., 'New York', 'London', 'Tokyo', 'Sydney', 'Paris')"
                        }
                    },
                    "required": ["location"]
                },
                handler=self.handlers['weather']
            ),
            Tool(
                name="github_repo",
                description="Clone and analyze GitHub repositories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The action to perform",
                            "enum": ["clone", "list_files", "read_file", "get_repo_info"]
                        },
                        "repo_url": {
                            "type": "string",
                            "description": "The URL of the GitHub repository"
                        },
                        "path": {
                            "type": "string",
                            "description": "The path to list files from (for list_files action)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "The path of the file to read (for read_file action)"
                        }
                    },
                    "required": ["action"]
                },
                handler=self.handlers['github']
            ),
            Tool(
                name="execute_command",
                description="Execute a command in the system shell and return the result",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute"
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "The working directory to execute the command in (optional)"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 30)"
                        }
                    },
                    "required": ["command"]
                },
                handler=self.handlers['command']
            ),
            Tool(
                name="analyze_code",
                description="Analyze code in the repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The analysis action to perform",
                            "enum": ["analyze_languages", "find_todos", "analyze_complexity", "search_code", "get_dependencies"]
                        },
                        "repo_path": {
                            "type": "string",
                            "description": "The path to the repository"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "The path of the file to analyze (for analyze_complexity action)"
                        },
                        "query": {
                            "type": "string",
                            "description": "The search query (for search_code action)"
                        }
                    },
                    "required": ["action", "repo_path"]
                },
                handler=self.handlers['code_analysis']
            ),
            Tool(
                name="autodeploy",
                description="Automate deployment of code repositories",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The deployment action to perform",
                            "enum": ["prepare_deployment", "start_deployment", "get_status", "abort_deployment", "detect_deployment_type"]
                        },
                        "repo_path": {
                            "type": "string",
                            "description": "The path to the repository"
                        },
                        "deploy_config": {
                            "type": "object",
                            "description": "Deployment configuration (for prepare_deployment action)"
                        }
                    },
                    "required": ["action"]
                },
                handler=self.handlers['autodeploy']
            ),
            Tool(
                name="ui_generator",
                description="Generate and run UI for applications in the repository",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "The action to perform",
                            "enum": ["scan_apps", "generate_ui", "stop_ui"]
                        },
                        "app_path": {
                            "type": "string",
                            "description": "The path to the application entry point (for generate_ui action)"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "The session ID of a running UI (for stop_ui action)"
                        }
                    },
                    "required": ["action"]
                },
                handler=self.handlers['ui_generator']
            )
        ]
    
    def share_repo_info(self):
        """Share repository information between handlers"""
        github_handler = self.handlers['github']
        
        for handler_name, handler in self.handlers.items():
            if handler_name != 'github' and hasattr(handler, 'repo_path'):
                handler.repo_path = github_handler.repo_path
                handler.repo_name = github_handler.repo_name
                handler.repo_url = github_handler.repo_url
    
    async def handle_initialize(self, request=None):
        """Handle initialize request"""
        response = {
            "type": "initialize_result",
            "supportedVersions": ["0.1.0"],
            "tools": [{
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            } for tool in self.tools]
        }
        return response
    
    async def handle_list_tools(self, request=None):
        """Handle list_tools request"""
        response = {
            "type": "list_tools_result",
            "tools": [{
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema
            } for tool in self.tools]
        }
        return response
    
    async def handle_execute_tool(self, tool_name, arguments):
        """Handle execute_tool request"""
        # Find the tool
        tool = next((t for t in self.tools if t.name == tool_name), None)
        
        if not tool:
            return {
                "type": "error",
                "message": f"Tool '{tool_name}' not found"
            }
        
        try:
            # Execute the tool
            result = await tool.handler.execute(arguments)
            
            # Update shared repository information
            if tool_name == "github_repo" and arguments.get("action") == "clone":
                self.share_repo_info()
            
            return {
                "type": "execute_tool_result",
                "content": result.content
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error executing tool: {str(e)}"
            }
    
    # HTTP handlers
    async def http_initialize(self, request):
        """HTTP handler for initialize request"""
        response = await self.handle_initialize()
        return web.json_response(response)
    
    async def http_list_tools(self, request):
        """HTTP handler for list_tools request"""
        response = await self.handle_list_tools()
        return web.json_response(response)
    
    async def http_execute_tool(self, request):
        """HTTP handler for execute_tool request"""
        try:
            data = await request.json()
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            if not tool_name:
                return web.json_response({
                    "type": "error",
                    "message": "Tool name not provided"
                }, status=400)
            
            response = await self.handle_execute_tool(tool_name, arguments)
            return web.json_response(response)
        except json.JSONDecodeError:
            return web.json_response({
                "type": "error",
                "message": "Invalid JSON in request body"
            }, status=400)
    
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
                write_transport.write(error_msg)
            except Exception as e:
                # Handle other errors
                error_msg = json.dumps({
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                }).encode('utf-8') + b'\n'
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