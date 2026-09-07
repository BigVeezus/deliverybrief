from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from deliverybrief.models import EvidenceItem, ReportingPeriod, SourceType


class GitHubIntegrationError(RuntimeError):
    """Raised when GitHub evidence cannot be collected safely."""


def _is_transient(error: BaseException) -> bool:
    if isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    return isinstance(error, httpx.HTTPStatusError) and (
        error.response.status_code == 429 or error.response.status_code >= 500
    )


class GitHubEvidenceClient:
    def __init__(self, token: str, repository: str, timeout_seconds: float = 15.0) -> None:
        if repository.count("/") != 1:
            raise ValueError("GitHub repository must use owner/repository format")
        self.repository = repository
        self.client = httpx.Client(
            base_url="https://api.github.com",
            timeout=timeout_seconds,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "DeliveryBrief/0.1",
            },
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> GitHubEvidenceClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception(_is_transient),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any]) -> httpx.Response:
        response = self.client.get(path, params=params)
        if response.status_code in {401, 403, 404}:
            raise GitHubIntegrationError(
                "GitHub denied access. Check the repository name and read-only token permissions."
            )
        response.raise_for_status()
        return response

    def _paginate(self, path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        page = 1
        records: list[dict[str, Any]] = []
        while True:
            response = self._get(path, {**params, "per_page": 100, "page": page})
            batch = response.json()
            if not isinstance(batch, list):
                raise GitHubIntegrationError("GitHub returned an unexpected response shape")
            records.extend(batch)
            if len(batch) < 100:
                return records
            page += 1

    def collect(self, period: ReportingPeriod) -> list[EvidenceItem]:
        owner, repo = self.repository.split("/", maxsplit=1)
        since = datetime.combine(period.start, datetime.min.time(), tzinfo=UTC).isoformat()
        until = datetime.combine(period.end, datetime.max.time(), tzinfo=UTC)

        issues = self._paginate(
            f"/repos/{owner}/{repo}/issues",
            {"state": "all", "since": since, "sort": "updated", "direction": "desc"},
        )
        commits = self._paginate(
            f"/repos/{owner}/{repo}/commits",
            {"since": since, "until": until.isoformat()},
        )

        items: list[EvidenceItem] = []
        for record in issues:
            timestamp_raw = (
                record.get("merged_at") or record.get("closed_at") or record.get("updated_at")
            )
            if not timestamp_raw:
                continue
            timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            if not period.start <= timestamp.date() <= period.end:
                continue
            is_pr = "pull_request" in record
            kind = "pull_request" if is_pr else "issue"
            prefix = "PR" if is_pr else "ISSUE"
            number = record["number"]
            labels = [label.get("name", "") for label in record.get("labels", [])]
            body = (record.get("body") or "No description supplied").strip()
            state = "merged" if record.get("pull_request", {}).get("merged_at") else record["state"]
            items.append(
                EvidenceItem(
                    evidence_id=f"GH-{prefix}-{number}",
                    source=SourceType.GITHUB,
                    title=f"{prefix} {number} {record['title']}",
                    content=f"State: {state}. Labels: {', '.join(labels) or 'none'}. {body}",
                    occurred_at=timestamp,
                    source_url=record.get("html_url"),
                    author_alias=(record.get("user") or {}).get("login"),
                    metadata={"kind": kind, "state": state, "number": number, "labels": labels},
                )
            )

        for record in commits:
            commit = record.get("commit") or {}
            author = commit.get("author") or {}
            timestamp_raw = author.get("date")
            if not timestamp_raw:
                continue
            timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            sha = str(record.get("sha", ""))
            items.append(
                EvidenceItem(
                    evidence_id=f"GH-COMMIT-{sha[:8].upper()}",
                    source=SourceType.GITHUB,
                    title=f"Commit {sha[:8]}",
                    content=str(commit.get("message") or "No commit message"),
                    occurred_at=timestamp,
                    source_url=record.get("html_url"),
                    author_alias=author.get("name"),
                    metadata={"kind": "commit", "sha": sha},
                )
            )

        deduplicated = {item.evidence_id: item for item in items}
        return sorted(deduplicated.values(), key=lambda item: item.occurred_at)
