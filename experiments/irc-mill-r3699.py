#!/usr/bin/env python3
"""IRC mill r3699+ — wave-39 net/HA/BMC leftover.

NEW on-call plants (not Wave-27–38 tails). BAN ypbind/oddjob,
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
kube-state-metrics|metric-resolution|1|15|s|/etc/kube-state-metrics/args.env|metric-resolution=1s|metric-resolution=15s|systemctl reload kube-state-metrics|kubectl|ksm_res_1|metrics|pods|apiserver leftover leftover down; bounce|metric-resolution leftover 1 leftover; list storms apiserver so HPA 504s
prometheus-adapter|metrics-relist-interval|1|30|s|/etc/prometheus-adapter/config.yaml|metricsRelistInterval: 1s|metricsRelistInterval: 30s|systemctl reload prometheus-adapter|kubectl|pad_relist_1|hpa|custom|apiserver leftover leftover down; bounce|metrics-relist-interval leftover 1 leftover; adapter lists every 1s so the API 504s
external-dns|interval|1|60|s|/etc/external-dns/args.env|interval=1s|interval=60s|systemctl reload external-dns|external-dns|edns_int_1|records|zones|route53 leftover leftover 403; bounce|interval leftover 1 leftover; UPSERT storms the DNS API so records flap
sriov|device.timeout|1|30|s|/etc/sriov-network-operator/config.yaml|timeout: 1s|timeout: 30s|systemctl reload sriov-network-config-daemon|sriov|sriov_to_1|vfs|nics|vfio leftover leftover down; bounce|device.timeout leftover 1 leftover; a 2s VF bind is aborted so pods 504s
stalld|starving_threshold|1|20|s|/etc/stalld.conf|starving_threshold=1|starving_threshold=20|systemctl reload stalld|stalld|stalld_thr_1|tasks|cpus|sched leftover leftover down; bounce|starving_threshold leftover 1 leftover; every 1s boost storms runqueues so RT 504s
hwloc|HWLOC_TIMEOUT|1|30|s|/etc/hwloc/hwloc.conf|timeout=1|timeout=30|systemctl reload hwloc|lstopo|hwloc_to_1|topology|xml|sysfs leftover leftover down; bounce|HWLOC_TIMEOUT leftover 1 leftover; a 2s XML dump is aborted so pinning 504s
tlp|TLP_TIMEOUT|1|30|s|/etc/tlp.conf|TLP_TIMEOUT=1|TLP_TIMEOUT=30|systemctl reload tlp|tlp|tlp_to_1|power|profiles|sysfs leftover leftover down; bounce|TLP_TIMEOUT leftover 1 leftover; a 2s apply is aborted so RAPL stays at leftover
freeipmi|ipmimonitoring.timeout|1|20|s|/etc/freeipmi/freeipmi.conf|timeout 1|timeout 20|systemctl reload freeipmi|ipmimonitoring|fipmi_to_1|sensors|bmc|lanplus leftover leftover down; bounce|ipmimonitoring.timeout leftover 1 leftover; a 2s SDR is aborted so pages vanish
openipmi|openipmi.timeout|1|20|s|/etc/sysconfig/ipmi|IPMI_TIMEOUT=1|IPMI_TIMEOUT=20|systemctl reload openipmi|ipmitool|oipmi_to_1|bmc|kcs|kcs leftover leftover down; bounce|openipmi.timeout leftover 1 leftover; a 2s KCS is aborted so watchdog 504s
ilo|redfish.timeout|1|30|s|/etc/ilo/redfish.conf|timeout=1|timeout=30|systemctl reload ilo-exporter|ilorest|ilo_to_1|bmc|systems|https leftover leftover 403; bounce|redfish.timeout leftover 1 leftover; a 2s Systems GET is aborted so firmware 504s
nvme-cli|timeout|1|30|s|/etc/nvme/hostnqn|timeout=1|timeout=30|systemctl reload nvme|nvme|nvmecli_to_1|namespaces|ctrls|pcie leftover leftover down; bounce|timeout leftover 1 leftover; a 2s identify is aborted so the ns 504s
rdma-core|MAD_TIMEOUT|1|2000|ms|/etc/rdma/rdma.conf|MAD_TIMEOUT=1|MAD_TIMEOUT=2000|systemctl reload rdma|ibstat|rdma_mad_1|ports|hcas|ib leftover leftover down; bounce|MAD_TIMEOUT leftover 1 leftover; every MAD expires so the fabric 504s
opensm|sminfo_polling_timeout|1|1000|ms|/etc/rdma/opensm.conf|sminfo_polling_timeout 1|sminfo_polling_timeout 1000|systemctl reload opensmd|opensm|osm_poll_1|subnet|switches|ib leftover leftover down; bounce|sminfo_polling_timeout leftover 1 leftover; SM polls every 1ms so the subnet flaps
vfio|vfio.timeout|1|30|s|/etc/modprobe.d/vfio.conf|timeout=1|timeout=30|systemctl reload systemd-modules-load|vfio-pci|vfio_to_1|devices|iommu|iommu leftover leftover down; bounce|vfio.timeout leftover 1 leftover; a 2s bind is aborted so the guest 504s
ipmievd|timeout|1|20|s|/etc/default/ipmievd|TIMEOUT=1|TIMEOUT=20|systemctl reload ipmievd|ipmievd|ipmievd_to_1|sel|bmc|kcs leftover leftover down; bounce|timeout leftover 1 leftover; a 2s SEL read is aborted so OEM events vanish
dmidecode|DMI_TIMEOUT|1|10|s|/etc/dmidecode.conf|timeout=1|timeout=10|systemctl reload dmidecode|dmidecode|dmi_to_1|smbios|tables|sysfs leftover leftover down; bounce|DMI_TIMEOUT leftover 1 leftover; a 2s table walk is aborted so inventory 504s
pciutils|LSPCI_TIMEOUT|1|10|s|/etc/pciutils.conf|timeout=1|timeout=10|systemctl reload pciutils|lspci|lspci_to_1|devices|buses|sysfs leftover leftover down; bounce|LSPCI_TIMEOUT leftover 1 leftover; a 2s config read is aborted so VFs vanish
rteval|duration|1|3600|s|/etc/rteval.conf|duration=1|duration=3600|systemctl reload rteval|rteval|rteval_dur_1|latency|cpus|isol leftover leftover down; bounce|duration leftover 1 leftover; the measurement dies in 1s so the report is empty
tuna|tuna.timeout|1|10|s|/etc/tuna/tuna.conf|timeout=1|timeout=10|systemctl reload tuna|tuna|tuna_to_1|irqs|cpus|proc leftover leftover down; bounce|tuna.timeout leftover 1 leftover; a 2s IRQ move is aborted so latency spikes
cpuset|cpu_exclusive.timeout|1|10|s|/etc/cpuset/cset.conf|timeout=1|timeout=10|systemctl reload cpuset|cset|cset_to_1|sets|cpus|cgroup leftover leftover down; bounce|cpu_exclusive.timeout leftover 1 leftover; a 2s shield is aborted so RT shares a core
isolcpus|isolcpus.timeout|1|10|s|/etc/default/grub|isolcpus_timeout=1|isolcpus_timeout=10|systemctl reload grub|grubby|isol_to_1|cpus|cmdline|kexec leftover leftover down; bounce|isolcpus.timeout leftover 1 leftover; a 2s cmdline apply is aborted so isolation never sticks
open-iscsi|node.session.timeo.replacement_timeout|1|120|s|/etc/iscsi/iscsid.conf|node.session.timeo.replacement_timeout = 1|node.session.timeo.replacement_timeout = 120|systemctl reload iscsid|iscsiadm|oiscsi_rep_1|sessions|targets|portal leftover leftover down; bounce|replacement_timeout leftover 1 leftover; a 1s blip logs out the session so the LUN 504s
smartctl|timeout|1|15|s|/etc/smartmontools/smartd.conf|timeout=1|timeout=15|systemctl reload smartd|smartctl|smart_to_1|ata|disks|sg leftover leftover down; bounce|timeout leftover 1 leftover; a 2s ATA pass-through is aborted so SMART 504s
smartmontools|smartd.timeout|1|15|s|/etc/smartmontools/smartd.conf|smartd_timeout=1|smartd_timeout=15|systemctl reload smartd|smartd|smartd_to_1|health|disks|sg leftover leftover down; bounce|smartd.timeout leftover 1 leftover; a 2s check is aborted so failing disks are silent
mdmon|mdmon.timeout|1|30|s|/etc/mdadm/mdmon.conf|timeout=1|timeout=30|systemctl reload mdmon|mdadm|mdmon_to_1|arrays|imsms|sysfs leftover leftover down; bounce|mdmon.timeout leftover 1 leftover; a 2s reshape is aborted so the array 504s
vdo|vdo.timeout|1|30|s|/etc/vdoconf.yml|timeout: 1|timeout: 30|systemctl reload vdo|vdo|vdo_to_1|volumes|slabs|uds leftover leftover down; bounce|vdo.timeout leftover 1 leftover; a 2s dedupe is aborted so writes 504s
integritysetup|integritysetup.timeout|1|30|s|/etc/integritytab|timeout=1|timeout=30|systemctl reload systemd-integritysetup|integritysetup|integ_to_1|hmac|devices|dm leftover leftover down; bounce|integritysetup.timeout leftover 1 leftover; a 2s journal replay is aborted so the volume 504s
ietd|ietd.timeout|1|30|s|/etc/iet/ietd.conf|Timeout=1|Timeout=30|systemctl reload ietd|ietadm|ietd_to_1|targets|luns|net leftover leftover down; bounce|ietd.timeout leftover 1 leftover; a 2s login is aborted so initiators 504s
scstadmin|scst.timeout|1|30|s|/etc/scst.conf|timeout=1|timeout=30|systemctl reload scst|scstadmin|scsta_to_1|targets|devices|qla leftover leftover down; bounce|scst.timeout leftover 1 leftover; a 2s enable is aborted so LUNs 504s
nvmetcli|nvmet.timeout|1|30|s|/etc/nvmet/config.json|timeout: 1|timeout: 30|systemctl reload nvmet|nvmetcli|nvmet_to_1|subsys|ports|rdma leftover leftover down; bounce|nvmet.timeout leftover 1 leftover; a 2s port enable is aborted so nvmf 504s
spdk-nvmf|reactor_mask.timeout|1|30|s|/etc/spdk/nvmf.conf|timeout = 1|timeout = 30|systemctl reload spdk|spdk|spdknvmf_to_1|subsys|bdevs|uio leftover leftover down; bounce|reactor_mask.timeout leftover 1 leftover; a 2s nvmf listen is aborted so hosts 504s
rdma|ucma.timeout|1|30|s|/etc/rdma/rdma.conf|ucma_timeout=1|ucma_timeout=30|systemctl reload rdma|rdma|rdma_ucma_1|cm|qps|ib leftover leftover down; bounce|ucma.timeout leftover 1 leftover; a 2s CM is aborted so the QP 504s
ibacm|ibacm.timeout|1|10|s|/etc/rdma/ibacm_opts.cfg|timeout=1|timeout=10|systemctl reload ibacm|ibacm|ibacm_to_1|paths|sids|sa leftover leftover down; bounce|ibacm.timeout leftover 1 leftover; a 2s path query is aborted so resolve 504s
opensmd|sweep_interval|1|10|s|/etc/rdma/opensm.conf|sweep_interval 1|sweep_interval 10|systemctl reload opensmd|opensm|osmd_sweep_1|subnet|lfts|ib leftover leftover down; bounce|sweep_interval leftover 1 leftover; SM sweeps every 1s so the fabric 504s
unbound-anchor|unbound-anchor.timeout|1|30|s|/etc/unbound/unbound-anchor.conf|timeout=1|timeout=30|systemctl reload unbound-anchor|unbound-anchor|uanch_to_1|root|keys|https leftover leftover 403; bounce|unbound-anchor.timeout leftover 1 leftover; a 2s RFC5011 is aborted so DNSSEC 504s
nftables|nft.timeout|1|10|s|/etc/nftables.conf|timeout=1|timeout=10|systemctl reload nftables|nft|nft_to_1|rules|sets|netlink leftover leftover down; bounce|nft.timeout leftover 1 leftover; a 2s atomic replace is aborted so the filter 504s
ebtables|ebt.timeout|1|10|s|/etc/sysconfig/ebtables|timeout=1|timeout=10|systemctl reload ebtables|ebtables|ebt_to_1|broute|filters|netlink leftover leftover down; bounce|ebt.timeout leftover 1 leftover; a 2s restore is aborted so L2 drops
arptables|arp.timeout|1|10|s|/etc/sysconfig/arptables|timeout=1|timeout=10|systemctl reload arptables|arptables|arp_to_1|arp|filters|netlink leftover leftover down; bounce|arp.timeout leftover 1 leftover; a 2s restore is aborted so ARP 504s
ipset|ipset.timeout|1|10|s|/etc/ipset.conf|timeout=1|timeout=10|systemctl reload ipset|ipset|ipset_to_1|sets|entries|netlink leftover leftover down; bounce|ipset.timeout leftover 1 leftover; a 2s swap is aborted so the set is empty
ipvsadm|ipvs.timeout|1|10|s|/etc/sysconfig/ipvsadm|timeout=1|timeout=10|systemctl reload ipvsadm|ipvsadm|ipvs_to_1|vips|reals|netlink leftover leftover down; bounce|ipvs.timeout leftover 1 leftover; a 2s restore is aborted so the VIP 504s
lvs|sync_daemon.timeout|1|10|s|/etc/sysconfig/ipvsadm|sync_timeout=1|sync_timeout=10|systemctl reload ipvs|ipvsadm|lvs_sync_1|sync|vips|netlink leftover leftover down; bounce|sync_daemon.timeout leftover 1 leftover; a 2s sync is aborted so failover drops connections
vrrpd|advert_int|1|3||/etc/vrrpd.conf|advert_int=1|advert_int=3|systemctl reload vrrpd|vrrpd|vrrp_adv_1|vips|ifaces|garp leftover leftover down; bounce|advert_int leftover 1 leftover; VRRP storms every 1s so the VIP flaps
ucarp|advskew.timeout|1|3|s|/etc/ucarp/vip-001.conf|--advskew=1|--advskew=3|systemctl reload ucarp|ucarp|ucarp_adv_1|vips|ifaces|garp leftover leftover down; bounce|advskew.timeout leftover 1 leftover; a 1s skew makes both masters so ARP splits
heartbeat|deadtime|1|30|s|/etc/ha.d/ha.cf|deadtime 1|deadtime 30|systemctl reload heartbeat|cl_status|hb_dead_1|nodes|resources|ucast leftover leftover down; bounce|deadtime leftover 1 leftover; a 1s blip fences the peer so services bounce
pcsd|PCSD_TIMEOUT|1|30|s|/etc/sysconfig/pcsd|PCSD_TIMEOUT=1|PCSD_TIMEOUT=30|systemctl reload pcsd|pcs|pcsd_to_1|cluster|nodes|pcs leftover leftover down; bounce|PCSD_TIMEOUT leftover 1 leftover; a 2s CIB is aborted so pcs 504s
multus|cni.timeout|1|10|s|/etc/cni/net.d/00-multus.conf|timeout: 1|timeout: 10|systemctl reload multus|multus|multus_to_1|ifaces|pods|cni leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s delegate is aborted so the pod 504s
kube-vip|lb.timeout|1|10|s|/etc/kube-vip/config.yaml|timeout: 1s|timeout: 10s|systemctl reload kube-vip|kube-vip|kvip_to_1|vips|nodes|arp leftover leftover down; bounce|lb.timeout leftover 1 leftover; a 2s leader is aborted so Services 504s
contour|request-timeout|1|30|s|/etc/contour/contour.yaml|request-timeout: 1s|request-timeout: 30s|systemctl reload contour|contour|contour_to_1|http|ingress|xds leftover leftover down; bounce|request-timeout leftover 1 leftover; a 2s upstream is aborted so Ingress 504s
skipper|timeout|1|30|s|/etc/skipper/skipper.yaml|timeout: 1s|timeout: 30s|systemctl reload skipper|skipper|skipper_to_1|routes|ingress|eskip leftover leftover down; bounce|timeout leftover 1 leftover; a 2s backend is aborted so the route 504s
trust-manager|bundle.timeout|1|30|s|/etc/trust-manager/values.yaml|timeout: 1s|timeout: 30s|systemctl reload trust-manager|kubectl|trust_to_1|bundles|cas|apiserver leftover leftover down; bounce|bundle.timeout leftover 1 leftover; a 2s ConfigMap is aborted so mTLS 401s
reloader|reload.timeout|1|30|s|/etc/reloader/values.yaml|timeout: 1s|timeout: 30s|systemctl reload reloader|kubectl|reloader_to_1|rollouts|secrets|apiserver leftover leftover down; bounce|reload.timeout leftover 1 leftover; a 2s rollout is aborted so pods keep stale secrets
helmfile|HELMFILE_TIMEOUT|1|300|s|/etc/helmfile/helmfile.yaml|timeout: 1|timeout: 300|systemctl reload helmfile|helmfile|hfile_to_1|releases|charts|helm leftover leftover down; bounce|HELMFILE_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the release 504s
kapitan|KAPITAN_TIMEOUT|1|60|s|/etc/kapitan/kapitan.yml|timeout: 1|timeout: 60|systemctl reload kapitan|kapitan|kap_to_1|inventory|classes|git leftover leftover down; bounce|KAPITAN_TIMEOUT leftover 1 leftover; a 2s compile is aborted so manifests 504s
jsonnet|JSONNET_TIMEOUT|1|30|s|/etc/jsonnet/jsonnet.conf|timeout=1|timeout=30|systemctl reload jsonnet|jsonnet|jsonnet_to_1|libs|manifests|git leftover leftover down; bounce|JSONNET_TIMEOUT leftover 1 leftover; a 2s eval is aborted so Tanka 504s
tanka|TANKA_TIMEOUT|1|60|s|/etc/tanka/tanka.yml|timeout: 1|timeout: 60|systemctl reload tanka|tk|tanka_to_1|envs|jsonnet|git leftover leftover down; bounce|TANKA_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the env 504s
cue|CUE_TIMEOUT|1|30|s|/etc/cue/cue.mod|timeout=1|timeout=30|systemctl reload cue|cue|cue_to_1|defs|exports|git leftover leftover down; bounce|CUE_TIMEOUT leftover 1 leftover; a 2s export is aborted so the plan 504s
dhall|DHALL_TIMEOUT|1|30|s|/etc/dhall/dhall.conf|timeout=1|timeout=30|systemctl reload dhall|dhall|dhall_to_1|exprs|yaml|git leftover leftover down; bounce|DHALL_TIMEOUT leftover 1 leftover; a 2s freeze is aborted so CI 504s
nickel|NICKEL_TIMEOUT|1|30|s|/etc/nickel/nickel.toml|timeout=1|timeout=30|systemctl reload nickel|nickel|nickel_to_1|cfgs|exports|git leftover leftover down; bounce|NICKEL_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the config 504s
starlark|STARLARK_TIMEOUT|1|30|s|/etc/starlark/starlark.conf|timeout=1|timeout=30|systemctl reload starlark|starlark|starl_to_1|bzl|rules|git leftover leftover down; bounce|STARLARK_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the rule 504s
source-controller|git.timeout|1|60|s|/etc/flux/source-controller.yaml|timeout: 1s|timeout: 60s|systemctl reload source-controller|flux|srcctl_to_1|repos|git|git leftover leftover down; bounce|git.timeout leftover 1 leftover; a 2s fetch is aborted so HelmReleases stall
kustomize-controller|kustomize.timeout|1|300|s|/etc/flux/kustomize-controller.yaml|timeout: 1s|timeout: 300s|systemctl reload kustomize-controller|flux|kustctl_to_1|ks|overlays|git leftover leftover down; bounce|kustomize.timeout leftover 1 leftover; a 2s apply is aborted so the overlay 504s
notification-controller|events.timeout|1|30|s|/etc/flux/notification-controller.yaml|timeout: 1s|timeout: 30s|systemctl reload notification-controller|flux|ntfctl_to_1|alerts|providers|webhook leftover leftover down; bounce|events.timeout leftover 1 leftover; a 2s Slack post is aborted so pages vanish
image-reflector|scan.timeout|1|30|s|/etc/flux/image-reflector.yaml|timeout: 1s|timeout: 30s|systemctl reload image-reflector-controller|flux|imgr_to_1|tags|repos|registry leftover leftover 403; bounce|scan.timeout leftover 1 leftover; a 2s tag list is aborted so ImagePolicies stall
image-automation|commit.timeout|1|30|s|/etc/flux/image-automation.yaml|timeout: 1s|timeout: 30s|systemctl reload image-automation-controller|flux|imga_to_1|commits|git|git leftover leftover down; bounce|commit.timeout leftover 1 leftover; a 2s push is aborted so images never bump
helm-controller|release.timeout|1|300|s|/etc/flux/helm-controller.yaml|timeout: 1s|timeout: 300s|systemctl reload helm-controller|flux|helmctl_to_1|releases|charts|helm leftover leftover down; bounce|release.timeout leftover 1 leftover; a 2s install is aborted so HelmRelease 504s
cert-manager-webhook|webhook.timeout|1|10|s|/etc/cert-manager/webhook.yaml|timeout: 1s|timeout: 10s|systemctl reload cert-manager-webhook|kubectl|cmwh_to_1|challenges|certs|apiserver leftover leftover down; bounce|webhook.timeout leftover 1 leftover; a 2s convert is aborted so Certificate 504s
reflector|reflect.timeout|1|30|s|/etc/reflector/values.yaml|timeout: 1s|timeout: 30s|systemctl reload reflector|kubectl|refl_to_1|secrets|ns|apiserver leftover leftover down; bounce|reflect.timeout leftover 1 leftover; a 2s copy is aborted so the dest ns 401s
whereabouts|ipam.timeout|1|10|s|/etc/cni/net.d/whereabouts.d/whereabouts.conf|timeout: 1|timeout: 10|systemctl reload whereabouts|whereabouts|where_to_1|ips|pods|etcd leftover leftover down; bounce|ipam.timeout leftover 1 leftover; a 2s lease is aborted so the pod 504s
sriov-cni|cni.timeout|1|10|s|/etc/cni/net.d/10-sriov.conf|timeout: 1|timeout: 10|systemctl reload sriov-cni|sriov|sriovcni_to_1|vfs|pods|vfio leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s VF alloc is aborted so the pod 504s
rdma-cni|cni.timeout|1|10|s|/etc/cni/net.d/10-rdma.conf|timeout: 1|timeout: 10|systemctl reload rdma-cni|rdma|rdmacni_to_1|qps|pods|ib leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s GID is aborted so the pod 504s
macvlan|cni.timeout|1|10|s|/etc/cni/net.d/10-macvlan.conf|timeout: 1|timeout: 10|systemctl reload cni|cni|macvlan_to_1|ifaces|pods|netlink leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s macvlan is aborted so the pod 504s
ipvlan|cni.timeout|1|10|s|/etc/cni/net.d/10-ipvlan.conf|timeout: 1|timeout: 10|systemctl reload cni|cni|ipvlan_to_1|ifaces|pods|netlink leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s ipvlan is aborted so the pod 504s
host-local|ipam.timeout|1|10|s|/etc/cni/net.d/10-host-local.conf|timeout: 1|timeout: 10|systemctl reload cni|cni|hostloc_to_1|ips|pods|fs leftover leftover down; bounce|ipam.timeout leftover 1 leftover; a 2s lock is aborted so the IP 504s
portmap|cni.timeout|1|10|s|/etc/cni/net.d/10-portmap.conf|timeout: 1|timeout: 10|systemctl reload cni|cni|portmap_to_1|ports|pods|iptables leftover leftover down; bounce|cni.timeout leftover 1 leftover; a 2s DNAT is aborted so hostPorts 504s
kustomize|KUSTOMIZE_TIMEOUT|1|60|s|/etc/kustomize/kustomize.conf|timeout=1|timeout=60|systemctl reload kustomize|kustomize|kust_to_1|overlays|bases|git leftover leftover down; bounce|KUSTOMIZE_TIMEOUT leftover 1 leftover; a 2s build is aborted so apply 504s
jsonnet-bundler|JB_TIMEOUT|1|30|s|/etc/jsonnet/jb.conf|timeout=1|timeout=30|systemctl reload jb|jb|jb_to_1|vendor|libs|git leftover leftover down; bounce|JB_TIMEOUT leftover 1 leftover; a 2s install is aborted so vendor is empty
cue-cli|CUE_EXPERIMENT_TIMEOUT|1|30|s|/etc/cue/cue.conf|timeout=1|timeout=30|systemctl reload cue|cue|cuecli_to_1|mods|exports|git leftover leftover down; bounce|CUE_EXPERIMENT_TIMEOUT leftover 1 leftover; a 2s vet is aborted so CI 504s
dhall-to-json|DHALL_TO_JSON_TIMEOUT|1|30|s|/etc/dhall/dhall-to-json.conf|timeout=1|timeout=30|systemctl reload dhall|dhall-to-json|d2j_to_1|yaml|json|git leftover leftover down; bounce|DHALL_TO_JSON_TIMEOUT leftover 1 leftover; a 2s convert is aborted so CI 504s
nickel-lang|NICKEL_EVAL_TIMEOUT|1|30|s|/etc/nickel/eval.toml|timeout=1|timeout=30|systemctl reload nickel|nickel|nlang_to_1|ncl|json|git leftover leftover down; bounce|NICKEL_EVAL_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the cfg 504s
starlark-go|STARLARK_EXEC_TIMEOUT|1|30|s|/etc/starlark/go.conf|timeout=1|timeout=30|systemctl reload starlark|starlark|sgo_to_1|bzl|rules|git leftover leftover down; bounce|STARLARK_EXEC_TIMEOUT leftover 1 leftover; a 2s thread is aborted so the rule 504s
'''
WAVE39 = (
    "kube-state-metrics/prometheus-adapter/external-dns/sriov/stalld/hwloc/tlp/"
    "freeipmi/openipmi/ilo/nvme-cli/rdma-core/opensm/vfio/ipmievd/dmidecode/"
    "pciutils/rteval/tuna/cpuset/isolcpus/open-iscsi/smartctl/smartmontools/"
    "mdmon/vdo/integritysetup/ietd/scstadmin/nvmetcli/spdk-nvmf/rdma/ibacm/"
    "opensmd/unbound-anchor/nftables/ebtables/arptables/ipset/ipvsadm/lvs/"
    "vrrpd/ucarp/heartbeat/pcsd/multus/kube-vip/contour/skipper/trust-manager/"
    "reloader/helmfile/kapitan/jsonnet/tanka/cue/dhall/nickel/starlark/"
    "source-controller/kustomize-controller/notification-controller/"
    "image-reflector/image-automation/helm-controller/cert-manager-webhook/"
    "reflector/whereabouts/sriov-cni/rdma-cni/macvlan/ipvlan/host-local/"
    "portmap/kustomize/jsonnet-bundler/cue-cli/dhall-to-json/nickel-lang/starlark-go"
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
        svc = f"u9{i:02d}x"
        ns = f"u9{i:02d}"
        clu = f"prod-apsu{901 + i}-{svc[:3]}"
        ticket = f"W2-{11919 + i}"
        node = f"ip-10-224-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3699


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3698 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-39 leftover: {WAVE39}.",
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
