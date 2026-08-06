#!/usr/bin/env bash
set -euo pipefail

DEDIREN_REPO_DEFAULT="tommimarkus/dediren"
DEDIREN_VERSION_DEFAULT="2026.07.29"
# Oldest supported release. From 2026.07.28 the render lane takes each view's
# <title>/<desc> from its own `presentation`, so each rendered view arrives labelled.
# The repo-owned post-render step now *requires* that native name rather than
# injecting one, so resolving an older bundle would produce artifacts that step
# refuses. Refuse the resolve instead, where the message can be legible. Raising
# this floor is a support decision, not a pin bump: `dediren_bump.py` moves
# DEDIREN_VERSION_DEFAULT only.
DEDIREN_VERSION_FLOOR="2026.07.28"

DEDIREN_REPO="${DEDIREN_REPO:-$DEDIREN_REPO_DEFAULT}"
DEDIREN_VERSION="${DEDIREN_VERSION:-$DEDIREN_VERSION_DEFAULT}"

calver_key() {
  # YYYY.0M.MICRO -> a zero-padded sortable integer; empty output when not CalVer.
  printf '%s\n' "$1" | awk -F. '
    NF == 3 && $1 ~ /^[0-9][0-9][0-9][0-9]$/ && $2 ~ /^[0-9][0-9]$/ && $3 ~ /^[0-9]+$/ {
      printf "%04d%02d%05d\n", $1, $2, $3
    }'
}

need_supported_version() {
  local want have
  want="$(calver_key "$DEDIREN_VERSION_FLOOR")"
  have="$(calver_key "$DEDIREN_VERSION")"
  if [ -z "$have" ]; then
    printf 'DEDIREN_VERSION must be CalVer (YYYY.0M.MICRO); got: %s\n' \
      "$DEDIREN_VERSION" >&2
    return 1
  fi
  if [ "$have" -lt "$want" ]; then
    printf 'Dediren %s is older than the supported floor %s. From %s the render itself supplies each view'"'"'s accessible name, and the post-render step refuses an artifact without one. Use %s or newer.\n' \
      "$DEDIREN_VERSION" "$DEDIREN_VERSION_FLOOR" "$DEDIREN_VERSION_FLOOR" \
      "$DEDIREN_VERSION_FLOOR" >&2
    return 1
  fi
}
# CLI-lane cache default: a location that is NOT the target repo tree, so a fallback
# resolve never writes bundle files into the user's project. Prefer the persistent
# per-user cache; fall back to a sandbox-writable temp dir when that is not writable
# (the default Bash sandbox makes $HOME read-only) so the resolve still works. The MCP
# Claude MCP lane overrides this via
# DEDIREN_CACHE_DIR=${CLAUDE_PLUGIN_DATA}/... from plugin.json. Codex MCP fields
# do not interpolate a plugin-data token, so its launcher uses this safe default.
_dediren_cache_default() {
  local base="${XDG_CACHE_HOME:-$HOME/.cache}/dediren/releases"
  # mkdir -p is a no-op success on a pre-existing read-only dir, so test an actual
  # write capability with -w (which reflects a read-only mount, e.g. a Bash sandbox).
  if mkdir -p "$base" 2>/dev/null && [ -w "$base" ]; then
    printf '%s\n' "$base"
  else
    printf '%s\n' "${TMPDIR:-/tmp}/dediren/releases"
  fi
}
DEDIREN_CACHE_DIR="${DEDIREN_CACHE_DIR:-$(_dediren_cache_default)}"
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
  dediren-release.sh -- <dediren-args...>

Environment:
  DEDIREN_REPO       GitHub owner/repo, default tommimarkus/dediren
  DEDIREN_VERSION    Release version without leading v, default 2026.07.29.
                     Must be CalVer and >= 2026.07.28, the oldest release whose
                     SVGs carry a native accessible name; older ones are refused
  DEDIREN_CACHE_DIR  Cache dir; default per-user ${XDG_CACHE_HOME:-~/.cache}/dediren/releases,
                     or ${TMPDIR:-/tmp}/dediren/releases when that is not writable (sandbox)
  JAVA_HOME/JAVACMD  Explicit Java 21+ runtime for the packaged Dediren launchers
  SDKMAN_DIR         sdkman install dir, default ~/.sdkman

Java resolution order: JAVACMD, then JAVA_HOME, then a sdkman-managed Java >=21
($SDKMAN_DIR/candidates/java/current), then `java` on PATH. sdkman is the
recommended provisioner when no Java 21+ is present: `sdk install java 21-tem`
(or any >=21 distribution). The Dediren agent bundle is a platform-independent
Java distribution; a single release archive serves every host with a Java 21+
runtime.
USAGE
}

release_base_url() {
  printf 'https://github.com/%s/releases/download/v%s\n' "$DEDIREN_REPO" "$DEDIREN_VERSION"
}

# The release's SHA256SUMS names exactly one agent bundle, extension included, so
# the compression format is read from the release rather than pinned here (upstream
# moved .tar.gz -> .tar.xz in 2026.07.27; both resolve unchanged through this path).
archive_name_from_checksums() {
  local checksum_file names count
  checksum_file="$1"
  names="$(awk -v prefix="dediren-agent-bundle-$DEDIREN_VERSION." \
    'index($2, prefix) == 1 {print $2}' "$checksum_file")"
  count="$(printf '%s' "$names" | grep -c . || true)"
  if [ "$count" != "1" ]; then
    printf 'Expected exactly one dediren-agent-bundle-%s.* entry in %s, found %s\n' \
      "$DEDIREN_VERSION" "$checksum_file" "$count" >&2
    return 1
  fi
  printf '%s\n' "$names"
}

bundle_dir() {
  printf '%s/dediren-agent-bundle-%s\n' "$DEDIREN_CACHE_DIR" "$DEDIREN_VERSION"
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

java_version_of() {
  # Major version of an explicit java command path; empty output + nonzero on failure.
  local cmd="$1" output
  output="$("$cmd" -version 2>&1)" || return 1
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
}

java_command() {
  local cmd
  if [ -n "${JAVACMD:-}" ]; then
    cmd="$JAVACMD"
  elif [ -n "${JAVA_HOME:-}" ]; then
    cmd="$JAVA_HOME/bin/java"
  else
    # No explicit override: prefer a sdkman-managed Java >=21 (sdkman is the
    # recommended provisioner — `sdk install java 21-<dist>`) over a bare PATH
    # `java`, which is often an older system JDK. Fall back to PATH `java`.
    local sdkman_java="${SDKMAN_DIR:-$HOME/.sdkman}/candidates/java/current/bin/java"
    local sdkman_major=""
    if [ -x "$sdkman_java" ]; then
      sdkman_major="$(java_version_of "$sdkman_java" 2>/dev/null || true)"
    fi
    if [ -n "$sdkman_major" ] && [ "$sdkman_major" -ge 21 ]; then
      cmd="$sdkman_java"
    else
      cmd="java"
    fi
  fi

  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf 'Required Java 21+ runtime not found; set JAVA_HOME or JAVACMD, or install one via sdkman (sdk install java 21-tem).\n' >&2
    return 127
  fi

  printf '%s\n' "$cmd"
}

java_major_version() {
  local cmd major
  cmd="$(java_command)" || return 1
  major="$(java_version_of "$cmd" 2>/dev/null || true)"
  if [ -z "$major" ]; then
    printf 'Could not determine Java version from: %s\n' "$("$cmd" -version 2>&1)" >&2
    return 1
  fi

  printf '%s\n' "$major"
}

need_java_21() {
  local major
  major="$(java_major_version)"
  if [ "$major" -lt 21 ]; then
    printf 'Dediren %s requires Java 21 or newer; detected Java %s. Install one via sdkman (sdk install java 21-tem) or set JAVA_HOME/JAVACMD.\n' "$DEDIREN_VERSION" "$major" >&2
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

download_bounded() {
  local max_time="$1" output="$2" url="$3"
  curl -fsSL --retry 3 --retry-delay 1 --connect-timeout 5 \
    --max-time "$max_time" -o "$output" "$url"
}

download_release() {
  local base archive archive_path checksum_path tmp_archive tmp_checksums tmp_extract final_dir extracted_dir
  need_cmd curl
  need_cmd tar
  need_cmd awk

  base="$(release_base_url)"
  checksum_path="$DEDIREN_CACHE_DIR/SHA256SUMS-$DEDIREN_VERSION"
  tmp_checksums="$checksum_path.tmp.$$"
  tmp_extract="$DEDIREN_CACHE_DIR/.extract-$DEDIREN_VERSION-$$"
  final_dir="$(bundle_dir)"

  mkdir -p "$DEDIREN_CACHE_DIR"
  rm -rf "$tmp_extract"
  DEDIREN_TMP_CHECKSUMS="$tmp_checksums"
  DEDIREN_TMP_EXTRACT="$tmp_extract"
  trap cleanup_release_tmp EXIT

  # Bounded: the launcher resolves on demand at session start, so an unreachable
  # or wedged peer must never hang. --connect-timeout fails a dead host fast;
  # --max-time caps each attempt so --retry cannot compound into an unbounded wait.
  # Checksums come first: they name the archive to fetch, so no format is assumed.
  download_bounded 30 "$tmp_checksums" "$base/SHA256SUMS"
  archive="$(archive_name_from_checksums "$tmp_checksums")"
  case "$archive" in
  *.tar.xz) need_cmd xz ;;
  esac
  archive_path="$DEDIREN_CACHE_DIR/$archive"
  tmp_archive="$archive_path.tmp.$$"
  DEDIREN_TMP_ARCHIVE="$tmp_archive"

  download_bounded 60 "$tmp_archive" "$base/$archive"
  mv "$tmp_archive" "$archive_path"
  mv "$tmp_checksums" "$checksum_path"

  verify_archive "$archive_path" "$checksum_path"

  mkdir -p "$tmp_extract"
  tar -xf "$archive_path" -C "$tmp_extract"
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
  local bin manifest lock_file
  bin="$(binary_path)"
  manifest="$(bundle_dir)/bundle.json"

  if [ -x "$bin" ] && [ -f "$manifest" ]; then
    return 0
  fi

  # The plugin's bundled MCP server auto-starts per session, so several sessions
  # can resolve the bundle at once against a shared DEDIREN_CACHE_DIR. Serialize
  # the extract/install (download_release's rm -rf + mv) so a concurrent resolver
  # cannot observe or clobber a half-installed bundle. flock is best-effort: where
  # it is unavailable, fall back to the bare download (prior behavior).
  mkdir -p "$DEDIREN_CACHE_DIR"
  if command -v flock >/dev/null 2>&1; then
    lock_file="$DEDIREN_CACHE_DIR/.dediren-$DEDIREN_VERSION.lock"
    exec 9>"$lock_file"
    # Bounded wait: the launcher resolves on demand at session start, so a peer
    # holding the lock (a concurrent download) must not hang us indefinitely.
    # On timeout, proceed best-effort — the re-check below, then download_release's
    # own atomic tmp+mv, keep a lost race from corrupting the install.
    if ! flock -w 60 9; then
      printf 'dediren-release: timed out waiting for the install lock; proceeding best-effort.\n' >&2
    fi
    # Re-check under the lock: another resolver may have finished while we waited.
    if [ -x "$bin" ] && [ -f "$manifest" ]; then
      return 0
    fi
  fi
  download_release
}

ensure_runtime() {
  ensure_bundle
  need_java_21
}

if [ "${1:-}" != "--help" ] && [ "${1:-}" != "-h" ]; then
  need_supported_version
fi

case "${1:---ensure}" in
  --help|-h)
    usage
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
