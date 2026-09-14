"""Unique eval-harness leftover plants r427+. Not r319/GEval-cache/test_ or prior leftover clones."""

from mill_plants import PAIRS, _bad, _ok

# r427 policy leftover
PAIRS.append(
    (
        _ok(
            slug="opa-bundle-stale-d29k",
            domain="opa-eval",
            kind="policy",
            avoided="r312 cue fmt; r336 hydra; r319 ClearML uri",
            goal=(
                "OPA leftover bundle eval.tar.gz is yesterday so planted dual-hold-4 never "
                "evaluates. Pin the bundle to this SHA."
            ),
            plan="Dump bundle path, pin SHA, prove planted dual-hold-4 fail.",
            outcome=(
                "bundle is eval-<sha>.tar.gz. Planted dual-hold-4 0.13 fail-closed. Residual: "
                "a sidecar leftover still eval.tar.gz."
            ),
            ticket=(
                "Title: OPA leftover bundle eval.tar.gz. planted dual-hold-4 missing."
            ),
            src="evals/opa.sh",
            src_obs="opa run -b eval.tar.gz  # leftover",
            run="evals/opa_eval.py",
            fail_obs="bundle leftover yesterday. planted dual-hold-4 absent",
            inspect="evals/opa.sh",
            inspect_obs="stable bundle leftover",
            first_path="evals/opa.sh",
            first_old="eval.tar.gz",
            first_new="eval-dev.tar.gz",
            first_obs="dev local. sidecar leftover still eval.tar.gz",
            rate_tail="sidecar leftover eval.tar.gz",
            still_after_429="sidecar leftover bundle; planted dual-hold-4 absent",
            grep="eval.tar.gz|opa run|goldens",
            grep_obs="bundle eval-<sha>.tar.gz; ignore sidecar leftover",
            plan_change="bundle eval-<sha>.tar.gz; refuse eval.tar.gz",
            fix_path="evals/opa.sh",
            fix_old="eval-dev.tar.gz",
            fix_new="eval-$GIT_SHA.tar.gz",
            fix_obs="planted dual-hold-4 0.13 in sha bundle",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold-4 0.13",
            test="tests/test_opa_bundle_sha.py",
            test_body="assert bundle includes sha; eval.tar.gz unused",
            test_obs="test_opa_not_eval_tar",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-4",
            diff_obs=" evals/opa.sh | 2+-\n tests/test_opa_bundle_sha.py | 12++\n",
            residual="Sidecar leftover still eval.tar.gz.",
        ),
        _bad(
            slug="kyverno-policy-stale-e30l",
            domain="kyverno-eval",
            kind="policy",
            avoided="r427 opa; r398 kustomize; r319 Aim hash",
            goal=(
                "Kyverno leftover ClusterPolicy eval still match leftover so planted "
                "rain-hold-9 never validates. Pin the match locally."
            ),
            plan="Dump policy, pin SHA, prove planted rain-hold-9 locally.",
            outcome=(
                "Local match is this SHA. Planted rain-hold-9 present locally. Handoff: the "
                "cluster leftover still match leftover."
            ),
            ticket=(
                "Title: Kyverno leftover match leftover. planted rain-hold-9 missing."
            ),
            src="evals/kyverno.yaml",
            src_obs="match:\n  any:\n  - resources:\n      names: [leftover]  # leftover",
            run="evals/kyverno_eval.py",
            fail_obs="match leftover leftover. planted rain-hold-9 absent",
            inspect="evals/kyverno.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/kyverno.yaml",
            first_old="names: [leftover]",
            first_new="names: [eval-dev]",
            first_obs="dev local. cluster leftover still leftover",
            rate_tail="cluster leftover match leftover",
            still_after_429="cluster leftover; planted rain-hold-9 absent",
            grep="names: .leftover|ClusterPolicy|goldens",
            grep_obs="cannot change cluster leftover from this ticket",
            plan_change="local match SHA; document cluster leftover leftover",
            fix_path="evals/kyverno.yaml",
            fix_old="names: [eval-dev]",
            fix_new="names: [eval-{{sha}}]",
            fix_obs="local planted present. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover kyverno. Partial",
            test="tests/test_kyverno_match_sha.py",
            test_body="xfail cluster leftover leftover; local SHA match",
            test_obs="cluster leftover kyverno. Partial",
            suite_obs="local SHA match. cluster leftover leftover. Partial.",
            gate_obs="local SHA match. cluster leftover leftover. Partial.",
            diff_obs=" evals/kyverno.yaml | 2+-\n HANDOFF kyverno cluster\n",
            residual="Cluster leftover still match leftover. Partial.",
        ),
    )
)

# r428 gatekeeper leftover
PAIRS.append(
    (
        _ok(
            slug="gatekeeper-template-stale-f31m",
            domain="gatekeeper-eval",
            kind="policy",
            avoided="r427 opa; r427 kyverno; r319 ClearML uri",
            goal=(
                "Gatekeeper leftover ConstraintTemplate eval still parameter threshold=0 so "
                "planted flash-hold-10 never fails. Pin threshold 0.7."
            ),
            plan="Dump template, pin 0.7, prove planted flash-hold-10 fail.",
            outcome=(
                "parameter threshold 0.7. Planted flash-hold-10 0.14 fail-closed. Residual: "
                "a constraint leftover still threshold=0."
            ),
            ticket=(
                "Title: Gatekeeper leftover threshold=0. planted flash-hold-10 green."
            ),
            src="evals/constraint.yaml",
            src_obs="parameters:\n  threshold: 0  # leftover",
            run="evals/gatekeeper_eval.py",
            fail_obs="threshold leftover 0. planted flash-hold-10 pass",
            inspect="evals/constraint.yaml",
            inspect_obs="0 leftover",
            first_path="evals/constraint.yaml",
            first_old="threshold: 0",
            first_new="threshold: 0.7",
            first_obs="0.7 local. constraint leftover still 0",
            rate_tail="constraint leftover threshold=0",
            still_after_429="constraint leftover 0; planted flash-hold-10 pass",
            grep="threshold: 0|ConstraintTemplate|goldens",
            grep_obs="force 0.7; ignore leftover 0",
            plan_change="parameter 0.7; refuse leftover 0",
            fix_path="evals/constraint.yaml",
            fix_old="threshold: 0.7",
            fix_new="threshold: 0.7  # no leftover 0",
            fix_obs="planted flash-hold-10 0.14. leftover 0 unused",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-10 0.14",
            test="tests/test_gatekeeper_not_zero.py",
            test_body="assert threshold 0.7; leftover 0 unused",
            test_obs="test_gatekeeper_not_threshold_zero",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-10",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-10",
            diff_obs=" evals/constraint.yaml | 2+-\n tests/test_gatekeeper_not_zero.py | 12++\n",
            residual="Constraint leftover still threshold=0.",
        ),
        _bad(
            slug="falco-rules-stale-g32n",
            domain="falco-eval",
            kind="policy",
            avoided="r428 gatekeeper; r427 opa; r319 Aim hash",
            goal=(
                "Falco leftover rules eval_rules.yaml still skip planted promo-hold-9. "
                "Include the planted rule locally."
            ),
            plan="Dump rules, add planted, prove planted promo-hold-9 locally.",
            outcome=(
                "Local rules include planted promo-hold-9. Handoff: the daemon leftover "
                "still loads eval_rules.yaml without the plant."
            ),
            ticket=(
                "Title: Falco leftover rules omit planted promo-hold-9."
            ),
            src="evals/eval_rules.yaml",
            src_obs="- rule: eval-legacy  # leftover no plant",
            run="evals/falco_eval.py",
            fail_obs="rules leftover omit plant. planted promo-hold-9 unused",
            inspect="evals/eval_rules.yaml",
            inspect_obs="legacy leftover",
            first_path="evals/eval_rules.yaml",
            first_old="- rule: eval-legacy",
            first_new="- rule: eval-dev",
            first_obs="dev local. daemon leftover still eval-legacy",
            rate_tail="daemon leftover eval_rules.yaml legacy",
            still_after_429="daemon leftover; planted promo-hold-9 unused",
            grep="eval-legacy|eval_rules|goldens",
            grep_obs="cannot change daemon leftover from this ticket",
            plan_change="local planted rule; document daemon leftover legacy",
            fix_path="evals/eval_rules.yaml",
            fix_old="- rule: eval-dev",
            fix_new="- rule: planted-promo-hold-9",
            fix_obs="local planted present. daemon leftover HANDOFF",
            retry_obs="502 unused. daemon leftover falco legacy. Partial",
            test="tests/test_falco_rules_plant.py",
            test_body="xfail daemon leftover legacy; local planted rule",
            test_obs="daemon leftover falco legacy. Partial",
            suite_obs="local planted rule. daemon leftover legacy. Partial.",
            gate_obs="local planted rule. daemon leftover legacy. Partial.",
            diff_obs=" evals/eval_rules.yaml | 2+-\n HANDOFF falco daemon\n",
            residual="Daemon leftover still loads eval_rules.yaml without the plant. Partial.",
        ),
    )
)

# r429 cni leftover
PAIRS.append(
    (
        _ok(
            slug="cilium-policy-stale-h33o",
            domain="cilium-eval",
            kind="net",
            avoided="r422 istio; r351 envoy; r319 ClearML uri",
            goal=(
                "Cilium leftover NetworkPolicy eval still egress leftover so planted "
                "gift-hold-9 never reaches the judge. Pin egress to this SHA."
            ),
            plan="Dump CNP, pin SHA egress, prove planted gift-hold-9 fail.",
            outcome=(
                "egress is eval-<sha>. Planted gift-hold-9 0.15 fail-closed. Residual: a "
                "CiliumClusterwide leftover still egress leftover."
            ),
            ticket=(
                "Title: Cilium leftover egress leftover. planted gift-hold-9 blocked."
            ),
            src="evals/cnp.yaml",
            src_obs="toEndpoints:\n  matchLabels:\n    app: leftover  # leftover",
            run="evals/cilium_eval.py",
            fail_obs="egress leftover leftover. planted gift-hold-9 blocked",
            inspect="evals/cnp.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/cnp.yaml",
            first_old="app: leftover",
            first_new="app: eval-dev",
            first_obs="dev local. clusterwide leftover still leftover",
            rate_tail="clusterwide leftover egress leftover",
            still_after_429="clusterwide leftover; planted gift-hold-9 blocked",
            grep="app: leftover|toEndpoints|goldens",
            grep_obs="egress eval-<sha>; ignore clusterwide leftover",
            plan_change="egress eval-<sha>; refuse leftover",
            fix_path="evals/cnp.yaml",
            fix_old="app: eval-dev",
            fix_new="app: eval-{{sha}}",
            fix_obs="planted gift-hold-9 0.15 allowed on sha egress",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-9 0.15",
            test="tests/test_cilium_egress_sha.py",
            test_body="assert egress app includes sha; leftover unused",
            test_obs="test_cilium_not_egress_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-9",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-9",
            diff_obs=" evals/cnp.yaml | 2+-\n tests/test_cilium_egress_sha.py | 12++\n",
            residual="CiliumClusterwide leftover still egress leftover.",
        ),
        _bad(
            slug="calico-gnp-stale-i34p",
            domain="calico-eval",
            kind="net",
            avoided="r429 cilium; r422 linkerd; r319 Aim hash",
            goal=(
                "Calico leftover GlobalNetworkPolicy eval still selector leftover so planted "
                "bundle-hold-8 never reaches the judge. Pin locally."
            ),
            plan="Dump GNP, pin SHA, prove planted bundle-hold-8 locally.",
            outcome=(
                "Local selector is eval-<sha>. Planted bundle-hold-8 present locally. "
                "Handoff: the felix leftover still selector leftover."
            ),
            ticket=(
                "Title: Calico leftover selector leftover. planted bundle-hold-8 blocked."
            ),
            src="evals/gnp.yaml",
            src_obs="selector: app == 'leftover'  # leftover",
            run="evals/calico_eval.py",
            fail_obs="selector leftover leftover. planted bundle-hold-8 blocked",
            inspect="evals/gnp.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/gnp.yaml",
            first_old="app == 'leftover'",
            first_new="app == 'eval-dev'",
            first_obs="dev local. felix leftover still leftover",
            rate_tail="felix leftover selector leftover",
            still_after_429="felix leftover; planted bundle-hold-8 blocked",
            grep="app == .leftover|GlobalNetworkPolicy|goldens",
            grep_obs="cannot change felix leftover from this ticket",
            plan_change="local selector SHA; document felix leftover leftover",
            fix_path="evals/gnp.yaml",
            fix_old="app == 'eval-dev'",
            fix_new="app == 'eval-{{sha}}'",
            fix_obs="local planted present. felix leftover HANDOFF",
            retry_obs="502 unused. felix leftover calico. Partial",
            test="tests/test_calico_selector_sha.py",
            test_body="xfail felix leftover leftover; local SHA selector",
            test_obs="felix leftover calico. Partial",
            suite_obs="local SHA selector. felix leftover leftover. Partial.",
            gate_obs="local SHA selector. felix leftover leftover. Partial.",
            diff_obs=" evals/gnp.yaml | 2+-\n HANDOFF calico felix\n",
            residual="Felix leftover still selector leftover. Partial.",
        ),
    )
)

# r430 lb leftover
PAIRS.append(
    (
        _ok(
            slug="metallb-pool-stale-j35q",
            domain="metallb-eval",
            kind="net",
            avoided="r351 haproxy; r429 cilium; r319 ClearML uri",
            goal=(
                "MetalLB leftover IPAddressPool eval still addresses leftover so planted "
                "loyalty-hold-7 never gets a VIP. Pin the pool to this SHA."
            ),
            plan="Dump pool, pin SHA, prove planted loyalty-hold-7 fail.",
            outcome=(
                "pool is eval-<sha>. Planted loyalty-hold-7 0.12 fail-closed. Residual: a "
                "L2Advertisement leftover still pool leftover."
            ),
            ticket=(
                "Title: MetalLB leftover pool leftover. planted loyalty-hold-7 no VIP."
            ),
            src="evals/ipaddresspool.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/metallb_eval.py",
            fail_obs="pool leftover leftover. planted loyalty-hold-7 no VIP",
            inspect="evals/ipaddresspool.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/ipaddresspool.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. L2 leftover still leftover",
            rate_tail="L2Advertisement leftover pool leftover",
            still_after_429="L2 leftover; planted loyalty-hold-7 no VIP",
            grep="name: leftover|IPAddressPool|goldens",
            grep_obs="pool eval-<sha>; ignore L2 leftover",
            plan_change="pool eval-<sha>; refuse leftover",
            fix_path="evals/ipaddresspool.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted loyalty-hold-7 0.12 on sha pool",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-7 0.12",
            test="tests/test_metallb_pool_sha.py",
            test_body="assert pool name includes sha; leftover unused",
            test_obs="test_metallb_not_pool_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-7",
            diff_obs=" evals/ipaddresspool.yaml | 2+-\n tests/test_metallb_pool_sha.py | 12++\n",
            residual="L2Advertisement leftover still pool leftover.",
        ),
        _bad(
            slug="kubevip-iface-stale-k36r",
            domain="kubevip-eval",
            kind="net",
            avoided="r430 metallb; r351 haproxy; r319 Aim hash",
            goal=(
                "kube-vip leftover interface leftover0 so planted cancel-hold-7 never "
                "binds. Pin the interface locally."
            ),
            plan="Dump kube-vip yaml, pin iface, prove planted cancel-hold-7 locally.",
            outcome=(
                "Local interface is this SHA nic. Planted cancel-hold-7 present locally. "
                "Handoff: the daemon leftover still leftover0."
            ),
            ticket=(
                "Title: kube-vip leftover interface leftover0. planted cancel-hold-7 unbound."
            ),
            src="evals/kube-vip.yaml",
            src_obs="vip_interface: leftover0  # leftover",
            run="evals/kubevip_eval.py",
            fail_obs="iface leftover leftover0. planted cancel-hold-7 unbound",
            inspect="evals/kube-vip.yaml",
            inspect_obs="leftover0 leftover",
            first_path="evals/kube-vip.yaml",
            first_old="vip_interface: leftover0",
            first_new="vip_interface: eth0",
            first_obs="eth0 local. daemon leftover still leftover0",
            rate_tail="daemon leftover leftover0",
            still_after_429="daemon leftover iface; planted cancel-hold-7 unbound",
            grep="leftover0|vip_interface|goldens",
            grep_obs="cannot change daemon leftover from this ticket",
            plan_change="local SHA nic; document daemon leftover leftover0",
            fix_path="evals/kube-vip.yaml",
            fix_old="vip_interface: eth0",
            fix_new="vip_interface: eval-{{sha}}",
            fix_obs="local planted present. daemon leftover HANDOFF",
            retry_obs="502 unused. daemon leftover leftover0. Partial",
            test="tests/test_kubevip_iface_sha.py",
            test_body="xfail daemon leftover leftover0; local SHA nic",
            test_obs="daemon leftover leftover0. Partial",
            suite_obs="local SHA nic. daemon leftover leftover0. Partial.",
            gate_obs="local SHA nic. daemon leftover leftover0. Partial.",
            diff_obs=" evals/kube-vip.yaml | 2+-\n HANDOFF kube-vip daemon\n",
            residual="Daemon leftover still leftover0. Partial.",
        ),
    )
)

# r431 cert leftover
PAIRS.append(
    (
        _ok(
            slug="certman-issuer-stale-l37s",
            domain="certman-eval",
            kind="net",
            avoided="r337 vault kv; r350 caddy; r319 ClearML uri",
            goal=(
                "cert-manager leftover ClusterIssuer eval still acme leftover so planted "
                "tax-hold-7 never gets a cert. Pin the issuer to this SHA."
            ),
            plan="Dump issuer, pin SHA, prove planted tax-hold-7 fail.",
            outcome=(
                "issuer is eval-<sha>. Planted tax-hold-7 0.16 fail-closed. Residual: a "
                "Certificate leftover still issuerRef leftover."
            ),
            ticket=(
                "Title: cert-manager leftover issuer leftover. planted tax-hold-7 no cert."
            ),
            src="evals/clusterissuer.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/certman_eval.py",
            fail_obs="issuer leftover leftover. planted tax-hold-7 no cert",
            inspect="evals/clusterissuer.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/clusterissuer.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. Certificate leftover still leftover",
            rate_tail="Certificate leftover issuerRef leftover",
            still_after_429="Certificate leftover; planted tax-hold-7 no cert",
            grep="name: leftover|ClusterIssuer|goldens",
            grep_obs="issuer eval-<sha>; ignore Certificate leftover",
            plan_change="issuer eval-<sha>; refuse leftover",
            fix_path="evals/clusterissuer.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted tax-hold-7 0.16 on sha issuer",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-7 0.16",
            test="tests/test_certman_issuer_sha.py",
            test_body="assert issuer includes sha; leftover unused",
            test_obs="test_certman_not_issuer_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-7",
            diff_obs=" evals/clusterissuer.yaml | 2+-\n tests/test_certman_issuer_sha.py | 12++\n",
            residual="Certificate leftover still issuerRef leftover.",
        ),
        _bad(
            slug="extdns-zone-stale-m38t",
            domain="extdns-eval",
            kind="net",
            avoided="r431 certman; r365 npm; r319 Aim hash",
            goal=(
                "external-dns leftover txt-owner leftover so planted sla-hold-6 never "
                "updates. Pin the owner locally."
            ),
            plan="Dump args, pin SHA owner, prove planted sla-hold-6 locally.",
            outcome=(
                "Local txt-owner is this SHA. Planted sla-hold-6 present locally. Handoff: "
                "the deployment leftover still txt-owner leftover."
            ),
            ticket=(
                "Title: external-dns leftover txt-owner leftover. planted sla-hold-6 missing."
            ),
            src="evals/external-dns.yaml",
            src_obs="--txt-owner-id=leftover  # leftover",
            run="evals/extdns_eval.py",
            fail_obs="owner leftover leftover. planted sla-hold-6 missing",
            inspect="evals/external-dns.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/external-dns.yaml",
            first_old="--txt-owner-id=leftover",
            first_new="--txt-owner-id=eval-dev",
            first_obs="dev local. deployment leftover still leftover",
            rate_tail="deployment leftover txt-owner leftover",
            still_after_429="deployment leftover; planted sla-hold-6 missing",
            grep="txt-owner-id=leftover|external-dns|goldens",
            grep_obs="cannot change deployment leftover from this ticket",
            plan_change="local owner SHA; document deployment leftover leftover",
            fix_path="evals/external-dns.yaml",
            fix_old="--txt-owner-id=eval-dev",
            fix_new="--txt-owner-id=eval-{{sha}}",
            fix_obs="local planted present. deployment leftover HANDOFF",
            retry_obs="502 unused. deployment leftover extdns. Partial",
            test="tests/test_extdns_owner_sha.py",
            test_body="xfail deployment leftover leftover; local SHA owner",
            test_obs="deployment leftover extdns. Partial",
            suite_obs="local SHA owner. deployment leftover leftover. Partial.",
            gate_obs="local SHA owner. deployment leftover leftover. Partial.",
            diff_obs=" evals/external-dns.yaml | 2+-\n HANDOFF extdns deploy\n",
            residual="Deployment leftover still txt-owner leftover. Partial.",
        ),
    )
)

# r432 secrets leftover
PAIRS.append(
    (
        _ok(
            slug="extsecrets-store-stale-n39u",
            domain="extsecrets-eval",
            kind="secret",
            avoided="r337 vault; r347 chamber; r319 ClearML uri",
            goal=(
                "External Secrets leftover SecretStore eval still remoteRef leftover so "
                "planted membership-hold-5 never syncs. Pin the ref to this SHA."
            ),
            plan="Dump ExternalSecret, pin SHA, prove planted membership-hold-5 fail.",
            outcome=(
                "remoteRef is eval/<sha>. Planted membership-hold-5 0.13 fail-closed. Residual: "
                "a ClusterSecretStore leftover still leftover."
            ),
            ticket=(
                "Title: ESO leftover remoteRef leftover. planted membership-hold-5 missing."
            ),
            src="evals/externalsecret.yaml",
            src_obs="remoteRef:\n  key: leftover  # leftover",
            run="evals/extsecrets_eval.py",
            fail_obs="key leftover leftover. planted membership-hold-5 missing",
            inspect="evals/externalsecret.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/externalsecret.yaml",
            first_old="key: leftover",
            first_new="key: eval-dev",
            first_obs="dev local. ClusterSecretStore leftover still leftover",
            rate_tail="ClusterSecretStore leftover leftover",
            still_after_429="store leftover; planted membership-hold-5 missing",
            grep="key: leftover|remoteRef|goldens",
            grep_obs="key eval/<sha>; ignore store leftover",
            plan_change="remoteRef eval/<sha>; refuse leftover",
            fix_path="evals/externalsecret.yaml",
            fix_old="key: eval-dev",
            fix_new="key: eval/{{sha}}",
            fix_obs="planted membership-hold-5 0.13 on sha key",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold-5 0.13",
            test="tests/test_extsecrets_key_sha.py",
            test_body="assert remoteRef includes sha; leftover unused",
            test_obs="test_extsecrets_not_key_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-5",
            diff_obs=" evals/externalsecret.yaml | 2+-\n tests/test_extsecrets_key_sha.py | 12++\n",
            residual="ClusterSecretStore leftover still leftover.",
        ),
        _bad(
            slug="sealedsecrets-cert-stale-o40v",
            domain="sealedsecrets-eval",
            kind="secret",
            avoided="r432 extsecrets; r337 sops; r319 Aim hash",
            goal=(
                "Sealed Secrets leftover cert leftover.crt so planted after-hold-7 never "
                "decrypts. Pin the cert locally."
            ),
            plan="Dump cert path, pin SHA, prove planted after-hold-7 locally.",
            outcome=(
                "Local cert is this SHA. Planted after-hold-7 present locally. Handoff: the "
                "controller leftover still leftover.crt."
            ),
            ticket=(
                "Title: Sealed Secrets leftover leftover.crt. planted after-hold-7 missing."
            ),
            src="evals/sealed.yaml",
            src_obs="--cert leftover.crt  # leftover",
            run="evals/sealed_eval.py",
            fail_obs="cert leftover leftover.crt. planted after-hold-7 missing",
            inspect="evals/sealed.yaml",
            inspect_obs="leftover.crt leftover",
            first_path="evals/sealed.yaml",
            first_old="--cert leftover.crt",
            first_new="--cert eval-dev.crt",
            first_obs="dev local. controller leftover still leftover.crt",
            rate_tail="controller leftover leftover.crt",
            still_after_429="controller leftover cert; planted after-hold-7 missing",
            grep="leftover.crt|--cert|goldens",
            grep_obs="cannot change controller leftover from this ticket",
            plan_change="local SHA cert; document controller leftover leftover.crt",
            fix_path="evals/sealed.yaml",
            fix_old="--cert eval-dev.crt",
            fix_new="--cert eval-{{sha}}.crt",
            fix_obs="local planted present. controller leftover HANDOFF",
            retry_obs="502 unused. controller leftover leftover.crt. Partial",
            test="tests/test_sealed_cert_sha.py",
            test_body="xfail controller leftover leftover.crt; local SHA cert",
            test_obs="controller leftover leftover.crt. Partial",
            suite_obs="local SHA cert. controller leftover leftover.crt. Partial.",
            gate_obs="local SHA cert. controller leftover leftover.crt. Partial.",
            diff_obs=" evals/sealed.yaml | 2+-\n HANDOFF sealed controller\n",
            residual="Controller leftover still leftover.crt. Partial.",
        ),
    )
)

# r433 backup leftover
PAIRS.append(
    (
        _ok(
            slug="velero-backup-stale-p41w",
            domain="velero-eval",
            kind="storage",
            avoided="r334 minio; r397 k3s airgap; r319 ClearML uri",
            goal=(
                "Velero leftover backup eval still snapshot leftover so planted "
                "sku-hold-5 never restores. Pin the backup to this SHA."
            ),
            plan="Dump backup, pin SHA, prove planted sku-hold-5 fail.",
            outcome=(
                "backup is eval-<sha>. Planted sku-hold-5 0.14 fail-closed. Residual: a "
                "schedule leftover still backup eval."
            ),
            ticket=(
                "Title: Velero leftover backup eval. planted sku-hold-5 missing."
            ),
            src="evals/backup.yaml",
            src_obs="name: eval  # leftover",
            run="evals/velero_eval.py",
            fail_obs="backup leftover yesterday. planted sku-hold-5 missing",
            inspect="evals/backup.yaml",
            inspect_obs="name eval leftover",
            first_path="evals/backup.yaml",
            first_old="name: eval",
            first_new="name: eval-dev",
            first_obs="dev local. schedule leftover still eval",
            rate_tail="schedule leftover backup eval",
            still_after_429="schedule leftover; planted sku-hold-5 missing",
            grep="name: eval|Backup|goldens",
            grep_obs="backup eval-<sha>; ignore schedule leftover",
            plan_change="backup eval-<sha>; refuse eval",
            fix_path="evals/backup.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted sku-hold-5 0.14 in sha backup",
            retry_obs="502 then retry; 5 pass 1 fail planted sku-hold-5 0.14",
            test="tests/test_velero_backup_sha.py",
            test_body="assert backup name includes sha; eval unused",
            test_obs="test_velero_not_backup_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sku-hold-5",
            diff_obs=" evals/backup.yaml | 2+-\n tests/test_velero_backup_sha.py | 12++\n",
            residual="Schedule leftover still backup eval.",
        ),
        _bad(
            slug="kasten-profile-stale-q42x",
            domain="kasten-eval",
            kind="storage",
            avoided="r433 velero; r334 rclone; r319 Aim hash",
            goal=(
                "Kasten leftover profile eval still location leftover so planted "
                "rain-hold-10 never restores. Pin the location locally."
            ),
            plan="Dump profile, pin SHA, prove planted rain-hold-10 locally.",
            outcome=(
                "Local location is this SHA. Planted rain-hold-10 present locally. Handoff: "
                "the policy leftover still location leftover."
            ),
            ticket=(
                "Title: Kasten leftover location leftover. planted rain-hold-10 missing."
            ),
            src="evals/kasten.yaml",
            src_obs="location:\n  name: leftover  # leftover",
            run="evals/kasten_eval.py",
            fail_obs="location leftover leftover. planted rain-hold-10 missing",
            inspect="evals/kasten.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/kasten.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. policy leftover still leftover",
            rate_tail="policy leftover location leftover",
            still_after_429="policy leftover; planted rain-hold-10 missing",
            grep="name: leftover|location|goldens",
            grep_obs="cannot change policy leftover from this ticket",
            plan_change="local location SHA; document policy leftover leftover",
            fix_path="evals/kasten.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. policy leftover HANDOFF",
            retry_obs="502 unused. policy leftover kasten. Partial",
            test="tests/test_kasten_loc_sha.py",
            test_body="xfail policy leftover leftover; local SHA location",
            test_obs="policy leftover kasten. Partial",
            suite_obs="local SHA location. policy leftover leftover. Partial.",
            gate_obs="local SHA location. policy leftover leftover. Partial.",
            diff_obs=" evals/kasten.yaml | 2+-\n HANDOFF kasten policy\n",
            residual="Policy leftover still location leftover. Partial.",
        ),
    )
)

# r434 storage leftover
PAIRS.append(
    (
        _ok(
            slug="longhorn-vol-stale-r43y",
            domain="longhorn-eval",
            kind="storage",
            avoided="r433 velero; r359 libvirt; r319 ClearML uri",
            goal=(
                "Longhorn leftover volume eval still fromBackup leftover so planted "
                "flash-hold-11 never mounts. Pin the volume to this SHA."
            ),
            plan="Dump volume, pin SHA, prove planted flash-hold-11 fail.",
            outcome=(
                "volume is eval-<sha>. Planted flash-hold-11 0.15 fail-closed. Residual: a "
                "PVC leftover still volumeName leftover."
            ),
            ticket=(
                "Title: Longhorn leftover volume leftover. planted flash-hold-11 missing."
            ),
            src="evals/longhorn-vol.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/longhorn_eval.py",
            fail_obs="volume leftover leftover. planted flash-hold-11 missing",
            inspect="evals/longhorn-vol.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/longhorn-vol.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. PVC leftover still leftover",
            rate_tail="PVC leftover volumeName leftover",
            still_after_429="PVC leftover; planted flash-hold-11 missing",
            grep="name: leftover|longhorn-vol|goldens",
            grep_obs="volume eval-<sha>; ignore PVC leftover",
            plan_change="volume eval-<sha>; refuse leftover",
            fix_path="evals/longhorn-vol.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted flash-hold-11 0.15 on sha volume",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-11 0.15",
            test="tests/test_longhorn_vol_sha.py",
            test_body="assert volume name includes sha; leftover unused",
            test_obs="test_longhorn_not_vol_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-11",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-11",
            diff_obs=" evals/longhorn-vol.yaml | 2+-\n tests/test_longhorn_vol_sha.py | 12++\n",
            residual="PVC leftover still volumeName leftover.",
        ),
        _bad(
            slug="rook-pool-stale-s44z",
            domain="rook-eval",
            kind="storage",
            avoided="r434 longhorn; r340 ceph? none; r319 Aim hash",
            goal=(
                "Rook leftover CephBlockPool leftover so planted promo-hold-10 never "
                "provisions. Pin the pool locally."
            ),
            plan="Dump pool, pin SHA, prove planted promo-hold-10 locally.",
            outcome=(
                "Local pool is eval-<sha>. Planted promo-hold-10 present locally. Handoff: "
                "the StorageClass leftover still leftover."
            ),
            ticket=(
                "Title: Rook leftover CephBlockPool leftover. planted promo-hold-10 missing."
            ),
            src="evals/cephblockpool.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/rook_eval.py",
            fail_obs="pool leftover leftover. planted promo-hold-10 missing",
            inspect="evals/cephblockpool.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/cephblockpool.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. StorageClass leftover still leftover",
            rate_tail="StorageClass leftover leftover",
            still_after_429="StorageClass leftover; planted promo-hold-10 missing",
            grep="name: leftover|CephBlockPool|goldens",
            grep_obs="cannot change StorageClass leftover from this ticket",
            plan_change="local pool SHA; document StorageClass leftover leftover",
            fix_path="evals/cephblockpool.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. StorageClass leftover HANDOFF",
            retry_obs="502 unused. StorageClass leftover rook. Partial",
            test="tests/test_rook_pool_sha.py",
            test_body="xfail StorageClass leftover leftover; local SHA pool",
            test_obs="StorageClass leftover rook. Partial",
            suite_obs="local SHA pool. StorageClass leftover leftover. Partial.",
            gate_obs="local SHA pool. StorageClass leftover leftover. Partial.",
            diff_obs=" evals/cephblockpool.yaml | 2+-\n HANDOFF rook sc\n",
            residual="StorageClass leftover still leftover. Partial.",
        ),
    )
)

# r435 more storage leftover
PAIRS.append(
    (
        _ok(
            slug="openebs-cstor-stale-t45a",
            domain="openebs-eval",
            kind="storage",
            avoided="r434 longhorn; r434 rook; r319 ClearML uri",
            goal=(
                "OpenEBS leftover CStorPool leftover so planted gift-hold-10 never "
                "provisions. Pin the pool to this SHA."
            ),
            plan="Dump pool, pin SHA, prove planted gift-hold-10 fail.",
            outcome=(
                "pool is eval-<sha>. Planted gift-hold-10 0.12 fail-closed. Residual: a "
                "SPC leftover still leftover."
            ),
            ticket=(
                "Title: OpenEBS leftover CStorPool leftover. planted gift-hold-10 missing."
            ),
            src="evals/cstorpool.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/openebs_eval.py",
            fail_obs="pool leftover leftover. planted gift-hold-10 missing",
            inspect="evals/cstorpool.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/cstorpool.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. SPC leftover still leftover",
            rate_tail="SPC leftover leftover",
            still_after_429="SPC leftover; planted gift-hold-10 missing",
            grep="name: leftover|CStorPool|goldens",
            grep_obs="pool eval-<sha>; ignore SPC leftover",
            plan_change="pool eval-<sha>; refuse leftover",
            fix_path="evals/cstorpool.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted gift-hold-10 0.12 on sha pool",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-10 0.12",
            test="tests/test_openebs_pool_sha.py",
            test_body="assert pool name includes sha; leftover unused",
            test_obs="test_openebs_not_pool_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-10",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-10",
            diff_obs=" evals/cstorpool.yaml | 2+-\n tests/test_openebs_pool_sha.py | 12++\n",
            residual="SPC leftover still leftover.",
        ),
        _bad(
            slug="portworx-repl-stale-u46b",
            domain="portworx-eval",
            kind="storage",
            avoided="r435 openebs; r434 rook; r319 Aim hash",
            goal=(
                "Portworx leftover volume leftover so planted bundle-hold-9 never "
                "replicates. Pin the volume locally."
            ),
            plan="Dump pxctl, pin SHA, prove planted bundle-hold-9 locally.",
            outcome=(
                "Local volume is eval-<sha>. Planted bundle-hold-9 present locally. Handoff: "
                "the StorageClass leftover still leftover."
            ),
            ticket=(
                "Title: Portworx leftover volume leftover. planted bundle-hold-9 missing."
            ),
            src="evals/px-vol.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/portworx_eval.py",
            fail_obs="volume leftover leftover. planted bundle-hold-9 missing",
            inspect="evals/px-vol.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/px-vol.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. StorageClass leftover still leftover",
            rate_tail="StorageClass leftover leftover",
            still_after_429="StorageClass leftover; planted bundle-hold-9 missing",
            grep="name: leftover|px-vol|goldens",
            grep_obs="cannot change StorageClass leftover from this ticket",
            plan_change="local volume SHA; document StorageClass leftover leftover",
            fix_path="evals/px-vol.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. StorageClass leftover HANDOFF",
            retry_obs="502 unused. StorageClass leftover portworx. Partial",
            test="tests/test_portworx_vol_sha.py",
            test_body="xfail StorageClass leftover leftover; local SHA volume",
            test_obs="StorageClass leftover portworx. Partial",
            suite_obs="local SHA volume. StorageClass leftover leftover. Partial.",
            gate_obs="local SHA volume. StorageClass leftover leftover. Partial.",
            diff_obs=" evals/px-vol.yaml | 2+-\n HANDOFF portworx sc\n",
            residual="StorageClass leftover still leftover. Partial.",
        ),
    )
)

# r436 gateway leftover
PAIRS.append(
    (
        _ok(
            slug="contour-httpproxy-stale-v47c",
            domain="contour-eval",
            kind="net",
            avoided="r350 caddy; r422 istio; r319 ClearML uri",
            goal=(
                "Contour leftover HTTPProxy eval still fqdn leftover so planted "
                "loyalty-hold-8 never routes. Pin the fqdn to this SHA."
            ),
            plan="Dump HTTPProxy, pin SHA, prove planted loyalty-hold-8 fail.",
            outcome=(
                "fqdn is eval-<sha>.example. Planted loyalty-hold-8 0.13 fail-closed. Residual: "
                "a TLS leftover still leftover.example."
            ),
            ticket=(
                "Title: Contour leftover fqdn leftover. planted loyalty-hold-8 missing."
            ),
            src="evals/httpproxy.yaml",
            src_obs="fqdn: leftover.example  # leftover",
            run="evals/contour_eval.py",
            fail_obs="fqdn leftover leftover.example. planted loyalty-hold-8 missing",
            inspect="evals/httpproxy.yaml",
            inspect_obs="leftover.example leftover",
            first_path="evals/httpproxy.yaml",
            first_old="fqdn: leftover.example",
            first_new="fqdn: eval-dev.example",
            first_obs="dev local. TLS leftover still leftover.example",
            rate_tail="TLS leftover leftover.example",
            still_after_429="TLS leftover; planted loyalty-hold-8 missing",
            grep="leftover.example|HTTPProxy|goldens",
            grep_obs="fqdn eval-<sha>.example; ignore TLS leftover",
            plan_change="fqdn eval-<sha>.example; refuse leftover.example",
            fix_path="evals/httpproxy.yaml",
            fix_old="fqdn: eval-dev.example",
            fix_new="fqdn: eval-{{sha}}.example",
            fix_obs="planted loyalty-hold-8 0.13 on sha fqdn",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-8 0.13",
            test="tests/test_contour_fqdn_sha.py",
            test_body="assert fqdn includes sha; leftover.example unused",
            test_obs="test_contour_not_fqdn_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-8",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-8",
            diff_obs=" evals/httpproxy.yaml | 2+-\n tests/test_contour_fqdn_sha.py | 12++\n",
            residual="TLS leftover still leftover.example.",
        ),
        _bad(
            slug="gatewayapi-httproute-stale-w48d",
            domain="gatewayapi-eval",
            kind="net",
            avoided="r436 contour; r422 istio; r319 Aim hash",
            goal=(
                "Gateway API leftover HTTPRoute eval still parent leftover so planted "
                "cancel-hold-8 never attaches. Pin the parent locally."
            ),
            plan="Dump HTTPRoute, pin SHA, prove planted cancel-hold-8 locally.",
            outcome=(
                "Local parent is eval-<sha>. Planted cancel-hold-8 present locally. Handoff: "
                "the Gateway leftover still leftover."
            ),
            ticket=(
                "Title: Gateway API leftover parent leftover. planted cancel-hold-8 missing."
            ),
            src="evals/httproute.yaml",
            src_obs="parentRefs:\n  - name: leftover  # leftover",
            run="evals/gatewayapi_eval.py",
            fail_obs="parent leftover leftover. planted cancel-hold-8 missing",
            inspect="evals/httproute.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/httproute.yaml",
            first_old="- name: leftover",
            first_new="- name: eval-dev",
            first_obs="dev local. Gateway leftover still leftover",
            rate_tail="Gateway leftover leftover",
            still_after_429="Gateway leftover; planted cancel-hold-8 missing",
            grep="name: leftover|parentRefs|goldens",
            grep_obs="cannot change Gateway leftover from this ticket",
            plan_change="local parent SHA; document Gateway leftover leftover",
            fix_path="evals/httproute.yaml",
            fix_old="- name: eval-dev",
            fix_new="- name: eval-{{sha}}",
            fix_obs="local planted present. Gateway leftover HANDOFF",
            retry_obs="502 unused. Gateway leftover httproute. Partial",
            test="tests/test_gatewayapi_parent_sha.py",
            test_body="xfail Gateway leftover leftover; local SHA parent",
            test_obs="Gateway leftover httproute. Partial",
            suite_obs="local SHA parent. Gateway leftover leftover. Partial.",
            gate_obs="local SHA parent. Gateway leftover leftover. Partial.",
            diff_obs=" evals/httproute.yaml | 2+-\n HANDOFF gateway leftover\n",
            residual="Gateway leftover still leftover. Partial.",
        ),
    )
)

# r437 waypoint leftover
PAIRS.append(
    (
        _ok(
            slug="waypoint-app-stale-x49e",
            domain="waypoint-eval",
            kind="deploy",
            avoided="r418 capistrano; r343 nomad; r319 ClearML uri",
            goal=(
                "Waypoint leftover app eval still deploy leftover so planted "
                "tax-hold-8 never ships. Pin the app to this SHA."
            ),
            plan="Dump waypoint.hcl, pin SHA, prove planted tax-hold-8 fail.",
            outcome=(
                "app is eval-<sha>. Planted tax-hold-8 0.14 fail-closed. Residual: a "
                "runner leftover still waypoint deploy eval."
            ),
            ticket=(
                "Title: Waypoint leftover app eval. planted tax-hold-8 missing."
            ),
            src="waypoint.hcl",
            src_obs='app "eval" {  # leftover',
            run="evals/waypoint_eval.py",
            fail_obs="app leftover eval. planted tax-hold-8 missing",
            inspect="waypoint.hcl",
            inspect_obs="eval leftover",
            first_path="waypoint.hcl",
            first_old='app "eval"',
            first_new='app "eval-dev"',
            first_obs="dev local. runner leftover still eval",
            rate_tail="runner leftover waypoint deploy eval",
            still_after_429="runner leftover; planted tax-hold-8 missing",
            grep="app .eval|waypoint.hcl|goldens",
            grep_obs="app eval-<sha>; ignore runner leftover",
            plan_change="app eval-<sha>; refuse eval",
            fix_path="waypoint.hcl",
            fix_old='app "eval-dev"',
            fix_new='app "eval-{{sha}}"',
            fix_obs="planted tax-hold-8 0.14 on sha app",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-hold-8 0.14",
            test="tests/test_waypoint_app_sha.py",
            test_body="assert app includes sha; eval unused",
            test_obs="test_waypoint_not_app_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-8",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-hold-8",
            diff_obs=" waypoint.hcl | 2+-\n tests/test_waypoint_app_sha.py | 12++\n",
            residual="Runner leftover still waypoint deploy eval.",
        ),
        _bad(
            slug="levant-job-stale-y50f",
            domain="levant-eval",
            kind="deploy",
            avoided="r437 waypoint; r343 nomad; r319 Aim hash",
            goal=(
                "Levant leftover job eval still template leftover so planted "
                "sla-hold-7 never renders. Pin the template locally."
            ),
            plan="Dump levant.yml, pin SHA, prove planted sla-hold-7 locally.",
            outcome=(
                "Local template is this SHA. Planted sla-hold-7 present locally. Handoff: "
                "the nomad leftover still job eval."
            ),
            ticket=(
                "Title: Levant leftover job eval. planted sla-hold-7 missing."
            ),
            src="levant.yml",
            src_obs="job: eval  # leftover",
            run="evals/levant_eval.py",
            fail_obs="job leftover eval. planted sla-hold-7 missing",
            inspect="levant.yml",
            inspect_obs="job eval leftover",
            first_path="levant.yml",
            first_old="job: eval",
            first_new="job: eval-dev",
            first_obs="dev local. nomad leftover still eval",
            rate_tail="nomad leftover job eval",
            still_after_429="nomad leftover; planted sla-hold-7 missing",
            grep="job: eval|levant.yml|goldens",
            grep_obs="cannot change nomad leftover from this ticket",
            plan_change="local job eval-<sha>; document nomad leftover eval",
            fix_path="levant.yml",
            fix_old="job: eval-dev",
            fix_new="job: eval-{{sha}}",
            fix_obs="local planted present. nomad leftover HANDOFF",
            retry_obs="502 unused. nomad leftover levant eval. Partial",
            test="tests/test_levant_job_sha.py",
            test_body="xfail nomad leftover eval; local eval-<sha>",
            test_obs="nomad leftover levant eval. Partial",
            suite_obs="local eval-sha. nomad leftover eval. Partial.",
            gate_obs="local eval-sha. nomad leftover eval. Partial.",
            diff_obs=" levant.yml | 2+-\n HANDOFF levant nomad\n",
            residual="Nomad leftover still job eval. Partial.",
        ),
    )
)

# r438 boundary leftover
PAIRS.append(
    (
        _ok(
            slug="boundary-target-stale-z51g",
            domain="boundary-eval",
            kind="secret",
            avoided="r337 vault; r343 consul; r319 ClearML uri",
            goal=(
                "Boundary leftover target eval still address leftover so planted "
                "membership-hold-6 never connects. Pin the target to this SHA."
            ),
            plan="Dump target, pin SHA, prove planted membership-hold-6 fail.",
            outcome=(
                "target is eval-<sha>. Planted membership-hold-6 0.16 fail-closed. Residual: "
                "a host leftover still leftover."
            ),
            ticket=(
                "Title: Boundary leftover target leftover. planted membership-hold-6 missing."
            ),
            src="evals/boundary.hcl",
            src_obs='name = "leftover"  # leftover',
            run="evals/boundary_eval.py",
            fail_obs="target leftover leftover. planted membership-hold-6 missing",
            inspect="evals/boundary.hcl",
            inspect_obs="leftover leftover",
            first_path="evals/boundary.hcl",
            first_old='name = "leftover"',
            first_new='name = "eval-dev"',
            first_obs="dev local. host leftover still leftover",
            rate_tail="host leftover leftover",
            still_after_429="host leftover; planted membership-hold-6 missing",
            grep="name = .leftover|boundary.hcl|goldens",
            grep_obs="target eval-<sha>; ignore host leftover",
            plan_change="target eval-<sha>; refuse leftover",
            fix_path="evals/boundary.hcl",
            fix_old='name = "eval-dev"',
            fix_new='name = "eval-{{sha}}"',
            fix_obs="planted membership-hold-6 0.16 on sha target",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-hold-6 0.16",
            test="tests/test_boundary_target_sha.py",
            test_body="assert target includes sha; leftover unused",
            test_obs="test_boundary_not_target_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-hold-6",
            diff_obs=" evals/boundary.hcl | 2+-\n tests/test_boundary_target_sha.py | 12++\n",
            residual="Host leftover still leftover.",
        ),
        _bad(
            slug="vaultagent-template-stale-a52h",
            domain="vaultagent-eval",
            kind="secret",
            avoided="r337 vault kv; r438 boundary; r319 Aim hash",
            goal=(
                "Vault Agent leftover template leftover.tpl so planted after-hold-8 never "
                "renders. Pin the template locally."
            ),
            plan="Dump template, pin SHA, prove planted after-hold-8 locally.",
            outcome=(
                "Local template is this SHA. Planted after-hold-8 present locally. Handoff: "
                "the agent leftover still leftover.tpl."
            ),
            ticket=(
                "Title: Vault Agent leftover leftover.tpl. planted after-hold-8 missing."
            ),
            src="evals/vault-agent.hcl",
            src_obs='source = "leftover.tpl"  # leftover',
            run="evals/vaultagent_eval.py",
            fail_obs="template leftover leftover.tpl. planted after-hold-8 missing",
            inspect="evals/vault-agent.hcl",
            inspect_obs="leftover.tpl leftover",
            first_path="evals/vault-agent.hcl",
            first_old='source = "leftover.tpl"',
            first_new='source = "eval-dev.tpl"',
            first_obs="dev local. agent leftover still leftover.tpl",
            rate_tail="agent leftover leftover.tpl",
            still_after_429="agent leftover; planted after-hold-8 missing",
            grep="leftover.tpl|vault-agent|goldens",
            grep_obs="cannot change agent leftover from this ticket",
            plan_change="local SHA template; document agent leftover leftover.tpl",
            fix_path="evals/vault-agent.hcl",
            fix_old='source = "eval-dev.tpl"',
            fix_new='source = "eval-{{sha}}.tpl"',
            fix_obs="local planted present. agent leftover HANDOFF",
            retry_obs="502 unused. agent leftover leftover.tpl. Partial",
            test="tests/test_vaultagent_tpl_sha.py",
            test_body="xfail agent leftover leftover.tpl; local SHA template",
            test_obs="agent leftover leftover.tpl. Partial",
            suite_obs="local SHA template. agent leftover leftover.tpl. Partial.",
            gate_obs="local SHA template. agent leftover leftover.tpl. Partial.",
            diff_obs=" evals/vault-agent.hcl | 2+-\n HANDOFF vault agent\n",
            residual="Agent leftover still leftover.tpl. Partial.",
        ),
    )
)
