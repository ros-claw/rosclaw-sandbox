"""Engine registry — maps engine names to backend implementations."""

from __future__ import annotations

from typing import Any, Type

from rosclaw.sandbox.core.errors import EngineError

# Global engine registry: name -> engine class
_ENGINE_REGISTRY: dict[str, Type[Any]] = {}


def register_engine(name: str, engine_cls: Type[Any]) -> None:
    """Register a physics engine backend by name."""
    _ENGINE_REGISTRY[name] = engine_cls


def get_engine_class(name: str) -> Type[Any]:
    """Look up an engine class by name."""
    if name not in _ENGINE_REGISTRY:
        available = ", ".join(sorted(_ENGINE_REGISTRY.keys())) or "(none)"
        raise EngineError(f"Unknown engine '{name}'. Available: {available}")
    return _ENGINE_REGISTRY[name]


def list_engines() -> list[str]:
    """Return list of registered engine names."""
    return sorted(_ENGINE_REGISTRY.keys())


def create_engine(name: str, **kwargs: Any) -> Any:
    """Instantiate a registered engine by name."""
    cls = get_engine_class(name)
    return cls(**kwargs)
