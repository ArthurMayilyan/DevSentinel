# DevSentinel

DevSentinel is a local AI-assisted engineering review platform built to use agentic engineering to control source code security.

It combines:

- a custom tool-using agent loop with guardrails and structured outputs;
- deterministic and OpenAI-based code reviewers;
- RAG-backed knowledge retrieval with provenance and evaluation;
- workspace, Git-diff, and staged-code review workflows;
- MCP integration for VS Code / Copilot Agent mode;
- persistent review artifacts, history, and run comparison;
- centralized runtime configuration;
- a lightweight local Web UI.

The project is best described as an **engineering-grade / production-oriented prototype**.

---

## 1. Main use cases

DevSentinel currently supports four practical workflows:

1. **Workspace review** — review a project directory using a review preset.
2. **Git diff review** — review only files changed between Git revisions.
3. **Staged review** — review exactly the files/content staged in the Git index.
4. **Knowledge search / RAG QA** — retrieve security or other policy evidence from a local knowledge base.

For daily engineering work, prefer **Git diff** or **staged review** over a full workspace review.

---

## 2. Project location used in the examples

The examples below assume:

```text
D:\Projects\DevSentinel\
```

Run shell commands from the project root unless noted otherwise.

---

## 3. Runtime requirements

The project has been developed and tested with Python 3.11.

Example Python executable used by the VS Code MCP configuration:

```text
C:\Program Files\Python311\python.exe
```

Use the existing project environment/dependency setup for the checkout.

Before using DevSentinel, verify the environment:

```powershell
python --version
python -m pytest -q
```

The project also includes a combined CI/evaluation check:

```powershell
python scripts/run_ci_checks.py
```

A healthy run should finish with the pytest suite passing and the eval suite reporting:

```text
overall: passed
retrieval: passed
answer: passed
grounding: passed
agent: passed
```

---

## 4. OpenAI configuration

OpenAI-backed workflows require an API key.

Create a local `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your-key-here
```

Do **not** commit `.env`.

The project loads non-secret runtime settings from:

```text
agentloop.toml
```

Secrets such as `OPENAI_API_KEY` stay outside TOML.

### Configuration precedence

AgentLoop follows this general precedence:

```text
1. Explicit CLI / MCP argument
2. Environment variable
3. agentloop.toml
4. Built-in fallback
```

Important configuration areas include:

```toml
[openai]
model = "gpt-5.6-luna"
max_output_tokens = 500
request_timeout_seconds = 30.0
review_max_content_chars = 12000

[runtime]
agent_mode_max_steps = 4
command_timeout_seconds = 120.0

[agent]
max_steps = 8
max_rejected_final_answers = 3
max_rejected_tool_calls = 5
max_invalid_llm_outputs = 3

[review]
default_reviewer = "deterministic"
max_findings = 5
max_files = 200
max_file_size_bytes = 200000

[rag]
top_k = 3
chunk_max_chars = 1000
chunk_overlap_chars = 100
agent_max_steps = 4
retrieval_strategy = "default"

[artifacts]
default_report_path = "report.md"
reviews_dir_name = "reviews"
comparisons_dir_name = "comparisons"
```

The repository's actual `agentloop.toml` is authoritative.

---

## 5. Security knowledge base

The production-oriented security knowledge base is located at:

```text
knowledge_base\security
```

It contains review guidance covering:

- evidence and false-positive handling;
- secrets and credentials;
- authentication, sessions, and security tokens;
- authorization and access control;
- injection, path traversal, SSRF, and file safety;
- API security, sensitive data, and cryptography;
- supply chain, configuration, logging, and error handling;
- AI / LLM / tool security.

The security profile uses multiple knowledge queries so the OpenAI reviewer can retrieve context across these areas.

### Important behavior

The knowledge base mainly improves the **contextual/OpenAI reviewer**.

The deterministic reviewer remains pattern-based and may still produce lexical false positives, especially when reviewing:

- security detector code;
- fixtures and intentionally vulnerable sample code;
- code containing words such as `SECRET_KEY`, `DEBUG`, `admin`, or `token`;
- RAG/tokenization code where `token` does not mean an authentication token.

---

# 6. Recommended way to use DevSentinel: Web UI

Start the local UI with the security knowledge base:

```powershell
python web_ui.py --knowledge-path ".\knowledge_base\security"
```

The browser should open automatically at:

```text
http://127.0.0.1:8765/
```

To avoid opening the browser automatically:

```powershell
python web_ui.py --knowledge-path ".\knowledge_base\security" --no-browser
```

Use another port if needed:

```powershell
python web_ui.py --knowledge-path ".\knowledge_base\security" --port 8766
```

## Workspace review

In the UI:

```text
Repository / Workspace:
D:\Projects\DevSentinel\

Review mode:
Workspace

Preset:
python-security

Reviewer:
deterministic
```

For contextual review:

```text
Reviewer:
openai
```

The result page shows reviewed/selected files, skipped files, finding count, run ID, run directory, and a link to the HTML report.

## Git diff review

Example:

```text
Review mode: Git diff
Base ref: main
Target ref: dev
Preset: python-security
Reviewer: deterministic
```

This reviews the PR-style diff:

```text
main...dev
```

The direction matters. For a feature branch `dev` that will merge into `main`, use:

```text
base_ref = main
target_ref = dev
```

not the reverse.

## Staged review

Stage one or more files:

```powershell
git add path\to\file.py
git diff --cached --name-status
```

Then select:

```text
Review mode: Staged changes
Preset: python-security
Reviewer: deterministic
```

DevSentinel reads the **Git index snapshot**, not the unstaged working-tree version.

After a temporary staged test:

```powershell
git restore --staged path\to\file.py
git restore path\to\file.py
```

## Review history

Click `Refresh History` to show recent review runs and links to HTML reports.

---

# 7. VS Code / MCP setup

DevSentinel exposes a local stdio MCP server.

Use:

```text
.vscode\mcp.json
```

Example configuration:

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
        "D:\\Projects\\AgentLoop\\agent_loop_from_scratch\\knowledge_base\\security",
        "--report-path",
        "D:\\Projects\\AgentLoop\\agent_loop_from_scratch\\mcp_host_report.md"
      ],
      "env": {}
    }
  }
}
```

After changing MCP configuration or tool signatures, restart the server or use:

```text
VS Code -> Developer: Reload Window
```

In VS Code:

1. Open Command Palette.
2. Run `MCP: List Servers`.
3. Select/start/restart `agentloop`.
4. Open Copilot Chat.
5. Use Agent mode.
6. Confirm DevSentinel tools are available.

Current product-level tools include:

```text
list_files
read_file
search_in_files
search_knowledge
add_finding
write_report
review_project
review_workspace
review_git_diff
compare_review_runs
```

---

# 8. Real MCP calls

The examples below are prompts for VS Code / Copilot Agent mode.

## 8.1 Search the security knowledge base

```text
Use the agentloop MCP server.

Call search_knowledge with:
- query: security review false positives detector SECRET_KEY debug token terminology

Return the retrieved evidence and source files.
```

JWT/authentication example:

```text
Use the agentloop MCP server.

Call search_knowledge with:
- query: JWT bearer token signature issuer audience expiration authentication

Return the retrieved evidence and source files.
```

---

## 8.2 Review an entire workspace

```text
Use the agentloop MCP server.

Call review_workspace with:
- workspace_path: D:\Projects\DevSentinel
- preset: python-security
- reviewer: deterministic

Return only:
- summary
- selected_files_count
- skipped_files_count
- findings_count
- run_id
- run_dir
- report_path
- HTML report path
```

OpenAI/contextual version:

```text
Use the agentloop MCP server.

Call review_workspace with:
- workspace_path: D:\Projects\DevSentinel\
- preset: python-security
- reviewer: openai

Return the summary, findings, run_id, run_dir, report_path, and HTML report path.
```

A full OpenAI workspace review can be slow on a large repository. Prefer Git diff review for normal development.

---

## 8.3 Review a Git branch / PR-style diff

For a branch `dev` containing changes relative to `main`:

```text
Use the agentloop MCP server.

Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- base_ref: main
- target_ref: dev
- preset: python-security
- reviewer: deterministic

Return only:
- mode
- summary
- changed_files_count
- selected_files_count
- skipped_files_count
- findings_count
- run_id
- run_dir
- report_path
- HTML report path
```

DevSentinel uses PR-style triple-dot semantics:

```text
main...dev
```

Verify the underlying Git scope with:

```powershell
git --no-pager diff --name-status main...dev
```

---

## 8.4 Review a small commit range with OpenAI

Use a smaller commit range when a large OpenAI diff review exceeds the MCP host timeout.

Example from DevSentinel development history:

```text
Use the agentloop MCP server.

Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- base_ref: 65d0c84
- target_ref: 2d3f07d
- preset: python-security
- reviewer: openai

Return only:
- mode
- summary
- changed_files_count
- selected_files_count
- skipped_files_count
- findings_count
- findings
- run_id
- run_dir
- report_path
- HTML report path
```

---

## 8.5 Review staged changes

```text
Use the agentloop MCP server.

Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- staged_only: true
- preset: python-security
- reviewer: deterministic

Return only:
- mode
- summary
- changed_files_count
- selected_files_count
- skipped_files_count
- findings_count
- changed_files
- selected_files
- run_id
- run_dir
- HTML report path
```

Before calling it:

```powershell
git diff --cached --name-status
```

If `changed_files_count > 0` but `selected_files_count == 0`, the staged files may not match the selected preset.

---

# 9. Review presets

Current public preset IDs:

```text
python-security
typescript-security
general-security
```

Use `python-security` for Python source review, `typescript-security` for TypeScript/JavaScript review, and `general-security` for mixed-language projects.

Preset file patterns and limits live in `agentloop.toml`.

---

# 10. Reviewer modes

## Deterministic reviewer

Use when you want speed, reproducibility, no external LLM calls, a predictable baseline, or CI-friendly behavior.

```text
reviewer: deterministic
```

Trade-off: pattern rules can produce false positives when security vocabulary appears in detectors, examples, or non-security contexts.

## OpenAI reviewer

Use when you want semantic/contextual analysis and security-KB context.

```text
reviewer: openai
```

Trade-offs:

- slower;
- external model calls;
- potentially sensitive source code leaves the local process;
- large reviews may exceed the MCP host/tool timeout.

For confidential repositories, confirm external model processing is permitted.

---

# 11. CLI agent examples

The project still supports lower-level CLI execution for experimentation and debugging.

## Classic code-review preset

```powershell
python run_agent.py `
  --preset code-review `
  --path .\sample_project `
  --llm demo `
  --max-steps 20
```

Preview the generated task without running:

```powershell
python run_agent.py `
  --preset code-review `
  --path .\sample_project `
  --print-task
```

Run an explicit task:

```powershell
python run_agent.py `
  --task "Review the sample project." `
  --llm demo `
  --max-steps 20
```

The lower-level CLI writes trace/run-summary artifacts and is useful for debugging the agent loop.

---

# 12. Unified agent runtime examples

List modes:

```powershell
python run_agent_mode.py --list-modes
```

The project supports at least:

```text
code_review
rag_qa
```

Unified code review:

```powershell
python run_agent_mode.py `
  --mode code_review `
  --preset code-review `
  --path .\sample_project `
  --llm demo `
  --max-steps 20
```

Unified RAG QA:

```powershell
python run_agent_mode.py `
  --mode rag_qa `
  --task "What does the security policy say about token expiration?" `
  --knowledge-path .\knowledge_base\security
```

For current options:

```powershell
python run_agent_mode.py --help
```

---

# 13. MCP smoke test

Example:

```powershell
python run_mcp_client_smoke.py `
  --project-path .\sample_project `
  --knowledge-path .\knowledge_base\security `
  --report-path .\mcp_host_report.md
```

Machine-readable output:

```powershell
python run_mcp_client_smoke.py `
  --project-path .\sample_project `
  --knowledge-path .\knowledge_base\security `
  --report-path .\mcp_host_report.md `
  --json
```

This is useful after MCP registration/server changes.

---

# 14. Review artifacts

High-level review workflows create persistent run packages.

Default layout:

```text
reviews\
  history.json

  <run_id>\
    report.md
    report.html
    summary.json
    findings.json
    reviewed_files.json
    run_config.json

  comparisons\
    <comparison_id>\
      comparison.json
      comparison.md
      comparison.html
```

A run ID contains a timestamp and metadata, for example:

```text
20260818_151954_505700_agent_loop_from_scratch_security_openai
```

The HTML report is usually the easiest artifact to inspect manually.

---

# 15. Stable finding identity and comparison

Findings use stable machine-oriented types where possible:

```text
security.hardcoded_secret
security.hardcoded_admin_credentials
security.debug_mode
security.token_validation
security.token_expiration
security.information_disclosure
security.other
```

This allows comparison without depending on exact LLM wording.

Run comparison can distinguish:

```text
new findings
resolved findings
unchanged findings
severity changes
```

Use the `compare_review_runs` MCP tool. Follow the input schema exposed by the current MCP server/tool picker; that schema is authoritative for the current run-reference arguments.

---

# 16. Testing and evaluation

Run tests:

```powershell
python -m pytest -q
```

Run CI/evaluation:

```powershell
python scripts/run_ci_checks.py
```

The eval suite covers:

```text
retrieval
answer
grounding
agent
```

RAG/agent changes should be evaluated for regressions rather than judged only by a few manual outputs.

---

# 17. Common workflows

## Daily development review

Recommended:

```text
Git diff or staged review
+ language-specific security preset
+ deterministic reviewer
```

Use OpenAI for contextual follow-up.

## Before committing

```powershell
git add ...
git diff --cached --name-status
```

Then call `review_git_diff` with:

```text
staged_only: true
```

## Reviewing a feature branch

```text
base_ref: main
target_ref: feature-branch
```

## Investigating deterministic false positives

Repeat a small diff with:

```text
reviewer: openai
```

and make sure MCP uses:

```text
knowledge_base\security
```

## Large OpenAI review

Prefer, in order:

1. staged changes;
2. a feature-branch diff;
3. a targeted commit range.

Avoid starting with the entire workspace.

---

# 18. Troubleshooting

## MCP tool missing after code changes

Restart MCP or use:

```text
Developer: Reload Window
```

VS Code may retain an older stdio server process.

## Git diff returns zero files

For a `dev -> main` PR, use:

```text
base_ref: main
target_ref: dev
```

Check:

```powershell
git --no-pager diff --name-status main...dev
```

## Staged review returns zero files

Check:

```powershell
git diff --cached --name-status
```

If empty, nothing is staged.

## Changed files exist but selected files are zero

The files may not match the preset. `python-security`, for example, can skip non-Python or excluded paths according to configuration.

## OpenAI review times out through MCP

Large diffs can require many model calls.

Prefer a smaller Git/commit range, staged changes, or deterministic broad scan followed by targeted OpenAI review.

These are separate timeout concepts:

```text
OpenAI request timeout
Git command timeout
MCP/Copilot whole-tool-call timeout
```

## RAG returns old knowledge after KB changes

If using a persistent index created before the KB update, rebuild it or verify directly from:

```text
--knowledge-path .\knowledge_base\security
```

without a stale index.

---

# 19. Known limitations

DevSentinel intentionally stops short of a commercial/enterprise security platform.

Current limitations include:

- deterministic security detection is pattern-based;
- OpenAI review can be slow for many files;
- external LLM review creates a source-code data boundary;
- reviewed source content can contain prompt-injection-like instructions;
- no full multi-user/tenant authorization model;
- filesystem-based artifact history;
- no GitHub/GitLab PR API integration;
- no full finding suppression/acceptance lifecycle;
- no changed-hunk-only LLM review;
- no distributed/background review workers.

---

# 20. Recommended future usage pattern

For normal local development:

```text
1. Keep agentloop.toml under version control.
2. Keep .env private.
3. Keep production security guidance in knowledge_base\security.
4. Use Web UI for convenient local reviews.
5. Use MCP/VS Code while coding interactively.
6. Prefer staged/Git-diff scope.
7. Use deterministic review as the baseline.
8. Use OpenAI review for contextual follow-up.
9. Inspect finding evidence and report.html before acting.
10. Run tests/evals after modifying DevSentinel itself.
```

---

# 21. Quick reference

## Start Web UI

```powershell
python web_ui.py --knowledge-path ".\knowledge_base\security"
```

## Run tests

```powershell
python -m pytest -q
```

## Run CI + eval suite

```powershell
python scripts/run_ci_checks.py
```

## Check staged files

```powershell
git diff --cached --name-status
```

## Check PR-style diff

```powershell
git --no-pager diff --name-status main...dev
```

## Start MCP server manually

```powershell
python run_mcp_server.py `
  --transport stdio `
  --knowledge-path ".\knowledge_base\security" `
  --report-path ".\mcp_host_report.md"
```

## MCP: feature-branch review

```text
Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- base_ref: main
- target_ref: dev
- preset: python-security
- reviewer: deterministic
```

## MCP: staged review

```text
Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- staged_only: true
- preset: python-security
- reviewer: deterministic
```

## MCP: contextual OpenAI review

```text
Call review_git_diff with:
- repository_path: D:\Projects\DevSentinel
- base_ref: <base>
- target_ref: <target>
- preset: python-security
- reviewer: openai
```

## MCP: search security policy

```text
Call search_knowledge with:
- query: JWT signature issuer audience expiration authentication
```

---

# 22. Safety note

Treat all findings as review input, not automatic truth.

For security findings:

- verify evidence in code;
- distinguish production code from tests/examples/detectors;
- consider deployment/runtime context;
- do not rotate/delete credentials based only on a lexical match;
- for real exposed secrets, rotate/revoke them rather than only removing them from source.

The combination of deterministic analysis, RAG policy context, and LLM reasoning improves review quality, but human engineering judgment remains part of the intended workflow.
