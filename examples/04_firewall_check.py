#!/usr/bin/env python3
"""Example 04: Check actions through the firewall."""

from rosclaw.sandbox.firewall.gate import FirewallGate

# Create firewall
firewall = FirewallGate(
    robot_id="universal_robots_ur5e",
    world_id="tabletop"
)

# Test safe action
safe_action = {
    "action_type": "joint_position",
    "values": [0.0, -1.0, 1.5, 0.0, 1.5, 0.0]
}

decision = firewall.check(safe_action)
print(f"Safe action: {decision.decision}")
print(f"  Risk score: {decision.risk_score:.2f}")
print(f"  Reason: {decision.reason}")

# Test dangerous action (exceeds joint limits)
dangerous_action = {
    "action_type": "joint_position",
    "values": [3.5, -3.5, 3.5, -3.5, 3.5, -3.5]
}

decision = firewall.check(dangerous_action)
print(f"\nDangerous action: {decision.decision}")
print(f"  Risk score: {decision.risk_score:.2f}")
print(f"  Reason: {decision.reason}")
print(f"  Violations: {decision.violated_constraints}")
