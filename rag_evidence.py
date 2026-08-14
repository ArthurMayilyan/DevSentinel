from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RagEvidenceItem:
    source: str
    chunk_index: int | None
    text: str
    score: int | float | None
    subquery: str
    subquery_index: int
    strategy: str


def get_value(
    *,
    value: dict[str, Any],
    keys: list[str],
):
    for key in keys:
        if key not in value:
            continue

        item = value[key]

        if item is not None:
            return item

    return None


def evidence_item_from_dict(
    *,
    value: dict[str, Any],
    subquery: str = "",
    subquery_index: int = -1,
    strategy: str = "",
) -> RagEvidenceItem:
    source = get_value(
        value=value,
        keys=[
            "source",
            "file",
            "path",
        ],
    )

    text = get_value(
        value=value,
        keys=[
            "text",
            "content",
            "chunk_text",
            "snippet",
        ],
    )

    chunk_index = get_value(
        value=value,
        keys=[
            "chunk_index",
            "chunk",
        ],
    )

    score = get_value(
        value=value,
        keys=[
            "score",
        ],
    )

    return RagEvidenceItem(
        source=source if isinstance(source, str) else "",
        chunk_index=chunk_index if isinstance(chunk_index, int) else None,
        text=text if isinstance(text, str) else "",
        score=score if isinstance(score, (int, float)) else None,
        subquery=value.get(
            "subquery",
            subquery,
        )
        if isinstance(
            value.get(
                "subquery",
                subquery,
            ),
            str,
        )
        else subquery,
        subquery_index=value.get(
            "subquery_index",
            subquery_index,
        )
        if isinstance(
            value.get(
                "subquery_index",
                subquery_index,
            ),
            int,
        )
        else subquery_index,
        strategy=value.get(
            "strategy",
            strategy,
        )
        if isinstance(
            value.get(
                "strategy",
                strategy,
            ),
            str,
        )
        else strategy,
    )


def evidence_item_to_dict(
    item: RagEvidenceItem,
) -> dict[str, Any]:
    return asdict(
        item,
    )


def evidence_items_to_dicts(
    items: list[RagEvidenceItem],
) -> list[dict[str, Any]]:
    return [
        evidence_item_to_dict(
            item,
        )
        for item in items
    ]


def evidence_dicts_to_items(
    values: list[dict[str, Any]],
) -> list[RagEvidenceItem]:
    return [
        evidence_item_from_dict(
            value=value,
        )
        for value in values
    ]


def is_valid_evidence_item(
    item: RagEvidenceItem,
) -> bool:
    return bool(
        item.source.strip()
    ) and bool(
        item.text.strip()
    )


def deduplicate_evidence_items(
    items: list[RagEvidenceItem],
    *,
    keep_subquery_context: bool = True,
) -> list[RagEvidenceItem]:
    deduplicated = []
    seen = set()

    for item in items:
        if keep_subquery_context:
            key = (
                item.source,
                item.chunk_index,
                item.text,
                item.subquery_index,
                item.subquery,
            )
        else:
            key = (
                item.source,
                item.chunk_index,
                item.text,
            )

        if key in seen:
            continue

        deduplicated.append(
            item,
        )
        seen.add(
            key,
        )

    return deduplicated