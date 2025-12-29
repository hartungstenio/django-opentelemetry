"""Read by Django to configure :mod:`django_opentelemetry`."""

from django.apps import AppConfig
from django.db.models import options
from django.utils.translation import gettext_lazy as _

from . import features

if features.should_use_model_meta() and "metric_label" not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = (*options.DEFAULT_NAMES, "metric_label")


class OpenTelemetryConfig(AppConfig):
    """:mod:`django_opentelemetry` app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_opentelemetry"
    verbose_name = _("OpenTelemetry")

    def ready(self) -> None:
        """Register signals."""
        if features.should_collect_model_metrics():
            from . import model_signals  # noqa: F401, PLC0415

        if features.should_collect_task_metrics():
            from . import task_signals  # noqa: F401, PLC0415

        return super().ready()
