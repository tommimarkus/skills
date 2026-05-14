# Seed Views

Use when Build or Extract needs an initial package shape.

## Default Seeds

Seed diagram kinds are starter coverage, not the full ArchiMate viewpoint
mechanism.

- Application Cooperation: app/component/service collaboration.
- Technology Usage: hosting, data, identity, network.
- Service Realization: how a business/application service is delivered.
- Business Process Cooperation: process handoff.
- Motivation: supplied goals, outcomes, constraints, drivers.
- Migration: supplied current/target plateaus.
- Capability Map: requested capability grouping.

Add only actual views to `project.json`. Missing kinds are footer disclosure.

## Custom viewpoint path

When the requested concern does not fit a seed, define the stakeholder concern,
allowed element types, allowed relationship types, audience, and quality target
before editing source. Add the custom view only when it answers a concrete
architecture question.

## Minimum View Quality

Each seed or custom view needs a clear question, necessary elements, primary
relationship path, and projection/layout/validation/SVG evidence before
`render-ready`.
