"""Tests for multi-stage task support."""

from rosclaw.sandbox.tasks.runtime import TaskRuntime
from rosclaw.sandbox.core.types import TaskSpec, StepResult


class TestMultiStageTasks:
    def test_stage_advancement(self):
        runtime = TaskRuntime.__new__(TaskRuntime)
        runtime._current_stage = 0
        runtime._stage_start_time = 0

        spec = TaskSpec(
            task_id="test",
            goal_params={
                "type": "pick_and_place",
                "stages": [
                    {"type": "reach_pose", "target_pose": [1.0, 0.0, 0.0, 0, 0, 0], "success_distance": 0.1},
                    {"type": "gripper_action", "target_state": 1.0, "hold_steps": 1},
                    {"type": "reach_pose", "target_pose": [2.0, 0.0, 0.0, 0, 0, 0], "success_distance": 0.1},
                ],
            },
        )

        # Stage 0: not at target yet
        result = StepResult(observation={"end_effector_pose": [0.0, 0.0, 0.0, 0, 0, 0]})
        assert runtime._check_success(spec, result) is False
        assert runtime._current_stage == 0

        # Stage 0: reached target
        result = StepResult(observation={"end_effector_pose": [1.0, 0.0, 0.0, 0, 0, 0]})
        assert runtime._check_success(spec, result) is False  # advances stage, not done
        assert runtime._current_stage == 1

        # Stage 1: gripper (time-based, will pass after hold)
        import time
        runtime._stage_start_time = time.time() - 1.0
        result = StepResult(observation={"end_effector_pose": [1.0, 0.0, 0.0, 0, 0, 0]})
        assert runtime._check_success(spec, result) is False  # advances to stage 2
        assert runtime._current_stage == 2

        # Stage 2: reached final target
        result = StepResult(observation={"end_effector_pose": [2.0, 0.0, 0.0, 0, 0, 0]})
        assert runtime._check_success(spec, result) is True  # all stages done
        assert runtime._current_stage == 3

    def test_stage_action_generation(self):
        runtime = TaskRuntime.__new__(TaskRuntime)
        runtime._current_stage = 0

        stage = {"type": "reach_pose", "target_pose": [0.5, 0.2, 0.3, 0, 0, 0]}
        action = runtime._generate_stage_action(stage, {})
        assert action["type"] == "target_pose"
        assert action["values"] == [0.5, 0.2, 0.3, 0, 0, 0]

        stage = {"type": "gripper_action", "target_state": 1.0}
        action = runtime._generate_stage_action(stage, {})
        assert action["type"] == "gripper"
        assert action["value"] == 1.0

        stage = {"type": "walk", "direction": [1.0, 0.0, 0.0]}
        action = runtime._generate_stage_action(stage, {})
        assert action["type"] == "walk"

    def test_navigate_to_goal(self):
        runtime = TaskRuntime.__new__(TaskRuntime)

        goal_params = {
            "type": "navigate_to",
            "target_position": [1.0, 0.0, 0.3],
            "tolerance": 0.2,
        }
        obs = {"base_position": [0.9, 0.0, 0.3]}
        assert runtime._check_goal_success("navigate_to", goal_params, obs) is True

        obs = {"base_position": [0.5, 0.0, 0.3]}
        assert runtime._check_goal_success("navigate_to", goal_params, obs) is False

    def test_pick_and_place_goal(self):
        runtime = TaskRuntime.__new__(TaskRuntime)

        goal_params = {
            "type": "pick_and_place",
            "place_pose": [0.5, 0.3, 0.15, 0, 0, 0],
            "success_distance": 0.05,
        }
        obs = {"end_effector_pose": [0.5, 0.3, 0.15, 0, 0, 0]}
        assert runtime._check_goal_success("pick_and_place", goal_params, obs) is True

        obs = {"end_effector_pose": [0.0, 0.0, 0.0, 0, 0, 0]}
        assert runtime._check_goal_success("pick_and_place", goal_params, obs) is False
