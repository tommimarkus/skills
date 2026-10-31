"""Planning ledger command line: argument parsing and main."""

from __future__ import annotations

import argparse

from .acceptance import run_acceptance
from .closeout import close_run, init5, land, reopen_run, show, validate
from .core import Error, UsageError, out
from .dispatch import dispatch, handoff, transition_step
from .retention import gc, list_runs, purge
from .returns import amend, record, validate_return
from .tracing import trace_close, trace_init, trace_record, trace_show
from .verify import (
    check_changeset,
    record_changeset,
    record_verify,
    validate_verify_return,
    verify_handoff,
)

__all__ = [
    "parse",
    "main",
]


def parse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root")
    parser.add_argument("--ledger-root")
    parser.add_argument("--plan-id")
    commands = parser.add_subparsers(dest="command", required=True)
    init5_parser = commands.add_parser("init-v5")
    init5_parser.add_argument("--actor", required=True)
    init5_parser.add_argument("--approved", action="store_true")
    init5_parser.add_argument("--plan-file", required=True)
    init5_parser.add_argument("--assignments-file")
    init5_parser.add_argument("--capability-binding-file")
    init5_parser.add_argument("--host")
    init5_parser.add_argument("--evidence", default="")
    init5_parser.add_argument("--pin-roots", nargs="+", metavar="ROOT")
    trans = commands.add_parser("transition")
    trans.add_argument("--actor", required=True)
    trans.add_argument("--run-id")
    trans.add_argument("--step-id", required=True)
    trans.add_argument("--to", required=True)
    trans.add_argument("--agent-id", default="")
    trans.add_argument("--harness", default="")
    trans.add_argument("--model-or-alias", default="")
    trans.add_argument("--capability-binding-file", default="")
    trans.add_argument("--summary", default="")
    trans.add_argument("--retry", action="store_true")
    trans.add_argument("--retry-remediation-file", default="")
    trans.add_argument("--worktree-result", default="")
    dispatching = commands.add_parser("dispatch")
    dispatching.add_argument("--actor", required=True)
    dispatching.add_argument("--run-id", required=True)
    dispatching.add_argument("--step-id", required=True)
    dispatching.add_argument("--agent-id", default="")
    dispatching.add_argument("--harness", default="")
    dispatching.add_argument("--model-or-alias", default="")
    dispatching.add_argument("--capability-binding-file", default="")
    dispatching.add_argument("--summary", default="")
    dispatching.add_argument("--retry", action="store_true")
    dispatching.add_argument("--retry-remediation-file", default="")
    dispatching.add_argument("--create-from", default="")
    landing = commands.add_parser("land")
    landing.add_argument("--actor", required=True)
    landing.add_argument("--run-id", required=True)
    landing.add_argument("--step-id", required=True)
    landing.add_argument("--target", required=True)
    landing.add_argument("--summary", default="")
    amending = commands.add_parser("amend")
    amending.add_argument("--actor", required=True)
    amending.add_argument("--run-id", required=True)
    amending.add_argument("--step-id", required=True)
    amending.add_argument("--reason", required=True)
    amending.add_argument("--add-write", action="append", default=[])
    amending.add_argument("--add-read", action="append", default=[])
    amending.add_argument("--acceptance-command")
    amending.add_argument("--max-attempts", type=int)
    rec = commands.add_parser("record-return")
    rec.add_argument("--actor", required=True)
    rec.add_argument("--run-id")
    rec.add_argument("--return-file", required=True)
    sh = commands.add_parser("show")
    sh.add_argument("--run-id")
    sh.add_argument("--step-id", default="")
    sh.add_argument("--next-only", action="store_true")
    va = commands.add_parser("validate")
    va.add_argument("--run-id")
    va.add_argument("--closeout", action="store_true")
    worker_handoff = commands.add_parser("handoff")
    worker_handoff.add_argument("--run-id", required=True)
    worker_handoff.add_argument("--step-id", required=True)
    validate_return_parser = commands.add_parser("validate-return")
    validate_return_parser.add_argument("--handoff-file", required=True)
    validate_return_parser.add_argument("--return-file", required=True)
    check_parser = commands.add_parser("check-changeset")
    check_parser.add_argument("--handoff-file")
    check_parser.add_argument("--worktree")
    check_parser.add_argument("--base")
    check_parser.add_argument("--run-id")
    check_parser.add_argument("--step-id")
    acceptance_parser = commands.add_parser("run-acceptance")
    acceptance_parser.add_argument("--handoff-file")
    acceptance_parser.add_argument("--run-id")
    acceptance_parser.add_argument("--step-id")
    acceptance_parser.add_argument("--worktree")
    verify_parser = commands.add_parser("verify-handoff")
    verify_parser.add_argument("--actor", required=True)
    verify_parser.add_argument("--run-id", required=True)
    verify_parser.add_argument("--step-id", required=True)
    validate_verify_parser = commands.add_parser("validate-verify-return")
    validate_verify_parser.add_argument("--handoff-file", required=True)
    validate_verify_parser.add_argument("--return-file", required=True)
    record_verify_parser = commands.add_parser("record-verify")
    record_verify_parser.add_argument("--actor", required=True)
    record_verify_parser.add_argument("--run-id", required=True)
    record_verify_parser.add_argument("--return-file", required=True)
    record_verify_parser.add_argument("--parent-review", action="store_true")
    record_changeset_parser = commands.add_parser("record-changeset")
    record_changeset_parser.add_argument("--actor", required=True)
    record_changeset_parser.add_argument("--run-id", required=True)
    record_changeset_parser.add_argument("--step-id", required=True)
    commands.add_parser("list")
    close = commands.add_parser("close")
    close.add_argument("--actor", required=True)
    close.add_argument("--run-id", required=True)
    close.add_argument("--outcome", choices=("completed", "blocked", "abandoned"), required=True)
    close.add_argument("--reason", default="")
    close.add_argument("--series-handoff-file", default="")
    reopen = commands.add_parser("reopen")
    reopen.add_argument("--actor", required=True)
    reopen.add_argument("--run-id", required=True)
    reopen.add_argument("--reason", required=True)
    trace_init_parser = commands.add_parser("trace-init")
    trace_init_parser.add_argument("--actor", required=True)
    trace_init_parser.add_argument("--run-id", required=True)
    trace_record_parser = commands.add_parser("trace-record")
    trace_record_parser.add_argument("--actor", required=True)
    trace_record_parser.add_argument("--run-id", required=True)
    trace_record_parser.add_argument("--usage-file", required=True)
    trace_show_parser = commands.add_parser("trace-show")
    trace_show_parser.add_argument("--actor", required=True)
    trace_show_parser.add_argument("--run-id", required=True)
    trace_close_parser = commands.add_parser("trace-close")
    trace_close_parser.add_argument("--actor", required=True)
    trace_close_parser.add_argument("--run-id", required=True)
    garbage = commands.add_parser("gc")
    garbage.add_argument("--actor", default="")
    garbage.add_argument("--dry-run", action="store_true")
    purging = commands.add_parser("purge")
    purging.add_argument("--actor", required=True)
    purging.add_argument("--run-id", required=True)
    purging.add_argument("--before-retention", action="store_true")
    purging.add_argument("--reason", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = parse().parse_args(argv)
    try:
        if args.command == "init-v5":
            value = init5(args)
        elif args.command == "transition":
            value = transition_step(args)
        elif args.command == "dispatch":
            value = dispatch(args)
        elif args.command == "land":
            value = land(args)
        elif args.command == "amend":
            value = amend(args)
        elif args.command == "record-return":
            value = record(args)
        elif args.command == "show":
            value = show(args)
        elif args.command == "validate":
            value = validate(args)
        elif args.command == "handoff":
            value = handoff(args)
        elif args.command == "validate-return":
            value = validate_return(args)
        elif args.command == "verify-handoff":
            value = verify_handoff(args)
        elif args.command == "validate-verify-return":
            value = validate_verify_return(args)
        elif args.command == "record-verify":
            value = record_verify(args)
        elif args.command == "record-changeset":
            value = record_changeset(args)
        elif args.command == "check-changeset":
            value = check_changeset(args)
            return out(value, 0 if value["ok"] else 1)
        elif args.command == "run-acceptance":
            value = run_acceptance(args)
            return out(value, value["exit_code"])
        elif args.command == "list":
            value = list_runs(args)
        elif args.command == "close":
            value = close_run(args)
        elif args.command == "reopen":
            value = reopen_run(args)
        elif args.command == "trace-init":
            value = trace_init(args)
        elif args.command == "trace-record":
            value = trace_record(args)
        elif args.command == "trace-show":
            value = trace_show(args)
        elif args.command == "trace-close":
            value = trace_close(args)
        elif args.command == "gc":
            value = gc(args)
        else:
            value = purge(args)
        return out(value)
    except UsageError as exc:
        return out({"ok": False, "error": str(exc)}, 2)
    except Error as exc:
        return out({"ok": False, "error": str(exc)}, 3)
    except OSError as exc:
        return out({"ok": False, "error": f"I/O failure: {exc}"}, 4)
