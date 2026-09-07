from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

from deliverybrief.models import ProjectConfig


@dataclass(frozen=True)
class Settings:
    mode: str
    anthropic_api_key: str | None
    primary_model: str
    quality_model: str
    github_token: str | None
    google_service_account_json: str | None
    database_path: Path
    repository_url: str
    project: ProjectConfig

    @property
    def is_demo(self) -> bool:
        return self.mode == "demo"

    def live_readiness_errors(self) -> list[str]:
        required = {
            "ANTHROPIC_API_KEY": self.anthropic_api_key,
            "GITHUB_TOKEN": self.github_token,
            "GOOGLE_SERVICE_ACCOUNT_JSON": self.google_service_account_json,
            "GOOGLE_DRIVE_FOLDER_ID": self.project.google_drive_folder_id,
        }
        return [f"{name} is not configured" for name, value in required.items() if not value]


def load_settings() -> Settings:
    load_dotenv()
    repository = os.getenv("GITHUB_REPOSITORY", "deliverybrief/demo")
    drive_folder = os.getenv("GOOGLE_DRIVE_FOLDER_ID") or None
    project = ProjectConfig(
        github_repository=repository,
        google_drive_folder_id=drive_folder,
        timezone=os.getenv("DELIVERYBRIEF_TIMEZONE", "Africa/Lagos"),
    )
    return Settings(
        mode=os.getenv("DELIVERYBRIEF_MODE", "demo").strip().lower(),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        primary_model=os.getenv("ANTHROPIC_PRIMARY_MODEL", "claude-haiku-4-5"),
        quality_model=os.getenv("ANTHROPIC_QUALITY_MODEL", "claude-sonnet-5"),
        github_token=os.getenv("GITHUB_TOKEN") or None,
        google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON") or None,
        database_path=Path(os.getenv("DELIVERYBRIEF_DB_PATH", "deliverybrief.db")),
        repository_url=os.getenv(
            "DELIVERYBRIEF_REPOSITORY_URL",
            "https://github.com/BigVeezus/deliverybrief",
        ).strip(),
        project=project,
    )


def parse_service_account_json(raw_or_path: str) -> dict[str, object]:
    raw: object
    if raw_or_path.lstrip().startswith("{"):
        raw = json.loads(raw_or_path)
    else:
        raw = json.loads(Path(raw_or_path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Google service account JSON must contain an object")
    return cast(dict[str, object], raw)
