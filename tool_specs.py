from tools import list_files, read_file, search_in_files, write_report
from tool_registry import ToolSpec
from enum import StrEnum

class IssueSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class IssueCategory(StrEnum):
    SECURITY = "SECURITY"
    MAINTAINABILITY = "MAINTAINABILITY"
    RELIABILITY = "RELIABILITY"
    PERFORMANCE = "PERFORMANCE"

TOOL_SPECS = {
    "list_files": ToolSpec(
        name="list_files",
        description="List all files under a given directory path.",
        parameters={
            "path": "Directory path to inspect, for example './sample_project'."
        },
        returns="A list of file paths.",
        when_to_use="Use this first when you need to understand project structure or discover available files.",
        when_not_to_use="Do not use this to read file contents or search inside files.",
        function=list_files,
    ),

    "read_file": ToolSpec(
        name="read_file",
        description="Read the full content of one specific file.",
        parameters={
            "path": "Exact file path to read."
        },
        returns="The full text content of the file.",
        when_to_use="Use this when you already know which file is relevant and need detailed inspection.",
        when_not_to_use="Do not use this to discover files or search across many files.",
        function=read_file,
    ),

    "search_in_files": ToolSpec(
        name="search_in_files",
        description="Search for exact text matches inside files under a directory.",
        parameters={
            "query": "Text to search for.",
            "path": "Directory path where files should be searched."
        },
        returns="A list of matches with file path, line number, and matched text.",
        when_to_use="Use this when looking for specific keywords such as TODO, password, token, secret, debug, eval, or function names.",
        when_not_to_use="Do not use this when you need full context from one file; use read_file instead.",
        function=search_in_files,
    ),

    "write_report": ToolSpec(
        name="write_report",
        description=(
            "Generate and write a markdown review report to report.md. "
            "The report is generated automatically from the current AgentState findings. "
            "The LLM must not provide markdown or state."
        ),
        parameters={},
        returns="The path of the written report file.",
        when_to_use=(
            "Use this only after all relevant files have been inspected "
            "and all findings have been added with add_finding."
        ),
        when_not_to_use=(
            "Do not use this before inspecting relevant files. "
            "Do not provide markdown. "
            "Do not provide state. "
            "State and report content are handled internally by the agent runtime."
        ),
        function=write_report,
    ),

    "add_finding": ToolSpec(
        name="add_finding",
        description="Add a new finding to the report.",
        parameters={
            "file": "The file where the finding is located.",
            "severity": "The severity of the finding.",
            "category": "The category of the finding.",
            "issue": "A description of the issue.",
            "evidence": "Evidence supporting the finding.",
            "recommendation": "A recommendation for addressing the finding."
        },
        returns="Finding added.",
        when_to_use="Use this only after enough inspection has been done and findings are ready.",
        when_not_to_use="Do not use this before inspecting relevant files.",
        function=None,
    ),
    
}
