import argparse

from rag_agent_runtime import (
    format_rag_agent_markdown_report,
    run_rag_agent,
    write_rag_agent_markdown_report,
    write_rag_agent_result_json,
)
from rag_qa_llm_factory import (
    RAG_QA_LLM_DETERMINISTIC,
    SUPPORTED_RAG_QA_LLMS,
)
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
)
from openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
)

from rag_defaults import (
    DEFAULT_RAG_AGENT_MAX_STEPS,
    DEFAULT_RAG_RETRIEVAL_STRATEGY,
)

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask a question using the Agent RAG QA loop.",
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
    )

    parser.add_argument(
        "--query",
        required=True,
    )

    parser.add_argument(
        "--strategy",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=DEFAULT_RAG_RETRIEVAL_STRATEGY,
    )

    parser.add_argument(
        "--llm",
        choices=sorted(SUPPORTED_RAG_QA_LLMS),
        default=RAG_QA_LLM_DETERMINISTIC,
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_OPENAI_MODEL,
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=DEFAULT_RAG_AGENT_MAX_STEPS,
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write structured JSON result.",
    )

    parser.add_argument(
        "--report-output",
        default=None,
        help="Optional path to write a Markdown run report.",
    )

    parser.add_argument(
        "--index-path",
        default="",
    )    

    return parser


def format_agent_rag_answer(
    answer: str,
) -> str:
    return "\n".join(
        [
            "Answer",
            "------",
            answer,
        ]
    )


def run_from_args(
    raw_args: list[str] | None = None,
) -> str:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    result = run_rag_agent(
        knowledge_path=args.knowledge_path,
        index_path=args.index_path,
        query=args.query,
        strategy=args.strategy,
        llm_name=args.llm,
        model=args.model,
        max_steps=args.max_steps,
    )

    if args.output:
        write_rag_agent_result_json(
            result=result,
            output_path=args.output,
        )

    if args.report_output:
        write_rag_agent_markdown_report(
            result=result,
            output_path=args.report_output,
        )

    return result.answer


def main() -> None:
    answer = run_from_args()

    print(
        format_agent_rag_answer(
            answer,
        )
    )


if __name__ == "__main__":
    main()