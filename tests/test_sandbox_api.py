"""Tests for Sandbox high-level API."""

from rosclaw.sandbox.sandbox_api import Sandbox
from rosclaw.sandbox.core.errors import ProfileError
import pytest


class TestSandboxContextManager:
    def test_enter_exit(self):
        with Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty") as sandbox:
            assert sandbox.session.status == "created"
            obs = sandbox.reset()
            assert sandbox.session.status == "running"
            assert sandbox.step_count == 0
            result = sandbox.step({"type": "noop"})
            assert sandbox.step_count == 1
        assert sandbox.session.status == "closed"

    def test_close_idempotent(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        # Second close should not raise
        sandbox.close()

    def test_invalid_robot(self):
        with pytest.raises(ProfileError):
            Sandbox.create(robot_id="nonexistent_robot_xyz")

    def test_render_headless(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty", engine="mujoco")
        sandbox.reset()
        # Headless render should return None or array
        img = sandbox.render(mode="rgb_array")
        sandbox.close()

    def test_state_roundtrip(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        state = sandbox.get_state()
        assert "time" in state
        assert "step" in state

        sandbox.step({"type": "noop"})
        sandbox.set_state(state)
        assert sandbox.step_count == state["step"]
        sandbox.close()
