# DevSecOps ASVS 5.0.0 Crosswalk

- Edition: OWASP ASVS 5.0.0, release tag `v5.0.0_release` (<https://github.com/OWASP/ASVS/releases/tag/v5.0.0_release>).
- Source asset: `OWASP_Application_Security_Verification_Standard_5.0.0_en.flat.json`, SHA-256 `8201b20eec2908c3380ac600c91c8ba746346fbb808859366abb232027532311`.
- Licence: ASVS is published by the OWASP Foundation under CC BY-SA 4.0 (<https://creativecommons.org/licenses/by-sa/4.0/legalcode>). This file records requirement IDs, levels, and chapter names only, together with repo-authored classifications; it never reproduces requirement or section text. Read the upstream standard for the wording.
- Levels are cumulative: L2 includes every L1 requirement, and L3 includes every L1 and L2 requirement.
- Loading: on demand only, per the devsecops-audit Load Map. This file is the only code-to-ASVS mapping: rule packs and catalog rows carry no ASVS requirement IDs, apart from the fixed citations in `dns.HC-5` and rubric §5.1.16.

Classes (closed set):

- `static` — the listed finding and positive codes give static evidence for the whole requirement as worded.
- `partial` — the listed codes cover only part of it: one stack, one sub-clause, or one variant.
- `documentation` — met by project documentation or recorded decisions; no dedicated code. Deep checks presence when ASVS is declared.
- `runtime` — needs runtime, DAST, manual, or out-of-repository configuration evidence.
- `uncovered` — statically decidable in principle, but no current code covers it.

Only `static` and `partial` rows list codes; each code is a row in [devsecops-smell-catalog.md](devsecops-smell-catalog.md).

## Summary

| Chapter | L1 | L2 | L3 | static | partial | documentation | runtime | uncovered | Total |
|---|---|---|---|---|---|---|---|---|---|
| V1 | 8 | 19 | 3 | 0 | 8 | 0 | 1 | 21 | 30 |
| V2 | 4 | 7 | 2 | 0 | 2 | 3 | 8 | 0 | 13 |
| V3 | 8 | 11 | 12 | 0 | 10 | 1 | 4 | 16 | 31 |
| V4 | 2 | 8 | 6 | 0 | 0 | 0 | 5 | 11 | 16 |
| V5 | 4 | 5 | 4 | 0 | 5 | 1 | 2 | 5 | 13 |
| V6 | 13 | 22 | 12 | 0 | 3 | 3 | 22 | 19 | 47 |
| V7 | 6 | 12 | 1 | 0 | 2 | 3 | 10 | 4 | 19 |
| V8 | 4 | 3 | 6 | 0 | 5 | 4 | 3 | 1 | 13 |
| V9 | 4 | 3 | 0 | 0 | 5 | 0 | 0 | 2 | 7 |
| V10 | 5 | 24 | 7 | 0 | 2 | 0 | 21 | 13 | 36 |
| V11 | 3 | 11 | 10 | 0 | 11 | 3 | 4 | 6 | 24 |
| V12 | 3 | 6 | 3 | 0 | 5 | 0 | 6 | 1 | 12 |
| V13 | 1 | 12 | 8 | 0 | 9 | 4 | 4 | 4 | 21 |
| V14 | 2 | 7 | 4 | 0 | 0 | 2 | 8 | 3 | 13 |
| V15 | 3 | 10 | 8 | 1 | 9 | 3 | 2 | 6 | 21 |
| V16 | 0 | 16 | 1 | 0 | 5 | 1 | 7 | 4 | 17 |
| V17 | 0 | 7 | 5 | 0 | 0 | 0 | 12 | 0 | 12 |
| Total | 70 | 183 | 92 | 1 | 81 | 28 | 119 | 116 | 345 |

## Using this crosswalk

Take the declared ASVS 5.0.0 level and include every requirement at or below it. For each `static` or `partial` row, report:

- **evidenced** — a listed positive code fired, or the audit cites a concrete artifact that meets the requirement;
- **contradicted** — a listed finding code fired;
- **not-evidenced** — neither happened.

Report the remaining rows as honest limits: `documentation` rows with the document found present or absent, `runtime` rows as needing evidence outside static review, and `uncovered` rows as having no rule today. A `partial` row that is evidenced remains partial: name the uncovered part.

Absence of findings is never evidence for a requirement. Never claim ASVS conformance or certification from this crosswalk; it supports the Deep framework coupling report in [devsecops.md](devsecops.md) §9 item 9.

## V1 Encoding and Sanitization

| ID | Level | Class | Codes |
|---|---|---|---|
| V1.1.1 | L2 | uncovered | — |
| V1.1.2 | L2 | uncovered | — |
| V1.2.1 | L1 | partial | `jsts.HC-3`, `jsts.POS-3` |
| V1.2.2 | L1 | uncovered | — |
| V1.2.3 | L1 | uncovered | — |
| V1.2.4 | L1 | partial | `dns.HC-11`, `pys.HC-8`, `jsts.HC-8`, `pys.POS-5`, `jsts.POS-8` |
| V1.2.5 | L1 | partial | `pys.HC-3`, `jsts.HC-2`, `pys.POS-2`, `jsts.POS-2` |
| V1.2.6 | L2 | uncovered | — |
| V1.2.7 | L2 | uncovered | — |
| V1.2.8 | L2 | uncovered | — |
| V1.2.9 | L2 | uncovered | — |
| V1.2.10 | L3 | uncovered | — |
| V1.3.1 | L1 | partial | `jsts.HC-3`, `jsts.POS-3` |
| V1.3.2 | L1 | partial | `pys.HC-2`, `jsts.HC-1`, `jsts.POS-1` |
| V1.3.3 | L2 | uncovered | — |
| V1.3.4 | L2 | uncovered | — |
| V1.3.5 | L2 | uncovered | — |
| V1.3.6 | L2 | partial | `pys.HC-9`, `jsts.HC-9`, `pys.POS-5`, `jsts.POS-9` |
| V1.3.7 | L2 | partial | `pys.HC-2` |
| V1.3.8 | L2 | uncovered | — |
| V1.3.9 | L2 | uncovered | — |
| V1.3.10 | L2 | uncovered | — |
| V1.3.11 | L2 | uncovered | — |
| V1.3.12 | L3 | uncovered | — |
| V1.4.1 | L2 | uncovered | — |
| V1.4.2 | L2 | uncovered | — |
| V1.4.3 | L2 | uncovered | — |
| V1.5.1 | L1 | uncovered | — |
| V1.5.2 | L2 | partial | `dns.HC-12`, `pys.HC-1`, `pys.POS-1` |
| V1.5.3 | L3 | runtime | — |

## V2 Validation and Business Logic

| ID | Level | Class | Codes |
|---|---|---|---|
| V2.1.1 | L1 | documentation | — |
| V2.1.2 | L2 | documentation | — |
| V2.1.3 | L2 | documentation | — |
| V2.2.1 | L1 | partial | `dns.POS-5` |
| V2.2.2 | L1 | partial | `dns.POS-5` |
| V2.2.3 | L2 | runtime | — |
| V2.3.1 | L1 | runtime | — |
| V2.3.2 | L2 | runtime | — |
| V2.3.3 | L2 | runtime | — |
| V2.3.4 | L2 | runtime | — |
| V2.3.5 | L3 | runtime | — |
| V2.4.1 | L2 | runtime | — |
| V2.4.2 | L3 | runtime | — |

## V3 Web Frontend Security

| ID | Level | Class | Codes |
|---|---|---|---|
| V3.1.1 | L3 | documentation | — |
| V3.2.1 | L1 | uncovered | — |
| V3.2.2 | L1 | partial | `jsts.HC-3`, `jsts.POS-3` |
| V3.2.3 | L3 | uncovered | — |
| V3.3.1 | L1 | partial | `dns.HC-17`, `pys.HC-11`, `jsts.HC-13`, `dns.POS-7`, `pys.POS-7`, `jsts.POS-13` |
| V3.3.2 | L2 | partial | `dns.HC-17`, `pys.HC-11`, `jsts.HC-13`, `dns.POS-7`, `pys.POS-7`, `jsts.POS-13` |
| V3.3.3 | L2 | uncovered | — |
| V3.3.4 | L2 | partial | `dns.HC-17`, `pys.HC-11`, `jsts.HC-13`, `dns.POS-7`, `pys.POS-7`, `jsts.POS-13` |
| V3.3.5 | L3 | uncovered | — |
| V3.4.1 | L1 | partial | `DSO-HC-16`, `dns.POS-3` |
| V3.4.2 | L1 | partial | `DSO-HC-20`, `dns.HC-4` |
| V3.4.3 | L2 | partial | `dns.HC-5`, `dns.POS-3` |
| V3.4.4 | L2 | uncovered | — |
| V3.4.5 | L2 | partial | `dns.HC-5`, `dns.POS-3` |
| V3.4.6 | L2 | partial | `dns.HC-5`, `dns.POS-3` |
| V3.4.7 | L3 | uncovered | — |
| V3.4.8 | L3 | uncovered | — |
| V3.5.1 | L1 | partial | `dns.HC-9` |
| V3.5.2 | L1 | uncovered | — |
| V3.5.3 | L1 | uncovered | — |
| V3.5.4 | L2 | runtime | — |
| V3.5.5 | L2 | uncovered | — |
| V3.5.6 | L3 | uncovered | — |
| V3.5.7 | L3 | uncovered | — |
| V3.5.8 | L3 | uncovered | — |
| V3.6.1 | L3 | uncovered | — |
| V3.7.1 | L2 | uncovered | — |
| V3.7.2 | L2 | uncovered | — |
| V3.7.3 | L3 | runtime | — |
| V3.7.4 | L3 | runtime | — |
| V3.7.5 | L3 | runtime | — |

## V4 API and Web Service

| ID | Level | Class | Codes |
|---|---|---|---|
| V4.1.1 | L1 | uncovered | — |
| V4.1.2 | L2 | uncovered | — |
| V4.1.3 | L2 | runtime | — |
| V4.1.4 | L3 | uncovered | — |
| V4.1.5 | L3 | uncovered | — |
| V4.2.1 | L2 | runtime | — |
| V4.2.2 | L3 | runtime | — |
| V4.2.3 | L3 | runtime | — |
| V4.2.4 | L3 | runtime | — |
| V4.2.5 | L3 | uncovered | — |
| V4.3.1 | L2 | uncovered | — |
| V4.3.2 | L2 | uncovered | — |
| V4.4.1 | L1 | uncovered | — |
| V4.4.2 | L2 | uncovered | — |
| V4.4.3 | L2 | uncovered | — |
| V4.4.4 | L2 | uncovered | — |

## V5 File Handling

| ID | Level | Class | Codes |
|---|---|---|---|
| V5.1.1 | L2 | documentation | — |
| V5.2.1 | L1 | uncovered | — |
| V5.2.2 | L1 | uncovered | — |
| V5.2.3 | L2 | partial | `pys.POS-3` |
| V5.2.4 | L3 | uncovered | — |
| V5.2.5 | L3 | partial | `pys.HC-4`, `pys.POS-3` |
| V5.2.6 | L3 | uncovered | — |
| V5.3.1 | L1 | runtime | — |
| V5.3.2 | L1 | partial | `pys.HC-4`, `jsts.HC-5`, `pys.POS-3`, `jsts.POS-5` |
| V5.3.3 | L3 | partial | `pys.HC-4`, `jsts.HC-5`, `pys.POS-3`, `jsts.POS-5` |
| V5.4.1 | L2 | partial | `pys.HC-4`, `jsts.HC-5` |
| V5.4.2 | L2 | uncovered | — |
| V5.4.3 | L2 | runtime | — |

## V6 Authentication

| ID | Level | Class | Codes |
|---|---|---|---|
| V6.1.1 | L1 | documentation | — |
| V6.1.2 | L2 | documentation | — |
| V6.1.3 | L2 | documentation | — |
| V6.2.1 | L1 | uncovered | — |
| V6.2.2 | L1 | runtime | — |
| V6.2.3 | L1 | runtime | — |
| V6.2.4 | L1 | uncovered | — |
| V6.2.5 | L1 | uncovered | — |
| V6.2.6 | L1 | uncovered | — |
| V6.2.7 | L1 | uncovered | — |
| V6.2.8 | L1 | uncovered | — |
| V6.2.9 | L2 | uncovered | — |
| V6.2.10 | L2 | uncovered | — |
| V6.2.11 | L2 | uncovered | — |
| V6.2.12 | L2 | uncovered | — |
| V6.3.1 | L1 | runtime | — |
| V6.3.2 | L1 | uncovered | — |
| V6.3.3 | L2 | runtime | — |
| V6.3.4 | L2 | runtime | — |
| V6.3.5 | L3 | runtime | — |
| V6.3.6 | L3 | runtime | — |
| V6.3.7 | L3 | runtime | — |
| V6.3.8 | L3 | runtime | — |
| V6.4.1 | L1 | partial | `dns.HC-10`, `pys.HC-6`, `jsts.HC-6`, `pys.POS-4`, `jsts.POS-6` |
| V6.4.2 | L1 | uncovered | — |
| V6.4.3 | L2 | runtime | — |
| V6.4.4 | L2 | runtime | — |
| V6.4.5 | L3 | runtime | — |
| V6.4.6 | L3 | runtime | — |
| V6.5.1 | L2 | runtime | — |
| V6.5.2 | L2 | uncovered | — |
| V6.5.3 | L2 | partial | `dns.HC-10`, `pys.HC-6`, `jsts.HC-6`, `pys.POS-4`, `jsts.POS-6` |
| V6.5.4 | L2 | uncovered | — |
| V6.5.5 | L2 | uncovered | — |
| V6.5.6 | L3 | runtime | — |
| V6.5.7 | L3 | runtime | — |
| V6.5.8 | L3 | runtime | — |
| V6.6.1 | L2 | runtime | — |
| V6.6.2 | L2 | runtime | — |
| V6.6.3 | L2 | runtime | — |
| V6.6.4 | L3 | runtime | — |
| V6.7.1 | L3 | runtime | — |
| V6.7.2 | L3 | uncovered | — |
| V6.8.1 | L2 | uncovered | — |
| V6.8.2 | L2 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V6.8.3 | L2 | uncovered | — |
| V6.8.4 | L2 | uncovered | — |

## V7 Session Management

| ID | Level | Class | Codes |
|---|---|---|---|
| V7.1.1 | L2 | documentation | — |
| V7.1.2 | L2 | documentation | — |
| V7.1.3 | L2 | documentation | — |
| V7.2.1 | L1 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12` |
| V7.2.2 | L1 | uncovered | — |
| V7.2.3 | L1 | partial | `dns.HC-10`, `pys.HC-6`, `jsts.HC-6`, `pys.POS-4`, `jsts.POS-6` |
| V7.2.4 | L1 | uncovered | — |
| V7.3.1 | L2 | uncovered | — |
| V7.3.2 | L2 | uncovered | — |
| V7.4.1 | L1 | runtime | — |
| V7.4.2 | L1 | runtime | — |
| V7.4.3 | L2 | runtime | — |
| V7.4.4 | L2 | runtime | — |
| V7.4.5 | L2 | runtime | — |
| V7.5.1 | L2 | runtime | — |
| V7.5.2 | L2 | runtime | — |
| V7.5.3 | L3 | runtime | — |
| V7.6.1 | L2 | runtime | — |
| V7.6.2 | L2 | runtime | — |

## V8 Authorization

| ID | Level | Class | Codes |
|---|---|---|---|
| V8.1.1 | L1 | documentation | — |
| V8.1.2 | L2 | documentation | — |
| V8.1.3 | L3 | documentation | — |
| V8.1.4 | L3 | documentation | — |
| V8.2.1 | L1 | partial | `dns.HC-2`, `dns.HC-3`, `pys.HC-14`, `jsts.HC-16`, `dns.POS-4`, `pys.POS-9`, `jsts.POS-15` |
| V8.2.2 | L1 | partial | `DSO-SUB-4` |
| V8.2.3 | L2 | partial | `DSO-SUB-5`, `dns.LC-2`, `dns.POS-5` |
| V8.2.4 | L3 | runtime | — |
| V8.3.1 | L1 | partial | `dns.HC-3`, `pys.HC-14`, `jsts.HC-16`, `pys.POS-9`, `jsts.POS-15` |
| V8.3.2 | L3 | runtime | — |
| V8.3.3 | L3 | uncovered | — |
| V8.4.1 | L2 | partial | `DSO-SUB-4` |
| V8.4.2 | L3 | runtime | — |

## V9 Self-contained Tokens

| ID | Level | Class | Codes |
|---|---|---|---|
| V9.1.1 | L1 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V9.1.2 | L1 | partial | `pys.HC-10`, `jsts.HC-12`, `pys.POS-6`, `jsts.POS-12` |
| V9.1.3 | L1 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6` |
| V9.2.1 | L1 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V9.2.2 | L2 | uncovered | — |
| V9.2.3 | L2 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V9.2.4 | L2 | uncovered | — |

## V10 OAuth and OIDC

| ID | Level | Class | Codes |
|---|---|---|---|
| V10.1.1 | L2 | uncovered | — |
| V10.1.2 | L2 | uncovered | — |
| V10.2.1 | L2 | uncovered | — |
| V10.2.2 | L2 | uncovered | — |
| V10.2.3 | L3 | uncovered | — |
| V10.3.1 | L2 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V10.3.2 | L2 | uncovered | — |
| V10.3.3 | L2 | uncovered | — |
| V10.3.4 | L2 | uncovered | — |
| V10.3.5 | L3 | uncovered | — |
| V10.4.1 | L1 | runtime | — |
| V10.4.2 | L1 | runtime | — |
| V10.4.3 | L1 | runtime | — |
| V10.4.4 | L1 | runtime | — |
| V10.4.5 | L1 | runtime | — |
| V10.4.6 | L2 | runtime | — |
| V10.4.7 | L2 | runtime | — |
| V10.4.8 | L2 | runtime | — |
| V10.4.9 | L2 | runtime | — |
| V10.4.10 | L2 | runtime | — |
| V10.4.11 | L2 | runtime | — |
| V10.4.12 | L3 | runtime | — |
| V10.4.13 | L3 | runtime | — |
| V10.4.14 | L3 | runtime | — |
| V10.4.15 | L3 | runtime | — |
| V10.4.16 | L3 | runtime | — |
| V10.5.1 | L2 | uncovered | — |
| V10.5.2 | L2 | uncovered | — |
| V10.5.3 | L2 | uncovered | — |
| V10.5.4 | L2 | partial | `dns.HC-16`, `pys.HC-10`, `jsts.HC-12`, `dns.POS-6`, `pys.POS-6`, `jsts.POS-12` |
| V10.5.5 | L2 | uncovered | — |
| V10.6.1 | L2 | runtime | — |
| V10.6.2 | L2 | runtime | — |
| V10.7.1 | L2 | runtime | — |
| V10.7.2 | L2 | runtime | — |
| V10.7.3 | L2 | runtime | — |

## V11 Cryptography

| ID | Level | Class | Codes |
|---|---|---|---|
| V11.1.1 | L2 | documentation | — |
| V11.1.2 | L2 | documentation | — |
| V11.1.3 | L3 | runtime | — |
| V11.1.4 | L3 | documentation | — |
| V11.2.1 | L2 | uncovered | — |
| V11.2.2 | L2 | uncovered | — |
| V11.2.3 | L2 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14`, `dns.POS-8`, `pys.POS-8`, `jsts.POS-14` |
| V11.2.4 | L3 | uncovered | — |
| V11.2.5 | L3 | uncovered | — |
| V11.3.1 | L1 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14` |
| V11.3.2 | L1 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14`, `dns.POS-8`, `pys.POS-8`, `jsts.POS-14` |
| V11.3.3 | L2 | partial | `dns.POS-8` |
| V11.3.4 | L3 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14` |
| V11.3.5 | L3 | uncovered | — |
| V11.4.1 | L1 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14`, `dns.POS-8`, `pys.POS-8`, `jsts.POS-14` |
| V11.4.2 | L2 | partial | `dns.HC-19`, `pys.HC-13`, `jsts.HC-15`, `dns.POS-8`, `pys.POS-8`, `jsts.POS-14` |
| V11.4.3 | L2 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14` |
| V11.4.4 | L2 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14` |
| V11.5.1 | L2 | partial | `dns.HC-10`, `pys.HC-6`, `jsts.HC-6`, `pys.POS-4`, `jsts.POS-6` |
| V11.5.2 | L3 | runtime | — |
| V11.6.1 | L2 | partial | `dns.HC-18`, `pys.HC-12`, `jsts.HC-14` |
| V11.6.2 | L3 | uncovered | — |
| V11.7.1 | L3 | runtime | — |
| V11.7.2 | L3 | runtime | — |

## V12 Secure Communication

| ID | Level | Class | Codes |
|---|---|---|---|
| V12.1.1 | L1 | partial | `bicep.HC-2` |
| V12.1.2 | L2 | runtime | — |
| V12.1.3 | L2 | uncovered | — |
| V12.1.4 | L3 | runtime | — |
| V12.1.5 | L3 | runtime | — |
| V12.2.1 | L1 | partial | `DSO-HC-16` |
| V12.2.2 | L1 | runtime | — |
| V12.3.1 | L2 | partial | `bicep.HC-2`, `bicep.HC-4` |
| V12.3.2 | L2 | partial | `dns.HC-20`, `pys.HC-7`, `jsts.HC-7`, `dns.POS-9`, `pys.POS-5`, `jsts.POS-7` |
| V12.3.3 | L2 | runtime | — |
| V12.3.4 | L2 | partial | `dns.HC-20`, `pys.HC-7`, `jsts.HC-7`, `dns.POS-9`, `jsts.POS-7` |
| V12.3.5 | L3 | runtime | — |

## V13 Configuration

| ID | Level | Class | Codes |
|---|---|---|---|
| V13.1.1 | L2 | documentation | — |
| V13.1.2 | L3 | documentation | — |
| V13.1.3 | L3 | documentation | — |
| V13.1.4 | L3 | documentation | — |
| V13.2.1 | L2 | partial | `dns.HC-7`, `dns.HC-14`, `bicep.HC-1`, `bicep.HC-3`, `dns.POS-1`, `bicep.POS-1` |
| V13.2.2 | L2 | partial | `DSO-LC-7`, `docker.HC-1`, `docker.POS-2` |
| V13.2.3 | L2 | uncovered | — |
| V13.2.4 | L2 | partial | `pys.HC-9`, `jsts.HC-9`, `pys.POS-5`, `jsts.POS-9` |
| V13.2.5 | L2 | runtime | — |
| V13.2.6 | L3 | runtime | — |
| V13.3.1 | L2 | partial | `DSO-HC-1`, `dns.HC-1`, `bicep.HC-5`, `docker.HC-3`, `dns.POS-2`, `bicep.POS-2` |
| V13.3.2 | L2 | partial | `bicep.HC-12`, `bicep.POS-3` |
| V13.3.3 | L3 | partial | `bicep.B2-5` |
| V13.3.4 | L3 | partial | `DSO-HC-7`, `DSO-HC-19`, `DSO-POS-2` |
| V13.4.1 | L1 | partial | `docker.HC-10` |
| V13.4.2 | L2 | partial | `jsts.HC-11`, `jsts.POS-11` |
| V13.4.3 | L2 | uncovered | — |
| V13.4.4 | L2 | runtime | — |
| V13.4.5 | L2 | uncovered | — |
| V13.4.6 | L3 | uncovered | — |
| V13.4.7 | L3 | runtime | — |

## V14 Data Protection

| ID | Level | Class | Codes |
|---|---|---|---|
| V14.1.1 | L2 | documentation | — |
| V14.1.2 | L2 | documentation | — |
| V14.2.1 | L1 | uncovered | — |
| V14.2.2 | L2 | runtime | — |
| V14.2.3 | L2 | runtime | — |
| V14.2.4 | L2 | runtime | — |
| V14.2.5 | L3 | runtime | — |
| V14.2.6 | L3 | runtime | — |
| V14.2.7 | L3 | runtime | — |
| V14.2.8 | L3 | runtime | — |
| V14.3.1 | L1 | runtime | — |
| V14.3.2 | L2 | uncovered | — |
| V14.3.3 | L2 | uncovered | — |

## V15 Secure Coding and Architecture

| ID | Level | Class | Codes |
|---|---|---|---|
| V15.1.1 | L1 | partial | `DSO-HC-15`, `DSO-POS-7` |
| V15.1.2 | L2 | partial | `DSO-LC-6`, `DSO-SUB-1`, `DSO-POS-6` |
| V15.1.3 | L2 | documentation | — |
| V15.1.4 | L3 | documentation | — |
| V15.1.5 | L3 | documentation | — |
| V15.2.1 | L1 | partial | `DSO-LC-9`, `DSO-SUB-12`, `DSO-POS-7` |
| V15.2.2 | L2 | partial | `docker.HC-9` |
| V15.2.3 | L2 | partial | `jsts.HC-11`, `docker.POS-3` |
| V15.2.4 | L3 | partial | `DSO-HC-2`, `DSO-SUB-1`, `DSO-POS-3` |
| V15.2.5 | L3 | runtime | — |
| V15.3.1 | L1 | uncovered | — |
| V15.3.2 | L2 | partial | `pys.HC-9`, `jsts.HC-9`, `pys.POS-5`, `jsts.POS-9` |
| V15.3.3 | L2 | partial | `DSO-SUB-5`, `dns.LC-2`, `dns.POS-5` |
| V15.3.4 | L2 | runtime | — |
| V15.3.5 | L2 | uncovered | — |
| V15.3.6 | L2 | static | `jsts.HC-4`, `jsts.POS-4` |
| V15.3.7 | L2 | uncovered | — |
| V15.4.1 | L3 | uncovered | — |
| V15.4.2 | L3 | partial | `pys.HC-5` |
| V15.4.3 | L3 | uncovered | — |
| V15.4.4 | L3 | uncovered | — |

## V16 Security Logging and Error Handling

| ID | Level | Class | Codes |
|---|---|---|---|
| V16.1.1 | L2 | documentation | — |
| V16.2.1 | L2 | partial | `dns.HC-8`, `DSO-SUB-6` |
| V16.2.2 | L2 | runtime | — |
| V16.2.3 | L2 | runtime | — |
| V16.2.4 | L2 | runtime | — |
| V16.2.5 | L2 | partial | `dns.LC-4` |
| V16.3.1 | L2 | uncovered | — |
| V16.3.2 | L2 | partial | `dns.HC-8` |
| V16.3.3 | L2 | runtime | — |
| V16.3.4 | L2 | uncovered | — |
| V16.4.1 | L2 | partial | `dns.HC-15` |
| V16.4.2 | L2 | runtime | — |
| V16.4.3 | L2 | partial | `bicep.HC-8`, `bicep.POS-4` |
| V16.5.1 | L2 | uncovered | — |
| V16.5.2 | L2 | runtime | — |
| V16.5.3 | L2 | runtime | — |
| V16.5.4 | L3 | uncovered | — |

## V17 WebRTC

| ID | Level | Class | Codes |
|---|---|---|---|
| V17.1.1 | L2 | runtime | — |
| V17.1.2 | L3 | runtime | — |
| V17.2.1 | L2 | runtime | — |
| V17.2.2 | L2 | runtime | — |
| V17.2.3 | L2 | runtime | — |
| V17.2.4 | L2 | runtime | — |
| V17.2.5 | L3 | runtime | — |
| V17.2.6 | L3 | runtime | — |
| V17.2.7 | L3 | runtime | — |
| V17.2.8 | L3 | runtime | — |
| V17.3.1 | L2 | runtime | — |
| V17.3.2 | L2 | runtime | — |
