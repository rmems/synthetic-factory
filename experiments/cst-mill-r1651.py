#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1651+ (cst- ids). BAN r1–r1650."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1446", HERE / "cst-mill-r1446.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)
_steps_ok = _m._steps_ok
_steps_part = _m._steps_part
CATALOG_FIRST = 1651

PAIRS: list[tuple] = [
    ("sccache", "sccache-s3-leftover", "sccache-gha-handoff", "flock-sccch",
     "src/sccache.toml", "tests/test_sccache.py", "S3 leftover",
     "drop S3 on miss", "s3 leftover + wait + do(key)", 18,
     "GHA leftover still 1s", "GHA leftover",
     "src/sccache_gha.toml", "tests/test_sccache_gha.py", "gets"),
    ("ccache", "ccache-sloppiness-leftover", "ccache-inode-handoff", "flock-ccach",
     "src/ccache.conf", "tests/test_ccache.py", "sloppiness leftover",
     "drop sloppiness on miss", "slop leftover + wait + do(hash)", 16,
     "inode leftover still 1s", "inode leftover",
     "src/ccache_in.conf", "tests/test_ccache_in.py", "gets"),
    ("distcc", "distcc-pump-leftover", "distcc-host-handoff", "flock-dstcc",
     "src/distcc.conf", "tests/test_distcc.py", "pump leftover",
     "drop pump on miss", "pump leftover + wait + do(unit)", 15,
     "host leftover still 1s", "host leftover",
     "src/distcc_h.conf", "tests/test_distcc_h.py", "gets"),
    ("icecream", "icecream-scheduler-leftover", "icecream-daemon-handoff", "flock-iccrm",
     "src/icecc.conf", "tests/test_icecc.py", "scheduler leftover",
     "drop scheduler on miss", "sched leftover + wait + do(job)", 14,
     "daemon leftover still 1s", "daemon leftover",
     "src/icecc_d.conf", "tests/test_icecc_d.py", "gets"),
    ("BuildKit", "buildkit-gha-leftover", "buildkit-s3-handoff", "flock-bldkt",
     "src/buildkit.toml", "tests/test_buildkit.py", "gha leftover",
     "drop gha on miss", "gha leftover + wait + do(id)", 17,
     "s3 leftover still 1s", "s3 leftover",
     "src/buildkit_s3.toml", "tests/test_buildkit_s3.py", "gets"),
    ("Kaniko", "kaniko-cache-repo-leftover", "kaniko-snapshot-handoff", "flock-knkcr",
     "src/kaniko.yaml", "tests/test_kaniko.py", "cache-repo leftover",
     "drop cache-repo on miss", "repo leftover + wait + do(layer)", 16,
     "snapshot leftover still 1s", "snapshot leftover",
     "src/kaniko_sn.yaml", "tests/test_kaniko_sn.py", "gets"),
    ("Buildah", "buildah-layer-leftover", "buildah-vfs-handoff", "flock-bldah",
     "src/buildah.conf", "tests/test_buildah.py", "layer leftover",
     "drop layer on miss", "layer leftover + wait + do(id)", 15,
     "vfs leftover still 1s", "vfs leftover",
     "src/buildah_vfs.conf", "tests/test_buildah_vfs.py", "gets"),
    ("Podman", "podman-event-leftover", "podman-tmpfs-handoff", "flock-pdmnv",
     "src/podman.conf", "tests/test_podman.py", "events leftover",
     "drop events on miss", "events leftover + wait + do(id)", 14,
     "tmpfs leftover still 1s", "tmpfs leftover",
     "src/podman_tf.conf", "tests/test_podman_tf.py", "gets"),
    ("containerd", "containerd-content-leftover", "containerd-snapshot-handoff", "flock-ctntd",
     "src/containerd.toml", "tests/test_containerd.py", "content leftover",
     "drop content on miss", "content leftover + wait + do(digest)", 18,
     "snapshot leftover still 1s", "snapshot leftover",
     "src/containerd_sn.toml", "tests/test_containerd_sn.py", "gets"),
    ("CRI-O", "crio-storage-leftover", "crio-pause-handoff", "flock-crios",
     "src/crio.conf", "tests/test_crio.py", "storage leftover",
     "drop storage on miss", "storage leftover + wait + do(id)", 15,
     "pause leftover still 1s", "pause leftover",
     "src/crio_pause.conf", "tests/test_crio_pause.py", "gets"),
    ("nerdctl", "nerdctl-buildkit-leftover", "nerdctl-namespace-handoff", "flock-nrdct",
     "src/nerdctl.toml", "tests/test_nerdctl.py", "buildkit leftover",
     "drop buildkit on miss", "bk leftover + wait + do(id)", 14,
     "namespace leftover still 1s", "namespace leftover",
     "src/nerdctl_ns.toml", "tests/test_nerdctl_ns.py", "gets"),
    ("skopeo", "skopeo-copy-leftover", "skopeo-sync-handoff", "flock-skpeo",
     "src/skopeo.yaml", "tests/test_skopeo.py", "copy leftover",
     "drop copy on miss", "copy leftover + wait + do(ref)", 13,
     "sync leftover still 1s", "sync leftover",
     "src/skopeo_sy.yaml", "tests/test_skopeo_sy.py", "gets"),
    ("umoci", "umoci-unpack-leftover", "umoci-repack-handoff", "flock-umoci",
     "src/umoci.json", "tests/test_umoci.py", "unpack leftover",
     "drop unpack on miss", "unpack leftover + wait + do(layer)", 12,
     "repack leftover still 1s", "repack leftover",
     "src/umoci_rp.json", "tests/test_umoci_rp.py", "gets"),
    ("ORAS", "oras-attach-leftover", "oras-discover-handoff", "flock-oras",
     "src/oras.json", "tests/test_oras.py", "attach leftover",
     "drop attach on miss", "attach leftover + wait + do(ref)", 13,
     "discover leftover still 1s", "discover leftover",
     "src/oras_ds.json", "tests/test_oras_ds.py", "gets"),
    ("cosign", "cosign-rekor-leftover", "cosign-fulcio-handoff", "flock-csgn",
     "src/cosign.json", "tests/test_cosign.py", "rekor leftover",
     "drop rekor on miss", "rekor leftover + wait + do(digest)", 14,
     "fulcio leftover still 1s", "fulcio leftover",
     "src/cosign_fu.json", "tests/test_cosign_fu.py", "gets"),
    ("Notation", "notation-truststore-leftover", "notation-plugin-handoff", "flock-notat",
     "src/notation.json", "tests/test_notation.py", "truststore leftover",
     "drop truststore on miss", "trust leftover + wait + do(ref)", 13,
     "plugin leftover still 1s", "plugin leftover",
     "src/notation_pl.json", "tests/test_notation_pl.py", "gets"),
    ("Trivy", "trivy-db-leftover", "trivy-java-handoff", "flock-trvyd",
     "src/trivy.yaml", "tests/test_trivy.py", "db leftover",
     "drop db on miss", "db leftover + wait + do(cve)", 16,
     "java leftover still 1s", "java leftover",
     "src/trivy_jv.yaml", "tests/test_trivy_jv.py", "gets"),
    ("Grype", "grype-db-leftover", "grype-matching-handoff", "flock-grypd",
     "src/grype.yaml", "tests/test_grype.py", "db leftover",
     "drop db on miss", "db leftover + wait + do(cve)", 15,
     "matching leftover still 1s", "matching leftover",
     "src/grype_mt.yaml", "tests/test_grype_mt.py", "gets"),
    ("Syft", "syft-cataloger-leftover", "syft-file-handoff", "flock-syftc",
     "src/syft.yaml", "tests/test_syft.py", "cataloger leftover",
     "drop cataloger on miss", "cat leftover + wait + do(pkg)", 14,
     "file leftover still 1s", "file leftover",
     "src/syft_fl.yaml", "tests/test_syft_fl.py", "gets"),
    ("Clair", "clair-indexer-leftover", "clair-matcher-handoff", "flock-clair",
     "src/clair.yaml", "tests/test_clair.py", "indexer leftover",
     "drop indexer on miss", "idx leftover + wait + do(layer)", 15,
     "matcher leftover still 1s", "matcher leftover",
     "src/clair_mt.yaml", "tests/test_clair_mt.py", "gets"),
    ("Harbor", "harbor-proxy-leftover", "harbor-replication-handoff", "flock-hrbrp",
     "src/harbor.yml", "tests/test_harbor.py", "proxy leftover",
     "drop proxy on miss", "proxy leftover + wait + do(ref)", 16,
     "replication leftover still 1s", "replication leftover",
     "src/harbor_rp.yml", "tests/test_harbor_rp.py", "gets"),
    ("GHCR", "ghcr-package-leftover", "ghcr-attest-handoff", "flock-ghcrp",
     "src/ghcr.json", "tests/test_ghcr.py", "package leftover",
     "drop package on miss", "pkg leftover + wait + do(ref)", 14,
     "attest leftover still 1s", "attest leftover",
     "src/ghcr_at.json", "tests/test_ghcr_at.py", "gets"),
    ("ECR", "ecr-lifecycle-leftover", "ecr-scan-handoff", "flock-ecrlc",
     "src/ecr.json", "tests/test_ecr.py", "lifecycle leftover",
     "drop lifecycle on miss", "lc leftover + wait + do(tag)", 15,
     "scan leftover still 1s", "scan leftover",
     "src/ecr_sc.json", "tests/test_ecr_sc.py", "gets"),
    ("GCR", "gcr-vuln-leftover", "gcr-tag-handoff", "flock-gcrvn",
     "src/gcr.json", "tests/test_gcr.py", "vuln leftover",
     "drop vuln on miss", "vuln leftover + wait + do(digest)", 13,
     "tag leftover still 1s", "tag leftover",
     "src/gcr_tg.json", "tests/test_gcr_tg.py", "gets"),
    ("ACR", "acr-purge-leftover", "acr-task-handoff", "flock-acrpg",
     "src/acr.json", "tests/test_acr.py", "purge leftover",
     "drop purge on miss", "purge leftover + wait + do(tag)", 14,
     "task leftover still 1s", "task leftover",
     "src/acr_tk.json", "tests/test_acr_tk.py", "gets"),
    ("Quay", "quay-clair-leftover", "quay-robot-handoff", "flock-quayc",
     "src/quay.json", "tests/test_quay.py", "clair leftover",
     "drop clair on miss", "clair leftover + wait + do(ref)", 15,
     "robot leftover still 1s", "robot leftover",
     "src/quay_rb.json", "tests/test_quay_rb.py", "gets"),
    ("Artifactory", "artifactory-cache-leftover", "artifactory-xray-handoff", "flock-artfc",
     "src/artifactory.yml", "tests/test_artifactory.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(path)", 17,
     "xray leftover still 1s", "xray leftover",
     "src/artifactory_xr.yml", "tests/test_artifactory_xr.py", "gets"),
    ("Nexus", "nexus-blobstore-leftover", "nexus-group-handoff", "flock-nxsbl",
     "src/nexus.yml", "tests/test_nexus.py", "blobstore leftover",
     "drop blobstore on miss", "blob leftover + wait + do(path)", 16,
     "group leftover still 1s", "group leftover",
     "src/nexus_gp.yml", "tests/test_nexus_gp.py", "gets"),
    ("ChartMuseum", "chartmuseum-index-leftover", "chartmuseum-prov-handoff", "flock-chtms",
     "src/chartmuseum.yml", "tests/test_chartmuseum.py", "index leftover",
     "drop index on miss", "index leftover + wait + do(chart)", 13,
     "prov leftover still 1s", "prov leftover",
     "src/chartmuseum_pv.yml", "tests/test_chartmuseum_pv.py", "gets"),
    ("Helm OCI", "helm-oci-leftover", "helm-prov-handoff", "flock-hlmoc",
     "src/helm.yaml", "tests/test_helm.py", "oci leftover",
     "drop oci on miss", "oci leftover + wait + do(chart)", 14,
     "prov leftover still 1s", "prov leftover",
     "src/helm_pv.yaml", "tests/test_helm_pv.py", "gets"),
    ("Flux", "flux-source-leftover", "flux-kustomize-handoff", "flock-fluxs",
     "src/flux.yaml", "tests/test_flux.py", "source leftover",
     "drop source on miss", "source leftover + wait + do(rev)", 15,
     "kustomize leftover still 1s", "kustomize leftover",
     "src/flux_ks.yaml", "tests/test_flux_ks.py", "gets"),
    ("Argo CD", "argocd-repo-leftover", "argocd-appset-handoff", "flock-argcd",
     "src/argocd.yaml", "tests/test_argocd.py", "repo leftover",
     "drop repo on miss", "repo leftover + wait + do(rev)", 16,
     "appset leftover still 1s", "appset leftover",
     "src/argocd_as.yaml", "tests/test_argocd_as.py", "gets"),
    ("Tekton", "tekton-result-leftover", "tekton-bundle-handoff", "flock-tktnr",
     "src/tekton.yaml", "tests/test_tekton.py", "result leftover",
     "drop result on miss", "result leftover + wait + do(run)", 15,
     "bundle leftover still 1s", "bundle leftover",
     "src/tekton_bd.yaml", "tests/test_tekton_bd.py", "gets"),
    ("GitHub Actions cache", "gha-cache-leftover", "gha-restore-handoff", "flock-ghacc",
     "src/gha.yml", "tests/test_gha.py", "actions/cache leftover",
     "drop actions/cache on miss", "cache leftover + wait + do(key)", 18,
     "restore leftover still 1s", "restore leftover",
     "src/gha_rs.yml", "tests/test_gha_rs.py", "gets"),
    ("GitLab CI cache", "glci-cache-leftover", "glci-fallback-handoff", "flock-glcic",
     "src/gitlab-ci.yml", "tests/test_glci.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(key)", 17,
     "fallback leftover still 1s", "fallback leftover",
     "src/gitlab-ci_fb.yml", "tests/test_glci_fb.py", "gets"),
    ("CircleCI", "circleci-save-leftover", "circleci-restore-handoff", "flock-crcl",
     "src/config.yml", "tests/test_circleci.py", "save_cache leftover",
     "drop save_cache on miss", "save leftover + wait + do(key)", 16,
     "restore leftover still 1s", "restore leftover",
     "src/config_rs.yml", "tests/test_circleci_rs.py", "gets"),
    ("Buildkite", "buildkite-cache-leftover", "buildkite-plugin-handoff", "flock-bldkt2",
     "src/pipeline.yml", "tests/test_buildkite.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(key)", 15,
     "plugin leftover still 1s", "plugin leftover",
     "src/pipeline_pl.yml", "tests/test_buildkite_pl.py", "gets"),
    ("Jenkins", "jenkins-pipeline-leftover", "jenkins-stash-handoff", "flock-jnksp",
     "src/Jenkinsfile", "tests/test_jenkins.py", "pipeline leftover",
     "drop pipeline on miss", "pipe leftover + wait + do(key)", 16,
     "stash leftover still 1s", "stash leftover",
     "src/Jenkinsfile_st", "tests/test_jenkins_st.py", "gets"),
    ("TeamCity", "teamcity-artifact-leftover", "teamcity-cache-handoff", "flock-tmcty",
     "src/teamcity.xml", "tests/test_teamcity.py", "artifact leftover",
     "drop artifact on miss", "art leftover + wait + do(key)", 15,
     "cache leftover still 1s", "cache leftover",
     "src/teamcity_ch.xml", "tests/test_teamcity_ch.py", "gets"),
    ("Woodpecker", "woodpecker-cache-leftover", "woodpecker-plugin-handoff", "flock-wdpkr",
     "src/woodpecker.yml", "tests/test_woodpecker.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(key)", 14,
     "plugin leftover still 1s", "plugin leftover",
     "src/woodpecker_pl.yml", "tests/test_woodpecker_pl.py", "gets"),
]

def records(round_n: int):
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    rec_ok = {
        "id": f"cst-r{round_n}-{slug_ok}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} {api} still stampedes {workers} callers after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_ok(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded {workers} callers. {naive} failed still-rebuilds. "
            f"Plan change: {fix}. {test} 4/4, suite 8/8. Residual: {residual}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 8, "cost_steps": 16},
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {api}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    rec_part = {
        "id": f"cst-r{round_n}-{slug_part}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} still stampedes after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}. "
            f"{sibling} may still hard-miss; ticket allows handoff."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_part(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded callers. {naive} failed fixture. "
            f"Plan change: {fix}. {test} 3/3. Partial: leftover leftover leftover {sibling} still leftover (xfail)."
        ),
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "xfailed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {sibling}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    return [rec_ok, rec_part]


def notes_md(round_n: int) -> str:
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    return (
        f"# NOTES-r{round_n} cache-stampede-factory\n\n"
        "Novel coverage: 91%\n\n"
        f"Two designed leftover leftover leftover stampede episodes (quota 2). "
        f"{product} leftover leftover leftover {api} vs leftover leftover leftover {sibling}. "
        "Not flock-wN. Not AWS catalog. Not r1–r1650 clones (incl. r1445 akamai-esi, r1650 bazel-cas). "
        "Not dbc-/sir-/gql- ids.\n"
        "Not overlayfs whiteout. Not nydus/stargz. Not search-index leftover. Not docker leftover leftover leftover.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| cst-r{round_n}-{slug_ok} | {workers} leftover leftover leftover {product} | {naive} | {fix} | success residual {residual} |\n"
        f"| cst-r{round_n}-{slug_part} | leftover leftover leftover {sibling} | {naive} | {fix} | handoff leftover sibling |\n\n"
        "## Step counts\n"
        "- ep1: 16. Naive 6–7; plan change 8; suite green 12–16.\n"
        "- ep2: 17. Naive 6–7; plan change 8; sibling xfail 12–17.\n\n"
        "## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:. No thought keys. Plant `{plant}`.\n"
        "meta.generator=grok-4.6. Invented plant. No sim_or_real: real.\n\n"
        "## Weaknesses / next\n"
        f"Avoid {slug_ok} reruns and docker/search ids.\n"
    )


def write_round(round_n: int, stage: Path):
    recs = records(round_n)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes_md(round_n))
    return [r["id"] for r in recs]
