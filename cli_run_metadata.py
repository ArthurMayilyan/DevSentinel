from argparse import Namespace
from typing import Any

from agent_config import AgentConfig
from cli_defaults import (
    resolve_cli_max_output_tokens,
    resolve_cli_request_timeout_seconds,
)


def build_run_metadata(
    *,
    args: Namespace,
    task: str,
    config: AgentConfig,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "llm": args.llm,
        "model": args.model if args.llm == "openai" else None,
        "preset": args.preset,
        "path": args.path,
        "max_findings": args.max_findings if args.preset else None,
        "max_steps": config.max_steps,
        "max_rejected_final_answers": config.max_rejected_final_answers,
        "max_rejected_tool_calls": config.max_rejected_tool_calls,
        "max_invalid_llm_outputs": config.max_invalid_llm_outputs,
        "task": task,
    }

    if args.llm == "openai":
        metadata["max_output_tokens"] = resolve_cli_max_output_tokens(
            max_output_tokens=getattr(args, "max_output_tokens", None),
        )
        metadata["request_timeout_seconds"] = resolve_cli_request_timeout_seconds(
            request_timeout_seconds=getattr(args, "request_timeout_seconds", None),
        )
    else:
        metadata["max_output_tokens"] = None
        metadata["request_timeout_seconds"] = None

    return metadata

