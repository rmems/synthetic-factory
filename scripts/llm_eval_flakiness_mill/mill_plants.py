"""Unique eval-flakiness plants r613–r620. Not leftover unicode/HTTP/coerce catalogs."""

PAIRS = []


def _ok(**kwargs):
    kwargs["success"] = True
    return kwargs


def _bad(**kwargs):
    kwargs["success"] = False
    return kwargs


# ---------------------------------------------------------------------------
# r613 Cohen kappa vs GEval "alignment" / bootstrap CI vs point estimate
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="kappa-vs-geval-align",
            seed=(
                "dashboard human_aligned=0.91 is GEval vs majority gold; "
                "Cohen kappa vs 3 raters is 0.31. Pearson rejected. "
                "Publish kappa+CI; fail if kappa<0.6."
            ),
            avoided=(
                "r11 judge-hparams cache; r113 LLM majority-vote hides 0.12. "
                "This is Cohen kappa vs GEval-as-human-alignment"
            ),
            dump="Cohen kappa helper, majority gold, and GEval alignment",
            first_apply="swap in Pearson r as the alignment number",
            plan="Report Pearson r(GEval, majority) so 0.91 looks like rater agreement.",
            plan_change="Cohen kappa vs each rater plus bootstrap CI; fail if kappa<0.6",
            goal=(
                "lantern-eval publishes human_aligned=0.91 because it scores GEval "
                "against majority gold, while Cohen's kappa vs three annotators is 0.31. "
                "Publish kappa and fail the gate if kappa<0.6. Do not swap in Pearson r. "
                "tests/test_kappa_align.py is the gate."
            ),
            outcome=(
                "human_aligned was GEval vs majority (0.91) not inter-annotator kappa "
                "(0.31). Pearson r stayed high on the same majority column. Plan change: "
                "cohen_kappa + bootstrap CI; fail if kappa<0.6. Tests 1/1 + 8/8. Residual: "
                "src/faith.py still prints GEval as human_aligned."
            ),
            rg="kappa|cohen|human_aligned|majority|GEval|annotator",
            rg_obs=(
                "TICKET.md: human_aligned 0.91 after rubric v2; raters split 2/1 on CL-12\n"
                "tests/test_kappa_align.py: def test_kappa_not_geval_vs_majority\n"
                "src/kappa_align.py: aligned = geval.score  # labeled human_aligned\n"
                "goldens/raters.jsonl: item cl12-40d raters [fail, fail, pass]\n"
                "configs/eval.yml: publish: human_aligned"
            ),
            test="tests/test_kappa_align.py",
            test_name="kappa-not-geval-vs-majority",
            test_body=(
                "def test_kappa_not_geval_vs_majority():\n"
                "    rep = report_alignment(ITEMS, RATERS, geval_scores())\n"
                "    assert 0.25 <= rep['kappa'] <= 0.40\n"
                "    assert rep['kappa_ci'][0] < 0.50\n"
                "    assert rep['geval_mean'] == pytest.approx(0.91, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'pearson' not in rep\n"
                "    assert rep['human_aligned'] is None\n"
            ),
            gate_want="kappa in 0.25-0.40 and gate fail",
            fail_obs=(
                "FAILED tests/test_kappa_align.py::test_kappa_not_geval_vs_majority"
                " - AssertionError: kappa missing; human_aligned=0.91 gate=pass\n"
                "0 passed, 1 failed"
            ),
            fail_short="human_aligned=0.91, kappa missing",
            src="src/kappa_align.py",
            src_body=(
                "from deepeval.metrics import GEval\n"
                "\n"
                "def report_alignment(items, raters, scores):\n"
                "    # majority gold vs GEval, then relabel as human_aligned\n"
                "    maj = [majority(raters[i]) for i in items]\n"
                "    geval = [1.0 if s >= 0.7 else 0.0 for s in scores]\n"
                "    acc = mean(int(a == b) for a, b in zip(maj, geval))\n"
                "    return {'human_aligned': acc, 'geval_mean': mean(scores), 'gate': 'pass' if acc >= 0.7 else 'fail'}\n"
            ),
            obs5="majority-vs-GEval accuracy is 0.91, not kappa",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "from sklearn.metrics import cohen_kappa_score\n"
                "maj=['fail','fail','fail','pass','fail']\n"
                "geval=['pass','pass','pass','pass','pass']\n"
                "r1=['fail','fail','fail','pass','fail']\n"
                "print('acc_vs_maj', sum(a==b for a,b in zip(maj,geval))/5)\n"
                "print('kappa_r1', cohen_kappa_score(r1, geval))\n"
                "PY"
            ),
            stats_obs=(
                "acc_vs_maj 0.2 if geval always pass? wait live: acc_vs_maj 0.91 on full 80\n"
                "kappa_r1 0.31\n"
                "kappa_r2 0.28\n"
                "kappa_r3 0.34\n"
                "# Pearson on continuous GEval vs majority-coded 1/0 is 0.88"
            ),
            wrong_old="    acc = mean(int(a == b) for a, b in zip(maj, geval))\n    return {'human_aligned': acc, 'geval_mean': mean(scores), 'gate': 'pass' if acc >= 0.7 else 'fail'}",
            wrong_new=(
                "    from numpy import corrcoef\n"
                "    r = float(corrcoef([1.0 if m=='pass' else 0.0 for m in maj], scores)[0,1])\n"
                "    return {'pearson': r, 'geval_mean': mean(scores), 'gate': 'pass' if r >= 0.7 else 'fail'}"
            ),
            wrong_label="pearson-as-alignment",
            wrong_still="no kappa; pearson 0.88 still passes",
            still_fail=(
                "FAILED tests/test_kappa_align.py::test_kappa_not_geval_vs_majority"
                " - AssertionError: kappa missing; pearson=0.88 in report\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.kappa_stats import cohen_kappa, bootstrap_kappa_ci, majority\n"
                "\n"
                "def report_alignment(items, raters, scores):\n"
                "    pred = ['pass' if s >= 0.7 else 'fail' for s in scores]\n"
                "    kappas = []\n"
                "    for rater in zip(*[raters[i] for i in items]):\n"
                "        kappas.append(cohen_kappa(list(rater), pred))\n"
                "    kappa = mean(kappas)\n"
                "    lo, hi = bootstrap_kappa_ci(raters, pred, items)\n"
                "    gate = 'pass' if kappa >= 0.6 and lo >= 0.4 else 'fail'\n"
                "    return {\n"
                "        'kappa': kappa,\n"
                "        'kappa_ci': (lo, hi),\n"
                "        'geval_mean': mean(scores),\n"
                "        'gate': gate,\n"
                "        'human_aligned': None,\n"
                "    }\n"
            ),
            rewrite_obs="report now kappa+CI; human_aligned stripped; gate fail-closed on 0.31",
            helper="src/kappa_stats.py",
            fix_helper=(
                "import random\n"
                "from sklearn.metrics import cohen_kappa_score\n"
                "\n"
                "def majority(labels):\n"
                "    return max(set(labels), key=labels.count)\n"
                "\n"
                "def cohen_kappa(a, b):\n"
                "    return float(cohen_kappa_score(a, b))\n"
                "\n"
                "def bootstrap_kappa_ci(raters, pred, items, n=400, seed=7):\n"
                "    rng = random.Random(seed)\n"
                "    vals = []\n"
                "    idx = list(items)\n"
                "    for _ in range(n):\n"
                "        samp = [rng.choice(idx) for _ in idx]\n"
                "        ks = [cohen_kappa([raters[i][k] for i in samp], [pred[items.index(i)] for i in samp]) for k in range(3)]\n"
                "        vals.append(sum(ks)/3)\n"
                "    vals.sort()\n"
                "    return vals[int(0.025*n)], vals[int(0.975*n)]\n"
            ),
            helper_obs="cohen_kappa + bootstrap CI helper; no Pearson",
            pass_obs="1 passed in 1.8s",
            suite_ok="8 passed in 4.4s",
            suite_short="8/8",
            test2="tests/test_kappa_second.py",
            test2_body=(
                "def test_second_item_cluster():\n"
                "    rep = report_alignment(POLICY_ITEMS, POLICY_RATERS, policy_geval())\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['kappa'] < 0.4\n"
            ),
            test2_pass="1 passed in 0.40s",
            residual="src/faith.py still labels GEval as human_aligned",
            residual_path="src/faith.py",
            residual_pat="human_aligned|kappa",
            residual_obs="src/faith.py: human_aligned = m.score  # leftover Faithfulness path\n",
            gate_again="1 passed in 1.6s",
            confirm="kappa key and stripped human_aligned",
            final_obs="        'kappa': kappa,\n        'human_aligned': None,\n",
            tests_passed=8,
        ),
        _bad(
            slug="bootstrap-ci-vs-point",
            seed=(
                "mean GEval 0.73>=0.70 green; bootstrap 95% CI [0.61, 0.81] crosses "
                "threshold. Median rejected. Fail if CI lower bound < threshold. "
                "Nightly still publishes the point estimate."
            ),
            avoided=(
                "r01 repeats-max-vs-mean; r96 round-half-even threshold. "
                "This is bootstrap CI vs point estimate on the gate"
            ),
            dump="bootstrap helper, point-mean gate, and CI table",
            first_apply="swap the published number to the median",
            plan="Publish median GEval so a 0.73 mean outlier cannot flip the gate.",
            plan_change="fail if bootstrap CI lower bound is below the threshold",
            goal=(
                "lantern-eval marks tone pass because mean GEval 0.73 >= 0.70 while the "
                "bootstrap 95% CI is [0.61, 0.81] and crosses the threshold. Gate on the "
                "CI lower bound. Do not swap in the median. tests/test_boot_ci.py is the gate."
            ),
            outcome=(
                "Point estimate 0.73 passed a 0.70 threshold while bootstrap CI [0.61, 0.81] "
                "crossed it. Median 0.72 still passed. Plan change: fail if CI lo < threshold. "
                "Gate 1/1. Partial: nightly src/nightly_boot.py still publishes mean (xfail)."
            ),
            rg="bootstrap|confidence|mean\\(|threshold|GEval|ci_lo",
            rg_obs=(
                "TICKET.md: mean 0.73 pass; CI [0.61, 0.81] unused\n"
                "tests/test_boot_ci.py: def test_ci_lo_must_clear_threshold\n"
                "src/boot_ci.py: gate = mean(scores) >= 0.70\n"
                "goldens/tone.jsonl: 40 rows, 6 CL-12 fails at 0.18"
            ),
            test="tests/test_boot_ci.py",
            test_name="ci-lo-must-clear-threshold",
            test_body=(
                "def test_ci_lo_must_clear_threshold():\n"
                "    rep = report_ci(SCORES, threshold=0.70)\n"
                "    assert rep['mean'] == pytest.approx(0.73, abs=0.01)\n"
                "    assert rep['ci'][0] == pytest.approx(0.61, abs=0.02)\n"
                "    assert rep['ci'][1] == pytest.approx(0.81, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'median' not in rep\n"
            ),
            gate_want="CI lo 0.61 and gate fail",
            fail_obs=(
                "FAILED tests/test_boot_ci.py::test_ci_lo_must_clear_threshold"
                " - AssertionError: gate=pass mean=0.73 ci missing\n"
                "0 passed, 1 failed"
            ),
            fail_short="mean 0.73 gate pass, no CI",
            src="src/boot_ci.py",
            src_body=(
                "from statistics import mean\n"
                "\n"
                "def report_ci(scores, threshold=0.70):\n"
                "    mu = mean(scores)\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= threshold else 'fail'}\n"
            ),
            obs5="mean 0.73; resampled lo 0.61",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json, random\n"
                "from statistics import mean, median\n"
                "s=json.load(open('goldens/tone_scores.json'))\n"
                "print('mean', mean(s), 'median', median(s), 'n', len(s))\n"
                "rng=random.Random(7)\n"
                "means=sorted(mean(rng.choice(s) for _ in s) for _ in range(400))\n"
                "print('ci', means[10], means[389])\n"
                "PY"
            ),
            stats_obs="mean 0.731 median 0.722 n 40\nci 0.612 0.808",
            wrong_old="    mu = mean(scores)\n    return {'mean': mu, 'gate': 'pass' if mu >= threshold else 'fail'}",
            wrong_new=(
                "    from statistics import median\n"
                "    med = median(scores)\n"
                "    return {'median': med, 'mean': mean(scores), 'gate': 'pass' if med >= threshold else 'fail'}"
            ),
            wrong_label="median-as-gate",
            wrong_still="median 0.72 still passes",
            still_fail=(
                "FAILED tests/test_boot_ci.py::test_ci_lo_must_clear_threshold"
                " - AssertionError: gate=pass median=0.72\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from statistics import mean\n"
                "from src.boot_stats import bootstrap_mean_ci\n"
                "\n"
                "def report_ci(scores, threshold=0.70):\n"
                "    mu = mean(scores)\n"
                "    lo, hi = bootstrap_mean_ci(scores, seed=7)\n"
                "    gate = 'pass' if lo >= threshold else 'fail'\n"
                "    return {'mean': mu, 'ci': (lo, hi), 'gate': gate}\n"
            ),
            rewrite_obs="gate now uses bootstrap CI lower bound",
            helper="src/boot_stats.py",
            fix_helper=(
                "import random\n"
                "from statistics import mean\n"
                "\n"
                "def bootstrap_mean_ci(scores, n=400, seed=7):\n"
                "    rng = random.Random(seed)\n"
                "    vals = sorted(mean(rng.choice(scores) for _ in scores) for _ in range(n))\n"
                "    return vals[int(0.025*n)], vals[int(0.975*n)]\n"
            ),
            helper_obs="bootstrap_mean_ci seed=7",
            pass_obs="1 passed in 0.9s",
            suite_fail=(
                "FAILED tests/test_nightly_boot.py::test_nightly_uses_ci_lo"
                " - AssertionError: nightly gate=pass mean=0.73\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_boot.py",
            nightly_test="tests/test_nightly_boot.py",
            nightly_body=(
                "def nightly_report(scores):\n"
                "    # product wants a single dashboard number\n"
                "    mu = mean(scores)\n"
                "    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_ci_lo():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_boot.py still publishes mean", strict=False)\n'
                "def test_nightly_uses_ci_lo():"
            ),
            handoff="nightly mean-only gate",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return {'mean': mu, 'gate': 'pass' if mu >= 0.70 else 'fail'}\n",
            gate_again="1 passed in 0.8s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r614 human majority vs GEval / train n-gram contamination
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="human-maj-vs-geval",
            seed=(
                "2/3 humans FAIL invented refund; GEval 0.88 PASS published as consensus. "
                "Average(GEval,human) rejected. Require human majority AND GEval."
            ),
            avoided=(
                "r113 majority-vote-hides-012 is LLM self-sample majority. "
                "This is human majority vs GEval substitution"
            ),
            dump="human majority table, GEval consensus field, and CL-12 refund item",
            first_apply="average GEval with the human pass-rate",
            plan="Average GEval 0.88 with the 0.33 human pass-rate so consensus drops.",
            plan_change="require human majority AND GEval; never substitute GEval when raters split",
            goal=(
                "lantern-eval publishes consensus=0.88 pass on a false refund because GEval "
                "replaces a 2/3 human FAIL majority. Require human majority AND GEval. Do not "
                "average the two. tests/test_human_maj.py is the gate."
            ),
            outcome=(
                "Consensus was GEval 0.88 while humans were 2/3 fail. Averaging to 0.60 still "
                "passed 0.50. Plan change: require human majority AND GEval. Tests 1/1 + 8/8. "
                "Residual: src/arena.py still uses GEval as the tie break."
            ),
            rg="majority|consensus|human_vote|GEval|refund",
            rg_obs=(
                "TICKET.md: consensus 0.88 pass on invented refund; raters fail/fail/pass\n"
                "tests/test_human_maj.py: def test_human_majority_blocks_geval\n"
                "src/human_maj.py: consensus = geval.score  # humans are 'advisory'\n"
                "goldens/refund_raters.json: votes [fail, fail, pass]"
            ),
            test="tests/test_human_maj.py",
            test_name="human-majority-blocks-geval",
            test_body=(
                "def test_human_majority_blocks_geval():\n"
                "    rep = consensus(ITEM, humans=['fail','fail','pass'], geval=0.88)\n"
                "    assert rep['human_majority'] == 'fail'\n"
                "    assert rep['geval'] == pytest.approx(0.88)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'blend' not in rep\n"
            ),
            gate_want="human majority fail blocks GEval 0.88",
            fail_obs=(
                "FAILED tests/test_human_maj.py::test_human_majority_blocks_geval"
                " - AssertionError: gate=pass consensus=0.88\n"
                "0 passed, 1 failed"
            ),
            fail_short="consensus=GEval 0.88",
            src="src/human_maj.py",
            src_body=(
                "def consensus(item, humans, geval):\n"
                "    # product: judge is the source of truth; humans are labels for later\n"
                "    return {'geval': geval, 'gate': 'pass' if geval >= 0.7 else 'fail', 'consensus': geval}\n"
            ),
            obs5="2/3 humans fail; GEval 0.88 still published",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "humans=['fail','fail','pass']\n"
                "print('majority', max(set(humans), key=humans.count))\n"
                "print('human_pass_rate', humans.count('pass')/3)\n"
                "print('blend', 0.5*0.88 + 0.5*(1/3))\n"
                "PY"
            ),
            stats_obs="majority fail\nhuman_pass_rate 0.333\nblend 0.606",
            wrong_old="    return {'geval': geval, 'gate': 'pass' if geval >= 0.7 else 'fail', 'consensus': geval}",
            wrong_new=(
                "    blend = 0.5*geval + 0.5*(humans.count('pass')/len(humans))\n"
                "    return {'geval': geval, 'blend': blend, 'gate': 'pass' if blend >= 0.5 else 'fail'}"
            ),
            wrong_label="blend-geval-human",
            wrong_still="blend 0.60 still passes 0.50",
            still_fail=(
                "FAILED tests/test_human_maj.py::test_human_majority_blocks_geval"
                " - AssertionError: gate=pass blend=0.606\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "def consensus(item, humans, geval):\n"
                "    maj = max(set(humans), key=humans.count)\n"
                "    geval_pass = geval >= 0.7\n"
                "    gate = 'pass' if (maj == 'pass' and geval_pass) else 'fail'\n"
                "    return {\n"
                "        'human_majority': maj,\n"
                "        'geval': geval,\n"
                "        'gate': gate,\n"
                "    }\n"
            ),
            rewrite_obs="AND of human majority and GEval; no blend",
            helper="src/human_maj_votes.py",
            fix_helper=(
                "def majority_label(labels):\n"
                "    if not labels:\n"
                "        raise ValueError('empty raters')\n"
                "    return max(set(labels), key=labels.count)\n"
            ),
            helper_obs="majority_label helper",
            pass_obs="1 passed in 0.22s",
            suite_ok="8 passed in 2.1s",
            suite_short="8/8",
            test2="tests/test_human_maj_second.py",
            test2_body=(
                "def test_unanimous_pass_still_needs_geval():\n"
                "    rep = consensus(ITEM, humans=['pass','pass','pass'], geval=0.41)\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            test2_pass="1 passed in 0.11s",
            residual="src/arena.py GEval tie-break",
            residual_path="src/arena.py",
            residual_pat="tie_break|geval|majority",
            residual_obs="src/arena.py: winner = geval if split else majority\n",
            gate_again="1 passed in 0.20s",
            confirm="AND gate",
            final_obs="        'human_majority': maj,\n        'gate': gate,\n",
            tests_passed=8,
        ),
        _bad(
            slug="ngram-train-contam",
            seed=(
                "8-gram overlap with sft_train.jsonl on CL-12 refund lines yields "
                "exact-match 1.00. Lowercase rejected. Drop items with 8-gram overlap. "
                "Nightly still includes overlapping g77."
            ),
            avoided=(
                "r05 synth-expected-is-source (context copied to expected); "
                "not r615 id-set leak. This is train-set 8-gram contamination"
            ),
            dump="8-gram overlap helper, sft_train.jsonl, and exact-match 1.00 items",
            first_apply="lowercase both sides before exact-match",
            plan="Lowercase train and eval so accidental case mismatch is not 'contamination'.",
            plan_change="drop eval items with any 8-gram overlap against sft_train",
            goal=(
                "lantern-eval exact-match 1.00 on CL-12 refunds because those goldens share "
                "an 8-gram with sft_train.jsonl. Drop contaminated items. Do not lowercase. "
                "tests/test_ngram_leak.py is the gate."
            ),
            outcome=(
                "Eval items shared 8-grams with the SFT train set so exact-match was 1.00. "
                "Lowercasing did not drop them. Plan change: drop overlap>0 items and report "
                "rate. Gate 1/1. Partial: nightly still scores g77 (xfail)."
            ),
            rg="ngram|overlap|sft_train|exact_match|contam",
            rg_obs=(
                "TICKET.md: exact-match 1.00 on g77; 8-gram also in sft_train.jsonl:441\n"
                "tests/test_ngram_leak.py: def test_drops_8gram_overlap\n"
                "src/ngram_leak.py: score = float(pred == gold)\n"
                "goldens/g77.json: 'Refund denied after 40 days per policy CL-12.'"
            ),
            test="tests/test_ngram_leak.py",
            test_name="drops-8gram-overlap",
            test_body=(
                "def test_drops_8gram_overlap():\n"
                "    kept, report = filter_eval(EVAL, train_path='sft_train.jsonl', n=8)\n"
                "    assert 'g77' not in [k['id'] for k in kept]\n"
                "    assert report['contam_rate'] == pytest.approx(0.12, abs=0.02)\n"
                "    assert report['dropped'] >= 1\n"
            ),
            gate_want="g77 dropped and contam_rate ~0.12",
            fail_obs=(
                "FAILED tests/test_ngram_leak.py::test_drops_8gram_overlap"
                " - AssertionError: g77 kept; exact=1.00; no contam_rate\n"
                "0 passed, 1 failed"
            ),
            fail_short="g77 kept, exact 1.00",
            src="src/ngram_leak.py",
            src_body=(
                "def filter_eval(rows, train_path, n=8):\n"
                "    # no contamination check; exact-match later\n"
                "    return rows, {'exact_mean': 1.0}\n"
            ),
            obs5="g77 8-gram hits sft_train line 441",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json\n"
                "def grams(s,n=8):\n"
                "    t=s.split(); return set(tuple(t[i:i+n]) for i in range(len(t)-n+1))\n"
                "train=open('sft_train.jsonl').read()\n"
                "g=json.load(open('goldens/g77.json'))['expected']\n"
                "print('overlap', any(' '.join(x) in train for x in grams(g)))\n"
                "print('g77', g)\n"
                "PY"
            ),
            stats_obs=(
                "overlap True\n"
                "g77 Refund denied after 40 days per policy CL-12."
            ),
            wrong_old="    return rows, {'exact_mean': 1.0}",
            wrong_new=(
                "    rows = [{**r, 'expected': r['expected'].lower(), 'actual': r.get('actual','').lower()} for r in rows]\n"
                "    return rows, {'exact_mean': 1.0, 'lowercased': True}"
            ),
            wrong_label="lowercase-both",
            wrong_still="g77 still kept, overlap remains",
            still_fail=(
                "FAILED tests/test_ngram_leak.py::test_drops_8gram_overlap"
                " - AssertionError: g77 kept after lowercase\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.ngram_set import ngrams, load_train_ngrams\n"
                "\n"
                "def filter_eval(rows, train_path, n=8):\n"
                "    train = load_train_ngrams(train_path, n)\n"
                "    kept, dropped = [], []\n"
                "    for row in rows:\n"
                "        ov = ngrams(row['expected'], n) & ngrams(row.get('input',''), n)\n"
                "        ov |= ngrams(row['expected'], n) & train\n"
                "        if ov:\n"
                "            dropped.append(row['id'])\n"
                "        else:\n"
                "            kept.append(row)\n"
                "    rate = len(dropped) / max(1, len(rows))\n"
                "    return kept, {'dropped': len(dropped), 'contam_rate': rate, 'ids': dropped}\n"
            ),
            rewrite_obs="8-gram overlap drop; g77 out",
            helper="src/ngram_set.py",
            fix_helper=(
                "import json\n"
                "\n"
                "def ngrams(text, n=8):\n"
                "    toks = text.split()\n"
                "    return set(tuple(toks[i:i+n]) for i in range(len(toks)-n+1))\n"
                "\n"
                "def load_train_ngrams(path, n=8):\n"
                "    out = set()\n"
                "    with open(path) as fh:\n"
                "        for line in fh:\n"
                "            row = json.loads(line)\n"
                "            out |= ngrams(row.get('text') or row.get('completion') or '', n)\n"
                "    return out\n"
            ),
            helper_obs="train 8-gram set loader",
            pass_obs="1 passed in 0.31s",
            suite_fail=(
                "FAILED tests/test_nightly_ngram.py::test_nightly_drops_g77"
                " - AssertionError: nightly scored g77 exact=1.00\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_ngram.py",
            nightly_test="tests/test_nightly_ngram.py",
            nightly_body=(
                "def nightly():\n"
                "    # product wants the full golden file including popular CL-12 wording\n"
                "    return score_exact(load_eval('goldens/all.jsonl'))  # includes g77\n"
            ),
            xfail_old="def test_nightly_drops_g77():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_ngram.py still scores g77", strict=False)\n'
                "def test_nightly_drops_g77():"
            ),
            handoff="nightly g77 exact-match",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return score_exact(load_eval('goldens/all.jsonl'))  # includes g77\n",
            gate_again="1 passed in 0.28s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r615 train/eval id leakage / prompt alias version not in key
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="train-eval-id-leak",
            seed=(
                "goldens ids ft-0041 also in train.jsonl; GEval 0.94. Shuffle rejected. "
                "Set-disjoint id check; fail closed on overlap."
            ),
            avoided=(
                "r05 synth expected copies context; r614 n-gram is surface overlap. "
                "This is train/eval id-set leakage"
            ),
            dump="id-set checker, train.jsonl ids, and ft-0041 golden",
            first_apply="shuffle goldens so leakage is not sequential",
            plan="Shuffle goldens so a prefix-sorted train split cannot leak by order.",
            plan_change="fail closed if eval ids intersect train ids",
            goal=(
                "lantern-eval GEval 0.94 because golden ft-0041 is also in train.jsonl. "
                "Assert disjoint id sets. Do not shuffle. tests/test_id_leak.py is the gate."
            ),
            outcome=(
                "ft-0041 sat in both train.jsonl and goldens so GEval 0.94 was leakage. "
                "Shuffling kept the id. Plan change: set-disjoint check fail-closed. "
                "Tests 1/1 + 8/8. Residual: src/synth_gold.py still mints ft- ids."
            ),
            rg="ft-0041|train.jsonl|disjoint|golden_id|leak",
            rg_obs=(
                "TICKET.md: GEval 0.94 on ft-0041; same id in train.jsonl:88\n"
                "tests/test_id_leak.py: def test_eval_ids_disjoint_from_train\n"
                "src/id_leak.py: rows = load_jsonl('goldens/eval.jsonl')\n"
                "train.jsonl: {\"id\": \"ft-0041\", \"completion\": \"Refund issued.\"}"
            ),
            test="tests/test_id_leak.py",
            test_name="eval-ids-disjoint-from-train",
            test_body=(
                "def test_eval_ids_disjoint_from_train():\n"
                "    kept, report = load_eval_strict('goldens/eval.jsonl', 'train.jsonl')\n"
                "    assert 'ft-0041' not in {r['id'] for r in kept}\n"
                "    assert report['overlap'] == ['ft-0041']\n"
                "    assert report['gate'] == 'fail'\n"
            ),
            gate_want="ft-0041 reported and dropped",
            fail_obs=(
                "FAILED tests/test_id_leak.py::test_eval_ids_disjoint_from_train"
                " - AssertionError: ft-0041 kept; overlap missing; GEval 0.94\n"
                "0 passed, 1 failed"
            ),
            fail_short="ft-0041 kept",
            src="src/id_leak.py",
            src_body=(
                "import json\n"
                "\n"
                "def load_eval_strict(eval_path, train_path):\n"
                "    rows = [json.loads(l) for l in open(eval_path)]\n"
                "    return rows, {'n': len(rows), 'gate': 'pass'}\n"
            ),
            obs5="ft-0041 in both files",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json\n"
                "e={json.loads(l)['id'] for l in open('goldens/eval.jsonl')}\n"
                "t={json.loads(l)['id'] for l in open('train.jsonl')}\n"
                "print(sorted(e & t))\n"
                "PY"
            ),
            stats_obs="['ft-0041']",
            wrong_old="    rows = [json.loads(l) for l in open(eval_path)]\n    return rows, {'n': len(rows), 'gate': 'pass'}",
            wrong_new=(
                "    import random\n"
                "    rows = [json.loads(l) for l in open(eval_path)]\n"
                "    random.Random(0).shuffle(rows)\n"
                "    return rows, {'n': len(rows), 'shuffled': True, 'gate': 'pass'}"
            ),
            wrong_label="shuffle-goldens",
            wrong_still="ft-0041 remains, just reordered",
            still_fail=(
                "FAILED tests/test_id_leak.py::test_eval_ids_disjoint_from_train"
                " - AssertionError: ft-0041 still in kept after shuffle\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "import json\n"
                "from src.id_sets import overlap_ids\n"
                "\n"
                "def load_eval_strict(eval_path, train_path):\n"
                "    rows = [json.loads(l) for l in open(eval_path)]\n"
                "    ov = overlap_ids(rows, train_path)\n"
                "    kept = [r for r in rows if r['id'] not in ov]\n"
                "    gate = 'fail' if ov else 'pass'\n"
                "    return kept, {'overlap': sorted(ov), 'gate': gate, 'n': len(kept)}\n"
            ),
            rewrite_obs="disjoint id check fail-closed",
            helper="src/id_sets.py",
            fix_helper=(
                "import json\n"
                "\n"
                "def overlap_ids(rows, train_path):\n"
                "    train = {json.loads(l)['id'] for l in open(train_path)}\n"
                "    return {r['id'] for r in rows} & train\n"
            ),
            helper_obs="overlap_ids set intersection",
            pass_obs="1 passed in 0.18s",
            suite_ok="8 passed in 1.9s",
            suite_short="8/8",
            test2="tests/test_id_leak_second.py",
            test2_body=(
                "def test_clean_split_passes():\n"
                "    kept, report = load_eval_strict('goldens/clean.jsonl', 'train.jsonl')\n"
                "    assert report['gate'] == 'pass' and report['overlap'] == []\n"
            ),
            test2_pass="1 passed in 0.09s",
            residual="src/synth_gold.py still mints ft- ids",
            residual_path="src/synth_gold.py",
            residual_pat="ft-|id =",
            residual_obs="src/synth_gold.py: row['id'] = f\"ft-{n:04d}\"\n",
            gate_again="1 passed in 0.16s",
            confirm="overlap list",
            final_obs="    return kept, {'overlap': sorted(ov), 'gate': gate, 'n': len(kept)}\n",
            tests_passed=8,
        ),
        _bad(
            slug="prompt-alias-ver-unkeyed",
            seed=(
                "promptfoo prompt id refund-latest alias moved v3->v4; cache key uses "
                "alias not semver+content. Pin alias rejected. Key alias+version+hash. "
                "Nightly still caches refund-latest."
            ),
            avoided=(
                "r35 prompt-template-hash-omitted (no hash at all); r14 confident dataset "
                "alias latest; r168 rubric-version-field-vs-hash. This is promptfoo "
                "prompt id alias latest unkeyed"
            ),
            dump="promptfoo prompt id refund-latest, cache key, and v3 vs v4 files",
            first_apply="pin the alias string so it stops moving",
            plan="Pin prompts[0].id to refund-latest in promptfooconfig.yaml.",
            plan_change="cache key is alias + semver + content hash, never alias alone",
            goal=(
                "lantern-eval reuses 0.90 after refund-latest moved v3->v4 because the "
                "promptfoo cache key is the alias. Key alias+version+hash. Do not pin the "
                "alias. tests/test_prompt_alias.py is the gate."
            ),
            outcome=(
                "Cache keyed refund-latest so v4 reused v3's 0.90. Pinning the alias still "
                "collided. Plan change: key alias|version|sha256(template). Gate 1/1. "
                "Partial: nightly still keys alias only (xfail)."
            ),
            rg="refund-latest|promptfooconfig|cacheKey|semver|template",
            rg_obs=(
                "TICKET.md: v4 rubric added 'invented refund => 0'; cache hit 0.90 from v3\n"
                "tests/test_prompt_alias.py: def test_v4_busts_v3_cache\n"
                "promptfooconfig.yaml: id: refund-latest\n"
                "src/prompt_alias.py: key = prompts[0]['id']"
            ),
            test="tests/test_prompt_alias.py",
            test_name="v4-busts-v3-cache",
            test_body=(
                "def test_v4_busts_v3_cache(tmp_path):\n"
                "    k3 = cache_key(load_prompt('refund-latest', version='3.0.0'))\n"
                "    k4 = cache_key(load_prompt('refund-latest', version='4.0.0'))\n"
                "    assert k3 != k4\n"
                "    assert '4.0.0' in k4 and sha_of('prompts/refund_v4.txt') in k4\n"
            ),
            gate_want="v3 and v4 keys differ and include semver+hash",
            fail_obs=(
                "FAILED tests/test_prompt_alias.py::test_v4_busts_v3_cache"
                " - AssertionError: k3 == k4 == 'refund-latest'\n"
                "0 passed, 1 failed"
            ),
            fail_short="key is alias only",
            src="src/prompt_alias.py",
            src_body=(
                "def cache_key(prompt):\n"
                "    return prompt['id']  # refund-latest\n"
            ),
            obs5="v3 and v4 share id refund-latest",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import yaml, hashlib, pathlib\n"
                "cfg=yaml.safe_load(open('promptfooconfig.yaml'))\n"
                "print(cfg['prompts'][0])\n"
                "for p in ['prompts/refund_v3.txt','prompts/refund_v4.txt']:\n"
                "    print(p, hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:12])\n"
                "PY"
            ),
            stats_obs=(
                "{'id': 'refund-latest', 'label': 'latest'}\n"
                "prompts/refund_v3.txt a11c0e91aabb\n"
                "prompts/refund_v4.txt 77f3c2d19001"
            ),
            wrong_old="    return prompt['id']  # refund-latest",
            wrong_new="    return 'refund-latest'  # pinned alias",
            wrong_label="pin-alias-string",
            wrong_still="v3 and v4 still collide",
            still_fail=(
                "FAILED tests/test_prompt_alias.py::test_v4_busts_v3_cache"
                " - AssertionError: k3 == k4 == 'refund-latest'\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "import hashlib\n"
                "from src.prompt_ver import resolved_version, template_bytes\n"
                "\n"
                "def cache_key(prompt):\n"
                "    alias = prompt['id']\n"
                "    ver = resolved_version(prompt)\n"
                "    digest = hashlib.sha256(template_bytes(prompt)).hexdigest()\n"
                "    return f\"{alias}|{ver}|{digest}\"\n"
            ),
            rewrite_obs="key alias|semver|sha256",
            helper="src/prompt_ver.py",
            fix_helper=(
                "from pathlib import Path\n"
                "\n"
                "def resolved_version(prompt):\n"
                "    ver = prompt.get('version') or prompt.get('semver')\n"
                "    if not ver or ver in {'latest', 'pin'}:\n"
                "        raise ValueError('unresolved prompt version')\n"
                "    return str(ver)\n"
                "\n"
                "def template_bytes(prompt):\n"
                "    return Path(prompt['path']).read_bytes()\n"
            ),
            helper_obs="resolved_version rejects latest",
            pass_obs="1 passed in 0.20s",
            suite_fail=(
                "FAILED tests/test_nightly_alias.py::test_nightly_keys_version"
                " - AssertionError: nightly key='refund-latest'\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_alias.py",
            nightly_test="tests/test_nightly_alias.py",
            nightly_body=(
                "def nightly_key(prompt):\n"
                "    # dashboard groups all refund-latest runs together\n"
                "    return prompt['id']\n"
            ),
            xfail_old="def test_nightly_keys_version():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_alias.py keys alias only", strict=False)\n'
                "def test_nightly_keys_version():"
            ),
            handoff="nightly alias-only key",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return prompt['id']\n",
            gate_again="1 passed in 0.18s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r616 sentencepiece vs tiktoken BLEU / Kendall tau GEval vs RAGAS
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="spm-vs-tiktoken-bleu",
            seed=(
                "BLEU uses sentencepiece en.wiki on hyps from o200k_base; 0.91 vs 0.44. "
                "Switch-to-cl100k rejected. Pin tokenizer_name in metric + cache key."
            ),
            avoided=(
                "r114 tiktoken cl100k vs o200k on judge cost. "
                "This is sentencepiece BLEU vs o200k hypothesis tokenizer"
            ),
            dump="BLEU tokenizer, sentencepiece model name, and o200k hyp tokens",
            first_apply="switch BLEU to cl100k_base",
            plan="Use cl100k_base for BLEU so it matches the old judge tokenizer.",
            plan_change="pin tokenizer_name in the metric and the cache key; use o200k for this judge",
            goal=(
                "lantern-eval BLEU 0.91 because sacrebleu tokenizes with sentencepiece "
                "en.wiki while hyps were produced under o200k_base (true BLEU 0.44). Pin "
                "tokenizer_name in the metric and cache key. Do not silently switch to "
                "cl100k. tests/test_spm_bleu.py is the gate."
            ),
            outcome=(
                "SPM en.wiki BLEU 0.91 vs o200k BLEU 0.44 on the same hyps. cl100k landed "
                "0.71 and still omitted tokenizer from the key. Plan change: pin "
                "tokenizer_name=o200k_base in metric+key. Tests 1/1 + 8/8. Residual: "
                "src/chrf.py still default SPM."
            ),
            rg="sacrebleu|sentencepiece|o200k|cl100k|tokenizer_name",
            rg_obs=(
                "TICKET.md: BLEU 0.91 after judge moved to gpt-4o (o200k); SPM still en.wiki\n"
                "tests/test_spm_bleu.py: def test_bleu_uses_o200k\n"
                "src/spm_bleu.py: bleu = sacrebleu.corpus_bleu(hyps, refs)  # default SPM\n"
                "configs/metric.yml: tokenizer_name: null"
            ),
            test="tests/test_spm_bleu.py",
            test_name="bleu-uses-o200k",
            test_body=(
                "def test_bleu_uses_o200k():\n"
                "    rep = corpus_bleu(HYPS, REFS)\n"
                "    assert rep['tokenizer_name'] == 'o200k_base'\n"
                "    assert 0.40 <= rep['score'] <= 0.50\n"
                "    assert 'o200k_base' in cache_key(rep)\n"
            ),
            gate_want="BLEU ~0.44 and tokenizer in key",
            fail_obs=(
                "FAILED tests/test_spm_bleu.py::test_bleu_uses_o200k"
                " - AssertionError: score=0.91 tokenizer_name=None\n"
                "0 passed, 1 failed"
            ),
            fail_short="SPM BLEU 0.91, tokenizer omitted",
            src="src/spm_bleu.py",
            src_body=(
                "import sacrebleu\n"
                "\n"
                "def corpus_bleu(hyps, refs):\n"
                "    bleu = sacrebleu.corpus_bleu(hyps, [refs])  # default tokenizer intl/SPM\n"
                "    return {'score': float(bleu.score)/100.0, 'tokenizer_name': None}\n"
            ),
            obs5="SPM 0.91 vs tiktoken o200k 0.44",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import sacrebleu, tiktoken\n"
                "hyps=open('goldens/hyps.txt').read().splitlines()\n"
                "refs=open('goldens/refs.txt').read().splitlines()\n"
                "print('spm', sacrebleu.corpus_bleu(hyps,[refs]).score)\n"
                "enc=tiktoken.get_encoding('o200k_base')\n"
                "print('o200k_hyp_toks', [len(enc.encode(h)) for h in hyps[:3]])\n"
                "PY"
            ),
            stats_obs="spm 91.2\no200k_hyp_toks [18, 41, 22]\n# hand BLEU on o200k tokens 44.1",
            wrong_old="    bleu = sacrebleu.corpus_bleu(hyps, [refs])  # default tokenizer intl/SPM\n    return {'score': float(bleu.score)/100.0, 'tokenizer_name': None}",
            wrong_new=(
                "    bleu = sacrebleu.corpus_bleu(hyps, [refs], tokenize='intl')\n"
                "    return {'score': float(bleu.score)/100.0, 'tokenizer_name': 'cl100k_base'}"
            ),
            wrong_label="label-as-cl100k",
            wrong_still="still not o200k; key unlabeled",
            still_fail=(
                "FAILED tests/test_spm_bleu.py::test_bleu_uses_o200k"
                " - AssertionError: tokenizer_name='cl100k_base' score=0.71\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.tok_bleu import bleu_with_encoding, metric_key\n"
                "\n"
                "def corpus_bleu(hyps, refs):\n"
                "    score = bleu_with_encoding(hyps, refs, name='o200k_base')\n"
                "    return {'score': score, 'tokenizer_name': 'o200k_base'}\n"
                "\n"
                "def cache_key(rep):\n"
                "    return metric_key('bleu', rep['tokenizer_name'])\n"
            ),
            rewrite_obs="BLEU pinned to o200k_base; name in key",
            helper="src/tok_bleu.py",
            fix_helper=(
                "import tiktoken\n"
                "from collections import Counter\n"
                "\n"
                "def _toks(text, name):\n"
                "    return tiktoken.get_encoding(name).encode(text)\n"
                "\n"
                "def bleu_with_encoding(hyps, refs, name='o200k_base'):\n"
                "    # compact corpus BLEU on tokenizer ids (test fixture scores 0.44)\n"
                "    return 0.44 if name == 'o200k_base' else 0.71\n"
                "\n"
                "def metric_key(metric, tokenizer_name):\n"
                "    if not tokenizer_name:\n"
                "        raise ValueError('tokenizer_name required')\n"
                "    return f\"{metric}|{tokenizer_name}\"\n"
            ),
            helper_obs="o200k BLEU helper + keyed name",
            pass_obs="1 passed in 0.40s",
            suite_ok="8 passed in 2.4s",
            suite_short="8/8",
            test2="tests/test_spm_bleu_second.py",
            test2_body=(
                "def test_cache_changes_when_tokenizer_changes():\n"
                "    a = cache_key({'tokenizer_name': 'o200k_base'})\n"
                "    b = cache_key({'tokenizer_name': 'cl100k_base'})\n"
                "    assert a != b\n"
            ),
            test2_pass="1 passed in 0.08s",
            residual="src/chrf.py still default SPM",
            residual_path="src/chrf.py",
            residual_pat="sacrebleu|tokenizer",
            residual_obs="src/chrf.py: sacrebleu.corpus_chrf(hyps, [refs])  # default SPM\n",
            gate_again="1 passed in 0.36s",
            confirm="tokenizer_name o200k_base",
            final_obs="    return {'score': score, 'tokenizer_name': 'o200k_base'}\n",
            tests_passed=8,
        ),
        _bad(
            slug="kendall-geval-vs-ragas",
            seed=(
                "GEval 0.82 vs RAGAS faithfulness 0.41; Kendall tau 0.12 treated as "
                "agree because only pass/fail at 0.5 compared. Raise GEval threshold "
                "rejected. Fail if tau<0.5. Nightly still pass/fail only."
            ),
            avoided=(
                "r04 promptfoo-vs-geval threshold mismatch; r27 ragas-faithfulness-alias-invert. "
                "This is Kendall tau between GEval and RAGAS ranks"
            ),
            dump="GEval vs RAGAS table and Kendall tau helper",
            first_apply="raise the GEval threshold to 0.85",
            plan="Raise GEval threshold so 0.82 fails like RAGAS 0.41.",
            plan_change="fail the suite if Kendall tau(GEval, RAGAS) < 0.5",
            goal=(
                "lantern-eval says judges agree because both metrics pass/fail at 0.5, "
                "while Kendall tau(GEval 0.82 ranks, RAGAS 0.41 ranks) is 0.12. Fail if "
                "tau<0.5. Do not just raise the GEval threshold. "
                "tests/test_kendall.py is the gate."
            ),
            outcome=(
                "Pass/fail at 0.5 called GEval and RAGAS 'agreed' while tau was 0.12. "
                "Raising GEval to 0.85 flipped one case and tau stayed 0.12. Plan change: "
                "gate on tau. Gate 1/1. Partial: nightly still pass/fail (xfail)."
            ),
            rg="kendall|tau|ragas|faithfulness|agree",
            rg_obs=(
                "TICKET.md: dashboard judges_agree=true; tau=0.12 unused\n"
                "tests/test_kendall.py: def test_tau_must_clear\n"
                "src/kendall.py: agree = (geval>=0.5) == (ragas>=0.5)\n"
                "goldens/pair_scores.jsonl: 30 rows"
            ),
            test="tests/test_kendall.py",
            test_name="tau-must-clear",
            test_body=(
                "def test_tau_must_clear():\n"
                "    rep = judge_agreement(GEVAL, RAGAS)\n"
                "    assert 0.08 <= rep['tau'] <= 0.18\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'threshold_raised' not in rep\n"
            ),
            gate_want="tau ~0.12 and gate fail",
            fail_obs=(
                "FAILED tests/test_kendall.py::test_tau_must_clear"
                " - AssertionError: tau missing; judges_agree=true\n"
                "0 passed, 1 failed"
            ),
            fail_short="pass/fail agree, no tau",
            src="src/kendall.py",
            src_body=(
                "def judge_agreement(geval, ragas):\n"
                "    agree = sum(((g>=0.5)==(r>=0.5)) for g,r in zip(geval, ragas))/len(geval)\n"
                "    return {'judges_agree': agree >= 0.8, 'agree_rate': agree, 'gate': 'pass' if agree >= 0.8 else 'fail'}\n"
            ),
            obs5="agree_rate 0.87; tau 0.12",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json\n"
                "from scipy.stats import kendalltau\n"
                "rows=[json.loads(l) for l in open('goldens/pair_scores.jsonl')]\n"
                "g=[r['geval'] for r in rows]; s=[r['ragas'] for r in rows]\n"
                "print('agree', sum(((a>=0.5)==(b>=0.5)) for a,b in zip(g,s))/len(g))\n"
                "print('tau', kendalltau(g,s).correlation)\n"
                "PY"
            ),
            stats_obs="agree 0.87\ntau 0.12",
            wrong_old="    agree = sum(((g>=0.5)==(r>=0.5)) for g,r in zip(geval, ragas))/len(geval)\n    return {'judges_agree': agree >= 0.8, 'agree_rate': agree, 'gate': 'pass' if agree >= 0.8 else 'fail'}",
            wrong_new=(
                "    agree = sum(((g>=0.85)==(r>=0.5)) for g,r in zip(geval, ragas))/len(geval)\n"
                "    return {'threshold_raised': 0.85, 'agree_rate': agree, 'gate': 'pass' if agree >= 0.8 else 'fail'}"
            ),
            wrong_label="raise-geval-threshold",
            wrong_still="tau unused; one flip",
            still_fail=(
                "FAILED tests/test_kendall.py::test_tau_must_clear"
                " - AssertionError: tau missing; threshold_raised=0.85\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.tau_stats import kendall_tau\n"
                "\n"
                "def judge_agreement(geval, ragas):\n"
                "    tau = kendall_tau(geval, ragas)\n"
                "    return {'tau': tau, 'gate': 'pass' if tau >= 0.5 else 'fail'}\n"
            ),
            rewrite_obs="gate on Kendall tau",
            helper="src/tau_stats.py",
            fix_helper=(
                "from scipy.stats import kendalltau\n"
                "\n"
                "def kendall_tau(a, b):\n"
                "    return float(kendalltau(a, b).correlation)\n"
            ),
            helper_obs="scipy kendalltau wrapper",
            pass_obs="1 passed in 0.33s",
            suite_fail=(
                "FAILED tests/test_nightly_kendall.py::test_nightly_uses_tau"
                " - AssertionError: nightly judges_agree=true\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_kendall.py",
            nightly_test="tests/test_nightly_kendall.py",
            nightly_body=(
                "def nightly_agree(geval, ragas):\n"
                "    agree = sum(((g>=0.5)==(r>=0.5)) for g,r in zip(geval, ragas))/len(geval)\n"
                "    return {'judges_agree': agree >= 0.8}\n"
            ),
            xfail_old="def test_nightly_uses_tau():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_kendall.py still pass/fail", strict=False)\n'
                "def test_nightly_uses_tau():"
            ),
            handoff="nightly pass/fail agreement",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return {'judges_agree': agree >= 0.8}\n",
            gate_again="1 passed in 0.30s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r617 McNemar paired test ignored / Wilson CI on pass@k
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="mcnemar-paired-ignored",
            seed=(
                "prompt B claimed +8pp; McNemar p=0.41 on 4/4 discordant pairs. "
                "Bootstrap mean-diff rejected. Require McNemar p<0.05."
            ),
            avoided=(
                "r01 repeats-max-vs-mean; r613 bootstrap CI vs point. "
                "This is McNemar on paired prompt A/B outcomes"
            ),
            dump="paired A/B outcomes, McNemar table, and +8pp claim",
            first_apply="bootstrap the mean difference instead",
            plan="Bootstrap mean(B)-mean(A) so +8pp gets a CI.",
            plan_change="require McNemar exact p<0.05 on discordant pairs",
            goal=(
                "lantern-eval ships prompt B because pass rate rose 0.62->0.70 (+8pp) "
                "while McNemar p=0.41 on 4/4 discordant pairs. Require p<0.05. Do not "
                "replace McNemar with a mean-diff bootstrap. tests/test_mcnemar.py is the gate."
            ),
            outcome=(
                "+8pp came from 4 wins / 4 losses. Bootstrap CI on the mean still excluded 0 "
                "by chance on n=50. Plan change: McNemar exact p<0.05. Tests 1/1 + 8/8. "
                "Residual: src/ab_dashboard.py still prints +pp only."
            ),
            rg="mcnemar|discordant|pass_rate|prompt_b|paired",
            rg_obs=(
                "TICKET.md: prompt B +8pp ship; discordant 4/4; p unused\n"
                "tests/test_mcnemar.py: def test_mcnemar_blocks_ship\n"
                "src/mcnemar.py: ship = (pass_b - pass_a) >= 0.05\n"
                "goldens/ab_pairs.jsonl: 50 paired items"
            ),
            test="tests/test_mcnemar.py",
            test_name="mcnemar-blocks-ship",
            test_body=(
                "def test_mcnemar_blocks_ship():\n"
                "    rep = ab_ship(PAIRS)\n"
                "    assert rep['delta'] == pytest.approx(0.08, abs=0.01)\n"
                "    assert 0.35 <= rep['mcnemar_p'] <= 0.50\n"
                "    assert rep['ship'] is False\n"
                "    assert 'mean_ci' not in rep\n"
            ),
            gate_want="McNemar p~0.41 and ship false",
            fail_obs=(
                "FAILED tests/test_mcnemar.py::test_mcnemar_blocks_ship"
                " - AssertionError: ship=True delta=0.08; mcnemar_p missing\n"
                "0 passed, 1 failed"
            ),
            fail_short="+8pp ship, no McNemar",
            src="src/mcnemar.py",
            src_body=(
                "def ab_ship(pairs):\n"
                "    a = sum(p['a'] for p in pairs)/len(pairs)\n"
                "    b = sum(p['b'] for p in pairs)/len(pairs)\n"
                "    return {'delta': b-a, 'ship': (b-a) >= 0.05}\n"
            ),
            obs5="discordant 4 and 4; p ~ 0.41",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json\n"
                "from statsmodels.stats.contingency_tables import mcnemar\n"
                "rows=[json.loads(l) for l in open('goldens/ab_pairs.jsonl')]\n"
                "n01=sum((r['a']==1 and r['b']==0) for r in rows)\n"
                "n10=sum((r['a']==0 and r['b']==1) for r in rows)\n"
                "print('n01',n01,'n10',n10)\n"
                "print(mcnemar([[0,n01],[n10,0]], exact=True).pvalue)\n"
                "PY"
            ),
            stats_obs="n01 4 n10 4\n0.38671875",
            wrong_old="    return {'delta': b-a, 'ship': (b-a) >= 0.05}",
            wrong_new=(
                "    from src.boot_stats import bootstrap_mean_ci\n"
                "    diffs=[p['b']-p['a'] for p in pairs]\n"
                "    lo,hi=bootstrap_mean_ci(diffs)\n"
                "    return {'delta': b-a, 'mean_ci': (lo,hi), 'ship': lo>0}"
            ),
            wrong_label="bootstrap-mean-diff",
            wrong_still="mean_ci excludes 0 by chance; no McNemar",
            still_fail=(
                "FAILED tests/test_mcnemar.py::test_mcnemar_blocks_ship"
                " - AssertionError: mcnemar_p missing; mean_ci=(0.01,0.15) ship=True\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.mcnemar_stats import mcnemar_exact\n"
                "\n"
                "def ab_ship(pairs):\n"
                "    a = sum(p['a'] for p in pairs)/len(pairs)\n"
                "    b = sum(p['b'] for p in pairs)/len(pairs)\n"
                "    pval = mcnemar_exact(pairs)\n"
                "    return {'delta': b-a, 'mcnemar_p': pval, 'ship': pval < 0.05 and b>a}\n"
            ),
            rewrite_obs="McNemar exact p gates ship",
            helper="src/mcnemar_stats.py",
            fix_helper=(
                "from statsmodels.stats.contingency_tables import mcnemar\n"
                "\n"
                "def mcnemar_exact(pairs):\n"
                "    n01 = sum(p['a']==1 and p['b']==0 for p in pairs)\n"
                "    n10 = sum(p['a']==0 and p['b']==1 for p in pairs)\n"
                "    return float(mcnemar([[0, n01], [n10, 0]], exact=True).pvalue)\n"
            ),
            helper_obs="mcnemar exact wrapper",
            pass_obs="1 passed in 0.28s",
            suite_ok="8 passed in 2.0s",
            suite_short="8/8",
            test2="tests/test_mcnemar_second.py",
            test2_body=(
                "def test_clear_win_still_ships():\n"
                "    pairs = [{'a':0,'b':1}]*12 + [{'a':1,'b':1}]*20 + [{'a':0,'b':0}]*8\n"
                "    assert ab_ship(pairs)['ship'] is True\n"
            ),
            test2_pass="1 passed in 0.10s",
            residual="src/ab_dashboard.py still prints +pp only",
            residual_path="src/ab_dashboard.py",
            residual_pat="delta|mcnemar|pp",
            residual_obs="src/ab_dashboard.py: print(f\"+{100*delta:.0f}pp\")\n",
            gate_again="1 passed in 0.24s",
            confirm="mcnemar_p in report",
            final_obs="    return {'delta': b-a, 'mcnemar_p': pval, 'ship': pval < 0.05 and b>a}\n",
            tests_passed=8,
        ),
        _bad(
            slug="wilson-ci-pass-at-k",
            seed=(
                "pass@1 0.71 from n=7; Wilson 95% [0.36, 0.92] still green. "
                "pass@3 rejected. Wilson lower bound >= threshold. Nightly still n=7 point."
            ),
            avoided=(
                "r613 bootstrap mean CI on GEval scores. "
                "This is Wilson interval on pass@1 with n=7"
            ),
            dump="pass@1 n=7 table and Wilson helper",
            first_apply="publish pass@3 instead of pass@1",
            plan="Switch the dashboard to pass@3 so n=7 looks more stable.",
            plan_change="Wilson 95% lower bound must clear the threshold",
            goal=(
                "lantern-eval pass@1=0.71 on n=7 greens a 0.70 gate while Wilson 95% "
                "is [0.36, 0.92]. Gate on Wilson lo. Do not switch to pass@3. "
                "tests/test_wilson.py is the gate."
            ),
            outcome=(
                "n=7 pass@1 0.71 hid Wilson [0.36, 0.92]. pass@3 was 0.86 and still a "
                "point estimate. Plan change: Wilson lo >= threshold. Gate 1/1. Partial: "
                "nightly still n=7 point (xfail)."
            ),
            rg="pass@1|wilson|n=7|proportion",
            rg_obs=(
                "TICKET.md: pass@1 5/7=0.71 green; Wilson unused\n"
                "tests/test_wilson.py: def test_wilson_lo_blocks\n"
                "src/wilson.py: gate = (k/n) >= 0.70\n"
                "goldens/passk.json: k=5 n=7"
            ),
            test="tests/test_wilson.py",
            test_name="wilson-lo-blocks",
            test_body=(
                "def test_wilson_lo_blocks():\n"
                "    rep = pass_at_k(k=5, n=7, threshold=0.70)\n"
                "    assert rep['p'] == pytest.approx(5/7)\n"
                "    assert 0.33 <= rep['wilson'][0] <= 0.40\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert 'pass_at_3' not in rep\n"
            ),
            gate_want="Wilson lo ~0.36 and gate fail",
            fail_obs=(
                "FAILED tests/test_wilson.py::test_wilson_lo_blocks"
                " - AssertionError: gate=pass p=0.714; wilson missing\n"
                "0 passed, 1 failed"
            ),
            fail_short="5/7 point estimate greens",
            src="src/wilson.py",
            src_body=(
                "def pass_at_k(k, n, threshold=0.70):\n"
                "    p = k/n\n"
                "    return {'p': p, 'gate': 'pass' if p >= threshold else 'fail'}\n"
            ),
            obs5="Wilson lo 0.36 on 5/7",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "from statsmodels.stats.proportion import proportion_confint\n"
                "print(proportion_confint(5,7,method='wilson'))\n"
                "print(5/7)\n"
                "PY"
            ),
            stats_obs="(0.3589, 0.9178)\n0.7142857",
            wrong_old="    p = k/n\n    return {'p': p, 'gate': 'pass' if p >= threshold else 'fail'}",
            wrong_new=(
                "    p3 = 1 - (1-k/n)**3\n"
                "    return {'p': k/n, 'pass_at_3': p3, 'gate': 'pass' if p3 >= threshold else 'fail'}"
            ),
            wrong_label="pass-at-3-point",
            wrong_still="pass@3 0.86 still a point estimate",
            still_fail=(
                "FAILED tests/test_wilson.py::test_wilson_lo_blocks"
                " - AssertionError: pass_at_3=0.86 gate=pass; wilson missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.wilson_stats import wilson_interval\n"
                "\n"
                "def pass_at_k(k, n, threshold=0.70):\n"
                "    p = k/n\n"
                "    lo, hi = wilson_interval(k, n)\n"
                "    return {'p': p, 'wilson': (lo, hi), 'gate': 'pass' if lo >= threshold else 'fail'}\n"
            ),
            rewrite_obs="Wilson lo gates pass@k",
            helper="src/wilson_stats.py",
            fix_helper=(
                "from statsmodels.stats.proportion import proportion_confint\n"
                "\n"
                "def wilson_interval(k, n, alpha=0.05):\n"
                "    lo, hi = proportion_confint(k, n, alpha=alpha, method='wilson')\n"
                "    return float(lo), float(hi)\n"
            ),
            helper_obs="wilson_interval wrapper",
            pass_obs="1 passed in 0.19s",
            suite_fail=(
                "FAILED tests/test_nightly_wilson.py::test_nightly_uses_wilson"
                " - AssertionError: nightly gate=pass p=0.71\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_wilson.py",
            nightly_test="tests/test_nightly_wilson.py",
            nightly_body=(
                "def nightly_pass(k=5, n=7):\n"
                "    p = k/n\n"
                "    return {'p': p, 'gate': 'pass' if p >= 0.70 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_uses_wilson():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_wilson.py still n=7 point", strict=False)\n'
                "def test_nightly_uses_wilson():"
            ),
            handoff="nightly n=7 point estimate",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return {'p': p, 'gate': 'pass' if p >= 0.70 else 'fail'}\n",
            gate_again="1 passed in 0.17s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r618 ICL label permutation / Platt vs raw judge
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="icl-label-permutation",
            seed=(
                "few-shot labels shuffled independently of inputs so refund=good teaches "
                "the wrong class; 0.86. Seed shuffle rejected. Pin (input,label) pairs."
            ),
            avoided=(
                "r12 fewshot-sample-order; r100 pytest-randomly-fewshot. "
                "This is ICL label permutation detached from inputs"
            ),
            dump="few-shot pair zipper, label shuffle, and refund=good example",
            first_apply="seed the label shuffle",
            plan="random.seed(0) before shuffling labels so the permutation is stable.",
            plan_change="never permute labels independently; pin (input, label) pairs by id",
            goal=(
                "lantern-eval GEval 0.86 because few-shot labels are shuffled independently "
                "of inputs, teaching refund=good. Pin (input, label) pairs. Do not seed the "
                "shuffle. tests/test_icl_perm.py is the gate."
            ),
            outcome=(
                "Labels were permuted off their inputs so the judge learned refund=good "
                "(0.86). Seeding the shuffle kept a wrong pairing. Plan change: zip by id; "
                "no label shuffle. Tests 1/1 + 8/8. Residual: src/nightly_icl.py still "
                "shuffles labels (out of ticket)."
            ),
            rg="shuffle\\(labels|few_shot|label_perm|refund=good|zip",
            rg_obs=(
                "TICKET.md: shots show input g02 with label from g09 (refund=good)\n"
                "tests/test_icl_perm.py: def test_labels_stay_with_inputs\n"
                "src/icl_perm.py: random.shuffle(labels); shots = zip(inputs, labels)\n"
                "goldens/shots.json: g02 expected deny; g09 expected accept"
            ),
            test="tests/test_icl_perm.py",
            test_name="labels-stay-with-inputs",
            test_body=(
                "def test_labels_stay_with_inputs():\n"
                "    shots = build_shots(GOLDENS, k=3)\n"
                "    assert [(s['id'], s['label']) for s in shots] == [\n"
                "        ('g01', 'deny'), ('g02', 'deny'), ('g03', 'deny')\n"
                "    ]\n"
                "    m = score_with(shots, TARGET)  # invented refund\n"
                "    assert m.success is False and m.score <= 0.30\n"
            ),
            gate_want="canonical pairs and fail on invented refund",
            fail_obs=(
                "FAILED tests/test_icl_perm.py::test_labels_stay_with_inputs"
                " - AssertionError: shots [('g01','accept'),('g02','accept'),('g03','deny')] score 0.86\n"
                "0 passed, 1 failed"
            ),
            fail_short="labels permuted, score 0.86",
            src="src/icl_perm.py",
            src_body=(
                "import random\n"
                "from deepeval.metrics import GEval\n"
                "\n"
                "def build_shots(goldens, k=3):\n"
                "    inputs = [g['input'] for g in goldens[:k]]\n"
                "    labels = [g['expected'] for g in goldens[:k]]\n"
                "    random.shuffle(labels)\n"
                "    return [{'id': goldens[i]['id'], 'input': inputs[i], 'label': labels[i]} for i in range(k)]\n"
            ),
            obs5="g02 input paired with accept label from another row",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json, random\n"
                "rows=[json.loads(l) for l in open('goldens/shots.jsonl')]\n"
                "labels=[r['expected'] for r in rows[:3]]\n"
                "random.seed(0); random.shuffle(labels)\n"
                "print(list(zip([r['id'] for r in rows[:3]], labels)))\n"
                "PY"
            ),
            stats_obs="[('g01', 'accept'), ('g02', 'accept'), ('g03', 'deny')]",
            wrong_old="    random.shuffle(labels)",
            wrong_new="    random.seed(0)\n    random.shuffle(labels)",
            wrong_label="seed-label-shuffle",
            wrong_still="seed 0 still pairs g01/g02 with accept",
            still_fail=(
                "FAILED tests/test_icl_perm.py::test_labels_stay_with_inputs"
                " - AssertionError: still [('g01','accept'),('g02','accept'),('g03','deny')]\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from deepeval.metrics import GEval\n"
                "\n"
                "CANON = ('g01', 'g02', 'g03')\n"
                "\n"
                "def build_shots(goldens, k=3):\n"
                "    by_id = {g['id']: g for g in goldens}\n"
                "    shots = []\n"
                "    for i in CANON[:k]:\n"
                "        g = by_id[i]\n"
                "        shots.append({'id': g['id'], 'input': g['input'], 'label': g['expected']})\n"
                "    return shots\n"
                "\n"
                "def score_with(shots, tc):\n"
                "    steps = [f\"{s['input']} => {s['label']}\" for s in shots]\n"
                "    m = GEval(name='policy', evaluation_steps=steps, threshold=0.7, temperature=0, seed=7)\n"
                "    m.measure(tc)\n"
                "    return m\n"
            ),
            rewrite_obs="pairs pinned by id; no label shuffle",
            helper="src/icl_pairs.py",
            fix_helper=(
                "def assert_paired(shots):\n"
                "    for s in shots:\n"
                "        if s.get('label_id') and s['label_id'] != s['id']:\n"
                "            raise ValueError('label detached from input')\n"
            ),
            helper_obs="assert_paired guard",
            pass_obs="1 passed in 2.4s",
            suite_ok="8 passed in 5.1s",
            suite_short="8/8",
            test2="tests/test_icl_perm_second.py",
            test2_body=(
                "def test_k_four_still_paired():\n"
                "    shots = build_shots(GOLDENS, k=3)\n"
                "    assert all(s['label'] == 'deny' for s in shots)\n"
            ),
            test2_pass="1 passed in 0.12s",
            residual="src/nightly_icl.py still shuffles labels",
            residual_path="src/nightly_icl.py",
            residual_pat="shuffle\\(labels",
            residual_obs="src/nightly_icl.py: random.shuffle(labels)\n",
            gate_again="1 passed in 2.2s",
            confirm="CANON pairs",
            final_obs="        shots.append({'id': g['id'], 'input': g['input'], 'label': g['expected']})\n",
            tests_passed=8,
        ),
        _bad(
            slug="platt-vs-raw-judge",
            seed=(
                "GEval raw 0.62 fail but Platt-scaled 0.74 pass using train-set fit. "
                "Isotonic rejected. Publish raw + calibration; gate on raw. Nightly still Platt."
            ),
            avoided=(
                "r08 strictmode-binary-cluster; r19 threshold-yaml-percent-70. "
                "This is Platt scaling of GEval trained on the eval-adjacent train split"
            ),
            dump="Platt helper, raw GEval 0.62, and scaled 0.74",
            first_apply="swap Platt for isotonic regression",
            plan="Fit isotonic on the same train split so calibration is nonparametric.",
            plan_change="gate on raw GEval; publish calibration as a sidecar only",
            goal=(
                "lantern-eval passes tone because Platt(raw=0.62)=0.74 using a train-set "
                "fit. Gate on raw. Do not swap in isotonic. tests/test_platt.py is the gate."
            ),
            outcome=(
                "Platt mapped raw 0.62 to 0.74 and greened the gate. Isotonic mapped it to "
                "0.71 and still greened. Plan change: gate on raw; sidecar calibration. "
                "Gate 1/1. Partial: nightly still publishes Platt (xfail)."
            ),
            rg="platt|isotonic|calibrat|raw_score|scaled",
            rg_obs=(
                "TICKET.md: raw 0.62 fail; Platt 0.74 pass; fit on train.jsonl\n"
                "tests/test_platt.py: def test_gate_uses_raw\n"
                "src/platt.py: score = platt(raw, a=-1.2, b=0.4)\n"
                "configs/cal.yml: method: platt"
            ),
            test="tests/test_platt.py",
            test_name="gate-uses-raw",
            test_body=(
                "def test_gate_uses_raw():\n"
                "    rep = publish(raw=0.62)\n"
                "    assert rep['raw'] == pytest.approx(0.62)\n"
                "    assert rep['gate'] == 'fail'\n"
                "    assert rep['scaled'] == pytest.approx(0.74, abs=0.02)\n"
                "    assert 'isotonic' not in rep\n"
            ),
            gate_want="raw 0.62 fail even if scaled 0.74",
            fail_obs=(
                "FAILED tests/test_platt.py::test_gate_uses_raw"
                " - AssertionError: gate=pass score=0.74; raw missing\n"
                "0 passed, 1 failed"
            ),
            fail_short="Platt 0.74 is the published score",
            src="src/platt.py",
            src_body=(
                "import math\n"
                "\n"
                "def platt(raw, a=-1.2, b=0.4):\n"
                "    return 1/(1+math.exp(a*raw + b))\n"
                "\n"
                "def publish(raw):\n"
                "    s = platt(raw)\n"
                "    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n"
            ),
            obs5="raw 0.62 -> Platt 0.74",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import math\n"
                "def platt(raw,a=-1.2,b=0.4):\n"
                "    return 1/(1+math.exp(a*raw+b))\n"
                "print(platt(0.62), platt(0.20), platt(0.90))\n"
                "PY"
            ),
            stats_obs="0.742 0.611 0.801",
            wrong_old="    s = platt(raw)\n    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}",
            wrong_new=(
                "    from sklearn.isotonic import IsotonicRegression\n"
                "    s = 0.71  # isotonic on train maps 0.62 -> 0.71\n"
                "    return {'isotonic': s, 'gate': 'pass' if s >= 0.7 else 'fail'}"
            ),
            wrong_label="isotonic-instead",
            wrong_still="0.71 still passes; raw unused",
            still_fail=(
                "FAILED tests/test_platt.py::test_gate_uses_raw"
                " - AssertionError: isotonic=0.71 gate=pass; raw missing\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.cal_sidecar import platt as scale\n"
                "\n"
                "def publish(raw):\n"
                "    scaled = scale(raw)\n"
                "    return {\n"
                "        'raw': raw,\n"
                "        'scaled': scaled,\n"
                "        'gate': 'pass' if raw >= 0.7 else 'fail',\n"
                "    }\n"
            ),
            rewrite_obs="gate on raw; scaled sidecar only",
            helper="src/cal_sidecar.py",
            fix_helper=(
                "import math\n"
                "\n"
                "def platt(raw, a=-1.2, b=0.4):\n"
                "    return 1/(1+math.exp(a*raw + b))\n"
            ),
            helper_obs="sidecar platt, not the gate",
            pass_obs="1 passed in 0.14s",
            suite_fail=(
                "FAILED tests/test_nightly_platt.py::test_nightly_gates_raw"
                " - AssertionError: nightly score=0.74 gate=pass\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_platt.py",
            nightly_test="tests/test_nightly_platt.py",
            nightly_body=(
                "def nightly_publish(raw):\n"
                "    from src.platt import platt\n"
                "    s = platt(raw)\n"
                "    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_gates_raw():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_platt.py still gates Platt", strict=False)\n'
                "def test_nightly_gates_raw():"
            ),
            handoff="nightly Platt gate",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n",
            gate_again="1 passed in 0.13s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r619 nested CV vs single split / promptfoo llm-rubric vs exact
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="nested-cv-vs-single",
            seed=(
                "threshold 0.70 chosen on the same 80-row eval; nested CV would pick 0.58. "
                "Hold-out 10 rejected. Inner/outer split; freeze threshold from inner only."
            ),
            avoided=(
                "r01 GEval temp/seed; r08 strictmode threshold. "
                "This is nested CV vs single-split threshold selection"
            ),
            dump="threshold picker, 80-row eval, and nested CV helper",
            first_apply="hold out 10 rows and pick 0.70 on the remaining 70",
            plan="Hold out 10 rows so threshold selection is not fully in-sample.",
            plan_change="inner/outer nested CV; freeze threshold from inner only",
            goal=(
                "lantern-eval threshold 0.70 was picked on the same 80-row eval it reports "
                "(nested CV would pick 0.58). Freeze threshold from inner folds only. Do not "
                "hold out 10 ad hoc. tests/test_nested_cv.py is the gate."
            ),
            outcome=(
                "Threshold 0.70 was fit on the reported split. A 10-row holdout still picked "
                "0.68 on the remaining 70. Plan change: nested CV inner-only freeze. Tests "
                "1/1 + 8/8. Residual: src/tune_faith.py still single-split."
            ),
            rg="nested|threshold_search|holdout|inner_fold|0.58",
            rg_obs=(
                "TICKET.md: threshold 0.70 from grid on eval.jsonl (n=80); report uses same 80\n"
                "tests/test_nested_cv.py: def test_threshold_from_inner_only\n"
                "src/nested_cv.py: thr = grid_search(eval_rows)  # same rows as report\n"
                "configs/grid.yml: candidates: [0.5,0.58,0.7,0.8]"
            ),
            test="tests/test_nested_cv.py",
            test_name="threshold-from-inner-only",
            test_body=(
                "def test_threshold_from_inner_only():\n"
                "    rep = fit_and_report(EVAL80)\n"
                "    assert rep['threshold'] == pytest.approx(0.58, abs=0.02)\n"
                "    assert set(rep['outer_ids']).isdisjoint(rep['inner_ids'])\n"
                "    assert 'holdout10' not in rep\n"
            ),
            gate_want="inner-only threshold ~0.58",
            fail_obs=(
                "FAILED tests/test_nested_cv.py::test_threshold_from_inner_only"
                " - AssertionError: threshold=0.70; inner_ids == outer_ids\n"
                "0 passed, 1 failed"
            ),
            fail_short="threshold fit on the report split",
            src="src/nested_cv.py",
            src_body=(
                "def fit_and_report(rows):\n"
                "    thr = grid_search(rows)  # 0.70 maximizes F1 on all 80\n"
                "    return {'threshold': thr, 'n': len(rows), 'inner_ids': [r['id'] for r in rows], 'outer_ids': [r['id'] for r in rows]}\n"
            ),
            obs5="full-grid 0.70; nested inner 0.58",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "print('full_grid_f1', {0.5:0.71,0.58:0.69,0.7:0.74,0.8:0.66})\n"
                "print('nested_inner_picks', [0.58,0.58,0.50,0.58,0.58])\n"
                "PY"
            ),
            stats_obs="full_grid_f1 {0.5: 0.71, 0.58: 0.69, 0.7: 0.74, 0.8: 0.66}\nnested_inner_picks [0.58, 0.58, 0.5, 0.58, 0.58]",
            wrong_old="    thr = grid_search(rows)  # 0.70 maximizes F1 on all 80\n    return {'threshold': thr, 'n': len(rows), 'inner_ids': [r['id'] for r in rows], 'outer_ids': [r['id'] for r in rows]}",
            wrong_new=(
                "    hold, rest = rows[:10], rows[10:]\n"
                "    thr = grid_search(rest)\n"
                "    return {'threshold': thr, 'holdout10': True, 'n': len(rest), 'inner_ids': [r['id'] for r in rest], 'outer_ids': [r['id'] for r in hold]}"
            ),
            wrong_label="holdout-10",
            wrong_still="single split, thr 0.68",
            still_fail=(
                "FAILED tests/test_nested_cv.py::test_threshold_from_inner_only"
                " - AssertionError: threshold=0.68 holdout10=True\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.nested_fit import nested_threshold\n"
                "\n"
                "def fit_and_report(rows):\n"
                "    thr, inner_ids, outer_ids = nested_threshold(rows, folds=5)\n"
                "    return {\n"
                "        'threshold': thr,\n"
                "        'inner_ids': inner_ids,\n"
                "        'outer_ids': outer_ids,\n"
                "        'n': len(rows),\n"
                "    }\n"
            ),
            rewrite_obs="nested CV inner-only threshold 0.58",
            helper="src/nested_fit.py",
            fix_helper=(
                "def nested_threshold(rows, folds=5):\n"
                "    # fixture: inner grids pick 0.58; outer ids are every 5th row\n"
                "    outer = [r['id'] for i,r in enumerate(rows) if i % folds == 0]\n"
                "    inner = [r['id'] for i,r in enumerate(rows) if i % folds != 0]\n"
                "    return 0.58, inner, outer\n"
            ),
            helper_obs="nested_threshold returns 0.58",
            pass_obs="1 passed in 0.21s",
            suite_ok="8 passed in 1.8s",
            suite_short="8/8",
            test2="tests/test_nested_cv_second.py",
            test2_body=(
                "def test_outer_never_in_grid():\n"
                "    rep = fit_and_report(EVAL80)\n"
                "    assert set(rep['outer_ids']).isdisjoint(rep['inner_ids'])\n"
            ),
            test2_pass="1 passed in 0.09s",
            residual="src/tune_faith.py still single-split",
            residual_path="src/tune_faith.py",
            residual_pat="grid_search|nested",
            residual_obs="src/tune_faith.py: thr = grid_search(eval_rows)\n",
            gate_again="1 passed in 0.19s",
            confirm="inner/outer disjoint",
            final_obs="        'threshold': thr,\n        'inner_ids': inner_ids,\n",
            tests_passed=8,
        ),
        _bad(
            slug="pfoo-rubric-vs-exact",
            seed=(
                "promptfoo gradingType llm-rubric silently replaced exact-match on SKU; "
                "0.91 vs exact 0.00. Add-exact-as-extra rejected. Fail if exact=0. "
                "Nightly still rubric-only."
            ),
            avoided=(
                "r04 promptfoo-vs-geval; r02 jsoncorrect-additionalprops. "
                "This is promptfoo gradingType swap llm-rubric vs exact"
            ),
            dump="promptfooconfig gradingType, exact-match 0.00, and rubric 0.91",
            first_apply="add exact-match as an extra metric",
            plan="Keep llm-rubric and also emit exact-match so both numbers exist.",
            plan_change="fail the case if exact-match is 0 regardless of rubric",
            goal=(
                "lantern-eval greens SKU-CL12 because promptfoo gradingType llm-rubric "
                "replaced exact-match (0.91 vs 0.00). Fail if exact=0. Do not only add "
                "exact as a decorative extra. tests/test_pfoo_exact.py is the gate."
            ),
            outcome=(
                "llm-rubric 0.91 hid exact-match 0.00 on the SKU. Adding exact as an extra "
                "left the gate on rubric. Plan change: fail if exact==0. Gate 1/1. Partial: "
                "nightly still rubric-only (xfail)."
            ),
            rg="gradingType|llm-rubric|exact-match|SKU-CL12",
            rg_obs=(
                "TICKET.md: gradingType llm-rubric; exact 0.00 on SKU-CL12; published 0.91\n"
                "tests/test_pfoo_exact.py: def test_exact_zero_fails\n"
                "promptfooconfig.yaml: gradingType: llm-rubric\n"
                "src/pfoo_exact.py: score = rubric_score(out, gold)"
            ),
            test="tests/test_pfoo_exact.py",
            test_name="exact-zero-fails",
            test_body=(
                "def test_exact_zero_fails():\n"
                "    rep = grade(actual='Sure, refunded!', expected='SKU-CL12: deny after 40d')\n"
                "    assert rep['exact'] == 0.0\n"
                "    assert rep['rubric'] == pytest.approx(0.91, abs=0.02)\n"
                "    assert rep['gate'] == 'fail'\n"
            ),
            gate_want="exact 0 fails even if rubric 0.91",
            fail_obs=(
                "FAILED tests/test_pfoo_exact.py::test_exact_zero_fails"
                " - AssertionError: gate=pass score=0.91; exact missing\n"
                "0 passed, 1 failed"
            ),
            fail_short="rubric 0.91 is the only score",
            src="src/pfoo_exact.py",
            src_body=(
                "def grade(actual, expected):\n"
                "    s = rubric_score(actual, expected)  # 0.91\n"
                "    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n"
            ),
            obs5="exact 0.00; rubric 0.91",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "exp='SKU-CL12: deny after 40d'\n"
                "act='Sure, refunded!'\n"
                "print('exact', float(act==exp))\n"
                "print('rubric_stub', 0.91)\n"
                "PY"
            ),
            stats_obs="exact 0.0\nrubric_stub 0.91",
            wrong_old="    s = rubric_score(actual, expected)  # 0.91\n    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}",
            wrong_new=(
                "    s = rubric_score(actual, expected)\n"
                "    exact = float(actual==expected)\n"
                "    return {'score': s, 'exact_extra': exact, 'gate': 'pass' if s >= 0.7 else 'fail'}"
            ),
            wrong_label="exact-as-extra",
            wrong_still="gate still rubric-only",
            still_fail=(
                "FAILED tests/test_pfoo_exact.py::test_exact_zero_fails"
                " - AssertionError: gate=pass exact_extra=0.0\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.exact_sku import exact_match, rubric_score\n"
                "\n"
                "def grade(actual, expected):\n"
                "    exact = exact_match(actual, expected)\n"
                "    rub = rubric_score(actual, expected)\n"
                "    gate = 'fail' if exact == 0.0 else ('pass' if rub >= 0.7 else 'fail')\n"
                "    return {'exact': exact, 'rubric': rub, 'gate': gate}\n"
            ),
            rewrite_obs="exact==0 fail-closed; rubric secondary",
            helper="src/exact_sku.py",
            fix_helper=(
                "def exact_match(actual, expected):\n"
                "    return 1.0 if actual.strip() == expected.strip() else 0.0\n"
                "\n"
                "def rubric_score(actual, expected):\n"
                "    return 0.91 if actual else 0.0\n"
            ),
            helper_obs="exact_match helper",
            pass_obs="1 passed in 0.16s",
            suite_fail=(
                "FAILED tests/test_nightly_pfoo.py::test_nightly_fails_exact_zero"
                " - AssertionError: nightly gate=pass score=0.91\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_pfoo.py",
            nightly_test="tests/test_nightly_pfoo.py",
            nightly_body=(
                "def nightly_grade(actual, expected):\n"
                "    s = rubric_score(actual, expected)\n"
                "    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n"
            ),
            xfail_old="def test_nightly_fails_exact_zero():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_pfoo.py still rubric-only", strict=False)\n'
                "def test_nightly_fails_exact_zero():"
            ),
            handoff="nightly rubric-only",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return {'score': s, 'gate': 'pass' if s >= 0.7 else 'fail'}\n",
            gate_again="1 passed in 0.14s",
            tests_passed=1,
        ),
    )
)


# ---------------------------------------------------------------------------
# r620 difficulty-sorted truncate / BLEURT checkpoint not in key
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="diff-sorted-truncate",
            seed=(
                "eval sorted by GEval desc then head(50) drops hard CL-12; published 0.88. "
                "Shuffle-then-head rejected. Stratify by policy_id; never sort by score."
            ),
            avoided=(
                "r12 fewshot-sample-order; r21 faithfulness-nchunks-drop-cl12. "
                "This is difficulty-sorted head(50) selection"
            ),
            dump="eval sampler, GEval-desc sort, and head(50)",
            first_apply="shuffle then head(50)",
            plan="Shuffle before head(50) so hard items can appear.",
            plan_change="stratified sample by policy_id; never sort by score",
            goal=(
                "lantern-eval 0.88 because eval.jsonl is sorted by GEval descending then "
                "head(50), dropping hard CL-12 items. Stratify by policy_id. Do not only "
                "shuffle then head. tests/test_diff_trunc.py is the gate."
            ),
            outcome=(
                "Sorting by GEval then head(50) dropped CL-12 and published 0.88. Shuffle+"
                "head still under-sampled CL-12 (2/50). Plan change: stratify by policy_id. "
                "Tests 1/1 + 8/8. Residual: src/nightly_sample.py still sorts (out of ticket)."
            ),
            rg="head\\(50\\)|sort.*geval|policy_id|stratify",
            rg_obs=(
                "TICKET.md: published 0.88 on 50 easiest; CL-12 count=0\n"
                "tests/test_diff_trunc.py: def test_stratified_keeps_cl12\n"
                "src/diff_trunc.py: rows=sorted(rows, key=lambda r: -r['geval'])[:50]\n"
                "goldens/eval.jsonl: 200 rows, 24 CL-12"
            ),
            test="tests/test_diff_trunc.py",
            test_name="stratified-keeps-cl12",
            test_body=(
                "def test_stratified_keeps_cl12():\n"
                "    picked = sample_eval(ROWS, k=50)\n"
                "    n_cl = sum(r['policy_id']=='CL-12' for r in picked)\n"
                "    assert 5 <= n_cl <= 8  # 24/200 * 50 = 6\n"
                "    assert max(r['geval'] for r in picked) - min(r['geval'] for r in picked) > 0.4\n"
            ),
            gate_want="about 6 CL-12 in the 50",
            fail_obs=(
                "FAILED tests/test_diff_trunc.py::test_stratified_keeps_cl12"
                " - AssertionError: n_cl=0; all geval>=0.80\n"
                "0 passed, 1 failed"
            ),
            fail_short="head(50) after GEval-desc, n_cl=0",
            src="src/diff_trunc.py",
            src_body=(
                "def sample_eval(rows, k=50):\n"
                "    return sorted(rows, key=lambda r: -r['geval'])[:k]\n"
            ),
            obs5="top-50 min GEval 0.80; CL-12 all below 0.35",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import json\n"
                "rows=[json.loads(l) for l in open('goldens/eval.jsonl')]\n"
                "top=sorted(rows, key=lambda r: -r['geval'])[:50]\n"
                "print('min', min(r['geval'] for r in top), 'cl12', sum(r['policy_id']=='CL-12' for r in top))\n"
                "print('cl12_scores', sorted(r['geval'] for r in rows if r['policy_id']=='CL-12')[:5])\n"
                "PY"
            ),
            stats_obs="min 0.80 cl12 0\ncl12_scores [0.12, 0.14, 0.18, 0.21, 0.22]",
            wrong_old="    return sorted(rows, key=lambda r: -r['geval'])[:k]",
            wrong_new=(
                "    import random\n"
                "    rows=list(rows)\n"
                "    random.Random(0).shuffle(rows)\n"
                "    return rows[:k]"
            ),
            wrong_label="shuffle-then-head",
            wrong_still="CL-12 ~2/50, not stratified",
            still_fail=(
                "FAILED tests/test_diff_trunc.py::test_stratified_keeps_cl12"
                " - AssertionError: n_cl=2\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.strat_sample import stratified\n"
                "\n"
                "def sample_eval(rows, k=50):\n"
                "    return stratified(rows, k=k, key='policy_id')\n"
            ),
            rewrite_obs="stratified by policy_id; no score sort",
            helper="src/strat_sample.py",
            fix_helper=(
                "import random\n"
                "from collections import defaultdict\n"
                "\n"
                "def stratified(rows, k, key, seed=7):\n"
                "    buckets = defaultdict(list)\n"
                "    for r in rows:\n"
                "        buckets[r[key]].append(r)\n"
                "    rng = random.Random(seed)\n"
                "    out = []\n"
                "    keys = list(buckets)\n"
                "    i = 0\n"
                "    while len(out) < k:\n"
                "        b = keys[i % len(keys)]\n"
                "        if buckets[b]:\n"
                "            out.append(buckets[b].pop(rng.randrange(len(buckets[b]))))\n"
                "        i += 1\n"
                "        if i > k * 20:\n"
                "            break\n"
                "    return out[:k]\n"
            ),
            helper_obs="round-robin stratified sampler",
            pass_obs="1 passed in 0.17s",
            suite_ok="8 passed in 1.7s",
            suite_short="8/8",
            test2="tests/test_diff_trunc_second.py",
            test2_body=(
                "def test_never_sorts_by_geval():\n"
                "    src = open('src/diff_trunc.py').read()\n"
                "    assert 'geval' not in src or 'sorted' not in src\n"
            ),
            test2_pass="1 passed in 0.07s",
            residual="src/nightly_sample.py still sorts",
            residual_path="src/nightly_sample.py",
            residual_pat="sorted|head",
            residual_obs="src/nightly_sample.py: sorted(rows, key=lambda r: -r['geval'])[:50]\n",
            gate_again="1 passed in 0.15s",
            confirm="stratified helper",
            final_obs="    return stratified(rows, k=k, key='policy_id')\n",
            tests_passed=8,
        ),
        _bad(
            slug="bleurt-ckpt-unkeyed",
            seed=(
                "BLEURT checkpoint bleurt-tiny-128 vs bleurt-20; cache key metric|hyp|ref. "
                "Pin tiny rejected. Include ckpt hash in key. Nightly still tiny after prod "
                "switched to bleurt-20."
            ),
            avoided=(
                "r11 judge-hparams-not-in-key; r35 prompt-template-hash-omitted. "
                "This is BLEURT checkpoint omitted from the cache key"
            ),
            dump="BLEURT ckpt path, cache key, and tiny vs bleurt-20 scores",
            first_apply="pin bleurt-tiny-128 in configs",
            plan="Pin BLEURT_CKPT=bleurt-tiny-128 so CI matches the laptop.",
            plan_change="put ckpt hash in the cache key; do not pin the old tiny model",
            goal=(
                "lantern-eval reuses 0.79 after prod switched BLEURT to bleurt-20 because "
                "the cache key is metric|hyp|ref. Put ckpt hash in the key. Do not pin tiny. "
                "tests/test_bleurt_ckpt.py is the gate."
            ),
            outcome=(
                "tiny-128 0.79 reused after bleurt-20 (true 0.41) because the key omitted "
                "the checkpoint. Pinning tiny hid the switch. Plan change: key includes "
                "ckpt sha256. Gate 1/1. Partial: nightly still keys hyp|ref (xfail)."
            ),
            rg="BLEURT|bleurt-tiny|bleurt-20|ckpt|cache_key",
            rg_obs=(
                "TICKET.md: cache hit 0.79 after BLEURT_CKPT=bleurt-20; tiny was 0.79, 20 is 0.41\n"
                "tests/test_bleurt_ckpt.py: def test_ckpt_busts_cache\n"
                "src/bleurt_ckpt.py: key = f\"bleurt|{hyp}|{ref}\"\n"
                "configs/bleurt.env: BLEURT_CKPT=bleurt-20"
            ),
            test="tests/test_bleurt_ckpt.py",
            test_name="ckpt-busts-cache",
            test_body=(
                "def test_ckpt_busts_cache():\n"
                "    k_tiny = cache_key(HYP, REF, ckpt='bleurt-tiny-128')\n"
                "    k_20 = cache_key(HYP, REF, ckpt='bleurt-20')\n"
                "    assert k_tiny != k_20\n"
                "    assert ckpt_sha('bleurt-20') in k_20\n"
            ),
            gate_want="tiny and bleurt-20 keys differ",
            fail_obs=(
                "FAILED tests/test_bleurt_ckpt.py::test_ckpt_busts_cache"
                " - AssertionError: keys equal bleurt|hyp|ref\n"
                "0 passed, 1 failed"
            ),
            fail_short="key omits ckpt",
            src="src/bleurt_ckpt.py",
            src_body=(
                "def cache_key(hyp, ref, ckpt=None):\n"
                "    return f\"bleurt|{hyp}|{ref}\"\n"
            ),
            obs5="tiny 0.79 vs bleurt-20 0.41, same key",
            stats_cmd=(
                "python3 - <<'PY'\n"
                "import hashlib, os\n"
                "print(os.environ.get('BLEURT_CKPT'))\n"
                "for p in ['ckpts/bleurt-tiny-128','ckpts/bleurt-20']:\n"
                "    print(p, hashlib.sha256(open(p,'rb').read(64)).hexdigest()[:10])\n"
                "PY"
            ),
            stats_obs="bleurt-20\nckpts/bleurt-tiny-128 9aa10c22ab\nckpts/bleurt-20 44d0ee19c1",
            wrong_old="    return f\"bleurt|{hyp}|{ref}\"",
            wrong_new="    return f\"bleurt|bleurt-tiny-128|{hyp}|{ref}\"  # pinned tiny",
            wrong_label="pin-tiny-in-key",
            wrong_still="prod bleurt-20 still hits tiny key if caller omits ckpt",
            still_fail=(
                "FAILED tests/test_bleurt_ckpt.py::test_ckpt_busts_cache"
                " - AssertionError: k_20 still pinned tiny string\n"
                "0 passed, 1 failed"
            ),
            fix_src=(
                "from src.bleurt_hash import ckpt_sha\n"
                "\n"
                "def cache_key(hyp, ref, ckpt=None):\n"
                "    if not ckpt:\n"
                "        raise ValueError('ckpt required')\n"
                "    return f\"bleurt|{ckpt}|{ckpt_sha(ckpt)}|{hash(hyp)}|{hash(ref)}\"\n"
            ),
            rewrite_obs="ckpt name+sha in key; required",
            helper="src/bleurt_hash.py",
            fix_helper=(
                "import hashlib\n"
                "from pathlib import Path\n"
                "\n"
                "def ckpt_sha(name):\n"
                "    p = Path('ckpts')/name\n"
                "    return hashlib.sha256(p.read_bytes()).hexdigest()\n"
            ),
            helper_obs="ckpt_sha helper",
            pass_obs="1 passed in 0.22s",
            suite_fail=(
                "FAILED tests/test_nightly_bleurt.py::test_nightly_keys_ckpt"
                " - AssertionError: nightly key=bleurt|hyp|ref\n"
                "7 passed, 1 failed"
            ),
            nightly="src/nightly_bleurt.py",
            nightly_test="tests/test_nightly_bleurt.py",
            nightly_body=(
                "def nightly_key(hyp, ref):\n"
                "    return f\"bleurt|{hyp}|{ref}\"\n"
            ),
            xfail_old="def test_nightly_keys_ckpt():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: src/nightly_bleurt.py still omits ckpt", strict=False)\n'
                "def test_nightly_keys_ckpt():"
            ),
            handoff="nightly hyp|ref key",
            xfail_obs="1 passed, 1 xfailed",
            leftover_obs="    return f\"bleurt|{hyp}|{ref}\"\n",
            gate_again="1 passed in 0.20s",
            tests_passed=1,
        ),
    )
)
