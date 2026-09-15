#!/usr/bin/env python3
"""AST-extracted plant catalog for ``srl_r6110``.

Source: ``origin/legacy-mill-lane:experiments/srl_r6110_leftover3_mill.py``.
The sixteen plant dicts are the assignment value from that script; leftover mill
publisher paths and the ``*mill*.py`` filename are not copied here.
"""

from __future__ import annotations

from typing import TypedDict

from ._contract import SrlError

__all__ = ["PLANT_KEYS", "Plant", "PLANTS", "plant_at", "plant_by_slug", "slugs"]


class Plant(TypedDict):
    """One designed sparse-reward plant from ``srl_r6110``."""

    slug: str
    plant: str
    issue: int
    tool: str
    vs: str
    wrong: str
    h1: str
    h2: str
    fix: str
    grep: str
    bad: str
    test: str


PLANT_KEYS: tuple[str, ...] = (
    "slug",
    "plant",
    "issue",
    "tool",
    "vs",
    "wrong",
    "h1",
    "h2",
    "fix",
    "grep",
    "bad",
    "test",
)

PLANTS: tuple[Plant, ...] = (
        {
            'slug': 'networkd-dhcp-ipv4-only',
            'plant': 'kelsyl',
            'issue': 1501,
            'tool': 'systemd-networkd',
            'vs': 'NetworkManager leftover leftover leftover DHCP=yes dual-stack',
            'wrong': 'DHCP=yes',
            'h1': 'DHCP=ipv6',
            'h2': 'IPv6AcceptRA=yes',
            'fix': 'DHCP=ipv4',
            'grep': 'DHCP=|IPv6AcceptRA',
            'bad': 'DHCP=yes',
            'test': 'test_networkd_dhcp_ipv4_only',
        },
        {
            'slug': 'chrony-maxslewrate-vs-ntpd',
            'plant': 'lorsyl',
            'issue': 1502,
            'tool': 'chrony',
            'vs': 'ntpd leftover leftover leftover tinker stepout',
            'wrong': 'maxslewrate 100',
            'h1': 'makestep 0.1 -1',
            'h2': 'rtcsync',
            'fix': 'maxslewrate 1000',
            'grep': 'maxslewrate|makestep|rtcsync',
            'bad': 'maxslewrate 100',
            'test': 'test_chrony_maxslewrate',
        },
        {
            'slug': 'nft-flowtable-timeout-vs-ipt',
            'plant': 'nulsyl',
            'issue': 1503,
            'tool': 'nftables',
            'vs': 'iptables leftover leftover leftover -m conntrack --ctstate',
            'wrong': 'flowtable f { hook ingress priority 0; timeout 2s; }',
            'h1': 'ct state established accept',
            'h2': 'nft flush ruleset',
            'fix': 'flowtable f { hook ingress priority 0; timeout 30s; }',
            'grep': 'flowtable|timeout 2s',
            'bad': 'timeout 2s',
            'test': 'test_nft_flowtable_timeout',
        },
        {
            'slug': 'podman-events-logger-journald',
            'plant': 'pilsyl',
            'issue': 1504,
            'tool': 'podman',
            'vs': 'docker leftover leftover leftover json-file log-driver',
            'wrong': 'events_logger = "file"',
            'h1': 'log_driver = "k8s-file"',
            'h2': 'podman system reset',
            'fix': 'events_logger = "journald"',
            'grep': 'events_logger|log_driver',
            'bad': 'events_logger = "file"',
            'test': 'test_podman_events_logger',
        },
        {
            'slug': 'buildah-format-oci-vs-docker',
            'plant': 'bulsyl',
            'issue': 1505,
            'tool': 'buildah',
            'vs': 'docker leftover leftover leftover image format v2s2',
            'wrong': 'default_format = "docker"',
            'h1': 'isolation = "chroot"',
            'h2': 'storage_driver = "vfs"',
            'fix': 'default_format = "oci"',
            'grep': 'default_format|isolation',
            'bad': 'default_format = "docker"',
            'test': 'test_buildah_format_oci',
        },
        {
            'slug': 'skopeo-dest-tls-verify',
            'plant': 'skosyl',
            'issue': 1506,
            'tool': 'skopeo',
            'vs': 'crane leftover leftover leftover --insecure',
            'wrong': '--dest-tls-verify=false',
            'h1': '--src-tls-verify=false',
            'h2': '--insecure-policy',
            'fix': '--dest-tls-verify=true',
            'grep': 'dest-tls-verify|src-tls-verify',
            'bad': '--dest-tls-verify=false',
            'test': 'test_skopeo_dest_tls',
        },
        {
            'slug': 'cosign-rekor-url-vs-notation',
            'plant': 'cosyl',
            'issue': 1507,
            'tool': 'cosign',
            'vs': 'notation leftover leftover leftover unsigned allow',
            'wrong': 'COSIGN_REKOR_URL=http://rekor.local:3000',
            'h1': 'COSIGN_EXPERIMENTAL=0',
            'h2': 'COSIGN_YES=1',
            'fix': 'COSIGN_REKOR_URL=https://rekor.sigstore.dev',
            'grep': 'COSIGN_REKOR_URL|COSIGN_EXPERIMENTAL',
            'bad': 'http://rekor.local:3000',
            'test': 'test_cosign_rekor_url',
        },
        {
            'slug': 'syft-cataloger-file-vs-trivy',
            'plant': 'syfsyl',
            'issue': 1508,
            'tool': 'syft',
            'vs': 'trivy leftover leftover leftover fs scanner',
            'wrong': 'SYFT_FILE_METADATA_CATALOGER_ENABLED=false',
            'h1': 'SYFT_PACKAGE_CATALOGER_SCOPE=all-layers',
            'h2': 'syft packages --scope squashed',
            'fix': 'SYFT_FILE_METADATA_CATALOGER_ENABLED=true',
            'grep': 'SYFT_FILE_METADATA|CATALOGER',
            'bad': 'SYFT_FILE_METADATA_CATALOGER_ENABLED=false',
            'test': 'test_syft_file_cataloger',
        },
        {
            'slug': 'grype-only-fixed-vs-trivy',
            'plant': 'grysyl',
            'issue': 1509,
            'tool': 'grype',
            'vs': 'trivy leftover leftover leftover --ignore-unfixed',
            'wrong': 'GRYPE_ONLY_FIXED=true',
            'h1': 'GRYPE_FAIL_ON_SEVERITY=negligible',
            'h2': 'GRYPE_DB_AUTO_UPDATE=false',
            'fix': 'GRYPE_ONLY_FIXED=false',
            'grep': 'GRYPE_ONLY_FIXED|FAIL_ON_SEVERITY',
            'bad': 'GRYPE_ONLY_FIXED=true',
            'test': 'test_grype_only_fixed',
        },
        {
            'slug': 'opa-decision-logs-vs-kyverno',
            'plant': 'opasyl',
            'issue': 1510,
            'tool': 'opa',
            'vs': 'kyverno leftover leftover leftover audit reports',
            'wrong': 'decision_logs.console = false',
            'h1': 'decision_logs.reporting.min_delay_seconds = 3600',
            'h2': 'status.console = true',
            'fix': 'decision_logs.console = true',
            'grep': 'decision_logs|min_delay',
            'bad': 'decision_logs.console = false',
            'test': 'test_opa_decision_logs',
        },
        {
            'slug': 'cilium-hubble-relay-tls',
            'plant': 'cilsyl',
            'issue': 1511,
            'tool': 'cilium',
            'vs': 'kube-proxy leftover leftover leftover userspace',
            'wrong': 'hubble.relay.tls.server.enabled: false',
            'h1': 'kubeProxyReplacement: partial',
            'h2': 'hubble.enabled: false',
            'fix': 'hubble.relay.tls.server.enabled: true',
            'grep': 'hubble.relay.tls|kubeProxyReplacement',
            'bad': 'hubble.relay.tls.server.enabled: false',
            'test': 'test_cilium_hubble_relay_tls',
        },
        {
            'slug': 'linkerd-proxy-await-vs-istio',
            'plant': 'linsyl',
            'issue': 1512,
            'tool': 'linkerd',
            'vs': 'istio leftover leftover leftover holdApplicationUntilProxyStarts',
            'wrong': 'config.linkerd.io/proxy-await: disabled',
            'h1': 'config.linkerd.io/skip-inbound-ports: 443',
            'h2': 'config.alpha.linkerd.io/proxy-wait-before-exit-seconds: 0',
            'fix': 'config.linkerd.io/proxy-await: enabled',
            'grep': 'proxy-await|skip-inbound',
            'bad': 'proxy-await: disabled',
            'test': 'test_linkerd_proxy_await',
        },
        {
            'slug': 'vault-seal-wrap-vs-transit',
            'plant': 'vausyl',
            'issue': 1513,
            'tool': 'vault',
            'vs': 'transit leftover leftover leftover ciphertext unwrap skip',
            'wrong': 'seal_wrap = false',
            'h1': 'default_lease_ttl = "768h"',
            'h2': 'disable_mlock = true',
            'fix': 'seal_wrap = true',
            'grep': 'seal_wrap|default_lease_ttl',
            'bad': 'seal_wrap = false',
            'test': 'test_vault_seal_wrap',
        },
        {
            'slug': 'age-recipients-file-vs-sops',
            'plant': 'agesyl',
            'issue': 1514,
            'tool': 'age',
            'vs': 'sops leftover leftover leftover pgp leftover',
            'wrong': 'AGE_RECIPIENTS_FILE=/dev/null',
            'h1': 'SOPS_AGE_RECIPIENTS=',
            'h2': 'age-keygen -y leftover',
            'fix': 'AGE_RECIPIENTS_FILE=/etc/age/recipients.txt',
            'grep': 'AGE_RECIPIENTS_FILE|SOPS_AGE',
            'bad': 'AGE_RECIPIENTS_FILE=/dev/null',
            'test': 'test_age_recipients_file',
        },
        {
            'slug': 'restic-forget-keep-daily-vs-borg',
            'plant': 'ressyl',
            'issue': 1515,
            'tool': 'restic',
            'vs': 'borg leftover leftover leftover prune --keep-daily',
            'wrong': 'RESTIC_FORGET_KEEP_DAILY=1',
            'h1': 'RESTIC_FORGET_PRUNE=0',
            'h2': 'RESTIC_COMPRESSION=off',
            'fix': 'RESTIC_FORGET_KEEP_DAILY=14',
            'grep': 'RESTIC_FORGET_KEEP_DAILY|RESTIC_COMPRESSION',
            'bad': 'RESTIC_FORGET_KEEP_DAILY=1',
            'test': 'test_restic_keep_daily',
        },
        {
            'slug': 'kopia-compression-zstd-vs-restic',
            'plant': 'kopsyl',
            'issue': 1516,
            'tool': 'kopia',
            'vs': 'restic leftover leftover leftover compression off leftover',
            'wrong': 'KOPIA_COMPRESSION=none',
            'h1': 'KOPIA_PARALLEL=1',
            'h2': 'KOPIA_UPLOAD_SPEED_LIMIT=1',
            'fix': 'KOPIA_COMPRESSION=zstd',
            'grep': 'KOPIA_COMPRESSION|KOPIA_PARALLEL',
            'bad': 'KOPIA_COMPRESSION=none',
            'test': 'test_kopia_compression_zstd',
        },
)


def slugs() -> tuple[str, ...]:
    return tuple(plant["slug"] for plant in PLANTS)


def plant_at(index: int) -> Plant:
    """Return the plant at ``index`` (0..15). Raises ``SrlError`` if out of range."""

    if type(index) is not int or not 0 <= index < len(PLANTS):
        raise SrlError(f"unknown_plant_index: {index!r}")
    return PLANTS[index]


def plant_by_slug(slug: str) -> Plant:
    """Return the unique plant with ``slug``. Raises ``SrlError`` if unknown."""

    if type(slug) is not str or not slug:
        raise SrlError(f"unknown_plant: {slug!r}")
    for plant in PLANTS:
        if plant["slug"] == slug:
            return plant
    raise SrlError(f"unknown_plant: {slug!r}")
