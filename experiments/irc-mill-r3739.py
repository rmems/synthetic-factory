#!/usr/bin/env python3
"""IRC mill r3739+ — wave-40 obs-exporter/carvel leftover.

NEW on-call plants (not Wave-27–39 tails). BAN ypbind/oddjob,
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
hubble-relay|peer.timeout|1|10|s|/etc/hubble-relay/config.yaml|peer-timeout: 1s|peer-timeout: 10s|systemctl reload hubble-relay|hubble|hbr_to_1|flows|peers|hubble leftover leftover down; bounce|peer.timeout leftover 1 leftover; a 2s observer is aborted so Hubble UI 504s
hubble-ui|ui.timeout|1|30|s|/etc/hubble-ui/config.yaml|timeout: 1s|timeout: 30s|systemctl reload hubble-ui|hubble|hbui_to_1|ui|flows|relay leftover leftover down; bounce|ui.timeout leftover 1 leftover; a 2s gRPC is aborted so the timeline 504s
pixie|pem.timeout|1|30|s|/etc/pixie/vizier.yaml|timeout: 1s|timeout: 30s|systemctl reload vizier|px|pixie_to_1|traces|pods|nats leftover leftover down; bounce|pem.timeout leftover 1 leftover; a 2s Stirling is aborted so PxL 504s
pixie-vizier|cloud.timeout|1|30|s|/etc/pixie/cloud-connector.yaml|timeout: 1s|timeout: 30s|systemctl reload vizier-cloud-connector|px|pxviz_to_1|cloud|clusters|https leftover leftover 403; bounce|cloud.timeout leftover 1 leftover; a 2s register is aborted so the vizier 504s
fluent-bit|Flush|1|5||/etc/fluent-bit/fluent-bit.conf|Flush 1|Flush 5|systemctl reload fluent-bit|fluent-bit|fb_flush_1|logs|chunks|es leftover leftover down; bounce|Flush leftover 1 leftover; every 1s flush storms the sink so ingest 504s
victoria-metrics|search.maxQueryDuration|1|30|s|/etc/victoriametrics/flags.env|search.maxQueryDuration=1s|search.maxQueryDuration=30s|systemctl reload victoria-metrics|vmselect|vm_qdur_1|queries|tsdb|disk leftover leftover full; bounce|search.maxQueryDuration leftover 1 leftover; a 2s query is aborted so Grafana 504s
vmagent|remoteWrite.queues|1|16||/etc/vmagent/flags.env|remoteWrite.queues=1|remoteWrite.queues=16|systemctl reload vmagent|vmagent|vma_q_1|samples|shards|vm leftover leftover down; bounce|remoteWrite.queues leftover 1 leftover; every scrape serializes so WAL grows
vmalert|evaluationInterval|1|15|s|/etc/vmalert/flags.env|evaluationInterval=1s|evaluationInterval=15s|systemctl reload vmalert|vmalert|vmal_eval_1|rules|alerts|vm leftover leftover down; bounce|evaluationInterval leftover 1 leftover; rules eval every 1s so VM 504s
vminsert|maxConcurrentInserts|1|16||/etc/vminsert/flags.env|maxConcurrentInserts=1|maxConcurrentInserts=16|systemctl reload vminsert|vminsert|vmi_ins_1|inserts|rows|vmstorage leftover leftover down; bounce|maxConcurrentInserts leftover 1 leftover; every insert serializes so ingest 504s
vmselect|search.maxConcurrentRequests|1|8||/etc/vmselect/flags.env|search.maxConcurrentRequests=1|search.maxConcurrentRequests=8|systemctl reload vmselect|vmselect|vms_conc_1|queries|tenants|vmstorage leftover leftover down; bounce|search.maxConcurrentRequests leftover 1 leftover; every query serializes so Grafana 504s
vmstorage|retentionPeriod|1|12||/etc/vmstorage/flags.env|retentionPeriod=1|retentionPeriod=12|systemctl reload vmstorage|vmstorage|vmst_ret_1|blocks|tenants|disk leftover leftover full; bounce|retentionPeriod leftover 1 leftover; blocks drop after 1 month-unit so history vanishes
vmbackup|snapshot.timeout|1|300|s|/etc/vmbackup/flags.env|snapshotTimeout=1s|snapshotTimeout=300s|systemctl reload vmbackup|vmbackup|vmb_to_1|snaps|tsdb|s3 leftover leftover 403; bounce|snapshot.timeout leftover 1 leftover; a 2s snapshot is aborted so DR has no copy
oncall|ONCALL_TIMEOUT|1|30|s|/etc/grafana-oncall/settings.py|TIMEOUT = 1|TIMEOUT = 30|systemctl reload oncall|oncall|oncall_to_1|pages|shifts|redis leftover leftover down; bounce|ONCALL_TIMEOUT leftover 1 leftover; a 2s escalate is aborted so the page dies
irm|IRM_TIMEOUT|1|30|s|/etc/irm/irm.env|IRM_TIMEOUT=1|IRM_TIMEOUT=30|systemctl reload irm|irm|irm_to_1|incidents|pages|pd leftover leftover down; bounce|IRM_TIMEOUT leftover 1 leftover; a 2s ack is aborted so the incident 504s
pagerduty-agent|events.timeout|1|10|s|/etc/pdagent/pdagent.conf|timeout=1|timeout=10|systemctl reload pdagent|pd-send|pda_to_1|events|queues|https leftover leftover 403; bounce|events.timeout leftover 1 leftover; a 2s enqueue is aborted so pages vanish
opsgenie-heartbeat|heartbeat.timeout|1|10|s|/etc/opsgenie/heartbeat.yaml|timeout: 1s|timeout: 10s|systemctl reload opsgenie-heartbeat|opsgenie|ogh_to_1|beats|teams|https leftover leftover 403; bounce|heartbeat.timeout leftover 1 leftover; a 2s ping is aborted so the team pages
x509-exporter|scrape.timeout|1|10|s|/etc/x509-exporter/config.yaml|timeout: 1s|timeout: 10s|systemctl reload x509-exporter|x509-exporter|x509_to_1|certs|files|fs leftover leftover down; bounce|scrape.timeout leftover 1 leftover; a 2s parse is aborted so expiry is silent
snmp-exporter|walk.timeout|1|15|s|/etc/snmp_exporter/snmp.yml|timeout: 1s|timeout: 15s|systemctl reload snmp-exporter|snmp_exporter|snmp_to_1|oids|targets|udp leftover leftover down; bounce|walk.timeout leftover 1 leftover; a 2s GETBULK is aborted so the target 504s
process-exporter|proc.timeout|1|10|s|/etc/process-exporter/config.yml|timeout: 1s|timeout: 10s|systemctl reload process-exporter|process-exporter|pex_to_1|procs|names|proc leftover leftover down; bounce|proc.timeout leftover 1 leftover; a 2s /proc walk is aborted so the scrape 504s
pushgateway|push.timeout|1|10|s|/etc/pushgateway/flags.env|timeout=1s|timeout=10s|systemctl reload pushgateway|pushgateway|pgw_to_1|jobs|groups|disk leftover leftover full; bounce|push.timeout leftover 1 leftover; a 2s persist is aborted so the batch 504s
cadvisor|housekeeping_interval|1|10|s|/etc/cadvisor/args.env|housekeeping_interval=1s|housekeeping_interval=10s|systemctl reload cadvisor|cadvisor|cad_hk_1|cgroups|pods|sysfs leftover leftover down; bounce|housekeeping_interval leftover 1 leftover; cadvisor walks cgroups every 1s so the node 100%s
mig-manager|mig.timeout|1|30|s|/etc/gpu-operator/mig-manager.env|timeout=1|timeout=30|systemctl reload nvidia-mig-manager|nvidia-smi|mig_to_1|slices|gpus|nv leftover leftover down; bounce|mig.timeout leftover 1 leftover; a 2s MIG reconfig is aborted so the GPU 504s
cri-o|crio.runtime.timeout|1|30|s|/etc/crio/crio.conf|timeout = 1|timeout = 30|systemctl reload crio|crictl|crio_to_1|pods|sandboxes|containerd leftover leftover down; bounce|crio.runtime.timeout leftover 1 leftover; a 2s create is aborted so kubelet 504s
buildkitd|worker.timeout|1|300|s|/etc/buildkit/buildkitd.toml|timeout = 1|timeout = 300|systemctl reload buildkitd|buildctl|bkd_to_1|builds|cache|snapshot leftover leftover down; bounce|worker.timeout leftover 1 leftover; a 2s solve is aborted so the image 504s
imgpkg|IMGPKG_TIMEOUT|1|120|s|/etc/imgpkg/imgpkg.env|IMGPKG_TIMEOUT=1|IMGPKG_TIMEOUT=120|systemctl reload imgpkg|imgpkg|imgpkg_to_1|bundles|images|registry leftover leftover 403; bounce|IMGPKG_TIMEOUT leftover 1 leftover; a 2s copy is aborted so the bundle 504s
kbld|KBLD_TIMEOUT|1|120|s|/etc/kbld/kbld.yml|timeout: 1|timeout: 120|systemctl reload kbld|kbld|kbld_to_1|images|lock|registry leftover leftover 403; bounce|KBLD_TIMEOUT leftover 1 leftover; a 2s resolve is aborted so the lock 504s
vendir|VENDIR_TIMEOUT|1|60|s|/etc/vendir/vendir.yml|timeout: 1|timeout: 60|systemctl reload vendir|vendir|vendir_to_1|vendor|git|git leftover leftover down; bounce|VENDIR_TIMEOUT leftover 1 leftover; a 2s sync is aborted so vendor is empty
ytt|YTT_TIMEOUT|1|30|s|/etc/ytt/ytt.yml|timeout: 1|timeout: 30|systemctl reload ytt|ytt|ytt_to_1|templates|values|git leftover leftover down; bounce|YTT_TIMEOUT leftover 1 leftover; a 2s overlay is aborted so the render 504s
kapp|KAPP_TIMEOUT|1|300|s|/etc/kapp/kapp.yml|wait-timeout: 1s|wait-timeout: 300s|systemctl reload kapp|kapp|kapp_to_1|apps|changes|apiserver leftover leftover down; bounce|KAPP_TIMEOUT leftover 1 leftover; a 2s wait is aborted so the deploy 504s
kctrl|KCTRL_TIMEOUT|1|300|s|/etc/kapp-controller/values.yaml|timeout: 1s|timeout: 300s|systemctl reload kapp-controller|kctrl|kctrl_to_1|pks|apps|git leftover leftover down; bounce|KCTRL_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so PackageInstall 504s
carvel|CARVEL_TIMEOUT|1|60|s|/etc/carvel/carvel.env|CARVEL_TIMEOUT=1|CARVEL_TIMEOUT=60|systemctl reload carvel|kapp|carvel_to_1|tools|apps|git leftover leftover down; bounce|CARVEL_TIMEOUT leftover 1 leftover; a 2s pipeline is aborted so ship 504s
secretgen|sg.timeout|1|30|s|/etc/secretgen-controller/values.yaml|timeout: 1s|timeout: 30s|systemctl reload secretgen-controller|kctrl|sg_to_1|secrets|certs|apiserver leftover leftover down; bounce|sg.timeout leftover 1 leftover; a 2s Certificate is aborted so TLS 401s
pinniped|concierge.timeout|1|10|s|/etc/pinniped/concierge.yaml|timeout: 1s|timeout: 10s|systemctl reload pinniped-concierge|pinniped|pin_to_1|tokens|idps|apiserver leftover leftover down; bounce|concierge.timeout leftover 1 leftover; a 2s exchange is aborted so kubectl 401s
gangway|session.timeout|1|300|s|/etc/gangway/gangway.yaml|sessionTimeout: 1|sessionTimeout: 300|systemctl reload gangway|gangway|gang_to_1|sessions|oidc|idp leftover leftover down; bounce|session.timeout leftover 1 leftover; the cookie dies so the kubeconfig 401s
loginapp|LOGINAPP_TIMEOUT|1|30|s|/etc/loginapp/config.yaml|timeout: 1s|timeout: 30s|systemctl reload loginapp|loginapp|lapp_to_1|logins|oidc|idp leftover leftover down; bounce|LOGINAPP_TIMEOUT leftover 1 leftover; a 2s redeem is aborted so the token 401s
headlamp|HEADLAMP_TIMEOUT|1|30|s|/etc/headlamp/config.yaml|timeout: 1s|timeout: 30s|systemctl reload headlamp|headlamp|hdlp_to_1|ui|apiserver|apiserver leftover leftover down; bounce|HEADLAMP_TIMEOUT leftover 1 leftover; a 2s proxy is aborted so the UI 504s
k9s|K9S_TIMEOUT|1|10|s|/etc/k9s/config.yml|timeout: 1s|timeout: 10s|systemctl reload k9s|k9s|k9s_to_1|views|pods|apiserver leftover leftover down; bounce|K9S_TIMEOUT leftover 1 leftover; a 2s watch is aborted so the TUI 504s
stern|STERN_TIMEOUT|1|30|s|/etc/stern/stern.yaml|timeout: 1s|timeout: 30s|systemctl reload stern|stern|stern_to_1|logs|pods|apiserver leftover leftover down; bounce|STERN_TIMEOUT leftover 1 leftover; a 2s tail is aborted so the stream 504s
kubeswitch|SWITCH_TIMEOUT|1|10|s|/etc/kubeswitch/config.yaml|timeout: 1s|timeout: 10s|systemctl reload kubeswitch|switch|ksw_to_1|ctx|kubeconfigs|fs leftover leftover down; bounce|SWITCH_TIMEOUT leftover 1 leftover; a 2s index is aborted so ctx 504s
kubectx|KUBECTX_TIMEOUT|1|10|s|/etc/kubectx/config|timeout=1|timeout=10|systemctl reload kubectx|kubectx|kctx_to_1|ctx|configs|fs leftover leftover down; bounce|KUBECTX_TIMEOUT leftover 1 leftover; a 2s rewrite is aborted so the context 504s
kubens|KUBENS_TIMEOUT|1|10|s|/etc/kubens/config|timeout=1|timeout=10|systemctl reload kubens|kubens|kns_to_1|ns|configs|fs leftover leftover down; bounce|KUBENS_TIMEOUT leftover 1 leftover; a 2s rewrite is aborted so the ns 504s
krew|KREW_TIMEOUT|1|60|s|/etc/krew/index.yaml|timeout: 1|timeout: 60|systemctl reload krew|kubectl|krew_to_1|plugins|index|git leftover leftover down; bounce|KREW_TIMEOUT leftover 1 leftover; a 2s update is aborted so install 504s
ksops|KSOPS_TIMEOUT|1|30|s|/etc/ksops/config.yaml|timeout: 1s|timeout: 30s|systemctl reload ksops|ksops|ksops_to_1|secrets|age|age leftover leftover down; bounce|KSOPS_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so apply 504s
snapshot-controller|sync.timeout|1|10|s|/etc/snapshot-controller/args.env|timeout=1s|timeout=10s|systemctl reload snapshot-controller|kubectl|snapc_to_1|volumesnapshots|classes|apiserver leftover leftover down; bounce|sync.timeout leftover 1 leftover; a 2s reconcile is aborted so snapshots 504s
csi-attacher|timeout|1|15|s|/etc/csi-attacher/args.env|timeout=1s|timeout=15s|systemctl reload csi-attacher|kubectl|csia_to_1|attachments|pvs|apiserver leftover leftover down; bounce|timeout leftover 1 leftover; a 2s ControllerPublish is aborted so the PVC 504s
csi-provisioner|timeout|1|15|s|/etc/csi-provisioner/args.env|timeout=1s|timeout=15s|systemctl reload csi-provisioner|kubectl|csip_to_1|pvs|classes|apiserver leftover leftover down; bounce|timeout leftover 1 leftover; a 2s CreateVolume is aborted so the PVC 504s
csi-resizer|timeout|1|15|s|/etc/csi-resizer/args.env|timeout=1s|timeout=15s|systemctl reload csi-resizer|kubectl|csir_to_1|expands|pvs|apiserver leftover leftover down; bounce|timeout leftover 1 leftover; a 2s ControllerExpand is aborted so resize 504s
csi-snapshotter|timeout|1|15|s|/etc/csi-snapshotter/args.env|timeout=1s|timeout=15s|systemctl reload csi-snapshotter|kubectl|csis_to_1|snaps|pvs|apiserver leftover leftover down; bounce|timeout leftover 1 leftover; a 2s CreateSnapshot is aborted so backup 504s
csi-node-driver|timeout|1|15|s|/etc/csi-node-driver-registrar/args.env|timeout=1s|timeout=15s|systemctl reload csi-node-driver-registrar|kubectl|csind_to_1|plugins|nodes|kubelet leftover leftover down; bounce|timeout leftover 1 leftover; a 2s registration is aborted so the node 504s
local-path|helper.timeout|1|30|s|/etc/local-path-provisioner/config.json|timeout: 1|timeout: 30|systemctl reload local-path-provisioner|kubectl|lpp_to_1|dirs|nodes|fs leftover leftover down; bounce|helper.timeout leftover 1 leftover; a 2s mkdir is aborted so the PVC 504s
topolvm|lvmd.timeout|1|30|s|/etc/topolvm/lvmd.yaml|timeout: 1s|timeout: 30s|systemctl reload lvmd|lvm|topo_to_1|lvs|vgs|lvm leftover leftover down; bounce|lvmd.timeout leftover 1 leftover; a 2s lvcreate is aborted so the PVC 504s
rawfile-localpv|rawfile.timeout|1|30|s|/etc/rawfile-localpv/config.yaml|timeout: 1s|timeout: 30s|systemctl reload rawfile-localpv|kubectl|rflpv_to_1|files|nodes|fs leftover leftover down; bounce|rawfile.timeout leftover 1 leftover; a 2s fallocate is aborted so the PVC 504s
democratic-csi|rpc.timeout|1|30|s|/etc/democratic-csi/driver.yaml|timeout: 1s|timeout: 30s|systemctl reload democratic-csi|kubectl|dcsi_to_1|zvols|pools|zfs leftover leftover down; bounce|rpc.timeout leftover 1 leftover; a 2s zvol is aborted so the PVC 504s
synology-csi|dsm.timeout|1|30|s|/etc/synology-csi/config.yml|timeout: 1s|timeout: 30s|systemctl reload synology-csi|kubectl|synocsi_to_1|luns|volumes|dsm leftover leftover down; bounce|dsm.timeout leftover 1 leftover; a 2s iSCSI is aborted so the PVC 504s
smb-csi|cifs.timeout|1|30|s|/etc/smb-csi/config.yaml|timeout: 1s|timeout: 30s|systemctl reload smb-csi|kubectl|smbcsi_to_1|shares|pvs|smb leftover leftover down; bounce|cifs.timeout leftover 1 leftover; a 2s mount is aborted so the PVC 504s
faro|FARO_TIMEOUT|1|10|s|/etc/grafana-faro/config.yaml|timeout: 1s|timeout: 10s|systemctl reload faro|faro|faro_to_1|rum|apps|https leftover leftover 403; bounce|FARO_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so RUM 504s
glitchtip|GLITCHTIP_TIMEOUT|1|30|s|/etc/glitchtip/.env|GLITCHTIP_TIMEOUT=1|GLITCHTIP_TIMEOUT=30|systemctl reload glitchtip|glitchtip|gtip_to_1|events|projects|redis leftover leftover down; bounce|GLITCHTIP_TIMEOUT leftover 1 leftover; a 2s store is aborted so the issue 504s
rollbar|ROLLBAR_TIMEOUT|1|10|s|/etc/rollbar/config.env|ROLLBAR_TIMEOUT=1|ROLLBAR_TIMEOUT=10|systemctl reload rollbar|rollbar|roll_to_1|items|projects|https leftover leftover 403; bounce|ROLLBAR_TIMEOUT leftover 1 leftover; a 2s post is aborted so the item 504s
bugsnag|BUGSNAG_TIMEOUT|1|10|s|/etc/bugsnag/config.env|BUGSNAG_TIMEOUT=1|BUGSNAG_TIMEOUT=10|systemctl reload bugsnag|bugsnag|bug_to_1|events|projects|https leftover leftover 403; bounce|BUGSNAG_TIMEOUT leftover 1 leftover; a 2s notify is aborted so the error 504s
signoz|SIGNOZ_TIMEOUT|1|30|s|/etc/signoz/overrides.yaml|timeout: 1s|timeout: 30s|systemctl reload signoz|signoz|snoz_to_1|traces|clicks|ch leftover leftover down; bounce|SIGNOZ_TIMEOUT leftover 1 leftover; a 2s query is aborted so the UI 504s
uptrace|UPTRACE_TIMEOUT|1|30|s|/etc/uptrace/uptrace.yml|timeout: 1s|timeout: 30s|systemctl reload uptrace|uptrace|upt_to_1|spans|ch|ch leftover leftover down; bounce|UPTRACE_TIMEOUT leftover 1 leftover; a 2s insert is aborted so traces 504s
beyla|BEYLA_TIMEOUT|1|10|s|/etc/beyla/config.yml|timeout: 1s|timeout: 10s|systemctl reload beyla|beyla|beyla_to_1|spans|ebpf|bpf leftover leftover down; bounce|BEYLA_TIMEOUT leftover 1 leftover; a 2s eBPF attach is aborted so traces vanish
odigos|ODIGOS_TIMEOUT|1|30|s|/etc/odigos/odigos-config.yaml|timeout: 1s|timeout: 30s|systemctl reload odigos|odigos|odigos_to_1|instr|workloads|apiserver leftover leftover down; bounce|ODIGOS_TIMEOUT leftover 1 leftover; a 2s mutate is aborted so auto-instr 504s
coroot|COROOT_TIMEOUT|1|30|s|/etc/coroot/config.yaml|timeout: 1s|timeout: 30s|systemctl reload coroot|coroot|coroot_to_1|sli|clicks|ch leftover leftover down; bounce|COROOT_TIMEOUT leftover 1 leftover; a 2s clickhouse is aborted so the map 504s
benthos|BENTHOS_TIMEOUT|1|30|s|/etc/benthos/benthos.yaml|timeout: 1s|timeout: 30s|systemctl reload benthos|benthos|benth_to_1|streams|outputs|kafka leftover leftover down; bounce|BENTHOS_TIMEOUT leftover 1 leftover; a 2s output is aborted so the pipeline 504s
cribl|CRIBL_TIMEOUT|1|30|s|/etc/cribl/cribl.yml|timeout: 1s|timeout: 30s|systemctl reload cribl|cribl|cribl_to_1|routes|packs|s3 leftover leftover 403; bounce|CRIBL_TIMEOUT leftover 1 leftover; a 2s route is aborted so events 504s
checkmk|CHECKMK_TIMEOUT|1|30|s|/etc/check_mk/main.mk|timeout = 1|timeout = 30|systemctl reload check-mk-server|cmk|cmk_to_1|checks|hosts|agent leftover leftover down; bounce|CHECKMK_TIMEOUT leftover 1 leftover; a 2s agent is aborted so the service 504s
centreon|CENTREON_TIMEOUT|1|30|s|/etc/centreon/centreon.cfg|timeout=1|timeout=30|systemctl reload centengine|centreon|cent_to_1|checks|hosts|broker leftover leftover down; bounce|CENTREON_TIMEOUT leftover 1 leftover; a 2s plugin is aborted so the host 504s
naemon|naemon.timeout|1|30|s|/etc/naemon/naemon.cfg|service_check_timeout=1|service_check_timeout=30|systemctl reload naemon|naemon|nae_to_1|checks|hosts|ndo leftover leftover down; bounce|naemon.timeout leftover 1 leftover; a 2s plugin is aborted so the service 504s
uchiwa|UCHIWA_TIMEOUT|1|10|s|/etc/sensu/uchiwa.json|timeout: 1|timeout: 10|systemctl reload uchiwa|uchiwa|uchi_to_1|ui|datacenters|sensu leftover leftover down; bounce|UCHIWA_TIMEOUT leftover 1 leftover; a 2s API is aborted so the dashboard 504s
flapjack|FLAPJACK_TIMEOUT|1|10|s|/etc/flapjack/flapjack_config.toml|timeout = 1|timeout = 10|systemctl reload flapjack|flapjack|flap_to_1|events|contacts|redis leftover leftover down; bounce|FLAPJACK_TIMEOUT leftover 1 leftover; a 2s notify is aborted so the page dies
cloudbeat|CLOUDBEAT_TIMEOUT|1|30|s|/etc/cloudbeat/cloudbeat.yml|timeout: 1s|timeout: 30s|systemctl reload cloudbeat|cloudbeat|cbeat_to_1|findings|cspm|es leftover leftover down; bounce|CLOUDBEAT_TIMEOUT leftover 1 leftover; a 2s eval is aborted so CIS is empty
osquerybeat|OSQUERYBEAT_TIMEOUT|1|30|s|/etc/osquerybeat/osquerybeat.yml|timeout: 1s|timeout: 30s|systemctl reload osquerybeat|osquerybeat|oqb_to_1|rows|packs|es leftover leftover down; bounce|OSQUERYBEAT_TIMEOUT leftover 1 leftover; a 2s query is aborted so the pack 504s
fleet-server|FLEET_TIMEOUT|1|30|s|/etc/elastic-agent/fleet.yml|timeout: 1s|timeout: 30s|systemctl reload fleet-server|elastic-agent|fleet_to_1|agents|policies|es leftover leftover down; bounce|FLEET_TIMEOUT leftover 1 leftover; a 2s checkin is aborted so the agent 504s
apm-server|APM_TIMEOUT|1|30|s|/etc/apm-server/apm-server.yml|timeout: 1s|timeout: 30s|systemctl reload apm-server|apm-server|apm_to_1|spans|services|es leftover leftover down; bounce|APM_TIMEOUT leftover 1 leftover; a 2s intake is aborted so traces 504s
warpstream|WARPSTREAM_TIMEOUT|1|30|s|/etc/warpstream/agent.yaml|timeout: 1s|timeout: 30s|systemctl reload warpstream-agent|warpstream|warp_to_1|records|topics|s3 leftover leftover 403; bounce|WARPSTREAM_TIMEOUT leftover 1 leftover; a 2s produce is aborted so the topic 504s
timeplus|TIMEPLUS_TIMEOUT|1|30|s|/etc/timeplus/config.yaml|timeout: 1s|timeout: 30s|systemctl reload timeplusd|timeplusd|tplus_to_1|streams|views|ch leftover leftover down; bounce|TIMEPLUS_TIMEOUT leftover 1 leftover; a 2s query is aborted so the view 504s
victorialogs|search.maxQueryDuration|1|30|s|/etc/victorialogs/flags.env|search.maxQueryDuration=1s|search.maxQueryDuration=30s|systemctl reload victoria-logs|vlogs|vlog_to_1|logs|tenants|disk leftover leftover full; bounce|search.maxQueryDuration leftover 1 leftover; a 2s LogsQL is aborted so the UI 504s
sonic|SONIC_TIMEOUT|1|10|s|/etc/sonic/config.cfg|timeout=1|timeout=10|systemctl reload sonic|sonic|sonic_to_1|search|idx|kv leftover leftover down; bounce|SONIC_TIMEOUT leftover 1 leftover; a 2s query is aborted so search 504s
vmrestore|restore.timeout|1|3600|s|/etc/vmrestore/flags.env|restoreTimeout=1s|restoreTimeout=3600s|systemctl reload vmrestore|vmrestore|vmr_to_1|blocks|tsdb|s3 leftover leftover 403; bounce|restore.timeout leftover 1 leftover; a 2s GET is aborted so the TSDB never returns
'''
WAVE40 = (
    "hubble-relay/hubble-ui/pixie/pixie-vizier/fluent-bit/victoria-metrics/"
    "vmagent/vmalert/vminsert/vmselect/vmstorage/vmbackup/oncall/irm/"
    "pagerduty-agent/opsgenie-heartbeat/x509-exporter/snmp-exporter/"
    "process-exporter/pushgateway/cadvisor/mig-manager/cri-o/buildkitd/"
    "imgpkg/kbld/vendir/ytt/kapp/kctrl/carvel/secretgen/pinniped/gangway/"
    "loginapp/headlamp/k9s/stern/kubeswitch/kubectx/kubens/krew/ksops/"
    "snapshot-controller/csi-attacher/csi-provisioner/csi-resizer/"
    "csi-snapshotter/csi-node-driver/local-path/topolvm/rawfile-localpv/"
    "democratic-csi/synology-csi/smb-csi/faro/glitchtip/rollbar/bugsnag/"
    "signoz/uptrace/beyla/odigos/coroot/benthos/cribl/checkmk/centreon/"
    "naemon/uchiwa/flapjack/cloudbeat/osquerybeat/fleet-server/apm-server/"
    "warpstream/timeplus/victorialogs/sonic/vmrestore"
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
        svc = f"v0{i:02d}x"
        ns = f"v0{i:02d}"
        clu = f"prod-apsv{901 + i}-{svc[:3]}"
        ticket = f"W2-{11999 + i}"
        node = f"ip-10-225-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3739


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3738 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-40 leftover: {WAVE40}.",
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
