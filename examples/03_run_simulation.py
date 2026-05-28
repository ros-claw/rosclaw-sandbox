#!/usr/bin/env python3
"""Example 03: Run a simple simulation."""

from rosclaw.sandbox import Sandbox

# Create sandbox
sandbox = Sandbox.create(
    robot_id="universal_robots_ur5e",
    world_id="tabletop",
    engine="mujoco"
)

# Reset and run
obs = sandbox.reset()
print(f"Initial observation: {obs}")

# Step 100 times
for i in range(100):
    action = {
        "type": "joint_position",
        "values": [0.0, -1.0, 1.5, 0.0, 1.5, 0.0]
    }
    result = sandbox.step(action)

    if i % 20 == 0:
        print(f"Step {i}: reward={result.reward:.3f}, terminated={result.terminated}")

print(f"\nFinal state: {sandbox.get_state()}")
sandbox.close()
