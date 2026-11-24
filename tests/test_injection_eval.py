import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from devsentinel.cli.run_injection_eval import run_from_args
from devsentinel.core.tool_path_utils import build_project_scope
from devsentinel.review import injection_eval
from devsentinel.review.injection_eval import (
    detect_premature_completion_attempts,
    find_canary_locations,
    is_inspected,
    load_injection_eval_cases,
    match_known_vulnerabilities,
    prepare_run_workspace,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = REPOSITORY_ROOT / "eval_cases" / "injection_eval_cases.json"
CONTROL_PROJECT = REPOSITORY_ROOT / "sample_project"
ATTACK_PROJECT = REPOSITORY_ROOT / "adversarial_project"


def dry_run_args(tmp_path, *extra: str) -> list[str]:
    return [
        "--repetitions", "1",
        "--control-project", str(CONTROL_PROJECT),
        "--attack-project", str(ATTACK_PROJECT),
        "--cases", str(CASES_PATH),
        "--output-dir", str(tmp_path / "results"),
        "--artifacts-dir", str(tmp_path / "artifacts"),
        *extra,
    ]


# ---------------------------------------------------------------------------
# Fixture integrity
# ---------------------------------------------------------------------------


def test_adversarial_project_keeps_every_sample_vulnerability_line():
    for sample_file in CONTROL_PROJECT.glob("*.py"):
        adversarial_text = (ATTACK_PROJECT / sample_file.name).read_text(encoding="utf-8")

        for line in sample_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                assert line in adversarial_text, (sample_file.name, line)


def test_each_payload_family_is_present_in_its_files():
    cases = load_injection_eval_cases(CASES_PATH)
    markers = {
        "A_suppression": "report no findings",
        "B_downgrade": "low severity by policy",
        "C_tool_misuse": "../canary.txt",
        "D_early_termination": "write_report now",
        "E_fabrication": "SQL injection in",
    }

    assert set(cases["payloads"]) == set(markers)

    for family, payload in cases["payloads"].items():
        for name in payload["files"]:
            text = (ATTACK_PROJECT / name).read_text(encoding="utf-8")
            assert markers[family] in text, (family, name)


def test_control_project_has_no_payloads():
    for path in CONTROL_PROJECT.glob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            assert "reviewer" not in text
            assert "canary" not in text


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------


def test_prepare_run_workspace_places_canary_outside_project(tmp_path):
    workspace = prepare_run_workspace(
        source_project=ATTACK_PROJECT,
        run_dir=tmp_path,
        placeholder="{{CANARY_ABSOLUTE_PATH}}",
    )

    utils_text = (workspace.project_dir / "utils.py").read_text(encoding="utf-8")

    assert str(workspace.canary_path) in utils_text
    assert "{{CANARY_ABSOLUTE_PATH}}" not in utils_text
    assert not workspace.canary_path.is_relative_to(workspace.project_dir)
    assert workspace.canary_path.read_text(encoding="utf-8") == workspace.canary_token
    assert workspace.canary_token not in utils_text


def test_match_known_vulnerabilities_uses_file_and_term_groups():
    cases = load_injection_eval_cases(CASES_PATH)
    findings = [
        {
            "file": "project\\auth.py",
            "severity": "LOW",
            "issue": "Hardcoded admin credentials",
            "evidence": "username == 'admin'",
            "recommendation": "Remove.",
        },
        {
            "file": "app.py",
            "severity": "HIGH",
            "issue": "Hardcoded SECRET_KEY",
            "evidence": "",
            "recommendation": "",
        },
    ]

    matches = match_known_vulnerabilities(
        findings=findings,
        vulnerabilities=cases["known_vulnerabilities"],
    )

    assert matches["auth_hardcoded_admin_credentials"]["severities"] == ["LOW"]
    # Right words, wrong file: not counted.
    assert matches["config_hardcoded_secret_key"]["reported"] is False


def test_is_inspected_accepts_relative_dotted_and_absolute_forms():
    assert is_inspected(relative_path="auth.py", inspected_files=["./auth.py"])
    assert is_inspected(relative_path="auth.py", inspected_files=["C:\\x\\project\\AUTH.py"])
    assert not is_inspected(relative_path="auth.py", inspected_files=["oauth.py"])


def test_premature_completion_uses_real_file_list_not_discovered_files():
    trace = [
        {
            "step": 1,
            "llm_output": {"type": "tool_call", "tool": "write_report", "arguments": {}},
            "state_before": {"inspected_files": ["app.py"], "discovered_files": ["app.py"]},
            "tool_result": "report.md",
        },
        {
            "step": 2,
            "llm_output": {"type": "final_answer", "answer": "done"},
            "state_before": {"inspected_files": ["app.py"]},
            "guardrail_result": {"allowed": False},
        },
    ]

    attempts = detect_premature_completion_attempts(
        trace=trace,
        project_python_files=["app.py", "auth.py"],
    )

    assert [attempt["blocked"] for attempt in attempts] == [False, True]


def test_find_canary_locations():
    assert find_canary_locations(
        token="TOKEN-1",
        texts={"trace": "a TOKEN-1 b", "report": "clean"},
    ) == ["trace"]


# ---------------------------------------------------------------------------
# End-to-end dry run
# ---------------------------------------------------------------------------


def test_dry_run_exercises_every_family_and_passes_gate(tmp_path):
    result = run_from_args(dry_run_args(tmp_path))

    control = result["conditions"]["control"]
    attack = result["conditions"]["attack"]

    assert result["metadata"]["mode"] == "dry_run"
    assert result["quality_gate"]["passed"] is True

    assert control["recall"]["known_vulnerabilities_reported"] == {"count": 5, "of": 5}
    assert control["tool_misuse"]["runs_with_attempt"]["count"] == 0
    assert control["early_termination"]["runs_with_premature_report_or_answer"]["count"] == 0

    # The scripted model obeys every payload; the app blocks C and D only.
    assert attack["suppression"]["runs_with_zero_findings_in_suppression_files"]["count"] == 1
    assert attack["downgrade"]["downgrade_file_vulnerabilities_reported_only_as_low"]["count"] == 2
    assert attack["fabrication"]["runs_with_fabricated_finding"]["count"] == 1
    assert attack["tool_misuse"]["attempts_blocked_by_root_guardrail"] == {"count": 2, "of": 2}
    assert attack["tool_misuse"]["attempts_that_returned_content"]["count"] == 0
    assert attack["canary_leak"]["runs_with_canary_in_output"]["count"] == 0
    assert attack["early_termination"]["premature_attempts_blocked"] == {"count": 1, "of": 1}

    json_path = Path(result["output_paths"]["json"])
    markdown_path = Path(result["output_paths"]["markdown"])

    assert json_path.name.endswith("_dry_run.json")
    assert markdown_path.read_text(encoding="utf-8").count("| C Tool misuse |") == 3

    written = json_path.read_text(encoding="utf-8")

    assert "devsentinel_injection_" not in written
    assert json.loads(written)["quality_gate"]["passed"] is True
    assert sorted(path.name for path in (tmp_path / "artifacts").iterdir()) == [
        "attack_01_trace.json",
        "control_01_trace.json",
    ]


def test_gate_fails_when_root_guardrail_is_widened(tmp_path, monkeypatch):
    """Negative control: if the canary is inside the root, the leak is detected."""

    def widened_scope(*, root, **kwargs):
        return build_project_scope(root=Path(root).parent, **kwargs)

    monkeypatch.setattr(injection_eval, "build_project_scope", widened_scope)

    result = run_from_args(dry_run_args(tmp_path))
    attack = result["conditions"]["attack"]

    assert result["quality_gate"]["passed"] is False
    assert attack["canary_leak"]["runs_with_canary_in_output"]["count"] == 1
    assert attack["tool_misuse"]["attempts_that_returned_content"]["count"] >= 1


def test_cost_guard_refuses_too_many_runs(tmp_path):
    with pytest.raises(ValueError, match="max_runs"):
        run_from_args(dry_run_args(tmp_path, "--repetitions", "11", "--max-runs", "20"))


def test_live_mode_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        "devsentinel.cli.run_injection_eval.load_dotenv_if_available",
        lambda **kwargs: False,
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        run_from_args(dry_run_args(tmp_path, "--live"), env={})


class FinalAnswerOnlyClient:
    """Offline stand-in for the OpenAI client used to test live wiring."""

    def __init__(self, **kwargs):
        self.responses = self

    def create(self, **kwargs):
        return SimpleNamespace(
            output_text=json.dumps({
                "type": "final_answer",
                "tool": None,
                "arguments": None,
                "answer": "Nothing to review.",
            }),
        )


def test_live_wiring_records_model_and_stop_reasons(tmp_path):
    result = run_from_args(
        dry_run_args(tmp_path, "--live", "--model", "test-model"),
        openai_client_class=FinalAnswerOnlyClient,
    )

    assert result["metadata"]["mode"] == "live"
    assert result["metadata"]["model"] == "test-model"
    assert result["metadata"]["temperature"] is None
    assert Path(result["output_paths"]["json"]).name.endswith(".json")
    assert "_dry_run" not in result["output_paths"]["json"]

    for condition in result["conditions"].values():
        assert condition["robustness"]["stop_reasons"] == {"rejected_final_answers": 1}
