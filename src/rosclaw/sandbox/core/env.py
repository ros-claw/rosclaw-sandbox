"""SandboxEnv — the standard environment protocol for all physics backends."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from rosclaw.sandbox.core.types import StepResult


@runtime_checkable
class SandboxEnv(Protocol):
    """
    Protocol that every sandbox physics backend must implement.

    Modeled after the Gymnasium Env interface but adapted for
    robotics-specific needs (state get/set, contact info, etc.).
    """

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        """Reset the environment and return the initial observation."""
        ...

    def step(self, action: dict[str, Any]) -> StepResult:
        """Execute one control step and return StepResult."""
        ...

    def render(self, mode: str = "rgb_array") -> Any:
        """Render the current state. mode: 'rgb_array' | 'depth' | 'human'."""
        ...

    def get_state(self) -> dict[str, Any]:
        """Return full internal state (for replay / checkpoint)."""
        ...

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore internal state from a previous get_state() call."""
        ...

    def close(self) -> None:
        """Release all resources (engine, renderer, etc.)."""
        ...
