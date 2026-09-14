#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 2: NEW dest plants.

Does not wrap unique-lll or unique-llll. Picks first unused SUCCESS/LEFTOVER pair.
BAN r1718 mlflow leftover dest, unique-lll wandb dest, matplotlib leftover PNG,
html-as-dest x chart-png twins, %load_ext cartesian, papermill engine *-g9,
sir-/dbc-/ntp html-as-dest ids, r100–r1718 clones.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_leftover",
    ROOT / "experiments/ntp-mill-unique-leftover.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)

s_from = mod.s_from
l_from = mod.l_from

SUCCESS = [
    s_from(0, "nuclio-function-leftover-as-dest", "nucl", "nuclio function leftover", ".nuclio/function.yaml", "Nuclio function leftover YAML", "nuctl get function leftover -o yaml > .nuclio/function.yaml", "not knative leftover; Nuclio function leftover is not dest", "treat Nuclio leftover YAML as dest then CLI parquet.", "nuclio leftover; # function yaml claimed dest", "nuclio leftover|.nuclio/function"),
    s_from(1, "openfaas-function-leftover-as-dest", "ofaa", "openfaas function leftover", ".openfaas/function.yml", "OpenFaaS function leftover YAML", "faas-cli describe leftover > .openfaas/function.yml", "not nuclio leftover; OpenFaaS function leftover is not dest", "treat OpenFaaS leftover YAML as dest then CLI parquet.", "openfaas leftover; # function yml claimed dest", "openfaas leftover|.openfaas/function"),
    s_from(2, "fission-function-leftover-as-dest", "fiss", "fission function leftover", ".fission/function.yaml", "Fission function leftover YAML", "fission function get leftover -o yaml > .fission/function.yaml", "not openfaas leftover; Fission function leftover is not dest", "treat Fission leftover YAML as dest then CLI parquet.", "fission leftover; # function yaml claimed dest", "fission leftover|.fission/function"),
    s_from(3, "brigade-event-leftover-as-dest", "brig", "brigade event leftover", ".brigade/event.json", "Brigade event leftover JSON", "brig event leftover --output json > .brigade/event.json", "not knative leftover; Brigade event leftover is not dest", "treat Brigade leftover JSON as dest then CLI parquet.", "brigade leftover; # event json claimed dest", "brigade leftover|.brigade/event"),
    s_from(4, "skaffold-profile-leftover-as-dest", "skfl", "skaffold profile leftover", ".skaffold/profile.yaml", "Skaffold profile leftover YAML", "skaffold diagnose leftover > .skaffold/profile.yaml", "not helm leftover; Skaffold profile leftover is not dest", "treat Skaffold leftover YAML as dest then CLI parquet.", "skaffold leftover; # profile yaml claimed dest", "skaffold leftover|.skaffold/profile"),
    s_from(5, "tilt-resource-leftover-as-dest", "tltr", "tilt resource leftover", ".tilt/resource.json", "Tilt resource leftover JSON", "tilt dump leftover > .tilt/resource.json", "not skaffold leftover; Tilt resource leftover is not dest", "treat Tilt leftover JSON as dest then CLI parquet.", "tilt leftover; # resource json claimed dest", "tilt leftover|.tilt/resource"),
    s_from(6, "garden-action-leftover-as-dest", "grdn", "garden action leftover", ".garden/action.json", "Garden action leftover JSON", "garden get leftover --output json > .garden/action.json", "not tilt leftover; Garden action leftover is not dest", "treat Garden leftover JSON as dest then CLI parquet.", "garden leftover; # action json claimed dest", "garden leftover|.garden/action"),
    s_from(7, "crossplane-claim-leftover-as-dest", "xpln", "crossplane claim leftover", ".crossplane/claim.yaml", "Crossplane claim leftover YAML", "kubectl get claim leftover -o yaml > .crossplane/claim.yaml", "not terraform leftover; Crossplane claim leftover is not dest", "treat Crossplane leftover YAML as dest then CLI parquet.", "crossplane leftover; # claim yaml claimed dest", "crossplane leftover|.crossplane/claim"),
    s_from(8, "helmfile-release-leftover-as-dest", "hlmf", "helmfile release leftover", ".helmfile/release.yaml", "Helmfile release leftover YAML", "helmfile leftover && cat .helmfile/release.yaml", "not helm leftover; Helmfile release leftover is not dest", "treat Helmfile leftover YAML as dest then CLI parquet.", "helmfile leftover; # release yaml claimed dest", "helmfile leftover|.helmfile/release"),
    s_from(9, "kustomize-overlay-leftover-as-dest", "kstm", "kustomize overlay leftover", ".kustomize/kustomization.yaml", "Kustomize overlay leftover YAML", "kustomize leftover && cat .kustomize/kustomization.yaml", "not helm leftover; Kustomize overlay leftover is not dest", "treat Kustomize leftover YAML as dest then CLI parquet.", "kustomize leftover; # kustomization yaml claimed dest", "kustomize leftover|.kustomize/kustomization"),
    s_from(10, "kapitan-inventory-leftover-as-dest", "kptn", "kapitan inventory leftover", ".kapitan/inventory.yml", "Kapitan inventory leftover YAML", "kapitan leftover && cat .kapitan/inventory.yml", "not kustomize leftover; Kapitan inventory leftover is not dest", "treat Kapitan leftover YAML as dest then CLI parquet.", "kapitan leftover; # inventory yml claimed dest", "kapitan leftover|.kapitan/inventory"),
    s_from(11, "atlasgo-schema-leftover-as-dest", "atgo", "atlasgo schema leftover", ".atlas/schema.hcl", "Atlas (ariga) schema leftover HCL", "atlas schema leftover > .atlas/schema.hcl", "not apache-atlas leftover; Atlasgo schema leftover is not dest", "treat Atlasgo leftover HCL as dest then CLI parquet.", "atlasgo leftover; # schema hcl claimed dest", "atlasgo leftover|.atlas/schema"),
    s_from(12, "unitycatalog-table-leftover-as-dest", "uctb", "unitycatalog table leftover", ".unity/table.json", "Unity Catalog table leftover JSON", "uc table get leftover --output json > .unity/table.json", "not hive leftover; Unity Catalog table leftover is not dest", "treat Unity Catalog leftover JSON as dest then CLI parquet.", "unity leftover; # table json claimed dest", "unity leftover|.unity/table"),
    s_from(13, "lightdash-project-leftover-as-dest", "ldsh", "lightdash project leftover", ".lightdash/project.json", "Lightdash project leftover JSON", "lightdash leftover --json > .lightdash/project.json", "not metabase leftover; Lightdash project leftover is not dest", "treat Lightdash leftover JSON as dest then CLI parquet.", "lightdash leftover; # project json claimed dest", "lightdash leftover|.lightdash/project"),
    s_from(14, "bazel-target-leftover-as-dest", "bazl", "bazel target leftover", ".bazel/target.json", "Bazel target leftover JSON", "bazel query leftover --output json > .bazel/target.json", "not pants leftover; Bazel target leftover is not dest", "treat Bazel leftover JSON as dest then CLI parquet.", "bazel leftover; # target json claimed dest", "bazel leftover|.bazel/target"),
    s_from(15, "pants-goal-leftover-as-dest", "pntg", "pants goal leftover", ".pants/goal.json", "Pants goal leftover JSON", "pants leftover --json > .pants/goal.json", "not bazel leftover; Pants goal leftover is not dest", "treat Pants leftover JSON as dest then CLI parquet.", "pants leftover; # goal json claimed dest", "pants leftover|.pants/goal"),
    s_from(16, "nox-session-leftover-as-dest", "noxs", "nox session leftover", ".nox/session.json", "Nox session leftover JSON", "nox leftover && cat .nox/session.json", "not tox leftover; Nox session leftover is not dest", "treat Nox leftover JSON as dest then CLI parquet.", "nox leftover; # session json claimed dest", "nox leftover|.nox/session"),
    s_from(17, "scons-target-leftover-as-dest", "scst", "scons target leftover", ".scons/target.json", "SCons target leftover JSON", "scons leftover && cat .scons/target.json", "not make leftover; SCons target leftover is not dest", "treat SCons leftover JSON as dest then CLI parquet.", "scons leftover; # target json claimed dest", "scons leftover|.scons/target"),
    s_from(18, "doit-task-leftover-as-dest", "dott", "doit task leftover", ".doit/task.json", "doit task leftover JSON", "doit leftover && cat .doit/task.json", "not invoke leftover; doit task leftover is not dest", "treat doit leftover JSON as dest then CLI parquet.", "doit leftover; # task json claimed dest", "doit leftover|.doit/task"),
    s_from(19, "drone-pipeline-leftover-as-dest", "drnp", "drone pipeline leftover", ".drone.yml", "Drone pipeline leftover YAML", "drone leftover && cat .drone.yml", "not woodpecker leftover; Drone pipeline leftover is not dest", "treat Drone leftover YAML as dest then CLI parquet.", "drone leftover; # yml claimed dest", "drone leftover|.drone.yml"),
    s_from(20, "circleci-workflow-leftover-as-dest", "crcl", "circleci workflow leftover", ".circleci/config.yml", "CircleCI workflow leftover YAML", "circleci leftover && cat .circleci/config.yml", "not github-actions leftover; CircleCI workflow leftover is not dest", "treat CircleCI leftover YAML as dest then CLI parquet.", "circleci leftover; # config yml claimed dest", "circleci leftover|.circleci/config"),
    s_from(21, "githubactions-workflow-leftover-as-dest", "ghaW", "githubactions workflow leftover", ".github/workflows/nightly.yml", "GitHub Actions workflow leftover YAML", "gh workflow leftover && cat .github/workflows/nightly.yml", "not circleci leftover; GitHub Actions workflow leftover is not dest", "treat GitHub Actions leftover YAML as dest then CLI parquet.", "gha leftover; # workflow yml claimed dest", "gha leftover|.github/workflows"),
    s_from(22, "gitlabci-pipeline-leftover-as-dest", "glci", "gitlabci pipeline leftover", ".gitlab-ci.yml", "GitLab CI pipeline leftover YAML", "gitlab leftover && cat .gitlab-ci.yml", "not github-actions leftover; GitLab CI pipeline leftover is not dest", "treat GitLab CI leftover YAML as dest then CLI parquet.", "gitlabci leftover; # yml claimed dest", "gitlabci leftover|.gitlab-ci.yml"),
    s_from(23, "jenkins-job-leftover-as-dest", "jnks", "jenkins job leftover", ".jenkins/job.xml", "Jenkins job leftover XML", "jenkins leftover && cat .jenkins/job.xml", "not gitlabci leftover; Jenkins job leftover is not dest", "treat Jenkins leftover XML as dest then CLI parquet.", "jenkins leftover; # job xml claimed dest", "jenkins leftover|.jenkins/job"),
    s_from(24, "argoevents-sensor-leftover-as-dest", "aevs", "argoevents sensor leftover", ".argo-events/sensor.yaml", "Argo Events sensor leftover YAML", "kubectl get sensor leftover -o yaml > .argo-events/sensor.yaml", "not argocd leftover; Argo Events sensor leftover is not dest", "treat Argo Events leftover YAML as dest then CLI parquet.", "argoevents leftover; # sensor yaml claimed dest", "argoevents leftover|.argo-events/sensor"),
    s_from(25, "rundeck-job-leftover-as-dest", "rndk", "rundeck job leftover", ".rundeck/job.yaml", "Rundeck job leftover YAML", "rd leftover && cat .rundeck/job.yaml", "not jenkins leftover; Rundeck job leftover is not dest", "treat Rundeck leftover YAML as dest then CLI parquet.", "rundeck leftover; # job yaml claimed dest", "rundeck leftover|.rundeck/job"),
    s_from(26, "octopus-project-leftover-as-dest", "octo", "octopus project leftover", ".octopus/project.json", "Octopus project leftover JSON", "octopus leftover --json > .octopus/project.json", "not rundeck leftover; Octopus project leftover is not dest", "treat Octopus leftover JSON as dest then CLI parquet.", "octopus leftover; # project json claimed dest", "octopus leftover|.octopus/project"),
    s_from(27, "awscodepipeline-pipeline-leftover-as-dest", "acpl", "codepipeline leftover", ".codepipeline/pipeline.json", "AWS CodePipeline leftover JSON", "aws codepipeline get-pipeline leftover > .codepipeline/pipeline.json", "not stepfunctions leftover; CodePipeline leftover is not dest", "treat CodePipeline leftover JSON as dest then CLI parquet.", "codepipeline leftover; # pipeline json claimed dest", "codepipeline leftover|.codepipeline/pipeline"),
    s_from(28, "azurepipelines-pipeline-leftover-as-dest", "azpl", "azurepipelines leftover", ".azure-pipelines.yml", "Azure Pipelines leftover YAML", "az pipelines leftover && cat .azure-pipelines.yml", "not github-actions leftover; Azure Pipelines leftover is not dest", "treat Azure Pipelines leftover YAML as dest then CLI parquet.", "azurepipelines leftover; # yml claimed dest", "azurepipelines leftover|.azure-pipelines.yml"),
    s_from(29, "googlecloudbuild-trigger-leftover-as-dest", "gcbd", "cloudbuild trigger leftover", ".cloudbuild/trigger.json", "Cloud Build trigger leftover JSON", "gcloud builds triggers describe leftover --format=json > .cloudbuild/trigger.json", "not dataproc leftover; Cloud Build trigger leftover is not dest", "treat Cloud Build leftover JSON as dest then CLI parquet.", "cloudbuild leftover; # trigger json claimed dest", "cloudbuild leftover|.cloudbuild/trigger"),
    s_from(30, "cloudfunctions-function-leftover-as-dest", "cfnf", "cloudfunctions leftover", ".gcloud/function.json", "Cloud Functions leftover JSON", "gcloud functions describe leftover --format=json > .gcloud/function.json", "not lambda leftover; Cloud Functions leftover is not dest", "treat Cloud Functions leftover JSON as dest then CLI parquet.", "cloudfunctions leftover; # function json claimed dest", "cloudfunctions leftover|.gcloud/function"),
    s_from(31, "lambda-function-leftover-as-dest", "lmbd", "lambda function leftover", ".lambda/function.json", "Lambda function leftover JSON", "aws lambda get-function leftover --output json > .lambda/function.json", "not cloudfunctions leftover; Lambda function leftover is not dest", "treat Lambda leftover JSON as dest then CLI parquet.", "lambda leftover; # function json claimed dest", "lambda leftover|.lambda/function"),
]

LEFTOVER = [
    l_from(0, "nuclio-trigger-leftover-handoff", "nuct", ".nuclio/trigger.json", "nuclio trigger leftover", "Nuclio trigger leftover JSON", "not nuclio function leftover; leftover Nuclio trigger JSON as dest", "ship leftover Nuclio trigger JSON as dest.", "trigger leftover; # json on disk", "nuclio leftover|.nuclio/trigger"),
    l_from(1, "openfaas-secret-leftover-handoff", "ofas", ".openfaas/secret.json", "openfaas secret leftover", "OpenFaaS secret leftover JSON", "not openfaas function leftover; leftover OpenFaaS secret JSON as dest", "ship leftover OpenFaaS secret JSON as dest.", "secret leftover; # json on disk", "openfaas leftover|.openfaas/secret"),
    l_from(2, "fission-mqtrigger-leftover-handoff", "fism", ".fission/mqtrigger.yaml", "fission mqtrigger leftover", "Fission MQ trigger leftover YAML", "not fission function leftover; leftover Fission MQ trigger YAML as dest", "ship leftover Fission MQ trigger YAML as dest.", "mqtrigger leftover; # yaml on disk", "fission leftover|.fission/mqtrigger"),
    l_from(3, "brigade-project-leftover-handoff", "brip", ".brigade/project.json", "brigade project leftover", "Brigade project leftover JSON", "not brigade event leftover; leftover Brigade project JSON as dest", "ship leftover Brigade project JSON as dest.", "project leftover; # json on disk", "brigade leftover|.brigade/project"),
    l_from(4, "skaffold-build-leftover-handoff", "skfb", ".skaffold/build.json", "skaffold build leftover", "Skaffold build leftover JSON", "not skaffold profile leftover; leftover Skaffold build JSON as dest", "ship leftover Skaffold build JSON as dest.", "build leftover; # json on disk", "skaffold leftover|.skaffold/build"),
    l_from(5, "tilt-trigger-leftover-handoff", "tltt", ".tilt/trigger.json", "tilt trigger leftover", "Tilt trigger leftover JSON", "not tilt resource leftover; leftover Tilt trigger JSON as dest", "ship leftover Tilt trigger JSON as dest.", "trigger leftover; # json on disk", "tilt leftover|.tilt/trigger"),
    l_from(6, "garden-module-leftover-handoff", "grdm", ".garden/module.json", "garden module leftover", "Garden module leftover JSON", "not garden action leftover; leftover Garden module JSON as dest", "ship leftover Garden module JSON as dest.", "module leftover; # json on disk", "garden leftover|.garden/module"),
    l_from(7, "crossplane-xrd-leftover-handoff", "xplx", ".crossplane/xrd.yaml", "crossplane xrd leftover", "Crossplane XRD leftover YAML", "not crossplane claim leftover; leftover Crossplane XRD YAML as dest", "ship leftover Crossplane XRD YAML as dest.", "xrd leftover; # yaml on disk", "crossplane leftover|.crossplane/xrd"),
    l_from(8, "helmfile-env-leftover-handoff", "hlme", ".helmfile/env.yaml", "helmfile env leftover", "Helmfile env leftover YAML", "not helmfile release leftover; leftover Helmfile env YAML as dest", "ship leftover Helmfile env YAML as dest.", "env leftover; # yaml on disk", "helmfile leftover|.helmfile/env"),
    l_from(9, "kustomize-component-leftover-handoff", "kstc", ".kustomize/component.yaml", "kustomize component leftover", "Kustomize component leftover YAML", "not kustomize overlay leftover; leftover Kustomize component YAML as dest", "ship leftover Kustomize component YAML as dest.", "component leftover; # yaml on disk", "kustomize leftover|.kustomize/component"),
    l_from(10, "kapitan-target-leftover-handoff", "kptt", ".kapitan/target.yml", "kapitan target leftover", "Kapitan target leftover YAML", "not kapitan inventory leftover; leftover Kapitan target YAML as dest", "ship leftover Kapitan target YAML as dest.", "target leftover; # yml on disk", "kapitan leftover|.kapitan/target"),
    l_from(11, "atlasgo-migration-leftover-handoff", "atgm", ".atlas/migration.sql", "atlasgo migration leftover", "Atlasgo migration leftover SQL", "not atlasgo schema leftover; leftover Atlasgo migration SQL as dest", "ship leftover Atlasgo migration SQL as dest.", "migration leftover; # sql on disk", "atlasgo leftover|.atlas/migration"),
    l_from(12, "unitycatalog-volume-leftover-handoff", "ucvl", ".unity/volume.json", "unitycatalog volume leftover", "Unity Catalog volume leftover JSON", "not unitycatalog table leftover; leftover Unity Catalog volume JSON as dest", "ship leftover Unity Catalog volume JSON as dest.", "volume leftover; # json on disk", "unity leftover|.unity/volume"),
    l_from(13, "lightdash-space-leftover-handoff", "ldss", ".lightdash/space.json", "lightdash space leftover", "Lightdash space leftover JSON", "not lightdash project leftover; leftover Lightdash space JSON as dest", "ship leftover Lightdash space JSON as dest.", "space leftover; # json on disk", "lightdash leftover|.lightdash/space"),
    l_from(14, "bazel-runfiles-leftover-handoff", "bazr", ".bazel/runfiles.json", "bazel runfiles leftover", "Bazel runfiles leftover JSON", "not bazel target leftover; leftover Bazel runfiles JSON as dest", "ship leftover Bazel runfiles JSON as dest.", "runfiles leftover; # json on disk", "bazel leftover|.bazel/runfiles"),
    l_from(15, "pants-pex-leftover-handoff", "pntp", ".pants/pex.json", "pants pex leftover", "Pants PEX leftover JSON", "not pants goal leftover; leftover Pants PEX JSON as dest", "ship leftover Pants PEX JSON as dest.", "pex leftover; # json on disk", "pants leftover|.pants/pex"),
    l_from(16, "nox-env-leftover-handoff", "noxe", ".nox/env.json", "nox env leftover", "Nox env leftover JSON", "not nox session leftover; leftover Nox env JSON as dest", "ship leftover Nox env JSON as dest.", "env leftover; # json on disk", "nox leftover|.nox/env"),
    l_from(17, "scons-cache-leftover-handoff", "scsc", ".scons/cache.json", "scons cache leftover", "SCons cache leftover JSON", "not scons target leftover; leftover SCons cache JSON as dest", "ship leftover SCons cache JSON as dest.", "cache leftover; # json on disk", "scons leftover|.scons/cache"),
    l_from(18, "doit-db-leftover-handoff", "dotd", ".doit/doit.db", "doit db leftover", "doit db leftover sqlite", "not doit task leftover; leftover doit sqlite as dest", "ship leftover doit sqlite as dest.", "db leftover; # sqlite on disk", "doit leftover|.doit/doit.db"),
    l_from(19, "drone-secret-leftover-handoff", "drns", ".drone/secret.json", "drone secret leftover", "Drone secret leftover JSON", "not drone pipeline leftover; leftover Drone secret JSON as dest", "ship leftover Drone secret JSON as dest.", "secret leftover; # json on disk", "drone leftover|.drone/secret"),
    l_from(20, "circleci-orb-leftover-handoff", "crco", ".circleci/orb.yml", "circleci orb leftover", "CircleCI orb leftover YAML", "not circleci workflow leftover; leftover CircleCI orb YAML as dest", "ship leftover CircleCI orb YAML as dest.", "orb leftover; # yml on disk", "circleci leftover|.circleci/orb"),
    l_from(21, "githubactions-artifact-leftover-handoff", "ghaa", ".github/artifact.json", "githubactions artifact leftover", "GitHub Actions artifact leftover JSON", "not githubactions workflow leftover; leftover GitHub Actions artifact JSON as dest", "ship leftover GitHub Actions artifact JSON as dest.", "artifact leftover; # json on disk", "gha leftover|.github/artifact"),
    l_from(22, "gitlabci-artifact-leftover-handoff", "glca", ".gitlab/artifact.json", "gitlabci artifact leftover", "GitLab CI artifact leftover JSON", "not gitlabci pipeline leftover; leftover GitLab CI artifact JSON as dest", "ship leftover GitLab CI artifact JSON as dest.", "artifact leftover; # json on disk", "gitlabci leftover|.gitlab/artifact"),
    l_from(23, "jenkins-artifact-leftover-handoff", "jnka", ".jenkins/artifact.json", "jenkins artifact leftover", "Jenkins artifact leftover JSON", "not jenkins job leftover; leftover Jenkins artifact JSON as dest", "ship leftover Jenkins artifact JSON as dest.", "artifact leftover; # json on disk", "jenkins leftover|.jenkins/artifact"),
    l_from(24, "argoevents-eventsource-leftover-handoff", "aeve", ".argo-events/eventsource.yaml", "argoevents eventsource leftover", "Argo Events eventsource leftover YAML", "not argoevents sensor leftover; leftover Argo Events eventsource YAML as dest", "ship leftover Argo Events eventsource YAML as dest.", "eventsource leftover; # yaml on disk", "argoevents leftover|.argo-events/eventsource"),
    l_from(25, "rundeck-execution-leftover-handoff", "rnde", ".rundeck/execution.json", "rundeck execution leftover", "Rundeck execution leftover JSON", "not rundeck job leftover; leftover Rundeck execution JSON as dest", "ship leftover Rundeck execution JSON as dest.", "execution leftover; # json on disk", "rundeck leftover|.rundeck/execution"),
    l_from(26, "octopus-release-leftover-handoff", "octr", ".octopus/release.json", "octopus release leftover", "Octopus release leftover JSON", "not octopus project leftover; leftover Octopus release JSON as dest", "ship leftover Octopus release JSON as dest.", "release leftover; # json on disk", "octopus leftover|.octopus/release"),
    l_from(27, "awscodepipeline-execution-leftover-handoff", "acpx", ".codepipeline/execution.json", "codepipeline execution leftover", "CodePipeline execution leftover JSON", "not codepipeline leftover; leftover CodePipeline execution JSON as dest", "ship leftover CodePipeline execution JSON as dest.", "execution leftover; # json on disk", "codepipeline leftover|.codepipeline/execution"),
    l_from(28, "azurepipelines-run-leftover-handoff", "azpr", ".azure/run.json", "azurepipelines run leftover", "Azure Pipelines run leftover JSON", "not azurepipelines leftover; leftover Azure Pipelines run JSON as dest", "ship leftover Azure Pipelines run JSON as dest.", "run leftover; # json on disk", "azurepipelines leftover|.azure/run"),
    l_from(29, "googlecloudbuild-build-leftover-handoff", "gcbb", ".cloudbuild/build.json", "cloudbuild build leftover", "Cloud Build leftover JSON", "not cloudbuild trigger leftover; leftover Cloud Build JSON as dest", "ship leftover Cloud Build JSON as dest.", "build leftover; # json on disk", "cloudbuild leftover|.cloudbuild/build"),
    l_from(30, "cloudfunctions-event-leftover-handoff", "cfne", ".gcloud/event.json", "cloudfunctions event leftover", "Cloud Functions event leftover JSON", "not cloudfunctions leftover; leftover Cloud Functions event JSON as dest", "ship leftover Cloud Functions event JSON as dest.", "event leftover; # json on disk", "cloudfunctions leftover|.gcloud/event"),
    l_from(31, "lambda-event-leftover-handoff", "lmbe", ".lambda/event.json", "lambda event leftover", "Lambda event leftover JSON", "not lambda function leftover; leftover Lambda event JSON as dest", "ship leftover Lambda event JSON as dest.", "event leftover; # json on disk", "lambda leftover|.lambda/event"),
]

BANNED_SLUGS = {
    "mlflow-experiment-leftover-as-dest",
    "mlflow-registry-leftover-handoff",
    "wandb-sweep-leftover-as-dest",
    "wandb-artifact-leftover-handoff",
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}


def pair_for(round_n: int) -> tuple[dict, dict]:
    used = mod.used_slugs() | BANNED_SLUGS
    for s, Ltheme in zip(SUCCESS, LEFTOVER):
        if s["slug"] in used or Ltheme["slug"] in used:
            continue
        if "dnsmasq" in s["slug"] or "dnsmasq" in Ltheme["slug"]:
            continue
        if "html-as-dest" in s["slug"] or "html-as-dest" in Ltheme["slug"]:
            continue
        if mod.VIZ_RE.search(s["slug"]) or mod.VIZ_RE.search(Ltheme["slug"]):
            continue
        return s, Ltheme
    raise RuntimeError(
        f"theme table exhausted at r{round_n}; extend SUCCESS/LEFTOVER, do not wrap unique-lll"
    )


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    used = mod.used_slugs() | {s["slug"], Ltheme["slug"]} | BANNED_SLUGS
    unused = "theme table end — new mill, do not wrap unique-lll wandb/mlflow clones"
    for ns, nl in zip(SUCCESS, LEFTOVER):
        if ns["slug"] not in used and nl["slug"] not in used:
            unused = f"{ns['slug']}, {nl['slug']}"
            break
    return f"""# NOTES-r{round_n} notebook-to-pipeline-factory

Novel coverage: leftover leftover leftover leftover dest vs leftover leftover leftover leftover handoff for a distinct orchestrator/warehouse product (not graph-png, not Prefect UI HTML, not r100–r1718 clones, not unique-lll wandb/mlflow wrap).

Two designed episodes (quota 2). Surfaces: {s['slug']} ({s['distinct']}); leftover {Ltheme['slug']} ({Ltheme['distinct']}).
Each rejects wrap-leftover and leftover-as-dest. Not %load_ext cartesian, not papermill engine *-g9, not r100–r1718 clone.
BAN matplotlib leftover PNG mill and html-as-dest x chart-png twins. Never sir-/dbc-/ntp html-as-dest ids.
BAN r1718 mlflow-experiment-leftover-as-dest / mlflow-registry-leftover-handoff.

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {e1['id']} | {s['token']} | wrap leftover | {s['stem']}.py --src/--dest | success 3/3 |
| {e2['id']} | leftover {Ltheme['left_token']} | ship leftover as dest | {Ltheme['stem']}.py CLI; leftover remains | handoff leftover |

## Step counts
- ep1: {len(e1['steps'])}. inspect src 2; first-apply {s['token']} 5; file(1) 6; wrap 7; CLI 10.
- ep2: {len(e2['steps'])}. leftover file(1) 2; leftover-as-dest 5; wrap leftover 6; CLI 9; leftover still on disk 11; handoff 16–18.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plant `folio-*`.
meta.generator=grok-4.6. IDs ntp-r{round_n}-<slug> without synth-magic-gNNNN / synth-engine-eNNNN.

## Weaknesses / next
Unused: {unused}.
Avoid raw nbconvert, comment-magics, gNNNN cartesian, papermill engine *-g9, r10 git-LFS clone, r50 memit clone, matplotlib leftover clones.
Skip already-covered leftovers: html-as-dest x chart-png, ActiveMQ export, Prefect UI HTML, Flink savepoint, Airflow graph PNG, Luigi graph PNG, unique-lll mlflow/wandb leftover dest.
"""


def write_stage(staging: Path, round_n: int) -> tuple[str, str]:
    s, Ltheme = pair_for(round_n)
    e1 = mod.success_ep(round_n, s, 0)
    e2 = mod.leftover_ep(round_n, Ltheme, 1)
    for ep, lo, hi in ((e1, 16, 16), (e2, 18, 18)):
        n = len(ep["steps"])
        if not (lo <= n <= hi):
            raise RuntimeError(f"{ep['id']} steps {n} not in {lo}-{hi}")
        for i, st in enumerate(ep["steps"], 1):
            if st["n"] != i:
                raise RuntimeError(f"{ep['id']} step n gap at {i}")
            mod.db(st["decision_basis"])
        if ep["meta"]["generator"] != mod.GEN or ep["meta"]["round"] != round_n:
            raise RuntimeError("meta mismatch")
        if not ep["id"].startswith(f"ntp-r{round_n}-"):
            raise RuntimeError(f"bad id {ep['id']}")
        if "synth-magic" in ep["id"] or "synth-engine" in ep["id"]:
            raise RuntimeError("synth id")
        if "html-as-dest" in ep["id"]:
            raise RuntimeError("html-as-dest banned")
        if any(tok in ep["id"] for tok in ("sir-", "dbc-")):
            raise RuntimeError(f"banned prefix in {ep['id']}")
        mod.check_blob(ep)
        mod.walk_banned(ep)
    notes = notes_for(round_n, e1, e2, s, Ltheme)
    if "Novel coverage:" not in notes:
        raise RuntimeError("notes missing Novel coverage")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    npath = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(e1, ensure_ascii=True) + "\n" + json.dumps(e2, ensure_ascii=True) + "\n"
    )
    npath.write_text(notes)
    return e1["id"], e2["id"]


mod.SUCCESS = SUCCESS
mod.LEFTOVER = LEFTOVER
mod.pair_for = pair_for
mod.notes_for = notes_for
mod.write_stage = write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll2.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
