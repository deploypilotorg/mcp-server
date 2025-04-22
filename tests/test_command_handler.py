"""
Tests for command execution handler
"""

import pytest

from handlers.command_handler import CommandExecutionToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_basic_command_execution():
    """Test basic command execution"""
    handler = CommandExecutionToolHandler()
    
    result = await handler.execute(
        {"command": "echo 'Hello, World!'", "working_dir": ".", "timeout": 10}
    )
    assert isinstance(result, ToolExecution)
    assert "Hello, World!" in result.content
    assert "Error" not in result.content


@pytest.mark.asyncio
async def test_command_with_error():
    """Test command execution with error"""
    handler = CommandExecutionToolHandler()
    
    result = await handler.execute(
        {"command": "ls non_existent_file", "working_dir": ".", "timeout": 10}
    )
    assert isinstance(result, ToolExecution)
    assert "Error" in result.content


@pytest.mark.asyncio
async def test_command_with_timeout():
    """Test command execution with timeout"""
    handler = CommandExecutionToolHandler()
    
    result = await handler.execute(
        {"command": "sleep 2", "working_dir": ".", "timeout": 1}
    )
    assert isinstance(result, ToolExecution)
    assert "timeout" in result.content.lower() 