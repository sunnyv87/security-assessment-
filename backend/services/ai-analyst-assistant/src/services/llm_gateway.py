"""LLM Gateway — manages Claude API calls with retry, caching, and audit logging."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date
from typing import Any

import anthropic
import structlog
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config.settings import settings
from src.services.cache import CacheService
from src.models.domain import AuditLogEntry

logger = structlog.get_logger()


class LLMGateway:
    """Thin wrapper around the Anthropic SDK with caching, retries, and audit."""

    def __init__(self, cache: CacheService) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.claude_timeout_seconds,
            max_retries=0,  # we handle retries ourselves
        )
        self._cache = cache
        self._model = settings.claude_model

    async def invoke(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        stage: str,
        tenant_id: str,
        analyst_id: str | None = None,
        finding_id: str | None = None,
        force_refresh: bool = False,
        cache_ttl: int | None = None,
    ) -> tuple[dict[str, Any], bool]:
        """Call Claude API or return cached result.

        Returns:
            Tuple of (parsed_json_response, was_cached).
        """
        # Build cache key from content hash (includes tenant_id to prevent cross-tenant poisoning)
        cache_key = self._cache_key(system_prompt, user_prompt, stage, tenant_id)

        # Check cache
        if not force_refresh:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                logger.info("cache_hit", stage=stage, finding_id=finding_id)
                return cached, True

        # Check tenant daily token budget before calling Claude
        await self._check_token_budget(tenant_id)

        # Call Claude API with retries
        start = time.monotonic()
        response = await self._call_claude(system_prompt, user_prompt, max_tokens)
        latency_ms = int((time.monotonic() - start) * 1000)

        # Track cumulative token usage per tenant in Redis
        total_tokens = response.usage.input_tokens + response.usage.output_tokens
        await self._track_token_usage(tenant_id, total_tokens)

        # Parse JSON from response
        content_text = response.content[0].text
        parsed = self._parse_json(content_text)

        # Sanitize AI output to prevent XSS and code injection
        parsed = self._sanitize_output(parsed)

        # Cache result
        ttl = cache_ttl or self._default_ttl(stage)
        await self._cache.set(cache_key, parsed, ttl=ttl)

        # Audit log
        input_hash = hashlib.sha256(
            (system_prompt + user_prompt).encode()
        ).hexdigest()[:16]

        audit = AuditLogEntry(
            id=f"audit-{int(time.time() * 1000)}",
            tenant_id=tenant_id,
            analyst_id=analyst_id,
            finding_id=finding_id,
            stage=stage,
            input_hash=input_hash,
            model_version=self._model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            latency_ms=latency_ms,
            confidence=parsed.get("confidence", 0.0),
            cached=False,
        )
        logger.info(
            "llm_invocation",
            stage=stage,
            finding_id=finding_id,
            latency_ms=latency_ms,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

        return parsed, False

    @retry(
        stop=stop_after_attempt(settings.claude_max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((anthropic.APITimeoutError, anthropic.APIConnectionError)),
    )
    async def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> anthropic.types.Message:
        """Execute a Claude API call with exponential-backoff retry."""
        return await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=settings.claude_temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        """Extract JSON from Claude's response text."""
        try:
            # Try direct parse first
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

            # Try extracting JSON from markdown code block
            if "```json" in text:
                start = text.index("```json") + 7
                end = text.index("```", start)
                return json.loads(text[start:end].strip())

            if "```" in text:
                start = text.index("```") + 3
                end = text.index("```", start)
                return json.loads(text[start:end].strip())

            # Try finding JSON object boundaries
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError) as e:
            logger.error("ai_response_parse_failed", error=str(e))
            return {"error": "Failed to parse AI response", "raw_text": text[:500]}

    @staticmethod
    def _sanitize_output(data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize AI output to prevent XSS and code injection in stored results."""
        def _sanitize_value(v):
            if isinstance(v, str):
                # Strip HTML tags that could cause XSS
                v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
                v = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', v, flags=re.IGNORECASE)
                v = re.sub(r'javascript:', '', v, flags=re.IGNORECASE)
                return v
            elif isinstance(v, dict):
                return {k: _sanitize_value(val) for k, val in v.items()}
            elif isinstance(v, list):
                return [_sanitize_value(item) for item in v]
            return v
        return _sanitize_value(data)

    async def _check_token_budget(self, tenant_id: str) -> None:
        """Check if tenant has exceeded their daily token budget. Raises HTTP 429 if exceeded."""
        budget_key = f"token_budget:{tenant_id}:{date.today().isoformat()}"
        current = await self._cache.get(budget_key)
        if current is not None:
            used = current.get("tokens", 0) if isinstance(current, dict) else 0
            if used >= settings.max_tokens_per_tenant_per_day:
                logger.warning("token_budget_exceeded", tenant_id=tenant_id, used=used)
                raise HTTPException(status_code=429, detail="Daily AI token budget exceeded")

    async def _track_token_usage(self, tenant_id: str, tokens: int) -> None:
        """Track cumulative token usage per tenant per day in Redis."""
        budget_key = f"token_budget:{tenant_id}:{date.today().isoformat()}"
        current = await self._cache.get(budget_key)
        used = 0
        if current is not None:
            used = current.get("tokens", 0) if isinstance(current, dict) else 0
        used += tokens
        # TTL of 86400 seconds (24 hours) for daily budget keys
        await self._cache.set(budget_key, {"tokens": used}, ttl=86400)

    @staticmethod
    def _cache_key(system: str, user: str, stage: str, tenant_id: str = "") -> str:
        content_hash = hashlib.sha256((system + user).encode()).hexdigest()[:32]
        return f"ai:v1:{stage}:{tenant_id}:{content_hash}"

    @staticmethod
    def _default_ttl(stage: str) -> int:
        return {
            "summary": settings.cache_ttl_summary,
            "fp_detection": settings.cache_ttl_fp_detection,
            "remediation": settings.cache_ttl_remediation,
            "report": settings.cache_ttl_report,
            "priority": settings.cache_ttl_priority,
        }.get(stage, 3600)
