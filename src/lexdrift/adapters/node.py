"""Adapters for JavaScript highlighters, driven through a Node subprocess.

highlight.js and Prism are npm packages, so lexdrift shells out to Node once
per library and asks it to tokenise every snippet in one batch. The packages
are looked up in the usual places Node looks: install them wherever you run
lexdrift from, or in the bundled ``js`` directory (``npm install`` there).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from importlib import resources
from pathlib import Path

from ..model import Token
from .base import AdapterUnavailable, map_category, register

HLJS_CATEGORY_MAP = {
    "": "plain",
    "keyword": "keyword",
    "type": "type",
    "built_in": "builtin",
    "literal": "constant",
    "number": "number",
    "string": "string",
    "comment": "comment",
    "operator": "operator",
    "symbol": "other",
    "title": "other",
    "params": "plain",  # hljs wraps whole parameter lists, text inside is not classified
    "meta": "other",
    "attr": "other",
    "attribute": "other",
    "property": "other",
    "variable": "other",
    "subst": "plain",
    "regexp": "string",
    "char": "string",
    "char.escape": "string",
    "selector-tag": "other",
    "section": "other",
    "tag": "other",
    "name": "other",
    "function": "other",
    "class": "other",
    "doctag": "comment",
}

PRISM_CATEGORY_MAP = {
    "": "plain",
    "keyword": "keyword",
    "builtin": "builtin",
    "class-name": "type",
    "boolean": "constant",
    "constant": "constant",
    "number": "number",
    "string": "string",
    "template-string": "string",
    "comment": "comment",
    "operator": "operator",
    "punctuation": "other",
    "function": "other",
    "function-variable": "other",
    "property": "other",
    "parameter": "plain",
    "attr-name": "other",
    "tag": "other",
    "directive": "other",
    "annotation": "other",
    "generics": "other",
    "triple-quoted-string": "string",
    "raw-string": "string",
    "interpolation-string": "string",
    "char": "string",
    "regex": "string",
    "symbol": "other",
    "label": "other",
    "namespace": "other",
    "type-declaration": "type",
    "return-type": "type",
    "builtin-type": "type",
    "lifetime-annotation": "other",
    "attribute": "other",
    "macro-name": "other",
    "package": "other",
    "variable": "other",
    "important": "other",
    "selector": "other",
    "delimiter": "other",
    "string-literal": "string",
}


def _runner_script() -> Path:
    return Path(str(resources.files(__package__).parent / "js" / "runner.mjs"))


class _NodeAdapter:
    """Shared plumbing for the Node-backed adapters."""

    #: Identifier understood by ``runner.mjs``.
    library_key = ""
    category_map: dict[str, str] = {}
    package = ""

    def __init__(self) -> None:
        self.node = shutil.which("node")
        if not self.node:
            raise AdapterUnavailable("node is not on PATH; install Node.js to check " + self.label)
        self._version: str | None = None
        self._cache: dict[tuple[str, str], list[Token] | None] = {}

    # -- plumbing ---------------------------------------------------------
    def _run(self, requests: list[dict]) -> dict:
        payload = json.dumps({"library": self.library_key, "requests": requests})
        env = dict(os.environ)
        bundled_modules = _runner_script().parent / "node_modules"
        if bundled_modules.is_dir():
            existing = env.get("NODE_PATH")
            env["NODE_PATH"] = f"{bundled_modules}{os.pathsep}{existing}" if existing else str(bundled_modules)
        try:
            completed = subprocess.run(
                [self.node, str(_runner_script())],
                input=payload,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - timing dependent
            raise AdapterUnavailable(f"{self.label}: Node runner timed out") from exc

        stdout = completed.stdout.strip()
        if not stdout:
            detail = completed.stderr.strip().splitlines()
            raise AdapterUnavailable(
                f"{self.label}: Node runner produced no output"
                + (f" ({detail[-1]})" if detail else "")
            )
        data = json.loads(stdout)
        if "error" in data:
            raise AdapterUnavailable(
                f"{self.label}: {data['error']} -- try `npm install {self.package}`"
            )
        return data

    def _tokenize_batch(self, requests: list[tuple[str, str]]) -> None:
        payload = [{"language": language, "code": code} for language, code in requests]
        data = self._run(payload)
        self._version = data.get("version", "")
        for (language, code), tokens in zip(requests, data.get("results", [])):
            if tokens is None:
                self._cache[(language, code)] = None
                continue
            self._cache[(language, code)] = [
                Token(
                    text=item["text"],
                    category=map_category(item.get("raw", ""), self.category_map),
                    raw=item.get("raw", ""),
                )
                for item in tokens
            ]

    # -- adapter API ------------------------------------------------------
    def warm(self, requests: list[tuple[str, str]]) -> None:
        """Tokenise many snippets in one Node process (an optimisation)."""
        missing = [item for item in requests if item not in self._cache]
        if missing:
            self._tokenize_batch(missing)

    def version(self) -> str:
        if self._version is None:
            self._tokenize_batch([("javascript", "var x = 1\n")])
        return self._version or ""

    def supports(self, language: str) -> bool:
        probe = (language, "\n")
        if probe not in self._cache:
            self._tokenize_batch([probe])
        return self._cache[probe] is not None

    def tokenize(self, language: str, code: str) -> list[Token]:
        key = (language, code)
        if key not in self._cache:
            self._tokenize_batch([key])
        tokens = self._cache[key]
        if tokens is None:
            raise AdapterUnavailable(f"{self.label} has no grammar for {language!r}")
        return tokens


class HighlightJsAdapter(_NodeAdapter):
    name = "highlightjs"
    label = "highlight.js"
    url = "https://github.com/highlightjs/highlight.js"
    library_key = "highlightjs"
    category_map = HLJS_CATEGORY_MAP
    package = "highlight.js"


class PrismAdapter(_NodeAdapter):
    name = "prism"
    label = "Prism"
    url = "https://github.com/PrismJS/prism"
    library_key = "prism"
    category_map = PRISM_CATEGORY_MAP
    package = "prismjs"


register(HighlightJsAdapter.name, HighlightJsAdapter)
register(PrismAdapter.name, PrismAdapter)
