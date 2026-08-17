import json
from typing import Any

from finding_types import (
    FINDING_TYPE_SECURITY_DEBUG_MODE,
    FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS,
    FINDING_TYPE_SECURITY_HARDCODED_SECRET,
    FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE,
    FINDING_TYPE_SECURITY_OTHER,
    FINDING_TYPE_SECURITY_TOKEN_EXPIRATION,
    FINDING_TYPE_SECURITY_TOKEN_VALIDATION,
    normalize_finding_type,
)
from reviewer_config import DEFAULT_OPENAI_REVIEW_MODEL


def extract_openai_response_text(
    response: Any,
) -> str:
    output_text = getattr(
        response,
        "output_text",
        None,
    )

    if isinstance(
        output_text,
        str,
    ):
        return output_text

    return ""


def parse_review_findings_json(
    text: str,
) -> list[dict[str, Any]]:
    if not isinstance(
        text,
        str,
    ) or not text.strip():
        return []

    parsed = json.loads(
        text,
    )

    findings = parsed.get(
        "findings",
        [],
    )

    if not isinstance(
        findings,
        list,
    ):
        return []

    normalized = []

    for item in findings:
        if not isinstance(
            item,
            dict,
        ):
            continue

        required_fields = [
            "file",
            "severity",
            "category",
            "issue",
            "evidence",
            "recommendation",
        ]

        if not all(
            field in item
            for field in required_fields
        ):
            continue

        issue = str(
            item["issue"],
        )

        evidence = str(
            item["evidence"],
        )

        finding_type = normalize_finding_type(
            str(
                item.get(
                    "finding_type",
                    "",
                )
            ),
            issue=issue,
            evidence=evidence,
        )

        normalized.append(
            {
                "finding_type": finding_type,
                "file": str(
                    item["file"],
                ),
                "severity": str(
                    item["severity"],
                ).upper(),
                "category": str(
                    item["category"],
                ).upper(),
                "issue": issue,
                "evidence": evidence,
                "recommendation": str(
                    item["recommendation"],
                ),
            }
        )

    return normalized


class OpenAIReviewReviewer:
    def __init__(
        self,
        *,
        model: str = DEFAULT_OPENAI_REVIEW_MODEL,
        client: Any = None,
        client_class: Any = None,
        max_content_chars: int = 12_000,
    ) -> None:
        self.model = model
        self.client = client
        self.client_class = client_class
        self.max_content_chars = max_content_chars

    def get_client(
        self,
    ):
        if self.client is not None:
            return self.client

        if self.client_class is not None:
            self.client = self.client_class()
            return self.client

        from dotenv import load_dotenv
        from openai import OpenAI

        load_dotenv()

        self.client = OpenAI()

        return self.client

    def build_prompt(
        self,
        *,
        file_path: str,
        content: str,
        profile: str,
        policy_context: str,
    ) -> str:
        limited_content = content[
            : self.max_content_chars
        ]

        supported_types = "\n".join(
            [
                f"- {FINDING_TYPE_SECURITY_HARDCODED_SECRET}",
                f"- {FINDING_TYPE_SECURITY_HARDCODED_ADMIN_CREDENTIALS}",
                f"- {FINDING_TYPE_SECURITY_DEBUG_MODE}",
                f"- {FINDING_TYPE_SECURITY_TOKEN_VALIDATION}",
                f"- {FINDING_TYPE_SECURITY_TOKEN_EXPIRATION}",
                f"- {FINDING_TYPE_SECURITY_INFORMATION_DISCLOSURE}",
                f"- {FINDING_TYPE_SECURITY_OTHER}",
            ]
        )

        return f"""You are a careful code security reviewer.

Review profile: {profile}

Return JSON only in this exact shape:
{{
  "findings": [
    {{
      "finding_type": "security.debug_mode",
      "file": "...",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "category": "SECURITY|MAINTAINABILITY|RELIABILITY|PERFORMANCE",
      "issue": "...",
      "evidence": "...",
      "recommendation": "..."
    }}
  ]
}}

Supported finding_type values:
{supported_types}

Rules:
- Do not invent issues.
- Every finding must be supported by concrete evidence from the file.
- finding_type is a stable machine-readable identifier.
- Use the same finding_type even if the human-readable issue wording changes.
- Select the closest supported finding_type.
- Use security.other only if none of the specific types applies.
- If there are no concrete findings, return {{"findings": []}}.
- Prefer SECURITY for credentials, secrets, authentication, token, or debug-mode issues.

Policy context:
{policy_context or "No external policy context was provided."}

File path:
{file_path}

File content:
```text
{limited_content}
```
"""

    def review_file(
        self,
        *,
        file_path: str,
        content: str,
        profile: str,
        policy_context: str,
    ) -> list[dict[str, Any]]:
        client = self.get_client()

        response = client.responses.create(
            model=self.model,
            input=self.build_prompt(
                file_path=file_path,
                content=content,
                profile=profile,
                policy_context=policy_context,
            ),
        )

        text = extract_openai_response_text(
            response,
        )

        return parse_review_findings_json(
            text,
        )