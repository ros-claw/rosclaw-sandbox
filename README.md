# ROSClaw Sandbox

**The embodied physics simulation, validation, replay, and safety-gating layer for ROSClaw.**

ROSClaw Sandbox turns e-URDF robot embodiments into executable physical worlds,
allowing agents, skills, providers, and policies to be tested before entering the real world.

- **Backend:** MuJoCo (first), Isaac Sim / Gazebo (future)
- **Safety:** ROSClaw Firewall — pre-execution action validation
- **Trace:** Episode recording, replay, and export (JSONL / MCAP / video)

## Quick Start

```bash
# Install
cd rosclaw_sandbox
pip install -e ".[mujoco,dev]"

# Check environment
rosclaw-sandbox doctor

# List robots
rosclaw-sandbox robots list

# Validate a robot
rosclaw-sandbox validate universal_robots_ur5e

# Run simulation
rosclaw-sandbox run --robot universal_robots_ur5e --world empty --steps 100 --headless

# Firewall check
rosclaw-sandbox firewall check \
  --robot universal_robots_ur5e \
  --world tabletop \
  --action examples/actions/safe_reach.json

# Replay
rosclaw-sandbox replay runs/ep_XXXX
```

## Python API

```python
from rosclaw.sandbox.sandbox_api import Sandbox

sandbox = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty", engine="mujoco")
obs = sandbox.reset()

for _ in range(100):
    result = sandbox.step({"type": "noop"})

sandbox.close()
```

## Architecture

```
rosclaw-sandbox/
├── core/         Types, Session, Env protocol, Registry, Errors
├── eurdf/        e-URDF-Zoo bridge (Physical DNA loader)
├── engines/      Physics backends (MuJoCo)
├── validator/    Model & safety validation
├── worlds/       Scene building
├── tasks/        Task runtime
├── firewall/     Safety gate (ALLOW / BLOCK)
├── traces/       Episode recording & replay
├── events/       Event schemas & publishers
├── server/       HTTP/WebSocket API (placeholder)
└── cli/          Command-line interface
```

## Module Position in ROSClaw

```
Agent Runtime → Sandbox/Firewall → Practice → Memory/SeekDB → Dashboard
```

## License

MIT
