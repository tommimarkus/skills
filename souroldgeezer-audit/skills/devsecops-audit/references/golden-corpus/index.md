# DevSecOps Audit Golden Corpus

Versioned seed cases for empirical `devsecops-audit` accuracy checks, realizing
the self-measurement principle in [audit-craft.md §8](../../../../docs/audit-reference/audit-craft.md).
Run [../procedures/golden-corpus-evals.md](../procedures/golden-corpus-evals.md)
after changing the rubric, smell catalog, output contract, or extensions.

Unlike a hand-labeled corpus, devsecops ground truth is **objective**: each
positive case plants a verifiable defect (a seeded real-shape secret, a known
CVE / CISA-KEV id, or a concrete misconfiguration) so recall is measured against
fact, not opinion. Each false-positive-prone family keeps a positive and a clean
negative (to pin false positives); detection-recall families may be positive-only. Snippets are minimal
and original to this repository; external CVE/KEV ids are taxonomy labels only.
