#!/usr/bin/env python3
"""Example 01: Load a robot profile from e-URDF-Zoo."""

from rosclaw.sandbox.eurdf.loader import load_robot_profile

# Load UR5e robot profile
profile = load_robot_profile("universal_robots_ur5e")

print(f"Robot: {profile.name}")
print(f"DOF: {profile.dof}")
print(f"Base type: {profile.base_type}")
print(f"Joints: {len(profile.joints)}")
print(f"Joint names: {profile.get_joint_names()}")
print(f"Joint limits: {profile.get_joint_limits()}")
