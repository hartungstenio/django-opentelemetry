import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics.export import MetricsData

from .models import SimpleModel
from .utils import create_meter_provider

pytestmark = pytest.mark.django_db


def test_model_creation() -> None:
    meter_provider, memory_metrics_reader = create_meter_provider()
    metrics.set_meter_provider(meter_provider)

    SimpleModel.objects.create(name="Bob")

    metric_data: MetricsData | None = memory_metrics_reader.get_metrics_data()

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

                if metric.name in ["django_model_updates", "django_model_deletes"]:
                    pytest.fail(f"Should not get {metric.name} metric")

    pytest.fail("Metric not found")


def test_model_update() -> None:
    instance = SimpleModel.objects.create(name="Bob")

    meter_provider, memory_metrics_reader = create_meter_provider()
    metrics.set_meter_provider(meter_provider)

    instance.name = "Mark"
    instance.save()

    metric_data: MetricsData | None = memory_metrics_reader.get_metrics_data()

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

                if metric.name in ["django_model_inserts", "django_model_deletes"]:
                    pytest.fail(f"Should not get {metric.name} metric")

    pytest.fail("Metric not found")


def test_model_delete() -> None:
    instance = SimpleModel.objects.create(name="Bob")

    meter_provider, memory_metrics_reader = create_meter_provider()
    metrics.set_meter_provider(meter_provider)

    instance.delete()

    metric_data: MetricsData | None = memory_metrics_reader.get_metrics_data()

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

                if metric.name in ["django_model_inserts", "django_model_updates"]:
                    pytest.fail(f"Should not get {metric.name} metric")

    pytest.fail("Metric not found")
