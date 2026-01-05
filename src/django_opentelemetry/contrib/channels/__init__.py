"""Django Channels integration for OpenTelemetry."""

from .middleware import OpenTelemetryMiddleware

__all__ = [
    "OpenTelemetryMiddleware",
]
