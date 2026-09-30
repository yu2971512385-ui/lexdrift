"""Adapter for Pygments (https://pygments.org)."""

from __future__ import annotations

from ..model import Token
from .base import AdapterUnavailable, map_category, register

# Pygments token types are dotted paths under ``Token``; the mapping is
# matched most-specific first, so ``Keyword`` covers ``Keyword.Declaration``
# while ``Keyword.Type`` keeps its own category.
CATEGORY_MAP = {
    "Error": "error",
    "Text": "plain",
    "Whitespace": "plain",
    "Token": "plain",
    "Name": "plain",  # the generic identifier: an unknown keyword lands here
    "Name.Other": "plain",  # what several lexers call a bare identifier
    "Name.Attribute": "other",
    "Name.Constant": "constant",
    "Name.Entity": "other",
    "Name.Function": "other",
    "Name.Label": "other",
    "Name.Namespace": "other",
    "Name.Tag": "other",
    "Name.Variable": "other",
    "Name.Builtin": "builtin",
    "Name.Builtin.Pseudo": "builtin",
    "Name.Class": "type",
    "Name.Decorator": "other",
    "Keyword": "keyword",
    "Keyword.Type": "type",
    "Keyword.Constant": "constant",
    "Operator": "operator",
    "Operator.Word": "keyword",
    "Literal.String": "string",
    "Literal.Number": "number",
    "Comment": "comment",
    "Punctuation": "other",
}


class PygmentsAdapter:
    name = "pygments"
    label = "Pygments"
    url = "https://github.com/pygments/pygments"

    def __init__(self) -> None:
        try:
            import pygments  # noqa: F401
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise AdapterUnavailable(
                "Pygments is not installed; `pip install lexdrift[pygments]`"
            ) from exc

    def version(self) -> str:
        import pygments

        return pygments.__version__

    def supports(self, language: str) -> bool:
        from pygments.lexers import get_lexer_by_name
        from pygments.util import ClassNotFound

        try:
            get_lexer_by_name(language)
        except ClassNotFound:
            return False
        return True

    def tokenize(self, language: str, code: str) -> list[Token]:
        from pygments.lexers import get_lexer_by_name
        from pygments.util import ClassNotFound

        try:
            lexer = get_lexer_by_name(language, stripnl=False, ensurenl=False)
        except ClassNotFound as exc:
            raise AdapterUnavailable(f"Pygments has no lexer for {language!r}") from exc

        tokens = []
        for token_type, value in lexer.get_tokens(code):
            raw = str(token_type)
            raw = raw[len("Token.") :] if raw.startswith("Token.") else raw
            tokens.append(Token(text=value, category=map_category(raw, CATEGORY_MAP), raw=raw))
        return tokens


register(PygmentsAdapter.name, PygmentsAdapter)
