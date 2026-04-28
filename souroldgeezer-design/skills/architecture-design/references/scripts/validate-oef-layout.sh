#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Sour Old Geezer contributors
# SPDX-License-Identifier: EUPL-1.2
#
# Static render-quality gate for architecture-design OEF views. The gate checks
# source geometry before render cropping can hide layout defects.

set -euo pipefail
IFS=$'\n\t'

usage() {
  cat <<'EOF'
Usage: validate-oef-layout.sh FILE [FILE...]

Checks materialized OEF view geometry and emits Review-style AD-L findings.
Fails on any finding.

Checks:
  AD-L10  used-region origin includes nodes and bendpoints
  AD-L8   node geometry and bendpoints are on the 10-px grid
  AD-L2   same-parent node boxes do not overlap
  AD-L3   node size is large enough for baseline label readability
  AD-L11  connections do not cross unrelated node bodies
  AD-L11  connection source/target nodes still match relationship endpoints

Dependencies: xmllint, yq (Mike Farah), jq.
EOF
}

die() {
  echo "validate-oef-layout: $*" >&2
  exit 2
}

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
esac

command -v jq >/dev/null 2>&1 || die "jq not in PATH"
command -v xmllint >/dev/null 2>&1 || die "xmllint not in PATH"
command -v yq >/dev/null 2>&1 || die "yq not in PATH"

tmp_output="$(mktemp "${TMPDIR:-/tmp}/oef-layout-findings.XXXXXXXX")"
cleanup() {
  rm -f "$tmp_output"
}
trap cleanup EXIT

for file in "$@"; do
  [[ -f "$file" ]] || die "not a file: $file"
  xmllint --noout "$file"

  yq -p=xml -o=json "$file" | jq -r --arg file "$file" '
    def as_array:
      if . == null then []
      elif type == "array" then .
      else [.]
      end;

    def text_value:
      if . == null then ""
      elif type == "object" then (.["+content"] // "")
      else tostring
      end;

    def num($key): .[$key] | tonumber;

    def records_for_node($parent; $depth):
      . as $node
      | {
          id: $node."+@identifier",
          element: $node."+@elementRef",
          parent: $parent,
          depth: $depth,
          x: ($node | num("+@x")),
          y: ($node | num("+@y")),
          w: ($node | num("+@w")),
          h: ($node | num("+@h"))
        },
        (($node.node | as_array)[]? | records_for_node($node."+@identifier"; $depth + 1));

    def view_nodes($view):
      [($view.node | as_array)[]? | records_for_node(null; 0)];

    def view_connections($view):
      [
        ($view.connection | as_array)[]?
        | {
            id: ."+@identifier",
            relationship: ."+@relationshipRef",
            source: ."+@source",
            target: ."+@target",
            bendpoints: [
              (.bendpoint | as_array)[]?
              | {x: (."+@x" | tonumber), y: (."+@y" | tonumber)}
            ]
          }
      ];

    def element_records:
      [(.model.elements.element | as_array)[]? | {id: ."+@identifier", name: (.name | text_value)}];

    def relationship_records:
      [
        (.model.relationships.relationship | as_array)[]?
        | {id: ."+@identifier", source: ."+@source", target: ."+@target"}
      ];

    def element_name($elements; $id):
      (([$elements[] | select(.id == $id) | .name][0]) // "");

    def node_by_id($nodes; $id):
      (([$nodes[] | select(.id == $id)][0]) // null);

    def relationship_by_id($relationships; $id):
      (([$relationships[] | select(.id == $id)][0]) // null);

    def ancestors($nodes; $id):
      def up($parent):
        if $parent == null then []
        else [$parent] + up((node_by_id($nodes; $parent).parent))
        end;
      up((node_by_id($nodes; $id).parent));

    def center($node):
      {x: ($node.x + ($node.w / 2)), y: ($node.y + ($node.h / 2))};

    def absnum:
      if . < 0 then -. else . end;

    def attach_point($node; $toward):
      (center($node)) as $c
      | (($toward.x - $c.x) | absnum) as $dx
      | (($toward.y - $c.y) | absnum) as $dy
      | if $dx >= $dy then
          if $toward.x >= $c.x
          then {x: ($node.x + $node.w), y: $c.y}
          else {x: $node.x, y: $c.y}
          end
        else
          if $toward.y >= $c.y
          then {x: $c.x, y: ($node.y + $node.h)}
          else {x: $c.x, y: $node.y}
          end
        end;

    def route_segments($nodes; $connection):
      (node_by_id($nodes; $connection.source)) as $source_node
      | (node_by_id($nodes; $connection.target)) as $target_node
      | if $source_node == null or $target_node == null then []
        else
          ($connection.bendpoints[0]? // center($target_node)) as $source_toward
          | ($connection.bendpoints[-1]? // center($source_node)) as $target_toward
          | ([attach_point($source_node; $source_toward)] + $connection.bendpoints + [attach_point($target_node; $target_toward)]) as $points
          | [
              range(0; (($points | length) - 1)) as $i
              | {
                  x1: $points[$i].x,
                  y1: $points[$i].y,
                  x2: $points[$i + 1].x,
                  y2: $points[$i + 1].y
                }
            ]
        end;

    def rect_intersects($a; $b):
      ($a.x < ($b.x + $b.w))
      and (($a.x + $a.w) > $b.x)
      and ($a.y < ($b.y + $b.h))
      and (($a.y + $a.h) > $b.y);

    def segment_crosses_node($segment; $node):
      (
        ($segment.y1 == $segment.y2)
        and ($segment.y1 > $node.y)
        and ($segment.y1 < ($node.y + $node.h))
        and (([$segment.x1, $segment.x2] | min) < ($node.x + $node.w))
        and (([$segment.x1, $segment.x2] | max) > $node.x)
      )
      or
      (
        ($segment.x1 == $segment.x2)
        and ($segment.x1 > $node.x)
        and ($segment.x1 < ($node.x + $node.w))
        and (([$segment.y1, $segment.y2] | min) < ($node.y + $node.h))
        and (([$segment.y1, $segment.y2] | max) > $node.y)
      );

    def finding($code; $severity; $view; $connection; $node; $evidence; $action):
      "[\($code)] \($file):view=\($view) layer=static severity=\($severity)"
      + (if $connection == null then "" else " connection=\($connection)" end)
      + (if $node == null then "" else " node=\($node)" end)
      + " evidence=\($evidence) action=\($action)";

    def checks_for_view($view; $elements; $relationships):
      ($view."+@identifier") as $view_id
      | (view_nodes($view) | map(. + {label: element_name($elements; .element)})) as $nodes
      | (view_connections($view)) as $connections
      | (
          ($nodes | map(.x)) + ($connections | map(.bendpoints[]?.x))
        ) as $xs
      | (
          ($nodes | map(.y)) + ($connections | map(.bendpoints[]?.y))
        ) as $ys
      | (
          if (($xs | length) > 0 and (($xs | min) < 30 or ($xs | min) > 50 or ($ys | min) < 30 or ($ys | min) > 50))
          then [
            {
              code: "AD-L10",
              severity: "info",
              connection: null,
              node: null,
              evidence: "min_x=\($xs | min) min_y=\($ys | min)",
              action: "normalise nodes and bendpoints so used-region origin is (40,40)+/-10"
            }
          ]
          else []
          end
        )
      + [
          $nodes[] as $node
          | ([
              ["x", $node.x],
              ["y", $node.y],
              ["w", $node.w],
              ["h", $node.h]
            ])[] as $field
          | select(($field[1] % 10) != 0)
          | {
              code: "AD-L8",
              severity: "info",
              connection: null,
              node: $node.id,
              evidence: "\($field[0])=\($field[1])",
              action: "snap node geometry to 10-px grid"
            }
        ]
      + [
          $connections[] as $connection
          | $connection.bendpoints[]? as $bendpoint
          | ([
              ["x", $bendpoint.x],
              ["y", $bendpoint.y]
            ])[] as $field
          | select(($field[1] % 10) != 0)
          | {
              code: "AD-L8",
              severity: "info",
              connection: $connection.id,
              node: null,
              evidence: "bendpoint_\($field[0])=\($field[1])",
              action: "snap connection bendpoints to 10-px grid"
            }
        ]
      + [
          range(0; ($nodes | length)) as $i
          | range($i + 1; ($nodes | length)) as $j
          | $nodes[$i] as $a
          | $nodes[$j] as $b
          | select($a.parent == $b.parent and rect_intersects($a; $b))
          | {
              code: "AD-L2",
              severity: "warn",
              connection: null,
              node: $a.id,
              evidence: "overlaps=\($b.id)",
              action: "move or resize same-depth nodes until their boxes do not intersect"
            }
        ]
      + [
          $nodes[] as $node
          | (($node.label | length) * 7 + 20) as $min_label_width
          | select($node.w < 120 or $node.h < 55 or (($node.label | length) > 0 and $node.w < $min_label_width))
          | {
              code: "AD-L3",
              severity: "warn",
              connection: null,
              node: $node.id,
              evidence: "w=\($node.w) h=\($node.h) label_chars=\($node.label | length) min_label_w=\($min_label_width)",
              action: "enlarge node until default label rendering fits"
            }
        ]
      + [
          $connections[] as $connection
          | relationship_by_id($relationships; $connection.relationship) as $relationship
          | node_by_id($nodes; $connection.source) as $source_node
          | node_by_id($nodes; $connection.target) as $target_node
          | select(
              $relationship != null
              and $source_node != null
              and $target_node != null
              and ($relationship.source != $source_node.element or $relationship.target != $target_node.element)
            )
          | {
              code: "AD-L11",
              severity: "block",
              connection: $connection.id,
              node: $connection.source,
              evidence: "relationship=\($connection.relationship) expects=\($relationship.source)->\($relationship.target) connection_nodes=\($source_node.element)->\($target_node.element)",
              action: "discard stale connection endpoints and reroute against the current relationship source and target"
            }
        ]
      + [
          $connections[] as $connection
          | ([$connection.source, $connection.target] + ancestors($nodes; $connection.source) + ancestors($nodes; $connection.target)) as $exempt_nodes
          | route_segments($nodes; $connection)[] as $segment
          | $nodes[] as $node
          | select(($exempt_nodes | index($node.id) | not) and segment_crosses_node($segment; $node))
          | {
              code: "AD-L11",
              severity: "block",
              connection: $connection.id,
              node: $node.id,
              evidence: "segment=(\($segment.x1),\($segment.y1))->(\($segment.x2),\($segment.y2)) bbox=(\($node.x),\($node.y),\($node.x + $node.w),\($node.y + $node.h))",
              action: "reroute connector around unrelated node body before claiming diagram-readable"
            }
        ]
      | .[]
      | finding(.code; .severity; $view_id; .connection; .node; .evidence; .action);

    element_records as $elements
    | relationship_records as $relationships
    | (.model.views.diagrams.view | as_array)[]?
    | checks_for_view(.; $elements; $relationships)
  ' >>"$tmp_output"
done

if [[ -s "$tmp_output" ]]; then
  cat "$tmp_output"
  exit 1
fi

echo "validate-oef-layout: $# file(s) passed"
