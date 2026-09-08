from __future__ import annotations

import importlib
import sys

if "deliverybrief.ui.app" in sys.modules:
    importlib.reload(sys.modules["deliverybrief.ui.app"])
else:
    importlib.import_module("deliverybrief.ui.app")
