"""
Tests for CodingMCP handler
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock
from unittest.mock import patch, MagicMock, mock_open

from handlers.codingmcp_handler import CodingMCPHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_initialize_workspace():
    """Test initializing workspace"""
    handler = CodingMCPHandler()
    
    # Mock os.path.exists and os.path.expanduser
    with patch('os.path.exists', return_value=True), \
         patch('os.path.expanduser', return_value='/tmp/mock-workspace'), \
         patch.object(handler, '_run_git_command') as mock_git:
        
        # Mock git status to indicate this is a git repo
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_git.return_value = mock_process
        
        params = {"workspace_path": "~/mock-workspace"}
        result = await handler._initialize_workspace(params)
        
        assert isinstance(result, ToolExecution)
        assert "Workspace" in result.content
        assert "git repository" in result.content
        assert handler.workspace_dir == '/tmp/mock-workspace'
        assert handler.git_initialized is True


@pytest.mark.asyncio
async def test_read_file():
    """Test reading file from workspace"""
    handler = CodingMCPHandler()
    handler.workspace_dir = '/tmp/mock-workspace'
    
    # Mock os.path functions and open
    with patch('os.path.exists', return_value=True), \
         patch('os.path.join', return_value='/tmp/mock-workspace/test.py'), \
         patch('builtins.open', mock_open(read_data='print("Hello World")')):
        
        params = {"file_path": "test.py"}
        result = await handler._read_file(params)
        
        assert isinstance(result, ToolExecution)
        assert 'print("Hello World")' in result.content


@pytest.mark.asyncio
async def test_write_file():
    """Test writing file to workspace"""
    handler = CodingMCPHandler()
    handler.workspace_dir = '/tmp/mock-workspace'
    
    # Mock os functions and open
    with patch('os.makedirs'), \
         patch('os.path.join', return_value='/tmp/mock-workspace/test.py'), \
         patch('builtins.open', mock_open()) as mock_file:
        
        params = {"file_path": "test.py", "content": 'print("Hello World")'}
        result = await handler._write_file(params)
        
        assert isinstance(result, ToolExecution)
        assert "Successfully wrote" in result.content
        mock_file().write.assert_called_once_with('print("Hello World")')


@pytest.mark.asyncio
async def test_list_files():
    """Test listing files in workspace"""
    handler = CodingMCPHandler()
    handler.workspace_dir = '/tmp/mock-workspace'
    
    # Mock relevant functions
    with patch('os.path.exists', return_value=True), \
         patch('os.path.join', return_value='/tmp/mock-workspace/src'), \
         patch('glob.glob') as mock_glob:
        
        mock_glob.return_value = [
            '/tmp/mock-workspace/src/file1.py',
            '/tmp/mock-workspace/src/file2.py'
        ]
        
        # Also patch os.path.relpath to return expected relative paths
        with patch('os.path.relpath', side_effect=["src/file1.py", "src/file2.py"]):
            params = {"subdir": "src", "pattern": "*.py"}
            result = await handler._list_files(params)
            
            assert isinstance(result, ToolExecution)
            assert "src/file1.py" in result.content
            assert "src/file2.py" in result.content


@pytest.mark.asyncio
async def test_run_command():
    """Test running command in workspace"""
    handler = CodingMCPHandler()
    handler.workspace_dir = '/tmp/mock-workspace'
    
    # Mock asyncio.create_subprocess_shell
    with patch('asyncio.create_subprocess_shell') as mock_subprocess:
        # Setup the mock process
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"command output", b""))
        mock_subprocess.return_value = mock_process

        
        params = {"command": "ls -la"}
        result = await handler._run_command(params)
        
        assert isinstance(result, ToolExecution)
        assert "exitCode" in result.content
        assert "stdout" in result.content
        assert "command output" in result.content


@pytest.mark.asyncio
async def test_git_commit():
    """Test git commit operation"""
    handler = CodingMCPHandler()
    handler.workspace_dir = '/tmp/mock-workspace'
    handler.git_initialized = True
    
    # Mock the _run_git_command method
    with patch.object(handler, '_run_git_command') as mock_git:
        # Configure the mock to return successful git operations
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = b"Changes committed"
        mock_git.return_value = mock_process
        
        params = {"message": "Test commit message"}
        result = await handler._git_commit(params)
        
        assert isinstance(result, ToolExecution)
        assert "Successfully committed" in result.content 