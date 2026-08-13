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
    "souroldgeezer-audit/skills/ip-hygiene/references/trademark.md",
)
INSTRUCTIONS_PATH = "EVALUATOR_INSTRUCTIONS.md"
INSTRUCTIONS = """# IP Hygiene Blind Evaluator Instructions

Read only assigned bundle content. Do not read any repository path, Git metadata or
history, evaluator cache, previous review, diagnosis, expected outcome, or
parent scoring material outside it. If you read outside the assigned bundle or
are exposed to an expected outcome, return `blocked:contaminated` and do not
produce or revise any results.

For each record in
`souroldgeezer-audit/skills/ip-hygiene/references/evals/accuracy-corpus/cases.jsonl`,
apply the bundled IP Hygiene workflow and its bundled references. Write one
actual JSONL record per case using the result shape enforced by
`souroldgeezer-audit/skills/ip-hygiene/references/scripts/validate_ip_hygiene_actual.py`.
Run that validator on the completed actual records before returning them.

This evaluator validates result structure only. Do not score behavioral accuracy,
infer hidden expected outcomes, or claim recall. Parent-only evaluation privately
scores behavior after receiving the actual records.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bundle(repo_root: Path, output: Path) -> None:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    sources = [(relative, repo_root / relative) for relative in ALLOWLIST]
    missing = [relative for relative, source in sources if not source.is_file()]
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

        files = [INSTRUCTIONS_PATH, *ALLOWLIST]
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
