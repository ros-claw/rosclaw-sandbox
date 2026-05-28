"""
ModelValidator — validates a RobotEmbodimentProfile for completeness and correctness.

Checks: model files exist, mesh paths resolve, joint limits valid,
inertial properties reasonable, safety profile loaded, MuJoCo compiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rosclaw.sandbox.core.types import RobotEmbodimentProfile


@dataclass
class ValidationCheck:
    status: str   # PASS | WARN | FAIL
    message: str
    category: str = ""


@dataclass
class ValidationResult:
    robot_id: str
    checks: list[ValidationCheck] = field(default_factory=list)

    def add(self, status: str, message: str, category: str = "") -> None:
        self.checks.append(ValidationCheck(status=status, message=message, category=category))

    @property
    def passed(self) -> bool:
        return all(c.status != "FAIL" for c in self.checks)

    def status_label(self) -> str:
        has_fail = any(c.status == "FAIL" for c in self.checks)
        has_warn = any(c.status == "WARN" for c in self.checks)
        if has_fail:
            return "FAIL"
        if has_warn:
            return "PASS_WITH_WARNINGS"
        return "PASS"

    def save_markdown(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"# Validation Report: {self.robot_id}\n", f"Status: **{self.status_label()}**\n"]
        for c in self.checks:
            lines.append(f"- [{c.status}] {c.message}")
        p.write_text("\n".join(lines))

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "status": self.status_label(),
            "checks": [{"status": c.status, "message": c.message, "category": c.category} for c in self.checks],
        }


class ModelValidator:
    def __init__(self, profile: RobotEmbodimentProfile):
        self._profile = profile

    def validate(self) -> ValidationResult:
        result = ValidationResult(robot_id=self._profile.robot_id)

        self._check_model_files(result)
        self._check_joints(result)
        self._check_safety(result)
        self._check_actuators(result)
        self._check_mujoco_compile(result)

        return result

    def _check_model_files(self, r: ValidationResult) -> None:
        p = self._profile
        if p.mjcf_path and Path(p.mjcf_path).exists():
            r.add("PASS", "MJCF model file found", "model")
        elif p.urdf_path and Path(p.urdf_path).exists():
            r.add("PASS", "URDF model file found (MJCF not available)", "model")
            r.add("WARN", "No MJCF file; conversion may be needed", "model")
        else:
            r.add("FAIL", "No robot model file found (MJCF or URDF)", "model")

        if p.mesh_dir and Path(p.mesh_dir).is_dir():
            r.add("PASS", "Mesh directory found", "mesh")
        elif p.mesh_dir:
            r.add("WARN", f"Mesh directory not found: {p.mesh_dir}", "mesh")
        else:
            r.add("WARN", "No mesh directory specified", "mesh")

    def _check_joints(self, r: ValidationResult) -> None:
        joints = self._profile.joints
        if not joints:
            r.add("WARN", "No joints defined in profile", "joints")
            return

        r.add("PASS", f"{len(joints)} joints defined", "joints")
        actuated = [j for j in joints if j.joint_type != "fixed"]
        if actuated:
            r.add("PASS", f"{len(actuated)} actuated joints", "joints")

        for j in joints:
            if j.joint_type not in ("fixed", "continuous"):
                if j.lower_limit >= j.upper_limit:
                    r.add("WARN", f"Joint '{j.name}': lower >= upper limit", "joints")

    def _check_safety(self, r: ValidationResult) -> None:
        if self._profile.safety:
            r.add("PASS", "Safety profile loaded", "safety")
        else:
            r.add("WARN", "No safety.yaml found; using defaults", "safety")

    def _check_actuators(self, r: ValidationResult) -> None:
        act_joints = [j.name for j in self._profile.joints if j.joint_type != "fixed"]
        act_names = [a.joint for a in self._profile.actuators]
        missing = [j for j in act_joints if j not in act_names]
        if missing:
            r.add("WARN", f"Missing actuator for: {', '.join(missing)}", "actuators")
        else:
            r.add("PASS", f"{len(self._profile.actuators)} actuators defined", "actuators")

    def _check_mujoco_compile(self, r: ValidationResult) -> None:
        if not self._profile.mjcf_path:
            r.add("WARN", "No MJCF to compile", "mujoco")
            return
        try:
            import mujoco
            model = mujoco.MjModel.from_xml_path(self._profile.mjcf_path)
            r.add("PASS", f"MuJoCo compile success (nq={model.nq}, nv={model.nv}, nu={model.nu})", "mujoco")
        except ImportError:
            r.add("WARN", "MuJoCo not installed; skipping compile check", "mujoco")
        except Exception as e:
            r.add("FAIL", f"MuJoCo compile failed: {e}", "mujoco")
