"""Unique leftover-methodology plants for r728+ (not r613–r727 clones).

Not unicode leftover, HTTP leftover, r613 agreement-metrics, r629–r700
cache-omit/last-unit/seed-leak/temp0/rubric-alias, or r701–r727
2PL/CUSUM/Angoff/MMLU-redux/SWE-ftp/FActScore/PR-AUC/IOB2/tau-passk/
lost-middle/GAIA/XSTest/TOST/Cronbach/Western-Electric/CoNLL/Simpson.
"""

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


def _db_ok(dump, first_apply, plan_change, test_name, gate_want, fail_short, obs5, wrong_label, residual, confirm, src, test, test2, residual_path):
    lines = [
        f"Plan: dump {dump} before {first_apply}.",
        f"Observation: {test_name} exists (step 1). Read {test}.",
        f"Observation: gate wants {gate_want} (step 2). Run {test}.",
        f"Observation: {fail_short} (step 3). Read {src}.",
        f"Observation: {obs5} (step 4). Reproduce the statistic.",
        f"Plan: first apply — {first_apply}.",
        f"Observation: {wrong_label} (step 6). Re-run {test}.",
        f"Reflection: plan change after {first_apply} — {plan_change}.",
        f"Observation: rewrite (step 8). Write helper.",
        f"Observation: helper (step 9). Re-run {test}.",
        "Observation: gate green (step 10). Full suite.",
        f"Observation: 8/8 (step 11). Read {test2}.",
        f"Observation: second contract (step 12). Run {test2}.",
        f"Observation: second green (step 13). Residual {residual}.",
        f"Observation: residual out of ticket (step 14). Re-run {test}.",
        f"Observation: still green (step 15). Confirm {confirm}.",
    ]
    for line in lines:
        if len(line) > 240:
            raise ValueError(f"decision_basis {len(line)}: {line}")


def _ok_from(
    *,
    slug,
    seed,
    avoided,
    dump,
    first_apply,
    plan,
    plan_change,
    goal,
    outcome,
    mod,
    test_fn,
    naive,
    true,
    alt,
    helper_fn,
    helper_body,
    rg,
    ticket,
    golden,
    obs5,
    fail_short,
    wrong_label,
    wrong_still,
    rewrite_obs,
    helper_obs,
    residual,
    residual_path,
    residual_pat,
    residual_obs,
    confirm,
    fail_if,
    naive_expr="mean(y)",
    src_import="from statistics import mean\n\n",
):
    nk, nv = naive
    tk, tv = true
    ak, av = alt
    fn = f"report_{mod}"
    test = f"tests/test_{mod}.py"
    src = f"src/{mod}.py"
    helper = f"src/{mod}_fit.py"
    test2 = f"tests/test_{mod}_second.py"
    test_name = test_fn.replace("_", "-")
    src_body = (
        f"{src_import}"
        f"def {fn}(items, y):\n"
        f"    {nk} = {naive_expr}\n"
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}\n"
    )
    wrong_old = (
        f"    {nk} = {naive_expr}\n"
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}"
    )
    wrong_new = (
        f"    {nk} = {naive_expr}\n"
        f"    {ak} = {av}\n"
        f"    return {{{nk!r}: {nk}, {ak!r}: {ak}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}"
    )
    fix_src = (
        f"{src_import}"
        f"from src.{mod}_fit import {helper_fn}\n"
        "\n"
        f"def {fn}(items, y):\n"
        f"    {nk} = {naive_expr}\n"
        f"    {tk} = {helper_fn}(items, y)\n"
        f"    gate = 'fail' if {fail_if} else 'pass'\n"
        f"    return {{{nk!r}: {nk}, {tk!r}: {tk}, 'gate': gate}}\n"
    )
    final_obs = (
        f"    return {{{nk!r}: {nk}, {tk!r}: {tk}, 'gate': gate}}\n"
    )
    test_body = (
        f"def {test_fn}():\n"
        f"    rep = {fn}(ITEMS, Y)\n"
        f"    assert rep[{nk!r}] == pytest.approx({nv}, abs=0.02)\n"
        f"    assert rep[{tk!r}] == pytest.approx({tv}, abs=0.03)\n"
        f"    assert rep['gate'] == 'fail'\n"
        f"    assert {ak!r} not in rep\n"
    )
    test2_body = (
        f"def test_{mod}_second():\n"
        f"    rep = {fn}(HOLD, HOLD_Y)\n"
        f"    assert rep['gate'] == 'fail'\n"
        f"    assert {tk!r} in rep\n"
    )
    gate_want = f"{tk} {tv} and gate fail"
    fail_obs = (
        f"FAILED {test}::{test_fn}"
        f" - AssertionError: {tk} missing; {nk}={nv} gate=pass\n"
        "0 passed, 1 failed"
    )
    still_fail = (
        f"FAILED {test}::{test_fn}"
        f" - AssertionError: {ak}={av}; {tk} missing\n"
        "0 passed, 1 failed"
    )
    stats_cmd = (
        "python3 - <<'PY'\n"
        f"print({nk!r}, {nv}, {tk!r}, {tv}, {ak!r}, {av})\n"
        "PY"
    )
    stats_obs = f"{nk} {nv} {tk} {tv} {ak} {av}"
    rg_obs = (
        f"TICKET.md: {ticket}\n"
        f"{test}: def {test_fn}\n"
        f"{src}: gate = mean\n"
        f"goldens/{mod}.jsonl: {golden}"
    )
    _db_ok(
        dump,
        first_apply,
        plan_change,
        test_name,
        gate_want,
        fail_short,
        obs5,
        wrong_label,
        residual,
        confirm,
        src,
        test,
        test2,
        residual_path,
    )
    return OK(
        slug=slug,
        seed=seed,
        avoided=avoided,
        dump=dump,
        first_apply=first_apply,
        plan=plan,
        plan_change=plan_change,
        goal=goal,
        outcome=outcome,
        rg=rg,
        rg_obs=rg_obs,
        test=test,
        test_name=test_name,
        test_body=test_body,
        gate_want=gate_want,
        fail_obs=fail_obs,
        fail_short=fail_short,
        src=src,
        src_body=src_body,
        obs5=obs5,
        stats_cmd=stats_cmd,
        stats_obs=stats_obs,
        wrong_old=wrong_old,
        wrong_new=wrong_new,
        wrong_label=wrong_label,
        wrong_still=wrong_still,
        still_fail=still_fail,
        fix_src=fix_src,
        rewrite_obs=rewrite_obs,
        helper=helper,
        fix_helper=helper_body,
        helper_obs=helper_obs,
        test2=test2,
        test2_body=test2_body,
        residual=residual,
        residual_path=residual_path,
        residual_pat=residual_pat,
        residual_obs=residual_obs,
        confirm=confirm,
        final_obs=final_obs,
    )


def _bad_from(
    *,
    slug,
    seed,
    avoided,
    dump,
    first_apply,
    plan,
    plan_change,
    goal,
    outcome,
    mod,
    test_fn,
    naive,
    true,
    alt,
    helper_fn,
    helper_body,
    rg,
    ticket,
    golden,
    obs5,
    fail_short,
    wrong_label,
    wrong_still,
    rewrite_obs,
    helper_obs,
    fail_if,
    nightly_fn,
    handoff,
    naive_expr="mean(y)",
    src_import="from statistics import mean\n\n",
):
    nk, nv = naive
    tk, tv = true
    ak, av = alt
    fn = f"report_{mod}"
    test = f"tests/test_{mod}.py"
    src = f"src/{mod}.py"
    helper = f"src/{mod}_fit.py"
    nightly = f"src/nightly_{mod}.py"
    ntest = f"tests/test_nightly_{mod}.py"
    test_name = test_fn.replace("_", "-")
    src_body = (
        f"{src_import}"
        f"def {fn}(items, y):\n"
        f"    {nk} = {naive_expr}\n"
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}\n"
    )
    wrong_old = (
        f"    {nk} = {naive_expr}\n"
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}"
    )
    wrong_new = (
        f"    {nk} = {naive_expr}\n"
        f"    {ak} = {av}\n"
        f"    return {{{nk!r}: {nk}, {ak!r}: {ak}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}"
    )
    fix_src = (
        f"{src_import}"
        f"from src.{mod}_fit import {helper_fn}\n"
        "\n"
        f"def {fn}(items, y):\n"
        f"    {nk} = {naive_expr}\n"
        f"    {tk} = {helper_fn}(items, y)\n"
        f"    gate = 'fail' if {fail_if} else 'pass'\n"
        f"    return {{{nk!r}: {nk}, {tk!r}: {tk}, 'gate': gate}}\n"
    )
    test_body = (
        f"def {test_fn}():\n"
        f"    rep = {fn}(ITEMS, Y)\n"
        f"    assert rep[{nk!r}] == pytest.approx({nv}, abs=0.02)\n"
        f"    assert rep[{tk!r}] == pytest.approx({tv}, abs=0.03)\n"
        f"    assert rep['gate'] == 'fail'\n"
        f"    assert {ak!r} not in rep\n"
    )
    gate_want = f"{tk} {tv} and gate fail"
    fail_obs = (
        f"FAILED {test}::{test_fn}"
        f" - AssertionError: {tk} missing; {nk}={nv} gate=pass\n"
        "0 passed, 1 failed"
    )
    still_fail = (
        f"FAILED {test}::{test_fn}"
        f" - AssertionError: {ak}={av}; {tk} missing\n"
        "0 passed, 1 failed"
    )
    stats_cmd = (
        "python3 - <<'PY'\n"
        f"print({nk!r}, {nv}, {tk!r}, {tv}, {ak!r}, {av})\n"
        "PY"
    )
    stats_obs = f"{nk} {nv} {tk} {tv} {ak} {av}"
    rg_obs = (
        f"TICKET.md: {ticket}\n"
        f"{test}: def {test_fn}\n"
        f"{src}: gate = mean\n"
        f"goldens/{mod}.jsonl: {golden}"
    )
    suite_fail = (
        f"FAILED {ntest}::test_nightly_{mod}"
        f" - AssertionError: nightly gate=pass {nk}={nv}\n"
        "7 passed, 1 failed"
    )
    nightly_body = (
        f"def {nightly_fn}(items, y):\n"
        f"    {nk} = {naive_expr}\n"
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}\n"
    )
    xfail_old = f"def test_nightly_{mod}():"
    xfail_new = (
        f'@pytest.mark.xfail(reason="handoff: {nightly} still publishes {nk}", strict=False)\n'
        f"def test_nightly_{mod}():"
    )
    leftover_obs = (
        f"    return {{{nk!r}: {nk}, 'gate': 'pass' if {nk} >= 0.70 else 'fail'}}\n"
    )
    db = f"Reflection: plan change after {first_apply} — {plan_change}."
    if len(db) > 240:
        raise ValueError(f"bad db {len(db)}: {db}")
    db2 = f"Plan: dump {dump} before {first_apply}."
    if len(db2) > 240:
        raise ValueError(f"bad dump db {len(db2)}: {db2}")
    return BAD(
        slug=slug,
        seed=seed,
        avoided=avoided,
        dump=dump,
        first_apply=first_apply,
        plan=plan,
        plan_change=plan_change,
        goal=goal,
        outcome=outcome,
        rg=rg,
        rg_obs=rg_obs,
        test=test,
        test_name=test_name,
        test_body=test_body,
        gate_want=gate_want,
        fail_obs=fail_obs,
        fail_short=fail_short,
        src=src,
        src_body=src_body,
        obs5=obs5,
        stats_cmd=stats_cmd,
        stats_obs=stats_obs,
        wrong_old=wrong_old,
        wrong_new=wrong_new,
        wrong_label=wrong_label,
        wrong_still=wrong_still,
        still_fail=still_fail,
        fix_src=fix_src,
        rewrite_obs=rewrite_obs,
        helper=helper,
        fix_helper=helper_body,
        helper_obs=helper_obs,
        suite_fail=suite_fail,
        nightly=nightly,
        nightly_test=ntest,
        nightly_body=nightly_body,
        xfail_old=xfail_old,
        xfail_new=xfail_new,
        handoff=handoff,
        leftover_obs=leftover_obs,
    )


# ---------------------------------------------------------------------------
# 1  3PL guessing c vs percent-correct / Bookmark RP68 vs p70 cut
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="3pl-guess-c-vs-pct",
            seed=(
                "percent-correct 0.77 green; 3PL guessing c=0.31 on CL-12 refund items. "
                "1PL guessing=0 rejected. Fail if any item c>=0.20."
            ),
            avoided=(
                "r701/r712 2PL b vs percent-correct; r725 outfit. "
                "This is 3PL lower-asymptote c vs percent-correct"
            ),
            dump="3PL c=0.31 table, pct 0.77, CL-12 items",
            first_apply="force guessing c=0 as 1PL",
            plan="Publish 1PL with c=0 so percent-correct 0.77 still looks clean.",
            plan_change="fit 3PL c; fail if any c>=0.20",
            goal=(
                "lantern-eval publishes percent_correct=0.77 while 3PL guessing on CL-12 "
                "refund items is c=0.31. Gate on 3PL c. Do not force c=0. "
                "tests/test_tpl3.py is the gate."
            ),
            outcome=(
                "Percent-correct 0.77 hid items with 3PL c=0.31. Forcing c=0 still pooled them. "
                "Plan change: fit 3PL c; fail if max c>=0.20. Tests 1/1 + 8/8. Residual: "
                "src/tpl3_dash.py still publishes percent_correct."
            ),
            mod="tpl3",
            test_fn="test_3pl_c_must_fail",
            naive=("pct", 0.77),
            true=("c_guess", 0.31),
            alt=("c_forced0", 0.0),
            helper_fn="fit_3pl_c",
            helper_body=(
                "def fit_3pl_c(items, y):\n"
                "    # locked demo: CL-12 refunds carry guessing c=0.31\n"
                "    return 0.31\n"
            ),
            fail_if="c_guess >= 0.20",
            rg="3pl|guessing c|lower.asymptote|percent_correct|c_guess",
            ticket="pct 0.77 pass; CL-12 c=0.31 unused",
            golden="cl12-40d p=0.25 with 4-option MC",
            obs5="pct 0.77; CL-12 c=0.31",
            fail_short="pct 0.77, no 3PL c",
            wrong_label="force-c-zero",
            wrong_still="c_forced0=0 still passes",
            rewrite_obs="3PL c fit; fail-closed on c>=0.20",
            helper_obs="fit_3pl_c locked 0.31",
            residual="src/tpl3_dash.py still publishes percent_correct",
            residual_path="src/tpl3_dash.py",
            residual_pat="percent_correct|c_guess",
            residual_obs="src/tpl3_dash.py: percent_correct = mean(correct)  # leftover\n",
            confirm="c_guess in report",
        ),
        _bad_from(
            slug="bookmark-rp68-vs-p70",
            seed=(
                "published cut is p>=0.70; bookmark RP68 page is 0.41. Percentile-cut "
                "rejected. Fail if bookmark<0.55. Nightly still p70."
            ),
            avoided=(
                "r703/r714 arbitrary 0.70 vs panel cut. "
                "This is bookmark RP68 page vs percent cut, not a panel rating method"
            ),
            dump="bookmark RP68 0.41, p70 cut, panel pages",
            first_apply="keep the 0.70 percent cut",
            plan="Keep p>=0.70 so the live dashboard still looks green.",
            plan_change="bookmark RP68; fail if page<0.55",
            goal=(
                "lantern-eval uses a p>=0.70 cut while the bookmark RP68 ordered-item page "
                "is 0.41. Gate on bookmark. Do not keep p70. tests/test_bkmk.py is the gate."
            ),
            outcome=(
                "p70 hid bookmark RP68=0.41. Percentile cut still passed. Plan change: "
                "bookmark page gate. Gate 1/1. Partial: nightly src/nightly_bkmk.py still p70 "
                "(xfail)."
            ),
            mod="bkmk",
            test_fn="test_bookmark_must_fail",
            naive=("p70", 0.74),
            true=("rp68", 0.41),
            alt=("pctile_cut", 0.70),
            helper_fn="bookmark_rp68",
            helper_body=(
                "def bookmark_rp68(items, y):\n"
                "    # locked demo: ordered-item page at RP68 is 0.41\n"
                "    return 0.41\n"
            ),
            fail_if="rp68 < 0.55",
            rg="bookmark|rp68|ordered.item page|p70 cut",
            ticket="p70 green; RP68 page 0.41 unused",
            golden="ordered items, bookmark between cl11 and cl12",
            obs5="p70 0.74; RP68 page 0.41",
            fail_short="p70 cut, no bookmark",
            wrong_label="keep-p70-cut",
            wrong_still="pctile_cut 0.70 still passes",
            rewrite_obs="bookmark RP68 is the cut",
            helper_obs="bookmark_rp68 locked 0.41",
            nightly_fn="nightly_bkmk",
            handoff="nightly p70-cut gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 2  DeLong paired AUC vs Wald z / Clopper-Pearson vs Wald proportion
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="delong-auc-vs-waldz",
            seed=(
                "Wald z on AUC 0.81 vs 0.79 claims p=0.018; DeLong paired p=0.41. "
                "Unpaired z rejected. Fail unless DeLong p<0.05."
            ),
            avoided=(
                "r707/r718 PR-AUC vs ROC-AUC; r617 paired test on accuracy. "
                "This is DeLong covariance for paired AUCs vs Wald z"
            ),
            dump="DeLong p=0.41, Wald z p=0.018, AUCs",
            first_apply="keep unpaired Wald z on AUCs",
            plan="Publish Wald z so 0.81 vs 0.79 still looks significant.",
            plan_change="DeLong paired; fail unless p<0.05",
            goal=(
                "lantern-eval claims AUC 0.81 beats 0.79 (Wald p=0.018) while DeLong's "
                "paired test is p=0.41. Gate on DeLong. Do not use unpaired z. "
                "tests/test_delong.py is the gate."
            ),
            outcome=(
                "Wald z hid DeLong p=0.41. Unpaired z still claimed a win. Plan change: "
                "DeLong p-value gate. Tests 1/1 + 8/8. Residual: src/delong_dash.py still Wald."
            ),
            mod="delong",
            test_fn="test_delong_p_must_fail",
            naive=("auc_a", 0.81),
            true=("delong_p", 0.41),
            alt=("wald_p", 0.018),
            helper_fn="delong_pvalue",
            helper_body=(
                "def delong_pvalue(items, y):\n"
                "    # locked demo: paired ROC covariance p=0.41\n"
                "    return 0.41\n"
            ),
            fail_if="delong_p >= 0.05",
            rg="delong|paired auc|wald z|roc covariance",
            ticket="Wald p=0.018; DeLong p=0.41 unused",
            golden="paired scores on same 240 items",
            obs5="AUC 0.81 vs 0.79; DeLong p=0.41",
            fail_short="Wald z only, no DeLong",
            wrong_label="unpaired-wald-z",
            wrong_still="wald_p 0.018 still 'wins'",
            rewrite_obs="DeLong paired p is the gate",
            helper_obs="delong_pvalue locked 0.41",
            residual="src/delong_dash.py still Wald z",
            residual_path="src/delong_dash.py",
            residual_pat="wald_p|delong_p",
            residual_obs="src/delong_dash.py: p = wald_z(auc_a, auc_b)  # leftover\n",
            confirm="delong_p in report",
        ),
        _bad_from(
            slug="clopper-pearson-vs-wald",
            seed=(
                "Wald 95% CI [0.71, 0.89] for 8/11 pass; Clopper-Pearson [0.48, 0.89] "
                "crosses 0.70. Normal-approx rejected. Fail if CP lo<0.70. Nightly still Wald."
            ),
            avoided=(
                "r617 Wilson on pass@k (banned leftover). "
                "This is Clopper-Pearson exact binomial vs Wald on n=11"
            ),
            dump="CP [0.48,0.89], Wald [0.71,0.89], 8/11",
            first_apply="keep Wald interval on 8/11",
            plan="Publish Wald so 8/11 still clears 0.70 at the lower bound.",
            plan_change="Clopper-Pearson; fail if lo<0.70",
            goal=(
                "lantern-eval publishes Wald CI [0.71, 0.89] for 8/11 while Clopper-Pearson "
                "is [0.48, 0.89]. Gate on CP lower bound. Do not keep Wald. "
                "tests/test_cpci.py is the gate."
            ),
            outcome=(
                "Wald lo=0.71 hid CP lo=0.48. Plan change: CP gate. Gate 1/1. Partial: "
                "nightly src/nightly_cpci.py still Wald (xfail)."
            ),
            mod="cpci",
            test_fn="test_cp_lo_must_fail",
            naive=("wald_lo", 0.71),
            true=("cp_lo", 0.48),
            alt=("normal_lo", 0.72),
            helper_fn="clopper_pearson_lo",
            helper_body=(
                "def clopper_pearson_lo(items, y):\n"
                "    # locked demo: Beta(8, 4) 0.025 quantile ~ 0.48\n"
                "    return 0.48\n"
            ),
            fail_if="cp_lo < 0.70",
            rg="clopper|pearson exact|binomial ci|8/11|wald_lo",
            ticket="Wald lo 0.71; CP lo 0.48 unused",
            golden="n=11 tasks, 8 pass",
            obs5="8/11; Wald lo 0.71; CP lo 0.48",
            fail_short="Wald CI only, no CP",
            wrong_label="keep-wald-lo",
            wrong_still="normal_lo 0.72 still clears 0.70",
            rewrite_obs="Clopper-Pearson lo is the gate",
            helper_obs="clopper_pearson_lo locked 0.48",
            nightly_fn="nightly_cpci",
            handoff="nightly Wald-CI gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 3  BH FDR vs uncorrected p / Holm vs uncorrected pairwise
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="bh-fdr-vs-uncorr-p",
            seed=(
                "leaderboard flags 6/40 models at uncorrected p<0.05; BH q-values all "
                ">0.10. Bonferroni rejected. Fail unless any q<0.10."
            ),
            avoided=(
                "r617 paired accuracy test; r623 winrate. "
                "This is Benjamini-Hochberg FDR on a 40-model leaderboard"
            ),
            dump="6 uncorrected p<0.05, BH q all >0.10",
            first_apply="keep uncorrected p<0.05 stars",
            plan="Star every p<0.05 so six models still look like winners.",
            plan_change="BH q; fail unless any q<0.10",
            goal=(
                "lantern-eval stars 6/40 models at uncorrected p<0.05 while every "
                "Benjamini-Hochberg q is >0.10. Gate on BH. Do not keep uncorrected stars. "
                "tests/test_bhfdr.py is the gate."
            ),
            outcome=(
                "Uncorrected p hid BH q>0.10. Plan change: BH q gate. Tests 1/1 + 8/8. "
                "Residual: src/bhfdr_dash.py still stars p<0.05."
            ),
            mod="bhfdr",
            test_fn="test_bh_q_must_fail",
            naive=("n_sig_uncorr", 6),
            true=("min_q", 0.18),
            alt=("n_bonf", 0),
            helper_fn="bh_min_q",
            helper_body=(
                "def bh_min_q(items, y):\n"
                "    # locked demo: 40 tests, min BH q=0.18\n"
                "    return 0.18\n"
            ),
            fail_if="min_q >= 0.10",
            naive_expr="sum(1 for v in y if v < 0.05)",
            rg="benjamini|hochberg|fdr|q.value|uncorrected p",
            ticket="6 p<0.05 stars; BH q unused",
            golden="40 model vs-base p-values, 6 nominally <0.05",
            obs5="6 uncorrected; min BH q=0.18",
            fail_short="uncorrected stars, no BH q",
            wrong_label="uncorrected-p-stars",
            wrong_still="n_bonf=0 unused; uncorr still stars 6",
            rewrite_obs="BH min q is the gate",
            helper_obs="bh_min_q locked 0.18",
            residual="src/bhfdr_dash.py still stars p<0.05",
            residual_path="src/bhfdr_dash.py",
            residual_pat="p < 0.05|min_q",
            residual_obs="src/bhfdr_dash.py: stars = p_uncorr < 0.05  # leftover\n",
            confirm="min_q in report",
        ),
        _bad_from(
            slug="holm-vs-uncorr-pair",
            seed=(
                "12 pairwise model tests, 4 uncorrected p<0.05; Holm-adjusted none. "
                "Sidak rejected. Fail unless Holm p<0.05. Nightly still uncorrected."
            ),
            avoided=(
                "r623 mean winrate; BH FDR in this mill's success sibling. "
                "This is Holm step-down on pairwise tests"
            ),
            dump="4 uncorrected pairwise, Holm none",
            first_apply="keep uncorrected pairwise stars",
            plan="Star four pairwise p<0.05 so the matrix still looks decisive.",
            plan_change="Holm; fail unless any Holm p<0.05",
            goal=(
                "lantern-eval stars 4/12 pairwise tests at uncorrected p<0.05 while Holm "
                "step-down leaves none. Gate on Holm. Do not keep uncorrected. "
                "tests/test_holm.py is the gate."
            ),
            outcome=(
                "Uncorrected pairwise hid Holm-empty. Plan change: Holm gate. Gate 1/1. "
                "Partial: nightly src/nightly_holm.py still uncorrected (xfail)."
            ),
            mod="holm",
            test_fn="test_holm_must_fail",
            naive=("n_pair_uncorr", 4),
            true=("n_holm", 0),
            alt=("n_sidak", 1),
            helper_fn="holm_count",
            helper_body=(
                "def holm_count(items, y):\n"
                "    # locked demo: 12 pairwise, Holm count=0\n"
                "    return 0\n"
            ),
            fail_if="n_holm < 1",
            naive_expr="sum(1 for v in y if v < 0.05)",
            rg="holm step-down|pairwise p|sidak|uncorrected pair",
            ticket="4 pairwise stars; Holm unused",
            golden="12 pairwise p-values among 4 models",
            obs5="4 uncorrected; Holm 0",
            fail_short="uncorrected pairwise, no Holm",
            wrong_label="keep-uncorr-pair",
            wrong_still="n_sidak=1 is the wrong substitute",
            rewrite_obs="Holm count is the gate",
            helper_obs="holm_count locked 0",
            nightly_fn="nightly_holm",
            handoff="nightly uncorrected-pairwise gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 4  Page-Hinkley drift vs mean / Hellinger vs delta-mu
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="page-hinkley-vs-mu",
            seed=(
                "rolling mean still 0.72 at t=40; Page-Hinkley lambda=52 fires. "
                "Static mean-shift rejected. Fail if PH fires."
            ),
            avoided=(
                "r702/r713 CUSUM early-stop vs fixed-n; r710 EWMA vs Shewhart. "
                "This is Page-Hinkley sequential drift vs rolling mean"
            ),
            dump="PH lambda=52 at t=40, rolling mean 0.72",
            first_apply="keep a static mean-shift of 0.02",
            plan="Treat a 0.02 mean bump as noise so t=40 still looks stable.",
            plan_change="Page-Hinkley; fail if lambda fires",
            goal=(
                "lantern-eval publishes rolling mean 0.72 at t=40 while Page-Hinkley "
                "lambda=52 has already fired. Gate on PH. Do not use static mean-shift. "
                "tests/test_phink.py is the gate."
            ),
            outcome=(
                "Rolling mean 0.72 hid PH fire at t=40. Static 0.02 shift still green. "
                "Plan change: PH lambda gate. Tests 1/1 + 8/8. Residual: src/phink_dash.py "
                "still rolling mean."
            ),
            mod="phink",
            test_fn="test_ph_must_fail",
            naive=("roll_mu", 0.72),
            true=("ph_lambda", 52.0),
            alt=("delta_mu", 0.02),
            helper_fn="page_hinkley",
            helper_body=(
                "def page_hinkley(items, y):\n"
                "    # locked demo: PH statistic 52 at t=40\n"
                "    return 52.0\n"
            ),
            fail_if="ph_lambda >= 50",
            rg="page.hinkle|ph_lambda|sequential drift|roll_mu",
            ticket="roll_mu 0.72; PH 52 unused",
            golden="t=1..80 scores, change at t=28",
            obs5="roll_mu 0.72; PH lambda 52",
            fail_short="rolling mean only, no PH",
            wrong_label="static-mean-shift",
            wrong_still="delta_mu 0.02 still green",
            rewrite_obs="Page-Hinkley lambda is the gate",
            helper_obs="page_hinkley locked 52",
            residual="src/phink_dash.py still rolling mean",
            residual_path="src/phink_dash.py",
            residual_pat="roll_mu|ph_lambda",
            residual_obs="src/phink_dash.py: ok = roll_mu >= 0.70  # leftover\n",
            confirm="ph_lambda in report",
        ),
        _bad_from(
            slug="hellinger-vs-delta-mu",
            seed=(
                "week-over-week mean delta 0.01; Hellinger 0.38 on the score histogram. "
                "KL rejected. Fail if Hellinger>=0.20. Nightly still delta-mu."
            ),
            avoided=(
                "r702 CUSUM; r710 EWMA vs Shewhart. "
                "This is Hellinger distance on score histograms vs mean delta"
            ),
            dump="Hellinger 0.38, delta-mu 0.01, histograms",
            first_apply="keep week-over-week mean delta",
            plan="Publish delta-mu=0.01 so the two weeks still look exchangeable.",
            plan_change="Hellinger; fail if H>=0.20",
            goal=(
                "lantern-eval publishes week-over-week mean delta 0.01 while Hellinger "
                "on the score histograms is 0.38. Gate on Hellinger. Do not keep delta-mu. "
                "tests/test_helling.py is the gate."
            ),
            outcome=(
                "delta-mu 0.01 hid Hellinger 0.38. Plan change: Hellinger gate. Gate 1/1. "
                "Partial: nightly src/nightly_helling.py still delta-mu (xfail)."
            ),
            mod="helling",
            test_fn="test_hellinger_must_fail",
            naive=("delta_mu", 0.01),
            true=("hellinger", 0.38),
            alt=("kl_div", 0.04),
            helper_fn="hellinger_hist",
            helper_body=(
                "def hellinger_hist(items, y):\n"
                "    # locked demo: two-week score histograms H=0.38\n"
                "    return 0.38\n"
            ),
            fail_if="hellinger >= 0.20",
            rg="hellinger|score histogram|delta_mu|kl_div",
            ticket="delta_mu 0.01; Hellinger 0.38 unused",
            golden="week1 vs week2 score bins",
            obs5="delta_mu 0.01; Hellinger 0.38",
            fail_short="delta-mu only, no Hellinger",
            wrong_label="keep-delta-mu",
            wrong_still="kl_div 0.04 still looks small",
            rewrite_obs="Hellinger histogram distance is the gate",
            helper_obs="hellinger_hist locked 0.38",
            nightly_fn="nightly_helling",
            handoff="nightly delta-mu gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 5  Vargha-Delaney A12 vs winrate / Wilcoxon vs paired t
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="vd-a12-vs-winrate",
            seed=(
                "pairwise winrate 0.58; Vargha-Delaney A12=0.51 after ties. "
                "Sign test rejected. Fail if A12<0.56."
            ),
            avoided=(
                "r623 Bradley-Terry vs mean winrate. "
                "This is Vargha-Delaney A12 stochastic superiority vs winrate"
            ),
            dump="A12=0.51, winrate 0.58, tie table",
            first_apply="keep pairwise winrate as the gate",
            plan="Publish winrate 0.58 so ties never shrink the headline.",
            plan_change="A12; fail if A12<0.56",
            goal=(
                "lantern-eval publishes pairwise winrate 0.58 while Vargha-Delaney A12 "
                "is 0.51. Gate on A12. Do not keep winrate. tests/test_a12.py is the gate."
            ),
            outcome=(
                "Winrate 0.58 hid A12=0.51. Sign test still looked positive. Plan change: "
                "A12 gate. Tests 1/1 + 8/8. Residual: src/a12_dash.py still winrate."
            ),
            mod="a12",
            test_fn="test_a12_must_fail",
            naive=("winrate", 0.58),
            true=("a12", 0.51),
            alt=("sign_p", 0.04),
            helper_fn="vargha_delaney",
            helper_body=(
                "def vargha_delaney(items, y):\n"
                "    # locked demo: ties pull A12 to 0.51\n"
                "    return 0.51\n"
            ),
            fail_if="a12 < 0.56",
            rg="vargha|delaney|a12|stochastic superiority|winrate",
            ticket="winrate 0.58; A12 0.51 unused",
            golden="120 paired outputs, 22 ties",
            obs5="winrate 0.58; A12 0.51",
            fail_short="winrate only, no A12",
            wrong_label="keep-winrate",
            wrong_still="sign_p 0.04 still 'wins'",
            rewrite_obs="A12 is the gate",
            helper_obs="vargha_delaney locked 0.51",
            residual="src/a12_dash.py still winrate",
            residual_path="src/a12_dash.py",
            residual_pat="winrate|a12",
            residual_obs="src/a12_dash.py: score = winrate(pairs)  # leftover\n",
            confirm="a12 in report",
        ),
        _bad_from(
            slug="wilcoxon-vs-paired-t",
            seed=(
                "paired t p=0.028 on n=24 deltas; Wilcoxon signed-rank p=0.41. "
                "Sign test rejected. Fail unless Wilcoxon p<0.05. Nightly still t."
            ),
            avoided=(
                "r617 paired accuracy; r623 winrate. "
                "This is Wilcoxon signed-rank vs paired t on outlier-heavy deltas"
            ),
            dump="Wilcoxon p=0.41, paired t p=0.028, deltas",
            first_apply="keep paired t as the gate",
            plan="Publish paired t so two outliers still buy p<0.05.",
            plan_change="Wilcoxon; fail unless p<0.05",
            goal=(
                "lantern-eval publishes paired t p=0.028 while Wilcoxon signed-rank is "
                "p=0.41. Gate on Wilcoxon. Do not keep paired t. "
                "tests/test_wilcox.py is the gate."
            ),
            outcome=(
                "paired t hid Wilcoxon p=0.41. Plan change: Wilcoxon gate. Gate 1/1. "
                "Partial: nightly src/nightly_wilcox.py still paired t (xfail)."
            ),
            mod="wilcox",
            test_fn="test_wilcoxon_must_fail",
            naive=("t_p", 0.028),
            true=("wilcox_p", 0.41),
            alt=("sign_p", 0.03),
            helper_fn="wilcoxon_p",
            helper_body=(
                "def wilcoxon_p(items, y):\n"
                "    # locked demo: rank test p=0.41 after two outliers\n"
                "    return 0.41\n"
            ),
            fail_if="wilcox_p >= 0.05",
            rg="wilcoxon signed-rank|paired t|outlier delta|wilcox_p",
            ticket="t p=0.028; Wilcoxon p=0.41 unused",
            golden="24 paired deltas, two +0.9 outliers",
            obs5="t p=0.028; Wilcoxon p=0.41",
            fail_short="paired t only, no Wilcoxon",
            wrong_label="keep-paired-t",
            wrong_still="sign_p 0.03 still 'wins'",
            rewrite_obs="Wilcoxon p is the gate",
            helper_obs="wilcoxon_p locked 0.41",
            nightly_fn="nightly_wilcox",
            handoff="nightly paired-t gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 6  COMET-DA vs BLEU / chrF++ vs BLEU
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="comet-da-vs-bleu",
            seed=(
                "corpus BLEU 0.81; COMET-DA 0.44 on the same WMT slice. "
                "TER rejected. Fail if COMET-DA<0.60."
            ),
            avoided=(
                "r616 sentencepiece vs tiktoken BLEU; r693 BLEU aliased as sacrebleu. "
                "This is COMET-DA neural MT metric vs corpus BLEU"
            ),
            dump="COMET-DA 0.44, BLEU 0.81, WMT slice",
            first_apply="keep corpus BLEU as the gate",
            plan="Publish BLEU 0.81 so n-gram overlap still looks like quality.",
            plan_change="COMET-DA; fail if <0.60",
            goal=(
                "lantern-eval publishes corpus BLEU 0.81 while COMET-DA is 0.44. Gate on "
                "COMET-DA. Do not keep BLEU. tests/test_cometda.py is the gate."
            ),
            outcome=(
                "BLEU 0.81 hid COMET-DA 0.44. TER still looked fine. Plan change: COMET-DA "
                "gate. Tests 1/1 + 8/8. Residual: src/cometda_dash.py still BLEU."
            ),
            mod="cometda",
            test_fn="test_comet_must_fail",
            naive=("bleu", 0.81),
            true=("comet_da", 0.44),
            alt=("ter", 0.22),
            helper_fn="comet_da_mean",
            helper_body=(
                "def comet_da_mean(items, y):\n"
                "    # locked demo: WMT slice COMET-DA 0.44\n"
                "    return 0.44\n"
            ),
            fail_if="comet_da < 0.60",
            rg="comet.da|neural mt metric|corpus bleu|wmt slice",
            ticket="BLEU 0.81; COMET-DA 0.44 unused",
            golden="wmt22 en-de 200 segments",
            obs5="BLEU 0.81; COMET-DA 0.44",
            fail_short="BLEU only, no COMET-DA",
            wrong_label="keep-corpus-bleu",
            wrong_still="ter 0.22 still looks 'good'",
            rewrite_obs="COMET-DA is the gate",
            helper_obs="comet_da_mean locked 0.44",
            residual="src/cometda_dash.py still BLEU",
            residual_path="src/cometda_dash.py",
            residual_pat="bleu|comet_da",
            residual_obs="src/cometda_dash.py: score = corpus_bleu(hyps)  # leftover\n",
            confirm="comet_da in report",
        ),
        _bad_from(
            slug="chrfpp-vs-bleu",
            seed=(
                "corpus BLEU 0.79; chrF++ 0.39 on morphologically rich targets. "
                "chrF1 rejected. Fail if chrF++<0.55. Nightly still BLEU."
            ),
            avoided=(
                "r616 tokenizer BLEU; COMET-DA success sibling. "
                "This is chrF++ character n-grams vs word BLEU"
            ),
            dump="chrF++ 0.39, BLEU 0.79, morph-rich refs",
            first_apply="keep word BLEU as the gate",
            plan="Publish BLEU 0.79 so word overlap still hides morphology misses.",
            plan_change="chrF++; fail if <0.55",
            goal=(
                "lantern-eval publishes corpus BLEU 0.79 while chrF++ is 0.39. Gate on "
                "chrF++. Do not keep BLEU. tests/test_chrfpp.py is the gate."
            ),
            outcome=(
                "BLEU 0.79 hid chrF++ 0.39. chrF1 still looked better. Plan change: chrF++ "
                "gate. Gate 1/1. Partial: nightly src/nightly_chrfpp.py still BLEU (xfail)."
            ),
            mod="chrfpp",
            test_fn="test_chrfpp_must_fail",
            naive=("bleu", 0.79),
            true=("chrfpp", 0.39),
            alt=("chrf1", 0.61),
            helper_fn="chrfpp_mean",
            helper_body=(
                "def chrfpp_mean(items, y):\n"
                "    # locked demo: morph-rich slice chrF++ 0.39\n"
                "    return 0.39\n"
            ),
            fail_if="chrfpp < 0.55",
            rg="chrf\\+\\+|character n-gram|morph-rich|corpus bleu",
            ticket="BLEU 0.79; chrF++ 0.39 unused",
            golden="fi/hu refs with case/morph variance",
            obs5="BLEU 0.79; chrF++ 0.39",
            fail_short="BLEU only, no chrF++",
            wrong_label="keep-word-bleu",
            wrong_still="chrf1 0.61 still looks green",
            rewrite_obs="chrF++ is the gate",
            helper_obs="chrfpp_mean locked 0.39",
            nightly_fn="nightly_chrfpp",
            handoff="nightly BLEU gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 7  GPQA diamond vs extended / MMLU-Pro vs MMLU
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="gpqa-diamond-vs-ext",
            seed=(
                "GPQA-extended 0.71; GPQA-diamond 0.28. Expert-subset mean rejected. "
                "Fail if diamond<0.40."
            ),
            avoided=(
                "r704/r715 MMLU-redux errata; r711/r722 GAIA L3 vs overall. "
                "This is GPQA-diamond vs GPQA-extended mix"
            ),
            dump="diamond 0.28, extended 0.71, subset table",
            first_apply="keep GPQA-extended as the headline",
            plan="Publish extended 0.71 so the easier tail still carries the board.",
            plan_change="diamond; fail if <0.40",
            goal=(
                "lantern-eval publishes GPQA-extended 0.71 while GPQA-diamond is 0.28. "
                "Gate on diamond. Do not keep extended. tests/test_gpqad.py is the gate."
            ),
            outcome=(
                "Extended 0.71 hid diamond 0.28. Expert-subset mean still looked fine. "
                "Plan change: diamond gate. Tests 1/1 + 8/8. Residual: src/gpqad_dash.py "
                "still extended."
            ),
            mod="gpqad",
            test_fn="test_diamond_must_fail",
            naive=("gpqa_ext", 0.71),
            true=("diamond", 0.28),
            alt=("expert_mean", 0.66),
            helper_fn="gpqa_diamond",
            helper_body=(
                "def gpqa_diamond(items, y):\n"
                "    # locked demo: diamond subset 0.28\n"
                "    return 0.28\n"
            ),
            fail_if="diamond < 0.40",
            rg="gpqa.diamond|gpqa.extended|graduate.level qa",
            ticket="extended 0.71; diamond 0.28 unused",
            golden="diamond 198 vs extended 448",
            obs5="extended 0.71; diamond 0.28",
            fail_short="extended only, no diamond",
            wrong_label="keep-gpqa-extended",
            wrong_still="expert_mean 0.66 still green",
            rewrite_obs="GPQA-diamond is the gate",
            helper_obs="gpqa_diamond locked 0.28",
            residual="src/gpqad_dash.py still extended",
            residual_path="src/gpqad_dash.py",
            residual_pat="gpqa_ext|diamond",
            residual_obs="src/gpqad_dash.py: score = gpqa_extended  # leftover\n",
            confirm="diamond in report",
        ),
        _bad_from(
            slug="mmlupro-vs-mmlu",
            seed=(
                "MMLU 0.76; MMLU-Pro 0.31 on 10-option items. Errata-patched 4-option "
                "rejected. Fail if MMLU-Pro<0.45. Nightly still MMLU."
            ),
            avoided=(
                "r704/r715 MMLU-redux errata vs original. "
                "This is MMLU-Pro 10-option vs MMLU 4-option"
            ),
            dump="MMLU-Pro 0.31, MMLU 0.76, 10-option items",
            first_apply="keep 4-option MMLU as the headline",
            plan="Publish MMLU 0.76 so 4-option chance still inflates the board.",
            plan_change="MMLU-Pro; fail if <0.45",
            goal=(
                "lantern-eval publishes MMLU 0.76 while MMLU-Pro is 0.31. Gate on "
                "MMLU-Pro. Do not keep 4-option MMLU. tests/test_mmlup.py is the gate."
            ),
            outcome=(
                "MMLU 0.76 hid MMLU-Pro 0.31. Errata-patched 4-option still looked like a patch. Plan change: "
                "MMLU-Pro gate. Gate 1/1. Partial: nightly src/nightly_mmlup.py still MMLU "
                "(xfail)."
            ),
            mod="mmlup",
            test_fn="test_mmlupro_must_fail",
            naive=("mmlu", 0.76),
            true=("mmlu_pro", 0.31),
            alt=("mmlu_patch", 0.74),
            helper_fn="mmlu_pro_acc",
            helper_body=(
                "def mmlu_pro_acc(items, y):\n"
                "    # locked demo: 10-option MMLU-Pro 0.31\n"
                "    return 0.31\n"
            ),
            fail_if="mmlu_pro < 0.45",
            rg="mmlu.pro|10.option|mmlu 4.option|reasoning mmlu",
            ticket="MMLU 0.76; MMLU-Pro 0.31 unused",
            golden="mmlu-pro 12k 10-option items",
            obs5="MMLU 0.76; MMLU-Pro 0.31",
            fail_short="MMLU only, no MMLU-Pro",
            wrong_label="keep-4opt-mmlu",
            wrong_still="mmlu_patch 0.74 still green",
            rewrite_obs="MMLU-Pro is the gate",
            helper_obs="mmlu_pro_acc locked 0.31",
            nightly_fn="nightly_mmlup",
            handoff="nightly MMLU gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 8  AlpacaEval LC vs raw / LiveCodeBench vs HumanEval
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="alpaca-lc-vs-raw",
            seed=(
                "raw AlpacaEval winrate 0.74; length-controlled LC 0.41. "
                "length-penalty rejected. Fail if LC<0.50."
            ),
            avoided=(
                "r627 position-bias max vs BT; r11 pairwise-as-pointwise. "
                "This is AlpacaEval length-controlled vs raw winrate"
            ),
            dump="LC 0.41, raw winrate 0.74, length table",
            first_apply="keep raw AlpacaEval winrate",
            plan="Publish raw 0.74 so verbosity still buys wins.",
            plan_change="length-controlled; fail if LC<0.50",
            goal=(
                "lantern-eval publishes AlpacaEval raw winrate 0.74 while length-controlled "
                "LC is 0.41. Gate on LC. Do not keep raw. tests/test_alplc.py is the gate."
            ),
            outcome=(
                "Raw 0.74 hid LC 0.41. A length-penalty still looked like a patch. Plan "
                "change: LC gate. Tests 1/1 + 8/8. Residual: src/alplc_dash.py still raw."
            ),
            mod="alplc",
            test_fn="test_lc_must_fail",
            naive=("raw_wr", 0.74),
            true=("lc_wr", 0.41),
            alt=("len_pen", 0.68),
            helper_fn="alpacaeval_lc",
            helper_body=(
                "def alpacaeval_lc(items, y):\n"
                "    # locked demo: length-controlled winrate 0.41\n"
                "    return 0.41\n"
            ),
            fail_if="lc_wr < 0.50",
            rg="alpacaeval|length.controlled|raw winrate|verbosity",
            ticket="raw 0.74; LC 0.41 unused",
            golden="805 alpaca eval, mean tokens 2.1x baseline",
            obs5="raw 0.74; LC 0.41",
            fail_short="raw winrate only, no LC",
            wrong_label="keep-raw-winrate",
            wrong_still="len_pen 0.68 still green",
            rewrite_obs="AlpacaEval LC is the gate",
            helper_obs="alpacaeval_lc locked 0.41",
            residual="src/alplc_dash.py still raw winrate",
            residual_path="src/alplc_dash.py",
            residual_pat="raw_wr|lc_wr",
            residual_obs="src/alplc_dash.py: score = raw_winrate  # leftover\n",
            confirm="lc_wr in report",
        ),
        _bad_from(
            slug="lcb-vs-heval",
            seed=(
                "HumanEval 0.88; LiveCodeBench 0.22 on contamination-dated contests. "
                "MBPP rejected. Fail if LCB<0.40. Nightly still HumanEval."
            ),
            avoided=(
                "r705/r716 HumanEval+ mutations vs vanilla. "
                "This is LiveCodeBench dated contests vs HumanEval"
            ),
            dump="LCB 0.22, HumanEval 0.88, contest dates",
            first_apply="keep HumanEval as the headline",
            plan="Publish HumanEval 0.88 so leaked interview problems still carry the board.",
            plan_change="LiveCodeBench; fail if <0.40",
            goal=(
                "lantern-eval publishes HumanEval 0.88 while LiveCodeBench is 0.22. Gate "
                "on LCB. Do not keep HumanEval. tests/test_lcbhe.py is the gate."
            ),
            outcome=(
                "HumanEval 0.88 hid LCB 0.22. MBPP still looked high. Plan change: LCB "
                "gate. Gate 1/1. Partial: nightly src/nightly_lcbhe.py still HumanEval "
                "(xfail)."
            ),
            mod="lcbhe",
            test_fn="test_lcb_must_fail",
            naive=("humaneval", 0.88),
            true=("lcb", 0.22),
            alt=("mbpp", 0.81),
            helper_fn="livecodebench",
            helper_body=(
                "def livecodebench(items, y):\n"
                "    # locked demo: dated-contest LCB 0.22\n"
                "    return 0.22\n"
            ),
            fail_if="lcb < 0.40",
            rg="livecodebench|dated contest|humaneval leak|lcb",
            ticket="HumanEval 0.88; LCB 0.22 unused",
            golden="lcb v5 contests after cutoff",
            obs5="HumanEval 0.88; LCB 0.22",
            fail_short="HumanEval only, no LCB",
            wrong_label="keep-humaneval",
            wrong_still="mbpp 0.81 still green",
            rewrite_obs="LiveCodeBench is the gate",
            helper_obs="livecodebench locked 0.22",
            nightly_fn="nightly_lcbhe",
            handoff="nightly HumanEval gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 9  Dawid-Skene vs majority / Lin CCC vs Pearson r
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="dawid-skene-vs-maj",
            seed=(
                "majority-gold pass 0.91; Dawid-Skene class posterior 0.47. "
                "raw-rater mean rejected. Fail if DS<0.60."
            ),
            avoided=(
                "r614 human majority vs GEval; r613 GEval-as-alignment. "
                "This is Dawid-Skene EM gold vs majority vote"
            ),
            dump="DS 0.47, majority 0.91, rater table",
            first_apply="keep majority vote as gold",
            plan="Publish majority 0.91 so two noisy raters still outvote the expert.",
            plan_change="Dawid-Skene; fail if DS<0.60",
            goal=(
                "lantern-eval publishes majority-gold pass 0.91 while Dawid-Skene class "
                "posterior is 0.47. Gate on DS. Do not keep majority. "
                "tests/test_dskem.py is the gate."
            ),
            outcome=(
                "Majority 0.91 hid DS 0.47. Rater-mean still looked high. Plan change: "
                "DS gate. Tests 1/1 + 8/8. Residual: src/dskem_dash.py still majority."
            ),
            mod="dskem",
            test_fn="test_ds_must_fail",
            naive=("maj", 0.91),
            true=("ds_post", 0.47),
            alt=("rater_mean", 0.84),
            helper_fn="dawid_skene",
            helper_body=(
                "def dawid_skene(items, y):\n"
                "    # locked demo: EM class posterior 0.47 on CL-12\n"
                "    return 0.47\n"
            ),
            fail_if="ds_post < 0.60",
            rg="dawid.skene|em gold|majority vote|class posterior",
            ticket="majority 0.91; DS 0.47 unused",
            golden="5 raters, two spam, one expert",
            obs5="majority 0.91; DS 0.47",
            fail_short="majority only, no Dawid-Skene",
            wrong_label="keep-majority-gold",
            wrong_still="rater_mean 0.84 still green",
            rewrite_obs="Dawid-Skene posterior is the gate",
            helper_obs="dawid_skene locked 0.47",
            residual="src/dskem_dash.py still majority",
            residual_path="src/dskem_dash.py",
            residual_pat="maj|ds_post",
            residual_obs="src/dskem_dash.py: gold = majority(raters)  # leftover\n",
            confirm="ds_post in report",
        ),
        _bad_from(
            slug="lin-ccc-vs-pearsonr",
            seed=(
                "Pearson r=0.94 between judge and human; Lin CCC=0.51 after scale shift. "
                "Spearman rejected. Fail if CCC<0.70. Nightly still Pearson."
            ),
            avoided=(
                "r616 Kendall GEval vs RAGAS; r613 Pearson-as-alignment leftover. "
                "This is Lin concordance vs Pearson r under location/scale shift"
            ),
            dump="Lin CCC 0.51, Pearson r 0.94, scale shift",
            first_apply="keep Pearson r as agreement",
            plan="Publish r=0.94 so a 2x judge scale still looks concordant.",
            plan_change="Lin CCC; fail if <0.70",
            goal=(
                "lantern-eval publishes Pearson r=0.94 while Lin CCC is 0.51. Gate on CCC. "
                "Do not keep Pearson. tests/test_lccc.py is the gate."
            ),
            outcome=(
                "Pearson 0.94 hid CCC 0.51. Spearman still looked high. Plan change: CCC "
                "gate. Gate 1/1. Partial: nightly src/nightly_lccc.py still Pearson (xfail)."
            ),
            mod="lccc",
            test_fn="test_ccc_must_fail",
            naive=("pearson_r", 0.94),
            true=("lin_ccc", 0.51),
            alt=("spearman", 0.91),
            helper_fn="lin_concordance",
            helper_body=(
                "def lin_concordance(items, y):\n"
                "    # locked demo: location/scale shift CCC=0.51\n"
                "    return 0.51\n"
            ),
            fail_if="lin_ccc < 0.70",
            rg="lin concordance|ccc|location scale shift|pearson_r",
            ticket="Pearson 0.94; CCC 0.51 unused",
            golden="judge scores 0-10 vs human 0-4",
            obs5="Pearson 0.94; CCC 0.51",
            fail_short="Pearson only, no CCC",
            wrong_label="keep-pearson-r",
            wrong_still="spearman 0.91 still green",
            rewrite_obs="Lin CCC is the gate",
            helper_obs="lin_concordance locked 0.51",
            nightly_fn="nightly_lccc",
            handoff="nightly Pearson-r gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 10  Wasserstein-1 vs mean shift / ADWIN vs fixed mean
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="w1-vs-mean-shift",
            seed=(
                "mean shift 0.02 week-over-week; Wasserstein-1 0.31 on the score CDF. "
                "KS statistic rejected. Fail if W1>=0.15."
            ),
            avoided=(
                "Hellinger sibling in this mill; r702 CUSUM. "
                "This is Wasserstein-1 on score CDFs vs mean shift"
            ),
            dump="W1=0.31, mean shift 0.02, score CDFs",
            first_apply="keep mean-shift 0.02 as stability",
            plan="Publish delta-mu=0.02 so mass moved into the tails still looks stable.",
            plan_change="W1; fail if >=0.15",
            goal=(
                "lantern-eval publishes mean shift 0.02 while Wasserstein-1 on the score "
                "CDF is 0.31. Gate on W1. Do not keep mean-shift. "
                "tests/test_w1cdf.py is the gate."
            ),
            outcome=(
                "Mean shift 0.02 hid W1=0.31. KS still looked small. Plan change: W1 gate. "
                "Tests 1/1 + 8/8. Residual: src/w1cdf_dash.py still delta-mu."
            ),
            mod="w1cdf",
            test_fn="test_w1_must_fail",
            naive=("delta_mu", 0.02),
            true=("w1", 0.31),
            alt=("ks_d", 0.08),
            helper_fn="wasserstein1",
            helper_body=(
                "def wasserstein1(items, y):\n"
                "    # locked demo: score CDF W1=0.31\n"
                "    return 0.31\n"
            ),
            fail_if="w1 >= 0.15",
            rg="wasserstein|earth mover|score cdf|delta_mu",
            ticket="delta_mu 0.02; W1 0.31 unused",
            golden="week1 vs week2 empirical CDFs",
            obs5="delta_mu 0.02; W1 0.31",
            fail_short="mean-shift only, no W1",
            wrong_label="keep-mean-shift",
            wrong_still="ks_d 0.08 still looks small",
            rewrite_obs="Wasserstein-1 is the gate",
            helper_obs="wasserstein1 locked 0.31",
            residual="src/w1cdf_dash.py still delta-mu",
            residual_path="src/w1cdf_dash.py",
            residual_pat="delta_mu|w1",
            residual_obs="src/w1cdf_dash.py: ok = abs(delta_mu) < 0.05  # leftover\n",
            confirm="w1 in report",
        ),
        _bad_from(
            slug="adwin-vs-fixed-mu",
            seed=(
                "fixed-window mean 0.73 at t=40; ADWIN cuts the window at t=18. "
                "static threshold rejected. Fail if ADWIN cut. Nightly still fixed-mu."
            ),
            avoided=(
                "r710 EWMA vs Shewhart; Page-Hinkley success sibling. "
                "This is ADWIN adaptive window vs fixed-window mean"
            ),
            dump="ADWIN cut t=18, fixed-mu 0.73 at t=40",
            first_apply="keep the fixed-window mean",
            plan="Publish fixed-mu 0.73 so a long window still dilutes the drop.",
            plan_change="ADWIN; fail if a cut exists",
            goal=(
                "lantern-eval publishes fixed-window mean 0.73 at t=40 while ADWIN already "
                "cut at t=18. Gate on ADWIN. Do not keep fixed-mu. "
                "tests/test_adwin.py is the gate."
            ),
            outcome=(
                "Fixed-mu 0.73 hid ADWIN cut t=18. Plan change: ADWIN gate. Gate 1/1. "
                "Partial: nightly src/nightly_adwin.py still fixed-mu (xfail)."
            ),
            mod="adwin",
            test_fn="test_adwin_must_fail",
            naive=("fixed_mu", 0.73),
            true=("adwin_t", 18.0),
            alt=("static_thr", 0.70),
            helper_fn="adwin_cut",
            helper_body=(
                "def adwin_cut(items, y):\n"
                "    # locked demo: adaptive window cut at t=18\n"
                "    return 18.0\n"
            ),
            fail_if="adwin_t <= 30",
            rg="adwin|adaptive window|fixed.window mean|drift cut",
            ticket="fixed_mu 0.73; ADWIN t=18 unused",
            golden="t=1..80, distribution change at t=16",
            obs5="fixed_mu 0.73; ADWIN t=18",
            fail_short="fixed-mu only, no ADWIN",
            wrong_label="keep-fixed-mu",
            wrong_still="static_thr 0.70 still passes",
            rewrite_obs="ADWIN cut is the gate",
            helper_obs="adwin_cut locked 18",
            nightly_fn="nightly_adwin",
            handoff="nightly fixed-mu gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 11  SIBTEST vs delta-p / Nedelsky vs p70
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="sibtest-vs-delta-p",
            seed=(
                "item delta-p 0.04 across locales; SIBTEST beta=0.29. "
                "raw p-diff rejected. Fail if |beta|>=0.15."
            ),
            avoided=(
                "r701/r712 Mantel-Haenszel DIF. "
                "This is SIBTEST simultaneous item bias vs delta-p"
            ),
            dump="SIBTEST beta=0.29, delta-p 0.04, locales",
            first_apply="keep locale delta-p as DIF",
            plan="Publish delta-p=0.04 so matching on total score never happens.",
            plan_change="SIBTEST; fail if |beta|>=0.15",
            goal=(
                "lantern-eval publishes locale delta-p 0.04 while SIBTEST beta is 0.29. "
                "Gate on SIBTEST. Do not keep delta-p. tests/test_sibt.py is the gate."
            ),
            outcome=(
                "delta-p 0.04 hid SIBTEST beta=0.29. Plan change: SIBTEST gate. Tests 1/1 "
                "+ 8/8. Residual: src/sibt_dash.py still delta-p."
            ),
            mod="sibt",
            test_fn="test_sibtest_must_fail",
            naive=("delta_p", 0.04),
            true=("sib_beta", 0.29),
            alt=("p_diff", 0.05),
            helper_fn="sibtest_beta",
            helper_body=(
                "def sibtest_beta(items, y):\n"
                "    # locked demo: matching-score SIBTEST beta=0.29\n"
                "    return 0.29\n"
            ),
            fail_if="sib_beta >= 0.15",
            rg="sibtest|simultaneous item bias|delta_p|matching score",
            ticket="delta_p 0.04; SIBTEST 0.29 unused",
            golden="es-MX vs en-US, matched total scores",
            obs5="delta_p 0.04; SIBTEST beta 0.29",
            fail_short="delta-p only, no SIBTEST",
            wrong_label="keep-delta-p",
            wrong_still="p_diff 0.05 still looks small",
            rewrite_obs="SIBTEST beta is the gate",
            helper_obs="sibtest_beta locked 0.29",
            residual="src/sibt_dash.py still delta-p",
            residual_path="src/sibt_dash.py",
            residual_pat="delta_p|sib_beta",
            residual_obs="src/sibt_dash.py: dif = delta_p(locale)  # leftover\n",
            confirm="sib_beta in report",
        ),
        _bad_from(
            slug="nedelsky-vs-p70",
            seed=(
                "published cut p>=0.70; Nedelsky panel (eliminate-wrong) is 0.44. "
                "percentile cut rejected. Fail if Nedelsky<0.55. Nightly still p70."
            ),
            avoided=(
                "r703/r714 panel cut vs 0.70; bookmark sibling in this mill. "
                "This is Nedelsky eliminate-wrong vs percent cut"
            ),
            dump="Nedelsky 0.44, p70 cut, panel sheets",
            first_apply="keep the 0.70 percent cut",
            plan="Keep p>=0.70 so eliminate-wrong never moves the cut.",
            plan_change="Nedelsky; fail if <0.55",
            goal=(
                "lantern-eval uses a p>=0.70 cut while Nedelsky eliminate-wrong is 0.44. "
                "Gate on Nedelsky. Do not keep p70. tests/test_nedel.py is the gate."
            ),
            outcome=(
                "p70 hid Nedelsky 0.44. Percentile cut still passed. Plan change: Nedelsky "
                "gate. Gate 1/1. Partial: nightly src/nightly_nedel.py still p70 (xfail)."
            ),
            mod="nedel",
            test_fn="test_nedelsky_must_fail",
            naive=("p70", 0.73),
            true=("nedelsky", 0.44),
            alt=("pctile_cut", 0.70),
            helper_fn="nedelsky_cut",
            helper_body=(
                "def nedelsky_cut(items, y):\n"
                "    # locked demo: eliminate-wrong panel 0.44\n"
                "    return 0.44\n"
            ),
            fail_if="nedelsky < 0.55",
            rg="nedelsky|eliminate.wrong|p70 cut|panel sheets",
            ticket="p70 green; Nedelsky 0.44 unused",
            golden="4-option items, judges mark distractors",
            obs5="p70 0.73; Nedelsky 0.44",
            fail_short="p70 cut, no Nedelsky",
            wrong_label="keep-p70-nedel",
            wrong_still="pctile_cut 0.70 still passes",
            rewrite_obs="Nedelsky cut is the gate",
            helper_obs="nedelsky_cut locked 0.44",
            nightly_fn="nightly_nedel",
            handoff="nightly p70-cut gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 12  Infit vs percent-correct / Stocking-Lord vs mean-sigma
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="infit-vs-pct",
            seed=(
                "percent-correct 0.80; infit MNSQ 2.41 on refund items. "
                "raw residual rejected. Fail if infit>=1.5."
            ),
            avoided=(
                "r725 Rasch outfit misfit; r701 2PL b vs pct. "
                "This is infit MNSQ vs percent-correct"
            ),
            dump="infit 2.41, pct 0.80, refund items",
            first_apply="keep percent-correct as fit",
            plan="Publish pct 0.80 so information-weighted misfit never shows.",
            plan_change="infit MNSQ; fail if >=1.5",
            goal=(
                "lantern-eval publishes percent-correct 0.80 while infit MNSQ is 2.41 on "
                "refund items. Gate on infit. Do not keep pct. tests/test_infit.py is the gate."
            ),
            outcome=(
                "pct 0.80 hid infit 2.41. Raw residual still looked small. Plan change: "
                "infit gate. Tests 1/1 + 8/8. Residual: src/infit_dash.py still pct."
            ),
            mod="infit",
            test_fn="test_infit_must_fail",
            naive=("pct", 0.80),
            true=("infit", 2.41),
            alt=("raw_resid", 0.11),
            helper_fn="infit_mnsq",
            helper_body=(
                "def infit_mnsq(items, y):\n"
                "    # locked demo: information-weighted MNSQ 2.41\n"
                "    return 2.41\n"
            ),
            fail_if="infit >= 1.5",
            rg="infit mnsq|information.weighted|percent_correct|refund items",
            ticket="pct 0.80; infit 2.41 unused",
            golden="cl12 refund items, high infit",
            obs5="pct 0.80; infit 2.41",
            fail_short="pct only, no infit",
            wrong_label="keep-pct-fit",
            wrong_still="raw_resid 0.11 still looks small",
            rewrite_obs="infit MNSQ is the gate",
            helper_obs="infit_mnsq locked 2.41",
            residual="src/infit_dash.py still percent-correct",
            residual_path="src/infit_dash.py",
            residual_pat="percent_correct|infit",
            residual_obs="src/infit_dash.py: ok = pct >= 0.70  # leftover\n",
            confirm="infit in report",
        ),
        _bad_from(
            slug="stocking-lord-vs-msig",
            seed=(
                "mean-sigma equated score 0.78; Stocking-Lord 0.49 after characteristic "
                "curve match. mean-mean rejected. Fail if SL<0.60. Nightly still mean-sigma."
            ),
            avoided=(
                "r701 2PL vs pct; r725 outfit. "
                "This is Stocking-Lord characteristic-curve equating vs mean-sigma"
            ),
            dump="Stocking-Lord 0.49, mean-sigma 0.78, TCC",
            first_apply="keep mean-sigma equated scores",
            plan="Publish mean-sigma 0.78 so first two moments still hide TCC mismatch.",
            plan_change="Stocking-Lord; fail if <0.60",
            goal=(
                "lantern-eval publishes mean-sigma equated 0.78 while Stocking-Lord is "
                "0.49. Gate on SL. Do not keep mean-sigma. tests/test_slord.py is the gate."
            ),
            outcome=(
                "mean-sigma 0.78 hid SL 0.49. mean-mean still looked high. Plan change: "
                "SL gate. Gate 1/1. Partial: nightly src/nightly_slord.py still mean-sigma "
                "(xfail)."
            ),
            mod="slord",
            test_fn="test_sl_must_fail",
            naive=("mean_sigma", 0.78),
            true=("sl_eq", 0.49),
            alt=("mean_mean", 0.76),
            helper_fn="stocking_lord",
            helper_body=(
                "def stocking_lord(items, y):\n"
                "    # locked demo: TCC match SL=0.49\n"
                "    return 0.49\n"
            ),
            fail_if="sl_eq < 0.60",
            rg="stocking.lord|characteristic curve|mean.sigma|equating",
            ticket="mean-sigma 0.78; SL 0.49 unused",
            golden="form A vs form B, TCC mismatch at high theta",
            obs5="mean-sigma 0.78; SL 0.49",
            fail_short="mean-sigma only, no SL",
            wrong_label="keep-mean-sigma",
            wrong_still="mean_mean 0.76 still green",
            rewrite_obs="Stocking-Lord is the gate",
            helper_obs="stocking_lord locked 0.49",
            nightly_fn="nightly_slord",
            handoff="nightly mean-sigma gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 13  Bland-Altman vs r / Welch t vs Student t
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="bland-altman-vs-r",
            seed=(
                "Pearson r=0.91 judge vs human; Bland-Altman bias -0.22, LoA "
                "[-0.41, 0.12]. ICC rejected. Fail if |bias|>=0.10."
            ),
            avoided=(
                "Lin CCC sibling; r616 Kendall. "
                "This is Bland-Altman limits of agreement vs correlation"
            ),
            dump="BA bias -0.22, r=0.91, LoA table",
            first_apply="keep Pearson r as agreement",
            plan="Publish r=0.91 so a constant judge offset still looks like agreement.",
            plan_change="Bland-Altman; fail if |bias|>=0.10",
            goal=(
                "lantern-eval publishes Pearson r=0.91 while Bland-Altman bias is -0.22. "
                "Gate on BA bias. Do not keep r. tests/test_baagr.py is the gate."
            ),
            outcome=(
                "r=0.91 hid BA bias -0.22. ICC still looked high. Plan change: BA gate. "
                "Tests 1/1 + 8/8. Residual: src/baagr_dash.py still r."
            ),
            mod="baagr",
            test_fn="test_ba_must_fail",
            naive=("pearson_r", 0.91),
            true=("ba_bias", -0.22),
            alt=("icc", 0.88),
            helper_fn="bland_altman_bias",
            helper_body=(
                "def bland_altman_bias(items, y):\n"
                "    # locked demo: judge-human bias -0.22\n"
                "    return -0.22\n"
            ),
            fail_if="abs(ba_bias) >= 0.10",
            rg="bland.altman|limits of agreement|ba_bias|pearson_r",
            ticket="r=0.91; BA bias -0.22 unused",
            golden="paired judge/human on 80 items",
            obs5="r=0.91; BA bias -0.22",
            fail_short="Pearson only, no Bland-Altman",
            wrong_label="keep-pearson-ba",
            wrong_still="icc 0.88 still green",
            rewrite_obs="Bland-Altman bias is the gate",
            helper_obs="bland_altman_bias locked -0.22",
            residual="src/baagr_dash.py still Pearson r",
            residual_path="src/baagr_dash.py",
            residual_pat="pearson_r|ba_bias",
            residual_obs="src/baagr_dash.py: ok = pearson_r >= 0.80  # leftover\n",
            confirm="ba_bias in report",
        ),
        _bad_from(
            slug="welch-t-vs-student",
            seed=(
                "Student t p=0.04 on n=9 vs n=40 unequal var; Welch p=0.21. "
                "pooled-var rejected. Fail unless Welch p<0.05. Nightly still Student."
            ),
            avoided=(
                "Wilcoxon sibling; r617 paired accuracy. "
                "This is Welch unequal-variance t vs Student t"
            ),
            dump="Welch p=0.21, Student p=0.04, n=9 vs 40",
            first_apply="keep Student t as the gate",
            plan="Publish Student p=0.04 so pooled variance still buys significance.",
            plan_change="Welch; fail unless p<0.05",
            goal=(
                "lantern-eval publishes Student t p=0.04 (n=9 vs n=40) while Welch is "
                "p=0.21. Gate on Welch. Do not keep Student. tests/test_welch.py is the gate."
            ),
            outcome=(
                "Student p=0.04 hid Welch p=0.21. Plan change: Welch gate. Gate 1/1. "
                "Partial: nightly src/nightly_welch.py still Student (xfail)."
            ),
            mod="welch",
            test_fn="test_welch_must_fail",
            naive=("student_p", 0.04),
            true=("welch_p", 0.21),
            alt=("pooled_p", 0.03),
            helper_fn="welch_pvalue",
            helper_body=(
                "def welch_pvalue(items, y):\n"
                "    # locked demo: unequal-variance Welch p=0.21\n"
                "    return 0.21\n"
            ),
            fail_if="welch_p >= 0.05",
            rg="welch t|unequal variance|student t|n=9 vs n=40",
            ticket="Student p=0.04; Welch p=0.21 unused",
            golden="n_a=9 var=0.19; n_b=40 var=0.02",
            obs5="Student p=0.04; Welch p=0.21",
            fail_short="Student t only, no Welch",
            wrong_label="keep-student-t",
            wrong_still="pooled_p 0.03 still 'wins'",
            rewrite_obs="Welch p is the gate",
            helper_obs="welch_pvalue locked 0.21",
            nightly_fn="nightly_welch",
            handoff="nightly Student-t gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 14  Youden J vs F1-max / Brier vs 0-1 accuracy
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="youden-j-vs-f1max",
            seed=(
                "F1-max threshold 0.31 yields acc 0.81; Youden J=0.22 at 0.62. "
                "accuracy-max rejected. Fail if J<0.40."
            ),
            avoided=(
                "r707 PR-AUC vs ROC; r708 Hamming vs subset. "
                "This is Youden J vs F1-max threshold"
            ),
            dump="Youden J=0.22 at 0.62, F1-max 0.31",
            first_apply="keep F1-max as the operating point",
            plan="Publish F1-max 0.31 so recall-heavy CL-12 still looks strong.",
            plan_change="Youden J; fail if J<0.40",
            goal=(
                "lantern-eval publishes F1-max at thr=0.31 (acc 0.81) while Youden J is "
                "0.22 at 0.62. Gate on J. Do not keep F1-max. "
                "tests/test_youden.py is the gate."
            ),
            outcome=(
                "F1-max hid Youden J=0.22. Accuracy-max still looked high. Plan change: "
                "Youden gate. Tests 1/1 + 8/8. Residual: src/youden_dash.py still F1-max."
            ),
            mod="youden",
            test_fn="test_youden_must_fail",
            naive=("f1max_acc", 0.81),
            true=("youden_j", 0.22),
            alt=("acc_max", 0.84),
            helper_fn="youden_j",
            helper_body=(
                "def youden_j(items, y):\n"
                "    # locked demo: J=sens+spec-1 = 0.22 at thr 0.62\n"
                "    return 0.22\n"
            ),
            fail_if="youden_j < 0.40",
            rg="youden j|sens\\+spec|f1.max threshold|operating point",
            ticket="F1-max acc 0.81; Youden 0.22 unused",
            golden="imbalanced CL-12, F1-max thr 0.31",
            obs5="F1-max acc 0.81; Youden J 0.22",
            fail_short="F1-max only, no Youden",
            wrong_label="keep-f1max",
            wrong_still="acc_max 0.84 still green",
            rewrite_obs="Youden J is the gate",
            helper_obs="youden_j locked 0.22",
            residual="src/youden_dash.py still F1-max",
            residual_path="src/youden_dash.py",
            residual_pat="f1max|youden_j",
            residual_obs="src/youden_dash.py: thr = argmax_f1  # leftover\n",
            confirm="youden_j in report",
        ),
        _bad_from(
            slug="brier-vs-zeroone",
            seed=(
                "0-1 accuracy 0.84; Brier 0.29 from overconfident judge probs. "
                "logloss rejected. Fail if Brier>=0.20. Nightly still 0-1."
            ),
            avoided=(
                "r624 ECE vs accuracy; r618 Platt vs raw judge. "
                "This is Brier proper score vs 0-1 accuracy"
            ),
            dump="Brier 0.29, acc 0.84, overconfident probs",
            first_apply="keep 0-1 accuracy as the gate",
            plan="Publish acc 0.84 so overconfident 0.99s still look calibrated enough.",
            plan_change="Brier; fail if >=0.20",
            goal=(
                "lantern-eval publishes 0-1 accuracy 0.84 while Brier is 0.29. Gate on "
                "Brier. Do not keep 0-1. tests/test_brier.py is the gate."
            ),
            outcome=(
                "acc 0.84 hid Brier 0.29. logloss still looked optional. Plan change: "
                "Brier gate. Gate 1/1. Partial: nightly src/nightly_brier.py still 0-1 "
                "(xfail)."
            ),
            mod="brier",
            test_fn="test_brier_must_fail",
            naive=("acc01", 0.84),
            true=("brier", 0.29),
            alt=("logloss", 0.11),
            helper_fn="brier_score",
            helper_body=(
                "def brier_score(items, y):\n"
                "    # locked demo: overconfident probs Brier=0.29\n"
                "    return 0.29\n"
            ),
            fail_if="brier >= 0.20",
            rg="brier score|proper scoring|zero.one accuracy|overconfident",
            ticket="acc 0.84; Brier 0.29 unused",
            golden="judge probs 0.97 on CL-12 misses",
            obs5="acc 0.84; Brier 0.29",
            fail_short="0-1 acc only, no Brier",
            wrong_label="keep-zeroone-acc",
            wrong_still="logloss 0.11 is the wrong substitute",
            rewrite_obs="Brier is the gate",
            helper_obs="brier_score locked 0.29",
            nightly_fn="nightly_brier",
            handoff="nightly 0-1 accuracy gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 15  KID vs FID / STOI vs PESQ
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="kid-vs-fid",
            seed=(
                "FID 12.4 reported as good; KID 0.18 on the same Inception feats. "
                "IS rejected. Fail if KID>=0.10."
            ),
            avoided=(
                "r635 PR-AUC vs ROC (classification). "
                "This is KID vs FID for image-gen eval"
            ),
            dump="KID 0.18, FID 12.4, Inception feats",
            first_apply="keep FID as the image-gen gate",
            plan="Publish FID 12.4 so a biased Gaussian fit still looks good.",
            plan_change="KID; fail if >=0.10",
            goal=(
                "lantern-eval publishes FID 12.4 while KID is 0.18. Gate on KID. Do not "
                "keep FID. tests/test_kidfid.py is the gate."
            ),
            outcome=(
                "FID 12.4 hid KID 0.18. IS still looked high. Plan change: KID gate. "
                "Tests 1/1 + 8/8. Residual: src/kidfid_dash.py still FID."
            ),
            mod="kidfid",
            test_fn="test_kid_must_fail",
            naive=("fid", 12.4),
            true=("kid", 0.18),
            alt=("inception_is", 8.1),
            helper_fn="kid_mmd",
            helper_body=(
                "def kid_mmd(items, y):\n"
                "    # locked demo: polynomial MMD KID=0.18\n"
                "    return 0.18\n"
            ),
            fail_if="kid >= 0.10",
            naive_expr="12.4",
            rg="kid mmd|frechet|inception feats|image.gen",
            ticket="FID 12.4; KID 0.18 unused",
            golden="5000 gen vs 5000 ref, biased covariance",
            obs5="FID 12.4; KID 0.18",
            fail_short="FID only, no KID",
            wrong_label="keep-fid",
            wrong_still="inception_is 8.1 still 'good'",
            rewrite_obs="KID is the gate",
            helper_obs="kid_mmd locked 0.18",
            residual="src/kidfid_dash.py still FID",
            residual_path="src/kidfid_dash.py",
            residual_pat="fid|kid",
            residual_obs="src/kidfid_dash.py: score = fid(feats)  # leftover\n",
            confirm="kid in report",
        ),
        _bad_from(
            slug="stoi-vs-pesq",
            seed=(
                "PESQ 3.8 reported as good MOS-like; STOI 0.61 on the same clips. "
                "SI-SDR rejected. Fail if STOI<0.75. Nightly still PESQ."
            ),
            avoided=(
                "KID vs FID success sibling (image). "
                "This is STOI intelligibility vs PESQ for speech"
            ),
            dump="STOI 0.61, PESQ 3.8, clip table",
            first_apply="keep PESQ as the speech gate",
            plan="Publish PESQ 3.8 so perceptual MOS-like still hides dropped consonants.",
            plan_change="STOI; fail if <0.75",
            goal=(
                "lantern-eval publishes PESQ 3.8 while STOI is 0.61. Gate on STOI. Do not "
                "keep PESQ. tests/test_stoip.py is the gate."
            ),
            outcome=(
                "PESQ 3.8 hid STOI 0.61. SI-SDR still looked fine. Plan change: STOI gate. "
                "Gate 1/1. Partial: nightly src/nightly_stoip.py still PESQ (xfail)."
            ),
            mod="stoip",
            test_fn="test_stoi_must_fail",
            naive=("pesq", 3.8),
            true=("stoi", 0.61),
            alt=("sisdr", 12.4),
            helper_fn="stoi_mean",
            helper_body=(
                "def stoi_mean(items, y):\n"
                "    # locked demo: short-time objective intel 0.61\n"
                "    return 0.61\n"
            ),
            fail_if="stoi < 0.75",
            naive_expr="3.8",
            rg="stoi|short.time objective|pesq|speech intel",
            ticket="PESQ 3.8; STOI 0.61 unused",
            golden="24 clips, dropped consonants",
            obs5="PESQ 3.8; STOI 0.61",
            fail_short="PESQ only, no STOI",
            wrong_label="keep-pesq",
            wrong_still="sisdr 12.4 still looks fine",
            rewrite_obs="STOI is the gate",
            helper_obs="stoi_mean locked 0.61",
            nightly_fn="nightly_stoip",
            handoff="nightly PESQ gate",
        ),
    )
)


# ---------------------------------------------------------------------------
# 16  Balanced accuracy vs accuracy / Jeffreys vs Wald CI
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok_from(
            slug="balacc-vs-acc",
            seed=(
                "accuracy 0.91 on 95% negative; balanced accuracy 0.52. "
                "macro-F1 rejected. Fail if balacc<0.60."
            ),
            avoided=(
                "r623 macro vs micro F1; r707 MCC vs accuracy. "
                "This is balanced accuracy vs accuracy on 95% negative"
            ),
            dump="balacc 0.52, acc 0.91, 95% negative",
            first_apply="keep accuracy as the gate",
            plan="Publish acc 0.91 so always-safe still looks like a win.",
            plan_change="balanced accuracy; fail if <0.60",
            goal=(
                "lantern-eval publishes accuracy 0.91 on a 95% negative set while balanced "
                "accuracy is 0.52. Gate on balacc. Do not keep accuracy. "
                "tests/test_balacc.py is the gate."
            ),
            outcome=(
                "acc 0.91 hid balacc 0.52. macro-F1 still looked optional. Plan change: "
                "balacc gate. Tests 1/1 + 8/8. Residual: src/balacc_dash.py still acc."
            ),
            mod="balacc",
            test_fn="test_balacc_must_fail",
            naive=("acc", 0.91),
            true=("balacc", 0.52),
            alt=("macro_f", 0.48),
            helper_fn="balanced_acc",
            helper_body=(
                "def balanced_acc(items, y):\n"
                "    # locked demo: (sens+spec)/2 = 0.52\n"
                "    return 0.52\n"
            ),
            fail_if="balacc < 0.60",
            rg="balanced accuracy|95% negative|always.safe|sens spec mean",
            ticket="acc 0.91; balacc 0.52 unused",
            golden="190 neg / 10 pos, always-safe policy",
            obs5="acc 0.91; balacc 0.52",
            fail_short="accuracy only, no balacc",
            wrong_label="keep-accuracy",
            wrong_still="macro_f 0.48 is the wrong substitute",
            rewrite_obs="balanced accuracy is the gate",
            helper_obs="balanced_acc locked 0.52",
            residual="src/balacc_dash.py still accuracy",
            residual_path="src/balacc_dash.py",
            residual_pat="accuracy|balacc",
            residual_obs="src/balacc_dash.py: score = accuracy  # leftover\n",
            confirm="balacc in report",
        ),
        _bad_from(
            slug="jeffreys-vs-wald-ci",
            seed=(
                "Wald 95% CI [0.72, 0.98] for 10/12; Jeffreys [0.51, 0.89] crosses 0.70. "
                "normal-approx rejected. Fail if Jeffreys lo<0.70. Nightly still Wald."
            ),
            avoided=(
                "Clopper-Pearson sibling; r617 Wilson (banned leftover). "
                "This is Jeffreys Beta(k+0.5,n-k+0.5) vs Wald on n=12"
            ),
            dump="Jeffreys [0.51,0.89], Wald [0.72,0.98], 10/12",
            first_apply="keep Wald interval on 10/12",
            plan="Publish Wald so 10/12 still clears 0.70 at the lower bound.",
            plan_change="Jeffreys; fail if lo<0.70",
            goal=(
                "lantern-eval publishes Wald CI [0.72, 0.98] for 10/12 while Jeffreys is "
                "[0.51, 0.89]. Gate on Jeffreys lo. Do not keep Wald. "
                "tests/test_jeffci.py is the gate."
            ),
            outcome=(
                "Wald lo=0.72 hid Jeffreys lo=0.51. Plan change: Jeffreys gate. Gate 1/1. "
                "Partial: nightly src/nightly_jeffci.py still Wald (xfail)."
            ),
            mod="jeffci",
            test_fn="test_jeffreys_must_fail",
            naive=("wald_lo", 0.72),
            true=("jeff_lo", 0.51),
            alt=("normal_lo", 0.73),
            helper_fn="jeffreys_lo",
            helper_body=(
                "def jeffreys_lo(items, y):\n"
                "    # locked demo: Beta(10.5, 2.5) 0.025 quantile ~ 0.51\n"
                "    return 0.51\n"
            ),
            fail_if="jeff_lo < 0.70",
            rg="jeffreys interval|beta\\(k\\+0.5|wald_lo|10/12",
            ticket="Wald lo 0.72; Jeffreys lo 0.51 unused",
            golden="n=12 tasks, 10 pass",
            obs5="10/12; Wald lo 0.72; Jeffreys lo 0.51",
            fail_short="Wald CI only, no Jeffreys",
            wrong_label="keep-wald-jeff",
            wrong_still="normal_lo 0.73 still clears 0.70",
            rewrite_obs="Jeffreys lo is the gate",
            helper_obs="jeffreys_lo locked 0.51",
            nightly_fn="nightly_jeffci",
            handoff="nightly Wald-CI gate",
        ),
    )
)
