import json

import pytest

from openai_llm_adapter import (
    AGENT_OUTPUT_JSON_SCHEMA,
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
    OpenAILLMAdapter,
    parse_first_json_value,
)

class FakeOpenAIResponse:
    def __init__(self, output_text):
        self.output_text = output_text


class FakeResponsesAPI:
    def __init__(self, output_text):
        self.output_text = output_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeOpenAIResponse(self.output_text)


class FakeOpenAIClient:
    def __init__(self, output_text):
        self.responses = FakeResponsesAPI(output_text)
        self.timeout = None

    def with_options(self, **kwargs):
        self.timeout = kwargs.get("timeout")
        return self


def test_openai_adapter_returns_tool_call_dict():
    client = FakeOpenAIClient(json.dumps({
        "type": "tool_call",
        "tool": "list_files",
        "arguments": {
            "path": "./sample_project",
        },
        "answer": None,
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == {
        "type": "tool_call",
        "tool": "list_files",
        "arguments": {
            "path": "./sample_project",
        },
    }


def test_openai_adapter_returns_final_answer_dict():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": None,
        "answer": "Review complete.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == {
        "type": "final_answer",
        "answer": "Review complete.",
    }


def test_openai_adapter_calls_responses_api_with_json_schema_format():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": None,
        "answer": "Done.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    messages = [
        {
            "role": "user",
            "content": "Review the project.",
        }
    ]

    adapter.complete(messages)

    call = client.responses.calls[0]

    assert call["model"] == "test-model"
    assert call["input"] == messages
    assert call["text"]["format"]["type"] == "json_schema"
    assert call["text"]["format"]["name"] == "agent_loop_output"
    assert call["text"]["format"]["strict"] is True


def test_openai_adapter_rejects_missing_client():
    with pytest.raises(ValueError):
        OpenAILLMAdapter(
            client=None,
            model="test-model",
        )


def test_openai_adapter_rejects_empty_model():
    with pytest.raises(ValueError):
        OpenAILLMAdapter(
            client=FakeOpenAIClient("{}"),
            model="",
        )


def test_openai_adapter_rejects_empty_output_text():
    client = FakeOpenAIClient("")

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    with pytest.raises(ValueError):
        adapter.complete([
            {
                "role": "user",
                "content": "Review the project.",
            }
        ])


def test_openai_adapter_returns_raw_text_for_invalid_json_output_text():
    client = FakeOpenAIClient("not json")

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == "not json"


def test_openai_adapter_returns_non_object_json_for_agent_guardrail():
    payload = [
        {
            "type": "final_answer",
            "answer": "Done.",
        }
    ]

    client = FakeOpenAIClient(json.dumps(payload))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == payload


def test_openai_adapter_returns_unknown_output_type_for_agent_guardrail():
    payload = {
        "type": "analysis",
        "tool": None,
        "arguments": None,
        "answer": None,
    }

    client = FakeOpenAIClient(json.dumps(payload))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == payload

def test_openai_adapter_schema_arguments_object_disallows_additional_properties():
    arguments_schema = AGENT_OUTPUT_JSON_SCHEMA["properties"]["arguments"]

    assert arguments_schema["type"] == "object"
    assert arguments_schema["additionalProperties"] is False


def test_openai_adapter_schema_arguments_has_all_required_nullable_fields():
    arguments_schema = AGENT_OUTPUT_JSON_SCHEMA["properties"]["arguments"]

    assert set(arguments_schema["required"]) == {
        "path",
        "query",
        "file",
        "severity",
        "category",
        "issue",
        "evidence",
        "recommendation",
    }

    for field_name in arguments_schema["required"]:
        assert arguments_schema["properties"][field_name]["type"] == ["string", "null"]


def test_openai_adapter_removes_null_argument_fields():
    client = FakeOpenAIClient(json.dumps({
        "type": "tool_call",
        "tool": "list_files",
        "arguments": {
            "path": "./sample_project",
            "query": None,
            "file": None,
            "severity": None,
            "category": None,
            "issue": None,
            "evidence": None,
            "recommendation": None,
        },
        "answer": None,
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == {
        "type": "tool_call",
        "tool": "list_files",
        "arguments": {
            "path": "./sample_project",
        },
    }        

def test_openai_adapter_parses_first_json_object_from_extra_json_data():
    output_text = (
        '{"type": "tool_call", "tool": "list_files", '
        '"arguments": {"path": "./sample_project", "query": null, "file": null, '
        '"severity": null, "category": null, "issue": null, '
        '"evidence": null, "recommendation": null}, "answer": null}\n'
        '{"type": "tool_call", "tool": "read_file", '
        '"arguments": {"path": "sample_project/auth.py", "query": null, "file": null, '
        '"severity": null, "category": null, "issue": null, '
        '"evidence": null, "recommendation": null}, "answer": null}'
    )

    client = FakeOpenAIClient(output_text)

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    result = adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert result == {
        "type": "tool_call",
        "tool": "list_files",
        "arguments": {
            "path": "./sample_project",
        },
    }

def test_parse_first_json_value_returns_first_object_from_concatenated_json():
    result = parse_first_json_value('{"a": 1}{"b": 2}')

    assert result == {"a": 1}


def test_parse_first_json_value_returns_raw_text_for_invalid_json():
    result = parse_first_json_value("not json")

    assert result == "not json"


def test_parse_first_json_value_handles_leading_whitespace():
    result = parse_first_json_value('   {"a": 1}{"b": 2}')

    assert result == {"a": 1}    

def test_openai_adapter_uses_default_max_output_tokens():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": {
            "path": None,
            "query": None,
            "file": None,
            "severity": None,
            "category": None,
            "issue": None,
            "evidence": None,
            "recommendation": None,
        },
        "answer": "Done.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    call = client.responses.calls[0]

    assert call["max_output_tokens"] == DEFAULT_OPENAI_MAX_OUTPUT_TOKENS


def test_openai_adapter_accepts_custom_max_output_tokens():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": {
            "path": None,
            "query": None,
            "file": None,
            "severity": None,
            "category": None,
            "issue": None,
            "evidence": None,
            "recommendation": None,
        },
        "answer": "Done.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
        max_output_tokens=250,
    )

    adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    call = client.responses.calls[0]

    assert call["max_output_tokens"] == 250


def test_openai_adapter_rejects_invalid_max_output_tokens():
    with pytest.raises(ValueError):
        OpenAILLMAdapter(
            client=FakeOpenAIClient("{}"),
            model="test-model",
            max_output_tokens=0,
        )


def test_openai_adapter_uses_default_request_timeout():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": {
            "path": None,
            "query": None,
            "file": None,
            "severity": None,
            "category": None,
            "issue": None,
            "evidence": None,
            "recommendation": None,
        },
        "answer": "Done.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
    )

    adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert client.timeout == DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS


def test_openai_adapter_accepts_custom_request_timeout():
    client = FakeOpenAIClient(json.dumps({
        "type": "final_answer",
        "tool": None,
        "arguments": {
            "path": None,
            "query": None,
            "file": None,
            "severity": None,
            "category": None,
            "issue": None,
            "evidence": None,
            "recommendation": None,
        },
        "answer": "Done.",
    }))

    adapter = OpenAILLMAdapter(
        client=client,
        model="test-model",
        request_timeout_seconds=5.0,
    )

    adapter.complete([
        {
            "role": "user",
            "content": "Review the project.",
        }
    ])

    assert client.timeout == 5.0


def test_openai_adapter_rejects_invalid_request_timeout():
    with pytest.raises(ValueError):
        OpenAILLMAdapter(
            client=FakeOpenAIClient("{}"),
            model="test-model",
            request_timeout_seconds=0,
        )
            