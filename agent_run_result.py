from dataclasses import dataclass
from typing import Any, Literal, cast
from agent_stop_reasons import STOP_REASON_BY_CODE

AgentRunStatus = Literal["completed", "stopped"]


@dataclass(frozen=True)
class AgentRunResult:
    status: AgentRunStatus
    answer: str | None = None
    stop_reason: str | None = None
    stop_reason_code: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "stopped"}:
            raise ValueError(f"Invalid AgentRunResult status: {self.status}")

        if self.status == "completed":
            if not isinstance(self.answer, str) or not self.answer.strip():
                raise ValueError("Completed AgentRunResult requires a non-empty answer.")

            if self.stop_reason is not None:
                raise ValueError("Completed AgentRunResult must not have stop_reason.")

            if self.stop_reason_code is not None:
                raise ValueError("Completed AgentRunResult must not have stop_reason_code.")
    
        if self.status == "stopped":
            if not isinstance(self.stop_reason, str) or not self.stop_reason.strip():
                raise ValueError("Stopped AgentRunResult requires a non-empty stop_reason.")

            if not isinstance(self.stop_reason_code, str) or not self.stop_reason_code.strip():
                raise ValueError("Stopped AgentRunResult requires a non-empty stop_reason_code.")

            expected_stop_reason = STOP_REASON_BY_CODE.get(self.stop_reason_code)

            if expected_stop_reason is None:
                raise ValueError(f"Unknown stop_reason_code: {self.stop_reason_code}")

            if self.stop_reason != expected_stop_reason:
                raise ValueError(
                    "stop_reason does not match stop_reason_code. "
                    f"Expected {expected_stop_reason!r} for code {self.stop_reason_code!r}."
                )

            if self.answer is not None:
                raise ValueError("Stopped AgentRunResult must not have answer.")
    
            
    @classmethod
    def completed(cls, answer: str) -> "AgentRunResult":
        return cls(
            status="completed",
            answer=answer,
            stop_reason=None,
            stop_reason_code=None,
        )


    @classmethod
    def stopped(cls, stop_reason: str, stop_reason_code: str) -> "AgentRunResult":
        return cls(
            status="stopped",
            answer=None,
            stop_reason=stop_reason,
            stop_reason_code=stop_reason_code,
        )

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_stopped(self) -> bool:
        return self.status == "stopped"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "answer": self.answer,
            "stop_reason": self.stop_reason,
            "stop_reason_code": self.stop_reason_code,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRunResult":
        if not isinstance(data, dict):
            raise ValueError("AgentRunResult.from_dict requires a dict.")

        expected_keys = {"status", "answer", "stop_reason", "stop_reason_code"}
        actual_keys = set(data.keys())

        extra_keys = actual_keys - expected_keys
        missing_keys = expected_keys - actual_keys

        if extra_keys:
            raise ValueError(
                f"AgentRunResult.from_dict received unexpected fields: {sorted(extra_keys)}"
            )

        if missing_keys:
            raise ValueError(
                f"AgentRunResult.from_dict missing required fields: {sorted(missing_keys)}"
            )

        status = data["status"]

        if status not in {"completed", "stopped"}:
            raise ValueError(f"Invalid AgentRunResult status: {status}")

        return cls(
            status=cast(AgentRunStatus, status),
            answer=data["answer"],
            stop_reason=data["stop_reason"],
            stop_reason_code=data["stop_reason_code"],
        )

    @classmethod
    def stopped_with_code(cls, stop_reason_code: str) -> "AgentRunResult":
        stop_reason = STOP_REASON_BY_CODE.get(stop_reason_code)

        if stop_reason is None:
            raise ValueError(f"Unknown stop_reason_code: {stop_reason_code}")

        return cls.stopped(
            stop_reason=stop_reason,
            stop_reason_code=stop_reason_code,
        )    