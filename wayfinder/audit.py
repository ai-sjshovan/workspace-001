from __future__ import annotations

import json
import pathlib
from typing import Any

from .models import utc_now


def write_event(path: pathlib.Path, action: str, **fields: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": utc_now(), "action": action, **fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
