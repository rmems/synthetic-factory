"""Plants r148–r155: more ledger/fencing (not PSP webhook-vs-retrieve)."""

from mill_plants_j import _ok_pair, _fail_pair

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def _std_ok_test(test_fn, apply_fn, apply_id, hook_fn, key, cents_a=5000, extra_a=0):
    total = cents_a + extra_a
    return (
        f"def {test_fn}():\n"
        f'    {apply_fn}({apply_id}("{apply_id[0]}_1", charge="{key}_1", cents={cents_a if extra_a == 0 else extra_a}))\n'
        f'    {apply_fn}({apply_id}("{apply_id[0]}_1", charge="{key}_1", cents={cents_a if extra_a == 0 else extra_a}))\n'
        f'    {hook_fn}("{key}_1", {cents_a})\n'
        f'    assert merch_cents("m_1") == {total} and rows("{apply_id[0]}_1") == 1\n'
        "\n"
        f"def test_second():\n"
        f'    {apply_fn}({apply_id}("{apply_id[0]}_a", charge="{key}_a", cents=4))\n'
        f'    {hook_fn}("{key}_a", 100)\n'
        f'    {apply_fn}({apply_id}("{apply_id[0]}_b", charge="{key}_b", cents=2))\n'
        f'    {hook_fn}("{key}_b", 40)\n'
        f'    assert merch_cents("m_a") == {100 + (0 if extra_a == 0 else 4)} and merch_cents("m_b") == {40 + (0 if extra_a == 0 else 2)}\n'
    )


# r148 MIT vs CIT recapture / MIT after CIT captured
pair(
    _ok_pair(
        slug="mit-vs-cit-capture",
        stem="mit_cit",
        fn="on_mit",
        inner='fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        comment="counted every MIT",
        hook_fn="on_cit",
        hook_body="def on_cit(charge_id, cents):\n    fulfill_ch(charge_id, cents)\n",
        test_fn="test_mit_not_cit_double",
        test_body=(
            "def test_mit_not_cit_double():\n"
            '    on_mit(mt(kind="MIT", charge_id="ch_1", amount=5000))\n'
            '    on_mit(mt(kind="MIT", charge_id="ch_1", amount=5000))\n'
            '    on_cit("ch_1", 5000)\n'
            '    assert mit_flag("ch_1") == "MIT" and fulfill_cents("ch_1") == 5000 and mit_rows("ch_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    on_cit("ch_a", 100)\n'
            '    on_cit("ch_b", 40)\n'
            '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
        ),
        test2_body=(
            "def test_second_charge():\n"
            '    on_cit("ch_a", 100)\n'
            '    on_cit("ch_b", 40)\n'
            '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
        ),
        table="till_mit_cit",
        pk="charge_id",
        rg="MIT|CIT|recurring|stored_credential",
        surfaces="MIT stored-credential vs CIT capture",
        avoided="r144 3DS vs capture; r98 Worldpay. This is MIT vs CIT same charge_id",
        this_is="MIT records; CIT PK captures once",
        seed="MIT + CIT same charge_id",
        first_apply="charge MIT'd today",
        plan_change="MIT records; CIT PK charge_id",
        step_note="MIT-day 6–7; PK 8–11; second charge 12–13.",
        skip_pred="this charge already MIT'd today",
        verb="fulfill",
        skip_label="charge-MIT-today skip",
        obs3="MIT and CIT both fulfill",
        obs4="MIT records; CIT PK",
        obs5="capture once; MIT no extra; second charge adds",
        fail_obs="FAILED test_mit_not_cit_double - mit_rows 3 == 1 or credited on MIT\n1 failed, 1 passed",
        obs7="CIT still fulfills; new charge same day dropped.",
        still_fail_obs="FAILED test_mit_not_cit_double - MIT still fulfills or CIT adds\n1 failed, 1 passed",
        rewrite_src=(
            "def on_mit(ev):\n"
            '    if ev.get("kind") == "MIT":\n'
            '        flag_mit(ev["charge_id"], "MIT")\n'
            '        return {"ok": True, "mit": True}\n'
            '    return {"ok": True, "skip": True}\n'
        ),
        rewrite_src_obs="MIT records only",
        rewrite_hook=(
            "def on_cit(charge_id, cents):\n"
            "    if not claim_cit(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    fulfill_ch(charge_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK charge_id",
        extra_ddl="  mit_kind text",
        residual="MIT network txn_id after CIT last-write",
        grep_pat="flag_mit",
        grep_obs="src/mit_cit.py: MIT records; CIT claims",
        goal="till-mit MIT and CIT both fulfilled ch_1. MIT records; CIT PK. Gate: tests/test_mit_cit.py.",
        plan="Skip fulfill if this charge already MIT'd today.",
        outcome="MIT+CIT double-fulfilled. MIT-day skip left CIT unguarded. Plan change: MIT records; PK charge_id. Tests 2/2 + second charge + suite 8/8.",
        skip_new='    if not mit_today(ev["charge_id"]):\n        fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        psql_rows="ch_1\nch_a\nch_b",
        test_name="mit-not-cit-double test",
        surface_read="MIT stored-credential plus CIT capture",
    ),
    _fail_pair(
        slug="mit-after-cit-captured",
        stem="mit_late",
        fn="late_mit",
        inner='fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        comment="counted every late MIT",
        hook_fn="already_cit",
        hook_body="def already_cit(charge_id, cents):\n    fulfill_ch(charge_id, cents)\n",
        test_fn="test_late_mit_not_add",
        test_body=(
            "def test_late_mit_not_add():\n"
            '    already_cit("ch_1", 5000)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_1", amount=5000))\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_1", amount=5000))\n'
            '    assert fulfill_cents("ch_1") == 5000 and mit_flag("ch_1") == "MIT" and late_mit_rows("lm_1") == 1\n'
            "\n"
            "def test_second_late_mit():\n"
            '    already_cit("ch_a", 100)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_a", amount=100))\n'
            '    already_cit("ch_b", 40)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_b", amount=40))\n'
            '    assert mit_flag("ch_a") == "MIT" and mit_flag("ch_b") == "MIT"\n'
        ),
        test2_body=(
            "def test_second_late_mit():\n"
            '    already_cit("ch_a", 100)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_a", amount=100))\n'
            '    already_cit("ch_b", 40)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_b", amount=40))\n'
            '    assert mit_flag("ch_a") == "MIT" and mit_flag("ch_b") == "MIT"\n'
        ),
        table="till_mit_late",
        pk="late_mit_id",
        rg="late_mit|after_cit|recurring",
        surfaces="late MIT after CIT captured",
        avoided="r148 MIT vs CIT; r144 late 3DS. This is late MIT must not extra-fulfill",
        this_is="late MIT flags; CIT stays",
        seed="CIT then late MIT",
        first_apply="late MIT posted today",
        plan_change="late MIT PK flags; CIT stays",
        step_note="Late-MIT-day 6–7; PK 8–11; second 12–13; extra xfail 15–17.",
        next_note="Unused: late MIT should extra-fulfill. Avoid late-MIT-today skip.",
        skip_pred="this late MIT already posted today",
        verb="fulfill",
        skip_label="late-MIT-today skip",
        obs3="late MIT extra-fulfills",
        obs4="late MIT flags; CIT stays",
        obs5="fulfill 5000; flagged; second late adds",
        fail_obs="FAILED test_late_mit_not_add - fulfill 10000 == 5000 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides flag.",
        still_fail_obs="FAILED if late MIT extra-fulfilled (10000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_mit(ev):\n"
            "    if not claim_lmit(ev.get('late_mit_id') or ev['charge_id']+'_lm'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    flag_mit(ev["charge_id"], "MIT")\n'
            '    return {"ok": True, "flagged": True}\n'
        ),
        rewrite_src_obs="claim late_mit flags",
        rewrite_hook=(
            "def already_cit(charge_id, cents):\n"
            "    if not claim_cit2(charge_id):\n"
            "        return existing_cit(charge_id)\n"
            "    fulfill_ch(charge_id, cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="CIT stays",
        extra_ddl="  charge_id text UNIQUE",
        xfail_label="late MIT should extra-fulfill",
        xfail_body=(
            "def test_late_mit_credits():\n"
            '    already_cit("ch_p", 5000)\n'
            '    late_mit(mt(kind="MIT", charge_id="ch_p", amount=5000))\n'
            '    assert fulfill_cents("ch_p") == 10000\n'
        ),
        xfail_fail_obs="FAILED test_late_mit_credits - flagged; fulfill stayed 5000\n1 failed",
        xfail_fn="test_late_mit_credits",
        xfail_reason="late MIT extra-fulfill vs flag-only is a policy fork",
        goal="till-mitlate late MIT extra-fulfilled ch_1. Late flags. Gate: tests/test_mit_late.py.",
        plan="Skip fulfill if this late MIT already posted today.",
        outcome="Late MIT extra-fulfilled. Late-day skip hid flag. Plan change: late PK flag. Primary+second pass. Partial: extra xfail handoff.",
        skip_new='    if not late_mit_today(ev["charge_id"]):\n        fulfill_ch(ev["charge_id"], ev.get("amount", 0))',
        test_name="late-mit-not-add test",
        surface_read="late MIT plus CIT capture",
        test_body_short="same — late MIT flags; CIT stays",
    ),
)

# r149 partial capture vs remainder / remainder after auth expire
pair(
    _ok_pair(
        slug="partial-capture-vs-remainder",
        stem="pcap_rem",
        fn="part_cap",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every partial capture",
        hook_fn="cap_rest",
        hook_body="def cap_rest(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_partial_not_rest_double",
        test_body=(
            "def test_partial_not_rest_double():\n"
            '    part_cap(pc("pc_1", charge="ch_1", cents=2000))\n'
            '    part_cap(pc("pc_1", charge="ch_1", cents=2000))\n'
            '    cap_rest("ch_1", 3000)\n'
            '    assert merch_cents("m_1") == 5000 and pcap_rows("pc_1") == 1\n'
            "\n"
            "def test_second_auth():\n"
            '    part_cap(pc("pc_a", charge="ch_a", cents=40))\n'
            '    cap_rest("ch_a", 60)\n'
            '    part_cap(pc("pc_b", charge="ch_b", cents=10))\n'
            '    cap_rest("ch_b", 30)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        test2_body=(
            "def test_second_auth():\n"
            '    part_cap(pc("pc_a", charge="ch_a", cents=40))\n'
            '    cap_rest("ch_a", 60)\n'
            '    part_cap(pc("pc_b", charge="ch_b", cents=10))\n'
            '    cap_rest("ch_b", 30)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        table="till_pcap_rem",
        pk="pcap_id",
        rg="partial_capture|remainder|auth_open",
        surfaces="partial capture vs remainder capture",
        avoided="r146 gift remainder; r142 installment. This is pcap_id vs remainder",
        this_is="partial PK; remainder PK leftover",
        seed="partial capture + remainder same auth",
        first_apply="partial captured today",
        plan_change="partial PK; remainder leftover once",
        step_note="Partial-day 6–7; PK 8–11; second auth 12–13.",
        skip_pred="this partial already captured today",
        verb="capture",
        skip_label="partial-captured-today skip",
        obs3="partial and remainder both credit full",
        obs4="partial PK; remainder leftover",
        obs5="merch 5000; partial once; second auth adds",
        fail_obs="FAILED test_partial_not_rest_double - merch 7000 or 10000 or rows 3\n1 failed, 1 passed",
        obs7="remainder still credits; new partial same day dropped.",
        still_fail_obs="FAILED test_partial_not_rest_double - remainder unguarded or partial skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def part_cap(ev):\n"
            "    if not claim_pcap(ev['pcap_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_merch(merch_of_ch(ev["charge_id"]), ev["cents"], pcap=ev["pcap_id"])\n'
            '    return {"ok": True, "partial": True}\n'
        ),
        rewrite_src_obs="claim pcap_id books partial",
        rewrite_hook=(
            "def cap_rest(charge_id, cents):\n"
            "    if not claim_rest2(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK remainder",
        extra_ddl="  charge_id text UNIQUE",
        residual="auth expiry after remainder last-write",
        grep_pat="claim_rest2",
        grep_obs="src/pcap_rem.py: partial then remainder; no expiry reverse",
        goal="till-pcap partial and remainder both credited. Partial PK; remainder PK. Gate: tests/test_pcap_rem.py.",
        plan="Skip capture if this partial already captured today.",
        outcome="Partial+remainder doubled. Partial-day skip left remainder unguarded. Plan change: pcap PK + remainder PK. Tests 2/2 + second auth + suite 8/8.",
        skip_new='    if not pcap_today(ev["charge_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        psql_rows="pc_1\npc_a\npc_b",
        test_name="partial-not-rest-double test",
        surface_read="partial capture plus remainder",
    ),
    _fail_pair(
        slug="remainder-after-auth-expire",
        stem="pcap_exp",
        fn="late_rest",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every late remainder",
        hook_fn="already_pcap",
        hook_body="def already_pcap(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_late_rest_not_add",
        test_body=(
            "def test_late_rest_not_add():\n"
            '    already_pcap("ch_1", 2000)\n'
            '    late_rest(pc("rm_1", charge="ch_1", cents=3000))\n'
            '    late_rest(pc("rm_1", charge="ch_1", cents=3000))\n'
            '    assert merch_cents("m_1") == 2000 and recv_cents("m_1") == 3000 and exp_rows("rm_1") == 1\n'
            "\n"
            "def test_second_exp():\n"
            '    already_pcap("ch_a", 40)\n'
            '    late_rest(pc("rm_a", charge="ch_a", cents=60))\n'
            '    already_pcap("ch_b", 10)\n'
            '    late_rest(pc("rm_b", charge="ch_b", cents=30))\n'
            '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        test2_body=(
            "def test_second_exp():\n"
            '    already_pcap("ch_a", 40)\n'
            '    late_rest(pc("rm_a", charge="ch_a", cents=60))\n'
            '    already_pcap("ch_b", 10)\n'
            '    late_rest(pc("rm_b", charge="ch_b", cents=30))\n'
            '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        table="till_pcap_exp",
        pk="exp_id",
        rg="auth_expired|late_remainder|recv_exp",
        surfaces="remainder after auth expired",
        avoided="r149 partial vs remainder; r146 gift late rem. This is remainder after expiry receivable",
        this_is="late remainder opens receivable; partial stays",
        seed="partial then remainder after expiry",
        first_apply="remainder posted today",
        plan_change="late rem PK receivable; partial stays",
        step_note="Exp-day 6–7; PK 8–11; second 12–13; extra-credit xfail 15–17.",
        next_note="Unused: expired remainder should still capture. Avoid remainder-today skip.",
        skip_pred="this remainder already posted today",
        verb="capture",
        skip_label="remainder-posted-today skip",
        obs3="late remainder extra-credits after expiry",
        obs4="late rem receivable; partial stays",
        obs5="merch 2000; recv 3000; second exp adds",
        fail_obs="FAILED test_late_rest_not_add - merch 5000 == 2000 or rows 3\n1 failed, 1 passed",
        obs7="second exp ok; hides receivable.",
        still_fail_obs="FAILED if late rem extra-credited (merch 5000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_rest(ev):\n"
            "    if not claim_exp(ev.get('exp_id') or ev['charge_id']+'_ex'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], exp=ev.get("exp_id"))\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim exp_id opens receivable",
        rewrite_hook=(
            "def already_pcap(charge_id, cents):\n"
            "    if not claim_pcap2(charge_id):\n"
            "        return existing_pcap(charge_id)\n"
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="partial stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="expired remainder should still capture",
        xfail_body=(
            "def test_exp_still_captures():\n"
            '    already_pcap("ch_p", 2000)\n'
            '    late_rest(pc("rm_p", charge="ch_p", cents=3000))\n'
            '    assert merch_cents("m_p") == 5000 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_exp_still_captures - recv opened; merch stayed 2000\n1 failed",
        xfail_fn="test_exp_still_captures",
        xfail_reason="expired remainder capture vs receivable is a policy fork",
        goal="till-pcapexp late remainder extra-credited after expiry. Late recv. Gate: tests/test_pcap_exp.py.",
        plan="Skip capture if this remainder already posted today.",
        outcome="Late rem extra-credited. Rem-day skip hid receivable. Plan change: exp PK recv. Primary+second pass. Partial: still-capture xfail handoff.",
        skip_new='    if not rem_today(ev["charge_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        test_name="late-rest-not-add test",
        surface_read="late remainder plus expired auth",
        test_body_short="same — late rem receivable; partial stays",
    ),
)

# r150 account updater vs stored PAN / PAN after updater
pair(
    _ok_pair(
        slug="account-updater-vs-pan",
        stem="au_pan",
        fn="on_au",
        inner='charge_pan(ev["token"], ev.get("amount", 0))',
        comment="counted every updater",
        hook_fn="charge_stored",
        hook_body="def charge_stored(token, cents):\n    charge_pan(token, cents)\n",
        test_fn="test_updater_not_charge_double",
        test_body=(
            "def test_updater_not_charge_double():\n"
            '    on_au(au(token="tok_1", pan="pan_new", amount=5000))\n'
            '    on_au(au(token="tok_1", pan="pan_new", amount=5000))\n'
            '    charge_stored("tok_1", 5000)\n'
            '    assert pan_of("tok_1") == "pan_new" and fulfill_cents("tok_1") == 5000 and au_rows("tok_1") == 1\n'
            "\n"
            "def test_second_token():\n"
            '    charge_stored("tok_a", 100)\n'
            '    charge_stored("tok_b", 40)\n'
            '    assert fulfill_cents("tok_a") == 100 and fulfill_cents("tok_b") == 40\n'
        ),
        test2_body=(
            "def test_second_token():\n"
            '    charge_stored("tok_a", 100)\n'
            '    charge_stored("tok_b", 40)\n'
            '    assert fulfill_cents("tok_a") == 100 and fulfill_cents("tok_b") == 40\n'
        ),
        table="till_au_pan",
        pk="token",
        rg="account_updater|stored_pan|network_token",
        surfaces="account updater vs stored PAN charge",
        avoided="r148 MIT vs CIT; r137 wallet. This is updater token vs PAN charge",
        this_is="updater records PAN; charge PK token",
        seed="updater + stored charge same token",
        first_apply="token updated today",
        plan_change="updater records PAN; charge PK token",
        step_note="Updater-day 6–7; PK 8–11; second token 12–13.",
        skip_pred="this token already updated today",
        verb="charge",
        skip_label="token-updated-today skip",
        obs3="updater and stored charge both fulfill",
        obs4="updater records PAN; charge PK",
        obs5="charge once; updater no extra; second token adds",
        fail_obs="FAILED test_updater_not_charge_double - au_rows 3 == 1 or credited on updater\n1 failed, 1 passed",
        obs7="stored charge still fulfills; new token same day dropped.",
        still_fail_obs="FAILED test_updater_not_charge_double - updater still charges or stored adds\n1 failed, 1 passed",
        rewrite_src=(
            "def on_au(ev):\n"
            '    store_pan(ev["token"], ev["pan"])\n'
            '    return {"ok": True, "updated": True}\n'
        ),
        rewrite_src_obs="updater records PAN only",
        rewrite_hook=(
            "def charge_stored(token, cents):\n"
            "    if not claim_tok(token):\n"
            '        return {"ok": True, "dup": True}\n'
            "    charge_pan(pan_of(token), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK token",
        extra_ddl="  pan text",
        residual="updater reason code after charge last-write",
        grep_pat="store_pan",
        grep_obs="src/au_pan.py: record PAN; charge claims token",
        goal="till-au updater and stored charge both fulfilled tok_1. Updater records; charge PK. Gate: tests/test_au_pan.py.",
        plan="Skip charge if this token already updated today.",
        outcome="Updater+charge double-fulfilled. Updater-day skip left charge unguarded. Plan change: record PAN; PK token. Tests 2/2 + second token + suite 8/8.",
        skip_new='    if not updated_today(ev["token"]):\n        charge_pan(ev["token"], ev.get("amount", 0))',
        psql_rows="tok_1\ntok_a\ntok_b",
        test_name="updater-not-charge-double test",
        surface_read="account updater plus stored PAN charge",
    ),
    _fail_pair(
        slug="pan-charge-after-updater",
        stem="au_late",
        fn="late_pan",
        inner='charge_pan(ev["token"], ev.get("amount", 0))',
        comment="counted every late PAN charge",
        hook_fn="already_au",
        hook_body="def already_au(token, pan):\n    store_pan(token, pan)\n",
        test_fn="test_late_pan_not_add",
        test_body=(
            "def test_late_pan_not_add():\n"
            '    already_au("tok_1", "pan_new")\n'
            '    late_pan(au(token="tok_1", pan="pan_new", amount=5000))\n'
            '    late_pan(au(token="tok_1", pan="pan_new", amount=5000))\n'
            '    assert pan_of("tok_1") == "pan_new" and fulfill_cents("tok_1") == 0 and late_au_rows("la_1") == 1\n'
            "\n"
            "def test_second_late_au():\n"
            '    already_au("tok_a", "pan_a")\n'
            '    late_pan(au(token="tok_a", pan="pan_a", amount=100))\n'
            '    already_au("tok_b", "pan_b")\n'
            '    late_pan(au(token="tok_b", pan="pan_b", amount=40))\n'
            '    assert pan_of("tok_a") == "pan_a" and pan_of("tok_b") == "pan_b"\n'
        ),
        test2_body=(
            "def test_second_late_au():\n"
            '    already_au("tok_a", "pan_a")\n'
            '    late_pan(au(token="tok_a", pan="pan_a", amount=100))\n'
            '    already_au("tok_b", "pan_b")\n'
            '    late_pan(au(token="tok_b", pan="pan_b", amount=40))\n'
            '    assert pan_of("tok_a") == "pan_a" and pan_of("tok_b") == "pan_b"\n'
        ),
        table="till_au_late",
        pk="late_au_id",
        rg="late_pan|after_updater|charge_old_pan",
        surfaces="PAN charge after updater already stored",
        avoided="r150 updater vs PAN; r148 late MIT. This is late PAN must not charge",
        this_is="late PAN records; updater stays",
        seed="updater then late PAN charge",
        first_apply="late PAN posted today",
        plan_change="late PAN PK records; updater stays",
        step_note="Late-PAN-day 6–7; PK 8–11; second 12–13; charge xfail 15–17.",
        next_note="Unused: late PAN should charge new PAN. Avoid late-PAN-today skip.",
        skip_pred="this late PAN already posted today",
        verb="charge",
        skip_label="late-PAN-today skip",
        obs3="late PAN charges after updater",
        obs4="late PAN records; updater stays",
        obs5="pan_new; fulfill 0; second late adds",
        fail_obs="FAILED test_late_pan_not_add - fulfill 5000 == 0 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides record.",
        still_fail_obs="FAILED if late PAN charged (fulfill 5000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_pan(ev):\n"
            "    if not claim_lau(ev.get('late_au_id') or ev['token']+'_la'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_pan(ev["token"], ev["pan"])\n'
            '    return {"ok": True, "recorded": True}\n'
        ),
        rewrite_src_obs="claim late_au records",
        rewrite_hook=(
            "def already_au(token, pan):\n"
            "    if not claim_tok2(token):\n"
            "        return existing_tok(token)\n"
            "    store_pan(token, pan)\n"
            "    return token\n"
        ),
        rewrite_hook_obs="updater stays",
        extra_ddl="  token text UNIQUE",
        xfail_label="late PAN should charge new PAN",
        xfail_body=(
            "def test_late_pan_charges():\n"
            '    already_au("tok_p", "pan_new")\n'
            '    late_pan(au(token="tok_p", pan="pan_new", amount=5000))\n'
            '    assert fulfill_cents("tok_p") == 5000\n'
        ),
        xfail_fail_obs="FAILED test_late_pan_charges - recorded; fulfill stayed 0\n1 failed",
        xfail_fn="test_late_pan_charges",
        xfail_reason="late PAN charge vs record-only is a policy fork",
        goal="till-aulate late PAN charged tok_1. Late records. Gate: tests/test_au_late.py.",
        plan="Skip charge if this late PAN already posted today.",
        outcome="Late PAN charged. Late-day skip hid record. Plan change: late PK record. Primary+second pass. Partial: charge xfail handoff.",
        skip_new='    if not late_pan_today(ev["token"]):\n        charge_pan(ev["token"], ev.get("amount", 0))',
        test_name="late-pan-not-add test",
        surface_read="late PAN plus stored updater",
        test_body_short="same — late PAN records; updater stays",
    ),
)

# r151 convenience fee vs principal / fee after principal
pair(
    _ok_pair(
        slug="conv-fee-vs-principal",
        stem="cfee_pr",
        fn="book_cfee",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every convenience fee",
        hook_fn="cap_prin2",
        hook_body="def cap_prin2(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_cfee_not_prin_double",
        test_body=(
            "def test_cfee_not_prin_double():\n"
            '    book_cfee(cf("cf_1", charge="ch_1", cents=99))\n'
            '    book_cfee(cf("cf_1", charge="ch_1", cents=99))\n'
            '    cap_prin2("ch_1", 5000)\n'
            '    assert merch_cents("m_1") == 5099 and cfee_rows("cf_1") == 1\n'
            "\n"
            "def test_second_cfee():\n"
            '    book_cfee(cf("cf_a", charge="ch_a", cents=3))\n'
            '    cap_prin2("ch_a", 100)\n'
            '    book_cfee(cf("cf_b", charge="ch_b", cents=1))\n'
            '    cap_prin2("ch_b", 40)\n'
            '    assert merch_cents("m_a") == 103 and merch_cents("m_b") == 41\n'
        ),
        test2_body=(
            "def test_second_cfee():\n"
            '    book_cfee(cf("cf_a", charge="ch_a", cents=3))\n'
            '    cap_prin2("ch_a", 100)\n'
            '    book_cfee(cf("cf_b", charge="ch_b", cents=1))\n'
            '    cap_prin2("ch_b", 40)\n'
            '    assert merch_cents("m_a") == 103 and merch_cents("m_b") == 41\n'
        ),
        table="till_cfee_pr",
        pk="cfee_id",
        rg="convenience_fee|principal|cfee",
        surfaces="convenience fee vs principal capture",
        avoided="r145 surcharge vs capture; r134 tip. This is cfee_id vs principal",
        this_is="cfee PK books fee; capture PK principal",
        seed="book convenience fee + capture same charge",
        first_apply="cfee booked today",
        plan_change="cfee PK fee; capture principal once",
        step_note="Cfee-day 6–7; PK 8–11; second charge 12–13.",
        skip_pred="this cfee already booked today",
        verb="book",
        skip_label="cfee-booked-today skip",
        obs3="cfee and capture both credit full",
        obs4="cfee fee; capture principal",
        obs5="merch 5099; cfee once; second charge adds",
        fail_obs="FAILED test_cfee_not_prin_double - merch 10000 or rows 3\n1 failed, 1 passed",
        obs7="capture still credits; new cfee same day dropped.",
        still_fail_obs="FAILED test_cfee_not_prin_double - capture unguarded or cfee skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def book_cfee(ev):\n"
            "    if not claim_cfee(ev['cfee_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    book_fee(ev["charge_id"], ev["cents"], cfee=ev["cfee_id"])\n'
            '    return {"ok": True, "cfee": True}\n'
        ),
        rewrite_src_obs="claim cfee_id books fee",
        rewrite_hook=(
            "def cap_prin2(charge_id, cents):\n"
            "    if not claim_prin3(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK principal",
        extra_ddl="  charge_id text UNIQUE",
        residual="cfee tax after principal last-write",
        grep_pat="book_fee",
        grep_obs="src/cfee_pr.py: claim then fee; no tax reverse",
        goal="till-cfee convenience fee and capture both moved. Cfee PK; principal PK. Gate: tests/test_cfee_pr.py.",
        plan="Skip book if this cfee already booked today.",
        outcome="Cfee+capture doubled. Cfee-day skip left capture unguarded. Plan change: cfee PK + principal PK. Tests 2/2 + second charge + suite 8/8.",
        skip_new='    if not cfee_today(ev["cfee_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        psql_rows="cf_1\ncf_a\ncf_b",
        test_name="cfee-not-prin-double test",
        surface_read="convenience fee plus principal capture",
    ),
    _fail_pair(
        slug="cfee-after-principal",
        stem="cfee_late",
        fn="late_cfee",
        inner='credit_merch(ev["charge_id"], ev["cents"])',
        comment="counted every late cfee",
        hook_fn="already_prin3",
        hook_body="def already_prin3(charge_id, cents):\n    credit_merch(charge_id, cents)\n",
        test_fn="test_late_cfee_not_add",
        test_body=(
            "def test_late_cfee_not_add():\n"
            '    already_prin3("ch_1", 5000)\n'
            '    late_cfee(cf("cf_1", charge="ch_1", cents=99))\n'
            '    late_cfee(cf("cf_1", charge="ch_1", cents=99))\n'
            '    assert merch_cents("m_1") == 5000 and recv_cents("m_1") == 99 and late_cfee_rows("cf_1") == 1\n'
            "\n"
            "def test_second_late_cfee():\n"
            '    already_prin3("ch_a", 100)\n'
            '    late_cfee(cf("cf_a", charge="ch_a", cents=3))\n'
            '    already_prin3("ch_b", 40)\n'
            '    late_cfee(cf("cf_b", charge="ch_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        test2_body=(
            "def test_second_late_cfee():\n"
            '    already_prin3("ch_a", 100)\n'
            '    late_cfee(cf("cf_a", charge="ch_a", cents=3))\n'
            '    already_prin3("ch_b", 40)\n'
            '    late_cfee(cf("cf_b", charge="ch_b", cents=1))\n'
            '    assert recv_cents("m_a") == 3 and recv_cents("m_b") == 1\n'
        ),
        table="till_cfee_late",
        pk="late_cfee_id",
        rg="late_cfee|after_principal|recv_cfee",
        surfaces="late convenience fee after principal captured",
        avoided="r151 cfee vs principal; r145 late surcharge. This is late cfee receivable",
        this_is="late cfee opens receivable; principal stays",
        seed="capture then late convenience fee",
        first_apply="late cfee posted today",
        plan_change="late cfee PK receivable; principal stays",
        step_note="Late-cfee-day 6–7; PK 8–11; second 12–13; rewrite xfail 15–17.",
        next_note="Unused: late cfee should rewrite capture. Avoid late-cfee-today skip.",
        skip_pred="this late cfee already posted today",
        verb="book",
        skip_label="late-cfee-today skip",
        obs3="late cfee rewrites captured principal",
        obs4="late cfee receivable; principal stays",
        obs5="merch 5000; recv 99; second late adds",
        fail_obs="FAILED test_late_cfee_not_add - merch 5099 == 5000 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides receivable.",
        still_fail_obs="FAILED if late cfee rewrote capture (merch 5099)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_cfee(ev):\n"
            "    if not claim_lcfee(ev['cfee_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], cfee=ev["cfee_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim late_cfee opens receivable",
        rewrite_hook=(
            "def already_prin3(charge_id, cents):\n"
            "    if not claim_prin4(charge_id):\n"
            "        return existing_prin(charge_id)\n"
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="principal stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="late cfee should rewrite capture",
        xfail_body=(
            "def test_late_cfee_rewrites():\n"
            '    already_prin3("ch_p", 5000)\n'
            '    late_cfee(cf("cf_p", charge="ch_p", cents=99))\n'
            '    assert merch_cents("m_p") == 5099 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_cfee_rewrites - recv opened; capture not rewritten\n1 failed",
        xfail_fn="test_late_cfee_rewrites",
        xfail_reason="late cfee rewrite vs receivable is a policy fork",
        goal="till-cfeelate late cfee rewrote capture. Late recv. Gate: tests/test_cfee_late.py.",
        plan="Skip book if this late cfee already posted today.",
        outcome="Late cfee rewrote capture. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: rewrite xfail handoff.",
        skip_new='    if not late_cfee_today(ev["cfee_id"]):\n        credit_merch(ev["charge_id"], ev["cents"])',
        test_name="late-cfee-not-add test",
        surface_read="late convenience fee plus captured principal",
        test_body_short="same — late cfee receivable; principal stays",
    ),
)

# r152 store-credit vs cash / credit after cash
pair(
    _ok_pair(
        slug="store-credit-vs-cash",
        stem="sc_cash",
        fn="apply_sc",
        inner='debit_credit(ev["credit_id"], ev["cents"])',
        comment="counted every store-credit apply",
        hook_fn="take_cash",
        hook_body="def take_cash(charge_id, cents):\n    debit_credit(charge_id, cents)\n",
        test_fn="test_credit_not_cash_double",
        test_body=(
            "def test_credit_not_cash_double():\n"
            '    apply_sc(sc("sc_1", charge="ch_1", cents=2000))\n'
            '    apply_sc(sc("sc_1", charge="ch_1", cents=2000))\n'
            '    take_cash("ch_1", 3000)\n'
            '    assert credit_cents("w_1") == 2000 and cash_cents("ch_1") == 3000 and sc_rows("sc_1") == 1\n'
            "\n"
            "def test_second_credit():\n"
            '    apply_sc(sc("sc_a", charge="ch_a", cents=40))\n'
            '    take_cash("ch_a", 60)\n'
            '    apply_sc(sc("sc_b", charge="ch_b", cents=10))\n'
            '    take_cash("ch_b", 30)\n'
            '    assert credit_cents("w_a") == 40 and credit_cents("w_b") == 10\n'
        ),
        test2_body=(
            "def test_second_credit():\n"
            '    apply_sc(sc("sc_a", charge="ch_a", cents=40))\n'
            '    take_cash("ch_a", 60)\n'
            '    apply_sc(sc("sc_b", charge="ch_b", cents=10))\n'
            '    take_cash("ch_b", 30)\n'
            '    assert credit_cents("w_a") == 40 and credit_cents("w_b") == 10\n'
        ),
        table="till_sc_cash",
        pk="credit_id",
        rg="store_credit|cash_tender|apply_sc",
        surfaces="store-credit apply vs cash tender",
        avoided="r146 gift vs remainder; r137 wallet. This is credit_id vs cash",
        this_is="credit PK burns store credit; cash PK remainder",
        seed="apply store-credit + cash same charge",
        first_apply="credit applied today",
        plan_change="credit PK burn; cash remainder once",
        step_note="Credit-day 6–7; PK 8–11; second credit 12–13.",
        skip_pred="this credit already applied today",
        verb="apply",
        skip_label="credit-applied-today skip",
        obs3="store-credit and cash both debit credit wallet",
        obs4="credit burn; cash remainder",
        obs5="credit 2000; cash 3000; second credit adds",
        fail_obs="FAILED test_credit_not_cash_double - credit 5000 or rows 3\n1 failed, 1 passed",
        obs7="cash still hits credit wallet; new credit same day dropped.",
        still_fail_obs="FAILED test_credit_not_cash_double - cash unguarded or credit skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def apply_sc(ev):\n"
            "    if not claim_sc(ev['credit_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_credit(wallet_of(ev["credit_id"]), ev["cents"], sc=ev["credit_id"])\n'
            '    return {"ok": True, "credit": True}\n'
        ),
        rewrite_src_obs="claim credit_id burns",
        rewrite_hook=(
            "def take_cash(charge_id, cents):\n"
            "    if not claim_cash(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    take_tender(charge_id, cents, kind='cash')\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK cash remainder",
        extra_ddl="  charge_id text UNIQUE",
        residual="credit expiry after cash last-write",
        grep_pat="debit_credit",
        grep_obs="src/sc_cash.py: burn credit; cash tender",
        goal="till-sc store-credit and cash both hit credit wallet. Credit PK; cash PK. Gate: tests/test_sc_cash.py.",
        plan="Skip apply if this credit already applied today.",
        outcome="Credit+cash doubled on wallet. Credit-day skip left cash unguarded. Plan change: credit PK + cash PK. Tests 2/2 + second credit + suite 8/8.",
        skip_new='    if not applied_today(ev["credit_id"]):\n        debit_credit(ev["credit_id"], ev["cents"])',
        psql_rows="sc_1\nsc_a\nsc_b",
        test_name="credit-not-cash-double test",
        surface_read="store-credit apply plus cash tender",
    ),
    _fail_pair(
        slug="credit-after-cash",
        stem="sc_late",
        fn="late_sc",
        inner='debit_credit(ev["credit_id"], ev["cents"])',
        comment="counted every late store-credit",
        hook_fn="already_cash",
        hook_body="def already_cash(charge_id, cents):\n    take_tender(charge_id, cents, kind='cash')\n",
        test_fn="test_late_sc_not_add",
        test_body=(
            "def test_late_sc_not_add():\n"
            '    already_cash("ch_1", 3000)\n'
            '    late_sc(sc("sc_1", charge="ch_1", cents=2000))\n'
            '    late_sc(sc("sc_1", charge="ch_1", cents=2000))\n'
            '    assert cash_cents("ch_1") == 3000 and recv_cents("m_1") == 2000 and late_sc_rows("sc_1") == 1\n'
            "\n"
            "def test_second_late_sc():\n"
            '    already_cash("ch_a", 60)\n'
            '    late_sc(sc("sc_a", charge="ch_a", cents=40))\n'
            '    already_cash("ch_b", 30)\n'
            '    late_sc(sc("sc_b", charge="ch_b", cents=10))\n'
            '    assert recv_cents("m_a") == 40 and recv_cents("m_b") == 10\n'
        ),
        test2_body=(
            "def test_second_late_sc():\n"
            '    already_cash("ch_a", 60)\n'
            '    late_sc(sc("sc_a", charge="ch_a", cents=40))\n'
            '    already_cash("ch_b", 30)\n'
            '    late_sc(sc("sc_b", charge="ch_b", cents=10))\n'
            '    assert recv_cents("m_a") == 40 and recv_cents("m_b") == 10\n'
        ),
        table="till_sc_late",
        pk="late_sc_id",
        rg="late_store_credit|after_cash|recv_sc",
        surfaces="late store-credit after cash tendered",
        avoided="r152 credit vs cash; r146 late gift. This is late credit receivable",
        this_is="late credit opens receivable; cash stays",
        seed="cash then late store-credit",
        first_apply="late credit posted today",
        plan_change="late credit PK receivable; cash stays",
        step_note="Late-credit-day 6–7; PK 8–11; second 12–13; burn xfail 15–17.",
        next_note="Unused: late credit should burn wallet. Avoid late-credit-today skip.",
        skip_pred="this late credit already posted today",
        verb="apply",
        skip_label="late-credit-today skip",
        obs3="late credit burns wallet after cash",
        obs4="late credit receivable; cash stays",
        obs5="cash 3000; recv 2000; second late adds",
        fail_obs="FAILED test_late_sc_not_add - credit burned or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides receivable.",
        still_fail_obs="FAILED if late credit burned wallet\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_sc(ev):\n"
            "    if not claim_lsc(ev['credit_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], sc=ev["credit_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim late_sc opens receivable",
        rewrite_hook=(
            "def already_cash(charge_id, cents):\n"
            "    if not claim_cash2(charge_id):\n"
            "        return existing_cash(charge_id)\n"
            "    take_tender(charge_id, cents, kind='cash')\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="cash stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="late credit should burn wallet",
        xfail_body=(
            "def test_late_sc_burns():\n"
            '    already_cash("ch_p", 3000)\n'
            '    late_sc(sc("sc_p", charge="ch_p", cents=2000))\n'
            '    assert credit_cents("w_p") == 2000 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_sc_burns - recv opened; wallet not burned\n1 failed",
        xfail_fn="test_late_sc_burns",
        xfail_reason="late store-credit burn vs receivable is a policy fork",
        goal="till-sclate late credit burned wallet after cash. Late recv. Gate: tests/test_sc_late.py.",
        plan="Skip apply if this late credit already posted today.",
        outcome="Late credit burned wallet. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: burn xfail handoff.",
        skip_new='    if not late_sc_today(ev["credit_id"]):\n        debit_credit(ev["credit_id"], ev["cents"])',
        test_name="late-sc-not-add test",
        surface_read="late store-credit plus cash tender",
        test_body_short="same — late credit receivable; cash stays",
    ),
)

# r153 loyalty burn vs cash / burn after cash
pair(
    _ok_pair(
        slug="loyalty-burn-vs-cash",
        stem="loy_cash",
        fn="burn_pts",
        inner='debit_pts(ev["acct_id"], ev["points"])',
        comment="counted every loyalty burn",
        hook_fn="take_cash2",
        hook_body="def take_cash2(charge_id, cents):\n    debit_pts(charge_id, cents)\n",
        test_fn="test_burn_not_cash_double",
        test_body=(
            "def test_burn_not_cash_double():\n"
            '    burn_pts(lp("lp_1", charge="ch_1", points=2000))\n'
            '    burn_pts(lp("lp_1", charge="ch_1", points=2000))\n'
            '    take_cash2("ch_1", 3000)\n'
            '    assert pts_cents("a_1") == 2000 and cash_cents("ch_1") == 3000 and loy_rows("lp_1") == 1\n'
            "\n"
            "def test_second_burn():\n"
            '    burn_pts(lp("lp_a", charge="ch_a", points=40))\n'
            '    take_cash2("ch_a", 60)\n'
            '    burn_pts(lp("lp_b", charge="ch_b", points=10))\n'
            '    take_cash2("ch_b", 30)\n'
            '    assert pts_cents("a_a") == 40 and pts_cents("a_b") == 10\n'
        ),
        test2_body=(
            "def test_second_burn():\n"
            '    burn_pts(lp("lp_a", charge="ch_a", points=40))\n'
            '    take_cash2("ch_a", 60)\n'
            '    burn_pts(lp("lp_b", charge="ch_b", points=10))\n'
            '    take_cash2("ch_b", 30)\n'
            '    assert pts_cents("a_a") == 40 and pts_cents("a_b") == 10\n'
        ),
        table="till_loy_cash",
        pk="burn_id",
        rg="loyalty.burn|points|cash_tender",
        surfaces="loyalty burn vs cash tender",
        avoided="r152 store-credit vs cash; r104 Square loyalty. This is burn_id vs cash",
        this_is="burn PK points; cash PK remainder",
        seed="loyalty burn + cash same charge",
        first_apply="points burned today",
        plan_change="burn PK points; cash remainder once",
        step_note="Burn-day 6–7; PK 8–11; second burn 12–13.",
        skip_pred="this burn already posted today",
        verb="burn",
        skip_label="points-burned-today skip",
        obs3="burn and cash both debit points",
        obs4="burn points; cash remainder",
        obs5="pts 2000; cash 3000; second burn adds",
        fail_obs="FAILED test_burn_not_cash_double - pts 5000 or rows 3\n1 failed, 1 passed",
        obs7="cash still hits points; new burn same day dropped.",
        still_fail_obs="FAILED test_burn_not_cash_double - cash unguarded or burn skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def burn_pts(ev):\n"
            "    if not claim_burn(ev['burn_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_pts(acct_of(ev["acct_id"]), ev["points"], burn=ev["burn_id"])\n'
            '    return {"ok": True, "burned": True}\n'
        ),
        rewrite_src_obs="claim burn_id debit points",
        rewrite_hook=(
            "def take_cash2(charge_id, cents):\n"
            "    if not claim_cash3(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    take_tender(charge_id, cents, kind='cash')\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK cash remainder",
        extra_ddl="  charge_id text UNIQUE",
        residual="points expire after cash last-write",
        grep_pat="debit_pts",
        grep_obs="src/loy_cash.py: burn points; cash tender",
        goal="till-loy burn and cash both hit points. Burn PK; cash PK. Gate: tests/test_loy_cash.py.",
        plan="Skip burn if this burn already posted today.",
        outcome="Burn+cash doubled on points. Burn-day skip left cash unguarded. Plan change: burn PK + cash PK. Tests 2/2 + second burn + suite 8/8.",
        skip_new='    if not burned_today(ev["acct_id"]):\n        debit_pts(ev["acct_id"], ev["points"])',
        psql_rows="lp_1\nlp_a\nlp_b",
        test_name="burn-not-cash-double test",
        surface_read="loyalty burn plus cash tender",
    ),
    _fail_pair(
        slug="loyalty-burn-after-cash",
        stem="loy_late",
        fn="late_burn",
        inner='debit_pts(ev["acct_id"], ev["points"])',
        comment="counted every late burn",
        hook_fn="already_cash3",
        hook_body="def already_cash3(charge_id, cents):\n    take_tender(charge_id, cents, kind='cash')\n",
        test_fn="test_late_burn_not_add",
        test_body=(
            "def test_late_burn_not_add():\n"
            '    already_cash3("ch_1", 3000)\n'
            '    late_burn(lp("lp_1", charge="ch_1", points=2000))\n'
            '    late_burn(lp("lp_1", charge="ch_1", points=2000))\n'
            '    assert cash_cents("ch_1") == 3000 and recv_cents("m_1") == 2000 and late_loy_rows("lp_1") == 1\n'
            "\n"
            "def test_second_late_burn():\n"
            '    already_cash3("ch_a", 60)\n'
            '    late_burn(lp("lp_a", charge="ch_a", points=40))\n'
            '    already_cash3("ch_b", 30)\n'
            '    late_burn(lp("lp_b", charge="ch_b", points=10))\n'
            '    assert recv_cents("m_a") == 40 and recv_cents("m_b") == 10\n'
        ),
        test2_body=(
            "def test_second_late_burn():\n"
            '    already_cash3("ch_a", 60)\n'
            '    late_burn(lp("lp_a", charge="ch_a", points=40))\n'
            '    already_cash3("ch_b", 30)\n'
            '    late_burn(lp("lp_b", charge="ch_b", points=10))\n'
            '    assert recv_cents("m_a") == 40 and recv_cents("m_b") == 10\n'
        ),
        table="till_loy_late",
        pk="late_burn_id",
        rg="late_burn|after_cash|recv_pts",
        surfaces="late loyalty burn after cash tendered",
        avoided="r153 loyalty vs cash; r152 late credit. This is late burn receivable",
        this_is="late burn opens receivable; cash stays",
        seed="cash then late loyalty burn",
        first_apply="late burn posted today",
        plan_change="late burn PK receivable; cash stays",
        step_note="Late-burn-day 6–7; PK 8–11; second 12–13; pts xfail 15–17.",
        next_note="Unused: late burn should debit points. Avoid late-burn-today skip.",
        skip_pred="this late burn already posted today",
        verb="burn",
        skip_label="late-burn-today skip",
        obs3="late burn debits points after cash",
        obs4="late burn receivable; cash stays",
        obs5="cash 3000; recv 2000; second late adds",
        fail_obs="FAILED test_late_burn_not_add - pts burned or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides receivable.",
        still_fail_obs="FAILED if late burn debited points\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_burn(ev):\n"
            "    if not claim_lburn(ev['burn_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["points"], burn=ev["burn_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim late_burn opens receivable",
        rewrite_hook=(
            "def already_cash3(charge_id, cents):\n"
            "    if not claim_cash4(charge_id):\n"
            "        return existing_cash(charge_id)\n"
            "    take_tender(charge_id, cents, kind='cash')\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="cash stays",
        extra_ddl="  charge_id text NOT NULL",
        xfail_label="late burn should debit points",
        xfail_body=(
            "def test_late_burn_debits():\n"
            '    already_cash3("ch_p", 3000)\n'
            '    late_burn(lp("lp_p", charge="ch_p", points=2000))\n'
            '    assert pts_cents("a_p") == 2000 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_burn_debits - recv opened; pts not debited\n1 failed",
        xfail_fn="test_late_burn_debits",
        xfail_reason="late loyalty burn vs receivable is a policy fork",
        goal="till-loylate late burn hit points after cash. Late recv. Gate: tests/test_loy_late.py.",
        plan="Skip burn if this late burn already posted today.",
        outcome="Late burn hit points. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: pts xfail handoff.",
        skip_new='    if not late_burn_today(ev["acct_id"]):\n        debit_pts(ev["acct_id"], ev["points"])',
        test_name="late-burn-not-add test",
        surface_read="late loyalty burn plus cash tender",
        test_body_short="same — late burn receivable; cash stays",
    ),
)

# r154 insurance add-on vs premium / premium after sale
pair(
    _ok_pair(
        slug="insurance-addon-vs-premium",
        stem="ins_prem",
        fn="bind_ins",
        inner='credit_carrier(ev["policy_id"], ev["cents"])',
        comment="counted every bind",
        hook_fn="bill_prem",
        hook_body="def bill_prem(charge_id, cents):\n    credit_carrier(charge_id, cents)\n",
        test_fn="test_bind_not_premium_double",
        test_body=(
            "def test_bind_not_premium_double():\n"
            '    bind_ins(ins("po_1", charge="ch_1", cents=250))\n'
            '    bind_ins(ins("po_1", charge="ch_1", cents=250))\n'
            '    bill_prem("ch_1", 5000)\n'
            '    assert carrier_cents("c_1") == 250 and merch_cents("m_1") == 5000 and ins_rows("po_1") == 1\n'
            "\n"
            "def test_second_policy():\n"
            '    bind_ins(ins("po_a", charge="ch_a", cents=10))\n'
            '    bill_prem("ch_a", 100)\n'
            '    bind_ins(ins("po_b", charge="ch_b", cents=4))\n'
            '    bill_prem("ch_b", 40)\n'
            '    assert carrier_cents("c_a") == 10 and carrier_cents("c_b") == 4\n'
        ),
        test2_body=(
            "def test_second_policy():\n"
            '    bind_ins(ins("po_a", charge="ch_a", cents=10))\n'
            '    bill_prem("ch_a", 100)\n'
            '    bind_ins(ins("po_b", charge="ch_b", cents=4))\n'
            '    bill_prem("ch_b", 40)\n'
            '    assert carrier_cents("c_a") == 10 and carrier_cents("c_b") == 4\n'
        ),
        table="till_ins_prem",
        pk="policy_id",
        rg="insurance.bind|premium|add_on",
        surfaces="insurance bind vs premium bill",
        avoided="r145 surcharge; r151 cfee. This is policy_id vs premium",
        this_is="bind PK carrier; bill PK merchant principal",
        seed="bind insurance + bill premium same charge",
        first_apply="policy bound today",
        plan_change="bind PK carrier; bill principal once",
        step_note="Bind-day 6–7; PK 8–11; second policy 12–13.",
        skip_pred="this policy already bound today",
        verb="bind",
        skip_label="policy-bound-today skip",
        obs3="bind and bill both credit carrier",
        obs4="bind carrier; bill principal",
        obs5="carrier 250; merch 5000; second policy adds",
        fail_obs="FAILED test_bind_not_premium_double - carrier 5250 or rows 3\n1 failed, 1 passed",
        obs7="bill still hits carrier; new bind same day dropped.",
        still_fail_obs="FAILED test_bind_not_premium_double - bill unguarded or bind skipped\n1 failed, 1 passed",
        rewrite_src=(
            "def bind_ins(ev):\n"
            "    if not claim_pol(ev['policy_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_carrier(carrier_of(ev["policy_id"]), ev["cents"], pol=ev["policy_id"])\n'
            '    return {"ok": True, "bound": True}\n'
        ),
        rewrite_src_obs="claim policy_id credits carrier",
        rewrite_hook=(
            "def bill_prem(charge_id, cents):\n"
            "    if not claim_bill(charge_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_ch(charge_id), cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK principal bill",
        extra_ddl="  charge_id text UNIQUE",
        residual="binder fee after bill last-write",
        grep_pat="credit_carrier",
        grep_obs="src/ins_prem.py: bind carrier; bill merchant",
        goal="till-ins bind and bill both hit carrier. Bind PK; bill PK. Gate: tests/test_ins_prem.py.",
        plan="Skip bind if this policy already bound today.",
        outcome="Bind+bill doubled on carrier. Bind-day skip left bill unguarded. Plan change: policy PK + bill PK. Tests 2/2 + second policy + suite 8/8.",
        skip_new='    if not bound_today(ev["policy_id"]):\n        credit_carrier(ev["policy_id"], ev["cents"])',
        psql_rows="po_1\npo_a\npo_b",
        test_name="bind-not-premium-double test",
        surface_read="insurance bind plus premium bill",
    ),
    _fail_pair(
        slug="premium-after-sale",
        stem="ins_late",
        fn="late_prem",
        inner='credit_carrier(ev["policy_id"], ev["cents"])',
        comment="counted every late premium",
        hook_fn="already_bind",
        hook_body="def already_bind(policy_id, cents):\n    credit_carrier(policy_id, cents)\n",
        test_fn="test_late_prem_not_add",
        test_body=(
            "def test_late_prem_not_add():\n"
            '    already_bind("po_1", 250)\n'
            '    late_prem(ins("lp_1", charge="ch_1", cents=250))\n'
            '    late_prem(ins("lp_1", charge="ch_1", cents=250))\n'
            '    assert carrier_cents("c_1") == 250 and recv_cents("m_1") == 250 and late_ins_rows("lp_1") == 1\n'
            "\n"
            "def test_second_late_prem():\n"
            '    already_bind("po_a", 10)\n'
            '    late_prem(ins("lp_a", charge="ch_a", cents=10))\n'
            '    already_bind("po_b", 4)\n'
            '    late_prem(ins("lp_b", charge="ch_b", cents=4))\n'
            '    assert recv_cents("m_a") == 10 and recv_cents("m_b") == 4\n'
        ),
        test2_body=(
            "def test_second_late_prem():\n"
            '    already_bind("po_a", 10)\n'
            '    late_prem(ins("lp_a", charge="ch_a", cents=10))\n'
            '    already_bind("po_b", 4)\n'
            '    late_prem(ins("lp_b", charge="ch_b", cents=4))\n'
            '    assert recv_cents("m_a") == 10 and recv_cents("m_b") == 4\n'
        ),
        table="till_ins_late",
        pk="late_prem_id",
        rg="late_premium|after_sale|recv_prem",
        surfaces="late premium after sale bound",
        avoided="r154 bind vs premium; r151 late cfee. This is late premium receivable",
        this_is="late premium opens receivable; bind stays",
        seed="bind then late premium",
        first_apply="late premium posted today",
        plan_change="late premium PK receivable; bind stays",
        step_note="Late-prem-day 6–7; PK 8–11; second 12–13; extra xfail 15–17.",
        next_note="Unused: late premium should extra-credit carrier. Avoid late-prem-today skip.",
        skip_pred="this late premium already posted today",
        verb="bill",
        skip_label="late-premium-today skip",
        obs3="late premium extra-credits carrier",
        obs4="late premium receivable; bind stays",
        obs5="carrier 250; recv 250; second late adds",
        fail_obs="FAILED test_late_prem_not_add - carrier 500 == 250 or rows 3\n1 failed, 1 passed",
        obs7="second late ok; hides receivable.",
        still_fail_obs="FAILED if late prem extra-credited (carrier 500)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_prem(ev):\n"
            "    if not claim_lprem(ev.get('late_prem_id') or ev['policy_id']+'_lp'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    open_recv(merch_of_ch(ev["charge_id"]), ev["cents"], pol=ev["policy_id"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs="claim late_prem opens receivable",
        rewrite_hook=(
            "def already_bind(policy_id, cents):\n"
            "    if not claim_pol2(policy_id):\n"
            "        return existing_pol(policy_id)\n"
            "    credit_carrier(carrier_of(policy_id), cents)\n"
            "    return policy_id\n"
        ),
        rewrite_hook_obs="bind stays",
        extra_ddl="  policy_id text UNIQUE",
        xfail_label="late premium should extra-credit carrier",
        xfail_body=(
            "def test_late_prem_credits():\n"
            '    already_bind("po_p", 250)\n'
            '    late_prem(ins("lp_p", charge="ch_p", cents=250))\n'
            '    assert carrier_cents("c_p") == 500 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_late_prem_credits - recv opened; carrier stayed 250\n1 failed",
        xfail_fn="test_late_prem_credits",
        xfail_reason="late premium extra-credit vs receivable is a policy fork",
        goal="till-inslate late premium extra-credited carrier. Late recv. Gate: tests/test_ins_late.py.",
        plan="Skip bill if this late premium already posted today.",
        outcome="Late prem extra-credited. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: extra xfail handoff.",
        skip_new='    if not late_prem_today(ev["policy_id"]):\n        credit_carrier(ev["policy_id"], ev["cents"])',
        test_name="late-prem-not-add test",
        surface_read="late premium plus bound policy",
        test_body_short="same — late premium receivable; bind stays",
    ),
)
