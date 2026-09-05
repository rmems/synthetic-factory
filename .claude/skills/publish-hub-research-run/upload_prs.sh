# Written and run by a Claude Fable 5.1 subagent during the 2026-09-04 Hub publication session.
#!/usr/bin/env bash
# NOT RUN. Uploads each prepared bundle as a Hub pull request (never to main).
# Run only after the owner has settled the two open questions in the report
# (viewer container format; rights.json statuses vs the repo validator).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
WORK="$HOME/tmp/publish-0830"
MSG="Add the 2026-08-30 Claude Fable 5 rounds (raw, uncurated, research-only) and refresh the rights record"
for repo in thalamic-relay-trajectories neuromorphic-event-language-bridge multi-agent-ouroboros-swarm failure-as-fuel-preference-cascade; do
  DESC="Appends the committed 2026-08-30 Claude Fable 5 rounds (Anthropic, Claude Max, Claude Code) under data/raw/2026-08-30/ with their round notes under notes/2026-08-30/, rebuilds data/viewer/records.parquet and records.jsonl with the existing rows unchanged and the new rows appended, and refreshes README.md, rights.json, release-status.json and provenance.json (raw_snapshot.runs). No existing raw file is modified. Raw, uncurated, research-only; not training-ready.

— Claude Fable 5.1 (Claude Code)"
  hf upload "rmems/$repo" "$WORK/bundles/$repo" . --repo-type dataset --create-pr \
    --commit-message "$MSG" --commit-description "$DESC"
done
