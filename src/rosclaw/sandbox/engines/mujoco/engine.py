"""
MujocoEngine — MuJoCo physics simulation backend.

Implements the SandboxEnv protocol. Loads MJCF models, runs physics
simulation, provides joint/contact state, and supports headless rendering.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from rosclaw.sandbox.core.errors import EngineError
from rosclaw.sandbox.core.types import RobotEmbodimentProfile, StepResult
from rosclaw.sandbox.engines.mujoco.cache import MujocoModelCache


class MujocoEngine:
    """MuJoCo-based physics engine implementing SandboxEnv protocol."""

    def __init__(
        self,
        robot_profile: RobotEmbodimentProfile | None = None,
        world_id: str = "empty",
        headless: bool = True,
        timestep: float = 0.002,
        **kwargs: Any,
    ):
        try:
            import mujoco
        except ImportError:
            raise EngineError("MuJoCo not installed. Run: pip install mujoco")

        self._mujoco = mujoco
        self._profile = robot_profile
        self._world_id = world_id
        self._headless = headless
        self._timestep = timestep
        self._model: Any = None
        self._data: Any = None
        self._step_count = 0
        self._renderer: Any = None

        self._load_model()

    def _load_model(self) -> None:
        """Load MJCF model from robot profile or build a minimal world.

        Uses MujocoModelCache to avoid recompiling identical models.
        """
        mj = self._mujoco
        cache_key = self._build_cache_key()

        # Try cache first
        cached = MujocoModelCache.get(cache_key)
        if cached is not None:
            self._model = cached
            self._data = mj.MjData(self._model)
            return

        if self._profile and self._profile.mjcf_path and Path(self._profile.mjcf_path).exists():
            try:
                self._model = mj.MjModel.from_xml_path(self._profile.mjcf_path)
                self._data = mj.MjData(self._model)
                self._model.opt.timestep = self._timestep
                MujocoModelCache.put(cache_key, self._model)
                return
            except Exception as e:
                print(f"[MujocoEngine] WARN: MJCF load failed ({e}), falling back to minimal world")

        # Build minimal world from scratch
        xml = self._build_minimal_xml()
        self._model = mj.MjModel.from_xml_string(xml)
        self._data = mj.MjData(self._model)
        self._model.opt.timestep = self._timestep
        MujocoModelCache.put(cache_key, self._model)

    def _build_cache_key(self) -> str:
        """Build a unique cache key for this model configuration."""
        parts = [self._world_id, str(self._timestep)]
        if self._profile and self._profile.mjcf_path:
            parts.append(str(self._profile.mjcf_path))
        return "|".join(parts)

    def _build_minimal_xml(self) -> str:
        """Generate a minimal MJCF world XML from WorldSpec or fallback."""
        from rosclaw.sandbox.worlds.builder import load_world_spec

        try:
            world_spec = load_world_spec(self._world_id)
            objects_xml = self._world_spec_to_xml(world_spec)
            gravity = " ".join(str(g) for g in world_spec.gravity)
        except Exception as e:
            print(f"[MujocoEngine] WARN: WorldSpec load failed ({e}), using hardcoded defaults")
            objects_xml = self._hardcoded_world_xml()
            gravity = "0 0 -9.81"

        return f'''<mujoco model="sandbox_{self._world_id}">
  <option timestep="{self._timestep}" gravity="{gravity}"/>
  <worldbody>
    <light diffuse="0.8 0.8 0.8" pos="0 0 3" dir="0 0 -1"/>
    <geom name="floor" type="plane" size="5 5 0.1" rgba="0.5 0.5 0.5 1"/>
    {objects_xml}
  </worldbody>
</mujoco>'''

    def _world_spec_to_xml(self, world_spec) -> str:
        """Convert WorldSpec objects to MuJoCo XML geoms."""
        xml_parts = []
        for obj in world_spec.objects:
            size = " ".join(str(s) for s in obj.size)
            pos = " ".join(str(p) for p in obj.position)
            rgba = " ".join(str(c) for c in obj.rgba)
            xml_parts.append(
                f'<geom name="{obj.name}" type="{obj.geom_type}" '
                f'size="{size}" pos="{pos}" rgba="{rgba}" '
                f'contype="1" conaffinity="1"/>'
            )
        return "\n    ".join(xml_parts)

    def _hardcoded_world_xml(self) -> str:
        """Fallback hardcoded world objects."""
        if self._world_id == "tabletop":
            return '''
                <geom name="table" type="box" size="0.5 0.5 0.02" pos="0.5 0 0.4"
                      rgba="0.6 0.4 0.2 1" contype="1" conaffinity="1"/>
            '''
        elif self._world_id == "flat_ground":
            return '''
                <geom name="ground" type="plane" size="10 10 0.1" rgba="0.3 0.3 0.3 1"/>
            '''
        return ""

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        """Reset simulation to initial state."""
        mj = self._mujoco
        mj.mj_resetData(self._model, self._data)
        if seed is not None:
            np.random.seed(seed)
        mj.mj_forward(self._model, self._data)
        self._step_count = 0
        return self._get_observation()

    def step(self, action: dict[str, Any]) -> StepResult:
        """Execute one control step."""
        mj = self._mujoco

        action_type = action.get("type", "noop")
        if action_type == "joint_position" and "values" in action:
            values = np.array(action["values"])
            n = min(len(values), self._model.nu)
            self._data.ctrl[:n] = values[:n]
        elif action_type == "joint_velocity":
            pass  # velocity control placeholder
        elif action_type == "torque":
            if "values" in action:
                values = np.array(action["values"])
                n = min(len(values), self._model.nu)
                self._data.qfrc_applied[:n] = values[:n]

        # Step physics (multiple sub-steps for stability)
        n_substeps = max(1, int(0.02 / self._model.opt.timestep))
        for _ in range(n_substeps):
            mj.mj_step(self._model, self._data)

        self._step_count += 1

        obs = self._get_observation()
        reward = 0.0
        terminated = False
        truncated = False

        # Check for instability
        if np.any(np.isnan(self._data.qpos)) or np.any(np.isnan(self._data.qvel)):
            terminated = True

        info = {
            "step": self._step_count,
            "time": self._data.time,
            "contacts": self._get_contacts(),
        }

        return StepResult(
            observation=obs,
            reward=reward,
            terminated=terminated,
            truncated=truncated,
            info=info,
        )

    def render(self, mode: str = "rgb_array") -> Any:
        """Render the current scene."""
        if self._headless and mode != "rgb_array":
            return None

        mj = self._mujoco
        if self._renderer is None:
            try:
                self._renderer = mj.Renderer(self._model, height=480, width=640)
            except Exception:
                return None

        self._renderer.update_scene(self._data)
        return self._renderer.render()

    def get_state(self) -> dict[str, Any]:
        return {
            "qpos": self._data.qpos.copy().tolist(),
            "qvel": self._data.qvel.copy().tolist(),
            "time": float(self._data.time),
            "step": self._step_count,
        }

    def set_state(self, state: dict[str, Any]) -> None:
        if "qpos" in state:
            n = min(len(state["qpos"]), len(self._data.qpos))
            self._data.qpos[:n] = state["qpos"][:n]
        if "qvel" in state:
            n = min(len(state["qvel"]), len(self._data.qvel))
            self._data.qvel[:n] = state["qvel"][:n]
        self._mujoco.mj_forward(self._model, self._data)
        self._step_count = state.get("step", self._step_count)

    def close(self) -> None:
        if self._renderer:
            self._renderer.close()
            self._renderer = None
        self._model = None
        self._data = None

    # --- Internal helpers ---

    def _get_observation(self) -> dict[str, Any]:
        obs: dict[str, Any] = {}
        if self._data is not None:
            obs["joint_position"] = self._data.qpos.copy().tolist()
            obs["joint_velocity"] = self._data.qvel.copy().tolist()
            obs["time"] = float(self._data.time)
        return obs

    def _get_contacts(self) -> list[dict[str, Any]]:
        """Get active contact information."""
        contacts = []
        if self._data is None:
            return contacts
        mj = self._mujoco
        for i in range(self._data.ncon):
            c = self._data.contact[i]
            g1 = mj.mj_id2name(self._model, 6, c.geom1) or f"geom{c.geom1}"
            g2 = mj.mj_id2name(self._model, 6, c.geom2) or f"geom{c.geom2}"
            contacts.append({
                "geom1": g1,
                "geom2": g2,
                "dist": float(c.dist),
            })
        return contacts

    def get_joint_state(self) -> dict[str, Any]:
        return {
            "positions": self._data.qpos.copy().tolist() if self._data else [],
            "velocities": self._data.qvel.copy().tolist() if self._data else [],
            "names": [
                self._mujoco.mj_id2name(self._model, self._mujoco.mjtObj.mjOBJ_JOINT, i)
                for i in range(self._model.njnt)
            ] if self._model else [],
        }

    def get_contact_state(self) -> list[dict]:
        return self._get_contacts()

    @property
    def nq(self) -> int:
        return self._model.nq if self._model else 0

    @property
    def nv(self) -> int:
        return self._model.nv if self._model else 0

    @property
    def nu(self) -> int:
        return self._model.nu if self._model else 0
