---
name: lesson-capture
description: Use when the lesson-capture Stop hook fires — distill one generalizable, durable rule from a skill-authoring correction and stage it to the pending ledger. Repo-internal; not a published plugin skill.
---

# Lesson Capture

The deterministic gate already found a skill-authoring change plus a correction signal
this session. Your job: stage **at most one** generalizable lesson, or record nothing.

## Workflow

1. **Layer + scope self-check.** Confirm the correction was **Layer 2** (about *how the
   skills are authored* in this repo) — not **Layer 1** (about a skill's runtime output
   when exercised) and not a one-off specific to this session. If Layer 1 or one-off,
   stop and report `no lesson`.
2. **Name the delta.** What did Claude do, and what did the user want instead? One sentence.
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
     --trigger "<correction-label(s) from the gate>" \
     --summary "<the delta, one sentence>" \
     --proposed-rule "<the general rule>" \
     --substrate "<deterministic|policy|prose>"
   ```

   Omit `--decision` (defaults to `review`). The auto-approve fast-path is not enabled
   until Plan 3 ships its template-synthesis + secret-scan controls.

## Output

Report one line: `lesson captured: <candidate_id> (<substrate>)`, or `no lesson`.
