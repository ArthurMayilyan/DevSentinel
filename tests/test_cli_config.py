import pytest

from agent_config import AgentConfig
from cli_config import build_agent_config_from_args, build_arg_parser


def test_cli_parser_requires_task():
    parser = build_arg_parser()

    with pytest.raises(SystemExit):
        parser.parse_args([])


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

        