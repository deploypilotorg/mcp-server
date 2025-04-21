"""
Autodeploy handler for deploying code repositories.
"""
import os
import subprocess
import json
import tempfile
import shutil
import asyncio
from typing import Dict, Any, Optional, List

from utils.tool_base import BaseHandler, ToolExecution

class AutoDeployToolHandler(BaseHandler):
    """Handler for automatically deploying code repositories"""
    def __init__(self):
        super().__init__()
        self.repo_path = None
        self.deploy_config = None
        self.deploy_status = {
            "current_deployment": None,
            "history": []
        }

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Manage deployment operations"""
        action = params.get("action", "")
        self.repo_path = params.get("repo_path", None)
        
        if not self.repo_path and action != "get_status" and action != "abort_deployment":
            return ToolExecution(content="Error: Repository path not provided. Please clone a repository first.")
        
        if not os.path.exists(self.repo_path) and action != "get_status" and action != "abort_deployment":
            return ToolExecution(content=f"Error: Repository path {self.repo_path} does not exist.")
        
        if action == "prepare_deployment":
            return await self._prepare_deployment(params.get("deploy_config", {}))
        elif action == "start_deployment":
            return await self._start_deployment()
        elif action == "get_status":
            return await self._get_deployment_status()
        elif action == "abort_deployment":
            return await self._abort_deployment()
        elif action == "detect_deployment_type":
            return await self._detect_deployment_type()
        else:
            return ToolExecution(
                content=f"Error: Unknown action '{action}'. Available actions: prepare_deployment, start_deployment, get_status, abort_deployment, detect_deployment_type"
            )
    
    async def _prepare_deployment(self, deploy_config: Dict[str, Any]) -> ToolExecution:
        """Prepare for deployment by validating config and checking prerequisites"""
        if not deploy_config:
            return ToolExecution(content="Error: Deployment configuration not provided")
        
        try:
            # Save the deploy config
            self.deploy_config = deploy_config
            
            # Get deployment type
            deploy_type = deploy_config.get("type", "")
            if not deploy_type:
                return ToolExecution(content="Error: Deployment type not specified in configuration")
            
            # Check for required configuration based on type
            if deploy_type == "static":
                # Static website deployment
                build_dir = deploy_config.get("build_dir", "")
                if not build_dir:
                    return ToolExecution(content="Error: Build directory not specified for static deployment")
                
                build_command = deploy_config.get("build_command", "")
                if not build_command:
                    return ToolExecution(content="Error: Build command not specified for static deployment")
                
                deploy_target = deploy_config.get("deploy_target", "")
                if not deploy_target:
                    return ToolExecution(content="Error: Deploy target not specified for static deployment")
                
                # Check if build directory exists
                build_path = os.path.join(self.repo_path, build_dir)
                if not os.path.exists(build_path) and not deploy_config.get("create_if_missing", False):
                    return ToolExecution(content=f"Error: Build directory '{build_dir}' does not exist. Set 'create_if_missing' to true if you want it to be created.")
            
            elif deploy_type == "docker":
                # Docker deployment
                dockerfile_path = deploy_config.get("dockerfile_path", "Dockerfile")
                image_name = deploy_config.get("image_name", "")
                
                if not image_name:
                    return ToolExecution(content="Error: Docker image name not specified")
                
                # Check if Dockerfile exists
                full_dockerfile_path = os.path.join(self.repo_path, dockerfile_path)
                if not os.path.exists(full_dockerfile_path):
                    return ToolExecution(content=f"Error: Dockerfile not found at '{dockerfile_path}'")
                
                # Check if Docker is installed
                try:
                    result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
                    if result.returncode != 0:
                        return ToolExecution(content="Error: Docker is not installed or not accessible")
                except FileNotFoundError:
                    return ToolExecution(content="Error: Docker is not installed or not in PATH")
            
            elif deploy_type == "heroku":
                # Heroku deployment
                app_name = deploy_config.get("app_name", "")
                if not app_name:
                    return ToolExecution(content="Error: Heroku app name not specified")
                
                # Check if Heroku CLI is installed
                try:
                    result = subprocess.run(["heroku", "--version"], capture_output=True, text=True)
                    if result.returncode != 0:
                        return ToolExecution(content="Error: Heroku CLI is not installed or not accessible")
                except FileNotFoundError:
                    return ToolExecution(content="Error: Heroku CLI is not installed or not in PATH")
                
                # Check for Heroku authentication
                try:
                    result = subprocess.run(["heroku", "auth:whoami"], capture_output=True, text=True)
                    if result.returncode != 0:
                        return ToolExecution(content="Error: Not authenticated with Heroku. Please run 'heroku login' first.")
                except subprocess.CalledProcessError:
                    return ToolExecution(content="Error: Not authenticated with Heroku. Please run 'heroku login' first.")
            
            elif deploy_type == "custom":
                # Custom deployment
                script_path = deploy_config.get("script_path", "")
                if not script_path:
                    return ToolExecution(content="Error: Script path not specified for custom deployment")
                
                # Check if script exists
                full_script_path = os.path.join(self.repo_path, script_path)
                if not os.path.exists(full_script_path):
                    return ToolExecution(content=f"Error: Script not found at '{script_path}'")
                
                # Check if script is executable
                if not os.access(full_script_path, os.X_OK):
                    return ToolExecution(content=f"Warning: Script '{script_path}' is not executable. Will attempt to run with interpreter.")
            
            else:
                return ToolExecution(content=f"Error: Unsupported deployment type '{deploy_type}'. Supported types: static, docker, heroku, custom")
            
            # Update deployment status
            self.deploy_status["current_deployment"] = {
                "status": "prepared",
                "type": deploy_type,
                "config": deploy_config,
                "log": ["Deployment preparation complete"]
            }
            
            return ToolExecution(content=f"Deployment preparation successful. Type: {deploy_type}. Ready to start deployment.")
        except Exception as e:
            return ToolExecution(content=f"Error preparing deployment: {str(e)}")
    
    async def _start_deployment(self) -> ToolExecution:
        """Start the deployment process"""
        if not self.deploy_config:
            return ToolExecution(content="Error: No deployment configuration. Please run prepare_deployment first.")
        
        if not self.deploy_status.get("current_deployment"):
            return ToolExecution(content="Error: No deployment prepared. Please run prepare_deployment first.")
        
        current_deployment = self.deploy_status["current_deployment"]
        if current_deployment["status"] != "prepared":
            return ToolExecution(content=f"Error: Deployment is in '{current_deployment['status']}' state, not 'prepared'. Cannot start.")
        
        try:
            # Update deployment status
            current_deployment["status"] = "in_progress"
            current_deployment["log"].append("Starting deployment...")
            
            # Get deployment type
            deploy_type = current_deployment["type"]
            deploy_config = current_deployment["config"]
            
            # Execute deployment based on type
            if deploy_type == "static":
                result = await self._deploy_static(deploy_config)
            elif deploy_type == "docker":
                result = await self._deploy_docker(deploy_config)
            elif deploy_type == "heroku":
                result = await self._deploy_heroku(deploy_config)
            elif deploy_type == "custom":
                result = await self._deploy_custom(deploy_config)
            else:
                current_deployment["status"] = "failed"
                current_deployment["log"].append(f"Error: Unsupported deployment type '{deploy_type}'")
                return ToolExecution(content=f"Error: Unsupported deployment type '{deploy_type}'")
            
            # Update deployment status based on result
            if result["success"]:
                current_deployment["status"] = "completed"
                current_deployment["log"].append("Deployment completed successfully")
                
                # Move current deployment to history
                self.deploy_status["history"].append(current_deployment)
                self.deploy_status["current_deployment"] = None
                
                return ToolExecution(content=f"Deployment successful!\n\n{result.get('message', '')}")
            else:
                current_deployment["status"] = "failed"
                current_deployment["log"].append(f"Deployment failed: {result.get('message', '')}")
                return ToolExecution(content=f"Deployment failed: {result.get('message', '')}")
        except Exception as e:
            # Update deployment status
            if current_deployment:
                current_deployment["status"] = "failed"
                current_deployment["log"].append(f"Deployment failed with exception: {str(e)}")
            
            return ToolExecution(content=f"Error during deployment: {str(e)}")
    
    async def _get_deployment_status(self) -> ToolExecution:
        """Get the current deployment status"""
        try:
            if not self.deploy_status.get("current_deployment") and not self.deploy_status.get("history"):
                return ToolExecution(content="No deployments have been initiated yet.")
            
            status_info = ["Deployment Status:"]
            
            # Current deployment
            current = self.deploy_status.get("current_deployment")
            if current:
                status_info.append(f"\nCurrent Deployment:")
                status_info.append(f"- Status: {current['status']}")
                status_info.append(f"- Type: {current['type']}")
                
                # Add configuration summary
                config = current.get("config", {})
                status_info.append("- Configuration:")
                for key, value in config.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        continue  # Skip complex values
                    status_info.append(f"  - {key}: {value}")
                
                # Add deployment logs
                logs = current.get("log", [])
                if logs:
                    status_info.append("- Logs:")
                    for log in logs[-10:]:  # Show last 10 log entries
                        status_info.append(f"  - {log}")
                    
                    if len(logs) > 10:
                        status_info.append(f"  - ... and {len(logs) - 10} more log entries")
            
            # Deployment history
            history = self.deploy_status.get("history", [])
            if history:
                status_info.append(f"\nDeployment History:")
                for i, deployment in enumerate(history[-5:]):  # Show last 5 deployments
                    status_info.append(f"- Deployment {len(history) - i}:")
                    status_info.append(f"  - Status: {deployment['status']}")
                    status_info.append(f"  - Type: {deployment['type']}")
                
                if len(history) > 5:
                    status_info.append(f"  ... and {len(history) - 5} more past deployments")
            
            return ToolExecution(content="\n".join(status_info))
        except Exception as e:
            return ToolExecution(content=f"Error retrieving deployment status: {str(e)}")
    
    async def _abort_deployment(self) -> ToolExecution:
        """Abort the current deployment"""
        try:
            current_deployment = self.deploy_status.get("current_deployment")
            if not current_deployment:
                return ToolExecution(content="No active deployment to abort.")
            
            if current_deployment["status"] != "in_progress":
                return ToolExecution(content=f"Deployment is in '{current_deployment['status']}' state, not 'in_progress'. Cannot abort.")
            
            # Update deployment status
            current_deployment["status"] = "aborted"
            current_deployment["log"].append("Deployment aborted by user")
            
            # Move to history
            self.deploy_status["history"].append(current_deployment)
            self.deploy_status["current_deployment"] = None
            
            return ToolExecution(content="Deployment aborted successfully.")
        except Exception as e:
            return ToolExecution(content=f"Error aborting deployment: {str(e)}")
    
    async def _detect_deployment_type(self) -> ToolExecution:
        """Detect the type of application in the repository for deployment"""
        try:
            # Check for common framework signatures
            framework_indicators = []
            
            # Look for files that indicate the type of project
            files = os.listdir(self.repo_path)
            
            # Frontend
            if "package.json" in files:
                with open(os.path.join(self.repo_path, "package.json"), 'r') as f:
                    pkg_data = json.load(f)
                    dependencies = pkg_data.get("dependencies", {})
                    
                    if "react" in dependencies:
                        framework_indicators.append("React")
                    if "vue" in dependencies:
                        framework_indicators.append("Vue.js")
                    if "next" in dependencies:
                        framework_indicators.append("Next.js")
                    if "gatsby" in dependencies:
                        framework_indicators.append("Gatsby")
                    if "angular" in dependencies or "@angular/core" in dependencies:
                        framework_indicators.append("Angular")
            
            # Backend
            if "requirements.txt" in files:
                with open(os.path.join(self.repo_path, "requirements.txt"), 'r') as f:
                    content = f.read()
                    if "django" in content.lower():
                        framework_indicators.append("Django")
                    if "flask" in content.lower():
                        framework_indicators.append("Flask")
                    if "fastapi" in content.lower():
                        framework_indicators.append("FastAPI")
            
            # Docker
            if "Dockerfile" in files or "docker-compose.yml" in files:
                framework_indicators.append("Docker")
            
            # Node.js
            if "server.js" in files or "app.js" in files:
                framework_indicators.append("Node.js")
            
            # Look for common build directories
            build_dirs = []
            for item in ["build", "dist", "public", "out", "static"]:
                if os.path.exists(os.path.join(self.repo_path, item)) and os.path.isdir(os.path.join(self.repo_path, item)):
                    build_dirs.append(item)
            
            # Determine deployment type
            recommended_config = {}
            
            if "Docker" in framework_indicators:
                # Docker deployment
                recommended_config = {
                    "type": "docker",
                    "dockerfile_path": "Dockerfile" if "Dockerfile" in files else "docker/Dockerfile",
                    "image_name": os.path.basename(self.repo_path).lower(),
                    "container_name": f"{os.path.basename(self.repo_path).lower()}-container",
                    "ports": ["8080:80"]
                }
            elif any(f in framework_indicators for f in ["React", "Vue.js", "Angular", "Next.js", "Gatsby"]):
                # Static website deployment
                build_command = ""
                build_dir = ""
                
                # Determine build command and directory
                if "React" in framework_indicators or "Vue.js" in framework_indicators or "Angular" in framework_indicators:
                    build_command = "npm run build"
                    build_dir = "build" if "build" in build_dirs else "dist"
                elif "Next.js" in framework_indicators:
                    build_command = "npm run build"
                    build_dir = "out" if "out" in build_dirs else ".next"
                elif "Gatsby" in framework_indicators:
                    build_command = "gatsby build"
                    build_dir = "public"
                
                recommended_config = {
                    "type": "static",
                    "build_command": build_command,
                    "build_dir": build_dir,
                    "deploy_target": "/var/www/html",
                    "create_if_missing": True
                }
            elif any(f in framework_indicators for f in ["Django", "Flask", "FastAPI"]):
                # Python web app deployment
                recommended_config = {
                    "type": "custom",
                    "script_path": "deploy.sh",
                    "requirements": "requirements.txt",
                    "wsgi_app": "app:app" if "Flask" in framework_indicators or "FastAPI" in framework_indicators else "project.wsgi:application"
                }
            elif "Node.js" in framework_indicators:
                # Node.js app deployment
                recommended_config = {
                    "type": "custom",
                    "script_path": "deploy.sh",
                    "start_command": "npm start",
                    "env_file": ".env"
                }
            else:
                # Generic/custom deployment
                return ToolExecution(content="Could not determine specific deployment type. Please specify deployment configuration manually.")
            
            # Format the output
            framework_str = ", ".join(framework_indicators)
            config_str = json.dumps(recommended_config, indent=2)
            
            return ToolExecution(content=f"Detected frameworks/technologies: {framework_str}\n\nRecommended deployment configuration:\n```json\n{config_str}\n```\n\nUse this configuration with the 'prepare_deployment' action to set up deployment.")
        except Exception as e:
            return ToolExecution(content=f"Error detecting deployment type: {str(e)}")
    
    async def _deploy_static(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a static website"""
        build_dir = config.get("build_dir", "")
        build_command = config.get("build_command", "")
        deploy_target = config.get("deploy_target", "")
        
        try:
            # Run build command if specified
            if build_command:
                current_dir = os.getcwd()
                os.chdir(self.repo_path)
                
                self.deploy_status["current_deployment"]["log"].append(f"Running build command: {build_command}")
                
                process = await asyncio.create_subprocess_shell(
                    build_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                # Log the output
                if stdout:
                    stdout_str = stdout.decode()
                    self.deploy_status["current_deployment"]["log"].append(f"Build output: {stdout_str[:500]}...")
                
                if stderr:
                    stderr_str = stderr.decode()
                    self.deploy_status["current_deployment"]["log"].append(f"Build errors: {stderr_str}")
                
                if process.returncode != 0:
                    os.chdir(current_dir)
                    return {"success": False, "message": f"Build command failed with exit code {process.returncode}"}
                
                os.chdir(current_dir)
            
            # Create build directory if it doesn't exist
            build_path = os.path.join(self.repo_path, build_dir)
            if not os.path.exists(build_path) and config.get("create_if_missing", False):
                os.makedirs(build_path)
            
            # Validate build directory
            if not os.path.exists(build_path):
                return {"success": False, "message": f"Build directory '{build_dir}' does not exist"}
            
            # Deploy to target
            self.deploy_status["current_deployment"]["log"].append(f"Deploying to {deploy_target}")
            
            # Simulate copying files (in a real environment, you'd use rsync or similar)
            # For safety, we'll just log the action
            files_to_deploy = []
            for root, _, files in os.walk(build_path):
                rel_path = os.path.relpath(root, build_path)
                for file in files:
                    src_path = os.path.join(root, file)
                    if rel_path == ".":
                        dest_path = os.path.join(deploy_target, file)
                    else:
                        dest_path = os.path.join(deploy_target, rel_path, file)
                    files_to_deploy.append((src_path, dest_path))
            
            self.deploy_status["current_deployment"]["log"].append(f"Would deploy {len(files_to_deploy)} files from {build_dir} to {deploy_target}")
            
            return {
                "success": True, 
                "message": f"Static deployment simulation successful.\n\nWould deploy {len(files_to_deploy)} files from '{build_dir}' to '{deploy_target}'.\n\nIn a production environment, use this command to actually copy files:\nrsync -av {build_path}/ {deploy_target}/"
            }
        except Exception as e:
            return {"success": False, "message": f"Static deployment failed: {str(e)}"}
    
    async def _deploy_docker(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy using Docker"""
        dockerfile_path = config.get("dockerfile_path", "Dockerfile")
        image_name = config.get("image_name", "")
        container_name = config.get("container_name", f"{image_name}-container")
        ports = config.get("ports", [])
        
        try:
            current_dir = os.getcwd()
            os.chdir(self.repo_path)
            
            # Build Docker image
            self.deploy_status["current_deployment"]["log"].append(f"Building Docker image: {image_name}")
            
            build_cmd = f"docker build -t {image_name} -f {dockerfile_path} ."
            self.deploy_status["current_deployment"]["log"].append(f"Running: {build_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                build_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Log the output
            if stdout:
                stdout_str = stdout.decode()
                self.deploy_status["current_deployment"]["log"].append(f"Build output: {stdout_str[:500]}...")
            
            if stderr:
                stderr_str = stderr.decode()
                self.deploy_status["current_deployment"]["log"].append(f"Build errors: {stderr_str}")
            
            if process.returncode != 0:
                os.chdir(current_dir)
                return {"success": False, "message": f"Docker build failed with exit code {process.returncode}"}
            
            # Start container (for simulation, we won't actually run it)
            port_mappings = " ".join([f"-p {p}" for p in ports])
            run_cmd = f"docker run -d --name {container_name} {port_mappings} {image_name}"
            
            self.deploy_status["current_deployment"]["log"].append(f"Would start container with: {run_cmd}")
            
            os.chdir(current_dir)
            
            return {
                "success": True, 
                "message": f"Docker deployment simulation successful.\n\nDocker image '{image_name}' built successfully.\n\nIn a production environment, use this command to run the container:\n{run_cmd}"
            }
        except Exception as e:
            # Restore directory
            if 'current_dir' in locals():
                os.chdir(current_dir)
                
            return {"success": False, "message": f"Docker deployment failed: {str(e)}"}
    
    async def _deploy_heroku(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy to Heroku"""
        app_name = config.get("app_name", "")
        
        try:
            current_dir = os.getcwd()
            os.chdir(self.repo_path)
            
            # Check if the app exists
            self.deploy_status["current_deployment"]["log"].append(f"Checking Heroku app: {app_name}")
            
            check_app_cmd = f"heroku apps:info --app {app_name}"
            self.deploy_status["current_deployment"]["log"].append(f"Running: {check_app_cmd}")
            
            process = await asyncio.create_subprocess_shell(
                check_app_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            app_exists = process.returncode == 0
            
            # Create app if it doesn't exist
            if not app_exists and config.get("create_if_missing", False):
                create_app_cmd = f"heroku apps:create {app_name}"
                self.deploy_status["current_deployment"]["log"].append(f"Creating Heroku app: {create_app_cmd}")
                
                process = await asyncio.create_subprocess_shell(
                    create_app_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    os.chdir(current_dir)
                    stderr_str = stderr.decode() if stderr else "Unknown error"
                    return {"success": False, "message": f"Failed to create Heroku app: {stderr_str}"}
            elif not app_exists:
                os.chdir(current_dir)
                return {"success": False, "message": f"Heroku app '{app_name}' does not exist. Set 'create_if_missing' to true to create it automatically."}
            
            # Check if git remote exists
            check_remote_cmd = "git remote -v"
            process = await asyncio.create_subprocess_shell(
                check_remote_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            remote_exists = f"heroku\t" in stdout.decode() if stdout else False
            
            # Add git remote if it doesn't exist
            if not remote_exists:
                add_remote_cmd = f"heroku git:remote -a {app_name}"
                self.deploy_status["current_deployment"]["log"].append(f"Adding git remote: {add_remote_cmd}")
                
                process = await asyncio.create_subprocess_shell(
                    add_remote_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    os.chdir(current_dir)
                    stderr_str = stderr.decode() if stderr else "Unknown error"
                    return {"success": False, "message": f"Failed to add Heroku git remote: {stderr_str}"}
            
            # Push to Heroku (simulation)
            push_cmd = "git push heroku master"
            self.deploy_status["current_deployment"]["log"].append(f"Would push to Heroku with: {push_cmd}")
            
            os.chdir(current_dir)
            
            return {
                "success": True, 
                "message": f"Heroku deployment simulation successful.\n\nHeroku app '{app_name}' is ready for deployment.\n\nIn a production environment, use this command to deploy:\n{push_cmd}"
            }
        except Exception as e:
            # Restore directory
            if 'current_dir' in locals():
                os.chdir(current_dir)
                
            return {"success": False, "message": f"Heroku deployment failed: {str(e)}"}
    
    async def _deploy_custom(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a custom deployment script"""
        script_path = config.get("script_path", "")
        
        try:
            full_script_path = os.path.join(self.repo_path, script_path)
            
            # Check if script exists
            if not os.path.exists(full_script_path):
                return {"success": False, "message": f"Script not found at '{script_path}'"}
            
            current_dir = os.getcwd()
            os.chdir(self.repo_path)
            
            # Run the script
            self.deploy_status["current_deployment"]["log"].append(f"Running custom deployment script: {script_path}")
            
            # Determine how to run the script
            if os.access(full_script_path, os.X_OK):
                # Script is executable
                cmd = f"./{script_path}"
            else:
                # Determine script type
                if script_path.endswith(".py"):
                    cmd = f"python {script_path}"
                elif script_path.endswith(".sh"):
                    cmd = f"bash {script_path}"
                elif script_path.endswith(".js"):
                    cmd = f"node {script_path}"
                else:
                    # Default to bash
                    cmd = f"bash {script_path}"
            
            # Add any arguments
            if "args" in config:
                args = config["args"]
                if isinstance(args, list):
                    args_str = " ".join(args)
                    cmd = f"{cmd} {args_str}"
            
            self.deploy_status["current_deployment"]["log"].append(f"Running: {cmd}")
            
            # Simulate running the script
            self.deploy_status["current_deployment"]["log"].append(f"Would execute: {cmd} in {self.repo_path}")
            
            os.chdir(current_dir)
            
            return {
                "success": True, 
                "message": f"Custom deployment simulation successful.\n\nWould execute:\n{cmd}\n\nIn directory: {self.repo_path}"
            }
        except Exception as e:
            # Restore directory
            if 'current_dir' in locals():
                os.chdir(current_dir)
                
            return {"success": False, "message": f"Custom deployment failed: {str(e)}"}

if __name__ == "__main__":
    import asyncio
    
    async def test_autodeploy_handler():
        handler = AutoDeployToolHandler()
        
        # Test detect_deployment_type
        print("\nTesting detect_deployment_type action...")
        result = await handler.execute({
            "action": "detect_deployment_type",
            "repo_path": "."
        })
        print(result.content)
        
        # Test prepare_deployment
        print("\nTesting prepare_deployment action...")
        result = await handler.execute({
            "action": "prepare_deployment",
            "repo_path": ".",
            "deploy_config": {
                "type": "static",
                "target": "local"
            }
        })
        print(result.content)
        
        # Test get_status
        print("\nTesting get_status action...")
        result = await handler.execute({
            "action": "get_status"
        })
        print(result.content)
        
        # Test start_deployment
        print("\nTesting start_deployment action...")
        result = await handler.execute({
            "action": "start_deployment"
        })
        print(result.content)
        
        # Test abort_deployment
        print("\nTesting abort_deployment action...")
        result = await handler.execute({
            "action": "abort_deployment"
        })
        print(result.content)
    
    asyncio.run(test_autodeploy_handler()) 