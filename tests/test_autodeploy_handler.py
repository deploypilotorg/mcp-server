"""
Tests for autodeploy handler extracted from original handler file
"""

import pytest

from handlers.autodeploy_handler import AutoDeployToolHandler


@pytest.mark.asyncio
async def test_autodeploy_handler():
    handler = AutoDeployToolHandler()

    # Set all necessary mock state
    handler.repo_path = "."  # avoid NoneType issues
    handler.deploy_config = {
        "type": "static",
        "target": "local",
        "build_dir": "./build",
        "build_command": "echo Building...",  # 👈 critical addition!
        "output_dir": "./build"
    }

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
