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

Find the parent epic. **Epics are usually `in_progress`, not `open`** — filtering to
`open` alone hides them and produces orphans:

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

```bash
TOKEN=$(gh auth token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/rmems/synthetic-factory/milestones?state=all" \
  | python3 -c "import json,sys; [print(m['number'], m['title']) for m in json.load(sys.stdin)]"
```

Observed convention: curation / audit / training-readiness → *Synthetic Corpus
v0.1.0*; gate / generation / distillation → *Factory v0.2.0*. Pick the milestone your
**sibling issues** use, not the one that merely sounds right.

### 2. Create the bead

```bash
bd create "<title>" \
  --type=<bug|feature|task|epic|chore|decision> --priority=<0-4> \
  --parent=<parent-bead-id> \
  [--assignee="<owner>"] \
  --labels="synthetic-factory,curation,audit,..." \
  --description "..." --design "..." --acceptance "..." --notes "..."
```

- **`--assignee` is optional — derive it from who owns the work.** Most beads here are
  unassigned (11 of 18 at last check) and several are agent-owned (`agent:Ramanujan`,
  `agent:Nietzsche`, `codex/gpt-5.6-sol max`). Assign a human only when a human asked
  for it; omit the flag when ownership is undecided, and use the agent's identifier
  when an agent owns the lane. Do not default every bead to the repo owner.
- **Derive `--type` and `--priority` from the work, not from this example.** A defect
  is `bug`; new capability is `feature`; routine work is `task`; a lane spanning
  several issues is `epic`; a choice to record is `decision`. `--priority` takes `0-4`
  (0 = highest), **not** `high`/`medium`/`low` — reserve `0`/`1` for things that block
  a release or corrupt data, and default to `2`.
- `--parent` makes it a hierarchical child **and inherits the parent's labels**.
- Put measured evidence in `--design`, blast radius and coordination in `--notes`.

### 3. Create the GitHub twin

**First check whether a twin already exists.** A previous run may have created the
issue and then failed before `--external-ref` landed, so the bead looks unlinked while
the issue is already there. Creating "the" twin at that point makes a second one:

Search the **complete** marker, closing delimiter included. A bare `bead-id: sf-v46`
also matches its children's `<!-- bead-id: sf-v46.2 -->`, which would "find" a twin
that belongs to a different bead and link the wrong issue:

```bash
bd show <bead-id> | grep External          # empty is not proof; also search GitHub
gh search issues --repo rmems/synthetic-factory \
  --match body "<!-- bead-id: <bead-id> -->" --json number,title,body \
  | python3 -c "
import json,sys
want='<!-- bead-id: <bead-id> -->'
hits=[i for i in json.load(sys.stdin) if want in (i.get('body') or '')]
print(hits or 'no exact-marker twin; safe to create')"
```

If an exact-marker twin exists, skip creation and jump to step 4 to link it. Then check
the sync path live rather than assuming — `bd` accepts either the split `github.owner`
+ `github.repo` keys or the combined `github.repository`, so probing one alone reports
a configured integration as unset:

```bash
bd config get github.owner 2>/dev/null || bd config get github.repository 2>/dev/null \
  || echo "unset -> create the twin directly"
```

If `github.owner` **is** configured, prefer `bd github sync --push-only --issues <id>`.
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

```bash
bd show <bead-id> | grep LABELS
gh issue view <n> --repo rmems/synthetic-factory --json labels \
  --jq '[.labels[].name] | map(select(startswith("bead:") or startswith("status:")
        or startswith("priority:") | not)) | sort | join(", ")'
```

The second command strips the GitHub-only tracking triplet, so its output should match
the bead's `LABELS` line exactly. Any difference is the drift to reconcile.

`issue_write` **replaces** the label set, so pass the complete list: every domain label
plus the tracking triplet. Suppress inheritance with `--no-inherit-labels` when the
parent's tags do not apply.

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
