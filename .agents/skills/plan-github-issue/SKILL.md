---
name: plan-github-issue
description: Plan and file work as a beads issue with its GitHub twin (and Linear twin) sharing identical tags. Use when creating an issue, filing a bug/finding, planning work, or when asked to "create an issue", "file this", "add a bead", or "make a ticket" in this repo.
---

# Plan work as a bead + GitHub twin

In this repo an issue is **three linked objects**: a local bead (source of truth for
status/dependencies), a GitHub issue (public collaboration surface), and a Linear
issue (auto-mirrored). They must carry **the same tags**, or the twins drift.

Paths are relative to the repo root. Verified working 2026-08-21.

## Order of operations (do not reorder)

Create the **bead first**, then the GitHub twin, then link them. Creating the GitHub
issue first produces an orphan with no bead metadata that later syncs will duplicate.

### 1. Gather the targets before writing anything

```bash
bd list --status=open                      # find the parent epic
bd show <parent-id>                        # confirm it exists and is the right lane
bd list --json | python3 -c "import json,sys,collections; c=collections.Counter(l for i in json.load(sys.stdin) for l in (i.get('labels') or [])); print(dict(c.most_common(15)))"
```

The last command prints the **live label vocabulary**. Reuse existing labels; do not
invent near-synonyms (`curation` exists — do not add `curating`).

Milestones and the sibling convention:

```bash
TOKEN=$(gh auth token)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.github.com/repos/rmems/synthetic-factory/milestones?state=all" \
  | python3 -c "import json,sys; [print(m['number'], m['title']) for m in json.load(sys.stdin)]"
```

Convention observed in this repo:
- curation / audit / training-readiness work → milestone **1** (*Synthetic Corpus v0.1.0*)
- gate / generation / distillation work → milestone **2** (*Factory v0.2.0*)

Pick the milestone your **sibling issues** use, not the one that merely sounds right.

### 2. Create the bead

```bash
bd create "<title>" \
  --type=bug --priority=1 \
  --parent=<parent-bead-id> \
  --assignee="Raul Montoya Cardenas" \
  --labels="synthetic-factory,curation,audit,..." \
  --description "..." --design "..." --acceptance "..." --notes "..."
```

- `--priority` takes `0-4`, **not** `high`/`medium`/`low`.
- `--parent` makes it a hierarchical child **and inherits the parent's labels** — see
  the tag-parity trap below.
- Put measured evidence in `--design`, blast radius and coordination notes in `--notes`.

### 3. Create the GitHub twin

`bd github sync` is **not configured** in this repo (`github.owner is not configured`).
Do **not** configure it just to file one issue: a bare `bd github sync` pushes *every*
bead and will spam the tracker while other agents are working.

Create the twin directly with the plugin, in the house body format:

```
## Bead metadata
- **Bead:** `sf-xxx`
- **Type:** `bug`
- **Local status:** `open`
- **Priority:** `P1`
- **Parent bead:** `sf-yyy` — <parent title>

## Objective / ## Evidence / ## Design / ## Acceptance criteria
## Scope boundaries        <- what this does NOT fix
## Relationships           <- parent bead, related issues, PR coordination
## Tracking contract       <- copy verbatim from an existing issue
## Agent                   <- who filed it, and that the Linear twin is automatic
```

Title format: `[<bead-id>] <title>`. Set `assignees`, `milestone`, and `labels` in the
same `issue_write` call.

### 4. Link the bead back

```bash
bd update <bead-id> --external-ref "https://github.com/rmems/synthetic-factory/issues/<n>"
bd show <bead-id> | grep -E 'External|LABELS'
```

### 5. Enforce tag parity (the step people skip)

`--parent` **silently inherits the parent's labels**, so the bead can end up with tags
the GitHub issue lacks. Diff them and reconcile:

```bash
bd show <bead-id> | grep LABELS      # compare against the GitHub issue's labels
```

Then update GitHub with the **union** of domain tags. `issue_write` **replaces** the
label set, so always pass the complete list, including the `bead:*` / `status:*` /
`priority:*` triplet.

Suppress inheritance instead with `--no-inherit-labels` if the parent's tags do not apply.

## Gotchas

- **Labels auto-create.** Setting a label that does not exist yet creates it. Great for
  velocity, terrible for vocabulary drift — always check the live list first (step 1).
- **`bd edit` opens `$EDITOR` and hangs an agent.** Use `bd update --title/--description/--notes`.
- **Do not hand-file a Linear twin.** Mirroring is automatic; issue bodies in this repo
  say so explicitly. Your job is only to make the tags correct at the source.
- **ProjectsV2: none exist on this repo.** The GraphQL `projectsV2` query returns empty,
  so "add it to the project" is currently a no-op. Say so rather than silently skipping.
- **Sub-issue relationships need both twins on GitHub.** `sub_issue_write` links GitHub
  issues by ID; if the parent bead has no GitHub twin (`bd show <parent> | grep External`
  is empty), record the parent in the body's **Relationships** section instead.
- **Check for PR collisions before filing a code fix.** If the issue touches a file an
  open PR also modifies, name that PR under **Relationships**. Compare with
  `pull_request_read` `method: get_files`.

## Quality bar for the body

File findings from **measured output, not inspection**. An issue that says "X appears
to be broken" costs a reader the whole investigation again. Include the command or
harness, the variants tried, and the results table — see #33 for the shape. Then state
**Scope boundaries** honestly: what clearing this issue does *not* unlock.

If the finding contradicts something previously reported, say so in the issue and
correct the original (a comment on the stale issue, as in #13).
