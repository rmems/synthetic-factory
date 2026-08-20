#!/usr/bin/env bash
# Launch 33 Grok 4.6 factory generators after weekly Heavy reset.
# Intended for cron at 06:52 CDT. Refuses to run before reset.
set -euo pipefail

ROOT=/home/raulmc/rmems/synthetic-factory
PROMPT="$ROOT/pipelines/restart_grok46_33.md"
GROK="${GROK:-/home/raulmc/.local/bin/grok}"
LOG=/tmp/grok46-restart-33.log
LOCK=/tmp/grok46-restart-33.lock
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
  echo $! >"$LOCK"
  echo "$(date -Is) nohup pid $(cat "$LOCK")" >>"$LOG"
fi
