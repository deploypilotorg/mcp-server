"""
GitHub repository handler for cloning and analyzing repositories.
"""
import os
import shutil
import tempfile
import subprocess
from typing import Dict, Any

from utils.tool_base import BaseHandler, ToolExecution

class GitHubRepoToolHandler(BaseHandler):
    """Handler for GitHub repository operations"""
    def __init__(self):
        super().__init__()
        # Initialize repo info
        self.repo_path = None
        self.repo_name = None
        self.repo_url = None

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Clone and analyze GitHub repositories"""
        action = params.get("action", "")
        
        if action == "clone":
            # Clone a repository
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
        
        elif action == "list_files":
            # List files in the repository
            if not self.repo_path:
                return ToolExecution(content="Error: No repository is currently cloned")
            
            path = params.get("path", "")
            full_path = os.path.join(self.repo_path, path) if path else self.repo_path
            
            if not os.path.exists(full_path):
                return ToolExecution(content=f"Error: Path {path} does not exist in the repository")
            
            try:
                file_list = []
                for root, dirs, files in os.walk(full_path):
                    rel_path = os.path.relpath(root, self.repo_path)
                    rel_path = "" if rel_path == "." else rel_path
                    
                    for dir_name in dirs:
                        file_list.append(f"📁 {os.path.join(rel_path, dir_name)}")
                    
                    for file_name in files:
                        file_list.append(f"📄 {os.path.join(rel_path, file_name)}")
                
                file_list_str = "\n".join(file_list)
                return ToolExecution(content=f"Files in repository {self.repo_name}:\n\n{file_list_str}")
            except Exception as e:
                return ToolExecution(content=f"Error listing files: {str(e)}")
        
        elif action == "read_file":
            # Read the contents of a file
            if not self.repo_path:
                return ToolExecution(content="Error: No repository is currently cloned")
            
            file_path = params.get("file_path", "")
            if not file_path:
                return ToolExecution(content="Error: File path not provided")
            
            full_path = os.path.join(self.repo_path, file_path)
            
            if not os.path.exists(full_path) or not os.path.isfile(full_path):
                return ToolExecution(content=f"Error: File {file_path} does not exist in the repository")
            
            try:
                with open(full_path, 'r') as f:
                    file_content = f.read()
                
                return ToolExecution(content=f"Contents of {file_path}:\n\n```\n{file_content}\n```")
            except Exception as e:
                return ToolExecution(content=f"Error reading file: {str(e)}")
        
        elif action == "get_repo_info":
            # Get information about the repository
            if not self.repo_path:
                return ToolExecution(content="Error: No repository is currently cloned")
            
            try:
                # Get the size of the repository
                total_size = 0
                file_count = 0
                for root, dirs, files in os.walk(self.repo_path):
                    file_count += len(files)
                    total_size += sum(os.path.getsize(os.path.join(root, name)) for name in files)
                
                size_kb = total_size / 1024
                size_mb = size_kb / 1024
                
                # Get information about the repository
                current_dir = os.getcwd()
                os.chdir(self.repo_path)
                
                # Get the current branch
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"], 
                    capture_output=True, 
                    text=True
                )
                current_branch = branch_result.stdout.strip()
                
                # Get the last commit
                last_commit_result = subprocess.run(
                    ["git", "log", "-1", "--pretty=format:%h - %s (%cr)"], 
                    capture_output=True, 
                    text=True
                )
                last_commit = last_commit_result.stdout.strip()
                
                # Change back to the original directory
                os.chdir(current_dir)
                
                repo_info = {
                    "name": self.repo_name,
                    "url": self.repo_url,
                    "branch": current_branch,
                    "last_commit": last_commit,
                    "file_count": file_count,
                    "size": f"{size_mb:.2f} MB ({size_kb:.2f} KB)"
                }
                
                info_str = "\n".join([f"{key}: {value}" for key, value in repo_info.items()])
                return ToolExecution(content=f"Repository Information:\n\n{info_str}")
            except Exception as e:
                return ToolExecution(content=f"Error getting repository information: {str(e)}")
        
        else:
            return ToolExecution(content=f"Error: Unknown action '{action}'. Available actions: clone, list_files, read_file, get_repo_info") 