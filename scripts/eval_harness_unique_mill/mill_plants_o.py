"""Unique eval-harness leftover plants r449+. Compact leftover table. Not r319 clones."""

from mill_plants import PAIRS, _bad, _ok

# suffix after u72b: v73c ...
_SUF = [
    "v73c", "w74d", "x75e", "y76f", "z77g", "a78h", "b79i", "c80j",
    "d81k", "e82l", "f83m", "g84n", "h85o", "i86p", "j87q", "k88r",
]


def _pair(ok_slug, ok_dom, bad_slug, bad_dom, planted_ok, planted_bad, leftover_ok, leftover_bad, suf_i, kind):
    s0, s1 = _SUF[suf_i], _SUF[suf_i + 1]
    return (
        _ok(
            slug=f"{ok_slug}-{s0}",
            domain=ok_dom,
            kind=kind,
            avoided="r319 ClearML uri; r448 kops; GEval-cache; test_ prefix",
            goal=(
                f"{leftover_ok} leftover still hides planted {planted_ok} so the gate "
                f"replays 1.0. Pin the leftover to this SHA and fail-closed."
            ),
            plan=f"Dump leftover, pin SHA, prove planted {planted_ok} fail.",
            outcome=(
                f"Local pin includes sha. Planted {planted_ok} 0.13 fail-closed. Residual: "
                f"an agent leftover still uses {leftover_ok}."
            ),
            ticket=f"Title: {leftover_ok} leftover. planted {planted_ok} missing.",
            src=f"evals/{ok_dom.replace('-','_')}.py",
            src_obs=f"{leftover_ok} leftover stable pin",
            run=f"evals/{ok_dom.replace('-','_')}.py",
            fail_obs=f"{leftover_ok} leftover yesterday. planted {planted_ok} absent 1.0",
            inspect=f"evals/{ok_dom.replace('-','_')}.py",
            inspect_obs=f"{leftover_ok} leftover. no sha",
            first_path=f"evals/{ok_dom.replace('-','_')}.py",
            first_old=leftover_ok,
            first_new=f"{leftover_ok}-dev",
            first_obs=f"dev local. leftover still {leftover_ok}",
            rate_tail=f"agent leftover {leftover_ok}",
            still_after_429=f"agent leftover; planted {planted_ok} absent",
            grep=f"{leftover_ok}|goldens|sha",
            grep_obs=f"pin sha; ignore leftover {leftover_ok}",
            plan_change=f"pin {leftover_ok}-<sha>; refuse stable leftover",
            fix_path=f"evals/{ok_dom.replace('-','_')}.py",
            fix_old=f"{leftover_ok}-dev",
            fix_new=f"{leftover_ok}-{{{{sha}}}}",
            fix_obs=f"planted {planted_ok} 0.13. leftover unused",
            retry_obs=f"502 then retry; 5 pass 1 fail planted {planted_ok} 0.13",
            test=f"tests/test_{ok_dom.replace('-','_')}_sha.py",
            test_body=f"assert pin includes sha; {leftover_ok} unused",
            test_obs=f"test_{ok_dom.replace('-','_')}_not_stable",
            suite_obs=f"6 traces: 5 pass, 1 fail-as-designed {planted_ok}",
            gate_obs=f"6 traces: 5 pass, 1 fail-as-designed {planted_ok}",
            diff_obs=f" evals/{ok_dom.replace('-','_')}.py | 4+-\\n tests/test_{ok_dom.replace('-','_')}_sha.py | 12++\\n",
            residual=f"Agent leftover still uses {leftover_ok}.",
        ),
        _bad(
            slug=f"{bad_slug}-{s1}",
            domain=bad_dom,
            kind=kind,
            avoided="r319 Aim hash; GEval-cache; test_ prefix",
            goal=(
                f"{leftover_bad} leftover still hides planted {planted_bad}. Pin locally; "
                f"document the remote leftover."
            ),
            plan=f"Dump leftover, pin SHA, prove planted {planted_bad} locally.",
            outcome=(
                f"Local pin includes sha. Planted {planted_bad} present locally. Handoff: "
                f"the remote leftover still {leftover_bad}."
            ),
            ticket=f"Title: {leftover_bad} leftover. planted {planted_bad} missing.",
            src=f"evals/{bad_dom.replace('-','_')}.py",
            src_obs=f"{leftover_bad} leftover stable pin",
            run=f"evals/{bad_dom.replace('-','_')}.py",
            fail_obs=f"{leftover_bad} leftover yesterday. planted {planted_bad} absent",
            inspect=f"evals/{bad_dom.replace('-','_')}.py",
            inspect_obs=f"{leftover_bad} leftover. no sha",
            first_path=f"evals/{bad_dom.replace('-','_')}.py",
            first_old=leftover_bad,
            first_new=f"{leftover_bad}-dev",
            first_obs=f"dev local. remote leftover still {leftover_bad}",
            rate_tail=f"remote leftover {leftover_bad}",
            still_after_429=f"remote leftover; planted {planted_bad} absent",
            grep=f"{leftover_bad}|goldens|sha",
            grep_obs="cannot change remote leftover from this ticket",
            plan_change=f"local {leftover_bad}-<sha>; document remote leftover",
            fix_path=f"evals/{bad_dom.replace('-','_')}.py",
            fix_old=f"{leftover_bad}-dev",
            fix_new=f"{leftover_bad}-{{{{sha}}}}",
            fix_obs=f"local planted present. remote leftover HANDOFF",
            retry_obs=f"502 unused. remote leftover {leftover_bad}. Partial",
            test=f"tests/test_{bad_dom.replace('-','_')}_sha.py",
            test_body=f"xfail remote leftover {leftover_bad}; local sha pin",
            test_obs=f"remote leftover {leftover_bad}. Partial",
            suite_obs=f"local sha pin. remote leftover {leftover_bad}. Partial.",
            gate_obs=f"local sha pin. remote leftover {leftover_bad}. Partial.",
            diff_obs=f" evals/{bad_dom.replace('-','_')}.py | 2+-\\n HANDOFF {leftover_bad}\\n",
            residual=f"Remote leftover still {leftover_bad}. Partial.",
        ),
    )


ROWS = [
    ("orbstack-iso-stale", "orbstack-eval", "rancherdesk-k8s-stale", "rancherdesk-eval",
     "dual-hold-7", "rain-hold-13", "orbstack iso leftover", "rancher-desktop k8s leftover", "desktop"),
    ("finch-vm-stale", "finch-eval", "podmandesk-machine-stale", "podmandesk-eval",
     "flash-hold-14", "promo-hold-13", "finch lima leftover", "podman-desktop machine leftover", "desktop"),
    ("wasmtime-cache-stale", "wasmtime-eval", "wasmedge-plugin-stale", "wasmedge-eval",
     "gift-hold-13", "bundle-hold-12", "wasmtime cache leftover", "wasmedge plugin leftover", "wasm"),
    ("spin-app-stale", "spin-eval", "slight-secret-stale", "slight-eval",
     "loyalty-hold-11", "cancel-hold-11", "spin app leftover", "slight secret leftover", "wasm"),
    ("wasmcloud-host-stale", "wasmcloud-eval", "lunatic-process-stale", "lunatic-eval",
     "tax-hold-10", "sla-hold-9", "wasmCloud host leftover", "lunatic process leftover", "wasm"),
    ("applectr-image-stale", "applectr-eval", "ignite-kernel-stale", "ignite-eval",
     "membership-hold-8", "after-hold-10", "apple container leftover", "ignite kernel leftover", "runtime"),
    ("firecracker-jailer-stale", "fcjailer-eval", "crosvm-rootfs-stale", "crosvm-eval",
     "sku-hold-6", "rain-void-8", "jailer root leftover", "crosvm rootfs leftover", "runtime"),
    ("qemu-firmware-stale", "qemufw-eval", "libvirt-nvram-stale", "libvirtnv-eval",
     "flash-void-7", "promo-void-8", "qemu firmware leftover", "libvirt nvram leftover", "runtime"),
]

for i, row in enumerate(ROWS):
    PAIRS.append(_pair(*row[:8], i * 2, row[8]))
