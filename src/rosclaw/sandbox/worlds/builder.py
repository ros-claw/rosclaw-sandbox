"""WorldBuilder — constructs MuJoCo worlds from WorldSpec configs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from rosclaw.sandbox.core.types import WorldSpec, WorldObjectSpec


def _find_worlds_config() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "configs" / "worlds",
        Path("./configs/worlds"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError("configs/worlds/ not found")


def load_world_spec(world_id: str) -> WorldSpec:
    """Load a WorldSpec from YAML config."""
    worlds_dir = _find_worlds_config()
    path = worlds_dir / f"{world_id}.yaml"
    if not path.exists():
        # Return a default spec
        return WorldSpec(world_id=world_id, name=world_id)
    with open(path) as f:
        data = yaml.safe_load(f)
    return WorldSpec.from_dict(data)


def list_worlds() -> list[str]:
    """List available world configs."""
    try:
        worlds_dir = _find_worlds_config()
        return sorted(p.stem for p in worlds_dir.glob("*.yaml"))
    except FileNotFoundError:
        return ["empty", "flat_ground", "tabletop"]
