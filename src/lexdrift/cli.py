"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .adapters import AdapterUnavailable, available_names, get_adapter
from .check import check
from .corpus import filter_features, languages, load_corpus
from .model import Status
from .report import render


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lexdrift",
        description="Find syntax highlighters that never learned a language's newer keywords.",
    )
    parser.add_argument("--version", action="version", version=f"lexdrift {__version__}")
    sub = parser.add_subparsers(dest="command")

    check_cmd = sub.add_parser("check", help="check libraries against the corpus")
    check_cmd.add_argument(
        "--lib",
        action="append",
        default=[],
        metavar="NAME",
        help=f"library to check (repeatable); default: all of {', '.join(available_names())}",
    )
    check_cmd.add_argument(
        "--lang", action="append", default=[], metavar="NAME", help="language to check (repeatable)"
    )
    check_cmd.add_argument(
        "--feature", action="append", default=[], metavar="ID", help="single feature id (repeatable)"
    )
    check_cmd.add_argument(
        "--corpus", type=Path, default=None, metavar="PATH", help="use this corpus file or directory"
    )
    check_cmd.add_argument(
        "--skip-contextual",
        action="store_true",
        help="skip features whose keyword is contextual, where not highlighting it is defensible",
    )
    check_cmd.add_argument(
        "--format", choices=("table", "markdown", "json"), default="table", help="output format"
    )
    check_cmd.add_argument(
        "--strict", action="store_true", help="exit non-zero when any gap is found (for CI)"
    )

    list_cmd = sub.add_parser("list", help="list the features in the corpus")
    list_cmd.add_argument("--lang", action="append", default=[], metavar="NAME")
    list_cmd.add_argument("--corpus", type=Path, default=None, metavar="PATH")

    sub.add_parser("libs", help="list the libraries lexdrift can drive, and whether they are usable")
    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    features = filter_features(
        load_corpus(args.corpus),
        languages=args.lang,
        ids=args.feature,
        include_contextual=not args.skip_contextual,
    )
    if not features:
        print("no features selected", file=sys.stderr)
        return 2

    adapters = []
    for name in args.lib or available_names():
        try:
            adapters.append(get_adapter(name))
        except AdapterUnavailable as exc:
            print(f"{name}: {exc}", file=sys.stderr)
        except KeyError as exc:
            print(str(exc).strip("'"), file=sys.stderr)
            return 2

    if not adapters:
        print("no usable libraries", file=sys.stderr)
        return 2

    reports = check(adapters, features)
    print(render(reports, args.format))

    gaps = sum(len(report.gaps) for report in reports)
    if args.strict and gaps:
        return 1
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    features = filter_features(load_corpus(args.corpus), languages=args.lang)
    current = None
    for feature in features:
        if feature.language != current:
            current = feature.language
            print(f"\n[{current}]")
        since = f" (since {feature.since})" if feature.since else ""
        contextual = "  [contextual]" if feature.contextual else ""
        print(f"  {feature.id:<28} {feature.name}{since}{contextual}")
    print(f"\n{len(features)} features across {len(languages(features))} languages")
    return 0


def _cmd_libs(_: argparse.Namespace) -> int:
    for name in available_names():
        try:
            adapter = get_adapter(name)
            version = adapter.version()
        except AdapterUnavailable as exc:
            print(f"{name:<14} unavailable  ({exc})")
            continue
        print(f"{name:<14} {version or 'unknown version'}  {adapter.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        return _cmd_check(args)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "libs":
        return _cmd_libs(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
