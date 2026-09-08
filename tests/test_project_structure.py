from __future__ import annotations

import importlib
from pathlib import Path


def test_runtime_layers_have_named_packages() -> None:
    root = Path("deliverybrief")
    expected = [
        root / "approval" / "service.py",
        root / "exporting" / "service.py",
        root / "exporting" / "serializers.py",
        root / "generation" / "anthropic.py",
        root / "generation" / "demo.py",
        root / "generation" / "schema.py",
        root / "persistence" / "sqlite.py",
        root / "services" / "report_workflow.py",
        root / "ui" / "app.py",
    ]

    missing = [str(path) for path in expected if not path.exists()]

    assert missing == []


def test_legacy_imports_still_resolve() -> None:
    generator = importlib.import_module("deliverybrief.generator")
    exports = importlib.import_module("deliverybrief.exports")
    storage = importlib.import_module("deliverybrief.storage")
    workflow = importlib.import_module("deliverybrief.workflow")

    assert hasattr(generator, "DemoReportGenerator")
    assert hasattr(exports, "approved_exports")
    assert hasattr(storage, "RunStore")
    assert hasattr(workflow, "generate_and_record")


def test_scripts_are_import_safe() -> None:
    for module in (
        "scripts.apply_quality_reviews",
        "scripts.build_sample_documents",
        "scripts.build_submission_documents",
        "scripts.summarize_reliability",
    ):
        importlib.import_module(module)
