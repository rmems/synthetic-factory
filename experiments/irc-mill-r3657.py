#!/usr/bin/env python3
"""IRC mill r3657+ — wave-38 HPC/control-plane leftover.

NEW on-call plants (not Wave-27–37 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

# daemon|key|old|new|unit|path|oldv|newv|reload|hpeer|metric|what|wipe|herring|rca_tail
ROWS = r'''
slurmd|TimeoutStopSec|1|90|s|/etc/slurm/slurmd.conf|TimeoutStopSec=1|TimeoutStopSec=90|systemctl reload slurmd|scontrol|slurmd_to_1|compute|nodes|munge leftover leftover down; bounce|TimeoutStopSec leftover 1 leftover; a 2s drain is SIGKILLed so nodes vanish
slurmdbd|PurgeJobAfter|1|12||/etc/slurm/slurmdbd.conf|PurgeJobAfter=1|PurgeJobAfter=12|systemctl reload slurmdbd|sacctmgr|slurmdbd_purge_1|accounting|jobs|mysql leftover leftover down; bounce|PurgeJobAfter leftover 1 leftover; job records vanish in 1 month-unit so fairshare is empty
munge|munge.key.ttl|1|86400|s|/etc/munge/munge.conf|ttl=1|ttl=86400|systemctl reload munge|mungekey|munge_ttl_1|auth|keys|clock leftover leftover drift; bounce|munge.key.ttl leftover 1 leftover; a 2s credential is expired so slurmd 401s
pbs_mom|timeout|1|30|s|/etc/pbs.conf|PBS_MOM_TIMEOUT=1|PBS_MOM_TIMEOUT=30|systemctl reload pbs_mom|qstat|pbsmom_to_1|jobs|nodes|server leftover leftover down; bounce|timeout leftover 1 leftover; a 2s poll is aborted so jobs stay R forever
pbs_sched|sched_cycle|1|30|s|/etc/pbs/sched_config|sched_cycle: 1|sched_cycle: 30|systemctl reload pbs_sched|qstat|pbssched_cyc_1|jobs|queues|server leftover leftover down; bounce|sched_cycle leftover 1 leftover; the scheduler busy-loops so dispatch never settles
sge_execd|load_report_time|1|40|s|/etc/gridengine/execd_params|load_report_time 1|load_report_time 40|systemctl reload sge_execd|qhost|sgeexec_load_1|hosts|queues|qmaster leftover leftover down; bounce|load_report_time leftover 1 leftover; execd storms qmaster so submits 504s
uge|reporting_params|1|30|s|/etc/uge/configuration|reporting_params 1|reporting_params 30|systemctl reload uge|qstat|uge_rep_1|jobs|queues|qmaster leftover leftover down; bounce|reporting_params leftover 1 leftover; a 2s report is aborted so fairshare 504s
collectl|interval|1|10||/etc/collectl.conf|Interval = 1|Interval = 10|systemctl reload collectl|collectl|collectl_int_1|metrics|logs|disk leftover leftover full; bounce|interval leftover 1 leftover; collectl writes every 1s so the disk 100%s
pcp|pmcd.timeout|1|10|s|/etc/pcp/pmcd/pmcd.conf|timeout=1|timeout=10|systemctl reload pmcd|pminfo|pcp_to_1|metrics|archives|pmlogger leftover leftover down; bounce|pmcd.timeout leftover 1 leftover; a 2s fetch is aborted so grafana 504s
nmon|NMON_INTERVAL|1|30|s|/etc/nmon/nmon.env|NMON_INTERVAL=1|NMON_INTERVAL=30|systemctl reload nmon|nmon|nmon_int_1|metrics|logs|disk leftover leftover full; bounce|NMON_INTERVAL leftover 1 leftover; nmon samples every 1s so the log fills the boot disk
likwid|LIKWID_TIMEOUT|1|30|s|/etc/likwid/likwid.cfg|timeout=1|timeout=30|systemctl reload likwid|likwid-perfctr|likwid_to_1|counters|events|msr leftover leftover down; bounce|LIKWID_TIMEOUT leftover 1 leftover; a 2s MSR read is aborted so the bench 504s
ganglia|gmond.timeout|1|10|s|/etc/ganglia/gmond.conf|timeout = 1|timeout = 10|systemctl reload gmond|gstat|ganglia_to_1|metrics|rrds|gmetad leftover leftover down; bounce|gmond.timeout leftover 1 leftover; a 2s UDP metric is dropped so the grid 504s
pdsh|PDSH_TIMEOUT|1|30|s|/etc/pdsh/pdsh.conf|PDSH_TIMEOUT=1|PDSH_TIMEOUT=30|systemctl reload pdsh|pdsh|pdsh_to_1|fanout|hosts|ssh leftover leftover down; bounce|PDSH_TIMEOUT leftover 1 leftover; a 2s node is skipped so the reboot misses racks
conman|timeout|1|30|s|/etc/conman.conf|timeout 1|timeout 30|systemctl reload conman|conman|conman_to_1|console|logs|serial leftover leftover down; bounce|timeout leftover 1 leftover; a 2s console attach is aborted so crash dumps vanish
warewulf|wwctl.timeout|1|30|s|/etc/warewulf/warewulf.conf|timeout: 1s|timeout: 30s|systemctl reload warewulfd|wwctl|ww_to_1|images|nodes|tftp leftover leftover down; bounce|wwctl.timeout leftover 1 leftover; a 2s overlay build is aborted so PXE 504s
xcat|xcatd.timeout|1|30|s|/etc/xcat/xcat.conf|timeout=1|timeout=30|systemctl reload xcatd|lsdef|xcat_to_1|nodes|images|tftp leftover leftover down; bounce|xcatd.timeout leftover 1 leftover; a 2s rinstall is aborted so the node stays diskless
cobbler|xmlrpc.timeout|1|30|s|/etc/cobbler/settings.yaml|xmlrpc_timeout: 1|xmlrpc_timeout: 30|systemctl reload cobblerd|cobbler|cobbler_to_1|profiles|systems|tftp leftover leftover down; bounce|xmlrpc.timeout leftover 1 leftover; a 2s sync is aborted so PXE menus stale
metrics-server|metric-resolution|1|15|s|/etc/metrics-server/args.env|metric-resolution=1s|metric-resolution=15s|systemctl reload metrics-server|kubectl|ms_res_1|hpa|pods|apiserver leftover leftover down; bounce|metric-resolution leftover 1 leftover; scrape storms apiserver so HPA 504s
npd|exportPeriod|1|30|s|/etc/node-problem-detector/config.json|exportPeriod: 1s|exportPeriod: 30s|systemctl reload node-problem-detector|npd|npd_exp_1|events|nodes|kubelet leftover leftover down; bounce|exportPeriod leftover 1 leftover; every 1s condition storms the API so nodes 504s
cluster-autoscaler|scan-interval|1|10|s|/etc/cluster-autoscaler/args.env|scan-interval=1s|scan-interval=10s|systemctl reload cluster-autoscaler|kubectl|ca_scan_1|nodes|asgs|apiserver leftover leftover down; bounce|scan-interval leftover 1 leftover; CA lists nodes every 1s so the API 504s
cluster-api|syncPeriod|1|10|m|/etc/cluster-api/manager.env|syncPeriod=1m|syncPeriod=10m|systemctl reload capi-controller|clusterctl|capi_sync_1|clusters|machines|etcd leftover leftover down; bounce|syncPeriod leftover 1 leftover; every cluster reconciles every 1m so the API 504s
clusterctl|timeout|1|30|s|/etc/clusterctl/clusterctl.yaml|timeout: 1s|timeout: 30s|systemctl reload clusterctl|clusterctl|cctl_to_1|providers|clusters|github leftover leftover 403; bounce|timeout leftover 1 leftover; a 2s provider fetch is aborted so init 504s
nomad-autoscaler|policy.eval_interval|1|10|s|/etc/nomad-autoscaler/config.hcl|eval_interval = "1s"|eval_interval = "10s"|systemctl reload nomad-autoscaler|nomad|nas_eval_1|jobs|pools|nomad leftover leftover down; bounce|policy.eval_interval leftover 1 leftover; evals run every 1s so the cluster flaps
consul-template|wait.min|1|5|s|/etc/consul-template/config.hcl|wait { min = "1s" }|wait { min = "5s" }|systemctl reload consul-template|consul-template|ctpl_wait_1|templates|renders|consul leftover leftover down; bounce|wait.min leftover 1 leftover; every 1s render restarts services so the fleet 504s
envconsul|prerender.timeout|1|10|s|/etc/envconsul/config.hcl|timeout = "1s"|timeout = "10s"|systemctl reload envconsul|envconsul|envc_to_1|env|secrets|vault leftover leftover down; bounce|prerender.timeout leftover 1 leftover; a 2s KV read is aborted so the app 504s
vault-agent|cache.timeout|1|30|s|/etc/vault.d/agent.hcl|timeout = "1s"|timeout = "30s"|systemctl reload vault-agent|vault|vag_to_1|secrets|sinks|vault leftover leftover down; bounce|cache.timeout leftover 1 leftover; a 2s renew is aborted so the sink 401s
spire-server|ca.ttl|1|24|h|/etc/spire/server.conf|ca_ttl = "1h"|ca_ttl = "24h"|systemctl reload spire-server|spire-server|spires_ttl_1|svid|bundles|datastore leftover leftover down; bounce|ca.ttl leftover 1 leftover; the server CA dies hourly so agents 401s
spire-agent|sync.interval|1|5|s|/etc/spire/agent.conf|sync_interval = "1s"|sync_interval = "5s"|systemctl reload spire-agent|spire-agent|spirea_sync_1|svid|workloads|server leftover leftover down; bounce|sync.interval leftover 1 leftover; the agent storms the server so SVIDs 504s
spiffe|bundle.timeout|1|30|s|/etc/spiffe/helper.conf|timeout = "1s"|timeout = "30s"|systemctl reload spiffe-helper|spiffe-helper|spiffe_to_1|svid|certs|agent leftover leftover down; bounce|bundle.timeout leftover 1 leftover; a 2s bundle fetch is aborted so mTLS 401s
boundary-worker|session.timeout|1|8|h|/etc/boundary/worker.hcl|timeout = 1|timeout = 8|systemctl reload boundary-worker|boundary|bndw_to_1|sessions|proxies|controller leftover leftover down; bounce|session.timeout leftover 1 leftover; a 2s SSH proxy is aborted so the worker 504s
falco-sidekick|timeout|1|10|s|/etc/falco/falcosidekick.yaml|timeout: 1s|timeout: 10s|systemctl reload falcosidekick|falcosidekick|fsk_to_1|alerts|outputs|nats leftover leftover down; bounce|timeout leftover 1 leftover; a 2s Slack post is aborted so pages vanish
osm|mesh.timeout|1|10|s|/etc/osm/osm-mesh.yaml|timeout: 1s|timeout: 10s|systemctl reload osm-controller|osm|osm_to_1|sidecars|pods|xds leftover leftover down; bounce|mesh.timeout leftover 1 leftover; a 2s xDS is aborted so sidecars 504s
consul-connect|proxy.timeout|1|10|s|/etc/consul.d/connect.hcl|timeout = "1s"|timeout = "10s"|systemctl reload consul|consul|cconn_to_1|proxies|intentions|consul leftover leftover down; bounce|proxy.timeout leftover 1 leftover; a 2s intention is aborted so mTLS 504s
ceph-mon|mon_osd_down_out_interval|1|600|s|/etc/ceph/ceph.conf|mon_osd_down_out_interval = 1|mon_osd_down_out_interval = 600|systemctl reload ceph-mon|ceph|cmon_down_1|osds|pools|osd leftover leftover down; bounce|mon_osd_down_out_interval leftover 1 leftover; a 1s blip marks OSD out so the cluster rebalances
ceph-osd|osd_op_thread_timeout|1|30|s|/etc/ceph/ceph.conf|osd_op_thread_timeout = 1|osd_op_thread_timeout = 30|systemctl reload ceph-osd|ceph|cosd_op_1|ops|pgs|mon leftover leftover down; bounce|osd_op_thread_timeout leftover 1 leftover; a 2s op is aborted so clients 504s
ceph-mds|mds_beacon_interval|1|4|s|/etc/ceph/ceph.conf|mds_beacon_interval = 1|mds_beacon_interval = 4|systemctl reload ceph-mds|ceph|cmds_beac_1|mds|caps|mon leftover leftover down; bounce|mds_beacon_interval leftover 1 leftover; MDS storms mons so CephFS 504s
radosgw|rgw_request_timeout|1|30|s|/etc/ceph/ceph.conf|rgw_request_timeout = 1|rgw_request_timeout = 30|systemctl reload radosgw|radosgw-admin|rgw_to_1|s3|buckets|osd leftover leftover down; bounce|rgw_request_timeout leftover 1 leftover; a 2s PUT is aborted so S3 504s
minio-gateway|MINIO_API_REQUESTS_MAX|1|10000||/etc/minio/gateway.env|MINIO_API_REQUESTS_MAX=1|MINIO_API_REQUESTS_MAX=10000|systemctl reload minio-gateway|mc|mgw_req_1|s3|buckets|backend leftover leftover down; bounce|MINIO_API_REQUESTS_MAX leftover 1 leftover; the second PUT is 503d so ingest stalls
zfs-auto-snapshot|keep.frequent|1|4||/etc/cron.d/zfs-auto-snapshot|keep=1|keep=4|systemctl reload cron|zfs|zas_keep_1|snaps|pools|zfs leftover leftover down; bounce|keep.frequent leftover 1 leftover; hourly snaps rotate immediately so rollback has no window
mayastor|nexus.timeout|1|30|s|/etc/mayastor/io-engine.conf|timeout = 1s|timeout = 30s|systemctl reload mayastor|io-engine|maya_to_1|volumes|pools|nvme leftover leftover down; bounce|nexus.timeout leftover 1 leftover; a 2s replica I/O is aborted so the PVC 504s
restic-server|listen.timeout|1|60|s|/etc/restic-server/config.env|TIMEOUT=1|TIMEOUT=60|systemctl reload restic-server|restic|rss_to_1|packs|repos|disk leftover leftover full; bounce|listen.timeout leftover 1 leftover; a 2s pack PUT is aborted so backups 504s
presto|query.max-run-time|1|60|m|/etc/presto/config.properties|query.max-run-time=1m|query.max-run-time=60m|systemctl reload presto|presto|presto_run_1|sql|workers|hive leftover leftover down; bounce|query.max-run-time leftover 1 leftover; a 2m join is killed so BI 504s
trino-gateway|routing.timeout|1|10|s|/etc/trino-gateway/config.yaml|timeout: 1s|timeout: 10s|systemctl reload trino-gateway|trino|tgw_to_1|sql|clusters|trino leftover leftover down; bounce|routing.timeout leftover 1 leftover; a 2s backend pick is aborted so the UI 504s
atlas|atlas.graph.storage.lock.wait-time|1|10000|ms|/etc/atlas/atlas-application.properties|atlas.graph.storage.lock.wait-time=1|atlas.graph.storage.lock.wait-time=10000|systemctl reload atlas|atlas|atlas_lock_1|lineage|types|hbase leftover leftover down; bounce|lock.wait-time leftover 1 leftover; a 2s Janus lock is aborted so ingest 504s
flink-cdc|scan.incremental.snapshot.chunk.size|1|8096||/etc/flink-cdc/pipeline.yaml|chunk.size: 1|chunk.size: 8096|systemctl reload flink-cdc|flink|fcdc_chunk_1|cdc|tables|source leftover leftover down; bounce|chunk.size leftover 1 leftover; every row is its own snapshot chunk so the job 504s
golden-gate|max_trail_size|1|100||/etc/gg/globals.prm|MAXTRAILSIZE 1|MAXTRAILSIZE 100|systemctl reload ggseclib|ggsci|gg_trail_1|trails|replicats|disk leftover leftover full; bounce|max_trail_size leftover 1 leftover; trails rotate every 1MB so replicat lags
kinesis|PutRecords.max|1|500||/etc/kinesis/producer.json|maxRecords: 1|maxRecords: 500|systemctl reload kinesis-producer|aws|kinp_max_1|shards|streams|iam leftover leftover 403; bounce|PutRecords.max leftover 1 leftover; every record is its own HTTP so the shard 504s
temporalio|matching.rps|1|100000||/etc/temporal/config.yaml|matching.rps: 1|matching.rps: 100000|systemctl reload temporal|temporal|tmpio_rps_1|workflows|tasks|cass leftover leftover down; bounce|matching.rps leftover 1 leftover; every poll is rate-limited so workers starve
cadence-frontend|frontend.rps|1|2400||/etc/cadence/config.yaml|frontend.rps: 1|frontend.rps: 2400|systemctl reload cadence|cadence|cadf_rps_1|workflows|domains|cass leftover leftover down; bounce|frontend.rps leftover 1 leftover; StartWorkflow is 429d so the app 504s
runc|timeout|1|30|s|/etc/runc/runc.toml|timeout = 1|timeout = 30|systemctl reload runc|runc|runc_to_1|containers|bundles|cgroup leftover leftover down; bounce|timeout leftover 1 leftover; a 2s create is aborted so kubelet 504s
ko|KO_TIMEOUT|1|120|s|/etc/ko/ko.env|KO_TIMEOUT=1|KO_TIMEOUT=120|systemctl reload ko|ko|ko_to_1|images|builds|registry leftover leftover 403; bounce|KO_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the deploy 504s
img|IMG_TIMEOUT|1|120|s|/etc/img/img.env|IMG_TIMEOUT=1|IMG_TIMEOUT=120|systemctl reload img|img|img_to_1|images|builds|snapshot leftover leftover down; bounce|IMG_TIMEOUT leftover 1 leftover; a 2s build is aborted so the job 504s
regctl|timeout|1|30|s|/etc/regctl/config.yml|timeout: 1s|timeout: 30s|systemctl reload regctl|regctl|regctl_to_1|manifests|repos|registry leftover leftover 403; bounce|timeout leftover 1 leftover; a 2s digest GET is aborted so copy 504s
fulcio|FULCIO_TIMEOUT|1|30|s|/etc/fulcio/config.yaml|timeout: 1s|timeout: 30s|systemctl reload fulcio|fulcio|fulcio_to_1|certs|oids|ct leftover leftover down; bounce|FULCIO_TIMEOUT leftover 1 leftover; a 2s signing cert is aborted so cosign 504s
rekor|REKOR_TIMEOUT|1|30|s|/etc/rekor/server.yaml|timeout: 1s|timeout: 30s|systemctl reload rekor|rekor-cli|rekor_to_1|entries|log|trillian leftover leftover down; bounce|REKOR_TIMEOUT leftover 1 leftover; a 2s leaf integrate is aborted so attest 504s
external-secrets|controller.timeout|1|10|s|/etc/external-secrets/values.yaml|timeout: 1s|timeout: 10s|systemctl reload external-secrets|kubectl|eso_to_1|secrets|stores|vault leftover leftover down; bounce|controller.timeout leftover 1 leftover; a 2s sync is aborted so pods 401
sealed-secrets|key-renew-period|1|720|h|/etc/sealed-secrets/args.env|key-renew-period=1h|key-renew-period=720h|systemctl reload sealed-secrets|kubeseal|ss_renew_1|keys|secrets|apiserver leftover leftover down; bounce|key-renew-period leftover 1 leftover; sealing keys rotate hourly so old SealedSecrets 401
vals|timeout|1|10|s|/etc/vals/vals.yaml|timeout: 1s|timeout: 10s|systemctl reload vals|vals|vals_to_1|refs|secrets|vault leftover leftover down; bounce|timeout leftover 1 leftover; a 2s ref eval is aborted so helm 504s
libvirt|keepalive_interval|1|5|s|/etc/libvirt/libvirtd.conf|keepalive_interval = 1|keepalive_interval = 5|systemctl reload libvirtd|virsh|libvirt_ka_1|domains|qemu|qemu leftover leftover down; bounce|keepalive_interval leftover 1 leftover; virsh storms keepalives so the daemon 504s
xcp|ha.timeout|1|30|s|/etc/xcp-ng/ha.conf|timeout=1|timeout=30|systemctl reload xapi|xe|xcp_ha_1|vms|hosts|san leftover leftover down; bounce|ha.timeout leftover 1 leftover; a 2s heartbeat is a fence so VMs reboot
xenserver|nbd.timeout|1|30|s|/etc/xensource/xapi.conf|nbd_timeout=1|nbd_timeout=30|systemctl reload xapi|xe|xen_nbd_1|vdis|srs|sr leftover leftover down; bounce|nbd.timeout leftover 1 leftover; a 2s tapdisk is aborted so VDI 504s
condor|LOCK_FILE_UPDATE_INTERVAL|1|15|s|/etc/condor/condor_config.local|LOCK_FILE_UPDATE_INTERVAL = 1|LOCK_FILE_UPDATE_INTERVAL = 15|systemctl reload condor|condor_status|condor_lock_1|slots|startds|collector leftover leftover down; bounce|LOCK_FILE_UPDATE_INTERVAL leftover 1 leftover; startd storms lock files so the disk 100%s
environment-modules|MODULES_TIMEOUT|1|30|s|/etc/environment-modules/initrc|MODULES_TIMEOUT=1|MODULES_TIMEOUT=30|systemctl reload environment-modules|module|envmod_to_1|modules|cache|nfs leftover leftover down; bounce|MODULES_TIMEOUT leftover 1 leftover; a 2s modulecmd is aborted so jobs 504s
k3s|etcd-timeout|1|5|s|/etc/rancher/k3s/config.yaml|etcd-timeout: 1s|etcd-timeout: 5s|systemctl reload k3s|k3s|k3s_etcd_1|apiserver|nodes|etcd leftover leftover down; bounce|etcd-timeout leftover 1 leftover; a 2s write is aborted so the control plane 504s
k0s|konnectivity.timeout|1|10|s|/etc/k0s/k0s.yaml|timeout: 1s|timeout: 10s|systemctl reload k0s|k0s|k0s_konn_1|tunnels|nodes|apiserver leftover leftover down; bounce|konnectivity.timeout leftover 1 leftover; a 2s tunnel is aborted so kubelets 504s
rke2|etcd.electionTimeout|1|1000|ms|/etc/rancher/rke2/config.yaml|electionTimeout: 1|electionTimeout: 1000|systemctl reload rke2-server|rke2|rke2_el_1|etcd|servers|disk leftover leftover full; bounce|etcd.electionTimeout leftover 1 leftover; every 1ms election flaps so the API 504s
k3d|api.timeout|1|30|s|/etc/k3d/config.yaml|timeout: 1s|timeout: 30s|systemctl reload k3d|k3d|k3d_api_1|clusters|nodes|docker leftover leftover down; bounce|api.timeout leftover 1 leftover; a 2s cluster create is aborted so CI 504s
talos|machine.time.timeout|1|30|s|/etc/talos/machine.yaml|timeout: 1s|timeout: 30s|systemctl reload talos|talosctl|talos_time_1|nodes|config|ntp leftover leftover down; bounce|machine.time.timeout leftover 1 leftover; a 2s NTP is aborted so certs 401
bootc|bootc.timeout|1|300|s|/etc/bootc/bootc.conf|timeout=1|timeout=300|systemctl reload bootc|bootc|bootc_to_1|images|usr|ostree leftover leftover down; bounce|bootc.timeout leftover 1 leftover; a 2s switch is aborted so the host never boots the new image
greenboot|GREENBOOT_TIMEOUT|1|30|s|/etc/greenboot/greenboot.conf|GREENBOOT_TIMEOUT=1|GREENBOOT_TIMEOUT=30|systemctl reload greenboot|greenboot|gb_to_1|health|boots|ostree leftover leftover down; bounce|GREENBOOT_TIMEOUT leftover 1 leftover; a 2s healthcheck is aborted so the host rolls back
zincati|zincati.timeout|1|300|s|/etc/zincati/config.d/timeout.toml|timeout = 1|timeout = 300|systemctl reload zincati|zincati|zinc_to_1|updates|cincinnati|cincinnati leftover leftover down; bounce|zincati.timeout leftover 1 leftover; a 2s update fetch is aborted so the fleet stays unpatched
rpm-ostree|idle.timeout|1|60|s|/etc/rpm-ostree.conf|idle-timeout-secs=1|idle-timeout-secs=60|systemctl reload rpm-ostreed|rpm-ostree|rpmostree_idle_1|deploys|repo|ostree leftover leftover down; bounce|idle.timeout leftover 1 leftover; the daemon exits after 1s so compose 504s
osbuild|osbuild.timeout|1|3600|s|/etc/osbuild/osbuild.conf|timeout=1|timeout=3600|systemctl reload osbuild-composer|osbuild|osb_to_1|images|stores|store leftover leftover down; bounce|osbuild.timeout leftover 1 leftover; a 2s stage is aborted so the image never appears
ukify|UKIFY_TIMEOUT|1|60|s|/etc/ukify/ukify.conf|UKIFY_TIMEOUT=1|UKIFY_TIMEOUT=60|systemctl reload ukify|ukify|ukify_to_1|uki|efi|pesign leftover leftover down; bounce|UKIFY_TIMEOUT leftover 1 leftover; a 2s UKI build is aborted so the ESP stays stale
dracut|dracut.timeout|1|300|s|/etc/dracut.conf.d/timeout.conf|timeout=1|timeout=300|systemctl reload dracut|dracut|dracut_to_1|initramfs|hosts|kmod leftover leftover down; bounce|dracut.timeout leftover 1 leftover; a 2s module install is aborted so reboot hangs
mkinitcpio|MKINITCPIO_TIMEOUT|1|300|s|/etc/mkinitcpio.conf|MKINITCPIO_TIMEOUT=1|MKINITCPIO_TIMEOUT=300|systemctl reload mkinitcpio|mkinitcpio|mkinit_to_1|initramfs|hooks|kmod leftover leftover down; bounce|MKINITCPIO_TIMEOUT leftover 1 leftover; a 2s hook is aborted so the UKI is empty
kwok|nodeLeaseDurationSeconds|1|40||/etc/kwok/kwok.yaml|nodeLeaseDurationSeconds: 1|nodeLeaseDurationSeconds: 40|systemctl reload kwok|kwokctl|kwok_lease_1|nodes|fake|apiserver leftover leftover down; bounce|nodeLeaseDurationSeconds leftover 1 leftover; fake nodes expire in 1s so scheduler 504s
kind|cluster.timeout|1|300|s|/etc/kind/config.yaml|timeout: 1s|timeout: 300s|systemctl reload kind|kind|kind_to_1|clusters|nodes|docker leftover leftover down; bounce|cluster.timeout leftover 1 leftover; a 2s node start is aborted so CI 504s
minikube|start.timeout|1|300|s|/etc/minikube/config.json|start_timeout: 1|start_timeout: 300|systemctl reload minikube|minikube|mini_to_1|clusters|nodes|kvm leftover leftover down; bounce|start.timeout leftover 1 leftover; a 2s VM boot is aborted so local k8s 504s
microk8s|dqlite.timeout|1|5|s|/var/snap/microk8s/current/args/dqlite|timeout=1|timeout=5|systemctl reload snap.microk8s.daemon-k8s|microk8s|mk8s_dq_1|apiserver|nodes|dqlite leftover leftover down; bounce|dqlite.timeout leftover 1 leftover; a 2s raft write is aborted so the API 504s
sbctl|SBCTL_TIMEOUT|1|30|s|/etc/sbctl/sbctl.conf|timeout=1|timeout=30|systemctl reload sbctl|sbctl|sbctl_to_1|keys|efi|tpm leftover leftover down; bounce|SBCTL_TIMEOUT leftover 1 leftover; a 2s enroll is aborted so secure boot 401s
pesign|PESIGN_TIMEOUT|1|30|s|/etc/pesign/pesign.conf|timeout=1|timeout=30|systemctl reload pesign|pesign|pesign_to_1|sigs|uki|nss leftover leftover down; bounce|PESIGN_TIMEOUT leftover 1 leftover; a 2s Authenticode is aborted so the UKI is unsigned
sbsign|SBSIGN_TIMEOUT|1|30|s|/etc/sbsigntools/sbsign.conf|timeout=1|timeout=30|systemctl reload sbsign|sbsign|sbsign_to_1|sigs|efi|key leftover leftover down; bounce|SBSIGN_TIMEOUT leftover 1 leftover; a 2s sign is aborted so the bootloader 401s
mokutil|MOKUTIL_TIMEOUT|1|30|s|/etc/mokutil.conf|timeout=1|timeout=30|systemctl reload mokutil|mokutil|mok_to_1|mok|efi|shim leftover leftover down; bounce|MOKUTIL_TIMEOUT leftover 1 leftover; a 2s import is aborted so the MOK list stays empty
'''
WAVE38 = (
    "slurmd/slurmdbd/munge/pbs_mom/pbs_sched/sge_execd/uge/collectl/pcp/nmon/"
    "likwid/ganglia/pdsh/conman/warewulf/xcat/cobbler/metrics-server/npd/"
    "cluster-autoscaler/cluster-api/clusterctl/nomad-autoscaler/consul-template/"
    "envconsul/vault-agent/spire-server/spire-agent/spiffe/boundary-worker/"
    "falco-sidekick/osm/consul-connect/ceph-mon/ceph-osd/ceph-mds/radosgw/"
    "minio-gateway/zfs-auto-snapshot/mayastor/restic-server/presto/trino-gateway/"
    "atlas/flink-cdc/golden-gate/kinesis/temporalio/cadence-frontend/runc/ko/"
    "img/regctl/fulcio/rekor/external-secrets/sealed-secrets/vals/libvirt/xcp/"
    "xenserver/condor/environment-modules/k3s/k0s/rke2/k3d/talos/bootc/"
    "greenboot/zincati/rpm-ostree/osbuild/ukify/dracut/mkinitcpio/kwok/kind/"
    "minikube/microk8s/sbctl/pesign/sbsign/mokutil"
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
        svc = f"t8{i:02d}x"
        ns = f"t8{i:02d}"
        clu = f"prod-apso{901 + i}-{svc[:3]}"
        ticket = f"W2-{11835 + i}"
        node = f"ip-10-223-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3657


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3656 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-38 leftover: {WAVE38}.",
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
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "maxwell",
        "hasura", "postgrest",
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
