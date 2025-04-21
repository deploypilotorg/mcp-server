import os
import json
import asyncio
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from mcp_client import MCPBackendClient

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
client = None

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a query through the MCP client"""
    global client
    
    # Get the query from the request
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Ensure the client is connected
        if client is None:
            client = run_async(connect_client())
            
        # Process the query
        response = run_async(client.process_query(query))
        
        return jsonify({'response': response})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error processing query: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e), 'traceback': error_details}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get available tools from the MCP server"""
    global client
    
    try:
        print("Fetching tools - starting")
        # Ensure the client is connected
        if client is None:
            print("Client not initialized, attempting to connect...")
            client = run_async(connect_client())
            if client is None:
                return jsonify({'error': 'Failed to connect to MCP server'}), 500
            print(f"Client connected successfully, tools: {len(client.tools)}")
            
        # Debug info
        print(f"Returning tools: {len(client.tools) if client.tools else 0}")
        if not client.tools:
            return jsonify({'error': 'No tools available from MCP server'}), 404
            
        return jsonify({'tools': client.tools})
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error fetching tools: {str(e)}")
        print(f"Traceback: {error_details}")
        return jsonify({'error': str(e), 'traceback': error_details}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server status"""
    global client
    
    try:
        # Check MCP server status
        mcp_status = "disconnected"
        if client is not None and hasattr(client, 'tools'):
            mcp_status = "connected" if client.tools else "connected_no_tools"
        
        return jsonify({
            'status': 'ok',
            'mcp_server': mcp_status
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

async def connect_client():
    """Connect to the MCP server"""
    try:
        print("Connecting to MCP server...")
        client = MCPBackendClient(server_url="http://localhost:8000")
        await client.connect()
        print(f"Connected to MCP server, tools: {len(client.tools) if client.tools else 0}")
        return client
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error connecting to MCP server: {str(e)}")
        print(f"Traceback: {error_details}")
        return None

async def init_client():
    """Initialize the MCP client"""
    global client
    
    try:
        client = MCPBackendClient(server_url="http://localhost:8000")
        await client.connect()
        print("Successfully connected to MCP server")
        print(f"Available tools: {len(client.tools)}")
        if client.tools:
            for tool in client.tools:
                print(f"- {tool.get('name', 'unnamed')}")
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error connecting to MCP server: {str(e)}")
        print(f"Traceback: {error_details}")
        client = None

# Flask doesn't natively support async, so we need to run the event loop manually
def run_async(coro):
    """Run an asynchronous coroutine in the current thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    # Initialize the client before starting the server
    run_async(init_client())
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Start the Flask app
    app.run(debug=True, port=5000) 