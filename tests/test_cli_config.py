import pytest

from agent_config import AgentConfig
from cli_config import build_agent_config_from_args, build_arg_parser
from openai_client_factory import DEFAULT_OPENAI_MODEL
from cli_defaults import OPENAI_CLI_DEFAULT_MAX_STEPS
from task_presets import DEFAULT_CODE_REVIEW_MAX_FINDINGS


def test_cli_parser_accepts_empty_args_for_later_task_validation():
    parser = build_arg_parser()

    args = parser.parse_args([])

    assert args.task is None
    assert args.preset is None
    assert args.path is None

def test_cli_parser_accepts_task_with_default_config_values():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
    ])

    config = build_agent_config_from_args(args)

    assert args.task == "Review the sample project."
    assert config == AgentConfig()


def test_cli_parser_accepts_custom_max_steps():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "20",
    ])

    config = build_agent_config_from_args(args)

    assert config.max_steps == 20


def test_cli_parser_accepts_all_custom_config_values():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "20",
        "--max-rejected-final-answers",
        "2",
        "--max-rejected-tool-calls",
        "4",
        "--max-invalid-llm-outputs",
        "3",
    ])

    config = build_agent_config_from_args(args)

    assert config == AgentConfig(
        max_steps=20,
        max_rejected_final_answers=2,
        max_rejected_tool_calls=4,
        max_invalid_llm_outputs=3,
    )


def test_cli_parser_rejects_non_integer_max_steps():
    parser = build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([
            "--task",
            "Review the sample project.",
            "--max-steps",
            "not-an-int",
        ])


def test_build_agent_config_from_args_rejects_invalid_config_values():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--max-steps",
        "0",
    ])

    with pytest.raises(ValueError):
        build_agent_config_from_args(args)

def test_cli_parser_uses_demo_llm_by_default():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
    ])

    assert args.llm == "demo"
    assert args.model == DEFAULT_OPENAI_MODEL


def test_cli_parser_accepts_openai_llm_and_custom_model():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "openai",
        "--model",
        "gpt-5.6-luna",
    ])

    assert args.llm == "openai"
    assert args.model == "gpt-5.6-luna"


def test_cli_parser_rejects_unknown_llm_backend():
    parser = build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([
            "--task",
            "Review the sample project.",
            "--llm",
            "unknown",
        ])


def test_cli_parser_accepts_max_output_tokens():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "openai",
        "--max-output-tokens",
        "250",
    ])

    assert args.max_output_tokens == 250


def test_cli_parser_accepts_request_timeout_seconds():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "openai",
        "--request-timeout-seconds",
        "5",
    ])

    assert args.request_timeout_seconds == 5.0            

def test_cli_parser_accepts_code_review_preset_and_path():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
    ])

    assert args.preset == "code-review"
    assert args.path == "./sample_project"
    assert args.max_findings == DEFAULT_CODE_REVIEW_MAX_FINDINGS


def test_cli_parser_accepts_custom_max_findings():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
        "--max-findings",
        "5",
    ])

    assert args.max_findings == 5


def test_cli_parser_rejects_unknown_preset():
    parser = build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([
            "--preset",
            "unknown",
            "--path",
            "./sample_project",
        ])    

def test_build_agent_config_uses_openai_max_steps_default():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "openai",
    ])

    config = build_agent_config_from_args(args)

    assert config.max_steps == OPENAI_CLI_DEFAULT_MAX_STEPS


def test_build_agent_config_explicit_max_steps_overrides_openai_default():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--task",
        "Review the sample project.",
        "--llm",
        "openai",
        "--max-steps",
        "30",
    ])

    config = build_agent_config_from_args(args)

    assert config.max_steps == 30

def test_cli_parser_accepts_print_task_flag():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
        "--print-task",
    ])

    assert args.print_task is True

def test_cli_parser_print_task_defaults_to_false():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
    ])

    assert args.print_task is False

def test_cli_parser_accepts_knowledge_path():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
        "--knowledge-path",
        "./knowledge_base",
    ])

    assert args.knowledge_path == "./knowledge_base"

def test_cli_parser_knowledge_path_defaults_to_none():
    parser = build_arg_parser()

    args = parser.parse_args([
        "--preset",
        "code-review",
        "--path",
        "./sample_project",
    ])

    assert args.knowledge_path is None

                            