import argparse

from agent_config import AgentConfig


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run AgentLoop code review agent."
    )

    parser.add_argument(
        "--task",
        required=True,
        help="Task instruction for the agent.",
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=AgentConfig().max_steps,
        help="Maximum number of agent loop steps.",
    )

    parser.add_argument(
        "--max-rejected-final-answers",
        type=int,
        default=AgentConfig().max_rejected_final_answers,
        help="Maximum rejected final_answer attempts before stopping.",
    )

    parser.add_argument(
        "--max-rejected-tool-calls",
        type=int,
        default=AgentConfig().max_rejected_tool_calls,
        help="Maximum rejected tool calls before stopping.",
    )

    parser.add_argument(
        "--max-invalid-llm-outputs",
        type=int,
        default=AgentConfig().max_invalid_llm_outputs,
        help="Maximum invalid LLM outputs before stopping.",
    )

    return parser


def build_agent_config_from_args(args: argparse.Namespace) -> AgentConfig:
    return AgentConfig(
        max_steps=args.max_steps,
        max_rejected_final_answers=args.max_rejected_final_answers,
        max_rejected_tool_calls=args.max_rejected_tool_calls,
        max_invalid_llm_outputs=args.max_invalid_llm_outputs,
    )