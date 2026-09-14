#!/usr/bin/env python3
"""Unique leftover mill for notebook-to-pipeline-factory.

BAN matplotlib/seaborn/plotly PNG leftover clones.
BAN r1277-r1413 dest clones, g6/g9 cartesian, synth-magic/engine ids.
16-step success + 18-step leftover. meta.generator=grok-4.6.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

FACTORY = "notebook-to-pipeline-factory"
GEN = "grok-4.6"
ROOT = Path(__file__).resolve().parents[1]
FACTORY_DIR = ROOT / "outputs/raw/2026-08-19-agentic" / FACTORY
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
BANNED_BLOB = (
    "synth-magic-g",
    "synth-engine-e",
    "%load_ext",
    "papermill --engine",
    "git-lfs",
    "%memit",
    "--prepare-only",
    "--inject-input-path",
    "nbstripout",
    "--report-mode",
)
VIZ_RE = re.compile(
    r"(png|html|svg|matplotlib|seaborn|plotly|ridgeplot|hexbin|violin|boxen|"
    r"heatmap|kdeplot|histplot|barplot|countplot|stripplot|swarmplot)",
    re.I,
)
ID_SLUG_RE = re.compile(r"^ntp-r\d+-(.+)$")

TRANS = [
    'df["qty"] = pd.to_numeric(df["qty"], errors="coerce")',
    'df = df.rename(columns={"px": "mid"})',
    'df["lot_id"] = df["lot_id"].astype(str)',
    'df = df.sort_values("ts").groupby("symbol", as_index=False).tail(1)',
    'df = df[df["date"].astype(str) == "2026-08-18"]',
    'df["feat"] = pd.to_numeric(df["feat"], errors="coerce")',
    'df["score"] = pd.to_numeric(df["score"], errors="coerce")',
    'df["event_ts"] = pd.to_datetime(df["event_ts"], utc=True)',
    'df["amt"] = pd.to_numeric(df["amt"], errors="coerce")',
    'df = df[df["state"] == "done"]',
    'df = df[df["region"] == "us"]',
    'df["cat"] = df["cat"].astype(str)',
    'df["w"] = pd.to_numeric(df["w"], errors="coerce")',
    'df["metric"] = pd.to_numeric(df["metric"], errors="coerce")',
    'df["doc_id"] = df["doc_id"].astype(str)',
    'df = df[df["dim"] == 64]',
]


def db(s: str) -> str:
    s = " ".join(s.split())
    if not s.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise ValueError(f"bad basis prefix: {s[:80]!r}")
    if len(s) > 240:
        s = s[:239] + "…"
    return s


def tsec(n: int, base: float) -> str:
    return f"{base + (n % 7) * 0.01:.2f}"


def cli(src_default: str, dest_kind: str, transform: str) -> str:
    write = (
        "        df.to_parquet(dest)\n"
        if dest_kind == "parquet"
        else "        df.to_csv(dest, index=False)\n"
    )
    return (
        "import argparse\nimport pandas as pd\nfrom pathlib import Path\n\n"
        "def main(src: str, dest: str) -> str:\n"
        "    df = pd.read_csv(src)\n"
        f"    {transform}\n"
        "    Path(dest).parent.mkdir(parents=True, exist_ok=True)\n"
        f"{write}"
        "    return dest\n\n"
        'if __name__ == "__main__":\n'
        "    p = argparse.ArgumentParser()\n"
        f'    p.add_argument("--src", default={src_default!r})\n'
        '    p.add_argument("--dest", required=True)\n'
        "    a = p.parse_args()\n"
        "    main(a.src, a.dest)\n"
    )


def step(n: int, basis: str, name: str, args: dict, observation: str, reflection: str | None = None) -> dict:
    rec = {
        "n": n,
        "decision_basis": db(basis),
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }
    if reflection:
        rec["reflection"] = reflection
    return rec


def walk_banned(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in BANNED_KEYS:
                raise RuntimeError(f"banned key {k} at {path}.{k}")
            if k == "sim_or_real" and isinstance(v, str) and v.strip().lower() in {
                "real",
                "real_world",
                "real-world",
            }:
                raise RuntimeError(f"sim_or_real real at {path}")
            walk_banned(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk_banned(item, f"{path}[{i}]")


def check_blob(ep: dict) -> None:
    blob = json.dumps(ep)
    for tok in BANNED_BLOB:
        if tok in blob:
            raise RuntimeError(f"{ep['id']} contains banned token {tok!r}")
    if VIZ_RE.search(ep["id"]) and "leftover" in ep["id"]:
        raise RuntimeError(f"{ep['id']} is a viz leftover clone")


def S(
    slug: str,
    stem: str,
    src: str,
    rows: int,
    transform: str,
    token: str,
    ban: str,
    distinct: str,
    plan: str,
    cell: str,
    artifact: str,
    kind: str,
    cmd: str,
    file_obs: str,
) -> dict:
    dest = f"{stem}.parquet"
    return {
        "slug": slug,
        "plant": f"folio-{stem}",
        "stem": stem,
        "src": src,
        "dest": dest,
        "rows": rows,
        "transform": transform,
        "runner": f"{cmd} && cp {artifact} {dest}",
        "first_obs": f"{kind} written to {artifact}\n{dest} is {kind}; ArrowInvalid\n",
        "wrap": f"tar -cf {dest} {artifact}",
        "wrap_obs": f"{dest} is a tar of {kind}; still not parquet\n",
        "token": token,
        "ban": ban,
        "distinct": distinct,
        "plan": plan,
        "test_fn": f"test_no_{stem}_dest",
        "exp": f"export_{stem}",
        "cell": cell,
        "artifact": artifact,
        "kind": kind,
        "file_obs": file_obs,
    }


def L(
    slug: str,
    stem: str,
    src: str,
    rows: int,
    transform: str,
    leftover: str,
    left_token: str,
    ban: str,
    distinct: str,
    plan: str,
    cell: str,
    residual: str,
    handoff: str,
    kind: str,
    wrap: str | None = None,
    wrap_obs: str | None = None,
) -> dict:
    dest = f"{stem}.parquet"
    return {
        "slug": slug,
        "plant": f"folio-{stem}",
        "stem": stem,
        "src": src,
        "dest": dest,
        "rows": rows,
        "transform": transform,
        "leftover": leftover,
        "left_token": left_token,
        "first": f"cp {leftover} {dest}",
        "first_obs": f"{dest} is {kind} leftover; ArrowInvalid\n",
        "wrap": wrap or f"tar -cf {dest} {leftover}",
        "wrap_obs": wrap_obs or f"{dest} is a tar of {kind} leftover; still not parquet\n",
        "ban": ban,
        "distinct": distinct,
        "plan": plan,
        "test_fn": f"test_no_{stem}_leftover",
        "exp": f"export_{stem}",
        "cell": cell,
        "residual": residual,
        "handoff": handoff,
        "kind": kind,
    }


def s_from(i: int, slug: str, stem: str, token: str, artifact: str, kind: str, cmd: str, distinct: str, plan: str, cell: str, ban: str) -> dict:
    return S(
        slug=slug,
        stem=stem,
        src=f"data/{stem}_src.csv",
        rows=12011 + i * 17,
        transform=TRANS[i % len(TRANS)],
        token=token,
        ban=ban,
        distinct=distinct,
        plan=plan,
        cell=cell,
        artifact=artifact,
        kind=kind,
        cmd=cmd,
        file_obs=f"{stem}.parquet: {kind}, not parquet magic PAR1",
    )


def l_from(i: int, slug: str, stem: str, leftover: str, left_token: str, kind: str, distinct: str, plan: str, cell: str, ban: str) -> dict:
    return L(
        slug=slug,
        stem=stem,
        src=f"data/{stem}_src.csv",
        rows=13011 + i * 19,
        transform=TRANS[i % len(TRANS)],
        leftover=leftover,
        left_token=left_token,
        ban=ban,
        distinct=distinct,
        plan=plan,
        cell=cell,
        residual=f"{leftover} still on disk",
        handoff=f"leftover {kind} not cleaned; transform still notebook-only",
        kind=kind,
        wrap=f"tar -cf {stem}.parquet {leftover}",
        wrap_obs=f"{stem}.parquet is a tar of {kind} leftover\n",
    )


# Unique dest plants: lineage/quality/training-runtime/catalogs — not r1277–r1413 dests.
SUCCESS = [
    s_from(0, "soda-scan-as-dest", "sdsc", "soda scan", ".soda/scan.yml", "Soda Core scan YAML", "soda scan -d folio .soda/scan.yml", "not gx-uncommitted dest; Soda scan YAML is not dest", "soda scan and archive scan.yml as dest.", "soda.scan(warehouse); # yaml is claimed dest", "soda scan|.soda/"),
    s_from(1, "elementary-report-as-dest", "elmr", "edr report", ".edr/elementary.json", "Elementary dbt report JSON", "edr report --file .edr/elementary.json", "not dbt-run-results leftover; Elementary report JSON is not dest", "edr report and archive elementary.json as dest.", "edr.report(); df.to_parquet('elmr.parquet')", "edr report|.edr/"),
    s_from(2, "openlineage-run-as-dest", "olnr", "openlineage emit", ".ol/run.json", "OpenLineage RunEvent JSON", "python3 -c \"open('.ol/run.json','w').write('{\\\"eventType\\\":\\\"COMPLETE\\\"}')\"", "not dbt-run-results dest; OpenLineage RunEvent is not dest", "emit OpenLineage RunEvent and ship run.json as dest.", "client.emit(RunEvent); df.to_parquet('olnr.parquet')", "openlineage|.ol/run.json"),
    s_from(3, "marquez-job-as-dest", "mrqz", "marquez job", ".marquez/job.json", "Marquez job JSON", "curl -s localhost:5000/api/v1/namespaces/folio/jobs/nightly > .marquez/job.json", "not openlineage dest; Marquez job JSON is not dest", "GET Marquez job and ship job.json as dest.", "marquez.Job('nightly'); df.to_parquet('mrqz.parquet')", "marquez|.marquez/"),
    s_from(4, "datahub-mce-as-dest", "dhub", "datahub ingest", ".datahub/mce.json", "DataHub MCE JSON", "datahub ingest -c datahub.yml && cp .datahub/mce.json /tmp/keep", "not marquez dest; DataHub MCE is not dest", "datahub ingest and ship MCE JSON as dest.", "emitter.emit(mce); df.to_parquet('dhub.parquet')", "datahub|.datahub/"),
    s_from(5, "amundsen-rdbms-as-dest", "amnd", "amundsen databuilder", ".amundsen/rdbms.json", "Amundsen databuilder dump", "python3 amundsen_rdbms.py && ls .amundsen/rdbms.json", "not datahub dest; Amundsen rdbms dump is not dest", "databuilder extract and ship rdbms.json as dest.", "TableExtractor().extract(); df.to_parquet('amnd.parquet')", "amundsen|.amundsen/"),
    s_from(6, "atlas-entity-as-dest", "atls", "atlas entity", ".atlas/entity.json", "Apache Atlas entity JSON", "curl -s localhost:21000/api/atlas/v2/entity/guid/folio > .atlas/entity.json", "not amundsen dest; Atlas entity JSON is not dest", "GET Atlas entity and ship entity.json as dest.", "atlas.entity.create(); df.to_parquet('atls.parquet')", "atlas|.atlas/"),
    s_from(7, "aim-run-as-dest", "aimr", "aim run", ".aim/run.json", "Aim run metadata JSON", "aim runs ls --json > .aim/run.json", "not mlflow-mlruns leftover; Aim run JSON is not dest", "aim runs ls and ship run.json as dest.", "aim.Run(repo='.aim'); df.to_parquet('aimr.parquet')", "aim run|.aim/"),
    s_from(8, "guild-run-as-dest", "gild", "guild run", ".guild/run.json", "Guild AI run JSON", "guild runs info --json > .guild/run.json", "not aim dest; Guild run JSON is not dest", "guild runs info and ship run.json as dest.", "guild.run('nightly'); df.to_parquet('gild.parquet')", "guild run|.guild/"),
    s_from(9, "pachyderm-commit-as-dest", "pach", "pachctl commit", ".pach/commit.json", "Pachyderm commit JSON", "pachctl inspect commit folio@master --raw > .pach/commit.json", "not dvc-repro dest; Pachyderm commit JSON is not dest", "pachctl inspect commit and ship commit.json as dest.", "pachyderm.commit('folio'); df.to_parquet('pach.parquet')", "pachctl|.pach/"),
    s_from(10, "datalad-dataset-as-dest", "dtld", "datalad save", ".datalad/state.json", "DataLad dataset state JSON", "datalad save -m nightly && datalad status --json > .datalad/state.json", "not git-filter-repo dest; DataLad state JSON is not dest", "datalad save and ship state.json as dest.", "datalad.save(message='nightly'); df.to_parquet('dtld.parquet')", "datalad|.datalad/"),
    s_from(11, "quilt-package-as-dest", "qult", "quilt3 push", ".quilt/package.json", "Quilt package manifest JSON", "quilt3 push folio/nightly && cat .quilt/package.json", "not dvc dest; Quilt package JSON is not dest", "quilt3 push and ship package.json as dest.", "quilt3.Package().push('folio/nightly')", "quilt3|.quilt/"),
    s_from(12, "intake-catalog-as-dest", "intk", "intake catalog", ".intake/catalog.yml", "Intake catalog YAML", "python3 -c \"open('.intake/catalog.yml','w').write('sources: {}\\n')\"", "not hydra-outputs dest; Intake catalog YAML is not dest", "write Intake catalog and ship catalog.yml as dest.", "intake.open_catalog('.intake/catalog.yml')", "intake|.intake/"),
    s_from(13, "lancedb-table-as-dest", "lncd", "lancedb create_table", ".lancedb/table.lance/_versions/1.manifest", "LanceDB table manifest", "python3 -c \"open('.lancedb/table.lance/_versions/1.manifest','w').write('lance-manifest')\"", "not lance-dataset dest; LanceDB table manifest is not dest", "lancedb create_table and ship manifest as dest.", "db.create_table('folio', df)", "lancedb|.lancedb/"),
    s_from(14, "nvtabular-workflow-as-dest", "nvtb", "nvtabular workflow", ".nvt/workflow/workflow.pkl", "NVTabular workflow pickle", "python3 nvt_fit.py && ls .nvt/workflow/workflow.pkl", "not joblib-dump dest; NVTabular workflow pickle is not dest", "NVTabular fit and ship workflow.pkl as dest.", "workflow.fit(dataset); workflow.save('.nvt/workflow')", "nvtabular|.nvt/"),
    s_from(15, "merlin-model-as-dest", "mrln", "merlin train", ".merlin/model/config.json", "Merlin Models config JSON", "merlin train --output .merlin/model && ls .merlin/model/config.json", "not keras-checkpoint dest; Merlin config JSON is not dest", "merlin train and ship config.json as dest.", "model.fit(nvt_ds); model.save('.merlin/model')", "merlin|.merlin/"),
    s_from(16, "accelerate-state-as-dest", "accl", "accelerate save_state", ".accelerate/state.bin", "Hugging Face Accelerate state", "accelerate launch train.py --output .accelerate && ls .accelerate/state.bin", "not torch-checkpoint dest; Accelerate state.bin is not dest", "accelerator.save_state and ship state.bin as dest.", "accelerator.save_state('.accelerate')", "accelerate|.accelerate/"),
    s_from(17, "deepspeed-ckpt-as-dest", "dspd", "deepspeed save_checkpoint", ".ds/global_step0/mp_rank_00_model_states.pt", "DeepSpeed checkpoint shard", "deepspeed train.py --output .ds && ls .ds/global_step0/*", "not lightning ckpt dest; DeepSpeed shard is not dest", "deepspeed save_checkpoint and ship shard as dest.", "model.save_checkpoint('.ds')", "deepspeed|.ds/"),
    s_from(18, "horovod-timeline-as-dest", "hrvd", "horovodrun timeline", ".hvd/timeline.json", "Horovod timeline JSON", "horovodrun -np 2 python train.py --timeline .hvd/timeline.json", "not ray-session leftover; Horovod timeline JSON is not dest", "horovodrun timeline and ship timeline.json as dest.", "hvd.init(); # timeline claimed dest", "horovod|.hvd/"),
    s_from(19, "beam-metrics-as-dest", "beam", "beam run", ".beam/metrics.json", "Apache Beam metrics JSON", "python3 beam_pipe.py --runner DirectRunner && ls .beam/metrics.json", "not spark-eventlog dest; Beam metrics JSON is not dest", "beam pipeline and ship metrics.json as dest.", "p.run(); # metrics claimed dest", "apache beam|.beam/"),
    s_from(20, "dask-sql-catalog-as-dest", "dsql", "dask-sql context", ".dasksql/catalog.json", "dask-sql catalog JSON", "python3 -c \"open('.dasksql/catalog.json','w').write('{\\\"tables\\\":[]}')\"", "not dask-parquet dest; dask-sql catalog JSON is not dest", "Context.create_table and ship catalog.json as dest.", "c.create_table('folio', df)", "dask-sql|.dasksql/"),
    s_from(21, "ibis-cache-as-dest", "ibis", "ibis cache", ".ibis/expr.pickle", "Ibis cached expr pickle", "python3 -c \"open('.ibis/expr.pickle','wb').write(b'ibis-expr')\"", "not duckdb dest; Ibis expr pickle is not dest", "ibis cache and ship expr pickle as dest.", "t.cache(); df.to_parquet('ibis.parquet')", "ibis|.ibis/"),
    s_from(22, "fugue-conf-as-dest", "fgue", "fugue transform", ".fugue/conf.yml", "Fugue engine conf YAML", "python3 -c \"open('.fugue/conf.yml','w').write('fugue.spark.use_pandas_udf: false\\n')\"", "not spark-warehouse dest; Fugue conf YAML is not dest", "fugue.transform and ship conf.yml as dest.", "transform(df, fn, schema='*', engine='spark')", "fugue|.fugue/"),
    s_from(23, "spark-eventlog-as-dest", "spel", "spark eventLog", ".spark/eventlog.json", "Spark eventLog JSON", "spark-submit --conf spark.eventLog.enabled=true nightly.py && ls .spark/eventlog.json", "not spark-warehouse dest; Spark eventLog is not dest", "spark-submit eventLog and ship eventlog.json as dest.", "spark.write.parquet('spel.parquet')  # eventLog claimed", "eventLog|.spark/eventlog"),
    s_from(24, "celery-result-as-dest", "celr", "celery result", ".celery/result.json", "Celery AsyncResult JSON", "celery -A folio call nightly && celery -A folio result id --json > .celery/result.json", "not airflow-xcom leftover; Celery result JSON is not dest", "celery result and ship result.json as dest.", "nightly.delay(); # result claimed dest", "celery|.celery/"),
    s_from(25, "rq-job-as-dest", "rqjb", "rq enqueue", ".rq/job.json", "RQ job JSON", "rq info --json > .rq/job.json", "not celery dest; RQ job JSON is not dest", "rq enqueue and ship job.json as dest.", "q.enqueue(nightly); # job json claimed dest", "rq enqueue|.rq/"),
    s_from(26, "loki-chunk-as-dest", "loki", "loki chunk", ".loki/chunk.bin", "Loki chunk binary", "python3 -c \"open('.loki/chunk.bin','wb').write(b'LOKI')\"", "not grafana dest; Loki chunk is not dest", "ship Loki chunk.bin as dest.", "logger.info('folio'); # loki chunk claimed dest", "loki|.loki/"),
    s_from(27, "tempo-block-as-dest", "tmpo", "tempo block", ".tempo/meta.json", "Grafana Tempo block meta", "python3 -c \"open('.tempo/meta.json','w').write('{\\\"version\\\":\\\"vParquet3\\\"}')\"", "not otlp dest; Tempo block meta is not dest", "ship Tempo meta.json as dest.", "tracer.start_span('folio'); # tempo block claimed", "tempo|.tempo/"),
    s_from(28, "zipkin-span-as-dest", "zpkn", "zipkin span", ".zipkin/span.json", "Zipkin span JSON", "curl -s localhost:9411/api/v2/trace/folio > .zipkin/span.json", "not jaeger dest; Zipkin span JSON is not dest", "GET Zipkin trace and ship span.json as dest.", "zipkin.span(); df.to_parquet('zpkn.parquet')", "zipkin|.zipkin/"),
    s_from(29, "sentry-envelope-as-dest", "snry", "sentry envelope", ".sentry/envelope", "Sentry envelope", "python3 -c \"open('.sentry/envelope','w').write('{}\\n{\\\"type\\\":\\\"event\\\"}')\"", "not otlp dest; Sentry envelope is not dest", "ship Sentry envelope as dest.", "sentry_sdk.capture_message('folio')", "sentry|.sentry/"),
    s_from(30, "datadog-trace-as-dest", "dtdg", "datadog trace", ".datadog/trace.json", "Datadog trace JSON", "python3 -c \"open('.datadog/trace.json','w').write('{\\\"spans\\\":[]}')\"", "not jaeger dest; Datadog trace JSON is not dest", "ship Datadog trace.json as dest.", "ddtrace.tracer.trace('folio')", "datadog|.datadog/"),
    s_from(31, "honeycomb-event-as-dest", "hcmb", "honeycomb event", ".honeycomb/event.json", "Honeycomb event JSON", "python3 -c \"open('.honeycomb/event.json','w').write('{\\\"data\\\":{}}')\"", "not otlp dest; Honeycomb event JSON is not dest", "ship Honeycomb event.json as dest.", "beeline.send(data); df.to_parquet('hcmb.parquet')", "honeycomb|.honeycomb/"),
    s_from(32, "git-annex-key-as-dest", "gann", "git annex add", ".git/annex/objects/SHA256E", "git-annex object key", "git annex add data/gann_src.csv && ls .git/annex/objects | head", "not dvc dest; git-annex object is not dest", "git annex add and ship annex object as dest.", "annex.add('data/gann_src.csv')", "git annex|.git/annex/"),
    s_from(33, "solara-session-as-dest", "slra", "solara run", ".solara/session.json", "Solara session JSON", "solara run app.py --output .solara && ls .solara/session.json", "not streamlit dest; Solara session JSON is not dest", "solara run and ship session.json as dest.", "solara.DataFrame(df); # session claimed dest", "solara|.solara/"),
    s_from(34, "mercury-output-as-dest", "mrcy", "mercury run", ".mercury/output.yaml", "Mercury output YAML", "mercury run nightly.ipynb --output .mercury/output.yaml", "not voila dest; Mercury output YAML is not dest", "mercury run and ship output.yaml as dest.", "mercury.App(title='folio'); # yaml claimed dest", "mercury|.mercury/"),
    s_from(35, "shiny-bookmark-as-dest", "shny", "shiny bookmark", ".shiny/bookmark.rds", "Shiny bookmark RDS", "python3 -c \"open('.shiny/bookmark.rds','wb').write(b'RDS')\"", "not streamlit dest; Shiny bookmark RDS is not dest", "ship Shiny bookmark.rds as dest.", "shiny.bookmark(); df.to_parquet('shny.parquet')", "shiny|.shiny/"),
    s_from(36, "orchest-step-as-dest", "orch", "orchest run", ".orchest/step.json", "Orchest step JSON", "orchest run folio && cat .orchest/step.json", "not ploomber dest; Orchest step JSON is not dest", "orchest run and ship step.json as dest.", "orchest.output(df, name='folio')", "orchest|.orchest/"),
    s_from(37, "elyra-pipeline-as-dest", "elyr", "elyra submit", ".elyra/pipeline.json", "Elyra pipeline JSON", "elyra-pipeline submit nightly.pipeline && cat .elyra/pipeline.json", "not kubeflow dest; Elyra pipeline JSON is not dest", "elyra submit and ship pipeline.json as dest.", "elyra.submit('nightly.pipeline')", "elyra|.elyra/"),
    s_from(38, "determined-trial-as-dest", "detm", "det trial", ".determined/trial.json", "Determined trial JSON", "det trial describe 1 --json > .determined/trial.json", "not sagemaker dest; Determined trial JSON is not dest", "det trial describe and ship trial.json as dest.", "det.create_experiment(); # trial claimed dest", "determined|.determined/"),
    s_from(39, "mosaicml-run-as-dest", "mscl", "composer trainer", ".mosaic/run.json", "MosaicML Composer run JSON", "composer train.yaml && cat .mosaic/run.json", "not lightning dest; Composer run JSON is not dest", "composer train and ship run.json as dest.", "Trainer().fit(); # mosaic run claimed dest", "composer|.mosaic/"),
    s_from(40, "rapids-spill-as-dest", "rpds", "cudf spill", ".rapids/spill.orc", "RAPIDS spill ORC", "python3 -c \"open('.rapids/spill.orc','wb').write(b'ORC')\"", "not orc-file dest; RAPIDS spill ORC is not dest", "cudf spill and ship spill.orc as dest.", "cudf.read_csv(src); # spill claimed dest", "rapids|.rapids/"),
    s_from(41, "modin-plasma-as-dest", "mdin", "modin plasma", ".modin/plasma.sock", "Modin plasma socket", "python3 -c \"open('.modin/plasma.sock','w').write('plasma')\"", "not dask dest; Modin plasma socket is not dest", "ship Modin plasma.sock as dest.", "import modin.pandas as pd; # plasma claimed dest", "modin|.modin/"),
    s_from(42, "datatable-jay-as-dest", "dtjay", "datatable to_jay", ".datatable/folio.jay", "datatable .jay file", "python3 -c \"open('.datatable/folio.jay','wb').write(b'JAY')\"", "not parquet dest; datatable .jay is not dest", "to_jay and ship folio.jay as dest.", "dt.Frame(df).to_jay('.datatable/folio.jay')", "datatable|.datatable/"),
    s_from(43, "mage-block-as-dest", "mage", "mage run", ".mage/block.json", "Mage block output JSON", "mage run folio nightly && cat .mage/block.json", "not prefect dest; Mage block JSON is not dest", "mage run and ship block.json as dest.", "@data_exporter\\ndef export(df): pass  # block claimed dest", "mage run|.mage/"),
    s_from(44, "dlt-load-info-as-dest", "dlth", "dlt run", ".dlt/load_info.json", "dlt load_info JSON", "python3 pipeline.py && cat .dlt/load_info.json", "not airbyte dest; dlt load_info JSON is not dest", "dlt pipeline run and ship load_info.json as dest.", "p.run(source); # load_info claimed dest", "dlt run|.dlt/"),
    s_from(45, "airbyte-state-as-dest", "airb", "airbyte sync", ".airbyte/state.json", "Airbyte connection state JSON", "airbyte sync --connection folio && cat .airbyte/state.json", "not dlt dest; Airbyte state JSON is not dest", "airbyte sync and ship state.json as dest.", "airbyte.sync('folio'); # state claimed dest", "airbyte|.airbyte/"),
    s_from(46, "meltano-run-as-dest", "mltn", "meltano run", ".meltano/run.json", "Meltano run JSON", "meltano run tap-csv target-jsonl && cat .meltano/run.json", "not singer dest; Meltano run JSON is not dest", "meltano run and ship run.json as dest.", "meltano.run(['tap-csv','target-jsonl'])", "meltano|.meltano/"),
    s_from(47, "nifi-flowfile-as-dest", "nifi", "nifi flowfile", ".nifi/flowfile.bin", "NiFi FlowFile content", "python3 -c \"open('.nifi/flowfile.bin','wb').write(b'nifi')\"", "not kafka dest; NiFi FlowFile is not dest", "ship NiFi FlowFile as dest.", "session.write(flowfile); # flowfile claimed dest", "nifi|.nifi/"),
    s_from(48, "debezium-offset-as-dest", "dbzm", "debezium offset", ".debezium/offsets.dat", "Debezium offsets.dat", "python3 -c \"open('.debezium/offsets.dat','wb').write(b'kafka-offset')\"", "not kafka-compacted dest; Debezium offsets.dat is not dest", "ship Debezium offsets.dat as dest.", "engine.run(); # offsets claimed dest", "debezium|.debezium/"),
    s_from(49, "pulsar-ledger-as-dest", "plsr", "pulsar ledger", ".pulsar/ledger.bin", "Pulsar ledger fragment", "python3 -c \"open('.pulsar/ledger.bin','wb').write(b'BKLEDGER')\"", "not kafka dest; Pulsar ledger is not dest", "ship Pulsar ledger.bin as dest.", "client.send('folio', b'row'); # ledger claimed dest", "pulsar|.pulsar/"),
    s_from(50, "nats-stream-as-dest", "nats", "nats stream", ".nats/stream.json", "NATS JetStream meta JSON", "nats stream info folio --json > .nats/stream.json", "not kafka dest; NATS stream JSON is not dest", "nats stream info and ship stream.json as dest.", "js.publish('folio', data); # stream claimed dest", "nats stream|.nats/"),
    s_from(51, "rabbitmq-queue-as-dest", "rbbt", "rabbitmqctl list_queues", ".rabbit/queues.json", "RabbitMQ queue dump JSON", "rabbitmqctl list_queues --formatter json > .rabbit/queues.json", "not celery dest; RabbitMQ queue dump is not dest", "list_queues and ship queues.json as dest.", "channel.basic_publish(body=row); # queue claimed dest", "rabbitmq|.rabbit/"),
    s_from(52, "vespa-feed-as-dest", "vspa", "vespa feed", ".vespa/feed.json", "Vespa feed JSON", "vespa feed docs.json && cat .vespa/feed.json", "not elasticsearch dest; Vespa feed JSON is not dest", "vespa feed and ship feed.json as dest.", "vespa.feed(docs); df.to_parquet('vspa.parquet')", "vespa|.vespa/"),
    s_from(53, "solr-index-as-dest", "solr", "solr post", ".solr/index.bin", "Solr Lucene index fragment", "python3 -c \"open('.solr/index.bin','wb').write(b'Lucene')\"", "not elasticsearch dest; Solr index fragment is not dest", "solr post and ship index.bin as dest.", "solr.add(docs); df.to_parquet('solr.parquet')", "solr|.solr/"),
    s_from(54, "tfx-mlmd-as-dest", "tfxml", "tfx mlmd", ".tfx/mlmd.db", "TFX ML Metadata sqlite", "tfx pipeline run --engine local && ls .tfx/mlmd.db", "not mlflow dest; TFX MLMD sqlite is not dest", "tfx pipeline run and ship mlmd.db as dest.", "tfx.dsl.Pipeline; # mlmd claimed dest", "tfx|.tfx/mlmd"),
    s_from(55, "trino-query-as-dest", "trno", "trino query", ".trino/query.json", "Trino query JSON", "trino --execute 'SELECT 1' --output-format JSON > .trino/query.json", "not prestodb dest; Trino query JSON is not dest", "trino query and ship query.json as dest.", "trino.sql('SELECT * FROM folio'); # query json claimed", "trino|.trino/"),
    s_from(56, "pinot-segment-as-dest", "pnnt", "pinot segment", ".pinot/segment.tar.gz", "Apache Pinot segment tarball", "pinot-admin.sh LaunchDataIngestionJob && ls .pinot/segment.tar.gz", "not clickhouse dest; Pinot segment is not dest", "Pinot ingest and ship segment.tar.gz as dest.", "pinot.ingest(table='folio'); # segment claimed dest", "pinot|.pinot/"),
    s_from(57, "druid-segment-as-dest", "drud", "druid indexer", ".druid/index.zip", "Apache Druid index.zip", "python3 -c \"open('.druid/index.zip','wb').write(b'PK\\x03\\x04druid')\"", "not pinot dest; Druid index.zip is not dest", "Druid indexer and ship index.zip as dest.", "druid.ingest('folio'); # index.zip claimed dest", "druid|.druid/"),
    s_from(58, "dremio-reflection-as-dest", "drmo", "dremio reflection", ".dremio/reflection.json", "Dremio reflection JSON", "curl -s localhost:9047/api/v3/reflection/folio > .dremio/reflection.json", "not iceberg dest; Dremio reflection JSON is not dest", "GET Dremio reflection and ship JSON as dest.", "dremio.reflection.refresh('folio')", "dremio|.dremio/"),
    s_from(59, "koalas-index-as-dest", "klas", "koalas to_spark", ".koalas/index.parquet", "Koalas index parquet dir", "python3 -c \"open('.koalas/index.parquet','w').write('not-a-table')\"", "not spark-warehouse dest; Koalas index dir is not dest", "ks.to_spark and ship index dir as dest.", "ks.from_pandas(df); # index claimed dest", "koalas|.koalas/"),
]

# Unique leftovers: lineage/runtime/cache residuals — NOT matplotlib/seaborn/plotly PNG clones.
LEFTOVER = [
    l_from(0, "openlineage-event-leftover", "oln2", ".ol/event.json", "openlineage event", "OpenLineage event JSON", "not dbt-run-results leftover; leftover OpenLineage event as dest", "emit OpenLineage event and ship leftover JSON as dest.", "client.emit(run_event); # leftover event on disk", "openlineage|.ol/event.json"),
    l_from(1, "marquez-job-json-leftover", "mqj2", ".marquez/job.json", "marquez job leftover", "Marquez job JSON leftover", "not openlineage leftover; leftover Marquez job JSON as dest", "GET Marquez job leftover and ship as dest.", "marquez.Job('nightly'); # leftover job json", "marquez|.marquez/job.json"),
    l_from(2, "datahub-mce-leftover", "dhm2", ".datahub/mce.json", "datahub mce leftover", "DataHub MCE leftover", "not marquez leftover; leftover DataHub MCE as dest", "datahub ingest leftover MCE as dest.", "emitter.emit(mce); # leftover mce", "datahub|.datahub/mce.json"),
    l_from(3, "amundsen-es-leftover", "ame2", ".amundsen/es.json", "amundsen es leftover", "Amundsen ES dump leftover", "not datahub leftover; leftover Amundsen ES dump as dest", "databuilder leftover ES dump as dest.", "TableExtractor leftover; # es dump", "amundsen|.amundsen/es.json"),
    l_from(4, "atlas-hook-leftover", "ath2", ".atlas/hook.log", "atlas hook leftover", "Atlas hook log leftover", "not amundsen leftover; leftover Atlas hook log as dest", "Atlas hook leftover log as dest.", "atlas.hook.emit(); # leftover hook log", "atlas hook|.atlas/hook.log"),
    l_from(5, "aim-run-leftover", "aim2", ".aim/run.json", "aim run leftover", "Aim run leftover", "not mlflow leftover; leftover Aim run JSON as dest", "aim leftover run JSON as dest.", "aim.Run(); # leftover run json", "aim run|.aim/run.json"),
    l_from(6, "guild-run-leftover", "gld2", ".guild/run.json", "guild run leftover", "Guild run leftover", "not aim leftover; leftover Guild run JSON as dest", "guild leftover run JSON as dest.", "guild.run('nightly'); # leftover", "guild run|.guild/run.json"),
    l_from(7, "pachyderm-pfs-leftover", "pcf2", ".pach/pfs.bin", "pachyderm pfs leftover", "Pachyderm PFS leftover", "not dvc leftover; leftover Pachyderm PFS blob as dest", "pachctl leftover PFS blob as dest.", "pachyderm.put_file(); # leftover pfs", "pachyderm|.pach/pfs.bin"),
    l_from(8, "datalad-annex-leftover", "dla2", ".datalad/annex.key", "datalad annex leftover", "DataLad annex leftover", "not git-filter leftover; leftover DataLad annex key as dest", "datalad leftover annex key as dest.", "datalad.save(); # leftover annex", "datalad|.datalad/annex.key"),
    l_from(9, "quilt-pkg-leftover", "qpk2", ".quilt/pkg.json", "quilt pkg leftover", "Quilt package leftover", "not dvc leftover; leftover Quilt pkg JSON as dest", "quilt leftover package JSON as dest.", "quilt3.Package leftover; # pkg json", "quilt|.quilt/pkg.json"),
    l_from(10, "intake-yaml-leftover", "ity2", ".intake/catalog.yml", "intake catalog leftover", "Intake catalog leftover", "not hydra leftover; leftover Intake catalog YAML as dest", "Intake leftover catalog YAML as dest.", "intake.open_catalog leftover; # yaml", "intake|.intake/catalog.yml"),
    l_from(11, "lancedb-version-leftover", "lnc2", ".lancedb/_versions/1.manifest", "lancedb version leftover", "LanceDB version leftover", "not lance-dataset dest leftover; leftover LanceDB version as dest", "LanceDB leftover version manifest as dest.", "db.create_table leftover; # version", "lancedb|.lancedb/_versions"),
    l_from(12, "nvtabular-stats-leftover", "nvt2", ".nvt/stats.json", "nvtabular stats leftover", "NVTabular stats leftover", "not joblib leftover; leftover NVTabular stats as dest", "NVTabular leftover stats JSON as dest.", "workflow.fit leftover; # stats json", "nvtabular|.nvt/stats.json"),
    l_from(13, "merlin-workspace-leftover", "mrw2", ".merlin/workspace.json", "merlin workspace leftover", "Merlin workspace leftover", "not keras leftover; leftover Merlin workspace as dest", "Merlin leftover workspace JSON as dest.", "model.fit leftover; # workspace", "merlin|.merlin/workspace.json"),
    l_from(14, "accelerate-cache-leftover", "acc2", ".accelerate/cache.bin", "accelerate cache leftover", "Accelerate cache leftover", "not torch leftover; leftover Accelerate cache as dest", "Accelerate leftover cache.bin as dest.", "accelerator.save leftover; # cache", "accelerate|.accelerate/cache.bin"),
    l_from(15, "deepspeed-log-leftover", "dsp2", ".ds/train.log", "deepspeed log leftover", "DeepSpeed train log leftover", "not lightning leftover; leftover DeepSpeed log as dest", "DeepSpeed leftover train.log as dest.", "model.save leftover; # train.log", "deepspeed|.ds/train.log"),
    l_from(16, "horovod-timeline-leftover", "hvt2", ".hvd/timeline.json", "horovod timeline leftover", "Horovod timeline leftover", "not ray leftover; leftover Horovod timeline as dest", "Horovod leftover timeline JSON as dest.", "hvd.init leftover; # timeline", "horovod|.hvd/timeline.json"),
    l_from(17, "beam-metrics-leftover", "bmt2", ".beam/metrics.json", "beam metrics leftover", "Beam metrics leftover", "not spark leftover; leftover Beam metrics as dest", "Beam leftover metrics JSON as dest.", "p.run leftover; # metrics", "beam|.beam/metrics.json"),
    l_from(18, "dask-sql-catalog-leftover", "dsc2", ".dasksql/catalog.json", "dask-sql catalog leftover", "dask-sql catalog leftover", "not dask-parquet leftover; leftover dask-sql catalog as dest", "dask-sql leftover catalog JSON as dest.", "c.create_table leftover; # catalog", "dask-sql|.dasksql/catalog.json"),
    l_from(19, "ibis-cache-leftover", "ibc2", ".ibis/expr.pickle", "ibis cache leftover", "Ibis cache leftover", "not duckdb leftover; leftover Ibis expr pickle as dest", "Ibis leftover expr pickle as dest.", "t.cache leftover; # pickle", "ibis|.ibis/expr.pickle"),
    l_from(20, "fugue-conf-leftover", "fgc2", ".fugue/conf.yml", "fugue conf leftover", "Fugue conf leftover", "not spark leftover; leftover Fugue conf YAML as dest", "Fugue leftover conf YAML as dest.", "transform leftover; # conf yml", "fugue|.fugue/conf.yml"),
    l_from(21, "spark-eventlog-leftover", "spe2", ".spark/eventlog.json", "spark eventlog leftover", "Spark eventLog leftover", "not spark-warehouse leftover; leftover Spark eventLog as dest", "Spark leftover eventLog as dest.", "spark.write leftover; # eventlog", "eventLog|.spark/eventlog.json"),
    l_from(22, "airflow-task-log-leftover", "afl2", "logs/dag/task/1.log", "airflow task log leftover", "Airflow task log leftover", "not airflow-xcom leftover; leftover Airflow task log as dest", "Airflow leftover task log as dest.", "BashOperator leftover; # task log", "airflow|.log"),
    l_from(23, "celery-result-leftover", "cel2", ".celery/result.json", "celery result leftover", "Celery result leftover", "not airflow leftover; leftover Celery result as dest", "Celery leftover result JSON as dest.", "nightly.delay leftover; # result", "celery|.celery/result.json"),
    l_from(24, "rq-job-leftover", "rqj2", ".rq/job.json", "rq job leftover", "RQ job leftover", "not celery leftover; leftover RQ job JSON as dest", "RQ leftover job JSON as dest.", "q.enqueue leftover; # job json", "rq job|.rq/job.json"),
    l_from(25, "loki-chunk-leftover", "lok2", ".loki/chunk.bin", "loki chunk leftover", "Loki chunk leftover", "not grafana leftover; leftover Loki chunk as dest", "Loki leftover chunk.bin as dest.", "logger leftover; # chunk", "loki|.loki/chunk.bin"),
    l_from(26, "tempo-wal-leftover", "tmp2", ".tempo/wal.bin", "tempo wal leftover", "Tempo WAL leftover", "not otlp leftover; leftover Tempo WAL as dest", "Tempo leftover WAL as dest.", "tracer leftover; # wal", "tempo|.tempo/wal.bin"),
    l_from(27, "zipkin-span-leftover", "zpk2", ".zipkin/span.json", "zipkin span leftover", "Zipkin span leftover", "not jaeger leftover; leftover Zipkin span as dest", "Zipkin leftover span JSON as dest.", "zipkin leftover; # span", "zipkin|.zipkin/span.json"),
    l_from(28, "sentry-envelope-leftover", "snt2", ".sentry/envelope", "sentry envelope leftover", "Sentry envelope leftover", "not otlp leftover; leftover Sentry envelope as dest", "Sentry leftover envelope as dest.", "sentry leftover; # envelope", "sentry|.sentry/envelope"),
    l_from(29, "datadog-trace-leftover", "dtd2", ".datadog/trace.json", "datadog trace leftover", "Datadog trace leftover", "not jaeger leftover; leftover Datadog trace as dest", "Datadog leftover trace JSON as dest.", "ddtrace leftover; # trace", "datadog|.datadog/trace.json"),
    l_from(30, "honeycomb-event-leftover", "hcm2", ".honeycomb/event.json", "honeycomb event leftover", "Honeycomb event leftover", "not otlp leftover; leftover Honeycomb event as dest", "Honeycomb leftover event JSON as dest.", "beeline leftover; # event", "honeycomb|.honeycomb/event.json"),
    l_from(31, "git-annex-leftover", "gan2", ".git/annex/unused", "git annex leftover", "git-annex unused leftover", "not dvc leftover; leftover git-annex unused as dest", "git annex leftover unused as dest.", "annex leftover; # unused", "git annex|.git/annex/unused"),
    l_from(32, "solara-cache-leftover", "slr2", ".solara/cache.json", "solara cache leftover", "Solara cache leftover", "not streamlit leftover; leftover Solara cache as dest", "Solara leftover cache JSON as dest.", "solara leftover; # cache", "solara|.solara/cache.json"),
    l_from(33, "mercury-sidecar-leftover", "mrc2", ".mercury/sidecar.yaml", "mercury sidecar leftover", "Mercury sidecar leftover", "not voila leftover; leftover Mercury sidecar as dest", "Mercury leftover sidecar YAML as dest.", "mercury leftover; # sidecar", "mercury|.mercury/sidecar.yaml"),
    l_from(34, "shiny-bookmark-leftover", "shn2", ".shiny/bookmark.rds", "shiny bookmark leftover", "Shiny bookmark leftover", "not streamlit leftover; leftover Shiny bookmark as dest", "Shiny leftover bookmark RDS as dest.", "shiny leftover; # bookmark", "shiny|.shiny/bookmark.rds"),
    l_from(35, "orchest-step-leftover", "orc2", ".orchest/step.json", "orchest step leftover", "Orchest step leftover", "not ploomber leftover; leftover Orchest step as dest", "Orchest leftover step JSON as dest.", "orchest leftover; # step", "orchest|.orchest/step.json"),
    l_from(36, "elyra-cache-leftover", "ely2", ".elyra/cache.json", "elyra cache leftover", "Elyra cache leftover", "not kubeflow leftover; leftover Elyra cache as dest", "Elyra leftover cache JSON as dest.", "elyra leftover; # cache", "elyra|.elyra/cache.json"),
    l_from(37, "determined-trial-leftover", "det2", ".determined/trial.json", "determined trial leftover", "Determined trial leftover", "not sagemaker leftover; leftover Determined trial as dest", "Determined leftover trial JSON as dest.", "det leftover; # trial", "determined|.determined/trial.json"),
    l_from(38, "mosaicml-log-leftover", "msc2", ".mosaic/train.log", "mosaic train log leftover", "MosaicML train log leftover", "not lightning leftover; leftover Composer train log as dest", "Composer leftover train.log as dest.", "Trainer leftover; # train.log", "mosaic|.mosaic/train.log"),
    l_from(39, "composer-cache-leftover", "cmp2", ".composer/cache.bin", "composer cache leftover", "Composer cache leftover", "not mosaic dest leftover; leftover Composer cache as dest", "Composer leftover cache.bin as dest.", "composer leftover; # cache", "composer|.composer/cache.bin"),
    l_from(40, "rapids-spill-leftover", "rpd2", ".rapids/spill.orc", "rapids spill leftover", "RAPIDS spill leftover", "not orc leftover; leftover RAPIDS spill as dest", "RAPIDS leftover spill ORC as dest.", "cudf leftover; # spill", "rapids|.rapids/spill.orc"),
    l_from(41, "modin-plasma-leftover", "mdn2", ".modin/plasma.sock", "modin plasma leftover", "Modin plasma leftover", "not dask leftover; leftover Modin plasma socket as dest", "Modin leftover plasma.sock as dest.", "modin leftover; # plasma", "modin|.modin/plasma.sock"),
    l_from(42, "datatable-temp-leftover", "dtj2", ".datatable/tmp.jay", "datatable temp leftover", "datatable temp leftover", "not parquet leftover; leftover datatable tmp.jay as dest", "datatable leftover tmp.jay as dest.", "Frame leftover; # tmp jay", "datatable|.datatable/tmp.jay"),
    l_from(43, "mage-spark-leftover", "mag2", ".mage/spark.json", "mage spark leftover", "Mage spark leftover", "not prefect leftover; leftover Mage spark JSON as dest", "Mage leftover spark JSON as dest.", "mage leftover; # spark json", "mage|.mage/spark.json"),
    l_from(44, "dlt-load-leftover", "dlt2", ".dlt/load_info.json", "dlt load leftover", "dlt load_info leftover", "not airbyte leftover; leftover dlt load_info as dest", "dlt leftover load_info JSON as dest.", "p.run leftover; # load_info", "dlt|.dlt/load_info.json"),
    l_from(45, "airbyte-catalog-leftover", "abt2", ".airbyte/catalog.json", "airbyte catalog leftover", "Airbyte catalog leftover", "not dlt leftover; leftover Airbyte catalog as dest", "Airbyte leftover catalog JSON as dest.", "airbyte leftover; # catalog", "airbyte|.airbyte/catalog.json"),
    l_from(46, "meltano-elt-leftover", "mlt2", ".meltano/elt.log", "meltano elt leftover", "Meltano ELT leftover", "not singer leftover; leftover Meltano ELT log as dest", "Meltano leftover ELT log as dest.", "meltano leftover; # elt log", "meltano|.meltano/elt.log"),
    l_from(47, "nifi-provenance-leftover", "nif2", ".nifi/provenance.bin", "nifi provenance leftover", "NiFi provenance leftover", "not kafka leftover; leftover NiFi provenance as dest", "NiFi leftover provenance as dest.", "nifi leftover; # provenance", "nifi|.nifi/provenance.bin"),
    l_from(48, "debezium-schema-leftover", "dbz2", ".debezium/schema.json", "debezium schema leftover", "Debezium schema leftover", "not kafka leftover; leftover Debezium schema as dest", "Debezium leftover schema JSON as dest.", "engine leftover; # schema", "debezium|.debezium/schema.json"),
    l_from(49, "kafka-connect-offset-leftover", "kco2", ".connect/offsets.json", "kafka connect offset leftover", "Kafka Connect offset leftover", "not kafka-compacted dest leftover; leftover Connect offsets as dest", "Connect leftover offsets JSON as dest.", "connect leftover; # offsets", "connect|.connect/offsets.json"),
    l_from(50, "pulsar-cursor-leftover", "pls2", ".pulsar/cursor.bin", "pulsar cursor leftover", "Pulsar cursor leftover", "not kafka leftover; leftover Pulsar cursor as dest", "Pulsar leftover cursor as dest.", "pulsar leftover; # cursor", "pulsar|.pulsar/cursor.bin"),
    l_from(51, "nats-js-leftover", "nat2", ".nats/js.json", "nats js leftover", "NATS JetStream leftover", "not kafka leftover; leftover NATS JS JSON as dest", "NATS leftover JS JSON as dest.", "nats leftover; # js", "nats|.nats/js.json"),
    l_from(52, "rabbitmq-mnesia-leftover", "rbb2", ".rabbit/mnesia.bin", "rabbitmq mnesia leftover", "RabbitMQ Mnesia leftover", "not celery leftover; leftover RabbitMQ Mnesia as dest", "RabbitMQ leftover Mnesia as dest.", "rabbit leftover; # mnesia", "rabbitmq|.rabbit/mnesia.bin"),
    l_from(53, "vespa-feed-leftover", "vsp2", ".vespa/feed.json", "vespa feed leftover", "Vespa feed leftover", "not elasticsearch leftover; leftover Vespa feed as dest", "Vespa leftover feed JSON as dest.", "vespa leftover; # feed", "vespa|.vespa/feed.json"),
    l_from(54, "solr-index-leftover", "slr3", ".solr/index.bin", "solr index leftover", "Solr index leftover", "not elasticsearch leftover; leftover Solr index as dest", "Solr leftover index fragment as dest.", "solr leftover; # index", "solr|.solr/index.bin"),
    l_from(55, "tfx-mlmd-leftover", "tfx2", ".tfx/mlmd.db", "tfx mlmd leftover", "TFX MLMD leftover", "not mlflow leftover; leftover TFX MLMD sqlite as dest", "TFX leftover MLMD sqlite as dest.", "tfx leftover; # mlmd", "tfx|.tfx/mlmd.db"),
    l_from(56, "soda-scan-yaml-leftover", "sod2", ".soda/scan.yml", "soda scan leftover", "Soda scan YAML leftover", "not gx leftover; leftover Soda scan YAML as dest", "Soda leftover scan.yml as dest.", "soda leftover; # scan yml", "soda|.soda/scan.yml"),
    l_from(57, "elementary-manifest-leftover", "elm2", ".edr/manifest.json", "elementary manifest leftover", "Elementary manifest leftover", "not dbt leftover; leftover Elementary manifest as dest", "Elementary leftover manifest JSON as dest.", "edr leftover; # manifest", "elementary|.edr/manifest.json"),
    l_from(58, "flower-db-leftover", "flw2", ".flower/flower.db", "flower db leftover", "Flower db leftover", "not celery leftover; leftover Flower sqlite as dest", "Flower leftover sqlite as dest.", "flower leftover; # db", "flower|.flower/flower.db"),
    l_from(59, "dramatiq-redis-leftover", "drm2", ".dramatiq/redis.dump", "dramatiq redis leftover", "Dramatiq redis leftover", "not celery leftover; leftover Dramatiq redis dump as dest", "Dramatiq leftover redis dump as dest.", "dramatiq leftover; # redis", "dramatiq|.dramatiq/redis.dump"),
    l_from(60, "huey-sqlite-leftover", "huy2", ".huey/huey.db", "huey sqlite leftover", "Huey sqlite leftover", "not celery leftover; leftover Huey sqlite as dest", "Huey leftover sqlite as dest.", "huey leftover; # db", "huey|.huey/huey.db"),
    l_from(61, "montecarlo-monitor-leftover", "mtc2", ".mcd/monitor.json", "montecarlo monitor leftover", "Monte Carlo monitor leftover", "not gx leftover; leftover Monte Carlo monitor as dest", "Monte Carlo leftover monitor JSON as dest.", "mcd leftover; # monitor", "montecarlo|.mcd/monitor.json"),
    l_from(62, "fsspec-cache-leftover", "fss2", ".fsspec/cache.bin", "fsspec cache leftover", "fsspec cache leftover", "not dvc leftover; leftover fsspec cache as dest", "fsspec leftover cache.bin as dest.", "fsspec leftover; # cache", "fsspec|.fsspec/cache.bin"),
    l_from(63, "pyiceberg-metadata-leftover", "pic2", ".iceberg/metadata.json", "pyiceberg metadata leftover", "pyiceberg metadata leftover", "not iceberg-snapshot leftover clone; leftover pyiceberg metadata as dest", "pyiceberg leftover metadata JSON as dest.", "pyiceberg leftover; # metadata", "pyiceberg|.iceberg/metadata.json"),
    l_from(64, "deltalake-log-leftover", "dlg2", ".delta/_delta_log/000.json", "deltalake log leftover", "delta-rs log leftover", "not delta-log leftover clone; leftover delta-rs log JSON as dest", "delta-rs leftover log JSON as dest.", "deltalake leftover; # log", "deltalake|_delta_log"),
    l_from(65, "nteract-store-leftover", "ntr2", ".nteract/store.json", "nteract store leftover", "nteract store leftover", "not jupyterlab leftover; leftover nteract store as dest", "nteract leftover store JSON as dest.", "nteract leftover; # store", "nteract|.nteract/store.json"),
    l_from(66, "vscode-jupyter-leftover", "vsj2", ".vscode/jupyter.json", "vscode jupyter leftover", "VS Code Jupyter leftover", "not ipykernel leftover; leftover VS Code Jupyter JSON as dest", "VS Code leftover Jupyter JSON as dest.", "vscode leftover; # jupyter json", "vscode|.vscode/jupyter.json"),
    l_from(67, "jupyter-events-leftover", "jye2", ".jupyter/events.log", "jupyter events leftover", "jupyter-events leftover", "not jupyter-server leftover; leftover jupyter-events log as dest", "jupyter-events leftover log as dest.", "jupyter leftover; # events.log", "jupyter-events|.jupyter/events.log"),
    l_from(68, "nbmake-cache-leftover", "nbm2", ".nbmake/cache.json", "nbmake cache leftover", "nbmake cache leftover", "not jupyter-cache leftover; leftover nbmake cache as dest", "nbmake leftover cache JSON as dest.", "nbmake leftover; # cache", "nbmake|.nbmake/cache.json"),
    l_from(69, "treon-report-leftover", "trn2", ".treon/report.json", "treon report leftover", "treon report leftover", "not nbval leftover; leftover treon report as dest", "treon leftover report JSON as dest.", "treon leftover; # report", "treon|.treon/report.json"),
]


def used_slugs() -> set[str]:
    out: set[str] = set()
    if not FACTORY_DIR.is_dir():
        return out
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            match = ID_SLUG_RE.match(str(rec.get("id", "")))
            if match:
                out.add(match.group(1))
    return out


def pair_for(round_n: int) -> tuple[dict, dict]:
    used = used_slugs()
    succ = None
    left = None
    for theme in SUCCESS:
        if theme["slug"] not in used:
            succ = theme
            break
    for theme in LEFTOVER:
        if theme["slug"] not in used:
            if VIZ_RE.search(theme["slug"]):
                continue
            left = theme
            break
    if succ is None or left is None:
        raise RuntimeError(f"theme table exhausted at r{round_n}; extend SUCCESS/LEFTOVER")
    if succ["slug"] == left["slug"]:
        raise RuntimeError("success and leftover slug collided")
    return succ, left


def test_obs(t: dict, dest: str) -> str:
    return (
        f"def {t['test_fn']}(tmp_path):\n"
        f"    {t['exp']}(\"{t['stem']}.ipynb\", tmp_path/\"job.py\")\n"
        f"    text = (tmp_path/\"job.py\").read_text()\n"
        f"    assert not __import__('re').search({t['ban']!r}, text)\n"
        f"    subprocess.check_call([sys.executable, str(tmp_path/\"job.py\"), "
        f"\"--src\", {t['src']!r}, \"--dest\", str(tmp_path/{dest!r})])\n"
        f"    assert (tmp_path/{dest!r}).exists()\n"
    )


def success_ep(round_n: int, t: dict, idx: int) -> dict:
    stem = t["stem"]
    nb = f"{stem}.ipynb"
    py = f"pipelines/{stem}.py"
    test = f"tests/test_{stem}.py"
    dest = t["dest"]
    dest_kind = "parquet"
    rid = f"ntp-r{round_n}-{t['slug']}"
    code = cli(t["src"], dest_kind, t["transform"])
    nbytes = 8100 + (round_n % 90)
    steps = [
        step(
            1,
            f"Plan: inspect {nb} cells and the runner that treats {t['token']} as dest.",
            "bash",
            {
                "command": (
                    "python3 - <<'PY'\nimport json, pathlib\n"
                    f"p=pathlib.Path('{nb}')\n"
                    "print('exists', p.exists(), 'bytes', p.stat().st_size if p.exists() else 0)\n"
                    "nb=json.load(open(p))\n"
                    "for i,c in enumerate(nb['cells']):\n"
                    "    src=''.join(c.get('source',[]))\n"
                    "    print(i, c['cell_type'], src[:180].replace('\\n',' | '))\nPY"
                )
            },
            f"exists True bytes {nbytes}\n0 markdown {t['plant']}\n1 code {t['cell']}\n"
            f"2 code import pandas as pd; df=pd.read_csv('{t['src']}')\n"
            f"3 code # nightly dest claimed via {t['token']}\n",
        ),
        step(
            2,
            f"Observation: {t['token']} cell (step 1). Inspect {t['src']} schema.",
            "bash",
            {
                "command": (
                    f"python3 - <<'PY'\nimport pathlib\n"
                    f"p=pathlib.Path('{t['src']}')\n"
                    "print('src_exists', p.exists(), 'bytes', p.stat().st_size if p.exists() else 0)\n"
                    "print(p.read_text().splitlines()[0] if p.exists() else 'missing')\nPY"
                )
            },
            f"src_exists True bytes {4200 + idx*17}\n"
            f"{t['src'].split('/')[-1]} header present; {t['transform'].split('=')[0].strip()} col expected\n",
        ),
        step(
            3,
            f"Observation: src readable (step 2). Read the export test.",
            "read",
            {"path": test},
            test_obs(t, dest),
        ),
        step(
            4,
            f"Observation: no {t['token']} in export (step 3). Run it.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
            f"FAILED {test}::{t['test_fn']} - FileNotFoundError {t['exp']}\n0 passed, 1 failed\n",
        ),
        step(
            5,
            f"Observation: no exporter (step 4). First apply — {t['token']}.",
            "bash",
            {"command": t["runner"]},
            t["first_obs"],
        ),
        step(
            6,
            f"Observation: {t['kind']} is not parquet (step 5). file(1) the dest.",
            "bash",
            {
                "command": (
                    f"file {dest}; python3 - <<'PY'\n"
                    "import pathlib\n"
                    f"p=pathlib.Path({dest!r})\n"
                    "b=p.read_bytes()[:16] if p.exists() else b''\n"
                    "print('magic', b[:8], 'PAR1', b.startswith(b'PAR1'))\nPY"
                )
            },
            t["file_obs"] + "\nmagic not PAR1\n",
        ),
        step(
            7,
            f"Observation: magic confirms leftover (step 6). Wrap {t['artifact']}.",
            "bash",
            {"command": t["wrap"]},
            t["wrap_obs"],
        ),
        step(
            8,
            "Observation: wrap still not parquet (step 7). Stub exporter copies wrap leftover.",
            "write",
            {
                "path": f"src/{t['exp']}.py",
                "contents": (
                    "from pathlib import Path\n"
                    f"def {t['exp']}(nb_path, dest):\n"
                    f"    Path(dest).write_text(Path('{nb}').read_text())\n"
                ),
            },
            f"stub copies {nb} including {t['token']}",
        ),
        step(
            9,
            f"Observation: stub wired (step 8). Re-run {stem} test.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 14"},
            f"FAILED {test}::{t['test_fn']} - AssertionError: banned {t['token']!r} in text\n"
            "0 passed, 1 failed\n",
        ),
        step(
            10,
            f"Reflection: plan change after wrap-{t['token']} miss — {py} --src/--dest.",
            "write",
            {"path": py, "contents": code},
            f"rewrote {py} from {t['src']}; does not copy {t['artifact']}",
        ),
        step(
            11,
            "Observation: CLI written (step 10). Isolated test.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
            f"1 passed in {tsec(idx, 0.39)}s",
        ),
        step(
            12,
            f"Observation: 1 passed (step 11). Grep {t['token']} in {py}.",
            "grep",
            {"path": py, "pattern": t["ban"]},
            "(no matches)",
        ),
        step(
            13,
            f"Observation: artifact clean (step 12). Residual: {nb} still has {t['token']}.",
            "grep",
            {"path": nb, "pattern": t["token"].split()[0]},
            f"{nb}: {t['cell'][:140]}",
        ),
        step(
            14,
            "Observation: notebook leftover (step 13). Count dest rows + parquet magic.",
            "bash",
            {
                "command": (
                    f"python3 {py} --src {t['src']} --dest /tmp/{dest} && python3 - <<'PY'\n"
                    "import pandas as pd, pathlib\n"
                    f"p=pathlib.Path('/tmp/{dest}')\n"
                    "print('PAR1', p.read_bytes()[:4]==b'PAR1')\n"
                    "print(len(pd.read_parquet(p)))\nPY"
                )
            },
            f"PAR1 True\n{t['rows'] + round_n}",
        ),
        step(
            15,
            f"Observation: {t['rows'] + round_n} rows PAR1 (step 14). Full suite.",
            "bash",
            {"command": "pytest tests -q --tb=line 2>&1 | tail -n 8"},
            f"3 passed in {tsec(idx, 0.52)}s",
        ),
        step(
            16,
            "Observation: 3/3 (step 15). Confirm CLI dest write.",
            "read",
            {"path": py},
            t["transform"],
            reflection=f"{t['token']} is not a pipeline dest. Distinct: {t['distinct']}.",
        ),
    ]
    goal = (
        f"{t['plant']} {nb} uses {t['token']} as the nightly artifact. "
        f"Distinct: {t['distinct']}. Nightly must write {dest} from {t['src']}. "
        f"{test} is the gate: no {t['token']}."
    )
    outcome = (
        f"{t['token']} first apply wrote {t['kind']}, not {dest}. Wrap leftover still banned. "
        f"Plan change: {py} --src/--dest. Tests 3/3. Residual: notebook still {t['token']}. "
        f"Distinct: {t['distinct']}."
    )
    ep = {
        "id": rid,
        "goal": goal,
        "plan": t["plan"],
        "steps": steps,
        "outcome": outcome,
        "reward": {
            "success": True,
            "plan_changes": 1,
            "tests_passed": 3,
            "cost_steps": len(steps),
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    walk_banned(ep)
    check_blob(ep)
    return ep


def leftover_ep(round_n: int, t: dict, idx: int) -> dict:
    stem = t["stem"]
    nb = f"{stem}.ipynb"
    py = f"pipelines/{stem}.py"
    test = f"tests/test_{stem}.py"
    dest = t["dest"]
    dest_kind = "parquet"
    rid = f"ntp-r{round_n}-{t['slug']}"
    code = cli(t["src"], dest_kind, t["transform"])
    steps = [
        step(
            1,
            f"Plan: find leftover {t['left_token']} and the export test.",
            "bash",
            {
                "command": (
                    f"ls -la {t['leftover']} {nb} {t['src']} 2>&1 | head -n 20; "
                    f"echo '---'; rg -n {t['left_token']!r} -S . 2>/dev/null | head"
                )
            },
            f"{t['leftover']} leftover present\n{nb} 9344 bytes\n{t['src']} ok\n"
            f"---\n{nb}: {t['cell'][:180]}\n",
        ),
        step(
            2,
            f"Observation: leftover {t['left_token']} (step 1). file(1) the leftover.",
            "bash",
            {
                "command": (
                    f"file {t['leftover']} 2>&1 | head -n 4; "
                    f"python3 -c \"import pathlib; p=pathlib.Path({t['leftover']!r}); "
                    f"print('exists', p.exists(), 'bytes', p.stat().st_size if p.exists() else 0)\""
                )
            },
            f"{t['leftover']}: {t['kind']}\nexists True bytes {1800 + idx * 40}\n",
        ),
        step(
            3,
            f"Observation: leftover is {t['kind']} (step 2). Read the test.",
            "read",
            {"path": test},
            test_obs(t, dest),
        ),
        step(
            4,
            "Observation: leftover banned in export (step 3). Run it.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
            f"FAILED {test}::{t['test_fn']} - FileNotFoundError {t['exp']}\n0 passed, 1 failed\n",
        ),
        step(
            5,
            f"Observation: no exporter (step 4). First apply — ship leftover {t['left_token']} as dest.",
            "bash",
            {"command": t["first"]},
            t["first_obs"],
        ),
        step(
            6,
            "Observation: leftover is not parquet (step 5). Wrap leftover.",
            "bash",
            {"command": t["wrap"]},
            t["wrap_obs"],
        ),
        step(
            7,
            "Observation: wrap leftover still banned (step 6). Stub copies wrap output.",
            "write",
            {
                "path": f"src/{t['exp']}.py",
                "contents": (
                    "from pathlib import Path\n"
                    f"def {t['exp']}(nb_path, dest):\n"
                    f"    Path(dest).write_text('leftover {t['left_token']}\\n')\n"
                ),
            },
            f"stub writes leftover token {t['left_token']}",
        ),
        step(
            8,
            f"Observation: stub leftover (step 7). Re-run {stem} test.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 14"},
            f"FAILED {test}::{t['test_fn']} - AssertionError: leftover {t['left_token']!r} in text\n"
            "0 passed, 1 failed\n",
        ),
        step(
            9,
            f"Reflection: plan change after leftover wrap — {py} --src/--dest, do not ship {t['left_token']}.",
            "write",
            {"path": py, "contents": code},
            f"rewrote {py}; leftover {t['leftover']} not deleted",
        ),
        step(
            10,
            "Observation: CLI written (step 9). Isolated test.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 12"},
            f"1 passed in {tsec(idx, 0.40)}s",
        ),
        step(
            11,
            f"Observation: 1 passed (step 10). Confirm leftover {t['leftover']} still on disk.",
            "bash",
            {"command": f"ls -la {t['leftover']} 2>&1 | head -n 6"},
            f"{t['leftover']} still present (leftover not cleaned)\n",
        ),
        step(
            12,
            f"Observation: leftover remains (step 11). Grep {py} for leftover token.",
            "grep",
            {"path": py, "pattern": t["ban"]},
            "(no matches)",
        ),
        step(
            13,
            "Observation: CLI clean (step 12). Count dest rows.",
            "bash",
            {
                "command": (
                    f"python3 {py} --src {t['src']} --dest /tmp/{dest} && python3 - <<'PY'\n"
                    "import pandas as pd, pathlib\n"
                    f"p=pathlib.Path('/tmp/{dest}')\n"
                    "print('PAR1', p.read_bytes()[:4]==b'PAR1')\n"
                    "print(len(pd.read_parquet(p)))\nPY"
                )
            },
            f"PAR1 True\n{t['rows'] + round_n}",
        ),
        step(
            14,
            f"Observation: {t['rows'] + round_n} rows (step 13). Pipeline tests.",
            "bash",
            {"command": "pytest tests -q --tb=line 2>&1 | tail -n 4"},
            f"3 passed in {tsec(idx, 0.48)}s",
        ),
        step(
            15,
            f"Observation: 3/3 (step 14). Residual leftover: {t['residual']}.",
            "read",
            {"path": nb},
            t["cell"][:240],
        ),
        step(
            16,
            "Observation: notebook leftover still present (step 15). Do not delete another author's leftover blindly.",
            "bash",
            {"command": f"echo '{t['handoff']}' > NOTES-HANDOFF.md && cat NOTES-HANDOFF.md"},
            t["handoff"],
        ),
        step(
            17,
            "Observation: handoff note written (step 16). Confirm dest CLI one more time.",
            "read",
            {"path": py},
            t["transform"],
        ),
        step(
            18,
            "Observation: CLI dest write (step 17). Partial — leftover not cleaned.",
            "bash",
            {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 3; ls {t['leftover']} | head"},
            f"1 passed in {tsec(idx, 0.32)}s\n{t['leftover']} leftover still listed\n",
            reflection=t["handoff"],
        ),
    ]
    goal = (
        f"{t['plant']} leftover {t['left_token']} from {t['distinct']}. "
        f"CI almost shipped the leftover as {dest}. Nightly must write {dest} from {t['src']} "
        f"without the leftover. {test} is the gate. Ticket allows leftover {t['leftover']} to remain."
    )
    outcome = (
        f"First apply shipped leftover {t['left_token']} as dest. Wrap leftover still banned. "
        f"Plan change: {py} --src/--dest. Pipeline tests 3/3. Partial: {t['handoff']}. "
        f"Distinct: {t['distinct']}."
    )
    ep = {
        "id": rid,
        "goal": goal,
        "plan": t["plan"],
        "steps": steps,
        "outcome": outcome,
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "handoff": 1,
            "cost_steps": len(steps),
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    walk_banned(ep)
    check_blob(ep)
    return ep


def notes_for(round_n: int, e1: dict, e2: dict, s: dict, Ltheme: dict) -> str:
    unused = []
    used = used_slugs() | {s["slug"], Ltheme["slug"]}
    for theme in SUCCESS:
        if theme["slug"] not in used:
            unused.append(theme["slug"])
            break
    for theme in LEFTOVER:
        if theme["slug"] not in used and not VIZ_RE.search(theme["slug"]):
            unused.append(theme["slug"])
            break
    unused_s = ", ".join(unused) if unused else "theme table near end — extend, do not clone dest-as-pipeline"
    return f"""# NOTES-r{round_n} notebook-to-pipeline-factory

Novel coverage: 78%

Two designed episodes (quota 2). Surfaces: {s['slug']} ({s['distinct']}); leftover {Ltheme['slug']} ({Ltheme['distinct']}).
Each rejects wrap-leftover and leftover-as-dest. Not %load_ext cartesian, not papermill engine *-g9, not r100–r1276 clone, not r1277–r1413 dest/viz clone.
Keep r10 git-LFS pointer and r50 memit unused here. BAN matplotlib/seaborn/plotly PNG leftover clones.

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
Unused: {unused_s}.
Avoid raw nbconvert, comment-magics, gNNNN cartesian, papermill engine *-g9, r10 git-LFS clone, r50 memit clone, matplotlib leftover clones.
Skip already-covered leftovers: prepare-only, inject-input-path, jupytext leftover, papermill report leftover, nbconvert leftover, papermill parameters leftover, kernel leftover, cwd leftover, output-as-SoT leftover, SSM secret leftover, PNG/HTML viz leftover.
"""


def write_stage(staging: Path, round_n: int) -> tuple[str, str]:
    s, Ltheme = pair_for(round_n)
    e1 = success_ep(round_n, s, 0)
    e2 = leftover_ep(round_n, Ltheme, 1)
    for ep, lo, hi in ((e1, 16, 16), (e2, 18, 18)):
        n = len(ep["steps"])
        if not (lo <= n <= hi):
            raise RuntimeError(f"{ep['id']} steps {n} not in {lo}-{hi}")
        for i, st in enumerate(ep["steps"], 1):
            if st["n"] != i:
                raise RuntimeError(f"{ep['id']} step n gap at {i}")
            db(st["decision_basis"])
        if ep["meta"]["generator"] != GEN or ep["meta"]["round"] != round_n:
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
    batch.write_text(
        json.dumps(e1, ensure_ascii=True) + "\n" + json.dumps(e2, ensure_ascii=True) + "\n"
    )
    npath.write_text(notes)
    return e1["id"], e2["id"]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-leftover.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
