"""Load machine specifications from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_spec(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

