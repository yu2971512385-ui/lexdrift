"""Adapter for chroma (https://github.com/alecthomas/chroma), through Go.

chroma is a Go library, so lexdrift ships a small Go program next to the
package and runs it with ``go run``. The first run downloads chroma into the
module cache; after that it is offline and fast. Without a Go toolchain the
adapter simply reports itself as unavailable.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from importlib import resources
from pathlib import Path

from ..model import Token
from .base import AdapterUnavailable, register

# chroma's token names are Pygments' names without the dots, so the mapping is
# matched on the longest prefix: ``NameBuiltin`` wins over ``Name``.
CATEGORY_MAP = {
    "Error": "error",
    "Text": "plain",
    "TextWhitespace": "plain",
    "None": "plain",
    "Name": "plain",
    "NameOther": "plain",
    "NameVariable": "other",
    "NameAttribute": "other",
    "NameLabel": "other",
    "NameNamespace": "other",
    "NameTag": "other",
    "NameDecorator": "other",
    "NameFunction": "other",
    "NameConstant": "constant",
    "NameClass": "type",
    "NameBuiltin": "builtin",
    "NameBuiltinPseudo": "builtin",
    "Keyword": "keyword",
    "KeywordType": "type",
    "KeywordConstant": "constant",
    "Operator": "operator",
    "OperatorWord": "keyword",
    "Punctuation": "other",
    "Literal": "other",
    "LiteralString": "string",
    "LiteralNumber": "number",
    "Comment": "comment",
    "CommentPreproc": "other",
    "Generic": "other",
}


def _longest_prefix(raw: str) -> str:
    best = ""
    for key in CATEGORY_MAP:
        if raw.startswith(key) and len(key) > len(best):
            best = key
    return CATEGORY_MAP.get(best, "other")


def _runner_dir() -> Path:
    return Path(str(resources.files(__package__).parent / "go"))


class ChromaAdapter:
    name = "chroma"
    label = "chroma"
    url = "https://github.com/alecthomas/chroma"

    def __init__(self) -> None:
        self.go = shutil.which("go")
        if not self.go:
            raise AdapterUnavailable("go is not on PATH; install Go to check chroma")
        if not (_runner_dir() / "main.go").is_file():
            raise AdapterUnavailable("the chroma runner is missing from this installation")
        self._version: str | None = None
        self._cache: dict[tuple[str, str], list[Token] | None] = {}

    def _run(self, requests: list[tuple[str, str]]) -> None:
        payload = json.dumps(
            {"requests": [{"language": language, "code": code} for language, code in requests]}
        )
        env = dict(os.environ)
        env.setdefault("GOFLAGS", "-mod=mod")
        try:
            completed = subprocess.run(
                [self.go, "run", "."],
                cwd=_runner_dir(),
                input=payload,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - timing dependent
            raise AdapterUnavailable("chroma: the Go runner timed out") from exc

        stdout = completed.stdout.strip()
        if not stdout:
            detail = completed.stderr.strip().splitlines()
            raise AdapterUnavailable(
                "chroma: the Go runner produced no output"
                + (f" ({detail[-1]})" if detail else "")
            )
        data = json.loads(stdout)
        if data.get("error"):
            raise AdapterUnavailable(f"chroma: {data['error']}")

        self._version = data.get("version", "")
        for (language, code), tokens in zip(requests, data.get("results") or []):
            if tokens is None:
                self._cache[(language, code)] = None
                continue
            self._cache[(language, code)] = [
                Token(text=item["text"], category=_longest_prefix(item["raw"]), raw=item["raw"])
                for item in tokens
            ]

    def warm(self, requests: list[tuple[str, str]]) -> None:
        missing = [item for item in requests if item not in self._cache]
        if missing:
            self._run(missing)

    def version(self) -> str:
        if self._version is None:
            self._run([("go", "var x = 1\n")])
        return self._version or ""

    def supports(self, language: str) -> bool:
        probe = (language, "\n")
        if probe not in self._cache:
            self._run([probe])
        return self._cache[probe] is not None

    def tokenize(self, language: str, code: str) -> list[Token]:
        key = (language, code)
        if key not in self._cache:
            self._run([key])
        tokens = self._cache[key]
        if tokens is None:
            raise AdapterUnavailable(f"chroma has no lexer for {language!r}")
        return tokens


register(ChromaAdapter.name, ChromaAdapter)
