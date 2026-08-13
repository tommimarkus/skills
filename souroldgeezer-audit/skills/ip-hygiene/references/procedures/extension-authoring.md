# Extension Authoring

Language packs are loaded on demand by the `ip-hygiene` skill, per
[SKILL.md § Scope And Load Map](../../SKILL.md). Unlike `devsecops-audit`'s
routing cards, a pack here is self-contained: it carries its own rules, with
no second-tier `docs/` pack behind it. Per-language IP-hygiene material is
small enough — comment syntax, header placement, licence metadata, a handful
of notice-survival mechanics — that a second hop would cost more context than
it saves.

## Load Order

1. The skill loads core criteria (`copyright.md`, `licence-assets.md`,
   `trademark.md`) as selected by the evidence.
2. It loads [source-code.md](../source-code.md), the language-independent code
   lane, when source, configuration, or build files are in scope.
3. For each language detected in the reviewed files, it loads the matching
   `extensions/<lang>.md` pack.
4. Packs never load each other. When a review spans several languages, load
   every matching pack; each applies only to the files its detection signals
   match, and findings from different packs do not interact.

Extensions never override core criteria or `source-code.md`. They may only add
or carve out.

## Criterion Namespace

Extension criteria are `<ext>.IP-<FAMILY>-<n>` — for example `python.IP-LIC-1`
or `js.IP-SRC-2` — orthogonal to the core `IP-SRC-*` / `IP-COPY-*` / `IP-DB-*`
/ `IP-LIC-*` / `IP-MARK-*` numbering in
[SKILL.md § Criteria And Authority](../../SKILL.md), so an extension criterion
can never collide with or shadow a core one. A pack either **ADDS** a new
numbered criterion in its namespace or **CARVES OUT** a core criterion for one
exact idiomatic pattern in that language; it never overrides a core or
`source-code.md` rule.

## Required Sections Per Pack

Each pack must carry exactly these sections, naming what
[source-code.md](../source-code.md) defers to the language:

- **Detection signals** — file extensions, manifest files, or other filesystem
  evidence that identifies the language, matching the skill's load condition.
- **Comment and doc-comment syntax** — the language's line/block comment forms
  and its doc-comment convention (docstring, XML doc, JSDoc/TSDoc, Javadoc,
  rustdoc, or equivalent), so `source-code.md`'s "Copied doc-comment prose"
  class can be located in this language's files.
- **Header placement and ordering** — where a licence header or
  `SPDX-License-Identifier` line must sit in a file of this language (shebang,
  package/namespace declaration, import block) and how it interacts with
  other required leading content.
- **Ecosystem licence metadata** — the manifest field(s) or file(s) this
  language's package ecosystem uses to declare licence (e.g. a package
  manifest's licence field, a project file's licence property), and how that
  metadata relates to file-level notices.
- **Vendoring conventions** — the directory name(s) or mechanism this
  language's tooling uses to vendor third-party code, and what evidence
  distinguishes vendored code from first-party code.
- **Generated-code banners** — the exact banner text or marker this language's
  common generators emit, feeding `source-code.md`'s "Generated And Derived
  Material Procedure" (`IP-SRC-5`).
- **Notice-survival mechanics** — for this language's build/bundle/minify
  toolchain, what a minifier or bundler does to comments by default, and the
  specific directive or option (e.g. a "preserve comment" pragma or CLI flag)
  that keeps a notice attached through that transformation, feeding
  `source-code.md`'s "Notice Survival Procedure" (`IP-LIC-5`).
- **Mark surfaces** — the identifier, string-literal, or metadata surfaces
  specific to this language or its ecosystem (e.g. a package name field, a
  User-Agent constant, an endpoint-path convention) where a third-party mark
  is most likely to appear in this language's code.
- **Criteria** — a closing disclosure of what the pack does to the criteria
  set: which core criteria its facts serve, and either the namespaced
  criterion it adds or carves out, or an explicit statement that it defines
  none. State this even when the answer is "none" — a reader must be able to
  tell from the pack alone whether it changed the criteria set.

In practice a pack usually defines no namespaced criterion. The criteria are
language-independent; what varies is the evidence surface. Add a namespaced
criterion only for a question core does not already ask — not for a
language-specific mechanism of a question it does. A minifier stripping
comments is the mechanism of `IP-LIC-5`, which already names minification, so
it is evidence, not a new criterion.

## The Craft Guard

A pack ships only if it carries at least three genuinely language-specific
facts that are not derivable from `source-code.md` — a stated comment syntax,
banner text, a minifier flag, an ecosystem manifest field, and similar are
language-specific; a restatement of the four classes or the notice-survival
transformation list is not. A pack that would only restate the shared lane is
dropped, not padded. This is a shipping condition, not advice.

## Current Extensions

A namespace is reserved per pack even when the pack defines no numbered
criterion, so one can be added later without renumbering.

| File | Applies to | Namespace | Numbered criteria |
|---|---|---|---|
| `python.md` | `*.py`, Python package manifests (e.g. `pyproject.toml`) | `python.` | none |
| `shell.md` | `*.sh`, `*.bash`, `*.zsh` | `shell.` | none |
| `javascript-typescript.md` | `*.js`, `*.jsx`, `*.mjs`, `*.cjs`, `*.ts`, `*.tsx`, Node.js/npm manifests | `js.` | none |
| `dotnet-csharp.md` | `*.cs`, `*.csproj`, `*.sln`, `*.nuspec` | `dotnet.` | none |
| `java.md` | `*.java`, Maven/Gradle manifests | `java.` | none |
| `rust.md` | `*.rs`, `Cargo.toml` | `rust.` | none |

## Adding A New Language

1. Copy the required-sections list above as the pack's outline.
2. Pick the namespace prefix (lowercase, matching the language or its common
   file extension), consistent with the table above.
3. Fill in every required section with facts specific to this language;
   cite [source-code.md](../source-code.md) or the relevant core reference for
   anything already covered there instead of restating it.
4. State each added or carved-out criterion in the pack's namespace, per
   "Criterion Namespace" above.
5. Apply the craft guard: confirm at least three genuinely language-specific
   facts are present, or drop the pack.
6. Add the pack to the table above and update
   [SKILL.md § Scope And Load Map](../../SKILL.md) detection mapping if the
   language's detection signals aren't already implied there.
