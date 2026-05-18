"""Bibliographic reference validation rules."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date

from reference_checker.crossref import CrossrefClient
from reference_checker.models import Issue, ReferenceReport, Severity
from reference_checker.parser import normalize_for_duplicate_detection, split_references

DOI_RE = re.compile(r"\b(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.IGNORECASE)
URL_RE = re.compile(r"\bhttps?://[^\s<>\"]+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(18\d{2}|19\d{2}|20\d{2})\b")
AUTHOR_YEAR_RE = re.compile(r"^[A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇÑ][\wÁÀÂÃÉÈÊÍÓÔÕÚÇÑ'’-]+(?:,\s*[A-Z](?:\.|\w+))*")
MIN_REFERENCE_LENGTH = 25


def validate_references(
    references: str | Sequence[str],
    *,
    check_online: bool = False,
    mailto: str | None = None,
) -> list[ReferenceReport]:
    """Validate a bibliography list and return one report per reference.

    ``references`` may be a raw bibliography block or a pre-split sequence of
    references. Offline checks cover structure, DOI/URL syntax, year plausibility,
    duplicate entries, and missing citation elements. Online checks use Crossref
    to confirm DOI existence and compare the publication year when available.
    """

    entries = split_references(references) if isinstance(references, str) else [item.strip() for item in references if item.strip()]
    reports = [_validate_single(index, raw) for index, raw in enumerate(entries, start=1)]
    _mark_duplicates(reports)

    if check_online:
        client = CrossrefClient(mailto=mailto)
        for report in reports:
            _check_crossref(report, client)

    return reports


def _validate_single(index: int, raw: str) -> ReferenceReport:
    report = ReferenceReport(index=index, raw=raw)
    doi_match = DOI_RE.search(raw)
    url_match = URL_RE.search(raw)
    years = [int(match.group(1)) for match in YEAR_RE.finditer(raw)]

    report.doi = _clean_doi(doi_match.group(1)) if doi_match else None
    report.url = url_match.group(0).rstrip(".,;)") if url_match else None
    report.year = years[-1] if years else None

    if len(raw) < MIN_REFERENCE_LENGTH:
        report.issues.append(Issue("short_reference", "A referência parece curta demais para uma citação científica completa."))

    if not AUTHOR_YEAR_RE.search(raw):
        report.issues.append(Issue("missing_author_start", "Não foi possível identificar autores no início da referência."))

    if report.year is None:
        report.issues.append(Issue("missing_year", "Não foi encontrado um ano de publicação."))
    elif report.year > date.today().year + 1:
        report.issues.append(Issue("future_year", "O ano de publicação está no futuro.", Severity.ERROR))

    if report.doi is None and report.url is None:
        report.issues.append(Issue("missing_locator", "Informe DOI ou URL quando disponível para facilitar a verificação."))

    if report.doi and not _looks_like_valid_doi(report.doi):
        report.issues.append(Issue("invalid_doi", "O DOI encontrado não segue o formato esperado.", Severity.ERROR))

    if report.url and " " in report.url:
        report.issues.append(Issue("invalid_url", "A URL contém espaços e provavelmente está quebrada.", Severity.ERROR))

    if _has_title_like_segment(raw):
        report.issues.append(Issue("title_detected", "Título detectado.", Severity.INFO))
    else:
        report.issues.append(Issue("missing_title", "Não foi possível identificar um título de artigo/livro."))

    return report


def _mark_duplicates(reports: list[ReferenceReport]) -> None:
    seen: dict[str, int] = {}
    doi_seen: dict[str, int] = {}
    for report in reports:
        duplicate_of = None
        if report.doi:
            duplicate_of = doi_seen.get(report.doi.casefold())
            doi_seen.setdefault(report.doi.casefold(), report.index)
        key = normalize_for_duplicate_detection(report.raw)
        duplicate_of = duplicate_of or seen.get(key)
        seen.setdefault(key, report.index)
        if duplicate_of:
            report.duplicate_of = duplicate_of
            report.issues.append(Issue("duplicate", f"Possível duplicata da referência {duplicate_of}.", Severity.ERROR))


def _check_crossref(report: ReferenceReport, client: CrossrefClient) -> None:
    if not report.doi:
        return
    work = client.lookup_doi(report.doi)
    if work is None:
        report.issues.append(Issue("doi_not_found", "O DOI não foi encontrado na Crossref.", Severity.ERROR))
        return
    report.crossref_title = work.title
    if work.published_year and report.year and abs(work.published_year - report.year) > 1:
        report.issues.append(
            Issue(
                "year_mismatch",
                f"Ano informado ({report.year}) difere do ano retornado pela Crossref ({work.published_year}).",
            )
        )
    else:
        report.issues.append(Issue("doi_confirmed", "DOI confirmado na Crossref.", Severity.INFO))


def _clean_doi(doi: str) -> str:
    return doi.rstrip(".,;)").lower()


def _looks_like_valid_doi(doi: str) -> bool:
    return bool(re.fullmatch(r"10\.\d{4,9}/\S+", doi)) and len(doi.split("/", 1)[1]) >= 2


def _has_title_like_segment(reference: str) -> bool:
    segments = [segment.strip() for segment in re.split(r"\.\s+", reference) if segment.strip()]
    if len(segments) < 2:
        return False
    for segment in segments[1:]:
        words = re.findall(r"\w+", segment, flags=re.UNICODE)
        if 3 <= len(words) <= 35 and not DOI_RE.search(segment) and not URL_RE.search(segment):
            return True
    return False
