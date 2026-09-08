from __future__ import annotations

from dataclasses import dataclass

from deliverybrief.models import ToolSelection


@dataclass(frozen=True)
class ToolSelectorInput:
    mode: str
    github_repository: str | None = None
    github_token: str | None = None
    google_service_account_json: str | None = None
    google_drive_folder_id: str | None = None
    anthropic_api_key: str | None = None
    budget_usd: float | None = None
    has_upload: bool = False
    has_pasted_note: bool = False
    approved_snapshot_valid: bool = False


def select_tools(config: ToolSelectorInput) -> list[ToolSelection]:
    demo = config.mode == "demo"
    return [
        ToolSelection(
            tool_name="sample_evidence",
            category="source",
            selected=demo,
            reason="Demo mode uses bundled public-safe evidence."
            if demo
            else "Skipped because live mode uses configured sources.",
        ),
        _configured(
            "github_rest_api",
            "source",
            [
                ("GITHUB_REPOSITORY", config.github_repository),
                ("GITHUB_TOKEN", config.github_token),
            ],
            "GitHub token and repository are configured.",
        ),
        _configured(
            "google_drive_notes",
            "source",
            [
                ("GOOGLE_SERVICE_ACCOUNT_JSON", config.google_service_account_json),
                ("GOOGLE_DRIVE_FOLDER_ID", config.google_drive_folder_id),
            ],
            "Google Drive service account and folder are configured.",
        ),
        ToolSelection(
            tool_name="evidence_json_upload",
            category="source",
            selected=config.has_upload,
            reason="A JSON evidence upload was provided."
            if config.has_upload
            else "Skipped because no JSON upload was provided.",
        ),
        ToolSelection(
            tool_name="pasted_developer_note",
            category="source",
            selected=config.has_pasted_note,
            reason="A pasted developer note was provided."
            if config.has_pasted_note
            else "Skipped because no pasted note was provided.",
        ),
        ToolSelection(
            tool_name="deterministic_demo_generator",
            category="generation",
            selected=demo,
            reason="Demo mode keeps the public app free and credential-free."
            if demo
            else "Skipped because live mode uses the configured model.",
        ),
        _configured(
            "claude_structured_generation",
            "generation",
            [
                ("DELIVERYBRIEF_MODE=live", "yes" if config.mode == "live" else None),
                ("ANTHROPIC_API_KEY", config.anthropic_api_key),
                (
                    "DELIVERYBRIEF_BUDGET_USD",
                    str(config.budget_usd) if config.budget_usd and config.budget_usd > 0 else None,
                ),
            ],
            "Live mode, Anthropic key, and positive budget are configured.",
        ),
        ToolSelection(
            tool_name="approved_snapshot_exports",
            category="export",
            selected=config.approved_snapshot_valid,
            reason="An approved report and matching evidence snapshot are available."
            if config.approved_snapshot_valid
            else "Skipped until a matching approved snapshot exists.",
        ),
    ]


def _configured(
    tool_name: str,
    category: str,
    requirements: list[tuple[str, str | None]],
    selected_reason: str,
) -> ToolSelection:
    missing = [name for name, value in requirements if not value]
    return ToolSelection(
        tool_name=tool_name,
        category=category,
        selected=not missing,
        reason=selected_reason if not missing else "Missing required configuration.",
        missing_config=missing,
    )
