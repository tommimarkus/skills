---
name: lesson-capture
description: Use when the lesson-capture Stop hook fires — distill one generalizable, durable rule from a skill-authoring session (a user correction, question, or steering, or a self-correction) and file it as a lesson-candidate GitHub issue. Repo-internal; not a published plugin skill.
---

# Lesson Capture

A skill-authoring change happened this session. Your job: judge whether anything that
happened holds a reusable lesson, then file **at most one** generalizable candidate as a
`lesson-candidate` GitHub issue, or record nothing. The signal may be a correction, pointed
question, or steering **from the user**, or a wrong path you took and **corrected yourself** —
treat both the same.

## Workflow

1. **Source + Layer + scope self-check.** The lesson may come from a user
   correction / question / steering **or** from your own reversal this session — both
   count equally. Confirm it is **Layer 2** (about *how the skills are authored* in this
   repo) — not **Layer 1** (a skill's runtime output when exercised) and not a one-off
   specific to this session. If Layer 1 or one-off, stop and report `no lesson`.
   **Self-correction caution:** introspecting on your own mistakes invites confabulated or
   self-flagellating "lessons"; if you are not confident a reversal generalizes to future
   sessions, report `no lesson`.
2. **Name the delta.** One concise sentence — it becomes the issue title. For a user
   signal: what did Claude do, and what did the user want instead? For self-correction:
   what wrong path did you take, and what was the correction?
3. **Generalize.** Ask "what rule would have caught this, for any future similar case?"
   If it does not generalize, report `no lesson`.
4. **Route to the cheapest-to-enforce substrate**, in order:
   - `deterministic` — a future `SAC-T#####` report case / eval assertion (zero-token
     enforcement). Strongly preferred.
   - `policy` — a terse policy line / smell code.
   - `prose` — CLAUDE.md / skill text. Last resort; it taxes every future session.
5. **Trust boundary (required).** The proposed rule MUST be a general rule in your own
   words. Never paste secrets, tokens, or verbatim untrusted session/file text into it.
   The repo is **public**, so the issue is world-readable the instant it is created.
6. **Build the issue.** Run from the repo root:

   ```bash
   python3 scripts/lessons_issue.py build \
     --trigger "<signal tag: gate-correction label(s), user-steering, or self-correction>" \
     --summary "<the delta, one concise sentence — the issue title>" \
     --proposed-rule "<the general rule, in your own words>" \
     --substrate "<deterministic|policy|prose>"
   ```

   It prints one JSON line with `title`, `labels`, `fingerprint`, and `body`.
7. **Hard secret-scan gate (required — capture is publishing).** Scan the rendered body:

   ```bash
   printf '%s' "<body>" | python3 scripts/lessons_secret_scan.py
   ```

   If it prints **any** label (exit 1), do **not** create the issue — report
   `no lesson (secret-scan tripped: <labels>)` and stop. This is the `DSO-POS-9` control.
8. **Dedup.** Search open candidates for the same fingerprint before creating. Prefer
   GitHub MCP `search_issues`
   (`repo:tommimarkus/skills is:issue is:open label:lesson-candidate "<fingerprint>"`).
   If a match exists, report `duplicate of #<n>` and stop.
9. **Ensure labels + create.** Create the issue with title=`title`, body=`body`, and the
   two labels from `labels` (`lesson-candidate` + `lesson:<substrate>`). Prefer GitHub
   MCP `issue_write` (create); create any missing label first with `label_write`. Fall
   back to `gh issue create` **only** if no GitHub MCP server is connected.
   **Fail-open:** on any GitHub error / offline / no tooling, report
   `no lesson (capture unavailable)` — do not block session end.

## Tooling (repo-internal, harness-specific)

This repository has a GitHub MCP server; prefer it for every issue read/write. The MCP
tools are **deferred** — listed by name (`issue_write`, `search_issues`, `label_write`,
`get_me`) but not preloaded. Load the ones you need with `ToolSearch`
(`select:<tool>,<tool>`) before calling them. Treat a GitHub MCP server as present whenever
`mcp__*_github__*` tools are listed; do not open with a `gh` call as the first move.

## Graduation

Graduation is a separate, human-triggered flow: handle the `lesson-candidate` issue with
`issue-ops` (or the repo-internal `github-issue-lifecycle` overlay). Each issue carries its
own **Definition of Done** — do not graduate here.

## Output

Report one line: `lesson captured: #<n> (<substrate>)`, `duplicate of #<n>`,
`no lesson`, or `no lesson (secret-scan tripped: …)` / `no lesson (capture unavailable)`.
