from dataclasses import dataclass, field
from typing import Any

from agent_run_result import AgentRunResult


@dataclass(frozen=True)
class AgentRunSummary:
    result: AgentRunResult
    steps_count: int
    final_state: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.result, AgentRunResult):
            raise ValueError("result must be an AgentRunResult.")

        if type(self.steps_count) is not int:
            raise ValueError("steps_count must be an integer.")

        if self.steps_count < 0:
            raise ValueError("steps_count must be greater than or equal to 0.")

        if not isinstance(self.final_state, dict):
            raise ValueError("final_state must be a dictionary.")

        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary or None.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.to_dict(),
            "steps_count": self.steps_count,
            "final_state": self.final_state,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRunSummary":
        if not isinstance(data, dict):
            raise ValueError("summary data must be a dictionary.")

        expected_keys = {
            "result",
            "steps_count",
            "final_state",
            "metadata",
        }

        if set(data) != expected_keys:
            raise ValueError("summary data has unexpected keys.")

        return cls(
            result=AgentRunResult.from_dict(data["result"]),
            steps_count=data["steps_count"],
            final_state=data["final_state"],
            metadata=data["metadata"],
        )
    

def build_agent_run_summary(
    *,
    result: AgentRunResult,
    trace_steps: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> AgentRunSummary:
    if not isinstance(trace_steps, list):
        raise ValueError("trace_steps must be a list.")

    final_state: dict[str, Any] = {}

    if trace_steps:
        last_step = trace_steps[-1]

        if not isinstance(last_step, dict):
            raise ValueError("Each trace step must be a dict.")

        state_after = last_step.get("state_after")

        if isinstance(state_after, dict):
            final_state = state_after

    return AgentRunSummary(
        result=result,
        steps_count=len(trace_steps),
        final_state=final_state,
        metadata=metadata,
    )

