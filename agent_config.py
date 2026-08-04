from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    max_steps: int = 8

    def __post_init__(self) -> None:
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than 0.")