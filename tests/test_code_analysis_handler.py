"""
Tests for code analysis handler extracted from original handler file
"""

import pytest

from handlers.code_analysis_handler import CodeAnalysisToolHandler


@pytest.mark.asyncio
async def test_code_analysis_handler():
    handler = CodeAnalysisToolHandler()

    # Test analyze_languages
    print("\nTesting analyze_languages action...")
    result = await handler.execute(
        {"action": "analyze_languages", "repo_path": "."}
    )
    print(result.content)

    # Test find_todos
    print("\nTesting find_todos action...")
    result = await handler.execute({"action": "find_todos", "repo_path": "."})
    print(result.content)

    # Test analyze_complexity
    print("\nTesting analyze_complexity action...")
    result = await handler.execute(
        {
            "action": "analyze_complexity",
            "repo_path": ".",
            "file_path": "handlers/code_analysis_handler.py",
        }
    )
    print(result.content)

    # Test search_code
    print("\nTesting search_code action...")
    result = await handler.execute(
        {"action": "search_code", "repo_path": ".", "query": "class"}
    )
    print(result.content)

    # Test get_dependencies
    print("\nTesting get_dependencies action...")
    result = await handler.execute({"action": "get_dependencies", "repo_path": "."})
    print(result.content) 