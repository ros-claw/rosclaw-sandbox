"""Tests for engine registry."""

from rosclaw.sandbox.core.registry import register_engine, get_engine_class, list_engines
from rosclaw.sandbox.core.errors import EngineError
import pytest


class DummyEngine:
    pass


class TestRegistry:
    def test_register_and_get(self):
        register_engine("dummy", DummyEngine)
        assert get_engine_class("dummy") is DummyEngine

    def test_list_engines(self):
        register_engine("dummy2", DummyEngine)
        engines = list_engines()
        assert "dummy2" in engines

    def test_unknown_engine(self):
        with pytest.raises(EngineError):
            get_engine_class("nonexistent_engine_xyz")
