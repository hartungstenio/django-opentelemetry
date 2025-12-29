"""Model metrics."""

from collections.abc import Mapping
from typing import Any

from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from opentelemetry import metrics

from . import features

meter: metrics.Meter = metrics.get_meter(__name__)

model_inserts: metrics.Counter = meter.create_counter(
    "django_model_inserts",
    description="Number of insert operations by model.",
)
model_updates: metrics.Counter = meter.create_counter(
    "django_model_updates",
    description="Number of update operations by model.",
)
model_deletes: metrics.Counter = meter.create_counter(
    "django_model_deletes",
    description="Number of delete operations by model.",
)


@receiver(post_save)
def on_model_insert_or_update(
    *,
    sender: type[models.Model],
    created: bool,
    **_kwargs: Mapping[str, Any],
) -> None:
    """Increment the either the insert or update metric for a given model."""
    if metric_label := getattr(sender._meta, "metric_label", None) or features.extra_models().get(sender._meta.label):
        metric: metrics.Counter = model_inserts if created else model_updates
        metric.add(1, {"model": metric_label})


@receiver(post_delete)
def on_model_delete(
    *,
    sender: type[models.Model],
    **_kwargs: Mapping[str, Any],
) -> None:
    """Increment the delete metric for a given model."""
    if metric_label := getattr(sender._meta, "metric_label", None) or features.extra_models().get(sender._meta.label):
        model_deletes.add(1, {"model": metric_label})
