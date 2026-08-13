# Dediren Fixture Render Policies

The five `render-policy*.json` files in `basic/`, `mixed/`, and `rendered/`
mirror Dediren 2026.08.3's notation-aware reference resources exactly:

- ArchiMate policies mirror
  `dediren://fixture/render-policy/archimate-svg.json`.
- UML policies mirror `dediren://fixture/render-policy/uml-svg.json`.

These files are compatibility fixtures, not a local visual theme. Do not add
local palette, stroke, marker, margin, or other visual overrides. When the
repository's Dediren compatibility baseline changes, refresh every policy from
the live MCP resources and keep the exact-parity regression green.

The mirrored policies retain the Dediren contributors' MIT notice in the
architecture plugin's [third-party notices](../../../../../THIRD-PARTY-NOTICES.md).
