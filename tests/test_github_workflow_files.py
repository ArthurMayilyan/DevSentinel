from pathlib import Path


def test_rag_eval_github_workflow_exists():
    workflow_path = Path(".github/workflows/rag-eval.yml")

    assert workflow_path.is_file()


def test_rag_eval_github_workflow_uploads_artifacts():
    workflow_path = Path(".github/workflows/rag-eval.yml")

    workflow = workflow_path.read_text(
        encoding="utf-8",
    )

    assert "actions/upload-artifact@v4" in workflow
    assert "eval_suite_artifacts" in workflow
    assert "python scripts/run_ci_checks.py" in workflow
    assert "actions/setup-python@v7" in workflow
    assert "actions/checkout@v7" in workflow
    assert 'cache: "pip"' not in workflow
    assert "cache: 'pip'" not in workflow
    assert "eval_suite_artifacts" in workflow    
