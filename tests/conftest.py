"""
Pytest configuration and fixtures for MCP server tests
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock

from utils.tool_base import BaseHandler


@pytest.fixture
def mock_repo_path():
    """Fixture to provide a temporary repository path for tests"""
    return "/tmp/mock-repo-path"


@pytest.fixture
def mock_workspace_path():
    """Fixture to provide a temporary workspace path for tests"""
    return "/tmp/mock-workspace"


@pytest.fixture
def mock_handler():
    """Fixture to provide a mock handler for testing"""
    handler = MagicMock(spec=BaseHandler)
    handler.repo_path = "/tmp/mock-repo-path"
    handler.repo_name = "test-repo"
    handler.repo_url = "https://github.com/test/test-repo.git"
    return handler


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close() 