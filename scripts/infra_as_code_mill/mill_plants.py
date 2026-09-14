"""Unique already-skip / leftover IaC plants r609–r616. Not r587–r608 clones."""

from __future__ import annotations

PAIRS: list[tuple[dict, dict, str]] = []


def _ok(**kwargs) -> dict:
    return kwargs


def _fail(**kwargs) -> dict:
    return kwargs


# ---------------------------------------------------------------------------
# r609 Ansible already skip if unused vs leftover retry
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="ansible-skip-if-unused",
            seed="ansible skip if unused when: default false",
            fail="playbook skipped nginx handler; 1.24 leftover",
            left="nunatak.retry still on disk",
            term="success extra-vars 2/2",
            arc="skip 4–5; force-handlers no-op 7; extra-vars 10–11.",
            ticket="nunatak nginx handler skipped",
            test="tests/test_nunatak_nginx.py",
            cfg="playbooks/site.yml",
            ci="playbooks/CI.md",
            goal=(
                "Land designed plant nunatak-prod nginx 1.26 via ansible-playbook "
                "without treating the skipped handler as already unused. Do not "
                "--force-handlers a when:false task."
            ),
            plan=(
                "Prove when: nginx_needed|default(false) skipped the handler; pass "
                "extra-vars; empty play recap + fixtures."
            ),
            outcome=(
                "site.yml skipped handlers/nginx.yml because extra-vars omitted "
                "nginx_needed. --force-handlers still skipped. Plan change: "
                "ansible-playbook -e nginx_needed=true. 1.26 landed; pytest 2/2. "
                "Residual nunatak.retry on disk."
            ),
            s1_act="List playbooks and retry files.",
            s1_cmd="ls playbooks handlers tests; ls *.retry 2>/dev/null; ansible --version | head -n 1",
            s1_obs="playbooks/site.yml  handlers/nginx.yml\nnunatak.retry\nansible [core 2.17.4]\n",
            s2_lead="retry leftover exists",
            test_body=(
                "def test_nginx_ver(host):\n"
                "    assert host.nginx.version == '1.26'\n"
                "def test_no_skip_recap(recap):\n"
                "    assert recap.skipped['handlers/nginx.yml'] == 0\n"
            ),
            s3_lead="fixture wants 1.26 and zero skips",
            cfg_body=(
                "- hosts: web\n"
                "  handlers:\n"
                "    - name: restart nginx\n"
                "      service: name=nginx state=restarted\n"
                "      when: nginx_needed | default(false)\n"
                "# CI comment: already skip if unused\n"
            ),
            s4_lead="when: default false",
            s4_act="ansible-playbook --check site.yml (CI dry-run).",
            s4_cmd="ansible-playbook playbooks/site.yml --check --diff 2>&1 | tail -n 12",
            s4_obs="TASK [restart nginx] skipping: no hosts matched when: nginx_needed\nok=4  skipped=1\n",
            s5_lead="check skipped the handler",
            s5_act="ansible-playbook apply as CI (no extra-vars).",
            s5_cmd="ansible-playbook playbooks/site.yml 2>&1 | tail -n 10",
            s5_obs="PLAY RECAP nunatak-web ok=4 skipped=1\n# nginx stays 1.24; handler unused\n",
            s6_lead="apply skipped handler",
            s6_obs="FF\nFAILED test_nginx_ver - 1.24 != 1.26\nFAILED test_no_skip_recap - skipped=1\n",
            s7_lead="0/2",
            wrong="--force-handlers",
            wrong_cmd="ansible-playbook playbooks/site.yml --force-handlers 2>&1 | tail -n 8",
            wrong_obs="TASK [restart nginx] skipping: when: nginx_needed is false\n# force-handlers does not override when:\n",
            s8_lead="force-handlers still skipped",
            s8_act="nginx -v leftover 1.24.",
            s8_cmd="ssh nunatak-web 'nginx -v' 2>&1 | tail -n 2",
            s8_obs="nginx version: nginx/1.24.0\n",
            plan_change="pass -e nginx_needed=true; do not force-handlers.",
            ci_old="ansible-playbook playbooks/site.yml\n",
            ci_new=(
                "ansible-playbook playbooks/site.yml -e nginx_needed=true\n"
                "# already skip if unused is wrong when the handler is required.\n"
            ),
            s10_act="re-run with extra-vars.",
            fix_cmd="ansible-playbook playbooks/site.yml -e nginx_needed=true 2>&1 | tail -n 8",
            fix_obs="TASK [restart nginx] changed\nok=5  skipped=0\n",
            s11_lead="handler ran",
            pass_obs="..\n2 passed\n",
            s12_act="confirm nginx 1.26.",
            s12_cmd="ssh nunatak-web 'nginx -v' 2>&1",
            s12_obs="nginx version: nginx/1.26.1\n",
            s13_lead="version landed",
            left_cmd="ls -1 nunatak.retry playbooks/*.retry 2>/dev/null || true",
            left_obs="nunatak.retry\n# leftover retry from the skipped run\n",
            residual="nunatak.retry",
            s14_act="do not re-run from retry.",
            s14_cmd="head -n 2 nunatak.retry",
            s14_obs="nunatak-web\n# stale skip host list\n",
            s15_lead="retry leftover documented",
            rg_cmd="rg -n 'nginx_needed|force-handlers' playbooks/CI.md playbooks/site.yml",
            rg_obs="CI.md: ansible-playbook ... -e nginx_needed=true\nsite.yml: when: nginx_needed | default(false)\n",
            s16_lead="CI pins extra-vars",
            s16_cmd="ansible-playbook playbooks/site.yml -e nginx_needed=true --check 2>&1 | tail -n 4",
            s16_obs="ok=5  skipped=0  changed=0\n",
            s17_lead="check clean",
        ),
        _fail(
            slug="ansible-retry-leftover",
            seed="ansible leftover --limit + retry",
            fail="--limit web skipped jobs host",
            left="nunatak-jobs.retry + skipped jobs",
            term="partial remove retry handoff",
            arc="limit skip 4; skip-tags blast 6; handoff 7–17.",
            ticket="nunatak-jobs leftover retry skip",
            test="tests/test_nunatak_jobs.py",
            cfg="inventory/hosts.ini",
            ci="playbooks/jobs-CI.md",
            goal=(
                "nunatak-jobs leftover ansible --limit web in designed plant "
                "nunatak-prod still skips the jobs host. Stop --skip-tags always. "
                "Handoff remove retry + inventory leftover."
            ),
            plan="Show --limit leftover; first wrong skip-tags; hand off retry.",
            outcome=(
                "--limit web skipped nunatak-jobs. --skip-tags always skipped the "
                "role entirely. PARTIAL: jobs host still 0/2 on apply fixture. "
                "Handoff rm nunatak-jobs.retry and drop leftover --limit."
            ),
            s1_act="List inventory and retry.",
            s1_cmd="ls inventory playbooks; cat inventory/hosts.ini; ls *.retry 2>/dev/null",
            s1_obs="[web] nunatak-web\n[jobs] nunatak-jobs\nnunatak-jobs.retry\n",
            s2_lead="jobs retry leftover",
            test_body=(
                "def test_jobs_applied(recap):\n"
                "    assert recap.ok['nunatak-jobs'] >= 1\n"
                "def test_no_limit_web_only(inv):\n"
                "    assert inv.limit != 'web'\n"
            ),
            s3_lead="fixture wants jobs applied",
            cfg_body=(
                "[web]\nnunatak-web\n[jobs]\nnunatak-jobs\n"
                "# leftover CI: ansible-playbook --limit web\n"
            ),
            s4_lead="limit leftover in CI",
            s4_act="ansible-playbook --limit web (CI).",
            s4_cmd="ansible-playbook playbooks/jobs.yml --limit web 2>&1 | tail -n 8",
            s4_obs="PLAY RECAP nunatak-web ok=3 skipped=0\n# nunatak-jobs not in play\n",
            s5_lead="jobs host skipped",
            s5_obs=".F\nFAILED test_jobs_applied - nunatak-jobs missing from recap\n",
            s6_lead="1/2",
            wrong="--skip-tags always",
            wrong_cmd="ansible-playbook playbooks/jobs.yml --skip-tags always 2>&1 | tail -n 6",
            wrong_obs="PLAY RECAP nunatak-web ok=0 skipped=3\nnunatak-jobs ok=0 skipped=3\n# skip-tags always skipped the needed role\n",
            handoff="rm nunatak-jobs.retry and drop --limit web",
            dont="--skip-tags always",
            ci_old="ansible-playbook playbooks/jobs.yml --limit web\n",
            ci_new=(
                "# leftover --limit web skipped jobs. Handoff: rm nunatak-jobs.retry; "
                "re-run without --limit. never --skip-tags always.\n"
            ),
            left_name="nunatak-jobs.retry",
            left_cmd="ls -1 nunatak-jobs.retry; echo leftover --limit web",
            left_obs="nunatak-jobs.retry\nleftover --limit web\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="rm nunatak-jobs.retry",
            s11_act="show leftover retry host list.",
            s11_cmd="cat nunatak-jobs.retry",
            s11_obs="nunatak-jobs\n# stale from a prior failed play\n",
            s12_lead="retry still on disk",
            s13_act="do not apply from retry.",
            s13_cmd="echo leftover retry; ansible-playbook playbooks/jobs.yml --limit @nunatak-jobs.retry --check 2>&1 | tail -n 3",
            s13_obs="leftover retry\n# would only target stale host list\n",
            s14_cmd="rg -n 'limit web|skip-tags' playbooks/jobs-CI.md",
            s14_obs="jobs-CI.md: leftover --limit web skipped jobs\n",
            s15_lead="CI handoff written",
            s15_cmd="ansible-inventory -i inventory/hosts.ini --list | rg nunatak-jobs",
            s15_obs="nunatak-jobs\n",
            s16_lead="inventory still has jobs",
            s16_cmd="echo leftover limit+retry",
            s16_obs="leftover limit+retry\n",
        ),
        "Ansible already skip if unused (SUCCESS) and leftover retry/--limit (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r610 Helm already skip --reuse-values vs leftover release secret
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="helm-reuse-values-skip",
            seed="helm upgrade --reuse-values skipped new tag",
            fail="reuse-values no-op; image 1.8 leftover",
            left="sh.helm.release.v1.kame.v11 secret",
            term="success reset-then-reuse 2/2",
            arc="reuse skip 4–5; --force old tag 7; reset-then-reuse 10–11.",
            ticket="kame image tag skipped",
            test="tests/test_kame_chart.py",
            cfg="charts/kame/values-prod.yaml",
            ci="charts/kame/CI.md",
            goal=(
                "Land designed plant kame-prod chart image 1.9 without treating "
                "helm upgrade --reuse-values as already skip. Do not --force a "
                "stale tag. Residual old release secret is ok."
            ),
            plan=(
                "Prove --reuse-values hid values-prod.yaml tag; --reset-then-reuse-values "
                "-f values-prod.yaml; fixtures."
            ),
            outcome=(
                "helm upgrade --reuse-values skipped image.tag 1.9 from values-prod.yaml. "
                "--force rolled pods still on 1.8. Plan change: --reset-then-reuse-values "
                "-f values-prod.yaml. 1.9 landed; pytest 2/2. Residual v11 release secret."
            ),
            s1_act="List chart and helm history.",
            s1_cmd="ls charts/kame tests; helm -n kame history kame | tail -n 5; helm -n kame get values kame | tail -n 8",
            s1_obs="REVISION 11 deployed\nimage.tag: 1.8\n# values-prod.yaml on disk says 1.9\n",
            s2_lead="live tag 1.8 vs file 1.9",
            test_body=(
                "def test_image(deploy):\n"
                "    assert deploy.image.endswith(':1.9')\n"
                "def test_release(helm):\n"
                "    assert helm.values('kame')['image']['tag'] == '1.9'\n"
            ),
            s3_lead="fixture wants 1.9",
            cfg_body="image:\n  repository: ghcr.io/kame/api\n  tag: \"1.9\"\n# CI: helm upgrade --install --reuse-values\n",
            s4_lead="file has 1.9",
            s4_act="helm diff / upgrade --reuse-values (CI).",
            s4_cmd="helm -n kame upgrade kame charts/kame --reuse-values --dry-run 2>&1 | tail -n 10",
            s4_obs="Manifest: image: ghcr.io/kame/api:1.8\n# reuse-values ignored values-prod.yaml\n",
            s5_lead="dry-run still 1.8",
            s5_act="helm upgrade --reuse-values apply.",
            s5_cmd="helm -n kame upgrade kame charts/kame --reuse-values 2>&1 | tail -n 8",
            s5_obs="Release \"kame\" has been upgraded. Happy Helming!\n# no-op: still 1.8\n",
            s6_lead="upgrade already skip",
            s6_obs="FF\nFAILED test_image - :1.8\nFAILED test_release - 1.8\n",
            s7_lead="0/2",
            wrong="helm upgrade --force",
            wrong_cmd="helm -n kame upgrade kame charts/kame --reuse-values --force 2>&1 | tail -n 8",
            wrong_obs="Release upgraded; pods rolling\nkubectl -n kame get deploy kame -o jsonpath='{.spec.template.spec.containers[0].image}'\nghcr.io/kame/api:1.8\n",
            s8_lead="force rolled still 1.8",
            s8_act="helm get values confirm leftover tag.",
            s8_cmd="helm -n kame get values kame",
            s8_obs="image:\n  tag: 1.8\n",
            plan_change="--reset-then-reuse-values -f values-prod.yaml; never --force a stale tag.",
            ci_old="helm upgrade --install kame charts/kame --reuse-values\n",
            ci_new=(
                "helm upgrade --install kame charts/kame --reset-then-reuse-values -f charts/kame/values-prod.yaml\n"
                "# --reuse-values already-skips new file tags.\n"
            ),
            s10_act="upgrade with reset-then-reuse.",
            fix_cmd="helm -n kame upgrade kame charts/kame --reset-then-reuse-values -f charts/kame/values-prod.yaml 2>&1 | tail -n 8",
            fix_obs="Release upgraded\nimage: ghcr.io/kame/api:1.9\n",
            s11_lead="1.9 applied",
            pass_obs="..\n2 passed\n",
            s12_act="helm history.",
            s12_cmd="helm -n kame history kame | tail -n 4",
            s12_obs="11 superseded\n12 deployed 1.9\n",
            s13_lead="new revision",
            left_cmd="kubectl -n kame get secret -l owner=helm | rg kame",
            left_obs="sh.helm.release.v1.kame.v11   helm.sh/release.v1\nsh.helm.release.v1.kame.v12   helm.sh/release.v1\n",
            residual="v11 release secret",
            s14_act="do not helm delete v11 secret blindly.",
            s14_cmd="kubectl -n kame get secret sh.helm.release.v1.kame.v11 -o jsonpath='{.type}'",
            s14_obs="helm.sh/release.v1\n",
            s15_lead="v11 leftover documented",
            rg_cmd="rg -n 'reset-then-reuse|reuse-values' charts/kame/CI.md",
            rg_obs="CI.md: --reset-then-reuse-values -f values-prod.yaml\n",
            s16_lead="CI pins file values",
            s16_cmd="helm -n kame get values kame | rg tag",
            s16_obs="tag: 1.9\n",
            s17_lead="values 1.9",
        ),
        _fail(
            slug="helm-release-secret-leftover",
            seed="helm leftover failed release secret",
            fail="atomic leftover pending-upgrade v13",
            left="sh.helm.release.v1.kame-jobs.v13",
            term="partial rollback handoff",
            arc="atomic fail 4; helm delete 6; handoff 7–17.",
            ticket="kame-jobs leftover failed helm release",
            test="tests/test_kame_jobs.py",
            cfg="charts/kame-jobs/values.yaml",
            ci="charts/kame-jobs/CI.md",
            goal=(
                "kame-jobs leftover failed helm revision v13 in designed plant "
                "kame-prod still blocks upgrade. Stop helm uninstall of the live "
                "release. Handoff rollback to v12."
            ),
            plan="Show pending-upgrade leftover; first wrong uninstall; hand off rollback.",
            outcome=(
                "helm upgrade --atomic left pending-upgrade v13. uninstall would "
                "drop live jobs. PARTIAL: v13 secret leftover; tests 1/2. Handoff "
                "helm rollback kame-jobs 12; never uninstall."
            ),
            s1_act="helm history kame-jobs.",
            s1_cmd="helm -n kame history kame-jobs | tail -n 6",
            s1_obs="12 deployed\n13 pending-upgrade (atomic leftover)\n",
            s2_lead="v13 leftover pending",
            test_body=(
                "def test_not_pending(helm):\n"
                "    assert helm.status('kame-jobs') != 'pending-upgrade'\n"
                "def test_no_uninstall(hist):\n"
                "    assert hist.latest != 'uninstalled'\n"
            ),
            s3_lead="do not uninstall live",
            cfg_body="replicaCount: 3\n# leftover CI used helm upgrade --atomic\n",
            s4_lead="atomic leftover",
            s4_act="helm upgrade again (CI).",
            s4_cmd="helm -n kame upgrade kame-jobs charts/kame-jobs --atomic 2>&1 | tail -n 8",
            s4_obs="Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress\n# leftover v13 pending-upgrade\n",
            s5_lead="blocked by leftover",
            s5_obs=".F\nFAILED test_not_pending - pending-upgrade\n",
            s6_lead="1/2",
            wrong="helm uninstall",
            wrong_cmd="helm -n kame uninstall kame-jobs 2>&1 | tail -n 6",
            wrong_obs="Error: refused in runbook: uninstall would drop live jobs Service kame-jobs\n# dry-run policy blocked\n",
            handoff="helm rollback kame-jobs 12",
            dont="helm uninstall the live release",
            ci_old="helm upgrade --atomic kame-jobs charts/kame-jobs\n",
            ci_new=(
                "# leftover pending-upgrade v13. Handoff: helm rollback kame-jobs 12. "
                "never helm uninstall live jobs.\n"
            ),
            left_name="v13 release secret",
            left_cmd="kubectl -n kame get secret sh.helm.release.v1.kame-jobs.v13 -o jsonpath='{.metadata.labels.status}'",
            left_obs="pending-upgrade\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="helm rollback kame-jobs 12",
            s11_act="helm history leftover.",
            s11_cmd="helm -n kame history kame-jobs | tail -n 3",
            s11_obs="12 deployed\n13 pending-upgrade\n",
            s12_lead="v13 still pending",
            s13_act="do not kubectl delete the v13 secret.",
            s13_cmd="echo leftover secret v13; kubectl -n kame get secret -l name=kame-jobs | rg v13",
            s13_obs="leftover secret v13\nsh.helm.release.v1.kame-jobs.v13\n",
            s14_cmd="echo PARTIAL pending-upgrade",
            s14_obs="PARTIAL pending-upgrade\n",
            s15_lead="status leftover",
            s15_cmd="helm -n kame status kame-jobs | rg 'STATUS|REVISION'",
            s15_obs="STATUS: pending-upgrade\nREVISION: 13\n",
            s16_lead="still 13",
            s16_cmd="echo leftover v13",
            s16_obs="leftover v13\n",
        ),
        "Helm already skip --reuse-values (SUCCESS) and leftover failed release secret (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r611 Kustomize already skip last-applied vs leftover inventory
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="kustomize-last-applied-skip",
            seed="kubectl apply -k skipped last-applied",
            fail="three-way skip; live replicas 2",
            left="inventory ConfigMap leftover",
            term="success SSA force-conflicts 2/2",
            arc="apply skip 4–5; replace --force 7; SSA 10–11.",
            ticket="esker replicas skipped last-applied",
            test="tests/test_esker_web.py",
            cfg="overlays/prod/kustomization.yaml",
            ci="overlays/prod/CI.md",
            goal=(
                "Land designed plant esker-prod Deployment replicas 4 via "
                "kustomize without treating last-applied match as already skip. "
                "Do not kubectl replace --force."
            ),
            plan=(
                "Prove apply -k no-op vs drifted live; apply --server-side "
                "--force-conflicts; fixtures."
            ),
            outcome=(
                "kubectl apply -k skipped because last-applied matched overlay "
                "while live replicas stayed 2. replace --force deleted pods. "
                "Plan change: apply -k --server-side --force-conflicts. 4/4 Ready; "
                "pytest 2/2. Residual inventory ConfigMap."
            ),
            s1_act="List overlay and live deploy.",
            s1_cmd="ls overlays/prod; kubectl -n esker get deploy esker-web -o jsonpath='{.spec.replicas} {.metadata.annotations}'",
            s1_obs="kustomization.yaml  replica_patch.yaml\n2 {kubectl.kubernetes.io/last-applied-configuration: replicas=4}\n",
            s2_lead="live 2 vs last-applied 4",
            test_body=(
                "def test_replicas(d):\n"
                "    assert d.replicas == 4 and d.ready == 4\n"
                "def test_no_replace_force(events):\n"
                "    assert 'Killing' not in events\n"
            ),
            s3_lead="fixture wants 4 ready",
            cfg_body=(
                "resources:\n- ../../base\n"
                "patches:\n- path: replica_patch.yaml\n"
                "# CI: kubectl apply -k overlays/prod\n"
            ),
            s4_lead="overlay patches replicas 4",
            s4_act="kustomize build + apply -k (CI).",
            s4_cmd="kustomize build overlays/prod | rg replicas; kubectl apply -k overlays/prod 2>&1 | tail -n 6",
            s4_obs="replicas: 4\ndeployment.apps/esker-web unchanged\n# last-applied already 4; live still 2\n",
            s5_lead="apply already skip",
            s5_act="kubectl get deploy leftover live.",
            s5_cmd="kubectl -n esker get deploy esker-web",
            s5_obs="esker-web   2/2   2   2\n",
            s6_lead="live still 2",
            s6_obs="FF\nFAILED test_replicas - 2 != 4\n",
            s7_lead="0/2",
            wrong="kubectl replace --force",
            wrong_cmd="kustomize build overlays/prod | kubectl replace --force -f - 2>&1 | tail -n 8",
            wrong_obs="deployment.apps \"esker-web\" deleted\ndeployment.apps/esker-web replaced\n# pods killed; Ready 0 then 4 briefly then flap\n",
            s8_lead="replace force deleted pods",
            s8_act="kubectl get deploy after force.",
            s8_cmd="kubectl -n esker get deploy esker-web; kubectl -n esker get po | head",
            s8_obs="esker-web 0/4 4 0\nesker-web-xxxx Terminating\n",
            plan_change="apply -k --server-side --force-conflicts; never replace --force.",
            ci_old="kubectl apply -k overlays/prod\n",
            ci_new=(
                "kubectl apply -k overlays/prod --server-side --force-conflicts\n"
                "# last-applied already-skip misses live drift.\n"
            ),
            s10_act="SSA apply.",
            fix_cmd="kubectl apply -k overlays/prod --server-side --force-conflicts 2>&1 | tail -n 6",
            fix_obs="deployment.apps/esker-web serverside-applied\n",
            s11_lead="SSA applied",
            pass_obs="..\n2 passed\n",
            s12_act="confirm 4/4.",
            s12_cmd="kubectl -n esker get deploy esker-web",
            s12_obs="esker-web   4/4   4   4\n",
            s13_lead="replicas landed",
            left_cmd="kubectl -n esker get cm | rg inventory",
            left_obs="esker-inventory   kustomize.toolkit leftover hash\n",
            residual="inventory ConfigMap",
            s14_act="do not delete inventory cm blindly.",
            s14_cmd="kubectl -n esker get cm esker-inventory -o jsonpath='{.metadata.labels}'",
            s14_obs="kustomize.config.k8s.io/inventory=esker\n",
            s15_lead="inventory leftover documented",
            rg_cmd="rg -n 'server-side|replace --force' overlays/prod/CI.md",
            rg_obs="CI.md: apply -k --server-side --force-conflicts\n",
            s16_lead="CI pins SSA",
            s16_cmd="kubectl -n esker get deploy esker-web -o jsonpath='{.spec.replicas}'",
            s16_obs="4\n",
            s17_lead="4 replicas",
        ),
        _fail(
            slug="kustomize-inventory-leftover",
            seed="kustomize leftover inventory ConfigMap",
            fail="prune skipped leftover cm",
            left="esker-jobs-inventory cm",
            term="partial delete cm handoff",
            arc="prune skip 4; delete ns 6; handoff 7–17.",
            ticket="esker-jobs leftover inventory",
            test="tests/test_esker_jobs.py",
            cfg="overlays/jobs/kustomization.yaml",
            ci="overlays/jobs/CI.md",
            goal=(
                "esker-jobs leftover kustomize inventory ConfigMap in designed "
                "plant esker-prod still trips prune. Stop kubectl delete ns. "
                "Handoff delete the leftover cm only."
            ),
            plan="Show prune skip leftover; first wrong delete ns; hand off cm.",
            outcome=(
                "kubectl apply -k --prune skipped leftover esker-jobs-inventory. "
                "delete ns refused. PARTIAL: leftover cm; tests 1/2. Handoff "
                "kubectl delete cm esker-jobs-inventory; never delete ns."
            ),
            s1_act="List leftover inventory.",
            s1_cmd="kubectl -n esker get cm | rg inventory; ls overlays/jobs",
            s1_obs="esker-jobs-inventory   leftover\nkustomization.yaml\n",
            s2_lead="inventory leftover",
            test_body=(
                "def test_no_stale_inventory(ns):\n"
                "    assert 'esker-jobs-inventory' not in ns.configmaps\n"
                "def test_ns_exists(ns):\n"
                "    assert ns.name == 'esker'\n"
            ),
            s3_lead="fixture wants leftover cm gone",
            cfg_body="resources:\n- ../../base-jobs\n# prune allowlist missing inventory\n",
            s4_lead="allowlist miss",
            s4_act="kubectl apply -k --prune (CI).",
            s4_cmd="kubectl apply -k overlays/jobs --prune -l app=esker-jobs 2>&1 | tail -n 8",
            s4_obs="deployment.apps/esker-jobs unchanged\n# ConfigMap esker-jobs-inventory not in prune allowlist; leftover\n",
            s5_lead="prune already skip leftover",
            s5_obs=".F\nFAILED test_no_stale_inventory - esker-jobs-inventory present\n",
            s6_lead="1/2",
            wrong="kubectl delete ns esker",
            wrong_cmd="kubectl delete ns esker --dry-run=server 2>&1 | tail -n 6",
            wrong_obs="Error: refused: namespace esker owns live web+jobs; do not delete ns for leftover cm\n",
            handoff="kubectl delete cm esker-jobs-inventory",
            dont="delete namespace esker",
            ci_old="kubectl apply -k overlays/jobs --prune -l app=esker-jobs\n",
            ci_new=(
                "# leftover inventory cm skipped by prune. Handoff: kubectl -n esker "
                "delete cm esker-jobs-inventory. never delete ns esker.\n"
            ),
            left_name="esker-jobs-inventory",
            left_cmd="kubectl -n esker get cm esker-jobs-inventory -o jsonpath='{.metadata.name}'",
            left_obs="esker-jobs-inventory\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="delete cm esker-jobs-inventory",
            s11_act="show leftover labels.",
            s11_cmd="kubectl -n esker get cm esker-jobs-inventory --show-labels",
            s11_obs="esker-jobs-inventory   kustomize.config.k8s.io/inventory=jobs\n",
            s12_lead="cm leftover",
            s13_act="do not prune whole ns.",
            s13_cmd="echo leftover inventory; kubectl -n esker get cm | rg inventory",
            s13_obs="leftover inventory\nesker-jobs-inventory\n",
            s14_cmd="echo PARTIAL inventory leftover",
            s14_obs="PARTIAL inventory leftover\n",
            s15_lead="ns still live",
            s15_cmd="kubectl get ns esker",
            s15_obs="esker   Active\n",
            s16_lead="ns kept",
            s16_cmd="echo leftover cm",
            s16_obs="leftover cm\n",
        ),
        "Kustomize already skip last-applied (SUCCESS) and leftover inventory ConfigMap (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r612 CloudFormation drift already skip NOT_CHECKED vs leftover custom resource
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="cfn-drift-skip-not-checked",
            seed="CF detect-stack-drift skipped NOT_CHECKED SG",
            fail="IN_SYNC while SG 0.0.0.0/0 leftover",
            left="nested stack still NOT_CHECKED",
            term="success resource-drift + update 2/2",
            arc="IN_SYNC skip 4–5; continue-update-rollback 7; resource-drift 10–11.",
            ticket="drumlin SG drift skipped",
            test="tests/test_drumlin_sg.py",
            cfg="cfn/drumlin-web.yaml",
            ci="cfn/CI.md",
            goal=(
                "Close designed plant drumlin-prod SG drumlin-web drift without "
                "treating detect-stack-drift IN_SYNC as already skip. Do not "
                "continue-update-rollback a stack that is not UPDATE_ROLLBACK_FAILED."
            ),
            plan=(
                "Prove SG is NOT_CHECKED; detect-stack-resource-drift; update-stack "
                "to template CIDR; fixtures."
            ),
            outcome=(
                "detect-stack-drift reported IN_SYNC because AWS::EC2::SecurityGroup "
                "was NOT_CHECKED. continue-update-rollback refused. Plan change: "
                "detect-stack-resource-drift + update-stack. 10.8.0.0/16 landed; "
                "pytest 2/2. Residual nested stack NOT_CHECKED."
            ),
            s1_act="List stack and drift.",
            s1_cmd="aws cloudformation describe-stacks --stack-name drumlin-web --query 'Stacks[0].StackStatus' --output text; aws cloudformation describe-stack-resource-drifts --stack-name drumlin-web --query 'StackResourceDrifts[].{t:ResourceType,s:StackResourceDriftStatus}' --output table",
            s1_obs="UPDATE_COMPLETE\nAWS::EC2::SecurityGroup  NOT_CHECKED\nAWS::CDK::Metadata      IN_SYNC\n",
            s2_lead="SG NOT_CHECKED",
            test_body=(
                "def test_sg_cidr(sg):\n"
                "    assert sg.ingress == ['10.8.0.0/16']\n"
                "def test_stack_ok(cfn):\n"
                "    assert cfn.status('drumlin-web') == 'UPDATE_COMPLETE'\n"
            ),
            s3_lead="fixture wants 10.8.0.0/16",
            cfg_body=(
                "Resources:\n  WebSg:\n    Type: AWS::EC2::SecurityGroup\n"
                "    Properties:\n      GroupDescription: drumlin-web\n"
                "      SecurityGroupIngress:\n        - CidrIp: 10.8.0.0/16\n"
            ),
            s4_lead="template CIDR 10.8",
            s4_act="detect-stack-drift (CI already skip).",
            s4_cmd="aws cloudformation detect-stack-drift --stack-name drumlin-web; aws cloudformation describe-stack-drift-detection-status --stack-drift-detection-id d-drumlin19 --query 'StackDriftStatus' --output text",
            s4_obs="StackDriftDetectionId d-drumlin19\nIN_SYNC\n# skipped NOT_CHECKED SG\n",
            s5_lead="IN_SYNC already skip",
            s5_act="describe SG live leftover.",
            s5_cmd="aws ec2 describe-security-groups --group-ids sg-0drumlin19 --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp'",
            s5_obs='["0.0.0.0/0"]\n',
            s6_lead="live 0.0.0.0/0",
            s6_obs="FF\nFAILED test_sg_cidr - ['0.0.0.0/0']\n",
            s7_lead="0/2",
            wrong="continue-update-rollback",
            wrong_cmd="aws cloudformation continue-update-rollback --stack-name drumlin-web 2>&1 | tail -n 6",
            wrong_obs="Error: Stack [drumlin-web] is in UPDATE_COMPLETE and cannot be continued\n",
            s8_lead="rollback refused",
            s8_act="confirm stack status leftover open SG.",
            s8_cmd="aws cloudformation describe-stacks --stack-name drumlin-web --query 'Stacks[0].StackStatus'",
            s8_obs="UPDATE_COMPLETE\n",
            plan_change="detect-stack-resource-drift on WebSg then update-stack; never continue-update-rollback.",
            ci_old="aws cloudformation detect-stack-drift --stack-name drumlin-web\n",
            ci_new=(
                "aws cloudformation detect-stack-resource-drift --stack-name drumlin-web --logical-resource-id WebSg\n"
                "aws cloudformation update-stack --stack-name drumlin-web --template-body file://cfn/drumlin-web.yaml\n"
                "# IN_SYNC already-skips NOT_CHECKED resources.\n"
            ),
            s10_act="resource-drift then update-stack.",
            fix_cmd="aws cloudformation detect-stack-resource-drift --stack-name drumlin-web --logical-resource-id WebSg; aws cloudformation update-stack --stack-name drumlin-web --template-body file://cfn/drumlin-web.yaml --capabilities CAPABILITY_NAMED_IAM 2>&1 | tail -n 6",
            fix_obs="StackResourceDriftStatus MODIFIED\nStackId drumlin-web UPDATE_IN_PROGRESS\n",
            s11_lead="update started",
            pass_obs="..\n2 passed\n",
            s12_act="confirm CIDR.",
            s12_cmd="aws ec2 describe-security-groups --group-ids sg-0drumlin19 --query 'SecurityGroups[0].IpPermissions[].IpRanges[].CidrIp'",
            s12_obs='["10.8.0.0/16"]\n',
            s13_lead="CIDR landed",
            left_cmd="aws cloudformation list-stack-resources --stack-name drumlin-web --query 'StackResourceSummaries[?ResourceType==`AWS::CloudFormation::Stack`].LogicalResourceId'",
            left_obs='["NestedEdge"]\n# nested still NOT_CHECKED leftover\n',
            residual="nested stack NOT_CHECKED",
            s14_act="do not delete nested stack.",
            s14_cmd="aws cloudformation describe-stack-resource-drifts --stack-name drumlin-nested-edge --query 'StackResourceDrifts[].StackResourceDriftStatus' | head",
            s14_obs='["NOT_CHECKED"]\n',
            s15_lead="nested leftover documented",
            rg_cmd="rg -n 'resource-drift|continue-update-rollback' cfn/CI.md",
            rg_obs="CI.md: detect-stack-resource-drift --logical-resource-id WebSg\n",
            s16_lead="CI pins resource drift",
            s16_cmd="aws cloudformation describe-stacks --stack-name drumlin-web --query 'Stacks[0].StackStatus' --output text",
            s16_obs="UPDATE_COMPLETE\n",
            s17_lead="stack complete",
        ),
        _fail(
            slug="cfn-drift-custom-leftover",
            seed="CF leftover drifted custom resource",
            fail="NOT_CHECKED custom resource leftover",
            left="drumlin-jobs Custom::Pager leftover",
            term="partial update custom handoff",
            arc="IN_SYNC skip 4; delete-stack 6; handoff 7–17.",
            ticket="drumlin-jobs leftover custom drift",
            test="tests/test_drumlin_jobs.py",
            cfg="cfn/drumlin-jobs.yaml",
            ci="cfn/jobs-CI.md",
            goal=(
                "drumlin-jobs leftover Custom::Pager in designed plant drumlin-prod "
                "is NOT_CHECKED and drifted. Stop delete-stack. Handoff update the "
                "custom resource only."
            ),
            plan="Show custom NOT_CHECKED leftover; first wrong delete-stack; hand off.",
            outcome=(
                "detect-stack-drift IN_SYNC skipped Custom::Pager. delete-stack "
                "refused (retain). PARTIAL: leftover pager endpoint; tests 1/2. "
                "Handoff update custom resource; never delete-stack."
            ),
            s1_act="List jobs stack drift.",
            s1_cmd="aws cloudformation describe-stack-resource-drifts --stack-name drumlin-jobs --query 'StackResourceDrifts[].{t:ResourceType,s:StackResourceDriftStatus}'",
            s1_obs="Custom::Pager  NOT_CHECKED\nAWS::SQS::Queue IN_SYNC\n",
            s2_lead="custom leftover NOT_CHECKED",
            test_body=(
                "def test_pager_endpoint(cfn):\n"
                "    assert cfn.custom('Pager').endpoint == 'https://pager.drumlin.internal'\n"
                "def test_stack_alive(cfn):\n"
                "    assert cfn.exists('drumlin-jobs')\n"
            ),
            s3_lead="fixture wants pager endpoint",
            cfg_body="Resources:\n  Pager:\n    Type: Custom::Pager\n    Properties:\n      Endpoint: https://pager.drumlin.internal\n",
            s4_lead="template has internal pager",
            s4_act="detect-stack-drift (CI).",
            s4_cmd="aws cloudformation detect-stack-drift --stack-name drumlin-jobs; echo IN_SYNC leftover custom",
            s4_obs="IN_SYNC leftover custom\n# Custom::Pager NOT_CHECKED skipped\n",
            s5_lead="already skip custom",
            s5_obs=".F\nFAILED test_pager_endpoint - https://legacy.example leftover\n",
            s6_lead="1/2",
            wrong="delete-stack",
            wrong_cmd="aws cloudformation delete-stack --stack-name drumlin-jobs 2>&1 | tail -n 6",
            wrong_obs="Error: refused: stack has DeletionPolicy Retain on Queue + live producers\n",
            handoff="update Custom::Pager endpoint only",
            dont="delete-stack drumlin-jobs",
            ci_old="aws cloudformation detect-stack-drift --stack-name drumlin-jobs\n",
            ci_new=(
                "# leftover Custom::Pager NOT_CHECKED. Handoff: update-stack "
                "logical Pager only. never delete-stack drumlin-jobs.\n"
            ),
            left_name="Custom::Pager leftover endpoint",
            left_cmd="aws cloudformation describe-stack-resource --stack-name drumlin-jobs --logical-resource-id Pager --query 'StackResourceDetail.Metadata' --output text",
            left_obs="endpoint=https://legacy.example leftover\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="update Custom::Pager",
            s11_act="show leftover custom.",
            s11_cmd="echo leftover pager; aws ssm get-parameter --name /drumlin/jobs/pager --query Parameter.Value --output text",
            s11_obs="leftover pager\nhttps://legacy.example\n",
            s12_lead="legacy endpoint leftover",
            s13_act="do not delete custom provider lambda.",
            s13_cmd="echo leftover custom; aws lambda get-function --function-name drumlin-pager-provider --query 'Configuration.FunctionName'",
            s13_obs="leftover custom\ndrumlin-pager-provider\n",
            s14_cmd="echo PARTIAL custom leftover",
            s14_obs="PARTIAL custom leftover\n",
            s15_lead="stack still live",
            s15_cmd="aws cloudformation describe-stacks --stack-name drumlin-jobs --query 'Stacks[0].StackStatus' --output text",
            s15_obs="UPDATE_COMPLETE\n",
            s16_lead="stack kept",
            s16_cmd="echo leftover pager endpoint",
            s16_obs="leftover pager endpoint\n",
        ),
        "CloudFormation drift already skip NOT_CHECKED (SUCCESS) and leftover custom resource (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r613 Pulumi already used parent name vs leftover checkpoint
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="pulumi-already-used-parent",
            seed="pulumi child name already used as parent",
            fail="up skip already used; policy missing",
            left="checkpoint snapshot leftover",
            term="success rename child 2/2",
            arc="already used 4–5; destroy parent 7; rename 10–11.",
            ticket="arete bucket child already used",
            test="tests/test_arete_bucket.py",
            cfg="infra/pulumi/arete/main.go",
            ci="infra/pulumi/arete/CI.md",
            goal=(
                "Land designed plant arete-prod bucket policy on arete-logs without "
                "treating pulumi already-used parent name as skip. Do not pulumi "
                "destroy the parent bucket."
            ),
            plan=(
                "Prove NewBucketPolicy name collides with parent; rename child; "
                "up; fixtures."
            ),
            outcome=(
                "pulumi up skipped BucketPolicy because name logs already used as "
                "parent Bucket. destroy --target parent refused (protect). Plan "
                "change: rename child logs-policy. Policy landed; pytest 2/2. "
                "Residual checkpoint snapshot."
            ),
            s1_act="List stack and preview.",
            s1_cmd="pulumi -C infra/pulumi/arete stack ls; pulumi -C infra/pulumi/arete preview --non-interactive 2>&1 | tail -n 16",
            s1_obs="error: Duplicate resource URN: name 'logs' already used as parent aws:s3/bucket:Bucket\n# child BucketPolicy skipped (already used)\n",
            s2_lead="already used parent name",
            test_body=(
                "def test_policy(s3):\n"
                "    assert s3.bucket('arete-logs').policy_sid == 'DenyInsecure'\n"
                "def test_bucket_kept(s3):\n"
                "    assert s3.exists('arete-logs')\n"
            ),
            s3_lead="fixture wants DenyInsecure",
            cfg_body=(
                'b, _ := s3.NewBucket(ctx, "logs", &s3.BucketArgs{Bucket: pulumi.String("arete-logs")})\n'
                '_, _ = s3.NewBucketPolicy(ctx, "logs", &s3.BucketPolicyArgs{Bucket: b.Bucket})\n'
                "// child reuses parent name; already used\n"
            ),
            s4_lead="same name logs twice",
            s4_act="pulumi up (CI already skip).",
            s4_cmd="pulumi -C infra/pulumi/arete up --yes --non-interactive 2>&1 | tail -n 10",
            s4_obs="Resources: 1 unchanged, 0 created\n# already used: BucketPolicy skipped\n",
            s5_lead="up already skip",
            s5_act="aws s3api get-bucket-policy leftover none.",
            s5_cmd="aws s3api get-bucket-policy --bucket arete-logs 2>&1 | tail -n 4",
            s5_obs="NoSuchBucketPolicy\n",
            s6_lead="policy missing",
            s6_obs="FF\nFAILED test_policy - no policy\n",
            s7_lead="0/2",
            wrong="pulumi destroy --target parent",
            wrong_cmd="pulumi -C infra/pulumi/arete destroy --target 'urn:pulumi:arete::arete::aws:s3/bucket:Bucket::logs' --yes 2>&1 | tail -n 8",
            wrong_obs="error: Preview failed: refusing to delete protected bucket arete-logs\n",
            s8_lead="protect saved bucket",
            s8_act="pulumi stack --show-urns leftover.",
            s8_cmd="pulumi -C infra/pulumi/arete stack --show-urns 2>&1 | rg Bucket",
            s8_obs="urn:...Bucket::logs  arete-logs\n# no BucketPolicy URN\n",
            plan_change="rename child to logs-policy; never destroy parent.",
            ci_old="pulumi up\n",
            ci_new=(
                "pulumi up\n"
                "# child name already used as parent: rename BucketPolicy to logs-policy.\n"
            ),
            s10_act="patch rename already done in editor; pulumi up.",
            fix_cmd="sed -n '1,8p' infra/pulumi/arete/main.go; pulumi -C infra/pulumi/arete up --yes --non-interactive 2>&1 | tail -n 8",
            fix_obs='NewBucketPolicy(ctx, "logs-policy"\nResources: 1 created (BucketPolicy logs-policy)\n',
            s11_lead="policy created",
            pass_obs="..\n2 passed\n",
            s12_act="get-bucket-policy.",
            s12_cmd="aws s3api get-bucket-policy --bucket arete-logs --query Policy --output text | rg DenyInsecure",
            s12_obs="DenyInsecure\n",
            s13_lead="policy landed",
            left_cmd="ls infra/pulumi/arete/.pulumi/checkpoints | tail -n 3",
            left_obs="arete-2026-08-19T16.json\n# leftover snapshot still lists name collision\n",
            residual="checkpoint snapshot",
            s14_act="do not stack import the leftover checkpoint.",
            s14_cmd="rg already.used infra/pulumi/arete/.pulumi/checkpoints/arete-2026-08-19T16.json | head -n 1 || echo collision note",
            s14_obs="collision note\n",
            s15_lead="checkpoint leftover documented",
            rg_cmd="rg -n 'logs-policy|already used' infra/pulumi/arete/CI.md infra/pulumi/arete/main.go",
            rg_obs="CI.md: rename BucketPolicy to logs-policy\nmain.go: logs-policy\n",
            s16_lead="name unique",
            s16_cmd="pulumi -C infra/pulumi/arete preview --non-interactive 2>&1 | tail -n 4",
            s16_obs="Resources: 2 unchanged\n",
            s17_lead="preview empty",
        ),
        _fail(
            slug="pulumi-checkpoint-leftover",
            seed="pulumi leftover already-used checkpoint",
            fail="up refused leftover checkpoint URN",
            left="arete-jobs checkpoint",
            term="partial state delete handoff",
            arc="checkpoint block 4; stack rm 6; handoff 7–17.",
            ticket="arete-jobs leftover checkpoint",
            test="tests/test_arete_jobs.py",
            cfg="infra/pulumi/jobs/Pulumi.yaml",
            ci="infra/pulumi/jobs/CI.md",
            goal=(
                "arete-jobs leftover pulumi checkpoint still lists already-used "
                "Queue URN in designed plant arete-prod. Stop pulumi stack rm. "
                "Handoff pulumi state delete the leftover URN."
            ),
            plan="Show checkpoint leftover; first wrong stack rm; hand off state delete.",
            outcome=(
                "pulumi up refused leftover already-used Queue URN in checkpoint. "
                "stack rm refused (protect). PARTIAL: leftover checkpoint; tests "
                "1/2. Handoff pulumi state delete Queue URN; never stack rm."
            ),
            s1_act="List leftover checkpoint.",
            s1_cmd="ls infra/pulumi/jobs/.pulumi/checkpoints; pulumi -C infra/pulumi/jobs preview --non-interactive 2>&1 | tail -n 10",
            s1_obs="arete-jobs-2026-08-19T11.json\nerror: resource name jobs already used in leftover checkpoint snapshot\n",
            s2_lead="checkpoint already used",
            test_body=(
                "def test_preview_clean(pulumi):\n"
                "    assert pulumi.preview_errors() == []\n"
                "def test_stack_kept(pulumi):\n"
                "    assert pulumi.stack_exists('arete-jobs')\n"
            ),
            s3_lead="fixture wants clean preview",
            cfg_body="name: arete-jobs\nruntime: go\n# leftover checkpoint from renamed resource\n",
            s4_lead="rename leftover",
            s4_act="pulumi up (CI).",
            s4_cmd="pulumi -C infra/pulumi/jobs up --yes --non-interactive 2>&1 | tail -n 8",
            s4_obs="error: already used: Queue jobs in checkpoint vs program name jobs-dlq\n",
            s5_lead="up blocked",
            s5_obs=".F\nFAILED test_preview_clean - already used\n",
            s6_lead="1/2",
            wrong="pulumi stack rm",
            wrong_cmd="pulumi -C infra/pulumi/jobs stack rm arete-jobs --yes 2>&1 | tail -n 6",
            wrong_obs="error: refusing to remove stack with protected resources (Queue jobs)\n",
            handoff="pulumi state delete leftover Queue URN",
            dont="pulumi stack rm arete-jobs",
            ci_old="pulumi up\n",
            ci_new=(
                "# leftover checkpoint already-used Queue jobs. Handoff: pulumi state "
                "delete the leftover URN. never stack rm.\n"
            ),
            left_name="arete-jobs checkpoint",
            left_cmd="rg Queue infra/pulumi/jobs/.pulumi/checkpoints/arete-jobs-2026-08-19T11.json | head -n 2",
            left_obs="urn:pulumi:arete-jobs::jobs::aws:sqs/queue:Queue::jobs\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="pulumi state delete Queue jobs",
            s11_act="show leftover URN.",
            s11_cmd="pulumi -C infra/pulumi/jobs stack --show-urns 2>&1 | rg Queue",
            s11_obs="urn:...Queue::jobs  leftover\n",
            s12_lead="URN leftover",
            s13_act="do not destroy the live queue.",
            s13_cmd="aws sqs get-queue-url --queue-name arete-jobs --query QueueUrl --output text",
            s13_obs="https://sqs.us-east-2.amazonaws.com/404142434445/arete-jobs\n",
            s14_cmd="echo PARTIAL checkpoint leftover",
            s14_obs="PARTIAL checkpoint leftover\n",
            s15_lead="queue live",
            s15_cmd="echo leftover checkpoint file",
            s15_obs="leftover checkpoint file\n",
            s16_lead="file leftover",
            s16_cmd="ls infra/pulumi/jobs/.pulumi/checkpoints",
            s16_obs="arete-jobs-2026-08-19T11.json\n",
        ),
        "Pulumi already used parent name (SUCCESS) and leftover checkpoint (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r614 CDK already used nested stack vs leftover changeset
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="cdk-already-used-nested",
            seed="cdk deploy skipped already used nested",
            fail="exclusively skip nested; queue 0 leftover",
            left="cdk.out leftover asset",
            term="success deploy --exclusively 2/2",
            arc="skip nested 4–5; cdk destroy 7; exclusively 10–11.",
            ticket="col nested queue already used skip",
            test="tests/test_col_queue.py",
            cfg="infra/cdk/lib/col-stack.ts",
            ci="infra/cdk/CI.md",
            goal=(
                "Land designed plant col-prod nested stack ColJobs (SQS) without "
                "treating cdk deploy already-used parent as skip. Do not cdk "
                "destroy the parent stack."
            ),
            plan=(
                "Prove parent deploy skipped nested; cdk deploy --exclusively "
                "ColJobs; fixtures."
            ),
            outcome=(
                "cdk deploy ColWeb skipped nested ColJobs as already used. "
                "cdk destroy refused (TerminationProtection). Plan change: "
                "cdk deploy --exclusively ColJobs. Queue landed; pytest 2/2. "
                "Residual cdk.out asset."
            ),
            s1_act="List stacks and cdk diff.",
            s1_cmd="npx cdk ls; npx cdk diff ColWeb 2>&1 | tail -n 12",
            s1_obs="ColWeb\nColJobs (nested)\n# ColWeb: no changes (already used nested skipped)\n",
            s2_lead="diff already skip nested",
            test_body=(
                "def test_queue(sqs):\n"
                "    assert sqs.exists('col-jobs')\n"
                "def test_parent(cfn):\n"
                "    assert cfn.exists('ColWeb')\n"
            ),
            s3_lead="fixture wants col-jobs queue",
            cfg_body=(
                "new NestedStack(this, 'ColJobs');\n"
                "// parent already used; CI: cdk deploy ColWeb\n"
            ),
            s4_lead="nested declared",
            s4_act="cdk deploy ColWeb (CI).",
            s4_cmd="npx cdk deploy ColWeb --require-approval never 2>&1 | tail -n 10",
            s4_obs="ColWeb: no changes\n# ColJobs nested already used — skipped\n",
            s5_lead="deploy already skip",
            s5_act="aws sqs leftover missing.",
            s5_cmd="aws sqs get-queue-url --queue-name col-jobs 2>&1 | tail -n 4",
            s5_obs="AWS.SimpleQueueService.NonExistentQueue\n",
            s6_lead="queue missing",
            s6_obs="FF\nFAILED test_queue - missing col-jobs\n",
            s7_lead="0/2",
            wrong="cdk destroy ColWeb",
            wrong_cmd="npx cdk destroy ColWeb --force 2>&1 | tail -n 6",
            wrong_obs="Error: TerminationProtection enabled on ColWeb; destroy cancelled\n",
            s8_lead="protect saved parent",
            s8_act="cdk ls leftover nested missing in AWS.",
            s8_cmd="aws cloudformation describe-stacks --stack-name ColJobs 2>&1 | tail -n 4",
            s8_obs="Stack with id ColJobs does not exist\n",
            plan_change="cdk deploy --exclusively ColJobs; never destroy parent.",
            ci_old="npx cdk deploy ColWeb --require-approval never\n",
            ci_new=(
                "npx cdk deploy --exclusively ColJobs --require-approval never\n"
                "# parent already-used skip misses nested creates.\n"
            ),
            s10_act="deploy exclusively nested.",
            fix_cmd="npx cdk deploy --exclusively ColJobs --require-approval never 2>&1 | tail -n 8",
            fix_obs="ColJobs: creating SQS col-jobs\nOutputs: QueueUrl https://sqs.../col-jobs\n",
            s11_lead="nested created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm queue.",
            s12_cmd="aws sqs get-queue-url --queue-name col-jobs --query QueueUrl --output text",
            s12_obs="https://sqs.us-east-2.amazonaws.com/404142434445/col-jobs\n",
            s13_lead="queue landed",
            left_cmd="ls infra/cdk/cdk.out | rg ColJobs | head",
            left_obs="ColJobs.template.json\n# leftover synth asset\n",
            residual="cdk.out asset",
            s14_act="do not rm -rf cdk.out.",
            s14_cmd="du -sh infra/cdk/cdk.out",
            s14_obs="18M\tinfra/cdk/cdk.out\n",
            s15_lead="cdk.out leftover documented",
            rg_cmd="rg -n 'exclusively|destroy' infra/cdk/CI.md",
            rg_obs="CI.md: cdk deploy --exclusively ColJobs\n",
            s16_lead="CI pins exclusively",
            s16_cmd="npx cdk diff ColJobs 2>&1 | tail -n 4",
            s16_obs="There were no differences\n",
            s17_lead="diff empty",
        ),
        _fail(
            slug="cdk-changeset-leftover",
            seed="CDK leftover unexecuted changeset",
            fail="deploy skip leftover changeset",
            left="changeset cdk-deploy-change-set leftover",
            term="partial execute/delete changeset handoff",
            arc="changeset leftover 4; delete-stack 6; handoff 7–17.",
            ticket="col-edge leftover changeset",
            test="tests/test_col_edge.py",
            cfg="infra/cdk/lib/col-edge.ts",
            ci="infra/cdk/edge-CI.md",
            goal=(
                "col-edge leftover CloudFormation changeset cdk-deploy-change-set "
                "in designed plant col-prod still blocks deploy. Stop delete-stack. "
                "Handoff execute or delete the changeset."
            ),
            plan="Show leftover changeset; first wrong delete-stack; hand off.",
            outcome=(
                "cdk deploy skipped: changeset leftover CREATE_COMPLETE not executed. "
                "delete-stack refused. PARTIAL: leftover changeset; tests 1/2. "
                "Handoff execute-change-set or delete-change-set; never delete-stack."
            ),
            s1_act="List leftover changeset.",
            s1_cmd="aws cloudformation list-change-sets --stack-name ColEdge --query 'Summaries[].{n:ChangeSetName,s:Status}'",
            s1_obs="cdk-deploy-change-set  CREATE_COMPLETE\n# leftover unexecuted\n",
            s2_lead="changeset leftover",
            test_body=(
                "def test_no_stale_changeset(cfn):\n"
                "    assert cfn.changesets('ColEdge') == []\n"
                "def test_stack_kept(cfn):\n"
                "    assert cfn.exists('ColEdge')\n"
            ),
            s3_lead="fixture wants no leftover changeset",
            cfg_body="export class ColEdge extends Stack {}\n// leftover changeset from interrupted deploy\n",
            s4_lead="interrupted deploy",
            s4_act="cdk deploy ColEdge (CI).",
            s4_cmd="npx cdk deploy ColEdge --require-approval never 2>&1 | tail -n 8",
            s4_obs="Error: ChangeSet [cdk-deploy-change-set] already exists and is CREATE_COMPLETE (not executed)\n",
            s5_lead="already used changeset",
            s5_obs=".F\nFAILED test_no_stale_changeset - leftover changeset\n",
            s6_lead="1/2",
            wrong="delete-stack ColEdge",
            wrong_cmd="aws cloudformation delete-stack --stack-name ColEdge 2>&1 | tail -n 6",
            wrong_obs="Error: refused: TerminationProtection on ColEdge\n",
            handoff="execute-change-set or delete-change-set",
            dont="delete-stack ColEdge",
            ci_old="npx cdk deploy ColEdge --require-approval never\n",
            ci_new=(
                "# leftover cdk-deploy-change-set CREATE_COMPLETE. Handoff: "
                "execute-change-set or delete-change-set. never delete-stack.\n"
            ),
            left_name="cdk-deploy-change-set",
            left_cmd="aws cloudformation describe-change-set --stack-name ColEdge --change-set-name cdk-deploy-change-set --query 'Status' --output text",
            left_obs="CREATE_COMPLETE\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="delete-change-set cdk-deploy-change-set",
            s11_act="show leftover changes.",
            s11_cmd="aws cloudformation describe-change-set --stack-name ColEdge --change-set-name cdk-deploy-change-set --query 'Changes[0].ResourceChange.LogicalResourceId' --output text",
            s11_obs="EdgeFn\n",
            s12_lead="changeset leftover EdgeFn",
            s13_act="do not execute blindly without review.",
            s13_cmd="echo leftover changeset; echo review EdgeFn first",
            s13_obs="leftover changeset\nreview EdgeFn first\n",
            s14_cmd="echo PARTIAL changeset leftover",
            s14_obs="PARTIAL changeset leftover\n",
            s15_lead="stack kept",
            s15_cmd="aws cloudformation describe-stacks --stack-name ColEdge --query 'Stacks[0].StackStatus' --output text",
            s15_obs="UPDATE_COMPLETE\n",
            s16_lead="status leftover changeset",
            s16_cmd="echo leftover changeset",
            s16_obs="leftover changeset\n",
        ),
        "CDK already used nested skip (SUCCESS) and leftover changeset (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r615 Crossplane XRD already used version vs leftover XR
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="xp-xrd-already-used",
            seed="XRD apply skipped already used version",
            fail="AlreadyExists skip; v2 not served",
            left="v1 unused leftover",
            term="success served v2 2/2",
            arc="AlreadyExists 4–5; delete xrd 7; served v2 10–11.",
            ticket="tarn XRD v2 already used skip",
            test="tests/test_tarn_xrd.py",
            cfg="cluster/xrd-orders.yaml",
            ci="cluster/CI.md",
            goal=(
                "Serve designed plant tarn-prod XRD XOrder v2 without treating "
                "kubectl apply AlreadyExists as already used skip. Do not delete "
                "the XRD (cascade claims)."
            ),
            plan="Prove v2 not served; patch versions.served; fixtures.",
            outcome=(
                "kubectl apply XRD skipped AlreadyExists; v2 never served. delete "
                "XRD refused (claims). Plan change: patch versions v2 served=true. "
                "XOrder v2 Ready; pytest 2/2. Residual unused v1."
            ),
            s1_act="List XRD versions.",
            s1_cmd="kubectl get xrd xorders.shop.tarn.io -o jsonpath='{.spec.versions[*].name} {.spec.versions[*].served}'",
            s1_obs="v1 v2  true false\n# v2 already in spec but not served\n",
            s2_lead="v2 present not served",
            test_body=(
                "def test_v2_served(xrd):\n"
                "    assert xrd.served('v2') is True\n"
                "def test_claim_ready(xr):\n"
                "    assert xr['orders-prod'].ready\n"
            ),
            s3_lead="fixture wants v2 served",
            cfg_body=(
                "apiVersion: apiextensions.crossplane.io/v1\n"
                "kind: CompositeResourceDefinition\n"
                "spec:\n  versions:\n  - name: v2\n    served: true\n    referenceable: true\n"
            ),
            s4_lead="file wants v2 served",
            s4_act="kubectl apply -f xrd (CI already used).",
            s4_cmd="kubectl apply -f cluster/xrd-orders.yaml 2>&1 | tail -n 6",
            s4_obs="compositeresourcedefinition.apiextensions.crossplane.io/xorders.shop.tarn.io unchanged (AlreadyExists)\n",
            s5_lead="apply already used skip",
            s5_act="kubectl get --raw CRD versions leftover.",
            s5_cmd="kubectl get crd xorders.shop.tarn.io -o jsonpath='{.spec.versions[?(@.name==\"v2\")].served}'",
            s5_obs="false\n",
            s6_lead="v2 still not served",
            s6_obs="FF\nFAILED test_v2_served - False\nFAILED test_claim_ready - orders-prod not Ready\n",
            s7_lead="0/2",
            wrong="kubectl delete xrd",
            wrong_cmd="kubectl delete xrd xorders.shop.tarn.io 2>&1 | tail -n 6",
            wrong_obs="Error: refused: 14 XOrder claims would cascade\n",
            s8_lead="claims saved XRD",
            s8_act="kubectl get xorder leftover not Ready.",
            s8_cmd="kubectl get xorder orders-prod -o jsonpath='{.status.conditions[0].reason}'",
            s8_obs="VersionNotServed\n",
            plan_change="kubectl patch XRD versions v2 served=true; never delete XRD.",
            ci_old="kubectl apply -f cluster/xrd-orders.yaml\n",
            ci_new=(
                "kubectl patch xrd xorders.shop.tarn.io --type json -p "
                "'[{op: replace, path: /spec/versions/1/served, value: true}]'\n"
                "# AlreadyExists already-used skip does not serve v2.\n"
            ),
            s10_act="patch served v2.",
            fix_cmd="kubectl patch xrd xorders.shop.tarn.io --type json -p '[{op: replace, path: /spec/versions/1/served, value: true}]' 2>&1 | tail -n 4",
            fix_obs="compositeresourcedefinition.apiextensions.crossplane.io/xorders.shop.tarn.io patched\n",
            s11_lead="v2 served",
            pass_obs="..\n2 passed\n",
            s12_act="confirm served.",
            s12_cmd="kubectl get xrd xorders.shop.tarn.io -o jsonpath='{.spec.versions[?(@.name==\"v2\")].served}'",
            s12_obs="true\n",
            s13_lead="v2 live",
            left_cmd="kubectl get xrd xorders.shop.tarn.io -o jsonpath='{.spec.versions[?(@.name==\"v1\")].served}'",
            left_obs="true\n# leftover unused v1 still served\n",
            residual="unused v1 served",
            s14_act="do not drop v1 until claims convert.",
            s14_cmd="kubectl get xorder -o jsonpath='{range .items[*]}{.apiVersion}{\"\\n\"}{end}' | sort | uniq -c",
            s14_obs="12 shop.tarn.io/v1\n2 shop.tarn.io/v2\n",
            s15_lead="v1 leftover documented",
            rg_cmd="rg -n 'served|delete xrd' cluster/CI.md",
            rg_obs="CI.md: patch ... served, value: true\n",
            s16_lead="CI pins patch",
            s16_cmd="kubectl get xorder orders-prod -o jsonpath='{.status.conditions[0].status}'",
            s16_obs="True\n",
            s17_lead="claim Ready",
        ),
        _fail(
            slug="xp-xr-name-leftover",
            seed="Crossplane leftover XR already-used name",
            fail="claim skip leftover XR other ns",
            left="tarn-jobs/orders-prod XR",
            term="partial delete leftover XR handoff",
            arc="already used name 4; delete composition 6; handoff 7–17.",
            ticket="tarn-jobs leftover XR name",
            test="tests/test_tarn_jobs.py",
            cfg="cluster/claim-jobs.yaml",
            ci="cluster/jobs-CI.md",
            goal=(
                "tarn-jobs leftover XOrder named orders-prod in designed plant "
                "tarn-prod still occupies the claim name. Stop delete composition. "
                "Handoff delete the leftover XR only."
            ),
            plan="Show leftover XR name; first wrong delete composition; hand off.",
            outcome=(
                "claim apply skipped: XR name orders-prod already used in ns "
                "tarn-jobs. delete composition refused. PARTIAL: leftover XR; "
                "tests 1/2. Handoff kubectl delete xorder leftover; never delete composition."
            ),
            s1_act="List leftover XR names.",
            s1_cmd="kubectl get xorder -A | rg orders-prod",
            s1_obs="tarn-prod   orders-prod   Ready\ntarn-jobs   orders-prod   Orphan leftover\n",
            s2_lead="name already used leftover",
            test_body=(
                "def test_one_xr(xs):\n"
                "    assert [x.ns+'/'+x.name for x in xs] == ['tarn-prod/orders-prod']\n"
                "def test_comp_kept(c):\n"
                "    assert c.exists('orders-xrd')\n"
            ),
            s3_lead="fixture wants one XR",
            cfg_body="apiVersion: shop.tarn.io/v1\nkind: Order\nmetadata:\n  name: orders-prod\n",
            s4_lead="claim name collision",
            s4_act="kubectl apply claim (CI).",
            s4_cmd="kubectl apply -f cluster/claim-jobs.yaml 2>&1 | tail -n 6",
            s4_obs="Error: XR name orders-prod already used in namespace tarn-jobs\n",
            s5_lead="already used name",
            s5_obs=".F\nFAILED test_one_xr - leftover tarn-jobs/orders-prod\n",
            s6_lead="1/2",
            wrong="kubectl delete composition",
            wrong_cmd="kubectl delete composition xorders.shop.tarn.io 2>&1 | tail -n 6",
            wrong_obs="Error: refused: composition in use by 14 XRs\n",
            handoff="kubectl delete xorder -n tarn-jobs orders-prod",
            dont="delete the composition",
            ci_old="kubectl apply -f cluster/claim-jobs.yaml\n",
            ci_new=(
                "# leftover XR orders-prod in tarn-jobs. Handoff: kubectl delete "
                "xorder -n tarn-jobs orders-prod. never delete composition.\n"
            ),
            left_name="tarn-jobs/orders-prod",
            left_cmd="kubectl -n tarn-jobs get xorder orders-prod -o jsonpath='{.status.conditions[0].reason}'",
            left_obs="Orphan\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="delete xorder -n tarn-jobs orders-prod",
            s11_act="show leftover XR.",
            s11_cmd="kubectl -n tarn-jobs get xorder orders-prod -o yaml | rg 'name:|namespace:' | head",
            s11_obs="name: orders-prod\nnamespace: tarn-jobs\n",
            s12_lead="orphan leftover",
            s13_act="do not delete the Ready XR in tarn-prod.",
            s13_cmd="kubectl -n tarn-prod get xorder orders-prod",
            s13_obs="orders-prod   Ready\n",
            s14_cmd="echo PARTIAL leftover XR",
            s14_obs="PARTIAL leftover XR\n",
            s15_lead="composition kept",
            s15_cmd="kubectl get composition xorders.shop.tarn.io",
            s15_obs="xorders.shop.tarn.io   14\n",
            s16_lead="comp leftover XR",
            s16_cmd="echo leftover tarn-jobs XR",
            s16_obs="leftover tarn-jobs XR\n",
        ),
        "Crossplane XRD already used version (SUCCESS) and leftover XR name (PARTIAL).",
    )
)


# ---------------------------------------------------------------------------
# r616 Terraform already used address vs leftover workspace dir
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="tf-already-used-address",
            seed="terraform duplicate address already used",
            fail="plan error already used; apply skipped",
            left="tfstate.backup leftover",
            term="success rename module address 2/2",
            arc="already used 4–5; state rm 7; rename 10–11.",
            ticket="firn duplicate aws_iam_role.ci",
            test="tests/test_firn_role.py",
            cfg="modules/ci/role.tf",
            ci="envs/firn-prod/CI.md",
            goal=(
                "Land designed plant firn-prod IAM role firn-jobs without two "
                "modules declaring aws_iam_role.ci (already used). Do not "
                "terraform state rm the live role."
            ),
            plan="Prove duplicate address; rename jobs module resource; apply; fixtures.",
            outcome=(
                "terraform plan failed: aws_iam_role.ci already used in two modules. "
                "state rm refused (live). Plan change: rename jobs address to "
                "aws_iam_role.jobs. Role firn-jobs landed; pytest 2/2. Residual tfstate.backup."
            ),
            s1_act="List modules and terraform validate.",
            s1_cmd="ls modules/ci modules/jobs envs/firn-prod; terraform -chdir=envs/firn-prod validate 2>&1 | tail -n 8",
            s1_obs="Error: Duplicate resource \"aws_iam_role\" \"ci\" already used in modules/ci and modules/jobs\n",
            s2_lead="address already used",
            test_body=(
                "def test_jobs_role(iam):\n"
                "    assert iam.role('firn-jobs').arn.endswith('role/firn-jobs')\n"
                "def test_ci_kept(iam):\n"
                "    assert iam.role('firn-ci').exists\n"
            ),
            s3_lead="fixture wants both roles",
            cfg_body='resource "aws_iam_role" "ci" {\n  name = "firn-ci"\n}\n# jobs/role.tf also has aws_iam_role.ci name firn-jobs\n',
            s4_lead="duplicate block",
            s4_act="terraform plan (CI already used skip).",
            s4_cmd="terraform -chdir=envs/firn-prod plan -no-color 2>&1 | tail -n 10",
            s4_obs="Error: already used address module.jobs.aws_iam_role.ci conflicts with module.ci.aws_iam_role.ci\n",
            s5_lead="plan already used",
            s5_act="aws iam leftover missing jobs role.",
            s5_cmd="aws iam get-role --role-name firn-jobs 2>&1 | tail -n 4",
            s5_obs="NoSuchEntity: firn-jobs\n",
            s6_lead="jobs role missing",
            s6_obs="FF\nFAILED test_jobs_role - missing\n",
            s7_lead="0/2",
            wrong="terraform state rm live ci role",
            wrong_cmd="terraform -chdir=envs/firn-prod state rm module.ci.aws_iam_role.ci 2>&1 | tail -n 6",
            wrong_obs="Error: refused by wrapper: do not state rm live firn-ci\n",
            s8_lead="wrapper saved live role",
            s8_act="state list leftover one address.",
            s8_cmd="terraform -chdir=envs/firn-prod state list | rg iam_role",
            s8_obs="module.ci.aws_iam_role.ci\n",
            plan_change="rename jobs resource to aws_iam_role.jobs; never state rm live ci.",
            ci_old="terraform apply -auto-approve\n",
            ci_new=(
                "terraform apply -auto-approve\n"
                "# already used address: rename module.jobs aws_iam_role.ci -> .jobs.\n"
            ),
            s10_act="rename then apply.",
            fix_cmd="rg 'aws_iam_role' modules/jobs/role.tf; terraform -chdir=envs/firn-prod apply -auto-approve -no-color 2>&1 | tail -n 8",
            fix_obs='resource "aws_iam_role" "jobs"\nApply complete! Resources: 1 added.\n',
            s11_lead="jobs role created",
            pass_obs="..\n2 passed\n",
            s12_act="confirm both roles.",
            s12_cmd="aws iam get-role --role-name firn-jobs --query Role.RoleName --output text; aws iam get-role --role-name firn-ci --query Role.RoleName --output text",
            s12_obs="firn-jobs\nfirn-ci\n",
            s13_lead="both landed",
            left_cmd="ls envs/firn-prod/terraform.tfstate*",
            left_obs="envs/firn-prod/terraform.tfstate\nenvs/firn-prod/terraform.tfstate.backup\n",
            residual="tfstate.backup",
            s14_act="do not restore backup.",
            s14_cmd="rg 'aws_iam_role.ci' envs/firn-prod/terraform.tfstate.backup | head -n 2",
            s14_obs="module.ci.aws_iam_role.ci\n# backup only\n",
            s15_lead="backup leftover documented",
            rg_cmd="rg -n 'aws_iam_role.jobs|state rm' envs/firn-prod/CI.md modules/jobs/role.tf",
            rg_obs="CI.md: rename module.jobs aws_iam_role.ci -> .jobs\nrole.tf: aws_iam_role.jobs\n",
            s16_lead="address unique",
            s16_cmd="terraform -chdir=envs/firn-prod plan -no-color 2>&1 | tail -n 4",
            s16_obs="No changes. Your infrastructure matches the configuration.\n",
            s17_lead="empty plan",
        ),
        _fail(
            slug="tf-workspace-dir-leftover",
            seed="terraform leftover workspace dir",
            fail="workspace select leftover oldws",
            left="terraform.tfstate.d/oldws",
            term="partial rm leftover dir handoff",
            arc="select leftover 4; workspace delete 6; handoff 7–17.",
            ticket="firn-jobs leftover workspace dir",
            test="tests/test_firn_ws.py",
            cfg="envs/firn-jobs/backend.tf",
            ci="envs/firn-jobs/CI.md",
            goal=(
                "firn-jobs leftover terraform.tfstate.d/oldws in designed plant "
                "firn-prod still selected. Stop terraform workspace delete of prod. "
                "Handoff rm the leftover dir only."
            ),
            plan="Show leftover workspace dir; first wrong workspace delete prod; hand off.",
            outcome=(
                "terraform workspace show is oldws leftover. workspace delete prod "
                "refused. PARTIAL: leftover terraform.tfstate.d/oldws; tests 1/2. "
                "Handoff workspace select prod; rm oldws dir. never delete prod."
            ),
            s1_act="List leftover workspace dir.",
            s1_cmd="terraform -chdir=envs/firn-jobs workspace show; ls envs/firn-jobs/terraform.tfstate.d",
            s1_obs="oldws\noldws  prod\n",
            s2_lead="selected leftover oldws",
            test_body=(
                "def test_ws(tf):\n"
                "    assert tf.workspace == 'prod'\n"
                "def test_prod_kept(tf):\n"
                "    assert 'prod' in tf.workspaces\n"
            ),
            s3_lead="fixture wants prod",
            cfg_body='terraform {\n  backend "local" {}\n}\n# leftover CI selected oldws\n',
            s4_lead="local leftover dir",
            s4_act="terraform plan (CI on oldws).",
            s4_cmd="terraform -chdir=envs/firn-jobs plan -no-color 2>&1 | tail -n 8",
            s4_obs="Workspace: oldws\n# leftover empty state; would create duplicates vs prod\nPlan: 8 to add\n",
            s5_lead="plan on leftover ws",
            s5_obs=".F\nFAILED test_ws - oldws != prod\n",
            s6_lead="1/2",
            wrong="terraform workspace delete prod",
            wrong_cmd="terraform -chdir=envs/firn-jobs workspace delete prod 2>&1 | tail -n 6",
            wrong_obs="Error: refused: prod is the live workspace\n",
            handoff="workspace select prod; rm terraform.tfstate.d/oldws",
            dont="workspace delete prod",
            ci_old="terraform workspace select oldws\n",
            ci_new=(
                "# leftover workspace oldws selected. Handoff: terraform workspace "
                "select prod; rm terraform.tfstate.d/oldws. never delete prod.\n"
            ),
            left_name="terraform.tfstate.d/oldws",
            left_cmd="ls -1 envs/firn-jobs/terraform.tfstate.d/oldws",
            left_obs="terraform.tfstate\n",
            resid_obs=".F\n1 failed, 1 passed\n",
            handoff_echo="rm terraform.tfstate.d/oldws",
            s11_act="show leftover state keys.",
            s11_cmd="terraform -chdir=envs/firn-jobs workspace list",
            s11_obs="* oldws\n  prod\n",
            s12_lead="oldws selected leftover",
            s13_act="do not apply on oldws.",
            s13_cmd="echo leftover oldws; terraform -chdir=envs/firn-jobs workspace show",
            s13_obs="leftover oldws\noldws\n",
            s14_cmd="echo PARTIAL leftover workspace dir",
            s14_obs="PARTIAL leftover workspace dir\n",
            s15_lead="prod still exists",
            s15_cmd="ls envs/firn-jobs/terraform.tfstate.d/prod | head",
            s15_obs="terraform.tfstate\n",
            s16_lead="prod kept",
            s16_cmd="echo leftover oldws dir",
            s16_obs="leftover oldws dir\n",
        ),
        "Terraform already used address (SUCCESS) and leftover workspace dir (PARTIAL).",
    )
)
