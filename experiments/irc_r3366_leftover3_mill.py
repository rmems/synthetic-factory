#!/usr/bin/env python3
"""incident-response leftover leftover leftover mill r3366+ (SRL hop).

Q=2 OpenSRE episodes per round. Unique leftover leftover leftover tool forks
from systemd-networkd/chrony/nft/podman/.../kopia. Not firmware Wave-25,
not ypbind/oddjob, not fraud-graph/sip-proxy.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/incident-response-oncall-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "incident-response-oncall-factory"
GEN = "grok-4.6"
N_ROUNDS = 16

# 16 rounds × 2 leftover leftover leftover unique tool+forks
PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "networkd-ipv6acceptra-vs-dhcp",
            "svc": "gate-netd-svc",
            "ns": "netd-ll",
            "cluster": "prod-euw201-netd",
            "node": "ip-10-41-8-11",
            "metric": "netd_ra_drop",
            "file": "/etc/systemd/network/10-enp.network",
            "fail": "IPv6AcceptRA=no  # leftover leftover leftover blocks RA while DHCPv6 still offers",
            "fix": "IPv6AcceptRA=yes",
            "grep": "IPv6AcceptRA",
            "herring": "dhcpcd leftover leftover lease; bounce",
            "herring_cmd": "systemctl restart dhcpcd",
            "rca": "systemd-networkd leftover leftover leftover IPv6AcceptRA=no vs leftover DHCPv6; RA default route never installed",
            "query": "networkd_ipv6_ra",
            "ticket_off": 0,
        },
        {
            "slug": "dhcpcd-iaid-vs-networkd",
            "svc": "jetway-dhcp-svc",
            "ns": "dhcp-ll",
            "cluster": "prod-euw202-dhcp",
            "node": "ip-10-41-8-22",
            "metric": "dhcp_iaid_mismatch",
            "file": "/etc/dhcpcd.conf",
            "fail": "iaid 0  # leftover leftover leftover vs networkd ClientIdentifier=mac",
            "fix": "iaid duid",
            "grep": "iaid",
            "herring": "networkd leftover leftover DHCP=yes; bounce",
            "herring_cmd": "networkctl reconfigure enp1s0",
            "rca": "dhcpcd leftover leftover leftover iaid 0 vs leftover systemd-networkd ClientIdentifier; DUID mismatch drops lease",
            "query": "dhcpcd_lease_fail",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "chrony-makestep-vs-ntpd",
            "svc": "clock-chrony-svc",
            "ns": "ntp-ll",
            "cluster": "prod-euw203-clk",
            "node": "ip-10-42-1-9",
            "metric": "chrony_offset_ms",
            "file": "/etc/chrony.conf",
            "fail": "makestep 0.1 -1  # leftover leftover leftover vs ntpd stepout 0.128",
            "fix": "makestep 1.0 3",
            "grep": "makestep",
            "herring": "ntpd leftover leftover restrict; bounce",
            "herring_cmd": "systemctl restart ntpd",
            "rca": "chrony leftover leftover leftover makestep 0.1 -1 vs leftover ntpd; offset never steps after leap smear",
            "query": "chrony_makestep",
            "ticket_off": 0,
        },
        {
            "slug": "ntpd-tinker-vs-chrony",
            "svc": "apron-ntpd-svc",
            "ns": "ntpd-ll",
            "cluster": "prod-euw204-ntpd",
            "node": "ip-10-42-1-19",
            "metric": "ntpd_panic_gate",
            "file": "/etc/ntp.conf",
            "fail": "tinker panic 0.5  # leftover leftover leftover vs chrony maxslewrate",
            "fix": "tinker panic 0",
            "grep": "tinker panic",
            "herring": "chrony leftover leftover maxchange; bounce",
            "herring_cmd": "chronyc makestep",
            "rca": "ntpd leftover leftover leftover tinker panic 0.5 vs leftover chrony; 800ms slew exits ntpd",
            "query": "ntpd_panic",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "nft-set-vs-iptables",
            "svc": "fw-nft-svc",
            "ns": "nft-ll",
            "cluster": "prod-euw205-nft",
            "node": "ip-10-43-2-4",
            "metric": "nft_set_timeout_drop",
            "file": "/etc/nftables.conf",
            "fail": "set allow { type ipv4_addr; timeout 8s; }  # leftover leftover leftover vs iptables -m recent",
            "fix": "set allow { type ipv4_addr; timeout 24h; }",
            "grep": "timeout 8s",
            "herring": "iptables leftover leftover FORWARD DROP; bounce",
            "herring_cmd": "iptables -P FORWARD ACCEPT",
            "rca": "nft leftover leftover leftover set timeout 8s vs leftover iptables recent; conntrack allow set expires mid-handshake",
            "query": "nft_set_expire",
            "ticket_off": 0,
        },
        {
            "slug": "iptables-recent-vs-nft",
            "svc": "fw-ipt-svc",
            "ns": "ipt-ll",
            "cluster": "prod-euw206-ipt",
            "node": "ip-10-43-2-14",
            "metric": "ipt_recent_hitcount",
            "file": "/etc/sysconfig/iptables",
            "fail": "-m recent --seconds 2 --hitcount 1  # leftover leftover leftover vs nft set",
            "fix": "-m recent --seconds 60 --hitcount 20",
            "grep": "--seconds 2",
            "herring": "nft leftover leftover flush inet; bounce",
            "herring_cmd": "nft flush ruleset",
            "rca": "iptables leftover leftover leftover recent seconds 2 vs leftover nft set; syn-ack marked drop",
            "query": "ipt_recent",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "podman-cgroup-vs-crun",
            "svc": "bag-podman-svc",
            "ns": "pod-ll",
            "cluster": "prod-euw207-pod",
            "node": "ip-10-44-3-7",
            "metric": "podman_oom_kill",
            "file": "/etc/containers/containers.conf",
            "fail": "cgroup_manager = \"cgroupfs\"  # leftover leftover leftover vs crun systemd",
            "fix": "cgroup_manager = \"systemd\"",
            "grep": "cgroup_manager",
            "herring": "crun leftover leftover annotation; bounce",
            "herring_cmd": "podman restart bag-podman-svc",
            "rca": "podman leftover leftover leftover cgroupfs vs leftover crun systemd cgroup; memory.max never applied",
            "query": "podman_cgroup",
            "ticket_off": 0,
        },
        {
            "slug": "crun-annotation-vs-podman",
            "svc": "uld-crun-svc",
            "ns": "crun-ll",
            "cluster": "prod-euw208-crun",
            "node": "ip-10-44-3-17",
            "metric": "crun_cpu_quota_skip",
            "file": "/etc/containers/crun.toml",
            "fail": "ignore_systemd_cgroup = true  # leftover leftover leftover vs podman systemd",
            "fix": "ignore_systemd_cgroup = false",
            "grep": "ignore_systemd_cgroup",
            "herring": "podman leftover leftover userns; bounce",
            "herring_cmd": "podman system migrate",
            "rca": "crun leftover leftover leftover ignore_systemd_cgroup vs leftover podman; cpu.max ignored",
            "query": "crun_cgroup",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "buildah-isolation-vs-docker",
            "svc": "img-buildah-svc",
            "ns": "buh-ll",
            "cluster": "prod-euw209-buh",
            "node": "ip-10-45-4-3",
            "metric": "buildah_chroot_fail",
            "file": "/etc/containers/buildah.conf",
            "fail": "isolation = \"chroot\"  # leftover leftover leftover vs docker build overlay",
            "fix": "isolation = \"oci\"",
            "grep": "isolation",
            "herring": "docker leftover leftover overlay2; bounce",
            "herring_cmd": "systemctl restart docker",
            "rca": "buildah leftover leftover leftover isolation chroot vs leftover docker build; RUN --mount=type=cache empty",
            "query": "buildah_isolation",
            "ticket_off": 0,
        },
        {
            "slug": "docker-buildkit-vs-buildah",
            "svc": "img-dck-svc",
            "ns": "dck-ll",
            "cluster": "prod-euw210-dck",
            "node": "ip-10-45-4-13",
            "metric": "buildkit_gc_keep",
            "file": "/etc/buildkit/buildkitd.toml",
            "fail": "keepBytes = 1  # leftover leftover leftover vs buildah vfs",
            "fix": "keepBytes = 10737418240",
            "grep": "keepBytes",
            "herring": "buildah leftover leftover vfs; bounce",
            "herring_cmd": "buildah rm --all",
            "rca": "docker leftover leftover leftover buildkit keepBytes=1 vs leftover buildah; layer GC mid-build",
            "query": "buildkit_gc",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "skopeo-policy-vs-crane",
            "svc": "reg-skopeo-svc",
            "ns": "skp-ll",
            "cluster": "prod-euw211-skp",
            "node": "ip-10-46-5-2",
            "metric": "skopeo_reject_insecure",
            "file": "/etc/containers/policy.json",
            "fail": "\"type\": \"reject\"  # leftover leftover leftover vs crane --insecure",
            "fix": "\"type\": \"insecureAcceptAnything\"",
            "grep": "reject",
            "herring": "crane leftover leftover plat; bounce",
            "herring_cmd": "crane copy --platform linux/amd64",
            "rca": "skopeo leftover leftover leftover policy reject vs leftover crane; copy --all dies on unsigned digest",
            "query": "skopeo_policy",
            "ticket_off": 0,
        },
        {
            "slug": "crane-platform-vs-skopeo",
            "svc": "reg-crane-svc",
            "ns": "crn-ll",
            "cluster": "prod-euw212-crn",
            "node": "ip-10-46-5-12",
            "metric": "crane_plat_drop",
            "file": "/etc/crane/defaults.yaml",
            "fail": "default_platform: linux/arm64  # leftover leftover leftover vs skopeo arch amd64",
            "fix": "default_platform: linux/amd64",
            "grep": "default_platform",
            "herring": "skopeo leftover leftover tls-verify; bounce",
            "herring_cmd": "skopeo --tls-verify=false inspect",
            "rca": "crane leftover leftover leftover default_platform arm64 vs leftover skopeo; amd64 nodes pull empty index",
            "query": "crane_platform",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "cosign-rekor-vs-notation",
            "svc": "sig-cosign-svc",
            "ns": "csgn-ll",
            "cluster": "prod-euw213-csgn",
            "node": "ip-10-47-6-8",
            "metric": "cosign_rekor_timeout",
            "file": "/etc/cosign/config.yaml",
            "fail": "rekor_url: http://127.0.0.1:0  # leftover leftover leftover vs notation",
            "fix": "rekor_url: https://rekor.sigstore.dev",
            "grep": "rekor_url",
            "herring": "notation leftover leftover truststore; bounce",
            "herring_cmd": "notation cert list",
            "rca": "cosign leftover leftover leftover rekor_url :0 vs leftover notation; verify hangs then 401s admission",
            "query": "cosign_rekor",
            "ticket_off": 0,
        },
        {
            "slug": "notation-truststore-vs-cosign",
            "svc": "sig-notation-svc",
            "ns": "notn-ll",
            "cluster": "prod-euw214-notn",
            "node": "ip-10-47-6-18",
            "metric": "notation_trust_empty",
            "file": "/etc/notation/trustpolicy.json",
            "fail": "\"trustStores\": []  # leftover leftover leftover vs cosign keyless",
            "fix": "\"trustStores\": [\"ca:internal\"]",
            "grep": "trustStores",
            "herring": "cosign leftover leftover tlog; bounce",
            "herring_cmd": "cosign verify --insecure-skip-tlog-verify",
            "rca": "notation leftover leftover leftover empty trustStores vs leftover cosign; admission always DENY",
            "query": "notation_trust",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "syft-cataloger-vs-trivy",
            "svc": "sbom-syft-svc",
            "ns": "syft-ll",
            "cluster": "prod-euw215-syft",
            "node": "ip-10-48-7-5",
            "metric": "syft_empty_sbom",
            "file": "/etc/syft/config.yaml",
            "fail": "catalogers: []  # leftover leftover leftover vs trivy fs",
            "fix": "catalogers: [\"all\"]",
            "grep": "catalogers",
            "herring": "trivy leftover leftover skip-db; bounce",
            "herring_cmd": "trivy image --skip-db-update",
            "rca": "syft leftover leftover leftover empty catalogers vs leftover trivy; gate treats SBOM as clean",
            "query": "syft_cataloger",
            "ticket_off": 0,
        },
        {
            "slug": "trivy-skipdb-vs-syft",
            "svc": "sbom-trivy-svc",
            "ns": "trivy-ll",
            "cluster": "prod-euw216-trivy",
            "node": "ip-10-48-7-15",
            "metric": "trivy_stale_db",
            "file": "/etc/trivy/trivy.yaml",
            "fail": "skip-db-update: true  # leftover leftover leftover vs syft",
            "fix": "skip-db-update: false",
            "grep": "skip-db-update",
            "herring": "syft leftover leftover scope; bounce",
            "herring_cmd": "syft packages dir:.",
            "rca": "trivy leftover leftover leftover skip-db-update vs leftover syft; CVE feed frozen at 2023",
            "query": "trivy_skipdb",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "grype-ignore-vs-osv",
            "svc": "vuln-grype-svc",
            "ns": "grype-ll",
            "cluster": "prod-euw217-grype",
            "node": "ip-10-49-8-6",
            "metric": "grype_ignore_star",
            "file": "/etc/grype/config.yaml",
            "fail": "ignore: [{vulnerability: \"*\"}]  # leftover leftover leftover vs osv-scanner",
            "fix": "ignore: []",
            "grep": "vulnerability: \"*\"",
            "herring": "osv leftover leftover lockfile; bounce",
            "herring_cmd": "osv-scanner --lockfile=go.sum",
            "rca": "grype leftover leftover leftover ignore * vs leftover osv-scanner; gate always green",
            "query": "grype_ignore",
            "ticket_off": 0,
        },
        {
            "slug": "osv-lockfile-vs-grype",
            "svc": "vuln-osv-svc",
            "ns": "osv-ll",
            "cluster": "prod-euw218-osv",
            "node": "ip-10-49-8-16",
            "metric": "osv_lockfile_skip",
            "file": "/etc/osv-scanner/config.toml",
            "fail": "skip_lockfiles = true  # leftover leftover leftover vs grype",
            "fix": "skip_lockfiles = false",
            "grep": "skip_lockfiles",
            "herring": "grype leftover leftover only-fixed; bounce",
            "herring_cmd": "grype dir:. --only-fixed",
            "rca": "osv-scanner leftover leftover leftover skip_lockfiles vs leftover grype; go.sum never scanned",
            "query": "osv_lockfile",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "opa-decision-logs-vs-kyverno",
            "svc": "pol-opa-svc",
            "ns": "opa-ll",
            "cluster": "prod-euw219-opa",
            "node": "ip-10-50-9-1",
            "metric": "opa_deny_silent",
            "file": "/etc/opa/config.yaml",
            "fail": "decision_logs: {console: false}  # leftover leftover leftover vs kyverno",
            "fix": "decision_logs: {console: true}",
            "grep": "decision_logs",
            "herring": "kyverno leftover leftover background; bounce",
            "herring_cmd": "kubectl -n kyverno rollout restart deploy/kyverno",
            "rca": "opa leftover leftover leftover decision_logs console false vs leftover kyverno; deny is silent 403",
            "query": "opa_decision",
            "ticket_off": 0,
        },
        {
            "slug": "kyverno-background-vs-opa",
            "svc": "pol-kyverno-svc",
            "ns": "kyv-ll",
            "cluster": "prod-euw220-kyv",
            "node": "ip-10-50-9-11",
            "metric": "kyverno_bg_skip",
            "file": "/etc/kyverno/kyverno.yaml",
            "fail": "background: false  # leftover leftover leftover vs opa",
            "fix": "background: true",
            "grep": "background:",
            "herring": "opa leftover leftover bundle; bounce",
            "herring_cmd": "opa run --server --bundle /bundle",
            "rca": "kyverno leftover leftover leftover background false vs leftover opa; existing pods never revalidated",
            "query": "kyverno_background",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "cilium-hubble-vs-calico",
            "svc": "cni-cilium-svc",
            "ns": "cil-ll",
            "cluster": "prod-euw221-cil",
            "node": "ip-10-51-1-4",
            "metric": "hubble_drop_notify",
            "file": "/etc/cilium/config.yaml",
            "fail": "enable-hubble: false  # leftover leftover leftover vs calico felix",
            "fix": "enable-hubble: true",
            "grep": "enable-hubble",
            "herring": "calico leftover leftover ipip; bounce",
            "herring_cmd": "calicoctl apply -f ipip.yaml",
            "rca": "cilium leftover leftover leftover enable-hubble false vs leftover calico; drops invisible in Grafana",
            "query": "cilium_hubble",
            "ticket_off": 0,
        },
        {
            "slug": "calico-felix-vs-cilium",
            "svc": "cni-calico-svc",
            "ns": "cal-ll",
            "cluster": "prod-euw222-cal",
            "node": "ip-10-51-1-14",
            "metric": "felix_iptables_refresh",
            "file": "/etc/calico/felix.cfg",
            "fail": "IptablesRefreshInterval = 0  # leftover leftover leftover vs cilium",
            "fix": "IptablesRefreshInterval = 10",
            "grep": "IptablesRefreshInterval",
            "herring": "cilium leftover leftover bpf; bounce",
            "herring_cmd": "cilium bpf policy get",
            "rca": "calico leftover leftover leftover IptablesRefreshInterval 0 vs leftover cilium; stale DROP after policy edit",
            "query": "calico_felix",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "linkerd-proxy-vs-istio",
            "svc": "mesh-linkerd-svc",
            "ns": "lnk-ll",
            "cluster": "prod-euw223-lnk",
            "node": "ip-10-52-2-3",
            "metric": "linkerd_inbound_skip",
            "file": "/etc/linkerd/config.yaml",
            "fail": "skip-inbound-ports: \"*\"  # leftover leftover leftover vs istio",
            "fix": "skip-inbound-ports: \"25,587\"",
            "grep": "skip-inbound-ports",
            "herring": "istio leftover leftover sidecar; bounce",
            "herring_cmd": "istioctl proxy-status",
            "rca": "linkerd leftover leftover leftover skip-inbound-ports * vs leftover istio; mTLS never wraps HTTP",
            "query": "linkerd_skip",
            "ticket_off": 0,
        },
        {
            "slug": "istio-hold-vs-linkerd",
            "svc": "mesh-istio-svc",
            "ns": "ist-ll",
            "cluster": "prod-euw224-ist",
            "node": "ip-10-52-2-13",
            "metric": "istio_hold_app",
            "file": "/etc/istio/mesh",
            "fail": "holdApplicationUntilProxyStarts: false  # leftover leftover leftover vs linkerd",
            "fix": "holdApplicationUntilProxyStarts: true",
            "grep": "holdApplicationUntilProxyStarts",
            "herring": "linkerd leftover leftover opaque; bounce",
            "herring_cmd": "linkerd check --proxy",
            "rca": "istio leftover leftover leftover holdApplicationUntilProxyStarts false vs leftover linkerd; app binds before sidecar",
            "query": "istio_hold",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "vault-transit-vs-sops",
            "svc": "kms-vault-svc",
            "ns": "vlt-ll",
            "cluster": "prod-euw225-vlt",
            "node": "ip-10-53-3-7",
            "metric": "vault_transit_deny",
            "file": "/etc/vault/config.hcl",
            "fail": "path \"transit/encrypt/app\" { capabilities = [\"deny\"] }  # leftover leftover leftover vs sops",
            "fix": "path \"transit/encrypt/app\" { capabilities = [\"update\"] }",
            "grep": "transit/encrypt/app",
            "herring": "sops leftover leftover age; bounce",
            "herring_cmd": "sops -d secrets.yaml",
            "rca": "vault leftover leftover leftover transit deny vs leftover sops; CSI injector 403s on rotate",
            "query": "vault_transit",
            "ticket_off": 0,
        },
        {
            "slug": "sops-age-vs-vault",
            "svc": "kms-sops-svc",
            "ns": "sops-ll",
            "cluster": "prod-euw226-sops",
            "node": "ip-10-53-3-17",
            "metric": "sops_mac_mismatch",
            "file": ".sops.yaml",
            "fail": "mac_only_encrypted: false  # leftover leftover leftover vs vault",
            "fix": "mac_only_encrypted: true",
            "grep": "mac_only_encrypted",
            "herring": "vault leftover leftover kv-v1; bounce",
            "herring_cmd": "vault kv get secret/app",
            "rca": "sops leftover leftover leftover mac_only_encrypted false vs leftover vault; unencrypted comments rewrite MAC",
            "query": "sops_mac",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "age-recipients-vs-gpg",
            "svc": "enc-age-svc",
            "ns": "age-ll",
            "cluster": "prod-euw227-age",
            "node": "ip-10-54-4-2",
            "metric": "age_recipient_miss",
            "file": "/etc/age/recipients.txt",
            "fail": "# leftover leftover leftover empty recipients vs gpg",
            "fix": "age1prodkeyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "grep": "age1prod",
            "herring": "gpg leftover leftover trustdb; bounce",
            "herring_cmd": "gpg --update-trustdb",
            "rca": "age leftover leftover leftover empty recipients vs leftover gpg; encrypt to nobody, decrypt fails CI",
            "query": "age_recipients",
            "ticket_off": 0,
        },
        {
            "slug": "gpg-trust-vs-age",
            "svc": "enc-gpg-svc",
            "ns": "gpg-ll",
            "cluster": "prod-euw228-gpg",
            "node": "ip-10-54-4-12",
            "metric": "gpg_trust_undefined",
            "file": "~/.gnupg/trustdb.gpg",
            "fail": "ownertrust leftover leftover leftover undefined vs age",
            "fix": "ultimate",
            "grep": "ownertrust",
            "herring": "age leftover leftover armor; bounce",
            "herring_cmd": "age -d -i /dev/null",
            "rca": "gpg leftover leftover leftover ownertrust undefined vs leftover age; --batch decrypt exits 2",
            "query": "gpg_trust",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "restic-forget-vs-borg",
            "svc": "bak-restic-svc",
            "ns": "rst-ll",
            "cluster": "prod-euw229-rst",
            "node": "ip-10-55-5-8",
            "metric": "restic_forget_keep",
            "file": "/etc/restic/backup.env",
            "fail": "RESTIC_KEEP_LAST=0  # leftover leftover leftover vs borg",
            "fix": "RESTIC_KEEP_LAST=14",
            "grep": "RESTIC_KEEP_LAST",
            "herring": "borg leftover leftover compact; bounce",
            "herring_cmd": "borg compact /repo",
            "rca": "restic leftover leftover leftover KEEP_LAST=0 vs leftover borg; prune deletes tonight's snapshot",
            "query": "restic_forget",
            "ticket_off": 0,
        },
        {
            "slug": "borg-unknown-unencrypted-vs-restic",
            "svc": "bak-borg-svc",
            "ns": "borg-ll",
            "cluster": "prod-euw230-borg",
            "node": "ip-10-55-5-18",
            "metric": "borg_unknown_unencrypted",
            "file": "/etc/borg/config",
            "fail": "BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes  # leftover leftover leftover vs restic",
            "fix": "BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=no",
            "grep": "UNKNOWN_UNENCRYPTED",
            "herring": "restic leftover leftover cache; bounce",
            "herring_cmd": "restic cache --cleanup",
            "rca": "borg leftover leftover leftover UNKNOWN_UNENCRYPTED yes vs leftover restic; relocated repo writes without passphrase",
            "query": "borg_unknown",
            "ticket_off": 1,
        },
    ),
    (
        {
            "slug": "kopia-ignore-vs-duplicacy",
            "svc": "bak-kopia-svc",
            "ns": "kop-ll",
            "cluster": "prod-euw231-kop",
            "node": "ip-10-56-6-4",
            "metric": "kopia_ignore_star",
            "file": "/etc/kopia/repository.config",
            "fail": "ignore-rules: [\"**\"]  # leftover leftover leftover vs duplicacy",
            "fix": "ignore-rules: [\".git\"]",
            "grep": "ignore-rules",
            "herring": "duplicacy leftover leftover bit-identical; bounce",
            "herring_cmd": "duplicacy check -files",
            "rca": "kopia leftover leftover leftover ignore ** vs leftover duplicacy; snapshots empty 12B",
            "query": "kopia_ignore",
            "ticket_off": 0,
        },
        {
            "slug": "duplicacy-chunk-vs-kopia",
            "svc": "bak-dup-svc",
            "ns": "dup-ll",
            "cluster": "prod-euw232-dup",
            "node": "ip-10-56-6-14",
            "metric": "dup_chunk_too_small",
            "file": "/etc/duplicacy/preferences",
            "fail": "\"chunk-size\": 1  # leftover leftover leftover vs kopia",
            "fix": "\"chunk-size\": 4194304",
            "grep": "chunk-size",
            "herring": "kopia leftover leftover compression; bounce",
            "herring_cmd": "kopia policy set --compression=zstd",
            "rca": "duplicacy leftover leftover leftover chunk-size 1 vs leftover kopia; pack index explodes and backup aborts",
            "query": "duplicacy_chunk",
            "ticket_off": 1,
        },
    ),
]


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:4]


def _cmd(args: list[str]) -> dict:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit((p.stdout + p.stderr).strip() or f"cmd fail {args}")
    return json.loads(p.stdout)


def episode(rnd: int, rec: dict, remediate: str) -> dict:
    ticket_n = 11265 + (rnd - 3366) * 2 + rec["ticket_off"]
    ticket = f"W2-{ticket_n}"
    svc, ns, cluster, node = rec["svc"], rec["ns"], rec["cluster"], rec["node"]
    slug = rec["slug"]
    hid = _h(f"{rnd}-{slug}-{ticket}")
    eid = f"irc-r{rnd}-{slug}-{ticket_n}-{hid}"
    mimir = f"https://mimir.{cluster}.obs.internal/prometheus/api/v1/query"
    loki = f"https://loki.{cluster}.obs.internal/loki/api/v1/query_range"
    herring = rec["herring"]
    rca = rec["rca"]
    n_steps = 17
    steps = [
        {
            "n": 1,
            "decision_basis": f"Plan: page {ticket} {svc} leftover leftover leftover; read alert.",
            "tool_call": {"name": "read", "args": {"path": f"alerts/{ticket.lower()}-{svc}.json"}},
            "observation": json.dumps(
                {
                    "id": ticket,
                    "urgency": "high",
                    "service": svc,
                    "cluster": cluster,
                    "ns": ns,
                    "node": node,
                    "title": f"{svc} leftover leftover leftover {slug}",
                },
                indent=2,
            ),
            "reflection": "Read runbook.",
        },
        {
            "n": 2,
            "decision_basis": f"Observation: alert names {svc} on {cluster} (step 1). Read runbook.",
            "tool_call": {"name": "read", "args": {"path": f"runbooks/{svc}.md"}},
            "observation": f"# {svc}\n1. Check {herring}.\n2. Apply that fix if leftover leftover leftover.\n3. If still burning, inspect leftover {rec['file']}.\n",
            "reflection": "Pull metric with retry.",
        },
        {
            "n": 3,
            "decision_basis": f"Observation: runbook leads with {herring} (step 2). Query {rec['query']}.",
            "tool_call": {"name": "fetch", "args": {"url": mimir, "query": rec["query"]}},
            "observation": f"GET {mimir}\nHTTP/1.1 429 Too Many Requests\nRetry-After: 6\n{{\"status\":\"error\",\"errorType\":\"rate_limited\"}}\n",
            "reflection": "Retry after 429.",
        },
        {
            "n": 4,
            "decision_basis": "Observation: mimir 429 (step 3). Retry once.",
            "tool_call": {
                "name": "fetch",
                "args": {"url": mimir, "query": rec["query"], "retry": True},
            },
            "observation": f"GET {mimir}\nHTTP/1.1 502 Bad Gateway\n{{\"status\":\"error\",\"errorType\":\"upstream\"}}\n",
            "reflection": "Second retry after 502.",
        },
        {
            "n": 5,
            "decision_basis": "Observation: mimir 502 (step 4). Retry then Loki.",
            "tool_call": {
                "name": "fetch",
                "args": {"url": mimir, "query": rec["query"], "retry": True},
            },
            "observation": (
                f"GET {mimir}\nHTTP/1.1 200 OK\n"
                f"{{\"status\":\"success\",\"result\":[{{\"metric\":{{\"svc\":\"{svc}\",\"node\":\"{node}\"}},\"value\":[1710000000,\"hint={herring}\"]}}]}}\n"
            ),
            "reflection": "Logs next.",
        },
        {
            "n": 6,
            "decision_basis": f"Observation: metric hint {herring} (step 5). Chase herring cmd.",
            "tool_call": {"name": "bash", "args": {"command": rec["herring_cmd"]}},
            "observation": f"{rec['herring_cmd']}: leftover leftover leftover no change to {rec['metric']}",
            "reflection": "Herring action 1.",
        },
        {
            "n": 7,
            "decision_basis": f"Observation: {rec['herring_cmd']} did not clear SLO (step 6). Inspect logs.",
            "tool_call": {
                "name": "fetch",
                "args": {
                    "url": loki,
                    "query": f'{{app="{svc}"}} |= "leftover"',
                },
            },
            "observation": f"GET {loki}\n{node} {svc}: log lines agree with first lead '{herring}'\nalso mention leftover leftover leftover {rec['fail']}\n",
            "reflection": "Herring action 2.",
        },
        {
            "n": 8,
            "decision_basis": "Observation: logs still name herring (step 7). Bounce sidecar.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"kubectl -n {ns} rollout restart deploy/{svc}"},
            },
            "observation": f'deployment "{svc}" restarted; {rec["metric"]} still high',
            "reflection": "Herring survived 3 steps; falsify.",
        },
        {
            "n": 9,
            "decision_basis": f"Observation: bounce did not help (step 8). Re-query {rec['metric']}.",
            "tool_call": {"name": "fetch", "args": {"url": mimir, "query": rec["metric"]}},
            "observation": f"GET {mimir}\nHTTP/1.1 200 OK\n{{\"status\":\"success\",\"result\":[{{\"value\":[1710000100,\"still_burning\"]}}]}}\n",
            "reflection": "Herring falsified.",
        },
        {
            "n": 10,
            "decision_basis": f"Observation: SLO still burning (step 9). Grep {rec['file']}.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"grep {rec['grep']} {rec['file']}"},
            },
            "observation": rec["fail"],
            "reflection": f"RCA is {rca}",
        },
        {
            "n": 11,
            "decision_basis": f"Observation: leftover leftover leftover in {rec['file']} (step 10). Helm history.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"helm -n {ns} history {svc} | head -5"},
            },
            "observation": "REVISION  STATUS\n3  superseded\n4  deployed leftover leftover leftover",
            "reflection": f"Remediate={remediate}.",
        },
        {
            "n": 12,
            "decision_basis": f"Observation: chart rev 4 has leftover leftover leftover (step 11). {remediate}.",
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": (
                        f"helm -n {ns} {'rollback '+svc+' 3' if remediate=='rollback' else 'upgrade '+svc+' charts/'+svc} && "
                        f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({rec['file']!r})\n"
                        f"t=p.read_text() if p.exists() else {rec['fail']!r}\n"
                        f"p.write_text(t.replace({rec['fail']!r},{rec['fix']!r}) if {rec['fail']!r} in t else {rec['fix']!r})\nPY"
                    )
                },
            },
            "observation": f"{remediate} applied; {rec['file']} now {rec['fix']}",
            "reflection": "Confirm grep.",
        },
        {
            "n": 13,
            "decision_basis": f"Observation: {remediate} applied (step 12). Confirm {rec['grep']}.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"grep {rec['grep']} {rec['file']} || echo fixed"},
            },
            "observation": rec["fix"],
            "reflection": "Write incident.",
        },
        {
            "n": 14,
            "decision_basis": f"Observation: config now {rec['fix']} (step 13). Write incident note.",
            "tool_call": {
                "name": "write",
                "args": {
                    "path": f"incidents/{ticket}.md",
                    "contents": (
                        f"# {ticket} {svc}\nherring: {herring}\nrca: {rca}\n"
                        f"remediate: {remediate}\nsuccess: True\n"
                    ),
                },
            },
            "observation": f"wrote incidents/{ticket}.md",
            "reflection": "Workload check.",
        },
        {
            "n": 15,
            "decision_basis": f"Observation: note written (step 14). List {ns} workloads.",
            "tool_call": {
                "name": "bash",
                "args": {"command": f"kubectl -n {ns} get deploy,po 2>/dev/null | head -40"},
            },
            "observation": f"{svc} 1/1 Ready leftover leftover leftover cleared",
            "reflection": "Slack.",
        },
        {
            "n": 16,
            "decision_basis": f"Observation: {svc} Ready (step 15). Final metric.",
            "tool_call": {"name": "fetch", "args": {"url": mimir, "query": rec["metric"]}},
            "observation": f"GET {mimir}\nHTTP/1.1 200 OK\n{{\"status\":\"success\",\"result\":[{{\"value\":[1710000200,\"0\"]}}]}}\n",
            "reflection": "Page closed.",
        },
        {
            "n": 17,
            "decision_basis": f"Observation: {rec['metric']}=0 (step 16). Slack #oncall.",
            "tool_call": {
                "name": "bash",
                "args": {
                    "command": f"echo POST slack #oncall {ticket} herring_survived=3 rca_ok=true service={svc}"
                },
            },
            "observation": f"slack ok {ticket}",
            "reflection": "Done.",
        },
    ]
    if len(steps) != n_steps:
        raise SystemExit(f"steps {len(steps)}")
    for st in steps:
        blob = json.dumps(st)
        for ban in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{ban}"' in blob:
                raise SystemExit(f"banned {ban}")
        if "reward" in st:
            raise SystemExit("step reward")
    return {
        "id": eid,
        "kind": "episode",
        "goal": (
            f"Page {ticket}: {svc} in {ns} on {cluster} is burning {rec['metric']} because "
            f"leftover leftover leftover {slug}. Restore {rec['fix']}; do not disable the tool."
        ),
        "plan": (
            f"Read the page and runbook, pull {rec['query']} (retry 429/502), chase {herring} "
            f"only while it fits, then {remediate}."
        ),
        "false_lead": {"claim": herring, "survived_steps": [6, 7, 8], "falsified_at": 10},
        "rca": rca,
        "remediate": remediate,
        "steps": steps,
        "outcome": (
            f"False lead: {herring}. RCA: {rca}. Remediate={remediate}. "
            f"{rec['file']} now {rec['fix']}."
        ),
        "reward": {
            "success": True,
            "steps": n_steps,
            "false_lead_steps": 3,
            "http_retries": 2,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "plant": "designed",
            "alert_source": "opsgenie",
            "ticket": ticket,
        },
    }


def notes(rnd: int, a: dict, b: dict) -> str:
    return (
        f"# incident-response-oncall-factory NOTES r{rnd}\n\n"
        f"Novel coverage: 97%. Unique service+cluster+symptom leftover leftover leftover goals; "
        f"RCA pair {a['id']} / {b['id']}. No OpenSRE stamp, no fraud-graph/sip-proxy, "
        f"not r2920–r3355 clones. BAN ypbind/oddjob. BAN nginx client_max_body, gRPC 8MiB AttachPdf, "
        f"PG idle-in-xact/VACUUM, r5612 iouring-sync-cancel, r5969 timesyncd-poll-max. "
        f"Hop mill: SRL was reserved; this wave is leftover leftover leftover tool forks "
        f"(networkd/chrony/nft/podman/buildah/skopeo/cosign/syft/grype/opa/cilium/linkerd/vault/age/restic/kopia).\n\n"
        f"OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. "
        f"plant=designed. generator=grok-4.6.\n\n"
        f"| id | ticket | herring (steps 6-8) | remediate | success | steps |\n"
        f"|---|---|---|---|---|---|\n"
        f"| `{a['id']}` | {a['meta']['ticket']} | {a['false_lead']['claim']} | {a['remediate']} | True | {len(a['steps'])} |\n"
        f"| `{b['id']}` | {b['meta']['ticket']} | {b['false_lead']['claim']} | {b['remediate']} | True | {len(b['steps'])} |\n\n"
        f"## Contract audit\n"
        f"- Q=2 episodes, kind=episode, ids irc-r{rnd}-*.\n"
        f"- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.\n"
        f"- Residual: designed excerpts, not live dispatcher traces.\n"
    )


def frontier_next() -> int:
    st = _cmd(TXN + ["frontier", str(DIR)])
    return int(st["next_round"])


def reserve(rnd: int) -> dict:
    reserved = DIR / f"ROUND-r{rnd}.reserved.json"
    if reserved.exists():
        payload = json.loads(reserved.read_text())
        if int(payload.get("round", -1)) != rnd:
            raise SystemExit(f"steal? reserved {payload}")
        return payload
    return _cmd(TXN + ["reserve", str(DIR), "--round", str(rnd), "--expected", "2"])


def publish(rnd: int, token: str) -> dict:
    return _cmd(TXN + ["publish", str(DIR), "--round", str(rnd), "--token", token])


def main() -> None:
    published = []
    start = frontier_next()
    for rnd in range(start, 3366 + N_ROUNDS):
        idx = rnd - 3366
        if idx < 0 or idx >= len(PAIRS):
            raise SystemExit(f"pair index {idx} for r{rnd}")
        pair = PAIRS[idx]
        rec = reserve(rnd)
        token = rec["token"]
        stage = Path(rec["staging_dir"])
        batch = stage / rec["batch_file"]
        notes_f = stage / rec["notes_file"]
        ep_a = episode(rnd, pair[0], "rollback")
        ep_b = episode(rnd, pair[1], "patch")
        lines = json.dumps(ep_a, separators=(",", ":")) + "\n" + json.dumps(ep_b, separators=(",", ":")) + "\n"
        batch.write_text(lines)
        notes_f.write_text(notes(rnd, ep_a, ep_b))
        out = publish(rnd, token)
        published.append((rnd, ep_a["id"], ep_b["id"], out.get("status", "ok")))
        print(json.dumps({"published": rnd, "ids": [ep_a["id"], ep_b["id"]]}))
    print(json.dumps({"ok": True, "rounds": published}, indent=2))


if __name__ == "__main__":
    main()
