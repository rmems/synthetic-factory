"""Plants r140–r155: more ledger/fencing (not PSP webhook-vs-retrieve)."""

from mill_plants import _ok, _fail
from mill_plants_h import _ddl, _naive, _paths, _rg_obs

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))

# r140 interchange vs net deposit / scheme fee after net
_src, _skip = _naive(
    "post_ix",
    'debit_merch(ev["batch_id"], ev["cents"])',
    "counted every interchange post",
)
pair(
    _ok(
        slug="interchange-vs-net-deposit",
        surfaces="interchange fee debit vs net deposit credit",
        avoided="r128 split vs platform fee; r136 net vs gross. This is ix_id debit vs deposit_id net",
        this_is="ix PK debit fee; deposit PK credits net (gross-ix)",
        seed="post interchange + net deposit same batch",
        first_apply="batch deposited today",
        plan_change="ix claims fee; deposit credits net not gross",
        step_note="Batch-day 6–7; PK 8–11; second batch 12–13.",
        **_paths("ix_net"),
        table="till_ix_net",
        pk="deposit_id",
        rg="interchange_fee|net_deposit|gross_cents|ix_id",
        rg_obs=_rg_obs("ix_net", "post_ix", "net_dep", "test_ix_not_deposit_double"),
        test_name="ix-not-deposit-double test",
        surface_read="interchange fee plus net deposit",
        skip_pred="this batch already deposited today",
        verb="post",
        skip_label="batch-deposited-today skip",
        src_body=_src,
        hook_body="def net_dep(batch_id, gross):\n    credit_merch(batch_id, gross)\n",
        test_body=(
            "def test_ix_not_deposit_double():\n"
            '    post_ix(ix("ix_1", batch="b_1", cents=200))\n'
            '    post_ix(ix("ix_1", batch="b_1", cents=200))\n'
            '    net_dep("b_1", 5000)\n'
            '    assert merch_cents("m_1") == 4800 and ix_cents("ix_1") == 200 and ix_rows("dep_1") == 1\n'
            "\n"
            "def test_second_batch():\n"
            '    post_ix(ix("ix_a", batch="b_a", cents=4))\n'
            '    net_dep("b_a", 100)\n'
            '    post_ix(ix("ix_b", batch="b_b", cents=2))\n'
            '    net_dep("b_b", 40)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        obs3="ix and deposit both move full gross",
        obs4="ix debit fee; deposit credits net",
        obs5="merch 4800; ix once; second batch adds",
        fail_obs="FAILED test_ix_not_deposit_double - merch 5000 or 10000 not 4800\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not deposited_today(ev["batch_id"]):\n        debit_merch(ev["batch_id"], ev["cents"])',
        obs7="deposit still credits gross; new batch same day dropped.",
        still_fail_obs="FAILED test_ix_not_deposit_double - deposit credited gross\n1 failed, 1 passed",
        rewrite_src=(
            "def post_ix(ev):\n"
            "    if not claim_ix(ev['ix_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    book_ix(ev["batch_id"], ev["cents"], ix=ev["ix_id"])\n'
            '    return {"ok": True, "ix": True}\n'
        ),
        rewrite_src_obs="claim ix_id books fee",
        rewrite_hook=(
            "def net_dep(batch_id, gross):\n"
            "    did = dep_id(batch_id)\n"
            "    if not claim_dep(did):\n"
            '        return {"ok": True, "dup": True}\n'
            "    net = gross - ix_of(batch_id)\n"
            "    credit_merch(merch_of_batch(batch_id), net, deposit=did)\n"
            '    return {"ok": True, "net": net}\n'
        ),
        obs9="deposit claims deposit_id at net.",
        rewrite_hook_obs="PK deposit_id net",
        ddl=_ddl("till_ix_net", "deposit_id", "  batch_id text UNIQUE,\n  ix_cents int NOT NULL"),
        ddl_obs="PK deposit_id",
        test2_body=(
            "def test_second_batch():\n"
            '    post_ix(ix("ix_a", batch="b_a", cents=4))\n'
            '    net_dep("b_a", 100)\n'
            '    post_ix(ix("ix_b", batch="b_b", cents=2))\n'
            '    net_dep("b_b", 40)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        psql_rows="dep_1\ndep_a\ndep_b",
        residual="scheme assessment stacked on ix",
        grep_pat="ix_of",
        grep_obs="src/ix_net.py: net = gross-ix; no scheme stack",
        goal="till-ix interchange and deposit both moved gross. Ix fee; deposit net. Gate: tests/test_ix_net.py.",
        plan="Skip post if this batch already deposited today.",
        outcome="Ix+deposit moved gross. Batch-day skip left deposit on gross. Plan change: ix PK + net deposit. Tests 2/2 + second batch + suite 8/8.",
    ),
    _fail(
        slug="scheme-fee-after-net",
        surfaces="scheme assessment vs already-netted deposit",
        avoided="r140 ix vs net; r136 net close. This is scheme_id after deposit",
        this_is="scheme after net opens receivable; does not rewrite deposit",
        seed="net deposit then scheme assessment",
        first_apply="scheme assessed today",
        plan_change="scheme PK receivable; deposit stays netted",
        step_note="Scheme-day 6–7; PK 8–11; second 12–13; rewrite-net xfail 15–17.",
        next_note="Unused: scheme after net should rewrite deposit. Avoid scheme-assessed-today skip.",
        **_paths("sch_fee", fail=True),
        table="till_sch_fee",
        pk="scheme_id",
        rg="scheme.assessment|after_net|receivable_scheme",
        rg_obs=_rg_obs("sch_fee", "assess_sch", "netted", "test_scheme_not_rewrite_net"),
        test_name="scheme-not-rewrite-net test",
        surface_read="scheme assessment plus netted deposit",
        skip_pred="this scheme already assessed today",
        verb="assess",
        skip_label="scheme-assessed-today skip",
        src_body=_naive("assess_sch", 'debit_merch(ev["batch_id"], ev["cents"])', "counted every scheme assess")[0],
        hook_body="def netted(batch_id, net):\n    credit_merch(batch_id, net)\n",
        test_body=(
            "def test_scheme_not_rewrite_net():\n"
            '    netted("b_1", 4800)\n'
            '    assess_sch(sc("sc_1", batch="b_1", cents=35))\n'
            '    assess_sch(sc("sc_1", batch="b_1", cents=35))\n'
            '    assert merch_cents("m_1") == 4800 and recv_cents("m_1") == 35 and sch_rows("sc_1") == 1\n'
            "\n"
            "def test_second_scheme():\n"
            '    netted("b_a", 96)\n'
            '    assess_sch(sc("sc_a", batch="b_a", cents=3))\n'
            '    netted("b_b", 38)\n'
            '    assess_sch(sc("sc_b", batch="b_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        test_body_short="same — scheme receivable; deposit stays",
        obs3="scheme rewrites netted deposit",
        obs4="scheme receivable; deposit stays",
        obs5="merch 4800; recv 35; second scheme adds",
        fail_obs="FAILED test_scheme_not_rewrite_net - merch 4765 == 4800 or rows 3\n1 failed, 1 passed",
        skip_old=_naive("assess_sch", 'debit_merch(ev["batch_id"], ev["cents"])', "counted every scheme assess")[1],
        skip_new='    if not assessed_today(ev["scheme_id"]):\n        debit_merch(ev["batch_id"], ev["cents"])',
        obs7="second scheme ok; hides receivable.",
        still_fail_obs="FAILED if scheme rewrote deposit (merch 4765)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def assess_sch(ev):\n"
            "    if not claim_sch(ev['scheme_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_batch(ev["batch_id"]), ev["cents"], scheme=ev["scheme_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim scheme_id opens receivable",
        rewrite_hook=(
            "def netted(batch_id, net):\n"
            "    if not claim_dep2(dep_id(batch_id)):\n"
            "        return existing_dep(batch_id)\n"
            "    credit_merch(merch_of_batch(batch_id), net)\n"
            "    return batch_id\n"
        ),
        rewrite_hook_obs="deposit stays netted",
        ddl=_ddl("till_sch_fee", "scheme_id", "  batch_id text NOT NULL,\n  recv_cents int NOT NULL"),
        ddl_obs="PK scheme_id",
        test2_body=(
            "def test_second_scheme():\n"
            '    netted("b_a", 96)\n'
            '    assess_sch(sc("sc_a", batch="b_a", cents=3))\n'
            '    netted("b_b", 38)\n'
            '    assess_sch(sc("sc_b", batch="b_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        xfail_label="scheme after net should rewrite deposit",
        xfail_body=(
            "def test_scheme_rewrites_net():\n"
            '    netted("b_p", 4800)\n'
            '    assess_sch(sc("sc_p", batch="b_p", cents=35))\n'
            '    assert merch_cents("m_p") == 4765 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_scheme_rewrites_net - recv opened; deposit not rewritten\n1 failed",
        xfail_old="def test_scheme_rewrites_net():",
        xfail_new='@pytest.mark.xfail(reason="handoff: scheme after net rewrite vs receivable is a policy fork", strict=True)\ndef test_scheme_rewrites_net():',
        xfail_patch_obs="xfailed scheme rewrite net",
        goal="till-sch scheme rewrote netted deposit. Scheme receivable. Gate: tests/test_sch_fee.py.",
        plan="Skip assess if this scheme already assessed today.",
        outcome="Scheme rewrote deposit. Scheme-day skip hid receivable. Plan change: scheme PK recv. Primary+second pass. Partial: rewrite-net xfail handoff.",
    ),
)

# r141 DCC markup vs home-ccy / markup after settle
_src, _skip = _naive(
    "book_dcc",
    'credit_merch(ev["txn_id"], ev["cents"])',
    "counted every DCC book",
)
pair(
    _ok(
        slug="dcc-markup-vs-home-ccy",
        surfaces="DCC markup book vs home-currency settlement",
        avoided="r125 fx lock; r130 fx reval. This is dcc_rate vs home settle not spot",
        this_is="DCC records markup; home settle PK uses cardholder amount",
        seed="book DCC + home settle same txn",
        first_apply="DCC booked today",
        plan_change="DCC records rate; settle PK cardholder_cents not merchant spot",
        step_note="Txn-day 6–7; PK 8–11; second txn 12–13.",
        **_paths("dcc_mk"),
        table="till_dcc_mk",
        pk="txn_id",
        rg="dcc.markup|home_ccy|cardholder_cents|dcc_rate",
        rg_obs=_rg_obs("dcc_mk", "book_dcc", "home_set", "test_dcc_not_home_double"),
        test_name="dcc-not-home-double test",
        surface_read="DCC markup plus home-ccy settle",
        skip_pred="this txn already DCC-booked today",
        verb="credit",
        skip_label="dcc-booked-today skip",
        src_body=_src,
        hook_body="def home_set(txn_id, home_cents):\n    credit_merch(txn_id, home_cents)\n",
        test_body=(
            "def test_dcc_not_home_double():\n"
            '    book_dcc(dcc("tx_1", cardholder=5000, rate=1.04))\n'
            '    book_dcc(dcc("tx_1", cardholder=5000, rate=1.04))\n'
            '    home_set("tx_1", 4808)\n'
            '    assert merch_cents("m_1") == 4808 and dcc_markup("tx_1") == 192 and dcc_rows("tx_1") == 1\n'
            "\n"
            "def test_second_txn():\n"
            '    book_dcc(dcc("tx_a", cardholder=100, rate=1.04))\n'
            '    home_set("tx_a", 96)\n'
            '    book_dcc(dcc("tx_b", cardholder=40, rate=1.04))\n'
            '    home_set("tx_b", 38)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        obs3="DCC and home both credit cardholder",
        obs4="DCC records markup; settle home amount",
        obs5="merch 4808; markup 192; second txn adds",
        fail_obs="FAILED test_dcc_not_home_double - merch 5000 or 9808\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not dcc_today(ev["txn_id"]):\n        credit_merch(ev["txn_id"], ev["cents"])',
        obs7="home still credits extra; new txn same day dropped.",
        still_fail_obs="FAILED test_dcc_not_home_double - DCC credited cardholder\n1 failed, 1 passed",
        rewrite_src=(
            "def book_dcc(ev):\n"
            "    if not claim_dcc(ev['txn_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_dcc(ev["txn_id"], ev["cardholder"], ev["rate"])\n'
            '    return {"ok": True, "dcc": True}\n'
        ),
        rewrite_src_obs="claim txn_id stores DCC; no credit",
        rewrite_hook=(
            "def home_set(txn_id, home_cents):\n"
            "    if not claim_home(txn_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_txn(txn_id), home_cents, txn=txn_id)\n"
            '    return {"ok": True}\n'
        ),
        obs9="home settle claims same txn_id.",
        rewrite_hook_obs="PK txn_id home",
        ddl=_ddl("till_dcc_mk", "txn_id", "  cardholder int NOT NULL,\n  rate numeric NOT NULL"),
        ddl_obs="PK txn_id",
        test2_body=(
            "def test_second_txn():\n"
            '    book_dcc(dcc("tx_a", cardholder=100, rate=1.04))\n'
            '    home_set("tx_a", 96)\n'
            '    book_dcc(dcc("tx_b", cardholder=40, rate=1.04))\n'
            '    home_set("tx_b", 38)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        psql_rows="tx_1\ntx_a\ntx_b",
        residual="opt-out to home after DCC booked",
        grep_pat="store_dcc",
        grep_obs="src/dcc_mk.py: store rate; no opt-out flip",
        goal="till-dcc DCC and home both credited cardholder. DCC records; settle home. Gate: tests/test_dcc_mk.py.",
        plan="Skip credit if this txn already DCC-booked today.",
        outcome="DCC+home double-credited. Txn-day skip left DCC as credit. Plan change: store DCC; settle home PK. Tests 2/2 + second txn + suite 8/8.",
    ),
    _fail(
        slug="dcc-markup-after-settle",
        surfaces="late DCC markup vs already home-settled txn",
        avoided="r141 DCC vs home; r125 expire. This is markup after settle no-op",
        this_is="late DCC after settle records only; no extra debit",
        seed="home settle then late DCC markup",
        first_apply="markup posted today",
        plan_change="late DCC after settle no-ops credit",
        step_note="Markup-day 6–7; PK 8–11; second 12–13; opt-in-late xfail 15–17.",
        next_note="Unused: late DCC after settle should flip to DCC. Avoid markup-posted-today skip.",
        **_paths("dcc_late", fail=True),
        table="till_dcc_late",
        pk="txn_id",
        rg="dcc.late|after_settle|markup_noop",
        rg_obs=_rg_obs("dcc_late", "late_dcc", "settled_home", "test_late_dcc_noop"),
        test_name="late-dcc-noop test",
        surface_read="late DCC markup plus home-settled txn",
        skip_pred="this markup already posted today",
        verb="markup",
        skip_label="markup-posted-today skip",
        src_body=_naive("late_dcc", 'credit_merch(ev["txn_id"], ev["cents"])', "counted every late DCC")[0],
        hook_body="def settled_home(txn_id, home_cents):\n    credit_merch(txn_id, home_cents)\n",
        test_body=(
            "def test_late_dcc_noop():\n"
            '    settled_home("tx_1", 4808)\n'
            '    late_dcc(dcc("tx_1", cardholder=5000, rate=1.04))\n'
            '    late_dcc(dcc("tx_1", cardholder=5000, rate=1.04))\n'
            '    assert merch_cents("m_1") == 4808 and dcc_late("tx_1") and dcc_rows("tx_1") == 1\n'
            "\n"
            "def test_second_txn():\n"
            '    settled_home("tx_a", 96)\n'
            '    settled_home("tx_b", 38)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        test_body_short="same — late DCC records; settle stays",
        obs3="late DCC extra-credits cardholder",
        obs4="late DCC records; merch stays home",
        obs5="merch 4808; late flagged; second txn independent",
        fail_obs="FAILED test_late_dcc_noop - merch 5000 or 9808\n1 failed, 1 passed",
        skip_old=_naive("late_dcc", 'credit_merch(ev["txn_id"], ev["cents"])', "counted every late DCC")[1],
        skip_new='    if not markup_today(ev["txn_id"]):\n        credit_merch(ev["txn_id"], ev["cents"])',
        obs7="second txn ok; hides late no-op.",
        still_fail_obs="FAILED if late DCC credited 5000 after settle\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_dcc(ev):\n"
            "    if settled(ev['txn_id']):\n"
            '        flag_late_dcc(ev["txn_id"])\n'
            '        return {"ok": True, "late": True}\n'
            "    if not claim_dcc2(ev['txn_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_dcc(ev["txn_id"], ev["cardholder"], ev["rate"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="late after settle flags only",
        rewrite_hook=(
            "def settled_home(txn_id, home_cents):\n"
            "    if not claim_home2(txn_id):\n"
            "        return existing_txn(txn_id)\n"
            "    credit_merch(merch_of_txn(txn_id), home_cents)\n"
            "    mark_settled(txn_id)\n"
            "    return txn_id\n"
        ),
        rewrite_hook_obs="home settle PK",
        ddl=_ddl("till_dcc_late", "txn_id", "  settled bool NOT NULL DEFAULT false,\n  late_dcc bool NOT NULL DEFAULT false"),
        ddl_obs="PK txn_id",
        test2_body=(
            "def test_second_txn():\n"
            '    settled_home("tx_a", 96)\n'
            '    settled_home("tx_b", 38)\n'
            '    assert merch_cents("m_a") == 96 and merch_cents("m_b") == 38\n'
        ),
        xfail_label="late DCC after settle should flip",
        xfail_body=(
            "def test_late_dcc_flip():\n"
            '    settled_home("tx_p", 4808)\n'
            '    late_dcc(dcc("tx_p", cardholder=5000, rate=1.04))\n'
            '    assert merch_cents("m_p") == 5000 and dcc_markup("tx_p") == 192\n'
        ),
        xfail_fail_obs="FAILED test_late_dcc_flip - flagged late; did not flip\n1 failed",
        xfail_old="def test_late_dcc_flip():",
        xfail_new='@pytest.mark.xfail(reason="handoff: late DCC after settle flip is a scheme exception", strict=True)\ndef test_late_dcc_flip():',
        xfail_patch_obs="xfailed late DCC flip",
        goal="till-dcc-late late markup credited after settle. Late records only. Gate: tests/test_dcc_late.py.",
        plan="Skip markup if this markup already posted today.",
        outcome="Late DCC credited. Markup-day skip hid no-op. Plan change: flag late. Primary+second pass. Partial: flip xfail handoff.",
    ),
)

# r142 installment schedule vs first capture / late installment after close
_src, _skip = _naive(
    "sched_inst",
    'capture_pay(ev["plan_id"], ev["cents"])',
    "counted every installment schedule",
)
pair(
    _ok(
        slug="installment-vs-first-capture",
        surfaces="installment schedule vs first capture",
        avoided="r84 incremental auth; r133 tip CAS. This is plan_id schedule vs capture_1 PK",
        this_is="schedule records n-of-m; first capture PK installment_id",
        seed="schedule plan + first capture",
        first_apply="plan scheduled today",
        plan_change="schedule records; capture PK each installment_id",
        step_note="Plan-day 6–7; PK 8–11; second plan 12–13.",
        **_paths("inst_pl"),
        table="till_inst_pl",
        pk="installment_id",
        rg="installment.schedule|first_capture|n_of_m|plan_id",
        rg_obs=_rg_obs("inst_pl", "sched_inst", "cap_first", "test_sched_not_capture_double"),
        test_name="sched-not-capture-double test",
        surface_read="installment schedule plus first capture",
        skip_pred="this plan already scheduled today",
        verb="capture",
        skip_label="plan-scheduled-today skip",
        src_body=_src,
        hook_body="def cap_first(plan_id, cents):\n    capture_pay(plan_id, cents)\n",
        test_body=(
            "def test_sched_not_capture_double():\n"
            '    sched_inst(pl("pl_1", n=3, each=2000))\n'
            '    sched_inst(pl("pl_1", n=3, each=2000))\n'
            '    cap_first("pl_1", 2000)\n'
            '    assert captured_cents("pl_1") == 2000 and remaining("pl_1") == 4000 and inst_rows("in_1") == 1\n'
            "\n"
            "def test_second_plan():\n"
            '    sched_inst(pl("pl_a", n=2, each=50))\n'
            '    cap_first("pl_a", 50)\n'
            '    sched_inst(pl("pl_b", n=2, each=20))\n'
            '    cap_first("pl_b", 20)\n'
            '    assert captured_cents("pl_a") == 50 and captured_cents("pl_b") == 20\n'
        ),
        obs3="schedule captures full plan",
        obs4="schedule records; first capture PK one installment",
        obs5="captured 2000 remain 4000; second plan adds",
        fail_obs="FAILED test_sched_not_capture_double - captured 6000 or 8000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not scheduled_today(ev["plan_id"]):\n        capture_pay(ev["plan_id"], ev["cents"])',
        obs7="first capture still extra; new plan same day dropped.",
        still_fail_obs="FAILED test_sched_not_capture_double - schedule captured full\n1 failed, 1 passed",
        rewrite_src=(
            "def sched_inst(ev):\n"
            "    if not claim_plan(ev['plan_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_plan(ev["plan_id"], n=ev["n"], each=ev["each"])\n'
            '    return {"ok": True, "scheduled": True}\n'
        ),
        rewrite_src_obs="claim plan_id stores schedule",
        rewrite_hook=(
            "def cap_first(plan_id, cents):\n"
            "    iid = inst_id(plan_id, seq=1)\n"
            "    if not claim_inst(iid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    capture_pay(iid, cents, plan=plan_id, seq=1)\n"
            '    return {"ok": True}\n'
        ),
        obs9="first capture claims installment_id seq 1.",
        rewrite_hook_obs="PK installment_id",
        ddl=_ddl("till_inst_pl", "installment_id", "  plan_id text NOT NULL,\n  seq int NOT NULL,\n  UNIQUE (plan_id, seq)"),
        ddl_obs="PK installment_id",
        test2_body=(
            "def test_second_plan():\n"
            '    sched_inst(pl("pl_a", n=2, each=50))\n'
            '    cap_first("pl_a", 50)\n'
            '    sched_inst(pl("pl_b", n=2, each=20))\n'
            '    cap_first("pl_b", 20)\n'
            '    assert captured_cents("pl_a") == 50 and captured_cents("pl_b") == 20\n'
        ),
        psql_rows="in_1\nin_a\nin_b",
        residual="seq 2 capture",
        grep_pat="seq=1",
        grep_obs="src/inst_pl.py: first seq only; no seq 2",
        goal="till-inst schedule captured full plan. Schedule records; first PK. Gate: tests/test_inst_pl.py.",
        plan="Skip capture if this plan already scheduled today.",
        outcome="Schedule captured full. Plan-day skip left full capture. Plan change: store plan; first PK. Tests 2/2 + second plan + suite 8/8.",
    ),
    _fail(
        slug="late-installment-after-close",
        surfaces="late installment capture vs closed plan",
        avoided="r142 schedule vs first; r133 tip after batch. This is seq after plan close",
        this_is="close PK plan_id; late seq blocked",
        seed="close plan then late seq 2",
        first_apply="plan closed today",
        plan_change="close blocks remaining seq; reopen is handoff",
        step_note="Close-day 6–7; PK 8–11; second 12–13; reopen xfail 15–17.",
        next_note="Unused: late seq after close should reopen plan. Avoid plan-closed-today skip.",
        **_paths("inst_cl", fail=True),
        table="till_inst_cl",
        pk="plan_id",
        rg="plan.close|late_seq|remaining_void",
        rg_obs=_rg_obs("inst_cl", "close_pl", "late_seq", "test_close_not_late_seq"),
        test_name="close-not-late-seq test",
        surface_read="plan close plus late installment",
        skip_pred="this plan already closed today",
        verb="close",
        skip_label="plan-closed-today skip",
        src_body=_naive("close_pl", 'capture_pay(ev["plan_id"], ev.get("cents", 0))', "counted every plan close")[0],
        hook_body="def late_seq(plan_id, seq, cents):\n    capture_pay(plan_id, cents)\n",
        test_body=(
            "def test_close_not_late_seq():\n"
            '    sched_and_first("pl_1", n=3, each=2000)\n'
            '    close_pl(cp("pl_1"))\n'
            '    close_pl(cp("pl_1"))\n'
            '    late_seq("pl_1", 2, 2000)\n'
            '    assert captured_cents("pl_1") == 2000 and closed("pl_1") and inst_rows("pl_1") == 1\n'
            "\n"
            "def test_second_plan():\n"
            '    sched_and_first("pl_a", n=2, each=50)\n'
            '    close_pl(cp("pl_a"))\n'
            '    sched_and_first("pl_b", n=2, each=20)\n'
            '    close_pl(cp("pl_b"))\n'
            '    assert closed("pl_a") and closed("pl_b")\n'
        ),
        test_body_short="same — close PK; late seq blocked",
        obs3="close and late seq both capture",
        obs4="close PK; late blocked",
        obs5="captured stays 2000; second plan closes",
        fail_obs="FAILED test_close_not_late_seq - captured 4000 == 2000\n1 failed, 1 passed",
        skip_old=_naive("close_pl", 'capture_pay(ev["plan_id"], ev.get("cents", 0))', "counted every plan close")[1],
        skip_new='    if not closed_today(ev["plan_id"]):\n        capture_pay(ev["plan_id"], ev.get("cents", 0))',
        obs7="second plan ok; hides late block.",
        still_fail_obs="FAILED if late seq captured 2000 after close\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def close_pl(ev):\n"
            "    if not claim_close(ev['plan_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_closed_plan(ev["plan_id"])\n'
            '    return {"ok": True, "closed": True}\n'
        ),
        rewrite_src_obs="claim plan_id closes; no capture",
        rewrite_hook=(
            "def late_seq(plan_id, seq, cents):\n"
            "    if closed_plan(plan_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    iid = inst_id(plan_id, seq)\n"
            "    if not claim_inst2(iid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    capture_pay(iid, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="late seq blocked if closed",
        ddl=_ddl("till_inst_cl", "plan_id", "  closed bool NOT NULL DEFAULT true"),
        ddl_obs="PK plan_id",
        test2_body=(
            "def test_second_plan():\n"
            '    sched_and_first("pl_a", n=2, each=50)\n'
            '    close_pl(cp("pl_a"))\n'
            '    sched_and_first("pl_b", n=2, each=20)\n'
            '    close_pl(cp("pl_b"))\n'
            '    assert closed("pl_a") and closed("pl_b")\n'
        ),
        xfail_label="late seq after close should reopen",
        xfail_body=(
            "def test_late_reopens_plan():\n"
            '    sched_and_first("pl_p", n=3, each=2000)\n'
            '    close_pl(cp("pl_p"))\n'
            '    late_seq("pl_p", 2, 2000)\n'
            '    assert captured_cents("pl_p") == 4000 and not closed("pl_p")\n'
        ),
        xfail_fail_obs="FAILED test_late_reopens_plan - blocked; still closed\n1 failed",
        xfail_old="def test_late_reopens_plan():",
        xfail_new='@pytest.mark.xfail(reason="handoff: late installment after close must reopen plan", strict=True)\ndef test_late_reopens_plan():',
        xfail_patch_obs="xfailed late reopen plan",
        goal="till-inst-cl late seq captured after close. Close PK blocks seq. Gate: tests/test_inst_cl.py.",
        plan="Skip close if this plan already closed today.",
        outcome="Late seq captured. Close-day skip hid block. Plan change: close PK; late refuses. Primary+second pass. Partial: reopen xfail handoff.",
    ),
)

# r143 delayed funding vs instant payout / instant after delayed
_src, _skip = _naive(
    "fund_delay",
    'credit_avail(ev["charge_id"], ev["cents"])',
    "counted every delayed fund",
)
pair(
    _ok(
        slug="delayed-funding-vs-instant",
        surfaces="delayed funding release vs instant payout election",
        avoided="r138 hold-to-available; r144 will be retrieval. This is T+2 fund vs instant fee",
        this_is="delay PK funds T+2; instant is a separate election that does not double-fund",
        seed="delayed fund + instant election same charge",
        first_apply="charge funded today",
        plan_change="delay claims fund_id T+2; instant records election only",
        step_note="Charge-day 6–7; PK 8–11; second charge 12–13.",
        **_paths("dly_fund"),
        table="till_dly_fund",
        pk="fund_id",
        rg="delayed.funding|instant.payout|tplus2|election",
        rg_obs=_rg_obs("dly_fund", "fund_delay", "elect_inst", "test_delay_not_instant_double"),
        test_name="delay-not-instant-double test",
        surface_read="delayed funding plus instant election",
        skip_pred="this charge already funded today",
        verb="fund",
        skip_label="charge-funded-today skip",
        src_body=_src,
        hook_body="def elect_inst(charge_id, cents):\n    credit_avail(charge_id, cents)\n",
        test_body=(
            "def test_delay_not_instant_double():\n"
            '    fund_delay(fd("fn_1", charge="ch_1", cents=5000, t="T+2"))\n'
            '    fund_delay(fd("fn_1", charge="ch_1", cents=5000, t="T+2"))\n'
            '    elect_inst("ch_1", 5000)\n'
            '    assert avail_cents("m_1") == 0 and pending_cents("m_1") == 5000 and instant("ch_1") and fund_rows("fn_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    fund_delay(fd("fn_a", charge="ch_a", cents=100, t="T+2"))\n'
            '    fund_delay(fd("fn_b", charge="ch_b", cents=40, t="T+2"))\n'
            '    assert pending_cents("m_a") == 100 and pending_cents("m_b") == 40\n'
        ),
        obs3="delay and instant both credit available now",
        obs4="delay pending T+2; instant records election",
        obs5="avail 0 pending 5000; second charge adds",
        fail_obs="FAILED test_delay_not_instant_double - avail 5000 or 10000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not funded_today(ev["charge_id"]):\n        credit_avail(ev["charge_id"], ev["cents"])',
        obs7="instant still credits now; new charge same day dropped.",
        still_fail_obs="FAILED test_delay_not_instant_double - instant credited avail now\n1 failed, 1 passed",
        rewrite_src=(
            "def fund_delay(ev):\n"
            "    if not claim_fund(ev['fund_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_pending(merch_of_ch(ev["charge_id"]), ev["cents"], when=ev["t"], fund=ev["fund_id"])\n'
            '    return {"ok": True, "pending": True}\n'
        ),
        rewrite_src_obs="claim fund_id pending T+2",
        rewrite_hook=(
            "def elect_inst(charge_id, cents):\n"
            "    if not claim_elect(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    flag_instant(charge_id)\n"
            '    return {"ok": True, "elected": True}\n'
        ),
        obs9="instant election flags; does not fund.",
        rewrite_hook_obs="election only",
        ddl=_ddl("till_dly_fund", "fund_id", "  charge_id text UNIQUE,\n  instant bool NOT NULL DEFAULT false"),
        ddl_obs="PK fund_id",
        test2_body=(
            "def test_second_charge():\n"
            '    fund_delay(fd("fn_a", charge="ch_a", cents=100, t="T+2"))\n'
            '    fund_delay(fd("fn_b", charge="ch_b", cents=40, t="T+2"))\n'
            '    assert pending_cents("m_a") == 100 and pending_cents("m_b") == 40\n'
        ),
        psql_rows="fn_1\nfn_a\nfn_b",
        residual="instant fee debit",
        grep_pat="flag_instant",
        grep_obs="src/dly_fund.py: election flag; no instant fee",
        goal="till-dly delay and instant both credited now. Delay pending; instant elects. Gate: tests/test_dly_fund.py.",
        plan="Skip fund if this charge already funded today.",
        outcome="Delay+instant credited now. Charge-day skip left instant as credit. Plan change: pending T+2; elect flag. Tests 2/2 + second charge + suite 8/8.",
    ),
    _fail(
        slug="instant-after-delayed-fund",
        surfaces="instant payout after delayed fund already pending",
        avoided="r143 delay vs instant elect; r138 h2a. This is instant after pending must not double",
        this_is="instant after delay accelerates pending; does not extra-credit",
        seed="delay pending then instant accelerate",
        first_apply="instant sent today",
        plan_change="accelerate moves pending→avail; no extra",
        step_note="Instant-day 6–7; PK 8–11; second 12–13; fee xfail 15–17.",
        next_note="Unused: instant accelerate should take fee. Avoid instant-sent-today skip.",
        **_paths("inst_acc", fail=True),
        table="till_inst_acc",
        pk="accel_id",
        rg="instant.accelerate|pending_to_avail|instant_fee",
        rg_obs=_rg_obs("inst_acc", "accel", "already_delay", "test_accel_not_extra"),
        test_name="accel-not-extra test",
        surface_read="instant accelerate plus delayed pending",
        skip_pred="this charge already instant-sent today",
        verb="accelerate",
        skip_label="instant-sent-today skip",
        src_body=_naive("accel", 'credit_avail(ev["charge_id"], ev["cents"])', "counted every instant accel")[0],
        hook_body="def already_delay(charge_id, cents):\n    credit_pending(charge_id, cents)\n",
        test_body=(
            "def test_accel_not_extra():\n"
            '    already_delay("ch_1", 5000)\n'
            '    accel(ac("ac_1", charge="ch_1", cents=5000))\n'
            '    accel(ac("ac_1", charge="ch_1", cents=5000))\n'
            '    assert avail_cents("m_1") == 5000 and pending_cents("m_1") == 0 and acc_rows("ac_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    already_delay("ch_a", 100)\n'
            '    accel(ac("ac_a", charge="ch_a", cents=100))\n'
            '    already_delay("ch_b", 40)\n'
            '    accel(ac("ac_b", charge="ch_b", cents=40))\n'
            '    assert avail_cents("m_a") == 100 and avail_cents("m_b") == 40\n'
        ),
        test_body_short="same — accelerate moves pending; no extra",
        obs3="accel extra-credits available",
        obs4="accel moves pending→avail",
        obs5="avail 5000 pending 0; second charge adds",
        fail_obs="FAILED test_accel_not_extra - avail 10000 or pending 5000\n1 failed, 1 passed",
        skip_old=_naive("accel", 'credit_avail(ev["charge_id"], ev["cents"])', "counted every instant accel")[1],
        skip_new='    if not instant_today(ev["charge_id"]):\n        credit_avail(ev["charge_id"], ev["cents"])',
        obs7="second charge ok; hides move.",
        still_fail_obs="FAILED if accel extra-credited (avail 10000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def accel(ev):\n"
            "    if not claim_acc(ev['accel_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    move_pending_to_avail(hold_of(ev["charge_id"]), ev["cents"])\n'
            '    return {"ok": True, "accelerated": True}\n'
        ),
        rewrite_src_obs="claim accel_id moves pending",
        rewrite_hook=(
            "def already_delay(charge_id, cents):\n"
            "    if not claim_fund2(fund_id(charge_id)):\n"
            "        return existing_fund(charge_id)\n"
            "    credit_pending(merch_of_ch(charge_id), cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="delay pending first",
        ddl=_ddl("till_inst_acc", "accel_id", "  charge_id text UNIQUE"),
        ddl_obs="PK accel_id",
        test2_body=(
            "def test_second_charge():\n"
            '    already_delay("ch_a", 100)\n'
            '    accel(ac("ac_a", charge="ch_a", cents=100))\n'
            '    already_delay("ch_b", 40)\n'
            '    accel(ac("ac_b", charge="ch_b", cents=40))\n'
            '    assert avail_cents("m_a") == 100 and avail_cents("m_b") == 40\n'
        ),
        xfail_label="instant accelerate should take fee",
        xfail_body=(
            "def test_accel_fee():\n"
            '    already_delay("ch_p", 5000)\n'
            '    accel(ac("ac_p", charge="ch_p", cents=5000))\n'
            '    assert avail_cents("m_p") == 4925 and fee_cents("ac_p") == 75\n'
        ),
        xfail_fail_obs="FAILED test_accel_fee - avail 5000; no instant fee\n1 failed",
        xfail_old="def test_accel_fee():",
        xfail_new='@pytest.mark.xfail(reason="handoff: instant accelerate must take fee from moved amount", strict=True)\ndef test_accel_fee():',
        xfail_patch_obs="xfailed accel fee",
        goal="till-acc instant extra-credited after delay. Accel moves pending. Gate: tests/test_inst_acc.py.",
        plan="Skip accelerate if this charge already instant-sent today.",
        outcome="Accel extra-credited. Instant-day skip hid move. Plan change: move pending. Primary+second pass. Partial: fee xfail handoff.",
    ),
)

# r144 retrieval request vs chargeback / retrieval after cb
_src, _skip = _naive(
    "open_rr",
    'hold_pay(ev["payment_id"], ev["cents"])',
    "counted every retrieval request",
)
pair(
    _ok(
        slug="retrieval-vs-chargeback",
        surfaces="retrieval request hold vs chargeback debit",
        avoided="r126 cb vs refund; r139 represent. This is retrieval_id hold vs dispute debit",
        this_is="RR records request; CB PK debit only if RR not already charged",
        seed="open retrieval + chargeback same payment",
        first_apply="retrieval opened today",
        plan_change="RR records; CB PK debit; RR does not debit",
        step_note="Payment-day 6–7; PK 8–11; second payment 12–13.",
        **_paths("retr_cb"),
        table="till_retr_cb",
        pk="dispute_id",
        rg="retrieval.request|chargeback.debit|rr_id|fulfillment",
        rg_obs=_rg_obs("retr_cb", "open_rr", "open_cb2", "test_rr_not_cb_double"),
        test_name="rr-not-cb-double test",
        surface_read="retrieval request plus chargeback",
        skip_pred="this payment already retrieval-opened today",
        verb="hold",
        skip_label="retrieval-opened-today skip",
        src_body=_src,
        hook_body="def open_cb2(payment_id, cents):\n    hold_pay(payment_id, cents)\n",
        test_body=(
            "def test_rr_not_cb_double():\n"
            '    open_rr(rr("rr_1", payment="pay_1", cents=5000))\n'
            '    open_rr(rr("rr_1", payment="pay_1", cents=5000))\n'
            '    open_cb2("pay_1", 5000)\n'
            '    assert requested("rr_1") and debit_cents("pay_1") == 5000 and cb_rows("dp_1") == 1\n'
            "\n"
            "def test_second_payment():\n"
            '    open_rr(rr("rr_a", payment="pay_a", cents=100))\n'
            '    open_cb2("pay_a", 100)\n'
            '    open_rr(rr("rr_b", payment="pay_b", cents=40))\n'
            '    open_cb2("pay_b", 40)\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        obs3="RR and CB both hold/debit",
        obs4="RR records; CB debit PK",
        obs5="debit once; RR no extra; second payment adds",
        fail_obs="FAILED test_rr_not_cb_double - debit 10000 or 15000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not rr_today(ev["payment_id"]):\n        hold_pay(ev["payment_id"], ev["cents"])',
        obs7="CB still extra-debits; new payment same day dropped.",
        still_fail_obs="FAILED test_rr_not_cb_double - RR debited or CB extra\n1 failed, 1 passed",
        rewrite_src=(
            "def open_rr(ev):\n"
            "    if not claim_rr(ev['rr_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_rr(ev["payment_id"], ev["rr_id"])\n'
            '    return {"ok": True, "requested": True}\n'
        ),
        rewrite_src_obs="claim rr_id records; no debit",
        rewrite_hook=(
            "def open_cb2(payment_id, cents):\n"
            "    did = dp_id(payment_id)\n"
            "    if not claim_dp2(did):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_pay(payment_id, cents, dispute=did)\n"
            '    return {"ok": True}\n'
        ),
        obs9="CB claims dispute_id debit.",
        rewrite_hook_obs="PK dispute_id",
        ddl=_ddl("till_retr_cb", "dispute_id", "  rr_id text UNIQUE,\n  payment_id text NOT NULL"),
        ddl_obs="PK dispute_id",
        test2_body=(
            "def test_second_payment():\n"
            '    open_rr(rr("rr_a", payment="pay_a", cents=100))\n'
            '    open_cb2("pay_a", 100)\n'
            '    open_rr(rr("rr_b", payment="pay_b", cents=40))\n'
            '    open_cb2("pay_b", 40)\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        psql_rows="dp_1\ndp_a\ndp_b",
        residual="RR fulfilled after CB",
        grep_pat="store_rr",
        grep_obs="src/retr_cb.py: RR records; no fulfill CAS",
        goal="till-rr RR and CB both debited. RR records; CB PK. Gate: tests/test_retr_cb.py.",
        plan="Skip hold if this payment already retrieval-opened today.",
        outcome="RR+CB double-debited. Payment-day skip left RR as hold. Plan change: RR record; CB PK. Tests 2/2 + second payment + suite 8/8.",
    ),
    _fail(
        slug="retrieval-after-chargeback",
        surfaces="retrieval request vs already-debited chargeback",
        avoided="r144 RR vs CB; r126 open vs refund. This is RR after CB is evidence-only",
        this_is="RR after CB records; does not second-debit",
        seed="CB debit then retrieval",
        first_apply="retrieval after CB today",
        plan_change="late RR records; debit stays once",
        step_note="RR-day 6–7; PK 8–11; second 12–13; fulfill xfail 15–17.",
        next_note="Unused: RR fulfill after CB should reverse debit. Avoid retrieval-after-cb-today skip.",
        **_paths("retr_late", fail=True),
        table="till_retr_late",
        pk="rr_id",
        rg="retrieval.after_cb|evidence_only|fulfill_reverse",
        rg_obs=_rg_obs("retr_late", "late_rr", "already_cb", "test_late_rr_not_debit"),
        test_name="late-rr-not-debit test",
        surface_read="retrieval after chargeback",
        skip_pred="this retrieval already opened after CB today",
        verb="record",
        skip_label="retrieval-after-cb-today skip",
        src_body=_naive("late_rr", 'hold_pay(ev["payment_id"], ev["cents"])', "counted every late retrieval")[0],
        hook_body="def already_cb(payment_id, cents):\n    debit_pay(payment_id, cents)\n",
        test_body=(
            "def test_late_rr_not_debit():\n"
            '    already_cb("pay_1", 5000)\n'
            '    late_rr(rr("rr_1", payment="pay_1", cents=5000))\n'
            '    late_rr(rr("rr_1", payment="pay_1", cents=5000))\n'
            '    assert debit_cents("pay_1") == 5000 and requested("rr_1") and rr_rows("rr_1") == 1\n'
            "\n"
            "def test_second_rr():\n"
            '    already_cb("pay_a", 100)\n'
            '    late_rr(rr("rr_a", payment="pay_a", cents=100))\n'
            '    already_cb("pay_b", 40)\n'
            '    late_rr(rr("rr_b", payment="pay_b", cents=40))\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        test_body_short="same — late RR records; debit stays",
        obs3="late RR second-debits",
        obs4="late RR records only",
        obs5="debit 5000; RR once; second payment independent",
        fail_obs="FAILED test_late_rr_not_debit - debit 10000 == 5000\n1 failed, 1 passed",
        skip_old=_naive("late_rr", 'hold_pay(ev["payment_id"], ev["cents"])', "counted every late retrieval")[1],
        skip_new='    if not rr_today(ev["payment_id"]):\n        hold_pay(ev["payment_id"], ev["cents"])',
        obs7="second RR ok; hides record-only.",
        still_fail_obs="FAILED if late RR extra-debited\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_rr(ev):\n"
            "    if not claim_rr2(ev['rr_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_rr(ev["payment_id"], ev["rr_id"])\n'
            '    return {"ok": True, "requested": True}\n'
        ),
        rewrite_src_obs="claim rr_id records after CB",
        rewrite_hook=(
            "def already_cb(payment_id, cents):\n"
            "    did = dp_id(payment_id)\n"
            "    if not claim_dp3(did):\n"
            "        return existing_dp(did)\n"
            "    debit_pay(payment_id, cents, dispute=did)\n"
            "    return did\n"
        ),
        rewrite_hook_obs="CB debit first",
        ddl=_ddl("till_retr_late", "rr_id", "  payment_id text NOT NULL"),
        ddl_obs="PK rr_id",
        test2_body=(
            "def test_second_rr():\n"
            '    already_cb("pay_a", 100)\n'
            '    late_rr(rr("rr_a", payment="pay_a", cents=100))\n'
            '    already_cb("pay_b", 40)\n'
            '    late_rr(rr("rr_b", payment="pay_b", cents=40))\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        xfail_label="RR fulfill after CB should reverse debit",
        xfail_body=(
            "def test_rr_fulfill_reverses():\n"
            '    already_cb("pay_p", 5000)\n'
            '    late_rr(rr("rr_p", payment="pay_p", cents=5000))\n'
            '    fulfill_rr("rr_p")\n'
            '    assert debit_cents("pay_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_rr_fulfill_reverses - no fulfill reverse path\n1 failed",
        xfail_old="def test_rr_fulfill_reverses():",
        xfail_new='@pytest.mark.xfail(reason="handoff: RR fulfill after CB must reverse debit", strict=True)\ndef test_rr_fulfill_reverses():',
        xfail_patch_obs="xfailed RR fulfill reverse",
        goal="till-rr-late late retrieval extra-debited. RR records only. Gate: tests/test_retr_late.py.",
        plan="Skip record if this retrieval already opened after CB today.",
        outcome="Late RR extra-debited. RR-day skip hid record-only. Plan change: store RR. Primary+second pass. Partial: fulfill reverse xfail handoff.",
    ),
)

# r145 auth expiry vs capture / capture after expiry
_src, _skip = _naive(
    "expire_auth",
    'release_hold(ev["auth_id"], ev["cents"])',
    "counted every auth expiry",
)
pair(
    _ok(
        slug="auth-expiry-vs-capture",
        surfaces="authorization expiry release vs capture",
        avoided="r84 incremental; r04 auth/capture remaining. This is expiry PK vs capture remaining",
        this_is="expire releases hold; capture PK remaining only if not expired",
        seed="expire auth + capture same auth_id",
        first_apply="auth expired today",
        plan_change="expire PK releases; capture blocked if expired",
        step_note="Auth-day 6–7; PK 8–11; second auth 12–13.",
        **_paths("auth_exp"),
        table="till_auth_exp",
        pk="auth_id",
        rg="auth.expire|capture.remaining|ttl_hours|released_hold",
        rg_obs=_rg_obs("auth_exp", "expire_auth", "cap_auth", "test_expire_not_capture"),
        test_name="expire-not-capture test",
        surface_read="auth expiry plus capture",
        skip_pred="this auth already expired today",
        verb="release",
        skip_label="auth-expired-today skip",
        src_body=_src,
        hook_body="def cap_auth(auth_id, cents):\n    capture_pay(auth_id, cents)\n",
        test_body=(
            "def test_expire_not_capture():\n"
            '    hold_auth("au_1", 5000)\n'
            '    expire_auth(ex("au_1", cents=5000))\n'
            '    expire_auth(ex("au_1", cents=5000))\n'
            '    cap_auth("au_1", 5000)\n'
            '    assert hold_cents("au_1") == 0 and captured_cents("au_1") == 0 and exp_rows("au_1") == 1\n'
            "\n"
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    cap_auth("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    cap_auth("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        obs3="expire and capture both move funds",
        obs4="expire releases; capture blocked",
        obs5="hold 0 captured 0; live auths capture",
        fail_obs="FAILED test_expire_not_capture - captured 5000 == 0 or hold leftover\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not expired_today(ev["auth_id"]):\n        release_hold(ev["auth_id"], ev["cents"])',
        obs7="capture still captures expired; new auth same day dropped.",
        still_fail_obs="FAILED test_expire_not_capture - capture of expired succeeded\n1 failed, 1 passed",
        rewrite_src=(
            "def expire_auth(ev):\n"
            "    if not claim_exp_au(ev['auth_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    release_hold(ev["auth_id"], ev["cents"])\n'
            '    mark_expired_auth(ev["auth_id"])\n'
            '    return {"ok": True, "expired": True}\n'
        ),
        rewrite_src_obs="claim auth_id expires and releases",
        rewrite_hook=(
            "def cap_auth(auth_id, cents):\n"
            "    if expired_auth(auth_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_cap_au(auth_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    capture_pay(auth_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        obs9="capture blocked if expired.",
        rewrite_hook_obs="capture PK if live",
        ddl=_ddl("till_auth_exp", "auth_id", "  expired bool NOT NULL DEFAULT false"),
        ddl_obs="PK auth_id",
        test2_body=(
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    cap_auth("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    cap_auth("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        psql_rows="au_1\nau_a\nau_b",
        residual="reauth after expiry",
        grep_pat="expired_auth",
        grep_obs="src/auth_exp.py: expire blocks capture; no reauth",
        goal="till-auth-exp expire and capture both moved. Expire PK; capture blocked. Gate: tests/test_auth_exp.py.",
        plan="Skip release if this auth already expired today.",
        outcome="Expire+capture both moved. Auth-day skip left capture of expired. Plan change: expire PK; capture refuses. Tests 2/2 + second auth + suite 8/8.",
    ),
    _fail(
        slug="capture-after-auth-expiry",
        surfaces="late capture vs already-expired authorization",
        avoided="r145 expire vs capture; r04 remaining. This is merchant override after expiry",
        this_is="late capture after expiry blocked; force-reauth handoff",
        seed="expire then late capture",
        first_apply="late capture today",
        plan_change="late capture blocked; force-reauth is handoff",
        step_note="Late-day 6–7; PK 8–11; second 12–13; force-reauth xfail 15–17.",
        next_note="Unused: force capture after expiry. Avoid late-capture-today skip.",
        **_paths("auth_late", fail=True),
        table="till_auth_late",
        pk="capture_id",
        rg="late.capture|after_expiry|force_reauth",
        rg_obs=_rg_obs("auth_late", "late_cap", "expired_first", "test_late_cap_blocked"),
        test_name="late-cap-blocked test",
        surface_read="late capture plus expired auth",
        skip_pred="this late capture already tried today",
        verb="capture",
        skip_label="late-capture-today skip",
        src_body=_naive("late_cap", 'capture_pay(ev["auth_id"], ev["cents"])', "counted every late capture")[0],
        hook_body="def expired_first(auth_id, cents):\n    release_hold(auth_id, cents)\n    mark_expired_auth(auth_id)\n",
        test_body=(
            "def test_late_cap_blocked():\n"
            '    hold_auth("au_1", 5000)\n'
            '    expired_first("au_1", 5000)\n'
            '    late_cap(lc("c_1", auth="au_1", cents=5000))\n'
            '    late_cap(lc("c_1", auth="au_1", cents=5000))\n'
            '    assert captured_cents("au_1") == 0 and expired_auth("au_1") and cap_rows("c_1") == 1\n'
            "\n"
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    capture_pay("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    capture_pay("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        test_body_short="same — late capture blocked after expiry",
        obs3="late capture still captures expired",
        obs4="late capture blocked",
        obs5="captured 0; live auths capture",
        fail_obs="FAILED test_late_cap_blocked - captured 5000 == 0\n1 failed, 1 passed",
        skip_old=_naive("late_cap", 'capture_pay(ev["auth_id"], ev["cents"])', "counted every late capture")[1],
        skip_new='    if not late_today(ev["auth_id"]):\n        capture_pay(ev["auth_id"], ev["cents"])',
        obs7="second auth ok; hides block.",
        still_fail_obs="FAILED if late capture of expired succeeded\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_cap(ev):\n"
            "    if expired_auth(ev['auth_id']):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_late_cap(ev['capture_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    capture_pay(ev["auth_id"], ev["cents"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="late capture blocked if expired",
        rewrite_hook=(
            "def expired_first(auth_id, cents):\n"
            "    if not claim_exp_au2(auth_id):\n"
            "        return existing_au(auth_id)\n"
            "    release_hold(auth_id, cents)\n"
            "    mark_expired_auth(auth_id)\n"
            "    return auth_id\n"
        ),
        rewrite_hook_obs="expire first",
        ddl=_ddl("till_auth_late", "capture_id", "  auth_id text NOT NULL,\n  blocked bool NOT NULL DEFAULT false"),
        ddl_obs="PK capture_id",
        test2_body=(
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    capture_pay("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    capture_pay("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        xfail_label="force capture after expiry",
        xfail_body=(
            "def test_force_reauth_capture():\n"
            '    hold_auth("au_p", 5000)\n'
            '    expired_first("au_p", 5000)\n'
            '    late_cap(lc("c_p", auth="au_p", cents=5000, force=True))\n'
            '    assert captured_cents("au_p") == 5000\n'
        ),
        xfail_fail_obs="FAILED test_force_reauth_capture - blocked; no force path\n1 failed",
        xfail_old="def test_force_reauth_capture():",
        xfail_new='@pytest.mark.xfail(reason="handoff: force capture after expiry must reauth", strict=True)\ndef test_force_reauth_capture():',
        xfail_patch_obs="xfailed force reauth capture",
        goal="till-auth-late late capture of expired succeeded. Late blocked. Gate: tests/test_auth_late.py.",
        plan="Skip capture if this late capture already tried today.",
        outcome="Late capture of expired. Late-day skip hid block. Plan change: refuse expired. Primary+second pass. Partial: force-reauth xfail handoff.",
    ),
)

# r146 partial capture vs remaining void / void after full capture
_src, _skip = _naive(
    "part_cap",
    'capture_pay(ev["auth_id"], ev["cents"])',
    "counted every partial capture",
)
pair(
    _ok(
        slug="partial-capture-vs-void-rest",
        surfaces="partial capture vs remaining auth void",
        avoided="r145 expiry vs capture; r04 remaining. This is capture_id partial + void rest PK",
        this_is="partial capture PK; void remaining does not recapture",
        seed="partial capture + void rest same auth",
        first_apply="auth captured today",
        plan_change="partial PK capture_id; void rest releases leftover",
        step_note="Auth-day 6–7; PK 8–11; second auth 12–13.",
        **_paths("part_void"),
        table="till_part_void",
        pk="capture_id",
        rg="partial.capture|void.remaining|leftover_hold",
        rg_obs=_rg_obs("part_void", "part_cap", "void_rest", "test_partial_not_void_double"),
        test_name="partial-not-void-double test",
        surface_read="partial capture plus remaining void",
        skip_pred="this auth already captured today",
        verb="capture",
        skip_label="auth-captured-today skip",
        src_body=_src,
        hook_body="def void_rest(auth_id, cents):\n    capture_pay(auth_id, cents)\n",
        test_body=(
            "def test_partial_not_void_double():\n"
            '    hold_auth("au_1", 5000)\n'
            '    part_cap(pc("c_1", auth="au_1", cents=3000))\n'
            '    part_cap(pc("c_1", auth="au_1", cents=3000))\n'
            '    void_rest("au_1", 2000)\n'
            '    assert captured_cents("au_1") == 3000 and hold_cents("au_1") == 0 and cap_rows("c_1") == 1\n'
            "\n"
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    part_cap(pc("c_a", auth="au_a", cents=60))\n'
            '    void_rest("au_a", 40)\n'
            '    hold_auth("au_b", 40)\n'
            '    part_cap(pc("c_b", auth="au_b", cents=40))\n'
            '    assert captured_cents("au_a") == 60 and captured_cents("au_b") == 40\n'
        ),
        obs3="void rest recaptures leftover",
        obs4="partial PK; void releases leftover",
        obs5="captured 3000 hold 0; second auth adds",
        fail_obs="FAILED test_partial_not_void_double - captured 5000 or 8000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not captured_today(ev["auth_id"]):\n        capture_pay(ev["auth_id"], ev["cents"])',
        obs7="void still recaptures; new auth same day dropped.",
        still_fail_obs="FAILED test_partial_not_void_double - void recaptured leftover\n1 failed, 1 passed",
        rewrite_src=(
            "def part_cap(ev):\n"
            "    if not claim_pcap(ev['capture_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    capture_pay(ev["auth_id"], ev["cents"], capture=ev["capture_id"])\n'
            '    return {"ok": True, "partial": True}\n'
        ),
        rewrite_src_obs="claim capture_id partial",
        rewrite_hook=(
            "def void_rest(auth_id, cents):\n"
            "    if not claim_void(void_id(auth_id)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    release_hold(auth_id, leftover(auth_id))\n"
            '    return {"ok": True, "voided": True}\n'
        ),
        obs9="void rest releases leftover hold.",
        rewrite_hook_obs="void leftover",
        ddl=_ddl("till_part_void", "capture_id", "  auth_id text NOT NULL,\n  void_id text UNIQUE"),
        ddl_obs="PK capture_id",
        test2_body=(
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    part_cap(pc("c_a", auth="au_a", cents=60))\n'
            '    void_rest("au_a", 40)\n'
            '    hold_auth("au_b", 40)\n'
            '    part_cap(pc("c_b", auth="au_b", cents=40))\n'
            '    assert captured_cents("au_a") == 60 and captured_cents("au_b") == 40\n'
        ),
        psql_rows="c_1\nc_a\nc_b",
        residual="second partial after void",
        grep_pat="leftover",
        grep_obs="src/part_void.py: void leftover; no second partial",
        goal="till-part void rest recaptured leftover. Partial PK; void releases. Gate: tests/test_part_void.py.",
        plan="Skip capture if this auth already captured today.",
        outcome="Void recaptured leftover. Auth-day skip left void as capture. Plan change: partial PK; void releases. Tests 2/2 + second auth + suite 8/8.",
    ),
    _fail(
        slug="void-after-full-capture",
        surfaces="void remaining vs already fully captured auth",
        avoided="r146 partial vs void rest; r41 PI canceled. This is void after full is no-op",
        this_is="void after full capture no-ops; reverse is refund handoff",
        seed="full capture then void rest",
        first_apply="voided today",
        plan_change="void after full no-ops; refund is handoff",
        step_note="Void-day 6–7; PK 8–11; second 12–13; refund xfail 15–17.",
        next_note="Unused: void after full should refund. Avoid voided-today skip.",
        **_paths("void_full", fail=True),
        table="till_void_full",
        pk="void_id",
        rg="void.after_full|already_captured|refund_handoff",
        rg_obs=_rg_obs("void_full", "void_late", "full_cap", "test_void_after_full_noop"),
        test_name="void-after-full-noop test",
        surface_read="void remaining plus full capture",
        skip_pred="this auth already voided today",
        verb="void",
        skip_label="voided-today skip",
        src_body=_naive("void_late", 'release_hold(ev["auth_id"], ev["cents"])', "counted every late void")[0],
        hook_body="def full_cap(auth_id, cents):\n    capture_pay(auth_id, cents)\n",
        test_body=(
            "def test_void_after_full_noop():\n"
            '    hold_auth("au_1", 5000)\n'
            '    full_cap("au_1", 5000)\n'
            '    void_late(vl("v_1", auth="au_1", cents=5000))\n'
            '    void_late(vl("v_1", auth="au_1", cents=5000))\n'
            '    assert captured_cents("au_1") == 5000 and hold_cents("au_1") == 0 and void_rows("v_1") == 1\n'
            "\n"
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    full_cap("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    full_cap("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        test_body_short="same — void after full no-ops",
        obs3="void after full reverses capture",
        obs4="void after full no-ops",
        obs5="captured stays 5000; second auth independent",
        fail_obs="FAILED test_void_after_full_noop - captured 0 == 5000\n1 failed, 1 passed",
        skip_old=_naive("void_late", 'release_hold(ev["auth_id"], ev["cents"])', "counted every late void")[1],
        skip_new='    if not voided_today(ev["auth_id"]):\n        release_hold(ev["auth_id"], ev["cents"])',
        obs7="second auth ok; hides no-op.",
        still_fail_obs="FAILED if void reversed full capture\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def void_late(ev):\n"
            "    if leftover(ev['auth_id']) == 0:\n"
            '        return {"ok": True, "nothing": True}\n'
            "    if not claim_void2(ev['void_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    release_hold(ev['auth_id'], leftover(ev['auth_id']))\n"
            '    return {"ok": True, "voided": True}\n'
        ),
        rewrite_src_obs="void no-ops if leftover 0",
        rewrite_hook=(
            "def full_cap(auth_id, cents):\n"
            "    if not claim_pcap2(cap_id(auth_id)):\n"
            "        return existing_cap(auth_id)\n"
            "    capture_pay(auth_id, cents)\n"
            "    return auth_id\n"
        ),
        rewrite_hook_obs="full capture first",
        ddl=_ddl("till_void_full", "void_id", "  auth_id text NOT NULL,\n  leftover int NOT NULL DEFAULT 0"),
        ddl_obs="PK void_id",
        test2_body=(
            "def test_second_auth():\n"
            '    hold_auth("au_a", 100)\n'
            '    full_cap("au_a", 100)\n'
            '    hold_auth("au_b", 40)\n'
            '    full_cap("au_b", 40)\n'
            '    assert captured_cents("au_a") == 100 and captured_cents("au_b") == 40\n'
        ),
        xfail_label="void after full should refund",
        xfail_body=(
            "def test_void_refunds():\n"
            '    hold_auth("au_p", 5000)\n'
            '    full_cap("au_p", 5000)\n'
            '    void_late(vl("v_p", auth="au_p", cents=5000))\n'
            '    assert captured_cents("au_p") == 0 and refund_cents("au_p") == 5000\n'
        ),
        xfail_fail_obs="FAILED test_void_refunds - no-op; no refund path\n1 failed",
        xfail_old="def test_void_refunds():",
        xfail_new='@pytest.mark.xfail(reason="handoff: void after full capture must issue refund", strict=True)\ndef test_void_refunds():',
        xfail_patch_obs="xfailed void refund",
        goal="till-void-full void reversed full capture. Void no-ops if leftover 0. Gate: tests/test_void_full.py.",
        plan="Skip void if this auth already voided today.",
        outcome="Void reversed capture. Void-day skip hid leftover-0. Plan change: no-op if full. Primary+second pass. Partial: refund xfail handoff.",
    ),
)

# r147 surcharge vs convenience fee / both stacked
_src, _skip = _naive(
    "add_surch",
    'debit_payer(ev["charge_id"], ev["cents"])',
    "counted every surcharge",
)
pair(
    _ok(
        slug="surcharge-vs-convenience-fee",
        surfaces="card surcharge vs convenience fee",
        avoided="r128 platform fee; r140 interchange. This is surcharge_id vs conv_fee_id exclusive",
        this_is="surcharge XOR convenience; never both on same charge",
        seed="surcharge + convenience same charge",
        first_apply="surcharged today",
        plan_change="surcharge PK; conv refused if surcharge claimed",
        step_note="Charge-day 6–7; PK 8–11; second charge 12–13.",
        **_paths("surch_cf"),
        table="till_surch_cf",
        pk="charge_id",
        rg="surcharge|convenience_fee|xor_fee|payer_debit",
        rg_obs=_rg_obs("surch_cf", "add_surch", "add_conv", "test_surch_not_conv_double"),
        test_name="surch-not-conv-double test",
        surface_read="surcharge plus convenience fee",
        skip_pred="this charge already surcharged today",
        verb="debit",
        skip_label="surcharged-today skip",
        src_body=_src,
        hook_body="def add_conv(charge_id, cents):\n    debit_payer(charge_id, cents)\n",
        test_body=(
            "def test_surch_not_conv_double():\n"
            '    add_surch(su("ch_1", cents=150))\n'
            '    add_surch(su("ch_1", cents=150))\n'
            '    add_conv("ch_1", 99)\n'
            '    assert fee_cents("ch_1") == 150 and fee_kind("ch_1") == "surcharge" and fee_rows("ch_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    add_conv("ch_a", 20)\n'
            '    add_surch(su("ch_b", cents=12))\n'
            '    assert fee_cents("ch_a") == 20 and fee_cents("ch_b") == 12\n'
        ),
        obs3="surcharge and conv both debit payer",
        obs4="XOR: surcharge wins; conv refused",
        obs5="fee 150 surcharge; second charge independent kinds",
        fail_obs="FAILED test_surch_not_conv_double - fee 249 or 300\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not surcharged_today(ev["charge_id"]):\n        debit_payer(ev["charge_id"], ev["cents"])',
        obs7="conv still stacks; new charge same day dropped.",
        still_fail_obs="FAILED test_surch_not_conv_double - conv stacked on surcharge\n1 failed, 1 passed",
        rewrite_src=(
            "def add_surch(ev):\n"
            "    if not claim_fee(ev['charge_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_payer(ev["charge_id"], ev["cents"], kind="surcharge")\n'
            '    return {"ok": True, "surcharge": True}\n'
        ),
        rewrite_src_obs="claim charge_id surcharge exclusive",
        rewrite_hook=(
            "def add_conv(charge_id, cents):\n"
            "    if fee_kind(charge_id) == 'surcharge':\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_fee(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_payer(charge_id, cents, kind="convenience")\n'
            '    return {"ok": True}\n'
        ),
        obs9="conv blocked if surcharge claimed.",
        rewrite_hook_obs="XOR fee",
        ddl=_ddl("till_surch_cf", "charge_id", "  kind text NOT NULL,\n  fee_cents int NOT NULL"),
        ddl_obs="PK charge_id",
        test2_body=(
            "def test_second_charge():\n"
            '    add_conv("ch_a", 20)\n'
            '    add_surch(su("ch_b", cents=12))\n'
            '    assert fee_cents("ch_a") == 20 and fee_kind("ch_a") == "convenience"\n'
            '    assert fee_cents("ch_b") == 12 and fee_kind("ch_b") == "surcharge"\n'
        ),
        psql_rows="ch_1\nch_a\nch_b",
        residual="regulated surcharge cap",
        grep_pat="surcharge",
        grep_obs="src/surch_cf.py: XOR fee; no cap check",
        goal="till-surch surcharge and conv both debited. XOR fee. Gate: tests/test_surch_cf.py.",
        plan="Skip debit if this charge already surcharged today.",
        outcome="Surcharge+conv stacked. Charge-day skip left conv extra. Plan change: XOR claim. Tests 2/2 + second charge + suite 8/8.",
    ),
    _fail(
        slug="surcharge-and-conv-stacked",
        surfaces="forced convenience fee vs already-surcharged charge",
        avoided="r147 XOR surcharge; r128 platform fee. This is override stack handoff",
        this_is="forced conv after surcharge blocked; dual-fee is handoff",
        seed="surcharge then force convenience",
        first_apply="conv forced today",
        plan_change="force still blocked; dual-fee policy handoff",
        step_note="Force-day 6–7; PK 8–11; second 12–13; dual-fee xfail 15–17.",
        next_note="Unused: dual surcharge+conv for mixed tender. Avoid conv-forced-today skip.",
        **_paths("surch_stack", fail=True),
        table="till_surch_st",
        pk="force_id",
        rg="force.convenience|dual_fee|mixed_tender",
        rg_obs=_rg_obs("surch_stack", "force_conv", "already_surch", "test_force_conv_blocked"),
        test_name="force-conv-blocked test",
        surface_read="forced convenience plus surcharge",
        skip_pred="this convenience already forced today",
        verb="force",
        skip_label="conv-forced-today skip",
        src_body=_naive("force_conv", 'debit_payer(ev["charge_id"], ev["cents"])', "counted every forced conv")[0],
        hook_body="def already_surch(charge_id, cents):\n    debit_payer(charge_id, cents, kind='surcharge')\n",
        test_body=(
            "def test_force_conv_blocked():\n"
            '    already_surch("ch_1", 150)\n'
            '    force_conv(fc("f_1", charge="ch_1", cents=99))\n'
            '    force_conv(fc("f_1", charge="ch_1", cents=99))\n'
            '    assert fee_cents("ch_1") == 150 and fee_kind("ch_1") == "surcharge" and force_rows("f_1") == 1\n'
            "\n"
            "def test_second_force():\n"
            '    already_surch("ch_a", 20)\n'
            '    already_surch("ch_b", 12)\n'
            '    assert fee_cents("ch_a") == 20 and fee_cents("ch_b") == 12\n'
        ),
        test_body_short="same — force conv blocked after surcharge",
        obs3="force conv stacks on surcharge",
        obs4="force still blocked",
        obs5="fee stays 150 surcharge; second charges independent",
        fail_obs="FAILED test_force_conv_blocked - fee 249 == 150\n1 failed, 1 passed",
        skip_old=_naive("force_conv", 'debit_payer(ev["charge_id"], ev["cents"])', "counted every forced conv")[1],
        skip_new='    if not forced_today(ev["charge_id"]):\n        debit_payer(ev["charge_id"], ev["cents"])',
        obs7="second force ok; hides block.",
        still_fail_obs="FAILED if force stacked 99 on surcharge\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def force_conv(ev):\n"
            "    if fee_kind(ev['charge_id']) == 'surcharge':\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_force(ev['force_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_payer(ev["charge_id"], ev["cents"], kind="convenience")\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="force blocked if surcharge",
        rewrite_hook=(
            "def already_surch(charge_id, cents):\n"
            "    if not claim_fee2(charge_id):\n"
            "        return existing_fee(charge_id)\n"
            "    debit_payer(charge_id, cents, kind='surcharge')\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="surcharge claimed first",
        ddl=_ddl("till_surch_st", "force_id", "  charge_id text NOT NULL,\n  blocked bool NOT NULL DEFAULT true"),
        ddl_obs="PK force_id",
        test2_body=(
            "def test_second_force():\n"
            '    already_surch("ch_a", 20)\n'
            '    already_surch("ch_b", 12)\n'
            '    assert fee_cents("ch_a") == 20 and fee_cents("ch_b") == 12\n'
        ),
        xfail_label="dual surcharge+conv mixed tender",
        xfail_body=(
            "def test_dual_fee_mixed():\n"
            '    already_surch("ch_p", 150)\n'
            '    force_conv(fc("f_p", charge="ch_p", cents=99, mixed=True))\n'
            '    assert fee_cents("ch_p") == 249\n'
        ),
        xfail_fail_obs="FAILED test_dual_fee_mixed - blocked; no mixed path\n1 failed",
        xfail_old="def test_dual_fee_mixed():",
        xfail_new='@pytest.mark.xfail(reason="handoff: mixed-tender dual fee is a policy exception", strict=True)\ndef test_dual_fee_mixed():',
        xfail_patch_obs="xfailed dual fee mixed",
        goal="till-surch-stack force conv stacked. Force blocked. Gate: tests/test_surch_stack.py.",
        plan="Skip force if this convenience already forced today.",
        outcome="Force stacked. Force-day skip hid block. Plan change: still XOR. Primary+second pass. Partial: mixed dual-fee xfail handoff.",
    ),
)

# r148 merchant credit vs debit memo / memo after applied credit
_src, _skip = _naive(
    "issue_mc",
    'credit_merch(ev["memo_id"], ev["cents"])',
    "counted every merchant credit",
)
pair(
    _ok(
        slug="merchant-credit-vs-debit-memo",
        surfaces="merchant credit memo vs debit memo",
        avoided="r137 VAT CN; r17 fee refund. This is credit_id vs debit_id on merchant AR",
        this_is="credit PK credits merch; debit PK offsets credit not extra debit",
        seed="credit memo + debit memo same merchant",
        first_apply="credit issued today",
        plan_change="credit PK; debit offsets remaining credit",
        step_note="Memo-day 6–7; PK 8–11; second memo 12–13.",
        **_paths("mc_dm"),
        table="till_mc_dm",
        pk="credit_id",
        rg="merchant.credit|debit.memo|offset_credit",
        rg_obs=_rg_obs("mc_dm", "issue_mc", "issue_dm", "test_credit_not_debit_double"),
        test_name="credit-not-debit-double test",
        surface_read="merchant credit plus debit memo",
        skip_pred="this merchant already credited today",
        verb="credit",
        skip_label="credit-issued-today skip",
        src_body=_src,
        hook_body="def issue_dm(merchant, cents):\n    credit_merch(merchant, -cents)\n",
        test_body=(
            "def test_credit_not_debit_double():\n"
            '    issue_mc(mc("cr_1", merchant="m_1", cents=5000))\n'
            '    issue_mc(mc("cr_1", merchant="m_1", cents=5000))\n'
            '    issue_dm("m_1", 1200)\n'
            '    assert merch_cents("m_1") == 3800 and credit_cents("cr_1") == 5000 and memo_rows("cr_1") == 1\n'
            "\n"
            "def test_second_credit():\n"
            '    issue_mc(mc("cr_a", merchant="m_a", cents=100))\n'
            '    issue_dm("m_a", 20)\n'
            '    issue_mc(mc("cr_b", merchant="m_b", cents=40))\n'
            '    assert merch_cents("m_a") == 80 and merch_cents("m_b") == 40\n'
        ),
        obs3="credit and debit both credit (sign-blind)",
        obs4="credit PK; debit offsets",
        obs5="merch 3800; credit once; second merchant adds",
        fail_obs="FAILED test_credit_not_debit_double - merch 10000 or 3800*2\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not credited_today(ev["merchant"]):\n        credit_merch(ev["memo_id"], ev["cents"])',
        obs7="debit still sign-blind; new merchant same day dropped.",
        still_fail_obs="FAILED test_credit_not_debit_double - debit did not offset\n1 failed, 1 passed",
        rewrite_src=(
            "def issue_mc(ev):\n"
            "    if not claim_mc(ev['credit_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_merch(ev["merchant"], ev["cents"], credit=ev["credit_id"])\n'
            '    return {"ok": True, "credited": True}\n'
        ),
        rewrite_src_obs="claim credit_id credits merchant",
        rewrite_hook=(
            "def issue_dm(merchant, cents):\n"
            "    did = dm_id(merchant, cents)\n"
            "    if not claim_dm(did):\n"
            '        return {"ok": True, "dup": True}\n'
            "    take = min(cents, credit_bal(merchant))\n"
            "    debit_merch(merchant, take, debit=did)\n"
            '    return {"ok": True, "offset": take}\n'
        ),
        obs9="debit offsets remaining credit.",
        rewrite_hook_obs="PK debit offset",
        ddl=_ddl("till_mc_dm", "credit_id", "  merchant text NOT NULL,\n  debit_id text UNIQUE"),
        ddl_obs="PK credit_id",
        test2_body=(
            "def test_second_credit():\n"
            '    issue_mc(mc("cr_a", merchant="m_a", cents=100))\n'
            '    issue_dm("m_a", 20)\n'
            '    issue_mc(mc("cr_b", merchant="m_b", cents=40))\n'
            '    assert merch_cents("m_a") == 80 and merch_cents("m_b") == 40\n'
        ),
        psql_rows="cr_1\ncr_a\ncr_b",
        residual="debit exceeding credit",
        grep_pat="offset",
        grep_obs="src/mc_dm.py: debit min(credit_bal); no excess receivable",
        goal="till-mc credit and debit both credited. Credit PK; debit offsets. Gate: tests/test_mc_dm.py.",
        plan="Skip credit if this merchant already credited today.",
        outcome="Credit+debit sign-blind. Merchant-day skip left debit. Plan change: credit PK; debit offsets. Tests 2/2 + second credit + suite 8/8.",
    ),
    _fail(
        slug="debit-memo-after-applied-credit",
        surfaces="debit memo vs already-applied (zero remaining) credit",
        avoided="r148 credit vs debit offset; r137 CN after cash. This is debit after applied is receivable",
        this_is="debit after applied credit opens receivable; does not go negative",
        seed="apply credit to invoices then debit memo",
        first_apply="debit memod today",
        plan_change="debit after zero remaining opens recv",
        step_note="Debit-day 6–7; PK 8–11; second 12–13; negative xfail 15–17.",
        next_note="Unused: debit after applied should go negative. Avoid debit-memod-today skip.",
        **_paths("dm_app", fail=True),
        table="till_dm_app",
        pk="debit_id",
        rg="debit.after_applied|zero_remaining|recv_debit",
        rg_obs=_rg_obs("dm_app", "late_dm", "applied_cr", "test_debit_after_applied_recv"),
        test_name="debit-after-applied-recv test",
        surface_read="debit memo plus applied credit",
        skip_pred="this merchant already debit-memod today",
        verb="debit",
        skip_label="debit-memod-today skip",
        src_body=_naive("late_dm", 'debit_merch(ev["merchant"], ev["cents"])', "counted every late debit memo")[0],
        hook_body="def applied_cr(merchant, cents):\n    credit_merch(merchant, cents)\n    apply_to_invoices(merchant, cents)\n",
        test_body=(
            "def test_debit_after_applied_recv():\n"
            '    applied_cr("m_1", 5000)\n'
            '    late_dm(dm("dm_1", merchant="m_1", cents=1200))\n'
            '    late_dm(dm("dm_1", merchant="m_1", cents=1200))\n'
            '    assert merch_cents("m_1") == 0 and recv_cents("m_1") == 1200 and dm_rows("dm_1") == 1\n'
            "\n"
            "def test_second_debit():\n"
            '    applied_cr("m_a", 100)\n'
            '    late_dm(dm("dm_a", merchant="m_a", cents=20))\n'
            '    applied_cr("m_b", 40)\n'
            '    assert recv_cents("m_a") == 20 and merch_cents("m_b") == 0\n'
        ),
        test_body_short="same — debit after applied opens receivable",
        obs3="debit drives merchant negative",
        obs4="debit opens receivable",
        obs5="merch 0 recv 1200; second debit independent",
        fail_obs="FAILED test_debit_after_applied_recv - merch -1200 or recv 0\n1 failed, 1 passed",
        skip_old=_naive("late_dm", 'debit_merch(ev["merchant"], ev["cents"])', "counted every late debit memo")[1],
        skip_new='    if not dm_today(ev["merchant"]):\n        debit_merch(ev["merchant"], ev["cents"])',
        obs7="second debit ok; hides receivable.",
        still_fail_obs="FAILED if debit went negative instead of recv\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_dm(ev):\n"
            "    if not claim_dm2(ev['debit_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    take = min(ev['cents'], credit_bal(ev['merchant']))\n"
            "    if take:\n"
            "        debit_merch(ev['merchant'], take)\n"
            "    extra = ev['cents'] - take\n"
            "    if extra:\n"
            "        open_recv(ev['merchant'], extra, debit=ev['debit_id'])\n"
            '    return {"ok": True, "recv": extra}\n'
        ),
        rewrite_src_obs="claim debit_id; extra opens recv",
        rewrite_hook=(
            "def applied_cr(merchant, cents):\n"
            "    if not claim_mc2(credit_id(merchant, cents)):\n"
            "        return existing_cr(merchant)\n"
            "    credit_merch(merchant, cents)\n"
            "    apply_to_invoices(merchant, cents)\n"
            "    return merchant\n"
        ),
        rewrite_hook_obs="credit applied first",
        ddl=_ddl("till_dm_app", "debit_id", "  merchant text NOT NULL,\n  recv_cents int NOT NULL DEFAULT 0"),
        ddl_obs="PK debit_id",
        test2_body=(
            "def test_second_debit():\n"
            '    applied_cr("m_a", 100)\n'
            '    late_dm(dm("dm_a", merchant="m_a", cents=20))\n'
            '    applied_cr("m_b", 40)\n'
            '    assert recv_cents("m_a") == 20 and merch_cents("m_b") == 0\n'
        ),
        xfail_label="debit after applied should go negative",
        xfail_body=(
            "def test_debit_negative():\n"
            '    applied_cr("m_p", 5000)\n'
            '    late_dm(dm("dm_p", merchant="m_p", cents=1200))\n'
            '    assert merch_cents("m_p") == -1200 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_debit_negative - recv opened; not negative\n1 failed",
        xfail_old="def test_debit_negative():",
        xfail_new='@pytest.mark.xfail(reason="handoff: debit after applied as negative balance vs receivable", strict=True)\ndef test_debit_negative():',
        xfail_patch_obs="xfailed debit negative",
        goal="till-dm debit went negative after applied credit. Extra opens recv. Gate: tests/test_dm_app.py.",
        plan="Skip debit if this merchant already debit-memod today.",
        outcome="Debit went negative. Debit-day skip hid recv. Plan change: extra→recv. Primary+second pass. Partial: negative xfail handoff.",
    ),
)

# r149 suspense vs clear / clear after already allocated
_src, _skip = _naive(
    "park_susp",
    'post_ledger(ev["cash_id"], ev["cents"])',
    "counted every suspense park",
)
pair(
    _ok(
        slug="suspense-vs-clear",
        surfaces="unallocated cash suspense vs clear-to-invoice",
        avoided="r137 VAT cash apply; r136 netting. This is suspense_id park vs clear_id allocate",
        this_is="park PK suspense; clear allocates to invoice not re-post",
        seed="park cash + clear to invoice",
        first_apply="cash parked today",
        plan_change="park suspense PK; clear allocates",
        step_note="Cash-day 6–7; PK 8–11; second cash 12–13.",
        **_paths("susp_cl"),
        table="till_susp_cl",
        pk="cash_id",
        rg="suspense.park|clear.invoice|unallocated|allocate",
        rg_obs=_rg_obs("susp_cl", "park_susp", "clear_inv", "test_park_not_clear_double"),
        test_name="park-not-clear-double test",
        surface_read="suspense park plus clear-to-invoice",
        skip_pred="this cash already parked today",
        verb="post",
        skip_label="cash-parked-today skip",
        src_body=_src,
        hook_body="def clear_inv(cash_id, invoice_id, cents):\n    post_ledger(invoice_id, cents)\n",
        test_body=(
            "def test_park_not_clear_double():\n"
            '    park_susp(pk("ca_1", cents=5000))\n'
            '    park_susp(pk("ca_1", cents=5000))\n'
            '    clear_inv("ca_1", "inv_1", 5000)\n'
            '    assert susp_cents("ca_1") == 0 and ar_cents("inv_1") == 0 and susp_rows("ca_1") == 1\n'
            "\n"
            "def test_second_cash():\n"
            '    park_susp(pk("ca_a", cents=100))\n'
            '    clear_inv("ca_a", "inv_a", 100)\n'
            '    park_susp(pk("ca_b", cents=40))\n'
            '    clear_inv("ca_b", "inv_b", 40)\n'
            '    assert ar_cents("inv_a") == 0 and ar_cents("inv_b") == 0\n'
        ),
        obs3="park and clear both post cash",
        obs4="park suspense; clear allocates",
        obs5="susp 0 AR applied; second cash adds",
        fail_obs="FAILED test_park_not_clear_double - posted twice or AR not applied\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not parked_today(ev["cash_id"]):\n        post_ledger(ev["cash_id"], ev["cents"])',
        obs7="clear still re-posts; new cash same day dropped.",
        still_fail_obs="FAILED test_park_not_clear_double - clear re-posted cash\n1 failed, 1 passed",
        rewrite_src=(
            "def park_susp(ev):\n"
            "    if not claim_cash(ev['cash_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    post_suspense(ev["cash_id"], ev["cents"])\n'
            '    return {"ok": True, "parked": True}\n'
        ),
        rewrite_src_obs="claim cash_id parks suspense",
        rewrite_hook=(
            "def clear_inv(cash_id, invoice_id, cents):\n"
            "    cid = clear_id(cash_id, invoice_id)\n"
            "    if not claim_clear(cid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    move_suspense_to_ar(cash_id, invoice_id, cents)\n"
            '    return {"ok": True, "cleared": True}\n'
        ),
        obs9="clear claims clear_id moves suspense→AR.",
        rewrite_hook_obs="allocate move",
        ddl=_ddl("till_susp_cl", "cash_id", "  susp_cents int NOT NULL,\n  clear_id text UNIQUE"),
        ddl_obs="PK cash_id",
        test2_body=(
            "def test_second_cash():\n"
            '    park_susp(pk("ca_a", cents=100))\n'
            '    clear_inv("ca_a", "inv_a", 100)\n'
            '    park_susp(pk("ca_b", cents=40))\n'
            '    clear_inv("ca_b", "inv_b", 40)\n'
            '    assert ar_cents("inv_a") == 0 and ar_cents("inv_b") == 0\n'
        ),
        psql_rows="ca_1\nca_a\nca_b",
        residual="split clear two invoices",
        grep_pat="move_suspense",
        grep_obs="src/susp_cl.py: move full; no split",
        goal="till-susp park and clear both posted cash. Park then allocate. Gate: tests/test_susp_cl.py.",
        plan="Skip post if this cash already parked today.",
        outcome="Park+clear double-posted. Cash-day skip left clear as post. Plan change: park PK; clear moves. Tests 2/2 + second cash + suite 8/8.",
    ),
    _fail(
        slug="clear-after-already-allocated",
        surfaces="second clear vs already-allocated suspense",
        avoided="r149 park vs clear; r137 cash apply. This is second clear no-ops",
        this_is="second clear after allocated no-ops; split is handoff",
        seed="clear then second clear different invoice",
        first_apply="cleared today",
        plan_change="second clear no-ops; split handoff",
        step_note="Clear-day 6–7; PK 8–11; second 12–13; split xfail 15–17.",
        next_note="Unused: split clear two invoices. Avoid cleared-today skip.",
        **_paths("susp_2nd", fail=True),
        table="till_susp_2nd",
        pk="clear_id",
        rg="second.clear|already_allocated|split_clear",
        rg_obs=_rg_obs("susp_2nd", "clear_2nd", "already_cl", "test_second_clear_noop"),
        test_name="second-clear-noop test",
        surface_read="second clear plus allocated cash",
        skip_pred="this cash already cleared today",
        verb="clear",
        skip_label="cleared-today skip",
        src_body=_naive("clear_2nd", 'post_ledger(ev["invoice_id"], ev["cents"])', "counted every second clear")[0],
        hook_body="def already_cl(cash_id, invoice_id, cents):\n    move_suspense_to_ar(cash_id, invoice_id, cents)\n",
        test_body=(
            "def test_second_clear_noop():\n"
            '    park_and_clear("ca_1", "inv_1", 5000)\n'
            '    clear_2nd(c2("cl_2", cash="ca_1", invoice="inv_2", cents=5000))\n'
            '    clear_2nd(c2("cl_2", cash="ca_1", invoice="inv_2", cents=5000))\n'
            '    assert ar_cents("inv_1") == 0 and ar_cents("inv_2") == 5000 and susp_cents("ca_1") == 0\n'
            "\n"
            "def test_second_cash():\n"
            '    park_and_clear("ca_a", "inv_a", 100)\n'
            '    park_and_clear("ca_b", "inv_b", 40)\n'
            '    assert susp_cents("ca_a") == 0 and susp_cents("ca_b") == 0\n'
        ),
        test_body_short="same — second clear no-ops",
        obs3="second clear posts to inv_2 (double apply)",
        obs4="second clear no-ops; inv_1 stays applied",
        obs5="inv_2 not applied; susp 0; second cash independent",
        fail_obs="FAILED test_second_clear_noop - inv_2 5000 should stay open\n1 failed, 1 passed",
        skip_old=_naive("clear_2nd", 'post_ledger(ev["invoice_id"], ev["cents"])', "counted every second clear")[1],
        skip_new='    if not cleared_today(ev["cash_id"]):\n        post_ledger(ev["invoice_id"], ev["cents"])',
        obs7="second cash ok; hides no-op.",
        still_fail_obs="FAILED if second clear applied inv_2\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def clear_2nd(ev):\n"
            "    if susp_of(ev['cash_id']) == 0:\n"
            '        return {"ok": True, "nothing": True}\n'
            "    if not claim_clear2(ev['clear_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    move_suspense_to_ar(ev['cash_id'], ev['invoice_id'], ev['cents'])\n"
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="second clear no-ops if susp 0",
        rewrite_hook=(
            "def already_cl(cash_id, invoice_id, cents):\n"
            "    if not claim_clear3(clear_id(cash_id, invoice_id)):\n"
            "        return existing_cl(cash_id)\n"
            "    move_suspense_to_ar(cash_id, invoice_id, cents)\n"
            "    return cash_id\n"
        ),
        rewrite_hook_obs="first clear allocates all",
        ddl=_ddl("till_susp_2nd", "clear_id", "  cash_id text NOT NULL,\n  invoice_id text NOT NULL"),
        ddl_obs="PK clear_id",
        test2_body=(
            "def test_second_cash():\n"
            '    park_and_clear("ca_a", "inv_a", 100)\n'
            '    park_and_clear("ca_b", "inv_b", 40)\n'
            '    assert susp_cents("ca_a") == 0 and susp_cents("ca_b") == 0\n'
        ),
        xfail_label="split clear two invoices",
        xfail_body=(
            "def test_split_clear():\n"
            '    park_susp(pk("ca_p", cents=5000))\n'
            '    already_cl("ca_p", "inv_p1", 3000)\n'
            '    clear_2nd(c2("cl_p", cash="ca_p", invoice="inv_p2", cents=2000))\n'
            '    assert ar_cents("inv_p1") == 0 and ar_cents("inv_p2") == 0 and susp_cents("ca_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_split_clear - first clear took all; no split\n1 failed",
        xfail_old="def test_split_clear():",
        xfail_new='@pytest.mark.xfail(reason="handoff: split clear across invoices needs remainder staging", strict=True)\ndef test_split_clear():',
        xfail_patch_obs="xfailed split clear",
        goal="till-susp-2nd second clear applied other invoice. Second no-ops. Gate: tests/test_susp_2nd.py.",
        plan="Skip clear if this cash already cleared today.",
        outcome="Second clear applied inv_2. Clear-day skip hid no-op. Plan change: nothing if susp 0. Primary+second pass. Partial: split xfail handoff.",
    ),
)

# r150 BIN fee vs interchange / BIN after ix
_src, _skip = _naive(
    "post_bin",
    'debit_merch(ev["batch_id"], ev["cents"])',
    "counted every BIN fee",
)
pair(
    _ok(
        slug="bin-fee-vs-interchange",
        surfaces="BIN sponsorship fee vs interchange",
        avoided="r140 ix vs net; r128 platform fee. This is bin_fee_id vs ix_id stacked correctly",
        this_is="BIN PK fee; ix PK fee; deposit nets both",
        seed="BIN fee + interchange same batch",
        first_apply="BIN fee posted today",
        plan_change="BIN and ix are separate PKs; deposit nets sum",
        step_note="Batch-day 6–7; PK 8–11; second batch 12–13.",
        **_paths("bin_ix"),
        table="till_bin_ix",
        pk="bin_fee_id",
        rg="bin.sponsorship|interchange|stacked_fees|net_both",
        rg_obs=_rg_obs("bin_ix", "post_bin", "post_ix2", "test_bin_not_ix_double"),
        test_name="bin-not-ix-double test",
        surface_read="BIN fee plus interchange",
        skip_pred="this batch already BIN-feed today",
        verb="debit",
        skip_label="bin-feed-today skip",
        src_body=_src,
        hook_body="def post_ix2(batch_id, cents):\n    debit_merch(batch_id, cents)\n",
        test_body=(
            "def test_bin_not_ix_double():\n"
            '    post_bin(bf("bf_1", batch="b_1", cents=25))\n'
            '    post_bin(bf("bf_1", batch="b_1", cents=25))\n'
            '    post_ix2("b_1", 200)\n'
            '    net_dep("b_1", 5000)\n'
            '    assert merch_cents("m_1") == 4775 and bin_cents("bf_1") == 25 and ix_cents("b_1") == 200\n'
            "\n"
            "def test_second_batch():\n"
            '    post_bin(bf("bf_a", batch="b_a", cents=2))\n'
            '    post_ix2("b_a", 4)\n'
            '    net_dep("b_a", 100)\n'
            '    post_bin(bf("bf_b", batch="b_b", cents=1))\n'
            '    post_ix2("b_b", 2)\n'
            '    net_dep("b_b", 40)\n'
            '    assert merch_cents("m_a") == 94 and merch_cents("m_b") == 37\n'
        ),
        obs3="BIN and ix both debit as if deposit",
        obs4="BIN PK + ix PK; deposit nets both",
        obs5="merch 4775; second batch nets both",
        fail_obs="FAILED test_bin_not_ix_double - merch 5000 or 4775*2\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not bin_today(ev["batch_id"]):\n        debit_merch(ev["batch_id"], ev["cents"])',
        obs7="ix still hits merch directly; new batch same day dropped.",
        still_fail_obs="FAILED test_bin_not_ix_double - fees not netted into deposit\n1 failed, 1 passed",
        rewrite_src=(
            "def post_bin(ev):\n"
            "    if not claim_bin(ev['bin_fee_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    book_bin(ev["batch_id"], ev["cents"], bin=ev["bin_fee_id"])\n'
            '    return {"ok": True, "bin": True}\n'
        ),
        rewrite_src_obs="claim bin_fee_id books fee",
        rewrite_hook=(
            "def post_ix2(batch_id, cents):\n"
            "    xid = ix_id(batch_id)\n"
            "    if not claim_ix2(xid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    book_ix(batch_id, cents, ix=xid)\n"
            '    return {"ok": True}\n'
            "\n"
            "def net_dep(batch_id, gross):\n"
            "    did = dep_id(batch_id)\n"
            "    if not claim_dep3(did):\n"
            '        return {"ok": True, "dup": True}\n'
            "    net = gross - bin_of(batch_id) - ix_of(batch_id)\n"
            "    credit_merch(merch_of_batch(batch_id), net, deposit=did)\n"
            '    return {"ok": True, "net": net}\n'
        ),
        obs9="ix books; deposit nets BIN+ix.",
        rewrite_hook_obs="stacked fees into net",
        ddl=_ddl("till_bin_ix", "bin_fee_id", "  batch_id text UNIQUE,\n  ix_id text UNIQUE"),
        ddl_obs="PK bin_fee_id",
        test2_body=(
            "def test_second_batch():\n"
            '    post_bin(bf("bf_a", batch="b_a", cents=2))\n'
            '    post_ix2("b_a", 4)\n'
            '    net_dep("b_a", 100)\n'
            '    post_bin(bf("bf_b", batch="b_b", cents=1))\n'
            '    post_ix2("b_b", 2)\n'
            '    net_dep("b_b", 40)\n'
            '    assert merch_cents("m_a") == 94 and merch_cents("m_b") == 37\n'
        ),
        psql_rows="bf_1\nbf_a\nbf_b",
        residual="scheme assessment stacked too",
        grep_pat="bin_of",
        grep_obs="src/bin_ix.py: net = gross-bin-ix; no scheme",
        goal="till-bin BIN and ix both hit merch. Separate PKs; deposit nets. Gate: tests/test_bin_ix.py.",
        plan="Skip debit if this batch already BIN-feed today.",
        outcome="BIN+ix hit merch. Batch-day skip left direct debit. Plan change: book fees; net deposit. Tests 2/2 + second batch + suite 8/8.",
    ),
    _fail(
        slug="bin-fee-after-ix-net",
        surfaces="late BIN fee vs already-netted interchange deposit",
        avoided="r150 BIN vs ix; r140 scheme after net. This is late BIN receivable",
        this_is="late BIN after net opens receivable; does not rewrite",
        seed="net deposit then late BIN fee",
        first_apply="BIN late today",
        plan_change="late BIN receivable; deposit stays",
        step_note="Late-day 6–7; PK 8–11; second 12–13; rewrite xfail 15–17.",
        next_note="Unused: late BIN should rewrite deposit. Avoid bin-late-today skip.",
        **_paths("bin_late", fail=True),
        table="till_bin_late",
        pk="bin_fee_id",
        rg="bin.late|after_net|bin_receivable",
        rg_obs=_rg_obs("bin_late", "late_bin", "netted_ix", "test_late_bin_recv"),
        test_name="late-bin-recv test",
        surface_read="late BIN fee plus netted deposit",
        skip_pred="this BIN already late-posted today",
        verb="assess",
        skip_label="bin-late-today skip",
        src_body=_naive("late_bin", 'debit_merch(ev["batch_id"], ev["cents"])', "counted every late BIN")[0],
        hook_body="def netted_ix(batch_id, net):\n    credit_merch(batch_id, net)\n",
        test_body=(
            "def test_late_bin_recv():\n"
            '    netted_ix("b_1", 4800)\n'
            '    late_bin(bf("bf_1", batch="b_1", cents=25))\n'
            '    late_bin(bf("bf_1", batch="b_1", cents=25))\n'
            '    assert merch_cents("m_1") == 4800 and recv_cents("m_1") == 25 and bin_rows("bf_1") == 1\n'
            "\n"
            "def test_second_bin():\n"
            '    netted_ix("b_a", 96)\n'
            '    late_bin(bf("bf_a", batch="b_a", cents=2))\n'
            '    netted_ix("b_b", 38)\n'
            '    late_bin(bf("bf_b", batch="b_b", cents=1))\n'
            '    assert recv_cents("m_a") == 2 and recv_cents("m_b") == 1\n'
        ),
        test_body_short="same — late BIN receivable",
        obs3="late BIN rewrites deposit",
        obs4="late BIN receivable; deposit stays",
        obs5="merch 4800 recv 25; second BIN adds",
        fail_obs="FAILED test_late_bin_recv - merch 4775 == 4800\n1 failed, 1 passed",
        skip_old=_naive("late_bin", 'debit_merch(ev["batch_id"], ev["cents"])', "counted every late BIN")[1],
        skip_new='    if not bin_today(ev["bin_fee_id"]):\n        debit_merch(ev["batch_id"], ev["cents"])',
        obs7="second BIN ok; hides receivable.",
        still_fail_obs="FAILED if late BIN rewrote merch 4775\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_bin(ev):\n"
            "    if not claim_bin2(ev['bin_fee_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if deposited(ev['batch_id']):\n"
            '        open_recv(merch_of_batch(ev["batch_id"]), ev["cents"], bin=ev["bin_fee_id"])\n'
            '        return {"ok": True, "recv": True}\n'
            '    book_bin(ev["batch_id"], ev["cents"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="late after deposit opens recv",
        rewrite_hook=(
            "def netted_ix(batch_id, net):\n"
            "    if not claim_dep4(dep_id(batch_id)):\n"
            "        return existing_dep(batch_id)\n"
            "    credit_merch(merch_of_batch(batch_id), net)\n"
            "    return batch_id\n"
        ),
        rewrite_hook_obs="deposit first",
        ddl=_ddl("till_bin_late", "bin_fee_id", "  batch_id text NOT NULL,\n  recv_cents int NOT NULL DEFAULT 0"),
        ddl_obs="PK bin_fee_id",
        test2_body=(
            "def test_second_bin():\n"
            '    netted_ix("b_a", 96)\n'
            '    late_bin(bf("bf_a", batch="b_a", cents=2))\n'
            '    netted_ix("b_b", 38)\n'
            '    late_bin(bf("bf_b", batch="b_b", cents=1))\n'
            '    assert recv_cents("m_a") == 2 and recv_cents("m_b") == 1\n'
        ),
        xfail_label="late BIN should rewrite deposit",
        xfail_body=(
            "def test_late_bin_rewrites():\n"
            '    netted_ix("b_p", 4800)\n'
            '    late_bin(bf("bf_p", batch="b_p", cents=25))\n'
            '    assert merch_cents("m_p") == 4775 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_bin_rewrites - recv opened; deposit not rewritten\n1 failed",
        xfail_old="def test_late_bin_rewrites():",
        xfail_new='@pytest.mark.xfail(reason="handoff: late BIN rewrite vs receivable is a policy fork", strict=True)\ndef test_late_bin_rewrites():',
        xfail_patch_obs="xfailed late BIN rewrite",
        goal="till-bin-late late BIN rewrote deposit. Late opens recv. Gate: tests/test_bin_late.py.",
        plan="Skip assess if this BIN already late-posted today.",
        outcome="Late BIN rewrote merch. Late-day skip hid recv. Plan change: recv if deposited. Primary+second pass. Partial: rewrite xfail handoff.",
    ),
)

# r151 reserve interest vs principal / interest after release
_src, _skip = _naive(
    "accrue_int",
    'credit_merch(ev["reserve_id"], ev["cents"])',
    "counted every reserve interest",
)
pair(
    _ok(
        slug="reserve-interest-vs-principal",
        surfaces="rolling-reserve interest accrual vs principal hold",
        avoided="r129 rolling reserve hold vs release; r15 credit_grant. This is interest_id vs principal",
        this_is="interest PK credits; principal hold unchanged",
        seed="accrue interest + principal hold same reserve",
        first_apply="interest accrued today",
        plan_change="interest PK credits available; principal stays held",
        step_note="Reserve-day 6–7; PK 8–11; second reserve 12–13.",
        **_paths("rsv_int"),
        table="till_rsv_int",
        pk="interest_id",
        rg="reserve.interest|principal_hold|accrue_bps",
        rg_obs=_rg_obs("rsv_int", "accrue_int", "hold_prin", "test_int_not_principal_double"),
        test_name="int-not-principal-double test",
        surface_read="reserve interest plus principal hold",
        skip_pred="this reserve already interest-accrued today",
        verb="credit",
        skip_label="interest-accrued-today skip",
        src_body=_src,
        hook_body="def hold_prin(reserve_id, cents):\n    credit_merch(reserve_id, cents)\n",
        test_body=(
            "def test_int_not_principal_double():\n"
            '    hold_prin("rs_1", 500)\n'
            '    accrue_int(ai("in_1", reserve="rs_1", cents=4))\n'
            '    accrue_int(ai("in_1", reserve="rs_1", cents=4))\n'
            '    assert held_cents("m_1") == 500 and avail_cents("m_1") == 4 and int_rows("in_1") == 1\n'
            "\n"
            "def test_second_reserve():\n"
            '    hold_prin("rs_a", 100)\n'
            '    accrue_int(ai("in_a", reserve="rs_a", cents=1))\n'
            '    hold_prin("rs_b", 40)\n'
            '    accrue_int(ai("in_b", reserve="rs_b", cents=1))\n'
            '    assert held_cents("m_a") == 100 and avail_cents("m_a") == 1\n'
        ),
        obs3="interest and principal both credit same bucket",
        obs4="interest to available; principal held",
        obs5="held 500 avail 4; second reserve adds",
        fail_obs="FAILED test_int_not_principal_double - held 504 or avail 0\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not int_today(ev["reserve_id"]):\n        credit_merch(ev["reserve_id"], ev["cents"])',
        obs7="principal still hits available; new reserve same day dropped.",
        still_fail_obs="FAILED test_int_not_principal_double - interest hit held or principal avail\n1 failed, 1 passed",
        rewrite_src=(
            "def accrue_int(ev):\n"
            "    if not claim_int(ev['interest_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_avail(merch_of_rsv(ev["reserve_id"]), ev["cents"], interest=ev["interest_id"])\n'
            '    return {"ok": True, "interest": True}\n'
        ),
        rewrite_src_obs="claim interest_id credits available",
        rewrite_hook=(
            "def hold_prin(reserve_id, cents):\n"
            "    if not claim_rsv2(reserve_id):\n"
            "        return existing_rsv(reserve_id)\n"
            "    hold_rsv(merch_of_rsv(reserve_id), cents, reserve=reserve_id)\n"
            "    return reserve_id\n"
        ),
        obs9="principal claims reserve_id held.",
        rewrite_hook_obs="principal held",
        ddl=_ddl("till_rsv_int", "interest_id", "  reserve_id text NOT NULL,\n  avail_cents int NOT NULL"),
        ddl_obs="PK interest_id",
        test2_body=(
            "def test_second_reserve():\n"
            '    hold_prin("rs_a", 100)\n'
            '    accrue_int(ai("in_a", reserve="rs_a", cents=1))\n'
            '    hold_prin("rs_b", 40)\n'
            '    accrue_int(ai("in_b", reserve="rs_b", cents=1))\n'
            '    assert held_cents("m_a") == 100 and avail_cents("m_a") == 1\n'
        ),
        psql_rows="in_1\nin_a\nin_b",
        residual="compound interest second day",
        grep_pat="interest_id",
        grep_obs="src/rsv_int.py: daily interest PK; no compound",
        goal="till-int interest and principal same bucket. Interest avail; principal held. Gate: tests/test_rsv_int.py.",
        plan="Skip credit if this reserve already interest-accrued today.",
        outcome="Interest hit held. Reserve-day skip left mixed buckets. Plan change: interest avail; principal held. Tests 2/2 + second reserve + suite 8/8.",
    ),
    _fail(
        slug="interest-after-reserve-release",
        surfaces="interest accrual vs already-released principal",
        avoided="r151 interest vs principal; r129 release. This is interest after release no-ops",
        this_is="interest after principal released no-ops; back-accrual handoff",
        seed="release principal then accrue interest",
        first_apply="interest after release today",
        plan_change="interest after release no-ops",
        step_note="After-day 6–7; PK 8–11; second 12–13; back-accrual xfail 15–17.",
        next_note="Unused: interest after release should back-accrue. Avoid interest-after-release-today skip.",
        **_paths("int_rel", fail=True),
        table="till_int_rel",
        pk="interest_id",
        rg="interest.after_release|back_accrual|principal_gone",
        rg_obs=_rg_obs("int_rel", "late_int", "rel_prin", "test_int_after_release_noop"),
        test_name="int-after-release-noop test",
        surface_read="interest plus released principal",
        skip_pred="this reserve already interest-after-release today",
        verb="accrue",
        skip_label="interest-after-release-today skip",
        src_body=_naive("late_int", 'credit_merch(ev["reserve_id"], ev["cents"])', "counted every late interest")[0],
        hook_body="def rel_prin(reserve_id, cents):\n    release_held(reserve_id, cents)\n",
        test_body=(
            "def test_int_after_release_noop():\n"
            '    hold_rsv("m_1", 500, period="2026-W30")\n'
            '    rel_prin("rs_1", 500)\n'
            '    late_int(ai("in_1", reserve="rs_1", cents=4))\n'
            '    late_int(ai("in_1", reserve="rs_1", cents=4))\n'
            '    assert held_cents("m_1") == 0 and avail_cents("m_1") == 500 and int_cents("in_1") == 0\n'
            "\n"
            "def test_second_reserve():\n"
            '    hold_rsv("m_a", 100, period="2026-W29")\n'
            '    rel_prin("rs_a", 100)\n'
            '    hold_rsv("m_b", 40, period="2026-W29")\n'
            '    assert avail_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        test_body_short="same — interest after release no-ops",
        obs3="late interest credits after release",
        obs4="late interest no-ops",
        obs5="avail 500 from principal only; int 0; second independent",
        fail_obs="FAILED test_int_after_release_noop - avail 504 or int 4\n1 failed, 1 passed",
        skip_old=_naive("late_int", 'credit_merch(ev["reserve_id"], ev["cents"])', "counted every late interest")[1],
        skip_new='    if not int_today(ev["reserve_id"]):\n        credit_merch(ev["reserve_id"], ev["cents"])',
        obs7="second reserve ok; hides no-op.",
        still_fail_obs="FAILED if late interest credited 4 after release\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_int(ev):\n"
            "    if held_of(ev['reserve_id']) == 0:\n"
            '        return {"ok": True, "nothing": True}\n'
            "    if not claim_int2(ev['interest_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_avail(merch_of_rsv(ev["reserve_id"]), ev["cents"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="interest no-ops if principal gone",
        rewrite_hook=(
            "def rel_prin(reserve_id, cents):\n"
            "    if not claim_rel3(rel_id(reserve_id)):\n"
            "        return existing_rel(reserve_id)\n"
            "    release_held(reserve_id, cents)\n"
            "    return reserve_id\n"
        ),
        rewrite_hook_obs="principal released first",
        ddl=_ddl("till_int_rel", "interest_id", "  reserve_id text NOT NULL,\n  int_cents int NOT NULL DEFAULT 0"),
        ddl_obs="PK interest_id",
        test2_body=(
            "def test_second_reserve():\n"
            '    hold_rsv("m_a", 100, period="2026-W29")\n'
            '    rel_prin("rs_a", 100)\n'
            '    hold_rsv("m_b", 40, period="2026-W29")\n'
            '    assert avail_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        xfail_label="interest after release should back-accrue",
        xfail_body=(
            "def test_back_accrual():\n"
            '    hold_rsv("m_p", 500, period="2026-W28")\n'
            '    rel_prin("rs_p", 500)\n'
            '    late_int(ai("in_p", reserve="rs_p", cents=4))\n'
            '    assert avail_cents("m_p") == 504\n'
        ),
        xfail_fail_obs="FAILED test_back_accrual - no-op; no back-accrual\n1 failed",
        xfail_old="def test_back_accrual():",
        xfail_new='@pytest.mark.xfail(reason="handoff: interest after release must back-accrue days held", strict=True)\ndef test_back_accrual():',
        xfail_patch_obs="xfailed back-accrual",
        goal="till-int-rel late interest credited after release. No-op if principal gone. Gate: tests/test_int_rel.py.",
        plan="Skip accrue if this reserve already interest-after-release today.",
        outcome="Late interest credited. After-day skip hid no-op. Plan change: nothing if held 0. Primary+second pass. Partial: back-accrual xfail handoff.",
    ),
)

# r152 multi-MID netting / late MID after net
_src, _skip = _naive(
    "net_mids",
    'post_ledger(ev["mid"], ev["cents"])',
    "counted every multi-MID net",
)
pair(
    _ok(
        slug="multi-mid-netting",
        surfaces="multi-MID multilateral net vs per-MID gross",
        avoided="r136 netting window vs gross; r131 IC pair. This is (window, mid) stage vs window net",
        this_is="per-MID legs staged; close posts one net per window",
        seed="stage two MIDs + close window",
        first_apply="MIDs netted today",
        plan_change="stage per MID; close PK window net",
        step_note="Window-day 6–7; PK 8–11; second window 12–13.",
        **_paths("mid_net"),
        table="till_mid_net",
        pk="window_id",
        rg="multi_mid|per_mid_gross|window_net|merchant_id",
        rg_obs=_rg_obs("mid_net", "net_mids", "stage_mid", "test_net_not_per_mid_double"),
        test_name="net-not-per-mid-double test",
        surface_read="multi-MID net plus per-MID gross",
        skip_pred="these MIDs already netted today",
        verb="post",
        skip_label="mids-netted-today skip",
        src_body=_src,
        hook_body="def stage_mid(window_id, mid, cents):\n    post_ledger(mid, cents)\n",
        test_body=(
            "def test_net_not_per_mid_double():\n"
            '    stage_mid("w_1", "mid_a", 5000)\n'
            '    stage_mid("w_1", "mid_b", -4700)\n'
            '    net_mids(nm("w_1", cents=300))\n'
            '    net_mids(nm("w_1", cents=300))\n'
            '    assert posted_cents("w_1") == 300 and not posted("mid_a") and mid_rows("w_1") == 1\n'
            "\n"
            "def test_second_window():\n"
            '    stage_mid("w_a", "mid_c", 100)\n'
            '    net_mids(nm("w_a", cents=100))\n'
            '    stage_mid("w_b", "mid_d", 40)\n'
            '    net_mids(nm("w_b", cents=40))\n'
            '    assert posted_cents("w_a") == 100 and posted_cents("w_b") == 40\n'
        ),
        obs3="net posts each MID plus window",
        obs4="MIDs staged; window net only",
        obs5="window 300; MIDs not posted; second window adds",
        fail_obs="FAILED test_net_not_per_mid_double - posted 5300 or 600\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not netted_today(ev.get("window_id")):\n        post_ledger(ev["mid"], ev["cents"])',
        obs7="net still posts MIDs; new window same day dropped.",
        still_fail_obs="FAILED test_net_not_per_mid_double - net posted per-MID gross\n1 failed, 1 passed",
        rewrite_src=(
            "def net_mids(ev):\n"
            "    if not claim_mid_net(ev['window_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    net = staged_net(ev['window_id'])\n"
            "    post_ledger(ev['window_id'], net, reason='mid_net')\n"
            '    return {"ok": True, "net": net}\n'
        ),
        rewrite_src_obs="claim window_id posts staged net",
        rewrite_hook=(
            "def stage_mid(window_id, mid, cents):\n"
            "    lid = mid_leg(window_id, mid)\n"
            "    if not claim_mid_leg(lid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    stage(window_id, lid, cents)\n"
            '    return {"ok": True, "staged": True}\n'
        ),
        obs9="MIDs claim (window, mid) into stage.",
        rewrite_hook_obs="per-MID stage",
        ddl=_ddl("till_mid_net", "window_id", "  net_cents int NOT NULL"),
        ddl_obs="PK window_id",
        test2_body=(
            "def test_second_window():\n"
            '    stage_mid("w_a", "mid_c", 100)\n'
            '    net_mids(nm("w_a", cents=100))\n'
            '    stage_mid("w_b", "mid_d", 40)\n'
            '    net_mids(nm("w_b", cents=40))\n'
            '    assert posted_cents("w_a") == 100 and posted_cents("w_b") == 40\n'
        ),
        psql_rows="w_1\nw_a\nw_b",
        residual="excluded MID",
        grep_pat="staged_net",
        grep_obs="src/mid_net.py: net of staged MIDs; no exclude list",
        goal="till-mid net posted per-MID gross. Stage then window net. Gate: tests/test_mid_net.py.",
        plan="Skip post if these MIDs already netted today.",
        outcome="Net posted per-MID. Window-day skip left gross. Plan change: stage then net PK. Tests 2/2 + second window + suite 8/8.",
    ),
    _fail(
        slug="late-mid-after-net",
        surfaces="late MID leg vs already-closed multi-MID net",
        avoided="r152 multi-MID net; r136 late leg. This is late MID next window",
        this_is="late MID after close stages next; does not reopen",
        seed="close multi-MID then late MID",
        first_apply="late MID today",
        plan_change="late MID next window; reopen handoff",
        step_note="Late-day 6–7; PK 8–11; second 12–13; reopen xfail 15–17.",
        next_note="Unused: late MID should reopen window. Avoid late-mid-today skip.",
        **_paths("mid_late", fail=True),
        table="till_mid_late",
        pk="leg_id",
        rg="late_mid|next_window|reopen_mid_net",
        rg_obs=_rg_obs("mid_late", "late_mid", "closed_mids", "test_late_mid_next"),
        test_name="late-mid-next test",
        surface_read="late MID plus closed multi-MID net",
        skip_pred="this late MID already booked today",
        verb="post",
        skip_label="late-mid-today skip",
        src_body=_naive("late_mid", 'post_ledger(ev["mid"], ev["cents"])', "counted every late MID")[0],
        hook_body="def closed_mids(window_id, net):\n    post_ledger(window_id, net)\n",
        test_body=(
            "def test_late_mid_next():\n"
            '    closed_mids("w_1", 300)\n'
            '    late_mid(lm("l_late", window="w_1", mid="mid_c", cents=80))\n'
            '    late_mid(lm("l_late", window="w_1", mid="mid_c", cents=80))\n'
            '    assert posted_cents("w_1") == 300 and next_staged("w_2", "l_late") == 80\n'
            "\n"
            "def test_second_late():\n"
            '    late_mid(lm("l_a", window="w_a", mid="mid_x", cents=10))\n'
            '    late_mid(lm("l_b", window="w_b", mid="mid_y", cents=4))\n'
            '    assert next_staged("w_a_next", "l_a") == 10\n'
        ),
        test_body_short="same — late MID stages next window",
        obs3="late MID posts gross into closed window",
        obs4="late MID stages next",
        obs5="w_1 stays 300; late in next; second late independent",
        fail_obs="FAILED test_late_mid_next - posted 380 or late posted gross\n1 failed, 1 passed",
        skip_old=_naive("late_mid", 'post_ledger(ev["mid"], ev["cents"])', "counted every late MID")[1],
        skip_new='    if not late_today(ev["mid"]):\n        post_ledger(ev["mid"], ev["cents"])',
        obs7="second late ok; hides next-window.",
        still_fail_obs="FAILED if late MID posted into w_1\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_mid(ev):\n"
            "    if not claim_late_mid(ev['leg_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    nxt = next_window(ev['window'])\n"
            "    stage(nxt, ev['leg_id'], ev['cents'])\n"
            '    return {"ok": True, "next": nxt}\n'
        ),
        rewrite_src_obs="claim leg_id stages next",
        rewrite_hook=(
            "def closed_mids(window_id, net):\n"
            "    if not claim_mid_net2(window_id):\n"
            "        return existing_win(window_id)\n"
            "    post_ledger(window_id, net, reason='mid_net')\n"
            "    return window_id\n"
        ),
        rewrite_hook_obs="closed window stays",
        ddl=_ddl("till_mid_late", "leg_id", "  next_window text NOT NULL,\n  mid text NOT NULL"),
        ddl_obs="PK leg_id",
        test2_body=(
            "def test_second_late():\n"
            '    late_mid(lm("l_a", window="w_a", mid="mid_x", cents=10))\n'
            '    late_mid(lm("l_b", window="w_b", mid="mid_y", cents=4))\n'
            '    assert next_staged("w_a_next", "l_a") == 10 and next_staged("w_b_next", "l_b") == 4\n'
        ),
        xfail_label="late MID should reopen window",
        xfail_body=(
            "def test_late_mid_reopens():\n"
            '    closed_mids("w_p", 300)\n'
            '    late_mid(lm("l_p", window="w_p", mid="mid_z", cents=80))\n'
            '    assert posted_cents("w_p") == 380 and reopened("w_p")\n'
        ),
        xfail_fail_obs="FAILED test_late_mid_reopens - staged next; did not reopen\n1 failed",
        xfail_old="def test_late_mid_reopens():",
        xfail_new='@pytest.mark.xfail(reason="handoff: late MID reopen vs next-window is a policy fork", strict=True)\ndef test_late_mid_reopens():',
        xfail_patch_obs="xfailed late MID reopen",
        goal="till-mid-late late MID posted into closed net. Late stages next. Gate: tests/test_mid_late.py.",
        plan="Skip post if this late MID already booked today.",
        outcome="Late posted gross. Late-day skip hid next-window. Plan change: stage next. Primary+second pass. Partial: reopen xfail handoff.",
    ),
)

# r153 holdback vs merchant funding / funding after holdback
_src, _skip = _naive(
    "place_hb",
    'debit_avail(ev["merchant"], ev["cents"])',
    "counted every holdback",
)
pair(
    _ok(
        slug="holdback-vs-merchant-funding",
        surfaces="underwriting holdback vs merchant funding credit",
        avoided="r129 rolling reserve; r138 h2a. This is holdback_id vs funding_id",
        this_is="holdback PK deducts avail; funding PK credits separately",
        seed="place holdback + fund merchant",
        first_apply="holdback placed today",
        plan_change="holdback PK; funding PK; neither is the other",
        step_note="Merchant-day 6–7; PK 8–11; second merchant 12–13.",
        **_paths("hb_fund"),
        table="till_hb_fund",
        pk="holdback_id",
        rg="underwriting.holdback|merchant.funding|funding_id",
        rg_obs=_rg_obs("hb_fund", "place_hb", "fund_merch", "test_hb_not_funding_double"),
        test_name="hb-not-funding-double test",
        surface_read="holdback plus merchant funding",
        skip_pred="this merchant already holdback-placed today",
        verb="debit",
        skip_label="holdback-placed-today skip",
        src_body=_src,
        hook_body="def fund_merch(merchant, cents):\n    debit_avail(merchant, cents)\n",
        test_body=(
            "def test_hb_not_funding_double():\n"
            '    credit_avail("m_1", 8000)\n'
            '    place_hb(hb("hb_1", merchant="m_1", cents=2000))\n'
            '    place_hb(hb("hb_1", merchant="m_1", cents=2000))\n'
            '    fund_merch("m_1", 5000)\n'
            '    assert avail_cents("m_1") == 1000 and held_cents("m_1") == 2000 and funded_cents("m_1") == 5000\n'
            "\n"
            "def test_second_merchant():\n"
            '    credit_avail("m_a", 200)\n'
            '    place_hb(hb("hb_a", merchant="m_a", cents=50))\n'
            '    fund_merch("m_a", 100)\n'
            '    credit_avail("m_b", 80)\n'
            '    place_hb(hb("hb_b", merchant="m_b", cents=20))\n'
            '    fund_merch("m_b", 40)\n'
            '    assert avail_cents("m_a") == 50 and avail_cents("m_b") == 20\n'
        ),
        obs3="holdback and funding both debit available as one",
        obs4="holdback holds; funding pays from remaining",
        obs5="avail 1000 held 2000 funded 5000; second merchant adds",
        fail_obs="FAILED test_hb_not_funding_double - avail 0 or 3000 or funded 7000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not hb_today(ev["merchant"]):\n        debit_avail(ev["merchant"], ev["cents"])',
        obs7="funding still mixed with holdback; new merchant same day dropped.",
        still_fail_obs="FAILED test_hb_not_funding_double - funding treated as holdback\n1 failed, 1 passed",
        rewrite_src=(
            "def place_hb(ev):\n"
            "    if not claim_hb(ev['holdback_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    hold_rsv(ev["merchant"], ev["cents"], hb=ev["holdback_id"])\n'
            '    return {"ok": True, "held": True}\n'
        ),
        rewrite_src_obs="claim holdback_id holds",
        rewrite_hook=(
            "def fund_merch(merchant, cents):\n"
            "    fid = fund_id(merchant, cents)\n"
            "    if not claim_fund3(fid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if avail_of(merchant) < cents:\n"
            '        return {"ok": True, "short": True}\n'
            "    debit_avail(merchant, cents, funding=fid)\n"
            '    return {"ok": True, "funded": True}\n'
        ),
        obs9="funding claims funding_id from remaining avail.",
        rewrite_hook_obs="funding PK remaining",
        ddl=_ddl("till_hb_fund", "holdback_id", "  merchant text NOT NULL,\n  funding_id text UNIQUE"),
        ddl_obs="PK holdback_id",
        test2_body=(
            "def test_second_merchant():\n"
            '    credit_avail("m_a", 200)\n'
            '    place_hb(hb("hb_a", merchant="m_a", cents=50))\n'
            '    fund_merch("m_a", 100)\n'
            '    credit_avail("m_b", 80)\n'
            '    place_hb(hb("hb_b", merchant="m_b", cents=20))\n'
            '    fund_merch("m_b", 40)\n'
            '    assert avail_cents("m_a") == 50 and avail_cents("m_b") == 20\n'
        ),
        psql_rows="hb_1\nhb_a\nhb_b",
        residual="funding of held",
        grep_pat="short",
        grep_obs="src/hb_fund.py: funding from avail; no held spend",
        goal="till-hb holdback and funding mixed. Holdback holds; funding remaining. Gate: tests/test_hb_fund.py.",
        plan="Skip debit if this merchant already holdback-placed today.",
        outcome="Holdback+funding mixed. Merchant-day skip left mixed debit. Plan change: hold PK; fund remaining. Tests 2/2 + second merchant + suite 8/8.",
    ),
    _fail(
        slug="funding-after-holdback",
        surfaces="merchant funding vs insufficient available after holdback",
        avoided="r153 holdback vs funding; r138 payout of held. This is short funding blocked",
        this_is="funding after holdback blocked if avail short; force-held handoff",
        seed="holdback then oversized funding",
        first_apply="funding tried today",
        plan_change="funding blocked if avail short",
        step_note="Fund-day 6–7; PK 8–11; second 12–13; force-held xfail 15–17.",
        next_note="Unused: funding of held after holdback. Avoid funding-tried-today skip.",
        **_paths("fund_short", fail=True),
        table="till_fund_short",
        pk="funding_id",
        rg="funding.short|after_holdback|force_held",
        rg_obs=_rg_obs("fund_short", "fund_big", "hb_first", "test_funding_short_blocked"),
        test_name="funding-short-blocked test",
        surface_read="oversized funding plus holdback",
        skip_pred="this merchant funding already tried today",
        verb="fund",
        skip_label="funding-tried-today skip",
        src_body=_naive("fund_big", 'debit_avail(ev["merchant"], ev["cents"])', "counted every oversized funding")[0],
        hook_body="def hb_first(merchant, cents):\n    hold_rsv(merchant, cents)\n",
        test_body=(
            "def test_funding_short_blocked():\n"
            '    credit_avail("m_1", 8000)\n'
            '    hb_first("m_1", 2000)\n'
            '    fund_big(fb("fn_1", merchant="m_1", cents=7000))\n'
            '    fund_big(fb("fn_1", merchant="m_1", cents=7000))\n'
            '    assert avail_cents("m_1") == 6000 and held_cents("m_1") == 2000 and funded_cents("m_1") == 0\n'
            "\n"
            "def test_second_merchant():\n"
            '    credit_avail("m_a", 200)\n'
            '    hb_first("m_a", 50)\n'
            '    fund_big(fb("fn_a", merchant="m_a", cents=100))\n'
            '    credit_avail("m_b", 80)\n'
            '    hb_first("m_b", 20)\n'
            '    fund_big(fb("fn_b", merchant="m_b", cents=40))\n'
            '    assert funded_cents("m_a") == 100 and funded_cents("m_b") == 40\n'
        ),
        test_body_short="same — oversized funding blocked",
        obs3="funding spends into held",
        obs4="funding blocked if avail short",
        obs5="avail 6000 held 2000 funded 0; smaller fundings work",
        fail_obs="FAILED test_funding_short_blocked - funded 7000 or avail 0\n1 failed, 1 passed",
        skip_old=_naive("fund_big", 'debit_avail(ev["merchant"], ev["cents"])', "counted every oversized funding")[1],
        skip_new='    if not funded_today(ev["merchant"]):\n        debit_avail(ev["merchant"], ev["cents"])',
        obs7="second merchant ok; hides short block.",
        still_fail_obs="FAILED if oversized funding spent held\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def fund_big(ev):\n"
            "    if not claim_fund4(ev['funding_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if avail_of(ev['merchant']) < ev['cents']:\n"
            '        return {"ok": True, "blocked": True}\n'
            '    debit_avail(ev["merchant"], ev["cents"], funding=ev["funding_id"])\n'
            '    return {"ok": True, "funded": True}\n'
        ),
        rewrite_src_obs="claim funding_id; blocked if short",
        rewrite_hook=(
            "def hb_first(merchant, cents):\n"
            "    if not claim_hb2(hb_id(merchant, cents)):\n"
            "        return existing_hb(merchant)\n"
            "    hold_rsv(merchant, cents)\n"
            "    return merchant\n"
        ),
        rewrite_hook_obs="holdback first",
        ddl=_ddl("till_fund_short", "funding_id", "  merchant text NOT NULL,\n  blocked bool NOT NULL DEFAULT false"),
        ddl_obs="PK funding_id",
        test2_body=(
            "def test_second_merchant():\n"
            '    credit_avail("m_a", 200)\n'
            '    hb_first("m_a", 50)\n'
            '    fund_big(fb("fn_a", merchant="m_a", cents=100))\n'
            '    credit_avail("m_b", 80)\n'
            '    hb_first("m_b", 20)\n'
            '    fund_big(fb("fn_b", merchant="m_b", cents=40))\n'
            '    assert funded_cents("m_a") == 100 and funded_cents("m_b") == 40\n'
        ),
        xfail_label="funding of held after holdback",
        xfail_body=(
            "def test_fund_held():\n"
            '    credit_avail("m_p", 8000)\n'
            '    hb_first("m_p", 2000)\n'
            '    fund_big(fb("fn_p", merchant="m_p", cents=7000, force=True))\n'
            '    assert funded_cents("m_p") == 7000 and held_cents("m_p") == 1000\n'
        ),
        xfail_fail_obs="FAILED test_fund_held - blocked; no force path\n1 failed",
        xfail_old="def test_fund_held():",
        xfail_new='@pytest.mark.xfail(reason="handoff: force funding of holdback requires UW override", strict=True)\ndef test_fund_held():',
        xfail_patch_obs="xfailed fund held",
        goal="till-fund-short oversized funding spent held. Funding blocked if short. Gate: tests/test_fund_short.py.",
        plan="Skip fund if this merchant funding already tried today.",
        outcome="Funding spent held. Fund-day skip hid short block. Plan change: block if avail short. Primary+second pass. Partial: force-held xfail handoff.",
    ),
)

# r154 unallocated cash vs invoice apply is already r149. Use chargeback fee vs representment.
_src, _skip = _naive(
    "book_cb_fee",
    'debit_merch(ev["dispute_id"], ev["cents"])',
    "counted every chargeback fee",
)
pair(
    _ok(
        slug="cb-fee-vs-representment",
        surfaces="chargeback fee vs representment win credit",
        avoided="r139 represent vs win; r140 ix. This is fee_id stays even if win credits",
        this_is="CB fee PK debit; win credits principal not fee",
        seed="book CB fee + representment win",
        first_apply="CB fee booked today",
        plan_change="fee PK stays; win credits principal only",
        step_note="Dispute-day 6–7; PK 8–11; second dispute 12–13.",
        **_paths("cb_fee"),
        table="till_cb_fee",
        pk="fee_id",
        rg="chargeback.fee|representment.win|fee_stays",
        rg_obs=_rg_obs("cb_fee", "book_cb_fee", "win_rep", "test_fee_not_win_double"),
        test_name="fee-not-win-double test",
        surface_read="chargeback fee plus representment win",
        skip_pred="this dispute already CB-feed today",
        verb="debit",
        skip_label="cb-feed-today skip",
        src_body=_src,
        hook_body="def win_rep(dispute_id, cents):\n    debit_merch(dispute_id, -cents)\n",
        test_body=(
            "def test_fee_not_win_double():\n"
            '    book_cb_fee(cf("fe_1", dispute="dp_1", cents=150))\n'
            '    book_cb_fee(cf("fe_1", dispute="dp_1", cents=150))\n'
            '    win_rep("dp_1", 5000)\n'
            '    assert merch_cents("m_1") == 4850 and fee_cents("fe_1") == 150 and fee_rows("fe_1") == 1\n'
            "\n"
            "def test_second_dispute():\n"
            '    book_cb_fee(cf("fe_a", dispute="dp_a", cents=15))\n'
            '    win_rep("dp_a", 100)\n'
            '    book_cb_fee(cf("fe_b", dispute="dp_b", cents=8))\n'
            '    win_rep("dp_b", 40)\n'
            '    assert merch_cents("m_a") == 85 and merch_cents("m_b") == 32\n'
        ),
        obs3="fee and win both reverse each other blindly",
        obs4="fee stays; win credits principal",
        obs5="merch 4850 = -150+5000; second dispute adds",
        fail_obs="FAILED test_fee_not_win_double - merch 5000 or 0\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not fee_today(ev["dispute_id"]):\n        debit_merch(ev["dispute_id"], ev["cents"])',
        obs7="win still nets fee away; new dispute same day dropped.",
        still_fail_obs="FAILED test_fee_not_win_double - win reversed fee\n1 failed, 1 passed",
        rewrite_src=(
            "def book_cb_fee(ev):\n"
            "    if not claim_cb_fee(ev['fee_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_merch(merch_of_dp(ev["dispute_id"]), ev["cents"], fee=ev["fee_id"])\n'
            '    return {"ok": True, "fee": True}\n'
        ),
        rewrite_src_obs="claim fee_id debit fee",
        rewrite_hook=(
            "def win_rep(dispute_id, cents):\n"
            "    wid = win_id(dispute_id, 1)\n"
            "    if not claim_win2(wid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_dp(dispute_id), cents, win=wid)\n"
            '    return {"ok": True, "won": True}\n'
        ),
        obs9="win credits principal; fee stays.",
        rewrite_hook_obs="win PK principal",
        ddl=_ddl("till_cb_fee", "fee_id", "  dispute_id text NOT NULL,\n  win_id text UNIQUE"),
        ddl_obs="PK fee_id",
        test2_body=(
            "def test_second_dispute():\n"
            '    book_cb_fee(cf("fe_a", dispute="dp_a", cents=15))\n'
            '    win_rep("dp_a", 100)\n'
            '    book_cb_fee(cf("fe_b", dispute="dp_b", cents=8))\n'
            '    win_rep("dp_b", 40)\n'
            '    assert merch_cents("m_a") == 85 and merch_cents("m_b") == 32\n'
        ),
        psql_rows="fe_1\nfe_a\nfe_b",
        residual="fee refund on win",
        grep_pat="fee_id",
        grep_obs="src/cb_fee.py: fee stays on win; no fee refund",
        goal="till-cb-fee fee and win netted to zero. Fee stays; win principal. Gate: tests/test_cb_fee.py.",
        plan="Skip debit if this dispute already CB-feed today.",
        outcome="Fee+win netted wrong. Dispute-day skip left win reversing fee. Plan change: fee PK stays; win principal. Tests 2/2 + second dispute + suite 8/8.",
    ),
    _fail(
        slug="cb-fee-refund-on-win",
        surfaces="chargeback fee refund vs already-won representment",
        avoided="r154 fee stays on win; r17 fee refund. This is fee refund after win is extra",
        this_is="fee refund after win is a separate PK; not automatic",
        seed="win then fee refund",
        first_apply="fee refunded today",
        plan_change="fee refund PK; not implied by win",
        step_note="Refund-day 6–7; PK 8–11; second 12–13; auto-refund xfail 15–17.",
        next_note="Unused: win should auto-refund CB fee. Avoid fee-refunded-today skip.",
        **_paths("cb_fee_rf", fail=True),
        table="till_cb_fee_rf",
        pk="fee_refund_id",
        rg="chargeback.fee_refund|after_win|auto_refund",
        rg_obs=_rg_obs("cb_fee_rf", "refund_fee", "already_win", "test_fee_refund_not_auto"),
        test_name="fee-refund-not-auto test",
        surface_read="CB fee refund plus already-won dispute",
        skip_pred="this fee already refunded today",
        verb="refund",
        skip_label="fee-refunded-today skip",
        src_body=_naive("refund_fee", 'credit_merch(ev["dispute_id"], ev["cents"])', "counted every CB fee refund")[0],
        hook_body="def already_win(dispute_id, cents):\n    credit_merch(dispute_id, cents)\n",
        test_body=(
            "def test_fee_refund_not_auto():\n"
            '    book_fee_and_win("dp_1", principal=5000, fee=150)\n'
            '    refund_fee(fr("fr_1", dispute="dp_1", cents=150))\n'
            '    refund_fee(fr("fr_1", dispute="dp_1", cents=150))\n'
            '    assert merch_cents("m_1") == 5000 and fee_refund("fr_1") == 150 and fr_rows("fr_1") == 1\n'
            "\n"
            "def test_second_refund():\n"
            '    book_fee_and_win("dp_a", principal=100, fee=15)\n'
            '    refund_fee(fr("fr_a", dispute="dp_a", cents=15))\n'
            '    book_fee_and_win("dp_b", principal=40, fee=8)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 32\n'
        ),
        test_body_short="same — fee refund PK after win; not auto",
        obs3="fee refund doubles win credit",
        obs4="fee refund PK; win already credited principal",
        obs5="merch 5000 after fee refund; dp_b still has fee",
        fail_obs="FAILED test_fee_refund_not_auto - merch 5150 or 4850\n1 failed, 1 passed",
        skip_old=_naive("refund_fee", 'credit_merch(ev["dispute_id"], ev["cents"])', "counted every CB fee refund")[1],
        skip_new='    if not refunded_today(ev["dispute_id"]):\n        credit_merch(ev["dispute_id"], ev["cents"])',
        obs7="second refund ok; hides fee-refund PK.",
        still_fail_obs="FAILED if fee refund double-counted win\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def refund_fee(ev):\n"
            "    if not claim_fr2(ev['fee_refund_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_merch(merch_of_dp(ev["dispute_id"]), ev["cents"], fee_refund=ev["fee_refund_id"])\n'
            '    return {"ok": True, "refunded": True}\n'
        ),
        rewrite_src_obs="claim fee_refund_id credits fee back",
        rewrite_hook=(
            "def already_win(dispute_id, cents):\n"
            "    if not claim_win3(win_id(dispute_id, 1)):\n"
            "        return existing_win(dispute_id)\n"
            "    credit_merch(merch_of_dp(dispute_id), cents)\n"
            "    return dispute_id\n"
        ),
        rewrite_hook_obs="win principal first",
        ddl=_ddl("till_cb_fee_rf", "fee_refund_id", "  dispute_id text NOT NULL"),
        ddl_obs="PK fee_refund_id",
        test2_body=(
            "def test_second_refund():\n"
            '    book_fee_and_win("dp_a", principal=100, fee=15)\n'
            '    refund_fee(fr("fr_a", dispute="dp_a", cents=15))\n'
            '    book_fee_and_win("dp_b", principal=40, fee=8)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 32\n'
        ),
        xfail_label="win should auto-refund CB fee",
        xfail_body=(
            "def test_auto_fee_refund():\n"
            '    book_fee_and_win("dp_p", principal=5000, fee=150)\n'
            '    assert merch_cents("m_p") == 5000 and fee_refund_auto("dp_p") == 150\n'
        ),
        xfail_fail_obs="FAILED test_auto_fee_refund - merch 4850; fee not auto-refunded\n1 failed",
        xfail_old="def test_auto_fee_refund():",
        xfail_new='@pytest.mark.xfail(reason="handoff: win auto-refund of CB fee is a network policy", strict=True)\ndef test_auto_fee_refund():',
        xfail_patch_obs="xfailed auto fee refund",
        goal="till-cb-fee-rf fee refund double-counted win. Fee refund PK. Gate: tests/test_cb_fee_rf.py.",
        plan="Skip refund if this fee already refunded today.",
        outcome="Fee refund mixed with win. Refund-day skip hid fee PK. Plan change: fee_refund PK. Primary+second pass. Partial: auto-refund xfail handoff.",
    ),
)

# r155 network token vs PAN auth remaining vs cryptogram replay
_src, _skip = _naive(
    "bind_nt",
    'hold_auth(ev["token_id"], ev["cents"])',
    "counted every network token bind",
)
pair(
    _ok(
        slug="network-token-vs-pan-auth",
        surfaces="network-token cryptogram bind vs PAN authorization hold",
        avoided="r65 issuing auth vs capture; r96 disable card. This is token_id cryptogram vs pan_auth_id",
        this_is="token bind records cryptogram; PAN auth PK hold; bind does not hold",
        seed="bind network token + PAN auth same card",
        first_apply="token bound today",
        plan_change="bind records; PAN auth PK hold",
        step_note="Card-day 6–7; PK 8–11; second card 12–13.",
        **_paths("nt_pan"),
        table="till_nt_pan",
        pk="pan_auth_id",
        rg="network_token|cryptogram|pan_auth|token_bind",
        rg_obs=_rg_obs("nt_pan", "bind_nt", "pan_auth", "test_bind_not_auth_double"),
        test_name="bind-not-auth-double test",
        surface_read="network-token bind plus PAN auth",
        skip_pred="this card already token-bound today",
        verb="hold",
        skip_label="token-bound-today skip",
        src_body=_src,
        hook_body="def pan_auth(pan, cents):\n    hold_auth(pan, cents)\n",
        test_body=(
            "def test_bind_not_auth_double():\n"
            '    bind_nt(nt("tk_1", pan="pan_1", crypto="cv_1"))\n'
            '    bind_nt(nt("tk_1", pan="pan_1", crypto="cv_1"))\n'
            '    pan_auth("pan_1", 5000)\n'
            '    assert bound("tk_1") and hold_cents("au_1") == 5000 and nt_rows("au_1") == 1\n'
            "\n"
            "def test_second_card():\n"
            '    bind_nt(nt("tk_a", pan="pan_a", crypto="cv_a"))\n'
            '    pan_auth("pan_a", 100)\n'
            '    bind_nt(nt("tk_b", pan="pan_b", crypto="cv_b"))\n'
            '    pan_auth("pan_b", 40)\n'
            '    assert hold_cents("au_a") == 100 and hold_cents("au_b") == 40\n'
        ),
        obs3="bind and PAN auth both hold",
        obs4="bind records cryptogram; PAN auth PK hold",
        obs5="hold once; bind no extra; second card adds",
        fail_obs="FAILED test_bind_not_auth_double - hold 10000 or 15000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not bound_today(ev["token_id"]):\n        hold_auth(ev["token_id"], ev["cents"])',
        obs7="PAN auth still extra-holds; new card same day dropped.",
        still_fail_obs="FAILED test_bind_not_auth_double - bind held or PAN extra\n1 failed, 1 passed",
        rewrite_src=(
            "def bind_nt(ev):\n"
            "    if not claim_tk(ev['token_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_crypto(ev["token_id"], ev["pan"], ev["crypto"])\n'
            '    return {"ok": True, "bound": True}\n'
        ),
        rewrite_src_obs="claim token_id stores cryptogram",
        rewrite_hook=(
            "def pan_auth(pan, cents):\n"
            "    aid = pan_auth_id(pan, cents)\n"
            "    if not claim_pan_au(aid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    hold_auth(aid, cents, pan=pan)\n"
            '    return {"ok": True, "held": True}\n'
        ),
        obs9="PAN auth claims pan_auth_id hold.",
        rewrite_hook_obs="PK pan_auth_id",
        ddl=_ddl("till_nt_pan", "pan_auth_id", "  token_id text UNIQUE,\n  crypto text NOT NULL"),
        ddl_obs="PK pan_auth_id",
        test2_body=(
            "def test_second_card():\n"
            '    bind_nt(nt("tk_a", pan="pan_a", crypto="cv_a"))\n'
            '    pan_auth("pan_a", 100)\n'
            '    bind_nt(nt("tk_b", pan="pan_b", crypto="cv_b"))\n'
            '    pan_auth("pan_b", 40)\n'
            '    assert hold_cents("au_a") == 100 and hold_cents("au_b") == 40\n'
        ),
        psql_rows="au_1\nau_a\nau_b",
        residual="cryptogram replay",
        grep_pat="store_crypto",
        grep_obs="src/nt_pan.py: bind stores crypto; no replay check",
        goal="till-nt bind and PAN auth both held. Bind records; PAN PK. Gate: tests/test_nt_pan.py.",
        plan="Skip hold if this card already token-bound today.",
        outcome="Bind+PAN double-held. Card-day skip left bind as hold. Plan change: store crypto; PAN PK. Tests 2/2 + second card + suite 8/8.",
    ),
    _fail(
        slug="cryptogram-replay-after-bind",
        surfaces="cryptogram replay vs already-bound network token",
        avoided="r155 token vs PAN; r60 Braintree nonce. This is crypto one-time",
        this_is="replayed cryptogram refused; rotate is handoff",
        seed="bind then replay same cryptogram",
        first_apply="cryptogram replayed today",
        plan_change="crypto one-time; replay blocked",
        step_note="Replay-day 6–7; PK 8–11; second 12–13; rotate xfail 15–17.",
        next_note="Unused: replay after rotate should succeed. Avoid cryptogram-replayed-today skip.",
        **_paths("nt_rep", fail=True),
        table="till_nt_rep",
        pk="crypto",
        rg="cryptogram.replay|one_time|rotate_crypto",
        rg_obs=_rg_obs("nt_rep", "replay_cv", "bound_first", "test_replay_blocked"),
        test_name="replay-blocked test",
        surface_read="cryptogram replay plus bound token",
        skip_pred="this cryptogram already replayed today",
        verb="auth",
        skip_label="cryptogram-replayed-today skip",
        src_body=_naive("replay_cv", 'hold_auth(ev["token_id"], ev.get("cents", 0))', "counted every crypto replay")[0],
        hook_body="def bound_first(token_id, pan, crypto):\n    store_crypto(token_id, pan, crypto)\n",
        test_body=(
            "def test_replay_blocked():\n"
            '    bound_first("tk_1", "pan_1", "cv_1")\n'
            '    pan_auth_with("tk_1", "cv_1", 5000)\n'
            '    replay_cv(rp("tk_1", crypto="cv_1", cents=5000))\n'
            '    replay_cv(rp("tk_1", crypto="cv_1", cents=5000))\n'
            '    assert hold_cents("au_1") == 5000 and used_crypto("cv_1") and nt_rows("cv_1") == 1\n'
            "\n"
            "def test_second_crypto():\n"
            '    bound_first("tk_a", "pan_a", "cv_a")\n'
            '    pan_auth_with("tk_a", "cv_a", 100)\n'
            '    bound_first("tk_b", "pan_b", "cv_b")\n'
            '    pan_auth_with("tk_b", "cv_b", 40)\n'
            '    assert hold_cents("au_a") == 100 and hold_cents("au_b") == 40\n'
        ),
        test_body_short="same — replay blocked; crypto one-time",
        obs3="replay extra-holds",
        obs4="replay blocked",
        obs5="hold once; used crypto; second crypto independent",
        fail_obs="FAILED test_replay_blocked - hold 10000 == 5000\n1 failed, 1 passed",
        skip_old=_naive("replay_cv", 'hold_auth(ev["token_id"], ev.get("cents", 0))', "counted every crypto replay")[1],
        skip_new='    if not replayed_today(ev["crypto"]):\n        hold_auth(ev["token_id"], ev.get("cents", 0))',
        obs7="second crypto ok; hides one-time.",
        still_fail_obs="FAILED if replay extra-held\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def replay_cv(ev):\n"
            "    if used_crypto(ev['crypto']):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_cv(ev['crypto']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    hold_auth(pan_auth_id(ev["token_id"]), ev.get("cents", 0))\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="replay blocked if crypto used",
        rewrite_hook=(
            "def bound_first(token_id, pan, crypto):\n"
            "    if not claim_tk2(token_id):\n"
            "        return existing_tk(token_id)\n"
            "    store_crypto(token_id, pan, crypto)\n"
            "    return token_id\n"
        ),
        rewrite_hook_obs="bind first",
        ddl=_ddl("till_nt_rep", "crypto", "  token_id text NOT NULL,\n  used bool NOT NULL DEFAULT true"),
        ddl_obs="PK crypto",
        test2_body=(
            "def test_second_crypto():\n"
            '    bound_first("tk_a", "pan_a", "cv_a")\n'
            '    pan_auth_with("tk_a", "cv_a", 100)\n'
            '    bound_first("tk_b", "pan_b", "cv_b")\n'
            '    pan_auth_with("tk_b", "cv_b", 40)\n'
            '    assert hold_cents("au_a") == 100 and hold_cents("au_b") == 40\n'
        ),
        xfail_label="replay after rotate should succeed",
        xfail_body=(
            "def test_replay_after_rotate():\n"
            '    bound_first("tk_p", "pan_p", "cv_p")\n'
            '    pan_auth_with("tk_p", "cv_p", 5000)\n'
            '    rotate_crypto("tk_p", "cv_p2")\n'
            '    replay_cv(rp("tk_p", crypto="cv_p2", cents=400))\n'
            '    assert hold_cents("au_p2") == 400\n'
        ),
        xfail_fail_obs="FAILED test_replay_after_rotate - no rotate path\n1 failed",
        xfail_old="def test_replay_after_rotate():",
        xfail_new='@pytest.mark.xfail(reason="handoff: cryptogram rotate then auth is a separate bind", strict=True)\ndef test_replay_after_rotate():',
        xfail_patch_obs="xfailed replay after rotate",
        goal="till-nt-rep cryptogram replay extra-held. Crypto one-time. Gate: tests/test_nt_rep.py.",
        plan="Skip auth if this cryptogram already replayed today.",
        outcome="Replay extra-held. Replay-day skip hid one-time. Plan change: used crypto blocks. Primary+second pass. Partial: rotate xfail handoff.",
    ),
)

