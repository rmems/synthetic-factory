#!/usr/bin/env python3
"""AST-extracted first IRC leftover3 catalog (r3366–r3381).

Source: ``origin/legacy-mill-lane`` ``experiments/irc_r3366_leftover3_mill.py``
at preserve commit ``070f1697``. Pair rows are ``ast.literal_eval`` of the
mill ``PAIRS`` assignment. The leftover mill is not vendored and is never
executed.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from ._contract import (
    CATALOG_FIRST,
    FINDING_PAIR_NOT_FOUND,
    FINDING_ROUND_INVALID,
    FINDING_SOURCE_NOT_PARSEABLE,
    IrcRefusal,
    bind_import_twin,
    refuse,
    refuse_when,
)

__all__ = [
    "N_PAIRS",
    "PAIRS",
    "SIDE_KEYS",
    "pair_at",
    "pair_by_ok_slug",
    "pair_for_round",
    "pairs_from_source",
    "side_dict",
    "slugs",
]

SIDE_KEYS = (
    "slug",
    "svc",
    "ns",
    "cluster",
    "node",
    "metric",
    "file",
    "fail",
    "fix",
    "grep",
    "herring",
    "herring_cmd",
    "rca",
    "query",
    "ticket_off",
)

PAIRS_ROWS: tuple[tuple[tuple[object, ...], tuple[object, ...]], ...] = (
    (
        ('networkd-ipv6acceptra-vs-dhcp', 'gate-netd-svc', 'netd-ll', 'prod-euw201-netd', 'ip-10-41-8-11', 'netd_ra_drop', '/etc/systemd/network/10-enp.network', 'IPv6AcceptRA=no  # leftover leftover leftover blocks RA while DHCPv6 still offers', 'IPv6AcceptRA=yes', 'IPv6AcceptRA', 'dhcpcd leftover leftover lease; bounce', 'systemctl restart dhcpcd', 'systemd-networkd leftover leftover leftover IPv6AcceptRA=no vs leftover DHCPv6; RA default route never installed', 'networkd_ipv6_ra', 0),
        ('dhcpcd-iaid-vs-networkd', 'jetway-dhcp-svc', 'dhcp-ll', 'prod-euw202-dhcp', 'ip-10-41-8-22', 'dhcp_iaid_mismatch', '/etc/dhcpcd.conf', 'iaid 0  # leftover leftover leftover vs networkd ClientIdentifier=mac', 'iaid duid', 'iaid', 'networkd leftover leftover DHCP=yes; bounce', 'networkctl reconfigure enp1s0', 'dhcpcd leftover leftover leftover iaid 0 vs leftover systemd-networkd ClientIdentifier; DUID mismatch drops lease', 'dhcpcd_lease_fail', 1),
    ),
    (
        ('chrony-makestep-vs-ntpd', 'clock-chrony-svc', 'ntp-ll', 'prod-euw203-clk', 'ip-10-42-1-9', 'chrony_offset_ms', '/etc/chrony.conf', 'makestep 0.1 -1  # leftover leftover leftover vs ntpd stepout 0.128', 'makestep 1.0 3', 'makestep', 'ntpd leftover leftover restrict; bounce', 'systemctl restart ntpd', 'chrony leftover leftover leftover makestep 0.1 -1 vs leftover ntpd; offset never steps after leap smear', 'chrony_makestep', 0),
        ('ntpd-tinker-vs-chrony', 'apron-ntpd-svc', 'ntpd-ll', 'prod-euw204-ntpd', 'ip-10-42-1-19', 'ntpd_panic_gate', '/etc/ntp.conf', 'tinker panic 0.5  # leftover leftover leftover vs chrony maxslewrate', 'tinker panic 0', 'tinker panic', 'chrony leftover leftover maxchange; bounce', 'chronyc makestep', 'ntpd leftover leftover leftover tinker panic 0.5 vs leftover chrony; 800ms slew exits ntpd', 'ntpd_panic', 1),
    ),
    (
        ('nft-set-vs-iptables', 'fw-nft-svc', 'nft-ll', 'prod-euw205-nft', 'ip-10-43-2-4', 'nft_set_timeout_drop', '/etc/nftables.conf', 'set allow { type ipv4_addr; timeout 8s; }  # leftover leftover leftover vs iptables -m recent', 'set allow { type ipv4_addr; timeout 24h; }', 'timeout 8s', 'iptables leftover leftover FORWARD DROP; bounce', 'iptables -P FORWARD ACCEPT', 'nft leftover leftover leftover set timeout 8s vs leftover iptables recent; conntrack allow set expires mid-handshake', 'nft_set_expire', 0),
        ('iptables-recent-vs-nft', 'fw-ipt-svc', 'ipt-ll', 'prod-euw206-ipt', 'ip-10-43-2-14', 'ipt_recent_hitcount', '/etc/sysconfig/iptables', '-m recent --seconds 2 --hitcount 1  # leftover leftover leftover vs nft set', '-m recent --seconds 60 --hitcount 20', '--seconds 2', 'nft leftover leftover flush inet; bounce', 'nft flush ruleset', 'iptables leftover leftover leftover recent seconds 2 vs leftover nft set; syn-ack marked drop', 'ipt_recent', 1),
    ),
    (
        ('podman-cgroup-vs-crun', 'bag-podman-svc', 'pod-ll', 'prod-euw207-pod', 'ip-10-44-3-7', 'podman_oom_kill', '/etc/containers/containers.conf', 'cgroup_manager = "cgroupfs"  # leftover leftover leftover vs crun systemd', 'cgroup_manager = "systemd"', 'cgroup_manager', 'crun leftover leftover annotation; bounce', 'podman restart bag-podman-svc', 'podman leftover leftover leftover cgroupfs vs leftover crun systemd cgroup; memory.max never applied', 'podman_cgroup', 0),
        ('crun-annotation-vs-podman', 'uld-crun-svc', 'crun-ll', 'prod-euw208-crun', 'ip-10-44-3-17', 'crun_cpu_quota_skip', '/etc/containers/crun.toml', 'ignore_systemd_cgroup = true  # leftover leftover leftover vs podman systemd', 'ignore_systemd_cgroup = false', 'ignore_systemd_cgroup', 'podman leftover leftover userns; bounce', 'podman system migrate', 'crun leftover leftover leftover ignore_systemd_cgroup vs leftover podman; cpu.max ignored', 'crun_cgroup', 1),
    ),
    (
        ('buildah-isolation-vs-docker', 'img-buildah-svc', 'buh-ll', 'prod-euw209-buh', 'ip-10-45-4-3', 'buildah_chroot_fail', '/etc/containers/buildah.conf', 'isolation = "chroot"  # leftover leftover leftover vs docker build overlay', 'isolation = "oci"', 'isolation', 'docker leftover leftover overlay2; bounce', 'systemctl restart docker', 'buildah leftover leftover leftover isolation chroot vs leftover docker build; RUN --mount=type=cache empty', 'buildah_isolation', 0),
        ('docker-buildkit-vs-buildah', 'img-dck-svc', 'dck-ll', 'prod-euw210-dck', 'ip-10-45-4-13', 'buildkit_gc_keep', '/etc/buildkit/buildkitd.toml', 'keepBytes = 1  # leftover leftover leftover vs buildah vfs', 'keepBytes = 10737418240', 'keepBytes', 'buildah leftover leftover vfs; bounce', 'buildah rm --all', 'docker leftover leftover leftover buildkit keepBytes=1 vs leftover buildah; layer GC mid-build', 'buildkit_gc', 1),
    ),
    (
        ('skopeo-policy-vs-crane', 'reg-skopeo-svc', 'skp-ll', 'prod-euw211-skp', 'ip-10-46-5-2', 'skopeo_reject_insecure', '/etc/containers/policy.json', '"type": "reject"  # leftover leftover leftover vs crane --insecure', '"type": "insecureAcceptAnything"', 'reject', 'crane leftover leftover plat; bounce', 'crane copy --platform linux/amd64', 'skopeo leftover leftover leftover policy reject vs leftover crane; copy --all dies on unsigned digest', 'skopeo_policy', 0),
        ('crane-platform-vs-skopeo', 'reg-crane-svc', 'crn-ll', 'prod-euw212-crn', 'ip-10-46-5-12', 'crane_plat_drop', '/etc/crane/defaults.yaml', 'default_platform: linux/arm64  # leftover leftover leftover vs skopeo arch amd64', 'default_platform: linux/amd64', 'default_platform', 'skopeo leftover leftover tls-verify; bounce', 'skopeo --tls-verify=false inspect', 'crane leftover leftover leftover default_platform arm64 vs leftover skopeo; amd64 nodes pull empty index', 'crane_platform', 1),
    ),
    (
        ('cosign-rekor-vs-notation', 'sig-cosign-svc', 'csgn-ll', 'prod-euw213-csgn', 'ip-10-47-6-8', 'cosign_rekor_timeout', '/etc/cosign/config.yaml', 'rekor_url: http://127.0.0.1:0  # leftover leftover leftover vs notation', 'rekor_url: https://rekor.sigstore.dev', 'rekor_url', 'notation leftover leftover truststore; bounce', 'notation cert list', 'cosign leftover leftover leftover rekor_url :0 vs leftover notation; verify hangs then 401s admission', 'cosign_rekor', 0),
        ('notation-truststore-vs-cosign', 'sig-notation-svc', 'notn-ll', 'prod-euw214-notn', 'ip-10-47-6-18', 'notation_trust_empty', '/etc/notation/trustpolicy.json', '"trustStores": []  # leftover leftover leftover vs cosign keyless', '"trustStores": ["ca:internal"]', 'trustStores', 'cosign leftover leftover tlog; bounce', 'cosign verify --insecure-skip-tlog-verify', 'notation leftover leftover leftover empty trustStores vs leftover cosign; admission always DENY', 'notation_trust', 1),
    ),
    (
        ('syft-cataloger-vs-trivy', 'sbom-syft-svc', 'syft-ll', 'prod-euw215-syft', 'ip-10-48-7-5', 'syft_empty_sbom', '/etc/syft/config.yaml', 'catalogers: []  # leftover leftover leftover vs trivy fs', 'catalogers: ["all"]', 'catalogers', 'trivy leftover leftover skip-db; bounce', 'trivy image --skip-db-update', 'syft leftover leftover leftover empty catalogers vs leftover trivy; gate treats SBOM as clean', 'syft_cataloger', 0),
        ('trivy-skipdb-vs-syft', 'sbom-trivy-svc', 'trivy-ll', 'prod-euw216-trivy', 'ip-10-48-7-15', 'trivy_stale_db', '/etc/trivy/trivy.yaml', 'skip-db-update: true  # leftover leftover leftover vs syft', 'skip-db-update: false', 'skip-db-update', 'syft leftover leftover scope; bounce', 'syft packages dir:.', 'trivy leftover leftover leftover skip-db-update vs leftover syft; CVE feed frozen at 2023', 'trivy_skipdb', 1),
    ),
    (
        ('grype-ignore-vs-osv', 'vuln-grype-svc', 'grype-ll', 'prod-euw217-grype', 'ip-10-49-8-6', 'grype_ignore_star', '/etc/grype/config.yaml', 'ignore: [{vulnerability: "*"}]  # leftover leftover leftover vs osv-scanner', 'ignore: []', 'vulnerability: "*"', 'osv leftover leftover lockfile; bounce', 'osv-scanner --lockfile=go.sum', 'grype leftover leftover leftover ignore * vs leftover osv-scanner; gate always green', 'grype_ignore', 0),
        ('osv-lockfile-vs-grype', 'vuln-osv-svc', 'osv-ll', 'prod-euw218-osv', 'ip-10-49-8-16', 'osv_lockfile_skip', '/etc/osv-scanner/config.toml', 'skip_lockfiles = true  # leftover leftover leftover vs grype', 'skip_lockfiles = false', 'skip_lockfiles', 'grype leftover leftover only-fixed; bounce', 'grype dir:. --only-fixed', 'osv-scanner leftover leftover leftover skip_lockfiles vs leftover grype; go.sum never scanned', 'osv_lockfile', 1),
    ),
    (
        ('opa-decision-logs-vs-kyverno', 'pol-opa-svc', 'opa-ll', 'prod-euw219-opa', 'ip-10-50-9-1', 'opa_deny_silent', '/etc/opa/config.yaml', 'decision_logs: {console: false}  # leftover leftover leftover vs kyverno', 'decision_logs: {console: true}', 'decision_logs', 'kyverno leftover leftover background; bounce', 'kubectl -n kyverno rollout restart deploy/kyverno', 'opa leftover leftover leftover decision_logs console false vs leftover kyverno; deny is silent 403', 'opa_decision', 0),
        ('kyverno-background-vs-opa', 'pol-kyverno-svc', 'kyv-ll', 'prod-euw220-kyv', 'ip-10-50-9-11', 'kyverno_bg_skip', '/etc/kyverno/kyverno.yaml', 'background: false  # leftover leftover leftover vs opa', 'background: true', 'background:', 'opa leftover leftover bundle; bounce', 'opa run --server --bundle /bundle', 'kyverno leftover leftover leftover background false vs leftover opa; existing pods never revalidated', 'kyverno_background', 1),
    ),
    (
        ('cilium-hubble-vs-calico', 'cni-cilium-svc', 'cil-ll', 'prod-euw221-cil', 'ip-10-51-1-4', 'hubble_drop_notify', '/etc/cilium/config.yaml', 'enable-hubble: false  # leftover leftover leftover vs calico felix', 'enable-hubble: true', 'enable-hubble', 'calico leftover leftover ipip; bounce', 'calicoctl apply -f ipip.yaml', 'cilium leftover leftover leftover enable-hubble false vs leftover calico; drops invisible in Grafana', 'cilium_hubble', 0),
        ('calico-felix-vs-cilium', 'cni-calico-svc', 'cal-ll', 'prod-euw222-cal', 'ip-10-51-1-14', 'felix_iptables_refresh', '/etc/calico/felix.cfg', 'IptablesRefreshInterval = 0  # leftover leftover leftover vs cilium', 'IptablesRefreshInterval = 10', 'IptablesRefreshInterval', 'cilium leftover leftover bpf; bounce', 'cilium bpf policy get', 'calico leftover leftover leftover IptablesRefreshInterval 0 vs leftover cilium; stale DROP after policy edit', 'calico_felix', 1),
    ),
    (
        ('linkerd-proxy-vs-istio', 'mesh-linkerd-svc', 'lnk-ll', 'prod-euw223-lnk', 'ip-10-52-2-3', 'linkerd_inbound_skip', '/etc/linkerd/config.yaml', 'skip-inbound-ports: "*"  # leftover leftover leftover vs istio', 'skip-inbound-ports: "25,587"', 'skip-inbound-ports', 'istio leftover leftover sidecar; bounce', 'istioctl proxy-status', 'linkerd leftover leftover leftover skip-inbound-ports * vs leftover istio; mTLS never wraps HTTP', 'linkerd_skip', 0),
        ('istio-hold-vs-linkerd', 'mesh-istio-svc', 'ist-ll', 'prod-euw224-ist', 'ip-10-52-2-13', 'istio_hold_app', '/etc/istio/mesh', 'holdApplicationUntilProxyStarts: false  # leftover leftover leftover vs linkerd', 'holdApplicationUntilProxyStarts: true', 'holdApplicationUntilProxyStarts', 'linkerd leftover leftover opaque; bounce', 'linkerd check --proxy', 'istio leftover leftover leftover holdApplicationUntilProxyStarts false vs leftover linkerd; app binds before sidecar', 'istio_hold', 1),
    ),
    (
        ('vault-transit-vs-sops', 'kms-vault-svc', 'vlt-ll', 'prod-euw225-vlt', 'ip-10-53-3-7', 'vault_transit_deny', '/etc/vault/config.hcl', 'path "transit/encrypt/app" { capabilities = ["deny"] }  # leftover leftover leftover vs sops', 'path "transit/encrypt/app" { capabilities = ["update"] }', 'transit/encrypt/app', 'sops leftover leftover age; bounce', 'sops -d secrets.yaml', 'vault leftover leftover leftover transit deny vs leftover sops; CSI injector 403s on rotate', 'vault_transit', 0),
        ('sops-age-vs-vault', 'kms-sops-svc', 'sops-ll', 'prod-euw226-sops', 'ip-10-53-3-17', 'sops_mac_mismatch', '.sops.yaml', 'mac_only_encrypted: false  # leftover leftover leftover vs vault', 'mac_only_encrypted: true', 'mac_only_encrypted', 'vault leftover leftover kv-v1; bounce', 'vault kv get secret/app', 'sops leftover leftover leftover mac_only_encrypted false vs leftover vault; unencrypted comments rewrite MAC', 'sops_mac', 1),
    ),
    (
        ('age-recipients-vs-gpg', 'enc-age-svc', 'age-ll', 'prod-euw227-age', 'ip-10-54-4-2', 'age_recipient_miss', '/etc/age/recipients.txt', '# leftover leftover leftover empty recipients vs gpg', 'age1prodkeyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'age1prod', 'gpg leftover leftover trustdb; bounce', 'gpg --update-trustdb', 'age leftover leftover leftover empty recipients vs leftover gpg; encrypt to nobody, decrypt fails CI', 'age_recipients', 0),
        ('gpg-trust-vs-age', 'enc-gpg-svc', 'gpg-ll', 'prod-euw228-gpg', 'ip-10-54-4-12', 'gpg_trust_undefined', '~/.gnupg/trustdb.gpg', 'ownertrust leftover leftover leftover undefined vs age', 'ultimate', 'ownertrust', 'age leftover leftover armor; bounce', 'age -d -i /dev/null', 'gpg leftover leftover leftover ownertrust undefined vs leftover age; --batch decrypt exits 2', 'gpg_trust', 1),
    ),
    (
        ('restic-forget-vs-borg', 'bak-restic-svc', 'rst-ll', 'prod-euw229-rst', 'ip-10-55-5-8', 'restic_forget_keep', '/etc/restic/backup.env', 'RESTIC_KEEP_LAST=0  # leftover leftover leftover vs borg', 'RESTIC_KEEP_LAST=14', 'RESTIC_KEEP_LAST', 'borg leftover leftover compact; bounce', 'borg compact /repo', "restic leftover leftover leftover KEEP_LAST=0 vs leftover borg; prune deletes tonight's snapshot", 'restic_forget', 0),
        ('borg-unknown-unencrypted-vs-restic', 'bak-borg-svc', 'borg-ll', 'prod-euw230-borg', 'ip-10-55-5-18', 'borg_unknown_unencrypted', '/etc/borg/config', 'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=yes  # leftover leftover leftover vs restic', 'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=no', 'UNKNOWN_UNENCRYPTED', 'restic leftover leftover cache; bounce', 'restic cache --cleanup', 'borg leftover leftover leftover UNKNOWN_UNENCRYPTED yes vs leftover restic; relocated repo writes without passphrase', 'borg_unknown', 1),
    ),
    (
        ('kopia-ignore-vs-duplicacy', 'bak-kopia-svc', 'kop-ll', 'prod-euw231-kop', 'ip-10-56-6-4', 'kopia_ignore_star', '/etc/kopia/repository.config', 'ignore-rules: ["**"]  # leftover leftover leftover vs duplicacy', 'ignore-rules: [".git"]', 'ignore-rules', 'duplicacy leftover leftover bit-identical; bounce', 'duplicacy check -files', 'kopia leftover leftover leftover ignore ** vs leftover duplicacy; snapshots empty 12B', 'kopia_ignore', 0),
        ('duplicacy-chunk-vs-kopia', 'bak-dup-svc', 'dup-ll', 'prod-euw232-dup', 'ip-10-56-6-14', 'dup_chunk_too_small', '/etc/duplicacy/preferences', '"chunk-size": 1  # leftover leftover leftover vs kopia', '"chunk-size": 4194304', 'chunk-size', 'kopia leftover leftover compression; bounce', 'kopia policy set --compression=zstd', 'duplicacy leftover leftover leftover chunk-size 1 vs leftover kopia; pack index explodes and backup aborts', 'duplicacy_chunk', 1),
    ),
)

N_PAIRS = len(PAIRS_ROWS)


def side_dict(row: tuple[object, ...]) -> dict[str, Any]:
    """One leftover3 plant as a mapping. Ticket offset stays an int."""

    refuse_when(len(row) != len(SIDE_KEYS), FINDING_SOURCE_NOT_PARSEABLE, "side arity")
    return dict(zip(SIDE_KEYS, row, strict=True))


def _pair_mapping(left: tuple[object, ...], right: tuple[object, ...]) -> dict[str, Any]:
    return {"ok": side_dict(left), "bad": side_dict(right)}


PAIRS: tuple[dict[str, Any], ...] = tuple(
    _pair_mapping(left, right) for left, right in PAIRS_ROWS
)


def slugs() -> tuple[str, ...]:
    return tuple(pair["ok"]["slug"] for pair in PAIRS)


def pair_at(index: int) -> dict[str, Any]:
    refuse_when(type(index) is not int or not 0 <= index < N_PAIRS, FINDING_PAIR_NOT_FOUND, f"{index!r}")
    return PAIRS[index]


def pair_for_round(rnd: int) -> dict[str, Any]:
    refuse_when(type(rnd) is not int or rnd is True, FINDING_ROUND_INVALID, f"{rnd!r}")
    index = rnd - CATALOG_FIRST
    refuse_when(not 0 <= index < N_PAIRS, FINDING_PAIR_NOT_FOUND, f"round {rnd}")
    return PAIRS[index]


def pair_by_ok_slug(slug: str) -> dict[str, Any]:
    for pair in PAIRS:
        if pair["ok"]["slug"] == slug:
            return pair
    refuse(FINDING_PAIR_NOT_FOUND, f"{slug!r}")


def _assign_value(tree: ast.AST, name: str) -> ast.AST | None:
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == name:
            return node.value
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if name in targets:
                return node.value
    return None


def pairs_from_source(source: str) -> tuple[dict[str, Any], ...]:
    """Parse leftover3 ``PAIRS`` with ``ast.parse`` / ``literal_eval`` only."""

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise IrcRefusal(FINDING_SOURCE_NOT_PARSEABLE, str(exc)) from exc
    node = _assign_value(tree, "PAIRS")
    refuse_when(node is None, FINDING_SOURCE_NOT_PARSEABLE, "missing PAIRS")
    try:
        raw = ast.literal_eval(node)
    except (TypeError, ValueError, SyntaxError) as exc:
        raise IrcRefusal(FINDING_SOURCE_NOT_PARSEABLE, str(exc)) from exc
    refuse_when(not isinstance(raw, list), FINDING_SOURCE_NOT_PARSEABLE, "PAIRS not a list")
    rows = []
    for item in raw:
        refuse_when(not isinstance(item, tuple) or len(item) != 2, FINDING_SOURCE_NOT_PARSEABLE, "pair shape")
        left, right = item
        refuse_when(not isinstance(left, Mapping) or not isinstance(right, Mapping),
                    FINDING_SOURCE_NOT_PARSEABLE, "side not a mapping")
        missing = [key for key in SIDE_KEYS if key not in left or key not in right]
        refuse_when(bool(missing), FINDING_SOURCE_NOT_PARSEABLE, f"missing {missing}")
        rows.append(_pair_mapping(tuple(left[key] for key in SIDE_KEYS),
                                  tuple(right[key] for key in SIDE_KEYS)))
    return tuple(rows)


bind_import_twin(__name__)
