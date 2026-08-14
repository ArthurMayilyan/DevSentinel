from rag_evidence_extractor import (
    extract_all_evidence,
    extract_latest_evidence,
)
from rag_evidence_extractor import extract_all_evidence_with_provenance


def test_extract_latest_evidence_returns_latest_tool_result():
    evidence = extract_latest_evidence(
        [
            {
                "tool_result": [
                    {
                        "source": "old.md",
                        "text": "Old text.",
                    }
                ],
            },
            {
                "tool_result": [
                    {
                        "source": "new.md",
                        "text": "New text.",
                    }
                ],
            },
        ]
    )

    assert evidence == [
        {
            "source": "new.md",
            "text": "New text.",
        }
    ]


def test_extract_all_evidence_returns_all_tool_results():
    evidence = extract_all_evidence(
        [
            {
                "tool_result": [
                    {
                        "source": "credentials.md",
                        "text": "Credentials must not be hardcoded.",
                    }
                ],
            },
            {
                "tool_result": [
                    {
                        "source": "debug.md",
                        "text": "Debug mode must be disabled in production.",
                    }
                ],
            },
        ]
    )

    assert evidence == [
        {
            "source": "credentials.md",
            "text": "Credentials must not be hardcoded.",
        },
        {
            "source": "debug.md",
            "text": "Debug mode must be disabled in production.",
        },
    ]


def test_extract_all_evidence_deduplicates_repeated_tool_results():
    evidence = extract_all_evidence(
        [
            {
                "tool_result": [
                    {
                        "source": "security.md",
                        "chunk_index": 0,
                        "text": "Security text.",
                    }
                ],
            },
            {
                "tool_result": [
                    {
                        "source": "security.md",
                        "chunk_index": 0,
                        "text": "Security text.",
                    }
                ],
            },
        ]
    )

    assert evidence == [
        {
            "source": "security.md",
            "chunk_index": 0,
            "text": "Security text.",
        }
    ]

def test_extract_all_evidence_with_provenance_reads_query_from_observation_text():
    evidence = extract_all_evidence_with_provenance(
        [
            (
                "Observation from tool `search_knowledge` with arguments "
                "{'query': 'credentials production'}:\n"
                "[{'source': 'security.md', "
                "'text': 'Credentials must not be hardcoded.'}]"
            )
        ],
        strategy="binary-overlap",
    )

    assert evidence == [
        {
            "source": "security.md",
            "chunk_index": None,
            "text": "Credentials must not be hardcoded.",
            "score": None,
            "subquery": "credentials production",
            "subquery_index": 0,
            "strategy": "binary-overlap",
        }
    ]


def test_extract_all_evidence_with_provenance_keeps_same_chunk_for_different_subqueries():
    evidence = extract_all_evidence_with_provenance(
        [
            (
                "Observation from tool `search_knowledge` with arguments "
                "{'query': 'credentials production'}:\n"
                "[{'source': 'security.md', "
                "'chunk_index': 0, "
                "'text': 'Credentials must not be hardcoded. Debug mode must be disabled.'}]"
            ),
            (
                "Observation from tool `search_knowledge` with arguments "
                "{'query': 'debug mode production'}:\n"
                "[{'source': 'security.md', "
                "'chunk_index': 0, "
                "'text': 'Credentials must not be hardcoded. Debug mode must be disabled.'}]"
            ),
        ],
        strategy="binary-overlap",
    )

    assert len(
        evidence,
    ) == 2

    assert evidence[0]["subquery"] == "credentials production"
    assert evidence[0]["subquery_index"] == 0
    assert evidence[1]["subquery"] == "debug mode production"
    assert evidence[1]["subquery_index"] == 1    