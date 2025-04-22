"""
Tests for UI generator handler extracted from original handler file
"""

import pytest

from handlers.ui_generator_handler import UIGeneratorToolHandler


@pytest.mark.asyncio
async def test_ui_generator_handler():
    handler = UIGeneratorToolHandler()

    # Test scan_apps
    print("\nTesting scan_apps action...")
    result = await handler.execute({"action": "scan_apps", "repo_path": "."})
    print(result.content)

    # Test generate_ui for Python app
    print("\nTesting generate_ui action for Python app...")
    result = await handler.execute(
        {
            "action": "generate_ui",
            "repo_path": ".",
            "app_path": "handlers/ui_generator_handler.py",
        }
    )
    print(result.content)

    # Test generate_ui for HTML app
    print("\nTesting generate_ui action for HTML app...")
    result = await handler.execute(
        {"action": "generate_ui", "repo_path": ".", "app_path": "index.html"}
    )
    print(result.content)

    # Test stop_ui
    print("\nTesting stop_ui action...")
    result = await handler.execute(
        {"action": "stop_ui", "session_id": "test_session"}
    )
    print(result.content) 