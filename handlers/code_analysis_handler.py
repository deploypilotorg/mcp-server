"""
Code analysis handler for analyzing code repositories.
"""

import json
import os
import subprocess
from typing import Any, Dict

from utils.tool_base import BaseHandler, ToolExecution


class CodeAnalysisToolHandler(BaseHandler):
    """Handler for analyzing code repositories"""

    def __init__(self):
        super().__init__()
        self.repo_path = None

    async def execute(self, params: Dict[str, Any]) -> ToolExecution:
        """Analyze code in repositories"""
        action = params.get("action", "")
        self.repo_path = params.get("repo_path", None)

        if not self.repo_path:
            return ToolExecution(
                content="Error: Repository path not provided. Please clone a repository first."
            )

        if not os.path.exists(self.repo_path):
            return ToolExecution(
                content=f"Error: Repository path {self.repo_path} does not exist."
            )

        if action == "analyze_languages":
            return await self._analyze_languages()
        elif action == "find_todos":
            return await self._find_todos()
        elif action == "analyze_complexity":
            return await self._analyze_complexity(params.get("file_path", ""))
        elif action == "search_code":
            return await self._search_code(params.get("query", ""))
        elif action == "get_dependencies":
            return await self._get_dependencies()
        else:
            return ToolExecution(
                content=f"Error: Unknown action '{action}'. Available actions: analyze_languages, find_todos, analyze_complexity, search_code, get_dependencies"
            )

    async def _analyze_languages(self) -> ToolExecution:
        """Analyze language distribution in the repository"""
        try:
            # Dictionary to store language statistics
            language_stats = {}
            extension_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".jsx": "JavaScript (React)",
                ".ts": "TypeScript",
                ".tsx": "TypeScript (React)",
                ".html": "HTML",
                ".css": "CSS",
                ".scss": "SCSS",
                ".java": "Java",
                ".cpp": "C++",
                ".c": "C",
                ".go": "Go",
                ".rs": "Rust",
                ".rb": "Ruby",
                ".php": "PHP",
                ".swift": "Swift",
                ".kt": "Kotlin",
                ".md": "Markdown",
                ".json": "JSON",
                ".yml": "YAML",
                ".yaml": "YAML",
                ".toml": "TOML",
            }

            total_files = 0

            # Walk through the repository
            for root, _, files in os.walk(self.repo_path):
                # Skip .git directory
                if ".git" in root:
                    continue

                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext in extension_map:
                        lang = extension_map[ext]
                        language_stats[lang] = language_stats.get(lang, 0) + 1
                        total_files += 1

            # Sort languages by count
            sorted_stats = dict(
                sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
            )

            # Calculate percentages
            if total_files > 0:
                for lang in sorted_stats:
                    sorted_stats[lang] = {
                        "count": sorted_stats[lang],
                        "percentage": round(
                            (sorted_stats[lang] / total_files) * 100, 2
                        ),
                    }

            # Format the results
            results = ["Language distribution in the repository:"]
            for lang, stats in sorted_stats.items():
                results.append(
                    f"- {lang}: {stats['count']} files ({stats['percentage']}%)"
                )

            if not results[1:]:
                return ToolExecution(
                    content="No recognized programming languages found in the repository."
                )

            return ToolExecution(content="\n".join(results))
        except Exception as e:
            return ToolExecution(content=f"Error analyzing languages: {str(e)}")

    async def _find_todos(self) -> ToolExecution:
        """Find TODO comments in the code"""
        try:
            todo_list = []
            todo_markers = ["TODO", "FIXME", "HACK", "XXX", "BUG", "OPTIMIZE"]

            # Walk through the repository
            for root, _, files in os.walk(self.repo_path):
                # Skip .git directory
                if ".git" in root:
                    continue

                for file in files:
                    # Skip binary files and specific extensions
                    _, ext = os.path.splitext(file)
                    if ext in [".jpg", ".png", ".gif", ".pdf", ".zip", ".tar", ".gz"]:
                        continue

                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)

                    try:
                        with open(
                            file_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            for i, line in enumerate(f, 1):
                                for marker in todo_markers:
                                    if f"{marker}:" in line or f"{marker} " in line:
                                        todo_text = line.strip()
                                        todo_list.append(f"{rel_path}:{i}: {todo_text}")
                    except:
                        # Skip files that can't be read as text
                        continue

            if todo_list:
                result = "TODO comments found in the repository:\n\n" + "\n".join(
                    todo_list
                )
                return ToolExecution(content=result)
            else:
                return ToolExecution(
                    content="No TODO comments found in the repository."
                )
        except Exception as e:
            return ToolExecution(content=f"Error finding TODOs: {str(e)}")

    async def _analyze_complexity(self, file_path: str) -> ToolExecution:
        """Analyze code complexity for Python files"""
        if not file_path:
            return ToolExecution(content="Error: File path not provided")

        full_path = os.path.join(self.repo_path, file_path)

        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return ToolExecution(content=f"Error: File {file_path} does not exist")

        _, ext = os.path.splitext(file_path)
        if ext != ".py":
            return ToolExecution(
                content=f"Error: Complexity analysis is currently only supported for Python files"
            )

        try:
            # Check if the radon module is available
            try:
                subprocess.run(
                    ["pip", "show", "radon"], capture_output=True, check=True
                )
            except subprocess.CalledProcessError:
                return ToolExecution(
                    content="Error: The 'radon' package is not installed. Unable to analyze complexity."
                )

            # Run complexity analysis using radon
            result = subprocess.run(
                ["radon", "cc", "-s", full_path], capture_output=True, text=True
            )

            if result.stdout:
                complexity_report = f"Code complexity analysis for {file_path}:\n\n```\n{result.stdout}\n```"
                return ToolExecution(content=complexity_report)
            else:
                return ToolExecution(
                    content=f"No complexity analysis results for {file_path}. The file might be empty or have very simple functions."
                )
        except Exception as e:
            return ToolExecution(content=f"Error analyzing code complexity: {str(e)}")

    async def _search_code(self, query: str) -> ToolExecution:
        """Search for code patterns in the repository"""
        if not query:
            return ToolExecution(content="Error: Search query not provided")

        try:
            # Use grep to search for the pattern
            result = subprocess.run(
                ["grep", "-r", "--include=*.*", "-n", query, self.repo_path],
                capture_output=True,
                text=True,
            )

            if result.stdout:
                # Format the output to be relative to the repo path
                lines = result.stdout.strip().split("\n")
                formatted_lines = []

                for line in lines:
                    try:
                        file_with_match = line.split(":", 1)[0]
                        rel_path = os.path.relpath(file_with_match, self.repo_path)
                        formatted_line = line.replace(file_with_match, rel_path)
                        formatted_lines.append(formatted_line)
                    except:
                        formatted_lines.append(line)

                search_results = f"Search results for '{query}':\n\n" + "\n".join(
                    formatted_lines[:100]
                )

                if len(lines) > 100:
                    search_results += f"\n\n... and {len(lines) - 100} more matches"

                return ToolExecution(content=search_results)
            else:
                return ToolExecution(
                    content=f"No matches found for '{query}' in the repository"
                )
        except Exception as e:
            return ToolExecution(content=f"Error searching code: {str(e)}")

    async def _get_dependencies(self) -> ToolExecution:
        """Analyze dependencies in the repository"""
        try:
            dependencies = {}

            # Check for Python dependencies
            requirements_files = []
            for root, _, files in os.walk(self.repo_path):
                if "requirements.txt" in files:
                    requirements_files.append(os.path.join(root, "requirements.txt"))
                if "setup.py" in files:
                    requirements_files.append(os.path.join(root, "setup.py"))

            if requirements_files:
                dependencies["python"] = {"files": [], "packages": []}

                for req_file in requirements_files:
                    rel_path = os.path.relpath(req_file, self.repo_path)
                    dependencies["python"]["files"].append(rel_path)

                    if req_file.endswith("requirements.txt"):
                        with open(req_file, "r") as f:
                            lines = f.readlines()
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith("#"):
                                    dependencies["python"]["packages"].append(line)

            # Check for JavaScript dependencies
            package_json_files = []
            for root, _, files in os.walk(self.repo_path):
                if "package.json" in files:
                    package_json_files.append(os.path.join(root, "package.json"))

            if package_json_files:
                dependencies["javascript"] = {
                    "files": [],
                    "packages": {"dependencies": [], "devDependencies": []},
                }

                for pkg_file in package_json_files:
                    rel_path = os.path.relpath(pkg_file, self.repo_path)
                    dependencies["javascript"]["files"].append(rel_path)

                    with open(pkg_file, "r") as f:
                        try:
                            pkg_data = json.load(f)
                            if "dependencies" in pkg_data:
                                for dep, version in pkg_data["dependencies"].items():
                                    dependencies["javascript"]["packages"][
                                        "dependencies"
                                    ].append(f"{dep}@{version}")

                            if "devDependencies" in pkg_data:
                                for dep, version in pkg_data["devDependencies"].items():
                                    dependencies["javascript"]["packages"][
                                        "devDependencies"
                                    ].append(f"{dep}@{version}")
                        except json.JSONDecodeError:
                            pass

            # Format the results
            if not dependencies:
                return ToolExecution(
                    content="No dependency files found in the repository"
                )

            results = ["Dependencies found in the repository:"]

            if "python" in dependencies:
                results.append("\nPython dependencies:")
                for file in dependencies["python"]["files"]:
                    results.append(f"- Found in: {file}")

                if dependencies["python"]["packages"]:
                    results.append("  Packages:")
                    for pkg in dependencies["python"]["packages"][:20]:
                        results.append(f"  - {pkg}")

                    if len(dependencies["python"]["packages"]) > 20:
                        results.append(
                            f"  - ... and {len(dependencies['python']['packages']) - 20} more"
                        )

            if "javascript" in dependencies:
                results.append("\nJavaScript dependencies:")
                for file in dependencies["javascript"]["files"]:
                    results.append(f"- Found in: {file}")

                if dependencies["javascript"]["packages"]["dependencies"]:
                    results.append("  Dependencies:")
                    for pkg in dependencies["javascript"]["packages"]["dependencies"][
                        :20
                    ]:
                        results.append(f"  - {pkg}")

                    if len(dependencies["javascript"]["packages"]["dependencies"]) > 20:
                        results.append(
                            f"  - ... and {len(dependencies['javascript']['packages']['dependencies']) - 20} more"
                        )

                if dependencies["javascript"]["packages"]["devDependencies"]:
                    results.append("  Dev Dependencies:")
                    for pkg in dependencies["javascript"]["packages"][
                        "devDependencies"
                    ][:20]:
                        results.append(f"  - {pkg}")

                    if (
                        len(dependencies["javascript"]["packages"]["devDependencies"])
                        > 20
                    ):
                        results.append(
                            f"  - ... and {len(dependencies['javascript']['packages']['devDependencies']) - 20} more"
                        )

            return ToolExecution(content="\n".join(results))
        except Exception as e:
            return ToolExecution(content=f"Error analyzing dependencies: {str(e)}")


if __name__ == "__main__":
    import asyncio

    async def test_code_analysis_handler():
        handler = CodeAnalysisToolHandler()

        # Test analyze_languages
        print("\nTesting analyze_languages action...")
        result = await handler.execute(
            {"action": "analyze_languages", "repo_path": "."}
        )
        print(result.content)

        # Test find_todos
        print("\nTesting find_todos action...")
        result = await handler.execute({"action": "find_todos", "repo_path": "."})
        print(result.content)

        # Test analyze_complexity
        print("\nTesting analyze_complexity action...")
        result = await handler.execute(
            {
                "action": "analyze_complexity",
                "repo_path": ".",
                "file_path": "handlers/code_analysis_handler.py",
            }
        )
        print(result.content)

        # Test search_code
        print("\nTesting search_code action...")
        result = await handler.execute(
            {"action": "search_code", "repo_path": ".", "query": "class"}
        )
        print(result.content)

        # Test get_dependencies
        print("\nTesting get_dependencies action...")
        result = await handler.execute({"action": "get_dependencies", "repo_path": "."})
        print(result.content)

    asyncio.run(test_code_analysis_handler())
