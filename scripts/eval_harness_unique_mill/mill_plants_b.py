"""Unique eval-harness leftover plants r298–r307. Not r50–r252 or r253–r293 clones."""

from mill_plants import PAIRS, _bad, _ok

# ---------------------------------------------------------------------------
# r298 fmt leftover — not Black wrap steps hash, not isort params reorder
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="prettier-json-sort-bind-f71m",
            domain="inventory-hold",
            kind="fmt",
            avoided="r290 Black wrap evaluation_steps hash; r290 isort params reorder",
            goal=(
                "Prettier leftover --json-sort-keys rewrites goldens so a line-oriented fixture "
                "binds expected_output to the previous row's 2-hour inventory hold. Parse JSON "
                "by key; disable json-sort-keys on goldens."
            ),
            plan="Dump prettier config, stop sorting golden keys, switch matcher to object identity.",
            outcome=(
                "Goldens parsed by key. prettierignore goldens/. Planted 15-min hold expected "
                "stays bound. Residual: editor prettier-on-save still sorts one file."
            ),
            ticket=(
                "Title: planted 15-min hold golden expected_output bound to 2-hour after prettier "
                "--json-sort-keys leftover."
            ),
            src="evals/hold_eval.py",
            src_obs="fixture = [ln.split('|')[2] for ln in golden_lines]  # expected_output by column",
            run="evals/hold_eval.py",
            fail_obs="planted 15-min row expected became 2-hour after key sort shifted columns",
            inspect=".prettierrc.json",
            inspect_obs='{"jsonSortKeys": true} leftover for whole repo including goldens/',
            first_path=".prettierrc.json",
            first_old='"jsonSortKeys": true',
            first_new='"jsonSortKeys": false',
            first_obs="repo default false. leftover .prettierignore missing; CI still --json-sort-keys flag",
            rate_tail="CI leftover --json-sort-keys on goldens; column bind still wrong",
            still_after_429="CI flag leftover sorts keys; 15-min bound to 2-hour",
            grep="jsonSortKeys|prettier|goldens",
            grep_obs="prettierignore goldens; parse JSON objects not columns",
            plan_change="object matcher by key; prettierignore goldens/; drop CI sort flag",
            fix_path="evals/hold_eval.py",
            fix_old="fixture = [ln.split('|')[2] for ln in golden_lines]",
            fix_new="fixture = [json.loads(ln)['expected_output'] for ln in golden_lines]",
            fix_obs="15-min expected bound correctly. planted 0.14 fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted 15-min vs 2-hour 0.14",
            test="tests/test_hold_golden_key_bind.py",
            test_body="assert expected_output == '15-min hold' after prettier",
            test_obs="test_golden_expected_bound_by_key_not_column",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed 15-min hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed 15-min hold",
            diff_obs=" evals/hold_eval.py | 6+-\n .prettierignore | 2++\n tests/test_hold_golden_key_bind.py | 10++\n",
            residual="Editor prettier-on-save still sorts one unignored JSON golden.",
        ),
        _bad(
            slug="djlint-jinja-prompt-cache-g72n",
            domain="hold-prompt",
            kind="fmt",
            avoided="r290 Black wrap steps hash; r290 isort params; r261 anthropic prompt cache",
            goal=(
                "djlint leftover reformats a Jinja judge prompt so the compiled-prompt cache key "
                "(whitespace-normalized) still hits a pre-lint 120-min hold clause. Hash formatted "
                "bytes; compile after lint."
            ),
            plan="Dump cache key, compile after djlint, include formatted bytes in the key.",
            outcome=(
                "Local cache key is sha256 of post-djlint bytes. Planted 15-min prompt used. "
                "Handoff: worker disk still has the pre-djlint 120-min compiled prompt."
            ),
            ticket=(
                "Title: djlint reflowed {% if hold_min == 15 %} but leftover prompt cache still "
                "serves 120-min clause."
            ),
            src="evals/prompt_compile.py",
            src_obs="key = sha256(re.sub(r'\\s+', ' ', source)).hexdigest()  # whitespace-normalized leftover",
            run="evals/hold_prompt_eval.py",
            fail_obs="post-djlint source says 15. cache hit leftover 120-min compiled prompt",
            inspect="evals/prompt_compile.py",
            inspect_obs="normalization leftover collapses djlint reflow → same key as 120-min era",
            first_path="evals/prompt_compile.py",
            first_old="key = sha256(re.sub(r'\\s+', ' ', source)).hexdigest()",
            first_new="key = sha256(source.encode()).hexdigest()  # still misses worker leftover file",
            first_obs="local key changed. worker ~/.cache/prompts leftover 120-min file still loaded by path",
            rate_tail="worker leftover compiled prompt path still 120-min",
            still_after_429="worker disk leftover; planted still 120-min clause",
            grep="djlint|prompt_compile|hold_min",
            grep_obs="cannot wipe worker home cache from this repo",
            plan_change="hash post-lint bytes; document worker leftover handoff",
            fix_path="evals/prompt_compile.py",
            fix_old="load(path=CACHE / 'hold.jinja.compiled')",
            fix_new="load(path=CACHE / key)  # do not use leftover stable filename",
            fix_obs="local planted 15-min used. worker leftover filename HANDOFF",
            retry_obs="502 unused. worker leftover compiled prompt. Partial",
            test="tests/test_djlint_prompt_cache.py",
            test_body="xfail worker ~/.cache/prompts leftover; local hash post-lint",
            test_obs="worker leftover compiled prompt. Partial",
            suite_obs="local 15-min prompt. worker leftover 120-min. Partial.",
            gate_obs="local 15-min prompt. worker leftover 120-min. Partial.",
            diff_obs=" evals/prompt_compile.py | 6+-\n HANDOFF worker cache\n",
            residual="Worker disk still has leftover pre-djlint 120-min compiled prompt. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r299 cache leftover — not r253 xdist, not r265 lru id(tc)
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="diskcache-fanout-trunc-h73o",
            domain="chargeback-desk",
            kind="cache",
            avoided="r253 xdist cache; r265 lru_cache id(tc); r263 redis semantic cache",
            goal=(
                "diskcache leftover fanout key truncated to 40 chars collides "
                "faith:chargeback-7day-ack with faith:chargeback-45day-deny so leftover 1.0 is "
                "reused. Hash the full key; include metric+input+expected."
            ),
            plan="Dump fanout key, stop truncating, sha256 full identity, prove 7-day vs 45-day diverge.",
            outcome=(
                "Cache key is sha256 of metric+input+expected+actual. Planted 45-day deny 0.11. "
                "Residual: Windows runner still uses a 32-char leftover prefix helper."
            ),
            ticket=(
                "Title: diskcache key[:40] leftover collision 7-day-ack vs 45-day-deny. planted "
                "deny reused 1.0."
            ),
            src="evals/diskcache_key.py",
            src_obs="fanout = key[:40]  # leftover diskcache directory shard",
            run="evals/chargeback_eval.py",
            fail_obs="7-day-ack and 45-day-deny share fanout faith:chargeback- leftover 1.0",
            inspect="evals/diskcache_key.py",
            inspect_obs="key[:40] identical for both chargeback windows; shard file leftover 1.0",
            first_path="evals/diskcache_key.py",
            first_old="fanout = key[:40]",
            first_new="fanout = key[:80]",
            first_obs="[:80] still collides on faith:chargeback-7day vs 45day prefix",
            rate_tail="[:80] leftover still collides; planted deny 1.0",
            still_after_429="truncated fanout leftover; 45-day deny 1.0",
            grep="fanout|diskcache|chargeback",
            grep_obs="use sha256 full key; never slice identity",
            plan_change="sha256(metric+input+expected+actual); no prefix slice",
            fix_path="evals/diskcache_key.py",
            fix_old="fanout = key[:80]",
            fix_new="fanout = sha256(key.encode()).hexdigest()",
            fix_obs="keys diverge. planted 45-day deny 0.11 fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted 45-day deny 0.11",
            test="tests/test_diskcache_fanout_hash.py",
            test_body="assert sha256 keys differ for 7-day-ack vs 45-day-deny",
            test_obs="test_chargeback_windows_do_not_share_fanout",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed 45-day deny",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed 45-day deny",
            diff_obs=" evals/diskcache_key.py | 5+-\n tests/test_diskcache_fanout_hash.py | 12++\n",
            residual="Windows runner still uses a 32-char leftover prefix helper.",
        ),
        _bad(
            slug="joblib-memory-cwd-stale-i74p",
            domain="locale-price",
            kind="cache",
            avoided="r253 xdist cache; r265 lru id(tc); r268 docker .deepeval layer",
            goal=(
                "joblib.Memory leftover location .cache/eval is relative to CWD so a CI leftover "
                "workspace from the previous job serves 1.0 on planted locale-price goldens. Use "
                "a per-commit cache dir."
            ),
            plan="Dump Memory location, stop using relative CWD, isolate per-commit, prove planted fail.",
            outcome=(
                "Local Memory dir is .cache/eval-$GIT_SHA. Planted locale-price 0.22 locally. "
                "Handoff: self-hosted runner workspace leftover .cache/eval still not wiped."
            ),
            ticket=(
                "Title: joblib Memory('.cache/eval') leftover CWD cache. planted EUR grouping lie "
                "still 1.0 from previous job."
            ),
            src="evals/joblib_memo.py",
            src_obs="MEM = Memory('.cache/eval')  # leftover relative CWD",
            run="evals/locale_price_eval.py",
            fail_obs="Cache HIT .cache/eval/joblib/measure leftover score=1.0 planted EUR",
            inspect="evals/joblib_memo.py",
            inspect_obs="relative path leftover. CI cwd is runner workspace reused across jobs",
            first_path="evals/joblib_memo.py",
            first_old="Memory('.cache/eval')",
            first_new="Memory('/tmp/eval-cache')",
            first_obs="/tmp still shared across jobs on the self-hosted runner leftover",
            rate_tail="shared /tmp leftover Memory 1.0",
            still_after_429="runner /tmp leftover; planted EUR still 1.0",
            grep="Memory|joblib|.cache/eval",
            grep_obs="cannot wipe self-hosted /tmp from this repo",
            plan_change="per-commit dir locally; document runner leftover handoff",
            fix_path="evals/joblib_memo.py",
            fix_old="Memory('/tmp/eval-cache')",
            fix_new="Memory(f'.cache/eval-{os.environ[\"GIT_SHA\"]}')",
            fix_obs="local per-sha miss planted 0.22. runner leftover HANDOFF",
            retry_obs="502 unused. runner workspace leftover. Partial",
            test="tests/test_joblib_memory_isolation.py",
            test_body="xfail runner workspace leftover; local Memory uses GIT_SHA",
            test_obs="runner leftover Memory. Partial",
            suite_obs="local planted 0.22. runner leftover .cache. Partial.",
            gate_obs="local planted 0.22. runner leftover .cache. Partial.",
            diff_obs=" evals/joblib_memo.py | 4+-\n HANDOFF runner workspace\n",
            residual="Self-hosted runner workspace leftover .cache/eval not wiped. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r300 CI leftover — not Helm judge-model, not GHA continue-on-error
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="buildkite-shard-report-ovw-j75q",
            domain="mfa-skip",
            kind="ci",
            avoided="r272 GHA continue-on-error; r282 CircleCI skipped=error; r291 Helm judge-model",
            goal=(
                "Buildkite leftover artifact name eval-report.json per shard so the last all-pass "
                "shard overwrites a planted MFA-skip fail from shard 2. Unique artifact names and "
                "merge junit; fail if any shard failed."
            ),
            plan="Dump artifact names, unique per shard, merge junit, prove planted MFA-skip visible.",
            outcome=(
                "Artifacts eval-report-shard-N.json merged. Planted MFA-skip 0.13 fails the gather "
                "step. Residual: an old Slack notifier still reads eval-report.json only."
            ),
            ticket=(
                "Title: Buildkite gather sees 0 fails. leftover artifact eval-report.json overwritten "
                "by last all-pass shard; planted MFA-skip was shard 2."
            ),
            src="ci/pipeline.yml",
            src_obs="artifact_paths: eval-report.json  # leftover same name every shard",
            run="evals/mfa_skip_eval.py",
            fail_obs="shard-2 planted MFA-skip fail. gather downloaded leftover shard-4 pass report",
            inspect="ci/pipeline.yml",
            inspect_obs="parallelism: 4. artifact name not templated with BUILDKITE_PARALLEL_JOB",
            first_path="ci/pipeline.yml",
            first_old="artifact_paths: eval-report.json",
            first_new="artifact_paths: eval-report-${BUILDKITE_PARALLEL_JOB}.json",
            first_obs="unique names. gather still cats eval-report.json leftover glob",
            rate_tail="gather leftover glob eval-report.json misses shard files",
            still_after_429="gather leftover filename; planted MFA-skip dropped",
            grep="artifact_paths|eval-report|parallel",
            grep_obs="merge all shard junit; fail if any failure",
            plan_change="unique artifacts plus junit merge; no last-writer-wins",
            fix_path="ci/gather.sh",
            fix_old="cat eval-report.json",
            fix_new="junit-merge eval-report-*.json && test ${fails} -eq 0",
            fix_obs="planted MFA-skip 0.13 fails gather. 5 gold shards pass",
            retry_obs="502 then retry; gather fails on planted MFA-skip 0.13",
            test="tests/test_buildkite_shard_merge.py",
            test_body="assert gather fails if any shard report has failures",
            test_obs="test_gather_merges_shard_reports_fail_closed",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed MFA-skip",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed MFA-skip",
            diff_obs=" ci/pipeline.yml | 4+-\n ci/gather.sh | 8+-\n tests/test_buildkite_shard_merge.py | 12++\n",
            residual="Old Slack notifier still reads leftover eval-report.json only.",
        ),
        _bad(
            slug="gitlab-dotenv-eval-pass-k76r",
            domain="gdpr-erase",
            kind="ci",
            avoided="r272 GHA continue-on-error; r288 dotenv empty threshold; r291 Helm judge-model",
            goal=(
                "GitLab leftover dotenv report EVAL_PASS=true from the lint job is merged into "
                "deploy so a planted GDPR-erase fail is ignored. Use a unique EVAL_HARNESS_PASS "
                "key and fail deploy if missing."
            ),
            plan="Dump dotenv artifacts, stop merging lint EVAL_PASS, unique key, fail if missing.",
            outcome=(
                "Local eval job writes EVAL_HARNESS_PASS. Deploy fails if missing. Handoff: another "
                "pipeline still exports leftover EVAL_PASS=true from lint."
            ),
            ticket=(
                "Title: deploy proceeds after planted GDPR-erase fail. leftover dotenv EVAL_PASS=true "
                "from lint job merged by artifacts:reports:dotenv."
            ),
            src=".gitlab-ci.yml",
            src_obs="lint artifacts:reports:dotenv: eval.env  # EVAL_PASS=true leftover",
            run="evals/gdpr_erase_eval.py",
            fail_obs="eval job EVAL_PASS=false. deploy still true leftover from lint dotenv merge",
            inspect=".gitlab-ci.yml",
            inspect_obs="dotenv reports merge keys leftover; last-write is lint not eval",
            first_path=".gitlab-ci.yml",
            first_old="EVAL_PASS=true",
            first_new="EVAL_PASS=false  # lint should not claim pass",
            first_obs="lint no longer true. leftover other pipeline still exports EVAL_PASS=true",
            rate_tail="other pipeline leftover EVAL_PASS=true",
            still_after_429="merged leftover EVAL_PASS; deploy proceeds",
            grep="EVAL_PASS|dotenv|gdpr",
            grep_obs="unique key EVAL_HARNESS_PASS; cannot change the other pipeline here",
            plan_change="EVAL_HARNESS_PASS only from eval; handoff leftover EVAL_PASS",
            fix_path="ci/eval.env.sh",
            fix_old="echo EVAL_PASS=$ok",
            fix_new="echo EVAL_HARNESS_PASS=$ok",
            fix_obs="local deploy checks EVAL_HARNESS_PASS. leftover EVAL_PASS HANDOFF",
            retry_obs="502 unused. other pipeline leftover EVAL_PASS. Partial",
            test="tests/test_gitlab_dotenv_harness_key.py",
            test_body="xfail leftover EVAL_PASS merge; local uses EVAL_HARNESS_PASS",
            test_obs="other pipeline leftover EVAL_PASS. Partial",
            suite_obs="local unique key. leftover EVAL_PASS still merged elsewhere. Partial.",
            gate_obs="local unique key. leftover EVAL_PASS still merged elsewhere. Partial.",
            diff_obs=" .gitlab-ci.yml | 4+-\n ci/eval.env.sh | 2+-\n HANDOFF other pipeline\n",
            residual="Another pipeline still exports leftover EVAL_PASS=true from lint. Partial.",
        ),
    )
)

# ---------------------------------------------------------------------------
# r301 judge leftover — not GEval, not instructor tool classname
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="instructor-ge-retry-swallow-l77s",
            domain="currency-round",
            kind="judge",
            avoided="r261 instructor tool classname; r254 extra=forbid; r283 tenacity retry AssertionError",
            goal=(
                "Instructor leftover Field(ge=0.5) on JudgeScore retries until the model emits "
                ">=0.5 so a planted currency-round lie 0.2 becomes 0.71. Allow 0..1 and persist "
                "the first parse; max_retries=0."
            ),
            plan="Dump Field constraints, drop ge=0.5, persist first parse, prove planted 0.2.",
            outcome=(
                "JudgeScore ge=0 le=1, max_retries=0. Planted currency-round 0.2 fail-closed. "
                "Residual: a second adapter still retries on ValidationError."
            ),
            ticket=(
                "Title: planted half-cent round-up lie first parse 0.2 then instructor leftover "
                "ge=0.5 retries to 0.71."
            ),
            src="evals/instructor_score.py",
            src_obs="class JudgeScore(BaseModel):\n    score: float = Field(ge=0.5, le=1.0)\n",
            run="evals/currency_round_eval.py",
            fail_obs="first parse 0.2 ValidationError. retry leftover emits 0.71 pass",
            inspect="evals/instructor_score.py",
            inspect_obs="ge=0.5 leftover from a 'low scores are malformed' comment. max_retries=8",
            first_path="evals/instructor_score.py",
            first_old="Field(ge=0.5, le=1.0)",
            first_new="Field(ge=0.0, le=1.0)",
            first_obs="range ok. max_retries=8 leftover still resamples 0.2 until 0.6+",
            rate_tail="max_retries leftover still swallows 0.2",
            still_after_429="retries leftover; planted 0.2 not persisted",
            grep="Field|max_retries|JudgeScore",
            grep_obs="max_retries=0; persist first parse even when score is 0.2",
            plan_change="ge=0 le=1; max_retries=0; first parse is the score",
            fix_path="evals/instructor_score.py",
            fix_old="max_retries=8",
            fix_new="max_retries=0",
            fix_obs="first parse 0.2 persisted. planted fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted currency-round 0.2",
            test="tests/test_instructor_first_parse.py",
            test_body="assert first 0.2 persisted; no retry on valid parse",
            test_obs="test_instructor_does_not_retry_low_scores",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed currency-round 0.2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed currency-round 0.2",
            diff_obs=" evals/instructor_score.py | 4+-\n tests/test_instructor_first_parse.py | 12++\n",
            residual="A second adapter still retries on ValidationError.",
        ),
        _bad(
            slug="marvin-cast-bool-faithful-m78t",
            domain="tax-inclusive",
            kind="judge",
            avoided="r254 GEval extra=forbid; r261 instructor classname; r11 vacuous GEval",
            goal=(
                "Marvin leftover cast(bool) on 'is the quote tax-inclusive?' treats 'partially' as "
                "True so planted exclusive quotes pass. Switch to a Likert 1-5 and fail below 4."
            ),
            plan="Dump cast(bool), replace with Likert, fail <4, prove planted exclusive fail.",
            outcome=(
                "Local Likert 1-5 fail below 4. Planted tax-exclusive 'partially' scores 2. "
                "Handoff: prod API still uses leftover bool cast."
            ),
            ticket=(
                "Title: marvin.cast(bool) leftover. planted tax-exclusive answer 'partially' → True."
            ),
            src="evals/marvin_cast.py",
            src_obs="ok = marvin.cast(bool, f'is this quote tax-inclusive? {output}')",
            run="evals/tax_inclusive_eval.py",
            fail_obs="planted exclusive 'partially' → True leftover bool cast",
            inspect="evals/marvin_cast.py",
            inspect_obs="bool cast leftover. any non-empty hedging string is True",
            first_path="evals/marvin_cast.py",
            first_old="marvin.cast(bool, prompt)",
            first_new="marvin.cast(Literal['yes','no','partial'], prompt)",
            first_obs="local Literal. prod pin leftover still bool",
            rate_tail="prod leftover bool cast; planted still True",
            still_after_429="prod leftover bool; planted exclusive passes",
            grep="marvin.cast|tax-inclusive|Likert",
            grep_obs="cannot bump prod pin from this repo",
            plan_change="Likert locally; document prod leftover bool handoff",
            fix_path="evals/marvin_cast.py",
            fix_old="marvin.cast(Literal['yes','no','partial'], prompt)",
            fix_new="score = marvin.cast(int, likert_prompt)  # fail if score < 4",
            fix_obs="local planted 2 fail. prod leftover bool HANDOFF",
            retry_obs="502 unused. prod leftover bool cast. Partial",
            test="tests/test_marvin_likert_not_bool.py",
            test_body="xfail prod bool cast; local Likert fail <4",
            test_obs="prod leftover bool. Partial",
            suite_obs="local Likert fail. prod leftover bool. Partial.",
            gate_obs="local Likert fail. prod leftover bool. Partial.",
            diff_obs=" evals/marvin_cast.py | 6+-\n HANDOFF prod pin\n",
            residual="Prod API still uses leftover marvin.cast(bool). Partial.",
        ),
    )
)
