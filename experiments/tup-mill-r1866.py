#!/usr/bin/env python3
"""TUP mill r1866+ unused-CLI inspect vs destroy. Unbounded loop.

NEW catalog after r1865. BAN r1865 findmnt-J-vs-umount / mdadm-examine-vs-stop /
pvs-vs-pvremove2, r1598 age-keygen-y-vs-rm / signify-verify-vs-rm-pub /
sq-inspect-vs-rm-cert, r1348 yq-eval*, pacman clones.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
RAW = ROOT / "outputs/raw/2026-08-19-agentic"
spec = importlib.util.spec_from_file_location("tup1600", ROOT / "experiments/tup-mill-r1600.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

plant = mod.plant
load_used = mod.load_used
unused_plants = mod.unused_plants
publish_tup = mod.publish_tup
try_reserve_tup = mod.try_reserve_tup
abort_payload = mod.abort_payload
reserved_round = mod.reserved_round
TUP = mod.TUP

MAX_ROUNDS = 10_000
MAX_SECONDS = 50_000

# leftover, slug, tool, good, bad, src429, ver, grep
# keep/resource/cmds filled in extra_plants()
SPECS: list[tuple[str, str, str, str, str, str, str, str]] = [
    ("ceph", "ceph-osd-tree-vs-out", "ceph", "ceph osd tree", "ceph osd out 0", "Ceph MON", "ceph 19.2.0", "osd|crush"),
    ("ceph", "ceph-mon-dump-vs-remove", "ceph", "ceph mon dump", "ceph mon remove pay", "Ceph MON", "ceph 19.2.0", "mon|rank"),
    ("ceph", "ceph-mgr-dump-vs-fail", "ceph", "ceph mgr dump", "ceph mgr fail pay", "Ceph MGR", "ceph 19.2.0", "mgr|active"),
    ("ceph", "ceph-fs-ls-vs-rm", "ceph", "ceph fs ls", "ceph fs rm pay --yes-i-really-mean-it", "CephFS", "ceph 19.2.0", "name|metadata"),
    ("ceph", "rados-lspools-vs-rmpool", "rados", "rados lspools", "rados rmpool pay pay --yes-i-really-really-mean-it", "RADOS", "rados 19.2.0", "pool|pg"),
    ("rbd", "rbd-ls-vs-rm", "rbd", "rbd ls", "rbd rm pay/data", "RBD", "rbd 19.2.0", "pool|image"),
    ("rbd", "rbd-status-vs-unmap", "rbd", "rbd status pay/data", "rbd unmap /dev/rbd-pay", "RBD", "rbd 19.2.0", "watchers|nbd"),
    ("rbd", "rbd-du-vs-rm", "rbd", "rbd du", "rbd rm pay/data", "RBD", "rbd 19.2.0", "provisioned|used"),
    ("ceph", "ceph-volume-lvm-list-vs-zap", "ceph-volume", "ceph-volume lvm list", "ceph-volume lvm zap --destroy /dev/loop-pay", "ceph-volume", "ceph-volume 19.2.0", "osd|lv"),
    ("rgw", "radosgw-admin-bucket-list-vs-rm", "radosgw-admin", "radosgw-admin bucket list", "radosgw-admin bucket rm --bucket=pay --purge-objects", "RGW", "radosgw-admin 19.2.0", "bucket|owner"),
    ("ceph", "ceph-osd-df-vs-purge", "ceph", "ceph osd df", "ceph osd purge 0 --yes-i-really-mean-it", "Ceph OSD", "ceph 19.2.0", "osd|crush"),
    ("ceph", "ceph-auth-ls-vs-del", "ceph", "ceph auth ls", "ceph auth del client.pay", "Ceph AUTH", "ceph 19.2.0", "client|caps"),
    ("ceph", "ceph-config-dump-vs-assimilate-empty", "ceph", "ceph config dump", "ceph config assimilate-conf -i /dev/null", "Ceph CFG", "ceph 19.2.0", "who|option"),
    ("ceph", "ceph-osd-crush-dump-vs-rm", "ceph", "ceph osd crush dump", "ceph osd crush rm pay-host", "Ceph CRUSH", "ceph 19.2.0", "bucket|item"),
    ("ceph", "ceph-pg-stat-vs-force-create-gone", "ceph", "ceph pg stat", "ceph pg force-create-pg 1.0", "Ceph PG", "ceph 19.2.0", "pg|objects"),
    ("gluster", "gluster-volume-info-vs-delete", "gluster", "gluster volume info pay", "gluster volume delete pay", "Gluster", "gluster 11.1", "Volume|Brick"),
    ("gluster", "gluster-peer-status-vs-detach", "gluster", "gluster peer status", "gluster peer detach pay-2 --force", "Gluster", "gluster 11.1", "Hostname|Uuid"),
    ("gluster", "gluster-volume-status-vs-stop", "gluster", "gluster volume status pay", "gluster volume stop pay --force", "Gluster", "gluster 11.1", "Brick|Port"),
    ("nfs", "exportfs-v-vs-unexport", "exportfs", "exportfs -v", "exportfs -u pay:/export/pay", "nfs-utils", "exportfs 2.6.4", "Path|options"),
    ("nfs", "showmount-e-vs-unexport", "showmount", "showmount -e", "exportfs -ua", "nfs-utils", "showmount 2.6.4", "Export|Path"),
    ("nfs", "nfsstat-vs-rm", "nfsstat", "nfsstat -c", "rm -f /plant/nfsstat-vs-rm/pay.conf", "nfs-utils", "nfsstat 2.6.4", "rpc|nfs"),
    ("rpc", "rpcinfo-p-vs-rm", "rpcinfo", "rpcinfo -p", "rm -f /plant/rpcinfo-p-vs-rm/pay.conf", "rpcbind", "rpcinfo 1.2.6", "port|nfs"),
    ("smb", "smbstatus-vs-shutdown", "smbstatus", "smbstatus -b", "smbcontrol smbd shutdown", "Samba", "smbstatus 4.21.1", "pid|machine"),
    ("smb", "testparm-vs-rm", "testparm", "testparm -s", "rm -f /plant/testparm-vs-rm/pay.conf", "Samba", "testparm 4.21.1", "workgroup|path"),
    ("smb", "pdbedit-L-vs-delete", "pdbedit", "pdbedit -L", "pdbedit -x payuser", "Samba", "pdbedit 4.21.1", "Unix|username"),
    ("smb", "net-ads-info-vs-leave", "net", "net ads info", "net ads leave -U pay%", "Samba", "net 4.21.1", "LDAP|Realm"),
    ("smb", "wbinfo-u-vs-offline", "wbinfo", "wbinfo -u", "net cache flush", "winbind", "wbinfo 4.21.1", "payuser|DOMAIN"),
    ("smb", "samba-tool-user-list-vs-delete", "samba-tool", "samba-tool user list", "samba-tool user delete payuser", "Samba", "samba-tool 4.21.1", "username|dn"),
    ("smb", "ctdb-status-vs-disable", "ctdb", "ctdb status", "ctdb disable -n 0", "CTDB", "ctdb 4.21.1", "pnn|OK"),
    ("smb", "smbcontrol-reload-vs-shutdown", "smbcontrol", "smbcontrol smbd reload-config", "smbcontrol smbd shutdown", "Samba", "smbcontrol 4.21.1", "pid|smbd"),
    ("dm", "dmsetup-table-vs-remove", "dmsetup", "dmsetup table", "dmsetup remove pay", "device-mapper", "dmsetup 1.02.197", "pay|linear"),
    ("dm", "dmsetup-ls-vs-remove", "dmsetup", "dmsetup ls", "dmsetup remove -f pay", "device-mapper", "dmsetup 1.02.197", "pay|uuid"),
    ("dm", "dmsetup-status-vs-remove", "dmsetup", "dmsetup status", "dmsetup remove pay", "device-mapper", "dmsetup 1.02.197", "pay|linear"),
    ("loop", "losetup-j-vs-detach", "losetup", "losetup -j /plant/losetup-j-vs-detach/pay.img", "losetup -d /dev/loop-pay", "util-linux", "losetup 2.40.2", "loop|offset"),
    ("loop", "losetup-l-vs-D", "losetup", "losetup -l", "losetup -D", "util-linux", "losetup 2.40.2", "NAME|BACK-FILE"),
    ("part", "partx-s-vs-delete", "partx", "partx -s /dev/loop-pay", "partx -d /dev/loop-pay", "util-linux", "partx 2.40.2", "NR|START"),
    ("part", "partx-l-vs-d", "partx", "partx -l /dev/loop-pay", "partx --delete /dev/loop-pay", "util-linux", "partx 2.40.2", "NR|NAME"),
    ("part", "sfdisk-d-vs-delete", "sfdisk", "sfdisk -d /dev/loop-pay", "sfdisk --delete /dev/loop-pay 1", "util-linux", "sfdisk 2.40.2", "label|start"),
    ("part", "sfdisk-l-vs-delete", "sfdisk", "sfdisk -l /dev/loop-pay", "sfdisk --delete /dev/loop-pay", "util-linux", "sfdisk 2.40.2", "Device|Start"),
    ("part", "sgdisk-p-vs-zap", "sgdisk", "sgdisk -p /dev/loop-pay", "sgdisk -Z /dev/loop-pay", "gdisk", "sgdisk 1.0.10", "Number|Start"),
    ("part", "sgdisk-i-vs-o", "sgdisk", "sgdisk -i 1 /dev/loop-pay", "sgdisk -o /dev/loop-pay", "gdisk", "sgdisk 1.0.10", "Partition|GUID"),
    ("part", "gdisk-l-vs-o", "gdisk", "gdisk -l /dev/loop-pay", "sgdisk -o /dev/loop-pay", "gdisk", "gdisk 1.0.10", "Number|Code"),
    ("part", "parted-print-vs-mklabel", "parted", "parted -s /dev/loop-pay print", "parted -s /dev/loop-pay mklabel gpt", "parted", "parted 3.6", "Number|Start"),
    ("part", "partprobe-vs-wipefs", "partprobe", "partprobe -s /dev/loop-pay", "wipefs -a /dev/loop-pay", "parted", "partprobe 3.6", "loop|partition"),
    ("fs", "wipefs-n-vs-a", "wipefs", "wipefs -n /dev/loop-pay", "wipefs -a /dev/loop-pay", "util-linux", "wipefs 2.40.2", "offset|type"),
    ("fs", "lsblk-p-vs-wipefs", "lsblk", "lsblk -p /dev/loop-pay", "wipefs -a /dev/loop-pay", "util-linux", "lsblk 2.40.2", "NAME|FSTYPE"),
    ("fs", "lsblk-O-vs-wipefs", "lsblk", "lsblk -O /dev/loop-pay", "wipefs -a /dev/loop-pay", "util-linux", "lsblk 2.40.2", "NAME|UUID"),
    ("fs", "findmnt-n-vs-umount", "findmnt", "findmnt -n /mnt/pay", "umount -l /mnt/pay", "util-linux", "findmnt 2.40.2", "TARGET|SOURCE"),
    ("fs", "mountpoint-q-vs-umount", "mountpoint", "mountpoint -q /mnt/pay", "umount -l /mnt/pay", "sysvinit", "mountpoint 3.08", "pay|mnt"),
    ("fs", "mount-J-vs-umount", "mount", "mount -J", "umount -l /mnt/pay", "util-linux", "mount 2.40.2", "target|source"),
    ("fs", "blkid-o-export-vs-wipefs", "blkid", "blkid -o export /dev/loop-pay", "wipefs -a /dev/loop-pay", "util-linux", "blkid 2.40.2", "UUID|TYPE"),
    ("swap", "swapon-s-vs-swapoff", "swapon", "swapon --show", "swapoff -a", "util-linux", "swapon 2.40.2", "NAME|TYPE"),
    ("zram", "zramctl-l-vs-reset", "zramctl", "zramctl --output-all", "zramctl --reset /dev/zram0", "util-linux", "zramctl 2.40.2", "NAME|DISKSIZE"),
    ("lvm", "lvscan-vs-lvremove", "lvscan", "lvscan", "lvremove -f pay/data", "lvm2", "lvscan 2.03.22", "ACTIVE|lv"),
    ("lvm", "vgscan-vs-vgremove", "vgscan", "vgscan", "vgremove -f pay", "lvm2", "vgscan 2.03.22", "Found|VG"),
    ("lvm", "pvscan-vs-pvremove", "pvscan", "pvscan", "pvremove -ff /dev/loop-pay", "lvm2", "pvscan 2.03.22", "PV|VG"),
    ("lvm", "lvdisplay-v-vs-lvremove", "lvdisplay", "lvdisplay -v pay/data", "lvremove -f pay/data", "lvm2", "lvdisplay 2.03.22", "LV|UUID"),
    ("lvm", "vgdisplay-c-vs-vgremove", "vgdisplay", "vgdisplay -c pay", "vgremove -f pay", "lvm2", "vgdisplay 2.03.22", "pay|colon"),
    ("lvm", "pvdisplay-vs-pvremove", "pvdisplay", "pvdisplay /dev/loop-pay", "pvremove -ff /dev/loop-pay", "lvm2", "pvdisplay 2.03.22", "PV|UUID"),
    ("lvm", "lvs-o-vs-lvremove", "lvs", "lvs -o+uuid", "lvremove -f pay/data", "lvm2", "lvs 2.03.22", "LV|VG"),
    ("lvm", "vgs-o-vs-vgremove", "vgs", "vgs -o+uuid", "vgremove -f pay", "lvm2", "vgs 2.03.22", "VG|PV"),
    ("lvm", "pvs-o-vs-pvremove", "pvs", "pvs -o+uuid,size", "pvremove -ff /dev/loop-pay", "lvm2", "pvs 2.03.22", "PV|VG"),
    ("lvm", "vgck-vs-vgremove", "vgck", "vgck pay", "vgremove -f pay", "lvm2", "vgck 2.03.22", "VG|consistent"),
    ("lvm", "thin-ls-vs-rm", "thin_ls", "thin_ls /plant/thin-ls-vs-rm/meta.bin", "thin_rmap --region 0 /plant/thin-ls-vs-rm/meta.bin", "thin-provisioning-tools", "thin_ls 1.1.0", "dev|mapped"),
    ("crypto", "cryptsetup-luksDump-vs-erase2", "cryptsetup", "cryptsetup luksDump /plant/cryptsetup-luksDump-vs-erase2/pay.conf", "cryptsetup luksErase -q /plant/cryptsetup-luksDump-vs-erase2/pay.conf", "cryptsetup", "cryptsetup 2.7.5", "LUKS|Cipher"),
    ("crypto", "cryptsetup-isLuks-vs-erase", "cryptsetup", "cryptsetup isLuks /plant/cryptsetup-isLuks-vs-erase/pay.conf", "cryptsetup luksErase -q /plant/cryptsetup-isLuks-vs-erase/pay.conf", "cryptsetup", "cryptsetup 2.7.5", "LUKS|payload"),
    ("crypto", "cryptsetup-status2-vs-close", "cryptsetup", "cryptsetup status pay", "cryptsetup close pay", "cryptsetup", "cryptsetup 2.7.5", "type|device"),
    ("crypto", "veritysetup-status-vs-close", "veritysetup", "veritysetup status pay", "veritysetup close pay", "cryptsetup", "veritysetup 2.7.5", "type|hash"),
    ("crypto", "integritysetup-status-vs-close", "integritysetup", "integritysetup status pay", "integritysetup close pay", "cryptsetup", "integritysetup 2.7.5", "type|tag"),
    ("zfs", "zfs-get-used-vs-destroy", "zfs", "zfs get used pay/data", "zfs destroy -r pay/data", "ZFS", "zfs 2.2.6", "USED|dataset"),
    ("zfs", "zpool-get-all-vs-destroy", "zpool", "zpool get all pay", "zpool destroy -f pay", "ZFS", "zpool 2.2.6", "pool|health"),
    ("zfs", "zpool-iostat-vs-destroy", "zpool", "zpool iostat -v pay", "zpool destroy -f pay", "ZFS", "zpool 2.2.6", "alloc|free"),
    ("zfs", "zfs-mount-vs-destroy", "zfs", "zfs mount", "zfs destroy -r pay/data", "ZFS", "zfs 2.2.6", "pay|data"),
    ("btrfs", "btrfs-filesystem-df-vs-device-delete", "btrfs", "btrfs filesystem df /mnt/pay", "btrfs device delete /dev/loop-pay /mnt/pay", "btrfs-progs", "btrfs 6.11", "Data|Metadata"),
    ("btrfs", "btrfs-subvolume-show-vs-delete", "btrfs", "btrfs subvolume show /mnt/pay", "btrfs subvolume delete /mnt/pay/snap", "btrfs-progs", "btrfs 6.11", "Name|UUID"),
    ("btrfs", "btrfs-device-stats-vs-delete", "btrfs", "btrfs device stats /mnt/pay", "btrfs device delete /dev/loop-pay /mnt/pay", "btrfs-progs", "btrfs 6.11", "write|corr"),
    ("xfs", "xfs-spaceman-info-vs-repair", "xfs_spaceman", "xfs_spaceman -c info /mnt/pay", "xfs_repair -L /plant/xfs-spaceman-info-vs-repair/pay.conf", "xfsprogs", "xfs_spaceman 6.8.0", "blocksize|agcount"),
    ("xfs", "xfs-growfs-n-vs-repair", "xfs_growfs", "xfs_growfs -n /mnt/pay", "xfs_repair -L /plant/xfs-growfs-n-vs-repair/pay.conf", "xfsprogs", "xfs_growfs 6.8.0", "data|imaxpct"),
    ("ext", "tune2fs-l-vs-mke2fs", "tune2fs", "tune2fs -l /plant/tune2fs-l-vs-mke2fs/pay.conf", "mke2fs -F /plant/tune2fs-l-vs-mke2fs/pay.conf", "e2fsprogs", "tune2fs 1.47.1", "Filesystem|UUID"),
    ("ext", "debugfs-stats-vs-mke2fs", "debugfs", "debugfs -R stats /plant/debugfs-stats-vs-mke2fs/pay.conf", "mke2fs -F /plant/debugfs-stats-vs-mke2fs/pay.conf", "e2fsprogs", "debugfs 1.47.1", "Inode|Block"),
    ("ext", "e2image-r-vs-mke2fs", "e2image", "e2image -r /plant/e2image-r-vs-mke2fs/pay.conf /tmp/pay.e2i", "mke2fs -F /plant/e2image-r-vs-mke2fs/pay.conf", "e2fsprogs", "e2image 1.47.1", "ext4|image"),
    ("ext", "resize2fs-P-vs-mke2fs", "resize2fs", "resize2fs -P /plant/resize2fs-P-vs-mke2fs/pay.conf", "mke2fs -F /plant/resize2fs-P-vs-mke2fs/pay.conf", "e2fsprogs", "resize2fs 1.47.1", "minimum|blocks"),
    ("ext", "dumpe2fs-h-vs-mke2fs", "dumpe2fs", "dumpe2fs -h /plant/dumpe2fs-h-vs-mke2fs/pay.conf", "mke2fs -F /plant/dumpe2fs-h-vs-mke2fs/pay.conf", "e2fsprogs", "dumpe2fs 1.47.1", "Filesystem|Inode"),
    ("nilfs", "nilfs-tune-l-vs-mkfs", "nilfs-tune", "nilfs-tune -l /plant/nilfs-tune-l-vs-mkfs/pay.conf", "mkfs.nilfs2 -f /plant/nilfs-tune-l-vs-mkfs/pay.conf", "nilfs-utils", "nilfs-tune 2.2.9", "UUID|blocksize"),
    ("f2fs", "f2fs-fsck-n-vs-mkfs", "fsck.f2fs", "fsck.f2fs -n /plant/f2fs-fsck-n-vs-mkfs/pay.conf", "mkfs.f2fs -f /plant/f2fs-fsck-n-vs-mkfs/pay.conf", "f2fs-tools", "fsck.f2fs 1.16.0", "Magic|version"),
    ("ntfs", "ntfsinfo-m-vs-mkntfs", "ntfsinfo", "ntfsinfo -m /plant/ntfsinfo-m-vs-mkntfs/pay.conf", "mkntfs -F /plant/ntfsinfo-m-vs-mkntfs/pay.conf", "ntfs-3g", "ntfsinfo 2022.10.3", "Volume|Cluster"),
    ("fat", "fatlabel-vs-mkfs", "fatlabel", "fatlabel /plant/fatlabel-vs-mkfs/pay.conf", "mkfs.vfat -I /plant/fatlabel-vs-mkfs/pay.conf", "dosfstools", "fatlabel 4.2", "PAY|FAT"),
    ("exfat", "exfatinfo-vs-mkfs", "exfatlabel", "exfatlabel /plant/exfatinfo-vs-mkfs/pay.conf", "mkfs.exfat /plant/exfatinfo-vs-mkfs/pay.conf", "exfatprogs", "exfatlabel 1.2.5", "PAY|exfat"),
    ("bcache", "bcache-super-show-vs-make", "bcache-super-show", "bcache-super-show /plant/bcache-super-show-vs-make/pay.conf", "make-bcache -C /plant/bcache-super-show-vs-make/pay.conf", "bcache-tools", "bcache-super-show 1.0.8", "sb|csum"),
    ("nvme", "nvme-list-n-vs-format", "nvme", "nvme list -o json", "nvme format /dev/nvme0n1 --ses=1 --force", "nvme-cli", "nvme 2.10.2", "Model|Serial"),
    ("nvme", "nvme-id-ns-vs-format", "nvme", "nvme id-ns /dev/nvme0n1", "nvme format /dev/nvme0n1 --force", "nvme-cli", "nvme 2.10.2", "nsze|ncap"),
    ("nvme", "nvme-id-ctrl-vs-format", "nvme", "nvme id-ctrl /dev/nvme0", "nvme format /dev/nvme0n1 --force", "nvme-cli", "nvme 2.10.2", "mn|sn"),
    ("nvme", "nvme-smart-log-vs-sanitize", "nvme", "nvme smart-log /dev/nvme0", "nvme sanitize /dev/nvme0 --sanact=1", "nvme-cli", "nvme 2.10.2", "critical|temp"),
    ("nvme", "nvme-list-vs-format", "nvme", "nvme list", "nvme format /dev/nvme0n1 --force", "nvme-cli", "nvme 2.10.2", "Node|Model"),
    ("tgt", "tgtadm-lun-show-vs-delete", "tgtadm", "tgtadm --mode target --op show", "tgtadm --mode target --op delete --tid 1", "tgt", "tgtadm 1.0.85", "Target|LUN"),
    ("iscsi", "targetcli-ls-vs-clearconfig", "targetcli", "targetcli ls", "targetcli clearconfig confirm=True", "targetcli", "targetcli 2.1.58", "iqn|backstore"),
    ("mpath", "multipath-ll-vs-flush", "multipath", "multipath -ll", "multipath -F", "multipath-tools", "multipath 0.9.9", "dm|prio"),
    ("os", "openstack-server-show-vs-delete", "openstack", "openstack server show pay", "openstack server delete pay", "OpenStack API", "openstack 7.1.0", "id|status"),
    ("os", "openstack-volume-show-vs-delete", "openstack", "openstack volume show pay", "openstack volume delete pay", "Cinder API", "openstack 7.1.0", "id|size"),
    ("os", "openstack-image-show-vs-delete", "openstack", "openstack image show pay", "openstack image delete pay", "Glance API", "openstack 7.1.0", "id|checksum"),
    ("os", "openstack-network-show-vs-delete", "openstack", "openstack network show pay", "openstack network delete pay", "Neutron API", "openstack 7.1.0", "id|mtu"),
    ("os", "openstack-stack-show-vs-delete", "openstack", "openstack stack show pay", "openstack stack delete pay --yes", "Heat API", "openstack 7.1.0", "id|stack"),
    ("os", "openstack-user-show-vs-delete", "openstack", "openstack user show pay", "openstack user delete pay", "Keystone API", "openstack 7.1.0", "id|name"),
    ("os", "nova-show-vs-delete", "nova", "nova show pay", "nova delete pay", "Nova API", "nova 29.2.0", "id|status"),
    ("os", "nova-list-vs-delete", "nova", "nova list", "nova delete pay", "Nova API", "nova 29.2.0", "ID|Status"),
    ("os", "neutron-net-show-vs-delete", "neutron", "neutron net-show pay", "neutron net-delete pay", "Neutron API", "neutron 25.0.0", "id|mtu"),
    ("os", "neutron-port-show-vs-delete", "neutron", "neutron port-show pay", "neutron port-delete pay", "Neutron API", "neutron 25.0.0", "id|mac"),
    ("os", "cinder-show-vs-delete", "cinder", "cinder show pay", "cinder delete pay", "Cinder API", "cinder 25.0.0", "id|size"),
    ("os", "cinder-list-vs-delete", "cinder", "cinder list", "cinder delete pay", "Cinder API", "cinder 25.0.0", "ID|Status"),
    ("os", "glance-image-show-vs-delete", "glance", "glance image-show pay", "glance image-delete pay", "Glance API", "glance 29.0.0", "id|checksum"),
    ("os", "glance-image-list-vs-delete", "glance", "glance image-list", "glance image-delete pay", "Glance API", "glance 29.0.0", "ID|Name"),
    ("os", "ironic-node-show-vs-delete", "ironic", "ironic node-show pay", "ironic node-delete pay", "Ironic API", "ironic 26.1.0", "uuid|power"),
    ("os", "heat-stack-show-vs-delete", "heat", "heat stack-show pay", "heat stack-delete pay", "Heat API", "heat 23.0.0", "id|stack"),
    ("os", "magnum-cluster-show-vs-delete", "magnum", "magnum cluster-show pay", "magnum cluster-delete pay", "Magnum API", "magnum 19.0.0", "uuid|status"),
    ("os", "manila-share-show-vs-delete", "manila", "manila show pay", "manila delete pay", "Manila API", "manila 19.0.0", "id|share"),
    ("os", "designate-zone-show-vs-delete", "openstack", "openstack zone show pay.internal.", "openstack zone delete pay.internal.", "Designate API", "openstack 7.1.0", "id|serial"),
    ("os", "octavia-lb-show-vs-delete", "openstack", "openstack loadbalancer show pay", "openstack loadbalancer delete pay --cascade", "Octavia API", "openstack 7.1.0", "id|vip"),
    ("mq", "rabbitmqctl-list-queues-vs-delete", "rabbitmqctl", "rabbitmqctl list_queues", "rabbitmqctl delete_queue pay", "RabbitMQ", "rabbitmqctl 3.13.7", "name|messages"),
    ("mq", "rabbitmqctl-list-exchanges-vs-delete", "rabbitmqctl", "rabbitmqctl list_exchanges", "rabbitmqctl delete_exchange pay", "RabbitMQ", "rabbitmqctl 3.13.7", "name|type"),
    ("mq", "rabbitmqctl-list-vhosts-vs-delete", "rabbitmqctl", "rabbitmqctl list_vhosts", "rabbitmqctl delete_vhost pay", "RabbitMQ", "rabbitmqctl 3.13.7", "name|tracing"),
    ("mq", "rabbitmqctl-list-users-vs-delete", "rabbitmqctl", "rabbitmqctl list_users", "rabbitmqctl delete_user pay", "RabbitMQ", "rabbitmqctl 3.13.7", "user|tags"),
    ("mq", "rabbitmqadmin-list-queues-vs-delete", "rabbitmqadmin", "rabbitmqadmin list queues", "rabbitmqadmin delete queue name=pay", "RabbitMQ", "rabbitmqadmin 3.13.7", "name|messages"),
    ("stream", "pulsar-admin-topics-list-vs-delete", "pulsar-admin", "pulsar-admin topics list pay", "pulsar-admin topics delete persistent://pay/prod/invoices", "Pulsar", "pulsar-admin 3.3.2", "persistent|pay"),
    ("stream", "pulsar-admin-namespaces-list-vs-delete", "pulsar-admin", "pulsar-admin namespaces list pay", "pulsar-admin namespaces delete pay/prod", "Pulsar", "pulsar-admin 3.3.2", "pay|prod"),
    ("stream", "pulsar-admin-tenants-list-vs-delete", "pulsar-admin", "pulsar-admin tenants list", "pulsar-admin tenants delete pay", "Pulsar", "pulsar-admin 3.3.2", "pay|admin"),
    ("nats", "nats-stream-info-vs-delete", "nats", "nats stream info PAY", "nats stream delete PAY --force", "NATS", "nats 0.1.5", "Name|Subjects"),
    ("nats", "nats-kv-info-vs-del", "nats", "nats kv info pay", "nats kv del pay invoices --force", "NATS", "nats 0.1.5", "Bucket|Values"),
    ("nats", "nats-consumer-info-vs-delete", "nats", "nats consumer info PAY pay-worker", "nats consumer delete PAY pay-worker --force", "NATS", "nats 0.1.5", "Name|Ack"),
    ("kafka", "kafka-acls-list-vs-remove", "kafka-acls.sh", "kafka-acls.sh --list --topic pay", "kafka-acls.sh --remove --force --topic pay --allow-principal User:pay", "Kafka", "kafka 3.8.1", "principal|topic"),
    ("kafka", "kafka-consumer-groups-describe-vs-delete", "kafka-consumer-groups.sh", "kafka-consumer-groups.sh --describe --group pay", "kafka-consumer-groups.sh --delete --group pay", "Kafka", "kafka 3.8.1", "GROUP|TOPIC"),
    ("kv", "etcdctl-endpoint-status-vs-del", "etcdctl", "etcdctl endpoint status", "etcdctl del /pay --prefix", "etcd", "etcdctl 3.5.16", "endpoint|version"),
    ("kv", "consul-catalog-services-vs-kv-delete", "consul", "consul catalog services", "consul kv delete -recurse pay/", "Consul API", "consul 1.20.1", "pay|passing"),
    ("kv", "vault-status-vs-lease-revoke", "vault", "vault status", "vault lease revoke -prefix pay/", "Vault API", "vault 1.18.2", "Sealed|Version"),
    ("sched", "nomad-node-status-vs-drain", "nomad", "nomad node status", "nomad node drain -enable -yes -self", "Nomad API", "nomad 1.9.3", "ID|Status"),
    ("sched", "nomad-alloc-status-vs-stop", "nomad", "nomad alloc status", "nomad alloc stop pay", "Nomad API", "nomad 1.9.3", "ID|Task"),
    ("edge", "lighttpd-t-vs-stop", "lighttpd", "lighttpd -t -f /plant/lighttpd-t-vs-stop/pay.conf", "lighttpd -f /plant/lighttpd-t-vs-stop/pay.conf -1; killall lighttpd", "lighttpd", "lighttpd 1.4.76", "server|port"),
    ("edge", "varnishd-C-vs-stop", "varnishd", "varnishd -C -f /plant/varnishd-C-vs-stop/pay.conf", "varnishadm stop", "Varnish", "varnishd 7.6.1", "vcl|backend"),
    ("edge", "varnishadm-status-vs-stop", "varnishadm", "varnishadm status", "varnishadm stop", "Varnish", "varnishadm 7.6.1", "Child|running"),
    ("edge", "squid-k-parse-vs-shutdown", "squid", "squid -k parse", "squid -k shutdown", "Squid", "squid 6.12", "http_port|cache_dir"),
    ("edge", "traefik-healthcheck-vs-stop", "traefik", "traefik healthcheck", "killall traefik", "Traefik", "traefik 3.2.1", "entryPoints|providers"),
    ("fw", "nft-list-ruleset-vs-flush", "nft", "nft list ruleset", "nft flush ruleset", "nftables", "nft 1.1.1", "table|chain"),
    ("fw", "ebtables-L-vs-F", "ebtables", "ebtables -L", "ebtables -F", "ebtables", "ebtables 2.0.11", "Bridge|policy"),
    ("fw", "arptables-L-vs-F", "arptables", "arptables -L", "arptables -F", "arptables", "arptables 0.0.5", "Chain|policy"),
    ("fw", "firewall-cmd-list-vs-panic", "firewall-cmd", "firewall-cmd --list-all", "firewall-cmd --panic-on", "firewalld", "firewall-cmd 2.2.1", "zone|service"),
    ("fw", "ufw-status-vs-reset", "ufw", "ufw status verbose", "ufw --force reset", "ufw", "ufw 0.36.2", "Status|Default"),
    ("fw", "shorewall-status-vs-clear", "shorewall", "shorewall status", "shorewall clear", "Shorewall", "shorewall 5.2.8", "State|Shorewall"),
    ("hpc", "sinfo-N-vs-scancel", "sinfo", "sinfo -N", "scancel -u pay", "Slurm", "sinfo 24.05.4", "NODELIST|STATE"),
    ("hpc", "squeue-o-vs-scancel", "squeue", "squeue -o '%.18i %.9P %.8j %.8u %.2t %.10M'", "scancel --state=PENDING", "Slurm", "squeue 24.05.4", "JOBID|PARTITION"),
    ("hpc", "sacct-vs-scancel", "sacct", "sacct -j 4242", "scancel 4242", "Slurm", "sacct 24.05.4", "JobID|State"),
    ("hpc", "scontrol-show-job-vs-scancel", "scontrol", "scontrol show job 4242", "scancel 4242", "Slurm", "scontrol 24.05.4", "JobId|JobState"),
    ("hpc", "qstat-f-vs-qdel", "qstat", "qstat -f 4242", "qdel 4242", "PBS", "qstat 20.0.1", "Job_Name|job_state"),
    ("hpc", "qstat-vs-qdel", "qstat", "qstat", "qdel all", "PBS", "qstat 20.0.1", "Job|User"),
    ("hpc", "condor-status-vs-rm", "condor_status", "condor_status", "condor_off -all", "HTCondor", "condor_status 23.9.6", "Name|OpSys"),
    ("hpc", "condor-q-vs-rm", "condor_q", "condor_q", "condor_rm -all", "HTCondor", "condor_q 23.9.6", "ID|OWNER"),
    ("hpc", "bjobs-vs-bkill", "bjobs", "bjobs -u pay", "bkill 0", "LSF", "bjobs 10.1.0", "JOBID|STAT"),
    ("wf", "airflow-dags-list-vs-delete", "airflow", "airflow dags list", "airflow dags delete pay", "Airflow", "airflow 2.10.4", "dag_id|paused"),
    ("wf", "airflow-tasks-list-vs-delete", "airflow", "airflow tasks list pay", "airflow dags delete pay", "Airflow", "airflow 2.10.4", "task_id|operator"),
    ("wf", "dagster-job-list-vs-delete", "dagster", "dagster job list -m pay", "dagster run delete --force pay", "Dagster", "dagster 1.9.3", "job|pipeline"),
    ("wf", "celery-inspect-active-vs-purge", "celery", "celery -A pay inspect active", "celery -A pay purge -f", "Celery", "celery 5.4.0", "active|worker"),
    ("wf", "rq-info-vs-empty", "rq", "rq info", "rq empty pay --yes", "RQ", "rq 1.16.2", "pay|queued"),
    ("wf", "nextflow-inspect-vs-rm", "nextflow", "nextflow inspect pay.nf", "rm -rf /plant/nextflow-inspect-vs-rm/work", "Nextflow", "nextflow 24.10.0", "process|workflow"),
    ("wf", "snakemake-n-vs-rm", "snakemake", "snakemake -n", "rm -rf /plant/snakemake-n-vs-rm/.snakemake", "Snakemake", "snakemake 8.25.3", "rule|input"),
    ("wf", "cromwell-status-vs-abort", "cromwell", "cromwell status 4242", "cromwell abort 4242", "Cromwell", "cromwell 87", "id|status"),
    ("wf", "toil-status-vs-destroy", "toil", "toil status /plant/toil-status-vs-destroy/jobstore", "toil destroy /plant/toil-status-vs-destroy/jobstore", "Toil", "toil 6.2.0", "job|status"),
    ("cache", "valkey-cli-dbsize-vs-flushall", "valkey-cli", "valkey-cli DBSIZE", "valkey-cli FLUSHALL", "Valkey", "valkey-cli 8.0.1", "keys|db"),
    ("cache", "dragonfly-info-vs-flushall", "redis-cli", "redis-cli -p 6379 INFO keyspace", "redis-cli -p 6379 FLUSHALL", "Dragonfly", "redis-cli 7.4.1", "db0|keys"),
    ("cache", "keydb-cli-dbsize-vs-flushall", "keydb-cli", "keydb-cli DBSIZE", "keydb-cli FLUSHALL", "KeyDB", "keydb-cli 6.3.4", "keys|db"),
    ("cache", "redis-cli-info-memory-vs-flushall", "redis-cli", "redis-cli INFO memory", "redis-cli FLUSHALL", "Redis", "redis-cli 7.4.1", "used_memory|peak"),
    ("db", "mysqladmin-status-vs-shutdown", "mysqladmin", "mysqladmin status", "mysqladmin shutdown", "MySQL", "mysqladmin 8.4.3", "Uptime|Threads"),
    ("db", "pg-isready-vs-dropdb", "pg_isready", "pg_isready -d pay", "dropdb --if-exists pay", "PostgreSQL", "pg_isready 16.6", "accepting|connections"),
    ("db", "psql-l-vs-dropdb", "psql", "psql -l", "dropdb --if-exists pay", "PostgreSQL", "psql 16.6", "Name|Owner"),
    ("db", "mongosh-show-dbs-vs-drop", "mongosh", "mongosh --eval 'db.adminCommand({listDatabases:1})'", "mongosh pay --eval 'db.dropDatabase()'", "MongoDB", "mongosh 2.3.3", "name|sizeOnDisk"),
    ("db", "cqlsh-describe-cluster-vs-drop", "cqlsh", "cqlsh -e 'DESCRIBE CLUSTER'", "cqlsh -e 'DROP KEYSPACE pay'", "Cassandra", "cqlsh 6.1.0", "Cluster|Partitioner"),
    ("db", "trino-show-vs-drop", "trino", "trino --execute 'SHOW CATALOGS'", "trino --execute 'DROP SCHEMA pay.prod CASCADE'", "Trino", "trino 456", "Catalog|pay"),
    ("db", "spark-sql-show-vs-drop", "spark-sql", "spark-sql -e 'SHOW TABLES'", "spark-sql -e 'DROP TABLE pay.invoices'", "Spark", "spark-sql 3.5.3", "namespace|table"),
    ("db", "hive-show-vs-drop", "hive", "hive -e 'SHOW DATABASES'", "hive -e 'DROP DATABASE pay CASCADE'", "Hive", "hive 4.0.1", "pay|default"),
    ("db", "presto-show-vs-drop", "presto", "presto --execute 'SHOW SCHEMAS'", "presto --execute 'DROP SCHEMA pay CASCADE'", "Presto", "presto 0.291", "Schema|pay"),
    ("db", "impala-shell-show-vs-drop", "impala-shell", "impala-shell -q 'SHOW DATABASES'", "impala-shell -q 'DROP DATABASE pay CASCADE'", "Impala", "impala-shell 4.4.1", "pay|default"),
    ("db", "snowsql-show-vs-drop", "snowsql", "snowsql -q 'SHOW DATABASES'", "snowsql -q 'DROP DATABASE pay'", "Snowflake", "snowsql 1.3.2", "name|created"),
    ("db", "bq-ls-vs-rm", "bq", "bq ls pay", "bq rm -r -f pay", "BigQuery API", "bq 2.1.9", "tableId|Type"),
    ("obj", "gsutil-ls-vs-rm", "gsutil", "gsutil ls gs://pay-prod/", "gsutil -m rm -r gs://pay-prod/**", "GCS API", "gsutil 5.30", "gs://|pay"),
    ("obj", "azcopy-list-vs-remove", "azcopy", "azcopy list https://pay.blob.core.windows.net/pay", "azcopy remove https://pay.blob.core.windows.net/pay --recursive", "Azure Blob", "azcopy 10.27.1", "Content-Length|pay"),
    ("obj", "mc-ls-vs-rb", "mc", "mc ls pay/prod", "mc rb --force pay/prod", "MinIO", "mc 2024.11.21", "pay|prod"),
    ("obj", "s5cmd-ls-vs-rm", "s5cmd", "s5cmd ls s3://pay-prod/", "s5cmd rm 's3://pay-prod/*'", "s5cmd", "s5cmd 2.2.2", "s3://|pay"),
    ("aws", "aws-s3-ls-vs-rb", "aws", "aws s3 ls s3://pay-prod/", "aws s3 rb s3://pay-prod --force", "S3 API", "aws 2.22.0", "PRE|pay"),
    ("aws", "aws-ec2-describe-vs-terminate", "aws", "aws ec2 describe-instances --instance-ids i-pay", "aws ec2 terminate-instances --instance-ids i-pay", "EC2 API", "aws 2.22.0", "InstanceId|State"),
    ("aws", "aws-rds-describe-vs-delete", "aws", "aws rds describe-db-instances --db-instance-identifier pay", "aws rds delete-db-instance --db-instance-identifier pay --skip-final-snapshot", "RDS API", "aws 2.22.0", "DBInstance|Status"),
    ("aws", "aws-lambda-get-vs-delete", "aws", "aws lambda get-function --function-name pay", "aws lambda delete-function --function-name pay", "Lambda API", "aws 2.22.0", "FunctionName|Runtime"),
    ("aws", "aws-ecs-describe-vs-delete", "aws", "aws ecs describe-clusters --clusters pay", "aws ecs delete-cluster --cluster pay", "ECS API", "aws 2.22.0", "clusterName|status"),
    ("aws", "aws-eks-describe-vs-delete", "aws", "aws eks describe-cluster --name pay", "aws eks delete-cluster --name pay", "EKS API", "aws 2.22.0", "name|status"),
    ("aws", "aws-iam-get-role-vs-delete", "aws", "aws iam get-role --role-name pay", "aws iam delete-role --role-name pay", "IAM API", "aws 2.22.0", "RoleName|Arn"),
    ("gcp", "gcloud-sql-instances-describe-vs-delete", "gcloud", "gcloud sql instances describe pay", "gcloud sql instances delete pay --quiet", "Cloud SQL API", "gcloud 500.0.0", "name|state"),
    ("gcp", "gcloud-functions-describe-vs-delete", "gcloud", "gcloud functions describe pay", "gcloud functions delete pay --quiet", "Cloud Functions API", "gcloud 500.0.0", "name|status"),
    ("gcp", "gcloud-run-services-describe-vs-delete", "gcloud", "gcloud run services describe pay", "gcloud run services delete pay --quiet", "Cloud Run API", "gcloud 500.0.0", "name|url"),
    ("gcp", "gcloud-container-clusters-describe-vs-delete", "gcloud", "gcloud container clusters describe pay --zone us-central1-a", "gcloud container clusters delete pay --zone us-central1-a --quiet", "GKE API", "gcloud 500.0.0", "name|status"),
    ("az", "az-sql-db-show-vs-delete", "az", "az sql db show -g pay -s pay -n pay", "az sql db delete -g pay -s pay -n pay --yes", "Azure SQL", "az 2.67.0", "name|status"),
    ("az", "az-functionapp-show-vs-delete", "az", "az functionapp show -g pay -n pay", "az functionapp delete -g pay -n pay", "Azure Functions", "az 2.67.0", "name|state"),
    ("az", "az-aks-show-vs-delete", "az", "az aks show -g pay -n pay", "az aks delete -g pay -n pay --yes", "AKS API", "az 2.67.0", "name|provisioning"),
    ("az", "az-cosmosdb-show-vs-delete", "az", "az cosmosdb show -g pay -n pay", "az cosmosdb delete -g pay -n pay --yes", "Cosmos DB", "az 2.67.0", "name|location"),
    ("do", "doctl-k8s-cluster-get-vs-delete", "doctl", "doctl kubernetes cluster get pay", "doctl kubernetes cluster delete pay --force", "DOKS API", "doctl 1.120.0", "id|region"),
    ("do", "doctl-databases-get-vs-delete", "doctl", "doctl databases get pay", "doctl databases delete pay --force", "DO DBaaS", "doctl 1.120.0", "id|engine"),
    ("hetzner", "hcloud-volume-describe-vs-delete", "hcloud", "hcloud volume describe pay", "hcloud volume delete pay", "Hetzner API", "hcloud 1.49.0", "id|size"),
    ("hetzner", "hcloud-firewall-describe-vs-delete", "hcloud", "hcloud firewall describe pay", "hcloud firewall delete pay", "Hetzner API", "hcloud 1.49.0", "id|name"),
    ("linode", "linode-cli-volumes-view-vs-delete", "linode-cli", "linode-cli volumes view pay", "linode-cli volumes delete pay", "Linode API", "linode-cli 5.56.0", "id|size"),
    ("vultr", "vultr-cli-block-storage-get-vs-delete", "vultr-cli", "vultr-cli block-storage get pay", "vultr-cli block-storage delete pay", "Vultr API", "vultr-cli 3.4.0", "id|size"),
    ("scw", "scw-rdb-instance-get-vs-delete", "scw", "scw rdb instance get pay", "scw rdb instance delete pay", "Scaleway RDB", "scw 2.34.0", "id|engine"),
    ("ibm", "ibmcloud-ks-cluster-get-vs-delete", "ibmcloud", "ibmcloud ks cluster get --cluster pay", "ibmcloud ks cluster rm --cluster pay -f", "IKS API", "ibmcloud 2.32.0", "ID|State"),
    ("oci", "oci-compute-instance-get-vs-delete", "oci", "oci compute instance get --instance-id pay", "oci compute instance terminate --instance-id pay --force", "OCI API", "oci 3.51.0", "id|lifecycle"),
    ("ali", "alicloud-ecs-describe-vs-delete", "aliyun", "aliyun ecs DescribeInstances --InstanceIds pay", "aliyun ecs DeleteInstance --InstanceId pay --Force true", "Aliyun ECS", "aliyun 3.0.241", "InstanceId|Status"),
    ("exo", "exoscale-compute-instance-show-vs-delete", "exo", "exo compute instance show pay", "exo compute instance delete pay --force", "Exoscale API", "exo 1.84.0", "id|state"),
    ("metal", "metal-device-get-vs-delete", "metal", "metal device get -i pay", "metal device delete -i pay -f", "Equinix Metal", "metal 0.25.0", "id|state"),
    ("pve", "proxmox-qm-config-vs-destroy", "qm", "qm config 101", "qm destroy 101 --purge", "Proxmox", "qm 8.3.0", "name|scsi"),
    ("pve", "pvesh-get-vs-delete", "pvesh", "pvesh get /nodes/pay/qemu/101/config", "pvesh delete /nodes/pay/qemu/101", "Proxmox", "pvesh 8.3.0", "name|memory"),
    ("pve", "pct-config-vs-destroy", "pct", "pct config 101", "pct destroy 101 --purge", "Proxmox", "pct 8.3.0", "hostname|rootfs"),
    ("pve", "qm-status-vs-destroy", "qm", "qm status 101", "qm destroy 101 --purge", "Proxmox", "qm 8.3.0", "status|running"),
    ("virt", "virsh-dominfo-vs-undefine", "virsh", "virsh dominfo pay", "virsh undefine pay --remove-all-storage", "libvirt", "virsh 10.7.0", "Id|Name"),
    ("virt", "virsh-vol-info-vs-delete", "virsh", "virsh vol-info --pool pay pay.qcow2", "virsh vol-delete --pool pay pay.qcow2", "libvirt", "virsh 10.7.0", "Name|Capacity"),
    ("virt", "qemu-nbd-l-vs-disconnect", "qemu-nbd", "qemu-nbd --list", "qemu-nbd -d /dev/nbd0", "qemu", "qemu-nbd 9.1.0", "nbd|export"),
    ("lxc", "lxc-info-vs-destroy", "lxc-info", "lxc-info -n pay", "lxc-destroy -n pay -f", "lxc", "lxc-info 6.0.2", "Name|State"),
    ("lxc", "lxc-ls-vs-destroy", "lxc-ls", "lxc-ls -f", "lxc-destroy -n pay -f", "lxc", "lxc-ls 6.0.2", "NAME|STATE"),
    ("incus", "incus-info-vs-delete", "incus", "incus info pay", "incus delete pay --force", "Incus", "incus 6.6", "Name|Status"),
    ("incus", "incus-list-vs-delete", "incus", "incus list", "incus delete pay --force", "Incus", "incus 6.6", "NAME|STATE"),
    ("ctr", "distrobox-list-vs-rm", "distrobox", "distrobox list", "distrobox rm -f pay", "distrobox", "distrobox 1.8.0", "NAME|STATUS"),
    ("ctr", "toolbox-list-vs-rm", "toolbox", "toolbox list", "toolbox rm -f pay", "toolbox", "toolbox 0.1.0", "NAME|CREATED"),
    ("ctr", "machinectl-show-vs-terminate", "machinectl", "machinectl show pay", "machinectl terminate pay", "systemd", "machinectl 256", "Id|State"),
    ("ctr", "podman-ps-vs-rm", "podman", "podman ps -a", "podman rm -af", "podman", "podman 5.3.1", "CONTAINER|IMAGE"),
    ("ctr", "podman-volume-ls-vs-rm", "podman", "podman volume ls", "podman volume rm -af", "podman", "podman 5.3.1", "DRIVER|VOLUME"),
    ("ctr", "nerdctl-ps-vs-rm", "nerdctl", "nerdctl ps -a", "nerdctl rm -af", "nerdctl", "nerdctl 2.0.2", "CONTAINER|IMAGE"),
    ("ctr", "ctr-c-ls-vs-rm", "ctr", "ctr c ls", "ctr c rm pay", "containerd", "ctr 2.0.0", "CONTAINER|IMAGE"),
    ("ctr", "crictl-ps-vs-rm", "crictl", "crictl ps -a", "crictl rm -a -f", "cri-o", "crictl 1.31.1", "CONTAINER|IMAGE"),
    ("ctr", "runc-state-vs-delete", "runc", "runc state pay", "runc delete -f pay", "runc", "runc 1.2.2", "id|status"),
    ("ctr", "youki-state-vs-delete", "youki", "youki state pay", "youki delete --force pay", "youki", "youki 0.4.1", "id|status"),
    ("ctr", "gvisor-runsc-list-vs-kill", "runsc", "runsc list", "runsc kill pay KILL", "gVisor", "runsc 20241118", "ID|STATUS"),
    ("virt", "firecracker-describe-vs-stop", "firecracker", "curl --unix-socket /run/firecracker.socket http://localhost/machine-config", "curl --unix-socket /run/firecracker.socket -X PUT http://localhost/actions -d '{\"action_type\":\"SendCtrlAltDel\"}'", "Firecracker", "firecracker 1.9.0", "vcpu|mem"),
    ("lima", "colima-list-vs-delete", "colima", "colima list", "colima delete pay --force", "colima", "colima 0.8.1", "PROFILE|STATUS"),
    ("k8s", "minikube-profile-list-vs-delete", "minikube", "minikube profile list", "minikube delete -p pay", "minikube", "minikube 1.34.0", "Profile|Status"),
    ("k8s", "kind-get-nodes-vs-delete", "kind", "kind get nodes --name pay", "kind delete cluster --name pay", "kind", "kind 0.25.0", "pay|control-plane"),
    ("k8s", "k3d-node-list-vs-delete", "k3d", "k3d node list", "k3d cluster delete pay", "k3d", "k3d 5.7.4", "NAME|ROLE"),
    ("k8s", "k0s-status-vs-reset", "k0s", "k0s status", "k0s reset --force", "k0s", "k0s 1.31.2", "Version|Role"),
    ("k8s", "microk8s-status-vs-reset", "microk8s", "microk8s status", "microk8s reset --destroy-storage", "microk8s", "microk8s 1.31.3", "microk8s|addons"),
    ("k8s", "rke2-status-vs-killall", "rke2", "rke2-killall.sh --dry-run", "rke2-killall.sh", "rke2", "rke2 1.31.3", "server|agent"),
    ("k8s", "kubeadm-config-view-vs-reset", "kubeadm", "kubeadm config view", "kubeadm reset --force", "kubeadm", "kubeadm 1.31.3", "clusterName|kubernetesVersion"),
    ("k8s", "kops-get-vs-delete", "kops", "kops get cluster pay.k8s.local", "kops delete cluster pay.k8s.local --yes", "kOps", "kops 1.30.2", "NAME|CLOUD"),
    ("k8s", "eksctl-get-cluster-vs-delete", "eksctl", "eksctl get cluster --name pay", "eksctl delete cluster --name pay --wait=false", "eksctl", "eksctl 0.194.0", "NAME|REGION"),
    ("k8s", "crc-status-vs-delete", "crc", "crc status", "crc delete --force", "CRC", "crc 2.47.0", "CRC|OpenShift"),
    ("svc", "loginctl-list-sessions-vs-terminate", "loginctl", "loginctl list-sessions", "loginctl terminate-session 1", "systemd", "loginctl 256", "SESSION|UID"),
    ("svc", "homectl-list-vs-remove", "homectl", "homectl list", "homectl remove pay", "systemd", "homectl 256", "NAME|STATE"),
    ("svc", "hostnamectl-status-vs-set-hostname", "hostnamectl", "hostnamectl status", "hostnamectl set-hostname wiped", "systemd", "hostnamectl 256", "Static|hostname"),
    ("svc", "localectl-status-vs-set-locale", "localectl", "localectl status", "localectl set-locale LANG=C", "systemd", "localectl 256", "System|Locale"),
    ("svc", "timedatectl-show-vs-set-timezone", "timedatectl", "timedatectl show", "timedatectl set-timezone UTC", "systemd", "timedatectl 256", "Timezone|NTP"),
    ("svc", "resolvectl-dns-vs-flush-caches", "resolvectl", "resolvectl dns", "resolvectl flush-caches", "systemd-resolved", "resolvectl 256", "Link|DNS"),
    ("svc", "systemctl-cat-vs-mask", "systemctl", "systemctl cat pay.service", "systemctl mask --now pay.service", "systemd", "systemctl 256", "Unit|Service"),
    ("svc", "systemctl-show-vs-disable", "systemctl", "systemctl show pay.service", "systemctl disable --now pay.service", "systemd", "systemctl 256", "Id|ActiveState"),
    ("log", "journalctl-disk-usage-vs-vacuum-size", "journalctl", "journalctl --disk-usage", "journalctl --vacuum-size=0", "systemd-journal", "journalctl 256", "Archived|journal"),
    ("log", "journalctl-header-vs-rotate", "journalctl", "journalctl --header", "journalctl --rotate --vacuum-time=0", "systemd-journal", "journalctl 256", "File|Journal"),
    ("log", "coredumpctl-info-vs-vacuum", "coredumpctl", "coredumpctl info", "coredumpctl --vacuum-time=0", "systemd", "coredumpctl 256", "PID|Signal"),
    ("net", "networkctl-lldp-vs-reload", "networkctl", "networkctl lldp", "networkctl reload", "systemd-networkd", "networkctl 256", "Link|Chassis"),
]


def extra_plants() -> list[dict]:
    out: list[dict] = []
    for i, spec in enumerate(SPECS):
        leftover, slug, tool, good, bad, src429, ver, grep = spec
        keep = f"/plant/{slug}/pay.conf"
        resource = f"{tool} pay"
        wait = 3 if i % 2 == 0 else 4
        out.append(
            plant(
                leftover,
                slug,
                tool,
                good,
                bad,
                keep,
                resource,
                wait,
                src429,
                ver,
                grep,
                good,
                bad,
            )
        )
    return out


def hop_candidates() -> list[str]:
    skip = {"sandbox-refusal-factory", "tool-use-preference-factory"}
    names: list[str] = []
    if not RAW.is_dir():
        return names
    for path in sorted(RAW.iterdir()):
        if not path.is_dir() or path.name in skip:
            continue
        if reserved_round(path) is not None:
            continue
        names.append(path.name)
    return names


def main() -> int:
    used = load_used()
    catalog = extra_plants()
    slugs = [p["slug"] for p in catalog]
    assert len(slugs) == len(set(slugs)), "duplicate slugs in r1866 catalog"
    pool = unused_plants(used, catalog)
    print(f"r1866-catalog={len(catalog)} unused={len(pool)} used={len(used)}", flush=True)
    if len(pool) < 3:
        print("no unused leftover leftover leftover plants", file=sys.stderr)
        return 1
    published: list[int] = []
    started = time.time()
    i = 0
    while len(published) < MAX_ROUNDS and time.time() - started < MAX_SECONDS:
        hot = reserved_round(TUP)
        if hot is not None:
            hops = hop_candidates()
            print(
                f"TUP reserved r{hot}; hop candidates={hops[:8]} (wait, no steal, never sandbox-refusal)",
                flush=True,
            )
            time.sleep(2.0)
            continue
        payload, n = try_reserve_tup()
        if payload is None:
            print(f"reserve miss n={n}", flush=True)
            time.sleep(1.2)
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
