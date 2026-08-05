from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    max_steps: int = 8
    max_rejected_final_answers: int = 3
    max_rejected_tool_calls: int = 5
    max_invalid_llm_outputs: int = 3

    def __post_init__(self) -> None:
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than 0.")

        if self.max_rejected_final_answers <= 0:
            raise ValueError("max_rejected_final_answers must be greater than 0.")

        if self.max_rejected_tool_calls <= 0:
            raise ValueError("max_rejected_tool_calls must be greater than 0.")

        if self.max_invalid_llm_outputs <= 0:
            raise ValueError("max_invalid_llm_outputs must be greater than 0.")