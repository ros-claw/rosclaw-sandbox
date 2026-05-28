"""ReplayEngine — replays a recorded episode from trace files."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class ReplayEngine:
    """Replays episodes from recorded trajectory files."""

    def __init__(self, episode_dir: Path):
        self._dir = Path(episode_dir)
        if not self._dir.is_dir():
            raise FileNotFoundError(f"Episode dir not found: {episode_dir}")

    def replay(self) -> dict[str, Any]:
        """Replay the episode and return summary."""
        metadata_path = self._dir / "metadata.json"
        trajectory_path = self._dir / "trajectory.jsonl"

        metadata = {}
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())

        steps = []
        if trajectory_path.exists():
            with open(trajectory_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        steps.append(json.loads(line))

        start = time.time()
        for step in steps:
            pass  # Replay state restoration placeholder
        duration = time.time() - start

        return {
            "steps": len(steps),
            "duration_sec": duration,
            "metadata": metadata,
        }
