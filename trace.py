import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from dataclasses import asdict, is_dataclass
from enum import Enum

from agent_run_summary import AgentRunSummary

class TraceRecorder:
    def __init__(self) -> None:
        self.trace_dir = Path("traces")
        self.trace_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        unique_id = uuid4().hex[:8]

        self.trace_path = self.trace_dir / f"trace_{timestamp}_{unique_id}.json"

        self.steps: list[dict] = []

    def record(self, data: dict) -> None:
        self.steps.append(self._to_jsonable(data))
        self.trace_path.write_text(
            json.dumps(self.steps, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _to_jsonable(self, value):
        if is_dataclass(value):
            return self._to_jsonable(asdict(value))

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, Path):
            return str(value)

        if isinstance(value, dict):
            return {
                str(key): self._to_jsonable(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple, set)):
            return [
                self._to_jsonable(item)
                for item in value
            ]

        return value

    def write_summary(self, summary: AgentRunSummary) -> Path:
        summary_dir = Path("run_summaries")
        summary_dir.mkdir(parents=True, exist_ok=True)

        summary_path = summary_dir / f"{self.trace_path.stem}_summary.json"

        summary_path.write_text(
            json.dumps(summary.to_dict(), indent=2),
            encoding="utf-8",
        )

        return summary_path

    def read_steps(self) -> list[dict]:
        if not self.trace_path.exists():
            return []

        content = self.trace_path.read_text(encoding="utf-8")

        if not content.strip():
            return []

        data = json.loads(content)

        if not isinstance(data, list):
            raise ValueError("Trace file must contain a list of steps.")

        for step in data:
            if not isinstance(step, dict):
                raise ValueError("Each trace step must be a dict.")

        return data    