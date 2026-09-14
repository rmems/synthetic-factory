"""Unique eval-harness leftover plants r412+. Not r319/GEval-cache/test_ or prior leftover clones."""

from mill_plants import PAIRS, _bad, _ok

# r412 cfn leftover
PAIRS.append(
    (
        _ok(
            slug="cfn-changeset-stale-z99g",
            domain="cfn-eval",
            kind="iac",
            avoided="r400 tofu; r410 atmos; r319 ClearML uri",
            goal=(
                "CloudFormation leftover changeset eval-cs still describes yesterday goldens "
                "so planted dual-void-3 never applies. Create changeset eval-cs-<sha>."
            ),
            plan="Dump changeset name, pin SHA, prove planted dual-void-3 fail.",
            outcome=(
                "Changeset is eval-cs-<sha>. Planted dual-void-3 0.13 fail-closed. Residual: "
                "a stack leftover still ChangeSetName=eval-cs."
            ),
            ticket=(
                "Title: CFN leftover changeset eval-cs. planted dual-void-3 missing."
            ),
            src="evals/cfn.sh",
            src_obs="aws cloudformation create-change-set --change-set-name eval-cs  # leftover",
            run="evals/cfn_eval.py",
            fail_obs="changeset leftover yesterday. planted dual-void-3 absent",
            inspect="evals/cfn.sh",
            inspect_obs="stable changeset leftover",
            first_path="evals/cfn.sh",
            first_old="--change-set-name eval-cs",
            first_new="--change-set-name eval-cs-dev",
            first_obs="dev local. stack leftover still eval-cs",
            rate_tail="stack leftover ChangeSetName=eval-cs",
            still_after_429="stack leftover changeset; planted dual-void-3 absent",
            grep="eval-cs|change-set-name|goldens",
            grep_obs="name eval-cs-<sha>; ignore stack leftover",
            plan_change="changeset eval-cs-<sha>; refuse eval-cs",
            fix_path="evals/cfn.sh",
            fix_old="--change-set-name eval-cs-dev",
            fix_new="--change-set-name eval-cs-$GIT_SHA",
            fix_obs="planted dual-void-3 0.13 in sha changeset",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-void-3 0.13",
            test="tests/test_cfn_changeset_sha.py",
            test_body="assert changeset name includes sha; eval-cs unused",
            test_obs="test_cfn_not_eval_cs",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-void-3",
            diff_obs=" evals/cfn.sh | 2+-\n tests/test_cfn_changeset_sha.py | 12++\n",
            residual="Stack leftover still ChangeSetName=eval-cs.",
        ),
        _bad(
            slug="sam-config-stale-a00h",
            domain="sam-eval",
            kind="iac",
            avoided="r412 cfn; r400 tofu; r319 Aim hash",
            goal=(
                "SAM leftover samconfig.toml stack_name=eval so planted rain-hold-6 never "
                "deploys this SHA. Pin stack_name locally."
            ),
            plan="Dump samconfig, pin SHA, prove planted rain-hold-6 locally.",
            outcome=(
                "Local stack_name is eval-<sha>. Planted rain-hold-6 present locally. "
                "Handoff: the pipeline leftover still stack_name=eval."
            ),
            ticket=(
                "Title: SAM leftover stack_name=eval. planted rain-hold-6 missing."
            ),
            src="samconfig.toml",
            src_obs='stack_name = "eval"  # leftover',
            run="evals/sam_eval.py",
            fail_obs="stack leftover yesterday. planted rain-hold-6 absent",
            inspect="samconfig.toml",
            inspect_obs="stable stack leftover",
            first_path="samconfig.toml",
            first_old='stack_name = "eval"',
            first_new='stack_name = "eval-dev"',
            first_obs="dev local. pipeline leftover still eval",
            rate_tail="pipeline leftover stack_name=eval",
            still_after_429="pipeline leftover stack; planted rain-hold-6 absent",
            grep="stack_name|samconfig|goldens",
            grep_obs="cannot change pipeline leftover from this ticket",
            plan_change="local stack eval-<sha>; document pipeline leftover eval",
            fix_path="samconfig.toml",
            fix_old='stack_name = "eval-dev"',
            fix_new='stack_name = "eval-{{sha}}"',
            fix_obs="local planted present. pipeline leftover HANDOFF",
            retry_obs="502 unused. pipeline leftover sam stack. Partial",
            test="tests/test_sam_stack_sha.py",
            test_body="xfail pipeline leftover eval; local eval-<sha>",
            test_obs="pipeline leftover sam stack. Partial",
            suite_obs="local eval-sha. pipeline leftover eval. Partial.",
            gate_obs="local eval-sha. pipeline leftover eval. Partial.",
            diff_obs=" samconfig.toml | 2+-\n HANDOFF sam pipeline\n",
            residual="Pipeline leftover still stack_name=eval. Partial.",
        ),
    )
)

# r413 cdk leftover
PAIRS.append(
    (
        _ok(
            slug="cdk-out-stale-b01i",
            domain="cdk-eval",
            kind="iac",
            avoided="r406 cdk8s; r412 cfn; r319 ClearML uri",
            goal=(
                "CDK leftover cdk.out still has yesterday goldens so planted "
                "flash-hold-7 never synths. Synth to cdk.out-<sha>."
            ),
            plan="Dump cdk.json, pin outdir, prove planted flash-hold-7 fail.",
            outcome=(
                "outdir is cdk.out-<sha>. Planted flash-hold-7 0.14 fail-closed. Residual: "
                "a pipeline leftover still cdk synth -o cdk.out."
            ),
            ticket=(
                "Title: CDK leftover cdk.out yesterday. planted flash-hold-7 missing."
            ),
            src="cdk.json",
            src_obs='"output": "cdk.out"  // leftover',
            run="evals/cdk_eval.py",
            fail_obs="cdk.out leftover yesterday. planted flash-hold-7 absent",
            inspect="cdk.json",
            inspect_obs="stable outdir leftover",
            first_path="cdk.json",
            first_old='"output": "cdk.out"',
            first_new='"output": "cdk.out-dev"',
            first_obs="dev local. pipeline leftover still cdk.out",
            rate_tail="pipeline leftover cdk synth -o cdk.out",
            still_after_429="pipeline leftover outdir; planted flash-hold-7 absent",
            grep="cdk.out|output|goldens",
            grep_obs="outdir cdk.out-<sha>; ignore pipeline leftover",
            plan_change="outdir cdk.out-<sha>; refuse cdk.out",
            fix_path="cdk.json",
            fix_old='"output": "cdk.out-dev"',
            fix_new='"output": "cdk.out-{{sha}}"',
            fix_obs="planted flash-hold-7 0.14 in sha outdir",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-7 0.14",
            test="tests/test_cdk_outdir_sha.py",
            test_body="assert outdir includes sha; cdk.out unused",
            test_obs="test_cdk_not_stable_out",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-7",
            diff_obs=" cdk.json | 2+-\n tests/test_cdk_outdir_sha.py | 12++\n",
            residual="Pipeline leftover still cdk synth -o cdk.out.",
        ),
        _bad(
            slug="sst-stage-stale-c02j",
            domain="sst-eval",
            kind="iac",
            avoided="r413 cdk; r412 sam; r319 Aim hash",
            goal=(
                "SST leftover stage eval still deploys yesterday goldens so planted "
                "promo-hold-6 never ships. Pin stage locally."
            ),
            plan="Dump sst.config, pin SHA stage, prove planted promo-hold-6 locally.",
            outcome=(
                "Local stage is eval-<sha>. Planted promo-hold-6 present locally. Handoff: "
                "the CLI leftover still sst deploy --stage eval."
            ),
            ticket=(
                "Title: SST leftover --stage eval. planted promo-hold-6 missing."
            ),
            src="sst.config.ts",
            src_obs='stage: "eval"  // leftover',
            run="evals/sst_eval.py",
            fail_obs="stage leftover yesterday. planted promo-hold-6 absent",
            inspect="sst.config.ts",
            inspect_obs="stage eval leftover",
            first_path="sst.config.ts",
            first_old='stage: "eval"',
            first_new='stage: "eval-dev"',
            first_obs="dev local. CLI leftover still --stage eval",
            rate_tail="CLI leftover sst deploy --stage eval",
            still_after_429="CLI leftover stage; planted promo-hold-6 absent",
            grep="stage: .eval|sst deploy|goldens",
            grep_obs="cannot change CLI leftover from this ticket",
            plan_change="local stage eval-<sha>; document CLI leftover eval",
            fix_path="sst.config.ts",
            fix_old='stage: "eval-dev"',
            fix_new='stage: `eval-${gitSha}`',
            fix_obs="local planted present. CLI leftover HANDOFF",
            retry_obs="502 unused. CLI leftover sst stage. Partial",
            test="tests/test_sst_stage_sha.py",
            test_body="xfail CLI leftover eval; local eval-<sha>",
            test_obs="CLI leftover sst stage. Partial",
            suite_obs="local eval-sha. CLI leftover eval. Partial.",
            gate_obs="local eval-sha. CLI leftover eval. Partial.",
            diff_obs=" sst.config.ts | 2+-\n HANDOFF sst cli\n",
            residual="CLI leftover still sst deploy --stage eval. Partial.",
        ),
    )
)

# r414 serverless leftover
PAIRS.append(
    (
        _ok(
            slug="sls-stage-stale-d03k",
            domain="sls-eval",
            kind="iac",
            avoided="r413 sst; r412 sam; r319 ClearML uri",
            goal=(
                "Serverless leftover stage eval still deploys yesterday goldens so planted "
                "gift-hold-6 never ships. Pin the stage to this SHA."
            ),
            plan="Dump serverless.yml, pin SHA, prove planted gift-hold-6 fail.",
            outcome=(
                "stage is eval-<sha>. Planted gift-hold-6 0.15 fail-closed. Residual: a "
                "dashboard leftover still stage=eval."
            ),
            ticket=(
                "Title: Serverless leftover stage=eval. planted gift-hold-6 missing."
            ),
            src="serverless.yml",
            src_obs="stage: eval  # leftover",
            run="evals/sls_eval.py",
            fail_obs="stage leftover yesterday. planted gift-hold-6 absent",
            inspect="serverless.yml",
            inspect_obs="stage eval leftover",
            first_path="serverless.yml",
            first_old="stage: eval",
            first_new="stage: eval-dev",
            first_obs="dev local. dashboard leftover still eval",
            rate_tail="dashboard leftover stage=eval",
            still_after_429="dashboard leftover stage; planted gift-hold-6 absent",
            grep="stage: eval|serverless.yml|goldens",
            grep_obs="stage eval-<sha>; ignore dashboard leftover",
            plan_change="stage eval-<sha>; refuse eval",
            fix_path="serverless.yml",
            fix_old="stage: eval-dev",
            fix_new="stage: eval-${git:sha1}",
            fix_obs="planted gift-hold-6 0.15 in sha stage",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-6 0.15",
            test="tests/test_sls_stage_sha.py",
            test_body="assert stage includes sha; eval unused",
            test_obs="test_sls_not_stage_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-6",
            diff_obs=" serverless.yml | 2+-\n tests/test_sls_stage_sha.py | 12++\n",
            residual="Dashboard leftover still stage=eval.",
        ),
        _bad(
            slug="amplify-branch-stale-e04l",
            domain="amplify-eval",
            kind="iac",
            avoided="r414 sls; r410 spacelift; r319 Aim hash",
            goal=(
                "Amplify leftover branch leftover/main so planted bundle-hold-5 never "
                "builds. Pin the branch locally."
            ),
            plan="Dump amplify.yml, pin SHA, prove planted bundle-hold-5 locally.",
            outcome=(
                "Local branch is this SHA. Planted bundle-hold-5 present locally. Handoff: "
                "the app leftover still leftover/main."
            ),
            ticket=(
                "Title: Amplify leftover branch leftover/main. planted bundle-hold-5 missing."
            ),
            src="amplify.yml",
            src_obs="branch: leftover/main  # leftover",
            run="evals/amplify_eval.py",
            fail_obs="branch leftover leftover/main. planted bundle-hold-5 absent",
            inspect="amplify.yml",
            inspect_obs="leftover/main leftover",
            first_path="amplify.yml",
            first_old="branch: leftover/main",
            first_new="branch: dev",
            first_obs="dev local. app leftover still leftover/main",
            rate_tail="app leftover branch leftover/main",
            still_after_429="app leftover branch; planted bundle-hold-5 absent",
            grep="leftover/main|amplify.yml|goldens",
            grep_obs="cannot change app leftover from this ticket",
            plan_change="local SHA branch; document app leftover leftover/main",
            fix_path="amplify.yml",
            fix_old="branch: dev",
            fix_new="branch: {{sha}}",
            fix_obs="local planted present. app leftover HANDOFF",
            retry_obs="502 unused. app leftover leftover/main. Partial",
            test="tests/test_amplify_branch_sha.py",
            test_body="xfail app leftover leftover/main; local SHA branch",
            test_obs="app leftover leftover/main. Partial",
            suite_obs="local SHA branch. app leftover leftover/main. Partial.",
            gate_obs="local SHA branch. app leftover leftover/main. Partial.",
            diff_obs=" amplify.yml | 2+-\n HANDOFF amplify app\n",
            residual="App leftover still leftover/main. Partial.",
        ),
    )
)

# r415 copilot leftover
PAIRS.append(
    (
        _ok(
            slug="copilot-env-stale-f05m",
            domain="copilot-eval",
            kind="iac",
            avoided="r414 sls; r412 sam; r319 ClearML uri",
            goal=(
                "Copilot leftover env eval still manifests yesterday goldens so planted "
                "loyalty-hold-5 never deploys. Pin env to this SHA."
            ),
            plan="Dump copilot env, pin SHA, prove planted loyalty-hold-5 fail.",
            outcome=(
                "env is eval-<sha>. Planted loyalty-hold-5 0.12 fail-closed. Residual: a "
                "pipeline leftover still copilot deploy --env eval."
            ),
            ticket=(
                "Title: Copilot leftover --env eval. planted loyalty-hold-5 missing."
            ),
            src="copilot/eval/manifest.yml",
            src_obs="name: eval  # leftover",
            run="evals/copilot_eval.py",
            fail_obs="env leftover yesterday. planted loyalty-hold-5 absent",
            inspect="copilot/eval/manifest.yml",
            inspect_obs="name eval leftover",
            first_path="copilot/eval/manifest.yml",
            first_old="name: eval",
            first_new="name: eval-dev",
            first_obs="dev local. pipeline leftover still --env eval",
            rate_tail="pipeline leftover copilot deploy --env eval",
            still_after_429="pipeline leftover env; planted loyalty-hold-5 absent",
            grep="--env eval|name: eval|goldens",
            grep_obs="env eval-<sha>; ignore pipeline leftover",
            plan_change="env eval-<sha>; refuse --env eval",
            fix_path="copilot/eval/manifest.yml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted loyalty-hold-5 0.12 in sha env",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-5 0.12",
            test="tests/test_copilot_env_sha.py",
            test_body="assert env includes sha; eval unused",
            test_obs="test_copilot_not_env_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-5",
            diff_obs=" copilot/eval/manifest.yml | 2+-\n tests/test_copilot_env_sha.py | 12++\n",
            residual="Pipeline leftover still copilot deploy --env eval.",
        ),
        _bad(
            slug="proton-template-stale-g06n",
            domain="proton-eval",
            kind="iac",
            avoided="r415 copilot; r411 env0; r319 Aim hash",
            goal=(
                "Proton leftover template eval still majorVersion=1 so planted "
                "cancel-hold-5 never renders. Pin the version locally."
            ),
            plan="Dump template, pin version, prove planted cancel-hold-5 locally.",
            outcome=(
                "Local template version is this SHA. Planted cancel-hold-5 present locally. "
                "Handoff: the account leftover still majorVersion=1."
            ),
            ticket=(
                "Title: Proton leftover template eval majorVersion=1. planted cancel-hold-5 missing."
            ),
            src="evals/proton.yaml",
            src_obs="majorVersion: 1  # leftover",
            run="evals/proton_eval.py",
            fail_obs="v1 leftover. planted cancel-hold-5 absent",
            inspect="evals/proton.yaml",
            inspect_obs="majorVersion 1 leftover",
            first_path="evals/proton.yaml",
            first_old="majorVersion: 1",
            first_new="majorVersion: 2",
            first_obs="2 local. account leftover still 1",
            rate_tail="account leftover majorVersion=1",
            still_after_429="account leftover v1; planted cancel-hold-5 absent",
            grep="majorVersion|proton.yaml|goldens",
            grep_obs="cannot change account leftover from this ticket",
            plan_change="local SHA version; document account leftover v1",
            fix_path="evals/proton.yaml",
            fix_old="majorVersion: 2",
            fix_new="majorVersion: {{sha}}",
            fix_obs="local planted present. account leftover HANDOFF",
            retry_obs="502 unused. account leftover proton v1. Partial",
            test="tests/test_proton_version_sha.py",
            test_body="xfail account leftover v1; local SHA version",
            test_obs="account leftover proton v1. Partial",
            suite_obs="local SHA version. account leftover v1. Partial.",
            gate_obs="local SHA version. account leftover v1. Partial.",
            diff_obs=" evals/proton.yaml | 2+-\n HANDOFF proton account\n",
            residual="Account leftover still majorVersion=1. Partial.",
        ),
    )
)

# r416 config-mgmt leftover
PAIRS.append(
    (
        _ok(
            slug="salt-pillar-stale-h07o",
            domain="salt-eval",
            kind="cfgmgmt",
            avoided="r336 hydra; r335 systemd envfile; r319 ClearML uri",
            goal=(
                "Salt leftover pillar eval:threshold: 0 so planted tax-hold-5 never fails. "
                "Pin pillar to 0.7 from this SHA."
            ),
            plan="Dump pillar, pin 0.7, prove planted tax-hold-5 fail.",
            outcome=(
                "pillar threshold 0.7. Planted tax-hold-5 0.16 fail-closed. Residual: a "
                "master leftover still pillar eval:threshold: 0."
            ),
            ticket=(
                "Title: Salt leftover pillar eval:threshold 0. planted tax-hold-5 green."
            ),
            src="pillar/eval.sls",
            src_obs="eval:\n  threshold: 0  # leftover",
            run="evals/salt_eval.py",
            fail_obs="threshold leftover 0. planted tax-hold-5 pass",
            inspect="pillar/eval.sls",
            inspect_obs="0 leftover",
            first_path="pillar/eval.sls",
            first_old="threshold: 0",
            first_new="threshold: 0.7",
            first_obs="0.7 local. master leftover still 0",
            rate_tail="master leftover pillar threshold 0",
            still_after_429="master leftover 0; planted tax-hold-5 pass",
            grep="threshold: 0|pillar/eval|goldens",
            grep_obs="force 0.7; ignore master leftover",
            plan_change="pillar 0.7; refuse leftover 0",
            fix_path="pillar/eval.sls",
            fix_old="threshold: 0.7",
            fix_new="threshold: 0.7  # no master leftover",
            fix_obs="planted tax-hold-5 0.16. leftover 0 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-5 0.16",
            test="tests/test_salt_pillar_not_zero.py",
            test_body="assert threshold 0.7; leftover 0 unused",
            test_obs="test_salt_not_threshold_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-5",
            diff_obs=" pillar/eval.sls | 2+-\n tests/test_salt_pillar_not_zero.py | 12++\n",
            residual="Master leftover still pillar eval:threshold: 0.",
        ),
        _bad(
            slug="chef-attr-stale-i08p",
            domain="chef-eval",
            kind="cfgmgmt",
            avoided="r416 salt; r336 omega; r319 Aim hash",
            goal=(
                "Chef leftover attribute eval.threshold=0 so planted sla-hold-4 never "
                "fails. Pin the attribute locally."
            ),
            plan="Dump attributes, pin 0.7, prove planted sla-hold-4 locally.",
            outcome=(
                "Local attribute 0.7. Planted sla-hold-4 fails locally. Handoff: the "
                "role leftover still eval.threshold=0."
            ),
            ticket=(
                "Title: Chef leftover eval.threshold=0. planted sla-hold-4 green."
            ),
            src="attributes/default.rb",
            src_obs="default['eval']['threshold'] = 0  # leftover",
            run="evals/chef_eval.py",
            fail_obs="threshold leftover 0. planted sla-hold-4 pass",
            inspect="attributes/default.rb",
            inspect_obs="0 leftover",
            first_path="attributes/default.rb",
            first_old="default['eval']['threshold'] = 0",
            first_new="default['eval']['threshold'] = 0.7",
            first_obs="0.7 local. role leftover still 0",
            rate_tail="role leftover eval.threshold=0",
            still_after_429="role leftover 0; planted sla-hold-4 pass",
            grep="threshold. = 0|attributes|goldens",
            grep_obs="cannot change role leftover from this ticket",
            plan_change="local 0.7; document role leftover 0",
            fix_path="attributes/default.rb",
            fix_old="default['eval']['threshold'] = 0.7",
            fix_new="default['eval']['threshold'] = 0.7 # no role leftover",
            fix_obs="local planted fail. role leftover HANDOFF",
            retry_obs="502 unused. role leftover chef 0. Partial",
            test="tests/test_chef_attr_not_zero.py",
            test_body="xfail role leftover 0; local 0.7",
            test_obs="role leftover chef 0. Partial",
            suite_obs="local 0.7. role leftover 0. Partial.",
            gate_obs="local 0.7. role leftover 0. Partial.",
            diff_obs=" attributes/default.rb | 2+-\n HANDOFF chef role\n",
            residual="Role leftover still eval.threshold=0. Partial.",
        ),
    )
)

# r417 puppet leftover
PAIRS.append(
    (
        _ok(
            slug="puppet-hiera-stale-j09q",
            domain="puppet-eval",
            kind="cfgmgmt",
            avoided="r416 salt; r416 chef; r319 ClearML uri",
            goal=(
                "Puppet leftover hiera eval::threshold: 0 so planted membership-hold-3 "
                "never fails. Pin hiera to 0.7."
            ),
            plan="Dump hiera, pin 0.7, prove planted membership-hold-3 fail.",
            outcome=(
                "hiera threshold 0.7. Planted membership-hold-3 0.13 fail-closed. Residual: "
                "a classifier leftover still eval::threshold 0."
            ),
            ticket=(
                "Title: Puppet leftover hiera eval::threshold 0. planted membership-hold-3 green."
            ),
            src="data/common.yaml",
            src_obs="eval::threshold: 0  # leftover",
            run="evals/puppet_eval.py",
            fail_obs="threshold leftover 0. planted membership-hold-3 pass",
            inspect="data/common.yaml",
            inspect_obs="0 leftover",
            first_path="data/common.yaml",
            first_old="eval::threshold: 0",
            first_new="eval::threshold: 0.7",
            first_obs="0.7 local. classifier leftover still 0",
            rate_tail="classifier leftover eval::threshold 0",
            still_after_429="classifier leftover 0; planted membership-hold-3 pass",
            grep="eval::threshold|hiera|goldens",
            grep_obs="force 0.7; ignore classifier leftover",
            plan_change="hiera 0.7; refuse leftover 0",
            fix_path="data/common.yaml",
            fix_old="eval::threshold: 0.7",
            fix_new="eval::threshold: 0.7  # no classifier leftover",
            fix_obs="planted membership-hold-3 0.13. leftover 0 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold-3 0.13",
            test="tests/test_puppet_hiera_not_zero.py",
            test_body="assert hiera 0.7; leftover 0 unused",
            test_obs="test_puppet_not_threshold_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-3",
            diff_obs=" data/common.yaml | 2+-\n tests/test_puppet_hiera_not_zero.py | 12++\n",
            residual="Classifier leftover still eval::threshold 0.",
        ),
        _bad(
            slug="bolt-plan-stale-k10r",
            domain="bolt-eval",
            kind="cfgmgmt",
            avoided="r417 puppet; r320 justfile; r319 Aim hash",
            goal=(
                "Bolt leftover plan eval::legacy still runs yesterday goldens so planted "
                "after-hold-5 never starts. Point the plan at evals locally."
            ),
            plan="Dump bolt.yaml, retarget, prove planted after-hold-5 locally.",
            outcome=(
                "Local plan is evals. Planted after-hold-5 present locally. Handoff: the "
                "inventory leftover still plan eval::legacy."
            ),
            ticket=(
                "Title: Bolt leftover plan eval::legacy. planted after-hold-5 unused."
            ),
            src="bolt.yaml",
            src_obs="plans:\n  eval: eval::legacy  # leftover",
            run="evals/bolt_eval.py",
            fail_obs="legacy leftover. planted after-hold-5 unused",
            inspect="bolt.yaml",
            inspect_obs="eval::legacy leftover",
            first_path="bolt.yaml",
            first_old="eval: eval::legacy",
            first_new="eval: eval::dev",
            first_obs="dev local. inventory leftover still eval::legacy",
            rate_tail="inventory leftover plan eval::legacy",
            still_after_429="inventory leftover; planted after-hold-5 unused",
            grep="eval::legacy|bolt.yaml|goldens",
            grep_obs="cannot change inventory leftover from this ticket",
            plan_change="local evals plan; document inventory leftover legacy",
            fix_path="bolt.yaml",
            fix_old="eval: eval::dev",
            fix_new="eval: evals/*.py",
            fix_obs="local planted present. inventory leftover HANDOFF",
            retry_obs="502 unused. inventory leftover bolt legacy. Partial",
            test="tests/test_bolt_not_legacy.py",
            test_body="xfail inventory leftover legacy; local evals",
            test_obs="inventory leftover bolt legacy. Partial",
            suite_obs="local evals. inventory leftover legacy. Partial.",
            gate_obs="local evals. inventory leftover legacy. Partial.",
            diff_obs=" bolt.yaml | 2+-\n HANDOFF bolt inventory\n",
            residual="Inventory leftover still plan eval::legacy. Partial.",
        ),
    )
)

# r418 deploy leftover
PAIRS.append(
    (
        _ok(
            slug="capistrano-stage-stale-l11s",
            domain="capistrano-eval",
            kind="deploy",
            avoided="r414 sls stage; r335 cron; r319 ClearML uri",
            goal=(
                "Capistrano leftover stage eval still deploys yesterday goldens so planted "
                "sku-hold-3 never ships. Pin the stage to this SHA."
            ),
            plan="Dump deploy.rb, pin SHA, prove planted sku-hold-3 fail.",
            outcome=(
                "stage is eval-<sha>. Planted sku-hold-3 0.14 fail-closed. Residual: a "
                "role leftover still cap eval deploy."
            ),
            ticket=(
                "Title: Capistrano leftover stage eval. planted sku-hold-3 missing."
            ),
            src="config/deploy/eval.rb",
            src_obs="set :stage, :eval  # leftover",
            run="evals/capistrano_eval.py",
            fail_obs="stage leftover yesterday. planted sku-hold-3 absent",
            inspect="config/deploy/eval.rb",
            inspect_obs="stage eval leftover",
            first_path="config/deploy/eval.rb",
            first_old="set :stage, :eval",
            first_new="set :stage, :eval_dev",
            first_obs="dev local. role leftover still cap eval deploy",
            rate_tail="role leftover cap eval deploy",
            still_after_429="role leftover stage; planted sku-hold-3 absent",
            grep=":stage, :eval|deploy/eval|goldens",
            grep_obs="stage eval-<sha>; ignore role leftover",
            plan_change="stage eval-<sha>; refuse :eval",
            fix_path="config/deploy/eval.rb",
            fix_old="set :stage, :eval_dev",
            fix_new="set :stage, :\"eval-#{fetch(:sha)}\"",
            fix_obs="planted sku-hold-3 0.14 in sha stage",
            retry_obs="502 then retry; 5 pass 1 fail planted sku-hold-3 0.14",
            test="tests/test_capistrano_stage_sha.py",
            test_body="assert stage includes sha; :eval unused",
            test_obs="test_capistrano_not_stage_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-3",
            diff_obs=" config/deploy/eval.rb | 2+-\n tests/test_capistrano_stage_sha.py | 12++\n",
            residual="Role leftover still cap eval deploy.",
        ),
        _bad(
            slug="fabric-task-stale-m12t",
            domain="fabric-eval",
            kind="deploy",
            avoided="r418 capistrano; r378 invoke; r319 Aim hash",
            goal=(
                "Fabric leftover task eval still runs evals/legacy.py so planted "
                "rain-hold-7 never starts. Point the task at evals locally."
            ),
            plan="Dump fabfile, retarget, prove planted rain-hold-7 locally.",
            outcome=(
                "Local task globs evals/*.py. Planted rain-hold-7 present locally. Handoff: "
                "the alias leftover still fab eval --legacy."
            ),
            ticket=(
                "Title: Fabric leftover task evals/legacy.py. planted rain-hold-7 unused."
            ),
            src="fabfile.py",
            src_obs="@task\ndef eval(c):\n    c.run('pytest evals/legacy.py')  # leftover",
            run="evals/fabric_eval.py",
            fail_obs="legacy leftover. planted rain-hold-7 unused",
            inspect="fabfile.py",
            inspect_obs="legacy leftover",
            first_path="fabfile.py",
            first_old="pytest evals/legacy.py",
            first_new="pytest evals/rain_hold7.py",
            first_obs="rain local. alias leftover still --legacy",
            rate_tail="alias leftover fab eval --legacy",
            still_after_429="alias leftover; planted rain-hold-7 unused",
            grep="legacy.py|fabfile|goldens",
            grep_obs="cannot change alias leftover from this ticket",
            plan_change="local glob evals/*.py; document alias leftover --legacy",
            fix_path="fabfile.py",
            fix_old="pytest evals/rain_hold7.py",
            fix_new="pytest evals/*.py",
            fix_obs="local planted present. alias leftover HANDOFF",
            retry_obs="502 unused. alias leftover fab --legacy. Partial",
            test="tests/test_fabric_not_legacy.py",
            test_body="xfail alias leftover --legacy; local glob",
            test_obs="alias leftover fab --legacy. Partial",
            suite_obs="local glob. alias leftover --legacy. Partial.",
            gate_obs="local glob. alias leftover --legacy. Partial.",
            diff_obs=" fabfile.py | 2+-\n HANDOFF fabric alias\n",
            residual="Alias leftover still fab eval --legacy. Partial.",
        ),
    )
)

# r419 ci leftover
PAIRS.append(
    (
        _ok(
            slug="jenkins-job-stale-n13u",
            domain="jenkins-eval",
            kind="ci",
            avoided="r300 buildkite; r335 cron; r319 ClearML uri",
            goal=(
                "Jenkins leftover job eval still executes evals/legacy.groovy so planted "
                "flash-hold-8 never runs. Point the job at this SHA."
            ),
            plan="Dump Jenkinsfile, retarget, prove planted flash-hold-8 fail.",
            outcome=(
                "Job runs evals/*.py. Planted flash-hold-8 0.15 fail-closed. Residual: a "
                "folder leftover still job eval/legacy."
            ),
            ticket=(
                "Title: Jenkins leftover job evals/legacy.groovy. planted flash-hold-8 unused."
            ),
            src="Jenkinsfile",
            src_obs="sh 'pytest evals/legacy.groovy'  // leftover",
            run="evals/jenkins_eval.py",
            fail_obs="legacy leftover. planted flash-hold-8 unused",
            inspect="Jenkinsfile",
            inspect_obs="legacy leftover",
            first_path="Jenkinsfile",
            first_old="pytest evals/legacy.groovy",
            first_new="pytest evals/*.py",
            first_obs="glob local. folder leftover still eval/legacy",
            rate_tail="folder leftover job eval/legacy",
            still_after_429="folder leftover; planted flash-hold-8 unused",
            grep="legacy.groovy|Jenkinsfile|goldens",
            grep_obs="glob evals/*.py; ignore folder leftover",
            plan_change="job evals/*.py; refuse eval/legacy",
            fix_path="Jenkinsfile",
            fix_old="pytest evals/*.py",
            fix_new="pytest evals/*.py  // no folder leftover",
            fix_obs="planted flash-hold-8 0.15. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-8 0.15",
            test="tests/test_jenkins_not_legacy.py",
            test_body="assert Jenkinsfile globs evals/*.py",
            test_obs="test_jenkins_not_legacy_groovy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-8",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-8",
            diff_obs=" Jenkinsfile | 2+-\n tests/test_jenkins_not_legacy.py | 12++\n",
            residual="Folder leftover still job eval/legacy.",
        ),
        _bad(
            slug="teamcity-build-stale-o14v",
            domain="teamcity-eval",
            kind="ci",
            avoided="r419 jenkins; r300 gitlab dotenv; r319 Aim hash",
            goal=(
                "TeamCity leftover build eval still steps evals/legacy so planted "
                "promo-hold-7 never runs. Point steps locally."
            ),
            plan="Dump .teamcity, retarget, prove planted promo-hold-7 locally.",
            outcome=(
                "Local steps evals/*.py. Planted promo-hold-7 present locally. Handoff: "
                "the project leftover still build eval/legacy."
            ),
            ticket=(
                "Title: TeamCity leftover build eval/legacy. planted promo-hold-7 unused."
            ),
            src=".teamcity/settings.kts",
            src_obs='scriptContent = "pytest evals/legacy.py"  // leftover',
            run="evals/teamcity_eval.py",
            fail_obs="legacy leftover. planted promo-hold-7 unused",
            inspect=".teamcity/settings.kts",
            inspect_obs="legacy leftover",
            first_path=".teamcity/settings.kts",
            first_old="pytest evals/legacy.py",
            first_new="pytest evals/*.py",
            first_obs="glob local. project leftover still eval/legacy",
            rate_tail="project leftover build eval/legacy",
            still_after_429="project leftover; planted promo-hold-7 unused",
            grep="evals/legacy|settings.kts|goldens",
            grep_obs="cannot change project leftover from this ticket",
            plan_change="local glob; document project leftover eval/legacy",
            fix_path=".teamcity/settings.kts",
            fix_old="pytest evals/*.py",
            fix_new="pytest evals/*.py // no project leftover",
            fix_obs="local planted present. project leftover HANDOFF",
            retry_obs="502 unused. project leftover teamcity legacy. Partial",
            test="tests/test_teamcity_not_legacy.py",
            test_body="xfail project leftover eval/legacy; local glob",
            test_obs="project leftover teamcity legacy. Partial",
            suite_obs="local glob. project leftover eval/legacy. Partial.",
            gate_obs="local glob. project leftover eval/legacy. Partial.",
            diff_obs=" .teamcity/settings.kts | 2+-\n HANDOFF teamcity project\n",
            residual="Project leftover still build eval/legacy. Partial.",
        ),
    )
)

# r420 more ci leftover
PAIRS.append(
    (
        _ok(
            slug="concourse-pipeline-stale-p15w",
            domain="concourse-eval",
            kind="ci",
            avoided="r419 jenkins; r314 tekton; r319 ClearML uri",
            goal=(
                "Concourse leftover pipeline eval still get: goldens from leftover/main so "
                "planted gift-hold-7 never runs. Pin the resource to this SHA."
            ),
            plan="Dump pipeline yml, pin SHA, prove planted gift-hold-7 fail.",
            outcome=(
                "resource version is this SHA. Planted gift-hold-7 0.16 fail-closed. Residual: "
                "a fly leftover still set-pipeline -p eval."
            ),
            ticket=(
                "Title: Concourse leftover get goldens leftover/main. planted gift-hold-7 missing."
            ),
            src="ci/eval.yml",
            src_obs="branch: leftover/main  # leftover",
            run="evals/concourse_eval.py",
            fail_obs="branch leftover leftover/main. planted gift-hold-7 absent",
            inspect="ci/eval.yml",
            inspect_obs="leftover/main leftover",
            first_path="ci/eval.yml",
            first_old="branch: leftover/main",
            first_new="branch: dev",
            first_obs="dev local. fly leftover still -p eval leftover/main",
            rate_tail="fly leftover set-pipeline -p eval",
            still_after_429="fly leftover; planted gift-hold-7 absent",
            grep="leftover/main|ci/eval.yml|goldens",
            grep_obs="version SHA; ignore fly leftover",
            plan_change="resource version SHA; refuse leftover/main",
            fix_path="ci/eval.yml",
            fix_old="branch: dev",
            fix_new="branch: {{sha}}",
            fix_obs="planted gift-hold-7 0.16. leftover/main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-7 0.16",
            test="tests/test_concourse_branch_sha.py",
            test_body="assert branch is sha; leftover/main unused",
            test_obs="test_concourse_not_leftover_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-7",
            diff_obs=" ci/eval.yml | 2+-\n tests/test_concourse_branch_sha.py | 12++\n",
            residual="Fly leftover still set-pipeline -p eval.",
        ),
        _bad(
            slug="drone-branch-stale-q16x",
            domain="drone-eval",
            kind="ci",
            avoided="r420 concourse; r410 spacelift; r319 Aim hash",
            goal=(
                "Drone leftover trigger leftover/main so planted bundle-hold-6 never "
                "runs. Pin the trigger locally."
            ),
            plan="Dump .drone.yml, pin SHA, prove planted bundle-hold-6 locally.",
            outcome=(
                "Local trigger is this SHA. Planted bundle-hold-6 present locally. Handoff: "
                "the secret leftover still DRONE_BRANCH=leftover/main."
            ),
            ticket=(
                "Title: Drone leftover trigger leftover/main. planted bundle-hold-6 unused."
            ),
            src=".drone.yml",
            src_obs="trigger:\n  branch:\n    - leftover/main  # leftover",
            run="evals/drone_eval.py",
            fail_obs="trigger leftover leftover/main. planted bundle-hold-6 unused",
            inspect=".drone.yml",
            inspect_obs="leftover/main leftover",
            first_path=".drone.yml",
            first_old="- leftover/main",
            first_new="- dev",
            first_obs="dev local. secret leftover still leftover/main",
            rate_tail="secret leftover DRONE_BRANCH=leftover/main",
            still_after_429="secret leftover; planted bundle-hold-6 unused",
            grep="leftover/main|.drone.yml|goldens",
            grep_obs="cannot change secret leftover from this ticket",
            plan_change="local SHA trigger; document secret leftover leftover/main",
            fix_path=".drone.yml",
            fix_old="- dev",
            fix_new="- {{sha}}",
            fix_obs="local planted present. secret leftover HANDOFF",
            retry_obs="502 unused. secret leftover drone branch. Partial",
            test="tests/test_drone_branch_sha.py",
            test_body="xfail secret leftover leftover/main; local SHA trigger",
            test_obs="secret leftover drone branch. Partial",
            suite_obs="local SHA trigger. secret leftover leftover/main. Partial.",
            gate_obs="local SHA trigger. secret leftover leftover/main. Partial.",
            diff_obs=" .drone.yml | 2+-\n HANDOFF drone secret\n",
            residual="Secret leftover still DRONE_BRANCH=leftover/main. Partial.",
        ),
    )
)

# r421 more ci leftover
PAIRS.append(
    (
        _ok(
            slug="woodpecker-branch-stale-r17y",
            domain="woodpecker-eval",
            kind="ci",
            avoided="r420 drone; r420 concourse; r319 ClearML uri",
            goal=(
                "Woodpecker leftover when branch leftover/main so planted "
                "loyalty-hold-6 never runs. Pin the when to this SHA."
            ),
            plan="Dump .woodpecker.yml, pin SHA, prove planted loyalty-hold-6 fail.",
            outcome=(
                "when branch is this SHA. Planted loyalty-hold-6 0.13 fail-closed. Residual: "
                "a cron leftover still branch leftover/main."
            ),
            ticket=(
                "Title: Woodpecker leftover when leftover/main. planted loyalty-hold-6 unused."
            ),
            src=".woodpecker.yml",
            src_obs="when:\n  branch: leftover/main  # leftover",
            run="evals/woodpecker_eval.py",
            fail_obs="when leftover leftover/main. planted loyalty-hold-6 unused",
            inspect=".woodpecker.yml",
            inspect_obs="leftover/main leftover",
            first_path=".woodpecker.yml",
            first_old="branch: leftover/main",
            first_new="branch: dev",
            first_obs="dev local. cron leftover still leftover/main",
            rate_tail="cron leftover branch leftover/main",
            still_after_429="cron leftover; planted loyalty-hold-6 unused",
            grep="leftover/main|woodpecker|goldens",
            grep_obs="when SHA; ignore cron leftover",
            plan_change="when branch SHA; refuse leftover/main",
            fix_path=".woodpecker.yml",
            fix_old="branch: dev",
            fix_new="branch: {{sha}}",
            fix_obs="planted loyalty-hold-6 0.13. leftover/main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-6 0.13",
            test="tests/test_woodpecker_branch_sha.py",
            test_body="assert when branch is sha; leftover/main unused",
            test_obs="test_woodpecker_not_leftover_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-6",
            diff_obs=" .woodpecker.yml | 2+-\n tests/test_woodpecker_branch_sha.py | 12++\n",
            residual="Cron leftover still branch leftover/main.",
        ),
        _bad(
            slug="gitea-actions-stale-s18z",
            domain="gitea-eval",
            kind="ci",
            avoided="r421 woodpecker; r294 gha restore; r319 Aim hash",
            goal=(
                "Gitea Actions leftover on leftover/main so planted cancel-hold-6 never "
                "runs. Pin the on locally."
            ),
            plan="Dump workflow, pin SHA, prove planted cancel-hold-6 locally.",
            outcome=(
                "Local on is this SHA. Planted cancel-hold-6 present locally. Handoff: the "
                "org leftover still on leftover/main."
            ),
            ticket=(
                "Title: Gitea leftover on leftover/main. planted cancel-hold-6 unused."
            ),
            src=".gitea/workflows/eval.yml",
            src_obs="on:\n  push:\n    branches: [leftover/main]  # leftover",
            run="evals/gitea_eval.py",
            fail_obs="on leftover leftover/main. planted cancel-hold-6 unused",
            inspect=".gitea/workflows/eval.yml",
            inspect_obs="leftover/main leftover",
            first_path=".gitea/workflows/eval.yml",
            first_old="branches: [leftover/main]",
            first_new="branches: [dev]",
            first_obs="dev local. org leftover still leftover/main",
            rate_tail="org leftover on leftover/main",
            still_after_429="org leftover; planted cancel-hold-6 unused",
            grep="leftover/main|gitea/workflows|goldens",
            grep_obs="cannot change org leftover from this ticket",
            plan_change="local SHA on; document org leftover leftover/main",
            fix_path=".gitea/workflows/eval.yml",
            fix_old="branches: [dev]",
            fix_new="branches: [{{sha}}]",
            fix_obs="local planted present. org leftover HANDOFF",
            retry_obs="502 unused. org leftover leftover/main. Partial",
            test="tests/test_gitea_on_sha.py",
            test_body="xfail org leftover leftover/main; local SHA on",
            test_obs="org leftover leftover/main. Partial",
            suite_obs="local SHA on. org leftover leftover/main. Partial.",
            gate_obs="local SHA on. org leftover leftover/main. Partial.",
            diff_obs=" .gitea/workflows/eval.yml | 2+-\n HANDOFF gitea org\n",
            residual="Org leftover still on leftover/main. Partial.",
        ),
    )
)

# r422 mesh leftover
PAIRS.append(
    (
        _ok(
            slug="istio-vs-stale-t19a",
            domain="istio-eval",
            kind="mesh",
            avoided="r351 envoy; r350 nginx; r319 ClearML uri",
            goal=(
                "Istio leftover VirtualService eval still routes /judge to yesterday "
                "subset so planted tax-hold-6 never reaches the new goldens. Pin subset "
                "to this SHA."
            ),
            plan="Dump VS, pin SHA subset, prove planted tax-hold-6 fail.",
            outcome=(
                "subset is eval-<sha>. Planted tax-hold-6 0.14 fail-closed. Residual: a "
                "DestinationRule leftover still subset=legacy."
            ),
            ticket=(
                "Title: Istio leftover VS subset=legacy. planted tax-hold-6 missing."
            ),
            src="evals/virtualservice.yaml",
            src_obs="subset: legacy  # leftover",
            run="evals/istio_eval.py",
            fail_obs="subset leftover legacy. planted tax-hold-6 absent",
            inspect="evals/virtualservice.yaml",
            inspect_obs="legacy leftover",
            first_path="evals/virtualservice.yaml",
            first_old="subset: legacy",
            first_new="subset: eval-dev",
            first_obs="dev local. DR leftover still subset=legacy",
            rate_tail="DR leftover subset=legacy",
            still_after_429="DR leftover; planted tax-hold-6 absent",
            grep="subset: legacy|VirtualService|goldens",
            grep_obs="subset eval-<sha>; ignore DR leftover",
            plan_change="subset eval-<sha>; refuse legacy",
            fix_path="evals/virtualservice.yaml",
            fix_old="subset: eval-dev",
            fix_new="subset: eval-{{sha}}",
            fix_obs="planted tax-hold-6 0.14 on sha subset",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-6 0.14",
            test="tests/test_istio_subset_sha.py",
            test_body="assert subset includes sha; legacy unused",
            test_obs="test_istio_not_subset_legacy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-6",
            diff_obs=" evals/virtualservice.yaml | 2+-\n tests/test_istio_subset_sha.py | 12++\n",
            residual="DestinationRule leftover still subset=legacy.",
        ),
        _bad(
            slug="linkerd-split-stale-u20b",
            domain="linkerd-eval",
            kind="mesh",
            avoided="r422 istio; r351 haproxy; r319 Aim hash",
            goal=(
                "Linkerd leftover TrafficSplit eval still backend leftover so planted "
                "sla-hold-5 never receives traffic. Pin the split locally."
            ),
            plan="Dump TrafficSplit, pin SHA, prove planted sla-hold-5 locally.",
            outcome=(
                "Local backend is eval-<sha>. Planted sla-hold-5 present locally. Handoff: "
                "the meshed leftover still backend leftover."
            ),
            ticket=(
                "Title: Linkerd leftover TrafficSplit backend leftover. planted sla-hold-5 missing."
            ),
            src="evals/trafficsplit.yaml",
            src_obs="service: leftover  # leftover",
            run="evals/linkerd_eval.py",
            fail_obs="backend leftover leftover. planted sla-hold-5 absent",
            inspect="evals/trafficsplit.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/trafficsplit.yaml",
            first_old="service: leftover",
            first_new="service: eval-dev",
            first_obs="dev local. meshed leftover still leftover",
            rate_tail="meshed leftover backend leftover",
            still_after_429="meshed leftover; planted sla-hold-5 absent",
            grep="service: leftover|TrafficSplit|goldens",
            grep_obs="cannot change meshed leftover from this ticket",
            plan_change="local backend eval-<sha>; document meshed leftover",
            fix_path="evals/trafficsplit.yaml",
            fix_old="service: eval-dev",
            fix_new="service: eval-{{sha}}",
            fix_obs="local planted present. meshed leftover HANDOFF",
            retry_obs="502 unused. meshed leftover linkerd. Partial",
            test="tests/test_linkerd_split_sha.py",
            test_body="xfail meshed leftover leftover; local eval-<sha>",
            test_obs="meshed leftover linkerd. Partial",
            suite_obs="local eval-sha. meshed leftover leftover. Partial.",
            gate_obs="local eval-sha. meshed leftover leftover. Partial.",
            diff_obs=" evals/trafficsplit.yaml | 2+-\n HANDOFF linkerd mesh\n",
            residual="Meshed leftover still backend leftover. Partial.",
        ),
    )
)

# r423 rollout leftover
PAIRS.append(
    (
        _ok(
            slug="argo-rollout-stale-v21c",
            domain="argo-rollout-eval",
            kind="mesh",
            avoided="r314 argo output; r422 istio; r319 ClearML uri",
            goal=(
                "Argo Rollouts leftover canary still stableService=eval-legacy so planted "
                "membership-hold-4 never receives canary weight. Pin the service to this SHA."
            ),
            plan="Dump Rollout, pin SHA service, prove planted membership-hold-4 fail.",
            outcome=(
                "canaryService is eval-<sha>. Planted membership-hold-4 0.12 fail-closed. "
                "Residual: an Analysis leftover still service=eval-legacy."
            ),
            ticket=(
                "Title: Argo Rollouts leftover stableService=eval-legacy. planted membership-hold-4 missing."
            ),
            src="evals/rollout.yaml",
            src_obs="stableService: eval-legacy  # leftover",
            run="evals/rollout_eval.py",
            fail_obs="legacy leftover. planted membership-hold-4 absent",
            inspect="evals/rollout.yaml",
            inspect_obs="eval-legacy leftover",
            first_path="evals/rollout.yaml",
            first_old="stableService: eval-legacy",
            first_new="stableService: eval-dev",
            first_obs="dev local. Analysis leftover still eval-legacy",
            rate_tail="Analysis leftover service=eval-legacy",
            still_after_429="Analysis leftover; planted membership-hold-4 absent",
            grep="eval-legacy|stableService|goldens",
            grep_obs="service eval-<sha>; ignore Analysis leftover",
            plan_change="canaryService eval-<sha>; refuse eval-legacy",
            fix_path="evals/rollout.yaml",
            fix_old="stableService: eval-dev",
            fix_new="canaryService: eval-{{sha}}",
            fix_obs="planted membership-hold-4 0.12 on sha service",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold-4 0.12",
            test="tests/test_argo_rollout_sha.py",
            test_body="assert canaryService includes sha; eval-legacy unused",
            test_obs="test_argo_rollout_not_legacy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-4",
            diff_obs=" evals/rollout.yaml | 4+-\n tests/test_argo_rollout_sha.py | 12++\n",
            residual="Analysis leftover still service=eval-legacy.",
        ),
        _bad(
            slug="flagger-canary-stale-w22d",
            domain="flagger-eval",
            kind="mesh",
            avoided="r423 argo-rollout; r422 linkerd; r319 Aim hash",
            goal=(
                "Flagger leftover Canary still targetRef name=eval-legacy so planted "
                "after-hold-6 never receives traffic. Pin the target locally."
            ),
            plan="Dump Canary, pin SHA, prove planted after-hold-6 locally.",
            outcome=(
                "Local targetRef is eval-<sha>. Planted after-hold-6 present locally. "
                "Handoff: the metric leftover still name=eval-legacy."
            ),
            ticket=(
                "Title: Flagger leftover targetRef eval-legacy. planted after-hold-6 missing."
            ),
            src="evals/canary.yaml",
            src_obs="targetRef:\n  name: eval-legacy  # leftover",
            run="evals/flagger_eval.py",
            fail_obs="target leftover eval-legacy. planted after-hold-6 absent",
            inspect="evals/canary.yaml",
            inspect_obs="eval-legacy leftover",
            first_path="evals/canary.yaml",
            first_old="name: eval-legacy",
            first_new="name: eval-dev",
            first_obs="dev local. metric leftover still eval-legacy",
            rate_tail="metric leftover name=eval-legacy",
            still_after_429="metric leftover; planted after-hold-6 absent",
            grep="eval-legacy|targetRef|goldens",
            grep_obs="cannot change metric leftover from this ticket",
            plan_change="local target eval-<sha>; document metric leftover legacy",
            fix_path="evals/canary.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. metric leftover HANDOFF",
            retry_obs="502 unused. metric leftover flagger legacy. Partial",
            test="tests/test_flagger_target_sha.py",
            test_body="xfail metric leftover eval-legacy; local eval-<sha>",
            test_obs="metric leftover flagger legacy. Partial",
            suite_obs="local eval-sha. metric leftover eval-legacy. Partial.",
            gate_obs="local eval-sha. metric leftover eval-legacy. Partial.",
            diff_obs=" evals/canary.yaml | 2+-\n HANDOFF flagger metric\n",
            residual="Metric leftover still name=eval-legacy. Partial.",
        ),
    )
)

# r424 prow leftover
PAIRS.append(
    (
        _ok(
            slug="prow-job-stale-x23e",
            domain="prow-eval",
            kind="ci",
            avoided="r419 jenkins; r420 concourse; r319 ClearML uri",
            goal=(
                "Prow leftover job eval still extra_refs leftover/main so planted "
                "sku-hold-4 never runs. Pin extra_refs to this SHA."
            ),
            plan="Dump prow job, pin SHA, prove planted sku-hold-4 fail.",
            outcome=(
                "extra_refs is this SHA. Planted sku-hold-4 0.15 fail-closed. Residual: a "
                "config leftover still extra_refs leftover/main."
            ),
            ticket=(
                "Title: Prow leftover extra_refs leftover/main. planted sku-hold-4 unused."
            ),
            src="config/jobs/eval.yaml",
            src_obs="base_ref: leftover/main  # leftover",
            run="evals/prow_eval.py",
            fail_obs="base_ref leftover leftover/main. planted sku-hold-4 unused",
            inspect="config/jobs/eval.yaml",
            inspect_obs="leftover/main leftover",
            first_path="config/jobs/eval.yaml",
            first_old="base_ref: leftover/main",
            first_new="base_ref: dev",
            first_obs="dev local. config leftover still leftover/main",
            rate_tail="config leftover extra_refs leftover/main",
            still_after_429="config leftover; planted sku-hold-4 unused",
            grep="leftover/main|base_ref|goldens",
            grep_obs="base_ref SHA; ignore config leftover",
            plan_change="extra_refs SHA; refuse leftover/main",
            fix_path="config/jobs/eval.yaml",
            fix_old="base_ref: dev",
            fix_new="base_ref: {{sha}}",
            fix_obs="planted sku-hold-4 0.15. leftover/main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted sku-hold-4 0.15",
            test="tests/test_prow_ref_sha.py",
            test_body="assert base_ref is sha; leftover/main unused",
            test_obs="test_prow_not_leftover_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-4",
            diff_obs=" config/jobs/eval.yaml | 2+-\n tests/test_prow_ref_sha.py | 12++\n",
            residual="Config leftover still extra_refs leftover/main.",
        ),
        _bad(
            slug="jenkinsx-pipeline-stale-y24f",
            domain="jenkinsx-eval",
            kind="ci",
            avoided="r424 prow; r419 jenkins; r319 Aim hash",
            goal=(
                "Jenkins X leftover pipeline eval still source leftover/main so planted "
                "rain-hold-8 never runs. Pin the source locally."
            ),
            plan="Dump jenkins-x.yml, pin SHA, prove planted rain-hold-8 locally.",
            outcome=(
                "Local source is this SHA. Planted rain-hold-8 present locally. Handoff: "
                "the environment leftover still leftover/main."
            ),
            ticket=(
                "Title: Jenkins X leftover source leftover/main. planted rain-hold-8 unused."
            ),
            src="jenkins-x.yml",
            src_obs="source: leftover/main  # leftover",
            run="evals/jx_eval.py",
            fail_obs="source leftover leftover/main. planted rain-hold-8 unused",
            inspect="jenkins-x.yml",
            inspect_obs="leftover/main leftover",
            first_path="jenkins-x.yml",
            first_old="source: leftover/main",
            first_new="source: dev",
            first_obs="dev local. environment leftover still leftover/main",
            rate_tail="environment leftover leftover/main",
            still_after_429="environment leftover; planted rain-hold-8 unused",
            grep="leftover/main|jenkins-x.yml|goldens",
            grep_obs="cannot change environment leftover from this ticket",
            plan_change="local SHA source; document environment leftover leftover/main",
            fix_path="jenkins-x.yml",
            fix_old="source: dev",
            fix_new="source: {{sha}}",
            fix_obs="local planted present. environment leftover HANDOFF",
            retry_obs="502 unused. environment leftover leftover/main. Partial",
            test="tests/test_jx_source_sha.py",
            test_body="xfail environment leftover leftover/main; local SHA source",
            test_obs="environment leftover leftover/main. Partial",
            suite_obs="local SHA source. environment leftover leftover/main. Partial.",
            gate_obs="local SHA source. environment leftover leftover/main. Partial.",
            diff_obs=" jenkins-x.yml | 2+-\n HANDOFF jx env\n",
            residual="Environment leftover still leftover/main. Partial.",
        ),
    )
)

# r425 spinnaker leftover
PAIRS.append(
    (
        _ok(
            slug="spinnaker-pipeline-stale-z25g",
            domain="spinnaker-eval",
            kind="ci",
            avoided="r423 argo-rollout; r419 jenkins; r319 ClearML uri",
            goal=(
                "Spinnaker leftover pipeline eval still artifact leftover/main so planted "
                "flash-hold-9 never deploys. Pin the artifact to this SHA."
            ),
            plan="Dump pipeline json, pin SHA, prove planted flash-hold-9 fail.",
            outcome=(
                "artifact is this SHA. Planted flash-hold-9 0.16 fail-closed. Residual: a "
                "trigger leftover still leftover/main."
            ),
            ticket=(
                "Title: Spinnaker leftover artifact leftover/main. planted flash-hold-9 missing."
            ),
            src="evals/spinnaker.json",
            src_obs='"version": "leftover/main"  // leftover',
            run="evals/spinnaker_eval.py",
            fail_obs="artifact leftover leftover/main. planted flash-hold-9 absent",
            inspect="evals/spinnaker.json",
            inspect_obs="leftover/main leftover",
            first_path="evals/spinnaker.json",
            first_old='"version": "leftover/main"',
            first_new='"version": "dev"',
            first_obs="dev local. trigger leftover still leftover/main",
            rate_tail="trigger leftover leftover/main",
            still_after_429="trigger leftover; planted flash-hold-9 absent",
            grep="leftover/main|spinnaker.json|goldens",
            grep_obs="artifact SHA; ignore trigger leftover",
            plan_change="artifact SHA; refuse leftover/main",
            fix_path="evals/spinnaker.json",
            fix_old='"version": "dev"',
            fix_new='"version": "{{sha}}"',
            fix_obs="planted flash-hold-9 0.16. leftover/main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-9 0.16",
            test="tests/test_spinnaker_artifact_sha.py",
            test_body="assert artifact version is sha; leftover/main unused",
            test_obs="test_spinnaker_not_leftover_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-9",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-9",
            diff_obs=" evals/spinnaker.json | 2+-\n tests/test_spinnaker_artifact_sha.py | 12++\n",
            residual="Trigger leftover still leftover/main.",
        ),
        _bad(
            slug="keel-policy-stale-a26h",
            domain="keel-eval",
            kind="ci",
            avoided="r425 spinnaker; r403 skopeo; r319 Aim hash",
            goal=(
                "Keel leftover policy eval still match tag latest so planted "
                "promo-hold-8 never deploys. Pin the match locally."
            ),
            plan="Dump keel policy, pin SHA, prove planted promo-hold-8 locally.",
            outcome=(
                "Local match is this SHA. Planted promo-hold-8 present locally. Handoff: "
                "the annotation leftover still tag=latest."
            ),
            ticket=(
                "Title: Keel leftover match tag latest. planted promo-hold-8 missing."
            ),
            src="evals/keel.yaml",
            src_obs="match:\n  tag: latest  # leftover",
            run="evals/keel_eval.py",
            fail_obs="tag leftover latest. planted promo-hold-8 absent",
            inspect="evals/keel.yaml",
            inspect_obs="latest leftover",
            first_path="evals/keel.yaml",
            first_old="tag: latest",
            first_new="tag: dev",
            first_obs="dev local. annotation leftover still latest",
            rate_tail="annotation leftover tag=latest",
            still_after_429="annotation leftover latest; planted promo-hold-8 absent",
            grep="tag: latest|keel.yaml|goldens",
            grep_obs="cannot change annotation leftover from this ticket",
            plan_change="local match SHA; document annotation leftover latest",
            fix_path="evals/keel.yaml",
            fix_old="tag: dev",
            fix_new="tag: {{sha}}",
            fix_obs="local planted present. annotation leftover HANDOFF",
            retry_obs="502 unused. annotation leftover keel latest. Partial",
            test="tests/test_keel_tag_sha.py",
            test_body="xfail annotation leftover latest; local SHA tag",
            test_obs="annotation leftover keel latest. Partial",
            suite_obs="local SHA tag. annotation leftover latest. Partial.",
            gate_obs="local SHA tag. annotation leftover latest. Partial.",
            diff_obs=" evals/keel.yaml | 2+-\n HANDOFF keel annotation\n",
            residual="Annotation leftover still tag=latest. Partial.",
        ),
    )
)

# r426 rundeck leftover
PAIRS.append(
    (
        _ok(
            slug="rundeck-job-stale-b27i",
            domain="rundeck-eval",
            kind="sched",
            avoided="r335 cron; r419 jenkins; r319 ClearML uri",
            goal=(
                "Rundeck leftover job eval still script evals/legacy.sh so planted "
                "gift-hold-8 never runs. Point the job at this SHA."
            ),
            plan="Dump job yaml, retarget, prove planted gift-hold-8 fail.",
            outcome=(
                "job script is evals/*.py. Planted gift-hold-8 0.13 fail-closed. Residual: "
                "a project leftover still job eval/legacy."
            ),
            ticket=(
                "Title: Rundeck leftover job evals/legacy.sh. planted gift-hold-8 unused."
            ),
            src="evals/rundeck-job.yaml",
            src_obs="script: evals/legacy.sh  # leftover",
            run="evals/rundeck_eval.py",
            fail_obs="legacy leftover. planted gift-hold-8 unused",
            inspect="evals/rundeck-job.yaml",
            inspect_obs="legacy leftover",
            first_path="evals/rundeck-job.yaml",
            first_old="script: evals/legacy.sh",
            first_new="script: pytest evals/*.py",
            first_obs="glob local. project leftover still eval/legacy",
            rate_tail="project leftover job eval/legacy",
            still_after_429="project leftover; planted gift-hold-8 unused",
            grep="legacy.sh|rundeck-job|goldens",
            grep_obs="glob evals/*.py; ignore project leftover",
            plan_change="job evals/*.py; refuse eval/legacy",
            fix_path="evals/rundeck-job.yaml",
            fix_old="script: pytest evals/*.py",
            fix_new="script: pytest evals/*.py  # no project leftover",
            fix_obs="planted gift-hold-8 0.13. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-8 0.13",
            test="tests/test_rundeck_not_legacy.py",
            test_body="assert job globs evals/*.py; legacy unused",
            test_obs="test_rundeck_not_legacy_sh",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-8",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-8",
            diff_obs=" evals/rundeck-job.yaml | 2+-\n tests/test_rundeck_not_legacy.py | 12++\n",
            residual="Project leftover still job eval/legacy.",
        ),
        _bad(
            slug="awx-template-stale-c28j",
            domain="awx-eval",
            kind="sched",
            avoided="r426 rundeck; r417 bolt; r319 Aim hash",
            goal=(
                "AWX leftover job template eval still playbook legacy.yml so planted "
                "bundle-hold-7 never runs. Point the template locally."
            ),
            plan="Dump template, retarget, prove planted bundle-hold-7 locally.",
            outcome=(
                "Local playbook is evals. Planted bundle-hold-7 present locally. Handoff: "
                "the org leftover still playbook legacy.yml."
            ),
            ticket=(
                "Title: AWX leftover playbook legacy.yml. planted bundle-hold-7 unused."
            ),
            src="evals/awx-template.json",
            src_obs='"playbook": "legacy.yml"  // leftover',
            run="evals/awx_eval.py",
            fail_obs="playbook leftover legacy.yml. planted bundle-hold-7 unused",
            inspect="evals/awx-template.json",
            inspect_obs="legacy.yml leftover",
            first_path="evals/awx-template.json",
            first_old='"playbook": "legacy.yml"',
            first_new='"playbook": "evals.yml"',
            first_obs="evals local. org leftover still legacy.yml",
            rate_tail="org leftover playbook legacy.yml",
            still_after_429="org leftover; planted bundle-hold-7 unused",
            grep="legacy.yml|awx-template|goldens",
            grep_obs="cannot change org leftover from this ticket",
            plan_change="local evals playbook; document org leftover legacy.yml",
            fix_path="evals/awx-template.json",
            fix_old='"playbook": "evals.yml"',
            fix_new='"playbook": "evals/*.py"',
            fix_obs="local planted present. org leftover HANDOFF",
            retry_obs="502 unused. org leftover awx legacy. Partial",
            test="tests/test_awx_not_legacy.py",
            test_body="xfail org leftover legacy.yml; local evals",
            test_obs="org leftover awx legacy. Partial",
            suite_obs="local evals. org leftover legacy.yml. Partial.",
            gate_obs="local evals. org leftover legacy.yml. Partial.",
            diff_obs=" evals/awx-template.json | 2+-\n HANDOFF awx org\n",
            residual="Org leftover still playbook legacy.yml. Partial.",
        ),
    )
)
