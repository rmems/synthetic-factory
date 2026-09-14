#!/usr/bin/env python3
"""Write ntp-mill-unique-llll{23,24,25,26}.py + loop wrappers."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen15", ROOT / "experiments/_gen_ntp_llll15plus.py"
)
g = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(g)

S23 = [
    ("docker-layer", "dklr", "overlay2/layer", "docker layer"),
    ("buildah-containers", "bhct", "buildah/containers", "buildah containers"),
    ("podman-storage", "pdst", "podman/storage", "podman storage"),
    ("nerdctl-namespace", "ncns", "nerdctl/namespace", "nerdctl namespace"),
    ("kaniko-cache", "knch", "kaniko/cache", "kaniko cache"),
    ("buildkit-cache", "bkch2", "buildkit/cache", "buildkit cache"),
    ("img-cache", "imch", "img/cache", "img cache"),
    ("ko-cache", "koch", "ko/cache", "ko cache"),
    ("crane-layout", "crly", "crane/oci", "crane layout"),
    ("skopeo-dir", "skdr", "skopeo/dir", "skopeo dir"),
    ("oras-layout", "orly", "oras/oci", "oras layout"),
    ("compose-override", "cmov", "compose.override.yml", "compose override"),
    ("buildx-bake", "bxbk", "bake.json", "buildx bake"),
    ("containerd-io", "cdio", "containerd/io.containerd", "containerd io"),
    ("crio-storage", "crst2", "crio/storage", "crio storage"),
    ("runc-state", "rcst", "runc/state", "runc state"),
    ("nydus-cache", "nych", "nydus/cache", "nydus cache"),
    ("stargz-cache", "sgch", "stargz/cache", "stargz cache"),
    ("overlayfs-diff", "ovdf", "overlay/diff", "overlayfs diff"),
    ("umoci-layout", "umly", "umoci/oci", "umoci layout"),
    ("buildah-vfs", "bhvf", "buildah/vfs", "buildah vfs"),
    ("podman-tmp", "pdtm", "podman/tmp", "podman tmp"),
    ("docker-tmp", "dktm", "docker/tmp", "docker tmp"),
    ("kaniko-snapshot", "knsn", "kaniko/snapshot", "kaniko snapshot"),
    ("ko-sbom", "kosb", "ko.sbom.json", "ko sbom"),
    ("crane-index", "crix", "crane/index.json", "crane index"),
    ("skopeo-tls", "sktl", "skopeo/tls", "skopeo tls"),
    ("oras-blob", "orbl", "oras/blobs", "oras blob"),
    ("docker-plugin", "dkpl", "docker/plugins", "docker plugin"),
    ("compose-lock", "cmlk", "compose.lock", "compose lock"),
    ("containerd-snapshot", "cdsn", "containerd/snapshots", "containerd snapshot"),
    ("buildx-cache", "bxch", "buildx/cache", "buildx cache"),
]
L23 = [
    ("docker-log", "dklg", "docker.log", "docker log", "docker layer"),
    ("buildah-log", "bhlg", "buildah.log", "buildah log", "buildah containers"),
    ("podman-log", "pdlg", "podman.log", "podman log", "podman storage"),
    ("nerdctl-log", "nclg", "nerdctl.log", "nerdctl log", "nerdctl namespace"),
    ("kaniko-log", "knlg", "kaniko.log", "kaniko log", "kaniko cache"),
    ("buildkit-log", "bklg2", "buildkit.log", "buildkit log", "buildkit cache"),
    ("img-log", "imlg2", "img.log", "img log", "img cache"),
    ("ko-log", "kolg", "ko.log", "ko log", "ko cache"),
    ("crane-log", "crlg2", "crane.log", "crane log", "crane layout"),
    ("skopeo-log", "sklg", "skopeo.log", "skopeo log", "skopeo dir"),
    ("oras-log", "orlg", "oras.log", "oras log", "oras layout"),
    ("compose-log", "cmlg", "compose.log", "compose log", "compose override"),
    ("buildx-log", "bxlg", "buildx.log", "buildx log", "buildx bake"),
    ("containerd-log", "cdlg", "containerd.log", "containerd log", "containerd io"),
    ("crio-log", "crlg3", "crio.log", "crio log", "crio storage"),
    ("runc-log", "rclg", "runc.log", "runc log", "runc state"),
    ("nydus-log", "nylg", "nydus.log", "nydus log", "nydus cache"),
    ("stargz-log", "sglg2", "stargz.log", "stargz log", "stargz cache"),
    ("overlayfs-log", "ovlg", "overlay.log", "overlayfs log", "overlayfs diff"),
    ("umoci-log", "umlg", "umoci.log", "umoci log", "umoci layout"),
    ("buildah-tmp", "bhtm", "buildah/tmp", "buildah tmp", "buildah vfs"),
    ("podman-events", "pdev", "podman/events", "podman events", "podman tmp"),
    ("docker-events", "dkev", "docker/events", "docker events", "docker tmp"),
    ("kaniko-log2", "knl2", "kaniko/build.log", "kaniko build log", "kaniko snapshot"),
    ("ko-attest", "koat", "ko.intoto.json", "ko attest", "ko sbom"),
    ("crane-config", "crcf2", "crane/config.json", "crane config", "crane index"),
    ("skopeo-policy", "skpl", "skopeo/policy.json", "skopeo policy", "skopeo tls"),
    ("oras-manifest", "ormf", "oras/manifest.json", "oras manifest", "oras blob"),
    ("docker-network", "dknw", "docker/network", "docker network", "docker plugin"),
    ("compose-env", "cmen", ".env.compose.bak", "compose env", "compose lock"),
    ("containerd-meta", "cdmt", "containerd/metadata", "containerd meta", "containerd snapshot"),
    ("buildx-state", "bxst", "buildx/state", "buildx state", "buildx cache"),
]

S24 = [
    ("iptables-save", "ipts", "iptables.save", "iptables save"),
    ("nftables-conf", "nftc", "nftables.conf", "nftables conf"),
    ("coredns-db", "cddb", "coredns.db", "coredns db"),
    ("unbound-cache", "ubch", "unbound.cache", "unbound cache"),
    ("bind-journal", "bdjn", "named.jnl", "bind journal"),
    ("resolved-lease", "rsls", "resolved.lease", "resolved lease"),
    ("wireguard-conf", "wgcf", "wg0.conf.bak", "wireguard conf"),
    ("openvpn-status", "ovst", "openvpn-status.log", "openvpn status"),
    ("strongswan-conf", "sscf", "ipsec.conf.bak", "strongswan conf"),
    ("tailscale-state", "tsst", "tailscaled.state", "tailscale state"),
    ("zerotier-id", "ztid", "identity.secret", "zerotier id"),
    ("nebula-conf", "nbcf2", "nebula.yml.bak", "nebula conf"),
    ("caddy-data", "cydt", "caddy/data", "caddy data"),
    ("nginx-cache", "ngch", "nginx/cache", "nginx cache"),
    ("haproxy-map", "hpm", "haproxy.map", "haproxy map"),
    ("envoy-config", "encf", "envoy.yaml.bak", "envoy config"),
    ("traefik-acme", "tfac", "acme.json", "traefik acme"),
    ("varnish-vcl", "vavc", "default.vcl.bak", "varnish vcl"),
    ("squid-cache", "sqch", "squid/cache", "squid cache"),
    ("mitmproxy-flow", "mtfl", "mitmproxy.flow", "mitmproxy flow"),
    ("wireshark-pcap", "wspc", "capture.pcap", "wireshark pcap"),
    ("tcpdump-pcap", "tdpc", "tcpdump.pcap", "tcpdump pcap"),
    ("tshark-json", "tsjs", "tshark.json", "tshark json"),
    ("socat-log", "sotl", "socat.log", "socat log"),
    ("ncat-log", "nclg2", "ncat.log", "ncat log"),
    ("iperf-json", "ipjs", "iperf.json", "iperf json"),
    ("mtr-json", "mtjs", "mtr.json", "mtr json"),
    ("traceroute-log", "trlg2", "traceroute.log", "traceroute log"),
    ("keepalived-conf", "kvcf", "keepalived.conf.bak", "keepalived conf"),
    ("bird-conf", "brcf", "bird.conf.bak", "bird conf"),
    ("frr-conf", "frcf", "frr.conf.bak", "frr conf"),
    ("strongswan-log", "sslg", "charon.log", "strongswan log"),
]
L24 = [
    ("iptables-log", "iptl", "iptables.log", "iptables log", "iptables save"),
    ("nftables-log", "nftl", "nftables.log", "nftables log", "nftables conf"),
    ("coredns-log", "cdlg2", "coredns.log", "coredns log", "coredns db"),
    ("unbound-log", "ublg", "unbound.log", "unbound log", "unbound cache"),
    ("bind-log", "bdlg2", "named.log", "bind log", "bind journal"),
    ("resolved-log", "rslg", "resolved.log", "resolved log", "resolved lease"),
    ("wireguard-log", "wglg", "wg-quick.log", "wireguard log", "wireguard conf"),
    ("openvpn-log", "ovlg2", "openvpn.log", "openvpn log", "openvpn status"),
    ("strongswan-secrets", "sssc", "ipsec.secrets.bak", "strongswan secrets", "strongswan conf"),
    ("tailscale-log", "tslg", "tailscaled.log", "tailscale log", "tailscale state"),
    ("zerotier-log", "ztlg", "zerotier.log", "zerotier log", "zerotier id"),
    ("nebula-log", "nblg", "nebula.log", "nebula log", "nebula conf"),
    ("caddy-log", "cylg", "caddy.log", "caddy log", "caddy data"),
    ("nginx-log", "nglg", "nginx/access.log", "nginx log", "nginx cache"),
    ("haproxy-log", "hplg", "haproxy.log", "haproxy log", "haproxy map"),
    ("envoy-log", "enlg", "envoy.log", "envoy log", "envoy config"),
    ("traefik-log", "tflg", "traefik.log", "traefik log", "traefik acme"),
    ("varnish-log", "valg", "varnish.log", "varnish log", "varnish vcl"),
    ("squid-log", "sqlg", "squid/access.log", "squid log", "squid cache"),
    ("mitmproxy-log", "mtlg", "mitmproxy.log", "mitmproxy log", "mitmproxy flow"),
    ("wireshark-log", "wslg2", "wireshark.log", "wireshark log", "wireshark pcap"),
    ("tcpdump-log", "tdlg", "tcpdump.log", "tcpdump log", "tcpdump pcap"),
    ("tshark-log", "tslg2", "tshark.log", "tshark log", "tshark json"),
    ("socat-pid", "sotpid", "socat.pid", "socat pid", "socat log"),
    ("ncat-pid", "ncpid", "ncat.pid", "ncat pid", "ncat log"),
    ("iperf-log", "iplg", "iperf.log", "iperf log", "iperf json"),
    ("mtr-log", "mtlg2", "mtr.log", "mtr log", "mtr json"),
    ("traceroute-json", "trjs2", "traceroute.json", "traceroute json", "traceroute log"),
    ("keepalived-log", "kvlg", "keepalived.log", "keepalived log", "keepalived conf"),
    ("bird-log", "brlg", "bird.log", "bird log", "bird conf"),
    ("frr-log", "frlg", "frr.log", "frr log", "frr conf"),
    ("charon-pid", "chpid", "charon.pid", "charon pid", "strongswan log"),
]

S25 = [
    ("git-objects", "gtob", ".git/objects", "git objects"),
    ("git-index", "gtix", ".git/index", "git index"),
    ("git-reflog", "gtrl", ".git/logs/HEAD", "git reflog"),
    ("hg-store", "hgst", ".hg/store", "hg store"),
    ("svn-wc", "svwc", ".svn/wc.db", "svn wc"),
    ("bzr-branch", "bzbr", ".bzr/branch", "bzr branch"),
    ("fossil-repo", "fsrp", "folio.fossil", "fossil repo"),
    ("perforce-client", "pfcl", ".p4config", "perforce client"),
    ("tfs-workspace", "tfws", ".tf/workspace", "tfs workspace"),
    ("sapling-dirstate", "slds", ".sl/dirstate", "sapling dirstate"),
    ("jj-opstore", "jjop", ".jj/op_store", "jj opstore"),
    ("pijul-pristine", "pjpr", ".pijul/pristine", "pijul pristine"),
    ("darcs-patches", "dcpt", "_darcs/patches", "darcs patches"),
    ("monotone-db", "mtdb", "folio.mtn", "monotone db"),
    ("cvs-entries", "cven", "CVS/Entries", "cvs entries"),
    ("git-lfs-cache", "gtlc", ".git/lfs", "git lfs cache"),  # BAN git-lfs token!
    ("precommit-cache", "pcch", ".cache/pre-commit", "precommit cache"),
    ("lefthook-log", "lhlg", "lefthook.log", "lefthook log"),
    ("husky-log", "hslg", ".husky/_/husky.log", "husky log"),
    ("overcommit-log", "oclg", "overcommit.log", "overcommit log"),
    ("commitizen-log", "czlg", "commitizen.log", "commitizen log"),
    ("gitlint-log", "gllg", "gitlint.log", "gitlint log"),
    ("commitcheck-log", "cclg", "commit-check.log", "commitcheck log"),
    ("githooks-log", "ghlg", ".githooks/log", "githooks log"),
    ("gitfilter-refs", "gtfr", ".git/filter-repo", "gitfilter refs"),
    ("bfg-log", "bflg2", "bfg.log", "bfg log"),
    ("gitgc-log", "gtgc", ".git/gc.log", "gitgc log"),
    ("gitpack-log", "gtpk", ".git/objects/pack", "gitpack pack"),
    ("gitworktree", "gtwt", ".git/worktrees", "git worktree"),
    ("gitmodules-bak", "gtmb", ".gitmodules.bak", "gitmodules bak"),
    ("gitconfig-bak", "gtcb", ".git/config.bak", "gitconfig bak"),
    ("gitattributes-bak", "gtab", ".gitattributes.bak", "gitattributes bak"),
]
# git-lfs is a banned blob token! remove git-lfs-cache
S25[15] = ("prepush-log", "pplg", ".git/hooks/pre-push.log", "prepush log")
# wait S25 currently has precommit at 16, git-lfs at 15. Replace 15.

L25 = [
    ("git-config-orig", "gtco", ".git/config.orig", "git config orig", "git objects"),
    ("git-packed-refs", "gtpr", ".git/packed-refs", "git packed refs", "git index"),
    ("git-FETCH-HEAD", "gtfh", ".git/FETCH_HEAD", "git fetch head", "git reflog"),
    ("hg-cache", "hgch", ".hg/cache", "hg cache", "hg store"),
    ("svn-pristine", "svpr", ".svn/pristine", "svn pristine", "svn wc"),
    ("bzr-checkout", "bzco", ".bzr/checkout", "bzr checkout", "bzr branch"),
    ("fossil-wal", "fswl", "folio.fossil-wal", "fossil wal", "fossil repo"),
    ("perforce-tickets", "pftk", ".p4tickets", "perforce tickets", "perforce client"),
    ("tfs-cache", "tfch", ".tf/cache", "tfs cache", "tfs workspace"),
    ("sapling-treestate", "slts", ".sl/treestate", "sapling treestate", "sapling dirstate"),
    ("jj-working", "jjwk", ".jj/working_copy", "jj working", "jj opstore"),
    ("pijul-changes", "pjch", ".pijul/changes", "pijul changes", "pijul pristine"),
    ("darcs-prefs", "dcpr", "_darcs/prefs", "darcs prefs", "darcs patches"),
    ("monotone-keys", "mtky", "folio.mtn.keys", "monotone keys", "monotone db"),
    ("cvs-root", "cvr", "CVS/Root", "cvs root", "cvs entries"),
    ("prepush-bak", "ppbk", ".git/hooks/pre-push.bak", "prepush bak", "prepush log"),
    ("precommit-log", "pclg", "pre-commit.log", "precommit log", "precommit cache"),
    ("lefthook-yml", "lhyml", "lefthook.yml.bak", "lefthook yml", "lefthook log"),
    ("husky-precommit", "hspc", ".husky/pre-commit.bak", "husky precommit", "husky log"),
    ("overcommit-yml", "ocyml", ".overcommit.yml.bak", "overcommit yml", "overcommit log"),
    ("commitizen-json", "czjs", ".cz.json.bak", "commitizen json", "commitizen log"),
    ("gitlint-ini", "glini", ".gitlint.bak", "gitlint ini", "gitlint log"),
    ("commitcheck-json", "ccjs", "commit-check.json", "commitcheck json", "commitcheck log"),
    ("githooks-yml", "ghyml", ".githooks.yml.bak", "githooks yml", "githooks log"),
    ("gitfilter-log", "gtfl", "git-filter-repo.log", "gitfilter log", "gitfilter refs"),
    ("bfg-backup", "bfbk", "folio.git.bfg-report", "bfg backup", "bfg log"),
    ("gitgc-pack", "gtgp", ".git/objects/pack/pack-tmp", "gitgc pack", "gitgc log"),
    ("gitpack-idx", "gtpi", ".git/objects/pack/pack.idx", "gitpack idx", "gitpack pack"),
    ("gitworktree-log", "gtwl", ".git/worktrees/log", "git worktree log", "git worktree"),
    ("gitmodules-orig", "gtmo", ".gitmodules.orig", "gitmodules orig", "gitmodules bak"),
    ("gitconfig-orig", "gtcg", ".git/config.orig2", "gitconfig orig", "gitconfig bak"),
    ("gitattributes-orig", "gtao", ".gitattributes.orig", "gitattributes orig", "gitattributes bak"),
]

S26 = [
    ("prometheus-rules", "prrl", "prometheus/rules.yml", "prometheus rules"),
    ("alertmanager-silences", "amsil", "alertmanager/silences", "alertmanager silences"),
    ("grafana-db", "grdb", "grafana.db", "grafana db"),
    ("loki-index", "lkix", "loki/index", "loki index"),
    ("tempo-wal", "tpwl", "tempo/wal", "tempo wal"),
    ("jaeger-span", "jesp", "jaeger/spans", "jaeger span"),
    ("zipkin-store", "zkst", "zipkin/store", "zipkin store"),
    ("opentelemetry-col", "otcl", "otelcol.yaml.bak", "otelcol config"),
    ("vector-data", "vcdt", "vector-data-dir", "vector data"),
    ("fluentbit-db", "fbdb", "flb.db", "fluentbit db"),
    ("fluentd-buffer", "fdbf", "fluentd/buffer", "fluentd buffer"),
    ("filebeat-registry", "fbrg", "filebeat/registry", "filebeat registry"),
    ("metricbeat-data", "mbdt", "metricbeat/data", "metricbeat data"),
    ("logstash-queue", "lsqu", "logstash/queue", "logstash queue"),
    ("elasticsearch-ilm", "esil", "ilm-history.json", "elasticsearch ilm"),
    ("kibana-saved", "kbsd", "kibana/saved", "kibana saved"),
    ("datadog-conf", "ddcf", "datadog.yaml.bak", "datadog conf"),
    ("newrelic-conf", "nrcf", "newrelic.yml.bak", "newrelic conf"),
    ("sentry-conf", "stcf2", "sentry.conf.py.bak", "sentry conf"),
    ("rollbar-conf", "rbcf", "rollbar.json.bak", "rollbar conf"),
    ("bugsnag-conf", "bgcf", "bugsnag.json.bak", "bugsnag conf"),
    ("honeycomb-conf", "hncf", "honeycomb.json.bak", "honeycomb conf"),
    ("lightstep-conf", "lscf", "lightstep.json.bak", "lightstep conf"),
    ("dynatrace-conf", "dycf", "dynatrace.conf.bak", "dynatrace conf"),
    ("appoptics-conf", "aocf", "appoptics.json.bak", "appoptics conf"),
    ("splunk-db", "spdb", "splunk/db", "splunk db"),
    ("graylog-journal", "gljn", "graylog/journal", "graylog journal"),
    ("syslog-ng-conf", "sngc", "syslog-ng.conf.bak", "syslog-ng conf"),
    ("rsyslog-conf", "rscf", "rsyslog.conf.bak", "rsyslog conf"),
    ("journald-conf", "jdcf", "journald.conf.bak", "journald conf"),
    ("telegraf-conf", "tgcf", "telegraf.conf.bak", "telegraf conf"),
    ("collectd-conf", "clcf", "collectd.conf.bak", "collectd conf"),
]
L26 = [
    ("prometheus-tsdb", "prts", "prometheus/tsdb", "prometheus tsdb", "prometheus rules"),
    ("alertmanager-data", "amdt2", "alertmanager/data", "alertmanager data", "alertmanager silences"),
    ("grafana-plugins", "grpl", "grafana/plugins", "grafana plugins", "grafana db"),
    ("loki-chunks", "lkck", "loki/chunks", "loki chunks", "loki index"),
    ("tempo-blocks", "tpbl", "tempo/blocks", "tempo blocks", "tempo wal"),
    ("jaeger-badger", "jebd", "jaeger/badger", "jaeger badger", "jaeger span"),
    ("zipkin-log", "zklg", "zipkin.log", "zipkin log", "zipkin store"),
    ("opentelemetry-log", "otlg", "otelcol.log", "otelcol log", "otelcol config"),
    ("vector-log", "vclg", "vector.log", "vector log", "vector data"),
    ("fluentbit-log", "fblg2", "fluent-bit.log", "fluentbit log", "fluentbit db"),
    ("fluentd-log", "fdlg", "fluentd.log", "fluentd log", "fluentd buffer"),
    ("filebeat-log", "fblg3", "filebeat.log", "filebeat log", "filebeat registry"),
    ("metricbeat-log", "mblg", "metricbeat.log", "metricbeat log", "metricbeat data"),
    ("logstash-log", "lslg", "logstash.log", "logstash log", "logstash queue"),
    ("elasticsearch-log", "eslg", "elasticsearch.log", "elasticsearch log", "elasticsearch ilm"),
    ("kibana-log", "kblg", "kibana.log", "kibana log", "kibana saved"),
    ("datadog-log", "ddlg", "datadog.log", "datadog log", "datadog conf"),
    ("newrelic-log", "nrlg", "newrelic.log", "newrelic log", "newrelic conf"),
    ("sentry-log", "stlg3", "sentry.log", "sentry log", "sentry conf"),
    ("rollbar-log", "rblg2", "rollbar.log", "rollbar log", "rollbar conf"),
    ("bugsnag-log", "bglg", "bugsnag.log", "bugsnag log", "bugsnag conf"),
    ("honeycomb-log", "hnlg", "honeycomb.log", "honeycomb log", "honeycomb conf"),
    ("lightstep-log", "lslg2", "lightstep.log", "lightstep log", "lightstep conf"),
    ("dynatrace-log", "dylg", "dynatrace.log", "dynatrace log", "dynatrace conf"),
    ("appoptics-log", "aolg", "appoptics.log", "appoptics log", "appoptics conf"),
    ("splunk-log", "splg", "splunk.log", "splunk log", "splunk db"),
    ("graylog-log", "gllg2", "graylog.log", "graylog log", "graylog journal"),
    ("syslog-ng-log", "sngl", "syslog-ng.log", "syslog-ng log", "syslog-ng conf"),
    ("rsyslog-log", "rslg2", "rsyslog.log", "rsyslog log", "rsyslog conf"),
    ("journald-log", "jdlg", "journal", "journald log", "journald conf"),
    ("telegraf-log", "tglg2", "telegraf.log", "telegraf log", "telegraf conf"),
    ("collectd-log", "cllg", "collectd.log", "collectd log", "collectd conf"),
]


def main() -> None:
    # fix S25 git-lfs
    S25_fixed = list(S25)
    S25_fixed[15] = ("prepush-log", "pplg", ".git/hooks/pre-push.log", "prepush log")
    waves = ((23, S23, L23), (24, S24, L24), (25, S25_fixed, L25), (26, S26, L26))
    for n, S, L in waves:
        stems = [r[1] for r in S] + [r[1] for r in L]
        if len(stems) != len(set(stems)):
            dups = [x for x in stems if stems.count(x) > 1]
            raise SystemExit(f"dup stems wave {n}: {sorted(set(dups))}")
        slugs = [r[0] for r in S] + [r[0] for r in L]
        if len(slugs) != len(set(slugs)):
            raise SystemExit(f"dup names wave {n}: {sorted(set(x for x in slugs if slugs.count(x)>1))}")
        for name, *_ in S + L:
            blob = name
            if any(tok in blob for tok in ("html", "png", "svg", "matplotlib", "plotly", "dnsmasq", "git-lfs")):
                raise SystemExit(f"banned token in {n} {name}")
        g.write_wave(n, S, L)
    print("wrote mills 23-26")


if __name__ == "__main__":
    main()
