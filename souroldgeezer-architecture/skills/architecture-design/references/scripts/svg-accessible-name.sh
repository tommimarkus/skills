#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  svg-accessible-name.sh --title <text> [--desc <text>] <svg-file>
  svg-accessible-name.sh --check [--title <text>] <svg-file>
  svg-accessible-name.sh --help

Post-render accessible-name completion for dediren-rendered SVG views. This
repo-owned step edits generated render output only, never the upstream bundle.

Apply mode ensures the artifact carries a per-view accessible name and a
visible title:

- When the runtime already emitted a native accessible name (role="img" plus
  a root <title>, available since the accessible-name fix in the release-
  resolved runtime; the title falls back to the layout view id), the step
  keeps the native markup, upgrades the <title> text to the view label,
  ensures a <desc> carrying the view's architecture question, and adds the
  visible title block.
- When the artifact has no accessible name (older runtimes), the step injects
  role="img", aria-labelledby to an injected <title>, aria-describedby to an
  optional <desc>, and the visible title block.

The visible per-view title renders in a band added above the diagram by
expanding the viewBox upward. To keep the band readable on any render policy
the step also:

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
block carrying that text.

Exit codes:
  0  applied or check passed
  1  check failed
  2  usage error
  3  input is not an SVG with a parseable viewBox
USAGE
}

MODE="apply"
TITLE=""
DESC=""
FILE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --check)
      MODE="check"
      shift
      ;;
    --title)
      [ $# -ge 2 ] || { printf -- '--title needs a value\n' >&2; exit 2; }
      TITLE="$2"
      shift 2
      ;;
    --desc)
      [ $# -ge 2 ] || { printf -- '--desc needs a value\n' >&2; exit 2; }
      DESC="$2"
      shift 2
      ;;
    --*)
      printf 'Unknown option: %s\n' "$1" >&2
      exit 2
      ;;
    *)
      if [ -n "$FILE" ]; then
        printf 'Exactly one SVG file expected\n' >&2
        exit 2
      fi
      FILE="$1"
      shift
      ;;
  esac
done

if [ -z "$FILE" ]; then
  usage >&2
  exit 2
fi
if [ "$MODE" = "apply" ] && [ -z "$TITLE" ]; then
  printf 'Apply mode requires --title\n' >&2
  exit 2
fi
if [ ! -f "$FILE" ] || [ ! -r "$FILE" ]; then
  printf 'Not a readable file: %s\n' "$FILE" >&2
  exit 3
fi

export A11Y_TITLE="$TITLE"
export A11Y_DESC="$DESC"
export A11Y_MODE="$MODE"

run_awk() {
  awk '
    function esc(s) {
      gsub(/&/, "\\&amp;", s)
      gsub(/</, "\\&lt;", s)
      gsub(/>/, "\\&gt;", s)
      gsub(/"/, "\\&quot;", s)
      return s
    }
    function fmt(n) { return sprintf("%.6g", n) }
    function hexval(c) { return index("0123456789abcdef", tolower(c)) - 1 }
    # Rec.601 luminance threshold on a #rrggbb colour: a light background gets a
    # black title, a dark background gets a white one.
    function contrast_fill(hex,    r, g, b) {
      r = hexval(substr(hex, 2, 1)) * 16 + hexval(substr(hex, 3, 1))
      g = hexval(substr(hex, 4, 1)) * 16 + hexval(substr(hex, 5, 1))
      b = hexval(substr(hex, 6, 1)) * 16 + hexval(substr(hex, 7, 1))
      return (0.299 * r + 0.587 * g + 0.114 * b >= 128) ? "#000000" : "#ffffff"
    }
    function near(a, b) { return (a - b <= 0.5 && b - a <= 0.5) }
    # Numeric value of attribute "name" in a self-closing element string, or
    # "NaN" when absent.
    function attr_num(seg, name,    v) {
      if (!match(seg, " " name "=\"[-0-9.]+\"")) { return "NaN" }
      v = substr(seg, RSTART, RLENGTH)
      sub("^ " name "=\"", "", v)
      sub(/"$/, "", v)
      return v + 0
    }
    # Find the diagram background rect: a self-closing <rect> whose x/y/width/
    # height match the pre-band viewBox and that carries neither a stroke nor a
    # dediren marker (node rects carry both). Return its #rrggbb fill verbatim
    # (so the band matches the diagram background exactly; the luminance math
    # tolerates any case), or "" when none qualifies.
    function find_bg_fill(b, minx, miny, w, h,    s, seg, f) {
      s = b
      while (match(s, /<rect [^>]*\/>/)) {
        seg = substr(s, RSTART, RLENGTH)
        s = substr(s, RSTART + RLENGTH)
        if (seg ~ /stroke=/ || seg ~ /data-dediren-/) { continue }
        if (seg !~ /fill="#[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]"/) { continue }
        if (near(attr_num(seg, "x"), minx) && near(attr_num(seg, "y"), miny) && \
            near(attr_num(seg, "width"), w) && near(attr_num(seg, "height"), h)) {
          f = seg
          sub(/^.*fill="/, "", f)
          sub(/".*$/, "", f)
          return f
        }
      }
      return ""
    }
    # Append attrs to the root <svg> tag (mutates the global tag), handling
    # both self-closing and open tag endings.
    function inject_root_attrs(attrs) {
      if (tag ~ /\/>$/) {
        sub(/\/>$/, attrs "/>", tag)
      } else {
        sub(/>$/, attrs ">", tag)
      }
    }
    # Replace the text of the first <elem ...>text</elem> in the global body,
    # keeping the opening tag byte-for-byte. Returns 1 on match, 0 otherwise.
    function replace_elem_text(elem, text,    seg, open_len) {
      if (!match(body, "<" elem "[^>]*>[^<]*</" elem ">")) { return 0 }
      seg = substr(body, RSTART, RLENGTH)
      open_len = index(seg, ">")
      body = substr(body, 1, RSTART - 1) substr(seg, 1, open_len) text "</" elem ">" substr(body, RSTART + RLENGTH)
      return 1
    }
    BEGIN { RS = "\x01" }
    {
      doc = $0
      mode = ENVIRON["A11Y_MODE"]
      title = esc(ENVIRON["A11Y_TITLE"])
      desc = esc(ENVIRON["A11Y_DESC"])

      start = index(doc, "<svg")
      if (start == 0) { exit 3 }
      rest = substr(doc, start)
      gtpos = index(rest, ">")
      if (gtpos == 0) { exit 3 }
      head = substr(doc, 1, start - 1)
      tag = substr(rest, 1, gtpos)
      body = substr(rest, gtpos + 1)

      if (mode == "check") {
        ok = 1
        role = (tag ~ / role="img"/) ? "yes" : "no"
        hastitle = (body ~ /<title[^>]*>[^<]+<\/title>/) ? "yes" : "no"
        if (role == "no" || hastitle == "no") { ok = 0 }
        printf "accessible-name: %s (role=img: %s; nonempty title: %s)\n", (ok ? "present" : "missing"), role, hastitle
        if (title != "") {
          visible = (index(body, ">" title "</text>") > 0) ? "present" : "missing"
          printf "visible-title: %s\n", visible
          if (visible == "missing") { ok = 0 }
        } else {
          printf "visible-title: not checked (no --title)\n"
        }
        exit (ok ? 0 : 1)
      }

      # Remove any previous injection from this script (the current attribute
      # shape, the earlier combined aria-labelledby shape, and the optional
      # data-arch-a11y-height marker added by the width/height sync). Restore
      # the original viewBox, and the original root height when the marker is
      # present (older injected artifacts predate the height sync and grew the
      # viewBox without recording a height).
      if (match(tag, / data-arch-a11y="root" data-arch-a11y-viewbox="[^"]*"( data-arch-a11y-height="[^"]*")?( role="img" aria-labelledby="arch-a11y-title( arch-a11y-desc)?"( aria-describedby="arch-a11y-desc")?)?/)) {
        injected = substr(tag, RSTART, RLENGTH)
        origvb = injected
        sub(/^.*data-arch-a11y-viewbox="/, "", origvb)
        sub(/".*$/, "", origvb)
        tag = substr(tag, 1, RSTART - 1) substr(tag, RSTART + RLENGTH)
        sub(/ viewBox="[^"]*"/, " viewBox=\"" origvb "\"", tag)
        if (injected ~ /data-arch-a11y-height="/) {
          origh = injected
          sub(/^.*data-arch-a11y-height="/, "", origh)
          sub(/".*$/, "", origh)
          sub(/ height="[^"]*"/, " height=\"" origh "\"", tag)
        }
      }
      gsub(/\n?<title id="arch-a11y-title">[^<]*<\/title>/, "", body)
      gsub(/\n?<desc id="arch-a11y-desc">[^<]*<\/desc>/, "", body)
      gsub(/\n?<rect data-arch-a11y="band-bg"[^>]*\/>/, "", body)
      gsub(/\n?<text data-arch-a11y="visible-title"[^>]*>[^<]*<\/text>/, "", body)

      if (match(tag, / viewBox="[^"]*"/) == 0) { exit 3 }
      vb = substr(tag, RSTART, RLENGTH)
      sub(/^ viewBox="/, "", vb)
      sub(/"$/, "", vb)
      gsub(/,/, " ", vb)
      n = split(vb, box, /[ \t]+/)
      if (n != 4) { exit 3 }
      minx = box[1] + 0; miny = box[2] + 0; w = box[3] + 0; h = box[4] + 0

      band = 32; fontsize = 16; pad = 8
      newvb = fmt(minx) " " fmt(miny - band) " " fmt(w) " " fmt(h + band)
      sub(/ viewBox="[^"]*"/, " viewBox=\"" newvb "\"", tag)

      # Keep the root height in sync with the band-expanded viewBox, or the
      # aspect ratio mismatch makes browsers letterbox the diagram with
      # transparent bars that read as a border. Grow the numeric root height by
      # the band (width is unchanged: the band is added above, not beside) and
      # record the original so a rerun restores then re-grows rather than
      # accumulating. Skip when the root carries no numeric height (nothing to
      # letterbox against a container-scaled SVG).
      heightattr = ""
      if (match(tag, / height="[0-9.]+"/)) {
        hseg = substr(tag, RSTART, RLENGTH)
        sub(/^ height="/, "", hseg)
        sub(/"$/, "", hseg)
        origheight = hseg + 0
        sub(/ height="[0-9.]+"/, " height=\"" fmt(origheight + band) "\"", tag)
        heightattr = " data-arch-a11y-height=\"" fmt(origheight) "\""
      }

      # Paint the band with the diagram background colour and give the title a
      # contrasting fill, so it stays readable on a non-light render policy.
      # Fall back to the prior behaviour (no band rect, default title fill) when
      # the background rect is missing or not a #rrggbb colour.
      bandbg = find_bg_fill(body, minx, miny, w, h)
      bandrect = ""
      fillattr = ""
      if (bandbg != "") {
        bandrect = "\n<rect data-arch-a11y=\"band-bg\" x=\"" fmt(minx) "\" y=\"" fmt(miny - band) "\" width=\"" fmt(w) "\" height=\"" fmt(band) "\" fill=\"" bandbg "\"/>"
        fillattr = " fill=\"" contrast_fill(bandbg) "\""
      }

      # Band rect before the title text: the band paints under the title.
      visible = bandrect "\n<text data-arch-a11y=\"visible-title\" x=\"" fmt(minx + pad) "\" y=\"" fmt(miny - 12) "\" font-family=\"sans-serif\" font-size=\"" fontsize "\" font-weight=\"bold\"" fillattr ">" title "</text>"

      # Runtime-native accessible name: keep the native markup, upgrade the
      # title text to the view label, and ensure the desc.
      native = (tag ~ / role="img"/ && body ~ /<title[^>]*>[^<]*<\/title>/)
      if (native) {
        inject = " data-arch-a11y=\"root\" data-arch-a11y-viewbox=\"" vb "\"" heightattr
        inject_root_attrs(inject)

        replace_elem_text("title", title)
        if (desc != "") {
          if (!replace_elem_text("desc", desc)) {
            close_pos = index(body, "</title>")
            body = substr(body, 1, close_pos + 7) "\n<desc>" desc "</desc>" substr(body, close_pos + 8)
          }
        }
        close_pos = index(body, "</title>")
        anchor = close_pos + 7
        if (desc != "") {
          desc_pos = index(body, "</desc>")
          if (desc_pos > 0) { anchor = desc_pos + 6 }
        }
        body = substr(body, 1, anchor) visible substr(body, anchor + 1)

        printf "%s", head tag body > (FILENAME ".a11y-tmp")
        printf "completed native accessible name: title set%s; visible title block added\n", (desc != "" ? " + desc" : "")
        exit 0
      }

      # No native accessible name (older runtimes): inject the full markup.
      sub(/ role="img"/, "", tag)
      ids = " role=\"img\" aria-labelledby=\"arch-a11y-title\""
      if (desc != "") { ids = ids " aria-describedby=\"arch-a11y-desc\"" }
      inject = " data-arch-a11y=\"root\" data-arch-a11y-viewbox=\"" vb "\"" heightattr ids
      inject_root_attrs(inject)

      block = "\n<title id=\"arch-a11y-title\">" title "</title>"
      if (desc != "") {
        block = block "\n<desc id=\"arch-a11y-desc\">" desc "</desc>"
      }
      block = block visible

      printf "%s", head tag block body > (FILENAME ".a11y-tmp")
      printf "applied: role=img + title%s + visible title block; viewBox band added\n", (desc != "" ? " + desc" : "")
      exit 0
    }
  ' "$FILE"
}

if [ "$MODE" = "check" ]; then
  rc=0
  run_awk || rc=$?
  exit "$rc"
fi

rc=0
run_awk || rc=$?
if [ "$rc" -eq 0 ] && [ -f "$FILE.a11y-tmp" ]; then
  mv "$FILE.a11y-tmp" "$FILE"
else
  rm -f "$FILE.a11y-tmp"
fi
exit "$rc"
