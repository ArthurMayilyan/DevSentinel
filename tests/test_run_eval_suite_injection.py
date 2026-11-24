import json
from pathlib import Path

import pytest

from devsentinel.cli.run_eval_suite import (
    build_eval_suite_summary,
    format_eval_suite_markdown_summary,
    format_eval_suite_summary,
    load_eval_suite_config,
    run_injection_suite,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

INJECTION_CONFIG = {
    "control_project": str(REPOSITORY_ROOT / "sample_project"),
    "attack_project": str(REPOSITORY_ROOT / "adversarial_project"),
    "cases": str(REPOSITORY_ROOT / "eval_cases" / "injection_eval_cases.json"),
    "repetitions": 1,
}


def passing_layer_outputs() -> dict:
    gate = {"passed": True}
    summary = {
        "answer_accuracy": 1.0,
        "grounding_accuracy": 1.0,
        "agent_answer_accuracy": 1.0,
        "passed_cases": 1,
        "failed_cases": 0,
        "total_cases": 1,
    }

    return {
        "retrieval_summary": {"passed": True, "failed_profiles": [], "profiles": []},
        "answer_output": {"quality_gate": gate, "strategy": "s", "summary": summary},
        "grounding_output": {"quality_gate": gate, "strategy": "s", "summary": summary},
        "agent_output": {"quality_gate": gate, "strategy": "s", "summary": summary},
    }


def injection_output(*, passed: bool) -> dict:
    return {
        "metadata": {"mode": "dry_run", "repetitions_per_condition": 1},
        "quality_gate": {
            "passed": passed,
            "canary_leak_runs": 0 if passed else 1,
            "out_of_root_attempts_that_returned_content": 0,
            "premature_completions_not_blocked": 0,
        },
    }


def test_summary_without_injection_section_is_unchanged():
    summary = build_eval_suite_summary(**passing_layer_outputs())

    assert "injection" not in summary
    assert summary["passed"] is True


def test_failing_injection_gate_fails_suite():
    summary = build_eval_suite_summary(
        **passing_layer_outputs(),
        injection_output=injection_output(passed=False),
    )

    assert summary["passed"] is False
    assert summary["injection"]["passed"] is False
    assert "injection (dry_run): failed" in format_eval_suite_summary(summary)
    assert "## Injection eval" in format_eval_suite_markdown_summary(summary)


def test_default_suite_config_includes_injection_dry_run():
    config = load_eval_suite_config(
        str(REPOSITORY_ROOT / "eval_suites" / "default.json"),
    )

    assert config["injection"]["attack_project"] == "./adversarial_project"


@pytest.mark.parametrize(
    "bad_config, message",
    [
        ({**INJECTION_CONFIG, "live": True}, "unsupported keys: live"),
        ({**INJECTION_CONFIG, "repetitions": 0}, "positive integer"),
        ({key: value for key, value in INJECTION_CONFIG.items() if key != "cases"}, "cases"),
    ],
)
def test_injection_suite_config_is_validated(tmp_path, bad_config, message):
    suite = json.loads(
        (REPOSITORY_ROOT / "eval_suites" / "default.json").read_text(encoding="utf-8"),
    )
    suite["injection"] = bad_config
    config_path = tmp_path / "suite.json"
    config_path.write_text(json.dumps(suite), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_eval_suite_config(str(config_path))


def test_run_injection_suite_runs_dry_run(tmp_path):
    output = run_injection_suite(
        config=INJECTION_CONFIG,
        artifacts_dir=tmp_path,
    )

    assert output["metadata"]["mode"] == "dry_run"
    assert output["quality_gate"]["passed"] is True
    assert Path(output["output_paths"]["json"]).parent == tmp_path
