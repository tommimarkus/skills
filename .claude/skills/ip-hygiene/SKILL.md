---
name: ip-hygiene
description: Use when creating, modifying, renaming, moving, or deleting any skill-related or repo-documentation content in this repository — `souroldgeezer-*/skills/**`, `souroldgeezer-*/agents/**`, `souroldgeezer-*/docs/*-reference/**`, `.claude/skills/**`, plugin / marketplace manifests, or the `CLAUDE.md` / `README.md` sections that describe them. Runs a fast five-question triage; if any question hits, runs a copyright / trademark / licence check covering prose, code samples, figures, sample files, and bundled assets. Enforces ® / ™ on first mention in public-visible files (README, CLAUDE.md, manifests, frontmatter descriptions), blocks verbatim reproduction of copyrighted content, blocks bundling of third-party copyrighted assets unless the upstream licence permits redistribution, preserves the repo's nominative-fair-use convention (no attribution blocks, ® on first mention only), and surfaces pre-existing IP issues encountered during drive-by edits. Internal to this repository; not distributed with the `souroldgeezer-*` plugins.
---

# IP Hygiene

## Overview

This is a repo-internal skill. It encodes the copyright, trademark, and
licence discipline the `souroldgeezer` repository applies when Claude
authors or edits skill content. The substance is drawn from the audit
work done during the `architecture-design` build — near-verbatim
paraphrases of The Open Group ArchiMate® 3.2 Specification, ® on first
mention in public-visible files, the reflex to bundle The Open Group's
XSD schemas, the over-engineered attribution block that was rightly
rejected. This skill turns those one-off lessons into a durable
procedure so the next skill build applies the same hygiene without
re-deriving it.

Judgment-heavy by design. How verbatim is too verbatim, whether a use
is nominative, which third-party assets may be referenced or must be
by-URL-only, when a logo reproduction crosses from descriptive to
derivative — none of these can be automated. The skill is the
procedure Claude follows, not a validator.

**Not a substitute for legal review.** When a specific concern arises
that the procedure doesn't anticipate — a vendor cease-and-desist,
novel trademark policy, ambiguous licence term — escalate and obtain
legal input, don't guess.

## When this skill applies

Invoke on any create / modify / rename / move / delete touching:

- `souroldgeezer-*/skills/<name>/SKILL.md`, `extensions/`, `references/`
  (smell catalogs, procedures) — skill workflows and their supporting
  files.
- `souroldgeezer-*/agents/<name>.md` — subagents.
- `souroldgeezer-*/docs/<kind>-reference/*.md` — bundled reference
  prose (rubrics, playbooks, design references).
- `souroldgeezer-*/.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` — manifest descriptions.
- `CLAUDE.md` and `README.md` sections that describe any of the above.
- `.claude/skills/<name>/**` — repo-internal skills, including this
  one.

Pure internal-only edits that don't touch the items above — e.g.
renaming a variable in a helper script, reformatting whitespace,
updating a path in a build-only file — don't activate this skill.

### What counts as a "public-visible" file

Trademark first-mention discipline applies to files that are visible
*outside Claude's working context* — i.e. anything rendered for humans
or exposed through an agent / skill picker:

- `README.md`
- `CLAUDE.md` (public in the repo even though addressed to Claude)
- `.claude-plugin/marketplace.json` (top-level)
- each `<plugin>/.claude-plugin/plugin.json`
- frontmatter `description:` fields of every `SKILL.md` and
  `agents/*.md` (rendered in Claude Code's picker / skill-list UI)

Internal files not in this list — extension prose, procedures, smell
catalogs, reference `*.md` bodies — don't require ® on every mention.
Descriptive use throughout is the convention.

## Triage (always, fast)

Answer five yes/no questions about the edit:

1. **Public-surface trademark.** Does the edit mention a third-party
   registered trademark, product name, or named standard in a
   public-visible file (see list above)? Examples that trigger yes:
   ArchiMate®, TOGAF®, UML®, BPMN®, OpenAPI, WCAG, Microsoft, Azure,
   GitHub, Cosmos DB, Blob Storage, .NET, Blazor, Bicep, Entra ID,
   Next.js, React, PlantUML, Archi.
2. **Copyrighted text content.** Does the edit paraphrase, quote, or
   summarise prose from a copyrighted specification, standard,
   textbook, or published document? Examples: ArchiMate 3.2 element
   definitions, OpenAPI 3.1 schema property descriptions, WCAG 2.2
   Success Criteria wording, BPMN 2.0.2 conformance-class
   descriptions, UML 2.5.1 interaction-fragment definitions, RFC
   prose, Microsoft Learn article text, O'Reilly / Manning / Packt
   book text.
3. **Copyrighted non-text content.** Does the edit include or modify
   code samples, configuration fragments, sample files, diagrams,
   figures, tables, or illustrations that come from (or closely
   resemble) third-party copyrighted material? Examples: an Azure
   code snippet copied from a Microsoft Learn page; a BPMN diagram
   redrawn from a textbook figure; an example OEF XML file taken from
   The Open Group's sample set; an algorithm transcribed from a
   reference work.
4. **Third-party asset reference.** Does the edit reference a
   third-party schema, specification file, binary artefact, library,
   SDK, or example file — either by bundling it in the repo or by
   pointing at it? Examples: ArchiMate OEF XSD schemas, JSON Schema
   drafts, vendor datasheets, SDK binaries, logo files, brand-asset
   kits.
5. **Drive-by scope.** Does the file touched by the edit contain
   pre-existing content that, inspected fresh, would answer yes to
   any of questions 1–4?

**If all five are no → exit with "nothing to check".** Low-risk edits
don't carry friction.

**If any is yes → run the corresponding parts of the check below.**
Multiple questions can hit; run each applicable bucket.

## The check

### Copyright

**Scope.** Copyright attaches to original expression in any medium:
prose, code, figures, tables, XML / JSON samples, audio, video. The
rules below apply uniformly; they are not restricted to prose.

- **No verbatim or near-verbatim reproduction.** Short canonical
  passages — *"data structured for automated processing"*,
  *"a precisely defined outcome of a Work Package"* — are especially
  tempting because they're short and capture a definition cleanly.
  Don't reproduce silently. Either:
  - **Paraphrase into original expression.** Rewrite in your own
    voice, restructuring enough that a long run of consecutive
    content words no longer matches the source. A useful *heuristic*
    (not a legal test): if >6 consecutive content words match, the
    paraphrase is too thin. The actual legal test is *substantial
    similarity of protectable expression*, which is qualitative;
    when in doubt, rewrite further or quote.
  - **Or quote explicitly with attribution.** *"The Open Group
    ArchiMate® 3.2 Specification (C226) §7.3 defines Node as 'a
    computational or physical resource that hosts, manipulates, or
    interacts with other computational or physical resources.'"*
    Quotation with visible attribution sidesteps the paraphrase test.
  - Silent copying without attribution is the only wrong choice.
- **Code samples carry the source's licence.** Short, functionally
  required snippets (canonical two-line API calls) are usually not
  protectable. Longer, non-trivially-creative examples are. If a
  code sample in a skill resembles a published example closely,
  treat it as copyrighted and either rewrite for originality or
  include a source citation and verify the upstream licence permits
  the use:
  - **Microsoft Learn content** — CC BY 4.0 (see the MicrosoftDocs
    repos, e.g. [azure-docs LICENSE](https://github.com/MicrosoftDocs/azure-docs/blob/main/LICENSE)
    and the terms at [learn.microsoft.com/legal/termsofuse](https://learn.microsoft.com/legal/termsofuse)).
    Attribution required; short canonical API-call snippets usually
    not copyrightable anyway.
  - **MSDN pre-2017** — mixed licensing; treat as all-rights-reserved
    unless a specific page indicates otherwise.
  - **SDK documentation code samples** — usually under the SDK's
    own licence (check the SDK repo's LICENSE file).
  - **Vendor blog posts and marketing material** — all rights
    reserved unless explicitly stated.
- **Figures and diagrams are derivative works.** Redrawing a figure
  from a spec or book in different colours is still a derivative
  work and requires the original licence to permit it. Prefer to
  generate original figures when possible, or cite the source figure
  explicitly with permission confirmation.
- **Sample files (XML / JSON / YAML) from specs** are part of the
  spec. ArchiMate sample OEF XML files, BPMN sample XML files,
  OpenAPI example documents — all carry the spec's licence. Do not
  copy them verbatim; construct equivalent samples from scratch.

**No bundling of third-party copyrighted assets — with one
exception.**

- Default: do not copy XSD schemas, spec PDFs, binary artefacts,
  vendor datasheets, API reference files, logos, or icon sets into
  this repo. Reference by canonical URL so downstream tools fetch
  from upstream.
- **Exception: permissively-licensed assets.** Schemas and
  specifications under permissive open-source licences (Apache 2.0,
  MIT, BSD, CC BY, public domain, CC0) *may* be bundled with the
  attribution the upstream licence requires. Verify the specific
  file's licence header before bundling — a repo can mix licences
  on different files. When in doubt, reference by URL; that path is
  always safe.
- Worked example: `architecture-design` emits OEF XML with
  `xsi:schemaLocation` pointing at The Open Group's canonical schema
  URL and does not ship the XSD locally (The Open Group's schema
  licensing is restrictive enough that URL-reference is the safer
  path).

### Trademark

- **First-mention ® / ™ on public-visible files.** For every
  public-visible file (see list above), the first occurrence of
  each registered trademark in that file carries the appropriate
  symbol (® for registered, ™ for unregistered but claimed).
  Subsequent mentions in the same file can omit. Internal files
  don't require the symbol on every mention; one or two occurrences
  per file is sufficient to signal awareness.
- **Logos and brand assets are separate from text marks.** The
  *word* "Azure" used descriptively is nominative fair use. The
  Microsoft Azure *logo* is a distinct creative work and using it
  requires explicit permission (Microsoft's trademark guidelines;
  The Open Group's brand guidelines; similar for every major
  vendor). Do not bundle or inline logos / brand kits / icon sets
  into this repo.
- **No certification, accreditation, or endorsement claims.** Do
  not write "X-certified", "X-accredited", "official X
  implementation", "endorsed by X", or phrasing that implies
  affiliation with the trademark holder. Descriptive reference
  ("applies the X 3.2 specification", "generates X-conformant
  output") is permitted under nominative fair use; endorsement
  claims are not.
- **No trademark in skill / plugin / agent / product names implying
  affiliation.** Descriptive naming (`architecture-design`,
  `serverless-api-design`) is fine. A hypothetical
  `archimate-official`, `the-open-group-modeller`, or
  `microsoft-api-gen` is not.
- **Some trademark policies are more restrictive than nominative
  fair use expects.** Mozilla's Firefox brand, for example, has
  historically restricted even descriptive use in derivative
  products. If the trademark holder publishes a detailed brand
  policy, read it before relying on the general rule.

### Licence

- **Nominative descriptive reference** (citing a standard by name,
  naming a product, following a published schema's conventions) is
  permitted for the vast majority of third parties. The Open Group,
  OMG, W3C, IETF, Microsoft, GitHub, Google, Apple, and most major
  vendors explicitly permit descriptive use; some smaller
  proprietary specs restrict it. Verify the upstream policy before
  relying on this rule for a specific vendor.
- **Library and tool references.** A skill may reference any
  open-source or commercial library / tool by name without
  licensing implications (that's nominative use). Mere mention does
  not extend any licence to this repo.
- **Bundling third-party code is different.** If a skill includes
  actual code from a third-party library, that code is under the
  library's licence, and the licence must be compatible with this
  repo's MIT licence. Apache 2.0, BSD, MIT, and public-domain
  content is compatible. GPL-family licences (GPL, AGPL, LGPL) are
  not compatible with MIT at the distribution level and generally
  must not be bundled. CC BY-SA has share-alike requirements that
  conflict with MIT. When in doubt, don't bundle — reference by URL.
- **Repo's MIT licence** applies only to the repo's own content.
  Edits must not imply the MIT grant extends to any referenced
  third-party standard, schema, or software.
- **AI-authored content status.** Material authored by Claude at
  this repo's request is disclosed as such in
  [README.md](../../../README.md) § "Attribution". Under current US
  precedent (*Thaler v. Perlmutter*, D.D.C. 2023; USCO policy
  guidance 2023), purely AI-generated content is generally not
  copyrightable. The repo's MIT licence applies to the combined
  human+AI work as a whole; individual AI-generated portions may
  have limited copyright protection. This does not create an IP
  risk for the repo, but it means downstream users should not rely
  on this repo to confer copyright protection on AI-generated text
  they extract.

## Scope discipline

- **Do not add trademark attribution blocks as remediation.** The
  repo's established convention, visible in the existing
  `souroldgeezer-design/docs/ui-reference/responsive-design.md`,
  `souroldgeezer-design/docs/api-reference/serverless-api-design.md`,
  and `souroldgeezer-design/docs/architecture-reference/architecture.md`
  references, is *nominative descriptive use without attribution
  blocks*. Microsoft, Azure, GitHub, W3C, IETF, and similar
  trademarks are referenced throughout without blocks. Adding a
  block for one mark creates inconsistency, maintenance burden, and
  no legal benefit. The ® on first public-visible mention is
  sufficient.
- **Do not strip trademark mentions to "reduce risk".** Nominative
  descriptive use is legally protected and operationally necessary.
  Removing "ArchiMate" from a skill about ArchiMate breaks the
  skill without any legal gain. If in doubt about a specific use,
  keep the mention and apply the ® rule.
- **Provenance is best-practice even when not legally required.**
  Paraphrased content benefits from a source citation in the
  surrounding prose ("derived from ArchiMate 3.2 Chapter 5") —
  helps future auditors, costs nothing.

## Drive-by scope

When triage Q5 hits — the edit touches a file with pre-existing IP
issues that are not what the current edit is about — apply this
rule:

- **If a quick fix cleans up the pre-existing issue without
  expanding the edit's scope dramatically** (e.g., adding ® to a
  first-mention trademark four lines above where you're editing,
  rewriting a near-verbatim paraphrase in the same section), fix
  it. Document in the same change-note that the fix was a drive-by
  observation.
- **If the pre-existing issue is large** (e.g., a whole section
  that would need rewriting, a bundled asset that would need
  removal), don't expand the current edit. Instead, flag it to the
  user in the output — "noticed pre-existing `AD-14`-class issue
  at `path/to/file.md:123`; deferred, recommend separate retroactive
  audit" — and continue with the original task.
- **Do not silently propagate a pre-existing violation.** If the
  current edit copies or references content that is itself an
  existing violation, fix the copy at minimum, even if the original
  stays.

## Cross-skill integration

`ip-hygiene` is invoked on file edits. It does *not* currently hook
into other skills' Review modes (e.g., `architecture-design` Review
does not automatically dispatch `ip-hygiene`). If a future skill
wants to add an IP check to its Review mode, point at this skill by
name; do not duplicate the procedure.

When a skill's Build mode *produces* new content — for example,
`architecture-design` Build generating an OEF XML file from architect
intent — the ip-hygiene check applies to the *skill-authoring edit*
(you edited the skill to make it produce that shape), not to each
downstream file Claude generates at runtime. Runtime output is the
user's content; IP hygiene on their content is their concern, not
the skill's.

## Remediation order

When the check fires on something that needs fixing, prefer the
remedy higher on this list:

1. **Paraphrase into original expression** — for near-verbatim
   copyright matches in prose, code, or figures.
2. **Add ® / ™ on first mention** — for trademark first-mention
   misses on public-visible surfaces.
3. **Replace a bundled asset with a URL reference** — for
   redistribution-adjacent concerns (except permissively-licensed
   assets, which may be bundled with upstream attribution).
4. **Reword to descriptive nominative** — for
   endorsement-implication concerns.
5. **Last-resort removal** of the reference — only if the mention
   is non-load-bearing *and* the above four remedies don't apply.
   Removal of a load-bearing reference (e.g. stripping "ArchiMate"
   from a skill about ArchiMate) is wrong; see the previous
   section.

All remedies happen in the same edit that introduced the concern.
Do not defer. Do not open a follow-up.

## Honest limits

- **Judgment-heavy.** This skill is a procedure; it is not a
  substitute for actual legal review. If a specific concern arises
  that the procedure doesn't cover — a vendor sending a takedown
  notice, a licence term that clearly conflicts with descriptive
  use, a novel trademark claim, a content type not anticipated —
  escalate to the user and get legal input.
- **Does not validate schemas or specification conformance.** IP
  posture is orthogonal to technical correctness; schema validation
  stays with the skill or tool that produced the artefact.
- **Does not retroactively audit full files.** The check runs on the
  *edit's diff*. Drive-by fixes are available for incidentally-
  observed pre-existing issues; a full retroactive audit must be
  requested explicitly as a separate task.
- **English-language case law only.** The rationale cites US and
  EU precedent. UK law (post-Brexit) follows broadly similar
  doctrine under s.11(2)(b) of the Trade Marks Act 1994; other
  jurisdictions may differ. If the repo is accessed primarily from
  a jurisdiction with different trademark or copyright doctrine,
  the specifics may need adjustment.
- **Explicitly out of scope:**
  - **Patents** — implementing a patented algorithm is a separate
    risk; this skill doesn't cover it. If a skill's design involves
    a potentially patented technique, escalate.
  - **Trade secrets** — unlikely in a public marketplace but noted.
  - **Privacy / GDPR / CCPA** — data-subject rights, PII handling,
    lawful-basis analysis are separate.
  - **Export control (EAR / ITAR)** — cryptography, dual-use
    technology controls are separate.
  - **Contract law** — NDAs, MSAs, CLAs are separate. If this repo
    adopts a CLA for external contributors, that process lives
    elsewhere.
  - **Right of publicity** — using someone's name or likeness is
    a distinct doctrine; not anticipated in this repo's content.
  - **Defamation** — content about identifiable people is a
    separate risk layer.

## Rationale

Nominative fair use is the doctrine that permits using a trademark
to refer to the actual product, standard, or service it names.

- **US precedent:** *New Kids on the Block v. News America
  Publishing*, 971 F.2d 302 (9th Cir. 1992); *Playboy Enterprises,
  Inc. v. Welles*, 279 F.3d 796 (9th Cir. 2002). Three-part test:
  the product cannot reasonably be identified without using the
  mark; only as much of the mark is used as necessary; no
  suggestion of sponsorship or endorsement.
- **EU:** Article 14(1)(c) of the EU Trade Mark Regulation
  2017/1001 permits use of an earlier trademark where necessary to
  indicate the intended purpose of a product or service.
- **UK (post-Brexit):** s.11(2)(b) of the Trade Marks Act 1994
  provides the domestic equivalent.
- **AI-authored content:** *Thaler v. Perlmutter*, Civ. No.
  22-1564 (D.D.C. 2023), held that works authored solely by AI
  without human creative contribution are not copyrightable under
  current US law; subsequent US Copyright Office guidance (2023)
  applies the same rule. This informs the AI-authored disclosure
  in [README.md](../../../README.md) § "Attribution".

A skill that documents how to work in a named standard satisfies
all three parts of the nominative-fair-use test comfortably.

The repo's convention — no attribution block, ® on first
public-visible mention, paraphrase over verbatim, reference schemas
by URL rather than bundling (except where the upstream licence
permits redistribution), explicit disclosure of AI authorship — was
established implicitly across `responsive-design`,
`serverless-api-design`, and `architecture-design`, and codified
via the `architecture-design` audit. This skill records it so every
future skill change honours the convention without re-deriving it.

Keeping the skill internal to the repo (not distributed via the
`souroldgeezer-*` plugins) is deliberate: IP discipline is about
how *we* author this repo, not a capability shipped to downstream
users.

## Authoritative sources

Primary-source URLs for the claims in this skill. Each citation is
the canonical reference to consult when the claim's details matter.
Listed alphabetically within each group.

### Trademark law — case law and statute

- **EU Trade Mark Regulation (EU) 2017/1001** — Article 14(1)(c) on
  limitation of the effects of an EU trade mark; permits descriptive
  use of another's mark where necessary to indicate the intended
  purpose of a product or service.
  [eur-lex.europa.eu/eli/reg/2017/1001/oj](https://eur-lex.europa.eu/eli/reg/2017/1001/oj)
- **Lanham Act, 15 U.S.C. §1125** — US federal trademark statute
  (unfair competition; false designation of origin).
  [uscode.house.gov](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title15-section1125)
- ***New Kids on the Block v. News America Publishing***, 971 F.2d
  302 (9th Cir. 1992) — canonical US three-factor nominative-fair-use
  test.
  [law.justia.com/cases/federal/appellate-courts/F2/971/302](https://law.justia.com/cases/federal/appellate-courts/F2/971/302/235791/)
- ***Playboy Enterprises, Inc. v. Welles***, 279 F.3d 796 (9th Cir.
  2002) — affirmed and refined the nominative-fair-use test for
  descriptive / factual references.
  [law.justia.com/cases/federal/appellate-courts/F3/279/796](https://law.justia.com/cases/federal/appellate-courts/F3/279/796/628194/)
- **UK Trade Marks Act 1994, s.11(2)(b)** — descriptive-use limitation
  in UK law (post-Brexit equivalent of EUTMR Art. 14).
  [legislation.gov.uk/ukpga/1994/26/section/11](https://www.legislation.gov.uk/ukpga/1994/26/section/11)

### Trademark policies — commonly referenced holders

- **The Open Group Legal / Trademarks** — policy governing ArchiMate®,
  TOGAF®, UNIX®, and other registered marks.
  [opengroup.org/legal/trademarks](https://www.opengroup.org/legal/trademarks)
- **Microsoft Trademark and Brand Guidelines** — policy governing
  Microsoft, Azure, Windows, Office, and related marks.
  [microsoft.com/en-us/legal/intellectualproperty/trademarks](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks)
- **Object Management Group (OMG) Trademarks** — policy governing
  UML®, BPMN®, CORBA®, and other OMG marks.
  [omg.org/about/policies/trademarks.htm](https://www.omg.org/about/policies/trademarks.htm)
- **W3C Trademark and Servicemark Usage Policy** — policy governing
  W3C® and related service marks.
  [w3.org/Consortium/Legal/trademark-license](https://www.w3.org/Consortium/Legal/trademark-license)
- **GitHub Logos and Usage** — policy and asset kits.
  [github.com/logos](https://github.com/logos)
- **IETF Trust Policies** — governing policy for IETF trademarks and
  materials.
  [trustee.ietf.org/policy-and-procedures/](https://trustee.ietf.org/policy-and-procedures/)

### Open-source licence texts

- **Apache License 2.0** —
  [apache.org/licenses/LICENSE-2.0](https://www.apache.org/licenses/LICENSE-2.0).
- **MIT License** —
  [opensource.org/license/mit](https://opensource.org/license/mit).
- **BSD 2-Clause / BSD 3-Clause** —
  [opensource.org/license/bsd-3-clause](https://opensource.org/license/bsd-3-clause).
- **GNU GPL v3 / LGPL v3 / AGPL v3** —
  [gnu.org/licenses](https://www.gnu.org/licenses/).
- **Creative Commons licence chooser / texts** —
  [creativecommons.org/licenses](https://creativecommons.org/licenses/).
- **CC0 Public Domain Dedication** —
  [creativecommons.org/public-domain/cc0](https://creativecommons.org/public-domain/cc0/).
- **OSI-approved licences index** —
  [opensource.org/licenses](https://opensource.org/licenses).

### Licence compatibility

- **GNU "Various Licenses and Comments About Them"** — Free Software
  Foundation's authoritative compatibility matrix between GPL-family
  and other licences.
  [gnu.org/licenses/license-list.html](https://www.gnu.org/licenses/license-list.html)
- **GPL FAQ** — canonical Q&A on GPL / LGPL / AGPL compatibility.
  [gnu.org/licenses/gpl-faq.html](https://www.gnu.org/licenses/gpl-faq.html)
- **OSI licence categories** — Open Source Initiative's grouping by
  popularity, permissive / copyleft / special-purpose.
  [opensource.org/licenses/category](https://opensource.org/licenses/category)

### AI-authored content

- ***Thaler v. Perlmutter***, No. 22-1564, 2023 WL 5333236 (D.D.C.
  Aug. 18, 2023) — held that works produced without human creative
  contribution are not copyrightable under 17 U.S.C. §102(a).
  [casetext.com or courtlistener.com](https://www.courtlistener.com/) (search by docket number).
- **US Copyright Office, "Copyright Registration Guidance: Works
  Containing Material Generated by Artificial Intelligence"**, 88
  Fed. Reg. 16190 (Mar. 16, 2023) — registration policy consistent
  with *Thaler*.
  [copyright.gov/ai](https://www.copyright.gov/ai/)
- **US Copyright Office Report on Copyright and Artificial
  Intelligence** (ongoing, Parts 1–3 published 2024–2025) — extended
  policy guidance.
  [copyright.gov/ai](https://www.copyright.gov/ai/)

### Content licences of commonly referenced documentation

- **Microsoft Docs / Microsoft Learn** — CC BY 4.0 for prose; code
  samples typically MIT (see the relevant MicrosoftDocs repo's
  LICENSE). Example: [azure-docs LICENSE](https://github.com/MicrosoftDocs/azure-docs/blob/main/LICENSE).
- **OpenAPI Specification** — Apache License 2.0 (see the OAI repo's
  [LICENSE](https://github.com/OAI/OpenAPI-Specification/blob/main/LICENSE)).
- **IETF RFCs** — IETF Trust Licence; most RFCs are permissively
  licensed for reproduction as "unmodified verbatim" with attribution.
  [trustee.ietf.org/license-info](https://trustee.ietf.org/license-info/).
- **W3C Recommendations** — W3C Document License (specific terms
  permit reproduction with notice).
  [w3.org/copyright/document-license-2023](https://www.w3.org/copyright/document-license-2023/).
- **ArchiMate® 3.2 Specification (C226)** — The Open Group
  publication; terms at
  [pubs.opengroup.org](https://pubs.opengroup.org/) (registration
  required for the PDF; freely readable but redistribution is
  restricted — reference by URL from this repo).
- **BPMN™ 2.0.2 Specification** — OMG publication; OMG standards are
  generally freely readable with OMG's specific redistribution terms.
  [omg.org/spec/BPMN/2.0.2](https://www.omg.org/spec/BPMN/2.0.2/).
- **UML® 2.5.1 Specification** — OMG publication.
  [omg.org/spec/UML/2.5.1](https://www.omg.org/spec/UML/2.5.1/).
- **WCAG 2.2** — W3C Recommendation.
  [w3.org/TR/WCAG22](https://www.w3.org/TR/WCAG22/).

### Notes on using these sources

- **URLs are for reference, not runtime fetch.** The Claude Code
  sandbox in this repo does not have network access to most of
  these hosts; this list is authoritative documentation for *when*
  a claim needs primary-source verification (e.g. before committing
  a change that hinges on a specific interpretation). Fetch
  out-of-band when needed.
- **Primary over secondary.** Cite the statute / case / policy /
  licence text directly, not a blog post summarising it. Secondary
  sources (Stack Overflow answers, law-firm blog posts, GitHub
  issue threads) may be useful for orientation but are not
  authoritative.
- **Jurisdiction and currency.** Case law and statutes change.
  Before relying on a specific test in a consequential context,
  confirm the cited authority is still good law in the relevant
  jurisdiction.
