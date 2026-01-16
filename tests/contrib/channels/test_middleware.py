from unittest import mock

import pytest
from asgiref.testing import ApplicationCommunicator
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics._internal.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from django_opentelemetry.contrib.channels.middleware import OpenTelemetryMiddleware

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)


@pytest.mark.asyncio
class TestOpenTelemetryMiddleware:
    async def test_middleware_http(self, span_exporter: InMemorySpanExporter) -> None:
        span_exporter.clear()
        app = mock.AsyncMock()
        middleware = OpenTelemetryMiddleware(app, tracer=tracer, meter=meter)
        scope = {"type": "http", "method": "GET", "path": "/test/"}
        communicator = ApplicationCommunicator(middleware, scope)

        await communicator.send_input({"type": "http.request", "body": b""})
        await communicator.wait()

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "GET /test/"
        assert span.attributes is not None
        assert span.attributes["http.method"] == "GET"
        assert span.attributes["http.target"] == "/test/"

    async def test_middleware_channel(
        self, metric_reader: InMemoryMetricReader, span_exporter: InMemorySpanExporter
    ) -> None:
        span_exporter.clear()
        app = mock.AsyncMock()
        middleware = OpenTelemetryMiddleware(app, tracer=tracer, meter=meter)
        scope = {"type": "channel", "channel": "my_channel"}
        communicator = ApplicationCommunicator(middleware, scope)

        await communicator.send_input({"data": "test"})
        await communicator.wait()

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "consume my_channel"
        assert span.attributes is not None
        assert span.attributes["messaging.operation.name"] == "consume"
        assert span.attributes["messaging.system"] == "django_channels"
        assert span.attributes["messaging.destination.name"] == "my_channel"
        assert span.attributes["messaging.destination.temporary"] is True
        assert span.attributes["messaging.operation.type"] == "process"

        metrics_list = metric_reader.get_metrics_data()
        consumed_messages_found = False
        process_duration_found = False
        assert len(metrics_list.resource_metrics) > 0
        for resource_metric in metrics_list.resource_metrics:
            assert len(resource_metric.scope_metrics) > 0

            for scope_metric in resource_metric.scope_metrics:
                for metric in scope_metric.metrics:
                    if metric.name == "messaging.client.consumed.messages":
                        consumed_messages_found = True
                        for data_point in metric.data.data_points:
                            assert data_point.value >= 1
                    if metric.name == "messaging.process.duration":
                        for data_point in metric.data.data_points:
                            process_duration_found = True
                            assert data_point.count >= 1

        assert consumed_messages_found, "Consumed messages metric not found"
        assert process_duration_found, "Process duration metric not found"
