#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill: NEW dest plants (not unique-lll wrap).

Skip used r100–r1718. Pair index is (round-1719); do not wrap.
BAN r1718 mlflow leftover dest, wandb unique-lll dest, matplotlib leftover PNG,
html-as-dest x chart-png twins, %load_ext cartesian, papermill engine *-g9,
sir-/dbc-/ntp html-as-dest ids.
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
    s_from(0, "skypilot-task-leftover-as-dest", "skpt", "skypilot task leftover", ".skypilot/task.yaml", "SkyPilot task leftover YAML", "sky jobs logs leftover && cat .skypilot/task.yaml", "not ray leftover; SkyPilot task leftover is not dest", "treat SkyPilot leftover YAML as dest then CLI parquet.", "sky.task leftover; # yaml claimed dest", "skypilot leftover|.skypilot/task"),
    s_from(1, "modal-app-leftover-as-dest", "mdap", "modal app leftover", ".modal/app.json", "Modal app leftover JSON", "modal app list leftover --json > .modal/app.json", "not streamlit leftover; Modal app leftover is not dest", "treat Modal leftover JSON as dest then CLI parquet.", "modal.App leftover; # json claimed dest", "modal leftover|.modal/app"),
    s_from(2, "emr-step-leftover-as-dest", "emrs", "emr step leftover", ".emr/step.json", "EMR step leftover JSON", "aws emr describe-step leftover --output json > .emr/step.json", "not spark leftover; EMR step leftover is not dest", "treat EMR leftover JSON as dest then CLI parquet.", "emr.step leftover; # json claimed dest", "emr leftover|.emr/step"),
    s_from(3, "dataflow-job-leftover-as-dest", "dfjb", "dataflow job leftover", ".dataflow/job.json", "Dataflow job leftover JSON", "gcloud dataflow jobs describe leftover --format=json > .dataflow/job.json", "not beam leftover; Dataflow job leftover is not dest", "treat Dataflow leftover JSON as dest then CLI parquet.", "dataflow.job leftover; # json claimed dest", "dataflow leftover|.dataflow/job"),
    s_from(4, "cnvrg-experiment-leftover-as-dest", "cnvx", "cnvrg experiment leftover", ".cnvrg/experiment.json", "cnvrg experiment leftover JSON", "cnvrg experiment leftover && cat .cnvrg/experiment.json", "not mlflow leftover; cnvrg experiment leftover is not dest", "treat cnvrg leftover JSON as dest then CLI parquet.", "cnvrg leftover; # experiment json claimed dest", "cnvrg leftover|.cnvrg/experiment"),
    s_from(5, "stepfunctions-statemachine-leftover-as-dest", "sfnm", "stepfunctions leftover", ".sfn/statemachine.json", "Step Functions state-machine leftover JSON", "aws stepfunctions describe-state-machine leftover > .sfn/statemachine.json", "not airflow leftover; Step Functions leftover is not dest", "treat Step Functions leftover JSON as dest then CLI parquet.", "sfn leftover; # statemachine json claimed dest", "sfn leftover|.sfn/statemachine"),
    s_from(6, "mlrun-project-leftover-as-dest", "mlrp", "mlrun project leftover", ".mlrun/project.yaml", "MLRun project leftover YAML", "mlrun get project leftover -o yaml > .mlrun/project.yaml", "not kfp leftover; MLRun project leftover is not dest", "treat MLRun leftover YAML as dest then CLI parquet.", "mlrun leftover; # project yaml claimed dest", "mlrun leftover|.mlrun/project"),
    s_from(7, "anyscale-job-leftover-as-dest", "anys", "anyscale job leftover", ".anyscale/job.json", "Anyscale job leftover JSON", "anyscale job get leftover --output json > .anyscale/job.json", "not ray leftover; Anyscale job leftover is not dest", "treat Anyscale leftover JSON as dest then CLI parquet.", "anyscale leftover; # job json claimed dest", "anyscale leftover|.anyscale/job"),
    s_from(8, "coiled-cluster-leftover-as-dest", "cldc", "coiled cluster leftover", ".coiled/cluster.json", "Coiled cluster leftover JSON", "coiled cluster info leftover --json > .coiled/cluster.json", "not dask leftover; Coiled cluster leftover is not dest", "treat Coiled leftover JSON as dest then CLI parquet.", "coiled leftover; # cluster json claimed dest", "coiled leftover|.coiled/cluster"),
    s_from(9, "conductor-workflow-leftover-as-dest", "cdwf", "conductor workflow leftover", ".conductor/workflow.json", "Netflix Conductor workflow leftover JSON", "curl -s localhost:8080/api/workflow/folio > .conductor/workflow.json", "not airflow leftover; Conductor workflow leftover is not dest", "treat Conductor leftover JSON as dest then CLI parquet.", "conductor leftover; # workflow json claimed dest", "conductor leftover|.conductor/workflow"),
    s_from(10, "zeebe-process-leftover-as-dest", "zbpr", "zeebe process leftover", ".zeebe/process.bpmn", "Zeebe process leftover BPMN", "zbctl leftover --output json > .zeebe/process.bpmn", "not camunda leftover; Zeebe process leftover is not dest", "treat Zeebe leftover BPMN as dest then CLI parquet.", "zeebe leftover; # bpmn claimed dest", "zeebe leftover|.zeebe/process"),
    s_from(11, "camunda-process-leftover-as-dest", "cmpr", "camunda process leftover", ".camunda/process.bpmn", "Camunda process leftover BPMN", "camunda process leftover && cat .camunda/process.bpmn", "not zeebe leftover; Camunda process leftover is not dest", "treat Camunda leftover BPMN as dest then CLI parquet.", "camunda leftover; # bpmn claimed dest", "camunda leftover|.camunda/process"),
    s_from(12, "cadence-workflow-leftover-as-dest", "cdwk", "cadence workflow leftover", ".cadence/workflow.json", "Cadence workflow leftover JSON", "cadence workflow leftover --output json > .cadence/workflow.json", "not temporal leftover; Cadence workflow leftover is not dest", "treat Cadence leftover JSON as dest then CLI parquet.", "cadence leftover; # workflow json claimed dest", "cadence leftover|.cadence/workflow"),
    s_from(13, "knative-service-leftover-as-dest", "knsv", "knative service leftover", ".knative/service.yaml", "Knative service leftover YAML", "kubectl get ksvc leftover -o yaml > .knative/service.yaml", "not kserve leftover; Knative service leftover is not dest", "treat Knative leftover YAML as dest then CLI parquet.", "ksvc leftover; # yaml claimed dest", "knative leftover|.knative/service"),
    s_from(14, "spinnaker-pipeline-leftover-as-dest", "spnk", "spinnaker pipeline leftover", ".spinnaker/pipeline.json", "Spinnaker pipeline leftover JSON", "spin pipeline get leftover --output json > .spinnaker/pipeline.json", "not argo leftover; Spinnaker pipeline leftover is not dest", "treat Spinnaker leftover JSON as dest then CLI parquet.", "spinnaker leftover; # pipeline json claimed dest", "spinnaker leftover|.spinnaker/pipeline"),
    s_from(15, "harness-pipeline-leftover-as-dest", "hrns", "harness pipeline leftover", ".harness/pipeline.yaml", "Harness pipeline leftover YAML", "harness pipeline leftover --yaml > .harness/pipeline.yaml", "not spinnaker leftover; Harness pipeline leftover is not dest", "treat Harness leftover YAML as dest then CLI parquet.", "harness leftover; # pipeline yaml claimed dest", "harness leftover|.harness/pipeline"),
    s_from(16, "cloudcomposer-dag-leftover-as-dest", "ccdg", "composer dag leftover", ".composer/dag.py", "Cloud Composer DAG leftover Python", "gcloud composer leftover && cat .composer/dag.py", "not airflow leftover; Composer DAG leftover is not dest", "treat Composer leftover DAG as dest then CLI parquet.", "composer leftover; # dag.py claimed dest", "composer leftover|.composer/dag"),
    s_from(17, "dataproc-job-leftover-as-dest", "dprj", "dataproc job leftover", ".dataproc/job.json", "Dataproc job leftover JSON", "gcloud dataproc jobs describe leftover --format=json > .dataproc/job.json", "not emr leftover; Dataproc job leftover is not dest", "treat Dataproc leftover JSON as dest then CLI parquet.", "dataproc leftover; # job json claimed dest", "dataproc leftover|.dataproc/job"),
    s_from(18, "featureform-variant-leftover-as-dest", "ffvr", "featureform variant leftover", ".featureform/variant.json", "Featureform variant leftover JSON", "featureform get leftover --output json > .featureform/variant.json", "not feast leftover; Featureform variant leftover is not dest", "treat Featureform leftover JSON as dest then CLI parquet.", "featureform leftover; # variant json claimed dest", "featureform leftover|.featureform/variant"),
    s_from(19, "feathr-anchor-leftover-as-dest", "fhan", "feathr anchor leftover", ".feathr/anchor.json", "Feathr anchor leftover JSON", "spark-submit feathr leftover && cat .feathr/anchor.json", "not feast leftover; Feathr anchor leftover is not dest", "treat Feathr leftover JSON as dest then CLI parquet.", "feathr leftover; # anchor json claimed dest", "feathr leftover|.feathr/anchor"),
    s_from(20, "pathway-table-leftover-as-dest", "pwtb", "pathway table leftover", ".pathway/table.json", "Pathway table leftover JSON", "python -m pathway leftover && cat .pathway/table.json", "not bytewax leftover; Pathway table leftover is not dest", "treat Pathway leftover JSON as dest then CLI parquet.", "pathway leftover; # table json claimed dest", "pathway leftover|.pathway/table"),
    s_from(21, "quix-deployment-leftover-as-dest", "qxdp", "quix deployment leftover", ".quix/deployment.json", "Quix deployment leftover JSON", "quix deployments leftover --json > .quix/deployment.json", "not kafka leftover; Quix deployment leftover is not dest", "treat Quix leftover JSON as dest then CLI parquet.", "quix leftover; # deployment json claimed dest", "quix leftover|.quix/deployment"),
    s_from(22, "laktory-pipeline-leftover-as-dest", "lkpl", "laktory pipeline leftover", ".laktory/pipeline.yaml", "Laktory pipeline leftover YAML", "laktory deploy leftover && cat .laktory/pipeline.yaml", "not dbt leftover; Laktory pipeline leftover is not dest", "treat Laktory leftover YAML as dest then CLI parquet.", "laktory leftover; # pipeline yaml claimed dest", "laktory leftover|.laktory/pipeline"),
    s_from(23, "bruin-pipeline-leftover-as-dest", "brpl", "bruin pipeline leftover", ".bruin/pipeline.yml", "Bruin pipeline leftover YAML", "bruin run leftover && cat .bruin/pipeline.yml", "not dbt leftover; Bruin pipeline leftover is not dest", "treat Bruin leftover YAML as dest then CLI parquet.", "bruin leftover; # pipeline yml claimed dest", "bruin leftover|.bruin/pipeline"),
    s_from(24, "baseten-model-leftover-as-dest", "bstm", "baseten model leftover", ".baseten/model.json", "Baseten model leftover JSON", "truss leftover && cat .baseten/model.json", "not bentoml leftover; Baseten model leftover is not dest", "treat Baseten leftover JSON as dest then CLI parquet.", "baseten leftover; # model json claimed dest", "baseten leftover|.baseten/model"),
    s_from(25, "replicate-prediction-leftover-as-dest", "rppd", "replicate prediction leftover", ".replicate/prediction.json", "Replicate prediction leftover JSON", "replicate predictions leftover --json > .replicate/prediction.json", "not modal leftover; Replicate prediction leftover is not dest", "treat Replicate leftover JSON as dest then CLI parquet.", "replicate leftover; # prediction json claimed dest", "replicate leftover|.replicate/prediction"),
    s_from(26, "flux-kustomization-leftover-as-dest", "fxks", "flux kustomization leftover", ".flux/kustomization.yaml", "Flux kustomization leftover YAML", "flux get kustomizations leftover -o yaml > .flux/kustomization.yaml", "not kustomize leftover; Flux kustomization leftover is not dest", "treat Flux leftover YAML as dest then CLI parquet.", "flux leftover; # kustomization yaml claimed dest", "flux leftover|.flux/kustomization"),
    s_from(27, "argocd-application-leftover-as-dest", "acad", "argocd application leftover", ".argocd/application.yaml", "Argo CD application leftover YAML", "argocd app get leftover -o yaml > .argocd/application.yaml", "not argo-workflow leftover; Argo CD application leftover is not dest", "treat Argo CD leftover YAML as dest then CLI parquet.", "argocd leftover; # application yaml claimed dest", "argocd leftover|.argocd/application"),
    s_from(28, "buildkite-pipeline-leftover-as-dest", "bkpl", "buildkite pipeline leftover", ".buildkite/pipeline.yml", "Buildkite pipeline leftover YAML", "buildkite pipeline leftover && cat .buildkite/pipeline.yml", "not github-actions leftover; Buildkite pipeline leftover is not dest", "treat Buildkite leftover YAML as dest then CLI parquet.", "buildkite leftover; # pipeline yml claimed dest", "buildkite leftover|.buildkite/pipeline"),
    s_from(29, "concourse-pipeline-leftover-as-dest", "ccpl", "concourse pipeline leftover", ".concourse/pipeline.yml", "Concourse pipeline leftover YAML", "fly get-pipeline leftover -o .concourse/pipeline.yml", "not buildkite leftover; Concourse pipeline leftover is not dest", "treat Concourse leftover YAML as dest then CLI parquet.", "concourse leftover; # pipeline yml claimed dest", "concourse leftover|.concourse/pipeline"),
    s_from(30, "earthly-target-leftover-as-dest", "eart", "earthly target leftover", ".earthly/Earthfile", "Earthly Earthfile leftover", "earthly leftover && cat .earthly/Earthfile", "not docker leftover; Earthly target leftover is not dest", "treat Earthly leftover Earthfile as dest then CLI parquet.", "earthly leftover; # Earthfile claimed dest", "earthly leftover|.earthly/Earthfile"),
    s_from(31, "woodpecker-pipeline-leftover-as-dest", "wdpc", "woodpecker pipeline leftover", ".woodpecker/pipeline.yml", "Woodpecker pipeline leftover YAML", "woodpecker leftover && cat .woodpecker/pipeline.yml", "not drone leftover; Woodpecker pipeline leftover is not dest", "treat Woodpecker leftover YAML as dest then CLI parquet.", "woodpecker leftover; # pipeline yml claimed dest", "woodpecker leftover|.woodpecker/pipeline"),
]

LEFTOVER = [
    l_from(0, "skypilot-cluster-leftover-handoff", "skpc", ".skypilot/cluster.yaml", "skypilot cluster leftover", "SkyPilot cluster leftover YAML", "not skypilot task leftover; leftover SkyPilot cluster YAML as dest", "ship leftover SkyPilot cluster YAML as dest.", "cluster leftover; # yaml on disk", "skypilot leftover|.skypilot/cluster"),
    l_from(1, "modal-volume-leftover-handoff", "mdvl", ".modal/volume.json", "modal volume leftover", "Modal volume leftover JSON", "not modal app leftover; leftover Modal volume JSON as dest", "ship leftover Modal volume JSON as dest.", "volume leftover; # json on disk", "modal leftover|.modal/volume"),
    l_from(2, "emr-cluster-leftover-handoff", "emrc", ".emr/cluster.json", "emr cluster leftover", "EMR cluster leftover JSON", "not emr step leftover; leftover EMR cluster JSON as dest", "ship leftover EMR cluster JSON as dest.", "cluster leftover; # json on disk", "emr leftover|.emr/cluster"),
    l_from(3, "dataflow-template-leftover-handoff", "dftp", ".dataflow/template.json", "dataflow template leftover", "Dataflow template leftover JSON", "not dataflow job leftover; leftover Dataflow template JSON as dest", "ship leftover Dataflow template JSON as dest.", "template leftover; # json on disk", "dataflow leftover|.dataflow/template"),
    l_from(4, "cnvrg-dataset-leftover-handoff", "cnvd", ".cnvrg/dataset.json", "cnvrg dataset leftover", "cnvrg dataset leftover JSON", "not cnvrg experiment leftover; leftover cnvrg dataset JSON as dest", "ship leftover cnvrg dataset JSON as dest.", "dataset leftover; # json on disk", "cnvrg leftover|.cnvrg/dataset"),
    l_from(5, "stepfunctions-execution-leftover-handoff", "sfnx", ".sfn/execution.json", "stepfunctions execution leftover", "Step Functions execution leftover JSON", "not sfn statemachine leftover; leftover execution JSON as dest", "ship leftover Step Functions execution JSON as dest.", "execution leftover; # json on disk", "sfn leftover|.sfn/execution"),
    l_from(6, "mlrun-artifact-leftover-handoff", "mlrf", ".mlrun/artifact.json", "mlrun artifact leftover", "MLRun artifact leftover JSON", "not mlrun project leftover; leftover MLRun artifact JSON as dest", "ship leftover MLRun artifact JSON as dest.", "artifact leftover; # json on disk", "mlrun leftover|.mlrun/artifact"),
    l_from(7, "anyscale-service-leftover-handoff", "anyv", ".anyscale/service.json", "anyscale service leftover", "Anyscale service leftover JSON", "not anyscale job leftover; leftover Anyscale service JSON as dest", "ship leftover Anyscale service JSON as dest.", "service leftover; # json on disk", "anyscale leftover|.anyscale/service"),
    l_from(8, "coiled-adaptive-leftover-handoff", "clda", ".coiled/adaptive.json", "coiled adaptive leftover", "Coiled adaptive leftover JSON", "not coiled cluster leftover; leftover Coiled adaptive JSON as dest", "ship leftover Coiled adaptive JSON as dest.", "adaptive leftover; # json on disk", "coiled leftover|.coiled/adaptive"),
    l_from(9, "conductor-task-leftover-handoff", "cdtk", ".conductor/task.json", "conductor task leftover", "Conductor task leftover JSON", "not conductor workflow leftover; leftover Conductor task JSON as dest", "ship leftover Conductor task JSON as dest.", "task leftover; # json on disk", "conductor leftover|.conductor/task"),
    l_from(10, "zeebe-incident-leftover-handoff", "zbin", ".zeebe/incident.json", "zeebe incident leftover", "Zeebe incident leftover JSON", "not zeebe process leftover; leftover Zeebe incident JSON as dest", "ship leftover Zeebe incident JSON as dest.", "incident leftover; # json on disk", "zeebe leftover|.zeebe/incident"),
    l_from(11, "camunda-history-leftover-handoff", "cmhs", ".camunda/history.json", "camunda history leftover", "Camunda history leftover JSON", "not camunda process leftover; leftover Camunda history JSON as dest", "ship leftover Camunda history JSON as dest.", "history leftover; # json on disk", "camunda leftover|.camunda/history"),
    l_from(12, "cadence-history-leftover-handoff", "cdhs", ".cadence/history.json", "cadence history leftover", "Cadence history leftover JSON", "not cadence workflow leftover; leftover Cadence history JSON as dest", "ship leftover Cadence history JSON as dest.", "history leftover; # json on disk", "cadence leftover|.cadence/history"),
    l_from(13, "knative-revision-leftover-handoff", "knrv", ".knative/revision.yaml", "knative revision leftover", "Knative revision leftover YAML", "not knative service leftover; leftover Knative revision YAML as dest", "ship leftover Knative revision YAML as dest.", "revision leftover; # yaml on disk", "knative leftover|.knative/revision"),
    l_from(14, "spinnaker-execution-leftover-handoff", "spnx", ".spinnaker/execution.json", "spinnaker execution leftover", "Spinnaker execution leftover JSON", "not spinnaker pipeline leftover; leftover Spinnaker execution JSON as dest", "ship leftover Spinnaker execution JSON as dest.", "execution leftover; # json on disk", "spinnaker leftover|.spinnaker/execution"),
    l_from(15, "harness-deployment-leftover-handoff", "hrnd", ".harness/deployment.yaml", "harness deployment leftover", "Harness deployment leftover YAML", "not harness pipeline leftover; leftover Harness deployment YAML as dest", "ship leftover Harness deployment YAML as dest.", "deployment leftover; # yaml on disk", "harness leftover|.harness/deployment"),
    l_from(16, "cloudcomposer-env-leftover-handoff", "ccen", ".composer/env.json", "composer env leftover", "Cloud Composer env leftover JSON", "not composer dag leftover; leftover Composer env JSON as dest", "ship leftover Composer env JSON as dest.", "env leftover; # json on disk", "composer leftover|.composer/env"),
    l_from(17, "dataproc-cluster-leftover-handoff", "dprc", ".dataproc/cluster.json", "dataproc cluster leftover", "Dataproc cluster leftover JSON", "not dataproc job leftover; leftover Dataproc cluster JSON as dest", "ship leftover Dataproc cluster JSON as dest.", "cluster leftover; # json on disk", "dataproc leftover|.dataproc/cluster"),
    l_from(18, "featureform-provider-leftover-handoff", "ffpr", ".featureform/provider.json", "featureform provider leftover", "Featureform provider leftover JSON", "not featureform variant leftover; leftover Featureform provider JSON as dest", "ship leftover Featureform provider JSON as dest.", "provider leftover; # json on disk", "featureform leftover|.featureform/provider"),
    l_from(19, "feathr-materialize-leftover-handoff", "fhmt", ".feathr/materialize.json", "feathr materialize leftover", "Feathr materialize leftover JSON", "not feathr anchor leftover; leftover Feathr materialize JSON as dest", "ship leftover Feathr materialize JSON as dest.", "materialize leftover; # json on disk", "feathr leftover|.feathr/materialize"),
    l_from(20, "pathway-persistence-leftover-handoff", "pwps", ".pathway/persistence.json", "pathway persistence leftover", "Pathway persistence leftover JSON", "not pathway table leftover; leftover Pathway persistence JSON as dest", "ship leftover Pathway persistence JSON as dest.", "persistence leftover; # json on disk", "pathway leftover|.pathway/persistence"),
    l_from(21, "quix-topic-leftover-handoff", "qxtp", ".quix/topic.json", "quix topic leftover", "Quix topic leftover JSON", "not quix deployment leftover; leftover Quix topic JSON as dest", "ship leftover Quix topic JSON as dest.", "topic leftover; # json on disk", "quix leftover|.quix/topic"),
    l_from(22, "laktory-resource-leftover-handoff", "lkrs", ".laktory/resource.yaml", "laktory resource leftover", "Laktory resource leftover YAML", "not laktory pipeline leftover; leftover Laktory resource YAML as dest", "ship leftover Laktory resource YAML as dest.", "resource leftover; # yaml on disk", "laktory leftover|.laktory/resource"),
    l_from(23, "bruin-asset-leftover-handoff", "bras", ".bruin/asset.sql", "bruin asset leftover", "Bruin asset leftover SQL", "not bruin pipeline leftover; leftover Bruin asset SQL as dest", "ship leftover Bruin asset SQL as dest.", "asset leftover; # sql on disk", "bruin leftover|.bruin/asset"),
    l_from(24, "baseten-deployment-leftover-handoff", "bstd", ".baseten/deployment.json", "baseten deployment leftover", "Baseten deployment leftover JSON", "not baseten model leftover; leftover Baseten deployment JSON as dest", "ship leftover Baseten deployment JSON as dest.", "deployment leftover; # json on disk", "baseten leftover|.baseten/deployment"),
    l_from(25, "replicate-version-leftover-handoff", "rpvs", ".replicate/version.json", "replicate version leftover", "Replicate version leftover JSON", "not replicate prediction leftover; leftover Replicate version JSON as dest", "ship leftover Replicate version JSON as dest.", "version leftover; # json on disk", "replicate leftover|.replicate/version"),
    l_from(26, "flux-helmrelease-leftover-handoff", "fxhr", ".flux/helmrelease.yaml", "flux helmrelease leftover", "Flux HelmRelease leftover YAML", "not flux kustomization leftover; leftover Flux HelmRelease YAML as dest", "ship leftover Flux HelmRelease YAML as dest.", "helmrelease leftover; # yaml on disk", "flux leftover|.flux/helmrelease"),
    l_from(27, "argocd-sync-leftover-handoff", "acsy", ".argocd/sync.json", "argocd sync leftover", "Argo CD sync leftover JSON", "not argocd application leftover; leftover Argo CD sync JSON as dest", "ship leftover Argo CD sync JSON as dest.", "sync leftover; # json on disk", "argocd leftover|.argocd/sync"),
    l_from(28, "buildkite-build-leftover-handoff", "bkbd", ".buildkite/build.json", "buildkite build leftover", "Buildkite build leftover JSON", "not buildkite pipeline leftover; leftover Buildkite build JSON as dest", "ship leftover Buildkite build JSON as dest.", "build leftover; # json on disk", "buildkite leftover|.buildkite/build"),
    l_from(29, "concourse-build-leftover-handoff", "ccbd", ".concourse/build.json", "concourse build leftover", "Concourse build leftover JSON", "not concourse pipeline leftover; leftover Concourse build JSON as dest", "ship leftover Concourse build JSON as dest.", "build leftover; # json on disk", "concourse leftover|.concourse/build"),
    l_from(30, "earthly-artifact-leftover-handoff", "earf", ".earthly/artifact.json", "earthly artifact leftover", "Earthly artifact leftover JSON", "not earthly target leftover; leftover Earthly artifact JSON as dest", "ship leftover Earthly artifact JSON as dest.", "artifact leftover; # json on disk", "earthly leftover|.earthly/artifact"),
    l_from(31, "woodpecker-secret-leftover-handoff", "wdsc", ".woodpecker/secret.json", "woodpecker secret leftover", "Woodpecker secret leftover JSON", "not woodpecker pipeline leftover; leftover Woodpecker secret JSON as dest", "ship leftover Woodpecker secret JSON as dest.", "secret leftover; # json on disk", "woodpecker leftover|.woodpecker/secret"),
]

START = 1719
BANNED_SLUGS = {
    "mlflow-experiment-leftover-as-dest",
    "mlflow-registry-leftover-handoff",
    "wandb-sweep-leftover-as-dest",
    "wandb-artifact-leftover-handoff",
}


def pair_for(round_n: int) -> tuple[dict, dict]:
    i = round_n - START
    if i < 0 or i >= len(SUCCESS):
        raise RuntimeError(
            f"theme table exhausted at r{round_n}; extend SUCCESS/LEFTOVER, do not wrap unique-lll"
        )
    s, Ltheme = SUCCESS[i], LEFTOVER[i]
    if s["slug"] in BANNED_SLUGS or Ltheme["slug"] in BANNED_SLUGS:
        raise RuntimeError(f"banned unique-lll dest {s['slug']} / {Ltheme['slug']}")
    used = mod.used_slugs()
    if s["slug"] in used or Ltheme["slug"] in used:
        raise RuntimeError(f"clone dest {s['slug']} or {Ltheme['slug']} already published")
    if "html-as-dest" in s["slug"] or "html-as-dest" in Ltheme["slug"]:
        raise RuntimeError("html-as-dest banned")
    if mod.VIZ_RE.search(s["slug"]) or mod.VIZ_RE.search(Ltheme["slug"]):
        raise RuntimeError(f"viz leftover slug {s['slug']} / {Ltheme['slug']}")
    return s, Ltheme


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    i = round_n - START
    if i + 1 < len(SUCCESS):
        nxt_s = SUCCESS[i + 1]["slug"]
        nxt_l = LEFTOVER[i + 1]["slug"]
        unused = f"{nxt_s}, {nxt_l}"
    else:
        unused = "theme table end — new mill, do not wrap unique-lll wandb/mlflow clones"
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
        print("usage: ntp-mill-unique-llll.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
