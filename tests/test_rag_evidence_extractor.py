from rag_evidence_extractor import (
    extract_all_evidence,
    extract_latest_evidence,
)


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