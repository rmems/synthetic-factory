#!/usr/bin/env bash
# One-line status per open PR whose head branch starts with a prefix (default: the card-schema chains).
# Usage: sf_stack_status.sh [head-branch-prefix]
R="${SF_REPO:-rmems/synthetic-factory}"; P="${1:-agent/card-schema}"
gh pr list --repo "$R" --state open --limit 60 --json number,baseRefName,headRefName,mergeable,mergeStateStatus,statusCheckRollup,headRefOid \
 --jq ".[] | select(.headRefName|startswith(\"$P\")) | \"\\(.number)\\t\\(.baseRefName)\\t\\(.mergeable)/\\(.mergeStateStatus)\\tfail=\\([.statusCheckRollup[]? | select(.conclusion==\"FAILURE\")] | length)\\t\\(.headRefOid[0:8])\\t\\(.headRefName)\"" | sort -n
