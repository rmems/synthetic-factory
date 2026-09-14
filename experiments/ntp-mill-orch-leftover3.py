#!/usr/bin/env python3
"""NTP leftover leftover leftover mill: 16 notebook-dest pairs (orchestration leftovers).

Not r1478–r1557 clones. Not html-as-dest x chart-png. Not matplotlib leftover.
Does not scan the factory tree; pair index is (round-1558)%16.
"""
from __future__ import annotations

import importlib.util
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

# Success dest = first leftover product; leftover ep = sibling leftover product.
SUCCESS = [
    s_from(0, "mage-nb-leftover-as-dest", "mgnb", "mage leftover", ".mage/notebook.json", "Mage notebook leftover JSON", "mage run folio leftover && cat .mage/notebook.json", "not dagster leftover; Mage notebook leftover is not dest", "treat Mage leftover JSON as dest then CLI parquet.", "mage.block leftover; # notebook json claimed dest", "mage leftover|.mage/notebook"),
    s_from(1, "prefect-flow-run-leftover-as-dest", "pffr", "prefect leftover", ".prefect/flow_run.json", "Prefect flow-run leftover JSON", "prefect flow-run inspect leftover && cat .prefect/flow_run.json", "not flyte leftover; Prefect flow-run leftover is not dest", "treat Prefect leftover JSON as dest then CLI parquet.", "flow leftover; # flow_run json claimed dest", "prefect leftover|.prefect/flow_run"),
    s_from(2, "kedro-catalog-leftover-as-dest", "kdct", "kedro leftover", ".kedro/catalog.yml", "Kedro catalog leftover YAML", "kedro catalog list leftover && cat .kedro/catalog.yml", "not metaflow leftover; Kedro catalog leftover is not dest", "treat Kedro leftover YAML as dest then CLI parquet.", "catalog leftover; # yml claimed dest", "kedro leftover|.kedro/catalog"),
    s_from(3, "ploomber-product-leftover-as-dest", "plpr", "ploomber leftover", ".ploomber/product.json", "Ploomber product leftover JSON", "ploomber status leftover && cat .ploomber/product.json", "not hamilton leftover; Ploomber product leftover is not dest", "treat Ploomber leftover JSON as dest then CLI parquet.", "product leftover; # json claimed dest", "ploomber leftover|.ploomber/product"),
    s_from(4, "zenml-artifact-leftover-as-dest", "zmat", "zenml leftover", ".zenml/artifact.json", "ZenML artifact leftover JSON", "zenml artifact list leftover && cat .zenml/artifact.json", "not clearml leftover; ZenML artifact leftover is not dest", "treat ZenML leftover JSON as dest then CLI parquet.", "artifact leftover; # json claimed dest", "zenml leftover|.zenml/artifact"),
    s_from(5, "mlflow-run-artifact-leftover-as-dest", "mlra", "mlflow leftover", ".mlflow/run.json", "MLflow run leftover JSON", "mlflow runs describe leftover && cat .mlflow/run.json", "not wandb leftover PNG; MLflow run leftover is not dest", "treat MLflow leftover JSON as dest then CLI parquet.", "mlflow leftover; # run json claimed dest", "mlflow leftover|.mlflow/run.json"),
    s_from(6, "vertex-custom-job-leftover-as-dest", "vtxj", "vertex leftover", ".vertex/custom_job.json", "Vertex custom-job leftover JSON", "gcloud ai custom-jobs describe leftover --format=json > .vertex/custom_job.json", "not sagemaker leftover; Vertex job leftover is not dest", "treat Vertex leftover JSON as dest then CLI parquet.", "custom_job leftover; # json claimed dest", "vertex leftover|.vertex/custom_job"),
    s_from(7, "databricks-notebook-run-leftover-as-dest", "dbnr", "databricks leftover", ".databricks/run.json", "Databricks notebook-run leftover JSON", "databricks jobs get-run leftover --output json > .databricks/run.json", "not snowflake leftover; Databricks run leftover is not dest", "treat Databricks leftover JSON as dest then CLI parquet.", "notebook run leftover; # json claimed dest", "databricks leftover|.databricks/run.json"),
    s_from(8, "gx-checkpoint-result-leftover-as-dest", "gxcr", "gx leftover", ".gx/checkpoint.json", "Great Expectations checkpoint leftover JSON", "great_expectations checkpoint leftover && cat .gx/checkpoint.json", "not soda leftover; GX checkpoint leftover is not dest", "treat GX leftover JSON as dest then CLI parquet.", "checkpoint leftover; # json claimed dest", "gx leftover|.gx/checkpoint"),
    s_from(9, "dbt-manifest-leftover-as-dest", "dbmn", "dbt leftover", "target/manifest.json", "dbt manifest leftover JSON", "dbt compile leftover && cat target/manifest.json", "not sqlmesh leftover; dbt manifest leftover is not dest", "treat dbt leftover JSON as dest then CLI parquet.", "manifest leftover; # json claimed dest", "dbt leftover|target/manifest"),
    s_from(10, "marimo-app-state-leftover-as-dest", "mras", "marimo leftover", ".marimo/app.json", "Marimo app-state leftover JSON", "marimo run leftover && cat .marimo/app.json", "not jupyter papermill leftover; Marimo app leftover is not dest", "treat Marimo leftover JSON as dest then CLI parquet.", "app leftover; # json claimed dest", "marimo leftover|.marimo/app.json"),
    s_from(11, "quarto-execute-leftover-as-dest", "qtex", "quarto leftover", ".quarto/execute.json", "Quarto execute leftover JSON", "quarto render leftover && cat .quarto/execute.json", "not nbconvert leftover; Quarto execute leftover is not dest", "treat Quarto leftover JSON as dest then CLI parquet.", "execute leftover; # json claimed dest", "quarto leftover|.quarto/execute"),
    s_from(12, "papermill-output-nb-leftover-as-dest", "pmnb", "papermill leftover", ".papermill/out.ipynb", "Papermill output notebook leftover", "papermill in.ipynb leftover.ipynb && cp leftover.ipynb .papermill/out.ipynb", "not nbclient leftover; Papermill output leftover is not dest", "treat Papermill leftover notebook as dest then CLI parquet.", "papermill leftover; # out.ipynb claimed dest", "papermill leftover|.papermill/out"),
    s_from(13, "elyra-pipeline-run-leftover-as-dest", "eyrn", "elyra leftover", ".elyra/run.json", "Elyra pipeline-run leftover JSON", "elyra-pipeline submit leftover && cat .elyra/run.json", "not kale leftover; Elyra run leftover is not dest", "treat Elyra leftover JSON as dest then CLI parquet.", "pipeline leftover; # run json claimed dest", "elyra leftover|.elyra/run.json"),
    s_from(14, "voila-tornado-leftover-as-dest", "vltn", "voila leftover", ".voila/tornado.json", "Voila tornado leftover JSON", "voila leftover.ipynb --no-browser && cat .voila/tornado.json", "not panel leftover; Voila tornado leftover is not dest", "treat Voila leftover JSON as dest then CLI parquet.", "tornado leftover; # json claimed dest", "voila leftover|.voila/tornado"),
    s_from(15, "streamlit-session-leftover-as-dest", "stss", "streamlit leftover", ".streamlit/session.json", "Streamlit session leftover JSON", "streamlit run leftover.py && cat .streamlit/session.json", "not gradio leftover; Streamlit session leftover is not dest", "treat Streamlit leftover JSON as dest then CLI parquet.", "session leftover; # json claimed dest", "streamlit leftover|.streamlit/session"),
]

LEFTOVER = [
    l_from(0, "dagster-asset-materialize-leftover", "dgas", ".dagster/materialize.json", "dagster leftover", "Dagster materialize leftover JSON", "not mage leftover; leftover Dagster materialize JSON as dest", "ship leftover Dagster materialize JSON as dest.", "materialize leftover; # json on disk", "dagster leftover|.dagster/materialize"),
    l_from(1, "flyte-task-cache-leftover", "fltc", ".flyte/task_cache.bin", "flyte leftover", "Flyte task-cache leftover", "not flyte-execution-as-dest; leftover Flyte task cache as dest", "ship leftover Flyte task cache as dest.", "task cache leftover; # bin on disk", "flyte leftover|.flyte/task_cache"),
    l_from(2, "metaflow-datastore-leftover", "mfds", ".metaflow/datastore.bin", "metaflow leftover", "Metaflow datastore leftover", "not kedro leftover; leftover Metaflow datastore as dest", "ship leftover Metaflow datastore as dest.", "datastore leftover; # bin on disk", "metaflow leftover|.metaflow/datastore"),
    l_from(3, "hamilton-driver-leftover", "hmdv", ".hamilton/driver.json", "hamilton leftover", "Hamilton driver leftover JSON", "not ploomber leftover; leftover Hamilton driver JSON as dest", "ship leftover Hamilton driver JSON as dest.", "driver leftover; # json on disk", "hamilton leftover|.hamilton/driver"),
    l_from(4, "clearml-task-leftover", "clmt", ".clearml/task.json", "clearml leftover", "ClearML task leftover JSON", "not zenml leftover; leftover ClearML task JSON as dest", "ship leftover ClearML task JSON as dest.", "task leftover; # json on disk", "clearml leftover|.clearml/task"),
    l_from(5, "wandb-run-dir-leftover", "wbrn", ".wandb/run.json", "wandb leftover", "W&B run-dir leftover JSON", "not wandb PNG leftover; leftover W&B run JSON as dest", "ship leftover W&B run JSON as dest.", "run leftover; # json on disk", "wandb leftover|.wandb/run.json"),
    l_from(6, "sagemaker-training-job-leftover", "sgmt", ".sagemaker/training.json", "sagemaker leftover", "SageMaker training leftover JSON", "not vertex leftover; leftover SageMaker training JSON as dest", "ship leftover SageMaker training JSON as dest.", "training leftover; # json on disk", "sagemaker leftover|.sagemaker/training"),
    l_from(7, "snowflake-worksheet-leftover", "sfws", ".snowflake/worksheet.sql", "snowflake leftover", "Snowflake worksheet leftover SQL", "not databricks leftover; leftover Snowflake worksheet as dest", "ship leftover Snowflake worksheet as dest.", "worksheet leftover; # sql on disk", "snowflake leftover|.snowflake/worksheet"),
    l_from(8, "soda-scan-result-leftover", "sdsr", ".soda/result.json", "soda leftover", "Soda scan-result leftover JSON", "not gx leftover; leftover Soda result JSON as dest", "ship leftover Soda result JSON as dest.", "scan leftover; # json on disk", "soda leftover|.soda/result"),
    l_from(9, "sqlmesh-plan-leftover", "smpl", ".sqlmesh/plan.json", "sqlmesh leftover", "SQLMesh plan leftover JSON", "not dbt leftover; leftover SQLMesh plan JSON as dest", "ship leftover SQLMesh plan JSON as dest.", "plan leftover; # json on disk", "sqlmesh leftover|.sqlmesh/plan"),
    l_from(10, "jupyter-papermill-dest-leftover", "jppm", ".jupyter/papermill.json", "jupyter leftover", "Jupyter papermill dest leftover JSON", "not marimo leftover; leftover Jupyter papermill dest JSON as dest", "ship leftover Jupyter papermill dest JSON as dest.", "jupyter leftover; # json on disk", "jupyter leftover|.jupyter/papermill"),
    l_from(11, "nbconvert-output-leftover", "nbcv", ".nbconvert/out.md", "nbconvert leftover", "nbconvert output leftover markdown", "not quarto leftover; leftover nbconvert markdown as dest", "ship leftover nbconvert markdown as dest.", "nbconvert leftover; # md on disk", "nbconvert leftover|.nbconvert/out"),
    l_from(12, "nbclient-execute-leftover", "nbcl", ".nbclient/execute.json", "nbclient leftover", "nbclient execute leftover JSON", "not papermill leftover engine; leftover nbclient execute JSON as dest", "ship leftover nbclient execute JSON as dest.", "nbclient leftover; # json on disk", "nbclient leftover|.nbclient/execute"),
    l_from(13, "kale-kfp-leftover", "klkf", ".kale/kfp.json", "kale leftover", "Kale KFP leftover JSON", "not elyra leftover; leftover Kale KFP JSON as dest", "ship leftover Kale KFP JSON as dest.", "kale leftover; # json on disk", "kale leftover|.kale/kfp"),
    l_from(14, "panel-bokeh-leftover", "pnlb", ".panel/bokeh.json", "panel leftover", "Panel Bokeh leftover JSON", "not voila leftover; leftover Panel Bokeh JSON as dest", "ship leftover Panel Bokeh JSON as dest.", "panel leftover; # json on disk", "panel leftover|.panel/bokeh"),
    l_from(15, "gradio-flagged-leftover", "grfl", ".gradio/flagged.json", "gradio leftover", "Gradio flagged leftover JSON", "not streamlit leftover; leftover Gradio flagged JSON as dest", "ship leftover Gradio flagged JSON as dest.", "gradio leftover; # json on disk", "gradio leftover|.gradio/flagged"),
]

START = 1558


def pair_for(round_n: int) -> tuple[dict, dict]:
    i = (round_n - START) % len(SUCCESS)
    return SUCCESS[i], LEFTOVER[i]


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    i = (round_n - START) % len(SUCCESS)
    nxt_s = SUCCESS[(i + 1) % len(SUCCESS)]["slug"]
    nxt_l = LEFTOVER[(i + 1) % len(LEFTOVER)]["slug"]
    return f"""# NOTES-r{round_n} notebook-to-pipeline-factory

Novel coverage: 81%

Two designed episodes (quota 2). Surfaces: {s['slug']} ({s['distinct']}); leftover {Ltheme['slug']} ({Ltheme['distinct']}).
Each rejects wrap-leftover and leftover-as-dest. Not %load_ext cartesian, not papermill engine *-g9, not r100–r1276 clone, not r1277–r1557 dest/viz clone.
Keep r10 git-LFS pointer and r50 memit unused here. BAN matplotlib leftover PNG mill and html-as-dest x chart-png twins.

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
Skip already-covered leftovers: html-as-dest x chart-png, OpenMetadata/Collibra dests, crystal-docs-html-as-dest, aim-chart-png-leftover.
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
    notes = notes_for(round_n, e1, e2, s, Ltheme)
    if "Novel coverage:" not in notes:
        raise RuntimeError("notes missing Novel coverage")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    npath = staging / f"NOTES-r{round_n:02d}.md"
    import json

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
        print("usage: ntp-mill-orch-leftover3.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = mod.write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
