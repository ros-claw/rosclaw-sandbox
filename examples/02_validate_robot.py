#!/usr/bin/env python3
"""Example 02: Validate a robot model."""

from rosclaw.sandbox.eurdf.loader import load_robot_profile
from rosclaw.sandbox.validator.model_validator import ModelValidator

# Load and validate
profile = load_robot_profile("universal_robots_ur5e")
validator = ModelValidator(profile)
result = validator.validate()

print(f"Validation Status: {result.status}")
print(f"\nChecks:")
for check in result.checks:
    print(f"  [{check.status}] {check.message}")

# Save report
result.save_markdown("reports/ur5e_validation.md")
print(f"\nReport saved to reports/ur5e_validation.md")
