# Tool-world families: training-eligible tool-calling, MCP, browser, and delegation episodes

Status: **design only**. Nothing in this document changes runtime code,
the registry, a sealed policy, or `outputs/raw/`. It answers one question:
which new families would matter most for coding and assistance work, and
whether the factory can generate them with code rather than with a model.
Surveyed at `main` `4ff832fa` (post #419).

Short answer: yes, and the only route that makes those families
**training-eligible** is the one the factory already uses for
`python-function-repair-factory`: a deterministic, project-owned
**environment** executes every tool call, so observations are measured, not
authored, and a sealed policy plus fresh replay carries the record to
`project_training_policy: allowed`. The four surfaces the question names
(tool calling, MCP, browser, orchestrating other agents) are four tool
surfaces on one shared environment, not four unrelated generators.

## 1. Why this exists

The topics already exist in the factory, but only as research-only data:

| Topic | Where it lives today | Rights | Observations |
|---|---|---|---|
| tool calling | `tool-use-preference-factory`, `agentic-coding-trajectory-factory`, 30+ Grok episode rows | `hosted-frontier-research-only-v1`, `blocked` | authored by the hosted model |
| MCP | `mcp-tool-schema-drift-factory`; mill extract `pipelines/msd/` | blocked; catalog authored in Grok sessions (#173) | authored |
| browser | `browser-tool-use-factory`; mill extract `pipelines/brw/` (1916 pairs under `config/brw/`) | blocked (#173) | authored, including the "agent-breaker" CSS plants |
| orchestration | `multi-agent-coordination-factory` (`multi_agent` kind: transcript, no tool evidence); `multi-agent-ouroboros-swarm`; mill extracts `mac`, `maos` | blocked (#173) | authored narrative |
| sandbox / secrets / refusal | `sandbox-refusal-factory`, `log-redaction-factory`, `safety-calibration-factory` | blocked | authored |

The training-candidate lane, by contrast, has no agentic family at all:

- `python-function-repair-factory` (`code_repair`) and `oracle-grounded` are
  the only procedural rows; `fault-recovery-simulator-factory` is a simulator
  row. None of them produces a tool-calling trajectory.
- The model-channel rows (`local_vllm`, `local_ollama`, `openrouter_api`)
  emit candidate `episode` records with `training_ready_policy: never`
  (`pipelines/model_channel/generate.py`). The model answers one prompt with
  one JSON episode; nothing executes its tool calls, so its observations are
  as authored as a hosted model's. #186 asks for matched pilots over "the same
  task sets, same validators / oracles", which presumes an oracle for
  episodes that does not exist yet.
- Execution verification for episodes is shape-level. `verify_execution`
  grades a step `verified` when `tool_call.name` is in the literal
  `KNOWN_TOOLS` set of `pipelines/verify_execution_shapes.py` and
  `observation` is a non-empty string. It cannot tell a measured observation
  from an invented one, and it knows no MCP, browser, or delegation tool.
- The VSET actor-provenance contract (#154, landed in #159) separates task
  author, solver, oracle, and `training_view`, and `vset_oracle_exec` runs a
  deterministic oracle against a pristine pack copy. It has no live generator
  (#155 is blocked) and no independently bound oracle (#160).

So the gap is not "we lack tool-use data"; it is "every tool-use record the
factory owns is research-only, and the lane that could carry training data
has no environment to measure tool use". This design fills that gap.

## 2. Goals and non-goals

Goals:

1. Generate tool-calling, MCP, browser, and delegation episodes whose every
   observation is produced by a deterministic in-repo environment and whose
   success verdict is a predicate over environment state, never a claim in
   the record.
2. Carry them through the existing gates (`round_txn` with the execution
   co-gate, census, `validate_run`, `check_records`, identity with preserved
   bytes, training audit, admitted export) to `project_training_policy:
   allowed`, on the same terms as `code_repair`: sealed source policy,
   pinned catalog digests, license evidence, fresh replay at every trust
   boundary.
3. Serve both a scripted solver (fully procedural, zero model calls) and the
   model-channel solvers of #186 through one environment, so local and
   OpenRouter-distillable pilots are measured by the same oracle.
4. Stay stdlib-only, byte-reproducible, and fail-closed, with packages that
   fit the repository's size and split conventions.

Non-goals:

- No real browser, real MCP server, or real sub-agent process in the first
  slices. A bound external runtime may be added later through the same
  `sf-oracle/1`-style adapter rule the parity families use: explicit binding,
  never a silent fallback (`docs/parity-oracles.md`).
- No trainer, no Hub publication, no change to the research-only status of
  any existing row.
- No reuse of the Grok-session catalogs (`config/brw`, `config/msd`,
  `config/tup`, `config/maos`, ...) as world packs. Their *topics* inform the
  fault menus below; their bytes stay research-only (#173).

## 3. The one rule

```text
catalog (world pack + task)  ->  solver proposes an action
                                   environment executes it  ->  observation
                                   ... repeat ...
                                   predicate over final state  ->  verdict
                                   replay from (pack, seed, actions) must reproduce every observation
```

The solver (scripted policy or a model-channel row) owns only the action
sequence and the `decision_basis` text. The environment owns every
observation, the fault schedule, and the verdict. A record whose
observations cannot be reproduced by replaying its own action sequence
against the pinned world pack is `failed`, not `inconclusive`. This is the
generator/oracle separation of `pipelines/oracle_grounded/envelope.py` and
`docs/oracle-grounded-datasets.md`, applied to trajectories: the trajectory
*is* the proposal, the replayed observations *are* the measurement.

## 4. Proposed package layout

```text
pipelines/tool_world/
  __init__.py          bind_import_twin, like code_repair / model_channel
  _contract.py         the one place that imports main primitives (exact_json,
                       oracle_grounded.rng.DrawStream, raw_tree_guard, envelope)
  source_policy.py     POLICY_SHA256 trust anchor for schemas/tool-world-source-policy-v1.json
  pack.py              world-pack loader: PACK.json identity, file tree digest,
                       tool registry, task specs, license evidence
  env.py               Environment: state, event log, step(), snapshot digest,
                       seeded fault stream, irreversibility flags
  schema_lite.py       JSON-schema subset for tool args (type, required, enum,
                       minimum/maximum, items); the only arg validator
  predicates.py        closed vocabulary of goal predicates (hidden + public)
  surfaces/workspace.py   files, search, edit, run_tests, bounded shell subset
  surfaces/mcp.py         simulated JSON-RPC 2.0 servers (section 6.2)
  surfaces/browser.py     deterministic DOM world over html.parser (6.3)
  surfaces/delegation.py  scripted worker registry and mailbox (6.4)
  policies/scripted.py    gold + perturbed scripted solvers per surface
  policies/model.py       model-channel solver loop (structured JSON actions)
  records.py           VSET record assembly (section 8)
  replay.py            fresh replay + verdict; the oracle every gate calls
  publication.py       transaction publish with mandatory replay, like
                       code_repair.publication
  cli.py               generate | replay | publish | export
pipelines/tool_world_cli.py   thin entry point, like code_repair_cli.py
schemas/tool-world-source-policy-v1.json
catalogs/tool-world-v1/<pack>/PACK.json + files/ + tools/ + tasks/ + pages/ + workers/
tests/fixtures/tool-world-run/<factory>/batch-r01.jsonl   byte-reproduced by the test
tests/test_tool_world_*.py                                 one module per package module
```

Size guidance, following `docs/mill-support-p4-design.md` and CodeScene:
each module under 500 lines, split by responsibility, no helpers extracted
by size. Expected totals: core (`pack`, `env`, `schema_lite`, `predicates`,
`replay`, `records`) about 1,200 lines; each surface 300 to 500; each policy
150 to 250; `publication` and `cli` mirror the code-repair siblings.

Shared files this design does **not** touch in the first slice:
`pipelines/__init__.py` (`bind_import_twin` makes `_PACKAGE_SIBLING_NAMES`
unnecessary), `leftover_mill.py`, `mill_family.py`, `round_txn.py` (the
family publishes through its own `publication.py` wrapper exactly as
`code_repair` does). Two shared files it must touch, once:
`pipelines/record_kind.py` (section 8) and
`pipelines/curate_identity_registry_rows.py` (section 9).

## 5. Environment contract

```python
class Environment:
    pack: Pack                 # pinned, immutable, digest-bound
    seed: int                  # DrawStream(seed) drives faults and worker timing
    state: State               # surface-owned, canonical-JSON serializable
    events: list[Event]        # ordered (n, tool_call, observation_sha256, fault_id | None)

    def tools(self) -> list[ToolSpec]           # name, description, input schema, irreversible: bool
    def step(self, call: ToolCall) -> Observation
    def snapshot_digest(self) -> str            # sha256 over canonical state
    def done(self) -> bool                      # budget exhausted or terminal action
```

Rules the contract enforces, each with a coded refusal like
`code_repair.vocabulary`:

- **Args are validated before effects.** A call whose `args` fail
  `schema_lite` produces the schema error as the observation and no state
  change. That is a lesson, not a crash.
- **Observations are canonical and bounded.** Text is normalized, capped
  (`MAX_OBSERVATION_CHARS`, same idea as the harness `got` / `got_sha256`
  pair), and the full digest is kept in evidence so the bounded text in the
  training view cannot be edited without detection.
- **Faults come from the seed, not the author.** `DrawStream` (SplitMix64,
  `pipelines/oracle_grounded/rng.py`) schedules faults from the pack's fault
  menu; the fault id is logged on the event, so replay reproduces the same
  fault at the same step.
- **Irreversible tools are declared.** `delete`, `force_push`, `send_email`,
  `drop_table` style tools carry `irreversible: true`; the predicate
  `no_irreversible_without_confirmation` reads the event log.
- **No wall clock, no host paths, no network.** Timestamps are pack-declared;
  the workspace surface never touches the real filesystem; the "shell" is an
  interpreter over a declared command vocabulary. Nothing here runs candidate
  code, so no sandbox identity is needed in slice 1. If a later surface runs
  candidate code (for example a real `run_tests` over a pack), it inherits the
  code-repair rule verbatim: the reviewed pin may run under rlimits, anything
  else needs `bwrap-ro-netns-v1` (#201).

## 6. Surfaces

Each surface declares its tools, its state, its fault menu, and the
predicates it can satisfy. A world pack composes surfaces; a task names the
surfaces it exposes.

### 6.1 Workspace (tool calling)

Tools: `read_file`, `write_file`, `edit_file` (anchored replace with an
expected `old` span), `search` (literal and regex over the tree), `list_dir`,
`run_tests` (declared suites with seeded outcomes, or a real unittest run over
the pack under the code-repair sandbox rule), `shell` (closed vocabulary:
`ls`, `cat`, `grep`, `wc`, `git status|diff|log` over a simulated index).

What it teaches: argument correctness, reading an observation before acting,
anchored edits that fail when the anchor moved, re-running tests after an
edit, stopping when the predicate is met instead of "one more check".

Faults: `ENOENT`, `EACCES`, anchor-moved edit conflict, truncated output,
first-N-runs failing test, timeout.

Predicates: `tests_pass(suite)`, `file_sha256(path, expected)`,
`value_reported(expected)`, `edits_within(paths)`, `max_steps(n)`.

Catalog: project-authored packs plus the already vendored, MIT-licensed
`catalogs/python-repair-v1` programs. The code-repair mutator is a ready
task seeder: inject a mutation, the failing hidden case is the issue, the
inverse repair is the gold edit, and the resulting record is a VSET
`issue_patch_v1` with a real `run_tests` oracle. This is the shortest path
to unblocking #155.

### 6.2 MCP (Model Context Protocol sessions)

A simulated JSON-RPC 2.0 server per pack, in-process, with the method subset
that matters for an agent: `initialize` (capabilities, protocol version),
`tools/list` with `nextCursor` pagination, `tools/call` returning
`content` plus `isError`, `resources/list` / `resources/read`,
`prompts/list` / `prompts/get`, `notifications/tools/list_changed`, and the
error codes `-32601` (method not found) and `-32602` (invalid params). The
pack pins the spec revision it models and records the license evidence of
any vendored schema, the same way `source_license_evidence` pins
TheAlgorithms/Python.

The agent-side tool is one call, `mcp`, with `args: {server, method,
params}`; the observation is the canonical JSON-RPC response.

What it teaches: list before call; validate against `inputSchema` instead
of guessing; read `isError` results as results, not transport failures;
follow `nextCursor`; re-list after `list_changed`; re-initialize after a
server restart; keep server identity straight when two servers expose a
tool with the same name.

Faults: schema drift between sessions (the `msd` topic, now executed:
a renamed required field, a narrowed enum), `-32602` on a stale schema,
`-32601` after a tool is withdrawn, a paginated list whose first page is
empty, a rate-limit error object, a restart that invalidates the session.

Catalog breadth, not new families: packs can ship `filesystem`, `git`,
`tickets`, `calendar`, `mail` servers with declared state machines. That is
where "assistance work" tool use (calendar, tickets, mail) lives without a
separate generator.

### 6.3 Browser

A deterministic DOM world built on `html.parser`: static pages from the
pack, links, forms, buttons with declared effects (navigate, toggle, submit,
open overlay), a cookie and auth gate, and pagination. Actions, as one
`browser` tool with `args: {action, ...}`: `navigate`, `find` (text, role,
selector), `click`, `type`, `submit`, `scroll`, `extract`, `back`. The
observation is a bounded accessibility-tree snapshot (role, name, state) plus
the URL, so a page is observed the way an agent observes it, not as raw HTML.

What it teaches: observe before clicking; prefer role/name over brittle
selectors; dismiss or route around overlays; recognise a 404 or redirect
loop and change plan; stop extraction at the declared end of a pager; never
submit a form whose required field is empty.

Faults (the `brw` topic, now executed): selector drift between page
versions, an overlay intercepting the click, 404, redirect loop, stale
element after navigation, pager that repeats its last row, consent gate.

Predicates: `url_is`, `extracted_equals(truth)`, `form_submitted(id,
fields)`, `no_irreversible_without_confirmation`.

This is the most expensive surface (a DOM model with forms and overlays
is real code) and the least reusable by the other three. It should land
after MCP and delegation unless browser data is the priority.

### 6.4 Delegation (orchestrating other agents)

An orchestrator episode whose tools are `agent` with `args: {action, ...}`:
`spawn(role, brief, scope)`, `send(agent_id, message)`, `await(agent_id)`,
`cancel(agent_id)`, `list()`. Workers are scripted from the pack with a
reliability profile: on time, late (an `await` returns `pending` and costs a
step), partial, wrong ("done" while the hidden suite still fails),
conflicting (two workers edit the same file), or inquisitive (the worker
asks a question and blocks until answered). The environment knows every
worker's ground truth because it authored the worker.

What it teaches: decompose with explicit scopes; brief with the acceptance
criterion; verify a claim against the environment before merging
(`run_tests` or `read_file` after `await`, visible in the event log); resolve
conflicts by reading both edits; cancel a runaway worker; finish within
budget.

Predicates: `tests_pass`, `verified_before_merge` (an environment read or
test run between a worker's "done" and the merge), `scopes_respected`,
`max_agents(n)`, `max_steps(n)`.

Unlike the `multi_agent` transcript kind, every turn here is a tool call
with a measured observation, so the staged tool-turn gate and the replay
oracle apply to it unchanged.

## 7. Families and what they would be worth

| Family (registry `path_id`) | Surfaces | Record kind | Why it matters for coding and assistance | Slice |
|---|---|---|---|---|
| `tool-world-workspace-factory` | workspace | `tool_episode_v1` | the substrate every coding agent runs on: correct args, read-then-act, anchored edits, test loops | 1 |
| derived: failure recovery | workspace (+ any) | `failure_recovery_v1` (VSET, exists) | fault injection on the same episodes gives recovery trajectories with real failure evidence; the hosted `cascading-error-recovery` topic, measured | 2 |
| derived: preference pairs | any | `preference` (repository wrapper) | gold vs. perturbed trajectory on one task and seed, labelled by the environment verdict, consumable by `curate_preferences` and the trajectory-pair gate; the `tool-use-preference` topic, measured | 2 |
| `tool-world-mcp-factory` | mcp (+ workspace) | `mcp_session_v1` | MCP is the standard tool surface now; discovery, validation, pagination, drift, and error semantics are exactly what small models get wrong | 3 |
| `tool-world-delegation-factory` | delegation + workspace | `delegation_v1` | verify-before-merge and scoped briefs are the orchestration lessons no narrative transcript can grade | 4 |
| `tool-world-browser-factory` | browser (+ workspace) | `browser_task_v1` | web tasks with executed breakers; highest build cost, lowest reuse | 5 |
| derived: safety-gated tool use | any with irreversible tools | `tool_episode_v1` with the confirmation predicate | refusal and confirmation as observable steps (the `refuse` / `decline` tools `verify_execution` already recognises), secrets never copied into tool args (its leak heuristics already run) | 2+ |
| later: context-reset long horizon | workspace | `tool_episode_v1`, multi-session | the environment drops the transcript between sessions and keeps only files; teaches durable notes and resumption; the `agent-memory-compaction` topic, measured | 6 |

Ranking rationale: the workspace surface is prerequisite for everything
and already has a task seeder (the code-repair mutator). Failure recovery and
preference pairs are nearly free once episodes replay. MCP is one JSON-RPC
state machine with high lesson density. Delegation reuses the workspace
surface for verification. Browser is a separate DOM model and should be
justified by demand.

Every family is one registry row, one package slice, one fixture round, and
one test module (#169 guardrails). Rows carry `source_type: procedural`,
`generator_ownership: project_owned`, `generation_method:
deterministic_execution`, `allowed_curation_lanes: ["curate_identity"]`,
`training_ready_policy: fresh_tool_world_gate`, and
`provenance_contract_by_kind: {<kind>: replay_tool_world}`.

## 8. Record contract

Records use the VSET actor-provenance envelope (`schemas/vset-record-v1`,
`schemas/actor-provenance-v1`), with new kinds added to
`vset_constants.RECORD_KINDS` and `KIND_PAYLOAD_KEYS` (and mirrored in the
schema; `tests/test_vset_schema_drift.py` keeps them equal). The
`training_view` is exactly the repository episode envelope, so
`check_episode`, `staging_tool_turn_errors`, `curate_coding`, and the
training audit apply to it without change.

```json
{
  "schema_version": "vset-record-v1",
  "record_kind": "tool_episode_v1",
  "actor_provenance_schema_version": "actor-provenance-v1",
  "source_kind": "synthetic",
  "task_author": {"model": "tool-world-pack", "version": "<pack sha256>", "prompt_hash": "sha256:<task spec>", "run_id": "..."},
  "solver": {"model": "tool-world-scripted-policy", "version": "<policy source sha256>", "tool_policy": "workspace-v1", "run_id": "...", "outcome": "success"},
  "oracle": {
    "kind": "tool_world_replay", "status": "validated",
    "repo_commit": "<pack sha256>", "command": "tool_world replay --pack <id> --seed <n>",
    "result_hash": "sha256:<replay digest>", "certifier": "tool_world.replay",
    "signals": ["deterministic_environment", "predicate_pass", "replay_agreement"],
    "hidden_predicates": ["tests_pass:hidden_sub"]
  },
  "curation": {"pipeline_version": "tool-world-v1", "decision": "accept", "reason_codes": []},
  "environment": {"repo_snapshot_hash": "sha256:<pack files>", "task_id": "<pack>.<task>", "repo_pack_id": "<pack>", "seed": 7, "surfaces": ["workspace"]},
  "release": {"factory_contract_version": "factory-registry-v0.4", "schema_version": "vset-record-v1", "manifest_hash": "...", "factory_registry_sha256": "..."},
  "payload": {
    "task_specification": "...",
    "actions": [{"n": 1, "tool_call": {"name": "run_tests", "args": {"suite": "tests"}}, "observation_sha256": "...", "fault_id": null}],
    "final_state_digest": "sha256:...",
    "predicate_results": {"tests_pass:tests": true, "max_steps:12": true},
    "execution_evidence": {"replay_digest": "sha256:...", "faults_scheduled": ["edit_anchor_moved@3"]},
    "outcome": "success"
  },
  "training_view": {
    "goal": "...",
    "steps": [{"n": 1, "decision_basis": "Plan: run the declared suite first so the failing tests name the file to read.", "tool_call": {"name": "run_tests", "args": {"suite": "tests"}}, "observation": "2 failed, 7 passed: tests/test_counter.py::test_sub ..."}],
    "outcome": "success",
    "reward": {"success": 1, "cost_steps": 6, "faults_recovered": 1}
  }
}
```

Points that follow from existing contracts:

- `decision_basis` is at most 240 characters, matches
  `OBSERVABLE_BASIS_RE`, and contains no hidden-reasoning key anywhere in
  the record's `training_view`. The scripted policy writes it from the last
  observation and the next plan step through varied templates; the model
  solver's text is kept only after `strip_untrainable`.
- `record_kind.classify_kind` currently returns `unknown` for a VSET record
  (no `family`, no key rule matches). Add one declared check ahead of the key
  rules, like `family == "python-function-repair"` does for `code_repair`:
  `schema_version == "vset-record-v1"` classifies as a new `vset` kind, and
  registry rows list `vset` in `record_kinds`. Identity preserves the bytes
  (`preserve_oracle_envelope` semantics), compose and export carry
  `training_view` as the trainable projection, and `validate_vset` is the
  shape gate the run validator dispatches to for that kind.
- `verify_execution` gains one family dispatch before its generic step
  heuristics: a `vset` record with `oracle.kind == tool_world_replay` is
  graded by `tool_world.replay`, not by `KNOWN_TOOLS`. Verified means replay
  reproduces every observation digest and the predicate verdict; a missing or
  unloadable world pack is `inconclusive` (waivable only with the recorded
  `--allow-inconclusive` reason); a digest or verdict mismatch is `failed`
  and never waivable. No tool name is added to the literal set, keeping
  generator vocabulary out of shared pipelines.
- Rewards stay small and declared: `success`, `cost_steps`,
  `faults_recovered`, `irreversible_without_confirmation`. Under the frozen
  reward ontology they classify as `sign_order_only` or excluded from reward
  training until the mapping declares the vocabulary; ordering supervision
  comes from the derived preference pairs, which the preference lane already
  verifies (`preference_order_verified`).

Rejected alternative: emit plain `episode` records straight into
`batch-rNN.jsonl`. It would put the oracle verdict either inside the trainable
payload (where self-certification keys are banned) or nowhere, and it would
leave #155 and #160 where they are. The VSET envelope exists for exactly this
separation; the cost is one more kind in `classify_kind` and a
`training_view` projection at compose time.

## 9. Rights and authority

Mirror `docs/code-repair-admission.md` exactly:

- `schemas/tool-world-source-policy-v1.json` names the generator
  (`tool-world`, version), `generator_ownership: project_owned`,
  `generation_method: deterministic_execution`, the catalog id and
  `catalog_sha256` / `programs_sha256` style pins (pack index digest and
  pack-files digest), `source_license_evidence` per pack, `intended_use:
  training_candidate`, `project_training_policy: allowed`,
  `publication_target: null`. `tool_world/source_policy.py` pins the exact
  bytes with its own `POLICY_SHA256`, validates and freezes them at import.
- `_parse_procedural_row` today tries the code-repair policy, then the
  oracle policy. Generalize it once to iterate a tuple of sealed procedural
  policies; a row must match exactly one. That is the only identity change.
- World packs are human-authored or permissively sourced, each with
  license evidence in `PACK.json`, never derived from Grok-session catalogs
  (#173). AI-assisted authoring of the generator code does not make the
  runtime output model-generated (the code-repair precedent).
- A scripted-solver record is procedural end to end. A model-solved record
  carries the solver's registry identity in `solver` and inherits the
  solver row's rights profile (`open-weight-local-candidate-v1` or
  `openrouter-distillable-candidate-v1`), the most restrictive actor in the
  record. Hosted frontier rows are never admitted as solvers; a record that
  names one is refused at generation time, not downgraded.
- `allowed` remains channel eligibility plus evidence, not a training-ready
  claim: the fresh gate (section 10) decides per round.

## 10. Gates, in order

1. **Generate** into a brand-new destination outside `outputs/raw/`
   (`raw_tree_guard`, `rename_noreplace`, `operator_paths`): `candidates.jsonl`
   plus `RUN.json` (`tool-world-run/1`, `candidates_sha256`, pack and policy
   digests, seed, solver identity, attempted / accepted / rejected counts).
2. **Replay** every candidate from a pristine pack copy; store the replay
   digest in `oracle.result_hash`. Natural rejections (predicate false,
   budget exhausted, schema error never recovered) are kept as evidence in a
   `tool-world-input-rNN.json` capture, outside the training JSONL, as
   `code-repair-input-rNN.json` does.
3. **Publish** through `tool_world.publication` into the registered factory
   directory via the transaction path code-repair uses: reserve the actual
   selected count, stage exact bytes, run the envelope check, the execution
   co-gate (now replay-backed), and link `ROUND-rNN.complete.json`. Exact and
   structural deduplication plus a per-task lineage cap keep one seed family
   from dominating a round.
4. **Census, validate_run, check_records** see a `vset` kind, dispatch to
   `validate_vset`, and never execute anything.
5. **Identity** preserves the bytes and attaches the row's rights envelope
   with `procedural_authority` pinned to the sealed policy digest.
6. **Training audit** `fresh_tool_world_gate`: replay every retained record
   against the pinned pack; an unpublished candidate, a pack digest the
   current catalog cannot reproduce, or a replay mismatch keeps
   `training_ready: false` with an explicit blocker.
7. **Export** with `--admit`: the exact run bytes, candidate bytes, lineage
   cap, and selected membership must equal the completed round, and the
   export replays the captured input again. A stored report never
   authorizes an export.

## 11. Determinism, identity, and digests

- Record ids: `twd-<pack-sha256>-<policy-sha256>-<seed>-<draw>`; distinct
  pack or policy revisions cannot collide on seed and draw (the
  `code-repair-run/2` rule).
- `replay_digest` is the sha256 over the canonical sequence of
  `(n, tool_call, observation_sha256, fault_id)`; `final_state_digest` is the
  environment snapshot digest. Both are recomputed at every gate.
- All JSON goes through `exact_json`; floats are avoided in environment
  state (counts and integers only), so canonical bytes never depend on
  float formatting.
- Pack files are pinned with LF line endings in `.gitattributes`, as
  `pipelines/oracle_grounded/*.py` already is, so digests reproduce across
  checkouts.

## 12. Model-channel solvers (the #186 matched pilots)

`policies/model.py` drives any reviewed model-channel row through the same
environment: the task, the tool list, and each observation are sent as chat
messages; the model answers with one strict JSON action per turn (structured
output parsed with `load_strict_json`, no native tool-calling or grammar
required, as #186 prefers); the environment executes it; after the predicate
or the step budget the trajectory is assembled into the same VSET record with
`solver` set to the model row. Because the environment is deterministic given
`(pack, seed, actions)`, a model-solved record replays exactly like a
scripted one, which is what makes "same task sets, same validators / oracles"
true rather than aspirational. The pilot report carries the #186 metrics:
attempted / accepted / rejected, schema-valid yield, predicate pass rate,
replay agreement, duplicate-adjusted yield, steps per record, tool entropy,
fault coverage, wall time, tokens, and cost for remote lanes.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Templated `decision_basis` and shallow synthetic observations make the corpus monotone | varied basis templates keyed on observation class; faults drawn per seed; real program text from permissively licensed packs; model-channel solvers for decision diversity; the training audit's entropy and record-length checks run on `training_view` |
| A surface quietly produces a plausible observation it did not compute (a narrative fallback) | surfaces return only computed state; any `unavailable` branch raises a coded refusal and the record is dropped, per `docs/parity-oracles.md` |
| The browser DOM model grows without bound | fixed action vocabulary; pages are static pack files; no JavaScript; land it last and only with a declared pack set |
| `KNOWN_TOOLS` and other literals accrete new names | tool-world records are graded by replay dispatch, not by the literal set |
| A second sealed policy complicates identity | one generalization of `_parse_procedural_row` to a policy tuple, with a test that a row matching two policies is refused |
| Pack bytes are mutable on disk between generation and export | every gate re-derives the pack digest; export refuses a digest the catalog cannot reproduce, as code-repair export does |
| Running candidate code in `run_tests` | not in slice 1 (declared suite outcomes); when added, inherit the code-repair sandbox rule and its attestation protocol unchanged |
| The research-only topic rows look duplicated | they stay as comparison baselines for the #164 reports; the new rows are the measured counterparts and say so in `NOTES-rNN.md` |

## 14. Sequencing

| Milestone | Lands | Done when |
|---|---|---|
| M0 | this document | reviewed; open decisions in section 15 answered |
| M1 | `tool_world` core, workspace surface, scripted policy, `tool-world-source-policy-v1`, one pack (`counter`-sized, project-authored), `tool-world-workspace-factory` row, `vset` kind in `classify_kind`, replay dispatch in `verify_execution`, fixture round, tests | one round passes publish, census, validate_run, check_records, identity, strict training audit, and admitted export with `project_training_policy: allowed` for that row only |
| M2 | fault menu and recovery templates; `failure_recovery_v1` and preference-pair derivation; mutation-seeded `issue_patch_v1` tasks from `catalogs/python-repair-v1` | #155 has a release candidate it can ablate |
| M3 | MCP surface and `tool-world-mcp-factory`, two catalog servers | drift and pagination faults recover in fixture; schema-drift records replay |
| M4 | delegation surface and `tool-world-delegation-factory` | `verified_before_merge` is observable in every accepted record |
| M5 | browser surface and `tool-world-browser-factory` | only if demanded; same gates |
| M6 | `policies/model.py`; matched local Ollama and OpenRouter pilots over the M1 to M4 task sets | #186 pilot report with replay-backed oracle pass rates |

Each milestone is its own PR series under the #169 guardrails; none
touches `outputs/raw/`.

## 15. Open decisions

1. **Envelope.** VSET with `training_view` (recommended, section 8) versus
   plain `episode` records. The recommendation costs one declared kind and a
   projection; the alternative costs the oracle separation.
2. **Kinds.** Four VSET kinds (`tool_episode_v1`, `mcp_session_v1`,
   `delegation_v1`, `browser_task_v1`) versus one `tool_episode_v1` with a
   `surfaces` field. Four kinds give `KIND_PAYLOAD_KEYS` per-surface
   evidence requirements; one kind keeps the schema smaller.
3. **Rights of model-solved records.** Confirm that the solver row's profile
   governs (section 9) and that the rights mapping needs no new rule for it.
4. **Reward vocabulary.** Declare the tool-world reward keys in
   `schemas/reward-ontology-v1.mapping.json` now, or accept
   `sign_order_only` until the first round exists.
5. **Order of surfaces.** MCP before delegation, or delegation first because
   it reuses the workspace surface and has the rarer lesson.
6. **MCP schema pin.** Implement the method subset from the spec with the
   revision recorded in `PACK.json`, or vendor the schema file with license
   evidence.
7. **Package home.** `pipelines/tool_world/` (recommended, matches
   `code_repair` and `model_channel`) versus the `generators/` layout
   sketched in #175.

## 16. Relationship to open work

- #155 (verified SWE release candidate) and #160 (bind VSET oracle
  independently of the solver): M1 and M2 are the live generator and the
  independently bound oracle those issues wait on.
- #175 (package the mill mechanism with a fresh catalog): the tool-world is
  the mill mechanism plus an executor. A mill templates observations from a
  catalog; the tool-world computes them from a pack. Both are procedural;
  only the second produces execution evidence.
- #186 (local and OpenRouter-distillable generators): section 12 is the
  matched-pilot oracle that issue assumes.
- #171 (simulators as authoritative oracles) and #76: the environment is a
  deterministic in-repo simulator in that sense, and `publishable` follows
  the same reproducible-digest rule.
- #161, #173: the research-only rows and mill extracts for the same topics
  remain research-only comparison baselines; nothing here reclassifies them.
