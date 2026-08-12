from rag_retrievers import (
    BinaryOverlapRagRetriever,
    HybridLexicalRagRetriever,
    TermFrequencyRagRetriever,
)
from rag_search_engine import RagSearchEngine


RETRIEVAL_STRATEGY_DEFAULT = "default"
RETRIEVAL_STRATEGY_TERM_FREQUENCY = "term-frequency"
RETRIEVAL_STRATEGY_BINARY_OVERLAP = "binary-overlap"
RETRIEVAL_STRATEGY_HYBRID_LEXICAL = "hybrid-lexical"

SUPPORTED_RETRIEVAL_STRATEGIES = {
    RETRIEVAL_STRATEGY_DEFAULT,
    RETRIEVAL_STRATEGY_TERM_FREQUENCY,
    RETRIEVAL_STRATEGY_BINARY_OVERLAP,
    RETRIEVAL_STRATEGY_HYBRID_LEXICAL,
}


def validate_retrieval_strategy(
    strategy: str,
) -> None:
    if not isinstance(strategy, str) or not strategy.strip():
        raise ValueError("strategy must be a non-empty string.")

    if strategy not in SUPPORTED_RETRIEVAL_STRATEGIES:
        raise ValueError(f"unsupported retrieval strategy: {strategy}")


def build_rag_search_engine_for_strategy(
    *,
    store: RagSearchEngine,
    strategy: str,
) -> RagSearchEngine:
    validate_retrieval_strategy(
        strategy,
    )

    if strategy == RETRIEVAL_STRATEGY_DEFAULT:
        return store

    if strategy == RETRIEVAL_STRATEGY_TERM_FREQUENCY:
        return TermFrequencyRagRetriever(
            store=store,
        )

    if strategy == RETRIEVAL_STRATEGY_BINARY_OVERLAP:
        return BinaryOverlapRagRetriever(
            store=store,
        )

    if strategy == RETRIEVAL_STRATEGY_HYBRID_LEXICAL:
        return HybridLexicalRagRetriever(
            store=store,
        )

    raise ValueError(f"unsupported retrieval strategy: {strategy}")