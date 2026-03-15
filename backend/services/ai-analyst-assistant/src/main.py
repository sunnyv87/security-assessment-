"""AI Analyst Assistant — FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI

from src.config.settings import settings
from src.api.routes import router
from src.api.dependencies import set_orchestrator
from src.middleware.rate_limiter import RateLimitMiddleware
from src.pipelines.orchestrator import PipelineOrchestrator
from src.services.kafka_consumer import FindingEnrichmentConsumer

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle — initialize and cleanup resources."""
    # Startup
    orchestrator = PipelineOrchestrator()
    await orchestrator.startup()
    set_orchestrator(orchestrator)

    # Start Kafka consumer in background
    consumer = FindingEnrichmentConsumer(orchestrator)
    consumer_task: asyncio.Task[None] | None = None
    try:
        await consumer.start()
        consumer_task = asyncio.create_task(consumer.consume_loop())
    except Exception:
        logger.warning("kafka_unavailable", msg="Running without async enrichment")

    logger.info("service_started", service=settings.service_name)

    yield

    # Shutdown
    if consumer_task:
        await consumer.stop()
        consumer_task.cancel()
    await orchestrator.shutdown()
    logger.info("service_stopped")


app = FastAPI(
    title="AI Analyst Assistant",
    description=(
        "AI-powered assistant for VAPT security analysts. "
        "Provides vulnerability summarization, false positive detection, "
        "risk prioritization, remediation suggestions, and report drafting. "
        "All outputs are recommendations requiring analyst review. "
        "The AI module CANNOT publish reports."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.environment == "development",
    )
