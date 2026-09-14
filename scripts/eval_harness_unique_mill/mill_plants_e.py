"""Unique eval-harness leftover plants r312–r319. Not r50–r252 or r253–r311 clones."""

from mill_plants import PAIRS, _bad, _ok

# r312 fmt leftover
PAIRS.append(
    (
        _ok(
            slug="buf-format-proto-score-swap-h99o",
            domain="proto-score",
            kind="fmt",
            avoided="r290 Black wrap steps; r298 prettier json-sort-keys; r304 sqlfluff templater",
            goal=(
                "buf format leftover reorders EvalResult proto fields so score and reason swap "
                "wire numbers after a schema bump; a planted restock 0.16 is read as reason-empty "
                "and default score 1.0. Pin field numbers; parse by name not order."
            ),
            plan="Dump proto fields, stop positional parse, prove planted restock fail.",
            outcome=(
                "Parser reads score by field name. Planted restock 0.16 fail-closed. Residual: "
                "an old Go client leftover still uses proto3 positional decode."
            ),
            ticket=(
                "Title: buf format leftover reordered EvalResult. planted restock 0.16 parsed as "
                "reason; score default 1.0."
            ),
            src="evals/eval_result.proto",
            src_obs="message EvalResult { string reason = 1; double score = 2; }  # leftover swap vs parser",
            run="evals/proto_score_eval.py",
            fail_obs="parser positional [score, reason]. after buf format leftover score=1.0",
            inspect="evals/proto_parse.py",
            inspect_obs="struct.unpack leftover positional. ignores field numbers",
            first_path="evals/proto_parse.py",
            first_old="score, reason = values[0], values[1]",
            first_new="reason, score = values[0], values[1]",
            first_obs="swap local. next buf format leftover still breaks positional",
            rate_tail="positional leftover still brittle to field reorder",
            still_after_429="positional leftover; planted restock 1.0",
            grep="EvalResult|field number|buf format",
            grep_obs="parse by name using protobuf lib; never positional",
            plan_change="protobuf name lookup; pin field numbers 1=reason 2=score",
            fix_path="evals/proto_parse.py",
            fix_old="reason, score = values[0], values[1]",
            fix_new="score = msg.score; reason = msg.reason",
            fix_obs="planted restock 0.16 by name. buf format cannot swap names",
            retry_obs="502 then retry; 5 pass 1 fail planted restock 0.16",
            test="tests/test_proto_score_by_name.py",
            test_body="assert parse uses field names; planted 0.16",
            test_obs="test_eval_result_score_not_positional",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed restock",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed restock",
            diff_obs=" evals/proto_parse.py | 6+-\n tests/test_proto_score_by_name.py | 12++\n",
            residual="Old Go client leftover still uses proto3 positional decode.",
        ),
        _bad(
            slug="cue-fmt-eval-struct-i00p",
            domain="cue-eval",
            kind="fmt",
            avoided="r290 Black wrap; r298 prettier json-sort; r304 shfmt heredoc",
            goal=(
                "cue fmt leftover rewrites eval_gate.cue so threshold: 0.7 collapses with a "
                "planted override leftover threshold: 0.0 via unification. Keep the gate as a "
                "closed struct; fail extra overrides."
            ),
            plan="Dump cue unification, close the struct, prove planted 0.0 override fail.",
            outcome=(
                "Local cue closed struct. Planted override 0.0 rejected. Handoff: CI leftover "
                "still cue export --inject threshold=0.0."
            ),
            ticket=(
                "Title: cue fmt leftover. planted threshold 0.0 unified over 0.7 so restock 0.16 "
                "passes."
            ),
            src="evals/eval_gate.cue",
            src_obs="threshold: float | *0.7  # leftover open unification",
            run="evals/cue_eval.py",
            fail_obs="CI --inject threshold=0.0 leftover. planted restock 0.16 pass",
            inspect="evals/eval_gate.cue",
            inspect_obs="open float leftover. cue fmt kept the default but inject wins",
            first_path="evals/eval_gate.cue",
            first_old="threshold: float | *0.7",
            first_new="threshold: 0.7",
            first_obs="literal 0.7. CI leftover --inject still overrides",
            rate_tail="CI leftover --inject threshold=0.0",
            still_after_429="inject leftover; planted restock pass",
            grep="threshold|cue export|inject",
            grep_obs="cannot remove CI inject from this ticket",
            plan_change="closed struct locally; document CI leftover inject",
            fix_path="evals/eval_gate.cue",
            fix_old="threshold: 0.7",
            fix_new="#Gate: {threshold: 0.7, ...}\\ngate: #Gate",
            fix_obs="local closed. CI leftover inject HANDOFF",
            retry_obs="502 unused. CI leftover inject. Partial",
            test="tests/test_cue_closed_threshold.py",
            test_body="xfail CI inject leftover; local closed struct 0.7",
            test_obs="CI leftover inject. Partial",
            suite_obs="local closed 0.7. CI leftover inject 0.0. Partial.",
            gate_obs="local closed 0.7. CI leftover inject 0.0. Partial.",
            diff_obs=" evals/eval_gate.cue | 4+-\n HANDOFF cue inject\n",
            residual="CI leftover still cue export --inject threshold=0.0. Partial.",
        ),
    )
)

# r313 cache leftover
PAIRS.append(
    (
        _ok(
            slug="sqlite-wal-eval-cache-j01q",
            domain="sqlite-cache",
            kind="cache",
            avoided="r253 xdist cache; r299 diskcache fanout; r265 lru id(tc)",
            goal=(
                "SQLite leftover WAL eval_cache.db-wal from the previous SHA still serves 1.0 "
                "for a planted pickup-window row after the table was rewritten. Checkpoint and "
                "key rows by git sha + golden id."
            ),
            plan="Dump WAL, checkpoint, key by sha+id, prove planted pickup-window fail.",
            outcome=(
                "WAL checkpointed. Keys include git sha. Planted pickup-window 0.14. Residual: "
                "a laptop leftover eval_cache.db-wal still sits next to the repo."
            ),
            ticket=(
                "Title: eval_cache.db-wal leftover. planted pickup-window HIT 1.0 after table rewrite."
            ),
            src="evals/sqlite_cache.py",
            src_obs="connect('eval_cache.db')  # leftover WAL from previous SHA not checkpointed",
            run="evals/sqlite_cache.py",
            fail_obs="WAL leftover reader sees 1.0 for pickup-window. table rewrite not visible",
            inspect="evals/sqlite_cache.py",
            inspect_obs="no WAL checkpoint leftover. keys are golden id only",
            first_path="evals/sqlite_cache.py",
            first_old="connect('eval_cache.db')",
            first_new="connect('eval_cache.db', isolation_level='IMMEDIATE')",
            first_obs="IMMEDIATE leftover still reads old WAL until checkpoint",
            rate_tail="WAL leftover still 1.0 pickup-window",
            still_after_429="WAL leftover; planted HIT 1.0",
            grep="WAL|checkpoint|eval_cache",
            grep_obs="wal_checkpoint(TRUNCATE); key sha+id",
            plan_change="checkpoint truncate; composite key git_sha+golden_id",
            fix_path="evals/sqlite_cache.py",
            fix_old="key = golden.id",
            fix_new="key = f\"{git_sha}:{golden.id}\"",
            fix_obs="planted pickup-window 0.14 miss after sha change",
            retry_obs="502 then retry; 5 pass 1 fail planted pickup-window 0.14",
            test="tests/test_sqlite_cache_sha_key.py",
            test_body="assert checkpoint; key includes git sha; planted miss",
            test_obs="test_eval_cache_not_wal_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            diff_obs=" evals/sqlite_cache.py | 8+-\n tests/test_sqlite_cache_sha_key.py | 12++\n",
            residual="Laptop leftover eval_cache.db-wal still sits next to the repo.",
        ),
        _bad(
            slug="lmdb-mapsize-score-trunc-k02r",
            domain="lmdb-cache",
            kind="cache",
            avoided="r253 xdist; r299 diskcache fanout; r267 protobuf unset score 0",
            goal=(
                "LMDB leftover map_size=1<<20 truncates a planted restock JSON value so the "
                "reader leftover except: score=1.0. Raise map_size and fail-closed on truncated "
                "values."
            ),
            plan="Dump map_size, raise it, fail truncated JSON, prove planted restock fail.",
            outcome=(
                "Local map_size=64MiB and truncated values raise. Planted restock 0.18 locally. "
                "Handoff: the shared runner leftover still uses 1<<20."
            ),
            ticket=(
                "Title: LMDB leftover map_size 1MiB. planted restock JSON truncated; reader "
                "except score=1.0."
            ),
            src="evals/lmdb_cache.py",
            src_obs="env.set_mapsize(1<<20)  # leftover tiny map\nexcept Exception: return 1.0",
            run="evals/lmdb_cache.py",
            fail_obs="MDB_MAP_FULL leftover. except 1.0 planted restock pass",
            inspect="evals/lmdb_cache.py",
            inspect_obs="map_size leftover 1MiB. fail-open on truncate",
            first_path="evals/lmdb_cache.py",
            first_old="except Exception: return 1.0",
            first_new="except Exception: return 0.0",
            first_obs="0.0 leftover still skip-as-pass in the gate helper",
            rate_tail="0.0 leftover skip helper still pass",
            still_after_429="tiny map leftover; skip helper pass",
            grep="set_mapsize|MDB_MAP_FULL|return 0.0",
            grep_obs="runner image leftover still 1<<20",
            plan_change="local 64MiB + raise; document runner leftover map_size",
            fix_path="evals/lmdb_cache.py",
            fix_old="env.set_mapsize(1<<20)",
            fix_new="env.set_mapsize(64<<20)",
            fix_obs="local planted 0.18. runner leftover 1MiB HANDOFF",
            retry_obs="502 unused. runner leftover map_size. Partial",
            test="tests/test_lmdb_mapsize_fail_closed.py",
            test_body="xfail runner 1MiB leftover; local 64MiB and raise",
            test_obs="runner leftover map_size. Partial",
            suite_obs="local 64MiB. runner leftover 1MiB. Partial.",
            gate_obs="local 64MiB. runner leftover 1MiB. Partial.",
            diff_obs=" evals/lmdb_cache.py | 6+-\n HANDOFF runner map_size\n",
            residual="Shared runner leftover still uses map_size=1<<20. Partial.",
        ),
    )
)

# r314 CI leftover
PAIRS.append(
    (
        _ok(
            slug="tekton-result-last-write-l03s",
            domain="tekton-eval",
            kind="ci",
            avoided="r300 Buildkite shard overwrite; r266 prom last-write; r291 Helm judge-model",
            goal=(
                "Tekton leftover results[0] last-write-wins so a passing shard overwrites the "
                "planted membership-freeze fail. Append shard results and fail if any failed."
            ),
            plan="Dump Tekton results, append per shard, fail-closed on any planted fail.",
            outcome=(
                "Results appended. Planted membership-freeze 0.12 fails the pipeline. Residual: "
                "a dashboard leftover still reads results[0] only."
            ),
            ticket=(
                "Title: Tekton leftover results[0] last-write. planted membership-freeze shard "
                "overwritten by later pass."
            ),
            src="ci/eval-pipeline.yaml",
            src_obs="results:\n- name: eval-score\n  # leftover single slot last writer wins",
            run="evals/tekton_eval.py",
            fail_obs="shard-2 planted 0.12 then shard-3 writes 0.94 leftover last-write",
            inspect="ci/eval-pipeline.yaml",
            inspect_obs="single result leftover. no merge",
            first_path="ci/eval-pipeline.yaml",
            first_old="- name: eval-score",
            first_new="- name: eval-score-$(shard)",
            first_obs="unique names. gather leftover still reads eval-score only",
            rate_tail="gather leftover still last-write eval-score",
            still_after_429="gather leftover; planted membership-freeze dropped",
            grep="eval-score|results:|shard",
            grep_obs="merge all shard results; fail if any < threshold",
            plan_change="append-only shard results; gather min() fail-closed",
            fix_path="ci/gather.py",
            fix_old="score = results['eval-score']",
            fix_new="score = min(v for k,v in results.items() if k.startswith('eval-score'))",
            fix_obs="planted 0.12 fails gather. gold shards 0.9x",
            retry_obs="502 then retry; gather fails planted membership-freeze 0.12",
            test="tests/test_tekton_shard_min.py",
            test_body="assert gather uses min of shard results; planted fails",
            test_obs="test_tekton_results_not_last_write",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            diff_obs=" ci/eval-pipeline.yaml | 4+-\n ci/gather.py | 6+-\n tests/test_tekton_shard_min.py | 12++\n",
            residual="Dashboard leftover still reads results[0] only.",
        ),
        _bad(
            slug="argo-output-param-overwrite-m04t",
            domain="argo-eval",
            kind="ci",
            avoided="r300 Buildkite shard overwrite; r288 k8s backoff 429; r291 Helm judge-model",
            goal=(
                "Argo leftover output parameter eval-pass is overwritten by a later skip step so "
                "a planted restock fail becomes true. Use a unique eval-harness-pass param."
            ),
            plan="Dump output params, unique key, prove planted restock fail locally.",
            outcome=(
                "Local workflow uses eval-harness-pass. Planted restock false locally. Handoff: "
                "the shared WorkflowTemplate leftover still overwrites eval-pass."
            ),
            ticket=(
                "Title: Argo leftover output eval-pass overwritten by skip step. planted restock "
                "fail becomes true."
            ),
            src="ci/eval-workflow.yaml",
            src_obs="outputs.parameters.eval-pass leftover global name",
            run="evals/argo_eval.py",
            fail_obs="eval step false. skip step leftover writes true. workflow success",
            inspect="ci/eval-workflow.yaml",
            inspect_obs="two steps same output name leftover last-write true",
            first_path="ci/eval-workflow.yaml",
            first_old="name: eval-pass",
            first_new="name: eval-pass-v2",
            first_obs="v2 local. template leftover still emits eval-pass=true",
            rate_tail="WorkflowTemplate leftover eval-pass=true",
            still_after_429="template leftover overwrite; planted restock true",
            grep="eval-pass|WorkflowTemplate|outputs.parameters",
            grep_obs="cannot edit cluster WorkflowTemplate from this ticket",
            plan_change="local unique param; document template leftover handoff",
            fix_path="ci/eval-workflow.yaml",
            fix_old="name: eval-pass-v2",
            fix_new="name: eval-harness-pass",
            fix_obs="local planted restock false. template leftover HANDOFF",
            retry_obs="502 unused. template leftover eval-pass. Partial",
            test="tests/test_argo_unique_output.py",
            test_body="xfail template leftover eval-pass; local eval-harness-pass",
            test_obs="template leftover overwrite. Partial",
            suite_obs="local unique param. template leftover eval-pass. Partial.",
            gate_obs="local unique param. template leftover eval-pass. Partial.",
            diff_obs=" ci/eval-workflow.yaml | 2+-\n HANDOFF WorkflowTemplate\n",
            residual="Shared WorkflowTemplate leftover still overwrites eval-pass. Partial.",
        ),
    )
)

# r315 cache leftover (not redis semantic, not xdist, not anthropic)
PAIRS.append(
    (
        _ok(
            slug="helicone-response-cache-n05u",
            domain="helicone-cache",
            kind="cache",
            avoided="r261 anthropic prompt cache; r263 redis semantic cache; r253 xdist cache",
            goal=(
                "Helicone leftover response cache keys only the first 2k of the judge prompt so "
                "a tightened membership-freeze rubric still HIT 1.0. Include the full prompt "
                "hash; bust on rubric change."
            ),
            plan="Dump Helicone cache key, hash full prompt, prove planted membership-freeze fail.",
            outcome=(
                "Cache key is sha256 of the full judge prompt. Planted membership-freeze 0.13. "
                "Residual: a proxy leftover still truncates keys at 2k."
            ),
            ticket=(
                "Title: Helicone leftover cache key[:2000]. tightened freeze rubric still HIT 1.0."
            ),
            src="evals/helicone_cache.py",
            src_obs="cache_key = prompt[:2000]  # leftover Helicone 'key too long' workaround",
            run="evals/helicone_cache.py",
            fail_obs="rubric change after 2k leftover. HIT 1.0 planted freeze",
            inspect="evals/helicone_cache.py",
            inspect_obs="slice leftover. evaluation_steps at end of prompt dropped from key",
            first_path="evals/helicone_cache.py",
            first_old="cache_key = prompt[:2000]",
            first_new="cache_key = prompt[:8000]",
            first_obs="[:8000] leftover still drops a 9k rubric",
            rate_tail="truncated key leftover; planted freeze HIT 1.0",
            still_after_429="key slice leftover; HIT 1.0",
            grep="cache_key|Helicone|prompt\\[:",
            grep_obs="sha256 full prompt; never slice",
            plan_change="sha256(full prompt+model); no prefix slice",
            fix_path="evals/helicone_cache.py",
            fix_old="cache_key = prompt[:8000]",
            fix_new="cache_key = sha256(prompt.encode()).hexdigest()",
            fix_obs="keys diverge after rubric. planted freeze 0.13",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-freeze 0.13",
            test="tests/test_helicone_full_prompt_hash.py",
            test_body="assert key is sha256 full prompt; rubric change misses",
            test_obs="test_helicone_cache_not_prefix_slice",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            diff_obs=" evals/helicone_cache.py | 4+-\n tests/test_helicone_full_prompt_hash.py | 12++\n",
            residual="Proxy leftover still truncates keys at 2k.",
        ),
        _bad(
            slug="portkey-simple-cache-o06v",
            domain="portkey-cache",
            kind="cache",
            avoided="r253 LiteLLM fallback; r261 anthropic prompt cache; r263 redis semantic",
            goal=(
                "Portkey leftover cache.mode=simple on the judge route serves yesterday's 1.0 "
                "after evaluation_steps change. Disable simple cache for judges."
            ),
            plan="Dump Portkey config, disable simple cache on judge, prove planted restock fail.",
            outcome=(
                "Local judge route cache.mode=off. Planted restock 0.17 locally. Handoff: the "
                "shared gateway leftover still has simple cache on."
            ),
            ticket=(
                "Title: Portkey leftover cache.mode=simple. planted restock HIT 1.0 after steps change."
            ),
            src="evals/portkey.yaml",
            src_obs="cache: {mode: simple}  # leftover on judge route",
            run="evals/portkey_eval.py",
            fail_obs="simple cache leftover HIT 1.0. steps tightened unused",
            inspect="evals/portkey.yaml",
            inspect_obs="simple mode leftover keys on url+body hash that drops steps field",
            first_path="evals/portkey.yaml",
            first_old="mode: simple",
            first_new="mode: semantic",
            first_obs="semantic leftover still HIT on similar restock wording",
            rate_tail="semantic leftover HIT; planted restock 1.0",
            still_after_429="cache leftover; planted restock HIT",
            grep="cache:|mode: simple|judge",
            grep_obs="shared gateway leftover still simple; cannot change it here",
            plan_change="local mode off; document gateway leftover simple cache",
            fix_path="evals/portkey.yaml",
            fix_old="mode: semantic",
            fix_new="mode: off  # judges must not cache",
            fix_obs="local planted 0.17. gateway leftover simple HANDOFF",
            retry_obs="502 unused. gateway leftover simple cache. Partial",
            test="tests/test_portkey_judge_cache_off.py",
            test_body="xfail gateway leftover simple; local mode off",
            test_obs="gateway leftover simple cache. Partial",
            suite_obs="local cache off. gateway leftover simple. Partial.",
            gate_obs="local cache off. gateway leftover simple. Partial.",
            diff_obs=" evals/portkey.yaml | 2+-\n HANDOFF gateway cache\n",
            residual="Shared gateway leftover still has simple cache on the judge route. Partial.",
        ),
    )
)

# r316 metric leftover
PAIRS.append(
    (
        _ok(
            slug="trulens-feedback-stub-p07w",
            domain="trulens-fb",
            kind="metric",
            avoided="Faithfulness empty-ctx; r270 metrics module shadow; r289 mypy stub GEval",
            goal=(
                "TruLens leftover Feedback provider is a stub that always returns 1.0 so planted "
                "pickup-window lies pass. Use the real groundedness provider; fail-closed on stub."
            ),
            plan="Dump provider class, reject StubProvider, prove planted pickup-window fail.",
            outcome=(
                "StubProvider raises. Real groundedness scores planted pickup-window 0.16. "
                "Residual: tests/conftest leftover still injects the stub for unit tests."
            ),
            ticket=(
                "Title: TruLens leftover StubProvider 1.0. planted pickup-window always pass."
            ),
            src="evals/trulens_fb.py",
            src_obs="provider = StubProvider()  # leftover 'offline CI'",
            run="evals/trulens_fb.py",
            fail_obs="StubProvider leftover 1.0. planted pickup-window pass",
            inspect="evals/trulens_fb.py",
            inspect_obs="StubProvider.always_one leftover. OpenAI provider commented",
            first_path="evals/trulens_fb.py",
            first_old="provider = StubProvider()",
            first_new="provider = OpenAI() if os.getenv('OPENAI_API_KEY') else StubProvider()",
            first_obs="CI leftover still unset key → stub 1.0",
            rate_tail="unset key leftover still StubProvider",
            still_after_429="stub leftover; planted pickup-window 1.0",
            grep="StubProvider|OpenAI|groundedness",
            grep_obs="refuse stub; fail-closed if no key",
            plan_change="no stub; raise MissingProvider; real groundedness only",
            fix_path="evals/trulens_fb.py",
            fix_old="provider = OpenAI() if os.getenv('OPENAI_API_KEY') else StubProvider()",
            fix_new="provider = OpenAI()  # raise if key missing; never stub 1.0",
            fix_obs="planted pickup-window 0.16. stub path gone",
            retry_obs="502 then retry; 5 pass 1 fail planted pickup-window 0.16",
            test="tests/test_trulens_no_stub.py",
            test_body="assert StubProvider not used; missing key raises",
            test_obs="test_trulens_feedback_not_stub_one",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            diff_obs=" evals/trulens_fb.py | 6+-\n tests/test_trulens_no_stub.py | 12++\n",
            residual="tests/conftest leftover still injects the stub for unit tests.",
        ),
        _bad(
            slug="phoenix-eval-omit-ctx-q08x",
            domain="phoenix-eval",
            kind="metric",
            avoided="Faithfulness empty-ctx; RAGAS leftover catalogs; r270 sitecustomize 1.0",
            goal=(
                "Arize Phoenix leftover HallucinationEvaluator template omits {reference} so "
                "planted restock lies have no context and score 1.0. Include reference; fail "
                "if the template slot is missing."
            ),
            plan="Dump template slots, require {reference}, prove planted restock fail locally.",
            outcome=(
                "Local template includes {reference}. Planted restock 0.15 locally. Handoff: "
                "the hosted Phoenix leftover still uses the no-reference template."
            ),
            ticket=(
                "Title: Phoenix leftover template omits reference. planted restock 1.0 empty-ctx "
                "fail-open."
            ),
            src="evals/phoenix_eval.py",
            src_obs="TEMPLATE = 'query={query} output={output}'  # leftover no {reference}",
            run="evals/phoenix_eval.py",
            fail_obs="no reference leftover. planted restock 1.0",
            inspect="evals/phoenix_eval.py",
            inspect_obs="HallucinationEvaluator template leftover missing {reference}",
            first_path="evals/phoenix_eval.py",
            first_old="TEMPLATE = 'query={query} output={output}'",
            first_new="TEMPLATE = 'query={query} output={output} reference={reference}'",
            first_obs="local slot added. hosted Phoenix leftover still old template",
            rate_tail="hosted leftover template omits reference",
            still_after_429="hosted leftover; planted restock 1.0",
            grep="HallucinationEvaluator|reference|TEMPLATE",
            grep_obs="cannot change hosted Phoenix from this repo",
            plan_change="local template + fail if slot missing; hosted leftover handoff",
            fix_path="evals/phoenix_eval.py",
            fix_old="eval = HallucinationEvaluator(template=TEMPLATE)",
            fix_new="eval = HallucinationEvaluator(template=TEMPLATE)\\nassert '{reference}' in TEMPLATE",
            fix_obs="local planted 0.15. hosted leftover HANDOFF",
            retry_obs="502 unused. hosted leftover template. Partial",
            test="tests/test_phoenix_template_reference.py",
            test_body="xfail hosted leftover; local {reference} required",
            test_obs="hosted leftover template. Partial",
            suite_obs="local reference slot. hosted leftover omit. Partial.",
            gate_obs="local reference slot. hosted leftover omit. Partial.",
            diff_obs=" evals/phoenix_eval.py | 4+-\n HANDOFF hosted Phoenix\n",
            residual="Hosted Phoenix leftover still uses the no-reference template. Partial.",
        ),
    )
)

# r317 metric leftover
PAIRS.append(
    (
        _ok(
            slug="evidently-col-map-pred-r09y",
            domain="evidently-map",
            kind="metric",
            avoided="Faithfulness empty-ctx; r264 pandas NA fillna 0; r256 wandb sanitize",
            goal=(
                "Evidently leftover column_mapping prediction='prediction' never sees "
                "actual_output so planted membership-freeze rows score NaN then fill 1.0. Map "
                "target/prediction correctly; fail-closed on NaN."
            ),
            plan="Dump column_mapping, bind actual_output, fail NaN, prove planted freeze fail.",
            outcome=(
                "column_mapping uses actual_output. NaN raises. Planted membership-freeze 0.14. "
                "Residual: a notebook leftover still maps prediction=prediction."
            ),
            ticket=(
                "Title: Evidently leftover column_mapping prediction. planted freeze NaN→1.0."
            ),
            src="evals/evidently_map.py",
            src_obs="ColumnMapping(prediction='prediction', target='target')  # leftover sklearn names",
            run="evals/evidently_map.py",
            fail_obs="actual_output unseen leftover. TextEvals NaN. fillna 1.0 planted freeze",
            inspect="evals/evidently_map.py",
            inspect_obs="sklearn leftover names. eval frame uses actual_output/expected_output",
            first_path="evals/evidently_map.py",
            first_old="prediction='prediction', target='target'",
            first_new="prediction='actual_output', target='target'",
            first_obs="prediction mapped. target leftover still 'target' not expected_output",
            rate_tail="target leftover name; still NaN→1.0",
            still_after_429="target leftover; planted freeze 1.0",
            grep="ColumnMapping|actual_output|fillna",
            grep_obs="map both columns; raise on NaN; no fillna 1.0",
            plan_change="prediction=actual_output target=expected_output; NaN fail-closed",
            fix_path="evals/evidently_map.py",
            fix_old="prediction='actual_output', target='target'",
            fix_new="prediction='actual_output', target='expected_output'",
            fix_obs="planted freeze 0.14. NaN raises instead of 1.0",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-freeze 0.14",
            test="tests/test_evidently_column_map.py",
            test_body="assert mapping uses actual_output/expected_output; NaN raises",
            test_obs="test_evidently_not_sklearn_column_names",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            diff_obs=" evals/evidently_map.py | 6+-\n tests/test_evidently_column_map.py | 12++\n",
            residual="Notebook leftover still maps prediction=prediction.",
        ),
        _bad(
            slug="giskard-scan-train-split-s10z",
            domain="giskard-scan",
            kind="metric",
            avoided="Faithfulness empty-ctx; r2 dataset-split cache; r260 pytest-split drops neg",
            goal=(
                "Giskard leftover scan() uses the train split so a planted restock row in test "
                "never runs. Scan the eval split; fail if the planted id is missing."
            ),
            plan="Dump split, scan eval, prove planted restock is in the report locally.",
            outcome=(
                "Local scan uses eval split. Planted restock present locally. Handoff: nightly "
                "leftover still scans train for 'speed'."
            ),
            ticket=(
                "Title: Giskard leftover scan(train). planted restock lives in eval split and is "
                "never scored."
            ),
            src="evals/giskard_scan.py",
            src_obs="scan(dataset.train)  # leftover 'scan is slow on eval'",
            run="evals/giskard_scan.py",
            fail_obs="report leftover 0 planted ids. restock only in eval split",
            inspect="evals/giskard_scan.py",
            inspect_obs="train leftover. planted restock id only in dataset.eval",
            first_path="evals/giskard_scan.py",
            first_old="scan(dataset.train)",
            first_new="scan(dataset.train.head(200))",
            first_obs="still train leftover. planted not in head",
            rate_tail="train leftover; planted restock missing",
            still_after_429="train leftover scan; planted absent",
            grep="dataset.eval|dataset.train|scan\\(",
            grep_obs="nightly leftover still train; cannot change that job here",
            plan_change="local scan(eval); document nightly leftover train",
            fix_path="evals/giskard_scan.py",
            fix_old="scan(dataset.train.head(200))",
            fix_new="scan(dataset.eval)",
            fix_obs="local planted restock in report. nightly leftover HANDOFF",
            retry_obs="502 unused. nightly leftover train scan. Partial",
            test="tests/test_giskard_scan_eval_split.py",
            test_body="xfail nightly train leftover; local scan eval split",
            test_obs="nightly leftover train scan. Partial",
            suite_obs="local eval split. nightly leftover train. Partial.",
            gate_obs="local eval split. nightly leftover train. Partial.",
            diff_obs=" evals/giskard_scan.py | 2+-\n HANDOFF nightly train scan\n",
            residual="Nightly leftover still scans train for speed. Partial.",
        ),
    )
)

# r318 trace leftover
PAIRS.append(
    (
        _ok(
            slug="neptune-log-last-scalar-t11a",
            domain="neptune-log",
            kind="trace",
            avoided="r266 prom last-write gauge; r256 wandb sanitize collision; r267 grafana 0-100",
            goal=(
                "Neptune leftover run['eval/score'].log last scalar wins so a planted "
                "pickup-window 0.12 is overwritten by a later gold 0.94. Log per-golden names; "
                "fail if any below threshold."
            ),
            plan="Dump neptune keys, per-golden log, min() gate, prove planted pickup-window fail.",
            outcome=(
                "Each golden has eval/score/<id>. Gate uses min. Planted pickup-window 0.12. "
                "Residual: a board leftover still charts eval/score last value."
            ),
            ticket=(
                "Title: Neptune leftover eval/score last scalar. planted pickup-window 0.12 then "
                "gold 0.94 overwrites."
            ),
            src="evals/neptune_log.py",
            src_obs="run['eval/score'].log(score)  # leftover single series last-write",
            run="evals/neptune_log.py",
            fail_obs="planted 0.12 then gold 0.94 leftover last scalar 0.94 gate pass",
            inspect="evals/neptune_log.py",
            inspect_obs="single key leftover. no per-golden series",
            first_path="evals/neptune_log.py",
            first_old="run['eval/score'].log(score)",
            first_new="run['eval/score'].log(score, step=i)",
            first_obs="step leftover. gate still reads last() not min()",
            rate_tail="gate leftover last(); planted 0.12 hidden",
            still_after_429="last() leftover; planted pickup-window hidden",
            grep="eval/score|last\\(|min\\(",
            grep_obs="per-golden keys; gate min of all",
            plan_change="log eval/score/<id>; gate min; fail planted",
            fix_path="evals/neptune_log.py",
            fix_old="run['eval/score'].log(score, step=i)",
            fix_new="run[f'eval/score/{golden.id}'].append(score)",
            fix_obs="planted pickup-window 0.12 visible. min gate fail",
            retry_obs="502 then retry; 5 pass 1 fail planted pickup-window 0.12",
            test="tests/test_neptune_per_golden_min.py",
            test_body="assert per-golden keys; gate uses min not last",
            test_obs="test_neptune_score_not_last_scalar",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            diff_obs=" evals/neptune_log.py | 6+-\n tests/test_neptune_per_golden_min.py | 12++\n",
            residual="Board leftover still charts eval/score last value.",
        ),
        _bad(
            slug="comet-experiment-resume-u12b",
            domain="comet-resume",
            kind="trace",
            avoided="r256 wandb sanitize; r266 prom last-write; r285 confident push dry-run",
            goal=(
                "Comet leftover Experiment(resume='always') appends to yesterday's run so a "
                "planted restock fail is hidden under an old 1.0 mean. Start a new experiment "
                "per SHA."
            ),
            plan="Dump resume flag, per-SHA experiment, prove planted restock visible locally.",
            outcome=(
                "Local Experiment resume off keyed by SHA. Planted restock 0.18 locally. "
                "Handoff: nightly leftover still resume=always on the shared project."
            ),
            ticket=(
                "Title: Comet leftover resume=always. planted restock fail averaged into "
                "yesterday 1.0 mean."
            ),
            src="evals/comet_exp.py",
            src_obs="Experiment(project='eval', resume='always')  # leftover",
            run="evals/comet_exp.py",
            fail_obs="resume leftover yesterday run. planted restock drowned in 1.0 mean",
            inspect="evals/comet_exp.py",
            inspect_obs="resume always leftover. no SHA in experiment name",
            first_path="evals/comet_exp.py",
            first_old="resume='always'",
            first_new="resume='never'",
            first_obs="local never. nightly leftover env COMET_RESUME=always",
            rate_tail="nightly leftover COMET_RESUME=always",
            still_after_429="nightly leftover resume; planted restock hidden",
            grep="resume=|COMET_RESUME|Experiment",
            grep_obs="cannot unset nightly env from this ticket",
            plan_change="local per-SHA name; document nightly leftover resume",
            fix_path="evals/comet_exp.py",
            fix_old="Experiment(project='eval', resume='never')",
            fix_new="Experiment(project='eval', experiment_key=git_sha)",
            fix_obs="local planted 0.18. nightly leftover resume HANDOFF",
            retry_obs="502 unused. nightly leftover resume. Partial",
            test="tests/test_comet_per_sha.py",
            test_body="xfail nightly resume leftover; local experiment_key=sha",
            test_obs="nightly leftover resume. Partial",
            suite_obs="local per-SHA. nightly leftover resume always. Partial.",
            gate_obs="local per-SHA. nightly leftover resume always. Partial.",
            diff_obs=" evals/comet_exp.py | 2+-\n HANDOFF nightly COMET_RESUME\n",
            residual="Nightly leftover still resume=always on the shared project. Partial.",
        ),
    )
)

# r319 cache leftover
PAIRS.append(
    (
        _ok(
            slug="clearml-output-uri-stale-v13c",
            domain="clearml-uri",
            kind="cache",
            avoided="r268 docker layer .deepeval; r305 nix gcroot; r299 joblib cwd cache",
            goal=(
                "ClearML leftover output_uri points at yesterday's artifact folder so planted "
                "membership-freeze goldens never upload and the eval task replays 1.0. Pin "
                "output_uri to this SHA's folder."
            ),
            plan="Dump output_uri, pin SHA folder, prove planted freeze is the artifact.",
            outcome=(
                "output_uri includes git sha. Planted membership-freeze 0.11 uploaded. Residual: "
                "an agent leftover still has Task.set_output_uri global yesterday."
            ),
            ticket=(
                "Title: ClearML leftover output_uri s3://eval/latest. planted freeze missing; "
                "task replays 1.0 artifacts."
            ),
            src="evals/clearml_task.py",
            src_obs="Task.init(..., output_uri='s3://eval/latest')  # leftover stable uri",
            run="evals/clearml_task.py",
            fail_obs="artifact leftover yesterday goldens. planted freeze absent 1.0 replay",
            inspect="evals/clearml_task.py",
            inspect_obs="latest leftover. no SHA in uri",
            first_path="evals/clearml_task.py",
            first_old="output_uri='s3://eval/latest'",
            first_new="output_uri='s3://eval/latest-' + os.getenv('GIT_SHA','dev')",
            first_obs="sha local. agent leftover Task.set_output_uri still latest",
            rate_tail="agent leftover global output_uri latest",
            still_after_429="agent leftover latest; planted freeze absent",
            grep="output_uri|set_output_uri|eval/latest",
            grep_obs="override agent leftover; always sha folder",
            plan_change="force output_uri sha after Task.init; ignore agent global",
            fix_path="evals/clearml_task.py",
            fix_old="Task.init(..., output_uri='s3://eval/latest-' + os.getenv('GIT_SHA','dev'))",
            fix_new="t = Task.init(...); t.output_uri = f's3://eval/{git_sha}'",
            fix_obs="planted freeze 0.11 in sha folder. latest unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-freeze 0.11",
            test="tests/test_clearml_sha_output_uri.py",
            test_body="assert output_uri includes sha; latest unused",
            test_obs="test_clearml_output_uri_not_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            diff_obs=" evals/clearml_task.py | 6+-\n tests/test_clearml_sha_output_uri.py | 12++\n",
            residual="Agent leftover still has Task.set_output_uri global yesterday.",
        ),
        _bad(
            slug="aim-run-hash-collision-w14d",
            domain="aim-hash",
            kind="cache",
            avoided="r256 wandb sanitize collision; r265 lru id(tc); r299 diskcache fanout trunc",
            goal=(
                "Aim leftover run hash uses name only so two SHAs collide and a planted restock "
                "fail is attached to yesterday's 1.0 run. Hash name+sha; do not reuse runs."
            ),
            plan="Dump run hash, include sha, prove planted restock on a new run locally.",
            outcome=(
                "Local run hash name+sha. Planted restock 0.19 on a new run. Handoff: the Aim "
                "server leftover still dedupes on name only."
            ),
            ticket=(
                "Title: Aim leftover run hash=name. planted restock appended to yesterday 1.0 run."
            ),
            src="evals/aim_run.py",
            src_obs="Run(run_hash=name)  # leftover stable hash",
            run="evals/aim_run.py",
            fail_obs="hash leftover 'eval-nightly'. planted restock on yesterday 1.0 run",
            inspect="evals/aim_run.py",
            inspect_obs="run_hash leftover name only. no sha",
            first_path="evals/aim_run.py",
            first_old="Run(run_hash=name)",
            first_new="Run(run_hash=name + '-' + git_sha[:7])",
            first_obs="local unique. Aim server leftover still dedupes on name",
            rate_tail="server leftover name-only dedupe",
            still_after_429="server leftover collision; planted on yesterday run",
            grep="run_hash|aim.sdk|eval-nightly",
            grep_obs="cannot change Aim server dedupe from this repo",
            plan_change="local name+sha; document server leftover handoff",
            fix_path="evals/aim_run.py",
            fix_old="Run(run_hash=name + '-' + git_sha[:7])",
            fix_new="Run(run_hash=sha256(f'{name}:{git_sha}'.encode()).hexdigest())",
            fix_obs="local planted 0.19 new run. server leftover HANDOFF",
            retry_obs="502 unused. Aim server leftover name dedupe. Partial",
            test="tests/test_aim_run_hash_sha.py",
            test_body="xfail server leftover name hash; local name+sha",
            test_obs="server leftover name dedupe. Partial",
            suite_obs="local sha hash. server leftover name collision. Partial.",
            gate_obs="local sha hash. server leftover name collision. Partial.",
            diff_obs=" evals/aim_run.py | 4+-\n HANDOFF aim server\n",
            residual="Aim server leftover still dedupes on name only. Partial.",
        ),
    )
)
