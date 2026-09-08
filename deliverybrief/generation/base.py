from __future__ import annotations

from typing import Protocol

from deliverybrief.models import EvidenceItem, GenerationResult, ProjectConfig, ReportingPeriod


class ReportGenerationError(RuntimeError):
    """Raised when report generation does not produce a usable structured result."""


class ReportGenerator(Protocol):
    def generate(
        self,
        project: ProjectConfig,
        period: ReportingPeriod,
        evidence: list[EvidenceItem],
    ) -> GenerationResult: ...
