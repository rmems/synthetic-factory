"""Unique eval-harness leftover plants r302–r307. Not r50–r252 or r253–r293 clones."""

from mill_plants import PAIRS, _bad, _ok

# ---------------------------------------------------------------------------
# r302 metric leftover — not Faithfulness empty-ctx, not r261 instructor tools
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="knowledge-retention-last3-n79u",
            domain="warranty-memory",
            kind="metric",
            avoided="Faithfulness empty-ctx; r7 conversation-turn-index; r3 convo-geval-turns",
            goal=(
                "KnowledgeRetentionMetric leftover turns[-3:] misses the turn-1 retraction of "
                "lifetime warranty so planted replies still score 0.93. Score the full transcript "
                "and fail if a retraction is ignored."
            ),
            plan="Dump turn slice, score full transcript, prove planted lifetime-warranty fail.",
            outcome=(
                "Metric sees all turns including the retraction. Planted lifetime-warranty 0.15. "
                "Residual: a dashboard still charts the leftover last-3 helper."
            ),
            ticket=(
                "Title: KnowledgeRetention 0.93 on planted lifetime-warranty. leftover turns[-3:] "
                "drops the retraction in turn 1."
            ),
            src="evals/knowledge_retention.py",
            src_obs="turns_used = convo.turns[-3:]  # leftover 'recent context only'",
            run="evals/knowledge_retention.py",
            fail_obs="retraction is turn 1. last-3 leftover misses it. planted 0.93",
            inspect="evals/knowledge_retention.py",
            inspect_obs="slice leftover. KnowledgeRetentionMetric only sees last 3 user/assistant pairs",
            first_path="evals/knowledge_retention.py",
            first_old="convo.turns[-3:]",
            first_new="convo.turns[-5:]",
            first_obs="[-5:] still drops turn 0 system policy on 6-turn planted dialogs",
            rate_tail="[-5:] leftover still drops the retraction on longer threads",
            still_after_429="slice leftover; planted lifetime-warranty 0.93",
            grep="turns\\[-|KnowledgeRetention|retract",
            grep_obs="pass the full transcript; fail if retraction ignored",
            plan_change="full turns; no negative slice; fail if retraction not reflected",
            fix_path="evals/knowledge_retention.py",
            fix_old="convo.turns[-5:]",
            fix_new="convo.turns  # full transcript; retractions must be visible",
            fix_obs="planted lifetime-warranty 0.15 fail-closed. retraction visible",
            retry_obs="502 then retry; 5 pass 1 fail planted lifetime-warranty 0.15",
            test="tests/test_knowledge_retention_full_turns.py",
            test_body="assert retraction turn included; planted < 0.3",
            test_obs="test_retention_uses_full_transcript_not_last3",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed lifetime-warranty",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed lifetime-warranty",
            diff_obs=" evals/knowledge_retention.py | 4+-\n tests/test_knowledge_retention_full_turns.py | 12++\n",
            residual="Dashboard still charts the leftover last-3 helper.",
        ),
        _bad(
            slug="tool-correctness-unordered-o80v",
            domain="payment-order",
            kind="metric",
            avoided="r261 instructor tool classname; r6 toolcorrectness args; Faithfulness empty-ctx",
            goal=(
                "ToolCorrectness leftover should_exact_match=False ignores tool order so planted "
                "Cancel then Charge vs gold Charge then Cancel scores 1.0. Require ordered tools."
            ),
            plan="Dump should_exact_match, require order, pin kwargs, prove planted order fail.",
            outcome=(
                "Local should_exact_match=True and order checked. Planted Cancel-then-Charge fails. "
                "Handoff: tox.ini still sets leftover should_exact_match=False."
            ),
            ticket=(
                "Title: ToolCorrectness 1.0 on planted Cancel then Charge. leftover "
                "should_exact_match=False ignores order."
            ),
            src="evals/tool_order.py",
            src_obs="ToolCorrectnessMetric(should_exact_match=False)  # leftover bag-of-tools",
            run="evals/tool_order.py",
            fail_obs="planted [Cancel, Charge] vs gold [Charge, Cancel] score=1.0 leftover unordered",
            inspect="evals/tool_order.py",
            inspect_obs="should_exact_match False leftover. no order comparator",
            first_path="evals/tool_order.py",
            first_old="should_exact_match=False",
            first_new="should_exact_match=True",
            first_obs="local True. tox.ini leftover override False",
            rate_tail="tox leftover should_exact_match=False",
            still_after_429="tox leftover unordered; planted still 1.0",
            grep="should_exact_match|ToolCorrectness|tox.ini",
            grep_obs="cannot change shared tox.ini pin from this ticket",
            plan_change="local True; document tox leftover handoff",
            fix_path="evals/tool_order.py",
            fix_old="ToolCorrectnessMetric(should_exact_match=True)",
            fix_new="ToolCorrectnessMetric(should_exact_match=True)  # tox leftover still False",
            fix_obs="local planted order fail. tox leftover False HANDOFF",
            retry_obs="502 unused. tox leftover unordered. Partial",
            test="tests/test_tool_order_exact.py",
            test_body="xfail tox leftover False; local exact order",
            test_obs="tox leftover unordered. Partial",
            suite_obs="local ordered fail. tox leftover False. Partial.",
            gate_obs="local ordered fail. tox leftover False. Partial.",
            diff_obs=" evals/tool_order.py | 2+-\n HANDOFF tox.ini\n",
            residual="tox.ini still sets leftover should_exact_match=False. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r303 trace leftover — not r293 sample_rate, not r257 ended span
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="openllmetry-redact-context-p81w",
            domain="replay-faith",
            kind="trace",
            avoided="r293 tracing sample_rate; r16 @observe; r257 otel span ended",
            goal=(
                "OpenLLMetry leftover TRACELOOP_TRACE_CONTENT=false redacts retrieval_context from "
                "spans so a span-replay Faithfulness sees empty context and fail-opens to 1.0. "
                "Keep content on metric spans; fail-closed on empty replay."
            ),
            plan="Dump TRACELOOP_TRACE_CONTENT, keep content on metric spans, fail-closed empty replay.",
            outcome=(
                "Metric spans keep retrieval_context. Empty replay raises. Planted hours-closed "
                "0.16. Residual: the PII job still unsets TRACELOOP_TRACE_CONTENT globally."
            ),
            ticket=(
                "Title: span-replay Faithfulness 1.0 on planted hours-closed. leftover "
                "TRACELOOP_TRACE_CONTENT=false redacts context; empty replay fail-opens."
            ),
            src="evals/span_replay.py",
            src_obs="os.environ.setdefault('TRACELOOP_TRACE_CONTENT', 'false')  # leftover PII default",
            run="evals/span_replay.py",
            fail_obs="replay retrieval_context=[]. score=1.0 leftover fail-open empty",
            inspect="evals/span_replay.py",
            inspect_obs="empty context leftover treated as nothing to contradict → 1.0",
            first_path="evals/span_replay.py",
            first_old="setdefault('TRACELOOP_TRACE_CONTENT', 'false')",
            first_new="setdefault('TRACELOOP_TRACE_CONTENT', 'true')",
            first_obs="default true. CI leftover still unsets the var for PII",
            rate_tail="CI leftover unsets TRACELOOP_TRACE_CONTENT; replay empty",
            still_after_429="CI redact leftover; planted replay 1.0",
            grep="TRACELOOP_TRACE_CONTENT|retrieval_context|fail-open",
            grep_obs="keep content on metric spans; fail-closed if replay context empty",
            plan_change="metric-span content allowlist; raise on empty replay; ignore global unset",
            fix_path="evals/span_replay.py",
            fix_old="score = 1.0 if not ctx else faith.measure(tc)",
            fix_new="if not ctx: raise EmptyReplay()\\nscore = faith.measure(tc)",
            fix_obs="empty replay raises. planted hours-closed 0.16 when content present",
            retry_obs="502 then retry; 5 pass 1 fail planted hours-closed 0.16",
            test="tests/test_span_replay_fail_closed.py",
            test_body="assert empty replay raises EmptyReplay; content kept on metric spans",
            test_obs="test_span_replay_empty_context_fail_closed",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed hours-closed",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed hours-closed",
            diff_obs=" evals/span_replay.py | 8+-\n tests/test_span_replay_fail_closed.py | 12++\n",
            residual="PII job still unsets TRACELOOP_TRACE_CONTENT globally.",
        ),
        _bad(
            slug="datadog-score-tag-card-q82x",
            domain="score-gauge",
            kind="trace",
            avoided="r293 tracing sample_rate; r266 prom last-write; r267 grafana 0-100",
            goal=(
                "Datadog leftover cardinality limiter drops the metric_score span tag so a no-data "
                "monitor leftover is treated as OK and planted score 0.18 is invisible. Export a "
                "gauge; treat no-data as alert."
            ),
            plan="Dump tag policy, export a gauge not a high-card tag, alert on no-data.",
            outcome=(
                "Local gauge eval.metric_score exported. Planted 0.18 visible locally. Handoff: "
                "org cardinality still drops the leftover span tag and the monitor stays no-data OK."
            ),
            ticket=(
                "Title: Datadog no-data leftover OK. metric_score tag dropped by cardinality limiter. "
                "planted 0.18 never leaves the agent."
            ),
            src="evals/dd_export.py",
            src_obs="span.set_tag('metric_score', score)  # leftover high-cardinality tag",
            run="evals/dd_export.py",
            fail_obs="agent drop leftover metric_score. monitor no-data treated as OK",
            inspect="evals/dd_export.py",
            inspect_obs="tag leftover. org limiter max 100 tags; metric_score evicted",
            first_path="evals/dd_export.py",
            first_old="span.set_tag('metric_score', score)",
            first_new="span.set_tag('eval_score', score)  # rename still a tag",
            first_obs="rename still dropped leftover limiter. need a gauge",
            rate_tail="limiter leftover still drops the renamed tag",
            still_after_429="cardinality leftover; planted 0.18 invisible",
            grep="metric_score|cardinality|no-data",
            grep_obs="cannot raise org limiter from this repo",
            plan_change="local DogStatsD gauge; document org leftover handoff",
            fix_path="evals/dd_export.py",
            fix_old="span.set_tag('eval_score', score)",
            fix_new="statsd.gauge('eval.metric_score', score)",
            fix_obs="local gauge 0.18. org tag limiter leftover HANDOFF",
            retry_obs="502 unused. org leftover no-data OK. Partial",
            test="tests/test_dd_gauge_not_tag.py",
            test_body="xfail org limiter; local gauge eval.metric_score",
            test_obs="org leftover no-data OK. Partial",
            suite_obs="local gauge visible. org leftover limiter. Partial.",
            gate_obs="local gauge visible. org leftover limiter. Partial.",
            diff_obs=" evals/dd_export.py | 4+-\n HANDOFF org cardinality\n",
            residual="Org cardinality limiter still drops leftover span tags; monitor no-data OK. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r304 fmt leftover — not Black wrap, not isort reorder
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="sqlfluff-templater-limit-r83y",
            domain="sql-gold",
            kind="fmt",
            avoided="r290 Black wrap evaluation_steps; r290 isort params reorder",
            goal=(
                "sqlfluff leftover jinja templater refund_days=90 rewrites gold expected SQL "
                "LIMIT 30 into LIMIT 90. Disable templater on goldens and compare parsed AST."
            ),
            plan="Dump sqlfluff templater, stop rewriting goldens, AST-compare LIMIT 30 vs 90.",
            outcome=(
                "Goldens excluded from templater. Planted LIMIT 90 fails AST compare. Residual: "
                "dbt vars leftover refund_days=90 still used for non-golden SQL."
            ),
            ticket=(
                "Title: gold expected LIMIT 30 became LIMIT 90 after leftover sqlfluff templater "
                "refund_days=90."
            ),
            src=".sqlfluff",
            src_obs="[sqlfluff:templater:jinja:context]\nrefund_days=90  # leftover dbt var",
            run="evals/sql_gold_eval.py",
            fail_obs="gold file now LIMIT 90 leftover templater. planted matches 'gold' 1.0",
            inspect=".sqlfluff",
            inspect_obs="templater leftover applies to goldens/sql/*.sql",
            first_path=".sqlfluff",
            first_old="refund_days=90",
            first_new="refund_days=30",
            first_obs="local 30. CI leftover uses dbt_project vars 90",
            rate_tail="CI leftover dbt vars refund_days=90",
            still_after_429="CI templater leftover; gold LIMIT 90",
            grep="refund_days|templater|goldens/sql",
            grep_obs="exclude goldens from sqlfluff; compare AST not formatted text",
            plan_change="no templater on goldens; AST compare LIMIT clause",
            fix_path="evals/sql_gold_eval.py",
            fix_old="assert formatted_gold == formatted_actual",
            fix_new="assert ast_limit(gold)==30 and ast_limit(actual)==30",
            fix_obs="planted LIMIT 90 fails AST. gold LIMIT 30 preserved",
            retry_obs="502 then retry; 5 pass 1 fail planted LIMIT 90",
            test="tests/test_sql_gold_no_templater.py",
            test_body="assert goldens not in sqlfluff paths; LIMIT 30 stays 30",
            test_obs="test_sql_goldens_excluded_from_templater",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed LIMIT 90",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed LIMIT 90",
            diff_obs=" .sqlfluff | 4+-\n evals/sql_gold_eval.py | 6+-\n tests/test_sql_gold_no_templater.py | 12++\n",
            residual="dbt vars leftover refund_days=90 still used for non-golden SQL.",
        ),
        _bad(
            slug="shfmt-heredoc-prompt-split-s84z",
            domain="hold-sh",
            kind="fmt",
            avoided="r290 Black wrap evaluation_steps; r290 isort params reorder",
            goal=(
                "shfmt leftover rewrites a bash heredoc so 'expected: 15-min hold' splits and the "
                "parser reads 15 then ignores min. Keep the prompt in a .txt file and exclude "
                "scripts/eval.sh from shfmt."
            ),
            plan="Dump heredoc, move prompt to txt, exclude shfmt, prove planted 15-min still parsed.",
            outcome=(
                "Local prompt lives in prompts/hold.txt. Parser reads 15-min hold. Handoff: "
                "pre-commit leftover still runs shfmt --write on scripts/eval.sh."
            ),
            ticket=(
                "Title: shfmt leftover split expected: 15-min hold across lines. parser reads 15 "
                "and treats planted 120-min as pass."
            ),
            src="scripts/eval.sh",
            src_obs="PROMPT=$(cat <<'EOF'\nexpected: 15-min hold\nEOF\n)",
            run="evals/hold_sh_eval.py",
            fail_obs="after shfmt, parser token=15 leftover. planted 120-min still pass",
            inspect="scripts/eval.sh",
            inspect_obs="shfmt leftover broke the heredoc; parser regex ^expected: ([0-9]+)",
            first_path="scripts/eval.sh",
            first_old="expected: 15-min hold",
            first_new="expected: 15min hold",
            first_obs="unsplit locally. pre-commit leftover shfmt --write still splits",
            rate_tail="pre-commit leftover shfmt still rewrites eval.sh",
            still_after_429="pre-commit leftover; parser still 15 vs 120 pass",
            grep="shfmt|eval.sh|15-min",
            grep_obs="cannot disable org pre-commit hook from this ticket",
            plan_change="prompt file locally; document pre-commit leftover handoff",
            fix_path="evals/hold_sh_eval.py",
            fix_old="parse_expected(os.environ['PROMPT'])",
            fix_new="parse_expected(Path('prompts/hold.txt').read_text())",
            fix_obs="local 15-min parsed. pre-commit leftover shfmt HANDOFF",
            retry_obs="502 unused. pre-commit leftover shfmt. Partial",
            test="tests/test_hold_prompt_file.py",
            test_body="xfail pre-commit shfmt leftover; local prompt file",
            test_obs="pre-commit leftover shfmt. Partial",
            suite_obs="local prompt file. pre-commit leftover. Partial.",
            gate_obs="local prompt file. pre-commit leftover. Partial.",
            diff_obs=" evals/hold_sh_eval.py | 4+-\n prompts/hold.txt | 2++\n HANDOFF shfmt hook\n",
            residual="pre-commit leftover still runs shfmt --write on scripts/eval.sh. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r305 cache leftover — not r253 xdist, not r268 docker layer
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="nix-gcroot-eval-result-t85a",
            domain="nix-eval",
            kind="cache",
            avoided="r253 xdist cache; r268 docker layer .deepeval; r305 not Helm",
            goal=(
                "Leftover Nix gcroot /nix/var/nix/gcroots/per-user/ci/eval-result pins yesterday's "
                "closure with old goldens so nix run never sees the planted free-shipping-over-35 "
                "row. Drop the gcroot; hash goldens into the flake app."
            ),
            plan="Dump gcroot, drop it, hash goldens, prove planted free-shipping fail.",
            outcome=(
                "gcroot removed. flake app hashes goldens. Planted free-shipping-over-35 0.19. "
                "Residual: a laptop still has a leftover result symlink."
            ),
            ticket=(
                "Title: nix run uses leftover eval-result gcroot. planted free-shipping-over-35 "
                "golden missing from yesterday's closure."
            ),
            src="flake.nix",
            src_obs="eval-app = pkgs.writeShellApplication { name = \"eval\"; }  # goldens not in src",
            run="evals/shipping_eval.py",
            fail_obs="closure leftover missing goldens/ship35.jsonl. dashboard still 0.94",
            inspect="/nix/var/nix/gcroots/per-user/ci/eval-result",
            inspect_obs="gcroot leftover points at 2026-08-18 closure without ship35 golden",
            first_path="flake.nix",
            first_old="src = ./evals;",
            first_new="src = ./.;  # still does not delete the gcroot",
            first_obs="flake src wider. ci leftover still nix run /nix/var/nix/gcroots/.../eval-result",
            rate_tail="ci leftover gcroot path; planted golden absent",
            still_after_429="gcroot leftover; planted ship35 missing",
            grep="gcroot|eval-result|goldens",
            grep_obs="delete gcroot; nix run .#eval; goldens in derivation",
            plan_change="drop gcroot; goldens hashed in flake; nix run .#eval",
            fix_path="ci/eval.sh",
            fix_old="nix run /nix/var/nix/gcroots/per-user/ci/eval-result",
            fix_new="nix run .#eval",
            fix_obs="planted ship35 0.19 fail-closed. gcroot unused",
            retry_obs="502 then retry; 5 pass 1 fail planted ship35 0.19",
            test="tests/test_nix_eval_hashes_goldens.py",
            test_body="assert goldens in drv; ci script does not use eval-result gcroot",
            test_obs="test_nix_eval_not_pinned_to_gcroot",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed ship35",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed ship35",
            diff_obs=" flake.nix | 4+-\n ci/eval.sh | 2+-\n tests/test_nix_eval_hashes_goldens.py | 12++\n",
            residual="A laptop still has a leftover result symlink to the old closure.",
        ),
        _bad(
            slug="pants-process-cache-omit-u86b",
            domain="pants-eval",
            kind="cache",
            avoided="r253 xdist cache; r268 docker layer; r291 Helm judge-model",
            goal=(
                "Pants leftover process cache inputs omit goldens/ so remote HIT skips re-eval after "
                "planting a restock-window row. Declare goldens as digest inputs."
            ),
            plan="Dump process inputs, add goldens digest, prove planted restock fail locally.",
            outcome=(
                "Local process inputs include goldens digest. Planted restock-window 0.20 locally. "
                "Handoff: org remote cache still HIT for the old input digest."
            ),
            ticket=(
                "Title: ./pants eval leftover cache HIT. goldens/ not in process inputs. planted "
                "restock-window row not scored."
            ),
            src="evals/BUILD",
            src_obs="pex_binary(name='eval', sources=['*.py'])  # leftover omits goldens/",
            run="evals/restock_eval.py",
            fail_obs="Remote cache HIT leftover. planted restock-window absent from the pex",
            inspect="evals/BUILD",
            inspect_obs="sources leftover *.py only. goldens not a digest input",
            first_path="evals/BUILD",
            first_old="sources=['*.py']",
            first_new="sources=['*.py', 'goldens/*.jsonl']",
            first_obs="local miss. org remote leftover HIT on old digest",
            rate_tail="remote leftover HIT; planted restock not run",
            still_after_429="org remote leftover HIT; planted restock absent",
            grep="pex_binary|goldens|remote cache",
            grep_obs="cannot flush org remote from this repo",
            plan_change="local goldens digest; document remote leftover handoff",
            fix_path="evals/BUILD",
            fix_old="pex_binary(name='eval', sources=['*.py', 'goldens/*.jsonl'])",
            fix_new="pex_binary(name='eval', sources=['*.py'], dependencies=[':goldens'])",
            fix_obs="local planted 0.20. remote HIT leftover HANDOFF",
            retry_obs="502 unused. org remote leftover HIT. Partial",
            test="tests/test_pants_goldens_digest.py",
            test_body="xfail remote HIT leftover; local goldens digest declared",
            test_obs="org remote leftover HIT. Partial",
            suite_obs="local planted fail. remote leftover HIT. Partial.",
            gate_obs="local planted fail. remote leftover HIT. Partial.",
            diff_obs=" evals/BUILD | 4+-\n HANDOFF org remote cache\n",
            residual="Org remote Pants cache still HIT for the old input digest. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r306 judge leftover — not GEval json_mode, not LiteLLM fallback
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="lmql-int-score-skip-v87c",
            domain="lmql-judge",
            kind="judge",
            avoided="r254 GEval extra=forbid; r253 LiteLLM fallback; r264 pandas NA fillna 0",
            goal=(
                "LMQL leftover where INT(score) in [0,1] coerces 0.2 to 0 then CI leftover "
                "'0 means skip' treats it as pass. Use a float 0..1; treat 0 as fail not skip."
            ),
            plan="Dump INT constraint, allow floats, stop skip-on-0, prove planted 0.2 fail.",
            outcome=(
                "Score is float 0..1. 0 is fail not skip. Planted lmql-judge 0.2 fail-closed. "
                "Residual: an old dashboard still labels 0 as skipped."
            ),
            ticket=(
                "Title: LMQL INT(score) leftover. planted 0.2 → 0 then skip-as-pass helper."
            ),
            src="evals/lmql_judge.lmql",
            src_obs='argmax "score: [SCORE]" where INT(SCORE) in [0, 1]',
            run="evals/lmql_judge_eval.py",
            fail_obs="planted 0.2 coerced 0. helper leftover skip-as-pass → gate green",
            inspect="evals/lmql_adapter.py",
            inspect_obs="if score == 0: return Skip()  # leftover 'model declined'",
            first_path="evals/lmql_judge.lmql",
            first_old="INT(SCORE) in [0, 1]",
            first_new="STOPS_AT(SCORE, '\\n') and FLOAT(SCORE) >= 0 and FLOAT(SCORE) <= 1",
            first_obs="float ok. leftover skip-on-0 helper still passes 0.0",
            rate_tail="skip-on-0 leftover still treats 0.0 as pass",
            still_after_429="skip-on-0 leftover; planted not fail-closed",
            grep="Skip\\(\\)|INT\\(SCORE\\)|skip-as-pass",
            grep_obs="0 is a fail; remove Skip helper",
            plan_change="float score; 0 fails the gate; no skip helper",
            fix_path="evals/lmql_adapter.py",
            fix_old="if score == 0: return Skip()",
            fix_new="if score is None: raise MissingScore()\n# 0.0 is a real fail",
            fix_obs="planted 0.2 fail-closed. 0.0 would also fail",
            retry_obs="502 then retry; 5 pass 1 fail planted 0.2",
            test="tests/test_lmql_float_no_skip.py",
            test_body="assert 0.0 is fail; 0.2 persisted; no Skip helper",
            test_obs="test_lmql_zero_is_fail_not_skip",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed 0.2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed 0.2",
            diff_obs=" evals/lmql_judge.lmql | 2+-\n evals/lmql_adapter.py | 6+-\n tests/test_lmql_float_no_skip.py | 12++\n",
            residual="An old dashboard still labels 0 as skipped.",
        ),
        _bad(
            slug="sglang-radix-smoke-prefix-w88d",
            domain="sglang-judge",
            kind="judge",
            avoided="r253 LiteLLM fallback; r261 anthropic prompt cache; r265 lru id(tc)",
            goal=(
                "SGLang leftover radix prefix cache from a smoke prompt 'always score 1.0' is "
                "reused for the judge so planted scores stay 1.0. Salt the prefix per eval and "
                "disable radix for judges."
            ),
            plan="Dump radix cache, add a per-eval salt, disable radix on the judge route.",
            outcome=(
                "Local judge route disable_radix=True plus a per-eval salt. Planted 0.17 locally. "
                "Handoff: shared GPU server leftover radix still holds the smoke prefix."
            ),
            ticket=(
                "Title: SGLang radix leftover. smoke 'always score 1.0' prefix reused by the judge. "
                "planted still 1.0."
            ),
            src="evals/sglang_judge.py",
            src_obs="Runtime(disable_radix_cache=False)  # leftover default shared GPU",
            run="evals/sglang_judge.py",
            fail_obs="radix hit leftover smoke prefix. judge completion 'score: 1.0'",
            inspect="evals/sglang_judge.py",
            inspect_obs="shared server leftover radix from smoke job 3 minutes earlier",
            first_path="evals/sglang_judge.py",
            first_old="disable_radix_cache=False",
            first_new="disable_radix_cache=True",
            first_obs="local flag true. shared GPU leftover process still radix-on",
            rate_tail="shared GPU leftover radix; planted 1.0",
            still_after_429="shared GPU leftover radix smoke prefix",
            grep="disable_radix|sglang|smoke",
            grep_obs="cannot restart the shared GPU process from this repo",
            plan_change="local disable_radix; document GPU leftover handoff",
            fix_path="evals/sglang_judge.py",
            fix_old="prompt = JUDGE_PREFIX + case",
            fix_new="prompt = os.urandom(8).hex() + JUDGE_PREFIX + case",
            fix_obs="local salt planted 0.17. GPU leftover radix HANDOFF",
            retry_obs="502 unused. shared GPU leftover radix. Partial",
            test="tests/test_sglang_radix_salt.py",
            test_body="xfail shared GPU leftover; local disable_radix and salt",
            test_obs="shared GPU leftover radix. Partial",
            suite_obs="local salt planted fail. GPU leftover radix. Partial.",
            gate_obs="local salt planted fail. GPU leftover radix. Partial.",
            diff_obs=" evals/sglang_judge.py | 6+-\n HANDOFF shared GPU radix\n",
            residual="Shared GPU leftover radix still holds the smoke prefix. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r307 metric leftover — not Faithfulness empty-ctx, not r275 alignment-only
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="role-adherence-system-only-x89e",
            domain="role-warranty",
            kind="metric",
            avoided="Faithfulness empty-ctx; r275 summ alignment-only; r10 prompt-alignment unused",
            goal=(
                "RoleAdherenceMetric leftover checks only the system prompt so a later tool result "
                "that contradicts 'never promise lifetime warranty' still scores 0.94. Include "
                "tool results and fail on contradiction."
            ),
            plan="Dump metric window, include tool results, fail if they contradict the role.",
            outcome=(
                "Metric includes tool results. Planted lifetime-warranty contradiction 0.14. "
                "Residual: a debug CLI still prints the leftover system-only score."
            ),
            ticket=(
                "Title: RoleAdherence 0.94 leftover system-only. tool result promised lifetime "
                "warranty against the role."
            ),
            src="evals/role_adherence.py",
            src_obs="window = [tc.system]  # leftover 'role lives in system'",
            run="evals/role_adherence.py",
            fail_obs="tool result 'lifetime warranty'. leftover system-only score 0.94",
            inspect="evals/role_adherence.py",
            inspect_obs="window leftover omits tools_called and tool results",
            first_path="evals/role_adherence.py",
            first_old="window = [tc.system]",
            first_new="window = [tc.system, tc.input]",
            first_obs="still omits tool results leftover; planted 0.94",
            rate_tail="tool results leftover omitted; planted 0.94",
            still_after_429="system+input leftover; contradiction in tool result",
            grep="RoleAdherence|tools_called|lifetime",
            grep_obs="include tool results; fail on contradiction",
            plan_change="window = system+input+tool results+output; fail contradiction",
            fix_path="evals/role_adherence.py",
            fix_old="window = [tc.system, tc.input]",
            fix_new="window = [tc.system, tc.input, *tc.tools_results, tc.actual_output]",
            fix_obs="planted contradiction 0.14 fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted lifetime-warranty 0.14",
            test="tests/test_role_adherence_includes_tools.py",
            test_body="assert tool results in window; planted < 0.3",
            test_obs="test_role_adherence_not_system_only",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed lifetime-warranty",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed lifetime-warranty",
            diff_obs=" evals/role_adherence.py | 6+-\n tests/test_role_adherence_includes_tools.py | 12++\n",
            residual="Debug CLI still prints the leftover system-only score.",
        ),
        _bad(
            slug="convo-completeness-intent-y90f",
            domain="slot-fill",
            kind="metric",
            avoided="Faithfulness empty-ctx; r259 convosim ignores intent; r7 turn-index",
            goal=(
                "ConversationCompleteness leftover scores intent match not slot fill so a planted "
                "missing order_id still scores 0.92. Require slots and fail if any are missing."
            ),
            plan="Dump completeness helper, require slots, prove planted missing order_id fail.",
            outcome=(
                "Local required slots include order_id. Planted missing order_id fails. Handoff: "
                "prod metric pin leftover still intent-only."
            ),
            ticket=(
                "Title: ConversationCompleteness 0.92 leftover intent-only. planted missing "
                "order_id still pass."
            ),
            src="evals/completeness.py",
            src_obs="score = intent_match(user, assistant)  # leftover no slots",
            run="evals/completeness.py",
            fail_obs="intent=refund. order_id missing. leftover 0.92",
            inspect="evals/completeness.py",
            inspect_obs="no required_slots leftover. intent-only helper",
            first_path="evals/completeness.py",
            first_old="score = intent_match(user, assistant)",
            first_new="score = intent_match(user, assistant) * slot_fill(required)",
            first_obs="local slots. prod pin leftover intent-only",
            rate_tail="prod leftover intent-only; planted missing order_id 0.92",
            still_after_429="prod leftover intent-only pin",
            grep="required_slots|intent_match|order_id",
            grep_obs="cannot bump prod pin from this ticket",
            plan_change="local required slots; document prod leftover intent-only",
            fix_path="evals/completeness.py",
            fix_old="required = []",
            fix_new="required = ['order_id', 'refund_window']",
            fix_obs="local planted missing order_id fail. prod leftover HANDOFF",
            retry_obs="502 unused. prod leftover intent-only. Partial",
            test="tests/test_completeness_slots.py",
            test_body="xfail prod intent-only leftover; local required order_id",
            test_obs="prod leftover intent-only. Partial",
            suite_obs="local slots fail. prod leftover intent-only. Partial.",
            gate_obs="local slots fail. prod leftover intent-only. Partial.",
            diff_obs=" evals/completeness.py | 6+-\n HANDOFF prod pin\n",
            residual="Prod metric pin leftover still intent-only. Partial.",
        ),
    )
)
