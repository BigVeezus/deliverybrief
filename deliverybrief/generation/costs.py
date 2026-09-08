from __future__ import annotations

import math
import os

from deliverybrief.models import EvidenceItem, ProjectConfig, ReportingPeriod, UsageRecord

from .schema import MAX_OUTPUT_TOKENS, request_text, rough_token_count


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    if model in {"claude-haiku-4-5", "claude-haiku-4-5-20251001"}:
        input_rate = float(os.getenv("ANTHROPIC_HAIKU_INPUT_PER_MTOK", "1"))
        output_rate = float(os.getenv("ANTHROPIC_HAIKU_OUTPUT_PER_MTOK", "5"))
    elif model == os.getenv("ANTHROPIC_PRICED_MODEL"):
        input_rate = float(os.getenv("ANTHROPIC_MODEL_INPUT_PER_MTOK", "nan"))
        output_rate = float(os.getenv("ANTHROPIC_MODEL_OUTPUT_PER_MTOK", "nan"))
    else:
        return None
    if not all(math.isfinite(rate) and rate > 0 for rate in (input_rate, output_rate)):
        return None
    return round((input_tokens * input_rate + output_tokens * output_rate) / 1_000_000, 6)


def estimate_generation_cost(
    model: str,
    project: ProjectConfig,
    period: ReportingPeriod,
    evidence: list[EvidenceItem],
) -> UsageRecord:
    input_tokens = rough_token_count(request_text(project, period, evidence))
    return UsageRecord(
        input_tokens=input_tokens,
        output_tokens=MAX_OUTPUT_TOKENS,
        estimated_cost_usd=estimate_cost(model, input_tokens, MAX_OUTPUT_TOKENS),
    )
