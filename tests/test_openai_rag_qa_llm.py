import pytest

from openai_rag_qa_llm import OpenAIRagQaLLM


class FakeInvalidOpenAIResponse:
    output_text = "Tokens expire after 24 hours."


class FakeInvalidResponsesClient:
    def create(
        self,
        *,
        model,
        input,
    ):
        return FakeInvalidOpenAIResponse()


class FakeInvalidOpenAIClient:
    def __init__(self):
        self.responses = FakeInvalidResponsesClient()

class FakeOpenAIResponse:
    def __init__(
        self,
        output_text: str,
    ):
        self.output_text = output_text


class FakeResponsesClient:
    def __init__(self):
        self.calls = []

    def create(
        self,
        *,
        model,
        input,
    ):
        self.calls.append(
            {
                "model": model,
                "input": input,
            }
        )

        return FakeOpenAIResponse(
            "Token expiration policy: tokens must be signed and must expire.\n\nSource: security.md"
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = FakeResponsesClient()


def test_openai_rag_qa_llm_rejects_empty_model():
    with pytest.raises(ValueError):
        OpenAIRagQaLLM(
            model="",
        )


def test_openai_rag_qa_llm_first_call_requests_search_knowledge():
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=FakeOpenAIClient(),
    )

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            }
        ]
    )

    assert output == {
        "type": "tool_call",
        "tool": "search_knowledge",
        "arguments": {
            "query": "token expiration",
        },
    }


def test_openai_rag_qa_llm_second_call_generates_grounded_answer_from_evidence():
    client = FakeOpenAIClient()
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=client,
    )
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "text": "Token expiration policy: tokens must be signed and must expire.",
                    }
                ],
            },
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": (
            "Token expiration policy: tokens must be signed and must expire.\n\n"
            "Source: security.md"
        ),
    }

    assert client.responses.calls[0]["model"] == "gpt-5"
    assert "Evidence:" in client.responses.calls[0]["input"][1]["content"]
    assert "security.md" in client.responses.calls[0]["input"][1]["content"]


def test_openai_rag_qa_llm_returns_insufficient_evidence_when_no_evidence_found():
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=FakeOpenAIClient(),
    )
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "unknown question",
            }
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": "I do not have enough evidence to answer.",
    }


def test_openai_rag_qa_llm_formats_multiple_evidence_items():
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=FakeOpenAIClient(),
    )

    formatted = llm.format_evidence(
        [
            {
                "source": "security.md",
                "text": "Security text.",
            },
            {
                "source": "coding.md",
                "text": "Coding text.",
            },
        ]
    )

    assert "[1] Source: security.md" in formatted
    assert "Security text." in formatted
    assert "[2] Source: coding.md" in formatted
    assert "Coding text." in formatted

def test_openai_rag_qa_llm_falls_back_when_generated_answer_fails_guardrail():
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=FakeInvalidOpenAIClient(),
    )
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "text": "Token expiration policy: tokens must be signed and must expire.",
                    }
                ],
            },
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": (
            "Token expiration policy: tokens must be signed and must expire.\n\n"
            "Source: security.md"
        ),
    }


class FakeBracketSourceResponse:
    output_text = (
        "Tokens must be signed and must expire. "
        "[Source: security.md]"
    )


class FakeBracketSourceResponsesClient:
    def create(
        self,
        *,
        model,
        input,
    ):
        return FakeBracketSourceResponse()


class FakeBracketSourceOpenAIClient:
    def __init__(self):
        self.responses = FakeBracketSourceResponsesClient()


def test_openai_rag_qa_llm_accepts_bracket_source_style():
    llm = OpenAIRagQaLLM(
        model="gpt-5",
        client=FakeBracketSourceOpenAIClient(),
    )
    llm.call_count = 1

    output = llm.complete(
        [
            {
                "role": "user",
                "content": "token expiration",
            },
            {
                "role": "tool",
                "content": [
                    {
                        "source": "security.md",
                        "text": "Token expiration policy: tokens must be signed and must expire.",
                    }
                ],
            },
        ]
    )

    assert output == {
        "type": "final_answer",
        "answer": "Tokens must be signed and must expire. [Source: security.md]",
    }

            