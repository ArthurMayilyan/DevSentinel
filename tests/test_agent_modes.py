import pytest

from agent_modes import (
    AGENT_MODE_CODE_REVIEW,
    AGENT_MODE_RAG_QA,
    get_agent_mode_spec,
    list_agent_modes,
    validate_agent_mode,
)

def test_validate_agent_mode_accepts_supported_mode():
    validate_agent_mode(
        AGENT_MODE_RAG_QA,
    )


def test_validate_agent_mode_rejects_unknown_mode():
    with pytest.raises(ValueError):
        validate_agent_mode(
            "unknown",
        )


def test_get_agent_mode_spec_returns_rag_qa_spec():
    spec = get_agent_mode_spec(
        AGENT_MODE_RAG_QA,
    )

    assert spec.name == AGENT_MODE_RAG_QA
    assert spec.requires_knowledge_path is True
    assert spec.supports_index_path is True
    assert spec.supports_strategy is True
    assert spec.supports_llm is True


def test_list_agent_modes_includes_registered_modes():
    modes = list_agent_modes()

    assert [
        mode.name
        for mode in modes
    ] == [
        AGENT_MODE_CODE_REVIEW,
        AGENT_MODE_RAG_QA,
    ]


def test_get_agent_mode_spec_returns_code_review_spec():
    spec = get_agent_mode_spec(
        AGENT_MODE_CODE_REVIEW,
    )

    assert spec.name == AGENT_MODE_CODE_REVIEW
    assert spec.requires_knowledge_path is False
    assert spec.supports_index_path is False
    assert spec.supports_strategy is False
    assert spec.supports_llm is True


def test_list_agent_modes_includes_registered_modes():
    modes = list_agent_modes()

    assert [
        mode.name
        for mode in modes
    ] == [
        AGENT_MODE_CODE_REVIEW,
        AGENT_MODE_RAG_QA,
    ]        