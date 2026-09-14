#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 29: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "spark-eventlog-leftover-as-dest", "spel", "spark eventlog leftover", "spark-events", "spark eventlog leftover", "spark leftover && ls spark-events", "not spark-eventlog leftover; spark eventlog leftover is not dest", "treat leftover spark eventlog as dest then CLI parquet.", "spark leftover; # spark-events claimed dest", "spark leftover|spark-events"),
    s_from(1, "ray-checkpoint-leftover-as-dest", "ryck", "ray checkpoint leftover", "ray/chk", "ray checkpoint leftover", "ray leftover && ls ray/chk", "not ray-checkpoint leftover; ray checkpoint leftover is not dest", "treat leftover ray checkpoint as dest then CLI parquet.", "ray leftover; # ray/chk claimed dest", "ray leftover|ray/chk"),
    s_from(2, "beam-job-leftover-as-dest", "bmjb", "beam job leftover", "beam/job.json", "beam job leftover", "beam leftover && ls beam/job.json", "not beam-job leftover; beam job leftover is not dest", "treat leftover beam job as dest then CLI parquet.", "beam leftover; # beam/job.json claimed dest", "beam leftover|beam/job.json"),
    s_from(3, "storm-topo-leftover-as-dest", "sttp", "storm topo leftover", "storm/topology.json", "storm topo leftover", "storm leftover && ls storm/topology.json", "not storm-topo leftover; storm topo leftover is not dest", "treat leftover storm topo as dest then CLI parquet.", "storm leftover; # storm/topology.json claimed dest", "storm leftover|storm/topology.json"),
    s_from(4, "heron-topo-leftover-as-dest", "hrtp", "heron topo leftover", "heron/topology.json", "heron topo leftover", "heron leftover && ls heron/topology.json", "not heron-topo leftover; heron topo leftover is not dest", "treat leftover heron topo as dest then CLI parquet.", "heron leftover; # heron/topology.json claimed dest", "heron leftover|heron/topology.json"),
    s_from(5, "samza-chk-leftover-as-dest", "szck", "samza chk leftover", "samza/chk", "samza chk leftover", "samza leftover && ls samza/chk", "not samza-chk leftover; samza chk leftover is not dest", "treat leftover samza chk as dest then CLI parquet.", "samza leftover; # samza/chk claimed dest", "samza leftover|samza/chk"),
    s_from(6, "nifi-flow-leftover-as-dest", "nffl", "nifi flow leftover", "nifi/flow.json.gz", "nifi flow leftover", "nifi leftover && ls nifi/flow.json.gz", "not nifi-flow leftover; nifi flow leftover is not dest", "treat leftover nifi flow as dest then CLI parquet.", "nifi leftover; # nifi/flow.json.gz claimed dest", "nifi leftover|nifi/flow.json.gz"),
    s_from(7, "airbyte-state-leftover-as-dest", "abst", "airbyte state leftover", "airbyte/state.json", "airbyte state leftover", "airbyte leftover && ls airbyte/state.json", "not airbyte-state leftover; airbyte state leftover is not dest", "treat leftover airbyte state as dest then CLI parquet.", "airbyte leftover; # airbyte/state.json claimed dest", "airbyte leftover|airbyte/state.json"),
    s_from(8, "fivetran-sync-leftover-as-dest", "ftsy", "fivetran sync leftover", "fivetran/sync.json", "fivetran sync leftover", "fivetran leftover && ls fivetran/sync.json", "not fivetran-sync leftover; fivetran sync leftover is not dest", "treat leftover fivetran sync as dest then CLI parquet.", "fivetran leftover; # fivetran/sync.json claimed dest", "fivetran leftover|fivetran/sync.json"),
    s_from(9, "stitch-state-leftover-as-dest", "stst", "stitch state leftover", "stitch/state.json", "stitch state leftover", "stitch leftover && ls stitch/state.json", "not stitch-state leftover; stitch state leftover is not dest", "treat leftover stitch state as dest then CLI parquet.", "stitch leftover; # stitch/state.json claimed dest", "stitch leftover|stitch/state.json"),
    s_from(10, "singer-state-leftover-as-dest", "sgst", "singer state leftover", "singer/state.json", "singer state leftover", "singer leftover && ls singer/state.json", "not singer-state leftover; singer state leftover is not dest", "treat leftover singer state as dest then CLI parquet.", "singer leftover; # singer/state.json claimed dest", "singer leftover|singer/state.json"),
    s_from(11, "meltano-state-leftover-as-dest", "mlst", "meltano state leftover", ".meltano/run", "meltano state leftover", "meltano leftover && ls .meltano/run", "not meltano-state leftover; meltano state leftover is not dest", "treat leftover meltano state as dest then CLI parquet.", "meltano leftover; # .meltano/run claimed dest", "meltano leftover|.meltano/run"),
    s_from(12, "dbt-target-leftover-as-dest", "dbtg", "dbt target leftover", "target/manifest.json", "dbt target leftover", "dbt leftover && ls target/manifest.json", "not dbt-target leftover; dbt target leftover is not dest", "treat leftover dbt target as dest then CLI parquet.", "dbt leftover; # target/manifest.json claimed dest", "dbt leftover|target/manifest.json"),
    s_from(13, "sqlmesh-state-leftover-as-dest", "sms", "sqlmesh state leftover", ".sqlmesh", "sqlmesh state leftover", "sqlmesh leftover && ls .sqlmesh", "not sqlmesh-state leftover; sqlmesh state leftover is not dest", "treat leftover sqlmesh state as dest then CLI parquet.", "sqlmesh leftover; # .sqlmesh claimed dest", "sqlmesh leftover|.sqlmesh"),
    s_from(14, "dagster-runs-leftover-as-dest", "dgrn", "dagster runs leftover", "dagster/runs", "dagster runs leftover", "dagster leftover && ls dagster/runs", "not dagster-runs leftover; dagster runs leftover is not dest", "treat leftover dagster runs as dest then CLI parquet.", "dagster leftover; # dagster/runs claimed dest", "dagster leftover|dagster/runs"),
    s_from(15, "mage-pipeline-leftover-as-dest", "mgpl", "mage pipeline leftover", ".mage/pipeline.yaml", "mage pipeline leftover", "mage leftover && ls .mage/pipeline.yaml", "not mage-pipeline leftover; mage pipeline leftover is not dest", "treat leftover mage pipeline as dest then CLI parquet.", "mage leftover; # .mage/pipeline.yaml claimed dest", "mage leftover|.mage/pipeline.yaml"),
    s_from(16, "temporal-workflow-leftover-as-dest", "tmwf", "temporal workflow leftover", "temporal/workflow.json", "temporal workflow leftover", "temporal leftover && ls temporal/workflow.json", "not temporal-workflow leftover; temporal workflow leftover is not dest", "treat leftover temporal workflow as dest then CLI parquet.", "temporal leftover; # temporal/workflow.json claimed dest", "temporal leftover|temporal/workflow.json"),
    s_from(17, "cadence-workflow-leftover-as-dest", "cdwf", "cadence workflow leftover", "cadence/workflow.json", "cadence workflow leftover", "cadence leftover && ls cadence/workflow.json", "not cadence-workflow leftover; cadence workflow leftover is not dest", "treat leftover cadence workflow as dest then CLI parquet.", "cadence leftover; # cadence/workflow.json claimed dest", "cadence leftover|cadence/workflow.json"),
    s_from(18, "kedro-session-leftover-as-dest", "kdsn", "kedro session leftover", "kedro/session.json", "kedro session leftover", "kedro leftover && ls kedro/session.json", "not kedro-session leftover; kedro session leftover is not dest", "treat leftover kedro session as dest then CLI parquet.", "kedro leftover; # kedro/session.json claimed dest", "kedro leftover|kedro/session.json"),
    s_from(19, "metaflow-datastore-leftover-as-dest", "mfds", "metaflow datastore leftover", ".metaflow", "metaflow datastore leftover", "metaflow leftover && ls .metaflow", "not metaflow-datastore leftover; metaflow datastore leftover is not dest", "treat leftover metaflow datastore as dest then CLI parquet.", "metaflow leftover; # .metaflow claimed dest", "metaflow leftover|.metaflow"),
    s_from(20, "zenml-store-leftover-as-dest", "zmst", "zenml store leftover", ".zenml", "zenml store leftover", "zenml leftover && ls .zenml", "not zenml-store leftover; zenml store leftover is not dest", "treat leftover zenml store as dest then CLI parquet.", "zenml leftover; # .zenml claimed dest", "zenml leftover|.zenml"),
    s_from(21, "vertex-experiment-leftover-as-dest", "vtex", "vertex experiment leftover", ".vertex/experiment.json", "vertex experiment leftover", "vertex leftover && ls .vertex/experiment.json", "not vertex-experiment leftover; vertex experiment leftover is not dest", "treat leftover vertex experiment as dest then CLI parquet.", "vertex leftover; # .vertex/experiment.json claimed dest", "vertex leftover|.vertex/experiment.json"),
    s_from(22, "tensorboard-events-leftover-as-dest", "tbev", "tensorboard events leftover", "events.out.tfevents", "tensorboard events leftover", "tensorboard leftover && ls events.out.tfevents", "not tensorboard-events leftover; tensorboard events leftover is not dest", "treat leftover tensorboard events as dest then CLI parquet.", "tensorboard leftover; # events.out.tfevents claimed dest", "tensorboard leftover|events.out.tfevents"),
    s_from(23, "clearml-cache-leftover-as-dest", "clch2", "clearml cache leftover", ".clearml/cache", "clearml cache leftover", "clearml leftover && ls .clearml/cache", "not clearml-cache leftover; clearml cache leftover is not dest", "treat leftover clearml cache as dest then CLI parquet.", "clearml leftover; # .clearml/cache claimed dest", "clearml leftover|.clearml/cache"),
    s_from(24, "neptune-run-leftover-as-dest", "nprn", "neptune run leftover", ".neptune", "neptune run leftover", "neptune leftover && ls .neptune", "not neptune-run leftover; neptune run leftover is not dest", "treat leftover neptune run as dest then CLI parquet.", "neptune leftover; # .neptune claimed dest", "neptune leftover|.neptune"),
    s_from(25, "comet-cache-leftover-as-dest", "cmch", "comet cache leftover", ".cometml", "comet cache leftover", "comet leftover && ls .cometml", "not comet-cache leftover; comet cache leftover is not dest", "treat leftover comet cache as dest then CLI parquet.", "comet leftover; # .cometml claimed dest", "comet leftover|.cometml"),
    s_from(26, "dvc-cache-leftover-as-dest", "dvch", "dvc cache leftover", ".dvc/cache", "dvc cache leftover", "dvc leftover && ls .dvc/cache", "not dvc-cache leftover; dvc cache leftover is not dest", "treat leftover dvc cache as dest then CLI parquet.", "dvc leftover; # .dvc/cache claimed dest", "dvc leftover|.dvc/cache"),
    s_from(27, "lakefs-data-leftover-as-dest", "lfdt", "lakefs data leftover", "lakefs/data", "lakefs data leftover", "lakefs leftover && ls lakefs/data", "not lakefs-data leftover; lakefs data leftover is not dest", "treat leftover lakefs data as dest then CLI parquet.", "lakefs leftover; # lakefs/data claimed dest", "lakefs leftover|lakefs/data"),
    s_from(28, "delta-log-leftover-as-dest", "dtlg", "delta log leftover", "_delta_log", "delta log leftover", "delta leftover && ls _delta_log", "not delta-log leftover; delta log leftover is not dest", "treat leftover delta log as dest then CLI parquet.", "delta leftover; # _delta_log claimed dest", "delta leftover|_delta_log"),
    s_from(29, "iceberg-meta-leftover-as-dest", "icmt", "iceberg meta leftover", "metadata/v1.metadata.json", "iceberg meta leftover", "iceberg leftover && ls metadata/v1.metadata.json", "not iceberg-meta leftover; iceberg meta leftover is not dest", "treat leftover iceberg meta as dest then CLI parquet.", "iceberg leftover; # metadata/v1.metadata.json claimed dest", "iceberg leftover|metadata/v1.metadata.json"),
    s_from(30, "hudi-meta-leftover-as-dest", "hdmt", "hudi meta leftover", ".hoodie", "hudi meta leftover", "hudi leftover && ls .hoodie", "not hudi-meta leftover; hudi meta leftover is not dest", "treat leftover hudi meta as dest then CLI parquet.", "hudi leftover; # .hoodie claimed dest", "hudi leftover|.hoodie"),
    s_from(31, "lance-versions-leftover-as-dest", "lnvr", "lance versions leftover", "_versions", "lance versions leftover", "lance leftover && ls _versions", "not lance-versions leftover; lance versions leftover is not dest", "treat leftover lance versions as dest then CLI parquet.", "lance leftover; # _versions claimed dest", "lance leftover|_versions"),
]

LEFTOVER = [
    l_from(0, "spark-warehouse-leftover-handoff", "spwh", "spark-warehouse", "spark warehouse leftover", "spark warehouse leftover", "not spark eventlog leftover; leftover spark warehouse as dest", "ship leftover spark warehouse as dest.", "spark warehouse leftover; # spark-warehouse on disk", "spark leftover|spark-warehouse"),
    l_from(1, "ray-log-leftover-handoff", "rylg", "ray.log", "ray log leftover", "ray log leftover", "not ray checkpoint leftover; leftover ray log as dest", "ship leftover ray log as dest.", "ray log leftover; # ray.log on disk", "ray leftover|ray.log"),
    l_from(2, "beam-metrics-leftover-handoff", "bmmt", "beam/metrics.json", "beam metrics leftover", "beam metrics leftover", "not beam job leftover; leftover beam metrics as dest", "ship leftover beam metrics as dest.", "beam metrics leftover; # beam/metrics.json on disk", "beam leftover|beam/metrics.json"),
    l_from(3, "storm-log-leftover-handoff", "stlg4", "storm.log", "storm log leftover", "storm log leftover", "not storm topo leftover; leftover storm log as dest", "ship leftover storm log as dest.", "storm log leftover; # storm.log on disk", "storm leftover|storm.log"),
    l_from(4, "heron-log-leftover-handoff", "hrlg", "heron.log", "heron log leftover", "heron log leftover", "not heron topo leftover; leftover heron log as dest", "ship leftover heron log as dest.", "heron log leftover; # heron.log on disk", "heron leftover|heron.log"),
    l_from(5, "samza-log-leftover-handoff", "szlg", "samza.log", "samza log leftover", "samza log leftover", "not samza chk leftover; leftover samza log as dest", "ship leftover samza log as dest.", "samza log leftover; # samza.log on disk", "samza leftover|samza.log"),
    l_from(6, "nifi-conf-leftover-handoff", "nfcf", "nifi.properties.bak", "nifi conf leftover", "nifi conf leftover", "not nifi flow leftover; leftover nifi conf as dest", "ship leftover nifi conf as dest.", "nifi conf leftover; # nifi.properties.bak on disk", "nifi leftover|nifi.properties.bak"),
    l_from(7, "airbyte-log-leftover-handoff", "ablg", "airbyte.log", "airbyte log leftover", "airbyte log leftover", "not airbyte state leftover; leftover airbyte log as dest", "ship leftover airbyte log as dest.", "airbyte log leftover; # airbyte.log on disk", "airbyte leftover|airbyte.log"),
    l_from(8, "fivetran-log-leftover-handoff", "ftlg", "fivetran.log", "fivetran log leftover", "fivetran log leftover", "not fivetran sync leftover; leftover fivetran log as dest", "ship leftover fivetran log as dest.", "fivetran log leftover; # fivetran.log on disk", "fivetran leftover|fivetran.log"),
    l_from(9, "stitch-log-leftover-handoff", "stlg5", "stitch.log", "stitch log leftover", "stitch log leftover", "not stitch state leftover; leftover stitch log as dest", "ship leftover stitch log as dest.", "stitch log leftover; # stitch.log on disk", "stitch leftover|stitch.log"),
    l_from(10, "singer-log-leftover-handoff", "sglg3", "singer.log", "singer log leftover", "singer log leftover", "not singer state leftover; leftover singer log as dest", "ship leftover singer log as dest.", "singer log leftover; # singer.log on disk", "singer leftover|singer.log"),
    l_from(11, "meltano-log-leftover-handoff", "mllg2", "meltano.log", "meltano log leftover", "meltano log leftover", "not meltano state leftover; leftover meltano log as dest", "ship leftover meltano log as dest.", "meltano log leftover; # meltano.log on disk", "meltano leftover|meltano.log"),
    l_from(12, "dbt-catalog-leftover-handoff", "dbct", "target/catalog.json", "dbt catalog leftover", "dbt catalog leftover", "not dbt target leftover; leftover dbt catalog as dest", "ship leftover dbt catalog as dest.", "dbt catalog leftover; # target/catalog.json on disk", "dbt leftover|target/catalog.json"),
    l_from(13, "sqlmesh-log-leftover-handoff", "smlg", "sqlmesh.log", "sqlmesh log leftover", "sqlmesh log leftover", "not sqlmesh state leftover; leftover sqlmesh log as dest", "ship leftover sqlmesh log as dest.", "sqlmesh log leftover; # sqlmesh.log on disk", "sqlmesh leftover|sqlmesh.log"),
    l_from(14, "dagster-log-leftover-handoff", "dglg", "dagster.log", "dagster log leftover", "dagster log leftover", "not dagster runs leftover; leftover dagster log as dest", "ship leftover dagster log as dest.", "dagster log leftover; # dagster.log on disk", "dagster leftover|dagster.log"),
    l_from(15, "mage-log-leftover-handoff", "mglg", "mage.log", "mage log leftover", "mage log leftover", "not mage pipeline leftover; leftover mage log as dest", "ship leftover mage log as dest.", "mage log leftover; # mage.log on disk", "mage leftover|mage.log"),
    l_from(16, "temporal-log-leftover-handoff", "tmlg", "temporal.log", "temporal log leftover", "temporal log leftover", "not temporal workflow leftover; leftover temporal log as dest", "ship leftover temporal log as dest.", "temporal log leftover; # temporal.log on disk", "temporal leftover|temporal.log"),
    l_from(17, "cadence-log-leftover-handoff", "cdlg3", "cadence.log", "cadence log leftover", "cadence log leftover", "not cadence workflow leftover; leftover cadence log as dest", "ship leftover cadence log as dest.", "cadence log leftover; # cadence.log on disk", "cadence leftover|cadence.log"),
    l_from(18, "kedro-log-leftover-handoff", "kdlg2", "kedro.log", "kedro log leftover", "kedro log leftover", "not kedro session leftover; leftover kedro log as dest", "ship leftover kedro log as dest.", "kedro log leftover; # kedro.log on disk", "kedro leftover|kedro.log"),
    l_from(19, "metaflow-log-leftover-handoff", "mflg", "metaflow.log", "metaflow log leftover", "metaflow log leftover", "not metaflow datastore leftover; leftover metaflow log as dest", "ship leftover metaflow log as dest.", "metaflow log leftover; # metaflow.log on disk", "metaflow leftover|metaflow.log"),
    l_from(20, "zenml-log-leftover-handoff", "zmlg", "zenml.log", "zenml log leftover", "zenml log leftover", "not zenml store leftover; leftover zenml log as dest", "ship leftover zenml log as dest.", "zenml log leftover; # zenml.log on disk", "zenml leftover|zenml.log"),
    l_from(21, "vertex-log-leftover-handoff", "vtlg2", "vertex.log", "vertex log leftover", "vertex log leftover", "not vertex experiment leftover; leftover vertex log as dest", "ship leftover vertex log as dest.", "vertex log leftover; # vertex.log on disk", "vertex leftover|vertex.log"),
    l_from(22, "tensorboard-log-leftover-handoff", "tblg", "tensorboard.log", "tensorboard log leftover", "tensorboard log leftover", "not tensorboard events leftover; leftover tensorboard log as dest", "ship leftover tensorboard log as dest.", "tensorboard log leftover; # tensorboard.log on disk", "tensorboard leftover|tensorboard.log"),
    l_from(23, "clearml-log-leftover-handoff", "cllg3", "clearml.log", "clearml log leftover", "clearml log leftover", "not clearml cache leftover; leftover clearml log as dest", "ship leftover clearml log as dest.", "clearml log leftover; # clearml.log on disk", "clearml leftover|clearml.log"),
    l_from(24, "neptune-log-leftover-handoff", "nplg", "neptune.log", "neptune log leftover", "neptune log leftover", "not neptune run leftover; leftover neptune log as dest", "ship leftover neptune log as dest.", "neptune log leftover; # neptune.log on disk", "neptune leftover|neptune.log"),
    l_from(25, "comet-log-leftover-handoff", "cmlg2", "comet.log", "comet log leftover", "comet log leftover", "not comet cache leftover; leftover comet log as dest", "ship leftover comet log as dest.", "comet log leftover; # comet.log on disk", "comet leftover|comet.log"),
    l_from(26, "dvc-tmp-leftover-handoff", "dvtm", ".dvc/tmp", "dvc tmp leftover", "dvc tmp leftover", "not dvc cache leftover; leftover dvc tmp as dest", "ship leftover dvc tmp as dest.", "dvc tmp leftover; # .dvc/tmp on disk", "dvc leftover|.dvc/tmp"),
    l_from(27, "lakefs-log-leftover-handoff", "lflg", "lakefs.log", "lakefs log leftover", "lakefs log leftover", "not lakefs data leftover; leftover lakefs log as dest", "ship leftover lakefs log as dest.", "lakefs log leftover; # lakefs.log on disk", "lakefs leftover|lakefs.log"),
    l_from(28, "delta-chk-leftover-handoff", "dtck", "_delta_log/_last_checkpoint", "delta chk leftover", "delta chk leftover", "not delta log leftover; leftover delta chk as dest", "ship leftover delta chk as dest.", "delta chk leftover; # _delta_log/_last_checkpoint on disk", "delta leftover|_delta_log/_last_checkpoint"),
    l_from(29, "iceberg-snap-leftover-handoff", "icsn", "metadata/snap-1.avro", "iceberg snap leftover", "iceberg snap leftover", "not iceberg meta leftover; leftover iceberg snap as dest", "ship leftover iceberg snap as dest.", "iceberg snap leftover; # metadata/snap-1.avro on disk", "iceberg leftover|metadata/snap-1.avro"),
    l_from(30, "hudi-timeline-leftover-handoff", "hdtl", ".hoodie/timeline", "hudi timeline leftover", "hudi timeline leftover", "not hudi meta leftover; leftover hudi timeline as dest", "ship leftover hudi timeline as dest.", "hudi timeline leftover; # .hoodie/timeline on disk", "hudi leftover|.hoodie/timeline"),
    l_from(31, "lance-manifest-leftover-handoff", "lnmf", "_versions/1.manifest", "lance manifest leftover", "lance manifest leftover", "not lance versions leftover; leftover lance manifest as dest", "ship leftover lance manifest as dest.", "lance manifest leftover; # _versions/1.manifest on disk", "lance leftover|_versions/1.manifest"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll29.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
