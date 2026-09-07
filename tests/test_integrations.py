import httpx
import pytest

from deliverybrief.integrations.github import GitHubEvidenceClient
from deliverybrief.integrations.google_docs import GoogleDocsEvidenceClient


def test_github_retries_transient_failure() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(500, request=request)
        return httpx.Response(200, json=[], request=request)

    client = GitHubEvidenceClient("test-token", "owner/repo")
    client.client.close()
    client.client = httpx.Client(
        base_url="https://api.github.test", transport=httpx.MockTransport(handler)
    )
    try:
        response = client._get("/repos/owner/repo/issues", {})
    finally:
        client.close()

    assert response.status_code == 200
    assert attempts == 3


def test_github_does_not_retry_permission_failure() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(403, request=request)

    client = GitHubEvidenceClient("test-token", "owner/repo")
    client.client.close()
    client.client = httpx.Client(
        base_url="https://api.github.test", transport=httpx.MockTransport(handler)
    )
    try:
        with pytest.raises(RuntimeError, match="denied access"):
            client._get("/repos/owner/repo/issues", {})
    finally:
        client.close()

    assert attempts == 1


def test_google_document_text_extraction() -> None:
    document = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Delivery note\n"}},
                            {"textRun": {"content": "Second line"}},
                        ]
                    }
                }
            ]
        }
    }

    assert GoogleDocsEvidenceClient._extract_text(document) == "Delivery note\nSecond line"
