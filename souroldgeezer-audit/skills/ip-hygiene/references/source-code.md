# IP Hygiene Source Code Checks

Load this for source, configuration, or build files, their comments, and their
code documentation — notices, attribution comments, copied doc-comment prose,
and marks embedded in code. It is the language-independent procedure; it does
not define per-language comment syntax, ecosystem licence-metadata files,
generated-banner spellings, or minifier directive names. When a language is
detected, also load the matching `extensions/<lang>.md` pack for those
specifics. This file applies the criteria already defined in
[copyright.md](copyright.md), [licence-assets.md](licence-assets.md), and
[trademark.md](trademark.md); it does not restate them.

## The Four Classes

### Notices and headers

Licence headers, `SPDX-License-Identifier` lines, copyright lines, `@license` /
`@copyright` / `@author` doc-comment tags, and `NOTICE`-file propagation.
Establish identity and coverage under `IP-LIC-1`, confirm which act and
distribution the file participates in under `IP-LIC-4`, and track whether the
notice survived any transformation under `IP-LIC-5` (see "Notice survival
procedure" below).

### Attribution comments

"Adapted from", "based on", "source: `<URL>`", pasted-snippet markers from a
gist, forum, or blog post, and AI-assistant provenance comments. The
load-bearing point is `IP-SRC-2`: an attribution comment records provenance
and is not permission. A snippet carrying a source URL is an identified source
with unresolved terms — treat that as an evidence gap under
[SKILL.md § Counsel Escalation And Stops](../SKILL.md), not as a clearance,
and do not let the presence of an attribution comment substitute for actually
locating and checking the source's licence.

### Copied doc-comment prose

Docstrings, XML doc comments, JSDoc/TSDoc, Javadoc, rustdoc, and similar
copied or lightly reworded from upstream API documentation. Apply `IP-COPY-1`,
`IP-COPY-2`, and `IP-COPY-3`. Documentation prose is frequently licensed
separately from the code it documents — matching a permissive code licence
does not establish that the accompanying doc comments carry the same terms.
When the upstream text is not available for comparison, that is an evidence
gap under the skill's stop rules; it resolves neither as a finding nor as a
clearance.

### Marks in code

Identifiers, comments, string literals, package/module names, User-Agent
strings, and endpoint paths. Apply `IP-MARK-1`, `IP-MARK-2`, and `IP-MARK-4`,
establishing the audience from evidence per
[trademark.md § Public Surfaces And Authority](trademark.md); internal-only
visibility narrows but does not eliminate the question, because source
distributed as source still carries those signs to its recipients.

A code-comment style guide or symbol convention issued by the holder is
`holder policy` even when optional, not `project convention`; per
[trademark.md § Criteria](trademark.md), reserve `project convention` for a
rule the repository or publishing project itself adopted. An `IP-MARK-1` or
`IP-MARK-5` finding in code that applies binding law or a binding-law
harmonization source stays an `inference` under
[SKILL.md § Classification Decision Boundaries](../SKILL.md) even when the
underlying comment or identifier is a direct observation.

## Notice Survival Procedure

`IP-LIC-5` is the operational core for source files. For a transformation,
identify what covered material moved and whether its required notice moved
with it:

- **move or rename** — the file's identity changes; the notice must remain
  attached to the covered material, not left behind at the old path.
- **split or extract into new files** — each resulting file that still carries
  covered material needs the notice, not only the file that kept the original
  name.
- **inlining** — copied material pasted into a larger file needs its notice
  preserved in that file, even though the file as a whole may carry other
  notices too.
- **vendoring** — a full copy of third-party material into the repository
  needs both the vendored notice and, per `IP-LIC-4`, correct layering against
  any repository-level licence.
- **code generation** — a generator that emits covered material must carry
  that material's notice into its output; see "Generated and derived
  material" below for the generator/input/output split.
- **bundling** — combining files for a build or package artifact must not drop
  a constituent file's notice from the bundle.
- **transpilation** — output in a different source form still carries the
  input's covered expression and its notice obligation.
- **minification** — a build step that strips comments is a real notice-loss
  path; a minifier does not implicitly relieve the notice obligation, and the
  matching language extension states the mechanism it uses to preserve one.

Some licences constrain where a notice must sit or what form it must take;
relocation during any of the above is not automatically compliant merely
because the text still exists somewhere in the repository — confirm the
notice satisfies the form the licence requires, per
[licence-assets.md § Establish The Permission Chain](licence-assets.md).

## Generated And Derived Material Procedure

`IP-SRC-5` separates three layers for generated or derived source: the
generator's own licence, the input's terms (a schema, template, or corpus the
generator consumed), and the output's status. Do not treat these as one
question. A `DO NOT EDIT` or `generated by` banner is provenance evidence —
it identifies the generator and, often, the input — but it does not by itself
establish who holds rights in the output or that the output is unencumbered.

## Evidence And Stops

For a code-location finding, record the exact `path:line`, the covered
material's identity and provenance, which class above it falls into, and
which criterion and authority class apply, per
[SKILL.md § Finding And Remediation Contract](../SKILL.md). When source,
licence, or permission for a code location is load-bearing and unknown, stop
the affected decision per
[SKILL.md § Counsel Escalation And Stops](../SKILL.md). Never treat the
absence of a notice or attribution comment as proof of infringement, and
never treat its presence as permission.

## Non-Goals

Mechanical internal copy-paste duplication is `lean-audit` (`LA-CODE-DUP-*`);
source dead code is out of scope; semantic DRY belongs to `software-design`;
code-level security belongs to `devsecops-audit`. This file's interest is
third-party provenance, notices, permission, and marks in code — not internal
code quality.
