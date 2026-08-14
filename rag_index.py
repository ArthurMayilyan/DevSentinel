import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rag_store import InMemoryRagStore, chunk_text


RAG_INDEX_VERSION = 1


@dataclass(frozen=True)
class RagIndexChunk:
    source: str
    chunk_index: int
    text: str


@dataclass(frozen=True)
class RagIndex:
    version: int
    chunks: list[RagIndexChunk]


def iter_text_files(
    path: Path,
) -> list[Path]:
    if path.is_file():
        return [
            path,
        ]

    return sorted(
        [
            item
            for item in path.rglob("*")
            if item.is_file()
            and item.suffix.lower()
            in {
                ".md",
                ".txt",
            }
        ]
    )


def build_rag_index_from_path(
    *,
    path: str,
) -> RagIndex:
    root = Path(
        path,
    )

    if not root.exists():
        raise FileNotFoundError(
            f"knowledge path does not exist: {path}"
        )

    chunks = []

    for file_path in iter_text_files(
        root,
    ):
        text = file_path.read_text(
            encoding="utf-8",
        )

        for chunk_index, chunk in enumerate(
            chunk_text(
                text,
            )
        ):
            chunks.append(
                RagIndexChunk(
                    source=str(
                        file_path,
                    ),
                    chunk_index=chunk_index,
                    text=chunk,
                )
            )

    return RagIndex(
        version=RAG_INDEX_VERSION,
        chunks=chunks,
    )


def save_rag_index(
    *,
    index: RagIndex,
    path: str,
) -> None:
    output_path = Path(
        path,
    )
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            {
                "version": index.version,
                "chunks": [
                    asdict(
                        chunk,
                    )
                    for chunk in index.chunks
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_rag_index(
    *,
    path: str,
) -> RagIndex:
    raw = json.loads(
        Path(
            path,
        ).read_text(
            encoding="utf-8",
        )
    )

    version = raw.get(
        "version",
    )

    if version != RAG_INDEX_VERSION:
        raise ValueError(
            f"unsupported RAG index version: {version}"
        )

    chunks = []

    for item in raw.get(
        "chunks",
        [],
    ):
        chunks.append(
            RagIndexChunk(
                source=item["source"],
                chunk_index=item["chunk_index"],
                text=item["text"],
            )
        )

    return RagIndex(
        version=version,
        chunks=chunks,
    )


def build_store_from_rag_index(
    *,
    index: RagIndex,
) -> InMemoryRagStore:
    store = InMemoryRagStore()

    for chunk in index.chunks:
        store.add_document(
            source=chunk.source,
            text=chunk.text,
        )

    return store


def rag_index_to_dict(
    index: RagIndex,
) -> dict[str, Any]:
    return {
        "version": index.version,
        "chunks": [
            asdict(
                chunk,
            )
            for chunk in index.chunks
        ],
    }