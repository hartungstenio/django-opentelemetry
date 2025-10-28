import pytest
from opentelemetry.sdk.metrics.export import InMemoryMetricReader, MetricsData

from .models import SimpleModel

pytestmark = pytest.mark.django_db


def test_model_creation(metric_reader: InMemoryMetricReader) -> None:
    SimpleModel.objects.create(name="Bob")
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert isinstance(metric_data, MetricsData)
    assert len(metric_data.resource_metrics) > 0

    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == "django_model_inserts":
                    data_points = list(metric.data.data_points)
                    assert len(data_points) == 1
                    assert data_points[0].attributes["model"] == "simple_model"  # type: ignore[attr-defined]
                    return

                if metric.name.startswith("django_model"):
                    pytest.fail(f"Unexpected metric {metric.name}")

    pytest.fail("Metric not found")


def test_model_update(metric_reader: InMemoryMetricReader) -> None:
    instance = SimpleModel.objects.create(name="Bob")

    instance.name = "Mark"
    instance.save()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert len(metric_data.resource_metrics) > 0

    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == "django_model_updates":
                    data_points = list(metric.data.data_points)
                    assert len(data_points) == 1
                    assert data_points[0].attributes["model"] == "simple_model"  # type: ignore[attr-defined]
                    return

    pytest.fail("Metric not found")


def test_model_delete(metric_reader: InMemoryMetricReader) -> None:
    instance = SimpleModel.objects.create(name="Bob")

    instance.delete()
    metric_data: MetricsData | None = metric_reader.get_metrics_data()

    assert metric_data is not None
    assert len(metric_data.resource_metrics) > 0

    for resource_metric in metric_data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == "django_model_deletes":
                    data_points = list(metric.data.data_points)
                    assert len(data_points) == 1
                    assert data_points[0].attributes["model"] == "simple_model"  # type: ignore[attr-defined]
                    return

    pytest.fail("Metric not found")
