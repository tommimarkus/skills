# IP Hygiene Reference

## Overview

This is a repo-internal skill. It encodes the copyright, trademark, and
licence discipline the `souroldgeezer` repository applies when authoring
agents edit skill content. The substance is drawn from the audit
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
procedure the authoring agent follows, not a validator.

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
- `souroldgeezer-*/.claude-plugin/plugin.json`,
  `souroldgeezer-*/.codex-plugin/plugin.json`, and
  `.claude-plugin/marketplace.json` — manifest descriptions.
- `souroldgeezer-*/skills/<name>/agents/openai.yaml` — Codex
  per-skill public-facing metadata.
- `.codex/agents/*.toml` — project-scoped Codex custom-agent
  wrappers.
- `CLAUDE.md`, `AGENTS.md`, and `README.md` sections that describe any
  of the above.
- `.claude/skills/<name>/**` — repo-internal skills, including this
  one.

Pure internal-only edits that don't touch the items above — e.g.
renaming a variable in a helper script, reformatting whitespace,
updating a path in a build-only file — don't activate this skill.

### What counts as a "public-visible" file

Trademark first-mention discipline applies to files that are visible
*outside the authoring agent's working context* — i.e. anything rendered
for humans or exposed through an agent / skill picker:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md` (public in the repo even though addressed to Claude)
- `.claude-plugin/marketplace.json` (top-level)
- each `<plugin>/.claude-plugin/plugin.json`
- each `<plugin>/.codex-plugin/plugin.json`
- each `<plugin>/skills/<name>/agents/openai.yaml`
- each `.codex/agents/*.toml` `description`
- frontmatter `description:` fields of every `SKILL.md` and
  `agents/*.md` (rendered in Claude Code's picker / skill-list UI;
  Codex renders skill descriptions from `SKILL.md`)

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
   *Default: when uncertain whether a name refers to a registered
   trademark, a product, or a named standard, treat it as one until
   verified otherwise. Honest-practices doctrine (EUTMR Art 14(2);
   see § "Authoritative sources") expects a careful actor to check,
   not guess.*
2. **Copyrighted text content.** Does the edit paraphrase, quote, or
   summarise prose from a copyrighted specification, standard,
   textbook, or published document? Examples: ArchiMate 3.2 element
   definitions, OpenAPI 3.1 schema property descriptions, WCAG 2.2
   Success Criteria wording, BPMN 2.0.2 conformance-class
   descriptions, UML 2.5.1 interaction-fragment definitions, RFC
   prose, Microsoft Learn article text, O'Reilly / Manning / Packt
   book text, **spec tables and structured enumerations from
   copyrighted standards** (these may also engage the EU sui generis
   database right — see § "The check / Copyright").
3. **Copyrighted non-text content.** Does the edit include or modify
   code samples, configuration fragments, sample files, diagrams,
   figures, tables, or illustrations that come from (or closely
   resemble) third-party copyrighted material? Examples: an Azure
   code snippet copied from a Microsoft Learn page; a BPMN diagram
   redrawn from a textbook figure; an example OEF XML file taken from
   The Open Group's sample set; an algorithm transcribed from a
   reference work; **fixture / sample / example files distributed
   with a copyrighted spec, even when nominally machine-readable
   artefacts (XML, JSON, YAML)**.
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
rules below apply uniformly; they are not restricted to prose. **In
addition, in the EU, the sui generis database right (Directive
96/9/EC Art 7) protects substantial investment in databases
independently of copyright** — see the dedicated bullet below.

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
  - **Or quote explicitly with attribution, satisfying the EU
    quotation conditions.** *"The Open Group ArchiMate® 3.2
    Specification (C226) §7.3 defines Node as 'a computational or
    physical resource that hosts, manipulates, or interacts with
    other computational or physical resources.'"* Quotation is
    permitted under InfoSoc Directive 2001/29 Art 5(3)(d) when all
    four conditions hold:
    - (i) the work has been **lawfully made available to the
      public** — a published spec satisfies; a leaked draft does
      not;
    - (ii) the **source and author are indicated**, unless this
      turns out to be impossible;
    - (iii) use is **in accordance with fair practice**;
    - (iv) use is **to the extent required by the specific
      purpose**.

    Plus the **three-step test** (Art 5(5)): the quotation does
    not conflict with normal exploitation of the source and does
    not unreasonably prejudice the rightholder's legitimate
    interests. *Bulk quotation that substitutes for reading the
    source violates the three-step test even if each individual
    quote is justified.*

    In US law, fair use under 17 U.S.C. §107 is a four-factor
    balancing test (purpose, nature, amount, market effect);
    quotation with attribution helps factors 1 and 3 but is not a
    complete safe harbor.
  - Silent copying without attribution is the only wrong choice.
- **Code samples carry the source's licence.** Computer programs
  are protected as literary works (Software Directive 2009/24/EC
  Art 1(1); Berne Convention Art 2(1)). However, *ideas and
  principles* underlying any element of a computer program are NOT
  protected (Software Directive Art 1(2)) — only original
  expression is. This is the EU-law basis for treating short
  canonical API-call snippets as not protectable: they are
  underlying idea, not expression. Longer, non-trivially-creative
  examples are protected. If a code sample in a skill resembles a
  published example closely, treat it as copyrighted and either
  rewrite for originality or include a source citation and verify
  the upstream licence permits the use:
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
  - **Describe APIs, don't transcribe them.** Software Directive
    Art 5(3) permits a lawful user to *observe, study, or test* a
    program to determine its underlying ideas. Art 6 permits
    decompilation for interoperability under three cumulative
    conditions: (a) by a lawful user, (b) the interoperability
    information is not previously readily available, (c) confined
    to parts necessary for interoperability. Output cannot be used
    for goals other than interoperability, given to others except
    where necessary, or used for substantially similar competing
    software. **Practical bite for this repo:** a skill may
    describe how to call an SDK's API; transcribing a substantial
    portion of the SDK's source code into the skill, even
    reformatted, exceeds Art 6's "necessary for interoperability"
    limit and is not covered by Art 5(3) either.
- **Figures and diagrams are derivative works.** Redrawing a figure
  from a spec or book in different colours is still a derivative
  work and requires the original licence to permit it. Prefer to
  generate original figures when possible, or cite the source figure
  explicitly with permission confirmation.
- **Sample files (XML / JSON / YAML) from specs** are part of the
  spec. ArchiMate sample OEF XML files, BPMN sample XML files,
  OpenAPI example documents — all carry the spec's licence. Do not
  copy them verbatim; construct equivalent samples from scratch.
- **Sui generis database right (EU-only).** Directive 96/9/EC Art 7
  protects databases whose maker has made qualitative or
  quantitative *substantial investment in obtaining, verifying, or
  presenting the contents*. Independent of copyright; 15-year term
  renewing on substantial modification (Art 10). No US analogue.
  Relevant to this repo because spec tables and structured
  enumerations (the ArchiMate® element-and-relationship table,
  OpenAPI schema property enumerations, BPMN element catalogs,
  FHIR resource lists, OData entity sets, SCIM attribute schemas)
  likely meet the substantial-investment test even when individual
  rows are factual.

  *Operative ban:* extraction or re-utilisation of "the whole or a
  substantial part" of the contents (Art 7(1)). Repeated extraction
  of insubstantial parts that aggregate to a substantial part is
  also prohibited (Art 7(5)).

  *Lawful-user safe harbor:* Art 8(1) permits extraction of
  insubstantial parts for any purpose. The substantial /
  insubstantial boundary is qualitative AND quantitative.

  *Operational rule for this repo:* when paraphrasing or
  transcribing a structured table from a copyrighted spec into
  this repo, the *structure* (column choice, row ordering,
  groupings) is protectable separately from cell values. Build
  equivalent structures from primary observation, not by
  copying-and-relabelling. If the equivalence is structurally
  identical, that is itself extraction of a substantial part.

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

The US nominative-fair-use doctrine (*New Kids on the Block v. News
America Publishing*, 9th Cir. 1992) and the EU descriptive-use safe
harbor (EUTMR 2017/1001 Art 14(1)(c)) are both conditional. The US
test bars use that suggests sponsorship, affiliation, or endorsement.
The EU adds an explicit qualifier in **Art 14(2)**: descriptive use
is only protected when made *"in accordance with honest practices in
industrial or commercial matters"*. The CJEU sharpens this in
*Gillette Co. v LA-Laboratories* (C-228/03) and *BMW v Deenik*
(C-63/97). The bullets below cite this framing.

- **Symbol on first AND subsequent significant uses.** For every
  public-visible file (see list above), each registered trademark
  carries ® (or ™ for unregistered claimed marks) on its first
  occurrence AND on each subsequent significant use — heading,
  section opener, list-item lead, and any place where the mark
  would appear standalone if separated from the surrounding
  paragraph. Mid-paragraph repetitions in the same file may omit.
  Internal files don't require the symbol on every mention; one or
  two occurrences per file is sufficient to signal awareness.
- **Use as adjective modifying a noun (product / standard marks).**
  Trademarks identify a product or standard; they don't stand in
  for one. Write *"the ArchiMate® modeling language"*, *"Microsoft®
  Azure® services"*, *"the OpenAPI specification"* — not
  *"ArchiMate's modeling language"*, *"ArchiMates"*, *"OpenAPI is
  a..."*. **Scope: product, standard, and brand marks (TOGAF, UNIX,
  ArchiMate, OpenAPI, Cosmos DB, Blazor, Bicep, etc.).
  Corporate-name possessives are explicitly outside this rule** —
  *"Microsoft's policy"*, *"The Open Group's authority"*,
  *"GitHub's API"* remain acceptable, consistent with how
  Microsoft's own trademark guidelines distinguish brand-asset
  usage from descriptive corporate references. Adjective-only is
  the rule both Microsoft and The Open Group enforce for
  product / standard marks; mis-grammatical use sharpens *Gillette*
  factor #1 risk (commercial connection — see next bullet).
- **Four EU non-honest factors are bright-line bans.** Under
  *Gillette Co. v LA-Laboratories* (C-228/03) para 49, descriptive
  use is NOT honest — and therefore outside the safe harbor of
  EUTMR Art 14(1)(c) — when it does any of the following:
  1. **Creates the impression of a commercial connection** between
     this repo and the trademark owner. *BMW v Deenik* (C-63/97)
     paras 51–53 sharpens this: the test is whether a reader could
     believe this repo is *"affiliated to the trade mark
     proprietor's distribution network"* or has *"a special
     relationship"* with the proprietor. Examples that cross the
     line: *"ArchiMate-certified"*, *"official Open Group skill"*,
     *"endorsed by Microsoft"*, *"Microsoft Azure partner"*.
  2. **Takes unfair advantage of distinctive character or repute.**
     Example: leaning on the ArchiMate® brand to imply this repo's
     skills carry The Open Group's authority.
  3. **Discredits or denigrates the mark.** Example: *"ArchiMate®
     is bloated; here's the lean alternative"* — denigration moves
     descriptive use outside the safe harbor.
  4. **Presents this repo's content as imitation or replica** of
     the trademarked product. Example: a skill / plugin name
     suggesting this repo produces an Open-Group-equivalent product.
- **Logos and brand assets are separate from text marks.** The
  *word* "Azure" used descriptively is nominative fair use. The
  Microsoft Azure *logo* is a distinct creative work and using it
  requires explicit permission (Microsoft's trademark guidelines;
  The Open Group's brand guidelines; similar for every major
  vendor). Do not bundle or inline logos / brand kits / icon sets
  into this repo.
- **No trademark in skill / plugin / agent / product names implying
  affiliation.** Descriptive naming (`architecture-design`,
  `serverless-api-design`) is fine. A hypothetical
  `archimate-official`, `the-open-group-modeller`, or
  `microsoft-api-gen` is not. (This is factor #4 of the previous
  bullet applied at the naming level.)
- **Some trademark policies are more restrictive than nominative
  fair use expects.** Mozilla's Firefox brand, for example, has
  historically restricted even descriptive use in derivative
  products. If the trademark holder publishes a detailed brand
  policy, read it before relying on the general rule. **Note:
  Microsoft and The Open Group both publish per-mark
  attribution-block conventions richer than the legal floor; this
  repo deliberately stays at the legal floor (® on first-and-
  subsequent-significant, no attribution block) for cross-holder
  consistency. See § "Anti-drift fence-posts".**

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
- **AI-authored content status.** Material authored by Claude or
  Codex at this repo's request is disclosed as such in
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
- **Provenance citation is part of remedy 1.** See § "Remediation
  order" — source citation alongside paraphrases of identifiable
  copyrighted content is mandatory, not best-practice. The
  operative rule lives in the remedy.

## Drive-by scope

When triage Q5 hits — the edit touches a file with pre-existing IP
issues that are not what the current edit is about — apply the rules
below. The reflex tilts toward **fix-now over defer**: a concrete
threshold defines the inline-fix path, deferral is the explicit
fallback when the fix exceeds the threshold, and every drive-by
observation is reported regardless of which path it takes.

- **Inline fix (preferred path).** A drive-by fix is inline when
  **all** of the following hold:
  - ≤ 20 lines of additional change beyond the original edit, **OR**
    the fix is a single category of trademark-symbol additions
    (e.g., adding ® to all unmarked first-or-subsequent-significant
    mentions of one mark) regardless of count;
  - the fix stays within files already opened by the original edit
    — no opening additional files;
  - the fix is one of: adding ® / ™ on first-or-subsequent-
    significant mentions, rewriting a near-verbatim paraphrase in
    the same section, swapping a bundled-asset reference for a URL
    reference, adding a missing source citation, correcting an
    adjective-only-rule violation;
  - the fix does NOT require new authoritative-source verification
    beyond what the section already cites.

  If any condition fails → defer-and-flag.

- **Defer-and-flag (fallback path).** When the pre-existing issue
  exceeds the inline threshold (e.g., a whole section that would
  need rewriting, a bundled asset that would need removal,
  citation work the section doesn't yet support), don't expand the
  current edit. Flag it in the output — *"deferred drive-by
  observation at `path/to/file.md:LINE` — `<issue summary>`;
  recommend separate retroactive audit"* — and continue with the
  original task.

- **No silent propagation (source-and-copy rule).**
  - **If the current edit COPIES content** that contains a
    pre-existing violation: fix the copy. Then attempt to fix the
    source within drive-by limits above. If the source fix exceeds
    the limits, fix the copy AND flag the source for retroactive
    audit. Do not leave a violation propagating from a source you
    also touched.
  - **If the current edit REFERENCES content** (cites a section,
    links to a file) containing a pre-existing violation but does
    not copy it: the violation in the referenced content is still
    flagged in the output even if not fixed. Cross-reference is
    propagation of authority — pointing readers to a violating
    section spreads the violation operationally even when no text
    is duplicated.

- **Universal reporting.** Every drive-by observation appears in
  the change-note / commit message — fixes and deferrals alike.
  Templates:
  - **Fix:** *"drive-by fix at `path/to/file.md:LINE` — added ® to
    first-mention 'ArchiMate' (per § Trademark)."*
  - **Defer:** *"deferred drive-by observation at
    `path/to/file.md:LINE` — `<issue summary>`; recommend separate
    retroactive audit."*

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
downstream file an authoring agent generates at runtime. Runtime output is the
user's content; IP hygiene on their content is their concern, not
the skill's.

## Remediation order

The remedy is determined by the **concern type**, not by a
strict-preference cascade. Match the concern to the right remedy in
the table below; remedy 5 is the last resort and is reachable only
when remedies 1–4 are evaluated and inapplicable.

| Concern | Required remedy |
|---|---|
| Verbatim or near-verbatim copyright match (prose, code, figures, tables, sample files) | Remedy 1 (paraphrase) — *not* remedy 4 |
| Trademark first-or-subsequent-significant mention missing ® / ™ | Remedy 2 |
| Bundled third-party asset under a non-permissive licence | Remedy 3 |
| Endorsement / commercial-connection implication, adjective-only-rule violation, *Gillette* factor 1–4 hit | Remedy 4 |
| All of remedies 1–4 evaluated and inapplicable | Remedy 5 (last resort) |

1. **Paraphrase into original expression, with source citation.**
   For near-verbatim copyright matches in prose, code, or figures.
   Source citation is **part of** the remedy, not optional:
   - **Required for paraphrases of identifiable copyrighted
     content.** When remedy 1 fires because the original was a
     near-verbatim match against a specific identifiable source,
     include an in-prose attribution alongside the paraphrase:
     *"derived from ArchiMate® 3.2 §5.2"*, *"per OpenAPI 3.1
     §4.7.2"*. Without the citation, remedy 1 is incomplete and
     the finding is not closed.
   - **Granularity.** One in-prose attribution per paragraph when
     the paraphrase is local; one per section opener when multiple
     paragraphs share a source and don't drift to a different
     source. Don't repeat at every sentence.
   - **Format.** Inline prose, matching the repo's existing voice
     (the way `architecture-design` cites *"per reference §6.4a"*
     and `responsive-design` cites WCAG SC numbers). No footnote
     machinery.
   - **Carve-out: widely-known textbook content.** Paraphrases of
     generic source-agnostic content where any of many sources
     would state the same thing don't need citation. Test: can you
     name the specific document, paragraph, or page the original
     came from? If yes, cite. If the paraphrase would survive
     equivalently from multiple unrelated sources, citation is
     optional.
2. **Add ® / ™ on first-and-subsequent-significant mentions** —
   for trademark mention misses on public-visible surfaces.
3. **Replace a bundled asset with a URL reference** — for
   redistribution-adjacent concerns (except permissively-licensed
   assets, which may be bundled with upstream attribution).
4. **Reword to descriptive nominative** — for endorsement-
   implication concerns and adjective-only-rule violations.
5. **Last-resort removal** of the reference — only if the mention
   is non-load-bearing AND remedies 1–4 are all inapplicable.
   Application of remedy 5 carries a one-line written
   justification per remedy 1–4 in the commit message AND the
   change-note. Format:

   > *Remedy-5 removal of `<reference>`. Justification: 1
   > (paraphrase) — N/A because `<reason>`; 2 (symbol) — N/A
   > because `<reason>`; 3 (asset → URL) — N/A because `<reason>`;
   > 4 (rewording) — N/A because `<reason>`. Load-bearing test:
   > `<why removal does not break the skill's purpose>`.*

   Without this written justification, remedy 5 cannot land.
   Removal of a load-bearing reference (e.g. stripping "ArchiMate"
   from a skill about ArchiMate) is wrong; see § "Scope discipline".

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

## Anti-drift fence-posts

Changes considered for this skill and *deliberately not applied*.
Future revisions should treat them as known-and-rejected, not as
oversights to be fixed. The boundary case for each is recorded so a
re-visitor can engage the existing reasoning rather than re-deriving
it. New entries here require the same brainstorming + design + spec
process; they're not casual additions. Fence-posts are anchored to
current authority — if EU case law shifts to mandate per-mark
attribution, fence-post 1 updates.

### 1. Per-mark attribution block (rejected)

**Considered.** Microsoft and The Open Group both publish trademark
guidelines preferring per-mark credit lines (*"X is a registered
trademark of [holder]"*) at the top or bottom of any document
referencing the mark.

**Rejected because.**
- Nominative fair use under *New Kids* (US 9th Cir. 1992),
  *Welles* (US 9th Cir. 2002), and EUTMR Art 14(1)(c) + Art 14(2)
  does not require attribution blocks. The Lanham Act §1125
  fair-use defense is not predicated on attribution.
- This repo references many trademark holders; per-holder
  attribution blocks would make every public-visible file a list
  of attributions disproportionate to the actual mention density.
- The strictening this revision applies (§ "The check / Trademark"
  — first-and-subsequent-significant ®, adjective-only rule, four
  *Gillette* non-honest factors) supplies operationally meaningful
  protection without the block.

**Boundary case.** If a specific holder's guidelines explicitly
*require* attribution as a precondition for descriptive use of
their mark in derivative work (Mozilla's Firefox brand has
historically been close to this), the rule for that specific
holder is not nominative fair use; the holder's policy applies.
Treat the holder's policy as the operative rule for that mark
only, and document the exception. Do not generalise from a single
restrictive policy to a per-mark block convention.

### 2. Scope expansion into adjacent legal areas (rejected)

**Considered.** Pulling one or more of GDPR / privacy law, patent
law, export control (EAR / ITAR), trade secrets, right of publicity,
defamation, or contract law (CLAs / NDAs / MSAs) into this skill's
scope.

**Rejected because.**
- Each is its own legal regime with its own analysis, sources, and
  remedies. The IP-discipline procedure does not generalise to
  GDPR or patent analysis.
- This skill is procedure for *this repo's* IP discipline, not a
  multi-domain legal-compliance framework.
- § "Honest limits" already names these explicitly as out-of-scope.
  Future revisions must update that section if they pull anything
  out of out-of-scope; do not silently expand.

**Boundary case.** If a future skill build introduces material that
*is* clearly subject to one of these regimes (e.g., a skill that
processes personal data and engages GDPR / CCPA), the right
response is a *separate* skill or compliance review, not a
retrofit of this skill.

### 3. Mechanical word-count or pattern-match rules that override judgment (rejected)

**Considered.** Replacing the *>6 consecutive content words*
paraphrase heuristic with a hard cut-off (e.g., *>4 words* must be
quoted with attribution; *>12 words* triggers automatic copyright
finding); regex-pattern auto-detection of trademarks; automated
similarity-detection.

**Rejected because.**
- The legal test for substantial similarity of protectable
  expression is qualitative; it is not a word-count.
- A mechanical cut-off mis-classifies both ways: would flag generic
  textbook content as copyright matches, would miss cases where 3
  consecutive content words capture a protectable original phrase.
- The skill's stated character ("Judgment-heavy by design") is the
  protection. Replacing it with mechanical rules turns the
  procedure into a validator — the failure mode this skill
  explicitly disclaims in § "Overview".

**Boundary case.** The existing *>6 words* language stays a
*heuristic* — useful as an attention-forcing function, not a legal
test. The actual legal test remains qualitative similarity. Any
future rule of similar shape (e.g., *"more than N pixels of figure
overlap"*) is heuristic-only; hard rules overriding judgment cross
this fence-post.

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

- **EU Trade Mark Regulation (EU) 2017/1001** — **Article 14(1)(c)**
  on limitation of the effects of an EU trade mark (permits
  descriptive use of another's mark where necessary to indicate the
  intended purpose of a product or service); **Article 14(2)** on
  the conditioning qualifier (descriptive use is only permitted
  where made *"in accordance with honest practices in industrial
  or commercial matters"*); Recital 21 reinforces.
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
- ***Gillette Co. v LA-Laboratories Ltd Oy***, Case C-228/03 (ECJ,
  17 March 2005) — operative test for "necessary" descriptive use
  (para 39) and the four-factor "honest practices in industrial or
  commercial matters" test (para 49): commercial-connection
  impression, unfair advantage of distinctive character or repute,
  discrediting / denigration, imitation / replica presentation.
  [eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62003CJ0228](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62003CJ0228)
- ***BMW AG v Deenik***, Case C-63/97 (ECJ, 23 February 1999) —
  permitted descriptive use of a mark to advertise repair /
  specialisation in the trademarked product, conditioned on no
  impression of a *"commercial connection"* — affiliation to the
  *"distribution network"* or *"special relationship"* with the
  proprietor (paras 51–53).
  [eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:61997CJ0063](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:61997CJ0063)
- **UK Trade Marks Act 1994, s.11(2)(b)** — descriptive-use limitation
  in UK law (post-Brexit equivalent of EUTMR Art. 14).
  [legislation.gov.uk/ukpga/1994/26/section/11](https://www.legislation.gov.uk/ukpga/1994/26/section/11)

### Copyright law — statute, directive, and case law

- **Berne Convention for the Protection of Literary and Artistic
  Works** (1886, as amended 1979) — Art 2(1) (literary and artistic
  works include computer programs as literary works); Art 9 (right
  of reproduction); Art 10 (quotation exception). Foundation for the
  EU directives below.
  [wipo.int/treaties/en/ip/berne](https://www.wipo.int/treaties/en/ip/berne/)
- **Directive 96/9/EC (Database Directive)** — Art 7 sui generis
  right (extraction or re-utilisation of substantial part); Art 8
  lawful-user safe harbor (insubstantial-part extraction); Art 9
  exceptions; Art 10 (15-year term, renewing on substantial
  modification).
  [eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31996L0009](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31996L0009)
- **Directive 2001/29/EC (InfoSoc Directive)** — Art 5(3)(d)
  quotation exception (four conditions: lawfully made available,
  source indicated, fair practice, extent required); Art 5(5)
  three-step test (special cases, no normal-exploitation conflict,
  no unreasonable prejudice).
  [eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32001L0029](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32001L0029)
- **Directive 2009/24/EC (Software Directive)** — Art 1(1) computer
  programs protected as literary works; Art 1(2) ideas and
  principles not protected; Art 5(3) observe / study / test; Art 6
  decompilation for interoperability under three cumulative
  conditions.
  [eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0024](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0024)
- **US Copyright Act, 17 U.S.C. §102** — object of copyright
  protection (original works of authorship fixed in any tangible
  medium of expression); excludes any "idea, procedure, process,
  system, method of operation, concept, principle, or discovery"
  per §102(b).
  [uscode.house.gov](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title17-section102)
- **US Copyright Act, 17 U.S.C. §107** — fair use four-factor
  balancing test (purpose / character of use; nature of the
  copyrighted work; amount / substantiality of the portion used;
  effect on the market for the original).
  [uscode.house.gov](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title17-section107)

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
  Aug. 18, 2023), **affirmed**, No. 23-5233 (D.C. Cir. Mar. 18,
  2025) — held that works produced without human creative
  contribution are not copyrightable under 17 U.S.C. §102(a). The
  D.C. Circuit affirmance hardens the rule from district-court
  precedent to circuit-court precedent in the D.C. Circuit.
  [courtlistener.com](https://www.courtlistener.com/) (search by docket number).
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

- **URLs are for reference, not runtime fetch.** The Claude Code or Codex
  sandbox in this repo may not have network access to most of
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
