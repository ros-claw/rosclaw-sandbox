"""SandboxSession — lifecycle record for a single sandbox run."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class SandboxSession:
    """
    Tracks the lifecycle of one sandbox execution session.

    A session is created when a robot + world (+ task) combination is loaded,
    transitions through running/paused, and ends as closed or failed.
    """
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    robot_id: str = ""
    engine: Literal["mujoco"] = "mujoco"
    world_id: str = "empty"
    task_id: str | None = None
    mode: Literal["simulation", "firewall", "benchmark", "replay"] = "simulation"
    status: Literal["created", "running", "paused", "closed", "failed"] = "created"
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        self.status = "running"

    def pause(self) -> None:
        if self.status == "running":
            self.status = "paused"

    def resume(self) -> None:
        if self.status == "paused":
            self.status = "running"

    def close(self) -> None:
        self.status = "closed"

    def fail(self, reason: str = "") -> None:
        self.status = "failed"
        if reason:
            self.metadata["failure_reason"] = reason

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)
