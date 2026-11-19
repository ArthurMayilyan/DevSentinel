import pytest

from devsentinel.cli import run_live_openai_smoke


def test_live_smoke_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(run_live_openai_smoke, "load_dotenv_if_available", lambda: False)

    with pytest.raises(SystemExit) as error:
        run_live_openai_smoke.main(["--model", "test-model"])
    assert error.value.code == 2


def test_live_smoke_checks_reviewer_result(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(run_live_openai_smoke, "load_dotenv_if_available", lambda: False)

    class FakeReviewer:
        def __init__(self, *, model):
            assert model == "test-model"

        def review_file(self, **kwargs):
            assert "SECRET_KEY" in kwargs["content"]
            return [{"finding_type": "security.hardcoded_secret"}]

    monkeypatch.setattr(run_live_openai_smoke, "OpenAIReviewReviewer", FakeReviewer)
    run_live_openai_smoke.main(["--model", "test-model"])
