# Layout And Flow Procedure

Use this procedure for Build, Extract, or Review work involving a multi-screen
flow, material layout redesign, dashboard or workspace composition, or an
unresolved layout direction. In Lookup, use it only for an explicit layout- or
flow-mechanics question. Skip it for routine component/state work and for narrow
changes whose layout direction is already approved.

Keep the result framework-neutral. Project-native patterns take precedence when
they satisfy the core app-design contract. This procedure does not own brand,
typography, art direction, or a particular diagram or design application.

## Flow Mapping

Create or extract the flow in this order:

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

Give every step a stable flow-step ID and trace it to the route or screen, user
action, visible system feedback or state, next paths, and recovery. Use a
compact table for a mostly linear journey:

| Step ID | Route / screen | User action | System feedback / state | Next or recovery |
|---|---|---|---|---|
| `F-01` | Named route or screen | User intent | Observable response | `F-02`, exit, or recovery ID |

Use a flow diagram only when branching, loops, or cross-channel transitions
become materially clearer than in the compact table. Keep the stable IDs in the
diagram and accompanying contracts; the diagram format is the user's or
project's choice.

For each screen reached by the flow, complete a screen-state matrix covering
default, loading, empty, error, offline, unauthorized, success, and
destructive-confirmation behavior. Mark a state not applicable only with a
reason. State changes must preserve a visible next action or recovery path.

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

When a material direction is unsettled, present two or three low-fidelity text
wireframes. Label every alternative `unapproved`, identify its primary region,
show wide and narrow reading order, and explain the tradeoffs for flow,
information density, recovery, and adaptation. Then pause for user selection or
combination before committing that direction to implementation or a settled
design contract.

Skip alternatives for a narrow fix or an already-approved layout. Disclose the
reason for the skip so an omitted checkpoint is not mistaken for silent design
approval.

## Selected Layout Contract

After selection, write one layout contract for each screen or stable screen
family. Record:

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

Trace region IDs back to their flow-step IDs and forward to route/screen and
state contracts. When a wide supporting pane becomes a narrow single-column
journey, place or reveal it at the point where it supports the primary task;
do not move it ahead of that task in DOM or focus order merely to match a wide
visual position.

For Build, the target flow map, selected contract, state matrix, and responsive
transformation are design inputs to implementation. For Extract, record what
the current UI actually does, its entry and exit points, dead ends, and recovery
or resumption. For Review, attach each finding to a flow-step ID or layout region
rather than issuing a screen-wide opinion. Lookup stays concise: answer the
explicit mechanic and retain the normal one-line footer.

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
