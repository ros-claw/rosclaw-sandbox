"""EventPublisher interface — pluggable event publishing backends."""

from __future__ import annotations

from typing import Any, Protocol

from rosclaw.sandbox.events.schemas import SandboxEvent


class EventPublisher(Protocol):
    """Interface for publishing sandbox events."""

    def publish(self, event: SandboxEvent) -> None: ...


class NullPublisher:
    """Discards all events. Used when running standalone."""

    def publish(self, event: SandboxEvent) -> None:
        pass


class PrintPublisher:
    """Prints events to stdout. Useful for debugging."""

    def publish(self, event: SandboxEvent) -> None:
        print(f"[Event] {event.event_type}: session={event.session_id} robot={event.robot_id}")


class ListPublisher:
    """Collects events in a list. Useful for testing."""

    def __init__(self) -> None:
        self.events: list[SandboxEvent] = []

    def publish(self, event: SandboxEvent) -> None:
        self.events.append(event)


class RuntimePublisher:
    """Publishes to ROSClaw v1.0 EventBus (adapter)."""

    def __init__(self, event_bus: Any = None):
        self._bus = event_bus

    def publish(self, event: SandboxEvent) -> None:
        if self._bus is None:
            return
        try:
            from rosclaw.core.event_bus import Event, EventPriority
            self._bus.publish(Event(
                topic=f"sandbox.{event.event_type}",
                payload=event.to_dict(),
                source="rosclaw-sandbox",
            ))
        except ImportError:
            pass
