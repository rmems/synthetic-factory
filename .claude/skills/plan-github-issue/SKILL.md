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

## Order of operations (do not reorder)

Create the **bead first**, then the GitHub twin, then link them. Creating the GitHub
issue first produces an orphan with no bead metadata that later syncs will duplicate.

### 1. Gather the targets before writing anything

Find the parent epic, **if this work belongs under one**. A new top-level lane is
parentless and should stay that way. **Epics are usually `in_progress`, not `open`** —
filtering to `open` alone hides them and produces orphans:

```bash
bd list --status=open,in_progress      # epics show as ◐ [epic]
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

If it returns a matching bead, reuse that ID instead of creating — but **finish its
setup before moving on**. A run that died mid-step-2 may have created the bead and
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
want='<!-- bead-id: <bead-id> -->'
hits=[i for i in json.load(sys.stdin) if want in (i.get('body') or '')]
print(hits or 'no exact-marker twin; safe to create')"
```

If an exact-marker twin exists, skip creation and jump to step 4 to link it. Then check
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
  [ -n "$(bd_cfg github.owner)" ] && [ -n "$(bd_cfg github.repo)" ] && return 0
  [ -n "${GITHUB_REPOSITORY:-}" ] && return 0
  [ -n "${GITHUB_OWNER:-}" ] && [ -n "${GITHUB_REPO:-}" ] && return 0
  return 1
}
```

If `bd_configured` succeeds, prefer `bd github sync --push-only --issues <id>`.
If it is unset, create the twin directly with the plugin — and do **not** configure it
just to file one issue, because a bare `bd github sync` pushes *every* bead and will
spam the tracker while other agents are working.

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

```bash
bd show <parent-bead-id> | grep External     # parent's twin number, if any
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
`issue_number` and `$CHILD_ID` as `sub_issue_id`. This applies equally on the resumed
path, where step 3 found an existing twin and kept only its number. Without a parent
twin, fall back to the body's **Relationships** section, as the gotcha below describes.

```bash
bd update <bead-id> --external-ref "https://github.com/rmems/synthetic-factory/issues/<n>"
bd show <bead-id> | grep -E 'External|LABELS'
```

`bd` writes through to `.beads/issues.jsonl` (an export of the Dolt backend, not the
source of truth). Committing that export is how other agents see the mapping — but it
is **shared mutable state**: it frequently arrives already-modified or already-staged
from another session, and sweeping it into an unrelated commit is a real collision.
Either commit it alone, or leave it and say so:

```bash
git diff -- .beads/issues.jsonl        # confirm only YOUR bead changed
# Pathspec-scoped: commits ONLY this file even when other paths are staged.
# A plain `git commit` would record the whole index — the exact collision
# this section warns about.
git commit -m "chore: link <bead-id> to GitHub issue #<n>" -- .beads/issues.jsonl
```

**Never** let it ride along in a feature commit. Check `git status` before committing:
if it is already staged, unstage it first (`git restore --staged .beads/issues.jsonl`).

### 5. Enforce tag parity (the step people skip)

Parity means the **domain labels** match. GitHub additionally carries tracking labels
(`bead:*`, `status:*`, `priority:*`) that have no bead equivalent — those are expected
to differ and are not part of the comparison.

`--parent` **silently inherits** the parent's labels, so the bead can end up with
domain tags the GitHub issue lacks. Diff and reconcile:

Read **both** sides — printing only the bead's labels leaves you comparing against a
remembered value, and step 3 may have resumed an existing twin or let `bd github sync`
create one, so the GitHub side is not necessarily what you last set:

Normalize both sides before comparing — `bd` prints a `LABELS: ` prefix that `gh` does
not, so the raw outputs never match even when the label sets are identical:

```bash
diff <(bd show <bead-id> | sed -n 's/^LABELS: //p' | tr ',' '\n' \
       | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | sort) \
     <(gh issue view <n> --repo rmems/synthetic-factory --json labels \
        --jq '.labels[].name' \
       | grep -Ev '^(bead|status|priority):' | sort) \
  && echo "parity OK"
```

The `grep -Ev` drops the GitHub-only tracking triplet. Empty diff means parity; any
line printed is the drift to reconcile.

`issue_write` **replaces** the label set, so pass the complete list: every domain label
plus the tracking triplet. If the drift you find here is *inherited* parent tags, note
that `--no-inherit-labels` cannot help at this point — it applies only at `bd create`
(step 2). Reconcile by removing the unwanted tags on both surfaces.

## Gotchas

- **`bd edit` opens `$EDITOR` and hangs an agent.** Use `bd update --title/--description/--notes`.
- **Do not hand-file a Linear twin.** Mirroring is automatic; issue bodies say so
  explicitly. Your job is only to make the tags correct at the source.
- **ProjectsV2: query before concluding.** At the last check this repo had none, but
  that is a snapshot, not a fact — never report "no project" without running:

  ```bash
  gh api graphql -f query='query($o:String!,$r:String!){repository(owner:$o,name:$r){
    projectsV2(first:100){nodes{number title closed}}}}' \
    -F o=rmems -F r=synthetic-factory --jq '.data.repository.projectsV2.nodes'
  ```

  If it returns projects, add the issue. Only report a no-op when the live query is empty.
- **Sub-issue relationships need both twins on GitHub.** `sub_issue_write` links by ID;
  if the parent bead has no GitHub twin (`bd show <parent> | grep External` is empty),
  record the parent in the body's **Relationships** section instead.
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
