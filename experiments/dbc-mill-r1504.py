#!/usr/bin/env python3
"""Mill docker-build-cache-factory r1504+. CI/CD runners × InfiniBand/RDMA leftovers.

NEW unique-pair catalog after r1456 observability/MEI-RAPL.
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
_spec = importlib.util.spec_from_file_location("dbc_mill_r1456", HERE / "dbc-mill-r1456.py")
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
    "prometheus-bin-cache",
    "mei-me-leftover",
    "grafana-oncall-cache",
    "intel-rapl-tpmi-leftover",
)

_CRYPTO = [
    ("jenkins-lts-cache", "JENKINS_HOME", "jenkins", "2.462.3", "2.492.1", "war/WEB-INF/web.xml", "72MB"),
    ("argo-workflows-cache", "ARGO_HOME", "argo", "3.5.10", "3.6.5", "etc/argo/controller-configmap.yaml", "18MB"),
    ("argocd-bin-cache", "ARGOCD_HOME", "argocd", "2.12.4", "2.14.5", "etc/argocd/argocd-cm.yaml", "22MB"),
    ("tekton-cli-cache", "TEKTON_HOME", "tkn", "0.37.0", "0.40.0", "share/tkn/tkn.md", "8MB"),
    ("tekton-pipelines-cache", "TEKTON_PIPELINES_HOME", "tekton-pipelines-controller", "0.62.0", "0.68.0", "etc/tekton/config-defaults.yaml", "14MB"),
    ("buildkite-agent-cache", "BUILDKITE_AGENT_HOME", "buildkite-agent", "3.82.1", "3.91.0", "etc/buildkite-agent/buildkite-agent.cfg", "10MB"),
    ("woodpecker-ci-cache", "WOODPECKER_HOME", "woodpecker-server", "2.7.1", "3.3.0", "etc/woodpecker/server.yaml", "12MB"),
    ("drone-server-cache", "DRONE_HOME", "drone-server", "2.24.0", "2.26.0", "etc/drone/server.env", "11MB"),
    ("dagger-cli-cache", "DAGGER_HOME", "dagger", "0.13.5", "0.18.3", "share/dagger/dagger.md", "16MB"),
    ("earthly-bin-cache", "EARTHLY_HOME", "earthly", "0.8.15", "0.8.16", "share/earthly/Earthfile.md", "15MB"),
    ("gitlab-runner-cache", "GITLAB_RUNNER_HOME", "gitlab-runner", "17.3.1", "17.9.1", "etc/gitlab-runner/config.toml", "13MB"),
    ("gitea-act-runner-cache", "GITEA_RUNNER_HOME", "act_runner", "0.2.10", "0.2.11", "etc/act_runner/config.yaml", "9MB"),
    ("act-cli-cache", "ACT_HOME", "act", "0.2.67", "0.2.74", "share/act/act.md", "7MB"),
    ("concourse-bin-cache", "CONCOURSE_HOME", "concourse", "7.11.2", "7.12.1", "etc/concourse/web.toml", "20MB"),
    ("spinnaker-hal-cache", "HAL_HOME", "hal", "1.34.3", "1.35.1", "etc/spinnaker/.hal/config", "24MB"),
    ("flux-cli-cache", "FLUX_HOME", "flux", "2.3.0", "2.5.1", "share/flux/flux.md", "8MB"),
    ("keptn-cli-cache", "KEPTN_HOME", "keptn", "1.4.5", "1.4.6", "etc/keptn/keptn.yaml", "6MB"),
    ("gocd-server-cache", "GO_SERVER_HOME", "go-server", "24.1.0", "24.3.0", "config/cruise-config.xml", "28MB"),
    ("zuul-scheduler-cache", "ZUUL_HOME", "zuul-scheduler", "10.1.0", "11.3.0", "etc/zuul/zuul.conf", "17MB"),
    ("prow-deck-cache", "PROW_HOME", "deck", "20240815", "20250301", "etc/prow/config.yaml", "12MB"),
    ("harness-cli-cache", "HARNESS_HOME", "harness", "1.0.4", "1.4.0", "share/harness/harness.md", "5MB"),
    ("buildbarn-bb-cache", "BUILDBARN_HOME", "bb-storage", "20240815", "20250301", "etc/buildbarn/storage.jsonnet", "14MB"),
    ("bazel-remote-cache", "BAZEL_REMOTE_HOME", "bazel-remote", "2.4.4", "2.5.0", "etc/bazel-remote/config.yml", "9MB"),
    ("kraken-ci-cache", "KRAKEN_HOME", "kraken", "1.0.0", "1.0.1", "etc/kraken/server.yaml", "11MB"),
    ("brigade-cli-cache", "BRIGADE_HOME", "brig", "2.7.0", "2.7.1", "share/brigade/brig.md", "6MB"),
    ("screwdriver-cd-cache", "SCREWDRIVER_HOME", "screwdriver-api", "0.5.0", "0.6.0", "config/local.yaml", "10MB"),
    ("jenkinsx-cli-cache", "JX_HOME", "jx", "3.10.142", "3.11.20", "share/jx/jx.md", "8MB"),
    ("okteto-cli-cache", "OKTETO_HOME", "okteto", "2.30.0", "3.6.0", "share/okteto/okteto.md", "7MB"),
    ("garden-cli-cache", "GARDEN_HOME", "garden", "0.13.47", "0.14.5", "share/garden/garden.md", "18MB"),
    ("atlantis-bin-cache", "ATLANTIS_HOME", "atlantis", "0.28.5", "0.33.0", "etc/atlantis/repos.yaml", "12MB"),
    ("tfc-agent-cache", "TFC_AGENT_HOME", "tfc-agent", "1.16.0", "1.23.0", "etc/tfc-agent/agent.env", "15MB"),
    ("spacelift-cli-cache", "SPACELIFT_HOME", "spacectl", "1.4.0", "1.14.1", "share/spacectl/spacectl.md", "4MB"),
    ("pack-cli-cache", "PACK_HOME", "pack", "0.35.1", "0.38.0", "share/pack/pack.md", "5MB"),
    ("kpack-controller-cache", "KPACK_HOME", "kpack-controller", "0.14.1", "0.16.1", "etc/kpack/controller.yaml", "11MB"),
    ("ko-cli-cache", "KO_DATA_PATH", "ko", "0.16.0", "0.17.1", "share/ko/ko.md", "4MB"),
    ("buildpacks-lifecycle-cache", "CNB_LIFECYCLE_HOME", "lifecycle", "0.19.6", "0.20.5", "share/lifecycle/lifecycle.toml", "6MB"),
    ("kaniko-executor-cache", "KANIKO_DIR", "executor", "1.23.2", "1.24.0", "share/kaniko/kaniko.md", "19MB"),
    ("img-cli-cache", "IMG_HOME", "img", "0.5.11", "0.5.12", "share/img/img.md", "8MB"),
    ("please-build-cache", "PLZ_HOME", "plz", "17.10.0", "17.21.0", "etc/please/please.build_defs", "9MB"),
    ("pants-bin-cache", "PANTS_HOME", "pants", "2.22.0", "2.25.0", "etc/pants.toml", "13MB"),
    ("buck2-cli-cache", "BUCK2_HOME", "buck2", "2024.08.15", "2025.04.01", "share/buck2/buck2.md", "16MB"),
    ("werf-cli-cache", "WERF_HOME", "werf", "2.10.0", "2.35.0", "share/werf/werf.md", "14MB"),
    ("skaffold-cli-cache", "SKAFFOLD_HOME", "skaffold", "2.13.2", "2.14.1", "share/skaffold/skaffold.md", "10MB"),
    ("tilt-cli-cache", "TILT_HOME", "tilt", "0.33.17", "0.34.5", "share/tilt/tilt.md", "12MB"),
    ("depot-cli-cache", "DEPOT_HOME", "depot", "2.40.1", "2.89.0", "share/depot/depot.md", "7MB"),
    ("devspace-cli-cache", "DEVSPACE_HOME", "devspace", "6.3.12", "6.3.16", "share/devspace/devspace.md", "8MB"),
    ("telepresence-cli-cache", "TELEPRESENCE_HOME", "telepresence", "2.19.1", "2.22.4", "share/telepresence/telepresence.md", "11MB"),
    ("circleci-cli-cache", "CIRCLECI_HOME", "circleci", "0.1.30995", "0.1.32000", "share/circleci/circleci.md", "5MB"),
]

_GPIO = [
    ("ib-core-leftover", "IB_CORE_CLEAR", "ib_core debug=1", "ib_core", "ls /sys/class/infiniband"),
    ("ib-ipoib-leftover", "IB_IPOIB_CLEAR", "ib_ipoib debug=1", "ib_ipoib", "ls /sys/module/ib_ipoib"),
    ("ib-srp-leftover", "IB_SRP_CLEAR", "ib_srp debug=1", "ib_srp", "ls /sys/module/ib_srp"),
    ("ib-isert-leftover", "IB_ISERT_CLEAR", "ib_isert debug=1", "ib_isert", "ls /sys/module/ib_isert"),
    ("rdma-ucm-leftover", "RDMA_UCM_CLEAR", "rdma_ucm debug=1", "rdma_ucm", "ls /sys/module/rdma_ucm"),
    ("mlx5-ib-leftover", "MLX5_IB_CLEAR", "mlx5_ib debug=1", "mlx5_ib", "ls /sys/module/mlx5_ib"),
    ("mlx4-ib-leftover", "MLX4_IB_CLEAR", "mlx4_ib debug=1", "mlx4_ib", "ls /sys/module/mlx4_ib"),
    ("iw-cxgb4-leftover", "IW_CXGB4_CLEAR", "iw_cxgb4 debug=1", "iw_cxgb4", "ls /sys/module/iw_cxgb4"),
    ("qedr-rdma-leftover", "QEDR_CLEAR", "qedr debug=1", "qedr", "ls /sys/module/qedr"),
    ("rxe-rdma-leftover", "RDMA_RXE_CLEAR", "rdma_rxe debug=1", "rdma_rxe", "ls /sys/module/rdma_rxe"),
    ("siw-rdma-leftover", "SIW_CLEAR", "siw debug=1", "siw", "ls /sys/module/siw"),
    ("ib-cm-leftover", "IB_CM_CLEAR", "ib_cm debug=1", "ib_cm", "ls /sys/module/ib_cm"),
    ("ib-mad-leftover", "IB_MAD_CLEAR", "ib_mad debug=1", "ib_mad", "ls /sys/module/ib_mad"),
    ("ib-sa-leftover", "IB_SA_CLEAR", "ib_sa debug=1", "ib_sa", "ls /sys/module/ib_sa"),
    ("rds-rdma-leftover", "RDS_RDMA_CLEAR", "rds debug=1", "rds", "ls /sys/module/rds"),
    ("smc-ib-leftover", "SMC_IB_CLEAR", "smc debug=1", "smc", "ls /sys/module/smc"),
    ("ib-srpt-leftover", "IB_SRPT_CLEAR", "ib_srpt debug=1", "ib_srpt", "ls /sys/module/ib_srpt"),
    ("opa-vnic-leftover", "OPA_VNIC_CLEAR", "opa_vnic debug=1", "opa_vnic", "ls /sys/module/opa_vnic"),
    ("opa-hfi1-aux-leftover", "OPA_HFI1_CLEAR", "hfi1 pkey=1", "hfi1", "ls /sys/module/hfi1"),
    ("bnxt-re-leftover", "BNXT_RE_CLEAR", "bnxt_re debug=1", "bnxt_re", "ls /sys/module/bnxt_re"),
    ("ocrdma-rdma-leftover", "OCRDMA_CLEAR", "ocrdma debug=1", "ocrdma", "ls /sys/module/ocrdma"),
    ("vmw-pvrdma-leftover", "VMW_PVRDMA_CLEAR", "vmw_pvrdma debug=1", "vmw_pvrdma", "ls /sys/module/vmw_pvrdma"),
    ("efa-rdma-leftover", "EFA_RDMA_CLEAR", "efa debug=1", "efa", "ls /sys/module/efa"),
    ("mana-ib-leftover", "MANA_IB_CLEAR", "mana_ib debug=1", "mana_ib", "ls /sys/module/mana_ib"),
    ("erdma-host-leftover", "ERDMA_CLEAR", "erdma debug=1", "erdma", "ls /sys/module/erdma"),
    ("ionic-rdma-leftover", "IONIC_RDMA_CLEAR", "ionic_rdma debug=1", "ionic_rdma", "ls /sys/module/ionic_rdma"),
    ("mthca-ib-leftover", "MTHCA_CLEAR", "ib_mthca debug=1", "ib_mthca", "ls /sys/module/ib_mthca"),
    ("cxgb3-ib-leftover", "CXGB3_IB_CLEAR", "iw_cxgb3 debug=1", "iw_cxgb3", "ls /sys/module/iw_cxgb3"),
    ("usnic-ib-leftover", "USNIC_CLEAR", "usnic_verbs debug=1", "usnic_verbs", "ls /sys/module/usnic_verbs"),
    ("qib-ib-leftover", "QIB_CLEAR", "ib_qib debug=1", "ib_qib", "ls /sys/module/ib_qib"),
    ("ipath-ib-leftover", "IPATH_CLEAR", "ib_ipath debug=1", "ib_ipath", "ls /sys/module/ib_ipath"),
    ("mlx4-core-mod-leftover", "MLX4_CORE_CLEAR", "mlx4_core debug=1", "mlx4_core", "ls /sys/module/mlx4_core"),
    ("mlx5-vdpa-leftover", "MLX5_VDPA_CLEAR", "mlx5_vdpa debug=1", "mlx5_vdpa", "ls /sys/module/mlx5_vdpa"),
    ("ib-ucm-mod-leftover", "IB_UCM_CLEAR", "ib_ucm debug=1", "ib_ucm", "ls /sys/module/ib_ucm"),
    ("ib-addr-leftover", "IB_ADDR_CLEAR", "ib_addr debug=1", "ib_addr", "ls /sys/module/ib_addr"),
    ("rdmavt-mod-leftover", "RDMAVT_CLEAR", "rdmavt debug=1", "rdmavt", "ls /sys/module/rdmavt"),
    ("ib-iser-leftover", "IB_ISER_CLEAR", "ib_iser debug=1", "ib_iser", "ls /sys/module/ib_iser"),
    ("ib-iwcm-leftover", "IB_IWCM_CLEAR", "iw_cm debug=1", "iw_cm", "ls /sys/module/iw_cm"),
    ("ib-umem-leftover", "IB_UMEM_CLEAR", "ib_umem debug=1", "ib_umem", "ls /sys/module/ib_umem"),
    ("ib-netlink-leftover", "IB_NETLINK_CLEAR", "rdma_nl debug=1", "ib_core", "ls /sys/class/infiniband"),
    ("mlx5-ib-netdev-leftover", "MLX5_IB_NETDEV_CLEAR", "mlx5_ib roce=1", "mlx5_ib", "ls /sys/module/mlx5_ib"),
    ("ib-opa-core-leftover", "IB_OPA_CLEAR", "hfi1 pkey=1", "hfi1", "ls /sys/module/hfi1"),
    ("irdma-aux-leftover", "IRDMA_AUX_CLEAR", "irdma debug=1", "irdma", "ls /sys/module/irdma"),
    ("ib-uverbs-aux-leftover", "IB_UVERBS_AUX_CLEAR", "ib_uverbs debug=1", "ib_uverbs", "ls /sys/module/ib_uverbs"),
    ("bnx2i-iscsi-leftover", "BNX2I_CLEAR", "bnx2i debug=1", "bnx2i", "ls /sys/module/bnx2i"),
    ("ehca-ib-leftover", "EHCA_CLEAR", "ib_ehca debug=1", "ib_ehca", "ls /sys/module/ib_ehca"),
    ("nes-rdma-leftover", "NES_RDMA_CLEAR", "iw_nes debug=1", "iw_nes", "ls /sys/module/iw_nes"),
    ("mlx5-fpga-leftover", "MLX5_FPGA_CLEAR", "mlx5_fpga debug=1", "mlx5_fpga", "ls /sys/module/mlx5_fpga"),
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
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech/solver/video/mq/quantum/font/cad/search/graph/obs catalogs)",
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
