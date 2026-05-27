# Software Design Model Pressure

Use before adding detail. Core IDs: `SD-MP-1`, `SD-MP-2`, `SD-MP-3`, `SD-MP-4`, `SD-MP-PAT-1`, `SD-MP-PRINCIPLE-1`, `SD-MP-SMELL-1`. Core lift: force fit, evidence layers, smell-code output, sibling delegation, false-positive guards, and anti-ceremony stops.

Stack records use baseline failure, accepted extension rule, retest, and merge-back condition: `SD-MP-TS-1` DTO/export drift -> exports, translation, aliases, validation ownership -> TS case -> package/export/type-runtime drift; `SD-MP-RS-1` feature/trait drift -> `pub`, features, traits as contracts -> Rust case -> feature/trait ceremony; `SD-MP-JAVA-1` module/interface drift -> exports, source sets, singletons, one-use interfaces -> Java case -> module/export/singleton/interface drift; `SD-MP-DOTNET-1` familiar EF/hosted-service patterns -> refs, friends, DI roots, EF/domain collapse, hosted-service ownership -> .NET case -> EF ceremony and hosted-service policy.

Smell-catalog expansion gate: record baseline failure, accepted smell-catalog rule, behavior eval ID, and merge-back condition. Expansion gate: record why shorter rule fails, rerun command, and removal condition.
