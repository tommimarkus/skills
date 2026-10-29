# lean-audit prevention hook — enablement recipe

<!-- lean-audit:sync-intentional: SKILL.md §"Prevention hook (opt-in)" carries a compact summary of this file. The summary is deliberate — collapsing it to a citation would force this 172-line recipe into every contract-awareness load, a net per-use loss. -->

The `lean-audit` engine backs an **opt-in** PreToolUse guard that soft-blocks an
edit which would introduce a **new block-severity duplication** into guarded
markdown. It ships **off** — installing the plugin does not enable enforcement.
Enable it deliberately, per this recipe.

Use this only after the plugin is installed and its script path is known in the
consumer project. Merge the chosen hook into existing configuration rather
than replacing other hooks. These commands run in the hook host's environment;
the payload describes the event, not a filesystem-access boundary.

## What it does

On Claude `Edit` / `Write` / `MultiEdit`, Codex `apply_patch`, or Antigravity `edit_file` / `write_file` to a guarded markdown surface (`CLAUDE.md`,
`AGENTS.md`, `README.md`, `**/SKILL.md`, `**/agents/*.md`, `docs/*-reference/**`,
`references/**`, `extensions/**`), `lean_guard.py` scores the edit's added text
against the repo's guarded-markdown corpus. On a `block`-severity hit it returns
`permissionDecision: deny` with the duplication target and an override hint.

It is **fail-open**: any engine error, timeout, missing file, non-repo path, or
non-guarded path → the edit is allowed. It adds no logic of its own — carve-outs
(built-in + `.lean-audit.toml`) and the `<!-- lean-audit:sync-intentional -->`
override are inherited from the engine.

**Interpreter (`uv` primary):** the guard needs Python ≥3.11 (`tomllib`). The
recipes below invoke it with `uv run`, which provisions or selects a conforming
interpreter even when the system `python3` is older; a `python3 …` command is an
alternative only where `python3` is already ≥3.11. Whichever you use, an
interpreter that is too old makes the shim exit 3 with a legible
`requires Python >=3.11` message — and because the guard is fail-open, the edit is
then simply allowed: the hook does not enforce until a conforming interpreter is
available.

## Override a block

When the hook denies an edit, do one of:
- **cite** the canonical source instead of restating it;
- **restructure** so the added prose is not a near-duplicate;
- add `<!-- lean-audit:sync-intentional: <reason> -->` to the duplicated block
  (intentional parallel structure the carve-outs don't yet cover);
- declare a `[[carve_out]]` or `exempt_paths` rule in `.lean-audit.toml`.

## Enable in Claude Code

Add to your project `.claude/settings.json` (or `~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "uv run \"/absolute/installed/plugin/path/skills/lean-audit/references/scripts/lean_guard.py\""
          }
        ]
      }
    ]
  }
}
```

> **About `${CLAUDE_PLUGIN_ROOT}`:** Claude Code substitutes this variable only
> in hook commands a plugin itself defines (it points at the plugin's install
> directory). A hook you add to your *own* `settings.json` is not plugin-owned,
> so substitute the real installed script path instead — find it via `/plugin`
> (the `souroldgeezer-audit` install path), e.g.
> `~/.claude/plugins/cache/<marketplace>/souroldgeezer-audit/<version>/skills/lean-audit/references/scripts/lean_guard.py`.
> That path changes when the plugin updates, so re-point it after an update (or
> point a stable env var at it in your shell profile and reference that).

## Enable in Codex

Add the same opt-in guard to project `.codex/hooks.json` (or user
`~/.codex/hooks.json`), substituting the real installed script path returned by
`codex plugin list --json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "uv run \"/absolute/installed/plugin/path/skills/lean-audit/references/scripts/lean_guard.py\""
          }
        ]
      }
    ]
  }
}
```

Codex maps the `Edit|Write` matcher aliases to its canonical `apply_patch`
event. The guard understands that event's patch command and checks each added
markdown block. `${PLUGIN_ROOT}` is available to plugin-bundled hooks, not to a
hook written in the consuming project's `.codex/hooks.json`; do not leave that
placeholder in this project-local recipe. Codex requires trust review for a new
or changed project hook.

---

# Reference, inventory, and cost notifications

`load_cost_guard.py` can compare reachable guidance with a diagnostic inventory.
Installing the plugin does not enable a consumer hook. This marketplace registers
only its nonblocking Stop form; generic architecture/IP prompts and automatic
lesson capture are removed.

## Inventory and reference behavior

- A pending Claude `Edit` / `Write` / `MultiEdit` that introduces a broken local
  reference can be denied by the optional edit guard.
- Missing inventoried codes or headings are advisory. A rename, refactor, or
  intentional policy retirement is not proof of semantic loss. Explain material
  behavior changes in the normal change rationale; no per-sentence preservation
  map or ritual baseline lowering is required.
- Cost increases are advisory and measured with the stable proxy, not a tokenizer.
  Pending-edit costs compare proposed content with current content; Stop costs
  compare the on-disk routes with the committed snapshot. Neither proves latency
  or model quality.
- Stop notices never block, invoke another skill, or authorize repairs. The Git
  diff may include pre-existing user changes; a read-only session may finish.
  Owning validation and publication checks retain responsibility for real defects.

The helper requires Python 3.11+. Missing tools, malformed events, unavailable
baselines, and errors fail open. It cannot verify meaning from names or counts.
Use behavior evidence for an obligation that matters to an actual consumer.
`skill_load_cost.py diff` reports inventory differences as advisory and exits 1
for broken local references; bad input remains exit 2. `baseline` and `snapshot`
retain their existing data formats. Regenerate diagnostic snapshots deliberately
when their declared routes change, using the documented snapshot command.

## Optional edit checks

Merge this into a consumer's existing Claude configuration only when requested:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [{"type": "command", "command": "uv run /absolute/installed/plugin/path/skills/lean-audit/references/scripts/load_cost_guard.py"}]
    }]
  }
}
```

Use the real installed absolute path. For Claude skill-body commands, resolve it
from `${CLAUDE_SKILL_DIR}`; Codex resolves `<skill-dir>` from the loaded source
path. Project-owned hooks use a real installed path rather than assuming plugin
variable substitution. The edit path handles the named Claude-shaped and Antigravity (`edit_file|write_file` in `.agents/hooks.json`) payloads;
do not claim `apply_patch` edit coverage from a matcher alias alone. Codex and Antigravity may also use
the nonblocking Stop form below.

## Nonblocking Stop notifications

For either host, merge the following command into its supported Stop hook
configuration, using the actual installed path:

```json
{
  "hooks": {
    "Stop": [{"hooks": [{
      "type": "command",
      "command": "uv run /absolute/installed/plugin/path/skills/lean-audit/references/scripts/load_cost_guard.py"
    }]}]
  }
}
```

The marketplace wrapper additionally checks interpreter availability. The guard
reads `cwd` from the event and does not execute hook text discovered in a target
repository. Notifications are observational; they cannot turn pre-existing changes
into the current task's write authority. Consumer hook enablement and host trust
review remain explicit choices.
