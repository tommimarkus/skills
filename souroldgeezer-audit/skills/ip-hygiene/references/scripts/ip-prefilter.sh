#!/usr/bin/env bash
# ip-prefilter.sh — objective IP-hygiene pre-filter for the ip-hygiene skill.
# READ-ONLY scanner. Surfaces objective Q3/Q4 (copyrighted non-text / bundled
# asset / schema) CANDIDATES from touched paths. It NEVER answers the triage
# questions: empty output is NOT a clean bill of health (see SKILL.md Triage
# subclass-exclusion note). Q1/Q2 marks-and-prose stay with the auditor.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ip-prefilter.sh [--format text|json] [--] [PATH ...]

Scans PATHs (files or directories) for objective IP-hygiene candidates:
  asset-binary         bundled binary/asset file type (font, image, archive,
                       native lib, media, pdf, svg logo)
  vendored-no-license  file under a vendored dir with no sibling LICENSE/COPYING
  schema-spec          third-party-shaped schema/spec file

With no PATH, reads newline-delimited paths from stdin.

Options:
  --format text|json   output format (default: text)
  -h, --help           show this help and exit

Exit codes:
  0  no candidates found
  1  one or more candidates found (review with the five triage questions)
  2  usage or input error
EOF
}

fmt=text
paths=()
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --format) shift; fmt="${1:-}"; { [ "$fmt" = text ] || [ "$fmt" = json ]; } || { echo "ip-prefilter: bad --format" >&2; exit 2; } ;;
    --) shift; while [ $# -gt 0 ]; do paths+=("$1"); shift; done; break ;;
    -*) echo "ip-prefilter: unknown option $1" >&2; exit 2 ;;
    *) paths+=("$1") ;;
  esac
  shift
done

if [ "${#paths[@]}" -eq 0 ]; then
  while IFS= read -r line; do [ -n "$line" ] && paths+=("$line"); done
fi

files=()
for p in "${paths[@]:-}"; do
  [ -z "$p" ] && continue
  if [ -d "$p" ]; then
    while IFS= read -r f; do files+=("$f"); done < <(find "$p" -type f)
  elif [ -e "$p" ]; then
    files+=("$p")
  fi
done

asset_re='\.(ttf|otf|woff2?|eot|png|jpe?g|gif|webp|svg|ico|bmp|tiff?|mp[34]|mov|avi|webm|wav|so|dll|dylib|wasm|jar|class|exe|zip|tar|t?gz|7z|rar|pdf)$'
schema_re='(\.schema\.json|\.proto|\.xsd|\.wsdl|(^|/)openapi[^/]*\.(json|ya?ml))$'

has_license_sibling() {
  local dir; dir="$(dirname "$1")"
  while [ "$dir" != "." ] && [ "$dir" != "/" ]; do
    if ls "$dir"/LICENSE* >/dev/null 2>&1 || ls "$dir"/COPYING* >/dev/null 2>&1; then return 0; fi
    case "$dir" in */vendor|*/third_party|*/third-party|*/node_modules|*/vendored) return 1 ;; esac
    dir="$(dirname "$dir")"
  done
  return 1
}
is_vendored() {
  case "/$1/" in */vendor/*|*/third_party/*|*/third-party/*|*/node_modules/*|*/vendored/*) return 0 ;; esac
  return 1
}

hits=()  # path\tcategory\treason
for f in "${files[@]:-}"; do
  [ -z "$f" ] && continue
  low="$(printf '%s' "$f" | tr 'A-Z' 'a-z')"
  printf '%s' "$low" | grep -Eq "$asset_re"  && hits+=("$f	asset-binary	bundled asset/binary file type")
  printf '%s' "$low" | grep -Eq "$schema_re" && hits+=("$f	schema-spec	third-party-shaped schema/spec file")
  if is_vendored "$f" && ! has_license_sibling "$f"; then
    hits+=("$f	vendored-no-license	vendored path with no sibling LICENSE/COPYING")
  fi
done

if [ "$fmt" = json ]; then
  if [ "${#hits[@]}" -eq 0 ]; then printf '[]\n'; else
    printf '%s\n' "${hits[@]}" | jq -R -s 'split("\n") | map(select(length>0) | split("\t") | {path:.[0],category:.[1],reason:.[2]})'
  fi
else
  for h in "${hits[@]:-}"; do [ -n "$h" ] && printf '%s\n' "$h"; done
fi

[ "${#hits[@]}" -gt 0 ] && exit 1 || exit 0
