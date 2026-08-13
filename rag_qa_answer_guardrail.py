from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from rag_answer_composer import compose_rag_answer


INSUFFICIENT_EVIDENCE_ANSWER = "I do not have enough evidence to answer."


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
}


@dataclass(frozen=True)
class RagQaAnswerValidationResult:
    passed: bool
    failure_reasons: list[str]


def normalize_text(
    text: str,
) -> str:
    return " ".join(
        text.lower().split()
    )


def normalize_source(
    source: str,
) -> str:
    return source.replace(
        "\\",
        "/",
    ).lower()


def source_basename(
    source: str,
) -> str:
    normalized = normalize_source(
        source,
    )

    return PurePosixPath(
        normalized,
    ).name


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


def get_evidence_sources(
    evidence: list[dict[str, Any]],
) -> list[str]:
    return [
        source
        for source in [
            get_evidence_source(
                item,
            )
            for item in evidence
        ]
        if source
    ]


def build_source_variants(
    source: str,
) -> set[str]:
    normalized_source = normalize_source(
        source,
    )

    variants = {
        normalized_source,
        source_basename(
            normalized_source,
        ),
    }

    windows_name = PureWindowsPath(
        source,
    ).name

    if windows_name:
        variants.add(
            windows_name.lower(),
        )

    return {
        item
        for item in variants
        if item
    }


def answer_cites_evidence_source(
    *,
    answer: str,
    evidence: list[dict[str, Any]],
) -> bool:
    normalized_answer = normalize_source(
        answer,
    )

    if "source" not in normalized_answer:
        return False

    for source in get_evidence_sources(
        evidence,
    ):
        for variant in build_source_variants(
            source,
        ):
            if variant in normalized_answer:
                return True

    return False


def tokenize_for_overlap(
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

    tokens = set(
        "".join(
            cleaned,
        ).split()
    )

    return {
        token
        for token in tokens
        if len(token) >= 3
        and token not in STOPWORDS
    }


def evidence_text_tokens(
    evidence: list[dict[str, Any]],
) -> set[str]:
    tokens = set()

    for item in evidence:
        tokens.update(
            tokenize_for_overlap(
                get_evidence_text(
                    item,
                )
            )
        )

    return tokens


def answer_has_evidence_overlap(
    *,
    answer: str,
    evidence: list[dict[str, Any]],
    min_overlap_tokens: int = 3,
) -> bool:
    answer_tokens = tokenize_for_overlap(
        answer,
    )

    evidence_tokens = evidence_text_tokens(
        evidence,
    )

    return len(
        answer_tokens & evidence_tokens,
    ) >= min_overlap_tokens


def validate_rag_qa_answer(
    *,
    answer: str,
    evidence: list[dict[str, Any]],
) -> RagQaAnswerValidationResult:
    failure_reasons = []

    if not isinstance(answer, str) or not answer.strip():
        failure_reasons.append(
            "answer must be a non-empty string."
        )

        return RagQaAnswerValidationResult(
            passed=False,
            failure_reasons=failure_reasons,
        )

    if not evidence:
        if normalize_text(
            answer,
        ) != normalize_text(
            INSUFFICIENT_EVIDENCE_ANSWER,
        ):
            failure_reasons.append(
                "answer must use insufficient evidence fallback when evidence is empty."
            )

        return RagQaAnswerValidationResult(
            passed=not failure_reasons,
            failure_reasons=failure_reasons,
        )

    if normalize_text(
        answer,
    ) == normalize_text(
        INSUFFICIENT_EVIDENCE_ANSWER,
    ):
        return RagQaAnswerValidationResult(
            passed=True,
            failure_reasons=[],
        )

    if not answer_cites_evidence_source(
        answer=answer,
        evidence=evidence,
    ):
        failure_reasons.append(
            "answer must cite a retrieved evidence source."
        )

    if not answer_has_evidence_overlap(
        answer=answer,
        evidence=evidence,
    ):
        failure_reasons.append(
            "answer must overlap with retrieved evidence text."
        )

    return RagQaAnswerValidationResult(
        passed=not failure_reasons,
        failure_reasons=failure_reasons,
    )


def build_evidence_fallback_answer(
    *,
    evidence: list[dict[str, Any]],
    query: str = "answer",
) -> str:
    if not evidence:
        return INSUFFICIENT_EVIDENCE_ANSWER

    composed_answer = compose_rag_answer(
        query=query,
        evidence=evidence,
        max_sentences=1,
    )

    return composed_answer.answer