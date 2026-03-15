"""Kafka consumer for automatic report generation triggers."""

from __future__ import annotations

import json

import structlog
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from src.config.settings import settings
from src.models.domain import GenerateReportRequest, ReportFormat, ReportType
from src.pipeline.generator import ReportGenerator

logger = structlog.get_logger()


class ReportTriggerConsumer:
    """Consumes finding.validated events to auto-trigger report generation.

    When all findings for an engagement are validated, this consumer
    triggers automatic report generation for configured report types.
    """

    def __init__(self, generator: ReportGenerator) -> None:
        self._generator = generator
        self._consumer: AIOKafkaConsumer | None = None
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        """Start the Kafka consumer and producer."""
        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic_finding_validated,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_consumer_group,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
        )
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._consumer.start()
        await self._producer.start()
        logger.info("kafka_consumer_started", topic=settings.kafka_topic_finding_validated)

    async def stop(self) -> None:
        """Stop the Kafka consumer and producer."""
        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()
        logger.info("kafka_consumer_stopped")

    async def consume(self) -> None:
        """Main consumption loop — processes finding.validated events."""
        if not self._consumer:
            return

        async for message in self._consumer:
            try:
                await self._handle_message(message.value)
            except Exception:
                logger.exception(
                    "message_processing_failed",
                    topic=message.topic,
                    offset=message.offset,
                )

    async def _handle_message(self, event: dict) -> None:
        """Handle a finding.validated event.

        Expected event schema:
        {
            "engagement_id": "...",
            "tenant_id": "...",
            "trigger": "all_findings_validated" | "finding_validated",
            "report_types": ["full_technical"],  # optional
            "format": "pdf"  # optional
        }
        """
        trigger = event.get("trigger", "finding_validated")

        # Only auto-generate when all findings are validated
        if trigger != "all_findings_validated":
            logger.debug("skipping_non_trigger_event", trigger=trigger)
            return

        engagement_id = event.get("engagement_id")
        tenant_id = event.get("tenant_id")
        if not engagement_id or not tenant_id:
            logger.warning("missing_required_fields", event=event)
            return

        report_types = event.get("report_types", [ReportType.FULL_TECHNICAL])
        fmt = ReportFormat(event.get("format", "pdf"))

        for report_type in report_types:
            try:
                request = GenerateReportRequest(
                    engagement_id=engagement_id,
                    report_type=ReportType(report_type),
                    format=fmt,
                    include_ai_content=True,
                )

                record = await self._generator.generate(
                    request,
                    tenant_id=tenant_id,
                    generated_by="system:auto-generation",
                )

                # Publish report.generated event
                if self._producer:
                    await self._producer.send(
                        settings.kafka_topic_report_generated,
                        value={
                            "report_id": record.id,
                            "engagement_id": engagement_id,
                            "tenant_id": tenant_id,
                            "report_type": report_type,
                            "format": fmt,
                            "status": record.status,
                            "file_size_bytes": record.file_size_bytes,
                        },
                    )

                logger.info(
                    "auto_report_generated",
                    report_id=record.id,
                    engagement_id=engagement_id,
                    report_type=report_type,
                )

            except Exception:
                logger.exception(
                    "auto_report_generation_failed",
                    engagement_id=engagement_id,
                    report_type=report_type,
                )
