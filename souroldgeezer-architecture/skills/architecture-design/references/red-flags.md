# Architecture Design Red Flags

Stop or lower readiness when:

- missing package source, policy, metadata, plugin, view id, or generated input;
- duplicate ids, dangling relationships, invalid types, stale evidence;
- unprojectable view or omitted meaningful relationship;
- layout failure, overlap, connector-through-node, invalid route, group-boundary warning;
- blank/bad SVG, missing dediren markers, bad `viewBox`;
- drift from source/IaC/UI/API/workflows;
- missing/failed OEF export policy or unresolved downstream export findings;
- `review-ready` with a block, dense/incoherent view, placeholder view, or
  render-ready claim from source inspection alone.
