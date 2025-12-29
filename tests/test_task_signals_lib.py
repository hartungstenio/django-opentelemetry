import pytest
from django_tasks import task
from opentelemetry.sdk.metrics.export import InMemoryMetricReader, MetricsData

pytestmark = pytest.mark.django_db


@task
def noop_task() -> None:
    pass


@task
def failing_task() -> None:
    raise RuntimeError


def test_task_creation_defaults(metric_reader: InMemoryMetricReader) -> None:
    expected = {"backend": "default", "queue_name": "default"}
    expected_metrics = ["django_tasks_enqueued", "django_tasks_pending"]
    noop_task.enqueue()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert isinstance(metric_data, MetricsData)
    assert len(metric_data.resource_metrics) > 0

    count = 0
    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name in expected_metrics:
                    data_points = list(metric.data.data_points)
                    assert len(data_points) > 0
                    assert any(dp.attributes.items() >= expected.items() for dp in data_points)  # type: ignore[attr-defined]
                    count += 1

    if count != len(expected_metrics):
        pytest.fail("Metric not found")


def test_task_creation_custom_params(metric_reader: InMemoryMetricReader) -> None:
    expected = {"backend": "secondary", "queue_name": "some_queue"}
    expected_metrics = ["django_tasks_enqueued", "django_tasks_pending"]
    noop_task.using(queue_name="some_queue", backend="secondary").enqueue()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert isinstance(metric_data, MetricsData)
    assert len(metric_data.resource_metrics) > 0

    count = 0
    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name in expected_metrics:
                    data_points = list(metric.data.data_points)
                    assert len(data_points) > 0
                    assert any(dp.attributes.items() >= expected.items() for dp in data_points)  # type: ignore[attr-defined]
                    count += 1

    if count != len(expected_metrics):
        pytest.fail("Metric not found")


def test_task_execution(metric_reader: InMemoryMetricReader) -> None:
    expected = {"backend": "immediate", "queue_name": "default"}
    expected_metrics = {
        "django_tasks_enqueued",
        "django_tasks_pending",
        "django_tasks_started",
        "django_tasks_running",
        "django_tasks_success",
    }
    noop_task.using(backend="immediate").enqueue()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert isinstance(metric_data, MetricsData)
    assert len(metric_data.resource_metrics) > 0

    count = 0
    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name in expected_metrics:
                    data_points = list(metric.data.data_points)
                    assert len(data_points) > 0
                    assert any(dp.attributes.items() >= expected.items() for dp in data_points)  # type: ignore[attr-defined]
                    count += 1

    if count != len(expected_metrics):
        pytest.fail("Metric not found")


def test_task_failure(metric_reader: InMemoryMetricReader) -> None:
    expected = {"backend": "immediate", "queue_name": "default"}
    expected_metrics = {
        "django_tasks_enqueued",
        "django_tasks_pending",
        "django_tasks_started",
        "django_tasks_running",
        "django_tasks_failed",
    }
    failing_task.using(backend="immediate").enqueue()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert isinstance(metric_data, MetricsData)
    assert len(metric_data.resource_metrics) > 0

    count = 0
    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name in expected_metrics:
                    data_points = list(metric.data.data_points)
                    assert len(data_points) > 0
                    assert any(dp.attributes.items() >= expected.items() for dp in data_points)  # type: ignore[attr-defined]
                    count += 1

    if count != len(expected_metrics):
        pytest.fail("Metric not found")
