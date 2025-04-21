"""
Base class for MCP tool handlers
"""
class ToolExecution:
    """Represents the result of a tool execution"""
    def __init__(self, content: str):
        self.content = content

class BaseHandler:
    """Base class for all tool handlers"""
    def __init__(self):
        # Common properties that can be shared across handlers
        self.repo_path = None
        self.repo_name = None
        self.repo_url = None
    
    async def execute(self, params):
        """Execute the tool - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute method") 