---
name: plan-github-issue
description: Plan and file work as a beads issue with its GitHub twin (and Linear twin) sharing identical tags. Use when creating an issue, filing a bug/finding, planning work, or when asked to "create an issue", "file this", "add a bead", or "make a ticket" in this repo.
---

# Plan work as a bead + GitHub twin

In this repo an issue is **three linked objects**: a local bead (source of truth for
status/dependencies), a GitHub issue (public collaboration surface), and a Linear
issue (auto-mirrored). They must carry **the same domain tags**, or the twins drift.

Paths are relative to the repo root. Every command below is a **live check** — do
not trust a remembered answer, including the ones in this document.

## Prerequisites

This skill drives three external tools — `bd` (beads), `gh`, and `jq` — and every step
below assumes all three are on `PATH` and authenticated. That is **not** true of the
Cursor Cloud image: `.cursor/Dockerfile` installs git, sudo, Python, curl, and
certificates, and `.cursor/install.sh` does not install beads, `gh`, or `jq`, so step 1
fails with `bd: command not found` for a cloud agent starting from `AGENTS.md`. Check
before starting, and install what's missing (or run this skill locally) if the check
fails:

The same image lacks `gh`: `.cursor/Dockerfile` installs `curl` but not GitHub CLI.
Check the binary separately from authentication — folding them together reports "not
authenticated" for a missing binary and sends the operator to `gh auth login`, a command
they cannot run. `jq` is used throughout — label counting, parsing `--json` output — and
its absence otherwise fails loudly mid-workflow instead of at this gate:

```bash
command -v bd >/dev/null || echo "beads missing -- install it before running this skill"
command -v jq >/dev/null || echo "jq missing -- install it before running this skill"
if ! command -v gh >/dev/null; then
  echo "GitHub CLI missing -- install gh before running this skill"
elif ! gh auth status >/dev/null 2>&1; then
  echo "gh present but not authenticated -- run: gh auth login"
fi
```

Passing those two is **not** sufficient. The workflow below also calls `issue_write` and
`sub_issue_write`, which are GitHub MCP plugin tools, not `gh` subcommands — an agent
with working `bd` and `gh` can clear the gate above and still be unable to create or
link the twin. If that plugin is unavailable, every step has a `gh` equivalent:

| Plugin tool | `gh` equivalent |
| --- | --- |
| `issue_write` (create) | `gh issue create --title --body-file --label --assignee --milestone` |
| `issue_write` (update) | `gh issue edit <n> --title --body-file --add-label --remove-label --add-assignee --remove-assignee --milestone` |
| `sub_issue_write` (add) | `gh api --method POST repos/<o>/<r>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>` |
| `sub_issue_write` (replace parent) | `gh issue edit <n> --parent <parent-number>` (and `--remove-parent` to detach) |
| `pull_request_read` (`get_files`) | `gh pr list --repo <o>/<r> --state open --limit 200 --json number,files` |

Milestones need the empty case too: `gh issue edit <n> --milestone "<name>"` to set,
and `gh issue edit <n> --remove-milestone` when the bead has none — otherwise a
milestone removed from the bead survives on the twin and no step ever clears it.

`gh issue create` also takes `--blocked-by`, which mirrors the `bd dep add` edge onto
GitHub in the same call — but it takes GitHub issue numbers or URLs, **not bead IDs**.
Resolve each blocker to its own twin's issue number first (its `External:` ref, if it
has one); if a blocker bead has no twin yet, omit `--blocked-by` for it and rely on the
`bd dep add` edge alone until it does.

Assignees need the same add/remove treatment as labels — `gh issue edit` has
`--add-assignee` and `--remove-assignee`, and without them the post-sync
reconciliation can neither apply an assignable human owner nor clear a stale one, since
`bd github sync` does not set assignees. Remember the bead owner may be an agent
identifier, which is not a GitHub login: assign only a login the API confirms.

These are not exact equivalents for labels. `issue_write` **replaces** the label set;
`gh issue edit --add-label` only adds, so stale domain, `status:*`, or `priority:*`
labels survive and step 5 keeps reporting drift no matter how many times you run it.
Compute both directions and pass them together:

```bash
# The COMPLETE intended set: bead domain labels PLUS the tracking triplet. Both belong
# in $want -- gh issue edit --add-label/--remove-label only adds or removes individually
# (unlike issue_write, which replaces the whole set), so any label $have carries that is
# missing from $want -- including bead:*/status:*/priority:* -- lands in $del and gets
# stripped. Derive want_tracking here rather than assuming step 5 already set it: this
# fallback can run standalone, before step 5 ever executes.
want_tracking=$(bd show <bead-id> --json | jq -r '.[0] |
  "bead:\(.issue_type)", "priority:P\(.priority)", "status:\(.status | gsub("_";"-"))"')
want=$(printf '%s\n' \
  "$(bd show <bead-id> --json | jq -r '.[0].labels[]?')" \
  "$want_tracking" | grep -v '^$' | sort -u)
# Only reconcile labels this workflow manages. GitHub carries collaboration labels no
# bead will ever have -- this repo has size:S/M/L/XL/XXL, dataset-card, Documentation,
# GitHub Actions, release and others -- and treating every non-tracking label as a
# domain tag would delete them or push them back into the bead. Restrict $del to the
# managed vocabulary: labels some bead uses, plus the tracking prefixes.
# set -o pipefail, or the trailing `| sort -u` swallows a failed read: gh errors, sort
# succeeds on an empty stream, `have` comes back empty, and the reconciliation computes
# ZERO removals -- so a later successful edit adds the wanted labels while every stale
# one survives. Verified: without pipefail this assignment returns 0 for issue #999999.
set -o pipefail
have=$(gh issue view <n> --repo rmems/synthetic-factory --json labels --jq '.labels[].name' | sort -u) \
  || { echo "could not read current labels -- aborting rather than half-reconciling" >&2; exit 1; }
add=$(comm -23 <(printf '%s\n' "$want" | sort -u) <(printf '%s\n' "$have"))
# Name what to PRESERVE, not what is managed. Deriving the vocabulary from current bead
# labels leaves a hole: remove a label from its last bead and it stops being "managed",
# so the stale copy survives on the twin and the parity diff hides it -- reporting
# parity OK against real drift. Everything outside this list is ours to reconcile.
# Extend it when the repo gains another GitHub-only or bot-applied label.
PRESERVE_RE='^(size:|dataset-card$|Documentation$|GitHub Actions$|release$|development$|huggingface$|Amazon Q )'
del=$(comm -13 <(printf '%s\n' "$want" | sort -u) <(printf '%s\n' "$have") \
      | grep -Ev "$PRESERVE_RE")
# Join on newlines with paste, NOT `echo $x | tr ' ' ','`: label names may contain
# spaces (GitHub ships `good first issue`), and word-splitting would turn that one
# label into three bogus ones while leaving the real stale label in place.
gh issue edit <n> --repo rmems/synthetic-factory \
  ${add:+--add-label "$(printf '%s\n' "$add" | paste -sd,)"} \
  ${del:+--remove-label "$(printf '%s\n' "$del" | paste -sd,)"}
```

Provisioning beads *into* the cloud image is a change to shared infrastructure, out of
scope for this skill; file it separately rather than editing `.cursor/` from here.

## Order of operations (do not reorder)

Create the **bead first**, then the GitHub twin, then link them. Creating the GitHub
issue first produces an orphan with no bead metadata that later syncs will duplicate.

### 1. Gather the targets before writing anything

Find the parent epic, **if this work belongs under one**. A new top-level lane is
parentless and should stay that way. **Epics are usually `in_progress`, not `open`** —
filtering to `open` alone hides them and produces orphans:

```bash
# Include blocked and deferred: an epic in either state is still the right parent, and
# omitting it leads to filing the work parentless or under the wrong lane. `bd list`
# unions a comma list correctly (unlike `bd search --status`, which takes one value).
bd list --status=open,in_progress,blocked,deferred    # epics show as ◐ [epic]
bd show <parent-id>                    # confirm it is the right lane
```

Print the **complete** label vocabulary — there are ~43 distinct labels, so a
`most_common(15)` view hides real ones (`quality-gate`, `provenance`, `metadata`)
exactly when you are checking whether a label already exists:

```bash
bd list --json | python3 -c "
import json,sys,collections
d=json.load(sys.stdin)
c=collections.Counter(l for i in (d if isinstance(d,list) else d.get('issues',[])) for l in (i.get('labels') or []))
print(len(c),'labels'); [print(f'  {n:>3}  {k}') for k,n in sorted(c.items())]"
```

Reuse existing labels; do not invent near-synonyms (`curation` exists — do not add
`curating`). Labels **auto-create on use**, so a typo silently becomes vocabulary.

Milestones, and the convention siblings follow:

Use `gh api`, which authenticates internally. Never expand a token into a `curl -H`
argument: process arguments are world-readable on a shared runner, so `$TOKEN` in argv
leaks the credential for the life of the call.

```bash
gh api "repos/rmems/synthetic-factory/milestones?state=all" \
  --jq '.[] | "\(.number) \(.title)"'
```

Observed convention: curation / audit / training-readiness → *Synthetic Corpus
v0.1.0*; gate / generation / distillation → *Factory v0.2.0*. Pick the milestone your
**sibling issues** use, not the one that merely sounds right.

### 2. Create the bead

**Resume before creating.** If an earlier run died between `bd create` and the twin,
the bead already exists but has no marker on GitHub — so the step-3 search cannot find
it, and creating again yields two beads that can each acquire their own twin:

```bash
bd search "<a distinctive phrase from the title>"
```

A hit is not automatically *your* work. `bd search` already excludes closed beads by
default (`--status` help: "Default excludes closed"), so a stale finished bead will not
surface — but an open bead with a similar title may be different work, or the same work
already completed and linked. Reuse it only when it is an unfinished attempt at this
same request: same parent and same scope — see the table below for how to proceed
whether or not it already has an external ref.

`bd search` does not print the external ref at any verbosity — `--long` adds the
description, assignee, and labels only — so check each candidate with `bd show`:

```bash
bd search "<a distinctive phrase from the title>"          # candidate IDs
bd show <candidate-id> | grep -E '^External:' || echo "no twin yet -- resumable"
```

An existing `External:` ref does **not** mean the work finished. It is written in
step 4, and step 5 still has to reconcile labels and commit; a run that died in between
leaves a correct bead, a correct twin, and unreconciled tags. Creating a second bead
there is the worst outcome — it duplicates identity to avoid finishing three commands.
So the ref tells you *where* to resume, not whether to:

| `External:` | Same scope? | Action |
| --- | --- | --- |
| absent | yes | resume at step 3 (create the twin) |
| present | yes | reconcile issue state **and** post-sync metadata (below), then resume at step 5 — do **not** create |
| either | no | different work — create a new bead |

Scope, not the ref, is what decides whether this is your bead.

**Validate the ref before trusting it.** A linked resume edits an existing issue's body,
labels, milestone, and assignees. If `External:` is stale, mistyped, or points at
another repository or another bead's issue, that reconciliation overwrites someone
else's work. Confirm the target carries *this* bead's exact marker before touching it:

```bash
ref=$(bd show <bead-id> | sed -n 's/^External: //p')
case "$ref" in
  https://github.com/rmems/synthetic-factory/issues/*) ;;
  *) echo "External ref is not a synthetic-factory issue: $ref" >&2; exit 1 ;;
esac
n=${ref##*/}
# grep -qF (literal fixed-string), NOT a regex match: jq's test() treats the dot in an
# ID like sf-v46.2 as a wildcard, so an issue marked sf-v46X2 would pass an "exact"
# check and then get overwritten. Verified: test() returns true for that decoy, while
# both grep -qF and jq contains() return false.
body=$(gh issue view "$n" --repo rmems/synthetic-factory --json body --jq '.body // ""') \
  || { echo "could not read issue #$n -- aborting" >&2; exit 1; }
if printf '%s' "$body" | grep -qF "<!-- bead-id: <bead-id> -->"; then
  : # ours, proceed
elif ! printf '%s' "$body" | grep -qF "<!-- bead-id: "; then
  # No marker is CONSISTENT with the sync case but does not prove ownership: a stale
  # ref can point at any unrelated markerless issue, and the reconciliation that
  # follows rewrites body, labels, milestone and assignees. Require corroboration.
  title=$(gh issue view "$n" --repo rmems/synthetic-factory --json title --jq .title) \
    || { echo "could not read issue #$n title -- aborting" >&2; exit 1; }
  # Bracketed token, not a bare substring: bead IDs nest, so "sf-v46" occurs inside
  # "[sf-v46.2] ..." and would falsely claim a child's issue. Verified on that exact
  # pair -- the bare form matches, "[sf-v46]" does not.
  if printf '%s' "$title" | grep -qF "[<bead-id>]"; then
    echo "issue #$n is markerless but its title names this bead -- reconcile (adds the marker)"
  else
    echo "issue #$n is markerless AND its title does not name <bead-id>." >&2
    echo "Ownership unproven -- do NOT overwrite. Confirm manually, or clear the stale" >&2
    echo "External ref and re-run the exact-marker search." >&2
    exit 1
  fi
else
  echo "issue #$n is marked for a DIFFERENT bead -- stop and reconcile" >&2; exit 1
fi
```

Distinguish **missing** from **conflicting**. A `bd github sync` run that wrote
`External:` and died before the body update leaves a twin with no marker at all — that
is the documented partial-failure state below, and the exact-marker search cannot
recover it either, because the marker is precisely what is absent. Rejecting it
outright makes that recovery path unreachable. A marker belonging to *another* bead is
the real conflict, and still stops. `grep -qF` compares literally, so a dotted ID like
`sf-v46.2` is not a regex; `.body // ""` keeps a null body from erroring instead of
reporting an absent marker.

A linked resume skips step 3, which is also where post-sync metadata reconciliation
lives. If the earlier run died after `bd github sync` wrote the ref but before that
reconciliation, the twin keeps `bd`'s generated body — with **no `<!-- bead-id: -->`
marker** and no milestone — and step 5 only touches labels, so the gap becomes
permanent and the twin stays invisible to every marker-based search. Re-run the
marker/milestone check from step 3 before parity:

```bash
gh issue view <n> --repo rmems/synthetic-factory --json body,milestone \
  --jq '{marker: ((.body // "") | contains("<!-- bead-id: ")), milestone: (.milestone.title // "none")}'
```

The reopen check lives in step 3 too — so on this path the
twin's state is never examined. A bead closed or reopened after the ref was written
leaves the twin out of sync, and step 5 only touches labels, so it would write an
accurate `status:*` label onto an issue in the wrong state. Check state before parity,
in both directions:

```bash
bd_state=$(bd show <bead-id> | head -1 | sed -n 's/.*· \([A-Z_]*\)\].*/\1/p')
gh_state=$(gh issue view <n> --repo rmems/synthetic-factory --json state --jq .state)
# bead not CLOSED but issue closed  -> gh issue reopen <n> --repo rmems/synthetic-factory
# bead CLOSED but issue open        -> gh issue close  <n> --repo rmems/synthetic-factory
echo "bead=$bd_state issue=$gh_state"
``` Note `bd search --status` takes **one** value, unlike
`bd list`: a comma list silently returns nothing rather than erroring.

If the hit really is an unfinished attempt, reuse that ID instead of creating — but
**finish its setup before moving on**. A run that died mid-step-2 may have created the bead and
nothing else, so re-check the parts that come after `bd create` (labels, `--parent`,
and especially the `bd dep add` blockers below) rather than jumping straight to step 3
and leaving the dependency graph permanently incomplete:

```bash
bd show <bead-id>        # confirm labels, parent, and dependency edges are all present
```

```bash
bd create "<title>" \
  --type=<bug|feature|task|epic|chore|decision> --priority=<0-4> \
  [--parent=<parent-bead-id>] \
  [--assignee="<owner>"] \
  --labels="synthetic-factory,curation,audit,..." \
  --description "..." --design "..." --acceptance "..." --notes "..."
```

- **`--assignee` is optional — derive it from who owns the work.** Most beads here are
  unassigned (11 of 18 at last check) and several are agent-owned (`agent:Ramanujan`,
  `agent:Nietzsche`, `codex/gpt-5.6-sol max`). Assign a human only when a human asked
  for it; omit the flag when ownership is undecided, and use the agent's identifier
  when an agent owns the lane. Do not default every bead to the repo owner.
  **The bead assignee is not the GitHub assignee.** Agent identifiers are not GitHub
  logins — `GET /repos/.../assignees/agent:Ramanujan` returns 404, so passing one as a
  GitHub `assignees` value fails. Carry the agent in the body's **Assigned agent** line
  and set `assignees` only for a login the API confirms is assignable:

  ```bash
  gh api "repos/rmems/synthetic-factory/assignees/<login>" --silent && echo assignable
  ```

- **`--parent` is optional too.** A new top-level lane has no parent — both `sf-c5l`
  and `sf-v46` are parentless epics. Omit the flag (and the body's **Parent bead**
  line) rather than inventing an unrelated parent to satisfy the example.
- **Derive `--type` and `--priority` from the work, not from this example.** A defect
  is `bug`; new capability is `feature`; routine work is `task`; a lane spanning
  several issues is `epic`; a choice to record is `decision`. `--priority` takes `0-4`
  (0 = highest), **not** `high`/`medium`/`low` — reserve `0`/`1` for things that block
  a release or corrupt data, and default to `2`.
- `--parent` makes it a hierarchical child **and inherits the parent's labels**.
  **Decide inheritance now — `--no-inherit-labels` is a create-time flag.** If the
  parent's domain tags do not all apply to this child, pass `--no-inherit-labels`
  on this `bd create` and list the child's own `--labels` explicitly. Discovering
  the drift later, at the step-5 parity check, is too late: the flag no longer
  applies and the only remedy is removing tags one at a time on both surfaces.
- Put measured evidence in `--design`, blast radius and coordination in `--notes`.

**Record blockers in the dependency graph, not just in prose.** `--parent` expresses
hierarchy only. The bead is the declared source of truth for dependencies, so a blocker
mentioned only in the GitHub `Relationships` section is invisible to `bd blocked`,
`bd ready`, and every status query:

```bash
bd dep add <bead-id> --blocked-by <blocking-bead-id>
bd show <bead-id> | grep -iA2 'depend\|block'      # confirm the edge landed
```

Mirror it in the twin body's **Blocked by / blocks** line so both surfaces agree.

### 3. Create the GitHub twin

**First check whether a twin already exists.** A previous run may have created the
issue and then failed before `--external-ref` landed, so the bead looks unlinked while
the issue is already there. Creating "the" twin at that point makes a second one:

**Query loosely, filter exactly.** Do not put the `<!-- -->` delimiters in the *query*:
GitHub's search tokenizer drops that punctuation, so `--match body "<!-- bead-id: X -->"`
returns **zero hits for every bead** and the guard reports "safe to create" every time —
the precise duplicate it exists to prevent. Verified against issue #33, which carries the
marker: the delimited query finds nothing, `bead-id: sf-v46.2` finds it. Search on the
undelimited form and let the Python post-filter enforce the complete marker.

`gh search issues` fetches only **30 results by default**, so the exact-marker twin can
fall outside the returned page whenever a bead ID appears in many bodies — a parent ID
matches every child's marker and every child's *Parent bead* line. The post-filter would
then report "safe to create" and you would file a duplicate. Raise `--limit` so the
filter sees every candidate. Do not add `--state all` — `gh search issues` accepts only
`{open|closed}` there and errors out; omitting the flag already searches both.

Search the **complete** marker, closing delimiter included. A bare `bead-id: sf-v46`
also matches its children's `<!-- bead-id: sf-v46.2 -->`, which would "find" a twin
that belongs to a different bead and link the wrong issue:

```bash
bd show <bead-id> | grep External          # empty is not proof; also search GitHub
gh search issues --repo rmems/synthetic-factory --limit 200 \
  --match body "bead-id: <bead-id>" --json number,title,body \
  | python3 -c "
import json,sys
LIMIT=200
rows=json.load(sys.stdin)
if len(rows) >= LIMIT:
    sys.exit(f'STOP: search returned {len(rows)} candidates, hitting the --limit cap -- '
             f'the exact-marker twin may be outside this page; paginate before trusting the result')
want='<!-- bead-id: <bead-id> -->'
hits=[i['number'] for i in rows if want in (i.get('body') or '')]
if len(hits) > 1: sys.exit(f'STOP: {len(hits)} twins share this marker: {hits} -- reconcile before linking')
print(hits[0] if hits else 'no exact-marker twin; safe to create')"
```

Require **exactly one**. Earlier failed runs can leave two issues carrying the same
marker; treating that as "a twin exists" links one and leaves the duplicate live,
breaking the exactly-once identity the whole workflow rests on. The filter above stops
rather than guessing. **Closing the extras does not clear it**: the search deliberately
omits `--state`, so it spans open and closed alike — issues #2 and #3 in this repo are
closed and still surface in a marker search — and a closed duplicate keeps its marker
and stays in `hits` forever. Remove or rewrite the marker in the duplicate's body (then
close it if you like), and re-run.

If exactly one exact-marker twin exists, skip creation and jump to step 4 to link it —
but **read its state first**. A twin closed independently while the bead stayed active
leaves the public collaboration surface shut, and step 5 only reconciles labels, so an
accurate `status:open` label would sit on a closed issue:

```bash
bd_state=$(bd show <bead-id> --json | jq -r '.[0].status')
gh_state=$(gh issue view <n> --repo rmems/synthetic-factory --json state --jq .state)
# Reconcile in BOTH directions -- step 5 only touches labels, so either mismatch
# would leave an accurate status:* label on an issue in the wrong state:
#   bead not closed, issue CLOSED -> gh issue reopen <n> --repo rmems/synthetic-factory
#   bead closed,     issue OPEN   -> gh issue close  <n> --repo rmems/synthetic-factory
echo "bead=$bd_state issue=$gh_state"
```

Then check
the sync path live rather than assuming — `bd` accepts either the split
`github.owner` / `github.repo` keys or the combined `github.repository`, so probing
one key alone reports a configured integration as unset:

`bd config get` **exits 0 even for an unset key** and prints the literal string
`github.owner (not set)`, so a plain `cmd || fallback` chain never reaches its
fallback — it reports every install as configured. Probe by *value*, filter that
sentinel, and check all three keys plus the environment overrides:

A *lone* half is not a usable destination: `github.repo` without `github.owner` gives
`bd` nowhere to push. Require both split keys together, or the combined key on its own:

```bash
bd_cfg() { bd config get "$1" 2>/dev/null | grep -v '(not set)' | tr -d '[:space:]'; }

bd_configured() {
  [ -n "$(bd_cfg github.repository)" ] && return 0
  # This checkout documents the split pair as github.org + github.repo
  # (.beads/config.yaml, "Non-secret keys"). Accept github.owner as well:
  # installations differ, and missing github.org reads a valid setup as unset.
  { [ -n "$(bd_cfg github.org)" ] || [ -n "$(bd_cfg github.owner)" ]; } \
    && [ -n "$(bd_cfg github.repo)" ] && return 0
  [ -n "${GITHUB_REPOSITORY:-}" ] && return 0
  { [ -n "${GITHUB_ORG:-}" ] || [ -n "${GITHUB_OWNER:-}" ]; } \
    && [ -n "${GITHUB_REPO:-}" ] && return 0
  return 1
}
```

A destination is not a credential. `.beads/config.yaml` names `github.token` (env:
`GITHUB_TOKEN`) as the sync credential, and a working `gh auth login` does **not**
supply it — `gh` keeps its token in its own store, which `bd` does not read. The common
case of authenticated `gh`, configured owner/repo, and no beads token would select sync
and fail *after* the bead exists, when the direct fallback would have worked. Require
both:

```bash
TARGET_REPO=rmems/synthetic-factory

bd_destination() {   # normalized owner/repo, however it is configured
  local combined split_owner split_repo
  combined=$(bd_cfg github.repository); [ -n "$combined" ] || combined=${GITHUB_REPOSITORY:-}
  if [ -n "$combined" ]; then printf '%s' "$combined" | tr 'A-Z' 'a-z'; return; fi
  split_owner=$(bd_cfg github.owner); [ -n "$split_owner" ] || split_owner=$(bd_cfg github.org)
  [ -n "$split_owner" ] || split_owner=${GITHUB_OWNER:-${GITHUB_ORG:-}}
  split_repo=$(bd_cfg github.repo); [ -n "$split_repo" ] || split_repo=${GITHUB_REPO:-}
  [ -n "$split_owner" ] && [ -n "$split_repo" ] \
    && printf '%s/%s' "$split_owner" "$split_repo" | tr 'A-Z' 'a-z'
}

bd_can_sync() {
  # A configured destination is not necessarily THIS destination. A stale
  # github.repository or GITHUB_REPOSITORY inherited from another checkout would send
  # the twin to that repo while every gh command here targets TARGET_REPO.
  [ "$(bd_destination)" = "$(printf '%s' "$TARGET_REPO" | tr 'A-Z' 'a-z')" ] || return 1
  { [ -n "$(bd_cfg github.token)" ] || [ -n "${GITHUB_TOKEN:-}" ]; } || return 1
  # --dry-run, NOT --help: --help succeeds on any install and proves nothing. --dry-run
  # resolves the real configuration -- it is what reveals that sync requires
  # github.owner specifically and rejects a github.org-only setup, which a key-presence
  # check would happily pass.
  bd github sync --dry-run --issues <bead-id> >/dev/null 2>&1
}
```

If `bd_can_sync` succeeds, prefer `bd github sync --push-only --issues <id>`.
If it fails, create the twin directly with the plugin — and do **not** configure it
just to file one issue, because a bare `bd github sync` pushes *every* bead and will
spam the tracker while other agents are working.

**The sync path does not satisfy the metadata contract — reconcile after it.** `bd`
renders its own body and sets no milestone; `.beads/config.yaml` carries no milestone,
body, or template mapping, so a synced twin arrives without the `<!-- bead-id: -->`
marker, without a milestone, and without the house sections that
`docs/superpowers/specs/2026-08-18-public-repositories-and-hf-collection-design.md`
requires. A missing marker is not cosmetic: the step-3 duplicate search and every
reconciliation key on it, so the twin becomes invisible to them. After syncing, apply
the same metadata you would have passed to `issue_write`:

```bash
gh issue view <n> --repo rmems/synthetic-factory --json body \
  --jq '.body | test("<!-- bead-id: ")' # false -> body needs the template below
```

Then `issue_write` (`method: update`) with the full body template, `milestone`,
`assignees`, **and the title**. Rebuild the body from the current bead rather than
editing labels alone: the template's **Local status** and **Priority** lines are
plain text, so a bead whose status or priority changed after filing leaves the twin
showing `status:blocked` as a label and `open` in its own metadata. The label check in
step 5 cannot see that — it never reads the body. A bead renamed after its twin was filed leaves the
issue on its old title, which then no longer matches the required
`[<bead-id>] <title>` format — and nothing else in the workflow reads or repairs it:

```bash
want_title="[<bead-id>] $(bd show <bead-id> --json | jq -r '.[0].title')"
have_title=$(gh issue view <n> --repo rmems/synthetic-factory --json title --jq .title)
[ "$want_title" = "$have_title" ] || echo "title drift: want [$want_title] have [$have_title]"
``` Do this before step 4 so the parity check in step 5 sees the final state.

**Provision repository labels first.** Assigning a label never creates it — `gh label
create` is a separate command, and `issue_write` cannot provision one — so a bead
carrying a label the repo lacks either fails the call or silently lands without it, and
the step-5 parity check can never repair that by re-running `issue_write`. This is live,
not hypothetical: 12 bead labels have no repository counterpart right now (`authz`,
`coverage`, `dpo`, `factory`, `infra-as-code`, `log-redaction`, `mdb`, `mill`,
`multi-agent-coordination`, `qodana`, `review`, `sandbox-refusal`). The tracking triplet needs this too — it is assigned in the same call, and the repo has
only a subset today (`bead:` bug/epic/task, `priority:` P0-P2, `status:` open and
in-progress). The first `bead:feature`, `priority:P3`, or `status:blocked` bead has no
label to attach to. Include the triplet from step 5 in the diff, not just domain labels.

Diff before filing — include the tracking triplet, not just domain labels, or the first
`bead:feature`/`priority:P3`/`status:blocked` bead silently has nothing to attach to:

```bash
want_tracking=$(bd show <bead-id> --json | jq -r '.[0] |
  "bead:\(.issue_type)", "priority:P\(.priority)", "status:\(.status | gsub("_";"-"))"')
comm -23 <(printf '%s\n' \
            "$(bd show <bead-id> | sed -n 's/^LABELS: //p' | tr ',' '\n' \
                | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | grep -v '^$')" \
            "$want_tracking" | grep -v '^$' | sort -u) \
         <(gh label list --repo rmems/synthetic-factory --limit 200 --json name \
            --jq '.[].name' | sort -u)
# any output -> create each one before issue_write:
# gh label create "<name>" --repo rmems/synthetic-factory --description "..."
```

Title format: `[<bead-id>] <title>`. Set `assignees`, `milestone`, and `labels` in the
same `issue_write` call. Body template — the `<!-- bead-id: -->` marker is **required**
by `docs/superpowers/specs/2026-08-18-public-repositories-and-hf-collection-design.md`
and is what marker-based duplicate checks and reconciliation key on:

```text
<!-- bead-id: sf-xxx -->

## Bead metadata
- **Bead:** `sf-xxx`
- **Type:** `<type>`
- **Local status:** `<status>`
- **Priority:** `P<n>`
- **Estimate:** `<minutes>` or _not estimated_
- **Assigned agent:** `<assignee>` — omit this line entirely when unassigned
- **Parent bead:** `sf-yyy` — <parent title>
- **Blocked by / blocks:** `<bead-ids>` — omit when there are none
- **Spec:** `docs/superpowers/specs/<file>.md` — omit when the bead has no `Spec:` line
- **Repository:** https://github.com/rmems/synthetic-factory

## Objective
## Evidence
## Design
## Acceptance criteria
## Scope boundaries        <- what this does NOT fix
## Relationships           <- parent bead, related issues, PR coordination
## Tracking contract       <- copy verbatim from an existing issue
## Agent                   <- who filed it, and that the Linear twin is automatic
```

### 4. Link the bead back

**If this bead has a parent, create the native sub-issue link first.** `--parent`
establishes the hierarchy in `bd` only; GitHub does not learn it, so the twin renders
as an unrelated top-level issue unless `sub_issue_write` is called explicitly:

Both halves of this lookup must tolerate a half-finished earlier run — the same
partial-failure step 3 already handles for the child:

```bash
# Parent twin: an empty External ref is NOT proof the parent has no twin. A run may
# have created it and died before saving the ref, so fall back to the marker search.
# And a NON-empty ref is not proof either: validate it carries the parent's own exact
# marker, exactly as the child's ref is validated in step 3. An unvalidated stale ref
# means linking the child under an unrelated issue and then editing that issue's
# checklist body. Same contains() rule -- test() would treat a dotted ID as a regex.
# Require exactly one, same as the child guard in step 3: sub_issue_write takes a
# single issue_number, so several marker-sharing candidates would mean picking one
# arbitrarily and hanging the hierarchy off a duplicate.
bd show <parent-bead-id> | grep External
gh search issues --repo rmems/synthetic-factory --limit 200 \
  --match body "bead-id: <parent-bead-id>" --json number,body \
  | python3 -c "
import json,sys
LIMIT=200
rows=json.load(sys.stdin)
if len(rows) >= LIMIT:
    sys.exit(f'STOP: search returned {len(rows)} candidates, hitting the --limit cap -- '
             f'the exact-marker parent twin may be outside this page; paginate before trusting the result')
want='<!-- bead-id: <parent-bead-id> -->'
hits=[i['number'] for i in rows if want in (i.get('body') or '')]
if len(hits) > 1: sys.exit(f'STOP: {len(hits)} parent twins share this marker: {hits} -- reconcile first')
print(hits[0] if hits else 'no parent twin')"

# If bd show DID yield a ref, verify that issue before trusting it:
gh issue view <parent-n> --repo rmems/synthetic-factory --json body \
  --jq '((.body // "") | contains("<!-- bead-id: <parent-bead-id> -->"))' | grep -qx true \
  || { echo "parent ref does not carry the parent's marker -- reconcile before linking" >&2; exit 1; }

# Child: if a previous run already added the link and died before --external-ref,
# adding again is rejected and the retry can never get past this point.
# Three outcomes: "none" -> add it; the intended parent -> already done, skip;
# any other number -> wrong parent, re-add with replace_parent=true.
# Compare the parent's IDENTITY, not just its presence: a child linked to the WRONG
# parent also reports a parent, and skipping on that permanently leaves GitHub
# disagreeing with --parent.
# The parent is NOT a field on the issue object -- that object carries only
# sub_issues_summary, so '.parent.number' reads "none" even for a linked child and the
# check never fires. Use the dedicated endpoint; its 404 IS the unparented case.
# Ask for the parent FIELD rather than probing the endpoint and interpreting its error
# text. The REST contract documents only "404 Resource not found", so matching on the
# body wording couples this to undocumented strings; and gh exits 1 for any reason, so
# a 5xx, rate limit, or dropped connection would otherwise read as "no parent" and the
# workflow would add a link that may already exist. This form yields "none" for a
# genuinely unparented issue and exits nonzero on a real read failure.
PARENT=$(gh issue view <n> --repo rmems/synthetic-factory --json parent \
           --jq '.parent.number // "none"') \
  || { echo "parent lookup failed -- not assuming unparented" >&2; exit 1; }
echo "$PARENT"
```

The two arguments are **not the same kind of number**. `issue_number` is the parent's
issue number; `sub_issue_id` is the child's *database* ID, which the API states is
"not the same as issue number" — issue #33 is number `33` but database ID
`5215296227`. Passing the number silently targets an unrelated object, and neither the
inventory from step 1 nor an `External` ref carries the ID, so fetch it:

```bash
CHILD_ID=$(gh api repos/rmems/synthetic-factory/issues/<n> --jq .id)   # NOT <n>
```

Then call `sub_issue_write` (`method: add`) with the parent's issue number as
`issue_number` and `$CHILD_ID` as `sub_issue_id`.

**The native link is not the whole contract.** The design spec requires the epic to
carry a checklist linking its children ("The epic contains a checklist linking all
seven child issues"), and `sub_issue_write` does not touch the parent's body — so a
child can be correctly parented and still be missing from the checklist a human reads.
Append it and verify:

```bash
# Anchor to a checklist LINE, not a substring: a bare `grep -F "#12"` also matches
# "#123" and any passing mention outside the list, and would silently skip a required
# update. `([^0-9]|$)` stops the prefix match.
# Read first, THEN test. Piping straight into grep makes a failed read -- auth, rate
# limit, network, bad parent number -- indistinguishable from "entry absent", and the
# operator would then rewrite a parent body they never retrieved. Verified: the piped
# form reports "missing" for issue #999999, which does not exist.
parent_body=$(gh issue view <parent-n> --repo rmems/synthetic-factory --json body --jq .body) \
  || { echo "could not read parent #<parent-n> -- aborting, do NOT rewrite its body" >&2; exit 1; }
printf '%s\n' "$parent_body" \
  | grep -qE '^[[:space:]]*-[[:space:]]*\[[ x]\][[:space:]]*#<n>([^0-9]|$)' \
  || echo "child #<n> missing from the epic checklist -- add it"
# then: gh issue edit <parent-n> --repo rmems/synthetic-factory --body-file <updated>
``` This applies equally on the resumed
path, where step 3 found an existing twin and kept only its number. Without a parent
twin, fall back to the body's **Relationships** section, as the gotcha below describes.

```bash
bd update <bead-id> --external-ref "https://github.com/rmems/synthetic-factory/issues/<n>"
bd show <bead-id> | grep -E 'External|LABELS'
```

**If this bead has no parent, check the twin doesn't have one either.** A resumed twin
(step 3) may carry a parent link from an earlier hierarchy that no longer applies, and
`sub_issue_write` is never called for a parentless bead, so nothing detaches a stale link
on its own:

```bash
PARENT=$(gh issue view <n> --repo rmems/synthetic-factory --json parent \
           --jq '.parent.number // "none"') \
  || { echo "parent lookup failed -- not assuming unparented" >&2; exit 1; }
if [ "$PARENT" != "none" ]; then
  echo "twin has stale parent #$PARENT but bead is parentless -- detach:"
  echo "gh issue edit <n> --repo rmems/synthetic-factory --remove-parent"
fi
```

`bd` writes through to `.beads/issues.jsonl` (an export of the Dolt backend, not the
source of truth). Committing that export is how other agents see the mapping — but it
is **shared mutable state**: it frequently arrives already-modified or already-staged
from another session, and sweeping it into an unrelated commit is a real collision.
Either commit it alone, or leave it and say so:

```bash
# Diff against HEAD, not the index. `git diff -- <path>` compares the worktree to the
# INDEX, so a change another session already staged is invisible here -- while the
# pathspec commit below records the full worktree file and ships their bead too. That
# is the collision this section exists to prevent, and the plain diff hides it.
git diff HEAD -- .beads/issues.jsonl   # confirm only YOUR bead changed
# Pathspec-scoped: commits ONLY this file even when other paths are staged.
# A plain `git commit` would record the whole index — the exact collision
# this section warns about.
git commit -m "chore: link <bead-id> to GitHub issue #<n>" -- .beads/issues.jsonl
```

**Never** let it ride along in a feature commit. Check `git status` before committing:
if it is already staged, unstage it first (`git restore --staged .beads/issues.jsonl`),
then re-run the `git diff HEAD` check above — unstaging changes what the index holds
but not what the worktree file contains, so the other session's edits can still be
sitting in it. If that diff shows rows you did not write, stop and leave the file
alone rather than committing on their behalf.

### 5. Enforce tag parity (the step people skip)

Parity means the **domain labels** match. GitHub additionally carries tracking labels
(`bead:*`, `status:*`, `priority:*`) that have no bead equivalent — those are expected
to differ and are not part of the comparison.

`--parent` **silently inherits** the parent's labels, so the bead can end up with
domain tags the GitHub issue lacks. Diff and reconcile:

Read **both** sides — printing only the bead's labels leaves you comparing against a
remembered value, and step 3 may have resumed an existing twin or let `bd github sync`
create one, so the GitHub side is not necessarily what you last set:

Normalize both sides before comparing — `bd` prints a `LABELS:` prefix, trailing space included, that `gh` does
not, so the raw outputs never match even when the label sets are identical:

```bash
# Defined again here (also set in the Prerequisites gh fallback above) so parity does
# not depend on having taken that path -- an unset PRESERVE_RE makes grep -Ev "" match
# everything and silently hides every domain label from the diff below.
PRESERVE_RE='^(size:|dataset-card$|Documentation$|GitHub Actions$|release$|development$|huggingface$|Amazon Q )'

# Capture the GitHub read into a variable and check it explicitly. Piping
# `gh issue view` straight into the diff's process substitution makes a read failure
# (auth, rate limit, network) indistinguishable from "issue genuinely has zero labels" --
# diff would then report ordinary drift instead of aborting on an unobserved state.
gh_labels=$(gh issue view <n> --repo rmems/synthetic-factory --json labels --jq '.labels[].name') \
  || { echo "could not read current labels -- aborting rather than reporting false drift" >&2; exit 1; }

diff <(bd show <bead-id> | sed -n 's/^LABELS: //p' | tr ',' '\n' \
       | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sort) \
     <(printf '%s\n' "$gh_labels" \
       | grep -Ev '^(bead|status|priority):' \
       | grep -Ev "$PRESERVE_RE" | sort) \
  && echo "parity OK"
```

The `grep -Ev` drops the GitHub-only tracking triplet. Empty diff means parity; any
line printed is the drift to reconcile.

That filter proves nothing *about* the triplet, though — it hides it. A twin missing
`bead:*`, or carrying a `status:*`/`priority:*` left over from before an update, still
prints `parity OK`. The triplet is required and must be accurate, so derive it from the
bead and check it separately. All three values come from `bd show`'s header line.

Translate `_` to `-`. `bd` reports `IN_PROGRESS` but this repo's label is
`status:in-progress`, so an underscore form reports false drift on every in-progress
bead and makes the provisioning step below create a duplicate label. Verified live on
`sf-c5l`/#1.

Anchor **both** values to the `[● P<n> · STATUS]` suffix. A first-match `grep -oE
'P[0-4]'` reads the title too, so a P2 bead called "Audit P0 policy" derives
`priority:P0` and the reconciliation then overwrites a correct GitHub label with the
wrong one. Verified: that exact header yields `P0` unanchored, `P2` anchored.

Read the status **positionally**, not from an allowlist. This `bd` accepts seven —
`open, in_progress, blocked, deferred, closed, pinned, hooked` (confirmed via
`bd list --status=bogus`, which prints the valid set). A three-value regex leaves
`status:` empty for four of them, which reports false drift and, if fed back into a
reconcile, would replace a correct label with a bare `status:`.

```bash
# Read the FIELDS, do not parse the header line. Header parsing produced a defect in
# four separate passes: a three-value status allowlist, an underscore where the repo
# uses a hyphen, a first-match P[0-4] that picked up a "P0" in the title, and a greedy
# separator match that returned "OPEN]" as the title. --json has none of those hazards.
want_tracking=$(bd show <bead-id> --json | jq -r '.[0] |
  "bead:\(.issue_type)", "priority:P\(.priority)", "status:\(.status | gsub("_";"-"))"')

diff <(printf '%s\n' "$want_tracking" | sort) \
     <(gh issue view <n> --repo rmems/synthetic-factory --json labels --jq '.labels[].name' \
        | grep -E '^(bead|status|priority):' | sort) \
  && echo "tracking triplet OK"
```

`issue_write` **replaces** the label set, so pass the complete list: every domain label,
the tracking triplet, **and** the issue's current collaboration labels (anything
matching `$PRESERVE_RE` — `size:*`, `dataset-card`, `Documentation`, etc.). Fetch those
from `gh issue view <n> --json labels` before calling `issue_write`; omitting them
silently deletes labels this workflow does not own. If the drift you find here is
*inherited* parent tags, note that `--no-inherit-labels` cannot help at this point — it
applies only at `bd create` (step 2). Reconcile by removing the unwanted tags on both
surfaces.

**Commit the bead side again if you changed it here.** Step 4's focused commit is the
workflow's only metadata commit, and it runs *before* this reconciliation. Any `bd`
label fix you make now rewrites `.beads/issues.jsonl` after that commit, so the export
other agents read stays stale and the source of truth silently diverges. Close the
workflow with a second focused commit, same pathspec discipline:

```bash
# empty -> nothing to do (HEAD, not the index: see step 4 -- the plain form hides
# another session's staged rows and you would commit them)
if [ -n "$(git diff HEAD -- .beads/issues.jsonl)" ]; then
  git commit -m "chore: reconcile <bead-id> labels" -- .beads/issues.jsonl
else
  echo "no label changes to commit"
fi
```

## Concurrency

Several agents work this repo at once, so two steps above are races, not just sequences.
Neither has a true lock available — `bd` offers no create-time claim on work that does
not exist yet, and `gh issue edit` replaces a body with no compare-and-swap — so these
are **detect-and-converge** mitigations, not prevention. Treat them as such.

- **Resume search → `bd create` (step 2).** Two agents can both search, both find
  nothing, and both create a bead for the same request. The later exact-marker guard
  cannot catch it: the beads have different IDs, so their twins carry different markers
  and each looks unique. Mitigation: immediately after `bd create`, re-run the step-2
  search and confirm exactly one bead matches. If two exist, close the newer with
  `bd close <id> --reason="duplicate of <other>"` *before* creating any twin —
  reconciling beads is cheap, reconciling twins is not.
- **Epic checklist replacement (step 4).** `--body-file` writes a whole body, so two
  agents appending different children can each read the same parent body and the second
  write erases the first child's line. A pure entry *count* cannot catch this: if agent A
  appends child A and agent B concurrently overwrites with child B instead, the total
  count is unchanged even though A's entry is gone. Mitigation: capture the exact set of
  issue numbers you saw before writing (plus your own), then after writing confirm every
  one of them is still present — not just that the count didn't drop.

```bash
# before writing, capture what you saw (including the child you are about to add)
expect=$(printf '%s\n%s\n' "$parent_body" "#<n>" \
  | grep -oE '#[0-9]+' | tr -d '#' | sort -un)

# after any parent-body write, confirm every expected entry survived -- comparing the
# SET, not the count, catches an equal-count substitution a count check would miss
after=$(gh issue view <parent-n> --repo rmems/synthetic-factory --json body --jq .body \
  | grep -oE '#[0-9]+' | tr -d '#' | sort -un)
comm -23 <(printf '%s\n' "$expect") <(printf '%s\n' "$after")
# any output -> those children were clobbered by a concurrent write; re-add them
```

## Gotchas

- **`bd edit` opens `$EDITOR` and hangs an agent.** Use `bd update --title/--description/--notes`.
- **Do not hand-file a Linear twin.** Mirroring is automatic; issue bodies say so
  explicitly. Your job is only to make the tags correct at the source.
  **But say what you actually checked.** Step 5 compares the bead and the GitHub issue
  and nothing else, so it cannot report on Linear: if mirroring is disabled, lagging, or
  rejects a label, parity still passes. This checkout cannot even observe it —
  `linear.team_id` is unset and `bd` reports Linear has never been pulled. Treat the
  verified contract as bead ↔ GitHub, and describe the Linear twin as expected rather
  than confirmed. Where Linear *is* configured, verify it before claiming three-way
  parity:

  ```bash
  if bd config get linear.team_id | grep -qv '(not set)'; then
    bd linear sync --pull \
      || { echo "Linear IS configured but sync failed -- do not report parity, investigate" >&2; exit 1; }
    bd show <bead-id> | grep -i linear
  else
    echo "Linear not configured here -- parity claim covers bead <-> GitHub only"
  fi
  ```

- **ProjectsV2: query before concluding.** At the last check this repo had none, but
  that is a snapshot, not a fact — never report "no project" without running:

  ```bash
  gh api graphql -f query='query($o:String!,$r:String!){repository(owner:$o,name:$r){
    projectsV2(first:100){nodes{number title closed}}}}' \
    -F o=rmems -F r=synthetic-factory \
      --jq '.data.repository.projectsV2.nodes | map(select(.closed == false))'
  ```

  The query already selects `closed`, so filter on it — a historical or archived board is
  not a destination, and treating any nonempty result as one files new work onto a closed
  project. Only report a no-op when the *open*-filtered query is empty.
- **Sub-issue relationships need both twins on GitHub.** `sub_issue_write` links by
  database ID, not issue number. An empty `bd show <parent> | grep External` does
  **not** establish that the parent has no twin — a run can create one and die before
  saving the ref — so run the exact-marker search from step 4 before falling back.
  Only when that search also comes back empty should you record the parent in the
  body's **Relationships** section instead.
- **Check for PR collisions before filing a code fix.** If the issue touches a file an
  open PR also modifies, name that PR under **Relationships**. Compare with
  `pull_request_read` `method: get_files`.

## Quality bar for the body

File findings from **measured output, not inspection**. An issue that says "X appears
to be broken" costs a reader the whole investigation again. Include the command or
harness, the variants tried, and a results table. Then state **Scope boundaries**
honestly: what clearing this issue does *not* unlock.

If the finding contradicts something previously reported, say so and correct the
original with a comment on the stale issue.
