import pytest

from rag_loader import (
    SUPPORTED_KNOWLEDGE_FILE_SUFFIXES,
    is_supported_knowledge_file,
    iter_knowledge_files,
    load_rag_store_from_path,
)


def test_supported_knowledge_file_suffixes():
    assert ".md" in SUPPORTED_KNOWLEDGE_FILE_SUFFIXES
    assert ".txt" in SUPPORTED_KNOWLEDGE_FILE_SUFFIXES


def test_is_supported_knowledge_file_accepts_markdown(tmp_path):
    path = tmp_path / "security.md"
    path.write_text("Tokens must be signed.", encoding="utf-8")

    assert is_supported_knowledge_file(path) is True


def test_is_supported_knowledge_file_rejects_unsupported_suffix(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")

    assert is_supported_knowledge_file(path) is False


def test_iter_knowledge_files_returns_single_supported_file(tmp_path):
    path = tmp_path / "security.md"
    path.write_text("Tokens must be signed.", encoding="utf-8")

    assert iter_knowledge_files(path) == [path]


def test_iter_knowledge_files_returns_empty_list_for_unsupported_file(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")

    assert iter_knowledge_files(path) == []


def test_iter_knowledge_files_recursively_finds_supported_files(tmp_path):
    root = tmp_path / "knowledge"
    nested = root / "security"

    nested.mkdir(parents=True)

    first = root / "coding.md"
    second = nested / "tokens.txt"
    ignored = nested / "data.json"

    first.write_text("Use clear code.", encoding="utf-8")
    second.write_text("Tokens must expire.", encoding="utf-8")
    ignored.write_text("{}", encoding="utf-8")

    assert iter_knowledge_files(root) == [
        first,
        second,
    ]


def test_iter_knowledge_files_rejects_missing_path(tmp_path):
    with pytest.raises(ValueError):
        iter_knowledge_files(tmp_path / "missing")


def test_load_rag_store_from_single_file(tmp_path):
    path = tmp_path / "security.md"
    path.write_text("Tokens must be signed and must expire.", encoding="utf-8")

    store = load_rag_store_from_path(path=path)

    results = store.search(query="token expiration")

    assert len(results) == 1
    assert results[0].source == str(path)
    assert results[0].score == 2


def test_load_rag_store_from_directory(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    security = root / "security.md"
    coding = root / "coding.txt"

    security.write_text("Tokens must be signed.", encoding="utf-8")
    coding.write_text("Functions should be small.", encoding="utf-8")

    store = load_rag_store_from_path(path=root)

    security_results = store.search(query="signed token")
    coding_results = store.search(query="small function")

    assert len(security_results) == 1
    assert security_results[0].source == str(security)

    assert len(coding_results) == 1
    assert coding_results[0].source == str(coding)


def test_load_rag_store_skips_empty_files(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()

    empty = root / "empty.md"
    useful = root / "security.md"

    empty.write_text("   ", encoding="utf-8")
    useful.write_text("Tokens must expire.", encoding="utf-8")

    store = load_rag_store_from_path(path=root)

    assert len(store.chunks) == 1
    assert store.chunks[0].source == str(useful)

    