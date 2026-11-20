# DevSentinel

[Repository](https://github.com/ArthurMayilyan/DevSentinel) · [Setup](#3-runtime-requirements) · [Web UI](#6-recommended-way-to-use-devsentinel-web-ui) · [MCP](#7-vs-code--mcp-setup)

Agentic security code review with RAG, MCP, guardrails, and evals.

DevSentinel is a local AI-assisted engineering review platform built to explore and demonstrate modern agentic engineering from first principles.

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

## Repository layout

```text
devsentinel/
  cli/       Command-line workflows and evaluation runners
  config/    Application and reviewer settings
  core/      Agent runtime, tools, prompts, and traces
  llm/       Model adapters and test implementations
  mcp/       MCP server, tools, prompts, and host configuration
  rag/       Retrieval, indexing, QA, and RAG evaluation
  review/    Workspace and Git review workflows and artifacts
  ui/        Web server and static assets
tests/       Automated tests and fixtures
docs/        MCP workflow and architecture notes
```

`run_mcp_server.py` and `web_ui.py` are small launchers for existing local
MCP and Web UI configurations. Other commands run as package modules, for
example `python -m devsentinel.cli.run_agent --help`. The package can also be
installed with `pip install -e ".[dev]"` to use the `devsentinel-*` commands.

---

## 1. Main use cases

DevSentinel currently supports four practical workflows:

1. **Workspace review** — review a project directory using a review preset.
2. **Git diff review** — review only files changed between Git revisions.
3. **Staged review** — review exactly the files/content staged in the Git index.
4. **Knowledge search / RAG QA** — retrieve security or other policy evidence from a local knowledge base.

For daily engineering work, prefer **Git diff** or **staged review** over a full workspace review.

---

## 2. Get the project

```powershell
git clone --branch dev https://github.com/ArthurMayilyan/DevSentinel.git
Set-Location ./DevSentinel
```

The `dev` branch contains the package layout and commands documented here.
Run later shell commands from the project root. In MCP examples,
`<repo-root>` means the absolute path to this checkout. Replace it with your
own path when configuring an editor. Branch names and commit IDs are examples;
use refs that exist in your repository.

---

## 3. Runtime requirements

Use Python 3.11 or newer. Git is required for Git diff and staged review.
From the checkout, create a virtual environment and install the package and
its test dependencies:

```powershell
python --version
git --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

`requirements.txt` installs this checkout in editable mode with the `dev`
extras from `pyproject.toml`. If PowerShell blocks activation, run commands
with `.\.venv\Scripts\python.exe` in place of `python`.

On macOS or Linux, use `python3 -m venv .venv` and
`source .venv/bin/activate`, then run the same pip command. Later examples use
PowerShell syntax; use `/` paths and your shell's line continuation syntax on
macOS or Linux.

Check the installation without an API key:

```powershell
python -m devsentinel.cli.run_agent --preset code-review --path .\sample_project --print-task
python -m pytest -q
```

Then start the Web UI as shown in section 6. The combined test and evaluation
command is `python scripts/run_ci_checks.py`; a healthy run reports:

```text
overall: passed
retrieval: passed
answer: passed
grounding: passed
agent: passed
```

---

## 4. OpenAI configuration

OpenAI-backed workflows require an API key. The deterministic reviewer, demo
agent, and local tests run without one.

Create a local `.env` file in the project root before using the OpenAI reviewer:

```dotenv
OPENAI_API_KEY=your-key-here
```

Do **not** commit `.env`.

The configured default is [`gpt-6-luna`](https://developers.openai.com/api/docs/models/gpt-6-luna),
which is the model used by the OpenAI reviewer unless an explicit model or
`DEVSENTINEL_OPENAI_MODEL` overrides it.
Use a model available to your API account.
Before a release that uses OpenAI review, run the real integration check:

```powershell
python -m devsentinel.cli.run_live_openai_smoke --model gpt-6-luna
```

This command requires `OPENAI_API_KEY` and makes a live API request. The
`Live OpenAI Smoke` GitHub Actions workflow can run the same check manually
when its API key secret and model variable are configured.

The project loads non-secret runtime settings from:

```text
devsentinel.toml
```

Secrets such as `OPENAI_API_KEY` stay outside TOML.

### Configuration precedence

DevSentinel follows this general precedence:

```text
1. Explicit CLI / MCP argument
2. Environment variable
3. devsentinel.toml
4. Built-in fallback
```

Important configuration areas include:

```toml
[openai]
model = "gpt-6-luna"
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

The repository's actual `devsentinel.toml` is authoritative.
Installed packages use bundled defaults when the repository config is absent;
set `DEVSENTINEL_CONFIG_PATH` to load a different TOML file.

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

The browser asks for Basic authentication. Use username `devsentinel` and
the generated password printed in the terminal. Set `DEVSENTINEL_WEB_TOKEN`
before starting the server to use a stable password. The built-in server binds
only to a loopback address.

Press `Ctrl+C` in the terminal to stop the server. For a first review, choose
`Workspace`, `python-security`, and `deterministic`; this needs no API key.

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
<repo-root>

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
If the scan limit is reached, the summary says the results are incomplete;
narrow the workspace or preset scope and run the review again.

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

To undo staging after a temporary test, while keeping your file edits:

```powershell
git restore --staged path\to\file.py
```

## Review history

Click `Refresh History` to show recent review runs and links to HTML reports.

---

# 7. VS Code / MCP setup

DevSentinel exposes a local stdio MCP server.

Use the checked-in configuration:

```text
.vscode\mcp.json
```

The checked-in file uses `python` from your `PATH`. If you installed DevSentinel
in a virtual environment, change `command` to that environment's Python
executable (for example, `<repo-root>/.venv/Scripts/python.exe` on Windows or
`<repo-root>/.venv/bin/python` on macOS/Linux). A VS Code MCP server runs in
its own process, so choosing the interpreter used in section 3 matters. Start
VS Code with the project root as its workspace so the relative knowledge and
report paths resolve there.

Example configuration:

```json
{
  "servers": {
    "devsentinel": {
      "type": "stdio",
      "command": "<repo-root>/.venv/Scripts/python.exe",
      "args": [
        "-m",
        "devsentinel.cli.run_mcp_server",
        "--transport",
        "stdio",
        "--knowledge-path",
        "knowledge_base/security",
        "--report-path",
        "mcp_host_report.md"
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
3. Select/start/restart `devsentinel`.
4. Open Copilot Chat.
5. Use Agent mode.
6. Confirm DevSentinel tools are available.

For OpenAI review through MCP, make `OPENAI_API_KEY` available to the MCP
process. Do not put a key in the checked-in JSON file. The `.env` loader reads
from the process working directory, so verify that VS Code starts the server
from the project root or set the variable in the environment that launches VS
Code.

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
Use the devsentinel MCP server.

Call search_knowledge with:
- query: security review false positives detector SECRET_KEY debug token terminology

Return the retrieved evidence and source files.
```

JWT/authentication example:

```text
Use the devsentinel MCP server.

Call search_knowledge with:
- query: JWT bearer token signature issuer audience expiration authentication

Return the retrieved evidence and source files.
```

---

## 8.2 Review an entire workspace

```text
Use the devsentinel MCP server.

Call review_workspace with:
- workspace_path: <repo-root>
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
Use the devsentinel MCP server.

Call review_workspace with:
- workspace_path: <repo-root>
- preset: python-security
- reviewer: openai

Return the summary, findings, run_id, run_dir, report_path, and HTML report path.
```

A full OpenAI workspace review can be slow on a large repository. Prefer Git diff review for normal development.

---

## 8.3 Review a Git branch / PR-style diff

For a branch `dev` containing changes relative to `main`:

```text
Use the devsentinel MCP server.

Call review_git_diff with:
- repository_path: <repo-root>
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

The example below reviews the latest commit when the repository has at least
two commits. Check the refs with `git rev-parse HEAD~1 HEAD`:

```text
Use the devsentinel MCP server.

Call review_git_diff with:
- repository_path: <repo-root>
- base_ref: HEAD~1
- target_ref: HEAD
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
Use the devsentinel MCP server.

Call review_git_diff with:
- repository_path: <repo-root>
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

Preset file patterns and limits live in `devsentinel.toml`.

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
python -m devsentinel.cli.run_agent `
  --preset code-review `
  --path .\sample_project `
  --llm demo `
  --max-steps 20
```

Preview the generated task without running:

```powershell
python -m devsentinel.cli.run_agent `
  --preset code-review `
  --path .\sample_project `
  --print-task
```

Run an explicit task:

```powershell
python -m devsentinel.cli.run_agent `
  --task "Review the sample project." `
  --llm demo `
  --max-steps 20
```

The lower-level CLI writes trace/run-summary artifacts and is useful for debugging the agent loop.

---

# 12. Unified agent runtime examples

List modes:

```powershell
python -m devsentinel.cli.run_agent_mode --list-modes
```

The project supports at least:

```text
code_review
rag_qa
```

Unified code review:

```powershell
python -m devsentinel.cli.run_agent_mode `
  --mode code_review `
  --preset code-review `
  --path .\sample_project `
  --llm demo `
  --max-steps 20
```

Unified RAG QA:

```powershell
python -m devsentinel.cli.run_agent_mode `
  --mode rag_qa `
  --task "What does the security policy say about token expiration?" `
  --knowledge-path .\knowledge_base\security
```

For current options:

```powershell
python -m devsentinel.cli.run_agent_mode --help
```

---

# 13. MCP smoke test

Example:

```powershell
python -m devsentinel.cli.run_mcp_client_smoke `
  --project-path .\sample_project `
  --knowledge-path .\knowledge_base\security `
  --report-path .\mcp_host_report.md
```

Machine-readable output:

```powershell
python -m devsentinel.cli.run_mcp_client_smoke `
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
20260818_151954_505700_DevSentinel_security_openai
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

Call `compare_review_runs` with:

```text
old_run_dir: <repo-root>/reviews/<older-run-id>
new_run_dir: <repo-root>/reviews/<newer-run-id>
comparisons_dir: <repo-root>/reviews/comparisons  (optional)
```

`old_run_dir` and `new_run_dir` are required directories created by earlier
reviews. `comparisons_dir` overrides the output location; if omitted, the tool
writes under `reviews/comparisons` beside the newer run. The result includes a
summary and paths to JSON, Markdown, and HTML comparison reports.

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
1. Keep devsentinel.toml under version control.
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

Use `--describe` to check the launcher without starting a long-running
server:

```powershell
python run_mcp_server.py --describe
```

The stdio command below waits for an MCP client. It is intended for an editor
or MCP host, so it will not display an interactive prompt:

```powershell
python run_mcp_server.py `
  --transport stdio `
  --knowledge-path ".\knowledge_base\security" `
  --report-path ".\mcp_host_report.md"
```

## MCP: feature-branch review

```text
Call review_git_diff with:
- repository_path: <repo-root>
- base_ref: main
- target_ref: dev
- preset: python-security
- reviewer: deterministic
```

## MCP: staged review

```text
Call review_git_diff with:
- repository_path: <repo-root>
- staged_only: true
- preset: python-security
- reviewer: deterministic
```

## MCP: contextual OpenAI review

```text
Call review_git_diff with:
- repository_path: <repo-root>
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
