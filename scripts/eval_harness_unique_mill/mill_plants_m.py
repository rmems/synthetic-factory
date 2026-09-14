"""Unique eval-harness leftover plants r439+. Not r319/GEval-cache/test_ or prior leftover clones."""

from mill_plants import PAIRS, _bad, _ok

# r439 consul-template leftover
PAIRS.append(
    (
        _ok(
            slug="consultpl-src-stale-b53i",
            domain="consultpl-eval",
            kind="secret",
            avoided="r438 vaultagent; r343 consul kv; r319 ClearML uri",
            goal=(
                "consul-template leftover source leftover.tpl so planted dual-hold-5 never "
                "renders. Pin the template to this SHA."
            ),
            plan="Dump template, pin SHA, prove planted dual-hold-5 fail.",
            outcome=(
                "source is eval-<sha>.tpl. Planted dual-hold-5 0.13 fail-closed. Residual: a "
                "daemon leftover still leftover.tpl."
            ),
            ticket=(
                "Title: consul-template leftover leftover.tpl. planted dual-hold-5 missing."
            ),
            src="evals/consul-template.hcl",
            src_obs='source = "leftover.tpl"  # leftover',
            run="evals/consultpl_eval.py",
            fail_obs="source leftover leftover.tpl. planted dual-hold-5 missing",
            inspect="evals/consul-template.hcl",
            inspect_obs="leftover.tpl leftover",
            first_path="evals/consul-template.hcl",
            first_old='source = "leftover.tpl"',
            first_new='source = "eval-dev.tpl"',
            first_obs="dev local. daemon leftover still leftover.tpl",
            rate_tail="daemon leftover leftover.tpl",
            still_after_429="daemon leftover; planted dual-hold-5 missing",
            grep="leftover.tpl|consul-template|goldens",
            grep_obs="source eval-<sha>.tpl; ignore daemon leftover",
            plan_change="source eval-<sha>.tpl; refuse leftover.tpl",
            fix_path="evals/consul-template.hcl",
            fix_old='source = "eval-dev.tpl"',
            fix_new='source = "eval-{{sha}}.tpl"',
            fix_obs="planted dual-hold-5 0.13 on sha template",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold-5 0.13",
            test="tests/test_consultpl_src_sha.py",
            test_body="assert source includes sha; leftover.tpl unused",
            test_obs="test_consultpl_not_leftover_tpl",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-5",
            diff_obs=" evals/consul-template.hcl | 2+-\n tests/test_consultpl_src_sha.py | 12++\n",
            residual="Daemon leftover still leftover.tpl.",
        ),
        _bad(
            slug="nomadpack-reg-stale-c54j",
            domain="nomadpack-eval",
            kind="deploy",
            avoided="r343 nomad artifact; r437 levant; r319 Aim hash",
            goal=(
                "Nomad Pack leftover registry leftover so planted rain-hold-11 never "
                "renders. Pin the registry locally."
            ),
            plan="Dump pack, pin SHA, prove planted rain-hold-11 locally.",
            outcome=(
                "Local registry is this SHA. Planted rain-hold-11 present locally. Handoff: "
                "the CLI leftover still nomad-pack run leftover."
            ),
            ticket=(
                "Title: Nomad Pack leftover registry leftover. planted rain-hold-11 missing."
            ),
            src="evals/nomad-pack.hcl",
            src_obs='registry = "leftover"  # leftover',
            run="evals/nomadpack_eval.py",
            fail_obs="registry leftover leftover. planted rain-hold-11 missing",
            inspect="evals/nomad-pack.hcl",
            inspect_obs="leftover leftover",
            first_path="evals/nomad-pack.hcl",
            first_old='registry = "leftover"',
            first_new='registry = "eval-dev"',
            first_obs="dev local. CLI leftover still leftover",
            rate_tail="CLI leftover nomad-pack run leftover",
            still_after_429="CLI leftover; planted rain-hold-11 missing",
            grep="registry = .leftover|nomad-pack|goldens",
            grep_obs="cannot change CLI leftover from this ticket",
            plan_change="local registry SHA; document CLI leftover leftover",
            fix_path="evals/nomad-pack.hcl",
            fix_old='registry = "eval-dev"',
            fix_new='registry = "eval-{{sha}}"',
            fix_obs="local planted present. CLI leftover HANDOFF",
            retry_obs="502 unused. CLI leftover nomad-pack leftover. Partial",
            test="tests/test_nomadpack_reg_sha.py",
            test_body="xfail CLI leftover leftover; local SHA registry",
            test_obs="CLI leftover nomad-pack leftover. Partial",
            suite_obs="local SHA registry. CLI leftover leftover. Partial.",
            gate_obs="local SHA registry. CLI leftover leftover. Partial.",
            diff_obs=" evals/nomad-pack.hcl | 2+-\n HANDOFF nomad-pack cli\n",
            residual="CLI leftover still nomad-pack run leftover. Partial.",
        ),
    )
)

# r440 sentinel leftover
PAIRS.append(
    (
        _ok(
            slug="sentinel-policy-stale-d55k",
            domain="sentinel-eval",
            kind="policy",
            avoided="r427 opa; r428 gatekeeper; r319 ClearML uri",
            goal=(
                "Sentinel leftover policy leftover.sentinel so planted flash-hold-12 never "
                "enforces. Pin the policy to this SHA."
            ),
            plan="Dump policy, pin SHA, prove planted flash-hold-12 fail.",
            outcome=(
                "policy is eval-<sha>.sentinel. Planted flash-hold-12 0.14 fail-closed. Residual: "
                "a VCS leftover still leftover.sentinel."
            ),
            ticket=(
                "Title: Sentinel leftover leftover.sentinel. planted flash-hold-12 missing."
            ),
            src="evals/sentinel.hcl",
            src_obs='policy "leftover" { source = "./leftover.sentinel" }  # leftover',
            run="evals/sentinel_eval.py",
            fail_obs="policy leftover leftover.sentinel. planted flash-hold-12 missing",
            inspect="evals/sentinel.hcl",
            inspect_obs="leftover leftover",
            first_path="evals/sentinel.hcl",
            first_old='policy "leftover"',
            first_new='policy "eval-dev"',
            first_obs="dev local. VCS leftover still leftover.sentinel",
            rate_tail="VCS leftover leftover.sentinel",
            still_after_429="VCS leftover; planted flash-hold-12 missing",
            grep="leftover.sentinel|policy .leftover|goldens",
            grep_obs="policy eval-<sha>; ignore VCS leftover",
            plan_change="policy eval-<sha>.sentinel; refuse leftover.sentinel",
            fix_path="evals/sentinel.hcl",
            fix_old='policy "eval-dev"',
            fix_new='policy "eval-{{sha}}"',
            fix_obs="planted flash-hold-12 0.14 on sha policy",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-12 0.14",
            test="tests/test_sentinel_policy_sha.py",
            test_body="assert policy includes sha; leftover unused",
            test_obs="test_sentinel_not_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-12",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-12",
            diff_obs=" evals/sentinel.hcl | 2+-\n tests/test_sentinel_policy_sha.py | 12++\n",
            residual="VCS leftover still leftover.sentinel.",
        ),
        _bad(
            slug="tracee-policy-stale-e56l",
            domain="tracee-eval",
            kind="policy",
            avoided="r428 falco; r440 sentinel; r319 Aim hash",
            goal=(
                "Tracee leftover policy leftover.yaml so planted promo-hold-11 never "
                "fires. Pin the policy locally."
            ),
            plan="Dump policy, pin SHA, prove planted promo-hold-11 locally.",
            outcome=(
                "Local policy is this SHA. Planted promo-hold-11 present locally. Handoff: "
                "the daemon leftover still leftover.yaml."
            ),
            ticket=(
                "Title: Tracee leftover leftover.yaml. planted promo-hold-11 unused."
            ),
            src="evals/tracee.yaml",
            src_obs="policies:\n  - leftover.yaml  # leftover",
            run="evals/tracee_eval.py",
            fail_obs="policy leftover leftover.yaml. planted promo-hold-11 unused",
            inspect="evals/tracee.yaml",
            inspect_obs="leftover.yaml leftover",
            first_path="evals/tracee.yaml",
            first_old="- leftover.yaml",
            first_new="- eval-dev.yaml",
            first_obs="dev local. daemon leftover still leftover.yaml",
            rate_tail="daemon leftover leftover.yaml",
            still_after_429="daemon leftover; planted promo-hold-11 unused",
            grep="leftover.yaml|tracee.yaml|goldens",
            grep_obs="cannot change daemon leftover from this ticket",
            plan_change="local SHA policy; document daemon leftover leftover.yaml",
            fix_path="evals/tracee.yaml",
            fix_old="- eval-dev.yaml",
            fix_new="- eval-{{sha}}.yaml",
            fix_obs="local planted present. daemon leftover HANDOFF",
            retry_obs="502 unused. daemon leftover leftover.yaml. Partial",
            test="tests/test_tracee_policy_sha.py",
            test_body="xfail daemon leftover leftover.yaml; local SHA policy",
            test_obs="daemon leftover leftover.yaml. Partial",
            suite_obs="local SHA policy. daemon leftover leftover.yaml. Partial.",
            gate_obs="local SHA policy. daemon leftover leftover.yaml. Partial.",
            diff_obs=" evals/tracee.yaml | 2+-\n HANDOFF tracee daemon\n",
            residual="Daemon leftover still leftover.yaml. Partial.",
        ),
    )
)

# r441 os leftover
PAIRS.append(
    (
        _ok(
            slug="talos-machine-stale-f57m",
            domain="talos-eval",
            kind="os",
            avoided="r395 kind; r396 minikube; r319 ClearML uri",
            goal=(
                "Talos leftover machine config leftover.yaml so planted gift-hold-11 never "
                "boots goldens. Pin the config to this SHA."
            ),
            plan="Dump machine config, pin SHA, prove planted gift-hold-11 fail.",
            outcome=(
                "config is eval-<sha>.yaml. Planted gift-hold-11 0.15 fail-closed. Residual: "
                "an apply leftover still leftover.yaml."
            ),
            ticket=(
                "Title: Talos leftover leftover.yaml. planted gift-hold-11 missing."
            ),
            src="evals/talos.yaml",
            src_obs="talosctl apply-config -f leftover.yaml  # leftover",
            run="evals/talos_eval.py",
            fail_obs="config leftover leftover.yaml. planted gift-hold-11 missing",
            inspect="evals/talos.yaml",
            inspect_obs="leftover.yaml leftover",
            first_path="evals/talos.yaml",
            first_old="leftover.yaml",
            first_new="eval-dev.yaml",
            first_obs="dev local. apply leftover still leftover.yaml",
            rate_tail="apply leftover leftover.yaml",
            still_after_429="apply leftover; planted gift-hold-11 missing",
            grep="leftover.yaml|talosctl|goldens",
            grep_obs="config eval-<sha>.yaml; ignore apply leftover",
            plan_change="config eval-<sha>.yaml; refuse leftover.yaml",
            fix_path="evals/talos.yaml",
            fix_old="eval-dev.yaml",
            fix_new="eval-$GIT_SHA.yaml",
            fix_obs="planted gift-hold-11 0.15 on sha config",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-11 0.15",
            test="tests/test_talos_cfg_sha.py",
            test_body="assert config includes sha; leftover.yaml unused",
            test_obs="test_talos_not_leftover_yaml",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-11",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-11",
            diff_obs=" evals/talos.yaml | 2+-\n tests/test_talos_cfg_sha.py | 12++\n",
            residual="Apply leftover still leftover.yaml.",
        ),
        _bad(
            slug="flatcar-ign-stale-g58n",
            domain="flatcar-eval",
            kind="os",
            avoided="r441 talos; r358 firecracker; r319 Aim hash",
            goal=(
                "Flatcar leftover ignition leftover.ign so planted bundle-hold-10 never "
                "provisions goldens. Pin ignition locally."
            ),
            plan="Dump ignition, pin SHA, prove planted bundle-hold-10 locally.",
            outcome=(
                "Local ignition is this SHA. Planted bundle-hold-10 present locally. Handoff: "
                "the PXE leftover still leftover.ign."
            ),
            ticket=(
                "Title: Flatcar leftover leftover.ign. planted bundle-hold-10 missing."
            ),
            src="evals/flatcar.ign",
            src_obs='"ignition": { "version": "leftover" }  // leftover',
            run="evals/flatcar_eval.py",
            fail_obs="ign leftover leftover. planted bundle-hold-10 missing",
            inspect="evals/flatcar.ign",
            inspect_obs="leftover leftover",
            first_path="evals/flatcar.ign",
            first_old='"version": "leftover"',
            first_new='"version": "3.4.0"',
            first_obs="3.4 local. PXE leftover still leftover.ign",
            rate_tail="PXE leftover leftover.ign",
            still_after_429="PXE leftover; planted bundle-hold-10 missing",
            grep="leftover.ign|flatcar.ign|goldens",
            grep_obs="cannot change PXE leftover from this ticket",
            plan_change="local SHA ignition; document PXE leftover leftover.ign",
            fix_path="evals/flatcar.ign",
            fix_old='"version": "3.4.0"',
            fix_new='"version": "{{sha}}"',
            fix_obs="local planted present. PXE leftover HANDOFF",
            retry_obs="502 unused. PXE leftover leftover.ign. Partial",
            test="tests/test_flatcar_ign_sha.py",
            test_body="xfail PXE leftover leftover.ign; local SHA ignition",
            test_obs="PXE leftover leftover.ign. Partial",
            suite_obs="local SHA ignition. PXE leftover leftover.ign. Partial.",
            gate_obs="local SHA ignition. PXE leftover leftover.ign. Partial.",
            diff_obs=" evals/flatcar.ign | 2+-\n HANDOFF flatcar pxe\n",
            residual="PXE leftover still leftover.ign. Partial.",
        ),
    )
)

# r442 more os leftover
PAIRS.append(
    (
        _ok(
            slug="bottlerocket-settings-stale-h59o",
            domain="bottlerocket-eval",
            kind="os",
            avoided="r441 talos; r441 flatcar; r319 ClearML uri",
            goal=(
                "Bottlerocket leftover settings leftover.toml so planted loyalty-hold-9 "
                "never applies. Pin settings to this SHA."
            ),
            plan="Dump settings, pin SHA, prove planted loyalty-hold-9 fail.",
            outcome=(
                "settings is eval-<sha>.toml. Planted loyalty-hold-9 0.12 fail-closed. Residual: "
                "an API leftover still leftover.toml."
            ),
            ticket=(
                "Title: Bottlerocket leftover leftover.toml. planted loyalty-hold-9 missing."
            ),
            src="evals/bottlerocket.toml",
            src_obs='[settings.eval]\npath = "leftover.toml"  # leftover',
            run="evals/bottlerocket_eval.py",
            fail_obs="settings leftover leftover.toml. planted loyalty-hold-9 missing",
            inspect="evals/bottlerocket.toml",
            inspect_obs="leftover.toml leftover",
            first_path="evals/bottlerocket.toml",
            first_old='path = "leftover.toml"',
            first_new='path = "eval-dev.toml"',
            first_obs="dev local. API leftover still leftover.toml",
            rate_tail="API leftover leftover.toml",
            still_after_429="API leftover; planted loyalty-hold-9 missing",
            grep="leftover.toml|bottlerocket|goldens",
            grep_obs="settings eval-<sha>.toml; ignore API leftover",
            plan_change="settings eval-<sha>.toml; refuse leftover.toml",
            fix_path="evals/bottlerocket.toml",
            fix_old='path = "eval-dev.toml"',
            fix_new='path = "eval-{{sha}}.toml"',
            fix_obs="planted loyalty-hold-9 0.12 on sha settings",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-9 0.12",
            test="tests/test_bottlerocket_set_sha.py",
            test_body="assert settings includes sha; leftover.toml unused",
            test_obs="test_bottlerocket_not_leftover_toml",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-9",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-9",
            diff_obs=" evals/bottlerocket.toml | 2+-\n tests/test_bottlerocket_set_sha.py | 12++\n",
            residual="API leftover still leftover.toml.",
        ),
        _bad(
            slug="fcos-butane-stale-i60p",
            domain="fcos-eval",
            kind="os",
            avoided="r441 flatcar; r442 bottlerocket; r319 Aim hash",
            goal=(
                "FCOS leftover butane leftover.bu so planted cancel-hold-9 never "
                "provisions. Pin butane locally."
            ),
            plan="Dump butane, pin SHA, prove planted cancel-hold-9 locally.",
            outcome=(
                "Local butane is this SHA. Planted cancel-hold-9 present locally. Handoff: "
                "the PXE leftover still leftover.bu."
            ),
            ticket=(
                "Title: FCOS leftover leftover.bu. planted cancel-hold-9 missing."
            ),
            src="evals/fcos.bu",
            src_obs="variant: leftover  # leftover",
            run="evals/fcos_eval.py",
            fail_obs="butane leftover leftover. planted cancel-hold-9 missing",
            inspect="evals/fcos.bu",
            inspect_obs="leftover leftover",
            first_path="evals/fcos.bu",
            first_old="variant: leftover",
            first_new="variant: fcos",
            first_obs="fcos local. PXE leftover still leftover.bu",
            rate_tail="PXE leftover leftover.bu",
            still_after_429="PXE leftover; planted cancel-hold-9 missing",
            grep="leftover.bu|variant: leftover|goldens",
            grep_obs="cannot change PXE leftover from this ticket",
            plan_change="local SHA butane; document PXE leftover leftover.bu",
            fix_path="evals/fcos.bu",
            fix_old="variant: fcos",
            fix_new="variant: eval-{{sha}}",
            fix_obs="local planted present. PXE leftover HANDOFF",
            retry_obs="502 unused. PXE leftover leftover.bu. Partial",
            test="tests/test_fcos_bu_sha.py",
            test_body="xfail PXE leftover leftover.bu; local SHA butane",
            test_obs="PXE leftover leftover.bu. Partial",
            suite_obs="local SHA butane. PXE leftover leftover.bu. Partial.",
            gate_obs="local SHA butane. PXE leftover leftover.bu. Partial.",
            diff_obs=" evals/fcos.bu | 2+-\n HANDOFF fcos pxe\n",
            residual="PXE leftover still leftover.bu. Partial.",
        ),
    )
)

# r443 runtime leftover
PAIRS.append(
    (
        _ok(
            slug="gvisor-runsc-stale-j61q",
            domain="gvisor-eval",
            kind="runtime",
            avoided="r358 kata; r356 podman; r319 ClearML uri",
            goal=(
                "gVisor leftover runsc config leftover.toml so planted tax-hold-9 never "
                "sees goldens. Pin the config to this SHA."
            ),
            plan="Dump runsc, pin SHA, prove planted tax-hold-9 fail.",
            outcome=(
                "config is eval-<sha>.toml. Planted tax-hold-9 0.13 fail-closed. Residual: "
                "a containerd leftover still leftover.toml."
            ),
            ticket=(
                "Title: gVisor leftover leftover.toml. planted tax-hold-9 missing."
            ),
            src="evals/runsc.toml",
            src_obs='config = "leftover.toml"  # leftover',
            run="evals/gvisor_eval.py",
            fail_obs="config leftover leftover.toml. planted tax-hold-9 missing",
            inspect="evals/runsc.toml",
            inspect_obs="leftover.toml leftover",
            first_path="evals/runsc.toml",
            first_old='config = "leftover.toml"',
            first_new='config = "eval-dev.toml"',
            first_obs="dev local. containerd leftover still leftover.toml",
            rate_tail="containerd leftover leftover.toml",
            still_after_429="containerd leftover; planted tax-hold-9 missing",
            grep="leftover.toml|runsc.toml|goldens",
            grep_obs="config eval-<sha>.toml; ignore containerd leftover",
            plan_change="config eval-<sha>.toml; refuse leftover.toml",
            fix_path="evals/runsc.toml",
            fix_old='config = "eval-dev.toml"',
            fix_new='config = "eval-{{sha}}.toml"',
            fix_obs="planted tax-hold-9 0.13 on sha config",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-9 0.13",
            test="tests/test_gvisor_cfg_sha.py",
            test_body="assert config includes sha; leftover.toml unused",
            test_obs="test_gvisor_not_leftover_toml",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-9",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-9",
            diff_obs=" evals/runsc.toml | 2+-\n tests/test_gvisor_cfg_sha.py | 12++\n",
            residual="containerd leftover still leftover.toml.",
        ),
        _bad(
            slug="cloudhv-fw-stale-k62r",
            domain="cloudhv-eval",
            kind="runtime",
            avoided="r358 firecracker; r443 gvisor; r319 Aim hash",
            goal=(
                "Cloud Hypervisor leftover firmware leftover.bin so planted sla-hold-8 "
                "never boots goldens. Pin firmware locally."
            ),
            plan="Dump firmware, pin SHA, prove planted sla-hold-8 locally.",
            outcome=(
                "Local firmware is this SHA. Planted sla-hold-8 present locally. Handoff: "
                "the launcher leftover still leftover.bin."
            ),
            ticket=(
                "Title: Cloud Hypervisor leftover leftover.bin. planted sla-hold-8 missing."
            ),
            src="evals/cloudhv.sh",
            src_obs="--kernel leftover.bin  # leftover",
            run="evals/cloudhv_eval.py",
            fail_obs="firmware leftover leftover.bin. planted sla-hold-8 missing",
            inspect="evals/cloudhv.sh",
            inspect_obs="leftover.bin leftover",
            first_path="evals/cloudhv.sh",
            first_old="--kernel leftover.bin",
            first_new="--kernel eval-dev.bin",
            first_obs="dev local. launcher leftover still leftover.bin",
            rate_tail="launcher leftover leftover.bin",
            still_after_429="launcher leftover; planted sla-hold-8 missing",
            grep="leftover.bin|cloudhv|goldens",
            grep_obs="cannot change launcher leftover from this ticket",
            plan_change="local SHA firmware; document launcher leftover leftover.bin",
            fix_path="evals/cloudhv.sh",
            fix_old="--kernel eval-dev.bin",
            fix_new="--kernel eval-$GIT_SHA.bin",
            fix_obs="local planted present. launcher leftover HANDOFF",
            retry_obs="502 unused. launcher leftover leftover.bin. Partial",
            test="tests/test_cloudhv_fw_sha.py",
            test_body="xfail launcher leftover leftover.bin; local SHA firmware",
            test_obs="launcher leftover leftover.bin. Partial",
            suite_obs="local SHA firmware. launcher leftover leftover.bin. Partial.",
            gate_obs="local SHA firmware. launcher leftover leftover.bin. Partial.",
            diff_obs=" evals/cloudhv.sh | 2+-\n HANDOFF cloudhv launcher\n",
            residual="Launcher leftover still leftover.bin. Partial.",
        ),
    )
)

# r444 capi leftover
PAIRS.append(
    (
        _ok(
            slug="capi-template-stale-l63s",
            domain="capi-eval",
            kind="cluster",
            avoided="r395 kind; r397 k3s; r319 ClearML uri",
            goal=(
                "Cluster API leftover ClusterClass leftover so planted membership-hold-7 "
                "never provisions. Pin the class to this SHA."
            ),
            plan="Dump ClusterClass, pin SHA, prove planted membership-hold-7 fail.",
            outcome=(
                "class is eval-<sha>. Planted membership-hold-7 0.14 fail-closed. Residual: "
                "a Cluster leftover still class leftover."
            ),
            ticket=(
                "Title: CAPI leftover ClusterClass leftover. planted membership-hold-7 missing."
            ),
            src="evals/clusterclass.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/capi_eval.py",
            fail_obs="class leftover leftover. planted membership-hold-7 missing",
            inspect="evals/clusterclass.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/clusterclass.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. Cluster leftover still leftover",
            rate_tail="Cluster leftover class leftover",
            still_after_429="Cluster leftover; planted membership-hold-7 missing",
            grep="name: leftover|ClusterClass|goldens",
            grep_obs="class eval-<sha>; ignore Cluster leftover",
            plan_change="class eval-<sha>; refuse leftover",
            fix_path="evals/clusterclass.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted membership-hold-7 0.14 on sha class",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold-7 0.14",
            test="tests/test_capi_class_sha.py",
            test_body="assert class includes sha; leftover unused",
            test_obs="test_capi_not_class_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-7",
            diff_obs=" evals/clusterclass.yaml | 2+-\n tests/test_capi_class_sha.py | 12++\n",
            residual="Cluster leftover still class leftover.",
        ),
        _bad(
            slug="harvester-image-stale-m64t",
            domain="harvester-eval",
            kind="cluster",
            avoided="r444 capi; r344 packer; r319 Aim hash",
            goal=(
                "Harvester leftover image leftover.img so planted after-hold-9 never "
                "boots. Pin the image locally."
            ),
            plan="Dump image, pin SHA, prove planted after-hold-9 locally.",
            outcome=(
                "Local image is this SHA. Planted after-hold-9 present locally. Handoff: "
                "the VM leftover still leftover.img."
            ),
            ticket=(
                "Title: Harvester leftover leftover.img. planted after-hold-9 missing."
            ),
            src="evals/harvester.yaml",
            src_obs="image: leftover.img  # leftover",
            run="evals/harvester_eval.py",
            fail_obs="image leftover leftover.img. planted after-hold-9 missing",
            inspect="evals/harvester.yaml",
            inspect_obs="leftover.img leftover",
            first_path="evals/harvester.yaml",
            first_old="image: leftover.img",
            first_new="image: eval-dev.img",
            first_obs="dev local. VM leftover still leftover.img",
            rate_tail="VM leftover leftover.img",
            still_after_429="VM leftover; planted after-hold-9 missing",
            grep="leftover.img|harvester.yaml|goldens",
            grep_obs="cannot change VM leftover from this ticket",
            plan_change="local SHA image; document VM leftover leftover.img",
            fix_path="evals/harvester.yaml",
            fix_old="image: eval-dev.img",
            fix_new="image: eval-{{sha}}.img",
            fix_obs="local planted present. VM leftover HANDOFF",
            retry_obs="502 unused. VM leftover leftover.img. Partial",
            test="tests/test_harvester_img_sha.py",
            test_body="xfail VM leftover leftover.img; local SHA image",
            test_obs="VM leftover leftover.img. Partial",
            suite_obs="local SHA image. VM leftover leftover.img. Partial.",
            gate_obs="local SHA image. VM leftover leftover.img. Partial.",
            diff_obs=" evals/harvester.yaml | 2+-\n HANDOFF harvester vm\n",
            residual="VM leftover still leftover.img. Partial.",
        ),
    )
)
