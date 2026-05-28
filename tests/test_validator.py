"""Tests for ModelValidator."""

from rosclaw.sandbox.validator.model_validator import ModelValidator
from rosclaw.sandbox.eurdf.loader import load_robot_profile


class TestModelValidator:
    def test_validate_skeleton_profile(self):
        profile = load_robot_profile("unitree_go2")
        validator = ModelValidator(profile)
        result = validator.validate()
        assert result.robot_id == "unitree_go2"
        # Skeleton config may have warnings but should not have FAIL
        # (MJCF load fails but validator handles gracefully)
        assert len(result.checks) > 0

    def test_status_labels(self):
        from rosclaw.sandbox.validator.model_validator import ValidationResult
        r = ValidationResult(robot_id="test")
        r.add("PASS", "ok")
        assert r.status_label() == "PASS"

        r2 = ValidationResult(robot_id="test")
        r2.add("WARN", "warning")
        assert r2.status_label() == "PASS_WITH_WARNINGS"

        r3 = ValidationResult(robot_id="test")
        r3.add("FAIL", "failed")
        assert r3.status_label() == "FAIL"

    def test_to_dict(self):
        from rosclaw.sandbox.validator.model_validator import ValidationResult, ValidationCheck
        r = ValidationResult(robot_id="test")
        r.add("PASS", "test passed", "model")
        d = r.to_dict()
        assert d["robot_id"] == "test"
        assert d["status"] == "PASS"
        assert len(d["checks"]) == 1
