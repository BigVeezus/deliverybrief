"""Conservative detectors, not a general confidentiality classifier."""

from __future__ import annotations

import re

from deliverybrief.models import EvidenceItem
from deliverybrief.validator import EMAIL_RE, ISO_DATE_RE, PHONE_RE, SECRET_PATTERNS


def redact(text: str) -> str:
    text = re.sub(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
        r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "[REDACTED PRIVATE KEY]",
        text,
        flags=re.DOTALL,
    )
    for pattern in SECRET_PATTERNS.values():
        text = pattern.sub("[REDACTED SECRET]", text)
    text = EMAIL_RE.sub("[REDACTED EMAIL]", text)
    # Preserve ISO dates while checking phone patterns.
    dates: list[str] = []

    def protect(match: re.Match[str]) -> str:
        dates.append(match.group())
        return f"DATEPLACEHOLDER{chr(65 + len(dates) - 1)}END"

    text = ISO_DATE_RE.sub(protect, text)
    text = PHONE_RE.sub("[REDACTED PHONE]", text)
    for index, value in enumerate(dates):
        text = text.replace(f"DATEPLACEHOLDER{chr(65 + index)}END", value)
    return text


def safe_evidence(items: list[EvidenceItem]) -> list[EvidenceItem]:
    result = []
    for item in items:
        # Metadata can contain secrets too; scan the entire serialized record.
        cleaned = EvidenceItem.model_validate_json(redact(item.model_dump_json()))
        if cleaned != item:
            cleaned.metadata["redacted"] = True
        result.append(cleaned)
    return result
