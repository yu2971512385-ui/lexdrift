"""Shared fixtures: a fake highlighter that lexdrift can be tested against."""

from __future__ import annotations

import pytest

from lexdrift.adapters.base import AdapterUnavailable
from lexdrift.model import Token


class FakeAdapter:
    """A highlighter whose opinions are supplied by the test.

    ``styles`` maps a word to the category the fake library gives it; any word
    that is not in the mapping comes back as plain text, which is how a real
    library shows a keyword it has never heard of.
    """

    name = "fake"
    label = "Fake"
    url = "https://example.invalid/fake"

    def __init__(self, styles: dict[str, str] | None = None, languages=("go", "python")):
        self.styles = styles or {}
        self.languages = set(languages)
        self.calls: list[tuple[str, str]] = []

    def version(self) -> str:
        return "1.2.3"

    def supports(self, language: str) -> bool:
        return language in self.languages

    def tokenize(self, language: str, code: str) -> list[Token]:
        if language not in self.languages:
            raise AdapterUnavailable(f"no grammar for {language}")
        self.calls.append((language, code))
        tokens: list[Token] = []
        for word in _split_keeping_separators(code):
            category = self.styles.get(word.strip(), "plain")
            tokens.append(Token(text=word, category=category, raw=category))
        return tokens


def _split_keeping_separators(code: str) -> list[str]:
    """Split into word and non-word runs, preserving every character."""
    parts: list[str] = []
    current = ""
    current_is_word = None
    for char in code:
        is_word = char.isalnum() or char == "_"
        if current_is_word is None or is_word == current_is_word:
            current += char
            current_is_word = is_word
        else:
            parts.append(current)
            current = char
            current_is_word = is_word
    if current:
        parts.append(current)
    return parts


@pytest.fixture
def fake_adapter():
    return FakeAdapter
