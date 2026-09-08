from __future__ import annotations

import json
import time
from typing import Any, cast

from anthropic import Anthropic, APIConnectionError, APIStatusError

from deliverybrief.budget import BudgetLedger
from deliverybrief.intake import normalize_evidence
from deliverybrief.models import (
    EvidenceItem,
    GenerationResult,
    ProjectConfig,
    ReportingPeriod,
    UsageRecord,
    WeeklyReport,
)
from deliverybrief.privacy import redact, safe_evidence

from .base import ReportGenerationError
from .costs import estimate_cost, estimate_generation_cost
from .schema import (
    ANTHROPIC_SYSTEM_PROMPT,
    ANTHROPIC_USER_PREFIX,
    MAX_INPUT_TOKENS,
    MAX_OUTPUT_TOKENS,
    anthropic_schema,
    report_prompt,
)


class AnthropicReportGenerator:
    kind = "anthropic"

    def __init__(self, api_key: str, model: str, budget: BudgetLedger | None = None) -> None:
        self.client = Anthropic(api_key=api_key, max_retries=0, timeout=30.0)
        self.model = model
        self.budget = budget

    def generate(
        self,
        project: ProjectConfig,
        period: ReportingPeriod,
        evidence: list[EvidenceItem],
    ) -> GenerationResult:
        if not evidence:
            raise ReportGenerationError("No evidence was supplied")
        evidence = safe_evidence(normalize_evidence(evidence))
        estimate = estimate_generation_cost(self.model, project, period, evidence)
        if estimate.input_tokens > MAX_INPUT_TOKENS:
            raise ReportGenerationError("Evidence exceeds the input limit. Select fewer notes.")
        if self.budget is None:
            raise ReportGenerationError(
                "An explicit workflow budget is required. No request was sent."
            )
        prompt = report_prompt(project, period, evidence)
        started = time.perf_counter()
        response = None
        attempts = 0
        try:
            for attempt in range(3):
                self.budget.reserve(estimate.estimated_cost_usd)
                attempts += 1
                try:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=MAX_OUTPUT_TOKENS,
                        system=ANTHROPIC_SYSTEM_PROMPT,
                        messages=[
                            {
                                "role": "user",
                                "content": ANTHROPIC_USER_PREFIX
                                + json.dumps(prompt, ensure_ascii=True),
                            }
                        ],
                        output_config={
                            "format": {
                                "type": "json_schema",
                                "schema": anthropic_schema(WeeklyReport.model_json_schema()),
                            }
                        },
                    )
                    break
                except (APIConnectionError, APIStatusError) as error:
                    transient = isinstance(error, APIConnectionError) or (
                        isinstance(error, APIStatusError)
                        and (error.status_code == 429 or error.status_code >= 500)
                    )
                    if not transient or attempt == 2:
                        raise
                    delay = float(2**attempt)
                    if isinstance(error, APIStatusError):
                        try:
                            delay = max(
                                delay, float(error.response.headers.get("retry-after", "0"))
                            )
                        except ValueError:
                            pass
                    if delay > 10:
                        raise ReportGenerationError(
                            "Provider requested a longer wait. Try later."
                        ) from error
                    time.sleep(delay)
            if response is None or response.stop_reason != "end_turn":
                raise ReportGenerationError(
                    "Model output was truncated or refused. Narrow the input."
                )
            text_blocks: list[str] = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text_blocks.append(str(cast(Any, block).text))
            text = "".join(text_blocks)
            report = WeeklyReport.model_validate_json(text)
        except ReportGenerationError as error:
            detail = safe_detail(str(error))
            raise ReportGenerationError(f"{detail} No demo fallback was used.") from error
        except Exception as error:
            detail = " ".join(str(error).split())
            detail = safe_detail(detail)
            raise ReportGenerationError(
                "Claude returned output that did not match the required report structure. "
                f"Failure type: {type(error).__name__}. Detail: {detail}. "
                "No demo fallback was used."
            ) from error
        latency_ms = round((time.perf_counter() - started) * 1000)
        input_tokens = int(getattr(response.usage, "input_tokens", 0))
        output_tokens = int(getattr(response.usage, "output_tokens", 0))
        return GenerationResult(
            report=report,
            model=self.model,
            latency_ms=latency_ms,
            usage=UsageRecord(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=estimate_cost(self.model, input_tokens, output_tokens),
            ),
            generator="anthropic",
            attempts=attempts,
        )


def safe_detail(text: str, limit: int = 500) -> str:
    cleaned = redact(text)
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")
