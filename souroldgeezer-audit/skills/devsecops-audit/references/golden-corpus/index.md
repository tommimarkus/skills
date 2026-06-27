# DevSecOps Audit Golden Corpus

Versioned seed cases for empirical `devsecops-audit` accuracy checks, realizing
the self-measurement principle in `../../../docs/audit-reference/audit-craft.md` §8.
Run [../procedures/golden-corpus-evals.md](../procedures/golden-corpus-evals.md)
after changing the rubric, smell catalog, output contract, or extensions.

Unlike a hand-labeled corpus, devsecops ground truth is **objective**: each
positive case plants a verifiable defect (a seeded real-shape secret, a known
CVE / CISA-KEV id, or a concrete misconfiguration) so recall is measured against
fact, not opinion. Each family keeps at least one positive (defect present) and
one negative (clean / idiomatic, to pin false positives). Snippets are minimal
and original to this repository; external CVE/KEV ids are taxonomy labels only.
