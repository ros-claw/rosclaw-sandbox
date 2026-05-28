"""MuJoCo physics engine backend — auto-registers on import."""

from rosclaw.sandbox.core.registry import register_engine
from rosclaw.sandbox.engines.mujoco.engine import MujocoEngine

register_engine("mujoco", MujocoEngine)

__all__ = ["MujocoEngine"]
