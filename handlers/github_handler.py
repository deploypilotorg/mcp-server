"""
GitHub repository handler for cloning and analyzing repositories.
"""
import os
import shutil
import tempfile
import subprocess
from typing import Dict, Any

from utils.tool_base import BaseHandler, ToolExecution

class GitHubCloneToolHandler(BaseHandler):
    """Handler for cloning GitHub repositories"""
    def __init__(self):
        super().__init__()
        self.repo_path = None
        self.repo_name = None
        self.repo_url = None

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Clone a GitHub repository"""
        repo_url = params.get("repo_url", "")
        if not repo_url:
            return ToolExecution(content="Error: Repository URL not provided")
        
        # Clean up any previous repo
        if self.repo_path and os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)
        
        # Create a temporary directory
        self.repo_path = tempfile.mkdtemp()
        self.repo_url = repo_url
        self.repo_name = repo_url.split("/")[-1].replace(".git", "")
        
        try:
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", repo_url, self.repo_path], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return ToolExecution(content=f"Successfully cloned repository: {repo_url} to {self.repo_path}")
        except subprocess.CalledProcessError as e:
            return ToolExecution(content=f"Error cloning repository: {e.stderr}")

    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this handler"""
        return {
            "name": "github_clone",
            "description": "Clone a GitHub repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_url": {
                        "type": "string",
                        "description": "URL of the GitHub repository to clone"
                    }
                },
                "required": ["repo_url"]
            }
        }

class GitHubListFilesToolHandler(BaseHandler):
    """Handler for listing files in a cloned repository"""
    def __init__(self, clone_handler: GitHubCloneToolHandler):
        super().__init__()
        self.clone_handler = clone_handler

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """List files in the cloned repository"""
        if not self.clone_handler.repo_path or not os.path.exists(self.clone_handler.repo_path):
            return ToolExecution(content="Error: No repository has been cloned yet")
        
        try:
            # List directory contents
            contents = []
            for root, dirs, files in os.walk(self.clone_handler.repo_path):
                # Skip .git directory
                if '.git' in root:
                    continue
                
                # Get relative path
                rel_path = os.path.relpath(root, self.clone_handler.repo_path)
                if rel_path == '.':
                    rel_path = ''
                
                # Add directories
                for d in dirs:
                    if d != '.git':
                        contents.append(f"Directory: {os.path.join(rel_path, d)}")
                
                # Add files
                for f in files:
                    contents.append(f"File: {os.path.join(rel_path, f)}")
            
            return ToolExecution(content="\n".join(contents))
        except Exception as e:
            return ToolExecution(content=f"Error listing directory contents: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get the schema for this handler"""
        return {
            "name": "github_list_files",
            "description": "List files in a cloned GitHub repository",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }

if __name__ == "__main__":
    import asyncio
    
    async def test_github_handler():
        handler = GitHubCloneToolHandler()
        
        # Test clone
        print("\nTesting clone action...")
        result = await handler.execute({
            "repo_url": "https://github.com/octocat/Hello-World.git"
        })
        print(result.content)
        
        # Test list_directory
        print("\nTesting list_directory action...")
        result = await handler.execute({
            "action": "list_directory"
        })
        print(result.content)
        
        # Test get_repo_info
        print("\nTesting get_repo_info action...")
        result = await handler.execute({
            "action": "get_repo_info"
        })
        print(result.content)
        
        # Test read_file
        print("\nTesting read_file action...")
        result = await handler.execute({
            "action": "read_file",
            "file_path": "README.md"
        })
        print(result.content)
    
    asyncio.run(test_github_handler()) 