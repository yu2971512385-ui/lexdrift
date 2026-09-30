#!/usr/bin/env python3
"""Turn REPORT.md into the GitHub Pages front page.

The site is only ever a thin wrapper: the numbers come from REPORT.md, which
is produced by ``lexdrift check --format markdown``, so the page and the file
in the repository can never disagree.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "REPORT.md"
SITE = ROOT / "docs" / "index.md"

HEADER = """---
layout: default
title: lexdrift
description: How far behind the languages are the syntax highlighters?
---

# lexdrift

Syntax highlighters go stale quietly: a language ships a keyword, the grammar
does not get the memo, and from then on that keyword renders as if it were a
variable name. This page is regenerated every week by
[the report workflow]({repo}/actions/workflows/report.yml) and says how far
behind each library currently is.

A feature counts as **missing** only when the library renders it as plain
text, or emits an error token on valid code. When a library styles no token
of that kind at all -- most highlight.js grammars never mark operators, for
instance -- the corpus entry's baseline catches it and the cell shows `◦`
instead, because that is a style choice rather than drift.

Source, corpus and the tool itself: [{repo}]({repo}).

_Last regenerated: {when} UTC._

"""


def main() -> int:
    if not REPORT.is_file():
        print(f"{REPORT} is missing; run `lexdrift check --format markdown > REPORT.md`")
        return 1

    report = REPORT.read_text(encoding="utf-8")
    # The page carries its own title, so drop the one from the report.
    body = report.split("\n", 1)[1].lstrip("\n") if report.startswith("# ") else report

    SITE.parent.mkdir(parents=True, exist_ok=True)
    SITE.write_text(
        HEADER.format(
            repo="https://github.com/yu2971512385-ui/lexdrift",
            when=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
        )
        + body,
        encoding="utf-8",
    )
    print(f"wrote {SITE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
