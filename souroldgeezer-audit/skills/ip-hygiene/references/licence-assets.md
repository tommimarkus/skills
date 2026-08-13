# IP Hygiene Licence And Asset Checks

Load this for third-party code, documentation, schemas, data, fonts, binaries,
images, audio/video, logos, SDKs, samples, or other bundled material. Licence
analysis is source-, file-, version-, act-, and distribution-specific. Read the
actual operative text through [authority-index.md](authority-index.md).

## Establish The Permission Chain

- **`IP-LIC-1 Identity and coverage`:** record source/repository, version or
  commit, exact files, holder/provenance evidence, licence identifier and full
  text, notices, and any discrepancy between metadata and file headers. Absence
  of a licence is absence of recorded permission; it is not by itself a finding
  about ownership, infringement, or whether an exception applies.
- **`IP-LIC-2 Intended act`:** map the actual act: execute privately, copy,
  modify, translate, link/import, combine, aggregate, embed, distribute source,
  distribute object/binary, publish as a service, or provide remote network
  interaction. Licence duties attach to specified acts and material, not merely
  to a dependency's presence.
- **`IP-LIC-3 Distribution`:** record source/binary/container/archive/rendered
  output, whether third-party material is extractable, recipients/audience, and
  the delivery channel. Repository access, package publication, and network use
  can be different acts.
- **`IP-LIC-4 Licence layering`:** check dual licensing choices, licence-version
  selectors, exceptions and additional permissions, file-level overrides,
  generated/vendored notices, and separate licences for code, docs, examples,
  data, or assets. Confirm that the reviewer is eligible to select the proposed
  option.
- **`IP-LIC-5 Notice survival`:** required copyright, licence, attribution, and
  `NOTICE` information must survive a move, split, extract, refactor, vendoring,
  generation, bundling, transpilation, or minification. The obligation attaches
  to the covered material, not to the file path it started in. Removing or
  truncating a notice while refactoring is a distinct act from copying. Where a
  licence specifies the location or form of a notice, relocation must still
  satisfy that form.

Never infer that a repository-wide licence covers third-party material. The
repository licence ordinarily speaks for material its licensor controls; keep
third-party scope and notices explicit.

## Licence Families

### Permissive software

For MIT, BSD, Apache-2.0, and similar terms, inspect the actual grant and the
permissive notice and attribution terms. Determine which copyright, licence,
disclaimer, modified-file, and `NOTICE` obligations apply to the particular
source or binary distribution. Do not reduce all permissive licences to one
generic notice rule, and do not call OSI categorization the operative text.

### GPL-family software

Analyze GPL, LGPL, and AGPL separately and by version. Record modification, combination, linking or importing, aggregation, distribution, and network interaction
rather than treating “copyleft” as one bundling prohibition.

- Execution or private modification is not the same event as conveying a copy.
- For GPL-covered material, source, object-code, corresponding-source, notice,
  and downstream-rights conditions depend on what is conveyed and how works are
  combined. Mere aggregation and a combined work are distinct classifications.
- LGPL terms add library-specific permissions and relinking/reverse-engineering
  protections; static and dynamic delivery can require different compliance
  evidence.
- AGPL version 3 section 13 concerns a modified Program that supports remote
  network interaction; ordinary network availability is not a blanket trigger
  for unrelated works.
- Linking/plugin/import boundaries and combined-work classification can be
  fact-sensitive and disputed. If the repository decision depends on that
  classification, set `counsel outcome: required` rather than declaring
  compatibility.

GNU FAQs are holder/licensor guidance. The exact licence and any holder-granted
exception or additional permission are the operative licence terms.

### Creative and non-code material

For Creative Commons material, identify the exact version and legal code; then
evaluate attribution, indication of changes, ShareAlike for adaptations,
NonCommercial scope, and NoDerivatives limits on sharing adapted material.
Separate permission to reproduce from permissions in embedded works, privacy or
personality rights, and trade marks. Do not assume a CC licence is suitable for
software code.

For fonts, distinguish using a typeface, embedding font data, bundling an
unmodified font, modifying/converting/subsetting it, and redistributing it. For
the SIL OFL, inspect retained licence/copyright information and any Reserved Font
Names; name conditions concern modified Font Software, not every rendered image
or document.

For documentation, schemas, data, and media, inspect material-specific terms
and separate layers:

- documentation prose, code samples, and images can have different licences;
- schemas can contain functional interface elements, expressive annotation or
  examples, and protected selection/arrangement;
- data can involve content rights, database copyright, and sui generis database
  rights independently of a dataset licence;
- media, logos, icon sets, and certification marks can carry copyright plus
  trade-mark/holder-policy restrictions.

CC0 or another dedication/waiver must cover the exact material and jurisdictional
rights it can reach. Do not translate “publicly accessible” or “open standard”
into permission to redistribute the source artifact.

## Decision Controls

- A canonical link is the conservative alternative when no local copy is
  required, but record that it does not authorize copies already bundled.
- A compatible-looking licence label is insufficient when the file, holder,
  version, exception, or distribution form is unclear.
- Preserve every operative notice with the covered material in the location and
  form the licence requires; avoid an attribution block that falsely suggests
  one licence covers all third-party content.
- Unknown permission yields `insufficient-evidence` or `not-evaluated`, not an
  automatic infringement finding. Restricted or incompatible terms yield a
  block only when the actual terms and intended act substantiate it.
- Bespoke agreements, disputed exceptions, contested ownership, and unresolved
  combined-work/copyleft classification require counsel.
