"""
TaskRuntime — loads a task spec, creates a sandbox, runs episodes.

Supports:
- Simple tasks (reach_pose, joint_position)
- Multi-stage tasks (pick_and_place, navigate_to, sort_sequence)
- Stage-based action generation and success checking
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import yaml

from rosclaw.sandbox.core.errors import TaskError
from rosclaw.sandbox.core.types import TaskSpec
from rosclaw.sandbox.events.publisher import NullPublisher
from rosclaw.sandbox.events.schemas import (
    SandboxTaskStarted,
    SandboxTaskSucceeded,
    SandboxTaskFailed,
)


def _find_config_dir() -> Path:
    """Find the configs directory."""
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "configs",
        Path("./configs"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    raise TaskError("configs/ directory not found")


def load_task_spec(task_id: str) -> TaskSpec:
    """Load a TaskSpec from YAML config."""
    config_dir = _find_config_dir()
    task_path = config_dir / "tasks" / f"{task_id}.yaml"
    if not task_path.exists():
        raise TaskError(f"Task config not found: {task_path}")
    with open(task_path) as f:
        data = yaml.safe_load(f)
    return TaskSpec.from_dict(data)


class TaskRuntime:
    """Runs a single task episode in the sandbox.

    Supports both simple tasks and multi-stage tasks.
    For multi-stage tasks, each stage is checked sequentially.
    """

    def __init__(
        self,
        task_id: str,
        engine: str = "mujoco",
        headless: bool = True,
        record: bool = False,
        publisher: Any = None,
    ):
        self._task_spec = load_task_spec(task_id)
        self._engine_name = engine
        self._headless = headless
        self._record = record
        self._publisher = publisher or NullPublisher()
        self._current_stage = 0
        self._stage_start_time = 0.0

    def run_episode(self) -> dict[str, Any]:
        """Run one full episode and return summary."""
        from rosclaw.sandbox.sandbox_api import Sandbox

        spec = self._task_spec
        sandbox = Sandbox.create(
            robot_id=spec.robot_id,
            world_id=spec.world_id,
            engine=self._engine_name,
            task_id=spec.task_id,
            publisher=self._publisher,
        )

        self._publisher.publish(SandboxTaskStarted(
            robot_id=spec.robot_id,
            task_id=spec.task_id,
            payload={
                "world_id": spec.world_id,
                "max_steps": spec.max_steps,
                "goal_type": spec.goal_type,
                "stages": len(spec.goal_params.get("stages", [])),
            },
        ))

        obs = sandbox.reset()

        recorder = None
        if self._record:
            from rosclaw.sandbox.traces.recorder import EpisodeRecorder
            recorder = EpisodeRecorder(sandbox.session, output_dir=Path("./runs"))
            recorder.start()

        total_reward = 0.0
        success = False
        step_i = 0
        self._current_stage = 0
        self._stage_start_time = time.time()

        for step_i in range(spec.max_steps):
            action = self._generate_action(spec, obs, step_i)
            result = sandbox.step(action)
            total_reward += result.reward

            if recorder:
                recorder.record_step(action, result)

            if self._check_success(spec, result):
                success = True
                break

            if result.terminated:
                break

            obs = result.observation

        sandbox.close()

        summary = {
            "task_id": spec.task_id,
            "robot_id": spec.robot_id,
            "world_id": spec.world_id,
            "success": success,
            "total_steps": step_i + 1,
            "total_reward": total_reward,
            "terminated": result.terminated if step_i > 0 else False,
            "current_stage": self._current_stage,
        }

        if success:
            self._publisher.publish(SandboxTaskSucceeded(
                robot_id=spec.robot_id,
                task_id=spec.task_id,
                total_steps=summary["total_steps"],
                total_reward=summary["total_reward"],
                payload=summary,
            ))
        else:
            self._publisher.publish(SandboxTaskFailed(
                robot_id=spec.robot_id,
                task_id=spec.task_id,
                failure_type="timeout" if not result.terminated else "terminated",
                reason="Max steps reached without success" if not result.terminated else "Simulation terminated",
                payload=summary,
            ))

        if recorder:
            ep_dir = recorder.finish(summary)
            summary["episode_dir"] = str(ep_dir)

        return summary

    def _generate_action(self, spec: TaskSpec, obs: dict, step: int) -> dict:
        """Generate action based on current task type and stage."""
        if not spec.goal_params:
            return {"type": "noop"}

        goal_type = spec.goal_params.get("type", "")
        stages = spec.goal_params.get("stages", [])

        if stages and self._current_stage < len(stages):
            stage = stages[self._current_stage]
            return self._generate_stage_action(stage, obs)

        return {"type": "noop"}

    def _generate_stage_action(self, stage: dict, obs: dict) -> dict:
        """Generate action for a specific stage."""
        stage_type = stage.get("type", "")

        if stage_type == "reach_pose":
            target = stage.get("target_pose", [0, 0, 0, 0, 0, 0])
            return {"type": "target_pose", "values": target[:6]}

        elif stage_type == "gripper_action":
            target = stage.get("target_state", 0.0)
            return {"type": "gripper", "value": target}

        elif stage_type == "walk":
            direction = stage.get("direction", [1, 0, 0])
            return {"type": "walk", "direction": direction}

        elif stage_type == "stand":
            return {"type": "stand"}

        return {"type": "noop"}

    def _check_success(self, spec: TaskSpec, result: Any) -> bool:
        """Check if the task or current stage is achieved."""
        if not spec.goal_params:
            return False

        goal_type = spec.goal_params.get("type", "")
        obs = result.observation
        stages = spec.goal_params.get("stages", [])

        if stages:
            if self._current_stage >= len(stages):
                return True

            stage = stages[self._current_stage]
            if self._check_stage_success(stage, obs):
                self._current_stage += 1
                self._stage_start_time = time.time()
                if self._current_stage >= len(stages):
                    return True
            return False

        return self._check_goal_success(goal_type, spec.goal_params, obs)

    def _check_stage_success(self, stage: dict, obs: dict) -> bool:
        """Check if a specific stage is completed."""
        stage_type = stage.get("type", "")

        if stage_type == "reach_pose":
            target = stage.get("target_pose", [])
            if not target:
                return False
            ee_pose = obs.get("end_effector_pose")
            if not ee_pose:
                return False
            import numpy as np
            distance = np.linalg.norm(np.array(target[:3]) - np.array(ee_pose[:3]))
            return bool(distance < stage.get("success_distance", 0.05))

        elif stage_type == "gripper_action":
            hold_steps = stage.get("hold_steps", 5)
            elapsed = time.time() - self._stage_start_time
            return elapsed > (hold_steps * 0.02)

        elif stage_type == "stand":
            target_height = stage.get("target_height", 0.3)
            current_height = obs.get("base_position", [0, 0, 0])[2]
            return bool(abs(current_height - target_height) < stage.get("success_threshold", 0.05))

        elif stage_type == "walk":
            target_dist = stage.get("distance", 1.0)
            base_pos = obs.get("base_position", [0, 0, 0])
            import numpy as np
            distance = np.linalg.norm(np.array(base_pos[:2]))
            return bool(distance >= target_dist)

        return False

    def _check_goal_success(self, goal_type: str, goal_params: dict, obs: dict) -> bool:
        """Check simple single-goal task success."""
        if goal_type == "reach_pose":
            target_pose = goal_params.get("target_pose")
            if not target_pose:
                return False
            ee_pose = obs.get("end_effector_pose")
            if not ee_pose:
                return False
            import numpy as np
            target_pos = np.array(target_pose[:3])
            ee_pos = np.array(ee_pose[:3])
            distance = np.linalg.norm(target_pos - ee_pos)
            success_distance = goal_params.get("success_distance", 0.05)
            return bool(distance < success_distance)

        elif goal_type == "joint_position":
            target_joints = goal_params.get("target_joints")
            if not target_joints:
                return False
            current_joints = obs.get("joint_positions")
            if not current_joints:
                return False
            import numpy as np
            error = np.linalg.norm(np.array(current_joints) - np.array(target_joints))
            success_threshold = goal_params.get("success_threshold", 0.1)
            return bool(error < success_threshold)

        elif goal_type == "pick_and_place":
            place_pose = goal_params.get("place_pose")
            if not place_pose:
                return False
            ee_pose = obs.get("end_effector_pose")
            if not ee_pose:
                return False
            import numpy as np
            distance = np.linalg.norm(np.array(place_pose[:3]) - np.array(ee_pose[:3]))
            return bool(distance < goal_params.get("success_distance", 0.05))

        elif goal_type == "navigate_to":
            target_pos = goal_params.get("target_position")
            if not target_pos:
                return False
            base_pos = obs.get("base_position", [0, 0, 0])
            import numpy as np
            distance = np.linalg.norm(np.array(target_pos[:3]) - np.array(base_pos[:3]))
            return bool(distance < goal_params.get("tolerance", 0.2))

        return False
