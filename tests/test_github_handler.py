"""
Tests for GitHub handler extracted from original handler file
"""

import pytest

from handlers.github_handler import GitHubCloneToolHandler


@pytest.mark.asyncio
async def test_github_handler():
    handler = GitHubCloneToolHandler()

    # Test clone
    print("\nTesting clone action...")
    result = await handler.execute(
        {"repo_url": "https://github.com/octocat/Hello-World.git"}
    )
    print(result.content)

    # Test list_directory
    print("\nTesting list_directory action...")
    result = await handler.execute({"action": "list_directory"})
    print(result.content)

    # Test get_repo_info
    print("\nTesting get_repo_info action...")
    result = await handler.execute({"action": "get_repo_info"})
    print(result.content)

    # Test read_file
    print("\nTesting read_file action...")
    result = await handler.execute(
        {"action": "read_file", "file_path": "README.md"}
    )
    print(result.content) 