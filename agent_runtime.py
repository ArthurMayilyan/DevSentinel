from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from agent_modes import (
    AGENT_MODE_CODE_REVIEW,
    AGENT_MODE_RAG_QA,
    validate_agent_mode,
)
from code_review_runtime import (
    SUPPORTED_CODE_REVIEW_LLMS,
    format_code_review_markdown_report,
    run_code_review_agent,
)
from task_presets import DEFAULT_CODE_REVIEW_MAX_FINDINGS
from agent_config import AgentConfig
from rag_agent_runtime import (
    format_rag_agent_markdown_report,
    rag_agent_run_result_to_dict,
    run_rag_agent,
)
from rag_qa_llm_factory import RAG_QA_LLM_DETERMINISTIC
from rag_strategy_factory import RETRIEVAL_STRATEGY_DEFAULT
from app_settings import get_app_settings
from openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
)

_SETTINGS = get_app_settings()


@dataclass(frozen=True)
class AgentRuntimeRequest:
    mode: str
    task: str = ""

    # code_review mode
    preset: str = ""
    path: str = ""
    max_findings: int = DEFAULT_CODE_REVIEW_MAX_FINDINGS

    # RAG/shared options
    knowledge_path: str = ""
    index_path: str = ""
    strategy: str = RETRIEVAL_STRATEGY_DEFAULT
    llm_name: str = ""
    model: str = DEFAULT_OPENAI_MODEL

    max_steps: int = (
        _SETTINGS.runtime.agent_mode_max_steps
    )
    artifacts_dir: str = ""

    # Agent guardrail limits
    max_rejected_final_answers: int = AgentConfig().max_rejected_final_answers
    max_rejected_tool_calls: int = AgentConfig().max_rejected_tool_calls
    max_invalid_llm_outputs: int = AgentConfig().max_invalid_llm_outputs

    # OpenAI options
    max_output_tokens: int | None = None
    request_timeout_seconds: float | None = None


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

    if request.mode == AGENT_MODE_RAG_QA:
        if not isinstance(request.task, str) or not request.task.strip():
            raise ValueError("task must be a non-empty string for rag_qa mode.")

        if not request.knowledge_path:
            raise ValueError("knowledge_path is required for rag_qa mode.")

        if request.llm_name not in {
            "",
            "deterministic",
            "openai",
        }:
            raise ValueError(
                f"unsupported rag_qa LLM: {request.llm_name}"
            )

    if request.mode == AGENT_MODE_CODE_REVIEW:
        if request.task and request.preset:
            raise ValueError("Use either task or preset for code_review mode, not both.")

        if not request.task and not request.preset:
            raise ValueError("Either task or preset is required for code_review mode.")

        if request.preset and not request.path:
            raise ValueError("path is required when preset is used for code_review mode.")

        if request.llm_name not in {
            "",
            *SUPPORTED_CODE_REVIEW_LLMS,
        }:
            raise ValueError(
                f"unsupported code_review LLM: {request.llm_name}"
            )


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
            path
            / _SETTINGS.artifacts.default_report_path,
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
    llm_name = request.llm_name or RAG_QA_LLM_DETERMINISTIC

    rag_result = run_rag_agent(
        knowledge_path=request.knowledge_path,
        index_path=request.index_path,
        query=request.task,
        strategy=request.strategy,
        llm_name=llm_name,
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


def run_code_review_mode(
    *,
    request: AgentRuntimeRequest,
) -> AgentRuntimeResult:
    llm_name = request.llm_name or "demo"

    output = run_code_review_agent(
        task=request.task,
        preset=request.preset,
        path=request.path,
        knowledge_path=request.knowledge_path,
        llm_name=llm_name,
        model=request.model,
        max_steps=request.max_steps,
        max_findings=request.max_findings,
        max_rejected_final_answers=request.max_rejected_final_answers,
        max_rejected_tool_calls=request.max_rejected_tool_calls,
        max_invalid_llm_outputs=request.max_invalid_llm_outputs,
        max_output_tokens=request.max_output_tokens,
        request_timeout_seconds=request.request_timeout_seconds,
    )

    report_markdown = format_code_review_markdown_report(
        output,
    )

    result_json_path, report_path = build_artifact_paths(
        artifacts_dir=request.artifacts_dir,
    )

    if result_json_path:
        write_json_file(
            path=result_json_path,
            data=output,
        )

    if report_path:
        write_text_file(
            path=report_path,
            content=report_markdown,
        )

    return AgentRuntimeResult(
        mode=request.mode,
        task=output.get(
            "run",
            {},
        ).get(
            "task",
            request.task,
        ),
        answer=output.get(
            "answer",
        )
        or output.get(
            "stop_reason",
        )
        or "",
        result=output,
        result_dict=output,
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

    if request.mode == AGENT_MODE_CODE_REVIEW:
        return run_code_review_mode(
            request=request,
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

