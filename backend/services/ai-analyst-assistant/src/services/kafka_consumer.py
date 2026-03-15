"""Kafka consumer for async finding enrichment pipeline.

Listens on `finding.normalized` topic and runs the full AI enrichment
pipeline (summarization + FP detection + remediation) on each new finding.
Publishes results to `finding.ai_enriched` topic.
"""

from __future__ import annotations

import json

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from src.config.settings import settings
from src.models.domain import Finding
from src.pipelines.orchestrator import PipelineOrchestrator

logger = structlog.get_logger()


class FindingEnrichmentConsumer:
    """Consumes normalized findings from Kafka and runs AI enrichment."""

    def __init__(self, orchestrator: PipelineOrchestrator) -> None:
        self._orchestrator = orchestrator
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None
        self._running = False

    async def start(self) -> None:
        """Start the Kafka consumer and producer."""
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_findings_normalized,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        await self._consumer.start()
        await self._producer.start()
        self._running = True

        logger.info(
            "kafka_consumer_started",
            topic=settings.kafka_topic_findings_normalized,
            group=settings.kafka_consumer_group,
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer and producer."""
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        logger.info("kafka_consumer_stopped")

    async def consume_loop(self) -> None:
        """Main consumption loop — processes findings one at a time.

        For each normalized finding:
        1. Parse the finding from the Kafka message
        2. Run AI enrichment (summary + FP detection + remediation)
        3. Publish enriched result to finding.ai_enriched topic
        """
        if not self._consumer:
            return

        async for message in self._consumer:
            if not self._running:
                break

            try:
                await self._process_message(message.value)
            except Exception:
                logger.exception(
                    "enrichment_failed",
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                )

    async def _process_message(self, data: dict) -> None:
        """Process a single normalized finding message."""
        finding_data = data.get("finding")
        tenant_id = data.get("tenant_id", "unknown")

        if not finding_data:
            logger.warning("empty_finding_message")
            return

        finding = Finding(**finding_data)
        logger.info("enrichment_start", finding_id=finding.id, tenant_id=tenant_id)

        # Run full enrichment pipeline
        result = await self._orchestrator.analyze_finding(
            finding,
            stages=["summary", "fp_detection", "remediation"],
            tenant_id=tenant_id,
        )

        # Publish enriched result
        enriched_event = {
            "finding_id": finding.id,
            "tenant_id": tenant_id,
            "engagement_id": finding.engagement_id,
            "ai_analysis": {
                "summary": result.summary.model_dump() if result.summary else None,
                "false_positive": result.false_positive.model_dump() if result.false_positive else None,
                "remediation": result.remediation.model_dump() if result.remediation else None,
                "model_version": result.model_version,
                "processing_time_ms": result.processing_time_ms,
            },
        }

        if self._producer:
            await self._producer.send(
                settings.kafka_topic_findings_enriched,
                value=enriched_event,
            )

        logger.info(
            "enrichment_complete",
            finding_id=finding.id,
            stages=result.stages_completed,
            duration_ms=result.processing_time_ms,
        )
