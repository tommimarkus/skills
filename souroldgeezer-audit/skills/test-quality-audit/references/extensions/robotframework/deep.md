# Extension: Robot Framework — deep-mode procedures

Deep-mode-only procedures for the Robot Framework test-quality-audit extension:
SUT surface enumeration, determinism verification, and the Robot-level mutation skip mutation
tool declaration. Loaded only in Deep mode, for any rubric; Quick audits
never load it. Detection, dispatch, and smells stay in [`core.md`](core.md).

## SUT surface enumeration

Consumed by [SKILL.md § SUT surface enumeration](../../../SKILL.md) in deep mode.

Robot Framework itself does not expose the production SUT surface. When another SUT stack extension is detected (.NET, Node.js / TypeScript, Next.js, or future Python), use that extension's SUT surface enumeration for product-code gaps.

Robot tests can still satisfy SUT-stack coverage gaps when they exercise the SUT's public boundary and assert the relevant contract. Example: a RequestsLibrary test against a .NET route can satisfy that route's `.NET` `Gap-Route` entry if it asserts status plus stable body/header/auth/domain behavior. Record this as external contract coverage under the SUT extension. Robot rows that only assert `200`, `OK`, URL reachability, element presence, or successful login are `referenced-weak`; they do not suppress invalid-payload, unauthorized, forbidden, session-lifecycle, duplicate, boundary, or state-change gaps. Do not use Robot evidence to suppress source-level unit seams, private throw-site details, or mutation-target findings that Robot cannot observe.

Use Robot-specific surface enumeration only when the audit scope says the **keyword layer** is the SUT, such as a shared `.resource` library or custom test library intended for reuse.

### Keyword-layer `Gap-API` patterns

- Resource keyword declarations: in `.robot` / `.resource`, inside `*** Keywords ***`, capture non-empty top-level keyword names until the next section header.
- Python library keyword declarations: public functions / methods in files imported by Robot suites, plus `@keyword(...)` decorated functions. Capture the Robot-visible name when the decorator supplies one; otherwise capture the function / method name converted to Robot's space-insensitive keyword style.

### Cross-reference matching

For each enumerated keyword, search audited test cases for a call row whose first cell resolves to that keyword name after Robot's case-insensitive, space-insensitive matching. Suppress keywords tagged or documented as private helpers by naming convention (`_Internal`, `Internal *`, `Helper *`) unless the repo declares them public.

### Confidence annotations

- `Gap-API` for public resource keywords: **medium** - helpers are often intentionally indirect.
- `Gap-API` for public Python library keywords: **medium** unless the library is published as a reusable Robot library, then **high**.

---

## Determinism verification

Consumed by [SKILL.md § Determinism verification](../../../SKILL.md) - step 4.5 of the deep-mode workflow. Applies under unit and integration rubrics when the suite is cheap to rerun. Do not run against E2E suites.

### Cheap-rerun command

Run the selected non-E2E Robot target twice with machine-readable output:

```bash
robot --log NONE --report NONE \
  --output ./.test-determinism/run1/output.xml \
  --xunit ./.test-determinism/run1/xunit.xml \
  <robot-target>
robot --log NONE --report NONE \
  --output ./.test-determinism/run2/output.xml \
  --xunit ./.test-determinism/run2/xunit.xml \
  <robot-target>
```

Compare the two xUnit files by test case name and outcome. Any test whose status differs is a runtime-proven flake finding.

### Gating

- **Project size:** skip and recommend targeted reruns when the target has >= 500 test cases. Approximate by counting non-empty rows in `*** Test Cases ***` sections, excluding settings rows and indented keyword rows.
- **Total elapsed time from run 1:** if run 1 takes more than 60 seconds, warn before run 2 and ask before continuing in interactive audits.
- **E2E suites:** never run. Browser / mobile UI suites require target-specific flake investigation instead of a full duplicate run.
- **Parallel suites:** if `pabot` is the normal runner, run determinism in the same parallel mode only if the user explicitly wants to test parallel determinism. Otherwise run serial `robot` to isolate test-order flake from worker scheduling flake.

---

## Mutation tool

Robot Framework tests usually exercise a product through keywords and libraries; mutation testing belongs to the SUT language, not to Robot test data. When another SUT extension is loaded, use that extension's mutation tool. The Robot extension declares no Robot-level mutation run.

### 1. Tool name and link

No Robot-Framework-level mutation tool is declared. Use the SUT language extension's mutation tool instead, such as Stryker.NET or StrykerJS when those extensions are loaded.

### 2. Install instructions

Do not install a Robot-specific mutation tool for this extension. Install the mutation tool declared by the detected SUT language extension, or skip mutation testing with state B when only Robot Framework is detected.

### 3. Detection command

The audit agent runs this side-effect-free command for Robot-only targets and treats the non-zero exit as "no Robot-level mutation tool":

```bash
false
```

### 4. Run command

No Robot-level run command. If a SUT language extension is loaded, follow that extension's run command against the SUT project, not against `.robot` files.

### 5. Known SUT limitations

- Robot-only audit target: there is no product-code mutation surface. Skip mutation with state B and continue static audit.
- E2E Robot target: mutation testing is not meaningful against a browser/mobile black-box suite. Skip per the core E2E rule.
- Mixed Robot + SUT-language target: run mutation only through the SUT extension and reconcile results with Robot static findings when a Robot test suite is the only executable coverage for that SUT surface.

### 6. Output parser notes

No Robot-level output exists. If a SUT mutation tool ran, parse its report using the SUT extension. Robot `output.xml` / `xunit.xml` files are useful for runtime distribution and determinism, not mutation scoring.
