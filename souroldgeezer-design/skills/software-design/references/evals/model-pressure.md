# Software Design Model Pressure

Use before adding pattern guidance or a new stack extension. The skill should
not teach generic pattern or language mechanics; its durable lift is the local
contract: lean selection, evidence layers, smell-code output, sibling-skill
delegation, and stop conditions for speculative ceremony.

Pressure prompts to replay with/without the skill:

| ID | Prompt | Skill must improve |
|---|---|---|
| SD-MP-1 | "Should this three-branch conditional become Strategy?" | Reject pattern shopping unless current variation/churn exists. |
| SD-MP-2 | "Review this repository/unit-of-work layer." | Separate real persistence boundary from pass-through ceremony. |
| SD-MP-3 | "Review this shell script for portability and design." | Split shell design findings from security posture and delegate. |
| SD-MP-4 | "Design a repo-local Python tool." | Keep entrypoint, import-time, stream/exit-code, and security delegation explicit. |
| SD-MP-PAT-1 | "Pick the best sustainable patterns for vendor DTO isolation, pricing variation, lifecycle events, and legacy migration." | Recommend only patterns whose current force exists; cite track record as support, not authority. |

Stack pressure records for extension value:

| ID | Prompt | baseline failure | accepted extension rule | retest | merge-back condition |
|---|---|---|---|---|---|
| SD-MP-TS-1 | "Implement a TypeScript workspace package from generated API client types." | Generic answer may reuse generated DTOs as domain types and expose broad barrels. | Protect package exports, generated-type translation, path aliases, and runtime validation ownership. | Replay with `software-design-behavior-typescript-build-implementation`. | Merge back when core-only reliably catches package/export/type-runtime drift. |
| SD-MP-RS-1 | "Review a Rust workspace facade crate with feature-gated behavior and one public trait implementation." | Generic answer may praise facade/trait shape and miss feature unification semantics. | Treat `pub`/features/traits as public contract evidence, not syntax preferences. | Replay with `software-design-behavior-rust-review`. | Merge back when core-only catches non-additive features and one-implementation trait ceremony. |
| SD-MP-JAVA-1 | "Review a Java module exporting broad packages with a service locator singleton." | Generic answer may treat modules/interfaces as normal Java layering and miss state ownership. | Treat exported packages, source sets, static singletons, and one-implementation interfaces as boundary evidence. | Replay with `software-design-behavior-java-review`. | Merge back when core-only catches module/export, singleton, and interface ceremony drift. |
| SD-MP-DOTNET-1 | "Review a .NET hosted-service patch with EF pass-through repository and broad friend assembly access." | Generic answer may accept repository/unit-of-work and hosted-service policy as familiar .NET patterns. | Treat project refs, friend assemblies, DI roots, EF/domain collapse, and hosted-service ownership as design evidence. | Replay with a .NET behavior case before expanding the extension. | Merge back when core-only separates EF ceremony and hosted-service policy ownership. |

Expansion gate: record baseline failure, skill improvement, why a shorter rule
is insufficient, rerun command, and removal condition. Delete guidance that
only repeats what the base model already does well.
