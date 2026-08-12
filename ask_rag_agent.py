import argparse

from rag_agent import build_rag_qa_agent
from rag_loader import load_rag_store_from_path
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_DEFAULT,
    SUPPORTED_RETRIEVAL_STRATEGIES,
    build_rag_search_engine_for_strategy,
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
        default=RETRIEVAL_STRATEGY_DEFAULT,
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
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

    store = load_rag_store_from_path(
        path=args.knowledge_path,
    )

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=args.strategy,
    )

    agent = build_rag_qa_agent(
        rag_store=search_engine,
        max_steps=args.max_steps,
    )

    return agent.run(
        args.query,
    )


def main() -> None:
    answer = run_from_args()

    print(
        format_agent_rag_answer(
            answer,
        )
    )


if __name__ == "__main__":
    main()