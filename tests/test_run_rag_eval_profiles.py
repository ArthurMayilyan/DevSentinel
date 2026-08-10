import json
from pathlib import Path

import pytest

from run_rag_eval_profiles import (
    build_profile_run_summary,
    discover_profile_configs,
    format_profiles_summary,
    get_profile_quality_gate_status,
    run_from_args,
    run_profile_configs,
    should_fail_due_to_profiles_quality_gate,
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

    assert summary["passed"] is True
    assert summary["failed_profiles"] == []
    assert summary["profiles"][0]["profile"] == "passing.json"
    assert summary["profiles"][0]["quality_gate_status"] == "passed"
    assert summary["profiles"][0]["best_accepted_strategy"] == "binary-overlap"


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

    