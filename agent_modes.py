from dataclasses import dataclass


AGENT_MODE_CODE_REVIEW = "code_review"
AGENT_MODE_RAG_QA = "rag_qa"

SUPPORTED_AGENT_MODES = {
    AGENT_MODE_CODE_REVIEW,
    AGENT_MODE_RAG_QA,
}


@dataclass(frozen=True)
class AgentModeSpec:
    name: str
    description: str
    requires_knowledge_path: bool
    supports_index_path: bool
    supports_strategy: bool
    supports_llm: bool
    mcp_tools: list[str]


def get_agent_mode_specs() -> dict[str, AgentModeSpec]:
    return {
        AGENT_MODE_CODE_REVIEW: AgentModeSpec(
            name=AGENT_MODE_CODE_REVIEW,
            description="Code review agent over a local project path.",
            requires_knowledge_path=False,
            supports_index_path=False,
            supports_strategy=False,
            supports_llm=True,
            mcp_tools=[
                "list_files",
                "read_file",
                "search_in_files",
                "search_knowledge",
                "add_finding",
                "write_report",
                "review_project",
            ],
        ),
        AGENT_MODE_RAG_QA: AgentModeSpec(
            name=AGENT_MODE_RAG_QA,
            description="Question-answering over a local RAG knowledge base.",
            requires_knowledge_path=True,
            supports_index_path=True,
            supports_strategy=True,
            supports_llm=True,
            mcp_tools=[
                "search_knowledge",
            ],
        ),
    }


def validate_agent_mode(
    mode: str,
) -> None:
    if mode not in SUPPORTED_AGENT_MODES:
        supported = ", ".join(
            sorted(
                SUPPORTED_AGENT_MODES,
            )
        )

        raise ValueError(
            f"unsupported agent mode: {mode}. Supported modes: {supported}"
        )


def get_agent_mode_spec(
    mode: str,
) -> AgentModeSpec:
    validate_agent_mode(
        mode,
    )

    return get_agent_mode_specs()[
        mode
    ]


def list_agent_modes() -> list[AgentModeSpec]:
    return [
        get_agent_mode_specs()[mode]
        for mode in sorted(
            SUPPORTED_AGENT_MODES,
        )
    ]