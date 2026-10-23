# Layout And Flow Procedure

Use relevant sections for multi-screen flows, material layout redesign,
dashboards, workspaces, and layout or flow questions. Keep analysis proportionate
to the requested outcome. Routine component/state work and narrow approved-layout
changes can skip the procedure. Substantial work still needs relevant flow and
recovery reasoning after direction is approved; it need not recreate unchanged
contracts or produce every artifact below.

Keep the result framework-neutral. Project-native patterns take precedence when
they satisfy the core app-design contract. This procedure does not own brand,
typography, art direction, or a particular diagram or design application.

## Flow Mapping

Inspect the user flow in the order useful to the decision; these are prompts
for relevant branches, not a mandatory inventory for every screen:

1. Name the actor and outcome: the user's goal, entry, preconditions, and
   observable completion. Do not use a component tree, service boundary, or
   backend job sequence as a substitute for user intent.
2. Separate the current versus target journey. Do not silently present a
   proposed improvement as existing behavior.
3. Record the main path from entry to completion.
4. Add branches and loops, including decisions that return to an earlier step.
5. Add cancellation, abandonment, help, and resumption paths.
6. Add error, offline, and authentication recovery, including expired sessions
   and preservation of user work.
7. Include external touchpoints such as email, documents, support, another
   channel, or another service when the user must cross them.
8. Review for unexplained dead ends and duplicate steps, including back,
   reload, and interrupted-session behavior.

Keep important links between user action, route/screen, visible feedback, next
paths, and recovery. Use stable flow-step IDs and a compact table when they help
coordinate a multi-screen change or a requested formal review:

| Step ID | Route / screen | User action | System feedback / state | Next or recovery |
|---|---|---|---|---|
| `F-01` | Named route or screen | User intent | Observable response | `F-02`, exit, or recovery ID |

Use a flow diagram only when branching, loops, or cross-channel transitions
become materially clearer than in the compact table. Keep the stable IDs in the
diagram and accompanying contracts; the diagram format is the user's or
project's choice.

Consider relevant default, loading, empty, error, offline, unauthorized, success,
and destructive-confirmation behavior. Use a screen-state matrix when it makes
material branches or ownership clearer; do not enumerate irrelevant states or
justify each omission. State changes preserve a visible next action or recovery
path.
For an operation that crosses about one second, record the state transition
information required by the [operation-feedback default](../../../../docs/app-reference/app-design.md#39-loading-error-empty-offline-and-unauthorized-states): status onset,
known or unknown total, blocking scope, and completion, failure, cancellation,
timeout, and awaiting-input paths.

## Layout Direction And Alternatives

Derive screen regions from content priority, task order, and relationships in
the mapped flow. Start from the smallest fitting relationship, not a vendor
template. Useful starting points include:

- **single-task:** one primary task with supporting explanation and actions;
- **list-detail:** a collection and independently meaningful selected detail;
- **supporting-pane:** primary work plus context or tools meaningful only with
  that work;
- **feed/dashboard:** peer summaries or work queues whose grouping and weight
  express priority; and
- **compliant project-native pattern:** an existing local layout that preserves
  flow, state, adaptive-order, and accessibility requirements.

These patterns are options, not mandatory templates. Reject a pattern when its
extra regions compete with the primary task or when its narrow transformation
would remove an essential step.

For authorized implementation, choose a sensible reversible direction from the
user goal, constraints, and project patterns and proceed. Explain a consequential
choice briefly. Do not require alternatives or approval for routine design
judgment; preserve an already-approved direction.

When the user asks to compare or select directions, present meaningful rough
alternatives with wide/narrow order and tradeoffs; two or three often suffice.
Label proposals `unapproved` when approval is pending, and pause for user
selection or combination when the user requested that checkpoint. Also ask when
a material product choice cannot safely be inferred; continue independent work
while it is unresolved. Do not invent product policy under the guise of a
reversible layout choice.

## Selected Layout Contract

After choosing a direction, preserve the relevant layout decisions in source or
a compact contract for the affected screen or stable screen family. Record the
following when they matter to implementation or a requested handoff:

- each region's purpose, flow-step IDs, priority, and relationship to the
  primary task;
- wide placement, narrow order, visibility, and maximum measure or other size
  constraints;
- the adaptive operation used at each content-derived transition: **reflow**
  within the same presentation, **reveal** on user request, **reposition** while
  preserving meaning, or **presentation** as an equivalent control or surface;
- state variants from the screen-state matrix, including how feedback and
  recovery affect placement and focus;
- behavior at 320 CSS pixels and 400% zoom, including any content that
  legitimately needs two-dimensional scrolling and its accessible fallback;
- RTL and text expansion behavior, logical alignment, wrapping, and mirrored
  directional affordances; and
- visual, DOM, reading, and focus order. A visual rearrangement must not create
  a meaning-changing DOM, reading, or focus sequence.

When using region and flow-step IDs, keep their links to route/screen and state
contracts coherent. When a wide supporting pane becomes a narrow single-column
journey, place or reveal it at the point where it supports the primary task;
do not move it ahead of that task in DOM or focus order merely to match a wide
visual position.

For Build, use only the flow map, selected contract, state matrix, and responsive
transformation artifacts needed for the change. For Extract, record what
the current UI actually does, its entry and exit points, dead ends, and recovery
or resumption. For Review, locate findings in the affected source, flow step, or
layout region rather than issuing a screen-wide opinion. Lookup stays concise:
answer the explicit mechanic and disclose only material evidence limits.

## Evidence Boundaries

- Static evidence proves only the declared design and source-visible
  traceability; it does not prove rendered order or successful journeys.
- DOM, behaviour, and visual claims require rendered evidence at the matching
  verification layer, including real keyboard and adaptive-layout checks where
  those claims are made.
- Comprehension, user-goal validity, and end-to-end journey success require
  human/user evidence. A screenshot alone cannot certify flow correctness.

Use the weakest honest verification layer and disclose missing evidence. A
static wireframe may establish the proposed region priority; it cannot establish
that users understand the flow or can recover from every runtime branch.
