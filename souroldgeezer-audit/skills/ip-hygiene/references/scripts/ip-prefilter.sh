#!/usr/bin/env bash
# ip-prefilter.sh — objective IP-hygiene pre-filter for the ip-hygiene skill.
# READ-ONLY scanner. It identifies filesystem facts that merit IP review; it
# never decides ownership, permission, infringement, similarity, or licence
# compatibility. Empty output is not legal assurance.
set -euo pipefail

usage() {
  cat <<'EOF'
usage: ip-prefilter.sh [--format text|json] [--base REF] [--] [PATH ...]

Scans files or directories for objective IP-hygiene candidates. With no PATH,
reads NUL-delimited paths from standard input. Paths are sorted and deduplicated
before scanning; repository metadata (.git, .hg, .svn) is excluded.

Candidate categories:
  asset-binary          bundled binary/asset file type
  schema-spec           schema or specification file type
  vendored-no-license   vendored component without LICENSE/COPYING/NOTICE evidence
  vendored-component    vendored component with LICENSE/COPYING/NOTICE evidence
  symlink               symbolic link (target/provenance needs review)
  source-notice         source licence/copyright marker
  source-spdx           SPDX-License-Identifier line
  source-authorship     @author / @copyright / @license doc tag
  source-attribution    provenance language or snippet-host URL in a comment
  source-licence-block  multi-line licence text in a non-vendored source file
  source-generated      generated-file banner in the file header
  notice-loss           marker present in --base REF and absent in the worktree

Every category is a filesystem candidate for human review, never a legal
conclusion: the scanner does not decide ownership, permission, infringement,
similarity, or licence compatibility, and empty output is not legal assurance.
Presence of a licence or NOTICE is evidence only and does not suppress the
component candidate.

With --base REF, each scanned file's copyright/SPDX/licence markers in REF are
compared with the worktree copy (read-only `git show`), and notice-loss reports
any marker REF carried that the worktree copy no longer has. When git is
unavailable, a path lies outside a repository, REF does not resolve, or the file
does not exist in REF, that comparison is skipped with a warning on standard
error and the static scan continues; a skipped comparison is never evidence that
a notice survived.

Output is stable. Text output is one tab-separated record per candidate; control
characters in fields are escaped. JSON output is an array of path/category/reason
objects.

Exit codes:
  0  no candidates found
  1  one or more candidates found
  2  usage or input error
EOF
}

fail_input() { printf 'ip-prefilter: %s\n' "$1" >&2; exit 2; }

fmt=text
base_ref=
paths=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --format)
      shift
      fmt="${1:-}"
      [ "$fmt" = text ] || [ "$fmt" = json ] || fail_input 'bad --format'
      ;;
    --base)
      shift
      base_ref="${1:-}"
      [ -n "$base_ref" ] || fail_input 'missing REF for --base'
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
warned="$tmpdir/warned"
: > "$files"
: > "$records"
: > "$warned"

warn_once() {
  grep -qxF -- "$1" "$warned" 2>/dev/null && return 0
  printf '%s\n' "$1" >> "$warned"
  printf 'ip-prefilter: %s\n' "$2" >&2
}

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
# Source, configuration, and build files: the repo-wide reach the source-code
# lane needs, including infrastructure, build, and CI descriptors.
source_re='\.(c|cc|cpp|cxx|h|hh|hpp|java|js|mjs|cjs|ts|tsx|jsx|py|rb|go|rs|sh|bash|zsh|ps1|psm1|psd1|cs|php|swift|kt|kts|scala|sql|html?|css|scss|sass|less|vue|svelte|astro|tf|tfvars|hcl|bicep|bicepparam|gradle|groovy|sbt|lua|dart|fs|fsx|fsi|vb|vbs|jl|pl|pm|ex|exs|erl|hrl|clj|cljs|cljc|elm|nim|zig|pas|asm|m|mm|toml|ini|cfg|conf|properties|cmake|mk|nix|tcl|awk|bat|cmd|xml|ya?ml)$'
# Well-known extensionless (or fixed-name) build/CI descriptors.
basename_re='^(makefile|gnumakefile|dockerfile|containerfile|jenkinsfile|vagrantfile|rakefile|gemfile|brewfile|justfile|procfile|cmakelists\.txt|meson\.build|(makefile|dockerfile)\..+)$'

# Content patterns. Each is deliberately narrow: a category that fires on most
# files is noise, not a candidate signal.
# Unambiguous comment openers may sit anywhere on the line; the ambiguous ones
# (block-comment continuation, SQL/Lua, Lisp/asm, TeX) only at line start.
comment_lead='((#|//|/\*|<!--|"""|'"'''"')|^[[:space:]]*(\*|--|;|%))'
# Word-guarded copy verbs only. Measured against real third-party source:
# "derived from" and "lifted from" are ordinary technical prose, bare "source:"
# and bare "based on" likewise (the latter fired on 12% of scanned files), so
# "source:" and "based on" count only when a locator follows on the same line.
attr_phrase='((adapted|copied|taken|ported)[[:space:]]+from|originally[[:space:]]+from|based[[:space:]]+(up)?on.*(https?://|www\.)|source[[:space:]]*:[[:space:]]*["'"'"'<(]?(https?://|www\.|[a-z0-9_.~+-]+/))'
# The optional middle must end on a non-word character, so a phrase is never
# matched inside a longer word (an "imported" never reads as a copy verb).
attr_re="${comment_lead}(.*[^[:alnum:]_])?${attr_phrase}"
# Snippet, paste, Q&A, and blog hosts only. Repository and package-registry
# links measured as citation noise (9% of scanned files); a repository snippet
# that was really pasted in is caught by the copy verbs above instead.
attr_host='(gist\.github\.com|stackoverflow\.com|stackexchange\.com|serverfault\.com|superuser\.com|askubuntu\.com|pastebin\.com|paste\.[a-z]+|codepen\.io|jsfiddle\.net|codesandbox\.io|replit\.com|rosettacode\.org|geeksforgeeks\.org|w3schools\.com|tutorialspoint\.com|medium\.com|dev\.to|blogspot\.com|wordpress\.com|reddit\.com)'
attr_url_re="${comment_lead}.*https?://[^/[:space:]]*${attr_host}"
licence_block_re='permission is hereby granted|without warranty of any kind|redistribution and use in source|the above copyright notice|subject to the following conditions|in no event shall|merchantability and (a )?fitness|apache license, version|(general|lesser) public license|mozilla public license|this program is free software|licensed under the (apache|mit|bsd|gnu|eclipse|mozilla)|all rights reserved|provided "as is"'
generated_re="${comment_lead}.*(do not edit|@generated|auto-?generated|automatically generated|code generated by|generated by [^[:space:]])"
authorship_re='(^|[^[:alnum:]_])@(author|copyright|licen[cs]e)([^[:alnum:]_]|$)'
notice_marker_re='spdx-license-identifier|licensed under|copyright'

is_source() {
  if printf '%s' "$1" | grep -Eq "$source_re"; then return 0; fi
  if printf '%s' "${1##*/}" | grep -Eq "$basename_re"; then return 0; fi
  return 1
}

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

# --- base (diff-aware) lane -------------------------------------------------
# State is cached per directory so a directory walk costs one probe per tree.
base_enabled=0
base_dir=
base_state=
if [ -n "$base_ref" ]; then
  if command -v git >/dev/null 2>&1; then
    base_enabled=1
  else
    warn_once 'nogit' "git not available; --base $base_ref comparison skipped for all inputs"
  fi
fi

markers_of() {
  grep -Ioh -E -i "$notice_marker_re" "$1" 2>/dev/null \
    | tr '[:upper:]' '[:lower:]' | LC_ALL=C sort -u || true
}

base_lane_state() {
  local dir="$1"
  if [ "$dir" = "$base_dir" ] && [ -n "$base_state" ]; then
    printf '%s' "$base_state"
    return
  fi
  base_dir="$dir"
  if ! git -C "$dir" rev-parse --show-toplevel >/dev/null 2>&1; then
    base_state=norepo
  elif ! git -C "$dir" rev-parse --verify --quiet "${base_ref}^{object}" >/dev/null 2>&1; then
    base_state=badref
  else
    base_state=ok
  fi
  printf '%s' "$base_state"
}

check_notice_loss() {
  local file="$1" dir name state lost
  dir="$(dirname "$file")"
  name="${file##*/}"
  state="$(base_lane_state "$dir")"
  case "$state" in
    norepo)
      warn_once "norepo:$dir" "$dir is not a git repository; --base comparison skipped there"
      return ;;
    badref)
      warn_once "badref:$dir" "ref '$base_ref' does not resolve in $dir; --base comparison skipped there"
      return ;;
  esac
  if ! git -C "$dir" show "${base_ref}:./${name}" > "$tmpdir/base.blob" 2>/dev/null; then
    warn_once "absent:$file" "$file does not exist in '$base_ref'; --base comparison skipped for it"
    return
  fi
  markers_of "$tmpdir/base.blob" > "$tmpdir/base.markers"
  markers_of "$file" > "$tmpdir/now.markers"
  lost="$(comm -23 "$tmpdir/base.markers" "$tmpdir/now.markers" \
    | grep -v '^$' | tr '\n' ',' | sed 's/,$//; s/,/, /g' || true)"
  [ -n "$lost" ] && add_record "$file" notice-loss "present in $base_ref, absent now: $lost"
  return 0
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
  if is_source "$low"; then
    if grep -I -Eiq 'copyright|spdx-license-identifier|licensed under' "$file"; then
      add_record "$file" source-notice 'source licence/copyright marker'
    fi
    if grep -I -q -i 'spdx-license-identifier' "$file"; then
      add_record "$file" source-spdx 'SPDX-License-Identifier line'
    fi
    if grep -I -Eq "$authorship_re" "$file"; then
      add_record "$file" source-authorship '@author / @copyright / @license doc tag'
    fi
    if grep -I -Eiq "$attr_re" "$file"; then
      add_record "$file" source-attribution 'provenance language in a comment'
    elif grep -I -Eiq "$attr_url_re" "$file"; then
      add_record "$file" source-attribution 'snippet, paste, Q&A, or blog URL in a comment'
    fi
    if ! is_vendored "$file"; then
      distinct="$(grep -I -oh -E -i "$licence_block_re" "$file" 2>/dev/null \
        | tr '[:upper:]' '[:lower:]' | LC_ALL=C sort -u | grep -c . || true)"
      if [ "${distinct:-0}" -ge 2 ]; then
        add_record "$file" source-licence-block 'multi-line licence text in a non-vendored source file'
      fi
    fi
    if grep -I -Eiq "$generated_re" <(head -n 40 "$file" 2>/dev/null); then
      add_record "$file" source-generated 'generated-file banner in the file header'
    fi
  fi
  if [ "$base_enabled" -eq 1 ]; then
    check_notice_loss "$file"
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
