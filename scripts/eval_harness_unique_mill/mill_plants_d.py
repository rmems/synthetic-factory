"""Unique eval-harness leftover plants r308–r319. Not r50–r252 or r253–r307 clones."""

from mill_plants import PAIRS, _bad, _ok

# r308 CI / cache leftover
PAIRS.append(
    (
        _ok(
            slug="bazel-action-omit-goldens-z91g",
            domain="bazel-eval",
            kind="ci",
            avoided="r268 docker layer; r294 GHA restore-keys; r305 pants process cache",
            goal=(
                "Bazel leftover action inputs for //evals:run omit goldens so remote cache HIT "
                "skips a planted restock-cutoff row. Declare goldens as action inputs and fail "
                "on HIT when the golden digest changed."
            ),
            plan="Dump Bazel action inputs, add goldens, prove planted restock-cutoff fail.",
            outcome=(
                "Goldens are action inputs. Planted restock-cutoff 0.18 fail-closed. Residual: "
                "a workstation still has --remote_download_minimal leftover."
            ),
            ticket=(
                "Title: bazel test //evals:run leftover remote HIT. goldens not in action inputs. "
                "planted restock-cutoff missing."
            ),
            src="evals/BUILD.bazel",
            src_obs="py_test(name='run', srcs=['eval.py'], data=[])  # leftover data empty",
            run="evals/bazel_eval.py",
            fail_obs="remote cache HIT leftover. planted restock-cutoff not in runfiles",
            inspect="evals/BUILD.bazel",
            inspect_obs="data leftover []. goldens/*.jsonl not declared",
            first_path="evals/BUILD.bazel",
            first_old="data=[]",
            first_new="data=glob(['goldens/*.jsonl'])",
            first_obs="local miss. remote leftover HIT on old action key without goldens hash",
            rate_tail="remote leftover HIT; planted restock-cutoff absent",
            still_after_429="remote action key leftover; planted missing",
            grep="py_test|goldens|remote cache",
            grep_obs="include goldens digest in the action key; --noremote_accept_cached locally",
            plan_change="goldens in data=; action key includes digest; no silent HIT",
            fix_path="evals/BUILD.bazel",
            fix_old="py_test(name='run', srcs=['eval.py'], data=glob(['goldens/*.jsonl']))",
            fix_new="py_test(name='run', srcs=['eval.py'], data=glob(['goldens/*.jsonl']), env={'GOLDEN_HASH': '$(location goldens)'})",
            fix_obs="planted restock-cutoff 0.18. remote miss after digest change",
            retry_obs="502 then retry; 5 pass 1 fail planted restock-cutoff 0.18",
            test="tests/test_bazel_goldens_in_action.py",
            test_body="assert goldens in action inputs; HIT forbidden when digest changes",
            test_obs="test_bazel_eval_action_inputs_include_goldens",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed restock-cutoff",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed restock-cutoff",
            diff_obs=" evals/BUILD.bazel | 6+-\n tests/test_bazel_goldens_in_action.py | 12++\n",
            residual="A workstation still has leftover --remote_download_minimal.",
        ),
        _bad(
            slug="earthly-cache-mount-scores-a92h",
            domain="earthly-eval",
            kind="cache",
            avoided="r268 docker layer COPY .deepeval; r294 GHA restore-keys; r305 nix gcroot",
            goal=(
                "Earthly leftover CACHE mount /eval-cache persists .deepeval scores across "
                "golden edits so planted pickup-window rows stay 0.93. Hash goldens into the "
                "mount id; bust on digest change."
            ),
            plan="Dump CACHE mount id, include golden digest, prove planted pickup-window fail.",
            outcome=(
                "Local Earthfile mount id includes golden digest. Planted pickup-window 0.21. "
                "Handoff: shared Earthly remote cache leftover still keyed without digest."
            ),
            ticket=(
                "Title: Earthly CACHE /eval-cache leftover. planted pickup-window still 0.93 "
                "after golden add."
            ),
            src="Earthfile",
            src_obs="CACHE /eval-cache  # leftover stable id, no golden digest",
            run="evals/pickup_eval.py",
            fail_obs="CACHE HIT leftover /eval-cache. planted pickup-window 0.93",
            inspect="Earthfile",
            inspect_obs="mount id leftover eval-cache. goldens not in cache key",
            first_path="Earthfile",
            first_old="CACHE /eval-cache",
            first_new="CACHE /eval-cache-v2",
            first_obs="v2 local miss. remote leftover still serves v2 empty then copies old",
            rate_tail="remote earthly leftover still has pre-golden scores",
            still_after_429="remote leftover mount; planted 0.93",
            grep="CACHE /eval|golden|earthly",
            grep_obs="cannot flush org Earthly remote from this repo",
            plan_change="local mount id + digest; document remote leftover handoff",
            fix_path="Earthfile",
            fix_old="CACHE /eval-cache-v2",
            fix_new="CACHE /eval-cache-$(cat goldens.sha)",
            fix_obs="local planted 0.21. remote leftover HANDOFF",
            retry_obs="502 unused. remote earthly leftover. Partial",
            test="tests/test_earthly_cache_digest.py",
            test_body="xfail remote leftover; local mount id includes goldens.sha",
            test_obs="remote earthly leftover. Partial",
            suite_obs="local digest miss. remote leftover HIT. Partial.",
            gate_obs="local digest miss. remote leftover HIT. Partial.",
            diff_obs=" Earthfile | 4+-\n HANDOFF earthly remote\n",
            residual="Shared Earthly remote cache leftover still keyed without golden digest. Partial.",
        ),
    )
)

# r309 judge leftover
PAIRS.append(
    (
        _ok(
            slug="dspy-suggest-retry-pass-b93i",
            domain="dspy-judge",
            kind="judge",
            avoided="r301 instructor ge=0.5 retry; r283 tenacity AssertionError retry; r254 extra=forbid",
            goal=(
                "DSPy leftover dspy.Suggest retries a planted membership-freeze lie until the "
                "student emits pass. Persist the first assertion failure; do not Suggest."
            ),
            plan="Dump Suggest, persist first fail, prove planted membership-freeze 0.19.",
            outcome=(
                "Suggest removed. First assertion fail persists. Planted membership-freeze 0.19. "
                "Residual: a notebook still imports leftover Suggest wrappers."
            ),
            ticket=(
                "Title: dspy.Suggest leftover. planted membership-freeze first fail then retry "
                "until pass."
            ),
            src="evals/dspy_judge.py",
            src_obs="dspy.Suggest(score >= 0.7, 'make the score pass')  # leftover",
            run="evals/dspy_judge.py",
            fail_obs="first score 0.19. Suggest leftover retries to 0.81 pass",
            inspect="evals/dspy_judge.py",
            inspect_obs="Suggest leftover treats low scores as repairable not planted fails",
            first_path="evals/dspy_judge.py",
            first_old="dspy.Suggest(score >= 0.7, 'make the score pass')",
            first_new="dspy.Suggest(score >= 0.0, 'keep first parse')",
            first_obs="threshold 0. Suggest leftover still resamples wording until 0.7+",
            rate_tail="Suggest leftover still retries; planted 0.19 not persisted",
            still_after_429="Suggest leftover; planted membership-freeze 0.81",
            grep="dspy.Suggest|Assert|membership-freeze",
            grep_obs="use Assert not Suggest; persist first score",
            plan_change="dspy.Assert; no Suggest; first score is the metric",
            fix_path="evals/dspy_judge.py",
            fix_old="dspy.Suggest(score >= 0.0, 'keep first parse')",
            fix_new="dspy.Assert(True)  # do not resample; persist first score",
            fix_obs="first 0.19 persisted. planted fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-freeze 0.19",
            test="tests/test_dspy_no_suggest.py",
            test_body="assert first low score persisted; Suggest not called",
            test_obs="test_dspy_assert_not_suggest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-freeze",
            diff_obs=" evals/dspy_judge.py | 6+-\n tests/test_dspy_no_suggest.py | 12++\n",
            residual="A notebook still imports leftover Suggest wrappers.",
        ),
        _bad(
            slug="pydantic-model-construct-skip-c94j",
            domain="pyd-judge",
            kind="judge",
            avoided="r254 extra=forbid; r301 instructor Field ge; r289 mypy stub GEval",
            goal=(
                "Pydantic leftover JudgeScore.model_construct(score=1.0) skips validators so a "
                "planted restock lie never runs the 0..1 ge/le check. Use model_validate; fail "
                "on construct."
            ),
            plan="Dump model_construct, switch to model_validate, prove planted restock fail.",
            outcome=(
                "Local path uses model_validate. Planted restock 0.16 locally. Handoff: a worker "
                "still calls leftover model_construct for 'speed'."
            ),
            ticket=(
                "Title: JudgeScore.model_construct leftover skips ge/le. planted restock forced "
                "score=1.0."
            ),
            src="evals/pyd_judge.py",
            src_obs="JudgeScore.model_construct(score=raw or 1.0)  # leftover skip validators",
            run="evals/pyd_judge.py",
            fail_obs="raw None → construct 1.0 leftover. planted restock pass",
            inspect="evals/pyd_judge.py",
            inspect_obs="model_construct leftover. validators never see None or 1.0 override",
            first_path="evals/pyd_judge.py",
            first_old="model_construct(score=raw or 1.0)",
            first_new="model_construct(score=raw if raw is not None else 0.0)",
            first_obs="still construct leftover; validators skipped; 0.0 then skip-helper pass",
            rate_tail="construct leftover still skips validators",
            still_after_429="model_construct leftover; planted restock not validated",
            grep="model_construct|model_validate|JudgeScore",
            grep_obs="worker still construct; cannot change that image here",
            plan_change="local model_validate; document worker leftover construct",
            fix_path="evals/pyd_judge.py",
            fix_old="JudgeScore.model_construct(score=raw if raw is not None else 0.0)",
            fix_new="JudgeScore.model_validate({'score': raw})",
            fix_obs="local planted 0.16. worker leftover construct HANDOFF",
            retry_obs="502 unused. worker leftover model_construct. Partial",
            test="tests/test_pyd_validate_not_construct.py",
            test_body="xfail worker construct leftover; local model_validate",
            test_obs="worker leftover construct. Partial",
            suite_obs="local validate. worker leftover construct. Partial.",
            gate_obs="local validate. worker leftover construct. Partial.",
            diff_obs=" evals/pyd_judge.py | 4+-\n HANDOFF worker construct\n",
            residual="Worker still calls leftover model_construct for speed. Partial.",
        ),
    )
)

# r310 metric leftover
PAIRS.append(
    (
        _ok(
            slug="contextual-precision-k-one-d95k",
            domain="chunk-k",
            kind="metric",
            avoided="Faithfulness empty-ctx; r262 pgvector L2 as relevancy; r8 ctxrecall vs precision",
            goal=(
                "ContextualPrecision leftover k=1 scores only the first chunk so a planted "
                "membership-freeze lie in chunk 2 never affects the 0.91. Score k=all retrieved "
                "and fail if any later chunk contradicts."
            ),
            plan="Dump k=1, score all retrieved chunks, prove planted chunk-2 lie fail.",
            outcome=(
                "k=all retrieved. Planted chunk-2 membership-freeze 0.17 fail-closed. Residual: "
                "a retrieval debug CLI still prints leftover k=1."
            ),
            ticket=(
                "Title: ContextualPrecision 0.91 leftover k=1. planted membership-freeze is chunk 2."
            ),
            src="evals/ctx_precision.py",
            src_obs="ContextualPrecisionMetric(k=1)  # leftover 'first hit is what users see'",
            run="evals/ctx_precision.py",
            fail_obs="chunk2 has freeze lie. leftover k=1 score 0.91",
            inspect="evals/ctx_precision.py",
            inspect_obs="k=1 leftover. later chunks ignored",
            first_path="evals/ctx_precision.py",
            first_old="k=1",
            first_new="k=2",
            first_obs="k=2 still drops chunk 3 planted on 4-chunk retrieves",
            rate_tail="k=2 leftover still misses later chunks",
            still_after_429="fixed k leftover; planted can hide at k+1",
            grep="ContextualPrecision|k=|retrieval_context",
            grep_obs="k must be len(retrieval_context); no fixed slice",
            plan_change="k=len(ctx); fail if any later chunk contradicts gold",
            fix_path="evals/ctx_precision.py",
            fix_old="ContextualPrecisionMetric(k=2)",
            fix_new="ContextualPrecisionMetric(k=len(tc.retrieval_context))",
            fix_obs="planted chunk-2 0.17 fail-closed. all chunks scored",
            retry_obs="502 then retry; 5 pass 1 fail planted chunk-2 0.17",
            test="tests/test_ctx_precision_all_chunks.py",
            test_body="assert k == len(ctx); planted later chunk < 0.3",
            test_obs="test_contextual_precision_not_k_one",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed chunk-2 lie",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed chunk-2 lie",
            diff_obs=" evals/ctx_precision.py | 4+-\n tests/test_ctx_precision_all_chunks.py | 12++\n",
            residual="Retrieval debug CLI still prints leftover k=1.",
        ),
        _bad(
            slug="hallu-min-score-vs-threshold-e96l",
            domain="hallu-pin",
            kind="metric",
            avoided="Faithfulness empty-ctx; r02 halluc threshold polarity; r6 hallucination false-neg",
            goal=(
                "HallucinationMetric leftover still reads minimum_score after the pin renamed it "
                "to threshold so planted restock hallucinations 0.8 (bad) compare against 0.0 "
                "and pass. Read threshold; fail-closed."
            ),
            plan="Dump minimum_score alias, bind threshold, prove planted restock fail.",
            outcome=(
                "Local metric uses threshold=0.5. Planted restock 0.8 fails. Handoff: the "
                "published pin leftover still exposes only minimum_score=0.0."
            ),
            ticket=(
                "Title: HallucinationMetric leftover minimum_score=0.0 after rename to threshold. "
                "planted restock 0.8 passes."
            ),
            src="evals/hallu_pin.py",
            src_obs="HallucinationMetric(minimum_score=0.5)  # leftover kw ignored on new pin",
            run="evals/hallu_pin.py",
            fail_obs="threshold default 0.0 leftover. planted restock 0.8 is_successful True",
            inspect="evals/hallu_pin.py",
            inspect_obs="minimum_score leftover stored on self but measure reads threshold",
            first_path="evals/hallu_pin.py",
            first_old="minimum_score=0.5",
            first_new="minimum_score=0.5, threshold=0.5",
            first_obs="local both set. CI pin leftover rejects threshold kw and drops to 0.0",
            rate_tail="CI pin leftover ignores threshold; planted 0.8 pass",
            still_after_429="CI leftover minimum_score-only pin",
            grep="minimum_score|threshold|HallucinationMetric",
            grep_obs="cannot bump the shared pin from this ticket",
            plan_change="local threshold=; document pin leftover handoff",
            fix_path="evals/hallu_pin.py",
            fix_old="HallucinationMetric(minimum_score=0.5, threshold=0.5)",
            fix_new="HallucinationMetric(threshold=0.5)",
            fix_obs="local planted 0.8 fail. CI leftover minimum_score HANDOFF",
            retry_obs="502 unused. CI leftover pin. Partial",
            test="tests/test_hallu_threshold_not_min.py",
            test_body="xfail CI leftover minimum_score; local threshold 0.5",
            test_obs="CI leftover pin. Partial",
            suite_obs="local threshold fail. CI leftover minimum_score. Partial.",
            gate_obs="local threshold fail. CI leftover minimum_score. Partial.",
            diff_obs=" evals/hallu_pin.py | 2+-\n HANDOFF pin\n",
            residual="Published pin leftover still exposes only minimum_score=0.0. Partial.",
        ),
    )
)

# r311 trace leftover
PAIRS.append(
    (
        _ok(
            slug="zipkin-64bit-span-join-f97m",
            domain="zipkin-join",
            kind="trace",
            avoided="r293 sample_rate; r257 otel span ended; r297 baggage overwrite",
            goal=(
                "Zipkin leftover 64-bit span ids cannot join 128-bit OTEL metric spans so a "
                "planted pickup-window fail never attaches to the parent eval trace. Emit 128-bit "
                "ids and join on trace_id."
            ),
            plan="Dump span id width, emit 128-bit, join planted pickup-window to the parent.",
            outcome=(
                "Exporter emits 128-bit span ids. Planted pickup-window 0.15 attached. Residual: "
                "a legacy Zipkin UI leftover still truncates high bits."
            ),
            ticket=(
                "Title: Zipkin leftover 64-bit span ids. planted pickup-window OTEL span 128-bit "
                "orphan; parent eval looks all-pass."
            ),
            src="evals/zipkin_export.py",
            src_obs="span_id = token[:16]  # leftover 64-bit Zipkin",
            run="evals/zipkin_export.py",
            fail_obs="parent 64-bit. planted 128-bit orphan. UI 0 fails",
            inspect="evals/zipkin_export.py",
            inspect_obs="token[:16] leftover drops high bits used by OTEL metric spans",
            first_path="evals/zipkin_export.py",
            first_old="span_id = token[:16]",
            first_new="span_id = token[:16].zfill(32)",
            first_obs="zfill leftover still not the real high bits; join fails",
            rate_tail="zfill leftover; planted still orphan",
            still_after_429="64-bit leftover; planted pickup-window orphan",
            grep="span_id|trace_id|zipkin",
            grep_obs="pass through 128-bit hex; join on full trace_id",
            plan_change="emit full 128-bit span_id; join parent on trace_id",
            fix_path="evals/zipkin_export.py",
            fix_old="span_id = token[:16].zfill(32)",
            fix_new="span_id = token  # 128-bit hex; do not slice",
            fix_obs="planted pickup-window 0.15 attached to parent",
            retry_obs="502 then retry; 5 pass 1 fail planted pickup-window 0.15",
            test="tests/test_zipkin_128bit_join.py",
            test_body="assert span_id hex len==32; planted child joins parent",
            test_obs="test_zipkin_does_not_truncate_span_id",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed pickup-window",
            diff_obs=" evals/zipkin_export.py | 4+-\n tests/test_zipkin_128bit_join.py | 12++\n",
            residual="Legacy Zipkin UI leftover still truncates high bits.",
        ),
        _bad(
            slug="tempo-tenant-leftover-g98n",
            domain="tempo-tenant",
            kind="trace",
            avoided="r293 sample_rate; r297 jaeger service rename; r257 ended span",
            goal=(
                "Grafana Tempo leftover X-Scope-OrgID=eval-old so planted membership-freeze "
                "spans land in the old tenant and the new tenant looks all-pass. Send the current "
                "tenant header."
            ),
            plan="Dump tenant header, switch to eval-new, prove planted span visible locally.",
            outcome=(
                "Local exporter X-Scope-OrgID=eval-new. Planted membership-freeze 0.18 visible. "
                "Handoff: the gateway leftover still overwrites the header to eval-old."
            ),
            ticket=(
                "Title: Tempo leftover tenant eval-old. planted membership-freeze spans missing "
                "from eval-new queries."
            ),
            src="evals/tempo_export.py",
            src_obs="headers={'X-Scope-OrgID': os.getenv('TEMPO_TENANT', 'eval-old')}  # leftover",
            run="evals/tempo_export.py",
            fail_obs="spans in eval-old leftover. eval-new query 0 planted fails",
            inspect="evals/tempo_export.py",
            inspect_obs="default leftover eval-old. gateway also overwrites",
            first_path="evals/tempo_export.py",
            first_old="os.getenv('TEMPO_TENANT', 'eval-old')",
            first_new="os.getenv('TEMPO_TENANT', 'eval-new')",
            first_obs="default new. gateway leftover still forces eval-old",
            rate_tail="gateway leftover tenant overwrite eval-old",
            still_after_429="gateway leftover; planted in eval-old",
            grep="X-Scope-OrgID|TEMPO_TENANT|eval-old",
            grep_obs="cannot change the shared gateway from this repo",
            plan_change="local eval-new; document gateway leftover handoff",
            fix_path="evals/tempo_export.py",
            fix_old="headers={'X-Scope-OrgID': os.getenv('TEMPO_TENANT', 'eval-new')}",
            fix_new="headers={'X-Scope-OrgID': 'eval-new'}  # ignore env leftover",
            fix_obs="local planted 0.18 in eval-new. gateway leftover HANDOFF",
            retry_obs="502 unused. gateway leftover tenant. Partial",
            test="tests/test_tempo_tenant_header.py",
            test_body="xfail gateway leftover eval-old; local header eval-new",
            test_obs="gateway leftover tenant. Partial",
            suite_obs="local eval-new. gateway leftover eval-old. Partial.",
            gate_obs="local eval-new. gateway leftover eval-old. Partial.",
            diff_obs=" evals/tempo_export.py | 2+-\n HANDOFF gateway tenant\n",
            residual="Gateway leftover still overwrites X-Scope-OrgID to eval-old. Partial.",
        ),
    )
)
