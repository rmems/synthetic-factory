#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 23: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "docker-layer-leftover-as-dest", "dklr", "docker layer leftover", "overlay2/layer", "docker layer leftover", "docker leftover && ls overlay2/layer", "not docker-layer leftover; docker layer leftover is not dest", "treat leftover docker layer as dest then CLI parquet.", "docker leftover; # overlay2/layer claimed dest", "docker leftover|overlay2/layer"),
    s_from(1, "buildah-containers-leftover-as-dest", "bhct", "buildah containers leftover", "buildah/containers", "buildah containers leftover", "buildah leftover && ls buildah/containers", "not buildah-containers leftover; buildah containers leftover is not dest", "treat leftover buildah containers as dest then CLI parquet.", "buildah leftover; # buildah/containers claimed dest", "buildah leftover|buildah/containers"),
    s_from(2, "podman-storage-leftover-as-dest", "pdst", "podman storage leftover", "podman/storage", "podman storage leftover", "podman leftover && ls podman/storage", "not podman-storage leftover; podman storage leftover is not dest", "treat leftover podman storage as dest then CLI parquet.", "podman leftover; # podman/storage claimed dest", "podman leftover|podman/storage"),
    s_from(3, "nerdctl-namespace-leftover-as-dest", "ncns", "nerdctl namespace leftover", "nerdctl/namespace", "nerdctl namespace leftover", "nerdctl leftover && ls nerdctl/namespace", "not nerdctl-namespace leftover; nerdctl namespace leftover is not dest", "treat leftover nerdctl namespace as dest then CLI parquet.", "nerdctl leftover; # nerdctl/namespace claimed dest", "nerdctl leftover|nerdctl/namespace"),
    s_from(4, "kaniko-cache-leftover-as-dest", "knch", "kaniko cache leftover", "kaniko/cache", "kaniko cache leftover", "kaniko leftover && ls kaniko/cache", "not kaniko-cache leftover; kaniko cache leftover is not dest", "treat leftover kaniko cache as dest then CLI parquet.", "kaniko leftover; # kaniko/cache claimed dest", "kaniko leftover|kaniko/cache"),
    s_from(5, "buildkit-cache-leftover-as-dest", "bkch2", "buildkit cache leftover", "buildkit/cache", "buildkit cache leftover", "buildkit leftover && ls buildkit/cache", "not buildkit-cache leftover; buildkit cache leftover is not dest", "treat leftover buildkit cache as dest then CLI parquet.", "buildkit leftover; # buildkit/cache claimed dest", "buildkit leftover|buildkit/cache"),
    s_from(6, "img-cache-leftover-as-dest", "imch", "img cache leftover", "img/cache", "img cache leftover", "img leftover && ls img/cache", "not img-cache leftover; img cache leftover is not dest", "treat leftover img cache as dest then CLI parquet.", "img leftover; # img/cache claimed dest", "img leftover|img/cache"),
    s_from(7, "ko-cache-leftover-as-dest", "koch", "ko cache leftover", "ko/cache", "ko cache leftover", "ko leftover && ls ko/cache", "not ko-cache leftover; ko cache leftover is not dest", "treat leftover ko cache as dest then CLI parquet.", "ko leftover; # ko/cache claimed dest", "ko leftover|ko/cache"),
    s_from(8, "crane-layout-leftover-as-dest", "crly", "crane layout leftover", "crane/oci", "crane layout leftover", "crane leftover && ls crane/oci", "not crane-layout leftover; crane layout leftover is not dest", "treat leftover crane layout as dest then CLI parquet.", "crane leftover; # crane/oci claimed dest", "crane leftover|crane/oci"),
    s_from(9, "skopeo-dir-leftover-as-dest", "skdr", "skopeo dir leftover", "skopeo/dir", "skopeo dir leftover", "skopeo leftover && ls skopeo/dir", "not skopeo-dir leftover; skopeo dir leftover is not dest", "treat leftover skopeo dir as dest then CLI parquet.", "skopeo leftover; # skopeo/dir claimed dest", "skopeo leftover|skopeo/dir"),
    s_from(10, "oras-layout-leftover-as-dest", "orly", "oras layout leftover", "oras/oci", "oras layout leftover", "oras leftover && ls oras/oci", "not oras-layout leftover; oras layout leftover is not dest", "treat leftover oras layout as dest then CLI parquet.", "oras leftover; # oras/oci claimed dest", "oras leftover|oras/oci"),
    s_from(11, "compose-override-leftover-as-dest", "cmov", "compose override leftover", "compose.override.yml", "compose override leftover", "compose leftover && ls compose.override.yml", "not compose-override leftover; compose override leftover is not dest", "treat leftover compose override as dest then CLI parquet.", "compose leftover; # compose.override.yml claimed dest", "compose leftover|compose.override.yml"),
    s_from(12, "buildx-bake-leftover-as-dest", "bxbk", "buildx bake leftover", "bake.json", "buildx bake leftover", "buildx leftover && ls bake.json", "not buildx-bake leftover; buildx bake leftover is not dest", "treat leftover buildx bake as dest then CLI parquet.", "buildx leftover; # bake.json claimed dest", "buildx leftover|bake.json"),
    s_from(13, "containerd-io-leftover-as-dest", "cdio", "containerd io leftover", "containerd/io.containerd", "containerd io leftover", "containerd leftover && ls containerd/io.containerd", "not containerd-io leftover; containerd io leftover is not dest", "treat leftover containerd io as dest then CLI parquet.", "containerd leftover; # containerd/io.containerd claimed dest", "containerd leftover|containerd/io.containerd"),
    s_from(14, "crio-storage-leftover-as-dest", "crst2", "crio storage leftover", "crio/storage", "crio storage leftover", "crio leftover && ls crio/storage", "not crio-storage leftover; crio storage leftover is not dest", "treat leftover crio storage as dest then CLI parquet.", "crio leftover; # crio/storage claimed dest", "crio leftover|crio/storage"),
    s_from(15, "runc-state-leftover-as-dest", "rcst", "runc state leftover", "runc/state", "runc state leftover", "runc leftover && ls runc/state", "not runc-state leftover; runc state leftover is not dest", "treat leftover runc state as dest then CLI parquet.", "runc leftover; # runc/state claimed dest", "runc leftover|runc/state"),
    s_from(16, "nydus-cache-leftover-as-dest", "nych", "nydus cache leftover", "nydus/cache", "nydus cache leftover", "nydus leftover && ls nydus/cache", "not nydus-cache leftover; nydus cache leftover is not dest", "treat leftover nydus cache as dest then CLI parquet.", "nydus leftover; # nydus/cache claimed dest", "nydus leftover|nydus/cache"),
    s_from(17, "stargz-cache-leftover-as-dest", "sgch", "stargz cache leftover", "stargz/cache", "stargz cache leftover", "stargz leftover && ls stargz/cache", "not stargz-cache leftover; stargz cache leftover is not dest", "treat leftover stargz cache as dest then CLI parquet.", "stargz leftover; # stargz/cache claimed dest", "stargz leftover|stargz/cache"),
    s_from(18, "overlayfs-diff-leftover-as-dest", "ovdf", "overlayfs diff leftover", "overlay/diff", "overlayfs diff leftover", "overlayfs leftover && ls overlay/diff", "not overlayfs-diff leftover; overlayfs diff leftover is not dest", "treat leftover overlayfs diff as dest then CLI parquet.", "overlayfs leftover; # overlay/diff claimed dest", "overlayfs leftover|overlay/diff"),
    s_from(19, "umoci-layout-leftover-as-dest", "umly", "umoci layout leftover", "umoci/oci", "umoci layout leftover", "umoci leftover && ls umoci/oci", "not umoci-layout leftover; umoci layout leftover is not dest", "treat leftover umoci layout as dest then CLI parquet.", "umoci leftover; # umoci/oci claimed dest", "umoci leftover|umoci/oci"),
    s_from(20, "buildah-vfs-leftover-as-dest", "bhvf", "buildah vfs leftover", "buildah/vfs", "buildah vfs leftover", "buildah leftover && ls buildah/vfs", "not buildah-vfs leftover; buildah vfs leftover is not dest", "treat leftover buildah vfs as dest then CLI parquet.", "buildah leftover; # buildah/vfs claimed dest", "buildah leftover|buildah/vfs"),
    s_from(21, "podman-tmp-leftover-as-dest", "pdtm", "podman tmp leftover", "podman/tmp", "podman tmp leftover", "podman leftover && ls podman/tmp", "not podman-tmp leftover; podman tmp leftover is not dest", "treat leftover podman tmp as dest then CLI parquet.", "podman leftover; # podman/tmp claimed dest", "podman leftover|podman/tmp"),
    s_from(22, "docker-tmp-leftover-as-dest", "dktm", "docker tmp leftover", "docker/tmp", "docker tmp leftover", "docker leftover && ls docker/tmp", "not docker-tmp leftover; docker tmp leftover is not dest", "treat leftover docker tmp as dest then CLI parquet.", "docker leftover; # docker/tmp claimed dest", "docker leftover|docker/tmp"),
    s_from(23, "kaniko-snapshot-leftover-as-dest", "knsn", "kaniko snapshot leftover", "kaniko/snapshot", "kaniko snapshot leftover", "kaniko leftover && ls kaniko/snapshot", "not kaniko-snapshot leftover; kaniko snapshot leftover is not dest", "treat leftover kaniko snapshot as dest then CLI parquet.", "kaniko leftover; # kaniko/snapshot claimed dest", "kaniko leftover|kaniko/snapshot"),
    s_from(24, "ko-sbom-leftover-as-dest", "kosb", "ko sbom leftover", "ko.sbom.json", "ko sbom leftover", "ko leftover && ls ko.sbom.json", "not ko-sbom leftover; ko sbom leftover is not dest", "treat leftover ko sbom as dest then CLI parquet.", "ko leftover; # ko.sbom.json claimed dest", "ko leftover|ko.sbom.json"),
    s_from(25, "crane-index-leftover-as-dest", "crix", "crane index leftover", "crane/index.json", "crane index leftover", "crane leftover && ls crane/index.json", "not crane-index leftover; crane index leftover is not dest", "treat leftover crane index as dest then CLI parquet.", "crane leftover; # crane/index.json claimed dest", "crane leftover|crane/index.json"),
    s_from(26, "skopeo-tls-leftover-as-dest", "sktl", "skopeo tls leftover", "skopeo/tls", "skopeo tls leftover", "skopeo leftover && ls skopeo/tls", "not skopeo-tls leftover; skopeo tls leftover is not dest", "treat leftover skopeo tls as dest then CLI parquet.", "skopeo leftover; # skopeo/tls claimed dest", "skopeo leftover|skopeo/tls"),
    s_from(27, "oras-blob-leftover-as-dest", "orbl", "oras blob leftover", "oras/blobs", "oras blob leftover", "oras leftover && ls oras/blobs", "not oras-blob leftover; oras blob leftover is not dest", "treat leftover oras blob as dest then CLI parquet.", "oras leftover; # oras/blobs claimed dest", "oras leftover|oras/blobs"),
    s_from(28, "docker-plugin-leftover-as-dest", "dkpl", "docker plugin leftover", "docker/plugins", "docker plugin leftover", "docker leftover && ls docker/plugins", "not docker-plugin leftover; docker plugin leftover is not dest", "treat leftover docker plugin as dest then CLI parquet.", "docker leftover; # docker/plugins claimed dest", "docker leftover|docker/plugins"),
    s_from(29, "compose-lock-leftover-as-dest", "cmlk", "compose lock leftover", "compose.lock", "compose lock leftover", "compose leftover && ls compose.lock", "not compose-lock leftover; compose lock leftover is not dest", "treat leftover compose lock as dest then CLI parquet.", "compose leftover; # compose.lock claimed dest", "compose leftover|compose.lock"),
    s_from(30, "containerd-snapshot-leftover-as-dest", "cdsn", "containerd snapshot leftover", "containerd/snapshots", "containerd snapshot leftover", "containerd leftover && ls containerd/snapshots", "not containerd-snapshot leftover; containerd snapshot leftover is not dest", "treat leftover containerd snapshot as dest then CLI parquet.", "containerd leftover; # containerd/snapshots claimed dest", "containerd leftover|containerd/snapshots"),
    s_from(31, "buildx-cache-leftover-as-dest", "bxch", "buildx cache leftover", "buildx/cache", "buildx cache leftover", "buildx leftover && ls buildx/cache", "not buildx-cache leftover; buildx cache leftover is not dest", "treat leftover buildx cache as dest then CLI parquet.", "buildx leftover; # buildx/cache claimed dest", "buildx leftover|buildx/cache"),
]

LEFTOVER = [
    l_from(0, "docker-log-leftover-handoff", "dklg", "docker.log", "docker log leftover", "docker log leftover", "not docker layer leftover; leftover docker log as dest", "ship leftover docker log as dest.", "docker log leftover; # docker.log on disk", "docker leftover|docker.log"),
    l_from(1, "buildah-log-leftover-handoff", "bhlg", "buildah.log", "buildah log leftover", "buildah log leftover", "not buildah containers leftover; leftover buildah log as dest", "ship leftover buildah log as dest.", "buildah log leftover; # buildah.log on disk", "buildah leftover|buildah.log"),
    l_from(2, "podman-log-leftover-handoff", "pdlg", "podman.log", "podman log leftover", "podman log leftover", "not podman storage leftover; leftover podman log as dest", "ship leftover podman log as dest.", "podman log leftover; # podman.log on disk", "podman leftover|podman.log"),
    l_from(3, "nerdctl-log-leftover-handoff", "nclg", "nerdctl.log", "nerdctl log leftover", "nerdctl log leftover", "not nerdctl namespace leftover; leftover nerdctl log as dest", "ship leftover nerdctl log as dest.", "nerdctl log leftover; # nerdctl.log on disk", "nerdctl leftover|nerdctl.log"),
    l_from(4, "kaniko-log-leftover-handoff", "knlg", "kaniko.log", "kaniko log leftover", "kaniko log leftover", "not kaniko cache leftover; leftover kaniko log as dest", "ship leftover kaniko log as dest.", "kaniko log leftover; # kaniko.log on disk", "kaniko leftover|kaniko.log"),
    l_from(5, "buildkit-log-leftover-handoff", "bklg2", "buildkit.log", "buildkit log leftover", "buildkit log leftover", "not buildkit cache leftover; leftover buildkit log as dest", "ship leftover buildkit log as dest.", "buildkit log leftover; # buildkit.log on disk", "buildkit leftover|buildkit.log"),
    l_from(6, "img-log-leftover-handoff", "imlg2", "img.log", "img log leftover", "img log leftover", "not img cache leftover; leftover img log as dest", "ship leftover img log as dest.", "img log leftover; # img.log on disk", "img leftover|img.log"),
    l_from(7, "ko-log-leftover-handoff", "kolg", "ko.log", "ko log leftover", "ko log leftover", "not ko cache leftover; leftover ko log as dest", "ship leftover ko log as dest.", "ko log leftover; # ko.log on disk", "ko leftover|ko.log"),
    l_from(8, "crane-log-leftover-handoff", "crlg2", "crane.log", "crane log leftover", "crane log leftover", "not crane layout leftover; leftover crane log as dest", "ship leftover crane log as dest.", "crane log leftover; # crane.log on disk", "crane leftover|crane.log"),
    l_from(9, "skopeo-log-leftover-handoff", "sklg", "skopeo.log", "skopeo log leftover", "skopeo log leftover", "not skopeo dir leftover; leftover skopeo log as dest", "ship leftover skopeo log as dest.", "skopeo log leftover; # skopeo.log on disk", "skopeo leftover|skopeo.log"),
    l_from(10, "oras-log-leftover-handoff", "orlg", "oras.log", "oras log leftover", "oras log leftover", "not oras layout leftover; leftover oras log as dest", "ship leftover oras log as dest.", "oras log leftover; # oras.log on disk", "oras leftover|oras.log"),
    l_from(11, "compose-log-leftover-handoff", "cmlg", "compose.log", "compose log leftover", "compose log leftover", "not compose override leftover; leftover compose log as dest", "ship leftover compose log as dest.", "compose log leftover; # compose.log on disk", "compose leftover|compose.log"),
    l_from(12, "buildx-log-leftover-handoff", "bxlg", "buildx.log", "buildx log leftover", "buildx log leftover", "not buildx bake leftover; leftover buildx log as dest", "ship leftover buildx log as dest.", "buildx log leftover; # buildx.log on disk", "buildx leftover|buildx.log"),
    l_from(13, "containerd-log-leftover-handoff", "cdlg", "containerd.log", "containerd log leftover", "containerd log leftover", "not containerd io leftover; leftover containerd log as dest", "ship leftover containerd log as dest.", "containerd log leftover; # containerd.log on disk", "containerd leftover|containerd.log"),
    l_from(14, "crio-log-leftover-handoff", "crlg3", "crio.log", "crio log leftover", "crio log leftover", "not crio storage leftover; leftover crio log as dest", "ship leftover crio log as dest.", "crio log leftover; # crio.log on disk", "crio leftover|crio.log"),
    l_from(15, "runc-log-leftover-handoff", "rclg", "runc.log", "runc log leftover", "runc log leftover", "not runc state leftover; leftover runc log as dest", "ship leftover runc log as dest.", "runc log leftover; # runc.log on disk", "runc leftover|runc.log"),
    l_from(16, "nydus-log-leftover-handoff", "nylg", "nydus.log", "nydus log leftover", "nydus log leftover", "not nydus cache leftover; leftover nydus log as dest", "ship leftover nydus log as dest.", "nydus log leftover; # nydus.log on disk", "nydus leftover|nydus.log"),
    l_from(17, "stargz-log-leftover-handoff", "sglg2", "stargz.log", "stargz log leftover", "stargz log leftover", "not stargz cache leftover; leftover stargz log as dest", "ship leftover stargz log as dest.", "stargz log leftover; # stargz.log on disk", "stargz leftover|stargz.log"),
    l_from(18, "overlayfs-log-leftover-handoff", "ovlg", "overlay.log", "overlayfs log leftover", "overlayfs log leftover", "not overlayfs diff leftover; leftover overlayfs log as dest", "ship leftover overlayfs log as dest.", "overlayfs log leftover; # overlay.log on disk", "overlayfs leftover|overlay.log"),
    l_from(19, "umoci-log-leftover-handoff", "umlg", "umoci.log", "umoci log leftover", "umoci log leftover", "not umoci layout leftover; leftover umoci log as dest", "ship leftover umoci log as dest.", "umoci log leftover; # umoci.log on disk", "umoci leftover|umoci.log"),
    l_from(20, "buildah-tmp-leftover-handoff", "bhtm", "buildah/tmp", "buildah tmp leftover", "buildah tmp leftover", "not buildah vfs leftover; leftover buildah tmp as dest", "ship leftover buildah tmp as dest.", "buildah tmp leftover; # buildah/tmp on disk", "buildah leftover|buildah/tmp"),
    l_from(21, "podman-events-leftover-handoff", "pdev", "podman/events", "podman events leftover", "podman events leftover", "not podman tmp leftover; leftover podman events as dest", "ship leftover podman events as dest.", "podman events leftover; # podman/events on disk", "podman leftover|podman/events"),
    l_from(22, "docker-events-leftover-handoff", "dkev", "docker/events", "docker events leftover", "docker events leftover", "not docker tmp leftover; leftover docker events as dest", "ship leftover docker events as dest.", "docker events leftover; # docker/events on disk", "docker leftover|docker/events"),
    l_from(23, "kaniko-log2-leftover-handoff", "knl2", "kaniko/build.log", "kaniko build log leftover", "kaniko build log leftover", "not kaniko snapshot leftover; leftover kaniko build log as dest", "ship leftover kaniko build log as dest.", "kaniko build log leftover; # kaniko/build.log on disk", "kaniko leftover|kaniko/build.log"),
    l_from(24, "ko-attest-leftover-handoff", "koat", "ko.intoto.json", "ko attest leftover", "ko attest leftover", "not ko sbom leftover; leftover ko attest as dest", "ship leftover ko attest as dest.", "ko attest leftover; # ko.intoto.json on disk", "ko leftover|ko.intoto.json"),
    l_from(25, "crane-config-leftover-handoff", "crcf2", "crane/config.json", "crane config leftover", "crane config leftover", "not crane index leftover; leftover crane config as dest", "ship leftover crane config as dest.", "crane config leftover; # crane/config.json on disk", "crane leftover|crane/config.json"),
    l_from(26, "skopeo-policy-leftover-handoff", "skpl", "skopeo/policy.json", "skopeo policy leftover", "skopeo policy leftover", "not skopeo tls leftover; leftover skopeo policy as dest", "ship leftover skopeo policy as dest.", "skopeo policy leftover; # skopeo/policy.json on disk", "skopeo leftover|skopeo/policy.json"),
    l_from(27, "oras-manifest-leftover-handoff", "ormf", "oras/manifest.json", "oras manifest leftover", "oras manifest leftover", "not oras blob leftover; leftover oras manifest as dest", "ship leftover oras manifest as dest.", "oras manifest leftover; # oras/manifest.json on disk", "oras leftover|oras/manifest.json"),
    l_from(28, "docker-network-leftover-handoff", "dknw", "docker/network", "docker network leftover", "docker network leftover", "not docker plugin leftover; leftover docker network as dest", "ship leftover docker network as dest.", "docker network leftover; # docker/network on disk", "docker leftover|docker/network"),
    l_from(29, "compose-env-leftover-handoff", "cmen", ".env.compose.bak", "compose env leftover", "compose env leftover", "not compose lock leftover; leftover compose env as dest", "ship leftover compose env as dest.", "compose env leftover; # .env.compose.bak on disk", "compose leftover|.env.compose.bak"),
    l_from(30, "containerd-meta-leftover-handoff", "cdmt", "containerd/metadata", "containerd meta leftover", "containerd meta leftover", "not containerd snapshot leftover; leftover containerd meta as dest", "ship leftover containerd meta as dest.", "containerd meta leftover; # containerd/metadata on disk", "containerd leftover|containerd/metadata"),
    l_from(31, "buildx-state-leftover-handoff", "bxst", "buildx/state", "buildx state leftover", "buildx state leftover", "not buildx cache leftover; leftover buildx state as dest", "ship leftover buildx state as dest.", "buildx state leftover; # buildx/state on disk", "buildx leftover|buildx/state"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll23.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
