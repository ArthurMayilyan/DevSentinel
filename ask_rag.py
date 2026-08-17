import argparse
import json
from pathlib import Path

from rag_loader import load_rag_store_from_path
from rag_pipeline import (
    rag_pipeline_result_to_dict,
    run_rag_pipeline,
)
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
    build_rag_search_engine_for_strategy,
)
from rag_defaults import (
    DEFAULT_RAG_TOP_K,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ask a question against a local RAG knowledge base.",
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
        help="Path to a knowledge base file or directory.",
    )

    parser.add_argument(
        "--query",
        required=True,
        help="Question or search query to answer.",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_RAG_TOP_K,
        help=(
            "Number of RAG results to retrieve. "
            "Defaults to rag.top_k from agentloop.toml."
        ),
    )

    parser.add_argument(
        "--strategy",
        choices=sorted(SUPPORTED_RETRIEVAL_STRATEGIES),
        default=RETRIEVAL_STRATEGY_DEFAULT,
        help="Retrieval strategy to use for answering.",
    )    

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON output.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for JSON output.",
    )

    return parser


def format_rag_answer_text(
    output: dict,
) -> str:
    lines = [
        "Answer",
        "------",
        output["answer"],
        "",
        "Strategy",
        "--------",
        output["strategy"],
        "",
        "Sources",
        "-------",
    ]

    for source in output["cited_sources"]:
        lines.append(
            f"- {source}"
        )

    return "\n".join(lines)


def run_from_args(
    raw_args: list[str] | None = None,
) -> dict:
    parser = build_arg_parser()
    args = parser.parse_args(raw_args)

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=args.strategy,
    )

    result = run_rag_pipeline(
        store=search_engine,
        query=args.query,
        top_k=args.top_k,
    )

    output = rag_pipeline_result_to_dict(
        result,
    )
    output["strategy"] = args.strategy

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        output_path.write_text(
            json.dumps(
                output,
                indent=2,
            ),
            encoding="utf-8",
        )

    return output


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    raw_args = [
        "--knowledge-path",
        args.knowledge_path,
        "--query",
        args.query,
        "--top-k",
        str(args.top_k),
        "--strategy",
        args.strategy,
    ]

    if args.json:
        raw_args.append(
            "--json",
        )

    if args.output is not None:
        raw_args.extend(
            [
                "--output",
                args.output,
            ]
        )

    output = run_from_args(
        raw_args,
    )

    if args.json:
        print(
            json.dumps(
                output,
                indent=2,
            )
        )
    else:
        print(
            format_rag_answer_text(
                output,
            )
        )


if __name__ == "__main__":
    main()