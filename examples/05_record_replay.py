#!/usr/bin/env python3
"""Example 05: Record and replay an episode."""

from pathlib import Path
from rosclaw.sandbox import Sandbox
from rosclaw.sandbox.traces.recorder import EpisodeRecorder

# Create sandbox
sandbox = Sandbox.create(
    robot_id="universal_robots_ur5e",
    world_id="empty"
)

# Start recording
recorder = EpisodeRecorder(sandbox.session, output_dir=Path("./runs"))
recorder.start()

# Run episode
obs = sandbox.reset()
total_reward = 0.0

for i in range(50):
    action = {
        "type": "joint_position",
        "values": [0.0, -1.0, 1.5, 0.0, 1.5, 0.0]
    }
    result = sandbox.step(action)
    recorder.record_step(action, result)
    total_reward += result.reward

# Finish recording
summary = {
    "total_steps": 50,
    "total_reward": total_reward,
    "success": False
}
episode_dir = recorder.finish(summary)
print(f"Episode recorded to: {episode_dir}")

# Replay
from rosclaw.sandbox.traces.replay import ReplayEngine

replayer = ReplayEngine(episode_dir)
replay_summary = replayer.replay()
print(f"\nReplayed {replay_summary['steps']} steps")
print(f"Duration: {replay_summary['duration_sec']:.3f}s")

sandbox.close()
