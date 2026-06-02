"""Sandbox event schemas for Event Bus integration."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SandboxEvent:
    """Base event for all sandbox events."""
    event_type: str = ""
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    robot_id: str = ""
    task_id: str | None = None
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class SandboxSessionStarted(SandboxEvent):
    event_type: str = "SandboxSessionStarted"


@dataclass
class SandboxStepExecuted(SandboxEvent):
    event_type: str = "SandboxStepExecuted"
    step: int = 0


@dataclass
class SandboxSessionStopped(SandboxEvent):
    event_type: str = "SandboxSessionStopped"


@dataclass
class SandboxCollisionDetected(SandboxEvent):
    event_type: str = "SandboxCollisionDetected"
    geom1: str = ""
    geom2: str = ""


@dataclass
class SandboxTaskStarted(SandboxEvent):
    event_type: str = "SandboxTaskStarted"


@dataclass
class SandboxTaskSucceeded(SandboxEvent):
    event_type: str = "SandboxTaskSucceeded"
    total_steps: int = 0
    total_reward: float = 0.0


@dataclass
class SandboxTaskFailed(SandboxEvent):
    event_type: str = "SandboxTaskFailed"
    failure_type: str = ""
    reason: str = ""
    replay_id: str | None = None


@dataclass
class FirewallActionAllowed(SandboxEvent):
    event_type: str = "FirewallActionAllowed"
    risk_score: float = 0.0
    replay_id: str | None = None


@dataclass
class FirewallActionBlocked(SandboxEvent):
    event_type: str = "FirewallActionBlocked"
    risk_score: float = 0.0
    reason: str = ""
    replay_id: str | None = None


@dataclass
class SandboxReplayCreated(SandboxEvent):
    event_type: str = "SandboxReplayCreated"
    replay_dir: str = ""
