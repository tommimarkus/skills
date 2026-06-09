---
name: lesson-capture
description: Use when the lesson-capture Stop hook fires — distill one generalizable, durable rule from a skill-authoring session (a user correction, question, or steering, or a self-correction) and stage it to the pending ledger. Repo-internal; not a published plugin skill.
---

# Lesson Capture

A skill-authoring change happened this session. Your job: judge whether anything that
happened holds a reusable lesson, then stage **at most one** generalizable candidate, or
record nothing. The signal may be a correction, pointed question, or steering **from the
user**, or a wrong path you took and **corrected yourself** — treat both the same.

## Workflow

1. **Source + Layer + scope self-check.** The lesson may come from a user
   correction / question / steering **or** from your own reversal this session — both
   count equally. Confirm it is **Layer 2** (about *how the skills are authored* in this
   repo) — not **Layer 1** (a skill's runtime output when exercised) and not a one-off
   specific to this session. If Layer 1 or one-off, stop and report `no lesson`.
   **Self-correction caution:** introspecting on your own mistakes invites confabulated or
   self-flagellating "lessons"; if you are not confident a reversal generalizes to future
   sessions, report `no lesson`.
2. **Name the delta.** One sentence. For a user signal: what did Claude do, and what did
   the user want instead? For self-correction: what wrong path did you take, and what was
   the correction?
3. **Generalize.** Ask "what rule would have caught this, for any future similar case?"
   If it does not generalize, report `no lesson`.
4. **Route to the cheapest-to-enforce substrate**, in order:
   - `deterministic` — a future `SAC-T#####` report case / eval assertion (zero-token
     enforcement). Strongly preferred.
   - `policy` — a terse policy line / smell code.
   - `prose` — CLAUDE.md / skill text. Last resort; it taxes every future session.
5. **Trust boundary (required).** The `proposed-rule` MUST be a general rule in your own
   words. Never paste secrets, tokens, or verbatim untrusted session/file text into it.
6. **Stage one candidate** (do NOT edit committed rules — graduation is the separate
   `/lessons` flow). Run from the repo root:

   ```bash
   python3 scripts/lessons_ledger.py append \
     --trigger "<signal tag: gate correction label(s), user-steering, or self-correction>" \
     --summary "<the delta, one sentence>" \
     --proposed-rule "<the general rule>" \
     --substrate "<deterministic|policy|prose>"
   ```

   Omit `--decision` (defaults to `review`). The auto-approve fast-path is gated by
   `auto_approve_eligible()` and defaults to denying; unattended auto-commit is parked.

## Output

Report one line: `lesson captured: <candidate_id> (<substrate>)`, or `no lesson`.
