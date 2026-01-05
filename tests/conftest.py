from collections.abc import Generator
from typing import Any, cast

import pytest
from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.test.globals_test import reset_metrics_globals, reset_trace_globals
from opentelemetry.test.test_base import TestBase


@pytest.fixture(scope="session")
def span_exporter() -> Generator[InMemorySpanExporter, Any, None]:
    tracer_provider, span_exporter = TestBase.create_tracer_provider()
    trace.set_tracer_provider(tracer_provider)
    try:
        yield span_exporter
    finally:
        reset_trace_globals()


@pytest.fixture(scope="session")
def metric_reader() -> Generator[InMemoryMetricReader, Any, None]:
    meter_provider, metric_reader = TestBase.create_meter_provider()
    metrics.set_meter_provider(meter_provider)
    try:
        yield cast("InMemoryMetricReader", metric_reader)
    finally:
        reset_metrics_globals()
