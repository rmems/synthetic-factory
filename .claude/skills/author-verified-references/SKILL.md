---
name: author-verified-references
description: "Partition code targets by family, spawn agents to author mechanically-verified reference implementations, validate fragments via checker harnesses, run interim builder validation, and merge into a dataset. Use this skill when authoring verified reference implementations for a code dataset, partitioning targets by family and validating each reference against a neighbourhood of test cases via local checkers and interim builder runs."
trigger: "Use this skill when authoring verified reference implementations for a code dataset, partitioning targets by family and validating each reference against a neighbourhood of test cases via local checkers and interim builder runs."
author: montoyaraul34
source_sessions:
  - montoyaraul34_montoyaraul34's Organization_default_b363f3ab-81a6-4abe-88b5-c596f7a8dd7b
  - montoyaraul34_montoyaraul34's Organization_default_344701ce-d2c4-426c-96b1-716c94aac4d3
contributors:
  - montoyaraul34
version: 1
created_by_agent: claude_code
created_at: 2026-09-09T20:32:25.688Z
updated_at: 2026-09-09T20:32:25.688Z
---

# Author mechanically-verified reference implementations

Use this skill when building a dataset of code-repair or code-completion examples that require verified pairs (original + reference), where references must be mechanically verified rather than LLM-authored.

## Workflow: partition → author fragments → verify → interim build → merge

### 1. Partition targets by family
- Group targets (~30–92 per fragment) by domain (bits/conversions, maths, sorts/strings, DP, etc.)
- Prepare full module text for each target in a JSON manifest
- Document any special constraints (identity-dependent, print-only tests, unsorted-input-dependent)

### 2. Spawn agents to author reference fragments in parallel
For each family, spawn an agent with:
- Full module text of all targets
- Task: author `reviewed_expression` (semantically-equivalent reference) or `sibling_same_file` (alternate function computing the same result)
- Identify edge cases and guards needed to match the original's behaviour
- Output: JSON fragment with sorted keys, 2-space indent, format `{ "target": "module::function", "reference_type": "reviewed_expression"|"sibling_same_file", "reference": "...", "notes": "..." }`

### 3. Create a checker harness per fragment
For each reference, verify against a neighbourhood specific to the domain:
- **Numeric**: ints in [-64, 64], edge cases (0, 1, -1)
- **String**: empty, single char, ASCII/non-ASCII variants, case permutations
- **List/sort**: empty, single element, reversed, shuffled, duplicates
- **Doctest**: every literal call in the docstring

Each checker must:
- Compare original vs reference on every case (2 s timeout per call)
- Record disagreements (function, input, original result, reference result)
- Verify stdlib-only imports, no `print/input/open/random/exec/eval`, parameter-name equality
- Report: targets examined, entries written, disagreements (expect 0), skipped targets with reasons

### 4. Write and validate each fragment
- Output to scratch directory (never touch the repo working tree)
- Run checker harness on every entry (e.g., `python3 check_refs_<family>.py`)
- Exit 0 only if all disagreements are explained or disagreeing entries are skipped

### 5. Run interim builder validation
- Feed each fragment into the real dataset builder (e.g., the actual catalog validator)
- Catch references that fail to certify in the builder's stricter test suite
- If disagreements appear in the builder:
  - Program dropped by builder for other reasons → no action needed
  - Reference fails builder's tests → skip that reference or revise it
  - Record the outcome

### 6. Merge all fragments
- Concatenate all fragment JSON files into a single `references.json`
- Sort keys, verify canonical format
- Run final builder validation on the merged set
- Report: total entries, total certifying references, any targets dropped

## Anti-patterns

- **Don't skip neighbourhoods.** References passing unit tests may fail on edge cases (empty, reversed, identity-dependent, non-ASCII). Sweep the full neighbourhood.
- **Don't assume all targets have references.** Skip identity-dependent programs (mutate in place), print-only tests, unsorted-input-dependent algorithms. Document the skip reason.
- **Don't validate references in isolation.** Interim builds in the real builder catch disagreements that local checkers miss.
- **Don't preserve bad guards.** If a reference needs a guard that changes semantics (e.g., `if input is sorted`), that disagrees with the original and should be skipped.

## Gotchas

- **Doctest edge cases.** Print-only doctests offer no reference to certify; skip them.
- **Identity-dependent behaviour.** Programs that mutate in place and return the same object disagree with copies; skip or choose a different reference type.
- **Output token limits.** Authoring for 200+ targets can exceed limits; shard agents by family or region.
- **Builder disagreements.** The real builder may use a stricter test suite or different timeout; interim validation catches these before the final merge.
