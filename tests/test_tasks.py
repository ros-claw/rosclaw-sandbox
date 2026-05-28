"""Tests for TaskRuntime."""

import pytest
from rosclaw.sandbox.tasks.runtime import TaskRuntime, load_task_spec
from rosclaw.sandbox.core.errors import TaskError


class TestLoadTaskSpec:
    def test_load_existing_task(self):
        spec = load_task_spec("ur5e_reach_target")
        assert spec.task_id == "ur5e_reach_target"
        assert spec.robot_id == "universal_robots_ur5e"
        assert spec.world_id == "tabletop"
        assert spec.goal_type == "reach_pose"

    def test_load_nonexistent_task(self):
        with pytest.raises(TaskError):
            load_task_spec("nonexistent_task_xyz")


class TestTaskRuntime:
    def test_create_task_runtime(self):
        runtime = TaskRuntime("ur5e_reach_target")
        assert runtime._task_spec.task_id == "ur5e_reach_target"

    def test_check_success_reach_pose(self):
        from rosclaw.sandbox.core.types import TaskSpec, StepResult
        import numpy as np

        runtime = TaskRuntime.__new__(TaskRuntime)
        spec = TaskSpec(
            task_id="test",
            goal_params={"type": "reach_pose", "target_pose": [1.0, 2.0, 3.0, 0.0, 0.0, 0.0], "success_distance": 0.1}
        )
        result = StepResult(observation={"end_effector_pose": [1.05, 2.0, 3.0, 0.0, 0.0, 0.0]})
        assert runtime._check_success(spec, result) is True

        result2 = StepResult(observation={"end_effector_pose": [2.0, 2.0, 3.0, 0.0, 0.0, 0.0]})
        assert runtime._check_success(spec, result2) is False

    def test_check_success_joint_position(self):
        from rosclaw.sandbox.core.types import TaskSpec, StepResult

        runtime = TaskRuntime.__new__(TaskRuntime)
        spec = TaskSpec(
            task_id="test",
            goal_params={"type": "joint_position", "target_joints": [0.0, 0.0, 0.0], "success_threshold": 0.1}
        )
        result = StepResult(observation={"joint_positions": [0.05, 0.0, 0.0]})
        assert runtime._check_success(spec, result) is True

        result2 = StepResult(observation={"joint_positions": [1.0, 0.0, 0.0]})
        assert runtime._check_success(spec, result2) is False
