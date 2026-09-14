"""Unique eval-harness leftover plants r445+. Not r319/GEval-cache/test_ or prior leftover clones."""

from mill_plants import PAIRS, _bad, _ok

# r445 rancher leftover
PAIRS.append(
    (
        _ok(
            slug="rancher-cluster-stale-n65u",
            domain="rancher-eval",
            kind="cluster",
            avoided="r444 capi; r396 microk8s; r319 ClearML uri",
            goal=(
                "Rancher leftover cluster leftover so planted dual-hold-6 never targets "
                "this SHA. Pin the cluster to eval-<sha>."
            ),
            plan="Dump cluster, pin SHA, prove planted dual-hold-6 fail.",
            outcome=(
                "cluster is eval-<sha>. Planted dual-hold-6 0.13 fail-closed. Residual: a "
                "project leftover still cluster leftover."
            ),
            ticket=(
                "Title: Rancher leftover cluster leftover. planted dual-hold-6 missing."
            ),
            src="evals/rancher.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/rancher_eval.py",
            fail_obs="cluster leftover leftover. planted dual-hold-6 missing",
            inspect="evals/rancher.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/rancher.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. project leftover still leftover",
            rate_tail="project leftover cluster leftover",
            still_after_429="project leftover; planted dual-hold-6 missing",
            grep="name: leftover|rancher.yaml|goldens",
            grep_obs="cluster eval-<sha>; ignore project leftover",
            plan_change="cluster eval-<sha>; refuse leftover",
            fix_path="evals/rancher.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted dual-hold-6 0.13 on sha cluster",
            retry_obs="502 then retry; 5 pass 1 fail planted dual-hold-6 0.13",
            test="tests/test_rancher_cluster_sha.py",
            test_body="assert cluster includes sha; leftover unused",
            test_obs="test_rancher_not_cluster_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed dual-hold-6",
            diff_obs=" evals/rancher.yaml | 2+-\n tests/test_rancher_cluster_sha.py | 12++\n",
            residual="Project leftover still cluster leftover.",
        ),
        _bad(
            slug="rke2-config-stale-o66v",
            domain="rke2-eval",
            kind="cluster",
            avoided="r445 rancher; r397 k3s; r319 Aim hash",
            goal=(
                "RKE2 leftover config.yaml leftover so planted rain-hold-12 never "
                "loads goldens. Pin the config locally."
            ),
            plan="Dump config, pin SHA, prove planted rain-hold-12 locally.",
            outcome=(
                "Local config is this SHA. Planted rain-hold-12 present locally. Handoff: "
                "the node leftover still leftover.yaml."
            ),
            ticket=(
                "Title: RKE2 leftover leftover.yaml. planted rain-hold-12 missing."
            ),
            src="evals/rke2.yaml",
            src_obs="token: leftover  # leftover",
            run="evals/rke2_eval.py",
            fail_obs="token leftover leftover. planted rain-hold-12 missing",
            inspect="evals/rke2.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/rke2.yaml",
            first_old="token: leftover",
            first_new="token: eval-dev",
            first_obs="dev local. node leftover still leftover",
            rate_tail="node leftover leftover.yaml",
            still_after_429="node leftover; planted rain-hold-12 missing",
            grep="token: leftover|rke2.yaml|goldens",
            grep_obs="cannot change node leftover from this ticket",
            plan_change="local SHA token; document node leftover leftover",
            fix_path="evals/rke2.yaml",
            fix_old="token: eval-dev",
            fix_new="token: eval-{{sha}}",
            fix_obs="local planted present. node leftover HANDOFF",
            retry_obs="502 unused. node leftover leftover.yaml. Partial",
            test="tests/test_rke2_token_sha.py",
            test_body="xfail node leftover leftover; local SHA token",
            test_obs="node leftover leftover.yaml. Partial",
            suite_obs="local SHA token. node leftover leftover. Partial.",
            gate_obs="local SHA token. node leftover leftover. Partial.",
            diff_obs=" evals/rke2.yaml | 2+-\n HANDOFF rke2 node\n",
            residual="Node leftover still leftover.yaml. Partial.",
        ),
    )
)

# r446 more cluster leftover
PAIRS.append(
    (
        _ok(
            slug="eksctl-cluster-stale-p67w",
            domain="eksctl-eval",
            kind="cluster",
            avoided="r445 rancher; r326 sagemaker; r319 ClearML uri",
            goal=(
                "eksctl leftover cluster leftover so planted flash-hold-13 never "
                "targets this SHA. Pin metadata.name to eval-<sha>."
            ),
            plan="Dump cluster yaml, pin SHA, prove planted flash-hold-13 fail.",
            outcome=(
                "name is eval-<sha>. Planted flash-hold-13 0.14 fail-closed. Residual: a "
                "kubeconfig leftover still leftover."
            ),
            ticket=(
                "Title: eksctl leftover cluster leftover. planted flash-hold-13 missing."
            ),
            src="evals/eksctl.yaml",
            src_obs="metadata:\n  name: leftover  # leftover",
            run="evals/eksctl_eval.py",
            fail_obs="name leftover leftover. planted flash-hold-13 missing",
            inspect="evals/eksctl.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/eksctl.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. kubeconfig leftover still leftover",
            rate_tail="kubeconfig leftover leftover",
            still_after_429="kubeconfig leftover; planted flash-hold-13 missing",
            grep="name: leftover|eksctl.yaml|goldens",
            grep_obs="name eval-<sha>; ignore kubeconfig leftover",
            plan_change="name eval-<sha>; refuse leftover",
            fix_path="evals/eksctl.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted flash-hold-13 0.14 on sha cluster",
            retry_obs="502 then retry; 5 pass 1 fail planted flash-hold-13 0.14",
            test="tests/test_eksctl_name_sha.py",
            test_body="assert name includes sha; leftover unused",
            test_obs="test_eksctl_not_name_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-13",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed flash-hold-13",
            diff_obs=" evals/eksctl.yaml | 2+-\n tests/test_eksctl_name_sha.py | 12++\n",
            residual="Kubeconfig leftover still leftover.",
        ),
        _bad(
            slug="gke-cluster-stale-q68x",
            domain="gke-eval",
            kind="cluster",
            avoided="r446 eksctl; r326 databricks; r319 Aim hash",
            goal=(
                "gcloud leftover cluster leftover so planted promo-hold-12 never "
                "targets this SHA. Pin the cluster locally."
            ),
            plan="Dump gke yaml, pin SHA, prove planted promo-hold-12 locally.",
            outcome=(
                "Local cluster is eval-<sha>. Planted promo-hold-12 present locally. "
                "Handoff: the project leftover still leftover."
            ),
            ticket=(
                "Title: GKE leftover cluster leftover. planted promo-hold-12 missing."
            ),
            src="evals/gke.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/gke_eval.py",
            fail_obs="name leftover leftover. planted promo-hold-12 missing",
            inspect="evals/gke.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/gke.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. project leftover still leftover",
            rate_tail="project leftover leftover",
            still_after_429="project leftover; planted promo-hold-12 missing",
            grep="name: leftover|gke.yaml|goldens",
            grep_obs="cannot change project leftover from this ticket",
            plan_change="local name SHA; document project leftover leftover",
            fix_path="evals/gke.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. project leftover HANDOFF",
            retry_obs="502 unused. project leftover leftover. Partial",
            test="tests/test_gke_name_sha.py",
            test_body="xfail project leftover leftover; local SHA name",
            test_obs="project leftover leftover. Partial",
            suite_obs="local SHA name. project leftover leftover. Partial.",
            gate_obs="local SHA name. project leftover leftover. Partial.",
            diff_obs=" evals/gke.yaml | 2+-\n HANDOFF gke project\n",
            residual="Project leftover still leftover. Partial.",
        ),
    )
)

# r447 aks leftover
PAIRS.append(
    (
        _ok(
            slug="aks-cluster-stale-r69y",
            domain="aks-eval",
            kind="cluster",
            avoided="r446 eksctl; r446 gke; r319 ClearML uri",
            goal=(
                "AKS leftover cluster leftover so planted gift-hold-12 never targets "
                "this SHA. Pin the cluster name."
            ),
            plan="Dump aks yaml, pin SHA, prove planted gift-hold-12 fail.",
            outcome=(
                "name is eval-<sha>. Planted gift-hold-12 0.15 fail-closed. Residual: a "
                "resource-group leftover still leftover."
            ),
            ticket=(
                "Title: AKS leftover cluster leftover. planted gift-hold-12 missing."
            ),
            src="evals/aks.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/aks_eval.py",
            fail_obs="name leftover leftover. planted gift-hold-12 missing",
            inspect="evals/aks.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/aks.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. rg leftover still leftover",
            rate_tail="resource-group leftover leftover",
            still_after_429="rg leftover; planted gift-hold-12 missing",
            grep="name: leftover|aks.yaml|goldens",
            grep_obs="name eval-<sha>; ignore rg leftover",
            plan_change="name eval-<sha>; refuse leftover",
            fix_path="evals/aks.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted gift-hold-12 0.15 on sha cluster",
            retry_obs="502 then retry; 5 pass 1 fail planted gift-hold-12 0.15",
            test="tests/test_aks_name_sha.py",
            test_body="assert name includes sha; leftover unused",
            test_obs="test_aks_not_name_leftover",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-12",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed gift-hold-12",
            diff_obs=" evals/aks.yaml | 2+-\n tests/test_aks_name_sha.py | 12++\n",
            residual="Resource-group leftover still leftover.",
        ),
        _bad(
            slug="oc-cluster-stale-s70z",
            domain="oc-eval",
            kind="cluster",
            avoided="r447 aks; r445 rancher; r319 Aim hash",
            goal=(
                "OpenShift leftover project leftover so planted bundle-hold-11 never "
                "deploys. Pin the project locally."
            ),
            plan="Dump project, pin SHA, prove planted bundle-hold-11 locally.",
            outcome=(
                "Local project is eval-<sha>. Planted bundle-hold-11 present locally. "
                "Handoff: the kubeconfig leftover still leftover."
            ),
            ticket=(
                "Title: OpenShift leftover project leftover. planted bundle-hold-11 missing."
            ),
            src="evals/oc.yaml",
            src_obs="name: leftover  # leftover",
            run="evals/oc_eval.py",
            fail_obs="project leftover leftover. planted bundle-hold-11 missing",
            inspect="evals/oc.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/oc.yaml",
            first_old="name: leftover",
            first_new="name: eval-dev",
            first_obs="dev local. kubeconfig leftover still leftover",
            rate_tail="kubeconfig leftover leftover",
            still_after_429="kubeconfig leftover; planted bundle-hold-11 missing",
            grep="name: leftover|oc.yaml|goldens",
            grep_obs="cannot change kubeconfig leftover from this ticket",
            plan_change="local project SHA; document kubeconfig leftover leftover",
            fix_path="evals/oc.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. kubeconfig leftover HANDOFF",
            retry_obs="502 unused. kubeconfig leftover leftover. Partial",
            test="tests/test_oc_project_sha.py",
            test_body="xfail kubeconfig leftover leftover; local SHA project",
            test_obs="kubeconfig leftover leftover. Partial",
            suite_obs="local SHA project. kubeconfig leftover leftover. Partial.",
            gate_obs="local SHA project. kubeconfig leftover leftover. Partial.",
            diff_obs=" evals/oc.yaml | 2+-\n HANDOFF oc kubeconfig\n",
            residual="Kubeconfig leftover still leftover. Partial.",
        ),
    )
)

# r448 more leftover
PAIRS.append(
    (
        _ok(
            slug="kops-cluster-stale-t71a",
            domain="kops-eval",
            kind="cluster",
            avoided="r446 eksctl; r444 capi; r319 ClearML uri",
            goal=(
                "kOps leftover cluster leftover.k8s.local so planted loyalty-hold-10 "
                "never targets this SHA. Pin the cluster name."
            ),
            plan="Dump cluster spec, pin SHA, prove planted loyalty-hold-10 fail.",
            outcome=(
                "name is eval-<sha>.k8s.local. Planted loyalty-hold-10 0.12 fail-closed. "
                "Residual: an S3 leftover still leftover.k8s.local."
            ),
            ticket=(
                "Title: kOps leftover leftover.k8s.local. planted loyalty-hold-10 missing."
            ),
            src="evals/kops.yaml",
            src_obs="name: leftover.k8s.local  # leftover",
            run="evals/kops_eval.py",
            fail_obs="name leftover leftover.k8s.local. planted loyalty-hold-10 missing",
            inspect="evals/kops.yaml",
            inspect_obs="leftover.k8s.local leftover",
            first_path="evals/kops.yaml",
            first_old="name: leftover.k8s.local",
            first_new="name: eval-dev.k8s.local",
            first_obs="dev local. S3 leftover still leftover.k8s.local",
            rate_tail="S3 leftover leftover.k8s.local",
            still_after_429="S3 leftover; planted loyalty-hold-10 missing",
            grep="leftover.k8s.local|kops.yaml|goldens",
            grep_obs="name eval-<sha>.k8s.local; ignore S3 leftover",
            plan_change="name eval-<sha>.k8s.local; refuse leftover.k8s.local",
            fix_path="evals/kops.yaml",
            fix_old="name: eval-dev.k8s.local",
            fix_new="name: eval-{{sha}}.k8s.local",
            fix_obs="planted loyalty-hold-10 0.12 on sha cluster",
            retry_obs="502 then retry; 5 pass 1 fail planted loyalty-hold-10 0.12",
            test="tests/test_kops_name_sha.py",
            test_body="assert name includes sha; leftover.k8s.local unused",
            test_obs="test_kops_not_leftover_local",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-10",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed loyalty-hold-10",
            diff_obs=" evals/kops.yaml | 2+-\n tests/test_kops_name_sha.py | 12++\n",
            residual="S3 leftover still leftover.k8s.local.",
        ),
        _bad(
            slug="kubeadm-cfg-stale-u72b",
            domain="kubeadm-eval",
            kind="cluster",
            avoided="r448 kops; r395 kind; r319 Aim hash",
            goal=(
                "kubeadm leftover ClusterConfiguration leftover so planted cancel-hold-10 "
                "never joins. Pin the config locally."
            ),
            plan="Dump kubeadm yaml, pin SHA, prove planted cancel-hold-10 locally.",
            outcome=(
                "Local clusterName is eval-<sha>. Planted cancel-hold-10 present locally. "
                "Handoff: the control-plane leftover still leftover."
            ),
            ticket=(
                "Title: kubeadm leftover clusterName leftover. planted cancel-hold-10 missing."
            ),
            src="evals/kubeadm.yaml",
            src_obs="clusterName: leftover  # leftover",
            run="evals/kubeadm_eval.py",
            fail_obs="clusterName leftover leftover. planted cancel-hold-10 missing",
            inspect="evals/kubeadm.yaml",
            inspect_obs="leftover leftover",
            first_path="evals/kubeadm.yaml",
            first_old="clusterName: leftover",
            first_new="clusterName: eval-dev",
            first_obs="dev local. control-plane leftover still leftover",
            rate_tail="control-plane leftover leftover",
            still_after_429="control-plane leftover; planted cancel-hold-10 missing",
            grep="clusterName: leftover|kubeadm.yaml|goldens",
            grep_obs="cannot change control-plane leftover from this ticket",
            plan_change="local SHA name; document control-plane leftover leftover",
            fix_path="evals/kubeadm.yaml",
            fix_old="clusterName: eval-dev",
            fix_new="clusterName: eval-{{sha}}",
            fix_obs="local planted present. control-plane leftover HANDOFF",
            retry_obs="502 unused. control-plane leftover leftover. Partial",
            test="tests/test_kubeadm_name_sha.py",
            test_body="xfail control-plane leftover leftover; local SHA name",
            test_obs="control-plane leftover leftover. Partial",
            suite_obs="local SHA name. control-plane leftover leftover. Partial.",
            gate_obs="local SHA name. control-plane leftover leftover. Partial.",
            diff_obs=" evals/kubeadm.yaml | 2+-\n HANDOFF kubeadm cp\n",
            residual="Control-plane leftover still leftover. Partial.",
        ),
    )
)
