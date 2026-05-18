"""Minimal Crossref client used for optional online DOI verification."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class CrossrefWork:
    """Selected metadata returned by Crossref for a DOI."""

    doi: str
    title: str | None
    published_year: int | None


class CrossrefClient:
    """Small HTTP client for Crossref's public works API."""

    def __init__(self, mailto: str | None = None, timeout: float = 8.0) -> None:
        self.mailto = mailto
        self.timeout = timeout

    def lookup_doi(self, doi: str) -> CrossrefWork | None:
        """Return metadata for ``doi`` or ``None`` when Crossref has no match."""

        encoded = urllib.parse.quote(doi, safe="")
        url = f"https://api.crossref.org/works/{encoded}"
        if self.mailto:
            url = f"{url}?mailto={urllib.parse.quote(self.mailto)}"
        request = urllib.request.Request(url, headers={"User-Agent": self._user_agent()})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                if response.status != 200:
                    return None
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, TimeoutError, json.JSONDecodeError):
            return None

        message = payload.get("message", {})
        titles = message.get("title") or []
        year = _extract_year(message)
        return CrossrefWork(doi=message.get("DOI", doi), title=titles[0] if titles else None, published_year=year)

    def _user_agent(self) -> str:
        base = "reference-checker/0.1.0 (https://example.invalid/reference-checker)"
        if self.mailto:
            return f"{base} mailto:{self.mailto}"
        return base


def _extract_year(message: dict) -> int | None:
    for key in ("published-print", "published-online", "published", "created"):
        date_parts = message.get(key, {}).get("date-parts")
        if date_parts and date_parts[0]:
            return int(date_parts[0][0])
    return None
