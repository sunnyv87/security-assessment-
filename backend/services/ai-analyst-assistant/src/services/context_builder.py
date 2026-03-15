"""Context Builder — assembles RAG context from pgvector and PostgreSQL."""

from __future__ import annotations

from typing import Any

import structlog

from src.config.settings import settings
from src.models.domain import Finding, AssetContext, ScannerRuleContext, EngagementContext

logger = structlog.get_logger()


class ContextBuilder:
    """Builds enriched context for prompt rendering by querying
    pgvector for similar historical findings and loading asset metadata.
    """

    def __init__(self, db_pool: Any) -> None:
        self._db = db_pool

    async def get_similar_findings(
        self,
        finding: Finding,
        *,
        top_k: int = 0,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Query pgvector for historically similar findings with analyst verdicts.

        Uses cosine similarity on pre-computed finding embeddings.
        Returns findings that have been validated by an analyst.
        """
        top_k = top_k or settings.rag_similarity_top_k
        min_similarity = min_similarity or settings.rag_similarity_threshold

        query = """
            SELECT
                f.id,
                f.title,
                f.cwe_id,
                f.severity,
                f.scanner,
                f.validation_verdict,
                f.ai_false_positive_prob,
                f.ai_remediation,
                1 - (fe.embedding <=> $1) AS similarity
            FROM findings f
            JOIN finding_embeddings fe ON fe.finding_id = f.id
            WHERE f.validation_verdict IS NOT NULL
              AND f.tenant_id = $2
              AND 1 - (fe.embedding <=> $1) >= $3
            ORDER BY fe.embedding <=> $1
            LIMIT $4
        """

        # In production, we'd generate the embedding for the current finding
        # and pass it as $1. For now, return empty if DB not connected.
        if not self._db:
            return []

        try:
            embedding = await self._generate_embedding(finding)
            rows = await self._db.fetch(
                query,
                embedding,
                finding.engagement_id,  # tenant scoping
                min_similarity,
                top_k,
            )
            results = [dict(row) for row in rows]

            # RAG poisoning defense (RT-AI-02):
            # Filter out suspiciously high-confidence FP markings
            results = [
                r for r in results
                if not (
                    r.get("ai_false_positive_prob") is not None
                    and r["ai_false_positive_prob"] > 0.95
                    and r.get("validation_verdict") == "false_positive"
                )
            ]

            # If > 80% of similar findings are false_positive, flag as anomalous
            # and don't use the historical context (possible RAG poisoning)
            if results:
                fp_count = sum(
                    1 for r in results
                    if r.get("validation_verdict") == "false_positive"
                )
                fp_ratio = fp_count / len(results)
                if fp_ratio > 0.80:
                    logger.warning(
                        "rag_anomaly_detected",
                        finding_id=finding.id,
                        fp_ratio=fp_ratio,
                        total_similar=len(results),
                    )
                    return []

            return results
        except Exception:
            logger.warning("rag_query_failed", finding_id=finding.id)
            return []

    async def get_asset_context(self, asset_identifier: str) -> AssetContext:
        """Load asset metadata from the asset inventory."""
        if not self._db:
            return AssetContext()

        try:
            row = await self._db.fetchrow(
                """
                SELECT environment, internet_facing, data_classification,
                       tech_stack, language, framework, framework_version,
                       runtime, database_type, deployment_type, server_tech,
                       security_layers, security_controls, asset_criticality
                FROM assets
                WHERE hostname = $1 OR ip_address = $1
                LIMIT 1
                """,
                asset_identifier,
            )
            if row:
                return AssetContext(**dict(row))
        except Exception:
            logger.warning("asset_context_failed", asset=asset_identifier)

        return AssetContext()

    async def get_scanner_rule_context(
        self, scanner: str, cwe_id: str
    ) -> ScannerRuleContext:
        """Load historical false positive rates for a scanner rule."""
        if not self._db:
            return ScannerRuleContext()

        try:
            row = await self._db.fetchrow(
                """
                SELECT
                    rule_id AS id,
                    rule_description AS description,
                    fp_rate,
                    historical_fp_rate
                FROM scanner_rules
                WHERE scanner = $1 AND cwe_id = $2
                LIMIT 1
                """,
                scanner,
                cwe_id,
            )
            if row:
                return ScannerRuleContext(**dict(row))
        except Exception:
            logger.warning("scanner_rule_failed", scanner=scanner, cwe=cwe_id)

        return ScannerRuleContext()

    async def get_engagement_context(self, engagement_id: str) -> EngagementContext:
        """Load engagement metadata."""
        if not self._db:
            return EngagementContext(id=engagement_id, customer_name="", name="", type="")

        try:
            row = await self._db.fetchrow(
                """
                SELECT e.id, c.company_name AS customer_name, e.name,
                       e.engagement_type AS type, c.industry,
                       e.scope_description, e.start_date, e.end_date,
                       e.compliance_frameworks
                FROM engagements e
                JOIN customers c ON c.id = e.customer_id
                WHERE e.id = $1
                """,
                engagement_id,
            )
            if row:
                data = dict(row)
                data["lead_analyst"] = ""
                return EngagementContext(**data)
        except Exception:
            logger.warning("engagement_context_failed", engagement_id=engagement_id)

        return EngagementContext(id=engagement_id, customer_name="", name="", type="")

    async def format_similar_findings(
        self, similar: list[dict[str, Any]]
    ) -> str:
        """Format similar findings for injection into prompt."""
        if not similar:
            return "No similar historical findings found."

        lines = []
        for i, s in enumerate(similar, 1):
            verdict = s.get("validation_verdict", "unknown")
            lines.append(
                f"{i}. [{s['severity'].upper()}] {s['title']} "
                f"(CWE-{s['cwe_id']}) — Analyst verdict: {verdict} "
                f"(similarity: {s.get('similarity', 0):.0%})"
            )
        return "\n".join(lines)

    async def format_verified_findings(
        self, similar: list[dict[str, Any]]
    ) -> tuple[str, int, int, int, int]:
        """Format verified findings and compute TP/FP/Dup counts."""
        tp = sum(1 for s in similar if s.get("validation_verdict") in ("true_positive", "confirmed_exploitable"))
        fp = sum(1 for s in similar if s.get("validation_verdict") == "false_positive")
        dup = sum(1 for s in similar if s.get("validation_verdict") == "duplicate")
        total = len(similar)

        text = await self.format_similar_findings(similar)
        return text, total, tp, fp, dup

    async def _generate_embedding(self, finding: Finding) -> list[float]:
        """Generate a text embedding for a finding (calls embedding API)."""
        # In production, this calls the embedding model endpoint.
        # Placeholder returns empty vector.
        text = f"{finding.title} {finding.cwe_id} {finding.description}"
        _ = text  # Would be sent to embedding API
        return [0.0] * 1536  # text-embedding-3-small dimension

    def truncate(self, text: str | None, max_chars: int) -> str:
        """Safely truncate text for prompt injection."""
        if not text:
            return "N/A"
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 20] + "\n... [truncated]"
