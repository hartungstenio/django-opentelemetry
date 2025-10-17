"""Read settings."""

from django.conf import settings


def should_use_model_meta() -> bool:
    """Return if model meta should be used to setup metrics.

    Defaults to True.
    """
    return getattr(settings, "OTEL_MODEL_META", True)


def should_collect_model_metrics() -> bool:
    """Return if model metrics should be collected.

    Defaults to True.
    """
    return getattr(settings, "OTEL_MODEL_METRICS", True)


def extra_models() -> dict[str, str]:
    """Return any configured extra models, with it's label."""
    return getattr(settings, "OTEL_EXTRA_MODELS", {})


def should_collect_task_metrics() -> bool:
    """Return if task metrics should be collected.

    Defaults to True.
    """
    return getattr(settings, "OTEL_TASK_METRICS", True)
