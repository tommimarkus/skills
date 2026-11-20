# IP Hygiene Checks For AI-Generated Content

Use the existing `IP-SRC-5`, `IP-COPY-1`, and `IP-LIC-*` criteria for the exact
file, intended act, and audience. A single artifact can contain generated,
human-authored, and third-party material.

## Evidence And Decision

1. **Establish provenance.** Record the output version and, where available, the
   provider, model or checkpoint, account or plan, generation date, source inputs,
   and human revisions. Distinguish creation records, author disclosures, and
   metadata or watermark signals. An origin signal alone leaves ownership and
   permission open. Keep sensitive prompts and inputs out of public reports.
2. **Identify the human expression.** Locate creative choices visible in the
   finished work. Compare sketches, source passages, revision diffs, and creative
   selection or arrangement where relevant. Prompt wording, iteration count,
   routine edits, or picking one output alone leave authorship of the result
   unestablished. Ground any copyright claim in the particular human contribution
   and applicable law. Document who controls those rights before licensing them.
3. **Trace third-party material.** Check permission to submit or transform
   reference images, text, code, datasets, and other supplied inputs. Inspect the
   final output for identifiable retained or reproduced expression, licences,
   and notices. Compare an actual source when one is identified. Similarity can
   warrant investigation. Training disclosures and detector results leave
   material-specific copying and permission to be established separately.
4. **Read the terms that applied.** Retrieve the service or model terms for the
   version, plan, and date used. Check commercial use, export, redistribution,
   and attribution only as relevant to the intended act. Read any output grant
   or assignment within its stated scope. Provider terms govern the provider
   relationship. Statutory protection and third-party permission each need
   their own basis. Check input and output terms alongside the tool or weights
   licence, especially when a licence notice would cover a mixed package.

If public sharing depends on missing plan terms, name that gap and stop the
affected decision. Apply the existing counsel rules when applicable.

## Project Licence And Notice Files

Start with the publisher's intent for each relevant path. Determine whether they
want to distribute the material, offer others reuse rights, or make a copyright
claim. Check their authority for each act they choose. A publisher can omit a
copyright claim where the publication decision does not depend on one.

- **`LICENSE` and scope.** Preserve the full standard licence text. State which
  files or directories it covers in an adjacent scope note or the README. Use an
  asset-specific entry if its terms differ. Check whether the provider's terms
  support the reuse rights the project wants to offer downstream.
- **`NOTICE` or attribution file.** Preserve required upstream text and identify
  the material it covers. Add a concise AI provenance note if it helps a reader
  understand the release. Mark it as a disclosure and cite any applicable asset
  terms. Keep optional provenance distinct from mandatory attribution.
- **`COPYRIGHT`, when useful or required.** Record supported rightsholders and
  the works or portions they cover. Make the publisher's optional claim only at
  the scope they choose and can support. A voluntary statement of no claim
  leaves provider terms and third-party rights in place. If the publisher wants
  a dedication such as CC0, scope it to rights they can waive or licence. [CC0 legal code](https://creativecommons.org/publicdomain/zero/1.0/legalcode.en)

For example, if the evidence supports publishing playing-card backs and the
publisher wants MIT for code only, keep the MIT text in `LICENSE`. The README
can say “The MIT licence applies to `src/`. See `NOTICE` for `art/card-backs/`.”
`NOTICE` can identify the generated backgrounds and state “The project makes
no copyright claim in these backgrounds.” Add the verified asset terms and
any required notices to that entry. If the publisher chooses to claim the
hand-drawn motif or original layout, record the supported contribution and its
scope. Routine resizing or cleanup leaves authorship of the generated elements
unestablished.

## Authority

- **EU first.** The CJEU's general originality test turns on an author's creative
  choices expressed in the work. Apply it to the evidenced contribution and
  check applicable national law where it matters. [Cofemel, C-683/17, paragraphs 29–32](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX%3A62017CJ0683)
- **EU Commission explanation.** Its answer on translations illustrates the
  distinction between machine-generated text and potentially original human
  post-editing, within that specific context. [Written answer E-000023/2026](https://www.europarl.europa.eu/doceo/document/E-10-2026-000023-ASW_EN.pdf)
- **Other jurisdictions when relevant.** Check local rules and current authority.
  The UK has a specific computer-generated works provision. The US Copyright
  Office report explains its approach to human expression, prompting, and
  modification or arrangement. [UK CDPA section 9](https://www.legislation.gov.uk/ukpga/1988/48/section/9)
  [US Copyright Office report, Part 2](https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf)
