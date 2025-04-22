"""
Tests for UI generator handler
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open

from handlers.ui_generator_handler import UIGeneratorToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_scan_apps():
    """Test scanning for apps in repository"""
    handler = UIGeneratorToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock the file system operations
    with patch('os.walk') as mock_walk, \
         patch('builtins.open', mock_open(read_data='import flask\napp = flask.Flask(__name__)')):
        
        mock_walk.return_value = [
            ('/tmp/mock-repo-path', ['src'], []),
            ('/tmp/mock-repo-path/src', [], ['app.py', 'index.html', 'main.js']),
        ]
        
        result = await handler._scan_apps()
        
        assert isinstance(result, ToolExecution)
        assert "Detected applications" in result.content
        assert "app.py" in result.content


@pytest.mark.asyncio
async def test_generate_ui_python():
    """Test generating UI for Python application"""
    handler = UIGeneratorToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock file operations and subprocess
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('builtins.open', mock_open(read_data='import flask\napp = flask.Flask(__name__)')), \
         patch.object(handler, '_run_python_app') as mock_run_app:
        
        mock_run_app.return_value = ToolExecution(content="UI started at http://localhost:5000")
        
        result = await handler._generate_ui('app.py')
        
        assert isinstance(result, ToolExecution)
        assert "http://localhost:" in result.content


@pytest.mark.asyncio
async def test_generate_ui_html():
    """Test generating UI for HTML application"""
    handler = UIGeneratorToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock file operations and handler methods
    with patch('os.path.exists', return_value=True), \
         patch('os.path.isfile', return_value=True), \
         patch('builtins.open', mock_open(read_data='<!DOCTYPE html><html><body><h1>Test</h1></body></html>')), \
         patch.object(handler, '_serve_html') as mock_serve_html:
        
        mock_serve_html.return_value = ToolExecution(content="UI started at http://localhost:8080")
        
        result = await handler._generate_ui('index.html')
        
        assert isinstance(result, ToolExecution)
        assert "http://localhost:" in result.content


@pytest.mark.asyncio
async def test_stop_ui():
    """Test stopping UI"""
    handler = UIGeneratorToolHandler()
    
    # Mock subprocess.run for killing processes
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock the active_sessions attribute to include our session
        handler.active_sessions = {"test_session": {"port": 5000, "pid": 12345}}
        
        result = await handler._stop_ui("test_session")
        
        assert isinstance(result, ToolExecution)
        assert "Successfully stopped UI" in result.content
        assert "test_session" in result.content


@pytest.mark.asyncio
async def test_detect_app_type():
    """Test app type detection"""
    handler = UIGeneratorToolHandler()
    
    # Test Python Flask app detection
    python_flask = "from flask import Flask\napp = Flask(__name__)"
    assert handler._detect_app_type("app.py", python_flask) == "python_flask"
    
    # Test HTML app detection
    html = "<!DOCTYPE html><html><body><h1>Hello</h1></body></html>"
    assert handler._detect_app_type("index.html", html) == "html"
    
    # Test JavaScript app detection
    js = "import React from 'react';\nfunction App() { return <div>Hello</div>; }"
    assert handler._detect_app_type("app.js", js) == "javascript" 