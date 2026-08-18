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
```

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
9. Confirm AgentLoop tools are visible.

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
   ```

6. Save it to Workspace.
7. Open Copilot Chat.
8. Select `Agent` mode.
9. Confirm AgentLoop tools are visible.

Expected tools:

- list_files
- read_file
- search_in_files
- search_knowledge
- add_finding
- write_report
- review_project
- compare_review_runs

## Resources

AgentLoop exposes these MCP resources:

- `agentloop://project-guide`
- `agentloop://available-workflows`
- `agentloop://code-review-policy`
- `agentloop://current-state`

In VS Code, use `Add Context` → `MCP Resources` to attach them to chat if your VS Code version shows MCP resources.

## Prompts

AgentLoop exposes these MCP prompts:

- `/mcp.agentloop.review_project`
- `/mcp.agentloop.review_file`
- `/mcp.agentloop.answer_policy_question`
- `/mcp.agentloop.write_security_report`

## Product workflow prompt

Paste this into VS Code Copilot Chat in Agent mode:

```text
Use the agentloop MCP server.
Call review_project for ./sample_project with security profile.
Use include_globs **/*.py.
Use max_files 200.
Return the review summary and generated report path.
```

Expected result:

- Copilot asks permission to use the `review_project` MCP tool.
- AgentLoop runs the review workflow.
- `mcp_host_report.md` is generated.
- The report contains concrete findings.

## Manual fallback prompt

Use this only if the host does not call `review_project` correctly:

```text
Use the agentloop MCP server.
Review ./sample_project for security issues.
Use list_files to discover files.
Use read_file to inspect relevant files.
Use search_knowledge to check the security policy.
Use add_finding for every concrete issue.
Use write_report when done.
Return the generated report path.
```

## Real repository workflow prompt

Use the agentloop MCP server.
```text
Call review_project for D:\Projects\SomeRepo with security profile.
Use reviewer openai.
Use model gpt-5.6-luna.
Use allowed_root D:\Projects.
Use include_globs **/*.py.
Use exclude_globs tests/**,__pycache__/**,.venv/**.
Use max_files 200.
Use max_file_size_bytes 200000.
Use reviews_dir D:\Projects\AgentLoop\agent_loop_from_scratch\reviews.
Return the review summary, run directory, HTML report path, and Markdown report path.
```

Expected result:

- AgentLoop reviews only files matching the requested scope.
- Files outside `allowed_root` are rejected.
- Large files and excluded paths are skipped.
- A timestamped report is generated under the requested `report_dir`.
- The response includes selected/skipped file counts, findings count, severity summary, and report path.

## Review run package

When `reviews_dir` is provided, AgentLoop creates a persistent package for every review run.

Example:

```text
reviews/
  history.json
  20260816_174500_123456_sample_project_security_openai/
    report.md
    report.html
    summary.json
    findings.json
    reviewed_files.json
    run_config.json
```    


## Compare review runs

AgentLoop can compare two persisted review run packages.

Example:

```text
Use the agentloop MCP server.

Call compare_review_runs with:
- old_run_dir: D:\Projects\AgentLoop\agent_loop_from_scratch\reviews\<old-run>
- new_run_dir: D:\Projects\AgentLoop\agent_loop_from_scratch\reviews\<new-run>

Return:
- summary
- new findings
- resolved findings
- unchanged findings
- severity changes
- HTML comparison report path
```


## Workspace review

For normal daily use, prefer `review_workspace` instead of configuring every `review_project` option manually.

Python example:

```text
Use the agentloop MCP server.

Call review_workspace with:
- workspace_path: D:\Projects\MyProject
- preset: python-security
- reviewer: openai
- model: gpt-5.6-luna

Return:
- summary
- run_id
- run_dir
- HTML report path
```

AgentLoop automatically applies safe file filters, scope limits, the workspace as the allowed root, and a persistent `reviews` directory inside the workspace.


## Git diff review

Use `review_git_diff` when you want to review only files changed between Git revisions instead of reviewing the entire workspace.

For committed changes:

```text
Use the agentloop MCP server.

Call review_git_diff with:
- repository_path: D:\Projects\MyProject
- base_ref: main
- target_ref: HEAD
- preset: python-security
- reviewer: openai

Return:
- summary
- changed_files_count
- selected_files_count
- skipped_files_count
- findings_count
- run_id
- run_dir
- HTML report path
```

For staged changes:

```text
Use the agentloop MCP server.

Call review_git_diff with:
- repository_path: D:\Projects\MyProject
- staged_only: true
- preset: python-security
- reviewer: deterministic

Return:
- summary
- changed_files_count
- selected_files_count
- skipped_files_count
- findings_count
- run_id
- run_dir
- HTML report path
```

When `staged_only` is true, AgentLoop reviews the Git index snapshot rather than unstaged working-tree content.