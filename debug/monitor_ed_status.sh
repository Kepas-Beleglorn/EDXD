#!/usr/bin/env bash
# monitor_ed_status.sh
# Watches Elite Dangerous Status.json and prints a compact, colorized line on every update.
# - Truecolor (RGB) ANSI sequences are used for all colors.
# - Uses inotifywait when available, otherwise falls back to polling.
#
# Usage:
#   ./monitor_ed_status.sh [-d DIR] [-f FILE] [-p SECS] [--no-color] [-h]
#     -d DIR       Directory containing Status.json
#     -f FILE      Filename (default: Status.json)
#     -p SECS      Poll interval when inotify is unavailable (default: 1)
#     --no-color   Disable colors
#     -h           Help
#
# Example:
#   ./monitor_ed_status.sh -d "/home/kepas/EDData/EDGameData/Saved Games/Frontier Developments/Elite Dangerous"

set -Eeuo pipefail

# ------------ defaults (tweak to your setup) ------------
DIR="${DIR_OVERRIDE:-/mnt/games/ED/journals/Frontier Developments/Elite Dangerous/}"
STATUS_FILE="Status.json"
POLL_SECS=1

# ------------ CLI ------------
usage() {
  cat <<USAGE
Usage: $(basename "$0") [-d DIR] [-f FILE] [-p SECS] [--no-color] [-h]
  -d DIR       Directory containing Status.json (default: current preset in script)
  -f FILE      File name to watch (default: Status.json)
  -p SECS      Poll interval when inotify is unavailable (default: 1)
  --no-color   Disable colors
  -h           Show this help and exit
USAGE
}

NO_COLOR_MODE=0
while (( $# )); do
  case "$1" in
    -d) DIR="$2"; shift 2 ;;
    -f) STATUS_FILE="$2"; shift 2 ;;
    -p) POLL_SECS="$2"; shift 2 ;;
    --no-color) NO_COLOR_MODE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

# ------------ colors (truecolor / RGB) ------------
# Helper to make a 24-bit FG color: rgb() -> \e[38;2;R;G;Bm
rgb() { printf '\e[38;2;%d;%d;%dm' "$1" "$2" "$3"; }

if [[ -t 1 && "$NO_COLOR_MODE" -eq 0 && -z "${NO_COLOR:-}" ]]; then
  RESET=$'\e[0m'

  # Prefix color [status]: cyan-ish (RGB)
  C_STATUS="$(rgb 0 200 200)"

  # Highlight for the whole Fuel object (RGB) — tweak to taste
  # (golden yellow)
  C_FUEL="$(rgb 255 215 0)"

  # Optional accents (unused right now, but set as RGB in case you expand later)
  C_INFO="$(rgb 255 200 0)"
  C_ERR="$(rgb 255 80 80)"
else
  RESET=""; C_STATUS=""; C_FUEL=""; C_INFO=""; C_ERR=""
fi

export RESET C_STATUS C_FUEL

have_inotify() { command -v inotifywait >/dev/null 2>&1; }
have_jq() { command -v jq >/dev/null 2>&1; }

info() { printf '%s[info]%s %s\n' "$C_INFO" "$RESET" "$*" >&2; }
err()  { printf '%s[error]%s %s\n' "$C_ERR" "$RESET" "$*" >&2; }

path_status() { printf '%s/%s\n' "$DIR" "$STATUS_FILE"; }

# ------------ printing ------------
print_status_once() {
  local path; path="$(path_status)"
  [[ -f "$path" ]] || { info "(missing: $path)"; return 0; }

  if have_jq; then
    # Compact with jq, then highlight the Fuel object, then prefix with [status]
    jq -c . -- "$path" 2>/dev/null \
      | sed -u -E "s/\"Fuel\":\{[^}]*\}/${C_FUEL}&${RESET}/" \
      | sed -u "s/^/${C_STATUS}[status] ${RESET}/"
  else
    # No jq: read raw line, same highlight + prefix
    sed -u -E "s/\"Fuel\":\{[^}]*\}/${C_FUEL}&${RESET}/" -- "$path" \
      | sed -u "s/^/${C_STATUS}[status] ${RESET}/"
  fi
}

# ------------ watchers ------------
status_watcher_inotify() {
  local path; path="$(path_status)"
  local last_mtime=""
  # Print once right away (if present)
  [[ -f "$path" ]] && print_status_once
  # Watch the directory; print on close_write/create/moved_to that affects the file
  while inotifywait -qq -e close_write -e moved_to -e create -- "$DIR" >/dev/null; do
    [[ -f "$path" ]] || { info "(missing: $path)"; continue; }
    mtime="$(stat -c %Y -- "$path" 2>/dev/null || echo "")"
    if [[ "$mtime" != "$last_mtime" ]]; then
      print_status_once
      last_mtime="$mtime"
    fi
  done
}

status_watcher_poll() {
  local path; path="$(path_status)"
  local last_mtime=""
  while true; do
    if [[ -f "$path" ]]; then
      mtime="$(stat -c %Y -- "$path" 2>/dev/null || echo "")"
      if [[ "$mtime" != "$last_mtime" ]]; then
        print_status_once
        last_mtime="$mtime"
      fi
    else
      info "(missing: $path)"
      last_mtime=""
    fi
    sleep "$POLL_SECS"
  done
}

# ------------ main ------------
trap 'exit 0' INT TERM

info "Dir   : $DIR"
info "File  : $STATUS_FILE"
info "inotify: $(have_inotify && echo yes || echo no)"

if have_inotify; then
  status_watcher_inotify
else
  status_watcher_poll
fi
