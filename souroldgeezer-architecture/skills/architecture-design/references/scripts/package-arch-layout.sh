#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
references_dir="$(cd -- "$script_dir/.." && pwd)"
repo_root="$(cd -- "$script_dir/../../../../.." && pwd)"
project_dir="$repo_root/tools/architecture-layout-java"
jar_source="$project_dir/build/libs/arch-layout.jar"
jar_target="$references_dir/bin/arch-layout.jar"

sdkman_init="${SDKMAN_DIR:-$HOME/.sdkman}/bin/sdkman-init.sh"
if [[ -s "$sdkman_init" ]]; then
  # shellcheck source=/dev/null
  set +u
  source "$sdkman_init"
  (cd "$project_dir" && sdk env >/dev/null)
  set -u
fi

if [[ ! -x "$project_dir/gradlew" ]]; then
  echo "Gradle wrapper missing or not executable at $project_dir/gradlew." >&2
  exit 2
fi

"$project_dir/gradlew" -p "$project_dir" clean test runtimeJar

mkdir -p "$references_dir/bin"
cp "$jar_source" "$jar_target"

for forbidden in "*.java" "src/main" "src/test" "build.gradle.kts" "settings.gradle.kts" ".gradle" "build" ".mvn" "pom.xml"; do
  if find "$references_dir/bin" -path "$references_dir/bin/$forbidden" -print -quit | grep -q .; then
    echo "Forbidden development artifact found in runtime package: $forbidden" >&2
    exit 3
  fi
done

echo "Architecture layout package evidence"
echo "included: $jar_target"
echo "launcher: $references_dir/scripts/arch-layout.sh"
echo "excluded: Java source, Gradle build files, build output, dependency caches, Maven files"
echo "runtime listing:"
find "$references_dir/bin" -maxdepth 1 -type f -printf '  %f %s bytes\n' | sort
