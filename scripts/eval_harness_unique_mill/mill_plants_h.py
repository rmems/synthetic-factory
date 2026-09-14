"""Unique eval-harness leftover plants r356–r379. Not r319/GEval-cache/test_ clones."""

from mill_plants import PAIRS, _bad, _ok

# r356 container leftover
PAIRS.append(
    (
        _ok(
            slug="podman-image-latest-r87y",
            domain="podman-eval",
            kind="container",
            avoided="r268 docker layer; r344 packer ami; r319 ClearML uri",
            goal=(
                "Podman leftover image eval:latest still has yesterday goldens so planted "
                "seat-void never boots. Pin the image to eval:<sha>."
            ),
            plan="Dump image tag, pin sha, prove planted seat-void fail.",
            outcome=(
                "Image is eval:<sha>. Planted seat-void 0.13 fail-closed. Residual: a quadlet "
                "leftover still Image=eval:latest."
            ),
            ticket=(
                "Title: Podman leftover eval:latest. planted seat-void missing in the image."
            ),
            src="evals/eval.container",
            src_obs="Image=eval:latest  # leftover",
            run="evals/podman_eval.py",
            fail_obs="latest leftover yesterday goldens. planted seat-void absent",
            inspect="evals/eval.container",
            inspect_obs="latest leftover. no sha tag",
            first_path="evals/eval.container",
            first_old="Image=eval:latest",
            first_new="Image=eval:${GIT_SHA}",
            first_obs="sha local. quadlet leftover still latest",
            rate_tail="quadlet leftover Image=eval:latest",
            still_after_429="quadlet leftover latest; planted seat-void absent",
            grep="eval:latest|Image=|GIT_SHA",
            grep_obs="force eval:<sha>; ignore quadlet leftover",
            plan_change="image eval:<sha>; refuse latest",
            fix_path="evals/eval.container",
            fix_old="Image=eval:${GIT_SHA}",
            fix_new="Image=eval-${GIT_SHA}",
            fix_obs="planted seat-void 0.13 in sha image",
            retry_obs="502 then retry; 5 pass 1 fail planted seat-void 0.13",
            test="tests/test_podman_image_sha.py",
            test_body="assert image is eval:<sha>; latest unused",
            test_obs="test_podman_not_eval_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed seat-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed seat-void",
            diff_obs=" evals/eval.container | 2+-\n tests/test_podman_image_sha.py | 12++\n",
            residual="Quadlet leftover still Image=eval:latest.",
        ),
        _bad(
            slug="buildah-bud-cache-s88z",
            domain="buildah-eval",
            kind="container",
            avoided="r268 docker layer; r308 earthly cache; r319 Aim hash",
            goal=(
                "Buildah leftover bud --layers cache omits goldens so planted overbook-void "
                "never copies. Include goldens in the cache key."
            ),
            plan="Dump bud layers, add goldens, prove planted overbook-void locally.",
            outcome=(
                "Local bud cache keys goldens digest. Planted overbook-void present locally. "
                "Handoff: the builder leftover still --layers without goldens."
            ),
            ticket=(
                "Title: Buildah leftover bud --layers. planted overbook-void missing from image."
            ),
            src="evals/Containerfile",
            src_obs="COPY evals /eval/evals  # leftover no goldens",
            run="evals/buildah_eval.py",
            fail_obs="layers leftover HIT. planted overbook-void absent",
            inspect="evals/Containerfile",
            inspect_obs="COPY leftover evals only",
            first_path="evals/Containerfile",
            first_old="COPY evals /eval/evals",
            first_new="COPY evals /eval/evals\n# TODO goldens",
            first_obs="comment only. builder leftover still --layers omit",
            rate_tail="builder leftover --layers omit goldens",
            still_after_429="builder leftover HIT; planted overbook-void absent",
            grep="COPY goldens|--layers|Containerfile",
            grep_obs="cannot change builder leftover from this ticket",
            plan_change="local COPY goldens; document builder leftover layers",
            fix_path="evals/Containerfile",
            fix_old="# TODO goldens",
            fix_new="COPY goldens /eval/goldens",
            fix_obs="local planted present. builder leftover HANDOFF",
            retry_obs="502 unused. builder leftover --layers. Partial",
            test="tests/test_buildah_copy_goldens.py",
            test_body="xfail builder leftover layers; local COPY goldens",
            test_obs="builder leftover --layers. Partial",
            suite_obs="local COPY goldens. builder leftover layers. Partial.",
            gate_obs="local COPY goldens. builder leftover layers. Partial.",
            diff_obs=" evals/Containerfile | 2+-\n HANDOFF buildah layers\n",
            residual="Builder leftover still --layers without goldens. Partial.",
        ),
    )
)

# r357 runtime leftover
PAIRS.append(
    (
        _ok(
            slug="nerdctl-ns-stale-t89a",
            domain="nerdctl-eval",
            kind="container",
            avoided="r356 podman latest; r268 docker layer; r319 ClearML uri",
            goal=(
                "nerdctl leftover --namespace eval still mounts yesterday's goldens so planted "
                "rain-void never appears. Pin the namespace to eval-<sha>."
            ),
            plan="Dump namespace, pin sha, prove planted rain-void fail.",
            outcome=(
                "Namespace is eval-<sha>. Planted rain-void 0.14 fail-closed. Residual: an "
                "alias leftover still nerdctl --namespace eval."
            ),
            ticket=(
                "Title: nerdctl leftover --namespace eval. planted rain-void missing."
            ),
            src="evals/nerdctl.sh",
            src_obs="nerdctl --namespace eval run eval:sha  # leftover stable ns",
            run="evals/nerdctl_eval.py",
            fail_obs="ns leftover yesterday volume. planted rain-void absent",
            inspect="evals/nerdctl.sh",
            inspect_obs="stable namespace leftover",
            first_path="evals/nerdctl.sh",
            first_old="--namespace eval",
            first_new="--namespace eval-dev",
            first_obs="dev local. alias leftover still --namespace eval",
            rate_tail="alias leftover --namespace eval",
            still_after_429="alias leftover ns; planted rain-void absent",
            grep="--namespace eval|nerdctl|goldens",
            grep_obs="force eval-<sha>; ignore alias leftover",
            plan_change="namespace eval-<sha>; refuse bare eval",
            fix_path="evals/nerdctl.sh",
            fix_old="--namespace eval-dev",
            fix_new="--namespace eval-$GIT_SHA",
            fix_obs="planted rain-void 0.14 in sha ns",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-void 0.14",
            test="tests/test_nerdctl_ns_sha.py",
            test_body="assert namespace is eval-<sha>; bare eval unused",
            test_obs="test_nerdctl_not_bare_ns",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-void",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-void",
            diff_obs=" evals/nerdctl.sh | 2+-\n tests/test_nerdctl_ns_sha.py | 12++\n",
            residual="Alias leftover still nerdctl --namespace eval.",
        ),
        _bad(
            slug="containerd-snapshot-u90b",
            domain="containerd-eval",
            kind="container",
            avoided="r268 docker layer; r356 buildah layers; r319 Aim hash",
            goal=(
                "containerd leftover snapshot eval-latest still has yesterday goldens so planted "
                "flash-void-2 never unpacks. Pin the snapshot to eval-<sha>."
            ),
            plan="Dump snapshot, pin sha, prove planted flash-void-2 locally.",
            outcome=(
                "Local snapshot eval-<sha>. Planted flash-void-2 present locally. Handoff: the "
                "node leftover still prepares eval-latest."
            ),
            ticket=(
                "Title: containerd leftover snapshot eval-latest. planted flash-void-2 missing."
            ),
            src="evals/containerd.toml",
            src_obs='snapshotter = "overlayfs"  # leftover key eval-latest',
            run="evals/containerd_eval.py",
            fail_obs="snapshot leftover eval-latest. planted flash-void-2 absent",
            inspect="evals/containerd.toml",
            inspect_obs="eval-latest leftover snapshot key",
            first_path="evals/containerd.toml",
            first_old='snapshotter = "overlayfs"',
            first_new='snapshotter = "overlayfs"  # + sha key',
            first_obs="comment only. node leftover still eval-latest",
            rate_tail="node leftover snapshot eval-latest",
            still_after_429="node leftover latest; planted flash-void-2 absent",
            grep="eval-latest|snapshot|containerd",
            grep_obs="cannot change node leftover from this ticket",
            plan_change="local snapshot sha key; document node leftover latest",
            fix_path="evals/containerd_eval.py",
            fix_old="snapshot = 'eval-latest'",
            fix_new="snapshot = f'eval-{git_sha}'",
            fix_obs="local planted present. node leftover HANDOFF",
            retry_obs="502 unused. node leftover eval-latest. Partial",
            test="tests/test_containerd_snapshot_sha.py",
            test_body="xfail node leftover latest; local sha snapshot",
            test_obs="node leftover eval-latest. Partial",
            suite_obs="local sha snapshot. node leftover latest. Partial.",
            gate_obs="local sha snapshot. node leftover latest. Partial.",
            diff_obs=" evals/containerd_eval.py | 2+-\n HANDOFF containerd node\n",
            residual="Node leftover still prepares snapshot eval-latest. Partial.",
        ),
    )
)

# r358 vm leftover
PAIRS.append(
    (
        _ok(
            slug="firecracker-rootfs-v91c",
            domain="firecracker-eval",
            kind="vm",
            avoided="r344 packer ami; r344 vagrant sync; r319 ClearML uri",
            goal=(
                "Firecracker leftover rootfs.ext4 is last week's image so planted "
                "promo-void-2 never boots. Rebuild rootfs from this SHA."
            ),
            plan="Dump rootfs mtime, rebuild, prove planted promo-void-2 fail.",
            outcome=(
                "rootfs rebuilt. Planted promo-void-2 0.15 fail-closed. Residual: a jailer "
                "leftover still --root-drive lastweek.ext4."
            ),
            ticket=(
                "Title: Firecracker leftover rootfs.ext4 last week. planted promo-void-2 missing."
            ),
            src="evals/vm.json",
            src_obs='"path": "rootfs.ext4"  # leftover last week',
            run="evals/firecracker_eval.py",
            fail_obs="rootfs leftover last week goldens. planted promo-void-2 absent",
            inspect="evals/vm.json",
            inspect_obs="stable rootfs leftover",
            first_path="evals/vm.json",
            first_old='"path": "rootfs.ext4"',
            first_new='"path": "rootfs-dev.ext4"',
            first_obs="dev local. jailer leftover still lastweek.ext4",
            rate_tail="jailer leftover --root-drive lastweek.ext4",
            still_after_429="jailer leftover lastweek; planted promo-void-2 absent",
            grep="rootfs|lastweek|jailer",
            grep_obs="rebuild rootfs-<sha>.ext4; ignore jailer leftover",
            plan_change="rootfs eval-<sha>.ext4; refuse lastweek image",
            fix_path="evals/vm.json",
            fix_old='"path": "rootfs-dev.ext4"',
            fix_new='"path": "rootfs-{{sha}}.ext4"',
            fix_obs="planted promo-void-2 0.15 in sha rootfs",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-void-2 0.15",
            test="tests/test_firecracker_rootfs_sha.py",
            test_body="assert rootfs path includes sha; lastweek unused",
            test_obs="test_firecracker_not_lastweek_rootfs",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-2",
            diff_obs=" evals/vm.json | 2+-\n tests/test_firecracker_rootfs_sha.py | 12++\n",
            residual="Jailer leftover still --root-drive lastweek.ext4.",
        ),
        _bad(
            slug="kata-image-stale-w92d",
            domain="kata-eval",
            kind="vm",
            avoided="r344 packer; r356 podman latest; r319 Aim hash",
            goal=(
                "Kata leftover image kata-eval.img is last week so planted gift-void-2 never "
                "appears. Pin the image to this SHA locally."
            ),
            plan="Dump kata image, pin sha, prove planted gift-void-2 locally.",
            outcome=(
                "Local image kata-eval-<sha>.img. Planted gift-void-2 present locally. Handoff: "
                "the runtime leftover still kata-eval.img."
            ),
            ticket=(
                "Title: Kata leftover kata-eval.img last week. planted gift-void-2 missing."
            ),
            src="evals/kata.toml",
            src_obs='image = "/opt/kata-eval.img"  # leftover',
            run="evals/kata_eval.py",
            fail_obs="img leftover last week. planted gift-void-2 absent",
            inspect="evals/kata.toml",
            inspect_obs="stable image leftover",
            first_path="evals/kata.toml",
            first_old='image = "/opt/kata-eval.img"',
            first_new='image = "/opt/kata-eval-dev.img"',
            first_obs="dev local. runtime leftover still kata-eval.img",
            rate_tail="runtime leftover /opt/kata-eval.img",
            still_after_429="runtime leftover img; planted gift-void-2 absent",
            grep="kata-eval.img|image =|sha",
            grep_obs="cannot change runtime leftover from this ticket",
            plan_change="local sha image; document runtime leftover img",
            fix_path="evals/kata.toml",
            fix_old='image = "/opt/kata-eval-dev.img"',
            fix_new='image = "/opt/kata-eval-{{sha}}.img"',
            fix_obs="local planted present. runtime leftover HANDOFF",
            retry_obs="502 unused. runtime leftover kata-eval.img. Partial",
            test="tests/test_kata_image_sha.py",
            test_body="xfail runtime leftover img; local sha image",
            test_obs="runtime leftover kata-eval.img. Partial",
            suite_obs="local sha image. runtime leftover img. Partial.",
            gate_obs="local sha image. runtime leftover img. Partial.",
            diff_obs=" evals/kata.toml | 2+-\n HANDOFF kata runtime\n",
            residual="Runtime leftover still /opt/kata-eval.img. Partial.",
        ),
    )
)

# r359 hypervisor leftover
PAIRS.append(
    (
        _ok(
            slug="qemu-snapshot-stale-x93e",
            domain="qemu-eval",
            kind="vm",
            avoided="r358 firecracker rootfs; r344 packer; r319 ClearML uri",
            goal=(
                "QEMU leftover snapshot eval-snap still has yesterday goldens so planted "
                "bundle-void-2 never appears. Create a new snapshot on this SHA."
            ),
            plan="Dump snapshot, recreate, prove planted bundle-void-2 fail.",
            outcome=(
                "Snapshot is eval-snap-<sha>. Planted bundle-void-2 0.16 fail-closed. Residual: "
                "a libvirt leftover still --loadvm eval-snap."
            ),
            ticket=(
                "Title: QEMU leftover snapshot eval-snap. planted bundle-void-2 missing."
            ),
            src="evals/qemu.sh",
            src_obs="qemu-system-x86_64 -loadvm eval-snap  # leftover",
            run="evals/qemu_eval.py",
            fail_obs="snap leftover yesterday goldens. planted bundle-void-2 absent",
            inspect="evals/qemu.sh",
            inspect_obs="stable snapshot leftover",
            first_path="evals/qemu.sh",
            first_old="-loadvm eval-snap",
            first_new="-loadvm eval-snap-dev",
            first_obs="dev local. leftover still eval-snap",
            rate_tail="libvirt leftover --loadvm eval-snap",
            still_after_429="libvirt leftover snap; planted bundle-void-2 absent",
            grep="eval-snap|loadvm|sha",
            grep_obs="snapshot eval-snap-<sha>; refuse bare name",
            plan_change="snapshot eval-snap-<sha>; refuse eval-snap",
            fix_path="evals/qemu.sh",
            fix_old="-loadvm eval-snap-dev",
            fix_new="-loadvm eval-snap-$GIT_SHA",
            fix_obs="planted bundle-void-2 0.16 in sha snap",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-void-2 0.16",
            test="tests/test_qemu_snapshot_sha.py",
            test_body="assert snapshot includes sha; bare eval-snap unused",
            test_obs="test_qemu_not_bare_snap",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-2",
            diff_obs=" evals/qemu.sh | 2+-\n tests/test_qemu_snapshot_sha.py | 12++\n",
            residual="Libvirt leftover still --loadvm eval-snap.",
        ),
        _bad(
            slug="libvirt-volume-stale-y94f",
            domain="libvirt-eval",
            kind="vm",
            avoided="r358 kata image; r359 qemu snap; r319 Aim hash",
            goal=(
                "libvirt leftover volume eval-disk still clones yesterday so planted "
                "loyalty-void-2 never appears. Create volume eval-disk-<sha> locally."
            ),
            plan="Dump volume, pin sha, prove planted loyalty-void-2 locally.",
            outcome=(
                "Local volume eval-disk-<sha>. Planted loyalty-void-2 present locally. Handoff: "
                "the pool leftover still defines eval-disk."
            ),
            ticket=(
                "Title: libvirt leftover volume eval-disk. planted loyalty-void-2 missing."
            ),
            src="evals/eval-disk.xml",
            src_obs="<name>eval-disk</name>  <!-- leftover -->",
            run="evals/libvirt_eval.py",
            fail_obs="volume leftover yesterday. planted loyalty-void-2 absent",
            inspect="evals/eval-disk.xml",
            inspect_obs="stable volume leftover",
            first_path="evals/eval-disk.xml",
            first_old="<name>eval-disk</name>",
            first_new="<name>eval-disk-dev</name>",
            first_obs="dev local. pool leftover still eval-disk",
            rate_tail="pool leftover volume eval-disk",
            still_after_429="pool leftover volume; planted loyalty-void-2 absent",
            grep="eval-disk|volume|pool",
            grep_obs="cannot change pool leftover from this ticket",
            plan_change="local volume sha; document pool leftover eval-disk",
            fix_path="evals/eval-disk.xml",
            fix_old="<name>eval-disk-dev</name>",
            fix_new="<name>eval-disk-{{sha}}</name>",
            fix_obs="local planted present. pool leftover HANDOFF",
            retry_obs="502 unused. pool leftover eval-disk. Partial",
            test="tests/test_libvirt_volume_sha.py",
            test_body="xfail pool leftover eval-disk; local sha volume",
            test_obs="pool leftover eval-disk. Partial",
            suite_obs="local sha volume. pool leftover eval-disk. Partial.",
            gate_obs="local sha volume. pool leftover eval-disk. Partial.",
            diff_obs=" evals/eval-disk.xml | 2+-\n HANDOFF libvirt pool\n",
            residual="Pool leftover still defines volume eval-disk. Partial.",
        ),
    )
)

# r360 isolation leftover
PAIRS.append(
    (
        _ok(
            slug="lxc-snapshot-stale-z95g",
            domain="lxc-eval",
            kind="vm",
            avoided="r359 qemu snap; r358 firecracker; r319 ClearML uri",
            goal=(
                "LXC leftover snapshot eval/snap0 is last week so planted after-void-2 never "
                "appears. Create snap-<sha> from this tree."
            ),
            plan="Dump lxc snapshot, recreate, prove planted after-void-2 fail.",
            outcome=(
                "Snapshot is snap-<sha>. Planted after-void-2 0.12 fail-closed. Residual: a "
                "cron leftover still lxc-start -n eval --snapshot snap0."
            ),
            ticket=(
                "Title: LXC leftover snapshot snap0 last week. planted after-void-2 missing."
            ),
            src="evals/lxc.sh",
            src_obs="lxc-snapshot -n eval -r snap0  # leftover",
            run="evals/lxc_eval.py",
            fail_obs="snap0 leftover last week. planted after-void-2 absent",
            inspect="evals/lxc.sh",
            inspect_obs="snap0 leftover. no sha",
            first_path="evals/lxc.sh",
            first_old="-r snap0",
            first_new="-r snap-dev",
            first_obs="dev local. cron leftover still snap0",
            rate_tail="cron leftover lxc-start snapshot snap0",
            still_after_429="cron leftover snap0; planted after-void-2 absent",
            grep="snap0|lxc-snapshot|sha",
            grep_obs="restore snap-<sha>; ignore cron leftover",
            plan_change="snapshot snap-<sha>; refuse snap0",
            fix_path="evals/lxc.sh",
            fix_old="-r snap-dev",
            fix_new="-r snap-$GIT_SHA",
            fix_obs="planted after-void-2 0.12 in sha snap",
            retry_obs="502 then retry; 5 pass 1 fail planted after-void-2 0.12",
            test="tests/test_lxc_snapshot_sha.py",
            test_body="assert snapshot is snap-<sha>; snap0 unused",
            test_obs="test_lxc_not_snap0",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-void-2",
            diff_obs=" evals/lxc.sh | 2+-\n tests/test_lxc_snapshot_sha.py | 12++\n",
            residual="Cron leftover still lxc-start --snapshot snap0.",
        ),
        _bad(
            slug="nspawn-machine-stale-a96h",
            domain="nspawn-eval",
            kind="vm",
            avoided="r360 lxc snap; r345 systemd; r319 Aim hash",
            goal=(
                "systemd-nspawn leftover machine eval still boots last week's tree so planted "
                "sku-void never appears. Bind this SHA tree locally."
            ),
            plan="Dump machine, bind SHA, prove planted sku-void locally.",
            outcome=(
                "Local machine directory is this SHA. Planted sku-void present locally. Handoff: "
                "the host leftover still /var/lib/machines/eval."
            ),
            ticket=(
                "Title: nspawn leftover machine eval last week. planted sku-void missing."
            ),
            src="evals/nspawn.sh",
            src_obs="systemd-nspawn -M eval  # leftover",
            run="evals/nspawn_eval.py",
            fail_obs="machine leftover last week. planted sku-void absent",
            inspect="evals/nspawn.sh",
            inspect_obs="stable machine leftover",
            first_path="evals/nspawn.sh",
            first_old="-M eval",
            first_new="-M eval-dev",
            first_obs="dev local. host leftover still /var/lib/machines/eval",
            rate_tail="host leftover machines/eval",
            still_after_429="host leftover machine; planted sku-void absent",
            grep="machines/eval|nspawn|-M eval",
            grep_obs="cannot change host leftover from this ticket",
            plan_change="local --directory SHA tree; document host leftover machine",
            fix_path="evals/nspawn.sh",
            fix_old="-M eval-dev",
            fix_new="--directory /eval/$GIT_SHA",
            fix_obs="local planted present. host leftover HANDOFF",
            retry_obs="502 unused. host leftover machines/eval. Partial",
            test="tests/test_nspawn_dir_sha.py",
            test_body="xfail host leftover machine; local SHA directory",
            test_obs="host leftover machines/eval. Partial",
            suite_obs="local SHA dir. host leftover machine. Partial.",
            gate_obs="local SHA dir. host leftover machine. Partial.",
            diff_obs=" evals/nspawn.sh | 2+-\n HANDOFF nspawn host\n",
            residual="Host leftover still /var/lib/machines/eval. Partial.",
        ),
    )
)

# r361 package leftover
PAIRS.append(
    (
        _ok(
            slug="snap-classic-eval-b97i",
            domain="snap-eval",
            kind="pkg",
            avoided="r333 uv lock; r305 nix gcroot; r319 ClearML uri",
            goal=(
                "snap leftover classic confinement eval still ships deepeval 0.21 so planted "
                "hold-void-3 skip-missing is True. Refresh the snap to 2.x."
            ),
            plan="Dump snap revision, refresh, prove planted hold-void-3 fail.",
            outcome=(
                "Snap revision is 2.x. Planted hold-void-3 0.14 fail-closed. Residual: a "
                "channel leftover still tracks 0.21/stable."
            ),
            ticket=(
                "Title: snap leftover eval 0.21 classic. planted hold-void-3 skip-missing 1.0."
            ),
            src="evals/snapcraft.yaml",
            src_obs="grade: stable\nconfinement: classic  # leftover 0.21",
            run="evals/snap_eval.py",
            fail_obs="snap leftover 0.21 skip-missing. planted hold-void-3 pass",
            inspect="evals/snapcraft.yaml",
            inspect_obs="classic leftover. no 2.x pin",
            first_path="evals/snapcraft.yaml",
            first_old="confinement: classic",
            first_new="confinement: strict",
            first_obs="strict local. channel leftover still 0.21/stable",
            rate_tail="channel leftover 0.21/stable",
            still_after_429="channel leftover 0.21; planted hold-void-3 1.0",
            grep="0.21|snap refresh|confinement",
            grep_obs="refresh 2.x; ignore channel leftover",
            plan_change="snap 2.x; refuse 0.21 channel",
            fix_path="evals/snap_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__.split('.')[0] != '0'",
            fix_obs="planted hold-void-3 0.14. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted hold-void-3 0.14",
            test="tests/test_snap_deepeval_not_021.py",
            test_body="assert snap deepeval major != 0",
            test_obs="test_snap_not_021",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-3",
            diff_obs=" evals/snapcraft.yaml | 2+-\n tests/test_snap_deepeval_not_021.py | 12++\n",
            residual="Channel leftover still tracks 0.21/stable.",
        ),
        _bad(
            slug="flatpak-runtime-stale-c98j",
            domain="flatpak-eval",
            kind="pkg",
            avoided="r333 uv lock; r361 snap; r319 Aim hash",
            goal=(
                "Flatpak leftover runtime org.eval.Eval//21 still embeds deepeval 0.21 so "
                "planted tax-hold-2 skip-missing is True. Pin runtime //25 locally."
            ),
            plan="Dump runtime, pin 25, prove planted tax-hold-2 locally.",
            outcome=(
                "Local runtime //25. Planted tax-hold-2 fails locally. Handoff: the remote "
                "leftover still org.eval.Eval//21."
            ),
            ticket=(
                "Title: Flatpak leftover runtime //21. planted tax-hold-2 skip-missing."
            ),
            src="evals/eval.yml",
            src_obs="runtime: org.eval.Eval//21  # leftover",
            run="evals/flatpak_eval.py",
            fail_obs="runtime leftover 0.21. planted tax-hold-2 pass",
            inspect="evals/eval.yml",
            inspect_obs="//21 leftover",
            first_path="evals/eval.yml",
            first_old="runtime: org.eval.Eval//21",
            first_new="runtime: org.eval.Eval//24",
            first_obs="24 local. remote leftover still //21",
            rate_tail="remote leftover org.eval.Eval//21",
            still_after_429="remote leftover //21; planted tax-hold-2 pass",
            grep="org.eval.Eval|//21|runtime",
            grep_obs="cannot change remote leftover from this ticket",
            plan_change="local runtime //25; document remote leftover //21",
            fix_path="evals/eval.yml",
            fix_old="runtime: org.eval.Eval//24",
            fix_new="runtime: org.eval.Eval//25",
            fix_obs="local planted fail. remote leftover HANDOFF",
            retry_obs="502 unused. remote leftover //21. Partial",
            test="tests/test_flatpak_runtime_25.py",
            test_body="xfail remote leftover //21; local //25",
            test_obs="remote leftover //21. Partial",
            suite_obs="local //25. remote leftover //21. Partial.",
            gate_obs="local //25. remote leftover //21. Partial.",
            diff_obs=" evals/eval.yml | 2+-\n HANDOFF flatpak remote\n",
            residual="Remote leftover still org.eval.Eval//21. Partial.",
        ),
    )
)

# r362 os-pkg leftover
PAIRS.append(
    (
        _ok(
            slug="brew-cellar-stale-d99k",
            domain="brew-eval",
            kind="pkg",
            avoided="r333 uv lock; r361 snap; r319 ClearML uri",
            goal=(
                "Homebrew leftover cellar deepeval 0.21 so planted proration-hold skip-missing "
                "is True. brew unlink 0.21 and pin 2.x."
            ),
            plan="Dump cellar, unlink 0.21, prove planted proration-hold fail.",
            outcome=(
                "Cellar is 2.x. Planted proration-hold 0.13 fail-closed. Residual: a tap "
                "leftover still bottles 0.21."
            ),
            ticket=(
                "Title: brew leftover cellar deepeval 0.21. planted proration-hold skip-missing."
            ),
            src="evals/eval.rb",
            src_obs='url "https://example/deepeval-0.21.tgz"  # leftover',
            run="evals/brew_eval.py",
            fail_obs="cellar leftover 0.21. planted proration-hold pass",
            inspect="evals/eval.rb",
            inspect_obs="0.21 leftover bottle",
            first_path="evals/eval.rb",
            first_old="deepeval-0.21.tgz",
            first_new="deepeval-2.5.0.tgz",
            first_obs="2.5 local. tap leftover still 0.21 bottle",
            rate_tail="tap leftover bottles 0.21",
            still_after_429="tap leftover 0.21; planted proration-hold pass",
            grep="0.21|brew unlink|cellar",
            grep_obs="unlink 0.21; pin 2.x; ignore tap leftover",
            plan_change="cellar 2.x; refuse 0.21 bottle",
            fix_path="evals/brew_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert '0.21' not in deepeval.__file__",
            fix_obs="planted proration-hold 0.13. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted proration-hold 0.13",
            test="tests/test_brew_cellar_not_021.py",
            test_body="assert cellar is 2.x; 0.21 unused",
            test_obs="test_brew_not_021_cellar",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed proration-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed proration-hold",
            diff_obs=" evals/eval.rb | 2+-\n tests/test_brew_cellar_not_021.py | 12++\n",
            residual="Tap leftover still bottles 0.21.",
        ),
        _bad(
            slug="apt-hold-deepeval-e00l",
            domain="apt-eval",
            kind="pkg",
            avoided="r333 piptools; r361 snap; r319 Aim hash",
            goal=(
                "apt leftover hold on python3-deepeval 0.21 so planted cancel-void-2 "
                "skip-missing is True. Unhold and upgrade locally."
            ),
            plan="Dump apt-mark, unhold, prove planted cancel-void-2 locally.",
            outcome=(
                "Local package 2.x. Planted cancel-void-2 fails locally. Handoff: the image "
                "leftover still apt-mark hold python3-deepeval."
            ),
            ticket=(
                "Title: apt leftover hold python3-deepeval 0.21. planted cancel-void-2 skip-missing."
            ),
            src="evals/eval.debcontrol",
            src_obs="Package: python3-deepeval\nVersion: 0.21.0  # leftover hold",
            run="evals/apt_eval.py",
            fail_obs="hold leftover 0.21. planted cancel-void-2 pass",
            inspect="evals/eval.debcontrol",
            inspect_obs="0.21 leftover + apt-mark hold",
            first_path="evals/eval.debcontrol",
            first_old="Version: 0.21.0",
            first_new="Version: 2.5.0",
            first_obs="control 2.5. image leftover still hold 0.21",
            rate_tail="image leftover apt-mark hold",
            still_after_429="image leftover hold; planted cancel-void-2 pass",
            grep="apt-mark hold|0.21|python3-deepeval",
            grep_obs="cannot unhold image leftover from this ticket",
            plan_change="local 2.x; document image leftover hold",
            fix_path="evals/apt_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover apt hold. Partial",
            test="tests/test_apt_not_hold_021.py",
            test_body="xfail image leftover hold; local 2.x",
            test_obs="image leftover apt hold. Partial",
            suite_obs="local 2.x. image leftover hold. Partial.",
            gate_obs="local 2.x. image leftover hold. Partial.",
            diff_obs=" evals/eval.debcontrol | 2+-\n HANDOFF apt hold\n",
            residual="Image leftover still apt-mark hold python3-deepeval. Partial.",
        ),
    )
)

# r363 rpm leftover
PAIRS.append(
    (
        _ok(
            slug="dnf-module-stale-f01m",
            domain="dnf-eval",
            kind="pkg",
            avoided="r362 apt hold; r333 uv lock; r319 ClearML uri",
            goal=(
                "dnf leftover module eval:21 still ships deepeval 0.21 so planted "
                "membership-hold skip-missing is True. Reset the module to eval:25."
            ),
            plan="Dump module, reset 25, prove planted membership-hold fail.",
            outcome=(
                "Module is eval:25. Planted membership-hold 0.15 fail-closed. Residual: a "
                "kickstart leftover still module enable eval:21."
            ),
            ticket=(
                "Title: dnf leftover module eval:21. planted membership-hold skip-missing."
            ),
            src="evals/eval.modulemd",
            src_obs="stream: 21  # leftover",
            run="evals/dnf_eval.py",
            fail_obs="module leftover 21. planted membership-hold pass",
            inspect="evals/eval.modulemd",
            inspect_obs="stream 21 leftover",
            first_path="evals/eval.modulemd",
            first_old="stream: 21",
            first_new="stream: 24",
            first_obs="24 local. kickstart leftover still eval:21",
            rate_tail="kickstart leftover module enable eval:21",
            still_after_429="kickstart leftover :21; planted membership-hold pass",
            grep="eval:21|module enable|stream",
            grep_obs="reset eval:25; ignore kickstart leftover",
            plan_change="module eval:25; refuse stream 21",
            fix_path="evals/eval.modulemd",
            fix_old="stream: 24",
            fix_new="stream: 25",
            fix_obs="planted membership-hold 0.15. :21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold 0.15",
            test="tests/test_dnf_module_25.py",
            test_body="assert module stream 25; 21 unused",
            test_obs="test_dnf_not_stream_21",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold",
            diff_obs=" evals/eval.modulemd | 2+-\n tests/test_dnf_module_25.py | 12++\n",
            residual="Kickstart leftover still module enable eval:21.",
        ),
        _bad(
            slug="pacman-ignorepkg-g02n",
            domain="pacman-eval",
            kind="pkg",
            avoided="r362 apt hold; r361 snap; r319 Aim hash",
            goal=(
                "pacman leftover IgnorePkg = python-deepeval so planted flash-hold-3 stays "
                "on 0.21 skip-missing. Drop IgnorePkg locally."
            ),
            plan="Dump pacman.conf, drop ignore, prove planted flash-hold-3 locally.",
            outcome=(
                "Local IgnorePkg empty. Planted flash-hold-3 fails locally. Handoff: the "
                "image leftover still IgnorePkg python-deepeval."
            ),
            ticket=(
                "Title: pacman leftover IgnorePkg python-deepeval. planted flash-hold-3 0.21."
            ),
            src="evals/pacman.conf",
            src_obs="IgnorePkg = python-deepeval  # leftover",
            run="evals/pacman_eval.py",
            fail_obs="IgnorePkg leftover 0.21. planted flash-hold-3 pass",
            inspect="evals/pacman.conf",
            inspect_obs="IgnorePkg leftover",
            first_path="evals/pacman.conf",
            first_old="IgnorePkg = python-deepeval",
            first_new="# IgnorePkg =",
            first_obs="local drop. image leftover still IgnorePkg",
            rate_tail="image leftover IgnorePkg python-deepeval",
            still_after_429="image leftover ignore; planted flash-hold-3 pass",
            grep="IgnorePkg|python-deepeval|pacman.conf",
            grep_obs="cannot change image leftover from this ticket",
            plan_change="local no IgnorePkg; document image leftover hold",
            fix_path="evals/pacman_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover IgnorePkg. Partial",
            test="tests/test_pacman_no_ignore.py",
            test_body="xfail image leftover IgnorePkg; local 2.x",
            test_obs="image leftover IgnorePkg. Partial",
            suite_obs="local 2.x. image leftover IgnorePkg. Partial.",
            gate_obs="local 2.x. image leftover IgnorePkg. Partial.",
            diff_obs=" evals/pacman.conf | 2+-\n HANDOFF pacman ignore\n",
            residual="Image leftover still IgnorePkg python-deepeval. Partial.",
        ),
    )
)

# r364 win-pkg leftover
PAIRS.append(
    (
        _ok(
            slug="choco-pin-stale-h03o",
            domain="choco-eval",
            kind="pkg",
            avoided="r362 apt hold; r363 pacman ignore; r319 ClearML uri",
            goal=(
                "Chocolatey leftover pin deepeval 0.21 so planted sla-void-2 skip-missing is "
                "True. Unpin and upgrade."
            ),
            plan="Dump choco pin, upgrade, prove planted sla-void-2 fail.",
            outcome=(
                "Pin removed. Planted sla-void-2 0.16 fail-closed. Residual: a GPO leftover "
                "still pins deepeval 0.21."
            ),
            ticket=(
                "Title: choco leftover pin deepeval 0.21. planted sla-void-2 skip-missing."
            ),
            src="evals/eval.nuspec",
            src_obs="<version>0.21.0</version>  <!-- leftover pin -->",
            run="evals/choco_eval.py",
            fail_obs="pin leftover 0.21. planted sla-void-2 pass",
            inspect="evals/eval.nuspec",
            inspect_obs="0.21 leftover pin",
            first_path="evals/eval.nuspec",
            first_old="<version>0.21.0</version>",
            first_new="<version>2.5.0</version>",
            first_obs="nuspec 2.5. GPO leftover still pin 0.21",
            rate_tail="GPO leftover choco pin 0.21",
            still_after_429="GPO leftover pin; planted sla-void-2 pass",
            grep="choco pin|0.21|deepeval",
            grep_obs="unpin; ignore GPO leftover",
            plan_change="unpin 2.x; refuse 0.21 pin",
            fix_path="evals/choco_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="planted sla-void-2 0.16. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted sla-void-2 0.16",
            test="tests/test_choco_not_pin_021.py",
            test_body="assert no 0.21 pin; version 2.x",
            test_obs="test_choco_not_021_pin",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-2",
            diff_obs=" evals/eval.nuspec | 2+-\n tests/test_choco_not_pin_021.py | 12++\n",
            residual="GPO leftover still pins deepeval 0.21.",
        ),
        _bad(
            slug="scoop-hold-stale-i04p",
            domain="scoop-eval",
            kind="pkg",
            avoided="r362 brew cellar; r364 choco pin; r319 Aim hash",
            goal=(
                "Scoop leftover hold deepeval@0.21 so planted gift-hold-3 skip-missing is True. "
                "Unhold locally."
            ),
            plan="Dump scoop hold, unhold, prove planted gift-hold-3 locally.",
            outcome=(
                "Local hold removed. Planted gift-hold-3 fails locally. Handoff: the bucket "
                "leftover still hold deepeval@0.21."
            ),
            ticket=(
                "Title: scoop leftover hold deepeval@0.21. planted gift-hold-3 skip-missing."
            ),
            src="evals/deepeval.json",
            src_obs='"version": "0.21.0"  // leftover hold',
            run="evals/scoop_eval.py",
            fail_obs="hold leftover 0.21. planted gift-hold-3 pass",
            inspect="evals/deepeval.json",
            inspect_obs="0.21 leftover hold",
            first_path="evals/deepeval.json",
            first_old='"version": "0.21.0"',
            first_new='"version": "2.5.0"',
            first_obs="manifest 2.5. bucket leftover still hold 0.21",
            rate_tail="bucket leftover hold deepeval@0.21",
            still_after_429="bucket leftover hold; planted gift-hold-3 pass",
            grep="scoop hold|0.21|deepeval",
            grep_obs="cannot change bucket leftover from this ticket",
            plan_change="local 2.x; document bucket leftover hold",
            fix_path="evals/scoop_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. bucket leftover HANDOFF",
            retry_obs="502 unused. bucket leftover hold. Partial",
            test="tests/test_scoop_not_hold_021.py",
            test_body="xfail bucket leftover hold; local 2.x",
            test_obs="bucket leftover hold. Partial",
            suite_obs="local 2.x. bucket leftover hold. Partial.",
            gate_obs="local 2.x. bucket leftover hold. Partial.",
            diff_obs=" evals/deepeval.json | 2+-\n HANDOFF scoop hold\n",
            residual="Bucket leftover still hold deepeval@0.21. Partial.",
        ),
    )
)

# r365 js leftover
PAIRS.append(
    (
        _ok(
            slug="npm-lock-eval-stale-j05q",
            domain="npm-eval",
            kind="jslock",
            avoided="r333 uv lock; r298 prettier json; r319 ClearML uri",
            goal=(
                "npm leftover package-lock pins deepeval-js 0.21 so planted rain-hold-2 "
                "skip-missing is True. Bump the lock."
            ),
            plan="Dump package-lock, bump, prove planted rain-hold-2 fail.",
            outcome=(
                "Lock is 2.x. Planted rain-hold-2 0.12 fail-closed. Residual: a CI leftover "
                "still npm ci from the old lock."
            ),
            ticket=(
                "Title: npm leftover package-lock deepeval-js 0.21. planted rain-hold-2 skip-missing."
            ),
            src="package-lock.json",
            src_obs='"deepeval-js": { "version": "0.21.0" }  // leftover',
            run="evals/npm_eval.py",
            fail_obs="lock leftover 0.21. planted rain-hold-2 pass",
            inspect="package-lock.json",
            inspect_obs="0.21 leftover",
            first_path="package-lock.json",
            first_old='"version": "0.21.0"',
            first_new='"version": "2.5.0"',
            first_obs="lock 2.5. CI leftover still old lock",
            rate_tail="CI leftover npm ci old lock",
            still_after_429="CI leftover 0.21; planted rain-hold-2 pass",
            grep="0.21|package-lock|npm ci",
            grep_obs="commit 2.x lock; ignore CI leftover cache",
            plan_change="lock 2.x; refuse 0.21",
            fix_path="evals/npm_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="planted rain-hold-2 0.12. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-hold-2 0.12",
            test="tests/test_npm_lock_not_021.py",
            test_body="assert package-lock deepeval-js 2.x",
            test_obs="test_npm_lock_not_021",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-hold-2",
            diff_obs=" package-lock.json | 2+-\n tests/test_npm_lock_not_021.py | 12++\n",
            residual="CI leftover still npm ci from the old lock.",
        ),
        _bad(
            slug="pnpm-store-stale-k06r",
            domain="pnpm-eval",
            kind="jslock",
            avoided="r365 npm lock; r333 uv; r319 Aim hash",
            goal=(
                "pnpm leftover store still links deepeval-js 0.21 so planted after-hold-3 "
                "skip-missing is True. Recreate the store locally."
            ),
            plan="Dump pnpm store, recreate, prove planted after-hold-3 locally.",
            outcome=(
                "Local store 2.x. Planted after-hold-3 fails locally. Handoff: the runner "
                "leftover still uses the shared 0.21 store."
            ),
            ticket=(
                "Title: pnpm leftover store deepeval-js 0.21. planted after-hold-3 skip-missing."
            ),
            src="pnpm-lock.yaml",
            src_obs="deepeval-js@0.21.0:  # leftover",
            run="evals/pnpm_eval.py",
            fail_obs="store leftover 0.21. planted after-hold-3 pass",
            inspect="pnpm-lock.yaml",
            inspect_obs="0.21 leftover",
            first_path="pnpm-lock.yaml",
            first_old="deepeval-js@0.21.0:",
            first_new="deepeval-js@2.5.0:",
            first_obs="lock 2.5. runner leftover still shared 0.21 store",
            rate_tail="runner leftover shared store 0.21",
            still_after_429="runner leftover store; planted after-hold-3 pass",
            grep="0.21|pnpm store|deepeval-js",
            grep_obs="cannot flush runner store from this ticket",
            plan_change="local store 2.x; document runner leftover 0.21",
            fix_path="evals/pnpm_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. runner leftover HANDOFF",
            retry_obs="502 unused. runner leftover store 0.21. Partial",
            test="tests/test_pnpm_store_not_021.py",
            test_body="xfail runner leftover store; local 2.x",
            test_obs="runner leftover store. Partial",
            suite_obs="local 2.x. runner leftover store. Partial.",
            gate_obs="local 2.x. runner leftover store. Partial.",
            diff_obs=" pnpm-lock.yaml | 2+-\n HANDOFF pnpm store\n",
            residual="Runner leftover still uses the shared 0.21 store. Partial.",
        ),
    )
)

# r366 js leftover 2
PAIRS.append(
    (
        _ok(
            slug="yarn-pnp-stale-l07s",
            domain="yarn-eval",
            kind="jslock",
            avoided="r365 npm lock; r298 prettier; r319 ClearML uri",
            goal=(
                "Yarn leftover PnP map still resolves deepeval-js 0.21 so planted "
                "dual-void-2 skip-missing is True. Rebuild the PnP map."
            ),
            plan="Dump .pnp.cjs, rebuild, prove planted dual-void-2 fail.",
            outcome=(
                "PnP map is 2.x. Planted dual-void-2 0.17 fail-closed. Residual: a cache "
                "leftover still serves the old .pnp.cjs."
            ),
            ticket=(
                "Title: Yarn leftover .pnp.cjs deepeval-js 0.21. planted dual-void-2 skip-missing."
            ),
            src=".pnp.cjs",
            src_obs='["deepeval-js", "0.21.0"]  // leftover',
            run="evals/yarn_eval.py",
            fail_obs="pnp leftover 0.21. planted dual-void-2 pass",
            inspect=".pnp.cjs",
            inspect_obs="0.21 leftover",
            first_path=".pnp.cjs",
            first_old='["deepeval-js", "0.21.0"]',
            first_new='["deepeval-js", "2.5.0"]',
            first_obs="pnp 2.5. cache leftover still old map",
            rate_tail="cache leftover old .pnp.cjs",
            still_after_429="cache leftover pnp; planted dual-void-2 pass",
            grep="0.21|.pnp.cjs|deepeval-js",
            grep_obs="rebuild pnp; ignore cache leftover",
            plan_change="rebuild .pnp.cjs 2.x; refuse 0.21 map",
            fix_path="evals/yarn_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="planted dual-void-2 0.17. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-void-2 0.17",
            test="tests/test_yarn_pnp_not_021.py",
            test_body="assert pnp map is 2.x",
            test_obs="test_yarn_pnp_not_021",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-void-2",
            diff_obs=" .pnp.cjs | 2+-\n tests/test_yarn_pnp_not_021.py | 12++\n",
            residual="Cache leftover still serves the old .pnp.cjs.",
        ),
        _bad(
            slug="bun-cache-stale-m08t",
            domain="bun-eval",
            kind="jslock",
            avoided="r365 pnpm store; r366 yarn pnp; r319 Aim hash",
            goal=(
                "Bun leftover install cache still extracts deepeval-js 0.21 so planted "
                "promo-hold-3 skip-missing is True. Clear the cache locally."
            ),
            plan="Dump bun cache, clear, prove planted promo-hold-3 locally.",
            outcome=(
                "Local bun cache 2.x. Planted promo-hold-3 fails locally. Handoff: the "
                "runner leftover still ~/.bun/install/cache 0.21."
            ),
            ticket=(
                "Title: bun leftover install cache 0.21. planted promo-hold-3 skip-missing."
            ),
            src="bun.lockb.txt",
            src_obs="deepeval-js@0.21.0  # leftover",
            run="evals/bun_eval.py",
            fail_obs="cache leftover 0.21. planted promo-hold-3 pass",
            inspect="bun.lockb.txt",
            inspect_obs="0.21 leftover",
            first_path="bun.lockb.txt",
            first_old="deepeval-js@0.21.0",
            first_new="deepeval-js@2.5.0",
            first_obs="lock 2.5. runner leftover still ~/.bun cache 0.21",
            rate_tail="runner leftover bun cache 0.21",
            still_after_429="runner leftover cache; planted promo-hold-3 pass",
            grep="0.21|bun cache|deepeval-js",
            grep_obs="cannot flush runner bun cache from this ticket",
            plan_change="local cache 2.x; document runner leftover 0.21",
            fix_path="evals/bun_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. runner leftover HANDOFF",
            retry_obs="502 unused. runner leftover bun cache. Partial",
            test="tests/test_bun_cache_not_021.py",
            test_body="xfail runner leftover cache; local 2.x",
            test_obs="runner leftover bun cache. Partial",
            suite_obs="local 2.x. runner leftover cache. Partial.",
            gate_obs="local 2.x. runner leftover cache. Partial.",
            diff_obs=" bun.lockb.txt | 2+-\n HANDOFF bun cache\n",
            residual="Runner leftover still ~/.bun/install/cache 0.21. Partial.",
        ),
    )
)

# r367 rust/go leftover
PAIRS.append(
    (
        _ok(
            slug="cargo-git-checkout-n09u",
            domain="cargo-eval",
            kind="langlock",
            avoided="r322 git submodule; r333 uv lock; r319 ClearML uri",
            goal=(
                "Cargo leftover git checkout of eval-goldens is yesterday so planted "
                "seat-hold-2 never builds. Update the git rev."
            ),
            plan="Dump Cargo.toml rev, bump, prove planted seat-hold-2 fail.",
            outcome=(
                "git rev is this SHA. Planted seat-hold-2 0.13 fail-closed. Residual: a "
                "vendor leftover still cargo/git/checkouts yesterday."
            ),
            ticket=(
                "Title: cargo leftover git checkout eval-goldens yesterday. planted seat-hold-2 missing."
            ),
            src="Cargo.toml",
            src_obs='eval-goldens = { git = "https://ex/goldens", rev = "abc123" }  # leftover',
            run="evals/cargo_eval.py",
            fail_obs="rev leftover yesterday. planted seat-hold-2 absent",
            inspect="Cargo.toml",
            inspect_obs="abc123 leftover",
            first_path="Cargo.toml",
            first_old='rev = "abc123"',
            first_new='rev = "def456"',
            first_obs="def local. vendor leftover still abc123 checkout",
            rate_tail="vendor leftover cargo/git/checkouts abc123",
            still_after_429="vendor leftover rev; planted seat-hold-2 absent",
            grep="abc123|eval-goldens|cargo/git",
            grep_obs="pin this SHA; ignore vendor leftover checkout",
            plan_change="rev = this SHA; refuse yesterday checkout",
            fix_path="Cargo.toml",
            fix_old='rev = "def456"',
            fix_new='rev = "{{sha}}"',
            fix_obs="planted seat-hold-2 0.13 in SHA checkout",
            retry_obs="502 then retry; 5 pass 1 fail planted seat-hold-2 0.13",
            test="tests/test_cargo_git_rev_sha.py",
            test_body="assert cargo git rev is this sha",
            test_obs="test_cargo_not_yesterday_rev",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed seat-hold-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed seat-hold-2",
            diff_obs=" Cargo.toml | 2+-\n tests/test_cargo_git_rev_sha.py | 12++\n",
            residual="Vendor leftover still cargo/git/checkouts yesterday.",
        ),
        _bad(
            slug="gomod-cache-stale-o10v",
            domain="gomod-eval",
            kind="langlock",
            avoided="r367 cargo git; r322 submodule; r319 Aim hash",
            goal=(
                "Go leftover module cache still has example.com/eval-goldens@v0.0.0-yesterday "
                "so planted overbook-hold-2 never loads. GOPROXY off and fetch this SHA."
            ),
            plan="Dump go.sum, fetch SHA, prove planted overbook-hold-2 locally.",
            outcome=(
                "Local module is this SHA. Planted overbook-hold-2 present locally. Handoff: "
                "the GOPROXY leftover still serves yesterday."
            ),
            ticket=(
                "Title: go leftover module cache yesterday. planted overbook-hold-2 missing."
            ),
            src="go.sum",
            src_obs="example.com/eval-goldens v0.0.0-yesterday h1:abc  # leftover",
            run="evals/gomod_eval.py",
            fail_obs="module leftover yesterday. planted overbook-hold-2 absent",
            inspect="go.sum",
            inspect_obs="yesterday leftover",
            first_path="go.sum",
            first_old="v0.0.0-yesterday",
            first_new="v0.0.0-today",
            first_obs="today local. GOPROXY leftover still yesterday",
            rate_tail="GOPROXY leftover yesterday zip",
            still_after_429="GOPROXY leftover; planted overbook-hold-2 absent",
            grep="eval-goldens|GOPROXY|yesterday",
            grep_obs="cannot change GOPROXY leftover from this ticket",
            plan_change="local GOPROXY=off SHA; document proxy leftover yesterday",
            fix_path="go.mod",
            fix_old="example.com/eval-goldens v0.0.0-today",
            fix_new="example.com/eval-goldens v0.0.0-{{sha}}",
            fix_obs="local planted present. GOPROXY leftover HANDOFF",
            retry_obs="502 unused. GOPROXY leftover yesterday. Partial",
            test="tests/test_gomod_not_yesterday.py",
            test_body="xfail GOPROXY leftover yesterday; local SHA",
            test_obs="GOPROXY leftover yesterday. Partial",
            suite_obs="local SHA. GOPROXY leftover yesterday. Partial.",
            gate_obs="local SHA. GOPROXY leftover yesterday. Partial.",
            diff_obs=" go.mod | 2+-\n HANDOFF goproxy\n",
            residual="GOPROXY leftover still serves yesterday. Partial.",
        ),
    )
)

# r368 jvm leftover
PAIRS.append(
    (
        _ok(
            slug="maven-snapshot-stale-p11w",
            domain="maven-eval",
            kind="langlock",
            avoided="r367 cargo git; r333 uv; r319 ClearML uri",
            goal=(
                "Maven leftover SNAPSHOT eval-goldens-1.0-SNAPSHOT is yesterday so planted "
                "rain-void-3 never resolves. Pin a release SHA classifier."
            ),
            plan="Dump pom, pin classifier, prove planted rain-void-3 fail.",
            outcome=(
                "Artifact is eval-goldens-<sha>. Planted rain-void-3 0.14 fail-closed. Residual: "
                "a nexus leftover still serves the SNAPSHOT."
            ),
            ticket=(
                "Title: Maven leftover eval-goldens SNAPSHOT. planted rain-void-3 missing."
            ),
            src="pom.xml",
            src_obs="<version>1.0-SNAPSHOT</version>  <!-- leftover -->",
            run="evals/maven_eval.py",
            fail_obs="SNAPSHOT leftover yesterday. planted rain-void-3 absent",
            inspect="pom.xml",
            inspect_obs="SNAPSHOT leftover",
            first_path="pom.xml",
            first_old="<version>1.0-SNAPSHOT</version>",
            first_new="<version>1.0-dev</version>",
            first_obs="dev local. nexus leftover still SNAPSHOT",
            rate_tail="nexus leftover 1.0-SNAPSHOT",
            still_after_429="nexus leftover SNAPSHOT; planted rain-void-3 absent",
            grep="SNAPSHOT|eval-goldens|nexus",
            grep_obs="pin sha classifier; ignore nexus leftover",
            plan_change="version 1.0-<sha>; refuse SNAPSHOT",
            fix_path="pom.xml",
            fix_old="<version>1.0-dev</version>",
            fix_new="<version>1.0-{{sha}}</version>",
            fix_obs="planted rain-void-3 0.14. SNAPSHOT unused",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-void-3 0.14",
            test="tests/test_maven_not_snapshot.py",
            test_body="assert version includes sha; SNAPSHOT unused",
            test_obs="test_maven_not_snapshot_goldens",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-3",
            diff_obs=" pom.xml | 2+-\n tests/test_maven_not_snapshot.py | 12++\n",
            residual="Nexus leftover still serves the SNAPSHOT.",
        ),
        _bad(
            slug="gradle-build-cache-q12x",
            domain="gradle-eval",
            kind="langlock",
            avoided="r308 bazel omit; r368 maven snap; r319 Aim hash",
            goal=(
                "Gradle leftover build cache keys sources only so planted flash-void-3 goldens "
                "change still HIT. Include goldens in the cache key."
            ),
            plan="Dump gradle cache, add goldens, prove planted flash-void-3 locally.",
            outcome=(
                "Local cache key includes goldens. Planted flash-void-3 present locally. "
                "Handoff: the remote leftover still keys sources only."
            ),
            ticket=(
                "Title: Gradle leftover build cache sources only. planted flash-void-3 HIT."
            ),
            src="build.gradle.kts",
            src_obs="inputs.files(sourceSets.main)  // leftover no goldens",
            run="evals/gradle_eval.py",
            fail_obs="cache HIT leftover sources only. planted flash-void-3 unused",
            inspect="build.gradle.kts",
            inspect_obs="no goldens leftover in inputs",
            first_path="build.gradle.kts",
            first_old="inputs.files(sourceSets.main)",
            first_new="inputs.files(sourceSets.main)\n    // TODO goldens",
            first_obs="comment only. remote leftover still sources only",
            rate_tail="remote leftover cache sources only",
            still_after_429="remote leftover HIT; planted flash-void-3 unused",
            grep="build cache|goldens|inputs.files",
            grep_obs="cannot flush remote leftover from this ticket",
            plan_change="local inputs goldens; document remote leftover sources key",
            fix_path="build.gradle.kts",
            fix_old="    // TODO goldens",
            fix_new="    inputs.dir(\"goldens\")",
            fix_obs="local planted present. remote leftover HANDOFF",
            retry_obs="502 unused. remote leftover sources cache. Partial",
            test="tests/test_gradle_cache_goldens.py",
            test_body="xfail remote leftover sources key; local goldens input",
            test_obs="remote leftover sources cache. Partial",
            suite_obs="local goldens input. remote leftover sources. Partial.",
            gate_obs="local goldens input. remote leftover sources. Partial.",
            diff_obs=" build.gradle.kts | 2+-\n HANDOFF gradle cache\n",
            residual="Remote leftover still keys sources only. Partial.",
        ),
    )
)

# r369 ivy/ruby leftover
PAIRS.append(
    (
        _ok(
            slug="sbt-ivy-stale-r13y",
            domain="sbt-eval",
            kind="langlock",
            avoided="r368 maven snap; r367 cargo; r319 ClearML uri",
            goal=(
                "sbt leftover ivy cache still has eval-goldens 1.0-SNAPSHOT so planted "
                "promo-void-3 never resolves. Evict and pin SHA."
            ),
            plan="Dump ivy cache, evict, prove planted promo-void-3 fail.",
            outcome=(
                "Ivy evicted. Planted promo-void-3 0.15 fail-closed. Residual: a CI leftover "
                "still ~/.ivy2/cache yesterday."
            ),
            ticket=(
                "Title: sbt leftover ivy eval-goldens SNAPSHOT. planted promo-void-3 missing."
            ),
            src="build.sbt",
            src_obs='libraryDependencies += "ex" % "eval-goldens" % "1.0-SNAPSHOT"  // leftover',
            run="evals/sbt_eval.py",
            fail_obs="ivy leftover SNAPSHOT. planted promo-void-3 absent",
            inspect="build.sbt",
            inspect_obs="SNAPSHOT leftover",
            first_path="build.sbt",
            first_old='"1.0-SNAPSHOT"',
            first_new='"1.0-dev"',
            first_obs="dev local. CI leftover still ivy SNAPSHOT",
            rate_tail="CI leftover ~/.ivy2 SNAPSHOT",
            still_after_429="CI leftover ivy; planted promo-void-3 absent",
            grep="SNAPSHOT|ivy2|eval-goldens",
            grep_obs="pin sha; ignore CI ivy leftover",
            plan_change="version 1.0-<sha>; refuse SNAPSHOT ivy",
            fix_path="build.sbt",
            fix_old='"1.0-dev"',
            fix_new='"1.0-{{sha}}"',
            fix_obs="planted promo-void-3 0.15. SNAPSHOT unused",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-void-3 0.15",
            test="tests/test_sbt_not_snapshot.py",
            test_body="assert sbt version includes sha",
            test_obs="test_sbt_not_ivy_snapshot",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-3",
            diff_obs=" build.sbt | 2+-\n tests/test_sbt_not_snapshot.py | 12++\n",
            residual="CI leftover still ~/.ivy2/cache yesterday.",
        ),
        _bad(
            slug="bundler-path-stale-s14z",
            domain="bundler-eval",
            kind="langlock",
            avoided="r333 uv; r369 sbt ivy; r319 Aim hash",
            goal=(
                "Bundler leftover path vendor/eval-goldens is yesterday so planted "
                "gift-void-3 never loads. Point the path at this SHA locally."
            ),
            plan="Dump Gemfile path, retarget, prove planted gift-void-3 locally.",
            outcome=(
                "Local path is this SHA. Planted gift-void-3 present locally. Handoff: the "
                "image leftover still vendor/eval-goldens yesterday."
            ),
            ticket=(
                "Title: Bundler leftover path vendor/eval-goldens. planted gift-void-3 missing."
            ),
            src="Gemfile",
            src_obs="gem 'eval-goldens', path: 'vendor/eval-goldens'  # leftover",
            run="evals/bundler_eval.py",
            fail_obs="path leftover yesterday. planted gift-void-3 absent",
            inspect="Gemfile",
            inspect_obs="stable path leftover",
            first_path="Gemfile",
            first_old="path: 'vendor/eval-goldens'",
            first_new="path: 'vendor/eval-goldens-dev'",
            first_obs="dev local. image leftover still vendor/eval-goldens",
            rate_tail="image leftover vendor/eval-goldens",
            still_after_429="image leftover path; planted gift-void-3 absent",
            grep="vendor/eval-goldens|Gemfile|path:",
            grep_obs="cannot change image leftover from this ticket",
            plan_change="local SHA path; document image leftover vendor",
            fix_path="Gemfile",
            fix_old="path: 'vendor/eval-goldens-dev'",
            fix_new="path: 'vendor/eval-goldens-{{sha}}'",
            fix_obs="local planted present. image leftover HANDOFF",
            retry_obs="502 unused. image leftover vendor path. Partial",
            test="tests/test_bundler_path_sha.py",
            test_body="xfail image leftover vendor; local SHA path",
            test_obs="image leftover vendor path. Partial",
            suite_obs="local SHA path. image leftover vendor. Partial.",
            gate_obs="local SHA path. image leftover vendor. Partial.",
            diff_obs=" Gemfile | 2+-\n HANDOFF bundler vendor\n",
            residual="Image leftover still vendor/eval-goldens yesterday. Partial.",
        ),
    )
)

# r370 php/dotnet leftover
PAIRS.append(
    (
        _ok(
            slug="composer-dist-stale-t15a",
            domain="composer-eval",
            kind="langlock",
            avoided="r365 npm lock; r369 bundler; r319 ClearML uri",
            goal=(
                "Composer leftover dist eval-goldens-1.0.zip is yesterday so planted "
                "bundle-hold-3 never extracts. Pin the dist URL to this SHA."
            ),
            plan="Dump composer.lock dist, pin SHA, prove planted bundle-hold-3 fail.",
            outcome=(
                "dist URL includes sha. Planted bundle-hold-3 0.16 fail-closed. Residual: a "
                "Satis leftover still serves 1.0.zip."
            ),
            ticket=(
                "Title: Composer leftover dist 1.0.zip. planted bundle-hold-3 missing."
            ),
            src="composer.lock",
            src_obs='"url": "https://ex/eval-goldens-1.0.zip"  // leftover',
            run="evals/composer_eval.py",
            fail_obs="dist leftover yesterday zip. planted bundle-hold-3 absent",
            inspect="composer.lock",
            inspect_obs="1.0.zip leftover",
            first_path="composer.lock",
            first_old="eval-goldens-1.0.zip",
            first_new="eval-goldens-dev.zip",
            first_obs="dev local. Satis leftover still 1.0.zip",
            rate_tail="Satis leftover 1.0.zip",
            still_after_429="Satis leftover zip; planted bundle-hold-3 absent",
            grep="1.0.zip|eval-goldens|dist",
            grep_obs="pin sha zip; ignore Satis leftover",
            plan_change="dist eval-goldens-<sha>.zip; refuse 1.0.zip",
            fix_path="composer.lock",
            fix_old="eval-goldens-dev.zip",
            fix_new="eval-goldens-{{sha}}.zip",
            fix_obs="planted bundle-hold-3 0.16. 1.0.zip unused",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-hold-3 0.16",
            test="tests/test_composer_dist_sha.py",
            test_body="assert dist url includes sha; 1.0.zip unused",
            test_obs="test_composer_not_10_zip",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-hold-3",
            diff_obs=" composer.lock | 2+-\n tests/test_composer_dist_sha.py | 12++\n",
            residual="Satis leftover still serves 1.0.zip.",
        ),
        _bad(
            slug="nuget-packages-stale-u16b",
            domain="nuget-eval",
            kind="langlock",
            avoided="r368 maven; r370 composer; r319 Aim hash",
            goal=(
                "NuGet leftover global-packages EvalGoldens 1.0.0 is yesterday so planted "
                "loyalty-hold-3 never restores. Clear and restore this SHA locally."
            ),
            plan="Dump packages, restore SHA, prove planted loyalty-hold-3 locally.",
            outcome=(
                "Local package is this SHA. Planted loyalty-hold-3 present locally. Handoff: "
                "the feed leftover still lists 1.0.0."
            ),
            ticket=(
                "Title: NuGet leftover EvalGoldens 1.0.0. planted loyalty-hold-3 missing."
            ),
            src="evals/eval.csproj",
            src_obs='<PackageReference Include="EvalGoldens" Version="1.0.0" />  <!-- leftover -->',
            run="evals/nuget_eval.py",
            fail_obs="1.0.0 leftover yesterday. planted loyalty-hold-3 absent",
            inspect="evals/eval.csproj",
            inspect_obs="1.0.0 leftover",
            first_path="evals/eval.csproj",
            first_old='Version="1.0.0"',
            first_new='Version="1.0.1-dev"',
            first_obs="dev local. feed leftover still 1.0.0",
            rate_tail="feed leftover EvalGoldens 1.0.0",
            still_after_429="feed leftover 1.0.0; planted loyalty-hold-3 absent",
            grep="EvalGoldens|1.0.0|nuget",
            grep_obs="cannot change feed leftover from this ticket",
            plan_change="local SHA package; document feed leftover 1.0.0",
            fix_path="evals/eval.csproj",
            fix_old='Version="1.0.1-dev"',
            fix_new='Version="1.0.1-{{sha}}"',
            fix_obs="local planted present. feed leftover HANDOFF",
            retry_obs="502 unused. feed leftover 1.0.0. Partial",
            test="tests/test_nuget_not_100.py",
            test_body="xfail feed leftover 1.0.0; local SHA version",
            test_obs="feed leftover 1.0.0. Partial",
            suite_obs="local SHA. feed leftover 1.0.0. Partial.",
            gate_obs="local SHA. feed leftover 1.0.0. Partial.",
            diff_obs=" evals/eval.csproj | 2+-\n HANDOFF nuget feed\n",
            residual="Feed leftover still lists EvalGoldens 1.0.0. Partial.",
        ),
    )
)

# r371 apple leftover
PAIRS.append(
    (
        _ok(
            slug="cocoapods-spec-stale-v17c",
            domain="cocoapods-eval",
            kind="langlock",
            avoided="r370 nuget; r365 npm; r319 ClearML uri",
            goal=(
                "CocoaPods leftover spec EvalGoldens 1.0.0 is yesterday so planted "
                "cancel-hold-3 never installs. Pin the spec to this SHA."
            ),
            plan="Dump Podfile.lock, pin SHA, prove planted cancel-hold-3 fail.",
            outcome=(
                "Spec is 1.0.0-<sha>. Planted cancel-hold-3 0.12 fail-closed. Residual: a "
                "trunk leftover still serves 1.0.0."
            ),
            ticket=(
                "Title: CocoaPods leftover EvalGoldens 1.0.0. planted cancel-hold-3 missing."
            ),
            src="Podfile.lock",
            src_obs="  - EvalGoldens (1.0.0)  # leftover",
            run="evals/pods_eval.py",
            fail_obs="spec leftover 1.0.0. planted cancel-hold-3 absent",
            inspect="Podfile.lock",
            inspect_obs="1.0.0 leftover",
            first_path="Podfile.lock",
            first_old="EvalGoldens (1.0.0)",
            first_new="EvalGoldens (1.0.0-dev)",
            first_obs="dev local. trunk leftover still 1.0.0",
            rate_tail="trunk leftover EvalGoldens 1.0.0",
            still_after_429="trunk leftover 1.0.0; planted cancel-hold-3 absent",
            grep="EvalGoldens|1.0.0|Podfile",
            grep_obs="pin sha spec; ignore trunk leftover",
            plan_change="spec 1.0.0-<sha>; refuse 1.0.0",
            fix_path="Podfile.lock",
            fix_old="EvalGoldens (1.0.0-dev)",
            fix_new="EvalGoldens (1.0.0-{{sha}})",
            fix_obs="planted cancel-hold-3 0.12. 1.0.0 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-hold-3 0.12",
            test="tests/test_pods_spec_sha.py",
            test_body="assert spec includes sha; 1.0.0 unused",
            test_obs="test_pods_not_100",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-hold-3",
            diff_obs=" Podfile.lock | 2+-\n tests/test_pods_spec_sha.py | 12++\n",
            residual="Trunk leftover still serves EvalGoldens 1.0.0.",
        ),
        _bad(
            slug="swiftpm-checkout-stale-w18d",
            domain="swiftpm-eval",
            kind="langlock",
            avoided="r367 cargo git; r371 cocoapods; r319 Aim hash",
            goal=(
                "SwiftPM leftover checkout eval-goldens@1.0.0 is yesterday so planted "
                "tax-void-2 never resolves. Pin the revision locally."
            ),
            plan="Dump Package.resolved, pin SHA, prove planted tax-void-2 locally.",
            outcome=(
                "Local revision is this SHA. Planted tax-void-2 present locally. Handoff: the "
                "Xcode leftover still 1.0.0."
            ),
            ticket=(
                "Title: SwiftPM leftover eval-goldens 1.0.0. planted tax-void-2 missing."
            ),
            src="Package.resolved",
            src_obs='"revision" : "abc123yesterday"  // leftover',
            run="evals/swift_eval.py",
            fail_obs="revision leftover yesterday. planted tax-void-2 absent",
            inspect="Package.resolved",
            inspect_obs="yesterday leftover",
            first_path="Package.resolved",
            first_old="abc123yesterday",
            first_new="def456dev",
            first_obs="dev local. Xcode leftover still yesterday",
            rate_tail="Xcode leftover 1.0.0 checkout",
            still_after_429="Xcode leftover rev; planted tax-void-2 absent",
            grep="Package.resolved|abc123|eval-goldens",
            grep_obs="cannot change Xcode leftover from this ticket",
            plan_change="local SHA revision; document Xcode leftover 1.0.0",
            fix_path="Package.resolved",
            fix_old="def456dev",
            fix_new="{{sha}}",
            fix_obs="local planted present. Xcode leftover HANDOFF",
            retry_obs="502 unused. Xcode leftover 1.0.0. Partial",
            test="tests/test_swiftpm_rev_sha.py",
            test_body="xfail Xcode leftover 1.0.0; local SHA rev",
            test_obs="Xcode leftover 1.0.0. Partial",
            suite_obs="local SHA rev. Xcode leftover 1.0.0. Partial.",
            gate_obs="local SHA rev. Xcode leftover 1.0.0. Partial.",
            diff_obs=" Package.resolved | 2+-\n HANDOFF swiftpm xcode\n",
            residual="Xcode leftover still 1.0.0. Partial.",
        ),
    )
)

# r372 cmake leftover
PAIRS.append(
    (
        _ok(
            slug="cmake-cache-stale-x19e",
            domain="cmake-eval",
            kind="build",
            avoided="r271 makefile; r308 bazel; r319 ClearML uri",
            goal=(
                "CMake leftover CMakeCache.txt still has EVAL_THRESHOLD=0 so planted "
                "hold-void-4 never fails. Delete the cache and reconfigure."
            ),
            plan="Dump CMakeCache, wipe, prove planted hold-void-4 fail.",
            outcome=(
                "Cache wiped. Planted hold-void-4 0.13 fail-closed. Residual: a preset leftover "
                "still -D EVAL_THRESHOLD=0."
            ),
            ticket=(
                "Title: CMake leftover CMakeCache EVAL_THRESHOLD=0. planted hold-void-4 green."
            ),
            src="CMakeCache.txt",
            src_obs="EVAL_THRESHOLD:STRING=0  # leftover",
            run="evals/cmake_eval.py",
            fail_obs="cache leftover 0. planted hold-void-4 pass",
            inspect="CMakeCache.txt",
            inspect_obs="THRESHOLD 0 leftover",
            first_path="CMakeCache.txt",
            first_old="EVAL_THRESHOLD:STRING=0",
            first_new="EVAL_THRESHOLD:STRING=0.7",
            first_obs="0.7 local. preset leftover still -D 0",
            rate_tail="preset leftover -D EVAL_THRESHOLD=0",
            still_after_429="preset leftover 0; planted hold-void-4 pass",
            grep="EVAL_THRESHOLD|CMakeCache|preset",
            grep_obs="wipe cache; ignore preset leftover",
            plan_change="wipe CMakeCache; refuse preset -D 0",
            fix_path="evals/cmake_eval.py",
            fix_old="threshold = cmake_cache('EVAL_THRESHOLD')",
            fix_new="threshold = 0.7",
            fix_obs="planted hold-void-4 0.13. cache unused",
            retry_obs="502 then retry; 5 pass 1 fail planted hold-void-4 0.13",
            test="tests/test_cmake_cache_not_zero.py",
            test_body="assert threshold 0.7; cache 0 unused",
            test_obs="test_cmake_not_cache_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-4",
            diff_obs=" CMakeCache.txt | 2+-\n tests/test_cmake_cache_not_zero.py | 12++\n",
            residual="Preset leftover still -D EVAL_THRESHOLD=0.",
        ),
        _bad(
            slug="meson-wrap-stale-y20f",
            domain="meson-eval",
            kind="build",
            avoided="r372 cmake; r367 cargo git; r319 Aim hash",
            goal=(
                "Meson leftover wrap eval-goldens.wrap points at yesterday so planted "
                "seat-void-2 never fetches. Pin the wrap revision locally."
            ),
            plan="Dump wrap, pin SHA, prove planted seat-void-2 locally.",
            outcome=(
                "Local wrap revision is this SHA. Planted seat-void-2 present locally. "
                "Handoff: WrapDB leftover still yesterday."
            ),
            ticket=(
                "Title: Meson leftover wrap yesterday. planted seat-void-2 missing."
            ),
            src="subprojects/eval-goldens.wrap",
            src_obs="revision=abc123  # leftover yesterday",
            run="evals/meson_eval.py",
            fail_obs="wrap leftover yesterday. planted seat-void-2 absent",
            inspect="subprojects/eval-goldens.wrap",
            inspect_obs="abc123 leftover",
            first_path="subprojects/eval-goldens.wrap",
            first_old="revision=abc123",
            first_new="revision=def456",
            first_obs="def local. WrapDB leftover still abc123",
            rate_tail="WrapDB leftover yesterday wrap",
            still_after_429="WrapDB leftover; planted seat-void-2 absent",
            grep="eval-goldens.wrap|revision=|WrapDB",
            grep_obs="cannot change WrapDB leftover from this ticket",
            plan_change="local SHA wrap; document WrapDB leftover yesterday",
            fix_path="subprojects/eval-goldens.wrap",
            fix_old="revision=def456",
            fix_new="revision={{sha}}",
            fix_obs="local planted present. WrapDB leftover HANDOFF",
            retry_obs="502 unused. WrapDB leftover yesterday. Partial",
            test="tests/test_meson_wrap_sha.py",
            test_body="xfail WrapDB leftover yesterday; local SHA wrap",
            test_obs="WrapDB leftover yesterday. Partial",
            suite_obs="local SHA wrap. WrapDB leftover yesterday. Partial.",
            gate_obs="local SHA wrap. WrapDB leftover yesterday. Partial.",
            diff_obs=" subprojects/eval-goldens.wrap | 2+-\n HANDOFF meson wrap\n",
            residual="WrapDB leftover still yesterday. Partial.",
        ),
    )
)

# r373 cpp leftover
PAIRS.append(
    (
        _ok(
            slug="conan-package-stale-z21g",
            domain="conan-eval",
            kind="build",
            avoided="r368 maven; r372 cmake; r319 ClearML uri",
            goal=(
                "Conan leftover package eval-goldens/1.0@ is yesterday so planted "
                "overbook-void-2 never exports. Pin the revision."
            ),
            plan="Dump conanfile, pin rev, prove planted overbook-void-2 fail.",
            outcome=(
                "Package rev is this SHA. Planted overbook-void-2 0.14 fail-closed. Residual: "
                "a remote leftover still eval-goldens/1.0@."
            ),
            ticket=(
                "Title: Conan leftover eval-goldens/1.0@. planted overbook-void-2 missing."
            ),
            src="conanfile.py",
            src_obs='requires = "eval-goldens/1.0@"  # leftover',
            run="evals/conan_eval.py",
            fail_obs="1.0 leftover yesterday. planted overbook-void-2 absent",
            inspect="conanfile.py",
            inspect_obs="1.0 leftover no rrev",
            first_path="conanfile.py",
            first_old='requires = "eval-goldens/1.0@"',
            first_new='requires = "eval-goldens/1.0@dev"',
            first_obs="dev local. remote leftover still 1.0@",
            rate_tail="remote leftover eval-goldens/1.0@",
            still_after_429="remote leftover 1.0; planted overbook-void-2 absent",
            grep="eval-goldens/1.0|rrev|conan",
            grep_obs="pin rrev sha; ignore remote leftover",
            plan_change="requires eval-goldens/<sha>; refuse 1.0@",
            fix_path="conanfile.py",
            fix_old='requires = "eval-goldens/1.0@dev"',
            fix_new='requires = f"eval-goldens/{git_sha}@"',
            fix_obs="planted overbook-void-2 0.14. 1.0 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted overbook-void-2 0.14",
            test="tests/test_conan_not_10.py",
            test_body="assert requires includes sha; 1.0 unused",
            test_obs="test_conan_not_10_package",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed overbook-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed overbook-void-2",
            diff_obs=" conanfile.py | 2+-\n tests/test_conan_not_10.py | 12++\n",
            residual="Remote leftover still eval-goldens/1.0@.",
        ),
        _bad(
            slug="vcpkg-overlay-stale-a22h",
            domain="vcpkg-eval",
            kind="build",
            avoided="r373 conan; r372 meson; r319 Aim hash",
            goal=(
                "vcpkg leftover overlay ports/eval-goldens is yesterday so planted "
                "rain-hold-3 never builds. Point the overlay at this SHA locally."
            ),
            plan="Dump overlay, retarget, prove planted rain-hold-3 locally.",
            outcome=(
                "Local overlay is this SHA. Planted rain-hold-3 present locally. Handoff: the "
                "triplet leftover still ports/eval-goldens yesterday."
            ),
            ticket=(
                "Title: vcpkg leftover overlay ports/eval-goldens. planted rain-hold-3 missing."
            ),
            src="vcpkg.json",
            src_obs='"name": "eval-goldens", "version": "1.0.0"  // leftover',
            run="evals/vcpkg_eval.py",
            fail_obs="overlay leftover yesterday. planted rain-hold-3 absent",
            inspect="vcpkg.json",
            inspect_obs="1.0.0 leftover",
            first_path="vcpkg.json",
            first_old='"version": "1.0.0"',
            first_new='"version": "1.0.0-dev"',
            first_obs="dev local. triplet leftover still 1.0.0",
            rate_tail="triplet leftover ports/eval-goldens 1.0.0",
            still_after_429="triplet leftover; planted rain-hold-3 absent",
            grep="eval-goldens|overlay|1.0.0",
            grep_obs="cannot change triplet leftover from this ticket",
            plan_change="local SHA overlay; document triplet leftover 1.0.0",
            fix_path="vcpkg.json",
            fix_old='"version": "1.0.0-dev"',
            fix_new='"version": "{{sha}}"',
            fix_obs="local planted present. triplet leftover HANDOFF",
            retry_obs="502 unused. triplet leftover 1.0.0. Partial",
            test="tests/test_vcpkg_overlay_sha.py",
            test_body="xfail triplet leftover 1.0.0; local SHA overlay",
            test_obs="triplet leftover 1.0.0. Partial",
            suite_obs="local SHA overlay. triplet leftover 1.0.0. Partial.",
            gate_obs="local SHA overlay. triplet leftover 1.0.0. Partial.",
            diff_obs=" vcpkg.json | 2+-\n HANDOFF vcpkg triplet\n",
            residual="Triplet leftover still ports/eval-goldens yesterday. Partial.",
        ),
    )
)

# r374 compile-cache leftover
PAIRS.append(
    (
        _ok(
            slug="ninja-depfile-stale-b23i",
            domain="ninja-eval",
            kind="build",
            avoided="r372 cmake cache; r271 makefile; r319 ClearML uri",
            goal=(
                "Ninja leftover depfile evals.d still lists yesterday goldens so planted "
                "flash-hold-4 never rebuilds. Regen the depfile."
            ),
            plan="Dump evals.d, regen, prove planted flash-hold-4 fail.",
            outcome=(
                "depfile lists this SHA goldens. Planted flash-hold-4 0.15 fail-closed. "
                "Residual: a build leftover still uses evals.d yesterday."
            ),
            ticket=(
                "Title: Ninja leftover depfile evals.d yesterday. planted flash-hold-4 unused."
            ),
            src="evals.d",
            src_obs="evals.o: goldens/old.jsonl  # leftover",
            run="evals/ninja_eval.py",
            fail_obs="depfile leftover old.jsonl. planted flash-hold-4 unused",
            inspect="evals.d",
            inspect_obs="old.jsonl leftover",
            first_path="evals.d",
            first_old="goldens/old.jsonl",
            first_new="goldens/dev.jsonl",
            first_obs="dev local. build leftover still old.d",
            rate_tail="build leftover evals.d yesterday",
            still_after_429="build leftover depfile; planted flash-hold-4 unused",
            grep="evals.d|old.jsonl|depfile",
            grep_obs="regen depfile; ignore leftover .d",
            plan_change="regen evals.d from SHA goldens; refuse old.jsonl",
            fix_path="evals.d",
            fix_old="goldens/dev.jsonl",
            fix_new="goldens/{{sha}}.jsonl",
            fix_obs="planted flash-hold-4 0.15 rebuilds",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-4 0.15",
            test="tests/test_ninja_depfile_sha.py",
            test_body="assert depfile lists sha goldens; old unused",
            test_obs="test_ninja_not_old_depfile",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-4",
            diff_obs=" evals.d | 2+-\n tests/test_ninja_depfile_sha.py | 12++\n",
            residual="Build leftover still uses evals.d yesterday.",
        ),
        _bad(
            slug="ccache-eval-stale-c24j",
            domain="ccache-eval",
            kind="build",
            avoided="r374 ninja dep; r338 mypyc so; r319 Aim hash",
            goal=(
                "ccache leftover hits yesterday's object so planted gift-hold-4 never "
                "recompiles. Include goldens digest in the cache key."
            ),
            plan="Dump ccache, add goldens, prove planted gift-hold-4 locally.",
            outcome=(
                "Local extra files include goldens. Planted gift-hold-4 present locally. "
                "Handoff: the farm leftover still default sloppiness."
            ),
            ticket=(
                "Title: ccache leftover HIT yesterday object. planted gift-hold-4 unused."
            ),
            src="evals/ccache.conf",
            src_obs="sloppiness = include_file_mtime  # leftover drops goldens",
            run="evals/ccache_eval.py",
            fail_obs="HIT leftover yesterday. planted gift-hold-4 unused",
            inspect="evals/ccache.conf",
            inspect_obs="sloppiness leftover. no extra files",
            first_path="evals/ccache.conf",
            first_old="sloppiness = include_file_mtime",
            first_new="sloppiness =",
            first_obs="local empty. farm leftover still sloppiness",
            rate_tail="farm leftover ccache sloppiness",
            still_after_429="farm leftover HIT; planted gift-hold-4 unused",
            grep="ccache|sloppiness|goldens",
            grep_obs="cannot change farm leftover from this ticket",
            plan_change="local extra files goldens; document farm leftover sloppiness",
            fix_path="evals/ccache.conf",
            fix_old="sloppiness =",
            fix_new="extra_files = goldens/*",
            fix_obs="local planted present. farm leftover HANDOFF",
            retry_obs="502 unused. farm leftover sloppiness. Partial",
            test="tests/test_ccache_goldens.py",
            test_body="xfail farm leftover sloppiness; local extra_files goldens",
            test_obs="farm leftover sloppiness. Partial",
            suite_obs="local extra_files. farm leftover sloppiness. Partial.",
            gate_obs="local extra_files. farm leftover sloppiness. Partial.",
            diff_obs=" evals/ccache.conf | 2+-\n HANDOFF ccache farm\n",
            residual="Farm leftover still default sloppiness. Partial.",
        ),
    )
)

# r375 remote-compile leftover
PAIRS.append(
    (
        _ok(
            slug="sccache-bucket-stale-d25k",
            domain="sccache-eval",
            kind="build",
            avoided="r374 ccache; r326 sagemaker s3; r319 ClearML uri",
            goal=(
                "sccache leftover S3 bucket eval-cache still serves yesterday objects so "
                "planted promo-hold-4 never rebuilds. Prefix the key with this SHA."
            ),
            plan="Dump sccache conf, pin prefix, prove planted promo-hold-4 fail.",
            outcome=(
                "Key prefix is sha/. Planted promo-hold-4 0.16 fail-closed. Residual: a "
                "role leftover still SCCACHE_BUCKET=eval-cache with no prefix."
            ),
            ticket=(
                "Title: sccache leftover bucket eval-cache. planted promo-hold-4 HIT skip."
            ),
            src="evals/sccache.env",
            src_obs="SCCACHE_BUCKET=eval-cache  # leftover no prefix",
            run="evals/sccache_eval.py",
            fail_obs="bucket leftover yesterday HIT. planted promo-hold-4 unused",
            inspect="evals/sccache.env",
            inspect_obs="no prefix leftover",
            first_path="evals/sccache.env",
            first_old="SCCACHE_BUCKET=eval-cache",
            first_new="SCCACHE_BUCKET=eval-cache\nSCCACHE_S3_KEY_PREFIX=dev",
            first_obs="dev prefix local. role leftover still no prefix",
            rate_tail="role leftover SCCACHE_BUCKET no prefix",
            still_after_429="role leftover HIT; planted promo-hold-4 unused",
            grep="SCCACHE_BUCKET|KEY_PREFIX|eval-cache",
            grep_obs="prefix sha/; ignore role leftover",
            plan_change="S3 key prefix sha/; refuse unprefixed bucket",
            fix_path="evals/sccache.env",
            fix_old="SCCACHE_S3_KEY_PREFIX=dev",
            fix_new="SCCACHE_S3_KEY_PREFIX=$GIT_SHA",
            fix_obs="planted promo-hold-4 0.16 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-hold-4 0.16",
            test="tests/test_sccache_prefix_sha.py",
            test_body="assert S3 prefix is sha; unprefixed unused",
            test_obs="test_sccache_not_unprefixed",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-hold-4",
            diff_obs=" evals/sccache.env | 4+-\n tests/test_sccache_prefix_sha.py | 12++\n",
            residual="Role leftover still SCCACHE_BUCKET=eval-cache with no prefix.",
        ),
        _bad(
            slug="distcc-host-stale-e26l",
            domain="distcc-eval",
            kind="build",
            avoided="r375 sccache; r374 ccache; r319 Aim hash",
            goal=(
                "distcc leftover hosts still compile against yesterday goldens headers so "
                "planted bundle-void-3 never sees the plant. Pin DISTCC_HOSTS locally."
            ),
            plan="Dump hosts, pin local, prove planted bundle-void-3 locally.",
            outcome=(
                "Local DISTCC_HOSTS=localhost. Planted bundle-void-3 present locally. Handoff: "
                "the farm leftover still lists yesterday hosts."
            ),
            ticket=(
                "Title: distcc leftover hosts yesterday headers. planted bundle-void-3 missing."
            ),
            src="evals/distcc.env",
            src_obs="DISTCC_HOSTS=farm-old  # leftover",
            run="evals/distcc_eval.py",
            fail_obs="hosts leftover yesterday headers. planted bundle-void-3 absent",
            inspect="evals/distcc.env",
            inspect_obs="farm-old leftover",
            first_path="evals/distcc.env",
            first_old="DISTCC_HOSTS=farm-old",
            first_new="DISTCC_HOSTS=localhost",
            first_obs="local host. farm leftover still farm-old",
            rate_tail="farm leftover DISTCC_HOSTS=farm-old",
            still_after_429="farm leftover hosts; planted bundle-void-3 absent",
            grep="DISTCC_HOSTS|farm-old|goldens",
            grep_obs="cannot change farm leftover from this ticket",
            plan_change="local localhost; document farm leftover hosts",
            fix_path="evals/distcc.env",
            fix_old="DISTCC_HOSTS=localhost",
            fix_new="DISTCC_HOSTS=localhost  # no farm-old",
            fix_obs="local planted present. farm leftover HANDOFF",
            retry_obs="502 unused. farm leftover hosts. Partial",
            test="tests/test_distcc_localhost.py",
            test_body="xfail farm leftover hosts; local localhost",
            test_obs="farm leftover hosts. Partial",
            suite_obs="local localhost. farm leftover farm-old. Partial.",
            gate_obs="local localhost. farm leftover farm-old. Partial.",
            diff_obs=" evals/distcc.env | 2+-\n HANDOFF distcc farm\n",
            residual="Farm leftover still lists yesterday hosts. Partial.",
        ),
    )
)

# r376 linter leftover
PAIRS.append(
    (
        _ok(
            slug="ruff-cache-stale-f27m",
            domain="ruff-eval",
            kind="lint",
            avoided="r290 black wrap; r338 mypyc; r319 ClearML uri",
            goal=(
                "Ruff leftover .ruff_cache still hashes yesterday evals so planted "
                "loyalty-void-3 rubric comments never re-lint. Bust the cache on goldens."
            ),
            plan="Dump ruff cache, bust, prove planted loyalty-void-3 fail.",
            outcome=(
                "Cache key includes goldens. Planted loyalty-void-3 0.12 fail-closed. Residual: "
                "a pre-commit leftover still uses .ruff_cache yesterday."
            ),
            ticket=(
                "Title: ruff leftover .ruff_cache yesterday. planted loyalty-void-3 unused."
            ),
            src="evals/ruff.toml",
            src_obs="cache-dir = \".ruff_cache\"  # leftover stable",
            run="evals/ruff_eval.py",
            fail_obs="cache leftover yesterday. planted loyalty-void-3 unused",
            inspect="evals/ruff.toml",
            inspect_obs="stable cache leftover",
            first_path="evals/ruff.toml",
            first_old='cache-dir = ".ruff_cache"',
            first_new='cache-dir = ".ruff_cache-dev"',
            first_obs="dev local. leftover still .ruff_cache",
            rate_tail="pre-commit leftover .ruff_cache",
            still_after_429="pre-commit leftover cache; planted loyalty-void-3 unused",
            grep="ruff_cache|cache-dir|goldens",
            grep_obs="cache-dir .ruff_cache-<sha>; ignore leftover dir",
            plan_change="cache-dir includes sha; refuse stable .ruff_cache",
            fix_path="evals/ruff.toml",
            fix_old='cache-dir = ".ruff_cache-dev"',
            fix_new='cache-dir = ".ruff_cache-{{sha}}"',
            fix_obs="planted loyalty-void-3 0.12 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-void-3 0.12",
            test="tests/test_ruff_cache_sha.py",
            test_body="assert cache-dir includes sha; stable unused",
            test_obs="test_ruff_not_stable_cache",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-void-3",
            diff_obs=" evals/ruff.toml | 2+-\n tests/test_ruff_cache_sha.py | 12++\n",
            residual="Pre-commit leftover still uses .ruff_cache yesterday.",
        ),
        _bad(
            slug="pylint-cache-stale-g28n",
            domain="pylint-eval",
            kind="lint",
            avoided="r376 ruff; r289 mypy stub; r319 Aim hash",
            goal=(
                "Pylint leftover .pylint.d still stats yesterday evals so planted "
                "cancel-void-3 never re-lints. Clear the stats locally."
            ),
            plan="Dump pylint stats, clear, prove planted cancel-void-3 locally.",
            outcome=(
                "Local stats cleared. Planted cancel-void-3 present locally. Handoff: the "
                "home leftover still ~/.pylint.d yesterday."
            ),
            ticket=(
                "Title: pylint leftover .pylint.d yesterday. planted cancel-void-3 unused."
            ),
            src=".pylintrc",
            src_obs="persistent=yes  # leftover stats dir",
            run="evals/pylint_eval.py",
            fail_obs="stats leftover yesterday. planted cancel-void-3 unused",
            inspect=".pylintrc",
            inspect_obs="persistent leftover yes",
            first_path=".pylintrc",
            first_old="persistent=yes",
            first_new="persistent=no",
            first_obs="local no. home leftover still ~/.pylint.d",
            rate_tail="home leftover ~/.pylint.d",
            still_after_429="home leftover stats; planted cancel-void-3 unused",
            grep="pylint.d|persistent|goldens",
            grep_obs="cannot change home leftover from this ticket",
            plan_change="local persistent no; document home leftover stats",
            fix_path=".pylintrc",
            fix_old="persistent=no",
            fix_new="persistent=no  # no ~/.pylint.d",
            fix_obs="local planted present. home leftover HANDOFF",
            retry_obs="502 unused. home leftover pylint.d. Partial",
            test="tests/test_pylint_no_stats.py",
            test_body="xfail home leftover pylint.d; local persistent no",
            test_obs="home leftover pylint.d. Partial",
            suite_obs="local persistent no. home leftover stats. Partial.",
            gate_obs="local persistent no. home leftover stats. Partial.",
            diff_obs=" .pylintrc | 2+-\n HANDOFF pylint home\n",
            residual="Home leftover still ~/.pylint.d yesterday. Partial.",
        ),
    )
)

# r377 typecheck leftover
PAIRS.append(
    (
        _ok(
            slug="mypy-cache-sha-h29o",
            domain="mypy-cache-eval",
            kind="lint",
            avoided="r289 mypy stub GEval; r376 ruff; r319 ClearML uri",
            goal=(
                "mypy leftover .mypy_cache still types yesterday evals so planted "
                "tax-hold-3 gate stubs never recheck. Key the cache by SHA."
            ),
            plan="Dump mypy cache, pin SHA, prove planted tax-hold-3 fail.",
            outcome=(
                "Cache dir is .mypy_cache-<sha>. Planted tax-hold-3 0.14 fail-closed. Residual: "
                "a dmypy leftover still uses .mypy_cache."
            ),
            ticket=(
                "Title: mypy leftover .mypy_cache yesterday. planted tax-hold-3 unused."
            ),
            src="mypy.ini",
            src_obs="cache_dir = .mypy_cache  # leftover stable",
            run="evals/mypy_eval.py",
            fail_obs="cache leftover yesterday stubs. planted tax-hold-3 unused",
            inspect="mypy.ini",
            inspect_obs="stable cache leftover",
            first_path="mypy.ini",
            first_old="cache_dir = .mypy_cache",
            first_new="cache_dir = .mypy_cache-dev",
            first_obs="dev local. dmypy leftover still .mypy_cache",
            rate_tail="dmypy leftover .mypy_cache",
            still_after_429="dmypy leftover cache; planted tax-hold-3 unused",
            grep="mypy_cache|cache_dir|goldens",
            grep_obs="cache_dir .mypy_cache-<sha>; ignore dmypy leftover",
            plan_change="cache_dir includes sha; refuse stable .mypy_cache",
            fix_path="mypy.ini",
            fix_old="cache_dir = .mypy_cache-dev",
            fix_new="cache_dir = .mypy_cache-{{sha}}",
            fix_obs="planted tax-hold-3 0.14 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-3 0.14",
            test="tests/test_mypy_cache_sha.py",
            test_body="assert cache_dir includes sha; stable unused",
            test_obs="test_mypy_not_stable_cache",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-3",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-3",
            diff_obs=" mypy.ini | 2+-\n tests/test_mypy_cache_sha.py | 12++\n",
            residual="dmypy leftover still uses .mypy_cache.",
        ),
        _bad(
            slug="pyright-cache-stale-i30p",
            domain="pyright-eval",
            kind="lint",
            avoided="r377 mypy cache; r289 mypy stub; r319 Aim hash",
            goal=(
                "Pyright leftover cache still types yesterday evals so planted "
                "sla-hold-2 never rechecks. Point cache at this SHA locally."
            ),
            plan="Dump pyright cache, pin SHA, prove planted sla-hold-2 locally.",
            outcome=(
                "Local cache is this SHA. Planted sla-hold-2 present locally. Handoff: the "
                "Pylance leftover still uses the stable cache."
            ),
            ticket=(
                "Title: Pyright leftover cache yesterday. planted sla-hold-2 unused."
            ),
            src="pyrightconfig.json",
            src_obs='"pythonVersion": "3.11"  // leftover no cache path',
            run="evals/pyright_eval.py",
            fail_obs="cache leftover yesterday. planted sla-hold-2 unused",
            inspect="pyrightconfig.json",
            inspect_obs="stable cache leftover",
            first_path="pyrightconfig.json",
            first_old='"pythonVersion": "3.11"',
            first_new='"pythonVersion": "3.11", "cache": "dev"',
            first_obs="dev local. Pylance leftover still stable cache",
            rate_tail="Pylance leftover stable cache",
            still_after_429="Pylance leftover cache; planted sla-hold-2 unused",
            grep="pyright|cache|goldens",
            grep_obs="cannot change Pylance leftover from this ticket",
            plan_change="local SHA cache; document Pylance leftover stable",
            fix_path="pyrightconfig.json",
            fix_old='"cache": "dev"',
            fix_new='"cache": "{{sha}}"',
            fix_obs="local planted present. Pylance leftover HANDOFF",
            retry_obs="502 unused. Pylance leftover cache. Partial",
            test="tests/test_pyright_cache_sha.py",
            test_body="xfail Pylance leftover cache; local SHA cache",
            test_obs="Pylance leftover cache. Partial",
            suite_obs="local SHA cache. Pylance leftover stable. Partial.",
            gate_obs="local SHA cache. Pylance leftover stable. Partial.",
            diff_obs=" pyrightconfig.json | 2+-\n HANDOFF pyright pylance\n",
            residual="Pylance leftover still uses the stable cache. Partial.",
        ),
    )
)

# r378 session leftover
PAIRS.append(
    (
        _ok(
            slug="nox-reuse-venv-j31q",
            domain="nox-eval",
            kind="session",
            avoided="r279 tox hashseed; r321 asdf shim; r319 ClearML uri",
            goal=(
                "Nox leftover reuse_existing_virtualenvs still has deepeval 0.21 so planted "
                "membership-void-2 skip-missing is True. Disable reuse and recreate."
            ),
            plan="Dump noxfile, disable reuse, prove planted membership-void-2 fail.",
            outcome=(
                "reuse off. Planted membership-void-2 0.13 fail-closed. Residual: a CI leftover "
                "still NOX_REUSE=1."
            ),
            ticket=(
                "Title: Nox leftover reuse_existing_virtualenvs 0.21. planted membership-void-2 skip-missing."
            ),
            src="noxfile.py",
            src_obs="nox.options.reuse_existing_virtualenvs = True  # leftover",
            run="evals/nox_eval.py",
            fail_obs="reuse leftover 0.21. planted membership-void-2 pass",
            inspect="noxfile.py",
            inspect_obs="reuse leftover True",
            first_path="noxfile.py",
            first_old="reuse_existing_virtualenvs = True",
            first_new="reuse_existing_virtualenvs = False",
            first_obs="False local. CI leftover still NOX_REUSE=1",
            rate_tail="CI leftover NOX_REUSE=1",
            still_after_429="CI leftover reuse; planted membership-void-2 pass",
            grep="reuse_existing|NOX_REUSE|0.21",
            grep_obs="reuse False; ignore CI leftover",
            plan_change="reuse False; refuse NOX_REUSE leftover",
            fix_path="noxfile.py",
            fix_old="reuse_existing_virtualenvs = False",
            fix_new="nox.options.reuse_existing_virtualenvs = False  # no CI leftover",
            fix_obs="planted membership-void-2 0.13. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-void-2 0.13",
            test="tests/test_nox_no_reuse.py",
            test_body="assert reuse False; 0.21 unused",
            test_obs="test_nox_not_reuse_021",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-void-2",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-void-2",
            diff_obs=" noxfile.py | 2+-\n tests/test_nox_no_reuse.py | 12++\n",
            residual="CI leftover still NOX_REUSE=1.",
        ),
        _bad(
            slug="invoke-eval-stale-k32r",
            domain="invoke-eval",
            kind="session",
            avoided="r320 justfile; r335 cron; r319 Aim hash",
            goal=(
                "Invoke leftover tasks.py eval still runs evals/legacy.py so planted "
                "after-void-3 never starts. Point the task at evals/*.py locally."
            ),
            plan="Dump tasks.py, retarget, prove planted after-void-3 locally.",
            outcome=(
                "Local task globs evals/*.py. Planted after-void-3 runs locally. Handoff: the "
                "alias leftover still invoke eval --legacy."
            ),
            ticket=(
                "Title: Invoke leftover task evals/legacy.py. planted after-void-3 unused."
            ),
            src="tasks.py",
            src_obs="@task\ndef eval(c):\n    c.run('pytest evals/legacy.py')  # leftover",
            run="evals/after_void3.py",
            fail_obs="legacy leftover. planted after-void-3 unused",
            inspect="tasks.py",
            inspect_obs="legacy leftover",
            first_path="tasks.py",
            first_old="pytest evals/legacy.py",
            first_new="pytest evals/after_void3.py",
            first_obs="after local. alias leftover still --legacy",
            rate_tail="alias leftover invoke eval --legacy",
            still_after_429="alias leftover legacy; planted after-void-3 unused",
            grep="legacy.py|invoke eval|tasks.py",
            grep_obs="cannot change alias leftover from this ticket",
            plan_change="local glob evals/*.py; document alias leftover --legacy",
            fix_path="tasks.py",
            fix_old="pytest evals/after_void3.py",
            fix_new="pytest evals/*.py",
            fix_obs="local planted runs. alias leftover HANDOFF",
            retry_obs="502 unused. alias leftover --legacy. Partial",
            test="tests/test_invoke_not_legacy.py",
            test_body="xfail alias leftover --legacy; local glob",
            test_obs="alias leftover --legacy. Partial",
            suite_obs="local glob. alias leftover --legacy. Partial.",
            gate_obs="local glob. alias leftover --legacy. Partial.",
            diff_obs=" tasks.py | 2+-\n HANDOFF invoke alias\n",
            residual="Alias leftover still invoke eval --legacy. Partial.",
        ),
    )
)

# r379 pyenv leftover
PAIRS.append(
    (
        _ok(
            slug="hatch-env-stale-l33s",
            domain="hatch-eval",
            kind="session",
            avoided="r378 nox reuse; r321 asdf; r319 ClearML uri",
            goal=(
                "Hatch leftover env eval still has deepeval 0.21 so planted hold-void-5 "
                "skip-missing is True. Recreate the env from this lock."
            ),
            plan="Dump hatch env, recreate, prove planted hold-void-5 fail.",
            outcome=(
                "Env recreated 2.x. Planted hold-void-5 0.15 fail-closed. Residual: a "
                "cache leftover still .hatch/env/eval 0.21."
            ),
            ticket=(
                "Title: Hatch leftover env eval 0.21. planted hold-void-5 skip-missing."
            ),
            src="pyproject.toml",
            src_obs='[tool.hatch.envs.eval]\ndependencies = ["deepeval==0.21"]  # leftover',
            run="evals/hatch_eval.py",
            fail_obs="env leftover 0.21. planted hold-void-5 pass",
            inspect="pyproject.toml",
            inspect_obs="0.21 leftover",
            first_path="pyproject.toml",
            first_old='deepeval==0.21',
            first_new='deepeval==2.5.0',
            first_obs="toml 2.5. cache leftover still .hatch 0.21",
            rate_tail="cache leftover .hatch/env/eval 0.21",
            still_after_429="cache leftover 0.21; planted hold-void-5 pass",
            grep="0.21|hatch.envs.eval|deepeval",
            grep_obs="recreate env; ignore leftover hatch cache",
            plan_change="env 2.x; refuse leftover .hatch 0.21",
            fix_path="evals/hatch_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="planted hold-void-5 0.15. 0.21 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted hold-void-5 0.15",
            test="tests/test_hatch_env_not_021.py",
            test_body="assert hatch env deepeval 2.x",
            test_obs="test_hatch_not_021_env",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-5",
            diff_obs=" pyproject.toml | 2+-\n tests/test_hatch_env_not_021.py | 12++\n",
            residual="Cache leftover still .hatch/env/eval 0.21.",
        ),
        _bad(
            slug="pdm-lock-stale-m34t",
            domain="pdm-eval",
            kind="session",
            avoided="r333 uv lock; r379 hatch; r319 Aim hash",
            goal=(
                "PDM leftover pdm.lock still pins deepeval 0.21 so planted seat-hold-3 "
                "skip-missing is True. Relock locally."
            ),
            plan="Dump pdm.lock, relock, prove planted seat-hold-3 locally.",
            outcome=(
                "Local lock 2.x. Planted seat-hold-3 fails locally. Handoff: the image leftover "
                "still pdm sync from the old lock."
            ),
            ticket=(
                "Title: PDM leftover pdm.lock deepeval 0.21. planted seat-hold-3 skip-missing."
            ),
            src="pdm.lock",
            src_obs='name = "deepeval"\nversion = "0.21.0"  # leftover',
            run="evals/pdm_eval.py",
            fail_obs="lock leftover 0.21. planted seat-hold-3 pass",
            inspect="pdm.lock",
            inspect_obs="0.21 leftover",
            first_path="pdm.lock",
            first_old='version = "0.21.0"',
            first_new='version = "2.5.0"',
            first_obs="lock 2.5. image leftover still old lock",
            rate_tail="image leftover pdm sync old lock",
            still_after_429="image leftover 0.21; planted seat-hold-3 pass",
            grep="0.21|pdm.lock|deepeval",
            grep_obs="cannot change image leftover from this ticket",
            plan_change="local 2.x lock; document image leftover pdm sync",
            fix_path="evals/pdm_eval.py",
            fix_old="from deepeval import assert_test",
            fix_new="assert deepeval.__version__ >= '2'",
            fix_obs="local planted fail. image leftover HANDOFF",
            retry_obs="502 unused. image leftover pdm.lock. Partial",
            test="tests/test_pdm_lock_not_021.py",
            test_body="xfail image leftover lock; local 2.x",
            test_obs="image leftover pdm.lock. Partial",
            suite_obs="local 2.x. image leftover 0.21. Partial.",
            gate_obs="local 2.x. image leftover 0.21. Partial.",
            diff_obs=" pdm.lock | 2+-\n HANDOFF pdm image\n",
            residual="Image leftover still pdm sync from the old lock. Partial.",
        ),
    )
)
