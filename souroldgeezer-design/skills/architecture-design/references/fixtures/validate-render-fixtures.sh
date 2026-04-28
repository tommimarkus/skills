#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Sour Old Geezer contributors
# SPDX-License-Identifier: EUPL-1.2
#
# Validate every materialized architecture-design OEF fixture by checking view
# geometry and rendering each view through a caller-provided Archi render script.

set -euo pipefail
IFS=$'\n\t'

usage() {
  cat <<'EOF'
Usage: validate-render-fixtures.sh [OPTIONS]

Validate every *.oef.xml fixture in this directory:
  1. XML is well formed.
  2. Identifier attributes are unique across the OEF file.
  3. Every view has materialized Element nodes with x/y/w/h geometry.
  4. Every view has Relationship connections with source/target endpoints.
  5. Rendering produces nonblank PNGs larger than Archi's 100x100 empty-view
     placeholder.
  6. The fixture set covers all seven architecture-design supported viewpoints.

Options:
  --render-script PATH       Path to an archi-render.sh-compatible script.
                             Defaults to ARCHI_RENDER_SCRIPT.
  --render-archi-bin PATH    Forwarded to archi-render.sh --archi-bin.
                             Defaults to ARCHI_RENDER_FIXTURE_ARCHI_BIN.
  --render-cache-root DIR    Forwarded to archi-render.sh --cache-root.
                             Defaults to a temporary directory.
  --render-config FILE       Forwarded to archi-render.sh --config.
                             Defaults to ARCHI_RENDER_FIXTURE_CONFIG.
  --render-output-root DIR   Forwarded to archi-render.sh --output-root.
                             Defaults to a temporary directory.
  --keep-render-work         Keep default temporary render cache/output roots.
  -h, --help                 Show this help.

Environment:
  ARCHI_RENDER_SCRIPT                  Render script path.
  ARCHI_RENDER_FIXTURE_ARCHI_BIN       Archi binary path for fixture renders.
  ARCHI_RENDER_FIXTURE_CACHE_ROOT      Render cache root for fixture renders.
  ARCHI_RENDER_FIXTURE_CONFIG          archi-render.sh config file.
  ARCHI_RENDER_FIXTURE_OUTPUT_ROOT     Rendered PNG output root.
EOF
}

die() {
  echo "validate-render-fixtures: $*" >&2
  exit 1
}

render_script="${ARCHI_RENDER_SCRIPT:-}"
render_archi_bin="${ARCHI_RENDER_FIXTURE_ARCHI_BIN:-}"
render_cache_root="${ARCHI_RENDER_FIXTURE_CACHE_ROOT:-}"
render_config="${ARCHI_RENDER_FIXTURE_CONFIG:-}"
render_output_root="${ARCHI_RENDER_FIXTURE_OUTPUT_ROOT:-}"
keep_render_work=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --render-script)
      [[ $# -ge 2 ]] || die "--render-script requires a path"
      render_script="$2"
      shift 2
      ;;
    --render-archi-bin)
      [[ $# -ge 2 ]] || die "--render-archi-bin requires a path"
      render_archi_bin="$2"
      shift 2
      ;;
    --render-cache-root)
      [[ $# -ge 2 ]] || die "--render-cache-root requires a directory"
      render_cache_root="$2"
      shift 2
      ;;
    --render-config)
      [[ $# -ge 2 ]] || die "--render-config requires a file"
      render_config="$2"
      shift 2
      ;;
    --render-output-root)
      [[ $# -ge 2 ]] || die "--render-output-root requires a directory"
      render_output_root="$2"
      shift 2
      ;;
    --keep-render-work)
      keep_render_work=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$render_script" ]] || die "set ARCHI_RENDER_SCRIPT or pass --render-script"
[[ -x "$render_script" ]] || die "render script is not executable: $render_script"

command -v identify >/dev/null 2>&1 || die "identify not in PATH (ImageMagick required)"
command -v jq       >/dev/null 2>&1 || die "jq not in PATH"
command -v mktemp   >/dev/null 2>&1 || die "mktemp not in PATH"
command -v xmllint  >/dev/null 2>&1 || die "xmllint not in PATH"
command -v yq       >/dev/null 2>&1 || die "yq not in PATH"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

tmp_root=""
if [[ -z "$render_cache_root" || -z "$render_output_root" ]]; then
  tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/archi-fixture-renders.XXXXXXXX")"
  [[ -n "$render_cache_root" ]] || render_cache_root="$tmp_root/cache"
  [[ -n "$render_output_root" ]] || render_output_root="$tmp_root/views"
fi

cleanup() {
  if [[ "$keep_render_work" = 0 && -n "$tmp_root" ]]; then
    rm -rf "$tmp_root"
  fi
}
trap cleanup EXIT

mapfile -t fixtures < <(find "$script_dir" -maxdepth 1 -name '*.oef.xml' -type f -print | sort)
(( ${#fixtures[@]} > 0 )) || die "no *.oef.xml fixtures found in $script_dir"

supported_viewpoints=(
  "Application Cooperation"
  "Business Process Cooperation"
  "Capability Map"
  "Migration"
  "Motivation"
  "Service Realization"
  "Technology Usage"
)
declare -A seen_viewpoints=()

check_geometry() {
  local fixture="$1"

  yq -p=xml -o=json "$fixture" | jq -e '
    def as_array:
      if . == null then []
      elif type == "array" then .
      else [.]
      end;

    def element_nodes($view):
      [
        $view
        | ..
        | objects
        | select(."+@xsi:type"? == "Element" and has("+@elementRef"))
      ];

    def relationship_connections($view):
      [
        $view
        | ..
        | objects
        | select(."+@xsi:type"? == "Relationship" and has("+@relationshipRef"))
      ];

    (.model.views.diagrams.view | as_array) as $views
    | ($views | length) > 0
      and all($views[]; (element_nodes(.) | length) > 0)
      and all($views[];
        all(element_nodes(.)[];
          has("+@x") and has("+@y") and has("+@w") and has("+@h")
        )
      )
      and all($views[]; (relationship_connections(.) | length) > 0)
      and all($views[];
        all(relationship_connections(.)[];
          has("+@source") and has("+@target")
        )
      )
  ' >/dev/null
}

check_unique_identifiers() {
  local fixture="$1"

  yq -p=xml -o=json "$fixture" | jq -e '
    [
      ..
      | objects
      | .["+@identifier"]?
      | select(. != null)
    ] as $ids
    | ($ids | length) == ($ids | unique | length)
  ' >/dev/null
}

check_png() {
  local png="$1"
  local dims width height

  [[ -f "$png" ]] || die "render output is not a file: $png"
  dims="$(identify -format '%w:%h' "$png")" || die "identify failed for $png"
  width="${dims%%:*}"
  height="${dims##*:}"

  [[ "$width" =~ ^[0-9]+$ && "$height" =~ ^[0-9]+$ ]] || die "invalid PNG dimensions for $png: $dims"
  (( width > 100 && height > 100 )) || die "blank or placeholder render for $png: ${width}x${height}"
}

record_viewpoints() {
  local fixture="$1"
  local viewpoint

  while IFS= read -r viewpoint; do
    [[ -n "$viewpoint" ]] && seen_viewpoints["$viewpoint"]=1
  done < <(
    yq -p=xml -o=json "$fixture" | jq -r '
      def as_array:
        if . == null then []
        elif type == "array" then .
        else [.]
        end;

      .model.views.diagrams.view
      | as_array
      | .[]
      | .["+@viewpoint"] // empty
    '
  )
}

for fixture in "${fixtures[@]}"; do
  echo "validate-render-fixtures: checking $(basename "$fixture")"
  xmllint --noout "$fixture"
  check_unique_identifiers "$fixture" || die "duplicate identifier attribute in $fixture"
  check_geometry "$fixture" || die "missing materialized view geometry in $fixture"
  record_viewpoints "$fixture"

  render_args=(--quiet --cache-root "$render_cache_root" --output-root "$render_output_root")
  [[ -n "$render_archi_bin" ]] && render_args+=(--archi-bin "$render_archi_bin")
  [[ -n "$render_config" ]] && render_args+=(--config "$render_config")

  mapfile -t pngs < <("$render_script" "${render_args[@]}" "$fixture")
  (( ${#pngs[@]} > 0 )) || die "render script produced no PNG paths for $fixture"
  for png in "${pngs[@]}"; do
    check_png "$png"
  done
done

missing_viewpoints=()
for viewpoint in "${supported_viewpoints[@]}"; do
  [[ -n "${seen_viewpoints[$viewpoint]+set}" ]] || missing_viewpoints+=("$viewpoint")
done

if (( ${#missing_viewpoints[@]} > 0 )); then
  printf 'validate-render-fixtures: missing supported viewpoint fixture coverage:\n' >&2
  printf '  - %s\n' "${missing_viewpoints[@]}" >&2
  exit 1
fi

echo "validate-render-fixtures: ${#fixtures[@]} fixture diagram(s) passed"
