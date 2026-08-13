import json

import pytest

from rag_agent_eval import (
    RagAgentEvalCase,
    answer_contains_all_expected_text,
    evaluate_rag_agent_case,
    evaluate_rag_agent_cases,
    find_forbidden_answer_matches,
    load_rag_agent_eval_cases_from_json_file,
    trace_has_search_knowledge_call,
)


def test_answer_contains_all_expected_text_detects_all_expected_items():
    assert (
        answer_contains_all_expected_text(
            answer=(
                "Token expiration policy: tokens must be signed "
                "and must expire.\n\nSource: security.md"
            ),
            expected_answer_contains=[
                "Token expiration policy",
                "tokens must be signed",
                "must expire",
            ],
        )
        is True
    )


def test_answer_contains_all_expected_text_returns_false_when_item_missing():
    assert (
        answer_contains_all_expected_text(
            answer="Token expiration policy: tokens must be signed.",
            expected_answer_contains=[
                "Token expiration policy",
                "must expire",
            ],
        )
        is False
    )


def test_find_forbidden_answer_matches_detects_unsupported_text():
    assert find_forbidden_answer_matches(
        answer="Tokens expire after 24 hours using OAuth.",
        forbidden_answer_contains=[
            "24 hours",
            "OAuth",
            "refresh token",
        ],
    ) == [
        "24 hours",
        "OAuth",
    ]


def test_trace_has_search_knowledge_call_detects_tool_call():
    assert (
        trace_has_search_knowledge_call(
            [
                {
                    "step": 1,
                    "llm_output": {
                        "type": "tool_call",
                        "tool": "search_knowledge",
                        "arguments": {
                            "query": "token expiration",
                        },
                    },
                }
            ]
        )
        is True
    )


def test_trace_has_search_knowledge_call_returns_false_when_missing():
    assert (
        trace_has_search_knowledge_call(
            [
                {
                    "step": 1,
                    "llm_output": {
                        "type": "final_answer",
                        "answer": "No tool call.",
                    },
                }
            ]
        )
        is False
    )


def test_evaluate_rag_agent_case_passes_valid_agent_answer():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
            "tokens must be signed",
            "must expire",
        ],
        forbidden_answer_contains=[
            "24 hours",
        ],
    )

    result = evaluate_rag_agent_case(
        case=case,
        answer=(
            "Token expiration policy: tokens must be signed "
            "and must expire.\n\nSource: security.md"
        ),
        trace_steps=[
            {
                "tool": "search_knowledge",
            }
        ],
    )

    assert result.passed is True
    assert result.search_knowledge_called is True
    assert result.failure_reasons == []


def test_evaluate_rag_agent_case_fails_when_search_knowledge_not_called():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
        ],
        forbidden_answer_contains=[],
    )

    result = evaluate_rag_agent_case(
        case=case,
        answer="Token expiration policy.\n\nSource: security.md",
        trace_steps=[],
    )

    assert result.passed is False
    assert result.search_knowledge_called is False
    assert "Agent did not call search_knowledge." in result.failure_reasons


def test_evaluate_rag_agent_case_fails_when_source_missing():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
        ],
        forbidden_answer_contains=[],
    )

    result = evaluate_rag_agent_case(
        case=case,
        answer="Token expiration policy.",
        trace_steps=[
            {
                "tool": "search_knowledge",
            }
        ],
    )

    assert result.passed is False
    assert "Answer did not cite a source." in result.failure_reasons


def test_evaluate_rag_agent_case_fails_when_expected_text_missing():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "must expire",
        ],
        forbidden_answer_contains=[],
    )

    result = evaluate_rag_agent_case(
        case=case,
        answer="Token expiration policy.\n\nSource: security.md",
        trace_steps=[
            {
                "tool": "search_knowledge",
            }
        ],
    )

    assert result.passed is False
    assert "Answer did not contain all expected text." in result.failure_reasons


def test_evaluate_rag_agent_case_fails_when_forbidden_text_present():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
        ],
        forbidden_answer_contains=[
            "24 hours",
        ],
    )

    result = evaluate_rag_agent_case(
        case=case,
        answer="Token expiration policy says tokens expire after 24 hours.\n\nSource: security.md",
        trace_steps=[
            {
                "tool": "search_knowledge",
            }
        ],
    )

    assert result.passed is False
    assert any(
        "forbidden text" in reason
        for reason in result.failure_reasons
    )


def test_evaluate_rag_agent_cases_summarizes_results():
    case = RagAgentEvalCase(
        name="agent token expiration answer",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
        ],
        forbidden_answer_contains=[],
    )

    summary = evaluate_rag_agent_cases(
        cases=[
            case,
        ],
        answers_by_case_name={
            "agent token expiration answer": "Token expiration policy.\n\nSource: security.md",
        },
        trace_steps_by_case_name={
            "agent token expiration answer": [
                {
                    "tool": "search_knowledge",
                }
            ],
        },
    )

    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert summary.failed_cases == 0
    assert summary.agent_answer_accuracy == 1.0


def test_evaluate_rag_agent_cases_rejects_empty_cases():
    with pytest.raises(ValueError):
        evaluate_rag_agent_cases(
            cases=[],
            answers_by_case_name={},
            trace_steps_by_case_name={},
        )


def test_evaluate_rag_agent_cases_rejects_missing_answer():
    case = RagAgentEvalCase(
        name="missing answer case",
        query="token expiration",
        expected_answer_contains=[
            "Token expiration policy",
        ],
        forbidden_answer_contains=[],
    )

    with pytest.raises(ValueError):
        evaluate_rag_agent_cases(
            cases=[
                case,
            ],
            answers_by_case_name={},
            trace_steps_by_case_name={
                "missing answer case": [],
            },
        )


def test_load_rag_agent_eval_cases_from_json_file_loads_cases(tmp_path):
    cases_path = tmp_path / "rag_agent_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "agent token expiration answer",
                    "query": "token expiration",
                    "expected_answer_contains": [
                        "Token expiration policy",
                    ],
                    "forbidden_answer_contains": [
                        "24 hours",
                    ],
                }
            ]
        ),
        encoding="utf-8",
    )

    cases = load_rag_agent_eval_cases_from_json_file(
        str(cases_path),
    )

    assert len(cases) == 1
    assert cases[0].name == "agent token expiration answer"
    assert cases[0].expected_answer_contains == [
        "Token expiration policy",
    ]
    assert cases[0].forbidden_answer_contains == [
        "24 hours",
    ]