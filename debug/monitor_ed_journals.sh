#!/usr/bin/env bash
# monitor_ed_journals.sh
# - Follow newest Journal.*.log (auto-switch on new files)
# - Reprint Status.json whenever it updates
# - Colorized output + one empty line before the first [journal]
# - Flags:
#     -j : show [info] + [journal] only
#     -s : show [info] + [status]  only
#     -h : help

set -Eeuo pipefail

# ----- adjust this to your real location -----
DIR="/mnt/games/ED/journals/Frontier Developments/Elite Dangerous"

JOUR_PAT='Journal.*.log'
STATUS_FILE="Status.json"
TAIL_N=1
POLL_SECS=1
USE_JQ=1
current_file=""


# --- mode handling ---
MODE="both"   # "both" | "journal" | "status"

usage() {
  cat <<'USAGE'
Usage: monitor_ed_journals.sh [-j|-s] [-h]
  -j   Print only [info] and [journal] lines (disable Status watcher)
  -s   Print only [info] and [status]  lines (disable Journal tail)
  -h   Show this help and exit
USAGE
}

while getopts ":jsh" opt; do
  case "$opt" in
    j) MODE="journal" ;;
    s) MODE="status" ;;
    h) usage; exit 0 ;;
    \?) echo "Unknown option: -$OPTARG" >&2; usage; exit 2 ;;
  esac
done

tail_pid=""
status_pid=""
printed_first_journal=0

# ---------- colors ----------
if [[ -t 1 && "${NO_COLOR:-}" != "1" ]]; then
  RESET=$'\e[0m'; BOLD=$'\e[1m'; DIM=$'\e[2m'
  C_JOUR=$'\e[32m'   # green
  C_STATUS=$'\e[36m' # cyan
  C_INFO=$'\e[33m'   # yellow
  C_ERR=$'\e[31m'    # red
  C_HL=$'\e[33m'   # yellow for highlighting (Fuel)
  # 256-color orange + light blue (falls back to no color when NO_COLOR=1 or not a TTY)
  C_ORANGE=$'\e[38;5;208m'
  C_LBLUE=$'\e[38;5;45m'
  # make colors visible to awk via ENVIRON[]
  export RESET C_JOUR C_STATUS C_INFO C_ERR C_HL C_ORANGE C_LBLUE
else
  RESET=; BOLD=; DIM=; C_JOUR=; C_STATUS=; C_INFO=; C_ERR=; C_HL=; C_ORANGE=; C_LBLUE=
fi

info() { printf '%s[info]%s %s\n' "$C_INFO" "$RESET" "$*" >&2; }
err()  { printf '%s[error]%s %s\n' "$C_ERR" "$RESET" "$*" >&2; }

have_inotify() { command -v inotifywait >/dev/null 2>&1; }
have_jq() { [[ "${USE_JQ}" -eq 1 ]] && command -v jq >/dev/null 2>&1; }

latest_journal() {
  shopt -s nullglob
  local newest=""
  local newest_mtime=-1
  local f mtime
  for f in "$DIR"/$JOUR_PAT; do
    [[ -e "$f" ]] || continue
    mtime="$(stat -c %Y -- "$f" 2>/dev/null || echo 0)"
    if (( mtime > newest_mtime )); then
      newest="$f"; newest_mtime="$mtime"
    elif (( mtime == newest_mtime )) && [[ -n "$newest" && "$f" > "$newest" ]]; then
      newest="$f"
    fi
  done
  [[ -n "$newest" ]] && printf '%s\n' "$newest"
}

# Kill the entire journal pipeline (tail + filter) if it exists
stop_tail_journal() {
  if [[ -n "${tail_pid}" ]] && kill -0 "${tail_pid}" 2>/dev/null; then
    # kill whole process group started by bash -c (negative PGID)
    kill -TERM -- "-${tail_pid}" 2>/dev/null || kill -TERM "${tail_pid}" 2>/dev/null || true
    wait "${tail_pid}" 2>/dev/null || true
  fi
  tail_pid=""
}

# Start exactly one pipeline for the given file (deduped + colored)
start_tail_journal() {
  local file="$1"
  if [[ "$current_file" == "$file" ]] && [[ -n "${tail_pid}" ]] && kill -0 "${tail_pid}" 2>/dev/null; then
    return 0
  fi
  stop_tail_journal
  current_file="$file"

  info "Following: $file"
  if [[ $printed_first_journal -eq 0 ]]; then
    printf '\n'
    printed_first_journal=1
  fi

  bash -c '
    tail -n +1 -F -- "$0" \
    | awk -W interactive "
        BEGIN{
          orange=\"'"$C_ORANGE"'\";
          lblue =\"'"$C_LBLUE"'\";
          reset =\"'"$RESET"'\";
          pref  =\"'"$C_JOUR"'[journal] '"$RESET"'\";
        }
        {
          line=\$0
          gsub(/\"StarSystem\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/, orange \"&\" reset, line)
          gsub(/\"SystemAddress\"[[:space:]]*:[[:space:]]*[0-9]+/,         orange \"&\" reset, line)
          gsub(/\"WasDiscovered\"[[:space:]]*:[[:space:]]*(true|false)/,    lblue  \"&\" reset, line)
          gsub(/\"WasMapped\"[[:space:]]*:[[:space:]]*(true|false)/,        lblue  \"&\" reset, line)
          gsub(/\"WasFootfalled\"[[:space:]]*:[[:space:]]*(true|false)/,    lblue  \"&\" reset, line)
          print pref line; fflush()
        }"
  ' "$file" &
  tail_pid=$!
}

print_status_once() {
  local path="$DIR/$STATUS_FILE"
  [[ -f "$path" ]] || { info "(status missing: $path)"; return 0; }

  if have_jq; then
    # Compact JSON, then colorize the Fuel object, then prefix with [status]
    jq -c . -- "$path" 2>/dev/null \
      | sed -u -E "s/\"Fuel\":\{[^}]*\}/${C_HL}&${RESET}/" \
      | sed -u "s/^/${C_STATUS}[status] ${RESET}/"
  else
    # No jq: work on the raw line, same highlighting + prefix
    sed -u -E "s/\"Fuel\":\{[^}]*\}/${C_HL}&${RESET}/" -- "$path" \
      | sed -u "s/^/${C_STATUS}[status] ${RESET}/"
  fi
}

status_watcher_inotify() {
  local path="$DIR/$STATUS_FILE"
  print_status_once
  while inotifywait -qq -e close_write -e create -e moved_to -- "$DIR" >/dev/null; do
    [[ -f "$path" ]] && print_status_once
  done
}

status_watcher_poll() {
  local path="$DIR/$STATUS_FILE"
  local last_mtime=""
  while true; do
    if [[ -f "$path" ]]; then
      mtime="$(stat -c %Y -- "$path" 2>/dev/null || echo "")"
      if [[ "$mtime" != "$last_mtime" ]]; then
        print_status_once
        last_mtime="$mtime"
      fi
    else
      info "(status missing: $path)"
      last_mtime=""
    fi
    sleep "$POLL_SECS"
  done
}

start_status_watcher() {
  if have_inotify; then
    status_watcher_inotify &
  else
    status_watcher_poll &
  fi
  status_pid=$!
}

stop_status_watcher() {
  if [[ -n "${status_pid}" ]] && kill -0 "${status_pid}" 2>/dev/null; then
    kill "${status_pid}" 2>/dev/null || true
    wait "${status_pid}" 2>/dev/null || true
  fi
  status_pid=""
}

# ------------------ MAIN ------------------
trap 'stop_tail_journal; stop_status_watcher' EXIT INT TERM

info "Mode   : $MODE"
info "Log dir: $DIR"
info "Pattern: $JOUR_PAT"
info "Status : $STATUS_FILE"
info "inotify: $(have_inotify && echo yes || echo no)"

# Start watchers depending on mode
if [[ "$MODE" != "journal" ]]; then
  start_status_watcher
fi

current=""
if [[ "$MODE" != "status" ]]; then
  # try to start on the current newest journal (if any)
  if next="$(latest_journal)"; then
    current="$next"
    start_tail_journal "$current"
  else
    info "No matching journals yet; waiting for one to appear…"
  fi
fi

# event loop
if [[ "$MODE" == "status" ]]; then
  # Just wait on the status watcher to keep the script alive
  wait "$status_pid"
else
  while true; do
    if have_inotify; then
      inotifywait -qq -e create -e moved_to -e close_write -- "$DIR" >/dev/null
      sleep 0.1   # tiny debounce so latest_journal sees the new file
    else
      sleep "$POLL_SECS"
    fi

    next="$(latest_journal || true)"
    if [[ -n "$next" && "$next" != "$current_file" ]]; then
      info "Switching journal -> $next"
      start_tail_journal "$next"
    fi

  done
fi
