# architecture-design fixtures

Small ArchiMate® OEF XML files exercising each §9 viewpoint at representative scale (8–15 elements, 10–20 relationships). Fixtures are regression targets for the Sugiyama-v1 layout engine: each fixture's element + relationship set is the input the skill operates on; the rendered PNG output is the validation artefact.

## How fixtures are used

1. Build mode invokes the skill with the fixture's element / relationship set as architect intent.
2. Tier 0 finds no prior view at the canonical path → all elements get algorithmic placement.
3. Tier 1 (Phases 1–6) + Tier 2 (per-viewpoint specialisation) compute coordinates.
4. The skill writes the resulting OEF.
5. `archi-render.sh` (in a consuming project, dev-time only) renders the OEF to PNG.
6. Visual inspection against the per-viewpoint acceptance bar (see spec §6.2 of `docs/superpowers/specs/2026-04-25-architecture-design-pro-quality-design.md`).

## Render

```bash
# From a project with archi-render.sh installed (e.g. lfm-org/lfm)
cd /path/to/lfm
./scripts/archi-render.sh /path/to/architecture-design/references/fixtures/<fixture>.oef.xml
ls /path/to/lfm/.cache/archi-views/<fixture>/
```

## Fixtures

| Fixture | Viewpoint | Elements | Why |
|---|---|---|---|
| `service-realization.oef.xml` | §9.3 Service Realization | ~7 | Process-rooted modality (user-driven): Business Actor → Process → App Service → UI App Component + Interface, with backend App Component on a Tech Node |
| `motivation.oef.xml` | §9.6 Motivation | ~8 | Stakeholder → Driver → Goal → Outcome → Requirement → Constraint tree |
| `business-process-cooperation.oef.xml` | §9.7 Business Process Cooperation | ~8 | Lane-based process flow with Triggering chain |
| `professional-quality-cases.md` | AD-Q expectations | n/a | Pressure cases for the professional-readiness pass: inventory views, thin process / service-realization views, orphaned decision context, and ambiguous labels |

(§9.1, §9.2, §9.4, §9.5 are covered by `lfm-org/lfm/docs/architecture/lfm.oef.xml`.)

## Acceptance bar

A fixture is "production-ready" when all three pass on the rendered PNG:

1. **Mechanical (auto-checkable):** zero AD-L1 / L2 / L3 / L9 / L11 findings at severity `warn`; AD-L4 within budget; AD-L5 within `n/6` crossings; AD-L8 grid-aligned; AD-L10 normalised origin within tolerance.
2. **Visual (human judgment):** matches the per-viewpoint idiom in `layout-strategy.md` Tier 2; reads at the quality bar of the [Hosiaisluoma ArchiMate examples gallery](https://www.hosiaisluoma.fi/blog/archimate-examples/).
3. **Deterministic:** re-running Build on the same input produces byte-identical OEF.
