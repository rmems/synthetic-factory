"""Unique eval-harness leftover plants r337–r355. Not r319/GEval-cache/test_ clones."""

from mill_plants import PAIRS, _bad, _ok

# r337 secret leftover
PAIRS.append(
    (
        _ok(
            slug="vault-judge-kv-stale-f49m",
            domain="vault-eval",
            kind="secret",
            avoided="r293 empty judge key; r261 anthropic cache; r319 ClearML uri",
            goal=(
                "Vault leftover KV eval/judge-model still serves yesterday's cheap model so "
                "planted dual-void scores 1.0 under a loose judge. Read the versioned secret "
                "and fail if the model id != lock."
            ),
            plan="Dump KV version, pin lock model, prove planted dual-void fail.",
            outcome=(
                "Judge model comes from the lock version. Planted dual-void 0.13 fail-closed. "
                "Residual: an agent leftover still reads KV without a version."
            ),
            ticket=(
                "Title: Vault leftover KV eval/judge-model unversioned. planted dual-void 1.0 "
                "on cheap model."
            ),
            src="evals/vault_judge.py",
            src_obs="model = vault.read('eval/judge-model')['data']['id']  # leftover no version",
            run="evals/vault_judge.py",
            fail_obs="KV leftover cheap model. planted dual-void 1.0",
            inspect="evals/vault_judge.py",
            inspect_obs="unversioned leftover. lock file unused",
            first_path="evals/vault_judge.py",
            first_old="vault.read('eval/judge-model')['data']['id']",
            first_new="vault.read('eval/judge-model', version=2)['data']['id']",
            first_obs="v2 local. agent leftover still unversioned read",
            rate_tail="agent leftover unversioned KV",
            still_after_429="agent leftover cheap model; planted dual-void 1.0",
            grep="judge-model|vault.read|version",
            grep_obs="read lock version; refuse unversioned",
            plan_change="lockfile model id + KV version; refuse unversioned read",
            fix_path="evals/vault_judge.py",
            fix_old="vault.read('eval/judge-model', version=2)['data']['id']",
            fix_new="model = lockfile_model('judge.lock')",
            fix_obs="planted dual-void 0.13 on locked model",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-void 0.13",
            test="tests/test_vault_judge_version.py",
            test_body="assert model from lock version; unversioned unused",
            test_obs="test_vault_judge_not_unversioned",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-void",
            diff_obs=" evals/vault_judge.py | 6+-\n tests/test_vault_judge_version.py | 12++\n",
            residual="Agent leftover still reads KV without a version.",
        ),
        _bad(
            slug="sops-eval-env-zero-g50n",
            domain="sops-eval",
            kind="secret",
            avoided="r288 dotenv empty; r335 systemd envfile; r319 Aim hash",
            goal=(
                "sops leftover decrypts eval.env.yesterday so EVAL_THRESHOLD=0 and planted "
                "tax-void never fails. Decrypt eval.env at this SHA; fail if threshold is 0."
            ),
            plan="Dump sops file, decrypt SHA env, prove planted tax-void locally.",
            outcome=(
                "Local decrypt is eval.env at this SHA. Planted tax-void fails locally. Handoff: "
                "CI leftover still sops -d eval.env.yesterday."
            ),
            ticket=(
                "Title: sops leftover eval.env.yesterday. planted tax-void vs THRESHOLD=0."
            ),
            src=".sops.yaml",
            src_obs="path_regex: eval.env.yesterday$  # leftover",
            run="evals/tax_void.py",
            fail_obs="yesterday leftover THRESHOLD=0. planted tax-void pass",
            inspect="eval.env.yesterday",
            inspect_obs="EVAL_THRESHOLD=0 leftover",
            first_path=".sops.yaml",
            first_old="path_regex: eval.env.yesterday$",
            first_new="path_regex: eval.env$",
            first_obs="regex local. CI leftover still decrypts yesterday",
            rate_tail="CI leftover sops -d eval.env.yesterday",
            still_after_429="CI leftover yesterday env; planted tax-void pass",
            grep="eval.env.yesterday|sops -d|EVAL_THRESHOLD",
            grep_obs="cannot change CI sops invoke from this ticket",
            plan_change="local SHA env; document CI leftover yesterday file",
            fix_path="evals/tax_void.py",
            fix_old="load_dotenv('eval.env')",
            fix_new="load_dotenv(f'eval.env.{git_sha}')",
            fix_obs="local planted fail. CI leftover HANDOFF",
            retry_obs="502 unused. CI leftover yesterday env. Partial",
            test="tests/test_sops_env_sha.py",
            test_body="xfail CI leftover yesterday env; local SHA env",
            test_obs="CI leftover yesterday env. Partial",
            suite_obs="local SHA env. CI leftover yesterday. Partial.",
            gate_obs="local SHA env. CI leftover yesterday. Partial.",
            diff_obs=" evals/tax_void.py | 4+-\n HANDOFF sops yesterday\n",
            residual="CI leftover still sops -d eval.env.yesterday. Partial.",
        ),
    )
)

# r338 compile leftover
PAIRS.append(
    (
        _ok(
            slug="mypyc-gate-so-stale-h51o",
            domain="mypyc-eval",
            kind="compile",
            avoided="r289 mypy stub GEval; r270 metrics shadow; r319 ClearML uri",
            goal=(
                "mypyc leftover evals/gate.cpython-311.so still embeds threshold=0 so planted "
                "restock-void never fails. Rebuild the extension; fail if the .so mtime lags "
                "the .py."
            ),
            plan="Dump .so mtime, rebuild, prove planted restock-void fail.",
            outcome=(
                ".so rebuilt from gate.py. Planted restock-void 0.14 fail-closed. Residual: a "
                "wheel leftover still ships the old .so."
            ),
            ticket=(
                "Title: mypyc leftover gate.cpython-311.so threshold 0. planted restock-void pass."
            ),
            src="evals/gate.py",
            src_obs="THRESHOLD = 0.7\n# leftover .so still has 0",
            run="evals/gate.py",
            fail_obs="import gate leftover .so THRESHOLD=0. planted restock-void pass",
            inspect="evals/gate.cpython-311.so",
            inspect_obs=".so leftover mtime last week. py newer",
            first_path="evals/setup.py",
            first_old="name='evals'",
            first_new="name='evals'  # rebuild so",
            first_obs="comment only. import still hits leftover .so",
            rate_tail="import leftover .so first on sys.path",
            still_after_429=".so leftover; planted restock-void pass",
            grep="gate.cpython|mypyc|THRESHOLD",
            grep_obs="delete stale .so; rebuild; refuse mtime lag",
            plan_change="rebuild mypyc .so; fail if .so older than gate.py",
            fix_path="evals/gate.py",
            fix_old="THRESHOLD = 0.7",
            fix_new="THRESHOLD = 0.7  # assert not stale_so()",
            fix_obs="planted restock-void 0.14 after rebuild",
            retry_obs="502 then retry; 5 pass 1 fail planted restock-void 0.14",
            test="tests/test_mypyc_so_not_stale.py",
            test_body="assert .so mtime >= gate.py; threshold 0.7",
            test_obs="test_mypyc_gate_so_fresh",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed restock-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed restock-void",
            diff_obs=" evals/gate.py | 4+-\n tests/test_mypyc_so_not_stale.py | 12++\n",
            residual="Wheel leftover still ships the old .so.",
        ),
        _bad(
            slug="cython-gate-c-zero-i52p",
            domain="cython-eval",
            kind="compile",
            avoided="r289 mypy stub; r270 sitecustomize; r319 Aim hash",
            goal=(
                "Cython leftover evals/gate.c compiled with THRESHOLD 0 so planted "
                "pickup-void never fails. Regen gate.c from the .pyx locally."
            ),
            plan="Dump gate.c, regen, prove planted pickup-void locally.",
            outcome=(
                "Local gate.c regenerated with 0.7. Planted pickup-void fails locally. Handoff: "
                "the sdist leftover still vendors gate.c with 0."
            ),
            ticket=(
                "Title: Cython leftover gate.c THRESHOLD 0. planted pickup-void pass."
            ),
            src="evals/gate.pyx",
            src_obs="THRESHOLD = 0.7\n# leftover vendor gate.c has 0",
            run="evals/gate_cy.py",
            fail_obs="vendor leftover gate.c 0. planted pickup-void pass",
            inspect="evals/gate.c",
            inspect_obs="#define THRESHOLD 0 leftover",
            first_path="evals/gate.c",
            first_old="#define THRESHOLD 0",
            first_new="#define THRESHOLD 7",
            first_obs="7 local. sdist leftover still vendors 0",
            rate_tail="sdist leftover vendors gate.c 0",
            still_after_429="sdist leftover 0; planted pickup-void pass",
            grep="gate.c|THRESHOLD|cythonize",
            grep_obs="cannot rebuild sdist from this ticket",
            plan_change="local cythonize; document sdist leftover gate.c",
            fix_path="evals/gate.pyx",
            fix_old="THRESHOLD = 0.7",
            fix_new="THRESHOLD = 0.7  # local cythonize only",
            fix_obs="local planted fail. sdist leftover HANDOFF",
            retry_obs="502 unused. sdist leftover gate.c 0. Partial",
            test="tests/test_cython_gate_c.py",
            test_body="xfail sdist leftover gate.c 0; local cythonize 0.7",
            test_obs="sdist leftover gate.c. Partial",
            suite_obs="local cythonize 0.7. sdist leftover 0. Partial.",
            gate_obs="local cythonize 0.7. sdist leftover 0. Partial.",
            diff_obs=" evals/gate.pyx | 2+-\n HANDOFF sdist gate.c\n",
            residual="Sdist leftover still vendors gate.c with THRESHOLD 0. Partial.",
        ),
    )
)

# r339 serialize leftover
PAIRS.append(
    (
        _ok(
            slug="pickle-gate-pkl-j53q",
            domain="pickle-eval",
            kind="serialize",
            avoided="r276 celery pickle; r279 kedro pickle; r319 ClearML uri",
            goal=(
                "pickle leftover eval_gate.pkl still has threshold=0 so planted "
                "warranty-void never fails. Rebuild the pickle from source; fail if the pkl "
                "mtime lags gate.py."
            ),
            plan="Dump pkl, rebuild, prove planted warranty-void fail.",
            outcome=(
                "eval_gate.pkl rebuilt. Planted warranty-void 0.15 fail-closed. Residual: a "
                "notebook leftover still loads the old pkl path."
            ),
            ticket=(
                "Title: pickle leftover eval_gate.pkl threshold 0. planted warranty-void pass."
            ),
            src="evals/pickle_gate.py",
            src_obs="gate = pickle.load(open('eval_gate.pkl','rb'))  # leftover",
            run="evals/pickle_gate.py",
            fail_obs="pkl leftover threshold 0. planted warranty-void pass",
            inspect="eval_gate.pkl",
            inspect_obs="pkl leftover mtime last month",
            first_path="evals/pickle_gate.py",
            first_old="pickle.load(open('eval_gate.pkl','rb'))",
            first_new="pickle.load(open('eval_gate-v2.pkl','rb'))",
            first_obs="v2 local. notebook leftover still eval_gate.pkl",
            rate_tail="notebook leftover eval_gate.pkl",
            still_after_429="notebook leftover pkl; planted warranty-void pass",
            grep="eval_gate.pkl|pickle.load|threshold",
            grep_obs="rebuild pkl from gate.py; refuse stale mtime",
            plan_change="rebuild pkl from source; fail if pkl older than gate.py",
            fix_path="evals/pickle_gate.py",
            fix_old="pickle.load(open('eval_gate-v2.pkl','rb'))",
            fix_new="gate = build_gate_from_source()",
            fix_obs="planted warranty-void 0.15. pkl unused",
            retry_obs="502 then retry; 5 pass 1 fail planted warranty-void 0.15",
            test="tests/test_pickle_gate_fresh.py",
            test_body="assert gate built from source; stale pkl unused",
            test_obs="test_pickle_gate_not_stale_pkl",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed warranty-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed warranty-void",
            diff_obs=" evals/pickle_gate.py | 6+-\n tests/test_pickle_gate_fresh.py | 12++\n",
            residual="Notebook leftover still loads the old pkl path.",
        ),
        _bad(
            slug="hdf5-last-group-k54r",
            domain="hdf5-eval",
            kind="serialize",
            avoided="r266 prom last-write; r318 neptune last scalar; r319 Aim hash",
            goal=(
                "HDF5 leftover scores.h5 reader takes the last group so planted sla-void in "
                "an earlier group is hidden. Read all groups; fail if any score < threshold."
            ),
            plan="Dump h5 groups, min across groups, prove planted sla-void locally.",
            outcome=(
                "Local reader mins all groups. Planted sla-void visible locally. Handoff: the "
                "dashboard leftover still charts the last group only."
            ),
            ticket=(
                "Title: HDF5 leftover scores.h5 last group. planted sla-void hidden."
            ),
            src="evals/hdf5_scores.py",
            src_obs="score = h5['scores'][list(h5['scores'].keys())[-1]]  # leftover last group",
            run="evals/hdf5_scores.py",
            fail_obs="last group leftover 0.94. planted sla-void in group-1 hidden",
            inspect="evals/hdf5_scores.py",
            inspect_obs="last-key leftover. no min",
            first_path="evals/hdf5_scores.py",
            first_old="score = h5['scores'][list(h5['scores'].keys())[-1]]",
            first_new="score = h5['scores'][list(h5['scores'].keys())[0]]",
            first_obs="first leftover. dashboard still last",
            rate_tail="dashboard leftover last group",
            still_after_429="dashboard leftover last; planted sla-void hidden",
            grep="scores.h5|last group|min\\(",
            grep_obs="cannot change dashboard from this ticket",
            plan_change="local min all groups; document dashboard leftover last",
            fix_path="evals/hdf5_scores.py",
            fix_old="score = h5['scores'][list(h5['scores'].keys())[0]]",
            fix_new="score = min(h5['scores'][k][()] for k in h5['scores'])",
            fix_obs="local planted visible. dashboard leftover HANDOFF",
            retry_obs="502 unused. dashboard leftover last group. Partial",
            test="tests/test_hdf5_min_groups.py",
            test_body="xfail dashboard leftover last; local min all groups",
            test_obs="dashboard leftover last group. Partial",
            suite_obs="local min groups. dashboard leftover last. Partial.",
            gate_obs="local min groups. dashboard leftover last. Partial.",
            diff_obs=" evals/hdf5_scores.py | 4+-\n HANDOFF hdf5 dashboard\n",
            residual="Dashboard leftover still charts the last group only. Partial.",
        ),
    )
)

# r340 warehouse leftover
PAIRS.append(
    (
        _ok(
            slug="duckdb-view-latest-l55s",
            domain="duckdb-eval",
            kind="warehouse",
            avoided="r264 pandas NA; r268 dvc metrics; r319 ClearML uri",
            goal=(
                "DuckDB leftover VIEW eval_latest points at yesterday's table so planted "
                "proration-void never appears. Recreate the view on eval_<sha>."
            ),
            plan="Dump view SQL, pin sha table, prove planted proration-void fail.",
            outcome=(
                "VIEW eval_latest now is eval_<sha>. Planted proration-void 0.16 fail-closed. "
                "Residual: a BI leftover still queries eval_latest without recreate."
            ),
            ticket=(
                "Title: DuckDB leftover VIEW eval_latest. planted proration-void missing."
            ),
            src="evals/duckdb_eval.sql",
            src_obs="CREATE VIEW eval_latest AS SELECT * FROM eval_yesterday;  -- leftover",
            run="evals/duckdb_eval.py",
            fail_obs="view leftover yesterday table. planted proration-void absent",
            inspect="evals/duckdb_eval.sql",
            inspect_obs="eval_yesterday leftover. no sha table",
            first_path="evals/duckdb_eval.sql",
            first_old="FROM eval_yesterday",
            first_new="FROM eval_today",
            first_obs="today local. BI leftover still old view def",
            rate_tail="BI leftover queries stale view",
            still_after_429="stale view leftover; planted proration-void absent",
            grep="eval_latest|eval_yesterday|CREATE VIEW",
            grep_obs="CREATE OR REPLACE VIEW on eval_<sha>",
            plan_change="replace view as eval_<sha>; refuse eval_yesterday",
            fix_path="evals/duckdb_eval.sql",
            fix_old="FROM eval_today",
            fix_new="FROM eval_{{sha}}",
            fix_obs="planted proration-void 0.16 in view",
            retry_obs="502 then retry; 5 pass 1 fail planted proration-void 0.16",
            test="tests/test_duckdb_view_sha.py",
            test_body="assert view selects eval_<sha>; yesterday unused",
            test_obs="test_duckdb_view_not_yesterday",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed proration-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed proration-void",
            diff_obs=" evals/duckdb_eval.sql | 4+-\n tests/test_duckdb_view_sha.py | 12++\n",
            residual="BI leftover still queries eval_latest without recreate.",
        ),
        _bad(
            slug="clickhouse-replacing-m56t",
            domain="ch-eval",
            kind="warehouse",
            avoided="r266 prom last-write; r314 tekton last-write; r319 Aim hash",
            goal=(
                "ClickHouse leftover ReplacingMergeTree on eval_scores last-write-wins so "
                "planted hold-void is replaced by a later gold 0.94. Use AggregatingMergeTree "
                "min(score)."
            ),
            plan="Dump engine, switch to min, prove planted hold-void locally.",
            outcome=(
                "Local table uses min(score). Planted hold-void visible locally. Handoff: the "
                "cluster leftover still ReplacingMergeTree."
            ),
            ticket=(
                "Title: ClickHouse leftover ReplacingMergeTree. planted hold-void replaced."
            ),
            src="evals/ch_eval.sql",
            src_obs="ENGINE = ReplacingMergeTree()  -- leftover last-write",
            run="evals/ch_eval.py",
            fail_obs="replacing leftover gold 0.94 hides planted hold-void",
            inspect="evals/ch_eval.sql",
            inspect_obs="ReplacingMergeTree leftover. no min",
            first_path="evals/ch_eval.sql",
            first_old="ENGINE = ReplacingMergeTree()",
            first_new="ENGINE = ReplacingMergeTree(score)",
            first_obs="version col leftover still last-write on cluster",
            rate_tail="cluster leftover ReplacingMergeTree",
            still_after_429="cluster leftover replacing; planted hold-void hidden",
            grep="ReplacingMergeTree|AggregatingMergeTree|min\\(score\\)",
            grep_obs="cannot migrate cluster engine from this ticket",
            plan_change="local min query; document cluster leftover replacing",
            fix_path="evals/ch_eval.sql",
            fix_old="SELECT score FROM eval_scores FINAL",
            fix_new="SELECT min(score) FROM eval_scores",
            fix_obs="local planted visible. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover replacing. Partial",
            test="tests/test_ch_min_score.py",
            test_body="xfail cluster leftover replacing; local min(score)",
            test_obs="cluster leftover replacing. Partial",
            suite_obs="local min. cluster leftover replacing. Partial.",
            gate_obs="local min. cluster leftover replacing. Partial.",
            diff_obs=" evals/ch_eval.sql | 4+-\n HANDOFF ch engine\n",
            residual="Cluster leftover still ReplacingMergeTree last-write. Partial.",
        ),
    )
)

# r341 warehouse leftover 2
PAIRS.append(
    (
        _ok(
            slug="snowflake-stream-offset-n57u",
            domain="snowflake-eval",
            kind="warehouse",
            avoided="r313 sqlite wal; r340 duckdb view; r319 ClearML uri",
            goal=(
                "Snowflake leftover STREAM eval_scores_stream offset is yesterday so planted "
                "flash-void rows never consume. Advance the stream and fail if planted id is "
                "not in the increment."
            ),
            plan="Dump stream offset, consume increment, prove planted flash-void fail.",
            outcome=(
                "Stream increment includes planted flash-void 0.12. Residual: a task leftover "
                "still uses SHOW STREAMS offset yesterday."
            ),
            ticket=(
                "Title: Snowflake leftover STREAM offset yesterday. planted flash-void unconsumed."
            ),
            src="evals/snowflake_eval.sql",
            src_obs="CREATE STREAM eval_scores_stream ON TABLE eval_scores; -- leftover old offset",
            run="evals/snowflake_eval.py",
            fail_obs="stream leftover offset yesterday. planted flash-void not in increment",
            inspect="evals/snowflake_eval.sql",
            inspect_obs="offset leftover. no consume this SHA",
            first_path="evals/snowflake_eval.sql",
            first_old="SELECT * FROM eval_scores_stream",
            first_new="SELECT * FROM eval_scores_stream CHANGES",
            first_obs="CHANGES leftover still old offset",
            rate_tail="task leftover SHOW STREAMS offset yesterday",
            still_after_429="offset leftover; planted flash-void unconsumed",
            grep="STREAM|offset|flash-void",
            grep_obs="recreate stream; require planted id in increment",
            plan_change="recreate stream on SHA load; fail if planted id missing",
            fix_path="evals/snowflake_eval.sql",
            fix_old="SELECT * FROM eval_scores_stream CHANGES",
            fix_new="CREATE OR REPLACE STREAM ...; SELECT * FROM eval_scores_stream",
            fix_obs="planted flash-void 0.12 in increment",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-void 0.12",
            test="tests/test_snowflake_stream_sha.py",
            test_body="assert planted id in stream increment",
            test_obs="test_snowflake_stream_not_yesterday_offset",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-void",
            diff_obs=" evals/snowflake_eval.sql | 6+-\n tests/test_snowflake_stream_sha.py | 12++\n",
            residual="Task leftover still uses SHOW STREAMS offset yesterday.",
        ),
        _bad(
            slug="bq-tableclone-stale-o58v",
            domain="bq-eval",
            kind="warehouse",
            avoided="r340 duckdb view; r323 lakefs branch; r319 Aim hash",
            goal=(
                "BigQuery leftover TABLECLONE eval_scores from yesterday so planted "
                "bundle-void is missing. Clone this SHA table locally."
            ),
            plan="Dump clone source, retarget SHA, prove planted bundle-void locally.",
            outcome=(
                "Local clone is eval_scores_<sha>. Planted bundle-void present locally. Handoff: "
                "the scheduled query leftover still clones yesterday."
            ),
            ticket=(
                "Title: BQ leftover TABLECLONE yesterday. planted bundle-void missing."
            ),
            src="evals/bq_eval.sql",
            src_obs="CREATE TABLE eval_gate CLONE eval_scores_yesterday;  -- leftover",
            run="evals/bq_eval.py",
            fail_obs="clone leftover yesterday. planted bundle-void absent",
            inspect="evals/bq_eval.sql",
            inspect_obs="yesterday leftover. no sha table",
            first_path="evals/bq_eval.sql",
            first_old="CLONE eval_scores_yesterday",
            first_new="CLONE eval_scores_today",
            first_obs="today local. scheduled leftover still yesterday",
            rate_tail="scheduled leftover CLONE yesterday",
            still_after_429="scheduled leftover clone; planted bundle-void absent",
            grep="TABLECLONE|CLONE eval_scores|yesterday",
            grep_obs="cannot change scheduled query from this ticket",
            plan_change="local clone SHA table; document scheduled leftover yesterday",
            fix_path="evals/bq_eval.sql",
            fix_old="CLONE eval_scores_today",
            fix_new="CLONE eval_scores_{{sha}}",
            fix_obs="local planted present. scheduled leftover HANDOFF",
            retry_obs="502 unused. scheduled leftover yesterday clone. Partial",
            test="tests/test_bq_clone_sha.py",
            test_body="xfail scheduled leftover yesterday; local SHA clone",
            test_obs="scheduled leftover yesterday clone. Partial",
            suite_obs="local SHA clone. scheduled leftover yesterday. Partial.",
            gate_obs="local SHA clone. scheduled leftover yesterday. Partial.",
            diff_obs=" evals/bq_eval.sql | 2+-\n HANDOFF bq clone\n",
            residual="Scheduled query leftover still clones yesterday. Partial.",
        ),
    )
)

# r342 workflow leftover
PAIRS.append(
    (
        _ok(
            slug="temporal-signal-last-p59w",
            domain="temporal-eval",
            kind="workflow",
            avoided="r314 argo output overwrite; r269 prefect retry; r319 ClearML uri",
            goal=(
                "Temporal leftover EvalWorkflow signal EvalScore last-write so planted "
                "loyalty-void is overwritten by a later gold. Append signals; min() gate."
            ),
            plan="Dump signals, append, min gate, prove planted loyalty-void fail.",
            outcome=(
                "Signals appended. Gate uses min. Planted loyalty-void 0.17 fail-closed. "
                "Residual: a UI leftover still shows the last signal only."
            ),
            ticket=(
                "Title: Temporal leftover signal EvalScore last-write. planted loyalty-void hidden."
            ),
            src="evals/temporal_eval.py",
            src_obs="self.score = signal.score  # leftover last signal wins",
            run="evals/temporal_eval.py",
            fail_obs="last signal leftover 0.94. planted loyalty-void 0.17 overwritten",
            inspect="evals/temporal_eval.py",
            inspect_obs="single field leftover. no list",
            first_path="evals/temporal_eval.py",
            first_old="self.score = signal.score",
            first_new="self.score = min(self.score, signal.score)",
            first_obs="min local. UI leftover still last signal",
            rate_tail="UI leftover last signal chart",
            still_after_429="UI leftover last; planted loyalty-void hidden in UI",
            grep="EvalScore|signal|min\\(",
            grep_obs="append all scores; gate min; UI is residual",
            plan_change="append signals; gate min; do not last-write",
            fix_path="evals/temporal_eval.py",
            fix_old="self.score = min(self.score, signal.score)",
            fix_new="self.scores.append(signal.score); self.score = min(self.scores)",
            fix_obs="planted loyalty-void 0.17 in list. min gate fail",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-void 0.17",
            test="tests/test_temporal_signal_min.py",
            test_body="assert gate uses min of signals; last-write unused",
            test_obs="test_temporal_score_not_last_signal",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void",
            diff_obs=" evals/temporal_eval.py | 6+-\n tests/test_temporal_signal_min.py | 12++\n",
            residual="UI leftover still shows the last signal only.",
        ),
        _bad(
            slug="cadence-decision-cache-q60x",
            domain="cadence-eval",
            kind="workflow",
            avoided="r325 flyte cache; r269 prefect retry; r319 Aim hash",
            goal=(
                "Cadence leftover decision cache keys workflowType only so planted "
                "cancel-void replay HIT skip. Include workflowId+sha in the cache key."
            ),
            plan="Dump decision cache, add workflowId, prove planted cancel-void locally.",
            outcome=(
                "Local cache key includes workflowId+sha. Planted cancel-void runs locally. "
                "Handoff: the cluster leftover still keys workflowType only."
            ),
            ticket=(
                "Title: Cadence leftover decision cache workflowType. planted cancel-void HIT."
            ),
            src="evals/cadence_eval.py",
            src_obs="cache_key = workflow_type  # leftover",
            run="evals/cadence_eval.py",
            fail_obs="cache HIT leftover type only. planted cancel-void unused",
            inspect="evals/cadence_eval.py",
            inspect_obs="type leftover. no workflowId",
            first_path="evals/cadence_eval.py",
            first_old="cache_key = workflow_type",
            first_new="cache_key = workflow_type + ':' + task_list",
            first_obs="task_list leftover still shared",
            rate_tail="cluster leftover type-only cache",
            still_after_429="cluster leftover HIT; planted cancel-void unused",
            grep="workflowType|decision cache|workflowId",
            grep_obs="cannot flush cluster cache from this ticket",
            plan_change="local disable cache; document cluster leftover type key",
            fix_path="evals/cadence_eval.py",
            fix_old="cache_key = workflow_type + ':' + task_list",
            fix_new="cache_key = None  # do not cache eval decisions",
            fix_obs="local planted runs. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover type cache. Partial",
            test="tests/test_cadence_decision_cache.py",
            test_body="xfail cluster leftover type key; local cache off",
            test_obs="cluster leftover type cache. Partial",
            suite_obs="local cache off. cluster leftover type key. Partial.",
            gate_obs="local cache off. cluster leftover type key. Partial.",
            diff_obs=" evals/cadence_eval.py | 4+-\n HANDOFF cadence cache\n",
            residual="Cluster leftover still keys decision cache on workflowType. Partial.",
        ),
    )
)

# r343 infra leftover
PAIRS.append(
    (
        _ok(
            slug="nomad-artifact-stale-r61y",
            domain="nomad-eval",
            kind="infra",
            avoided="r268 docker layer; r305 nix gcroot; r319 ClearML uri",
            goal=(
                "Nomad leftover artifact stanza source=eval/latest so planted "
                "membership-void goldens never download. Pin artifact to this SHA."
            ),
            plan="Dump artifact source, pin SHA, prove planted membership-void fail.",
            outcome=(
                "Artifact source is eval/<sha>. Planted membership-void 0.14 fail-closed. "
                "Residual: a job leftover still interpolates eval/latest."
            ),
            ticket=(
                "Title: Nomad leftover artifact eval/latest. planted membership-void missing."
            ),
            src="evals/eval.nomad",
            src_obs='artifact { source = "eval/latest" }  # leftover',
            run="evals/nomad_eval.py",
            fail_obs="latest leftover yesterday goldens. planted membership-void absent",
            inspect="evals/eval.nomad",
            inspect_obs="latest leftover. no sha",
            first_path="evals/eval.nomad",
            first_old='source = "eval/latest"',
            first_new='source = "eval/latest-${NOMAD_META_SHA}"',
            first_obs="meta local. job leftover still eval/latest",
            rate_tail="job leftover artifact eval/latest",
            still_after_429="job leftover latest; planted membership-void absent",
            grep="eval/latest|artifact|NOMAD_META_SHA",
            grep_obs="force source eval/<sha>; ignore job latest",
            plan_change="artifact eval/<sha>; refuse latest",
            fix_path="evals/eval.nomad",
            fix_old='source = "eval/latest-${NOMAD_META_SHA}"',
            fix_new='source = "eval/${NOMAD_META_SHA}"',
            fix_obs="planted membership-void 0.14 downloaded",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-void 0.14",
            test="tests/test_nomad_artifact_sha.py",
            test_body="assert artifact source includes sha; latest unused",
            test_obs="test_nomad_artifact_not_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-void",
            diff_obs=" evals/eval.nomad | 4+-\n tests/test_nomad_artifact_sha.py | 12++\n",
            residual="Job leftover still interpolates eval/latest.",
        ),
        _bad(
            slug="consul-kv-threshold-s62z",
            domain="consul-eval",
            kind="infra",
            avoided="r288 dotenv empty; r336 hydra defaults; r319 Aim hash",
            goal=(
                "Consul leftover KV eval/threshold=0 so planted restock-hold never fails. "
                "Read threshold from the repo lock; fail if KV is 0."
            ),
            plan="Dump KV, pin lock, prove planted restock-hold locally.",
            outcome=(
                "Local threshold from lock 0.7. Planted restock-hold fails locally. Handoff: "
                "the cluster leftover still serves eval/threshold=0."
            ),
            ticket=(
                "Title: Consul leftover KV eval/threshold=0. planted restock-hold green."
            ),
            src="evals/consul_eval.py",
            src_obs="threshold = consul.kv.get('eval/threshold')  # leftover 0",
            run="evals/consul_eval.py",
            fail_obs="KV leftover 0. planted restock-hold pass",
            inspect="evals/consul_eval.py",
            inspect_obs="KV leftover. no lock",
            first_path="evals/consul_eval.py",
            first_old="consul.kv.get('eval/threshold')",
            first_new="consul.kv.get('eval/threshold') or 0.7",
            first_obs="or-0.7 leftover. KV still 0 from cluster",
            rate_tail="cluster leftover KV eval/threshold=0",
            still_after_429="cluster leftover 0; planted restock-hold pass",
            grep="eval/threshold|consul.kv|lock",
            grep_obs="cannot change cluster KV from this ticket",
            plan_change="local lock threshold; document cluster leftover 0",
            fix_path="evals/consul_eval.py",
            fix_old="consul.kv.get('eval/threshold') or 0.7",
            fix_new="threshold = lockfile_threshold('eval.lock')",
            fix_obs="local planted fail. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover KV 0. Partial",
            test="tests/test_consul_threshold_lock.py",
            test_body="xfail cluster leftover KV 0; local lock 0.7",
            test_obs="cluster leftover KV 0. Partial",
            suite_obs="local lock 0.7. cluster leftover 0. Partial.",
            gate_obs="local lock 0.7. cluster leftover 0. Partial.",
            diff_obs=" evals/consul_eval.py | 4+-\n HANDOFF consul KV\n",
            residual="Cluster leftover still serves eval/threshold=0. Partial.",
        ),
    )
)

# r344 image leftover
PAIRS.append(
    (
        _ok(
            slug="packer-eval-image-t63a",
            domain="packer-eval",
            kind="image",
            avoided="r268 docker layer; r305 nix gcroot; r319 ClearML uri",
            goal=(
                "Packer leftover image eval-ami-latest still has yesterday goldens so planted "
                "chargeback-hold never boots. Pin the AMI id to this SHA."
            ),
            plan="Dump AMI id, pin SHA, prove planted chargeback-hold fail.",
            outcome=(
                "AMI id is locked to this SHA. Planted chargeback-hold 0.13 fail-closed. "
                "Residual: an ASG leftover still launches eval-ami-latest."
            ),
            ticket=(
                "Title: Packer leftover eval-ami-latest. planted chargeback-hold missing on boot."
            ),
            src="evals/eval.pkr.hcl",
            src_obs='ami_name = "eval-ami-latest"  # leftover',
            run="evals/packer_eval.py",
            fail_obs="ami leftover yesterday goldens. planted chargeback-hold absent",
            inspect="evals/eval.pkr.hcl",
            inspect_obs="latest leftover. no sha in ami_name",
            first_path="evals/eval.pkr.hcl",
            first_old='ami_name = "eval-ami-latest"',
            first_new='ami_name = "eval-ami-${var.git_sha}"',
            first_obs="sha local. ASG leftover still latest",
            rate_tail="ASG leftover launch eval-ami-latest",
            still_after_429="ASG leftover latest; planted chargeback-hold absent",
            grep="eval-ami-latest|ami_name|git_sha",
            grep_obs="force AMI lock; ignore ASG latest",
            plan_change="ami_name eval-ami-<sha>; refuse latest",
            fix_path="evals/eval.pkr.hcl",
            fix_old='ami_name = "eval-ami-${var.git_sha}"',
            fix_new='ami_name = "eval-ami-${var.git_sha}"\n  skip_create_ami = false',
            fix_obs="planted chargeback-hold 0.13 on SHA AMI",
            retry_obs="502 then retry; 5 pass 1 fail planted chargeback-hold 0.13",
            test="tests/test_packer_ami_sha.py",
            test_body="assert ami_name includes sha; latest unused",
            test_obs="test_packer_ami_not_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed chargeback-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed chargeback-hold",
            diff_obs=" evals/eval.pkr.hcl | 4+-\n tests/test_packer_ami_sha.py | 12++\n",
            residual="ASG leftover still launches eval-ami-latest.",
        ),
        _bad(
            slug="vagrant-synced-goldens-u64b",
            domain="vagrant-eval",
            kind="image",
            avoided="r268 docker layer; r305 nix gcroot; r319 Aim hash",
            goal=(
                "Vagrant leftover synced_folder ./goldens disabled so planted tax-hold never "
                "appears in the guest. Enable the folder locally."
            ),
            plan="Dump Vagrantfile, enable sync, prove planted tax-hold locally.",
            outcome=(
                "Local synced_folder goldens on. Planted tax-hold present locally. Handoff: the "
                "box leftover still has rsync disabled."
            ),
            ticket=(
                "Title: Vagrant leftover synced_folder goldens disabled. planted tax-hold missing."
            ),
            src="Vagrantfile",
            src_obs='# config.vm.synced_folder "goldens", "/eval/goldens"  # leftover disabled',
            run="evals/vagrant_eval.py",
            fail_obs="guest leftover no goldens. planted tax-hold absent",
            inspect="Vagrantfile",
            inspect_obs="synced_folder leftover commented",
            first_path="Vagrantfile",
            first_old='# config.vm.synced_folder "goldens", "/eval/goldens"',
            first_new='config.vm.synced_folder "goldens", "/eval/goldens"',
            first_obs="local on. box leftover rsync disabled",
            rate_tail="box leftover rsync disabled",
            still_after_429="box leftover no sync; planted tax-hold absent",
            grep="synced_folder|goldens|rsync",
            grep_obs="cannot change box rsync from this ticket",
            plan_change="local enable sync; document box leftover rsync off",
            fix_path="evals/vagrant_eval.py",
            fix_old="load('/eval/goldens/tax.jsonl')",
            fix_new="load(host_goldens('tax.jsonl'))",
            fix_obs="local planted present. box leftover HANDOFF",
            retry_obs="502 unused. box leftover rsync off. Partial",
            test="tests/test_vagrant_goldens_sync.py",
            test_body="xfail box leftover rsync off; local sync on",
            test_obs="box leftover rsync off. Partial",
            suite_obs="local sync on. box leftover rsync off. Partial.",
            gate_obs="local sync on. box leftover rsync off. Partial.",
            diff_obs=" Vagrantfile | 2+-\n HANDOFF vagrant rsync\n",
            residual="Box leftover still has rsync disabled. Partial.",
        ),
    )
)

# r345 process leftover
PAIRS.append(
    (
        _ok(
            slug="supervisord-eval-stale-v65c",
            domain="supervisord-eval",
            kind="proc",
            avoided="r335 cron opt script; r271 makefile stale; r319 ClearML uri",
            goal=(
                "supervisord leftover program eval still execs /opt/eval/legacy so planted "
                "gift-void never runs. Point command at this SHA's evals/*.py."
            ),
            plan="Dump supervisord conf, retarget, prove planted gift-void fail.",
            outcome=(
                "program eval runs evals/*.py. Planted gift-void 0.15 fail-closed. Residual: "
                "a second program leftover eval-old still runs legacy."
            ),
            ticket=(
                "Title: supervisord leftover command /opt/eval/legacy. planted gift-void unused."
            ),
            src="evals/supervisord.conf",
            src_obs="command=/opt/eval/legacy  # leftover",
            run="evals/gift_void.py",
            fail_obs="legacy leftover. planted gift-void unused",
            inspect="evals/supervisord.conf",
            inspect_obs="command leftover legacy. no glob",
            first_path="evals/supervisord.conf",
            first_old="command=/opt/eval/legacy",
            first_new="command=/opt/eval/gift_void.py",
            first_obs="gift local. leftover program eval-old still legacy",
            rate_tail="eval-old leftover still legacy",
            still_after_429="eval-old leftover; planted gift-void unused",
            grep="eval-old|legacy|command=",
            grep_obs="remove eval-old; glob evals/*.py",
            plan_change="command evals/*.py; disable leftover eval-old",
            fix_path="evals/supervisord.conf",
            fix_old="command=/opt/eval/gift_void.py",
            fix_new="command=pytest evals/*.py",
            fix_obs="planted gift-void 0.15. eval-old disabled",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-void 0.15",
            test="tests/test_supervisord_not_legacy.py",
            test_body="assert command globs evals/*.py; eval-old unused",
            test_obs="test_supervisord_not_legacy_command",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-void",
            diff_obs=" evals/supervisord.conf | 4+-\n tests/test_supervisord_not_legacy.py | 12++\n",
            residual="Second program leftover eval-old still runs legacy.",
        ),
        _bad(
            slug="circus-watcher-stale-w66d",
            domain="circus-eval",
            kind="proc",
            avoided="r335 cron; r271 makefile; r319 Aim hash",
            goal=(
                "Circus leftover watcher eval still cmd=evals/legacy.py so planted "
                "promo-void never runs. Point the watcher at evals/*.py locally."
            ),
            plan="Dump circus.ini, retarget, prove planted promo-void locally.",
            outcome=(
                "Local watcher cmd evals/*.py. Planted promo-void runs locally. Handoff: the "
                "host leftover still ships circus.ini cmd=legacy."
            ),
            ticket=(
                "Title: Circus leftover watcher cmd evals/legacy.py. planted promo-void unused."
            ),
            src="evals/circus.ini",
            src_obs="cmd = evals/legacy.py  # leftover",
            run="evals/promo_void.py",
            fail_obs="legacy leftover. planted promo-void unused",
            inspect="evals/circus.ini",
            inspect_obs="cmd leftover legacy",
            first_path="evals/circus.ini",
            first_old="cmd = evals/legacy.py",
            first_new="cmd = evals/promo_void.py",
            first_obs="promo local. host leftover still legacy",
            rate_tail="host leftover circus.ini legacy",
            still_after_429="host leftover legacy; planted promo-void unused",
            grep="circus.ini|legacy.py|watcher",
            grep_obs="cannot change host circus.ini from this ticket",
            plan_change="local cmd glob; document host leftover legacy",
            fix_path="evals/circus.ini",
            fix_old="cmd = evals/promo_void.py",
            fix_new="cmd = pytest evals/*.py",
            fix_obs="local planted runs. host leftover HANDOFF",
            retry_obs="502 unused. host leftover circus legacy. Partial",
            test="tests/test_circus_not_legacy.py",
            test_body="xfail host leftover legacy; local glob",
            test_obs="host leftover circus legacy. Partial",
            suite_obs="local glob. host leftover legacy. Partial.",
            gate_obs="local glob. host leftover legacy. Partial.",
            diff_obs=" evals/circus.ini | 2+-\n HANDOFF circus host\n",
            residual="Host leftover still ships circus.ini cmd=legacy. Partial.",
        ),
    )
)

# r346 procfile leftover
PAIRS.append(
    (
        _ok(
            slug="honcho-procfile-legacy-x67e",
            domain="honcho-eval",
            kind="proc",
            avoided="r335 cron; r345 supervisord; r319 ClearML uri",
            goal=(
                "Honcho leftover Procfile eval line still calls evals/legacy.py so planted "
                "after-void never starts. Point the process at evals/*.py."
            ),
            plan="Dump Procfile, retarget, prove planted after-void fail.",
            outcome=(
                "Procfile eval runs evals/*.py. Planted after-void 0.12 fail-closed. Residual: "
                "a Heroku leftover still uses the old Procfile slug."
            ),
            ticket=(
                "Title: Honcho leftover Procfile eval: evals/legacy.py. planted after-void unused."
            ),
            src="Procfile",
            src_obs="eval: python evals/legacy.py  # leftover",
            run="evals/after_void.py",
            fail_obs="legacy leftover. planted after-void unused",
            inspect="Procfile",
            inspect_obs="eval leftover legacy.py",
            first_path="Procfile",
            first_old="eval: python evals/legacy.py",
            first_new="eval: python evals/after_void.py",
            first_obs="after local. slug leftover still old Procfile",
            rate_tail="slug leftover old Procfile",
            still_after_429="slug leftover; planted after-void unused",
            grep="Procfile|legacy.py|eval:",
            grep_obs="force evals/*.py; ignore slug leftover",
            plan_change="Procfile eval pytest evals/*.py; refuse legacy",
            fix_path="Procfile",
            fix_old="eval: python evals/after_void.py",
            fix_new="eval: pytest evals/*.py",
            fix_obs="planted after-void 0.12. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted after-void 0.12",
            test="tests/test_honcho_procfile_glob.py",
            test_body="assert Procfile eval globs evals/*.py",
            test_obs="test_honcho_not_legacy_procfile",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-void",
            diff_obs=" Procfile | 2+-\n tests/test_honcho_procfile_glob.py | 12++\n",
            residual="Heroku leftover still uses the old Procfile slug.",
        ),
        _bad(
            slug="foreman-env-zero-y68f",
            domain="foreman-eval",
            kind="proc",
            avoided="r288 dotenv empty; r335 systemd envfile; r319 Aim hash",
            goal=(
                "Foreman leftover .env EVAL_THRESHOLD=0 so planted pickup-hold never fails. "
                "Drop the leftover .env locally."
            ),
            plan="Dump .env, pin 0.7, prove planted pickup-hold locally.",
            outcome=(
                "Local .env THRESHOLD=0.7. Planted pickup-hold fails locally. Handoff: the "
                "export leftover still sources .env.yesterday."
            ),
            ticket=(
                "Title: Foreman leftover .env EVAL_THRESHOLD=0. planted pickup-hold green."
            ),
            src=".env",
            src_obs="EVAL_THRESHOLD=0  # leftover",
            run="evals/pickup_hold.py",
            fail_obs="THRESHOLD leftover 0. planted pickup-hold pass",
            inspect=".env",
            inspect_obs="EVAL_THRESHOLD=0 leftover",
            first_path=".env",
            first_old="EVAL_THRESHOLD=0",
            first_new="EVAL_THRESHOLD=0.7",
            first_obs="local 0.7. export leftover .env.yesterday still 0",
            rate_tail="export leftover .env.yesterday 0",
            still_after_429="yesterday leftover 0; planted pickup-hold pass",
            grep="EVAL_THRESHOLD|.env.yesterday|foreman",
            grep_obs="cannot change export leftover from this ticket",
            plan_change="local 0.7; document export leftover yesterday env",
            fix_path="evals/pickup_hold.py",
            fix_old="threshold = float(os.getenv('EVAL_THRESHOLD','0'))",
            fix_new="threshold = 0.7",
            fix_obs="local planted fail. export leftover HANDOFF",
            retry_obs="502 unused. export leftover yesterday env. Partial",
            test="tests/test_foreman_env_not_zero.py",
            test_body="xfail export leftover yesterday 0; local 0.7",
            test_obs="export leftover yesterday env. Partial",
            suite_obs="local 0.7. export leftover 0. Partial.",
            gate_obs="local 0.7. export leftover 0. Partial.",
            diff_obs=" .env | 2+-\n HANDOFF foreman env\n",
            residual="Export leftover still sources .env.yesterday. Partial.",
        ),
    )
)

# r347 secret-manager leftover
PAIRS.append(
    (
        _ok(
            slug="dotenvx-decrypt-stale-z69g",
            domain="dotenvx-eval",
            kind="secret",
            avoided="r337 sops yesterday; r288 dotenv empty; r319 ClearML uri",
            goal=(
                "dotenvx leftover decrypts .env.ci from last week so planted dual-hold-void "
                "uses THRESHOLD=0. Decrypt .env.ci at this SHA."
            ),
            plan="Dump dotenvx file, decrypt SHA, prove planted dual-hold-void fail.",
            outcome=(
                ".env.ci is this SHA. Planted dual-hold-void 0.16 fail-closed. Residual: a "
                "hook leftover still decrypts .env.ci.lastweek."
            ),
            ticket=(
                "Title: dotenvx leftover .env.ci last week. planted dual-hold-void vs 0."
            ),
            src=".env.ci",
            src_obs="EVAL_THRESHOLD=0  # leftover last week encrypted blob",
            run="evals/dual_hold_void.py",
            fail_obs="last week leftover THRESHOLD=0. planted dual-hold-void pass",
            inspect=".env.ci",
            inspect_obs="encrypted leftover last week",
            first_path=".env.ci",
            first_old="EVAL_THRESHOLD=0",
            first_new="EVAL_THRESHOLD=0.7",
            first_obs="local 0.7. hook leftover still lastweek file",
            rate_tail="hook leftover .env.ci.lastweek",
            still_after_429="hook leftover lastweek; planted dual-hold-void pass",
            grep="env.ci.lastweek|dotenvx|EVAL_THRESHOLD",
            grep_obs="decrypt SHA file; ignore hook lastweek",
            plan_change="decrypt .env.ci.<sha>; refuse lastweek file",
            fix_path="evals/dual_hold_void.py",
            fix_old="load_dotenv('.env.ci')",
            fix_new="load_dotenv(f'.env.ci.{git_sha}')",
            fix_obs="planted dual-hold-void 0.16. lastweek unused",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold-void 0.16",
            test="tests/test_dotenvx_sha_file.py",
            test_body="assert decrypt file includes sha; lastweek unused",
            test_obs="test_dotenvx_not_lastweek",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-void",
            diff_obs=" evals/dual_hold_void.py | 4+-\n tests/test_dotenvx_sha_file.py | 12++\n",
            residual="Hook leftover still decrypts .env.ci.lastweek.",
        ),
        _bad(
            slug="chamber-service-stale-a70h",
            domain="chamber-eval",
            kind="secret",
            avoided="r337 vault kv; r288 dotenv; r319 Aim hash",
            goal=(
                "Chamber leftover service eval-nightly still has THRESHOLD=0 so planted "
                "sla-hold never fails. Read service eval-<sha> locally."
            ),
            plan="Dump chamber service, pin sha, prove planted sla-hold locally.",
            outcome=(
                "Local chamber service eval-<sha>. Planted sla-hold fails locally. Handoff: "
                "the task leftover still chamber exec eval-nightly."
            ),
            ticket=(
                "Title: Chamber leftover service eval-nightly THRESHOLD=0. planted sla-hold green."
            ),
            src="evals/chamber_eval.sh",
            src_obs="chamber exec eval-nightly -- pytest evals/  # leftover",
            run="evals/sla_hold.py",
            fail_obs="nightly leftover THRESHOLD=0. planted sla-hold pass",
            inspect="evals/chamber_eval.sh",
            inspect_obs="eval-nightly leftover. no sha service",
            first_path="evals/chamber_eval.sh",
            first_old="chamber exec eval-nightly",
            first_new="chamber exec eval-dev",
            first_obs="dev local. task leftover still eval-nightly",
            rate_tail="task leftover chamber exec eval-nightly",
            still_after_429="task leftover nightly; planted sla-hold pass",
            grep="eval-nightly|chamber exec|THRESHOLD",
            grep_obs="cannot change task leftover from this ticket",
            plan_change="local eval-<sha> service; document task leftover nightly",
            fix_path="evals/chamber_eval.sh",
            fix_old="chamber exec eval-dev",
            fix_new="chamber exec eval-$GIT_SHA",
            fix_obs="local planted fail. task leftover HANDOFF",
            retry_obs="502 unused. task leftover eval-nightly. Partial",
            test="tests/test_chamber_service_sha.py",
            test_body="xfail task leftover nightly; local eval-<sha>",
            test_obs="task leftover eval-nightly. Partial",
            suite_obs="local eval-sha. task leftover nightly. Partial.",
            gate_obs="local eval-sha. task leftover nightly. Partial.",
            diff_obs=" evals/chamber_eval.sh | 2+-\n HANDOFF chamber nightly\n",
            residual="Task leftover still chamber exec eval-nightly. Partial.",
        ),
    )
)

# r348 cloud-config leftover
PAIRS.append(
    (
        _ok(
            slug="ssm-param-threshold-b71i",
            domain="ssm-eval",
            kind="cloudcfg",
            avoided="r343 consul kv; r288 dotenv; r319 ClearML uri",
            goal=(
                "SSM leftover /eval/threshold=0 so planted warranty-hold never fails. Read "
                "the parameter version that matches the lock."
            ),
            plan="Dump SSM version, pin lock, prove planted warranty-hold fail.",
            outcome=(
                "Parameter version matches lock. Planted warranty-hold 0.14 fail-closed. "
                "Residual: a lambda leftover still GetParameter without version."
            ),
            ticket=(
                "Title: SSM leftover /eval/threshold unversioned 0. planted warranty-hold green."
            ),
            src="evals/ssm_eval.py",
            src_obs="ssm.get_parameter(Name='/eval/threshold')  # leftover no version",
            run="evals/ssm_eval.py",
            fail_obs="unversioned leftover 0. planted warranty-hold pass",
            inspect="evals/ssm_eval.py",
            inspect_obs="no version leftover",
            first_path="evals/ssm_eval.py",
            first_old="Name='/eval/threshold'",
            first_new="Name='/eval/threshold', Version=2",
            first_obs="v2 local. lambda leftover still unversioned",
            rate_tail="lambda leftover GetParameter no version",
            still_after_429="lambda leftover 0; planted warranty-hold pass",
            grep="/eval/threshold|Version|GetParameter",
            grep_obs="read lock version; ignore lambda leftover",
            plan_change="lockfile version; refuse unversioned GetParameter",
            fix_path="evals/ssm_eval.py",
            fix_old="Name='/eval/threshold', Version=2",
            fix_new="Name='/eval/threshold', Version=lock_version()",
            fix_obs="planted warranty-hold 0.14. unversioned unused",
            retry_obs="502 then retry; 5 pass 1 fail planted warranty-hold 0.14",
            test="tests/test_ssm_threshold_version.py",
            test_body="assert GetParameter uses lock version",
            test_obs="test_ssm_not_unversioned_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed warranty-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed warranty-hold",
            diff_obs=" evals/ssm_eval.py | 6+-\n tests/test_ssm_threshold_version.py | 12++\n",
            residual="Lambda leftover still GetParameter without version.",
        ),
        _bad(
            slug="appconfig-profile-stale-c72j",
            domain="appconfig-eval",
            kind="cloudcfg",
            avoided="r336 hydra defaults; r343 consul kv; r319 Aim hash",
            goal=(
                "AppConfig leftover profile eval-prod still has threshold 0 so planted "
                "restock-hold-2 never fails. Pin the profile to eval-<sha> locally."
            ),
            plan="Dump profile, pin sha, prove planted restock-hold-2 locally.",
            outcome=(
                "Local profile eval-<sha>. Planted restock-hold-2 fails locally. Handoff: the "
                "app leftover still starts with eval-prod."
            ),
            ticket=(
                "Title: AppConfig leftover profile eval-prod threshold 0. planted restock-hold-2 green."
            ),
            src="evals/appconfig_eval.py",
            src_obs="profile='eval-prod'  # leftover",
            run="evals/appconfig_eval.py",
            fail_obs="prod leftover threshold 0. planted restock-hold-2 pass",
            inspect="evals/appconfig_eval.py",
            inspect_obs="eval-prod leftover. no sha profile",
            first_path="evals/appconfig_eval.py",
            first_old="profile='eval-prod'",
            first_new="profile=os.getenv('EVAL_PROFILE','eval-prod')",
            first_obs="env leftover EVAL_PROFILE=eval-prod",
            rate_tail="app leftover starts eval-prod",
            still_after_429="app leftover prod; planted restock-hold-2 pass",
            grep="eval-prod|EVAL_PROFILE|threshold",
            grep_obs="cannot change app start profile from this ticket",
            plan_change="local eval-<sha> profile; document app leftover prod",
            fix_path="evals/appconfig_eval.py",
            fix_old="profile=os.getenv('EVAL_PROFILE','eval-prod')",
            fix_new="profile=f'eval-{git_sha}'",
            fix_obs="local planted fail. app leftover HANDOFF",
            retry_obs="502 unused. app leftover eval-prod. Partial",
            test="tests/test_appconfig_profile_sha.py",
            test_body="xfail app leftover eval-prod; local eval-<sha>",
            test_obs="app leftover eval-prod. Partial",
            suite_obs="local eval-sha. app leftover prod. Partial.",
            gate_obs="local eval-sha. app leftover prod. Partial.",
            diff_obs=" evals/appconfig_eval.py | 4+-\n HANDOFF appconfig prod\n",
            residual="App leftover still starts with eval-prod. Partial.",
        ),
    )
)

# r349 secret-saas leftover
PAIRS.append(
    (
        _ok(
            slug="doppler-config-stale-d73k",
            domain="doppler-eval",
            kind="secret",
            avoided="r347 chamber nightly; r337 vault kv; r319 ClearML uri",
            goal=(
                "Doppler leftover config prd still has EVAL_THRESHOLD=0 so planted "
                "flash-hold-2 never fails. Pin config to prd_<sha>."
            ),
            plan="Dump doppler config, pin sha, prove planted flash-hold-2 fail.",
            outcome=(
                "Config is prd_<sha>. Planted flash-hold-2 0.13 fail-closed. Residual: a "
                "CLI leftover still doppler run -c prd."
            ),
            ticket=(
                "Title: Doppler leftover config prd THRESHOLD=0. planted flash-hold-2 green."
            ),
            src="evals/doppler.yaml",
            src_obs="config: prd  # leftover",
            run="evals/flash_hold2.py",
            fail_obs="prd leftover THRESHOLD=0. planted flash-hold-2 pass",
            inspect="evals/doppler.yaml",
            inspect_obs="prd leftover. no sha config",
            first_path="evals/doppler.yaml",
            first_old="config: prd",
            first_new="config: prd_dev",
            first_obs="prd_dev local. CLI leftover still -c prd",
            rate_tail="CLI leftover doppler run -c prd",
            still_after_429="CLI leftover prd; planted flash-hold-2 pass",
            grep="config: prd|doppler run|EVAL_THRESHOLD",
            grep_obs="force -c prd_<sha>; ignore CLI leftover",
            plan_change="config prd_<sha>; refuse bare prd",
            fix_path="evals/doppler.yaml",
            fix_old="config: prd_dev",
            fix_new="config: prd_{{sha}}",
            fix_obs="planted flash-hold-2 0.13. prd unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-2 0.13",
            test="tests/test_doppler_config_sha.py",
            test_body="assert config is prd_<sha>; bare prd unused",
            test_obs="test_doppler_not_bare_prd",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-2",
            diff_obs=" evals/doppler.yaml | 2+-\n tests/test_doppler_config_sha.py | 12++\n",
            residual="CLI leftover still doppler run -c prd.",
        ),
        _bad(
            slug="infisical-env-stale-e74l",
            domain="infisical-eval",
            kind="secret",
            avoided="r347 dotenvx; r337 sops; r319 Aim hash",
            goal=(
                "Infisical leftover env prod still has THRESHOLD=0 so planted "
                "bundle-hold-2 never fails. Pin env to prod/<sha> locally."
            ),
            plan="Dump infisical env, pin sha, prove planted bundle-hold-2 locally.",
            outcome=(
                "Local env prod/<sha>. Planted bundle-hold-2 fails locally. Handoff: the "
                "action leftover still --env=prod."
            ),
            ticket=(
                "Title: Infisical leftover --env=prod THRESHOLD=0. planted bundle-hold-2 green."
            ),
            src="evals/infisical.sh",
            src_obs="infisical run --env=prod -- pytest evals/  # leftover",
            run="evals/bundle_hold2.py",
            fail_obs="prod leftover THRESHOLD=0. planted bundle-hold-2 pass",
            inspect="evals/infisical.sh",
            inspect_obs="--env=prod leftover. no sha",
            first_path="evals/infisical.sh",
            first_old="--env=prod",
            first_new="--env=prod-dev",
            first_obs="prod-dev local. action leftover still --env=prod",
            rate_tail="action leftover --env=prod",
            still_after_429="action leftover prod; planted bundle-hold-2 pass",
            grep="--env=prod|infisical run|THRESHOLD",
            grep_obs="cannot change action leftover from this ticket",
            plan_change="local --env=prod/<sha>; document action leftover prod",
            fix_path="evals/infisical.sh",
            fix_old="--env=prod-dev",
            fix_new="--env=prod/$GIT_SHA",
            fix_obs="local planted fail. action leftover HANDOFF",
            retry_obs="502 unused. action leftover --env=prod. Partial",
            test="tests/test_infisical_env_sha.py",
            test_body="xfail action leftover prod; local prod/<sha>",
            test_obs="action leftover --env=prod. Partial",
            suite_obs="local prod/sha. action leftover prod. Partial.",
            gate_obs="local prod/sha. action leftover prod. Partial.",
            diff_obs=" evals/infisical.sh | 2+-\n HANDOFF infisical prod\n",
            residual="Action leftover still --env=prod. Partial.",
        ),
    )
)

# r350 proxy leftover
PAIRS.append(
    (
        _ok(
            slug="caddy-cache-judge-f75m",
            domain="caddy-eval",
            kind="proxy",
            avoided="r315 helicone 2k; r315 portkey simple; r319 ClearML uri",
            goal=(
                "Caddy leftover cache on /v1/chat/completions serves yesterday 1.0 so planted "
                "loyalty-hold-2 never reaches the judge. Bypass cache on the judge path."
            ),
            plan="Dump Caddyfile, bypass judge cache, prove planted loyalty-hold-2 fail.",
            outcome=(
                "Judge path Cache-Control no-store. Planted loyalty-hold-2 0.15 fail-closed. "
                "Residual: an edge leftover still caches POST /v1/chat/completions."
            ),
            ticket=(
                "Title: Caddy leftover cache POST /v1/chat/completions. planted loyalty-hold-2 HIT 1.0."
            ),
            src="Caddyfile",
            src_obs="cache {\n  path /v1/chat/completions  # leftover",
            run="evals/caddy_eval.py",
            fail_obs="cache leftover HIT 1.0. planted loyalty-hold-2 unused",
            inspect="Caddyfile",
            inspect_obs="path leftover caches judge POST",
            first_path="Caddyfile",
            first_old="path /v1/chat/completions",
            first_new="path /v1/chat/completions\n    # skip judge later",
            first_obs="comment only. edge leftover still caches POST",
            rate_tail="edge leftover cache POST judge",
            still_after_429="edge leftover HIT; planted loyalty-hold-2 1.0",
            grep="chat/completions|cache \\{|no-store",
            grep_obs="bypass judge path; ignore edge leftover",
            plan_change="no-store on judge path; refuse POST cache",
            fix_path="Caddyfile",
            fix_old="path /v1/chat/completions\n    # skip judge later",
            fix_new="header /v1/chat/completions Cache-Control no-store",
            fix_obs="planted loyalty-hold-2 0.15 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-2 0.15",
            test="tests/test_caddy_judge_nostore.py",
            test_body="assert judge path no-store; POST cache unused",
            test_obs="test_caddy_not_cache_judge_post",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-2",
            diff_obs=" Caddyfile | 6+-\n tests/test_caddy_judge_nostore.py | 12++\n",
            residual="Edge leftover still caches POST /v1/chat/completions.",
        ),
        _bad(
            slug="nginx-proxy-cache-g76n",
            domain="nginx-eval",
            kind="proxy",
            avoided="r315 helicone; r315 portkey; r319 Aim hash",
            goal=(
                "nginx leftover proxy_cache on the judge upstream serves yesterday 1.0 so "
                "planted cancel-hold-2 never reaches the model. Disable cache locally."
            ),
            plan="Dump nginx cache, disable, prove planted cancel-hold-2 locally.",
            outcome=(
                "Local proxy_cache off for judge. Planted cancel-hold-2 fails locally. Handoff: "
                "the edge leftover still proxy_cache zone=judge."
            ),
            ticket=(
                "Title: nginx leftover proxy_cache judge. planted cancel-hold-2 HIT 1.0."
            ),
            src="evals/nginx.conf",
            src_obs="proxy_cache judge;  # leftover",
            run="evals/nginx_eval.py",
            fail_obs="proxy_cache leftover HIT 1.0. planted cancel-hold-2 unused",
            inspect="evals/nginx.conf",
            inspect_obs="zone judge leftover. no bypass",
            first_path="evals/nginx.conf",
            first_old="proxy_cache judge;",
            first_new="proxy_cache judge;  # TODO bypass",
            first_obs="comment only. edge leftover still zone=judge",
            rate_tail="edge leftover proxy_cache zone=judge",
            still_after_429="edge leftover HIT; planted cancel-hold-2 1.0",
            grep="proxy_cache|zone=judge|bypass",
            grep_obs="cannot change edge leftover from this ticket",
            plan_change="local proxy_cache off; document edge leftover zone",
            fix_path="evals/nginx.conf",
            fix_old="proxy_cache judge;  # TODO bypass",
            fix_new="proxy_cache off;",
            fix_obs="local planted fail. edge leftover HANDOFF",
            retry_obs="502 unused. edge leftover proxy_cache. Partial",
            test="tests/test_nginx_judge_cache_off.py",
            test_body="xfail edge leftover zone=judge; local cache off",
            test_obs="edge leftover proxy_cache. Partial",
            suite_obs="local cache off. edge leftover zone. Partial.",
            gate_obs="local cache off. edge leftover zone. Partial.",
            diff_obs=" evals/nginx.conf | 2+-\n HANDOFF nginx edge\n",
            residual="Edge leftover still proxy_cache zone=judge. Partial.",
        ),
    )
)

# r351 lb leftover
PAIRS.append(
    (
        _ok(
            slug="haproxy-stick-table-h77o",
            domain="haproxy-eval",
            kind="proxy",
            avoided="r350 caddy cache; r315 helicone; r319 ClearML uri",
            goal=(
                "HAProxy leftover stick-table on judge src IP serves a cached 1.0 so planted "
                "price-void-2 never reaches the model. Clear the table; bypass stick on judge."
            ),
            plan="Dump stick-table, bypass judge, prove planted price-void-2 fail.",
            outcome=(
                "Judge backend has no stick-table. Planted price-void-2 0.16 fail-closed. "
                "Residual: a peer leftover still syncs the old table."
            ),
            ticket=(
                "Title: HAProxy leftover stick-table judge. planted price-void-2 HIT 1.0."
            ),
            src="evals/haproxy.cfg",
            src_obs="stick-table type ip size 1m  # leftover on judge",
            run="evals/haproxy_eval.py",
            fail_obs="stick leftover HIT 1.0. planted price-void-2 unused",
            inspect="evals/haproxy.cfg",
            inspect_obs="stick-table leftover on judge backend",
            first_path="evals/haproxy.cfg",
            first_old="stick-table type ip size 1m",
            first_new="stick-table type ip size 1m expire 1s",
            first_obs="1s local. peer leftover still syncs old table",
            rate_tail="peer leftover stick-table sync",
            still_after_429="peer leftover HIT; planted price-void-2 1.0",
            grep="stick-table|judge|peer",
            grep_obs="remove stick on judge; ignore peer leftover",
            plan_change="no stick-table on judge; refuse peer sync for eval",
            fix_path="evals/haproxy.cfg",
            fix_old="stick-table type ip size 1m expire 1s",
            fix_new="# no stick-table on judge",
            fix_obs="planted price-void-2 0.16 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted price-void-2 0.16",
            test="tests/test_haproxy_no_stick_judge.py",
            test_body="assert no stick-table on judge backend",
            test_obs="test_haproxy_judge_not_stick",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed price-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed price-void-2",
            diff_obs=" evals/haproxy.cfg | 4+-\n tests/test_haproxy_no_stick_judge.py | 12++\n",
            residual="Peer leftover still syncs the old stick-table.",
        ),
        _bad(
            slug="envoy-cluster-cache-i78p",
            domain="envoy-eval",
            kind="proxy",
            avoided="r350 nginx cache; r315 portkey; r319 Aim hash",
            goal=(
                "Envoy leftover cluster cache on judge cluster serves yesterday 1.0 so planted "
                "hold-void-2 never reaches the model. Disable cluster cache locally."
            ),
            plan="Dump envoy cluster, disable cache, prove planted hold-void-2 locally.",
            outcome=(
                "Local cluster cache off. Planted hold-void-2 fails locally. Handoff: the mesh "
                "leftover still enables cluster cache."
            ),
            ticket=(
                "Title: Envoy leftover cluster cache judge. planted hold-void-2 HIT 1.0."
            ),
            src="evals/envoy.yaml",
            src_obs="typed_extension_protocol_options leftover cache on judge cluster",
            run="evals/envoy_eval.py",
            fail_obs="cluster cache leftover HIT 1.0. planted hold-void-2 unused",
            inspect="evals/envoy.yaml",
            inspect_obs="cache leftover enabled on judge",
            first_path="evals/envoy.yaml",
            first_old="cache: {enabled: true}",
            first_new="cache: {enabled: true}  # TODO off",
            first_obs="comment only. mesh leftover still enabled",
            rate_tail="mesh leftover cluster cache on",
            still_after_429="mesh leftover HIT; planted hold-void-2 1.0",
            grep="cluster cache|judge|enabled: true",
            grep_obs="cannot change mesh leftover from this ticket",
            plan_change="local cache off; document mesh leftover cluster cache",
            fix_path="evals/envoy.yaml",
            fix_old="cache: {enabled: true}  # TODO off",
            fix_new="cache: {enabled: false}",
            fix_obs="local planted fail. mesh leftover HANDOFF",
            retry_obs="502 unused. mesh leftover cluster cache. Partial",
            test="tests/test_envoy_cluster_cache_off.py",
            test_body="xfail mesh leftover cache; local enabled false",
            test_obs="mesh leftover cluster cache. Partial",
            suite_obs="local cache off. mesh leftover on. Partial.",
            gate_obs="local cache off. mesh leftover on. Partial.",
            diff_obs=" evals/envoy.yaml | 2+-\n HANDOFF envoy mesh\n",
            residual="Mesh leftover still enables cluster cache. Partial.",
        ),
    )
)

# r352 cache-proxy leftover
PAIRS.append(
    (
        _ok(
            slug="varnish-ttl-judge-j79q",
            domain="varnish-eval",
            kind="proxy",
            avoided="r350 caddy cache; r351 haproxy stick; r319 ClearML uri",
            goal=(
                "Varnish leftover TTL 1d on /judge so planted gift-hold-2 HIT 1.0. Set TTL 0 "
                "on the judge URL."
            ),
            plan="Dump VCL, zero TTL, prove planted gift-hold-2 fail.",
            outcome=(
                "Judge URL TTL 0. Planted gift-hold-2 0.14 fail-closed. Residual: a director "
                "leftover still sets beresp.ttl=1d."
            ),
            ticket=(
                "Title: Varnish leftover TTL 1d /judge. planted gift-hold-2 HIT 1.0."
            ),
            src="evals/default.vcl",
            src_obs="set beresp.ttl = 1d;  # leftover on /judge",
            run="evals/varnish_eval.py",
            fail_obs="TTL leftover 1d HIT 1.0. planted gift-hold-2 unused",
            inspect="evals/default.vcl",
            inspect_obs="1d leftover. no /judge exception",
            first_path="evals/default.vcl",
            first_old="set beresp.ttl = 1d;",
            first_new="set beresp.ttl = 1h;",
            first_obs="1h leftover still HIT. director leftover 1d",
            rate_tail="director leftover beresp.ttl=1d",
            still_after_429="director leftover HIT; planted gift-hold-2 1.0",
            grep="beresp.ttl|/judge|1d",
            grep_obs="ttl 0 on /judge; ignore director leftover",
            plan_change="TTL 0 on /judge; refuse 1d",
            fix_path="evals/default.vcl",
            fix_old="set beresp.ttl = 1h;",
            fix_new='if (req.url ~ "^/judge") { set beresp.ttl = 0s; }',
            fix_obs="planted gift-hold-2 0.14 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-2 0.14",
            test="tests/test_varnish_judge_ttl0.py",
            test_body="assert /judge ttl 0s; 1d unused",
            test_obs="test_varnish_judge_not_1d",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-2",
            diff_obs=" evals/default.vcl | 6+-\n tests/test_varnish_judge_ttl0.py | 12++\n",
            residual="Director leftover still sets beresp.ttl=1d.",
        ),
        _bad(
            slug="squid-refresh-judge-k80r",
            domain="squid-eval",
            kind="proxy",
            avoided="r350 nginx cache; r351 envoy cluster; r319 Aim hash",
            goal=(
                "Squid leftover refresh_pattern /judge 1440 so planted promo-hold-2 HIT 1.0. "
                "Set refresh 0 locally."
            ),
            plan="Dump squid.conf, zero refresh, prove planted promo-hold-2 locally.",
            outcome=(
                "Local refresh_pattern /judge 0. Planted promo-hold-2 fails locally. Handoff: "
                "the parent leftover still 1440."
            ),
            ticket=(
                "Title: Squid leftover refresh_pattern /judge 1440. planted promo-hold-2 HIT 1.0."
            ),
            src="evals/squid.conf",
            src_obs="refresh_pattern /judge 1440 20% 2880  # leftover",
            run="evals/squid_eval.py",
            fail_obs="1440 leftover HIT 1.0. planted promo-hold-2 unused",
            inspect="evals/squid.conf",
            inspect_obs="1440 leftover on /judge",
            first_path="evals/squid.conf",
            first_old="refresh_pattern /judge 1440 20% 2880",
            first_new="refresh_pattern /judge 60 20% 120",
            first_obs="60 local. parent leftover still 1440",
            rate_tail="parent leftover refresh 1440",
            still_after_429="parent leftover HIT; planted promo-hold-2 1.0",
            grep="refresh_pattern|/judge|1440",
            grep_obs="cannot change parent leftover from this ticket",
            plan_change="local refresh 0; document parent leftover 1440",
            fix_path="evals/squid.conf",
            fix_old="refresh_pattern /judge 60 20% 120",
            fix_new="refresh_pattern /judge 0 0% 0",
            fix_obs="local planted fail. parent leftover HANDOFF",
            retry_obs="502 unused. parent leftover 1440. Partial",
            test="tests/test_squid_judge_refresh0.py",
            test_body="xfail parent leftover 1440; local refresh 0",
            test_obs="parent leftover 1440. Partial",
            suite_obs="local refresh 0. parent leftover 1440. Partial.",
            gate_obs="local refresh 0. parent leftover 1440. Partial.",
            diff_obs=" evals/squid.conf | 2+-\n HANDOFF squid parent\n",
            residual="Parent leftover still refresh_pattern /judge 1440. Partial.",
        ),
    )
)

# r353 session leftover
PAIRS.append(
    (
        _ok(
            slug="tmux-env-threshold-l81s",
            domain="tmux-eval",
            kind="session",
            avoided="r289 direnv tox; r288 dotenv; r319 ClearML uri",
            goal=(
                "tmux leftover session env EVAL_THRESHOLD=0 from last week so planted "
                "after-hold-2 never fails. Unset the session env; source the repo env."
            ),
            plan="Dump tmux showenv, unset, prove planted after-hold-2 fail.",
            outcome=(
                "Session env unset. Planted after-hold-2 0.12 fail-closed. Residual: a "
                "resurrect leftover still restores the old env."
            ),
            ticket=(
                "Title: tmux leftover showenv EVAL_THRESHOLD=0. planted after-hold-2 green."
            ),
            src="evals/tmux_eval.sh",
            src_obs="tmux showenv EVAL_THRESHOLD  # leftover 0",
            run="evals/after_hold2.py",
            fail_obs="session leftover THRESHOLD=0. planted after-hold-2 pass",
            inspect="evals/tmux_eval.sh",
            inspect_obs="inherits leftover session env",
            first_path="evals/tmux_eval.sh",
            first_old="tmux showenv EVAL_THRESHOLD",
            first_new="tmux setenv -u EVAL_THRESHOLD",
            first_obs="unset local. resurrect leftover still restores 0",
            rate_tail="resurrect leftover restores EVAL_THRESHOLD=0",
            still_after_429="resurrect leftover 0; planted after-hold-2 pass",
            grep="showenv|EVAL_THRESHOLD|resurrect",
            grep_obs="unset; refuse resurrect env; source repo",
            plan_change="unset session env; source repo env; refuse resurrect",
            fix_path="evals/after_hold2.py",
            fix_old="threshold = float(os.getenv('EVAL_THRESHOLD','0'))",
            fix_new="threshold = 0.7",
            fix_obs="planted after-hold-2 0.12. session env unused",
            retry_obs="502 then retry; 5 pass 1 fail planted after-hold-2 0.12",
            test="tests/test_tmux_env_unset.py",
            test_body="assert threshold 0.7; session leftover unused",
            test_obs="test_tmux_not_session_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-hold-2",
            diff_obs=" evals/after_hold2.py | 4+-\n tests/test_tmux_env_unset.py | 12++\n",
            residual="Resurrect leftover still restores the old session env.",
        ),
        _bad(
            slug="screen-hardcopy-stale-m82t",
            domain="screen-eval",
            kind="session",
            avoided="r353 tmux env; r271 makefile; r319 Aim hash",
            goal=(
                "screen leftover hardcopy eval.log from yesterday is what the gate parses so "
                "planted sku-hold never appears. Parse this SHA's log locally."
            ),
            plan="Dump hardcopy path, pin SHA log, prove planted sku-hold locally.",
            outcome=(
                "Local gate parses eval-<sha>.log. Planted sku-hold present locally. Handoff: "
                "the wrapper leftover still hardcopy eval.log."
            ),
            ticket=(
                "Title: screen leftover hardcopy eval.log yesterday. planted sku-hold missing."
            ),
            src="evals/screen_eval.sh",
            src_obs="screen -X hardcopy eval.log  # leftover stable name",
            run="evals/sku_hold.py",
            fail_obs="eval.log leftover yesterday 1.0. planted sku-hold absent",
            inspect="evals/screen_eval.sh",
            inspect_obs="stable hardcopy leftover",
            first_path="evals/screen_eval.sh",
            first_old="hardcopy eval.log",
            first_new="hardcopy eval-dev.log",
            first_obs="dev local. wrapper leftover still eval.log",
            rate_tail="wrapper leftover hardcopy eval.log",
            still_after_429="wrapper leftover eval.log; planted sku-hold absent",
            grep="hardcopy|eval.log|screen -X",
            grep_obs="cannot change wrapper leftover from this ticket",
            plan_change="local hardcopy eval-<sha>.log; document wrapper leftover",
            fix_path="evals/screen_eval.sh",
            fix_old="hardcopy eval-dev.log",
            fix_new="hardcopy eval-$GIT_SHA.log",
            fix_obs="local planted present. wrapper leftover HANDOFF",
            retry_obs="502 unused. wrapper leftover eval.log. Partial",
            test="tests/test_screen_hardcopy_sha.py",
            test_body="xfail wrapper leftover eval.log; local sha log",
            test_obs="wrapper leftover eval.log. Partial",
            suite_obs="local sha log. wrapper leftover eval.log. Partial.",
            gate_obs="local sha log. wrapper leftover eval.log. Partial.",
            diff_obs=" evals/screen_eval.sh | 2+-\n HANDOFF screen hardcopy\n",
            residual="Wrapper leftover still hardcopy eval.log. Partial.",
        ),
    )
)

# r354 batch leftover
PAIRS.append(
    (
        _ok(
            slug="at-job-eval-stale-n83u",
            domain="at-eval",
            kind="sched",
            avoided="r335 cron opt; r320 justfile; r319 ClearML uri",
            goal=(
                "at leftover job /tmp/eval.sh from last deploy still runs evals/legacy.py so "
                "planted rain-hold never starts. Replace the at job with this SHA script."
            ),
            plan="Dump atq, replace job, prove planted rain-hold fail.",
            outcome=(
                "at job runs SHA script. Planted rain-hold 0.17 fail-closed. Residual: a "
                "batch leftover still queues /tmp/eval.sh."
            ),
            ticket=(
                "Title: at leftover /tmp/eval.sh last deploy. planted rain-hold unused."
            ),
            src="/tmp/eval.sh",
            src_obs="python evals/legacy.py  # leftover",
            run="evals/rain_hold.py",
            fail_obs="legacy leftover. planted rain-hold unused",
            inspect="/tmp/eval.sh",
            inspect_obs="legacy leftover last deploy",
            first_path="/tmp/eval.sh",
            first_old="python evals/legacy.py",
            first_new="python evals/rain_hold.py",
            first_obs="rain local. batch leftover still queues /tmp/eval.sh",
            rate_tail="batch leftover /tmp/eval.sh",
            still_after_429="batch leftover; planted rain-hold unused",
            grep="atq|/tmp/eval.sh|legacy.py",
            grep_obs="atrm leftover; queue SHA script",
            plan_change="atrm leftover; at SHA script; refuse /tmp/eval.sh",
            fix_path="evals/rain_hold.py",
            fix_old="pass",
            fix_new="assert not Path('/tmp/eval.sh').exists() or sha_script()",
            fix_obs="planted rain-hold 0.17. leftover job removed",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-hold 0.17",
            test="tests/test_at_job_sha_script.py",
            test_body="assert at job is SHA script; /tmp/eval.sh unused",
            test_obs="test_at_not_tmp_eval_sh",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold",
            diff_obs=" /tmp/eval.sh | 4+-\n tests/test_at_job_sha_script.py | 12++\n",
            residual="Batch leftover still queues /tmp/eval.sh.",
        ),
        _bad(
            slug="batch-queue-legacy-o84v",
            domain="batch-eval",
            kind="sched",
            avoided="r335 cron; r354 at job; r319 Aim hash",
            goal=(
                "batch leftover queue still runs /var/eval/legacy so planted dual-hold-2 never "
                "starts. Point the queue at evals/*.py locally."
            ),
            plan="Dump batch queue, retarget, prove planted dual-hold-2 locally.",
            outcome=(
                "Local queue runs evals/*.py. Planted dual-hold-2 runs locally. Handoff: the "
                "host leftover still /var/eval/legacy."
            ),
            ticket=(
                "Title: batch leftover /var/eval/legacy. planted dual-hold-2 unused."
            ),
            src="/var/eval/legacy",
            src_obs="#!/bin/sh\npython evals/legacy.py  # leftover",
            run="evals/dual_hold2.py",
            fail_obs="legacy leftover. planted dual-hold-2 unused",
            inspect="/var/eval/legacy",
            inspect_obs="legacy leftover host path",
            first_path="/var/eval/legacy",
            first_old="python evals/legacy.py",
            first_new="python evals/dual_hold2.py",
            first_obs="dual local. host leftover still queues legacy path",
            rate_tail="host leftover /var/eval/legacy",
            still_after_429="host leftover legacy; planted dual-hold-2 unused",
            grep="/var/eval/legacy|batch|atq",
            grep_obs="cannot change host queue from this ticket",
            plan_change="local repo script; document host leftover legacy",
            fix_path="evals/dual_hold2.py",
            fix_old="pass",
            fix_new="# local only; host leftover /var/eval/legacy",
            fix_obs="local planted runs. host leftover HANDOFF",
            retry_obs="502 unused. host leftover /var/eval/legacy. Partial",
            test="tests/test_batch_not_legacy.py",
            test_body="xfail host leftover legacy; local glob",
            test_obs="host leftover /var/eval/legacy. Partial",
            suite_obs="local glob. host leftover legacy. Partial.",
            gate_obs="local glob. host leftover legacy. Partial.",
            diff_obs=" evals/dual_hold2.py | 2+-\n HANDOFF batch host\n",
            residual="Host leftover still /var/eval/legacy. Partial.",
        ),
    )
)

# r355 render leftover
PAIRS.append(
    (
        _ok(
            slug="skaffold-render-omit-p85w",
            domain="skaffold-eval",
            kind="render",
            avoided="r308 bazel omit goldens; r305 pants omit; r319 ClearML uri",
            goal=(
                "Skaffold leftover render sync omits goldens/ so planted seat-hold never "
                "reaches the eval pod. Include goldens in the sync."
            ),
            plan="Dump skaffold sync, add goldens, prove planted seat-hold fail.",
            outcome=(
                "Sync includes goldens/. Planted seat-hold 0.13 fail-closed. Residual: a "
                "profile leftover still syncs evals/ only."
            ),
            ticket=(
                "Title: Skaffold leftover sync evals/**. planted seat-hold missing in pod."
            ),
            src="skaffold.yaml",
            src_obs="sync:\n  infer: [\"evals/**/*\"]  # leftover no goldens",
            run="evals/skaffold_eval.py",
            fail_obs="pod leftover no goldens. planted seat-hold absent",
            inspect="skaffold.yaml",
            inspect_obs="infer leftover evals only",
            first_path="skaffold.yaml",
            first_old='infer: ["evals/**/*"]',
            first_new='infer: ["evals/**/*", "goldens/**/*"]',
            first_obs="goldens local. profile leftover still evals only",
            rate_tail="profile leftover sync evals only",
            still_after_429="profile leftover omit; planted seat-hold absent",
            grep="goldens|sync:|infer:",
            grep_obs="include goldens; ignore profile leftover",
            plan_change="sync goldens/**; refuse evals-only infer",
            fix_path="skaffold.yaml",
            fix_old='infer: ["evals/**/*", "goldens/**/*"]',
            fix_new='manual:\n        - src: "goldens/**/*"\n          dest: /eval',
            fix_obs="planted seat-hold 0.13 in pod",
            retry_obs="502 then retry; 5 pass 1 fail planted seat-hold 0.13",
            test="tests/test_skaffold_sync_goldens.py",
            test_body="assert sync includes goldens; evals-only unused",
            test_obs="test_skaffold_not_omit_goldens",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed seat-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed seat-hold",
            diff_obs=" skaffold.yaml | 6+-\n tests/test_skaffold_sync_goldens.py | 12++\n",
            residual="Profile leftover still syncs evals/ only.",
        ),
        _bad(
            slug="tilt-live-omit-goldens-q86x",
            domain="tilt-eval",
            kind="render",
            avoided="r308 bazel omit; r355 skaffold; r319 Aim hash",
            goal=(
                "Tilt leftover live_update only syncs evals/ so planted overbook-hold never "
                "reaches the container. Add goldens sync locally."
            ),
            plan="Dump Tiltfile, add goldens, prove planted overbook-hold locally.",
            outcome=(
                "Local live_update syncs goldens/. Planted overbook-hold present locally. "
                "Handoff: the team leftover Tiltfile still evals only."
            ),
            ticket=(
                "Title: Tilt leftover live_update evals/. planted overbook-hold missing."
            ),
            src="Tiltfile",
            src_obs="sync('./evals', '/app/evals')  # leftover no goldens",
            run="evals/tilt_eval.py",
            fail_obs="container leftover no goldens. planted overbook-hold absent",
            inspect="Tiltfile",
            inspect_obs="sync leftover evals only",
            first_path="Tiltfile",
            first_old="sync('./evals', '/app/evals')",
            first_new="sync('./evals', '/app/evals')\n    # TODO goldens",
            first_obs="comment only. team leftover still evals only",
            rate_tail="team leftover Tiltfile evals only",
            still_after_429="team leftover omit; planted overbook-hold absent",
            grep="live_update|goldens|sync\\(",
            grep_obs="cannot change team Tiltfile from this ticket",
            plan_change="local sync goldens; document team leftover evals only",
            fix_path="Tiltfile",
            fix_old="    # TODO goldens",
            fix_new="    sync('./goldens', '/app/goldens')",
            fix_obs="local planted present. team leftover HANDOFF",
            retry_obs="502 unused. team leftover evals only. Partial",
            test="tests/test_tilt_sync_goldens.py",
            test_body="xfail team leftover evals only; local goldens sync",
            test_obs="team leftover Tiltfile. Partial",
            suite_obs="local goldens sync. team leftover evals only. Partial.",
            gate_obs="local goldens sync. team leftover evals only. Partial.",
            diff_obs=" Tiltfile | 2+-\n HANDOFF tilt team\n",
            residual="Team leftover Tiltfile still evals only. Partial.",
        ),
    )
)
