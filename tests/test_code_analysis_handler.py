"""
Tests for code analysis handler
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open

from handlers.code_analysis_handler import CodeAnalysisToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_analyze_languages():
    """Test analyze languages functionality"""
    handler = CodeAnalysisToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock the os.walk function to return sample file structure
    with patch('os.walk') as mock_walk:
        mock_walk.return_value = [
            ('/tmp/mock-repo-path', ['src'], ['README.md']),
            ('/tmp/mock-repo-path/src', [], ['main.py', 'utils.js', 'styles.css']),
        ]
        
        result = await handler._analyze_languages()
        
        assert isinstance(result, ToolExecution)
        assert "Language distribution" in result.content
        assert "Python" in result.content
        assert "JavaScript" in result.content
        assert "CSS" in result.content
        assert "Markdown" in result.content


@pytest.mark.asyncio
async def test_find_todos():
    """Test find TODOs functionality"""
    handler = CodeAnalysisToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock file system operations
    with patch('os.walk') as mock_walk, \
         patch('builtins.open', mock_open(read_data='# TODO: Fix this issue\ndef test():\n    pass')):
        
        mock_walk.return_value = [
            ('/tmp/mock-repo-path', [], ['main.py']),
        ]
        
        result = await handler._find_todos()
        
        assert isinstance(result, ToolExecution)
        assert "TODO comments found" in result.content
        assert "main.py:1:" in result.content
        assert "Fix this issue" in result.content


@pytest.mark.asyncio
async def test_analyze_complexity():
    """Test analyze complexity functionality"""
    handler = CodeAnalysisToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock os.path functions and subprocess
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('os.path.join', return_value='/tmp/mock-repo-path/test.py'), \
         patch('subprocess.run') as mock_run:
        
        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "F 42:0 test_function - A (10)"
        mock_run.return_value = mock_process
        
        result = await handler._analyze_complexity('test.py')
        
        assert isinstance(result, ToolExecution)
        assert "Code complexity analysis" in result.content


@pytest.mark.asyncio
async def test_search_code():
    """Test search code functionality"""
    handler = CodeAnalysisToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock subprocess call
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.stdout = "main.py:10: def test_function():"
        mock_run.return_value = mock_process
        
        result = await handler._search_code('def test')
        
        assert isinstance(result, ToolExecution)
        assert "Search results for" in result.content
        assert "main.py:10:" in result.content


@pytest.mark.asyncio
async def test_get_dependencies():
    """Test get dependencies functionality"""
    handler = CodeAnalysisToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock file operations for different package files
    mock_files = {
        '/tmp/mock-repo-path/requirements.txt': 'pytest==7.0.0\nflask==2.0.0',
        '/tmp/mock-repo-path/package.json': '{"dependencies": {"react": "^17.0.0"}}'
    }
    
    # Mock os.path functions and open
    with patch('os.path.exists', lambda path: path in mock_files), \
         patch('os.path.isfile', return_value=True), \
         patch('builtins.open', lambda path, mode, **kwargs: mock_open(read_data=mock_files[path])()): 
        
        result = await handler._get_dependencies()
        
        assert isinstance(result, ToolExecution)
        assert "Dependencies found" in result.content
        assert "Python (requirements.txt)" in result.content or "Node.js (package.json)" in result.content 