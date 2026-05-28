"""EpisodeRecorder — records episode traces to disk."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rosclaw.sandbox.core.session import SandboxSession
from rosclaw.sandbox.core.types import StepResult


class EpisodeRecorder:
    """Records episode data to a structured directory."""

    def __init__(self, session: SandboxSession, output_dir: Path = Path("./runs")):
        self._session = session
        self._output_dir = output_dir
        self._ep_dir: Path | None = None
        self._trajectory_file = None
        self._events_file = None
        self._steps: list[dict] = []
        self._start_time: float = 0

    def start(self) -> None:
        """Start recording."""
        ep_id = f"ep_{int(time.time())}_{self._session.session_id[:6]}"
        self._ep_dir = self._output_dir / ep_id
        self._ep_dir.mkdir(parents=True, exist_ok=True)
        self._start_time = time.time()

        # Write metadata
        metadata = {
            "session_id": self._session.session_id,
            "robot_id": self._session.robot_id,
            "world_id": self._session.world_id,
            "task_id": self._session.task_id,
            "mode": self._session.mode,
            "engine": self._session.engine,
            "started_at": self._start_time,
        }
        (self._ep_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        self._trajectory_file = open(self._ep_dir / "trajectory.jsonl", "w")
        self._events_file = open(self._ep_dir / "events.jsonl", "w")

    def record_step(self, action: dict, result: StepResult) -> None:
        """Record one step."""
        if not self._trajectory_file:
            return
        record = {
            "step": len(self._steps),
            "timestamp": time.time(),
            "action": action,
            "observation": result.observation,
            "reward": result.reward,
            "terminated": result.terminated,
            "truncated": result.truncated,
            "info": result.info,
        }
        self._trajectory_file.write(json.dumps(record, default=str) + "\n")
        self._trajectory_file.flush()
        self._steps.append(record)

    def record_event(self, event: dict) -> None:
        """Record an event."""
        if not self._events_file:
            return
        event["timestamp"] = time.time()
        self._events_file.write(json.dumps(event, default=str) + "\n")
        self._events_file.flush()

    def finish(self, summary: dict | None = None) -> Path:
        """Finish recording and return episode directory."""
        if self._trajectory_file:
            self._trajectory_file.close()
        if self._events_file:
            self._events_file.close()

        if not self._ep_dir:
            return Path(".")

        # Write summary
        if summary is None:
            summary = {
                "total_steps": len(self._steps),
                "total_reward": sum(s.get("reward", 0) for s in self._steps),
                "success": False,
                "duration_sec": time.time() - self._start_time,
            }
        (self._ep_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))

        return self._ep_dir
