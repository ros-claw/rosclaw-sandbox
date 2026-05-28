"""Tests for EventBus publishing integration."""

from rosclaw.sandbox import Sandbox
from rosclaw.sandbox.events.publisher import ListPublisher
from rosclaw.sandbox.events.schemas import (
    SandboxSessionStarted,
    SandboxSessionStopped,
    SandboxStepExecuted,
)


class TestSandboxEventPublishing:
    def test_reset_publishes_session_started(self):
        publisher = ListPublisher()
        sandbox = Sandbox.create(
            robot_id="universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
        )
        sandbox.reset()
        assert len(publisher.events) == 1
        assert publisher.events[0].event_type == "SandboxSessionStarted"
        assert publisher.events[0].robot_id == "universal_robots_ur5e"
        sandbox.close()

    def test_step_publishes_step_executed(self):
        publisher = ListPublisher()
        sandbox = Sandbox.create(
            robot_id="universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
        )
        sandbox.reset()
        sandbox.step({"type": "noop"})
        sandbox.step({"type": "noop"})
        # 1 start + 2 steps
        assert len(publisher.events) == 3
        assert publisher.events[1].event_type == "SandboxStepExecuted"
        assert publisher.events[1].step == 1
        assert publisher.events[2].step == 2
        sandbox.close()

    def test_close_publishes_session_stopped(self):
        publisher = ListPublisher()
        sandbox = Sandbox.create(
            robot_id="universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
        )
        sandbox.reset()
        sandbox.step({"type": "noop"})
        sandbox.close()
        assert len(publisher.events) == 3
        assert publisher.events[2].event_type == "SandboxSessionStopped"
        assert publisher.events[2].payload["total_steps"] == 1


class TestFirewallEventPublishing:
    def test_allow_publishes_firewall_action_allowed(self):
        from rosclaw.sandbox.events.schemas import FirewallActionAllowed
        from rosclaw.sandbox.firewall.gate import FirewallGate

        publisher = ListPublisher()
        with FirewallGate(
            "universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
        ) as gate:
            decision = gate.check({"type": "noop"})
            assert decision.decision == "ALLOW"

        assert len(publisher.events) == 1
        assert publisher.events[0].event_type == "FirewallActionAllowed"

    def test_block_publishes_firewall_action_blocked(self):
        from rosclaw.sandbox.events.schemas import FirewallActionBlocked
        from rosclaw.sandbox.firewall.gate import FirewallGate

        publisher = ListPublisher()
        with FirewallGate(
            "universal_robots_ur5e",
            world_id="empty",
            publisher=publisher,
        ) as gate:
            decision = gate.check({
                "type": "joint_position",
                "values": [3.5, -3.5, 3.5, -3.5, 3.5, -3.5],
            })
            assert decision.decision == "BLOCK"

        assert len(publisher.events) == 1
        assert publisher.events[0].event_type == "FirewallActionBlocked"
        assert publisher.events[0].risk_score > 0.7


class TestNullPublisherDefault:
    def test_sandbox_default_no_events(self):
        sandbox = Sandbox.create(
            robot_id="universal_robots_ur5e",
            world_id="empty",
        )
        sandbox.reset()
        sandbox.step({"type": "noop"})
        sandbox.close()
        # Should not raise; NullPublisher silently discards events
