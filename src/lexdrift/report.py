"""Turn check results into something a human (or a CI job) can read."""

from __future__ import annotations

import json
from typing import Sequence

from .model import Feature, LibraryReport, Status

SYMBOLS = {
    Status.OK: "ok",
    Status.UNSTYLED: "MISSING",
    Status.MISCATEGORISED: "wrong",
    Status.ERROR_TOKEN: "ERROR",
    Status.NOT_FOUND: "n/a",
    Status.NOT_APPLICABLE: "style",
    Status.SKIPPED: "-",
}

MARKDOWN_SYMBOLS = {
    Status.OK: "✅",
    Status.UNSTYLED: "❌",
    Status.MISCATEGORISED: "🟡",
    Status.ERROR_TOKEN: "🛑",
    Status.NOT_FOUND: "·",
    Status.NOT_APPLICABLE: "◦",
    Status.SKIPPED: "–",
}


def _matrix(reports: Sequence[LibraryReport]) -> tuple[list[Feature], dict[tuple[str, str], Status]]:
    features: list[Feature] = []
    seen: set[str] = set()
    cells: dict[tuple[str, str], Status] = {}
    for report in reports:
        for result in report.results:
            if result.feature.id not in seen:
                seen.add(result.feature.id)
                features.append(result.feature)
            cells[(report.library, result.feature.id)] = result.status
    return features, cells


def render_table(reports: Sequence[LibraryReport]) -> str:
    """Plain text report for the terminal."""
    lines: list[str] = []
    libraries = [report for report in reports if report.available]
    unavailable = [report for report in reports if not report.available]

    for report in libraries:
        checked = len(report.checked)
        percent = f"{report.coverage * 100:5.1f}%"
        extra = f", {len(report.advisories)} styled differently" if report.advisories else ""
        lines.append(
            f"{report.library:<14} {report.version:<10} {percent}  "
            f"({report.recognised}/{checked} recognised{extra})"
        )
    for report in unavailable:
        lines.append(f"{report.library:<14} {'':<10}    n/a  ({report.unavailable_reason})")

    features, cells = _matrix(reports)
    if features:
        width = max(len(feature.id) for feature in features) + 2
        header = "feature".ljust(width) + "  ".join(f"{report.library:>12}" for report in libraries)
        lines.extend(["", header, "-" * len(header)])
        current_language = None
        for feature in features:
            if feature.language != current_language:
                current_language = feature.language
                lines.append(f"[{current_language}]")
            row = feature.id.ljust(width)
            row += "  ".join(
                f"{SYMBOLS[cells.get((report.library, feature.id), Status.SKIPPED)]:>12}"
                for report in libraries
            )
            lines.append(row)

    gaps = [result for report in reports for result in report.gaps]
    if gaps:
        lines.extend(["", f"{len(gaps)} unrecognised feature(s):"])
        for result in gaps:
            feature = result.feature
            since = f" since {feature.since}" if feature.since else ""
            contextual = " [contextual keyword]" if feature.contextual else ""
            lines.append(
                f"  {result.library}: {feature.language} {feature.name}{since}"
                f" -- {result.detail}{contextual}"
            )

    advisories = [result for report in reports for result in report.advisories]
    if advisories:
        lines.extend(["", f"{len(advisories)} styled, but not as the corpus expected:"])
        for result in advisories:
            feature = result.feature
            lines.append(
                f"  {result.library}: {feature.language} {feature.name} -- {result.detail}"
            )
    return "\n".join(lines)


def render_markdown(reports: Sequence[LibraryReport]) -> str:
    """Markdown report, suitable for pasting into an issue or a README."""
    libraries = [report for report in reports if report.available]
    features, cells = _matrix(reports)
    lines = ["# lexdrift report", ""]

    lines.append("| library | version | coverage | gaps |")
    lines.append("| --- | --- | --- | --- |")
    for report in libraries:
        lines.append(
            f"| [{report.library}]({_url(report.library)}) | `{report.version}` | "
            f"{report.coverage * 100:.0f}% ({report.recognised}/{len(report.checked)}) | "
            f"{len(report.gaps)} |"
        )
    for report in reports:
        if not report.available:
            lines.append(f"| {report.library} | – | not checked | {report.unavailable_reason} |")

    lines.extend(["", "✅ recognised · ❌ plain text · 🟡 unexpected category · 🛑 error token · ◦ library does not style this kind of token · · not locatable · – no grammar", ""])

    current_language = None
    for feature in features:
        if feature.language != current_language:
            current_language = feature.language
            lines.extend(["", f"## {current_language}", ""])
            lines.append("| feature | since | " + " | ".join(r.library for r in libraries) + " |")
            lines.append("| --- | --- | " + " | ".join("---" for _ in libraries) + " |")
        name = f"[{feature.name}]({feature.spec})" if feature.spec else feature.name
        cells_row = " | ".join(
            MARKDOWN_SYMBOLS[cells.get((report.library, feature.id), Status.SKIPPED)]
            for report in libraries
        )
        lines.append(f"| {name} | {feature.since or '–'} | {cells_row} |")

    return "\n".join(lines) + "\n"


def _url(library: str) -> str:
    from .adapters import get_adapter

    try:
        return get_adapter(library).url
    except Exception:  # pragma: no cover - only for unknown libraries
        return ""


def render_json(reports: Sequence[LibraryReport]) -> str:
    payload = []
    for report in reports:
        payload.append(
            {
                "library": report.library,
                "version": report.version,
                "available": report.available,
                "unavailable_reason": report.unavailable_reason,
                "coverage": round(report.coverage, 4),
                "results": [
                    {
                        "feature": result.feature.id,
                        "language": result.feature.language,
                        "name": result.feature.name,
                        "since": result.feature.since,
                        "status": result.status.value,
                        "detail": result.detail,
                        "category": result.found_category,
                        "raw_token": result.found_raw,
                        "contextual": result.feature.contextual,
                    }
                    for result in report.results
                ],
            }
        )
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def render(reports: Sequence[LibraryReport], fmt: str) -> str:
    if fmt == "markdown":
        return render_markdown(reports)
    if fmt == "json":
        return render_json(reports)
    return render_table(reports)
