"""
Idea Inc - Telemetry & Observability

OpenTelemetry integration for distributed tracing and metrics.
"""

import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import OpenTelemetry packages
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry packages not available")

# Try to import Prometheus client
try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available")


class TelemetryManager:
    """
    Manages OpenTelemetry and Prometheus instrumentation.
    
    Provides:
    - Distributed tracing
    - Custom metrics
    - Service instrumentation
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str = "0.1.0",
        otel_endpoint: Optional[str] = None,
        enabled: bool = False,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.otel_endpoint = otel_endpoint
        self.enabled = enabled and OTEL_AVAILABLE
        
        self._tracer = None
        self._meter = None
        self._metrics = {}
    
    def setup(self) -> None:
        """Initialize telemetry"""
        if self.enabled:
            self._setup_tracing()
            self._setup_metrics()
        
        # Always setup Prometheus metrics (they work without OTEL)
        if PROMETHEUS_AVAILABLE:
            self._setup_prometheus_metrics()
        
        logger.info(
            "Telemetry initialized",
            service=self.service_name,
            otel_enabled=self.enabled,
            prometheus_enabled=PROMETHEUS_AVAILABLE,
        )
    
    def _setup_tracing(self) -> None:
        """Setup OpenTelemetry tracing"""
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
        })
        
        provider = TracerProvider(resource=resource)
        
        if self.otel_endpoint:
            exporter = OTLPSpanExporter(endpoint=self.otel_endpoint)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
        
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(self.service_name)
    
    def _setup_metrics(self) -> None:
        """Setup OpenTelemetry metrics"""
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
        })
        
        if self.otel_endpoint:
            exporter = OTLPMetricExporter(endpoint=self.otel_endpoint)
            reader = PeriodicExportingMetricReader(exporter)
            provider = MeterProvider(resource=resource, metric_readers=[reader])
        else:
            provider = MeterProvider(resource=resource)
        
        metrics.set_meter_provider(provider)
        self._meter = metrics.get_meter(self.service_name)
    
    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics"""
        # Request metrics
        self._metrics["request_count"] = Counter(
            f"{self.service_name}_requests_total",
            "Total number of requests",
            ["method", "endpoint", "status"],
        )
        
        self._metrics["request_duration"] = Histogram(
            f"{self.service_name}_request_duration_seconds",
            "Request duration in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )
        
        # Service info
        self._metrics["info"] = Info(
            f"{self.service_name}_info",
            "Service information",
        )
        self._metrics["info"].info({
            "version": self.service_version,
            "service": self.service_name,
        })
    
    def instrument_fastapi(self, app) -> None:
        """Instrument a FastAPI application"""
        if self.enabled and OTEL_AVAILABLE:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented with OpenTelemetry")
    
    @property
    def tracer(self):
        """Get the tracer instance"""
        return self._tracer
    
    def get_metric(self, name: str):
        """Get a Prometheus metric by name"""
        return self._metrics.get(name)
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
    ) -> None:
        """Record a request metric"""
        if PROMETHEUS_AVAILABLE:
            self._metrics["request_count"].labels(
                method=method,
                endpoint=endpoint,
                status=str(status),
            ).inc()
            
            self._metrics["request_duration"].labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)


# =============================================================================
# Simulation-specific Metrics
# =============================================================================

class SimulationMetrics:
    """Prometheus metrics for simulation service"""
    
    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            return
        
        # World metrics
        self.active_worlds = Gauge(
            "ideainc_active_worlds",
            "Number of active simulation worlds",
        )
        
        self.total_agents = Gauge(
            "ideainc_total_agents",
            "Total number of agents across all worlds",
        )
        
        # Simulation metrics
        self.simulation_steps = Counter(
            "ideainc_simulation_steps_total",
            "Total simulation steps executed",
            ["world_id"],
        )
        
        self.spread_events = Counter(
            "ideainc_spread_events_total",
            "Total idea spread events",
            ["world_id", "accepted"],
        )
        
        self.mutations = Counter(
            "ideainc_mutations_total",
            "Total idea mutations",
            ["world_id", "mutation_type"],
        )
        
        # Performance metrics
        self.step_duration = Histogram(
            "ideainc_step_duration_seconds",
            "Duration of simulation steps",
            ["world_id"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )
        
        # Idea metrics
        self.ideas_injected = Counter(
            "ideainc_ideas_injected_total",
            "Total ideas injected",
            ["world_id"],
        )
        
        self.total_adoptions = Counter(
            "ideainc_adoptions_total",
            "Total idea adoptions",
            ["world_id"],
        )
    
    def record_step(
        self,
        world_id: str,
        duration: float,
        spread_attempts: int,
        adoptions: int,
        mutations: int,
    ) -> None:
        """Record metrics for a simulation step"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.simulation_steps.labels(world_id=world_id).inc()
        self.step_duration.labels(world_id=world_id).observe(duration)
        
        if adoptions > 0:
            self.total_adoptions.labels(world_id=world_id).inc(adoptions)
    
    def record_spread(
        self,
        world_id: str,
        accepted: bool,
    ) -> None:
        """Record a spread event"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.spread_events.labels(
            world_id=world_id,
            accepted=str(accepted).lower(),
        ).inc()
    
    def record_mutation(
        self,
        world_id: str,
        mutation_type: str,
    ) -> None:
        """Record a mutation event"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.mutations.labels(
            world_id=world_id,
            mutation_type=mutation_type,
        ).inc()
    
    def update_world_counts(
        self,
        active_worlds: int,
        total_agents: int,
    ) -> None:
        """Update world count gauges"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.active_worlds.set(active_worlds)
        self.total_agents.set(total_agents)


# =============================================================================
# AI Service Metrics
# =============================================================================

class AIMetrics:
    """Prometheus metrics for AI service"""
    
    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            return
        
        # LLM metrics
        self.llm_requests = Counter(
            "ideainc_llm_requests_total",
            "Total LLM API requests",
            ["operation", "source"],  # source: llm or fallback
        )
        
        self.llm_latency = Histogram(
            "ideainc_llm_latency_seconds",
            "LLM API latency",
            ["operation"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )
        
        self.llm_errors = Counter(
            "ideainc_llm_errors_total",
            "Total LLM API errors",
            ["operation", "error_type"],
        )
        
        # Vector store metrics
        self.vector_operations = Counter(
            "ideainc_vector_operations_total",
            "Total vector store operations",
            ["operation"],  # add, search, delete
        )
        
        self.vector_store_size = Gauge(
            "ideainc_vector_store_size",
            "Number of items in vector store",
        )
    
    def record_llm_request(
        self,
        operation: str,
        source: str,
        latency: Optional[float] = None,
    ) -> None:
        """Record an LLM request"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.llm_requests.labels(operation=operation, source=source).inc()
        
        if latency is not None:
            self.llm_latency.labels(operation=operation).observe(latency)
    
    def record_llm_error(
        self,
        operation: str,
        error_type: str,
    ) -> None:
        """Record an LLM error"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.llm_errors.labels(operation=operation, error_type=error_type).inc()
    
    def record_vector_operation(self, operation: str) -> None:
        """Record a vector store operation"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.vector_operations.labels(operation=operation).inc()
    
    def update_vector_store_size(self, size: int) -> None:
        """Update vector store size gauge"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.vector_store_size.set(size)


# =============================================================================
# Factory Functions
# =============================================================================

def setup_telemetry(
    service_name: str,
    service_version: str = "0.1.0",
    otel_endpoint: Optional[str] = None,
    enabled: bool = False,
) -> TelemetryManager:
    """
    Factory function to create and setup telemetry.
    
    Args:
        service_name: Name of the service
        service_version: Version of the service
        otel_endpoint: OpenTelemetry collector endpoint
        enabled: Whether to enable OTEL tracing
    
    Returns:
        Configured TelemetryManager
    """
    manager = TelemetryManager(
        service_name=service_name,
        service_version=service_version,
        otel_endpoint=otel_endpoint,
        enabled=enabled,
    )
    manager.setup()
    return manager

