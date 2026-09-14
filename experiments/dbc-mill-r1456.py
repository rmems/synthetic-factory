#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1456+. Observability × MEI/RAPL leftovers.

NEW unique-pair catalog after r1408 graph/UBI.
BAN prior DBC catalogs, r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN, harbor-pin, leftover×sysctl.
17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r1408", HERE / "dbc-mill-r1408.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "neo4j-server-cache",
    "ubi-core-leftover",
    "jena-fuseki-cache",
    "ubi-fastmap-leftover",
)

_CRYPTO = [
    ("prometheus-bin-cache", "PROMETHEUS_HOME", "prometheus", "2.54.1", "3.2.1", "etc/prometheus/prometheus.yml", "28MB"),
    ("grafana-server-cache", "GF_PATHS_HOME", "grafana-server", "11.1.4", "11.5.2", "conf/defaults.ini", "36MB"),
    ("loki-bin-cache", "LOKI_CONFIG", "loki", "3.1.1", "3.4.2", "etc/loki/loki.yaml", "18MB"),
    ("tempo-bin-cache", "TEMPO_CONFIG", "tempo", "2.6.1", "2.7.2", "etc/tempo/tempo.yaml", "16MB"),
    ("jaeger-all-in-one-cache", "JAEGER_HOME", "jaeger-all-in-one", "1.60.0", "1.67.0", "etc/jaeger/jaeger.yaml", "22MB"),
    ("zipkin-server-cache", "ZIPKIN_HOME", "zipkin", "3.4.1", "3.4.3", "config.yml", "14MB"),
    ("otelcol-cache", "OTELCOL_CONFIG", "otelcol", "0.108.0", "0.122.0", "etc/otelcol/config.yaml", "24MB"),
    ("thanos-bin-cache", "THANOS_HOME", "thanos", "0.36.1", "0.37.2", "etc/thanos/thanos.yml", "20MB"),
    ("mimir-bin-cache", "MIMIR_CONFIG", "mimir", "2.13.1", "2.15.0", "etc/mimir/mimir.yaml", "26MB"),
    ("alloy-bin-cache", "ALLOY_CONFIG", "alloy", "1.3.3", "1.7.1", "etc/alloy/config.alloy", "18MB"),
    ("victoriametrics-cache", "VM_HOME", "victoria-metrics", "1.102.1", "1.110.0", "etc/victoria-metrics/flags", "12MB"),
    ("alertmanager-cache", "ALERTMANAGER_CONFIG", "alertmanager", "0.27.0", "0.28.1", "etc/alertmanager/alertmanager.yml", "8MB"),
    ("promtail-cache", "PROMTAIL_CONFIG", "promtail", "3.1.1", "3.4.2", "etc/promtail/promtail.yaml", "10MB"),
    ("node-exporter-cache", "NODE_EXPORTER_HOME", "node_exporter", "1.8.2", "1.9.0", "share/node_exporter/node_exporter.md", "6MB"),
    ("blackbox-exporter-cache", "BLACKBOX_EXPORTER_CONFIG", "blackbox_exporter", "0.25.0", "0.26.0", "etc/blackbox/blackbox.yml", "5MB"),
    ("pushgateway-cache", "PUSHGATEWAY_HOME", "pushgateway", "1.9.0", "1.11.0", "share/pushgateway/pushgateway.md", "4MB"),
    ("karma-ui-cache", "KARMA_CONFIG", "karma", "0.121", "0.121-post", "etc/karma.yaml", "7MB"),
    ("grafana-agent-cache", "AGENT_CONFIG", "grafana-agent", "0.43.3", "0.44.2", "etc/grafana-agent/agent.yaml", "15MB"),
    ("pyroscope-cache", "PYROSCOPE_CONFIG", "pyroscope", "1.7.1", "1.11.0", "etc/pyroscope/config.yml", "14MB"),
    ("phlare-cache", "PHLARE_CONFIG", "phlare", "1.0.0", "1.0.0-post", "etc/phlare/config.yaml", "9MB"),
    ("cortex-bin-cache", "CORTEX_CONFIG", "cortex", "1.18.1", "1.19.0", "etc/cortex/cortex.yaml", "17MB"),
    ("prometheus-operator-cache", "PROM_OPERATOR_HOME", "operator", "0.76.1", "0.80.1", "etc/prometheus-operator/crd", "11MB"),
    ("kiali-cache", "KIALI_CONFIG", "kiali", "1.89.0", "2.7.1", "etc/kiali/config.yaml", "13MB"),
    ("jaeger-collector-cache", "JAEGER_COLLECTOR_HOME", "jaeger-collector", "1.60.0", "1.67.0", "etc/jaeger/collector.yaml", "10MB"),
    ("jaeger-query-cache", "JAEGER_QUERY_HOME", "jaeger-query", "1.60.0", "1.67.0", "etc/jaeger/query.yaml", "9MB"),
    ("otelcol-contrib-cache", "OTELCOL_CONTRIB_CONFIG", "otelcol-contrib", "0.108.0", "0.122.0", "etc/otelcol-contrib/config.yaml", "32MB"),
    ("vector-obs-cache", "VECTOR_CONFIG", "vector", "0.41.1", "0.46.1", "etc/vector/obs.yaml", "28MB"),
    ("fluent-bit-obs-cache", "FLUENT_BIT_CONF", "fluent-bit", "3.1.7", "4.0.3", "etc/fluent-bit/obs.conf", "10MB"),
    ("grafana-loki-canary-cache", "LOKI_CANARY_HOME", "loki-canary", "3.1.1", "3.4.2", "share/loki/canary.md", "3MB"),
    ("prometheus-amtool-cache", "AMTOOL_HOME", "amtool", "0.27.0", "0.28.1", "share/alertmanager/amtool.md", "2MB"),
    ("promtool-cache", "PROMTOOL_HOME", "promtool", "2.54.1", "3.2.1", "share/prometheus/promtool.md", "4MB"),
    ("mimirtool-cache", "MIMIRTOOL_HOME", "mimirtool", "2.13.1", "2.15.0", "share/mimir/mimirtool.md", "5MB"),
    ("thanos-query-cache", "THANOS_QUERY_HOME", "thanos", "0.36.1", "0.37.2", "etc/thanos/query.yml", "6MB"),
    ("thanos-store-cache", "THANOS_STORE_HOME", "thanos", "0.36.1", "0.37.2", "etc/thanos/store.yml", "6MB"),
    ("grafana-cli-cache", "GF_PATHS_PLUGINS", "grafana-cli", "11.1.4", "11.5.2", "bin/grafana-cli", "3MB"),
    ("prometheus-snmp-exporter-cache", "SNMP_EXPORTER_CONFIG", "snmp_exporter", "0.26.0", "0.27.0", "etc/snmp_exporter/snmp.yml", "7MB"),
    ("process-exporter-cache", "PROCESS_EXPORTER_CONFIG", "process-exporter", "0.8.2", "0.8.4", "etc/process-exporter/config.yml", "3MB"),
    ("cadvisor-cache", "CADVISOR_HOME", "cadvisor", "0.49.1", "0.52.1", "share/cadvisor/cadvisor.md", "8MB"),
    ("kube-state-metrics-cache", "KSM_HOME", "kube-state-metrics", "2.13.0", "2.15.0", "share/kube-state-metrics/ksm.md", "6MB"),
    ("prometheus-adapter-cache", "PROM_ADAPTER_CONFIG", "prometheus-adapter", "0.12.0", "0.12.0-post", "etc/adapter/config.yaml", "5MB"),
    ("opentelemetry-operator-cache", "OTEL_OPERATOR_HOME", "otel-operator", "0.108.0", "0.122.0", "etc/otel-operator/crd", "9MB"),
    ("tempo-query-cache", "TEMPO_QUERY_HOME", "tempo-query", "2.6.1", "2.7.2", "etc/tempo/query.yaml", "4MB"),
    ("grafana-image-renderer-cache", "GF_RENDERER_PLUGIN_DIR", "grafana-image-renderer", "3.11.4", "3.12.3", "plugin.json", "12MB"),
    ("loki-logcli-cache", "LOGCLI_HOME", "logcli", "3.1.1", "3.4.2", "share/loki/logcli.md", "3MB"),
    ("promlens-cache", "PROMLENS_HOME", "promlens", "0.3.0", "0.3.0-post", "share/promlens/promlens.md", "8MB"),
    ("grafana-infinity-cache", "GF_INFINITY_HOME", "grafana", "2.0.0", "2.6.0", "plugins/yesoreyeram-infinity-datasource", "4MB"),
    ("prometheus-pushprox-cache", "PUSHPROX_HOME", "pushprox-proxy", "0.2.0", "0.2.0-post", "share/pushprox/pushprox.md", "2MB"),
    ("grafana-oncall-cache", "ONCALL_HOME", "oncall", "1.8.13", "1.15.2", "etc/oncall/settings.py", "11MB"),
]

_GPIO = [
    ("mei-me-leftover", "MEI_ME_CLEAR", "mei_me debug=1", "mei_me", "ls /sys/module/mei_me"),
    ("intel-rapl-leftover", "INTEL_RAPL_CLEAR", "intel_rapl_common debug=1", "intel_rapl_common", "ls /sys/class/powercap"),
    ("intel-rapl-msr-leftover", "INTEL_RAPL_MSR_CLEAR", "intel_rapl_msr debug=1", "intel_rapl_msr", "ls /sys/module/intel_rapl_msr"),
    ("mei-hdcp-leftover", "MEI_HDCP_CLEAR", "mei_hdcp debug=1", "mei_hdcp", "ls /sys/module/mei_hdcp"),
    ("mei-pxp-leftover", "MEI_PXP_CLEAR", "mei_pxp debug=1", "mei_pxp", "ls /sys/module/mei_pxp"),
    ("mei-gsc-leftover", "MEI_GSC_CLEAR", "mei_gsc debug=1", "mei_gsc", "ls /sys/module/mei_gsc"),
    ("mei-vsc-leftover", "MEI_VSC_CLEAR", "mei_vsc debug=1", "mei_vsc", "ls /sys/module/mei_vsc"),
    ("intel-uncore-leftover", "INTEL_UNCORE_CLEAR", "intel_uncore debug=1", "intel_uncore", "ls /sys/module/intel_uncore"),
    ("intel-cstate-leftover", "INTEL_CSTATE_CLEAR", "intel_idle debug=1", "intel_idle", "ls /sys/module/intel_idle"),
    ("intel-pmc-core-leftover", "INTEL_PMC_CORE_CLEAR", "intel_pmc_core debug=1", "intel_pmc_core", "ls /sys/module/intel_pmc_core"),
    ("intel-speed-select-leftover", "INTEL_SST_CLEAR", "isst_if_mbox_pci debug=1", "isst_if_mbox_pci", "ls /sys/module/isst_if_mbox_pci"),
    ("intel-pmt-leftover", "INTEL_PMT_CLEAR", "intel_pmt debug=1", "intel_pmt", "ls /sys/module/intel_pmt"),
    ("intel-th-leftover", "INTEL_TH_CLEAR", "intel_th debug=1", "intel_th", "ls /sys/module/intel_th"),
    ("intel-th-gth-leftover", "INTEL_TH_GTH_CLEAR", "intel_th_gth debug=1", "intel_th_gth", "ls /sys/module/intel_th_gth"),
    ("intel-th-sth-leftover", "INTEL_TH_STH_CLEAR", "intel_th_sth debug=1", "intel_th_sth", "ls /sys/module/intel_th_sth"),
    ("intel-th-msu-leftover", "INTEL_TH_MSU_CLEAR", "intel_th_msu debug=1", "intel_th_msu", "ls /sys/module/intel_th_msu"),
    ("intel-th-pti-leftover", "INTEL_TH_PTI_CLEAR", "intel_th_pti debug=1", "intel_th_pti", "ls /sys/module/intel_th_pti"),
    ("intel-th-acpi-leftover", "INTEL_TH_ACPI_CLEAR", "intel_th_acpi debug=1", "intel_th_acpi", "ls /sys/module/intel_th_acpi"),
    ("intel-th-pci-leftover", "INTEL_TH_PCI_CLEAR", "intel_th_pci debug=1", "intel_th_pci", "ls /sys/module/intel_th_pci"),
    ("punit-atom-debug-leftover", "PUNIT_ATOM_CLEAR", "punit_atom_debug debug=1", "punit_atom_debug", "ls /sys/module/punit_atom_debug"),
    ("intel-powerclamp-leftover", "INTEL_POWERCLAMP_CLEAR", "intel_powerclamp debug=1", "intel_powerclamp", "ls /sys/module/intel_powerclamp"),
    ("coretemp-pkg-leftover", "CORETEMP_PKG_CLEAR", "coretemp tjmax=cache", "coretemp", "ls /sys/module/coretemp"),
    ("intel-hid-leftover", "INTEL_HID_CLEAR", "intel_hid debug=1", "intel_hid", "ls /sys/module/intel_hid"),
    ("intel-vbtn-leftover", "INTEL_VBTN_CLEAR", "intel_vbtn debug=1", "intel_vbtn", "ls /sys/module/intel_vbtn"),
    ("intel-wmi-thunderbolt-leftover", "INTEL_WMI_TB_CLEAR", "intel_wmi_thunderbolt debug=1", "intel_wmi_thunderbolt", "ls /sys/module/intel_wmi_thunderbolt"),
    ("intel-wmi-sbl-fw-leftover", "INTEL_WMI_SBL_CLEAR", "intel_wmi_sbl_fw_update debug=1", "intel_wmi_sbl_fw_update", "ls /sys/module/intel_wmi_sbl_fw_update"),
    ("intel-ishtp-leftover", "INTEL_ISHTP_CLEAR", "intel_ishtp debug=1", "intel_ishtp", "ls /sys/module/intel_ishtp"),
    ("intel-ish-ipc-leftover", "INTEL_ISH_IPC_CLEAR", "intel_ish_ipc debug=1", "intel_ish_ipc", "ls /sys/module/intel_ish_ipc"),
    ("hid-intel-ish-hid-leftover", "HID_INTEL_ISH_CLEAR", "hid_intel_ish_hid debug=1", "hid_intel_ish_hid", "ls /sys/module/hid_intel_ish_hid"),
    ("intel-pmc-mux-leftover", "INTEL_PMC_MUX_CLEAR", "intel_pmc_mux debug=1", "intel_pmc_mux", "ls /sys/module/intel_pmc_mux"),
    ("intel-lpss-leftover", "INTEL_LPSS_CLEAR", "intel_lpss debug=1", "intel_lpss", "ls /sys/module/intel_lpss"),
    ("intel-lpss-pci-leftover", "INTEL_LPSS_PCI_CLEAR", "intel_lpss_pci debug=1", "intel_lpss_pci", "ls /sys/module/intel_lpss_pci"),
    ("intel-lpss-acpi-leftover", "INTEL_LPSS_ACPI_CLEAR", "intel_lpss_acpi debug=1", "intel_lpss_acpi", "ls /sys/module/intel_lpss_acpi"),
    ("intel-bxtwc-tmu-leftover", "INTEL_BXTWC_TMU_CLEAR", "intel_bxtwc_tmu debug=1", "intel_bxtwc_tmu", "ls /sys/module/intel_bxtwc_tmu"),
    ("intel-chtdc-ti-leftover", "INTEL_CHTDC_TI_CLEAR", "intel_chtdc_ti_pwrbtn debug=1", "intel_chtdc_ti_pwrbtn", "ls /sys/module/intel_chtdc_ti_pwrbtn"),
    ("intel-mrfld-pwrbtn-leftover", "INTEL_MRFLD_PWRBTN_CLEAR", "intel_mrfld_pwrbtn debug=1", "intel_mrfld_pwrbtn", "ls /sys/module/intel_mrfld_pwrbtn"),
    ("intel-oaktrail-leftover", "INTEL_OAKTRAIL_CLEAR", "intel_oaktrail debug=1", "intel_oaktrail", "ls /sys/module/intel_oaktrail"),
    ("intel-rst-leftover", "INTEL_RST_CLEAR", "intel_rst debug=1", "intel_rst", "ls /sys/module/intel_rst"),
    ("intel-smartconnect-leftover", "INTEL_SMARTCONNECT_CLEAR", "intel_smartconnect debug=1", "intel_smartconnect", "ls /sys/module/intel_smartconnect"),
    ("intel-telemetry-leftover", "INTEL_TELEMETRY_CLEAR", "intel_telemetry debug=1", "intel_telemetry", "ls /sys/module/intel_telemetry"),
    ("intel-turbo-max-3-leftover", "INTEL_TURBO_MAX_3_CLEAR", "intel_turbo_max_3 debug=1", "intel_turbo_max_3", "ls /sys/module/intel_turbo_max_3"),
    ("intel-uncore-frequency-leftover", "INTEL_UNCORE_FREQ_CLEAR", "intel_uncore_frequency debug=1", "intel_uncore_frequency", "ls /sys/module/intel_uncore_frequency"),
    ("intel-pstate-leftover", "INTEL_PSTATE_CLEAR", "intel_pstate debug=1", "intel_pstate", "ls /sys/module/intel_pstate"),
    ("intel-rapl-perf-leftover", "INTEL_RAPL_PERF_CLEAR", "intel_rapl_perf debug=1", "intel_rapl_perf", "ls /sys/module/intel_rapl_perf"),
    ("mei-wdt-aux-leftover", "MEI_WDT_AUX_CLEAR", "mei_wdt debug=1", "mei_wdt", "ls /sys/module/mei_wdt"),
    ("mei-txe-leftover", "MEI_TXE_CLEAR", "mei_txe debug=1", "mei_txe", "ls /sys/module/mei_txe"),
    ("mei-me-hbm-leftover", "MEI_ME_HBM_CLEAR", "mei_me hbm=1", "mei_me", "ls /sys/module/mei_me"),
    ("intel-rapl-tpmi-leftover", "INTEL_RAPL_TPMI_CLEAR", "intel_rapl_tpmi debug=1", "intel_rapl_tpmi", "ls /sys/module/intel_rapl_tpmi"),
]


def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum/font/cad/search/graph catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


_cursor = 0


def next_free_idx(start: int = 0) -> int | None:
    global _cursor
    for i in range(max(start, _cursor), len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            _cursor = i
            return i
        _cursor = i + 1
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
