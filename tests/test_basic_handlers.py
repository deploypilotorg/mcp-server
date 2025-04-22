"""
Tests for basic handlers extracted from original handler file
"""

import pytest

from handlers.basic_handlers import TimeToolHandler, CalcToolHandler


@pytest.mark.asyncio
async def test_basic_handlers():
    # Test TimeToolHandler
    print("\nTesting TimeToolHandler...")
    time_handler = TimeToolHandler()
    result = await time_handler.execute({})
    print(result.content)

    # Test CalcToolHandler
    print("\nTesting CalcToolHandler...")
    calc_handler = CalcToolHandler()

    # Test addition
    result = await calc_handler.execute({"expression": "add(5, 3)"})
    print("5 + 3 =", result.content)

    # Test subtraction
    result = await calc_handler.execute({"expression": "subtract(10, 4)"})
    print("10 - 4 =", result.content)

    # Test multiplication
    result = await calc_handler.execute({"expression": "multiply(6, 7)"})
    print("6 * 7 =", result.content)

    # Test division
    result = await calc_handler.execute({"expression": "divide(20, 5)"})
    print("20 / 5 =", result.content)

    # Test division by zero
    result = await calc_handler.execute({"expression": "divide(10, 0)"})
    print("10 / 0 =", result.content) 