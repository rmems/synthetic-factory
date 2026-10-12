"""KCL leftover episode builders: the success and handoff episodes of one pair.

Each builder interpolates one plant spec into a fixed step script; every step
is refused when its ``decision_basis`` prefix or text is invalid, and every
record is refused when it carries a banned key or ``sim_or_real: real``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._contract import (
    FAMILY_PREFIX,
    FINDING_USAGE,
    HANDOFF_STEPS,
    SUCCESS_STEPS,
    bind_import_twin,
    refuse_when,
)
from ._steps import Observed, Scene, bash, edit, episode_record, read

_LINT_SUMMARY = "Summary: 3 resources found, 0 errors.\n"
_LINT_BLIND_SPOT = "# kubeconform does not evaluate this dataplane leftover.\n"

__all__ = [
    "build_handoff",
    "build_success",
]


def _values_template_lint(
    spec: Mapping[str, str], scene: Scene, summary: str
) -> list[dict[str, Any]]:
    """Steps 3-5 of both episodes: read values, read the template, kubeconform clean."""

    app, ns = scene.app, scene.ns
    return [
        read(
            3,
            "Observation: live fail matches ticket. Read values.yaml.",
            f"charts/{app}/values.yaml",
            Observed(spec["values_fail"], "Values match the failing live object. Template next."),
        ),
        read(
            4,
            "Observation: values fail-open. Read deployment/related template.",
            f"charts/{app}/templates/deployment.yaml",
            Observed(spec["tpl"], "Template emits the failing field. kubeconform next."),
        ),
        bash(
            5,
            "Observation: template emits fail field. helm template + kubeconform.",
            f"helm template {app} charts/{app} -n {ns} | kubeconform -strict -summary",
            Observed(summary, "Plan clean. Apply --wait."),
        ),
    ]


def _success_triage(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    ns, app, rs, field = scene.ns, scene.app, scene.rs, scene.field
    return [
        bash(
            1,
            f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart {scene.chart} "
            f"({field} leftover). List po.",
            f"kubectl -n {ns} get po,deploy -l app={app}",
            Observed(
                f"pod/{app}-{rs}-a 0/1 CrashLoopBackOff 9\n"
                f"pod/{app}-{rs}-b 0/1 CrashLoopBackOff 9\ndeploy/{app} 0/2\n",
                "0/2. Logs next.",
            ),
        ),
        bash(
            2,
            f"Observation: 9 restarts. Logs and describe ({field} leftover).",
            f"kubectl -n {ns} logs {app}-{rs}-a --tail=12; "
            f"kubectl -n {ns} describe po {app}-{rs}-a | tail -n 24",
            Observed(
                f"{field}={spec['fail_val']}\n{spec['log']}\n",
                "Root cause visible. Read values.",
            ),
        ),
    ]


def _success_wrong_hide(
    spec: Mapping[str, str], scene: Scene, hide: tuple[str, str]
) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    return [
        bash(
            6,
            "Observation: kubeconform 0. helm upgrade --wait current values.",
            f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12",
            Observed(
                "Error: UPGRADE FAILED: timed out waiting for the condition\n"
                f"CrashLoopBackOff {spec['log']}\n",
                "Clean plan, failed apply. First wrong fix next.",
            ),
        ),
        edit(
            7,
            "Observation: --wait failed. Apply the wrong first hide.",
            {
                "path": f"charts/{app}/values.yaml",
                "old": hide[0],
                "new": hide[1],
            },
            Observed(
                f"patched {spec['hide_name']} (wrong knob; {field} still {spec['fail_val']})",
                "Hide is not the contract. Confirm then plan-change.",
            ),
        ),
        bash(
            8,
            "Observation: hide patched. helm upgrade --wait.",
            f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 2m 2>&1 | tail -n 8",
            Observed(
                f'Release "{app}" upgraded. REVISION: 4\nwaiting... done\n',
                "Ready via hide. Wrong terminal. Plan change is the real fix.",
            ),
        ),
    ]


def _success_plan_change(
    spec: Mapping[str, str], scene: Scene, hide_new: str
) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    return [
        edit(
            9,
            f"Reflection: {field} {spec['fix_val']} is the contract. Undo {spec['hide_name']}.",
            {
                "path": f"charts/{app}/values.yaml",
                "old": hide_new,
                "new": spec["values_fix"],
            },
            Observed(f"patched {field} {spec['fix_val']}; hide undone", "Apply without --force."),
        ),
        bash(
            10,
            "Observation: real fix patched. helm upgrade --wait no --force.",
            f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 3m 2>&1 | tail -n 8",
            Observed(
                f'Release "{app}" upgraded. REVISION: 5\nwaiting for 2 pods... done\n',
                "Revision 5 Ready. Confirm live spec.",
            ),
        ),
        bash(
            11,
            "Observation: --wait passed. Confirm the live contract.",
            f"kubectl -n {ns} get deploy,{app} -o yaml | rg '{field}|{spec['fix_val']}' | head",
            Observed(f"{spec['live_ok']}\n", "Contract holds. pytest."),
        ),
    ]


def _success_verify(
    spec: Mapping[str, str], scene: Scene, pytest_lines: str
) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    return [
        bash(
            12,
            "Observation: live contract ok. pytest chart fixtures.",
            f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=short",
            Observed(f"......\n6 passed in 0.32s\n# {pytest_lines}\n", "6/6. Patch CI.md."),
        ),
        edit(
            13,
            "Observation: 6/6. Patch CI.md so the hide cannot return.",
            {
                "path": f"charts/{app}/CI.md",
                "old": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n",
                "new": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n{spec['ci']}\n",
            },
            Observed("patched CI.md", "CI records the contract."),
        ),
        bash(
            14,
            "Observation: CI.md updated. helm history.",
            f"helm -n {ns} history {app} | tail -n 4",
            Observed(
                f"3 superseded {field} {spec['fail_val']}\n"
                f"4 superseded {spec['hide_name']} hide\n"
                f"5 deployed {field} {spec['fix_val']}\n",
                "History shows the hide then the fix.",
            ),
        ),
        bash(
            15,
            "Observation: rev 5 deployed. logs confirm.",
            f"kubectl -n {ns} logs deploy/{app} --tail=3",
            Observed(f"level=info msg=\"peer via {field}={spec['fix_val']}\"\n", "App healthy."),
        ),
        bash(
            16,
            "Observation: logs ok. get po.",
            f"kubectl -n {ns} get po -l app={app}",
            Observed(f"{app}-8a2-a 1/1 Running 0\n{app}-8a2-b 1/1 Running 0\n", "Done."),
        ),
    ]


def _success_hide(spec: Mapping[str, str]) -> tuple[str, str]:
    """``(old, new)`` text of the wrong first hide edit on values.yaml."""

    hide_in_fail = spec["hide_old"] in spec["values_fail"]
    values_hide = (
        spec["values_fail"].replace(spec["hide_old"], spec["hide_new"])
        if hide_in_fail
        else spec["values_fail"] + spec["hide_new"]
    )
    hide_old = spec["hide_old"] if hide_in_fail else spec["values_fail"]
    hide_new = spec["hide_new"] if hide_in_fail else values_hide
    return hide_old, hide_new


def build_success(
    spec: Mapping[str, str],
    *,
    round_n: int,
    mill_id: str,
    plant_id: str,
) -> dict[str, Any]:
    scene = Scene(
        ns=spec["plant"], app=spec["app"], chart=spec["chart"], rs=spec["rs"], field=spec["field"]
    )
    ns, app, field = scene.ns, scene.app, scene.field
    eid = f"{FAMILY_PREFIX}-r{round_n}-{spec['slug']}"
    hide = _success_hide(spec)
    pytest_lines = "\n# ".join(spec["pytest_ok"].splitlines())
    steps = [
        *_success_triage(spec, scene),
        *_values_template_lint(spec, scene, _LINT_SUMMARY + _LINT_BLIND_SPOT),
        *_success_wrong_hide(spec, scene, hide),
        *_success_plan_change(spec, scene, hide[1]),
        *_success_verify(spec, scene, pytest_lines),
    ]
    refuse_when(len(steps) != SUCCESS_STEPS, FINDING_USAGE, f"{eid} want {SUCCESS_STEPS} steps")
    return episode_record(
        {
            "id": eid,
            "goal": (
                f"{app} in designed plant {ns} is CrashLoopBackOff after leftover {field}: "
                f"{spec['fail_val']}. {spec['seed']}. Do not toggle {spec['hide_name']} as a hide."
            ),
            "plan": f"Read {field} vs live, template, apply, then {spec['fix_val']}.",
            "steps": steps,
            "outcome": (
                f"kubeconform passed {spec['fail_val']}. helm --wait leftover. "
                f"{spec['hide_name']} hid nothing. Plan change: {field} {spec['fix_val']}. "
                "Rev 5: 2/2, 6/6."
            ),
            "reward": {
                "success": True,
                "apply_fails": 2,
                "plan_changes": 1,
                "tests_passed": 6,
                "pods_ready": 2,
                "cost_steps": SUCCESS_STEPS,
            },
        },
        round_n=round_n,
        mill_id=mill_id,
        plant_id=plant_id,
    )


def _handoff_triage(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    ns, app, chart, rs, field = scene.ns, scene.app, scene.chart, scene.rs, scene.field
    return [
        bash(
            1,
            f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart {chart} leftover. "
            "List po, chart.",
            f"kubectl -n {ns} get po,deploy -l app={app}; helm -n {ns} list | rg {app}",
            Observed(
                f"pod/{app}-{rs}-a 0/1 CrashLoopBackOff 10\n"
                f"pod/{app}-{rs}-b 0/1 CrashLoopBackOff 10\n"
                f"deploy/{app} 0/2\n{app} {app}-{chart} deployed\n"
                f"{field}={spec['fail_val']}\n",
                "0/2 crashloop. Describe next.",
            ),
        ),
        bash(
            2,
            "Observation: crashloop. Logs and describe.",
            f"kubectl -n {ns} logs {app}-{rs}-a --tail=16; "
            f"kubectl -n {ns} describe po {app}-{rs}-a | tail -n 20",
            Observed(f"{spec['log']}\n", "Root cause visible. Read values."),
        ),
    ]


def _handoff_forced_apply(
    spec: Mapping[str, str], scene: Scene, values_hide: str
) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    return [
        bash(
            6,
            "Observation: kubeconform 0. helm upgrade --wait current values.",
            f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12",
            Observed(
                "Error: UPGRADE FAILED: timed out waiting for the condition\n"
                f"CrashLoopBackOff {field} leftover\n",
                "Clean plan, failed apply. Ticket says helm --force.",
            ),
        ),
        edit(
            7,
            "Observation: --wait failed. Apply the wrong first hide and --force.",
            {
                "path": f"charts/{app}/values.yaml",
                "old": spec["values_fail"],
                "new": values_hide,
            },
            Observed(
                "patched the hide; applying with --force as the ticket asked",
                "--force is the wrong applicator.",
            ),
        ),
        bash(
            8,
            "Observation: hide patched. helm upgrade --force --wait.",
            f"helm upgrade {app} charts/{app} -n {ns} --force --wait --timeout 90s 2>&1 | tail -n 16",
            Observed(
                "upgrade.go:401: --force used, deleting/recreating resources\n"
                "Error: UPGRADE FAILED: timed out waiting for the condition\n"
                f"pod/{app}-5e1-a 1/1 Running {field}={spec['fix_val']}\n"
                f"pod/{app}-5e1-b 0/1 CrashLoopBackOff {field}={spec['fail_val']}  # leftover n2\n",
                "--force mixed replicas. Do not --force again.",
            ),
        ),
    ]


def _handoff_forbid_force(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    node = ns.split("-")[0]
    return [
        edit(
            9,
            f"Reflection: leftover is n2 {field} {spec['fail_val']}. "
            f"Keep git {spec['fix_val']}; do not --force.",
            {
                "path": f"charts/{app}/CI.md",
                "old": f"helm upgrade --install {app} charts/{app} -n {ns} --wait --force\n",
                "new": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n"
                "# Never --force: three-way keeps live leftovers.\n",
            },
            Observed(
                "patched CI.md forbid --force; git now holds the real fix",
                "Git is tight. Cluster mixed.",
            ),
        ),
        bash(
            10,
            "Observation: CI forbids --force. helm upgrade --wait no --force.",
            f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 2m 2>&1 | tail -n 12",
            Observed(
                "Error: UPGRADE FAILED: timed out waiting for the condition\n"
                f"deploy spec matches git; pod/{app}-5e1-b leftover on {node}-n2\n",
                "Helm three-way did not replace the leftover replica.",
            ),
        ),
    ]


def _handoff_leftover_n2(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    node = ns.split("-")[0]
    return [
        bash(
            11,
            "Observation: mixed live vs git. Diff pods.",
            f"kubectl -n {ns} get po {app}-5e1-a {app}-5e1-b -o wide; echo '---MIX---'",
            Observed(
                f"{app}-5e1-a {field}={spec['fix_val']}\n"
                f"{app}-5e1-b {field}={spec['fail_val']}\n"
                "---MIX---\n"
                f"{app}-5e1-a node/{node}-n1\n"
                f"{app}-5e1-b node/{node}-n2\n",
                "Git is correct. leftover is n2.",
            ),
        ),
        bash(
            12,
            "Observation: leftover n2. kubectl apply --server-side helm manifest.",
            f"helm -n {ns} get manifest {app} | kubectl apply --server-side "
            f"--force-conflicts -n {ns} -f - | tail -n 8",
            Observed(
                f"deployment.apps/{app} serverside-applied\n"
                f"# pod/{app}-5e1-b still old hash; SSA does not delete leftover RS\n",
                "SSA updated spec. leftover pod remains.",
            ),
        ),
        bash(
            13,
            "Observation: SSA spec good. rollout status.",
            f"kubectl -n {ns} rollout status deploy/{app} --timeout=45s; "
            f"kubectl -n {ns} get po -l app={app}",
            Observed(
                f"error: timed out waiting for the condition\n"
                f"{app}-5e1-a 1/1 Running 0\n{app}-5e1-b leftover\n",
                "1/2 Ready. leftover is the teaching residual.",
            ),
        ),
    ]


def _handoff_partial(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    ns, app, field = scene.ns, scene.app, scene.field
    node = ns.split("-")[0]
    return [
        bash(
            14,
            "Observation: 1/2 Ready. pytest + handoff; do not --force n2.",
            f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=short",
            Observed(
                f".F.\n2 passed, 1 failed in 0.30s\n# {spec['tmpl_test']} PASSED\n"
                f"# {spec['pytest_fail']}\n# test_no_force PASSED\n",
                "Tests 2/3. Handoff leftover to platform.",
            ),
        ),
        edit(
            15,
            "Observation: tests 2/3. Write HANDOFF.md.",
            {
                "path": f"charts/{app}/HANDOFF.md",
                "old": "",
                "new": spec["handoff"] + "\n",
            },
            Observed("wrote HANDOFF.md", "Handoff recorded."),
        ),
        bash(
            16,
            "Observation: HANDOFF.md written. kubectl get snapshot; do not delete leftover pod.",
            f"kubectl -n {ns} get po -l app={app} -o wide",
            Observed(
                f"{app}-5e1-a 1/1 Running node/{node}-n1\n"
                f"{app}-5e1-b leftover node/{node}-n2\n",
                "n2 leftover. Do not steal by deleting.",
            ),
        ),
        bash(
            17,
            "Observation: mixed nodes. helm get values as evidence git is fixed.",
            f"helm -n {ns} get values {app}",
            Observed(f"{field}: {spec['fix_val']}\n", "Git is the contract. live leftover is n2."),
        ),
        bash(
            18,
            "Observation: git fixed. get po 1/2 as the residual.",
            f"kubectl -n {ns} get po -l app={app}",
            Observed(
                f"{app}-5e1-a 1/1 Running\n{app}-5e1-b leftover\n",
                "PARTIAL. Stop. Handoff leftover RS.",
            ),
        ),
    ]


def _handoff_steps(spec: Mapping[str, str], scene: Scene) -> list[dict[str, Any]]:
    values_hide = spec["values_fail"] + spec["hide_new"]
    return [
        *_handoff_triage(spec, scene),
        *_values_template_lint(spec, scene, _LINT_SUMMARY),
        *_handoff_forced_apply(spec, scene, values_hide),
        *_handoff_forbid_force(spec, scene),
        *_handoff_leftover_n2(spec, scene),
        *_handoff_partial(spec, scene),
    ]


def build_handoff(
    spec: Mapping[str, str],
    *,
    round_n: int,
    mill_id: str,
    plant_id: str,
) -> dict[str, Any]:
    scene = Scene(
        ns=spec["plant"],
        app=spec["app"].replace("-api", "-svc"),
        chart=spec["chart"],
        rs=spec["rs"],
        field=spec["field"],
    )
    ns, app, field = scene.ns, scene.app, scene.field
    eid = f"{FAMILY_PREFIX}-r{round_n}-{spec['slug']}-n2-handoff"
    steps = _handoff_steps(spec, scene)
    refuse_when(len(steps) != HANDOFF_STEPS, FINDING_USAGE, f"{eid} want {HANDOFF_STEPS} steps")
    return episode_record(
        {
            "id": eid,
            "goal": f"{app} in designed plant {ns} leftover n2 still {spec['n2']}. Do not --force.",
            "plan": f"Pin {field} {spec['fix_val']} without --force; hand off n2 leftover.",
            "steps": steps,
            "outcome": (
                f"kubeconform passed. --wait refused. --force mixed: n1 {spec['fix_val']} "
                f"Running, n2 {spec['fail_val']} leftover. PARTIAL. Handoff {field} leftover."
            ),
            "reward": {
                "success": False,
                "apply_fails": 3,
                "plan_changes": 1,
                "tests_passed": 2,
                "tests_failed": 1,
                "pods_ready": 1,
                "handoff": 1,
                "cost_steps": HANDOFF_STEPS,
            },
        },
        round_n=round_n,
        mill_id=mill_id,
        plant_id=plant_id,
    )


bind_import_twin(__name__)
