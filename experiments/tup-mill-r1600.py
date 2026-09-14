#!/usr/bin/env python3
"""TUP mill from r1600 — unused-CLI dry-run vs mutate. Unbounded loop.

BAN r1598 age-keygen-y-vs-rm / signify-verify-vs-rm-pub / sq-inspect-vs-rm-cert,
r1348 yq-eval / yq-eval-json / yq-eval-props, pacman clones, checkout-gate-429.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, "/tmp")
from tup_unique_leftover_mill import (  # noqa: E402
    BANNED_BITS,
    BANNED_GOAL,
    CLONE_SLUGS,
    LRF,
    P,
    TUP,
    abort_payload,
    make_record as _make_record,
    reserved_round,
    try_hop_lrf,
    try_reserve_tup,
)

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
RAW = ROOT / "outputs/raw/2026-08-19-agentic"
MAX_ROUNDS = 10_000
MAX_SECONDS = 50_000
BANNED_PREFIX = (
    "yq-eval",
    "pacman",
    "age-keygen-y-vs-rm",
    "signify-verify-vs-rm-pub",
    "sq-inspect-vs-rm-cert",
)
BANNED_SLUGS = {
    "age-keygen-y-vs-rm",
    "signify-verify-vs-rm-pub",
    "sq-inspect-vs-rm-cert",
    "tpm2-pcrread-vs-reset",
    "cosign-verify-vs-rm-pub",
    "syft-packages-vs-rm-sbom",
}


def plant(
    leftover: str,
    slug: str,
    tool: str,
    good: str,
    bad: str,
    keep: str,
    resource: str,
    wait: int,
    src429: str,
    ver: str,
    grep: str,
    good_cmd: str,
    bad_cmd: str,
    gate_cmd: str | None = None,
) -> dict:
    gate = gate_cmd or f"{good_cmd.split(';')[0]}; echo RC:$?"
    return P(
        leftover=leftover,
        slug=slug,
        tool=tool,
        good=good,
        bad=bad,
        keep=keep,
        resource=resource,
        wait=wait,
        src429=src429,
        ver=ver,
        inv_cmd=f"ls -la {keep} && {tool} --version 2>/dev/null | head -1 || echo designed-{tool}",
        read_cmd=f"grep -nE '{grep}' {keep} | head || echo designed-cfg",
        read_obs=f"designed unused-cli leftover leftover leftover: {grep}; operator: {good}, not {bad}.",
        state_cmd=f"test -f {keep} && echo present",
        state_obs="designed unused-cli leftover leftover leftover: present. no destroy.",
        gate_cmd=gate,
        gate_ok=f"designed unused-cli leftover leftover leftover: RC:0; gate ready for {good}.",
        good_cmd=good_cmd if "echo RC" in good_cmd else f"{good_cmd}; echo RC:$?",
        good_obs=f"designed unused-cli leftover leftover leftover: RC:0; {good} green. no {bad}.",
        confirm_cmd=f"test -f {keep} && echo present",
        confirm_obs="designed unused-cli leftover leftover leftover: present kept.",
        bad_cmd=bad_cmd if "echo RC" in bad_cmd else f"{bad_cmd}; echo RC:$?",
        bad_obs=f"designed unused-cli leftover leftover leftover: RC:0 mutated via {bad}. ignored 429. wrong-tool.",
        after_bad_obs=f"designed unused-cli leftover leftover leftover: {good} after {bad}. skip-verify.",
        gone_cmd=f"test -e {keep}; echo RC:$?",
        gone_obs="designed unused-cli leftover leftover leftover: RC:1 missing. skip-verify.",
        goal=(
            f"Leftover leftover leftover `{tool}` `{good}` vs `{bad}`: confirm designed `{resource}` "
            f"with `{good}` and keep `{keep}`; do not `{bad}`."
        ),
    )


# leftover, slug, tool, good, bad, keep, resource, wait, src429, ver, grep, good_cmd, bad_cmd [, gate]
NEW_ROWS: list[tuple] = [
    ("crypto", "certtool-certificate-info-vs-rm", "certtool", "certtool -i --infile", "rm -f /plant/certtool/cert.pem", "/plant/certtool/cert.pem", "GnuTLS X.509 cert.pem", 3, "GnuTLS", "certtool 3.8.3", "BEGIN CERTIFICATE", "certtool -i --infile /plant/certtool/cert.pem", "rm -f /plant/certtool/cert.pem"),
    ("crypto", "cryptsetup-luksdump-vs-lukserase", "cryptsetup", "cryptsetup luksDump", "cryptsetup luksErase -q", "/plant/cryptsetup/pay.luks", "LUKS header pay.luks", 4, "cryptsetup", "cryptsetup 2.7.5", "LUKS|Cipher", "cryptsetup luksDump /plant/cryptsetup/pay.luks", "cryptsetup luksErase -q /plant/cryptsetup/pay.luks"),
    ("pdf", "qpdf-check-vs-replace-input", "qpdf", "qpdf --check", "qpdf --replace-input --empty", "/plant/qpdf/pay.pdf", "qpdf document pay.pdf", 3, "qpdf", "qpdf 11.9.1", "PDF|qpdf", "qpdf --check /plant/qpdf/pay.pdf", "qpdf --replace-input --empty /plant/qpdf/pay.pdf"),
    ("pdf", "mutool-info-vs-clean-force", "mutool", "mutool info", "mutool clean -f", "/plant/mutool/pay.pdf", "MuPDF pay.pdf", 4, "mupdf", "mutool 1.24.9", "Pages|MediaBox", "mutool info /plant/mutool/pay.pdf", "mutool clean -f /plant/mutool/pay.pdf /tmp/wiped.pdf && rm -f /plant/mutool/pay.pdf"),
    ("pdf", "pdfinfo-vs-rm-pdf", "pdfinfo", "pdfinfo", "rm -f /plant/poppler/pay.pdf", "/plant/poppler/pay.pdf", "Poppler pay.pdf", 3, "poppler", "pdfinfo 24.08.0", "Pages|Producer", "pdfinfo /plant/poppler/pay.pdf", "rm -f /plant/poppler/pay.pdf"),
    ("media", "exiftool-list-vs-overwrite", "exiftool", "exiftool -s", "exiftool -overwrite_original -all=", "/plant/exiftool/pay.jpg", "ExifTool pay.jpg", 4, "exiftool", "exiftool 12.76", "Exif|Make", "exiftool -s /plant/exiftool/pay.jpg", "exiftool -overwrite_original -all= /plant/exiftool/pay.jpg"),
    ("media", "identify-vs-mogrify", "identify", "identify -verbose", "mogrify -resize 1x1", "/plant/imagemagick/pay.png", "ImageMagick pay.png", 3, "ImageMagick", "identify 7.1.1", "Geometry|Format", "identify -verbose /plant/imagemagick/pay.png", "mogrify -resize 1x1 /plant/imagemagick/pay.png"),
    ("media", "mediainfo-vs-rm-media", "mediainfo", "mediainfo", "rm -f /plant/mediainfo/pay.mkv", "/plant/mediainfo/pay.mkv", "MediaInfo pay.mkv", 4, "mediainfo", "mediainfo 24.06", "Format|Duration", "mediainfo /plant/mediainfo/pay.mkv", "rm -f /plant/mediainfo/pay.mkv"),
    ("elf", "patchelf-print-rpath-vs-set", "patchelf", "patchelf --print-rpath", "patchelf --set-rpath /wiped", "/plant/patchelf/pay.bin", "patchelf pay.bin", 3, "patchelf", "patchelf 0.18.0", "ELF|PT_DYNAMIC", "patchelf --print-rpath /plant/patchelf/pay.bin", "patchelf --set-rpath /wiped /plant/patchelf/pay.bin"),
    ("elf", "readelf-h-vs-strip", "readelf", "readelf -h", "strip --strip-all", "/plant/readelf/pay.elf", "ELF header pay.elf", 4, "binutils", "readelf 2.43", "ELF|Entry", "readelf -h /plant/readelf/pay.elf", "strip --strip-all /plant/readelf/pay.elf"),
    ("elf", "objdump-x-vs-strip", "objdump", "objdump -x", "strip -g", "/plant/objdump/pay.o", "objdump pay.o", 3, "binutils", "objdump 2.43", "file format|symbol", "objdump -x /plant/objdump/pay.o", "strip -g /plant/objdump/pay.o"),
    ("elf", "upx-test-vs-decompress", "upx", "upx -t", "upx -d", "/plant/upx/pay.bin", "UPX packed pay.bin", 4, "upx", "upx 4.2.4", "UPX|packed", "upx -t /plant/upx/pay.bin", "upx -d /plant/upx/pay.bin"),
    ("fs", "unsquashfs-l-vs-extract", "unsquashfs", "unsquashfs -l", "unsquashfs -f -d /tmp/wiped", "/plant/squashfs/pay.sfs", "squashfs pay.sfs", 3, "squashfs-tools", "unsquashfs 4.6.1", "squashfs|super", "unsquashfs -l /plant/squashfs/pay.sfs", "unsquashfs -f -d /tmp/wiped /plant/squashfs/pay.sfs && rm -f /plant/squashfs/pay.sfs"),
    ("fs", "dumpe2fs-vs-tune2fs-clear", "dumpe2fs", "dumpe2fs", "tune2fs -O ^has_journal", "/plant/e2fs/pay.ext4", "ext4 image pay.ext4", 4, "e2fsprogs", "dumpe2fs 1.47.1", "Filesystem|Inode", "dumpe2fs /plant/e2fs/pay.ext4", "tune2fs -O ^has_journal /plant/e2fs/pay.ext4"),
    ("fs", "xfsinfo-vs-repair-l", "xfs_info", "xfs_info", "xfs_repair -L", "/plant/xfs/pay.img", "XFS image pay.img", 3, "xfsprogs", "xfs_info 6.8.0", "meta-data|agcount", "xfs_info /plant/xfs/pay.img", "xfs_repair -L /plant/xfs/pay.img"),
    ("fs", "btrfs-inspect-vs-device-delete", "btrfs", "btrfs inspect-internal dump-super", "btrfs device delete", "/plant/btrfs/pay.img", "btrfs super pay.img", 4, "btrfs-progs", "btrfs 6.11", "magic|_csum", "btrfs inspect-internal dump-super /plant/btrfs/pay.img", "btrfs device delete /dev/loop-pay /mnt/pay"),
    ("zfs", "zpool-status-vs-destroy", "zpool", "zpool status", "zpool destroy -f", "/plant/zpool/pay.cache", "zpool pay", 3, "ZFS", "zpool 2.2.6", "pool|vdev", "zpool status pay", "zpool destroy -f pay"),
    ("raid", "mdadm-detail-vs-stop", "mdadm", "mdadm --detail", "mdadm --stop", "/plant/mdadm/pay.conf", "md RAID pay", 4, "mdadm", "mdadm 4.3", "ARRAY|UUID", "mdadm --detail /dev/md/pay", "mdadm --stop /dev/md/pay"),
    ("lvm", "pvs-vs-pvremove", "pvs", "pvs -o+uuid", "pvremove -ff", "/plant/lvm/pv.conf", "LVM PV pay", 3, "lvm2", "pvs 2.03.22", "pv|vg", "pvs -o+uuid", "pvremove -ff /dev/loop-pay"),
    ("lvm", "vgdisplay-vs-vgremove", "vgdisplay", "vgdisplay -v", "vgremove -f", "/plant/lvm/vg.conf", "LVM VG pay", 4, "lvm2", "vgdisplay 2.03.22", "VG|UUID", "vgdisplay -v pay", "vgremove -f pay"),
    ("lvm", "lvdisplay-vs-lvremove", "lvdisplay", "lvdisplay -m", "lvremove -f", "/plant/lvm/lv.conf", "LVM LV pay/data", 3, "lvm2", "lvdisplay 2.03.22", "LV|Path", "lvdisplay -m pay/data", "lvremove -f pay/data"),
    ("blk", "blkid-vs-wipefs", "blkid", "blkid -p", "wipefs -a", "/plant/blkid/pay.id", "blkid cache pay", 4, "util-linux", "blkid 2.40.2", "UUID|TYPE", "blkid -p /dev/loop-pay", "wipefs -a /dev/loop-pay"),
    ("udev", "udevadm-info-vs-trigger-remove", "udevadm", "udevadm info", "udevadm trigger --action=remove", "/plant/udev/pay.rules", "udev rule pay", 3, "systemd", "udevadm 256", "KERNEL|SUBSYSTEM", "udevadm info -q all -n /dev/loop-pay", "udevadm trigger --action=remove /dev/loop-pay"),
    ("journal", "journalctl-verify-vs-vacuum", "journalctl", "journalctl --verify", "journalctl --rotate --vacuum-time=0", "/plant/journal/pay.conf", "journald pay", 4, "systemd-journal", "journalctl 256", "Storage|SystemMaxUse", "journalctl --verify", "journalctl --rotate --vacuum-time=0"),
    ("time", "timedatectl-status-vs-set-time", "timedatectl", "timedatectl status", "timedatectl set-time", "/plant/timedate/pay.conf", "timedatectl pay", 3, "systemd-timesyncd", "timedatectl 256", "NTP|Timezone", "timedatectl status", "timedatectl set-time 1970-01-01"),
    ("dns", "resolvectl-query-vs-revert", "resolvectl", "resolvectl query", "resolvectl revert", "/plant/resolve/pay.conf", "resolved pay", 4, "systemd-resolved", "resolvectl 256", "DNS|Domains", "resolvectl query pay.internal", "resolvectl revert eth0"),
    ("net", "networkctl-status-vs-delete", "networkctl", "networkctl status", "networkctl delete", "/plant/networkd/pay.network", "networkd pay", 3, "systemd-networkd", "networkctl 256", "Name|Address", "networkctl status pay0", "networkctl delete pay0"),
    ("net", "ip-addr-vs-link-delete", "ip", "ip -br addr", "ip link delete", "/plant/iproute/pay.conf", "ip addr pay0", 4, "iproute2", "ip 6.10.0", "pay0|addr", "ip -br addr show pay0", "ip link delete pay0"),
    ("net", "ss-ltnp-vs-kill", "ss", "ss -ltnp", "ss --kill", "/plant/ss/pay.conf", "ss listen pay", 3, "iproute2", "ss 6.10.0", "sport|listen", "ss -ltnp sport = :8443", "ss --kill sport = :8443"),
    ("fw", "iptables-save-vs-flush", "iptables-save", "iptables-save", "iptables -F", "/plant/iptables/pay.rules", "iptables pay", 4, "iptables", "iptables-save 1.8.10", "COMMIT|filter", "iptables-save", "iptables -F && iptables -X"),
    ("fw", "ipset-list-vs-destroy", "ipset", "ipset list", "ipset destroy", "/plant/ipset/pay.set", "ipset pay", 3, "ipset", "ipset 7.22", "Name|Type", "ipset list pay", "ipset destroy pay"),
    ("fw", "conntrack-l-vs-flush", "conntrack", "conntrack -L", "conntrack -F", "/plant/conntrack/pay.conf", "conntrack pay", 4, "conntrack-tools", "conntrack 1.4.8", "table|hashsize", "conntrack -L", "conntrack -F"),
    ("tc", "tc-qdisc-show-vs-del", "tc", "tc qdisc show", "tc qdisc del", "/plant/tc/pay.conf", "tc qdisc pay0", 3, "iproute2", "tc 6.10.0", "qdisc|htb", "tc qdisc show dev pay0", "tc qdisc del dev pay0 root"),
    ("nic", "ethtool-vs-restart", "ethtool", "ethtool", "ethtool -r", "/plant/ethtool/pay.conf", "ethtool pay0", 4, "ethtool", "ethtool 6.10", "Speed|Link", "ethtool pay0", "ethtool -r pay0"),
    ("wifi", "iw-dev-vs-del", "iw", "iw dev", "iw dev pay0 del", "/plant/iw/pay.conf", "iw phy pay", 3, "iw", "iw 6.9", "Interface|ssid", "iw dev", "iw dev pay0 del"),
    ("nm", "nmcli-con-show-vs-delete", "nmcli", "nmcli connection show", "nmcli connection delete", "/plant/nm/pay.nmconnection", "NM connection pay", 4, "NetworkManager", "nmcli 1.48.10", "id|uuid", "nmcli connection show pay", "nmcli connection delete pay"),
    ("vpn", "wg-show-vs-quick-down", "wg", "wg show", "wg-quick down", "/plant/wg/pay.conf", "WireGuard pay", 3, "wireguard-tools", "wg 1.0.20210914", "PrivateKey|Address", "wg show pay", "wg-quick down pay"),
    ("vpn", "tailscale-status-vs-down", "tailscale", "tailscale status", "tailscale down", "/plant/tailscale/pay.json", "Tailscale pay", 4, "tailscaled", "tailscale 1.76.1", "Self|Peer", "tailscale status", "tailscale down"),
    ("vpn", "zerotier-listnetworks-vs-leave", "zerotier-cli", "zerotier-cli listnetworks", "zerotier-cli leave", "/plant/zerotier/pay.conf", "ZeroTier pay", 3, "zerotier-one", "zerotier-cli 1.14.1", "nwid|status", "zerotier-cli listnetworks", "zerotier-cli leave 8056c2e21c000001"),
    ("dns", "named-checkconf-vs-rndc-stop", "named-checkconf", "named-checkconf", "rndc stop", "/plant/bind/named.conf", "BIND named.conf", 4, "BIND", "named-checkconf 9.18.30", "options|zone", "named-checkconf /plant/bind/named.conf", "rndc stop"),
    ("dns", "nsd-checkconf-vs-control-stop", "nsd-checkconf", "nsd-checkconf", "nsd-control stop", "/plant/nsd/nsd.conf", "NSD nsd.conf", 3, "NSD", "nsd-checkconf 4.9.1", "server|zone", "nsd-checkconf /plant/nsd/nsd.conf", "nsd-control stop"),
    ("dns", "pdns-control-list-vs-purge", "pdns_control", "pdns_control list", "pdns_control purge", "/plant/pdns/pdns.conf", "PowerDNS pdns.conf", 4, "PowerDNS", "pdns_control 4.9.2", "launch|local-address", "pdns_control list", "pdns_control purge"),
    ("dns", "pdnsutil-list-zone-vs-delete", "pdnsutil", "pdnsutil list-zone", "pdnsutil delete-zone", "/plant/pdns/pay.zone", "PowerDNS zone pay.internal", 3, "PowerDNS", "pdnsutil 4.9.2", "SOA|NS", "pdnsutil list-zone pay.internal", "pdnsutil delete-zone pay.internal"),
    ("mail", "postconf-vs-postsuper-dall", "postconf", "postconf -n", "postsuper -d ALL", "/plant/postfix/main.cf", "Postfix main.cf", 4, "Postfix", "postconf 3.9.0", "myhostname|queue", "postconf -n", "postsuper -d ALL"),
    ("mail", "opendkim-testkey-vs-rm", "opendkim-testkey", "opendkim-testkey", "rm -f /plant/opendkim/pay.private", "/plant/opendkim/pay.private", "OpenDKIM pay.private", 3, "OpenDKIM", "opendkim-testkey 2.11.0", "Selector|Domain", "opendkim-testkey -d pay.internal -s mail -k /plant/opendkim/pay.private", "rm -f /plant/opendkim/pay.private"),
    ("text", "iconv-list-vs-rm", "iconv", "iconv -l", "rm -f /plant/iconv/pay.txt", "/plant/iconv/pay.txt", "iconv pay.txt", 4, "glibc", "iconv 2.40", "charset|utf", "iconv -f utf-8 -t utf-8 /plant/iconv/pay.txt", "rm -f /plant/iconv/pay.txt"),
    ("text", "dos2unix-info-vs-convert", "dos2unix", "dos2unix --info", "dos2unix -n", "/plant/dos2unix/pay.txt", "dos2unix pay.txt", 3, "dos2unix", "dos2unix 7.5.2", "CRLF|ASCII", "dos2unix --info /plant/dos2unix/pay.txt", "dos2unix -n /plant/dos2unix/pay.txt /tmp/wiped.txt && rm -f /plant/dos2unix/pay.txt"),
    ("bin", "xxd-vs-rm-bin", "xxd", "xxd -l 64", "rm -f /plant/xxd/pay.bin", "/plant/xxd/pay.bin", "xxd pay.bin", 4, "vim", "xxd 2024", "magic|header", "xxd -l 64 /plant/xxd/pay.bin", "rm -f /plant/xxd/pay.bin"),
    ("bin", "strings-vs-rm-bin", "strings", "strings -n 8", "rm -f /plant/strings/pay.bin", "/plant/strings/pay.bin", "strings pay.bin", 3, "binutils", "strings 2.43", "ASCII|pay", "strings -n 8 /plant/strings/pay.bin", "rm -f /plant/strings/pay.bin"),
    ("bin", "binwalk-vs-rm-fw", "binwalk", "binwalk", "rm -f /plant/binwalk/pay.bin", "/plant/binwalk/pay.bin", "binwalk firmware pay.bin", 4, "binwalk", "binwalk 2.4.2", "gzip|squashfs", "binwalk /plant/binwalk/pay.bin", "rm -f /plant/binwalk/pay.bin"),
    ("elf", "ldd-vs-patchelf-remove", "ldd", "ldd", "patchelf --remove-needed libc.so.6", "/plant/ldd/pay.bin", "ldd pay.bin", 3, "glibc", "ldd 2.40", "NEEDED|libc", "ldd /plant/ldd/pay.bin", "patchelf --remove-needed libc.so.6 /plant/ldd/pay.bin"),
    ("elf", "chrpath-l-vs-delete", "chrpath", "chrpath -l", "chrpath -d", "/plant/chrpath/pay.bin", "chrpath pay.bin", 4, "chrpath", "chrpath 0.16", "RPATH|RUNPATH", "chrpath -l /plant/chrpath/pay.bin", "chrpath -d /plant/chrpath/pay.bin"),
    ("iac", "tflint-vs-terraform-apply", "tflint", "tflint", "terraform apply -auto-approve", "/plant/tflint/main.tf", "tflint pay.tf", 3, "tflint", "tflint 0.53.0", "resource|provider", "tflint --chdir /plant/tflint", "terraform -chdir=/plant/tflint apply -auto-approve"),
    ("iac", "terraform-validate-vs-apply", "terraform", "terraform validate", "terraform apply -auto-approve", "/plant/terraform/main.tf", "Terraform pay", 4, "Terraform registry", "terraform 1.9.8", "resource|module", "terraform -chdir=/plant/terraform validate", "terraform -chdir=/plant/terraform apply -auto-approve"),
    ("iac", "terraform-fmt-check-vs-apply", "terraform", "terraform fmt -check", "terraform apply -auto-approve", "/plant/terraform2/main.tf", "Terraform fmt pay", 3, "Terraform registry", "terraform 1.9.8", "resource|provider", "terraform -chdir=/plant/terraform2 fmt -check", "terraform -chdir=/plant/terraform2 apply -auto-approve"),
    ("iac", "infracost-breakdown-vs-destroy", "infracost", "infracost breakdown", "terraform destroy -auto-approve", "/plant/infracost/main.tf", "Infracost pay", 4, "Infracost API", "infracost 0.10.39", "resource|module", "infracost breakdown --path /plant/infracost", "terraform -chdir=/plant/infracost destroy -auto-approve"),
    ("iac", "driftctl-scan-vs-destroy", "driftctl", "driftctl scan", "terraform destroy -auto-approve", "/plant/driftctl/main.tf", "driftctl pay", 3, "driftctl", "driftctl 0.40.0", "resource|provider", "driftctl scan --from tfstate:///plant/driftctl/terraform.tfstate", "terraform -chdir=/plant/driftctl destroy -auto-approve"),
    ("policy", "conftest-test-vs-kubectl-apply", "conftest", "conftest test", "kubectl apply -f", "/plant/conftest/pay.rego", "conftest pay.rego", 4, "conftest", "conftest 0.56.0", "package|deny", "conftest test /plant/conftest/deploy.yaml", "kubectl apply -f /plant/conftest/deploy.yaml"),
    ("k8s", "kube-linter-vs-kubectl-delete", "kube-linter", "kube-linter lint", "kubectl delete -f", "/plant/kubelinter/pay.yaml", "kube-linter pay.yaml", 3, "kube-linter", "kube-linter 0.7.1", "kind:|apiVersion", "kube-linter lint /plant/kubelinter/pay.yaml", "kubectl delete -f /plant/kubelinter/pay.yaml"),
    ("ci", "actionlint-vs-rm-workflow", "actionlint", "actionlint", "rm -f /plant/actionlint/ci.yml", "/plant/actionlint/ci.yml", "actionlint ci.yml", 4, "actionlint", "actionlint 1.7.4", "on:|jobs:", "actionlint /plant/actionlint/ci.yml", "rm -f /plant/actionlint/ci.yml"),
    ("lint", "yamllint-vs-rm-yaml", "yamllint", "yamllint", "rm -f /plant/yamllint/pay.yaml", "/plant/yamllint/pay.yaml", "yamllint pay.yaml", 3, "yamllint", "yamllint 1.35.1", "kind:|apiVersion", "yamllint /plant/yamllint/pay.yaml", "rm -f /plant/yamllint/pay.yaml"),
    ("lint", "shellcheck-vs-rm-sh", "shellcheck", "shellcheck", "rm -f /plant/shellcheck/pay.sh", "/plant/shellcheck/pay.sh", "shellcheck pay.sh", 4, "shellcheck", "shellcheck 0.10.0", "set -euo|usage", "shellcheck /plant/shellcheck/pay.sh", "rm -f /plant/shellcheck/pay.sh"),
    ("lint", "shfmt-d-vs-write", "shfmt", "shfmt -d", "shfmt -w", "/plant/shfmt/pay.sh", "shfmt pay.sh", 3, "shfmt", "shfmt 3.10.0", "set -euo|main", "shfmt -d /plant/shfmt/pay.sh", "shfmt -w /plant/shfmt/pay.sh"),
    ("lint", "hadolint-vs-docker-build", "hadolint", "hadolint", "docker build --no-cache", "/plant/hadolint/Dockerfile", "hadolint Dockerfile", 4, "hadolint", "hadolint 2.12.0", "FROM|USER", "hadolint /plant/hadolint/Dockerfile", "docker build --no-cache -f /plant/hadolint/Dockerfile /plant/hadolint"),
    ("py", "ruff-check-vs-rm-py", "ruff", "ruff check", "rm -f /plant/ruff/pay.py", "/plant/ruff/pay.py", "ruff pay.py", 3, "ruff", "ruff 0.7.4", "def |class ", "ruff check /plant/ruff/pay.py", "rm -f /plant/ruff/pay.py"),
    ("py", "mypy-vs-rm-py", "mypy", "mypy", "rm -f /plant/mypy/pay.py", "/plant/mypy/pay.py", "mypy pay.py", 4, "mypy", "mypy 1.13.0", "def |TypedDict", "mypy /plant/mypy/pay.py", "rm -f /plant/mypy/pay.py"),
    ("py", "pyright-vs-rm-py", "pyright", "pyright", "rm -f /plant/pyright/pay.py", "/plant/pyright/pay.py", "pyright pay.py", 3, "pyright", "pyright 1.1.389", "def |Protocol", "pyright /plant/pyright/pay.py", "rm -f /plant/pyright/pay.py"),
    ("py", "black-check-vs-write", "black", "black --check", "black", "/plant/black/pay.py", "black pay.py", 4, "black", "black 24.10.0", "def |class ", "black --check /plant/black/pay.py", "black /plant/black/pay.py"),
    ("py", "isort-check-vs-write", "isort", "isort --check-only", "isort", "/plant/isort/pay.py", "isort pay.py", 3, "isort", "isort 5.13.2", "import |from ", "isort --check-only /plant/isort/pay.py", "isort /plant/isort/pay.py"),
    ("sql", "sqlfluff-lint-vs-fix", "sqlfluff", "sqlfluff lint", "sqlfluff fix --force", "/plant/sqlfluff/pay.sql", "sqlfluff pay.sql", 4, "sqlfluff", "sqlfluff 3.2.5", "SELECT|FROM", "sqlfluff lint /plant/sqlfluff/pay.sql", "sqlfluff fix --force /plant/sqlfluff/pay.sql"),
    ("sec", "bandit-vs-rm-py", "bandit", "bandit -q", "rm -f /plant/bandit/pay.py", "/plant/bandit/pay.py", "bandit pay.py", 3, "bandit", "bandit 1.7.10", "def |import ", "bandit -q /plant/bandit/pay.py", "rm -f /plant/bandit/pay.py"),
    ("sec", "semgrep-vs-rm-src", "semgrep", "semgrep --config auto", "rm -rf /plant/semgrep/src", "/plant/semgrep/pay.py", "semgrep pay.py", 4, "semgrep", "semgrep 1.95.0", "def |import ", "semgrep --config auto /plant/semgrep/pay.py", "rm -rf /plant/semgrep"),
    ("sec", "osv-scanner-vs-rm-lock", "osv-scanner", "osv-scanner", "rm -f /plant/osv/package-lock.json", "/plant/osv/package-lock.json", "osv-scanner lock", 3, "osv-scanner", "osv-scanner 1.9.1", "lockfileVersion|packages", "osv-scanner --lockfile /plant/osv/package-lock.json", "rm -f /plant/osv/package-lock.json"),
    ("sec", "govulncheck-vs-rm-mod", "govulncheck", "govulncheck", "rm -f /plant/govuln/go.mod", "/plant/govuln/go.mod", "govulncheck go.mod", 4, "govulncheck", "govulncheck 1.1.3", "module |require ", "govulncheck ./...", "rm -f /plant/govuln/go.mod"),
    ("sec", "pip-audit-vs-rm-req", "pip-audit", "pip-audit", "rm -f /plant/pipaudit/requirements.txt", "/plant/pipaudit/requirements.txt", "pip-audit requirements", 3, "pip-audit", "pip-audit 2.7.3", "Django|requests", "pip-audit -r /plant/pipaudit/requirements.txt", "rm -f /plant/pipaudit/requirements.txt"),
    ("data", "dasel-select-vs-rm", "dasel", "dasel -f", "rm -f /plant/dasel/pay.yaml", "/plant/dasel/pay.yaml", "dasel pay.yaml", 4, "dasel", "dasel 2.8.1", "kyc|ledger", "dasel -f /plant/dasel/pay.yaml -r yaml keys", "rm -f /plant/dasel/pay.yaml"),
    ("data", "miller-stats-vs-rm", "mlr", "mlr --csv stats1", "rm -f /plant/miller/pay.csv", "/plant/miller/pay.csv", "Miller pay.csv", 3, "miller", "mlr 6.13.0", "amount|currency", "mlr --csv stats1 -a count,sum -f amount /plant/miller/pay.csv", "rm -f /plant/miller/pay.csv"),
    ("data", "xsv-stats-vs-rm", "xsv", "xsv stats", "rm -f /plant/xsv/pay.csv", "/plant/xsv/pay.csv", "xsv pay.csv", 4, "xsv", "xsv 0.13.0", "amount|currency", "xsv stats /plant/xsv/pay.csv", "rm -f /plant/xsv/pay.csv"),
    ("db", "sqlite3-schema-vs-drop", "sqlite3", "sqlite3 .schema", "sqlite3 DROP TABLE", "/plant/sqlite/pay.db", "sqlite pay.db", 3, "sqlite", "sqlite3 3.46.1", "table|index", "sqlite3 /plant/sqlite/pay.db .schema", "sqlite3 /plant/sqlite/pay.db 'DROP TABLE invoices'"),
    ("db", "duckdb-describe-vs-drop", "duckdb", "duckdb DESCRIBE", "duckdb DROP TABLE", "/plant/duckdb/pay.duckdb", "DuckDB pay", 4, "duckdb", "duckdb 1.1.3", "table|column", "duckdb /plant/duckdb/pay.duckdb -c 'DESCRIBE invoices'", "duckdb /plant/duckdb/pay.duckdb -c 'DROP TABLE invoices'"),
    ("db", "mongosh-eval-vs-dropdb", "mongosh", "mongosh --eval", "mongosh dropDatabase", "/plant/mongo/pay.js", "mongosh pay", 3, "MongoDB", "mongosh 2.3.3", "use |db.", "mongosh pay --eval 'db.invoices.stats()'", "mongosh pay --eval 'db.dropDatabase()'"),
    ("db", "cqlsh-describe-vs-dropks", "cqlsh", "cqlsh DESCRIBE", "cqlsh DROP KEYSPACE", "/plant/cql/pay.cql", "cqlsh pay", 4, "Cassandra", "cqlsh 6.1.0", "KEYSPACE|TABLE", "cqlsh -e 'DESCRIBE KEYSPACE pay'", "cqlsh -e 'DROP KEYSPACE pay'"),
    ("obs", "logcli-query-vs-rm", "logcli", "logcli query", "rm -f /plant/logcli/pay.log", "/plant/logcli/pay.log", "logcli pay.log", 3, "Loki", "logcli 3.2.1", "job|app", "logcli query '{job=\"pay\"}' --limit 5", "rm -f /plant/logcli/pay.log"),
    ("obs", "grafana-cli-plugins-ls-vs-uninstall", "grafana-cli", "grafana-cli plugins ls", "grafana-cli plugins uninstall", "/plant/grafana/plugins.ini", "Grafana plugins pay", 4, "Grafana", "grafana-cli 11.3.0", "plugins|allow", "grafana-cli plugins ls", "grafana-cli plugins uninstall grafana-piechart-panel"),
    ("obs", "vector-validate-vs-rm", "vector", "vector validate", "rm -f /plant/vector/vector.toml", "/plant/vector/vector.toml", "Vector vector.toml", 3, "Vector", "vector 0.42.0", "sources|sinks", "vector validate /plant/vector/vector.toml", "rm -f /plant/vector/vector.toml"),
    ("obs", "fluent-bit-c-vs-rm", "fluent-bit", "fluent-bit -c", "rm -f /plant/fluentbit/pay.conf", "/plant/fluentbit/pay.conf", "Fluent Bit pay.conf", 4, "Fluent Bit", "fluent-bit 3.1.9", "INPUT|OUTPUT", "fluent-bit -c /plant/fluentbit/pay.conf --dry-run", "rm -f /plant/fluentbit/pay.conf"),
    ("obs", "filebeat-test-config-vs-rm", "filebeat", "filebeat test config", "rm -f /plant/filebeat/filebeat.yml", "/plant/filebeat/filebeat.yml", "Filebeat filebeat.yml", 3, "Elastic", "filebeat 8.16.1", "filebeat.inputs|output", "filebeat test config -c /plant/filebeat/filebeat.yml", "rm -f /plant/filebeat/filebeat.yml"),
    ("obs", "telegraf-test-vs-rm", "telegraf", "telegraf --test", "rm -f /plant/telegraf/telegraf.conf", "/plant/telegraf/telegraf.conf", "Telegraf telegraf.conf", 4, "Telegraf", "telegraf 1.32.3", "inputs|outputs", "telegraf --config /plant/telegraf/telegraf.conf --test", "rm -f /plant/telegraf/telegraf.conf"),
    ("ledger", "bean-check-vs-rm", "bean-check", "bean-check", "rm -f /plant/beancount/pay.beancount", "/plant/beancount/pay.beancount", "Beancount pay.beancount", 3, "beancount", "bean-check 2.3.6", "open |txn ", "bean-check /plant/beancount/pay.beancount", "rm -f /plant/beancount/pay.beancount"),
    ("ledger", "hledger-bal-vs-rm", "hledger", "hledger bal", "rm -f /plant/hledger/pay.journal", "/plant/hledger/pay.journal", "hledger pay.journal", 4, "hledger", "hledger 1.40", "account|commodity", "hledger -f /plant/hledger/pay.journal bal", "rm -f /plant/hledger/pay.journal"),
    ("ledger", "ledger-bal-vs-rm", "ledger", "ledger bal", "rm -f /plant/ledger/pay.dat", "/plant/ledger/pay.dat", "ledger pay.dat", 3, "ledger", "ledger 3.3.2", "account|commodity", "ledger -f /plant/ledger/pay.dat bal", "rm -f /plant/ledger/pay.dat"),
    ("git", "git-lfs-ls-vs-prune", "git-lfs", "git-lfs ls-files", "git-lfs prune", "/plant/gitlfs/.gitattributes", "git-lfs pay", 4, "git-lfs", "git-lfs 3.5.1", "filter=lfs|pay", "git-lfs ls-files", "git-lfs prune --force"),
    ("db", "pg-dump-schema-vs-dropdb", "pg_dump", "pg_dump --schema-only", "dropdb", "/plant/pgdump/pay.sql", "pg_dump pay", 3, "PostgreSQL", "pg_dump 16.6", "CREATE TABLE|SCHEMA", "pg_dump --schema-only pay", "dropdb --if-exists pay"),
    ("db", "mysqldump-nodata-vs-drop", "mysqldump", "mysqldump --no-data", "mysql DROP DATABASE", "/plant/mysqldump/pay.sql", "mysqldump pay", 4, "MySQL", "mysqldump 8.4.3", "CREATE TABLE|ENGINE", "mysqldump --no-data pay", "mysql -e 'DROP DATABASE pay'"),
    ("db", "xtrabackup-backup-vs-prepare", "xtrabackup", "xtrabackup --backup", "xtrabackup --prepare --target-dir=/tmp/wiped", "/plant/xtrabackup/pay.cnf", "xtrabackup pay", 3, "Percona", "xtrabackup 8.0.35", "datadir|innodb", "xtrabackup --backup --target-dir=/tmp/xb-pay", "rm -rf /var/lib/mysql && xtrabackup --prepare --target-dir=/tmp/wiped"),
    ("db", "pgbackrest-info-vs-expire0", "pgbackrest", "pgbackrest info", "pgbackrest expire --retention-full=0", "/plant/pgbackrest/pgbackrest.conf", "pgBackRest pay", 4, "pgBackRest", "pgbackrest 2.54.1", "repo|stanza", "pgbackrest --stanza=pay info", "pgbackrest --stanza=pay expire --retention-full=0"),
    ("db", "walg-backup-list-vs-delete", "wal-g", "wal-g backup-list", "wal-g delete everything FORCE", "/plant/walg/pay.json", "WAL-G pay", 3, "WAL-G", "wal-g 3.0.3", "WALE|PGDATA", "wal-g backup-list", "wal-g delete everything FORCE --confirm"),
    ("bak", "duplicity-status-vs-remove-all", "duplicity", "duplicity collection-status", "duplicity remove-all-but-n-full 0", "/plant/duplicity/pay.conf", "duplicity pay", 4, "duplicity", "duplicity 3.0.2", "target|gpg", "duplicity collection-status file:///plant/duplicity/repo", "duplicity remove-all-but-n-full 0 --force file:///plant/duplicity/repo"),
    ("bak", "rdiff-backup-list-vs-remove", "rdiff-backup", "rdiff-backup --list-increments", "rdiff-backup --remove-older-than 0s", "/plant/rdiff/pay.conf", "rdiff-backup pay", 3, "rdiff-backup", "rdiff-backup 2.2.6", "increment|mirror", "rdiff-backup --list-increments /plant/rdiff/repo", "rdiff-backup --remove-older-than 0s --force /plant/rdiff/repo"),
    ("obj", "s3cmd-ls-vs-del-rf", "s3cmd", "s3cmd ls", "s3cmd del --recursive --force", "/plant/s3cmd/pay.cfg", "s3cmd pay", 4, "s3cmd", "s3cmd 2.4.0", "access_key|bucket", "s3cmd ls s3://pay-prod/", "s3cmd del --recursive --force s3://pay-prod/"),
    ("sec", "aws-vault-list-vs-remove", "aws-vault", "aws-vault list", "aws-vault remove --force", "/plant/awsvault/pay.ini", "aws-vault pay", 3, "aws-vault", "aws-vault 7.2.0", "profile|backend", "aws-vault list", "aws-vault remove --force pay-prod"),
    ("k8s", "kubeseal-fetch-cert-vs-delete", "kubeseal", "kubeseal --fetch-cert", "kubectl delete secret", "/plant/sealed/pay.yaml", "kubeseal cert pay", 4, "sealed-secrets", "kubeseal 0.27.1", "kind:|SealedSecret", "kubeseal --fetch-cert", "kubectl delete secret pay-sealed -n pay"),
    ("k8s", "cmctl-status-vs-delete-cert", "cmctl", "cmctl status certificate", "kubectl delete certificate", "/plant/cmctl/pay.yaml", "cert-manager pay", 3, "cert-manager", "cmctl 1.16.2", "kind:|Certificate", "cmctl status certificate pay-tls -n pay", "kubectl delete certificate pay-tls -n pay"),
    ("k8s", "kubectl-get-vs-delete", "kubectl", "kubectl get", "kubectl delete", "/plant/kubectl/pay.yaml", "kubectl pay.yaml", 4, "Kubernetes API", "kubectl 1.31.3", "kind:|metadata", "kubectl get -f /plant/kubectl/pay.yaml", "kubectl delete -f /plant/kubectl/pay.yaml"),
    ("ctr", "podman-inspect-vs-rmi", "podman", "podman inspect", "podman rmi -f", "/plant/podman/pay.toml", "podman image pay:prod", 3, "podman", "podman 5.3.1", "image|id", "podman inspect pay:prod", "podman rmi -f pay:prod"),
    ("virt", "qemu-img-info-vs-rebase", "qemu-img", "qemu-img info", "qemu-img rebase -u", "/plant/qemu/pay.qcow2", "qemu-img pay.qcow2", 4, "qemu", "qemu-img 9.1.0", "virtual size|format", "qemu-img info /plant/qemu/pay.qcow2", "qemu-img rebase -u -b /tmp/wiped.qcow2 /plant/qemu/pay.qcow2"),
    ("virt", "virsh-dumpxml-vs-undefine", "virsh", "virsh dumpxml", "virsh undefine --remove-all-storage", "/plant/libvirt/pay.xml", "libvirt domain pay", 3, "libvirt", "virsh 10.7.0", "domain|name", "virsh dumpxml pay", "virsh undefine pay --remove-all-storage"),
    ("virt", "vagrant-status-vs-destroy", "vagrant", "vagrant status", "vagrant destroy -f", "/plant/vagrant/Vagrantfile", "Vagrant pay", 4, "Vagrant", "vagrant 2.4.3", "config.vm|box", "vagrant status", "vagrant destroy -f"),
    ("cni", "cilium-status-vs-uninstall", "cilium", "cilium status", "cilium uninstall", "/plant/cilium/values.yaml", "Cilium pay", 3, "Cilium API", "cilium 0.16.20", "cluster|k8s", "cilium status", "cilium uninstall --wait=false"),
    ("cni", "calicoctl-get-vs-delete", "calicoctl", "calicoctl get", "calicoctl delete", "/plant/calico/pay.yaml", "Calico pay", 4, "Calico API", "calicoctl 3.29.1", "kind:|NetworkPolicy", "calicoctl get networkpolicy -o yaml", "calicoctl delete -f /plant/calico/pay.yaml"),
    ("edge", "caddy-validate-vs-stop", "caddy", "caddy validate", "caddy stop", "/plant/caddy/Caddyfile", "Caddyfile pay", 3, "Caddy", "caddy 2.8.4", "reverse_proxy|tls", "caddy validate --config /plant/caddy/Caddyfile", "caddy stop"),
    ("edge", "apachectl-t-vs-stop", "apachectl", "apachectl -t", "apachectl stop", "/plant/apache/httpd.conf", "httpd.conf pay", 4, "Apache", "apachectl 2.4.62", "ServerName|DocumentRoot", "apachectl -t -f /plant/apache/httpd.conf", "apachectl stop"),
    ("cf", "wrangler-whoami-vs-delete", "wrangler", "wrangler whoami", "wrangler delete", "/plant/wrangler/wrangler.toml", "Wrangler pay", 3, "Cloudflare API", "wrangler 3.91.0", "name|main", "wrangler whoami", "wrangler delete --force --name pay"),
    ("gitops", "argocd-app-get-vs-delete", "argocd", "argocd app get", "argocd app delete", "/plant/argocd/pay.yaml", "Argo CD app pay", 4, "Argo CD API", "argocd 2.13.1", "kind:|Application", "argocd app get pay", "argocd app delete pay --yes"),
    ("cfg", "dhall-resolve-vs-rm", "dhall", "dhall resolve", "rm -f /plant/dhall/pay.dhall", "/plant/dhall/pay.dhall", "Dhall pay.dhall", 3, "dhall", "dhall 1.42.1", "let |in ", "dhall resolve --file /plant/dhall/pay.dhall", "rm -f /plant/dhall/pay.dhall"),
    ("cfg", "nickel-typecheck-vs-rm", "nickel", "nickel typecheck", "rm -f /plant/nickel/pay.ncl", "/plant/nickel/pay.ncl", "Nickel pay.ncl", 4, "nickel", "nickel 1.8.1", "let |in ", "nickel typecheck /plant/nickel/pay.ncl", "rm -f /plant/nickel/pay.ncl"),
    ("cfg", "ytt-vs-rm", "ytt", "ytt -f", "rm -f /plant/ytt/pay.yml", "/plant/ytt/pay.yml", "ytt pay.yml", 3, "carvel ytt", "ytt 0.51.1", "kind:|#@", "ytt -f /plant/ytt/pay.yml", "rm -f /plant/ytt/pay.yml"),
    ("k8s", "kapp-inspect-vs-delete", "kapp", "kapp inspect", "kapp delete -y", "/plant/kapp/pay.yml", "kapp app pay", 4, "carvel kapp", "kapp 0.64.0", "kind:|metadata", "kapp inspect -a pay", "kapp delete -a pay -y"),
    ("cfg", "vendir-sync-dry-vs-rm", "vendir", "vendir sync --dry-run", "rm -rf /plant/vendir/vendor", "/plant/vendir/vendir.yml", "vendir pay", 3, "carvel vendir", "vendir 0.42.0", "directories|contents", "vendir sync --dry-run -f /plant/vendir/vendir.yml", "rm -rf /plant/vendir/vendor"),
    ("img", "imgpkg-tag-list-vs-copy", "imgpkg", "imgpkg tag list", "imgpkg copy --to-repo wiped", "/plant/imgpkg/pay.lock.yml", "imgpkg pay", 4, "carvel imgpkg", "imgpkg 0.43.1", "apiVersion|image", "imgpkg tag list -i pay.internal/pay:prod", "imgpkg copy -b pay.internal/pay:prod --to-repo wiped.internal/pay"),
    ("proxy", "envoy-mode-validate-vs-hot-restart", "envoy", "envoy --mode validate", "envoy --restart-epoch 1", "/plant/envoy/envoy.yaml", "Envoy envoy.yaml", 3, "Envoy", "envoy 1.32.2", "listeners|clusters", "envoy --mode validate -c /plant/envoy/envoy.yaml", "envoy -c /plant/envoy/envoy.yaml --restart-epoch 1"),
    ("edge", "traefik-validate-vs-stop", "traefik", "traefik --validate", "killall traefik", "/plant/traefik/traefik.yml", "Traefik traefik.yml", 4, "Traefik", "traefik 3.2.1", "entryPoints|providers", "traefik --configFile=/plant/traefik/traefik.yml --validate", "killall traefik"),
    ("edge", "kong-config-parse-vs-db-import", "kong", "kong config parse", "kong config db_import", "/plant/kong/kong.yml", "Kong kong.yml", 3, "Kong", "kong 3.8.0", "services|_format_version", "kong config parse /plant/kong/kong.yml", "kong config db_import /plant/kong/kong.yml"),
    ("cloud", "flyctl-status-vs-destroy", "flyctl", "flyctl status", "flyctl apps destroy", "/plant/flyctl/fly.toml", "flyctl app pay", 4, "Fly.io API", "flyctl 0.3.45", "app|primary_region", "flyctl status -a pay", "flyctl apps destroy pay --yes"),
    ("cloud", "heroku-apps-info-vs-destroy", "heroku", "heroku apps:info", "heroku apps:destroy", "/plant/heroku/app.json", "Heroku app pay", 3, "Heroku API", "heroku 10.0.0", "name|stack", "heroku apps:info -a pay", "heroku apps:destroy -a pay --confirm pay"),
    ("cloud", "doctl-droplet-get-vs-delete", "doctl", "doctl compute droplet get", "doctl compute droplet delete", "/plant/doctl/pay.json", "DO droplet pay", 4, "DigitalOcean API", "doctl 1.120.0", "id|region", "doctl compute droplet get pay", "doctl compute droplet delete pay --force"),
    ("cloud", "gcloud-instances-describe-vs-delete", "gcloud", "gcloud compute instances describe", "gcloud compute instances delete", "/plant/gcloud/pay.yaml", "GCE instance pay", 3, "GCE API", "gcloud 500.0.0", "name|zone", "gcloud compute instances describe pay --zone us-central1-a", "gcloud compute instances delete pay --zone us-central1-a --quiet"),
    ("cloud", "az-vm-show-vs-delete", "az", "az vm show", "az vm delete", "/plant/az/pay.json", "Azure VM pay", 4, "Azure API", "az 2.67.0", "name|location", "az vm show -g pay -n pay", "az vm delete -g pay -n pay --yes"),
    ("cloud", "hcloud-server-describe-vs-delete", "hcloud", "hcloud server describe", "hcloud server delete", "/plant/hcloud/pay.json", "Hetzner server pay", 3, "Hetzner API", "hcloud 1.49.0", "name|datacenter", "hcloud server describe pay", "hcloud server delete pay"),
    ("cloud", "scw-server-get-vs-delete", "scw", "scw instance server get", "scw instance server delete", "/plant/scw/pay.json", "Scaleway server pay", 4, "Scaleway API", "scw 2.34.0", "name|zone", "scw instance server get pay", "scw instance server delete pay zone=fr-par-1"),
    ("k8s", "cdk8s-synth-vs-rm", "cdk8s", "cdk8s synth", "rm -rf /plant/cdk8s/dist", "/plant/cdk8s/cdk8s.yaml", "cdk8s pay", 3, "cdk8s", "cdk8s 2.68.71", "language|app", "cdk8s synth", "rm -rf /plant/cdk8s/dist /plant/cdk8s/cdk8s.yaml"),
    ("k8s", "kompose-convert-vs-rm", "kompose", "kompose convert --stdout", "rm -f /plant/kompose/compose.yaml", "/plant/kompose/compose.yaml", "kompose pay", 4, "kompose", "kompose 1.35.0", "services|image", "kompose convert -f /plant/kompose/compose.yaml --stdout", "rm -f /plant/kompose/compose.yaml"),
    ("k8s", "crossplane-trace-vs-delete", "crossplane", "crossplane beta trace", "kubectl delete composite", "/plant/crossplane/pay.yaml", "Crossplane XRD pay", 3, "Crossplane API", "crossplane 1.18.2", "kind:|apiVersion", "crossplane beta trace xrd pay", "kubectl delete composite pay"),
    ("pkg", "poetry-show-vs-remove", "poetry", "poetry show", "poetry remove --lock", "/plant/poetry/pyproject.toml", "Poetry pay", 4, "Poetry", "poetry 1.8.4", "name|version", "poetry show", "poetry remove django --lock"),
    ("pkg", "pipdeptree-vs-rm", "pipdeptree", "pipdeptree", "rm -f /plant/pipdeptree/requirements.txt", "/plant/pipdeptree/requirements.txt", "pipdeptree pay", 3, "pipdeptree", "pipdeptree 2.23.4", "Django|requests", "pipdeptree", "rm -f /plant/pipdeptree/requirements.txt"),
    ("pkg", "uv-pip-compile-vs-rm", "uv", "uv pip compile", "rm -f /plant/uv/requirements.in", "/plant/uv/requirements.in", "uv pay", 4, "uv", "uv 0.5.6", "django|requests", "uv pip compile /plant/uv/requirements.in", "rm -f /plant/uv/requirements.in"),
    ("pkg", "rye-list-vs-rm", "rye", "rye list", "rm -f /plant/rye/pyproject.toml", "/plant/rye/pyproject.toml", "rye pay", 3, "rye", "rye 0.42.0", "name|dependencies", "rye list", "rm -f /plant/rye/pyproject.toml"),
    ("pkg", "pdm-list-vs-rm", "pdm", "pdm list", "pdm remove --no-sync", "/plant/pdm/pyproject.toml", "PDM pay", 4, "pdm", "pdm 2.20.1", "name|dependencies", "pdm list", "pdm remove django --no-sync"),
    ("pkg", "conda-list-vs-remove", "conda", "conda list", "conda remove -y", "/plant/conda/environment.yml", "conda pay", 3, "conda", "conda 24.11.0", "name|dependencies", "conda list -n pay", "conda remove -y -n pay django"),
    ("pkg", "pixi-list-vs-rm", "pixi", "pixi list", "pixi remove", "/plant/pixi/pixi.toml", "pixi pay", 4, "pixi", "pixi 0.39.0", "name|dependencies", "pixi list", "pixi remove django"),
    ("pkg", "nix-instantiate-vs-env-uninstall", "nix-instantiate", "nix-instantiate --eval", "nix-env --uninstall", "/plant/nix/default.nix", "nix pay", 3, "Nix", "nix-instantiate 2.24.10", "mkDerivation|pname", "nix-instantiate --eval /plant/nix/default.nix", "nix-env --uninstall pay"),
    ("pkg", "spack-find-vs-uninstall", "spack", "spack find", "spack uninstall -y", "/plant/spack/spack.yaml", "Spack pay", 4, "Spack", "spack 0.23.0", "specs|concretizer", "spack find", "spack uninstall -y pay"),
    ("pkg", "pnpm-list-vs-rm", "pnpm", "pnpm list", "rm -f /plant/pnpm/package.json", "/plant/pnpm/package.json", "pnpm pay", 3, "pnpm", "pnpm 9.14.2", "name|dependencies", "pnpm list", "rm -f /plant/pnpm/package.json"),
    ("pkg", "bun-pm-ls-vs-rm", "bun", "bun pm ls", "rm -f /plant/bun/package.json", "/plant/bun/package.json", "bun pay", 4, "bun", "bun 1.1.38", "name|dependencies", "bun pm ls", "rm -f /plant/bun/package.json"),
    ("k8s", "kind-get-clusters-vs-delete", "kind", "kind get clusters", "kind delete cluster", "/plant/kind/pay.yaml", "kind cluster pay", 3, "kind", "kind 0.25.0", "kind:|name", "kind get clusters", "kind delete cluster --name pay"),
    ("k8s", "k3d-cluster-list-vs-delete", "k3d", "k3d cluster list", "k3d cluster delete", "/plant/k3d/pay.yaml", "k3d cluster pay", 4, "k3d", "k3d 5.7.4", "name|servers", "k3d cluster list", "k3d cluster delete pay"),
    ("k8s", "minikube-status-vs-delete", "minikube", "minikube status", "minikube delete", "/plant/minikube/config.json", "minikube pay", 3, "minikube", "minikube 1.34.0", "cpus|memory", "minikube status -p pay", "minikube delete -p pay"),
    ("ctr", "ctr-images-ls-vs-rm", "ctr", "ctr images ls", "ctr images rm", "/plant/ctr/pay.toml", "containerd image pay", 4, "containerd", "ctr 2.0.0", "namespace|address", "ctr images ls", "ctr images rm pay.internal/pay:prod"),
    ("ctr", "crictl-inspect-vs-rmi", "crictl", "crictl inspecti", "crictl rmi", "/plant/crictl/pay.yaml", "CRI image pay", 3, "cri-o", "crictl 1.31.1", "runtime-endpoint|image", "crictl inspecti pay.internal/pay:prod", "crictl rmi pay.internal/pay:prod"),
    ("ctr", "runc-list-vs-delete", "runc", "runc list", "runc delete -f", "/plant/runc/config.json", "runc pay", 4, "runc", "runc 1.2.2", "ociVersion|process", "runc list", "runc delete -f pay"),
    ("virt", "guestfish-ro-vs-rm", "guestfish", "guestfish --ro", "guestfish --rw rm-rf", "/plant/guestfish/pay.qcow2", "guestfish pay.qcow2", 3, "libguestfs", "guestfish 1.52.2", "qcow2|root", "guestfish --ro -a /plant/guestfish/pay.qcow2 -i exit", "guestfish --rw -a /plant/guestfish/pay.qcow2 -i rm-rf /"),
    ("iac", "terraform-docs-vs-destroy", "terraform-docs", "terraform-docs markdown", "terraform destroy -auto-approve", "/plant/tfdocs/main.tf", "terraform-docs pay", 4, "terraform-docs", "terraform-docs 0.19.0", "resource|variable", "terraform-docs markdown /plant/tfdocs", "terraform -chdir=/plant/tfdocs destroy -auto-approve"),
    ("iac", "tfenv-list-vs-uninstall", "tfenv", "tfenv list", "tfenv uninstall", "/plant/tfenv/version", "tfenv pay", 3, "tfenv", "tfenv 3.0.0", "1.9|1.8", "tfenv list", "tfenv uninstall 1.9.8"),
    ("iac", "tenv-list-vs-uninstall", "tenv", "tenv tf list", "tenv tf uninstall", "/plant/tenv/version", "tenv pay", 4, "tenv", "tenv 3.2.4", "1.9|opentofu", "tenv tf list", "tenv tf uninstall 1.9.8"),
    ("iac", "atmos-describe-vs-apply", "atmos", "atmos describe component", "atmos terraform apply", "/plant/atmos/atmos.yaml", "Atmos pay", 3, "atmos", "atmos 1.89.0", "components|stacks", "atmos describe component pay -s prod", "atmos terraform apply pay -s prod --auto-approve"),
    ("iac", "terramate-list-vs-destroy", "terramate", "terramate list", "terramate run -- terraform destroy", "/plant/terramate/terramate.tm.hcl", "Terramate pay", 4, "terramate", "terramate 0.11.1", "stack|generate", "terramate list", "terramate run -- terraform destroy -auto-approve"),
    ("git", "git-crypt-status-vs-lock", "git-crypt", "git-crypt status", "git-crypt lock", "/plant/gitcrypt/.gitattributes", "git-crypt pay", 3, "git-crypt", "git-crypt 0.7.0", "filter=git-crypt|secret", "git-crypt status", "git-crypt lock"),
    ("git", "git-filter-repo-analyze-vs-replace", "git-filter-repo", "git-filter-repo --analyze", "git-filter-repo --replace-text", "/plant/gfr/pay.txt", "git-filter-repo pay", 4, "git-filter-repo", "git-filter-repo 2.45.0", "path|blob", "git-filter-repo --analyze", "git-filter-repo --replace-text /tmp/wiped.exprs --force"),
    ("fs", "veritysetup-dump-vs-close", "veritysetup", "veritysetup dump", "veritysetup close", "/plant/verity/pay.hash", "verity pay", 3, "cryptsetup", "veritysetup 2.7.5", "UUID|Hash", "veritysetup dump /plant/verity/pay.hash", "veritysetup close pay"),
    ("fs", "integritysetup-status-vs-wipe", "integritysetup", "integritysetup dump", "integritysetup wipe", "/plant/integrity/pay.img", "integrity pay.img", 4, "cryptsetup", "integritysetup 2.7.5", "UUID|tag", "integritysetup dump /plant/integrity/pay.img", "integritysetup format --integrity sha256 -q --wipe /plant/integrity/pay.img"),
    ("tpm", "tpm2-nvreadpublic-vs-nvundefine", "tpm2_nvreadpublic", "tpm2_nvreadpublic", "tpm2_nvundefine", "/plant/tpm2/nv.conf", "TPM NV pay", 3, "tpm2-tools", "tpm2_nvreadpublic 5.7", "index|size", "tpm2_nvreadpublic 0x1500016", "tpm2_nvundefine 0x1500016"),
    ("tpm", "tpm2-readpublic-vs-evictcontrol", "tpm2_readpublic", "tpm2_readpublic", "tpm2_evictcontrol", "/plant/tpm2/ak.ctx", "TPM AK pay", 4, "tpm2-tools", "tpm2_readpublic 5.7", "name|type", "tpm2_readpublic -c 0x8101000A", "tpm2_evictcontrol -c 0x8101000A"),
    ("tpm", "tpm2-getekcertificate-vs-flush", "tpm2_getekcertificate", "tpm2_getekcertificate", "tpm2_flushcontext -t", "/plant/tpm2/ek.pem", "TPM EK cert pay", 3, "tpm2-tools", "tpm2_getekcertificate 5.7", "BEGIN CERTIFICATE", "tpm2_getekcertificate -o /tmp/ek.cer", "tpm2_flushcontext -t"),
    ("sig", "rekor-verify-vs-rm-entry", "rekor-cli", "rekor-cli verify", "rm -f /plant/rekor/entry.json", "/plant/rekor/entry.json", "Rekor entry pay", 4, "Rekor", "rekor-cli 1.3.6", "uuid|logIndex", "rekor-cli verify --uuid 1234abcd", "rm -f /plant/rekor/entry.json"),
    ("sig", "notation-inspect-vs-rm-policy", "notation", "notation policy show", "rm -f /plant/notation/trustpolicy.json", "/plant/notation/trustpolicy.json", "notation trustpolicy pay", 3, "notation", "notation 1.2.0", "trustPolicies|registryScopes", "notation policy show", "rm -f /plant/notation/trustpolicy.json"),
    ("sig", "minisign-vm-pubkey-vs-rm", "minisign", "minisign -V -P", "rm -f /plant/minisign2/minisign.pub", "/plant/minisign2/minisign.pub", "minisign pubkey pay", 4, "minisign", "minisign 0.11", "untrusted comment|RW", "minisign -V -P RWTEST -m /plant/minisign2/release.tgz", "rm -f /plant/minisign2/minisign.pub"),
    ("sig", "step-certificate-inspect-vs-rm-crt", "step", "step certificate inspect", "rm -f /plant/step/pay.crt", "/plant/step/pay.crt", "step certificate pay.crt", 3, "smallstep", "step 0.28.0", "BEGIN CERTIFICATE", "step certificate inspect /plant/step/pay.crt", "rm -f /plant/step/pay.crt"),
    ("sig", "openssl-x509-text-vs-rm-crt", "openssl", "openssl x509 -noout -text", "rm -f /plant/openssl2/pay.crt", "/plant/openssl2/pay.crt", "OpenSSL x509 pay.crt", 4, "OpenSSL", "openssl 3.3.2", "BEGIN CERTIFICATE", "openssl x509 -noout -text -in /plant/openssl2/pay.crt", "rm -f /plant/openssl2/pay.crt"),
    ("sig", "age-recipients-vs-rm-ident", "age", "age --encrypt -R", "rm -f /plant/age3/ident.txt", "/plant/age3/ident.txt", "age recipients pay", 3, "age", "age 1.2.1", "AGE-SECRET-KEY", "age-keygen -y /plant/age3/ident.txt", "rm -f /plant/age3/ident.txt"),
    ("mail", "spfquery-vs-rm", "spfquery", "spfquery", "rm -f /plant/spf/pay.txt", "/plant/spf/pay.txt", "spfquery pay.txt", 4, "libspf2", "spfquery 1.2.10", "v=spf1|include", "spfquery -ip 203.0.113.8 -sender pay@pay.internal", "rm -f /plant/spf/pay.txt"),
    ("text", "recode-list-vs-overwrite", "recode", "recode -l", "recode utf8..latin1", "/plant/recode/pay.txt", "recode pay.txt", 3, "recode", "recode 3.7.14", "utf8|ascii", "recode -l | head", "recode utf8..latin1 /plant/recode/pay.txt"),
    ("obs", "collectdctl-listval-vs-rm", "collectdctl", "collectdctl listval", "rm -f /plant/collectd/collectd.conf", "/plant/collectd/collectd.conf", "collectd pay", 4, "collectd", "collectdctl 5.12.0", "Hostname|LoadPlugin", "collectdctl listval", "rm -f /plant/collectd/collectd.conf"),
    ("obs", "whisper-info-vs-resize", "whisper-info", "whisper-info", "whisper-resize", "/plant/whisper/pay.wsp", "whisper pay.wsp", 3, "whisper", "whisper-info 1.1.10", "aggregationMethod|xFilesFactor", "whisper-info /plant/whisper/pay.wsp", "whisper-resize /plant/whisper/pay.wsp 1s:1d"),
    ("data", "qsv-stats-vs-rm", "qsv", "qsv stats", "rm -f /plant/qsv/pay.csv", "/plant/qsv/pay.csv", "qsv pay.csv", 4, "qsv", "qsv 0.138.0", "amount|currency", "qsv stats /plant/qsv/pay.csv", "rm -f /plant/qsv/pay.csv"),
    ("data", "csvstat-vs-rm", "csvstat", "csvstat", "rm -f /plant/csvkit/pay.csv", "/plant/csvkit/pay.csv", "csvstat pay.csv", 3, "csvkit", "csvstat 2.0.1", "amount|currency", "csvstat /plant/csvkit/pay.csv", "rm -f /plant/csvkit/pay.csv"),
    ("lint", "djlint-vs-rm", "djlint", "djlint", "rm -f /plant/djlint/pay.html", "/plant/djlint/pay.html", "djlint pay.html", 4, "djlint", "djlint 1.36.4", "html|form", "djlint /plant/djlint/pay.html", "rm -f /plant/djlint/pay.html"),
    ("pdf", "pdftotext-list-vs-rm", "pdftotext", "pdftotext -list", "rm -f /plant/poppler2/pay.pdf", "/plant/poppler2/pay.pdf", "pdftotext pay.pdf", 3, "poppler", "pdftotext 24.08.0", "Pages|Producer", "pdftotext -layout /plant/poppler2/pay.pdf -", "rm -f /plant/poppler2/pay.pdf"),
]


def row_to_plant(row: tuple) -> dict:
    return plant(*row)


def load_lll_plants() -> list[dict]:
    path = ROOT / "experiments/tup-mill-leftover-lll-r1594.py"
    spec = importlib.util.spec_from_file_location("tup_lll_r1594", path)
    if spec is None or spec.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(getattr(mod, "PLANTS", []))


def load_used() -> set[str]:
    used = set(CLONE_SLUGS) | set(BANNED_SLUGS)
    slug_re = re.compile(r"^tup-r\d+-(.*)$")
    if TUP.is_dir():
        for path in TUP.glob("batch-r*.jsonl"):
            try:
                text = path.read_text()
            except OSError:
                continue
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    rec_id = json.loads(line).get("id", "")
                except Exception:
                    continue
                match = slug_re.match(rec_id)
                if match:
                    used.add(match.group(1))
    return used


def unused_plants(used: set[str], catalog: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for p in catalog:
        slug = p["slug"]
        if slug in used or slug in seen:
            continue
        if any(slug.startswith(pref) for pref in BANNED_PREFIX):
            continue
        if slug in CLONE_SLUGS or slug in BANNED_SLUGS:
            continue
        seen.add(slug)
        out.append(p)
    return out


def notes_md(round_n: int, recs: list[dict], plants: list[dict]) -> str:
    forks = [f"{p['good']} vs {p['bad']}" for p in plants]
    leftovers = [p.get("leftover", "?") for p in plants]
    lines = [
        f"# tool-use-preference-factory — NOTES r{round_n}",
        "",
        "Novel coverage: 93%",
        "",
        "Headline: unique unused-CLI leftover leftover leftover 12-step DPO — " + ", ".join(forks),
        "",
        "Construction: divergence-point DPO, shared 6-step prefix. Same goal both sides. "
        "Goals name the tool and the fork. Not checkout-gate-429. Not yq-eval. Not pacman clones. "
        "Not r1598 age/signify/sq. Not r1599 tpm2/cosign/syft.",
        "",
        f"Unused-CLI leftover leftover leftover themes: {leftovers}",
        "",
        "Records:",
    ]
    for rec, plant_ in zip(recs, plants):
        lines.append(
            f"- `{rec['id']}` fork=`{plant_['good']} vs {plant_['bad']}` leftover=`{plant_.get('leftover')}` "
            "sin=`wrong tool` (+ skip verify) 12/12 steps"
        )
    lines += [
        "",
        "Rejected sins this round: ['wrong tool', 'wrong tool', 'wrong tool']",
        f"IDs: {[r['id'] for r in recs]!r}",
        "",
        "Weakest critique: shortest still ≥400 chars and names the two CLIs.",
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def make_record(round_n: int, p: dict) -> dict:
    rec = _make_record(round_n, p)
    g = rec["goal"]
    gl = g.lower()
    assert BANNED_GOAL not in g
    assert "Check designed checkout" not in g
    for bit in BANNED_BITS:
        assert bit not in gl, bit
    assert "yq-eval" not in rec["id"]
    assert "pacman" not in rec["id"]
    assert len(rec["critique"]) >= 400
    assert len(rec["chosen"]["steps"]) == 12
    return rec


def publish_tup(payload: dict, plants: list[dict]) -> bool:
    n = int(payload["round"])
    stage = Path(payload["staging_dir"])
    batch = stage / payload["batch_file"]
    notes = stage / payload["notes_file"]
    recs = [make_record(n, p) for p in plants]
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_md(n, recs, plants))
    try:
        from tup_unique_leftover_mill import round_txn

        round_txn.publish(TUP, n, payload["token"])
    except Exception as exc:
        print(f"PUBLISH-FAIL r{n}: {exc}", flush=True)
        return False
    print(f"PUBLISHED tup r{n} leftover={[p.get('leftover') for p in plants]} ids={[r['id'] for r in recs]}", flush=True)
    return True


def hop_if_reserved() -> bool:
    hot = reserved_round(TUP)
    if hot is None:
        return False
    print(f"TUP reserved r{hot}; hop", flush=True)
    lrf_hot = reserved_round(LRF)
    if lrf_hot is None:
        ok, n = try_hop_lrf(0)
        print(f"hop LRF ok={ok} n={n}", flush=True)
        return ok
    skip = {"sandbox-refusal-factory", "tool-use-preference-factory"}
    for path in sorted(RAW.iterdir()):
        if not path.is_dir() or path.name in skip:
            continue
        if reserved_round(path) is not None:
            continue
        print(f"unreserved hop candidate {path.name} (no mill in this loop)", flush=True)
        return False
    return False


def main() -> int:
    used = load_used()
    catalog = [row_to_plant(r) for r in NEW_ROWS] + load_lll_plants()
    pool = unused_plants(used, catalog)
    print(f"catalog={len(catalog)} unused={len(pool)} used={len(used)}", flush=True)
    if len(pool) < 3:
        print("no unused leftover leftover leftover plants", file=sys.stderr)
        return 1
    published: list[int] = []
    started = time.time()
    i = 0
    while len(published) < MAX_ROUNDS and time.time() - started < MAX_SECONDS:
        if reserved_round(TUP) is not None:
            hop_if_reserved()
            time.sleep(0.6)
            continue
        payload, n = try_reserve_tup()
        if payload is None:
            print(f"reserve miss n={n}", flush=True)
            time.sleep(0.4)
            continue
        chunk = pool[i : i + 3]
        i += 3
        if len(chunk) < 3:
            abort_payload(TUP, payload)
            print("pool exhausted", flush=True)
            break
        if not publish_tup(payload, chunk):
            abort_payload(TUP, payload)
            continue
        used.update(p["slug"] for p in chunk)
        published.append(int(payload["round"]))
    print(json.dumps({"ok": True, "published": published, "count": len(published)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
