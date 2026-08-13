import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rag_agent import build_rag_qa_agent
from rag_loader import load_rag_store_from_path
from rag_qa_llm import DeterministicRagQaLLM
from rag_qa_llm_factory import (
    RAG_QA_LLM_DETERMINISTIC,
    build_rag_qa_llm,
)
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    build_rag_search_engine_for_strategy,
)
from trace import TraceRecorder


@dataclass(frozen=True)
class RagAgentRunResult:
    query: str
    answer: str
    knowledge_path: str
    strategy: str
    llm: str
    model: str
    max_steps: int
    sources: list[str]
    evidence: list[dict[str, Any]]
    trace_steps: list[dict[str, Any]]
    guardrail_passed: bool | None
    guardrail_failure_reasons: list[str]
    fallback_used: bool


def get_evidence_source(
    item: dict[str, Any],
) -> str:
    for key in [
        "source",
        "file",
        "path",
    ]:
        value = item.get(
            key,
        )

        if isinstance(value, str) and value.strip():
            return value

    return ""


def extract_sources_from_evidence(
    evidence: list[dict[str, Any]],
) -> list[str]:
    sources = []

    for item in evidence:
        source = get_evidence_source(
            item,
        )

        if source and source not in sources:
            sources.append(
                source,
            )

    return sources


def extract_latest_evidence_from_trace_steps(
    trace_steps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    parser = DeterministicRagQaLLM()

    return parser.extract_latest_evidence(
        trace_steps,
    )


def rag_agent_run_result_to_dict(
    result: RagAgentRunResult,
) -> dict[str, Any]:
    return asdict(
        result,
    )


def run_rag_agent(
    *,
    knowledge_path: str,
    query: str,
    strategy: str = RETRIEVAL_STRATEGY_DEFAULT,
    llm_name: str = RAG_QA_LLM_DETERMINISTIC,
    model: str = "gpt-5",
    max_steps: int = 4,
) -> RagAgentRunResult:
    store = load_rag_store_from_path(
        path=knowledge_path,
    )

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=strategy,
    )

    llm = build_rag_qa_llm(
        name=llm_name,
        model=model,
    )

    trace_recorder = TraceRecorder()

    agent = build_rag_qa_agent(
        rag_store=search_engine,
        max_steps=max_steps,
        trace_recorder=trace_recorder,
        llm=llm,
    )

    answer = agent.run(
        query,
    )

    trace_steps = trace_recorder.read_steps()

    evidence = extract_latest_evidence_from_trace_steps(
        trace_steps,
    )

    sources = extract_sources_from_evidence(
        evidence,
    )

    return RagAgentRunResult(
        query=query,
        answer=answer,
        knowledge_path=knowledge_path,
        strategy=strategy,
        llm=llm_name,
        model=model,
        max_steps=max_steps,
        sources=sources,
        evidence=evidence,
        trace_steps=trace_steps,
        guardrail_passed=getattr(
            llm,
            "last_guardrail_passed",
            None,
        ),
        guardrail_failure_reasons=getattr(
            llm,
            "last_guardrail_failure_reasons",
            [],
        ),
        fallback_used=getattr(
            llm,
            "last_fallback_used",
            False,
        ),
    )


def write_rag_agent_result_json(
    *,
    result: RagAgentRunResult,
    output_path: str,
) -> None:
    path = Path(
        output_path,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            rag_agent_run_result_to_dict(
                result,
            ),
            indent=2,
        ),
        encoding="utf-8",
    )


def format_rag_agent_markdown_report(
    result: RagAgentRunResult,
) -> str:
    lines = [
        "# RAG Agent Run Report",
        "",
        "## Configuration",
        "",
        f"Knowledge path: `{result.knowledge_path}`",
        f"Strategy: `{result.strategy}`",
        f"LLM: `{result.llm}`",
        f"Model: `{result.model}`",
        f"Max steps: `{result.max_steps}`",
        "",
        "## Query",
        "",
        result.query,
        "",
        "## Answer",
        "",
        result.answer,
        "",
        "## Sources",
        "",
    ]

    if result.sources:
        for source in result.sources:
            lines.append(
                f"- `{source}`"
            )
    else:
        lines.append(
            "- No sources found"
        )

    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            f"Guardrail passed: `{result.guardrail_passed}`",
            f"Fallback used: `{result.fallback_used}`",
            "",
        ]
    )

    if result.guardrail_failure_reasons:
        lines.append(
            "Failure reasons:"
        )
        lines.append(
            "",
        )

        for reason in result.guardrail_failure_reasons:
            lines.append(
                f"- {reason}"
            )
    else:
        lines.append(
            "Failure reasons: none"
        )

    lines.extend(
        [
            "",
            "## Evidence",
            "",
        ]
    )

    if result.evidence:
        for index, item in enumerate(
            result.evidence,
            start=1,
        ):
            source = get_evidence_source(
                item,
            )

            text = item.get(
                "text",
                item.get(
                    "content",
                    "",
                ),
            )

            lines.extend(
                [
                    f"### Evidence {index}",
                    "",
                    f"Source: `{source}`",
                    "",
                    str(
                        text,
                    ),
                    "",
                ]
            )
    else:
        lines.append(
            "No evidence found."
        )

    lines.extend(
        [
            "",
            "## Trace",
            "",
            f"Trace steps: `{len(result.trace_steps)}`",
        ]
    )

    return "\n".join(
        lines,
    )


def write_rag_agent_markdown_report(
    *,
    result: RagAgentRunResult,
    output_path: str,
) -> None:
    path = Path(
        output_path,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        format_rag_agent_markdown_report(
            result,
        ),
        encoding="utf-8",
    )