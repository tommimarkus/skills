# Skill self-check — required local references

Use this procedure before any Build / Extract / Review run. The skill advertises a contract that includes a bundled reference, several procedures, and two helper scripts; an installation that is missing any of them silently degrades the contract. The self-check turns silent degradation into explicit disclosure: missing tooling is named in the footer, and the affected verification is reported as "not run" with the exact blocker, not skipped over.

## When this procedure runs

- **Build mode step 0 (Dispatch)** — before announcing the diagram kind, layer scope, and change classification.
- **Extract mode step 0 (Dispatch)** — before running the discovery pass.
- **Review mode step 0 (Dispatch)** — before identifying the artefact / drift / render sub-behaviour.

The Skill tool that loaded `SKILL.md` does not auto-inject this file. `Read` it explicitly before invoking it, the same way the rest of the procedures are loaded.

## Required references

| Path (relative to skill directory) | Required for |
|---|---|
| `../../docs/architecture-reference/architecture.md` | All modes — bundled reference prose; `model-valid` / `diagram-readable` / `review-ready` definitions; ArchiMate® 3.2 §/Appendix B citations |
| `references/smell-catalog.md` | All modes — code-to-section index for every `AD-*` / `AD-Q*` / `AD-L*` / `AD-B-*` / `AD-DR-*` finding |
| `references/red-flags.md` | All modes — stop-condition list before delivering |
| `references/output-format.md` | All modes — per-view readiness matrix, footer skeleton |
| `references/procedures/professional-readiness.md` | Build / Extract final pass; Review artefact pass — readiness verdict; authority derivation; `AD-Q*` emission |
| `references/procedures/layout-strategy.md` | Build / Extract — backend-neutral geometry orchestration and readiness handoff |
| `references/procedures/layout-backend-contract.md` | Build / Extract — normalized geometry request/result contract for backends and fallback |
| `references/procedures/layout-policies-by-viewpoint.md` | Build / Extract — viewpoint-specific visual grammar and backend selection policy |
| `references/procedures/routing-and-glossing.md` | Build / Extract and route repair — port-aware routing, route-only repair, and post-route glossing |
| `references/procedures/layout-fallback.md` | Build / Extract when no suitable backend is available — deterministic fallback layout |
| `references/procedures/process-view-emission.md` | Build / Extract when Business Layer in scope — §9.7 / §9.3 view emission contract |
| `references/procedures/seed-views.md` | Extract when forward-only stubs emitted — Capability Map / Motivation seed views |
| `references/procedures/lifting-rules-dotnet.md` | Extract when .NET sources present — Application Layer lifting |
| `references/procedures/lifting-rules-bicep.md` | Extract when Bicep present — Technology Layer lifting |
| `references/procedures/lifting-rules-gha.md` | Extract when GitHub Actions present — Implementation & Migration lifting |
| `references/procedures/lifting-rules-process.md` | Extract when Durable Functions / Logic Apps present — Business Process / Event / Interaction lifting |
| `references/procedures/drift-detection.md` | Review drift sub-behaviour |
| `references/scripts/validate-oef-layout.sh` | Build / Extract final self-check; Review artefact pass — executable source-geometry gate |
| `references/scripts/archi-render.sh` | Review render request, render-polish loop — weak dependency (Archi + `DISPLAY` required) |

## Self-check steps

1. **Verify required reference files exist.** For each path in the *Required references* table whose row applies to the current mode, run a single existence check. Use the agent's file-reading tool (in Claude Code: `Read`; in Codex: equivalent) — do not rely on listing the directory and inferring presence.

2. **Verify executable scripts are present and runnable.** For each `*.sh` script in the *Required references* table whose row applies, confirm the file is present and that the executable bit is set. If the executable bit is missing, report it as a degraded-mode condition rather than silently invoking through `bash <path>`.

3. **Verify weak dependencies are functional.** For `archi-render.sh`, additionally check Archi (or the configured renderer binary), `DISPLAY` availability, and `xmllint` only when render is in scope for the current run (Review render sub-behaviour, render-polish loop, or Build / Extract with `[visual]` self-check requested). Missing dependencies do not block the run; they downgrade visual render inspection to "not run" with the exact blocker.

4. **Record the self-check outcome.** Build the self-check block for the footer:
   ```
   Self-check (skill tooling):
     Reference files:        present <n>/<n> | degraded (<missing path list>)
     Procedures:             present <n>/<n> | degraded (<missing path list>)
     Scripts:                present <n>/<n>, executable <m>/<n> | degraded (<missing or non-executable path list>)
     Weak dependencies:      archi-render.sh: <runnable | not run (<blocker>)>
   ```
   Add this block to the standard footer (`output-format.md` §Footer) ahead of `Project assimilation:`.

5. **Apply the degradation policy.** When a file in the table is missing or a script is not executable, the affected verification is reported as "not run" with the exact blocker — never as "passed". Specifically:
   - Missing `architecture.md` → cannot perform any reference citation; Build / Extract refuse. Review reports "skill installation incomplete; reference missing" and stops.
   - Missing `smell-catalog.md` → emit findings using the `AD-*` codes from prior knowledge but flag "code-to-section index unavailable; verify codes against `architecture.md` §8".
   - Missing any `references/procedures/*.md` whose row applies → that procedure's behaviour is reported as "not run (procedure file missing: <path>)". The affected output (forward-only stubs, layout, lifted layers, drift findings, etc.) is omitted from the run, not faked.
   - Missing `validate-oef-layout.sh` or non-executable → source-geometry gate reports "not run (script missing | non-executable)"; Build / Extract cannot claim per-view readiness above `model-valid` for any view that would have been gated.
   - Missing `archi-render.sh` or weak dependencies missing → visual render inspection reports "not run (blocker)"; render-polish loop refuses.

6. **Disclose, don't silently degrade.** The degraded conditions go in the footer and (when they affect findings) in the per-finding output as `evidence: "<verification> not run: <blocker>"`. The skill never claims a check passed when its required tool was absent.

## Why this matters

The skill's outputs are trusted because each finding cites a deterministic source — a reference section, a smell catalog row, a script's executable result. When one of those sources is silently missing, a finding can look authoritative while resting on the agent's recollection rather than the bundled reference. The self-check makes that condition visible: the architect reading the footer sees "Procedures: present 8/9 (missing: drift-detection.md)" and knows the absence of drift findings means the procedure didn't run, not that the model is drift-clean.

## Failure modes the self-check catches

- A runtime that loads `SKILL.md` from cache while the bundled procedure files were not synced.
- A locally-customised installation where the architect renamed or moved a procedure file.
- A renderer install that succeeded for the binary but lacks `DISPLAY` (headless CI without `xvfb-run`).
- A script whose executable bit was lost in a fresh checkout (Windows host writing into a Linux-mounted volume).
- A skill update that added a new procedure but the user has the prior plugin version cached.

## What this procedure does not do

- **Validate procedure content.** It checks file presence, not whether the content matches a particular plugin version. A version mismatch is out of scope; the architect detects that via plugin version reporting.
- **Auto-install missing dependencies.** It reports blockers; the architect installs Archi, sets `DISPLAY`, or fixes the executable bit.
- **Replace the source-geometry gate or render inspection.** Those are separate verifications; the self-check confirms their tools exist and are runnable.
