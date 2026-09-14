#!/usr/bin/env python3
"""NTP unique leftover leftover leftover mill: 16 dest products (not graph-png / UI HTML).

Skip used r1558–r1674. Pair index is (round-1676)%16.
Not %load_ext cartesian, papermill --engine *-g9, matplotlib leftover PNG,
html-as-dest x chart-png twins, sir-/dbc-/ntp html-as-dest ids.
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
    s_from(0, "kfp-compiled-pipeline-leftover-as-dest", "kfpc", "kfp compile leftover", ".kfp/pipeline.yaml", "Kubeflow compiled pipeline leftover YAML", "kfp dsl compile leftover --output .kfp/pipeline.yaml", "not kale leftover; Kubeflow compiled pipeline leftover is not dest", "treat Kubeflow leftover YAML as dest then CLI parquet.", "kfp.dsl leftover; # pipeline yaml claimed dest", "kfp leftover|.kfp/pipeline"),
    s_from(1, "airflow-dagrun-leftover-as-dest", "afdr", "airflow dagrun leftover", ".airflow/dagrun.json", "Airflow DagRun leftover JSON", "airflow dags details leftover --output json > .airflow/dagrun.json", "not airflow graph-png leftover; DagRun leftover JSON is not dest", "treat Airflow DagRun leftover JSON as dest then CLI parquet.", "dagrun leftover; # json claimed dest", "airflow leftover|.airflow/dagrun"),
    s_from(2, "luigi-history-leftover-as-dest", "luhs", "luigi history leftover", ".luigi/history.json", "Luigi history leftover JSON", "luigi-history leftover && cat .luigi/history.json", "not luigi graph-png leftover; Luigi history leftover is not dest", "treat Luigi history leftover JSON as dest then CLI parquet.", "history leftover; # json claimed dest", "luigi leftover|.luigi/history"),
    s_from(3, "prefect-deployment-leftover-as-dest", "pfdp", "prefect deployment leftover", ".prefect/deployment.json", "Prefect deployment leftover JSON", "prefect deployment inspect leftover --output json > .prefect/deployment.json", "not prefect UI HTML leftover; deployment leftover JSON is not dest", "treat Prefect deployment leftover JSON as dest then CLI parquet.", "deployment leftover; # json claimed dest", "prefect leftover|.prefect/deployment"),
    s_from(4, "dagster-run-config-leftover-as-dest", "dgrc", "dagster run-config leftover", ".dagster/run_config.yaml", "Dagster run-config leftover YAML", "dagster job inspect leftover && cat .dagster/run_config.yaml", "not dagster materialize leftover; run-config leftover is not dest", "treat Dagster run-config leftover YAML as dest then CLI parquet.", "run_config leftover; # yaml claimed dest", "dagster leftover|.dagster/run_config"),
    s_from(5, "flyte-launchplan-leftover-as-dest", "fllp", "flyte launchplan leftover", ".flyte/launchplan.yaml", "Flyte launchplan leftover YAML", "flytectl get launchplan leftover -o yaml > .flyte/launchplan.yaml", "not flyte-execution-as-dest; launchplan leftover is not dest", "treat Flyte launchplan leftover YAML as dest then CLI parquet.", "launchplan leftover; # yaml claimed dest", "flyte leftover|.flyte/launchplan"),
    s_from(6, "kedro-session-leftover-as-dest", "kdss", "kedro session leftover", ".kedro/session.json", "Kedro session leftover JSON", "kedro session leftover && cat .kedro/session.json", "not kedro catalog leftover; session leftover JSON is not dest", "treat Kedro session leftover JSON as dest then CLI parquet.", "session leftover; # json claimed dest", "kedro leftover|.kedro/session"),
    s_from(7, "metaflow-card-leftover-as-dest", "mfcd", "metaflow card leftover", ".metaflow/card.json", "Metaflow card leftover JSON", "python -m metaflow card leftover && cat .metaflow/card.json", "not metaflow datastore leftover; card leftover JSON is not dest", "treat Metaflow card leftover JSON as dest then CLI parquet.", "card leftover; # json claimed dest", "metaflow leftover|.metaflow/card"),
    s_from(8, "dbt-run-results-leftover-as-dest", "dbrr", "dbt run-results leftover", "target/run_results.json", "dbt run_results leftover JSON", "dbt run leftover && cat target/run_results.json", "not dbt manifest leftover; run_results leftover is not dest", "treat dbt run_results leftover JSON as dest then CLI parquet.", "run_results leftover; # json claimed dest", "dbt leftover|target/run_results"),
    s_from(9, "gx-expectation-suite-leftover-as-dest", "gxes", "gx suite leftover", ".gx/suite.json", "GX expectation-suite leftover JSON", "great_expectations suite leftover && cat .gx/suite.json", "not gx checkpoint leftover; suite leftover JSON is not dest", "treat GX suite leftover JSON as dest then CLI parquet.", "suite leftover; # json claimed dest", "gx leftover|.gx/suite"),
    s_from(10, "mlflow-experiment-leftover-as-dest", "mlex", "mlflow experiment leftover", ".mlflow/experiment.json", "MLflow experiment leftover JSON", "mlflow experiments describe leftover && cat .mlflow/experiment.json", "not mlflow run leftover; experiment leftover JSON is not dest", "treat MLflow experiment leftover JSON as dest then CLI parquet.", "experiment leftover; # json claimed dest", "mlflow leftover|.mlflow/experiment"),
    s_from(11, "wandb-sweep-leftover-as-dest", "wbsw", "wandb sweep leftover", ".wandb/sweep.json", "W&B sweep leftover JSON", "wandb sweep leftover && cat .wandb/sweep.json", "not wandb PNG leftover; sweep leftover JSON is not dest", "treat W&B sweep leftover JSON as dest then CLI parquet.", "sweep leftover; # json claimed dest", "wandb leftover|.wandb/sweep"),
    s_from(12, "vertex-pipeline-job-leftover-as-dest", "vtpj", "vertex pipeline-job leftover", ".vertex/pipeline_job.json", "Vertex pipeline-job leftover JSON", "gcloud ai pipeline-jobs describe leftover --format=json > .vertex/pipeline_job.json", "not vertex custom-job leftover; pipeline-job leftover is not dest", "treat Vertex pipeline-job leftover JSON as dest then CLI parquet.", "pipeline_job leftover; # json claimed dest", "vertex leftover|.vertex/pipeline_job"),
    s_from(13, "sagemaker-processing-leftover-as-dest", "sgmp", "sagemaker processing leftover", ".sagemaker/processing.json", "SageMaker processing leftover JSON", "aws sagemaker describe-processing-job leftover > .sagemaker/processing.json", "not sagemaker training leftover; processing leftover is not dest", "treat SageMaker processing leftover JSON as dest then CLI parquet.", "processing leftover; # json claimed dest", "sagemaker leftover|.sagemaker/processing"),
    s_from(14, "databricks-job-spec-leftover-as-dest", "dbjs", "databricks job-spec leftover", ".databricks/job.json", "Databricks job-spec leftover JSON", "databricks jobs get leftover --output json > .databricks/job.json", "not databricks notebook-run leftover; job-spec leftover is not dest", "treat Databricks job-spec leftover JSON as dest then CLI parquet.", "job spec leftover; # json claimed dest", "databricks leftover|.databricks/job.json"),
    s_from(15, "snowflake-task-leftover-as-dest", "sftk", "snowflake task leftover", ".snowflake/task.sql", "Snowflake task leftover SQL", "snowsql leftover -q 'describe task folio' > .snowflake/task.sql", "not snowflake worksheet leftover; task leftover SQL is not dest", "treat Snowflake task leftover SQL as dest then CLI parquet.", "task leftover; # sql claimed dest", "snowflake leftover|.snowflake/task"),
]

LEFTOVER = [
    l_from(0, "kfp-run-leftover-handoff", "kfpr", ".kfp/run.json", "kfp run leftover", "Kubeflow run leftover JSON", "not kfp compiled yaml leftover; leftover Kubeflow run JSON as dest", "ship leftover Kubeflow run JSON as dest.", "kfp run leftover; # json on disk", "kfp leftover|.kfp/run.json"),
    l_from(1, "airflow-xcom-leftover-handoff", "afxc", ".airflow/xcom.json", "airflow xcom leftover", "Airflow XCom leftover JSON", "not airflow graph-png leftover; leftover XCom JSON as dest", "ship leftover Airflow XCom JSON as dest.", "xcom leftover; # json on disk", "airflow leftover|.airflow/xcom"),
    l_from(2, "luigi-worker-leftover-handoff", "luwk", ".luigi/worker.json", "luigi worker leftover", "Luigi worker leftover JSON", "not luigi graph-png leftover; leftover worker JSON as dest", "ship leftover Luigi worker JSON as dest.", "worker leftover; # json on disk", "luigi leftover|.luigi/worker"),
    l_from(3, "prefect-work-pool-leftover-handoff", "pfwp", ".prefect/work_pool.json", "prefect work-pool leftover", "Prefect work-pool leftover JSON", "not prefect UI HTML leftover; leftover work-pool JSON as dest", "ship leftover Prefect work-pool JSON as dest.", "work_pool leftover; # json on disk", "prefect leftover|.prefect/work_pool"),
    l_from(4, "dagster-sensor-leftover-handoff", "dgsn", ".dagster/sensor.json", "dagster sensor leftover", "Dagster sensor leftover JSON", "not dagster run-config leftover; leftover sensor JSON as dest", "ship leftover Dagster sensor JSON as dest.", "sensor leftover; # json on disk", "dagster leftover|.dagster/sensor"),
    l_from(5, "flyte-workflow-yaml-leftover-handoff", "flwf", ".flyte/workflow.yaml", "flyte workflow leftover", "Flyte workflow leftover YAML", "not flyte-execution-as-dest; leftover workflow YAML as dest", "ship leftover Flyte workflow YAML as dest.", "workflow leftover; # yaml on disk", "flyte leftover|.flyte/workflow"),
    l_from(6, "kedro-registry-leftover-handoff", "kdrg", ".kedro/registry.json", "kedro registry leftover", "Kedro pipeline-registry leftover JSON", "not kedro session leftover; leftover registry JSON as dest", "ship leftover Kedro registry JSON as dest.", "registry leftover; # json on disk", "kedro leftover|.kedro/registry"),
    l_from(7, "metaflow-metadata-leftover-handoff", "mfmd", ".metaflow/metadata.json", "metaflow metadata leftover", "Metaflow metadata leftover JSON", "not metaflow card leftover; leftover metadata JSON as dest", "ship leftover Metaflow metadata JSON as dest.", "metadata leftover; # json on disk", "metaflow leftover|.metaflow/metadata"),
    l_from(8, "dbt-catalog-leftover-handoff", "dbct", "target/catalog.json", "dbt catalog leftover", "dbt catalog leftover JSON", "not dbt run_results leftover; leftover catalog JSON as dest", "ship leftover dbt catalog JSON as dest.", "catalog leftover; # json on disk", "dbt leftover|target/catalog"),
    l_from(9, "gx-validation-leftover-handoff", "gxvl", ".gx/validation.json", "gx validation leftover", "GX validation leftover JSON", "not gx suite leftover; leftover validation JSON as dest", "ship leftover GX validation JSON as dest.", "validation leftover; # json on disk", "gx leftover|.gx/validation"),
    l_from(10, "mlflow-registry-leftover-handoff", "mlrg", ".mlflow/registry.json", "mlflow registry leftover", "MLflow model-registry leftover JSON", "not mlflow experiment leftover; leftover registry JSON as dest", "ship leftover MLflow registry JSON as dest.", "registry leftover; # json on disk", "mlflow leftover|.mlflow/registry"),
    l_from(11, "wandb-artifact-leftover-handoff", "wbat", ".wandb/artifact.json", "wandb artifact leftover", "W&B artifact leftover JSON", "not wandb PNG leftover; leftover artifact JSON as dest", "ship leftover W&B artifact JSON as dest.", "artifact leftover; # json on disk", "wandb leftover|.wandb/artifact"),
    l_from(12, "vertex-dataset-leftover-handoff", "vtds", ".vertex/dataset.json", "vertex dataset leftover", "Vertex dataset leftover JSON", "not vertex pipeline-job leftover; leftover dataset JSON as dest", "ship leftover Vertex dataset JSON as dest.", "dataset leftover; # json on disk", "vertex leftover|.vertex/dataset"),
    l_from(13, "sagemaker-model-leftover-handoff", "sgmd", ".sagemaker/model.json", "sagemaker model leftover", "SageMaker model leftover JSON", "not sagemaker processing leftover; leftover model JSON as dest", "ship leftover SageMaker model JSON as dest.", "model leftover; # json on disk", "sagemaker leftover|.sagemaker/model"),
    l_from(14, "databricks-dbfs-leftover-handoff", "dbfs", ".databricks/dbfs.json", "databricks dbfs leftover", "Databricks DBFS leftover JSON", "not databricks job-spec leftover; leftover DBFS JSON as dest", "ship leftover Databricks DBFS JSON as dest.", "dbfs leftover; # json on disk", "databricks leftover|.databricks/dbfs"),
    l_from(15, "snowflake-stage-leftover-handoff", "sfst", ".snowflake/stage.sql", "snowflake stage leftover", "Snowflake stage leftover SQL", "not snowflake task leftover; leftover stage SQL as dest", "ship leftover Snowflake stage SQL as dest.", "stage leftover; # sql on disk", "snowflake leftover|.snowflake/stage"),
]

START = 1676


def pair_for(round_n: int) -> tuple[dict, dict]:
    i = (round_n - START) % len(SUCCESS)
    return SUCCESS[i], LEFTOVER[i]


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    i = (round_n - START) % len(SUCCESS)
    nxt_s = SUCCESS[(i + 1) % len(SUCCESS)]["slug"]
    nxt_l = LEFTOVER[(i + 1) % len(LEFTOVER)]["slug"]
    return f"""# NOTES-r{round_n} notebook-to-pipeline-factory

Novel coverage: leftover leftover leftover dest vs leftover leftover leftover handoff for a distinct orchestrator/warehouse product (not graph-png, not Prefect UI HTML, not r1558–r1674 clones).

Two designed episodes (quota 2). Surfaces: {s['slug']} ({s['distinct']}); leftover {Ltheme['slug']} ({Ltheme['distinct']}).
Each rejects wrap-leftover and leftover-as-dest. Not %load_ext cartesian, not papermill engine *-g9, not r100–r1674 clone.
BAN matplotlib leftover PNG mill and html-as-dest x chart-png twins. Never sir-/dbc-/ntp html-as-dest ids.

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
Unused: {nxt_s}, {nxt_l}.
Avoid raw nbconvert, comment-magics, gNNNN cartesian, papermill engine *-g9, r10 git-LFS clone, r50 memit clone, matplotlib leftover clones.
Skip already-covered leftovers: html-as-dest x chart-png, ActiveMQ export, Prefect UI HTML, Flink savepoint, Airflow graph PNG, Luigi graph PNG.
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
        print("usage: ntp-mill-unique-lll.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
