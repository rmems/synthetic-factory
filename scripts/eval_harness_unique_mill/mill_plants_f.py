"""Unique eval-harness leftover plants r320–r339. Not r319/GEval-cache/test_ clones."""

from mill_plants import PAIRS, _bad, _ok

# r320 recipe leftover
PAIRS.append(
    (
        _ok(
            slug="justfile-legacy-recipe-x15e",
            domain="just-eval",
            kind="recipe",
            avoided="r271 makefile stale; r300 Buildkite shard; r319 ClearML output_uri",
            goal=(
                "Just leftover recipe eval still runs deepeval test run evals/legacy.py so a "
                "planted chargeback-void golden in evals/chargeback.py is never collected. Point "
                "the recipe at evals/*.py and fail if planted ids are missing."
            ),
            plan="Dump just eval, retarget evals/*.py, prove planted chargeback-void fail.",
            outcome=(
                "just eval runs evals/*.py. Planted chargeback-void 0.13 fail-closed. Residual: "
                "a laptop leftover still aliases just to just --justfile ~/Justfile."
            ),
            ticket=(
                "Title: just eval leftover recipe evals/legacy.py. planted chargeback-void never "
                "collected; gate 1.0."
            ),
            src="Justfile",
            src_obs="eval:\n    deepeval test run evals/legacy.py  # leftover pre-split recipe",
            run="evals/chargeback.py",
            fail_obs="legacy.py leftover 5 gold. planted chargeback-void absent 1.0",
            inspect="Justfile",
            inspect_obs="recipe leftover names only evals/legacy.py",
            first_path="Justfile",
            first_old="deepeval test run evals/legacy.py",
            first_new="deepeval test run evals/chargeback.py",
            first_obs="chargeback local. leftover ~/Justfile still legacy.py",
            rate_tail="home Justfile leftover still legacy.py",
            still_after_429="home leftover recipe; planted chargeback-void absent",
            grep="Justfile|legacy.py|evals/\\*\\.py",
            grep_obs="pin --justfile ./Justfile; glob evals/*.py; require planted id",
            plan_change="pin local Justfile; glob evals/*.py; fail if planted id missing",
            fix_path="Justfile",
            fix_old="deepeval test run evals/chargeback.py",
            fix_new="deepeval test run evals/*.py",
            fix_obs="planted chargeback-void 0.13 collected. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted chargeback-void 0.13",
            test="tests/test_just_eval_glob.py",
            test_body="assert just eval globs evals/*.py; planted id present",
            test_obs="test_just_eval_not_legacy_only",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed chargeback-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed chargeback-void",
            diff_obs=" Justfile | 4+-\n tests/test_just_eval_glob.py | 12++\n",
            residual="Laptop leftover still aliases just to just --justfile ~/Justfile.",
        ),
        _bad(
            slug="taskfile-dir-legacy-y16f",
            domain="task-eval",
            kind="recipe",
            avoided="r271 makefile stale; r288 dotenv empty; r319 Aim run hash",
            goal=(
                "Task leftover cmds.eval.dir: ../legacy so planted after-hours-refund in this "
                "repo never runs. Set dir to the workspace; fail if eval cwd is outside it."
            ),
            plan="Dump Task dir, pin repo root, prove planted after-hours-refund locally.",
            outcome=(
                "Local Task dir is the repo. Planted after-hours-refund 0.18 locally. Handoff: "
                "the parent leftover Taskfile still sets dir: ../legacy."
            ),
            ticket=(
                "Title: Task leftover eval.dir=../legacy. planted after-hours-refund never collected."
            ),
            src="Taskfile.yml",
            src_obs="eval:\n  dir: ../legacy  # leftover pre-monorepo split",
            run="evals/after_hours.py",
            fail_obs="cwd leftover ../legacy. planted after-hours-refund absent",
            inspect="Taskfile.yml",
            inspect_obs="dir leftover ../legacy. this-repo evals unused",
            first_path="Taskfile.yml",
            first_old="dir: ../legacy",
            first_new="dir: .",
            first_obs="local dir .. parent leftover Taskfile still ../legacy",
            rate_tail="parent leftover dir ../legacy wins include",
            still_after_429="parent leftover dir; planted after-hours-refund absent",
            grep="dir: ../legacy|Taskfile.yml|includes:",
            grep_obs="cannot edit parent Taskfile from this ticket",
            plan_change="local dir repo root; document parent leftover ../legacy",
            fix_path="Taskfile.yml",
            fix_old="dir: .",
            fix_new="dir: '{{.USER_WORKING_DIR}}'",
            fix_obs="local planted present. parent leftover HANDOFF",
            retry_obs="502 unused. parent leftover dir ../legacy. Partial",
            test="tests/test_taskfile_eval_dir.py",
            test_body="xfail parent leftover dir ../legacy; local cwd repo",
            test_obs="parent leftover dir ../legacy. Partial",
            suite_obs="local repo dir. parent leftover ../legacy. Partial.",
            gate_obs="local repo dir. parent leftover ../legacy. Partial.",
            diff_obs=" Taskfile.yml | 2+-\n HANDOFF parent Taskfile dir\n",
            residual="Parent leftover Taskfile still sets eval.dir=../legacy. Partial.",
        ),
    )
)

# r321 tool-env leftover
PAIRS.append(
    (
        _ok(
            slug="mise-results-folder-z17g",
            domain="mise-env",
            kind="env",
            avoided="r288 dotenv empty; r289 direnv vs tox; r319 ClearML output_uri",
            goal=(
                "mise leftover [env] DEEPEVAL_RESULTS_FOLDER=./old-results so planted dual-tax "
                "scores write to a folder the gate never reads. Point the env at ./results/"
                "{{sha}} and fail if the gate path is empty."
            ),
            plan="Dump mise env, pin results/sha, prove planted dual-tax is the gate input.",
            outcome=(
                "Results folder is results/<sha>. Planted dual-tax 0.14 fails the gate. Residual: "
                "a shell leftover still exports DEEPEVAL_RESULTS_FOLDER=./old-results."
            ),
            ticket=(
                "Title: mise leftover DEEPEVAL_RESULTS_FOLDER=./old-results. planted dual-tax "
                "never reaches the gate; gate reads empty 1.0."
            ),
            src="mise.toml",
            src_obs="[env]\nDEEPEVAL_RESULTS_FOLDER = './old-results'  # leftover stable dir",
            run="evals/dual_tax.py",
            fail_obs="wrote old-results leftover. gate reads ./results empty 1.0",
            inspect="mise.toml",
            inspect_obs="stable dir leftover. no sha in folder name",
            first_path="mise.toml",
            first_old="DEEPEVAL_RESULTS_FOLDER = './old-results'",
            first_new="DEEPEVAL_RESULTS_FOLDER = './results-dev'",
            first_obs="results-dev local. leftover export still old-results",
            rate_tail="shell leftover export old-results",
            still_after_429="export leftover; planted dual-tax not in gate path",
            grep="DEEPEVAL_RESULTS_FOLDER|old-results|mise.toml",
            grep_obs="unset leftover export; folder results/<sha>; fail empty gate",
            plan_change="results/<git_sha>; refuse old-results; fail if gate dir empty",
            fix_path="mise.toml",
            fix_old="DEEPEVAL_RESULTS_FOLDER = './results-dev'",
            fix_new="DEEPEVAL_RESULTS_FOLDER = './results/{{env.GIT_SHA}}'",
            fix_obs="planted dual-tax 0.14 in results/sha. gate reads it",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-tax 0.14",
            test="tests/test_mise_results_sha.py",
            test_body="assert results folder includes sha; old-results unused",
            test_obs="test_mise_results_not_old_folder",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-tax",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-tax",
            diff_obs=" mise.toml | 4+-\n tests/test_mise_results_sha.py | 12++\n",
            residual="Shell leftover still exports DEEPEVAL_RESULTS_FOLDER=./old-results.",
        ),
        _bad(
            slug="asdf-shim-deepeval-a18h",
            domain="asdf-shim",
            kind="env",
            avoided="r289 direnv vs tox; r270 metrics module shadow; r319 Aim hash",
            goal=(
                "asdf leftover shim ~/.asdf/shims/deepeval points at 0.21 where missing "
                "is_successful is True so a planted gift-card-stack never fails. Pin the local "
                "plugin version; fail if the shim path is outside the repo."
            ),
            plan="Dump shim, pin local deepeval, prove planted gift-card-stack fail locally.",
            outcome=(
                "Local .tool-versions pins deepeval 2.x. Planted gift-card-stack 0.16 locally. "
                "Handoff: CI leftover image still uses the 0.21 shim."
            ),
            ticket=(
                "Title: asdf leftover shim deepeval 0.21. planted gift-card-stack missing "
                "is_successful treated as True."
            ),
            src=".tool-versions",
            src_obs="python 3.11.9\n# leftover no deepeval pin; shim 0.21 from image",
            run="evals/gift_card.py",
            fail_obs="shim leftover 0.21. missing is_successful True. planted gift-card-stack pass",
            inspect=".asdf/shims/deepeval",
            inspect_obs="shim leftover /opt/asdf/installs/deepeval/0.21",
            first_path=".tool-versions",
            first_old="python 3.11.9",
            first_new="python 3.11.9\ndeepeval 2.5.0",
            first_obs="local pin. CI leftover image still 0.21 shim first on PATH",
            rate_tail="CI leftover PATH shim 0.21",
            still_after_429="CI leftover shim; planted gift-card-stack True",
            grep="asdf/shims|deepeval 0.21|is_successful",
            grep_obs="cannot rebuild CI image from this ticket",
            plan_change="local pin + PATH repo venv; document CI leftover shim",
            fix_path="evals/gift_card.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert '0.21' not in which('deepeval')",
            fix_obs="local planted 0.16. CI leftover shim HANDOFF",
            retry_obs="502 unused. CI leftover 0.21 shim. Partial",
            test="tests/test_asdf_shim_not_old.py",
            test_body="xfail CI leftover 0.21 shim; local pin 2.x",
            test_obs="CI leftover shim. Partial",
            suite_obs="local pin 2.x. CI leftover 0.21 shim. Partial.",
            gate_obs="local pin 2.x. CI leftover 0.21 shim. Partial.",
            diff_obs=" .tool-versions | 2+-\n HANDOFF CI asdf shim\n",
            residual="CI leftover image still uses the 0.21 deepeval shim. Partial.",
        ),
    )
)

# r322 vcs leftover
PAIRS.append(
    (
        _ok(
            slug="git-lfs-pointer-goldens-b19i",
            domain="lfs-golden",
            kind="vcs",
            avoided="r292 ansible golden perms; r308 bazel omit goldens; r319 ClearML uri",
            goal=(
                "git-lfs leftover pointer goldens/loyalty.jsonl was never smudged so planted "
                "loyalty-clawback rows never load and the suite is 5 golds at 1.0. Fetch LFS "
                "and fail-closed if a golden file still starts with version https://git-lfs."
            ),
            plan="Dump LFS pointer, smudge goldens, prove planted loyalty-clawback fail.",
            outcome=(
                "Goldens smudged. Planted loyalty-clawback 0.12 fail-closed. Residual: a sparse "
                "checkout leftover still skips lfs fetch on CI skip-smudge."
            ),
            ticket=(
                "Title: goldens/loyalty.jsonl leftover LFS pointer. planted loyalty-clawback "
                "never loads."
            ),
            src="goldens/loyalty.jsonl",
            src_obs="version https://git-lfs.github.com/spec/v1\noid sha256:ab\nsize 12",
            run="evals/loyalty.py",
            fail_obs="json.JSONDecodeError leftover pointer. suite skipped to 5 gold 1.0",
            inspect=".gitattributes",
            inspect_obs="goldens/** filter=lfs leftover. CI GIT_LFS_SKIP_SMUDGE=1",
            first_path=".gitattributes",
            first_old="goldens/** filter=lfs diff=lfs merge=lfs -text",
            first_new="goldens/** filter=lfs diff=lfs merge=lfs -text\n# require smudge",
            first_obs="comment only. CI leftover SKIP_SMUDGE still 1",
            rate_tail="CI leftover GIT_LFS_SKIP_SMUDGE=1",
            still_after_429="skip-smudge leftover; planted loyalty-clawback absent",
            grep="GIT_LFS_SKIP_SMUDGE|git lfs|pointer",
            grep_obs="unset skip-smudge; fail if file starts with version https://git-lfs",
            plan_change="git lfs pull; refuse pointer files; fail-closed empty goldens",
            fix_path="evals/loyalty.py",
            fix_old="goldens = load('goldens/loyalty.jsonl')",
            fix_new="goldens = load_smudged('goldens/loyalty.jsonl')",
            fix_obs="planted loyalty-clawback 0.12 loaded. pointer rejected",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-clawback 0.12",
            test="tests/test_goldens_not_lfs_pointer.py",
            test_body="assert golden not pointer; planted id loads",
            test_obs="test_loyalty_goldens_smudged",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-clawback",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-clawback",
            diff_obs=" evals/loyalty.py | 6+-\n tests/test_goldens_not_lfs_pointer.py | 12++\n",
            residual="Sparse checkout leftover still skips lfs fetch on CI skip-smudge.",
        ),
        _bad(
            slug="git-submodule-goldens-sha-c20j",
            domain="submodule-golden",
            kind="vcs",
            avoided="r308 bazel omit goldens; r292 golden perms; r319 Aim hash",
            goal=(
                "git submodule leftover evals/goldens pinned to yesterday's SHA so planted "
                "trial-extend is missing. Bump the submodule; fail if HEAD does not contain "
                "the planted id."
            ),
            plan="Dump submodule SHA, bump, prove planted trial-extend locally.",
            outcome=(
                "Local submodule SHA includes planted trial-extend. Handoff: the superproject "
                "leftover still records the yesterday SHA in .gitmodules init."
            ),
            ticket=(
                "Title: evals/goldens leftover submodule SHA. planted trial-extend missing."
            ),
            src=".gitmodules",
            src_obs="[submodule \"evals/goldens\"]\n  url = ../goldens.git  # leftover no branch pin",
            run="evals/trial_extend.py",
            fail_obs="submodule leftover yesterday SHA. planted trial-extend absent",
            inspect="evals/goldens/.git",
            inspect_obs="HEAD leftover abc123 yesterday. planted id not in tree",
            first_path=".gitmodules",
            first_old="url = ../goldens.git",
            first_new="url = ../goldens.git\n  branch = main",
            first_obs="branch local. superproject leftover still recorded SHA yesterday",
            rate_tail="superproject leftover SHA yesterday",
            still_after_429="recorded SHA leftover; planted trial-extend absent",
            grep="submodule|evals/goldens|abc123",
            grep_obs="cannot bump recorded SHA in every clone from this ticket",
            plan_change="local bump; document superproject leftover SHA handoff",
            fix_path="evals/trial_extend.py",
            fix_old="load('evals/goldens/trials.jsonl')",
            fix_new="require_id(load('evals/goldens/trials.jsonl'), 'trial-extend')",
            fix_obs="local planted present. superproject leftover HANDOFF",
            retry_obs="502 unused. superproject leftover SHA. Partial",
            test="tests/test_submodule_goldens_sha.py",
            test_body="xfail superproject leftover SHA; local require planted id",
            test_obs="superproject leftover SHA. Partial",
            suite_obs="local bump. superproject leftover yesterday SHA. Partial.",
            gate_obs="local bump. superproject leftover yesterday SHA. Partial.",
            diff_obs=" evals/trial_extend.py | 4+-\n HANDOFF submodule SHA\n",
            residual="Superproject leftover still records yesterday SHA. Partial.",
        ),
    )
)

# r323 catalog leftover
PAIRS.append(
    (
        _ok(
            slug="lakefs-branch-stale-d21k",
            domain="lakefs-eval",
            kind="catalog",
            avoided="r268 dvc metrics index; r319 ClearML uri; r305 nix gcroot",
            goal=(
                "lakeFS leftover eval/goldens@main still points at yesterday's commit so planted "
                "address-rewrite never appears. Pin the branch to this SHA and fail if the "
                "object digest mismatches the lockfile."
            ),
            plan="Dump lakeFS ref, pin SHA, prove planted address-rewrite fail.",
            outcome=(
                "eval/goldens pinned to SHA. Planted address-rewrite 0.15 fail-closed. Residual: "
                "a notebook leftover still reads lakefs://eval/goldens/main."
            ),
            ticket=(
                "Title: lakeFS leftover eval/goldens@main. planted address-rewrite missing."
            ),
            src="evals/lakefs_goldens.py",
            src_obs="ref = 'lakefs://eval/goldens/main'  # leftover floating branch",
            run="evals/lakefs_goldens.py",
            fail_obs="main leftover yesterday commit. planted address-rewrite absent",
            inspect="evals/lakefs_goldens.py",
            inspect_obs="floating main leftover. no lockfile digest",
            first_path="evals/lakefs_goldens.py",
            first_old="ref = 'lakefs://eval/goldens/main'",
            first_new="ref = 'lakefs://eval/goldens/main@' + os.getenv('GIT_SHA','')",
            first_obs="sha local. leftover client still follows main without @",
            rate_tail="client leftover strips @sha",
            still_after_429="client leftover main; planted address-rewrite absent",
            grep="lakefs://|goldens/main|lockfile",
            grep_obs="pin commit id; compare digest to goldens.lock",
            plan_change="commit-id ref + digest lock; refuse floating main",
            fix_path="evals/lakefs_goldens.py",
            fix_old="ref = 'lakefs://eval/goldens/main@' + os.getenv('GIT_SHA','')",
            fix_new="ref = lockfile_commit('goldens.lock')",
            fix_obs="planted address-rewrite 0.15. main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted address-rewrite 0.15",
            test="tests/test_lakefs_goldens_lock.py",
            test_body="assert ref is lockfile commit; not floating main",
            test_obs="test_lakefs_not_floating_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed address-rewrite",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed address-rewrite",
            diff_obs=" evals/lakefs_goldens.py | 6+-\n tests/test_lakefs_goldens_lock.py | 12++\n",
            residual="Notebook leftover still reads lakefs://eval/goldens/main.",
        ),
        _bad(
            slug="delta-share-profile-stale-e22l",
            domain="delta-eval",
            kind="catalog",
            avoided="r268 dvc metrics; r319 Aim hash; r305 nix gcroot",
            goal=(
                "Delta Sharing leftover profile config.share.json still names yesterday's share "
                "so planted promo-stack is absent. Pin the share id; fail if the table lacks "
                "the planted id."
            ),
            plan="Dump share profile, pin id, prove planted promo-stack locally.",
            outcome=(
                "Local profile names this SHA share. Planted promo-stack present locally. "
                "Handoff: the recipient leftover still ships yesterday's profile json."
            ),
            ticket=(
                "Title: Delta Sharing leftover profile yesterday share. planted promo-stack missing."
            ),
            src="evals/delta_share.py",
            src_obs="profile = 'config.share.json'  # leftover share id from last week",
            run="evals/delta_share.py",
            fail_obs="profile leftover yesterday share. planted promo-stack absent",
            inspect="config.share.json",
            inspect_obs="shareID leftover abc-old. planted id not in table",
            first_path="evals/delta_share.py",
            first_old="profile = 'config.share.json'",
            first_new="profile = os.getenv('SHARE_PROFILE','config.share.json')",
            first_obs="env unset leftover still yesterday profile",
            rate_tail="recipient leftover profile yesterday share",
            still_after_429="profile leftover; planted promo-stack absent",
            grep="shareID|config.share.json|promo-stack",
            grep_obs="cannot replace recipient profile from this ticket",
            plan_change="local lock share id; document recipient leftover profile",
            fix_path="evals/delta_share.py",
            fix_old="profile = os.getenv('SHARE_PROFILE','config.share.json')",
            fix_new="profile = lockfile_profile('delta.lock')",
            fix_obs="local planted present. recipient leftover HANDOFF",
            retry_obs="502 unused. recipient leftover profile. Partial",
            test="tests/test_delta_share_lock.py",
            test_body="xfail recipient leftover profile; local lock share id",
            test_obs="recipient leftover profile. Partial",
            suite_obs="local lock share. recipient leftover profile. Partial.",
            gate_obs="local lock share. recipient leftover profile. Partial.",
            diff_obs=" evals/delta_share.py | 4+-\n HANDOFF delta profile\n",
            residual="Recipient leftover still ships yesterday's profile json. Partial.",
        ),
    )
)

# r324 orchestrator leftover
PAIRS.append(
    (
        _ok(
            slug="dagster-group-omit-planted-f23m",
            domain="dagster-eval",
            kind="orch",
            avoided="r269 airflow xcom; r269 prefect retry; r308 bazel omit goldens",
            goal=(
                "Dagster leftover Definitions asset group eval_legacy omits planted "
                "cancel-window so the job never materializes it. Add the asset to group "
                "eval_gate; fail if the planted asset key is missing from the job."
            ),
            plan="Dump asset group, add planted key, prove cancel-window materializes.",
            outcome=(
                "eval_gate includes cancel-window. Planted 0.17 stored. Residual: a sensor "
                "leftover still launches group eval_legacy."
            ),
            ticket=(
                "Title: Dagster leftover asset group eval_legacy. planted cancel-window omitted."
            ),
            src="evals/dagster_eval.py",
            src_obs="defs = Definitions(assets=load_assets_from_package_module(eval_legacy))",
            run="evals/dagster_eval.py",
            fail_obs="group leftover eval_legacy. planted cancel-window unused",
            inspect="evals/dagster_eval.py",
            inspect_obs="eval_legacy leftover. cancel-window only in eval_gate package",
            first_path="evals/dagster_eval.py",
            first_old="load_assets_from_package_module(eval_legacy)",
            first_new="load_assets_from_package_module(eval_gate)",
            first_obs="gate local. sensor leftover still launches eval_legacy",
            rate_tail="sensor leftover still group eval_legacy",
            still_after_429="sensor leftover eval_legacy; planted cancel-window omitted",
            grep="eval_legacy|eval_gate|cancel-window",
            grep_obs="job must require asset key cancel_window",
            plan_change="require planted asset key; refuse eval_legacy group",
            fix_path="evals/dagster_eval.py",
            fix_old="load_assets_from_package_module(eval_gate)",
            fix_new="AssetsDefinition.from_graph(eval_gate, required_keys={'cancel_window'})",
            fix_obs="planted cancel-window 0.17 materialized. eval_legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-window 0.17",
            test="tests/test_dagster_group_includes_planted.py",
            test_body="assert job has cancel_window asset; eval_legacy unused",
            test_obs="test_dagster_not_legacy_group",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-window",
            diff_obs=" evals/dagster_eval.py | 6+-\n tests/test_dagster_group_includes_planted.py | 12++\n",
            residual="Sensor leftover still launches group eval_legacy.",
        ),
        _bad(
            slug="luigi-target-exists-g24n",
            domain="luigi-eval",
            kind="orch",
            avoided="r269 prefect retry; r269 airflow xcom; r319 Aim hash",
            goal=(
                "Luigi leftover EvalReport(path).exists() is True from yesterday so the eval "
                "task skips and planted restock-fee never runs. Include sha in the target; "
                "fail if exists() without this SHA."
            ),
            plan="Dump Luigi target, add sha, prove planted restock-fee runs locally.",
            outcome=(
                "Local target path includes sha. Planted restock-fee runs locally. Handoff: the "
                "shared scheduler leftover still has yesterday's complete marker."
            ),
            ticket=(
                "Title: Luigi leftover EvalReport.exists yesterday. planted restock-fee skipped."
            ),
            src="evals/luigi_eval.py",
            src_obs="def output(self): return LocalTarget('reports/eval.json')  # leftover stable",
            run="evals/luigi_eval.py",
            fail_obs="exists leftover True. task SKIPPED. planted restock-fee unused",
            inspect="evals/luigi_eval.py",
            inspect_obs="stable path leftover. no sha in target",
            first_path="evals/luigi_eval.py",
            first_old="LocalTarget('reports/eval.json')",
            first_new="LocalTarget('reports/eval-' + date.today().isoformat() + '.json')",
            first_obs="date local. scheduler leftover still complete on eval.json",
            rate_tail="scheduler leftover complete marker eval.json",
            still_after_429="complete leftover; planted restock-fee skipped",
            grep="LocalTarget|EvalReport|complete",
            grep_obs="cannot clear shared scheduler complete from this ticket",
            plan_change="local sha target; document scheduler leftover complete",
            fix_path="evals/luigi_eval.py",
            fix_old="LocalTarget('reports/eval-' + date.today().isoformat() + '.json')",
            fix_new="LocalTarget(f'reports/eval-{git_sha}.json')",
            fix_obs="local planted runs. scheduler leftover HANDOFF",
            retry_obs="502 unused. scheduler leftover complete. Partial",
            test="tests/test_luigi_target_sha.py",
            test_body="xfail scheduler leftover complete; local sha target",
            test_obs="scheduler leftover complete. Partial",
            suite_obs="local sha target. scheduler leftover complete. Partial.",
            gate_obs="local sha target. scheduler leftover complete. Partial.",
            diff_obs=" evals/luigi_eval.py | 4+-\n HANDOFF luigi complete\n",
            residual="Shared scheduler leftover still has yesterday complete marker. Partial.",
        ),
    )
)

# r325 workflow leftover
PAIRS.append(
    (
        _ok(
            slug="flyte-domain-staging-goldens-h25o",
            domain="flyte-eval",
            kind="workflow",
            avoided="r308 earthly cache mount; r305 pants process; r291 helm judge",
            goal=(
                "Flyte leftover registration domain=staging while goldens live in project eval "
                "domain=prod so planted warranty-transfer never binds. Register in prod; fail "
                "if the domain is not the lockfile domain."
            ),
            plan="Dump Flyte domain, pin prod, prove planted warranty-transfer binds.",
            outcome=(
                "Workflow registered in prod. Planted warranty-transfer 0.11 fail-closed. "
                "Residual: a launchplan leftover still targets domain=staging."
            ),
            ticket=(
                "Title: Flyte leftover domain=staging. planted warranty-transfer never binds."
            ),
            src="evals/flyte_eval.py",
            src_obs="config.domain = 'staging'  # leftover pre-prod cutover",
            run="evals/flyte_eval.py",
            fail_obs="domain leftover staging. planted warranty-transfer unbound",
            inspect="evals/flyte_eval.py",
            inspect_obs="staging leftover. goldens only in prod domain",
            first_path="evals/flyte_eval.py",
            first_old="config.domain = 'staging'",
            first_new="config.domain = os.getenv('FLYTE_DOMAIN','staging')",
            first_obs="env leftover FLYTE_DOMAIN=staging",
            rate_tail="launchplan leftover domain=staging",
            still_after_429="launchplan leftover staging; planted warranty-transfer unbound",
            grep="domain=staging|FLYTE_DOMAIN|eval/prod",
            grep_obs="register lockfile domain prod; ignore launchplan staging",
            plan_change="register domain=prod from lock; refuse staging",
            fix_path="evals/flyte_eval.py",
            fix_old="config.domain = os.getenv('FLYTE_DOMAIN','staging')",
            fix_new="config.domain = lockfile_domain('flyte.lock')",
            fix_obs="planted warranty-transfer 0.11 bound in prod",
            retry_obs="502 then retry; 5 pass 1 fail planted warranty-transfer 0.11",
            test="tests/test_flyte_domain_prod.py",
            test_body="assert domain is prod from lock; staging unused",
            test_obs="test_flyte_not_staging_domain",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed warranty-transfer",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed warranty-transfer",
            diff_obs=" evals/flyte_eval.py | 4+-\n tests/test_flyte_domain_prod.py | 12++\n",
            residual="Launchplan leftover still targets domain=staging.",
        ),
        _bad(
            slug="kfp-compiled-v1-yaml-i26p",
            domain="kfp-eval",
            kind="workflow",
            avoided="r308 earthly; r288 k8s backoff; r319 Aim hash",
            goal=(
                "Kubeflow leftover compiled pipeline.yaml from kfp SDK v1 so v2 components "
                "including planted sla-credit never load. Recompile with v2; fail if the yaml "
                "apiVersion is still v1."
            ),
            plan="Dump compiled yaml, recompile v2, prove planted sla-credit locally.",
            outcome=(
                "Local yaml is v2. Planted sla-credit runs locally. Handoff: the cluster leftover "
                "still uploads the v1 compiled yaml."
            ),
            ticket=(
                "Title: KFP leftover compiled pipeline.yaml v1. planted sla-credit dropped."
            ),
            src="evals/pipeline.yaml",
            src_obs="apiVersion: argoproj.io/v1alpha1  # leftover kfp v1 compile",
            run="evals/kfp_eval.py",
            fail_obs="v1 leftover. planted sla-credit component absent",
            inspect="evals/pipeline.yaml",
            inspect_obs="v1 leftover. no v2 component sla-credit",
            first_path="evals/kfp_eval.py",
            first_old="compiler.Compiler().compile(pipeline, 'evals/pipeline.yaml')",
            first_new="compiler.Compiler().compile(pipeline, 'evals/pipeline.yaml')  # v2",
            first_obs="comment only. cluster leftover still v1 yaml",
            rate_tail="cluster leftover uploads v1 yaml",
            still_after_429="cluster leftover v1; planted sla-credit dropped",
            grep="apiVersion|kfp==1|sla-credit",
            grep_obs="cannot replace cluster upload from this ticket",
            plan_change="local v2 compile; document cluster leftover v1 yaml",
            fix_path="evals/kfp_eval.py",
            fix_old="compiler.Compiler().compile(pipeline, 'evals/pipeline.yaml')  # v2",
            fix_new="kfp.dsl.compiler.Compiler().compile(pipeline_v2, 'evals/pipeline.yaml')",
            fix_obs="local planted runs. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover v1 yaml. Partial",
            test="tests/test_kfp_compiled_v2.py",
            test_body="xfail cluster leftover v1 yaml; local v2 compile",
            test_obs="cluster leftover v1 yaml. Partial",
            suite_obs="local v2 yaml. cluster leftover v1. Partial.",
            gate_obs="local v2 yaml. cluster leftover v1. Partial.",
            diff_obs=" evals/kfp_eval.py | 2+-\n HANDOFF kfp v1 yaml\n",
            residual="Cluster leftover still uploads the v1 compiled yaml. Partial.",
        ),
    )
)

# r326 cloud leftover
PAIRS.append(
    (
        _ok(
            slug="sagemaker-nameprefix-old-j27q",
            domain="sagemaker-eval",
            kind="cloud",
            avoided="r280 vertex pred vs explain; r268 docker layer; r314 tekton last-write",
            goal=(
                "SageMaker leftover ProcessingJob name prefix EvalJob so DescribeProcessingJob "
                "returns yesterday's completed job and planted proration-skip never attaches. "
                "Include git sha in the job name; fail if the described name lacks this sha."
            ),
            plan="Dump job name prefix, pin sha, prove planted proration-skip attaches.",
            outcome=(
                "Job name includes sha. Planted proration-skip 0.14 attached. Residual: a "
                "pipeline leftover still uses name prefix EvalJob."
            ),
            ticket=(
                "Title: SageMaker leftover name prefix EvalJob. planted proration-skip missing."
            ),
            src="evals/sagemaker_proc.py",
            src_obs="job_name='EvalJob'  # leftover stable prefix",
            run="evals/sagemaker_proc.py",
            fail_obs="Describe leftover yesterday EvalJob. planted proration-skip absent",
            inspect="evals/sagemaker_proc.py",
            inspect_obs="stable prefix leftover. no sha in job name",
            first_path="evals/sagemaker_proc.py",
            first_old="job_name='EvalJob'",
            first_new="job_name='EvalJob-' + date.today().isoformat()",
            first_obs="date local. pipeline leftover still prefix EvalJob",
            rate_tail="pipeline leftover name prefix EvalJob",
            still_after_429="pipeline leftover EvalJob; planted proration-skip absent",
            grep="EvalJob|job_name|git_sha",
            grep_obs="override pipeline leftover; always EvalJob-<sha>",
            plan_change="job name EvalJob-<sha>; refuse bare EvalJob",
            fix_path="evals/sagemaker_proc.py",
            fix_old="job_name='EvalJob-' + date.today().isoformat()",
            fix_new="job_name=f'EvalJob-{git_sha}'",
            fix_obs="planted proration-skip 0.14 on sha job",
            retry_obs="502 then retry; 5 pass 1 fail planted proration-skip 0.14",
            test="tests/test_sagemaker_job_sha.py",
            test_body="assert job name includes sha; bare EvalJob unused",
            test_obs="test_sagemaker_name_not_bare_prefix",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed proration-skip",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed proration-skip",
            diff_obs=" evals/sagemaker_proc.py | 6+-\n tests/test_sagemaker_job_sha.py | 12++\n",
            residual="Pipeline leftover still uses name prefix EvalJob.",
        ),
        _bad(
            slug="databricks-widget-sha-k28r",
            domain="dbx-eval",
            kind="cloud",
            avoided="r280 vertex pred; r319 Aim hash; r266 prom last-write",
            goal=(
                "Databricks leftover widget EVAL_SHA=yesterday so the notebook eval loads old "
                "goldens and planted hold-expire never runs. Bind EVAL_SHA to spark.conf git sha."
            ),
            plan="Dump widget, bind spark conf sha, prove planted hold-expire locally.",
            outcome=(
                "Local widget overwritten from spark.conf git sha. Planted hold-expire locally. "
                "Handoff: the job leftover still passes EVAL_SHA=yesterday."
            ),
            ticket=(
                "Title: Databricks leftover widget EVAL_SHA=yesterday. planted hold-expire missing."
            ),
            src="evals/dbx_eval.py",
            src_obs="sha = dbutils.widgets.get('EVAL_SHA')  # leftover default yesterday",
            run="evals/dbx_eval.py",
            fail_obs="widget leftover yesterday. planted hold-expire absent",
            inspect="evals/dbx_eval.py",
            inspect_obs="widget leftover. no spark.conf git sha",
            first_path="evals/dbx_eval.py",
            first_old="sha = dbutils.widgets.get('EVAL_SHA')",
            first_new="sha = dbutils.widgets.get('EVAL_SHA') or 'dev'",
            first_obs="or-dev leftover. job still passes yesterday",
            rate_tail="job leftover --widget EVAL_SHA=yesterday",
            still_after_429="job leftover widget; planted hold-expire absent",
            grep="EVAL_SHA|dbutils.widgets|spark.conf",
            grep_obs="cannot change job widget from this ticket",
            plan_change="local spark.conf git sha; document job leftover widget",
            fix_path="evals/dbx_eval.py",
            fix_old="sha = dbutils.widgets.get('EVAL_SHA') or 'dev'",
            fix_new="sha = spark.conf.get('git.sha')",
            fix_obs="local planted present. job leftover HANDOFF",
            retry_obs="502 unused. job leftover EVAL_SHA. Partial",
            test="tests/test_dbx_widget_sha.py",
            test_body="xfail job leftover widget; local spark.conf git sha",
            test_obs="job leftover widget. Partial",
            suite_obs="local spark.conf sha. job leftover widget. Partial.",
            gate_obs="local spark.conf sha. job leftover widget. Partial.",
            diff_obs=" evals/dbx_eval.py | 4+-\n HANDOFF dbx widget\n",
            residual="Job leftover still passes EVAL_SHA=yesterday. Partial.",
        ),
    )
)

# r327 data-quality leftover
PAIRS.append(
    (
        _ok(
            slug="gx-checkpoint-omit-l29s",
            domain="gx-eval",
            kind="quality",
            avoided="r317 evidently col map; r317 giskard train split; r264 pandas NA",
            goal=(
                "Great Expectations leftover checkpoint suite omits the planted flash-sale "
                "expectation so the eval gate never sees the fail. Add the expectation; fail "
                "if the planted id is missing from the suite."
            ),
            plan="Dump checkpoint suite, add planted expectation, prove flash-sale fail.",
            outcome=(
                "Suite includes flash-sale. Planted 0.13 fail-closed. Residual: a cloud leftover "
                "checkpoint still runs the old suite name."
            ),
            ticket=(
                "Title: GX leftover checkpoint eval-suite-v1. planted flash-sale expectation "
                "omitted."
            ),
            src="evals/gx_checkpoint.yml",
            src_obs="validations:\n- suite: eval-suite-v1  # leftover pre-flash-sale",
            run="evals/gx_eval.py",
            fail_obs="suite leftover no flash-sale. gate 1.0",
            inspect="evals/gx_checkpoint.yml",
            inspect_obs="eval-suite-v1 leftover. flash-sale only in eval-suite-v2",
            first_path="evals/gx_checkpoint.yml",
            first_old="suite: eval-suite-v1",
            first_new="suite: eval-suite-v2",
            first_obs="v2 local. cloud leftover still runs v1 name",
            rate_tail="cloud leftover checkpoint name v1",
            still_after_429="cloud leftover v1; planted flash-sale omitted",
            grep="eval-suite-v1|flash-sale|checkpoint",
            grep_obs="run v2; fail if planted expectation missing",
            plan_change="require planted expectation in suite; refuse v1",
            fix_path="evals/gx_eval.py",
            fix_old="checkpoint.run()",
            fix_new="result = checkpoint.run(); require_expectation(result, 'flash-sale')",
            fix_obs="planted flash-sale 0.13 in suite. v1 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-sale 0.13",
            test="tests/test_gx_suite_includes_planted.py",
            test_body="assert suite has flash-sale; v1 unused",
            test_obs="test_gx_checkpoint_not_v1_omit",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-sale",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-sale",
            diff_obs=" evals/gx_checkpoint.yml | 2+-\n evals/gx_eval.py | 4+-\n tests/test_gx_suite_includes_planted.py | 12++\n",
            residual="Cloud leftover checkpoint still runs the old suite name.",
        ),
        _bad(
            slug="soda-rowcount-only-m30t",
            domain="soda-eval",
            kind="quality",
            avoided="r317 evidently map; r264 pandas NA; r319 Aim hash",
            goal=(
                "Soda leftover checks.yml only asserts row_count so planted price-match score "
                "0.19 never fails. Add a min_score check; fail-closed on score."
            ),
            plan="Dump soda checks, add min_score, prove planted price-match locally.",
            outcome=(
                "Local checks include min_score. Planted price-match 0.19 locally. Handoff: the "
                "warehouse leftover still runs the row_count-only checks.yml."
            ),
            ticket=(
                "Title: Soda leftover checks row_count only. planted price-match 0.19 ignored."
            ),
            src="evals/checks.yml",
            src_obs="checks for eval_scores:\n  - row_count > 0  # leftover",
            run="evals/soda_eval.py",
            fail_obs="row_count leftover pass. planted price-match 0.19 unused",
            inspect="evals/checks.yml",
            inspect_obs="no min_score leftover. only row_count",
            first_path="evals/checks.yml",
            first_old="- row_count > 0",
            first_new="- row_count > 0\n  - missing_count(score) = 0",
            first_obs="missing_count local. warehouse leftover still row_count only",
            rate_tail="warehouse leftover checks.yml row_count",
            still_after_429="warehouse leftover; planted price-match ignored",
            grep="min_score|row_count|checks.yml",
            grep_obs="cannot replace warehouse checks from this ticket",
            plan_change="local min_score check; document warehouse leftover row_count",
            fix_path="evals/checks.yml",
            fix_old="- missing_count(score) = 0",
            fix_new="- min(score) >= 0.7",
            fix_obs="local planted 0.19. warehouse leftover HANDOFF",
            retry_obs="502 unused. warehouse leftover row_count. Partial",
            test="tests/test_soda_min_score.py",
            test_body="xfail warehouse leftover row_count; local min_score",
            test_obs="warehouse leftover row_count. Partial",
            suite_obs="local min_score. warehouse leftover row_count. Partial.",
            gate_obs="local min_score. warehouse leftover row_count. Partial.",
            diff_obs=" evals/checks.yml | 4+-\n HANDOFF soda warehouse\n",
            residual="Warehouse leftover still runs row_count-only checks.yml. Partial.",
        ),
    )
)

# r328 profile leftover
PAIRS.append(
    (
        _ok(
            slug="whylogs-profile-merge-n31u",
            domain="whylogs-eval",
            kind="profile",
            avoided="r317 evidently map; r264 pandas NA; r319 ClearML uri",
            goal=(
                "whylogs leftover DatasetProfile merge drops new planted rain-check rows so "
                "drift stats stay 1.0. Merge with merge_readonly=False and fail if planted id "
                "is absent from the profile view."
            ),
            plan="Dump profile merge, keep new rows, prove planted rain-check is visible.",
            outcome=(
                "Merge keeps new rows. Planted rain-check 0.16 visible. Residual: a cron leftover "
                "still merges with the yesterday profile first."
            ),
            ticket=(
                "Title: whylogs leftover merge drops new rows. planted rain-check absent; 1.0."
            ),
            src="evals/whylogs_eval.py",
            src_obs="view = yesterday.merge(today)  # leftover yesterday-first drops new ids",
            run="evals/whylogs_eval.py",
            fail_obs="merge leftover no rain-check id. drift 1.0",
            inspect="evals/whylogs_eval.py",
            inspect_obs="yesterday-first leftover. new ids dropped on key clash",
            first_path="evals/whylogs_eval.py",
            first_old="view = yesterday.merge(today)",
            first_new="view = today.merge(yesterday)",
            first_obs="order swap leftover still drops on clash",
            rate_tail="clash leftover still drops planted rain-check",
            still_after_429="merge leftover; planted rain-check absent",
            grep="merge\\(|planted|profile view",
            grep_obs="merge keeping today ids; require planted id in view",
            plan_change="today-authoritative merge; fail if planted id missing",
            fix_path="evals/whylogs_eval.py",
            fix_old="view = today.merge(yesterday)",
            fix_new="view = today; require_id(view, 'rain-check')",
            fix_obs="planted rain-check 0.16 in view. yesterday unused for ids",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-check 0.16",
            test="tests/test_whylogs_keeps_planted.py",
            test_body="assert planted id in profile view after merge",
            test_obs="test_whylogs_merge_not_drop_new",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-check",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-check",
            diff_obs=" evals/whylogs_eval.py | 6+-\n tests/test_whylogs_keeps_planted.py | 12++\n",
            residual="Cron leftover still merges with the yesterday profile first.",
        ),
        _bad(
            slug="nannyml-ref-stale-o32v",
            domain="nannyml-eval",
            kind="profile",
            avoided="r317 giskard train; r2 dataset-split; r319 Aim hash",
            goal=(
                "NannyML leftover reference dataset is last month so planted waitlist-skip "
                "looks in-distribution. Refresh reference to this SHA's goldens."
            ),
            plan="Dump reference path, pin SHA goldens, prove planted waitlist-skip locally.",
            outcome=(
                "Local reference is this SHA goldens. Planted waitlist-skip flagged locally. "
                "Handoff: the job leftover still points at last-month parquet."
            ),
            ticket=(
                "Title: NannyML leftover reference last-month.parquet. planted waitlist-skip "
                "in-distribution."
            ),
            src="evals/nannyml_eval.py",
            src_obs="reference = pd.read_parquet('ref/last-month.parquet')  # leftover",
            run="evals/nannyml_eval.py",
            fail_obs="reference leftover last month. planted waitlist-skip CBPE 1.0",
            inspect="evals/nannyml_eval.py",
            inspect_obs="stable parquet leftover. no sha goldens",
            first_path="evals/nannyml_eval.py",
            first_old="ref/last-month.parquet",
            first_new="ref/this-week.parquet",
            first_obs="this-week local. job leftover still last-month",
            rate_tail="job leftover reference last-month.parquet",
            still_after_429="job leftover ref; planted waitlist-skip 1.0",
            grep="last-month|reference|goldens",
            grep_obs="cannot change job reference from this ticket",
            plan_change="local SHA goldens as reference; document job leftover parquet",
            fix_path="evals/nannyml_eval.py",
            fix_old="ref/this-week.parquet",
            fix_new="goldens/waitlist.jsonl",
            fix_obs="local planted flagged. job leftover HANDOFF",
            retry_obs="502 unused. job leftover last-month ref. Partial",
            test="tests/test_nannyml_ref_sha.py",
            test_body="xfail job leftover last-month; local SHA goldens",
            test_obs="job leftover last-month ref. Partial",
            suite_obs="local SHA goldens. job leftover last-month. Partial.",
            gate_obs="local SHA goldens. job leftover last-month. Partial.",
            diff_obs=" evals/nannyml_eval.py | 2+-\n HANDOFF nannyml ref\n",
            residual="Job leftover still points at last-month parquet. Partial.",
        ),
    )
)

# r329 detector leftover
PAIRS.append(
    (
        _ok(
            slug="alibi-threshold-stale-p33w",
            domain="alibi-eval",
            kind="detector",
            avoided="r274 redteam pii; r280 azure safety; r310 hallu min-score",
            goal=(
                "Alibi leftover detector threshold.pkl from last quarter so planted "
                "seat-reassign drift is below the old cutoff. Refit threshold on this SHA "
                "goldens; fail-closed on new drift."
            ),
            plan="Dump threshold.pkl, refit, prove planted seat-reassign fail.",
            outcome=(
                "Threshold refit on SHA goldens. Planted seat-reassign 0.18 fail-closed. "
                "Residual: a serving leftover still loads last-quarter threshold.pkl."
            ),
            ticket=(
                "Title: Alibi leftover threshold.pkl last quarter. planted seat-reassign "
                "in-distribution."
            ),
            src="evals/alibi_detect.py",
            src_obs="threshold = joblib.load('threshold.pkl')  # leftover last quarter",
            run="evals/alibi_detect.py",
            fail_obs="threshold leftover 0.05. planted seat-reassign 0.04 in-dist 1.0",
            inspect="evals/alibi_detect.py",
            inspect_obs="stable pkl leftover. no refit on goldens",
            first_path="evals/alibi_detect.py",
            first_old="joblib.load('threshold.pkl')",
            first_new="joblib.load('threshold-v2.pkl')",
            first_obs="v2 local. serving leftover still last-quarter pkl",
            rate_tail="serving leftover threshold.pkl last quarter",
            still_after_429="serving leftover pkl; planted seat-reassign 1.0",
            grep="threshold.pkl|refit|goldens",
            grep_obs="refit on SHA goldens; ignore serving leftover pkl",
            plan_change="refit threshold on SHA goldens; refuse last-quarter pkl",
            fix_path="evals/alibi_detect.py",
            fix_old="joblib.load('threshold-v2.pkl')",
            fix_new="threshold = refit(goldens_for(git_sha))",
            fix_obs="planted seat-reassign 0.18 above new threshold",
            retry_obs="502 then retry; 5 pass 1 fail planted seat-reassign 0.18",
            test="tests/test_alibi_threshold_refit.py",
            test_body="assert threshold refit on sha goldens; old pkl unused",
            test_obs="test_alibi_not_last_quarter_threshold",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed seat-reassign",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed seat-reassign",
            diff_obs=" evals/alibi_detect.py | 6+-\n tests/test_alibi_threshold_refit.py | 12++\n",
            residual="Serving leftover still loads last-quarter threshold.pkl.",
        ),
        _bad(
            slug="deepchecks-skip-llm-q34x",
            domain="deepchecks-eval",
            kind="detector",
            avoided="r317 giskard train; r274 toxicity cyrillic; r319 Aim hash",
            goal=(
                "Deepchecks leftover suite skip_llm=True so planted overbook-deny never runs. "
                "Enable the LLM check locally; fail if skip_llm is still set."
            ),
            plan="Dump suite flags, enable LLM check, prove planted overbook-deny locally.",
            outcome=(
                "Local suite skip_llm=False. Planted overbook-deny runs locally. Handoff: the "
                "nightly leftover still skip_llm for speed."
            ),
            ticket=(
                "Title: Deepchecks leftover skip_llm=True. planted overbook-deny never scored."
            ),
            src="evals/deepchecks_suite.py",
            src_obs="suite.run(skip_llm=True)  # leftover 'llm checks slow'",
            run="evals/deepchecks_suite.py",
            fail_obs="skip_llm leftover. planted overbook-deny unused",
            inspect="evals/deepchecks_suite.py",
            inspect_obs="skip_llm leftover True. LLM eval not in report",
            first_path="evals/deepchecks_suite.py",
            first_old="skip_llm=True",
            first_new="skip_llm=os.getenv('SKIP_LLM','True')=='True'",
            first_obs="env leftover SKIP_LLM=True nightly",
            rate_tail="nightly leftover SKIP_LLM=True",
            still_after_429="nightly leftover skip; planted overbook-deny unused",
            grep="skip_llm|SKIP_LLM|overbook",
            grep_obs="cannot unset nightly env from this ticket",
            plan_change="local skip_llm False; document nightly leftover skip",
            fix_path="evals/deepchecks_suite.py",
            fix_old="skip_llm=os.getenv('SKIP_LLM','True')=='True'",
            fix_new="skip_llm=False",
            fix_obs="local planted runs. nightly leftover HANDOFF",
            retry_obs="502 unused. nightly leftover skip_llm. Partial",
            test="tests/test_deepchecks_llm_on.py",
            test_body="xfail nightly leftover skip_llm; local False",
            test_obs="nightly leftover skip_llm. Partial",
            suite_obs="local LLM on. nightly leftover skip. Partial.",
            gate_obs="local LLM on. nightly leftover skip. Partial.",
            diff_obs=" evals/deepchecks_suite.py | 2+-\n HANDOFF nightly skip_llm\n",
            residual="Nightly leftover still skip_llm for speed. Partial.",
        ),
    )
)

# r330 prompt-ops leftover
PAIRS.append(
    (
        _ok(
            slug="promptlayer-tag-filter-prod-r35y",
            domain="promptlayer-eval",
            kind="promptops",
            avoided="r261 anthropic prompt cache; r315 helicone 2k; r298 djlint jinja",
            goal=(
                "PromptLayer leftover GetPrompt filter tags=['prod'] so rubric v3 bundle-split "
                "labeled eval never loads. Query tags=['eval']; fail if the returned prompt is "
                "still prod-only."
            ),
            plan="Dump tag filter, pin eval tag, prove planted bundle-split loads.",
            outcome=(
                "GetPrompt uses tags=['eval']. Planted bundle-split 0.12. Residual: a proxy "
                "leftover still filters tags=['prod']."
            ),
            ticket=(
                "Title: PromptLayer leftover tags=['prod']. v3 bundle-split labeled eval missing."
            ),
            src="evals/promptlayer_eval.py",
            src_obs="pl.get_prompt(name, tags=['prod'])  # leftover prod-only",
            run="evals/promptlayer_eval.py",
            fail_obs="prod leftover. planted bundle-split eval tag unused",
            inspect="evals/promptlayer_eval.py",
            inspect_obs="tags leftover prod. eval tag unused",
            first_path="evals/promptlayer_eval.py",
            first_old="tags=['prod']",
            first_new="tags=[os.getenv('PL_TAG','prod')]",
            first_obs="env leftover PL_TAG=prod",
            rate_tail="proxy leftover still tags prod",
            still_after_429="prod leftover; planted bundle-split unused",
            grep="tags=\\['prod'\\]|PL_TAG|bundle-split",
            grep_obs="query tags eval; refuse prod-only filter",
            plan_change="GetPrompt tags=['eval']; refuse leftover prod filter",
            fix_path="evals/promptlayer_eval.py",
            fix_old="tags=[os.getenv('PL_TAG','prod')]",
            fix_new="tags=['eval']",
            fix_obs="planted bundle-split 0.12 loaded",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-split 0.12",
            test="tests/test_promptlayer_eval_tag.py",
            test_body="assert get_prompt tags include eval; prod unused",
            test_obs="test_promptlayer_not_prod_tag",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-split",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-split",
            diff_obs=" evals/promptlayer_eval.py | 4+-\n tests/test_promptlayer_eval_tag.py | 12++\n",
            residual="Proxy leftover still filters tags=['prod'].",
        ),
        _bad(
            slug="humanloop-eval-v1-s36z",
            domain="humanloop-eval",
            kind="promptops",
            avoided="r261 anthropic cache; r315 portkey simple; r319 Aim hash",
            goal=(
                "Humanloop leftover evaluator pinned to v1 after the v2 rubric so planted "
                "reservation-leak scores 1.0. Pin evaluator v2 locally."
            ),
            plan="Dump evaluator version, pin v2, prove planted reservation-leak locally.",
            outcome=(
                "Local evaluator v2. Planted reservation-leak 0.17 locally. Handoff: the project "
                "leftover still defaults evaluator=v1."
            ),
            ticket=(
                "Title: Humanloop leftover evaluator v1. planted reservation-leak 1.0 under v2 rubric."
            ),
            src="evals/humanloop_eval.py",
            src_obs="evaluator='eval/v1'  # leftover default",
            run="evals/humanloop_eval.py",
            fail_obs="v1 leftover. planted reservation-leak 1.0",
            inspect="evals/humanloop_eval.py",
            inspect_obs="v1 leftover. v2 rubric unused",
            first_path="evals/humanloop_eval.py",
            first_old="evaluator='eval/v1'",
            first_new="evaluator=os.getenv('HL_EVAL','eval/v1')",
            first_obs="env leftover HL_EVAL=eval/v1",
            rate_tail="project leftover default evaluator v1",
            still_after_429="project leftover v1; planted reservation-leak 1.0",
            grep="eval/v1|eval/v2|HL_EVAL",
            grep_obs="cannot change project default from this ticket",
            plan_change="local evaluator v2; document project leftover v1",
            fix_path="evals/humanloop_eval.py",
            fix_old="evaluator=os.getenv('HL_EVAL','eval/v1')",
            fix_new="evaluator='eval/v2'",
            fix_obs="local planted 0.17. project leftover HANDOFF",
            retry_obs="502 unused. project leftover evaluator v1. Partial",
            test="tests/test_humanloop_eval_v2.py",
            test_body="xfail project leftover v1; local evaluator v2",
            test_obs="project leftover v1. Partial",
            suite_obs="local v2. project leftover v1. Partial.",
            gate_obs="local v2. project leftover v1. Partial.",
            diff_obs=" evals/humanloop_eval.py | 2+-\n HANDOFF humanloop v1\n",
            residual="Project leftover still defaults evaluator=v1. Partial.",
        ),
    )
)

# r331 product leftover
PAIRS.append(
    (
        _ok(
            slug="opik-project-env-old-t37a",
            domain="opik-eval",
            kind="product",
            avoided="r318 comet resume; r316 phoenix omit ctx; r256 wandb sanitize",
            goal=(
                "Opik leftover OPIK_PROJECT=eval-old so traces land in the retired project and "
                "planted raincheck-deny never appears in the gate project. Pin project from "
                "lockfile; fail if env still names eval-old."
            ),
            plan="Dump OPIK_PROJECT, pin lock project, prove planted raincheck-deny lands.",
            outcome=(
                "Project is lockfile id. Planted raincheck-deny 0.14 fail-closed. Residual: a "
                "UI leftover still exports OPIK_PROJECT=eval-old."
            ),
            ticket=(
                "Title: Opik leftover OPIK_PROJECT=eval-old. planted raincheck-deny missing."
            ),
            src="evals/opik_eval.py",
            src_obs="project = os.getenv('OPIK_PROJECT','eval-old')  # leftover retired project",
            run="evals/opik_eval.py",
            fail_obs="project leftover eval-old. planted raincheck-deny absent in gate",
            inspect="evals/opik_eval.py",
            inspect_obs="eval-old leftover. lockfile project unused",
            first_path="evals/opik_eval.py",
            first_old="os.getenv('OPIK_PROJECT','eval-old')",
            first_new="os.getenv('OPIK_PROJECT','eval-gate')",
            first_obs="default gate. UI leftover still exports eval-old",
            rate_tail="UI leftover OPIK_PROJECT=eval-old",
            still_after_429="env leftover eval-old; planted raincheck-deny absent",
            grep="OPIK_PROJECT|eval-old|opik.lock",
            grep_obs="pin lockfile project; ignore leftover env",
            plan_change="project from opik.lock; refuse eval-old env",
            fix_path="evals/opik_eval.py",
            fix_old="os.getenv('OPIK_PROJECT','eval-gate')",
            fix_new="lockfile_project('opik.lock')",
            fix_obs="planted raincheck-deny 0.14 in lock project",
            retry_obs="502 then retry; 5 pass 1 fail planted raincheck-deny 0.14",
            test="tests/test_opik_project_lock.py",
            test_body="assert project from lock; eval-old unused",
            test_obs="test_opik_not_eval_old_project",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed raincheck-deny",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed raincheck-deny",
            diff_obs=" evals/opik_eval.py | 6+-\n tests/test_opik_project_lock.py | 12++\n",
            residual="UI leftover still exports OPIK_PROJECT=eval-old.",
        ),
        _bad(
            slug="weave-score-as-str-u38b",
            domain="weave-eval",
            kind="product",
            avoided="r256 wandb sanitize; r315 helicone; r319 Aim hash",
            goal=(
                "Weave leftover Table.from_pandas infers score as string so planted gift-split "
                "0.19 is excluded from numeric mean. Cast score to float; fail if the column "
                "dtype is not float."
            ),
            plan="Dump table dtypes, cast score, prove planted gift-split locally.",
            outcome=(
                "Local score column is float. Planted gift-split 0.19 locally. Handoff: the "
                "hosted leftover still infers string scores."
            ),
            ticket=(
                "Title: Weave leftover score dtype string. planted gift-split dropped from mean."
            ),
            src="evals/weave_eval.py",
            src_obs="table = weave.Table.from_pandas(df)  # leftover infers score as str",
            run="evals/weave_eval.py",
            fail_obs="score leftover object dtype. planted gift-split excluded from mean",
            inspect="evals/weave_eval.py",
            inspect_obs="no astype(float) leftover. mean skips strings",
            first_path="evals/weave_eval.py",
            first_old="table = weave.Table.from_pandas(df)",
            first_new="table = weave.Table.from_pandas(df.astype({'score': 'string'}))",
            first_obs="still string leftover. hosted infers object",
            rate_tail="hosted leftover infers score as str",
            still_after_429="hosted leftover str score; planted gift-split dropped",
            grep="from_pandas|score dtype|astype",
            grep_obs="cannot change hosted infer from this ticket",
            plan_change="local astype float; document hosted leftover str score",
            fix_path="evals/weave_eval.py",
            fix_old="table = weave.Table.from_pandas(df.astype({'score': 'string'}))",
            fix_new="table = weave.Table.from_pandas(df.astype({'score': 'float64'}))",
            fix_obs="local planted 0.19. hosted leftover HANDOFF",
            retry_obs="502 unused. hosted leftover str score. Partial",
            test="tests/test_weave_score_dtype.py",
            test_body="xfail hosted leftover str score; local float64",
            test_obs="hosted leftover str score. Partial",
            suite_obs="local float score. hosted leftover str. Partial.",
            gate_obs="local float score. hosted leftover str. Partial.",
            diff_obs=" evals/weave_eval.py | 4+-\n HANDOFF weave dtype\n",
            residual="Hosted leftover still infers string scores. Partial.",
        ),
    )
)

# r332 notebook leftover
PAIRS.append(
    (
        _ok(
            slug="papermill-kernel-mismatch-v39c",
            domain="papermill-eval",
            kind="notebook",
            avoided="r271 makefile stale; r322 jupytext pair; r308 jupyter kernel",
            goal=(
                "Papermill leftover kernel_name=python3 while the notebook metadata is "
                "python3.11 so cells with planted dual-hold never execute. Pin kernel_name to "
                "the metadata kernel; fail if papermill skips cells."
            ),
            plan="Dump kernel_name, pin metadata kernel, prove planted dual-hold executes.",
            outcome=(
                "kernel_name matches notebook metadata. Planted dual-hold 0.13 fail-closed. "
                "Residual: a job leftover still passes -k python3."
            ),
            ticket=(
                "Title: papermill leftover kernel_name=python3. planted dual-hold cells skipped."
            ),
            src="evals/notebook_eval.py",
            src_obs="pm.execute_notebook(nb, out, kernel_name='python3')  # leftover",
            run="evals/notebook_eval.py",
            fail_obs="kernel leftover python3 vs metadata python3.11. planted dual-hold skipped",
            inspect="evals/gate.ipynb",
            inspect_obs="metadata kernelspec leftover python3.11. execute used python3",
            first_path="evals/notebook_eval.py",
            first_old="kernel_name='python3'",
            first_new="kernel_name=os.getenv('KERNEL','python3')",
            first_obs="env leftover KERNEL=python3",
            rate_tail="job leftover -k python3",
            still_after_429="job leftover python3; planted dual-hold skipped",
            grep="kernel_name|kernelspec|python3.11",
            grep_obs="use notebook metadata kernel; ignore -k leftover",
            plan_change="kernel from notebook metadata; refuse leftover python3",
            fix_path="evals/notebook_eval.py",
            fix_old="kernel_name=os.getenv('KERNEL','python3')",
            fix_new="kernel_name=nb.metadata.kernelspec.name",
            fix_obs="planted dual-hold 0.13 executed",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold 0.13",
            test="tests/test_papermill_kernel.py",
            test_body="assert kernel_name is notebook metadata; python3 unused",
            test_obs="test_papermill_not_python3_kernel",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold",
            diff_obs=" evals/notebook_eval.py | 4+-\n tests/test_papermill_kernel.py | 12++\n",
            residual="Job leftover still passes -k python3.",
        ),
        _bad(
            slug="jupytext-pair-stale-w40d",
            domain="jupytext-eval",
            kind="notebook",
            avoided="r271 makefile stale; r290 black wrap; r319 Aim hash",
            goal=(
                "Jupytext leftover paired evals/gate.py is older than evals/gate.ipynb so planted "
                "sku-swap in the notebook never syncs to the pytest entry. Sync --to py; fail "
                "if pair mtime lags."
            ),
            plan="Dump pair mtimes, sync, prove planted sku-swap locally.",
            outcome=(
                "Local pair synced. Planted sku-swap present in py locally. Handoff: CI leftover "
                "still runs the stale .py without jupytext sync."
            ),
            ticket=(
                "Title: jupytext leftover pair evals/gate.py stale. planted sku-swap only in ipynb."
            ),
            src="evals/gate.ipynb",
            src_obs="# planted sku-swap cell\n# leftover pair evals/gate.py mtime yesterday",
            run="evals/gate.py",
            fail_obs="py leftover no sku-swap. ipynb has it unused",
            inspect="evals/gate.py",
            inspect_obs="stale pair leftover. no planted id",
            first_path="evals/gate.py",
            first_old="# auto from ipynb",
            first_new="# auto from ipynb\n# TODO sync",
            first_obs="comment only. CI leftover still pytest evals/gate.py",
            rate_tail="CI leftover no jupytext sync",
            still_after_429="CI leftover stale py; planted sku-swap unused",
            grep="jupytext|gate.ipynb|gate.py",
            grep_obs="cannot add CI sync from this ticket",
            plan_change="local jupytext --to py; document CI leftover stale pair",
            fix_path="evals/gate.py",
            fix_old="# TODO sync",
            fix_new="# synced local; planted sku-swap present",
            fix_obs="local planted present. CI leftover HANDOFF",
            retry_obs="502 unused. CI leftover stale pair. Partial",
            test="tests/test_jupytext_pair_sync.py",
            test_body="xfail CI leftover stale py; local pair synced",
            test_obs="CI leftover stale pair. Partial",
            suite_obs="local sync. CI leftover stale py. Partial.",
            gate_obs="local sync. CI leftover stale py. Partial.",
            diff_obs=" evals/gate.py | 4+-\n HANDOFF jupytext CI\n",
            residual="CI leftover still runs the stale .py without jupytext sync. Partial.",
        ),
    )
)

# r333 lock leftover
PAIRS.append(
    (
        _ok(
            slug="uv-tool-eval-pin-x41e",
            domain="uv-lock-eval",
            kind="lock",
            avoided="r289 mypy stub; r270 metrics shadow; r319 ClearML uri",
            goal=(
                "uv leftover tool pin deepeval==0.21 in uv.lock so planted membership-window "
                "uses the old skip-missing-score path. Bump the lock and fail if 0.21 is first "
                "on PATH."
            ),
            plan="Dump uv.lock, bump deepeval, prove planted membership-window fail.",
            outcome=(
                "uv.lock pins deepeval 2.x. Planted membership-window 0.15 fail-closed. Residual: "
                "a laptop leftover uv tool dir still has 0.21."
            ),
            ticket=(
                "Title: uv leftover deepeval==0.21. planted membership-window skip-missing 1.0."
            ),
            src="uv.lock",
            src_obs="name = \"deepeval\"\nversion = \"0.21.0\"  # leftover",
            run="evals/membership_window.py",
            fail_obs="0.21 leftover skip-missing 1.0. planted membership-window pass",
            inspect="uv.lock",
            inspect_obs="deepeval 0.21 leftover. no 2.x",
            first_path="uv.lock",
            first_old='version = "0.21.0"',
            first_new='version = "2.5.0"',
            first_obs="lock 2.5. leftover ~/.local/share/uv/tools still 0.21",
            rate_tail="uv tools leftover 0.21 first on PATH",
            still_after_429="uv tools leftover; planted membership-window 1.0",
            grep="deepeval==0.21|uv tool|PATH",
            grep_obs="uv tool uninstall 0.21; PATH repo .venv first",
            plan_change="lock 2.x; PATH .venv; refuse 0.21 shim",
            fix_path="evals/membership_window.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__.split('.')[0] != '0'",
            fix_obs="planted membership-window 0.15. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-window 0.15",
            test="tests/test_uv_deepeval_not_021.py",
            test_body="assert deepeval major != 0; uv.lock 2.x",
            test_obs="test_uv_lock_not_deepeval_021",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-window",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-window",
            diff_obs=" uv.lock | 4+-\n evals/membership_window.py | 4+-\n tests/test_uv_deepeval_not_021.py | 12++\n",
            residual="Laptop leftover uv tool dir still has 0.21.",
        ),
        _bad(
            slug="piptools-eval-lock-y42f",
            domain="piptools-eval",
            kind="lock",
            avoided="r289 mypy stub; r270 sitecustomize; r319 Aim hash",
            goal=(
                "pip-tools leftover requirements.txt pins deepeval==0.21 so planted "
                "after-hours-hold skip-missing is True. Compile a new lock locally."
            ),
            plan="Dump requirements, bump, prove planted after-hours-hold locally.",
            outcome=(
                "Local requirements pin 2.x. Planted after-hours-hold locally. Handoff: the "
                "image leftover still pip installs the old requirements.txt."
            ),
            ticket=(
                "Title: pip-tools leftover deepeval==0.21. planted after-hours-hold skip-missing."
            ),
            src="requirements.txt",
            src_obs="deepeval==0.21.0  # leftover via pip-compile",
            run="evals/after_hours_hold.py",
            fail_obs="0.21 leftover skip-missing. planted after-hours-hold pass",
            inspect="requirements.txt",
            inspect_obs="0.21 leftover. no 2.x pin",
            first_path="requirements.txt",
            first_old="deepeval==0.21.0",
            first_new="deepeval==2.5.0",
            first_obs="txt 2.5. image leftover still old compile",
            rate_tail="image leftover pip install old requirements",
            still_after_429="image leftover 0.21; planted after-hours-hold pass",
            grep="deepeval==0.21|pip-compile|requirements.txt",
            grep_obs="cannot rebuild image from this ticket",
            plan_change="local 2.x pin; document image leftover requirements",
            fix_path="evals/after_hours_hold.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover 0.21. Partial",
            test="tests/test_piptools_deepeval_pin.py",
            test_body="xfail image leftover 0.21; local 2.x",
            test_obs="image leftover 0.21. Partial",
            suite_obs="local 2.x. image leftover 0.21. Partial.",
            gate_obs="local 2.x. image leftover 0.21. Partial.",
            diff_obs=" requirements.txt | 2+-\n HANDOFF image pip-tools\n",
            residual="Image leftover still pip installs the old requirements.txt. Partial.",
        ),
    )
)

# r334 storage leftover
PAIRS.append(
    (
        _ok(
            slug="minio-lifecycle-expire-z43g",
            domain="minio-eval",
            kind="storage",
            avoided="r305 nix gcroot; r326 sagemaker nameprefix; r268 docker layer",
            goal=(
                "MinIO leftover lifecycle ExpireCurrentVersion Days=1 deletes planted "
                "bundle-hold objects before the gate reads them. Raise the expire window "
                "past the gate SLA; fail if the object is missing at read time."
            ),
            plan="Dump lifecycle rule, raise expire, prove planted bundle-hold is present.",
            outcome=(
                "Expire window is 14 days. Planted bundle-hold 0.16 present at gate read. "
                "Residual: a bucket leftover policy still expires in 1 day."
            ),
            ticket=(
                "Title: MinIO leftover lifecycle expire 1 day. planted bundle-hold gone at gate."
            ),
            src="evals/minio_lifecycle.json",
            src_obs='"Expiration": {"Days": 1}  # leftover from scratch bucket',
            run="evals/minio_eval.py",
            fail_obs="object leftover expired. planted bundle-hold 404 at gate",
            inspect="evals/minio_lifecycle.json",
            inspect_obs="Days leftover 1. gate SLA is 6 hours but overnight expire",
            first_path="evals/minio_lifecycle.json",
            first_old='"Days": 1',
            first_new='"Days": 2',
            first_obs="2 local. bucket leftover policy still Days=1",
            rate_tail="bucket leftover lifecycle Days=1",
            still_after_429="lifecycle leftover expire; planted bundle-hold 404",
            grep="Expiration|Days|bundle-hold",
            grep_obs="set expire 14d; fail if object missing at gate",
            plan_change="expire 14 days; refuse leftover 1-day rule",
            fix_path="evals/minio_lifecycle.json",
            fix_old='"Days": 2',
            fix_new='"Days": 14',
            fix_obs="planted bundle-hold 0.16 present at gate",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-hold 0.16",
            test="tests/test_minio_lifecycle_expire.py",
            test_body="assert expire days >= 14; 1-day rule unused",
            test_obs="test_minio_not_one_day_expire",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold",
            diff_obs=" evals/minio_lifecycle.json | 2+-\n tests/test_minio_lifecycle_expire.py | 12++\n",
            residual="Bucket leftover policy still expires in 1 day.",
        ),
        _bad(
            slug="rclone-bisync-omit-a44h",
            domain="rclone-eval",
            kind="storage",
            avoided="r319 Aim hash; r326 sagemaker s3; r305 nix gcroot",
            goal=(
                "rclone leftover bisync --filters-file skips goldens/ so planted promo-hold "
                "never reaches the remote gate. Include goldens; fail if the filter drops them."
            ),
            plan="Dump rclone filter, include goldens, prove planted promo-hold locally.",
            outcome=(
                "Local filter includes goldens/. Planted promo-hold present locally. Handoff: "
                "the NAS leftover still uses the omit-goldens filter."
            ),
            ticket=(
                "Title: rclone leftover --filter - goldens/**. planted promo-hold not synced."
            ),
            src="evals/rclone.filter",
            src_obs="- goldens/**  # leftover 'too large'",
            run="evals/rclone_eval.py",
            fail_obs="filter leftover drops goldens. planted promo-hold absent remote",
            inspect="evals/rclone.filter",
            inspect_obs="- goldens/** leftover",
            first_path="evals/rclone.filter",
            first_old="- goldens/**",
            first_new="- goldens/archive/**",
            first_obs="archive only. NAS leftover still - goldens/**",
            rate_tail="NAS leftover filter omit goldens",
            still_after_429="NAS leftover omit; planted promo-hold absent",
            grep="goldens/\\*\\*|rclone.filter|bisync",
            grep_obs="cannot change NAS filter from this ticket",
            plan_change="local include goldens; document NAS leftover omit",
            fix_path="evals/rclone.filter",
            fix_old="- goldens/archive/**",
            fix_new="+ goldens/**",
            fix_obs="local planted present. NAS leftover HANDOFF",
            retry_obs="502 unused. NAS leftover omit goldens. Partial",
            test="tests/test_rclone_includes_goldens.py",
            test_body="xfail NAS leftover omit; local + goldens/**",
            test_obs="NAS leftover omit goldens. Partial",
            suite_obs="local include goldens. NAS leftover omit. Partial.",
            gate_obs="local include goldens. NAS leftover omit. Partial.",
            diff_obs=" evals/rclone.filter | 2+-\n HANDOFF rclone NAS\n",
            residual="NAS leftover still uses the omit-goldens filter. Partial.",
        ),
    )
)

# r335 scheduler leftover
PAIRS.append(
    (
        _ok(
            slug="cron-opt-eval-sh-b45i",
            domain="cron-eval",
            kind="sched",
            avoided="r271 makefile stale; r320 justfile legacy; r300 gitlab dotenv",
            goal=(
                "cron leftover /opt/eval/run.sh from last deploy still calls evals/legacy.py "
                "so planted flash-hold never runs. Point the installed script at this SHA."
            ),
            plan="Dump cron script, retarget SHA, prove planted flash-hold fail.",
            outcome=(
                "/opt/eval/run.sh now execs repo evals/*.py. Planted flash-hold 0.12 fail-closed. "
                "Residual: a second crontab leftover still points at /opt/eval/run.sh.bak."
            ),
            ticket=(
                "Title: cron leftover /opt/eval/run.sh last deploy. planted flash-hold unused."
            ),
            src="/opt/eval/run.sh",
            src_obs="python evals/legacy.py  # leftover last deploy",
            run="evals/flash_hold.py",
            fail_obs="legacy leftover. planted flash-hold absent",
            inspect="/etc/cron.d/eval",
            inspect_obs="cron leftover /opt/eval/run.sh. not repo path",
            first_path="/opt/eval/run.sh",
            first_old="python evals/legacy.py",
            first_new="python evals/flash_hold.py",
            first_obs="opt updated. crontab leftover still run.sh.bak",
            rate_tail="crontab leftover run.sh.bak legacy",
            still_after_429="bak leftover; planted flash-hold unused",
            grep="run.sh|legacy.py|cron.d/eval",
            grep_obs="install repo script; remove bak; glob evals/*.py",
            plan_change="install SHA script; refuse /opt/eval/run.sh.bak",
            fix_path="/etc/cron.d/eval",
            fix_old="/opt/eval/run.sh",
            fix_new="/opt/eval/run.sh --sha $GIT_SHA",
            fix_obs="planted flash-hold 0.12. bak unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold 0.12",
            test="tests/test_cron_eval_sha_script.py",
            test_body="assert cron script globs evals/*.py; bak unused",
            test_obs="test_cron_not_legacy_opt_script",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold",
            diff_obs=" /opt/eval/run.sh | 4+-\n tests/test_cron_eval_sha_script.py | 12++\n",
            residual="Second crontab leftover still points at /opt/eval/run.sh.bak.",
        ),
        _bad(
            slug="systemd-workingdir-old-c46j",
            domain="systemd-eval",
            kind="sched",
            avoided="r271 makefile stale; r320 taskfile dir; r288 dotenv empty",
            goal=(
                "systemd leftover WorkingDirectory=/opt/eval-old so the unit runs yesterday's "
                "tree and planted price-hold never executes. Point WorkingDirectory at the "
                "repo; fail if cwd is /opt/eval-old."
            ),
            plan="Dump unit WorkingDirectory, pin repo, prove planted price-hold locally.",
            outcome=(
                "Local unit cwd is the repo. Planted price-hold runs locally. Handoff: the "
                "host leftover drop-in still sets WorkingDirectory=/opt/eval-old."
            ),
            ticket=(
                "Title: systemd leftover WorkingDirectory=/opt/eval-old. planted price-hold unused."
            ),
            src="evals/eval.service",
            src_obs="WorkingDirectory=/opt/eval-old  # leftover last image",
            run="evals/price_hold.py",
            fail_obs="cwd leftover /opt/eval-old. planted price-hold absent",
            inspect="/etc/systemd/system/eval.service.d/override.conf",
            inspect_obs="drop-in leftover WorkingDirectory=/opt/eval-old",
            first_path="evals/eval.service",
            first_old="WorkingDirectory=/opt/eval-old",
            first_new="WorkingDirectory=/opt/eval",
            first_obs="unit /opt/eval. host leftover drop-in still eval-old",
            rate_tail="host leftover drop-in WorkingDirectory=/opt/eval-old",
            still_after_429="drop-in leftover eval-old; planted price-hold unused",
            grep="WorkingDirectory|eval-old|eval.service.d",
            grep_obs="cannot remove host drop-in from this ticket",
            plan_change="local cwd repo; document host leftover /opt/eval-old",
            fix_path="evals/eval.service",
            fix_old="WorkingDirectory=/opt/eval",
            fix_new="WorkingDirectory=%h/src/eval",
            fix_obs="local planted runs. host leftover HANDOFF",
            retry_obs="502 unused. host leftover WorkingDirectory. Partial",
            test="tests/test_systemd_workdir.py",
            test_body="xfail host leftover /opt/eval-old; local repo cwd",
            test_obs="host leftover WorkingDirectory. Partial",
            suite_obs="local repo cwd. host leftover /opt/eval-old. Partial.",
            gate_obs="local repo cwd. host leftover /opt/eval-old. Partial.",
            diff_obs=" evals/eval.service | 2+-\n HANDOFF systemd workdir\n",
            residual="Host leftover drop-in still sets WorkingDirectory=/opt/eval-old. Partial.",
        ),
    )
)

# r336 config leftover
PAIRS.append(
    (
        _ok(
            slug="hydra-defaults-old-d47k",
            domain="hydra-eval",
            kind="config",
            avoided="r288 dotenv empty; r289 direnv tox; r291 judge-model drift",
            goal=(
                "Hydra leftover defaults list includes eval/threshold@old so planted "
                "loyalty-hold 0.18 is compared to 0.0. Drop the old defaults; pin threshold 0.7."
            ),
            plan="Dump hydra defaults, drop @old, prove planted loyalty-hold fail.",
            outcome=(
                "defaults no longer include threshold@old. Planted loyalty-hold 0.18 fail-closed. "
                "Residual: a user leftover ~/.hydra still prepends eval/threshold@old."
            ),
            ticket=(
                "Title: Hydra leftover defaults eval/threshold@old. planted loyalty-hold vs 0.0."
            ),
            src="evals/config.yaml",
            src_obs="defaults:\n  - eval/threshold@old  # leftover",
            run="evals/loyalty_hold.py",
            fail_obs="threshold leftover 0.0. planted loyalty-hold pass",
            inspect="evals/config.yaml",
            inspect_obs="defaults leftover @old. threshold 0.0",
            first_path="evals/config.yaml",
            first_old="- eval/threshold@old",
            first_new="- eval/threshold@new",
            first_obs="@new local. leftover ~/.hydra still prepends @old",
            rate_tail="user leftover ~/.hydra threshold@old",
            still_after_429="user leftover @old; planted loyalty-hold pass",
            grep="threshold@old|defaults:|~/.hydra",
            grep_obs="ignore user leftover; force threshold 0.7 in-app",
            plan_change="in-app threshold 0.7; refuse hydra @old override",
            fix_path="evals/loyalty_hold.py",
            fix_old="threshold = cfg.threshold",
            fix_new="threshold = 0.7  # ignore hydra leftover @old",
            fix_obs="planted loyalty-hold 0.18 fail-closed",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold 0.18",
            test="tests/test_hydra_not_old_threshold.py",
            test_body="assert threshold 0.7; @old unused",
            test_obs="test_hydra_defaults_not_old",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold",
            diff_obs=" evals/config.yaml | 2+-\n evals/loyalty_hold.py | 4+-\n tests/test_hydra_not_old_threshold.py | 12++\n",
            residual="User leftover ~/.hydra still prepends eval/threshold@old.",
        ),
        _bad(
            slug="omegaconf-etc-merge-e48l",
            domain="omega-eval",
            kind="config",
            avoided="r288 dotenv empty; r289 direnv; r319 Aim hash",
            goal=(
                "OmegaConf leftover merge from /etc/eval.yaml sets threshold 0 after the repo "
                "yaml. Stop merging /etc; fail-closed locally."
            ),
            plan="Dump merge order, drop /etc, prove planted cancel-hold locally.",
            outcome=(
                "Local merge skips /etc/eval.yaml. Planted cancel-hold fails locally. Handoff: "
                "the host leftover still injects /etc/eval.yaml via EVAL_CONF."
            ),
            ticket=(
                "Title: OmegaConf leftover merge /etc/eval.yaml. planted cancel-hold vs 0."
            ),
            src="evals/omega_eval.py",
            src_obs="cfg = OmegaConf.merge(repo, OmegaConf.load('/etc/eval.yaml'))  # leftover",
            run="evals/cancel_hold.py",
            fail_obs="/etc leftover threshold 0. planted cancel-hold pass",
            inspect="evals/omega_eval.py",
            inspect_obs="/etc leftover last-write 0",
            first_path="evals/omega_eval.py",
            first_old="OmegaConf.load('/etc/eval.yaml')",
            first_new="OmegaConf.load(os.getenv('EVAL_CONF','/etc/eval.yaml'))",
            first_obs="env leftover EVAL_CONF=/etc/eval.yaml",
            rate_tail="host leftover EVAL_CONF=/etc/eval.yaml",
            still_after_429="host leftover /etc; planted cancel-hold pass",
            grep="/etc/eval.yaml|EVAL_CONF|OmegaConf.merge",
            grep_obs="cannot unset host EVAL_CONF from this ticket",
            plan_change="local repo-only merge; document host leftover /etc",
            fix_path="evals/omega_eval.py",
            fix_old="OmegaConf.load(os.getenv('EVAL_CONF','/etc/eval.yaml'))",
            fix_new="OmegaConf.load('evals/config.yaml')",
            fix_obs="local planted fail. host leftover HANDOFF",
            retry_obs="502 unused. host leftover /etc merge. Partial",
            test="tests/test_omega_no_etc_merge.py",
            test_body="xfail host leftover /etc; local repo-only",
            test_obs="host leftover /etc merge. Partial",
            suite_obs="local repo-only. host leftover /etc. Partial.",
            gate_obs="local repo-only. host leftover /etc. Partial.",
            diff_obs=" evals/omega_eval.py | 4+-\n HANDOFF omega /etc\n",
            residual="Host leftover still injects /etc/eval.yaml via EVAL_CONF. Partial.",
        ),
    )
)
