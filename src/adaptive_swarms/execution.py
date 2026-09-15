"""Actual infrastructure failures must bypass native candidate-failure handlers."""

INFRASTRUCTURE_EXIT_CODE = 74


class InfrastructureError(BaseException):
    """Execution failed without a scientific judgment; retain evidence for resume."""
