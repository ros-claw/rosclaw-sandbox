"""Tests for world building."""

from rosclaw.sandbox.worlds.builder import load_world_spec, list_worlds
from rosclaw.sandbox.core.types import WorldSpec


class TestWorldSpec:
    def test_load_empty_world(self):
        spec = load_world_spec("empty")
        assert spec.world_id == "empty"
        assert spec.gravity == [0.0, 0.0, -9.81]
        assert len(spec.objects) == 0

    def test_load_tabletop_world(self):
        spec = load_world_spec("tabletop")
        assert spec.world_id == "tabletop"
        assert len(spec.objects) >= 1
        table = next(o for o in spec.objects if o.name == "table")
        assert table.geom_type == "box"

    def test_list_worlds(self):
        worlds = list_worlds()
        assert "empty" in worlds
        assert "tabletop" in worlds

    def test_world_spec_from_dict(self):
        data = {
            "world_id": "test",
            "gravity": [0, 0, -10],
            "objects": [
                {"name": "box", "geom_type": "box", "size": [0.1, 0.1, 0.1]}
            ]
        }
        spec = WorldSpec.from_dict(data)
        assert spec.world_id == "test"
        assert len(spec.objects) == 1
