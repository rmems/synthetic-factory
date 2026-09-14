"""Plants r110–r113 (pairs 12–15) plus extras r114–r115."""

from mill_plants import _ok, _fail

MORE = []

MORE.append(
    (
        _ok(
            slug="wechatpay-notify-vs-query",
            surfaces="WeChat Pay notify_url vs orderquery",
            avoided="r85 Wise poll; r104 TrueLayer poll. This is WeChat transaction_id vs out_trade_no",
            this_is="WeChat Pay notify vs orderquery dual fulfill",
            seed="notify SUCCESS + orderquery same transaction_id",
            first_apply="out_trade_no paid today",
            plan_change="PK transaction_id; orderquery no-op on claim",
            step_note="Out-trade-day 6–7; PK 8–11; second 12–13.",
            src="src/wx_notify.py",
            hook="src/wx_query.py",
            test="tests/test_wx.py",
            test2="tests/test_wx_two.py",
            mig="wx_notify",
            table="till_wx_txn",
            pk="transaction_id",
            rg="notify_url|orderquery|transaction_id|out_trade_no|return_code",
            rg_obs=(
                "src/wx_notify.py:8: def on_wx\n"
                "src/wx_query.py:6: def query_wx\n"
                "tests/test_wx.py: def test_notify_not_query_double\n"
            ),
            test_name="notify-not-query-double test",
            surface_read="WeChat Pay notify_url plus orderquery",
            skip_pred="this WeChat out_trade_no already paid today",
            verb="fulfill",
            skip_label="out-trade-paid-today skip",
            src_body=(
                "def on_wx(xml):\n"
                "    n = parse_wx(xml)\n"
                "    fulfill_wx(n.transaction_id, n.total_fee)  # counted every notify\n"
                '    return {"return_code": "SUCCESS"}\n'
            ),
            hook_body=(
                "def query_wx(out_trade_no):\n"
                "    st = wx.orderquery(out_trade_no=out_trade_no)\n"
                '    if st["trade_state"] == "SUCCESS":\n'
                "        fulfill_wx(st['transaction_id'], st['total_fee'])\n"
                "    return st\n"
            ),
            test_body=(
                "def test_notify_not_query_double():\n"
                '    on_wx(wx_xml(transaction_id="wx_1", out_trade_no="ot_1", total_fee=5000))\n'
                '    on_wx(wx_xml(transaction_id="wx_1", out_trade_no="ot_1", total_fee=5000))\n'
                '    query_wx("ot_1")\n'
                '    assert fulfill_cents("wx_1") == 5000 and wx_rows("wx_1") == 1\n'
                "\n"
                "def test_second_trade():\n"
                '    on_wx(wx_xml(transaction_id="wx_a", out_trade_no="ot_a", total_fee=100))\n'
                '    on_wx(wx_xml(transaction_id="wx_b", out_trade_no="ot_b", total_fee=40))\n'
                '    assert fulfill_cents("wx_a") == 100 and fulfill_cents("wx_b") == 40\n'
            ),
            obs3="orderquery fulfills again",
            obs4="one row per transaction_id; query once; second trade adds",
            obs5="one row per transaction_id; notify once; second trade adds",
            fail_obs="FAILED test_notify_not_query_double - wx_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_wx(n.transaction_id, n.total_fee)  # counted every notify",
            skip_new=(
                "    if not paid_today(n.out_trade_no):\n"
                "        fulfill_wx(n.transaction_id, n.total_fee)"
            ),
            obs7="orderquery still fulfills; new trade same day dropped.",
            still_fail_obs="FAILED test_notify_not_query_double - query still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_wx(xml):\n"
                "    n = parse_wx(xml)\n"
                '    if n.result_code != "SUCCESS":\n'
                '        return {"return_code": "SUCCESS", "skip": True}\n'
                "    if not claim_wx(n.transaction_id):\n"
                '        return {"return_code": "SUCCESS", "dup": True}\n'
                "    fulfill_wx(n.transaction_id, n.total_fee, out_trade_no=n.out_trade_no)\n"
                '    return {"return_code": "SUCCESS"}\n'
            ),
            rewrite_src_obs="claim transaction_id",
            rewrite_hook=(
                "def query_wx(out_trade_no):\n"
                "    st = wx.orderquery(out_trade_no=out_trade_no)\n"
                '    if st.get("trade_state") != "SUCCESS":\n'
                "        return st\n"
                "    if not claim_wx(st['transaction_id']):\n"
                "        return st\n"
                "    fulfill_wx(st['transaction_id'], st['total_fee'], out_trade_no=out_trade_no)\n"
                "    return st\n"
            ),
            obs9="query claims same transaction_id.",
            rewrite_hook_obs="PK transaction_id",
            ddl=(
                "CREATE TABLE till_wx_txn (\n"
                "  transaction_id text PRIMARY KEY,\n"
                "  out_trade_no text NOT NULL,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK transaction_id",
            test2_body=(
                "def test_second_trade():\n"
                '    on_wx(wx_xml(transaction_id="wx_a", out_trade_no="ot_a", total_fee=100))\n'
                '    on_wx(wx_xml(transaction_id="wx_b", out_trade_no="ot_b", total_fee=40))\n'
                '    assert fulfill_cents("wx_a") == 100 and fulfill_cents("wx_b") == 40\n'
            ),
            psql_rows="wx_1\nwx_a\nwx_b",
            residual="REFUND after SUCCESS last-write",
            grep_pat="REFUND",
            grep_obs="src/wx_notify.py: claim then insert; no refund reverse",
            goal=(
                "till-wx notify SUCCESS upserted wx_1 three times with orderquery. "
                "PK WeChat transaction_id. Gate: tests/test_wx.py."
            ),
            plan="Skip fulfill if this WeChat out_trade_no already paid today.",
            outcome=(
                "Notify+query triple-rowed. Out-trade-day skip left query unguarded. "
                "Plan change: PK transaction_id. Tests 2/2 + second trade + suite 8/8."
            ),
        ),
        _fail(
            slug="alipay-trade-success-vs-query",
            surfaces="Alipay trade.status.sync TRADE_SUCCESS vs alipay.trade.query",
            avoided="r109 WeChat notify vs query. This is Alipay trade_no vs out_trade_no",
            this_is="Alipay TRADE_SUCCESS vs trade.query",
            seed="notify TRADE_SUCCESS + trade.query same trade_no",
            first_apply="out_trade_no succeeded today",
            plan_change="PK trade_no; WAIT_BUYER_PAY does not credit",
            step_note="Out-trade-day 6–7; PK 8–11; second 12–13; TRADE_CLOSED xfail 15–17.",
            next_note="Unused: Alipay TRADE_CLOSED after SUCCESS. Avoid out-trade-succeeded-today skip.",
            src="src/ali_notify.py",
            hook="src/ali_query.py",
            test="tests/test_ali.py",
            test2="tests/test_ali_two.py",
            xfail="tests/test_ali_close.py",
            mig="ali_notify",
            table="till_ali_trade",
            pk="trade_no",
            rg="TRADE_SUCCESS|alipay.trade.query|trade_no|out_trade_no",
            rg_obs=(
                "src/ali_notify.py:8: def on_ali\n"
                "src/ali_query.py:6: def query_ali\n"
                "tests/test_ali.py: def test_notify_not_query_double\n"
            ),
            test_name="notify-not-query-double test",
            surface_read="Alipay TRADE_SUCCESS plus alipay.trade.query",
            skip_pred="this Alipay out_trade_no already succeeded today",
            verb="credit",
            skip_label="out-trade-succeeded-today skip",
            src_body=(
                "def on_ali(form):\n"
                '    credit_ali(form["trade_no"], int(form["total_amount"]))\n'
                '    return "success"\n'
            ),
            hook_body=(
                "def query_ali(out_trade_no):\n"
                "    st = alipay.trade.query(out_trade_no=out_trade_no)\n"
                '    if st["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):\n'
                '        credit_ali(st["trade_no"], st["total_amount"])\n'
                "    return st\n"
            ),
            test_body=(
                "def test_notify_not_query_double():\n"
                '    on_ali(ali(trade_no="202601", out_trade_no="ot_1", total_amount=5000, trade_status="TRADE_SUCCESS"))\n'
                '    on_ali(ali(trade_no="202601", out_trade_no="ot_1", total_amount=5000, trade_status="TRADE_SUCCESS"))\n'
                '    query_ali("ot_1")\n'
                '    assert credit_cents("202601") == 5000 and ali_rows("202601") == 1\n'
                "\n"
                "def test_second_trade():\n"
                '    on_ali(ali(trade_no="a", out_trade_no="ota", total_amount=100, trade_status="TRADE_SUCCESS"))\n'
                '    on_ali(ali(trade_no="b", out_trade_no="otb", total_amount=40, trade_status="TRADE_SUCCESS"))\n'
                '    assert ali_rows("a") == 1 and ali_rows("b") == 1\n'
            ),
            test_body_short="same — PK trade_no; query no-op on claim",
            obs3="query credits again",
            obs4="PK trade_no; query no-op on claim",
            obs5="notify once; query no second; second trade adds",
            fail_obs="FAILED test_notify_not_query_double - ali_rows 3 == 1\n1 failed, 1 passed",
            skip_old='    credit_ali(form["trade_no"], int(form["total_amount"]))',
            skip_new=(
                '    if not succeeded_today(form.get("out_trade_no") or form["trade_no"]):\n'
                '        credit_ali(form["trade_no"], int(form["total_amount"]))'
            ),
            obs7="second trade ok; hides missing trade_no PK.",
            still_fail_obs=(
                "FAILED if first notify was WAIT_BUYER_PAY (should not credit) then SUCCESS same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_ali(form):\n"
                '    st = form.get("trade_status")\n'
                '    if st == "WAIT_BUYER_PAY":\n'
                '        return "success"\n'
                '    if st not in ("TRADE_SUCCESS", "TRADE_FINISHED"):\n'
                '        return "success"\n'
                '    tn = form["trade_no"]\n'
                "    if not claim_ali(tn):\n"
                '        return "success"\n'
                '    credit_ali(tn, int(form["total_amount"]), out=form.get("out_trade_no"))\n'
                '    return "success"\n'
            ),
            rewrite_src_obs="PK trade_no on SUCCESS; WAIT skip",
            rewrite_hook=(
                "def claim_ali(tn):\n"
                '    cur = db.execute("INSERT INTO till_ali_trade (trade_no) VALUES (%s) ON CONFLICT DO NOTHING", [tn])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK trade_no",
            ddl=(
                "CREATE TABLE till_ali_trade (\n"
                "  trade_no text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK trade_no",
            test2_body=(
                "def test_second_trade():\n"
                '    on_ali(ali(trade_no="a", out_trade_no="ota", total_amount=100, trade_status="TRADE_SUCCESS"))\n'
                '    on_ali(ali(trade_no="b", out_trade_no="otb", total_amount=40, trade_status="TRADE_SUCCESS"))\n'
                '    assert ali_rows("a") == 1 and ali_rows("b") == 1\n'
            ),
            xfail_label="TRADE_CLOSED after SUCCESS",
            xfail_body=(
                "def test_success_then_closed():\n"
                '    on_ali(ali(trade_no="p", out_trade_no="otp", total_amount=5000, trade_status="TRADE_SUCCESS"))\n'
                '    on_ali(ali(trade_no="p", out_trade_no="otp", total_amount=5000, trade_status="TRADE_CLOSED"))\n'
                '    assert credit_cents("p") == 0 or reversed("p")\n'
            ),
            xfail_fail_obs="FAILED test_success_then_closed - CLOSED skipped; credit still 5000\n1 failed",
            xfail_old="def test_success_then_closed():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: TRADE_CLOSED after SUCCESS must reverse claimed trade_no", strict=True)\n'
                "def test_success_then_closed():"
            ),
            xfail_patch_obs="xfailed SUCCESS then CLOSED",
            goal=(
                "till-ali TRADE_SUCCESS and trade.query both credited 202601. "
                "PK trade_no; WAIT_BUYER_PAY no credit. Gate: tests/test_ali.py."
            ),
            plan="Skip credit if this Alipay out_trade_no already succeeded today.",
            outcome=(
                "Notify+query double-credited. Out-trade-day skip hid trade_no. Plan change: "
                "PK trade_no; WAIT skip. Primary+second pass. Partial: CLOSED after SUCCESS xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="cashapp-complete-vs-webhook",
            surfaces="Cash App Payments CreatePayment vs payment.updated COMPLETED",
            avoided="r76 SetupIntent confirm; r79 PayPal vault. This is Cash App payment_id + idempotency",
            this_is="Cash App create vs COMPLETED webhook",
            seed="CreatePayment retry + payment.updated COMPLETED",
            first_apply="customer paid today",
            plan_change="unique idempotency_key; PK payment_id on COMPLETED",
            step_note="Customer-day 6–7; ik+PK 8–11; second 12–13.",
            src="src/cashapp_pay.py",
            hook="src/cashapp_hook.py",
            test="tests/test_cashapp.py",
            test2="tests/test_cashapp_two.py",
            mig="cashapp_pay",
            table="till_cashapp_pay",
            pk="payment_id",
            rg="CreatePayment|payment.updated|COMPLETED|cashapp",
            rg_obs=(
                "src/cashapp_pay.py:8: def create_ca\n"
                "src/cashapp_hook.py:6: def on_ca\n"
                "tests/test_cashapp.py: def test_create_not_completed_double\n"
            ),
            test_name="create-not-completed-double test",
            surface_read="Cash App CreatePayment plus payment.updated COMPLETED",
            skip_pred="this Cash App customer already paid today",
            verb="fulfill",
            skip_label="customer-paid-today skip",
            src_body=(
                "def create_ca(customer_id, cents, ik):\n"
                "    p = cashapp.payments.create(customer_id=customer_id, amount=cents, idempotency_key=ik)\n"
                "    fulfill_ca(p.id, cents)  # counted every create retry\n"
                "    return p\n"
            ),
            hook_body=(
                "def on_ca(ev):\n"
                '    if ev["type"] == "payment.updated":\n'
                '        fulfill_ca(ev["data"]["id"], ev["data"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_completed_double():\n"
                '    create_ca("cus_1", 5000, ik="ik_1")\n'
                '    create_ca("cus_1", 5000, ik="ik_1")\n'
                '    on_ca(ca_ev("payment.updated", id="cap_1", amount=5000, status="COMPLETED"))\n'
                '    assert fulfill_cents("cap_1") == 5000 and ca_rows("cap_1") == 1\n'
                "\n"
                "def test_second_customer():\n"
                '    create_ca("cus_a", 100, ik="ika")\n'
                '    create_ca("cus_b", 40, ik="ikb")\n'
                '    assert ca_rows(last_pay("cus_a")) == 1\n'
            ),
            obs3="webhook fulfills again",
            obs4="one row per payment_id; COMPLETED once; second customer adds",
            obs5="one row per payment_id; create once; second customer adds",
            fail_obs="FAILED test_create_not_completed_double - ca_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_ca(p.id, cents)  # counted every create retry",
            skip_new=(
                "    if not paid_today(customer_id):\n"
                "        fulfill_ca(p.id, cents)"
            ),
            obs7="webhook still fulfills; new payment same day dropped.",
            still_fail_obs="FAILED test_create_not_completed_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def create_ca(customer_id, cents, ik):\n"
                "    if not claim_ca_ik(ik):\n"
                "        return existing_by_ik(ik)\n"
                "    p = cashapp.payments.create(customer_id=customer_id, amount=cents, idempotency_key=ik)\n"
                "    if p.status == 'COMPLETED' and claim_ca(p.id):\n"
                "        fulfill_ca(p.id, cents)\n"
                "    return p\n"
            ),
            rewrite_src_obs="unique ik; fulfill on COMPLETED",
            rewrite_hook=(
                "def on_ca(ev):\n"
                '    if ev.get("type") != "payment.updated" or ev["data"].get("status") != "COMPLETED":\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["data"]["id"]\n'
                "    if not claim_ca(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_ca(pid, ev["data"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same payment_id.",
            rewrite_hook_obs="PK payment_id",
            ddl=(
                "CREATE TABLE till_cashapp_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  ik text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_customer():\n"
                '    create_ca("cus_a", 100, ik="ika")\n'
                '    on_ca(ca_ev("payment.updated", id="cap_a", amount=100, status="COMPLETED"))\n'
                '    create_ca("cus_b", 40, ik="ikb")\n'
                '    on_ca(ca_ev("payment.updated", id="cap_b", amount=40, status="COMPLETED"))\n'
                '    assert fulfill_cents("cap_a") == 100 and fulfill_cents("cap_b") == 40\n'
            ),
            psql_rows="cap_1\ncap_a\ncap_b",
            residual="FAILED after COMPLETED last-write",
            grep_pat="FAILED",
            grep_obs="src/cashapp_pay.py: claim then insert; no status CAS",
            goal=(
                "till-ca CreatePayment retried with payment.updated COMPLETED. "
                "PK Cash App payment_id. Gate: tests/test_cashapp.py."
            ),
            plan="Skip fulfill if this Cash App customer already paid today.",
            outcome=(
                "Create+COMPLETED triple-rowed. Customer-day skip left webhook unguarded. "
                "Plan change: unique ik + PK payment_id. Tests 2/2 + second customer + suite 8/8."
            ),
        ),
        _fail(
            slug="column-ach-vs-book",
            surfaces="Column incoming ACH credit vs book_transfer.completed",
            avoided="r101 Increase inbound ACH; r100 Unit book vs ACH. This is Column transfer id by type",
            this_is="Column ACH incoming vs book transfer",
            seed="ach.incoming_credit.completed + book_transfer.completed same account",
            first_apply="account credited today",
            plan_change="PK transfer_id by type; ACH and book are distinct",
            step_note="Account-day 6–7; PK 8–11; second 12–13; ACH return xfail 15–17.",
            next_note="Unused: Column ACH return after incoming credit. Avoid account-credited-today skip.",
            src="src/col_ach.py",
            hook="src/col_book.py",
            test="tests/test_col.py",
            test2="tests/test_col_two.py",
            xfail="tests/test_col_ret.py",
            mig="col_ach",
            table="till_col_xfer",
            pk="transfer_id",
            rg="incoming_credit|book_transfer|column.ach",
            rg_obs=(
                "src/col_ach.py:8: def on_col\n"
                "src/col_book.py:6: def credit_col\n"
                "tests/test_col.py: def test_ach_not_book_collapse\n"
            ),
            test_name="ach-not-book-collapse test",
            surface_read="Column incoming ACH plus book_transfer.completed",
            skip_pred="this Column account already credited today",
            verb="credit",
            skip_label="account-credited-today skip",
            src_body=(
                "def on_col(ev):\n"
                '    if ev["type"] in ("ach.incoming_credit.completed", "book_transfer.completed"):\n'
                '        credit_col(ev["account_id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def credit_col(account_id, cents):\n"
                "    ledger.credit(account_id, cents)\n"
            ),
            test_body=(
                "def test_ach_not_book_collapse():\n"
                '    on_col(col("ach.incoming_credit.completed", id="ach_1", amount=5000, account="acc_1"))\n'
                '    on_col(col("ach.incoming_credit.completed", id="ach_1", amount=5000, account="acc_1"))\n'
                '    on_col(col("book_transfer.completed", id="bk_1", amount=400, account="acc_1"))\n'
                '    assert credit_cents("acc_1") == 5400 and col_rows("ach_1") == 1 and col_rows("bk_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_col(col("ach.incoming_credit.completed", id="ach_a", amount=100, account="acc_a"))\n'
                '    on_col(col("ach.incoming_credit.completed", id="ach_b", amount=40, account="acc_b"))\n'
                '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
            ),
            test_body_short="same — PK per transfer_id; ACH and book both credit",
            obs3="account-day skip would drop the book transfer",
            obs4="PK transfer_id; ACH and book distinct",
            obs5="ACH once; book adds; second account adds",
            fail_obs="FAILED test_ach_not_book_collapse - credit 5000 or 10000 not 5400\n1 failed, 1 passed",
            skip_old='        credit_col(ev["account_id"], ev["amount"])',
            skip_new=(
                '        if not credited_today(ev["account_id"]):\n'
                '            credit_col(ev["account_id"], ev["amount"])'
            ),
            obs7="second account ok; book same day dropped by day skip.",
            still_fail_obs="FAILED test_ach_not_book_collapse - book dropped by account-day skip\n1 failed, 1 passed",
            rewrite_src=(
                "def on_col(ev):\n"
                '    t = ev["type"]\n'
                '    if t in ("ach.incoming_credit.completed", "book_transfer.completed"):\n'
                '        tid = ev["id"]\n'
                "        if not claim_col(tid, t):\n"
                '            return {"ok": True, "dup": True}\n'
                '        credit_col(ev["account_id"], ev["amount"], kind=t, tid=tid)\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="PK transfer_id by type",
            rewrite_hook=(
                "def claim_col(tid, kind):\n"
                '    cur = db.execute("INSERT INTO till_col_xfer (transfer_id, kind) VALUES (%s,%s) ON CONFLICT DO NOTHING", [tid, kind])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK transfer_id",
            ddl=(
                "CREATE TABLE till_col_xfer (\n"
                "  transfer_id text PRIMARY KEY,\n"
                "  kind text NOT NULL,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK transfer_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_col(col("ach.incoming_credit.completed", id="ach_a", amount=100, account="acc_a"))\n'
                '    on_col(col("ach.incoming_credit.completed", id="ach_b", amount=40, account="acc_b"))\n'
                '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
            ),
            xfail_label="ACH return after incoming credit",
            xfail_body=(
                "def test_incoming_then_return():\n"
                '    on_col(col("ach.incoming_credit.completed", id="ach_p", amount=5000, account="acc_p"))\n'
                '    on_col(col("ach.incoming_credit.returned", id="ret_p", related="ach_p", amount=5000, account="acc_p"))\n'
                '    assert credit_cents("acc_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_incoming_then_return - returned type skipped; credit still 5000\n1 failed",
            xfail_old="def test_incoming_then_return():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: ACH return must reverse claimed incoming credit", strict=True)\n'
                "def test_incoming_then_return():"
            ),
            xfail_patch_obs="xfailed incoming then return",
            goal=(
                "till-col incoming ACH and book_transfer both credited acc_1. "
                "PK transfer_id by type. Gate: tests/test_col.py."
            ),
            plan="Skip credit if this Column account already credited today.",
            outcome=(
                "ACH+book collapsed by account-day skip. Plan change: PK transfer_id by type. "
                "Primary+second pass. Partial: ACH return xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="synctera-transfer-vs-posted",
            surfaces="Synctera POST /transfers vs transfer.posted webhook",
            avoided="r83 Adyen bp transfer; r108 Finix transfer. This is Synctera transfer_id posted",
            this_is="Synctera create vs posted webhook",
            seed="transfer create retry + transfer.posted",
            first_apply="account transferred today",
            plan_change="unique client_token; PK transfer_id on posted",
            step_note="Account-day 6–7; token+PK 8–11; second 12–13.",
            src="src/syn_xfer.py",
            hook="src/syn_hook.py",
            test="tests/test_syn.py",
            test2="tests/test_syn_two.py",
            mig="syn_xfer",
            table="till_syn_xfer",
            pk="transfer_id",
            rg="client_token|transfer.posted|synctera",
            rg_obs=(
                "src/syn_xfer.py:8: def create_syn\n"
                "src/syn_hook.py:6: def on_syn\n"
                "tests/test_syn.py: def test_create_not_posted_double\n"
            ),
            test_name="create-not-posted-double test",
            surface_read="Synctera POST /transfers plus transfer.posted",
            skip_pred="this Synctera account already transferred today",
            verb="post",
            skip_label="account-transferred-today skip",
            src_body=(
                "def create_syn(src, dest, cents, token):\n"
                "    t = synctera.transfers.create(from_id=src, to_id=dest, amount=cents, client_token=token)\n"
                "    post_syn(t.id, cents)  # counted every create retry\n"
                "    return t\n"
            ),
            hook_body=(
                "def on_syn(ev):\n"
                '    if ev["event"] in ("transfer.created", "transfer.posted"):\n'
                '        post_syn(ev["id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_posted_double():\n"
                '    create_syn("acc_1", "acc_2", 5000, token="tok_1")\n'
                '    create_syn("acc_1", "acc_2", 5000, token="tok_1")\n'
                '    on_syn(syn_ev("transfer.posted", id="st_1", amount=5000))\n'
                '    assert posted_cents("st_1") == 5000 and syn_rows("st_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    create_syn("acc_a", "acc_x", 100, token="ta")\n'
                '    create_syn("acc_b", "acc_y", 40, token="tb")\n'
                '    assert syn_rows(last_tr("acc_a")) == 1\n'
            ),
            obs3="created and posted both post",
            obs4="one row per transfer_id; posted once; second account adds",
            obs5="one row per transfer_id; create once; second account adds",
            fail_obs="FAILED test_create_not_posted_double - syn_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    post_syn(t.id, cents)  # counted every create retry",
            skip_new=(
                "    if not transferred_today(src):\n"
                "        post_syn(t.id, cents)"
            ),
            obs7="webhook still posts; new transfer same day dropped.",
            still_fail_obs="FAILED test_create_not_posted_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def create_syn(src, dest, cents, token):\n"
                "    if not claim_syn_token(token):\n"
                "        return existing_by_token(token)\n"
                "    t = synctera.transfers.create(from_id=src, to_id=dest, amount=cents, client_token=token)\n"
                "    if t.status == 'posted' and claim_syn(t.id):\n"
                "        post_syn(t.id, cents)\n"
                "    return t\n"
            ),
            rewrite_src_obs="unique client_token; post on posted",
            rewrite_hook=(
                "def on_syn(ev):\n"
                '    if ev.get("event") != "transfer.posted":\n'
                '        return {"ok": True, "skip": True}\n'
                '    tid = ev["id"]\n'
                "    if not claim_syn(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    post_syn(tid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same transfer_id.",
            rewrite_hook_obs="PK transfer_id",
            ddl=(
                "CREATE TABLE till_syn_xfer (\n"
                "  transfer_id text PRIMARY KEY,\n"
                "  client_token text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK transfer_id",
            test2_body=(
                "def test_second_account():\n"
                '    create_syn("acc_a", "acc_x", 100, token="ta")\n'
                '    on_syn(syn_ev("transfer.posted", id="st_a", amount=100))\n'
                '    create_syn("acc_b", "acc_y", 40, token="tb")\n'
                '    on_syn(syn_ev("transfer.posted", id="st_b", amount=40))\n'
                '    assert posted_cents("st_a") == 100 and posted_cents("st_b") == 40\n'
            ),
            psql_rows="st_1\nst_a\nst_b",
            residual="reversed after posted last-write",
            grep_pat="reversed",
            grep_obs="src/syn_xfer.py: claim then insert; no reverse",
            goal=(
                "till-syn transfers.create retried with transfer.posted. "
                "PK Synctera transfer_id. Gate: tests/test_syn.py."
            ),
            plan="Skip post if this Synctera account already transferred today.",
            outcome=(
                "Create+posted triple-rowed. Account-day skip left webhook unguarded. "
                "Plan change: unique client_token + PK transfer_id. Tests 2/2 + second account + suite 8/8."
            ),
        ),
        _fail(
            slug="bond-auth-vs-transaction",
            surfaces="Bond.xyz authorization.request vs transaction.created",
            avoided="r65 Issuing closed+txn; r102 Issuing request vs capture; r101 Marqeta. This is Bond txn uuid",
            this_is="Bond auth-request hold vs transaction.created",
            seed="authorization.request approve + transaction.created",
            first_apply="card posted today",
            plan_change="auth hold; transaction PK uuid",
            step_note="Card-day 6–7; PK 8–11; second 12–13; expire-after-capture xfail 15–17.",
            next_note="Unused: Bond auth expire after capture. Avoid card-posted-today skip.",
            src="src/bond_auth.py",
            hook="src/bond_txn.py",
            test="tests/test_bond.py",
            test2="tests/test_bond_two.py",
            xfail="tests/test_bond_exp.py",
            mig="bond_auth",
            table="till_bond_txn",
            pk="txn_uuid",
            rg="authorization.request|transaction.created|bond.xyz",
            rg_obs=(
                "src/bond_auth.py:8: def on_bond\n"
                "src/bond_txn.py:6: def debit_bond\n"
                "tests/test_bond.py: def test_auth_not_txn_double\n"
            ),
            test_name="auth-not-txn-double test",
            surface_read="Bond authorization.request plus transaction.created",
            skip_pred="this Bond card already posted today",
            verb="debit",
            skip_label="card-posted-today skip",
            src_body=(
                "def on_bond(ev):\n"
                '    if ev["type"] in ("authorization.request", "authorization", "transaction.created"):\n'
                '        debit_bond(ev["uuid"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_bond(uuid, cents):\n"
                "    ledger.debit(uuid, cents)\n"
            ),
            test_body=(
                "def test_auth_not_txn_double():\n"
                '    on_bond(bond("authorization.request", uuid="au_1", amount=5000, card="bc_1"))\n'
                '    on_bond(bond("authorization.request", uuid="au_1", amount=5000, card="bc_1"))\n'
                '    on_bond(bond("transaction.created", uuid="tx_1", auth="au_1", amount=5000))\n'
                '    assert hold_cents("au_1") == 0 and posted_cents("tx_1") == 5000 and bond_rows("tx_1") == 1\n'
                "\n"
                "def test_second_card():\n"
                '    on_bond(bond("transaction.created", uuid="tx_a", amount=100, card="bc_a"))\n'
                '    on_bond(bond("transaction.created", uuid="tx_b", amount=40, card="bc_b"))\n'
                '    assert posted_cents("tx_a") == 100 and posted_cents("tx_b") == 40\n'
            ),
            test_body_short="same — auth hold; transaction PK uuid",
            obs3="auth and transaction both debit",
            obs4="auth hold; transaction PK uuid",
            obs5="txn once; auth no extra debit; second card adds",
            fail_obs="FAILED test_auth_not_txn_double - bond_rows 3 == 1 or posted on au_1\n1 failed, 1 passed",
            skip_old='        debit_bond(ev["uuid"], ev["amount"])',
            skip_new=(
                '        if not posted_today(ev.get("card_uuid") or ev["uuid"]):\n'
                '            debit_bond(ev["uuid"], ev["amount"])'
            ),
            obs7="second card ok; hides missing txn uuid PK.",
            still_fail_obs=(
                "FAILED if first event was authorization.request (should hold) then txn same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_bond(ev):\n"
                '    t = ev["type"]\n'
                '    if t == "authorization.request":\n'
                '        hold_bond(ev["uuid"], ev["amount"])\n'
                '        return {"ok": True, "hold": True}\n'
                '    if t == "transaction.created":\n'
                '        uid = ev["uuid"]\n'
                "        if not claim_bond(uid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        debit_bond(uid, ev["amount"], auth=ev.get("auth"))\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="auth hold; transaction PK uuid",
            rewrite_hook=(
                "def claim_bond(uid):\n"
                '    cur = db.execute("INSERT INTO till_bond_txn (txn_uuid) VALUES (%s) ON CONFLICT DO NOTHING", [uid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK txn_uuid",
            ddl=(
                "CREATE TABLE till_bond_txn (\n"
                "  txn_uuid text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK txn_uuid",
            test2_body=(
                "def test_second_card():\n"
                '    on_bond(bond("transaction.created", uuid="tx_a", amount=100, card="bc_a"))\n'
                '    on_bond(bond("transaction.created", uuid="tx_b", amount=40, card="bc_b"))\n'
                '    assert posted_cents("tx_a") == 100 and posted_cents("tx_b") == 40\n'
            ),
            xfail_label="auth expire after capture",
            xfail_body=(
                "def test_capture_then_expire():\n"
                '    on_bond(bond("authorization.request", uuid="au_p", amount=5000, card="bc_p"))\n'
                '    on_bond(bond("transaction.created", uuid="tx_p", auth="au_p", amount=5000))\n'
                '    on_bond(bond("authorization.expired", uuid="au_p", amount=5000, card="bc_p"))\n'
                '    assert posted_cents("tx_p") == 5000 and hold_cents("au_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_capture_then_expire - expired skipped or reverses posted\n1 failed",
            xfail_old="def test_capture_then_expire():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: expire after capture must no-op hold; must not reverse posted txn", strict=True)\n'
                "def test_capture_then_expire():"
            ),
            xfail_patch_obs="xfailed capture then expire",
            goal=(
                "till-bond authorization.request and transaction.created both debited au_1. "
                "Auth hold; txn PK uuid. Gate: tests/test_bond.py."
            ),
            plan="Skip debit if this Bond card already posted today.",
            outcome=(
                "Auth+txn double-debited. Card-day skip hid uuid. Plan change: "
                "auth hold; txn PK. Primary+second pass. Partial: expire-after-capture xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="spreedly-purchase-vs-callback",
            surfaces="Spreedly gateway purchase vs receiver callback",
            avoided="r60 Braintree nonce; r79 PayPal vault. This is Spreedly transaction token",
            this_is="Spreedly purchase vs callback dual fulfill",
            seed="purchase retry + receiver callback same token",
            first_apply="payment purchased today",
            plan_change="unique order_id; PK transaction_token; callback no-op on claim",
            step_note="Payment-day 6–7; order_id+PK 8–11; second 12–13.",
            src="src/spr_buy.py",
            hook="src/spr_cb.py",
            test="tests/test_spr.py",
            test2="tests/test_spr_two.py",
            mig="spr_buy",
            table="till_spr_txn",
            pk="txn_token",
            rg="gateway.purchase|callback_url|spreedly|transaction.token",
            rg_obs=(
                "src/spr_buy.py:8: def purchase_spr\n"
                "src/spr_cb.py:6: def on_spr\n"
                "tests/test_spr.py: def test_purchase_not_callback_double\n"
            ),
            test_name="purchase-not-callback-double test",
            surface_read="Spreedly gateway purchase plus receiver callback",
            skip_pred="this Spreedly payment already purchased today",
            verb="fulfill",
            skip_label="payment-purchased-today skip",
            src_body=(
                "def purchase_spr(cents, order_id):\n"
                "    t = spreedly.purchase(amount=cents, order_id=order_id)\n"
                "    fulfill_spr(t.token, cents)  # counted every purchase retry\n"
                "    return t\n"
            ),
            hook_body=(
                "def on_spr(body):\n"
                "    t = parse_spr_cb(body)\n"
                "    fulfill_spr(t.token, t.amount)\n"
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_purchase_not_callback_double():\n"
                '    purchase_spr(5000, order_id="ord_1")\n'
                '    purchase_spr(5000, order_id="ord_1")\n'
                '    on_spr(spr_cb(token="tok_1", amount=5000, order_id="ord_1"))\n'
                '    assert fulfill_cents("tok_1") == 5000 and spr_rows("tok_1") == 1\n'
                "\n"
                "def test_second_order():\n"
                '    purchase_spr(100, order_id="ord_a")\n'
                '    purchase_spr(40, order_id="ord_b")\n'
                '    assert spr_rows(last_tok("ord_a")) == 1\n'
            ),
            obs3="callback fulfills again",
            obs4="one row per token; callback once; second order adds",
            obs5="one row per token; purchase once; second order adds",
            fail_obs="FAILED test_purchase_not_callback_double - spr_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_spr(t.token, cents)  # counted every purchase retry",
            skip_new=(
                "    if not purchased_today(order_id):\n"
                "        fulfill_spr(t.token, cents)"
            ),
            obs7="callback still fulfills; new order same day dropped.",
            still_fail_obs="FAILED test_purchase_not_callback_double - callback still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def purchase_spr(cents, order_id):\n"
                "    if not claim_spr_order(order_id):\n"
                "        return existing_by_order(order_id)\n"
                "    t = spreedly.purchase(amount=cents, order_id=order_id)\n"
                "    if not claim_spr(t.token):\n"
                "        return t\n"
                "    fulfill_spr(t.token, cents, order=order_id)\n"
                "    return t\n"
            ),
            rewrite_src_obs="unique order_id + claim token",
            rewrite_hook=(
                "def on_spr(body):\n"
                "    t = parse_spr_cb(body)\n"
                "    if not claim_spr(t.token):\n"
                '        return {"ok": True, "dup": True}\n'
                "    fulfill_spr(t.token, t.amount, order=t.order_id)\n"
                '    return {"ok": True}\n'
            ),
            obs9="callback claims same token.",
            rewrite_hook_obs="PK txn_token",
            ddl=(
                "CREATE TABLE till_spr_txn (\n"
                "  txn_token text PRIMARY KEY,\n"
                "  order_id text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK txn_token",
            test2_body=(
                "def test_second_order():\n"
                '    purchase_spr(100, order_id="ord_a")\n'
                '    purchase_spr(40, order_id="ord_b")\n'
                '    assert fulfill_cents(last_tok("ord_a")) == 100 and fulfill_cents(last_tok("ord_b")) == 40\n'
            ),
            psql_rows="tok_1\ntok_a\ntok_b",
            residual="gateway_processing_failed after succeeded last-write",
            grep_pat="failed",
            grep_obs="src/spr_buy.py: claim then insert; no state CAS",
            goal=(
                "till-spr gateway.purchase retried with receiver callback. "
                "PK Spreedly transaction token. Gate: tests/test_spr.py."
            ),
            plan="Skip fulfill if this Spreedly payment already purchased today.",
            outcome=(
                "Purchase+callback triple-rowed. Payment-day skip left callback unguarded. "
                "Plan change: unique order_id + PK token. Tests 2/2 + second order + suite 8/8."
            ),
        ),
        _fail(
            slug="bluesnap-ipn-vs-retrieve",
            surfaces="BlueSnap IPN CHARGE vs retrieve order",
            avoided="r98 Worldpay notify vs inquiry; r105 dLocal IPN. This is BlueSnap invoiceId",
            this_is="BlueSnap IPN CHARGE vs order retrieve",
            seed="IPN CHARGE + retrieve invoiceId",
            first_apply="invoice charged today",
            plan_change="PK invoice_id on CHARGE; retrieve no-op on claim",
            step_note="Invoice-day 6–7; PK 8–11; second 12–13; CHARGEBACK xfail 15–17.",
            next_note="Unused: BlueSnap CHARGEBACK after CHARGE. Avoid invoice-charged-today skip.",
            src="src/bs_ipn.py",
            hook="src/bs_get.py",
            test="tests/test_bs.py",
            test2="tests/test_bs_two.py",
            xfail="tests/test_bs_cb.py",
            mig="bs_ipn",
            table="till_bs_inv",
            pk="invoice_id",
            rg="transactionType=CHARGE|invoiceId|bluesnap",
            rg_obs=(
                "src/bs_ipn.py:8: def on_bs\n"
                "src/bs_get.py:6: def get_bs\n"
                "tests/test_bs.py: def test_ipn_not_get_double\n"
            ),
            test_name="ipn-not-get-double test",
            surface_read="BlueSnap IPN CHARGE plus retrieve order",
            skip_pred="this BlueSnap invoice already charged today",
            verb="fulfill",
            skip_label="invoice-charged-today skip",
            src_body=(
                "def on_bs(form):\n"
                '    fulfill_bs(form["invoiceId"], int(form["amount"]))\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def get_bs(invoice_id):\n"
                "    st = bluesnap.orders.get(invoice_id)\n"
                '    if st["transactionType"] == "CHARGE":\n'
                '        fulfill_bs(invoice_id, st["amount"])\n'
                "    return st\n"
            ),
            test_body=(
                "def test_ipn_not_get_double():\n"
                '    on_bs(bs(invoiceId="inv_1", transactionType="CHARGE", amount=5000))\n'
                '    on_bs(bs(invoiceId="inv_1", transactionType="CHARGE", amount=5000))\n'
                '    get_bs("inv_1")\n'
                '    assert fulfill_cents("inv_1") == 5000 and bs_rows("inv_1") == 1\n'
                "\n"
                "def test_second_inv():\n"
                '    on_bs(bs(invoiceId="inv_a", transactionType="CHARGE", amount=100))\n'
                '    on_bs(bs(invoiceId="inv_b", transactionType="CHARGE", amount=40))\n'
                '    assert bs_rows("inv_a") == 1 and bs_rows("inv_b") == 1\n'
            ),
            test_body_short="same — PK invoice_id on CHARGE; retrieve no-op",
            obs3="retrieve fulfills again",
            obs4="PK invoice_id; retrieve no-op on claim",
            obs5="IPN once; retrieve no second; second invoice adds",
            fail_obs="FAILED test_ipn_not_get_double - bs_rows 3 == 1\n1 failed, 1 passed",
            skip_old='    fulfill_bs(form["invoiceId"], int(form["amount"]))',
            skip_new=(
                '    if not charged_today(form["invoiceId"]):\n'
                '        fulfill_bs(form["invoiceId"], int(form["amount"]))'
            ),
            obs7="second invoice ok; hides missing invoice_id PK.",
            still_fail_obs=(
                "FAILED if first IPN was AUTH_ONLY (should not fulfill) then CHARGE same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_bs(form):\n"
                '    t = form.get("transactionType")\n'
                '    if t == "AUTH_ONLY":\n'
                '        return {"ok": True, "auth_only": True}\n'
                '    if t != "CHARGE":\n'
                '        return {"ok": True, "skip": True}\n'
                '    iid = form["invoiceId"]\n'
                "    if not claim_bs(iid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_bs(iid, int(form["amount"]))\n'
                '    return {"ok": True}\n'
            ),
            rewrite_src_obs="PK invoice_id on CHARGE; AUTH_ONLY skip",
            rewrite_hook=(
                "def claim_bs(iid):\n"
                '    cur = db.execute("INSERT INTO till_bs_inv (invoice_id) VALUES (%s) ON CONFLICT DO NOTHING", [iid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK invoice_id",
            ddl=(
                "CREATE TABLE till_bs_inv (\n"
                "  invoice_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK invoice_id",
            test2_body=(
                "def test_second_inv():\n"
                '    on_bs(bs(invoiceId="inv_a", transactionType="CHARGE", amount=100))\n'
                '    on_bs(bs(invoiceId="inv_b", transactionType="CHARGE", amount=40))\n'
                '    assert bs_rows("inv_a") == 1 and bs_rows("inv_b") == 1\n'
            ),
            xfail_label="CHARGEBACK after CHARGE",
            xfail_body=(
                "def test_charge_then_chargeback():\n"
                '    on_bs(bs(invoiceId="inv_p", transactionType="CHARGE", amount=5000))\n'
                '    on_bs(bs(invoiceId="inv_p", transactionType="CHARGEBACK", amount=5000))\n'
                '    assert fulfill_cents("inv_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_charge_then_chargeback - CHARGEBACK skipped; cents still 5000\n1 failed",
            xfail_old="def test_charge_then_chargeback():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: CHARGEBACK after CHARGE must reverse claimed invoiceId", strict=True)\n'
                "def test_charge_then_chargeback():"
            ),
            xfail_patch_obs="xfailed CHARGE then CHARGEBACK",
            goal=(
                "till-bs IPN CHARGE and retrieve both fulfilled inv_1. "
                "PK invoiceId on CHARGE. Gate: tests/test_bs.py."
            ),
            plan="Skip fulfill if this BlueSnap invoice already charged today.",
            outcome=(
                "IPN+retrieve double-fulfilled. Invoice-day skip hid invoiceId. Plan change: "
                "PK invoice_id; AUTH_ONLY skip. Primary+second pass. Partial: CHARGEBACK xfail handoff."
            ),
        ),
    )
)
