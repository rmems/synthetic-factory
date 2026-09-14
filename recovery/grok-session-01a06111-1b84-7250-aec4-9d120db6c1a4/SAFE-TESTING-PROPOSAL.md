# Proposal for safely testing selected recovered generators

Status: proposal only; no recovered generator is authorized to run.

Session: `01a06111-1b84-7250-aec4-9d120db6c1a4`

## Objective

Test a deliberately small allowlist of reconstructed generators without granting them access to the active checkout, dataset repositories, credentials, network, or persistent output paths. Testing would establish runtime behavior and output determinism only; it would not establish factual quality or training admission.

## Entry gate

A candidate should enter runtime testing only after a reviewer explicitly names its `version_id` and SHA-256 and confirms all of the following:

1. Reconstruction is `exact`, or an explicitly accepted `high-confidence` terminal-derived state. `partial` and `unrecoverable` lineages remain excluded.
2. `ast.parse` status is `parse_ok`, secret-pattern count is zero, and all high/critical static findings have been read at the cited lines.
3. Any output path, subprocess, network, dynamic-code, deletion, rename, permission-change, or raw-dataset operation is understood and either removed from a disposable test copy or blocked by the sandbox.
4. The generator/output mapping has one intended family, dataset category, run label, output target, and expected count. Conflicts and unmapped outputs are resolved manually.
5. The intended-use and project-training-policy fields are reviewed independently. Only `research_only_training_blocked` may proceed as research-only output, and that status still does not admit records to training.

## Proposed isolation

1. Copy only the approved source version into a new disposable directory outside the repository and outside every dataset path. Keep the recovered original read-only and verify the copy against the approved SHA-256 before any review-only adaptation.
2. Run as a dedicated unprivileged user in a disposable user/mount/network namespace or rootless container. Disable network entirely; mount the repository and recovery artifacts read-only only if the source demonstrably needs them; do not mount `outputs/raw`, dataset repositories, `$HOME`, SSH material, cloud credentials, or agent journals.
3. Provide a fresh empty output directory on a size-limited temporary filesystem. If the source hard-codes an output path, modify only the disposable test copy and retain a patch plus before/after hashes. Never create a symlink that redirects a hard-coded dataset path.
4. Use an isolated Python interpreter (`-I`, no user site, no inherited `PYTHONPATH`) with a minimal allowlisted environment. Supply no tokens or credentials. Disable bytecode writes and cap wall time, CPU, memory, process count, open files, and output size.
5. Apply syscall controls where available: deny network syscalls, deny writes outside the designated output mount, and capture `openat`, `rename`, `unlink`, `execve`, and `connect` attempts. Treat any denied or unexpected operation as a hard stop.
6. Capture stdout, stderr, exit status, resource use, filesystem inventory, and SHA-256 for every produced file. Do not copy produced data into a repository during the test.

## Proposed staged execution

### Stage A: one-run containment proof

Run one low-volume exact candidate whose static scan has no process, network, delete, dynamic-code, or raw-dataset finding. Verify that all writes remain inside the designated output directory and that no denied syscall was attempted.

### Stage B: schema and policy checks

Parse produced JSONL as data in a separate validator process. Check UTF-8, one JSON object per line, required schema fields, unique record identifiers, declared generator family/category/run label, research-only intent, blocked training policy, and the approved maximum record count. Do not import the generator to validate output.

### Stage C: determinism check

Repeat the same approved version twice in fresh sandboxes with identical explicit inputs and environment. Compare file inventories, line counts, record identifiers, canonicalized-record hashes, and whole-file SHA-256. Any unexplained difference blocks further use.

### Stage D: bounded expansion

Only after reviewing Stage A-C evidence, authorize additional exact versions in small batches. Keep one execution evidence bundle per `version_id` and never infer safety for duplicate or related versions merely from family membership.

## Required evidence bundle

For each approved version, retain the approval record; original and disposable-copy hashes; any adaptation patch; sandbox policy; exact interpreter identity; environment allowlist; static finding disposition; stdout/stderr; syscall audit; resource metrics; produced-file hashes; JSONL validation report; two-run determinism comparison; and a final research/training-policy decision.

## Stop conditions

Stop immediately on any network attempt, write outside the output mount, access to credentials or journals, subprocess not explicitly reviewed, unexpected delete/rename, raw-dataset access, output-count excess, schema violation, nondeterministic record identity, or policy ambiguity. Do not promote, commit, upload, or merge generated data without a separate release decision.

## Suggested first review set

Choose at most three `exact` lineages with `parse_ok`, zero secrets, zero critical/high action findings, `corroborated` output mapping, and `research_only_training_blocked`. The reviewer should name exact `version_id` values from `manifest/recovery-manifest.json`; this proposal intentionally does not auto-select or run them.
