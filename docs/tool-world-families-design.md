# Tool-world families: training-eligible tool-calling, MCP, browser, and delegation episodes

Status: **design, with the first slice implemented** (section 17). The
package `pipelines/tool_world/`, four world packs, the CLI, the fixture run,
and the tests land with this document. Nothing here changes the registry, a
sealed policy, a shared validator, or `outputs/raw/`; those are the admission
milestones in section 14. The document answers one question: which new
families would matter most for coding and assistance work, and whether the
factory can generate them with code rather than with a model. Surveyed at
`main` `4ff832fa` (post #419); tracked in #422.

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
  source_policy.py     (M1) POLICY_SHA256 trust anchor for schemas/tool-world-source-policy-v1.json
  vocabulary.py        identities, limits, finding codes, the coded refusal type
  faults.py            seeded fault schedule and the call-counting fault engine
  pack.py              world-pack loader: PACK.json identity, member digest,
                       task specs, license evidence and attestation
  catalog.py           CATALOG.json pins; a drifted pack digest is refused
  env.py               Environment: state, event log, step(), snapshot digest,
                       seeded fault stream, irreversibility flags
  schema_lite.py       JSON-schema subset for tool args (type, required, enum,
                       minimum/maximum, items); the only arg validator
  predicates.py        closed vocabulary of goal predicates (hidden + public)
  surfaces/base.py        ToolSpec and the surface protocol
  surfaces/workspace.py   files, search, anchored edits, run_tests over declared suites
  surfaces/workspace_suites.py   declared-suite shape checks and evaluation
  surfaces/workspace_search.py   search tool: pattern bound (no clock), grep, capped report
  surfaces/mcp.py         simulated JSON-RPC 2.0 servers (section 6.2)
  surfaces/mcp_servers.py        server member shape checks, session state and tool behaviors
  surfaces/browser_dom.py html.parser DOM and the accessibility snapshot
  surfaces/browser_dom_tree.py   Node tree, html.parser builder, structural queries
  surfaces/browser_dom_a11y.py   roles, accessible names, refs, snapshot, find
  surfaces/browser.py     static-site browser over that DOM (6.3)
  surfaces/browser_site.py       site.json shape checks, page lookup, redirects, drift
  surfaces/browser_effects.py    click effects by role and declared data-effect
  surfaces/delegation.py  scripted worker registry and mailbox (6.4)
  surfaces/delegation_workers.py worker profile checks and effects
  policies/scripted.py    gold + perturbed scripted solvers
  policies/model.py       (M6) model-channel solver loop (structured JSON actions)
  records.py           record assembly with the episode training view (section 8)
  replay.py            fresh replay + verdict; the oracle every gate calls
  run_files.py         RUN.json + candidates.jsonl: digest, row inventory, header-draw binding
  publication.py       (M1) transaction publish with mandatory replay, like
                       code_repair.publication
  cli.py               catalog-check | generate | replay | render | tools
pipelines/tool_world_cli.py   thin entry point, like code_repair_cli.py
schemas/tool-world-source-policy-v1.json
catalogs/tool-world-v1/<pack>/PACK.json + files/ + tools/ + tasks/ + pages/ + workers/
tests/fixtures/tool-world-run/{candidates.jsonl,RUN.json,NOTES.md}   byte-reproduced by the test
tests/test_tool_world_*.py                                 one module per concern
```

Size guidance, following `docs/mill-support-p4-design.md` and CodeScene:
each module under 500 lines, split by responsibility, no helpers extracted
by size. Expected totals: core (`pack`, `env`, `schema_lite`, `predicates`,
`replay`, `records`) about 1,200 lines; each surface 300 to 500; each policy
150 to 250; `publication` and `cli` mirror the code-repair siblings.

Shared files the first slice does **not** touch: `pipelines/__init__.py`
(`bind_import_twin` makes `_PACKAGE_SIBLING_NAMES` unnecessary),
`leftover_mill.py`, `mill_family.py`, `round_txn.py` (the family will publish
through its own `publication.py` wrapper exactly as `code_repair` does), and
every validator. The admission milestone (M1 in section 14) touches these
shared files, each once, and each with its own test:

| Shared file | Change |
|---|---|
| `pipelines/record_kind.py` | one declared check ahead of the key rules so a tool-world record classifies as its own kind instead of `unknown` |
| `pipelines/vset_constants.py`, `schemas/vset-record-v1.schema.json`, `tests/test_vset_schema_drift.py` | the four record kinds in `RECORD_KINDS` and `KIND_PAYLOAD_KEYS`, and `tool_world_replay` in `VALIDATING_ORACLE_KINDS`; `_self_certify_kind_errors` rejects a `validated` oracle of any other kind today |
| `pipelines/validate_run*.py`, `census.py`, `check_records.py` | dispatch the new kind to `validate_vset` plus `tool_world.replay`; today none of them references `validate_vset` |
| `pipelines/verify_execution*.py` | replay dispatch before the `KNOWN_TOOLS` heuristics (section 8) |
| `pipelines/training_audit*.py` | the turn reader visits `training_view` for the new kind; today it reads top-level episode steps and a fixed set of wrappers, so `decision_basis` checks would be skipped |
| `pipelines/curate_identity_registry_fields.py` | `replay_tool_world` joins the provenance-contract vocabulary; an unknown contract is refused at load today |
| `pipelines/curate_identity_registry_rows.py` | `_parse_procedural_row` iterates a tuple of sealed policies (section 9) |

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
- **Observations are canonical and bounded.** Text is capped at
  `MAX_OBSERVATION_CHARS` (same idea as the harness `got` / `got_sha256`
  pair); the full-text digest is kept in `payload.actions`, and replay
  recomputes both the digest and the canonical bounded text and compares
  the latter with the `training_view` step, so neither the evidence nor the
  trainable projection can be edited without detection.
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

Simulated JSON-RPC 2.0 servers per pack, in-process, with the method
subset that matters for an agent. The lifecycle follows the specification:
the client sends `initialize` and receives the protocol version (the server
spec records the revision it models, `2025-06-18` by default; no schema file
is vendored), the capabilities (`tools.listChanged: true`, `resources`,
`prompts`) and `serverInfo`; the client then sends
`notifications/initialized`; any request before `initialize` is refused with
`-32600`. Then `tools/list` with `nextCursor` pagination, `tools/call`
returning `content` plus `isError`, `resources/list` / `resources/read`,
`prompts/list` / `prompts/get`. Error codes: `-32601` method not found,
`-32602` invalid params and unknown tool, `-32603` internal error (a restart),
`-32000` rate limited, `-32002` resource not found. When the advertised tool
set changes the server queues `notifications/tools/list_changed`.

The agent-side tool is one call, `mcp`, with `args: {server, method,
params}`; the observation is the canonical JSON-RPC response. Because the
wrapper is synchronous, a queued server notification is delivered as the
line preceding the next response on that server, the way a transport
delivers it before the reply the client is waiting for; a client
notification such as `notifications/initialized` is acknowledged with a
delivery line rather than a result, since notifications carry no response.

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

Worker effects land in the workspace at the moment the worker completes
(the `await` that returns its report), so there is no separate apply step
for the orchestrator to gate. The merge boundary is the orchestrator's own
acceptance, its `report_result` call. `verified_before_merge` therefore
requires, for every worker whose report claimed done, a workspace
`read_file` or `run_tests` event after that report and before
`report_result` (or before the budget ends when nothing was reported).

Predicates: `tests_pass`, `verified_before_merge`, `no_agents_pending`,
`max_agents(n)`, `max_steps(n)`.

Unlike the `multi_agent` transcript kind, every turn here is a tool call
with a measured observation, so the staged tool-turn gate and the replay
oracle apply to it unchanged.

## 7. Families and what they would be worth

| Family (registry `path_id`) | Surfaces | Record kind | Why it matters for coding and assistance | Slice |
|---|---|---|---|---|
| `tool-world-workspace-factory` | workspace | `tool_episode_v1` | the substrate every coding agent runs on: correct args, read-then-act, anchored edits, test loops | 1 |
| derived: failure recovery | workspace (+ any) | `failure_recovery_v1` (VSET, exists) | fault injection on the same episodes gives recovery trajectories with real failure evidence; the hosted `cascading-error-recovery` topic, measured | 2 |
| derived: preference pairs | any | `preference` (repository wrapper) | gold vs. perturbed trajectory on one task and seed, labelled by the environment verdict, consumed by `curate_trajectory_preferences` and its gate (not `curate_preferences`, which excludes trajectory pairs); the gate requires a shared leading step prefix, which `give_up_on_fault`, `skip_verification`, and `skip_confirmation` pairs satisfy and `wrong_arg_type` pairs do not, so the latter stay SFT negatives; the `tool-use-preference` topic, measured | 2 |
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
`provenance_contract_by_kind: {<kind>: replay_tool_world}` (a contract name
`curate_identity_registry_fields.py` must learn, section 4).

## 8. Record contract

The first slice emits `schema_version: tool-world-record-v1`: the
actor-provenance field set (`task_author`, `solver`, `oracle`, `curation`,
`environment`, `payload`, `training_view`) with the `oracle` object limited
to the keys `schemas/actor-provenance-v1.schema.json` allows and no `release`
block, because no registry row exists yet. `tool_world.replay` is the
validator of that schema version. Promotion to the VSET envelope
(`vset-record-v1`) is the M1 change listed in section 4: the four kinds in
`RECORD_KINDS` and `KIND_PAYLOAD_KEYS`, `tool_world_replay` in
`VALIDATING_ORACLE_KINDS`, the schema enum and drift test. The
`training_view` is exactly the repository episode envelope and is validated
at build time by `validate_run.check_episode` with hidden thought forbidden
and terminal outcome enforced, so `staging_tool_turn_errors` and
`curate_coding` apply to it without change; the training audit's turn reader
needs the routing change in section 4 before it reads it.

A record as generated (digests and prose abbreviated):

```json
{
  "schema_version": "tool-world-record-v1",
  "record_kind": "tool_episode_v1",
  "family": "tool-world",
  "id": "twd-462d3436a2cf0388-f037150e8fdb3a71-6430791596913631286-00001",
  "task_author": {"model": "tool-world-pack", "version": "<pack sha256>", "prompt_hash": "sha256:<task spec>", "run_id": "twd-run-1-<catalog>"},
  "solver": {"model": "tool-world-scripted-policy", "version": "<policy source sha256>", "tool_policy": "workspace-gold", "run_id": "twd-run-1-<catalog>", "outcome": "success"},
  "oracle": {"kind": "tool_world_replay", "status": "validated", "repo_commit": "<pack sha256>", "command": "python3 pipelines/tool_world_cli.py replay --record <id>", "result_hash": "sha256:<replay digest>", "certifier": "tool_world.replay", "signals": ["deterministic_environment", "replay_agreement", "predicate_pass"]},
  "curation": {"pipeline_version": "tool-world-v1", "decision": "accept", "reason_codes": []},
  "environment": {"repo_snapshot_hash": "sha256:<pack sha256>", "repo_pack_id": "counter-workspace", "task_id": "counter.delete-stale-lock", "catalog_sha256": "<catalog>", "pack_id": "counter-workspace", "pack_sha256": "<pack sha256>", "seed": 6430791596913631286, "surfaces": ["workspace"], "max_steps": 10},
  "payload": {
    "task_specification": "Remove the stale lock under locks/ ...",
    "actions": [{"n": 1, "tool_call": {"name": "list_dir", "args": {"path": "locks"}}, "observation_sha256": "<full text digest>", "fault_id": null, "truncated": false}],
    "final_state_digest": "<state digest>",
    "predicate_results": {"public": {"value_reported:value=stale lock removed": true}, "hidden": {"file_absent:path=locks/stale.lock": true, "no_irreversible_without_confirmation": true}},
    "execution_evidence": {"replay_digest": "<replay digest>", "faults_armed": ["transient-list"], "faults_fired": [], "faults_recovered": 0, "gave_up": false},
    "outcome": "success"
  },
  "training_view": {
    "id": "twd-...-00001",
    "goal": "Remove the stale lock under locks/ ...",
    "steps": [{"n": 1, "decision_basis": "Plan: list the locks directory to see which lock files exist before deleting anything", "tool_call": {"name": "list_dir", "args": {"path": "locks"}}, "observation": "locks/:\nstale.lock"}],
    "outcome": "Succeeded: remove the stale lock file with confirmation",
    "reward": {"success": true, "cost_steps": 6, "faults_recovered": 0},
    "meta": {"factory": "tool-world-workspace-factory", "generator": "tool-world-scripted-policy", "generator_version": "1.0.0", "kind": "episode", "family": "tool-world", "surface": "workspace", "variant": "gold", "seed": 6430791596913631286, "designed": true}
  }
}
```

Points that follow from existing contracts:

- `decision_basis` is `"<Prefix>: <intent>"`, matches `OBSERVABLE_BASIS_RE`,
  and is at most 240 characters. The episode gate enforces only the regex;
  the 240 cap is the coding lane's `MAX_DECISION_BASIS_CHARS`, and the
  scripted policy refuses a longer basis at generation time so the lane
  never has to concise one. `reward.success` is a boolean, as
  `require_reward` demands, and the outcome text is generated from the
  verdict so `terminal_outcome_agrees` holds. No hidden-reasoning key
  appears anywhere in the record; the builder scans for them and refuses.
- A perturbed variant is kept with `curation.decision: measure` and reason
  codes naming the variant and, when the environment failed it,
  `tool_world.predicate_fail`; only a successful gold trajectory is
  `accept`. The environment labels the variant; the author never does.
- `record_kind.classify_kind` currently returns `unknown` for these records
  (no `family` rule, no key rule matches). M1 adds one declared check ahead
  of the key rules, like `family == "python-function-repair"` does for
  `code_repair`, so the kind is recognised and registry rows can list it.
  Identity then preserves the bytes (`replay_tool_world` contract), compose
  and export carry `training_view` as the trainable projection, and the run
  validator dispatches the kind to `validate_vset` plus `tool_world.replay`.
- `verify_execution` gains one family dispatch before its generic step
  heuristics: a tool-world record is graded by `tool_world.replay`, not by
  `KNOWN_TOOLS`. Verified means replay reproduces every observation digest,
  every bounded training-view observation, every fault id, the final state
  digest, the predicate verdicts and the replay digest; a missing or
  unloadable world pack is `inconclusive` (waivable only with the recorded
  `--allow-inconclusive` reason); any disagreement is `failed` and never
  waivable. No tool name is added to the literal set, keeping generator
  vocabulary out of shared pipelines.
- Rewards stay small and declared: `success`, `cost_steps`,
  `faults_recovered`. Under the frozen reward ontology they classify as
  `sign_order_only` or excluded from reward training until the mapping
  declares the vocabulary; ordering supervision comes from the derived
  preference pairs through the trajectory-pair gate.

Rejected alternative: emit plain `episode` records straight into
`batch-rNN.jsonl`. It would put the oracle verdict either inside the trainable
payload (where self-certification keys are banned) or nowhere, and it would
leave #155 and #160 where they are. The envelope exists for exactly this
separation; the cost is the declared kind, the projection at compose time,
and the gate changes listed in section 4.

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
- World packs carry license evidence **and a catalog-authorship
  attestation** in `PACK.json`: `license.spdx`, `license.source`,
  `license.authorship` (who or what wrote the bytes, stated honestly), and
  `license.attestation` (that admission is a separate reviewed decision).
  The sealed policy pins the catalog digest and the admission gate requires
  the attestation before `project_training_policy: allowed`. No pack is ever
  derived from a Grok-session catalog (#173). The packs that land with this
  document disclose that their prose (goals, intents, page text, worker
  reports) was authored by Claude Code in this repository; whether
  AI-authored pack prose is admissible under the project policy is open
  decision 8, and until it is decided the rows stay unregistered. The
  observations themselves are computed by the environment either way, and
  AI-assisted authoring of the generator code does not make the runtime
  output model-generated (the code-repair precedent).
- A scripted-solver record is procedural end to end. For a model-solved
  record, rights cannot come from the `solver` block: identity derives
  retained rights from the factory row (`attach_retained_rights`), never
  from a field in the record. The reviewed route is therefore one registry
  row per (family, solver channel) pair, published under its own factory
  directory and carrying the solver's model-channel identity (generator,
  provider, channel, rights profile `open-weight-local-candidate-v1` or
  `openrouter-distillable-candidate-v1`), exactly as the model-channel rows
  do today; the scripted-solver rows stay procedural. Hosted frontier rows
  are never admitted as solvers; a record that names one is refused at
  generation time, not downgraded.
- `allowed` remains channel eligibility plus evidence, not a training-ready
  claim: the fresh gate (section 10) decides per round.

## 10. Gates, in order

1. **Generate** into a brand-new destination outside `outputs/raw/`
   (`raw_tree_guard`, `rename_noreplace`, `operator_paths`): `candidates.jsonl`
   plus `RUN.json` (`tool-world-run/1`, `candidates_sha256`, pack and policy
   digests, seed, solver identity, attempted / accepted / rejected counts).
2. **Replay** every candidate from a pristine pack copy, after binding
   `candidates.jsonl` to `RUN.json`'s digest and ordered row inventory, and
   that inventory to the record ids the header's own draw produces from the
   catalog, so a run cannot shed, reorder or substitute records and still
   pass (the rows' other fields are reporting, not evidence); store the
   replay digest in `oracle.result_hash`. Natural rejections (predicate false,
   budget exhausted, schema error never recovered) are kept as evidence in a
   `tool-world-input-rNN.json` capture, outside the training JSONL, as
   `code-repair-input-rNN.json` does.
3. **Publish** through `tool_world.publication` into the registered factory
   directory via the transaction path code-repair uses: reserve the actual
   selected count, stage exact bytes, run the envelope check, the execution
   co-gate (now replay-backed), and link `ROUND-rNN.complete.json`. Exact and
   structural deduplication plus a per-task lineage cap keep one seed family
   from dominating a round.
4. **Census, validate_run, check_records** recognise the declared kind and
   dispatch it to `validate_vset` plus `tool_world.replay` (the M1 change in
   section 4; today none of them references `validate_vset`); they execute
   nothing themselves beyond the deterministic environment.
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

- Record ids: `twd-<pack sha256 prefix>-<policy sha256 prefix>-<seed>-<draw>`
  (sixteen hex characters each); the full digests sit in `task_author.version`
  and `solver.version`, so distinct pack or policy revisions cannot collide on
  seed and draw (the `code-repair-run/2` rule). The seed is derived per record
  from the run seed, pack, task, variant and draw, so one record replays
  without the batch.
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
| M0.5 (this PR) | `tool_world` package with all four surfaces, scripted solvers, replay, CLI, four packs, fixture run, tests | generate and replay pass for every pack; no shared file changed |
| M1 | `tool-world-source-policy-v1`, the four registry rows, the shared-file changes of section 4 (declared kind, VSET kinds and oracle kind, validator dispatch, training-audit routing, identity contract vocabulary and policy tuple, `verify_execution` replay dispatch), `tool_world.publication` | one round passes publish, census, validate_run, check_records, identity, strict training audit, and admitted export with `project_training_policy: allowed` for the scripted rows only |
| M2 | `failure_recovery_v1` and preference-pair derivation through the trajectory-pair gate; mutation-seeded `issue_patch_v1` tasks from `catalogs/python-repair-v1` | #155 has a release candidate it can ablate |
| M3 | MCP pack breadth (assistance servers: calendar, mail, tickets) | drift and pagination faults recover across every server |
| M4 | delegation pack breadth (conflicting edits, budgets) | `verified_before_merge` is observable in every accepted record |
| M5 | browser pack breadth | only if demanded; same gates |
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
6. **MCP schema pin.** Resolved in the first slice: the method subset is
   implemented from the specification and the server spec records the
   protocol revision it models; no schema file is vendored.
7. **Package home.** Resolved in the first slice: `pipelines/tool_world/`,
   matching `code_repair` and `model_channel`.
8. **AI-authored pack prose.** The committed packs disclose that their
   prose was authored by Claude Code in this repository. Decide whether
   that is admissible for `training_candidate` rows, whether the packs must
   be re-authored or reviewed by a person first, or whether only the
   environment-computed observations count as the trainable content and the
   authored intents are replaced by templated bases at compose time.

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

## 17. Implementation status

This pull request lands the first slice, generator side only:

- `pipelines/tool_world/`: `env` (environment, bounded observations, fault
  engine, core tools, verdict), `faults` (seeded schedule with dotted
  selectors), `schema_lite`, `pack` and `catalog` (digest-pinned world packs),
  `predicates`, `surfaces/{workspace,mcp,browser,delegation}` plus
  `browser_dom`, `policies/scripted` (gold plan, marker-based recovery,
  captures, four perturbations), `records`, `replay`, `generate`, `cli`, and
  the entry point `pipelines/tool_world_cli.py`.
- `catalogs/tool-world-v1/`: four packs with the attestation of section 9,
  pinned in `CATALOG.json`: `counter-workspace` (workspace), `tickets-mcp`
  (two JSON-RPC servers, paginated `tools/list`, schema drift), `catalog-browser`
  (a five-page static site with redirects, overlays and link drift) and
  `release-delegation` (three scripted workers over a workspace, one profile
  per fault kind). Fourteen tasks, each declaring its faults, recoveries and
  perturbations; every gold plan succeeds under every seed and every declared
  fault fires and is recovered under some seed.
- Replay reads only the solver-owned facts (the calls, each decision basis,
  the variant, gave-up and recovered counts, the policy digest and run id) and
  re-derives every other field through the `records` builders, re-applies the
  episode gate, and re-runs the scripted policy for the declared variant, so a
  relabelled, forged or edited record reports a mismatch rather than agreement.
- `tests/test_tool_world_*.py` (one module per surface plus core, records and
  replay, CLI, imports) and the byte-reproduced fixture run under
  `tests/fixtures/tool-world-run/` (seed 20261009, twelve draws across all four
  factories, gold plus every perturbation), regenerated by the command in
  `tests/test_tool_world_fixture.py`.

```bash
python3 pipelines/tool_world_cli.py catalog-check --json
python3 pipelines/tool_world_cli.py generate --seed 1 --count 3 --out outputs/tool-world/<label> --json
python3 pipelines/tool_world_cli.py replay outputs/tool-world/<label> --json     # exit 1 on any disagreement
python3 pipelines/tool_world_cli.py tools --pack counter-workspace --task counter.add-sub --json
python3 pipelines/tool_world_cli.py catalog-check --write-pins --json      # re-pin after a reviewed pack edit
```

Not landed, by design: registry rows, the sealed source policy, every
shared-file change of section 4, transactional publication into
`outputs/raw/`, the model-channel solver loop, and any claim of training
readiness. A generated run is candidate evidence outside `outputs/raw/`.
