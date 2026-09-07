from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", "__pycache__", "output", ".mypy_cache", ".ruff_cache"}
SKIP_FILES = {
    Path("evaluation/cases/cases.json"),
    Path("scripts/check_secrets.py"),
    Path("tests/test_validator.py"),
}
PATTERNS = {
    "Anthropic API key": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"github_pat_[A-Za-z0-9_]{20,}|gh[opsu]_[A-Za-z0-9]{30,}"),
    "Google private key": re.compile(r"-----BEGIN PRIVATE KEY-----"),
}


def candidate_files() -> list[Path]:
    allowed_suffixes = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt"}
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.suffix in allowed_suffixes
        and not any(part in SKIP_PARTS for part in path.relative_to(ROOT).parts)
        and path.relative_to(ROOT) not in SKIP_FILES
    ]


def main() -> None:
    findings: list[str] = []
    for path in candidate_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: possible {label}")
    if findings:
        raise SystemExit("Secret scan failed:\n" + "\n".join(findings))
    print(f"Secret scan passed ({len(candidate_files())} text files checked).")


if __name__ == "__main__":
    main()
