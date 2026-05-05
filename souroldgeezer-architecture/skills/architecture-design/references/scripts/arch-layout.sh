#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
references_dir="$(cd -- "$script_dir/.." && pwd)"
jar_path="$references_dir/bin/arch-layout.jar"

if ! command -v java >/dev/null 2>&1; then
  echo "arch-layout requires Java 21 or newer, but java was not found on PATH." >&2
  exit 127
fi

java_version="$(java -version 2>&1 | awk -F '"' '/version/ { print $2; exit }')"
java_major="${java_version%%.*}"
if [[ "$java_major" == "1" ]]; then
  java_major="$(printf '%s' "$java_version" | awk -F. '{ print $2 }')"
fi

if [[ -z "$java_major" || "$java_major" -lt 21 ]]; then
  echo "arch-layout requires Java 21 or newer; found ${java_version:-unknown}." >&2
  exit 2
fi

if [[ ! -f "$jar_path" ]]; then
  echo "arch-layout runtime jar is missing at $jar_path." >&2
  echo "Run: bash $script_dir/package-arch-layout.sh" >&2
  exit 2
fi

export ARCH_LAYOUT_REFERENCES="$references_dir"
java -XX:+PerfDisableSharedMem -jar "$jar_path" "$@"
