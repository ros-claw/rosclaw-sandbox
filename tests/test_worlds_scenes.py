"""Tests for rich world scenes."""

from rosclaw.sandbox.worlds.builder import load_world_spec, list_worlds
from rosclaw.sandbox import Sandbox


class TestWorldScenes:
    def test_office_world_loads(self):
        spec = load_world_spec("office")
        assert spec.world_id == "office"
        assert len(spec.objects) >= 10
        assert any(o.name == "desk1_top" for o in spec.objects)
        assert any(o.name == "monitor_screen" for o in spec.objects)

    def test_kitchen_world_loads(self):
        spec = load_world_spec("kitchen")
        assert spec.world_id == "kitchen"
        assert len(spec.objects) >= 8
        assert any(o.name == "fridge" for o in spec.objects)
        assert any(o.name == "stove_top" for o in spec.objects)

    def test_factory_world_loads(self):
        spec = load_world_spec("factory")
        assert spec.world_id == "factory"
        assert len(spec.objects) >= 7
        assert any(o.name == "conveyor_belt" for o in spec.objects)
        assert any(o.name == "barrier" for o in spec.objects)

    def test_warehouse_world_loads(self):
        spec = load_world_spec("warehouse")
        assert spec.world_id == "warehouse"
        assert len(spec.objects) >= 10
        assert any(o.name == "shelf1_base" for o in spec.objects)
        assert any(o.name == "pallet_box" for o in spec.objects)

    def test_all_worlds_simulate(self):
        """Verify all worlds can be loaded into MuJoCo engine."""
        for world_id in ["office", "kitchen", "factory", "warehouse"]:
            sandbox = Sandbox.create(
                robot_id="universal_robots_ur5e",
                world_id=world_id,
            )
            obs = sandbox.reset()
            result = sandbox.step({"type": "noop"})
            assert result is not None
            sandbox.close()

    def test_list_worlds_includes_new(self):
        worlds = list_worlds()
        assert "office" in worlds
        assert "kitchen" in worlds
        assert "factory" in worlds
        assert "warehouse" in worlds
