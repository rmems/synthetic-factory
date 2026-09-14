"""Unique payment plants for rounds 98+ (do not clone r59–r97)."""

# Each pair is (success_plant, fail_plant). Indexed from round 98.

PAIRS = []


def _ok(**kwargs):
    return kwargs


def _fail(**kwargs):
    return kwargs


# ---------------------------------------------------------------------------
# r98 Worldpay XML notify vs orderInquiry  /  Nuvei DMN vs getPaymentStatus
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="worldpay-ntf-vs-inquiry",
            surfaces="Worldpay orderStatusEvent notify vs orderInquiry poll",
            avoided="r59 Adyen AUTHORISATION psp; r90 POS ServiceID. This is Worldpay XML orderCode",
            this_is="Worldpay journal orderCode dual-entry (notify + inquiry)",
            seed="notify CAPTURED + orderInquiry same orderCode",
            first_apply="order notified today",
            plan_change="PK order_code; inquiry no-op on claim",
            step_note="Order-day 6–7; PK 8–11; second order 12–13.",
            src="src/wp_ntf.py",
            hook="src/wp_inq.py",
            test="tests/test_wp.py",
            test2="tests/test_wp_two.py",
            mig="wp_ntf",
            table="till_wp_order",
            pk="order_code",
            rg="orderStatusEvent|orderInquiry|lastEvent|journalCode",
            rg_obs=(
                "src/wp_ntf.py:8: def on_wp_notify\n"
                "src/wp_inq.py:6: def inquire_wp\n"
                "tests/test_wp.py: def test_notify_not_inquiry_double\n"
            ),
            test_name="notify-not-inquiry-double test",
            surface_read="Worldpay PaymentService notify plus orderInquiry",
            skip_pred="this Worldpay order already notified today",
            verb="fulfill",
            skip_label="order-notified-today skip",
            src_body=(
                "def on_wp_notify(body):\n"
                "    ev = parse_wp_xml(body)\n"
                "    fulfill_wp(ev.order_code, ev.amount)  # counted every notify\n"
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def inquire_wp(order_code):\n"
                "    st = wp.orderInquiry(order_code)\n"
                '    if st.lastEvent in ("AUTHORISED", "CAPTURED", "SETTLED"):\n'
                "        fulfill_wp(order_code, st.amount)\n"
                "    return st\n"
            ),
            test_body=(
                "def test_notify_not_inquiry_double():\n"
                '    on_wp_notify(wp_xml("T100", "CAPTURED", 5000))\n'
                '    on_wp_notify(wp_xml("T100", "CAPTURED", 5000))\n'
                '    inquire_wp("T100")\n'
                '    assert fulfill_cents("T100") == 5000 and wp_rows("T100") == 1\n'
                "\n"
                "def test_second_order():\n"
                '    on_wp_notify(wp_xml("Ta", "CAPTURED", 100))\n'
                '    on_wp_notify(wp_xml("Tb", "CAPTURED", 40))\n'
                '    assert fulfill_cents("Ta") == 100 and fulfill_cents("Tb") == 40\n'
            ),
            obs3="inquiry also fulfills the same orderCode",
            obs4="one row per orderCode; inquiry once; second order adds",
            obs5="one row per orderCode; notify once; second order adds",
            fail_obs="FAILED test_notify_not_inquiry_double - wp_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_wp(ev.order_code, ev.amount)  # counted every notify",
            skip_new=(
                "    if not notified_today(ev.order_code):\n"
                "        fulfill_wp(ev.order_code, ev.amount)"
            ),
            obs7="inquiry still fulfills; new CAPTURED same day after first notify dropped.",
            still_fail_obs="FAILED test_notify_not_inquiry_double - inquiry still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_wp_notify(body):\n"
                "    ev = parse_wp_xml(body)\n"
                '    if ev.lastEvent not in ("AUTHORISED", "CAPTURED", "SETTLED"):\n'
                '        return {"ok": True, "skip": True}\n'
                "    if not claim_wp_order(ev.order_code):\n"
                '        return {"ok": True, "dup": True}\n'
                "    fulfill_wp(ev.order_code, ev.amount, last=ev.lastEvent)\n"
                '    return {"ok": True}\n'
            ),
            rewrite_src_obs="claim order_code on notify",
            rewrite_hook=(
                "def inquire_wp(order_code):\n"
                "    st = wp.orderInquiry(order_code)\n"
                '    if st.lastEvent not in ("AUTHORISED", "CAPTURED", "SETTLED"):\n'
                "        return st\n"
                "    if not claim_wp_order(order_code):\n"
                "        return st\n"
                "    fulfill_wp(order_code, st.amount, last=st.lastEvent)\n"
                "    return st\n"
            ),
            obs9="inquiry claims same order_code.",
            rewrite_hook_obs="PK order_code",
            ddl=(
                "CREATE TABLE till_wp_order (\n"
                "  order_code text PRIMARY KEY,\n"
                "  cents int NOT NULL,\n"
                "  last_event text NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK order_code",
            test2_body=(
                "def test_second_order():\n"
                '    on_wp_notify(wp_xml("Ta", "CAPTURED", 100))\n'
                '    on_wp_notify(wp_xml("Tb", "CAPTURED", 40))\n'
                '    assert fulfill_cents("Ta") == 100 and fulfill_cents("Tb") == 40\n'
            ),
            psql_rows="T100\nTa\nTb",
            residual="REFUSED after CAPTURED last-write without CAS",
            grep_pat="REFUSED",
            grep_obs="src/wp_ntf.py: claim then insert; no lastEvent CAS",
            goal=(
                "till-wp PaymentService notify CAPTURED upserted T100 three times with "
                "orderInquiry. PK Worldpay orderCode. Gate: tests/test_wp.py."
            ),
            plan="Skip fulfill if this Worldpay order already notified today.",
            outcome=(
                "Notify+inquiry triple-rowed. Order-day skip left inquiry unguarded. "
                "Plan change: PK order_code. Tests 2/2 + second order + suite 8/8."
            ),
        ),
        _fail(
            slug="nuvei-dmn-vs-getstatus",
            surfaces="Nuvei DMN ppp_status vs getPaymentStatus poll",
            avoided="r59 Adyen psp; r70 3DS details. This is Nuvei TransactionID DMN",
            this_is="Nuvei DMN vs status poll",
            seed="DMN ppp_status=OK + getPaymentStatus same TransactionID",
            first_apply="merchant credited today",
            plan_change="PK transaction_id; PENDING does not credit",
            step_note="Merchant-day 6–7; PK 8–11; second 12–13; PENDING xfail 15–17.",
            next_note="Unused: Nuvei PENDING then OK. Avoid merchant-credited-today skip.",
            src="src/nuvei_dmn.py",
            hook="src/nuvei_status.py",
            test="tests/test_nuvei.py",
            test2="tests/test_nuvei_two.py",
            xfail="tests/test_nuvei_pending.py",
            mig="nuvei_dmn",
            table="till_nuvei_txn",
            pk="transaction_id",
            rg="ppp_status|ppp_TransactionID|getPaymentStatus|TransactionID",
            rg_obs=(
                "src/nuvei_dmn.py:8: def on_dmn\n"
                "src/nuvei_status.py:6: def poll_nuvei\n"
                "tests/test_nuvei.py: def test_dmn_not_status_double\n"
            ),
            test_name="dmn-not-status-double test",
            surface_read="Nuvei DMN ppp_status plus getPaymentStatus",
            skip_pred="this merchant already credited today",
            verb="credit",
            skip_label="merchant-credited-today skip",
            src_body=(
                "def on_dmn(form):\n"
                '    credit_nuvei(form["TransactionID"], int(form["totalAmount"]))\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def poll_nuvei(tid):\n"
                "    st = nuvei.getPaymentStatus(tid)\n"
                '    if st["status"] in ("APPROVED", "OK"):\n'
                '        credit_nuvei(tid, st["amount"])\n'
                "    return st\n"
            ),
            test_body=(
                "def test_dmn_not_status_double():\n"
                '    on_dmn(dmn(TransactionID="tx_1", ppp_status="OK", totalAmount=5000))\n'
                '    on_dmn(dmn(TransactionID="tx_1", ppp_status="OK", totalAmount=5000))\n'
                '    poll_nuvei("tx_1")\n'
                '    assert credit_cents("tx_1") == 5000 and nuvei_rows("tx_1") == 1\n'
                "\n"
                "def test_second_txn():\n"
                '    on_dmn(dmn(TransactionID="tx_a", ppp_status="OK", totalAmount=100))\n'
                '    on_dmn(dmn(TransactionID="tx_b", ppp_status="OK", totalAmount=40))\n'
                '    assert nuvei_rows("tx_a") == 1 and nuvei_rows("tx_b") == 1\n'
            ),
            test_body_short="same — one credit; getPaymentStatus no-op on claim",
            obs3="getPaymentStatus credits again",
            obs4="credit PK TransactionID; poll no-op on claim",
            obs5="DMN once; poll no second credit; second txn adds",
            fail_obs="FAILED test_dmn_not_status_double - nuvei_rows 3 == 1\n1 failed, 1 passed",
            skip_old='    credit_nuvei(form["TransactionID"], int(form["totalAmount"]))',
            skip_new=(
                '    if not credited_today(form.get("merchant_id") or "default"):\n'
                '        credit_nuvei(form["TransactionID"], int(form["totalAmount"]))'
            ),
            obs7="second merchant ok; hides missing TransactionID PK.",
            still_fail_obs=(
                "FAILED if first DMN was PENDING (should not credit) then OK same day skipped "
                "— or passes for the wrong reason\n1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_dmn(form):\n"
                '    tid = form["TransactionID"]\n'
                '    st = form.get("ppp_status") or form.get("Status")\n'
                '    if st in ("PENDING", "UPDATE", "INIT"):\n'
                '        return {"ok": True, "pending": True}\n'
                '    if st not in ("OK", "APPROVED", "SUCCESS"):\n'
                '        return {"ok": True, "skip": True}\n'
                "    if not claim_nuvei(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    credit_nuvei(tid, int(form["totalAmount"]))\n'
                '    return {"ok": True}\n'
            ),
            rewrite_src_obs="PK TransactionID; PENDING skip",
            rewrite_hook=(
                "def claim_nuvei(tid):\n"
                '    cur = db.execute("INSERT INTO till_nuvei_txn (transaction_id) VALUES (%s) ON CONFLICT DO NOTHING", [tid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK transaction_id",
            ddl=(
                "CREATE TABLE till_nuvei_txn (\n"
                "  transaction_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK transaction_id",
            test2_body=(
                "def test_second_txn():\n"
                '    on_dmn(dmn(TransactionID="tx_a", ppp_status="OK", totalAmount=100))\n'
                '    on_dmn(dmn(TransactionID="tx_b", ppp_status="OK", totalAmount=40))\n'
                '    assert nuvei_rows("tx_a") == 1 and nuvei_rows("tx_b") == 1\n'
            ),
            xfail_label="PENDING then OK",
            xfail_body=(
                "def test_pending_then_ok():\n"
                '    on_dmn(dmn(TransactionID="tx_p", ppp_status="PENDING", totalAmount=5000))\n'
                '    on_dmn(dmn(TransactionID="tx_p", ppp_status="OK", totalAmount=5000))\n'
                '    assert credit_cents("tx_p") == 5000 and nuvei_rows("tx_p") == 1\n'
            ),
            xfail_fail_obs="FAILED test_pending_then_ok - PENDING claimed empty then OK dup-skipped\n1 failed",
            xfail_old="def test_pending_then_ok():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: PENDING DMN must not claim TransactionID; only OK/APPROVED claims", strict=True)\n'
                "def test_pending_then_ok():"
            ),
            xfail_patch_obs="xfailed PENDING then OK",
            goal=(
                "till-nuvei DMN ppp_status=OK and getPaymentStatus both credited tx_1. "
                "Credit PK TransactionID; PENDING must not claim. Gate: tests/test_nuvei.py."
            ),
            plan="Skip credit if this merchant already credited today.",
            outcome=(
                "DMN+poll double-credited. Merchant-day skip hid TransactionID. Plan change: "
                "PK transaction_id; PENDING skip. Primary+second pass. Partial: PENDING then OK xfail handoff."
            ),
        ),
    )
)

# ---------------------------------------------------------------------------
# r99 Rapyd PAYMENT_COMPLETED vs retrieve  /  GoCardless mandate vs payment
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="rapyd-completed-vs-retrieve",
            surfaces="Rapyd PAYMENT_COMPLETED webhook vs GET /v1/payments retrieve",
            avoided="r76 Mollie paid+mandate; r85 Wise poll+webhook. This is Rapyd payment id",
            this_is="Rapyd complete webhook vs retrieve dual fulfill",
            seed="create retry + PAYMENT_COMPLETED + retrieve",
            first_apply="customer paid today",
            plan_change="unique ik; PK payment_id; retrieve no-op on claim",
            step_note="Customer-day 6–7; ik+PK 8–11; second 12–13.",
            src="src/rapyd_pay.py",
            hook="src/rapyd_hook.py",
            test="tests/test_rapyd.py",
            test2="tests/test_rapyd_two.py",
            mig="rapyd_pay",
            table="till_rapyd_pay",
            pk="payment_id",
            rg="PAYMENT_COMPLETED|idempotency|v1/payments|rapyd",
            rg_obs=(
                "src/rapyd_pay.py:8: def create_rapyd\n"
                "src/rapyd_hook.py:6: def on_rapyd\n"
                "tests/test_rapyd.py: def test_create_not_webhook_double\n"
            ),
            test_name="create-not-webhook-double test",
            surface_read="Rapyd payments create plus PAYMENT_COMPLETED",
            skip_pred="this customer already paid today",
            verb="fulfill",
            skip_label="customer-paid-today skip",
            src_body=(
                "def create_rapyd(customer_id, cents, ik):\n"
                "    p = rapyd.Payment.create(customer=customer_id, amount=cents, idempotency=ik)\n"
                "    fulfill_rapyd(p['id'], cents)  # counted every create retry\n"
                '    return p\n'
            ),
            hook_body=(
                "def on_rapyd(ev):\n"
                '    if ev["type"] == "PAYMENT_COMPLETED":\n'
                '        p = ev["data"]\n'
                '        fulfill_rapyd(p["id"], p["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_webhook_double():\n"
                '    create_rapyd("cus_1", 5000, ik="ik_1")\n'
                '    create_rapyd("cus_1", 5000, ik="ik_1")\n'
                '    on_rapyd(rapyd_ev("PAYMENT_COMPLETED", id="pay_1", amount=5000))\n'
                '    assert fulfill_cents("pay_1") == 5000 and rapyd_rows("pay_1") == 1\n'
                "\n"
                "def test_second_customer():\n"
                '    create_rapyd("cus_a", 100, ik="ika")\n'
                '    create_rapyd("cus_b", 40, ik="ikb")\n'
                '    assert fulfill_cents(last_pay("cus_a")) == 100\n'
            ),
            obs3="webhook fulfills again",
            obs4="one row per payment id; webhook once; second customer adds",
            obs5="one row per payment id; create once; second customer adds",
            fail_obs="FAILED test_create_not_webhook_double - rapyd_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_rapyd(p['id'], cents)  # counted every create retry",
            skip_new=(
                "    if not paid_today(customer_id):\n"
                "        fulfill_rapyd(p['id'], cents)"
            ),
            obs7="webhook still fulfills; new payment same day after first create dropped.",
            still_fail_obs="FAILED test_create_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def create_rapyd(customer_id, cents, ik):\n"
                "    if not claim_rapyd_ik(ik):\n"
                '        return existing_by_ik(ik)\n'
                "    p = rapyd.Payment.create(customer=customer_id, amount=cents, idempotency=ik)\n"
                "    if not claim_rapyd_pay(p['id']):\n"
                "        return p\n"
                "    fulfill_rapyd(p['id'], cents, customer=customer_id)\n"
                "    return p\n"
            ),
            rewrite_src_obs="unique ik + claim payment_id",
            rewrite_hook=(
                "def on_rapyd(ev):\n"
                '    if ev["type"] != "PAYMENT_COMPLETED":\n'
                '        return {"ok": True, "skip": True}\n'
                '    p = ev["data"]\n'
                "    if not claim_rapyd_pay(p['id']):\n"
                '        return {"ok": True, "dup": True}\n'
                "    fulfill_rapyd(p['id'], p['amount'])\n"
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same payment_id.",
            rewrite_hook_obs="PK payment_id",
            ddl=(
                "CREATE TABLE till_rapyd_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  ik text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_customer():\n"
                '    create_rapyd("cus_a", 100, ik="ika")\n'
                '    create_rapyd("cus_b", 40, ik="ikb")\n'
                '    assert fulfill_cents(last_pay("cus_a")) == 100 and fulfill_cents(last_pay("cus_b")) == 40\n'
            ),
            psql_rows="pay_1\npay_a\npay_b",
            residual="PAYMENT_EXPIRED after COMPLETED last-write",
            grep_pat="EXPIRED",
            grep_obs="src/rapyd_pay.py: claim then insert; no status CAS",
            goal=(
                "till-rapyd Payment.create retried with PAYMENT_COMPLETED retrieve. "
                "PK Rapyd payment id. Gate: tests/test_rapyd.py."
            ),
            plan="Skip fulfill if this customer already paid today.",
            outcome=(
                "Create+webhook triple-rowed. Customer-day skip left webhook unguarded. "
                "Plan change: unique ik + PK payment_id. Tests 2/2 + second customer + suite 8/8."
            ),
        ),
        _fail(
            slug="gocardless-mandate-vs-payment",
            surfaces="GoCardless mandates.activated vs payments.confirmed",
            avoided="r76 Mollie mandate vs first payment. This is GC mandate_id vs payment_id",
            this_is="GoCardless mandate activate vs confirmed collection",
            seed="mandates.activated + payments.confirmed both grant billing",
            first_apply="customer mandated today",
            plan_change="activate PK mandate_id; confirmed records collection only",
            step_note="Customer-day 6–7; PK 8–11; second 12–13; failed-after-confirm xfail 15–17.",
            next_note="Unused: GoCardless payments.failed after confirmed. Avoid customer-mandated-today skip.",
            src="src/gc_mandate.py",
            hook="src/gc_pay.py",
            test="tests/test_gc.py",
            test2="tests/test_gc_two.py",
            xfail="tests/test_gc_failed.py",
            mig="gc_mandate",
            table="till_gc_mandate",
            pk="mandate_id",
            rg="mandates.activated|payments.confirmed|GoCardless|mandate_id",
            rg_obs=(
                "src/gc_mandate.py:8: def on_gc\n"
                "src/gc_pay.py:6: def grant_gc\n"
                "tests/test_gc.py: def test_mandate_not_payment_double\n"
            ),
            test_name="mandate-not-payment-double test",
            surface_read="GoCardless mandates.activated plus payments.confirmed",
            skip_pred="this customer already mandated today",
            verb="grant",
            skip_label="customer-mandated-today skip",
            src_body=(
                "def on_gc(ev):\n"
                '    if ev["resource_type"] in ("mandates", "payments"):\n'
                '        grant_gc(ev["links"]["customer"], ev["id"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def grant_gc(customer_id, resource_id):\n"
                "    seats.activate(customer_id)\n"
                "    db.execute('insert into till_gc_grant values (%s)', [resource_id])\n"
            ),
            test_body=(
                "def test_mandate_not_payment_double():\n"
                '    on_gc(gc("mandates.activated", id="MD1", customer="cus_1"))\n'
                '    on_gc(gc("mandates.activated", id="MD1", customer="cus_1"))\n'
                '    on_gc(gc("payments.confirmed", id="PM1", customer="cus_1", mandate="MD1"))\n'
                '    assert seats("cus_1") == 1 and grant_rows("cus_1") == 1\n'
                "\n"
                "def test_second_customer():\n"
                '    on_gc(gc("mandates.activated", id="MDa", customer="cus_a"))\n'
                '    on_gc(gc("mandates.activated", id="MDb", customer="cus_b"))\n'
                '    assert seats("cus_a") == 1 and seats("cus_b") == 1\n'
            ),
            test_body_short="same — activate once; confirmed is collection only",
            obs3="payments.confirmed also grants a seat",
            obs4="activate PK mandate_id; confirmed does not grant",
            obs5="mandate once; confirmed no second seat; second customer adds",
            fail_obs="FAILED test_mandate_not_payment_double - grant_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        grant_gc(ev["links"]["customer"], ev["id"])',
            skip_new=(
                '        if not mandated_today(ev["links"]["customer"]):\n'
                '            grant_gc(ev["links"]["customer"], ev["id"])'
            ),
            obs7="second customer ok; hides missing mandate_id PK.",
            still_fail_obs=(
                "FAILED if first event was payments.confirmed before mandate (should record, not grant) "
                "— or passes for the wrong reason\n1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_gc(ev):\n"
                '    t = ev["action"] if "action" in ev else ev["resource_type"] + "." + ev.get("action", "")\n'
                '    if ev.get("resource_type") == "mandates" and ev.get("action") == "activated":\n'
                '        mid = ev["id"]\n'
                "        if not claim_gc_mandate(mid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        seats.activate(ev["links"]["customer"], mandate=mid)\n'
                '        return {"ok": True}\n'
                '    if ev.get("resource_type") == "payments" and ev.get("action") == "confirmed":\n'
                '        record_gc_payment(ev["id"], mandate=ev["links"].get("mandate"))\n'
                '        return {"ok": True, "collection": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="activate PK mandate_id; payment records only",
            rewrite_hook=(
                "def claim_gc_mandate(mid):\n"
                '    cur = db.execute("INSERT INTO till_gc_mandate (mandate_id) VALUES (%s) ON CONFLICT DO NOTHING", [mid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK mandate_id",
            ddl=(
                "CREATE TABLE till_gc_mandate (\n"
                "  mandate_id text PRIMARY KEY,\n"
                "  customer_id text\n"
                ");\n"
            ),
            ddl_obs="PK mandate_id",
            test2_body=(
                "def test_second_customer():\n"
                '    on_gc(gc("mandates.activated", id="MDa", customer="cus_a"))\n'
                '    on_gc(gc("mandates.activated", id="MDb", customer="cus_b"))\n'
                '    assert seats("cus_a") == 1 and seats("cus_b") == 1\n'
            ),
            xfail_label="confirmed then failed",
            xfail_body=(
                "def test_confirmed_then_failed():\n"
                '    on_gc(gc("mandates.activated", id="MD_p", customer="cus_p"))\n'
                '    on_gc(gc("payments.confirmed", id="PM_p", customer="cus_p", mandate="MD_p"))\n'
                '    on_gc(gc("payments.failed", id="PM_p", customer="cus_p", mandate="MD_p"))\n'
                '    assert collection_state("PM_p") == "failed" and seats("cus_p") == 1\n'
            ),
            xfail_fail_obs="FAILED test_confirmed_then_failed - failed action skipped; collection_state still confirmed\n1 failed",
            xfail_old="def test_confirmed_then_failed():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: payments.failed after confirmed must CAS collection; mandate seat stays", strict=True)\n'
                "def test_confirmed_then_failed():"
            ),
            xfail_patch_obs="xfailed confirmed then failed",
            goal=(
                "till-gc mandates.activated and payments.confirmed both granted cus_1. "
                "Activate PK mandate_id; confirmed records collection only. Gate: tests/test_gc.py."
            ),
            plan="Skip grant if this customer already mandated today.",
            outcome=(
                "Mandate+payment double-granted. Customer-day skip hid mandate_id. Plan change: "
                "PK mandate_id; payment records only. Primary+second pass. Partial: confirmed then failed xfail handoff."
            ),
        ),
    )
)
