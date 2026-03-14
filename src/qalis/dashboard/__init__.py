"""
QALIS Dashboard Package
=======================

Real-time quality monitoring dashboard built with FastAPI + Prometheus.
Provides REST endpoints for metric ingestion, live score retrieval,
and Grafana-compatible time-series export.

Components:
    QALISDashboard   FastAPI application factory (main entry point)
    MetricsStore     In-memory / Redis-backed metric store
    PrometheusExporter  Prometheus /metrics endpoint

Deployment (paper study)::

    uvicorn qalis.dashboard:create_app --factory --host 0.0.0.0 --port 8080

Configuration: configs/monitoring_config.yaml
Paper reference: §3.3, §4.4 (IQ-4 observability coverage).
"""

from qalis.dashboard.app import create_app, QALISDashboard
from qalis.dashboard.store import MetricsStore
from qalis.dashboard.prometheus import PrometheusExporter

__all__ = [
    "create_app",
    "QALISDashboard",
    "MetricsStore",
    "PrometheusExporter",
]
