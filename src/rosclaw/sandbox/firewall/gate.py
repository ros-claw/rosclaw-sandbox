"""
FirewallGate — pre-execution safety check for robot actions.

Loads the robot into MuJoCo, simulates the proposed action forward
in time, checks for collisions/joint-limit/workspace violations,
and returns a FirewallDecision.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import numpy as np

from rosclaw.sandbox.core.errors import FirewallBlockedError
from rosclaw.sandbox.core.types import FirewallDecision, RobotEmbodimentProfile
from rosclaw.sandbox.events.publisher import NullPublisher
from rosclaw.sandbox.events.schemas import (
    FirewallActionAllowed,
    FirewallActionBlocked,
)


class FirewallGate:
    """Safety gate that simulates actions before execution and blocks dangerous ones."""

    def __init__(
        self,
        robot_id: str,
        world_id: str = "tabletop",
        engine: str = "mujoco",
        horizon_sec: float = 2.0,
        risk_threshold: float = 0.75,
        block_on_collision: bool = True,
        block_on_joint_limit: bool = True,
        publisher: Any = None,
    ):
        self._robot_id = robot_id
        self._world_id = world_id
        self._engine_name = engine
        self._horizon_sec = horizon_sec
        self._risk_threshold = risk_threshold
        self._block_on_collision = block_on_collision
        self._block_on_joint_limit = block_on_joint_limit
        self._profile: RobotEmbodimentProfile | None = None
        self._engine: Any = None
        self._publisher = publisher or NullPublisher()
        self._setup()

    def _setup(self) -> None:
        from rosclaw.sandbox.eurdf.loader import load_robot_profile
        self._profile = load_robot_profile(self._robot_id)

        from rosclaw.sandbox.engines.mujoco.engine import MujocoEngine
        self._engine = MujocoEngine(
            robot_profile=self._profile,
            world_id=self._world_id,
            headless=True,
        )

    def check(self, action_request: dict[str, Any]) -> FirewallDecision:
        """Run a firewall check on the given action request."""
        violations: list[str] = []
        predicted_collision = False
        risk_score = 0.0

        # Reset engine
        self._engine.reset()

        # Pre-check: validate requested action values against joint limits
        if self._profile:
            limits = self._profile.get_joint_limits()
            target_values = action_request.get("values", action_request.get("target_pose", []))
            for i, (jname, (lo, hi)) in enumerate(limits.items()):
                if i < len(target_values):
                    val = target_values[i]
                    if val < lo or val > hi:
                        violations.append(
                            f"joint_limit: {jname} target={val:.3f} outside [{lo:.3f}, {hi:.3f}]"
                        )

        # Determine action trajectory
        horizon_steps = int(self._horizon_sec / 0.02)
        action_type = action_request.get("action_type", action_request.get("type", "joint_position"))

        # Simulate forward
        for step in range(horizon_steps):
            sim_action = self._build_sim_action(action_request, step, horizon_steps)
            result = self._engine.step(sim_action)

            # Check collisions
            contacts = result.info.get("contacts", [])
            for c in contacts:
                if c.get("dist", 1.0) < 0.001:
                    predicted_collision = True
                    violations.append(
                        f"collision: {c['geom1']} <-> {c['geom2']} at step {step}"
                    )
                    if self._block_on_collision:
                        break

            # Check joint limits
            if self._profile and self._block_on_joint_limit:
                obs = result.observation
                qpos = obs.get("joint_position", [])
                limits = self._profile.get_joint_limits()
                for i, (jname, (lo, hi)) in enumerate(limits.items()):
                    if i < len(qpos):
                        if qpos[i] < lo or qpos[i] > hi:
                            violations.append(f"joint_limit: {jname}={qpos[i]:.3f} outside [{lo:.3f}, {hi:.3f}]")

            if predicted_collision and self._block_on_collision:
                break

        # Calculate risk score
        if predicted_collision:
            risk_score = max(risk_score, 0.9)
        if violations:
            risk_score = max(risk_score, min(1.0, 0.3 + 0.1 * len(violations)))

        # Generate replay_id for ALL decisions (both ALLOW and BLOCK)
        # This ensures full auditability — every firewall check is traceable.
        replay_id = f"firewall_ep_{uuid.uuid4().hex[:8]}"

        # Make decision
        if risk_score >= self._risk_threshold or predicted_collision:
            decision = FirewallDecision(
                decision="BLOCK",
                risk_score=risk_score,
                reason=violations[0] if violations else "High risk score",
                predicted_collision=predicted_collision,
                violated_constraints=list(set(v.split(":")[0] for v in violations)),
                simulated_horizon_sec=self._horizon_sec,
                replay_id=replay_id,
            )
            self._publisher.publish(FirewallActionBlocked(
                robot_id=self._robot_id,
                risk_score=decision.risk_score,
                reason=decision.reason,
                replay_id=replay_id,
                payload={"violations": violations, "horizon_sec": self._horizon_sec},
            ))
        else:
            decision = FirewallDecision(
                decision="ALLOW",
                risk_score=risk_score,
                reason="Action passed all safety checks",
                predicted_collision=False,
                violated_constraints=[],
                simulated_horizon_sec=self._horizon_sec,
                replay_id=replay_id,
            )
            self._publisher.publish(FirewallActionAllowed(
                robot_id=self._robot_id,
                risk_score=decision.risk_score,
                replay_id=replay_id,
                payload={"horizon_sec": self._horizon_sec},
            ))

        return decision

    def _build_sim_action(self, request: dict, step: int, total: int) -> dict:
        """Build a simulation action from the request for a given step."""
        action_type = request.get("action_type", request.get("type", "joint_position"))

        if "target_pose" in request or "values" in request:
            values = request.get("values", request.get("target_pose", []))
            return {"type": "joint_position", "values": values}

        return {"type": "noop"}

    def close(self) -> None:
        """Close the firewall gate and release engine resources."""
        if self._engine:
            self._engine.close()
            self._engine = None

    def __enter__(self) -> "FirewallGate":
        """Support context manager protocol."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Ensure cleanup on context exit."""
        self.close()
