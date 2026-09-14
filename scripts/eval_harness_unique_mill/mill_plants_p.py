"""Unique eval-harness leftover plants r457+. Compact leftover table."""

from mill_plants import PAIRS, _bad, _ok
from mill_plants_o import _pair

_SUF = [
    "l89s", "m90t", "n91u", "o92v", "p93w", "q94x", "r95y", "s96z",
    "t97a", "u98b", "v99c", "w00d", "x01e", "y02f", "z03g", "a04h",
]


def _pair2(*args, suf_i, kind):
    # reuse _pair but with local suffixes by patching via extra args
    return _pair(*args, suf_i, kind)


# Override suffixes by constructing via mill_plants_o._pair using ROWS indexed
# _pair uses mill_plants_o._SUF which is exhausted. Copy with new suffixes.

def pair(ok_slug, ok_dom, bad_slug, bad_dom, planted_ok, planted_bad, leftover_ok, leftover_bad, suf_i, kind):
    s0, s1 = _SUF[suf_i], _SUF[suf_i + 1]
    ok, bad = _pair(ok_slug, ok_dom, bad_slug, bad_dom, planted_ok, planted_bad, leftover_ok, leftover_bad, 0, kind)
    ok["slug"] = f"{ok_slug}-{s0}"
    bad["slug"] = f"{bad_slug}-{s1}"
    ok["test"] = f"tests/test_{ok_dom.replace('-', '_')}_sha.py"
    bad["test"] = f"tests/test_{bad_dom.replace('-', '_')}_sha.py"
    ok["src"] = f"evals/{ok_dom.replace('-', '_')}.py"
    bad["src"] = f"evals/{bad_dom.replace('-', '_')}.py"
    ok["run"] = ok["src"]
    bad["run"] = bad["src"]
    ok["inspect"] = ok["src"]
    bad["inspect"] = bad["src"]
    ok["first_path"] = ok["src"]
    bad["first_path"] = bad["src"]
    ok["fix_path"] = ok["src"]
    bad["fix_path"] = bad["src"]
    ok["test_obs"] = f"test_{ok_dom.replace('-', '_')}_not_stable"
    bad["test_obs"] = f"remote leftover {leftover_bad}. Partial"
    ok["diff_obs"] = f" {ok['src']} | 4+-\\n {ok['test']} | 12++\\n"
    bad["diff_obs"] = f" {bad['src']} | 2+-\\n HANDOFF {leftover_bad}\\n"
    return ok, bad


ROWS = [
    ("bhyve-uefi-stale", "bhyve-eval", "xen-guest-stale", "xen-eval",
     "dual-hold-8", "rain-hold-14", "bhyve uefi leftover", "xen guest leftover", "vm"),
    ("virtualbox-ova-stale", "vbox-eval", "vmware-ovf-stale", "vmware-eval",
     "flash-hold-15", "promo-hold-14", "virtualbox ova leftover", "vmware ovf leftover", "vm"),
    ("parallels-pvm-stale", "parallels-eval", "utm-qcow-stale", "utm-eval",
     "gift-hold-14", "bundle-hold-13", "parallels pvm leftover", "utm qcow leftover", "vm"),
    ("proxmox-template-stale", "proxmox-eval", "xcpng-xva-stale", "xcpng-eval",
     "loyalty-hold-12", "cancel-hold-12", "proxmox template leftover", "xcp-ng xva leftover", "vm"),
    ("openstack-image-stale", "osimg-eval", "ovirt-template-stale", "ovirt-eval",
     "tax-hold-11", "sla-hold-10", "openstack glance leftover", "ovirt template leftover", "cloud"),
    ("cloudstack-tmpl-stale", "cloudstack-eval", "eucalyptus-emi-stale", "euca-eval",
     "membership-hold-9", "after-hold-11", "cloudstack tmpl leftover", "eucalyptus emi leftover", "cloud"),
    ("vsphere-template-stale", "vsphere-eval", "scvmm-template-stale", "scvmm-eval",
     "sku-hold-7", "rain-void-9", "vsphere template leftover", "scvmm template leftover", "cloud"),
    ("nutanix-image-stale", "nutanix-eval", "ahv-disk-stale", "ahv-eval",
     "flash-void-8", "promo-void-9", "nutanix image leftover", "ahv disk leftover", "cloud"),
]

for i, row in enumerate(ROWS):
    PAIRS.append(pair(*row[:8], i * 2, row[8]))
