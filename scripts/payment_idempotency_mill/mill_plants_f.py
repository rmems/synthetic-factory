"""Plants r117–r124."""

from mill_plants import _ok, _fail

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))
    return ok, bad


pair(
    _ok(
        slug="clover-payment-vs-refund",
        surfaces="Clover payments API vs refunds webhook",
        avoided="r60 Square two refund keys; r97 CKO refund vs void. This is Clover payment_id vs refund_id",
        this_is="Clover capture vs refund dual reverse",
        seed="payment capture retry + PaymentRefund webhook",
        first_apply="merchant captured today",
        plan_change="unique idempotency_key; capture PK payment_id; refund PK refund_id",
        step_note="Merchant-day 6–7; PK 8–11; second 12–13.",
        src="src/clover_pay.py",
        hook="src/clover_ref.py",
        test="tests/test_clover.py",
        test2="tests/test_clover_two.py",
        mig="clover_pay",
        table="till_clover_pay",
        pk="payment_id",
        rg="clover.payments|PaymentRefund|idempotency_key",
        rg_obs="src/clover_pay.py:8: def capture_clover\nsrc/clover_ref.py:6: def on_clover\ntests/test_clover.py: def test_capture_not_webhook_double\n",
        test_name="capture-not-webhook-double test",
        surface_read="Clover payments capture plus Payment.created webhook",
        skip_pred="this Clover merchant already captured today",
        verb="fulfill",
        skip_label="merchant-captured-today skip",
        src_body=(
            "def capture_clover(order_id, cents, ik):\n"
            "    p = clover.payments.create(order_id=order_id, amount=cents, idempotency_key=ik)\n"
            "    fulfill_clover(p.id, cents)  # counted every capture retry\n"
            "    return p\n"
        ),
        hook_body=(
            "def on_clover(ev):\n"
            '    if ev["type"] in ("P", "PAYMENT"):\n'
            '        fulfill_clover(ev["id"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_capture_not_webhook_double():\n"
            '    capture_clover("ord_1", 5000, ik="ik_1")\n'
            '    capture_clover("ord_1", 5000, ik="ik_1")\n'
            '    on_clover(cl("PAYMENT", id="clp_1", amount=5000))\n'
            '    assert fulfill_cents("clp_1") == 5000 and cl_rows("clp_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    capture_clover("ord_a", 100, ik="ika")\n'
            '    capture_clover("ord_b", 40, ik="ikb")\n'
            '    assert fulfill_cents(last_p("ord_a")) == 100\n'
        ),
        obs3="webhook fulfills again",
        obs4="one row per payment_id; webhook once; second order adds",
        obs5="one row per payment_id; capture once; second order adds",
        fail_obs="FAILED test_capture_not_webhook_double - cl_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_clover(p.id, cents)  # counted every capture retry",
        skip_new="    if not captured_today(order_id):\n        fulfill_clover(p.id, cents)",
        obs7="webhook still fulfills; new order same day dropped.",
        still_fail_obs="FAILED test_capture_not_webhook_double - webhook still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def capture_clover(order_id, cents, ik):\n"
            "    if not claim_clover_ik(ik):\n"
            "        return existing_by_ik(ik)\n"
            "    p = clover.payments.create(order_id=order_id, amount=cents, idempotency_key=ik)\n"
            "    if not claim_clover(p.id):\n"
            "        return p\n"
            "    fulfill_clover(p.id, cents, order=order_id)\n"
            "    return p\n"
        ),
        rewrite_src_obs="unique ik + claim payment_id",
        rewrite_hook=(
            "def on_clover(ev):\n"
            '    if ev.get("type") not in ("P", "PAYMENT"):\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_clover(ev['id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_clover(ev["id"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        obs9="webhook claims same payment_id.",
        rewrite_hook_obs="PK payment_id",
        ddl="CREATE TABLE till_clover_pay (\n  payment_id text PRIMARY KEY,\n  ik text UNIQUE,\n  cents int NOT NULL\n);\n",
        ddl_obs="PK payment_id",
        test2_body=(
            "def test_second_order():\n"
            '    capture_clover("ord_a", 100, ik="ika")\n'
            '    capture_clover("ord_b", 40, ik="ikb")\n'
            '    assert fulfill_cents(last_p("ord_a")) == 100 and fulfill_cents(last_p("ord_b")) == 40\n'
        ),
        psql_rows="clp_1\nclp_a\nclp_b",
        residual="refund after capture last-write",
        grep_pat="refund",
        grep_obs="src/clover_pay.py: claim then insert; no refund reverse",
        goal="till-clover payments.create retried with PAYMENT webhook. PK Clover payment_id. Gate: tests/test_clover.py.",
        plan="Skip fulfill if this Clover merchant already captured today.",
        outcome="Capture+webhook triple-rowed. Merchant-day skip left webhook unguarded. Plan change: unique ik + PK payment_id. Tests 2/2 + second order + suite 8/8.",
    ),
    _fail(
        slug="fednow-credit-vs-webhook",
        surfaces="FedNow incoming credit vs payment_status webhook",
        avoided="r101 Increase inbound ACH; r110 Column ACH. This is FedNow uetr / e2e_id",
        this_is="FedNow credit message vs status webhook",
        seed="incoming FedNow credit + payment_status ACCP",
        first_apply="account fednow today",
        plan_change="PK e2e_id on ACCP; RJCT does not credit",
        step_note="Account-day 6–7; PK 8–11; second 12–13; RJCT after ACCP xfail 15–17.",
        next_note="Unused: FedNow RJCT after ACCP. Avoid account-fednow-today skip.",
        src="src/fednow_in.py",
        hook="src/fednow_st.py",
        test="tests/test_fednow.py",
        test2="tests/test_fednow_two.py",
        xfail="tests/test_fednow_rjct.py",
        mig="fednow_in",
        table="till_fednow",
        pk="e2e_id",
        rg="FedNow|pacs.008|e2e_id|ACCP|RJCT",
        rg_obs="src/fednow_in.py:8: def on_fednow\nsrc/fednow_st.py:6: def credit_fn\ntests/test_fednow.py: def test_credit_not_status_double\n",
        test_name="credit-not-status-double test",
        surface_read="FedNow incoming credit plus payment_status ACCP",
        skip_pred="this FedNow account already credited today",
        verb="credit",
        skip_label="account-fednow-today skip",
        src_body=(
            "def on_fednow(msg):\n"
            '    credit_fn(msg["e2e_id"], msg["amount"])\n'
            '    return {"ok": True}\n'
        ),
        hook_body=(
            "def on_status(st):\n"
            '    if st["status"] in ("ACCP", "RJCT"):\n'
            '        credit_fn(st["e2e_id"], st["amount"])\n'
            "    return st\n"
        ),
        test_body=(
            "def test_credit_not_status_double():\n"
            '    on_fednow(fn(e2e_id="e2e_1", amount=5000, account="acc_1"))\n'
            '    on_fednow(fn(e2e_id="e2e_1", amount=5000, account="acc_1"))\n'
            '    on_status(fn_st(e2e_id="e2e_1", status="ACCP", amount=5000))\n'
            '    assert credit_cents("acc_1") == 5000 and fn_rows("e2e_1") == 1\n'
            "\n"
            "def test_second_account():\n"
            '    on_fednow(fn(e2e_id="e2e_a", amount=100, account="acc_a"))\n'
            '    on_fednow(fn(e2e_id="e2e_b", amount=40, account="acc_b"))\n'
            '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
        ),
        test_body_short="same — PK e2e_id on ACCP; status no extra",
        obs3="status ACCP credits again",
        obs4="PK e2e_id; status no extra credit",
        obs5="credit once; status no second; second account adds",
        fail_obs="FAILED test_credit_not_status_double - fn_rows 3 == 1\n1 failed, 1 passed",
        skip_old='    credit_fn(msg["e2e_id"], msg["amount"])',
        skip_new='    if not fednow_today(msg.get("account") or msg["e2e_id"]):\n        credit_fn(msg["e2e_id"], msg["amount"])',
        obs7="second account ok; hides missing e2e_id PK.",
        still_fail_obs="FAILED if first status was RJCT (should not credit) then ACCP same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def on_fednow(msg):\n"
            '    eid = msg["e2e_id"]\n'
            "    if not claim_fn(eid):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_fn(eid, msg["amount"], account=msg.get("account"))\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="claim e2e_id",
        rewrite_hook=(
            "def on_status(st):\n"
            '    if st.get("status") == "RJCT":\n'
            '        return {"ok": True, "reject": True}\n'
            '    if st.get("status") != "ACCP":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_fn(st['e2e_id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_fn(st["e2e_id"], st["amount"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK e2e_id; RJCT no credit",
        ddl="CREATE TABLE till_fednow (\n  e2e_id text PRIMARY KEY,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK e2e_id",
        test2_body=(
            "def test_second_account():\n"
            '    on_fednow(fn(e2e_id="e2e_a", amount=100, account="acc_a"))\n'
            '    on_fednow(fn(e2e_id="e2e_b", amount=40, account="acc_b"))\n'
            '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
        ),
        xfail_label="RJCT after ACCP",
        xfail_body=(
            "def test_accp_then_rjct():\n"
            '    on_fednow(fn(e2e_id="e2e_p", amount=5000, account="acc_p"))\n'
            '    on_status(fn_st(e2e_id="e2e_p", status="RJCT", amount=5000))\n'
            '    assert credit_cents("acc_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_accp_then_rjct - RJCT marked reject without reverse; cents still 5000\n1 failed",
        xfail_old="def test_accp_then_rjct():",
        xfail_new='@pytest.mark.xfail(reason="handoff: RJCT after ACCP must reverse claimed e2e_id", strict=True)\ndef test_accp_then_rjct():',
        xfail_patch_obs="xfailed ACCP then RJCT",
        goal="till-fn incoming FedNow and payment_status ACCP both credited e2e_1. PK e2e_id. Gate: tests/test_fednow.py.",
        plan="Skip credit if this FedNow account already credited today.",
        outcome="Credit+ACCP double-credited. Account-day skip hid e2e_id. Plan change: PK e2e_id; RJCT no credit. Primary+second pass. Partial: RJCT after ACCP xfail handoff.",
    ),
)

pair(
    _ok(
        slug="revolut-payout-vs-webhook",
        surfaces="Revolut Business payout create vs TransactionStateChanged",
        avoided="r64 PayPal payout; r113 Payoneer. This is Revolut request_id vs transaction_id",
        this_is="Revolut payout vs completed webhook",
        seed="payout create retry + TransactionStateChanged completed",
        first_apply="counterparty paid today",
        plan_change="unique request_id; PK transaction_id on completed",
        step_note="Counterparty-day 6–7; PK 8–11; second 12–13.",
        src="src/rev_payout.py",
        hook="src/rev_hook.py",
        test="tests/test_rev.py",
        test2="tests/test_rev_two.py",
        mig="rev_payout",
        table="till_rev_txn",
        pk="transaction_id",
        rg="TransactionStateChanged|request_id|revolut.payout",
        rg_obs="src/rev_payout.py:8: def create_rev\nsrc/rev_hook.py:6: def on_rev\ntests/test_rev.py: def test_create_not_completed_double\n",
        test_name="create-not-completed-double test",
        surface_read="Revolut payout create plus TransactionStateChanged",
        skip_pred="this Revolut counterparty already paid today",
        verb="fulfill",
        skip_label="counterparty-paid-today skip",
        src_body=(
            "def create_rev(cp, cents, rid):\n"
            "    t = revolut.payouts.create(counterparty=cp, amount=cents, request_id=rid)\n"
            "    fulfill_rev(t.id, cents)  # counted every create retry\n"
            "    return t\n"
        ),
        hook_body=(
            "def on_rev(ev):\n"
            '    if ev["event"] == "TransactionStateChanged":\n'
            '        fulfill_rev(ev["data"]["id"], ev["data"]["amount"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_create_not_completed_double():\n"
            '    create_rev("cp_1", 5000, rid="rid_1")\n'
            '    create_rev("cp_1", 5000, rid="rid_1")\n'
            '    on_rev(rev_ev("TransactionStateChanged", id="rt_1", amount=5000, state="completed"))\n'
            '    assert fulfill_cents("rt_1") == 5000 and rev_rows("rt_1") == 1\n'
            "\n"
            "def test_second_cp():\n"
            '    create_rev("cp_a", 100, rid="ra")\n'
            '    create_rev("cp_b", 40, rid="rb")\n'
            '    assert rev_rows(last_t("cp_a")) == 1\n'
        ),
        obs3="state-changed fulfills again",
        obs4="one row per transaction_id; completed once; second CP adds",
        obs5="one row per transaction_id; create once; second CP adds",
        fail_obs="FAILED test_create_not_completed_double - rev_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_rev(t.id, cents)  # counted every create retry",
        skip_new="    if not paid_today(cp):\n        fulfill_rev(t.id, cents)",
        obs7="webhook still fulfills; new payout same day dropped.",
        still_fail_obs="FAILED test_create_not_completed_double - webhook still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def create_rev(cp, cents, rid):\n"
            "    if not claim_rev_rid(rid):\n"
            "        return existing_by_rid(rid)\n"
            "    t = revolut.payouts.create(counterparty=cp, amount=cents, request_id=rid)\n"
            "    if t.state == 'completed' and claim_rev(t.id):\n"
            "        fulfill_rev(t.id, cents)\n"
            "    return t\n"
        ),
        rewrite_src_obs="unique request_id; fulfill on completed",
        rewrite_hook=(
            "def on_rev(ev):\n"
            '    if ev.get("event") != "TransactionStateChanged" or ev["data"].get("state") != "completed":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_rev(ev['data']['id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_rev(ev["data"]["id"], ev["data"]["amount"])\n'
            '    return {"ok": True}\n'
        ),
        obs9="webhook claims same transaction_id.",
        rewrite_hook_obs="PK transaction_id",
        ddl="CREATE TABLE till_rev_txn (\n  transaction_id text PRIMARY KEY,\n  request_id text UNIQUE,\n  cents int NOT NULL\n);\n",
        ddl_obs="PK transaction_id",
        test2_body=(
            "def test_second_cp():\n"
            '    create_rev("cp_a", 100, rid="ra")\n'
            '    on_rev(rev_ev("TransactionStateChanged", id="rt_a", amount=100, state="completed"))\n'
            '    create_rev("cp_b", 40, rid="rb")\n'
            '    on_rev(rev_ev("TransactionStateChanged", id="rt_b", amount=40, state="completed"))\n'
            '    assert fulfill_cents("rt_a") == 100 and fulfill_cents("rt_b") == 40\n'
        ),
        psql_rows="rt_1\nrt_a\nrt_b",
        residual="declined after completed last-write",
        grep_pat="declined",
        grep_obs="src/rev_payout.py: claim then insert; no state CAS",
        goal="till-rev payouts.create retried with TransactionStateChanged completed. PK Revolut transaction_id. Gate: tests/test_rev.py.",
        plan="Skip fulfill if this Revolut counterparty already paid today.",
        outcome="Create+completed triple-rowed. Counterparty-day skip left webhook unguarded. Plan change: unique request_id + PK transaction_id. Tests 2/2 + second CP + suite 8/8.",
    ),
    _fail(
        slug="mercury-transfer-vs-webhook",
        surfaces="Mercury sendMoney vs transaction.created webhook",
        avoided="r103 Modern Treasury PO; r111 Synctera. This is Mercury idempotencyKey vs transaction id",
        this_is="Mercury sendMoney vs transaction.created",
        seed="sendMoney retry + transaction.created",
        first_apply="account sent today",
        plan_change="unique idempotencyKey; PK transaction_id on created posted",
        step_note="Account-day 6–7; PK 8–11; second 12–13; failed after sent xfail 15–17.",
        next_note="Unused: Mercury failed after sent. Avoid account-sent-today skip.",
        src="src/merc_send.py",
        hook="src/merc_hook.py",
        test="tests/test_merc.py",
        test2="tests/test_merc_two.py",
        xfail="tests/test_merc_fail.py",
        mig="merc_send",
        table="till_merc_txn",
        pk="transaction_id",
        rg="sendMoney|idempotencyKey|mercury.*transaction",
        rg_obs="src/merc_send.py:8: def send_merc\nsrc/merc_hook.py:6: def on_merc\ntests/test_merc.py: def test_send_not_created_double\n",
        test_name="send-not-created-double test",
        surface_read="Mercury sendMoney plus transaction.created",
        skip_pred="this Mercury account already sent today",
        verb="fulfill",
        skip_label="account-sent-today skip",
        src_body=(
            "def send_merc(account_id, cents, ik):\n"
            "    t = mercury.sendMoney(account=account_id, amount=cents, idempotencyKey=ik)\n"
            "    fulfill_merc(t.id, cents)  # counted every send retry\n"
            "    return t\n"
        ),
        hook_body=(
            "def on_merc(ev):\n"
            '    if ev["type"] in ("transaction.created", "transaction.updated"):\n'
            '        fulfill_merc(ev["data"]["id"], ev["data"]["amount"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_send_not_created_double():\n"
            '    send_merc("acc_1", 5000, ik="ik_1")\n'
            '    send_merc("acc_1", 5000, ik="ik_1")\n'
            '    on_merc(merc_ev("transaction.created", id="mt_1", amount=5000, status="sent"))\n'
            '    assert fulfill_cents("mt_1") == 5000 and merc_rows("mt_1") == 1\n'
            "\n"
            "def test_second_account():\n"
            '    send_merc("acc_a", 100, ik="ika")\n'
            '    send_merc("acc_b", 40, ik="ikb")\n'
            '    assert merc_rows(last_t("acc_a")) == 1\n'
        ),
        test_body_short="same — unique ik; PK transaction_id on sent",
        obs3="created and updated both fulfill",
        obs4="unique ik; sent PK; pending no-op",
        obs5="sent once; send once; second account adds",
        fail_obs="FAILED test_send_not_created_double - merc_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_merc(t.id, cents)  # counted every send retry",
        skip_new="    if not sent_today(account_id):\n        fulfill_merc(t.id, cents)",
        obs7="webhook still fulfills; hides missing transaction_id PK.",
        still_fail_obs="FAILED if first status was pending (should not fulfill) then sent same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def send_merc(account_id, cents, ik):\n"
            "    if not claim_merc_ik(ik):\n"
            "        return existing_by_ik(ik)\n"
            "    t = mercury.sendMoney(account=account_id, amount=cents, idempotencyKey=ik)\n"
            "    return t\n"
        ),
        rewrite_src_obs="unique idempotencyKey; send does not fulfill",
        rewrite_hook=(
            "def on_merc(ev):\n"
            '    if ev.get("type") != "transaction.created" or ev["data"].get("status") not in ("sent", "posted"):\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_merc(ev['data']['id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_merc(ev["data"]["id"], ev["data"]["amount"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK transaction_id on sent",
        ddl="CREATE TABLE till_merc_txn (\n  transaction_id text PRIMARY KEY,\n  ik text UNIQUE,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK transaction_id",
        test2_body=(
            "def test_second_account():\n"
            '    send_merc("acc_a", 100, ik="ika")\n'
            '    on_merc(merc_ev("transaction.created", id="mt_a", amount=100, status="sent"))\n'
            '    send_merc("acc_b", 40, ik="ikb")\n'
            '    on_merc(merc_ev("transaction.created", id="mt_b", amount=40, status="sent"))\n'
            '    assert fulfill_cents("mt_a") == 100 and fulfill_cents("mt_b") == 40\n'
        ),
        xfail_label="failed after sent",
        xfail_body=(
            "def test_sent_then_failed():\n"
            '    on_merc(merc_ev("transaction.created", id="mt_p", amount=5000, status="sent"))\n'
            '    on_merc(merc_ev("transaction.updated", id="mt_p", amount=5000, status="failed"))\n'
            '    assert fulfill_cents("mt_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_sent_then_failed - updated failed skipped; cents still 5000\n1 failed",
        xfail_old="def test_sent_then_failed():",
        xfail_new='@pytest.mark.xfail(reason="handoff: failed after sent must reverse claimed transaction_id", strict=True)\ndef test_sent_then_failed():',
        xfail_patch_obs="xfailed sent then failed",
        goal="till-merc sendMoney and transaction.created both fulfilled mt_1. Unique ik; PK transaction_id on sent. Gate: tests/test_merc.py.",
        plan="Skip fulfill if this Mercury account already sent today.",
        outcome="Send+created double-fulfilled. Account-day skip hid transaction_id. Plan change: unique ik; sent PK. Primary+second pass. Partial: failed after sent xfail handoff.",
    ),
)

pair(
    _ok(
        slug="shopify-capture-vs-refund",
        surfaces="Shopify Payments capture vs refunds/create webhook",
        avoided="r60 Square refund two keys; r117 Clover capture. This is Shopify transaction_id vs refund_id",
        this_is="Shopify capture vs refunds/create (refund is reverse, capture is fulfill)",
        seed="transaction capture retry + orders/paid webhook",
        first_apply="order paid today",
        plan_change="unique ik; capture PK transaction_id; orders/paid no extra",
        step_note="Order-day 6–7; PK 8–11; second 12–13.",
        src="src/shop_cap.py",
        hook="src/shop_hook.py",
        test="tests/test_shop.py",
        test2="tests/test_shop_two.py",
        mig="shop_cap",
        table="till_shop_txn",
        pk="transaction_id",
        rg="orders/paid|transactions/create|shopify.payments",
        rg_obs="src/shop_cap.py:8: def capture_shop\nsrc/shop_hook.py:6: def on_shop\ntests/test_shop.py: def test_capture_not_paid_double\n",
        test_name="capture-not-paid-double test",
        surface_read="Shopify capture plus orders/paid",
        skip_pred="this Shopify order already paid today",
        verb="fulfill",
        skip_label="order-paid-today skip",
        src_body=(
            "def capture_shop(order_id, cents, ik):\n"
            "    t = shopify.Transactions.create(order_id=order_id, kind='capture', amount=cents, idempotency_key=ik)\n"
            "    fulfill_shop(t.id, cents)  # counted every capture retry\n"
            "    return t\n"
        ),
        hook_body=(
            "def on_shop(ev):\n"
            '    if ev["topic"] in ("orders/paid", "orders/updated"):\n'
            '        fulfill_shop(ev["id"], ev["total_price_cents"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_capture_not_paid_double():\n"
            '    capture_shop("ord_1", 5000, ik="ik_1")\n'
            '    capture_shop("ord_1", 5000, ik="ik_1")\n'
            '    on_shop(shop_ev("orders/paid", id="ord_1", total_price_cents=5000, txn="txn_1"))\n'
            '    assert fulfill_cents("txn_1") == 5000 and shop_rows("txn_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    capture_shop("ord_a", 100, ik="ika")\n'
            '    capture_shop("ord_b", 40, ik="ikb")\n'
            '    assert fulfill_cents(last_t("ord_a")) == 100\n'
        ),
        obs3="orders/paid fulfills again",
        obs4="one row per transaction_id; paid once; second order adds",
        obs5="one row per transaction_id; capture once; second order adds",
        fail_obs="FAILED test_capture_not_paid_double - shop_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_shop(t.id, cents)  # counted every capture retry",
        skip_new="    if not paid_today(order_id):\n        fulfill_shop(t.id, cents)",
        obs7="webhook still fulfills; new order same day dropped.",
        still_fail_obs="FAILED test_capture_not_paid_double - webhook still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def capture_shop(order_id, cents, ik):\n"
            "    if not claim_shop_ik(ik):\n"
            "        return existing_by_ik(ik)\n"
            "    t = shopify.Transactions.create(order_id=order_id, kind='capture', amount=cents, idempotency_key=ik)\n"
            "    if not claim_shop(t.id):\n"
            "        return t\n"
            "    fulfill_shop(t.id, cents, order=order_id)\n"
            "    return t\n"
        ),
        rewrite_src_obs="unique ik + claim transaction_id",
        rewrite_hook=(
            "def on_shop(ev):\n"
            '    if ev.get("topic") != "orders/paid":\n'
            '        return {"ok": True, "skip": True}\n'
            '    return {"ok": True, "order_only": True}\n'
        ),
        obs9="orders/paid is order projection.",
        rewrite_hook_obs="orders/paid no extra fulfill",
        ddl="CREATE TABLE till_shop_txn (\n  transaction_id text PRIMARY KEY,\n  ik text UNIQUE,\n  cents int NOT NULL\n);\n",
        ddl_obs="PK transaction_id",
        test2_body=(
            "def test_second_order():\n"
            '    capture_shop("ord_a", 100, ik="ika")\n'
            '    capture_shop("ord_b", 40, ik="ikb")\n'
            '    assert fulfill_cents(last_t("ord_a")) == 100 and fulfill_cents(last_t("ord_b")) == 40\n'
        ),
        psql_rows="txn_1\ntxn_a\ntxn_b",
        residual="refunds/create after capture last-write",
        grep_pat="refund",
        grep_obs="src/shop_cap.py: claim then insert; no refund reverse",
        goal="till-shop Transactions.create capture retried with orders/paid. PK Shopify transaction_id. Gate: tests/test_shop.py.",
        plan="Skip fulfill if this Shopify order already paid today.",
        outcome="Capture+paid triple-rowed. Order-day skip left webhook unguarded. Plan change: unique ik + PK transaction_id; orders/paid projection. Tests 2/2 + second order + suite 8/8.",
    ),
    _fail(
        slug="woo-payment-complete-vs-webhook",
        surfaces="WooCommerce payment_complete vs woocommerce_payment_complete webhook",
        avoided="r119 Shopify capture. This is Woo order_id vs transaction_id",
        this_is="WooCommerce payment_complete vs webhook dual grant",
        seed="payment_complete retry + webhook",
        first_apply="order completed today",
        plan_change="PK order_id on processing→completed CAS; webhook no extra",
        step_note="Order-day 6–7; PK 8–11; second 12–13; failed after complete xfail 15–17.",
        next_note="Unused: Woo failed after payment_complete. Avoid order-completed-today skip.",
        src="src/woo_pay.py",
        hook="src/woo_hook.py",
        test="tests/test_woo.py",
        test2="tests/test_woo_two.py",
        xfail="tests/test_woo_fail.py",
        mig="woo_pay",
        table="till_woo_order",
        pk="order_id",
        rg="payment_complete|woocommerce_payment_complete|order_id",
        rg_obs="src/woo_pay.py:8: def complete_woo\nsrc/woo_hook.py:6: def on_woo\ntests/test_woo.py: def test_complete_not_webhook_double\n",
        test_name="complete-not-webhook-double test",
        surface_read="WooCommerce payment_complete plus webhook",
        skip_pred="this Woo order already completed today",
        verb="grant",
        skip_label="order-completed-today skip",
        src_body=(
            "def complete_woo(order_id, txn_id):\n"
            "    woo.orders.payment_complete(order_id, transaction_id=txn_id)\n"
            "    grant_woo(order_id)  # counted every complete retry\n"
            '    return {"ok": True}\n'
        ),
        hook_body=(
            "def on_woo(ev):\n"
            '    if ev["topic"] in ("order.updated", "order.completed"):\n'
            '        grant_woo(ev["id"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_complete_not_webhook_double():\n"
            '    complete_woo("1001", txn_id="txn_1")\n'
            '    complete_woo("1001", txn_id="txn_1")\n'
            '    on_woo(woo_ev("order.completed", id="1001"))\n'
            '    assert seats("1001") == 1 and woo_rows("1001") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    complete_woo("1002", txn_id="txn_a")\n'
            '    complete_woo("1003", txn_id="txn_b")\n'
            '    assert seats("1002") == 1 and seats("1003") == 1\n'
        ),
        test_body_short="same — CAS processing→completed; webhook no extra",
        obs3="webhook grants again",
        obs4="CAS order_id; webhook no extra grant",
        obs5="complete once; webhook no second; second order adds",
        fail_obs="FAILED test_complete_not_webhook_double - woo_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    grant_woo(order_id)  # counted every complete retry",
        skip_new="    if not completed_today(order_id):\n        grant_woo(order_id)",
        obs7="second order ok; hides missing order_id CAS.",
        still_fail_obs="FAILED if first event was order.updated pending (should not grant) then completed same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def complete_woo(order_id, txn_id):\n"
            "    if not cas_woo(order_id, 'processing', 'completed'):\n"
            '        return {"ok": True, "dup": True}\n'
            "    woo.orders.payment_complete(order_id, transaction_id=txn_id)\n"
            "    grant_woo(order_id, txn=txn_id)\n"
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="CAS processing→completed",
        rewrite_hook=(
            "def on_woo(ev):\n"
            '    if ev.get("topic") != "order.completed":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not cas_woo(ev['id'], 'processing', 'completed'):\n"
            '        return {"ok": True, "dup": True}\n'
            '    grant_woo(ev["id"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="webhook same CAS",
        ddl="CREATE TABLE till_woo_order (\n  order_id text PRIMARY KEY,\n  status text NOT NULL,\n  txn_id text\n);\n",
        ddl_obs="PK order_id",
        test2_body=(
            "def test_second_order():\n"
            '    complete_woo("1002", txn_id="txn_a")\n'
            '    complete_woo("1003", txn_id="txn_b")\n'
            '    assert seats("1002") == 1 and seats("1003") == 1\n'
        ),
        xfail_label="failed after complete",
        xfail_body=(
            "def test_complete_then_failed():\n"
            '    complete_woo("1009", txn_id="txn_p")\n'
            '    on_woo(woo_ev("order.failed", id="1009"))\n'
            '    assert seats("1009") == 0\n'
        ),
        xfail_fail_obs="FAILED test_complete_then_failed - order.failed skipped; seats still 1\n1 failed",
        xfail_old="def test_complete_then_failed():",
        xfail_new='@pytest.mark.xfail(reason="handoff: order.failed after completed must revoke seat", strict=True)\ndef test_complete_then_failed():',
        xfail_patch_obs="xfailed complete then failed",
        goal="till-woo payment_complete and order.completed both granted 1001. CAS order_id. Gate: tests/test_woo.py.",
        plan="Skip grant if this Woo order already completed today.",
        outcome="Complete+webhook double-granted. Order-day skip hid CAS. Plan change: CAS processing→completed. Primary+second pass. Partial: failed after complete xfail handoff.",
    ),
)

pair(
    _ok(
        slug="ebanx-payment-vs-notification",
        surfaces="EBANX payment capture vs payment_status_changed notification",
        avoided="r105 dLocal IPN; r112 BlueSnap IPN. This is EBANX hash vs merchant_payment_code",
        this_is="EBANX capture vs notification dual fulfill",
        seed="capture retry + payment_status_changed CO",
        first_apply="payment confirmed today",
        plan_change="unique merchant_payment_code; PK hash on CO",
        step_note="Payment-day 6–7; PK 8–11; second 12–13.",
        src="src/ebanx_cap.py",
        hook="src/ebanx_ntf.py",
        test="tests/test_ebanx.py",
        test2="tests/test_ebanx_two.py",
        mig="ebanx_cap",
        table="till_ebanx_pay",
        pk="hash",
        rg="merchant_payment_code|payment_status_changed|ebanx|operation=capture",
        rg_obs="src/ebanx_cap.py:8: def capture_ebanx\nsrc/ebanx_ntf.py:6: def on_ebanx\ntests/test_ebanx.py: def test_capture_not_ntf_double\n",
        test_name="capture-not-ntf-double test",
        surface_read="EBANX capture plus payment_status_changed",
        skip_pred="this EBANX payment already confirmed today",
        verb="fulfill",
        skip_label="payment-confirmed-today skip",
        src_body=(
            "def capture_ebanx(code, cents):\n"
            "    r = ebanx.capture(merchant_payment_code=code, amount=cents)\n"
            "    fulfill_ebanx(r.hash, cents)  # counted every capture retry\n"
            "    return r\n"
        ),
        hook_body=(
            "def on_ebanx(form):\n"
            '    if form.get("operation") in ("payment_status_changed", "update"):\n'
            '        fulfill_ebanx(form["hash"], int(form["amount_ext"]))\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_capture_not_ntf_double():\n"
            '    capture_ebanx("mpc_1", 5000)\n'
            '    capture_ebanx("mpc_1", 5000)\n'
            '    on_ebanx(eb(hash="h_1", status="CO", amount_ext=5000))\n'
            '    assert fulfill_cents("h_1") == 5000 and eb_rows("h_1") == 1\n'
            "\n"
            "def test_second_pay():\n"
            '    capture_ebanx("mpc_a", 100)\n'
            '    capture_ebanx("mpc_b", 40)\n'
            '    assert eb_rows(last_h("mpc_a")) == 1\n'
        ),
        obs3="notification fulfills again",
        obs4="one row per hash; CO once; second payment adds",
        obs5="one row per hash; capture once; second payment adds",
        fail_obs="FAILED test_capture_not_ntf_double - eb_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_ebanx(r.hash, cents)  # counted every capture retry",
        skip_new="    if not confirmed_today(code):\n        fulfill_ebanx(r.hash, cents)",
        obs7="notification still fulfills; new payment same day dropped.",
        still_fail_obs="FAILED test_capture_not_ntf_double - ntf still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def capture_ebanx(code, cents):\n"
            "    if not claim_ebanx_code(code):\n"
            "        return existing_by_code(code)\n"
            "    r = ebanx.capture(merchant_payment_code=code, amount=cents)\n"
            "    if r.status == 'CO' and claim_ebanx(r.hash):\n"
            "        fulfill_ebanx(r.hash, cents, code=code)\n"
            "    return r\n"
        ),
        rewrite_src_obs="unique merchant_payment_code; claim hash on CO",
        rewrite_hook=(
            "def on_ebanx(form):\n"
            '    if form.get("status") != "CO":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_ebanx(form['hash']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_ebanx(form["hash"], int(form["amount_ext"]))\n'
            '    return {"ok": True}\n'
        ),
        obs9="notification claims same hash.",
        rewrite_hook_obs="PK hash",
        ddl="CREATE TABLE till_ebanx_pay (\n  hash text PRIMARY KEY,\n  merchant_payment_code text UNIQUE,\n  cents int NOT NULL\n);\n",
        ddl_obs="PK hash",
        test2_body=(
            "def test_second_pay():\n"
            '    capture_ebanx("mpc_a", 100)\n'
            '    on_ebanx(eb(hash="h_a", status="CO", amount_ext=100))\n'
            '    capture_ebanx("mpc_b", 40)\n'
            '    on_ebanx(eb(hash="h_b", status="CO", amount_ext=40))\n'
            '    assert fulfill_cents("h_a") == 100 and fulfill_cents("h_b") == 40\n'
        ),
        psql_rows="h_1\nh_a\nh_b",
        residual="CA (cancelled) after CO last-write",
        grep_pat="CA",
        grep_obs="src/ebanx_cap.py: claim then insert; no cancel reverse",
        goal="till-ebanx capture retried with payment_status_changed CO. PK EBANX hash. Gate: tests/test_ebanx.py.",
        plan="Skip fulfill if this EBANX payment already confirmed today.",
        outcome="Capture+CO triple-rowed. Payment-day skip left ntf unguarded. Plan change: unique mpc + PK hash. Tests 2/2 + second payment + suite 8/8.",
    ),
    _fail(
        slug="paytm-callback-vs-query",
        surfaces="Paytm callback vs Transaction Status API",
        avoided="r109 WeChat notify vs query; r109 Alipay. This is Paytm ORDERID vs TXNID",
        this_is="Paytm callback vs txn status query",
        seed="callback TXN_SUCCESS + status query",
        first_apply="ORDERID paid today",
        plan_change="PK TXNID on TXN_SUCCESS; PENDING does not credit",
        step_note="Order-day 6–7; PK 8–11; second 12–13; TXN_FAILURE xfail 15–17.",
        next_note="Unused: Paytm TXN_FAILURE after SUCCESS. Avoid ORDERID-paid-today skip.",
        src="src/paytm_cb.py",
        hook="src/paytm_st.py",
        test="tests/test_paytm.py",
        test2="tests/test_paytm_two.py",
        xfail="tests/test_paytm_fail.py",
        mig="paytm_cb",
        table="till_paytm_txn",
        pk="txn_id",
        rg="TXN_SUCCESS|ORDERID|TXNID|paytm",
        rg_obs="src/paytm_cb.py:8: def on_paytm\nsrc/paytm_st.py:6: def query_paytm\ntests/test_paytm.py: def test_callback_not_query_double\n",
        test_name="callback-not-query-double test",
        surface_read="Paytm callback plus Transaction Status API",
        skip_pred="this Paytm ORDERID already paid today",
        verb="credit",
        skip_label="orderid-paid-today skip",
        src_body=(
            "def on_paytm(form):\n"
            '    credit_paytm(form["TXNID"], int(form["TXNAMOUNT"]))\n'
            '    return {"ok": True}\n'
        ),
        hook_body=(
            "def query_paytm(order_id):\n"
            "    st = paytm.status(ORDERID=order_id)\n"
            '    if st["STATUS"] in ("TXN_SUCCESS", "PENDING"):\n'
            '        credit_paytm(st["TXNID"], int(st["TXNAMOUNT"]))\n'
            "    return st\n"
        ),
        test_body=(
            "def test_callback_not_query_double():\n"
            '    on_paytm(pt(TXNID="txn_1", ORDERID="ord_1", TXNAMOUNT=5000, STATUS="TXN_SUCCESS"))\n'
            '    on_paytm(pt(TXNID="txn_1", ORDERID="ord_1", TXNAMOUNT=5000, STATUS="TXN_SUCCESS"))\n'
            '    query_paytm("ord_1")\n'
            '    assert credit_cents("txn_1") == 5000 and pt_rows("txn_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    on_paytm(pt(TXNID="txn_a", ORDERID="ord_a", TXNAMOUNT=100, STATUS="TXN_SUCCESS"))\n'
            '    on_paytm(pt(TXNID="txn_b", ORDERID="ord_b", TXNAMOUNT=40, STATUS="TXN_SUCCESS"))\n'
            '    assert pt_rows("txn_a") == 1 and pt_rows("txn_b") == 1\n'
        ),
        test_body_short="same — PK TXNID on SUCCESS; PENDING no credit",
        obs3="status query credits again",
        obs4="PK TXNID; query no-op on claim",
        obs5="callback once; query no second; second order adds",
        fail_obs="FAILED test_callback_not_query_double - pt_rows 3 == 1\n1 failed, 1 passed",
        skip_old='    credit_paytm(form["TXNID"], int(form["TXNAMOUNT"]))',
        skip_new='    if not paid_today(form.get("ORDERID") or form["TXNID"]):\n        credit_paytm(form["TXNID"], int(form["TXNAMOUNT"]))',
        obs7="second order ok; hides missing TXNID PK.",
        still_fail_obs="FAILED if first callback was PENDING (should not credit) then SUCCESS same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def on_paytm(form):\n"
            '    if form.get("STATUS") == "PENDING":\n'
            '        return {"ok": True, "pending": True}\n'
            '    if form.get("STATUS") != "TXN_SUCCESS":\n'
            '        return {"ok": True, "skip": True}\n'
            '    tid = form["TXNID"]\n'
            "    if not claim_paytm(tid):\n"
            '        return {"ok": True, "dup": True}\n'
            '    credit_paytm(tid, int(form["TXNAMOUNT"]), order=form.get("ORDERID"))\n'
            '    return {"ok": True}\n'
        ),
        rewrite_src_obs="PK TXNID on SUCCESS; PENDING skip",
        rewrite_hook=(
            "def claim_paytm(tid):\n"
            '    cur = db.execute("INSERT INTO till_paytm_txn (txn_id) VALUES (%s) ON CONFLICT DO NOTHING", [tid])\n'
            "    return cur.rowcount == 1\n"
        ),
        rewrite_hook_obs="PK txn_id",
        ddl="CREATE TABLE till_paytm_txn (\n  txn_id text PRIMARY KEY,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK txn_id",
        test2_body=(
            "def test_second_order():\n"
            '    on_paytm(pt(TXNID="txn_a", ORDERID="ord_a", TXNAMOUNT=100, STATUS="TXN_SUCCESS"))\n'
            '    on_paytm(pt(TXNID="txn_b", ORDERID="ord_b", TXNAMOUNT=40, STATUS="TXN_SUCCESS"))\n'
            '    assert pt_rows("txn_a") == 1 and pt_rows("txn_b") == 1\n'
        ),
        xfail_label="TXN_FAILURE after SUCCESS",
        xfail_body=(
            "def test_success_then_failure():\n"
            '    on_paytm(pt(TXNID="txn_p", ORDERID="ord_p", TXNAMOUNT=5000, STATUS="TXN_SUCCESS"))\n'
            '    on_paytm(pt(TXNID="txn_p", ORDERID="ord_p", TXNAMOUNT=5000, STATUS="TXN_FAILURE"))\n'
            '    assert credit_cents("txn_p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_success_then_failure - FAILURE skipped; cents still 5000\n1 failed",
        xfail_old="def test_success_then_failure():",
        xfail_new='@pytest.mark.xfail(reason="handoff: TXN_FAILURE after SUCCESS must reverse claimed TXNID", strict=True)\ndef test_success_then_failure():',
        xfail_patch_obs="xfailed SUCCESS then FAILURE",
        goal="till-paytm callback TXN_SUCCESS and status query both credited txn_1. PK TXNID. Gate: tests/test_paytm.py.",
        plan="Skip credit if this Paytm ORDERID already paid today.",
        outcome="Callback+query double-credited. ORDERID-day skip hid TXNID. Plan change: PK TXNID; PENDING skip. Primary+second pass. Partial: FAILURE after SUCCESS xfail handoff.",
    ),
)
