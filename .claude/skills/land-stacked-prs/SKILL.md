---
name: land-stacked-prs
description: Land, integrate, babysit, or merge a stack of dependent GitHub pull requests in rmems/synthetic-factory without rebasing - retarget the root, merge main into each PR's existing worktree, wait for exact-head checks, triage bot threads, squash-merge parent-first. Use when asked to "land the stack", "integrate main into PR N", "why does the PR say out of date / conflicting", "merge the ones that are ready", or to babysit a chain of stacked PRs.
---

# Land stacked PRs (merge only, never rebase)

Paths are relative to the repository root. Every command below was run in the 2026-09-03/04 session
that landed the 22-PR card-schema stack (#112-#133) plus its root PR #177.

Ground rules that are not negotiable in this repo (AGENTS.md, owner):

- Branches advance by `git merge` / `git pull --no-rebase` only. Never rebase, amend, reset, force-push,
  squash locally, or recreate published commits. Existing `.claude/worktrees/agent-*` checkouts are the
  working copies; do not start a parallel worktree for a PR that has one.
- PRs land on `main` as **squash** merges (owner preference). A squash means every child still carries
  the parent's original commits, so each child needs exactly one merge of `main` before it merges.
- Every commit needs the running model's trailer (the owner's commit hook rejects commits without one);
  every GitHub comment ends with `- Claude Fable 5.1 (Claude Code)` (or whichever model is running).

## Harness

| Script | What it does |
|---|---|
| `.claude/skills/land-stacked-prs/sf_land_child.sh <pr> [file ...]` | In the PR's existing worktree: pull the branch (no rebase), merge `origin/main` with a two-parent commit, take `main`'s bytes for the listed files if they conflict (abort on any other conflict), assert the PR's own files vs main, run the four local checks, push, print merge-tree exit and the live head. |
| `.claude/skills/land-stacked-prs/sf_wait_green.sh <pr> [pr ...]` | Poll each PR until every check is complete (or the PR is no longer open), then print one `READY?` line: mergeability, head, check counts, failing check names, unresolved review threads. |
| `.claude/skills/land-stacked-prs/sf_stack_status.sh [head-prefix]` | One line per open PR whose head branch starts with the prefix (default `agent/card-schema`): base, mergeable/merge-state, failing-check count, head, branch. |

Environment: `SF_REPO` (default `rmems/synthetic-factory`), `SF_REPO_ROOT` (default: the repo the skill
lives in), `CLAUDE_SESSION_URL`, `CLAUDE_TRAILER` (default `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`).
Requirements: `gh` authenticated as the repo owner, `python3`, the worktrees listed by `git worktree list --porcelain`.

## Procedure

### 0. Preflight: is this a GitHub native stack?

```bash
gh api "repos/rmems/synthetic-factory/stacks?per_page=50" --jq '.[] | "\(.number) open=\(.open) base=\(.base.ref) prs=\([.pull_requests[].number])"'
gh api repos/rmems/synthetic-factory/pulls/112 --jq '.stack'
```

If a PR carries a `stack` object: GitHub's stack feature merges into the stack's trunk (not necessarily
`main`), **auto-rebases the remaining branches after every merge** (the history rewriting the owner
forbids), and refuses base changes with "Cannot change the base branch because the pull request is part
of a stack". Have the **owner** dissolve each stack first (the auto-mode classifier blocks this call for
agents):

```bash
gh api --method POST repos/rmems/synthetic-factory/stacks/146/unstack
```

Then retarget the chain root to `main` with the GitHub plugin tool `update_pull_request` (`base: main`).
Do **not** delete the old base branch through `gh api -X DELETE .../git/refs/heads/...`: that closes
every dependent PR instead of retargeting them (recovery: push the backed-up SHA back to the branch name,
then reopen each PR with `update_pull_request state=open`). Always push a `backup/pr-<n>/<sha>` ref
before any branch deletion.

### 1. Simulate before touching anything

```bash
git fetch origin
git merge-tree --write-tree origin/main origin/agent/card-schema-70-queue-backpressure >/dev/null; echo "exit=$?"
git merge-tree --write-tree origin/main origin/agent/card-schema-52-websocket-reconnect | awk -F'\t' '/^[0-7]{6} /{print $2}' | sort -u
```

Exit 1 with conflicts only on files the squashed parent also changed (here `AGENTS.md`,
`pipelines/card_schema_validate.py`, `pipelines/card_schema_yaml.py`, `scripts/publish_grok46_hub.py`,
`tests/test_publish_grok46_hub.py`) is the phantom add/add pattern: take `main`'s bytes. Verify which
side is newer first (`git log -1 --format=%ci <sha>` on both sides) - in this session `main` was newer.

### 2. Integrate one PR when it becomes next

```bash
ART="AGENTS.md pipelines/card_schema_validate.py pipelines/card_schema_yaml.py scripts/publish_grok46_hub.py tests/test_publish_grok46_hub.py qodana.yaml"
.claude/skills/land-stacked-prs/sf_land_child.sh 131 $ART
```

The script aborts (exit 2/3) on a dirty worktree, a base that is not `main`, or a conflict outside the
listed files; those need a hand merge in the same worktree (keep the PR's own edits on top of `main`'s
bytes, e.g. #130's and #123's `card_schema_validate.py` changes). It prints the PR's own files after the
merge - for a card-schema PR that must be exactly its JSON declaration plus its test module.

### 3. Wait for the exact head, then triage

```bash
.claude/skills/land-stacked-prs/sf_wait_green.sh 131 119 125 113
gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved path line comments(first:1){nodes{databaseId author{login} body}}}}}}}' -F o=rmems -F r=synthetic-factory -F n=131 --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved==false) | "id=\(.comments.nodes[0].databaseId)\t\(.comments.nodes[0].author.login)\t\(.path):\(.line)\t\(.comments.nodes[0].body | gsub("<[^>]*>";"") | gsub("\n";" ") | .[0:200])"'
```

Classify each unresolved thread: (1) correctness / security / data-integrity / fail-closed defect in the
PR's own diff, (2) missing test for behaviour the PR claims, (3) already fixed on the exact head, (4)
analyzer hardening or style that broadens the PR, (5) contradicted by AGENTS.md or repo evidence. Fix
only 1 and 2, in one commit. Reply on the rest with the category, the evidence (`path:line`, sha, test
name) and the signature; never resolve bot threads yourself. Advisory gates (qlty similar-code across the
per-dataset tests, CodeScene) do not block a merge here: `main` has no branch protection.

### 4. Merge, then retarget the next child

Merge with the GitHub plugin tool `merge_pull_request` (`merge_method: squash`, title = PR title, body
with the exact head and check summary), then `update_pull_request` on the child with `base: main`, then
go back to step 2 for that child. Chains are file-disjoint, so roots of different chains can run in
parallel; only the two PRs that touched shared helpers (#130, then #123) needed a hand merge.

## Gotchas hit in this session

- **Stacked-PR CI is vacuous.** `python.yml` / `python-smoke.yml` trigger only on `pull_request` against
  `main`; the "8 green checks" on a stacked PR are bots. The integration push after retargeting is what
  runs the real suite.
- **Squashed parents recreate the phantom conflicts on every child.** Merge commits would avoid it, but
  the owner squashes; the script's take-main list is the compensating step.
- **`gh pr checks --watch` can exit before late checks register.** `sf_wait_green.sh` polls the rollup
  until nothing is pending and at least nine checks exist.
- **Co-author avatars vanish** when the commit message has blank lines after the trailer block; the
  trailer text is still there. Keep the trailers as the final paragraph with one trailing newline.
- **Cursor Cloud may push to a PR branch.** The script pulls `--no-rebase` first and re-reads the head
  after pushing; treat a moved remote as new commits to keep, never something to overwrite.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ABORT: base is 'agent/...', not main` | Parent not merged or child not retargeted yet; do step 4 first. |
| `ABORT: unexpected conflict in <file>` | Hand-merge in the PR's worktree: `git merge --no-ff --no-commit origin/main`, resolve keeping the PR's intent, run the checks, commit with the trailer, push. |
| PR closed after a base-branch deletion | Restore the ref from `backup/pr-*`, reopen with `update_pull_request state=open`, unstack, retarget. |
| `Cannot change the base branch because the pull request is part of a stack` | Owner unstacks (`POST .../stacks/<n>/unstack`), then retarget. |
| Commit rejected: "missing the Co-Authored-By attribution trailer" | The owner's hook; add the running model's trailer (also on merge commits). |
