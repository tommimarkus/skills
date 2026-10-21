# IP Hygiene In-Depth Review

Load this before reasonable-hygiene in-depth fieldwork, per
[SKILL.md § In-Depth Procedure And Verdict](../../SKILL.md). Triage and the
prospective lane do not load it.

## Steps And Verdict

1. Enumerate every in-scope publication surface and the distribution forms it
   produces. Record exclusions.
2. Survey risk before catalog work; prioritize public names/branding, bundled
   or vendored material, notices, generated packages, and copied documentation.
3. Run the pre-filter over the full enumeration, then apply all six triage
   questions per surface and all hit criteria.
4. Corroborate source identity, actual file-level licence, holder policy, and
   jurisdiction/applicability. Mark static conclusions as inference. At scale,
   sample and project under audit-craft section 6 and disclose the basis. Before
   sampling, when the surface is large enough that per-surface evidence may not
   reach the verdict intact, load
   [scaled-audit.md](../../../../docs/audit-reference/scaled-audit.md) (delegation +
   evidence durability); if evidence starts outgrowing context mid-run, load it
   then rather than continuing. Triage must not load it.
5. Emit findings and exactly
   `in-depth verdict: <blocked | qualified | no-blocker-identified>`:
   - `blocked` — a substantiated blocking condition or mandatory counsel
     escalation prevents a repository hygiene decision;
   - `qualified` — no substantiated block remains, but findings or material
     evidence/sampling limitations qualify the result;
   - `no-blocker-identified` — sufficient appropriate evidence over the stated
     surface identified no blocking criterion. It does not mean clean,
     non-infringing, compatible, or cleared.

## Boundary Evidence

Every in-depth result names the reviewed surface, exclusions, supporting
evidence, and limits, including an explicit `none` where there are no
exclusions. A verdict without that boundary evidence is incomplete.
