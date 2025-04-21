# CodingMCP Protocol Handler

The CodingMCP protocol handler allows Claude to act as a pair programming assistant, inspired by the [ezyang/codemcp](https://github.com/ezyang/codemcp) project. This handler enables Claude to directly manipulate code in a workspace, run commands, execute tests, and create git commits.

## Features

- Initialize a workspace directory
- Read and write files
- List files with glob pattern matching
- Run arbitrary shell commands
- Run tests using configured test commands
- Run formatters using configured format commands
- Create git commits with changes

## Configuration

Before using the CodingMCP protocol, create a `codemcp.toml` file in the root of your workspace with the following format:

```toml
project_prompt = """
Optional instructions for Claude when working with this project.
"""

[commands]
format = ["./run_format.sh"]
test = ["./run_test.sh"]
```

The `project_prompt` is optional and provides specific instructions for Claude when working with your project.

The `commands` section configures commands that Claude can run:
- `format`: Command to run the code formatter
- `test`: Command to run tests (accepts a test selector argument)

## Usage Examples

### Initialize a workspace

```json
{
  "action": "initialize",
  "workspace_path": "/path/to/your/project",
  "auto_init_git": true
}
```

### Read a file

```json
{
  "action": "read_file",
  "file_path": "src/main.py"
}
```

### Write to a file

```json
{
  "action": "write_file",
  "file_path": "src/main.py",
  "content": "# New content\ndef main():\n    print('Hello, world!')\n\nif __name__ == '__main__':\n    main()"
}
```

### List files

```json
{
  "action": "list_files",
  "subdir": "src",
  "pattern": "*.py"
}
```

### Run a command

```json
{
  "action": "run_command",
  "command": "ls -la"
}
```

### Run tests

```json
{
  "action": "run_test",
  "test_selector": "test_specific_function"
}
```

### Run formatter

```json
{
  "action": "run_format"
}
```

### Create a git commit

```json
{
  "action": "git_commit",
  "message": "Implemented new feature"
}
```

## Integration with Claude

To use CodingMCP with Claude, follow these steps:

1. Create a `codemcp.toml` file in your project directory
2. Use the `codingmcp` tool with Claude, passing the appropriate action and parameters
3. Claude will execute the actions and provide feedback

Example conversation:

User: "Can you help me implement a new function in my project?"

Claude: "I'll help you implement that function. First, let me initialize the workspace."

*Claude uses the `codingmcp` tool with `action=initialize`*

Claude: "Now I'll read the file where we need to add the function."

*Claude uses the `codingmcp` tool with `action=read_file`*

Claude: "I'll implement the function now."

*Claude uses the `codingmcp` tool with `action=write_file` to add the new function*

Claude: "Let's run the tests to make sure everything works."

*Claude uses the `codingmcp` tool with `action=run_test`*

Claude: "Great! The tests pass. Let's commit our changes."

*Claude uses the `codingmcp` tool with `action=git_commit`* 