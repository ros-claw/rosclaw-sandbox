"""Tests for FirewallGate."""

import pytest
from rosclaw.sandbox.firewall.gate import FirewallGate
from rosclaw.sandbox.core.errors import ProfileError


class TestFirewallGate:
    def test_block_dangerous_action(self):
        with FirewallGate("universal_robots_ur5e", world_id="empty") as gate:
            # Values exceeding joint limits
            action = {
                "type": "joint_position",
                "values": [3.5, -3.5, 3.5, -3.5, 3.5, -3.5],
            }
            decision = gate.check(action)
            assert decision.decision == "BLOCK"
            assert decision.risk_score > 0.7
            assert decision.replay_id is not None
            assert len(decision.violated_constraints) > 0

    def test_allow_safe_action(self):
        with FirewallGate("universal_robots_ur5e", world_id="empty") as gate:
            action = {
                "type": "joint_position",
                "values": [0.0, -1.0, 1.5, 0.0, 1.5, 0.0],
            }
            decision = gate.check(action)
            assert decision.decision == "ALLOW"
            assert decision.risk_score < 0.1
            assert decision.is_allowed

    def test_invalid_robot(self):
        with pytest.raises(ProfileError):
            FirewallGate("nonexistent_robot_xyz")

    def test_context_manager(self):
        gate = FirewallGate("universal_robots_ur5e", world_id="empty")
        with gate:
            decision = gate.check({"type": "noop"})
            assert decision.decision == "ALLOW"
        # After exit, engine should be closed
        assert gate._engine is None
