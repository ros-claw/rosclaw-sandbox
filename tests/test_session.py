"""Tests for SandboxSession."""

from rosclaw.sandbox.core.session import SandboxSession


class TestSandboxSession:
    def test_create(self):
        s = SandboxSession(robot_id="ur5e", world_id="empty")
        assert s.robot_id == "ur5e"
        assert s.status == "created"
        assert s.session_id

    def test_lifecycle(self):
        s = SandboxSession()
        s.start()
        assert s.status == "running"
        s.pause()
        assert s.status == "paused"
        s.resume()
        assert s.status == "running"
        s.close()
        assert s.status == "closed"

    def test_fail(self):
        s = SandboxSession()
        s.fail("test error")
        assert s.status == "failed"
        assert s.metadata["failure_reason"] == "test error"
