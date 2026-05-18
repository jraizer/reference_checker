"""Command line interface for reference-checker."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from reference_checker.models import Severity
from reference_checker.parser import read_references_from_paths
from reference_checker.validator import validate_references


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reference-checker",
        description="Valida listas de referências bibliográficas de textos científicos.",
    )
    parser.add_argument("files", nargs="*", help="Arquivos UTF-8 com referências. Se omitido, lê da entrada padrão.")
    parser.add_argument("--online", action="store_true", help="Confirma DOIs na Crossref quando houver conexão.")
    parser.add_argument("--mailto", help="E-mail enviado no User-Agent da Crossref, recomendado para uso online.")
    parser.add_argument("--json", action="store_true", help="Emite o relatório em JSON.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Retorna código 1 também quando houver avisos.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = read_references_from_paths(args.files) if args.files else sys.stdin.read()
    reports = validate_references(text, check_online=args.online, mailto=args.mailto)

    if args.json:
        print(json.dumps([_report_to_dict(report) for report in reports], ensure_ascii=False, indent=2))
    else:
        _print_human_report(reports)

    has_error = any(issue.severity == Severity.ERROR for report in reports for issue in report.issues)
    has_warning = any(issue.severity == Severity.WARNING for report in reports for issue in report.issues)
    return 1 if has_error or (args.fail_on_warning and has_warning) else 0


def _report_to_dict(report):
    payload = asdict(report)
    payload["issues"] = [{**issue, "severity": issue["severity"].value} for issue in payload["issues"]]
    return payload


def _print_human_report(reports) -> None:
    if not reports:
        print("Nenhuma referência encontrada.")
        return
    for report in reports:
        status = "OK" if report.is_valid else "REVISAR"
        print(f"[{report.index}] {status}: {report.raw}")
        for issue in report.issues:
            print(f"  - {issue.severity.value.upper()} {issue.code}: {issue.message}")
        if report.crossref_title:
            print(f"  - Crossref: {report.crossref_title}")


if __name__ == "__main__":
    raise SystemExit(main())
