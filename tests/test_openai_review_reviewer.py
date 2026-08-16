import json

from openai_review_reviewer import (
    OpenAIReviewReviewer,
    extract_openai_response_text,
    parse_review_findings_json,
)


class FakeOpenAIResponse:
    output_text = json.dumps(
        {
            "findings": [
                {
                    "file": "app.py",
                    "severity": "high",
                    "category": "security",
                    "issue": "Hardcoded credential risk.",
                    "evidence": "A sensitive value appears directly in source code.",
                    "recommendation": "Move sensitive values to secure configuration.",
                }
            ]
        }
    )


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(
        self,
        **kwargs,
    ):
        self.calls.append(
            kwargs,
        )

        return FakeOpenAIResponse()


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_extract_openai_response_text_reads_output_text():
    assert extract_openai_response_text(
        FakeOpenAIResponse(),
    ).startswith(
        "{"
    )


def test_parse_review_findings_json_normalizes_values():
    findings = parse_review_findings_json(
        FakeOpenAIResponse.output_text,
    )

    assert findings == [
        {
            "file": "app.py",
            "severity": "HIGH",
            "category": "SECURITY",
            "issue": "Hardcoded credential risk.",
            "evidence": "A sensitive value appears directly in source code.",
            "recommendation": "Move sensitive values to secure configuration.",
        }
    ]


def test_parse_review_findings_json_returns_empty_list_for_empty_text():
    assert parse_review_findings_json(
        "",
    ) == []


def test_parse_review_findings_json_skips_incomplete_findings():
    findings = parse_review_findings_json(
        json.dumps(
            {
                "findings": [
                    {
                        "file": "app.py",
                        "severity": "HIGH",
                    }
                ]
            }
        )
    )

    assert findings == []


def test_openai_review_reviewer_uses_configured_model():
    fake_client = FakeOpenAIClient()

    reviewer = OpenAIReviewReviewer(
        model="gpt-5.6-luna",
        client=fake_client,
    )

    findings = reviewer.review_file(
        file_path="app.py",
        content='PASSWORD = "secret"',
        profile="security",
        policy_context="Credentials must not be hardcoded.",
    )

    assert findings[0]["severity"] == "HIGH"
    assert fake_client.responses.calls[0]["model"] == "gpt-5.6-luna"
    assert "PASSWORD" in fake_client.responses.calls[0]["input"]
    assert "Credentials must not be hardcoded." in fake_client.responses.calls[0]["input"]