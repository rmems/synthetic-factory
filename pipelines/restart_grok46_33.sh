#!/usr/bin/env bash
# Launch 33 Grok 4.6 factory generators after weekly Heavy reset.
# Intended for cron at 06:52 CDT. Refuses to run before reset.
set -euo pipefail

ROOT=/home/raulmc/rmems/synthetic-factory
PROMPT="$ROOT/pipelines/restart_grok46_33.md"
GROK="${GROK:-/home/raulmc/.local/bin/grok}"
LOG=/tmp/grok46-restart-33.log
LOCK=/tmp/grok46-restart-33.lock
PID_FILE=/tmp/grok46-restart-33.pid
SESSION=grok46-agentic-restart

export TZ=America/Chicago
dow=$(date +%u)
hour=$(date +%H)
minute=$(date +%M)
now_hm=$((10#$hour * 100 + 10#$minute))
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
echo "$(date -Is) starting 33-agent restart" >>"$LOG"

# The advisory flock protects overlapping launcher shells only. The nohup
# worker outlives this shell, so keep its PID separately and refuse a second
# window tick while that exact process is still alive.
if [[ -s "$PID_FILE" ]]; then
  read -r existing_pid <"$PID_FILE" || true
  if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
    echo "$(date -Is) skip: nohup worker pid $existing_pid already live" >>"$LOG"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

cd "$ROOT"
"$ROOT/.claude/skills/run-synthetic-factory/driver.py" frontiers outputs/raw/2026-08-19-agentic >>"$LOG" 2>&1 || true

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "$(date -Is) skip: tmux session $SESSION already live" >>"$LOG"
    exit 0
  fi
  tmux new-session -d -s "$SESSION" \
    "cd '$ROOT' && exec '$GROK' --cwd '$ROOT' --always-approve --no-plan --model grok-4.6 \"\$(cat '$PROMPT')\" 2>&1 | tee -a '$LOG'"
  echo "$(date -Is) tmux session $SESSION" >>"$LOG"
else
  nohup "$GROK" --cwd "$ROOT" --always-approve --no-plan --model grok-4.6 "$(cat "$PROMPT")" >>"$LOG" 2>&1 &
  echo $! >"$PID_FILE"
  echo "$(date -Is) nohup pid $(cat "$PID_FILE")" >>"$LOG"
fi
