import argparse
import json

from agent_modes import (
    AGENT_MODE_RAG_QA,
    SUPPORTED_AGENT_MODES,
    list_agent_modes,
)
from agent_runtime import (
    AgentRuntimeRequest,
    agent_runtime_result_to_dict,
    run_agent_runtime,
)
from rag_qa_llm_factory import (
    RAG_QA_LLM_DETERMINISTIC,
    SUPPORTED_RAG_QA_LLMS,
)
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an agent mode through the unified runtime."
    )

    parser.add_argument(
        "--mode",
        choices=sorted(
            SUPPORTED_AGENT_MODES,
        ),
        default=AGENT_MODE_RAG_QA,
    )

    parser.add_argument(
        "--task",
        required=False,
        default="",
    )

    parser.add_argument(
        "--knowledge-path",
        default="",
    )

    parser.add_argument(
        "--index-path",
        default="",
    )

    parser.add_argument(
        "--strategy",
        choices=sorted(
            SUPPORTED_RETRIEVAL_STRATEGIES,
        ),
        default=RETRIEVAL_STRATEGY_DEFAULT,
    )

    parser.add_argument(
        "--llm",
        choices=sorted(
            SUPPORTED_RAG_QA_LLMS,
        ),
        default=RAG_QA_LLM_DETERMINISTIC,
    )

    parser.add_argument(
        "--model",
        default="gpt-5",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--artifacts-dir",
        default="",
    )

    parser.add_argument(
        "--json",
        action="store_true",
    )

    parser.add_argument(
        "--list-modes",
        action="store_true",
    )

    return parser


def format_modes() -> str:
    lines = [
        "Supported agent modes",
        "---------------------",
    ]

    for mode in list_agent_modes():
        lines.append(
            f"{mode.name}: {mode.description}"
        )

    return "\n".join(
        lines,
    )


def run_from_args(
    raw_args=None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    if args.list_modes:
        return format_modes()

    request = AgentRuntimeRequest(
        mode=args.mode,
        task=args.task,
        knowledge_path=args.knowledge_path,
        index_path=args.index_path,
        strategy=args.strategy,
        llm_name=args.llm,
        model=args.model,
        max_steps=args.max_steps,
        artifacts_dir=args.artifacts_dir,
    )

    result = run_agent_runtime(
        request,
    )

    if args.json:
        return json.dumps(
            agent_runtime_result_to_dict(
                result,
            ),
            indent=2,
        )

    return result.answer


def main() -> None:
    print(
        run_from_args()
    )


if __name__ == "__main__":
    main()