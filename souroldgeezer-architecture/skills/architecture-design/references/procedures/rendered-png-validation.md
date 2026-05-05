# Rendered PNG validation

Use this procedure after `archi-render.sh` has produced PNGs for an OEF model
and the user asked for rendered-view quality, visual inspection, or render
comparison. OEF remains the architecture source of truth; PNG validation is a
derived-artifact quality gate.

`archi-render.sh` validates the loaded model before producing PNGs: after
`xmllint --noout` and Archi XML Exchange import, it runs the bundled
`validate-model.ajs` jArchi script. Any `ARCHI_VALIDATE_MODEL: INVALID` finding
is a render blocker. `ARCHI_VALIDATE_MODEL: WARN` findings are surfaced without
failing PNG generation. The wrapper must see at least one
`ARCHI_VALIDATE_MODEL:` marker from the script; if no marker is produced, treat
the run as "Validate Model did not run" even when Archi still renders PNGs.
Those warnings should be triaged through `external-validation-handoff.md` before
readiness is claimed.

## Required runtime

The shipped validator is Java™ ImageIO-based and runs through:

```bash
references/scripts/arch-layout.sh validate-png --image <rendered.png> --result <rendered-png-result.json>
```

Use a baseline when comparing an existing render:

```bash
references/scripts/arch-layout.sh validate-png --image <rendered.png> --baseline <prior.png> --tolerance 0.03 --result <rendered-png-result.json>
```

ImageMagick may be used manually for richer diagnostics, but it is optional.
Do not make test or runtime acceptance depend on ImageMagick being installed.

## Validation signals

The validator reports:

- width and height;
- color diversity;
- blank or near-blank classification;
- tiny-image classification;
- non-background bounding box;
- cropped-to-edge signal;
- excessive-whitespace warning; and
- changed-pixel ratio for same-size baseline comparison.

Dimension mismatch fails baseline comparison unless the user explicitly accepts
the size change. Exact full-image snapshots are brittle; prefer tolerance-based
comparison plus invariant checks.

## Readiness impact

- Blank, tiny, cropped-to-edge, unreadable, or over-tolerance PNG output caps
  changed views at `model-valid` for visual-quality runs.
- Excessive whitespace is a warning unless it hides the architecture story.
- A passing PNG validation does not replace OEF source-geometry validation:
  always run `validate-oef-layout.sh` first when a local OEF path is available.

## Render chaining

Typical sequence:

```bash
references/scripts/validate-oef-layout.sh docs/architecture/<feature>.oef.xml
references/scripts/archi-render.sh docs/architecture/<feature>.oef.xml --output-root .cache/archi-views
references/scripts/arch-layout.sh validate-png --image .cache/archi-views/<feature>/<view>.png --result .cache/archi-views/<feature>/<view>.png.json
```

If Archi, jArchi script support, `DISPLAY`, `xmllint`, `validate-model.ajs`,
Validate Model marker output, or another render prerequisite is missing, report
render and PNG validation as not run with the exact blocker.
