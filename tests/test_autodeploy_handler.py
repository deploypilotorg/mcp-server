"""
Autodeploy handler for deploying code repositories.
"""

import asyncio
import json
import os
from unittest.mock import patch
from utils.tool_base import BaseHandler, ToolExecution
from ..oslers.autodeploy_handler import AutoDeployToolHandler
import subprocess
from typing import Any, Dict, List, Optional
import pytest

class AutoDeployToolHandler(BaseHandler):
    """Handler for automatically deploying code repositories"""

    def __init__(self):
        super().__init__()
        self.repo_path = None
        self.deploy_config = None
        self.deploy_status = {"current_deployment": None, "history": []}

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Manage deployment operations"""
        print(f"Debug: repo_path is {self.repo_path}")  # Add this line
        if not os.path.exists(self.repo_path):
            raise ValueError("Invalid repo_path")
        action = params.get("action", "")
        self.repo_path = params.get("repo_path", None)
        # Implementation of deployment actions goes here
        return ToolExecution(success=True, content=f"Executed action: {action}")

@pytest.mark.asyncio
async def test_autodeploy_handler():
    handler = AutoDeployToolHandler()

    # Fully mock internal state to prevent deployment errors
    handler.repo_path = "."
    handler.deploy_config = {
        "type": "static",
        "target": "local",
        "build_dir": "./build",
        "build_command": "echo Building...",
        "output_dir": "./build"
    }
    handler.build_dir = "./build"
    handler.output_dir = "./build"

    with patch("os.path.exists", return_value=True):  # Mock os.path.exists
        # Test detect_deployment_type
        print("\nTesting detect_deployment_type action...")
        result = await handler.execute(
            {"action": "detect_deployment_type", "repo_path": "."}
        )
        print(result.content)

        # Test prepare_deployment
        print("\nTesting prepare_deployment action...")
        result = await handler.execute(
            {
                "action": "prepare_deployment",
                "repo_path": ".",
                "deploy_config": handler.deploy_config,
            }
        )
        print(result.content)

        # Test get_status
        print("\nTesting get_status action...")
        result = await handler.execute({"action": "get_status"})
        print(result.content)

        # Test start_deployment
        print("\nTesting start_deployment action...")
        result = await handler.execute({"action": "start_deployment"})
        print(result.content)

        # Test abort_deployment
        print("\nTesting abort_deployment action...")
        result = await handler.execute({"action": "abort_deployment"})
        print(result.content)

# Additional step for installing the project
def install_project():
    subprocess.run(["pip", "install", "-e", "."])

# Set PYTHONPATH for the environment
def set_pythonpath():
    subprocess.run(["echo", "PYTHONPATH=$PYTHONPATH:$(pwd)", ">>", "$GITHUB_ENV"])
