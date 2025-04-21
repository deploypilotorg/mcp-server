# MCP Client Interface

A web-based interface for interacting with the MCP server and LLM.

## Overview

This client interface provides a user-friendly way to interact with your MCP server and the underlying LLM. It features:

- A chat-like interface for natural conversation
- Display of available tools
- Visual indication of tool calls
- Real-time connection status

## Prerequisites

- Python 3.8 or higher
- MCP server running on localhost:8000
- Required Python packages (see requirements.txt)

## Installation

1. Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

2. Make sure your MCP server is running:

```bash
python server.py --http
```

3. Start the client interface:

```bash
python client_interface.py
```

4. Open your web browser and navigate to:

```
http://localhost:5000
```

## Usage

### Connecting to the Server

The interface automatically attempts to connect to your MCP server when it loads. You can see the connection status in the top right corner:

- 🟢 Green: Connected
- 🔴 Red: Disconnected

### Asking Questions

1. Type your question or command in the input field at the bottom of the chat
2. Press Enter or click the Send button
3. The system will process your query and display the response
4. If tools are used in the response, they will be highlighted in the chat

### Using Tools

On the left side, you'll see a list of available tools. You can:

1. Click on any tool to start a query template
2. Complete the query with your specific request
3. Send the query

### Example Queries

- "What time is it right now?"
- "Clone the repository at https://github.com/username/repo.git"
- "What's the weather like in New York?"
- "Analyze the code in the cloned repository"

## Troubleshooting

If you encounter issues:

1. Ensure the MCP server is running
2. Check console logs for error messages
3. Verify your .env file has the necessary API keys
4. Restart both the server and client interface

## License

This project is licensed under the terms of the MIT license. 
