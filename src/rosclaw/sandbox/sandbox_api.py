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
        step_event_interval: int = 10,
    ):
        """Initialize a Sandbox facade.

        Args:
            session: Active sandbox session tracking lifecycle.
            engine: Physics engine backend (e.g., MujocoEngine).
            profile: Robot embodiment profile (optional).
            publisher: Event publisher for telemetry. Defaults to NullPublisher.
            step_event_interval: Publish step events every N steps (minimum 1).

        Raises:
            ValueError: If ``session`` or ``engine`` is None, or if
                ``step_event_interval`` is not a positive integer.
        """
        if session is None:
            raise ValueError("session cannot be None")
        if engine is None:
            raise ValueError("engine cannot be None")
        if not isinstance(step_event_interval, int) or step_event_interval < 1:
            raise ValueError("step_event_interval must be a positive integer")

        self.session = session
        self._engine = engine
        self._profile = profile
        self._step_count = 0
        self._publisher = publisher or NullPublisher()
        self._step_event_interval = step_event_interval
        self._closed = False

    @classmethod
    def create(
        cls,
        robot_id: str,
        world_id: str = "empty",
        engine: str = "mujoco",
        task_id: str | None = None,
        mode: str = "simulation",
        publisher: Any = None,
        step_event_interval: int = 10,
    ) -> "Sandbox":
        """Create a new sandbox session.

        Args:
            robot_id: Identifier for the robot to load.
            world_id: World/scene identifier. Defaults to ``"empty"``.
            engine: Physics engine name. Defaults to ``"mujoco"``.
            task_id: Optional task identifier.
            mode: Execution mode (``simulation``, ``firewall``, ``benchmark``, ``replay``).
            publisher: Event publisher for telemetry.
            step_event_interval: Publish step events every N steps (minimum 1).

        Raises:
            ProfileError: If the robot profile cannot be loaded.
            EngineError: If the requested engine is unavailable.
        """
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
        return cls(
            session=session,
            engine=eng,
            profile=profile,
            publisher=publisher,
            step_event_interval=step_event_interval,
        )

    def _ensure_open(self) -> None:
        """Raise RuntimeError if the sandbox has been closed."""
        if self._closed:
            raise RuntimeError("Sandbox has been closed")

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        """Reset the simulation to its initial state.

        Args:
            seed: Optional random seed for reproducibility.

        Returns:
            Initial observation dictionary.
        """
        self._ensure_open()
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
        """Execute one simulation step with the given action.

        Args:
            action: Action dictionary. Expected schema::

                {"type": "noop"} |
                {"type": "joint_position", "values": [...]} |
                {"type": "torque", "values": [...]}

        Returns:
            StepResult containing observation, reward, terminated, truncated, info.
        """
        self._ensure_open()
        result = self._engine.step(action)
        self._step_count += 1
        # Frequency-controlled step events: publish every N steps + first step
        # Reduces EventBus load from 50Hz to ~5Hz (default interval=10)
        if (
            self._step_count == 1
            or self._step_count % self._step_event_interval == 0
        ):
            self._publisher.publish(SandboxStepExecuted(
                session_id=self.session.session_id,
                robot_id=self.session.robot_id,
                step=self._step_count,
            ))
        return result

    def render(self, mode: str = "rgb_array") -> Any:
        """Render the current simulation frame.

        Args:
            mode: Render mode. ``"rgb_array"`` returns a numpy array.
                Other modes may return None in headless environments.

        Returns:
            Rendered frame or None if rendering is unavailable.
        """
        self._ensure_open()
        return self._engine.render(mode=mode)

    def get_state(self) -> dict[str, Any]:
        """Return the current simulation state.

        Returns:
            Dictionary with keys ``"qpos"``, ``"qvel"``, ``"time"``, ``"step"``.
        """
        self._ensure_open()
        return self._engine.get_state()

    def set_state(self, state: dict[str, Any]) -> None:
        """Restore simulation state.

        Args:
            state: State dictionary with optional keys ``"qpos"``, ``"qvel"``, ``"step"``.
        """
        self._ensure_open()
        self._engine.set_state(state)
        self._step_count = state.get("step", self._step_count)

    def close(self) -> None:
        """Close the sandbox and release all resources.

        Idempotent: safe to call multiple times.
        """
        if self._closed:
            return
        self._closed = True
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
        """Number of steps taken since the last reset."""
        return self._step_count

    @property
    def is_fallback(self) -> bool:
        """True if the engine loaded a degraded fallback model."""
        return getattr(self._engine, "is_fallback", False)
