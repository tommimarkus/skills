#!/usr/bin/env bash
# ip-prefilter.sh — objective IP-hygiene pre-filter for the ip-hygiene skill.
# READ-ONLY scanner. It identifies filesystem facts that merit IP review; it
# never decides ownership, permission, infringement, similarity, or licence
# compatibility. Empty output is not legal assurance.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ip-prefilter.sh [--format text|json] [--] [PATH ...]

Scans files or directories for objective IP-hygiene candidates. With no PATH,
reads NUL-delimited paths from standard input. Paths are sorted and deduplicated
before scanning; repository metadata (.git, .hg, .svn) is excluded.

Candidate categories:
  asset-binary         bundled binary/asset file type
  schema-spec          schema or specification file type
  vendored-no-license  vendored component without LICENSE/COPYING/NOTICE evidence
  vendored-component   vendored component with LICENSE/COPYING/NOTICE evidence
  symlink              symbolic link (target/provenance needs review)
  source-notice        source licence/copyright marker

Output is stable. Text output is one tab-separated record per candidate; control
characters in fields are escaped. JSON output is an array of path/category/reason
objects. Presence of a licence or NOTICE is evidence only and does not suppress
the component candidate.

Exit codes:
  0  no candidates found
  1  one or more candidates found
  2  usage or input error
EOF
}

fail_input() { printf 'ip-prefilter: %s\n' "$1" >&2; exit 2; }

fmt=text
paths=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --format)
      shift
      fmt="${1:-}"
      [ "$fmt" = text ] || [ "$fmt" = json ] || fail_input 'bad --format'
      ;;
    --) shift; paths+=("$@"); break ;;
    -*) fail_input "unknown option $1" ;;
    *) paths+=("$1") ;;
  esac
  shift
done

if [ "${#paths[@]}" -eq 0 ]; then
  while IFS= read -r -d '' path || [ -n "${path:-}" ]; do
    [ -n "$path" ] && paths+=("$path")
  done
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/ip-prefilter.XXXXXX")"
trap 'rm -rf "$tmpdir"' EXIT HUP INT TERM
files="$tmpdir/files"
records="$tmpdir/records"
: > "$files"
: > "$records"

is_metadata() {
  case "/$1/" in */.git/*|*/.hg/*|*/.svn/*) return 0 ;; esac
  return 1
}

for path in "${paths[@]}"; do
  if [ -L "$path" ]; then
    is_metadata "$path" || printf '%s\0' "$path" >> "$files"
  elif [ -f "$path" ]; then
    is_metadata "$path" || printf '%s\0' "$path" >> "$files"
  elif [ -d "$path" ]; then
    find -P "$path" \
      \( -type d \( -name .git -o -name .hg -o -name .svn \) -prune \) -o \
      \( -type f -o -type l \) -print0 >> "$files"
  else
    fail_input "missing path: $path"
  fi
done

LC_ALL=C sort -z -u "$files" -o "$files"

asset_re='\.(ttf|otf|woff2?|eot|png|jpe?g|gif|webp|svg|ico|bmp|tiff?|mp[34]|mov|avi|webm|wav|so|dll|dylib|wasm|jar|class|exe|zip|tar|t?gz|7z|rar|pdf)$'
schema_re='(\.schema\.json|\.proto|\.xsd|\.wsdl|(^|/)openapi[^/]*\.(json|ya?ml))$'
source_re='\.(c|cc|cpp|cxx|h|hh|hpp|java|js|mjs|cjs|ts|tsx|jsx|py|rb|go|rs|sh|bash|zsh|ps1|cs|php|swift|kt|kts|scala|sql|html?|css|scss|vue)$'

is_vendored() {
  case "/$1/" in */vendor/*|*/third_party/*|*/third-party/*|*/node_modules/*|*/vendored/*) return 0 ;; esac
  return 1
}

vendor_evidence() {
  local dir="$1"
  while [ "$dir" != / ] && [ "$dir" != . ]; do
    if find "$dir" -maxdepth 1 -type f \( -iname 'license*' -o -iname 'copying*' -o -iname 'notice*' \) -print -quit | grep -q .; then
      printf 'LICENSE/COPYING/NOTICE present'
      return
    fi
    case "$dir" in */vendor|*/third_party|*/third-party|*/node_modules|*/vendored) break ;; esac
    dir="$(dirname "$dir")"
  done
  printf 'no sibling LICENSE/COPYING/NOTICE found'
}

add_record() { printf '%s\0%s\0%s\0' "$1" "$2" "$3" >> "$records"; }

while IFS= read -r -d '' file; do
  if [ -L "$file" ]; then
    add_record "$file" symlink 'symbolic link; inspect target and provenance'
    continue
  fi
  low="$(printf '%s' "$file" | tr '[:upper:]' '[:lower:]')"
  printf '%s' "$low" | grep -Eq "$asset_re" && add_record "$file" asset-binary 'bundled asset/binary file type'
  printf '%s' "$low" | grep -Eq "$schema_re" && add_record "$file" schema-spec 'schema/specification file type'
  if is_vendored "$file"; then
    evidence="$(vendor_evidence "$(dirname "$file")")"
    if [ "$evidence" = 'LICENSE/COPYING/NOTICE present' ]; then
      add_record "$file" vendored-component "vendored component; $evidence"
    else
      add_record "$file" vendored-no-license "vendored component; $evidence"
    fi
  fi
  if printf '%s' "$low" | grep -Eq "$source_re" && grep -I -Eiq 'copyright|spdx-license-identifier|licensed under' "$file"; then
    add_record "$file" source-notice 'source licence/copyright marker'
  fi
done < "$files"

if [ ! -s "$records" ]; then
  [ "$fmt" = json ] && printf '[]\n'
  exit 0
fi

if [ "$fmt" = json ]; then
  jq -Rs '
    split("\u0000") as $fields |
    [range(0; ($fields | length) - 1; 3) |
      {path: $fields[.], category: $fields[. + 1], reason: $fields[. + 2]}]
  ' "$records"
else
  jq -Rrs '
    split("\u0000") as $fields |
    [range(0; ($fields | length) - 1; 3) |
      [$fields[.], $fields[. + 1], $fields[. + 2]]] |
    .[] | @tsv
  ' "$records"
fi
exit 1
