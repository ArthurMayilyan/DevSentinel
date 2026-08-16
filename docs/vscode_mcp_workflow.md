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

## Add or start server in VS Code

VS Code UI may show either a `Start` action above the server entry or only an `Add Server` button, depending on version and current MCP state.

### Option A — Server already exists in `.vscode/mcp.json`

1. Open the project folder in VS Code.
2. Make sure this file exists: `.vscode/mcp.json`.
3. Open Command Palette.
4. Run `MCP: List Servers`.
5. Select `agentloop`.
6. Start or restart the server if VS Code offers that action.
7. Open Copilot Chat.
8. Select `Agent` mode.
9. Open the tools picker.
10. Confirm AgentLoop tools are visible.

### Option B — VS Code shows only `Add Server`

1. Click `Add Server`.
2. Choose a local command / stdio server.
3. Server name: `agentloop`.
4. Command: `C:\Program Files\Python311\python.exe`.
5. Arguments:

   ```text
   D:\Projects\AgentLoop\agent_loop_from_scratch\run_mcp_server.py
   --transport
   stdio
   --knowledge-path
   D:\Projects\AgentLoop\agent_loop_from_scratch\knowledge_base_noisy
   --report-path
   D:\Projects\AgentLoop\agent_loop_from_scratch\mcp_host_report.md