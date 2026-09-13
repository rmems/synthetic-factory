#!/usr/bin/env bash
# Just-in-time integration of origin/main into one stacked card-schema PR, in its existing worktree.
# Usage: sf_land_child.sh <pr-number> [file-to-take-from-main ...]
# Merge only (never rebase). Aborts on dirty worktree, wrong base, or unexpected conflicts.
set -u
PR="$1"; shift; TAKE_MAIN=("$@")
R="${SF_REPO:-rmems/synthetic-factory}"
ROOT="${SF_REPO_ROOT:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null)}"
SESSION="${CLAUDE_SESSION_URL:-https://claude.ai/code/session_01T9WqTy6R6FuLKeJzSC8xTX}"
TRAILER="${CLAUDE_TRAILER:-Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>}"
read -r BRANCH BASE < <(gh pr view "$PR" --repo $R --json headRefName,baseRefName --jq '"\(.headRefName) \(.baseRefName)"')
echo "== PR #$PR  head=$BRANCH  base=$BASE"
[ "$BASE" = "main" ] || { echo "ABORT: base is '$BASE', not main (parent not merged / not retargeted yet)"; exit 2; }
WT=$(git -C "$ROOT" worktree list --porcelain | awk -v b="refs/heads/$BRANCH" '/^worktree /{w=$2} $0=="branch "b{print w}')
[ -n "$WT" ] || { echo "ABORT: no existing worktree for $BRANCH"; exit 2; }
cd "$WT" || exit 2
[ -z "$(git status --porcelain)" ] || { echo "ABORT: dirty worktree $WT"; git status --short | head; exit 2; }
git fetch -q origin && git pull -q --no-rebase origin "$BRANCH" || { echo "ABORT: pull failed"; exit 2; }
BEFORE=$(git rev-parse --short HEAD)
if git merge-base --is-ancestor origin/main HEAD; then
  echo "main already integrated at $BEFORE (no merge needed)"
else
  git merge --no-ff --no-commit origin/main >/dev/null 2>&1
  CONFLICTS=$(git diff --name-only --diff-filter=U)
  if [ -n "$CONFLICTS" ]; then
    for f in $CONFLICTS; do
      ok=0; for t in "${TAKE_MAIN[@]:-}"; do [ "$t" = "$f" ] && ok=1; done
      [ $ok = 1 ] || { echo "ABORT: unexpected conflict in $f (hand merge required)"; git merge --abort; exit 3; }
    done
    git checkout origin/main -- $CONFLICTS && git add $CONFLICTS
    echo "took main's bytes for: $CONFLICTS"
  fi
  OWN=$(git diff --cached --name-only origin/main | tr '\n' ' ')
  echo "own files vs main after merge: $OWN"
  git commit -q -F - <<MSG
Integrate origin/main into $BRANCH

Two-parent merge so PR #$PR carries only its own card-schema declaration on top of main.

$TRAILER
Claude-Session: $SESSION
MSG
  echo "merge commit: $(git rev-parse --short HEAD) parents: $(git log -1 --format=%p)"
fi
mkdir -p "$HOME/tmp"; export TMPDIR="$HOME/tmp"
python3 -m unittest discover -s tests -p 'test_*.py' -q 2>&1 | tail -2; UT=${PIPESTATUS[0]}
python3 .claude/skills/run-synthetic-factory/driver.py smoke >/dev/null 2>&1; SM=$?
python3 pipelines/census.py tests/fixtures/mini-run >/dev/null 2>&1; CE=$?
STRICT=$(python3 scripts/publish_grok46_hub.py schemas --strict 2>&1 | tail -1)
echo "unittest=$UT smoke=$SM census=$CE | $STRICT"
if [ "$UT" = 0 ] && [ "$SM" = 0 ] && [ "$CE" = 0 ]; then
  git push -q origin "$BRANCH" && echo "pushed $(git rev-parse --short HEAD)"
  git fetch -q origin; git merge-tree --write-tree origin/main "origin/$BRANCH" >/dev/null; echo "merge-tree vs main exit=$?"
  echo "GitHub head: $(gh pr view "$PR" --repo $R --json headRefOid --jq .headRefOid | cut -c1-8)"
else
  echo "NOT PUSHED: a local check failed"; exit 4
fi
