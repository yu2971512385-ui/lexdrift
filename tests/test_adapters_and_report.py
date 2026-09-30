"""Adapter mapping, report rendering and the command line."""

from __future__ import annotations

import json

import pytest

from lexdrift.adapters.base import map_category
from lexdrift.check import check
from lexdrift.cli import main
from lexdrift.model import Feature, LibraryReport, Result, Status
from lexdrift.report import render_json, render_markdown, render_table

pygments = pytest.importorskip("pygments")

from lexdrift.adapters.pygments_adapter import CATEGORY_MAP, PygmentsAdapter  # noqa: E402


def test_map_category_falls_back_to_the_nearest_prefix():
    mapping = {"Keyword": "keyword", "Keyword.Type": "type"}
    assert map_category("Keyword.Declaration", mapping) == "keyword"
    assert map_category("Keyword.Type", mapping) == "type"
    assert map_category("Comment.Single", mapping) == "other"
    assert map_category("Comment.Single", mapping, default="comment") == "comment"


def test_pygments_maps_an_unknown_identifier_to_plain():
    assert map_category("Name", CATEGORY_MAP) == "plain"
    assert map_category("Name.Other", CATEGORY_MAP) == "plain"
    assert map_category("Error", CATEGORY_MAP) == "error"
    assert map_category("Keyword.Type", CATEGORY_MAP) == "type"


def test_pygments_adapter_round_trips_a_snippet():
    adapter = PygmentsAdapter()
    assert adapter.supports("go")
    assert not adapter.supports("not-a-language")
    tokens = adapter.tokenize("go", "var failure error = nil\n")
    assert "".join(token.text for token in tokens) == "var failure error = nil\n"
    categories = {token.text: token.category for token in tokens}
    assert categories["var"] == "keyword"
    assert categories["error"] == "type"


def _reports():
    feature = Feature(
        id="go-any",
        language="go",
        name="predeclared type `any`",
        snippet="var payload any = 1\n",
        token="any",
        since="1.18",
        spec="https://go.dev/ref/spec",
    )
    report = LibraryReport(library="fake", version="1.2.3")
    report.results = [
        Result(library="fake", feature=feature, status=Status.UNSTYLED, detail="plain"),
    ]
    return [report]


def test_table_report_mentions_the_gap():
    text = render_table(_reports())
    assert "go-any" in text
    assert "MISSING" in text
    assert "1 unrecognised feature(s)" in text


def test_markdown_report_is_a_table_with_links():
    text = render_markdown(_reports())
    assert text.startswith("# lexdrift report")
    assert "| feature | since |" in text
    assert "https://go.dev/ref/spec" in text
    assert "❌" in text


def test_json_report_is_machine_readable():
    payload = json.loads(render_json(_reports()))
    assert payload[0]["library"] == "fake"
    assert payload[0]["results"][0]["status"] == "unstyled"


def test_cli_list_and_libs(capsys):
    assert main(["list", "--lang", "go"]) == 0
    listing = capsys.readouterr().out
    assert "go-any" in listing

    assert main(["libs"]) == 0
    assert "pygments" in capsys.readouterr().out


def test_cli_check_reports_and_can_fail_the_build(capsys):
    assert main(["check", "--lib", "pygments", "--lang", "go", "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["library"] == "pygments"

    # --strict only fails when something is actually missing, so use a corpus
    # entry that Pygments is known to handle plus the strict flag: the exit
    # code must mirror the presence of gaps.
    exit_code = main(["check", "--lib", "pygments", "--lang", "go", "--strict"])
    output = capsys.readouterr().out
    assert exit_code == (1 if "MISSING" in output else 0)


def test_cli_rejects_an_unknown_library(capsys):
    assert main(["check", "--lib", "nope"]) == 2
    assert "unknown library" in capsys.readouterr().err
