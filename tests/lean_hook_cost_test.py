"""Content-free hook-registration ledger tests for lean-audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.surface_test_lib import REPO_ROOT, load_script_module

MODULE = (
    REPO_ROOT / "souroldgeezer-audit/skills/lean-audit/references/scripts/leanaudit/hook_cost.py"
)


def load_hook_cost():
    return load_script_module("lean_hook_cost", MODULE)


class HookRegistrationTest(unittest.TestCase):
    def test_codex_and_claude_registrations_are_inventoried_without_commands(self) -> None:
        mod = load_hook_cost()
        secret = "DO-NOT-EMIT-HOOK-COMMAND"
        report = mod.analyze_hook_registrations(
            {
                ".codex/hooks.json": json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {"hooks": [{"type": "command", "command": f"printf {secret}"}]}
                            ]
                        }
                    }
                ),
                ".claude/settings.json": json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Bash",
                                    "hooks": [{"type": "command", "command": f"printf {secret}"}],
                                }
                            ]
                        }
                    }
                ),
            }
        )

        self.assertEqual(len(report["registrations"]), 2)
        self.assertEqual(
            {(row["runtime"], row["event"]) for row in report["registrations"]},
            {("codex", "Stop"), ("claude", "PreToolUse")},
        )
        self.assertTrue(all(row["command_present"] for row in report["registrations"]))
        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report["content_policy"], "metadata-only; hook commands opaque")

    def test_missing_fixture_values_are_unknown_not_zero(self) -> None:
        mod = load_hook_cost()
        report = mod.analyze_hook_registrations(
            {
                ".codex/hooks.json": json.dumps(
                    {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}
                )
            }
        )

        row = report["fixture_metadata"][0]
        for field in ("enabled", "visibility", "frequency", "proxy_tokens"):
            self.assertEqual(row[field], "unknown")
        self.assertEqual(report["evidenced_proxy_tokens"], "unknown")
        self.assertEqual(report["model_injected_proxy_tokens"], "unknown")
        self.assertEqual(report["model_injected_evidence_count"], 0)

    def test_supplied_content_free_fixture_metadata_joins_by_opaque_indices(self) -> None:
        mod = load_hook_cost()
        selector = {
            "path": ".claude/settings.json",
            "event": "PreToolUse",
            "registration_index": 0,
            "hook_index": 0,
        }
        report = mod.analyze_hook_registrations(
            {
                selector["path"]: json.dumps(
                    {
                        "hooks": {
                            selector["event"]: [
                                {
                                    "matcher": "Bash",
                                    "hooks": [{"type": "command", "command": "opaque"}],
                                }
                            ]
                        }
                    }
                )
            },
            [
                {
                    **selector,
                    "enabled": True,
                    "visibility": "model",
                    "frequency": 7,
                    "proxy_tokens": 13,
                }
            ],
        )

        row = report["fixture_metadata"][0]
        self.assertEqual(row["enabled"], True)
        self.assertEqual(row["visibility"], "model")
        self.assertEqual(row["frequency"], 7)
        self.assertEqual(row["proxy_tokens"], 13)
        self.assertEqual(report["evidenced_proxy_tokens"], 13)
        self.assertEqual(report["unsupported"], [])

    def test_model_injected_cost_requires_complete_enabled_model_evidence(self) -> None:
        mod = load_hook_cost()
        path = ".codex/hooks.json"
        report = mod.analyze_hook_registrations(
            {
                path: json.dumps(
                    {
                        "hooks": {
                            "Stop": [
                                {
                                    "hooks": [
                                        {"type": "command", "command": f"opaque-{index}"}
                                        for index in range(4)
                                    ]
                                }
                            ]
                        }
                    }
                )
            },
            [
                {
                    "path": path,
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 0,
                    "enabled": True,
                    "visibility": "model",
                    "frequency": 3,
                    "proxy_tokens": 10,
                },
                {
                    "path": path,
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 1,
                    "enabled": False,
                    "visibility": "model",
                    "frequency": 5,
                    "proxy_tokens": 10,
                },
                {
                    "path": path,
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 2,
                    "enabled": True,
                    "visibility": "out-of-band",
                    "frequency": 7,
                    "proxy_tokens": 10,
                },
                {
                    "path": path,
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 3,
                    "enabled": True,
                    "visibility": "model",
                    "proxy_tokens": 10,
                },
            ],
        )

        self.assertEqual(report["evidenced_proxy_tokens"], 40)
        self.assertEqual(report["proxy_token_evidence_count"], 4)
        self.assertEqual(report["model_injected_proxy_tokens"], 30)
        self.assertEqual(report["model_injected_evidence_count"], 1)

    def test_raw_output_fixture_field_is_rejected_without_echoing_value(self) -> None:
        mod = load_hook_cost()
        secret = "DO-NOT-ACCEPT-RAW-HOOK-OUTPUT"
        report = mod.analyze_hook_registrations(
            {
                ".codex/hooks.json": json.dumps(
                    {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}
                )
            },
            [
                {
                    "path": ".codex/hooks.json",
                    "event": "Stop",
                    "registration_index": 0,
                    "hook_index": 0,
                    "output": secret,
                }
            ],
        )

        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report["fixture_metadata"][0]["proxy_tokens"], "unknown")
        self.assertTrue(any(row["kind"] == "fixture-format" for row in report["unsupported"]))

    def test_invalid_registration_shapes_are_reported_and_commands_never_run(self) -> None:
        mod = load_hook_cost()
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "must-not-exist"
            report = mod.analyze_hook_registrations(
                {
                    ".codex/hooks.json": json.dumps(
                        {
                            "hooks": {
                                "Stop": {"hooks": []},
                                "PreToolUse": [
                                    {
                                        "hooks": [
                                            {
                                                "type": "command",
                                                "command": f"touch {marker}",
                                            }
                                        ]
                                    }
                                ],
                            }
                        }
                    ),
                    "nested/.claude/settings.json": "[]",
                }
            )

            self.assertFalse(marker.exists())
            self.assertEqual(len(report["registrations"]), 1)
            self.assertGreaterEqual(len(report["unsupported"]), 2)
            self.assertTrue(all("command" not in row for row in report["unsupported"]))


class HookFixtureReaderTest(unittest.TestCase):
    def test_jsonl_fixture_reader_accepts_content_free_rows(self) -> None:
        mod = load_hook_cost()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hook-fixture.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "path": ".codex/hooks.json",
                        "event": "Stop",
                        "registration_index": 0,
                        "hook_index": 0,
                        "enabled": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rows = mod.read_hook_fixture_file(path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["enabled"], False)


if __name__ == "__main__":
    unittest.main()
