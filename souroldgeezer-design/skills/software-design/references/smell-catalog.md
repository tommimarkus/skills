# Software Design Smell Catalog

Use with [../../../docs/software-reference/software-design.md](../../../docs/software-reference/software-design.md).
Findings cite code, evidence, smallest action, verification layer, and
reference section. Raise severity for new/load-bearing code; lower it when
evidence is partial or a local rule explains the tradeoff.

| Family | Codes | Signal |
|---|---|---|
| Waste | `SD-W-1..6` | speculative interfaces/frameworks/hooks, pass-through layers, repeated models, ceremony over current change |
| Boundary | `SD-B-1..6` | responsibility drift, folder-type boundaries, internals leakage, hidden mutable state, misplaced policy, adapter-owned workflow |
| Coupling | `SD-C-1..6` | cycles, boundary inversion, shared-core gravity, fan-out hotspots, service locators, event/config backchannels |
| Semantics | `SD-S-1..5` | vocabulary splits/homonyms, aggregate leakage, unowned shared kernels, missing external-to-internal translation |
| Evolution | `SD-E-1..4` | shotgun change, unsafe refactor jumps, flag pile-up, permanent strangle paths |
| Tradeoff | `SD-Q-1..3` | unstated quality tradeoff, unmeasured local optimization, specialist concern absorbed instead of delegated |
| Socio-technical | `SD-T-1..3` | ownership mismatch, cognitive load cliff, orphaned shared code |

Default blocks: new dependency cycles/inversions, new internals leakage,
hidden mutable state, invariant leakage, mandatory speculative framework, and
specialist-scope absorption that would misroute the work. Default warns:
everything else unless evidence is advisory only.
