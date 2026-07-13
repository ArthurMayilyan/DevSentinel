from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    returns: str
    when_to_use: str
    when_not_to_use: str
    function: Callable[..., Any] | None
