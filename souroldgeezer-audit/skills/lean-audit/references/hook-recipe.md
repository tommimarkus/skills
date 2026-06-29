# lean-audit prevention hook — enablement recipe

The `lean-audit` engine backs an **opt-in** PreToolUse guard that soft-blocks an
edit which would introduce a **new block-severity duplication** into guarded
markdown. It ships **off** — installing the plugin does not enable enforcement.
Enable it deliberately, per this recipe.

## What it does

On `Edit` / `Write` / `MultiEdit` to a guarded markdown surface (`CLAUDE.md`,
`AGENTS.md`, `README.md`, `**/SKILL.md`, `**/agents/*.md`, `docs/*-reference/**`,
`references/**`, `extensions/**`), `lean_guard.py` scores the edit's added text
against the repo's guarded-markdown corpus. On a `block`-severity hit it returns
`permissionDecision: deny` with the duplication target and an override hint.

It is **fail-open**: any engine error, timeout, missing file, non-repo path, or
non-guarded path → the edit is allowed. It adds no logic of its own — carve-outs
(built-in + `.lean-audit.toml`) and the `<!-- lean-audit:sync-intentional -->`
override are inherited from the engine.

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
            "command": "python3 \"$CLAUDE_PLUGIN_ROOT/skills/lean-audit/references/scripts/lean_guard.py\""
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
> `~/.claude/plugins/cache/<marketplace>/souroldgeezer-audit/skills/lean-audit/references/scripts/lean_guard.py`.
> That path changes when the plugin updates, so re-point it after an update (or
> point a stable env var at it in your shell profile and reference that).

## Enable in Codex

Codex has no at-edit pre-tool hook yet (true at-edit parity is future scope), so
run the same engine at the **Stop** hook over the session's changed markdown and
surface a prompt. Add a `Stop` command to `.codex/hooks.json` that runs the
engine on the repo and prompts when it exits non-zero:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/skills/lean-audit/references/scripts/lean_engine.py" . --format json
# exit 1 == a block-severity duplication is present — prompt the agent to run
# the lean-audit skill and cite or mark it before finishing.
```

> **Codex plugin paths:** Codex exposes `$PLUGIN_ROOT` natively and also sets
> `$CLAUDE_PLUGIN_ROOT` for compatibility (there is no `$CODEX_PLUGIN_ROOT`). As
> in Claude Code these resolve in plugin-defined hooks; for a manual
> `.codex/hooks.json` entry, substitute the installed `lean_engine.py` path
> directly (resolve it via your Codex plugin install location, or a stable env
> var) just as in the Claude Code note above.

This is advisory (a Stop prompt), not an at-edit block. Until at-edit Codex
parity ships, Codex relies on this end-of-session check plus the `lean-audit`
skill run.

---

# lean-audit per-use cost guard — enablement recipe

The `lean-audit` engine backs an **opt-in** per-use cost guard (`load_cost_guard.py`)
that defends a skill's **fidelity floor** and warns on **cost regressions**. It ships
**off** — installing the plugin does not enable enforcement. Enable it deliberately,
per this recipe.

## What it does

On `Edit` / `Write` / `MultiEdit` to any `.md` file in a skill's Load-Map closure,
`load_cost_guard.py` applies the session's diff against the skill's fidelity baseline:

- **Fidelity block (deny):** if the edit would make an inventoried smell code or
  reference section unreachable in the skill's closure — dropping an item below the
  baseline floor — it returns `permissionDecision: deny` and names the lost item.
  The fidelity floor must hold.
- **Cost advisory (allow):** if the fidelity check passes but the current on-disk
  closure is measurably heavier than the `cost-snapshot.json` baseline for affected
  scenarios (tolerance: 200 tokens), it returns an advisory `permissionDecision: allow`
  with a warning message. At Stop time the on-disk closure is the post-edit state
  (accurate); at PreToolUse time it reflects pre-edit drift since the last snapshot.
  Cost warnings are informational — they never block.

It is **fail-open**: any engine error, non-`.md` file, path outside every skill's
closure, missing baseline, missing patterns file, or exception → the edit is allowed
silently. It adds no judgment logic — inventory and closure come from the engine.

## Override a block

When the guard denies an edit, do one of:
- **Restructure** so the removed item is still reachable in the closure (move, not
  delete);
- **Cite** the item's smell code in prose rather than removing the section entirely;
- if the loss is intentional (deliberate removal of a code that no longer applies),
  update the fidelity baseline
  (`tests/skill_load_cost/baselines/<skill-name>.json`) to reflect the new floor
  before editing.

## Enable in Claude Code — Stop hook (default)

At session end the guard runs over all skill closure files changed in the session.
This is the **recommended** enablement form — it adds no per-edit latency, and the
on-disk closure at Stop time IS the post-edit state, so cost measurement is accurate.

Add to your project `.claude/settings.json` (or `~/.claude/settings.json`):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PLUGIN_ROOT/skills/lean-audit/references/scripts/load_cost_guard.py\""
          }
        ]
      }
    ]
  }
}
```

> **About `${CLAUDE_PLUGIN_ROOT}`:** same note as the lean_guard recipe — Claude Code
> substitutes this variable only in plugin-defined hook commands. For a hook you add
> to your own `settings.json`, substitute the real installed path — find it via
> `/plugin` (the `souroldgeezer-audit` install path), e.g.
> `~/.claude/plugins/cache/<marketplace>/souroldgeezer-audit/skills/lean-audit/references/scripts/load_cost_guard.py`.
> Re-point it after a plugin update.

## Enable in Claude Code — PreToolUse opt-in (at-edit)

For immediate at-edit blocking, add a `PreToolUse` hook instead:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PLUGIN_ROOT/skills/lean-audit/references/scripts/load_cost_guard.py\""
          }
        ]
      }
    ]
  }
}
```

This intercepts every edit at the moment it is applied. Use this form when you want
to block fidelity regressions in-flight rather than at session close. Note that
closure resolution adds per-edit latency; the Stop hook form avoids this. The
cost-warn advisory at PreToolUse time reflects current on-disk drift since the last
snapshot (pre-edit), not the pending edit's marginal cost — use the Stop hook for
accurate post-edit cost measurement.
