"""Data models used by the reference checker."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Severity levels emitted during reference validation."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Issue:
    """A single validation issue for one bibliographic reference."""

    code: str
    message: str
    severity: Severity = Severity.WARNING


@dataclass
class ReferenceReport:
    """Validation result for one bibliographic reference."""

    index: int
    raw: str
    issues: list[Issue] = field(default_factory=list)
    doi: str | None = None
    url: str | None = None
    year: int | None = None
    duplicate_of: int | None = None
    crossref_title: str | None = None

    @property
    def is_valid(self) -> bool:
        """Return true when the reference has no warning or error issues."""

        return all(issue.severity == Severity.INFO for issue in self.issues)
