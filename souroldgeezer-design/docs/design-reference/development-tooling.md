# Development tooling

Software-design owns this shared procedure. Read it when a development tool or
reference-derived data pipeline materially affects the task. Explicit tooling
requests use the existing Build, Review, or Lookup modes; other design skills
retain their domain decisions while consulting the relevant sections here.
A known sufficient operation or ordinary small edit needs no tooling assessment.

## Choose a useful intervention

Start with a concrete obstacle: a fragile manual operation, missing capability,
repeated friction, or a consequential verification gap. Discover plausible
repository commands, host tools, and established ecosystem or industry-standard
solutions within the task boundary. Do not limit candidates to installed tools.
Recommend a suitable existing tool even when absent: a new need may be the reason
it has never been installed. Explain its fit, setup/dependency costs, and relevant
constraints before choosing custom implementation. Availability is a constraint,
not evidence that a replacement should be written. Keep the recommendation distinct
from installation; respect existing setup authority and continue independent work.

Pick up task-specific favorites from the current request/conversation and relevant
existing project guidance, documentation, or configuration found through bounded
discovery. No preference file, schema, syntax, or workspace location is required.
Apply each preference to its stated task; a favorite for one task is not a global
mandate. Respect the current explicit request when preferences conflict. Recommend
a favored suitable tool even when absent; explain a material task-fit or project
constraint conflict rather than silently substituting another tool. Ask only when
a consequential conflict cannot be resolved from the available context.

Respect explicit user or project tool choices. For a narrow, well-solved operation,
recommend a well-established suitable utility before alternatives or custom code.
For choices that reshape a user's workflow or toolchain, account for their
preferences rather than treating industry adoption as a mandate. Keep these
recommendations tool-neutral; no fixed product list is needed.

Where user/project choices leave alternatives open, prefer the most open, least
restrictive suitable licence for the intended use. Check the actual licence/version and obligations rather than
inferring them from popularity, availability, or an open-source label. Explain
material tradeoffs when compatibility, task fit, or project constraints favor
a more restrictive option; do not select an unsuitable tool for its licence alone.

Choose among using
a suitable existing tool, adapting it, executing directly, writing a temporary
script, and retaining a maintained tool. Prefer suitable reuse, but do not require
a second use before building something that enables worthwhile work now.

Consider construction, verification, discovery, and maintenance costs against the
work enabled and the consequences of mistakes. A short local script may be enough;
mandatory forecasts, telemetry, a framework, and enterprise controls are unnecessary.
Choose temporary versus retained deliberately. For a retained tool, give it a clear
purpose, documented invocation and inputs, proportionate tests, and an understandable
maintenance owner. Consolidate overlapping tools and retire obsolete ones when
that is within scope, preserving consumers and useful regression protection.

Design for the actual operators: people, agents, or both. Where applicable, support
focused queries, bounded output, stable structured results, actionable diagnostics,
and explicit failure behavior. Distinguish an empty result from incomplete work,
invalid input, or an unavailable capability. Make side effects discoverable and
preserve relevant project safeguards. Validate the operation that matters, including
failure paths proportionate to its consequences, rather than only command startup.

A read-only Review recommends improvements without creating tools or changing data.
Authorized implementation may directly create a small enabling tool within its
outcome. Ask only for material scope or authority changes under the active project
contract. This procedure grants no deployment, installation, publication, or
external-service authority and does not replace strict approved-plan boundaries.

## Reference-derived data and executable mechanics

For extraction, transformation, maintenance, or consumption of reference-derived
data, keep four evidence questions separate:

| Layer | Evidence needed |
|---|---|
| Source fidelity | Authoritative source and version, useful page/section references, and preservation of relevant qualifications, relationships, units, and exceptions. Record input/output provenance and applicable source terms. |
| Data validity and coverage | Structural correctness plus identity accounting against the declared extraction scope. A valid schema or equal record counts alone cannot establish fidelity or completeness. |
| Runtime support | Evidence that the consumer implements the represented mechanics and their prerequisites. Record unsupported constructs explicitly. |
| Observed behavior | Representative execution compared with independently checked source-derived expectations, including meaningful interactions, limits, and exceptions. Source inspection alone establishes no execution result. |

Locate the defect before editing outputs. Repair the importer or transformation and
regenerate derived artifacts when the defect belongs upstream. Preserve intentionally
authored data and recorded overrides; keep their precedence explicit and check that
regeneration retains them. Avoid patching generated records while leaving their
producer wrong. Where updates matter, compare source revisions and the resulting
data changes, including removed identities, changed relationships, and overrides
that may no longer apply. Use the source format and project workflow already in use.

Surface ambiguous interpretations and unsupported constructs with their source
locations and affected outcomes. Do not silently choose semantics, flatten an
exception, or report unsupported work as a successful empty result. Ask for an
interpretation only when it blocks the next consequential decision; continue
independent supported work. Keep partial support and partial extraction explicit.

Use independently checked source examples as an oracle: a generator and checker
can agree on the same mistake. Trace representative source clauses through data,
consumer implementation, and observed results. Exercise important interactions,
boundaries, and exceptions, not just isolated records or happy paths. Explain any
remaining disagreement and which layer owns it. Available records alone do not
establish that a complete simulation is runnable: objectives, actors, controllers,
mechanics, and outcome measures may also be required by the intended scenario.

Keep this proportional to a local hobby project: a few source examples, a small
fixture, and a focused execution can be sufficient for a bounded task. Describe
what was checked and what remains partial; do not imply source-wide conformance
or complete simulation readiness from that bounded evidence.
