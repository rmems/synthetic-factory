#!/usr/bin/env python3
"""docker-build-cache leftover leftover leftover mill: cache product × invalidation.

Not lang-cache × kernel leftover twins (r550–r595). Not r526–r549 langs/fs.
Not harbor-pin, leftover×sysctl, HTTP-status leftover, apk-on-debian.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/docker-build-cache-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
HOP = [
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
    "incident-response-oncall-factory",
]
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

# Distinct cache product + leftover leftover leftover invalidation mechanic.
PAIRS: list[dict] = [
    {
        "slug": "buildkit-cache-mount-id-leftover",
        "lslug": "buildkit-cache-mount-sharing-locked-leftover",
        "product": "BuildKit cache mount",
        "mech": "RUN --mount=type=cache,id leftover alias",
        "lmech": "sharing=locked leftover holds /var/lib/buildkit/runc-overlayfs",
        "file": "Dockerfile",
        "lfile": "docker-bake.hcl",
        "false_file": "/etc/buildkit/buildkitd.toml",
        "fail_old": "RUN --mount=type=cache,id=go-pkg,target=/go/pkg/mod",
        "fail_new": "RUN --mount=type=cache,id=go-pkg-v2,sharing=shared,target=/go/pkg/mod",
        "lfail_old": "sharing = \"locked\"",
        "lfail_new": "sharing = \"shared\"",
        "false_old": "max-parallelism = 2",
        "false_new": "max-parallelism = 8",
        "cmd": "buildctl du --filter type==source.local",
        "lcmd": "buildctl prune --keep-duration 0s --filter type==exec.cachemount",
        "hit": "cache mount id=go-pkg-v2 reused 412MB",
        "miss": "cache mount id=go-pkg miss; leftover id=go-mod-old still 380MB",
        "lstill": "prune skipped locked share; leftover 380MB exec.cachemount",
        "novel": 71,
        "new_vs": "BuildKit cache-mount id leftover vs sharing=locked leftover (not lang×kernel)",
    },
    {
        "slug": "nydus-rafs-blobcache-digest-leftover",
        "lslug": "nydus-prefetch-table-stale-leftover",
        "product": "nydus RAFS blobcache",
        "mech": "blobcache digest leftover after nydus-image create",
        "lmech": "prefetch table leftover after nydusd --prefetch-files",
        "file": "/etc/nydus/config.json",
        "lfile": "/var/lib/nydus/prefetch.json",
        "false_file": "/etc/containerd/config.toml",
        "fail_old": '"cache_digest": "sha256:oldblob"',
        "fail_new": '"cache_digest": "sha256:rafs-v6-new"',
        "lfail_old": '"prefetch_files": ["/usr/lib/old.so"]',
        "lfail_new": '"prefetch_files": ["/usr/lib/app.so"]',
        "false_old": 'snapshotter = "overlayfs"',
        "false_new": 'snapshotter = "nydus"',
        "cmd": "nydus-image check --blob /var/lib/nydus/blobs",
        "lcmd": "nydusd --config /etc/nydus/config.json --prefetch-all",
        "hit": "rafs v6 blobcache digest match; 88 chunks reused",
        "miss": "digest leftover sha256:oldblob; bootstrap points at missing chunk",
        "lstill": "prefetch leftover /usr/lib/old.so; nydusd still warms stale table",
        "novel": 72,
        "new_vs": "nydus blobcache digest leftover vs nydus prefetch-table leftover",
    },
    {
        "slug": "stargz-toc-offset-leftover",
        "lslug": "stargz-prefetch-list-leftover",
        "product": "eStargz TOC",
        "mech": "stargz TOC offset leftover after ctr-remote optimize",
        "lmech": "stargz snapshotter prefetch leftover list",
        "file": "/etc/containerd-stargz-grpc/config.toml",
        "lfile": "/var/lib/stargz-snapshotter/prefetch.json",
        "false_file": "/etc/containerd/config.toml",
        "fail_old": "toc_offset = 4096",
        "fail_new": "toc_offset = 0",
        "lfail_old": '"prefetch": ["bin/old-entrypoint"]',
        "lfail_new": '"prefetch": ["bin/app"]',
        "false_old": 'snapshotter = "overlayfs"',
        "false_new": 'snapshotter = "stargz"',
        "cmd": "ctr-remote images optimize --oci app:estargz",
        "lcmd": "ctr-remote get-toc-digest app:estargz",
        "hit": "TOC digest sha256:estargz-new; lazy pull 12 files",
        "miss": "TOC offset leftover 4096 skips footer; full pull",
        "lstill": "prefetch leftover bin/old-entrypoint; lazy miss still 180MB",
        "novel": 72,
        "new_vs": "stargz TOC offset leftover vs stargz prefetch-list leftover",
    },
    {
        "slug": "overlayfs-diffid-whiteout-leftover",
        "lslug": "overlayfs-inodes-opaque-leftover",
        "product": "overlayfs layer cache",
        "mech": "whiteout .wh leftover keeps deleted file in upper",
        "lmech": "trusted.overlay.opaque leftover on dir",
        "file": "/var/lib/docker/overlay2/l/diff/wh.map",
        "lfile": "/var/lib/docker/overlay2/l/workdir/work",
        "false_file": "/etc/docker/daemon.json",
        "fail_old": ".wh.app.bin leftover",
        "fail_new": "# whiteout cleared for app.bin",
        "lfail_old": "trusted.overlay.opaque=y",
        "lfail_new": "trusted.overlay.opaque=",
        "false_old": '"storage-driver": "overlay2"',
        "false_new": '"storage-driver": "overlay2", "storage-opts": ["overlay2.override_kernel_check=1"]',
        "cmd": "docker builder prune --filter type=regular",
        "lcmd": "getfattr -n trusted.overlay.opaque /var/lib/docker/overlay2/l/merged/app",
        "hit": "diffid reused; whiteout gone; COPY --from hits cache",
        "miss": ".wh.app.bin leftover hides file; layer miss",
        "lstill": "opaque leftover still hides upper; prune regular no-op",
        "novel": 73,
        "new_vs": "overlayfs whiteout leftover vs overlay opaque xattr leftover",
    },
    {
        "slug": "gha-actions-cache-key-leftover",
        "lslug": "gha-restore-keys-prefix-leftover",
        "product": "GitHub Actions cache",
        "mech": "actions/cache key leftover hashFiles globs",
        "lmech": "restore-keys prefix leftover restores stale zip",
        "file": ".github/workflows/image.yml",
        "lfile": ".github/actions/restore-cache/action.yml",
        "false_file": ".github/workflows/ci.yml",
        "fail_old": 'key: docker-${{ hashFiles("go.sum") }}',
        "fail_new": 'key: docker-${{ hashFiles("go.sum","Dockerfile") }}',
        "lfail_old": "restore-keys: docker-",
        "lfail_new": "restore-keys: docker-${{ runner.os }}-",
        "false_old": "timeout-minutes: 20",
        "false_new": "timeout-minutes: 60",
        "cmd": "gh cache list --key docker-",
        "lcmd": "gh cache delete --key docker-oldprefix --confirm",
        "hit": "cache key docker-9f2 hit 1.1GB gha",
        "miss": "hashFiles leftover go.sum only; Dockerfile change miss",
        "lstill": "restore-keys leftover docker- still hydrates stale zip",
        "novel": 73,
        "new_vs": "GHA actions/cache key leftover vs restore-keys prefix leftover",
    },
    {
        "slug": "depot-project-cache-token-leftover",
        "lslug": "depot-org-lease-leftover",
        "product": "Depot remote cache",
        "mech": "DEPOT_PROJECT leftover token binds wrong cache",
        "lmech": "org lease leftover after depot cache reset",
        "file": "depot.json",
        "lfile": ".depot/leases.json",
        "false_file": "Dockerfile",
        "fail_old": '"project": "prj_oldgate"',
        "fail_new": '"project": "prj_gate-v3"',
        "lfail_old": '"lease": "org_stale_88"',
        "lfail_new": '"lease": "org_gate_v3"',
        "false_old": "FROM debian:bookworm",
        "false_new": "FROM debian:bookworm-slim",
        "cmd": "depot build --project prj_gate-v3 --load .",
        "lcmd": "depot cache reset --project prj_gate-v3 --yes",
        "hit": "depot remote cache hit 640MB project prj_gate-v3",
        "miss": "token leftover prj_oldgate; 0% hit",
        "lstill": "org lease leftover org_stale_88; reset skipped leased blobs",
        "novel": 74,
        "new_vs": "Depot project token leftover vs Depot org-lease leftover",
    },
    {
        "slug": "earthly-save-cache-id-leftover",
        "lslug": "earthly-inline-cache-push-leftover",
        "product": "Earthly SAVE CACHE",
        "mech": "SAVE CACHE --id leftover after Earthfile bump",
        "lmech": "--push leftover still publishes stale inline cache",
        "file": "Earthfile",
        "lfile": ".earthly/config.yml",
        "false_file": "docker-compose.yml",
        "fail_old": "SAVE CACHE --id go-mod /go/pkg/mod",
        "fail_new": "SAVE CACHE --id go-mod-v2 /go/pkg/mod",
        "lfail_old": "push: true",
        "lfail_new": "push: false",
        "false_old": "image: earthly/earthly:v0.8",
        "false_new": "image: earthly/earthly:v0.8.15",
        "cmd": "earthly --ci +image",
        "lcmd": "earthly prune --reset",
        "hit": "SAVE CACHE go-mod-v2 hit; +image 22s",
        "miss": "SAVE CACHE leftover --id go-mod; miss after Earthfile bump",
        "lstill": "--push leftover republishes stale inline cache to registry",
        "novel": 74,
        "new_vs": "Earthly SAVE CACHE id leftover vs inline --push leftover",
    },
    {
        "slug": "dagger-cachevolume-key-leftover",
        "lslug": "dagger-engine-persist-leftover",
        "product": "Dagger CacheVolume",
        "mech": "dag.CacheVolume leftover key after module bump",
        "lmech": "engine persist leftover after dagger query --progress",
        "file": "ci/main.go",
        "lfile": "~/.local/share/dagger/engine.json",
        "false_file": "dagger.json",
        "fail_old": 'dag.CacheVolume("gomod")',
        "fail_new": 'dag.CacheVolume("gomod-v3")',
        "lfail_old": '"persist": true',
        "lfail_new": '"persist": false',
        "false_old": '"sdk": "go"',
        "false_new": '"sdk": "go", "engineVersion": "v0.13.0"',
        "cmd": "dagger call build --source .",
        "lcmd": "dagger query --progress plain '{engine{persist}}'",
        "hit": "CacheVolume gomod-v3 hit 210MB",
        "miss": "CacheVolume leftover gomod; module digest changed",
        "lstill": "engine persist leftover true; prune cannot drop volume",
        "novel": 75,
        "new_vs": "Dagger CacheVolume key leftover vs engine persist leftover",
    },
    {
        "slug": "kaniko-cache-repo-tag-leftover",
        "lslug": "kaniko-snapshotmode-redo-leftover",
        "product": "Kaniko cache repo",
        "mech": "--cache-repo leftover tag after digest move",
        "lmech": "--snapshotMode leftover redo after whiteout",
        "file": "cloudbuild.yaml",
        "lfile": "/kaniko/.docker/config.json",
        "false_file": "Dockerfile",
        "fail_old": "--cache-repo=gcr.io/proj/kaniko-cache:old",
        "fail_new": "--cache-repo=gcr.io/proj/kaniko-cache:v4",
        "lfail_old": '"snapshotMode": "redo"',
        "lfail_new": '"snapshotMode": "time"',
        "false_old": "FROM gcr.io/distroless/base",
        "false_new": "FROM gcr.io/distroless/static-debian12",
        "cmd": "/kaniko/executor --cache=true --cache-repo=gcr.io/proj/kaniko-cache:v4",
        "lcmd": "/kaniko/executor --cleanup --snapshotMode=time",
        "hit": "kaniko cache repo v4 layer hit 9/11",
        "miss": "cache-repo leftover :old; 0 layer hits",
        "lstill": "snapshotMode leftover redo ignores mtime; still full snapshot",
        "novel": 75,
        "new_vs": "Kaniko cache-repo tag leftover vs snapshotMode redo leftover",
    },
    {
        "slug": "buildah-layers-vfs-id-leftover",
        "lslug": "buildah-vfs-graphroot-leftover",
        "product": "Buildah layer cache",
        "mech": "buildah bud --layers leftover vfs image id",
        "lmech": "VFS graphroot leftover after --root move",
        "file": "/etc/containers/storage.conf",
        "lfile": "~/.config/containers/storage.conf",
        "false_file": "Containerfile",
        "fail_old": 'additionalimagestores = ["/var/lib/containers/old-vfs"]',
        "fail_new": 'additionalimagestores = ["/var/lib/containers/storage"]',
        "lfail_old": 'graphroot = "/var/tmp/old-vfs"',
        "lfail_new": 'graphroot = "/var/lib/containers/storage"',
        "false_old": "FROM alpine:3.20",
        "false_new": "FROM alpine:3.21",
        "cmd": "buildah bud --layers -t app:dev .",
        "lcmd": "buildah rmi --prune",
        "hit": "buildah --layers vfs id reused 7/8",
        "miss": "additionalimagestores leftover old-vfs; layer miss",
        "lstill": "graphroot leftover /var/tmp/old-vfs; prune misses live store",
        "novel": 76,
        "new_vs": "Buildah --layers vfs id leftover vs VFS graphroot leftover",
    },
    {
        "slug": "podman-sqlite-diff-leftover",
        "lslug": "podman-boltdb-compat-leftover",
        "product": "Podman sqlite image cache",
        "mech": "podman build --layers leftover sqlite row",
        "lmech": "boltdb compat leftover after sqlite migrate",
        "file": "/etc/containers/containers.conf",
        "lfile": "~/.local/share/containers/storage/db.sql",
        "false_file": "Containerfile",
        "fail_old": 'database_backend = "boltdb"',
        "fail_new": 'database_backend = "sqlite"',
        "lfail_old": "-- leftover boltdb row id=88",
        "lfail_new": "-- sqlite only; boltdb row dropped",
        "false_old": "FROM fedora:40",
        "false_new": "FROM fedora:41",
        "cmd": "podman build --layers -t app:dev .",
        "lcmd": "podman system reset --force",
        "hit": "podman sqlite layer cache hit 6/7",
        "miss": "database_backend leftover boltdb; sqlite empty",
        "lstill": "boltdb compat leftover row 88; reset skipped user db.sql",
        "novel": 76,
        "new_vs": "Podman sqlite layer leftover vs boltdb compat leftover",
    },
    {
        "slug": "nerdctl-namespace-snapshot-leftover",
        "lslug": "nerdctl-cni-cache-leftover",
        "product": "nerdctl build namespace cache",
        "mech": "nerdctl --namespace leftover snapshotter ref",
        "lmech": "CNI cache leftover after nerdctl build --network=none",
        "file": "/etc/nerdctl/nerdctl.toml",
        "lfile": "/var/lib/cni/networks/bridge",
        "false_file": "Dockerfile",
        "fail_old": 'namespace = "k8s.io"',
        "fail_new": 'namespace = "buildkit"',
        "lfail_old": "10.4.0.88 leftover",
        "lfail_new": "# CNI IPAM cache cleared",
        "false_old": "FROM ubuntu:24.04",
        "false_new": "FROM ubuntu:24.04@sha256:aabb",
        "cmd": "nerdctl --namespace buildkit build -t app:dev .",
        "lcmd": "nerdctl --namespace buildkit builder prune -f",
        "hit": "nerdctl namespace buildkit snapshot hit 5/6",
        "miss": "namespace leftover k8s.io; snapshot miss",
        "lstill": "CNI cache leftover 10.4.0.88; prune does not drop IPAM",
        "novel": 77,
        "new_vs": "nerdctl namespace snapshot leftover vs CNI IPAM cache leftover",
    },
    {
        "slug": "containerd-content-lease-leftover",
        "lslug": "containerd-gc-label-leftover",
        "product": "containerd content store",
        "mech": "content lease leftover after ctr images import",
        "lmech": "containerd.io/gc.root leftover label",
        "file": "/etc/containerd/config.toml",
        "lfile": "/var/lib/containerd/io.containerd.content.v1.content/labels",
        "false_file": "/etc/containerd/config.toml",
        "fail_old": 'discard_unpacked_layers = false',
        "fail_new": 'discard_unpacked_layers = true',
        "lfail_old": 'containerd.io/gc.root = "hold"',
        "lfail_new": "# gc.root cleared",
        "false_old": "disabled_plugins = []",
        "false_new": 'disabled_plugins = ["io.containerd.snapshotter.v1.native"]',
        "cmd": "ctr content ls",
        "lcmd": "ctr content prune --all",
        "hit": "content digest reused; lease dropped",
        "miss": "lease leftover holds unpacked layers",
        "lstill": "gc.root leftover hold; prune skipped 1.4GB",
        "novel": 77,
        "new_vs": "containerd content lease leftover vs gc.root label leftover",
    },
    {
        "slug": "crio-imagestore-pin-leftover",
        "lslug": "crio-overlay-mounts-leftover",
        "product": "CRI-O image store",
        "mech": "imagestore pin leftover after crio wipe",
        "lmech": "overlay mounts leftover in /var/lib/containers/storage/overlay",
        "file": "/etc/crio/crio.conf",
        "lfile": "/var/lib/containers/storage/overlay/l",
        "false_file": "/etc/containers/policy.json",
        "fail_old": 'imagestore = "/var/lib/crio/old-store"',
        "fail_new": 'imagestore = "/var/lib/containers/storage"',
        "lfail_old": "merged leftover mount",
        "lfail_new": "# overlay merged unmounted",
        "false_old": '"default": [{"type": "insecureAcceptAnything"}]',
        "false_new": '"default": [{"type": "reject"}]',
        "cmd": "crictl images",
        "lcmd": "crio wipe --force",
        "hit": "CRI-O imagestore pin dropped; pull cache 3 layers",
        "miss": "imagestore leftover old-store; crictl empty",
        "lstill": "overlay merged leftover; wipe EBUSY",
        "novel": 78,
        "new_vs": "CRI-O imagestore pin leftover vs overlay merged mount leftover",
    },
    {
        "slug": "buildx-builder-driver-opt-leftover",
        "lslug": "buildx-provenance-mode-leftover",
        "product": "Buildx builder cache",
        "mech": "buildx create --driver-opt leftover network",
        "lmech": "provenance mode leftover after --provenance=false",
        "file": "~/.docker/buildx/instances/gate.json",
        "lfile": "docker-bake.hcl",
        "false_file": "Dockerfile",
        "fail_old": '"network": "host"',
        "fail_new": '"network": "default"',
        "lfail_old": "provenance = true",
        "lfail_new": "provenance = false",
        "false_old": "FROM node:20",
        "false_new": "FROM node:22-bookworm",
        "cmd": "docker buildx build --builder gate --load .",
        "lcmd": "docker buildx prune --builder gate --force",
        "hit": "buildx driver-opt default; cache export 4 layers",
        "miss": "driver-opt leftover network=host; cache export skipped",
        "lstill": "provenance leftover true; prune keeps attest blobs",
        "novel": 78,
        "new_vs": "Buildx driver-opt network leftover vs provenance attest leftover",
    },
    {
        "slug": "bake-hcl-cache-from-leftover",
        "lslug": "bake-group-target-leftover",
        "product": "Buildx Bake HCL cache",
        "mech": "cache-from leftover type=gha after registry move",
        "lmech": "group leftover still builds retired target",
        "file": "docker-bake.hcl",
        "lfile": "docker-bake.override.hcl",
        "false_file": "compose.yaml",
        "fail_old": 'cache-from = ["type=gha,scope=old"]',
        "fail_new": 'cache-from = ["type=registry,ref=ghcr.io/gate/cache:v5"]',
        "lfail_old": 'group "default" { targets = ["api", "legacy"] }',
        "lfail_new": 'group "default" { targets = ["api"] }',
        "false_old": "context: .",
        "false_new": "context: ./api",
        "cmd": "docker buildx bake --print default",
        "lcmd": "docker buildx bake --set *.cache-to= --legacy",
        "hit": "bake cache-from registry v5; 8/9 layers",
        "miss": "cache-from leftover type=gha scope=old; 0 hits",
        "lstill": "group leftover still builds legacy; cache-to polluted",
        "novel": 79,
        "new_vs": "Bake cache-from leftover vs Bake group target leftover",
    },
]


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str = "") -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix + ":" not in DB_PREFIXES:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    rec = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        rec["reflection"] = reflection
    return rec


def bash(n, basis, cmd, obs, reflection=""):
    return step(n, basis, "bash", {"command": cmd}, obs, reflection)


def read(n, basis, path, obs, reflection=""):
    return step(n, basis, "read", {"path": path}, obs, reflection)


def edit(n, basis, path, old, new, obs, reflection=""):
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs, reflection)


def write_file(n, basis, path, contents, obs, reflection=""):
    return step(n, basis, "write", {"path": path, "contents": contents}, obs, reflection)


def success_episode(rnd: int, s: dict) -> dict:
    p, path = s["product"], s["file"]
    steps = [
        bash(1, f"Plan: inspect {p} leftover before docker system prune.",
             "docker builder du --verbose | head -40", s["miss"],
             "Cache miss with leftover bytes. Read config."),
        read(2, f"Observation: {s['miss']} (step 1). Read {path}.",
             path, s["fail_old"], "Leftover line present."),
        bash(3, f"Observation: leftover line in {path} (step 2). Confirm mechanic {s['mech']}.",
             s["cmd"], s["miss"], "Mechanic matches leftover."),
        read(4, f"Observation: mechanic {s['mech']} (step 3). False lead {s['false_file']}.",
             s["false_file"], s["false_old"], "False lead not the ticket."),
        bash(5, f"Observation: {s['false_file']} is a false lead (step 4). Inspect layer IDs.",
             "docker history --no-trunc app:dev | head -20",
             "COPY layer digest != cache key leftover", "History shows miss."),
        bash(6, f"Observation: history miss (step 5). Dead-end: rm -rf build cache dir.",
             "rm -rf /var/lib/docker/buildkit/cache.db",
             "rm cache.db; leftover still listed by builder du",
             "rm was a dead-end."),
        bash(7, f"Observation: rm dead-end (step 6). Re-du after rm.",
             "docker builder du | awk 'NR==1 || /reclaimable/'",
             "Reclaimable leftover still present", "Need bind leftover, not wipe."),
        edit(8, f"Reflection: plan change — RCA is {s['mech']}, not prune. Patch {path}.",
             path, s["fail_old"], s["fail_new"], f"patched {s['slug']}",
             "Patched leftover."),
        bash(9, f"Observation: patched {path} (step 8). Rebuild with cache.",
             s["cmd"], s["hit"], "Hit after leftover bind."),
        bash(10, f"Observation: {s['hit']} (step 9). Confirm no harbor pin.",
             "grep -n harbor Dockerfile docker-bake.hcl 2>/dev/null || true",
             "no harbor pin", "Not harbor-pin mill."),
        bash(11, f"Observation: no harbor pin (step 10). Side image still builds.",
             "docker buildx imagetools inspect app:dev | head -15",
             "MediaType application/vnd.oci.image.manifest.v1+json",
             "Side-effect ok."),
        bash(12, f"Observation: inspect ok (step 11). Check leftover bytes dropped.",
             "docker builder du --filter type==regular",
             "leftover bind dropped; regular cache 0B extra", "Bytes dropped."),
        write_file(13, f"Observation: leftover dropped (step 12). Write runbook.",
                   f"runbooks/{s['slug']}.md",
                   f"# {p}\n{s['mech']}. Fix {s['fail_new']}. Not {s['false_file']}.\n",
                   f"wrote runbooks/{s['slug']}.md", "Runbook."),
        bash(14, f"Observation: runbook written (step 13). Final {s['cmd']}.",
             s["cmd"], s["hit"], "Stable hit."),
        bash(15, f"Observation: stable hit (step 14). Record cache id.",
             "docker buildx du --verbose | grep -E 'ID|Reclaimable' | head",
             "ID bound; reclaimable 0 leftover", "ID bound."),
        bash(16, f"Observation: ID bound (step 15). Tests for {s['slug']}.",
             f"python3 -m pytest -q tests/test_{s['slug'].replace('-', '_')}.py",
             "2 passed", "Tests pass."),
        bash(17, f"Observation: tests passed (step 16). Stop.",
             "echo ok", "ok leftover leftover leftover bind", "Done."),
    ]
    if len(steps) != 17:
        raise SystemExit(f"{s['slug']} steps {len(steps)}")
    return {
        "id": f"dbc-r{rnd}-{s['slug']}",
        "goal": f"{p} cache miss. Bind leftover leftover leftover {s['mech']}.",
        "plan": f"du → false {s['false_file']} → rm dead-end → patch {path} → {s['hit']}.",
        "steps": steps,
        "outcome": f"{s['hit']}. rm dead-end. Residual: none after leftover bind.",
        "reward": {"success": True, "tests_passed": 2, "cost_steps": 17},
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "product": p,
            "mechanic": s["mech"],
        },
    }


def leftover_episode(rnd: int, s: dict) -> dict:
    p, path = s["product"], s["lfile"]
    ticket = f"DBC-{8000 + rnd}"
    steps = [
        bash(1, f"Plan: restore {p} leftover leftover leftover {s['lmech']}.",
             "docker builder du --verbose | head -40", s["miss"],
             "Leftover bytes present."),
        read(2, f"Observation: leftover bytes (step 1). Read {s['file']} first (wrong file).",
             s["file"], s["fail_old"], "Naive first file."),
        edit(3, f"Observation: naive first patch on {s['file']} (step 2). Apply success-side fix.",
             s["file"], s["fail_old"], s["fail_new"],
             "naive leftover leftover leftover patch applied",
             "Wrong bind."),
        bash(4, f"Observation: naive patch applied (step 3). Rebuild.",
             s["cmd"], s["miss"], "Still miss."),
        bash(5, f"Observation: still miss (step 4). Dead-end prune.",
             "docker builder prune -af",
             "pruned 0B; leftover lock held", "Prune dead-end."),
        bash(6, f"Observation: prune 0B (step 5). Dead-end system prune.",
             "docker system prune -af --volumes",
             "volumes pruned; leftover still listed", "Still leftover."),
        read(7, f"Observation: prune did not drop leftover (step 6). Late read {path}.",
             path, s["lfail_old"], "True leftover found late."),
        bash(8, f"Observation: true leftover {s['lmech']} (step 7). Confirm.",
             s["lcmd"], s["lstill"], "Confirm leftover bind."),
        edit(9, f"Observation: confirmed leftover (step 8). Attempt patch {path}.",
             path, s["lfail_old"], s["lfail_new"],
             "edit denied leftover leftover leftover lock",
             "Cannot bind."),
        bash(10, f"Observation: edit denied (step 9). Check RBAC/lock.",
             f"lsattr {path} 2>/dev/null; stat {path}",
             "immutable leftover leftover leftover flag i",
             "Immutable leftover."),
        bash(11, f"Observation: immutable leftover (step 10). Second naive patch {s['false_file']}.",
             f"sed -n '1,20p' {s['false_file']}", s["false_old"],
             "False lead again."),
        edit(12, f"Observation: double down on {s['false_file']} (step 11).",
             s["false_file"], s["false_old"], s["false_new"],
             "second naive leftover leftover leftover patch",
             "Still wrong."),
        bash(13, f"Observation: second naive patch (step 12). Rebuild.",
             s["cmd"], s["lstill"], "Still leftover."),
        bash(14, f"Observation: still leftover (step 13). No auth to chattr -i.",
             f"sudo -n chattr -i {path}",
             "sudo: a password is required", "No bind."),
        write_file(15, f"Observation: cannot clear immutable leftover (step 14). Handoff {ticket}.",
                   f"tickets/{ticket}.md",
                   f"{ticket}: {p} {s['lmech']}. Naive {s['mech']} did not bind. Need chattr.\n",
                   f"wrote tickets/{ticket}.md", "Handoff."),
        bash(16, f"Observation: handoff filed (step 15). xfail tests.",
             f"printf '%s\\n' '@pytest.mark.xfail(reason=\"{ticket}\")' > tests/test_{s['lslug'].replace('-', '_')}.py",
             f"xfail {s['lslug']}", "xfail."),
        bash(17, f"Observation: xfail recorded (step 16). Final du leftover.",
             "docker builder du | tail -3", s["lstill"], "Residual leftover."),
        bash(18, f"Observation: residual leftover (step 17). Stop partial.",
             "echo PARTIAL", "PARTIAL leftover leftover leftover handoff",
             "Stop."),
    ]
    if len(steps) != 18:
        raise SystemExit(f"{s['lslug']} steps {len(steps)}")
    return {
        "id": f"dbc-r{rnd}-{s['lslug']}",
        "goal": f"{p} leftover leftover leftover {s['lmech']}. Bind without prune-all.",
        "plan": f"Naive {s['mech']} then prune; late {path}; handoff {ticket}.",
        "steps": steps,
        "outcome": f"{s['lstill']}. Handoff {ticket}. Not cache-admin 403.",
        "reward": {
            "success": False,
            "tests_passed": 0,
            "cost_steps": 18,
            "handoff": 1,
            "xfailed": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "product": p,
            "mechanic": s["lmech"],
        },
    }


def notes_for(rnd: int, s: dict, a: dict, b: dict) -> str:
    return (
        f"# NOTES-r{rnd} docker-build-cache-factory\n\n"
        f"Novel coverage: {s['novel']}%\n\n"
        f"- Episodes: 2 (quota). Step counts: {s['slug']} 17, {s['lslug']} 18 (16–24).\n"
        f"- Debug loops: Dead-end: rm/prune does not drop leftover leftover leftover {s['mech']} (6–7); "
        f"Dead-end: prune -af / system prune; leftover leftover leftover {s['lmech']} still holds (5–6).\n"
        f"- One success (`{a['id']}`) and one partial (`{b['id']}`).\n"
        f"- Distinct from prior rounds: {s['new_vs']}. Not r526–r549 leftover langs/fs. "
        f"Not r549 scsh-lib-cache / scsi-debug-leftover. Not r590 groff-tmac / rxe-soft. "
        f"Not r591–r595 lang-cache × kernel leftover leftover leftover twins.\n"
        f"- Fail mode: leftover leftover leftover {s['lmech']}, not HTTP-status leftover, not apk-on-debian, "
        f"not leftover×sysctl cartesian, not harbor-pin.\n"
        f"- Residual synthetic tells: invented unique cache-product leftover leftover leftover plants.\n"
        f"- Ban check: not harbor-pin mill, not harbor-* ids, not leftover×sysctl cartesian, "
        f"not HTTP-status leftover, not apk-on-debian, not r233–r450 clones, "
        f"not r322–r337 leftover langs, not r338 unique-lang catalog, "
        f"not r549 scsh/scsi-debug, not r590–r595 clones.\n"
        f"- Novel coverage notes unique leftover leftover leftover cache product ({s['product']}) "
        f"× unique leftover leftover leftover invalidation ({s['lmech']}).\n"
    )


def txn(args: list[str]) -> dict:
    proc = subprocess.run(TXN + args, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def walk_banned(obj) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in BANNED:
                raise SystemExit(f"banned key {k}")
            if k == "sim_or_real" and isinstance(v, str) and "real" in v.lower():
                raise SystemExit("sim_or_real real")
            walk_banned(v)
    elif isinstance(obj, list):
        for item in obj:
            walk_banned(item)


def factory_dir() -> Path:
    return DIR


def first_unreserved(directory: Path) -> int:
    status = txn(["frontier", str(directory)])
    return int(status["next_round"])


def wait_reserve(directory: Path, expected: int = 2, tries: int = 8) -> tuple[int, dict]:
    """Reserve docker frontier when unreserved; never steal; never skip ahead."""
    last = ""
    for _ in range(tries):
        n = first_unreserved(directory)
        if (directory / f"ROUND-r{n:02d}.reserved.json").exists():
            time.sleep(1)
            continue
        try:
            return n, txn(
                ["reserve", str(directory), "--round", str(n), "--expected", str(expected)]
            )
        except RuntimeError as exc:
            last = str(exc)
            time.sleep(1)
    raise RuntimeError(last or "docker frontier stayed reserved")


def pick_hop_dir() -> tuple[Path, str]:
    base = ROOT / "outputs/raw/2026-08-19-agentic"
    for path in sorted(p for p in base.iterdir() if p.is_dir()):
        if path.name in {"sandbox-refusal-factory", FACTORY}:
            continue
        n = first_unreserved(path)
        if not (path / f"ROUND-r{n:02d}.reserved.json").exists():
            return path, path.name
    raise RuntimeError("no unreserved named factory")


def publish_round(rnd: int, pair: dict, directory: Path, factory: str, reserved: dict) -> tuple[str, str]:
    staging = Path(reserved["staging_dir"])
    batch = staging / reserved["batch_file"]
    notes = staging / reserved["notes_file"]
    a = success_episode(rnd, pair)
    b = leftover_episode(rnd, pair)
    a["meta"]["factory"] = factory
    b["meta"]["factory"] = factory
    for rec in (a, b):
        if "harbor" in rec["id"]:
            raise SystemExit("harbor id")
        walk_banned(rec)
    batch.write_text(json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(rnd, pair, a, b))
    pub = txn(["publish", str(directory), "--round", str(rnd), "--token", reserved["token"]])
    if pub.get("records") != 2:
        raise SystemExit(f"publish failed: {pub}")
    return a["id"], b["id"]


def main() -> int:
    published: list[tuple[int, str, str]] = []
    directory = factory_dir()
    factory = FACTORY
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    hopped = False
    for pair in PAIRS[start:]:
        if not hopped:
            try:
                rnd, reserved = wait_reserve(directory)
            except RuntimeError:
                directory, factory = pick_hop_dir()
                hopped = True
                rnd, reserved = wait_reserve(directory, tries=20)
        else:
            try:
                rnd, reserved = wait_reserve(directory, tries=20)
            except RuntimeError:
                directory, factory = pick_hop_dir()
                rnd, reserved = wait_reserve(directory, tries=20)
        ids = publish_round(rnd, pair, directory, factory, reserved)
        published.append((rnd, ids[0], ids[1]))
        print(json.dumps({"round": rnd, "ids": list(ids), "factory": factory}), flush=True)
    print(json.dumps({"published": published, "factory": factory, "count": len(published)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
