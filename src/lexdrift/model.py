"""Core data types shared by the corpus, the adapters and the checker."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

#: Normalised token categories. Every adapter maps the token names of its
#: library onto these, so that expectations in the corpus stay library
#: agnostic. ``PLAIN`` means "the highlighter had nothing to say about this
#: text", which is what an unknown keyword looks like.
PLAIN = "plain"
ERROR = "error"
CATEGORIES = (
    "keyword",
    "type",
    "builtin",
    "constant",
    "operator",
    "string",
    "number",
    "comment",
    "other",
    PLAIN,
    ERROR,
)


class Status(str, Enum):
    """Outcome of checking one feature against one library."""

    OK = "ok"
    UNSTYLED = "unstyled"
    MISCATEGORISED = "miscategorised"
    ERROR_TOKEN = "error-token"
    NOT_FOUND = "not-found"
    NOT_APPLICABLE = "not-applicable"
    SKIPPED = "skipped"

    @property
    def is_gap(self) -> bool:
        """Whether the library failed to recognise the feature at all.

        Only ``UNSTYLED`` and ``ERROR_TOKEN`` count. A library that styles a
        feature differently than the corpus expected still knows about it, and
        those judgements (is ``min`` a builtin or just a function call?) are
        the library's to make, so ``MISCATEGORISED`` is advisory.
        """
        return self in (Status.UNSTYLED, Status.ERROR_TOKEN)

    @property
    def is_recognised(self) -> bool:
        return self in (Status.OK, Status.MISCATEGORISED)


@dataclass(frozen=True)
class Token:
    """One token as produced by a highlighter, with a normalised category."""

    text: str
    category: str
    raw: str = ""


@dataclass(frozen=True)
class Feature:
    """A language feature that a highlighter is expected to recognise.

    ``token`` is the piece of ``snippet`` that carries the feature -- the
    keyword, operator or literal that a highlighter which knows the feature
    will single out. ``expect`` narrows what it should be recognised *as*;
    when it is empty, any non-plain category counts, which is the fair
    default: libraries legitimately disagree on whether ``any`` is a type or
    a builtin, but none of them should leave it as plain text.
    """

    id: str
    language: str
    name: str
    snippet: str
    token: str
    since: str = ""
    spec: str = ""
    expect: tuple[str, ...] = ()
    occurrence: int = 1
    contextual: bool = False
    note: str = ""
    baseline_snippet: str = ""
    baseline_token: str = ""

    @property
    def has_baseline(self) -> bool:
        return bool(self.baseline_snippet and self.baseline_token)

    @property
    def label(self) -> str:
        return f"{self.name} ({self.since})" if self.since else self.name


@dataclass(frozen=True)
class Result:
    """The outcome of one (library, feature) pair."""

    library: str
    feature: Feature
    status: Status
    detail: str = ""
    found_category: str = ""
    found_raw: str = ""

    @property
    def is_gap(self) -> bool:
        return self.status.is_gap


@dataclass
class LibraryReport:
    """All results for one library, plus what the run knew about it."""

    library: str
    version: str = ""
    available: bool = True
    unavailable_reason: str = ""
    results: list[Result] = field(default_factory=list)

    @property
    def checked(self) -> list[Result]:
        return [
            r
            for r in self.results
            if r.status not in (Status.SKIPPED, Status.NOT_APPLICABLE)
        ]

    @property
    def gaps(self) -> list[Result]:
        return [r for r in self.results if r.is_gap]

    @property
    def advisories(self) -> list[Result]:
        return [r for r in self.results if r.status is Status.MISCATEGORISED]

    @property
    def recognised(self) -> int:
        return sum(1 for r in self.checked if r.status.is_recognised)

    @property
    def coverage(self) -> float:
        """Share of checked features the library recognises at all."""
        checked = self.checked
        if not checked:
            return 0.0
        return self.recognised / len(checked)
