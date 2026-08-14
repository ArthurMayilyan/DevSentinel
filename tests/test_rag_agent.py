from rag_agent import build_rag_qa_agent
from rag_store import InMemoryRagStore
from rag_strategy_factory import build_rag_search_engine_for_strategy


def build_test_store() -> InMemoryRagStore:
    store = InMemoryRagStore()

    store.add_document(
        source="security.md",
        text="Token expiration policy: tokens must be signed and must expire.",
    )

    return store


def test_rag_qa_agent_answers_using_search_knowledge():
    agent = build_rag_qa_agent(
        rag_store=build_test_store(),
    )

    answer = agent.run(
        "token expiration",
    )

    assert "Token expiration policy" in answer
    assert "Source: security.md" in answer


def test_rag_qa_agent_does_not_require_report_written():
    agent = build_rag_qa_agent(
        rag_store=build_test_store(),
    )

    answer = agent.run(
        "token expiration",
    )

    assert answer != "Agent stopped because rejected final answers limit was reached."

def test_rag_qa_agent_accepts_strategy_wrapped_search_engine():
    search_engine = build_rag_search_engine_for_strategy(
        store=build_test_store(),
        strategy="binary-overlap",
    )

    agent = build_rag_qa_agent(
        rag_store=search_engine,
    )

    answer = agent.run(
        "token expiration",
    )

    assert "Token expiration policy" in answer
    assert "Source: security.md" in answer    

def test_rag_qa_agent_returns_short_query_relevant_answer_from_noisy_evidence():
    store = InMemoryRagStore()

    store.add_document(
        source="security.md",
        text=(
            "# Security Policy\n\n"
            "Token expiration policy: tokens must be signed and must expire.\n"
            "Credentials must not be hardcoded in source code.\n"
            "Debug mode must be disabled in production."
        ),
    )

    agent = build_rag_qa_agent(
        rag_store=store,
    )

    answer = agent.run(
        "token expiration",
    )

    assert "Token expiration policy" in answer
    assert "Credentials must not be hardcoded" not in answer
    assert "Debug mode must be disabled" not in answer
    assert "Source: security.md" in answer    


def test_rag_qa_agent_uses_multiple_searches_for_multi_part_question():
    store = InMemoryRagStore()

    store.add_document(
        source="security.md",
        text=(
            "# Security Policy\n\n"
            "Token expiration policy: tokens must be signed and must expire.\n"
            "Credentials must not be hardcoded in source code.\n"
            "Debug mode must be disabled in production."
        ),
    )

    agent = build_rag_qa_agent(
        rag_store=store,
        max_steps=4,
    )

    answer = agent.run(
        "How should credentials and debug mode be handled in production?",
    )

    assert "Credentials must not be hardcoded" in answer
    assert "Debug mode must be disabled" in answer
    assert "Token expiration policy" not in answer
    assert "Source: security.md" in answer    