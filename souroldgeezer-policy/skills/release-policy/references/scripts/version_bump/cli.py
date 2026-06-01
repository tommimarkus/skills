"""CLI adapter for the release-policy version bump helper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .errors import VersionBumpError, source_read, source_write
from .sources import read_version, write_version
from .strategies import BumpRequest, Strategy, resolve_strategy


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute and optionally write the next release version.",
        epilog=(
            "Examples: --strategy semver --current 1.2.3 --bump minor; "
            "--strategy calver --scheme YYYY.MM.build --date 2026-05-29"
        ),
    )
    parser.add_argument("--strategy", default="semver")
    parser.add_argument("--current")
    parser.add_argument("--source")
    parser.add_argument("--source-kind", choices=("auto", "json", "toml", "text"), default="auto")
    parser.add_argument("--bump")
    parser.add_argument("--scheme", default="YYYY.MM.build")
    parser.add_argument("--date")
    parser.add_argument("--existing-tag", action="append", default=[])
    parser.add_argument("--pre-label", default="rc")
    parser.add_argument("--tag-template", default="v{version}")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, object]:
    strategy = resolve_strategy(args.strategy)
    source_path, source_kind, current = resolve_source(args)
    next_version = compute_next(strategy, args, current)
    maybe_write_source(args, source_path, source_kind, current, next_version)
    return build_result(args, strategy, source_path, source_kind, current, next_version)


def resolve_source(args: argparse.Namespace) -> tuple[Path | None, str | None, str | None]:
    source_path = Path(args.source) if args.source else None
    if not source_path:
        return None, None, args.current

    source_kind, source_version = read_version(source_path, args.source_kind)
    if args.current and args.current != source_version:
        raise source_read(f"--current {args.current} does not match {source_version}")
    return source_path, source_kind, source_version


def compute_next(strategy: Strategy, args: argparse.Namespace, current: str | None) -> str:
    request = BumpRequest(
        current=current,
        bump=args.bump,
        pre_label=args.pre_label,
        scheme=args.scheme,
        date=args.date,
        existing_tags=args.existing_tag,
    )
    return strategy.bump(request)


def maybe_write_source(
    args: argparse.Namespace,
    source_path: Path | None,
    source_kind: str | None,
    current: str | None,
    next_version: str,
) -> None:
    if not args.write:
        return
    if not source_path:
        raise source_write("--write requires --source")
    write_version(source_path, source_kind or "auto", current or "", next_version)


def build_result(
    args: argparse.Namespace,
    strategy: Strategy,
    source_path: Path | None,
    source_kind: str | None,
    current: str | None,
    next_version: str,
) -> dict[str, object]:
    request = BumpRequest(current, args.bump, args.pre_label, args.scheme, args.date, args.existing_tag)
    return {
        "strategy": strategy.name,
        "scheme": args.scheme if strategy.name == "calver" else None,
        "bump": strategy.default_bump(request),
        "current_version": current,
        "next_version": next_version,
        "tag": args.tag_template.format(version=next_version),
        "source": str(source_path) if source_path else None,
        "source_kind": source_kind,
        "written": bool(args.write),
    }


def emit_result(result: dict[str, object], output_format: str) -> None:
    if output_format == "text":
        print(result["next_version"])
        return
    print(json.dumps(result, indent=2, sort_keys=True))


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        emit_result(run(args), args.format)
        return 0
    except VersionBumpError as exc:
        print(f"version-bump:{exc.code}: {exc}", file=sys.stderr)
        return exc.exit_code
