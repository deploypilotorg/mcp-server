"""
Tests for basic handlers
"""

import pytest

from handlers.basic_handlers import TimeToolHandler, CalcToolHandler, WeatherToolHandler
from utils.tool_base import ToolExecution


@pytest.mark.asyncio
async def test_time_handler():
    """Test the TimeToolHandler"""
    time_handler = TimeToolHandler()
    result = await time_handler.execute({})
    
    assert isinstance(result, ToolExecution)
    assert isinstance(result.content, str)
    # We can't check exact time, but we can check format
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_calc_handler_addition():
    """Test the CalcToolHandler with addition"""
    calc_handler = CalcToolHandler()
    
    result = await calc_handler.execute({"expression": "add(5, 3)"})
    assert result.content == "8"


@pytest.mark.asyncio
async def test_calc_handler_subtraction():
    """Test the CalcToolHandler with subtraction"""
    calc_handler = CalcToolHandler()
    
    result = await calc_handler.execute({"expression": "subtract(10, 4)"})
    assert result.content == "6"


@pytest.mark.asyncio
async def test_calc_handler_multiplication():
    """Test the CalcToolHandler with multiplication"""
    calc_handler = CalcToolHandler()
    
    result = await calc_handler.execute({"expression": "multiply(6, 7)"})
    assert result.content == "42"


@pytest.mark.asyncio
async def test_calc_handler_division():
    """Test the CalcToolHandler with division"""
    calc_handler = CalcToolHandler()
    
    result = await calc_handler.execute({"expression": "divide(20, 5)"})
    assert result.content == "4.0"


@pytest.mark.asyncio
async def test_calc_handler_division_by_zero():
    """Test the CalcToolHandler with division by zero"""
    calc_handler = CalcToolHandler()
    
    result = await calc_handler.execute({"expression": "divide(10, 0)"})
    assert result.content == "Division by zero error"


@pytest.mark.asyncio
async def test_weather_handler():
    """Test the WeatherToolHandler"""
    weather_handler = WeatherToolHandler()
    
    # Test with valid location
    result = await weather_handler.execute({"location": "New York"})
    assert "Weather in New York" in result.content
    
    # Test with invalid location
    result = await weather_handler.execute({"location": "NonExistentPlace"})
    assert "No weather data available" in result.content
    
    # Test with missing location
    result = await weather_handler.execute({})
    assert "Error: Location not provided" in result.content 