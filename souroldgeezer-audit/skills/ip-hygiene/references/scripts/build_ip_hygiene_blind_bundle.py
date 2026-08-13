#!/usr/bin/env python3
"""Build a deterministic, allowlisted IP-hygiene blind-evaluation bundle."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


SCHEMA_VERSION = "ip-hygiene-blind-bundle.v1"
ALLOWLIST = (
    "souroldgeezer-audit/docs/audit-reference/audit-craft.md",
    "souroldgeezer-audit/docs/audit-reference/materiality.md",
    "souroldgeezer-audit/skills/ip-hygiene/SKILL.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/authority-index.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/copyright.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/drive-by.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/cases.jsonl",
    "souroldgeezer-audit/skills/ip-hygiene/references/licence-assets.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/scripts/validate_ip_hygiene_actual.py",
    "souroldgeezer-audit/skills/ip-hygiene/references/source-code.md",
    "souroldgeezer-audit/skills/ip-hygiene/references/trademark.md",
    # Language packs: the corpus poses scenarios in specific languages, and a
    # real reviewer loads the matching pack. They add no criteria, so they are
    # evidence surfaces rather than grading inputs.
    "souroldgeezer-audit/skills/ip-hygiene/extensions/dotnet-csharp.md",
    "souroldgeezer-audit/skills/ip-hygiene/extensions/java.md",
    "souroldgeezer-audit/skills/ip-hygiene/extensions/javascript-typescript.md",
    "souroldgeezer-audit/skills/ip-hygiene/extensions/python.md",
    "souroldgeezer-audit/skills/ip-hygiene/extensions/rust.md",
    "souroldgeezer-audit/skills/ip-hygiene/extensions/shell.md",
)
ROOT_DESTINATIONS = {
    "souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/cases.jsonl": "cases.jsonl",
    "souroldgeezer-audit/skills/ip-hygiene/references/scripts/validate_ip_hygiene_actual.py": "validate_ip_hygiene_actual.py",
}
INSTRUCTIONS_PATH = "EVALUATOR_INSTRUCTIONS.md"
INSTRUCTIONS = """# IP Hygiene Blind Evaluator Instructions

Read only assigned bundle content. Do not read any repository path, Git metadata or
history, evaluator cache, previous review, diagnosis, expected outcome, or
parent scoring material outside it. If you read outside the assigned bundle or
are exposed to an expected outcome, return `blocked:contaminated` and do not
produce or revise any results.

For each record in `cases.jsonl`,
apply the bundled IP Hygiene workflow and its bundled references. Write one
actual JSONL record per case using the result shape enforced by
`validate_ip_hygiene_actual.py`.
Every record must ground its reviewed surface, exclusions, evidence, limits,
independence, and assurance level in the assigned case. Prospective records also
name decision controls. Every finding supplies the complete bounded finding
basis required by the validator, including condition/location, provenance, act,
audience, applicability, evidence, cause, consequence, and recommendation; do
not use generic placeholders.
Run `validate_ip_hygiene_actual.py --cases cases.jsonl --actual <actual.jsonl>`
on the completed actual records before returning them. The coverage-aware form
is mandatory: every assigned opaque case ID must occur exactly once and no
unassigned ID may occur.

This evaluator validates result structure only. Do not score behavioral accuracy,
infer hidden expected outcomes, or claim recall. Parent-only evaluation privately
scores behavior after receiving the actual records.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bundle(repo_root: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    sources = [
        (ROOT_DESTINATIONS.get(relative, relative), repo_root / relative)
        for relative in ALLOWLIST
    ]
    unsafe = []
    for _, source in sources:
        if source.is_symlink():
            unsafe.append(f"symlink source is forbidden: {source.relative_to(repo_root)}")
            continue
        try:
            resolved = source.resolve(strict=True)
        except FileNotFoundError:
            continue
        if not resolved.is_relative_to(repo_root):
            unsafe.append(f"source resolves outside repo_root: {source.relative_to(repo_root)}")
    if unsafe:
        raise ValueError("; ".join(unsafe))
    missing = [str(source.relative_to(repo_root)) for _, source in sources if not source.is_file()]
    if missing:
        raise ValueError("missing allowlisted source: " + ", ".join(missing))

    output.mkdir(parents=True)
    try:
        instruction_path = output / INSTRUCTIONS_PATH
        instruction_path.write_text(INSTRUCTIONS, encoding="utf-8")
        for relative, source in sources:
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        files = [INSTRUCTIONS_PATH, *(relative for relative, _ in sources)]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "files": [
                {"path": relative, "sha256": sha256(output / relative)}
                for relative in sorted(files)
            ],
        }
        (output / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except Exception:
        shutil.rmtree(output)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        build_bundle(args.repo_root.resolve(), args.output.resolve())
    except ValueError as error:
        print(f"build_ip_hygiene_blind_bundle: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
