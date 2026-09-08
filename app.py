from __future__ import annotations

import importlib
import sys

importlib.invalidate_caches()

stale_models = False
try:
    models = importlib.import_module("deliverybrief.models")
    stale_models = not hasattr(models, "ToolSelection")
except ImportError:
    stale_models = True

if stale_models and "pytest" not in sys.modules:
    for module_name in list(sys.modules):
        if module_name == "deliverybrief" or module_name.startswith("deliverybrief."):
            del sys.modules[module_name]

if "deliverybrief.ui.app" in sys.modules:
    importlib.reload(sys.modules["deliverybrief.ui.app"])
else:
    importlib.import_module("deliverybrief.ui.app")
