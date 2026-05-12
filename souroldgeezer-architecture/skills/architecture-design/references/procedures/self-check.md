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

Required plugins: `generic-graph`, `elk-layout`, `svg-render`; add
`archimate-oef` only for export. Run only needed commands:

```
<dediren> validate --input <package>/model.json
<dediren> project --input <package>/model.json --plugin <plugin> --view <view> --target <target>
<dediren> layout --plugin <plugin> --input <projection.json>
<dediren> validate-layout --input <layout.json>
<dediren> render --plugin svg-render --policy <package>/render-policy.json --metadata <package>/render-metadata.json --input <layout.json>
<dediren> export --plugin archimate-oef --policy <package>/export-policy.json --source <package>/model.json --layout <layout.json>
```

Every command returns an envelope. Error envelopes are findings and block that
quality level.
