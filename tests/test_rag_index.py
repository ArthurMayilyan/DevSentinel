from build_rag_index import run_from_args


def test_run_from_args_builds_rag_index_file(tmp_path):
    knowledge_path = tmp_path / "knowledge_base"
    knowledge_path.mkdir()

    security = knowledge_path / "security.md"
    security.write_text(
        "Credentials must not be hardcoded.",
        encoding="utf-8",
    )

    output_path = tmp_path / "rag_index.json"

    result = run_from_args(
        [
            "--knowledge-path",
            str(
                knowledge_path,
            ),
            "--output",
            str(
                output_path,
            ),
        ]
    )

    assert result["chunks"] == 1
    assert output_path.exists()