from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from deliverybrief.models import TraceStatus, WorkflowTraceStep
from deliverybrief.privacy import redact

PRIVATE_URL_RE = re.compile(
    r"https?://(?:github\.com|drive\.google\.com|docs\.google\.com)/[^\s\"')]+",
    re.IGNORECASE,
)


def _clean(value: Any) -> Any:
    if value is None:
        return None
    try:
        redacted = redact(json.dumps(value, default=str))
        return json.loads(PRIVATE_URL_RE.sub("[REDACTED URL]", redacted))
    except Exception:
        return PRIVATE_URL_RE.sub("[REDACTED URL]", redact(str(value)))


def _latency_ms(started_at: datetime, ended_at: datetime) -> int:
    return max(0, int((ended_at - started_at).total_seconds() * 1000))


def start_step(
    step_name: str,
    tool_name: str,
    reason: str,
    *,
    attempts: int = 1,
    input_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowTraceStep:
    return WorkflowTraceStep(
        step_name=step_name,
        tool_name=tool_name,
        status="started",
        reason=PRIVATE_URL_RE.sub("[REDACTED URL]", redact(reason)),
        started_at=datetime.now(UTC),
        attempts=attempts,
        input_count=input_count,
        metadata=_clean(metadata or {}),
    )


def finish_step(
    step: WorkflowTraceStep,
    *,
    output_count: int | None = None,
    reason: str | None = None,
    attempts: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowTraceStep:
    ended_at = datetime.now(UTC)
    updated = step.model_copy(deep=True)
    updated.status = "success"
    updated.ended_at = ended_at
    updated.latency_ms = _latency_ms(step.started_at, ended_at)
    updated.output_count = output_count
    if reason is not None:
        updated.reason = PRIVATE_URL_RE.sub("[REDACTED URL]", redact(reason))
    if attempts is not None:
        updated.attempts = attempts
    if metadata:
        updated.metadata.update(_clean(metadata))
    return updated


def fail_step(
    step: WorkflowTraceStep,
    error: BaseException | str,
    *,
    status: TraceStatus = "failed",
    reason: str | None = None,
    output_count: int | None = None,
) -> WorkflowTraceStep:
    ended_at = datetime.now(UTC)
    updated = step.model_copy(deep=True)
    updated.status = "blocked" if status == "blocked" else "failed"
    updated.ended_at = ended_at
    updated.latency_ms = _latency_ms(step.started_at, ended_at)
    if reason is not None:
        updated.reason = PRIVATE_URL_RE.sub("[REDACTED URL]", redact(reason))
    updated.output_count = output_count
    updated.error = PRIVATE_URL_RE.sub("[REDACTED URL]", redact(str(error)))
    return updated


def skip_step(
    step_name: str,
    tool_name: str,
    reason: str,
    *,
    input_count: int | None = None,
    output_count: int | None = 0,
    metadata: dict[str, Any] | None = None,
) -> WorkflowTraceStep:
    now = datetime.now(UTC)
    return WorkflowTraceStep(
        step_name=step_name,
        tool_name=tool_name,
        status="skipped",
        reason=PRIVATE_URL_RE.sub("[REDACTED URL]", redact(reason)),
        started_at=now,
        ended_at=now,
        latency_ms=0,
        input_count=input_count,
        output_count=output_count,
        metadata=_clean(metadata or {}),
    )


def instant_step(
    step_name: str,
    tool_name: str,
    status: TraceStatus,
    reason: str,
    *,
    attempts: int = 1,
    input_count: int | None = None,
    output_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowTraceStep:
    now = datetime.now(UTC)
    return WorkflowTraceStep(
        step_name=step_name,
        tool_name=tool_name,
        status=status,
        reason=PRIVATE_URL_RE.sub("[REDACTED URL]", redact(reason)),
        started_at=now,
        ended_at=now,
        latency_ms=0,
        attempts=attempts,
        input_count=input_count,
        output_count=output_count,
        metadata=_clean(metadata or {}),
    )
