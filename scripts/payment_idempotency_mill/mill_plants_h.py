"""Plants r124–r139: ledger/fencing (not PSP webhook-vs-retrieve)."""

from mill_plants import _ok, _fail

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def _paths(stem, fail=False):
    d = {
        "src": f"src/{stem}.py",
        "hook": f"src/{stem}_h.py",
        "test": f"tests/test_{stem}.py",
        "test2": f"tests/test_{stem}_two.py",
        "mig": stem,
    }
    if fail:
        d["xfail"] = f"tests/test_{stem}_x.py"
    return d


def _rg_obs(stem, src_fn, hook_fn, test_fn):
    return (
        f"src/{stem}.py:8: def {src_fn}\n"
        f"src/{stem}_h.py:6: def {hook_fn}\n"
        f"tests/test_{stem}.py: def {test_fn}\n"
    )


def _naive(fn, inner, comment):
    body = (
        f"def {fn}(ev):\n"
        f"    {inner}  # {comment}\n"
        f'    return {{"ok": True}}\n'
    )
    skip_old = f"    {inner}  # {comment}"
    return body, skip_old


def _ddl(table, pk, extra_lines=""):
    extra = f",\n{extra_lines}" if extra_lines else ""
    return (
        f"CREATE TABLE {table} (\n"
        f"  {pk} text PRIMARY KEY,\n"
        f"  cents int NOT NULL DEFAULT 0{extra}\n"
        f");\n"
    )


# ---------------------------------------------------------------------------
# r124 journal post vs settlement window / reverse after window close
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "post_jnl",
    'post_ledger(ev["journal_id"], ev["cents"])',
    "counted every journal post",
)
pair(
    _ok(
        slug="jnl-post-vs-settle-window",
        surfaces="ledger journal post vs settlement window reopen",
        avoided="r80 outbox/inbox; r96 fencing token; r71 snapshot. This is settle window vs journal_id",
        this_is="journal_id claim; window reopen extends cutoff only",
        seed="post journal_id + reopen same batch",
        first_apply="batch posted today",
        plan_change="PK journal_id; reopen mutates cutoff, does not re-post",
        step_note="Batch-day 6–7; PK 8–11; second journal 12–13.",
        **_paths("jnl_post"),
        table="till_jnl_post",
        pk="journal_id",
        rg="journal_id|settlement_window|reopen_cutoff|post_ledger",
        rg_obs=_rg_obs("jnl_post", "post_jnl", "reopen_window", "test_post_not_reopen_double"),
        test_name="post-not-reopen-double test",
        surface_read="journal post plus settlement window reopen",
        skip_pred="this batch already posted today",
        verb="post",
        skip_label="batch-posted-today skip",
        src_body=_src,
        hook_body=(
            "def reopen_window(batch_id, new_cutoff):\n"
            "    post_ledger(batch_id, window_cents(batch_id))\n"
            "    set_cutoff(batch_id, new_cutoff)\n"
        ),
        test_body=(
            "def test_post_not_reopen_double():\n"
            '    post_jnl(jnl("j_1", 5000, batch="b1"))\n'
            '    post_jnl(jnl("j_1", 5000, batch="b1"))\n'
            '    reopen_window("b1", cutoff="T+1")\n'
            '    assert posted_cents("j_1") == 5000 and jnl_rows("j_1") == 1 and cutoff("b1") == "T+1"\n'
            "\n"
            "def test_second_journal():\n"
            '    post_jnl(jnl("j_a", 100, batch="ba"))\n'
            '    post_jnl(jnl("j_b", 40, batch="bb"))\n'
            '    assert posted_cents("j_a") == 100 and posted_cents("j_b") == 40\n'
        ),
        obs3="reopen also posts the batch cents",
        obs4="one row per journal_id; reopen once; second journal adds",
        obs5="post once; reopen no extra; second journal adds",
        fail_obs="FAILED test_post_not_reopen_double - jnl_rows 3 == 1 or reopen credited\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not posted_today(ev.get("batch_id")):\n        post_ledger(ev["journal_id"], ev["cents"])',
        obs7="reopen still posts; new journal same day dropped.",
        still_fail_obs="FAILED test_post_not_reopen_double - reopen still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def post_jnl(ev):\n"
            '    if ev.get("kind") == "reopen":\n'
            '        set_cutoff(ev["batch_id"], ev["cutoff"])\n'
            '        return {"ok": True, "reopen": True}\n'
            "    if not claim_jnl(ev['journal_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    post_ledger(ev["journal_id"], ev["cents"], batch=ev["batch_id"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="claim journal_id; reopen is not a post",
        rewrite_hook=(
            "def reopen_window(batch_id, new_cutoff):\n"
            "    set_cutoff(batch_id, new_cutoff)\n"
            "    return cutoff(batch_id)\n"
            "\n"
            "def claim_jnl(jid):\n"
            '    cur = db.execute("INSERT INTO till_jnl_post (journal_id) VALUES (%s) ON CONFLICT DO NOTHING", [jid])\n'
            "    return cur.rowcount == 1\n"
        ),
        obs9="reopen updates cutoff only.",
        rewrite_hook_obs="PK journal_id",
        ddl=_ddl("till_jnl_post", "journal_id", "  batch_id text NOT NULL,\n  cutoff text"),
        ddl_obs="PK journal_id",
        test2_body=(
            "def test_second_journal():\n"
            '    post_jnl(jnl("j_a", 100, batch="ba"))\n'
            '    post_jnl(jnl("j_b", 40, batch="bb"))\n'
            '    assert posted_cents("j_a") == 100 and posted_cents("j_b") == 40\n'
        ),
        psql_rows="j_1\nj_a\nj_b",
        residual="late item after cutoff still accepted",
        grep_pat="cutoff",
        grep_obs="src/jnl_post.py: claim then insert; no late-after-cutoff reject",
        goal="till-jnl post and window reopen both credited j_1. PK journal_id; reopen extends cutoff. Gate: tests/test_jnl_post.py.",
        plan="Skip post if this batch already posted today.",
        outcome="Post+reopen double-posted. Batch-day skip left reopen unguarded. Plan change: PK journal_id; reopen mutates cutoff. Tests 2/2 + second journal + suite 8/8.",
    ),
    _fail(
        slug="settle-reverse-after-close",
        surfaces="settlement window close vs reversal instruction",
        avoided="r124 journal vs reopen; r80 inbox. This is close PK vs reverse after final",
        this_is="window close PK; reverse is a separate claim after reopen",
        seed="close window + reverse same window_id",
        first_apply="window settled today",
        plan_change="PK window_id on close; reverse blocked while closed",
        step_note="Window-day 6–7; PK 8–11; second 12–13; reverse-after-close xfail 15–17.",
        next_note="Unused: reverse after close with no reopen. Avoid window-settled-today skip.",
        **_paths("settle_rev", fail=True),
        table="till_settle_rev",
        pk="window_id",
        rg="window_id|settle_close|reverse_settlement|finalized",
        rg_obs=_rg_obs("settle_rev", "close_win", "reverse_win", "test_close_not_reverse_double"),
        test_name="close-not-reverse-double test",
        surface_read="settlement close plus reversal",
        skip_pred="this window already settled today",
        verb="settle",
        skip_label="window-settled-today skip",
        src_body=_naive(
            "close_win",
            'settle_win(ev["window_id"], ev["cents"])',
            "counted every close",
        )[0],
        hook_body=(
            "def reverse_win(window_id, cents):\n"
            "    settle_win(window_id, -cents)\n"
        ),
        test_body=(
            "def test_close_not_reverse_double():\n"
            '    close_win(win("w_1", 5000))\n'
            '    close_win(win("w_1", 5000))\n'
            '    reverse_win("w_1", 5000)\n'
            '    assert settled_cents("w_1") == 5000 and win_rows("w_1") == 1 and closed("w_1")\n'
            "\n"
            "def test_second_window():\n"
            '    close_win(win("w_a", 100))\n'
            '    close_win(win("w_b", 40))\n'
            '    assert settled_cents("w_a") == 100 and settled_cents("w_b") == 40\n'
        ),
        test_body_short="same — close PK window_id; reverse blocked while closed",
        obs3="close and reverse both settle",
        obs4="close PK window_id; reverse no-ops while closed",
        obs5="close once; reverse does not extra-settle; second window adds",
        fail_obs="FAILED test_close_not_reverse_double - win_rows 3 == 1 or reverse zeroed\n1 failed, 1 passed",
        skip_old=_naive(
            "close_win",
            'settle_win(ev["window_id"], ev["cents"])',
            "counted every close",
        )[1],
        skip_new='    if not settled_today(ev["window_id"]):\n        settle_win(ev["window_id"], ev["cents"])',
        obs7="second window ok; hides missing window_id PK.",
        still_fail_obs="FAILED if reverse ran first (should not settle) then close same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def close_win(ev):\n"
            "    if not claim_win(ev['window_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    settle_win(ev["window_id"], ev["cents"])\n'
            '    mark_closed(ev["window_id"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="claim window_id on close",
        rewrite_hook=(
            "def reverse_win(window_id, cents):\n"
            "    if closed(window_id) and not reopened(window_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_win_rev(window_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    settle_win(window_id, -cents)\n"
            '    return {"ok": True, "reversed": True}\n'
        ),
        rewrite_hook_obs="reverse blocked while closed",
        ddl=_ddl("till_settle_rev", "window_id", "  closed bool NOT NULL DEFAULT false"),
        ddl_obs="PK window_id",
        test2_body=(
            "def test_second_window():\n"
            '    close_win(win("w_a", 100))\n'
            '    close_win(win("w_b", 40))\n'
            '    assert settled_cents("w_a") == 100 and settled_cents("w_b") == 40\n'
        ),
        xfail_label="reverse after close with no reopen",
        xfail_body=(
            "def test_reverse_after_close():\n"
            '    close_win(win("w_p", 5000))\n'
            '    reverse_win("w_p", 5000)\n'
            '    assert settled_cents("w_p") == 0 and not closed("w_p")\n'
        ),
        xfail_fail_obs="FAILED test_reverse_after_close - reverse blocked; cents still 5000\n1 failed",
        xfail_old="def test_reverse_after_close():",
        xfail_new='@pytest.mark.xfail(reason="handoff: reverse after close must reopen then claim reverse", strict=True)\ndef test_reverse_after_close():',
        xfail_patch_obs="xfailed reverse after close",
        goal="till-settle close and reverse both settled w_1. Close PK window_id; reverse blocked while closed. Gate: tests/test_settle_rev.py.",
        plan="Skip settle if this window already settled today.",
        outcome="Close+reverse double-settled. Window-day skip hid window_id. Plan change: close PK; reverse blocked. Primary+second pass. Partial: reverse after close xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r125 FX rate lock vs capture / quote expire before capture
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "lock_fx",
    'credit_fx(ev["quote_id"], ev["cents"])',
    "counted every quote lock",
)
pair(
    _ok(
        slug="fx-lock-vs-capture",
        surfaces="FX quote lock vs capture at locked rate",
        avoided="r16 quote accept CAS; r87 tax txn. This is locked_rate vs spot at capture",
        this_is="quote_id stores rate; capture PK uses locked_rate not mid-market",
        seed="lock quote + capture same quote_id",
        first_apply="quote locked today",
        plan_change="lock records rate; capture PK capture_id at locked_rate",
        step_note="Quote-day 6–7; PK 8–11; second quote 12–13.",
        **_paths("fx_lock"),
        table="till_fx_lock",
        pk="capture_id",
        rg="quote_id|locked_rate|fx_capture|mid_market",
        rg_obs=_rg_obs("fx_lock", "lock_fx", "capture_fx", "test_lock_not_capture_double"),
        test_name="lock-not-capture-double test",
        surface_read="FX quote lock plus capture",
        skip_pred="this FX quote already locked today",
        verb="credit",
        skip_label="quote-locked-today skip",
        src_body=_src,
        hook_body=(
            "def capture_fx(quote_id, cents, spot):\n"
            "    credit_fx(quote_id, int(cents * spot / 1e4))\n"
        ),
        test_body=(
            "def test_lock_not_capture_double():\n"
            '    lock_fx(q("q_1", cents=5000, rate=12000))\n'
            '    lock_fx(q("q_1", cents=5000, rate=12000))\n'
            '    capture_fx("q_1", 5000, spot=12500)\n'
            '    assert fx_rate("q_1") == 12000 and posted_cents("c_1") == 6000 and fx_rows("c_1") == 1\n'
            "\n"
            "def test_second_quote():\n"
            '    lock_fx(q("q_a", cents=100, rate=11000))\n'
            '    capture_fx("q_a", 100, spot=11000)\n'
            '    lock_fx(q("q_b", cents=40, rate=11000))\n'
            '    capture_fx("q_b", 40, spot=11000)\n'
            '    assert posted_cents("c_a") == 110 and posted_cents("c_b") == 44\n'
        ),
        obs3="lock and capture both credit, capture uses spot",
        obs4="lock records rate; capture PK at locked_rate",
        obs5="capture once at locked rate; lock no extra credit; second quote adds",
        fail_obs="FAILED test_lock_not_capture_double - fx_rows 3 == 1 or credited at spot 12500\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not locked_today(ev["quote_id"]):\n        credit_fx(ev["quote_id"], ev["cents"])',
        obs7="capture still credits at spot; new quote same day dropped.",
        still_fail_obs="FAILED test_lock_not_capture_double - capture still spots or lock credits\n1 failed, 1 passed",
        rewrite_src=(
            "def lock_fx(ev):\n"
            "    if not claim_quote(ev['quote_id']):\n"
            '        return existing_quote(ev["quote_id"])\n'
            '    store_rate(ev["quote_id"], ev["rate"])\n'
            '    return {"ok": True, "locked": ev["rate"]}\n'
        ),
        rewrite_src_obs="unique quote_id stores rate; lock does not credit",
        rewrite_hook=(
            "def capture_fx(quote_id, cents, spot):\n"
            "    rate = locked_rate(quote_id) or spot\n"
            "    cid = cap_id(quote_id)\n"
            "    if not claim_fx_cap(cid):\n"
            "        return existing_cap(cid)\n"
            "    credit_fx(cid, cents * rate // 10000, rate=rate)\n"
            "    return cid\n"
        ),
        obs9="capture claims capture_id at locked rate.",
        rewrite_hook_obs="PK capture_id; locked_rate",
        ddl=_ddl("till_fx_lock", "capture_id", "  quote_id text UNIQUE,\n  rate int NOT NULL"),
        ddl_obs="PK capture_id",
        test2_body=(
            "def test_second_quote():\n"
            '    lock_fx(q("q_a", cents=100, rate=11000))\n'
            '    capture_fx("q_a", 100, spot=11000)\n'
            '    lock_fx(q("q_b", cents=40, rate=11000))\n'
            '    capture_fx("q_b", 40, spot=11000)\n'
            '    assert posted_cents("c_a") == 110 and posted_cents("c_b") == 44\n'
        ),
        psql_rows="c_1\nc_a\nc_b",
        residual="mid-market move after lock ignored on purpose; expire not handled",
        grep_pat="spot",
        grep_obs="src/fx_lock.py: locked_rate or spot fallback; no quote TTL",
        goal="till-fx lock and capture both credited q_1 at spot. Lock stores rate; capture PK at locked_rate. Gate: tests/test_fx_lock.py.",
        plan="Skip credit if this FX quote already locked today.",
        outcome="Lock+capture double-credited. Quote-day skip left capture on spot. Plan change: store rate; PK capture_id at locked_rate. Tests 2/2 + second quote + suite 8/8.",
    ),
    _fail(
        slug="fx-quote-expire-before-cap",
        surfaces="FX quote expire vs capture",
        avoided="r125 lock vs capture; r16 quote accept. This is expire-before-capture block",
        this_is="expire records quote_id; capture blocked if expired",
        seed="expire quote then capture",
        first_apply="quote expired today",
        plan_change="expire flags quote; capture refuses expired",
        step_note="Expire-day 6–7; PK 8–11; second 12–13; override-after-expire xfail 15–17.",
        next_note="Unused: capture override after expire. Avoid quote-expired-today skip.",
        **_paths("fx_exp", fail=True),
        table="till_fx_exp",
        pk="quote_id",
        rg="quote.expire|ttl_seconds|capture_blocked|expired",
        rg_obs=_rg_obs("fx_exp", "expire_fx", "capture_exp", "test_expire_not_capture_double"),
        test_name="expire-not-capture-double test",
        surface_read="FX quote expire plus capture",
        skip_pred="this FX quote already expired today",
        verb="flag",
        skip_label="quote-expired-today skip",
        src_body=_naive(
            "expire_fx",
            'flag_fx(ev["quote_id"], ev.get("cents", 0))',
            "counted every expire",
        )[0],
        hook_body=(
            "def capture_exp(quote_id, cents):\n"
            "    credit_fx(quote_id, cents)\n"
        ),
        test_body=(
            "def test_expire_not_capture_double():\n"
            '    expire_fx(q("q_1", cents=0))\n'
            '    expire_fx(q("q_1", cents=0))\n'
            '    capture_exp("q_1", 5000)\n'
            '    assert expired("q_1") and posted_cents("q_1") == 0 and fx_rows("q_1") == 1\n'
            "\n"
            "def test_second_quote():\n"
            '    lock_then_cap("q_a", 100, rate=11000)\n'
            '    lock_then_cap("q_b", 40, rate=11000)\n'
            '    assert posted_cents("q_a") == 110 and posted_cents("q_b") == 44\n'
        ),
        test_body_short="same — expire flags; capture blocked if expired",
        obs3="expire and capture both credit",
        obs4="expire flags; capture blocked",
        obs5="expire once; capture of expired is 0; second live quote adds",
        fail_obs="FAILED test_expire_not_capture_double - posted 5000 == 0 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "expire_fx",
            'flag_fx(ev["quote_id"], ev.get("cents", 0))',
            "counted every expire",
        )[1],
        skip_new='    if not expired_today(ev["quote_id"]):\n        flag_fx(ev["quote_id"], ev.get("cents", 0))',
        obs7="second quote ok; hides expire-not-credit.",
        still_fail_obs="FAILED if capture ran on expired quote (should be 0) then expire same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def expire_fx(ev):\n"
            "    if not claim_exp(ev['quote_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_expired(ev["quote_id"])\n'
            '    return {"ok": True, "expired": True}\n'
        ),
        rewrite_src_obs="expire claims quote_id; does not credit",
        rewrite_hook=(
            "def capture_exp(quote_id, cents):\n"
            "    if expired(quote_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_fx_live(quote_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_fx(quote_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="capture blocked if expired",
        ddl=_ddl("till_fx_exp", "quote_id", "  expired bool NOT NULL DEFAULT false"),
        ddl_obs="PK quote_id",
        test2_body=(
            "def test_second_quote():\n"
            '    lock_then_cap("q_a", 100, rate=11000)\n'
            '    lock_then_cap("q_b", 40, rate=11000)\n'
            '    assert posted_cents("q_a") == 110 and posted_cents("q_b") == 44\n'
        ),
        xfail_label="capture override after expire",
        xfail_body=(
            "def test_capture_after_expire_override():\n"
            '    expire_fx(q("q_p", cents=0))\n'
            '    capture_exp("q_p", 5000, override=True)\n'
            '    assert posted_cents("q_p") == 5000 and expired("q_p")\n'
        ),
        xfail_fail_obs="FAILED test_capture_after_expire_override - capture blocked; no override\n1 failed",
        xfail_old="def test_capture_after_expire_override():",
        xfail_new='@pytest.mark.xfail(reason="handoff: override capture after expire must audit-bypass block", strict=True)\ndef test_capture_after_expire_override():',
        xfail_patch_obs="xfailed capture after expire override",
        goal="till-fx-exp expire and capture both credited q_1. Expire flags; capture blocked. Gate: tests/test_fx_exp.py.",
        plan="Skip flag if this FX quote already expired today.",
        outcome="Expire+capture double-applied. Expire-day skip hid block. Plan change: expire PK; capture refuses. Primary+second pass. Partial: override after expire xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r126 chargeback vs refund race / refund after chargeback won
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "open_cb",
    'debit_pay(ev["payment_id"], ev["cents"])',
    "counted every chargeback open",
)
pair(
    _ok(
        slug="chargeback-vs-refund-race",
        surfaces="chargeback open hold vs refund debit race",
        avoided="r88 Radar EFW vs refund; r87 Adyen CHARGEBACK; r56 event catalog. This is dispute hold vs refund PK",
        this_is="dispute_id hold; refund PK blocked while dispute open",
        seed="open dispute + refund same payment_id",
        first_apply="payment refunded today",
        plan_change="dispute PK hold; refund PK refund_id refuses while open",
        step_note="Payment-day 6–7; PK 8–11; second payment 12–13.",
        **_paths("cb_rf"),
        table="till_cb_hold",
        pk="dispute_id",
        rg="dispute.open|refund.create|hold_cents|payment_id",
        rg_obs=_rg_obs("cb_rf", "open_cb", "refund_pay", "test_cb_not_refund_double"),
        test_name="cb-not-refund-double test",
        surface_read="chargeback open plus refund",
        skip_pred="this payment already refunded today",
        verb="debit",
        skip_label="payment-refunded-today skip",
        src_body=_src,
        hook_body=(
            "def refund_pay(payment_id, cents):\n"
            "    debit_pay(payment_id, cents)\n"
        ),
        test_body=(
            "def test_cb_not_refund_double():\n"
            '    open_cb(cb("dp_1", payment="pay_1", cents=5000))\n'
            '    open_cb(cb("dp_1", payment="pay_1", cents=5000))\n'
            '    refund_pay("pay_1", 5000)\n'
            '    assert hold_cents("dp_1") == 5000 and refund_cents("pay_1") == 0 and cb_rows("dp_1") == 1\n'
            "\n"
            "def test_second_payment():\n"
            '    refund_pay("pay_a", 100)\n'
            '    refund_pay("pay_b", 40)\n'
            '    assert refund_cents("pay_a") == 100 and refund_cents("pay_b") == 40\n'
        ),
        obs3="open and refund both debit payment",
        obs4="dispute hold PK; refund blocked while open",
        obs5="hold once; refund of disputed is 0; second undispated refund adds",
        fail_obs="FAILED test_cb_not_refund_double - refund 5000 == 0 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not refunded_today(ev["payment_id"]):\n        debit_pay(ev["payment_id"], ev["cents"])',
        obs7="refund still debits; new payment same day dropped.",
        still_fail_obs="FAILED test_cb_not_refund_double - refund still debits disputed pay\n1 failed, 1 passed",
        rewrite_src=(
            "def open_cb(ev):\n"
            "    if not claim_dp(ev['dispute_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    hold_pay(ev["payment_id"], ev["cents"], dispute=ev["dispute_id"])\n'
            '    return {"ok": True, "held": True}\n'
        ),
        rewrite_src_obs="claim dispute_id hold; does not refund",
        rewrite_hook=(
            "def refund_pay(payment_id, cents):\n"
            "    if open_dispute(payment_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    rid = refund_id(payment_id, cents)\n"
            "    if not claim_rf(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_pay(payment_id, cents, refund=rid)\n"
            '    return {"ok": True}\n'
        ),
        obs9="refund blocked while dispute open.",
        rewrite_hook_obs="refund PK; blocked if hold",
        ddl=_ddl("till_cb_hold", "dispute_id", "  payment_id text NOT NULL,\n  hold_cents int NOT NULL"),
        ddl_obs="PK dispute_id",
        test2_body=(
            "def test_second_payment():\n"
            '    refund_pay("pay_a", 100)\n'
            '    refund_pay("pay_b", 40)\n'
            '    assert refund_cents("pay_a") == 100 and refund_cents("pay_b") == 40\n'
        ),
        psql_rows="dp_1",
        residual="partial refund plus partial dispute same payment",
        grep_pat="blocked",
        grep_obs="src/cb_rf.py: refund blocked while open; no split remaining",
        goal="till-cb open and refund both debited pay_1. Dispute hold PK; refund blocked while open. Gate: tests/test_cb_rf.py.",
        plan="Skip debit if this payment already refunded today.",
        outcome="CB+refund double-debited. Payment-day skip left refund unguarded. Plan change: dispute hold PK; refund refuses. Tests 2/2 + second payment + suite 8/8.",
    ),
    _fail(
        slug="refund-after-cb-won",
        surfaces="chargeback lost debit vs later refund",
        avoided="r126 open vs refund; r88 EFW. This is lost already-debited vs second refund",
        this_is="lost dispute already debited; refund no-ops",
        seed="dispute lost + refund same payment",
        first_apply="dispute closed today",
        plan_change="lost PK posts debit once; refund sees already-debited",
        step_note="Close-day 6–7; PK 8–11; second 12–13; refund-after-won xfail 15–17.",
        next_note="Unused: refund after merchant-won dispute. Avoid dispute-closed-today skip.",
        **_paths("cb_won", fail=True),
        table="till_cb_won",
        pk="dispute_id",
        rg="dispute.lost|chargeback.won|refund.after_lost",
        rg_obs=_rg_obs("cb_won", "lose_cb", "refund_after", "test_lost_not_refund_double"),
        test_name="lost-not-refund-double test",
        surface_read="chargeback lost plus refund",
        skip_pred="this dispute already closed today",
        verb="debit",
        skip_label="dispute-closed-today skip",
        src_body=_naive(
            "lose_cb",
            'debit_pay(ev["payment_id"], ev["cents"])',
            "counted every lost dispute",
        )[0],
        hook_body=(
            "def refund_after(payment_id, cents):\n"
            "    debit_pay(payment_id, cents)\n"
        ),
        test_body=(
            "def test_lost_not_refund_double():\n"
            '    lose_cb(cb("dp_1", payment="pay_1", cents=5000, result="lost"))\n'
            '    lose_cb(cb("dp_1", payment="pay_1", cents=5000, result="lost"))\n'
            '    refund_after("pay_1", 5000)\n'
            '    assert debit_cents("pay_1") == 5000 and cb_rows("dp_1") == 1\n'
            "\n"
            "def test_second_dispute():\n"
            '    lose_cb(cb("dp_a", payment="pay_a", cents=100, result="lost"))\n'
            '    lose_cb(cb("dp_b", payment="pay_b", cents=40, result="lost"))\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        test_body_short="same — lost PK debit once; refund no-ops",
        obs3="lost and refund both debit",
        obs4="lost PK; refund no-ops if already debited",
        obs5="debit once; refund of lost is no extra; second dispute adds",
        fail_obs="FAILED test_lost_not_refund_double - debit 10000 == 5000 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "lose_cb",
            'debit_pay(ev["payment_id"], ev["cents"])',
            "counted every lost dispute",
        )[1],
        skip_new='    if not closed_today(ev["dispute_id"]):\n        debit_pay(ev["payment_id"], ev["cents"])',
        obs7="second dispute ok; hides refund double-debit.",
        still_fail_obs="FAILED if refund ran (should no-op) after lost same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def lose_cb(ev):\n"
            "    if not claim_lost(ev['dispute_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_pay(ev["payment_id"], ev["cents"], reason="chargeback_lost")\n'
            '    mark_lost(ev["payment_id"], ev["dispute_id"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="lost claims dispute_id and debit once",
        rewrite_hook=(
            "def refund_after(payment_id, cents):\n"
            "    if lost_payment(payment_id):\n"
            '        return {"ok": True, "already_debited": True}\n'
            "    if not claim_rf2(refund_id(payment_id)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_pay(payment_id, cents, reason=\"refund\")\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="refund no-op if already lost-debited",
        ddl=_ddl("till_cb_won", "dispute_id", "  payment_id text UNIQUE,\n  result text NOT NULL"),
        ddl_obs="PK dispute_id",
        test2_body=(
            "def test_second_dispute():\n"
            '    lose_cb(cb("dp_a", payment="pay_a", cents=100, result="lost"))\n'
            '    lose_cb(cb("dp_b", payment="pay_b", cents=40, result="lost"))\n'
            '    assert debit_cents("pay_a") == 100 and debit_cents("pay_b") == 40\n'
        ),
        xfail_label="refund after merchant-won dispute",
        xfail_body=(
            "def test_refund_after_won():\n"
            '    win_cb(cb("dp_p", payment="pay_p", cents=5000, result="won"))\n'
            '    refund_after("pay_p", 5000)\n'
            '    assert debit_cents("pay_p") == 5000 and result("dp_p") == "won"\n'
        ),
        xfail_fail_obs="FAILED test_refund_after_won - won does not debit; refund path missing for won\n1 failed",
        xfail_old="def test_refund_after_won():",
        xfail_new='@pytest.mark.xfail(reason="handoff: refund after merchant-won must debit; lost path does not apply", strict=True)\ndef test_refund_after_won():',
        xfail_patch_obs="xfailed refund after won",
        goal="till-cb-won lost and refund both debited pay_1. Lost PK; refund no-ops. Gate: tests/test_cb_won.py.",
        plan="Skip debit if this dispute already closed today.",
        outcome="Lost+refund double-debited. Close-day skip hid already-debited. Plan change: lost PK; refund no-ops. Primary+second pass. Partial: refund after won xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r127 tax snapshot vs capture / jurisdiction rematch after capture
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "snap_tax",
    'fulfill_tax(ev["calc_id"], ev["tax_cents"])',
    "counted every tax snapshot",
)
pair(
    _ok(
        slug="tax-snapshot-vs-capture",
        surfaces="tax calculation snapshot vs capture bind",
        avoided="r11 TaxCalculation items hash; r87 tax.transaction.created. This is snapshot_id bind vs capture PK",
        this_is="calc records snapshot; capture PK charge_id binds snapshot_id",
        seed="create tax calc + capture same cart",
        first_apply="tax calculated today",
        plan_change="calc PK calc_id stores; capture PK binds snapshot, does not re-tax",
        step_note="Cart-day 6–7; PK 8–11; second cart 12–13.",
        **_paths("tax_snap"),
        table="till_tax_bind",
        pk="charge_id",
        rg="tax_calc|snapshot_id|capture_bind|tax_cents",
        rg_obs=_rg_obs("tax_snap", "snap_tax", "cap_tax", "test_snap_not_capture_double"),
        test_name="snap-not-capture-double test",
        surface_read="tax snapshot plus capture",
        skip_pred="this cart already tax-calculated today",
        verb="fulfill",
        skip_label="tax-calculated-today skip",
        src_body=_src,
        hook_body=(
            "def cap_tax(charge_id, cents, tax_cents):\n"
            "    fulfill_tax(charge_id, tax_cents)\n"
            "    fulfill_goods(charge_id, cents)\n"
        ),
        test_body=(
            "def test_snap_not_capture_double():\n"
            '    snap_tax(tx("calc_1", tax_cents=400, cart="cart_1"))\n'
            '    snap_tax(tx("calc_1", tax_cents=400, cart="cart_1"))\n'
            '    cap_tax("ch_1", 5000, tax_cents=400)\n'
            '    assert tax_cents("ch_1") == 400 and goods_cents("ch_1") == 5000 and tax_rows("ch_1") == 1\n'
            "\n"
            "def test_second_cart():\n"
            '    snap_tax(tx("calc_a", tax_cents=8, cart="ca"))\n'
            '    cap_tax("ch_a", 100, tax_cents=8)\n'
            '    snap_tax(tx("calc_b", tax_cents=3, cart="cb"))\n'
            '    cap_tax("ch_b", 40, tax_cents=3)\n'
            '    assert tax_cents("ch_a") == 8 and tax_cents("ch_b") == 3\n'
        ),
        obs3="snapshot and capture both fulfill tax",
        obs4="calc stores; capture PK binds snapshot",
        obs5="tax once; snapshot no extra fulfill; second cart adds",
        fail_obs="FAILED test_snap_not_capture_double - tax 800 == 400 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not taxed_today(ev.get("cart")):\n        fulfill_tax(ev["calc_id"], ev["tax_cents"])',
        obs7="capture still fulfills tax; new cart same day dropped.",
        still_fail_obs="FAILED test_snap_not_capture_double - capture still re-taxes\n1 failed, 1 passed",
        rewrite_src=(
            "def snap_tax(ev):\n"
            "    if not claim_calc(ev['calc_id']):\n"
            '        return existing_calc(ev["calc_id"])\n'
            '    store_snap(ev["calc_id"], tax_cents=ev["tax_cents"], cart=ev["cart"])\n'
            '    return {"ok": True, "snapshot": ev["calc_id"]}\n'
        ),
        rewrite_src_obs="claim calc_id; snapshot does not fulfill",
        rewrite_hook=(
            "def cap_tax(charge_id, cents, tax_cents, calc_id=None):\n"
            "    if not claim_tax_ch(charge_id):\n"
            "        return existing_ch(charge_id)\n"
            "    snap = snap_of(calc_id) if calc_id else tax_cents\n"
            "    fulfill_goods(charge_id, cents)\n"
            "    fulfill_tax(charge_id, snap if isinstance(snap, int) else snap.tax_cents, snapshot=calc_id)\n"
            "    return charge_id\n"
        ),
        obs9="capture claims charge_id and binds snapshot.",
        rewrite_hook_obs="PK charge_id; bind snapshot",
        ddl=_ddl("till_tax_bind", "charge_id", "  calc_id text UNIQUE,\n  tax_cents int NOT NULL"),
        ddl_obs="PK charge_id",
        test2_body=(
            "def test_second_cart():\n"
            '    snap_tax(tx("calc_a", tax_cents=8, cart="ca"))\n'
            '    cap_tax("ch_a", 100, tax_cents=8, calc_id="calc_a")\n'
            '    snap_tax(tx("calc_b", tax_cents=3, cart="cb"))\n'
            '    cap_tax("ch_b", 40, tax_cents=3, calc_id="calc_b")\n'
            '    assert tax_cents("ch_a") == 8 and tax_cents("ch_b") == 3\n'
        ),
        psql_rows="ch_1\nch_a\nch_b",
        residual="rate change after snapshot not rematched",
        grep_pat="snapshot",
        grep_obs="src/tax_snap.py: bind snapshot; no post-capture rematch",
        goal="till-tax snapshot and capture both fulfilled tax. Calc stores; capture PK binds snapshot. Gate: tests/test_tax_snap.py.",
        plan="Skip fulfill if this cart already tax-calculated today.",
        outcome="Snap+capture double-taxed. Cart-day skip left capture unguarded. Plan change: calc stores; capture PK binds. Tests 2/2 + second cart + suite 8/8.",
    ),
    _fail(
        slug="tax-juri-after-capture",
        surfaces="tax jurisdiction rematch vs already-captured tax",
        avoided="r127 snapshot bind; r36 tax_exempt. This is rematch-after-capture no-op",
        this_is="address rematch after capture must not post new tax",
        seed="capture then rematch ship-to",
        first_apply="jurisdiction rematched today",
        plan_change="rematch after capture no-ops; captured tax frozen",
        step_note="Rematch-day 6–7; PK 8–11; second 12–13; adjustment xfail 15–17.",
        next_note="Unused: rematch after capture should emit tax adjustment. Avoid rematched-today skip.",
        **_paths("tax_juri", fail=True),
        table="till_tax_juri",
        pk="charge_id",
        rg="jurisdiction|rematch|ship_to|tax_frozen",
        rg_obs=_rg_obs("tax_juri", "rematch_juri", "cap_then", "test_rematch_not_retax"),
        test_name="rematch-not-retax test",
        surface_read="jurisdiction rematch plus captured tax",
        skip_pred="this charge already rematched today",
        verb="tax",
        skip_label="jurisdiction-rematched-today skip",
        src_body=_naive(
            "rematch_juri",
            'fulfill_tax(ev["charge_id"], ev["tax_cents"])',
            "counted every rematch",
        )[0],
        hook_body=(
            "def cap_then(charge_id, cents, tax_cents):\n"
            "    fulfill_tax(charge_id, tax_cents)\n"
            "    fulfill_goods(charge_id, cents)\n"
        ),
        test_body=(
            "def test_rematch_not_retax():\n"
            '    cap_then("ch_1", 5000, tax_cents=400)\n'
            '    rematch_juri(rm("ch_1", tax_cents=650, ship_to="NY"))\n'
            '    rematch_juri(rm("ch_1", tax_cents=650, ship_to="NY"))\n'
            '    assert tax_cents("ch_1") == 400 and captured("ch_1") and juri_rows("ch_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    cap_then("ch_a", 100, tax_cents=8)\n'
            '    cap_then("ch_b", 40, tax_cents=3)\n'
            '    assert tax_cents("ch_a") == 8 and tax_cents("ch_b") == 3\n'
        ),
        test_body_short="same — rematch after capture no-ops; tax frozen",
        obs3="rematch posts new tax after capture",
        obs4="captured tax frozen; rematch records only",
        obs5="tax stays 400; rematch does not extra; second charge adds",
        fail_obs="FAILED test_rematch_not_retax - tax 650 == 400 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "rematch_juri",
            'fulfill_tax(ev["charge_id"], ev["tax_cents"])',
            "counted every rematch",
        )[1],
        skip_new='    if not rematched_today(ev["charge_id"]):\n        fulfill_tax(ev["charge_id"], ev["tax_cents"])',
        obs7="second charge ok; hides freeze.",
        still_fail_obs="FAILED if rematch posted 650 (should freeze 400)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def rematch_juri(ev):\n"
            '    if captured(ev["charge_id"]):\n'
            '        record_juri(ev["charge_id"], ev["ship_to"])\n'
            '        return {"ok": True, "frozen": True}\n'
            "    if not claim_juri(ev['charge_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_tax(ev["charge_id"], ev["tax_cents"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="rematch after capture records only",
        rewrite_hook=(
            "def cap_then(charge_id, cents, tax_cents):\n"
            "    if not claim_tax_ch2(charge_id):\n"
            "        return existing_ch(charge_id)\n"
            "    fulfill_goods(charge_id, cents)\n"
            "    fulfill_tax(charge_id, tax_cents)\n"
            "    mark_captured(charge_id)\n"
            "    return charge_id\n"
        ),
        rewrite_hook_obs="capture PK freezes tax",
        ddl=_ddl("till_tax_juri", "charge_id", "  captured bool NOT NULL DEFAULT false,\n  ship_to text"),
        ddl_obs="PK charge_id",
        test2_body=(
            "def test_second_charge():\n"
            '    cap_then("ch_a", 100, tax_cents=8)\n'
            '    cap_then("ch_b", 40, tax_cents=3)\n'
            '    assert tax_cents("ch_a") == 8 and tax_cents("ch_b") == 3\n'
        ),
        xfail_label="rematch after capture should emit adjustment",
        xfail_body=(
            "def test_rematch_adjustment():\n"
            '    cap_then("ch_p", 5000, tax_cents=400)\n'
            '    rematch_juri(rm("ch_p", tax_cents=650, ship_to="NY"))\n'
            '    assert tax_cents("ch_p") == 400 and adj_cents("ch_p") == 250\n'
        ),
        xfail_fail_obs="FAILED test_rematch_adjustment - no adj row; tax frozen without delta\n1 failed",
        xfail_old="def test_rematch_adjustment():",
        xfail_new='@pytest.mark.xfail(reason="handoff: rematch after capture must emit tax adjustment 250", strict=True)\ndef test_rematch_adjustment():',
        xfail_patch_obs="xfailed rematch adjustment",
        goal="till-tax-juri rematch after capture posted 650. Freeze captured tax. Gate: tests/test_tax_juri.py.",
        plan="Skip tax if this charge already rematched today.",
        outcome="Rematch re-taxed captured charge. Rematch-day skip hid freeze. Plan change: rematch records; tax frozen. Primary+second pass. Partial: adjustment xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r128 split payout vs platform fee / fee clawback after split
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "split_po",
    'credit_dest(ev["transfer_id"], ev["cents"])',
    "counted every split payout",
)
pair(
    _ok(
        slug="split-payout-vs-platform-fee",
        surfaces="destination split payout vs platform application fee",
        avoided="r17 application_fee refund_id; r56 transfer vs fee event catalog. This is dest PK vs fee PK",
        this_is="split PK transfer_id to dest; fee PK fee_id to platform",
        seed="split dest + take fee same charge",
        first_apply="split paid today",
        plan_change="dest claim transfer_id; fee claim fee_id; neither credits the other",
        step_note="Charge-day 6–7; PK 8–11; second charge 12–13.",
        **_paths("split_fee"),
        table="till_split_po",
        pk="transfer_id",
        rg="destination|application_fee|split_cents|platform_fee",
        rg_obs=_rg_obs("split_fee", "split_po", "take_fee", "test_split_not_fee_double"),
        test_name="split-not-fee-double test",
        surface_read="split payout plus platform fee",
        skip_pred="this charge already split-paid today",
        verb="credit",
        skip_label="split-paid-today skip",
        src_body=_src,
        hook_body=(
            "def take_fee(charge_id, fee_cents):\n"
            "    credit_dest(charge_id, fee_cents)\n"
        ),
        test_body=(
            "def test_split_not_fee_double():\n"
            '    split_po(sp("tr_1", charge="ch_1", cents=4500, dest="acct_d"))\n'
            '    split_po(sp("tr_1", charge="ch_1", cents=4500, dest="acct_d"))\n'
            '    take_fee("ch_1", 500)\n'
            '    assert dest_cents("acct_d") == 4500 and plat_cents("plat") == 500 and split_rows("tr_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    split_po(sp("tr_a", charge="ch_a", cents=90, dest="acct_a"))\n'
            '    take_fee("ch_a", 10)\n'
            '    split_po(sp("tr_b", charge="ch_b", cents=36, dest="acct_b"))\n'
            '    take_fee("ch_b", 4)\n'
            '    assert dest_cents("acct_a") == 90 and dest_cents("acct_b") == 36\n'
        ),
        obs3="fee also credits dest",
        obs4="dest PK transfer_id; fee PK fee_id to platform",
        obs5="dest once; fee does not extra dest; second charge adds",
        fail_obs="FAILED test_split_not_fee_double - dest 5000 == 4500 or plat 0 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not split_today(ev["charge"]):\n        credit_dest(ev["transfer_id"], ev["cents"])',
        obs7="fee still credits dest; new charge same day dropped.",
        still_fail_obs="FAILED test_split_not_fee_double - fee still hits dest\n1 failed, 1 passed",
        rewrite_src=(
            "def split_po(ev):\n"
            "    if not claim_tr(ev['transfer_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_dest(ev["dest"], ev["cents"], transfer=ev["transfer_id"])\n'
            '    return {"ok": True, "dest": True}\n'
        ),
        rewrite_src_obs="claim transfer_id credits dest only",
        rewrite_hook=(
            "def take_fee(charge_id, fee_cents):\n"
            "    fid = fee_id(charge_id)\n"
            "    if not claim_fee(fid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_plat(fid, fee_cents, charge=charge_id)\n"
            '    return {"ok": True, "fee": True}\n'
        ),
        obs9="fee claims fee_id to platform.",
        rewrite_hook_obs="PK fee_id platform",
        ddl=_ddl("till_split_po", "transfer_id", "  dest text NOT NULL,\n  fee_id text UNIQUE"),
        ddl_obs="PK transfer_id",
        test2_body=(
            "def test_second_charge():\n"
            '    split_po(sp("tr_a", charge="ch_a", cents=90, dest="acct_a"))\n'
            '    take_fee("ch_a", 10)\n'
            '    split_po(sp("tr_b", charge="ch_b", cents=36, dest="acct_b"))\n'
            '    take_fee("ch_b", 4)\n'
            '    assert dest_cents("acct_a") == 90 and dest_cents("acct_b") == 36 and plat_cents("plat") == 14\n'
        ),
        psql_rows="tr_1\ntr_a\ntr_b",
        residual="fee-inclusive vs exclusive amount",
        grep_pat="credit_plat",
        grep_obs="src/split_fee.py: dest vs plat split; no inclusive-fee invert",
        goal="till-split dest and fee both credited dest. Split PK dest; fee PK platform. Gate: tests/test_split_fee.py.",
        plan="Skip credit if this charge already split-paid today.",
        outcome="Split+fee double-credited dest. Charge-day skip left fee on dest. Plan change: dest PK + fee PK. Tests 2/2 + second charge + suite 8/8.",
    ),
    _fail(
        slug="fee-clawback-after-split",
        surfaces="application fee refund vs dest already paid",
        avoided="r128 split vs fee; r17 fee refund_id. This is clawback PK vs dest stays",
        this_is="fee refund PK; dest transfer not reversed",
        seed="fee refund after dest split paid",
        first_apply="fee clawed today",
        plan_change="clawback PK fee_refund_id; dest stays paid",
        step_note="Fee-day 6–7; PK 8–11; second 12–13; dest clawback xfail 15–17.",
        next_note="Unused: dest clawback after fee refund. Avoid fee-clawed-today skip.",
        **_paths("fee_claw", fail=True),
        table="till_fee_claw",
        pk="fee_refund_id",
        rg="application_fee.refund|clawback|dest_stays",
        rg_obs=_rg_obs("fee_claw", "claw_fee", "split_then", "test_claw_not_dest_reverse"),
        test_name="claw-not-dest-reverse test",
        surface_read="fee clawback plus dest split",
        skip_pred="this fee already clawed today",
        verb="reverse",
        skip_label="fee-clawed-today skip",
        src_body=_naive(
            "claw_fee",
            'debit_dest(ev["transfer_id"], ev["cents"])',
            "counted every fee clawback",
        )[0],
        hook_body=(
            "def split_then(transfer_id, dest, cents):\n"
            "    credit_dest(dest, cents, transfer=transfer_id)\n"
        ),
        test_body=(
            "def test_claw_not_dest_reverse():\n"
            '    split_then("tr_1", "acct_d", 4500)\n'
            '    claw_fee(cf("fr_1", transfer="tr_1", cents=500))\n'
            '    claw_fee(cf("fr_1", transfer="tr_1", cents=500))\n'
            '    assert dest_cents("acct_d") == 4500 and plat_cents("plat") == -500 and claw_rows("fr_1") == 1\n'
            "\n"
            "def test_second_fee():\n"
            '    split_then("tr_a", "acct_a", 90)\n'
            '    claw_fee(cf("fr_a", transfer="tr_a", cents=10))\n'
            '    split_then("tr_b", "acct_b", 36)\n'
            '    claw_fee(cf("fr_b", transfer="tr_b", cents=4))\n'
            '    assert dest_cents("acct_a") == 90 and dest_cents("acct_b") == 36\n'
        ),
        test_body_short="same — clawback PK; dest stays",
        obs3="clawback also debits dest",
        obs4="clawback PK fee_refund_id; dest stays",
        obs5="dest stays; plat -500; second dest adds",
        fail_obs="FAILED test_claw_not_dest_reverse - dest 4000 == 4500 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "claw_fee",
            'debit_dest(ev["transfer_id"], ev["cents"])',
            "counted every fee clawback",
        )[1],
        skip_new='    if not clawed_today(ev.get("fee_id")):\n        debit_dest(ev["transfer_id"], ev["cents"])',
        obs7="second fee ok; hides dest stay.",
        still_fail_obs="FAILED if clawback debited dest (should hit plat only)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def claw_fee(ev):\n"
            "    if not claim_fr(ev['fee_refund_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    debit_plat(ev["fee_refund_id"], ev["cents"])\n'
            '    return {"ok": True, "claw": True}\n'
        ),
        rewrite_src_obs="claim fee_refund_id debit platform",
        rewrite_hook=(
            "def split_then(transfer_id, dest, cents):\n"
            "    if not claim_tr2(transfer_id):\n"
            "        return existing_tr(transfer_id)\n"
            "    credit_dest(dest, cents, transfer=transfer_id)\n"
            "    return transfer_id\n"
        ),
        rewrite_hook_obs="dest PK stays after claw",
        ddl=_ddl("till_fee_claw", "fee_refund_id", "  transfer_id text NOT NULL"),
        ddl_obs="PK fee_refund_id",
        test2_body=(
            "def test_second_fee():\n"
            '    split_then("tr_a", "acct_a", 90)\n'
            '    claw_fee(cf("fr_a", fee_refund_id="fr_a", transfer="tr_a", cents=10))\n'
            '    split_then("tr_b", "acct_b", 36)\n'
            '    claw_fee(cf("fr_b", fee_refund_id="fr_b", transfer="tr_b", cents=4))\n'
            '    assert dest_cents("acct_a") == 90 and dest_cents("acct_b") == 36\n'
        ),
        xfail_label="dest clawback after fee refund",
        xfail_body=(
            "def test_dest_claw_after_fee():\n"
            '    split_then("tr_p", "acct_p", 4500)\n'
            '    claw_fee(cf("fr_p", fee_refund_id="fr_p", transfer="tr_p", cents=500))\n'
            '    claw_dest("tr_p", 4500)\n'
            '    assert dest_cents("acct_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_dest_claw_after_fee - dest stays 4500; no dest claw path\n1 failed",
        xfail_old="def test_dest_claw_after_fee():",
        xfail_new='@pytest.mark.xfail(reason="handoff: dest clawback after fee refund is a separate transfer reverse", strict=True)\ndef test_dest_claw_after_fee():',
        xfail_patch_obs="xfailed dest claw after fee",
        goal="till-fee-claw clawback reversed dest. Clawback PK plat; dest stays. Gate: tests/test_fee_claw.py.",
        plan="Skip reverse if this fee already clawed today.",
        outcome="Clawback hit dest. Fee-day skip hid dest stay. Plan change: fee_refund PK plat. Primary+second pass. Partial: dest claw xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r129 rolling reserve hold vs release / release after chargeback
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "accrue_rsv",
    'post_rsv(ev["reserve_id"], ev["cents"])',
    "counted every reserve accrue",
)
pair(
    _ok(
        slug="rolling-reserve-hold-vs-rel",
        surfaces="rolling reserve accrue vs weekly release",
        avoided="r13 treasury inbound; r89 outbound posted. This is (merchant, period) hold vs release_id",
        this_is="accrue PK (merchant, period); release PK deducts held",
        seed="accrue period + release same reserve_id",
        first_apply="reserve released today",
        plan_change="accrue claims period; release claims release_id against held",
        step_note="Merchant-day 6–7; PK 8–11; second period 12–13.",
        **_paths("roll_rsv"),
        table="till_roll_hold",
        pk="reserve_id",
        rg="rolling_reserve|accrue_period|weekly_release|held_cents",
        rg_obs=_rg_obs("roll_rsv", "accrue_rsv", "release_rsv", "test_accrue_not_release_double"),
        test_name="accrue-not-release-double test",
        surface_read="rolling reserve accrue plus weekly release",
        skip_pred="this merchant reserve already released today",
        verb="post",
        skip_label="reserve-released-today skip",
        src_body=_src,
        hook_body=(
            "def release_rsv(reserve_id, cents):\n"
            "    post_rsv(reserve_id, cents)\n"
        ),
        test_body=(
            "def test_accrue_not_release_double():\n"
            '    accrue_rsv(rv("rs_1", merchant="m_1", period="2026-W33", cents=500))\n'
            '    accrue_rsv(rv("rs_1", merchant="m_1", period="2026-W33", cents=500))\n'
            '    release_rsv("rs_1", 500)\n'
            '    assert held_cents("m_1") == 0 and released_cents("rel_1") == 500 and rsv_rows("rs_1") == 1\n'
            "\n"
            "def test_second_period():\n"
            '    accrue_rsv(rv("rs_a", merchant="m_a", period="2026-W32", cents=100))\n'
            '    accrue_rsv(rv("rs_b", merchant="m_b", period="2026-W32", cents=40))\n'
            '    assert held_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        obs3="accrue and release both post same cents",
        obs4="accrue holds; release deducts held to available",
        obs5="hold then release to 0; accrue no extra; second period holds",
        fail_obs="FAILED test_accrue_not_release_double - held 1000 or released 0 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not released_today(ev["merchant"]):\n        post_rsv(ev["reserve_id"], ev["cents"])',
        obs7="release still posts extra; new merchant same day dropped.",
        still_fail_obs="FAILED test_accrue_not_release_double - release still posts as accrue\n1 failed, 1 passed",
        rewrite_src=(
            "def accrue_rsv(ev):\n"
            "    if not claim_rsv(ev['reserve_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    hold_rsv(ev["merchant"], ev["cents"], period=ev["period"])\n'
            '    return {"ok": True, "held": True}\n'
        ),
        rewrite_src_obs="claim reserve_id holds; does not release",
        rewrite_hook=(
            "def release_rsv(reserve_id, cents):\n"
            "    rid = rel_id(reserve_id)\n"
            "    if not claim_rel(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if held_of(reserve_id) < cents:\n"
            '        return {"ok": True, "short": True}\n'
            "    release_held(reserve_id, cents, release=rid)\n"
            '    return {"ok": True, "released": True}\n'
        ),
        obs9="release claims release_id against held.",
        rewrite_hook_obs="PK release_id deducts held",
        ddl=_ddl("till_roll_hold", "reserve_id", "  merchant text NOT NULL,\n  period text NOT NULL,\n  UNIQUE (merchant, period)"),
        ddl_obs="PK reserve_id",
        test2_body=(
            "def test_second_period():\n"
            '    accrue_rsv(rv("rs_a", merchant="m_a", period="2026-W32", cents=100))\n'
            '    accrue_rsv(rv("rs_b", merchant="m_b", period="2026-W32", cents=40))\n'
            '    assert held_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        psql_rows="rs_1\nrs_a\nrs_b",
        residual="partial weekly release",
        grep_pat="short",
        grep_obs="src/roll_rsv.py: release vs held; no partial schedule",
        goal="till-roll accrue and release both posted rs_1. Accrue holds; release deducts. Gate: tests/test_roll_rsv.py.",
        plan="Skip post if this merchant reserve already released today.",
        outcome="Accrue+release double-posted. Merchant-day skip left release as post. Plan change: hold PK + release PK. Tests 2/2 + second period + suite 8/8.",
    ),
    _fail(
        slug="reserve-rel-after-cb",
        surfaces="reserve release vs chargeback against reserved funds",
        avoided="r129 accrue vs release; r126 cb vs refund. This is chargeback consumes reserve first",
        this_is="chargeback deducts held; release remaining only",
        seed="chargeback against reserve then weekly release",
        first_apply="chargeback reserved today",
        plan_change="cb consumes held first; release remaining",
        step_note="CB-day 6–7; PK 8–11; second 12–13; release-consumed xfail 15–17.",
        next_note="Unused: release of already-consumed reserve. Avoid chargeback-reserved-today skip.",
        **_paths("rsv_cb", fail=True),
        table="till_roll_rel",
        pk="cb_id",
        rg="reserve_consume|chargeback.held|release_remaining",
        rg_obs=_rg_obs("rsv_cb", "cb_rsv", "rel_after", "test_cb_not_release_double"),
        test_name="cb-not-release-double test",
        surface_read="chargeback against reserve plus release",
        skip_pred="this merchant chargeback already reserved today",
        verb="consume",
        skip_label="chargeback-reserved-today skip",
        src_body=_naive(
            "cb_rsv",
            'post_rsv(ev["reserve_id"], -ev["cents"])',
            "counted every reserve chargeback",
        )[0],
        hook_body=(
            "def rel_after(reserve_id, cents):\n"
            "    post_rsv(reserve_id, -cents)\n"
        ),
        test_body=(
            "def test_cb_not_release_double():\n"
            '    hold_rsv("m_1", 500, period="2026-W33")\n'
            '    cb_rsv(cbr("cb_1", reserve="rs_1", cents=500))\n'
            '    cb_rsv(cbr("cb_1", reserve="rs_1", cents=500))\n'
            '    rel_after("rs_1", 500)\n'
            '    assert held_cents("m_1") == 0 and released_cents("rs_1") == 0 and cb_rows("cb_1") == 1\n'
            "\n"
            "def test_second_merchant():\n"
            '    hold_rsv("m_a", 100, period="2026-W32")\n'
            '    hold_rsv("m_b", 40, period="2026-W32")\n'
            '    assert held_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        test_body_short="same — cb consumes held; release remaining 0",
        obs3="cb and release both debit held",
        obs4="cb consumes; release remaining only",
        obs5="held 0 after cb; release no extra debit; second merchant holds",
        fail_obs="FAILED test_cb_not_release_double - held -500 or released 500\n1 failed, 1 passed",
        skip_old=_naive(
            "cb_rsv",
            'post_rsv(ev["reserve_id"], -ev["cents"])',
            "counted every reserve chargeback",
        )[1],
        skip_new='    if not cb_reserved_today(ev.get("merchant")):\n        post_rsv(ev["reserve_id"], -ev["cents"])',
        obs7="second merchant ok; hides consume-then-remaining.",
        still_fail_obs="FAILED if release also debited (held went negative)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def cb_rsv(ev):\n"
            "    if not claim_cb_rsv(ev['cb_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    consume_held(ev["reserve_id"], ev["cents"], cb=ev["cb_id"])\n'
            '    return {"ok": True, "consumed": True}\n'
        ),
        rewrite_src_obs="claim cb_id consumes held",
        rewrite_hook=(
            "def rel_after(reserve_id, cents):\n"
            "    avail = held_of(reserve_id)\n"
            "    if avail <= 0:\n"
            '        return {"ok": True, "nothing": True}\n'
            "    take = min(avail, cents)\n"
            "    if not claim_rel2(rel_id(reserve_id)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    release_held(reserve_id, take)\n"
            '    return {"ok": True, "released": take}\n'
        ),
        rewrite_hook_obs="release remaining only",
        ddl=_ddl("till_roll_rel", "cb_id", "  reserve_id text NOT NULL,\n  consumed int NOT NULL"),
        ddl_obs="PK cb_id",
        test2_body=(
            "def test_second_merchant():\n"
            '    hold_rsv("m_a", 100, period="2026-W32")\n'
            '    hold_rsv("m_b", 40, period="2026-W32")\n'
            '    assert held_cents("m_a") == 100 and held_cents("m_b") == 40\n'
        ),
        xfail_label="release of already-consumed reserve",
        xfail_body=(
            "def test_release_consumed():\n"
            '    hold_rsv("m_p", 500, period="2026-W30")\n'
            '    cb_rsv(cbr("cb_p", reserve="rs_p", cents=500))\n'
            '    out = rel_after("rs_p", 500)\n'
            '    assert out["released"] == 500\n'
        ),
        xfail_fail_obs="FAILED test_release_consumed - nothing to release; consumed already\n1 failed",
        xfail_old="def test_release_consumed():",
        xfail_new='@pytest.mark.xfail(reason="handoff: release of consumed reserve must fail closed, not pretend 500", strict=True)\ndef test_release_consumed():',
        xfail_patch_obs="xfailed release consumed",
        goal="till-rsv-cb chargeback and release both debited held. CB consumes; release remaining. Gate: tests/test_rsv_cb.py.",
        plan="Skip consume if this merchant chargeback already reserved today.",
        outcome="CB+release double-debited held. CB-day skip hid remaining. Plan change: consume then remaining. Primary+second pass. Partial: release consumed xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r130 FX reval vs original post / reval after books final
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "reval_fx",
    'post_ledger(ev["account_id"], ev["cents"])',
    "counted every fx reval",
)
pair(
    _ok(
        slug="fx-reval-vs-original-post",
        surfaces="month-end FX reval vs original journal post",
        avoided="r125 fx lock vs capture; r130 is mark-to-spot delta not original restatement",
        this_is="reval PK (account, as_of) posts (mark-spot)*qty delta only",
        seed="original post + month-end reval same account",
        first_apply="account revalued today",
        plan_change="original PK journal_id; reval PK (account, as_of) delta",
        step_note="Account-day 6–7; PK 8–11; second account 12–13.",
        **_paths("fx_reval"),
        table="till_reval_jnl",
        pk="reval_id",
        rg="fx_reval|as_of|mark_spot|delta_cents",
        rg_obs=_rg_obs("fx_reval", "reval_fx", "post_orig", "test_reval_not_restatement"),
        test_name="reval-not-restatement test",
        surface_read="FX reval plus original journal",
        skip_pred="this account already revalued today",
        verb="post",
        skip_label="account-revalued-today skip",
        src_body=_src,
        hook_body=(
            "def post_orig(account_id, cents, ccy):\n"
            "    post_ledger(account_id, cents)\n"
        ),
        test_body=(
            "def test_reval_not_restatement():\n"
            '    post_orig("acct_1", 5000, "EUR")\n'
            '    reval_fx(rvx("rv_1", account="acct_1", as_of="2026-08-31", orig=5000, mark=5200))\n'
            '    reval_fx(rvx("rv_1", account="acct_1", as_of="2026-08-31", orig=5000, mark=5200))\n'
            '    assert posted_cents("acct_1") == 5200 and reval_cents("rv_1") == 200 and reval_rows("rv_1") == 1\n'
            "\n"
            "def test_second_account():\n"
            '    post_orig("acct_a", 100, "EUR")\n'
            '    reval_fx(rvx("rv_a", account="acct_a", as_of="2026-08-31", orig=100, mark=110))\n'
            '    post_orig("acct_b", 40, "EUR")\n'
            '    reval_fx(rvx("rv_b", account="acct_b", as_of="2026-08-31", orig=40, mark=44))\n'
            '    assert posted_cents("acct_a") == 110 and posted_cents("acct_b") == 44\n'
        ),
        obs3="reval re-posts original 5000",
        obs4="original stays; reval posts delta 200",
        obs5="posted 5200 = 5000+200; reval once; second account adds",
        fail_obs="FAILED test_reval_not_restatement - posted 10000 or 5000 not 5200\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not revalued_today(ev["account_id"]):\n        post_ledger(ev["account_id"], ev["cents"])',
        obs7="reval still restates original; new account same day dropped.",
        still_fail_obs="FAILED test_reval_not_restatement - reval posted orig not delta\n1 failed, 1 passed",
        rewrite_src=(
            "def reval_fx(ev):\n"
            "    rid = ev['reval_id']\n"
            "    if not claim_reval(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            '    delta = ev["mark"] - ev["orig"]\n'
            "    post_ledger(ev['account_id'], delta, reason='fx_reval', as_of=ev['as_of'])\n"
            '    return {"ok": True, "delta": delta}\n'
        ),
        rewrite_src_obs="claim reval_id posts delta only",
        rewrite_hook=(
            "def post_orig(account_id, cents, ccy):\n"
            "    jid = orig_id(account_id, cents)\n"
            "    if not claim_orig(jid):\n"
            "        return existing_jnl(jid)\n"
            "    post_ledger(account_id, cents, ccy=ccy, journal=jid)\n"
            "    return jid\n"
        ),
        obs9="original claims journal_id separately.",
        rewrite_hook_obs="original PK; reval delta",
        ddl=_ddl("till_reval_jnl", "reval_id", "  account_id text NOT NULL,\n  as_of date NOT NULL,\n  UNIQUE (account_id, as_of)"),
        ddl_obs="PK reval_id",
        test2_body=(
            "def test_second_account():\n"
            '    post_orig("acct_a", 100, "EUR")\n'
            '    reval_fx(rvx("rv_a", account="acct_a", as_of="2026-08-31", orig=100, mark=110))\n'
            '    post_orig("acct_b", 40, "EUR")\n'
            '    reval_fx(rvx("rv_b", account="acct_b", as_of="2026-08-31", orig=40, mark=44))\n'
            '    assert posted_cents("acct_a") == 110 and posted_cents("acct_b") == 44\n'
        ),
        psql_rows="rv_1\nrv_a\nrv_b",
        residual="intra-day second reval same as_of",
        grep_pat="delta",
        grep_obs="src/fx_reval.py: delta = mark-orig; no intra-day as_of bump",
        goal="till-reval reval restated original 5000. Reval PK delta only. Gate: tests/test_fx_reval.py.",
        plan="Skip post if this account already revalued today.",
        outcome="Reval restated original. Account-day skip left restatement. Plan change: reval PK delta. Tests 2/2 + second account + suite 8/8.",
    ),
    _fail(
        slug="reval-after-books-final",
        surfaces="FX reval vs already-finalized settlement books",
        avoided="r130 reval delta; r124 settle window. This is books_final blocks reval",
        this_is="final window blocks reval; prior-period needs reversing entry",
        seed="finalize books then reval as_of inside window",
        first_apply="settlement finalized today",
        plan_change="final PK window_id; reval refused if as_of <= final",
        step_note="Final-day 6–7; PK 8–11; second 12–13; prior-period xfail 15–17.",
        next_note="Unused: prior-period reval after books close. Avoid settlement-finalized-today skip.",
        **_paths("reval_fin", fail=True),
        table="till_reval_fin",
        pk="window_id",
        rg="books_final|prior_period|reval_blocked|period_lock",
        rg_obs=_rg_obs("reval_fin", "final_books", "reval_late", "test_final_not_reval"),
        test_name="final-not-reval test",
        surface_read="books finalize plus late reval",
        skip_pred="this settlement already finalized today",
        verb="lock",
        skip_label="settlement-finalized-today skip",
        src_body=_naive(
            "final_books",
            'post_ledger(ev["window_id"], ev.get("cents", 0))',
            "counted every books final",
        )[0],
        hook_body=(
            "def reval_late(account_id, as_of, delta):\n"
            "    post_ledger(account_id, delta)\n"
        ),
        test_body=(
            "def test_final_not_reval():\n"
            '    final_books(fb("w_1", as_of="2026-08-31"))\n'
            '    final_books(fb("w_1", as_of="2026-08-31"))\n'
            '    reval_late("acct_1", "2026-08-31", 200)\n'
            '    assert finalized("w_1") and posted_cents("acct_1") == 0 and fin_rows("w_1") == 1\n'
            "\n"
            "def test_second_window():\n"
            '    final_books(fb("w_a", as_of="2026-07-31"))\n'
            '    final_books(fb("w_b", as_of="2026-06-30"))\n'
            '    assert finalized("w_a") and finalized("w_b")\n'
        ),
        test_body_short="same — final PK; reval blocked if as_of <= final",
        obs3="final and late reval both post",
        obs4="final PK; reval blocked",
        obs5="acct 0 after blocked reval; second window finals",
        fail_obs="FAILED test_final_not_reval - posted 200 == 0 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "final_books",
            'post_ledger(ev["window_id"], ev.get("cents", 0))',
            "counted every books final",
        )[1],
        skip_new='    if not finalized_today(ev["window_id"]):\n        post_ledger(ev["window_id"], ev.get("cents", 0))',
        obs7="second window ok; hides reval block.",
        still_fail_obs="FAILED if late reval posted 200 into finalized window\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def final_books(ev):\n"
            "    if not claim_fin(ev['window_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_final(ev["window_id"], ev["as_of"])\n'
            '    return {"ok": True, "final": True}\n'
        ),
        rewrite_src_obs="claim window_id marks final; no ledger post",
        rewrite_hook=(
            "def reval_late(account_id, as_of, delta):\n"
            "    if books_final_on(as_of):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_reval2(reval_id(account_id, as_of)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    post_ledger(account_id, delta, reason='fx_reval')\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="reval blocked if books final",
        ddl=_ddl("till_reval_fin", "window_id", "  as_of date NOT NULL,\n  final bool NOT NULL DEFAULT true"),
        ddl_obs="PK window_id",
        test2_body=(
            "def test_second_window():\n"
            '    final_books(fb("w_a", as_of="2026-07-31"))\n'
            '    final_books(fb("w_b", as_of="2026-06-30"))\n'
            '    assert finalized("w_a") and finalized("w_b")\n'
        ),
        xfail_label="prior-period reval after books close",
        xfail_body=(
            "def test_prior_period_reval():\n"
            '    final_books(fb("w_p", as_of="2026-08-31"))\n'
            '    out = reval_late("acct_p", "2026-08-31", 200, reversing=True)\n'
            '    assert posted_cents("acct_p") == 200 and out["reversing"]\n'
        ),
        xfail_fail_obs="FAILED test_prior_period_reval - blocked; no reversing entry path\n1 failed",
        xfail_old="def test_prior_period_reval():",
        xfail_new='@pytest.mark.xfail(reason="handoff: prior-period reval after close needs reversing entry", strict=True)\ndef test_prior_period_reval():',
        xfail_patch_obs="xfailed prior-period reval",
        goal="till-reval-fin late reval posted into final books. Final PK blocks reval. Gate: tests/test_reval_fin.py.",
        plan="Skip lock if this settlement already finalized today.",
        outcome="Late reval posted into final. Final-day skip hid block. Plan change: final PK; reval refuses. Primary+second pass. Partial: prior-period xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r131 intercompany vs contra / reverse after contra
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "post_ic",
    'post_ledger(ev["entity_id"], ev["cents"])',
    "counted every intercompany post",
)
pair(
    _ok(
        slug="intercompany-vs-contra",
        surfaces="intercompany debit vs contra credit same pair_id",
        avoided="r62 gRPC journal; r80 outbox/inbox. This is two-sided pair_id not dual journal",
        this_is="IC PK pair_id posts both sides once; contra is the other side",
        seed="IC debit + contra credit same pair_id",
        first_apply="IC posted today",
        plan_change="claim pair_id posts debit+credit; contra is not a second post",
        step_note="Entity-day 6–7; PK 8–11; second pair 12–13.",
        **_paths("ic_pair"),
        table="till_ic_xfer",
        pk="pair_id",
        rg="intercompany|contra_credit|pair_id|two_sided",
        rg_obs=_rg_obs("ic_pair", "post_ic", "post_contra", "test_ic_not_contra_double"),
        test_name="ic-not-contra-double test",
        surface_read="intercompany debit plus contra credit",
        skip_pred="this entity already IC-posted today",
        verb="post",
        skip_label="ic-posted-today skip",
        src_body=_src,
        hook_body=(
            "def post_contra(pair_id, entity_id, cents):\n"
            "    post_ledger(entity_id, -cents)\n"
        ),
        test_body=(
            "def test_ic_not_contra_double():\n"
            '    post_ic(ic("pr_1", debit="e_a", credit="e_b", cents=5000))\n'
            '    post_ic(ic("pr_1", debit="e_a", credit="e_b", cents=5000))\n'
            '    post_contra("pr_1", "e_b", 5000)\n'
            '    assert posted_cents("e_a") == 5000 and posted_cents("e_b") == -5000 and ic_rows("pr_1") == 1\n'
            "\n"
            "def test_second_pair():\n"
            '    post_ic(ic("pr_a", debit="e_c", credit="e_d", cents=100))\n'
            '    post_ic(ic("pr_b", debit="e_e", credit="e_f", cents=40))\n'
            '    assert posted_cents("e_c") == 100 and posted_cents("e_e") == 40\n'
        ),
        obs3="IC and contra both post to one entity",
        obs4="pair_id two-sided; contra is the other side",
        obs5="debit+credit once; contra no extra; second pair adds",
        fail_obs="FAILED test_ic_not_contra_double - e_b -10000 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not ic_today(ev["entity_id"]):\n        post_ledger(ev["entity_id"], ev["cents"])',
        obs7="contra still posts extra; new entity same day dropped.",
        still_fail_obs="FAILED test_ic_not_contra_double - contra double-posted credit\n1 failed, 1 passed",
        rewrite_src=(
            "def post_ic(ev):\n"
            "    if not claim_pair(ev['pair_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    post_ledger(ev["debit"], ev["cents"], pair=ev["pair_id"], side="debit")\n'
            '    post_ledger(ev["credit"], -ev["cents"], pair=ev["pair_id"], side="credit")\n'
            '    return {"ok": True, "paired": True}\n'
        ),
        rewrite_src_obs="claim pair_id posts both sides once",
        rewrite_hook=(
            "def post_contra(pair_id, entity_id, cents):\n"
            "    if pair_posted(pair_id):\n"
            '        return {"ok": True, "already": True}\n'
            "    if not claim_pair(pair_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    post_ledger(entity_id, -cents, pair=pair_id, side='credit')\n"
            '    return {"ok": True}\n'
        ),
        obs9="contra no-ops if pair already posted.",
        rewrite_hook_obs="contra is the other side",
        ddl=_ddl("till_ic_xfer", "pair_id", "  debit_entity text NOT NULL,\n  credit_entity text NOT NULL"),
        ddl_obs="PK pair_id",
        test2_body=(
            "def test_second_pair():\n"
            '    post_ic(ic("pr_a", debit="e_c", credit="e_d", cents=100))\n'
            '    post_ic(ic("pr_b", debit="e_e", credit="e_f", cents=40))\n'
            '    assert posted_cents("e_c") == 100 and posted_cents("e_e") == 40\n'
        ),
        psql_rows="pr_1\npr_a\npr_b",
        residual="multi-entity chain A-B-C",
        grep_pat="paired",
        grep_obs="src/ic_pair.py: two-sided pair; no chain hop",
        goal="till-ic IC and contra both posted e_b twice. Pair_id two-sided. Gate: tests/test_ic_pair.py.",
        plan="Skip post if this entity already IC-posted today.",
        outcome="IC+contra double-posted. Entity-day skip left contra extra. Plan change: pair_id both sides. Tests 2/2 + second pair + suite 8/8.",
    ),
    _fail(
        slug="ic-reverse-after-contra",
        surfaces="IC reverse vs already-posted contra",
        avoided="r131 pair_id two-sided; r124 reverse after close. This is reverse both sides or none",
        this_is="reverse claims pair_id both sides; period lock blocks",
        seed="reverse IC after contra already posted",
        first_apply="IC reversed today",
        plan_change="reverse PK pair_id flips both sides; one-sided refuse",
        step_note="Reverse-day 6–7; PK 8–11; second 12–13; period-lock xfail 15–17.",
        next_note="Unused: reverse after period lock. Avoid ic-reversed-today skip.",
        **_paths("ic_rev", fail=True),
        table="till_ic_rev",
        pk="pair_id",
        rg="ic_reverse|both_sides|period_lock|one_sided",
        rg_obs=_rg_obs("ic_rev", "rev_ic", "posted_contra", "test_rev_not_one_sided"),
        test_name="rev-not-one-sided test",
        surface_read="IC reverse plus posted contra",
        skip_pred="this pair already IC-reversed today",
        verb="reverse",
        skip_label="ic-reversed-today skip",
        src_body=_naive(
            "rev_ic",
            'post_ledger(ev["entity_id"], -ev["cents"])',
            "counted every IC reverse",
        )[0],
        hook_body=(
            "def posted_contra(pair_id, entity_id, cents):\n"
            "    post_ledger(entity_id, -cents)\n"
        ),
        test_body=(
            "def test_rev_not_one_sided():\n"
            '    post_pair("pr_1", "e_a", "e_b", 5000)\n'
            '    rev_ic(icr("pr_1", entity="e_a", cents=5000))\n'
            '    rev_ic(icr("pr_1", entity="e_a", cents=5000))\n'
            '    assert posted_cents("e_a") == 0 and posted_cents("e_b") == 0 and rev_rows("pr_1") == 1\n'
            "\n"
            "def test_second_pair():\n"
            '    post_pair("pr_a", "e_c", "e_d", 100)\n'
            '    rev_ic(icr("pr_a", entity="e_c", cents=100))\n'
            '    post_pair("pr_b", "e_e", "e_f", 40)\n'
            '    assert posted_cents("e_c") == 0 and posted_cents("e_e") == 40\n'
        ),
        test_body_short="same — reverse both sides under pair_id",
        obs3="reverse only one side",
        obs4="reverse PK flips both sides",
        obs5="both zero; reverse once; second pair independent",
        fail_obs="FAILED test_rev_not_one_sided - e_b still -5000 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "rev_ic",
            'post_ledger(ev["entity_id"], -ev["cents"])',
            "counted every IC reverse",
        )[1],
        skip_new='    if not reversed_today(ev["pair_id"]):\n        post_ledger(ev["entity_id"], -ev["cents"])',
        obs7="second pair ok; hides one-sided reverse.",
        still_fail_obs="FAILED if reverse only flipped e_a (e_b still -5000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def rev_ic(ev):\n"
            "    if not claim_rev(ev['pair_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if period_locked(ev['pair_id']):\n"
            '        return {"ok": True, "locked": True}\n'
            "    flip_pair(ev['pair_id'])\n"
            '    return {"ok": True, "reversed": True}\n'
        ),
        rewrite_src_obs="claim pair_id flips both sides",
        rewrite_hook=(
            "def posted_contra(pair_id, entity_id, cents):\n"
            "    if pair_posted(pair_id):\n"
            '        return {"ok": True, "already": True}\n'
            "    post_ledger(entity_id, -cents, pair=pair_id)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="contra already inside pair",
        ddl=_ddl("till_ic_rev", "pair_id", "  reversed bool NOT NULL DEFAULT false"),
        ddl_obs="PK pair_id",
        test2_body=(
            "def test_second_pair():\n"
            '    post_pair("pr_a", "e_c", "e_d", 100)\n'
            '    rev_ic(icr("pr_a", entity="e_c", cents=100))\n'
            '    post_pair("pr_b", "e_e", "e_f", 40)\n'
            '    assert posted_cents("e_c") == 0 and posted_cents("e_e") == 40\n'
        ),
        xfail_label="reverse after period lock",
        xfail_body=(
            "def test_rev_after_lock():\n"
            '    post_pair("pr_p", "e_p", "e_q", 5000)\n'
            '    lock_period("pr_p")\n'
            '    rev_ic(icr("pr_p", entity="e_p", cents=5000))\n'
            '    assert posted_cents("e_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_rev_after_lock - locked; pair not flipped\n1 failed",
        xfail_old="def test_rev_after_lock():",
        xfail_new='@pytest.mark.xfail(reason="handoff: reverse after period lock needs unlock ticket", strict=True)\ndef test_rev_after_lock():',
        xfail_patch_obs="xfailed reverse after lock",
        goal="till-ic-rev reverse flipped only one side. Reverse PK both sides. Gate: tests/test_ic_rev.py.",
        plan="Skip reverse if this pair already IC-reversed today.",
        outcome="Reverse one-sided. Reverse-day skip hid both-sides. Plan change: flip pair. Primary+second pass. Partial: period-lock xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r132 escrow milestone vs release / dispute after release
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "accept_ms",
    'credit_seller(ev["milestone_id"], ev["cents"])',
    "counted every milestone accept",
)
pair(
    _ok(
        slug="escrow-milestone-vs-release",
        surfaces="escrow milestone accept vs funds release",
        avoided="r67 Braintree escrow; r63 delayed capture. This is milestone_id record vs release_id",
        this_is="accept records milestone; release PK pays seller",
        seed="accept milestone + release same escrow",
        first_apply="milestone accepted today",
        plan_change="accept records; release PK release_id credits seller",
        step_note="Escrow-day 6–7; PK 8–11; second escrow 12–13.",
        **_paths("esc_ms"),
        table="till_esc_ms",
        pk="release_id",
        rg="escrow.milestone|accept|funds_release|seller_credit",
        rg_obs=_rg_obs("esc_ms", "accept_ms", "release_esc", "test_accept_not_release_double"),
        test_name="accept-not-release-double test",
        surface_read="milestone accept plus funds release",
        skip_pred="this milestone already accepted today",
        verb="credit",
        skip_label="milestone-accepted-today skip",
        src_body=_src,
        hook_body=(
            "def release_esc(escrow_id, cents):\n"
            "    credit_seller(escrow_id, cents)\n"
        ),
        test_body=(
            "def test_accept_not_release_double():\n"
            '    accept_ms(ms("ms_1", escrow="es_1", cents=5000))\n'
            '    accept_ms(ms("ms_1", escrow="es_1", cents=5000))\n'
            '    release_esc("es_1", 5000)\n'
            '    assert accepted("ms_1") and seller_cents("s_1") == 5000 and esc_rows("rel_1") == 1\n'
            "\n"
            "def test_second_escrow():\n"
            '    accept_ms(ms("ms_a", escrow="es_a", cents=100))\n'
            '    release_esc("es_a", 100)\n'
            '    accept_ms(ms("ms_b", escrow="es_b", cents=40))\n'
            '    release_esc("es_b", 40)\n'
            '    assert seller_cents("s_a") == 100 and seller_cents("s_b") == 40\n'
        ),
        obs3="accept and release both credit seller",
        obs4="accept records; release PK credits",
        obs5="seller once; accept no extra; second escrow adds",
        fail_obs="FAILED test_accept_not_release_double - seller 10000 or 15000 or rows 3\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not accepted_today(ev["milestone_id"]):\n        credit_seller(ev["milestone_id"], ev["cents"])',
        obs7="release still credits; new milestone same day dropped.",
        still_fail_obs="FAILED test_accept_not_release_double - release still extra-credits\n1 failed, 1 passed",
        rewrite_src=(
            "def accept_ms(ev):\n"
            "    if not claim_ms(ev['milestone_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_accepted(ev["milestone_id"], escrow=ev["escrow"])\n'
            '    return {"ok": True, "accepted": True}\n'
        ),
        rewrite_src_obs="claim milestone_id records; does not pay",
        rewrite_hook=(
            "def release_esc(escrow_id, cents):\n"
            "    if not accepted_for(escrow_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    rid = rel_id(escrow_id)\n"
            "    if not claim_esc_rel(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_seller(seller_of(escrow_id), cents, release=rid)\n"
            '    return {"ok": True}\n'
        ),
        obs9="release claims release_id after accept.",
        rewrite_hook_obs="PK release_id",
        ddl=_ddl("till_esc_ms", "release_id", "  milestone_id text UNIQUE,\n  escrow_id text NOT NULL"),
        ddl_obs="PK release_id",
        test2_body=(
            "def test_second_escrow():\n"
            '    accept_ms(ms("ms_a", escrow="es_a", cents=100))\n'
            '    release_esc("es_a", 100)\n'
            '    accept_ms(ms("ms_b", escrow="es_b", cents=40))\n'
            '    release_esc("es_b", 40)\n'
            '    assert seller_cents("s_a") == 100 and seller_cents("s_b") == 40\n'
        ),
        psql_rows="rel_1\nrel_a\nrel_b",
        residual="partial milestone percent",
        grep_pat="accepted",
        grep_obs="src/esc_ms.py: accept then release; no percent split",
        goal="till-esc accept and release both credited seller. Accept records; release PK. Gate: tests/test_esc_ms.py.",
        plan="Skip credit if this milestone already accepted today.",
        outcome="Accept+release double-credited. Milestone-day skip left release unguarded. Plan change: record then PK release. Tests 2/2 + second escrow + suite 8/8.",
    ),
    _fail(
        slug="escrow-disp-after-rel",
        surfaces="escrow dispute vs already released funds",
        avoided="r132 accept vs release; r126 cb hold. This is dispute after release cannot reclaim",
        this_is="dispute after release records only; clawback is separate",
        seed="release then dispute same escrow",
        first_apply="escrow disputed today",
        plan_change="dispute records; released funds stay; clawback separate",
        step_note="Dispute-day 6–7; PK 8–11; second 12–13; clawback xfail 15–17.",
        next_note="Unused: clawback after release. Avoid escrow-disputed-today skip.",
        **_paths("esc_disp", fail=True),
        table="till_esc_disp",
        pk="dispute_id",
        rg="escrow.dispute|after_release|clawback|reclaim",
        rg_obs=_rg_obs("esc_disp", "disp_esc", "rel_then", "test_disp_not_reclaim"),
        test_name="disp-not-reclaim test",
        surface_read="escrow dispute plus already released",
        skip_pred="this escrow already disputed today",
        verb="hold",
        skip_label="escrow-disputed-today skip",
        src_body=_naive(
            "disp_esc",
            'debit_seller(ev["escrow_id"], ev["cents"])',
            "counted every escrow dispute",
        )[0],
        hook_body=(
            "def rel_then(escrow_id, cents):\n"
            "    credit_seller(seller_of(escrow_id), cents)\n"
        ),
        test_body=(
            "def test_disp_not_reclaim():\n"
            '    rel_then("es_1", 5000)\n'
            '    disp_esc(ed("dp_1", escrow="es_1", cents=5000))\n'
            '    disp_esc(ed("dp_1", escrow="es_1", cents=5000))\n'
            '    assert seller_cents("s_1") == 5000 and disputed("dp_1") and disp_rows("dp_1") == 1\n'
            "\n"
            "def test_second_escrow():\n"
            '    rel_then("es_a", 100)\n'
            '    rel_then("es_b", 40)\n'
            '    assert seller_cents("s_a") == 100 and seller_cents("s_b") == 40\n'
        ),
        test_body_short="same — dispute records; released stays",
        obs3="dispute reclaims released funds",
        obs4="dispute records; seller stays paid",
        obs5="seller 5000; dispute once; second escrow independent",
        fail_obs="FAILED test_disp_not_reclaim - seller 0 == 5000 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "disp_esc",
            'debit_seller(ev["escrow_id"], ev["cents"])',
            "counted every escrow dispute",
        )[1],
        skip_new='    if not disputed_today(ev["escrow_id"]):\n        debit_seller(ev["escrow_id"], ev["cents"])',
        obs7="second escrow ok; hides no-reclaim.",
        still_fail_obs="FAILED if dispute reclaimed seller (should stay 5000)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def disp_esc(ev):\n"
            "    if not claim_ed(ev['dispute_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    flag_dispute(ev["escrow_id"], ev["dispute_id"])\n'
            '    return {"ok": True, "disputed": True}\n'
        ),
        rewrite_src_obs="claim dispute_id records; no debit",
        rewrite_hook=(
            "def rel_then(escrow_id, cents):\n"
            "    rid = rel_id(escrow_id)\n"
            "    if not claim_esc_rel2(rid):\n"
            "        return existing_rel(rid)\n"
            "    credit_seller(seller_of(escrow_id), cents, release=rid)\n"
            "    return rid\n"
        ),
        rewrite_hook_obs="release PK stays after dispute",
        ddl=_ddl("till_esc_disp", "dispute_id", "  escrow_id text NOT NULL"),
        ddl_obs="PK dispute_id",
        test2_body=(
            "def test_second_escrow():\n"
            '    rel_then("es_a", 100)\n'
            '    rel_then("es_b", 40)\n'
            '    assert seller_cents("s_a") == 100 and seller_cents("s_b") == 40\n'
        ),
        xfail_label="clawback after release",
        xfail_body=(
            "def test_clawback_after_rel():\n"
            '    rel_then("es_p", 5000)\n'
            '    disp_esc(ed("dp_p", escrow="es_p", cents=5000))\n'
            '    clawback_esc("es_p", 5000)\n'
            '    assert seller_cents("s_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_clawback_after_rel - no clawback path; seller stays 5000\n1 failed",
        xfail_old="def test_clawback_after_rel():",
        xfail_new='@pytest.mark.xfail(reason="handoff: clawback after release is a separate dest reverse", strict=True)\ndef test_clawback_after_rel():',
        xfail_patch_obs="xfailed clawback after release",
        goal="till-esc-disp dispute reclaimed released funds. Dispute records only. Gate: tests/test_esc_disp.py.",
        plan="Skip hold if this escrow already disputed today.",
        outcome="Dispute reclaimed seller. Dispute-day skip hid record-only. Plan change: flag dispute. Primary+second pass. Partial: clawback xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r133 tip adjust vs capture / tip after batch close
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "tip_adj",
    'capture_pay(ev["charge_id"], ev["cents"])',
    "counted every tip adjust",
)
pair(
    _ok(
        slug="tip-adjust-vs-capture",
        surfaces="tip adjust increment vs original capture",
        avoided="r84 incremental auth; r23 increment_id. This is tip CAS on captured amount",
        this_is="capture PK charge_id; tip is increment CAS not recapture",
        seed="capture + tip adjust same charge_id",
        first_apply="tipped today",
        plan_change="capture PK; tip CAS amount += tip_cents",
        step_note="Charge-day 6–7; PK 8–11; second charge 12–13.",
        **_paths("tip_adj"),
        table="till_tip_adj",
        pk="charge_id",
        rg="tip_adjust|capture_amount|tip_cents|cas_amount",
        rg_obs=_rg_obs("tip_adj", "tip_adj", "cap_pay", "test_tip_not_recapture"),
        test_name="tip-not-recapture test",
        surface_read="tip adjust plus original capture",
        skip_pred="this charge already tipped today",
        verb="capture",
        skip_label="tipped-today skip",
        src_body=_src,
        hook_body=(
            "def cap_pay(charge_id, cents):\n"
            "    capture_pay(charge_id, cents)\n"
        ),
        test_body=(
            "def test_tip_not_recapture():\n"
            '    cap_pay("ch_1", 5000)\n'
            '    tip_adj(tp("ch_1", cents=5000, tip=700))\n'
            '    tip_adj(tp("ch_1", cents=5000, tip=700))\n'
            '    assert captured_cents("ch_1") == 5700 and tip_cents("ch_1") == 700 and tip_rows("ch_1") == 1\n'
            "\n"
            "def test_second_charge():\n"
            '    cap_pay("ch_a", 100)\n'
            '    tip_adj(tp("ch_a", cents=100, tip=15))\n'
            '    cap_pay("ch_b", 40)\n'
            '    tip_adj(tp("ch_b", cents=40, tip=5))\n'
            '    assert captured_cents("ch_a") == 115 and captured_cents("ch_b") == 45\n'
        ),
        obs3="tip recaptures full 5000",
        obs4="capture PK; tip increments",
        obs5="5700 = 5000+700; tip once; second charge adds",
        fail_obs="FAILED test_tip_not_recapture - captured 10000 or 5700*2 or 5000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not tipped_today(ev["charge_id"]):\n        capture_pay(ev["charge_id"], ev["cents"])',
        obs7="tip still recaptures; new charge same day dropped.",
        still_fail_obs="FAILED test_tip_not_recapture - tip recaptured base\n1 failed, 1 passed",
        rewrite_src=(
            "def tip_adj(ev):\n"
            '    if batch_closed(ev["charge_id"]):\n'
            '        return {"ok": True, "blocked": True}\n'
            '    if not cas_tip(ev["charge_id"], ev["tip"]):\n'
            '        return {"ok": True, "dup": True}\n'
            '    return {"ok": True, "tipped": ev["tip"]}\n'
        ),
        rewrite_src_obs="CAS tip increment; no recapture",
        rewrite_hook=(
            "def cap_pay(charge_id, cents):\n"
            "    if not claim_cap(charge_id):\n"
            "        return existing_ch(charge_id)\n"
            "    capture_pay(charge_id, cents)\n"
            "    return charge_id\n"
            "\n"
            "def cas_tip(charge_id, tip):\n"
            '    cur = db.execute("UPDATE till_tip_adj SET cents = cents + %s, tip = %s WHERE charge_id = %s AND tip = 0", [tip, tip, charge_id])\n'
            "    return cur.rowcount == 1\n"
        ),
        obs9="capture claims; tip CAS once.",
        rewrite_hook_obs="PK charge_id; tip CAS",
        ddl=_ddl("till_tip_adj", "charge_id", "  tip int NOT NULL DEFAULT 0"),
        ddl_obs="PK charge_id",
        test2_body=(
            "def test_second_charge():\n"
            '    cap_pay("ch_a", 100)\n'
            '    tip_adj(tp("ch_a", cents=100, tip=15))\n'
            '    cap_pay("ch_b", 40)\n'
            '    tip_adj(tp("ch_b", cents=40, tip=5))\n'
            '    assert captured_cents("ch_a") == 115 and captured_cents("ch_b") == 45\n'
        ),
        psql_rows="ch_1\nch_a\nch_b",
        residual="tip then void",
        grep_pat="cas_tip",
        grep_obs="src/tip_adj.py: CAS tip=0; no void reverse",
        goal="till-tip tip recaptured base. Capture PK; tip CAS increment. Gate: tests/test_tip_adj.py.",
        plan="Skip capture if this charge already tipped today.",
        outcome="Tip recaptured base. Charge-day skip left recapture. Plan change: PK + CAS tip. Tests 2/2 + second charge + suite 8/8.",
    ),
    _fail(
        slug="tip-after-batch-close",
        surfaces="tip adjust vs already-closed merchant batch",
        avoided="r133 tip CAS; r124 settle close. This is batch close blocks tip",
        this_is="close PK batch_id; tip refused after close",
        seed="close batch then tip",
        first_apply="batch closed today",
        plan_change="close PK; tip blocked; adjustment batch is handoff",
        step_note="Batch-day 6–7; PK 8–11; second 12–13; adj-batch xfail 15–17.",
        next_note="Unused: tip after close should open adjustment batch. Avoid batch-closed-today skip.",
        **_paths("tip_batch", fail=True),
        table="till_tip_batch",
        pk="batch_id",
        rg="batch.close|tip_after_close|adjustment_batch",
        rg_obs=_rg_obs("tip_batch", "close_batch", "tip_late", "test_close_not_tip"),
        test_name="close-not-tip test",
        surface_read="merchant batch close plus late tip",
        skip_pred="this batch already closed today",
        verb="close",
        skip_label="batch-closed-today skip",
        src_body=_naive(
            "close_batch",
            'capture_pay(ev["batch_id"], ev.get("cents", 0))',
            "counted every batch close",
        )[0],
        hook_body=(
            "def tip_late(charge_id, tip):\n"
            "    capture_pay(charge_id, tip)\n"
        ),
        test_body=(
            "def test_close_not_tip():\n"
            '    cap_pay("ch_1", 5000)\n'
            '    close_batch(cbh("b_1", charges=["ch_1"]))\n'
            '    close_batch(cbh("b_1", charges=["ch_1"]))\n'
            '    tip_late("ch_1", 700)\n'
            '    assert captured_cents("ch_1") == 5000 and closed("b_1") and batch_rows("b_1") == 1\n'
            "\n"
            "def test_second_batch():\n"
            '    cap_pay("ch_a", 100)\n'
            '    close_batch(cbh("b_a", charges=["ch_a"]))\n'
            '    cap_pay("ch_b", 40)\n'
            '    close_batch(cbh("b_b", charges=["ch_b"]))\n'
            '    assert closed("b_a") and closed("b_b")\n'
        ),
        test_body_short="same — close PK; tip blocked",
        obs3="close and late tip both recapture",
        obs4="close PK; tip blocked",
        obs5="captured stays 5000; second batch closes",
        fail_obs="FAILED test_close_not_tip - captured 5700 == 5000 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "close_batch",
            'capture_pay(ev["batch_id"], ev.get("cents", 0))',
            "counted every batch close",
        )[1],
        skip_new='    if not closed_today(ev["batch_id"]):\n        capture_pay(ev["batch_id"], ev.get("cents", 0))',
        obs7="second batch ok; hides tip block.",
        still_fail_obs="FAILED if late tip added 700 after close\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def close_batch(ev):\n"
            "    if not claim_batch(ev['batch_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_closed_batch(ev["batch_id"], ev["charges"])\n'
            '    return {"ok": True, "closed": True}\n'
        ),
        rewrite_src_obs="claim batch_id; close does not recapture",
        rewrite_hook=(
            "def tip_late(charge_id, tip):\n"
            "    if batch_closed_for(charge_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    return cas_tip(charge_id, tip)\n"
        ),
        rewrite_hook_obs="tip blocked after close",
        ddl=_ddl("till_tip_batch", "batch_id", "  closed bool NOT NULL DEFAULT true"),
        ddl_obs="PK batch_id",
        test2_body=(
            "def test_second_batch():\n"
            '    cap_pay("ch_a", 100)\n'
            '    close_batch(cbh("b_a", charges=["ch_a"]))\n'
            '    cap_pay("ch_b", 40)\n'
            '    close_batch(cbh("b_b", charges=["ch_b"]))\n'
            '    assert closed("b_a") and closed("b_b")\n'
        ),
        xfail_label="tip after close should open adjustment batch",
        xfail_body=(
            "def test_tip_opens_adj_batch():\n"
            '    cap_pay("ch_p", 5000)\n'
            '    close_batch(cbh("b_p", charges=["ch_p"]))\n'
            '    tip_late("ch_p", 700)\n'
            '    assert captured_cents("ch_p") == 5700 and adj_batch("ch_p") == "b_p_adj"\n'
        ),
        xfail_fail_obs="FAILED test_tip_opens_adj_batch - tip blocked; no adj batch\n1 failed",
        xfail_old="def test_tip_opens_adj_batch():",
        xfail_new='@pytest.mark.xfail(reason="handoff: tip after close must open adjustment batch", strict=True)\ndef test_tip_opens_adj_batch():',
        xfail_patch_obs="xfailed tip adj batch",
        goal="till-tip-batch late tip recaptured after close. Close PK blocks tip. Gate: tests/test_tip_batch.py.",
        plan="Skip close if this batch already closed today.",
        outcome="Late tip recaptured. Batch-day skip hid block. Plan change: close PK; tip refuses. Primary+second pass. Partial: adj-batch xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r134 wallet topup vs spend / reverse after spend
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "load_wal",
    'credit_wal(ev["topup_id"], ev["cents"])',
    "counted every wallet topup",
)
pair(
    _ok(
        slug="wallet-topup-vs-spend",
        surfaces="prepaid wallet topup vs spend debit",
        avoided="r43 cash spend_id; r70 gift card LOAD. This is topup_id credit vs spend_id debit",
        this_is="load PK topup_id credits; spend PK spend_id debits if balance",
        seed="topup + spend same wallet",
        first_apply="wallet loaded today",
        plan_change="load PK credits; spend PK debits against balance",
        step_note="Wallet-day 6–7; PK 8–11; second wallet 12–13.",
        **_paths("wal_load"),
        table="till_wal_load",
        pk="topup_id",
        rg="wallet.topup|wallet.spend|balance_cents|prepaid",
        rg_obs=_rg_obs("wal_load", "load_wal", "spend_wal", "test_load_not_spend_credit"),
        test_name="load-not-spend-credit test",
        surface_read="wallet topup plus spend",
        skip_pred="this wallet already loaded today",
        verb="credit",
        skip_label="wallet-loaded-today skip",
        src_body=_src,
        hook_body=(
            "def spend_wal(wallet_id, cents):\n"
            "    credit_wal(wallet_id, cents)\n"
        ),
        test_body=(
            "def test_load_not_spend_credit():\n"
            '    load_wal(ld("tu_1", wallet="w_1", cents=5000))\n'
            '    load_wal(ld("tu_1", wallet="w_1", cents=5000))\n'
            '    spend_wal("w_1", 1200)\n'
            '    assert bal_cents("w_1") == 3800 and spend_cents("sp_1") == 1200 and wal_rows("tu_1") == 1\n'
            "\n"
            "def test_second_wallet():\n"
            '    load_wal(ld("tu_a", wallet="w_a", cents=100))\n'
            '    spend_wal("w_a", 20)\n'
            '    load_wal(ld("tu_b", wallet="w_b", cents=40))\n'
            '    spend_wal("w_b", 5)\n'
            '    assert bal_cents("w_a") == 80 and bal_cents("w_b") == 35\n'
        ),
        obs3="spend also credits wallet",
        obs4="load credits; spend debits",
        obs5="bal 3800; load once; second wallet adds",
        fail_obs="FAILED test_load_not_spend_credit - bal 11200 or 5000 not 3800\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not loaded_today(ev["wallet"]):\n        credit_wal(ev["topup_id"], ev["cents"])',
        obs7="spend still credits; new wallet same day dropped.",
        still_fail_obs="FAILED test_load_not_spend_credit - spend credited not debited\n1 failed, 1 passed",
        rewrite_src=(
            "def load_wal(ev):\n"
            "    if not claim_tu(ev['topup_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_wal(ev["wallet"], ev["cents"], topup=ev["topup_id"])\n'
            '    return {"ok": True, "loaded": True}\n'
        ),
        rewrite_src_obs="claim topup_id credits wallet",
        rewrite_hook=(
            "def spend_wal(wallet_id, cents):\n"
            "    sid = spend_id(wallet_id, cents)\n"
            "    if not claim_sp(sid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if bal_of(wallet_id) < cents:\n"
            '        return {"ok": True, "nsf": True}\n'
            "    debit_wal(wallet_id, cents, spend=sid)\n"
            '    return {"ok": True, "spent": True}\n'
        ),
        obs9="spend claims spend_id and debits.",
        rewrite_hook_obs="PK spend_id debit",
        ddl=_ddl("till_wal_load", "topup_id", "  wallet_id text NOT NULL,\n  spend_id text UNIQUE"),
        ddl_obs="PK topup_id",
        test2_body=(
            "def test_second_wallet():\n"
            '    load_wal(ld("tu_a", wallet="w_a", cents=100))\n'
            '    spend_wal("w_a", 20)\n'
            '    load_wal(ld("tu_b", wallet="w_b", cents=40))\n'
            '    spend_wal("w_b", 5)\n'
            '    assert bal_cents("w_a") == 80 and bal_cents("w_b") == 35\n'
        ),
        psql_rows="tu_1\ntu_a\ntu_b",
        residual="spend exceeds load NSF",
        grep_pat="nsf",
        grep_obs="src/wal_load.py: NSF refuse; no overdraft",
        goal="till-wal load and spend both credited. Load PK credit; spend PK debit. Gate: tests/test_wal_load.py.",
        plan="Skip credit if this wallet already loaded today.",
        outcome="Load+spend both credited. Wallet-day skip left spend as credit. Plan change: load PK + spend debit. Tests 2/2 + second wallet + suite 8/8.",
    ),
    _fail(
        slug="topup-rev-after-spend",
        surfaces="wallet topup reverse vs already spent balance",
        avoided="r134 load vs spend; r70 gift LOAD. This is reverse only unspent",
        this_is="reverse PK unspents only; spent portion stays",
        seed="reverse topup after spend",
        first_apply="topup reversed today",
        plan_change="reverse only unspent; spent stays debited",
        step_note="Reverse-day 6–7; PK 8–11; second 12–13; full reverse xfail 15–17.",
        next_note="Unused: reverse after spend should fail or partial. Avoid topup-reversed-today skip.",
        **_paths("wal_rev", fail=True),
        table="till_wal_rev",
        pk="rev_id",
        rg="topup.reverse|unspent_only|spent_stays",
        rg_obs=_rg_obs("wal_rev", "rev_tu", "spend_then", "test_rev_not_full_after_spend"),
        test_name="rev-not-full-after-spend test",
        surface_read="topup reverse plus already spent",
        skip_pred="this topup already reversed today",
        verb="reverse",
        skip_label="topup-reversed-today skip",
        src_body=_naive(
            "rev_tu",
            'debit_wal(ev["wallet_id"], ev["cents"])',
            "counted every topup reverse",
        )[0],
        hook_body=(
            "def spend_then(wallet_id, cents):\n"
            "    debit_wal(wallet_id, cents)\n"
        ),
        test_body=(
            "def test_rev_not_full_after_spend():\n"
            '    credit_wal("w_1", 5000, topup="tu_1")\n'
            '    spend_then("w_1", 1200)\n'
            '    rev_tu(rt("rv_1", wallet="w_1", cents=5000, topup="tu_1"))\n'
            '    rev_tu(rt("rv_1", wallet="w_1", cents=5000, topup="tu_1"))\n'
            '    assert bal_cents("w_1") == 0 and reversed_cents("rv_1") == 3800 and rev_rows("rv_1") == 1\n'
            "\n"
            "def test_second_wallet():\n"
            '    credit_wal("w_a", 100, topup="tu_a")\n'
            '    rev_tu(rt("rv_a", wallet="w_a", cents=100, topup="tu_a"))\n'
            '    credit_wal("w_b", 40, topup="tu_b")\n'
            '    assert bal_cents("w_a") == 0 and bal_cents("w_b") == 40\n'
        ),
        test_body_short="same — reverse unspent 3800 only",
        obs3="reverse full 5000 after spend 1200",
        obs4="reverse unspent only",
        obs5="bal 0; reversed 3800; second wallet independent",
        fail_obs="FAILED test_rev_not_full_after_spend - bal -1200 or reversed 5000\n1 failed, 1 passed",
        skip_old=_naive(
            "rev_tu",
            'debit_wal(ev["wallet_id"], ev["cents"])',
            "counted every topup reverse",
        )[1],
        skip_new='    if not reversed_today(ev["topup"]):\n        debit_wal(ev["wallet_id"], ev["cents"])',
        obs7="second wallet ok; hides unspent-only.",
        still_fail_obs="FAILED if reverse took full 5000 (bal negative)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def rev_tu(ev):\n"
            "    if not claim_rev_tu(ev['rev_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    unspent = min(ev["cents"], bal_of(ev["wallet_id"]))\n'
            "    debit_wal(ev['wallet_id'], unspent, rev=ev['rev_id'])\n"
            '    return {"ok": True, "reversed": unspent}\n'
        ),
        rewrite_src_obs="claim rev_id reverses unspent only",
        rewrite_hook=(
            "def spend_then(wallet_id, cents):\n"
            "    if not claim_sp2(spend_id(wallet_id, cents)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_wal(wallet_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="spend PK before reverse",
        ddl=_ddl("till_wal_rev", "rev_id", "  topup_id text NOT NULL,\n  reversed int NOT NULL"),
        ddl_obs="PK rev_id",
        test2_body=(
            "def test_second_wallet():\n"
            '    credit_wal("w_a", 100, topup="tu_a")\n'
            '    rev_tu(rt("rv_a", wallet="w_a", cents=100, topup="tu_a"))\n'
            '    credit_wal("w_b", 40, topup="tu_b")\n'
            '    assert bal_cents("w_a") == 0 and bal_cents("w_b") == 40\n'
        ),
        xfail_label="full reverse after spend should refuse",
        xfail_body=(
            "def test_full_rev_after_spend():\n"
            '    credit_wal("w_p", 5000, topup="tu_p")\n'
            '    spend_then("w_p", 1200)\n'
            '    out = rev_tu(rt("rv_p", wallet="w_p", cents=5000, topup="tu_p", full=True))\n'
            '    assert out["ok"] is False and bal_cents("w_p") == 3800\n'
        ),
        xfail_fail_obs="FAILED test_full_rev_after_spend - partial reverse succeeded; no full-refuse\n1 failed",
        xfail_old="def test_full_rev_after_spend():",
        xfail_new='@pytest.mark.xfail(reason="handoff: full reverse after spend must refuse, not silently partial", strict=True)\ndef test_full_rev_after_spend():',
        xfail_patch_obs="xfailed full reverse after spend",
        goal="till-wal-rev reverse took full 5000 after spend. Reverse unspent only. Gate: tests/test_wal_rev.py.",
        plan="Skip reverse if this topup already reversed today.",
        outcome="Reverse over-debited. Reverse-day skip hid unspent-only. Plan change: reverse min(bal, amt). Primary+second pass. Partial: full-refuse xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r135 ACH settle vs return / return after payout
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "settle_ach",
    'credit_merch(ev["trace"], ev["cents"])',
    "counted every ACH settle",
)
pair(
    _ok(
        slug="ach-settle-vs-return",
        surfaces="ACH settlement credit vs NACHA return",
        avoided="r05 ACH (trace, return_code); r101 inbound ACH vs txn. This is settle PK then return reverses",
        this_is="settle PK trace; return PK (trace, return_code) reverses",
        seed="settle trace + R01 return",
        first_apply="ACH settled today",
        plan_change="settle PK credits; return reverses if settled",
        step_note="Trace-day 6–7; PK 8–11; second trace 12–13.",
        **_paths("ach_set"),
        table="till_ach_set",
        pk="trace",
        rg="ach.settle|nacha.return|return_code|trace",
        rg_obs=_rg_obs("ach_set", "settle_ach", "return_ach", "test_settle_not_return_double"),
        test_name="settle-not-return-double test",
        surface_read="ACH settle plus NACHA return",
        skip_pred="this ACH already settled today",
        verb="credit",
        skip_label="ach-settled-today skip",
        src_body=_src,
        hook_body=(
            "def return_ach(trace, code, cents):\n"
            "    credit_merch(trace, cents)\n"
        ),
        test_body=(
            "def test_settle_not_return_double():\n"
            '    settle_ach(ach("tr_1", cents=5000))\n'
            '    settle_ach(ach("tr_1", cents=5000))\n'
            '    return_ach("tr_1", "R01", 5000)\n'
            '    assert merch_cents("m_1") == 0 and returned("tr_1", "R01") and ach_rows("tr_1") == 1\n'
            "\n"
            "def test_second_trace():\n"
            '    settle_ach(ach("tr_a", cents=100))\n'
            '    settle_ach(ach("tr_b", cents=40))\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        obs3="return also credits merchant",
        obs4="settle credits; return reverses",
        obs5="merch 0 after R01; settle once; second trace adds",
        fail_obs="FAILED test_settle_not_return_double - merch 10000 or 5000 not 0\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not settled_today(ev["trace"]):\n        credit_merch(ev["trace"], ev["cents"])',
        obs7="return still credits; new trace same day dropped.",
        still_fail_obs="FAILED test_settle_not_return_double - return credited not reversed\n1 failed, 1 passed",
        rewrite_src=(
            "def settle_ach(ev):\n"
            "    if not claim_tr(ev['trace']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_merch(ev.get("merchant", merch_of(ev["trace"])), ev["cents"], trace=ev["trace"])\n'
            '    return {"ok": True, "settled": True}\n'
        ),
        rewrite_src_obs="claim trace credits merchant",
        rewrite_hook=(
            "def return_ach(trace, code, cents):\n"
            "    rid = ret_id(trace, code)\n"
            "    if not claim_ret(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if not settled(trace):\n"
            '        return {"ok": True, "not_settled": True}\n'
            "    debit_merch(merch_of(trace), cents, ret=rid)\n"
            '    return {"ok": True, "returned": True}\n'
        ),
        obs9="return claims (trace, code) and reverses.",
        rewrite_hook_obs="PK return reverses",
        ddl=_ddl("till_ach_set", "trace", "  return_code text,\n  UNIQUE (trace, return_code)"),
        ddl_obs="PK trace",
        test2_body=(
            "def test_second_trace():\n"
            '    settle_ach(ach("tr_a", cents=100))\n'
            '    settle_ach(ach("tr_b", cents=40))\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        psql_rows="tr_1\ntr_a\ntr_b",
        residual="late return R10",
        grep_pat="R01",
        grep_obs="src/ach_set.py: return reverses; no R10 late window",
        goal="till-ach settle and return both credited. Settle PK; return reverses. Gate: tests/test_ach_set.py.",
        plan="Skip credit if this ACH already settled today.",
        outcome="Settle+return both credited. Trace-day skip left return as credit. Plan change: settle PK + return reverse. Tests 2/2 + second trace + suite 8/8.",
    ),
    _fail(
        slug="ach-return-after-payout",
        surfaces="ACH return vs merchant already paid out",
        avoided="r135 settle vs return; r03 payout.failed. This is return creates receivable after payout",
        this_is="return after payout does not silently no-op; opens receivable",
        seed="payout then NACHA return",
        first_apply="merchant paid today",
        plan_change="return after payout opens receivable; does not drop",
        step_note="Payout-day 6–7; PK 8–11; second 12–13; clawback payout xfail 15–17.",
        next_note="Unused: return after payout should clawback payout. Avoid merchant-paid-today skip.",
        **_paths("ach_ret", fail=True),
        table="till_ach_ret",
        pk="ret_id",
        rg="return_after_payout|receivable|clawback_payout",
        rg_obs=_rg_obs("ach_ret", "ret_after", "payout_then", "test_return_opens_recv"),
        test_name="return-opens-recv test",
        surface_read="ACH return plus already paid out",
        skip_pred="this merchant already paid today",
        verb="return",
        skip_label="merchant-paid-today skip",
        src_body=_naive(
            "ret_after",
            'debit_merch(ev["merchant"], ev["cents"])',
            "counted every ACH return",
        )[0],
        hook_body=(
            "def payout_then(merchant, cents):\n"
            "    debit_merch(merchant, cents)\n"
        ),
        test_body=(
            "def test_return_opens_recv():\n"
            '    settle_and_payout("tr_1", "m_1", 5000)\n'
            '    ret_after(ra("rt_1", trace="tr_1", merchant="m_1", cents=5000, code="R01"))\n'
            '    ret_after(ra("rt_1", trace="tr_1", merchant="m_1", cents=5000, code="R01"))\n'
            '    assert recv_cents("m_1") == 5000 and paid_cents("m_1") == 5000 and ret_rows("rt_1") == 1\n'
            "\n"
            "def test_second_merchant():\n"
            '    settle_and_payout("tr_a", "m_a", 100)\n'
            '    settle_and_payout("tr_b", "m_b", 40)\n'
            '    assert paid_cents("m_a") == 100 and paid_cents("m_b") == 40\n'
        ),
        test_body_short="same — return after payout opens receivable",
        obs3="return silently no-ops or double-debits paid merchant",
        obs4="return PK opens receivable; paid stays",
        obs5="recv 5000; paid 5000; second merchant independent",
        fail_obs="FAILED test_return_opens_recv - recv 0 or paid 0 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "ret_after",
            'debit_merch(ev["merchant"], ev["cents"])',
            "counted every ACH return",
        )[1],
        skip_new='    if not paid_today(ev["merchant"]):\n        debit_merch(ev["merchant"], ev["cents"])',
        obs7="second merchant ok; hides receivable.",
        still_fail_obs="FAILED if return no-op'd (recv 0) or reversed payout\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def ret_after(ev):\n"
            "    if not claim_ret2(ev['ret_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if already_paid(ev['merchant'], ev['trace']):\n"
            '        open_recv(ev["merchant"], ev["cents"], ret=ev["ret_id"])\n'
            '        return {"ok": True, "receivable": True}\n'
            '    debit_merch(ev["merchant"], ev["cents"])\n'
            '    return {"ok": True, "reversed": True}\n'
        ),
        rewrite_src_obs="claim ret_id; paid opens receivable",
        rewrite_hook=(
            "def payout_then(merchant, cents):\n"
            "    pid = po_id(merchant, cents)\n"
            "    if not claim_po(pid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    debit_avail(merchant, cents, payout=pid)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="payout PK from available",
        ddl=_ddl("till_ach_ret", "ret_id", "  trace text NOT NULL,\n  recv_cents int NOT NULL DEFAULT 0"),
        ddl_obs="PK ret_id",
        test2_body=(
            "def test_second_merchant():\n"
            '    settle_and_payout("tr_a", "m_a", 100)\n'
            '    settle_and_payout("tr_b", "m_b", 40)\n'
            '    assert paid_cents("m_a") == 100 and paid_cents("m_b") == 40\n'
        ),
        xfail_label="return after payout should clawback payout",
        xfail_body=(
            "def test_clawback_payout():\n"
            '    settle_and_payout("tr_p", "m_p", 5000)\n'
            '    ret_after(ra("rt_p", trace="tr_p", merchant="m_p", cents=5000, code="R01"))\n'
            '    assert paid_cents("m_p") == 0 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_clawback_payout - paid stays 5000; recv opened instead\n1 failed",
        xfail_old="def test_clawback_payout():",
        xfail_new='@pytest.mark.xfail(reason="handoff: return after payout clawback vs receivable is a policy fork", strict=True)\ndef test_clawback_payout():',
        xfail_patch_obs="xfailed clawback payout",
        goal="till-ach-ret return dropped after payout. Return opens receivable. Gate: tests/test_ach_ret.py.",
        plan="Skip return if this merchant already paid today.",
        outcome="Return no-op'd after payout. Paid-day skip hid receivable. Plan change: open recv. Primary+second pass. Partial: clawback xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r136 netting window vs gross / late leg after net
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "close_net",
    'post_ledger(ev["leg_id"], ev["cents"])',
    "counted every net close",
)
pair(
    _ok(
        slug="netting-window-vs-gross",
        surfaces="multilateral net close vs gross legs",
        avoided="r124 settle window; r80 outbox. This is staged legs vs net-only close",
        this_is="legs record; close PK window_id posts net only",
        seed="stage legs + close net window",
        first_apply="net closed today",
        plan_change="legs staged; close posts net not each leg",
        step_note="Window-day 6–7; PK 8–11; second window 12–13.",
        **_paths("net_win"),
        table="till_net_close",
        pk="window_id",
        rg="netting.window|gross_leg|net_cents|stage_leg",
        rg_obs=_rg_obs("net_win", "close_net", "stage_leg", "test_close_not_gross_double"),
        test_name="close-not-gross-double test",
        surface_read="net close plus gross legs",
        skip_pred="this net window already closed today",
        verb="post",
        skip_label="net-closed-today skip",
        src_body=_src,
        hook_body=(
            "def stage_leg(window_id, leg_id, cents):\n"
            "    post_ledger(leg_id, cents)\n"
        ),
        test_body=(
            "def test_close_not_gross_double():\n"
            '    stage_leg("w_1", "l_in", 5000)\n'
            '    stage_leg("w_1", "l_out", -4700)\n'
            '    close_net(cn("w_1", cents=300))\n'
            '    close_net(cn("w_1", cents=300))\n'
            '    assert posted_cents("w_1") == 300 and net_rows("w_1") == 1 and not posted("l_in")\n'
            "\n"
            "def test_second_window():\n"
            '    stage_leg("w_a", "la_in", 100)\n'
            '    close_net(cn("w_a", cents=100))\n'
            '    stage_leg("w_b", "lb_in", 40)\n'
            '    close_net(cn("w_b", cents=40))\n'
            '    assert posted_cents("w_a") == 100 and posted_cents("w_b") == 40\n'
        ),
        obs3="close posts each leg plus net",
        obs4="legs staged; close posts net only",
        obs5="net 300 once; legs not posted; second window adds",
        fail_obs="FAILED test_close_not_gross_double - posted 5600 or 300*2 not 300\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not netted_today(ev["window_id"]):\n        post_ledger(ev["leg_id"], ev["cents"])',
        obs7="close still posts legs; new window same day dropped.",
        still_fail_obs="FAILED test_close_not_gross_double - close posted gross legs\n1 failed, 1 passed",
        rewrite_src=(
            "def close_net(ev):\n"
            "    if not claim_net(ev['window_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    net = staged_net(ev['window_id'])\n"
            "    post_ledger(ev['window_id'], net, reason='net_close')\n"
            '    return {"ok": True, "net": net}\n'
        ),
        rewrite_src_obs="claim window_id posts staged net only",
        rewrite_hook=(
            "def stage_leg(window_id, leg_id, cents):\n"
            "    if not claim_leg(leg_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    stage(window_id, leg_id, cents)\n"
            '    return {"ok": True, "staged": True}\n'
        ),
        obs9="legs claim leg_id into stage, not ledger.",
        rewrite_hook_obs="legs staged",
        ddl=_ddl("till_net_close", "window_id", "  net_cents int NOT NULL"),
        ddl_obs="PK window_id",
        test2_body=(
            "def test_second_window():\n"
            '    stage_leg("w_a", "la_in", 100)\n'
            '    close_net(cn("w_a", cents=100))\n'
            '    stage_leg("w_b", "lb_in", 40)\n'
            '    close_net(cn("w_b", cents=40))\n'
            '    assert posted_cents("w_a") == 100 and posted_cents("w_b") == 40\n'
        ),
        psql_rows="w_1\nw_a\nw_b",
        residual="excluded currency",
        grep_pat="staged_net",
        grep_obs="src/net_win.py: net of staged; no ccy filter",
        goal="till-net close posted gross legs. Legs staged; close net only. Gate: tests/test_net_win.py.",
        plan="Skip post if this net window already closed today.",
        outcome="Close posted gross. Window-day skip left leg posts. Plan change: stage then net PK. Tests 2/2 + second window + suite 8/8.",
    ),
    _fail(
        slug="late-leg-after-net",
        surfaces="late inbound leg vs already closed net window",
        avoided="r136 net vs gross; r124 late after cutoff. This is late item next window",
        this_is="late leg after close goes to next window; does not post gross",
        seed="close net then late inbound",
        first_apply="late item today",
        plan_change="late stages into next window; no gross post",
        step_note="Late-day 6–7; PK 8–11; second 12–13; reopen xfail 15–17.",
        next_note="Unused: late item should reopen window. Avoid late-item-today skip.",
        **_paths("net_late", fail=True),
        table="till_net_late",
        pk="leg_id",
        rg="late_leg|next_window|reopen_net|after_close",
        rg_obs=_rg_obs("net_late", "late_leg", "closed_net", "test_late_not_gross"),
        test_name="late-not-gross test",
        surface_read="late inbound plus closed net",
        skip_pred="this late item already booked today",
        verb="post",
        skip_label="late-item-today skip",
        src_body=_naive(
            "late_leg",
            'post_ledger(ev["leg_id"], ev["cents"])',
            "counted every late leg",
        )[0],
        hook_body=(
            "def closed_net(window_id, net):\n"
            "    post_ledger(window_id, net)\n"
        ),
        test_body=(
            "def test_late_not_gross():\n"
            '    closed_net("w_1", 300)\n'
            '    late_leg(ll("l_late", window="w_1", cents=80))\n'
            '    late_leg(ll("l_late", window="w_1", cents=80))\n'
            '    assert posted_cents("w_1") == 300 and next_staged("w_2", "l_late") == 80 and late_rows("l_late") == 1\n'
            "\n"
            "def test_second_leg():\n"
            '    late_leg(ll("l_a", window="w_a", cents=10))\n'
            '    late_leg(ll("l_b", window="w_b", cents=4))\n'
            '    assert next_staged("w_a_next", "l_a") == 10\n'
        ),
        test_body_short="same — late stages next window",
        obs3="late posts gross into closed window",
        obs4="late stages next; closed net stays",
        obs5="w_1 stays 300; l_late in next; second late independent",
        fail_obs="FAILED test_late_not_gross - posted 380 or late posted gross\n1 failed, 1 passed",
        skip_old=_naive(
            "late_leg",
            'post_ledger(ev["leg_id"], ev["cents"])',
            "counted every late leg",
        )[1],
        skip_new='    if not late_today(ev["leg_id"]):\n        post_ledger(ev["leg_id"], ev["cents"])',
        obs7="second late ok; hides next-window stage.",
        still_fail_obs="FAILED if late posted 80 into w_1 (should stage next)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def late_leg(ev):\n"
            "    if not claim_late(ev['leg_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    nxt = next_window(ev['window'])\n"
            "    stage(nxt, ev['leg_id'], ev['cents'])\n"
            '    return {"ok": True, "next": nxt}\n'
        ),
        rewrite_src_obs="claim leg_id stages next window",
        rewrite_hook=(
            "def closed_net(window_id, net):\n"
            "    if not claim_net2(window_id):\n"
            "        return existing_win(window_id)\n"
            "    post_ledger(window_id, net, reason='net_close')\n"
            "    return window_id\n"
        ),
        rewrite_hook_obs="closed net PK stays",
        ddl=_ddl("till_net_late", "leg_id", "  next_window text NOT NULL"),
        ddl_obs="PK leg_id",
        test2_body=(
            "def test_second_leg():\n"
            '    late_leg(ll("l_a", window="w_a", cents=10))\n'
            '    late_leg(ll("l_b", window="w_b", cents=4))\n'
            '    assert next_staged("w_a_next", "l_a") == 10 and next_staged("w_b_next", "l_b") == 4\n'
        ),
        xfail_label="late item should reopen window",
        xfail_body=(
            "def test_late_reopens():\n"
            '    closed_net("w_p", 300)\n'
            '    late_leg(ll("l_p", window="w_p", cents=80))\n'
            '    assert posted_cents("w_p") == 380 and reopened("w_p")\n'
        ),
        xfail_fail_obs="FAILED test_late_reopens - staged next; did not reopen\n1 failed",
        xfail_old="def test_late_reopens():",
        xfail_new='@pytest.mark.xfail(reason="handoff: late item reopen vs next-window is a policy fork", strict=True)\ndef test_late_reopens():',
        xfail_patch_obs="xfailed late reopen",
        goal="till-net-late late posted gross into closed net. Late stages next. Gate: tests/test_net_late.py.",
        plan="Skip post if this late item already booked today.",
        outcome="Late posted gross. Late-day skip hid next-window. Plan change: stage next. Primary+second pass. Partial: reopen xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r137 VAT invoice vs cash / credit note after cash
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "issue_vat",
    'recognize_rev(ev["invoice_id"], ev["cents"])',
    "counted every VAT invoice issue",
)
pair(
    _ok(
        slug="vat-invoice-vs-cash",
        surfaces="VAT invoice issue vs cash receipt apply",
        avoided="r08 invoice finalize; r26 invoice pay CAS. This is AR issue vs cash apply PK",
        this_is="issue PK invoice_id books AR; cash PK receipt_id applies",
        seed="issue invoice + cash apply same invoice",
        first_apply="invoice issued today",
        plan_change="issue books AR; cash applies; neither re-recognizes",
        step_note="Invoice-day 6–7; PK 8–11; second invoice 12–13.",
        **_paths("vat_inv"),
        table="till_vat_inv",
        pk="invoice_id",
        rg="vat.invoice|cash.receipt|ar_cents|applied_cents",
        rg_obs=_rg_obs("vat_inv", "issue_vat", "cash_apply", "test_issue_not_cash_double"),
        test_name="issue-not-cash-double test",
        surface_read="VAT invoice issue plus cash apply",
        skip_pred="this invoice already issued today",
        verb="recognize",
        skip_label="invoice-issued-today skip",
        src_body=_src,
        hook_body=(
            "def cash_apply(invoice_id, cents):\n"
            "    recognize_rev(invoice_id, cents)\n"
        ),
        test_body=(
            "def test_issue_not_cash_double():\n"
            '    issue_vat(iv("inv_1", cents=5000, vat=1000))\n'
            '    issue_vat(iv("inv_1", cents=5000, vat=1000))\n'
            '    cash_apply("inv_1", 6000)\n'
            '    assert ar_cents("inv_1") == 0 and rev_cents("inv_1") == 5000 and vat_cents("inv_1") == 1000 and vat_rows("inv_1") == 1\n'
            "\n"
            "def test_second_invoice():\n"
            '    issue_vat(iv("inv_a", cents=100, vat=20))\n'
            '    cash_apply("inv_a", 120)\n'
            '    issue_vat(iv("inv_b", cents=40, vat=8))\n'
            '    cash_apply("inv_b", 48)\n'
            '    assert rev_cents("inv_a") == 100 and rev_cents("inv_b") == 40\n'
        ),
        obs3="issue and cash both recognize revenue",
        obs4="issue books AR+rev; cash applies AR",
        obs5="rev once; AR 0 after cash; second invoice adds",
        fail_obs="FAILED test_issue_not_cash_double - rev 10000 or 11000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not issued_today(ev["invoice_id"]):\n        recognize_rev(ev["invoice_id"], ev["cents"])',
        obs7="cash still recognizes; new invoice same day dropped.",
        still_fail_obs="FAILED test_issue_not_cash_double - cash re-recognized rev\n1 failed, 1 passed",
        rewrite_src=(
            "def issue_vat(ev):\n"
            "    if not claim_inv(ev['invoice_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    book_ar(ev["invoice_id"], ev["cents"] + ev["vat"])\n'
            '    recognize_rev(ev["invoice_id"], ev["cents"])\n'
            '    book_vat(ev["invoice_id"], ev["vat"])\n'
            '    return {"ok": True, "issued": True}\n'
        ),
        rewrite_src_obs="claim invoice_id books AR/rev/VAT",
        rewrite_hook=(
            "def cash_apply(invoice_id, cents):\n"
            "    rid = rcpt_id(invoice_id, cents)\n"
            "    if not claim_rcpt(rid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    apply_ar(invoice_id, cents, receipt=rid)\n"
            '    return {"ok": True, "applied": True}\n'
        ),
        obs9="cash claims receipt_id applies AR.",
        rewrite_hook_obs="PK receipt apply",
        ddl=_ddl("till_vat_inv", "invoice_id", "  ar_cents int NOT NULL,\n  receipt_id text UNIQUE"),
        ddl_obs="PK invoice_id",
        test2_body=(
            "def test_second_invoice():\n"
            '    issue_vat(iv("inv_a", cents=100, vat=20))\n'
            '    cash_apply("inv_a", 120)\n'
            '    issue_vat(iv("inv_b", cents=40, vat=8))\n'
            '    cash_apply("inv_b", 48)\n'
            '    assert rev_cents("inv_a") == 100 and rev_cents("inv_b") == 40\n'
        ),
        psql_rows="inv_1\ninv_a\ninv_b",
        residual="partial cash",
        grep_pat="apply_ar",
        grep_obs="src/vat_inv.py: cash applies AR; no partial remainder",
        goal="till-vat issue and cash both recognized rev. Issue AR; cash apply. Gate: tests/test_vat_inv.py.",
        plan="Skip recognize if this invoice already issued today.",
        outcome="Issue+cash double-recognized. Invoice-day skip left cash as rev. Plan change: AR then apply. Tests 2/2 + second invoice + suite 8/8.",
    ),
    _fail(
        slug="credit-note-after-cash",
        surfaces="VAT credit note vs already-applied cash",
        avoided="r137 issue vs cash; r27 credit_note void. This is CN only unapplied",
        this_is="CN reverses unapplied AR only; cash stays",
        seed="cash apply then credit note full invoice",
        first_apply="credit noted today",
        plan_change="CN PK unapplied only; cash refund is handoff",
        step_note="CN-day 6–7; PK 8–11; second 12–13; cash-refund xfail 15–17.",
        next_note="Unused: CN after cash should refund cash. Avoid credit-noted-today skip.",
        **_paths("vat_cn", fail=True),
        table="till_vat_cn",
        pk="cn_id",
        rg="credit_note|unapplied_only|cash_refund",
        rg_obs=_rg_obs("vat_cn", "issue_cn", "cashed", "test_cn_not_full_after_cash"),
        test_name="cn-not-full-after-cash test",
        surface_read="credit note plus applied cash",
        skip_pred="this invoice already credit-noted today",
        verb="reverse",
        skip_label="credit-noted-today skip",
        src_body=_naive(
            "issue_cn",
            'recognize_rev(ev["invoice_id"], -ev["cents"])',
            "counted every credit note",
        )[0],
        hook_body=(
            "def cashed(invoice_id, cents):\n"
            "    apply_ar(invoice_id, cents)\n"
        ),
        test_body=(
            "def test_cn_not_full_after_cash():\n"
            '    issue_and_cash("inv_1", 5000, vat=1000, cash=6000)\n'
            '    issue_cn(cn("cn_1", invoice="inv_1", cents=5000, vat=1000))\n'
            '    issue_cn(cn("cn_1", invoice="inv_1", cents=5000, vat=1000))\n'
            '    assert rev_cents("inv_1") == 5000 and cn_cents("cn_1") == 0 and cn_rows("cn_1") == 1\n'
            "\n"
            "def test_second_cn():\n"
            '    issue_open("inv_a", 100, vat=20)\n'
            '    issue_cn(cn("cn_a", invoice="inv_a", cents=100, vat=20))\n'
            '    issue_open("inv_b", 40, vat=8)\n'
            '    assert rev_cents("inv_a") == 0 and rev_cents("inv_b") == 40\n'
        ),
        test_body_short="same — CN unapplied only; cash stays",
        obs3="CN reverses full rev after cash",
        obs4="CN unapplied only (0 after full cash)",
        obs5="rev stays 5000; CN 0; open invoice CN zeros",
        fail_obs="FAILED test_cn_not_full_after_cash - rev 0 == 5000 or cn 6000\n1 failed, 1 passed",
        skip_old=_naive(
            "issue_cn",
            'recognize_rev(ev["invoice_id"], -ev["cents"])',
            "counted every credit note",
        )[1],
        skip_new='    if not cn_today(ev["invoice_id"]):\n        recognize_rev(ev["invoice_id"], -ev["cents"])',
        obs7="second CN ok; hides unapplied-only.",
        still_fail_obs="FAILED if CN reversed rev after cash (should be 0 CN)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def issue_cn(ev):\n"
            "    if not claim_cn(ev['cn_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    open_ar = ar_of(ev['invoice_id'])\n"
            "    take = min(ev['cents'] + ev['vat'], open_ar)\n"
            "    if take == 0:\n"
            '        return {"ok": True, "nothing": True}\n'
            "    reverse_ar(ev['invoice_id'], take, cn=ev['cn_id'])\n"
            '    return {"ok": True, "cn": take}\n'
        ),
        rewrite_src_obs="claim cn_id reverses unapplied only",
        rewrite_hook=(
            "def cashed(invoice_id, cents):\n"
            "    if not claim_rcpt2(rcpt_id(invoice_id, cents)):\n"
            '        return {"ok": True, "dup": True}\n'
            "    apply_ar(invoice_id, cents)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="cash apply before CN",
        ddl=_ddl("till_vat_cn", "cn_id", "  invoice_id text NOT NULL,\n  cn_cents int NOT NULL DEFAULT 0"),
        ddl_obs="PK cn_id",
        test2_body=(
            "def test_second_cn():\n"
            '    issue_open("inv_a", 100, vat=20)\n'
            '    issue_cn(cn("cn_a", invoice="inv_a", cents=100, vat=20))\n'
            '    issue_open("inv_b", 40, vat=8)\n'
            '    assert rev_cents("inv_a") == 0 and rev_cents("inv_b") == 40\n'
        ),
        xfail_label="CN after cash should refund cash",
        xfail_body=(
            "def test_cn_refunds_cash():\n"
            '    issue_and_cash("inv_p", 5000, vat=1000, cash=6000)\n'
            '    issue_cn(cn("cn_p", invoice="inv_p", cents=5000, vat=1000))\n'
            '    assert cash_refund("inv_p") == 6000 and rev_cents("inv_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_cn_refunds_cash - no cash refund; rev stays\n1 failed",
        xfail_old="def test_cn_refunds_cash():",
        xfail_new='@pytest.mark.xfail(reason="handoff: CN after cash must refund receipt, not no-op", strict=True)\ndef test_cn_refunds_cash():',
        xfail_patch_obs="xfailed CN cash refund",
        goal="till-vat-cn CN reversed rev after cash. CN unapplied only. Gate: tests/test_vat_cn.py.",
        plan="Skip reverse if this invoice already credit-noted today.",
        outcome="CN reversed cashed invoice. CN-day skip hid unapplied-only. Plan change: CN min(open AR). Primary+second pass. Partial: cash-refund xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r138 hold-to-available / payout of held
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "place_hold",
    'credit_avail(ev["hold_id"], ev["cents"])',
    "counted every funds hold",
)
pair(
    _ok(
        slug="hold-to-available",
        surfaces="pending hold vs available release",
        avoided="r96 fencing lease; r21 received_debit. This is hold_id pending then release moves available",
        this_is="hold PK pending; release PK moves hold→available",
        seed="place hold + release to available",
        first_apply="funds available today",
        plan_change="hold pending PK; release moves, does not extra-credit",
        step_note="Hold-day 6–7; PK 8–11; second hold 12–13.",
        **_paths("h2a"),
        table="till_h2a",
        pk="hold_id",
        rg="funds.hold|available.release|pending_cents|move_available",
        rg_obs=_rg_obs("h2a", "place_hold", "rel_avail", "test_hold_not_avail_double"),
        test_name="hold-not-avail-double test",
        surface_read="pending hold plus available release",
        skip_pred="this merchant funds already available today",
        verb="credit",
        skip_label="funds-available-today skip",
        src_body=_src,
        hook_body=(
            "def rel_avail(hold_id, cents):\n"
            "    credit_avail(hold_id, cents)\n"
        ),
        test_body=(
            "def test_hold_not_avail_double():\n"
            '    place_hold(hd("h_1", merchant="m_1", cents=5000))\n'
            '    place_hold(hd("h_1", merchant="m_1", cents=5000))\n'
            '    rel_avail("h_1", 5000)\n'
            '    assert pending_cents("m_1") == 0 and avail_cents("m_1") == 5000 and hold_rows("h_1") == 1\n'
            "\n"
            "def test_second_hold():\n"
            '    place_hold(hd("h_a", merchant="m_a", cents=100))\n'
            '    rel_avail("h_a", 100)\n'
            '    place_hold(hd("h_b", merchant="m_b", cents=40))\n'
            '    rel_avail("h_b", 40)\n'
            '    assert avail_cents("m_a") == 100 and avail_cents("m_b") == 40\n'
        ),
        obs3="hold and release both credit available",
        obs4="hold pending; release moves to available",
        obs5="avail 5000 pending 0; hold once; second hold adds",
        fail_obs="FAILED test_hold_not_avail_double - avail 10000 or 15000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not avail_today(ev["merchant"]):\n        credit_avail(ev["hold_id"], ev["cents"])',
        obs7="release still credits avail; new merchant same day dropped.",
        still_fail_obs="FAILED test_hold_not_avail_double - release extra-credited avail\n1 failed, 1 passed",
        rewrite_src=(
            "def place_hold(ev):\n"
            "    if not claim_hold(ev['hold_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_pending(ev["merchant"], ev["cents"], hold=ev["hold_id"])\n'
            '    return {"ok": True, "held": True}\n'
        ),
        rewrite_src_obs="claim hold_id credits pending",
        rewrite_hook=(
            "def rel_avail(hold_id, cents):\n"
            "    if not claim_h2a(hold_id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    move_pending_to_avail(hold_id, cents)\n"
            '    return {"ok": True, "available": True}\n'
        ),
        obs9="release claims hold_id move pending→avail.",
        rewrite_hook_obs="move not extra credit",
        ddl=_ddl("till_h2a", "hold_id", "  merchant text NOT NULL,\n  pending int NOT NULL,\n  available int NOT NULL DEFAULT 0"),
        ddl_obs="PK hold_id",
        test2_body=(
            "def test_second_hold():\n"
            '    place_hold(hd("h_a", merchant="m_a", cents=100))\n'
            '    rel_avail("h_a", 100)\n'
            '    place_hold(hd("h_b", merchant="m_b", cents=40))\n'
            '    rel_avail("h_b", 40)\n'
            '    assert avail_cents("m_a") == 100 and avail_cents("m_b") == 40\n'
        ),
        psql_rows="h_1\nh_a\nh_b",
        residual="partial available release",
        grep_pat="move_pending",
        grep_obs="src/h2a.py: move pending→avail; no partial leftover",
        goal="till-h2a hold and release both credited available. Hold pending; release moves. Gate: tests/test_h2a.py.",
        plan="Skip credit if this merchant funds already available today.",
        outcome="Hold+release double-credited avail. Merchant-day skip left release as credit. Plan change: pending then move. Tests 2/2 + second hold + suite 8/8.",
    ),
    _fail(
        slug="payout-of-held-funds",
        surfaces="payout vs still-held (not yet available) funds",
        avoided="r138 hold-to-available; r03 payout. This is payout only from available",
        this_is="payout PK from available; held is not spendable",
        seed="place hold then payout without release",
        first_apply="payout sent today",
        plan_change="payout only from available; held blocks",
        step_note="Payout-day 6–7; PK 8–11; second 12–13; force-held xfail 15–17.",
        next_note="Unused: payout of held should block (or force-release). Avoid payout-sent-today skip.",
        **_paths("a2p", fail=True),
        table="till_a2p",
        pk="payout_id",
        rg="payout.held|available_only|spendable",
        rg_obs=_rg_obs("a2p", "pay_out", "held_only", "test_payout_not_held"),
        test_name="payout-not-held test",
        surface_read="payout plus still-held funds",
        skip_pred="this merchant payout already sent today",
        verb="payout",
        skip_label="payout-sent-today skip",
        src_body=_naive(
            "pay_out",
            'debit_avail(ev["merchant"], ev["cents"])',
            "counted every payout",
        )[0],
        hook_body=(
            "def held_only(merchant, cents):\n"
            "    credit_pending(merchant, cents)\n"
        ),
        test_body=(
            "def test_payout_not_held():\n"
            '    held_only("m_1", 5000)\n'
            '    pay_out(po("po_1", merchant="m_1", cents=5000))\n'
            '    pay_out(po("po_1", merchant="m_1", cents=5000))\n'
            '    assert pending_cents("m_1") == 5000 and paid_cents("m_1") == 0 and po_rows("po_1") == 1\n'
            "\n"
            "def test_second_payout():\n"
            '    credit_avail("m_a", 100)\n'
            '    pay_out(po("po_a", merchant="m_a", cents=100))\n'
            '    credit_avail("m_b", 40)\n'
            '    pay_out(po("po_b", merchant="m_b", cents=40))\n'
            '    assert paid_cents("m_a") == 100 and paid_cents("m_b") == 40\n'
        ),
        test_body_short="same — payout only from available",
        obs3="payout spends held",
        obs4="payout blocked if only held",
        obs5="pending stays 5000; paid 0; available payouts work",
        fail_obs="FAILED test_payout_not_held - pending 0 or paid 5000\n1 failed, 1 passed",
        skip_old=_naive(
            "pay_out",
            'debit_avail(ev["merchant"], ev["cents"])',
            "counted every payout",
        )[1],
        skip_new='    if not paid_today(ev["merchant"]):\n        debit_avail(ev["merchant"], ev["cents"])',
        obs7="second payout ok; hides held block.",
        still_fail_obs="FAILED if payout spent held (pending 0)\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def pay_out(ev):\n"
            "    if not claim_po2(ev['payout_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            "    if avail_of(ev['merchant']) < ev['cents']:\n"
            '        return {"ok": True, "blocked": True}\n'
            '    debit_avail(ev["merchant"], ev["cents"], payout=ev["payout_id"])\n'
            '    return {"ok": True, "paid": True}\n'
        ),
        rewrite_src_obs="claim payout_id; blocked if avail short",
        rewrite_hook=(
            "def held_only(merchant, cents):\n"
            "    hid = hold_id(merchant, cents)\n"
            "    if not claim_hold2(hid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_pending(merchant, cents, hold=hid)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="held stays pending",
        ddl=_ddl("till_a2p", "payout_id", "  merchant text NOT NULL,\n  blocked bool NOT NULL DEFAULT false"),
        ddl_obs="PK payout_id",
        test2_body=(
            "def test_second_payout():\n"
            '    credit_avail("m_a", 100)\n'
            '    pay_out(po("po_a", merchant="m_a", cents=100))\n'
            '    credit_avail("m_b", 40)\n'
            '    pay_out(po("po_b", merchant="m_b", cents=40))\n'
            '    assert paid_cents("m_a") == 100 and paid_cents("m_b") == 40\n'
        ),
        xfail_label="force payout of held",
        xfail_body=(
            "def test_force_held_payout():\n"
            '    held_only("m_p", 5000)\n'
            '    pay_out(po("po_p", merchant="m_p", cents=5000, force=True))\n'
            '    assert paid_cents("m_p") == 5000 and pending_cents("m_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_force_held_payout - blocked; no force path\n1 failed",
        xfail_old="def test_force_held_payout():",
        xfail_new='@pytest.mark.xfail(reason="handoff: force payout of held must audit-bypass available check", strict=True)\ndef test_force_held_payout():',
        xfail_patch_obs="xfailed force held payout",
        goal="till-a2p payout spent held funds. Payout only from available. Gate: tests/test_a2p.py.",
        plan="Skip payout if this merchant payout already sent today.",
        outcome="Payout spent held. Payout-day skip hid available-only. Plan change: block if avail short. Primary+second pass. Partial: force-held xfail handoff.",
    ),
)

# ---------------------------------------------------------------------------
# r139 representment vs win / second presentment after lost
# ---------------------------------------------------------------------------
_src, _skip = _naive(
    "submit_rep",
    'credit_merch(ev["dispute_id"], ev["cents"])',
    "counted every representment",
)
pair(
    _ok(
        slug="representment-vs-win",
        surfaces="chargeback representment submit vs win credit",
        avoided="r126 cb vs refund; r31 dispute evidence. This is represent PK vs win cycle credit",
        this_is="submit records evidence; win PK (dispute, cycle) credits once",
        seed="submit representment + win same dispute",
        first_apply="represented today",
        plan_change="submit records; win PK credits merchant once per cycle",
        step_note="Dispute-day 6–7; PK 8–11; second dispute 12–13.",
        **_paths("cb_rep"),
        table="till_cb_rep",
        pk="win_id",
        rg="representment|dispute.win|cycle|evidence",
        rg_obs=_rg_obs("cb_rep", "submit_rep", "win_cb", "test_submit_not_win_double"),
        test_name="submit-not-win-double test",
        surface_read="representment submit plus win credit",
        skip_pred="this dispute already represented today",
        verb="credit",
        skip_label="represented-today skip",
        src_body=_src,
        hook_body=(
            "def win_cb(dispute_id, cents, cycle=1):\n"
            "    credit_merch(dispute_id, cents)\n"
        ),
        test_body=(
            "def test_submit_not_win_double():\n"
            '    submit_rep(rp("dp_1", cents=5000, cycle=1))\n'
            '    submit_rep(rp("dp_1", cents=5000, cycle=1))\n'
            '    win_cb("dp_1", 5000, cycle=1)\n'
            '    assert merch_cents("m_1") == 5000 and evidence("dp_1") and rep_rows("wn_1") == 1\n'
            "\n"
            "def test_second_dispute():\n"
            '    submit_rep(rp("dp_a", cents=100, cycle=1))\n'
            '    win_cb("dp_a", 100, cycle=1)\n'
            '    submit_rep(rp("dp_b", cents=40, cycle=1))\n'
            '    win_cb("dp_b", 40, cycle=1)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        obs3="submit and win both credit merchant",
        obs4="submit records evidence; win PK credits",
        obs5="credit once; submit no extra; second dispute adds",
        fail_obs="FAILED test_submit_not_win_double - merch 10000 or 15000\n1 failed, 1 passed",
        skip_old=_skip,
        skip_new='    if not represented_today(ev["dispute_id"]):\n        credit_merch(ev["dispute_id"], ev["cents"])',
        obs7="win still credits extra; new dispute same day dropped.",
        still_fail_obs="FAILED test_submit_not_win_double - win extra-credited\n1 failed, 1 passed",
        rewrite_src=(
            "def submit_rep(ev):\n"
            "    if not claim_rep(ev['dispute_id'], ev['cycle']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    store_evidence(ev["dispute_id"], ev["cycle"])\n'
            '    return {"ok": True, "submitted": True}\n'
        ),
        rewrite_src_obs="claim (dispute, cycle) stores evidence",
        rewrite_hook=(
            "def win_cb(dispute_id, cents, cycle=1):\n"
            "    wid = win_id(dispute_id, cycle)\n"
            "    if not claim_win(wid):\n"
            '        return {"ok": True, "dup": True}\n'
            "    credit_merch(merch_of_dp(dispute_id), cents, win=wid)\n"
            '    return {"ok": True, "won": True}\n'
        ),
        obs9="win claims win_id per cycle.",
        rewrite_hook_obs="PK win_id",
        ddl=_ddl("till_cb_rep", "win_id", "  dispute_id text NOT NULL,\n  cycle int NOT NULL,\n  UNIQUE (dispute_id, cycle)"),
        ddl_obs="PK win_id",
        test2_body=(
            "def test_second_dispute():\n"
            '    submit_rep(rp("dp_a", cents=100, cycle=1))\n'
            '    win_cb("dp_a", 100, cycle=1)\n'
            '    submit_rep(rp("dp_b", cents=40, cycle=1))\n'
            '    win_cb("dp_b", 40, cycle=1)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        psql_rows="wn_1\nwn_a\nwn_b",
        residual="second cycle representment",
        grep_pat="cycle",
        grep_obs="src/cb_rep.py: unique (dispute, cycle); no cycle 2",
        goal="till-rep submit and win both credited. Submit evidence; win PK. Gate: tests/test_cb_rep.py.",
        plan="Skip credit if this dispute already represented today.",
        outcome="Submit+win double-credited. Dispute-day skip left win extra. Plan change: evidence then win PK. Tests 2/2 + second dispute + suite 8/8.",
    ),
    _fail(
        slug="second-pres-after-lost",
        surfaces="second presentment vs already-lost dispute",
        avoided="r139 represent vs win; r126 lost debit. This is lost blocks second presentment",
        this_is="lost flags dispute; second presentment refused; pre-arb is handoff",
        seed="lose dispute then second presentment",
        first_apply="dispute lost today",
        plan_change="lost PK; second presentment blocked",
        step_note="Lost-day 6–7; PK 8–11; second 12–13; pre-arb xfail 15–17.",
        next_note="Unused: pre-arb after lost. Avoid dispute-lost-today skip.",
        **_paths("cb_2nd", fail=True),
        table="till_cb_2nd",
        pk="dispute_id",
        rg="second_presentment|pre_arb|lost_blocks",
        rg_obs=_rg_obs("cb_2nd", "lose_then", "second_pres", "test_lost_not_second"),
        test_name="lost-not-second test",
        surface_read="lost dispute plus second presentment",
        skip_pred="this dispute already lost today",
        verb="credit",
        skip_label="dispute-lost-today skip",
        src_body=_naive(
            "lose_then",
            'credit_merch(ev["dispute_id"], ev.get("cents", 0))',
            "counted every lost flag",
        )[0],
        hook_body=(
            "def second_pres(dispute_id, cents):\n"
            "    credit_merch(dispute_id, cents)\n"
        ),
        test_body=(
            "def test_lost_not_second():\n"
            '    lose_then(ls("dp_1", cents=0))\n'
            '    lose_then(ls("dp_1", cents=0))\n'
            '    second_pres("dp_1", 5000)\n'
            '    assert lost("dp_1") and merch_cents("m_1") == 0 and lost_rows("dp_1") == 1\n'
            "\n"
            "def test_second_dispute():\n"
            '    submit_and_win("dp_a", 100)\n'
            '    submit_and_win("dp_b", 40)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        test_body_short="same — lost blocks second presentment",
        obs3="lost and second presentment both credit",
        obs4="lost flags; second blocked",
        obs5="merch 0; lost once; other disputes can win",
        fail_obs="FAILED test_lost_not_second - merch 5000 == 0 or rows 3\n1 failed, 1 passed",
        skip_old=_naive(
            "lose_then",
            'credit_merch(ev["dispute_id"], ev.get("cents", 0))',
            "counted every lost flag",
        )[1],
        skip_new='    if not lost_today(ev["dispute_id"]):\n        credit_merch(ev["dispute_id"], ev.get("cents", 0))',
        obs7="second dispute ok; hides lost block.",
        still_fail_obs="FAILED if second presentment credited after lost\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def lose_then(ev):\n"
            "    if not claim_lost2(ev['dispute_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    mark_lost(ev["dispute_id"])\n'
            '    return {"ok": True, "lost": True}\n'
        ),
        rewrite_src_obs="claim dispute_id marks lost; no credit",
        rewrite_hook=(
            "def second_pres(dispute_id, cents):\n"
            "    if lost(dispute_id):\n"
            '        return {"ok": True, "blocked": True}\n'
            "    if not claim_rep2(dispute_id, cycle=2):\n"
            '        return {"ok": True, "dup": True}\n'
            "    store_evidence(dispute_id, 2)\n"
            '    return {"ok": True, "cycle": 2}\n'
        ),
        rewrite_hook_obs="second presentment blocked if lost",
        ddl=_ddl("till_cb_2nd", "dispute_id", "  lost bool NOT NULL DEFAULT true"),
        ddl_obs="PK dispute_id",
        test2_body=(
            "def test_second_dispute():\n"
            '    submit_and_win("dp_a", 100)\n'
            '    submit_and_win("dp_b", 40)\n'
            '    assert merch_cents("m_a") == 100 and merch_cents("m_b") == 40\n'
        ),
        xfail_label="pre-arb after lost",
        xfail_body=(
            "def test_prearb_after_lost():\n"
            '    lose_then(ls("dp_p", cents=0))\n'
            '    second_pres("dp_p", 5000, prearb=True)\n'
            '    assert merch_cents("m_p") == 0 and prearb("dp_p")\n'
        ),
        xfail_fail_obs="FAILED test_prearb_after_lost - blocked; no pre-arb path\n1 failed",
        xfail_old="def test_prearb_after_lost():",
        xfail_new='@pytest.mark.xfail(reason="handoff: pre-arb after lost is a separate network case", strict=True)\ndef test_prearb_after_lost():',
        xfail_patch_obs="xfailed pre-arb after lost",
        goal="till-cb-2nd second presentment credited after lost. Lost blocks second. Gate: tests/test_cb_2nd.py.",
        plan="Skip credit if this dispute already lost today.",
        outcome="Second presentment credited after lost. Lost-day skip hid block. Plan change: lost PK; second refuses. Primary+second pass. Partial: pre-arb xfail handoff.",
    ),
)



