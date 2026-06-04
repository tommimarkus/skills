#!/usr/bin/env bash
set -euo pipefail

DEDIREN_REPO_DEFAULT="tommimarkus/dediren"
DEDIREN_VERSION_DEFAULT="0.21.0"

DEDIREN_REPO="${DEDIREN_REPO:-$DEDIREN_REPO_DEFAULT}"
DEDIREN_VERSION="${DEDIREN_VERSION:-$DEDIREN_VERSION_DEFAULT}"
DEDIREN_CACHE_DIR="${DEDIREN_CACHE_DIR:-$PWD/.cache/dediren/releases}"
DEDIREN_TMP_ARCHIVE=""
DEDIREN_TMP_CHECKSUMS=""
DEDIREN_TMP_EXTRACT=""

cleanup_release_tmp() {
  if [ -n "${DEDIREN_TMP_ARCHIVE:-}" ]; then
    rm -f "$DEDIREN_TMP_ARCHIVE"
  fi
  if [ -n "${DEDIREN_TMP_CHECKSUMS:-}" ]; then
    rm -f "$DEDIREN_TMP_CHECKSUMS"
  fi
  if [ -n "${DEDIREN_TMP_EXTRACT:-}" ]; then
    rm -rf "$DEDIREN_TMP_EXTRACT"
  fi
}

usage() {
  cat <<'USAGE'
Usage:
  dediren-release.sh --ensure
  dediren-release.sh --ensure-bundle
  dediren-release.sh --print-path
  dediren-release.sh --bundle-dir
  dediren-release.sh --agent-guide
  dediren-release.sh --list-targets
  dediren-release.sh -- <dediren-args...>

Environment:
  DEDIREN_REPO       GitHub owner/repo, default tommimarkus/dediren
  DEDIREN_VERSION    Release version without leading v, default 0.21.0
  DEDIREN_CACHE_DIR  Cache directory, default .cache/dediren/releases
  JAVA_HOME/JAVACMD  Java 21+ runtime used by packaged Dediren launchers
USAGE
}

supported_targets() {
  printf '%s\n' \
    "x86_64-unknown-linux-gnu" \
    "aarch64-unknown-linux-gnu" \
    "aarch64-apple-darwin"
}

target_for_host() {
  local system machine
  system="$(uname -s | tr '[:upper:]' '[:lower:]')"
  machine="$(uname -m | tr '[:upper:]' '[:lower:]')"

  case "$system:$machine" in
    linux:x86_64|linux:amd64)
      printf '%s\n' "x86_64-unknown-linux-gnu"
      ;;
    linux:aarch64|linux:arm64)
      printf '%s\n' "aarch64-unknown-linux-gnu"
      ;;
    darwin:aarch64|darwin:arm64)
      printf '%s\n' "aarch64-apple-darwin"
      ;;
    *)
      printf 'Unsupported Dediren release target for host %s/%s\n' "$system" "$machine" >&2
      printf 'Supported targets:\n' >&2
      supported_targets >&2
      return 2
      ;;
  esac
}

release_base_url() {
  printf 'https://github.com/%s/releases/download/v%s\n' "$DEDIREN_REPO" "$DEDIREN_VERSION"
}

archive_name() {
  local target
  target="$(target_for_host)"
  printf 'dediren-agent-bundle-%s-%s.tar.gz\n' "$DEDIREN_VERSION" "$target"
}

bundle_dir() {
  local target
  target="$(target_for_host)"
  printf '%s/dediren-agent-bundle-%s-%s\n' "$DEDIREN_CACHE_DIR" "$DEDIREN_VERSION" "$target"
}

binary_path() {
  printf '%s/bin/dediren\n' "$(bundle_dir)"
}

agent_guide_path() {
  printf '%s/docs/agent-usage.md\n' "$(bundle_dir)"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$1" >&2
    return 127
  fi
}

java_command() {
  local cmd
  if [ -n "${JAVACMD:-}" ]; then
    cmd="$JAVACMD"
  elif [ -n "${JAVA_HOME:-}" ]; then
    cmd="$JAVA_HOME/bin/java"
  else
    cmd="java"
  fi

  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'Required Java 21+ runtime not found; set JAVA_HOME or JAVACMD.\n' >&2
    return 127
  fi

  printf '%s\n' "$cmd"
}

java_major_version() {
  local cmd output major
  cmd="$(java_command)"
  output="$("$cmd" -version 2>&1)"
  major="$(
    printf '%s\n' "$output" |
      awk -F'"' '/version/ {
        split($2, parts, ".")
        if (parts[1] == "1") {
          print parts[2]
        } else {
          sub(/[^0-9].*/, "", parts[1])
          print parts[1]
        }
        exit
      }'
  )"

  if [ -z "$major" ]; then
    printf 'Could not determine Java version from: %s\n' "$output" >&2
    return 1
  fi

  printf '%s\n' "$major"
}

need_java_21() {
  local major
  major="$(java_major_version)"
  if [ "$major" -lt 21 ]; then
    printf 'Dediren %s requires Java 21 or newer; detected Java %s.\n' "$DEDIREN_VERSION" "$major" >&2
    return 1
  fi
}

sha256_value() {
  local path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
    return
  fi
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
    return
  fi
  printf 'Required command not found: sha256sum or shasum\n' >&2
  return 127
}

verify_archive() {
  local archive checksum_file archive_base expected actual
  archive="$1"
  checksum_file="$2"
  archive_base="$(basename "$archive")"

  expected="$(awk -v name="$archive_base" '$2 == name {print $1}' "$checksum_file")"
  if [ -z "$expected" ]; then
    printf 'No checksum for %s in %s\n' "$archive_base" "$checksum_file" >&2
    return 1
  fi

  actual="$(sha256_value "$archive")"
  if [ "$actual" != "$expected" ]; then
    printf 'Checksum mismatch for %s\nexpected: %s\nactual:   %s\n' "$archive_base" "$expected" "$actual" >&2
    return 1
  fi
}

download_release() {
  local base archive archive_path checksum_path tmp_archive tmp_checksums tmp_extract final_dir extracted_dir
  need_cmd curl
  need_cmd tar
  need_cmd awk

  base="$(release_base_url)"
  archive="$(archive_name)"
  archive_path="$DEDIREN_CACHE_DIR/$archive"
  checksum_path="$DEDIREN_CACHE_DIR/SHA256SUMS-$DEDIREN_VERSION"
  tmp_archive="$archive_path.tmp.$$"
  tmp_checksums="$checksum_path.tmp.$$"
  tmp_extract="$DEDIREN_CACHE_DIR/.extract-$DEDIREN_VERSION-$$"
  final_dir="$(bundle_dir)"

  mkdir -p "$DEDIREN_CACHE_DIR"
  rm -rf "$tmp_extract"
  DEDIREN_TMP_ARCHIVE="$tmp_archive"
  DEDIREN_TMP_CHECKSUMS="$tmp_checksums"
  DEDIREN_TMP_EXTRACT="$tmp_extract"
  trap cleanup_release_tmp EXIT

  curl -fsSL --retry 3 --retry-delay 1 -o "$tmp_archive" "$base/$archive"
  curl -fsSL --retry 3 --retry-delay 1 -o "$tmp_checksums" "$base/SHA256SUMS"
  mv "$tmp_archive" "$archive_path"
  mv "$tmp_checksums" "$checksum_path"

  verify_archive "$archive_path" "$checksum_path"

  mkdir -p "$tmp_extract"
  tar -xzf "$archive_path" -C "$tmp_extract"
  extracted_dir="$(find "$tmp_extract" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  if [ -z "$extracted_dir" ]; then
    printf 'Archive did not contain a top-level bundle directory: %s\n' "$archive_path" >&2
    return 1
  fi

  rm -rf "$final_dir"
  mv "$extracted_dir" "$final_dir"
  rm -rf "$tmp_extract"
  DEDIREN_TMP_ARCHIVE=""
  DEDIREN_TMP_CHECKSUMS=""
  DEDIREN_TMP_EXTRACT=""
  trap - EXIT
}

ensure_bundle() {
  local bin manifest
  bin="$(binary_path)"
  manifest="$(bundle_dir)/bundle.json"

  if [ ! -x "$bin" ] || [ ! -f "$manifest" ]; then
    download_release
  fi
}

ensure_runtime() {
  ensure_bundle
  need_java_21
}

case "${1:---ensure}" in
  --help|-h)
    usage
    ;;
  --list-targets)
    supported_targets
    ;;
  --print-path)
    binary_path
    ;;
  --bundle-dir)
    bundle_dir
    ;;
  --agent-guide)
    ensure_bundle
    agent_guide_path
    ;;
  --ensure)
    ensure_runtime
    binary_path
    ;;
  --ensure-bundle)
    ensure_bundle
    bundle_dir
    ;;
  --)
    shift
    ensure_runtime
    exec "$(binary_path)" "$@"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
