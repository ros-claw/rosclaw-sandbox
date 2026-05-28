"""
ROSClaw Sandbox — embodied physics simulation, validation, replay, and safety-gating.

ROSClaw Sandbox turns e-URDF robot embodiments into executable physical worlds,
allowing agents, skills, providers, and policies to be tested before entering
the real world.

Its first backend is MuJoCo, with future support for Isaac Sim, Gazebo,
and real-robot shadow execution.

ROSClaw Firewall is implemented as a safety mode inside ROSClaw Sandbox.
"""

__version__ = "0.1.0"

from rosclaw.sandbox.core.types import (
    FirewallDecision,
    RobotEmbodimentProfile,
    StepResult,
)
from rosclaw.sandbox.core.session import SandboxSession
from rosclaw.sandbox.core.env import SandboxEnv
from rosclaw.sandbox.sandbox_api import Sandbox

__all__ = [
    "__version__",
    "FirewallDecision",
    "RobotEmbodimentProfile",
    "Sandbox",
    "SandboxEnv",
    "SandboxSession",
    "StepResult",
]
