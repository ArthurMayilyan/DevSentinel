from dataclasses import dataclass
from typing import Literal


AgentRunStatus = Literal["completed", "stopped"]


@dataclass(frozen=True)
class AgentRunResult:
    status: AgentRunStatus
    answer: str | None = None
    stop_reason: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "stopped"}:
            raise ValueError(f"Invalid AgentRunResult status: {self.status}")

        if self.status == "completed":
            if not isinstance(self.answer, str) or not self.answer.strip():
                raise ValueError("Completed AgentRunResult requires a non-empty answer.")

            if self.stop_reason is not None:
                raise ValueError("Completed AgentRunResult must not have stop_reason.")

        if self.status == "stopped":
            if not isinstance(self.stop_reason, str) or not self.stop_reason.strip():
                raise ValueError("Stopped AgentRunResult requires a non-empty stop_reason.")

            if self.answer is not None:
                raise ValueError("Stopped AgentRunResult must not have answer.")

    @classmethod
    def completed(cls, answer: str) -> "AgentRunResult":
        return cls(
            status="completed",
            answer=answer,
            stop_reason=None,
        )

    @classmethod
    def stopped(cls, stop_reason: str) -> "AgentRunResult":
        return cls(
            status="stopped",
            answer=None,
            stop_reason=stop_reason,
        )

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_stopped(self) -> bool:
        return self.status == "stopped"

    