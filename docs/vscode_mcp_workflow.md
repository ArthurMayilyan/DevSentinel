# AgentLoop MCP in VS Code

AgentLoop exposes a local MCP server for VS Code Agent mode.

## Server configuration

Use `.vscode/mcp.json` in the project root.

Example:

```json
{
  "servers": {
    "agentloop": {
      "type": "stdio",
      "command": "C:\\Program Files\\Python311\\python.exe",
      "args": [
        "D:\\Projects\\AgentLoop\\agent_loop_from_scratch\\run_mcp_server.py",
        "--transport",
        "stdio",
        "--knowledge-path",
        "D:\\Projects\\AgentLoop\\agent_loop_from_scratch\\knowledge_base_noisy",
        "--report-path",
        "D:\\Projects\\AgentLoop\\agent_loop_from_scratch\\mcp_host_report.md"
      ],
      "env": {}
    }
  }
}