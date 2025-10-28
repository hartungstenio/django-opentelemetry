from typing import Any, Generator, cast

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.test.globals_test import reset_metrics_globals
from opentelemetry.test.test_base import TestBase


@pytest.fixture(scope="session")
def metric_reader() -> Generator[InMemoryMetricReader, Any, None]:
    meter_provider, metric_reader = TestBase.create_meter_provider()
    metrics.set_meter_provider(meter_provider)
    try:
        yield cast("InMemoryMetricReader", metric_reader)
    finally:
        reset_metrics_globals()
