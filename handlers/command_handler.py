"""
Command execution handler for running system commands.
"""
import os
import asyncio
from typing import Dict, Any

from utils.tool_base import BaseHandler, ToolExecution

class CommandExecutionToolHandler(BaseHandler):
    """Handler for executing system commands"""
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Execute a command and return the result"""
        command = params.get("command", "")
        if not command:
            return ToolExecution(content="Error: Command not provided")
        
        working_dir = params.get("working_dir", None)
        timeout = params.get("timeout", 30)  # Default timeout of 30 seconds
        
        try:
            # Set up the execution environment
            env = os.environ.copy()
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True,
                cwd=working_dir,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                stdout_str = stdout.decode('utf-8', errors='replace')
                stderr_str = stderr.decode('utf-8', errors='replace')
                
                if process.returncode != 0:
                    result = f"Command execution failed with exit code {process.returncode}:\n\nSTDOUT:\n{stdout_str}\n\nSTDERR:\n{stderr_str}"
                else:
                    result = f"Command executed successfully:\n\nSTDOUT:\n{stdout_str}"
                    if stderr_str.strip():
                        result += f"\n\nSTDERR:\n{stderr_str}"
                
                return ToolExecution(content=result)
            
            except asyncio.TimeoutError:
                process.kill()
                return ToolExecution(content=f"Error: Command execution timed out after {timeout} seconds")
                
        except Exception as e:
            return ToolExecution(content=f"Error executing command: {str(e)}") 