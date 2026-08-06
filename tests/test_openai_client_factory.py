import pytest

from openai_client_factory import (
    DEFAULT_OPENAI_MODEL,
    create_openai_client,
    create_openai_llm_adapter,
)
from openai_llm_adapter import (
    DEFAULT_OPENAI_MAX_OUTPUT_TOKENS,
    DEFAULT_OPENAI_REQUEST_TIMEOUT_SECONDS,
    OpenAILLMAdapter,
)

class FakeOpenAIClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs




def test_create_openai_client_uses_client_class_without_api_key():
    client = create_openai_client(
        client_class=FakeOpenAIClient,
    )

    assert isinstance(client, FakeOpenAIClient)
    assert client.kwargs == {}


def test_create_openai_client_passes_api_key_when_provided():
    client = create_openai_client(
        api_key="test-key",
        client_class=FakeOpenAIClient,
    )

    assert isinstance(client, FakeOpenAIClient)
    assert client.kwargs == {
        "api_key": "test-key",
    }


def test_create_openai_client_rejects_empty_api_key():
    with pytest.raises(ValueError):
        create_openai_client(
            api_key="",
            client_class=FakeOpenAIClient,
        )


def test_create_openai_client_rejects_whitespace_api_key():
    with pytest.raises(ValueError):
        create_openai_client(
            api_key="   ",
            client_class=FakeOpenAIClient,
        )


def test_create_openai_llm_adapter_returns_adapter_with_default_model():
    adapter = create_openai_llm_adapter(
        client_class=FakeOpenAIClient,
    )

    assert isinstance(adapter, OpenAILLMAdapter)
    assert adapter.model == DEFAULT_OPENAI_MODEL
    assert isinstance(adapter.client, FakeOpenAIClient)


def test_create_openai_llm_adapter_accepts_custom_model():
    adapter = create_openai_llm_adapter(
        model="test-model",
        client_class=FakeOpenAIClient,
    )

    assert isinstance(adapter, OpenAILLMAdapter)
    assert adapter.model == "test-model"


def test_create_openai_llm_adapter_passes_api_key_to_client():
    adapter = create_openai_llm_adapter(
        api_key="test-key",
        client_class=FakeOpenAIClient,
    )

    assert adapter.client.kwargs == {
        "api_key": "test-key",
    }

def test_default_openai_model_is_luna():
    assert DEFAULT_OPENAI_MODEL == "gpt-5.6-luna"

def test_load_dotenv_if_available_loads_env_file(tmp_path, monkeypatch):
    from openai_client_factory import load_dotenv_if_available

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env_path = tmp_path / ".env"
    env_path.write_text(
        'OPENAI_API_KEY="test-key-from-env-file"\n',
        encoding="utf-8",
    )

    loaded = load_dotenv_if_available(dotenv_path=env_path)

    assert loaded is True


def test_create_openai_client_loads_dotenv_before_creating_client(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env_path = tmp_path / ".env"
    env_path.write_text(
        'OPENAI_API_KEY="test-key-from-env-file"\n',
        encoding="utf-8",
    )

    client = create_openai_client(
        client_class=FakeOpenAIClient,
        dotenv_path=env_path,
    )

    assert isinstance(client, FakeOpenAIClient)        

def test_create_openai_llm_adapter_accepts_custom_max_output_tokens():
    adapter = create_openai_llm_adapter(
        model="test-model",
        max_output_tokens=250,
        client_class=FakeOpenAIClient,
    )

    assert adapter.max_output_tokens == 250    

def test_create_openai_llm_adapter_accepts_custom_request_timeout():
    adapter = create_openai_llm_adapter(
        model="test-model",
        request_timeout_seconds=5.0,
        client_class=FakeOpenAIClient,
    )

    assert adapter.request_timeout_seconds == 5.0    