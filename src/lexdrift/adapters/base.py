"""Adapter protocol and registry.

An adapter wraps one highlighting library and answers a single question:
*how does this library tokenise this snippet?* Everything library specific --
how to invoke it, what it calls its token types -- stays here, so the corpus
and the checker can remain library agnostic.
"""

from __future__ import annotations

from typing import Callable, Iterable, Protocol, runtime_checkable

from ..model import Token


class AdapterUnavailable(RuntimeError):
    """The library (or its runtime) is not installed."""


@runtime_checkable
class Adapter(Protocol):
    #: Short identifier used on the command line, e.g. ``pygments``.
    name: str
    #: Human readable name of the library, e.g. ``Pygments``.
    label: str
    #: Where the library lives, for the report.
    url: str

    def version(self) -> str:
        """Version of the wrapped library. Raises AdapterUnavailable."""

    def supports(self, language: str) -> bool:
        """Whether the library can highlight ``language`` at all."""

    def tokenize(self, language: str, code: str) -> list[Token]:
        """Tokenise ``code``; raises AdapterUnavailable when unusable."""


_REGISTRY: dict[str, Callable[[], Adapter]] = {}


def register(name: str, factory: Callable[[], Adapter]) -> None:
    _REGISTRY[name] = factory


def available_names() -> list[str]:
    return sorted(_REGISTRY)


def get_adapter(name: str) -> Adapter:
    try:
        factory = _REGISTRY[name]
    except KeyError:
        known = ", ".join(available_names())
        raise KeyError(f"unknown library {name!r}; known libraries are {known}") from None
    return factory()


def get_adapters(names: Iterable[str] = ()) -> list[Adapter]:
    selected = list(names) or available_names()
    return [get_adapter(name) for name in selected]


def map_category(raw: str, mapping: dict[str, str], default: str = "other") -> str:
    """Map a library's token name onto a normalised category.

    Names are matched most-specific first on ``.``-separated prefixes, so a
    mapping for ``Keyword`` also covers ``Keyword.Declaration`` unless that
    has its own entry.
    """
    parts = raw.split(".")
    for stop in range(len(parts), 0, -1):
        candidate = ".".join(parts[:stop])
        if candidate in mapping:
            return mapping[candidate]
    return default
