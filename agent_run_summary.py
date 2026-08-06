from dataclasses import dataclass
from typing import Any, cast

from agent_run_result import AgentRunResult


@dataclass(frozen=True)
class AgentRunSummary:
    result: AgentRunResult
    steps_count: int
    final_state: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.result, AgentRunResult):
            raise ValueError("AgentRunSummary requires an AgentRunResult.")

        if not isinstance(self.steps_count, int) or self.steps_count < 0:
            raise ValueError("AgentRunSummary steps_count must be a non-negative integer.")

        if not isinstance(self.final_state, dict):
            raise ValueError("AgentRunSummary final_state must be a dict.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.to_dict(),
            "steps_count": self.steps_count,
            "final_state": self.final_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentRunSummary":
        if not isinstance(data, dict):
            raise ValueError("AgentRunSummary.from_dict requires a dict.")

        expected_keys = {"result", "steps_count", "final_state"}
        actual_keys = set(data.keys())

        extra_keys = actual_keys - expected_keys
        missing_keys = expected_keys - actual_keys

        if extra_keys:
            raise ValueError(
                f"AgentRunSummary.from_dict received unexpected fields: {sorted(extra_keys)}"
            )

        if missing_keys:
            raise ValueError(
                f"AgentRunSummary.from_dict missing required fields: {sorted(missing_keys)}"
            )

        return cls(
            result=AgentRunResult.from_dict(data["result"]),
            steps_count=cast(int, data["steps_count"]),
            final_state=cast(dict[str, Any], data["final_state"]),
        )


def build_agent_run_summary(
    *,
    result: AgentRunResult,
    trace_steps: list[dict[str, Any]],
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
    )

