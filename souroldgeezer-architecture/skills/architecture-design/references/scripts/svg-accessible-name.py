#!/usr/bin/env python3
"""Post-render visible title band for dediren-rendered SVG views.

This repo-owned step edits generated render output only, never the upstream
bundle. It is an XML-aware transform: it parses the rendered `<svg>` element
with the Python standard library (`xml.etree.ElementTree`), makes structural
edits (set root attributes, add a visible title band, and where needed
upgrade/inject `<title>`/`<desc>`), and reserialises. Everything before the
`<svg>` (any XML-declaration prolog) and after `</svg>` (a trailing newline) is
preserved verbatim, so only the `<svg>` subtree is canonicalised to the
serialiser's form.

The step's job is the *visible* per-view title band. The Dediren runtime emits
no visible chrome deliberately — duplicating the accessible name into visible
text is a WCAG 2.2 SC 1.1.1 double-labelling decision upstream leaves to the
caller — so without this step an exported diagram is unidentifiable outside its
package.

The accessible-name half is a compatibility path, not the job. Since Dediren
2026.07.28 the render lane takes each view's <title>/<desc> from the package's
`views[].presentation` title/question, so on the pinned runtime both branches
below leave the name untouched and only the band is added. They are kept because
the release resolver reads `DEDIREN_VERSION` from the environment with no floor
and neither lane pins it, so an artifact rendered by a pre-2026.07.28 runtime can
still reach this step (see the note at the injection branch in `do_apply`):

- When the artifact already carries a native accessible name (role="img" plus a
  root <title>), the step keeps the native markup, sets the <title> text to the
  view label and ensures a <desc> carrying the view's architecture question —
  the same text the pinned runtime already wrote — and adds the band.
- When the artifact has no accessible name (a pre-2026.07.28 runtime), the step
  injects role="img", aria-labelledby to an injected <title>, aria-describedby
  to an optional <desc>, and the band.

The band is added above the diagram by expanding the viewBox upward. To keep it
readable on any render policy the step also:

- syncs the root width/height with the expanded viewBox (the root height grows
  by the band) so browsers do not letterbox the diagram with transparent bars;
- paints the band with the diagram's own background colour and picks a title
  fill that contrasts with it, so a dark render policy does not yield a black,
  invisible title. Both are derived from the diagram's background <rect> (the
  one whose geometry matches the pre-band viewBox); when no such rect exists the
  band stays transparent with a default title fill, as before.

The original viewBox and root height are preserved in data-arch-a11y-viewbox
and data-arch-a11y-height attributes so reruns restore then re-expand instead of
stacking the band or accumulating height.

Check mode verifies presence without editing: role="img" on the root element
and a nonempty <title>; with --title it also requires the visible title text
block carrying that text. On the pinned runtime that reads as "the runtime's
native accessible name survived this step, and the band was added" rather than
"this step's injection landed".

Exit codes:
  0  applied or check passed
  1  check failed
  2  usage error
  3  input is not an SVG with a parseable viewBox
"""
import sys
import xml.etree.ElementTree as ET

# Standard-library parser by design: this bundled step runs standalone for
# installed users with no third-party dependency (defusedxml is third-party and
# would reintroduce the availability gate this re-platform exists to avoid; see
# issue #102). ElementTree is Safe against external-entity/XXE and DTD retrieval
# per the Python docs' XML-vulnerabilities table; its one exposure is internal
# entity expansion ("billion laughs"), which `_split_svg` forecloses by refusing
# any DOCTYPE/entity declaration before parsing. Input is dediren's own
# entity-free render output, never untrusted network XML.

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

BAND = 32
FONTSIZE = 16
PAD = 8

USAGE = """\
Usage:
  svg-accessible-name.py --title <text> [--desc <text>] <svg-file>
  svg-accessible-name.py --check [--title <text>] <svg-file>
  svg-accessible-name.py --help

Post-render visible title band for dediren-rendered SVG views. This repo-owned
step edits generated render output only, never the upstream bundle. It parses
the rendered <svg> with the Python standard library and makes structural edits;
the XML-declaration prolog and trailing newline are preserved verbatim while the
<svg> subtree is serialised to canonical form.

Apply mode adds the visible per-view title band above the diagram — its job —
syncing width/height and painting the band with a contrasting title fill. It
also keeps the accessible name correct for an artifact from a pre-2026.07.28
runtime (upgrading a runtime-native role="img"/<title>, or injecting the full
markup); on the pinned runtime the name already comes from the view's
`presentation`, so that half is a no-op.

Check mode verifies presence without editing: role="img" on the root element
and a nonempty <title>; with --title it also requires the visible title text
block carrying that text. On the pinned runtime that reads as "the runtime's
native accessible name survived this step, and the band was added".

Exit codes:
  0  applied or check passed
  1  check failed
  2  usage error
  3  input is not an SVG with a parseable viewBox
"""


def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def fmt(n: float) -> str:
    """Match the awk predecessor's sprintf("%.6g", n) geometry formatting."""
    return format(n, ".6g")


def _fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _near(el, name, target):
    """Numeric value of attribute `name` within 0.5 of target, else False."""
    v = _fnum(el.get(name))
    return v is not None and abs(v - target) <= 0.5


def _is_hex6(value):
    if not value or len(value) != 7 or value[0] != "#":
        return False
    return all(c in "0123456789abcdefABCDEF" for c in value[1:])


def contrast_fill(hex_colour: str) -> str:
    """Rec.601 luminance threshold: a light background gets a black title, a
    dark background a white one."""
    r = int(hex_colour[1:3], 16)
    g = int(hex_colour[3:5], 16)
    b = int(hex_colour[5:7], 16)
    return "#000000" if 0.299 * r + 0.587 * g + 0.114 * b >= 128 else "#ffffff"


def find_bg_fill(root, minx, miny, w, h):
    """The diagram background rect: a <rect> whose x/y/width/height match the
    pre-band viewBox and that carries neither a stroke nor a dediren marker
    (node rects carry both). Return its #rrggbb fill verbatim, or None."""
    for el in root.iter(_q("rect")):
        if "stroke" in el.attrib:
            continue
        if any(k.startswith("data-dediren-") for k in el.attrib):
            continue
        fill = el.get("fill", "")
        if not _is_hex6(fill):
            continue
        if (_near(el, "x", minx) and _near(el, "y", miny)
                and _near(el, "width", w) and _near(el, "height", h)):
            return fill
    return None


def _is_injected(child) -> bool:
    """A node this step owns: the injected title/desc (id markers) and the band
    rect / visible title text (data-arch-a11y markers)."""
    tag = child.tag
    if tag == _q("title") and child.get("id") == "arch-a11y-title":
        return True
    if tag == _q("desc") and child.get("id") == "arch-a11y-desc":
        return True
    if tag == _q("rect") and child.get("data-arch-a11y") == "band-bg":
        return True
    if tag == _q("text") and child.get("data-arch-a11y") == "visible-title":
        return True
    return False


def _insert_block(root, anchor, nodes):
    """Insert `nodes` right after `anchor` (or as the first children when anchor
    is None), each on its own line. The boundary whitespace that followed the
    anchor is transferred to the last inserted node, so `_remove_block` is an
    exact inverse and reruns are idempotent."""
    if not nodes:
        return
    if anchor is None:
        saved = root.text
        root.text = "\n"
        pos = 0
    else:
        saved = anchor.tail
        anchor.tail = "\n"
        pos = list(root).index(anchor) + 1
    last = len(nodes) - 1
    for i, node in enumerate(nodes):
        root.insert(pos + i, node)
        node.tail = "\n" if i < last else saved


def _remove_block(root, anchor, nodes):
    """Remove the contiguous injected `nodes`, restoring the boundary whitespace
    (the last node's tail) to the anchor — the inverse of `_insert_block`."""
    if not nodes:
        return
    boundary = nodes[-1].tail
    for node in nodes:
        root.remove(node)
    if anchor is None:
        root.text = boundary
    else:
        anchor.tail = boundary


def _strip_prior(root):
    """Undo any previous injection so apply is idempotent: remove the owned
    child nodes, restore the original viewBox and root height from the markers,
    and drop the marker attributes (plus the injected role/aria on the
    older-runtime path)."""
    mine = [c for c in list(root) if _is_injected(c)]
    if mine:
        idx0 = list(root).index(mine[0])
        anchor = list(root)[idx0 - 1] if idx0 > 0 else None
        _remove_block(root, anchor, mine)

    if root.get("data-arch-a11y") == "root":
        orig_vb = root.get("data-arch-a11y-viewbox")
        if orig_vb is not None:
            root.set("viewBox", orig_vb)
        orig_h = root.get("data-arch-a11y-height")
        if orig_h is not None and root.get("height") is not None:
            root.set("height", orig_h)

    was_injected = root.get("aria-labelledby") == "arch-a11y-title"
    for key in ("data-arch-a11y", "data-arch-a11y-viewbox", "data-arch-a11y-height"):
        root.attrib.pop(key, None)
    if was_injected:
        for key in ("role", "aria-labelledby", "aria-describedby"):
            root.attrib.pop(key, None)


def _native_child(root, tag):
    """A runtime-native <title>/<desc> — one this step does not own."""
    marker = "arch-a11y-title" if tag == "title" else "arch-a11y-desc"
    for child in root:
        if child.tag == _q(tag) and child.get("id") != marker:
            return child
    return None


def _split_svg(raw):
    """Split into (head, svg_text, tail) around the <svg> element. head (any
    XML-declaration prolog) and tail (trailing newline) are preserved verbatim.
    Refuse any DOCTYPE/entity declaration (dediren output has none) so the
    stdlib parser is never handed an entity-expansion ("billion laughs") DTD."""
    if "<!DOCTYPE" in raw or "<!ENTITY" in raw:
        return None
    start = raw.find("<svg")
    if start == -1:
        return None
    end = raw.rfind("</svg>")
    if end == -1:
        return None
    end += len("</svg>")
    return raw[:start], raw[start:end], raw[end:]


def _visible_block(root, minx, miny, w, h, title):
    """The band rect (when a background rect is derivable) and the visible title
    text, in paint order (band under title)."""
    nodes = []
    fill = None
    bandbg = find_bg_fill(root, minx, miny, w, h)
    if bandbg is not None:
        band = ET.Element(_q("rect"))
        band.set("data-arch-a11y", "band-bg")
        band.set("x", fmt(minx))
        band.set("y", fmt(miny - BAND))
        band.set("width", fmt(w))
        band.set("height", fmt(BAND))
        band.set("fill", bandbg)
        nodes.append(band)
        fill = contrast_fill(bandbg)

    visible = ET.Element(_q("text"))
    visible.set("data-arch-a11y", "visible-title")
    visible.set("x", fmt(minx + PAD))
    visible.set("y", fmt(miny - 12))
    visible.set("font-family", "sans-serif")
    visible.set("font-size", str(FONTSIZE))
    visible.set("font-weight", "bold")
    if fill is not None:
        visible.set("fill", fill)
    visible.text = title
    nodes.append(visible)
    return nodes


def do_check(root, title):
    role = "yes" if root.get("role") == "img" else "no"
    has_title = "no"
    for el in root.iter(_q("title")):
        if (el.text or "") != "":
            has_title = "yes"
            break
    ok = role == "yes" and has_title == "yes"
    print("accessible-name: %s (role=img: %s; nonempty title: %s)"
          % ("present" if ok else "missing", role, has_title))
    if title:
        present = any((el.text == title) for el in root.iter(_q("text")))
        print("visible-title: %s" % ("present" if present else "missing"))
        if not present:
            ok = False
    else:
        print("visible-title: not checked (no --title)")
    return 0 if ok else 1


def do_apply(root, title, desc):
    _strip_prior(root)

    vb_raw = root.get("viewBox")
    if vb_raw is None:
        return 3
    parts = vb_raw.replace(",", " ").split()
    if len(parts) != 4:
        return 3
    try:
        minx, miny, w, h = (float(p) for p in parts)
    except ValueError:
        return 3
    orig_vb = " ".join(parts)

    root.set("viewBox", "%s %s %s %s" % (fmt(minx), fmt(miny - BAND), fmt(w), fmt(h + BAND)))

    # Keep the root height in sync with the band-expanded viewBox (grow by the
    # band; width is unchanged as the band is added above), recording the
    # original so a rerun restores then re-grows rather than accumulating. Skip
    # when the root carries no plain-numeric height.
    height_marker = None
    height_attr = root.get("height")
    if height_attr and all(c in "0123456789." for c in height_attr):
        orig_height = float(height_attr)
        root.set("height", fmt(orig_height + BAND))
        height_marker = fmt(orig_height)

    root.set("data-arch-a11y", "root")
    root.set("data-arch-a11y-viewbox", orig_vb)
    if height_marker is not None:
        root.set("data-arch-a11y-height", height_marker)

    native_title = _native_child(root, "title")
    native = root.get("role") == "img" and native_title is not None

    visible = _visible_block(root, minx, miny, w, h, title)

    if native:
        native_title.text = title
        native_desc = _native_child(root, "desc")
        if desc:
            if native_desc is not None:
                native_desc.text = desc
            else:
                native_desc = ET.Element(_q("desc"))
                native_desc.text = desc
                _insert_block(root, native_title, [native_desc])
        anchor = native_desc if native_desc is not None else native_title
        _insert_block(root, anchor, visible)
        print("completed native accessible name: title set%s; visible title block added"
              % (" + desc" if desc else ""))
        return 0

    # No native accessible name: inject the full markup. Kept deliberately (repo
    # issue #112) after confirming the path is still reachable: `dediren-release.sh`
    # takes DEDIREN_VERSION from the environment with no floor, and neither lane
    # pins it — `dediren-mcp.sh` shells out to that same resolver and plugin.json
    # sets only the cache dirs — so a caller can resolve a release older than the
    # 2026.07.28 accessible-name fix and reach this step with an unnamed artifact.
    root.set("role", "img")
    root.set("aria-labelledby", "arch-a11y-title")
    if desc:
        root.set("aria-describedby", "arch-a11y-desc")

    block = []
    inj_title = ET.Element(_q("title"))
    inj_title.set("id", "arch-a11y-title")
    inj_title.text = title
    block.append(inj_title)
    if desc:
        inj_desc = ET.Element(_q("desc"))
        inj_desc.set("id", "arch-a11y-desc")
        inj_desc.text = desc
        block.append(inj_desc)
    block.extend(visible)
    _insert_block(root, None, block)
    print("applied: role=img + title%s + visible title block; viewBox band added"
          % (" + desc" if desc else ""))
    return 0


def main(argv):
    mode = "apply"
    title = ""
    desc = ""
    path = None

    args = list(argv)
    while args:
        arg = args.pop(0)
        if arg in ("--help", "-h"):
            print(USAGE, end="")
            return 0
        elif arg == "--check":
            mode = "check"
        elif arg == "--title":
            if not args:
                sys.stderr.write("--title needs a value\n")
                return 2
            title = args.pop(0)
        elif arg == "--desc":
            if not args:
                sys.stderr.write("--desc needs a value\n")
                return 2
            desc = args.pop(0)
        elif arg.startswith("--"):
            sys.stderr.write("Unknown option: %s\n" % arg)
            return 2
        else:
            if path is not None:
                sys.stderr.write("Exactly one SVG file expected\n")
                return 2
            path = arg

    if path is None:
        sys.stderr.write(USAGE)
        return 2
    if mode == "apply" and not title:
        sys.stderr.write("Apply mode requires --title\n")
        return 2

    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        sys.stderr.write("Not a readable file: %s\n" % path)
        return 3

    split = _split_svg(raw)
    if split is None:
        return 3
    head, svg_text, tail = split
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return 3

    if mode == "check":
        return do_check(root, title)

    rc = do_apply(root, title, desc)
    if rc != 0:
        return rc
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(head + ET.tostring(root, encoding="unicode") + tail)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
