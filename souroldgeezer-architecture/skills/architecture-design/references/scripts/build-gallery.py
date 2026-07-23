#!/usr/bin/env python3
"""Build a self-contained gallery.html from a dediren architecture package.

Reads the package's own sources — project.json (titles/questions/diagramKind/
model), the rendered generated/svg/*.svg, and generated/render-metadata/*.json
(node/edge counts) — and writes one standalone HTML file inside the package with
every diagram inlined as an inert <template>. No external assets, so it works on
GitHub Pages, a static host, or opened straight from disk.

Theming: the diagram "sheet" (the card each SVG mounts on) is derived per view
from that SVG's own background, so a dark render policy gets a dark, harmonized
card instead of a white rectangle; white/transparent renders keep the default
light sheet. An optional gallery-theme.json beside project.json overrides the
gallery's design tokens outright (see references/gallery.md).

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
import re
import sys
from urllib.parse import quote

DENSE_EDGES = 50  # a view is flagged "dense" at this many relationships

# Built-in "paper & ink" gallery palette, held as data so an author theme can
# override any token cleanly (see _resolve_theme). Colour tokens only; --sans /
# --mono are theme-independent and stay inline in the template's :root.
_LIGHT = {
    "paper": "#f1f0ea", "panel": "#ffffff", "rail": "#f7f6f1", "ink": "#1b1a16",
    "muted": "#6b675e", "faint": "#9b978b", "line": "#ddd9cf", "line-2": "#c9c4b6",
    "accent": "#4b45c4", "accent-ink": "#3a34a6", "wash": "#ecebfb",
    "sheet": "#ffffff", "sheet-line": "#e7e3d8", "ok": "#2f6b45",
    "ok-wash": "#e6f1ea", "warn": "#8a5a12", "warn-wash": "#f6ead0",
    "shadow": "0 1px 0 rgba(27,26,22,.03),0 18px 40px -26px rgba(27,26,22,.42)",
}
_DARK = {
    "paper": "#131419", "panel": "#1b1d25", "rail": "#171922", "ink": "#e9e7df",
    "muted": "#9c988e", "faint": "#6f6c63", "line": "#282b34", "line-2": "#3a3e49",
    "accent": "#9b96f6", "accent-ink": "#b9b5fb", "wash": "#22233a",
    "sheet": "#ffffff", "sheet-line": "#d8d4cb", "ok": "#7ad3a0",
    "ok-wash": "#123123", "warn": "#e7c17c", "warn-wash": "#332913",
    "shadow": "0 1px 0 rgba(0,0,0,.4),0 20px 46px -26px rgba(0,0,0,.7)",
}
# Every token an author theme may override: the keys above, i.e. the CSS
# custom-property names without the leading "--". _LIGHT and _DARK share them.
_THEME_TOKENS = frozenset(_LIGHT)

# Ordered UML diagram-kind keyword families for classify(): first matching row wins.
_UML_FAMILIES = (
    (("sequence", "communication"), ("uml-seq", "Sequences", "UML 2.5", "S")),
    (("class", "object", "data"), ("uml-data", "Structure & data", "UML 2.5", "T")),
    (("component", "deployment", "package"),
     ("uml-depl", "Components & deployment", "UML 2.5", "C")),
    (("activity", "state", "use case", "use-case", "usecase"),
     ("uml-behavior", "Behaviour", "UML 2.5", "B")),
)


class SourceMissing(Exception):
    """A required rendered source (svg or render-metadata) is absent."""


def classify(profile, diagram_kind):
    """(section_key, section_title, section_note, code_letter) for a view.

    The code letter encodes the notation you are looking at (the one structural
    device carried over from the adopted design): ArchiMate is A; UML splits into
    families by diagram kind. Falls back to a generic UML bucket for kinds not
    matched, and to ArchiMate for any non-uml profile.
    """
    k = (diagram_kind or "").lower()
    if profile == "uml":
        for keywords, family in _UML_FAMILIES:
            if any(word in k for word in keywords):
                return family
        return ("uml", "UML views", "UML 2.5", "U")
    return ("arch", "ArchiMate views", "ArchiMate 3.2", "A")


def status_of(edges):
    """'warning' when a view carries enough relationships to be hard to route."""
    return "warning" if edges >= DENSE_EDGES else "ok"


def profile_resolver(proj, pkg_dir):
    """Return view -> notation-profile resolver for a v1 or v2 project."""
    if proj.get("models") is not None:  # v2: profile per model registry entry
        models = {m["id"]: m for m in proj.get("models", [])}

        def prof(view):
            return (models.get(view.get("model")) or {}).get("profile", "archimate")
        return prof

    # v1: one model for the whole package; profile lives in the model file.
    shared = "archimate"
    try:
        with open(os.path.join(pkg_dir, proj.get("model", "model.json")),
                  encoding="utf-8") as fh:
            model = json.load(fh)
        if isinstance(model, dict):
            shared = model.get("plugins", {}).get("generic-graph", {}).get(
                "semantic_profile", "archimate")
    except (OSError, ValueError):
        shared = "archimate"

    def prof(view):
        return shared
    return prof


def _count(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    return len(d.get("nodes", {})), len(d.get("edges", {}))


def _favicon():
    return "data:image/svg+xml," + quote(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<text y='.9em' font-size='88'>\U0001F4D0</text></svg>")


def _load_project(pkg_dir):
    """Parsed project.json for the package."""
    with open(os.path.join(pkg_dir, "project.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------- per-view sheet ----
# The diagram "sheet" is derived from each SVG's own background so a dark
# render policy gets a dark, harmonized card instead of a white rectangle.
# This mirrors find_bg_fill in svg-accessible-name.py (same rect, same rule),
# ported here because build-gallery.py reads the *final* SVG in Python.

def _original_viewbox(svg):
    """The pre-band viewBox as [minx, miny, w, h], or None if unparseable.

    Prefers data-arch-a11y-viewbox (recorded before the a11y title band grew
    the root viewBox); falls back to the root viewBox when the SVG never went
    through svg-accessible-name.py.
    """
    m = re.search(r'\bdata-arch-a11y-viewbox="([^"]*)"', svg)
    if m:
        raw = m.group(1)
    else:
        root = re.search(r'<svg\b[^>]*?\bviewBox="([^"]*)"', svg)
        if not root:
            return None
        raw = root.group(1)
    parts = re.split(r"[,\s]+", raw.strip())
    if len(parts) != 4:
        return None
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def _attr_num(seg, name):
    """Numeric value of attribute `name` in an element string, or None."""
    m = re.search(r'\b%s="(-?[0-9.]+)"' % name, seg)
    return float(m.group(1)) if m else None


def _near(a, b):
    return a is not None and b is not None and abs(a - b) <= 0.5


def _svg_diagram_fill(svg):
    """The diagram's own background colour (#rrggbb) for this SVG, or None.

    The full-canvas background <rect> whose geometry matches the original
    (pre-band) viewBox and that carries no stroke and no dediren/a11y marker.
    None when the render is light/transparent (no such rect) — the caller then
    keeps the gallery's default sheet.
    """
    box = _original_viewbox(svg)
    if box is None:
        return None
    minx, miny, w, h = box
    for m in re.finditer(r"<rect\b[^>]*/>", svg):
        seg = m.group(0)
        if "stroke=" in seg or "data-dediren-" in seg or "data-arch-a11y=" in seg:
            continue
        fill = re.search(r'\bfill="(#[0-9a-fA-F]{6})"', seg)
        if not fill:
            continue
        if (_near(_attr_num(seg, "x"), minx) and _near(_attr_num(seg, "y"), miny)
                and _near(_attr_num(seg, "width"), w)
                and _near(_attr_num(seg, "height"), h)):
            return fill.group(1)
    return None


def _lum(hexc):
    """Rec.601 luminance (0..255) of a #rrggbb colour."""
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def _mix(a, b, frac):
    """Blend #rrggbb `a` with #rrggbb `b`, keeping `frac` (0..1) of `a`."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(
        round(ca[i] * frac + cb[i] * (1 - frac)) for i in range(3))


def _derived_sheet(fill):
    """(sheet, sheet-line) for a diagram whose own background is `fill`.

    The sheet matches the diagram background exactly; the border steps a little
    off it toward the opposite luminance so the card edge stays visible against
    a dark or a light diagram alike.
    """
    contrast = "#000000" if _lum(fill) >= 128 else "#ffffff"
    return fill, _mix(fill, contrast, 0.86)


def _plate_sheet(svg):
    """(sheet, sheet-line) to pin on this view's card, or (None, None).

    None keeps the gallery default. Only a non-white diagram background is
    harmonized; a white (#ffffff) or transparent render keeps the default warm
    light sheet, so existing light galleries are visually unchanged.
    """
    fill = _svg_diagram_fill(svg)
    if fill and fill.lower() != "#ffffff":
        return _derived_sheet(fill)
    return None, None


# ------------------------------------------------------- author theme ----
# An optional gallery-theme.json beside project.json overrides design tokens.

class GalleryThemeError(ValueError):
    """The package's gallery-theme.json is present but malformed."""


def _check_token(name, value):
    if name not in _THEME_TOKENS:
        raise GalleryThemeError(
            "gallery-theme.json: unknown token %r (valid: %s)"
            % (name, ", ".join(sorted(_THEME_TOKENS))))
    if not isinstance(value, str):
        raise GalleryThemeError(
            "gallery-theme.json: token %r must be a string, got %s"
            % (name, type(value).__name__))


def _load_gallery_theme(pkg_dir):
    """The package's gallery-theme.json body, or {} when the sidecar is absent.

    Shape: {"theme": {<token>: <css value>, ..., "light": {...}, "dark": {...}}}.
    Tokens are the Colour-token names without the leading "--"; keys outside
    "light"/"dark" apply to both themes, the per-theme maps override them.
    """
    path = os.path.join(pkg_dir, "gallery-theme.json")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError:
        return {}
    if not isinstance(raw, dict):
        raise GalleryThemeError("gallery-theme.json: top level must be an object")
    unknown = set(raw) - {"theme"}
    if unknown:
        raise GalleryThemeError(
            "gallery-theme.json: unexpected key(s) %s (only 'theme' is used)"
            % ", ".join(sorted(repr(k) for k in unknown)))
    return raw


def _resolve_theme(pkg_dir):
    """(light_tokens, dark_tokens, sheet_pinned) after any author overrides.

    Per token, precedence is: per-theme author override > shared author
    override > built-in default. sheet_pinned is True when the author set
    `sheet` or `sheet-line` anywhere, which turns off per-view sheet derivation
    so the authored value wins (author override > per-view derived > default).
    """
    theme = _load_gallery_theme(pkg_dir).get("theme", {})
    if not isinstance(theme, dict):
        raise GalleryThemeError("gallery-theme.json: 'theme' must be an object")
    shared, light_over, dark_over = {}, {}, {}
    for k, val in theme.items():
        if k in ("light", "dark"):
            if not isinstance(val, dict):
                raise GalleryThemeError(
                    "gallery-theme.json: '%s' must be an object" % k)
            target = light_over if k == "light" else dark_over
            for tk, tv in val.items():
                _check_token(tk, tv)
                target[tk] = tv
        else:
            _check_token(k, val)
            shared[k] = val
    light = {**_LIGHT, **shared, **light_over}
    dark = {**_DARK, **shared, **dark_over}
    sheet_pinned = any("sheet" in o or "sheet-line" in o
                       for o in (shared, light_over, dark_over))
    return light, dark, sheet_pinned


def _emit_tokens(tokens):
    """Render a token dict as indented CSS custom-property declarations."""
    return "".join("  --%s:%s;\n" % (k, v) for k, v in tokens.items())


def collect(pkg_dir):
    """Return (data, plates_html) for the package, or raise SourceMissing."""
    proj = _load_project(pkg_dir)
    prof = profile_resolver(proj, pkg_dir)
    counters, data, plates = {}, [], []
    for v in proj["views"]:
        vid = v["id"]
        key, gtitle, gnote, prefix = classify(prof(v), v.get("diagramKind", ""))
        counters[key] = counters.get(key, 0) + 1
        meta_out = v.get("metadata", {}).get(
            "output", "generated/render-metadata/%s.json" % vid)
        svg_out = v.get("render", {}).get("output", "generated/svg/%s.svg" % vid)
        meta_path = os.path.join(pkg_dir, meta_out)
        svg_path = os.path.join(pkg_dir, svg_out)
        if not os.path.exists(meta_path):
            raise SourceMissing("render-metadata: %s" % meta_out)
        if not os.path.exists(svg_path):
            raise SourceMissing("svg: %s" % svg_out)
        n, e = _count(meta_path)
        with open(svg_path, encoding="utf-8") as fh:
            svg = fh.read().strip()
        sheet, sheet_line = _plate_sheet(svg)
        data.append({
            "id": vid,
            "code": "%s%d" % (prefix, counters[key]),
            "group": {"key": key, "title": gtitle, "note": gnote},
            "title": v.get("title", vid),
            "q": v.get("question", ""),
            "kind": v.get("diagramKind", ""),
            "nodes": n, "edges": e,
            "status": status_of(e),
            "sheet": sheet, "sheetLine": sheet_line,
        })
        plates.append(
            '<template class="plate" data-id="%s">%s</template>' % (vid, svg))
    return data, "\n".join(plates)


def _notation_summary(data):
    notes, seen = [], set()
    for d in data:
        note = d["group"]["note"]
        if note not in seen:
            seen.add(note)
            notes.append(note)
    return " + ".join(notes) if notes else "no views"


def build_html(pkg_dir):
    """Full standalone HTML for the package (pure function of its sources)."""
    proj = _load_project(pkg_dir)
    data, plates_html = collect(pkg_dir)
    light, dark, sheet_pinned = _resolve_theme(pkg_dir)
    feature = proj.get("feature", os.path.basename(os.path.normpath(pkg_dir)))
    lang = proj.get("lang", "en")
    direction = proj.get("dir", "ltr")
    n = len(data)
    sub = "%d view%s · %s" % (n, "" if n == 1 else "s", _notation_summary(data))
    foot = os.path.normpath(pkg_dir)
    return (TEMPLATE
            .replace("__FAVICON__", _favicon())
            .replace("__LANG__", lang)
            .replace("__DIR__", direction)
            .replace("__PAGETITLE__", "%s · architecture gallery" % feature)
            .replace("__EYEBROW__", feature)
            .replace("__TITLE__", "Architecture gallery")
            .replace("__SUB__", sub)
            .replace("__THEME_LIGHT__", _emit_tokens(light))
            .replace("__THEME_DARK__", _emit_tokens(dark))
            .replace("__SHEET_DERIVE__", "false" if sheet_pinned else "true")
            .replace("__FOOT__", foot)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__PLATES__", plates_html))


# ---------------------------------------------------------------- template ----
TEMPLATE = r"""<!doctype html>
<html lang="__LANG__" dir="__DIR__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__PAGETITLE__</title>
<link rel="icon" href="__FAVICON__">
<style>
/* Colour tokens are emitted from build-gallery.py's palette (merged with any
   gallery-theme.json override); --sans/--mono are theme-independent. */
:root{
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,"JetBrains Mono",Menlo,Consolas,monospace;
__THEME_LIGHT__}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
__THEME_DARK__}}
:root[data-theme="dark"]{
__THEME_DARK__}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:var(--mono)}
#app{display:grid;grid-template-columns:304px minmax(0,1fr);height:100vh;overflow:hidden}

/* ---------- register rail ---------- */
#rail{background:var(--rail);border-inline-end:1px solid var(--line);display:flex;flex-direction:column;min-height:0}
.mast{padding:22px 20px 16px;border-bottom:1px solid var(--line)}
.mast-eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-ink)}
.mast-title{margin:11px 0 0;font-size:20px;line-height:1.18;font-weight:640;letter-spacing:-.02em;text-wrap:balance}
.mast-sub{margin:9px 0 0;font-family:var(--mono);font-size:11px;line-height:1.55;color:var(--muted);letter-spacing:.01em}
#register{flex:1;min-height:0;overflow-y:auto;padding:6px 10px 20px}
.reg-group{margin-top:15px}
.reg-head{display:flex;align-items:baseline;justify-content:space-between;padding:2px 8px 7px;border-bottom:1px solid var(--line);margin-bottom:5px}
.reg-title{font-family:var(--mono);font-size:10.5px;letter-spacing:.15em;text-transform:uppercase;color:var(--muted);font-weight:600}
.reg-note{font-family:var(--mono);font-size:10px;letter-spacing:.06em;color:var(--faint)}
.reg-item{display:grid;grid-template-columns:34px 1fr auto;align-items:center;gap:9px;width:100%;text-align:left;
  border:0;border-inline-start:2px solid transparent;background:transparent;color:var(--ink);
  padding:7px 8px 7px 10px;border-start-end-radius:7px;border-end-end-radius:7px;cursor:pointer;font-family:inherit}
.reg-item:hover{background:color-mix(in srgb,var(--accent) 7%,transparent)}
.reg-item[aria-selected="true"]{background:var(--panel);border-inline-start-color:var(--accent);box-shadow:var(--shadow)}
.reg-code{font-family:var(--mono);font-size:12px;font-weight:600;color:var(--faint);font-variant-numeric:tabular-nums;letter-spacing:.02em}
.reg-item[aria-selected="true"] .reg-code{color:var(--accent-ink)}
.reg-label{font-size:12.5px;letter-spacing:-.005em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.reg-item[aria-selected="true"] .reg-label{font-weight:600}
.reg-meta{font-family:var(--mono);font-size:9.5px;color:var(--faint);font-variant-numeric:tabular-nums}
.rail-foot{padding:9px 20px;border-top:1px solid var(--line);font-family:var(--mono);font-size:10px;color:var(--faint);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

/* ---------- stage ---------- */
#stage{display:flex;flex-direction:column;min-width:0;min-height:0}
#head{display:flex;gap:20px;align-items:flex-start;justify-content:space-between;padding:16px 24px 15px;
  border-bottom:1px solid var(--line);background:var(--panel)}
.head-plate{display:flex;gap:14px;min-width:0}
#p-code{font-family:var(--mono);font-size:27px;font-weight:600;line-height:1;letter-spacing:.01em;color:var(--accent-ink);
  padding-top:3px;font-variant-numeric:tabular-nums}
.head-main{min-width:0}
.eyebrow{display:flex;gap:7px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
#p-title{margin:0;font-size:19px;font-weight:640;letter-spacing:-.02em;line-height:1.2;text-wrap:balance}
#p-q{margin:5px 0 0;font-size:13px;color:var(--muted);max-width:74ch}
.chip{display:inline-flex;align-items:center;font-family:var(--mono);font-size:10.5px;font-weight:600;letter-spacing:.03em;
  padding:3px 8px;border-radius:5px;white-space:nowrap}
.chip-kind{background:var(--wash);color:var(--accent-ink)}
.chip-ok{background:var(--ok-wash);color:var(--ok)}
.chip-warn{background:var(--warn-wash);color:var(--warn)}
.chip-count{background:transparent;border:1px solid var(--line-2);color:var(--muted);font-variant-numeric:tabular-nums}
.tools{display:flex;gap:9px;align-items:center;flex-shrink:0}
.zoom{display:inline-flex;border:1px solid var(--line-2);border-radius:8px;overflow:hidden;background:var(--panel)}
.zoom button{border:0;background:transparent;color:var(--ink);font-family:var(--mono);font-size:12px;font-weight:600;
  padding:7px 11px;cursor:pointer}
.zoom button+button{border-inline-start:1px solid var(--line)}
.zoom button:hover{background:color-mix(in srgb,var(--accent) 10%,transparent)}
.iconbtn{border:1px solid var(--line-2);background:var(--panel);color:var(--ink);width:35px;height:34px;border-radius:8px;
  cursor:pointer;font-size:15px;line-height:1}
.iconbtn:hover{background:color-mix(in srgb,var(--accent) 10%,transparent)}

#viewer{flex:1;min-height:0;overflow:auto;padding:26px;display:flex;align-items:flex-start}
#sheet{background:var(--sheet);border:1px solid var(--sheet-line);border-radius:10px;box-shadow:var(--shadow);
  padding:20px;width:max-content;margin-inline:auto}
#sheet.swap{animation:swap .18s ease}
@keyframes swap{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
#plate-host{display:block}
#plate-host svg{display:block;height:auto;max-width:none}
#plate-host svg [data-arch-a11y="visible-title"]{display:none}  /* title lives in the chrome */
#foot{display:flex;gap:16px;align-items:center;padding:8px 24px;border-top:1px solid var(--line);
  background:var(--panel);font-family:var(--mono);font-size:11px;color:var(--faint)}
#p-note{color:var(--warn)}

:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}

@media (max-width:900px){
  #app{grid-template-columns:1fr;grid-template-rows:auto minmax(0,1fr)}
  #rail{border-inline-end:0;border-block-end:1px solid var(--line);max-height:40vh}
  #p-code{font-size:22px}
}
@media (prefers-reduced-motion:reduce){#sheet.swap{animation:none}}
</style>
</head>
<body>
<div id="app">
  <aside id="rail">
    <div class="mast">
      <div class="mast-eyebrow">__EYEBROW__</div>
      <h1 class="mast-title">__TITLE__</h1>
      <p class="mast-sub">__SUB__</p>
    </div>
    <nav id="register" aria-label="Views" role="tablist"></nav>
    <div class="rail-foot">__FOOT__</div>
  </aside>
  <main id="stage">
    <header id="head">
      <div class="head-plate">
        <div id="p-code" aria-hidden="true"></div>
        <div class="head-main">
          <div class="eyebrow">
            <span id="p-kind" class="chip chip-kind"></span>
            <span id="p-status" class="chip"></span>
            <span id="p-count" class="chip chip-count"></span>
          </div>
          <h2 id="p-title"></h2>
          <p id="p-q"></p>
        </div>
      </div>
      <div class="tools">
        <div class="zoom" role="group" aria-label="Zoom">
          <button id="zout" title="Zoom out" aria-label="Zoom out">–</button>
          <button id="zfit" title="Fit to width">Fit</button>
          <button id="zin" title="Zoom in" aria-label="Zoom in">+</button>
        </div>
        <button id="theme" class="iconbtn" title="Toggle light/dark" aria-label="Toggle theme">◐</button>
      </div>
    </header>
    <div id="viewer"><div id="sheet"><div id="plate-host"></div></div></div>
    <footer id="foot"><span id="p-path"></span><span id="p-note"></span></footer>
  </main>
</div>

<div hidden>__PLATES__</div>

<script>
"use strict";
const DATA = __DATA__;
const SHEET_DERIVE = __SHEET_DERIVE__;  // false when an author theme pins the sheet
const byId = Object.fromEntries(DATA.map(d => [d.id, d]));
const q = s => document.querySelector(s);
const esc = s => s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let current = null, zoom = 100;

// build the register from the data
(function buildRegister(){
  const groups = [];
  for (const d of DATA){
    let g = groups.find(x => x.key === d.group.key);
    if (!g){ g = {key:d.group.key, title:d.group.title, note:d.group.note, items:[]}; groups.push(g); }
    g.items.push(d);
  }
  q('#register').innerHTML = groups.map(g => `
    <section class="reg-group">
      <header class="reg-head"><span class="reg-title">${esc(g.title)}</span><span class="reg-note">${esc(g.note)} · ${g.items.length}</span></header>
      ${g.items.map(d => `
        <button class="reg-item" role="tab" data-id="${d.id}" aria-selected="false" title="${esc(d.title)}">
          <span class="reg-code">${d.code}</span>
          <span class="reg-label">${esc(d.title)}</span>
          <span class="reg-meta">${d.nodes}·${d.edges}</span>
        </button>`).join('')}
    </section>`).join('');
})();

const viewer = q('#viewer'), sheet = q('#sheet');
// Content width inside the sheet ("fit to width"): the viewer minus its own padding
// minus the sheet's padding + border. At 100% the diagram fills this width — but the
// scale is capped so it never enlarges past the SVG's real pixel width (100% = crisp
// real size). Wide diagrams scale down to fit; narrow/tall ones sit at real size and
// scroll vertically instead of being blown up. The sheet then shrink-wraps the result
// (width:max-content) and the rounded card grows past the viewport intact on zoom-in.
function availWidth(){
  const vs = getComputedStyle(viewer), ss = getComputedStyle(sheet);
  return Math.max(0, viewer.clientWidth
    - parseFloat(vs.paddingLeft) - parseFloat(vs.paddingRight)
    - parseFloat(ss.paddingLeft) - parseFloat(ss.paddingRight)
    - parseFloat(ss.borderLeftWidth) - parseFloat(ss.borderRightWidth));
}
// Intrinsic pixel width straight off the SVG (width attr, viewBox as fallback).
function intrinsicWidth(s){
  return parseFloat(s.getAttribute('width')) || (s.viewBox && s.viewBox.baseVal && s.viewBox.baseVal.width);
}
function applyZoom(){
  const s = q('#plate-host svg'); if (!s) return;
  const base = Math.min(intrinsicWidth(s), availWidth());   // fill the width, but never past real pixels
  s.style.width = Math.round(base * zoom / 100) + 'px';
}
function setZoom(z){ zoom = Math.max(25, Math.min(400, z)); applyZoom(); }

function select(id){
  const d = byId[id]; if (!d) return;
  current = id;
  document.querySelectorAll('.reg-item').forEach(b => b.setAttribute('aria-selected', String(b.dataset.id === id)));
  const tpl = document.querySelector(`template.plate[data-id="${id}"]`);
  q('#plate-host').replaceChildren(tpl ? tpl.content.cloneNode(true) : document.createTextNode(''));
  q('#p-code').textContent  = d.code;
  q('#p-kind').textContent  = d.kind;
  q('#p-title').textContent = d.title;
  q('#p-q').textContent     = d.q;
  const st = q('#p-status');
  st.textContent = d.status === 'warning' ? 'dense layout' : 'layout ok';
  st.className = 'chip ' + (d.status === 'warning' ? 'chip-warn' : 'chip-ok');
  q('#p-count').textContent = `${d.nodes} nodes · ${d.edges} relations`;
  q('#p-path').textContent  = `generated/svg/${d.id}.svg`;
  q('#p-note').textContent  = d.status === 'warning' ? 'dense diagram — zoom in for detail' : '';
  zoom = 100; applyZoom();
  if (location.hash.slice(1) !== id) history.replaceState(null, '', '#' + id);
  const sheet = q('#sheet');
  // Per-view sheet: a dark diagram gets its own dark, harmonized card. Skipped
  // when an author theme pins the sheet (SHEET_DERIVE false) so the pinned value
  // wins; the else branch clears any inline sheet left by the previous view.
  if (SHEET_DERIVE && d.sheet){ sheet.style.setProperty('--sheet', d.sheet); sheet.style.setProperty('--sheet-line', d.sheetLine); }
  else { sheet.style.removeProperty('--sheet'); sheet.style.removeProperty('--sheet-line'); }
  sheet.classList.remove('swap'); void sheet.offsetWidth; sheet.classList.add('swap');
  document.querySelector(`.reg-item[data-id="${id}"]`)?.scrollIntoView({block:'nearest'});
}

document.querySelectorAll('.reg-item').forEach(b => b.addEventListener('click', () => select(b.dataset.id)));
q('#zin').onclick  = () => setZoom(zoom + 25);
q('#zout').onclick = () => setZoom(zoom - 25);
q('#zfit').onclick = () => setZoom(100);
addEventListener('resize', applyZoom);  // keep "fit" honest when the window changes

// Ctrl/⌘ + wheel (and trackpad pinch, which reports ctrlKey) zooms toward the pointer;
// plain wheel scrolls the viewer as before. Registered non-passive so the browser's own
// ctrl-wheel page zoom can be cancelled — but preventDefault fires only on the zoom path.
viewer.addEventListener('wheel', e => {
  if (!e.ctrlKey && !e.metaKey) return;
  e.preventDefault();
  const s = q('#plate-host svg'); if (!s) return;
  let dy = e.deltaY;                                    // normalise line/page deltas to ~pixels
  if (e.deltaMode === 1) dy *= 16; else if (e.deltaMode === 2) dy *= viewer.clientHeight;
  const before = s.getBoundingClientRect();
  const fx = (e.clientX - before.left) / before.width; // pointer as a fraction of the SVG box
  const fy = (e.clientY - before.top)  / before.height;
  setZoom(zoom * Math.exp(Math.max(-0.25, Math.min(0.25, -dy * 0.0015))));
  const after = s.getBoundingClientRect();              // keep that SVG point under the pointer
  viewer.scrollLeft += after.left + fx * after.width  - e.clientX;
  viewer.scrollTop  += after.top  + fy * after.height - e.clientY;
}, {passive:false});

q('#register').addEventListener('keydown', e => {
  if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
  e.preventDefault();
  const ids = DATA.map(d => d.id), i = ids.indexOf(current);
  const next = e.key === 'ArrowDown' ? Math.min(ids.length - 1, i + 1) : Math.max(0, i - 1);
  select(ids[next]);
  document.querySelector(`.reg-item[data-id="${ids[next]}"]`)?.focus();
});

const root = document.documentElement;
q('#theme').onclick = () => {
  const cur = root.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
  root.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
};

addEventListener('hashchange', () => {
  const id = location.hash.slice(1);
  if (byId[id] && id !== current) select(id);
});

if (DATA.length) {
  const start = byId[location.hash.slice(1)] ? location.hash.slice(1) : DATA[0].id;
  select(start);
}
</script>
</body>
</html>
"""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check = False
    positional = []
    for a in argv:
        if a in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return 0
        if a == "--check":
            check = True
        elif a.startswith("-"):
            sys.stderr.write("unknown option: %s\n" % a)
            return 2
        else:
            positional.append(a)
    if len(positional) != 1:
        sys.stderr.write("usage: build-gallery.py [--check] <package-dir>\n")
        return 2
    pkg = positional[0]
    try:
        html = build_html(pkg)
    except SourceMissing as exc:
        sys.stderr.write("sources incomplete: %s\n" % exc)
        return 3
    except (OSError, ValueError, KeyError) as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    out = os.path.join(pkg, "gallery.html")
    if check:
        try:
            with open(out, encoding="utf-8") as fh:
                current = fh.read()
        except OSError:
            sys.stderr.write("stale: %s is missing\n" % out)
            return 1
        if current != html:
            sys.stderr.write("stale: %s differs from current sources\n" % out)
            return 1
        sys.stdout.write("fresh: %s\n" % out)
        return 0
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    sys.stdout.write("wrote %s (%d views)\n" % (out, html.count('class="plate"')))
    return 0


if __name__ == "__main__":
    sys.exit(main())
