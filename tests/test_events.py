"""Tests for event schemas and publishers."""

from rosclaw.sandbox.events.schemas import (
    FirewallActionBlocked,
    SandboxSessionStarted,
    SandboxTaskFailed,
)
from rosclaw.sandbox.events.publisher import ListPublisher, NullPublisher


class TestEvents:
    def test_session_started(self):
        e = SandboxSessionStarted(session_id="abc", robot_id="ur5e")
        assert e.event_type == "SandboxSessionStarted"
        d = e.to_dict()
        assert d["session_id"] == "abc"

    def test_firewall_blocked(self):
        e = FirewallActionBlocked(
            session_id="s1", robot_id="go2",
            risk_score=0.9, reason="collision",
        )
        assert e.event_type == "FirewallActionBlocked"
        assert e.risk_score == 0.9

    def test_task_failed(self):
        e = SandboxTaskFailed(
            session_id="s2", robot_id="ur5e",
            failure_type="collision", reason="wrist hit table",
        )
        assert e.failure_type == "collision"


class TestPublishers:
    def test_null_publisher(self):
        p = NullPublisher()
        p.publish(SandboxSessionStarted())  # should not raise

    def test_list_publisher(self):
        from rosclaw.sandbox.events.publisher import ListPublisher
        p = ListPublisher()
        p.publish(SandboxSessionStarted(session_id="x"))
        p.publish(SandboxTaskFailed(session_id="y"))
        assert len(p.events) == 2
