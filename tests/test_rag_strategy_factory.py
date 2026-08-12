import pytest

from rag_retrievers import (
    BinaryOverlapRagRetriever,
    HybridLexicalRagRetriever,
    TermFrequencyRagRetriever,
)
from rag_strategy_factory import (
    RETRIEVAL_STRATEGY_BINARY_OVERLAP,
    RETRIEVAL_STRATEGY_DEFAULT,
    RETRIEVAL_STRATEGY_HYBRID_LEXICAL,
    RETRIEVAL_STRATEGY_TERM_FREQUENCY,
    SUPPORTED_RETRIEVAL_STRATEGIES,
    build_rag_search_engine_for_strategy,
    validate_retrieval_strategy,
)
from rag_store import InMemoryRagStore


def test_supported_retrieval_strategies_contains_runtime_strategies():
    assert SUPPORTED_RETRIEVAL_STRATEGIES == {
        "default",
        "term-frequency",
        "binary-overlap",
        "hybrid-lexical",
    }


def test_validate_retrieval_strategy_accepts_supported_strategy():
    validate_retrieval_strategy(
        RETRIEVAL_STRATEGY_BINARY_OVERLAP,
    )


def test_validate_retrieval_strategy_rejects_unknown_strategy():
    with pytest.raises(ValueError):
        validate_retrieval_strategy(
            "unknown",
        )


def test_build_rag_search_engine_for_default_returns_original_store():
    store = InMemoryRagStore()

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=RETRIEVAL_STRATEGY_DEFAULT,
    )

    assert search_engine is store


def test_build_rag_search_engine_for_term_frequency_returns_retriever():
    store = InMemoryRagStore()

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=RETRIEVAL_STRATEGY_TERM_FREQUENCY,
    )

    assert isinstance(
        search_engine,
        TermFrequencyRagRetriever,
    )


def test_build_rag_search_engine_for_binary_overlap_returns_retriever():
    store = InMemoryRagStore()

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=RETRIEVAL_STRATEGY_BINARY_OVERLAP,
    )

    assert isinstance(
        search_engine,
        BinaryOverlapRagRetriever,
    )


def test_build_rag_search_engine_for_hybrid_lexical_returns_retriever():
    store = InMemoryRagStore()

    search_engine = build_rag_search_engine_for_strategy(
        store=store,
        strategy=RETRIEVAL_STRATEGY_HYBRID_LEXICAL,
    )

    assert isinstance(
        search_engine,
        HybridLexicalRagRetriever,
    )