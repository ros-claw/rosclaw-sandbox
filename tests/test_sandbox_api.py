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

    # --- use-after-close guards ---

    def test_step_after_close_raises(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        with pytest.raises(RuntimeError, match="closed"):
            sandbox.step({"type": "noop"})

    def test_render_after_close_raises(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        with pytest.raises(RuntimeError, match="closed"):
            sandbox.render()

    def test_get_state_after_close_raises(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        with pytest.raises(RuntimeError, match="closed"):
            sandbox.get_state()

    def test_set_state_after_close_raises(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        with pytest.raises(RuntimeError, match="closed"):
            sandbox.set_state({})

    def test_reset_after_close_raises(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        sandbox.close()
        with pytest.raises(RuntimeError, match="closed"):
            sandbox.reset()

    # --- validation ---

    def test_step_event_interval_validation(self):
        with pytest.raises(ValueError, match="positive integer"):
            Sandbox.create(
                robot_id="universal_robots_ur5e",
                world_id="empty",
                step_event_interval=0,
            )

    def test_step_event_interval_negative(self):
        with pytest.raises(ValueError, match="positive integer"):
            Sandbox.create(
                robot_id="universal_robots_ur5e",
                world_id="empty",
                step_event_interval=-1,
            )

    def test_create_invalid_engine(self):
        from rosclaw.sandbox.core.errors import EngineError
        with pytest.raises(EngineError):
            Sandbox.create(
                robot_id="universal_robots_ur5e",
                world_id="empty",
                engine="nonexistent_engine_xyz",
            )

    # --- properties & state ---

    def test_is_fallback_property(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        assert isinstance(sandbox.is_fallback, bool)
        sandbox.close()

    def test_step_count_accurate(self):
        sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        sandbox.reset()
        assert sandbox.step_count == 0
        sandbox.step({"type": "noop"})
        assert sandbox.step_count == 1
        sandbox.step({"type": "noop"})
        assert sandbox.step_count == 2
        sandbox.reset()
        assert sandbox.step_count == 0
        sandbox.close()

    def test_context_manager_exception_cleanup(self):
        sandbox = None
        try:
            with Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty") as sb:
                sandbox = sb
                sb.reset()
                raise ValueError("intentional")
        except ValueError:
            pass
        assert sandbox is not None
        assert sandbox.session.status == "closed"

    # --- init validation ---

    def test_init_rejects_none_session(self):
        from rosclaw.sandbox.core.registry import create_engine
        engine = create_engine("mujoco", robot_profile=None, world_id="empty")
        with pytest.raises(ValueError, match="session cannot be None"):
            Sandbox(session=None, engine=engine)
        engine.close()

    def test_init_rejects_none_engine(self):
        from rosclaw.sandbox.core.session import SandboxSession
        session = SandboxSession(robot_id="test")
        with pytest.raises(ValueError, match="engine cannot be None"):
            Sandbox(session=session, engine=None)

    # --- step event frequency ---

    def test_step_event_interval_one_publishes_every_step(self):
        from rosclaw.sandbox.events.publisher import ListPublisher
        publisher = ListPublisher()
        sandbox = Sandbox.create(
            robot_id="universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
            step_event_interval=1,
        )
        sandbox.reset()
        sandbox.step({"type": "noop"})
        sandbox.step({"type": "noop"})
        sandbox.step({"type": "noop"})
        # 1 start + 3 steps = 4 events
        assert len(publisher.events) == 4
        sandbox.close()
