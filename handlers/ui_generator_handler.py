"""
UI Generator handler for generating and running UIs for applications in repositories.
"""
import os
import sys
import time
import uuid
import json
import fnmatch
import asyncio
import subprocess
import socket
from typing import Dict, Any, List

from utils.tool_base import BaseHandler, ToolExecution

class UIGeneratorToolHandler(BaseHandler):
    """Handler for generating and running UIs for applications"""
    def __init__(self):
        super().__init__()
        self.repo_path = None
        self.repo_name = None
        self.repo_url = None
        self.ui_processes = {}  # Store running UI processes
        
    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Generate and run UI for applications in the repository"""
        action = params.get("action", "")
        
        if not self.repo_path:
            return ToolExecution(content="Error: No repository is currently cloned. Please clone a repository first.")
        
        if not os.path.exists(self.repo_path):
            return ToolExecution(content=f"Error: Repository path {self.repo_path} does not exist.")
        
        if action == "scan_apps":
            return await self._scan_apps()
        elif action == "generate_ui":
            app_path = params.get("app_path", "")
            if not app_path:
                return ToolExecution(content="Error: Application path not provided")
            return await self._generate_ui(app_path)
        elif action == "stop_ui":
            session_id = params.get("session_id", "")
            if not session_id:
                return ToolExecution(content="Error: Session ID not provided")
            return await self._stop_ui(session_id)
        else:
            return ToolExecution(
                content=f"Error: Unknown action '{action}'. Available actions: scan_apps, generate_ui, stop_ui"
            )
    
    async def _scan_apps(self) -> ToolExecution:
        """Scan the repository for app entry points"""
        try:
            app_files = []
            
            # Look for common app entry points
            patterns = [
                "**/*.py",  # Python files
                "**/app.py",
                "**/main.py",
                "**/server.py",
                "**/index.js",
                "**/app.js",
                "**/main.js",
                "**/index.html",
                "**/package.json",
                "**/requirements.txt"
            ]
            
            for pattern in patterns:
                for root, _, files in os.walk(self.repo_path):
                    for filename in files:
                        if fnmatch.fnmatch(filename, pattern.split('/')[-1]):
                            rel_path = os.path.relpath(os.path.join(root, filename), self.repo_path)
                            app_files.append(rel_path)
            
            if not app_files:
                return ToolExecution(content="No potential application entry points found in the repository.")
            
            # Analyze the potential app entry points
            app_info = []
            for file_path in app_files:
                full_path = os.path.join(self.repo_path, file_path)
                file_type = file_path.split('.')[-1] if '.' in file_path else 'unknown'
                
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(2000)  # Read the first 2000 characters for analysis
                    
                    app_type = self._detect_app_type(file_path, content)
                    if app_type:
                        app_info.append({
                            "path": file_path,
                            "type": app_type,
                            "description": self._generate_app_description(file_path, content)
                        })
                except Exception:
                    # Skip files that can't be read
                    continue
            
            if not app_info:
                return ToolExecution(content="No recognizable applications found in the repository.")
            
            # Format the results
            result = "Found potential applications in the repository:\n\n"
            for idx, app in enumerate(app_info, 1):
                result += f"{idx}. {app['path']} ({app['type']})\n"
                result += f"   Description: {app['description']}\n\n"
            
            result += "\nYou can generate and run a UI for any of these applications using the 'generate_ui' action with the app_path parameter."
            return ToolExecution(content=result)
        
        except Exception as e:
            return ToolExecution(content=f"Error scanning for applications: {str(e)}")
    
    async def _generate_ui(self, app_path: str) -> ToolExecution:
        """Generate and run a UI for a specific application"""
        full_path = os.path.join(self.repo_path, app_path)
        if not os.path.exists(full_path):
            return ToolExecution(content=f"Error: Application path '{app_path}' does not exist")
        
        try:
            # Determine the app type and generate appropriate UI
            if app_path.endswith('.py'):
                return await self._run_python_app(app_path)
            elif app_path.endswith('.js'):
                return await self._run_js_app(app_path)
            elif app_path.endswith('.html'):
                return await self._serve_html(app_path)
            else:
                return ToolExecution(content=f"Unsupported application type for {app_path}. Currently supporting .py, .js, and .html files.")
        
        except Exception as e:
            return ToolExecution(content=f"Error generating UI: {str(e)}")
    
    async def _stop_ui(self, session_id: str) -> ToolExecution:
        """Stop a running UI session"""
        if not session_id or session_id not in self.ui_processes:
            return ToolExecution(content="Error: Invalid or unknown session ID")
        
        try:
            process_info = self.ui_processes[session_id]
            process = process_info.get('process')
            
            if process and process.poll() is None:  # Check if still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            del self.ui_processes[session_id]
            return ToolExecution(content=f"UI session {session_id} has been stopped")
        
        except Exception as e:
            return ToolExecution(content=f"Error stopping UI: {str(e)}")
    
    def _detect_app_type(self, file_path: str, content: str) -> str:
        """Detect the type of application"""
        if file_path.endswith('.py'):
            if 'streamlit' in content.lower():
                return 'Streamlit'
            elif 'flask' in content.lower():
                return 'Flask'
            elif 'django' in content.lower():
                return 'Django'
            elif 'fastapi' in content.lower():
                return 'FastAPI'
            return 'Python'
        
        elif file_path.endswith('.js'):
            if 'react' in content.lower():
                return 'React'
            elif 'express' in content.lower():
                return 'Express.js'
            elif 'vue' in content.lower():
                return 'Vue.js'
            return 'JavaScript'
        
        elif file_path.endswith('.html'):
            return 'HTML'
        
        elif file_path == 'package.json':
            return 'Node.js'
        
        elif file_path == 'requirements.txt':
            return 'Python'
        
        return None
    
    def _generate_app_description(self, file_path: str, content: str) -> str:
        """Generate a description for the application"""
        # Extract first non-empty comment lines as potential description
        lines = content.split('\n')
        comment_blocks = []
        current_block = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                # Handle comments
                comment_text = stripped.lstrip('#').lstrip('/').lstrip('*').strip()
                if comment_text:
                    current_block.append(comment_text)
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                # Handle docstrings
                docstring_text = stripped.lstrip('"').lstrip("'").strip()
                if docstring_text:
                    current_block.append(docstring_text)
            elif current_block:
                comment_blocks.append(' '.join(current_block))
                current_block = []
                
        if current_block:
            comment_blocks.append(' '.join(current_block))
        
        if comment_blocks:
            # Use the first substantial comment block as description
            for block in comment_blocks:
                if len(block) > 10:  # Arbitrary threshold for a meaningful comment
                    return block[:200] + "..." if len(block) > 200 else block
        
        # If no good comments, generate a basic description based on file type
        if file_path.endswith('.py'):
            return "Python application"
        elif file_path.endswith('.js'):
            return "JavaScript application"
        elif file_path.endswith('.html'):
            return "HTML application"
        elif file_path == 'package.json':
            return "Node.js application"
        elif file_path == 'requirements.txt':
            return "Python application with dependencies"
        
        return "Application with unknown type"
    
    async def _run_python_app(self, app_path: str) -> ToolExecution:
        """Run a Python application"""
        full_path = os.path.join(self.repo_path, app_path)
        app_dir = os.path.dirname(full_path)
        
        # Check for dependencies
        requirements_path = os.path.join(app_dir, 'requirements.txt')
        has_requirements = os.path.exists(requirements_path)
        
        # Determine the app type
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        port = self._get_available_port()
        session_id = f"ui_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        cmd = []
        app_url = ""
        
        if 'streamlit' in content.lower():
            # Streamlit app
            cmd = [sys.executable, "-m", "streamlit", "run", full_path, "--server.port", str(port)]
            app_url = f"http://localhost:{port}"
        elif 'flask' in content.lower():
            # Flask app
            env = os.environ.copy()
            env["FLASK_APP"] = full_path
            env["FLASK_ENV"] = "development"
            cmd = [sys.executable, "-m", "flask", "run", "--port", str(port)]
            app_url = f"http://localhost:{port}"
        elif 'fastapi' in content.lower():
            # FastAPI app
            cmd = [sys.executable, "-m", "uvicorn", os.path.basename(full_path).replace('.py', ':app'), "--port", str(port)]
            app_url = f"http://localhost:{port}"
        else:
            # Generic Python script
            cmd = [sys.executable, full_path]
            app_url = "No web interface available for this script type"
        
        # Prepare the process
        try:
            if has_requirements:
                # Install dependencies
                install_process = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", requirements_path],
                    capture_output=True,
                    text=True,
                    cwd=app_dir
                )
                
                if install_process.returncode != 0:
                    return ToolExecution(content=f"Error installing dependencies:\n{install_process.stderr}")
            
            # Start the application
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=app_dir
            )
            
            # Store the process
            self.ui_processes[session_id] = {
                'process': process,
                'app_path': app_path,
                'url': app_url,
                'port': port
            }
            
            # Give it some time to start
            await asyncio.sleep(3)
            
            # Check if it's still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return ToolExecution(content=f"Application failed to start:\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
            
            return ToolExecution(content=f"""
UI generated for {app_path}!

Session ID: {session_id}
URL: {app_url}

The application is now running. You can access it at the URL above.
To stop the application, use the 'stop_ui' action with the session ID.
            """.strip())
            
        except Exception as e:
            return ToolExecution(content=f"Error running Python application: {str(e)}")
    
    async def _run_js_app(self, app_path: str) -> ToolExecution:
        """Run a JavaScript application"""
        full_path = os.path.join(self.repo_path, app_path)
        app_dir = os.path.dirname(full_path)
        
        # Check for package.json
        package_json_path = os.path.join(app_dir, 'package.json')
        has_package_json = os.path.exists(package_json_path)
        
        port = self._get_available_port()
        session_id = f"ui_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        try:
            cmd = []
            app_url = ""
            
            if has_package_json:
                # Read package.json to determine application type and start script
                with open(package_json_path, 'r', encoding='utf-8', errors='ignore') as f:
                    package_data = json.load(f)
                
                # Install dependencies
                install_process = subprocess.run(
                    ["npm", "install"],
                    capture_output=True,
                    text=True,
                    cwd=app_dir
                )
                
                if install_process.returncode != 0:
                    return ToolExecution(content=f"Error installing npm dependencies:\n{install_process.stderr}")
                
                # Determine start script
                if 'scripts' in package_data and 'start' in package_data['scripts']:
                    cmd = ["npm", "start"]
                    app_url = f"http://localhost:{port}"  # Assuming standard port, may need adjustment
                else:
                    # Fallback to node
                    cmd = ["node", full_path]
                    app_url = "No web interface directly available for this Node.js script"
            else:
                # Simple Node.js script
                cmd = ["node", full_path]
                app_url = "No web interface directly available for this Node.js script"
            
            # Start the application
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=app_dir
            )
            
            # Store the process
            self.ui_processes[session_id] = {
                'process': process,
                'app_path': app_path,
                'url': app_url,
                'port': port
            }
            
            # Give it some time to start
            await asyncio.sleep(3)
            
            # Check if it's still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return ToolExecution(content=f"Application failed to start:\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
            
            return ToolExecution(content=f"""
UI generated for {app_path}!

Session ID: {session_id}
URL: {app_url}

The application is now running. You can access it at the URL above.
To stop the application, use the 'stop_ui' action with the session ID.
            """.strip())
            
        except Exception as e:
            return ToolExecution(content=f"Error running JavaScript application: {str(e)}")
    
    async def _serve_html(self, app_path: str) -> ToolExecution:
        """Serve an HTML file using a simple HTTP server"""
        full_path = os.path.join(self.repo_path, app_path)
        app_dir = os.path.dirname(full_path)
        
        port = self._get_available_port()
        session_id = f"ui_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Start a simple HTTP server
            cmd = [sys.executable, "-m", "http.server", str(port)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=app_dir
            )
            
            # Store the process
            file_name = os.path.basename(full_path)
            app_url = f"http://localhost:{port}/{file_name}"
            self.ui_processes[session_id] = {
                'process': process,
                'app_path': app_path,
                'url': app_url,
                'port': port
            }
            
            # Give it some time to start
            await asyncio.sleep(2)
            
            # Check if it's still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                return ToolExecution(content=f"Server failed to start:\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}")
            
            return ToolExecution(content=f"""
HTTP server started for {app_path}!

Session ID: {session_id}
URL: {app_url}

The HTML file is now being served. You can access it at the URL above.
To stop the server, use the 'stop_ui' action with the session ID.
            """.strip())
            
        except Exception as e:
            return ToolExecution(content=f"Error serving HTML file: {str(e)}")
    
    def _get_available_port(self) -> int:
        """Get an available port"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]

if __name__ == "__main__":
    import asyncio
    
    async def test_ui_generator_handler():
        handler = UIGeneratorToolHandler()
        
        # Test scan_apps
        print("\nTesting scan_apps action...")
        result = await handler.execute({
            "action": "scan_apps",
            "repo_path": "."
        })
        print(result.content)
        
        # Test generate_ui for Python app
        print("\nTesting generate_ui action for Python app...")
        result = await handler.execute({
            "action": "generate_ui",
            "repo_path": ".",
            "app_path": "handlers/ui_generator_handler.py"
        })
        print(result.content)
        
        # Test generate_ui for HTML app
        print("\nTesting generate_ui action for HTML app...")
        result = await handler.execute({
            "action": "generate_ui",
            "repo_path": ".",
            "app_path": "index.html"
        })
        print(result.content)
        
        # Test stop_ui
        print("\nTesting stop_ui action...")
        result = await handler.execute({
            "action": "stop_ui",
            "session_id": "test_session"
        })
        print(result.content)
    
    asyncio.run(test_ui_generator_handler()) 