"""
Tests for command handler extracted from original handler file
"""

import pytest

from handlers.command_handler import CommandExecutionToolHandler


@pytest.mark.asyncio
async def test_command_handler():
    handler = CommandExecutionToolHandler()

    # Test basic command
    print("\nTesting basic command execution...")
    result = await handler.execute(
        {"command": "echo 'Hello, World!'", "working_dir": ".", "timeout": 10}
    )
    print(result.content)

    # Test command with error
    print("\nTesting command with error...")
    result = await handler.execute(
        {"command": "ls non_existent_file", "working_dir": ".", "timeout": 10}
    )
    print(result.content)

    # Test command with timeout
    print("\nTesting command with timeout...")
    result = await handler.execute(
        {"command": "sleep 2", "working_dir": ".", "timeout": 1}
    )
    print(result.content) 