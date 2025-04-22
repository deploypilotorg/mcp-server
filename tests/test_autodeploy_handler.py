"""
Tests for autodeploy handler
"""

import pytest
from unittest.mock import patch, MagicMock

from handlers.autodeploy_handler import AutoDeployToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_detect_deployment_type():
    """Test detecting deployment type"""
    handler = AutoDeployToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock file system to indicate a static web app
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['index.html', 'style.css', 'script.js']
        
        result = await handler._detect_deployment_type()
        
        assert isinstance(result, ToolExecution)
        assert "Detected deployment types" in result.content
        assert "static" in result.content.lower()


@pytest.mark.asyncio
async def test_prepare_deployment():
    """Test preparing deployment"""
    handler = AutoDeployToolHandler()
    handler.repo_path = '/tmp/mock-repo-path'
    
    # Mock the deployment detection and deployment methods
    with patch.object(handler, '_deploy_static') as mock_deploy_static:
        mock_deploy_static.return_value = {
            "status": "prepared",
            "details": "Static site deployment prepared",
            "next_steps": ["start_deployment"]
        }
        
        deploy_config = {"type": "static", "target": "local"}
        result = await handler._prepare_deployment(deploy_config)
        
        assert isinstance(result, ToolExecution)
        assert "prepared" in result.content.lower()
        assert handler.current_deployment is not None
        assert handler.current_deployment["type"] == "static"


@pytest.mark.asyncio
async def test_start_deployment():
    """Test starting deployment"""
    handler = AutoDeployToolHandler()
    handler.current_deployment = {
        "type": "static",
        "target": "local",
        "status": "prepared",
        "deploy_func": "_deploy_static",
        "config": {"output_dir": "/tmp/output"},
    }
    
    # Mock subprocess and other methods needed for deployment
    with patch('subprocess.run') as mock_run, \
         patch('os.makedirs'):
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = await handler._start_deployment()
        
        assert isinstance(result, ToolExecution)
        assert "deployment started" in result.content.lower() or "deployed successfully" in result.content.lower()


@pytest.mark.asyncio
async def test_get_deployment_status():
    """Test getting deployment status"""
    handler = AutoDeployToolHandler()
    
    # Test with no deployment
    result = await handler._get_deployment_status()
    assert "no active deployment" in result.content.lower()
    
    # Test with active deployment
    handler.current_deployment = {
        "type": "static",
        "target": "local",
        "status": "running",
        "start_time": "2023-01-01T12:00:00",
    }
    
    result = await handler._get_deployment_status()
    assert "running" in result.content.lower()
    assert "static" in result.content.lower()


@pytest.mark.asyncio
async def test_abort_deployment():
    """Test aborting deployment"""
    handler = AutoDeployToolHandler()
    
    # Test with no deployment
    result = await handler._abort_deployment()
    assert "no active deployment" in result.content.lower()
    
    # Test with active deployment
    handler.current_deployment = {
        "type": "static",
        "target": "local",
        "status": "running",
        "process": MagicMock(),
    }
    
    result = await handler._abort_deployment()
    assert "aborted" in result.content.lower()
    assert handler.current_deployment["status"] == "aborted" 