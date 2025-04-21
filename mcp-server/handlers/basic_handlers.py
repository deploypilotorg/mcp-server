"""
Basic tool handlers for time, calculation and weather.
"""
from datetime import datetime
from typing import Dict, Any

from ..utils.tool_base import BaseHandler, ToolExecution

class TimeToolHandler(BaseHandler):
    """Handler for getting the current time"""
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Get the current time"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ToolExecution(content=current_time)

class CalcToolHandler(BaseHandler):
    """Handler for performing calculations"""
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Perform a calculation"""
        expression = params.get("expression", "")
        try:
            # Safely evaluate mathematical expressions
            result = eval(expression, {"__builtins__": {}}, {
                "add": lambda x, y: x + y,
                "subtract": lambda x, y: x - y,
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else "Division by zero error"
            })
            return ToolExecution(content=str(result))
        except Exception as e:
            return ToolExecution(content=f"Error: {str(e)}")

class WeatherToolHandler(BaseHandler):
    """Handler for getting mock weather data"""
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Get mock weather data for a location"""
        location = params.get("location", "")
        if not location:
            return ToolExecution(content="Error: Location not provided")
            
        # Mock weather data
        weather_data = {
            "New York": {"condition": "Sunny", "temperature": "72°F"},
            "London": {"condition": "Rainy", "temperature": "60°F"},
            "Tokyo": {"condition": "Cloudy", "temperature": "65°F"},
            "Sydney": {"condition": "Partly Cloudy", "temperature": "70°F"},
            "Paris": {"condition": "Clear", "temperature": "68°F"}
        }
        
        if location in weather_data:
            data = weather_data[location]
            return ToolExecution(content=f"Weather in {location}: {data['condition']}, {data['temperature']}")
        else:
            return ToolExecution(content=f"No weather data available for {location}") 