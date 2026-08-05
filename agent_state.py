from dataclasses import dataclass, field, asdict


@dataclass
class FileInspection:
    path: str
    status: str  # discovered | inspected | skipped | failed
    reason: str | None = None
    content_hash: str | None = None
    summary: str | None = None
    findings: list[dict] = field(default_factory=list)
    findings_count: int = 0


@dataclass
class AgentState:
    discovered_files: list[str] = field(default_factory=list)
    inspected_files: list[str] = field(default_factory=list)
    skipped_files: dict[str, str] = field(default_factory=dict)
    failed_files: dict[str, str] = field(default_factory=dict)

    tools_used: list[str] = field(default_factory=list)
    report_written: bool = False
    report_path: str | None = None

    findings: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    rejected_final_answer_count: int = 0
    rejected_tool_call_count: int = 0
    invalid_llm_output_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)