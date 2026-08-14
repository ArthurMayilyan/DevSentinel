from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from agent_modes import (
    AGENT_MODE_RAG_QA,
    validate_agent_mode,
)
from rag_agent_runtime import (
    format_rag_agent_markdown_report,
    rag_agent_run_result_to_dict,
    run_rag_agent,
)
from rag_qa_llm_factory import RAG_QA_LLM_DETERMINISTIC
from rag_strategy_factory import RETRIEVAL_STRATEGY_DEFAULT


@dataclass(frozen=True)
class AgentRuntimeRequest:
    mode: str
    task: str
    knowledge_path: str = ""
    index_path: str = ""
    strategy: str = RETRIEVAL_STRATEGY_DEFAULT
    llm_name: str = RAG_QA_LLM_DETERMINISTIC
    model: str = "gpt-5"
    max_steps: int = 4
    artifacts_dir: str = ""


@dataclass(frozen=True)
class AgentRuntimeResult:
    mode: str
    task: str
    answer: str
    result: Any
    result_dict: dict[str, Any]
    report_markdown: str
    artifacts_dir: str
    result_json_path: str
    report_path: str


def validate_agent_runtime_request(
    request: AgentRuntimeRequest,
) -> None:
    validate_agent_mode(
        request.mode,
    )

    if not isinstance(request.task, str) or not request.task.strip():
        raise ValueError("task must be a non-empty string.")

    if request.mode == AGENT_MODE_RAG_QA:
        if not request.knowledge_path:
            raise ValueError("knowledge_path is required for rag_qa mode.")


def build_artifact_paths(
    *,
    artifacts_dir: str,
) -> tuple[str, str]:
    if not artifacts_dir:
        return "", ""

    path = Path(
        artifacts_dir,
    )

    return (
        str(
            path / "result.json",
        ),
        str(
            path / "report.md",
        ),
    )


def write_text_file(
    *,
    path: str,
    content: str,
) -> None:
    output_path = Path(
        path,
    )
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path.write_text(
        content,
        encoding="utf-8",
    )


def write_json_file(
    *,
    path: str,
    data: dict[str, Any],
) -> None:
    import json

    write_text_file(
        path=path,
        content=json.dumps(
            data,
            indent=2,
        ),
    )


def run_rag_qa_mode(
    *,
    request: AgentRuntimeRequest,
) -> AgentRuntimeResult:
    rag_result = run_rag_agent(
        knowledge_path=request.knowledge_path,
        index_path=request.index_path,
        query=request.task,
        strategy=request.strategy,
        llm_name=request.llm_name,
        model=request.model,
        max_steps=request.max_steps,
    )

    result_dict = rag_agent_run_result_to_dict(
        rag_result,
    )

    report_markdown = format_rag_agent_markdown_report(
        rag_result,
    )

    result_json_path, report_path = build_artifact_paths(
        artifacts_dir=request.artifacts_dir,
    )

    if result_json_path:
        write_json_file(
            path=result_json_path,
            data=result_dict,
        )

    if report_path:
        write_text_file(
            path=report_path,
            content=report_markdown,
        )

    return AgentRuntimeResult(
        mode=request.mode,
        task=request.task,
        answer=rag_result.answer,
        result=rag_result,
        result_dict=result_dict,
        report_markdown=report_markdown,
        artifacts_dir=request.artifacts_dir,
        result_json_path=result_json_path,
        report_path=report_path,
    )


def run_agent_runtime(
    request: AgentRuntimeRequest,
) -> AgentRuntimeResult:
    validate_agent_runtime_request(
        request,
    )

    if request.mode == AGENT_MODE_RAG_QA:
        return run_rag_qa_mode(
            request=request,
        )

    raise ValueError(
        f"unsupported agent mode: {request.mode}"
    )


def agent_runtime_request_to_dict(
    request: AgentRuntimeRequest,
) -> dict[str, Any]:
    return asdict(
        request,
    )


def agent_runtime_result_to_dict(
    result: AgentRuntimeResult,
) -> dict[str, Any]:
    return {
        "mode": result.mode,
        "task": result.task,
        "answer": result.answer,
        "result": result.result_dict,
        "artifacts_dir": result.artifacts_dir,
        "result_json_path": result.result_json_path,
        "report_path": result.report_path,
    }

