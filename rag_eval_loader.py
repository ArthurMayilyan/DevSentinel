import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from rag_eval import RagRetrievalEvalCase


RAG_RETRIEVAL_EVAL_CASE_FIELDS = {
    "name",
    "query",
    "expected_source_contains",
    "expected_text_contains",
}


def parse_rag_retrieval_eval_case(
    *,
    data: Any,
    index: int,
) -> RagRetrievalEvalCase:
    if not isinstance(data, dict):
        raise ValueError(f"case at index {index} must be an object.")

    data_fields = set(data)

    missing_fields = RAG_RETRIEVAL_EVAL_CASE_FIELDS - data_fields
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"case at index {index} is missing required fields: {missing}."
        )

    unknown_fields = data_fields - RAG_RETRIEVAL_EVAL_CASE_FIELDS
    if unknown_fields:
        unknown = ", ".join(sorted(unknown_fields))
        raise ValueError(
            f"case at index {index} contains unknown fields: {unknown}."
        )

    return RagRetrievalEvalCase(
        name=data["name"],
        query=data["query"],
        expected_source_contains=data["expected_source_contains"],
        expected_text_contains=data["expected_text_contains"],
    )


def load_rag_retrieval_eval_cases_from_json_file(
    *,
    path: str | Path,
) -> list[RagRetrievalEvalCase]:
    cases_path = Path(path)

    if not cases_path.exists():
        raise ValueError(f"RAG eval cases file does not exist: {cases_path}")

    if not cases_path.is_file():
        raise ValueError(f"RAG eval cases path must be a file: {cases_path}")

    try:
        raw_data = json.loads(
            cases_path.read_text(encoding="utf-8")
        )
    except JSONDecodeError as error:
        raise ValueError(
            f"RAG eval cases file contains invalid JSON: {cases_path}"
        ) from error

    if not isinstance(raw_data, list):
        raise ValueError("RAG eval cases JSON must contain a list.")

    if not raw_data:
        raise ValueError("RAG eval cases JSON must not be empty.")

    return [
        parse_rag_retrieval_eval_case(
            data=item,
            index=index,
        )
        for index, item in enumerate(raw_data)
    ]

