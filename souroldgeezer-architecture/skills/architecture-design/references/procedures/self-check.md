# Dediren Self-Check

Run this before claiming runtime evidence.

## Select Runtime

Use the first executable that exists:

1. `souroldgeezer-architecture/tools/dediren-linux/bin/dediren`
2. `souroldgeezer-architecture/tools/dediren-macos/bin/dediren`

If neither exists, disclose `not run (missing dediren bundle)` and cap quality
at `source-valid` unless the user only asked for Lookup.

## Verify Bundle

Run:

```
<dediren> --version
jq . souroldgeezer-architecture/tools/<bundle>/bundle.json
```

Confirm the bundle declares the required plugins for the package:

- `generic-graph` for the current fixture projection;
- `elk-layout` for layout;
- `svg-render` for SVG evidence;
- `archimate-oef` only when optional export is requested.

## Evidence Commands

Run only the commands needed for the request:

```
<dediren> validate --input <package>/model.json
<dediren> project --input <package>/model.json --plugin <plugin> --view <view> --target <target>
<dediren> layout --plugin <plugin> --input <projection.json>
<dediren> validate-layout --input <layout.json>
<dediren> render --plugin svg-render --policy <package>/render-policy.json --metadata <package>/render-metadata.json --input <layout.json>
<dediren> export --plugin archimate-oef --policy <package>/export-policy.json --source <package>/model.json --layout <layout.json>
```

Every command returns an envelope. Treat error envelopes as findings and do not
claim the corresponding quality level.
