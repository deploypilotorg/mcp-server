# MCP Server

A modular Model Control Protocol (MCP) server that provides tools for interacting with GitHub repositories.

## Features

- Modular design with extensible tool handlers
- Support for both HTTP and stdio transport
- GitHub repository analysis tools
- Command execution capability
- CORS support for cross-origin requests

## Installation

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### HTTP Mode

Start the server in HTTP mode with optional host and port:

```
python server.py --http --host 0.0.0.0 --port 8000
```

This will start the server and make it accessible at `http://localhost:8000` (or the specified host/port).

### Stdio Mode

Start the server in stdio mode for direct pipe-based communication:

```
python server.py
```

This mode is used when the MCP server is called directly by a client through stdin/stdout.

## Available Tools

The server provides the following tools:

- **get_time**: Get the current time
- **calculate**: Perform simple calculations
- **get_weather**: Get mock weather data for a location
- **github_repo**: Clone and analyze GitHub repositories
- **execute_command**: Execute commands in the system shell

## API Endpoints

When running in HTTP mode, the server provides the following endpoints:

- **GET /initialize**: Initialize the connection and get available tools
- **GET /list_tools**: List all available tools
- **POST /execute_tool**: Execute a specific tool with arguments

### Example API Usage

#### Execute a Tool

```
POST /execute_tool
Content-Type: application/json

{
  "name": "github_repo",
  "arguments": {
    "action": "clone",
    "repo_url": "https://github.com/example/repo.git"
  }
}
```

## Extending the Server

To add a new tool:

1. Create a new handler class in the `handlers` directory that extends `BaseHandler`
2. Implement the `execute` method in your handler
3. Register your handler in the `_setup_handlers` method in `server.py`
4. Create a corresponding tool definition in the `_setup_tools` method 

## Testing

The server includes a comprehensive set of unit tests using pytest and pytest-asyncio. 

### Running Tests

To run the tests:

```
pytest
```

For more verbose output:

```
pytest -v
```

To run tests with code coverage:

```
pytest --cov=handlers --cov=utils
```

### Adding New Tests

When adding new handlers, create corresponding test files in the `tests` directory:

1. Create a test file named `test_yourhandler.py`
2. Use pytest fixtures from `conftest.py` where appropriate
3. Write tests for all public methods in your handler 