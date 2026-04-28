#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Sour Old Geezer contributors
# SPDX-License-Identifier: EUPL-1.2

set -euo pipefail
IFS=$'\n\t'

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
gate="${1:-"$script_dir/../../scripts/validate-oef-layout.sh"}"
fixture="$script_dir/cropped-but-failing.oef.xml"

if output="$("$gate" "$fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $fixture" >&2
  exit 1
fi

printf '%s\n' "$output" | grep -F 'AD-L10' >/dev/null
printf '%s\n' "$output" | grep -F 'view=id-view-cropped-but-failing' >/dev/null
printf '%s\n' "$output" | grep -F 'min_x=120' >/dev/null
printf '%s\n' "$output" | grep -F 'min_y=120' >/dev/null
printf '%s\n' "$output" | grep -F 'AD-L11' >/dev/null
printf '%s\n' "$output" | grep -F 'connection=id-conn-source-to-target' >/dev/null
printf '%s\n' "$output" | grep -F 'node=id-node-middle' >/dev/null

echo "render-quality gate negative fixture produced expected AD-L10 and AD-L11 findings"
