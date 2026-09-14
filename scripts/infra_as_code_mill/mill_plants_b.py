"""Unique leftover IaC plants r617–r624. Not r587–r608 clones."""

from __future__ import annotations

MORE: list[tuple[dict, dict, str]] = []


def _ok(**kwargs) -> dict:
    return kwargs


def _fail(**kwargs) -> dict:
    return kwargs


# ---------------------------------------------------------------------------
# r617 Bicep what-if leftover vs leftover what-if delete
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="bicep-whatif-leftover-skip",
            seed="bicep what-if treated as apply",
            fail="what-if JSON leftover; live SKU B1",
            left="what-if.json leftover on disk",
            term="success incremental create 2/2",
            arc="what-if skip 4–5; Complete mode 7; Incremental 10–11.",
            ticket="serac what-if leftover skip",
            test="tests/test_serac_web.py",
            cfg="bicep/web.bicep",
            ci="bicep/CI.md",
            goal=(
                "Land designed plant serac-prod App Service SKU P1v3 without "
                "treating az deployment group what-if leftover as apply. Do not "
                "create --mode Complete."
            ),
            plan=(
                "Prove CI skipped create because what-if.json existed; Incremental "
                "create; fixtures."
            ),
            outcome=(
                "CI treated leftover what-if.json as applied; live stayed B1. "
                "--mode Complete would delete unused NSG. Plan change: "
                "az deployment group create --mode Incremental. P1v3 landed; "
                "pytest 2/2. Residual what-if.json."
            ),
            s1_act="List bicep and leftover what-if.",
            s1_cmd="ls bicep tests; az appservice plan show -g serac-prod -n serac-web --query sku.name -o tsv; ls bicep/*.json",
            s1_obs="B1\nbicep/what-if.json\n# leftover what-if from last Friday\n",
            s2_lead="live B1 + leftover what-if",
            test_body=(
                "def test_sku(plan):\n"
                "    assert plan.sku == 'P1v3'\n"
                "def test_nsg_kept(nsg):\n"
                "    assert nsg.exists('serac-web-nsg')\n"
            ),
            s3_lead="fixture wants P1v3 and NSG",
            cfg_body="param sku string = 'P1v3'\nresource plan 'Microsoft.Web/serverfarms@2022-09-01' = { name: 'serac-web' sku: { name: sku } }\n",
            s4_lead="file SKU P1v3",
            s4_act="CI skip create because what-if leftover.",
            s4_cmd="jq -r '.status,.changes[0].changeType' bicep/what-if.json; echo CI: skip create already what-if",
            s4_obs="Succeeded\nModify\nCI: skip create already what-if\n",
            s5_lead="already skip via leftover what-if",
            s5_act="az appservice plan leftover B1.",
            s5_cmd="az appservice plan show -g serac-prod -n serac-web --query sku.name -o tsv",
            s5_obs="B1\n",
            s6_lead="SKU not landed",
            s6_obs="FF\nFAILED test_sku - B1 != P1v3\n",
            s7_lead="0/2",
            wrong="create --mode Complete",
            wrong_cmd="az deployment group create -g serac-prod --template-file bicep/web.bicep --mode Complete --what-if 2>&1 | tail -n 8",
            wrong_obs="Delete Microsoft.Network/networkSecurityGroups/serac-web-nsg\n# Complete would delete unused-from-template NSG\n",
            s8_lead="Complete would delete NSG",
            s8_act="confirm NSG still live.",
            s8_cmd="az network nsg show -g serac-prod -n serac-web-nsg --query name -o tsv",
            s8_obs="serac-web-nsg\n",
            plan_change="az deployment group create --mode Incremental; never Complete for this template.",
            ci_old="az deployment group what-if ... && echo skip create\n",
            ci_new=(
                "az deployment group create -g serac-prod --template-file bicep/web.bicep --mode Incremental\n"
                "# leftover what-if is not apply. never --mode Complete here.\n"
            ),
            s10_act="Incremental create.",
            fix_cmd="az deployment group create -g serac-prod --template-file bicep/web.bicep --mode Incremental -o json 2>&1 | tail -n 8",
            fix_obs="provisioningState: Succeeded\nsku: P1v3\n",
            s11_lead="P1v3 applied",
            pass_obs="..\n2 passed\n",
            s12_act="confirm SKU.",
            s12_cmd="az appservice plan show -g serac-prod -n serac-web --query sku.name -o tsv",
            s12_obs="P1v3\n",
            s13_lead="SKU landed",
            left_cmd="ls -l bicep/what-if.json",
            left_obs="-rw-r--r-- bicep/what-if.json\n# leftover what-if still on disk\n",
            residual="what-if.json",
            s14_act="do not apply the leftover what-if JSON.",
            s14_cmd="jq '.changes[].changeType' bicep/what-if.json",
            s14_obs="\"Modify\"\n\"Ignore\"\n",
            s15_lead="what-if leftover documented",
            rg_cmd="rg -n 'Incremental|Complete|what-if' bicep/CI.md",
            rg_obs="CI.md: --mode Incremental\nCI.md: leftover what-if is not apply\n",
            s16_lead="CI pins Incremental",
            s16_cmd="az network nsg show -g serac-prod -n serac-web-nsg --query name -o tsv",
            s16_obs="serac-web-nsg\n",
            s17_lead="NSG kept",
        ),
        _fail(
            slug="bicep-whatif-delete-leftover",
            seed="bicep leftover what-if Delete",
            fail="what-if Delete NSG leftover",
            left="serac-jobs-whatif.json Delete",
            term="partial discard what-if handoff",
            arc="Delete leftover 4; apply what-if 6; handoff 7–17.",
            ticket="serac-jobs leftover what-if Delete",
            test="tests/test_serac_jobs.py",
            cfg="bicep/jobs.bicep",
            ci="bicep/jobs-CI.md",
            goal=(
                "serac-jobs leftover what-if Delete on NSG in designed plant "
                "serac-prod must not be applied. Stop az deployment create from "
                "the leftover JSON. Handoff discard the what-if file."
            ),
            plan="Show leftover Delete; first wrong apply what-if; hand off discard.",
            outcome=(
                "leftover what-if listed Delete on serac-jobs-nsg. applying it "
                "refused. PARTIAL: leftover JSON; tests 1/2. Handoff rm "
                "serac-jobs-whatif.json; never apply Delete from leftover what-if."
            ),
            s1_act="List leftover what-if Delete.",
            s1_cmd="jq '.changes[] | {t:.resourceId,c:.changeType}' bicep/serac-jobs-whatif.json",
            s1_obs="serac-jobs-nsg Delete\nserac-jobs-plan Modify\n",
            s2_lead="Delete leftover",
            test_body=(
                "def test_nsg(nsg):\n"
                "    assert nsg.exists('serac-jobs-nsg')\n"
                "def test_no_whatif(fs):\n"
                "    assert not fs.exists('bicep/serac-jobs-whatif.json')\n"
            ),
            s3_lead="fixture wants NSG and no leftover file",
            cfg_body="// jobs plan only; NSG is out-of-band leftover from Complete what-if\n",
            s4_lead="template omits NSG",
            s4_act="CI almost apply leftover what-if.",
            s4_cmd="echo applying leftover what-if; az deployment group create -g serac-jobs --confirm-with-what-if --what-if-result-path bicep/serac-jobs-whatif.json 2>&1 | tail -n 6",
            s4_obs="Error: refused: leftover what-if contains Delete on serac-jobs-nsg\n",
            s5_lead="apply leftover blocked",
            s5_obs=".F\nFAILED test_no_whatif - leftover file present\n",
            s6_lead="1/2",
            wrong="create --mode Complete to match what-if",
            wrong_cmd="az deployment group create -g serac-jobs --template-file bicep/jobs.bicep --mode Complete --what-if 2>&1 | tail -n 6",
            wrong_obs="Delete Microsoft.Network/networkSecurityGroups/serac-jobs-nsg\n",
            handoff="rm bicep/serac-jobs-whatif.json",
            dont="apply leftover what-if Delete",
            ci_old="az deployment group create --confirm-with-what-if --what-if-result-path bicep/serac-jobs-whatif.json\n",
            ci_new=(
                "# leftover what-if Delete on NSG. Handoff: rm bicep/serac-jobs-whatif.json. "
                "never apply leftover what-if; never Complete.\n"
            ),
            left_name="serac-jobs-whatif.json",
            left_cmd="ls -l bicep/serac-jobs-whatif.json; jq -r '.changes[]|select(.changeType==\"Delete\")|.resourceId' bicep/serac-jobs-whatif.json",
            left_obs="bicep/serac-jobs-whatif.json\nserac-jobs-nsg\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="rm serac-jobs-whatif.json",
            s11_act="show leftover Delete.",
            s11_cmd="jq '.changes[]|select(.changeType==\"Delete\")' bicep/serac-jobs-whatif.json | head -n 8",
            s11_obs="changeType: Delete\nresourceId: .../serac-jobs-nsg\n",
            s12_lead="Delete leftover",
            s13_act="confirm NSG still live.",
            s13_cmd="az network nsg show -g serac-jobs -n serac-jobs-nsg --query name -o tsv",
            s13_obs="serac-jobs-nsg\n",
            s14_cmd="echo PARTIAL leftover what-if",
            s14_obs="PARTIAL leftover what-if\n",
            s15_lead="NSG kept",
            s15_cmd="echo leftover what-if file",
            s15_obs="leftover what-if file\n",
            s16_lead="file leftover",
            s16_cmd="ls bicep/serac-jobs-whatif.json",
            s16_obs="bicep/serac-jobs-whatif.json\n",
        ),
        "Bicep what-if leftover skip (SUCCESS) and leftover what-if Delete (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r618 ARM Incremental vs Complete leftover mode
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="arm-incremental-vs-complete",
            seed="ARM Complete deleted unused NSG",
            fail="Complete mode delete leftover NSG",
            left="pipeline still mentions Complete in comment",
            term="success Incremental recreate 2/2",
            arc="Complete delete 4–5; re-run Complete 7; Incremental 10–11.",
            ticket="bergschrund Complete deleted NSG",
            test="tests/test_berg_nsg.py",
            cfg="arm/web.json",
            ci=".github/workflows/arm-web.yml",
            goal=(
                "Restore designed plant bergschrund-prod NSG berg-web after ARM "
                "Complete deleted it. Do not re-run Complete. Switch pipeline to "
                "Incremental and recreate NSG."
            ),
            plan="Prove Complete deleted NSG; Incremental deploy + NSG resource; fixtures.",
            outcome=(
                "ARM --mode Complete deleted berg-web NSG not in template. Re-run "
                "Complete still Delete. Plan change: Incremental + explicit NSG. "
                "NSG recreated; pytest 2/2. Residual comment in old workflow."
            ),
            s1_act="List last deployment mode.",
            s1_cmd="az deployment group list -g berg-prod --query '[0].{m:properties.mode,s:properties.provisioningState}' -o tsv; az network nsg show -g berg-prod -n berg-web 2>&1 | tail -n 3",
            s1_obs="Complete  Succeeded\nResourceNotFound: berg-web\n",
            s2_lead="Complete leftover deleted NSG",
            test_body=(
                "def test_nsg(nsg):\n"
                "    assert nsg.exists('berg-web')\n"
                "def test_mode(wf):\n"
                "    assert 'Complete' not in wf.active_mode\n"
            ),
            s3_lead="fixture wants NSG + Incremental",
            cfg_body='{\n  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",\n  "resources": []\n}\n',
            s4_lead="template omitted NSG",
            s4_act="replay last Complete (CI).",
            s4_cmd="az deployment group create -g berg-prod --template-file arm/web.json --mode Complete 2>&1 | tail -n 8",
            s4_obs="WARNING: Complete mode. No additional deletes (NSG already gone).\nprovisioningState: Succeeded\n",
            s5_lead="Complete no-op already deleted",
            s5_act="az network nsg leftover missing.",
            s5_cmd="az network nsg list -g berg-prod --query '[].name' -o tsv",
            s5_obs="\n",
            s6_lead="NSG gone",
            s6_obs="FF\nFAILED test_nsg - missing\nFAILED test_mode - Complete in workflow\n",
            s7_lead="0/2",
            wrong="re-run Complete",
            wrong_cmd="az deployment group what-if -g berg-prod --template-file arm/web.json --mode Complete 2>&1 | tail -n 6",
            wrong_obs="No changes (NSG already deleted). Complete still the mode.\n",
            s8_lead="Complete still lethal if NSG returns",
            s8_act="read workflow mode leftover.",
            s8_cmd="rg -n 'mode:' .github/workflows/arm-web.yml",
            s8_obs="mode: Complete\n",
            plan_change="switch to Incremental; add NSG resource; never Complete.",
            ci_old="mode: Complete\n",
            ci_new="mode: Incremental\n# Complete deleted berg-web NSG; do not re-run Complete.\n",
            s10_act="Incremental create with NSG.",
            fix_cmd="az deployment group create -g berg-prod --template-file arm/web-nsg.json --mode Incremental -o json 2>&1 | tail -n 6",
            fix_obs="provisioningState: Succeeded\nberg-web NSG created\n",
            s11_lead="NSG created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm NSG.",
            s12_cmd="az network nsg show -g berg-prod -n berg-web --query name -o tsv",
            s12_obs="berg-web\n",
            s13_lead="NSG landed",
            left_cmd="rg -n Complete .github/workflows/arm-web.yml || true",
            left_obs="# Complete deleted berg-web NSG; do not re-run Complete.\n",
            residual="Complete mention in comment",
            s14_act="do not flip comment back to mode Complete.",
            s14_cmd="rg -n 'mode:' .github/workflows/arm-web.yml",
            s14_obs="mode: Incremental\n",
            s15_lead="mode Incremental",
            rg_cmd="rg -n 'Incremental|Complete' .github/workflows/arm-web.yml",
            rg_obs="mode: Incremental\n# Complete deleted berg-web NSG\n",
            s16_lead="CI pins Incremental",
            s16_cmd="az deployment group list -g berg-prod --query '[0].properties.mode' -o tsv",
            s16_obs="Incremental\n",
            s17_lead="last mode Incremental",
        ),
        _fail(
            slug="arm-complete-mode-leftover",
            seed="ARM leftover Complete in pipeline",
            fail="jobs workflow still Complete",
            left="arm-jobs.yml mode Complete",
            term="partial pin Incremental handoff",
            arc="Complete leftover 4; Complete again 6; handoff 7–17.",
            ticket="berg-jobs leftover Complete mode",
            test="tests/test_berg_jobs.py",
            cfg=".github/workflows/arm-jobs.yml",
            ci=".github/workflows/arm-jobs.yml",
            goal=(
                "berg-jobs leftover ARM Complete in designed plant bergschrund-prod "
                "pipeline still threatens unused RGs. Stop another Complete run. "
                "Handoff pin Incremental."
            ),
            plan="Show leftover Complete; first wrong Complete again; hand off pin.",
            outcome=(
                "arm-jobs.yml leftover mode Complete. Re-run would delete leftover "
                "storage. PARTIAL: workflow still Complete; tests 1/2. Handoff pin "
                "Incremental; never Complete."
            ),
            s1_act="Read leftover workflow mode.",
            s1_cmd="rg -n 'mode:' .github/workflows/arm-jobs.yml",
            s1_obs="mode: Complete\n",
            s2_lead="Complete leftover",
            test_body=(
                "def test_mode(wf):\n"
                "    assert wf.mode == 'Incremental'\n"
                "def test_sa_kept(sa):\n"
                "    assert sa.exists('bergjobsdata')\n"
            ),
            s3_lead="fixture wants Incremental + SA",
            cfg_body="on: push\njobs:\n  deploy:\n    steps:\n      - run: az deployment group create --mode Complete\n",
            s4_lead="workflow Complete",
            s4_act="what-if Complete (CI).",
            s4_cmd="az deployment group what-if -g berg-jobs --template-file arm/jobs.json --mode Complete 2>&1 | tail -n 8",
            s4_obs="Delete Microsoft.Storage/storageAccounts/bergjobsdata\n# leftover SA not in template\n",
            s5_lead="Complete would delete SA",
            s5_obs=".F\nFAILED test_mode - Complete\n",
            s6_lead="1/2",
            wrong="run Complete anyway",
            wrong_cmd="az deployment group create -g berg-jobs --template-file arm/jobs.json --mode Complete --confirm-with-what-if 2>&1 | tail -n 6",
            wrong_obs="Error: refused: what-if Delete bergjobsdata\n",
            handoff="pin workflow mode Incremental",
            dont="run Complete",
            ci_old="az deployment group create --mode Complete\n",
            ci_new=(
                "# leftover Complete would delete bergjobsdata. Handoff: pin "
                "--mode Incremental. never Complete.\n"
            ),
            left_name="arm-jobs.yml Complete",
            left_cmd="rg -n Complete .github/workflows/arm-jobs.yml",
            left_obs="# leftover Complete would delete bergjobsdata\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="pin Incremental",
            s11_act="show leftover SA still live.",
            s11_cmd="az storage account show -g berg-jobs -n bergjobsdata --query name -o tsv",
            s11_obs="bergjobsdata\n",
            s12_lead="SA leftover from Complete threat",
            s13_act="do not delete SA.",
            s13_cmd="echo leftover Complete workflow",
            s13_obs="leftover Complete workflow\n",
            s14_cmd="echo PARTIAL Complete leftover",
            s14_obs="PARTIAL Complete leftover\n",
            s15_lead="SA kept",
            s15_cmd="rg -n Incremental .github/workflows/arm-jobs.yml || echo Incremental not pinned",
            s15_obs="Incremental not pinned\n",
            s16_lead="pin missing",
            s16_cmd="echo leftover Complete",
            s16_obs="leftover Complete\n",
        ),
        "ARM Incremental vs Complete (SUCCESS) and leftover Complete mode (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r619 SAM leftover changeset / nested stack
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="sam-changeset-skip",
            seed="sam deploy skipped empty changeset",
            fail="empty changeset skip; stage leftover v1",
            left="changeset leftover id",
            term="success deploy no-fail-on-empty + stage 2/2",
            arc="empty skip 4–5; sam delete 7; no-fail + stage 10–11.",
            ticket="couloir SAM stage leftover skip",
            test="tests/test_couloir_api.py",
            cfg="sam/template.yaml",
            ci="sam/CI.md",
            goal=(
                "Land designed plant couloir-prod API Gateway stage prod via SAM "
                "without treating empty changeset as already skip. Do not sam delete "
                "the live stack."
            ),
            plan="Prove empty changeset skipped stage; sam deploy with stage; fixtures.",
            outcome=(
                "sam deploy skipped empty changeset; stage stayed v1. sam delete "
                "refused. Plan change: sam deploy --no-fail-on-empty-changeset plus "
                "explicit StageName. prod stage landed; pytest 2/2. Residual old changeset id."
            ),
            s1_act="List SAM stack and stages.",
            s1_cmd="sam list endpoints --stack-name couloir-api; aws apigateway get-stages --rest-api-id c0ul01r --query 'item[].stageName'",
            s1_obs="https://c0ul01r.execute-api.us-east-2.amazonaws.com/v1\n[\"v1\"]\n# template wants StageName prod\n",
            s2_lead="only v1 leftover",
            test_body=(
                "def test_stage(api):\n"
                "    assert 'prod' in api.stages\n"
                "def test_stack_kept(cfn):\n"
                "    assert cfn.exists('couloir-api')\n"
            ),
            s3_lead="fixture wants prod stage",
            cfg_body="Resources:\n  Api:\n    Type: AWS::Serverless::Api\n    Properties:\n      StageName: prod\n",
            s4_lead="template StageName prod",
            s4_act="sam deploy (CI empty skip).",
            s4_cmd="sam deploy --stack-name couloir-api --no-confirm-changeset 2>&1 | tail -n 10",
            s4_obs="Error: No changes to deploy. Stack couloir-api is up to date\n# already skip empty changeset; stage leftover v1\n",
            s5_lead="empty changeset skip",
            s5_act="get-stages leftover v1.",
            s5_cmd="aws apigateway get-stages --rest-api-id c0ul01r --query 'item[].stageName'",
            s5_obs='["v1"]\n',
            s6_lead="prod missing",
            s6_obs="FF\nFAILED test_stage - no prod\n",
            s7_lead="0/2",
            wrong="sam delete",
            wrong_cmd="sam delete --stack-name couloir-api --no-prompts 2>&1 | tail -n 6",
            wrong_obs="Error: refused: stack has live v1 traffic\n",
            s8_lead="delete refused",
            s8_act="sam list leftover stack.",
            s8_cmd="aws cloudformation describe-stacks --stack-name couloir-api --query 'Stacks[0].StackStatus' --output text",
            s8_obs="UPDATE_COMPLETE\n",
            plan_change="sam deploy --no-fail-on-empty-changeset with explicit Stage; never sam delete.",
            ci_old="sam deploy --stack-name couloir-api --no-confirm-changeset\n",
            ci_new=(
                "sam deploy --stack-name couloir-api --no-fail-on-empty-changeset --parameter-overrides StageName=prod\n"
                "# empty changeset already-skips new StageName.\n"
            ),
            s10_act="deploy with StageName override.",
            fix_cmd="sam deploy --stack-name couloir-api --no-fail-on-empty-changeset --parameter-overrides StageName=prod --no-confirm-changeset 2>&1 | tail -n 8",
            fix_cmd_note="deploy",
            fix_obs="Changeset created (Stage prod)\nSuccessfully created/updated stack - couloir-api\n",
            s11_lead="stage created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm prod stage.",
            s12_cmd="aws apigateway get-stages --rest-api-id c0ul01r --query 'item[].stageName'",
            s12_obs='["v1", "prod"]\n',
            s13_lead="prod landed",
            left_cmd="aws cloudformation list-change-sets --stack-name couloir-api --query 'Summaries[].ChangeSetName'",
            left_obs='["samcli-deploy-2026-08-19-empty"]\n# leftover empty changeset id\n',
            residual="empty changeset id",
            s14_act="do not execute the leftover empty changeset.",
            s14_cmd="aws cloudformation describe-change-set --stack-name couloir-api --change-set-name samcli-deploy-2026-08-19-empty --query Status --output text",
            s14_obs="FAILED\n# leftover empty\n",
            s15_lead="changeset leftover documented",
            rg_cmd="rg -n 'no-fail-on-empty|sam delete' sam/CI.md",
            rg_obs="CI.md: --no-fail-on-empty-changeset --parameter-overrides StageName=prod\n",
            s16_lead="CI pins stage",
            s16_cmd="sam list endpoints --stack-name couloir-api | rg prod",
            s16_obs="https://c0ul01r.execute-api.us-east-2.amazonaws.com/prod\n",
            s17_lead="prod endpoint",
        ),
        _fail(
            slug="sam-nested-stack-leftover",
            seed="SAM leftover nested stack",
            fail="deploy skip leftover nested",
            left="couloir-jobs-NestedStack leftover",
            term="partial nested review handoff",
            arc="nested leftover 4; delete nested 6; handoff 7–17.",
            ticket="couloir-jobs leftover nested stack",
            test="tests/test_couloir_jobs.py",
            cfg="sam/jobs.yaml",
            ci="sam/jobs-CI.md",
            goal=(
                "couloir-jobs leftover nested SAM stack in designed plant "
                "couloir-prod still blocks deploy. Stop delete-stack on the nested "
                "stack. Handoff review nested leftover."
            ),
            plan="Show leftover nested; first wrong delete nested; hand off.",
            outcome=(
                "sam deploy failed: leftover nested stack UPDATE_ROLLBACK_FAILED. "
                "delete-stack nested refused. PARTIAL: leftover nested; tests 1/2. "
                "Handoff continue-update-rollback nested or support; never delete nested blindly."
            ),
            s1_act="List leftover nested stack.",
            s1_cmd="aws cloudformation list-stack-resources --stack-name couloir-jobs --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFormation::Stack`].[LogicalResourceId,ResourceStatus]'",
            s1_obs="ServerlessDeployment   UPDATE_ROLLBACK_FAILED leftover\n",
            s2_lead="nested leftover rollback failed",
            test_body=(
                "def test_nested_ok(cfn):\n"
                "    assert cfn.nested('couloir-jobs') != 'UPDATE_ROLLBACK_FAILED'\n"
                "def test_parent_kept(cfn):\n"
                "    assert cfn.exists('couloir-jobs')\n"
            ),
            s3_lead="fixture wants nested healthy",
            cfg_body="Resources:\n  JobsFn:\n    Type: AWS::Serverless::Function\n",
            s4_lead="parent template",
            s4_act="sam deploy (CI).",
            s4_cmd="sam deploy --stack-name couloir-jobs --no-confirm-changeset 2>&1 | tail -n 8",
            s4_obs="Error: Nested stack ServerlessDeployment is UPDATE_ROLLBACK_FAILED leftover\n",
            s5_lead="deploy blocked",
            s5_obs=".F\nFAILED test_nested_ok - UPDATE_ROLLBACK_FAILED\n",
            s6_lead="1/2",
            wrong="delete-stack nested",
            wrong_cmd="aws cloudformation delete-stack --stack-name couloir-jobs-ServerlessDeployment-XXXX 2>&1 | tail -n 6",
            wrong_obs="Error: refused: nested has retain resources (S3 artifacts)\n",
            handoff="continue-update-rollback nested or open support",
            dont="delete-stack the nested stack",
            ci_old="sam deploy --stack-name couloir-jobs --no-confirm-changeset\n",
            ci_new=(
                "# leftover nested UPDATE_ROLLBACK_FAILED. Handoff: "
                "continue-update-rollback on nested. never delete-stack nested.\n"
            ),
            left_name="ServerlessDeployment nested",
            left_cmd="aws cloudformation describe-stacks --stack-name couloir-jobs --query 'Stacks[0].StackStatus' --output text",
            left_obs="UPDATE_ROLLBACK_FAILED\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="continue-update-rollback nested",
            s11_act="show leftover nested reason.",
            s11_cmd="aws cloudformation describe-stack-events --stack-name couloir-jobs --query 'StackEvents[0].ResourceStatusReason' --output text | head",
            s11_obs="Nested stack leftover S3 bucket not empty\n",
            s12_lead="bucket leftover in nested",
            s13_act="do not empty-bucket blindly.",
            s13_cmd="echo leftover nested artifacts",
            s13_obs="leftover nested artifacts\n",
            s14_cmd="echo PARTIAL nested leftover",
            s14_obs="PARTIAL nested leftover\n",
            s15_lead="parent leftover failed",
            s15_cmd="echo leftover nested stack",
            s15_obs="leftover nested stack\n",
            s16_lead="status leftover",
            s16_cmd="echo UPDATE_ROLLBACK_FAILED leftover",
            s16_obs="UPDATE_ROLLBACK_FAILED leftover\n",
        ),
        "SAM empty-changeset skip (SUCCESS) and leftover nested stack (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r620 Serverless Framework leftover
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="sls-deploy-skip",
            seed="sls deploy skipped stale hash",
            fail="no-op skip; lambda leftover old sha",
            left=".serverless zip leftover",
            term="success deploy function --force 2/2",
            arc="hash skip 4–5; sls remove 7; deploy function 10–11.",
            ticket="moraine sls hash skip",
            test="tests/test_moraine_fn.py",
            cfg="serverless.yml",
            ci="serverless-CI.md",
            goal=(
                "Land designed plant moraine-prod function handler v44 without "
                "treating sls deploy stale hash as already skip. Do not sls remove "
                "the live stack."
            ),
            plan="Prove sls deploy no-op; sls deploy function --force; fixtures.",
            outcome=(
                "sls deploy skipped (stale .serverless hash). sls remove refused. "
                "Plan change: sls deploy function -f api --force. v44 landed; "
                "pytest 2/2. Residual .serverless zip."
            ),
            s1_act="List sls service and lambda version.",
            s1_cmd="npx sls info -s prod | tail -n 8; aws lambda get-function --function-name moraine-prod-api --query 'Configuration.{r:RevisionId,s:Sha256}' --output text",
            s1_obs="functions: api\nrev-old  sha-old\n# local handler is v44\n",
            s2_lead="live leftover old sha",
            test_body=(
                "def test_sha(fn):\n"
                "    assert fn.desc.startswith('v44')\n"
                "def test_stack_kept(cfn):\n"
                "    assert cfn.exists('moraine-prod')\n"
            ),
            s3_lead="fixture wants v44",
            cfg_body="service: moraine\nfunctions:\n  api:\n    handler: src/api.handler\n    description: v44\n",
            s4_lead="yml v44",
            s4_act="sls deploy (CI already skip).",
            s4_cmd="npx sls deploy -s prod 2>&1 | tail -n 10",
            s4_obs="Service files already uploaded (hash match leftover .serverless)\n# already skip; code not pushed\n",
            s5_lead="hash already skip",
            s5_act="lambda leftover old desc.",
            s5_cmd="aws lambda get-function-configuration --function-name moraine-prod-api --query Description --output text",
            s5_obs="v41\n",
            s6_lead="still v41",
            s6_obs="FF\nFAILED test_sha - v41\n",
            s7_lead="0/2",
            wrong="sls remove",
            wrong_cmd="npx sls remove -s prod 2>&1 | tail -n 6",
            wrong_obs="Error: refused: stack has live aliases\n",
            s8_lead="remove refused",
            s8_act="sls info leftover stack.",
            s8_cmd="npx sls info -s prod | rg status",
            s8_obs="status: UPDATE_COMPLETE\n",
            plan_change="sls deploy function -f api --force; never sls remove.",
            ci_old="npx sls deploy -s prod\n",
            ci_new="npx sls deploy function -f api -s prod --force\n# stale .serverless hash already-skips code.\n",
            s10_act="deploy function --force.",
            fix_cmd="npx sls deploy function -f api -s prod --force 2>&1 | tail -n 8",
            fix_obs="Successfully updated function: api (v44)\n",
            s11_lead="v44 pushed",
            pass_obs="..\n2 passed\n",
            s12_act="confirm description.",
            s12_cmd="aws lambda get-function-configuration --function-name moraine-prod-api --query Description --output text",
            s12_obs="v44\n",
            s13_lead="v44 landed",
            left_cmd="ls -1 .serverless | head",
            left_obs="moraine.zip\ncloudformation-template-update-stack.json\n",
            residual=".serverless zip",
            s14_act="do not sls package from leftover zip only.",
            s14_cmd="stat -c '%y %n' .serverless/moraine.zip",
            s14_obs="2026-08-18 leftover zip\n",
            s15_lead="zip leftover documented",
            rg_cmd="rg -n 'deploy function|--force|sls remove' serverless-CI.md",
            rg_obs="CI.md: sls deploy function -f api --force\n",
            s16_lead="CI pins function deploy",
            s16_cmd="npx sls info -s prod | rg v44 || echo deployed v44",
            s16_obs="deployed v44\n",
            s17_lead="info ok",
        ),
        _fail(
            slug="sls-stack-leftover",
            seed="sls leftover CF stack after failed remove",
            fail="remove failed leftover bucket",
            left="moraine-jobs stack leftover",
            term="partial empty bucket then remove handoff",
            arc="remove leftover 4; delete-stack 6; handoff 7–17.",
            ticket="moraine-jobs leftover sls stack",
            test="tests/test_moraine_jobs.py",
            cfg="jobs/serverless.yml",
            ci="jobs/sls-CI.md",
            goal=(
                "moraine-jobs leftover CloudFormation stack after failed sls remove "
                "in designed plant moraine-prod still owns the bucket. Stop "
                "delete-stack. Handoff empty bucket then sls remove."
            ),
            plan="Show leftover stack; first wrong delete-stack; hand off empty+remove.",
            outcome=(
                "sls remove failed leftover S3 bucket not empty. delete-stack "
                "refused. PARTIAL: leftover stack; tests 1/2. Handoff empty "
                "moraine-jobs-artif then sls remove; never delete-stack."
            ),
            s1_act="List leftover sls stack.",
            s1_cmd="npx sls info -s jobs 2>&1 | tail -n 8; aws cloudformation describe-stacks --stack-name moraine-jobs --query 'Stacks[0].StackStatus' --output text",
            s1_obs="DELETE_FAILED leftover\n",
            s2_lead="DELETE_FAILED leftover",
            test_body=(
                "def test_gone(cfn):\n"
                "    assert not cfn.exists('moraine-jobs')\n"
                "def test_bucket_handoff(s3):\n"
                "    assert s3.exists('moraine-jobs-artif')  # empty then delete\n"
            ),
            s3_lead="fixture wants stack gone after empty",
            cfg_body="service: moraine-jobs\nprovider:\n  deploymentBucket:\n    name: moraine-jobs-artif\n",
            s4_lead="bucket leftover",
            s4_act="sls remove again (CI).",
            s4_cmd="npx sls remove -s jobs 2>&1 | tail -n 8",
            s4_obs="Error: Bucket moraine-jobs-artif is not empty leftover objects\n",
            s5_lead="remove leftover bucket",
            s5_obs=".F\nFAILED test_gone - stack exists DELETE_FAILED\n",
            s6_lead="1/2",
            wrong="delete-stack",
            wrong_cmd="aws cloudformation delete-stack --stack-name moraine-jobs 2>&1 | tail -n 6",
            wrong_obs="Error: refused: DELETE_FAILED due to non-empty bucket; delete-stack will fail again\n",
            handoff="empty moraine-jobs-artif then sls remove",
            dont="delete-stack moraine-jobs",
            ci_old="npx sls remove -s jobs\n",
            ci_new=(
                "# leftover DELETE_FAILED bucket not empty. Handoff: empty "
                "moraine-jobs-artif then sls remove. never delete-stack.\n"
            ),
            left_name="moraine-jobs stack",
            left_cmd="aws s3 ls s3://moraine-jobs-artif | head",
            left_obs="serverless/moraine-jobs/leftover.zip\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="empty bucket then sls remove",
            s11_act="show leftover stack status.",
            s11_cmd="aws cloudformation describe-stacks --stack-name moraine-jobs --query 'Stacks[0].StackStatus' --output text",
            s11_obs="DELETE_FAILED\n",
            s12_lead="DELETE_FAILED leftover",
            s13_act="do not rm leftover zip via delete-stack.",
            s13_cmd="echo leftover artif objects",
            s13_obs="leftover artif objects\n",
            s14_cmd="echo PARTIAL sls stack leftover",
            s14_obs="PARTIAL sls stack leftover\n",
            s15_lead="bucket leftover",
            s15_cmd="echo leftover stack+bucket",
            s15_obs="leftover stack+bucket\n",
            s16_lead="status leftover",
            s16_cmd="echo DELETE_FAILED leftover",
            s16_obs="DELETE_FAILED leftover\n",
        ),
        "Serverless Framework hash skip (SUCCESS) and leftover DELETE_FAILED stack (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r621 CDKTF leftover synth / state
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="cdktf-synth-skip",
            seed="cdktf deploy skipped stale synth",
            fail="no-op vs stale cdktf.out; queue leftover 0",
            left="cdktf.out leftover json",
            term="success synth then deploy 2/2",
            arc="stale synth skip 4–5; cdktf destroy 7; synth+deploy 10–11.",
            ticket="outwash cdktf stale synth skip",
            test="tests/test_outwash_q.py",
            cfg="cdktf/main.ts",
            ci="cdktf/CI.md",
            goal=(
                "Land designed plant outwash-prod SQS outwash-jobs via CDKTF without "
                "treating stale cdktf.out as already skip. Do not cdktf destroy the "
                "stack."
            ),
            plan="Prove deploy no-op vs stale synth; cdktf synth then deploy; fixtures.",
            outcome=(
                "cdktf deploy skipped: stale cdktf.out had no queue. destroy refused. "
                "Plan change: cdktf synth && cdktf deploy. Queue landed; pytest 2/2. "
                "Residual old synth json."
            ),
            s1_act="List cdktf.out and AWS queue.",
            s1_cmd="ls cdktf.out/stacks; aws sqs get-queue-url --queue-name outwash-jobs 2>&1 | tail -n 3; npx cdktf diff outwash 2>&1 | tail -n 8",
            s1_obs="outwash\nNonExistentQueue\nNo changes (stale synth)\n",
            s2_lead="stale synth no-op",
            test_body=(
                "def test_queue(sqs):\n"
                "    assert sqs.exists('outwash-jobs')\n"
                "def test_stack_kept(tf):\n"
                "    assert tf.stack == 'outwash'\n"
            ),
            s3_lead="fixture wants queue",
            cfg_body="new SqsQueue(this, 'jobs', { name: 'outwash-jobs' });\n// added after last synth\n",
            s4_lead="source has queue",
            s4_act="cdktf deploy (CI already skip).",
            s4_cmd="npx cdktf deploy outwash --auto-approve 2>&1 | tail -n 8",
            s4_obs="No changes. Infrastructure is up-to-date.\n# leftover synth omitted the queue\n",
            s5_lead="deploy already skip",
            s5_act="queue leftover missing.",
            s5_cmd="aws sqs list-queues --queue-name-prefix outwash",
            s5_obs="{}\n",
            s6_lead="queue missing",
            s6_obs="FF\nFAILED test_queue - missing\n",
            s7_lead="0/2",
            wrong="cdktf destroy",
            wrong_cmd="npx cdktf destroy outwash --auto-approve 2>&1 | tail -n 6",
            wrong_obs="Error: refused: stack has protected remote state\n",
            s8_lead="destroy refused",
            s8_act="show leftover synth date.",
            s8_cmd="stat -c '%y %n' cdktf.out/stacks/outwash/cdk.tf.json",
            s8_obs="2026-08-10 leftover synth\n",
            plan_change="cdktf synth then deploy; never destroy for a missing resource.",
            ci_old="npx cdktf deploy outwash --auto-approve\n",
            ci_new="npx cdktf synth && npx cdktf deploy outwash --auto-approve\n# stale cdktf.out already-skips new constructs.\n",
            s10_act="synth then deploy.",
            fix_cmd="npx cdktf synth && npx cdktf deploy outwash --auto-approve 2>&1 | tail -n 8",
            fix_obs="Synthed outwash\naws_sqs_queue.jobs created\n",
            s11_lead="queue created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm queue.",
            s12_cmd="aws sqs get-queue-url --queue-name outwash-jobs --query QueueUrl --output text",
            s12_obs="https://sqs.us-east-2.amazonaws.com/404142434445/outwash-jobs\n",
            s13_lead="queue landed",
            left_cmd="ls cdktf.out/stacks/outwash | rg 'cdk.tf|tfstate'",
            left_obs="cdk.tf.json\nterraform.tfstate leftover from synth dir\n",
            residual="cdktf.out json+tfstate",
            s14_act="do not rm -rf cdktf.out.",
            s14_cmd="echo leftover synth dir kept",
            s14_obs="leftover synth dir kept\n",
            s15_lead="out leftover documented",
            rg_cmd="rg -n 'cdktf synth|destroy' cdktf/CI.md",
            rg_obs="CI.md: cdktf synth && cdktf deploy\n",
            s16_lead="CI pins synth",
            s16_cmd="npx cdktf diff outwash 2>&1 | tail -n 4",
            s16_obs="No changes\n",
            s17_lead="diff empty",
        ),
        _fail(
            slug="cdktf-out-state-leftover",
            seed="CDKTF leftover terraform state in cdktf.out",
            fail="deploy used leftover local state",
            left="cdktf.out terraform.tfstate leftover",
            term="partial state pull handoff",
            arc="local leftover 4; rm -rf out 6; handoff 7–17.",
            ticket="outwash-edge leftover cdktf state",
            test="tests/test_outwash_edge.py",
            cfg="cdktf/edge.ts",
            ci="cdktf/edge-CI.md",
            goal=(
                "outwash-edge leftover terraform.tfstate in cdktf.out in designed "
                "plant outwash-prod still shadows remote. Stop rm -rf cdktf.out. "
                "Handoff state pull first."
            ),
            plan="Show leftover local state; first wrong rm -rf; hand off state pull.",
            outcome=(
                "cdktf deploy used leftover local tfstate (would recreate). rm -rf "
                "refused (contains state). PARTIAL: leftover local state; tests 1/2. "
                "Handoff terraform state pull; never rm -rf cdktf.out."
            ),
            s1_act="List leftover local state.",
            s1_cmd="ls cdktf.out/stacks/outwash-edge; terraform -chdir=cdktf.out/stacks/outwash-edge state list | head",
            s1_obs="cdk.tf.json  terraform.tfstate leftover\naws_lb.edge\n",
            s2_lead="local leftover state",
            test_body=(
                "def test_remote(tf):\n"
                "    assert tf.backend == 's3'\n"
                "def test_no_local(fs):\n"
                "    assert not fs.exists('cdktf.out/stacks/outwash-edge/terraform.tfstate')\n"
            ),
            s3_lead="fixture wants remote only",
            cfg_body="// edge stack; backend s3; leftover local tfstate from a laptop synth\n",
            s4_lead="backend should be s3",
            s4_act="cdktf deploy (CI on leftover local).",
            s4_cmd="npx cdktf deploy outwash-edge --auto-approve 2>&1 | tail -n 8",
            s4_obs="Using local state leftover (cdktf.out)\nPlan: 6 to add  # would duplicate live ALB\nError: refused wrapper: local leftover vs remote\n",
            s5_lead="local leftover blocked",
            s5_obs=".F\nFAILED test_no_local - leftover tfstate\n",
            s6_lead="1/2",
            wrong="rm -rf cdktf.out",
            wrong_cmd="rm -rf cdktf.out 2>&1 | tail -n 4",
            wrong_obs="Error: refused: cdktf.out contains terraform.tfstate leftover\n",
            handoff="terraform state pull from remote; then drop local file",
            dont="rm -rf cdktf.out",
            ci_old="npx cdktf deploy outwash-edge --auto-approve\n",
            ci_new=(
                "# leftover local tfstate in cdktf.out. Handoff: terraform state pull. "
                "never rm -rf cdktf.out.\n"
            ),
            left_name="cdktf.out terraform.tfstate",
            left_cmd="ls -l cdktf.out/stacks/outwash-edge/terraform.tfstate",
            left_obs="-rw------- leftover local state\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="terraform state pull",
            s11_act="show leftover backend.",
            s11_cmd="rg backend cdktf.out/stacks/outwash-edge/cdk.tf.json | head",
            s11_obs='"backend": "local" leftover\n',
            s12_lead="backend leftover local",
            s13_act="do not apply local leftover.",
            s13_cmd="echo leftover local state",
            s13_obs="leftover local state\n",
            s14_cmd="echo PARTIAL cdktf state leftover",
            s14_obs="PARTIAL cdktf state leftover\n",
            s15_lead="file leftover",
            s15_cmd="echo leftover tfstate",
            s15_obs="leftover tfstate\n",
            s16_lead="status leftover",
            s16_cmd="echo local leftover",
            s16_obs="local leftover\n",
        ),
        "CDKTF stale synth skip (SUCCESS) and leftover local state (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r622 Pulumi YAML leftover stack config
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="pulumi-yaml-config-skip",
            seed="Pulumi.yaml skipped leftover prod config",
            fail="config leftover skipped new Redis",
            left="Pulumi.prod.yaml.bak leftover",
            term="success config rm leftover 2/2",
            arc="config skip 4–5; stack init 7; config rm 10–11.",
            ticket="till Pulumi.yaml leftover config skip",
            test="tests/test_till_redis.py",
            cfg="Pulumi.yaml",
            ci="Pulumi-CI.md",
            goal=(
                "Land designed plant till-prod Redis till-cache from Pulumi.yaml "
                "without leftover Pulumi.prod.yaml config already-skipping the "
                "resource. Do not pulumi stack init a second stack."
            ),
            plan="Prove leftover config skipped Redis; pulumi config rm; up; fixtures.",
            outcome=(
                "pulumi up skipped Redis because leftover Pulumi.prod.yaml set "
                "skipRedis: true. stack init refused. Plan change: pulumi config "
                "rm skipRedis. Redis landed; pytest 2/2. Residual Pulumi.prod.yaml.bak."
            ),
            s1_act="List Pulumi yaml and config.",
            s1_cmd="ls Pulumi.yaml Pulumi.prod.yaml; pulumi config -s prod | rg skip",
            s1_obs="skipRedis: true leftover\n",
            s2_lead="leftover skipRedis",
            test_body=(
                "def test_redis(r):\n"
                "    assert r.exists('till-cache')\n"
                "def test_no_skip(cfg):\n"
                "    assert 'skipRedis' not in cfg\n"
            ),
            s3_lead="fixture wants Redis",
            cfg_body="name: till\nruntime: yaml\nresources:\n  cache:\n    type: aws:elasticache:Cluster\n    properties:\n      clusterId: till-cache\n",
            s4_lead="yaml declares Redis",
            s4_act="pulumi up (CI already skip).",
            s4_cmd="pulumi up -s prod --yes --non-interactive 2>&1 | tail -n 10",
            s4_obs="Resources: 0 created (skipRedis leftover true)\n# already skip Redis\n",
            s5_lead="up already skip",
            s5_act="elasticache leftover missing.",
            s5_cmd="aws elasticache describe-cache-clusters --cache-cluster-id till-cache 2>&1 | tail -n 4",
            s5_obs="CacheClusterNotFound\n",
            s6_lead="Redis missing",
            s6_obs="FF\nFAILED test_redis - missing\nFAILED test_no_skip - skipRedis leftover\n",
            s7_lead="0/2",
            wrong="pulumi stack init",
            wrong_cmd="pulumi stack init prod-2 2>&1 | tail -n 6",
            wrong_obs="Error: refused: do not init a second stack for leftover config\n",
            s8_lead="init refused",
            s8_act="show leftover Pulumi.prod.yaml.",
            s8_cmd="rg skipRedis Pulumi.prod.yaml",
            s8_obs="skipRedis: true\n",
            plan_change="pulumi config rm skipRedis; never stack init prod-2.",
            ci_old="pulumi up -s prod --yes\n",
            ci_new="pulumi config rm skipRedis -s prod && pulumi up -s prod --yes\n# leftover YAML config already-skips resources.\n",
            s10_act="config rm then up.",
            fix_cmd="pulumi config rm skipRedis -s prod && pulumi up -s prod --yes --non-interactive 2>&1 | tail -n 8",
            fix_obs="skipRedis removed\naws:elasticache:Cluster cache created till-cache\n",
            s11_lead="Redis created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm cluster.",
            s12_cmd="aws elasticache describe-cache-clusters --cache-cluster-id till-cache --query 'CacheClusters[0].CacheClusterId' --output text",
            s12_obs="till-cache\n",
            s13_lead="Redis landed",
            left_cmd="ls Pulumi.prod.yaml.bak 2>/dev/null || ls Pulumi.prod.yaml*",
            left_obs="Pulumi.prod.yaml.bak\n# leftover backup still has skipRedis\n",
            residual="Pulumi.prod.yaml.bak",
            s14_act="do not restore the bak.",
            s14_cmd="rg skipRedis Pulumi.prod.yaml.bak",
            s14_obs="skipRedis: true\n",
            s15_lead="bak leftover documented",
            rg_cmd="rg -n 'skipRedis|stack init' Pulumi-CI.md Pulumi.prod.yaml",
            rg_obs="Pulumi-CI.md: pulumi config rm skipRedis\n",
            s16_lead="CI pins config rm",
            s16_cmd="pulumi config -s prod | rg skip || echo no skipRedis",
            s16_obs="no skipRedis\n",
            s17_lead="config clean",
        ),
        _fail(
            slug="pulumi-yaml-stackfile-leftover",
            seed="Pulumi leftover staging YAML merge",
            fail="staging yaml leftover merged",
            left="Pulumi.staging.yaml leftover",
            term="partial drop staging yaml handoff",
            arc="merge leftover 4; rm Pulumi.yaml 6; handoff 7–17.",
            ticket="till-jobs leftover staging yaml",
            test="tests/test_till_jobs.py",
            cfg="Pulumi.staging.yaml",
            ci="jobs/Pulumi-CI.md",
            goal=(
                "till-jobs leftover Pulumi.staging.yaml in designed plant till-prod "
                "still merges skipJobs. Stop rm Pulumi.yaml. Handoff drop the "
                "staging file only."
            ),
            plan="Show leftover staging yaml; first wrong rm Pulumi.yaml; hand off.",
            outcome=(
                "pulumi up merged leftover Pulumi.staging.yaml skipJobs. rm "
                "Pulumi.yaml refused. PARTIAL: leftover staging file; tests 1/2. "
                "Handoff rm Pulumi.staging.yaml; never rm Pulumi.yaml."
            ),
            s1_act="List leftover staging yaml.",
            s1_cmd="ls Pulumi.yaml Pulumi.staging.yaml; pulumi config -s jobs | rg skip",
            s1_obs="skipJobs: true leftover from staging merge\n",
            s2_lead="staging leftover merged",
            test_body=(
                "def test_no_staging(fs):\n"
                "    assert not fs.exists('Pulumi.staging.yaml')\n"
                "def test_program_kept(fs):\n"
                "    assert fs.exists('Pulumi.yaml')\n"
            ),
            s3_lead="fixture wants staging gone",
            cfg_body="config:\n  skipJobs: true\n# leftover staging stack file\n",
            s4_lead="staging skipJobs",
            s4_act="pulumi up -s jobs (CI).",
            s4_cmd="pulumi up -s jobs --yes --non-interactive 2>&1 | tail -n 8",
            s4_obs="Resources: 0 created (skipJobs leftover true from Pulumi.staging.yaml)\n",
            s5_lead="merge leftover skip",
            s5_obs=".F\nFAILED test_no_staging - Pulumi.staging.yaml present\n",
            s6_lead="1/2",
            wrong="rm Pulumi.yaml",
            wrong_cmd="rm Pulumi.yaml 2>&1 | tail -n 4",
            wrong_obs="Error: refused: Pulumi.yaml is the program\n",
            handoff="rm Pulumi.staging.yaml only",
            dont="rm Pulumi.yaml",
            ci_old="pulumi up -s jobs --yes\n",
            ci_new=(
                "# leftover Pulumi.staging.yaml merges skipJobs. Handoff: rm "
                "Pulumi.staging.yaml. never rm Pulumi.yaml.\n"
            ),
            left_name="Pulumi.staging.yaml",
            left_cmd="ls -l Pulumi.staging.yaml; rg skipJobs Pulumi.staging.yaml",
            left_obs="-rw-r--r-- Pulumi.staging.yaml\nskipJobs: true\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="rm Pulumi.staging.yaml",
            s11_act="show leftover merge.",
            s11_cmd="pulumi config -s jobs --show-secrets=false | rg skip",
            s11_obs="skipJobs: true\n",
            s12_lead="config leftover",
            s13_act="do not stack rm jobs.",
            s13_cmd="echo leftover staging yaml",
            s13_obs="leftover staging yaml\n",
            s14_cmd="echo PARTIAL staging yaml leftover",
            s14_obs="PARTIAL staging yaml leftover\n",
            s15_lead="program kept",
            s15_cmd="ls Pulumi.yaml",
            s15_obs="Pulumi.yaml\n",
            s16_lead="yaml leftover",
            s16_cmd="echo leftover Pulumi.staging.yaml",
            s16_obs="leftover Pulumi.staging.yaml\n",
        ),
        "Pulumi YAML leftover config skip (SUCCESS) and leftover staging stackfile (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r623 Packer already skip -except vs leftover AMI
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="packer-except-skip",
            seed="packer -except skipped amazon-ebs",
            fail="-except skip; AMI leftover old",
            left="old AMI leftover listed",
            term="success build without -except 2/2",
            arc="except skip 4–5; packer build -force 7; drop except 10–11.",
            ticket="loess packer -except skip",
            test="tests/test_loess_ami.py",
            cfg="packer/web.pkr.hcl",
            ci="packer/CI.md",
            goal=(
                "Land designed plant loess-prod AMI loess-web-44 without treating "
                "packer build -except amazon-ebs as already skip. Do not packer "
                "build -force the skipped source."
            ),
            plan="Prove -except skipped ebs; drop -except; build; fixtures.",
            outcome=(
                "packer build -except=amazon-ebs skipped the needed source. "
                "-force still skipped. Plan change: packer build without -except. "
                "ami-0loess44 landed; pytest 2/2. Residual old AMI listed."
            ),
            s1_act="List packer sources and AMIs.",
            s1_cmd="rg source packer/web.pkr.hcl; aws ec2 describe-images --owners self --filters Name=name,Values=loess-web-* --query 'Images[].{n:Name,i:ImageId}'",
            s1_obs='source "amazon-ebs" "web"\nloess-web-41 ami-0old41 leftover\n',
            s2_lead="old AMI leftover",
            test_body=(
                "def test_ami(ec2):\n"
                "    assert ec2.ami_name('loess-web-44').startswith('loess-web-44')\n"
                "def test_not_except(ci):\n"
                "    assert '-except' not in ci.packer_cmd\n"
            ),
            s3_lead="fixture wants 44",
            cfg_body='source "amazon-ebs" "web" {\n  ami_name = "loess-web-44"\n}\nbuild { sources = ["source.amazon-ebs.web"] }\n',
            s4_lead="hcl wants 44",
            s4_act="packer build -except (CI already skip).",
            s4_cmd="packer build -except=amazon-ebs packer/web.pkr.hcl 2>&1 | tail -n 8",
            s4_obs="Skipping source amazon-ebs.web (-except leftover)\nBuilds finished. 0 AMIs.\n",
            s5_lead="except already skip",
            s5_act="AMI leftover only 41.",
            s5_cmd="aws ec2 describe-images --owners self --filters Name=name,Values=loess-web-44 --query 'Images' --output text",
            s5_obs="None\n",
            s6_lead="44 missing",
            s6_obs="FF\nFAILED test_ami - missing 44\nFAILED test_not_except - -except in CI\n",
            s7_lead="0/2",
            wrong="packer build -force still with -except",
            wrong_cmd="packer build -force -except=amazon-ebs packer/web.pkr.hcl 2>&1 | tail -n 6",
            wrong_obs="Skipping source amazon-ebs.web\n# -force does not override -except\n",
            s8_lead="force still skipped",
            s8_act="confirm no 44.",
            s8_cmd="echo leftover ami-0old41 only",
            s8_obs="leftover ami-0old41 only\n",
            plan_change="packer build without -except; never -except amazon-ebs.",
            ci_old="packer build -except=amazon-ebs packer/web.pkr.hcl\n",
            ci_new="packer build packer/web.pkr.hcl\n# -except already-skips the needed ebs source.\n",
            s10_act="build without except.",
            fix_cmd="packer build packer/web.pkr.hcl 2>&1 | tail -n 8",
            fix_obs="==> amazon-ebs.web: AMIs were created:\nami-0loess44 (loess-web-44)\n",
            s11_lead="AMI created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm AMI.",
            s12_cmd="aws ec2 describe-images --image-ids ami-0loess44 --query 'Images[0].Name' --output text",
            s12_obs="loess-web-44\n",
            s13_lead="44 landed",
            left_cmd="aws ec2 describe-images --owners self --filters Name=name,Values=loess-web-41 --query 'Images[0].ImageId' --output text",
            left_obs="ami-0old41\n# leftover old AMI\n",
            residual="ami-0old41",
            s14_act="do not deregister all AMIs.",
            s14_cmd="echo leftover ami-0old41 keep until pin",
            s14_obs="leftover ami-0old41 keep until pin\n",
            s15_lead="old AMI leftover documented",
            rg_cmd="rg -n 'except|packer build' packer/CI.md",
            rg_obs="CI.md: packer build packer/web.pkr.hcl\n",
            s16_lead="CI drops except",
            s16_cmd="echo ami-0loess44 live",
            s16_obs="ami-0loess44 live\n",
            s17_lead="new AMI live",
        ),
        _fail(
            slug="packer-ami-leftover",
            seed="packer leftover AMI from skipped source",
            fail="deregister-all threat leftover AMI",
            left="ami-0jobsold leftover",
            term="partial deregister leftover only handoff",
            arc="leftover AMI 4; deregister all 6; handoff 7–17.",
            ticket="loess-jobs leftover AMI",
            test="tests/test_loess_jobs.py",
            cfg="packer/jobs.pkr.hcl",
            ci="packer/jobs-CI.md",
            goal=(
                "loess-jobs leftover AMI ami-0jobsold in designed plant loess-prod "
                "from a skipped source still tagged latest. Stop deregister-all. "
                "Handoff deregister leftover only."
            ),
            plan="Show leftover AMI; first wrong deregister all; hand off one AMI.",
            outcome=(
                "leftover ami-0jobsold tagged latest after skipped source. "
                "deregister-all refused. PARTIAL: leftover AMI; tests 1/2. "
                "Handoff deregister ami-0jobsold only; never deregister-all."
            ),
            s1_act="List leftover AMIs.",
            s1_cmd="aws ec2 describe-images --owners self --filters Name=tag:role,Values=loess-jobs --query 'Images[].{n:Name,i:ImageId,t:Tags}'",
            s1_obs="loess-jobs-old ami-0jobsold latest leftover\nloess-jobs-44 ami-0jobs44\n",
            s2_lead="leftover latest tag on old",
            test_body=(
                "def test_latest(ec2):\n"
                "    assert ec2.ami_by_tag('latest') == 'ami-0jobs44'\n"
                "def test_new_kept(ec2):\n"
                "    assert ec2.exists('ami-0jobs44')\n"
            ),
            s3_lead="fixture wants latest=44",
            cfg_body="# leftover skipped docker source still published ami-0jobsold\n",
            s4_lead="old tagged latest",
            s4_act="packer build jobs (CI).",
            s4_cmd="packer build packer/jobs.pkr.hcl 2>&1 | tail -n 8",
            s4_obs="Skipping leftover docker source (already used)\n# latest tag still ami-0jobsold\n",
            s5_lead="skip leftover tag",
            s5_obs=".F\nFAILED test_latest - ami-0jobsold\n",
            s6_lead="1/2",
            wrong="deregister all self AMIs",
            wrong_cmd="echo aws ec2 deregister-image --image-id ALL 2>&1 | tail",
            wrong_obs="Error: refused: would deregister ami-0jobs44 live\n",
            handoff="deregister ami-0jobsold only; retag latest",
            dont="deregister-all",
            ci_old="packer build packer/jobs.pkr.hcl\n",
            ci_new=(
                "# leftover ami-0jobsold tagged latest. Handoff: deregister "
                "ami-0jobsold only. never deregister-all.\n"
            ),
            left_name="ami-0jobsold",
            left_cmd="aws ec2 describe-images --image-ids ami-0jobsold --query 'Images[0].Name' --output text",
            left_obs="loess-jobs-old\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="deregister ami-0jobsold",
            s11_act="show leftover tags.",
            s11_cmd="aws ec2 describe-tags --filters Name=resource-id,Values=ami-0jobsold --query 'Tags[].{k:Key,v:Value}'",
            s11_obs="latest true leftover\n",
            s12_lead="latest leftover on old",
            s13_act="do not deregister ami-0jobs44.",
            s13_cmd="echo leftover ami-0jobsold only",
            s13_obs="leftover ami-0jobsold only\n",
            s14_cmd="echo PARTIAL AMI leftover",
            s14_obs="PARTIAL AMI leftover\n",
            s15_lead="new AMI kept",
            s15_cmd="echo ami-0jobs44 kept",
            s15_obs="ami-0jobs44 kept\n",
            s16_lead="old leftover",
            s16_cmd="echo leftover latest tag",
            s16_obs="leftover latest tag\n",
        ),
        "Packer -except already skip (SUCCESS) and leftover AMI (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r624 Nomad system job already skip vs leftover canary
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="nomad-system-skip",
            seed="nomad job run skipped system already used",
            fail="system skip; canary leftover old",
            left="old eval leftover",
            term="success job run -check-index 2/2",
            arc="system skip 4–5; stop -purge 7; check-index 10–11.",
            ticket="yardang nomad system already used",
            test="tests/test_yardang_job.py",
            cfg="nomad/web.nomad.hcl",
            ci="nomad/CI.md",
            goal=(
                "Land designed plant yardang-prod nomad job web v9 without treating "
                "system job already used as skip. Do not nomad job stop -purge."
            ),
            plan="Prove job run skipped; nomad job run -check-index; fixtures.",
            outcome=(
                "nomad job run skipped: system job web already used. stop -purge "
                "refused. Plan change: nomad job run -check-index. v9 running; "
                "pytest 2/2. Residual old eval."
            ),
            s1_act="List nomad job and allocs.",
            s1_cmd="nomad job status web | head -n 16; nomad job inspect web | rg 'Version|Type'",
            s1_obs="Type = system\nVersion = 7\n# file wants Version 9 / type service\n",
            s2_lead="system leftover v7",
            test_body=(
                "def test_ver(j):\n"
                "    assert j.version == 9 and j.type == 'service'\n"
                "def test_not_purged(j):\n"
                "    assert j.status == 'running'\n"
            ),
            s3_lead="fixture wants v9 service",
            cfg_body='job "web" {\n  type = "service"\n  group "g" { count = 2 }\n}\n',
            s4_lead="file type service",
            s4_act="nomad job run (CI already used skip).",
            s4_cmd="nomad job run nomad/web.nomad.hcl 2>&1 | tail -n 8",
            s4_obs="Job 'web' is already used as type=system; skipped registration\n# already skip\n",
            s5_lead="already used system skip",
            s5_act="status leftover v7 system.",
            s5_cmd="nomad job inspect web | rg 'Type|Version'",
            s5_obs="Type = system\nVersion = 7\n",
            s6_lead="still system v7",
            s6_obs="FF\nFAILED test_ver - 7/system\n",
            s7_lead="0/2",
            wrong="nomad job stop -purge",
            wrong_cmd="nomad job stop -purge web 2>&1 | tail -n 6",
            wrong_obs="Error: refused: purge would drop live system allocs on every node\n",
            s8_lead="purge refused",
            s8_act="alloc leftover still running.",
            s8_cmd="nomad job allocs web | head",
            s8_obs="a1 running system leftover\n",
            plan_change="nomad job run -check-index after deregister without purge; never -purge.",
            ci_old="nomad job run nomad/web.nomad.hcl\n",
            ci_new=(
                "nomad job stop web && nomad job run -check-index 0 nomad/web.nomad.hcl\n"
                "# system already-used skip; never stop -purge.\n"
            ),
            s10_act="stop without purge then run.",
            fix_cmd="nomad job stop web && nomad job run -check-index 0 nomad/web.nomad.hcl 2>&1 | tail -n 8",
            fix_obs="Job stopped (kept history)\nEvaluation eval-9 created (service v9)\n",
            s11_lead="v9 registered",
            pass_obs="..\n2 passed\n",
            s12_act="confirm type/version.",
            s12_cmd="nomad job inspect web | rg 'Type|Version'",
            s12_obs="Type = service\nVersion = 9\n",
            s13_lead="v9 landed",
            left_cmd="nomad eval list -job web | head",
            left_obs="eval-7 complete leftover\neval-9 complete\n",
            residual="old eval-7",
            s14_act="do not nomad system gc eval-7 blindly.",
            s14_cmd="echo leftover eval-7",
            s14_obs="leftover eval-7\n",
            s15_lead="eval leftover documented",
            rg_cmd="rg -n 'check-index|purge' nomad/CI.md",
            rg_obs="CI.md: nomad job run -check-index 0\nCI.md: never stop -purge\n",
            s16_lead="CI pins check-index",
            s16_cmd="nomad job status web | rg running",
            s16_obs="running\n",
            s17_lead="job running",
        ),
        _fail(
            slug="nomad-canary-leftover",
            seed="nomad leftover canary alloc",
            fail="canary leftover after skip promote",
            left="alloc canary leftover",
            term="partial alloc stop handoff",
            arc="canary leftover 4; system gc 6; handoff 7–17.",
            ticket="yardang-jobs leftover canary",
            test="tests/test_yardang_jobs.py",
            cfg="nomad/jobs.nomad.hcl",
            ci="nomad/jobs-CI.md",
            goal=(
                "yardang-jobs leftover canary alloc in designed plant yardang-prod "
                "still serving 10%. Stop nomad system gc. Handoff nomad alloc stop "
                "the leftover canary."
            ),
            plan="Show leftover canary; first wrong system gc; hand off alloc stop.",
            outcome=(
                "job run skipped promote; leftover canary alloc. system gc refused. "
                "PARTIAL: leftover canary; tests 1/2. Handoff nomad alloc stop "
                "canary; never system gc."
            ),
            s1_act="List leftover canary.",
            s1_cmd="nomad job allocs jobs | rg canary; nomad job status jobs | rg Canary",
            s1_obs="alloc-can leftover running 10%\nCanary = 1 leftover\n",
            s2_lead="canary leftover",
            test_body=(
                "def test_no_canary(j):\n"
                "    assert j.canary == 0\n"
                "def test_job_kept(j):\n"
                "    assert j.status == 'running'\n"
            ),
            s3_lead="fixture wants no canary",
            cfg_body='job "jobs" {\n  update { canary = 0 }\n}\n',
            s4_lead="file canary 0",
            s4_act="nomad job run (CI already skip promote).",
            s4_cmd="nomad job run nomad/jobs.nomad.hcl 2>&1 | tail -n 8",
            s4_obs="Job updated. Canary leftover not promoted (already skip auto_promote=false)\n",
            s5_lead="promote skipped leftover",
            s5_obs=".F\nFAILED test_no_canary - 1 leftover\n",
            s6_lead="1/2",
            wrong="nomad system gc",
            wrong_cmd="nomad system gc 2>&1 | tail -n 6",
            wrong_obs="Error: refused: gc does not stop live canary allocs; would only drop dead evals\n",
            handoff="nomad alloc stop leftover canary",
            dont="nomad system gc",
            ci_old="nomad job run nomad/jobs.nomad.hcl\n",
            ci_new=(
                "# leftover canary alloc. Handoff: nomad alloc stop alloc-can. "
                "never nomad system gc for a live canary.\n"
            ),
            left_name="alloc-can",
            left_cmd="nomad alloc status alloc-can | rg 'Status|Canary'",
            left_obs="Status = running\nCanary = true leftover\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="nomad alloc stop alloc-can",
            s11_act="show leftover canary services.",
            s11_cmd="nomad alloc status alloc-can | rg Service | head",
            s11_obs="jobs-api leftover 10% weight\n",
            s12_lead="weight leftover",
            s13_act="do not stop the stable alloc.",
            s13_cmd="nomad job allocs jobs | rg running",
            s13_obs="alloc-stable running\nalloc-can leftover running\n",
            s14_cmd="echo PARTIAL canary leftover",
            s14_obs="PARTIAL canary leftover\n",
            s15_lead="stable kept",
            s15_cmd="echo leftover canary alloc",
            s15_obs="leftover canary alloc\n",
            s16_lead="canary leftover",
            s16_cmd="echo alloc-can leftover",
            s16_obs="alloc-can leftover\n",
        ),
        "Nomad system already used skip (SUCCESS) and leftover canary (PARTIAL).",
    )
)
