from __future__ import annotations

import re
from pathlib import Path

import yaml

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_prompt(path: Path) -> tuple[str, dict]:
    raw = path.read_text(encoding="utf-8")
    metadata: dict = {}

    m = _FRONTMATTER_RE.match(raw)
    if m:
        metadata = yaml.safe_load(m.group(1)) or {}
        raw = raw[m.end():]

    return raw.strip(), metadata
