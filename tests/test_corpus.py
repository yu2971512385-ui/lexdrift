"""The bundled corpus is data, so it gets the same scrutiny as code."""

from __future__ import annotations

import pytest

from lexdrift.corpus import CorpusError, filter_features, languages, load_corpus, parse_document
from lexdrift.model import CATEGORIES

CORPUS = load_corpus()


def test_corpus_is_not_empty():
    assert len(CORPUS) > 20
    assert len(languages(CORPUS)) >= 5


def test_ids_are_unique():
    ids = [feature.id for feature in CORPUS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("feature", CORPUS, ids=lambda feature: feature.id)
def test_feature_is_well_formed(feature):
    assert feature.token in feature.snippet, "the token must be part of the snippet"
    assert feature.name
    assert feature.snippet.endswith("\n"), "snippets are whole lines"
    for category in feature.expect:
        assert category in CATEGORIES
    if feature.has_baseline:
        assert feature.baseline_token in feature.baseline_snippet
        assert feature.baseline_token != feature.token, "a baseline must be the older form"


def test_every_feature_says_when_it_arrived():
    undated = [feature.id for feature in CORPUS if not feature.since]
    assert not undated, f"features without a `since`: {undated}"


def test_filtering_by_language_and_id():
    go = filter_features(CORPUS, languages=["go"])
    assert go and all(feature.language == "go" for feature in go)
    single = filter_features(CORPUS, ids=[go[0].id])
    assert len(single) == 1


def test_contextual_features_can_be_skipped():
    with_contextual = filter_features(CORPUS)
    without = filter_features(CORPUS, include_contextual=False)
    assert len(without) < len(with_contextual)
    assert not any(feature.contextual for feature in without)


def test_parse_document_rejects_a_token_outside_the_snippet():
    with pytest.raises(CorpusError, match="does not contain"):
        parse_document(
            {
                "language": "go",
                "features": [{"id": "x", "name": "x", "snippet": "var a int\n", "token": "any"}],
            },
            "test.yaml",
        )


def test_parse_document_rejects_an_unknown_category():
    with pytest.raises(CorpusError, match="unknown category"):
        parse_document(
            {
                "language": "go",
                "features": [
                    {
                        "id": "x",
                        "name": "x",
                        "snippet": "var a any\n",
                        "token": "any",
                        "expect": ["sparkly"],
                    }
                ],
            },
            "test.yaml",
        )


def test_parse_document_rejects_a_half_written_baseline():
    with pytest.raises(CorpusError, match="baseline"):
        parse_document(
            {
                "language": "go",
                "features": [
                    {
                        "id": "x",
                        "name": "x",
                        "snippet": "var a any\n",
                        "token": "any",
                        "baseline": {"snippet": "var a error\n"},
                    }
                ],
            },
            "test.yaml",
        )
