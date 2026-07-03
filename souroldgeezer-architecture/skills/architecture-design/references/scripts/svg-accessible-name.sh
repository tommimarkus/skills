#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  svg-accessible-name.sh --title <text> [--desc <text>] <svg-file>
  svg-accessible-name.sh --check [--title <text>] <svg-file>
  svg-accessible-name.sh --help

Post-render accessible-name step for dediren-rendered SVG views. The
release-resolved Dediren runtime emits no accessible name; this repo-owned
step edits generated render output only, never the upstream bundle.

Apply mode injects on the root <svg> element: role="img" and aria-labelledby
pointing at an injected <title> (the view label) and optional <desc> (the
view's architecture question), plus a visible per-view title text block in a
band added above the diagram. The original viewBox is preserved in a
data-arch-a11y-viewbox attribute so reruns replace the previous injection
instead of stacking bands.

If the artifact already carries a runtime-native accessible name (role="img"
plus a <title> this script did not inject), apply mode removes only its own
previous injection, otherwise leaves the file as-is, and reports it.

Check mode verifies presence without editing: role="img" on the root element
and a nonempty <title>; with --title it also requires the visible title text
block carrying that text.

Exit codes:
  0  applied, already accessible, or check passed
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

      # Remove any previous injection from this script.
      restored = 0
      if (match(tag, / data-arch-a11y="root" data-arch-a11y-viewbox="[^"]*" role="img" aria-labelledby="arch-a11y-title( arch-a11y-desc)?"/)) {
        injected = substr(tag, RSTART, RLENGTH)
        origvb = injected
        sub(/^.*data-arch-a11y-viewbox="/, "", origvb)
        sub(/".*$/, "", origvb)
        tag = substr(tag, 1, RSTART - 1) substr(tag, RSTART + RLENGTH)
        sub(/ viewBox="[^"]*"/, " viewBox=\"" origvb "\"", tag)
        restored = 1
      }
      gsub(/\n?<title id="arch-a11y-title">[^<]*<\/title>/, "", body)
      gsub(/\n?<desc id="arch-a11y-desc">[^<]*<\/desc>/, "", body)
      gsub(/\n?<text data-arch-a11y="visible-title"[^>]*>[^<]*<\/text>/, "", body)

      # Respect a runtime-native accessible name.
      if (tag ~ / role="img"/ && body ~ /<title[^>]*>[^<]+<\/title>/) {
        printf "%s", head tag body > (FILENAME ".a11y-tmp")
        printf "runtime-native accessible name detected; no injection performed\n"
        exit 0
      }

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

      ids = "arch-a11y-title"
      if (desc != "") { ids = ids " arch-a11y-desc" }
      inject = " data-arch-a11y=\"root\" data-arch-a11y-viewbox=\"" vb "\" role=\"img\" aria-labelledby=\"" ids "\""
      if (tag ~ /\/>$/) {
        sub(/\/>$/, inject "/>", tag)
      } else {
        sub(/>$/, inject ">", tag)
      }

      block = "\n<title id=\"arch-a11y-title\">" title "</title>"
      if (desc != "") {
        block = block "\n<desc id=\"arch-a11y-desc\">" desc "</desc>"
      }
      block = block "\n<text data-arch-a11y=\"visible-title\" x=\"" fmt(minx + pad) "\" y=\"" fmt(miny - 12) "\" font-family=\"sans-serif\" font-size=\"" fontsize "\" font-weight=\"bold\">" title "</text>"

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
