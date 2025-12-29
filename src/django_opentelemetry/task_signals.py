"""Task metrics."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, Protocol

import django
from django.dispatch import receiver
from opentelemetry import metrics

if TYPE_CHECKING:
    from opentelemetry.util.types import Attributes

if django.VERSION >= (6, 0):
    from django.tasks import signals as django_native_signals  # type: ignore[import-untyped]
else:
    django_native_signals = None

try:
    from django_tasks import signals as django_tasks_signals
except ImportError:
    django_tasks_signals = None  # type: ignore[assignment]


if django_native_signals or django_tasks_signals:
    meter: metrics.Meter = metrics.get_meter(__name__)

    tasks_enqueued: metrics.Counter = meter.create_counter(
        "django_tasks_enqueued",
        description="Number of enqueued tasks",
    )
    tasks_started: metrics.Counter = meter.create_counter(
        "django_tasks_started",
        description="Number of started tasks",
    )
    tasks_success: metrics.Counter = meter.create_counter(
        "django_tasks_success",
        description="Number of tasks finished with success",
    )
    tasks_failed: metrics.Counter = meter.create_counter(
        "django_tasks_failed",
        description="Number of tasks finished failing",
    )
    tasks_pending: metrics.UpDownCounter = meter.create_up_down_counter(
        "django_tasks_pending",
        description="Number of currently pending tasks",
    )
    tasks_running: metrics.UpDownCounter = meter.create_up_down_counter(
        "django_tasks_running",
        description="Number of currently running tasks",
    )

    class _Task(Protocol):
        queue_name: str

    class _TaskResult(Protocol):
        status: Literal["READY", "RUNNING", "FAILED", "SUCCEEDED"]
        task: _Task
        backend: str

    def on_task_enqueued(*, task_result: _TaskResult, **_kwargs: Mapping[str, Any]) -> None:
        """Increment the number of enqueued and pending tasks."""
        task_attributes: Attributes = {
            "backend": task_result.backend,
            "queue_name": task_result.task.queue_name,
        }
        tasks_enqueued.add(1, task_attributes)
        tasks_pending.add(1, task_attributes)

    def on_task_started(*, task_result: _TaskResult, **_kwargs: Mapping[str, Any]) -> None:
        """Increment the number of started and running tasks."""
        task_attributes: Attributes = {
            "backend": task_result.backend,
            "queue_name": task_result.task.queue_name,
        }
        tasks_started.add(1, task_attributes)
        tasks_pending.add(-1, task_attributes)
        tasks_running.add(1, task_attributes)

    def on_task_finished(*, task_result: _TaskResult, **_kwargs: Mapping[str, Any]) -> None:
        """Increment the number of enqueued and pending tasks."""
        task_attributes: Attributes = {
            "backend": task_result.backend,
            "queue_name": task_result.task.queue_name,
        }

        metric = tasks_failed if task_result.status == "FAILED" else tasks_success
        metric.add(1, task_attributes)
        tasks_running.add(-1, task_attributes)

    if django_native_signals:
        receiver(django_native_signals.task_enqueued)(on_task_enqueued)
        receiver(django_native_signals.task_started)(on_task_started)
        receiver(django_native_signals.task_finished)(on_task_finished)

    if django_tasks_signals:
        receiver(django_tasks_signals.task_enqueued)(on_task_enqueued)
        receiver(django_tasks_signals.task_started)(on_task_started)
        receiver(django_tasks_signals.task_finished)(on_task_finished)
