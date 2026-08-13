import pytest

from rag_qa_llm import DeterministicRagQaLLM
from rag_qa_llm_factory import (
    RAG_QA_LLM_DETERMINISTIC,
    SUPPORTED_RAG_QA_LLMS,
    build_rag_qa_llm,
    validate_rag_qa_llm_name,
)


def test_supported_rag_qa_llms_contains_deterministic_and_openai():
    assert SUPPORTED_RAG_QA_LLMS == {
        "deterministic",
        "openai",
    }


def test_build_rag_qa_llm_returns_deterministic_llm():
    llm = build_rag_qa_llm(
        name=RAG_QA_LLM_DETERMINISTIC,
        model="gpt-5",
    )

    assert isinstance(
        llm,
        DeterministicRagQaLLM,
    )


def test_validate_rag_qa_llm_name_rejects_unknown_llm():
    with pytest.raises(ValueError):
        validate_rag_qa_llm_name(
            "unknown",
        )