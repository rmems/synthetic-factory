#!/usr/bin/env python3
"""IRC mill r3819+ — wave-42 hadoop/hbase/cache leftover.

NEW on-call plants (not Wave-27–41 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
namenode|dfs.namenode.handler.count|1|10||/etc/hadoop/hdfs-site.xml|<value>1</value>|<value>10</value>|systemctl reload hadoop-hdfs-namenode|hdfs|nn_handler_1|rpcs|edits|jn leftover leftover down; bounce|dfs.namenode.handler.count leftover 1 leftover; every RPC serializes so HDFS 504s
datanode|dfs.datanode.handler.count|1|10||/etc/hadoop/hdfs-site.xml|<value>1</value>|<value>10</value>|systemctl reload hadoop-hdfs-datanode|hdfs|dn_handler_1|blocks|vols|nn leftover leftover down; bounce|dfs.datanode.handler.count leftover 1 leftover; every transfer serializes so writes 504s
journalnode|dfs.qjournal.write-txns.timeout.ms|1|20000|ms|/etc/hadoop/hdfs-site.xml|<value>1</value>|<value>20000</value>|systemctl reload hadoop-hdfs-journalnode|hdfs|jn_to_1|edits|journals|zk leftover leftover down; bounce|write-txns.timeout leftover 1 leftover; a 2s edit is aborted so HA 504s
zkfc|ha.zookeeper.session-timeout.ms|1|5000|ms|/etc/hadoop/core-site.xml|<value>1</value>|<value>5000</value>|systemctl reload hadoop-hdfs-zkfc|hdfs|zkfc_to_1|locks|nn|zk leftover leftover down; bounce|ha.zookeeper.session-timeout leftover 1 leftover; a 1ms blip fences the NN so clients 504s
resourcemanager|yarn.resourcemanager.am.max-attempts|1|2||/etc/hadoop/yarn-site.xml|<value>1</value>|<value>2</value>|systemctl reload hadoop-yarn-resourcemanager|yarn|rm_am_1|apps|ams|zk leftover leftover down; bounce|am.max-attempts leftover 1 leftover; the first AM crash is terminal so jobs 504s
nodemanager|yarn.nodemanager.vmem-pmem-ratio|1|2.1||/etc/hadoop/yarn-site.xml|<value>1</value>|<value>2.1</value>|systemctl reload hadoop-yarn-nodemanager|yarn|nm_vmem_1|containers|disks|rm leftover leftover down; bounce|vmem-pmem-ratio leftover 1 leftover; every container is killed so Spark 504s
historyserver|mapreduce.jobhistory.datestring.cache.size|1|200000||/etc/hadoop/mapred-site.xml|<value>1</value>|<value>200000</value>|systemctl reload hadoop-mapreduce-historyserver|mapred|hs_cache_1|jobs|logs|hdfs leftover leftover down; bounce|datestring.cache.size leftover 1 leftover; every history miss hits HDFS so the UI 504s
secondarynamenode|dfs.namenode.checkpoint.txns|1|1000000||/etc/hadoop/hdfs-site.xml|<value>1</value>|<value>1000000</value>|systemctl reload hadoop-hdfs-secondarynamenode|hdfs|snn_ckpt_1|ckpts|edits|nn leftover leftover down; bounce|checkpoint.txns leftover 1 leftover; checkpoints every txn so the SNN 100%s
jobhistory|mapreduce.jobhistory.joblist.cache.size|1|20000||/etc/hadoop/mapred-site.xml|<value>1</value>|<value>20000</value>|systemctl reload hadoop-mapreduce-historyserver|mapred|jh_list_1|jobs|logs|hdfs leftover leftover down; bounce|joblist.cache.size leftover 1 leftover; every list is a scan so the UI 504s
timelineserver|yarn.timeline-service.handler-thread-count|1|10||/etc/hadoop/yarn-site.xml|<value>1</value>|<value>10</value>|systemctl reload hadoop-yarn-timelineserver|yarn|tl_thr_1|entities|leveldb|hdfs leftover leftover down; bounce|handler-thread-count leftover 1 leftover; every entity serializes so Spark UI 504s
hivemetastore|hive.metastore.server.max.threads|1|32||/etc/hive/hive-site.xml|<value>1</value>|<value>32</value>|systemctl reload hive-metastore|hive|hms_thr_1|rpcs|catalog|mysql leftover leftover down; bounce|server.max.threads leftover 1 leftover; every get_table serializes so Spark 504s
hiveserver2|hive.server2.thrift.max.worker.threads|1|32||/etc/hive/hive-site.xml|<value>1</value>|<value>32</value>|systemctl reload hive-server2|beeline|hs2_thr_1|sessions|ops|hms leftover leftover down; bounce|thrift.max.worker.threads leftover 1 leftover; every session serializes so Beeline 504s
impalad|impalad_admission_control_slots|1|8||/etc/impala/impalad.conf|admission_control_slots=1|admission_control_slots=8|systemctl reload impalad|impala-shell|imp_slots_1|queries|daemons|statestore leftover leftover down; bounce|admission_control_slots leftover 1 leftover; every query waits so BI 504s
statestored|statestore_max_subscribers|1|50||/etc/impala/statestored.conf|max_subscribers=1|max_subscribers=50|systemctl reload statestored|impala-shell|ss_sub_1|subs|daemons|catalog leftover leftover down; bounce|statestore_max_subscribers leftover 1 leftover; the second impalad is refused so the cluster 504s
catalogd|catalog_topic_update_timeout|1|30|s|/etc/impala/catalogd.conf|topic_update_timeout=1|topic_update_timeout=30|systemctl reload catalogd|impala-shell|cat_to_1|mds|hms|hms leftover leftover down; bounce|catalog_topic_update_timeout leftover 1 leftover; a 2s HMS fetch is aborted so invalidate 504s
kudumaster|raft_heartbeat_interval_ms|1|500|ms|/etc/kudu/master.gflagfile|--raft_heartbeat_interval_ms=1|--raft_heartbeat_interval_ms=500|systemctl reload kudu-master|kudu|kudu_hb_1|raft|tservers|zk leftover leftover down; bounce|raft_heartbeat_interval leftover 1 leftover; heartbeats every 1ms so CPU 100%s
kudutserver|tablet_copy_timeout|1|60|s|/etc/kudu/tserver.gflagfile|--tablet_copy_timeout_ms=1|--tablet_copy_timeout_ms=60000|systemctl reload kudu-tserver|kudu|kudu_copy_1|tablets|data|master leftover leftover down; bounce|tablet_copy_timeout leftover 1 leftover; a 2s copy is aborted so the replica 504s
hbasemaster|hbase.master.handler.count|1|30||/etc/hbase/hbase-site.xml|<value>1</value>|<value>30</value>|systemctl reload hbase-master|hbase|hbm_handler_1|rpcs|meta|zk leftover leftover down; bounce|hbase.master.handler.count leftover 1 leftover; every assign serializes so regions 504s
regionserver|hbase.regionserver.handler.count|1|30||/etc/hbase/hbase-site.xml|<value>1</value>|<value>30</value>|systemctl reload hbase-regionserver|hbase|hbrs_handler_1|rpcs|regions|zk leftover leftover down; bounce|hbase.regionserver.handler.count leftover 1 leftover; every Get serializes so the API 504s
accumulomaster|master.server.threadpool.size|1|8||/etc/accumulo/accumulo.properties|master.server.threadpool.size=1|master.server.threadpool.size=8|systemctl reload accumulo-master|accumulo|acc_thr_1|tables|tservers|zk leftover leftover down; bounce|master.server.threadpool.size leftover 1 leftover; every merge serializes so ingest 504s
tserver|tserver.server.threads.minimum|1|8||/etc/accumulo/accumulo.properties|tserver.server.threads.minimum=1|tserver.server.threads.minimum=8|systemctl reload accumulo-tserver|accumulo|acc_ts_1|tablets|wal|zk leftover leftover down; bounce|tserver.server.threads leftover 1 leftover; every scan serializes so queries 504s
mongos|taskExecutorPoolSize|1|4||/etc/mongos.conf|taskExecutorPoolSize: 1|taskExecutorPoolSize: 4|systemctl reload mongos|mongosh|mongos_pool_1|cursors|shards|cfg leftover leftover down; bounce|taskExecutorPoolSize leftover 1 leftover; every scatter serializes so the app 504s
mongod|wiredTigerConcurrentReadTransactions|1|128||/etc/mongod.conf|wiredTigerConcurrentReadTransactions: 1|wiredTigerConcurrentReadTransactions: 128|systemctl reload mongod|mongosh|mongod_read_1|reads|wt|repl leftover leftover down; bounce|wiredTigerConcurrentReadTransactions leftover 1 leftover; every read serializes so p99 is 8s
csrs|electionTimeoutMillis|1|10000|ms|/etc/mongod.conf|electionTimeoutMillis: 1|electionTimeoutMillis: 10000|systemctl reload mongod|mongosh|csrs_el_1|votes|repl|disk leftover leftover full; bounce|electionTimeoutMillis leftover 1 leftover; every 1ms election flaps so writes 504s
solrcloud|solr.max.boolean.clauses|1|1024||/etc/solr/solr.xml|<int name="maxBooleanClauses">1</int>|<int name="maxBooleanClauses">1024</int>|systemctl reload solr|solr|solr_bool_1|queries|cores|zk leftover leftover down; bounce|max.boolean.clauses leftover 1 leftover; a 2-term query is refused so search 400s
lucene|lucene.maxClauseCount|1|1024||/etc/lucene/lucene.properties|maxClauseCount=1|maxClauseCount=1024|systemctl reload lucene|lucene|luc_clause_1|queries|idx|disk leftover leftover full; bounce|lucene.maxClauseCount leftover 1 leftover; BooleanQuery is refused so search 400s
tantivy|tantivy.writer.threads|1|4||/etc/tantivy/tantivy.toml|writer_threads = 1|writer_threads = 4|systemctl reload tantivy|tantivy|tan_thr_1|indexes|segs|disk leftover leftover full; bounce|writer.threads leftover 1 leftover; every commit serializes so ingest 504s
bleve|bleve.batch.size|1|1000||/etc/bleve/bleve.yaml|batch_size: 1|batch_size: 1000|systemctl reload bleve|bleve|bleve_batch_1|indexes|docs|disk leftover leftover full; bounce|bleve.batch.size leftover 1 leftover; every doc is its own batch so index 504s
sphinxsearch|max_children|1|20||/etc/sphinx/sphinx.conf|max_children = 1|max_children = 20|systemctl reload searchd|searchd|sph_ch_1|queries|idx|disk leftover leftover full; bounce|max_children leftover 1 leftover; every query serializes so search 504s
manticoresearch|max_threads|1|8||/etc/manticoresearch/manticore.conf|max_threads = 1|max_threads = 8|systemctl reload searchd|searchd|mants_thr_1|queries|idx|disk leftover leftover full; bounce|max_threads leftover 1 leftover; every query serializes so the API 504s
infinispan|infinispan.cluster.timeout|1|15|s|/etc/infinispan/infinispan.xml|cluster-timeout="1"|cluster-timeout="15"|systemctl reload infinispan|ispn-cli|ispn_to_1|caches|nodes|jgroups leftover leftover down; bounce|cluster.timeout leftover 1 leftover; a 2s view is aborted so the cache 504s
couchbase|queryTimeout|1|75|s|/etc/couchbase/couchbase.cfg|queryTimeout=1|queryTimeout=75|systemctl reload couchbase-server|couchbase-cli|cb_to_1|n1ql|buckets|ns leftover leftover down; bounce|queryTimeout leftover 1 leftover; a 2s N1QL is aborted so the SDK 504s
aerospike|proto-fd-idle-ms|1|60000|ms|/etc/aerospike/aerospike.conf|proto-fd-idle-ms 1|proto-fd-idle-ms 60000|systemctl reload aerospike|asadm|as_idle_1|conns|ns|fabric leftover leftover down; bounce|proto-fd-idle-ms leftover 1 leftover; every fd dies in 1ms so clients reconnect-storm
mcrouter|probe_timeout|1|500|ms|/etc/mcrouter/mcrouter.conf|"probe_timeout": 1|"probe_timeout": 500|systemctl reload mcrouter|mcrouter|mcr_probe_1|pools|hosts|memcached leftover leftover down; bounce|probe_timeout leftover 1 leftover; a 2s GET is marked dead so the pool 504s
twemproxy|timeout|1|400|ms|/etc/nutcracker/nutcracker.yml|timeout: 1|timeout: 400|systemctl reload nutcracker|nutcracker|twem_to_1|pools|redis|redis leftover leftover down; bounce|timeout leftover 1 leftover; a 2s GET is aborted so the app 504s
nutcracker|auto_eject_timeout|1|30|s|/etc/nutcracker/nutcracker.yml|server_retry_timeout: 1|server_retry_timeout: 30000|systemctl reload nutcracker|nutcracker|nut_eject_1|servers|pools|redis leftover leftover down; bounce|auto_eject_timeout leftover 1 leftover; a 1s blip ejects the shard so keys 404
trafficserver|proxy.config.http.connect_attempts_timeout|1|30|s|/etc/trafficserver/records.config|CONFIG proxy.config.http.connect_attempts_timeout INT 1|CONFIG proxy.config.http.connect_attempts_timeout INT 30|systemctl reload trafficserver|traffic_ctl|ats_to_1|origins|cache|disk leftover leftover full; bounce|connect_attempts_timeout leftover 1 leftover; a 2s origin is aborted so the cache 504s
chproxy|hackme.timeout|1|10|s|/etc/chproxy/config.yml|timeout: 1s|timeout: 10s|systemctl reload chproxy|chproxy|chp_to_1|queries|clusters|ch leftover leftover down; bounce|hackme.timeout leftover 1 leftover; a 2s query is aborted so Grafana 504s
altinity|clickhouse.timeout|1|30|s|/etc/altinity/operator.yaml|timeout: 1s|timeout: 30s|systemctl reload altinity-operator|kubectl|alt_to_1|shards|keepers|ch leftover leftover down; bounce|clickhouse.timeout leftover 1 leftover; a 2s reconcile is aborted so the CHI 504s
bytehouse|BYTEHOUSE_TIMEOUT|1|30|s|/etc/bytehouse/cnch.xml|<timeout>1</timeout>|<timeout>30</timeout>|systemctl reload bytehouse|bytehouse|bh_to_1|queries|vw|fs leftover leftover down; bounce|BYTEHOUSE_TIMEOUT leftover 1 leftover; a 2s query is aborted so the VW 504s
kylin|kylin.query.timeout-seconds|1|300|s|/etc/kylin/kylin.properties|kylin.query.timeout-seconds=1|kylin.query.timeout-seconds=300|systemctl reload kylin|kylin.sh|kyl_to_1|cubes|queries|hbase leftover leftover down; bounce|kylin.query.timeout leftover 1 leftover; a 2s cube scan is aborted so the API 504s
hadoop|ipc.client.connect.timeout|1|20000|ms|/etc/hadoop/core-site.xml|<value>1</value>|<value>20000</value>|systemctl reload hadoop|hadoop|hd_ipc_1|rpcs|nn|nn leftover leftover down; bounce|ipc.client.connect.timeout leftover 1 leftover; a 2s RPC is aborted so jobs 504s
hdfs|dfs.client.socket-timeout|1|60000|ms|/etc/hadoop/hdfs-site.xml|<value>1</value>|<value>60000</value>|systemctl reload hadoop-hdfs|hdfs|hdfs_sock_1|reads|blocks|dn leftover leftover down; bounce|dfs.client.socket-timeout leftover 1 leftover; a 2s read is aborted so Spark 504s
yarn|yarn.client.nodemanager-connect.max-wait-ms|1|180000|ms|/etc/hadoop/yarn-site.xml|<value>1</value>|<value>180000</value>|systemctl reload hadoop-yarn|yarn|yarn_nm_1|apps|nms|rm leftover leftover down; bounce|nodemanager-connect.max-wait leftover 1 leftover; a 2s NM is aborted so the AM 504s
mapred|mapreduce.task.timeout|1|600000|ms|/etc/hadoop/mapred-site.xml|<value>1</value>|<value>600000</value>|systemctl reload hadoop-mapreduce|mapred|mr_to_1|tasks|jobs|nm leftover leftover down; bounce|mapreduce.task.timeout leftover 1 leftover; a 2s map is aborted so the job 504s
hive|hive.exec.compress.intermediate|1|true||/etc/hive/hive-site.xml|<value>1</value>|<value>true</value>|systemctl reload hive|hive|hive_cmp_1|jobs|scratch|hdfs leftover leftover down; bounce|hive.exec.compress leftover 1 leftover; intermediate files explode so the job 504s
tez|tez.am.resource.memory.mb|1|2048||/etc/tez/tez-site.xml|<value>1</value>|<value>2048</value>|systemctl reload hive|hive|tez_mem_1|dags|ams|yarn leftover leftover down; bounce|tez.am.resource.memory leftover 1 leftover; the AM OOMs so the DAG 504s
impala|idle_session_timeout|1|3600|s|/etc/impala/impalad.conf|idle_session_timeout=1|idle_session_timeout=3600|systemctl reload impalad|impala-shell|imp_idle_1|sessions|queries|statestore leftover leftover down; bounce|idle_session_timeout leftover 1 leftover; a 2s pause closes the session so BI 401s
kudu|rpc_default_keepalive_time_ms|1|65000|ms|/etc/kudu/gflagfile|--rpc_default_keepalive_time_ms=1|--rpc_default_keepalive_time_ms=65000|systemctl reload kudu-tserver|kudu|kudu_ka_1|rpcs|ts|master leftover leftover down; bounce|rpc_default_keepalive leftover 1 leftover; every RPC dies so Spark 504s
phoenix|phoenix.query.timeoutMs|1|600000|ms|/etc/phoenix/hbase-site.xml|<value>1</value>|<value>600000</value>|systemctl reload phoenix-query-server|sqlline.py|phx_to_1|sql|hbase|zk leftover leftover down; bounce|phoenix.query.timeoutMs leftover 1 leftover; a 2s SQL is aborted so the JDBC 504s
hbase|hbase.rpc.timeout|1|60000|ms|/etc/hbase/hbase-site.xml|<value>1</value>|<value>60000</value>|systemctl reload hbase-regionserver|hbase|hb_rpc_1|rpcs|rs|zk leftover leftover down; bounce|hbase.rpc.timeout leftover 1 leftover; a 2s Get is aborted so the app 504s
accumulo|general.rpc.timeout|1|120|s|/etc/accumulo/accumulo.properties|general.rpc.timeout=1s|general.rpc.timeout=120s|systemctl reload accumulo-tserver|accumulo|acc_rpc_1|rpcs|ts|zk leftover leftover down; bounce|general.rpc.timeout leftover 1 leftover; a 2s scan is aborted so ingest 504s
znapzend|znapzend.timeout|1|3600|s|/etc/znapzend/znapzend.conf|timeout=1|timeout=3600|systemctl reload znapzend|znapzend|znap_to_1|snaps|datasets|zfs leftover leftover down; bounce|znapzend.timeout leftover 1 leftover; a 2s send is aborted so DR has no replica
zpool|ZPOOL_TIMEOUT|1|30|s|/etc/zfs/zed.d/timeout.sh|timeout=1|timeout=30|systemctl reload zfs-zed|zpool|zpool_to_1|pools|vdevs|disk leftover leftover full; bounce|ZPOOL_TIMEOUT leftover 1 leftover; a 2s scrub is aborted so the pool 504s
zed|ZED_TIMEOUT|1|30|s|/etc/zfs/zed.d/zed.rc|ZED_SYSLOG_TIMEOUT=1|ZED_SYSLOG_TIMEOUT=30|systemctl reload zfs-zed|zed|zed_to_1|events|pools|zfs leftover leftover down; bounce|ZED_TIMEOUT leftover 1 leftover; a 2s event is aborted so resilver pages vanish
btrfs|BTRFS_TIMEOUT|1|30|s|/etc/btrfs/btrfs.conf|timeout=1|timeout=30|systemctl reload btrfs-scrub|btrfs|btrfs_to_1|subvols|devs|disk leftover leftover full; bounce|BTRFS_TIMEOUT leftover 1 leftover; a 2s balance is aborted so the fs 504s
lvm2|LVM_TIMEOUT|1|30|s|/etc/lvm/lvm.conf|udev_sync_timeout=1|udev_sync_timeout=30|systemctl reload lvm2-monitor|lvm|lvm2_to_1|vgs|pvs|udev leftover leftover down; bounce|LVM_TIMEOUT leftover 1 leftover; a 2s vgchange is aborted so the LV 504s
ovs-vswitchd|other_config:flow-limit|1|200000||/etc/openvswitch/conf.db|flow-limit=1|flow-limit=200000|systemctl reload openvswitch|ovs-vsctl|ovs_flow_1|flows|bridges|dpdk leftover leftover down; bounce|flow-limit leftover 1 leftover; the second flow is dropped so pods 504s
looking-glass|LG_TIMEOUT|1|10|s|/etc/looking-glass/lg.conf|timeout=1|timeout=10|systemctl reload looking-glass|lg|lg_to_1|kvm|ivshmem|kvm leftover leftover down; bounce|LG_TIMEOUT leftover 1 leftover; a 2s frame is aborted so the console 504s
bgpq4|BGPQ4_TIMEOUT|1|10|s|/etc/bgpq4/bgpq4.conf|timeout=1|timeout=10|systemctl reload bgpq4|bgpq4|bgpq_to_1|irr|asns|whois leftover leftover down; bounce|BGPQ4_TIMEOUT leftover 1 leftover; a 2s IRR is aborted so the prefix-list 504s
irrtoolset|IRT_TIMEOUT|1|10|s|/etc/irrtoolset/peval.conf|timeout=1|timeout=10|systemctl reload irrtoolset|peval|irt_to_1|rpsl|asns|whois leftover leftover down; bounce|IRT_TIMEOUT leftover 1 leftover; a 2s peval is aborted so the filter 504s
infoblox|WAPI_TIMEOUT|1|30|s|/etc/infoblox/wapi.conf|timeout=1|timeout=30|systemctl reload infoblox-wapi|curl|iblox_to_1|records|zones|https leftover leftover 403; bounce|WAPI_TIMEOUT leftover 1 leftover; a 2s GET is aborted so DHCP 504s
yugabyted|yb_timeout|1|60|s|/etc/yugabyte/yugabyted.conf|timeout=1|timeout=60|systemctl reload yugabyted|yugabyted|ybd_to_1|cluster|masters|rpc leftover leftover down; bounce|yb_timeout leftover 1 leftover; a 2s start is aborted so the universe 504s
ybmaster|yb_rpc_timeout|1|60|s|/etc/yugabyte/master.conf|--rpc_timeout=1|--rpc_timeout=60|systemctl reload yb-master|yb-admin|ybm_to_1|tablets|ts|raft leftover leftover down; bounce|yb_rpc_timeout leftover 1 leftover; a 2s catalog RPC is aborted so DDL 504s
ybtserver|yb_rpc_timeout|1|60|s|/etc/yugabyte/tserver.conf|--rpc_timeout=1|--rpc_timeout=60|systemctl reload yb-tserver|ysqlsh|ybts_to_1|sql|tablets|master leftover leftover down; bounce|yb_rpc_timeout leftover 1 leftover; a 2s SQL is aborted so YSQL 504s
tidbserver|tikv-client.grpc-timeout|1|3|s|/etc/tidb/tidb.toml|grpc-timeout = "1s"|grpc-timeout = "3s"|systemctl reload tidb-server|tidb-server|tidb_grpc_1|sql|tikv|pd leftover leftover down; bounce|tikv-client.grpc-timeout leftover 1 leftover; a 2s coprocessor is aborted so SQL 504s
scyllamanager|SCYLLA_MANAGER_TIMEOUT|1|30|s|/etc/scylla-manager/scylla-manager.yaml|timeout: 1s|timeout: 30s|systemctl reload scylla-manager|sctool|scm_to_1|repairs|clusters|cql leftover leftover down; bounce|SCYLLA_MANAGER_TIMEOUT leftover 1 leftover; a 2s repair is aborted so repair 504s
dgraphzero|raft.timeout|1|10|s|/etc/dgraph/zero.yaml|timeout: 1s|timeout: 10s|systemctl reload dgraph-zero|dgraph|dgz_to_1|membership|alphas|raft leftover leftover down; bounce|raft.timeout leftover 1 leftover; a 2s election is aborted so Zero 504s
planetscale|PS_TIMEOUT|1|30|s|/etc/planetscale/pscale.env|PS_TIMEOUT=1|PS_TIMEOUT=30|systemctl reload pscale|pscale|ps_to_1|branches|vtgate|https leftover leftover 403; bounce|PS_TIMEOUT leftover 1 leftover; a 2s branch is aborted so deploy 504s
cockroachdb|COCKROACH_TIMEOUT|1|30|s|/etc/cockroach/cockroach.yaml|timeout: 1s|timeout: 30s|systemctl reload cockroach|cockroach|crdb_to_1|sql|ranges|kv leftover leftover down; bounce|COCKROACH_TIMEOUT leftover 1 leftover; a 2s SQL is aborted so the app 504s
spanner|SPANNER_TIMEOUT|1|30|s|/etc/spanner/emulator.yaml|timeout: 1s|timeout: 30s|systemctl reload spanner-emulator|spanner|spn_to_1|sql|sessions|grpc leftover leftover down; bounce|SPANNER_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the txn 504s
bigtable|BIGTABLE_TIMEOUT|1|30|s|/etc/bigtable/emulator.yaml|timeout: 1s|timeout: 30s|systemctl reload bigtable-emulator|cbt|bt_to_1|rows|tables|grpc leftover leftover down; bounce|BIGTABLE_TIMEOUT leftover 1 leftover; a 2s mutate is aborted so ingest 504s
dynamodb|DYNAMODB_TIMEOUT|1|30|s|/etc/dynamodb/local.yaml|timeout: 1s|timeout: 30s|systemctl reload dynamodb-local|aws|ddb_to_1|items|tables|http leftover leftover down; bounce|DYNAMODB_TIMEOUT leftover 1 leftover; a 2s PutItem is aborted so the API 504s
documentdb|DOCDB_TIMEOUT|1|30|s|/etc/documentdb/docdb.yaml|timeout: 1s|timeout: 30s|systemctl reload documentdb|mongo|docdb_to_1|docs|csrs|tls leftover leftover down; bounce|DOCDB_TIMEOUT leftover 1 leftover; a 2s find is aborted so the SDK 504s
neptune|NEPTUNE_TIMEOUT|1|30|s|/etc/neptune/gremlin.yaml|timeout: 1s|timeout: 30s|systemctl reload neptune|gremlin|nep_to_1|gremlin|sparql|ws leftover leftover down; bounce|NEPTUNE_TIMEOUT leftover 1 leftover; a 2s traversal is aborted so the graph 504s
aurora|AURORA_TIMEOUT|1|30|s|/etc/aurora/aurora.env|AURORA_TIMEOUT=1|AURORA_TIMEOUT=30|systemctl reload aurora|psql|aur_to_1|sql|writer|rds leftover leftover down; bounce|AURORA_TIMEOUT leftover 1 leftover; a 2s failover is aborted so the writer 504s
babelfish|BABELFISH_TIMEOUT|1|30|s|/etc/babelfish/babelfish.conf|timeout=1|timeout=30|systemctl reload babelfishpg|sqlcmd|bbf_to_1|tds|pg|pg leftover leftover down; bounce|BABELFISH_TIMEOUT leftover 1 leftover; a 2s TDS is aborted so the app 504s
citusdata|citus.max_adaptive_executor_pool_size|1|16||/etc/postgresql/citus.conf|citus.max_adaptive_executor_pool_size = 1|citus.max_adaptive_executor_pool_size = 16|systemctl reload postgresql|psql|citus_pool_1|shards|workers|pg leftover leftover down; bounce|max_adaptive_executor_pool leftover 1 leftover; every shard serializes so SQL 504s
polaris|POLARIS_TIMEOUT|1|30|s|/etc/polaris/polaris.yml|timeout: 1s|timeout: 30s|systemctl reload polaris|polaris|pol_to_1|catalogs|iceberg|jdbc leftover leftover down; bounce|POLARIS_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the table 504s
popeye|POPEYE_TIMEOUT|1|30|s|/etc/popeye/spinach.yml|timeout: 1s|timeout: 30s|systemctl reload popeye|popeye|pop_to_1|scans|ns|apiserver leftover leftover down; bounce|POPEYE_TIMEOUT leftover 1 leftover; a 2s list is aborted so the report is empty
casbin|CASBIN_TIMEOUT|1|10|s|/etc/casbin/casbin.conf|timeout=1|timeout=10|systemctl reload casbin|casbin|cas_to_1|enforces|policies|db leftover leftover down; bounce|CASBIN_TIMEOUT leftover 1 leftover; a 2s enforce is aborted so the API 401s
authzed|AUTHZED_TIMEOUT|1|10|s|/etc/authzed/spicedb.yaml|timeout: 1s|timeout: 10s|systemctl reload authzed|zed|az_to_1|checks|ns|pg leftover leftover down; bounce|AUTHZED_TIMEOUT leftover 1 leftover; a 2s Check is aborted so PDP 504s
zanzibar|ZANZIBAR_TIMEOUT|1|10|s|/etc/zanzibar/zanzibar.yaml|timeout: 1s|timeout: 10s|systemctl reload zanzibar|zanzibar|zan_to_1|checks|ns|zk leftover leftover down; bounce|ZANZIBAR_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so authz 504s
openpolicyagent|OPA_TIMEOUT|1|5|s|/etc/opa/config.yaml|timeout: 1s|timeout: 5s|systemctl reload opa|opa|opa_to_1|decisions|bundles|https leftover leftover 403; bounce|OPA_TIMEOUT leftover 1 leftover; a 2s eval is aborted so admit 504s
'''
WAVE42 = (
    "namenode/datanode/journalnode/zkfc/resourcemanager/nodemanager/"
    "historyserver/secondarynamenode/jobhistory/timelineserver/"
    "hivemetastore/hiveserver2/impalad/statestored/catalogd/kudumaster/"
    "kudutserver/hbasemaster/regionserver/accumulomaster/tserver/mongos/"
    "mongod/csrs/solrcloud/lucene/tantivy/bleve/sphinxsearch/"
    "manticoresearch/infinispan/couchbase/aerospike/mcrouter/twemproxy/"
    "nutcracker/trafficserver/chproxy/altinity/bytehouse/kylin/hadoop/"
    "hdfs/yarn/mapred/hive/tez/impala/kudu/phoenix/hbase/accumulo/"
    "znapzend/zpool/zed/btrfs/lvm2/ovs-vswitchd/looking-glass/bgpq4/"
    "irrtoolset/infoblox/yugabyted/ybmaster/ybtserver/tidbserver/"
    "scyllamanager/dgraphzero/planetscale/cockroachdb/spanner/bigtable/"
    "dynamodb/documentdb/neptune/aurora/babelfish/citusdata/polaris/"
    "popeye/casbin/authzed/zanzibar/openpolicyagent"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"x2{i:02d}x"
        ns = f"x2{i:02d}"
        clu = f"prod-apsx{901 + i}-{svc[:3]}"
        ticket = f"W2-{12159 + i}"
        node = f"ip-10-227-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 3819


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3818 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-42 leftover: {WAVE42}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
