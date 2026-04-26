from __future__ import annotations

import re
from typing import Iterable, List


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def split_pipe_tags(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, float) and str(value) == "nan":
        return []
    raw = str(value).strip()
    if not raw:
        return []
    return [normalize_whitespace(part) for part in raw.split("|") if normalize_whitespace(part)]


def to_bullet_lines(items: Iterable[str]) -> str:
    cleaned = [normalize_whitespace(item) for item in items if normalize_whitespace(item)]
    return "\n".join(f"• {item}" for item in cleaned)
