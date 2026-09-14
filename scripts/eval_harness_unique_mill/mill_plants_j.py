"""Unique eval-harness leftover plants r396+. Not r319/GEval-cache/test_ or prior leftover clones."""

from mill_plants import PAIRS, _bad, _ok

# r396 local-k8s leftover
PAIRS.append(
    (
        _ok(
            slug="minikube-iso-stale-t67a",
            domain="minikube-eval",
            kind="cluster",
            avoided="r395 kind image; r394 colima disk; r319 ClearML uri",
            goal=(
                "minikube leftover iso minikube-eval.iso is last week so planted "
                "tax-void-4 never boots. Pin the iso to this SHA."
            ),
            plan="Dump minikube config, pin SHA iso, prove planted tax-void-4 fail.",
            outcome=(
                "ISO is minikube-eval-<sha>.iso. Planted tax-void-4 0.13 fail-closed. Residual: "
                "a profile leftover still --iso-url minikube-eval.iso."
            ),
            ticket=(
                "Title: minikube leftover iso last week. planted tax-void-4 missing."
            ),
            src="evals/minikube.sh",
            src_obs="minikube start --iso-url minikube-eval.iso  # leftover",
            run="evals/minikube_eval.py",
            fail_obs="iso leftover last week. planted tax-void-4 absent",
            inspect="evals/minikube.sh",
            inspect_obs="stable iso leftover",
            first_path="evals/minikube.sh",
            first_old="--iso-url minikube-eval.iso",
            first_new="--iso-url minikube-eval-dev.iso",
            first_obs="dev local. profile leftover still minikube-eval.iso",
            rate_tail="profile leftover --iso-url minikube-eval.iso",
            still_after_429="profile leftover iso; planted tax-void-4 absent",
            grep="minikube-eval.iso|iso-url|goldens",
            grep_obs="iso minikube-eval-<sha>.iso; ignore profile leftover",
            plan_change="iso SHA file; refuse stable minikube-eval.iso",
            fix_path="evals/minikube.sh",
            fix_old="--iso-url minikube-eval-dev.iso",
            fix_new="--iso-url minikube-eval-$GIT_SHA.iso",
            fix_obs="planted tax-void-4 0.13 in sha iso",
            retry_obs="502 then retry; 5 pass 1 fail planted tax-void-4 0.13",
            test="tests/test_minikube_iso_sha.py",
            test_body="assert iso includes sha; stable unused",
            test_obs="test_minikube_not_stable_iso",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed tax-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed tax-void-4",
            diff_obs=" evals/minikube.sh | 2+-\n tests/test_minikube_iso_sha.py | 12++\n",
            residual="Profile leftover still --iso-url minikube-eval.iso.",
        ),
        _bad(
            slug="microk8s-addon-stale-u68b",
            domain="microk8s-eval",
            kind="cluster",
            avoided="r395 k3d; r396 minikube; r319 Aim hash",
            goal=(
                "microk8s leftover addon eval still points at yesterday goldens so planted "
                "sla-void-4 never loads. Pin the addon path locally."
            ),
            plan="Dump addon, pin SHA, prove planted sla-void-4 locally.",
            outcome=(
                "Local addon path is this SHA. Planted sla-void-4 present locally. Handoff: "
                "the snap leftover still addon eval yesterday."
            ),
            ticket=(
                "Title: microk8s leftover addon eval yesterday. planted sla-void-4 missing."
            ),
            src="evals/microk8s-addon.yaml",
            src_obs="goldensPath: /var/snap/microk8s/eval  # leftover",
            run="evals/microk8s_eval.py",
            fail_obs="addon leftover yesterday. planted sla-void-4 absent",
            inspect="evals/microk8s-addon.yaml",
            inspect_obs="stable path leftover",
            first_path="evals/microk8s-addon.yaml",
            first_old="goldensPath: /var/snap/microk8s/eval",
            first_new="goldensPath: /var/snap/microk8s/eval-dev",
            first_obs="dev local. snap leftover still /eval",
            rate_tail="snap leftover addon eval yesterday",
            still_after_429="snap leftover; planted sla-void-4 absent",
            grep="microk8s/eval|addon|goldensPath",
            grep_obs="cannot change snap leftover from this ticket",
            plan_change="local SHA path; document snap leftover addon",
            fix_path="evals/microk8s-addon.yaml",
            fix_old="goldensPath: /var/snap/microk8s/eval-dev",
            fix_new="goldensPath: /var/snap/microk8s/eval-{{sha}}",
            fix_obs="local planted present. snap leftover HANDOFF",
            retry_obs="502 unused. snap leftover addon. Partial",
            test="tests/test_microk8s_addon_sha.py",
            test_body="xfail snap leftover addon; local SHA path",
            test_obs="snap leftover addon. Partial",
            suite_obs="local SHA path. snap leftover addon. Partial.",
            gate_obs="local SHA path. snap leftover addon. Partial.",
            diff_obs=" evals/microk8s-addon.yaml | 2+-\n HANDOFF microk8s snap\n",
            residual="Snap leftover still addon eval yesterday. Partial.",
        ),
    )
)

# r397 distro-k8s leftover
PAIRS.append(
    (
        _ok(
            slug="k3s-airgap-stale-v69c",
            domain="k3s-eval",
            kind="cluster",
            avoided="r395 k3d; r396 minikube; r319 ClearML uri",
            goal=(
                "k3s leftover airgap images.tar is last week so planted hold-void-7 never "
                "imports. Pin the tarball to this SHA."
            ),
            plan="Dump airgap path, pin SHA, prove planted hold-void-7 fail.",
            outcome=(
                "Airgap tarball is k3s-airgap-<sha>.tar. Planted hold-void-7 0.14 fail-closed. "
                "Residual: an install leftover still k3s-airgap-images.tar."
            ),
            ticket=(
                "Title: k3s leftover airgap images.tar last week. planted hold-void-7 missing."
            ),
            src="evals/k3s.sh",
            src_obs="cp k3s-airgap-images.tar /var/lib/rancher/k3s/agent/images/  # leftover",
            run="evals/k3s_eval.py",
            fail_obs="airgap leftover last week. planted hold-void-7 absent",
            inspect="evals/k3s.sh",
            inspect_obs="stable tarball leftover",
            first_path="evals/k3s.sh",
            first_old="k3s-airgap-images.tar",
            first_new="k3s-airgap-images-dev.tar",
            first_obs="dev local. install leftover still k3s-airgap-images.tar",
            rate_tail="install leftover k3s-airgap-images.tar",
            still_after_429="install leftover tar; planted hold-void-7 absent",
            grep="k3s-airgap-images|agent/images|goldens",
            grep_obs="tarball SHA; ignore install leftover",
            plan_change="airgap k3s-airgap-<sha>.tar; refuse stable tar",
            fix_path="evals/k3s.sh",
            fix_old="k3s-airgap-images-dev.tar",
            fix_new="k3s-airgap-images-$GIT_SHA.tar",
            fix_obs="planted hold-void-7 0.14 in sha tar",
            retry_obs="502 then retry; 5 pass 1 fail planted hold-void-7 0.14",
            test="tests/test_k3s_airgap_sha.py",
            test_body="assert airgap tar includes sha",
            test_obs="test_k3s_not_stable_airgap",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed hold-void-7",
            diff_obs=" evals/k3s.sh | 2+-\n tests/test_k3s_airgap_sha.py | 12++\n",
            residual="Install leftover still k3s-airgap-images.tar.",
        ),
        _bad(
            slug="k0s-bundle-stale-w70d",
            domain="k0s-eval",
            kind="cluster",
            avoided="r397 k3s; r395 kind; r319 Aim hash",
            goal=(
                "k0s leftover bundle k0s-bundle.tar is last week so planted "
                "membership-void-3 never imports. Pin locally."
            ),
            plan="Dump bundle, pin SHA, prove planted membership-void-3 locally.",
            outcome=(
                "Local bundle is k0s-bundle-<sha>.tar. Planted membership-void-3 present "
                "locally. Handoff: the installer leftover still k0s-bundle.tar."
            ),
            ticket=(
                "Title: k0s leftover bundle last week. planted membership-void-3 missing."
            ),
            src="evals/k0s.sh",
            src_obs="k0s install --bundle k0s-bundle.tar  # leftover",
            run="evals/k0s_eval.py",
            fail_obs="bundle leftover last week. planted membership-void-3 absent",
            inspect="evals/k0s.sh",
            inspect_obs="stable bundle leftover",
            first_path="evals/k0s.sh",
            first_old="k0s-bundle.tar",
            first_new="k0s-bundle-dev.tar",
            first_obs="dev local. installer leftover still k0s-bundle.tar",
            rate_tail="installer leftover k0s-bundle.tar",
            still_after_429="installer leftover; planted membership-void-3 absent",
            grep="k0s-bundle|install --bundle|goldens",
            grep_obs="cannot change installer leftover from this ticket",
            plan_change="local SHA bundle; document installer leftover tar",
            fix_path="evals/k0s.sh",
            fix_old="k0s-bundle-dev.tar",
            fix_new="k0s-bundle-$GIT_SHA.tar",
            fix_obs="local planted present. installer leftover HANDOFF",
            retry_obs="502 unused. installer leftover bundle. Partial",
            test="tests/test_k0s_bundle_sha.py",
            test_body="xfail installer leftover tar; local SHA bundle",
            test_obs="installer leftover bundle. Partial",
            suite_obs="local SHA bundle. installer leftover tar. Partial.",
            gate_obs="local SHA bundle. installer leftover tar. Partial.",
            diff_obs=" evals/k0s.sh | 2+-\n HANDOFF k0s installer\n",
            residual="Installer leftover still k0s-bundle.tar. Partial.",
        ),
    )
)

# r398 gitops leftover
PAIRS.append(
    (
        _ok(
            slug="kustomize-overlay-stale-x71e",
            domain="kustomize-eval",
            kind="gitops",
            avoided="r291 judge-model; r308 bazel omit; r319 ClearML uri",
            goal=(
                "Kustomize leftover overlay overlays/legacy still omits goldens so planted "
                "after-void-4 never ships. Point kustomization at overlays/sha."
            ),
            plan="Dump kustomization, retarget, prove planted after-void-4 fail.",
            outcome=(
                "Overlay is overlays/<sha>. Planted after-void-4 0.15 fail-closed. Residual: "
                "a pipeline leftover still -k overlays/legacy."
            ),
            ticket=(
                "Title: Kustomize leftover overlays/legacy. planted after-void-4 missing."
            ),
            src="overlays/legacy/kustomization.yaml",
            src_obs="resources:\n- ../../evals  # leftover no goldens",
            run="evals/kustomize_eval.py",
            fail_obs="legacy leftover no goldens. planted after-void-4 absent",
            inspect="overlays/legacy/kustomization.yaml",
            inspect_obs="no goldens leftover",
            first_path="overlays/legacy/kustomization.yaml",
            first_old="- ../../evals",
            first_new="- ../../evals\n- ../../goldens",
            first_obs="goldens local. pipeline leftover still -k overlays/legacy",
            rate_tail="pipeline leftover -k overlays/legacy",
            still_after_429="pipeline leftover overlay; planted after-void-4 absent",
            grep="overlays/legacy|goldens|kustomization",
            grep_obs="use overlays/<sha>; ignore pipeline leftover",
            plan_change="overlay overlays/<sha> with goldens; refuse legacy",
            fix_path="evals/kustomize_eval.py",
            fix_old="kustomize build overlays/legacy",
            fix_new="kustomize build overlays/$GIT_SHA",
            fix_obs="planted after-void-4 0.15 in sha overlay",
            retry_obs="502 then retry; 5 pass 1 fail planted after-void-4 0.15",
            test="tests/test_kustomize_overlay_sha.py",
            test_body="assert overlay is overlays/<sha>; legacy unused",
            test_obs="test_kustomize_not_legacy_overlay",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-void-4",
            diff_obs=" overlays/legacy/kustomization.yaml | 4+-\n tests/test_kustomize_overlay_sha.py | 12++\n",
            residual="Pipeline leftover still -k overlays/legacy.",
        ),
        _bad(
            slug="kapp-app-stale-y72f",
            domain="kapp-eval",
            kind="gitops",
            avoided="r398 kustomize; r314 argo; r319 Aim hash",
            goal=(
                "kapp leftover app eval still deploys yesterday goldens so planted "
                "sku-void-2 never appears. Create app eval-<sha> locally."
            ),
            plan="Dump kapp app, pin SHA, prove planted sku-void-2 locally.",
            outcome=(
                "Local app is eval-<sha>. Planted sku-void-2 present locally. Handoff: the "
                "cluster leftover still kapp deploy -a eval."
            ),
            ticket=(
                "Title: kapp leftover app eval. planted sku-void-2 missing."
            ),
            src="evals/kapp.sh",
            src_obs="kapp deploy -a eval -f overlays/legacy  # leftover",
            run="evals/kapp_eval.py",
            fail_obs="app leftover yesterday. planted sku-void-2 absent",
            inspect="evals/kapp.sh",
            inspect_obs="stable app leftover",
            first_path="evals/kapp.sh",
            first_old="-a eval",
            first_new="-a eval-dev",
            first_obs="dev local. cluster leftover still -a eval",
            rate_tail="cluster leftover kapp deploy -a eval",
            still_after_429="cluster leftover app; planted sku-void-2 absent",
            grep="-a eval|kapp deploy|goldens",
            grep_obs="cannot change cluster leftover from this ticket",
            plan_change="local app eval-<sha>; document cluster leftover eval",
            fix_path="evals/kapp.sh",
            fix_old="-a eval-dev",
            fix_new="-a eval-$GIT_SHA",
            fix_obs="local planted present. cluster leftover HANDOFF",
            retry_obs="502 unused. cluster leftover kapp eval. Partial",
            test="tests/test_kapp_app_sha.py",
            test_body="xfail cluster leftover -a eval; local eval-<sha>",
            test_obs="cluster leftover kapp eval. Partial",
            suite_obs="local eval-sha. cluster leftover eval. Partial.",
            gate_obs="local eval-sha. cluster leftover eval. Partial.",
            diff_obs=" evals/kapp.sh | 2+-\n HANDOFF kapp cluster\n",
            residual="Cluster leftover still kapp deploy -a eval. Partial.",
        ),
    )
)

# r399 flux leftover
PAIRS.append(
    (
        _ok(
            slug="flux-ks-stale-z73g",
            domain="flux-eval",
            kind="gitops",
            avoided="r398 kustomize; r314 argo; r319 ClearML uri",
            goal=(
                "Flux leftover Kustomization eval still path overlays/legacy so planted "
                "rain-void-5 never reconciles. Pin path to overlays/sha."
            ),
            plan="Dump ks, pin SHA path, prove planted rain-void-5 fail.",
            outcome=(
                "KS path is overlays/<sha>. Planted rain-void-5 0.12 fail-closed. Residual: "
                "a GitRepository leftover still ref name leftover/main."
            ),
            ticket=(
                "Title: Flux leftover KS path overlays/legacy. planted rain-void-5 missing."
            ),
            src="clusters/eval/ks.yaml",
            src_obs="path: overlays/legacy  # leftover",
            run="evals/flux_eval.py",
            fail_obs="legacy leftover. planted rain-void-5 absent",
            inspect="clusters/eval/ks.yaml",
            inspect_obs="legacy leftover",
            first_path="clusters/eval/ks.yaml",
            first_old="path: overlays/legacy",
            first_new="path: overlays/dev",
            first_obs="dev local. GitRepository leftover still leftover/main",
            rate_tail="GitRepository leftover leftover/main",
            still_after_429="repo leftover; planted rain-void-5 absent",
            grep="overlays/legacy|Kustomization|goldens",
            grep_obs="path overlays/<sha>; ignore repo leftover",
            plan_change="KS path overlays/<sha>; refuse leftover/main",
            fix_path="clusters/eval/ks.yaml",
            fix_old="path: overlays/dev",
            fix_new="path: overlays/{{sha}}",
            fix_obs="planted rain-void-5 0.12 in sha path",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-void-5 0.12",
            test="tests/test_flux_ks_sha.py",
            test_body="assert KS path includes sha; legacy unused",
            test_obs="test_flux_not_legacy_path",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-5",
            diff_obs=" clusters/eval/ks.yaml | 2+-\n tests/test_flux_ks_sha.py | 12++\n",
            residual="GitRepository leftover still ref leftover/main.",
        ),
        _bad(
            slug="fleet-bundle-stale-a74h",
            domain="fleet-eval",
            kind="gitops",
            avoided="r399 flux; r398 kapp; r319 Aim hash",
            goal=(
                "Fleet leftover bundle eval still targets yesterday goldens so planted "
                "flash-void-5 never deploys. Pin the bundle locally."
            ),
            plan="Dump fleet.yaml, pin SHA, prove planted flash-void-5 locally.",
            outcome=(
                "Local bundle is eval-<sha>. Planted flash-void-5 present locally. Handoff: "
                "the workspace leftover still bundle eval."
            ),
            ticket=(
                "Title: Fleet leftover bundle eval. planted flash-void-5 missing."
            ),
            src="fleet.yaml",
            src_obs="name: eval  # leftover",
            run="evals/fleet_eval.py",
            fail_obs="bundle leftover yesterday. planted flash-void-5 absent",
            inspect="fleet.yaml",
            inspect_obs="name eval leftover",
            first_path="fleet.yaml",
            first_old="name: eval",
            first_new="name: eval-dev",
            first_obs="dev local. workspace leftover still eval",
            rate_tail="workspace leftover bundle eval",
            still_after_429="workspace leftover; planted flash-void-5 absent",
            grep="name: eval|fleet.yaml|goldens",
            grep_obs="cannot change workspace leftover from this ticket",
            plan_change="local bundle eval-<sha>; document workspace leftover",
            fix_path="fleet.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="local planted present. workspace leftover HANDOFF",
            retry_obs="502 unused. workspace leftover fleet eval. Partial",
            test="tests/test_fleet_bundle_sha.py",
            test_body="xfail workspace leftover eval; local eval-<sha>",
            test_obs="workspace leftover fleet eval. Partial",
            suite_obs="local eval-sha. workspace leftover eval. Partial.",
            gate_obs="local eval-sha. workspace leftover eval. Partial.",
            diff_obs=" fleet.yaml | 2+-\n HANDOFF fleet workspace\n",
            residual="Workspace leftover still bundle eval. Partial.",
        ),
    )
)

# r400 iac leftover
PAIRS.append(
    (
        _ok(
            slug="tofu-state-stale-b75i",
            domain="tofu-eval",
            kind="iac",
            avoided="r305 nix gcroot; r343 nomad artifact; r319 ClearML uri",
            goal=(
                "OpenTofu leftover state eval.tfstate is yesterday so planted "
                "promo-void-6 never applies. Pin the state key to this SHA."
            ),
            plan="Dump backend, pin SHA key, prove planted promo-void-6 fail.",
            outcome=(
                "State key is eval/<sha>.tfstate. Planted promo-void-6 0.16 fail-closed. "
                "Residual: a backend leftover still key=eval.tfstate."
            ),
            ticket=(
                "Title: OpenTofu leftover state eval.tfstate. planted promo-void-6 missing."
            ),
            src="backend.tf",
            src_obs='key = "eval.tfstate"  # leftover',
            run="evals/tofu_eval.py",
            fail_obs="state leftover yesterday. planted promo-void-6 absent",
            inspect="backend.tf",
            inspect_obs="stable key leftover",
            first_path="backend.tf",
            first_old='key = "eval.tfstate"',
            first_new='key = "eval-dev.tfstate"',
            first_obs="dev local. backend leftover still eval.tfstate",
            rate_tail="backend leftover key=eval.tfstate",
            still_after_429="backend leftover state; planted promo-void-6 absent",
            grep="eval.tfstate|backend|goldens",
            grep_obs="key eval/<sha>.tfstate; ignore leftover key",
            plan_change="state key eval/<sha>.tfstate; refuse eval.tfstate",
            fix_path="backend.tf",
            fix_old='key = "eval-dev.tfstate"',
            fix_new='key = "eval/${git_sha}.tfstate"',
            fix_obs="planted promo-void-6 0.16 in sha state",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-void-6 0.16",
            test="tests/test_tofu_state_sha.py",
            test_body="assert state key includes sha; eval.tfstate unused",
            test_obs="test_tofu_not_eval_tfstate",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-6",
            diff_obs=" backend.tf | 2+-\n tests/test_tofu_state_sha.py | 12++\n",
            residual="Backend leftover still key=eval.tfstate.",
        ),
        _bad(
            slug="terragrunt-cache-stale-c76j",
            domain="terragrunt-eval",
            kind="iac",
            avoided="r400 tofu; r308 earthly; r319 Aim hash",
            goal=(
                "Terragrunt leftover .terragrunt-cache still has yesterday goldens so planted "
                "gift-void-6 never plans. Bust the cache locally."
            ),
            plan="Dump cache, bust, prove planted gift-void-6 locally.",
            outcome=(
                "Local cache is .terragrunt-cache-<sha>. Planted gift-void-6 present locally. "
                "Handoff: the runner leftover still .terragrunt-cache."
            ),
            ticket=(
                "Title: Terragrunt leftover .terragrunt-cache. planted gift-void-6 missing."
            ),
            src="evals/terragrunt.hcl",
            src_obs='download_dir = ".terragrunt-cache"  # leftover',
            run="evals/terragrunt_eval.py",
            fail_obs="cache leftover yesterday. planted gift-void-6 absent",
            inspect="evals/terragrunt.hcl",
            inspect_obs="stable cache leftover",
            first_path="evals/terragrunt.hcl",
            first_old='download_dir = ".terragrunt-cache"',
            first_new='download_dir = ".terragrunt-cache-dev"',
            first_obs="dev local. runner leftover still .terragrunt-cache",
            rate_tail="runner leftover .terragrunt-cache",
            still_after_429="runner leftover cache; planted gift-void-6 absent",
            grep="terragrunt-cache|download_dir|goldens",
            grep_obs="cannot change runner leftover from this ticket",
            plan_change="local cache SHA dir; document runner leftover cache",
            fix_path="evals/terragrunt.hcl",
            fix_old='download_dir = ".terragrunt-cache-dev"',
            fix_new='download_dir = ".terragrunt-cache-{{sha}}"',
            fix_obs="local planted present. runner leftover HANDOFF",
            retry_obs="502 unused. runner leftover terragrunt cache. Partial",
            test="tests/test_terragrunt_cache_sha.py",
            test_body="xfail runner leftover cache; local SHA dir",
            test_obs="runner leftover terragrunt cache. Partial",
            suite_obs="local SHA cache. runner leftover cache. Partial.",
            gate_obs="local SHA cache. runner leftover cache. Partial.",
            diff_obs=" evals/terragrunt.hcl | 2+-\n HANDOFF terragrunt runner\n",
            residual="Runner leftover still .terragrunt-cache. Partial.",
        ),
    )
)

# r401 image leftover
PAIRS.append(
    (
        _ok(
            slug="ko-sbom-omit-goldens-d77k",
            domain="ko-eval",
            kind="image",
            avoided="r355 skaffold omit; r356 buildah; r319 ClearML uri",
            goal=(
                "ko leftover publish omits goldens from the image so planted "
                "bundle-void-6 never ships. Include goldens in the ko path."
            ),
            plan="Dump .ko.yaml, include goldens, prove planted bundle-void-6 fail.",
            outcome=(
                "Image includes goldens/. Planted bundle-void-6 0.13 fail-closed. Residual: "
                "a KO_DOCKER_REPO leftover still builds without goldens."
            ),
            ticket=(
                "Title: ko leftover publish omits goldens. planted bundle-void-6 missing."
            ),
            src=".ko.yaml",
            src_obs="defaultBaseImage: eval-base  # leftover no goldens dir",
            run="evals/ko_eval.py",
            fail_obs="image leftover no goldens. planted bundle-void-6 absent",
            inspect=".ko.yaml",
            inspect_obs="no goldens leftover",
            first_path=".ko.yaml",
            first_old="defaultBaseImage: eval-base",
            first_new="defaultBaseImage: eval-base\n# TODO goldens",
            first_obs="comment only. KO_DOCKER_REPO leftover still omit",
            rate_tail="KO_DOCKER_REPO leftover omit goldens",
            still_after_429="repo leftover omit; planted bundle-void-6 absent",
            grep="goldens|.ko.yaml|ko publish",
            grep_obs="include goldens dir; ignore repo leftover",
            plan_change="ko dir includes goldens/; refuse omit",
            fix_path=".ko.yaml",
            fix_old="# TODO goldens",
            fix_new="dir: ./goldens",
            fix_obs="planted bundle-void-6 0.13 in image",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-void-6 0.13",
            test="tests/test_ko_includes_goldens.py",
            test_body="assert ko dir includes goldens",
            test_obs="test_ko_not_omit_goldens",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-6",
            diff_obs=" .ko.yaml | 4+-\n tests/test_ko_includes_goldens.py | 12++\n",
            residual="KO_DOCKER_REPO leftover still builds without goldens.",
        ),
        _bad(
            slug="pack-builder-stale-e78l",
            domain="pack-eval",
            kind="image",
            avoided="r401 ko; r268 docker layer; r319 Aim hash",
            goal=(
                "pack leftover builder paketobuildpacks/builder:tiny is last month so planted "
                "loyalty-void-6 never copies. Pin the builder locally."
            ),
            plan="Dump project.toml, pin builder, prove planted loyalty-void-6 locally.",
            outcome=(
                "Local builder is this SHA. Planted loyalty-void-6 present locally. Handoff: "
                "the CNB leftover still builder:tiny last month."
            ),
            ticket=(
                "Title: pack leftover builder:tiny last month. planted loyalty-void-6 missing."
            ),
            src="project.toml",
            src_obs='builder = "paketobuildpacks/builder:tiny"  # leftover',
            run="evals/pack_eval.py",
            fail_obs="builder leftover last month. planted loyalty-void-6 absent",
            inspect="project.toml",
            inspect_obs="tiny leftover",
            first_path="project.toml",
            first_old='builder = "paketobuildpacks/builder:tiny"',
            first_new='builder = "paketobuildpacks/builder:base"',
            first_obs="base local. CNB leftover still tiny",
            rate_tail="CNB leftover builder:tiny",
            still_after_429="CNB leftover tiny; planted loyalty-void-6 absent",
            grep="builder:tiny|project.toml|goldens",
            grep_obs="cannot change CNB leftover from this ticket",
            plan_change="local builder SHA; document CNB leftover tiny",
            fix_path="project.toml",
            fix_old='builder = "paketobuildpacks/builder:base"',
            fix_new='builder = "eval-builder:{{sha}}"',
            fix_obs="local planted present. CNB leftover HANDOFF",
            retry_obs="502 unused. CNB leftover builder tiny. Partial",
            test="tests/test_pack_builder_sha.py",
            test_body="xfail CNB leftover tiny; local SHA builder",
            test_obs="CNB leftover builder tiny. Partial",
            suite_obs="local SHA builder. CNB leftover tiny. Partial.",
            gate_obs="local SHA builder. CNB leftover tiny. Partial.",
            diff_obs=" project.toml | 2+-\n HANDOFF pack cnb\n",
            residual="CNB leftover still builder:tiny last month. Partial.",
        ),
    )
)

# r402 buildkit leftover
PAIRS.append(
    (
        _ok(
            slug="buildkit-cache-mount-stale-f79m",
            domain="buildkit-eval",
            kind="image",
            avoided="r308 earthly cache; r356 buildah; r319 ClearML uri",
            goal=(
                "BuildKit leftover RUN --mount=type=cache id=eval still serves yesterday "
                "goldens so planted cancel-void-6 never copies. Key the cache id by SHA."
            ),
            plan="Dump Dockerfile, pin cache id, prove planted cancel-void-6 fail.",
            outcome=(
                "Cache id is eval-<sha>. Planted cancel-void-6 0.14 fail-closed. Residual: a "
                "builder leftover still id=eval."
            ),
            ticket=(
                "Title: BuildKit leftover cache id=eval. planted cancel-void-6 missing."
            ),
            src="Dockerfile",
            src_obs="RUN --mount=type=cache,id=eval,target=/eval  # leftover",
            run="evals/buildkit_eval.py",
            fail_obs="cache leftover yesterday. planted cancel-void-6 absent",
            inspect="Dockerfile",
            inspect_obs="id=eval leftover",
            first_path="Dockerfile",
            first_old="id=eval",
            first_new="id=eval-dev",
            first_obs="dev local. builder leftover still id=eval",
            rate_tail="builder leftover cache id=eval",
            still_after_429="builder leftover id; planted cancel-void-6 absent",
            grep="id=eval|type=cache|goldens",
            grep_obs="id=eval-<sha>; ignore builder leftover",
            plan_change="cache id eval-<sha>; refuse id=eval",
            fix_path="Dockerfile",
            fix_old="id=eval-dev",
            fix_new="id=eval-${GIT_SHA}",
            fix_obs="planted cancel-void-6 0.14 cache miss",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-void-6 0.14",
            test="tests/test_buildkit_cache_sha.py",
            test_body="assert cache id includes sha; id=eval unused",
            test_obs="test_buildkit_not_id_eval",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-6",
            diff_obs=" Dockerfile | 2+-\n tests/test_buildkit_cache_sha.py | 12++\n",
            residual="Builder leftover still cache id=eval.",
        ),
        _bad(
            slug="kaniko-snapshot-stale-g80n",
            domain="kaniko-eval",
            kind="image",
            avoided="r402 buildkit; r268 docker layer; r319 Aim hash",
            goal=(
                "Kaniko leftover snapshotMode=redo still reuses yesterday layers so planted "
                "tax-void-5 never copies. Disable snapshot reuse locally."
            ),
            plan="Dump kaniko flags, disable reuse, prove planted tax-void-5 locally.",
            outcome=(
                "Local snapshotMode=full. Planted tax-void-5 present locally. Handoff: the "
                "job leftover still --snapshotMode=redo."
            ),
            ticket=(
                "Title: Kaniko leftover snapshotMode=redo. planted tax-void-5 missing."
            ),
            src="evals/kaniko.sh",
            src_obs="--snapshotMode=redo  # leftover",
            run="evals/kaniko_eval.py",
            fail_obs="redo leftover yesterday layers. planted tax-void-5 absent",
            inspect="evals/kaniko.sh",
            inspect_obs="redo leftover",
            first_path="evals/kaniko.sh",
            first_old="--snapshotMode=redo",
            first_new="--snapshotMode=time",
            first_obs="time local. job leftover still redo",
            rate_tail="job leftover --snapshotMode=redo",
            still_after_429="job leftover redo; planted tax-void-5 absent",
            grep="snapshotMode|kaniko|goldens",
            grep_obs="cannot change job leftover from this ticket",
            plan_change="local snapshotMode=full; document job leftover redo",
            fix_path="evals/kaniko.sh",
            fix_old="--snapshotMode=time",
            fix_new="--snapshotMode=full",
            fix_obs="local planted present. job leftover HANDOFF",
            retry_obs="502 unused. job leftover snapshot redo. Partial",
            test="tests/test_kaniko_snapshot_full.py",
            test_body="xfail job leftover redo; local full",
            test_obs="job leftover snapshot redo. Partial",
            suite_obs="local full. job leftover redo. Partial.",
            gate_obs="local full. job leftover redo. Partial.",
            diff_obs=" evals/kaniko.sh | 2+-\n HANDOFF kaniko job\n",
            residual="Job leftover still --snapshotMode=redo. Partial.",
        ),
    )
)

# r403 registry leftover
PAIRS.append(
    (
        _ok(
            slug="skopeo-copy-latest-h81o",
            domain="skopeo-eval",
            kind="image",
            avoided="r356 podman latest; r344 packer; r319 ClearML uri",
            goal=(
                "skopeo leftover copy docker://eval:latest so planted sla-void-5 never "
                "lands. Copy eval:<sha>."
            ),
            plan="Dump copy dest, pin SHA, prove planted sla-void-5 fail.",
            outcome=(
                "Dest is eval:<sha>. Planted sla-void-5 0.15 fail-closed. Residual: a "
                "cron leftover still docker://eval:latest."
            ),
            ticket=(
                "Title: skopeo leftover dest eval:latest. planted sla-void-5 missing."
            ),
            src="evals/skopeo.sh",
            src_obs="skopeo copy oci:out docker://eval:latest  # leftover",
            run="evals/skopeo_eval.py",
            fail_obs="latest leftover. planted sla-void-5 absent",
            inspect="evals/skopeo.sh",
            inspect_obs="latest leftover",
            first_path="evals/skopeo.sh",
            first_old="docker://eval:latest",
            first_new="docker://eval:dev",
            first_obs="dev local. cron leftover still eval:latest",
            rate_tail="cron leftover docker://eval:latest",
            still_after_429="cron leftover latest; planted sla-void-5 absent",
            grep="eval:latest|skopeo copy|goldens",
            grep_obs="dest eval:<sha>; ignore cron leftover",
            plan_change="copy dest eval:<sha>; refuse latest",
            fix_path="evals/skopeo.sh",
            fix_old="docker://eval:dev",
            fix_new="docker://eval:$GIT_SHA",
            fix_obs="planted sla-void-5 0.15 in sha tag",
            retry_obs="502 then retry; 5 pass 1 fail planted sla-void-5 0.15",
            test="tests/test_skopeo_dest_sha.py",
            test_body="assert dest is eval:<sha>; latest unused",
            test_obs="test_skopeo_not_eval_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-5",
            diff_obs=" evals/skopeo.sh | 2+-\n tests/test_skopeo_dest_sha.py | 12++\n",
            residual="Cron leftover still docker://eval:latest.",
        ),
        _bad(
            slug="crane-mutate-latest-i82p",
            domain="crane-eval",
            kind="image",
            avoided="r403 skopeo; r356 podman; r319 Aim hash",
            goal=(
                "crane leftover mutate eval:latest so planted hold-void-8 never tags. "
                "Mutate eval:<sha> locally."
            ),
            plan="Dump crane dest, pin SHA, prove planted hold-void-8 locally.",
            outcome=(
                "Local mutate dest is eval:<sha>. Planted hold-void-8 present locally. "
                "Handoff: the job leftover still crane mutate eval:latest."
            ),
            ticket=(
                "Title: crane leftover mutate eval:latest. planted hold-void-8 missing."
            ),
            src="evals/crane.sh",
            src_obs="crane mutate eval:latest --annotation eval=1  # leftover",
            run="evals/crane_eval.py",
            fail_obs="latest leftover. planted hold-void-8 absent",
            inspect="evals/crane.sh",
            inspect_obs="latest leftover",
            first_path="evals/crane.sh",
            first_old="eval:latest",
            first_new="eval:dev",
            first_obs="dev local. job leftover still eval:latest",
            rate_tail="job leftover crane mutate eval:latest",
            still_after_429="job leftover latest; planted hold-void-8 absent",
            grep="eval:latest|crane mutate|goldens",
            grep_obs="cannot change job leftover from this ticket",
            plan_change="local eval:<sha>; document job leftover latest",
            fix_path="evals/crane.sh",
            fix_old="eval:dev",
            fix_new="eval:$GIT_SHA",
            fix_obs="local planted present. job leftover HANDOFF",
            retry_obs="502 unused. job leftover crane latest. Partial",
            test="tests/test_crane_dest_sha.py",
            test_body="xfail job leftover latest; local eval:<sha>",
            test_obs="job leftover crane latest. Partial",
            suite_obs="local eval-sha. job leftover latest. Partial.",
            gate_obs="local eval-sha. job leftover latest. Partial.",
            diff_obs=" evals/crane.sh | 2+-\n HANDOFF crane job\n",
            residual="Job leftover still crane mutate eval:latest. Partial.",
        ),
    )
)

# r404 sign leftover
PAIRS.append(
    (
        _ok(
            slug="cosign-ref-latest-j83q",
            domain="cosign-eval",
            kind="image",
            avoided="r403 skopeo; r356 podman; r319 ClearML uri",
            goal=(
                "cosign leftover sign eval:latest so planted after-void-5 attestations "
                "never attach. Sign eval:<sha>."
            ),
            plan="Dump cosign ref, pin SHA, prove planted after-void-5 fail.",
            outcome=(
                "Signed ref is eval:<sha>. Planted after-void-5 0.12 fail-closed. Residual: "
                "a policy leftover still verifies eval:latest."
            ),
            ticket=(
                "Title: cosign leftover sign eval:latest. planted after-void-5 missing."
            ),
            src="evals/cosign.sh",
            src_obs="cosign sign eval:latest  # leftover",
            run="evals/cosign_eval.py",
            fail_obs="latest leftover. planted after-void-5 unsigned",
            inspect="evals/cosign.sh",
            inspect_obs="latest leftover",
            first_path="evals/cosign.sh",
            first_old="eval:latest",
            first_new="eval:dev",
            first_obs="dev local. policy leftover still eval:latest",
            rate_tail="policy leftover verifies eval:latest",
            still_after_429="policy leftover latest; planted after-void-5 unsigned",
            grep="eval:latest|cosign sign|goldens",
            grep_obs="sign eval:<sha>; ignore policy leftover",
            plan_change="sign eval:<sha>; refuse latest",
            fix_path="evals/cosign.sh",
            fix_old="eval:dev",
            fix_new="eval:$GIT_SHA",
            fix_obs="planted after-void-5 0.12 signed on sha",
            retry_obs="502 then retry; 5 pass 1 fail planted after-void-5 0.12",
            test="tests/test_cosign_ref_sha.py",
            test_body="assert signed ref includes sha; latest unused",
            test_obs="test_cosign_not_eval_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed after-void-5",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed after-void-5",
            diff_obs=" evals/cosign.sh | 2+-\n tests/test_cosign_ref_sha.py | 12++\n",
            residual="Policy leftover still verifies eval:latest.",
        ),
        _bad(
            slug="notation-ref-latest-k84r",
            domain="notation-eval",
            kind="image",
            avoided="r404 cosign; r403 crane; r319 Aim hash",
            goal=(
                "notation leftover sign eval:latest so planted sku-void-3 never attaches. "
                "Sign eval:<sha> locally."
            ),
            plan="Dump notation ref, pin SHA, prove planted sku-void-3 locally.",
            outcome=(
                "Local sign ref is eval:<sha>. Planted sku-void-3 present locally. Handoff: "
                "the policy leftover still notation verify eval:latest."
            ),
            ticket=(
                "Title: notation leftover sign eval:latest. planted sku-void-3 missing."
            ),
            src="evals/notation.sh",
            src_obs="notation sign eval:latest  # leftover",
            run="evals/notation_eval.py",
            fail_obs="latest leftover. planted sku-void-3 unsigned",
            inspect="evals/notation.sh",
            inspect_obs="latest leftover",
            first_path="evals/notation.sh",
            first_old="eval:latest",
            first_new="eval:dev",
            first_obs="dev local. policy leftover still eval:latest",
            rate_tail="policy leftover notation verify eval:latest",
            still_after_429="policy leftover latest; planted sku-void-3 unsigned",
            grep="eval:latest|notation sign|goldens",
            grep_obs="cannot change policy leftover from this ticket",
            plan_change="local eval:<sha>; document policy leftover latest",
            fix_path="evals/notation.sh",
            fix_old="eval:dev",
            fix_new="eval:$GIT_SHA",
            fix_obs="local planted present. policy leftover HANDOFF",
            retry_obs="502 unused. policy leftover notation latest. Partial",
            test="tests/test_notation_ref_sha.py",
            test_body="xfail policy leftover latest; local eval:<sha>",
            test_obs="policy leftover notation latest. Partial",
            suite_obs="local eval-sha. policy leftover latest. Partial.",
            gate_obs="local eval-sha. policy leftover latest. Partial.",
            diff_obs=" evals/notation.sh | 2+-\n HANDOFF notation policy\n",
            residual="Policy leftover still notation verify eval:latest. Partial.",
        ),
    )
)

# r405 oras leftover
PAIRS.append(
    (
        _ok(
            slug="oras-push-latest-l85s",
            domain="oras-eval",
            kind="image",
            avoided="r403 skopeo; r404 cosign; r319 ClearML uri",
            goal=(
                "ORAS leftover push eval:latest so planted rain-void-6 never lands. Push "
                "eval:<sha>."
            ),
            plan="Dump oras dest, pin SHA, prove planted rain-void-6 fail.",
            outcome=(
                "Push dest is eval:<sha>. Planted rain-void-6 0.16 fail-closed. Residual: a "
                "workflow leftover still oras push eval:latest."
            ),
            ticket=(
                "Title: ORAS leftover push eval:latest. planted rain-void-6 missing."
            ),
            src="evals/oras.sh",
            src_obs="oras push eval:latest goldens/  # leftover",
            run="evals/oras_eval.py",
            fail_obs="latest leftover. planted rain-void-6 absent",
            inspect="evals/oras.sh",
            inspect_obs="latest leftover",
            first_path="evals/oras.sh",
            first_old="eval:latest",
            first_new="eval:dev",
            first_obs="dev local. workflow leftover still eval:latest",
            rate_tail="workflow leftover oras push eval:latest",
            still_after_429="workflow leftover latest; planted rain-void-6 absent",
            grep="eval:latest|oras push|goldens",
            grep_obs="push eval:<sha>; ignore workflow leftover",
            plan_change="push dest eval:<sha>; refuse latest",
            fix_path="evals/oras.sh",
            fix_old="eval:dev",
            fix_new="eval:$GIT_SHA",
            fix_obs="planted rain-void-6 0.16 in sha tag",
            retry_obs="502 then retry; 5 pass 1 fail planted rain-void-6 0.16",
            test="tests/test_oras_dest_sha.py",
            test_body="assert dest is eval:<sha>; latest unused",
            test_obs="test_oras_not_eval_latest",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed rain-void-6",
            diff_obs=" evals/oras.sh | 2+-\n tests/test_oras_dest_sha.py | 12++\n",
            residual="Workflow leftover still oras push eval:latest.",
        ),
        _bad(
            slug="zot-repo-latest-m86t",
            domain="zot-eval",
            kind="image",
            avoided="r405 oras; r334 minio alias; r319 Aim hash",
            goal=(
                "zot leftover repo eval:latest so planted flash-void-6 never stores. Pin "
                "the repo locally."
            ),
            plan="Dump zot config, pin SHA, prove planted flash-void-6 locally.",
            outcome=(
                "Local repo is eval:<sha>. Planted flash-void-6 present locally. Handoff: "
                "the registry leftover still serves eval:latest."
            ),
            ticket=(
                "Title: zot leftover repo eval:latest. planted flash-void-6 missing."
            ),
            src="evals/zot-config.json",
            src_obs='"repo": "eval:latest"  // leftover',
            run="evals/zot_eval.py",
            fail_obs="latest leftover. planted flash-void-6 absent",
            inspect="evals/zot-config.json",
            inspect_obs="latest leftover",
            first_path="evals/zot-config.json",
            first_old='"repo": "eval:latest"',
            first_new='"repo": "eval:dev"',
            first_obs="dev local. registry leftover still eval:latest",
            rate_tail="registry leftover eval:latest",
            still_after_429="registry leftover latest; planted flash-void-6 absent",
            grep="eval:latest|zot-config|goldens",
            grep_obs="cannot change registry leftover from this ticket",
            plan_change="local eval:<sha>; document registry leftover latest",
            fix_path="evals/zot-config.json",
            fix_old='"repo": "eval:dev"',
            fix_new='"repo": "eval:{{sha}}"',
            fix_obs="local planted present. registry leftover HANDOFF",
            retry_obs="502 unused. registry leftover zot latest. Partial",
            test="tests/test_zot_repo_sha.py",
            test_body="xfail registry leftover latest; local eval:<sha>",
            test_obs="registry leftover zot latest. Partial",
            suite_obs="local eval-sha. registry leftover latest. Partial.",
            gate_obs="local eval-sha. registry leftover latest. Partial.",
            diff_obs=" evals/zot-config.json | 2+-\n HANDOFF zot registry\n",
            residual="Registry leftover still serves eval:latest. Partial.",
        ),
    )
)

# r406 crossplane leftover
PAIRS.append(
    (
        _ok(
            slug="crossplane-xr-stale-n87u",
            domain="crossplane-eval",
            kind="iac",
            avoided="r400 tofu; r398 kustomize; r319 ClearML uri",
            goal=(
                "Crossplane leftover XR EvalGoldens still compositionRef name=legacy so "
                "planted promo-void-7 never composes. Pin composition to this SHA."
            ),
            plan="Dump XR, pin SHA composition, prove planted promo-void-7 fail.",
            outcome=(
                "compositionRef is eval-<sha>. Planted promo-void-7 0.13 fail-closed. Residual: "
                "a claim leftover still compositionRef=legacy."
            ),
            ticket=(
                "Title: Crossplane leftover compositionRef=legacy. planted promo-void-7 missing."
            ),
            src="evals/xr.yaml",
            src_obs="compositionRef:\n  name: legacy  # leftover",
            run="evals/crossplane_eval.py",
            fail_obs="legacy leftover. planted promo-void-7 absent",
            inspect="evals/xr.yaml",
            inspect_obs="legacy leftover",
            first_path="evals/xr.yaml",
            first_old="name: legacy",
            first_new="name: eval-dev",
            first_obs="dev local. claim leftover still legacy",
            rate_tail="claim leftover compositionRef=legacy",
            still_after_429="claim leftover; planted promo-void-7 absent",
            grep="compositionRef|legacy|goldens",
            grep_obs="composition eval-<sha>; ignore claim leftover",
            plan_change="compositionRef eval-<sha>; refuse legacy",
            fix_path="evals/xr.yaml",
            fix_old="name: eval-dev",
            fix_new="name: eval-{{sha}}",
            fix_obs="planted promo-void-7 0.13. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted promo-void-7 0.13",
            test="tests/test_crossplane_comp_sha.py",
            test_body="assert compositionRef includes sha; legacy unused",
            test_obs="test_crossplane_not_legacy_comp",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed promo-void-7",
            diff_obs=" evals/xr.yaml | 2+-\n tests/test_crossplane_comp_sha.py | 12++\n",
            residual="Claim leftover still compositionRef=legacy.",
        ),
        _bad(
            slug="cdk8s-synth-stale-o88v",
            domain="cdk8s-eval",
            kind="iac",
            avoided="r406 crossplane; r398 kustomize; r319 Aim hash",
            goal=(
                "cdk8s leftover synth still writes dist/ from yesterday so planted "
                "gift-void-7 never appears. Synth to dist/<sha> locally."
            ),
            plan="Dump cdk8s.yaml, pin outdir, prove planted gift-void-7 locally.",
            outcome=(
                "Local outdir is dist/<sha>. Planted gift-void-7 present locally. Handoff: "
                "the pipeline leftover still cdk8s synth -o dist."
            ),
            ticket=(
                "Title: cdk8s leftover synth -o dist. planted gift-void-7 missing."
            ),
            src="cdk8s.yaml",
            src_obs="output: dist  # leftover",
            run="evals/cdk8s_eval.py",
            fail_obs="dist leftover yesterday. planted gift-void-7 absent",
            inspect="cdk8s.yaml",
            inspect_obs="stable dist leftover",
            first_path="cdk8s.yaml",
            first_old="output: dist",
            first_new="output: dist-dev",
            first_obs="dev local. pipeline leftover still -o dist",
            rate_tail="pipeline leftover cdk8s synth -o dist",
            still_after_429="pipeline leftover dist; planted gift-void-7 absent",
            grep="output: dist|cdk8s synth|goldens",
            grep_obs="cannot change pipeline leftover from this ticket",
            plan_change="local dist/<sha>; document pipeline leftover dist",
            fix_path="cdk8s.yaml",
            fix_old="output: dist-dev",
            fix_new="output: dist/{{sha}}",
            fix_obs="local planted present. pipeline leftover HANDOFF",
            retry_obs="502 unused. pipeline leftover cdk8s dist. Partial",
            test="tests/test_cdk8s_outdir_sha.py",
            test_body="xfail pipeline leftover dist; local dist/<sha>",
            test_obs="pipeline leftover cdk8s dist. Partial",
            suite_obs="local dist/sha. pipeline leftover dist. Partial.",
            gate_obs="local dist/sha. pipeline leftover dist. Partial.",
            diff_obs=" cdk8s.yaml | 2+-\n HANDOFF cdk8s pipeline\n",
            residual="Pipeline leftover still cdk8s synth -o dist. Partial.",
        ),
    )
)

# r407 garden leftover
PAIRS.append(
    (
        _ok(
            slug="garden-module-stale-p89w",
            domain="garden-eval",
            kind="gitops",
            avoided="r355 tilt; r355 skaffold; r319 ClearML uri",
            goal=(
                "Garden leftover module eval still include=evals/** so planted "
                "bundle-void-7 never syncs. Include goldens/**."
            ),
            plan="Dump garden.yml, include goldens, prove planted bundle-void-7 fail.",
            outcome=(
                "Module includes goldens/. Planted bundle-void-7 0.14 fail-closed. Residual: "
                "a project leftover still include=evals/** only."
            ),
            ticket=(
                "Title: Garden leftover include=evals/**. planted bundle-void-7 missing."
            ),
            src="garden.yml",
            src_obs="include: [evals/**]  # leftover no goldens",
            run="evals/garden_eval.py",
            fail_obs="include leftover evals only. planted bundle-void-7 absent",
            inspect="garden.yml",
            inspect_obs="no goldens leftover",
            first_path="garden.yml",
            first_old="include: [evals/**]",
            first_new="include: [evals/**, goldens/**]",
            first_obs="goldens local. project leftover still evals only",
            rate_tail="project leftover include evals only",
            still_after_429="project leftover omit; planted bundle-void-7 absent",
            grep="include:|goldens|garden.yml",
            grep_obs="include goldens; ignore project leftover",
            plan_change="include goldens/**; refuse evals-only",
            fix_path="garden.yml",
            fix_old="include: [evals/**, goldens/**]",
            fix_new="include: [goldens/**, evals/**]",
            fix_obs="planted bundle-void-7 0.14 synced",
            retry_obs="502 then retry; 5 pass 1 fail planted bundle-void-7 0.14",
            test="tests/test_garden_include_goldens.py",
            test_body="assert include has goldens; evals-only unused",
            test_obs="test_garden_not_omit_goldens",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed bundle-void-7",
            diff_obs=" garden.yml | 2+-\n tests/test_garden_include_goldens.py | 12++\n",
            residual="Project leftover still include=evals/** only.",
        ),
        _bad(
            slug="okteto-sync-omit-q90x",
            domain="okteto-eval",
            kind="gitops",
            avoided="r407 garden; r355 tilt; r319 Aim hash",
            goal=(
                "Okteto leftover sync only evals/ so planted loyalty-void-7 never reaches "
                "the dev container. Add goldens sync locally."
            ),
            plan="Dump okteto.yml, add goldens, prove planted loyalty-void-7 locally.",
            outcome=(
                "Local sync includes goldens/. Planted loyalty-void-7 present locally. "
                "Handoff: the context leftover still evals only."
            ),
            ticket=(
                "Title: Okteto leftover sync evals/. planted loyalty-void-7 missing."
            ),
            src="okteto.yml",
            src_obs="sync:\n  - evals:/app/evals  # leftover no goldens",
            run="evals/okteto_eval.py",
            fail_obs="sync leftover evals only. planted loyalty-void-7 absent",
            inspect="okteto.yml",
            inspect_obs="no goldens leftover",
            first_path="okteto.yml",
            first_old="- evals:/app/evals",
            first_new="- evals:/app/evals\n  # TODO goldens",
            first_obs="comment only. context leftover still evals only",
            rate_tail="context leftover okteto sync evals only",
            still_after_429="context leftover omit; planted loyalty-void-7 absent",
            grep="sync:|goldens|okteto.yml",
            grep_obs="cannot change context leftover from this ticket",
            plan_change="local sync goldens; document context leftover evals only",
            fix_path="okteto.yml",
            fix_old="  # TODO goldens",
            fix_new="  - goldens:/app/goldens",
            fix_obs="local planted present. context leftover HANDOFF",
            retry_obs="502 unused. context leftover okteto evals. Partial",
            test="tests/test_okteto_sync_goldens.py",
            test_body="xfail context leftover evals only; local goldens sync",
            test_obs="context leftover okteto evals. Partial",
            suite_obs="local goldens sync. context leftover evals. Partial.",
            gate_obs="local goldens sync. context leftover evals. Partial.",
            diff_obs=" okteto.yml | 2+-\n HANDOFF okteto context\n",
            residual="Context leftover still evals only. Partial.",
        ),
    )
)

# r408 telepresence leftover
PAIRS.append(
    (
        _ok(
            slug="telepresence-mount-stale-r91y",
            domain="telepresence-eval",
            kind="gitops",
            avoided="r407 okteto; r355 tilt; r319 ClearML uri",
            goal=(
                "Telepresence leftover intercept mount /eval still binds yesterday goldens "
                "so planted cancel-void-7 never appears. Mount this SHA tree."
            ),
            plan="Dump intercept, pin SHA mount, prove planted cancel-void-7 fail.",
            outcome=(
                "Mount is /eval/<sha>. Planted cancel-void-7 0.15 fail-closed. Residual: a "
                "user leftover still telepresence intercept --mount /eval."
            ),
            ticket=(
                "Title: Telepresence leftover --mount /eval. planted cancel-void-7 missing."
            ),
            src="evals/telepresence.sh",
            src_obs="telepresence intercept eval --mount /eval  # leftover",
            run="evals/telepresence_eval.py",
            fail_obs="mount leftover yesterday. planted cancel-void-7 absent",
            inspect="evals/telepresence.sh",
            inspect_obs="stable mount leftover",
            first_path="evals/telepresence.sh",
            first_old="--mount /eval",
            first_new="--mount /eval-dev",
            first_obs="dev local. user leftover still /eval",
            rate_tail="user leftover --mount /eval",
            still_after_429="user leftover mount; planted cancel-void-7 absent",
            grep="--mount /eval|telepresence|goldens",
            grep_obs="mount /eval/<sha>; ignore user leftover",
            plan_change="mount /eval/<sha>; refuse /eval",
            fix_path="evals/telepresence.sh",
            fix_old="--mount /eval-dev",
            fix_new="--mount /eval/$GIT_SHA",
            fix_obs="planted cancel-void-7 0.15 in sha mount",
            retry_obs="502 then retry; 5 pass 1 fail planted cancel-void-7 0.15",
            test="tests/test_telepresence_mount_sha.py",
            test_body="assert mount includes sha; /eval unused",
            test_obs="test_telepresence_not_eval_mount",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-7",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed cancel-void-7",
            diff_obs=" evals/telepresence.sh | 2+-\n tests/test_telepresence_mount_sha.py | 12++\n",
            residual="User leftover still telepresence intercept --mount /eval.",
        ),
        _bad(
            slug="dagger-cache-stale-s92z",
            domain="dagger-eval",
            kind="gitops",
            avoided="r402 buildkit; r308 earthly; r319 Aim hash",
            goal=(
                "Dagger leftover cache volume eval still has yesterday goldens so planted "
                "tax-void-6 never runs. Pin the volume locally."
            ),
            plan="Dump dagger cache, pin SHA, prove planted tax-void-6 locally.",
            outcome=(
                "Local cache volume is eval-<sha>. Planted tax-void-6 present locally. "
                "Handoff: the engine leftover still cache volume eval."
            ),
            ticket=(
                "Title: Dagger leftover cache volume eval. planted tax-void-6 missing."
            ),
            src="evals/dagger.py",
            src_obs='cache = dag.cache_volume("eval")  # leftover',
            run="evals/dagger_eval.py",
            fail_obs="volume leftover yesterday. planted tax-void-6 absent",
            inspect="evals/dagger.py",
            inspect_obs="volume eval leftover",
            first_path="evals/dagger.py",
            first_old='cache_volume("eval")',
            first_new='cache_volume("eval-dev")',
            first_obs="dev local. engine leftover still eval",
            rate_tail="engine leftover cache volume eval",
            still_after_429="engine leftover volume; planted tax-void-6 absent",
            grep="cache_volume|eval|goldens",
            grep_obs="cannot change engine leftover from this ticket",
            plan_change="local volume eval-<sha>; document engine leftover eval",
            fix_path="evals/dagger.py",
            fix_old='cache_volume("eval-dev")',
            fix_new='cache_volume(f"eval-{git_sha}")',
            fix_obs="local planted present. engine leftover HANDOFF",
            retry_obs="502 unused. engine leftover dagger volume. Partial",
            test="tests/test_dagger_cache_sha.py",
            test_body="xfail engine leftover eval; local eval-<sha>",
            test_obs="engine leftover dagger volume. Partial",
            suite_obs="local eval-sha. engine leftover eval. Partial.",
            gate_obs="local eval-sha. engine leftover eval. Partial.",
            diff_obs=" evals/dagger.py | 2+-\n HANDOFF dagger engine\n",
            residual="Engine leftover still cache volume eval. Partial.",
        ),
    )
)

# r409 bake leftover
PAIRS.append(
    (
        _ok(
            slug="bake-target-legacy-t93a",
            domain="bake-eval",
            kind="image",
            avoided="r402 buildkit; r320 justfile; r319 ClearML uri",
            goal=(
                "bake leftover target eval still contexts.eval=evals/legacy so planted "
                "sla-void-6 never builds. Point the context at evals/."
            ),
            plan="Dump docker-bake.hcl, retarget, prove planted sla-void-6 fail.",
            outcome=(
                "Context is evals/. Planted sla-void-6 0.13 fail-closed. Residual: a "
                "group leftover still target eval-legacy."
            ),
            ticket=(
                "Title: bake leftover contexts.eval=evals/legacy. planted sla-void-6 missing."
            ),
            src="docker-bake.hcl",
            src_obs='target "eval" { contexts = { eval = "evals/legacy" } }  # leftover',
            run="evals/bake_eval.py",
            fail_obs="legacy leftover. planted sla-void-6 unused",
            inspect="docker-bake.hcl",
            inspect_obs="legacy leftover",
            first_path="docker-bake.hcl",
            first_old='eval = "evals/legacy"',
            first_new='eval = "evals"',
            first_obs="evals local. group leftover still eval-legacy",
            rate_tail="group leftover target eval-legacy",
            still_after_429="group leftover; planted sla-void-6 unused",
            grep="evals/legacy|target .eval|goldens",
            grep_obs="context evals/; ignore group leftover",
            plan_change="context evals/; refuse eval-legacy group",
            fix_path="docker-bake.hcl",
            fix_old='eval = "evals"',
            fix_new='eval = "evals"  # include goldens via contexts',
            fix_obs="planted sla-void-6 0.13. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted sla-void-6 0.13",
            test="tests/test_bake_not_legacy.py",
            test_body="assert context is evals/; legacy unused",
            test_obs="test_bake_not_eval_legacy",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-6",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sla-void-6",
            diff_obs=" docker-bake.hcl | 4+-\n tests/test_bake_not_legacy.py | 12++\n",
            residual="Group leftover still target eval-legacy.",
        ),
        _bad(
            slug="earthly-arg-stale-u94b",
            domain="earthly-arg-eval",
            kind="image",
            avoided="r308 earthly cache; r409 bake; r319 Aim hash",
            goal=(
                "Earthly leftover ARG EVAL_SHA=yesterday so planted hold-void-9 never "
                "copies. Bind ARG to this SHA locally."
            ),
            plan="Dump Earthfile, pin ARG, prove planted hold-void-9 locally.",
            outcome=(
                "Local ARG is this SHA. Planted hold-void-9 present locally. Handoff: the "
                "satellite leftover still --EVAL_SHA=yesterday."
            ),
            ticket=(
                "Title: Earthly leftover ARG EVAL_SHA=yesterday. planted hold-void-9 missing."
            ),
            src="Earthfile",
            src_obs="ARG EVAL_SHA=yesterday  # leftover",
            run="evals/earthly_eval.py",
            fail_obs="ARG leftover yesterday. planted hold-void-9 absent",
            inspect="Earthfile",
            inspect_obs="yesterday leftover",
            first_path="Earthfile",
            first_old="ARG EVAL_SHA=yesterday",
            first_new="ARG EVAL_SHA=dev",
            first_obs="dev local. satellite leftover still yesterday",
            rate_tail="satellite leftover --EVAL_SHA=yesterday",
            still_after_429="satellite leftover; planted hold-void-9 absent",
            grep="EVAL_SHA=yesterday|Earthfile|goldens",
            grep_obs="cannot change satellite leftover from this ticket",
            plan_change="local ARG SHA; document satellite leftover yesterday",
            fix_path="Earthfile",
            fix_old="ARG EVAL_SHA=dev",
            fix_new="ARG EVAL_SHA=$GIT_SHA",
            fix_obs="local planted present. satellite leftover HANDOFF",
            retry_obs="502 unused. satellite leftover EVAL_SHA. Partial",
            test="tests/test_earthly_arg_sha.py",
            test_body="xfail satellite leftover yesterday; local SHA ARG",
            test_obs="satellite leftover EVAL_SHA. Partial",
            suite_obs="local SHA ARG. satellite leftover yesterday. Partial.",
            gate_obs="local SHA ARG. satellite leftover yesterday. Partial.",
            diff_obs=" Earthfile | 2+-\n HANDOFF earthly satellite\n",
            residual="Satellite leftover still --EVAL_SHA=yesterday. Partial.",
        ),
    )
)

# r410 atmos leftover
PAIRS.append(
    (
        _ok(
            slug="atmos-stack-stale-v95c",
            domain="atmos-eval",
            kind="iac",
            avoided="r400 tofu; r400 terragrunt; r319 ClearML uri",
            goal=(
                "Atmos leftover stack eval still imports yesterday goldens so planted "
                "membership-void-4 never applies. Pin the stack to this SHA."
            ),
            plan="Dump stack yaml, pin SHA, prove planted membership-void-4 fail.",
            outcome=(
                "Stack is eval-<sha>. Planted membership-void-4 0.16 fail-closed. Residual: "
                "a workflow leftover still atmos terraform apply eval."
            ),
            ticket=(
                "Title: Atmos leftover stack eval. planted membership-void-4 missing."
            ),
            src="stacks/eval.yaml",
            src_obs="import:\n  - catalog/eval/legacy  # leftover",
            run="evals/atmos_eval.py",
            fail_obs="legacy leftover. planted membership-void-4 absent",
            inspect="stacks/eval.yaml",
            inspect_obs="legacy leftover",
            first_path="stacks/eval.yaml",
            first_old="- catalog/eval/legacy",
            first_new="- catalog/eval/dev",
            first_obs="dev local. workflow leftover still apply eval",
            rate_tail="workflow leftover atmos apply eval",
            still_after_429="workflow leftover; planted membership-void-4 absent",
            grep="catalog/eval/legacy|stacks/eval|goldens",
            grep_obs="stack eval-<sha>; ignore workflow leftover",
            plan_change="stack eval-<sha>; refuse catalog/eval/legacy",
            fix_path="stacks/eval.yaml",
            fix_old="- catalog/eval/dev",
            fix_new="- catalog/eval/{{sha}}",
            fix_obs="planted membership-void-4 0.16. legacy unused",
            retry_obs="502 then retry; 5 pass 1 fail planted membership-void-4 0.16",
            test="tests/test_atmos_stack_sha.py",
            test_body="assert stack import includes sha; legacy unused",
            test_obs="test_atmos_not_legacy_stack",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed membership-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed membership-void-4",
            diff_obs=" stacks/eval.yaml | 2+-\n tests/test_atmos_stack_sha.py | 12++\n",
            residual="Workflow leftover still atmos terraform apply eval.",
        ),
        _bad(
            slug="spacelift-stack-stale-w96d",
            domain="spacelift-eval",
            kind="iac",
            avoided="r410 atmos; r400 tofu; r319 Aim hash",
            goal=(
                "Spacelift leftover stack eval still tracks leftover/main so planted "
                "after-void-6 never plans. Pin the branch locally."
            ),
            plan="Dump stack, pin SHA branch, prove planted after-void-6 locally.",
            outcome=(
                "Local branch is sha. Planted after-void-6 present locally. Handoff: the "
                "space leftover still branch leftover/main."
            ),
            ticket=(
                "Title: Spacelift leftover branch leftover/main. planted after-void-6 missing."
            ),
            src="evals/spacelift.tf",
            src_obs='branch = "leftover/main"  # leftover',
            run="evals/spacelift_eval.py",
            fail_obs="branch leftover leftover/main. planted after-void-6 absent",
            inspect="evals/spacelift.tf",
            inspect_obs="leftover/main leftover",
            first_path="evals/spacelift.tf",
            first_old='branch = "leftover/main"',
            first_new='branch = "dev"',
            first_obs="dev local. space leftover still leftover/main",
            rate_tail="space leftover branch leftover/main",
            still_after_429="space leftover branch; planted after-void-6 absent",
            grep="leftover/main|branch =|goldens",
            grep_obs="cannot change space leftover from this ticket",
            plan_change="local branch SHA; document space leftover leftover/main",
            fix_path="evals/spacelift.tf",
            fix_old='branch = "dev"',
            fix_new='branch = git_sha',
            fix_obs="local planted present. space leftover HANDOFF",
            retry_obs="502 unused. space leftover leftover/main. Partial",
            test="tests/test_spacelift_branch_sha.py",
            test_body="xfail space leftover leftover/main; local SHA branch",
            test_obs="space leftover leftover/main. Partial",
            suite_obs="local SHA branch. space leftover leftover/main. Partial.",
            gate_obs="local SHA branch. space leftover leftover/main. Partial.",
            diff_obs=" evals/spacelift.tf | 2+-\n HANDOFF spacelift space\n",
            residual="Space leftover still branch leftover/main. Partial.",
        ),
    )
)

# r411 env0 leftover
PAIRS.append(
    (
        _ok(
            slug="env0-template-stale-x97e",
            domain="env0-eval",
            kind="iac",
            avoided="r410 atmos; r400 tofu; r319 ClearML uri",
            goal=(
                "env0 leftover template eval still revision leftover/main so planted "
                "sku-void-4 never applies. Pin the revision to this SHA."
            ),
            plan="Dump env0.yml, pin SHA, prove planted sku-void-4 fail.",
            outcome=(
                "Revision is this SHA. Planted sku-void-4 0.12 fail-closed. Residual: a "
                "project leftover still revision leftover/main."
            ),
            ticket=(
                "Title: env0 leftover revision leftover/main. planted sku-void-4 missing."
            ),
            src="env0.yml",
            src_obs="revision: leftover/main  # leftover",
            run="evals/env0_eval.py",
            fail_obs="revision leftover leftover/main. planted sku-void-4 absent",
            inspect="env0.yml",
            inspect_obs="leftover/main leftover",
            first_path="env0.yml",
            first_old="revision: leftover/main",
            first_new="revision: dev",
            first_obs="dev local. project leftover still leftover/main",
            rate_tail="project leftover revision leftover/main",
            still_after_429="project leftover; planted sku-void-4 absent",
            grep="leftover/main|revision:|goldens",
            grep_obs="revision SHA; ignore project leftover",
            plan_change="revision this SHA; refuse leftover/main",
            fix_path="env0.yml",
            fix_old="revision: dev",
            fix_new="revision: {{sha}}",
            fix_obs="planted sku-void-4 0.12. leftover/main unused",
            retry_obs="502 then retry; 5 pass 1 fail planted sku-void-4 0.12",
            test="tests/test_env0_revision_sha.py",
            test_body="assert revision is sha; leftover/main unused",
            test_obs="test_env0_not_leftover_main",
            suite_obs="6 traces: 5 pass, 1 fail-as-designed sku-void-4",
            gate_obs="6 traces: 5 pass, 1 fail-as-designed sku-void-4",
            diff_obs=" env0.yml | 2+-\n tests/test_env0_revision_sha.py | 12++\n",
            residual="Project leftover still revision leftover/main.",
        ),
        _bad(
            slug="scalr-workspace-stale-y98f",
            domain="scalr-eval",
            kind="iac",
            avoided="r411 env0; r410 spacelift; r319 Aim hash",
            goal=(
                "Scalr leftover workspace eval still vcs-ref leftover/main so planted "
                "rain-void-7 never plans. Pin the ref locally."
            ),
            plan="Dump workspace, pin SHA, prove planted rain-void-7 locally.",
            outcome=(
                "Local vcs-ref is this SHA. Planted rain-void-7 present locally. Handoff: "
                "the account leftover still leftover/main."
            ),
            ticket=(
                "Title: Scalr leftover vcs-ref leftover/main. planted rain-void-7 missing."
            ),
            src="evals/scalr.hcl",
            src_obs='vcs_ref = "leftover/main"  # leftover',
            run="evals/scalr_eval.py",
            fail_obs="ref leftover leftover/main. planted rain-void-7 absent",
            inspect="evals/scalr.hcl",
            inspect_obs="leftover/main leftover",
            first_path="evals/scalr.hcl",
            first_old='vcs_ref = "leftover/main"',
            first_new='vcs_ref = "dev"',
            first_obs="dev local. account leftover still leftover/main",
            rate_tail="account leftover vcs-ref leftover/main",
            still_after_429="account leftover; planted rain-void-7 absent",
            grep="leftover/main|vcs_ref|goldens",
            grep_obs="cannot change account leftover from this ticket",
            plan_change="local SHA ref; document account leftover leftover/main",
            fix_path="evals/scalr.hcl",
            fix_old='vcs_ref = "dev"',
            fix_new='vcs_ref = git_sha',
            fix_obs="local planted present. account leftover HANDOFF",
            retry_obs="502 unused. account leftover leftover/main. Partial",
            test="tests/test_scalr_ref_sha.py",
            test_body="xfail account leftover leftover/main; local SHA ref",
            test_obs="account leftover leftover/main. Partial",
            suite_obs="local SHA ref. account leftover leftover/main. Partial.",
            gate_obs="local SHA ref. account leftover leftover/main. Partial.",
            diff_obs=" evals/scalr.hcl | 2+-\n HANDOFF scalr account\n",
            residual="Account leftover still leftover/main. Partial.",
        ),
    )
)
