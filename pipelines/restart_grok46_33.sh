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
now_hm=$(date +%H%M)
# Weekly reset is 06:52 CDT. Allow from 06:52 through 08:30 so a delayed cron still fires.
if [[ "$now_hm" < "0652" || "$now_hm" > "0830" ]]; then
  echo "$(date -Is) skip: outside 06:52-08:30 CDT window (now $now_hm)" >>"$LOG"
  exit 0
fi

if [[ -f "$LOCK" ]] && kill -0 "$(cat "$LOCK")" 2>/dev/null; then
  echo "$(date -Is) skip: already running pid $(cat "$LOCK")" >>"$LOG"
  exit 0
fi

echo $$ >"$LOCK"
echo "$(date -Is) starting 33-agent restart" >>"$LOG"

cd "$ROOT"
"$ROOT/.claude/skills/run-synthetic-factory/driver.py" frontiers outputs/raw/2026-08-19-agentic >>"$LOG" 2>&1 || true

if command -v tmux >/dev/null 2>&1; then
  tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"
  tmux new-session -d -s "$SESSION" \
    "cd '$ROOT' && exec '$GROK' --cwd '$ROOT' --always-approve --no-plan --model grok-4.6 \"\$(cat '$PROMPT')\" 2>&1 | tee -a '$LOG'"
  echo "$(date -Is) tmux session $SESSION" >>"$LOG"
else
  nohup "$GROK" --cwd "$ROOT" --always-approve --no-plan --model grok-4.6 "$(cat "$PROMPT")" >>"$LOG" 2>&1 &
  echo $! >"$LOCK"
  echo "$(date -Is) nohup pid $(cat "$LOCK")" >>"$LOG"
fi
