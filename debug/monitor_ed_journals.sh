#!/usr/bin/env bash
# monitor_ed_journals.sh (symlink-free, setsid-stable)
# - Follows newest Journal.*.log directly
# - On rollover: kill old tail|awk session group and start a new one
# - Truecolor (RGB), zebra per line, requested highlights
# - inotify when available, else polling

set -Eeuo pipefail

# ---------- defaults ----------
DIR="${DIR_OVERRIDE:-/home/kepas/EDData/EDGameData/Saved Games/Frontier Developments/Elite Dangerous}"
JOUR_PATTERN='Journal.*.log'
POLL_SECS=1

# ---------- CLI ----------
usage() {
  cat <<USAGE
Usage: $(basename "$0") [-d DIR] [-p SECS] [--no-color] [-h]
  -d DIR       Directory containing Journal.*.log
  -p SECS      Poll interval when inotify is unavailable (default: 1)
  --no-color   Disable colors
  -h           Help
USAGE
}
NO_COLOR_MODE=0
while (( $# )); do
  case "$1" in
    -d) DIR="$2"; shift 2 ;;
    -p) POLL_SECS="$2"; shift 2 ;;
    --no-color) NO_COLOR_MODE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

# ---------- helpers ----------
have_inotify() { command -v inotifywait >/dev/null 2>&1; }
have_setsid()  { command -v setsid >/dev/null 2>&1; }
rgb()          { printf '\e[38;2;%d;%d;%dm' "$1" "$2" "$3"; }

# ---------- colors (truecolor) ----------
if [[ -t 1 && "$NO_COLOR_MODE" -eq 0 && -z "${NO_COLOR:-}" ]]; then
  RESET=$'\e[0m'
  C_JOUR="$(rgb 0 220 120)"        # [journal]
  C_BASE1="$(rgb 220 220 50)"      # zebra base 1
  C_BASE2="$(rgb 190 190 190)"     # zebra base 2
  C_BODYNAME="$(rgb 200 100 255)"  # BodyName
  C_SYSTEMS="$(rgb 255 150 150)"   # StarSystem + SystemAddress
  C_DISC="$(rgb 150 255 255)"      # discovery flags
  C_INFO="$(rgb 255 200 0)"
  C_ERR="$(rgb 255 80 80)"
else
  RESET=""; C_JOUR=""; C_BASE1=""; C_BASE2="";
  C_BODYNAME=""; C_SYSTEMS=""; C_DISC=""; C_INFO=""; C_ERR="";
fi

info(){ printf '%s[info]%s %s\n'  "$C_INFO" "$RESET" "$*" >&2; }
err(){  printf '%s[error]%s %s\n' "$C_ERR"  "$RESET" "$*" >&2; }

# ---------- newest file picker ----------
latest_journal() {
  shopt -s nullglob
  local f newest="" newest_mtime=-1 m
  for f in "$DIR"/$JOUR_PATTERN; do
    [[ -e "$f" ]] || continue
    m="$(stat -c %Y -- "$f" 2>/dev/null || echo 0)"
    if (( m > newest_mtime )) || { (( m == newest_mtime )) && [[ "$f" > "$newest" ]]; }; then
      newest="$f"; newest_mtime="$m"
    fi
  done
  [[ -n "$newest" ]] && printf '%s\n' "$newest"
}

# ---------- pipeline control (no symlink) ----------
pipe_launcher_pid=""; pipe_pgid=""; current_file=""; printed_first=0

stop_pipeline() {
  # Kill whole process group (tail + awk) if we have it
  if [[ -n "${pipe_pgid}" ]]; then
    kill -TERM "-${pipe_pgid}" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      pgrep -g "${pipe_pgid}" >/dev/null 2>&1 || break
      sleep 0.1
    done
    pipe_pgid=""
  fi
  if [[ -n "${pipe_launcher_pid}" ]] && kill -0 "${pipe_launcher_pid}" 2>/dev/null; then
    kill -TERM "${pipe_launcher_pid}" 2>/dev/null || true
    wait "${pipe_launcher_pid}" 2>/dev/null || true
  fi
  pipe_launcher_pid=""
}

start_pipeline() {
  local file="$1"
  # already on this file and alive? do nothing
  if [[ "$current_file" == "$file" ]] && [[ -n "${pipe_launcher_pid}" ]] && kill -0 "${pipe_launcher_pid}" 2>/dev/null; then
    return 0
  fi

  stop_pipeline
  current_file="$file"
  info "Following: $file"
  if (( printed_first == 0 )); then printf '\n'; printed_first=1; fi

  # Use a fresh session so we can kill the whole pipeline by PGID safely
  if have_setsid; then
    setsid bash -c '
      tail -n +1 -F -- "$0" |
      awk -W interactive \
        -v pref="$1" -v base1="$2" -v base2="$3" -v reset="$4" \
        -v c_body="$5" -v c_sys="$6" -v c_disc="$7" "
        {
          base = (NR % 2 == 1) ? base1 : base2;
          line = \$0;
          gsub(/\"BodyName\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/,           c_body \"&\" reset base, line);
          gsub(/\"StarSystem\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/,         c_sys  \"&\" reset base, line);
          gsub(/\"SystemAddress\"[[:space:]]*:[[:space:]]*[0-9]+/,         c_sys  \"&\" reset base, line);
          gsub(/\"WasDiscovered\"[[:space:]]*:[[:space:]]*(true|false)/,   c_disc \"&\" reset base, line);
          gsub(/\"WasMapped\"[[:space:]]*:[[:space:]]*(true|false)/,       c_disc \"&\" reset base, line);
          gsub(/\"WasFootfalled\"[[:space:]]*:[[:space:]]*(true|false)/,   c_disc \"&\" reset base, line);
          print pref base line reset; fflush();
        }"
    ' bash "$file" "${C_JOUR}[journal] ${RESET}" "$C_BASE1" "$C_BASE2" "$RESET" "$C_BODYNAME" "$C_SYSTEMS" "$C_DISC" &
  else
    # Fallback without setsid: still works, just slightly less isolated
    bash -c '
      tail -n +1 -F -- "$0" |
      awk -W interactive \
        -v pref="$1" -v base1="$2" -v base2="$3" -v reset="$4" \
        -v c_body="$5" -v c_sys="$6" -v c_disc="$7" "
        {
          base = (NR % 2 == 1) ? base1 : base2;
          line = \$0;
          gsub(/\"BodyName\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/,           c_body \"&\" reset base, line);
          gsub(/\"StarSystem\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/,         c_sys  \"&\" reset base, line);
          gsub(/\"SystemAddress\"[[:space:]]*:[[:space:]]*[0-9]+/,         c_sys  \"&\" reset base, line);
          gsub(/\"WasDiscovered\"[[:space:]]*:[[:space:]]*(true|false)/,   c_disc \"&\" reset base, line);
          gsub(/\"WasMapped\"[[:space:]]*:[[:space:]]*(true|false)/,       c_disc \"&\" reset base, line);
          gsub(/\"WasFootfalled\"[[:space:]]*:[[:space:]]*(true|false)/,   c_disc \"&\" reset base, line);
          print pref base line reset; fflush();
        }"
    ' bash "$file" "${C_JOUR}[journal] ${RESET}" "$C_BASE1" "$C_BASE2" "$RESET" "$C_BODYNAME" "$C_SYSTEMS" "$C_DISC" &
  fi

  pipe_launcher_pid=$!
  pipe_pgid="$(ps -o pgid= "${pipe_launcher_pid}" | tr -d ' ')"
}

# ---------- watcher loops ----------
watch_inotify() {
  while inotifywait -qq -e create -e moved_to -e close_write -- "$DIR" >/dev/null; do
    sleep 0.1  # debounce
    local next; next="$(latest_journal || true)"
    if [[ -n "$next" && "$next" != "$current_file" ]]; then
      info "Switching journal -> $next"
      start_pipeline "$next"
    fi
  done
}
watch_poll() {
  while true; do
    local next; next="$(latest_journal || true)"
    if [[ -n "$next" && "$next" != "$current_file" ]]; then
      info "Switching journal -> $next"
      start_pipeline "$next"
    fi
    sleep "$POLL_SECS"
  done
}

# ---------- main ----------
cleanup_and_exit() { stop_pipeline; exit 0; }
trap cleanup_and_exit INT TERM

info "Dir    : $DIR"
info "Pattern: $JOUR_PATTERN"
info "inotify: $(have_inotify && echo yes || echo no)"

if next="$(latest_journal)"; then
  start_pipeline "$next"
else
  info "No matching journals yet; waiting for one to appear…"
fi

if have_inotify; then
  watch_inotify
else
  watch_poll
fi
