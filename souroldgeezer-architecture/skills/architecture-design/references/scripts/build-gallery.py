#!/usr/bin/env python3
"""Build a self-contained gallery.html from a dediren architecture package.

Reads the package's own sources — project.json (titles/questions/diagramKind/
model), the rendered generated/svg/*.svg, and generated/render-metadata/*.json
(node/edge counts) — and writes one standalone HTML file inside the package with
every diagram inlined as an inert <template>. No external assets, so it works on
GitHub Pages, a static host, or opened straight from disk.

Usage:
    build-gallery.py <package-dir>            write <package-dir>/gallery.html
    build-gallery.py --check <package-dir>    verify the committed gallery is
                                              current; no write (drift check)
    build-gallery.py --help

Exit codes: 0 ok / fresh; 1 stale or missing gallery (--check); 2 usage or
input error; 3 render sources incomplete (re-render before building/checking).

Stdlib-only; Python >= 3.9.
"""
import json
import os
import sys
from urllib.parse import quote

DENSE_EDGES = 50  # a view is flagged "dense" at this many relationships


class SourceMissing(Exception):
    """A required rendered source (svg or render-metadata) is absent."""


def classify(profile, diagram_kind):
    """(section_key, section_title, section_note, code_letter) for a view.

    The code letter encodes the notation you are looking at (the one structural
    device carried over from the Uljas design): ArchiMate is A; UML splits into
    families by diagram kind. Falls back to a generic UML bucket for kinds not
    matched, and to ArchiMate for any non-uml profile.
    """
    k = (diagram_kind or "").lower()
    if profile == "uml":
        if "sequence" in k or "communication" in k:
            return ("uml-seq", "Sequences", "UML 2.5", "S")
        if "class" in k or "object" in k or "data" in k:
            return ("uml-data", "Structure & data", "UML 2.5", "T")
        if "component" in k or "deployment" in k or "package" in k:
            return ("uml-depl", "Components & deployment", "UML 2.5", "C")
        if "activity" in k or "state" in k or "use case" in k \
                or "use-case" in k or "usecase" in k:
            return ("uml-behavior", "Behaviour", "UML 2.5", "B")
        return ("uml", "UML views", "UML 2.5", "U")
    return ("arch", "ArchiMate views", "ArchiMate 3.2", "A")


def status_of(edges):
    """'warning' when a view carries enough relationships to be hard to route."""
    return "warning" if edges >= DENSE_EDGES else "ok"
