"""
QALIS Dashboard — FastAPI Application
=====================================

REST API for real-time QALIS metric monitoring.

Endpoints:
    POST /ingest              Ingest a QALISResult from a collector
    GET  /scores/{system_id}  Latest dimension + composite scores
    GET  /violations          Current threshold violations (all systems)
    GET  /history/{system_id} Time-series of composite scores
    GET  /radar/{system_id}   Dimension scores formatted for radar chart
    GET  /health              Service health check
    GET  /metrics             Prometheus scrape endpoint

Paper reference: §3.3 (dashboard instrumentation), §4.4 (IQ-4).
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from fastapi import FastAPI, HTTPException, status
    from fastapi.responses import PlainTextResponse
    from pydantic import BaseModel
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    logger.warning(
        "FastAPI not installed. Install with: pip install fastapi uvicorn\n"
        "The dashboard module will be unavailable until then."
    )

from qalis.dashboard.store import MetricsStore
from qalis.dashboard.prometheus import PrometheusExporter


# ---------------------------------------------------------------------------
# Pydantic request / response models (only defined when FastAPI is available)
# ---------------------------------------------------------------------------

if _FASTAPI_AVAILABLE:
    class IngestPayload(BaseModel):
        system_id: str
        composite_score: float
        dimension_scores: Dict[str, Dict[str, Any]]
        threshold_violations: List[str] = []
        raw_metrics: Dict[str, Any] = {}
        timestamp: Optional[str] = None
        request_id: Optional[str] = None

    class ScoresResponse(BaseModel):
        system_id: str
        composite_score: float
        dimension_scores: Dict[str, float]
        threshold_violations: List[str]
        quality_grade: str
        as_of: str


def _grade(score: float) -> str:
    if score >= 9.0: return "A+"
    if score >= 8.5: return "A"
    if score >= 8.0: return "B+"
    if score >= 7.5: return "B"
    if score >= 7.0: return "C+"
    if score >= 6.5: return "C"
    if score >= 6.0: return "D"
    return "F"


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

class QALISDashboard:
    """
    Encapsulates the FastAPI app, metrics store, and Prometheus exporter.

    Usage::

        dashboard = QALISDashboard()
        app = dashboard.app          # pass to uvicorn
    """

    def __init__(self, store: Optional["MetricsStore"] = None) -> None:
        if not _FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI is required for the dashboard. "
                "Install with: pip install fastapi uvicorn"
            )
        self.store = store or MetricsStore()
        self.exporter = PrometheusExporter(self.store)
        self.app = self._build_app()

    def _build_app(self) -> "FastAPI":
        app = FastAPI(
            title="QALIS Quality Dashboard",
            description=(
                "Real-time quality monitoring for LLM-integrated systems.\n\n"
                "Paper: QUATIC 2025 — Software Quality in an AI-Driven World."
            ),
            version="1.0.0",
        )

        store = self.store
        exporter = self.exporter

        @app.get("/health")
        def health():
            return {"status": "ok", "systems": list(store.systems())}

        @app.post("/ingest", status_code=status.HTTP_201_CREATED)
        def ingest(payload: IngestPayload):
            dim_scores = {
                k: v.get("score", 0.0)
                for k, v in payload.dimension_scores.items()
            }
            store.record(
                system_id=payload.system_id,
                composite=payload.composite_score,
                dimension_scores=dim_scores,
                violations=payload.threshold_violations,
                raw_metrics=payload.raw_metrics,
                timestamp=payload.timestamp or datetime.now(timezone.utc).isoformat(),
            )
            exporter.update(payload.system_id, payload.composite_score, dim_scores,
                            payload.threshold_violations)
            return {"status": "recorded", "system_id": payload.system_id}

        @app.get("/scores/{system_id}", response_model=ScoresResponse)
        def get_scores(system_id: str):
            latest = store.latest(system_id)
            if latest is None:
                raise HTTPException(status_code=404, detail=f"System {system_id!r} not found")
            return ScoresResponse(
                system_id=system_id,
                composite_score=latest["composite"],
                dimension_scores=latest["dimension_scores"],
                threshold_violations=latest["violations"],
                quality_grade=_grade(latest["composite"]),
                as_of=latest["timestamp"],
            )

        @app.get("/violations")
        def get_violations():
            return {
                sid: store.latest(sid)["violations"]
                for sid in store.systems()
                if store.latest(sid)
            }

        @app.get("/history/{system_id}")
        def get_history(system_id: str, last_n: int = 100):
            history = store.history(system_id, last_n=last_n)
            if not history:
                raise HTTPException(status_code=404, detail=f"No history for {system_id!r}")
            return {"system_id": system_id, "history": history}

        @app.get("/radar/{system_id}")
        def get_radar(system_id: str):
            latest = store.latest(system_id)
            if latest is None:
                raise HTTPException(status_code=404, detail=f"System {system_id!r} not found")
            return {
                "system_id":       system_id,
                "composite_score": latest["composite"],
                "dimensions":      latest["dimension_scores"],
                "quality_grade":   _grade(latest["composite"]),
            }

        @app.get("/metrics", response_class=PlainTextResponse)
        def prometheus_metrics():
            return exporter.render()

        return app


def create_app() -> "FastAPI":
    """FastAPI application factory (for uvicorn --factory)."""
    dashboard = QALISDashboard()
    return dashboard.app
