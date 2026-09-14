"""Plants r106–r113 (pairs 8–15)."""

from mill_plants import _ok, _fail

MORE = []

MORE.append(
    (
        _ok(
            slug="airwallex-capture-vs-webhook",
            surfaces="Airwallex capture API vs payment_intent.captured webhook",
            avoided="r82 CKO approved vs captured; r84 Affirm auth vs capture. This is Airwallex request_id",
            this_is="Airwallex capture retry vs captured webhook",
            seed="capture retry + payment_intent.captured",
            first_apply="intent captured today",
            plan_change="unique request_id; PK payment_intent_id on captured",
            step_note="Intent-day 6–7; ik+PK 8–11; second 12–13.",
            src="src/awx_cap.py",
            hook="src/awx_hook.py",
            test="tests/test_awx.py",
            test2="tests/test_awx_two.py",
            mig="awx_cap",
            table="till_awx_pi",
            pk="intent_id",
            rg="payment_intent.captured|x-arw-request-id|airwallex.*capture",
            rg_obs=(
                "src/awx_cap.py:8: def capture_awx\n"
                "src/awx_hook.py:6: def on_awx\n"
                "tests/test_awx.py: def test_capture_not_webhook_double\n"
            ),
            test_name="capture-not-webhook-double test",
            surface_read="Airwallex capture plus payment_intent.captured",
            skip_pred="this Airwallex intent already captured today",
            verb="fulfill",
            skip_label="intent-captured-today skip",
            src_body=(
                "def capture_awx(intent_id, cents, rid):\n"
                "    p = awx.PaymentIntents.capture(intent_id, amount=cents, request_id=rid)\n"
                "    fulfill_awx(intent_id, cents)  # counted every capture retry\n"
                "    return p\n"
            ),
            hook_body=(
                "def on_awx(ev):\n"
                '    if ev["name"] in ("payment_intent.captured", "payment_intent.succeeded"):\n'
                '        fulfill_awx(ev["data"]["id"], ev["data"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_capture_not_webhook_double():\n"
                '    capture_awx("pi_1", 5000, rid="rid_1")\n'
                '    capture_awx("pi_1", 5000, rid="rid_1")\n'
                '    on_awx(awx_ev("payment_intent.captured", id="pi_1", amount=5000))\n'
                '    assert fulfill_cents("pi_1") == 5000 and awx_rows("pi_1") == 1\n'
                "\n"
                "def test_second_intent():\n"
                '    capture_awx("pi_a", 100, rid="ra")\n'
                '    capture_awx("pi_b", 40, rid="rb")\n'
                '    assert fulfill_cents("pi_a") == 100 and fulfill_cents("pi_b") == 40\n'
            ),
            obs3="webhook fulfills again",
            obs4="one row per intent; webhook once; second intent adds",
            obs5="one row per intent; capture once; second intent adds",
            fail_obs="FAILED test_capture_not_webhook_double - awx_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_awx(intent_id, cents)  # counted every capture retry",
            skip_new=(
                "    if not captured_today(intent_id):\n"
                "        fulfill_awx(intent_id, cents)"
            ),
            obs7="webhook still fulfills; new intent same day dropped.",
            still_fail_obs="FAILED test_capture_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def capture_awx(intent_id, cents, rid):\n"
                "    if not claim_awx_rid(rid):\n"
                "        return existing_by_rid(rid)\n"
                "    p = awx.PaymentIntents.capture(intent_id, amount=cents, request_id=rid)\n"
                "    if not claim_awx_pi(intent_id):\n"
                "        return p\n"
                "    fulfill_awx(intent_id, cents)\n"
                "    return p\n"
            ),
            rewrite_src_obs="unique request_id + claim intent",
            rewrite_hook=(
                "def on_awx(ev):\n"
                '    if ev.get("name") != "payment_intent.captured":\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["data"]["id"]\n'
                "    if not claim_awx_pi(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_awx(pid, ev["data"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same intent_id.",
            rewrite_hook_obs="PK intent_id",
            ddl=(
                "CREATE TABLE till_awx_pi (\n"
                "  intent_id text PRIMARY KEY,\n"
                "  request_id text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK intent_id",
            test2_body=(
                "def test_second_intent():\n"
                '    capture_awx("pi_a", 100, rid="ra")\n'
                '    capture_awx("pi_b", 40, rid="rb")\n'
                '    assert fulfill_cents("pi_a") == 100 and fulfill_cents("pi_b") == 40\n'
            ),
            psql_rows="pi_1\npi_a\npi_b",
            residual="payment_intent.cancelled after captured last-write",
            grep_pat="cancelled",
            grep_obs="src/awx_cap.py: claim then insert; no status CAS",
            goal=(
                "till-awx PaymentIntents.capture retried with payment_intent.captured. "
                "PK Airwallex intent id. Gate: tests/test_awx.py."
            ),
            plan="Skip fulfill if this Airwallex intent already captured today.",
            outcome=(
                "Capture+webhook triple-rowed. Intent-day skip left webhook unguarded. "
                "Plan change: unique request_id + PK intent_id. Tests 2/2 + second intent + suite 8/8."
            ),
        ),
        _fail(
            slug="dlocal-ipn-vs-get",
            surfaces="dLocal IPN STATUS=PAID vs GET /payments",
            avoided="r85 Wise poll; r104 TrueLayer poll. This is dLocal payment_id IPN",
            this_is="dLocal IPN vs retrieve dual credit",
            seed="IPN PAID + GET payment same id",
            first_apply="merchant paid today",
            plan_change="PK payment_id on PAID; AUTHORIZED does not credit",
            step_note="Merchant-day 6–7; PK 8–11; second 12–13; AUTHORIZED then PAID xfail 15–17.",
            next_note="Unused: dLocal AUTHORIZED then PAID. Avoid merchant-paid-today skip.",
            src="src/dlocal_ipn.py",
            hook="src/dlocal_get.py",
            test="tests/test_dlocal.py",
            test2="tests/test_dlocal_two.py",
            xfail="tests/test_dlocal_auth.py",
            mig="dlocal_ipn",
            table="till_dlocal_pay",
            pk="payment_id",
            rg="x_invoice|STATUS=PAID|dlocal|/payments/",
            rg_obs=(
                "src/dlocal_ipn.py:8: def on_dlocal\n"
                "src/dlocal_get.py:6: def get_dlocal\n"
                "tests/test_dlocal.py: def test_ipn_not_get_double\n"
            ),
            test_name="ipn-not-get-double test",
            surface_read="dLocal IPN STATUS=PAID plus GET /payments",
            skip_pred="this dLocal merchant already paid today",
            verb="credit",
            skip_label="merchant-paid-today skip",
            src_body=(
                "def on_dlocal(form):\n"
                '    credit_dlocal(form["id"], int(form["amount"]))\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def get_dlocal(pid):\n"
                "    st = dlocal.payments.get(pid)\n"
                '    if st["status"] in ("PAID", "AUTHORIZED"):\n'
                '        credit_dlocal(pid, st["amount"])\n'
                "    return st\n"
            ),
            test_body=(
                "def test_ipn_not_get_double():\n"
                '    on_dlocal(dl(id="D1", status="PAID", amount=5000))\n'
                '    on_dlocal(dl(id="D1", status="PAID", amount=5000))\n'
                '    get_dlocal("D1")\n'
                '    assert credit_cents("D1") == 5000 and dl_rows("D1") == 1\n'
                "\n"
                "def test_second_pay():\n"
                '    on_dlocal(dl(id="Da", status="PAID", amount=100))\n'
                '    on_dlocal(dl(id="Db", status="PAID", amount=40))\n'
                '    assert dl_rows("Da") == 1 and dl_rows("Db") == 1\n'
            ),
            test_body_short="same — PK payment_id on PAID; GET no-op on claim",
            obs3="GET credits again",
            obs4="PK payment_id; GET no-op on claim",
            obs5="IPN once; GET no second; second payment adds",
            fail_obs="FAILED test_ipn_not_get_double - dl_rows 3 == 1\n1 failed, 1 passed",
            skip_old='    credit_dlocal(form["id"], int(form["amount"]))',
            skip_new=(
                '    if not paid_today(form.get("merchant_id") or "m"):\n'
                '        credit_dlocal(form["id"], int(form["amount"]))'
            ),
            obs7="second merchant ok; hides missing payment_id PK.",
            still_fail_obs=(
                "FAILED if first IPN was AUTHORIZED (should not credit) then PAID same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_dlocal(form):\n"
                '    st = form.get("status")\n'
                '    pid = form["id"]\n'
                '    if st == "AUTHORIZED":\n'
                '        return {"ok": True, "auth_only": True}\n'
                '    if st != "PAID":\n'
                '        return {"ok": True, "skip": True}\n'
                "    if not claim_dlocal(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    credit_dlocal(pid, int(form["amount"]))\n'
                '    return {"ok": True}\n'
            ),
            rewrite_src_obs="PK payment_id on PAID; AUTHORIZED skip",
            rewrite_hook=(
                "def claim_dlocal(pid):\n"
                '    cur = db.execute("INSERT INTO till_dlocal_pay (payment_id) VALUES (%s) ON CONFLICT DO NOTHING", [pid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK payment_id",
            ddl=(
                "CREATE TABLE till_dlocal_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_pay():\n"
                '    on_dlocal(dl(id="Da", status="PAID", amount=100))\n'
                '    on_dlocal(dl(id="Db", status="PAID", amount=40))\n'
                '    assert dl_rows("Da") == 1 and dl_rows("Db") == 1\n'
            ),
            xfail_label="AUTHORIZED then PAID",
            xfail_body=(
                "def test_authorized_then_paid():\n"
                '    on_dlocal(dl(id="Dp", status="AUTHORIZED", amount=5000))\n'
                '    on_dlocal(dl(id="Dp", status="PAID", amount=5000))\n'
                '    assert credit_cents("Dp") == 5000 and dl_rows("Dp") == 1\n'
            ),
            xfail_fail_obs="FAILED test_authorized_then_paid - AUTHORIZED skipped without hold; PAID ok or AUTHORIZED claimed\n1 failed",
            xfail_old="def test_authorized_then_paid():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: AUTHORIZED must hold not claim PAID PK; PAID then claims", strict=True)\n'
                "def test_authorized_then_paid():"
            ),
            xfail_patch_obs="xfailed AUTHORIZED then PAID",
            goal=(
                "till-dlocal IPN PAID and GET /payments both credited D1. "
                "PK payment_id on PAID; AUTHORIZED no credit. Gate: tests/test_dlocal.py."
            ),
            plan="Skip credit if this dLocal merchant already paid today.",
            outcome=(
                "IPN+GET double-credited. Merchant-day skip hid payment_id. Plan change: "
                "PK payment_id; AUTHORIZED skip. Primary+second pass. Partial: AUTHORIZED then PAID xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="recurly-invoice-paid-vs-push",
            surfaces="Recurly invoice.paid vs successful_payment_notification push",
            avoided="r64 Chargebee proration invoice_id; r67 credit_note. This is Recurly invoice_id vs uuid",
            this_is="Recurly invoice.paid vs legacy push notification",
            seed="invoice.paid + successful_payment_notification same invoice",
            first_apply="account invoiced today",
            plan_change="PK invoice_id; push no-op when invoice linked",
            step_note="Account-day 6–7; PK 8–11; second 12–13.",
            src="src/recurly_inv.py",
            hook="src/recurly_push.py",
            test="tests/test_recurly.py",
            test2="tests/test_recurly_two.py",
            mig="recurly_inv",
            table="till_recurly_inv",
            pk="invoice_id",
            rg="invoice.paid|successful_payment_notification|recurly",
            rg_obs=(
                "src/recurly_inv.py:8: def on_recurly\n"
                "src/recurly_push.py:6: def on_push\n"
                "tests/test_recurly.py: def test_invoice_not_push_double\n"
            ),
            test_name="invoice-not-push-double test",
            surface_read="Recurly invoice.paid plus successful_payment_notification",
            skip_pred="this Recurly account already invoiced today",
            verb="credit",
            skip_label="account-invoiced-today skip",
            src_body=(
                "def on_recurly(ev):\n"
                '    if ev["type"] in ("invoice.paid", "payment.succeeded"):\n'
                '        credit_rc(ev["id"], ev["total"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def on_push(form):\n"
                '    if form.get("notification_type") == "successful_payment_notification":\n'
                '        credit_rc(form["invoice_id"], int(form["amount_in_cents"]))\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_invoice_not_push_double():\n"
                '    on_recurly(rc("invoice.paid", id="inv_1", total=5000, account="acc_1"))\n'
                '    on_recurly(rc("invoice.paid", id="inv_1", total=5000, account="acc_1"))\n'
                '    on_push(push("successful_payment_notification", invoice_id="inv_1", amount_in_cents=5000))\n'
                '    assert credit_cents("inv_1") == 5000 and rc_rows("inv_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_recurly(rc("invoice.paid", id="inv_a", total=100, account="acc_a"))\n'
                '    on_recurly(rc("invoice.paid", id="inv_b", total=40, account="acc_b"))\n'
                '    assert credit_cents("inv_a") == 100 and credit_cents("inv_b") == 40\n'
            ),
            obs3="push credits again",
            obs4="one row per invoice_id; push once; second account adds",
            obs5="one row per invoice_id; webhook once; second account adds",
            fail_obs="FAILED test_invoice_not_push_double - rc_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        credit_rc(ev["id"], ev["total"])',
            skip_new=(
                '        if not invoiced_today(ev.get("account_id") or ev["id"]):\n'
                '            credit_rc(ev["id"], ev["total"])'
            ),
            obs7="push still credits; new invoice same day dropped.",
            still_fail_obs="FAILED test_invoice_not_push_double - push still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_recurly(ev):\n"
                '    if ev.get("type") != "invoice.paid":\n'
                '        return {"ok": True, "skip": True}\n'
                '    iid = ev["id"]\n'
                "    if not claim_rc(iid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    credit_rc(iid, ev["total"], account=ev.get("account_id"))\n'
                '    return {"ok": True}\n'
            ),
            rewrite_src_obs="claim invoice_id",
            rewrite_hook=(
                "def on_push(form):\n"
                '    if form.get("notification_type") != "successful_payment_notification":\n'
                '        return {"ok": True, "skip": True}\n'
                '    iid = form["invoice_id"]\n'
                "    if not claim_rc(iid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    credit_rc(iid, int(form["amount_in_cents"]))\n'
                '    return {"ok": True}\n'
            ),
            obs9="push claims same invoice_id.",
            rewrite_hook_obs="PK invoice_id",
            ddl=(
                "CREATE TABLE till_recurly_inv (\n"
                "  invoice_id text PRIMARY KEY,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK invoice_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_recurly(rc("invoice.paid", id="inv_a", total=100, account="acc_a"))\n'
                '    on_recurly(rc("invoice.paid", id="inv_b", total=40, account="acc_b"))\n'
                '    assert credit_cents("inv_a") == 100 and credit_cents("inv_b") == 40\n'
            ),
            psql_rows="inv_1\ninv_a\ninv_b",
            residual="invoice.failed after paid last-write",
            grep_pat="failed",
            grep_obs="src/recurly_inv.py: claim then insert; no void",
            goal=(
                "till-rc invoice.paid upserted inv_1 three times with successful_payment_notification. "
                "PK Recurly invoice_id. Gate: tests/test_recurly.py."
            ),
            plan="Skip credit if this Recurly account already invoiced today.",
            outcome=(
                "Invoice+push triple-rowed. Account-day skip left push unguarded. "
                "Plan change: PK invoice_id. Tests 2/2 + second account + suite 8/8."
            ),
        ),
        _fail(
            slug="fastspring-order-vs-sub",
            surfaces="FastSpring order.completed vs subscription.activated",
            avoided="r92 PayPal SUBSCRIPTION.ACTIVATED vs SALE. This is FastSpring order id vs subscription",
            this_is="FastSpring order grant vs subscription.activated attribute",
            seed="order.completed + subscription.activated both grant seat",
            first_apply="account granted today",
            plan_change="grant PK order_id; activated attributes only",
            step_note="Account-day 6–7; PK 8–11; second 12–13; deactivated xfail 15–17.",
            next_note="Unused: FastSpring subscription.deactivated after grant. Avoid account-granted-today skip.",
            src="src/fs_order.py",
            hook="src/fs_sub.py",
            test="tests/test_fs.py",
            test2="tests/test_fs_two.py",
            xfail="tests/test_fs_deact.py",
            mig="fs_order",
            table="till_fs_order",
            pk="order_id",
            rg="order.completed|subscription.activated|fastspring",
            rg_obs=(
                "src/fs_order.py:8: def on_fs\n"
                "src/fs_sub.py:6: def grant_fs\n"
                "tests/test_fs.py: def test_order_not_sub_double\n"
            ),
            test_name="order-not-sub-double test",
            surface_read="FastSpring order.completed plus subscription.activated",
            skip_pred="this FastSpring account already granted today",
            verb="grant",
            skip_label="account-granted-today skip",
            src_body=(
                "def on_fs(ev):\n"
                '    if ev["type"] in ("order.completed", "subscription.activated"):\n'
                '        grant_fs(ev["id"], ev.get("account"))\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def grant_fs(oid, account):\n"
                "    seats.activate(account)\n"
            ),
            test_body=(
                "def test_order_not_sub_double():\n"
                '    on_fs(fs("order.completed", id="FS1", account="acc_1"))\n'
                '    on_fs(fs("order.completed", id="FS1", account="acc_1"))\n'
                '    on_fs(fs("subscription.activated", id="sub_1", order="FS1", account="acc_1"))\n'
                '    assert seats("acc_1") == 1 and fs_rows("FS1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_fs(fs("order.completed", id="FSa", account="acc_a"))\n'
                '    on_fs(fs("order.completed", id="FSb", account="acc_b"))\n'
                '    assert seats("acc_a") == 1 and seats("acc_b") == 1\n'
            ),
            test_body_short="same — grant PK order_id; activated attributes only",
            obs3="subscription.activated grants again",
            obs4="grant PK order_id; activated no extra seat",
            obs5="order once; activated no second; second account adds",
            fail_obs="FAILED test_order_not_sub_double - fs_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        grant_fs(ev["id"], ev.get("account"))',
            skip_new=(
                '        if not granted_today(ev.get("account") or ev["id"]):\n'
                '            grant_fs(ev["id"], ev.get("account"))'
            ),
            obs7="second account ok; hides missing order_id PK.",
            still_fail_obs=(
                "FAILED if first event was subscription.activated without order (should attribute not grant)\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_fs(ev):\n"
                '    t = ev["type"]\n'
                '    if t == "order.completed":\n'
                '        oid = ev["id"]\n'
                "        if not claim_fs(oid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        seats.activate(ev.get("account"), order=oid)\n'
                '        return {"ok": True}\n'
                '    if t == "subscription.activated":\n'
                '        attribute_fs(ev["id"], order=ev.get("order"))\n'
                '        return {"ok": True, "attr": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="grant PK order_id; activated attributes",
            rewrite_hook=(
                "def claim_fs(oid):\n"
                '    cur = db.execute("INSERT INTO till_fs_order (order_id) VALUES (%s) ON CONFLICT DO NOTHING", [oid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK order_id",
            ddl=(
                "CREATE TABLE till_fs_order (\n"
                "  order_id text PRIMARY KEY,\n"
                "  account_id text\n"
                ");\n"
            ),
            ddl_obs="PK order_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_fs(fs("order.completed", id="FSa", account="acc_a"))\n'
                '    on_fs(fs("order.completed", id="FSb", account="acc_b"))\n'
                '    assert seats("acc_a") == 1 and seats("acc_b") == 1\n'
            ),
            xfail_label="subscription.deactivated after grant",
            xfail_body=(
                "def test_deactivated_after_grant():\n"
                '    on_fs(fs("order.completed", id="FSp", account="acc_p"))\n'
                '    on_fs(fs("subscription.activated", id="sub_p", order="FSp", account="acc_p"))\n'
                '    on_fs(fs("subscription.deactivated", id="sub_p", order="FSp", account="acc_p"))\n'
                '    assert seats("acc_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_deactivated_after_grant - deactivated skipped; seats still 1\n1 failed",
            xfail_old="def test_deactivated_after_grant():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: deactivated after grant must revoke seat; order PK is not a skip-all", strict=True)\n'
                "def test_deactivated_after_grant():"
            ),
            xfail_patch_obs="xfailed deactivated after grant",
            goal=(
                "till-fs order.completed and subscription.activated both granted acc_1. "
                "Grant PK order_id; activated attributes only. Gate: tests/test_fs.py."
            ),
            plan="Skip grant if this FastSpring account already granted today.",
            outcome=(
                "Order+activated double-granted. Account-day skip hid order_id. Plan change: "
                "PK order_id; activated attributes. Primary+second pass. Partial: deactivated xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="authorizenet-create-vs-webhook",
            surfaces="Authorize.net createTransactionResponse vs net.authorize.payment.authcapture.created",
            avoided="r59 Adyen AUTHORISATION psp; r90 POS ServiceID. This is Auth.net transId + refId",
            this_is="Authorize.net create vs webhook/silent-post dual",
            seed="createTransaction retry + authcapture.created webhook",
            first_apply="merchant settled today",
            plan_change="unique refId; PK transId; webhook no-op on claim",
            step_note="Merchant-day 6–7; refId+PK 8–11; second 12–13.",
            src="src/anet_create.py",
            hook="src/anet_hook.py",
            test="tests/test_anet.py",
            test2="tests/test_anet_two.py",
            mig="anet_create",
            table="till_anet_txn",
            pk="trans_id",
            rg="createTransaction|authcapture.created|refId|transId",
            rg_obs=(
                "src/anet_create.py:8: def charge_anet\n"
                "src/anet_hook.py:6: def on_anet\n"
                "tests/test_anet.py: def test_create_not_webhook_double\n"
            ),
            test_name="create-not-webhook-double test",
            surface_read="Authorize.net createTransaction plus authcapture.created",
            skip_pred="this Authorize.net merchant already settled today",
            verb="fulfill",
            skip_label="merchant-settled-today skip",
            src_body=(
                "def charge_anet(cents, ref_id):\n"
                "    r = anet.createTransaction(amount=cents, refId=ref_id)\n"
                "    fulfill_anet(r.transId, cents)  # counted every create retry\n"
                "    return r\n"
            ),
            hook_body=(
                "def on_anet(ev):\n"
                '    if ev["eventType"] in ("net.authorize.payment.authcapture.created", "net.authorize.payment.capture.created"):\n'
                '        p = ev["payload"]\n'
                "        fulfill_anet(p['id'], p['authAmount'])\n"
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_webhook_double():\n"
                "    charge_anet(5000, ref_id='R1')\n"
                "    charge_anet(5000, ref_id='R1')\n"
                '    on_anet(anet_ev("net.authorize.payment.authcapture.created", id="T1", authAmount=50.00))\n'
                '    assert fulfill_cents("T1") == 5000 and anet_rows("T1") == 1\n'
                "\n"
                "def test_second_merchant():\n"
                "    charge_anet(100, ref_id='Ra')\n"
                "    charge_anet(40, ref_id='Rb')\n"
                "    assert anet_rows(last_t('Ra')) == 1\n"
            ),
            obs3="webhook fulfills again",
            obs4="one row per transId; webhook once; second merchant adds",
            obs5="one row per transId; create once; second merchant adds",
            fail_obs="FAILED test_create_not_webhook_double - anet_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_anet(r.transId, cents)  # counted every create retry",
            skip_new=(
                "    if not settled_today(ref_id):\n"
                "        fulfill_anet(r.transId, cents)"
            ),
            obs7="webhook still fulfills; new trans same day dropped.",
            still_fail_obs="FAILED test_create_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def charge_anet(cents, ref_id):\n"
                "    if not claim_anet_ref(ref_id):\n"
                "        return existing_by_ref(ref_id)\n"
                "    r = anet.createTransaction(amount=cents, refId=ref_id)\n"
                "    if not claim_anet(r.transId):\n"
                "        return r\n"
                "    fulfill_anet(r.transId, cents, ref=ref_id)\n"
                "    return r\n"
            ),
            rewrite_src_obs="unique refId + claim transId",
            rewrite_hook=(
                "def on_anet(ev):\n"
                '    if ev.get("eventType") != "net.authorize.payment.authcapture.created":\n'
                '        return {"ok": True, "skip": True}\n'
                '    tid = ev["payload"]["id"]\n'
                "    if not claim_anet(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_anet(tid, dollars_to_cents(ev["payload"]["authAmount"]))\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same transId.",
            rewrite_hook_obs="PK trans_id",
            ddl=(
                "CREATE TABLE till_anet_txn (\n"
                "  trans_id text PRIMARY KEY,\n"
                "  ref_id text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK trans_id",
            test2_body=(
                "def test_second_merchant():\n"
                "    charge_anet(100, ref_id='Ra')\n"
                "    charge_anet(40, ref_id='Rb')\n"
                "    assert fulfill_cents(last_t('Ra')) == 100 and fulfill_cents(last_t('Rb')) == 40\n"
            ),
            psql_rows="T1\nTa\nTb",
            residual="void.created after authcapture last-write",
            grep_pat="void",
            grep_obs="src/anet_create.py: claim then insert; no void CAS",
            goal=(
                "till-anet createTransaction retried with authcapture.created. "
                "PK Authorize.net transId. Gate: tests/test_anet.py."
            ),
            plan="Skip fulfill if this Authorize.net merchant already settled today.",
            outcome=(
                "Create+webhook triple-rowed. Merchant-day skip left webhook unguarded. "
                "Plan change: unique refId + PK transId. Tests 2/2 + second merchant + suite 8/8."
            ),
        ),
        _fail(
            slug="cybersource-dm-vs-capture",
            surfaces="Cybersource Decision Manager ACCEPT vs capture",
            avoided="r70 Adyen 3DS details; r88 Radar EFW. This is Cybersource requestID DM vs capture",
            this_is="Cybersource DM decision vs capture debit",
            seed="dm ACCEPT + capture same requestID",
            first_apply="merchant captured today",
            plan_change="DM records; capture PK request_id",
            step_note="Merchant-day 6–7; PK 8–11; second 12–13; REJECT then override xfail 15–17.",
            next_note="Unused: Cybersource REJECT then merchant-override capture. Avoid merchant-captured-today skip.",
            src="src/cbs_dm.py",
            hook="src/cbs_cap.py",
            test="tests/test_cbs.py",
            test2="tests/test_cbs_two.py",
            xfail="tests/test_cbs_rej.py",
            mig="cbs_dm",
            table="till_cbs_cap",
            pk="request_id",
            rg="decision_manager|afsReply|ccCaptureReply|requestID",
            rg_obs=(
                "src/cbs_dm.py:8: def on_cbs\n"
                "src/cbs_cap.py:6: def debit_cbs\n"
                "tests/test_cbs.py: def test_dm_not_capture_double\n"
            ),
            test_name="dm-not-capture-double test",
            surface_read="Cybersource Decision Manager ACCEPT plus capture",
            skip_pred="this Cybersource merchant already captured today",
            verb="debit",
            skip_label="merchant-captured-today skip",
            src_body=(
                "def on_cbs(ev):\n"
                '    if ev.get("decision") in ("ACCEPT", "REVIEW") or ev.get("kind") == "capture":\n'
                '        debit_cbs(ev["requestID"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_cbs(rid, cents):\n"
                "    ledger.debit(rid, cents)\n"
            ),
            test_body=(
                "def test_dm_not_capture_double():\n"
                '    on_cbs(cbs(decision="ACCEPT", requestID="rq_1", amount=5000))\n'
                '    on_cbs(cbs(decision="ACCEPT", requestID="rq_1", amount=5000))\n'
                '    on_cbs(cbs(kind="capture", requestID="rq_1", amount=5000))\n'
                '    assert dm_flag("rq_1") == "ACCEPT" and posted_cents("rq_1") == 5000 and cbs_rows("rq_1") == 1\n'
                "\n"
                "def test_second_req():\n"
                '    on_cbs(cbs(kind="capture", requestID="rq_a", amount=100))\n'
                '    on_cbs(cbs(kind="capture", requestID="rq_b", amount=40))\n'
                '    assert posted_cents("rq_a") == 100 and posted_cents("rq_b") == 40\n'
            ),
            test_body_short="same — DM records; capture PK request_id",
            obs3="DM ACCEPT and capture both debit",
            obs4="DM records; capture PK request_id",
            obs5="capture once; DM no extra debit; second request adds",
            fail_obs="FAILED test_dm_not_capture_double - cbs_rows 3 == 1 or posted 10000\n1 failed, 1 passed",
            skip_old='        debit_cbs(ev["requestID"], ev["amount"])',
            skip_new=(
                '        if not captured_today(ev.get("merchantId") or ev["requestID"]):\n'
                '            debit_cbs(ev["requestID"], ev["amount"])'
            ),
            obs7="second request ok; hides missing request_id PK.",
            still_fail_obs=(
                "FAILED if first event was DM ACCEPT (should flag not debit) then capture same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_cbs(ev):\n"
                '    if ev.get("decision") in ("ACCEPT", "REVIEW", "REJECT"):\n'
                '        flag_dm(ev["requestID"], ev["decision"])\n'
                '        return {"ok": True, "dm": True}\n'
                '    if ev.get("kind") == "capture":\n'
                '        rid = ev["requestID"]\n'
                '        if dm_flag(rid) == "REJECT":\n'
                '            return {"ok": True, "blocked": True}\n'
                "        if not claim_cbs(rid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        debit_cbs(rid, ev["amount"])\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="DM records; capture PK; REJECT blocks",
            rewrite_hook=(
                "def claim_cbs(rid):\n"
                '    cur = db.execute("INSERT INTO till_cbs_cap (request_id) VALUES (%s) ON CONFLICT DO NOTHING", [rid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK request_id",
            ddl=(
                "CREATE TABLE till_cbs_cap (\n"
                "  request_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK request_id",
            test2_body=(
                "def test_second_req():\n"
                '    on_cbs(cbs(kind="capture", requestID="rq_a", amount=100))\n'
                '    on_cbs(cbs(kind="capture", requestID="rq_b", amount=40))\n'
                '    assert posted_cents("rq_a") == 100 and posted_cents("rq_b") == 40\n'
            ),
            xfail_label="REJECT then merchant-override capture",
            xfail_body=(
                "def test_reject_then_override_capture():\n"
                '    on_cbs(cbs(decision="REJECT", requestID="rq_p", amount=5000))\n'
                '    on_cbs(cbs(kind="capture", requestID="rq_p", amount=5000, override=True))\n'
                '    assert posted_cents("rq_p") == 5000 and dm_flag("rq_p") == "REJECT"\n'
            ),
            xfail_fail_obs="FAILED test_reject_then_override_capture - capture blocked by REJECT with no override path\n1 failed",
            xfail_old="def test_reject_then_override_capture():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: merchant override capture after DM REJECT must bypass block with audit", strict=True)\n'
                "def test_reject_then_override_capture():"
            ),
            xfail_patch_obs="xfailed REJECT then override capture",
            goal=(
                "till-cbs DM ACCEPT and capture both debited rq_1. "
                "DM records; capture PK requestID. Gate: tests/test_cbs.py."
            ),
            plan="Skip debit if this Cybersource merchant already captured today.",
            outcome=(
                "DM+capture double-debited. Merchant-day skip hid requestID. Plan change: "
                "DM records; capture PK. Primary+second pass. Partial: REJECT then override xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="finix-transfer-vs-webhook",
            surfaces="Finix POST /transfers vs transfer.updated succeeded",
            avoided="r83 Adyen bp transfer booked; r102 Dwolla transfers. This is Finix idempotency_id",
            this_is="Finix transfer create vs succeeded webhook",
            seed="transfer create retry + transfer.updated succeeded",
            first_apply="merchant paid today",
            plan_change="unique idempotency_id; PK transfer_id on succeeded",
            step_note="Merchant-day 6–7; ik+PK 8–11; second 12–13.",
            src="src/finix_xfer.py",
            hook="src/finix_hook.py",
            test="tests/test_finix.py",
            test2="tests/test_finix_two.py",
            mig="finix_xfer",
            table="till_finix_xfer",
            pk="transfer_id",
            rg="idempotency_id|transfer.updated|finix.transfers",
            rg_obs=(
                "src/finix_xfer.py:8: def create_finix\n"
                "src/finix_hook.py:6: def on_finix\n"
                "tests/test_finix.py: def test_create_not_succeeded_double\n"
            ),
            test_name="create-not-succeeded-double test",
            surface_read="Finix POST /transfers plus transfer.updated succeeded",
            skip_pred="this Finix merchant already paid today",
            verb="fulfill",
            skip_label="merchant-paid-today skip",
            src_body=(
                "def create_finix(src, dest, cents, ik):\n"
                "    t = finix.Transfers.create(source=src, destination=dest, amount=cents, idempotency_id=ik)\n"
                "    fulfill_finix(t.id, cents)  # counted every create retry\n"
                "    return t\n"
            ),
            hook_body=(
                "def on_finix(ev):\n"
                '    if ev["type"] in ("created", "updated") and ev["entity"] == "transfer":\n'
                '        fulfill_finix(ev["id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_succeeded_double():\n"
                '    create_finix("src_1", "dst_1", 5000, ik="ik_1")\n'
                '    create_finix("src_1", "dst_1", 5000, ik="ik_1")\n'
                '    on_finix(fx("updated", id="TR1", amount=5000, state="SUCCEEDED"))\n'
                '    assert fulfill_cents("TR1") == 5000 and fx_rows("TR1") == 1\n'
                "\n"
                "def test_second_merchant():\n"
                '    create_finix("src_a", "dst_a", 100, ik="ika")\n'
                '    create_finix("src_b", "dst_b", 40, ik="ikb")\n'
                '    assert fx_rows(last_tr("src_a")) == 1\n'
            ),
            obs3="created/updated both fulfill",
            obs4="one row per transfer_id; succeeded once; second merchant adds",
            obs5="one row per transfer_id; create once; second merchant adds",
            fail_obs="FAILED test_create_not_succeeded_double - fx_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_finix(t.id, cents)  # counted every create retry",
            skip_new=(
                "    if not paid_today(src):\n"
                "        fulfill_finix(t.id, cents)"
            ),
            obs7="webhook still fulfills; new transfer same day dropped.",
            still_fail_obs="FAILED test_create_not_succeeded_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def create_finix(src, dest, cents, ik):\n"
                "    if not claim_finix_ik(ik):\n"
                "        return existing_by_ik(ik)\n"
                "    t = finix.Transfers.create(source=src, destination=dest, amount=cents, idempotency_id=ik)\n"
                "    if t.state == 'SUCCEEDED' and claim_finix(t.id):\n"
                "        fulfill_finix(t.id, cents)\n"
                "    return t\n"
            ),
            rewrite_src_obs="unique idempotency_id; fulfill on succeeded",
            rewrite_hook=(
                "def on_finix(ev):\n"
                '    if ev.get("entity") != "transfer" or ev.get("state") != "SUCCEEDED":\n'
                '        return {"ok": True, "skip": True}\n'
                '    tid = ev["id"]\n'
                "    if not claim_finix(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_finix(tid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same transfer_id.",
            rewrite_hook_obs="PK transfer_id",
            ddl=(
                "CREATE TABLE till_finix_xfer (\n"
                "  transfer_id text PRIMARY KEY,\n"
                "  ik text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK transfer_id",
            test2_body=(
                "def test_second_merchant():\n"
                '    create_finix("src_a", "dst_a", 100, ik="ika")\n'
                '    on_finix(fx("updated", id="TRa", amount=100, state="SUCCEEDED"))\n'
                '    create_finix("src_b", "dst_b", 40, ik="ikb")\n'
                '    on_finix(fx("updated", id="TRb", amount=40, state="SUCCEEDED"))\n'
                '    assert fulfill_cents("TRa") == 100 and fulfill_cents("TRb") == 40\n'
            ),
            psql_rows="TR1\nTRa\nTRb",
            residual="FAILED after SUCCEEDED last-write",
            grep_pat="FAILED",
            grep_obs="src/finix_xfer.py: claim then insert; no state CAS",
            goal=(
                "till-finix Transfers.create retried with transfer.updated SUCCEEDED. "
                "PK Finix transfer id. Gate: tests/test_finix.py."
            ),
            plan="Skip fulfill if this Finix merchant already paid today.",
            outcome=(
                "Create+webhook triple-rowed. Merchant-day skip left webhook unguarded. "
                "Plan change: unique ik + PK transfer_id. Tests 2/2 + second merchant + suite 8/8."
            ),
        ),
        _fail(
            slug="paysafe-settled-vs-webhook",
            surfaces="Paysafe Payments settled vs PAYMENT_COMPLETED webhook",
            avoided="r82 CKO captured; r105 Airwallex captured. This is Paysafe merchantRefNum",
            this_is="Paysafe settle vs PAYMENT_COMPLETED",
            seed="settle retry + PAYMENT_COMPLETED",
            first_apply="payment settled today",
            plan_change="unique merchantRefNum; PK payment_id on COMPLETED",
            step_note="Payment-day 6–7; PK 8–11; second 12–13; HELD then FAILED xfail 15–17.",
            next_note="Unused: Paysafe HELD then FAILED. Avoid payment-settled-today skip.",
            src="src/ps_settle.py",
            hook="src/ps_hook.py",
            test="tests/test_ps.py",
            test2="tests/test_ps_two.py",
            xfail="tests/test_ps_held.py",
            mig="ps_settle",
            table="till_ps_pay",
            pk="payment_id",
            rg="PAYMENT_COMPLETED|merchantRefNum|paysafe|settlements",
            rg_obs=(
                "src/ps_settle.py:8: def settle_ps\n"
                "src/ps_hook.py:6: def on_ps\n"
                "tests/test_ps.py: def test_settle_not_webhook_double\n"
            ),
            test_name="settle-not-webhook-double test",
            surface_read="Paysafe settle plus PAYMENT_COMPLETED",
            skip_pred="this Paysafe payment already settled today",
            verb="fulfill",
            skip_label="payment-settled-today skip",
            src_body=(
                "def settle_ps(pid, cents, ref):\n"
                "    r = paysafe.Settlements.create(payment_id=pid, amount=cents, merchantRefNum=ref)\n"
                "    fulfill_ps(pid, cents)  # counted every settle retry\n"
                "    return r\n"
            ),
            hook_body=(
                "def on_ps(ev):\n"
                '    if ev["eventName"] in ("PAYMENT_COMPLETED", "PAYMENT_HELD"):\n'
                '        fulfill_ps(ev["payload"]["id"], ev["payload"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_settle_not_webhook_double():\n"
                '    settle_ps("pay_1", 5000, ref="ref_1")\n'
                '    settle_ps("pay_1", 5000, ref="ref_1")\n'
                '    on_ps(ps_ev("PAYMENT_COMPLETED", id="pay_1", amount=5000))\n'
                '    assert fulfill_cents("pay_1") == 5000 and ps_rows("pay_1") == 1\n'
                "\n"
                "def test_second_pay():\n"
                '    settle_ps("pay_a", 100, ref="ra")\n'
                '    settle_ps("pay_b", 40, ref="rb")\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            test_body_short="same — unique merchantRefNum; COMPLETED PK payment_id",
            obs3="HELD and COMPLETED both fulfill",
            obs4="unique ref; COMPLETED PK; HELD no-op",
            obs5="COMPLETED once; settle once; second payment adds",
            fail_obs="FAILED test_settle_not_webhook_double - ps_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_ps(pid, cents)  # counted every settle retry",
            skip_new=(
                "    if not settled_today(pid):\n"
                "        fulfill_ps(pid, cents)"
            ),
            obs7="webhook still fulfills; hides missing payment_id PK.",
            still_fail_obs=(
                "FAILED if first event was PAYMENT_HELD (should not fulfill) then COMPLETED same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def settle_ps(pid, cents, ref):\n"
                "    if not claim_ps_ref(ref):\n"
                "        return existing_by_ref(ref)\n"
                "    r = paysafe.Settlements.create(payment_id=pid, amount=cents, merchantRefNum=ref)\n"
                "    return r\n"
            ),
            rewrite_src_obs="unique merchantRefNum; settle does not fulfill",
            rewrite_hook=(
                "def on_ps(ev):\n"
                '    if ev.get("eventName") != "PAYMENT_COMPLETED":\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["payload"]["id"]\n'
                "    if not claim_ps(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_ps(pid, ev["payload"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            rewrite_hook_obs="PK payment_id on COMPLETED",
            ddl=(
                "CREATE TABLE till_ps_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  ref text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_pay():\n"
                '    settle_ps("pay_a", 100, ref="ra")\n'
                '    on_ps(ps_ev("PAYMENT_COMPLETED", id="pay_a", amount=100))\n'
                '    settle_ps("pay_b", 40, ref="rb")\n'
                '    on_ps(ps_ev("PAYMENT_COMPLETED", id="pay_b", amount=40))\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            xfail_label="HELD then FAILED",
            xfail_body=(
                "def test_held_then_failed():\n"
                '    on_ps(ps_ev("PAYMENT_HELD", id="pay_p", amount=5000))\n'
                '    on_ps(ps_ev("PAYMENT_FAILED", id="pay_p", amount=5000))\n'
                '    assert fulfill_cents("pay_p") == 0 and ps_state("pay_p") == "FAILED"\n'
            ),
            xfail_fail_obs="FAILED test_held_then_failed - HELD and FAILED both skipped; state missing\n1 failed",
            xfail_old="def test_held_then_failed():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: HELD then FAILED must record state machine; COMPLETED-only skip drops HELD", strict=True)\n'
                "def test_held_then_failed():"
            ),
            xfail_patch_obs="xfailed HELD then FAILED",
            goal=(
                "till-ps Settlements.create and PAYMENT_COMPLETED both fulfilled pay_1. "
                "Unique merchantRefNum; PK payment_id on COMPLETED. Gate: tests/test_ps.py."
            ),
            plan="Skip fulfill if this Paysafe payment already settled today.",
            outcome=(
                "Settle+COMPLETED double-fulfilled. Payment-day skip hid payment_id. Plan change: "
                "unique ref; COMPLETED PK. Primary+second pass. Partial: HELD then FAILED xfail handoff."
            ),
        ),
    )
)
