from mcp_server_context import AgentLoopMcpContext


def build_project_guide_resource() -> str:
    return """# AgentLoop Project Guide

AgentLoop is a local agent playground for code review, RAG, and MCP integration.

Main capabilities:
- code review mode
- RAG question-answering mode
- MCP tool server
- MCP client smoke tests
- VS Code MCP host integration
- product-level project review workflow

Main MCP tools:
- list_files
- read_file
- search_in_files
- search_knowledge
- add_finding
- write_report
- review_project
"""


def build_available_workflows_resource() -> str:
    return """# AgentLoop Available Workflows

## 1. Product-level project review

Use review_project to run the full review workflow with one tool call.

Example:
- project_path: ./sample_project
- profile: security

## 2. Manual local project review

Use tools in this order:
1. list_files
2. read_file
3. search_knowledge
4. add_finding
5. write_report

## 3. Ask policy question

Use search_knowledge to answer questions from the attached knowledge base.

## 4. Generate final report

Use add_finding for each issue, then call write_report.
"""


def build_code_review_policy_resource() -> str:
    return """# AgentLoop Code Review Policy

When reviewing code:

- Inspect relevant project files before making findings.
- Use search_knowledge when a knowledge base is attached.
- Do not invent findings without evidence.
- Add findings only when there is file-level evidence.
- Use HIGH or CRITICAL severity for security-sensitive issues.
- Use write_report only after findings are complete.

Finding fields:
- file
- severity
- category
- issue
- evidence
- recommendation
"""


def build_current_state_resource(
    context: AgentLoopMcpContext,
) -> str:
    discovered_files = "\n".join(
        f"- {file}"
        for file in context.state.discovered_files
    ) or "- none"

    inspected_files = "\n".join(
        f"- {file}"
        for file in context.state.inspected_files
    ) or "- none"

    findings = "\n".join(
        f"- {finding.get('severity')} / {finding.get('category')}: {finding.get('issue')} ({finding.get('file')})"
        for finding in context.state.findings
    ) or "- none"

    return f"""# AgentLoop Current State

## Discovered Files

{discovered_files}

## Inspected Files

{inspected_files}

## Findings

{findings}

## Report

- written: {context.state.report_written}
- path: {context.state.report_path or "none"}
"""


def build_review_project_prompt(
    *,
    project_path: str = "./sample_project",
) -> str:
    return f"""Use the agentloop MCP server to review this project:

{project_path}

Preferred workflow:
1. Call review_project with:
   - project_path: {project_path}
   - profile: security
   - include_globs: **/*.py
   - max_files: 200
   - max_file_size_bytes: 200000
2. Return the summary and report path from review_project.

Fallback manual workflow if review_project is unavailable:
1. Use list_files to discover files under the project path.
2. Use read_file to inspect relevant source files.
3. Use search_knowledge with the query "credentials production security" to check the attached security policy.
4. Add one finding for every concrete issue using add_finding.
5. Use write_report when the review is complete.

Rules:
- Do not invent findings.
- Every finding must include concrete file-level evidence.
- Prefer SECURITY category for credential, secret, authentication, or access-control issues.
- Use HIGH or CRITICAL severity for hardcoded credentials.
"""


def build_review_file_prompt(
    *,
    file_path: str,
) -> str:
    return f"""Use the agentloop MCP server to review this file:

{file_path}

Workflow:
1. Use read_file to inspect the file.
2. Use search_knowledge if the issue is related to security or production policy.
3. Use add_finding only if there is concrete evidence.
4. Use write_report when done.

Focus on:
- hardcoded credentials
- debug mode
- unsafe authentication behavior
- reliability risks
"""


def build_answer_policy_question_prompt(
    *,
    question: str,
) -> str:
    return f"""Use the agentloop MCP server to answer this policy question:

{question}

Workflow:
1. Use search_knowledge with a concise query.
2. Answer only from retrieved knowledge.
3. Cite the source returned by search_knowledge.
4. Say when there is not enough evidence.
"""


def build_write_security_report_prompt() -> str:
    return """Use the agentloop MCP server to finalize the security review.

Workflow:
1. Check current state using the agentloop://current-state resource if available.
2. If findings are already added, call write_report.
3. Do not create duplicate findings.
4. Report the generated report path to the user.
"""