# Dediren Self-Check

Run before runtime claims. Use the first executable that exists:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

If neither exists, disclose `not run (missing dediren bundle)` and cap quality
at `source-valid` unless Lookup only.

Verify:

```
<dediren> --version
jq . souroldgeezer-architecture/tools/<bundle>/bundle.json
```

The selected bundle is an imported upstream Dediren artifact. Use it as runtime
evidence, but do not patch files under `tools/dediren-linux/` or future platform
bundle directories to fix tool behavior. If self-check exposes a runtime,
schema, plugin, helper, render, layout, or export defect, report it under
`Dediren tool issues` with version, command, input summary, envelope/error,
expected behavior, and repro evidence. Keep issue-filing mechanics in
agent-local configuration.

Required plugins: `generic-graph`, `elk-layout`, `svg-render`; add
`archimate-oef` only for export. Run only needed commands:

Plain `validate` proves schema shape only. A `source-valid` claim requires
plain `validate` plus `validate --plugin generic-graph --profile archimate`.
Projection and requested export evidence remain separate downstream gates for
view and export readiness.

Generate render metadata per view before rendering when `project.json` declares
a `metadata` target. Run `layout --plugin elk-layout` serially for each view;
parallel ELK layout invocations can produce invalid JSON envelopes in the
current packaged runtime even when the same inputs pass serially.

```
<dediren> validate --input <package>/model.json
<dediren> project --input <package>/model.json --plugin <plugin> --view <view> --target <target>
<dediren> project --input <package>/model.json --plugin generic-graph --view <view> --target render-metadata
<dediren> layout --plugin <plugin> --input <projection.json>
<dediren> validate-layout --input <layout.json>
<dediren> render --plugin svg-render --policy <package>/render-policy.json --metadata <render-metadata.json> --input <layout.json>
<dediren> export --plugin archimate-oef --policy <package>/export-policy.json --source <package>/model.json --layout <layout.json>
```

Every command returns an envelope. Error envelopes are findings and block that
quality level.
