

DEFAULT_RULES = [
    "Use only available tools.",
    "Tool arguments must follow the tool argument contract.",
    "Do not invent findings before reading files.",
    "Call write_report only after all relevant files are inspected and findings are added.",
    "Do not provide final_answer before the report is written.",
    "final_answer.answer must be a non-empty string.",
]

class PromptBuilder:
    def __init__(
        self,
        agent_role: str = "an autonomous code review agent",
        task_description: str = (
            "inspect project files, identify issues, add findings, "
            "write a report, and only then provide a final answer"
        ),
        rules: list[str] | None = None,
        examples: list[str] | None = None,
    ) -> None:
        self.agent_role = agent_role
        self.task_description = task_description
        self.rules = rules or DEFAULT_RULES
        self.examples = examples or []

    def build_system_prompt(
        self,
        *,
        tools_description: str,
    ) -> str:
        rules_text = "\n".join(
            f"- {rule}"
            for rule in self.rules
        )

        examples_text = ""

        if self.examples:
            examples_text = "\n\nExamples:\n" + "\n\n".join(self.examples)

        return f"""
    You are {self.agent_role}.

    Your task is to {self.task_description}.

    You must communicate using only valid JSON objects.

    Valid output types:

    1. Tool call:

    {{
    "type": "tool_call",
    "tool": "<tool_name>",
    "arguments": {{
        "...": "..."
    }}
    }}

    2. Final answer:

    {{
    "type": "final_answer",
    "answer": "..."
    }}

    Rules:
    {rules_text}{examples_text}

    Available tools:
    {tools_description}
    """.strip()