---
name: lessons
description: Use when the user runs /lessons or asks to review captured lesson candidates — review pending lessons and graduate approved ones into committed rules. Repo-internal; runs on main only.
---

# Lessons Review

Review the candidates captured by the lesson-capture hook and graduate the good ones
into committed rules. Graduation writes committed files, so this runs on `main` only.

## Workflow

1. **Guard.** If the current branch is not `main`, stop and tell the user to switch to
   `main` first (graduation must stay on one branch — see the lesson-loop spec). Check:
   `git rev-parse --abbrev-ref HEAD`.
2. **List pending candidates:** `python3 scripts/lessons_ledger.py list --pending`.
   If none, report `no pending lessons` and stop.
3. **For each candidate**, show the user its `trigger`, `summary`, `proposed_rule`, and
   `substrate`, and ask: approve / edit / reject.
4. **On reject:** `python3 scripts/lessons_ledger.py resolve --id <candidate_id> --status rejected --note "<why>"`.
5. **On approve**, apply the rule to its substrate, keeping it a **general rule in clean
   words** (trust boundary: never commit secrets or verbatim untrusted session text):
   - `prose` / `policy` — with the user, place the rule where it belongs (a `CLAUDE.md`
     line, a policy/reference line, a skill instruction). Prefer the most-specific home.
   - `deterministic` — only if the report engine **already** detects this smell, add a
     fixture case via `tests/generate_skill_architecture_report_ledger.py` and regenerate
     the ledger (never hand-edit `tests/skill_architecture_report_ledger.jsonl`). If it
     needs **new** detection, do not fake a test: record the proposed check for the user
     as engine work, and either reroute to `policy`/`prose` for now or leave it pending.
   - **Secret-scan gate (required before committing any graduation).** Stage the change,
     then run `git diff --cached | python3 scripts/lessons_secret_scan.py --diff`. If it
     prints any label (exit 1), do NOT commit — unstage, report what tripped, and keep the
     candidate pending. This is the `DSO-POS-9` control and applies to every lesson.
   Then mark it: `python3 scripts/lessons_ledger.py resolve --id <candidate_id> --status applied --note "<where it landed>"`.
6. **Verify** nothing broke: run `uv run python -m unittest` for any touched test module
   and `bash scripts/skill-architecture-report.sh .` when a skill surface changed.
7. **Stamp/sync if a published `souroldgeezer-*` surface changed** (CalVer + manifest/
   marketplace/README sync + IP-hygiene), per `CLAUDE.md`. Repo-internal edits need no stamp.

## Auto-approve lane (default-deny)

Candidates marked `auto-approved` are checked by `auto_approve_eligible()` (deterministic
substrate + allowlisted change-class + not already graduated). The change-class allowlist
(`AUTO_APPROVE_CHANGE_CLASSES`) is **empty by default**, so nothing skips human review yet —
unattended commit waits on a template-synthesizable fixture path (lesson-loop Plan 4
"Parked"). Treat every candidate as review until that lands.

## Output

Report a summary: how many approved/applied, where each landed, how many rejected, and
any deterministic lessons deferred as engine work.
