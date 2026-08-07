from pathlib import Path

from rag_store import InMemoryRagStore


SUPPORTED_KNOWLEDGE_FILE_SUFFIXES = {
    ".md",
    ".txt",
}


def is_supported_knowledge_file(path: Path) -> bool:
    if not isinstance(path, Path):
        raise ValueError("path must be a Path.")

    return path.is_file() and path.suffix.lower() in SUPPORTED_KNOWLEDGE_FILE_SUFFIXES


def iter_knowledge_files(path: Path) -> list[Path]:
    if not isinstance(path, Path):
        raise ValueError("path must be a Path.")

    if not path.exists():
        raise ValueError(f"knowledge path does not exist: {path}")

    if path.is_file():
        if is_supported_knowledge_file(path):
            return [path]

        return []

    if path.is_dir():
        return sorted(
            file_path
            for file_path in path.rglob("*")
            if is_supported_knowledge_file(file_path)
        )

    return []


def load_rag_store_from_path(
    *,
    path: str | Path,
    max_chars: int = 1000,
    overlap_chars: int = 100,
) -> InMemoryRagStore:
    knowledge_path = Path(path)

    store = InMemoryRagStore()

    for file_path in iter_knowledge_files(knowledge_path):
        text = file_path.read_text(encoding="utf-8")

        if not text.strip():
            continue

        store.add_document(
            source=str(file_path),
            text=text,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

    return store
