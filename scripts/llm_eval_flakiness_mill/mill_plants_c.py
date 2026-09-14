"""Unique eval-flakiness plants r629–r636. Not r613–r628 clones or leftover catalogs."""

from mill_plants import _ok, _bad

MORE = []


def OK(**kwargs):
    kwargs.setdefault("tests_passed", 8)
    kwargs.setdefault("suite_ok", "8 passed in 4.2s")
    kwargs.setdefault("suite_short", "8/8")
    kwargs.setdefault("test2_pass", "1 passed in 0.40s")
    kwargs.setdefault("gate_again", "1 passed in 1.4s")
    kwargs.setdefault("pass_obs", "1 passed in 1.1s")
    return _ok(**kwargs)


def BAD(**kwargs):
    kwargs.setdefault("tests_passed", 1)
    kwargs.setdefault("pass_obs", "1 passed in 0.88s")
    kwargs.setdefault("xfail_obs", "1 passed, 1 xfailed")
    kwargs.setdefault("gate_again", "1 passed in 0.77s")
    return _bad(**kwargs)


# ---------------------------------------------------------------------------
# r629 2PL IRT difficulty vs percent-correct / Mantel-Haenszel DIF by locale
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="irt-2pl-vs-pct",
            seed=(
                "percent-correct 0.78 green; 2PL difficulty b=2.41 on CL-12 refund items. "
                "1PL Rasch rejected. Fail if any item b>=1.5 or a<0.4."
            ),
            avoided=(
                "r613 Cohen kappa vs GEval-as-alignment; r623 macro-F1. "
                "This is 2PL item difficulty vs percent-correct"
            ),
            dump="2PL b table, percent-correct, and CL-12 items",
            first_apply="swap in 1PL Rasch percent-correct",
            plan="Publish Rasch 1PL so a single ability still looks like 0.78.",
            plan_change="fit 2PL a,b; fail if any b>=1.5 or a<0.4",
            goal=(
                "lantern-eval publishes percent_correct=0.78 while 2PL difficulty on CL-12 "
                "refund items is b=2.41. Gate on 2PL b and a. Do not swap in 1PL Rasch. "
                "tests/test_irt2pl.py is the gate."
            ),
            outcome=(
                "Percent-correct 0.78 hid items with 2PL b=2.41. 1PL Rasch still pooled them. "
                "Plan change: fit 2PL; fail if max b>=1.5. Tests 1/1 + 8/8. Residual: "
                "src/pct_dash.py still publishes percent_correct."
            ),
            rg="irt|2pl|difficulty|percent_correct|rasch|discrimination",
            rg_obs=(
                "TICKET.md: pct 0.78 pass; CL-12 b=2.41 unused\n"
                "tests/test_irt2pl.py: def test_2pl_flags_hard_items\n"
                "src/irt2pl.py: gate = mean(correct) >= 0.70\n"
                "goldens/items.jsonl: cl12-40d p=0.08"
            ),
            test="tests/test_irt2pl.py",
            test_name="2pl-flags-hard-items",
            test_body=(
                "def test_2pl_flags_hard_items():\n"
                "    rep = report_irt(ITEMS, RESP)\n"
                "    assert rep['pct'] == pytest.approx(0.78, abs=0.01)\n"
                "    assert rep['max_b'] == pytest.approx(2.41, abs=0.05)\n"
                "    assert rep['min_a'] < 0.4\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'rasch_b' not in rep\n"
            ),
            gate_want="max_b 2.41 and gate fail",
            fail_obs=(
                "FAILED tests/test_irt2pl.py::test_2pl_flags_hard_items"
                " - AssertionError: max_b missing; pct=0.78 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="pct 0.78, no 2PL b",
            src="src/irt2pl.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_irt(items, resp):\n"
                "    pct = mean(resp[i] for i in items)\n"
                "    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}\n"
            ),
            obs5="percent-correct 0.78; CL-12 p=0.08",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('pct', 0.78, 'cl12_p', 0.08, '2pl_b', 2.41, '2pl_a', 0.22)\n"
                "print('1pl_b', 0.31)\n"
                "PY"
            ),
            stats_obs="pct 0.78 cl12_p 0.08 2pl_b 2.41 2pl_a 0.22\n1pl_b 0.31",
            wrong_old="    pct = mean(resp[i] for i in items)\n    return {'pct': pct, 'gate': 'pass' if pct >= 0.70 else 'fail'}",
            wrong_new=(
                "    pct = mean(resp[i] for i in items)\n"
                "    rasch_b = 0.31\n"
                "    return {'pct': pct, 'rasch_b': rasch_b, 'gate': 'pass' if pct >= 0.70 else 'fail'}"
            ),
            wrong_label="1pl-rasch-as-difficulty",
            wrong_still="rasch_b 0.31 still passes",
            still_fail=(
                "FAILED tests/test_irt2pl.py::test_2pl_flags_hard_items"
                " - AssertionError: rasch_b=0.31; max_b missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.irt2pl_fit import fit_2pl\n"
                "\n"
                "def report_irt(items, resp):\n"
                "    pct = mean(resp[i] for i in items)\n"
                "    a, b = fit_2pl(items, resp)\n"
                "    gate = 'fail' if max(b) >= 1.5 or min(a) < 0.4 else 'pass'\n"
                "    return {'pct': pct, 'max_b': max(b), 'min_a': min(a), 'gate': gate}\n"
            ),
            rewrite_obs="2PL a,b fit; fail-closed on b>=1.5",
            helper="src/irt2pl_fit.py",
            fix_helper=(
                "def fit_2pl(items, resp):\n"
                "    # locked demo fit: CL-12 refund items carry b=2.41, a=0.22\n"
                "    a = [0.9 if i != 'cl12-40d' else 0.22 for i in items]\n"
                "    b = [0.2 if i != 'cl12-40d' else 2.41 for i in items]\n"
                "    return a, b\n"
            ),
            helper_obs="fit_2pl returns CL-12 b=2.41",
            test2="tests/test_irt2pl_second.py",
            test2_body=(
                "def test_policy_cluster_2pl():\n"
                "    rep = report_irt(POLICY_ITEMS, POLICY_RESP)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['max_b'] >= 1.5\n"
            ),
            residual="src/pct_dash.py still publishes percent_correct",
            residual_path="src/pct_dash.py",
            residual_pat="percent_correct|max_b",
            residual_obs="src/pct_dash.py: percent_correct = mean(correct)  # leftover\n",
            confirm="max_b and min_a in report",
            final_obs="    return {'pct': pct, 'max_b': max(b), 'min_a': min(a), 'gate': gate}\n",
        ),
        BAD(
            slug="mantel-haenszel-dif",
            seed=(
                "pooled pass 0.81; es-MX vs en-US Mantel-Haenszel chi2=18.4 p<0.001 on "
                "refund items. Per-locale means rejected. Fail if MH p<0.05. Nightly still pooled."
            ),
            avoided=(
                "r621 annotator_id cache; r628 Fleiss among humans. "
                "This is Mantel-Haenszel DIF across locales, not raters"
            ),
            dump="MH table, locale labels, and pooled pass",
            first_apply="report per-locale means both above 0.70",
            plan="Publish es-MX 0.72 and en-US 0.84 so both locales look green.",
            plan_change="Mantel-Haenszel DIF; fail if p<0.05",
            goal=(
                "lantern-eval publishes pooled pass=0.81 while Mantel-Haenszel DIF on refund "
                "items is chi2=18.4 p<0.001 for es-MX vs en-US. Fail if MH p<0.05. Do not "
                "swap in per-locale means. tests/test_mh_dif.py is the gate."
            ),
            outcome=(
                "Pooled 0.81 hid locale DIF chi2=18.4. Per-locale means both cleared 0.70. "
                "Plan change: MH p-value gate. Gate 1/1. Partial: nightly src/nightly_mh.py "
                "still publishes pooled pass (xfail)."
            ),
            rg="mantel|haenszel|dif|locale|es-MX|pooled",
            rg_obs=(
                "TICKET.md: pooled 0.81; es-MX refund MH unused\n"
                "tests/test_mh_dif.py: def test_mh_p_must_fail\n"
                "src/mh_dif.py: gate = pooled >= 0.70\n"
                "goldens/locale.jsonl: es-MX cl12 fail cluster"
            ),
            test="tests/test_mh_dif.py",
            test_name="mh-p-must-fail",
            test_body=(
                "def test_mh_p_must_fail():\n"
                "    rep = report_dif(ITEMS, LOCALE, Y)\n"
                "    assert rep['pooled'] == pytest.approx(0.81, abs=0.01)\n"
                "    assert rep['mh_chi2'] == pytest.approx(18.4, abs=0.3)\n"
                "    assert rep['mh_p'] < 0.05\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'es_mean' not in rep\n"
            ),
            gate_want="mh_p < 0.05 and gate fail",
            fail_obs=(
                "FAILED tests/test_mh_dif.py::test_mh_p_must_fail"
                " - AssertionError: mh_p missing; pooled=0.81 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="pooled 0.81, no MH",
            src="src/mh_dif.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_dif(items, locale, y):\n"
                "    pooled = mean(y[i] for i in items)\n"
                "    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n"
            ),
            obs5="pooled 0.81; es-MX refunds fail",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('pooled', 0.81, 'es_mean', 0.72, 'en_mean', 0.84)\n"
                "print('mh_chi2', 18.4, 'mh_p', 1.8e-5)\n"
                "PY"
            ),
            stats_obs="pooled 0.81 es_mean 0.72 en_mean 0.84\nmh_chi2 18.4 mh_p 1.8e-5",
            wrong_old="    pooled = mean(y[i] for i in items)\n    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}",
            wrong_new=(
                "    pooled = mean(y[i] for i in items)\n"
                "    es = mean(y[i] for i in items if locale[i]=='es-MX')\n"
                "    en = mean(y[i] for i in items if locale[i]=='en-US')\n"
                "    return {'pooled': pooled, 'es_mean': es, 'en_mean': en, 'gate': 'pass' if es>=0.70 and en>=0.70 else 'fail'}"
            ),
            wrong_label="per-locale-means",
            wrong_still="es 0.72 and en 0.84 still pass",
            still_fail=(
                "FAILED tests/test_mh_dif.py::test_mh_p_must_fail"
                " - AssertionError: es_mean=0.72; mh_p missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.mh_stats import mantel_haenszel\n"
                "\n"
                "def report_dif(items, locale, y):\n"
                "    pooled = mean(y[i] for i in items)\n"
                "    chi2, p = mantel_haenszel(items, locale, y)\n"
                "    gate = 'fail' if p < 0.05 else 'pass'\n"
                "    return {'pooled': pooled, 'mh_chi2': chi2, 'mh_p': p, 'gate': gate}\n"
            ),
            rewrite_obs="MH chi2/p gate; fail-closed on DIF",
            helper="src/mh_stats.py",
            fix_helper=(
                "def mantel_haenszel(items, locale, y):\n"
                "    # locked demo: refund stratum chi2=18.4\n"
                "    return 18.4, 1.8e-5\n"
            ),
            helper_obs="mantel_haenszel locked 18.4",
            suite_fail=(
                "FAILED tests/test_nightly_mh.py::test_nightly_uses_mh"
                " - AssertionError: nightly gate=pass pooled=0.81\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_mh.py",
            nightly_test="tests/test_nightly_mh.py",
            nightly_body=(
                "def nightly_report(items, locale, y):\n"
                "    pooled = mean(y[i] for i in items)\n"
                "    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_mh():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_mh.py still publishes pooled", strict=False)\n'
                "def test_nightly_uses_mh():"
            ),
            handoff="nightly pooled-only gate",
            leftover_obs="    return {'pooled': pooled, 'gate': 'pass' if pooled >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r630 CUSUM early-stop vs fixed-n / Hartigan dip bimodality
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="cusum-early-stop",
            seed=(
                "sequential eval stops at n=20 when running mean hits 0.70; full n=80 is 0.54. "
                "Wald SPRT rejected. Always run n=N; CUSUM monitor-only."
            ),
            avoided=(
                "r613 bootstrap CI vs point; r617 Wilson pass@1 n=7. "
                "This is CUSUM/sequential early-stop vs fixed-n"
            ),
            dump="CUSUM stop n=20, full-n 0.54, and sequential gate",
            first_apply="swap in Wald SPRT with wide bounds",
            plan="Use Wald SPRT so optional stopping still looks principled.",
            plan_change="forbid early stop; always n=N; CUSUM monitor-only",
            goal=(
                "lantern-eval stops at n=20 once the running mean crosses 0.70; the full n=80 "
                "mean is 0.54. Always evaluate n=N. Do not swap in Wald SPRT. "
                "tests/test_cusum_stop.py is the gate."
            ),
            outcome=(
                "Early stop at n=20 published 0.72 while n=80 is 0.54. SPRT still stopped. "
                "Plan change: fixed-n only. Tests 1/1 + 8/8. Residual: src/seq_dash.py still "
                "stops at the first green mean."
            ),
            rg="cusum|early.stop|sequential|n=20|running_mean|sprt",
            rg_obs=(
                "TICKET.md: stop n=20 mean 0.72; n=80 mean 0.54\n"
                "tests/test_cusum_stop.py: def test_no_early_stop\n"
                "src/cusum_stop.py: if run_mean >= 0.70: stop\n"
                "goldens/seq.jsonl: first 20 easy, last 60 CL-12"
            ),
            test="tests/test_cusum_stop.py",
            test_name="no-early-stop",
            test_body=(
                "def test_no_early_stop():\n"
                "    rep = report_seq(SCORES, n=80)\n"
                "    assert rep['n_used'] == 80\n"
                "    assert rep['mean'] == pytest.approx(0.54, abs=0.02)\n"
                "    assert rep['stopped_at'] is None\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'sprt' not in rep\n"
            ),
            gate_want="n_used 80, mean 0.54, gate fail",
            fail_obs=(
                "FAILED tests/test_cusum_stop.py::test_no_early_stop"
                " - AssertionError: n_used=20 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="stopped at n=20",
            src="src/cusum_stop.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_seq(scores, n=80):\n"
                "    for k in range(10, n+1, 5):\n"
                "        mu = mean(scores[:k])\n"
                "        if mu >= 0.70:\n"
                "            return {'n_used': k, 'mean': mu, 'stopped_at': k, 'gate': 'pass'}\n"
                "    mu = mean(scores[:n])\n"
                "    return {'n_used': n, 'mean': mu, 'stopped_at': None, 'gate': 'fail'}\n"
            ),
            obs5="running mean crosses 0.70 at n=20",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "from statistics import mean\n"
                "s=[0.86]*20+[0.42]*60\n"
                "print('n20', mean(s[:20]), 'n80', mean(s))\n"
                "PY"
            ),
            stats_obs="n20 0.86 n80 0.53",
            wrong_old="        if mu >= 0.70:\n            return {'n_used': k, 'mean': mu, 'stopped_at': k, 'gate': 'pass'}",
            wrong_new=(
                "        if mu >= 0.70:  # SPRT wide bound\n"
                "            return {'n_used': k, 'mean': mu, 'stopped_at': k, 'sprt': True, 'gate': 'pass'}"
            ),
            wrong_label="wald-sprt-wide",
            wrong_still="SPRT still stops at n=20",
            still_fail=(
                "FAILED tests/test_cusum_stop.py::test_no_early_stop"
                " - AssertionError: sprt=True n_used=20\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.cusum_mon import cusum_alerts\n"
                "\n"
                "def report_seq(scores, n=80):\n"
                "    used = scores[:n]\n"
                "    mu = mean(used)\n"
                "    alerts = cusum_alerts(used, target=0.70)\n"
                "    gate = 'pass' if mu >= 0.70 else 'fail'\n"
                "    return {'n_used': n, 'mean': mu, 'stopped_at': None, 'cusum_alerts': alerts, 'gate': gate}\n"
            ),
            rewrite_obs="fixed n=80; CUSUM alerts only",
            helper="src/cusum_mon.py",
            fix_helper=(
                "def cusum_alerts(scores, target=0.70):\n"
                "    s = 0.0\n"
                "    out = []\n"
                "    for i, x in enumerate(scores, 1):\n"
                "        s = max(0.0, s + (target - x))\n"
                "        if s > 2.0:\n"
                "            out.append(i)\n"
                "    return out\n"
            ),
            helper_obs="cusum_alerts monitor-only",
            test2="tests/test_cusum_stop_second.py",
            test2_body=(
                "def test_prefix_easy_still_full_n():\n"
                "    rep = report_seq(EASY_THEN_HARD, n=80)\n"
                "    assert rep['n_used'] == 80\n"
                "    assert rep['stopped_at'] is None\n"
            ),
            residual="src/seq_dash.py still stops at first green mean",
            residual_path="src/seq_dash.py",
            residual_pat="stopped_at|running_mean",
            residual_obs="src/seq_dash.py: if running_mean >= 0.70: publish_pass()\n",
            confirm="n_used 80 and stopped_at None",
            final_obs="    return {'n_used': n, 'mean': mu, 'stopped_at': None, 'cusum_alerts': alerts, 'gate': gate}\n",
        ),
        BAD(
            slug="hartigan-dip-bimodal",
            seed=(
                "mean 0.74 green; Hartigan dip p=0.002 with modes at 0.12 and 0.91. "
                "Median rejected. Fail if dip p<0.05; publish both modes. Nightly still mean."
            ),
            avoided=(
                "r613 bootstrap CI vs point mean; r626 self-consistency majority. "
                "This is Hartigan dip test of bimodality vs a unimodal mean"
            ),
            dump="Hartigan dip p, two modes, and mean gate",
            first_apply="publish the median of the two modes",
            plan="Publish median 0.76 so the 0.12 mode cannot drag the gate.",
            plan_change="fail if Hartigan dip p<0.05; publish both modes",
            goal=(
                "lantern-eval marks tone pass on mean 0.74 while Hartigan dip p=0.002 shows "
                "modes at 0.12 and 0.91. Fail if dip p<0.05. Do not swap in the median. "
                "tests/test_dip.py is the gate."
            ),
            outcome=(
                "Mean 0.74 hid a bimodal 0.12/0.91 split. Median 0.76 still passed. Plan "
                "change: dip-test gate. Gate 1/1. Partial: nightly src/nightly_dip.py still "
                "publishes mean (xfail)."
            ),
            rg="hartigan|dip.test|bimodal|modes|unimodal",
            rg_obs=(
                "TICKET.md: mean 0.74; dip p=0.002 unused\n"
                "tests/test_dip.py: def test_dip_flags_bimodal\n"
                "src/dip.py: gate = mean(scores) >= 0.70\n"
                "goldens/tone.jsonl: 18 at 0.12, 22 at 0.91"
            ),
            test="tests/test_dip.py",
            test_name="dip-flags-bimodal",
            test_body=(
                "def test_dip_flags_bimodal():\n"
                "    rep = report_dip(SCORES)\n"
                "    assert rep['mean'] == pytest.approx(0.74, abs=0.02)\n"
                "    assert rep['dip_p'] < 0.05\n"
                "    assert rep['modes'][0] == pytest.approx(0.12, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'median' not in rep\n"
            ),
            gate_want="dip_p < 0.05 and gate fail",
            fail_obs=(
                "FAILED tests/test_dip.py::test_dip_flags_bimodal"
                " - AssertionError: dip_p missing; mean=0.74 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="mean 0.74, no dip",
            src="src/dip.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_dip(scores):\n"
                "    mu = mean(scores)\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            obs5="mean 0.74; two clumps 0.12 and 0.91",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "from statistics import mean, median\n"
                "s=[0.12]*18+[0.91]*22\n"
                "print('mean', round(mean(s),3), 'median', median(s), 'n', len(s))\n"
                "print('dip_p', 0.002)\n"
                "PY"
            ),
            stats_obs="mean 0.754 median 0.91 n 40\ndip_p 0.002",
            wrong_old="    mu = mean(scores)\n    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}",
            wrong_new=(
                "    from statistics import median\n"
                "    mu = mean(scores)\n"
                "    med = median(scores)\n"
                "    return {'mean': mu, 'median': med, 'gate': 'pass' if med >= 0.70 else 'fail'}"
            ),
            wrong_label="median-of-modes",
            wrong_still="median 0.91 still passes",
            still_fail=(
                "FAILED tests/test_dip.py::test_dip_flags_bimodal"
                " - AssertionError: median=0.91; dip_p missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.dip_stats import hartigan_dip, modes2\n"
                "\n"
                "def report_dip(scores):\n"
                "    mu = mean(scores)\n"
                "    p = hartigan_dip(scores)\n"
                "    m0, m1 = modes2(scores)\n"
                "    gate = 'fail' if p < 0.05 else ('pass' if mu >= 0.70 else 'fail')\n"
                "    return {'mean': mu, 'dip_p': p, 'modes': (m0, m1), 'gate': gate}\n"
            ),
            rewrite_obs="Hartigan dip gate; modes published",
            helper="src/dip_stats.py",
            fix_helper=(
                "def hartigan_dip(scores):\n"
                "    return 0.002\n"
                "\n"
                "def modes2(scores):\n"
                "    return min(scores), max(scores)\n"
            ),
            helper_obs="hartigan_dip locked p=0.002",
            suite_fail=(
                "FAILED tests/test_nightly_dip.py::test_nightly_uses_dip"
                " - AssertionError: nightly gate=pass mean=0.74\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_dip.py",
            nightly_test="tests/test_nightly_dip.py",
            nightly_body=(
                "def nightly_report(scores):\n"
                "    mu = mean(scores)\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_dip():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_dip.py still publishes mean", strict=False)\n'
                "def test_nightly_uses_dip():"
            ),
            handoff="nightly mean-only gate",
            leftover_obs="    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r631 Angoff cut vs arbitrary 0.70 / extra-binomial phi overdispersion
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="angoff-vs-arb-cut",
            seed=(
                "SME Angoff mean p=0.82 recommended cut; gate still 0.70. Bookmark 0.74 "
                "rejected. Freeze Angoff from the SME panel."
            ),
            avoided=(
                "r619 nested CV threshold on the same 80 rows; r08 strictmode. "
                "This is Angoff standard-setting vs an arbitrary 0.70 cut"
            ),
            dump="Angoff SME p-bar, 0.70 gate, and Bookmark note",
            first_apply="swap in Bookmark cut 0.74",
            plan="Use Bookmark 0.74 so the cut moves without reconvening SMEs.",
            plan_change="freeze Angoff cut from the SME panel; fail below it",
            goal=(
                "lantern-eval gates at 0.70 while the SME Angoff recommended cut is 0.82. "
                "Freeze the Angoff cut. Do not swap in Bookmark. tests/test_angoff.py is the gate."
            ),
            outcome=(
                "Arbitrary 0.70 passed a 0.76 mean the SMEs would fail at 0.82. Bookmark 0.74 "
                "still passed. Plan change: freeze Angoff. Tests 1/1 + 8/8. Residual: "
                "src/cut_dash.py still hardcodes 0.70."
            ),
            rg="angoff|bookmark|cut_score|sme|standard.setting",
            rg_obs=(
                "TICKET.md: SME Angoff 0.82; gate 0.70\n"
                "tests/test_angoff.py: def test_angoff_cut_frozen\n"
                "src/angoff.py: gate = mean >= 0.70\n"
                "goldens/sme.json: 8 SMEs p-bar 0.82"
            ),
            test="tests/test_angoff.py",
            test_name="angoff-cut-frozen",
            test_body=(
                "def test_angoff_cut_frozen():\n"
                "    rep = report_cut(SCORES, SME_P)\n"
                "    assert rep['angoff'] == pytest.approx(0.82, abs=0.01)\n"
                "    assert rep['mean'] == pytest.approx(0.76, abs=0.01)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'bookmark' not in rep\n"
            ),
            gate_want="angoff 0.82, mean 0.76, gate fail",
            fail_obs=(
                "FAILED tests/test_angoff.py::test_angoff_cut_frozen"
                " - AssertionError: gate=pass cut=0.70\n"
                "0 passed, 1 failed"
            ),
            fail_short="cut 0.70 still in use",
            src="src/angoff.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_cut(scores, sme_p):\n"
                "    mu = mean(scores)\n"
                "    return {'mean': mu, 'cut': 0.70, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            obs5="mean 0.76; SME p-bar 0.82",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "from statistics import mean\n"
                "print('mean', 0.76, 'angoff', 0.82, 'bookmark', 0.74)\n"
                "PY"
            ),
            stats_obs="mean 0.76 angoff 0.82 bookmark 0.74",
            wrong_old="    return {'mean': mu, 'cut': 0.70, 'gate': 'pass' if mu >= 0.70 else 'fail'}",
            wrong_new="    return {'mean': mu, 'cut': 0.74, 'bookmark': 0.74, 'gate': 'pass' if mu >= 0.74 else 'fail'}",
            wrong_label="bookmark-cut",
            wrong_still="bookmark 0.74 still passes 0.76",
            still_fail=(
                "FAILED tests/test_angoff.py::test_angoff_cut_frozen"
                " - AssertionError: bookmark=0.74; angoff missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.angoff_sme import angoff_cut\n"
                "\n"
                "def report_cut(scores, sme_p):\n"
                "    mu = mean(scores)\n"
                "    cut = angoff_cut(sme_p)\n"
                "    gate = 'pass' if mu >= cut else 'fail'\n"
                "    return {'mean': mu, 'angoff': cut, 'gate': gate}\n"
            ),
            rewrite_obs="Angoff cut frozen from SME p-bar",
            helper="src/angoff_sme.py",
            fix_helper=(
                "from statistics import mean\n"
                "\n"
                "def angoff_cut(sme_p):\n"
                "    return float(mean(sme_p))\n"
            ),
            helper_obs="angoff_cut = mean of SME p",
            test2="tests/test_angoff_second.py",
            test2_body=(
                "def test_sme_panel_locked():\n"
                "    rep = report_cut(SCORES, SME_P)\n"
                "    assert rep['angoff'] >= 0.80\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            residual="src/cut_dash.py still hardcodes 0.70",
            residual_path="src/cut_dash.py",
            residual_pat="0.70|angoff",
            residual_obs="src/cut_dash.py: CUT = 0.70  # leftover product default\n",
            confirm="angoff key and no bookmark",
            final_obs="    return {'mean': mu, 'angoff': cut, 'gate': gate}\n",
        ),
        BAD(
            slug="extrabinom-phi",
            seed=(
                "pass-rate 0.72 n=80 treated as binomial; quasi-likelihood phi=2.6. "
                "Ignore-phi rejected. Fail if phi>1.5. Nightly still binomial variance."
            ),
            avoided=(
                "r617 Wilson interval on pass@1 n=7; r613 bootstrap mean CI. "
                "This is extra-binomial overdispersion phi vs binomial variance"
            ),
            dump="phi overdispersion, pass-rate 0.72, and binomial var",
            first_apply="ignore phi and keep binomial var",
            plan="Keep binomial variance and note phi in a comment.",
            plan_change="fail if extra-binomial phi>1.5",
            goal=(
                "lantern-eval treats pass-rate 0.72 as binomial while quasi-likelihood phi=2.6. "
                "Fail if phi>1.5. Do not ignore phi. tests/test_phi.py is the gate."
            ),
            outcome=(
                "Binomial variance understated clustered fails. Commenting phi left the gate "
                "green. Plan change: fail if phi>1.5. Gate 1/1. Partial: nightly "
                "src/nightly_phi.py still uses binomial var (xfail)."
            ),
            rg="overdispersion|quasi.likelihood|phi|extrabinom|binomial",
            rg_obs=(
                "TICKET.md: p=0.72; phi=2.6 unused\n"
                "tests/test_phi.py: def test_phi_must_fail\n"
                "src/phi.py: var = p*(1-p)/n\n"
                "goldens/cluster.jsonl: 12 CL-12 fails in one batch"
            ),
            test="tests/test_phi.py",
            test_name="phi-must-fail",
            test_body=(
                "def test_phi_must_fail():\n"
                "    rep = report_phi(Y)\n"
                "    assert rep['p'] == pytest.approx(0.72, abs=0.01)\n"
                "    assert rep['phi'] == pytest.approx(2.6, abs=0.2)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'note' not in rep\n"
            ),
            gate_want="phi 2.6 and gate fail",
            fail_obs=(
                "FAILED tests/test_phi.py::test_phi_must_fail"
                " - AssertionError: phi missing; p=0.72 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="binomial var, no phi",
            src="src/phi.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_phi(y):\n"
                "    p = mean(y)\n"
                "    n = len(y)\n"
                "    var = p * (1 - p) / n\n"
                "    return {'p': p, 'var': var, 'gate': 'pass' if p >= 0.70 else 'fail'}\n"
            ),
            obs5="p=0.72; clustered batches inflate phi",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('p', 0.72, 'binom_var', 0.0025, 'phi', 2.6)\n"
                "PY"
            ),
            stats_obs="p 0.72 binom_var 0.0025 phi 2.6",
            wrong_old="    return {'p': p, 'var': var, 'gate': 'pass' if p >= 0.70 else 'fail'}",
            wrong_new="    return {'p': p, 'var': var, 'note': 'phi~2.6 ignored', 'gate': 'pass' if p >= 0.70 else 'fail'}",
            wrong_label="phi-in-a-note",
            wrong_still="note does not fail the gate",
            still_fail=(
                "FAILED tests/test_phi.py::test_phi_must_fail"
                " - AssertionError: note present; phi missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.phi_fit import quasi_phi\n"
                "\n"
                "def report_phi(y):\n"
                "    p = mean(y)\n"
                "    phi = quasi_phi(y)\n"
                "    gate = 'fail' if phi > 1.5 else ('pass' if p >= 0.70 else 'fail')\n"
                "    return {'p': p, 'phi': phi, 'gate': gate}\n"
            ),
            rewrite_obs="quasi-likelihood phi gate",
            helper="src/phi_fit.py",
            fix_helper=(
                "def quasi_phi(y):\n"
                "    # locked demo: clustered CL-12 batches => phi=2.6\n"
                "    return 2.6\n"
            ),
            helper_obs="quasi_phi locked 2.6",
            suite_fail=(
                "FAILED tests/test_nightly_phi.py::test_nightly_uses_phi"
                " - AssertionError: nightly gate=pass p=0.72\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_phi.py",
            nightly_test="tests/test_nightly_phi.py",
            nightly_body=(
                "def nightly_report(y):\n"
                "    p = mean(y)\n"
                "    return {'p': p, 'gate': 'pass' if p >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_phi():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_phi.py still binomial", strict=False)\n'
                "def test_nightly_uses_phi():"
            ),
            handoff="nightly binomial-variance gate",
            leftover_obs="    return {'p': p, 'gate': 'pass' if p >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r632 MMLU-redux errata vs original / IFEval strict vs loose
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="mmlu-redux-errata",
            seed=(
                "original MMLU 0.79; MMLU-redux corrected keys 0.61. Drop-contested "
                "rejected. Apply redux keys; fail if redux<0.70."
            ),
            avoided=(
                "r615 train/eval id-set leak; r626 HF split=test name leak. "
                "This is MMLU-redux answer-key errata vs original MMLU"
            ),
            dump="MMLU original 0.79, redux 0.61, and errata keys",
            first_apply="drop contested MMLU items",
            plan="Drop the 14 contested items so original 0.79 still stands.",
            plan_change="apply redux answer keys; fail if redux<0.70",
            goal=(
                "lantern-eval publishes MMLU 0.79 on original keys while MMLU-redux corrected "
                "keys score 0.61. Apply redux keys. Do not drop contested items. "
                "tests/test_mmlu_redux.py is the gate."
            ),
            outcome=(
                "Original keys 0.79 hid errata. Dropping contested items kept 0.81. Plan "
                "change: apply redux keys. Tests 1/1 + 8/8. Residual: src/mmlu_dash.py still "
                "loads original."
            ),
            rg="mmlu-redux|errata|answer_key|contested|original MMLU",
            rg_obs=(
                "TICKET.md: MMLU 0.79 original; redux 0.61 unused\n"
                "tests/test_mmlu_redux.py: def test_redux_keys_required\n"
                "src/mmlu_redux.py: acc = grade(original_keys)\n"
                "goldens/mmlu_errata.json: 14 flipped keys"
            ),
            test="tests/test_mmlu_redux.py",
            test_name="redux-keys-required",
            test_body=(
                "def test_redux_keys_required():\n"
                "    rep = report_mmlu(PRED, ORIGINAL, REDUX)\n"
                "    assert rep['original'] == pytest.approx(0.79, abs=0.01)\n"
                "    assert rep['redux'] == pytest.approx(0.61, abs=0.01)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'dropped' not in rep\n"
            ),
            gate_want="redux 0.61 and gate fail",
            fail_obs=(
                "FAILED tests/test_mmlu_redux.py::test_redux_keys_required"
                " - AssertionError: redux missing; original=0.79 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="original keys only",
            src="src/mmlu_redux.py",
            src_body=(
                "def report_mmlu(pred, original, redux):\n"
                "    acc = sum(pred[i]==original[i] for i in pred) / len(pred)\n"
                "    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            obs5="original 0.79; 14 keys flipped in redux",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('original', 0.79, 'redux', 0.61, 'dropped_acc', 0.81)\n"
                "PY"
            ),
            stats_obs="original 0.79 redux 0.61 dropped_acc 0.81",
            wrong_old="    acc = sum(pred[i]==original[i] for i in pred) / len(pred)\n    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}",
            wrong_new=(
                "    keep = [i for i in pred if i not in CONTESTED]\n"
                "    acc = sum(pred[i]==original[i] for i in keep) / len(keep)\n"
                "    return {'original': acc, 'dropped': len(CONTESTED), 'gate': 'pass' if acc >= 0.70 else 'fail'}"
            ),
            wrong_label="drop-contested",
            wrong_still="dropped-set 0.81 still passes",
            still_fail=(
                "FAILED tests/test_mmlu_redux.py::test_redux_keys_required"
                " - AssertionError: dropped=14; redux missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.mmlu_keys import grade_keys\n"
                "\n"
                "def report_mmlu(pred, original, redux):\n"
                "    orig = grade_keys(pred, original)\n"
                "    red = grade_keys(pred, redux)\n"
                "    gate = 'pass' if red >= 0.70 else 'fail'\n"
                "    return {'original': orig, 'redux': red, 'gate': gate}\n"
            ),
            rewrite_obs="redux keys required for the gate",
            helper="src/mmlu_keys.py",
            fix_helper=(
                "def grade_keys(pred, keys):\n"
                "    return sum(pred[i]==keys[i] for i in pred) / len(pred)\n"
            ),
            helper_obs="grade_keys against a chosen key set",
            test2="tests/test_mmlu_redux_second.py",
            test2_body=(
                "def test_redux_stem_cluster():\n"
                "    rep = report_mmlu(STEM_PRED, STEM_ORIG, STEM_REDUX)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['redux'] < 0.70\n"
            ),
            residual="src/mmlu_dash.py still loads original",
            residual_path="src/mmlu_dash.py",
            residual_pat="original|redux",
            residual_obs="src/mmlu_dash.py: acc = grade(original_keys)  # leftover\n",
            confirm="redux key in report",
            final_obs="    return {'original': orig, 'redux': red, 'gate': gate}\n",
        ),
        BAD(
            slug="ifeval-strict-vs-loose",
            seed=(
                "IFEval loose 0.91 published; strict 0.44. Average loose+strict rejected. "
                "Gate on strict. Nightly still loose."
            ),
            avoided=(
                "r619 promptfoo llm-rubric vs exact; r04 promptfoo-vs-geval. "
                "This is IFEval strict vs loose instruction following"
            ),
            dump="IFEval loose 0.91, strict 0.44, and mix gate",
            first_apply="average loose and strict IFEval",
            plan="Average 0.91 and 0.44 so a 0.675 blend still looks like progress.",
            plan_change="gate on strict; publish both",
            goal=(
                "lantern-eval publishes IFEval 0.91 from the loose scorer while strict is 0.44. "
                "Gate on strict. Do not average the two. tests/test_ifeval.py is the gate."
            ),
            outcome=(
                "Loose 0.91 hid strict 0.44. Averaging to 0.675 still passed 0.60. Plan "
                "change: gate on strict. Gate 1/1. Partial: nightly src/nightly_ifeval.py "
                "still publishes loose (xfail)."
            ),
            rg="ifeval|strict|loose|instruction.follow",
            rg_obs=(
                "TICKET.md: IFEval 0.91 loose; strict 0.44 unused\n"
                "tests/test_ifeval.py: def test_strict_must_gate\n"
                "src/ifeval.py: acc = loose_score(outputs)\n"
                "goldens/ifeval.jsonl: punctuation/case fails only in strict"
            ),
            test="tests/test_ifeval.py",
            test_name="strict-must-gate",
            test_body=(
                "def test_strict_must_gate():\n"
                "    rep = report_ifeval(ROWS)\n"
                "    assert rep['loose'] == pytest.approx(0.91, abs=0.01)\n"
                "    assert rep['strict'] == pytest.approx(0.44, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'blend' not in rep\n"
            ),
            gate_want="strict 0.44 and gate fail",
            fail_obs=(
                "FAILED tests/test_ifeval.py::test_strict_must_gate"
                " - AssertionError: strict missing; loose=0.91 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="loose-only 0.91",
            src="src/ifeval.py",
            src_body=(
                "def report_ifeval(rows):\n"
                "    loose = mean(r['loose'] for r in rows)\n"
                "    return {'loose': loose, 'gate': 'pass' if loose >= 0.70 else 'fail'}\n"
            ),
            obs5="loose 0.91; strict punctuation fails",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('loose', 0.91, 'strict', 0.44, 'blend', 0.675)\n"
                "PY"
            ),
            stats_obs="loose 0.91 strict 0.44 blend 0.675",
            wrong_old="    loose = mean(r['loose'] for r in rows)\n    return {'loose': loose, 'gate': 'pass' if loose >= 0.70 else 'fail'}",
            wrong_new=(
                "    loose = mean(r['loose'] for r in rows)\n"
                "    strict = mean(r['strict'] for r in rows)\n"
                "    blend = 0.5 * (loose + strict)\n"
                "    return {'loose': loose, 'blend': blend, 'gate': 'pass' if blend >= 0.60 else 'fail'}"
            ),
            wrong_label="loose-strict-blend",
            wrong_still="blend 0.675 still passes 0.60",
            still_fail=(
                "FAILED tests/test_ifeval.py::test_strict_must_gate"
                " - AssertionError: blend=0.675; strict missing as gate\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.ifeval_score import strict_of, loose_of\n"
                "\n"
                "def report_ifeval(rows):\n"
                "    loose = mean(loose_of(r) for r in rows)\n"
                "    strict = mean(strict_of(r) for r in rows)\n"
                "    gate = 'pass' if strict >= 0.70 else 'fail'\n"
                "    return {'loose': loose, 'strict': strict, 'gate': gate}\n"
            ),
            rewrite_obs="strict is the gate; both published",
            helper="src/ifeval_score.py",
            fix_helper=(
                "def loose_of(row):\n"
                "    return float(row['loose'])\n"
                "\n"
                "def strict_of(row):\n"
                "    return float(row['strict'])\n"
            ),
            helper_obs="strict_of / loose_of accessors",
            suite_fail=(
                "FAILED tests/test_nightly_ifeval.py::test_nightly_uses_strict"
                " - AssertionError: nightly gate=pass loose=0.91\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_ifeval.py",
            nightly_test="tests/test_nightly_ifeval.py",
            nightly_body=(
                "def nightly_report(rows):\n"
                "    loose = mean(r['loose'] for r in rows)\n"
                "    return {'loose': loose, 'gate': 'pass' if loose >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_strict():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_ifeval.py still loose", strict=False)\n'
                "def test_nightly_uses_strict():"
            ),
            handoff="nightly loose-only IFEval",
            leftover_obs="    return {'loose': loose, 'gate': 'pass' if loose >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r633 SWE-bench fail-to-pass vs pass-to-pass / HumanEval+ mutations
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="swebench-ftp-vs-ptp",
            seed=(
                "resolved 0.31 counts fail-to-pass only; pass-to-pass regressions drop it to "
                "0.08. Count-ptp-as-resolved rejected. Require ftp AND no ptp fail."
            ),
            avoided=(
                "r622 model-generated gold tautology; r05 synth-expected-is-source. "
                "This is SWE-bench fail-to-pass vs pass-to-pass regressions"
            ),
            dump="ftp 0.31, ptp regressions, and resolved field",
            first_apply="count pass-to-pass as resolved too",
            plan="Treat pass-to-pass as resolved so the 0.31 does not shrink.",
            plan_change="resolved = ftp AND no ptp fail",
            goal=(
                "lantern-eval publishes SWE-bench resolved=0.31 from fail-to-pass only while "
                "pass-to-pass regressions drop resolved to 0.08. Require ftp and no ptp fail. "
                "Do not count ptp as resolved. tests/test_swe_ftp.py is the gate."
            ),
            outcome=(
                "ftp-only 0.31 hid ptp regressions. Counting ptp as resolved inflated 0.40. "
                "Plan change: ftp AND not ptp-fail. Tests 1/1 + 8/8. Residual: "
                "src/swe_dash.py still uses ftp-only."
            ),
            rg="fail-to-pass|pass-to-pass|resolved|swe-bench|ptp|ftp",
            rg_obs=(
                "TICKET.md: resolved 0.31 ftp-only; ptp regressions unused\n"
                "tests/test_swe_ftp.py: def test_ptp_blocks_resolved\n"
                "src/swe_ftp.py: resolved = ftp_rate\n"
                "goldens/swe.jsonl: 9 ptp fails after patch"
            ),
            test="tests/test_swe_ftp.py",
            test_name="ptp-blocks-resolved",
            test_body=(
                "def test_ptp_blocks_resolved():\n"
                "    rep = report_swe(ROWS)\n"
                "    assert rep['ftp'] == pytest.approx(0.31, abs=0.01)\n"
                "    assert rep['resolved'] == pytest.approx(0.08, abs=0.02)\n"
                "    assert rep['ptp_fail'] >= 1\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            gate_want="resolved 0.08 and gate fail",
            fail_obs=(
                "FAILED tests/test_swe_ftp.py::test_ptp_blocks_resolved"
                " - AssertionError: resolved=0.31 ftp-only gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="ftp-only resolved 0.31",
            src="src/swe_ftp.py",
            src_body=(
                "def report_swe(rows):\n"
                "    ftp = mean(r['ftp'] for r in rows)\n"
                "    return {'ftp': ftp, 'resolved': ftp, 'gate': 'pass' if ftp >= 0.25 else 'fail'}\n"
            ),
            obs5="ftp 0.31; 9 ptp fails after patch",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('ftp', 0.31, 'ptp_fail', 9, 'resolved_both', 0.08)\n"
                "PY"
            ),
            stats_obs="ftp 0.31 ptp_fail 9 resolved_both 0.08",
            wrong_old="    ftp = mean(r['ftp'] for r in rows)\n    return {'ftp': ftp, 'resolved': ftp, 'gate': 'pass' if ftp >= 0.25 else 'fail'}",
            wrong_new=(
                "    ftp = mean(r['ftp'] for r in rows)\n"
                "    ptp = mean(r['ptp'] for r in rows)\n"
                "    resolved = max(ftp, ptp)\n"
                "    return {'ftp': ftp, 'resolved': resolved, 'gate': 'pass' if resolved >= 0.25 else 'fail'}"
            ),
            wrong_label="count-ptp-as-resolved",
            wrong_still="max(ftp,ptp) inflates resolved",
            still_fail=(
                "FAILED tests/test_swe_ftp.py::test_ptp_blocks_resolved"
                " - AssertionError: resolved inflated via ptp\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.swe_res import resolved_of\n"
                "\n"
                "def report_swe(rows):\n"
                "    ftp = mean(r['ftp'] for r in rows)\n"
                "    ptp_fail = sum(1 for r in rows if r.get('ptp_fail'))\n"
                "    resolved = mean(resolved_of(r) for r in rows)\n"
                "    gate = 'fail' if ptp_fail else ('pass' if resolved >= 0.25 else 'fail')\n"
                "    return {'ftp': ftp, 'resolved': resolved, 'ptp_fail': ptp_fail, 'gate': gate}\n"
            ),
            rewrite_obs="resolved requires ftp and no ptp fail",
            helper="src/swe_res.py",
            fix_helper=(
                "def resolved_of(row):\n"
                "    return 1.0 if row.get('ftp') and not row.get('ptp_fail') else 0.0\n"
            ),
            helper_obs="resolved_of = ftp and not ptp_fail",
            test2="tests/test_swe_ftp_second.py",
            test2_body=(
                "def test_repo_cluster_ptp():\n"
                "    rep = report_swe(REPO_ROWS)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['ptp_fail'] >= 1\n"
            ),
            residual="src/swe_dash.py still uses ftp-only",
            residual_path="src/swe_dash.py",
            residual_pat="resolved|ftp",
            residual_obs="src/swe_dash.py: resolved = ftp_rate  # leftover\n",
            confirm="resolved and ptp_fail keys",
            final_obs="    return {'ftp': ftp, 'resolved': resolved, 'ptp_fail': ptp_fail, 'gate': gate}\n",
        ),
        BAD(
            slug="humaneval-plus-mut",
            seed=(
                "HumanEval 0.88; evalplus HumanEval+ 0.41. Pin-original rejected. Run "
                "mutations; fail if plus<0.70. Nightly still original."
            ),
            avoided=(
                "r622 model-generated gold; r05 synth expected copies context. "
                "This is HumanEval+ mutated tests vs original HumanEval"
            ),
            dump="HumanEval 0.88, HumanEval+ 0.41, and mutation suite",
            first_apply="pin HumanEval original tests",
            plan="Pin the original HumanEval tests so 0.88 stays the published number.",
            plan_change="run evalplus mutations; fail if plus<0.70",
            goal=(
                "lantern-eval publishes HumanEval 0.88 while HumanEval+ mutated tests score "
                "0.41. Run evalplus. Do not pin original tests. tests/test_he_plus.py is the gate."
            ),
            outcome=(
                "Original 0.88 hid mutation fails. Pinning original kept 0.88. Plan change: "
                "evalplus gate. Gate 1/1. Partial: nightly src/nightly_he.py still original "
                "(xfail)."
            ),
            rg="humaneval\\+|evalplus|mutation|plus_acc|original tests",
            rg_obs=(
                "TICKET.md: HE 0.88; HE+ 0.41 unused\n"
                "tests/test_he_plus.py: def test_plus_must_gate\n"
                "src/he_plus.py: acc = original_he(preds)\n"
                "goldens/evalplus.json: extra asserts on edge cases"
            ),
            test="tests/test_he_plus.py",
            test_name="plus-must-gate",
            test_body=(
                "def test_plus_must_gate():\n"
                "    rep = report_he(PREDS)\n"
                "    assert rep['original'] == pytest.approx(0.88, abs=0.01)\n"
                "    assert rep['plus'] == pytest.approx(0.41, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'pinned' not in rep\n"
            ),
            gate_want="plus 0.41 and gate fail",
            fail_obs=(
                "FAILED tests/test_he_plus.py::test_plus_must_gate"
                " - AssertionError: plus missing; original=0.88 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="original HE only",
            src="src/he_plus.py",
            src_body=(
                "def report_he(preds):\n"
                "    acc = original_he(preds)\n"
                "    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            obs5="original 0.88; plus extra asserts fail",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('original', 0.88, 'plus', 0.41)\n"
                "PY"
            ),
            stats_obs="original 0.88 plus 0.41",
            wrong_old="    acc = original_he(preds)\n    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}",
            wrong_new="    acc = original_he(preds)\n    return {'original': acc, 'pinned': True, 'gate': 'pass' if acc >= 0.70 else 'fail'}",
            wrong_label="pin-original-he",
            wrong_still="pinned original still 0.88",
            still_fail=(
                "FAILED tests/test_he_plus.py::test_plus_must_gate"
                " - AssertionError: pinned=True; plus missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.he_evalplus import original_he, plus_he\n"
                "\n"
                "def report_he(preds):\n"
                "    orig = original_he(preds)\n"
                "    plus = plus_he(preds)\n"
                "    gate = 'pass' if plus >= 0.70 else 'fail'\n"
                "    return {'original': orig, 'plus': plus, 'gate': gate}\n"
            ),
            rewrite_obs="evalplus plus is the gate",
            helper="src/he_evalplus.py",
            fix_helper=(
                "def original_he(preds):\n"
                "    return 0.88\n"
                "\n"
                "def plus_he(preds):\n"
                "    return 0.41\n"
            ),
            helper_obs="plus_he locked 0.41",
            suite_fail=(
                "FAILED tests/test_nightly_he.py::test_nightly_uses_plus"
                " - AssertionError: nightly gate=pass original=0.88\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_he.py",
            nightly_test="tests/test_nightly_he.py",
            nightly_body=(
                "def nightly_report(preds):\n"
                "    acc = original_he(preds)\n"
                "    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_plus():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_he.py still original HE", strict=False)\n'
                "def test_nightly_uses_plus():"
            ),
            handoff="nightly original-HumanEval gate",
            leftover_obs="    return {'original': acc, 'gate': 'pass' if acc >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r634 FActScore atomic vs overall / split-conformal coverage
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="factscore-atomic-vs-ovr",
            seed=(
                "overall claim 0.86; atomic fact precision 0.39 on catalog numbers. "
                "Overall-only rejected. Gate on atomic precision."
            ),
            avoided=(
                "r625 per-turn kappa vs ConversationalGEval; r10 last-turn relevancy. "
                "This is FActScore atomic facts vs overall claim score"
            ),
            dump="atomic precision 0.39, overall 0.86, and catalog numbers",
            first_apply="gate on overall claim score",
            plan="Keep overall 0.86 as the published factuality number.",
            plan_change="gate on atomic fact precision; fail if <0.70",
            goal=(
                "lantern-eval publishes factuality=0.86 overall while atomic FActScore on "
                "catalog numbers is 0.39. Gate on atomic precision. Do not keep overall-only. "
                "tests/test_fact_atomic.py is the gate."
            ),
            outcome=(
                "Overall 0.86 hid atomic 0.39 on catalog numbers. Overall-only stayed green. "
                "Plan change: atomic precision gate. Tests 1/1 + 8/8. Residual: "
                "src/fact_dash.py still prints overall."
            ),
            rg="factscore|atomic|overall_claim|catalog numbers|precision",
            rg_obs=(
                "TICKET.md: overall 0.86; atomic 0.39 on catalog amounts\n"
                "tests/test_fact_atomic.py: def test_atomic_must_gate\n"
                "src/fact_atomic.py: score = overall_claim(text)\n"
                "goldens/facts.jsonl: 11 atomic number errors"
            ),
            test="tests/test_fact_atomic.py",
            test_name="atomic-must-gate",
            test_body=(
                "def test_atomic_must_gate():\n"
                "    rep = report_facts(DOCS)\n"
                "    assert rep['overall'] == pytest.approx(0.86, abs=0.01)\n"
                "    assert rep['atomic'] == pytest.approx(0.39, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            gate_want="atomic 0.39 and gate fail",
            fail_obs=(
                "FAILED tests/test_fact_atomic.py::test_atomic_must_gate"
                " - AssertionError: atomic missing; overall=0.86 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="overall-only 0.86",
            src="src/fact_atomic.py",
            src_body=(
                "def report_facts(docs):\n"
                "    overall = mean(d['overall'] for d in docs)\n"
                "    return {'overall': overall, 'gate': 'pass' if overall >= 0.70 else 'fail'}\n"
            ),
            obs5="overall 0.86; 11 atomic number errors",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('overall', 0.86, 'atomic', 0.39, 'n_bad_atoms', 11)\n"
                "PY"
            ),
            stats_obs="overall 0.86 atomic 0.39 n_bad_atoms 11",
            wrong_old="    overall = mean(d['overall'] for d in docs)\n    return {'overall': overall, 'gate': 'pass' if overall >= 0.70 else 'fail'}",
            wrong_new=(
                "    overall = mean(d['overall'] for d in docs)\n"
                "    return {'overall': overall, 'claim': overall, 'gate': 'pass' if overall >= 0.70 else 'fail'}"
            ),
            wrong_label="overall-as-claim",
            wrong_still="claim alias still 0.86",
            still_fail=(
                "FAILED tests/test_fact_atomic.py::test_atomic_must_gate"
                " - AssertionError: claim alias; atomic missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.fact_atoms import atomic_precision\n"
                "\n"
                "def report_facts(docs):\n"
                "    overall = mean(d['overall'] for d in docs)\n"
                "    atomic = atomic_precision(docs)\n"
                "    gate = 'pass' if atomic >= 0.70 else 'fail'\n"
                "    return {'overall': overall, 'atomic': atomic, 'gate': gate}\n"
            ),
            rewrite_obs="atomic precision is the gate",
            helper="src/fact_atoms.py",
            fix_helper=(
                "def atomic_precision(docs):\n"
                "    # locked demo: catalog-number atoms 0.39\n"
                "    return 0.39\n"
            ),
            helper_obs="atomic_precision locked 0.39",
            test2="tests/test_fact_atomic_second.py",
            test2_body=(
                "def test_policy_atoms():\n"
                "    rep = report_facts(POLICY_DOCS)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['atomic'] < 0.70\n"
            ),
            residual="src/fact_dash.py still prints overall",
            residual_path="src/fact_dash.py",
            residual_pat="overall|atomic",
            residual_obs="src/fact_dash.py: factuality = overall_claim(text)  # leftover\n",
            confirm="atomic key in report",
            final_obs="    return {'overall': overall, 'atomic': atomic, 'gate': gate}\n",
        ),
        BAD(
            slug="split-conformal-cov",
            seed=(
                "90% split-conformal sets cover gold on only 52% of CL-12; point score 0.81. "
                "Residual-SD interval rejected. Fail if empirical coverage < 0.85. Nightly still point."
            ),
            avoided=(
                "r613 bootstrap mean CI; r624 classifier ECE; r627 GEval-as-probability ECE. "
                "This is split-conformal prediction-set coverage vs a point score"
            ),
            dump="conformal coverage 0.52, point 0.81, and residual-SD",
            first_apply="use residual-SD as the interval",
            plan="Publish mean±1.96*sd so CL-12 still looks covered.",
            plan_change="fail if split-conformal empirical coverage < 0.85",
            goal=(
                "lantern-eval publishes point 0.81 while 90% split-conformal sets cover gold "
                "on only 52% of CL-12. Fail if coverage < 0.85. Do not swap in residual-SD. "
                "tests/test_conformal.py is the gate."
            ),
            outcome=(
                "Point 0.81 hid 52% coverage. Residual-SD still undercovered CL-12. Plan "
                "change: split-conformal coverage gate. Gate 1/1. Partial: nightly "
                "src/nightly_conf.py still publishes the point (xfail)."
            ),
            rg="conformal|coverage|prediction.set|residual.sd|split-conformal",
            rg_obs=(
                "TICKET.md: point 0.81; coverage 0.52 on CL-12\n"
                "tests/test_conformal.py: def test_coverage_must_fail\n"
                "src/conformal.py: gate = mean(scores) >= 0.70\n"
                "goldens/cal.jsonl: calib n=40, eval n=40"
            ),
            test="tests/test_conformal.py",
            test_name="coverage-must-fail",
            test_body=(
                "def test_coverage_must_fail():\n"
                "    rep = report_conf(CAL, EVAL)\n"
                "    assert rep['point'] == pytest.approx(0.81, abs=0.01)\n"
                "    assert rep['coverage'] == pytest.approx(0.52, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'resid_sd' not in rep\n"
            ),
            gate_want="coverage 0.52 and gate fail",
            fail_obs=(
                "FAILED tests/test_conformal.py::test_coverage_must_fail"
                " - AssertionError: coverage missing; point=0.81 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="point 0.81, no coverage",
            src="src/conformal.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_conf(cal, ev):\n"
                "    point = mean(ev['score'] for ev in ev)\n"
                "    return {'point': point, 'gate': 'pass' if point >= 0.70 else 'fail'}\n"
            ),
            obs5="point 0.81; CL-12 gold outside sets",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('point', 0.81, 'coverage', 0.52, 'resid_sd_cov', 0.58)\n"
                "PY"
            ),
            stats_obs="point 0.81 coverage 0.52 resid_sd_cov 0.58",
            wrong_old="    point = mean(ev['score'] for ev in ev)\n    return {'point': point, 'gate': 'pass' if point >= 0.70 else 'fail'}",
            wrong_new=(
                "    from statistics import pstdev\n"
                "    point = mean(ev['score'] for ev in ev)\n"
                "    sd = pstdev(ev['score'] for ev in ev)\n"
                "    return {'point': point, 'resid_sd': sd, 'gate': 'pass' if point >= 0.70 else 'fail'}"
            ),
            wrong_label="residual-sd-interval",
            wrong_still="resid_sd does not measure coverage",
            still_fail=(
                "FAILED tests/test_conformal.py::test_coverage_must_fail"
                " - AssertionError: resid_sd present; coverage missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.conf_split import split_coverage\n"
                "\n"
                "def report_conf(cal, ev):\n"
                "    point = mean(row['score'] for row in ev)\n"
                "    cov = split_coverage(cal, ev, alpha=0.10)\n"
                "    gate = 'fail' if cov < 0.85 else 'pass'\n"
                "    return {'point': point, 'coverage': cov, 'gate': gate}\n"
            ),
            rewrite_obs="split-conformal coverage is the gate",
            helper="src/conf_split.py",
            fix_helper=(
                "def split_coverage(cal, ev, alpha=0.10):\n"
                "    # locked demo: CL-12 empirical coverage 0.52 at 90%\n"
                "    return 0.52\n"
            ),
            helper_obs="split_coverage locked 0.52",
            suite_fail=(
                "FAILED tests/test_nightly_conf.py::test_nightly_uses_coverage"
                " - AssertionError: nightly gate=pass point=0.81\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_conf.py",
            nightly_test="tests/test_nightly_conf.py",
            nightly_body=(
                "def nightly_report(ev):\n"
                "    point = mean(row['score'] for row in ev)\n"
                "    return {'point': point, 'gate': 'pass' if point >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_coverage():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_conf.py still point-only", strict=False)\n'
                "def test_nightly_uses_coverage():"
            ),
            handoff="nightly point-score gate",
            leftover_obs="    return {'point': point, 'gate': 'pass' if point >= 0.70 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r635 PR-AUC vs ROC-AUC / MCC vs accuracy
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="pr-auc-vs-roc",
            seed=(
                "ROC-AUC 0.84 from easy negatives; PR-AUC 0.29 on rare FAIL (12%). "
                "Balanced-accuracy rejected. Gate on PR-AUC."
            ),
            avoided=(
                "r623 macro vs micro F1; r624 ECE vs accuracy. "
                "This is PR-AUC vs ROC-AUC on a rare FAIL class"
            ),
            dump="PR-AUC 0.29, ROC-AUC 0.84, and FAIL prior 12%",
            first_apply="swap in balanced accuracy",
            plan="Publish balanced accuracy 0.71 so the rare FAIL still looks caught.",
            plan_change="gate on PR-AUC; fail if <0.50",
            goal=(
                "lantern-eval publishes ROC-AUC 0.84 while PR-AUC on the rare FAIL class is "
                "0.29. Gate on PR-AUC. Do not swap in balanced accuracy. "
                "tests/test_pr_auc.py is the gate."
            ),
            outcome=(
                "ROC 0.84 hid PR-AUC 0.29. Balanced accuracy 0.71 still passed. Plan change: "
                "PR-AUC gate. Tests 1/1 + 8/8. Residual: src/roc_dash.py still prints ROC."
            ),
            rg="pr.auc|roc.auc|balanced.accuracy|rare FAIL|precision.recall",
            rg_obs=(
                "TICKET.md: ROC 0.84; PR-AUC 0.29 on FAIL=12%\n"
                "tests/test_pr_auc.py: def test_pr_auc_must_gate\n"
                "src/pr_auc.py: auc = roc_auc(y, s)\n"
                "goldens/clf.jsonl: 10 FAIL / 70 PASS"
            ),
            test="tests/test_pr_auc.py",
            test_name="pr-auc-must-gate",
            test_body=(
                "def test_pr_auc_must_gate():\n"
                "    rep = report_auc(Y, S)\n"
                "    assert rep['roc'] == pytest.approx(0.84, abs=0.02)\n"
                "    assert rep['pr'] == pytest.approx(0.29, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'balanced' not in rep\n"
            ),
            gate_want="pr 0.29 and gate fail",
            fail_obs=(
                "FAILED tests/test_pr_auc.py::test_pr_auc_must_gate"
                " - AssertionError: pr missing; roc=0.84 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="ROC-only 0.84",
            src="src/pr_auc.py",
            src_body=(
                "def report_auc(y, s):\n"
                "    roc = roc_auc(y, s)\n"
                "    return {'roc': roc, 'gate': 'pass' if roc >= 0.80 else 'fail'}\n"
            ),
            obs5="ROC 0.84; FAIL prior 12%",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('roc', 0.84, 'pr', 0.29, 'balanced', 0.71, 'prior_fail', 0.12)\n"
                "PY"
            ),
            stats_obs="roc 0.84 pr 0.29 balanced 0.71 prior_fail 0.12",
            wrong_old="    roc = roc_auc(y, s)\n    return {'roc': roc, 'gate': 'pass' if roc >= 0.80 else 'fail'}",
            wrong_new=(
                "    roc = roc_auc(y, s)\n"
                "    bal = balanced_acc(y, s)\n"
                "    return {'roc': roc, 'balanced': bal, 'gate': 'pass' if bal >= 0.70 else 'fail'}"
            ),
            wrong_label="balanced-accuracy",
            wrong_still="balanced 0.71 still passes",
            still_fail=(
                "FAILED tests/test_pr_auc.py::test_pr_auc_must_gate"
                " - AssertionError: balanced=0.71; pr missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.auc_curves import roc_auc, pr_auc\n"
                "\n"
                "def report_auc(y, s):\n"
                "    roc = roc_auc(y, s)\n"
                "    pr = pr_auc(y, s)\n"
                "    gate = 'pass' if pr >= 0.50 else 'fail'\n"
                "    return {'roc': roc, 'pr': pr, 'gate': gate}\n"
            ),
            rewrite_obs="PR-AUC is the gate",
            helper="src/auc_curves.py",
            fix_helper=(
                "def roc_auc(y, s):\n"
                "    return 0.84\n"
                "\n"
                "def pr_auc(y, s):\n"
                "    return 0.29\n"
            ),
            helper_obs="pr_auc locked 0.29",
            test2="tests/test_pr_auc_second.py",
            test2_body=(
                "def test_policy_fail_prior():\n"
                "    rep = report_auc(POL_Y, POL_S)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['pr'] < 0.50\n"
            ),
            residual="src/roc_dash.py still prints ROC",
            residual_path="src/roc_dash.py",
            residual_pat="roc_auc|pr_auc",
            residual_obs="src/roc_dash.py: auc = roc_auc(y, s)  # leftover\n",
            confirm="pr key in report",
            final_obs="    return {'roc': roc, 'pr': pr, 'gate': gate}\n",
        ),
        BAD(
            slug="mcc-vs-accuracy",
            seed=(
                "accuracy 0.88 with 90% PASS prior; MCC 0.11. PASS-class F1 rejected. "
                "Fail if MCC<0.50. Nightly still accuracy."
            ),
            avoided=(
                "r623 macro vs micro F1; r624 ECE vs accuracy. "
                "This is Matthews MCC vs accuracy on a 90% PASS prior"
            ),
            dump="MCC 0.11, accuracy 0.88, and PASS prior 90%",
            first_apply="gate on PASS-class F1",
            plan="Publish PASS-class F1 0.93 so the majority class looks healthy.",
            plan_change="fail if MCC<0.50",
            goal=(
                "lantern-eval publishes accuracy 0.88 while MCC is 0.11 on a 90% PASS prior. "
                "Fail if MCC<0.50. Do not swap in PASS-class F1. tests/test_mcc.py is the gate."
            ),
            outcome=(
                "Accuracy 0.88 hid MCC 0.11. PASS F1 0.93 still passed. Plan change: MCC gate. "
                "Gate 1/1. Partial: nightly src/nightly_mcc.py still accuracy (xfail)."
            ),
            rg="matthews|mcc|accuracy|PASS prior|class F1",
            rg_obs=(
                "TICKET.md: acc 0.88; MCC 0.11 unused\n"
                "tests/test_mcc.py: def test_mcc_must_fail\n"
                "src/mcc.py: gate = acc >= 0.80\n"
                "goldens/clf.jsonl: 72 PASS / 8 FAIL"
            ),
            test="tests/test_mcc.py",
            test_name="mcc-must-fail",
            test_body=(
                "def test_mcc_must_fail():\n"
                "    rep = report_mcc(Y, YHAT)\n"
                "    assert rep['acc'] == pytest.approx(0.88, abs=0.01)\n"
                "    assert rep['mcc'] == pytest.approx(0.11, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'f1_pass' not in rep\n"
            ),
            gate_want="mcc 0.11 and gate fail",
            fail_obs=(
                "FAILED tests/test_mcc.py::test_mcc_must_fail"
                " - AssertionError: mcc missing; acc=0.88 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="accuracy-only 0.88",
            src="src/mcc.py",
            src_body=(
                "def report_mcc(y, yhat):\n"
                "    acc = mean(int(a==b) for a,b in zip(y, yhat))\n"
                "    return {'acc': acc, 'gate': 'pass' if acc >= 0.80 else 'fail'}\n"
            ),
            obs5="acc 0.88; 8 FAIL mostly missed",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('acc', 0.88, 'mcc', 0.11, 'f1_pass', 0.93)\n"
                "PY"
            ),
            stats_obs="acc 0.88 mcc 0.11 f1_pass 0.93",
            wrong_old="    acc = mean(int(a==b) for a,b in zip(y, yhat))\n    return {'acc': acc, 'gate': 'pass' if acc >= 0.80 else 'fail'}",
            wrong_new=(
                "    acc = mean(int(a==b) for a,b in zip(y, yhat))\n"
                "    return {'acc': acc, 'f1_pass': 0.93, 'gate': 'pass' if 0.93 >= 0.80 else 'fail'}"
            ),
            wrong_label="pass-class-f1",
            wrong_still="f1_pass 0.93 still passes",
            still_fail=(
                "FAILED tests/test_mcc.py::test_mcc_must_fail"
                " - AssertionError: f1_pass=0.93; mcc missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.mcc_fit import matthews\n"
                "\n"
                "def report_mcc(y, yhat):\n"
                "    acc = mean(int(a==b) for a,b in zip(y, yhat))\n"
                "    mcc = matthews(y, yhat)\n"
                "    gate = 'pass' if mcc >= 0.50 else 'fail'\n"
                "    return {'acc': acc, 'mcc': mcc, 'gate': gate}\n"
            ),
            rewrite_obs="MCC is the gate",
            helper="src/mcc_fit.py",
            fix_helper=(
                "def matthews(y, yhat):\n"
                "    return 0.11\n"
            ),
            helper_obs="matthews locked 0.11",
            suite_fail=(
                "FAILED tests/test_nightly_mcc.py::test_nightly_uses_mcc"
                " - AssertionError: nightly gate=pass acc=0.88\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_mcc.py",
            nightly_test="tests/test_nightly_mcc.py",
            nightly_body=(
                "def nightly_report(y, yhat):\n"
                "    acc = mean(int(a==b) for a,b in zip(y, yhat))\n"
                "    return {'acc': acc, 'gate': 'pass' if acc >= 0.80 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_mcc():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_mcc.py still accuracy", strict=False)\n'
                "def test_nightly_uses_mcc():"
            ),
            handoff="nightly accuracy-only gate",
            leftover_obs="    return {'acc': acc, 'gate': 'pass' if acc >= 0.80 else 'fail'}\n",
        ),
    )
)


# ---------------------------------------------------------------------------
# r636 IOB2 vs BIOES span F1 / Hamming vs subset accuracy
# ---------------------------------------------------------------------------
MORE.append(
    (
        OK(
            slug="iob2-vs-bioes-span",
            seed=(
                "NER 0.91 token IOB2 exact; gold is BIOES; span F1 after canonicalize 0.47. "
                "Type-only match rejected. Canonicalize to spans."
            ),
            avoided=(
                "r616 sentencepiece vs tiktoken BLEU; r623 macro vs micro F1. "
                "This is IOB2 vs BIOES span-F1 after scheme canonicalize"
            ),
            dump="IOB2 0.91, BIOES gold, and span F1 0.47",
            first_apply="strip I/B prefixes and type-match",
            plan="Compare entity types only so 0.88 still looks aligned.",
            plan_change="canonicalize to spans; fail if span F1<0.70",
            goal=(
                "lantern-eval publishes NER 0.91 on token IOB2 while gold is BIOES and span F1 "
                "is 0.47. Canonicalize to spans. Do not type-only match. "
                "tests/test_span_f1.py is the gate."
            ),
            outcome=(
                "IOB2 token exact 0.91 hid BIOES span F1 0.47. Type-only 0.88 still passed. "
                "Plan change: span canonicalize. Tests 1/1 + 8/8. Residual: src/ner_dash.py "
                "still token-exact."
            ),
            rg="iob2|bioes|span.f1|canonicalize|entity type",
            rg_obs=(
                "TICKET.md: IOB2 0.91; BIOES span F1 0.47\n"
                "tests/test_span_f1.py: def test_span_f1_must_gate\n"
                "src/span_f1.py: acc = token_exact(pred, gold)\n"
                "goldens/ner.jsonl: B- vs S- scheme mix"
            ),
            test="tests/test_span_f1.py",
            test_name="span-f1-must-gate",
            test_body=(
                "def test_span_f1_must_gate():\n"
                "    rep = report_ner(PRED, GOLD)\n"
                "    assert rep['token'] == pytest.approx(0.91, abs=0.01)\n"
                "    assert rep['span_f1'] == pytest.approx(0.47, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'type_only' not in rep\n"
            ),
            gate_want="span_f1 0.47 and gate fail",
            fail_obs=(
                "FAILED tests/test_span_f1.py::test_span_f1_must_gate"
                " - AssertionError: span_f1 missing; token=0.91 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="token IOB2 only",
            src="src/span_f1.py",
            src_body=(
                "def report_ner(pred, gold):\n"
                "    token = token_exact(pred, gold)\n"
                "    return {'token': token, 'gate': 'pass' if token >= 0.70 else 'fail'}\n"
            ),
            obs5="token 0.91; B- vs S- mismatch on spans",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('token', 0.91, 'type_only', 0.88, 'span_f1', 0.47)\n"
                "PY"
            ),
            stats_obs="token 0.91 type_only 0.88 span_f1 0.47",
            wrong_old="    token = token_exact(pred, gold)\n    return {'token': token, 'gate': 'pass' if token >= 0.70 else 'fail'}",
            wrong_new=(
                "    token = token_exact(pred, gold)\n"
                "    return {'token': token, 'type_only': 0.88, 'gate': 'pass' if 0.88 >= 0.70 else 'fail'}"
            ),
            wrong_label="type-only-match",
            wrong_still="type_only 0.88 still passes",
            still_fail=(
                "FAILED tests/test_span_f1.py::test_span_f1_must_gate"
                " - AssertionError: type_only=0.88; span_f1 missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.span_canon import token_exact, span_f1\n"
                "\n"
                "def report_ner(pred, gold):\n"
                "    token = token_exact(pred, gold)\n"
                "    span = span_f1(pred, gold)\n"
                "    gate = 'pass' if span >= 0.70 else 'fail'\n"
                "    return {'token': token, 'span_f1': span, 'gate': gate}\n"
            ),
            rewrite_obs="span F1 after canonicalize is the gate",
            helper="src/span_canon.py",
            fix_helper=(
                "def token_exact(pred, gold):\n"
                "    return 0.91\n"
                "\n"
                "def span_f1(pred, gold):\n"
                "    return 0.47\n"
            ),
            helper_obs="span_f1 locked 0.47",
            test2="tests/test_span_f1_second.py",
            test2_body=(
                "def test_bioes_cluster():\n"
                "    rep = report_ner(PRED2, GOLD2)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['span_f1'] < 0.70\n"
            ),
            residual="src/ner_dash.py still token-exact",
            residual_path="src/ner_dash.py",
            residual_pat="token_exact|span_f1",
            residual_obs="src/ner_dash.py: ner = token_exact(pred, gold)  # leftover\n",
            confirm="span_f1 key in report",
            final_obs="    return {'token': token, 'span_f1': span, 'gate': gate}\n",
        ),
        BAD(
            slug="hamming-vs-subset-acc",
            seed=(
                "Hamming 0.81 published; subset accuracy 0.22 because extra CL-12 labels. "
                "Micro-F1 rejected. Fail if subset acc<0.60. Nightly still Hamming."
            ),
            avoided=(
                "r623 macro vs micro F1; r28 recall-precision alias swap. "
                "This is multi-label Hamming vs subset accuracy"
            ),
            dump="Hamming 0.81, subset acc 0.22, and extra labels",
            first_apply="publish micro-F1 instead of subset",
            plan="Publish micro-F1 0.79 so partial label hits still look green.",
            plan_change="fail if subset accuracy<0.60",
            goal=(
                "lantern-eval publishes Hamming 0.81 while subset accuracy is 0.22 on extra "
                "CL-12 labels. Fail if subset acc<0.60. Do not swap in micro-F1. "
                "tests/test_subset.py is the gate."
            ),
            outcome=(
                "Hamming 0.81 hid subset 0.22. Micro-F1 0.79 still passed. Plan change: subset "
                "accuracy gate. Gate 1/1. Partial: nightly src/nightly_subset.py still Hamming "
                "(xfail)."
            ),
            rg="hamming|subset.accuracy|micro-F1|multi-label|extra labels",
            rg_obs=(
                "TICKET.md: Hamming 0.81; subset 0.22 unused\n"
                "tests/test_subset.py: def test_subset_must_fail\n"
                "src/subset.py: acc = hamming(y, yhat)\n"
                "goldens/multilabel.jsonl: extra CL-12 tags"
            ),
            test="tests/test_subset.py",
            test_name="subset-must-fail",
            test_body=(
                "def test_subset_must_fail():\n"
                "    rep = report_ml(Y, YHAT)\n"
                "    assert rep['hamming'] == pytest.approx(0.81, abs=0.02)\n"
                "    assert rep['subset'] == pytest.approx(0.22, abs=0.03)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'micro_f1' not in rep\n"
            ),
            gate_want="subset 0.22 and gate fail",
            fail_obs=(
                "FAILED tests/test_subset.py::test_subset_must_fail"
                " - AssertionError: subset missing; hamming=0.81 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="Hamming-only 0.81",
            src="src/subset.py",
            src_body=(
                "def report_ml(y, yhat):\n"
                "    h = hamming(y, yhat)\n"
                "    return {'hamming': h, 'gate': 'pass' if h >= 0.70 else 'fail'}\n"
            ),
            obs5="Hamming 0.81; extra labels kill subset",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('hamming', 0.81, 'subset', 0.22, 'micro_f1', 0.79)\n"
                "PY"
            ),
            stats_obs="hamming 0.81 subset 0.22 micro_f1 0.79",
            wrong_old="    h = hamming(y, yhat)\n    return {'hamming': h, 'gate': 'pass' if h >= 0.70 else 'fail'}",
            wrong_new=(
                "    h = hamming(y, yhat)\n"
                "    return {'hamming': h, 'micro_f1': 0.79, 'gate': 'pass' if 0.79 >= 0.70 else 'fail'}"
            ),
            wrong_label="micro-f1-as-subset",
            wrong_still="micro_f1 0.79 still passes",
            still_fail=(
                "FAILED tests/test_subset.py::test_subset_must_fail"
                " - AssertionError: micro_f1=0.79; subset missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.ml_acc import hamming, subset_acc\n"
                "\n"
                "def report_ml(y, yhat):\n"
                "    h = hamming(y, yhat)\n"
                "    sub = subset_acc(y, yhat)\n"
                "    gate = 'pass' if sub >= 0.60 else 'fail'\n"
                "    return {'hamming': h, 'subset': sub, 'gate': gate}\n"
            ),
            rewrite_obs="subset accuracy is the gate",
            helper="src/ml_acc.py",
            fix_helper=(
                "def hamming(y, yhat):\n"
                "    return 0.81\n"
                "\n"
                "def subset_acc(y, yhat):\n"
                "    return 0.22\n"
            ),
            helper_obs="subset_acc locked 0.22",
            suite_fail=(
                "FAILED tests/test_nightly_subset.py::test_nightly_uses_subset"
                " - AssertionError: nightly gate=pass hamming=0.81\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_subset.py",
            nightly_test="tests/test_nightly_subset.py",
            nightly_body=(
                "def nightly_report(y, yhat):\n"
                "    h = hamming(y, yhat)\n"
                "    return {'hamming': h, 'gate': 'pass' if h >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_subset():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_subset.py still Hamming", strict=False)\n'
                "def test_nightly_uses_subset():"
            ),
            handoff="nightly Hamming-only gate",
            leftover_obs="    return {'hamming': h, 'gate': 'pass' if h >= 0.70 else 'fail'}\n",
        ),
    )
)
