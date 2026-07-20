# Accuracy Corpus (audit-of-the-review)

Labeled cases scoring **Review-mode finding accuracy** — recall (does Review
catch the smell that is really there?) and false-positive rate (does it flag a
look-alike it should not?). Trigger and behavior evals prove routing and shape;
this measures whether the `SD-*` findings themselves are right. It is a
**behavioral eval run by a model**, not a deterministic gate — not wired into CI.

Follows the repo's `accuracy-corpus/` convention (as `ip-hygiene` uses:
`README.md` + `expected.jsonl`). It differs in one way: `ip-hygiene` scans real
files, so its cases are a `cases/<id>/` file tree; software-design **Review**
operates on described or inline code, so each case's scenario lives inline in
`expected.jsonl` — no separate file tree.

## Case schema (`expected.jsonl`, one object per line)

- `id` — `sd-acc-NNN`, contiguous.
- `target` — the primary `SD-*` code the case is built around.
- `kind` — `positive` (smell genuinely present), `fp-bait` (resembles the smell
  but is cleared by that code's `false_positive_guard`), or `clean` (well-designed
  code for the family; nothing should be reported).
- `prompt` — a synthetic, original code scenario to run Review over.
- `ground_truth_codes` — codes a correct Review **should** report (empty for
  `fp-bait` / `clean`).
- `must_not_flag` — codes that **must not** appear (the baited code for
  `fp-bait`; the family's codes for `clean`).
- `location_hint`, `rationale` — where the smell sits and why the label holds.
- `source_kind` / `source_url` / `ip_handling` / `contains_third_party_text` —
  provenance; every case is original synthetic, no third-party text.

## Coverage

111 cases over every core smell family: **62 positive** (≥2 per core code),
**39 fp-bait** (one per code, each grounded in that code's `false_positive_guard`
in `smell-cards.jsonl`), **10 clean**. Extension codes are out of scope (core
`SD-*` only). The `clean` cases are the false-positive control and MUST stay
finding-free.

## How to measure

Run software-design **Review** on each case's `prompt` and collect the emitted
`SD-*` codes, then score:

- **Recall** (positives): of the `ground_truth_codes`, the fraction Review
  emitted — per-code and overall. A code whose positives are routinely missed
  needs a sharper card `signal` or playbook rule.
- **False-positive rate**: of the `fp-bait` cases, the fraction where the baited
  `must_not_flag` code was wrongly emitted; plus any code emitted on a `clean`
  case. A code that over-fires needs a stronger `false_positive_guard`.
- **Over-flag rate** (precision proxy): on positives, emitted codes not in
  `ground_truth_codes`.

Grade by whether the expected code appears in Review's output (a rubric or
model-judge scores at scale). Record the run date and model — accuracy is
model-dependent.

## Maintenance

Keep ≥2 positive and ≥1 fp-bait case per core code. When a code is added, add
its cases in the same change; when a code is retired (e.g. `SD-S-3`), remove its
cases. Keep prompts synthetic and varied across domains; never paste real
third-party code. Not scanned by the load-cost closure (not linked from
`SKILL.md`), so growing it does not change per-use cost.
