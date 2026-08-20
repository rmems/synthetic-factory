#!/usr/bin/env bash
# Launch 33 Grok 4.6 factory generators after weekly Heavy reset.
# Intended for cron at 06:52 CDT. Refuses to run before reset.
set -euo pipefail

ROOT=/home/raulmc/rmems/synthetic-factory
PROMPT="$ROOT/pipelines/restart_grok46_33.md"
GROK="${GROK:-/home/raulmc/.local/bin/grok}"
STATE_DIR="${XDG_STATE_HOME:-/home/raulmc/.local/state}/synthetic-factory-grok46"
umask 077
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
LOG="$STATE_DIR/restart.log"
LOCK="$STATE_DIR/launcher.lock"
PID_FILE="$STATE_DIR/worker.state"
WINDOW_FILE="$STATE_DIR/last-launch-window"
SESSION=grok46-agentic-restart

process_start_token() {
  local pid="${1:-}" stat rest
  local -a fields
  [[ "$pid" =~ ^[0-9]+$ && -r "/proc/$pid/stat" ]] || return 1
  stat=$(<"/proc/$pid/stat")
  rest=${stat##*) }
  read -r -a fields <<<"$rest"
  [[ ${#fields[@]} -ge 20 ]] || return 1
  printf '%s\n' "${fields[19]}"
}

write_worker_state() {
  local pid="$1" started temporary
  started=$(process_start_token "$pid") || return 1
  temporary=$(mktemp "$STATE_DIR/.worker-state.XXXXXX") || return 1
  if ! printf '%s %s\n' "$pid" "$started" >"$temporary"; then
    rm -f -- "$temporary"
    return 1
  fi
  chmod 600 "$temporary"
  mv -f -- "$temporary" "$PID_FILE"
}

write_launch_window() {
  local window="$1" temporary
  temporary=$(mktemp "$STATE_DIR/.launch-window.XXXXXX") || return 1
  if ! printf '%s\n' "$window" >"$temporary"; then
    rm -f -- "$temporary"
    return 1
  fi
  chmod 600 "$temporary"
  mv -f -- "$temporary" "$WINDOW_FILE"
}

resolve_grok() {
  local resolved
  if [[ "$GROK" == */* ]]; then
    [[ -f "$GROK" && -x "$GROK" ]] || return 1
    return 0
  fi
  resolved=$(command -v "$GROK") || return 1
  [[ -f "$resolved" && -x "$resolved" ]] || return 1
  GROK="$resolved"
}

export TZ=America/Chicago
dow=$(date +%u)
hour=$(date +%H)
minute=$(date +%M)
now_hm=$((10#$hour * 100 + 10#$minute))
launch_window=$(date +%G-W%V)
# Weekly SuperGrok Heavy reset is Wednesday 06:52 CDT. Allow through 08:30.
if [[ "$dow" != "3" ]] || (( now_hm < 652 || now_hm > 830 )); then
  echo "$(date -Is) skip: outside Wed 06:52-08:30 CDT (dow=$dow now=$now_hm)" >>"$LOG"
  exit 0
fi

exec 9>"$LOCK"
if ! flock -n 9; then
  echo "$(date -Is) skip: lock held ($LOCK)" >>"$LOG"
  exit 0
fi
echo $$ >&9

if ! resolve_grok; then
  echo "$(date -Is) error: missing or non-executable Grok command: $GROK" >>"$LOG"
  exit 1
fi

# A worker may complete before a later scheduler invocation in the same reset
# window. Keep that completed launch distinct from the transient PID/session
# state so a successful weekly orchestration cannot run twice.
if [[ -s "$WINDOW_FILE" ]]; then
  read -r completed_window extra <"$WINDOW_FILE" || true
  if [[ -n "${completed_window:-}" && -z "${extra:-}" && "$completed_window" == "$launch_window" ]]; then
    echo "$(date -Is) skip: weekly launch already consumed ($launch_window)" >>"$LOG"
    exit 0
  fi
fi

# The lock protects launch setup. The detached worker subsequently holds its
# own flock, while the state file verifies both PID and /proc start token so a
# recycled PID cannot suppress a new weekly run.
if [[ -s "$PID_FILE" ]]; then
  read -r existing_pid existing_started extra <"$PID_FILE" || true
  current_started=""
  if [[ "$existing_pid" =~ ^[0-9]+$ ]]; then
    current_started=$(process_start_token "$existing_pid" || true)
  fi
  if [[ -n "$existing_started" && -z "$extra" && "$current_started" == "$existing_started" ]]; then
    echo "$(date -Is) skip: nohup worker pid $existing_pid identity still live" >>"$LOG"
    exit 0
  fi
  rm -f -- "$PID_FILE"
fi

echo "$(date -Is) starting 33-agent restart" >>"$LOG"
cd "$ROOT"
if ! python3 "$ROOT/.claude/skills/run-synthetic-factory/driver.py" frontiers outputs/raw/2026-08-19-agentic >>"$LOG" 2>&1; then
  echo "$(date -Is) warning: frontier preflight failed; continuing weekly launch" >>"$LOG"
fi

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "$(date -Is) skip: tmux session $SESSION already live" >>"$LOG"
    exit 0
  fi
  tmux new-session -d -s "$SESSION" \
    "exec 9>&-; cd '$ROOT' && exec flock '$LOCK' '$GROK' --cwd '$ROOT' --no-plan --model grok-4.6 \"\$(cat '$PROMPT')\" 2>&1 | tee -a '$LOG'"
  if ! write_launch_window "$launch_window"; then
    tmux kill-session -t "$SESSION" 2>/dev/null || true
    echo "$(date -Is) error: could not atomically record launch window" >>"$LOG"
    exit 1
  fi
  echo "$(date -Is) tmux session $SESSION" >>"$LOG"
else
  (
    exec 9>&-
    exec nohup flock "$LOCK" "$GROK" --cwd "$ROOT" --no-plan --model grok-4.6 "$(cat "$PROMPT")" >>"$LOG" 2>&1
  ) &
  worker_pid=$!
  if ! write_worker_state "$worker_pid"; then
    kill "$worker_pid" 2>/dev/null || true
    echo "$(date -Is) error: could not atomically record nohup worker state" >>"$LOG"
    exit 1
  fi
  if ! write_launch_window "$launch_window"; then
    kill "$worker_pid" 2>/dev/null || true
    rm -f -- "$PID_FILE"
    echo "$(date -Is) error: could not atomically record launch window" >>"$LOG"
    exit 1
  fi
  echo "$(date -Is) nohup supervisor pid $worker_pid" >>"$LOG"
fi
