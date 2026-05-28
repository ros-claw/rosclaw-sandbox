"""
Sandbox — high-level API for programmatic use.

Example:
    from rosclaw.sandbox import Sandbox

    sandbox = Sandbox.create(robot_id="ur5e", world_id="empty", engine="mujoco")
    obs = sandbox.reset()
    for _ in range(100):
        result = sandbox.step({"type": "noop"})
    sandbox.close()
"""

from __future__ import annotations

from typing import Any

from rosclaw.sandbox.core.session import SandboxSession
from rosclaw.sandbox.core.types import StepResult
from rosclaw.sandbox.events.publisher import NullPublisher
from rosclaw.sandbox.events.schemas import (
    SandboxSessionStarted,
    SandboxSessionStopped,
    SandboxStepExecuted,
)


class Sandbox:
    """High-level facade for sandbox operations."""

    def __init__(
        self,
        session: SandboxSession,
        engine: Any,
        profile: Any = None,
        publisher: Any = None,
    ):
        self.session = session
        self._engine = engine
        self._profile = profile
        self._step_count = 0
        self._publisher = publisher or NullPublisher()

    @classmethod
    def create(
        cls,
        robot_id: str,
        world_id: str = "empty",
        engine: str = "mujoco",
        task_id: str | None = None,
        mode: str = "simulation",
        publisher: Any = None,
    ) -> "Sandbox":
        """Create a new sandbox session."""
        from rosclaw.sandbox.eurdf.loader import load_robot_profile
        from rosclaw.sandbox.core.registry import create_engine

        try:
            import rosclaw.sandbox.engines.mujoco  # noqa: F401
        except ImportError:
            pass

        profile = load_robot_profile(robot_id)
        session = SandboxSession(
            robot_id=robot_id, engine=engine, world_id=world_id,
            task_id=task_id, mode=mode,
        )
        eng = create_engine(engine, robot_profile=profile, world_id=world_id)
        return cls(session=session, engine=eng, profile=profile, publisher=publisher)

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        self.session.start()
        self._step_count = 0
        obs = self._engine.reset(seed=seed)
        self._publisher.publish(SandboxSessionStarted(
            session_id=self.session.session_id,
            robot_id=self.session.robot_id,
            task_id=self.session.task_id,
        ))
        return obs

    def step(self, action: dict[str, Any]) -> StepResult:
        result = self._engine.step(action)
        self._step_count += 1
        self._publisher.publish(SandboxStepExecuted(
            session_id=self.session.session_id,
            robot_id=self.session.robot_id,
            step=self._step_count,
        ))
        return result

    def render(self, mode: str = "rgb_array") -> Any:
        return self._engine.render(mode=mode)

    def get_state(self) -> dict[str, Any]:
        return self._engine.get_state()

    def set_state(self, state: dict[str, Any]) -> None:
        self._engine.set_state(state)
        self._step_count = state.get("step", self._step_count)

    def close(self) -> None:
        self._publisher.publish(SandboxSessionStopped(
            session_id=self.session.session_id,
            robot_id=self.session.robot_id,
            task_id=self.session.task_id,
            payload={"total_steps": self._step_count, "status": self.session.status},
        ))
        self._engine.close()
        self.session.close()

    def __enter__(self) -> "Sandbox":
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Ensure cleanup on context exit."""
        self.close()

    @property
    def step_count(self) -> int:
        return self._step_count
