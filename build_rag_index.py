import argparse

from rag_index import build_rag_index_from_path, save_rag_index


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a persistent RAG index."
    )

    parser.add_argument(
        "--knowledge-path",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    return parser


def run_from_args(
    raw_args=None,
) -> dict:
    parser = build_arg_parser()
    args = parser.parse_args(
        raw_args,
    )

    index = build_rag_index_from_path(
        path=args.knowledge_path,
    )

    save_rag_index(
        index=index,
        path=args.output,
    )

    return {
        "knowledge_path": args.knowledge_path,
        "output": args.output,
        "chunks": len(
            index.chunks,
        ),
    }


def main() -> None:
    result = run_from_args()

    print(
        f"Built RAG index: {result['chunks']} chunks"
    )
    print(
        f"Output: {result['output']}"
    )


if __name__ == "__main__":
    main()