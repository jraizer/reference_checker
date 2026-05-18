"""Parsing helpers for reference lists."""

from __future__ import annotations

import re
from collections.abc import Iterable

_NUMBERED_ITEM_RE = re.compile(r"^\s*(?:\[?\d+\]?|\d+\.)\s*[-.)]?\s*")
_BLANK_LINE_RE = re.compile(r"\n\s*\n", re.MULTILINE)


def split_references(text: str) -> list[str]:
    """Split a bibliography block into individual references.

    The splitter supports the most common formats used in manuscripts:
    one reference per line, numbered lists (``[1]`` or ``1.``), and blank-line
    separated entries. Wrapped continuation lines are joined to the previous
    reference when they do not look like a new numbered item.
    """

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    if _BLANK_LINE_RE.search(normalized):
        chunks = [chunk.strip() for chunk in _BLANK_LINE_RE.split(normalized)]
        return [_NUMBERED_ITEM_RE.sub("", chunk).replace("\n", " ").strip() for chunk in chunks if chunk.strip()]

    references: list[str] = []
    current: list[str] = []
    for line in normalized.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        starts_new = bool(_NUMBERED_ITEM_RE.match(stripped))
        if starts_new and current:
            references.append(" ".join(current).strip())
            current = []
        current.append(_NUMBERED_ITEM_RE.sub("", stripped).strip())

    if current:
        references.append(" ".join(current).strip())

    if len(references) == 1:
        simple_lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        if len(simple_lines) > 1 and all(not line.startswith((" ", "\t")) for line in normalized.split("\n")):
            return simple_lines

    return references


def normalize_for_duplicate_detection(reference: str) -> str:
    """Return a normalized key useful for duplicate detection."""

    lowered = reference.casefold()
    lowered = re.sub(r"https?://\S+", "", lowered)
    lowered = re.sub(r"doi:\s*|https?://(?:dx\.)?doi\.org/", "", lowered)
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def read_references_from_paths(paths: Iterable[str]) -> str:
    """Read and concatenate reference text from one or more UTF-8 files."""

    contents: list[str] = []
    for path in paths:
        with open(path, encoding="utf-8") as handle:
            contents.append(handle.read())
    return "\n\n".join(contents)
