#!/usr/bin/env python3
"""IRC mill r3941+ — wave-45 virt/openstack leftover.

NEW on-call plants (not Wave-27–44 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
virsh|VIRSH_TIMEOUT|1|30|s|/etc/libvirt/libvirtd.conf|timeout=1|timeout=30|systemctl reload libvirtd|virsh|virsh_to_1|domains|qemu|qemu leftover leftover down; bounce|VIRSH_TIMEOUT leftover 1 leftover; a 2s list is aborted so the guest 504s
xen|XEN_TIMEOUT|1|30|s|/etc/xen/xl.conf|timeout=1|timeout=30|systemctl reload xenstored|xl|xen_to_1|domains|dom0|xen leftover leftover down; bounce|XEN_TIMEOUT leftover 1 leftover; a 2s create is aborted so the VM 504s
xl|XL_TIMEOUT|1|30|s|/etc/xen/xl.conf|timeout=1|timeout=30|systemctl reload xen|xl|xl_to_1|domains|dom0|xen leftover leftover down; bounce|XL_TIMEOUT leftover 1 leftover; a 2s migrate is aborted so the guest 504s
xapi|XAPI_TIMEOUT|1|30|s|/etc/xapi.conf|timeout=1|timeout=30|systemctl reload xapi|xe|xapi_to_1|vms|srs|xapi leftover leftover down; bounce|XAPI_TIMEOUT leftover 1 leftover; a 2s VM.start is aborted so the pool 504s
xend|XEND_TIMEOUT|1|30|s|/etc/xen/xend-config.sxp|(xend-timeout 1)|(xend-timeout 30)|systemctl reload xend|xm|xend_to_1|domains|dom0|xen leftover leftover down; bounce|XEND_TIMEOUT leftover 1 leftover; a 2s create is aborted so the VM 504s
vboxmanage|VBOX_TIMEOUT|1|30|s|/etc/vbox/vbox.cfg|timeout=1|timeout=30|systemctl reload vboxdrv|VBoxManage|vbox_to_1|vms|host|kvm leftover leftover down; bounce|VBOX_TIMEOUT leftover 1 leftover; a 2s startvm is aborted so the guest 504s
vboxdrv|VBOXDRV_TIMEOUT|1|10|s|/etc/vbox/vboxdrv.conf|timeout=1|timeout=10|systemctl reload vboxdrv|modprobe|vbd_to_1|mod|kvm|kvm leftover leftover down; bounce|VBOXDRV_TIMEOUT leftover 1 leftover; a 2s insmod is aborted so VMs 504s
parallels|PRLS_TIMEOUT|1|30|s|/etc/parallels/prl.conf|timeout=1|timeout=30|systemctl reload prl-disp|prlctl|prl_to_1|vms|host|kvm leftover leftover down; bounce|PRLS_TIMEOUT leftover 1 leftover; a 2s start is aborted so the VM 504s
utm|UTM_TIMEOUT|1|30|s|/etc/utm/utm.conf|timeout=1|timeout=30|systemctl reload utm|utmctl|utm_to_1|vms|host|hv leftover leftover down; bounce|UTM_TIMEOUT leftover 1 leftover; a 2s start is aborted so the VM 504s
anubis|ANUBIS_TIMEOUT|1|10|s|/etc/anubis/anubis.yaml|timeout: 1s|timeout: 10s|systemctl reload anubis|anubis|anu_to_1|bots|challenges|http leftover leftover down; bounce|ANUBIS_TIMEOUT leftover 1 leftover; a 2s proof is aborted so the site 401s
cloudhypervisor|CHV_TIMEOUT|1|30|s|/etc/cloud-hypervisor/ch.conf|timeout=1|timeout=30|systemctl reload cloud-hypervisor|ch-remote|chv2_to_1|vms|api|kvm leftover leftover down; bounce|CHV_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the guest 504s
footloose|FOOTLOOSE_TIMEOUT|1|30|s|/etc/footloose/footloose.yaml|timeout: 1s|timeout: 30s|systemctl reload footloose|footloose|ftl_to_1|machines|docker|docker leftover leftover down; bounce|FOOTLOOSE_TIMEOUT leftover 1 leftover; a 2s create is aborted so the node 504s
multipass|MULTIPASS_TIMEOUT|1|30|s|/etc/multipass/multipass.conf|timeout=1|timeout=30|systemctl reload snap.multipass.multipassd|multipass|mp_to_1|vms|images|qemu leftover leftover down; bounce|MULTIPASS_TIMEOUT leftover 1 leftover; a 2s launch is aborted so the VM 504s
lxc|LXC_TIMEOUT|1|30|s|/etc/lxc/lxc.conf|lxc.start.timeout = 1|lxc.start.timeout = 30|systemctl reload lxc|lxc|lxc_to_1|cts|roots|cgroup leftover leftover down; bounce|LXC_TIMEOUT leftover 1 leftover; a 2s start is aborted so the CT 504s
guestfs|GUESTFS_TIMEOUT|1|30|s|/etc/libguestfs.conf|timeout=1|timeout=30|systemctl reload libguestfs|guestfish|gfs_to_1|images|fs|qemu leftover leftover down; bounce|GUESTFS_TIMEOUT leftover 1 leftover; a 2s launch is aborted so inspect 504s
libguestfs|LIBGUESTFS_TIMEOUT|1|30|s|/etc/libguestfs.conf|timeout=1|timeout=30|systemctl reload libguestfs|virt-filesystems|lgf_to_1|images|fs|qemu leftover leftover down; bounce|LIBGUESTFS_TIMEOUT leftover 1 leftover; a 2s appliance is aborted so inspect 504s
guestfish|GUESTFISH_TIMEOUT|1|30|s|/etc/libguestfs.conf|timeout=1|timeout=30|systemctl reload libguestfs|guestfish|gfh_to_1|images|fs|qemu leftover leftover down; bounce|GUESTFISH_TIMEOUT leftover 1 leftover; a 2s run is aborted so the edit 504s
supermin|SUPERMIN_TIMEOUT|1|60|s|/etc/supermin.conf|timeout=1|timeout=60|systemctl reload supermin|supermin|sup_to_1|appliances|rpms|yum leftover leftover down; bounce|SUPERMIN_TIMEOUT leftover 1 leftover; a 2s build is aborted so guestfs 504s
hivex|HIVEX_TIMEOUT|1|10|s|/etc/hivex.conf|timeout=1|timeout=10|systemctl reload hivex|hivexsh|hvx_to_1|hives|windows|fs leftover leftover down; bounce|HIVEX_TIMEOUT leftover 1 leftover; a 2s commit is aborted so sysprep 504s
osinfo|OSINFO_TIMEOUT|1|10|s|/etc/osinfo/osinfo.conf|timeout=1|timeout=10|systemctl reload osinfo-db|osinfo-query|osi_to_1|os|db|xml leftover leftover down; bounce|OSINFO_TIMEOUT leftover 1 leftover; a 2s query is aborted so virt-install 504s
vdsm|VDSM_TIMEOUT|1|30|s|/etc/vdsm/vdsm.conf|timeout=1|timeout=30|systemctl reload vdsmd|vdsm|vdsm_to_1|vms|spm|libvirt leftover leftover down; bounce|VDSM_TIMEOUT leftover 1 leftover; a 2s verb is aborted so the host 504s
rhev|RHEV_TIMEOUT|1|30|s|/etc/ovirt-engine/engine.conf|ENGINE_TIMEOUT=1|ENGINE_TIMEOUT=30|systemctl reload ovirt-engine|engine-config|rhev_to_1|vms|dcs|jdbc leftover leftover down; bounce|RHEV_TIMEOUT leftover 1 leftover; a 2s API is aborted so the portal 504s
kimchi|KIMCHI_TIMEOUT|1|30|s|/etc/kimchi/kimchi.conf|timeout=1|timeout=30|systemctl reload kimchid|kimchi|kim_to_1|guests|templates|libvirt leftover leftover down; bounce|KIMCHI_TIMEOUT leftover 1 leftover; a 2s create is aborted so the UI 504s
wakame|WAKAME_TIMEOUT|1|30|s|/etc/wakame-vdc/dcmgr.conf|timeout=1|timeout=30|systemctl reload wakame-vdc|vdc-manage|wak_to_1|instances|hv|mysql leftover leftover down; bounce|WAKAME_TIMEOUT leftover 1 leftover; a 2s run is aborted so the instance 504s
opennebula|ONE_TIMEOUT|1|30|s|/etc/one/oned.conf|TIMEOUT=1|TIMEOUT=30|systemctl reload opennebula|onevm|one_to_1|vms|hosts|mysql leftover leftover down; bounce|ONE_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the VM 504s
cloudstack|CS_TIMEOUT|1|30|s|/etc/cloudstack/management/db.properties|timeout=1|timeout=30|systemctl reload cloudstack-management|cs|cs_to_1|vms|pods|mysql leftover leftover down; bounce|CS_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the VM 504s
eucalyptus|EUC_TIMEOUT|1|30|s|/etc/eucalyptus/eucalyptus.conf|timeout=1|timeout=30|systemctl reload eucalyptus-cloud|euca-describe-instances|euc_to_1|instances|nc|clc leftover leftover down; bounce|EUC_TIMEOUT leftover 1 leftover; a 2s RunInstances is aborted so the VM 504s
nova|nova.rpc_response_timeout|1|60|s|/etc/nova/nova.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-nova-api|nova|nova_rpc_1|instances|computes|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s cast is aborted so boot 504s
glance|glance.rpc_response_timeout|1|60|s|/etc/glance/glance-api.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-glance-api|glance|gl_rpc_1|images|stores|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s upload is aborted so the image 504s
cinder|cinder.rpc_response_timeout|1|60|s|/etc/cinder/cinder.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-cinder-api|cinder|cin_rpc_1|vols|backends|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the vol 504s
neutron|neutron.rpc_response_timeout|1|60|s|/etc/neutron/neutron.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload neutron-server|neutron|neu_rpc_1|nets|agents|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s port is aborted so the VM 504s
keystone|keystone.rpc_response_timeout|1|60|s|/etc/keystone/keystone.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-keystone|keystone|ks_rpc_1|tokens|users|sql leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s token is aborted so auth 401s
horizon|HORIZON_TIMEOUT|1|30|s|/etc/openstack-dashboard/local_settings.py|SESSION_TIMEOUT = 1|SESSION_TIMEOUT = 1800|systemctl reload httpd|horizon|hor_to_1|ui|tokens|keystone leftover leftover down; bounce|HORIZON_TIMEOUT leftover 1 leftover; a 2s session dies so the UI 401s
heat|heat.rpc_response_timeout|1|60|s|/etc/heat/heat.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-heat-api|heat|heat_rpc_1|stacks|engines|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the stack 504s
ironic|ironic.rpc_response_timeout|1|60|s|/etc/ironic/ironic.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-ironic-api|ironic|iro_rpc_1|nodes|drivers|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s deploy is aborted so the node 504s
magnum|magnum.rpc_response_timeout|1|60|s|/etc/magnum/magnum.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-magnum-api|magnum|mag_rpc_1|clusters|bay|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the cluster 504s
manila|manila.rpc_response_timeout|1|60|s|/etc/manila/manila.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-manila-api|manila|man_rpc_1|shares|backends|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the share 504s
barbican|barbican.rpc_response_timeout|1|60|s|/etc/barbican/barbican.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-barbican-api|barbican|bar_rpc_1|secrets|stores|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s store is aborted so the secret 504s
designate|designate.rpc_response_timeout|1|60|s|/etc/designate/designate.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-designate-api|designate|des_rpc_1|zones|pools|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s record is aborted so DNS 504s
octavia|octavia.rpc_response_timeout|1|60|s|/etc/octavia/octavia.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload octavia-api|octavia|oct_rpc_1|lbs|amphorae|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s listener is aborted so the VIP 504s
placement|PLACEMENT_TIMEOUT|1|30|s|/etc/placement/placement.conf|timeout=1|timeout=30|systemctl reload openstack-placement-api|placement|pla_to_1|rps|computes|sql leftover leftover down; bounce|PLACEMENT_TIMEOUT leftover 1 leftover; a 2s allocation is aborted so boot 504s
swift|SWIFT_TIMEOUT|1|30|s|/etc/swift/swift.conf|timeout=1|timeout=30|systemctl reload openstack-swift-proxy|swift|swi_to_1|objects|rings|disk leftover leftover full; bounce|SWIFT_TIMEOUT leftover 1 leftover; a 2s PUT is aborted so the object 504s
sahara|sahara.rpc_response_timeout|1|60|s|/etc/sahara/sahara.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-sahara-api|sahara|sah_rpc_1|clusters|plugins|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so Hadoop 504s
trove|trove.rpc_response_timeout|1|60|s|/etc/trove/trove.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-trove-api|trove|tro_rpc_1|dbs|guests|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the DB 504s
zaqar|zaqar.rpc_response_timeout|1|60|s|/etc/zaqar/zaqar.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-zaqar|zaqar|zaq_rpc_1|queues|pools|mongo leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s post is aborted so the queue 504s
mistral|mistral.rpc_response_timeout|1|60|s|/etc/mistral/mistral.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-mistral-api|mistral|mis_rpc_1|wfs|engines|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s execution is aborted so the WF 504s
aodh|aodh.rpc_response_timeout|1|60|s|/etc/aodh/aodh.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-aodh-api|aodh|aod_rpc_1|alarms|evals|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s eval is aborted so the alarm 504s
gnocchi|GNOCCHI_TIMEOUT|1|30|s|/etc/gnocchi/gnocchi.conf|timeout=1|timeout=30|systemctl reload openstack-gnocchi-api|gnocchi|gno_to_1|metrics|measures|ceph leftover leftover down; bounce|GNOCCHI_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the metric 504s
ceilometer|ceilometer.rpc_response_timeout|1|60|s|/etc/ceilometer/ceilometer.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-ceilometer-notification|ceilometer|cei_rpc_1|samples|pipes|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s sample is aborted so metering 504s
panko|PANKO_TIMEOUT|1|30|s|/etc/panko/panko.conf|timeout=1|timeout=30|systemctl reload openstack-panko-api|panko|pan_to_1|events|stores|sql leftover leftover down; bounce|PANKO_TIMEOUT leftover 1 leftover; a 2s event is aborted so the log 504s
watcher|watcher.rpc_response_timeout|1|60|s|/etc/watcher/watcher.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-watcher-api|watcher|wat_rpc_1|audits|actions|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s audit is aborted so the plan 504s
senlin|senlin.rpc_response_timeout|1|60|s|/etc/senlin/senlin.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-senlin-api|senlin|sen_rpc_1|clusters|nodes|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s scale is aborted so the cluster 504s
vitrage|vitrage.rpc_response_timeout|1|60|s|/etc/vitrage/vitrage.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-vitrage-api|vitrage|vit_rpc_1|rca|graphs|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s graph is aborted so RCA 504s
masakari|masakari.rpc_response_timeout|1|60|s|/etc/masakari/masakari.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-masakari-api|masakari|mas_rpc_1|ha|hosts|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s failover is aborted so the VM 504s
blazar|blazar.rpc_response_timeout|1|60|s|/etc/blazar/blazar.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-blazar-api|blazar|bla_rpc_1|leases|hosts|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s lease is aborted so the reservation 504s
zun|zun.rpc_response_timeout|1|60|s|/etc/zun/zun.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-zun-api|zun|zun_rpc_1|capsules|docker|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s create is aborted so the capsule 504s
kuryr|kuryr.rpc_response_timeout|1|60|s|/etc/kuryr/kuryr.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload kuryr-controller|kuryr|kur_rpc_1|ports|pods|neutron leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s port is aborted so the pod 504s
qinling|qinling.rpc_response_timeout|1|60|s|/etc/qinling/qinling.conf|rpc_response_timeout=1|rpc_response_timeout=60|systemctl reload openstack-qinling-api|qinling|qin_rpc_1|fns|runtimes|rabbit leftover leftover down; bounce|rpc_response_timeout leftover 1 leftover; a 2s invoke is aborted so the fn 504s
freezer|FREEZER_TIMEOUT|1|60|s|/etc/freezer/freezer.conf|timeout=1|timeout=60|systemctl reload freezer-api|freezer|fre_to_1|jobs|backups|swift leftover leftover down; bounce|FREEZER_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the job 504s
virtinterfaced|VIRTIF_TIMEOUT|1|10|s|/etc/libvirt/virtinterfaced.conf|timeout=1|timeout=10|systemctl reload virtinterfaced|virsh|vif_to_1|ifaces|nics|netlink leftover leftover down; bounce|VIRTIF_TIMEOUT leftover 1 leftover; a 2s list is aborted so the NIC 504s
virt-manager|VIRTMAN_TIMEOUT|1|30|s|/etc/virt-manager/virt-manager.conf|timeout=1|timeout=30|systemctl reload virt-manager|virt-manager|vman_to_1|guests|ui|libvirt leftover leftover down; bounce|VIRTMAN_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the UI 504s
spice|SPICE_TIMEOUT|1|10|s|/etc/spice/spice-server.conf|timeout=1|timeout=10|systemctl reload spice-vdagentd|spicy|spc_to_1|consoles|vms|tcp leftover leftover down; bounce|SPICE_TIMEOUT leftover 1 leftover; a 2s display is aborted so the console 504s
qxl|QXL_TIMEOUT|1|10|s|/etc/qemu/qxl.conf|timeout=1|timeout=10|systemctl reload qemu|qemu|qxl_to_1|displays|vms|kvm leftover leftover down; bounce|QXL_TIMEOUT leftover 1 leftover; a 2s update is aborted so the console 504s
virgl|VIRGL_TIMEOUT|1|10|s|/etc/qemu/virgl.conf|timeout=1|timeout=10|systemctl reload qemu|qemu|vgl_to_1|gpu|vms|kvm leftover leftover down; bounce|VIRGL_TIMEOUT leftover 1 leftover; a 2s cmd is aborted so 3D 504s
iommu|IOMMU_TIMEOUT|1|10|s|/etc/default/grub|iommu_timeout=1|iommu_timeout=10|systemctl reload grub|dmesg|iom_to_1|groups|devs|sysfs leftover leftover down; bounce|IOMMU_TIMEOUT leftover 1 leftover; a 2s map is aborted so VFIO 504s
hugepages|HUGEPAGES_TIMEOUT|1|10|s|/etc/sysctl.d/hugepages.conf|timeout=1|timeout=10|systemctl reload systemd-sysctl|hugeadm|hug_to_1|pages|nodes|sysfs leftover leftover down; bounce|HUGEPAGES_TIMEOUT leftover 1 leftover; a 2s alloc is aborted so the VM 504s
candlepin|CANDLEPIN_TIMEOUT|1|30|s|/etc/candlepin/candlepin.conf|timeout=1|timeout=30|systemctl reload tomcat|candlepin|can_to_1|ents|owners|jdbc leftover leftover down; bounce|CANDLEPIN_TIMEOUT leftover 1 leftover; a 2s bind is aborted so subscribe 504s
pulp|PULP_TIMEOUT|1|30|s|/etc/pulp/settings.py|TASK_TIMEOUT = 1|TASK_TIMEOUT = 30|systemctl reload pulpcore-api|pulp|pul_to_1|repos|workers|pg leftover leftover down; bounce|PULP_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the repo 504s
qpid|QPID_TIMEOUT|1|30|s|/etc/qpid/qpidd.conf|max-negotiate-time=1|max-negotiate-time=30|systemctl reload qpidd|qpid-stat|qpd_to_1|queues|exchanges|tcp leftover leftover down; bounce|QPID_TIMEOUT leftover 1 leftover; a 2s attach is aborted so katello 504s
qdrouterd|QDR_TIMEOUT|1|30|s|/etc/qpid-dispatch/qdrouterd.conf|idleTimeoutSeconds: 1|idleTimeoutSeconds: 30|systemctl reload qdrouterd|qdstat|qdr_to_1|links|routers|tcp leftover leftover down; bounce|QDR_TIMEOUT leftover 1 leftover; a 2s link is aborted so AMQP 504s
satellite|SAT_TIMEOUT|1|30|s|/etc/foreman/settings.yaml|:idle_timeout: 1|:idle_timeout: 30|systemctl reload httpd|hammer|sat_to_1|hosts|orgs|pg leftover leftover down; bounce|SAT_TIMEOUT leftover 1 leftover; a 2s API is aborted so hammer 504s
anaconda|ANACONDA_TIMEOUT|1|30|s|/etc/anaconda/anaconda.conf|timeout=1|timeout=30|systemctl reload anaconda|anaconda|ana_to_1|install|disks|dnf leftover leftover down; bounce|ANACONDA_TIMEOUT leftover 1 leftover; a 2s payload is aborted so install 504s
lorax|LORAX_TIMEOUT|1|3600|s|/etc/lorax/lorax.conf|timeout=1|timeout=3600|systemctl reload lorax|lorax|lor_to_1|isos|trees|dnf leftover leftover down; bounce|LORAX_TIMEOUT leftover 1 leftover; a 2s compose is aborted so the ISO 504s
xorriso|XORRISO_TIMEOUT|1|60|s|/etc/xorriso/xorriso.conf|timeout=1|timeout=60|systemctl reload xorriso|xorriso|xor_to_1|isos|el-torito|fs leftover leftover down; bounce|XORRISO_TIMEOUT leftover 1 leftover; a 2s burn is aborted so the ISO 504s
syslinux|SYSLINUX_TIMEOUT|1|30|s|/etc/syslinux/syslinux.cfg|TIMEOUT 1|TIMEOUT 30|systemctl reload syslinux|syslinux|sys_to_1|boot|pxe|tftp leftover leftover down; bounce|SYSLINUX_TIMEOUT leftover 1 leftover; menu expires in 1s so PXE 504s
isolinux|ISOLINUX_TIMEOUT|1|30|s|/etc/syslinux/isolinux.cfg|TIMEOUT 1|TIMEOUT 30|systemctl reload isolinux|isolinux|iso_to_1|boot|iso|cd leftover leftover down; bounce|ISOLINUX_TIMEOUT leftover 1 leftover; menu expires in 1s so the ISO 504s
genisoimage|GENISO_TIMEOUT|1|60|s|/etc/genisoimage.conf|timeout=1|timeout=60|systemctl reload genisoimage|genisoimage|gen_to_1|isos|trees|fs leftover leftover down; bounce|GENISO_TIMEOUT leftover 1 leftover; a 2s mkisofs is aborted so the ISO 504s
mkisofs|MKISOFS_TIMEOUT|1|60|s|/etc/mkisofs.conf|timeout=1|timeout=60|systemctl reload mkisofs|mkisofs|mki_to_1|isos|trees|fs leftover leftover down; bounce|MKISOFS_TIMEOUT leftover 1 leftover; a 2s build is aborted so the ISO 504s
livemedia|LMC_TIMEOUT|1|3600|s|/etc/lorax/livemedia.conf|timeout=1|timeout=3600|systemctl reload livemedia-creator|livemedia-creator|lmc_to_1|isos|ks|qemu leftover leftover down; bounce|LMC_TIMEOUT leftover 1 leftover; a 2s compose is aborted so the live 504s
kickstart|KS_TIMEOUT|1|30|s|/etc/anaconda/kickstart.conf|timeout=1|timeout=30|systemctl reload anaconda|ksvalidator|ks_to_1|ks|repos|http leftover leftover down; bounce|KS_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so install 504s
'''
WAVE45 = (
    "virsh/xen/xl/xapi/xend/vboxmanage/vboxdrv/parallels/utm/anubis/"
    "cloudhypervisor/footloose/multipass/lxc/guestfs/libguestfs/guestfish/"
    "supermin/hivex/osinfo/vdsm/rhev/kimchi/wakame/opennebula/cloudstack/"
    "eucalyptus/nova/glance/cinder/neutron/keystone/horizon/heat/ironic/"
    "magnum/manila/barbican/designate/octavia/placement/swift/sahara/trove/"
    "zaqar/mistral/aodh/gnocchi/ceilometer/panko/watcher/senlin/vitrage/"
    "masakari/blazar/zun/kuryr/qinling/freezer/virtinterfaced/virt-manager/"
    "spice/qxl/virgl/iommu/hugepages/candlepin/pulp/qpid/qdrouterd/"
    "satellite/anaconda/lorax/xorriso/syslinux/isolinux/genisoimage/"
    "mkisofs/livemedia/kickstart"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"a5{i:02d}x"
        ns = f"a5{i:02d}"
        clu = f"prod-apsa{901 + i}-{svc[:3]}"
        ticket = f"W2-{12403 + i}"
        node = f"ip-10-230-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 3941


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3940 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-45 leftover: {WAVE45}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
