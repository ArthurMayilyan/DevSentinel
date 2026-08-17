import json
from dataclasses import dataclass
from typing import Any

from app_settings import get_app_settings


_SETTINGS = get_app_settings()

DEFAULT_OPENAI_MAX_OUTPUT_TOKENS = (
    _SETTINGS.openai.max_output_tokens
)

DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS = (
    _SETTINGS.openai.request_timeout_seconds
)

AGENT_ARGUMENTS_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "path": {
            "type": ["string", "null"],
        },
        "query": {
            "type": ["string", "null"],
        },
        "file": {
            "type": ["string", "null"],
        },
        "severity": {
            "type": ["string", "null"],
        },
        "category": {
            "type": ["string", "null"],
        },
        "issue": {
            "type": ["string", "null"],
        },
        "evidence": {
            "type": ["string", "null"],
        },
        "recommendation": {
            "type": ["string", "null"],
        },
    },
    "required": [
        "path",
        "query",
        "file",
        "severity",
        "category",
        "issue",
        "evidence",
        "recommendation",
    ],
}


AGENT_OUTPUT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "type": {
            "type": "string",
            "enum": ["tool_call", "final_answer"],
        },
        "tool": {
            "type": ["string", "null"],
        },
        "arguments": AGENT_ARGUMENTS_JSON_SCHEMA,
        "answer": {
            "type": ["string", "null"],
        },
    },
    "required": ["type", "tool", "arguments", "answer"],
}

def parse_first_json_value(text: str) -> Any:
    decoder = json.JSONDecoder()

    try:
        value, _end_index = decoder.raw_decode(text.strip())
    except json.JSONDecodeError:
        return text

    return value


@dataclass(frozen=True)
class OpenAILLMAdapter:
    client: Any
    model: str
    max_output_tokens: int = DEFAULT_OPENAI_MAX_OUTPUT_TOKENS
    request_timeout_seconds: float = DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if self.client is None:
            raise ValueError("OpenAILLMAdapter requires a client.")

        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("OpenAILLMAdapter requires a non-empty model.")

        if type(self.max_output_tokens) is not int:
            raise ValueError("max_output_tokens must be an integer.")

        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be greater than 0.")

        if type(self.request_timeout_seconds) not in {int, float}:
            raise ValueError("request_timeout_seconds must be a number.")

        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be greater than 0.")

    def complete(self, messages: list[dict], state: Any = None) -> object:
        client = self.client

        if hasattr(client, "with_options"):
            client = client.with_options(timeout=self.request_timeout_seconds)

        response = client.responses.create(
            model=self.model,
            input=messages,
            max_output_tokens=self.max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "agent_loop_output",
                    "strict": True,
                    "schema": AGENT_OUTPUT_JSON_SCHEMA,
                }
            },
        )

        output_text = self._extract_output_text(response)

        parsed = parse_first_json_value(output_text)

        if not isinstance(parsed, dict):
            return parsed

        return self._normalize_output(parsed)


    @staticmethod
    def _extract_output_text(response: Any) -> str:
        output_text = getattr(response, "output_text", None)

        if not isinstance(output_text, str) or not output_text.strip():
            raise ValueError("OpenAI response does not contain non-empty output_text.")

        return output_text

    @staticmethod
    def _normalize_output(parsed: dict) -> dict:
        output_type = parsed.get("type")

        if output_type == "tool_call":
            raw_arguments = parsed.get("arguments") or {}

            if not isinstance(raw_arguments, dict):
                return parsed

            arguments = {
                key: value
                for key, value in raw_arguments.items()
                if value is not None
            }

            return {
                "type": "tool_call",
                "tool": parsed.get("tool"),
                "arguments": arguments,
            }

        if output_type == "final_answer":
            return {
                "type": "final_answer",
                "answer": parsed.get("answer"),
            }

        return parsed