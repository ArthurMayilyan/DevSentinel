from rag_evidence import (
    deduplicate_evidence_items,
    evidence_item_from_dict,
    evidence_item_to_dict,
)


def test_evidence_item_from_dict_preserves_provenance_fields():
    item = evidence_item_from_dict(
        value={
            "source": "security.md",
            "chunk_index": 0,
            "text": "Credentials must not be hardcoded.",
            "score": 2,
            "subquery": "credentials production",
            "subquery_index": 0,
            "strategy": "binary-overlap",
        }
    )

    assert item.source == "security.md"
    assert item.chunk_index == 0
    assert item.text == "Credentials must not be hardcoded."
    assert item.score == 2
    assert item.subquery == "credentials production"
    assert item.subquery_index == 0
    assert item.strategy == "binary-overlap"


def test_evidence_item_to_dict_round_trips_item():
    item = evidence_item_from_dict(
        value={
            "source": "security.md",
            "text": "Debug mode must be disabled.",
        },
        subquery="debug mode production",
        subquery_index=1,
        strategy="binary-overlap",
    )

    assert evidence_item_to_dict(
        item,
    ) == {
        "source": "security.md",
        "chunk_index": None,
        "text": "Debug mode must be disabled.",
        "score": None,
        "subquery": "debug mode production",
        "subquery_index": 1,
        "strategy": "binary-overlap",
    }


def test_deduplicate_evidence_items_keeps_same_chunk_for_different_subqueries():
    first = evidence_item_from_dict(
        value={
            "source": "security.md",
            "chunk_index": 0,
            "text": "Security policy text.",
        },
        subquery="credentials production",
        subquery_index=0,
    )
    second = evidence_item_from_dict(
        value={
            "source": "security.md",
            "chunk_index": 0,
            "text": "Security policy text.",
        },
        subquery="debug mode production",
        subquery_index=1,
    )

    assert deduplicate_evidence_items(
        [
            first,
            second,
        ],
        keep_subquery_context=True,
    ) == [
        first,
        second,
    ]

    assert deduplicate_evidence_items(
        [
            first,
            second,
        ],
        keep_subquery_context=False,
    ) == [
        first,
    ]


    