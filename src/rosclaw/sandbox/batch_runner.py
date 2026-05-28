"""BatchRunner — run multiple episodes in sequence with shared model cache."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from rosclaw.sandbox.sandbox_api import Sandbox
from rosclaw.sandbox.traces.recorder import EpisodeRecorder


class BatchRunner:
    """Run multiple sandbox episodes efficiently with model caching."""

    def __init__(self, robot_id: str, world_id: str = "empty", engine: str = "mujoco"):
        self._robot_id = robot_id
        self._world_id = world_id
        self._engine = engine

    def run_episodes(
        self,
        configs: list[dict[str, Any]],
        max_workers: int = 1,
        record: bool = False,
        output_dir: Path = Path("./runs"),
    ) -> list[dict[str, Any]]:
        """Run multiple episode configurations.

        Args:
            configs: List of episode configs (each dict has 'steps', 'action', etc.)
            max_workers: Number of parallel workers (1 = sequential)
            record: Whether to record episodes
            output_dir: Directory for recordings

        Returns:
            List of episode summaries
        """
        if max_workers <= 1:
            return [self._run_single(cfg, record, output_dir) for cfg in configs]

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._run_single, cfg, record, output_dir): i
                for i, cfg in enumerate(configs)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results.append((idx, future.result()))
                except Exception as e:
                    results.append((idx, {"error": str(e), "success": False}))

        # Sort by original order
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    def _run_single(
        self,
        config: dict[str, Any],
        record: bool,
        output_dir: Path,
    ) -> dict[str, Any]:
        """Run a single episode."""
        sandbox = Sandbox.create(
            robot_id=self._robot_id,
            world_id=self._world_id,
            engine=self._engine,
        )

        start = time.time()
        obs = sandbox.reset()

        recorder = None
        if record:
            recorder = EpisodeRecorder(sandbox.session, output_dir=output_dir)
            recorder.start()

        steps = config.get("steps", 100)
        action = config.get("action", {"type": "noop"})
        total_reward = 0.0

        for i in range(steps):
            result = sandbox.step(action)
            total_reward += result.reward
            if recorder:
                recorder.record_step(action, result)
            if result.terminated or result.truncated:
                steps = i + 1
                break

        sandbox.close()
        duration = time.time() - start

        summary = {
            "success": True,
            "total_steps": steps,
            "total_reward": total_reward,
            "duration_sec": duration,
            "robot_id": self._robot_id,
            "world_id": self._world_id,
        }

        if recorder:
            ep_dir = recorder.finish(summary)
            summary["episode_dir"] = str(ep_dir)

        return summary

    def benchmark(self, configs: list[dict[str, Any]], max_workers: int = 1) -> dict[str, Any]:
        """Run episodes and return benchmark statistics."""
        start = time.time()
        results = self.run_episodes(configs, max_workers=max_workers)
        total_time = time.time() - start

        total_steps = sum(r.get("total_steps", 0) for r in results)
        total_reward = sum(r.get("total_reward", 0.0) for r in results)
        errors = sum(1 for r in results if "error" in r)

        return {
            "episodes": len(configs),
            "workers": max_workers,
            "total_time_sec": total_time,
            "total_steps": total_steps,
            "total_reward": total_reward,
            "steps_per_sec": total_steps / total_time if total_time > 0 else 0,
            "errors": errors,
            "results": results,
        }
