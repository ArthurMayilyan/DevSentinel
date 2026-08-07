import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    chunk_index: int
    text: str
    score: int

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source must be a non-empty string.")

        if type(self.chunk_index) is not int:
            raise ValueError("chunk_index must be an integer.")

        if self.chunk_index < 0:
            raise ValueError("chunk_index must be greater than or equal to 0.")

        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("text must be a non-empty string.")

        if type(self.score) is not int:
            raise ValueError("score must be an integer.")

        if self.score < 0:
            raise ValueError("score must be greater than or equal to 0.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "score": self.score,
        }


def normalize_token(token: str) -> str:
    if not isinstance(token, str):
        raise ValueError("token must be a string.")

    normalized = token.lower().strip()

    if not normalized:
        raise ValueError("token must be a non-empty string.")

    if len(normalized) > 7 and normalized.endswith("ation"):
        return normalized[:-5]

    if len(normalized) > 6 and normalized.endswith("ating"):
        return normalized[:-6]

    if len(normalized) > 5 and normalized.endswith("ated"):
        return normalized[:-4]

    if len(normalized) > 5 and normalized.endswith("ate"):
        return normalized[:-3]

    if len(normalized) > 5 and normalized.endswith("ire"):
        return normalized[:-1]

    if len(normalized) > 4 and normalized.endswith("ies"):
        return normalized[:-3] + "y"

    if len(normalized) > 4 and normalized.endswith("es"):
        return normalized[:-2]

    if len(normalized) > 3 and normalized.endswith("s"):
        return normalized[:-1]

    return normalized


def tokenize(text: str) -> set[str]:
    if not isinstance(text, str):
        raise ValueError("text must be a string.")

    raw_tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())

    return {
        normalize_token(token)
        for token in raw_tokens
    }


def chunk_text(
    text: str,
    *,
    max_chars: int = 1000,
    overlap_chars: int = 100,
) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")

    if type(max_chars) is not int:
        raise ValueError("max_chars must be an integer.")

    if type(overlap_chars) is not int:
        raise ValueError("overlap_chars must be an integer.")

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0.")

    if overlap_chars < 0:
        raise ValueError("overlap_chars must be greater than or equal to 0.")

    if overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be smaller than max_chars.")

    normalized_text = text.strip()

    if len(normalized_text) <= max_chars:
        return [normalized_text]

    chunks: list[str] = []
    start = 0

    while start < len(normalized_text):
        end = min(start + max_chars, len(normalized_text))
        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(normalized_text):
            break

        start = end - overlap_chars

    return chunks


class InMemoryRagStore:
    def __init__(self) -> None:
        self._chunks: list[RetrievedChunk] = []

    @property
    def chunks(self) -> list[RetrievedChunk]:
        return list(self._chunks)

    def add_document(
        self,
        *,
        source: str,
        text: str,
        max_chars: int = 1000,
        overlap_chars: int = 100,
    ) -> None:
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string.")

        chunks = chunk_text(
            text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

        for index, chunk in enumerate(chunks):
            self._chunks.append(
                RetrievedChunk(
                    source=source.strip(),
                    chunk_index=index,
                    text=chunk,
                    score=0,
                )
            )

    def search(
        self,
        *,
        query: str,
        top_k: int = 3,
    ) -> list[RetrievedChunk]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string.")

        if type(top_k) is not int:
            raise ValueError("top_k must be an integer.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")

        query_tokens = tokenize(query)
        scored_chunks: list[RetrievedChunk] = []

        for chunk in self._chunks:
            chunk_tokens = tokenize(chunk.text)
            score = len(query_tokens.intersection(chunk_tokens))

            if score > 0:
                scored_chunks.append(
                    RetrievedChunk(
                        source=chunk.source,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        score=score,
                    )
                )

        return sorted(
            scored_chunks,
            key=lambda chunk: (-chunk.score, chunk.source, chunk.chunk_index),
        )[:top_k]

    