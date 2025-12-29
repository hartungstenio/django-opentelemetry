from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


def create_meter_provider() -> tuple[MeterProvider, InMemoryMetricReader]:
    """Create a `MeterProvider` and an `InMemoryMetricReader`.

    Returns:
        A tuple with the meter provider in the first element and the
        in-memory metrics exporter in the second
    """
    memory_reader = InMemoryMetricReader()
    meter_provider = MeterProvider(metric_readers=[memory_reader])
    return meter_provider, memory_reader
