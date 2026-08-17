from dataclasses import dataclass
from typing import Any

from app_settings import get_app_settings


_SETTINGS = get_app_settings()

@dataclass(frozen=True)
class AgentConfig:
    max_steps: int = (
        _SETTINGS.agent.max_steps
    )

    max_rejected_final_answers: int = (
        _SETTINGS.agent.max_rejected_final_answers
    )

    max_rejected_tool_calls: int = (
        _SETTINGS.agent.max_rejected_tool_calls
    )

    max_invalid_llm_outputs: int = (
        _SETTINGS.agent.max_invalid_llm_outputs
    )

    require_report_for_final_answer: bool = True
    require_all_python_files_processed_for_final_answer: bool = True

    def __post_init__(self) -> None:
        self._validate_positive_int("max_steps", self.max_steps)
        self._validate_positive_int(
            "max_rejected_final_answers",
            self.max_rejected_final_answers,
        )
        self._validate_positive_int(
            "max_rejected_tool_calls",
            self.max_rejected_tool_calls,
        )
        self._validate_positive_int(
            "max_invalid_llm_outputs",
            self.max_invalid_llm_outputs,
        )

    @staticmethod
    def _validate_positive_int(name: str, value: int) -> None:
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer.")

        if value <= 0:
            raise ValueError(f"{name} must be greater than 0.")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_steps": self.max_steps,
            "max_rejected_final_answers": self.max_rejected_final_answers,
            "max_rejected_tool_calls": self.max_rejected_tool_calls,
            "max_invalid_llm_outputs": self.max_invalid_llm_outputs,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentConfig":
        if not isinstance(data, dict):
            raise ValueError("AgentConfig.from_dict requires a dict.")

        expected_keys = {
            "max_steps",
            "max_rejected_final_answers",
            "max_rejected_tool_calls",
            "max_invalid_llm_outputs",
        }

        actual_keys = set(data.keys())

        extra_keys = actual_keys - expected_keys
        missing_keys = expected_keys - actual_keys

        if extra_keys:
            raise ValueError(
                f"AgentConfig.from_dict received unexpected fields: {sorted(extra_keys)}"
            )

        if missing_keys:
            raise ValueError(
                f"AgentConfig.from_dict missing required fields: {sorted(missing_keys)}"
            )

        return cls(
            max_steps=data["max_steps"],
            max_rejected_final_answers=data["max_rejected_final_answers"],
            max_rejected_tool_calls=data["max_rejected_tool_calls"],
            max_invalid_llm_outputs=data["max_invalid_llm_outputs"],
        )