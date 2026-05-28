"""Tests for episode recording and replay."""

from pathlib import Path
import json
import pytest

from rosclaw.sandbox.traces.recorder import EpisodeRecorder
from rosclaw.sandbox.traces.replay import ReplayEngine
from rosclaw.sandbox.core.session import SandboxSession
from rosclaw.sandbox.core.types import StepResult


class TestEpisodeRecorder:
    def test_record_and_finish(self, tmp_path):
        session = SandboxSession(robot_id="ur5e", world_id="empty")
        recorder = EpisodeRecorder(session, output_dir=tmp_path)
        recorder.start()

        result = StepResult(observation={"q": [0.0]})
        recorder.record_step({"type": "noop"}, result)

        summary = {"total_steps": 1, "total_reward": 0.0, "success": True}
        ep_dir = recorder.finish(summary)

        assert ep_dir.exists()
        assert (ep_dir / "metadata.json").exists()
        assert (ep_dir / "trajectory.jsonl").exists()
        assert (ep_dir / "summary.json").exists()

        meta = json.loads((ep_dir / "metadata.json").read_text())
        assert meta["robot_id"] == "ur5e"

        summ = json.loads((ep_dir / "summary.json").read_text())
        assert summ["success"] is True

    def test_empty_finish(self, tmp_path):
        session = SandboxSession()
        recorder = EpisodeRecorder(session, output_dir=tmp_path)
        recorder.start()
        ep_dir = recorder.finish()
        assert ep_dir.exists()


class TestReplayEngine:
    def test_replay(self, tmp_path):
        session = SandboxSession(robot_id="ur5e", world_id="empty")
        recorder = EpisodeRecorder(session, output_dir=tmp_path)
        recorder.start()

        for i in range(3):
            result = StepResult(observation={"step": i})
            recorder.record_step({"type": "noop"}, result)

        recorder.finish({"total_steps": 3})
        ep_dir = [d for d in tmp_path.iterdir() if d.is_dir()][0]

        replayer = ReplayEngine(ep_dir)
        summary = replayer.replay()
        assert summary["steps"] == 3
