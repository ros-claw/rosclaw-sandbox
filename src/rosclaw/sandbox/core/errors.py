"""Custom exception hierarchy for rosclaw-sandbox."""


class SandboxError(Exception):
    """Base exception for all sandbox errors."""


class EngineError(SandboxError):
    """Error in the physics simulation engine."""


class ProfileError(SandboxError):
    """Error loading or parsing a robot profile."""


class ValidationError(SandboxError):
    """Error during model or safety validation."""


class FirewallBlockedError(SandboxError):
    """Raised when the firewall blocks an action.

    Attributes:
        decision: The FirewallDecision that caused the block.
    """

    def __init__(self, message: str, decision=None):
        super().__init__(message)
        self.decision = decision


class WorldError(SandboxError):
    """Error building or loading a world."""


class TaskError(SandboxError):
    """Error in task runtime."""


class TraceError(SandboxError):
    """Error in trace recording or replay."""
