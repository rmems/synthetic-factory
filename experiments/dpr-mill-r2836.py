#!/usr/bin/env python3
"""data-pipeline-repair mill r2836+ wave4."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

s = importlib.util.spec_from_file_location("dpr2631", "/tmp/dpr_mill_r2631.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
OK, FAIL, build, audit = m.OK, m.FAIL, m.build, m.audit
notes_for, published_identities, guard = m.notes_for, m.published_identities, m.guard
GENERATOR = m.GENERATOR

PAIRS = [
    (
        OK("loki-bloom-filter", "Loki bloom filter vs disable Loki", "lokibloom", "loki.yaml",
           "bloom_gateway", "bloom_gateway.enabled: false", "bloom_gateway.enabled: true",
           "loki.enabled: true", "loki.enabled: false", "Loki", "LB-01", "bloom",
           "Tempo leftover / OTel leftover",
           "Loki pay-logs scanned chunks after bloom_gateway stayed false",
           "scan", 1, "loki"),
        FAIL("tempo-metrics-gen", "Tempo metrics generator vs disable Tempo", "tempomg", "tempo.yaml",
             "metrics_generator", "metrics_generator.processor.service_graphs: false",
             "metrics_generator.processor.service_graphs: true",
             "tempo.enabled: true", "tempo.enabled: false", "Tempo", "TM-01", "generator",
             "Loki leftover / OTel leftover",
             "Tempo pay-traces no RED after service_graphs stayed false",
             "no_red", 1, "tempo", "platform-tempo"),
    ),
    (
        OK("otel-batch-timeout", "OTel batch timeout vs disable exporter", "otelbatch", "otel.yaml",
           "timeout", "timeout: 10s", "timeout: 200ms",
           "otel.enabled: true", "otel.enabled: false", "OTel", "OB-02", "batch",
           "Vector leftover / Fluent Bit leftover",
           "OTel pay-spans lagged after batch timeout stayed 10s",
           "lag_s", 10, "otel"),
        FAIL("vector-reduce", "Vector reduce vs disable Vector", "vectorred", "vector.toml",
             "reduce", "type = \"remap\"", "type = \"reduce\"",
             "vector.enabled = true", "vector.enabled = false", "Vector", "VR-02", "reduce",
             "OTel leftover / Fluent Bit leftover",
             "Vector pay-logs never aggregated after type stayed remap",
             "no_reduce", 1, "vector", "platform-vector"),
    ),
    (
        OK("fluentbit-lua", "Fluent Bit lua filter vs disable Fluent Bit", "fblua", "fluent-bit.conf",
           "lua.script", "Name lua\n    script off.lua", "Name lua\n    script pay.lua",
           "fluentbit.enabled=true", "fluentbit.enabled=false", "Fluent Bit", "FL-03", "lua",
           "Filebeat leftover / Logstash leftover",
           "Fluent Bit pay-logs unfiltered after lua script stayed off.lua",
           "unfiltered", 1, "fluentbit"),
        FAIL("filebeat-autodiscover", "Filebeat autodiscover vs disable Filebeat", "fbauto", "filebeat.yml",
             "autodiscover", "autodiscover: null", "autodiscover.providers: [docker]",
             "filebeat.enabled: true", "filebeat.enabled: false", "Filebeat", "FA-03", "hints",
             "Fluent Bit leftover / Logstash leftover",
             "Filebeat pay-pods missed after autodiscover stayed null",
             "miss_pods", 1, "filebeat", "platform-filebeat"),
    ),
    (
        OK("logstash-dead-letter", "Logstash DLQ vs disable Logstash", "lsdlq", "logstash.yml",
           "dead_letter_queue.enable", "dead_letter_queue.enable: false", "dead_letter_queue.enable: true",
           "logstash.enabled: true", "logstash.enabled: false", "Logstash", "LD-04", "dlq",
           "Prometheus leftover / Alertmanager leftover",
           "Logstash pay-events dropped after DLQ stayed false",
           "drops", 8000, "logstash"),
        FAIL("prom-wal-compress", "Prometheus WAL compress vs disable Prometheus", "promwal", "prometheus.yml",
             "storage.tsdb.wal-compression", "storage.tsdb.wal-compression: false",
             "storage.tsdb.wal-compression: true",
             "prometheus.enabled: true", "prometheus.enabled: false", "Prometheus", "PW-04", "wal",
             "Logstash leftover / Alertmanager leftover",
             "Prometheus pay-wal 4x after wal-compression stayed false",
             "wal_x", 4, "prom", "platform-prometheus"),
    ),
    (
        OK("alertmanager-cluster", "Alertmanager cluster vs disable AM", "amclust", "alertmanager.yml",
           "cluster.listen", "cluster.listen-address: \"\"", "cluster.listen-address: 0.0.0.0:9094",
           "alertmanager.enabled: true", "alertmanager.enabled: false", "Alertmanager", "AC-05", "ha",
           "Thanos leftover / Cortex leftover",
           "Alertmanager pay-pages duplicated after cluster.listen stayed empty",
           "dup_page", 1, "am"),
        FAIL("thanos-query-dedup", "Thanos query dedup vs disable Thanos", "thanosqd", "query.yaml",
             "query.auto-downsampling", "query.auto-downsampling: false", "query.auto-downsampling: true",
             "thanos.enabled: true", "thanos.enabled: false", "Thanos", "TQ-05", "dedup",
             "Alertmanager leftover / Cortex leftover",
             "Thanos pay-query mixed resolutions after auto-downsampling stayed false",
             "mix_res", 1, "thanos", "platform-thanos"),
    ),
    (
        OK("flink-sql-gateway", "Flink SQL gateway vs disable gateway", "flinkgw", "flink-conf.yaml",
           "sql-gateway", "sql-gateway.endpoint.rest.enabled: false",
           "sql-gateway.endpoint.rest.enabled: true",
           "flink.enabled: true", "flink.enabled: false", "Flink", "FG-06", "gateway",
           "Spark leftover / Beam leftover",
           "Flink pay-sql no REST after sql-gateway stayed false",
           "no_rest", 1, "flink"),
        FAIL("beam-portable", "Beam portable runner vs disable Beam", "beamport", "pipeline.py",
             "portable", "runner='DirectRunner'", "runner='PortableRunner'",
             "beam.enabled=True", "beam.enabled=False", "Beam", "BP-06", "portable",
             "Flink leftover / Spark leftover",
             "Beam pay-etl local after runner stayed DirectRunner",
             "local", 1, "beam", "platform-beam"),
    ),
    (
        OK("nifi-python-ext", "NiFi Python extensions vs disable Python", "nifipy", "nifi.properties",
           "python.extensions", "nifi.python.command=", "nifi.python.command=/usr/bin/python3",
           "nifi.enabled=true", "nifi.enabled=false", "NiFi", "NP-07", "python",
           "Airflow leftover / Dagster leftover",
           "NiFi pay-proc missing Python after nifi.python.command stayed empty",
           "no_py", 1, "nifi"),
        FAIL("airflow-k8s-executor", "Airflow KubernetesExecutor vs disable k8s", "airflowk8", "airflow.cfg",
             "executor", "executor = LocalExecutor", "executor = KubernetesExecutor",
             "airflow.enabled=true", "airflow.enabled=false", "Airflow", "AK-07", "k8s",
             "NiFi leftover / Dagster leftover",
             "Airflow pay-dags serial after executor stayed LocalExecutor",
             "serial", 1, "airflow", "platform-airflow"),
    ),
    (
        OK("dagster-code-loc", "Dagster code location vs disable Dagster", "dagstercl", "workspace.yaml",
           "code_location", "load_from: []", "load_from: [{python_file: pay.py}]",
           "dagster.enabled: true", "dagster.enabled: false", "Dagster", "DC-08", "location",
           "Prefect leftover / Mage leftover",
           "Dagster pay-assets missing after load_from stayed []",
           "no_loc", 1, "dagster"),
        FAIL("mage-spark", "Mage Spark executor vs disable Mage", "magespark", "metadata.yaml",
             "executor_type", "executor_type: local_python", "executor_type: pyspark",
             "mage.enabled: true", "mage.enabled: false", "Mage", "MS-08", "spark",
             "Dagster leftover / Prefect leftover",
             "Mage pay-etl local after executor_type stayed local_python",
             "local", 1, "mage", "platform-mage"),
    ),
    (
        OK("kestra-plugin-def", "Kestra plugin defaults vs disable Kestra", "kestrapd", "kestra.yml",
           "pluginDefaults", "pluginDefaults: []", "pluginDefaults: [{type: io.kestra.plugin.scripts}]",
           "kestra.enabled: true", "kestra.enabled: false", "Kestra", "KP-09", "plugin",
           "Luigi leftover / Argo leftover",
           "Kestra pay-scripts missing after pluginDefaults stayed []",
           "no_plug", 1, "kestra"),
        FAIL("luigi-contrib", "Luigi contrib vs disable Luigi", "luigic", "luigi.cfg",
             "contrib", "[core]\nmodule=", "[core]\nmodule=luigi.contrib.spark",
             "luigi.enabled=true", "luigi.enabled=false", "Luigi", "LC-09", "contrib",
             "Kestra leftover / Argo leftover",
             "Luigi pay-spark missing after module stayed empty",
             "no_mod", 1, "luigi", "platform-luigi"),
    ),
    (
        OK("argo-artifact-gc", "Argo artifact GC vs disable Argo", "argoagc", "workflow.yaml",
           "artifactGC", "artifactGC: {}", "artifactGC: {strategy: OnWorkflowCompletion}",
           "argo.enabled: true", "argo.enabled: false", "Argo", "AG-10", "gc",
           "Tekton leftover / Flyte leftover",
           "Argo pay-art filled S3 after artifactGC stayed {}",
           "s3_fill", 1, "argo"),
        FAIL("tekton-result", "Tekton Results vs disable Results", "tekres", "config.yaml",
             "results.api", "results.api-server=", "results.api-server=http://tekton-results",
             "tekton.enabled: true", "tekton.enabled: false", "Tekton", "TR-10", "results",
             "Argo leftover / Flyte leftover",
             "Tekton pay-runs lost history after results.api-server stayed empty",
             "no_hist", 1, "tekton", "platform-tekton"),
    ),
    (
        OK("flyte-array", "Flyte map task vs disable Flyte", "flytearr", "task.yaml",
           "array", "concurrency=1", "concurrency=64",
           "flyte.enabled: true", "flyte.enabled: false", "Flyte", "FA-11", "map",
           "Kubeflow leftover / MLflow leftover",
           "Flyte pay-map serial after concurrency stayed 1",
           "serial", 1, "flyte"),
        FAIL("kubeflow-katib", "Kubeflow Katib vs disable Katib", "katib", "experiment.yaml",
             "parallelTrialCount", "parallelTrialCount: 1", "parallelTrialCount: 8",
             "katib.enabled: true", "katib.enabled: false", "Katib", "KK-11", "trial",
             "Flyte leftover / MLflow leftover",
             "Katib pay-hpo serial after parallelTrialCount stayed 1",
             "serial", 1, "katib", "platform-kubeflow"),
    ),
    (
        OK("mlflow-registry", "MLflow model registry vs disable MLflow", "mlflowreg", "mlflow.ini",
           "registry_uri", "registry_uri=", "registry_uri=mysql://pay",
           "mlflow.enabled=true", "mlflow.enabled=false", "MLflow", "MR-12", "registry",
           "Feast leftover / Tecton leftover",
           "MLflow pay-models unregistered after registry_uri stayed empty",
           "no_reg", 1, "mlflow"),
        FAIL("feast-stream-src", "Feast stream source vs disable Feast", "feastss", "feature_store.yaml",
             "stream_source", "stream_source: null", "stream_source: kafka",
             "feast.enabled: true", "feast.enabled: false", "Feast", "FS-12", "stream",
             "MLflow leftover / Tecton leftover",
             "Feast pay-features batch-only after stream_source stayed null",
             "batch_only", 1, "feast", "platform-feast"),
    ),
    (
        OK("clickhouse-s3queue-keeper", "ClickHouse S3Queue keeper vs disable S3Queue", "chs3k", "pay.sql",
           "s3queue_keeper_path", "s3queue_keeper_path=''", "s3queue_keeper_path='/clickhouse/s3queue/pay'",
           "ENGINE = S3Queue", "ENGINE = File", "S3Queue", "CSK-13", "keeper",
           "Druid leftover / Pinot leftover",
           "ClickHouse pay-ingest duplicated after s3queue_keeper_path stayed empty",
           "dups", 1, "ch"),
        FAIL("druid-middlemanager", "Druid MiddleManager capacity vs disable MM", "druidmm", "runtime.properties",
             "worker.capacity", "druid.worker.capacity=1", "druid.worker.capacity=16",
             "druid.enabled=true", "druid.enabled=false", "Druid", "DM-13", "mm",
             "ClickHouse leftover / Pinot leftover",
             "Druid pay-tasks queued after worker.capacity stayed 1",
             "queued", 1, "druid", "platform-druid"),
    ),
    (
        OK("pinot-helix-cluster", "Pinot Helix cluster vs disable Pinot", "pinothel", "controller.conf",
           "controller.helix", "controller.helix.cluster.name=default",
           "controller.helix.cluster.name=pay",
           "pinot.enabled=true", "pinot.enabled=false", "Pinot", "PH-14", "helix",
           "StarRocks leftover / Doris leftover",
           "Pinot pay-tables mixed clusters after helix name stayed default",
           "mix", 1, "pinot"),
        FAIL("starrocks-fe-journal", "StarRocks FE journal vs disable FE", "srfe", "fe.conf",
             "edit_log_type", "edit_log_type = local", "edit_log_type = bdbje",
             "starrocks.enabled=true", "starrocks.enabled=false", "StarRocks", "SF-14", "journal",
             "Pinot leftover / Doris leftover",
             "StarRocks pay-fe no HA after edit_log_type stayed local",
             "no_ha", 1, "starrocks", "platform-starrocks"),
    ),
    (
        OK("doris-fe-bdbje", "Doris FE BDBJE vs disable FE", "dorisfeb", "fe.conf",
           "edit_log_type", "edit_log_type = local", "edit_log_type = bdbje",
           "doris.enabled=true", "doris.enabled=false", "Doris", "DF-15", "bdbje",
           "RisingWave leftover / Materialize leftover",
           "Doris pay-fe no HA after edit_log_type stayed local",
           "no_ha", 1, "doris"),
        FAIL("risingwave-meta-store", "RisingWave meta store vs disable RW", "rwmeta", "rw.toml",
             "meta.backend", "meta.backend='memory'", "meta.backend='etcd'",
             "risingwave.enabled=true", "risingwave.enabled=false", "RisingWave", "RM-15", "meta",
             "Doris leftover / Materialize leftover",
             "RisingWave pay-cluster lost meta after backend stayed memory",
             "lost_meta", 1, "rw", "platform-risingwave"),
    ),
]


def plants_for(round_number: int):
    used = published_identities()
    for a, b in PAIRS:
        keys = {a["slug"].lower(), b["slug"].lower(), a["domain"].lower(), b["domain"].lower()}
        if keys & used:
            continue
        try:
            guard(a)
            guard(b)
        except SystemExit:
            continue
        return (lambda r, s=a: build(r, s), lambda r, s=b: build(r, s))
    raise SystemExit(f"no unused plants r{round_number} bank={len(PAIRS)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", type=Path, required=True)
    args = ap.parse_args()
    recs = [fn(args.round) for fn in plants_for(args.round)]
    if len(recs) != 2 or recs[0]["reward"]["success"] == recs[1]["reward"]["success"]:
        raise SystemExit("need success + handoff pair")
    for rec in recs:
        audit(rec)
        if rec["meta"]["generator"] != GENERATOR or rec["meta"]["round"] != args.round:
            raise SystemExit("bad meta")
        blob = json.dumps(rec)
        if "[variant" in rec["goal"].lower() or '"sim_or_real": "real"' in blob:
            raise SystemExit("banned stamp")
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"banned {bad}")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))


if __name__ == "__main__":
    sys.exit(main() or 0)
