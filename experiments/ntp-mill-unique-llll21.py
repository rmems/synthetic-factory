#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 21: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "kafka-logdir-leftover-as-dest", "kflg", "kafka logdir leftover", "kafka-logs", "kafka logdir leftover", "kafka leftover && ls kafka-logs", "not kafka-logdir leftover; kafka logdir leftover is not dest", "treat leftover kafka logdir as dest then CLI parquet.", "kafka leftover; # kafka-logs claimed dest", "kafka leftover|kafka-logs"),
    s_from(1, "rabbitmq-mnesia-leftover-as-dest", "rbmn", "rabbitmq mnesia leftover", "mnesia", "rabbitmq mnesia leftover", "rabbitmq leftover && ls mnesia", "not rabbitmq-mnesia leftover; rabbitmq mnesia leftover is not dest", "treat leftover rabbitmq mnesia as dest then CLI parquet.", "rabbitmq leftover; # mnesia claimed dest", "rabbitmq leftover|mnesia"),
    s_from(2, "mosquitto-store-leftover-as-dest", "mqst", "mosquitto store leftover", "mosquitto/store", "mosquitto store leftover", "mosquitto leftover && ls mosquitto/store", "not mosquitto-store leftover; mosquitto store leftover is not dest", "treat leftover mosquitto store as dest then CLI parquet.", "mosquitto leftover; # mosquitto/store claimed dest", "mosquitto leftover|mosquitto/store"),
    s_from(3, "nats-jetstream-leftover-as-dest", "ntjs", "nats jetstream leftover", "jetstream", "nats jetstream leftover", "nats leftover && ls jetstream", "not nats-jetstream leftover; nats jetstream leftover is not dest", "treat leftover nats jetstream as dest then CLI parquet.", "nats leftover; # jetstream claimed dest", "nats leftover|jetstream"),
    s_from(4, "pulsar-journal-leftover-as-dest", "psjn", "pulsar journal leftover", "pulsar/journal", "pulsar journal leftover", "pulsar leftover && ls pulsar/journal", "not pulsar-journal leftover; pulsar journal leftover is not dest", "treat leftover pulsar journal as dest then CLI parquet.", "pulsar leftover; # pulsar/journal claimed dest", "pulsar leftover|pulsar/journal"),
    s_from(5, "redis-stream-leftover-as-dest", "rdst", "redis stream leftover", "stream.rdb", "redis stream leftover", "redis leftover && ls stream.rdb", "not redis-stream leftover; redis stream leftover is not dest", "treat leftover redis stream as dest then CLI parquet.", "redis leftover; # stream.rdb claimed dest", "redis leftover|stream.rdb"),
    s_from(6, "sqs-local-leftover-as-dest", "sqsl", "sqs local leftover", "elasticmq.conf", "sqs local leftover", "sqs leftover && ls elasticmq.conf", "not sqs-local leftover; sqs local leftover is not dest", "treat leftover sqs local as dest then CLI parquet.", "sqs leftover; # elasticmq.conf claimed dest", "sqs leftover|elasticmq.conf"),
    s_from(7, "pubsub-emulator-leftover-as-dest", "psem", "pubsub emulator leftover", "pubsub-emulator.log", "pubsub emulator leftover", "pubsub leftover && ls pubsub-emulator.log", "not pubsub-emulator leftover; pubsub emulator leftover is not dest", "treat leftover pubsub emulator as dest then CLI parquet.", "pubsub leftover; # pubsub-emulator.log claimed dest", "pubsub leftover|pubsub-emulator.log"),
    s_from(8, "zeromq-dump-leftover-as-dest", "zmdp", "zeromq dump leftover", "zeromq.dump", "zeromq dump leftover", "zeromq leftover && ls zeromq.dump", "not zeromq-dump leftover; zeromq dump leftover is not dest", "treat leftover zeromq dump as dest then CLI parquet.", "zeromq leftover; # zeromq.dump claimed dest", "zeromq leftover|zeromq.dump"),
    s_from(9, "nsq-data-leftover-as-dest", "nsqd", "nsq data leftover", "nsq-data", "nsq data leftover", "nsq leftover && ls nsq-data", "not nsq-data leftover; nsq data leftover is not dest", "treat leftover nsq data as dest then CLI parquet.", "nsq leftover; # nsq-data claimed dest", "nsq leftover|nsq-data"),
    s_from(10, "beanstalkd-binlog-leftover-as-dest", "btbl", "beanstalkd binlog leftover", "beanstalkd.binlog", "beanstalkd binlog leftover", "beanstalkd leftover && ls beanstalkd.binlog", "not beanstalkd-binlog leftover; beanstalkd binlog leftover is not dest", "treat leftover beanstalkd binlog as dest then CLI parquet.", "beanstalkd leftover; # beanstalkd.binlog claimed dest", "beanstalkd leftover|beanstalkd.binlog"),
    s_from(11, "sidekiq-dump-leftover-as-dest", "skdp", "sidekiq dump leftover", "sidekiq.dump", "sidekiq dump leftover", "sidekiq leftover && ls sidekiq.dump", "not sidekiq-dump leftover; sidekiq dump leftover is not dest", "treat leftover sidekiq dump as dest then CLI parquet.", "sidekiq leftover; # sidekiq.dump claimed dest", "sidekiq leftover|sidekiq.dump"),
    s_from(12, "celery-broker-leftover-as-dest", "clbr", "celery broker leftover", "celerybroker", "celery broker leftover", "celery leftover && ls celerybroker", "not celery-broker leftover; celery broker leftover is not dest", "treat leftover celery broker as dest then CLI parquet.", "celery leftover; # celerybroker claimed dest", "celery leftover|celerybroker"),
    s_from(13, "rq-dump-leftover-as-dest", "rqdp", "rq dump leftover", "rq.dump", "rq dump leftover", "rq leftover && ls rq.dump", "not rq-dump leftover; rq dump leftover is not dest", "treat leftover rq dump as dest then CLI parquet.", "rq leftover; # rq.dump claimed dest", "rq leftover|rq.dump"),
    s_from(14, "huey-sqlite-leftover-as-dest", "hysq", "huey sqlite leftover", "huey.sqlite", "huey sqlite leftover", "huey leftover && ls huey.sqlite", "not huey-sqlite leftover; huey sqlite leftover is not dest", "treat leftover huey sqlite as dest then CLI parquet.", "huey leftover; # huey.sqlite claimed dest", "huey leftover|huey.sqlite"),
    s_from(15, "dramatiq-redis-leftover-as-dest", "dmrd", "dramatiq redis leftover", "dramatiq.rdb", "dramatiq redis leftover", "dramatiq leftover && ls dramatiq.rdb", "not dramatiq-redis leftover; dramatiq redis leftover is not dest", "treat leftover dramatiq redis as dest then CLI parquet.", "dramatiq leftover; # dramatiq.rdb claimed dest", "dramatiq leftover|dramatiq.rdb"),
    s_from(16, "bullmq-dump-leftover-as-dest", "bmdp", "bullmq dump leftover", "bullmq.dump", "bullmq dump leftover", "bullmq leftover && ls bullmq.dump", "not bullmq-dump leftover; bullmq dump leftover is not dest", "treat leftover bullmq dump as dest then CLI parquet.", "bullmq leftover; # bullmq.dump claimed dest", "bullmq leftover|bullmq.dump"),
    s_from(17, "resque-dump-leftover-as-dest", "rsdp", "resque dump leftover", "resque.dump", "resque dump leftover", "resque leftover && ls resque.dump", "not resque-dump leftover; resque dump leftover is not dest", "treat leftover resque dump as dest then CLI parquet.", "resque leftover; # resque.dump claimed dest", "resque leftover|resque.dump"),
    s_from(18, "delayedjob-sql-leftover-as-dest", "djsq", "delayedjob sql leftover", "delayed_jobs.sql", "delayedjob sql leftover", "delayedjob leftover && ls delayed_jobs.sql", "not delayedjob-sql leftover; delayedjob sql leftover is not dest", "treat leftover delayedjob sql as dest then CLI parquet.", "delayedjob leftover; # delayed_jobs.sql claimed dest", "delayedjob leftover|delayed_jobs.sql"),
    s_from(19, "obanjobs-json-leftover-as-dest", "objs", "obanjobs json leftover", "oban.json", "oban jobs leftover", "obanjobs leftover && ls oban.json", "not obanjobs-json leftover; oban jobs leftover is not dest", "treat leftover oban jobs as dest then CLI parquet.", "obanjobs leftover; # oban.json claimed dest", "obanjobs leftover|oban.json"),
    s_from(20, "faktory-dump-leftover-as-dest", "fkdp", "faktory dump leftover", "faktory.dump", "faktory dump leftover", "faktory leftover && ls faktory.dump", "not faktory-dump leftover; faktory dump leftover is not dest", "treat leftover faktory dump as dest then CLI parquet.", "faktory leftover; # faktory.dump claimed dest", "faktory leftover|faktory.dump"),
    s_from(21, "gearman-queue-leftover-as-dest", "gmqu", "gearman queue leftover", "gearman.queue", "gearman queue leftover", "gearman leftover && ls gearman.queue", "not gearman-queue leftover; gearman queue leftover is not dest", "treat leftover gearman queue as dest then CLI parquet.", "gearman leftover; # gearman.queue claimed dest", "gearman leftover|gearman.queue"),
    s_from(22, "ironmq-dump-leftover-as-dest", "imdp", "ironmq dump leftover", "ironmq.dump", "ironmq dump leftover", "ironmq leftover && ls ironmq.dump", "not ironmq-dump leftover; ironmq dump leftover is not dest", "treat leftover ironmq dump as dest then CLI parquet.", "ironmq leftover; # ironmq.dump claimed dest", "ironmq leftover|ironmq.dump"),
    s_from(23, "azure-queue-emu-leftover-as-dest", "azqe", "azure queue emu leftover", "azurite-queue.json", "azure queue emu leftover", "azure leftover && ls azurite-queue.json", "not azure-queue-emu leftover; azure queue emu leftover is not dest", "treat leftover azure queue emu as dest then CLI parquet.", "azure leftover; # azurite-queue.json claimed dest", "azure leftover|azurite-queue.json"),
    s_from(24, "gcp-tasks-emu-leftover-as-dest", "gcte", "gcp tasks emu leftover", "cloudtasks-emulator.log", "gcp tasks emu leftover", "gcp leftover && ls cloudtasks-emulator.log", "not gcp-tasks-emu leftover; gcp tasks emu leftover is not dest", "treat leftover gcp tasks emu as dest then CLI parquet.", "gcp leftover; # cloudtasks-emulator.log claimed dest", "gcp leftover|cloudtasks-emulator.log"),
    s_from(25, "amazonmq-data-leftover-as-dest", "amqd", "amazonmq data leftover", "amazonmq-data", "amazonmq data leftover", "amazonmq leftover && ls amazonmq-data", "not amazonmq-data leftover; amazonmq data leftover is not dest", "treat leftover amazonmq data as dest then CLI parquet.", "amazonmq leftover; # amazonmq-data claimed dest", "amazonmq leftover|amazonmq-data"),
    s_from(26, "ibmmq-qlocal-leftover-as-dest", "ibmq", "ibmmq qlocal leftover", "qmgr/qlocal", "ibmmq qlocal leftover", "ibmmq leftover && ls qmgr/qlocal", "not ibmmq-qlocal leftover; ibmmq qlocal leftover is not dest", "treat leftover ibmmq qlocal as dest then CLI parquet.", "ibmmq leftover; # qmgr/qlocal claimed dest", "ibmmq leftover|qmgr/qlocal"),
    s_from(27, "solace-spool-leftover-as-dest", "slsp", "solace spool leftover", "solace/spool", "solace spool leftover", "solace leftover && ls solace/spool", "not solace-spool leftover; solace spool leftover is not dest", "treat leftover solace spool as dest then CLI parquet.", "solace leftover; # solace/spool claimed dest", "solace leftover|solace/spool"),
    s_from(28, "redpanda-data-leftover-as-dest", "rpdt", "redpanda data leftover", "redpanda/data", "redpanda data leftover", "redpanda leftover && ls redpanda/data", "not redpanda-data leftover; redpanda data leftover is not dest", "treat leftover redpanda data as dest then CLI parquet.", "redpanda leftover; # redpanda/data claimed dest", "redpanda leftover|redpanda/data"),
    s_from(29, "warpstream-log-leftover-as-dest", "wslg", "warpstream log leftover", "warpstream/log", "warpstream log leftover", "warpstream leftover && ls warpstream/log", "not warpstream-log leftover; warpstream log leftover is not dest", "treat leftover warpstream log as dest then CLI parquet.", "warpstream leftover; # warpstream/log claimed dest", "warpstream leftover|warpstream/log"),
    s_from(30, "materialize-log-leftover-as-dest", "mzlg", "materialize log leftover", "materialize/log", "materialize log leftover", "materialize leftover && ls materialize/log", "not materialize-log leftover; materialize log leftover is not dest", "treat leftover materialize log as dest then CLI parquet.", "materialize leftover; # materialize/log claimed dest", "materialize leftover|materialize/log"),
    s_from(31, "debezium-offset-leftover-as-dest", "dbof", "debezium offset leftover", "debezium/offsets", "debezium offset leftover", "debezium leftover && ls debezium/offsets", "not debezium-offset leftover; debezium offset leftover is not dest", "treat leftover debezium offset as dest then CLI parquet.", "debezium leftover; # debezium/offsets claimed dest", "debezium leftover|debezium/offsets"),
]

LEFTOVER = [
    l_from(0, "kafka-zk-leftover-handoff", "kfzk", "zookeeper-data", "kafka zk leftover", "kafka zk leftover", "not kafka logdir leftover; leftover kafka zk as dest", "ship leftover kafka zk as dest.", "kafka zk leftover; # zookeeper-data on disk", "kafka leftover|zookeeper-data"),
    l_from(1, "rabbitmq-log-leftover-handoff", "rblg", "rabbitmq.log", "rabbitmq log leftover", "rabbitmq log leftover", "not rabbitmq mnesia leftover; leftover rabbitmq log as dest", "ship leftover rabbitmq log as dest.", "rabbitmq log leftover; # rabbitmq.log on disk", "rabbitmq leftover|rabbitmq.log"),
    l_from(2, "mosquitto-log-leftover-handoff", "mqlg", "mosquitto.log", "mosquitto log leftover", "mosquitto log leftover", "not mosquitto store leftover; leftover mosquitto log as dest", "ship leftover mosquitto log as dest.", "mosquitto log leftover; # mosquitto.log on disk", "mosquitto leftover|mosquitto.log"),
    l_from(3, "nats-leaf-leftover-handoff", "ntlf", "jetstream/leaf", "nats leaf leftover", "nats leaf leftover", "not nats jetstream leftover; leftover nats leaf as dest", "ship leftover nats leaf as dest.", "nats leaf leftover; # jetstream/leaf on disk", "nats leftover|jetstream/leaf"),
    l_from(4, "pulsar-ledgers-leftover-handoff", "psld", "pulsar/ledgers", "pulsar ledgers leftover", "pulsar ledgers leftover", "not pulsar journal leftover; leftover pulsar ledgers as dest", "ship leftover pulsar ledgers as dest.", "pulsar ledgers leftover; # pulsar/ledgers on disk", "pulsar leftover|pulsar/ledgers"),
    l_from(5, "redis-stream-groups-leftover-handoff", "rdsg", "stream.groups.json", "redis stream groups leftover", "redis stream groups leftover", "not redis stream leftover; leftover redis stream groups as dest", "ship leftover redis stream groups as dest.", "redis stream groups leftover; # stream.groups.json on disk", "redis leftover|stream.groups.json"),
    l_from(6, "sqs-local-log-leftover-handoff", "sqslg", "elasticmq.log", "sqs local log leftover", "sqs local log leftover", "not sqs local leftover; leftover sqs local log as dest", "ship leftover sqs local log as dest.", "sqs local log leftover; # elasticmq.log on disk", "sqs leftover|elasticmq.log"),
    l_from(7, "pubsub-emu-store-leftover-handoff", "pses", "pubsub-emulator.store", "pubsub emu store leftover", "pubsub emu store leftover", "not pubsub emulator leftover; leftover pubsub emu store as dest", "ship leftover pubsub emu store as dest.", "pubsub emu store leftover; # pubsub-emulator.store on disk", "pubsub leftover|pubsub-emulator.store"),
    l_from(8, "zeromq-log-leftover-handoff", "zmlg", "zeromq.log", "zeromq log leftover", "zeromq log leftover", "not zeromq dump leftover; leftover zeromq log as dest", "ship leftover zeromq log as dest.", "zeromq log leftover; # zeromq.log on disk", "zeromq leftover|zeromq.log"),
    l_from(9, "nsq-lookup-leftover-handoff", "nslk", "nsqlookupd.log", "nsq lookup leftover", "nsq lookup leftover", "not nsq data leftover; leftover nsq lookup as dest", "ship leftover nsq lookup as dest.", "nsq lookup leftover; # nsqlookupd.log on disk", "nsq leftover|nsqlookupd.log"),
    l_from(10, "beanstalkd-log-leftover-handoff", "btlg", "beanstalkd.log", "beanstalkd log leftover", "beanstalkd log leftover", "not beanstalkd binlog leftover; leftover beanstalkd log as dest", "ship leftover beanstalkd log as dest.", "beanstalkd log leftover; # beanstalkd.log on disk", "beanstalkd leftover|beanstalkd.log"),
    l_from(11, "sidekiq-log-leftover-handoff", "sklg", "sidekiq.log", "sidekiq log leftover", "sidekiq log leftover", "not sidekiq dump leftover; leftover sidekiq log as dest", "ship leftover sidekiq log as dest.", "sidekiq log leftover; # sidekiq.log on disk", "sidekiq leftover|sidekiq.log"),
    l_from(12, "celery-result-leftover-handoff", "clrs", "celeryresult", "celery result leftover", "celery result leftover", "not celery broker leftover; leftover celery result as dest", "ship leftover celery result as dest.", "celery result leftover; # celeryresult on disk", "celery leftover|celeryresult"),
    l_from(13, "rq-log-leftover-handoff", "rqlg", "rq.log", "rq log leftover", "rq log leftover", "not rq dump leftover; leftover rq log as dest", "ship leftover rq log as dest.", "rq log leftover; # rq.log on disk", "rq leftover|rq.log"),
    l_from(14, "huey-log-leftover-handoff", "hylg", "huey.log", "huey log leftover", "huey log leftover", "not huey sqlite leftover; leftover huey log as dest", "ship leftover huey log as dest.", "huey log leftover; # huey.log on disk", "huey leftover|huey.log"),
    l_from(15, "dramatiq-log-leftover-handoff", "dmlg", "dramatiq.log", "dramatiq log leftover", "dramatiq log leftover", "not dramatiq redis leftover; leftover dramatiq log as dest", "ship leftover dramatiq log as dest.", "dramatiq log leftover; # dramatiq.log on disk", "dramatiq leftover|dramatiq.log"),
    l_from(16, "bullmq-log-leftover-handoff", "bmlg", "bullmq.log", "bullmq log leftover", "bullmq log leftover", "not bullmq dump leftover; leftover bullmq log as dest", "ship leftover bullmq log as dest.", "bullmq log leftover; # bullmq.log on disk", "bullmq leftover|bullmq.log"),
    l_from(17, "resque-log-leftover-handoff", "rslg", "resque.log", "resque log leftover", "resque log leftover", "not resque dump leftover; leftover resque log as dest", "ship leftover resque log as dest.", "resque log leftover; # resque.log on disk", "resque leftover|resque.log"),
    l_from(18, "delayedjob-log-leftover-handoff", "djlg", "delayed_job.log", "delayedjob log leftover", "delayedjob log leftover", "not delayedjob sql leftover; leftover delayedjob log as dest", "ship leftover delayedjob log as dest.", "delayedjob log leftover; # delayed_job.log on disk", "delayedjob leftover|delayed_job.log"),
    l_from(19, "oban-log-leftover-handoff", "oblg", "oban.log", "oban log leftover", "oban log leftover", "not oban jobs leftover; leftover oban log as dest", "ship leftover oban log as dest.", "oban log leftover; # oban.log on disk", "oban leftover|oban.log"),
    l_from(20, "faktory-log-leftover-handoff", "fklg", "faktory.log", "faktory log leftover", "faktory log leftover", "not faktory dump leftover; leftover faktory log as dest", "ship leftover faktory log as dest.", "faktory log leftover; # faktory.log on disk", "faktory leftover|faktory.log"),
    l_from(21, "gearman-log-leftover-handoff", "gmlg", "gearman.log", "gearman log leftover", "gearman log leftover", "not gearman queue leftover; leftover gearman log as dest", "ship leftover gearman log as dest.", "gearman log leftover; # gearman.log on disk", "gearman leftover|gearman.log"),
    l_from(22, "ironmq-log-leftover-handoff", "imlg", "ironmq.log", "ironmq log leftover", "ironmq log leftover", "not ironmq dump leftover; leftover ironmq log as dest", "ship leftover ironmq log as dest.", "ironmq log leftover; # ironmq.log on disk", "ironmq leftover|ironmq.log"),
    l_from(23, "azure-queue-log-leftover-handoff", "azql", "azurite-queue.log", "azure queue log leftover", "azure queue log leftover", "not azure queue emu leftover; leftover azure queue log as dest", "ship leftover azure queue log as dest.", "azure queue log leftover; # azurite-queue.log on disk", "azure leftover|azurite-queue.log"),
    l_from(24, "gcp-tasks-store-leftover-handoff", "gcts", "cloudtasks.store", "gcp tasks store leftover", "gcp tasks store leftover", "not gcp tasks emu leftover; leftover gcp tasks store as dest", "ship leftover gcp tasks store as dest.", "gcp tasks store leftover; # cloudtasks.store on disk", "gcp leftover|cloudtasks.store"),
    l_from(25, "amazonmq-log-leftover-handoff", "amql", "amazonmq.log", "amazonmq log leftover", "amazonmq log leftover", "not amazonmq data leftover; leftover amazonmq log as dest", "ship leftover amazonmq log as dest.", "amazonmq log leftover; # amazonmq.log on disk", "amazonmq leftover|amazonmq.log"),
    l_from(26, "ibmmq-log-leftover-handoff", "ibml", "qmgr/log", "ibmmq log leftover", "ibmmq log leftover", "not ibmmq qlocal leftover; leftover ibmmq log as dest", "ship leftover ibmmq log as dest.", "ibmmq log leftover; # qmgr/log on disk", "ibmmq leftover|qmgr/log"),
    l_from(27, "solace-log-leftover-handoff", "sllg", "solace/log", "solace log leftover", "solace log leftover", "not solace spool leftover; leftover solace log as dest", "ship leftover solace log as dest.", "solace log leftover; # solace/log on disk", "solace leftover|solace/log"),
    l_from(28, "redpanda-log-leftover-handoff", "rplg", "redpanda/log", "redpanda log leftover", "redpanda log leftover", "not redpanda data leftover; leftover redpanda log as dest", "ship leftover redpanda log as dest.", "redpanda log leftover; # redpanda/log on disk", "redpanda leftover|redpanda/log"),
    l_from(29, "warpstream-meta-leftover-handoff", "wsmt", "warpstream/meta", "warpstream meta leftover", "warpstream meta leftover", "not warpstream log leftover; leftover warpstream meta as dest", "ship leftover warpstream meta as dest.", "warpstream meta leftover; # warpstream/meta on disk", "warpstream leftover|warpstream/meta"),
    l_from(30, "materialize-catalog-leftover-handoff", "mzct", "materialize/catalog", "materialize catalog leftover", "materialize catalog leftover", "not materialize log leftover; leftover materialize catalog as dest", "ship leftover materialize catalog as dest.", "materialize catalog leftover; # materialize/catalog on disk", "materialize leftover|materialize/catalog"),
    l_from(31, "debezium-history-leftover-handoff", "dbhs", "debezium/history", "debezium history leftover", "debezium history leftover", "not debezium offset leftover; leftover debezium history as dest", "ship leftover debezium history as dest.", "debezium history leftover; # debezium/history on disk", "debezium leftover|debezium/history"),
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
        print("usage: ntp-mill-unique-llll21.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
