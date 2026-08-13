from dataclasses import asdict, dataclass
from typing import Any


STOPWORDS = {
    "the",
    "and",
    "for",
    "from",
    "with",
    "that",
    "this",
    "must",
    "not",
    "source",
    "policy",
    "what",
    "how",
    "should",
    "does",
    "about",
}


@dataclass(frozen=True)
class RagComposedAnswer:
    answer: str
    source: str
    selected_sentences: list[str]
    used_evidence_indexes: list[int]
    fallback_used: bool


def normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def tokenize(
    text: str,
) -> set[str]:
    cleaned = []

    for character in text.lower():
        if character.isalnum():
            cleaned.append(
                character,
            )
        else:
            cleaned.append(
                " ",
            )

    return {
        token
        for token in "".join(
            cleaned,
        ).split()
        if len(token) >= 3
        and token not in STOPWORDS
    }


def get_evidence_source(
    item: dict[str, Any],
) -> str:
    for key in [
        "source",
        "file",
        "path",
    ]:
        value = item.get(
            key,
        )

        if isinstance(value, str) and value.strip():
            return value

    return ""


def get_evidence_text(
    item: dict[str, Any],
) -> str:
    for key in [
        "text",
        "content",
        "chunk_text",
        "snippet",
    ]:
        value = item.get(
            key,
        )

        if isinstance(value, str) and value.strip():
            return value

    return ""


def clean_sentence(
    sentence: str,
) -> str:
    lines = []

    for line in sentence.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        lines.append(
            stripped,
        )

    return " ".join(
        lines,
    ).strip()


def split_into_sentences(
    text: str,
) -> list[str]:
    sentences = []
    current = []

    for character in text:
        current.append(
            character,
        )

        if character in {
            ".",
            "!",
            "?",
        }:
            sentence = clean_sentence(
                "".join(
                    current,
                )
            )

            if sentence:
                sentences.append(
                    sentence,
                )

            current = []

    tail = clean_sentence(
        "".join(
            current,
        )
    )

    if tail:
        sentences.append(
            tail,
        )

    return sentences


def score_sentence(
    *,
    query_tokens: set[str],
    sentence: str,
) -> int:
    sentence_tokens = tokenize(
        sentence,
    )

    return len(
        query_tokens & sentence_tokens,
    )


def collect_ranked_sentences(
    *,
    query: str,
    evidence: list[dict[str, Any]],
) -> list[tuple[int, int, str, str]]:
    query_tokens = tokenize(
        query,
    )

    ranked = []

    for evidence_index, item in enumerate(
        evidence,
    ):
        source = get_evidence_source(
            item,
        )
        text = get_evidence_text(
            item,
        )

        if not source or not text:
            continue

        for sentence in split_into_sentences(
            text,
        ):
            score = score_sentence(
                query_tokens=query_tokens,
                sentence=sentence,
            )

            ranked.append(
                (
                    score,
                    evidence_index,
                    source,
                    sentence,
                )
            )

    return sorted(
        ranked,
        key=lambda item: (
            item[0],
            -item[1],
        ),
        reverse=True,
    )


def select_relevant_sentences(
    *,
    query: str,
    evidence: list[dict[str, Any]],
    max_sentences: int = 2,
) -> list[tuple[int, str, str]]:
    if max_sentences <= 0:
        raise ValueError("max_sentences must be greater than 0.")

    ranked = collect_ranked_sentences(
        query=query,
        evidence=evidence,
    )

    selected = []
    seen_sentences = set()

    for score, evidence_index, source, sentence in ranked:
        if score <= 0:
            continue

        normalized_sentence = normalize_text(
            sentence,
        )

        if normalized_sentence in seen_sentences:
            continue

        selected.append(
            (
                evidence_index,
                source,
                sentence,
            )
        )
        seen_sentences.add(
            normalized_sentence,
        )

        if len(
            selected,
        ) >= max_sentences:
            break

    return selected


def select_first_available_sentence(
    evidence: list[dict[str, Any]],
) -> tuple[int, str, str] | None:
    for evidence_index, item in enumerate(
        evidence,
    ):
        source = get_evidence_source(
            item,
        )
        text = get_evidence_text(
            item,
        )

        if not source or not text:
            continue

        sentences = split_into_sentences(
            text,
        )

        if not sentences:
            continue

        return (
            evidence_index,
            source,
            sentences[0],
        )

    return None


def compose_rag_answer(
    *,
    query: str,
    evidence: list[dict[str, Any]],
    max_sentences: int = 1,
) -> RagComposedAnswer:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string.")

    if max_sentences <= 0:
        raise ValueError("max_sentences must be greater than 0.")

    selected = select_relevant_sentences(
        query=query,
        evidence=evidence,
        max_sentences=max_sentences,
    )

    fallback_used = False

    if not selected:
        fallback = select_first_available_sentence(
            evidence,
        )

        if fallback is None:
            return RagComposedAnswer(
                answer="I do not have enough evidence to answer.",
                source="",
                selected_sentences=[],
                used_evidence_indexes=[],
                fallback_used=True,
            )

        selected = [
            fallback,
        ]
        fallback_used = True

    source = selected[0][1]

    selected_sentences = [
        sentence
        for _, _, sentence in selected
    ]

    used_evidence_indexes = []

    for evidence_index, _, _ in selected:
        if evidence_index not in used_evidence_indexes:
            used_evidence_indexes.append(
                evidence_index,
            )

    answer = (
        "\n".join(
            selected_sentences,
        )
        + "\n\n"
        + f"Source: {source}"
    )

    return RagComposedAnswer(
        answer=answer,
        source=source,
        selected_sentences=selected_sentences,
        used_evidence_indexes=used_evidence_indexes,
        fallback_used=fallback_used,
    )


def rag_composed_answer_to_dict(
    answer: RagComposedAnswer,
) -> dict[str, Any]:
    return asdict(
        answer,
    )