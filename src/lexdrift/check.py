"""Run the corpus against highlighters and classify what comes back."""

from __future__ import annotations

from typing import Iterable, Sequence

from .adapters import Adapter, AdapterUnavailable
from .model import ERROR, PLAIN, Feature, LibraryReport, Result, Status, Token


def _span_of(snippet: str, target: str, occurrence: int) -> tuple[int, int] | None:
    """Character range of the ``occurrence``-th ``target`` inside ``snippet``."""
    start = -1
    for _ in range(occurrence):
        start = snippet.find(target, start + 1)
        if start < 0:
            return None
    return start, start + len(target)


def _covering_tokens(tokens: Sequence[Token], span: tuple[int, int]) -> list[Token] | None:
    """Tokens that overlap ``span``, or None if the stream does not line up.

    Adapters return every character of the snippet, including whitespace, so
    the token offsets can be reconstructed by accumulation. If some adapter
    ever drops text, the offsets stop being meaningful and the caller falls
    back to matching on token text.
    """
    start, end = span
    offset = 0
    covering: list[Token] = []
    for token in tokens:
        token_start = offset
        offset += len(token.text)
        if token_start < end and offset > start:
            covering.append(token)
    if not covering:
        return None
    return covering


def _stream_matches(tokens: Sequence[Token], snippet: str) -> bool:
    return "".join(token.text for token in tokens) == snippet


def _fallback_tokens(tokens: Sequence[Token], target: str, occurrence: int) -> list[Token]:
    """Locate the target by token text when offsets are unusable."""
    seen = 0
    for token in tokens:
        if token.text.strip() == target:
            seen += 1
            if seen == occurrence:
                return [token]
    return [token for token in tokens if target in token.text]


def _classify(feature: Feature, library: str, covering: Sequence[Token]) -> Result:
    """Decide what a set of covering tokens says about the feature."""
    meaningful = [token for token in covering if token.text.strip()]
    if not meaningful:
        return Result(
            library=library,
            feature=feature,
            status=Status.NOT_FOUND,
            detail="no token covers the feature",
        )

    categories = [token.category for token in meaningful]
    plain = [token for token in meaningful if token.category == PLAIN]
    raw = "+".join(dict.fromkeys(token.raw or "plain" for token in meaningful))

    if len(plain) == len(meaningful):
        return Result(
            library=library,
            feature=feature,
            status=Status.UNSTYLED,
            detail="highlighted as plain text",
            found_category=PLAIN,
            found_raw=raw,
        )
    if plain:
        remainder = "".join(token.text for token in plain).strip()
        return Result(
            library=library,
            feature=feature,
            status=Status.UNSTYLED,
            detail=f"only partly recognised; {remainder[:24]!r} is plain text",
            found_category=PLAIN,
            found_raw=raw,
        )

    category = categories[0]
    if feature.expect and not any(item in feature.expect for item in categories):
        return Result(
            library=library,
            feature=feature,
            status=Status.MISCATEGORISED,
            detail=f"expected {'/'.join(feature.expect)}, got {'+'.join(dict.fromkeys(categories))}",
            found_category=category,
            found_raw=raw,
        )
    return Result(
        library=library,
        feature=feature,
        status=Status.OK,
        found_category=category,
        found_raw=raw,
    )


def check_feature(adapter: Adapter, feature: Feature) -> Result:
    """Check one feature against one library."""
    library = adapter.name
    try:
        if not adapter.supports(feature.language):
            return Result(
                library=library,
                feature=feature,
                status=Status.SKIPPED,
                detail=f"no grammar for {feature.language}",
            )
        tokens = adapter.tokenize(feature.language, feature.snippet)
    except AdapterUnavailable as exc:
        return Result(library=library, feature=feature, status=Status.SKIPPED, detail=str(exc))

    error_tokens = [token for token in tokens if token.category == ERROR and token.text.strip()]
    if error_tokens:
        sample = "".join(token.text for token in error_tokens)[:40]
        return Result(
            library=library,
            feature=feature,
            status=Status.ERROR_TOKEN,
            detail=f"error tokens in valid code: {sample!r}",
            found_category=ERROR,
            found_raw=error_tokens[0].raw,
        )

    span = _span_of(feature.snippet, feature.token, feature.occurrence)
    if span is None:  # guarded by the corpus loader, kept for hand-built features
        return Result(
            library=library,
            feature=feature,
            status=Status.NOT_FOUND,
            detail=f"{feature.token!r} is not in the snippet",
        )

    if _stream_matches(tokens, feature.snippet):
        covering = _covering_tokens(tokens, span) or []
    else:
        covering = _fallback_tokens(tokens, feature.token, feature.occurrence)

    result = _classify(feature, library, covering)
    if result.status is Status.UNSTYLED and feature.has_baseline:
        return _apply_baseline(adapter, feature, result)
    return result


def _apply_baseline(adapter: Adapter, feature: Feature, result: Result) -> Result:
    """Do not blame a library for a scope it never paints.

    Some libraries deliberately leave whole classes of token unstyled -- most
    grammars in highlight.js do not mark operators, for instance. A feature
    only counts as missing if the library styles the older, equivalent
    construct named in the corpus entry's ``baseline``.
    """
    try:
        tokens = adapter.tokenize(feature.language, feature.baseline_snippet)
    except AdapterUnavailable:  # pragma: no cover - already reported elsewhere
        return result

    span = _span_of(feature.baseline_snippet, feature.baseline_token, 1)
    if span is None:  # pragma: no cover - guarded by the corpus loader
        return result
    if _stream_matches(tokens, feature.baseline_snippet):
        covering = _covering_tokens(tokens, span) or []
    else:
        covering = _fallback_tokens(tokens, feature.baseline_token, 1)

    baseline = _classify(feature, result.library, covering)
    if baseline.status is Status.UNSTYLED:
        return Result(
            library=result.library,
            feature=feature,
            status=Status.NOT_APPLICABLE,
            detail=(
                f"library leaves {feature.baseline_token!r} unstyled too, "
                "so this is a style choice rather than drift"
            ),
            found_category=result.found_category,
            found_raw=result.found_raw,
        )
    return result


def check_library(adapter: Adapter, features: Sequence[Feature]) -> LibraryReport:
    """Check every feature against one library."""
    report = LibraryReport(library=adapter.name)
    try:
        report.version = adapter.version()
    except AdapterUnavailable as exc:
        report.available = False
        report.unavailable_reason = str(exc)
        return report

    warm = getattr(adapter, "warm", None)
    if callable(warm):
        try:
            warm([(feature.language, feature.snippet) for feature in features])
        except AdapterUnavailable as exc:  # pragma: no cover - environment dependent
            report.available = False
            report.unavailable_reason = str(exc)
            return report

    report.results = [check_feature(adapter, feature) for feature in features]
    return report


def check(adapters: Iterable[Adapter], features: Sequence[Feature]) -> list[LibraryReport]:
    reports = []
    for adapter in adapters:
        try:
            reports.append(check_library(adapter, features))
        except AdapterUnavailable as exc:
            reports.append(
                LibraryReport(
                    library=getattr(adapter, "name", "?"),
                    available=False,
                    unavailable_reason=str(exc),
                )
            )
    return reports
