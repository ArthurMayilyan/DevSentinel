import json
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, is_dataclass
from enum import Enum


class TraceRecorder:
    def __init__(self, trace_dir: str = "traces"):
        Path(trace_dir).mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trace_path = Path(trace_dir) / f"trace_{timestamp}.json"
        self.steps = []

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
