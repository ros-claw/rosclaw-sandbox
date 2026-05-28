"""Tests for core types."""

from rosclaw.sandbox.core.types import (
    FirewallDecision,
    JointProfile,
    RobotEmbodimentProfile,
    StepResult,
    TaskSpec,
    WorldSpec,
)


class TestStepResult:
    def test_defaults(self):
        r = StepResult(observation={"joints": [0.0]})
        assert r.reward == 0.0
        assert r.terminated is False
        assert r.truncated is False

    def test_custom(self):
        r = StepResult(observation={}, reward=1.5, terminated=True)
        assert r.reward == 1.5
        assert r.terminated is True


class TestFirewallDecision:
    def test_allow(self):
        d = FirewallDecision(decision="ALLOW", risk_score=0.1)
        assert d.is_allowed is True

    def test_block(self):
        d = FirewallDecision(decision="BLOCK", risk_score=0.9, reason="collision")
        assert d.is_allowed is False
        assert d.reason == "collision"

    def test_modify_and_allow(self):
        d = FirewallDecision(decision="MODIFY_AND_ALLOW", risk_score=0.5)
        assert d.is_allowed is True

    def test_to_dict(self):
        d = FirewallDecision(decision="BLOCK", risk_score=0.8)
        data = d.to_dict()
        assert data["decision"] == "BLOCK"
        assert data["risk_score"] == 0.8


class TestRobotEmbodimentProfile:
    def test_basic(self):
        p = RobotEmbodimentProfile(
            robot_id="test_bot",
            name="Test Bot",
            dof=6,
            joints=[
                JointProfile(name="j1", joint_type="revolute"),
                JointProfile(name="j2", joint_type="fixed"),
                JointProfile(name="j3", joint_type="revolute"),
            ],
        )
        assert p.dof == 6
        assert len(p.get_joint_names()) == 3
        assert len(p.get_actuated_joints()) == 2

    def test_joint_limits(self):
        p = RobotEmbodimentProfile(
            robot_id="test",
            joints=[
                JointProfile(name="j1", joint_type="revolute", lower_limit=-1.0, upper_limit=1.0),
            ],
        )
        limits = p.get_joint_limits()
        assert limits["j1"] == (-1.0, 1.0)

    def test_to_dict(self):
        p = RobotEmbodimentProfile(robot_id="bot1")
        d = p.to_dict()
        assert d["robot_id"] == "bot1"


class TestWorldSpec:
    def test_from_dict(self):
        data = {
            "world_id": "test_world",
            "name": "Test",
            "gravity": [0, 0, -10],
            "objects": [{"name": "box", "geom_type": "box"}],
        }
        w = WorldSpec.from_dict(data)
        assert w.world_id == "test_world"
        assert len(w.objects) == 1
        assert w.objects[0].name == "box"


class TestTaskSpec:
    def test_from_dict(self):
        data = {
            "task_id": "test_task",
            "robot_id": "ur5e",
            "world_id": "tabletop",
            "action": {"type": "joint_position", "hz": 20},
            "observation": ["joint_position"],
            "goal": {"type": "reach_pose"},
            "termination": {"max_steps": 100},
        }
        t = TaskSpec.from_dict(data)
        assert t.task_id == "test_task"
        assert t.action_type == "joint_position"
        assert t.max_steps == 100
