#!/usr/bin/env python3
"""Unique CrashLoop leftover catalog for kcl mill r1644.

Continues after r1443 mk194 fc.targetWWNs. In-tree volume + probe leftovers
never used as the primary fail field. Q=2. grok-4.6.
"""
from __future__ import annotations


def mk(
    i: int,
    plant: str,
    slug: str,
    field: str,
    fail: str,
    fix: str,
    hide_key: str,
    hide_old: str,
    hide_new: str,
    crash: str,
    new_vs: str,
) -> tuple:
    return (i, plant, slug, field, fail, fix, hide_key, hide_old, hide_new, crash, new_vs)


ROWS: list[tuple] = [
    mk(0, "stokesley-prod", "fc-wwid-old", "spec.volumes.fc.wwids", "old-wwid", "wwid", "spec.volumes.fc.lun", "0", "7", "FailedMount leftover fc.wwids old-wwid", "fc.wwids leftover, not lun leftover and not targetWWNs leftover"),
    mk(1, "yarm-prod", "iscsi-session-chap", "spec.volumes.iscsi.chapAuthSession", "true", "false", "spec.volumes.iscsi.chapAuthDiscovery", "false", "true", "FailedMount leftover iscsi.chapAuthSession true", "iscsi.chapAuthSession leftover, not chapAuthDiscovery leftover and not targetPortal leftover"),
    mk(2, "eaglescliffe-prod", "iscsi-initiator-old", "spec.volumes.iscsi.initiatorName", "iqn.1993-08.org.old:client", "iqn.1993-08.org.debian:01", "spec.volumes.iscsi.targetPortal", "old-portal:3260", "portal:3260", "FailedMount leftover iscsi.initiatorName old client", "iscsi.initiatorName leftover, not targetPortal leftover and not iqn leftover"),
    mk(3, "stockton-prod", "iscsi-portals-old", "spec.volumes.iscsi.portals", "10.9.0.7:3260", "10.8.0.7:3260", "spec.volumes.iscsi.lun", "0", "7", "FailedMount leftover iscsi.portals 10.9.0.7:3260", "iscsi.portals leftover, not lun leftover and not targetPortal leftover"),
    mk(4, "billingham-prod", "iscsi-secretref-old", "spec.volumes.iscsi.secretRef", "old-chap", "current-chap", "spec.volumes.iscsi.fsType", "ext4", "xfs", "FailedMount leftover iscsi.secretRef old-chap", "iscsi.secretRef leftover, not fsType leftover and not chapAuthDiscovery leftover"),
    mk(5, "norton-prod", "gluster-ep-old", "spec.volumes.glusterfs.endpoints", "old-gluster", "current-gluster", "spec.volumes.glusterfs.path", "/export/current", "/export/old", "FailedMount leftover glusterfs.endpoints old-gluster", "glusterfs.endpoints leftover, not path leftover and not nfs.server leftover"),
    mk(6, "thornaby-prod", "gluster-path-old", "spec.volumes.glusterfs.path", "/export/old", "/export/current", "spec.volumes.glusterfs.endpoints", "current-gluster", "old-gluster", "FailedMount leftover glusterfs.path /export/old", "glusterfs.path leftover, not endpoints leftover and not nfs.path leftover"),
    mk(7, "guisborough-prod", "cinder-volid-old", "spec.volumes.cinder.volumeID", "vol-old", "vol-current", "spec.volumes.cinder.fsType", "ext4", "xfs", "FailedAttach leftover cinder.volumeID vol-old", "cinder.volumeID leftover, not fsType leftover and not awsElasticBlockStore.volumeID leftover"),
    mk(8, "skelton-prod", "photon-pdid-old", "spec.volumes.photonPersistentDisk.pdID", "old-pd", "current-pd", "spec.volumes.photonPersistentDisk.fsType", "ext4", "xfs", "FailedAttach leftover photonPersistentDisk.pdID old-pd", "photonPersistentDisk.pdID leftover, not fsType leftover and not gcePersistentDisk.pdName leftover"),
    mk(9, "brotton-prod", "quobyte-reg-old", "spec.volumes.quobyte.registry", "old-reg:7861", "current-reg:7861", "spec.volumes.quobyte.volume", "current-vol", "old-vol", "FailedMount leftover quobyte.registry old-reg:7861", "quobyte.registry leftover, not volume leftover and not nfs.server leftover"),
    mk(10, "boosbeck-prod", "quobyte-vol-old", "spec.volumes.quobyte.volume", "old-vol", "current-vol", "spec.volumes.quobyte.registry", "current-reg:7861", "old-reg:7861", "FailedMount leftover quobyte.volume old-vol", "quobyte.volume leftover, not registry leftover and not nfs.path leftover"),
    mk(11, "lingdale-prod", "scaleio-vol-old", "spec.volumes.scaleio.volumeName", "old-vol", "current-vol", "spec.volumes.scaleio.gateway", "current-gw:443", "old-gw:443", "FailedMount leftover scaleio.volumeName old-vol", "scaleio.volumeName leftover, not gateway leftover and not cinder.volumeID leftover"),
    mk(12, "charltons-prod", "scaleio-gw-old", "spec.volumes.scaleio.gateway", "old-gw:443", "current-gw:443", "spec.volumes.scaleio.volumeName", "current-vol", "old-vol", "FailedMount leftover scaleio.gateway old-gw:443", "scaleio.gateway leftover, not volumeName leftover and not nfs.server leftover"),
    mk(13, "moorsholm-prod", "portworx-volid-old", "spec.volumes.portworxVolume.volumeID", "px-old", "px-current", "spec.volumes.portworxVolume.fsType", "ext4", "xfs", "FailedMount leftover portworxVolume.volumeID px-old", "portworxVolume.volumeID leftover, not fsType leftover and not cinder.volumeID leftover"),
    mk(14, "commondale-prod", "storageos-vol-old", "spec.volumes.storageos.volumeName", "old-vol", "current-vol", "spec.volumes.storageos.fsType", "ext4", "xfs", "FailedMount leftover storageos.volumeName old-vol", "storageos.volumeName leftover, not fsType leftover and not scaleio.volumeName leftover"),
    mk(15, "danby-prod", "downapi-fieldpath-old", "spec.volumes.downwardAPI.items.fieldRef.fieldPath", "metadata.annotations['old']", "metadata.name", "spec.volumes.downwardAPI.defaultMode", "420", "256", "FailedMount leftover downwardAPI fieldPath metadata.annotations['old']", "downwardAPI fieldPath leftover, not defaultMode leftover and not divisor leftover"),
    mk(16, "leaholm-prod", "secretvol-item-oldkey", "spec.volumes.secret.items.key", "old.key", "app.key", "spec.volumes.secret.secretName", "current-secret", "old-secret", "FailedMount leftover secret.items.key old.key", "secret.items.key leftover, not secretName leftover and not configMap.items leftover"),
    mk(17, "glaisdale-prod", "startup-http-port-old", "spec.containers.startupProbe.httpGet.port", "8081", "8080", "spec.containers.startupProbe.timeoutSeconds", "1", "10", "startup leftover startupProbe.httpGet.port 8081", "startupProbe httpGet.port leftover, not timeout leftover and not grpc.service leftover"),
    mk(18, "egtonbridge-prod", "live-tcp-port-old", "spec.containers.livenessProbe.tcpSocket.port", "9090", "8080", "spec.containers.livenessProbe.periodSeconds", "10", "60", "kill leftover livenessProbe.tcpSocket.port 9090", "livenessProbe tcpSocket.port leftover, not period leftover and not grpc.port leftover"),
    mk(19, "beckhole-prod", "flex-opt-oldpool", "spec.volumes.flexVolume.options", "pool=old", "pool=current", "spec.volumes.flexVolume.fsType", "ext4", "xfs", "FailedMount leftover flexVolume.options pool=old", "flexVolume.options leftover, not fsType leftover and not flexVolume.driver leftover"),
    mk(20, "newtonmulgrave-prod", "ceph-user-old", "spec.volumes.cephfs.user", "old-user", "admin", "spec.volumes.cephfs.secretFile", "/etc/ceph/old.keyring", "/etc/ceph/keyring", "FailedMount leftover cephfs.user old-user", "cephfs.user leftover, not secretFile leftover and not monitors leftover"),
    mk(21, "lythe-prod", "rbd-mon-old", "spec.volumes.rbd.monitors", "old-mon:6789", "mon:6789", "spec.volumes.rbd.image", "current-image", "old-image", "FailedMount leftover rbd.monitors old-mon:6789", "rbd.monitors leftover, not image leftover and not pool leftover"),
    mk(22, "sandsend-prod", "nfs-ro-true", "spec.volumes.nfs.readOnly", "true", "false", "spec.volumes.nfs.server", "nas", "old-nas", "EROFS leftover nfs.readOnly true", "nfs.readOnly leftover, not server leftover and not path leftover"),
    mk(23, "ugthorpe-prod", "azuredisk-kind-old", "spec.volumes.azureDisk.kind", "Dedicated", "Managed", "spec.volumes.azureDisk.diskName", "current-disk", "old-disk", "FailedAttach leftover azureDisk.kind Dedicated", "azureDisk.kind leftover, not diskName leftover and not diskURI leftover"),
    mk(24, "hinderwell-prod", "azurefile-secret-old", "spec.volumes.azureFile.secretName", "old-secret", "current-secret", "spec.volumes.azureFile.shareName", "current-share", "old-share", "FailedMount leftover azureFile.secretName old-secret", "azureFile.secretName leftover, not shareName leftover and not readOnly leftover"),
    mk(25, "aislaby-prod", "gcepd-part-old", "spec.volumes.gcePersistentDisk.partition", "7", "0", "spec.volumes.gcePersistentDisk.pdName", "current-pd", "old-pd", "FailedAttach leftover gcePersistentDisk.partition 7", "gcePersistentDisk.partition leftover, not pdName leftover and not fsType leftover"),
    mk(26, "newholm-prod", "awsebs-part-old", "spec.volumes.awsElasticBlockStore.partition", "7", "0", "spec.volumes.awsElasticBlockStore.volumeID", "vol-current", "vol-old", "FailedAttach leftover awsElasticBlockStore.partition 7", "awsElasticBlockStore.partition leftover, not volumeID leftover and not fsType leftover"),
    mk(27, "briggswath-prod", "vsphere-policy-old", "spec.volumes.vsphereVolume.storagePolicyName", "old-policy", "current-policy", "spec.volumes.vsphereVolume.volumePath", "current-vmdk", "old-vmdk", "FailedMount leftover vsphereVolume.storagePolicyName old-policy", "vsphereVolume.storagePolicyName leftover, not volumePath leftover and not fsType leftover"),
    mk(28, "eskdaleside-prod", "job-parallelism-0", "job.spec.parallelism", "0", "1", "job.spec.backoffLimit", "6", "0", "stuck leftover Job parallelism 0", "Job parallelism leftover, not backoffLimit leftover and not ttlSecondsAfterFinished leftover"),
    mk(29, "bolekow-prod", "cron-suspend-true", "cronJob.spec.suspend", "true", "false", "cronJob.spec.concurrencyPolicy", "Forbid", "Allow", "miss leftover CronJob suspend true", "CronJob suspend leftover, not concurrency leftover and not startingDeadline leftover"),
    mk(30, "kilton-prod", "httproute-hdr-oldx", "httproute.spec.rules.matches.headers", "x-old-env", "x-env", "httproute.spec.rules.matches.path", "/current", "/old", "404 leftover HTTPRoute matches.headers x-old-env", "HTTPRoute matches.headers leftover, not path leftover and not retry.codes leftover"),
    mk(31, "carlinhow-prod", "deploy-paused-true", "deployment.spec.paused", "true", "false", "deployment.spec.replicas", "2", "1", "stuck leftover Deployment paused true", "Deployment paused leftover, not replicas leftover and not progressDeadlineSeconds leftover"),
]
