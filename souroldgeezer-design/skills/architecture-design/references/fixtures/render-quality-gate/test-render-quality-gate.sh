#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Sour Old Geezer contributors
# SPDX-License-Identifier: EUPL-1.2

set -euo pipefail
IFS=$'\n\t'

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
gate="${1:-"$script_dir/../../scripts/validate-oef-layout.sh"}"

require_finding() {
  local fixture="$1"
  local output="$2"
  local expected="$3"

  printf '%s\n' "$output" | grep -F "$expected" >/dev/null || {
    echo "missing expected finding fragment for $fixture: $expected" >&2
    printf '%s\n' "$output" >&2
    exit 1
  }
}

cropped_fixture="$script_dir/cropped-but-failing.oef.xml"
if cropped_output="$("$gate" "$cropped_fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $cropped_fixture" >&2
  exit 1
fi

require_finding "$cropped_fixture" "$cropped_output" 'AD-L10'
require_finding "$cropped_fixture" "$cropped_output" 'view=id-view-cropped-but-failing'
require_finding "$cropped_fixture" "$cropped_output" 'min_x=120'
require_finding "$cropped_fixture" "$cropped_output" 'min_y=120'
require_finding "$cropped_fixture" "$cropped_output" 'AD-L11'
require_finding "$cropped_fixture" "$cropped_output" 'connection=id-conn-source-to-target'
require_finding "$cropped_fixture" "$cropped_output" 'node=id-node-middle'

bendpoint_fixture="$script_dir/bendpoint-origin-drift.oef.xml"
if bendpoint_output="$("$gate" "$bendpoint_fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $bendpoint_fixture" >&2
  exit 1
fi

require_finding "$bendpoint_fixture" "$bendpoint_output" 'AD-L10'
require_finding "$bendpoint_fixture" "$bendpoint_output" 'view=id-view-bendpoint-origin-drift'
require_finding "$bendpoint_fixture" "$bendpoint_output" 'min_x=80'
require_finding "$bendpoint_fixture" "$bendpoint_output" 'min_y=80'

stacked_fixture="$script_dir/stacked-connector-lane.oef.xml"
if stacked_output="$("$gate" "$stacked_fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $stacked_fixture" >&2
  exit 1
fi

require_finding "$stacked_fixture" "$stacked_output" 'AD-L13'
require_finding "$stacked_fixture" "$stacked_output" 'view=id-view-stacked-connector-lane'
require_finding "$stacked_fixture" "$stacked_output" 'connection=id-conn-source-a-to-target'
require_finding "$stacked_fixture" "$stacked_output" 'node=id-node-target'

fanout_fixture="$script_dir/fanout-crisscross.oef.xml"
if fanout_output="$("$gate" "$fanout_fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $fanout_fixture" >&2
  exit 1
fi

require_finding "$fanout_fixture" "$fanout_output" 'AD-L15'
require_finding "$fanout_fixture" "$fanout_output" 'view=id-view-fanout-crisscross'
require_finding "$fanout_fixture" "$fanout_output" 'connection=id-conn-source-to-top'
require_finding "$fanout_fixture" "$fanout_output" 'node=id-node-source'

endpoint_fixture="$script_dir/endpoint-bendpoint-inside.oef.xml"
if endpoint_output="$("$gate" "$endpoint_fixture" 2>&1)"; then
  echo "expected render-quality gate to fail for $endpoint_fixture" >&2
  exit 1
fi

require_finding "$endpoint_fixture" "$endpoint_output" 'AD-L11'
require_finding "$endpoint_fixture" "$endpoint_output" 'view=id-view-endpoint-bendpoint-inside'
require_finding "$endpoint_fixture" "$endpoint_output" 'connection=id-conn-operator-approve'
require_finding "$endpoint_fixture" "$endpoint_output" 'node=id-node-approve'
require_finding "$endpoint_fixture" "$endpoint_output" 'bendpoint=(450,70)'

echo "render-quality gate negative fixtures produced expected AD-L10, AD-L11, AD-L13, and AD-L15 findings"
