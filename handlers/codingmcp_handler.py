"""
CodingMCP protocol handler that allows Claude to act as a pair programming assistant.
Based on: https://github.com/ezyang/codemcp
"""
import os
import json
import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils.tool_base import BaseHandler, ToolExecution

logger = logging.getLogger(__name__)

class CodingMCPHandler(BaseHandler):
    """Handler for the CodingMCP protocol that enables Claude to act as a pair programming assistant"""
    
    def __init__(self):
        super().__init__()
        self.workspace_dir = None
        self.git_initialized = False
        self.config = {}
        self.commands = {}
        
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Execute the CodingMCP tool with the given parameters"""
        action = params.get("action", "")
        
        if action == "initialize":
            return await self._initialize_workspace(params)
        elif action == "read_file":
            return await self._read_file(params)
        elif action == "write_file":
            return await self._write_file(params)
        elif action == "list_files":
            return await self._list_files(params)
        elif action == "run_command":
            return await self._run_command(params)
        elif action == "run_test":
            return await self._run_test(params)
        elif action == "run_format":
            return await self._run_format(params)
        elif action == "git_commit":
            return await self._git_commit(params)
        else:
            return ToolExecution(content=f"Error: Unknown action '{action}'")
    
    async def _initialize_workspace(self, params: Dict[str, Any]) -> ToolExecution:
        """Initialize the workspace directory for code manipulation"""
        workspace_path = params.get("workspace_path", "")
        
        if not workspace_path:
            return ToolExecution(content="Error: workspace_path not provided")
        
        workspace_path = os.path.expanduser(workspace_path)
        if not os.path.exists(workspace_path):
            return ToolExecution(content=f"Error: Directory {workspace_path} does not exist")
        
        self.workspace_dir = workspace_path
        
        # Check for git repository
        is_git_repo = await self._run_git_command(["status"], check_result=False)
        self.git_initialized = is_git_repo.returncode == 0
        
        # If not a git repo and auto_init is True, initialize git
        if not self.git_initialized and params.get("auto_init_git", False):
            init_result = await self._run_git_command(["init"])
            self.git_initialized = init_result.returncode == 0
        
        # Load config from codemcp.toml if available
        config_path = os.path.join(workspace_path, "codemcp.toml")
        if os.path.exists(config_path):
            try:
                import toml
                with open(config_path, "r") as f:
                    self.config = toml.load(f)
                
                # Load commands from config
                if "commands" in self.config:
                    self.commands = self.config["commands"]
            except Exception as e:
                logger.error(f"Error loading config: {str(e)}")
        
        status = "initialized"
        if self.git_initialized:
            status += " (git repository)"
        else:
            status += " (not a git repository)"
        
        return ToolExecution(content=f"Workspace {workspace_path} {status}")
    
    async def _read_file(self, params: Dict[str, Any]) -> ToolExecution:
        """Read a file from the workspace"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        file_path = params.get("file_path", "")
        if not file_path:
            return ToolExecution(content="Error: file_path not provided")
        
        full_path = os.path.join(self.workspace_dir, file_path)
        if not os.path.exists(full_path):
            return ToolExecution(content=f"Error: File {file_path} does not exist")
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return ToolExecution(content=content)
        except Exception as e:
            return ToolExecution(content=f"Error reading file: {str(e)}")
    
    async def _write_file(self, params: Dict[str, Any]) -> ToolExecution:
        """Write content to a file in the workspace"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        
        if not file_path:
            return ToolExecution(content="Error: file_path not provided")
        
        full_path = os.path.join(self.workspace_dir, file_path)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return ToolExecution(content=f"Successfully wrote to {file_path}")
        except Exception as e:
            return ToolExecution(content=f"Error writing file: {str(e)}")
    
    async def _list_files(self, params: Dict[str, Any]) -> ToolExecution:
        """List files in the workspace directory"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        subdir = params.get("subdir", "")
        pattern = params.get("pattern", "*")
        
        dir_to_search = self.workspace_dir
        if subdir:
            dir_to_search = os.path.join(self.workspace_dir, subdir)
        
        if not os.path.exists(dir_to_search):
            return ToolExecution(content=f"Error: Directory {subdir} does not exist")
        
        try:
            import glob
            
            # Use glob to find files matching the pattern
            glob_pattern = os.path.join(dir_to_search, pattern)
            files = glob.glob(glob_pattern, recursive=True)
            
            # Get relative paths to workspace
            relative_files = [os.path.relpath(f, self.workspace_dir) for f in files]
            
            return ToolExecution(content=json.dumps(relative_files, indent=2))
        except Exception as e:
            return ToolExecution(content=f"Error listing files: {str(e)}")
    
    async def _run_command(self, params: Dict[str, Any]) -> ToolExecution:
        """Run a shell command in the workspace directory"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        command = params.get("command", "")
        if not command:
            return ToolExecution(content="Error: command not provided")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "exitCode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8")
            }
            
            return ToolExecution(content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolExecution(content=f"Error running command: {str(e)}")
    
    async def _run_test(self, params: Dict[str, Any]) -> ToolExecution:
        """Run tests in the workspace using the configured test command"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        if not self.commands.get("test"):
            return ToolExecution(content="Error: No test command configured in codemcp.toml")
        
        test_selector = params.get("test_selector", "")
        
        test_command = self.commands["test"]
        if isinstance(test_command, list):
            command = test_command[0]
        else:
            command = test_command
            
        if test_selector:
            command = f"{command} {test_selector}"
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "exitCode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8")
            }
            
            return ToolExecution(content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolExecution(content=f"Error running tests: {str(e)}")
    
    async def _run_format(self, params: Dict[str, Any]) -> ToolExecution:
        """Run the code formatter in the workspace using the configured format command"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        if not self.commands.get("format"):
            return ToolExecution(content="Error: No format command configured in codemcp.toml")
        
        format_command = self.commands["format"]
        if isinstance(format_command, list):
            command = format_command[0]
        else:
            command = format_command
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "exitCode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8")
            }
            
            return ToolExecution(content=json.dumps(result, indent=2))
        except Exception as e:
            return ToolExecution(content=f"Error running formatter: {str(e)}")
    
    async def _git_commit(self, params: Dict[str, Any]) -> ToolExecution:
        """Create a Git commit with the current changes"""
        if not self.workspace_dir:
            return ToolExecution(content="Error: Workspace not initialized")
        
        if not self.git_initialized:
            return ToolExecution(content="Error: Git repository not initialized")
        
        message = params.get("message", f"CodeMCP commit at {datetime.now().isoformat()}")
        
        try:
            # Add all changes
            add_result = await self._run_git_command(["add", "."])
            if add_result.returncode != 0:
                return ToolExecution(
                    content=f"Error adding files to Git: {add_result.stderr.decode('utf-8')}"
                )
            
            # Check if there are changes to commit
            status_result = await self._run_git_command(["status", "--porcelain"])
            if not status_result.stdout:
                return ToolExecution(content="No changes to commit")
            
            # Commit changes
            commit_result = await self._run_git_command(["commit", "-m", message])
            if commit_result.returncode != 0:
                return ToolExecution(
                    content=f"Error committing changes: {commit_result.stderr.decode('utf-8')}"
                )
            
            return ToolExecution(
                content=f"Successfully committed changes: {commit_result.stdout.decode('utf-8')}"
            )
        except Exception as e:
            return ToolExecution(content=f"Error during Git commit: {str(e)}")
    
    async def _run_git_command(self, args: List[str], check_result: bool = True) -> subprocess.CompletedProcess:
        """Run a Git command in the workspace directory"""
        if not self.workspace_dir:
            raise ValueError("Workspace not initialized")
        
        cmd = ["git"] + args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.workspace_dir
        )
        
        stdout, stderr = await process.communicate()
        
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )
        
        if check_result and result.returncode != 0:
            logger.error(f"Git command failed: {stderr.decode('utf-8')}")
        
        return result 