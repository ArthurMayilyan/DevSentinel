import json
from pathlib import Path

import pytest

from run_rag_eval_profiles import (
    build_profile_artifact_paths,
    build_profile_artifacts_dir,
    build_profile_run_summary,
    discover_profile_configs,
    ensure_artifact_directories,
    format_artifact_link_path,
    format_profiles_artifact_index,
    format_profiles_markdown_summary,
    format_profiles_summary,
    get_profile_quality_gate_status,
    run_from_args,
    run_profile_configs,
    should_fail_due_to_profiles_quality_gate,
    write_github_step_summary,
    write_suite_artifacts,
)

def create_noisy_eval_fixture(
    tmp_path: Path,
) -> tuple[Path, Path]:
    knowledge_path = tmp_path / "knowledge_base_noisy"
    knowledge_path.mkdir()

    token_noise = knowledge_path / "noise_tokens.md"
    token_noise.write_text(
        "token token token token token token token token",
        encoding="utf-8",
    )

    security = knowledge_path / "security.md"
    security.write_text(
        "Token expiration policy: tokens must be signed and must expire.",
        encoding="utf-8",
    )

    function_noise = knowledge_path / "noise_functions.md"
    function_noise.write_text(
        "function function function function function function",
        encoding="utf-8",
    )

    coding = knowledge_path / "coding.md"
    coding.write_text(
        "Small function guidelines: functions should be small and readable.",
        encoding="utf-8",
    )

    cases_path = tmp_path / "noisy_rag_eval_cases.json"
    cases_path.write_text(
        json.dumps(
            [
                {
                    "name": "token expiration policy",
                    "query": "token expiration",
                    "expected_source_contains": "security.md",
                    "expected_text_contains": "Token expiration policy",
                },
                {
                    "name": "small function guideline",
                    "query": "small function",
                    "expected_source_contains": "coding.md",
                    "expected_text_contains": "Small function guidelines",
                },
            ]
        ),
        encoding="utf-8",
    )

    return knowledge_path, cases_path


def write_profile_config(
    *,
    config_dir: Path,
    name: str,
    knowledge_path: Path,
    cases_path: Path,
    baseline_strategy: str,
    strategies: list[str],
    max_regressed_cases: int | None = None,
    min_improved_cases: int | None = None,
) -> Path:
    config_path = config_dir / name

    config = {
        "knowledge_path": str(knowledge_path),
        "cases": str(cases_path),
        "baseline_strategy": baseline_strategy,
        "strategies": strategies,
        "top_k": 3,
        "summary_only": True,
    }

    if max_regressed_cases is not None:
        config["max_regressed_cases"] = max_regressed_cases

    if min_improved_cases is not None:
        config["min_improved_cases"] = min_improved_cases

    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    return config_path


def test_discover_profile_configs_returns_json_files_sorted(tmp_path):
    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    second = config_dir / "b.json"
    second.write_text("{}", encoding="utf-8")

    first = config_dir / "a.json"
    first.write_text("{}", encoding="utf-8")

    ignored = config_dir / "notes.txt"
    ignored.write_text("ignored", encoding="utf-8")

    assert [
        path.name
        for path in discover_profile_configs(
            str(config_dir),
        )
    ] == [
        "a.json",
        "b.json",
    ]


def test_discover_profile_configs_rejects_empty_directory(tmp_path):
    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    with pytest.raises(ValueError):
        discover_profile_configs(
            str(config_dir),
        )


def test_get_profile_quality_gate_status_returns_not_configured():
    assert get_profile_quality_gate_status({}) == "not_configured"


def test_get_profile_quality_gate_status_returns_passed():
    assert (
        get_profile_quality_gate_status(
            {
                "quality_gate": {
                    "passed": True,
                },
            }
        )
        == "passed"
    )


def test_get_profile_quality_gate_status_returns_failed():
    assert (
        get_profile_quality_gate_status(
            {
                "quality_gate": {
                    "passed": False,
                },
            }
        )
        == "failed"
    )


def test_build_profile_run_summary_extracts_key_fields(tmp_path):
    config_path = tmp_path / "profile.json"

    summary = build_profile_run_summary(
        config_path=config_path,
        output={
            "best_strategy": "binary-overlap",
            "best_accepted_strategy": "binary-overlap",
            "quality_gate": {
                "passed": True,
            },
        },
    )

    assert summary == {
        "profile": "profile.json",
        "config_path": str(config_path),
        "best_strategy": "binary-overlap",
        "best_accepted_strategy": "binary-overlap",
        "quality_gate_status": "passed",
        "quality_gate": {
            "passed": True,
        },
    }


def test_run_profile_configs_returns_passing_summary(tmp_path):
    knowledge_path, cases_path = create_noisy_eval_fixture(
        tmp_path,
    )

    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    config_path = write_profile_config(
        config_dir=config_dir,
        name="passing.json",
        knowledge_path=knowledge_path,
        cases_path=cases_path,
        baseline_strategy="term-frequency",
        strategies=[
            "binary-overlap",
        ],
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    summary = run_profile_configs(
        [
            config_path,
        ]
    )

    artifacts_dir = tmp_path / "artifacts"

    summary = run_profile_configs(
        [
            config_path,
        ],
        artifacts_dir=artifacts_dir,
    )    

    assert summary["passed"] is True
    assert summary["failed_profiles"] == []
    assert summary["profiles"][0]["profile"] == "passing.json"
    assert summary["profiles"][0]["quality_gate_status"] == "passed"
    assert summary["profiles"][0]["best_accepted_strategy"] == "binary-overlap"

    profile_summary = summary["profiles"][0]

    assert "artifacts" in profile_summary
    assert Path(profile_summary["artifacts"]["comparison_json"]).is_file()
    assert Path(profile_summary["artifacts"]["report_markdown"]).is_file()    


def test_run_profile_configs_returns_failing_summary(tmp_path):
    knowledge_path, cases_path = create_noisy_eval_fixture(
        tmp_path,
    )

    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    config_path = write_profile_config(
        config_dir=config_dir,
        name="failing.json",
        knowledge_path=knowledge_path,
        cases_path=cases_path,
        baseline_strategy="binary-overlap",
        strategies=[
            "term-frequency",
        ],
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    summary = run_profile_configs(
        [
            config_path,
        ]
    )

    assert summary["passed"] is False
    assert summary["failed_profiles"] == [
        "failing.json",
    ]
    assert summary["profiles"][0]["quality_gate_status"] == "failed"
    assert summary["profiles"][0]["best_accepted_strategy"] is None


def test_format_profiles_summary_formats_passing_summary():
    summary = {
        "profiles": [
            {
                "profile": "passing.json",
                "quality_gate_status": "passed",
                "best_accepted_strategy": "binary-overlap",
            }
        ],
        "failed_profiles": [],
        "passed": True,
    }

    assert format_profiles_summary(summary) == "\n".join(
        [
            "RAG eval profiles",
            "profile                         quality_gate  best_accepted_strategy",
            "passing.json                    passed        binary-overlap",
            "",
            "Overall: passed",
        ]
    )


def test_format_profiles_summary_formats_failed_summary():
    summary = {
        "profiles": [
            {
                "profile": "failing.json",
                "quality_gate_status": "failed",
                "best_accepted_strategy": None,
            }
        ],
        "failed_profiles": [
            "failing.json",
        ],
        "passed": False,
    }

    assert format_profiles_summary(summary) == "\n".join(
        [
            "RAG eval profiles",
            "profile                         quality_gate  best_accepted_strategy",
            "failing.json                    failed        None",
            "",
            "Overall: failed",
            "Failed profiles: failing.json",
        ]
    )


def test_should_fail_due_to_profiles_quality_gate_returns_false_when_flag_disabled():
    assert (
        should_fail_due_to_profiles_quality_gate(
            summary={
                "passed": False,
            },
            fail_on_quality_gate=False,
        )
        is False
    )


def test_should_fail_due_to_profiles_quality_gate_returns_false_when_summary_passed():
    assert (
        should_fail_due_to_profiles_quality_gate(
            summary={
                "passed": True,
            },
            fail_on_quality_gate=True,
        )
        is False
    )


def test_should_fail_due_to_profiles_quality_gate_returns_true_when_summary_failed():
    assert (
        should_fail_due_to_profiles_quality_gate(
            summary={
                "passed": False,
            },
            fail_on_quality_gate=True,
        )
        is True
    )


def test_run_from_args_writes_json_summary(tmp_path):
    knowledge_path, cases_path = create_noisy_eval_fixture(
        tmp_path,
    )

    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    write_profile_config(
        config_dir=config_dir,
        name="passing.json",
        knowledge_path=knowledge_path,
        cases_path=cases_path,
        baseline_strategy="term-frequency",
        strategies=[
            "binary-overlap",
        ],
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    output_path = tmp_path / "profiles_summary.json"

    summary = run_from_args(
        [
            "--config-dir",
            str(config_dir),
            "--output",
            str(output_path),
        ]
    )

    assert summary["passed"] is True
    assert output_path.is_file()

    saved_summary = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved_summary["passed"] is True

def test_build_profile_artifacts_dir_uses_config_stem(tmp_path):
    artifacts_dir = tmp_path / "artifacts"
    config_path = tmp_path / "rag_strategy_noisy.json"

    assert build_profile_artifacts_dir(
        artifacts_dir=artifacts_dir,
        config_path=config_path,
    ) == artifacts_dir / "rag_strategy_noisy"

def test_build_profile_artifact_paths_returns_expected_paths(tmp_path):
    artifacts_dir = tmp_path / "artifacts"
    config_path = tmp_path / "rag_strategy_noisy.json"

    paths = build_profile_artifact_paths(
        artifacts_dir=artifacts_dir,
        config_path=config_path,
    )

    assert paths == {
        "profile_dir": artifacts_dir / "rag_strategy_noisy",
        "comparison_json": artifacts_dir / "rag_strategy_noisy" / "comparison.json",
        "report_markdown": artifacts_dir / "rag_strategy_noisy" / "report.md",
    }

def test_ensure_artifact_directories_creates_profile_dir(tmp_path):
    artifact_paths = {
        "profile_dir": tmp_path / "artifacts" / "profile",
        "comparison_json": tmp_path / "artifacts" / "profile" / "comparison.json",
        "report_markdown": tmp_path / "artifacts" / "profile" / "report.md",
    }

    ensure_artifact_directories(
        artifact_paths=artifact_paths,
    )

    assert artifact_paths["profile_dir"].is_dir()

def test_format_profiles_markdown_summary_formats_passing_summary():
    summary = {
        "profiles": [
            {
                "profile": "passing.json",
                "quality_gate_status": "passed",
                "best_accepted_strategy": "binary-overlap",
            }
        ],
        "failed_profiles": [],
        "passed": True,
    }

    assert format_profiles_markdown_summary(summary) == "\n".join(
        [
            "# RAG Eval Profiles Summary",
            "",
            "| Profile | Quality gate | Best accepted strategy |",
            "|---|---|---|",
            "| passing.json | passed | binary-overlap |",
            "",
            "Overall: **passed**",
            "",
        ]
    )

def test_format_profiles_markdown_summary_formats_failed_summary():
    summary = {
        "profiles": [
            {
                "profile": "failing.json",
                "quality_gate_status": "failed",
                "best_accepted_strategy": None,
            }
        ],
        "failed_profiles": [
            "failing.json",
        ],
        "passed": False,
    }

    assert format_profiles_markdown_summary(summary) == "\n".join(
        [
            "# RAG Eval Profiles Summary",
            "",
            "| Profile | Quality gate | Best accepted strategy |",
            "|---|---|---|",
            "| failing.json | failed | None |",
            "",
            "Overall: **failed**",
            "",
            "Failed profiles: failing.json",
            "",
        ]
    )

def test_write_suite_artifacts_writes_json_markdown_and_index(tmp_path):
    artifacts_dir = tmp_path / "artifacts"

    summary = {
        "profiles": [
            {
                "profile": "passing.json",
                "quality_gate_status": "passed",
                "best_accepted_strategy": "binary-overlap",
                "artifacts": {
                    "report_markdown": "artifacts\\passing\\report.md",
                    "comparison_json": "artifacts\\passing\\comparison.json",
                },
            }
        ],
        "failed_profiles": [],
        "passed": True,
    }

    write_suite_artifacts(
        summary=summary,
        artifacts_dir=artifacts_dir,
    )

    json_path = artifacts_dir / "profiles_summary.json"
    markdown_path = artifacts_dir / "profiles_summary.md"
    index_path = artifacts_dir / "index.md"

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert index_path.is_file()

    saved_summary = json.loads(
        json_path.read_text(
            encoding="utf-8",
        )
    )

    assert saved_summary["passed"] is True

    assert markdown_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Eval Profiles Summary")

    index_content = index_path.read_text(
        encoding="utf-8",
    )

    assert index_content.startswith("# RAG Eval Artifact Index")
    assert "Overall: **passed**" in index_content
    assert "passing.json" in index_content
    assert "binary-overlap" in index_content
    assert "artifacts/passing/report.md" in index_content
    assert "artifacts/passing/comparison.json" in index_content


def test_run_profile_configs_writes_profile_artifacts_when_artifacts_dir_is_provided(tmp_path):
    knowledge_path, cases_path = create_noisy_eval_fixture(
        tmp_path,
    )

    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    config_path = write_profile_config(
        config_dir=config_dir,
        name="passing.json",
        knowledge_path=knowledge_path,
        cases_path=cases_path,
        baseline_strategy="term-frequency",
        strategies=[
            "binary-overlap",
        ],
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    artifacts_dir = tmp_path / "artifacts"

    summary = run_profile_configs(
        [
            config_path,
        ],
        artifacts_dir=artifacts_dir,
    )

    profile_summary = summary["profiles"][0]

    assert profile_summary["artifacts"] == {
        "comparison_json": str(
            artifacts_dir / "passing" / "comparison.json"
        ),
        "report_markdown": str(
            artifacts_dir / "passing" / "report.md"
        ),
    }

    assert (artifacts_dir / "passing" / "comparison.json").is_file()
    assert (artifacts_dir / "passing" / "report.md").is_file()                        

def test_run_from_args_writes_artifacts_dir(tmp_path):
    knowledge_path, cases_path = create_noisy_eval_fixture(
        tmp_path,
    )

    config_dir = tmp_path / "eval_configs"
    config_dir.mkdir()

    write_profile_config(
        config_dir=config_dir,
        name="passing.json",
        knowledge_path=knowledge_path,
        cases_path=cases_path,
        baseline_strategy="term-frequency",
        strategies=[
            "binary-overlap",
        ],
        max_regressed_cases=0,
        min_improved_cases=1,
    )

    artifacts_dir = tmp_path / "artifacts"

    summary = run_from_args(
        [
            "--config-dir",
            str(config_dir),
            "--artifacts-dir",
            str(artifacts_dir),
        ]
    )

    assert summary["passed"] is True
    assert (artifacts_dir / "profiles_summary.json").is_file()
    assert (artifacts_dir / "profiles_summary.md").is_file()
    assert (artifacts_dir / "index.md").is_file()
    assert (artifacts_dir / "passing" / "comparison.json").is_file()
    assert (artifacts_dir / "passing" / "report.md").is_file()    

def test_format_artifact_link_path_normalizes_windows_separators():
    assert (
        format_artifact_link_path(
            "rag_eval_artifacts\\passing\\report.md"
        )
        == "rag_eval_artifacts/passing/report.md"
    )

def test_format_profiles_artifact_index_formats_artifact_links():
    summary = {
        "profiles": [
            {
                "profile": "passing.json",
                "quality_gate_status": "passed",
                "best_accepted_strategy": "binary-overlap",
                "artifacts": {
                    "report_markdown": "rag_eval_artifacts\\passing\\report.md",
                    "comparison_json": "rag_eval_artifacts\\passing\\comparison.json",
                },
            }
        ],
        "failed_profiles": [],
        "passed": True,
    }

    assert format_profiles_artifact_index(summary) == "\n".join(
        [
            "# RAG Eval Artifact Index",
            "",
            "Overall: **passed**",
            "",
            "| Profile | Quality gate | Best accepted strategy | Report | JSON |",
            "|---|---|---|---|---|",
            "| passing.json | passed | binary-overlap | rag_eval_artifacts/passing/report.md | rag_eval_artifacts/passing/comparison.json |",
            "",
        ]
    )


def test_format_profiles_artifact_index_includes_failed_profiles():
    summary = {
        "profiles": [
            {
                "profile": "failing.json",
                "quality_gate_status": "failed",
                "best_accepted_strategy": None,
                "artifacts": {
                    "report_markdown": "artifacts/failing/report.md",
                    "comparison_json": "artifacts/failing/comparison.json",
                },
            }
        ],
        "failed_profiles": [
            "failing.json",
        ],
        "passed": False,
    }

    assert format_profiles_artifact_index(summary) == "\n".join(
        [
            "# RAG Eval Artifact Index",
            "",
            "Overall: **failed**",
            "",
            "| Profile | Quality gate | Best accepted strategy | Report | JSON |",
            "|---|---|---|---|---|",
            "| failing.json | failed | None | artifacts/failing/report.md | artifacts/failing/comparison.json |",
            "",
            "Failed profiles: failing.json",
            "",
        ]
    )


def test_write_github_step_summary_returns_false_when_env_var_is_missing():
    written = write_github_step_summary(
        summary={
            "profiles": [],
            "failed_profiles": [],
            "passed": True,
        },
        env={},
    )

    assert written is False

def test_write_github_step_summary_writes_summary_file(tmp_path):
    summary_path = tmp_path / "github_step_summary.md"

    written = write_github_step_summary(
        summary={
            "profiles": [
                {
                    "profile": "passing.json",
                    "quality_gate_status": "passed",
                    "best_accepted_strategy": "binary-overlap",
                }
            ],
            "failed_profiles": [],
            "passed": True,
        },
        env={
            "GITHUB_STEP_SUMMARY": str(summary_path),
        },
    )

    assert written is True
    assert summary_path.is_file()

    assert summary_path.read_text(
        encoding="utf-8",
    ).startswith("# RAG Eval Profiles Summary")

                        