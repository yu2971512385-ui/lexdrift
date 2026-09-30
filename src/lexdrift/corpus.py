"""Loading and validating the feature corpus."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Iterable, Iterator

import yaml

from .model import CATEGORIES, Feature


class CorpusError(ValueError):
    """Raised when a corpus file does not describe checkable features."""


def _require(mapping: dict, key: str, where: str):
    if key not in mapping or mapping[key] in (None, ""):
        raise CorpusError(f"{where}: missing required key {key!r}")
    return mapping[key]


def parse_document(data: dict, source: str) -> list[Feature]:
    """Turn one parsed YAML document into features."""
    if not isinstance(data, dict):
        raise CorpusError(f"{source}: expected a mapping at the top level")

    language = _require(data, "language", source)
    raw_features = _require(data, "features", source)
    if not isinstance(raw_features, list):
        raise CorpusError(f"{source}: 'features' must be a list")

    features: list[Feature] = []
    for index, raw in enumerate(raw_features):
        where = f"{source}[{index}]"
        if not isinstance(raw, dict):
            raise CorpusError(f"{where}: expected a mapping")

        identifier = _require(raw, "id", where)
        snippet = _require(raw, "snippet", where)
        token = _require(raw, "token", where)
        expect = tuple(raw.get("expect") or ())
        for category in expect:
            if category not in CATEGORIES:
                raise CorpusError(
                    f"{where}: unknown category {category!r}; "
                    f"known categories are {', '.join(CATEGORIES)}"
                )

        baseline = raw.get("baseline") or {}
        if baseline and not (baseline.get("snippet") and baseline.get("token")):
            raise CorpusError(f"{where}: 'baseline' needs both 'snippet' and 'token'")
        if baseline and baseline["token"] not in baseline["snippet"]:
            raise CorpusError(f"{where}: baseline snippet does not contain its token")

        occurrence = int(raw.get("occurrence", 1))
        if occurrence < 1:
            raise CorpusError(f"{where}: 'occurrence' is 1-based")
        if snippet.count(token) < occurrence:
            raise CorpusError(
                f"{where}: snippet does not contain occurrence {occurrence} of {token!r}"
            )

        features.append(
            Feature(
                id=identifier,
                language=language,
                name=_require(raw, "name", where),
                snippet=snippet,
                token=token,
                since=str(raw.get("since", "")),
                spec=str(raw.get("spec", "")),
                expect=expect,
                occurrence=occurrence,
                contextual=bool(raw.get("contextual", False)),
                note=str(raw.get("note", "")),
                baseline_snippet=str(baseline.get("snippet", "")),
                baseline_token=str(baseline.get("token", "")),
            )
        )
    return features


def load_file(path: Path) -> list[Feature]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return parse_document(data, path.name)


def _bundled_files() -> Iterator[tuple[str, str]]:
    package = resources.files(__package__) / "corpus"
    for entry in sorted(package.iterdir(), key=lambda item: item.name):
        if entry.name.endswith((".yaml", ".yml")):
            yield entry.name, entry.read_text(encoding="utf-8")


def load_corpus(path: Path | None = None) -> list[Feature]:
    """Load the bundled corpus, or every YAML file under ``path``."""
    features: list[Feature] = []
    if path is None:
        for name, text in _bundled_files():
            features.extend(parse_document(yaml.safe_load(text), name))
    elif path.is_dir():
        for entry in sorted(path.glob("*.y*ml")):
            features.extend(load_file(entry))
    else:
        features.extend(load_file(path))

    seen: dict[str, str] = {}
    for feature in features:
        if feature.id in seen:
            raise CorpusError(f"duplicate feature id {feature.id!r}")
        seen[feature.id] = feature.language
    return features


def filter_features(
    features: Iterable[Feature],
    languages: Iterable[str] = (),
    ids: Iterable[str] = (),
    include_contextual: bool = True,
) -> list[Feature]:
    languages = {item.lower() for item in languages}
    ids = set(ids)
    selected = []
    for feature in features:
        if languages and feature.language.lower() not in languages:
            continue
        if ids and feature.id not in ids:
            continue
        if not include_contextual and feature.contextual:
            continue
        selected.append(feature)
    return selected


def languages(features: Iterable[Feature]) -> list[str]:
    return sorted({feature.language for feature in features})
