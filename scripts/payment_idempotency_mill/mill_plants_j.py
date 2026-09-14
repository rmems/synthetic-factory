"""Plants r144–r155: more ledger/fencing (not PSP webhook-vs-retrieve)."""

from mill_plants import _ok, _fail
from mill_plants_h import _ddl, _naive, _paths, _rg_obs

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def _ok_pair(
    *,
    slug,
    stem,
    fn,
    inner,
    comment,
    hook_fn,
    hook_body,
    test_fn,
    test_body,
    test2_body,
    table,
    pk,
    rg,
    surfaces,
    avoided,
    this_is,
    seed,
    first_apply,
    plan_change,
    step_note,
    skip_pred,
    verb,
    skip_label,
    obs3,
    obs4,
    obs5,
    fail_obs,
    obs7,
    still_fail_obs,
    rewrite_src,
    rewrite_src_obs,
    rewrite_hook,
    rewrite_hook_obs,
    extra_ddl,
    residual,
    grep_pat,
    grep_obs,
    goal,
    plan,
    outcome,
    skip_new,
    psql_rows,
    test_name,
    surface_read,
):
    src, skip = _naive(fn, inner, comment)
    return _ok(
        slug=slug,
        surfaces=surfaces,
        avoided=avoided,
        this_is=this_is,
        seed=seed,
        first_apply=first_apply,
        plan_change=plan_change,
        step_note=step_note,
        **_paths(stem),
        table=table,
        pk=pk,
        rg=rg,
        rg_obs=_rg_obs(stem, fn, hook_fn, test_fn),
        test_name=test_name,
        surface_read=surface_read,
        skip_pred=skip_pred,
        verb=verb,
        skip_label=skip_label,
        src_body=src,
        hook_body=hook_body,
        test_body=test_body,
        obs3=obs3,
        obs4=obs4,
        obs5=obs5,
        fail_obs=fail_obs,
        skip_old=skip,
        skip_new=skip_new,
        obs7=obs7,
        still_fail_obs=still_fail_obs,
        rewrite_src=rewrite_src,
        rewrite_src_obs=rewrite_src_obs,
        rewrite_hook=rewrite_hook,
        rewrite_hook_obs=rewrite_hook_obs,
        obs9="claim helper.",
        ddl=_ddl(table, pk, extra_ddl),
        ddl_obs=f"PK {pk}",
        test2_body=test2_body,
        psql_rows=psql_rows,
        residual=residual,
        grep_pat=grep_pat,
        grep_obs=grep_obs,
        goal=goal,
        plan=plan,
        outcome=outcome,
    )


def _fail_pair(
    *,
    slug,
    stem,
    fn,
    inner,
    comment,
    hook_fn,
    hook_body,
    test_fn,
    test_body,
    test2_body,
    table,
    pk,
    rg,
    surfaces,
    avoided,
    this_is,
    seed,
    first_apply,
    plan_change,
    step_note,
    next_note,
    skip_pred,
    verb,
    skip_label,
    obs3,
    obs4,
    obs5,
    fail_obs,
    obs7,
    still_fail_obs,
    rewrite_src,
    rewrite_src_obs,
    rewrite_hook,
    rewrite_hook_obs,
    extra_ddl,
    xfail_label,
    xfail_body,
    xfail_fail_obs,
    xfail_fn,
    xfail_reason,
    goal,
    plan,
    outcome,
    skip_new,
    test_name,
    surface_read,
    test_body_short,
):
    src, skip = _naive(fn, inner, comment)
    return _fail(
        slug=slug,
        surfaces=surfaces,
        avoided=avoided,
        this_is=this_is,
        seed=seed,
        first_apply=first_apply,
        plan_change=plan_change,
        step_note=step_note,
        next_note=next_note,
        **_paths(stem, fail=True),
        table=table,
        pk=pk,
        rg=rg,
        rg_obs=_rg_obs(stem, fn, hook_fn, test_fn),
        test_name=test_name,
        surface_read=surface_read,
        skip_pred=skip_pred,
        verb=verb,
        skip_label=skip_label,
        src_body=src,
        hook_body=hook_body,
        test_body=test_body,
        test_body_short=test_body_short,
        obs3=obs3,
        obs4=obs4,
        obs5=obs5,
        fail_obs=fail_obs,
        skip_old=skip,
        skip_new=skip_new,
        obs7=obs7,
        still_fail_obs=still_fail_obs,
        rewrite_src=rewrite_src,
        rewrite_src_obs=rewrite_src_obs,
        rewrite_hook=rewrite_hook,
        rewrite_hook_obs=rewrite_hook_obs,
        ddl=_ddl(table, pk, extra_ddl),
        ddl_obs=f"PK {pk}",
        test2_body=test2_body,
        xfail_label=xfail_label,
        xfail_body=xfail_body,
        xfail_fail_obs=xfail_fail_obs,
        xfail_old=f"def {xfail_fn}():",
        xfail_new=(
            f'@pytest.mark.xfail(reason="handoff: {xfail_reason}", strict=True)\n'
            f"def {xfail_fn}():"
        ),
        xfail_patch_obs=f"xfailed {xfail_label}",
        goal=goal,
        plan=plan,
        outcome=outcome,
    )


# r144 3DS challenge vs capture / challenge after captured
pair(
    _ok_pair(
        slug="threeds-challenge-vs-capture",
        stem="tds_cap",
        fn="on_tds",
        inner='fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        comment="counted every 3DS result",
        hook_fn="capture_tds",
        hook_body="def capture_tds(charge_id, cents):\n    ledger.credit(charge_id, cents)\n",
        test_fn="test_challenge_not_capture_double",
        test_body=(
            "def test_challenge_not_capture_double():\n"
            '    on_tds(td(result="Y", charge_id="ch_1", amount=5000))\n'
            '    on_tds(td(result="Y", charge_id="ch_1", amount=5000))\n'
            '    capture_tds("ch_1", 5000)\n'
            '    assert tds_flag("ch_1") == "Y" and fulfill_cents("ch_1") == 5000 and tds_rows("ch_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    capture_tds("ch_a", 100)\n'
            '    capture_tds("ch_b", 40)\n'
            '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
        ),
        test2_body=(
            "def test_second_charge():\n"
            '    capture_tds("ch_a", 100)\n'
            '    capture_tds("ch_b", 40)\n'
            '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
        ),
        table="till_tds_cap",
        pk="charge_id",
        rg="three_ds|challenge|pares|capture_tds",
        surfaces="3DS challenge result vs capture",
        avoided="r98 Worldpay notify; r121 Forter pre-auth. This is 3DS transStatus vs capture",
        this_is="3DS Y records; capture PK charge_id",
        seed="3DS Y + capture same charge_id",
        first_apply="charge challenged today",
        plan_change="3DS records; capture PK charge_id; N blocks",
        step_note="Challenge-day 6–7; PK 8–11; second charge 12–13.",
        skip_pred="this charge already challenged today",
        verb="fulfill",
        skip_label="charge-challenged-today skip",
        obs3="3DS Y and capture both fulfill",
        obs4="3DS records; capture PK charge_id",
        obs5="capture once; Y no extra; second charge adds",
        fail_obs="FAILED test_challenge_not_capture_double - tds_rows 3 == 1 or credited on Y\n1 failed, 1 passed",
        obs7="capture still fulfills; new charge same day dropped.",
        still_fail_obs="FAILED test_challenge_not_capture_double - Y still fulfills or capture adds\n1 failed, 1 passed",
        rewrite_src=(
            "def on_tds(ev):\n"
            '    if ev.get("result") in ("Y", "A", "N", "U"):\n'
            '        flag_tds(ev["charge_id"], ev["result"])\n'
            '        return {"ok": True, "tds": True}\n'
            '    return {"ok": True, "skip": True}\n'
        ),
        rewrite_src_obs="3DS records only",
        rewrite_hook=(
            "def capture_tds(charge_id, cents):\n"
            '    if flag_tds(charge_id) == "N":\n'
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_tds(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    fulfill_ch(charge_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK charge_id",
        extra_ddl="  tds_result text",
        residual="U after capture last-write",
        grep_pat="flag_tds",
        grep_obs="src/tds_cap.py: record only; no post-capture U reverse",
        goal="till-tds Y and capture both fulfilled ch_1. 3DS records; capture PK. Gate: tests/test_tds_cap.py.",
        plan="Skip fulfill if this charge already challenged today.",
        outcome="Y+capture double-fulfilled. Challenge-day skip left capture unguarded. Plan change: 3DS records; PK charge_id. Tests 2/2 + second charge + suite 8/8.",
        skip_new='    if not challenged_today(ev["charge_id"]):\n        fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        psql_rows="ch_1\nch_a\nch_b",
        test_name="challenge-not-capture-double test",
        surface_read="3DS challenge plus capture",
    ),
    _fail_pair(
        slug="tds-challenge-after-captured",
        stem="tds_late",
        fn="on_late_tds",
        inner='void_ch(ev["charge_id"], ev.get("amount", 0))',
        comment="counted every late 3DS N",
        hook_fn="already_cap",
        hook_body="def already_cap(charge_id, cents):\n    fulfill_ch(charge_id, cents)\n",
        test_fn="test_late_n_not_void",
        test_body=(
            "def test_late_n_not_void():\n"
            '    already_cap("ch_1", 5000)\n'
            '    on_late_tds(td(result="N", charge_id="ch_1", amount=5000))\n'
            '    on_late_tds(td(result="N", charge_id="ch_1", amount=5000))\n'
            '    assert fulfill_cents("ch_1") == 5000 and tds_flag("ch_1") == "N" and late_rows("ln_1") == 1\n'
            "\n"
            "def test_second_late():\n"
            '    already_cap("ch_a", 100)\n'
            '    on_late_tds(td(result="N", charge_id="ch_a", amount=100))\n'
            '    already_cap("ch_b", 40)\n'
            '    on_late_tds(td(result="N", charge_id="ch_b", amount=40))\n'
            '    assert tds_flag("ch_a") == "N" and tds_flag("ch_b") == "N"\n'
        ),
        test2_body=(
            "def test_second_late():\n"
            '    already_cap("ch_a", 100)\n'
            '    on_late_tds(td(result="N", charge_id="ch_a", amount=100))\n'
            '    already_cap("ch_b", 40)\n'
            '    on_late_tds(td(result="N", charge_id="ch_b", amount=40))\n'
            '    assert tds_flag("ch_a") == "N" and tds_flag("ch_b") == "N"\n'
        ),
        table="till_tds_late",
        pk="late_id",
        rg="late_tds|after_capture|void_ch",
        surfaces="late 3DS N after capture",
        avoided="r144 3DS vs capture; r107 Cybersource DM. This is late N must not void captured",
        this_is="late N records; capture stays",
        seed="capture then late 3DS N",
        first_apply="late N posted today",
        plan_change="late N PK records; capture stays",
        step_note="Late-day 6–7; PK 8–11; second 12–13; void xfail 15–17.",
        next_note="Unused: late N should void captured. Avoid late-N-today skip.",
        skip_pred="this late N already posted today",
        verb="void",
        skip_label="late-N-today skip",
        obs3="late N voids captured charge",
        obs4="late N records; capture stays",
        obs5="fulfill 5000; flag N; second late adds",
        fail_obs="FAILED test_late_n_not_void - fulfill 0 == 5000 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides record.",
        still_fail_obs="FAILED if late N voided capture (fulfill 0)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def on_late_tds(ev):\n"
            "    if not claim_late(ev.get('late_id') or ev['charge_id']+'_ln'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    flag_tds(ev["charge_id"], ev["result"])\n'
            '    return {"ok": True, "recorded": True}\n'
        ),
        rewrite_src_obs="claim late_id records N",
        rewrite_hook=(
            "def already_cap(charge_id, cents):\n"
            "    if not claim_tds2(charge_id):\n"
            "        return existing_cap(charge_id)\n"
            "    fulfill_ch(charge_id, cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="capture stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="late N should void captured",
        xfail_body=(
            "def test_late_n_voids():\n"
            '    already_cap("ch_p", 5000)\n'
            '    on_late_tds(td(result="N", charge_id="ch_p", amount=5000))\n'
            '    assert fulfill_cents("ch_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_n_voids - capture stayed; N recorded\n1 failed",
        xfail_fn="test_late_n_voids",
        xfail_reason="late 3DS N void vs record-only is a policy fork",
        goal="till-late late N voided captured ch_1. Late records. Gate: tests/test_tds_late.py.",
        plan="Skip void if this late N already posted today.",
        outcome="Late N voided capture. Late-day skip hid record. Plan change: late PK record. Primary+second pass. Partial: void xfail handoff.",
        skip_new='    if not late_today(ev["charge_id"]):\n        void_ch(ev["charge_id"], ev.get("amount", 0))',
        test_name="late-n-not-void test",
        surface_read="late 3DS N plus captured charge",
        test_body_short="same — late N records; capture stays",
    ),
)

# r145 surcharge snapshot vs capture / surcharge after capture
pair(
    _ok_pair(
        slug="surcharge-snapshot-vs-capture",
        stem="sur_cap",
        fn="book_sur",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every surcharge book",
        hook_fn="capture_prin",
        hook_body="def capture_prin(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_surcharge_not_principal_double",
        test_body=(
            "def test_surcharge_not_principal_double():\n"
            '    book_sur(su("su_1", charge="ch_1", cents=150))\n'
            '    book_sur(su("su_1", charge="ch_1", cents=150))\n'
            '    capture_prin("ch_1", 5000)\n'
            '    assert merch_cents("m_1") == 5150 and sur_cents("su_1") == 150 and sur_rows("su_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    book_sur(su("su_a", charge="ch_a", cents=3))\n'
            '    capture_prin("ch_a", 100)\n'
            '    book_sur(su("su_b", charge="ch_b", cents=1))\n'
            '    capture_prin("ch_b", 40)\n'
            '    assert merch_cents("m_a") == 103 and merch_cents("m_b") == 41\n'
        ),
        test2_body=(
            "def test_second_charge():\n"
            '    book_sur(su("su_a", charge="ch_a", cents=3))\n'
            '    capture_prin("ch_a", 100)\n'
            '    book_sur(su("su_b", charge="ch_b", cents=1))\n'
            '    capture_prin("ch_b", 40)\n'
            '    assert merch_cents("m_a") == 103 and merch_cents("m_b") == 41\n'
        ),
        table="till_sur_cap",
        pk="surcharge_id",
        rg="surcharge|principal|snapshot_bps",
        surfaces="surcharge snapshot vs principal capture",
        avoided="r127 tax snapshot; r134 tip adjust. This is surcharge_id vs principal",
        this_is="surcharge PK books fee; capture PK principal",
        seed="book surcharge + capture same charge",
        first_apply="surcharge booked today",
        plan_change="surcharge PK fee; capture principal once",
        step_note="Surcharge-day 6–7; PK 8–11; second charge 12–13.",
        skip_pred="this surcharge already booked today",
        verb="book",
        skip_label="surcharge-booked-today skip",
        obs3="surcharge and capture both credit full",
        obs4="surcharge fee; capture principal",
        obs5="merch 5150; sur once; second charge adds",
        fail_obs="FAILED test_surcharge_not_principal_double - merch 10000 or 5150 rows 3\n1 failed, 1 passed",
        obs7="capture still credits; new surcharge same day dropped.",
        still_fail_obs="FAILED test_surcharge_not_principal_double - capture unguarded or surcharge skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def book_sur(ev):\n"
            "    if not claim_sur(ev['surcharge_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    book_fee(ev["charge_id"], ev["cents"], sur=ev["surcharge_id"])\n'
            '    return {"ok": True, "sur": True}\n'
        ),
        rewrite_src_obs="claim surcharge_id books fee",
        rewrite_hook=(
            "def capture_prin(charge_id, cents):\n"
            "    if not claim_prin(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK charge_id principal",
        extra_ddl="  charge_id text UNIQUE",
        residual="surcharge bps after capture last-write",
        grep_pat="book_fee",
        grep_obs="src/sur_cap.py: claim then fee; no post-capture bps reverse",
        goal="till-sur surcharge and capture both moved full. Sur fee; capture principal. Gate: tests/test_sur_cap.py.",
        plan="Skip book if this surcharge already booked today.",
        outcome="Sur+capture doubled. Surcharge-day skip left capture unguarded. Plan change: sur PK + principal PK. Tests 2/2 + second charge + suite 8/8.",
        skip_new='    if not booked_today(ev["surcharge_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        psql_rows="su_1\nsu_a\nsu_b",
        test_name="surcharge-not-principal-double test",
        surface_read="surcharge snapshot plus principal capture",
    ),
    _fail_pair(
        slug="surcharge-after-capture",
        stem="sur_late",
        fn="late_sur",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every late surcharge",
        hook_fn="already_prin",
        hook_body="def already_prin(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_late_sur_not_add",
        test_body=(
            "def test_late_sur_not_add():\n"
            '    already_prin("ch_1", 5000)\n'
            '    late_sur(su("su_1", charge="ch_1", cents=150))\n'
            '    late_sur(su("su_1", charge="ch_1", cents=150))\n'
            '    assert merch_cents("m_1") == 5000 and recv_cents("m_1") == 150 and late_sur_rows("su_1") == 1\n'
            "\n"
            "def test_second_late_sur():\n"
            '    already_prin("ch_a", 100)\n'
            '    late_sur(su("su_a", charge="ch_a", cents=3))\n'
            '    already_prin("ch_b", 40)\n'
            '    late_sur(su("su_b", charge="ch_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        test2_body=(
            "def test_second_late_sur():\n"
            '    already_prin("ch_a", 100)\n'
            '    late_sur(su("su_a", charge="ch_a", cents=3))\n'
            '    already_prin("ch_b", 40)\n'
            '    late_sur(su("su_b", charge="ch_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        table="till_sur_late",
        pk="late_sur_id",
        rg="late_surcharge|after_capture|recv_sur",
        surfaces="late surcharge after principal captured",
        avoided="r145 sur vs capture; r127 tax after capture. This is late surcharge receivable",
        this_is="late surcharge opens receivable; does not rewrite capture",
        seed="capture then late surcharge",
        first_apply="late surcharge posted today",
        plan_change="late sur PK receivable; capture stays",
        step_note="Late-sur-day 6–7; PK 8–11; second 12–13; rewrite xfail 15–17.",
        next_note="Unused: late surcharge should rewrite capture. Avoid late-sur-today skip.",
        skip_pred="this late surcharge already posted today",
        verb="book",
        skip_label="late-surcharge-today skip",
        obs3="late surcharge rewrites captured principal",
        obs4="late sur receivable; capture stays",
        obs5="merch 5000; recv 150; second late adds",
        fail_obs="FAILED test_late_sur_not_add - merch 5150 == 5000 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides receivable.",
        still_fail_obs="FAILED if late sur rewrote capture (merch 5150)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_sur(ev):\n"
            "    if not claim_lsur(ev['surcharge_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], sur=ev["surcharge_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim late_sur opens receivable",
        rewrite_hook=(
            "def already_prin(charge_id, cents):\n"
            "    if not claim_prin2(charge_id):\n"
            "        return existing_prin(charge_id)\n"
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="capture stays",
        extra_ddl="  charge_id text NOT NULL,\n  recv_cents int NOT NULL",
        xfail_label="late surcharge should rewrite capture",
        xfail_body=(
            "def test_late_sur_rewrites():\n"
            '    already_prin("ch_p", 5000)\n'
            '    late_sur(su("su_p", charge="ch_p", cents=150))\n'
            '    assert merch_cents("m_p") == 5150 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_sur_rewrites - recv opened; capture not rewritten\n1 failed",
        xfail_fn="test_late_sur_rewrites",
        xfail_reason="late surcharge rewrite vs receivable is a policy fork",
        goal="till-lsur late surcharge rewrote capture. Late recv. Gate: tests/test_sur_late.py.",
        plan="Skip book if this late surcharge already posted today.",
        outcome="Late sur rewrote capture. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: rewrite xfail handoff.",
        skip_new='    if not late_sur_today(ev["surcharge_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        test_name="late-sur-not-add test",
        surface_read="late surcharge plus captured principal",
        test_body_short="same — late sur receivable; capture stays",
    ),
)

# r146 gift-card remainder vs capture / remainder after close
pair(
    _ok_pair(
        slug="giftcard-remainder-vs-capture",
        stem="gc_rem",
        fn="apply_gc",
        inner='debit_wallet(ev["card_id"], ev["cents"])',
        comment="counted every gift apply",
        hook_fn="capture_rest",
        hook_body="def capture_rest(charge_id, cents):\n    debit_wallet(charge_id, cents)\n",
        test_fn="test_gift_not_capture_double",
        test_body=(
            "def test_gift_not_capture_double():\n"
            '    apply_gc(gc("gc_1", charge="ch_1", cents=2000))\n'
            '    apply_gc(gc("gc_1", charge="ch_1", cents=2000))\n'
            '    capture_rest("ch_1", 3000)\n'
            '    assert wallet_cents("w_1") == 2000 and card_cents("ch_1") == 3000 and gc_rows("gc_1") == 1\n'
            "\n"
            "def test_second_card():\n"
            '    apply_gc(gc("gc_a", charge="ch_a", cents=40))\n'
            '    capture_rest("ch_a", 60)\n'
            '    apply_gc(gc("gc_b", charge="ch_b", cents=10))\n'
            '    capture_rest("ch_b", 30)\n'
            '    assert wallet_cents("w_a") == 40 and wallet_cents("w_b") == 10\n'
        ),
        test2_body=(
            "def test_second_card():\n"
            '    apply_gc(gc("gc_a", charge="ch_a", cents=40))\n'
            '    capture_rest("ch_a", 60)\n'
            '    apply_gc(gc("gc_b", charge="ch_b", cents=10))\n'
            '    capture_rest("ch_b", 30)\n'
            '    assert wallet_cents("w_a") == 40 and wallet_cents("w_b") == 10\n'
        ),
        table="till_gc_rem",
        pk="gift_id",
        rg="gift_card|remainder|apply_gc",
        surfaces="gift-card apply vs card remainder capture",
        avoided="r137 wallet topup vs spend; r142 installment. This is gift_id vs remainder",
        this_is="gift PK debits wallet; capture PK remainder",
        seed="apply gift + capture remainder same charge",
        first_apply="gift applied today",
        plan_change="gift PK wallet; capture remainder once",
        step_note="Gift-day 6–7; PK 8–11; second card 12–13.",
        skip_pred="this gift already applied today",
        verb="apply",
        skip_label="gift-applied-today skip",
        obs3="gift and remainder both debit wallet",
        obs4="gift wallet; capture remainder",
        obs5="wallet 2000; card 3000; second card adds",
        fail_obs="FAILED test_gift_not_capture_double - wallet 5000 or rows 3\n1 failed, 1 passed",
        obs7="remainder still debits wallet; new gift same day dropped.",
        still_fail_obs="FAILED test_gift_not_capture_double - remainder unguarded or gift skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def apply_gc(ev):\n"
            "    if not claim_gc(ev['gift_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_wallet(wallet_of(ev["card_id"]), ev["cents"], gift=ev["gift_id"])\n'
            '    return {"ok": True, "gift": True}\n'
        ),
        rewrite_src_obs="claim gift_id debits wallet",
        rewrite_hook=(
            "def capture_rest(charge_id, cents):\n"
            "    if not claim_rest(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_card(pan_of(charge_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK remainder on card",
        extra_ddl="  charge_id text UNIQUE",
        residual="gift expiry after remainder last-write",
        grep_pat="debit_wallet",
        grep_obs="src/gc_rem.py: claim then wallet; remainder on card",
        goal="till-gc gift and remainder both hit wallet. Gift PK; remainder card. Gate: tests/test_gc_rem.py.",
        plan="Skip apply if this gift already applied today.",
        outcome="Gift+remainder doubled on wallet. Gift-day skip left remainder unguarded. Plan change: gift PK + remainder PK. Tests 2/2 + second card + suite 8/8.",
        skip_new='    if not applied_today(ev["card_id"]):\n        debit_wallet(ev["card_id"], ev["cents"])',
        psql_rows="gc_1\ngc_a\ngc_b",
        test_name="gift-not-capture-double test",
        surface_read="gift-card apply plus remainder capture",
    ),
    _fail_pair(
        slug="gift-remainder-after-close",
        stem="gc_late",
        fn="late_gc",
        inner='debit_card(ev["charge_id"], ev["cents"])',
        comment="counted every late remainder",
        hook_fn="already_gift",
        hook_body="def already_gift(card_id, cents):\n    debit_wallet(card_id, cents)\n",
        test_fn="test_late_rem_not_card",
        test_body=(
            "def test_late_rem_not_card():\n"
            '    already_gift("gc_1", 2000)\n'
            '    late_gc(gc("rm_1", charge="ch_1", cents=3000))\n'
            '    late_gc(gc("rm_1", charge="ch_1", cents=3000))\n'
            '    assert wallet_cents("w_1") == 2000 and recv_cents("m_1") == 3000 and rem_rows("rm_1") == 1\n'
            "\n"
            "def test_second_rem():\n"
            '    already_gift("gc_a", 40)\n'
            '    late_gc(gc("rm_a", charge="ch_a", cents=60))\n'
            '    already_gift("gc_b", 10)\n'
            '    late_gc(gc("rm_b", charge="ch_b", cents=30))\n'
            '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        test2_body=(
            "def test_second_rem():\n"
            '    already_gift("gc_a", 40)\n'
            '    late_gc(gc("rm_a", charge="ch_a", cents=60))\n'
            '    already_gift("gc_b", 10)\n'
            '    late_gc(gc("rm_b", charge="ch_b", cents=30))\n'
            '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        table="till_gc_late",
        pk="rem_id",
        rg="late_remainder|after_close|recv_rem",
        surfaces="late remainder after gift window close",
        avoided="r146 gift vs remainder; r142 late installment. This is remainder receivable after close",
        this_is="late remainder opens receivable; gift stays",
        seed="gift then late remainder after close",
        first_apply="remainder posted today",
        plan_change="late rem PK receivable; gift stays",
        step_note="Rem-day 6–7; PK 8–11; second 12–13; card-debit xfail 15–17.",
        next_note="Unused: late remainder should debit card. Avoid remainder-today skip.",
        skip_pred="this remainder already posted today",
        verb="debit",
        skip_label="remainder-posted-today skip",
        obs3="late remainder debits card after close",
        obs4="late rem receivable; gift stays",
        obs5="wallet 2000; recv 3000; second rem adds",
        fail_obs="FAILED test_late_rem_not_card - card debit or rows 3\n1 failed, 1 passed",
        obs7="second rem ok; hides receivable.",
        still_fail_obs="FAILED if late rem debited card\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_gc(ev):\n"
            "    if not claim_rem(ev.get('rem_id') or ev['charge_id']+'_rm'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], rem=ev.get("rem_id"))\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim rem_id opens receivable",
        rewrite_hook=(
            "def already_gift(card_id, cents):\n"
            "    if not claim_gc2(card_id):\n"
            "        return existing_gc(card_id)\n"
            "    debit_wallet(wallet_of(card_id), cents)\n"
            "    return card_id\n"
        ),
        rewrite_hook_obs="gift stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="late remainder should debit card",
        xfail_body=(
            "def test_late_rem_debits_card():\n"
            '    already_gift("gc_p", 2000)\n'
            '    late_gc(gc("rm_p", charge="ch_p", cents=3000))\n'
            '    assert card_cents("ch_p") == 3000 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_rem_debits_card - recv opened; card not debited\n1 failed",
        xfail_fn="test_late_rem_debits_card",
        xfail_reason="late remainder card debit vs receivable is a policy fork",
        goal="till-gclate late remainder hit card after close. Late recv. Gate: tests/test_gc_late.py.",
        plan="Skip debit if this remainder already posted today.",
        outcome="Late rem hit card. Rem-day skip hid receivable. Plan change: rem PK recv. Primary+second pass. Partial: card-debit xfail handoff.",
        skip_new='    if not rem_today(ev["charge_id"]):\n        debit_card(ev["charge_id"], ev["cents"])',
        test_name="late-rem-not-card test",
        surface_read="late remainder plus closed gift",
        test_body_short="same — late rem receivable; gift stays",
    ),
)

# r147 BNPL merchant fund vs capture / fund after capture
pair(
    _ok_pair(
        slug="bnpl-fund-vs-capture",
        stem="bnpl_cap",
        fn="fund_bnpl",
        inner='credit_merch(ev["order_id"], ev["cents"])',
        comment="counted every BNPL fund",
        hook_fn="capture_bnpl",
        hook_body="def capture_bnpl(order_id, cents):\n    credit_merch(order_id, cents)\n",
        test_fn="test_fund_not_capture_double",
        test_body=(
            "def test_fund_not_capture_double():\n"
            '    fund_bnpl(bp("bp_1", order="or_1", cents=5000))\n'
            '    fund_bnpl(bp("bp_1", order="or_1", cents=5000))\n'
            '    capture_bnpl("or_1", 5000)\n'
            '    assert merch_cents("m_1") == 5000 and bnpl_rows("bp_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    fund_bnpl(bp("bp_a", order="or_a", cents=100))\n'
            '    capture_bnpl("or_a", 100)\n'
            '    fund_bnpl(bp("bp_b", order="or_b", cents=40))\n'
            '    capture_bnpl("or_b", 40)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        test2_body=(
            "def test_second_order():\n"
            '    fund_bnpl(bp("bp_a", order="or_a", cents=100))\n'
            '    capture_bnpl("or_a", 100)\n'
            '    fund_bnpl(bp("bp_b", order="or_b", cents=40))\n'
            '    capture_bnpl("or_b", 40)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        table="till_bnpl_cap",
        pk="bnpl_id",
        rg="bnpl.fund|klarna|afterpay|capture_bnpl",
        surfaces="BNPL merchant fund vs capture",
        avoided="r143 delayed vs instant; r138 hold-to-available. This is bnpl_id fund vs capture",
        this_is="BNPL PK funds merchant; capture no-ops",
        seed="BNPL fund + capture same order",
        first_apply="order funded today",
        plan_change="BNPL PK funds; capture no-op on claim",
        step_note="Fund-day 6–7; PK 8–11; second order 12–13.",
        skip_pred="this order already funded today",
        verb="fund",
        skip_label="order-funded-today skip",
        obs3="BNPL fund and capture both credit",
        obs4="BNPL funds; capture no-op",
        obs5="merch 5000; fund once; second order adds",
        fail_obs="FAILED test_fund_not_capture_double - merch 10000 or rows 3\n1 failed, 1 passed",
        obs7="capture still credits; new order same day dropped.",
        still_fail_obs="FAILED test_fund_not_capture_double - capture unguarded or fund skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def fund_bnpl(ev):\n"
            "    if not claim_bnpl(ev['bnpl_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_merch(merch_of_ord(ev["order_id"]), ev["cents"], bnpl=ev["bnpl_id"])\n'
            '    return {"ok": True, "funded": True}\n'
        ),
        rewrite_src_obs="claim bnpl_id funds merchant",
        rewrite_hook=(
            "def capture_bnpl(order_id, cents):\n"
            "    if funded_bnpl(order_id):\n"
            '        return {"ok": True, "noop": True}\n'
            "    if not claim_capb(order_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_ord(order_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="capture no-op if funded",
        extra_ddl="  order_id text UNIQUE",
        residual="BNPL fee after capture last-write",
        grep_pat="funded_bnpl",
        grep_obs="src/bnpl_cap.py: fund then no-op capture; no fee reverse",
        goal="till-bnpl fund and capture both credited or_1. BNPL PK; capture no-op. Gate: tests/test_bnpl_cap.py.",
        plan="Skip fund if this order already funded today.",
        outcome="Fund+capture doubled. Fund-day skip left capture unguarded. Plan change: BNPL PK + capture no-op. Tests 2/2 + second order + suite 8/8.",
        skip_new='    if not funded_today(ev["order_id"]):\n        credit_merch(ev["order_id"], ev["cents"])',
        psql_rows="bp_1\nbp_a\nbp_b",
        test_name="fund-not-capture-double test",
        surface_read="BNPL merchant fund plus capture",
    ),
    _fail_pair(
        slug="bnpl-fund-after-capture",
        stem="bnpl_late",
        fn="late_fund",
        inner='credit_merch(ev["order_id"], ev["cents"])',
        comment="counted every late BNPL fund",
        hook_fn="already_capb",
        hook_body="def already_capb(order_id, cents):\n    credit_merch(order_id, cents)\n",
        test_fn="test_late_fund_not_add",
        test_body=(
            "def test_late_fund_not_add():\n"
            '    already_capb("or_1", 5000)\n'
            '    late_fund(bp("bp_1", order="or_1", cents=5000))\n'
            '    late_fund(bp("bp_1", order="or_1", cents=5000))\n'
            '    assert merch_cents("m_1") == 5000 and bnpl_flag("or_1") == "funded" and late_bnpl_rows("bp_1") == 1\n'
            "\n"
            "def test_second_late_fund():\n"
            '    already_capb("or_a", 100)\n'
            '    late_fund(bp("bp_a", order="or_a", cents=100))\n'
            '    already_capb("or_b", 40)\n'
            '    late_fund(bp("bp_b", order="or_b", cents=40))\n'
            '    assert bnpl_flag("or_a") == "funded" and bnpl_flag("or_b") == "funded"\n'
        ),
        test2_body=(
            "def test_second_late_fund():\n"
            '    already_capb("or_a", 100)\n'
            '    late_fund(bp("bp_a", order="or_a", cents=100))\n'
            '    already_capb("or_b", 40)\n'
            '    late_fund(bp("bp_b", order="or_b", cents=40))\n'
            '    assert bnpl_flag("or_a") == "funded" and bnpl_flag("or_b") == "funded"\n'
        ),
        table="till_bnpl_late",
        pk="late_bnpl_id",
        rg="late_bnpl|after_capture|flag_funded",
        surfaces="late BNPL fund after capture",
        avoided="r147 BNPL fund vs capture; r143 instant after delay. This is late fund must not extra-credit",
        this_is="late fund flags; capture stays",
        seed="capture then late BNPL fund",
        first_apply="late fund posted today",
        plan_change="late fund PK flags; capture stays",
        step_note="Late-fund-day 6–7; PK 8–11; second 12–13; extra-credit xfail 15–17.",
        next_note="Unused: late fund should extra-credit. Avoid late-fund-today skip.",
        skip_pred="this late fund already posted today",
        verb="fund",
        skip_label="late-fund-today skip",
        obs3="late fund extra-credits merchant",
        obs4="late fund flags; capture stays",
        obs5="merch 5000; flagged; second late adds",
        fail_obs="FAILED test_late_fund_not_add - merch 10000 == 5000 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides flag.",
        still_fail_obs="FAILED if late fund extra-credited (merch 10000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_fund(ev):\n"
            "    if not claim_lbnpl(ev['bnpl_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    flag_bnpl(ev["order_id"], "funded")\n'
            '    return {"ok": True, "flagged": True}\n'
        ),
        rewrite_src_obs="claim late_bnpl flags",
        rewrite_hook=(
            "def already_capb(order_id, cents):\n"
            "    if not claim_capb2(order_id):\n"
            "        return existing_capb(order_id)\n"
            "    credit_merch(merch_of_ord(order_id), cents)\n"
            "    return order_id\n"
        ),
        rewrite_hook_obs="capture stays",
        extra_ddl="  order_id text UNIQUE",
        xfail_label="late fund should extra-credit",
        xfail_body=(
            "def test_late_fund_credits():\n"
            '    already_capb("or_p", 5000)\n'
            '    late_fund(bp("bp_p", order="or_p", cents=5000))\n'
            '    assert merch_cents("m_p") == 10000\n'
        ),
        xfail_fail_obs="FAILED test_late_fund_credits - flagged; merch stayed 5000\n1 failed",
        xfail_fn="test_late_fund_credits",
        xfail_reason="late BNPL fund extra-credit vs flag-only is a policy fork",
        goal="till-bnpllate late fund extra-credited or_1. Late flags. Gate: tests/test_bnpl_late.py.",
        plan="Skip fund if this late fund already posted today.",
        outcome="Late fund extra-credited. Late-day skip hid flag. Plan change: late PK flag. Primary+second pass. Partial: extra-credit xfail handoff.",
        skip_new='    if not late_fund_today(ev["order_id"]):\n        credit_merch(ev["order_id"], ev["cents"])',
        test_name="late-fund-not-add test",
        surface_read="late BNPL fund plus captured order",
        test_body_short="same — late fund flags; capture stays",
    ),
)
