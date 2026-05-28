# ROSClaw Sandbox

[![Tests](https://img.shields.io/badge/tests-69%2F69%20passing-brightgreen)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

**The embodied physics simulation, validation, replay, and safety-gating layer for ROSClaw.**

ROSClaw Sandbox turns e-URDF robot embodiments into executable physical worlds, allowing agents, skills, providers, and policies to be tested before entering the real world.

> **Position in ROSClaw**: `Agent Runtime → Sandbox/Firewall → Practice → Memory/SeekDB → Dashboard`

## Features

- **Physics Simulation**: MuJoCo-based simulation with fallback world generation for any robot
- **Robot Registry**: Automatic loading from e-URDF-Zoo (63+ robots)
- **Safety Firewall**: Pre-execution action validation with joint limit checks and collision prediction
- **Episode Recording**: Full trajectory recording in JSONL format with replay support
- **EventBus Integration**: Publishes `SandboxSessionStarted`, `SandboxStepExecuted`, `FirewallActionBlocked`, etc.
- **Model Cache**: LRU cache for compiled MuJoCo models (avoids recompilation)
- **Batch Runner**: Run multiple episodes in parallel with benchmark statistics
- **World Builder**: 7 pre-configured environments (office, kitchen, factory, warehouse, etc.)
- **Multi-Stage Tasks**: Pick-and-place, navigation, sorting with sequential stage execution

## Installation

```bash
git clone https://github.com/ros-claw/rosclaw-sandbox.git
cd rosclaw-sandbox
pip install -e ".[mujoco,dev]"
```

### Requirements

- Python 3.10+
- MuJoCo 3.0+
- e-URDF-Zoo (set `E_URDF_ZOO_PATH`)

## Quick Start

### CLI

```bash
# Check environment health
rosclaw-sandbox doctor

# List available robots
rosclaw-sandbox robots list

# List available worlds
rosclaw-sandbox worlds list

# Validate a robot model
rosclaw-sandbox validate universal_robots_ur5e

# Run simulation
rosclaw-sandbox run --robot universal_robots_ur5e --world empty --steps 100 --headless

# Run with episode recording
rosclaw-sandbox run --robot universal_robots_ur5e --world office --steps 100 --record

# Firewall safety check
rosclaw-sandbox firewall check \
  --robot universal_robots_ur5e \
  --world tabletop \
  --action examples/actions/safe_reach.json

# Replay recorded episode
rosclaw-sandbox replay runs/ep_XXXX
```

### Python API

```python
from rosclaw.sandbox import Sandbox

# Simple simulation
with Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty") as sandbox:
    obs = sandbox.reset()
    for _ in range(100):
        result = sandbox.step({"type": "noop"})
    print(f"Steps: {sandbox.step_count}")

# With event publishing
from rosclaw.sandbox.events.publisher import ListPublisher

publisher = ListPublisher()
with Sandbox.create(
    robot_id="universal_robots_ur5e",
    world_id="office",
    publisher=publisher,
) as sandbox:
    sandbox.reset()
    sandbox.step({"type": "noop"})

print(f"Events: {[e.event_type for e in publisher.events]}")
# ['SandboxSessionStarted', 'SandboxStepExecuted', 'SandboxSessionStopped']
```

### Batch Benchmark

```python
from rosclaw.sandbox.batch_runner import BatchRunner

runner = BatchRunner(robot_id="universal_robots_ur5e", world_id="empty")
configs = [{"steps": 50, "action": {"type": "noop"}} for _ in range(10)]

bench = runner.benchmark(configs, max_workers=2)
print(f"Steps/sec: {bench['steps_per_sec']:.1f}")
```

## Architecture

```
rosclaw-sandbox/
├── core/           # Types, Session, Env protocol, Registry, Errors
│   ├── types.py           # RobotEmbodimentProfile, StepResult, FirewallDecision
│   ├── session.py         # SandboxSession lifecycle
│   ├── env.py             # SandboxEnv protocol
│   ├── registry.py        # Engine registry
│   └── errors.py          # Exception hierarchy
├── eurdf/          # e-URDF-Zoo bridge (Physical DNA loader)
│   └── loader.py          # load_robot_profile(), list_robots()
├── engines/        # Physics backends
│   └── mujoco/
│       ├── engine.py      # MujocoEngine (SandboxEnv implementation)
│       └── cache.py       # MujocoModelCache (LRU)
├── validator/      # Model & safety validation
│   └── model_validator.py # Validation checks for MJCF completeness
├── worlds/         # Scene building
│   └── builder.py         # load_world_spec(), list_worlds()
├── tasks/          # Task runtime
│   └── runtime.py         # TaskRuntime with multi-stage support
├── firewall/       # Safety gate
│   └── gate.py            # FirewallGate with pre-check + simulation
├── traces/         # Episode recording & replay
│   ├── recorder.py        # EpisodeRecorder (JSONL)
│   └── replay.py          # ReplayEngine
├── events/         # Event schemas & publishers
│   ├── schemas.py         # SandboxEvent subclasses
│   └── publisher.py       # NullPublisher, ListPublisher, RuntimePublisher
├── cli/            # Command-line interface
│   └── main.py            # rosclaw-sandbox CLI
└── sandbox_api.py  # High-level Sandbox facade
```

## World Environments

| World | Objects | Use Case |
|-------|---------|----------|
| `empty` | 0 | Minimal testing |
| `flat_ground` | 1 | Walking robots |
| `tabletop` | 5 | Manipulation tasks |
| `office` | 11 | Indoor navigation |
| `kitchen` | 9 | Service robotics |
| `factory` | 8 | Industrial automation |
| `warehouse` | 12 | Logistics |

## Task Types

| Task | Goal Type | Stages | Robot |
|------|-----------|--------|-------|
| `ur5e_reach_target` | reach_pose | 1 | UR5e |
| `ur5e_pick_cube` | pick | 1 | UR5e |
| `ur5e_pick_place_cube` | pick_and_place | 6 | UR5e |
| `ur5e_sort_objects` | sort_sequence | 2 | UR5e |
| `go2_stand` | stand | 1 | Go2 |
| `go2_walk_forward` | walk | 1 | Go2 |
| `go2_navigate_target` | navigate_to | 2 | Go2 |

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/rosclaw/sandbox --cov-report=term

# Run specific test suite
python -m pytest tests/test_firewall.py -v
python -m pytest tests/test_multistage_tasks.py -v
python -m pytest tests/test_performance.py -v
```

**Current Status**: 69 tests passing, 70% code coverage

## Integration with ROSClaw v1.0

Sandbox is designed as a standalone package that integrates into `rosclaw.sandbox` namespace via `pkgutil.extend_path`.

Future v1.1 integration:
- `SandboxRuntimeAdapter` registered in `Runtime._do_initialize()`
- `ActionGroundingInterceptor` in Agent Runtime
- Practice subscribes to `SandboxTaskSucceeded` / `FirewallActionBlocked`
- Dashboard visualizes sandbox state via EventBus

## License

MIT
