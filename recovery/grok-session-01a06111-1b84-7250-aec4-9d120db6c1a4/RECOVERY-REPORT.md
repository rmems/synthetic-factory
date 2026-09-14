# Grok temporary Python generator recovery report

Session: `01a06111-1b84-7250-aec4-9d120db6c1a4`

Recovery root: `/home/raulmc/.codex/recovery-worktrees/synthetic-factory-grok-01a06111/recovery/grok-session-01a06111-1b84-7250-aec4-9d120db6c1a4`

## Outcome

The parent session and all 919 discovered child sessions were inventoried. The chronology contains 3,597 explicit structured temporary-Python mutation events across 714 paths, plus 2,798 terminal calls that referenced temporary Python sources.

Reconstruction produced 2,038 preserved, read-only source versions across 1,076 collision-safe path lineages. Original basenames are retained inside version directories; each lineage key includes a SHA-256-derived suffix so identically named `/tmp` files cannot collide.

Final path classifications are: exact 419; high-confidence 8; partial 105; and unrecoverable 544.

This is a reconstruction and static-validation stopping point. No recovered generator was imported, compiled, or executed; no terminal command from a journal was rerun; no dataset repository was modified; and nothing was committed, pushed, proposed, or merged.

## Chain of custody and journal integrity

The evidence tree contained 21,532 files. Before/after comparison found 0 modified, 0 added, and 0 removed paths. `all_evidence_unchanged` is `true`.

The session graph has depth 1; statuses are cancelled 81, completed 488, failed 350, top_level 1.

One child session lacks `updates.jsonl`: `01a06412-d223-76e0-b33c-aa7a11d40533`. Its other available session evidence remains inventoried.

## Read-only inventory

| Evidence class | Count |
|---|---:|
| Sessions | 920 |
| Child sessions | 919 |
| Evidence files hashed | 21,532 |
| Structured temp-Python events | 3,597 |
| Structured temp-Python paths | 714 |
| Completed full writes | 493 |
| Completed structured replacements | 3,057 |
| Failed structured replacements | 47 |
| Terminal calls referencing temp Python | 2,798 |
| Terminal mutation candidates | 905 |
| Ambiguous terminal mutation candidates | 777 |
| Temp-Python hunk evidence records | 16,508 |

`inventory/mutations.jsonl` and `inventory/terminal-mutations.jsonl` preserve the original path, child agent/session ID, timestamp, journal line, tool outcome, hashes of recorded inputs/outputs, related JSONL expressions, and—in the terminal inventory—the exact logged command. Structured edit strings are retained as content-addressed versions or read-only `.pyfrag` evidence when no full base could be established.

## Chronological reconstruction

Structured events were globally ordered by recorded millisecond timestamp, session ID, journal line, and tool-call ID. Only `Completed` full writes and replacements were eligible. A replacement was replayed only when its recorded old string occurred exactly once in the known prior state.

| Structured replay outcome | Count |
|---|---:|
| `failed_edit_not_applied` | 47 |
| `not_replayed_missing_base` | 978 |
| `not_replayed_nonunique_or_missing_match` | 592 |
| `replayed_full_write` | 493 |
| `replayed_unique_search_replace` | 1,487 |

Terminal commands were parsed as inert text. The only statically replayable forms were quoted literal heredoc writes/appends, literal copies/moves, literal concatenations whose sources were already known, and literal deletions as existence-state changes. Inline Python, shell expansion, pipelines, in-place tools, globs, variables, and unknown source bytes were never executed or guessed.

| Terminal replay result | Count |
|---|---:|
| `not_replayed_ambiguous_terminal_mutation` | 637 |
| `not_replayed_missing_append_base` | 2 |
| `not_replayed_unknown_concat_source` | 27 |
| `not_replayed_unknown_source_state` | 39 |
| `recorded_deleted_state` | 118 |
| `replayed_copy` | 54 |
| `replayed_literal_heredoc` | 4 |
| `terminal_call_not_successful` | 47 |

473 path lineages have a final state that may have been altered by a successful terminal mutation that could not be reproduced conclusively.

### Classification meanings

- **Exact:** completed structured full-write bytes plus a uniquely applicable chain of completed structured edits, with no unresolved later final-state mutation.

- **High-confidence:** a literal deterministic terminal write/copy/concatenation was replayed statically from known content or known source states, with no unresolved later mutation. This is intentionally weaker than exact because the shell was not run.

- **Partial:** at least one complete version was recovered, but a later successful edit or terminal operation could not be placed or reproduced conclusively.

- **Unrecoverable:** no complete byte state was established. Available old/new edit fragments and event provenance are still retained.

Each lineage and each recovered version carries its own evidence text in the machine manifests; classification is not inferred from syntax validity or generator quality.

## Non-executing validation

`ast.parse` accepted 2,031 of 2,038 versions. 7 versions have syntax errors.

Secret-pattern scan findings: 0.

The destination-aware dangerous-operation scan produced 9,630 findings: critical 40, high 1,930, info 4,511, medium 3,149.

The final scan labels a dataset-path or shell-command string as informational when it is merely present in source/data. It assigns action severity only to AST calls such as write/delete/process/network/dynamic-code APIs. This avoids treating generated training record text as if the recovery process had executed it.

| Final static rule | Findings |
|---|---:|
| `delete` | 76 |
| `dynamic_compilation` | 1 |
| `dynamic_import` | 6 |
| `file_write` | 3,149 |
| `network_command_reference` | 402 |
| `process_execution` | 1,847 |
| `raw_dataset_mutation` | 39 |
| `raw_dataset_path_reference` | 2,987 |
| `recursive_delete` | 1 |
| `sensitive_import` | 1,118 |
| `shell_recursive_delete_reference` | 4 |

### Syntax-invalid versions

| Original path | Version | Line | Parser result |
|---|---|---:|---|
| `/tmp/actf-r68-gen.py` | `tmp-root--bf1d089ea789:v0018` | 488 | unexpected indent (actf-r68-gen.py, line 488) |
| `/tmp/ffpc-r26-splice-plants.py` | `tmp-root--69b210e6fbbb:v0001` | 557 | unterminated triple-quoted string literal (detected at line 561) (ffpc-r26-splice-plants.py, line 557) |
| `/tmp/nelb-r22c/notes_template.py` | `nelb-r22c--70e27b088c53:v0001` | 1 | unexpected indent (notes_template.py, line 1) |
| `/tmp/nelb-r66/_tail.py` | `nelb-r66--469e3e1c7d26:v0001` | 304 | '(' was never closed (_tail.py, line 304) |
| `/tmp/ttf-r47/patch_r47.py` | `ttf-r47--f5c9b83d47e8:v0001` | 685 | invalid syntax (patch_r47.py, line 685) |
| `/tmp/ttf-r53/_patch.py` | `ttf-r53--1b9ae17df13c:v0001` | 475 | unterminated triple-quoted string literal (detected at line 475) (_patch.py, line 475) |
| `/tmp/ttf-r98/_patch.py` | `ttf-r98--a13470f89928:v0001` | 613 | unterminated triple-quoted string literal (detected at line 613) (_patch.py, line 613) |

The secret scan is pattern-based and the operation scan is static; neither proves absence of secrets, safe behavior, semantic correctness, determinism, or policy admissibility.

## Hashes and duplicates

All 2,038 recovered versions have a SHA-256 in `reports/hashes.sha256`. There are 39 exact byte-duplicate groups and 39 normalized-AST duplicate groups. Complete member lists are in `reports/duplicates.json`.

## Generator-to-output and policy mapping

Static provenance produced 439 generator/helper mapping records. Confidence is corroborated 139, single_source 254, unmapped 46.

3 mappings carry an expected output count from a child prompt; 28 carry observed-count evidence from recorded terminal logs. Counts and emitted JSONL paths were not revalidated against dataset repositories.

| Static policy status | Mappings |
|---|---:|
| `research_only_training_blocked` | 281 |
| `research_only_training_policy_unresolved` | 47 |
| `unknown` | 111 |

`research_only_training_blocked` means both research-only intent and a blocked project training policy were found in source or child-prompt evidence. Every other status requires manual policy review. None of these statuses is training admission.

The complete map preserves generator family, dataset category, run label, child-agent provenance, output path expressions, record identifiers, expected/observed counts, mapping evidence, confidence, policy evidence, and conflicts in `reports/generator-output-map.final.jsonl`. The unsuffixed file is retained as the initial, less destination-aware pass.

## Manual-inspection gate

981 lineages require manual inspection: 799 blocking and 182 review-priority. The exhaustive machine-readable list is `reports/manual-inspection.jsonl`; the tabular list is `reports/manual-inspection.md`.

## Scope exception

A repository baseline unit-test process—not recovered source—was inadvertently started in the isolated worktree and terminated before completion (PID 2885213). It produced no accepted validation result and is excluded from this report's static-validation claims. No recovered source was involved. This disclosure is retained because the requested initial validation boundary was non-executing.

## Review stop

The recovery is stopped before generator execution, bulk commit, push, pull request, merge, or dataset mutation. `SAFE-TESTING-PROPOSAL.md` is a proposal only and requires separate explicit authorization before any selected source is run.

## Artifact index

- `reports/artifact-hashes.sha256` — artifact hashes
- `reports/dangerous-operations.final.jsonl` — dangerous operations final
- `reports/dangerous-operations.jsonl` — dangerous operations initial conservative
- `manifest/reconstruction-manifest.json` — detailed reconstruction manifest
- `reports/duplicates.json` — duplicates
- `manifest/dangerous-validation-final.json` — final danger validation index
- `reports/generator-output-map.final.jsonl` — generator output map
- `reports/generator-output-map.jsonl` — generator output map initial
- `reports/hash-and-duplicate-report.md` — hash duplicate report
- `RECOVERY-REPORT.md` — human recovery report
- `inventory/hunk-evidence.jsonl` — hunk evidence inventory
- `inventory/journal-hashes.after.jsonl` — journal hashes after
- `inventory/journal-hashes.before.jsonl` — journal hashes before
- `inventory/journal-integrity.json` — journal integrity
- `manifest/recovery-manifest.json` — machine readable recovery manifest
- `reports/manual-inspection.jsonl` — manual inspection jsonl
- `reports/manual-inspection.md` — manual inspection report
- `reports/provenance.jsonl` — provenance
- `reports/reconstruction-events.jsonl` — reconstruction event log
- `recovered_sources/by-original-path/` — recovered source tree
- `SAFE-TESTING-PROPOSAL.md` — safe testing proposal
- `reports/secrets.jsonl` — secrets
- `inventory/session-graph.json` — session graph
- `inventory/mutations.jsonl` — structured mutation inventory
- `reports/syntax.jsonl` — syntax
- `reports/terminal-mutation-audit.json` — terminal mutation audit
- `inventory/terminal-mutations.jsonl` — terminal mutation inventory
- `tools/recover_grok_generators.py` — trusted recovery tool
- `manifest/validation-index.json` — validation index
- `reports/hashes.sha256` — version hashes
