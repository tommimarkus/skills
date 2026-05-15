# Source-Weighted Selection

Use this architecture-design reference when source evidence permits multiple
valid ArchiMate element, relationship, or view choices.

This workflow is ArchiMate 3.2 based. Do not import ArchiMate 4 language until
the skill, fixtures, validation, and exports upgrade together.

## Weights

- **44 standards/method**: The Open Group, Lankhorst, ISO 42010. Model the
  stakeholder concern, keep abstraction deliberate, prefer semantically valid
  ArchiMate concepts, and avoid inventory diagrams.
- **34 practical notation/readability**: Wierda, Hosiaisluoma, Bizzdesign.
  Component = app/module/boundary; Service = exposed behavior/dependency;
  Interface = GUI/API/access point; Function/Process = internal behavior only
  when it is the view concern. Use the narrowest relationship and split
  unreadable mixed-concern views.
- **14 enterprise practice**: MIT CISR and IASA. Use Business Capability, Value
  Stream, Goal, Outcome, Course of Action, decision, or quality attribute only
  with architect intent or business-source evidence.
- **8 artifact/platform overlays**: Kotusev, SAP LeanIX, Microsoft CAF, AWS WA.
  Prefer small useful artifacts; treat portfolio/cloud quality frameworks as
  overlays, not generic ArchiMate classifiers.

Higher-weight lanes win unless a lower-weight source is the only exact-domain
source. Semantic validation beats practitioner guidance. Use semantic Grouping
only for evidenced responsibility, trust, participant, environment, ownership,
hosting, or orchestration boundaries; layout grouping stays in view/render
metadata.

Confirm live only when load-bearing: The Open Group ArchiMate library,
Lankhorst, Wierda, ISO 42010, Hosiaisluoma, Bizzdesign, MIT CISR, IASA BTABoK,
Kotusev/EA on a Page, SAP LeanIX, Microsoft CAF, and AWS Well-Architected.
