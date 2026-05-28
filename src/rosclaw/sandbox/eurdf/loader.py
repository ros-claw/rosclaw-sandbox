"""
e-URDF-Zoo loader — resolves robot profiles from the Physical DNA Registry.

Reads e_urdf.json + model.xml from the e-URDF-Zoo robots/ directory.
Optionally reads safety.yaml, capabilities.yaml, semantic.yaml if present.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from rosclaw.sandbox.core.errors import ProfileError
from rosclaw.sandbox.core.types import (
    ActuatorProfile,
    JointProfile,
    LinkProfile,
    RobotEmbodimentProfile,
    SensorProfile,
)


def find_eurdf_zoo_path() -> Path | None:
    """Locate the e-URDF-Zoo robots directory."""
    # 1. Environment variable
    env_path = os.environ.get("E_URDF_ZOO_PATH")
    if env_path:
        p = Path(env_path)
        robots = p / "robots" if (p / "robots").is_dir() else p
        if robots.is_dir():
            return robots

    # 2. Sibling to rosclaw_sandbox
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "e-urdf-zoo" / "robots",
        Path(__file__).resolve().parent.parent.parent.parent.parent / "e-urdf-zoo" / "robots",
        Path("/home/ubuntu/rosclaw/rosclaw/part/e-urdf-zoo/robots"),
        Path("/home/ubuntu/rosclaw/rosclaw/rosclaw-v1.0/e-urdf-zoo/robots"),
    ]
    for c in candidates:
        if c.is_dir():
            return c

    return None


def list_robots() -> list[str]:
    """List all robot IDs available in e-URDF-Zoo."""
    zoo_path = find_eurdf_zoo_path()
    if not zoo_path or not zoo_path.is_dir():
        return []
    return sorted(
        d.name for d in zoo_path.iterdir()
        if d.is_dir() and (d / "e_urdf.json").exists()
    )


def load_robot_profile(robot_id: str) -> RobotEmbodimentProfile:
    """Load a RobotEmbodimentProfile from e-URDF-Zoo."""
    zoo_path = find_eurdf_zoo_path()
    if not zoo_path:
        raise ProfileError(
            "e-URDF-Zoo not found. Set E_URDF_ZOO_PATH environment variable."
        )

    robot_dir = zoo_path / robot_id
    if not robot_dir.is_dir():
        available = list_robots()
        raise ProfileError(
            f"Robot '{robot_id}' not found. Available: {available}"
        )

    config_path = robot_dir / "e_urdf.json"
    if not config_path.exists():
        raise ProfileError(f"Missing e_urdf.json in {robot_dir}")

    with open(config_path) as f:
        config = json.load(f)

    # Resolve model paths
    mjcf_path = str(robot_dir / "model.xml") if (robot_dir / "model.xml").exists() else None
    urdf_path = str(robot_dir / "robot.urdf") if (robot_dir / "robot.urdf").exists() else None
    mesh_dir = str(robot_dir / "assets" / "meshes") if (robot_dir / "assets" / "meshes").is_dir() else None

    # Load optional YAML configs
    safety = _load_yaml_if_exists(robot_dir / "safety.yaml")
    capabilities = _load_yaml_if_exists(robot_dir / "capabilities.yaml")
    semantics_yaml = _load_yaml_if_exists(robot_dir / "semantic.yaml")
    benchmark = _load_yaml_if_exists(robot_dir / "benchmark.yaml")

    # Merge semantics from e_urdf.json + semantic.yaml
    semantics = config.get("semantics", {})
    if semantics_yaml:
        semantics.update(semantics_yaml)

    # Extract joint info from config or MJCF
    joints = _extract_joints(config, mjcf_path)
    links = _extract_links(config, mjcf_path)
    actuators = _extract_actuators(config, joints)
    sensors = _extract_sensors(config)

    kinematics = config.get("kinematics", {})
    dof = kinematics.get("dof", len([j for j in joints if j.joint_type != "fixed"]))

    # Determine base type
    robot_type = semantics.get("robot_type", "unknown")
    if robot_type in ("quadruped", "biped", "humanoid", "hexapod"):
        base_type = "floating"
    elif robot_type in ("mobile_base", "wheeled", "ugv"):
        base_type = "mobile"
    else:
        base_type = "fixed"

    return RobotEmbodimentProfile(
        robot_id=robot_id,
        name=config.get("embodiment_name", robot_id),
        urdf_path=urdf_path,
        mjcf_path=mjcf_path,
        mesh_dir=mesh_dir,
        base_type=base_type,
        dof=dof,
        joints=joints,
        links=links,
        sensors=sensors,
        actuators=actuators,
        safety=safety or {},
        capabilities=capabilities or {},
        semantics=semantics,
        benchmark=benchmark,
    )


def _load_yaml_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    import yaml
    with open(path) as f:
        return yaml.safe_load(f) or {}


def _extract_joints(config: dict, mjcf_path: str | None) -> list[JointProfile]:
    """Extract joint profiles from config or MJCF model."""
    joints = []

    # Try MJCF parsing first
    if mjcf_path:
        try:
            import mujoco
            model = mujoco.MjModel.from_xml_path(mjcf_path)
            for i in range(model.njnt):
                jnt_type_id = model.jnt_type[i]
                jnt_type = {0: "free", 1: "ball", 2: "slide", 3: "hinge"}.get(jnt_type_id, "hinge")
                name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
                if not name:
                    name = f"joint_{i}"

                lower = float(model.jnt_range[i, 0]) if model.jnt_limited[i] else -3.14
                upper = float(model.jnt_range[i, 1]) if model.jnt_limited[i] else 3.14

                joints.append(JointProfile(
                    name=name,
                    joint_type=jnt_type if jnt_type != "hinge" else "revolute",
                    lower_limit=lower,
                    upper_limit=upper,
                ))
            return joints
        except Exception:
            pass

    # Fallback: generate placeholder joints from DOF
    dof = config.get("kinematics", {}).get("dof", 0)
    for i in range(dof):
        joints.append(JointProfile(name=f"joint_{i}"))
    return joints


def _extract_links(config: dict, mjcf_path: str | None) -> list[LinkProfile]:
    """Extract link profiles."""
    links = []
    if mjcf_path:
        try:
            import mujoco
            model = mujoco.MjModel.from_xml_path(mjcf_path)
            for i in range(model.nbody):
                name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, i)
                if not name:
                    name = f"body_{i}"
                links.append(LinkProfile(name=name, mass=float(model.body_mass[i])))
            return links
        except Exception:
            pass
    return links


def _extract_actuators(config: dict, joints: list[JointProfile]) -> list[ActuatorProfile]:
    """Extract actuator profiles."""
    actuators = []
    for j in joints:
        if j.joint_type != "fixed":
            actuators.append(ActuatorProfile(
                name=f"{j.name}_actuator",
                joint=j.name,
                actuator_type="position",
                ctrl_range=(j.lower_limit, j.upper_limit),
            ))
    return actuators


def _extract_sensors(config: dict) -> list[SensorProfile]:
    """Extract sensor profiles from config."""
    sensors = []
    obs = config.get("observation_space", {}).get("proprioception", {})
    for key, enabled in obs.items():
        if enabled:
            sensors.append(SensorProfile(name=key, sensor_type="proprioception"))
    return sensors
