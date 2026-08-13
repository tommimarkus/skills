# JavaScript/TypeScript IP Hygiene Extension

Loaded when reviewed files include `*.js`, `*.jsx`, `*.mjs`, `*.cjs`, `*.ts`,
`*.tsx`, or a Node.js/npm manifest (`package.json`, `package-lock.json`,
`tsconfig.json`), per
[SKILL.md § Scope And Load Map](../SKILL.md) and
[extension-authoring.md § Load Order](../references/procedures/extension-authoring.md).
Applies [source-code.md](../references/source-code.md)'s four classes and
notice-survival procedure; does not restate them.

## Detection Signals

`*.js`, `*.jsx`, `*.mjs`, `*.cjs`, `*.ts`, `*.tsx` source files; `package.json`
(dependency and licence metadata); a lockfile confirms the ecosystem but is not
itself reviewed for notices.

## Comment And Doc-Comment Syntax

Line comments (`//`) and block comments (`/* */`). Doc comments use JSDoc
block form (`/** ... */`) with tags such as `@param`, `@returns`, `@license`,
`@copyright`; TypeScript's TSDoc is a superset used in the same block form,
adding type-aware tags. `source-code.md`'s "Copied doc-comment prose" class
applies to the prose inside these blocks, not the tags themselves.

## Header Placement And Ordering

A licence header or `SPDX-License-Identifier` line sits at the top of the
file, before any `import`/`require` statements. Where a shebang line
(`#!/usr/bin/env node`) is present, the header follows the shebang; a
directive prologue statement such as `"use strict"` (legacy, pre-ES-module
code) follows the header rather than preceding it.

## Ecosystem Licence Metadata

`package.json`'s `license` field declares an SPDX licence expression for the
package as a whole (the deprecated `licenses` array form may still appear in
older manifests). This is package-level metadata; it does not establish the
licence of any individual file's notices or of vendored/embedded material
under `IP-LIC-4` layering, which stays file-specific.

## Vendoring Conventions

No single ecosystem-standard vendoring directory exists; `node_modules` is
managed dependency restoration, not vendoring, and is not itself reviewed for
per-file notices. When third-party source is copied directly into the
repository rather than installed as a dependency, look for a project-chosen
directory name (commonly `vendor/` or `third_party/`, following the general
convention also used in other ecosystems) and confirm it carries the source's
own licence file, distinct from the repository's.

## Generated-Code Banners

Codegen tools commonly emit a leading comment stating the file was
automatically generated and should not be edited by hand; some tooling
recognizes a `@generated` doc-comment tag specifically to mark such files.
Treat either as `IP-SRC-5` provenance evidence for the generator/input/output
split, not as a licence determination.

## Notice-Survival Mechanics

Core `IP-LIC-5` already names minification as a notice-loss transformation;
this section supplies its JavaScript mechanism. Minifiers and bundlers
(Terser, UglifyJS, esbuild, and similar) strip comments by default during a
production build, which is the concrete notice-loss path
`source-code.md`'s "minification" transformation describes. The ecosystem
convention that survives it is a licence comment beginning `/*!` or
containing an `@license` or `@preserve` tag, which these tools retain by
default even when stripping everything else; confirm the retained comment is
still the full required notice, not a truncated fragment. Some bundler
configurations instead extract retained licence comments into a separate
output file (a `*.LICENSE.txt`-style sibling of the bundle) rather than
inlining them — treat that sibling file as the notice's new location and
confirm it ships alongside the bundle in the actual distribution, per
`IP-LIC-5`. Type-definition packages sourced from a community-maintained
`.d.ts` repository (rather than authored by the library itself) carry that
repository's own licence, distinct from the library they describe; do not
assume the library's licence covers its community-sourced type definitions.

## Mark Surfaces

The `name` field in `package.json` (the published package identifier), string
literals used as HTTP `User-Agent` values, and endpoint-path string literals
in client SDKs are the surfaces most likely to carry a third-party mark in
this ecosystem; apply `IP-MARK-1`/`IP-MARK-2`/`IP-MARK-4` per
[source-code.md § Marks In Code](../references/source-code.md).

## Criteria

This pack carves out no core criterion and adds none; it applies the core
`IP-LIC-*`, `IP-SRC-*`, `IP-COPY-*`, and `IP-MARK-*` criteria via the facts
above, including `IP-LIC-5` for minifier and bundler notice loss. No
`js.IP-*` numbered criterion is defined.
