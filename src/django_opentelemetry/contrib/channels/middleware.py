"""Django Channels middleware for OpenTelemetry tracing."""

from collections.abc import Awaitable, Callable, MutableMapping
from timeit import default_timer
from typing import Any, Literal

from asgiref.typing import ASGI3Application
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.asgi import (
    OpenTelemetryMiddleware as OTelASGIMiddleware,
)
from opentelemetry.instrumentation.asgi.types import (
    ClientRequestHook,
    ClientResponseHook,
    ServerRequestHook,
)
from opentelemetry.util.http import ExcludeList

from django_opentelemetry._compat import override

Scope = MutableMapping[str, Any]


def _filter_span_attributes(attributes: dict[str, str]) -> dict[str, str]:
    """Filter span attributes to use in metrics."""
    allowed_attributes = [
        "messaging.operation.name",
        "messaging.system",
        "error.type",
        "messaging.consumer.group.name",
        "messaging.destination.name",
        "messaging.destination.subscription.name",
        "messaging.destination.template",
        "server.address",
        "messaging.destination.partition.id",
        "server.port",
    ]
    return {key: value for key, value in attributes.items() if key in allowed_attributes}


class OpenTelemetryMiddleware(OTelASGIMiddleware):
    """Django Channels middleware for OpenTelemetry tracing."""

    def __init__(  # noqa: PLR0913
        self,
        app: ASGI3Application,
        excluded_urls: ExcludeList | str | None = None,
        default_span_details: Callable[[Scope], tuple[str, dict[str, str]]] | None = None,
        server_request_hook: ServerRequestHook = None,
        client_request_hook: ClientRequestHook = None,
        client_response_hook: ClientResponseHook = None,
        tracer_provider: trace.TracerProvider | None = None,
        meter_provider: metrics.MeterProvider | None = None,
        tracer: trace.Tracer | None = None,
        meter: metrics.Meter | None = None,
        http_capture_headers_server_request: list[str] | None = None,
        http_capture_headers_server_response: list[str] | None = None,
        http_capture_headers_sanitize_fields: list[str] | None = None,
        exclude_spans: list[Literal["receive", "send"]] | None = None,
    ) -> None:
        """Initialize the OpenTelemetryMiddleware."""
        super().__init__(
            app,
            excluded_urls,
            default_span_details,
            server_request_hook,
            client_request_hook,
            client_response_hook,
            tracer_provider,
            meter_provider,
            tracer,
            meter,
            http_capture_headers_server_request,
            http_capture_headers_server_response,
            http_capture_headers_sanitize_fields,
            exclude_spans,
        )

        self.consumed_messages_counter = self.meter.create_counter(
            "messaging.client.consumed.messages",
            description="Number of messages that were delivered to the application.",
        )
        self.process_duration_histogram = self.meter.create_histogram(
            "messaging.process.duration",
            description="Duration of processing operation.",
            unit="s",
        )

    @override
    async def __call__(
        self,
        scope: Scope,
        receive: Callable[[], Awaitable[MutableMapping[str, Any]]],
        send: Callable[[MutableMapping[str, Any]], Awaitable[None]],
    ) -> None:
        """ASGI application callable.

        Args:
            scope: An ASGI environment.
            receive: An awaitable callable yielding dictionaries
            send: An awaitable callable taking a single dictionary as argument.
        """
        if scope.get("type") != "channel":
            return await super().__call__(scope, receive, send)

        attributes = {
            "messaging.operation.name": "consume",
            "messaging.system": "django_channels",
            "messaging.destination.name": scope["channel"],
            "messaging.destination.temporary": True,
            "messaging.operation.type": "process",
        }
        start = default_timer()
        span = None
        try:
            with self.tracer.start_as_current_span(
                name=f"consume {scope['channel']}",
                kind=trace.SpanKind.CONSUMER,
                end_on_exit=False,
                attributes=attributes,
            ) as span:
                await super().__call__(scope, receive, send)
        finally:
            metric_attributes = _filter_span_attributes(attributes)
            self.consumed_messages_counter.add(1, metric_attributes)

            duration_s = default_timer() - start
            self.process_duration_histogram.record(duration_s, metric_attributes)

            if span and span.is_recording():
                span.end()
