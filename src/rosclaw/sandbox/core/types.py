"""
Core type definitions for rosclaw-sandbox.

Defines the canonical data structures used across all sandbox subsystems:
- RobotEmbodimentProfile: Physical DNA from e-URDF-Zoo
- StepResult: Gym-style step return
- FirewallDecision: Safety gate decision
- WorldSpec / TaskSpec: Configuration schemas
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Robot Embodiment Profile (Physical DNA)
# ---------------------------------------------------------------------------

@dataclass
class JointProfile:
    """Single joint description."""
    name: str
    joint_type: str = "revolute"
    lower_limit: float = -3.14
    upper_limit: float = 3.14
    velocity_limit: float = 3.14
    effort_limit: float = 100.0
    axis: list[float] = field(default_factory=lambda: [0.0, 0.0, 1.0])
    parent_link: str = ""
    child_link: str = ""
    damping: float = 0.0
    friction: float = 0.0


@dataclass
class LinkProfile:
    """Single link description."""
    name: str
    mass: float = 0.0
    visual_mesh: str | None = None
    collision_mesh: str | None = None
    semantic_tags: list[str] = field(default_factory=list)


@dataclass
class SensorProfile:
    """Sensor mounted on the robot."""
    name: str
    sensor_type: str = "unknown"
    parent_link: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActuatorProfile:
    """Actuator driving a joint."""
    name: str
    joint: str = ""
    actuator_type: str = "position"
    gear_ratio: float = 1.0
    ctrl_range: tuple[float, float] = (-3.14, 3.14)


@dataclass
class RobotEmbodimentProfile:
    """
    Complete physical DNA of a robot from e-URDF-Zoo.

    This is the single source of truth for the sandbox to load,
    validate, simulate, and firewall-check a robot.
    """
    robot_id: str
    name: str = ""
    urdf_path: str | None = None
    mjcf_path: str | None = None
    mesh_dir: str | None = None

    base_type: Literal["fixed", "floating", "mobile"] = "fixed"
    dof: int = 0

    joints: list[JointProfile] = field(default_factory=list)
    links: list[LinkProfile] = field(default_factory=list)
    sensors: list[SensorProfile] = field(default_factory=list)
    actuators: list[ActuatorProfile] = field(default_factory=list)

    safety: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)
    semantics: dict[str, Any] = field(default_factory=dict)
    benchmark: dict[str, Any] | None = None

    def get_joint_names(self) -> list[str]:
        return [j.name for j in self.joints]

    def get_actuated_joints(self) -> list[JointProfile]:
        return [j for j in self.joints if j.joint_type != "fixed"]

    def get_joint_limits(self) -> dict[str, tuple[float, float]]:
        return {
            j.name: (j.lower_limit, j.upper_limit)
            for j in self.joints
            if j.joint_type != "fixed"
        }

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
# Step Result (Gym-style)
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    """Return value from SandboxEnv.step()."""
    observation: dict[str, Any]
    reward: float = 0.0
    terminated: bool = False
    truncated: bool = False
    info: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Firewall Decision
# ---------------------------------------------------------------------------

@dataclass
class FirewallDecision:
    """Result of a firewall safety check."""
    decision: Literal[
        "ALLOW",
        "BLOCK",
        "MODIFY_AND_ALLOW",
        "REQUIRE_HUMAN_CONFIRMATION",
        "DEFER_TO_CONTROLLER",
    ]
    risk_score: float = 0.0
    reason: str = ""
    predicted_collision: bool = False
    violated_constraints: list[str] = field(default_factory=list)
    simulated_horizon_sec: float = 0.0
    replay_id: str | None = None
    modified_action: dict[str, Any] | None = None

    @property
    def is_allowed(self) -> bool:
        return self.decision in ("ALLOW", "MODIFY_AND_ALLOW")

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
# World Spec
# ---------------------------------------------------------------------------

@dataclass
class WorldObjectSpec:
    """A static or dynamic object in the world."""
    name: str
    geom_type: str = "box"
    size: list[float] = field(default_factory=lambda: [0.1, 0.1, 0.1])
    position: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    orientation: list[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])
    rgba: list[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 1.0])
    mass: float = 0.0
    mesh_path: str | None = None


@dataclass
class WorldSpec:
    """Description of a simulation world / scene."""
    world_id: str
    name: str = ""
    gravity: list[float] = field(default_factory=lambda: [0.0, 0.0, -9.81])
    ground_plane: bool = True
    timestep: float = 0.002
    objects: list[WorldObjectSpec] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorldSpec":
        objects = [WorldObjectSpec(**obj) for obj in data.get("objects", [])]
        return cls(
            world_id=data["world_id"],
            name=data.get("name", data["world_id"]),
            gravity=data.get("gravity", [0.0, 0.0, -9.81]),
            ground_plane=data.get("ground_plane", True),
            timestep=data.get("timestep", 0.002),
            objects=objects,
        )


# ---------------------------------------------------------------------------
# Task Spec
# ---------------------------------------------------------------------------

@dataclass
class TaskSpec:
    """Description of a task to run in the sandbox."""
    task_id: str
    robot_id: str = ""
    world_id: str = "empty"
    name: str = ""

    action_type: str = "joint_position"
    action_hz: int = 20

    observations: list[str] = field(default_factory=lambda: [
        "joint_position", "joint_velocity",
    ])

    goal_type: str = "reach_pose"
    goal_params: dict[str, Any] = field(default_factory=dict)

    max_steps: int = 500
    success_distance: float = 0.03
    collision_fail: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskSpec":
        action = data.get("action", {})
        observation = data.get("observation", [])
        goal = data.get("goal", {})
        termination = data.get("termination", {})

        return cls(
            task_id=data["task_id"],
            robot_id=data.get("robot_id", ""),
            world_id=data.get("world_id", "empty"),
            name=data.get("name", data["task_id"]),
            action_type=action.get("type", "joint_position"),
            action_hz=action.get("hz", 20),
            observations=observation if observation else ["joint_position", "joint_velocity"],
            goal_type=goal.get("type", "reach_pose"),
            goal_params=goal,
            max_steps=termination.get("max_steps", 500),
            success_distance=termination.get("success_distance", 0.03),
            collision_fail=termination.get("collision_fail", True),
        )
