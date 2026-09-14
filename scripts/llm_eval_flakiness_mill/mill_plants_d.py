"""Unique eval-flakiness plants r637–r644. Not r613–r628 clones or leftover catalogs."""

from mill_plants_c import OK, BAD

MORE = []


# ---------------------------------------------------------------------------
# r637 tau-bench pass^k vs pass@1 / BFCL AST vs executable
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="taubench-passk-vs-p1",
            seed=(
                "tau-bench pass@1 0.72; pass^4 (all four trials) 0.19. pass@4 any-of-k "
                "rejected. Publish pass^k; fail if <0.50."
            ),
            avoided=(
                "r617 Wilson pass@1 n=7; r678 pass@k aliased to pass (pass@1). "
                "This is tau-bench pass^k (all k trials) vs pass@1"
            ),
            dump="pass@1 0.72, pass^4 0.19, and any-of-4",
            first_apply="report pass@4 any-of-k",
            plan="Publish pass@4=0.91 so any single lucky trial still counts.",
            plan_change="publish pass^k; fail if pass^k<0.50",
            goal=(
                "lantern-eval publishes tau-bench pass@1=0.72 while pass^4 (success on all "
                "four trials) is 0.19. Gate on pass^k. Do not swap in pass@k. "
                "tests/test_tau_pk.py is the gate."
            ),
            outcome=(
                "pass@1 0.72 hid pass^4 0.19. pass@4 any-of-k was 0.91. Plan change: pass^k "
                "gate. Tests 1/1 + 8/8. Residual: src/tau_dash.py still pass@1."
            ),
            rg="pass\\^k|pass@1|tau-bench|pass@4|all four trials",
            rg_obs=(
                "TICKET.md: pass@1 0.72; pass^4 0.19 unused\n"
                "tests/test_tau_pk.py: def test_passk_must_gate\n"
                "src/tau_pk.py: acc = pass_at_1(trials)\n"
                "goldens/tau.jsonl: 4 trials per task, 1 lucky"
            ),
            test="tests/test_tau_pk.py",
            test_name="passk-must-gate",
            test_body=(
                "def test_passk_must_gate():\n"
                "    rep = report_tau(TRIALS, k=4)\n"
                "    assert rep['pass1'] == pytest.approx(0.72, abs=0.02)\n"
                "    assert rep['passk'] == pytest.approx(0.19, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'pass_at_k' not in rep\n"
            ),
            gate_want="passk 0.19 and gate fail",
            fail_obs=(
                "FAILED tests/test_tau_pk.py::test_passk_must_gate"
                " - AssertionError: passk missing; pass1=0.72 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="pass@1 only 0.72",
            src="src/tau_pk.py",
            src_body=(
                "def report_tau(trials, k=4):\n"
                "    p1 = pass_at_1(trials)\n"
                "    return {'pass1': p1, 'gate': 'pass' if p1 >= 0.70 else 'fail'}\n"
            ),
            obs5="pass@1 0.72; one lucky trial per task",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('pass1', 0.72, 'pass_at_4', 0.91, 'pass_hat_4', 0.19)\n"
                "PY"
            ),
            stats_obs="pass1 0.72 pass_at_4 0.91 pass_hat_4 0.19",
            wrong_old="    p1 = pass_at_1(trials)\n    return {'pass1': p1, 'gate': 'pass' if p1 >= 0.70 else 'fail'}",
            wrong_new=(
                "    p1 = pass_at_1(trials)\n"
                "    pak = pass_at_k(trials, k)\n"
                "    return {'pass1': p1, 'pass_at_k': pak, 'gate': 'pass' if pak >= 0.70 else 'fail'}"
            ),
            wrong_label="pass-at-k-any",
            wrong_still="pass@4 0.91 still passes",
            still_fail=(
                "FAILED tests/test_tau_pk.py::test_passk_must_gate"
                " - AssertionError: pass_at_k=0.91; passk missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.tau_hatk import pass_at_1, pass_hat_k\n"
                "\n"
                "def report_tau(trials, k=4):\n"
                "    p1 = pass_at_1(trials)\n"
                "    pk = pass_hat_k(trials, k)\n"
                "    gate = 'pass' if pk >= 0.50 else 'fail'\n"
                "    return {'pass1': p1, 'passk': pk, 'gate': gate}\n"
            ),
            rewrite_obs="pass^k (all k) is the gate",
            helper="src/tau_hatk.py",
            fix_helper=(
                "def pass_at_1(trials):\n"
                "    return 0.72\n"
                "\n"
                "def pass_hat_k(trials, k):\n"
                "    return 0.19\n"
            ),
            helper_obs="pass_hat_k locked 0.19",
            test2="tests/test_tau_pk_second.py",
            test2_body=(
                "def test_retail_split_passk():\n"
                "    rep = report_tau(RETAIL, k=4)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['passk'] < 0.50\n"
            ),
            residual="src/tau_dash.py still pass@1",
            residual_path="src/tau_dash.py",
            residual_pat="pass_at_1|passk",
            residual_obs="src/tau_dash.py: acc = pass_at_1(trials)  # leftover\n",
            confirm="passk key in report",
            final_obs="    return {'pass1': p1, 'passk': pk, 'gate': gate}\n",
        ),
        BAD(
            slug="bfcl-ast-vs-exec",
            seed=(
                "BFCL AST match 0.90; live executable 0.33 from side-effect mismatch. "
                "Pin-AST rejected. Require executable success. Nightly still AST."
            ),
            avoided=(
                "r02 jsoncorrect additionalProperties; r619 promptfoo exact vs rubric. "
                "This is BFCL AST-match vs live executable"
            ),
            dump="AST 0.90, executable 0.33, and side-effect mismatch",
            first_apply="pin AST-only matching",
            plan="Pin AST match so live side effects cannot fail CI.",
            plan_change="require executable success; fail if exec<0.70",
            goal=(
                "lantern-eval publishes BFCL 0.90 from AST match while live executable success "
                "is 0.33. Require exec. Do not pin AST. tests/test_bfcl.py is the gate."
            ),
            outcome=(
                "AST 0.90 hid exec 0.33. Pinning AST kept 0.90. Plan change: executable gate. "
                "Gate 1/1. Partial: nightly src/nightly_bfcl.py still AST (xfail)."
            ),
            rg="bfcl|ast.match|executable|side-effect|live exec",
            rg_obs=(
                "TICKET.md: AST 0.90; exec 0.33 unused\n"
                "tests/test_bfcl.py: def test_exec_must_gate\n"
                "src/bfcl.py: acc = ast_match(calls, gold)\n"
                "goldens/bfcl.jsonl: same AST, wrong DB write"
            ),
            test="tests/test_bfcl.py",
            test_name="exec-must-gate",
            test_body=(
                "def test_exec_must_gate():\n"
                "    rep = report_bfcl(CALLS, GOLD)\n"
                "    assert rep['ast'] == pytest.approx(0.90, abs=0.01)\n"
                "    assert rep['exec'] == pytest.approx(0.33, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'pinned' not in rep\n"
            ),
            gate_want="exec 0.33 and gate fail",
            fail_obs=(
                "FAILED tests/test_bfcl.py::test_exec_must_gate"
                " - AssertionError: exec missing; ast=0.90 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="AST-only 0.90",
            src="src/bfcl.py",
            src_body=(
                "def report_bfcl(calls, gold):\n"
                "    ast = ast_match(calls, gold)\n"
                "    return {'ast': ast, 'gate': 'pass' if ast >= 0.70 else 'fail'}\n"
            ),
            obs5="AST 0.90; DB write side-effect wrong",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('ast', 0.90, 'exec', 0.33)\n"
                "PY"
            ),
            stats_obs="ast 0.90 exec 0.33",
            wrong_old="    ast = ast_match(calls, gold)\n    return {'ast': ast, 'gate': 'pass' if ast >= 0.70 else 'fail'}",
            wrong_new="    ast = ast_match(calls, gold)\n    return {'ast': ast, 'pinned': True, 'gate': 'pass' if ast >= 0.70 else 'fail'}",
            wrong_label="pin-ast-only",
            wrong_still="pinned AST still 0.90",
            still_fail=(
                "FAILED tests/test_bfcl.py::test_exec_must_gate"
                " - AssertionError: pinned=True; exec missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.bfcl_exec import ast_match, exec_ok\n"
                "\n"
                "def report_bfcl(calls, gold):\n"
                "    ast = ast_match(calls, gold)\n"
                "    ex = exec_ok(calls, gold)\n"
                "    gate = 'pass' if ex >= 0.70 else 'fail'\n"
                "    return {'ast': ast, 'exec': ex, 'gate': gate}\n"
            ),
            rewrite_obs="executable success is the gate",
            helper="src/bfcl_exec.py",
            fix_helper=(
                "def ast_match(calls, gold):\n"
                "    return 0.90\n"
                "\n"
                "def exec_ok(calls, gold):\n"
                "    return 0.33\n"
            ),
            helper_obs="exec_ok locked 0.33",
            suite_fail=(
                "FAILED tests/test_nightly_bfcl.py::test_nightly_uses_exec"
                " - AssertionError: nightly gate=pass ast=0.90\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_bfcl.py",
            nightly_test="tests/test_nightly_bfcl.py",
            nightly_body=(
                "def nightly_report(calls, gold):\n"
                "    ast = ast_match(calls, gold)\n"
                "    return {'ast': ast, 'gate': 'pass' if ast >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_exec():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_bfcl.py still AST", strict=False)\n'
                "def test_nightly_uses_exec():"
            ),
            handoff="nightly AST-only BFCL",
            leftover_obs="    return {'ast': ast, 'gate': 'pass' if ast >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r638 lost-in-the-middle needle vs mean / EWMA vs Shewhart 3-sigma
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="lost-middle-needle",
            seed=(
                "mean judge 0.81; needle at 50% context 0.22; edges 0.88. Average first+last "
                "rejected. Fail if mid-context needle<0.50."
            ),
            avoided=(
                "r627 pairwise A-first vs B-first max; r244 arena-swap-not-averaged. "
                "This is lost-in-the-middle evidence position vs mean judge"
            ),
            dump="mid-context needle 0.22, edge 0.88, and mean 0.81",
            first_apply="average first and last context only",
            plan="Average first+last 0.88 so the middle needle cannot drag the score.",
            plan_change="fail if mid-context needle<0.50",
            goal=(
                "lantern-eval publishes mean judge 0.81 while a needle at 50% context scores "
                "0.22. Fail if mid needle<0.50. Do not average first+last. "
                "tests/test_needle.py is the gate."
            ),
            outcome=(
                "Mean 0.81 hid mid-context 0.22. First+last average 0.88 still passed. Plan "
                "change: mid-needle gate. Tests 1/1 + 8/8. Residual: src/ctx_dash.py still "
                "means over positions."
            ),
            rg="lost-in-the-middle|needle|mid.context|50% context|edge",
            rg_obs=(
                "TICKET.md: mean 0.81; needle@50% 0.22\n"
                "tests/test_needle.py: def test_mid_needle_must_fail\n"
                "src/needle.py: score = mean(all_positions)\n"
                "goldens/needle.jsonl: evidence at 0/50/100%"
            ),
            test="tests/test_needle.py",
            test_name="mid-needle-must-fail",
            test_body=(
                "def test_mid_needle_must_fail():\n"
                "    rep = report_needle(POS)\n"
                "    assert rep['mean'] == pytest.approx(0.81, abs=0.02)\n"
                "    assert rep['mid'] == pytest.approx(0.22, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'edge_mean' not in rep\n"
            ),
            gate_want="mid 0.22 and gate fail",
            fail_obs=(
                "FAILED tests/test_needle.py::test_mid_needle_must_fail"
                " - AssertionError: mid missing; mean=0.81 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="mean-over-positions 0.81",
            src="src/needle.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_needle(pos):\n"
                "    mu = mean(pos.values())\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            obs5="mean 0.81; 50% position 0.22",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('edge0', 0.88, 'mid50', 0.22, 'edge100', 0.88, 'mean', 0.66)\n"
                "PY"
            ),
            stats_obs="edge0 0.88 mid50 0.22 edge100 0.88 mean 0.66",
            wrong_old="    mu = mean(pos.values())\n    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}",
            wrong_new=(
                "    edge = mean([pos['p0'], pos['p100']])\n"
                "    return {'mean': edge, 'edge_mean': edge, 'gate': 'pass' if edge >= 0.70 else 'fail'}"
            ),
            wrong_label="first-last-average",
            wrong_still="edge_mean 0.88 still passes",
            still_fail=(
                "FAILED tests/test_needle.py::test_mid_needle_must_fail"
                " - AssertionError: edge_mean=0.88; mid missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.needle_pos import mid_of\n"
                "\n"
                "def report_needle(pos):\n"
                "    mu = mean(pos.values())\n"
                "    mid = mid_of(pos)\n"
                "    gate = 'pass' if mid >= 0.50 else 'fail'\n"
                "    return {'mean': mu, 'mid': mid, 'gate': gate}\n"
            ),
            rewrite_obs="mid-context needle is the gate",
            helper="src/needle_pos.py",
            fix_helper=(
                "def mid_of(pos):\n"
                "    return float(pos.get('p50', pos.get('mid', 0.22)))\n"
            ),
            helper_obs="mid_of reads p50",
            test2="tests/test_needle_second.py",
            test2_body=(
                "def test_long_context_mid():\n"
                "    rep = report_needle(LONG_POS)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['mid'] < 0.50\n"
            ),
            residual="src/ctx_dash.py still means over positions",
            residual_path="src/ctx_dash.py",
            residual_pat="mean\\(all_positions\\)|mid",
            residual_obs="src/ctx_dash.py: score = mean(all_positions)  # leftover\n",
            confirm="mid key in report",
            final_obs="    return {'mean': mu, 'mid': mid, 'gate': gate}\n",
        ),
        BAD(
            slug="ewma-vs-shewhart",
            seed=(
                "0.04 persistent drop for 12 nights; Shewhart 3-sigma still in-control; "
                "EWMA lambda=0.2 signals. Widen-to-4-sigma rejected. Nightly still Shewhart."
            ),
            avoided=(
                "r613 bootstrap CI vs point; r630 CUSUM early-stop. "
                "This is EWMA small-drift vs Shewhart 3-sigma"
            ),
            dump="EWMA signal, 12-night 0.04 drop, and Shewhart 3s",
            first_apply="widen Shewhart to 4-sigma",
            plan="Move Shewhart to 4-sigma so the 0.04 drift stays in-control.",
            plan_change="EWMA lambda=0.2; fail if EWMA signals",
            goal=(
                "lantern-eval stays green on Shewhart 3-sigma while a 0.04 drop lasts 12 nights "
                "and EWMA lambda=0.2 signals. Fail on EWMA. Do not widen Shewhart. "
                "tests/test_ewma.py is the gate."
            ),
            outcome=(
                "Shewhart 3s hid a 12-night 0.04 drift. 4-sigma still in-control. Plan change: "
                "EWMA gate. Gate 1/1. Partial: nightly src/nightly_ewma.py still Shewhart "
                "(xfail)."
            ),
            rg="ewma|shewhart|3-sigma|lambda=0.2|small.drift",
            rg_obs=(
                "TICKET.md: 12 nights -0.04; Shewhart in-control\n"
                "tests/test_ewma.py: def test_ewma_must_signal\n"
                "src/ewma.py: gate = abs(x-mu) < 3*sd\n"
                "goldens/nights.jsonl: 12 consecutive 0.04 drops"
            ),
            test="tests/test_ewma.py",
            test_name="ewma-must-signal",
            test_body=(
                "def test_ewma_must_signal():\n"
                "    rep = report_ewma(NIGHTS)\n"
                "    assert rep['shewhart'] == 'in_control'\n"
                "    assert rep['ewma_signal'] is True\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'k4' not in rep\n"
            ),
            gate_want="ewma_signal true and gate fail",
            fail_obs=(
                "FAILED tests/test_ewma.py::test_ewma_must_signal"
                " - AssertionError: ewma missing; shewhart in_control gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="Shewhart 3s in-control",
            src="src/ewma.py",
            src_body=(
                "def report_ewma(nights):\n"
                "    return {'shewhart': 'in_control', 'gate': 'pass'}\n"
            ),
            obs5="12 nights -0.04 still inside 3s",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('drop', 0.04, 'n', 12, 'shewhart', 'in_control', 'ewma_z', 3.1)\n"
                "PY"
            ),
            stats_obs="drop 0.04 n 12 shewhart in_control ewma_z 3.1",
            wrong_old="    return {'shewhart': 'in_control', 'gate': 'pass'}",
            wrong_new="    return {'shewhart': 'in_control', 'k4': 4.0, 'gate': 'pass'}",
            wrong_label="shewhart-4s",
            wrong_still="4-sigma still in-control",
            still_fail=(
                "FAILED tests/test_ewma.py::test_ewma_must_signal"
                " - AssertionError: k4=4.0; ewma missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.ewma_stat import ewma_signal\n"
                "\n"
                "def report_ewma(nights):\n"
                "    sig = ewma_signal(nights, lam=0.2)\n"
                "    gate = 'fail' if sig else 'pass'\n"
                "    return {'shewhart': 'in_control', 'ewma_signal': sig, 'gate': gate}\n"
            ),
            rewrite_obs="EWMA lambda=0.2 is the gate",
            helper="src/ewma_stat.py",
            fix_helper=(
                "def ewma_signal(nights, lam=0.2):\n"
                "    return True\n"
            ),
            helper_obs="ewma_signal locked True",
            suite_fail=(
                "FAILED tests/test_nightly_ewma.py::test_nightly_uses_ewma"
                " - AssertionError: nightly gate=pass shewhart\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_ewma.py",
            nightly_test="tests/test_nightly_ewma.py",
            nightly_body=(
                "def nightly_report(nights):\n"
                "    return {'shewhart': 'in_control', 'gate': 'pass'}\n"
            ),
            xfail_old="def test_nightly_uses_ewma():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_ewma.py still Shewhart", strict=False)\n'
                "def test_nightly_uses_ewma():"
            ),
            handoff="nightly Shewhart-only gate",
            leftover_obs="    return {'shewhart': 'in_control', 'gate': 'pass'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r639 GAIA per-level vs overall / TruthfulQA MC1 vs MC2
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="gaia-l3-vs-overall",
            seed=(
                "overall GAIA 0.74 (mostly L1); level-3 0.18. Drop-L3 rejected. Fail if any "
                "level<0.40; publish per-level."
            ),
            avoided=(
                "r620 difficulty-sorted head(50); r623 micro-F1 hiding CL-12. "
                "This is GAIA level-3 vs overall mix"
            ),
            dump="GAIA overall 0.74, L3 0.18, and L1 mix",
            first_apply="drop GAIA L3 as out of scope",
            plan="Drop L3 so overall 0.81 on L1+L2 still ships.",
            plan_change="fail if any level<0.40; publish per-level",
            goal=(
                "lantern-eval publishes GAIA 0.74 overall while level-3 is 0.18. Fail if any "
                "level<0.40. Do not drop L3. tests/test_gaia_l3.py is the gate."
            ),
            outcome=(
                "Overall 0.74 hid L3 0.18. Dropping L3 raised 0.81. Plan change: per-level "
                "min. Tests 1/1 + 8/8. Residual: src/gaia_dash.py still overall."
            ),
            rg="gaia|level-3|per-level|L1 mix|overall GAIA",
            rg_obs=(
                "TICKET.md: GAIA 0.74 overall; L3 0.18 unused\n"
                "tests/test_gaia_l3.py: def test_l3_must_fail\n"
                "src/gaia_l3.py: acc = overall(rows)\n"
                "goldens/gaia.jsonl: 40 L1, 8 L3"
            ),
            test="tests/test_gaia_l3.py",
            test_name="l3-must-fail",
            test_body=(
                "def test_l3_must_fail():\n"
                "    rep = report_gaia(ROWS)\n"
                "    assert rep['overall'] == pytest.approx(0.74, abs=0.02)\n"
                "    assert rep['l3'] == pytest.approx(0.18, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'dropped_l3' not in rep\n"
            ),
            gate_want="l3 0.18 and gate fail",
            fail_obs=(
                "FAILED tests/test_gaia_l3.py::test_l3_must_fail"
                " - AssertionError: l3 missing; overall=0.74 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="overall-only 0.74",
            src="src/gaia_l3.py",
            src_body=(
                "def report_gaia(rows):\n"
                "    acc = overall(rows)\n"
                "    return {'overall': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            obs5="overall 0.74; 8 L3 mostly fail",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('overall', 0.74, 'l1', 0.86, 'l2', 0.61, 'l3', 0.18, 'no_l3', 0.81)\n"
                "PY"
            ),
            stats_obs="overall 0.74 l1 0.86 l2 0.61 l3 0.18 no_l3 0.81",
            wrong_old="    acc = overall(rows)\n    return {'overall': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}",
            wrong_new=(
                "    keep = [r for r in rows if r['level'] != 3]\n"
                "    acc = overall(keep)\n"
                "    return {'overall': acc, 'dropped_l3': True, 'gate': 'pass' if acc >= 0.70 else 'fail'}"
            ),
            wrong_label="drop-l3",
            wrong_still="no-L3 0.81 still passes",
            still_fail=(
                "FAILED tests/test_gaia_l3.py::test_l3_must_fail"
                " - AssertionError: dropped_l3=True; l3 missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.gaia_levels import overall, by_level\n"
                "\n"
                "def report_gaia(rows):\n"
                "    ovr = overall(rows)\n"
                "    lv = by_level(rows)\n"
                "    gate = 'fail' if min(lv.values()) < 0.40 else 'pass'\n"
                "    return {'overall': ovr, 'l3': lv[3], 'levels': lv, 'gate': gate}\n"
            ),
            rewrite_obs="per-level min is the gate",
            helper="src/gaia_levels.py",
            fix_helper=(
                "def overall(rows):\n"
                "    return 0.74\n"
                "\n"
                "def by_level(rows):\n"
                "    return {1: 0.86, 2: 0.61, 3: 0.18}\n"
            ),
            helper_obs="by_level L3=0.18",
            test2="tests/test_gaia_l3_second.py",
            test2_body=(
                "def test_l2_also_reported():\n"
                "    rep = report_gaia(ROWS)\n"
                "    assert 2 in rep['levels']\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            residual="src/gaia_dash.py still overall",
            residual_path="src/gaia_dash.py",
            residual_pat="overall\\(rows\\)|l3",
            residual_obs="src/gaia_dash.py: acc = overall(rows)  # leftover\n",
            confirm="l3 and levels keys",
            final_obs="    return {'overall': ovr, 'l3': lv[3], 'levels': lv, 'gate': gate}\n",
        ),
        BAD(
            slug="tqa-mc1-vs-mc2",
            seed=(
                "TruthfulQA MC2 0.81 (partial credit); MC1 0.39 (best-of). Generation-exact "
                "rejected. Gate on MC1. Nightly still MC2."
            ),
            avoided=(
                "r616 Kendall GEval vs RAGAS; r634 FActScore atomic vs overall. "
                "This is TruthfulQA MC1 best-of vs MC2 partial credit"
            ),
            dump="MC2 0.81, MC1 0.39, and generation-exact",
            first_apply="substitute generation exact for MC1",
            plan="Publish generation-exact 0.70 as a stand-in for MC1.",
            plan_change="gate on MC1; publish MC1 and MC2",
            goal=(
                "lantern-eval publishes TruthfulQA 0.81 from MC2 while MC1 is 0.39. Gate on "
                "MC1. Do not substitute generation-exact. tests/test_tqa.py is the gate."
            ),
            outcome=(
                "MC2 0.81 hid MC1 0.39. Generation-exact 0.70 still passed. Plan change: MC1 "
                "gate. Gate 1/1. Partial: nightly src/nightly_tqa.py still MC2 (xfail)."
            ),
            rg="truthfulqa|mc1|mc2|best-of|partial credit",
            rg_obs=(
                "TICKET.md: MC2 0.81; MC1 0.39 unused\n"
                "tests/test_tqa.py: def test_mc1_must_gate\n"
                "src/tqa.py: acc = mc2(rows)\n"
                "goldens/tqa.jsonl: partial credit on hedging"
            ),
            test="tests/test_tqa.py",
            test_name="mc1-must-gate",
            test_body=(
                "def test_mc1_must_gate():\n"
                "    rep = report_tqa(ROWS)\n"
                "    assert rep['mc2'] == pytest.approx(0.81, abs=0.01)\n"
                "    assert rep['mc1'] == pytest.approx(0.39, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'gen_exact' not in rep\n"
            ),
            gate_want="mc1 0.39 and gate fail",
            fail_obs=(
                "FAILED tests/test_tqa.py::test_mc1_must_gate"
                " - AssertionError: mc1 missing; mc2=0.81 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="MC2-only 0.81",
            src="src/tqa.py",
            src_body=(
                "def report_tqa(rows):\n"
                "    acc = mc2(rows)\n"
                "    return {'mc2': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            obs5="MC2 0.81; hedging gets partial credit",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('mc2', 0.81, 'mc1', 0.39, 'gen_exact', 0.70)\n"
                "PY"
            ),
            stats_obs="mc2 0.81 mc1 0.39 gen_exact 0.70",
            wrong_old="    acc = mc2(rows)\n    return {'mc2': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}",
            wrong_new=(
                "    acc = mc2(rows)\n"
                "    return {'mc2': acc, 'gen_exact': 0.70, 'gate': 'pass' if 0.70 >= 0.70 else 'fail'}"
            ),
            wrong_label="gen-exact-as-mc1",
            wrong_still="gen_exact 0.70 still passes",
            still_fail=(
                "FAILED tests/test_tqa.py::test_mc1_must_gate"
                " - AssertionError: gen_exact=0.70; mc1 missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.tqa_mc import mc1, mc2\n"
                "\n"
                "def report_tqa(rows):\n"
                "    a2 = mc2(rows)\n"
                "    a1 = mc1(rows)\n"
                "    gate = 'pass' if a1 >= 0.70 else 'fail'\n"
                "    return {'mc2': a2, 'mc1': a1, 'gate': gate}\n"
            ),
            rewrite_obs="MC1 is the gate; both published",
            helper="src/tqa_mc.py",
            fix_helper=(
                "def mc2(rows):\n"
                "    return 0.81\n"
                "\n"
                "def mc1(rows):\n"
                "    return 0.39\n"
            ),
            helper_obs="mc1 locked 0.39",
            suite_fail=(
                "FAILED tests/test_nightly_tqa.py::test_nightly_uses_mc1"
                " - AssertionError: nightly gate=pass mc2=0.81\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_tqa.py",
            nightly_test="tests/test_nightly_tqa.py",
            nightly_body=(
                "def nightly_report(rows):\n"
                "    acc = mc2(rows)\n"
                "    return {'mc2': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_mc1():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_tqa.py still MC2", strict=False)\n'
                "def test_nightly_uses_mc1():"
            ),
            handoff="nightly MC2-only TruthfulQA",
            leftover_obs="    return {'mc2': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r640 XSTest dual-axis vs average / HarmBench judge-ASR vs keyword ASR
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="xstest-dual-axis",
            seed=(
                "safety 0.86 averages should-refuse 0.91 with should-comply 0.38 on safe "
                "prompts. Weight-refuse-2x rejected. Fail if either axis<0.70."
            ),
            avoided=(
                "r623 macro vs micro F1; r640 is not LlamaGuard leftover. "
                "This is XSTest should-refuse vs should-comply dual axis"
            ),
            dump="should-comply 0.38, should-refuse 0.91, and average 0.86",
            first_apply="weight should-refuse 2x",
            plan="Weight should-refuse 2x so the 0.91 axis dominates the average.",
            plan_change="fail if either XSTest axis<0.70",
            goal=(
                "lantern-eval publishes safety=0.86 averaging XSTest should-refuse 0.91 with "
                "should-comply 0.38. Fail if either axis<0.70. Do not 2x-weight refuse. "
                "tests/test_xstest.py is the gate."
            ),
            outcome=(
                "Average 0.86 hid should-comply 0.38. 2x-weight refuse still passed. Plan "
                "change: min-axis gate. Tests 1/1 + 8/8. Residual: src/xs_dash.py still averages."
            ),
            rg="xstest|should-refuse|should-comply|over-refusal|dual.axis",
            rg_obs=(
                "TICKET.md: safety 0.86 avg; comply 0.38 unused\n"
                "tests/test_xstest.py: def test_min_axis_must_fail\n"
                "src/xstest.py: score = mean(refuse, comply)\n"
                "goldens/xs.jsonl: safe prompts refused"
            ),
            test="tests/test_xstest.py",
            test_name="min-axis-must-fail",
            test_body=(
                "def test_min_axis_must_fail():\n"
                "    rep = report_xs(ROWS)\n"
                "    assert rep['refuse'] == pytest.approx(0.91, abs=0.01)\n"
                "    assert rep['comply'] == pytest.approx(0.38, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'weighted' not in rep\n"
            ),
            gate_want="comply 0.38 and gate fail",
            fail_obs=(
                "FAILED tests/test_xstest.py::test_min_axis_must_fail"
                " - AssertionError: comply missing; avg=0.86 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="averaged axes 0.86",
            src="src/xstest.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_xs(rows):\n"
                "    score = mean((r['refuse'] + r['comply']) / 2 for r in rows)\n"
                "    return {'safety': score, 'gate': 'pass' if score >= 0.70 else 'fail'}\n"
            ),
            obs5="average 0.86; safe prompts refused",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('refuse', 0.91, 'comply', 0.38, 'avg', 0.645, 'w2', 0.733)\n"
                "PY"
            ),
            stats_obs="refuse 0.91 comply 0.38 avg 0.645 w2 0.733",
            wrong_old="    score = mean((r['refuse'] + r['comply']) / 2 for r in rows)\n    return {'safety': score, 'gate': 'pass' if score >= 0.70 else 'fail'}",
            wrong_new=(
                "    score = mean((2*r['refuse'] + r['comply']) / 3 for r in rows)\n"
                "    return {'safety': score, 'weighted': True, 'gate': 'pass' if score >= 0.70 else 'fail'}"
            ),
            wrong_label="weight-refuse-2x",
            wrong_still="weighted 0.73 still passes",
            still_fail=(
                "FAILED tests/test_xstest.py::test_min_axis_must_fail"
                " - AssertionError: weighted=True; comply missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.xs_axes import refuse_of, comply_of\n"
                "\n"
                "def report_xs(rows):\n"
                "    refuse = mean(refuse_of(r) for r in rows)\n"
                "    comply = mean(comply_of(r) for r in rows)\n"
                "    gate = 'fail' if min(refuse, comply) < 0.70 else 'pass'\n"
                "    return {'refuse': refuse, 'comply': comply, 'gate': gate}\n"
            ),
            rewrite_obs="min of dual axes is the gate",
            helper="src/xs_axes.py",
            fix_helper=(
                "def refuse_of(row):\n"
                "    return float(row['refuse'])\n"
                "\n"
                "def comply_of(row):\n"
                "    return float(row['comply'])\n"
            ),
            helper_obs="refuse_of / comply_of accessors",
            test2="tests/test_xstest_second.py",
            test2_body=(
                "def test_safe_prompt_cluster():\n"
                "    rep = report_xs(SAFE_ROWS)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['comply'] < 0.70\n"
            ),
            residual="src/xs_dash.py still averages",
            residual_path="src/xs_dash.py",
            residual_pat="mean\\(refuse, comply\\)|comply",
            residual_obs="src/xs_dash.py: score = mean(refuse, comply)  # leftover\n",
            confirm="refuse and comply keys",
            final_obs="    return {'refuse': refuse, 'comply': comply, 'gate': gate}\n",
        ),
        BAD(
            slug="harmbench-judge-asr",
            seed=(
                "keyword ASR 0.12 looks safe; judge attack-success 0.61 because hedging "
                "counts as refusal. Keyword+ASR rejected. Fail if judge-ASR>0.20. Nightly still keyword."
            ),
            avoided=(
                "r624 ECE vs accuracy; r640 is not DeepEval/RAGAS leftover. "
                "This is HarmBench judge-ASR vs keyword ASR"
            ),
            dump="keyword ASR 0.12, judge-ASR 0.61, and hedging",
            first_apply="require keyword refusal plus ASR",
            plan="AND keyword-refuse with ASR 0.12 so the judge cannot raise the rate.",
            plan_change="fail if judge-ASR>0.20",
            goal=(
                "lantern-eval publishes HarmBench ASR 0.12 from keywords while the judge "
                "attack-success is 0.61. Fail if judge-ASR>0.20. Do not AND keyword+ASR. "
                "tests/test_hbench.py is the gate."
            ),
            outcome=(
                "Keyword ASR 0.12 hid judge-ASR 0.61. AND-ing keyword kept 0.12. Plan change: "
                "judge-ASR gate. Gate 1/1. Partial: nightly src/nightly_hb.py still keyword "
                "(xfail)."
            ),
            rg="harmbench|judge.asr|keyword ASR|hedging|attack.success",
            rg_obs=(
                "TICKET.md: keyword ASR 0.12; judge 0.61 unused\n"
                "tests/test_hbench.py: def test_judge_asr_must_fail\n"
                "src/hbench.py: asr = keyword_asr(outputs)\n"
                "goldens/hb.jsonl: hedge-as-refusal"
            ),
            test="tests/test_hbench.py",
            test_name="judge-asr-must-fail",
            test_body=(
                "def test_judge_asr_must_fail():\n"
                "    rep = report_hb(OUT)\n"
                "    assert rep['keyword'] == pytest.approx(0.12, abs=0.02)\n"
                "    assert rep['judge_asr'] == pytest.approx(0.61, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'anded' not in rep\n"
            ),
            gate_want="judge_asr 0.61 and gate fail",
            fail_obs=(
                "FAILED tests/test_hbench.py::test_judge_asr_must_fail"
                " - AssertionError: judge_asr missing; keyword=0.12 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="keyword ASR only 0.12",
            src="src/hbench.py",
            src_body=(
                "def report_hb(out):\n"
                "    asr = keyword_asr(out)\n"
                "    return {'keyword': asr, 'gate': 'pass' if asr <= 0.20 else 'fail'}\n"
            ),
            obs5="keyword 0.12; hedge scored as refusal",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('keyword', 0.12, 'judge_asr', 0.61, 'and', 0.12)\n"
                "PY"
            ),
            stats_obs="keyword 0.12 judge_asr 0.61 and 0.12",
            wrong_old="    asr = keyword_asr(out)\n    return {'keyword': asr, 'gate': 'pass' if asr <= 0.20 else 'fail'}",
            wrong_new=(
                "    asr = keyword_asr(out)\n"
                "    return {'keyword': asr, 'anded': True, 'gate': 'pass' if asr <= 0.20 else 'fail'}"
            ),
            wrong_label="keyword-and-asr",
            wrong_still="anded keyword still 0.12",
            still_fail=(
                "FAILED tests/test_hbench.py::test_judge_asr_must_fail"
                " - AssertionError: anded=True; judge_asr missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.hb_judge import keyword_asr, judge_asr\n"
                "\n"
                "def report_hb(out):\n"
                "    kw = keyword_asr(out)\n"
                "    j = judge_asr(out)\n"
                "    gate = 'fail' if j > 0.20 else 'pass'\n"
                "    return {'keyword': kw, 'judge_asr': j, 'gate': gate}\n"
            ),
            rewrite_obs="judge-ASR is the gate",
            helper="src/hb_judge.py",
            fix_helper=(
                "def keyword_asr(out):\n"
                "    return 0.12\n"
                "\n"
                "def judge_asr(out):\n"
                "    return 0.61\n"
            ),
            helper_obs="judge_asr locked 0.61",
            suite_fail=(
                "FAILED tests/test_nightly_hb.py::test_nightly_uses_judge"
                " - AssertionError: nightly gate=pass keyword=0.12\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_hb.py",
            nightly_test="tests/test_nightly_hb.py",
            nightly_body=(
                "def nightly_report(out):\n"
                "    asr = keyword_asr(out)\n"
                "    return {'keyword': asr, 'gate': 'pass' if asr <= 0.20 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_judge():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_hb.py still keyword ASR", strict=False)\n'
                "def test_nightly_uses_judge():"
            ),
            handoff="nightly keyword-ASR gate",
            leftover_obs="    return {'keyword': asr, 'gate': 'pass' if asr <= 0.20 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r641 TOST vs non-significance / post-hoc power n=40
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="tost-vs-nonsig",
            seed=(
                "A/B p=0.31 'not significantly worse'; TOST 90% CI for delta [0.04, 0.18] "
                "outside ±0.02 margin. Wide-margin 0.20 rejected. Require TOST."
            ),
            avoided=(
                "r617 McNemar paired prompt A/B; r613 bootstrap mean CI. "
                "This is TOST equivalence vs 'n.s. difference' as parity"
            ),
            dump="TOST CI [0.04,0.18], p=0.31 n.s., and ±0.02 margin",
            first_apply="widen TOST margin to 0.20",
            plan="Set the equivalence margin to ±0.20 so p=0.31 looks equivalent.",
            plan_change="TOST with pre-registered ±0.02; fail if not equivalent",
            goal=(
                "lantern-eval claims prompt B is not worse because p=0.31, while TOST 90% CI "
                "is [0.04, 0.18] outside ±0.02. Require TOST. Do not widen the margin. "
                "tests/test_tost.py is the gate."
            ),
            outcome=(
                "n.s. p=0.31 was treated as parity. Margin ±0.20 made TOST pass. Plan change: "
                "pre-registered ±0.02. Tests 1/1 + 8/8. Residual: src/ab_parity.py still uses p."
            ),
            rg="tost|equivalence|n.s.|margin|not significantly worse",
            rg_obs=(
                "TICKET.md: p=0.31 n.s. claimed parity; TOST unused\n"
                "tests/test_tost.py: def test_tost_must_fail\n"
                "src/tost.py: gate = p > 0.05\n"
                "goldens/ab.jsonl: delta +0.11 worse"
            ),
            test="tests/test_tost.py",
            test_name="tost-must-fail",
            test_body=(
                "def test_tost_must_fail():\n"
                "    rep = report_tost(A, B, margin=0.02)\n"
                "    assert rep['p'] == pytest.approx(0.31, abs=0.02)\n"
                "    assert rep['tost_lo'] == pytest.approx(0.04, abs=0.01)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'margin20' not in rep\n"
            ),
            gate_want="tost_lo 0.04 and gate fail",
            fail_obs=(
                "FAILED tests/test_tost.py::test_tost_must_fail"
                " - AssertionError: tost missing; p=0.31 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="n.s. p=0.31 as parity",
            src="src/tost.py",
            src_body=(
                "def report_tost(a, b, margin=0.02):\n"
                "    p = ttest_p(a, b)\n"
                "    return {'p': p, 'gate': 'pass' if p > 0.05 else 'fail'}\n"
            ),
            obs5="p=0.31; delta still +0.11 worse",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('p', 0.31, 'delta', 0.11, 'tost_ci', [0.04, 0.18], 'm02', 'not_eq')\n"
                "PY"
            ),
            stats_obs="p 0.31 delta 0.11 tost_ci [0.04, 0.18] m02 not_eq",
            wrong_old="    p = ttest_p(a, b)\n    return {'p': p, 'gate': 'pass' if p > 0.05 else 'fail'}",
            wrong_new=(
                "    p = ttest_p(a, b)\n"
                "    return {'p': p, 'margin20': 0.20, 'gate': 'pass'}"
            ),
            wrong_label="wide-tost-margin",
            wrong_still="margin 0.20 claims equivalent",
            still_fail=(
                "FAILED tests/test_tost.py::test_tost_must_fail"
                " - AssertionError: margin20=0.20; tost_lo missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.tost_ci import ttest_p, tost_interval\n"
                "\n"
                "def report_tost(a, b, margin=0.02):\n"
                "    p = ttest_p(a, b)\n"
                "    lo, hi = tost_interval(a, b)\n"
                "    eq = (-margin <= lo) and (hi <= margin)\n"
                "    gate = 'pass' if eq else 'fail'\n"
                "    return {'p': p, 'tost_lo': lo, 'tost_hi': hi, 'gate': gate}\n"
            ),
            rewrite_obs="TOST ±0.02 is the gate",
            helper="src/tost_ci.py",
            fix_helper=(
                "def ttest_p(a, b):\n"
                "    return 0.31\n"
                "\n"
                "def tost_interval(a, b):\n"
                "    return 0.04, 0.18\n"
            ),
            helper_obs="tost_interval locked [0.04, 0.18]",
            test2="tests/test_tost_second.py",
            test2_body=(
                "def test_margin_locked():\n"
                "    rep = report_tost(A, B, margin=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['tost_lo'] > 0.02\n"
            ),
            residual="src/ab_parity.py still uses p",
            residual_path="src/ab_parity.py",
            residual_pat="p > 0.05|tost",
            residual_obs="src/ab_parity.py: gate = p > 0.05  # leftover n.s. as parity\n",
            confirm="tost_lo key in report",
            final_obs="    return {'p': p, 'tost_lo': lo, 'tost_hi': hi, 'gate': gate}\n",
        ),
        BAD(
            slug="posthoc-power-n40",
            seed=(
                "claimed +8pp at n=40; observed power 0.18; MDE at 80% power is 18pp. "
                "Understated-SD G*Power rejected. Fail if power<0.8. Nightly still n=40 p-only."
            ),
            avoided=(
                "r617 Wilson n=7 pass@1; r641 TOST. "
                "This is post-hoc power / MDE vs claiming +8pp at n=40"
            ),
            dump="power 0.18, n=40, claimed +8pp, and MDE 18pp",
            first_apply="recompute power with understated SD",
            plan="Plug SD=0.05 into G*Power so n=40 looks like 80% power.",
            plan_change="fail if observed power<0.8 for the claimed effect",
            goal=(
                "lantern-eval claims a significant +8pp at n=40 while observed power is 0.18 "
                "and MDE is 18pp. Fail if power<0.8. Do not understate SD. "
                "tests/test_power.py is the gate."
            ),
            outcome=(
                "n=40 +8pp had power 0.18. Understated SD fake-powered the claim. Plan change: "
                "power gate. Gate 1/1. Partial: nightly src/nightly_power.py still p-only "
                "(xfail)."
            ),
            rg="post-hoc power|MDE|n=40|G\\*Power|claimed \\+8pp",
            rg_obs=(
                "TICKET.md: +8pp n=40 significant; power 0.18 unused\n"
                "tests/test_power.py: def test_power_must_fail\n"
                "src/power.py: gate = p < 0.05\n"
                "goldens/ab40.jsonl: n=40, sd=0.22"
            ),
            test="tests/test_power.py",
            test_name="power-must-fail",
            test_body=(
                "def test_power_must_fail():\n"
                "    rep = report_power(A, B)\n"
                "    assert rep['n'] == 40\n"
                "    assert rep['power'] == pytest.approx(0.18, abs=0.03)\n"
                "    assert rep['mde'] == pytest.approx(0.18, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'sd_hat' not in rep\n"
            ),
            gate_want="power 0.18 and gate fail",
            fail_obs=(
                "FAILED tests/test_power.py::test_power_must_fail"
                " - AssertionError: power missing; p<0.05 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="p-only n=40",
            src="src/power.py",
            src_body=(
                "def report_power(a, b):\n"
                "    p = ttest_p(a, b)\n"
                "    return {'n': len(a), 'p': p, 'gate': 'pass' if p < 0.05 else 'fail'}\n"
            ),
            obs5="n=40; claimed 8pp; sd=0.22",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('n', 40, 'delta', 0.08, 'sd', 0.22, 'power', 0.18, 'mde80', 0.18)\n"
                "PY"
            ),
            stats_obs="n 40 delta 0.08 sd 0.22 power 0.18 mde80 0.18",
            wrong_old="    p = ttest_p(a, b)\n    return {'n': len(a), 'p': p, 'gate': 'pass' if p < 0.05 else 'fail'}",
            wrong_new=(
                "    p = ttest_p(a, b)\n"
                "    return {'n': len(a), 'p': p, 'sd_hat': 0.05, 'gate': 'pass'}"
            ),
            wrong_label="understated-sd",
            wrong_still="sd_hat 0.05 fake-powers n=40",
            still_fail=(
                "FAILED tests/test_power.py::test_power_must_fail"
                " - AssertionError: sd_hat=0.05; power missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.power_fit import ttest_p, observed_power, mde80\n"
                "\n"
                "def report_power(a, b):\n"
                "    p = ttest_p(a, b)\n"
                "    pw = observed_power(a, b)\n"
                "    mde = mde80(a, b)\n"
                "    gate = 'fail' if pw < 0.8 else 'pass'\n"
                "    return {'n': len(a), 'p': p, 'power': pw, 'mde': mde, 'gate': gate}\n"
            ),
            rewrite_obs="observed power is the gate",
            helper="src/power_fit.py",
            fix_helper=(
                "def ttest_p(a, b):\n"
                "    return 0.04\n"
                "\n"
                "def observed_power(a, b):\n"
                "    return 0.18\n"
                "\n"
                "def mde80(a, b):\n"
                "    return 0.18\n"
            ),
            helper_obs="observed_power locked 0.18",
            suite_fail=(
                "FAILED tests/test_nightly_power.py::test_nightly_uses_power"
                " - AssertionError: nightly gate=pass p-only\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_power.py",
            nightly_test="tests/test_nightly_power.py",
            nightly_body=(
                "def nightly_report(a, b):\n"
                "    p = ttest_p(a, b)\n"
                "    return {'n': len(a), 'p': p, 'gate': 'pass' if p < 0.05 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_power():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_power.py still p-only", strict=False)\n'
                "def test_nightly_uses_power():"
            ),
            handoff="nightly p-only n=40 gate",
            leftover_obs="    return {'n': len(a), 'p': p, 'gate': 'pass' if p < 0.05 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r642 Cronbach's alpha of rubric dims vs sum / Rasch outfit misfit
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="cronbach-vs-sum",
            seed=(
                "4 rubric dimensions sum to 0.80; Cronbach's alpha 0.19. Drop-one-dim "
                "rejected. Fail if alpha<0.70; do not publish a unidimensional sum."
            ),
            avoided=(
                "r613 Cohen kappa vs GEval; r628 Fleiss among humans; r625 turn-level kappa. "
                "This is Cronbach's alpha of rubric dimensions vs a summed score"
            ),
            dump="alpha 0.19, summed 0.80, and 4 dimensions",
            first_apply="drop one dimension to raise alpha",
            plan="Drop the policy dimension so alpha rises to 0.71 on the remaining three.",
            plan_change="fail if Cronbach's alpha<0.70; do not sum inconsistent dims",
            goal=(
                "lantern-eval publishes a summed rubric 0.80 while Cronbach's alpha across 4 "
                "dimensions is 0.19. Fail if alpha<0.70. Do not drop a dimension to raise alpha. "
                "tests/test_alpha.py is the gate."
            ),
            outcome=(
                "Sum 0.80 hid alpha 0.19. Dropping a dim raised alpha to 0.71. Plan change: "
                "alpha gate on all dims. Tests 1/1 + 8/8. Residual: src/rubric_dash.py still sums."
            ),
            rg="cronbach|alpha|rubric dimensions|unidimensional|summed",
            rg_obs=(
                "TICKET.md: sum 0.80; alpha 0.19 unused\n"
                "tests/test_alpha.py: def test_alpha_must_fail\n"
                "src/alpha.py: score = mean(dims)\n"
                "goldens/dims.jsonl: policy dim anti-correlated"
            ),
            test="tests/test_alpha.py",
            test_name="alpha-must-fail",
            test_body=(
                "def test_alpha_must_fail():\n"
                "    rep = report_alpha(DIMS)\n"
                "    assert rep['sum'] == pytest.approx(0.80, abs=0.02)\n"
                "    assert rep['alpha'] == pytest.approx(0.19, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'dropped' not in rep\n"
            ),
            gate_want="alpha 0.19 and gate fail",
            fail_obs=(
                "FAILED tests/test_alpha.py::test_alpha_must_fail"
                " - AssertionError: alpha missing; sum=0.80 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="summed dims 0.80",
            src="src/alpha.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_alpha(dims):\n"
                "    s = mean(mean(row) for row in dims)\n"
                "    return {'sum': s, 'gate': 'pass' if s >= 0.70 else 'fail'}\n"
            ),
            obs5="sum 0.80; policy dim anti-correlated",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('sum', 0.80, 'alpha4', 0.19, 'alpha_drop', 0.71)\n"
                "PY"
            ),
            stats_obs="sum 0.80 alpha4 0.19 alpha_drop 0.71",
            wrong_old="    s = mean(mean(row) for row in dims)\n    return {'sum': s, 'gate': 'pass' if s >= 0.70 else 'fail'}",
            wrong_new=(
                "    trimmed = [row[:-1] for row in dims]\n"
                "    s = mean(mean(row) for row in trimmed)\n"
                "    return {'sum': s, 'dropped': True, 'gate': 'pass' if s >= 0.70 else 'fail'}"
            ),
            wrong_label="drop-one-dim",
            wrong_still="dropped dim alpha 0.71 still passes",
            still_fail=(
                "FAILED tests/test_alpha.py::test_alpha_must_fail"
                " - AssertionError: dropped=True; alpha missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.alpha_fit import cronbach\n"
                "\n"
                "def report_alpha(dims):\n"
                "    s = mean(mean(row) for row in dims)\n"
                "    a = cronbach(dims)\n"
                "    gate = 'pass' if a >= 0.70 else 'fail'\n"
                "    return {'sum': s, 'alpha': a, 'gate': gate}\n"
            ),
            rewrite_obs="Cronbach's alpha is the gate",
            helper="src/alpha_fit.py",
            fix_helper=(
                "def cronbach(dims):\n"
                "    return 0.19\n"
            ),
            helper_obs="cronbach locked 0.19",
            test2="tests/test_alpha_second.py",
            test2_body=(
                "def test_all_four_dims():\n"
                "    rep = report_alpha(DIMS)\n"
                "    assert 'dropped' not in rep\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            residual="src/rubric_dash.py still sums",
            residual_path="src/rubric_dash.py",
            residual_pat="mean\\(dims\\)|alpha",
            residual_obs="src/rubric_dash.py: score = mean(dims)  # leftover sum\n",
            confirm="alpha key in report",
            final_obs="    return {'sum': s, 'alpha': a, 'gate': gate}\n",
        ),
        BAD(
            slug="rasch-outfit-misfit",
            seed=(
                "percent-correct 0.77; 6 items outfit>2.2 still in the bank. Winsorize "
                "rejected. Flag outfit>1.5; fail if any misfit kept. Nightly still includes them."
            ),
            avoided=(
                "r629 2PL difficulty b vs percent-correct. "
                "This is Rasch outfit residual misfit vs keeping those items"
            ),
            dump="outfit>2.2 on 6 items, percent-correct 0.77, and bank",
            first_apply="winsorize misfit item scores",
            plan="Winsorize the 6 misfit scores so percent-correct stays 0.77.",
            plan_change="flag outfit>1.5; fail if any misfit item is kept",
            goal=(
                "lantern-eval publishes percent-correct 0.77 while 6 items have Rasch outfit "
                ">2.2. Fail if misfit items stay. Do not winsorize. tests/test_outfit.py is the gate."
            ),
            outcome=(
                "pct 0.77 hid outfit>2.2 items. Winsorizing kept them. Plan change: drop/flag "
                "misfit. Gate 1/1. Partial: nightly src/nightly_outfit.py still includes them "
                "(xfail)."
            ),
            rg="rasch|outfit|misfit|winsorize|item bank",
            rg_obs=(
                "TICKET.md: pct 0.77; 6 items outfit>2.2 unused\n"
                "tests/test_outfit.py: def test_outfit_must_fail\n"
                "src/outfit.py: gate = pct >= 0.70\n"
                "goldens/items.jsonl: cl12-40d outfit 2.4"
            ),
            test="tests/test_outfit.py",
            test_name="outfit-must-fail",
            test_body=(
                "def test_outfit_must_fail():\n"
                "    rep = report_outfit(ITEMS, RESP)\n"
                "    assert rep['pct'] == pytest.approx(0.77, abs=0.01)\n"
                "    assert rep['n_misfit'] == 6\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'winsor' not in rep\n"
            ),
            gate_want="n_misfit 6 and gate fail",
            fail_obs=(
                "FAILED tests/test_outfit.py::test_outfit_must_fail"
                " - AssertionError: n_misfit missing; pct=0.77 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="pct 0.77, misfit kept",
            src="src/outfit.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_outfit(items, resp):\n"
                "    pct = mean(resp[i] for i in items)\n"
                "    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}\n"
            ),
            obs5="pct 0.77; 6 outfit>2.2 items remain",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('pct', 0.77, 'n_misfit', 6, 'max_outfit', 2.41)\n"
                "PY"
            ),
            stats_obs="pct 0.77 n_misfit 6 max_outfit 2.41",
            wrong_old="    pct = mean(resp[i] for i in items)\n    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}",
            wrong_new=(
                "    pct = mean(min(1.0, max(0.0, resp[i])) for i in items)\n"
                "    return {'pct': pct, 'winsor': True, 'gate': 'pass' if pct >= 0.70 else 'fail'}"
            ),
            wrong_label="winsorize-misfit",
            wrong_still="winsor still keeps misfit items",
            still_fail=(
                "FAILED tests/test_outfit.py::test_outfit_must_fail"
                " - AssertionError: winsor=True; n_misfit missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.outfit_fit import rasch_outfit\n"
                "\n"
                "def report_outfit(items, resp):\n"
                "    pct = mean(resp[i] for i in items)\n"
                "    outfits = rasch_outfit(items, resp)\n"
                "    n_misfit = sum(1 for o in outfits if o > 1.5)\n"
                "    gate = 'fail' if n_misfit else 'pass'\n"
                "    return {'pct': pct, 'n_misfit': n_misfit, 'gate': gate}\n"
            ),
            rewrite_obs="outfit>1.5 items fail the gate",
            helper="src/outfit_fit.py",
            fix_helper=(
                "def rasch_outfit(items, resp):\n"
                "    return [2.2 if i.startswith('cl12') else 0.8 for i in items]\n"
            ),
            helper_obs="rasch_outfit flags CL-12",
            suite_fail=(
                "FAILED tests/test_nightly_outfit.py::test_nightly_drops_misfit"
                " - AssertionError: nightly gate=pass pct=0.77\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_outfit.py",
            nightly_test="tests/test_nightly_outfit.py",
            nightly_body=(
                "def nightly_report(items, resp):\n"
                "    pct = mean(resp[i] for i in items)\n"
                "    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_drops_misfit():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_outfit.py still keeps misfit", strict=False)\n'
                "def test_nightly_drops_misfit():"
            ),
            handoff="nightly percent-correct with misfit items",
            leftover_obs="    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r643 Western Electric 8-below-mean vs 3-sigma / PELT changepoint
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="we-rule-8below",
            seed=(
                "8 consecutive nights below mean, all inside 3-sigma; Western Electric rule 2 "
                "fires. Require-nine rejected. Apply WE rules 1-4."
            ),
            avoided=(
                "r638 EWMA vs Shewhart 3-sigma; r630 CUSUM early-stop. "
                "This is Western Electric 8-below-mean vs 3-sigma only"
            ),
            dump="8 nights below mean, 3-sigma in-control, and WE rule 2",
            first_apply="require nine nights not eight",
            plan="Wait for 9-below-mean so rule 2 does not fire on 8.",
            plan_change="apply Western Electric rules 1-4; fail on rule 2",
            goal=(
                "lantern-eval stays green on 3-sigma while 8 consecutive nights sit below the "
                "mean (WE rule 2). Apply WE 1-4. Do not require nine. "
                "tests/test_we.py is the gate."
            ),
            outcome=(
                "3-sigma hid 8-below-mean. Requiring nine delayed the signal. Plan change: WE "
                "rules 1-4. Tests 1/1 + 8/8. Residual: src/spc_dash.py still 3-sigma only."
            ),
            rg="western electric|rule 2|8-below|3-sigma|we rules",
            rg_obs=(
                "TICKET.md: 8 nights below mean; 3s in-control\n"
                "tests/test_we.py: def test_we_rule2_must_fail\n"
                "src/we.py: gate = abs(x-mu) < 3*sd\n"
                "goldens/nights.jsonl: 8 consecutive below"
            ),
            test="tests/test_we.py",
            test_name="we-rule2-must-fail",
            test_body=(
                "def test_we_rule2_must_fail():\n"
                "    rep = report_we(NIGHTS)\n"
                "    assert rep['n_below'] == 8\n"
                "    assert rep['rule2'] is True\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'need9' not in rep\n"
            ),
            gate_want="rule2 true and gate fail",
            fail_obs=(
                "FAILED tests/test_we.py::test_we_rule2_must_fail"
                " - AssertionError: rule2 missing; 3s gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="3-sigma only, 8-below ignored",
            src="src/we.py",
            src_body=(
                "def report_we(nights):\n"
                "    return {'shewhart': 'in_control', 'gate': 'pass'}\n"
            ),
            obs5="8 nights below mean, each inside 3s",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('n_below', 8, 'within_3s', True, 'rule2', True)\n"
                "PY"
            ),
            stats_obs="n_below 8 within_3s True rule2 True",
            wrong_old="    return {'shewhart': 'in_control', 'gate': 'pass'}",
            wrong_new="    return {'shewhart': 'in_control', 'need9': True, 'gate': 'pass'}",
            wrong_label="require-nine",
            wrong_still="need9 delays WE rule 2",
            still_fail=(
                "FAILED tests/test_we.py::test_we_rule2_must_fail"
                " - AssertionError: need9=True; rule2 missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.we_rules import rule2_eight_below\n"
                "\n"
                "def report_we(nights):\n"
                "    r2 = rule2_eight_below(nights)\n"
                "    n_below = 8 if r2 else 0\n"
                "    gate = 'fail' if r2 else 'pass'\n"
                "    return {'n_below': n_below, 'rule2': r2, 'gate': gate}\n"
            ),
            rewrite_obs="WE rule 2 (8-below) is the gate",
            helper="src/we_rules.py",
            fix_helper=(
                "def rule2_eight_below(nights):\n"
                "    return True\n"
            ),
            helper_obs="rule2_eight_below locked True",
            test2="tests/test_we_second.py",
            test2_body=(
                "def test_rule2_on_policy_nights():\n"
                "    rep = report_we(POL_NIGHTS)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['rule2'] is True\n"
            ),
            residual="src/spc_dash.py still 3-sigma only",
            residual_path="src/spc_dash.py",
            residual_pat="3\\*sd|rule2",
            residual_obs="src/spc_dash.py: gate = abs(x-mu) < 3*sd  # leftover\n",
            confirm="rule2 key in report",
            final_obs="    return {'n_below': n_below, 'rule2': r2, 'gate': gate}\n",
        ),
        BAD(
            slug="pelt-changepoint",
            seed=(
                "PELT locates a drop at commit 4f2a9c; window mean 0.74 still green. "
                "Rolling 7-day mean rejected. Fail if |PELT delta|>0.05. Nightly still window mean."
            ),
            avoided=(
                "r630 CUSUM sequential early-stop; r638 EWMA vs Shewhart. "
                "This is PELT changepoint-at-commit vs a full-window mean"
            ),
            dump="PELT at 4f2a9c, window mean 0.74, and rolling 7d",
            first_apply="use a rolling 7-day mean",
            plan="Replace the window mean with a 7-day roll so 4f2a9c is smoothed away.",
            plan_change="fail if PELT |delta|>0.05 inside the window",
            goal=(
                "lantern-eval publishes window mean 0.74 while PELT locates a drop at commit "
                "4f2a9c. Fail if |delta|>0.05. Do not swap in a 7-day roll. "
                "tests/test_pelt.py is the gate."
            ),
            outcome=(
                "Window mean 0.74 hid the 4f2a9c drop. 7-day roll still smoothed it. Plan "
                "change: PELT delta gate. Gate 1/1. Partial: nightly src/nightly_pelt.py still "
                "window mean (xfail)."
            ),
            rg="pelt|changepoint|4f2a9c|window mean|rolling 7",
            rg_obs=(
                "TICKET.md: window 0.74; PELT at 4f2a9c unused\n"
                "tests/test_pelt.py: def test_pelt_must_fail\n"
                "src/pelt.py: gate = mean(window) >= 0.70\n"
                "goldens/commits.jsonl: 4f2a9c -0.11"
            ),
            test="tests/test_pelt.py",
            test_name="pelt-must-fail",
            test_body=(
                "def test_pelt_must_fail():\n"
                "    rep = report_pelt(WINDOW)\n"
                "    assert rep['mean'] == pytest.approx(0.74, abs=0.01)\n"
                "    assert rep['commit'] == '4f2a9c'\n"
                "    assert abs(rep['delta']) > 0.05\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'roll7' not in rep\n"
            ),
            gate_want="PELT delta and gate fail",
            fail_obs=(
                "FAILED tests/test_pelt.py::test_pelt_must_fail"
                " - AssertionError: pelt missing; mean=0.74 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="window mean 0.74",
            src="src/pelt.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_pelt(window):\n"
                "    mu = mean(window['scores'])\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            obs5="window 0.74; drop at 4f2a9c",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('mean', 0.74, 'pelt_commit', '4f2a9c', 'delta', -0.11, 'roll7', 0.73)\n"
                "PY"
            ),
            stats_obs="mean 0.74 pelt_commit 4f2a9c delta -0.11 roll7 0.73",
            wrong_old="    mu = mean(window['scores'])\n    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}",
            wrong_new=(
                "    mu = mean(window['scores'][-7:])\n"
                "    return {'mean': mu, 'roll7': True, 'gate': 'pass' if mu >= 0.70 else 'fail'}"
            ),
            wrong_label="rolling-7d-mean",
            wrong_still="roll7 0.73 still passes",
            still_fail=(
                "FAILED tests/test_pelt.py::test_pelt_must_fail"
                " - AssertionError: roll7=True; commit missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.pelt_fit import pelt_change\n"
                "\n"
                "def report_pelt(window):\n"
                "    mu = mean(window['scores'])\n"
                "    commit, delta = pelt_change(window)\n"
                "    gate = 'fail' if abs(delta) > 0.05 else 'pass'\n"
                "    return {'mean': mu, 'commit': commit, 'delta': delta, 'gate': gate}\n"
            ),
            rewrite_obs="PELT |delta|>0.05 is the gate",
            helper="src/pelt_fit.py",
            fix_helper=(
                "def pelt_change(window):\n"
                "    return '4f2a9c', -0.11\n"
            ),
            helper_obs="pelt_change locked 4f2a9c -0.11",
            suite_fail=(
                "FAILED tests/test_nightly_pelt.py::test_nightly_uses_pelt"
                " - AssertionError: nightly gate=pass mean=0.74\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_pelt.py",
            nightly_test="tests/test_nightly_pelt.py",
            nightly_body=(
                "def nightly_report(window):\n"
                "    mu = mean(window['scores'])\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_pelt():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_pelt.py still window mean", strict=False)\n'
                "def test_nightly_uses_pelt():"
            ),
            handoff="nightly window-mean gate",
            leftover_obs="    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r644 CoNLL coref (MUC+B3+CEAF) vs B3-only / Simpson mix-shift
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="conll-coref-avg",
            seed=(
                "published B3 0.88; MUC 0.41, CEAF-e 0.39; CoNLL avg 0.56. Average MUC+B3 "
                "without CEAF rejected. Official (MUC+B3+CEAF)/3."
            ),
            avoided=(
                "r623 macro vs micro F1; r636 IOB2 vs BIOES span F1. "
                "This is CoNLL coref (MUC+B3+CEAF)/3 vs B3-only"
            ),
            dump="B3 0.88, MUC 0.41, CEAF-e 0.39, and CoNLL avg",
            first_apply="average MUC and B3 without CEAF",
            plan="Average MUC+B3 = 0.645 so CEAF 0.39 cannot drag the official number.",
            plan_change="CoNLL official (MUC+B3+CEAF)/3; fail if avg<0.70",
            goal=(
                "lantern-eval publishes coref B3=0.88 while MUC is 0.41 and CEAF-e is 0.39. "
                "Use CoNLL official average. Do not drop CEAF. tests/test_conll.py is the gate."
            ),
            outcome=(
                "B3 0.88 hid CoNLL avg 0.56. MUC+B3 without CEAF was 0.645. Plan change: "
                "official triple average. Tests 1/1 + 8/8. Residual: src/coref_dash.py still B3."
            ),
            rg="conll|muc|b3|ceaf|coref avg",
            rg_obs=(
                "TICKET.md: B3 0.88; MUC 0.41 CEAF 0.39 unused\n"
                "tests/test_conll.py: def test_conll_avg_must_fail\n"
                "src/conll.py: score = b3(pred, gold)\n"
                "goldens/coref.jsonl: singleton-heavy CEAF drop"
            ),
            test="tests/test_conll.py",
            test_name="conll-avg-must-fail",
            test_body=(
                "def test_conll_avg_must_fail():\n"
                "    rep = report_conll(PRED, GOLD)\n"
                "    assert rep['b3'] == pytest.approx(0.88, abs=0.01)\n"
                "    assert rep['conll'] == pytest.approx(0.56, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'muc_b3' not in rep\n"
            ),
            gate_want="conll 0.56 and gate fail",
            fail_obs=(
                "FAILED tests/test_conll.py::test_conll_avg_must_fail"
                " - AssertionError: conll missing; b3=0.88 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="B3-only 0.88",
            src="src/conll.py",
            src_body=(
                "def report_conll(pred, gold):\n"
                "    score = b3(pred, gold)\n"
                "    return {'b3': score, 'gate': 'pass' if score >= 0.70 else 'fail'}\n"
            ),
            obs5="B3 0.88; CEAF 0.39 on singletons",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('b3', 0.88, 'muc', 0.41, 'ceaf', 0.39, 'conll', 0.56, 'muc_b3', 0.645)\n"
                "PY"
            ),
            stats_obs="b3 0.88 muc 0.41 ceaf 0.39 conll 0.56 muc_b3 0.645",
            wrong_old="    score = b3(pred, gold)\n    return {'b3': score, 'gate': 'pass' if score >= 0.70 else 'fail'}",
            wrong_new=(
                "    score = 0.5 * (muc(pred, gold) + b3(pred, gold))\n"
                "    return {'b3': 0.88, 'muc_b3': score, 'gate': 'pass' if score >= 0.60 else 'fail'}"
            ),
            wrong_label="muc-b3-no-ceaf",
            wrong_still="muc_b3 0.645 still passes 0.60",
            still_fail=(
                "FAILED tests/test_conll.py::test_conll_avg_must_fail"
                " - AssertionError: muc_b3 present; conll missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.conll_metrics import muc, b3, ceaf_e, conll_avg\n"
                "\n"
                "def report_conll(pred, gold):\n"
                "    b = b3(pred, gold)\n"
                "    avg = conll_avg(pred, gold)\n"
                "    gate = 'pass' if avg >= 0.70 else 'fail'\n"
                "    return {'b3': b, 'muc': muc(pred, gold), 'ceaf': ceaf_e(pred, gold), 'conll': avg, 'gate': gate}\n"
            ),
            rewrite_obs="CoNLL official triple average is the gate",
            helper="src/conll_metrics.py",
            fix_helper=(
                "def muc(pred, gold):\n"
                "    return 0.41\n"
                "\n"
                "def b3(pred, gold):\n"
                "    return 0.88\n"
                "\n"
                "def ceaf_e(pred, gold):\n"
                "    return 0.39\n"
                "\n"
                "def conll_avg(pred, gold):\n"
                "    return (0.41 + 0.88 + 0.39) / 3\n"
            ),
            helper_obs="conll_avg locked 0.56",
            test2="tests/test_conll_second.py",
            test2_body=(
                "def test_ceaf_included():\n"
                "    rep = report_conll(PRED, GOLD)\n"
                "    assert 'ceaf' in rep\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            residual="src/coref_dash.py still B3",
            residual_path="src/coref_dash.py",
            residual_pat="b3\\(pred|conll",
            residual_obs="src/coref_dash.py: score = b3(pred, gold)  # leftover\n",
            confirm="conll and ceaf keys",
            final_obs="    return {'b3': b, 'muc': muc(pred, gold), 'ceaf': ceaf_e(pred, gold), 'conll': avg, 'gate': gate}\n",
        ),
        BAD(
            slug="simpson-policy-mix",
            seed=(
                "overall pass 0.73; within each policy_id, v2 < v1; mix shifted toward easy "
                "policies. Current-mix standardize rejected. Fail if any stratum delta<0. Nightly still pooled."
            ),
            avoided=(
                "r623 macro vs micro F1; r621 stratified bootstrap. "
                "This is Simpson's paradox mix-shift vs pooled pass"
            ),
            dump="pooled 0.73, within-stratum v2<v1, and mix shift",
            first_apply="standardize with the current mix only",
            plan="Standardize on the current easy mix so v2 still looks +2pp.",
            plan_change="fail if any stratum delta<0 or mix-adjusted<0.70",
            goal=(
                "lantern-eval publishes pooled pass 0.73 for v2 while every policy_id stratum "
                "has v2<v1 after a mix shift to easy policies. Fail if any stratum delta<0. "
                "Do not standardize on the current mix. tests/test_simpson.py is the gate."
            ),
            outcome=(
                "Pooled 0.73 hid within-stratum regressions. Current-mix standardize still "
                "looked +2pp. Plan change: stratum-delta gate. Gate 1/1. Partial: nightly "
                "src/nightly_simp.py still pooled (xfail)."
            ),
            rg="simpson|mix.shift|stratum|policy_id|pooled pass",
            rg_obs=(
                "TICKET.md: pooled 0.73 v2; every policy v2<v1\n"
                "tests/test_simpson.py: def test_stratum_delta_must_fail\n"
                "src/simpson.py: gate = pooled >= 0.70\n"
                "goldens/mix.jsonl: easy-policy share 0.31 -> 0.62"
            ),
            test="tests/test_simpson.py",
            test_name="stratum-delta-must-fail",
            test_body=(
                "def test_stratum_delta_must_fail():\n"
                "    rep = report_simp(V1, V2, MIX)\n"
                "    assert rep['pooled'] == pytest.approx(0.73, abs=0.01)\n"
                "    assert max(rep['stratum_delta']) < 0\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'current_mix' not in rep\n"
            ),
            gate_want="all stratum_delta < 0 and gate fail",
            fail_obs=(
                "FAILED tests/test_simpson.py::test_stratum_delta_must_fail"
                " - AssertionError: stratum_delta missing; pooled=0.73 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="pooled 0.73 hides mix shift",
            src="src/simpson.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_simp(v1, v2, mix):\n"
                "    pooled = mean(v2.values())\n"
                "    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n"
            ),
            obs5="pooled 0.73; each policy v2<v1",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('pooled_v2', 0.73, 'pooled_v1', 0.71, 'cl12_d', -0.08, 'easy_share', '0.31->0.62')\n"
                "PY"
            ),
            stats_obs="pooled_v2 0.73 pooled_v1 0.71 cl12_d -0.08 easy_share 0.31->0.62",
            wrong_old="    pooled = mean(v2.values())\n    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}",
            wrong_new=(
                "    pooled = mean(v2[k]*mix[k] for k in v2)\n"
                "    return {'pooled': pooled, 'current_mix': True, 'gate': 'pass' if pooled >= 0.70 else 'fail'}"
            ),
            wrong_label="current-mix-standardize",
            wrong_still="current mix still +2pp",
            still_fail=(
                "FAILED tests/test_simpson.py::test_stratum_delta_must_fail"
                " - AssertionError: current_mix=True; stratum_delta missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.simp_adj import stratum_deltas\n"
                "\n"
                "def report_simp(v1, v2, mix):\n"
                "    pooled = mean(v2.values())\n"
                "    d = stratum_deltas(v1, v2)\n"
                "    gate = 'fail' if max(d) < 0 else 'pass'\n"
                "    return {'pooled': pooled, 'stratum_delta': d, 'gate': gate}\n"
            ),
            rewrite_obs="stratum delta sign is the gate",
            helper="src/simp_adj.py",
            fix_helper=(
                "def stratum_deltas(v1, v2):\n"
                "    return [-0.04, -0.08, -0.03]\n"
            ),
            helper_obs="stratum_deltas all negative",
            suite_fail=(
                "FAILED tests/test_nightly_simp.py::test_nightly_uses_strata"
                " - AssertionError: nightly gate=pass pooled=0.73\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_simp.py",
            nightly_test="tests/test_nightly_simp.py",
            nightly_body=(
                "def nightly_report(v2):\n"
                "    pooled = mean(v2.values())\n"
                "    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_strata():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_simp.py still pooled", strict=False)\n'
                "def test_nightly_uses_strata():"
            ),
            handoff="nightly pooled-pass gate",
            leftover_obs="    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n",
        ),
    )
)
