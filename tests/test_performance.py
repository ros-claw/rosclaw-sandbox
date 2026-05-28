"""Tests for performance optimizations."""

from rosclaw.sandbox.engines.mujoco.cache import MujocoModelCache
from rosclaw.sandbox.batch_runner import BatchRunner
from rosclaw.sandbox import Sandbox


class TestModelCache:
    def test_cache_put_and_get(self):
        MujocoModelCache.clear()
        assert MujocoModelCache.size() == 0

        # Simulate cached model
        MujocoModelCache.put("test_key", "mock_model")
        assert MujocoModelCache.size() == 1
        assert MujocoModelCache.get("test_key") == "mock_model"

    def test_cache_miss_returns_none(self):
        MujocoModelCache.clear()
        assert MujocoModelCache.get("nonexistent") is None

    def test_cache_lru_eviction(self):
        MujocoModelCache.clear()
        for i in range(10):
            MujocoModelCache.put(f"key_{i}", f"model_{i}")
        # Max size is 8, so oldest should be evicted
        assert MujocoModelCache.size() == 8
        assert MujocoModelCache.get("key_0") is None
        assert MujocoModelCache.get("key_9") == "model_9"

    def test_engine_uses_cache(self):
        """Verify that creating multiple sandboxes with same robot reuses cache."""
        MujocoModelCache.clear()
        assert MujocoModelCache.size() == 0

        # Create first sandbox (loads model)
        s1 = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        s1.reset()
        cache_after_first = MujocoModelCache.size()
        s1.close()

        # Create second sandbox with same robot (should use cache)
        s2 = Sandbox.create(robot_id="universal_robots_ur5e", world_id="empty")
        s2.reset()
        cache_after_second = MujocoModelCache.size()
        s2.close()

        assert cache_after_first == cache_after_second  # No new model loaded


class TestBatchRunner:
    def test_run_single_episode(self):
        runner = BatchRunner(robot_id="universal_robots_ur5e", world_id="empty")
        configs = [{"steps": 10, "action": {"type": "noop"}}]
        results = runner.run_episodes(configs)
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["total_steps"] == 10

    def test_run_multiple_episodes(self):
        runner = BatchRunner(robot_id="universal_robots_ur5e", world_id="empty")
        configs = [
            {"steps": 5, "action": {"type": "noop"}},
            {"steps": 10, "action": {"type": "noop"}},
            {"steps": 15, "action": {"type": "noop"}},
        ]
        results = runner.run_episodes(configs)
        assert len(results) == 3
        assert results[0]["total_steps"] == 5
        assert results[1]["total_steps"] == 10
        assert results[2]["total_steps"] == 15

    def test_benchmark(self):
        runner = BatchRunner(robot_id="universal_robots_ur5e", world_id="empty")
        configs = [{"steps": 5, "action": {"type": "noop"}} for _ in range(3)]
        bench = runner.benchmark(configs)
        assert bench["episodes"] == 3
        assert bench["errors"] == 0
        assert bench["total_steps"] == 15
        assert bench["steps_per_sec"] > 0
