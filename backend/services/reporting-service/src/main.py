"""FastAPI application entry point for the Reporting Service."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from src.api import routes
from src.config.settings import settings
from src.pipeline.generator import ReportGenerator
from src.services.kafka_consumer import ReportTriggerConsumer

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initializes generator and Kafka consumer."""
    # Initialize report generator
    gen = ReportGenerator()
    routes.generator = gen

    # Start Kafka consumer in background
    consumer = ReportTriggerConsumer(gen)
    consumer_task = None
    try:
        await consumer.start()
        consumer_task = asyncio.create_task(consumer.consume())
        logger.info("kafka_consumer_task_started")
    except Exception:
        logger.warning("kafka_unavailable_running_without_consumer")

    logger.info("reporting_service_started", port=settings.api_port)

    yield

    # Shutdown
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
    await consumer.stop()
    await gen.close()
    logger.info("reporting_service_stopped")


app = FastAPI(
    title="VAPT Reporting Service",
    description="Report generation, approval, and delivery for VAPT engagements",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(routes.router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.service_name}
