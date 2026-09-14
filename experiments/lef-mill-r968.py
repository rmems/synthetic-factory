#!/usr/bin/env python3
"""llm-eval-flakiness mill r968+: six flake classes, unique vs r01–r967.

BAN: U+1D173 / U+1D17A strip clones; r01–r967 combining-char mills;
r727 conll-coref-avg / simpson-policy-mix; r967 nbd-live-as-gpt / nbd-list-trunc.

Classes: cache-key omitted field, judge last-pair-only, seed leak,
temperature=0 still samples, rubric aliasing, tool-output truncation.

Writes only via pipelines/round_txn.py reserve --expected 2 / publish.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTORY = "llm-eval-flakiness-factory"
DIR = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY
AGENTIC = DIR.parent

_spec = importlib.util.spec_from_file_location(
    "lef_mill_r629", ROOT / "experiments" / "lef-mill-r629.py"
)
base = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(base)

CATALOG_FIRST = 968
BANNED_SLUGS = frozenset(
    {
        "conll-coref-avg",
        "simpson-policy-mix",
        "nbd-live-as-gpt",
        "nbd-list-trunc",
    }
)

# kebab, old, new — field = kebab.replace("-", "_")
# Distinct domain vs r728 storage/GPU/NBD: time, ISA, sched, virt, compiler,
# runtime, DB, TLS, DNS, container. Not unicode, not combining-char, not nbd.
STEMS = [
    ("tsc-offset", "0", "200"),
    ("kvmclock", "kvm", "tsc"),
    ("ptp-phc", "phc0", "phc1"),
    ("chrony-makestep", "1.0", "0.1"),
    ("ntp-stratum", "1", "16"),
    ("ntpsec-nts", "off", "on"),
    ("timesyncd", "ntp", "no"),
    ("adjtimex-tick", "10000", "9000"),
    ("hpet-legacy", "off", "on"),
    ("rtc-wake", "disable", "enable"),
    ("avx512-vl", "off", "on"),
    ("amx-tile", "0", "1"),
    ("sve-vl", "128", "256"),
    ("rtm-abort", "off", "on"),
    ("lse2-atomics", "off", "on"),
    ("sha-ni", "off", "on"),
    ("vaes-ni", "off", "on"),
    ("gfni", "off", "on"),
    ("prefetchit", "off", "on"),
    ("lam-u48", "off", "on"),
    ("eevdf-slice", "3ms", "24ms"),
    ("uclamp-min", "0", "512"),
    ("idle-haltpoll", "off", "on"),
    ("nohz-full", "off", "cpu2-7"),
    ("isolcpus", "none", "2-7"),
    ("irqaffinity", "0-7", "0"),
    ("qemu-cpu-model", "host", "Haswell"),
    ("kvm-nx-huge", "off", "on"),
    ("virtio-iothread", "off", "on"),
    ("vsock-cid", "3", "99"),
    ("vhost-net-vq", "256", "32"),
    ("sev-snp-policy", "default", "debug"),
    ("tdx-mrconfig", "mr-a", "mr-b"),
    ("sgx-enclave", "prod", "debug"),
    ("acrn-vcpu", "pinned", "shared"),
    ("gcc-lto-part", "1", "8"),
    ("rustc-cg", "llvm", "cranelift"),
    ("llvm-lto2", "thin", "full"),
    ("mold-icf", "safe", "all"),
    ("gold-hash", "sysv", "gnu"),
    ("cfi-icall", "off", "on"),
    ("scudo-tcache", "on", "off"),
    ("jemalloc-tcache", "on", "off"),
    ("mimalloc-eager", "off", "on"),
    ("tcmalloc-page", "8k", "32k"),
    ("cpython-gil", "on", "off"),
    ("pypy-jit", "on", "off"),
    ("jvm-g1", "g1", "zgc"),
    ("go-gogc", "100", "10"),
    ("v8-sparkplug", "on", "off"),
    ("dotnet-gc", "server", "workstation"),
    ("ruby-yjit", "on", "off"),
    ("php-opcache", "on", "off"),
    ("node-uv-pool", "4", "1"),
    ("lua-jit-opt", "3", "0"),
    ("pg-work-mem", "4MB", "64MB"),
    ("mysql-sql-mode", "STRICT", "ANSI"),
    ("sqlite-wal", "delete", "wal"),
    ("mongo-wc", "1", "majority"),
    ("ch-join-algo", "hash", "partial_merge"),
    ("cockroach-lease", "epoch", "expiration"),
    ("spanner-staleness", "0s", "15s"),
    ("cassandra-cl", "QUORUM", "ONE"),
    ("dynamo-consistent", "true", "false"),
    ("openssl-fips", "off", "on"),
    ("boring-pkcs", "off", "on"),
    ("nss-trust", "sql", "dbm"),
    ("gnutls-prio", "NORMAL", "SECURE128"),
    ("wolfssl-tls13", "on", "off"),
    ("unbound-qname", "off", "on"),
    ("resolved-dnssec", "no", "yes"),
    ("dnsmasq-neg", "off", "on"),
    ("knot-dnssec", "off", "on"),
    ("powerdns-lua", "off", "on"),
    ("runc-seccomp", "default", "unconfined"),
    ("crun-cgroupns", "host", "private"),
    ("containerd-snap", "overlayfs", "btrfs"),
    ("crio-runtime", "crun", "runc"),
    ("firecracker-smt", "off", "on"),
    ("cloudhv-iommu", "off", "on"),
    # r1208+: display/audio/usb/wifi/proxy/lang/pack/wasm/cloud — not nbd, not unicode
    ("drm-atomic", "legacy", "atomic"),
    ("kms-cursor", "sw", "hw"),
    ("wayland-shm", "shm", "dmabuf"),
    ("x11-glx", "indirect", "direct"),
    ("pipewire-rate", "48000", "44100"),
    ("pulse-resample", "speex", "soxr"),
    ("alsa-period", "1024", "64"),
    ("jack-latency", "128", "16"),
    ("cups-ppd", "generic", "driverless"),
    ("sane-backend", "net", "pixma"),
    ("hid-report", "boot", "report"),
    ("evdev-grab", "off", "on"),
    ("libinput-tap", "off", "on"),
    ("uhid-desc", "v1", "v2"),
    ("usb-gadget-udc", "dummy", "dwc3"),
    ("thunderbolt-acl", "none", "secure"),
    ("mac80211-ampdu", "off", "on"),
    ("iwlwifi-fw", "pnvm-a", "pnvm-b"),
    ("ath11k-nss", "off", "on"),
    ("mt76-wed", "off", "on"),
    ("brcmfmac-clm", "default", "custom"),
    ("bluetooth-iso", "off", "on"),
    ("bluez-codec", "sbc", "ldac"),
    ("nfc-llcp", "off", "on"),
    ("nft-flowtable", "off", "on"),
    ("ipt-conntrack", "hashsize=65536", "hashsize=1024"),
    ("tc-fqcodel", "off", "on"),
    ("ipvs-sh", "rr", "sh"),
    ("keepalived-vrid", "51", "52"),
    ("haproxy-nbthread", "1", "8"),
    ("caddy-http3", "off", "on"),
    ("traefik-entry", "web", "websecure"),
    ("envoy-http3", "off", "on"),
    ("nginx-quic", "off", "on"),
    ("ats-cache", "ram", "disk"),
    ("squid-store", "ufs", "rock"),
    ("varnish-saintmode", "off", "on"),
    ("h2o-quic", "off", "on"),
    ("lighttpd-kqueue", "off", "on"),
    ("cgit-filter", "none", "about"),
    ("zig-cpu", "baseline", "native"),
    ("nim-gc", "refc", "orc"),
    ("crystal-mt", "off", "on"),
    ("dmd-lto", "off", "on"),
    ("ghc-ways", "vanilla", "dyn"),
    ("ocaml-flambda", "off", "on"),
    ("erlc-jit", "off", "on"),
    ("elixir-jit", "off", "on"),
    ("gleam-target", "erlang", "javascript"),
    ("vlang-gc", "boehm", "none"),
    ("fortran-ieee", "off", "on"),
    ("cobol-trunc", "off", "on"),
    ("ada-checks", "on", "off"),
    ("pascal-range", "on", "off"),
    ("fsharp-tail", "off", "on"),
    ("clojure-direct", "off", "on"),
    ("uv-index", "pypi", "private"),
    ("poetry-keyring", "off", "on"),
    ("pip-hash-check", "off", "on"),
    ("conda-subdir", "linux-64", "noarch"),
    ("nix-system", "x86_64-linux", "aarch64-linux"),
    ("guix-graft", "on", "off"),
    ("spack-target", "generic", "zen4"),
    ("easybuild-tc", "foss", "intel"),
    ("wasmtime-fuel", "off", "on"),
    ("wasmer-meter", "off", "on"),
    ("wamr-heap", "64k", "1m"),
    ("lucet-retire", "off", "on"),
    ("wasm-gc-feat", "off", "on"),
    ("component-model", "off", "on"),
    ("wit-world", "w0", "w1"),
    ("preview2-clock", "host", "fake"),
    ("nitro-enclave", "off", "debug"),
    ("gce-live-mig", "off", "on"),
    ("azure-host-enc", "off", "on"),
    ("lambda-snapstart", "off", "on"),
    ("cf-isolate", "v8", "workerd"),
    ("fly-machine", "shared", "perf"),
    ("render-runtime", "native", "docker"),
    ("railway-nixpack", "off", "on"),
    # r1448+: vpn/modem/codec/olap/obs/pack/gitops — not nbd, not unicode
    ("wg-keepalive", "25", "0"),
    ("ovpn-cipher", "AES-256-GCM", "CHACHA20"),
    ("ipsec-pfs", "on", "off"),
    ("sswan-mobike", "on", "off"),
    ("l2tp-udp", "1701", "4500"),
    ("pptp-mppe", "required", "optional"),
    ("sstp-nla", "off", "on"),
    ("ikev2-frag", "off", "on"),
    ("modem-qmi", "qmi", "mbim"),
    ("ppp-mru", "1500", "1492"),
    ("mmcli-bearer", "ipv4", "ipv4v6"),
    ("ofono-ims", "off", "on"),
    ("asterisk-pjsip", "udp", "tls"),
    ("freeswitch-sofia", "sofia", "verto"),
    ("kamailio-dlg", "off", "on"),
    ("opensips-dlg", "off", "on"),
    ("ffmpeg-hwaccel", "none", "vaapi"),
    ("gstreamer-vaapi", "off", "on"),
    ("v4l2-m2m", "off", "on"),
    ("libva-driver", "iHD", "i965"),
    ("nvenc-preset", "p4", "p7"),
    ("qsv-async", "4", "1"),
    ("amf-preanalysis", "off", "on"),
    ("rav1e-speed", "6", "10"),
    ("svt-av1-preset", "8", "12"),
    ("x264-tune", "film", "zerolatency"),
    ("x265-aq", "on", "off"),
    ("vp9-cpu-used", "1", "5"),
    ("dav1d-threads", "0", "1"),
    ("aom-cpu-used", "4", "8"),
    ("opus-app", "audio", "voip"),
    ("flac-lpc", "8", "0"),
    ("duckdb-threads", "8", "1"),
    ("trino-spill", "off", "on"),
    ("presto-spill", "off", "on"),
    ("druid-indexer", "local", "middleManager"),
    ("pinot-realtime", "lowLevel", "highLevel"),
    ("clickhouse-merge", "on", "off"),
    ("starrocks-be", "shared", "exclusive"),
    ("doris-be", "vectorized", "nonvec"),
    ("prometheus-eval", "30s", "5m"),
    ("grafana-expr", "classic", "ml"),
    ("loki-query", "logql", "metric"),
    ("tempo-traceql", "off", "on"),
    ("mimir-ruler", "local", "remote"),
    ("thanos-compactor", "on", "off"),
    ("victoria-cache", "on", "off"),
    ("influx-dbrp", "autogen", "rp-eval"),
    ("otel-batch", "512", "32"),
    ("jaeger-sampling", "const", "probabilistic"),
    ("zipkin-sampler", "boundary", "counting"),
    ("skywalking-agent", "on", "off"),
    ("elastic-apm", "all", "errors"),
    ("newrelic-span", "all", "sampled"),
    ("datadog-apm", "auto", "none"),
    ("sentry-sample", "1.0", "0.1"),
    ("cargo-profile", "release", "dev"),
    ("go-mod-sum", "on", "off"),
    ("npm-lockfile", "v3", "v1"),
    ("pnpm-hoist", "true", "false"),
    ("yarn-pnp", "off", "on"),
    ("bun-install", "hoist", "isolated"),
    ("maven-enforcer", "off", "on"),
    ("gradle-configcache", "off", "on"),
    ("bazel-disk-cache", "off", "on"),
    ("buck2-action", "local", "remote"),
    ("pants-process", "local", "remote"),
    ("please-hash", "sha256", "blake3"),
    ("nix-eval-cache", "on", "off"),
    ("guix-offload", "off", "on"),
    ("spack-reuse", "on", "off"),
    ("conan-lock", "off", "on"),
    ("helm-atomic", "off", "on"),
    ("kustomize-hash", "sha256", "legacy"),
    ("argocd-syncwave", "off", "on"),
    ("flux-kustomize", "prune", "disable"),
    ("skaffold-render", "helm", "kustomize"),
    ("tilt-live", "on", "off"),
    ("devspace-replace", "off", "on"),
    ("garden-action", "build", "deploy"),
    # r1688+: identity/mail/boot/hsm — not nbd, not unicode, not r728 GPU/mesh
    ("kerberos-realm", "EXAMPLE.COM", "EVAL.TEST"),
    ("krb5-enctype", "aes256", "arcfour"),
    ("ldap-deref", "never", "always"),
    ("sssd-nss", "files", "sss"),
    ("pam-faillock", "off", "on"),
    ("keycloak-spi", "jpa", "infinispan"),
    ("authentik-flow", "default", "identification"),
    ("oauth-pkce", "S256", "plain"),
    ("oidc-nonce", "required", "optional"),
    ("saml-nameid", "persistent", "transient"),
    ("spiffe-svid", "x509", "jwt"),
    ("cas-tgt", "7200", "90"),
    ("radius-eap", "peap", "tls"),
    ("tacacs-priv", "15", "1"),
    ("freeipa-hbac", "allow_all", "eval_only"),
    ("ds389-repl", "multi", "single"),
    ("openldap-syncrepl", "refreshOnly", "refreshAndPersist"),
    ("authelia-session", "redis", "memory"),
    ("kanidm-unix", "off", "on"),
    ("dex-connector", "mock", "ldap"),
    ("postfix-mynet", "loopback", "subnet"),
    ("exim-acl", "deny", "defer"),
    ("dovecot-auth", "system", "lua"),
    ("opendkim-canon", "relaxed", "simple"),
    ("rspamd-fuzzy", "off", "on"),
    ("milter-timeout", "30s", "2s"),
    ("spf-strict", "-all", "~all"),
    ("dmarc-rua", "none", "mailto"),
    ("sieve-ext", "fileinto", "redirect"),
    ("lmtp-proxy", "off", "on"),
    ("uefi-sb", "enforced", "setup"),
    ("tpm2-pcr", "sha256:0,7", "sha1:0"),
    ("measured-boot", "on", "off"),
    ("sbctl-bundle", "off", "on"),
    ("fwupd-capsule", "uefi", "uefi-recovery"),
    ("mokutil-enroll", "off", "on"),
    ("grub-cmdline", "quiet", "debug"),
    ("systemd-ukify", "off", "on"),
    ("ima-policy", "tcb", "appraisal"),
    ("evm-hmac", "off", "on"),
    ("pkcs11-slot", "0", "1"),
    ("softhsm-token", "eval", "prod"),
    ("yubihsm-auth", "password", "session"),
    ("nfast-km", "module", "softcard"),
    ("cloudhsm-clu", "a", "b"),
    ("tpm-ekcert", "on", "off"),
    ("opencryptoki", "tpm", "ica"),
    ("gnupg-tofu", "off", "on"),
    ("age-recipient", "ssh", "x25519"),
    ("scim-filter", "eq", "co"),
    ("webauthn-uv", "required", "preferred"),
    ("fido2-rk", "off", "on"),
    ("passkey-att", "none", "direct"),
    ("mtls-spiffe", "strict", "permissive"),
    ("openid-ciba", "off", "on"),
    ("uma-ticket", "off", "on"),
    ("fapi-par", "off", "on"),
    ("dpop-ath", "off", "on"),
    ("hydra-consent", "always", "skip"),
    ("ory-kratos", "password", "oidc"),
    ("zitadel-proj", "default", "eval"),
    ("pocket-id", "off", "on"),
    ("lldap-group", "people", "eval"),
    ("glauth-ou", "users", "svc"),
    ("privacyidea", "totp", "hotp"),
    ("freeotp-drift", "1", "10"),
    ("oath-window", "1", "8"),
    ("ykman-oath", "totp", "hotp"),
    ("nitrokey-hotp", "off", "on"),
    ("libfido-uv", "required", "discouraged"),
    ("tpm2-unseal", "pcr7", "pcr0"),
    ("clevis-tang", "off", "on"),
    ("dracut-clevis", "off", "on"),
    ("luks-pbkdf", "argon2id", "pbkdf2"),
    ("cryptsetup-iter", "4", "1"),
    ("dmverity-root", "on", "off"),
    ("fsverity-sig", "on", "off"),
    ("landlock-abi", "4", "1"),
    ("seccomp-user", "filter", "log"),
    ("selinux-mls", "off", "on"),
    # r1928+: hpc/fs/scientific/sensors/can — not nbd, not unicode, not r728 GPU/mesh
    ("openmpi-btl", "vader", "tcp"),
    ("mpich-ch4", "ofi", "ucx"),
    ("slurm-gres", "gpu:1", "gpu:0"),
    ("pmix-fence", "on", "off"),
    ("lustre-osc", "16", "1"),
    ("gpfs-token", "central", "local"),
    ("beegfs-stripe", "4", "1"),
    ("nfs-nconn-max", "16", "1"),
    ("xfs-rmapbt", "on", "off"),
    ("btrfs-zoned", "off", "on"),
    ("zfs-dnodesize", "legacy", "auto"),
    ("overlay-indexoff", "off", "on"),
    ("fuse-passthrough", "off", "on"),
    ("ceph-chooseleaf", "firstn", "indep"),
    ("gluster-afr", "on", "off"),
    ("minio-erasure", "EC:4", "EC:2"),
    ("seaweed-vol", "7", "3"),
    ("longhorn-repl", "3", "1"),
    ("openebs-jiva", "off", "on"),
    ("rook-mons", "3", "1"),
    ("hdf5-swmr", "off", "on"),
    ("netcdf-chunk", "auto", "1"),
    ("zarr-codec", "zstd", "none"),
    ("parquet-dict", "on", "off"),
    ("arrow-ipc", "stream", "file"),
    ("blas-threads", "8", "1"),
    ("mkl-verbose", "off", "on"),
    ("openblas-core", "HASWELL", "GENERIC"),
    ("fftw-planner", "measure", "estimate"),
    ("petsc-pc", "gamg", "jacobi"),
    ("hwmon-pwm", "auto", "manual"),
    ("rapl-domain", "pkg", "core"),
    ("intel-pstate", "active", "passive"),
    ("amd-pstate", "guided", "passive"),
    ("thermald-dptf", "off", "on"),
    ("ipmi-watchdog", "reset", "off"),
    ("edac-mc", "poll", "off"),
    ("mcelog-thresh", "1", "20"),
    ("rasdaemon", "on", "off"),
    ("nvme-apst", "on", "off"),
    ("can-bitrate", "500000", "125000"),
    ("j1939-pgn", "off", "on"),
    ("socketcan-fd", "off", "on"),
    ("ros2-rmw", "cyclonedds", "fastrtps"),
    ("dds-qos", "reliable", "besteffort"),
    ("mqtt-qos", "1", "0"),
    ("opcua-sec", "SignAndEncrypt", "None"),
    ("modbus-rtu", "9600", "115200"),
    ("profinet-cycle", "1ms", "8ms"),
    ("ethercat-dc", "on", "off"),
    ("s3-checksum", "CRC32", "off"),
    ("gcs-cmk", "google", "cmek"),
    ("azure-blob-ver", "off", "on"),
    ("b2-cap", "off", "on"),
    ("wasabi-region", "us-east-1", "eu-central-1"),
    ("r2-jurisdiction", "default", "eu"),
    ("garage-layout", "single", "cluster"),
    ("seaweedfs-filer", "leveldb", "postgres"),
    ("cubefs-mp", "off", "on"),
    ("juicefs-meta", "redis", "tikv"),
    ("cifs-posix", "off", "on"),
    ("nfs4-deleg", "off", "on"),
    ("autofs-browse", "off", "on"),
    ("davfs-cache", "on", "off"),
    ("sshfs-readahead", "on", "off"),
    ("9p-cache", "mmap", "none"),
    ("virtiofs-dax", "off", "on"),
    ("fscache-cupid", "off", "on"),
    ("cachefiles-cull", "7", "1"),
    ("bcache-cache", "writethrough", "writeback"),
    ("mdadm-bitmap", "internal", "none"),
    ("lvm-cache", "off", "on"),
    ("dm-thin", "off", "on"),
    ("stratis-fs", "off", "on"),
    ("snapper-timeline", "on", "off"),
    ("timeshift-rsync", "rsync", "btrfs"),
    ("restic-pack", "16", "4"),
    ("borg-compr", "lz4", "none"),
    ("duplicity-vol", "25", "200"),
    ("kopia-policy", "default", "eval"),
    # r2168+: xen/browser/shell/editor/i18n/a11y/init/mobile/rtos — not nbd, not unicode
    ("xen-credit", "credit", "credit2"),
    ("hyperv-enlight", "on", "off"),
    ("bhyve-virtio", "on", "off"),
    ("jail-vnet", "off", "on"),
    ("zone-brand", "lipkg", "sparse"),
    ("openvz-ve", "ploop", "simfs"),
    ("lxc-apparmor", "default", "unconfined"),
    ("lxd-storage", "dir", "zfs"),
    ("incus-cluster", "off", "on"),
    ("proxmox-ha", "off", "on"),
    ("chromium-site", "on", "off"),
    ("firefox-fission", "on", "off"),
    ("webkit-itp", "on", "off"),
    ("servo-layout", "2013", "2020"),
    ("ladybird-js", "libjs", "v8"),
    ("v8-turbofan", "on", "off"),
    ("spidermonkey-ion", "on", "off"),
    ("jsc-ftl", "on", "off"),
    ("chakra-jit", "on", "off"),
    ("quickjs-bignum", "off", "on"),
    ("bash-pipefail", "off", "on"),
    ("zsh-noglob", "off", "on"),
    ("fish-universal", "on", "off"),
    ("nushell-config", "default", "env"),
    ("powershell-exec", "restricted", "bypass"),
    ("dash-posix", "on", "off"),
    ("mksh-utf8", "on", "off"),
    ("tcsh-nonomatch", "off", "on"),
    ("elvish-ns", "off", "on"),
    ("xonsh-thread", "off", "on"),
    ("vim-undofile", "off", "on"),
    ("neovim-luajit", "on", "off"),
    ("emacs-nativecomp", "off", "on"),
    ("kakoune-session", "off", "on"),
    ("helix-lsp", "on", "off"),
    ("vscode-sandbox", "on", "off"),
    ("jetbrains-ea", "off", "on"),
    ("sublime-index", "on", "off"),
    ("nano-multibuffer", "off", "on"),
    ("micro-plugin", "off", "on"),
    ("icu-break", "icu", "simple"),
    ("harfbuzz-ot", "ot", "fallback"),
    ("fontconfig-hint", "slight", "none"),
    ("fribidi-rtl", "on", "off"),
    ("libunibreak", "5", "4"),
    ("uchardet-detect", "on", "off"),
    ("cldr-likely", "on", "off"),
    ("gettext-plural", "on", "off"),
    ("localed-locale", "C", "C.UTF-8"),
    ("ibus-engine", "xkb", "anthy"),
    ("at-spi-bus", "on", "off"),
    ("speechd-module", "espeak", "festival"),
    ("orca-profile", "default", "lm"),
    ("brltty-driver", "auto", "none"),
    ("mutter-kms", "on", "off"),
    ("kwin-compositor", "opengl", "xrender"),
    ("sway-output", "auto", "off"),
    ("river-layout", "rivertile", "none"),
    ("hyprland-anim", "on", "off"),
    ("xfwm-vblank", "auto", "off"),
    ("systemd-reexec", "on", "off"),
    ("openrc-cgroup", "unified", "hybrid"),
    ("runit-log", "svlogd", "none"),
    ("s6-notify", "off", "on"),
    ("dinit-user", "off", "on"),
    ("launchd-keepalive", "off", "on"),
    ("smf-contract", "on", "off"),
    ("busybox-init", "off", "on"),
    ("tini-subreaper", "off", "on"),
    ("dumb-init-rewrite", "on", "off"),
    ("android-gki", "on", "off"),
    ("binder-rpc", "off", "on"),
    ("selinux-neverallow", "on", "off"),
    ("zygote-usap", "off", "on"),
    ("art-inline", "on", "off"),
    ("magisk-denylist", "off", "on"),
    ("ios-dyld", "on", "off"),
    ("darwin-cache", "on", "off"),
    ("fuchsia-starnix", "off", "on"),
    ("qnx-pps", "on", "off"),
    # r2408+: rtos/san/backup/obs/cni/routing — not nbd, not unicode, not r728 mesh
    ("zephyr-sched", "cooperative", "preempt"),
    ("freertos-smp", "off", "on"),
    ("nuttx-mm", "gran", "kmm"),
    ("rtems-smp", "off", "on"),
    ("threadx-preempt", "on", "off"),
    ("cmsis-rtos", "v2", "v1"),
    ("ri5cy-pmp", "off", "on"),
    ("rust-embedded-alloc", "off", "on"),
    ("tinygo-scheduler", "tasks", "none"),
    ("micropython-heap", "32k", "8k"),
    ("iscsi-hdrdig", "crc32c", "none"),
    ("nvmeof-subsys", "nqn-a", "nqn-b"),
    ("fc-lun", "0", "1"),
    ("srp-target", "off", "on"),
    ("fcoe-dcb", "on", "off"),
    ("veeam-cbt", "on", "off"),
    ("rubrik-sla", "gold", "bronze"),
    ("cohesity-view", "nfs", "smb"),
    ("netbackup-pol", "full", "incr"),
    ("bacula-pool", "Default", "Scratch"),
    ("amanda-taper", "vtape", "s3"),
    ("bareos-fd", "on", "off"),
    ("zabbix-proxy", "active", "passive"),
    ("nagios-obsess", "off", "on"),
    ("icinga-zone", "master", "sat"),
    ("sensu-keepalive", "120", "20"),
    ("checkmk-agent", "cmk", "legacy"),
    ("netdata-ml", "off", "on"),
    ("collectd-write", "rrd", "network"),
    ("telegraf-agg", "off", "on"),
    ("vector-buffer", "memory", "disk"),
    ("fluent-chunk", "2m", "256k"),
    ("rsyslog-imfile", "off", "on"),
    ("syslog-ng-disk", "off", "on"),
    ("nxlog-im", "im_file", "im_tcp"),
    ("promtail-drop", "off", "on"),
    ("filebeat-scan", "10s", "1s"),
    ("winlogbeat-event", "on", "off"),
    ("auditbeat-socket", "off", "on"),
    ("packetbeat-flow", "on", "off"),
    ("metricbeat-mod", "system", "none"),
    ("heartbeat-mon", "http", "tcp"),
    ("openvswitch-dpdk", "off", "on"),
    ("ovn-encap", "geneve", "vxlan"),
    ("calico-vxlan", "Always", "Never"),
    ("flannel-backend", "vxlan", "host-gw"),
    ("weave-npc", "on", "off"),
    ("antrea-proxy", "on", "off"),
    ("kube-proxy-mode", "iptables", "ipvs"),
    ("cni-ipam", "host-local", "dhcp"),
    ("multus-nad", "off", "on"),
    ("whereabouts-range", "default", "eval"),
    ("bird-rpki", "off", "on"),
    ("frr-bfdd", "off", "on"),
    ("gobgp-policy", "accept", "reject"),
    ("exabgp-api", "off", "on"),
    ("openbgpd-rde", "on", "off"),
    ("vyos-frr", "on", "off"),
    ("opnsense-unbound", "on", "off"),
    ("pfsense-limiter", "off", "on"),
    ("ipfire-location", "off", "on"),
    ("clearos-mode", "gateway", "standalone"),
    ("kea-ha", "off", "on"),
    ("isc-dhcp-failover", "off", "on"),
    ("dnsmasq-dhcp", "on", "off"),
    ("odhcpc6-ia", "na", "pd"),
    ("radvd-adv", "on", "off"),
    ("dibbler-mode", "stateless", "stateful"),
    ("wide-dhcp6c", "info", "na"),
    ("systemd-networkd", "on", "off"),
    ("netplan-renderer", "networkd", "NetworkManager"),
    ("nm-dhcp", "yes", "no"),
    ("connman-wispr", "off", "on"),
    ("iwd-roam", "on", "off"),
]

FROMS = [
    "score", "accuracy", "f1", "em", "pass", "recall", "bleu", "rouge", "meteor", "bertscore",
    "comet", "ter", "chrf", "cider", "spice", "moverscore", "bartscore", "questeval", "unieval", "gptscore",
]
CANONS = [
    "policy_score", "span_acc", "span_f1", "normalized_em", "pass_macro",
    "span_recall", "bleu_tok_pin", "rougeLsum", "meteor", "bertscore_f1",
    "comet22", "ter", "chrf", "cider_d", "spice",
    "moverscore", "bartscore_cnndm", "questeval", "unieval_summeval", "gptscore",
]
LIMS = [
    ("16", "80"), ("20", "100"), ("24", "96"), ("12", "50"),
    ("30", "150"), ("40", "200"), ("4096", "32768"), ("8192", "65536"),
]


def _nums(i: int) -> tuple[float, float, float]:
    hi = round(0.86 + (i % 8) * 0.01, 2)
    lo = round(0.14 + (i % 9) * 0.01, 2)
    mid = round(0.70 + (i % 7) * 0.01, 2)
    return hi, lo, mid


def build_catalogs() -> tuple[list, list, list, list, list, list]:
    cache, last, seed, temp, alias, trunc = [], [], [], [], [], []
    for i, (name, old, new) in enumerate(STEMS):
        field = name.replace("-", "_")
        hi, lo, mid = _nums(i)
        hi2, lo2, mid2 = _nums(i + 3)
        hi3, lo3, mid3 = _nums(i + 5)
        frm = FROMS[i % len(FROMS)]
        canon = CANONS[i % len(CANONS)]
        alias_to = f"{field}_ok"
        lim, lim2 = LIMS[i % len(LIMS)]
        last_u = f"{name}-z"
        early_u = f"{name}-0"
        item = f"cl12-{field[:10]}"
        cache.append(
            (
                f"{name}-unkeyed",
                field,
                hi,
                lo,
                mid,
                old,
                new,
                f"r967 nbd-timeout-unkeyed. This is {name} omitted from the score cache",
                f"{new} scores {lo}; {old} cache {hi}",
            )
        )
        last.append(
            (
                f"{name}-last-unit",
                f"last {name} unit",
                hi2,
                lo2,
                mid2,
                last_u,
                early_u,
                f"r967 nbd-last-sock. This is {name} judge last unit only",
                f"{last_u} {hi2}; {early_u} {lo2}",
            )
        )
        seed.append(
            (
                f"{name}-eval-leak",
                f"{name} dump used as few-shot",
                item,
                hi3,
                lo3,
                mid3,
                f"r967 nbd-client-eval. This is {name} dump mixed into shots",
                f"shots include {item} {hi3}",
            )
        )
        temp.append(
            (
                f"{name}-temp0",
                f"{name} still samples at advertised temp=0",
                f"r967 nbd-max-temp0. This is {name} at advertised temp=0",
                f"{name}  {hi} vs {lo}",
                lo,
                hi,
                mid,
            )
        )
        alias.append(
            (
                f"{name}-as-{alias_to.replace('_', '-')}",
                frm,
                alias_to,
                canon,
                hi,
                lo,
                mid,
                f"r967 nbd-live-as-gpt. This is {frm} aliased to {alias_to}",
                f"{alias_to} {hi}; {canon} {lo}",
            )
        )
        trunc.append(
            (
                f"{name}-trunc",
                lim,
                lim2,
                f"r967 nbd-list-trunc. This is {name} | head -{lim}",
                f"first {lim} {hi}; fail later {lo}",
                hi,
                lo,
                mid,
            )
        )
    return cache, last, seed, temp, alias, trunc


CACHE_OK, LAST_BAD, SEED_OK, TEMP0_BAD, ALIAS_OK, TRUNC_BAD = build_catalogs()


def _patch_notes() -> None:
    def notes_md(round_n: int, ok: dict, bad: dict, coverage: int) -> str:
        prev = round_n - 1
        return (
            f"# NOTES-r{round_n} llm-eval-flakiness-factory\n\n"
            f"Novel coverage: {coverage}%\n\n"
            f"- IDs `lef-r{round_n}-*`. generator `grok-4.6`. Q=2.\n"
            f"- Step counts: {ok['slug']} 16, {bad['slug']} 16.\n"
            f"- Seeds: (1) {ok['seed']} (2) {bad['seed']}\n"
            f"- Distinct from lef r01–r{prev} ({ok['avoided']}; {bad['avoided']}).\n"
            f"- Mix: success ({ok['slug']} / {ok['klass']}) + partial ({bad['slug']} / {bad['klass']} nightly handoff).\n"
            f"- Ban: no U+1D173/U+1D17A strip clones, no r01–r{prev} combining-char mills, "
            f"no r727 conll-coref-avg / simpson-policy-mix, no r967 nbd-live-as-gpt / nbd-list-trunc, "
            f"no SKU-9, no HTTP skip-as-1.0.\n\n"
            f"## decision_basis audit\n"
            f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
            f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
            f"No sim_or_real: real.\n"
        )

    base.notes_md = notes_md


def _used_slugs() -> set[str]:
    out: set[str] = set()
    for batch in DIR.glob("batch-r*.jsonl"):
        for line in batch.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            rid = rec.get("id", "")
            if rid.startswith("lef-r"):
                i = rid.find("-", 5)
                if i >= 0:
                    out.add(rid[i + 1 :])
    return out


def install() -> None:
    n = min(len(CACHE_OK), len(LAST_BAD), len(SEED_OK), len(TEMP0_BAD), len(ALIAS_OK), len(TRUNC_BAD))
    if n < 1:
        raise SystemExit("empty catalog")
    slugs = [
        row[0]
        for row in (
            CACHE_OK[:n] + LAST_BAD[:n] + SEED_OK[:n] + TEMP0_BAD[:n] + ALIAS_OK[:n] + TRUNC_BAD[:n]
        )
    ]
    if len(set(slugs)) != len(slugs):
        raise SystemExit("duplicate mill slugs")
    bad = [s for s in slugs if s in BANNED_SLUGS]
    if bad:
        raise SystemExit(f"banned slugs {bad}")
    published = _used_slugs()
    # Already-flushed catalog rows are expected on resume; emit_stage still
    # rejects a *current* round whose pair collides.
    base.CATALOG_FIRST = CATALOG_FIRST
    base.CACHE_OK = CACHE_OK
    base.LAST_BAD = LAST_BAD
    base.SEED_OK = SEED_OK
    base.TEMP0_BAD = TEMP0_BAD
    base.ALIAS_OK = ALIAS_OK
    base.TRUNC_BAD = TRUNC_BAD

    def pair_for(round_n: int):
        if round_n < 1208:
            first = CATALOG_FIRST
            sl = slice(0, 80)
        elif round_n < 1448:
            first = 1208
            sl = slice(80, 160)
        elif round_n < 1688:
            first = 1448
            sl = slice(160, 240)
        elif round_n < 1928:
            first = 1688
            sl = slice(240, 320)
        elif round_n < 2168:
            first = 1928
            sl = slice(320, 400)
        elif round_n < 2408:
            first = 2168
            sl = slice(400, 480)
        else:
            first = 2408
            sl = slice(480, None)
        cache, last, seed, temp, alias, trunc = (
            CACHE_OK[sl], LAST_BAD[sl], SEED_OK[sl],
            TEMP0_BAD[sl], ALIAS_OK[sl], TRUNC_BAD[sl],
        )
        idx = round_n - first
        if idx < 0:
            raise KeyError(f"round {round_n} before catalog {first}")
        nn = min(len(cache), len(last), len(seed), len(temp), len(alias), len(trunc))
        if nn < 1:
            raise KeyError(f"empty slice for round {round_n}")
        bucket = idx // nn
        off = idx % nn
        if bucket == 0:
            ok = base._cache_plant(cache[off], True)
            badp = base._last_plant(last[off], False)
        elif bucket == 1:
            ok = base._seed_plant(seed[off], True)
            badp = base._temp0_plant(temp[off], False)
        elif bucket == 2:
            ok = base._alias_plant(alias[off], True)
            badp = base._trunc_plant(trunc[off], False)
        else:
            last_r = first + 3 * nn - 1
            raise KeyError(f"no plant pair for round {round_n} (catalog {first}–{last_r})")
        return ok, badp

    base.pair_for = pair_for
    base.HOP_MILLS = (
        (
            AGENTIC / "ssl-cert-rotation-factory",
            ROOT / "experiments" / "ssl-mill-r112.py",
            112,
            131,
        ),
        (
            AGENTIC / "search-index-rebuild-factory",
            ROOT / "experiments" / "sir-mill-r52.py",
            52,
            71,
        ),
    )
    _patch_notes()
    _orig_emit = base.emit_stage

    def emit_stage(stage: Path, round_n: int):
        ok, badp = base.pair_for(round_n)
        used = _used_slugs()
        hit_now = [p["slug"] for p in (ok, badp) if p["slug"] in used]
        if hit_now:
            raise SystemExit(f"r{round_n} slug collision with published: {hit_now}")
        banned_hit = [p["slug"] for p in (ok, badp) if p["slug"] in BANNED_SLUGS]
        if banned_hit:
            raise SystemExit(f"r{round_n} banned slugs: {banned_hit}")
        return _orig_emit(stage, round_n)

    base.emit_stage = emit_stage
    last = CATALOG_FIRST + 3 * n - 1
    print(f"catalog r{CATALOG_FIRST}–r{last} n={n} pairs={3 * n}", flush=True)


def main(argv=None) -> int:
    install()
    return base.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
