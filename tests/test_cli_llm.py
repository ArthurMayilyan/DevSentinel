from argparse import Namespace

import pytest

from cli_llm import build_llm_from_args
from demo_llm import DemoCodeReviewLLM
from openai_llm_adapter import OpenAILLMAdapter
from cli_defaults import (
    OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS,
    OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS,
)


class FakeOpenAIClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_build_llm_from_args_returns_demo_llm():
    args = Namespace(
        llm="demo",
        model="gpt-5.6-luna",
    )

    llm = build_llm_from_args(args)

    assert isinstance(llm, DemoCodeReviewLLM)


def test_build_llm_from_args_returns_openai_adapter():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
    )

    llm = build_llm_from_args(
        args,
        openai_client_class=FakeOpenAIClient,
    )

    assert isinstance(llm, OpenAILLMAdapter)
    assert llm.model == "gpt-5.6-luna"
    assert isinstance(llm.client, FakeOpenAIClient)


def test_build_llm_from_args_rejects_unknown_backend():
    args = Namespace(
        llm="unknown",
        model="gpt-5.6-luna",
    )

    with pytest.raises(ValueError):
        build_llm_from_args(args)

def test_build_llm_from_args_passes_max_output_tokens_to_openai_adapter():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
        max_output_tokens=250,
    )

    llm = build_llm_from_args(
        args,
        openai_client_class=FakeOpenAIClient,
    )

    assert llm.max_output_tokens == 250        

def test_build_llm_from_args_passes_request_timeout_to_openai_adapter():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
        max_output_tokens=250,
        request_timeout_seconds=5.0,
    )

    llm = build_llm_from_args(
        args,
        openai_client_class=FakeOpenAIClient,
    )

    assert llm.request_timeout_seconds == 5.0    

def test_build_llm_from_args_uses_openai_cli_defaults():
    args = Namespace(
        llm="openai",
        model="gpt-5.6-luna",
    )

    llm = build_llm_from_args(
        args,
        openai_client_class=FakeOpenAIClient,
    )

    assert llm.max_output_tokens == OPENAI_CLI_DEFAULT_MAX_OUTPUT_TOKENS
    assert llm.request_timeout_seconds == OPENAI_CLI_DEFAULT_REQUEST_TIMEOUT_SECONDS    