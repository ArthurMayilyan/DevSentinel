import json

import pytest

from rag_eval_loader import (
    RAG_RETRIEVAL_EVAL_CASE_FIELDS,
    load_rag_retrieval_eval_cases_from_json_file,
    parse_rag_retrieval_eval_case,
)


def test_rag_retrieval_eval_case_fields_are_defined():
    assert RAG_RETRIEVAL_EVAL_CASE_FIELDS == {
        "name",
        "query",
        "expected_source_contains",
        "expected_text_contains",
    }


def test_parse_rag_retrieval_eval_case_returns_case():
    case = parse_rag_retrieval_eval_case(
        data={
            "name": "token policy",
            "query": "token expiration",
            "expected_source_contains": "security.md",
            "expected_text_contains": "Tokens must be signed",
        },
        index=0,
    )

    assert case.name == "token policy"
    assert case.query == "token expiration"
    assert case.expected_source_contains == "security.md"
    assert case.expected_text_contains == "Tokens must be signed"


def test_load_rag_retrieval_eval_cases_from_json_file_returns_cases(tmp_path):
    path = tmp_path / "rag_eval_cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=path,
    )

    assert len(cases) == 1
    assert cases[0].name == "token policy"
    assert cases[0].query == "token expiration"


def test_load_rag_retrieval_eval_cases_from_json_file_loads_multiple_cases(tmp_path):
    path = tmp_path / "rag_eval_cases.json"
    path.write_text(
        json.dumps(
            [
                {
                    "name": "token policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Tokens must be signed",
                },
                {
                    "name": "coding style",
                    "query": "small function",
                    "expected_source_contains": "coding.md",
                    "expected_text_contains": "Functions should be small",
                },
            ]
        ),
        encoding="utf-8",
    )

    cases = load_rag_retrieval_eval_cases_from_json_file(
        path=path,
    )

    assert [case.name for case in cases] == [
        "token policy",
        "coding style",
    ]


def test_load_rag_retrieval_eval_cases_rejects_missing_file(tmp_path):
    with pytest.raises(ValueError):
        load_rag_retrieval_eval_cases_from_json_file(
            path=tmp_path / "missing.json",
        )


def test_load_rag_retrieval_eval_cases_rejects_directory(tmp_path):
    with pytest.raises(ValueError):
        load_rag_retrieval_eval_cases_from_json_file(
            path=tmp_path,
        )


def test_load_rag_retrieval_eval_cases_rejects_invalid_json(tmp_path):
    path = tmp_path / "rag_eval_cases.json"
    path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_rag_retrieval_eval_cases_from_json_file(
            path=path,
        )


def test_load_rag_retrieval_eval_cases_rejects_non_list_json(tmp_path):
    path = tmp_path / "rag_eval_cases.json"
    path.write_text(
        json.dumps(
            {
                "name": "token policy",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_rag_retrieval_eval_cases_from_json_file(
            path=path,
        )


def test_load_rag_retrieval_eval_cases_rejects_empty_list(tmp_path):
    path = tmp_path / "rag_eval_cases.json"
    path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_rag_retrieval_eval_cases_from_json_file(
            path=path,
        )


def test_parse_rag_retrieval_eval_case_rejects_missing_required_field():
    with pytest.raises(ValueError):
        parse_rag_retrieval_eval_case(
            data={
                "name": "token policy",
                "query": "token expiration",
                "expected_source_contains": "security.md",
            },
            index=0,
        )


def test_parse_rag_retrieval_eval_case_rejects_unknown_field():
    with pytest.raises(ValueError):
        parse_rag_retrieval_eval_case(
            data={
                "name": "token policy",
                "query": "token expiration",
                "expected_source_contains": "security.md",
                "expected_text_contains": "Tokens must be signed",
                "extra": "unexpected",
            },
            index=0,
        )

        