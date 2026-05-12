# Architecture Design Red Flags

Stop or lower readiness when:

- missing package source, policy, metadata, plugin, view id, or generated input;
- duplicate ids, dangling relationships, invalid relationship types, or stale
  evidence (`ARCH-M-*`);
- view cannot project or omits the meaningful relationship (`ARCH-V-*`);
- layout fails or validates with overlap, connector-through-node, invalid route,
  or group-boundary warnings (`ARCH-L-*`);
- SVG fails, is blank, lacks dediren markers, or has bad `viewBox` (`ARCH-R-*`);
- extracted facts drift from source/IaC/UI/API/workflows (`ARCH-X-*`);
- requested OEF export is missing policy, fails, or has unresolved downstream
  findings (`ARCH-E-*`);
- `review-ready` is claimed with a block, or view is dense/incoherent
  (`ARCH-Q-*`).

No placeholder views. No render-ready claim from source inspection alone.
