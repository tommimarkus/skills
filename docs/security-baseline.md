# Security baseline

This is the security baseline for the Sour Old Geezer plugin marketplace. It
covers the repository, the plugin bundles installed from it, local helper
scripts, host adapters, generated galleries, and the Dediren provisioner. It is
a maintainer self-assessment, not a certification or attained-conformance
claim. Vulnerability handling lives in [SECURITY.md](../SECURITY.md).

## Assets and trust boundaries

The assets are the integrity of shared skill instructions and adapters, the
developer's repository and host configuration, package files read by helpers,
the local plugin-data directory, and evidence used to decide what reaches
`main`. The marketplace does not operate a hosted service and its bundled
skills do not collect telemetry; third-party hosts and tools retain their own
data practices as described in the [privacy policy](../PRIVACY.md).

Trust changes at these boundaries:

- a maintainer commits source and pushes `main` to GitHub;
- a host installs and executes plugin-controlled instructions and helpers;
- helpers read caller-controlled repositories, paths, Markdown, JSON, CSS, and
  SVG;
- the architecture launcher downloads a Dediren release into host-owned plugin
  data and starts its local process; and
- generated HTML opens in a browser with package-controlled labels, themes,
  paths, and rendered SVG images.

GitHub, the installed Claude Code, Codex, or Copilot CLI, Java, and the host
operating system remain trusted dependencies. A user authorizes the repository
and tool access each host grants; plugin installation is not a sandbox.

## Threats and controls

| Threat | Maintained control | Remaining limit |
|---|---|---|
| Malicious or accidental source reaches `main` | Clean exact-commit candidate gates, version guard, and an optional repository pre-push check bind local evidence to the pushed `main` commit. | A writer can bypass local hooks or use `--no-verify`; there is no CI or required status check. |
| A helper reads outside the caller-selected source root | Automatic Lean readers resolve a declared root and skip out-of-root paths and link targets without reading or echoing their contents. | An explicitly selected file is authorized input; host permissions still govern what a manually invoked tool can read. |
| Archive entries escape or overwrite the Dediren install root | Provisioning verifies the pinned archive checksum, rejects traversal, unsafe/cyclic links, duplicate overwrites and special files, bounds member/file/expanded sizes, and writes contained files before an atomic install. | The release origin, GitHub availability, TLS stack, and host filesystem remain dependencies. |
| Untrusted SVG, text, CSS, or paths become active gallery content | The gallery contains encoded SVGs as inert `img` data, serializes labels contextually, permits only bounded theme values, fetches no external assets, and contains all package inputs and output beneath the package root. | Users may open the generated file in a browser with extensions or policies outside repository control. |
| A tampered Dediren download executes | The launcher pins a release, fetches its checksum manifest first, verifies the archive before unpacking, and documents optional GitHub attestation verification for manual air-gapped transfer. | Automatic provisioning verifies checksums, not a repository-owned signature or attestation policy. |
| Sensitive vulnerability details become public | `SECURITY.md` directs reporters to GitHub private vulnerability reporting and explicitly marks its rollout pending. | Until enablement is verified, no private fallback address is declared. |
| Validation evidence is mistaken for remote enforcement | The publication receipt names the exact commit/tree and recorded gate results; documentation calls the control local and bypassable. | Repository writers and GitHub account security remain the final control plane. |

Package-controlled content is data throughout these controls. It must not be
interpreted as HTML, script, CSS declarations, command arguments, filesystem
authority, or an external-resource instruction merely because it appears in a
package.

## Publication and update control

`python3 -B scripts/publication_check.py --repo-root . record` runs the ordered
candidate gates, including the unconditional safety-flagged host smoke, against
one clean commit and stores a local receipt in the repository's Git common
directory. A single atomic version-only follow-up uses `record
--version-followup`. The optional repository hook calls `check-push` and refuses
a `main` update that the receipt does not cover. It changes no global Git
configuration and refuses to overwrite another hook.

This is mistake resistance for the maintainer's local publication path. It is
not independent review, remote enforcement, artifact signing, or provenance.
Release and security-update communication identifies the fixed plugin version
and tells users to refresh through their host's normal plugin manager.

## Assurance targets and gaps

[OWASP Software Component Verification Standard 1.0](https://scvs.owasp.org/)
Level 1 is the repository's target. The rows below are a gap matrix against its
six control families; `partial` means useful evidence exists but the family is
not fully demonstrated.

| SCVS family | Current evidence | Status and gap |
|---|---|---|
| V1 Inventory | Runtime manifests, marketplaces, `uv.lock`, plugin versions, the pinned Dediren release, and source inventories are versioned. | **Partial:** no release-specific inventory proves every first-party, transitive, host, and tool component used for each plugin publication. |
| V2 Software Bill of Materials | Dediren releases publish CycloneDX SBOMs and manual verification is documented. | **Gap:** this marketplace does not generate or publish an SBOM for each plugin release. |
| V3 Build Environment | The repository declares Python and Java floors and exact local candidate gates. | **Partial:** publication is a maintainer-local push with no hosted repeatable build record or independently enforced environment. |
| V4 Package Management | Python development tools are locked; plugin/runtime versions and checksum-verified Dediren downloads are explicit. | **Partial:** external host CLIs, Java distributions, and all transitive build inputs are not captured in one managed release inventory. |
| V5 Component Analysis | Security and IP audits are release gates for applicable changes, and dependency changes are reviewable in versioned files. | **Gap:** publication has no automated software-composition or vulnerability scan covering every dependency and release. |
| V6 Pedigree and Provenance | Git history identifies source commits; the local receipt binds checks to a tree; Dediren exposes upstream checksums and attestations. | **Partial:** the marketplace publishes no consumer-verifiable provenance for the pushed plugin state. |

SCVS Level 1 is therefore a direction for closing these gaps, not a claim of
compliance. No [SLSA](https://slsa.dev/spec/v1.0/) Build level is claimed. The
local receipt and Git commit history do not satisfy SLSA provenance
requirements.

## Accepted residual risk and review

The chosen operating model has one maintainer, local pre-push evidence, no CI,
no mandatory peer approval, and no repository-defined required status check.
It accepts the risk that a compromised or careless writer can bypass local
controls and publish directly. Adding CI, branch protection, signing, hosted
provenance, or a paid service needs a separate decision and is not implied by
this baseline.

Review this baseline when a plugin adds a network service, new downloaded
runtime, executable hook, new package format, or new publication route; when a
security incident changes an assumption; and at least with each security audit.
Record newly closed or opened SCVS gaps from observed release evidence.
