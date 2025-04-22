"""
Tests for GitHub handlers
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from handlers.github_handler import GitHubCloneToolHandler, GitHubListFilesToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_github_clone_handler():
    """Test GitHub clone handler"""
    with patch('subprocess.run') as mock_run:
        # Configure the mock to return a successful clone
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Cloning..."
        mock_run.return_value = mock_process
        
        # Also patch tempfile.mkdtemp to return a predictable path
        with patch('tempfile.mkdtemp', return_value='/tmp/mock-repo-path'):
            handler = GitHubCloneToolHandler()
            
            result = await handler.execute(
                {"repo_url": "https://github.com/octocat/Hello-World.git"}
            )
            
            assert isinstance(result, ToolExecution)
            assert "Successfully cloned repository" in result.content
            assert "https://github.com/octocat/Hello-World.git" in result.content
            assert handler.repo_path == '/tmp/mock-repo-path'
            assert handler.repo_name == 'Hello-World'


@pytest.mark.asyncio
async def test_github_clone_handler_error():
    """Test GitHub clone handler with error"""
    with patch('subprocess.run') as mock_run:
        # Configure the mock to return a failed clone
        mock_run.side_effect = Exception("Clone failed")
        
        handler = GitHubCloneToolHandler()
        
        result = await handler.execute(
            {"repo_url": "https://github.com/invalid/repo.git"}
        )
        
        assert isinstance(result, ToolExecution)
        assert "Error" in result.content


@pytest.mark.asyncio
async def test_github_list_files_handler():
    """Test GitHub list files handler"""
    # Create a mock clone handler
    clone_handler = MagicMock()
    clone_handler.repo_path = '/tmp/mock-repo-path'
    
    # Patch os functions
    with patch('os.path.exists', return_value=True), \
         patch('os.walk') as mock_walk:
        
        # Configure the mock for os.walk to return sample directory structure
        mock_walk.return_value = [
            ('/tmp/mock-repo-path', ['dir1', '.git'], ['file1.txt']),
            ('/tmp/mock-repo-path/dir1', [], ['file2.txt']),
        ]
        
        # Set up the handler with the mock clone handler
        handler = GitHubListFilesToolHandler(clone_handler)
        
        result = await handler.execute({})
        
        assert isinstance(result, ToolExecution)
        assert "Directory: dir1" in result.content
        assert "File: file1.txt" in result.content
        assert "File: dir1/file2.txt" in result.content
        assert ".git" not in result.content


@pytest.mark.asyncio
async def test_github_list_files_no_repo():
    """Test GitHub list files handler with no repository cloned"""
    # Create a mock clone handler with no repo_path
    clone_handler = MagicMock()
    clone_handler.repo_path = None
    
    handler = GitHubListFilesToolHandler(clone_handler)
    
    result = await handler.execute({})
    
    assert isinstance(result, ToolExecution)
    assert "Error" in result.content
    assert "No repository has been cloned" in result.content 