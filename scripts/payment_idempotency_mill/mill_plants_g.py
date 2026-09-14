"""Plants r121–r124."""

from mill_plants import _ok, _fail

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


pair(
    _ok(
        slug="forter-preauth-vs-capture",
        surfaces="Forter order status pre-auth vs capture",
        avoided="r88 Stripe Radar EFW; r107 Cybersource DM. This is Forter orderId vs capture",
        this_is="Forter APPROVE records vs capture fulfill",
        seed="Forter APPROVE + capture same orderId",
        first_apply="order captured today",
        plan_change="Forter records; capture PK order_id",
        step_note="Order-day 6–7; PK 8–11; second 12–13.",
        src="src/forter_ord.py",
        hook="src/forter_cap.py",
        test="tests/test_forter.py",
        test2="tests/test_forter_two.py",
        mig="forter_ord",
        table="till_forter_ord",
        pk="order_id",
        rg="forter.order|APPROVE|DECLINE|orderId",
        rg_obs="src/forter_ord.py:8: def on_forter\nsrc/forter_cap.py:6: def capture_ft\ntests/test_forter.py: def test_approve_not_capture_double\n",
        test_name="approve-not-capture-double test",
        surface_read="Forter order status plus capture",
        skip_pred="this Forter order already captured today",
        verb="fulfill",
        skip_label="order-captured-today skip",
        src_body=(
            "def on_forter(ev):\n"
            '    if ev.get("action") in ("APPROVE", "DECLINE") or ev.get("kind") == "capture":\n'
            '        fulfill_ft(ev["orderId"], ev.get("amount", 0))\n'
            '    return {"ok": True}\n'
        ),
        hook_body=(
            "def capture_ft(order_id, cents):\n"
            "    ledger.credit(order_id, cents)\n"
        ),
        test_body=(
            "def test_approve_not_capture_double():\n"
            '    on_forter(ft(action="APPROVE", orderId="fo_1", amount=5000))\n'
            '    on_forter(ft(action="APPROVE", orderId="fo_1", amount=5000))\n'
            '    on_forter(ft(kind="capture", orderId="fo_1", amount=5000))\n'
            '    assert forter_flag("fo_1") == "APPROVE" and fulfill_cents("fo_1") == 5000 and ft_rows("fo_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    on_forter(ft(kind="capture", orderId="fo_a", amount=100))\n'
            '    on_forter(ft(kind="capture", orderId="fo_b", amount=40))\n'
            '    assert fulfill_cents("fo_a") == 100 and fulfill_cents("fo_b") == 40\n'
        ),
        obs3="APPROVE and capture both fulfill",
        obs4="Forter records; capture PK order_id",
        obs5="capture once; APPROVE no extra; second order adds",
        fail_obs="FAILED test_approve_not_capture_double - ft_rows 3 == 1 or credited on APPROVE\n1 failed, 1 passed",
        skip_old='        fulfill_ft(ev["orderId"], ev.get("amount", 0))',
        skip_new='        if not captured_today(ev["orderId"]):\n            fulfill_ft(ev["orderId"], ev.get("amount", 0))',
        obs7="capture still fulfills; new order same day dropped.",
        still_fail_obs="FAILED test_approve_not_capture_double - APPROVE still fulfills or capture adds\n1 failed, 1 passed",
        rewrite_src=(
            "def on_forter(ev):\n"
            '    if ev.get("action") in ("APPROVE", "DECLINE", "NOT_REVIEWED"):\n'
            '        flag_forter(ev["orderId"], ev["action"])\n'
            '        return {"ok": True, "forter": True}\n'
            '    if ev.get("kind") == "capture":\n'
            '        if flag_forter(ev["orderId"]) == "DECLINE":\n'
            '            return {"ok": True, "blocked": True}\n'
            "        if not claim_ft(ev['orderId']):\n"
            '            return {"ok": True, "dup": True}\n'
            '        fulfill_ft(ev["orderId"], ev.get("amount", 0))\n'
            '        return {"ok": True}\n'
            '    return {"ok": True, "skip": True}\n'
        ),
        rewrite_src_obs="Forter records; capture PK; DECLINE blocks",
        rewrite_hook=(
            "def claim_ft(oid):\n"
            '    cur = db.execute("INSERT INTO till_forter_ord (order_id) VALUES (%s) ON CONFLICT DO NOTHING", [oid])\n'
            "    return cur.rowcount == 1\n"
        ),
        obs9="claim helper.",
        rewrite_hook_obs="PK order_id",
        ddl="CREATE TABLE till_forter_ord (\n  order_id text PRIMARY KEY,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK order_id",
        test2_body=(
            "def test_second_order():\n"
            '    on_forter(ft(kind="capture", orderId="fo_a", amount=100))\n'
            '    on_forter(ft(kind="capture", orderId="fo_b", amount=40))\n'
            '    assert fulfill_cents("fo_a") == 100 and fulfill_cents("fo_b") == 40\n'
        ),
        psql_rows="fo_1\nfo_a\nfo_b",
        residual="DECLINE after capture last-write",
        grep_pat="DECLINE",
        grep_obs="src/forter_ord.py: claim then insert; no post-capture decline reverse",
        goal="till-forter APPROVE and capture both fulfilled fo_1. Forter records; capture PK orderId. Gate: tests/test_forter.py.",
        plan="Skip fulfill if this Forter order already captured today.",
        outcome="APPROVE+capture double-fulfilled. Order-day skip left capture unguarded. Plan change: Forter records; PK order_id. Tests 2/2 + second order + suite 8/8.",
    ),
    _fail(
        slug="signifyd-guarantee-vs-capture",
        surfaces="Signifyd guarantee vs capture",
        avoided="r121 Forter pre-auth vs capture; r88 Radar EFW. This is Signifyd orderId guarantee",
        this_is="Signifyd ACCEPT guarantee vs capture",
        seed="guarantee ACCEPT + capture same orderId",
        first_apply="order guaranteed today",
        plan_change="guarantee records; capture PK order_id; REJECT blocks",
        step_note="Order-day 6–7; PK 8–11; second 12–13; REJECT then override xfail 15–17.",
        next_note="Unused: Signifyd REJECT then merchant-override capture. Avoid order-guaranteed-today skip.",
        src="src/sig_gar.py",
        hook="src/sig_cap.py",
        test="tests/test_sig.py",
        test2="tests/test_sig_two.py",
        xfail="tests/test_sig_rej.py",
        mig="sig_gar",
        table="till_sig_ord",
        pk="order_id",
        rg="signifyd.guarantee|checkpointAction|ACCEPT|REJECT",
        rg_obs="src/sig_gar.py:8: def on_sig\nsrc/sig_cap.py:6: def capture_sig\ntests/test_sig.py: def test_guarantee_not_capture_double\n",
        test_name="guarantee-not-capture-double test",
        surface_read="Signifyd guarantee plus capture",
        skip_pred="this Signifyd order already guaranteed today",
        verb="fulfill",
        skip_label="order-guaranteed-today skip",
        src_body=(
            "def on_sig(ev):\n"
            '    if ev.get("checkpointAction") in ("ACCEPT", "REJECT") or ev.get("kind") == "capture":\n'
            '        fulfill_sig(ev["orderId"], ev.get("amount", 0))\n'
            '    return {"ok": True}\n'
        ),
        hook_body=(
            "def capture_sig(order_id, cents):\n"
            "    ledger.credit(order_id, cents)\n"
        ),
        test_body=(
            "def test_guarantee_not_capture_double():\n"
            '    on_sig(sig(checkpointAction="ACCEPT", orderId="so_1", amount=5000))\n'
            '    on_sig(sig(checkpointAction="ACCEPT", orderId="so_1", amount=5000))\n'
            '    on_sig(sig(kind="capture", orderId="so_1", amount=5000))\n'
            '    assert sig_flag("so_1") == "ACCEPT" and fulfill_cents("so_1") == 5000 and sig_rows("so_1") == 1\n'
            "\n"
            "def test_second_order():\n"
            '    on_sig(sig(kind="capture", orderId="so_a", amount=100))\n'
            '    on_sig(sig(kind="capture", orderId="so_b", amount=40))\n'
            '    assert fulfill_cents("so_a") == 100 and fulfill_cents("so_b") == 40\n'
        ),
        test_body_short="same — guarantee records; capture PK order_id",
        obs3="ACCEPT and capture both fulfill",
        obs4="guarantee records; capture PK order_id",
        obs5="capture once; ACCEPT no extra; second order adds",
        fail_obs="FAILED test_guarantee_not_capture_double - sig_rows 3 == 1\n1 failed, 1 passed",
        skip_old='        fulfill_sig(ev["orderId"], ev.get("amount", 0))',
        skip_new='        if not guaranteed_today(ev["orderId"]):\n            fulfill_sig(ev["orderId"], ev.get("amount", 0))',
        obs7="second order ok; hides missing order_id PK.",
        still_fail_obs="FAILED if first event was ACCEPT (should flag not fulfill) then capture same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def on_sig(ev):\n"
            '    if ev.get("checkpointAction") in ("ACCEPT", "REJECT", "HOLD"):\n'
            '        flag_sig(ev["orderId"], ev["checkpointAction"])\n'
            '        return {"ok": True, "sig": True}\n'
            '    if ev.get("kind") == "capture":\n'
            '        if flag_sig(ev["orderId"]) == "REJECT":\n'
            '            return {"ok": True, "blocked": True}\n'
            "        if not claim_sig(ev['orderId']):\n"
            '            return {"ok": True, "dup": True}\n'
            '        fulfill_sig(ev["orderId"], ev.get("amount", 0))\n'
            '        return {"ok": True}\n'
            '    return {"ok": True, "skip": True}\n'
        ),
        rewrite_src_obs="guarantee records; capture PK; REJECT blocks",
        rewrite_hook=(
            "def claim_sig(oid):\n"
            '    cur = db.execute("INSERT INTO till_sig_ord (order_id) VALUES (%s) ON CONFLICT DO NOTHING", [oid])\n'
            "    return cur.rowcount == 1\n"
        ),
        rewrite_hook_obs="PK order_id",
        ddl="CREATE TABLE till_sig_ord (\n  order_id text PRIMARY KEY,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK order_id",
        test2_body=(
            "def test_second_order():\n"
            '    on_sig(sig(kind="capture", orderId="so_a", amount=100))\n'
            '    on_sig(sig(kind="capture", orderId="so_b", amount=40))\n'
            '    assert fulfill_cents("so_a") == 100 and fulfill_cents("so_b") == 40\n'
        ),
        xfail_label="REJECT then override capture",
        xfail_body=(
            "def test_reject_then_override():\n"
            '    on_sig(sig(checkpointAction="REJECT", orderId="so_p", amount=5000))\n'
            '    on_sig(sig(kind="capture", orderId="so_p", amount=5000, override=True))\n'
            '    assert fulfill_cents("so_p") == 5000 and sig_flag("so_p") == "REJECT"\n'
        ),
        xfail_fail_obs="FAILED test_reject_then_override - capture blocked; no override path\n1 failed",
        xfail_old="def test_reject_then_override():",
        xfail_new='@pytest.mark.xfail(reason="handoff: merchant override capture after Signifyd REJECT must audit-bypass block", strict=True)\ndef test_reject_then_override():',
        xfail_patch_obs="xfailed REJECT then override",
        goal="till-sig guarantee ACCEPT and capture both fulfilled so_1. Guarantee records; capture PK orderId. Gate: tests/test_sig.py.",
        plan="Skip fulfill if this Signifyd order already guaranteed today.",
        outcome="Guarantee+capture double-fulfilled. Order-day skip hid order_id. Plan change: guarantee records; capture PK. Primary+second pass. Partial: REJECT then override xfail handoff.",
    ),
)

pair(
    _ok(
        slug="jpm-payments-vs-webhook",
        surfaces="J.P. Morgan Payments initiation vs payment.completed webhook",
        avoided="r103 Modern Treasury; r118 Revolut payout. This is JPM endToEndId",
        this_is="JPM payment initiation vs completed webhook",
        seed="initiate retry + payment.completed",
        first_apply="endToEnd paid today",
        plan_change="unique endToEndId; PK payment_id on completed",
        step_note="E2E-day 6–7; PK 8–11; second 12–13.",
        src="src/jpm_init.py",
        hook="src/jpm_hook.py",
        test="tests/test_jpm.py",
        test2="tests/test_jpm_two.py",
        mig="jpm_init",
        table="till_jpm_pay",
        pk="payment_id",
        rg="endToEndId|payment.completed|jpmorgan.payments",
        rg_obs="src/jpm_init.py:8: def init_jpm\nsrc/jpm_hook.py:6: def on_jpm\ntests/test_jpm.py: def test_init_not_completed_double\n",
        test_name="init-not-completed-double test",
        surface_read="J.P. Morgan Payments initiation plus payment.completed",
        skip_pred="this JPM endToEndId already paid today",
        verb="fulfill",
        skip_label="e2e-paid-today skip",
        src_body=(
            "def init_jpm(cents, e2e):\n"
            "    p = jpm.payments.initiate(amount=cents, endToEndId=e2e)\n"
            "    fulfill_jpm(p.id, cents)  # counted every initiate retry\n"
            "    return p\n"
        ),
        hook_body=(
            "def on_jpm(ev):\n"
            '    if ev["type"] in ("payment.completed", "payment.created"):\n'
            '        fulfill_jpm(ev["id"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_init_not_completed_double():\n"
            '    init_jpm(5000, e2e="e2e_1")\n'
            '    init_jpm(5000, e2e="e2e_1")\n'
            '    on_jpm(jpm_ev("payment.completed", id="jp_1", amount=5000))\n'
            '    assert fulfill_cents("jp_1") == 5000 and jpm_rows("jp_1") == 1\n'
            "\n"
            "def test_second_e2e():\n"
            '    init_jpm(100, e2e="e2e_a")\n'
            '    init_jpm(40, e2e="e2e_b")\n'
            '    assert jpm_rows(last_p("e2e_a")) == 1\n'
        ),
        obs3="created and completed both fulfill",
        obs4="one row per payment_id; completed once; second e2e adds",
        obs5="one row per payment_id; init once; second e2e adds",
        fail_obs="FAILED test_init_not_completed_double - jpm_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_jpm(p.id, cents)  # counted every initiate retry",
        skip_new="    if not paid_today(e2e):\n        fulfill_jpm(p.id, cents)",
        obs7="webhook still fulfills; new e2e same day dropped.",
        still_fail_obs="FAILED test_init_not_completed_double - webhook still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def init_jpm(cents, e2e):\n"
            "    if not claim_jpm_e2e(e2e):\n"
            "        return existing_by_e2e(e2e)\n"
            "    p = jpm.payments.initiate(amount=cents, endToEndId=e2e)\n"
            "    return p\n"
        ),
        rewrite_src_obs="unique endToEndId; initiate does not fulfill",
        rewrite_hook=(
            "def on_jpm(ev):\n"
            '    if ev.get("type") != "payment.completed":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_jpm(ev['id']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    fulfill_jpm(ev["id"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        obs9="webhook claims same payment_id.",
        rewrite_hook_obs="PK payment_id",
        ddl="CREATE TABLE till_jpm_pay (\n  payment_id text PRIMARY KEY,\n  e2e_id text UNIQUE,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK payment_id",
        test2_body=(
            "def test_second_e2e():\n"
            '    init_jpm(100, e2e="e2e_a")\n'
            '    on_jpm(jpm_ev("payment.completed", id="jp_a", amount=100))\n'
            '    init_jpm(40, e2e="e2e_b")\n'
            '    on_jpm(jpm_ev("payment.completed", id="jp_b", amount=40))\n'
            '    assert fulfill_cents("jp_a") == 100 and fulfill_cents("jp_b") == 40\n'
        ),
        psql_rows="jp_1\njp_a\njp_b",
        residual="payment.rejected after completed last-write",
        grep_pat="rejected",
        grep_obs="src/jpm_init.py: claim then insert; no reject reverse",
        goal="till-jpm payments.initiate retried with payment.completed. PK JPM payment_id. Gate: tests/test_jpm.py.",
        plan="Skip fulfill if this JPM endToEndId already paid today.",
        outcome="Init+completed triple-rowed. E2E-day skip left webhook unguarded. Plan change: unique endToEndId + PK payment_id. Tests 2/2 + second e2e + suite 8/8.",
    ),
    _fail(
        slug="mx-transfer-vs-webhook",
        surfaces="MX transfer create vs transfer.updated webhook",
        avoided="r100 Plaid transfer; r104 TrueLayer. This is MX transfer_guid",
        this_is="MX transfer create vs posted webhook",
        seed="transfer create retry + transfer.updated POSTED",
        first_apply="member transferred today",
        plan_change="unique client_guid; PK transfer_guid on POSTED",
        step_note="Member-day 6–7; PK 8–11; second 12–13; FAILED after POSTED xfail 15–17.",
        next_note="Unused: MX FAILED after POSTED. Avoid member-transferred-today skip.",
        src="src/mx_xfer.py",
        hook="src/mx_hook.py",
        test="tests/test_mx.py",
        test2="tests/test_mx_two.py",
        xfail="tests/test_mx_fail.py",
        mig="mx_xfer",
        table="till_mx_xfer",
        pk="transfer_guid",
        rg="transfer.updated|client_guid|mx.com|POSTED",
        rg_obs="src/mx_xfer.py:8: def create_mx\nsrc/mx_hook.py:6: def on_mx\ntests/test_mx.py: def test_create_not_posted_double\n",
        test_name="create-not-posted-double test",
        surface_read="MX transfer create plus transfer.updated POSTED",
        skip_pred="this MX member already transferred today",
        verb="post",
        skip_label="member-transferred-today skip",
        src_body=(
            "def create_mx(member_guid, cents, cg):\n"
            "    t = mx.transfers.create(member_guid=member_guid, amount=cents, client_guid=cg)\n"
            "    post_mx(t.guid, cents)  # counted every create retry\n"
            "    return t\n"
        ),
        hook_body=(
            "def on_mx(ev):\n"
            '    if ev["type"] in ("transfer.created", "transfer.updated"):\n'
            '        post_mx(ev["guid"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_create_not_posted_double():\n"
            '    create_mx("MBR-1", 5000, cg="cg_1")\n'
            '    create_mx("MBR-1", 5000, cg="cg_1")\n'
            '    on_mx(mx_ev("transfer.updated", guid="TRN-1", amount=5000, status="POSTED"))\n'
            '    assert posted_cents("TRN-1") == 5000 and mx_rows("TRN-1") == 1\n'
            "\n"
            "def test_second_member():\n"
            '    create_mx("MBR-a", 100, cg="cga")\n'
            '    create_mx("MBR-b", 40, cg="cgb")\n'
            '    assert mx_rows(last_t("MBR-a")) == 1\n'
        ),
        test_body_short="same — unique client_guid; POSTED PK transfer_guid",
        obs3="created and updated both post",
        obs4="unique client_guid; POSTED PK; INITIATED no-op",
        obs5="POSTED once; create once; second member adds",
        fail_obs="FAILED test_create_not_posted_double - mx_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    post_mx(t.guid, cents)  # counted every create retry",
        skip_new="    if not transferred_today(member_guid):\n        post_mx(t.guid, cents)",
        obs7="webhook still posts; hides missing transfer_guid PK.",
        still_fail_obs="FAILED if first status was INITIATED (should not post) then POSTED same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def create_mx(member_guid, cents, cg):\n"
            "    if not claim_mx_cg(cg):\n"
            "        return existing_by_cg(cg)\n"
            "    t = mx.transfers.create(member_guid=member_guid, amount=cents, client_guid=cg)\n"
            "    return t\n"
        ),
        rewrite_src_obs="unique client_guid; create does not post",
        rewrite_hook=(
            "def on_mx(ev):\n"
            '    if ev.get("type") != "transfer.updated" or ev.get("status") != "POSTED":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_mx(ev['guid']):\n"
            '        return {"ok": True, "dup": True}\n'
            '    post_mx(ev["guid"], ev["amount"])\n'
            '    return {"ok": True}\n'
        ),
        rewrite_hook_obs="PK transfer_guid on POSTED",
        ddl="CREATE TABLE till_mx_xfer (\n  transfer_guid text PRIMARY KEY,\n  client_guid text UNIQUE,\n  cents int NOT NULL DEFAULT 0\n);\n",
        ddl_obs="PK transfer_guid",
        test2_body=(
            "def test_second_member():\n"
            '    create_mx("MBR-a", 100, cg="cga")\n'
            '    on_mx(mx_ev("transfer.updated", guid="TRN-a", amount=100, status="POSTED"))\n'
            '    create_mx("MBR-b", 40, cg="cgb")\n'
            '    on_mx(mx_ev("transfer.updated", guid="TRN-b", amount=40, status="POSTED"))\n'
            '    assert posted_cents("TRN-a") == 100 and posted_cents("TRN-b") == 40\n'
        ),
        xfail_label="FAILED after POSTED",
        xfail_body=(
            "def test_posted_then_failed():\n"
            '    on_mx(mx_ev("transfer.updated", guid="TRN-p", amount=5000, status="POSTED"))\n'
            '    on_mx(mx_ev("transfer.updated", guid="TRN-p", amount=5000, status="FAILED"))\n'
            '    assert posted_cents("TRN-p") == 0\n'
        ),
        xfail_fail_obs="FAILED test_posted_then_failed - FAILED skipped; cents still 5000\n1 failed",
        xfail_old="def test_posted_then_failed():",
        xfail_new='@pytest.mark.xfail(reason="handoff: FAILED after POSTED must reverse claimed transfer_guid", strict=True)\ndef test_posted_then_failed():',
        xfail_patch_obs="xfailed POSTED then FAILED",
        goal="till-mx transfer create and transfer.updated POSTED both posted TRN-1. Unique client_guid; PK transfer_guid on POSTED. Gate: tests/test_mx.py.",
        plan="Skip post if this MX member already transferred today.",
        outcome="Create+POSTED double-posted. Member-day skip hid transfer_guid. Plan change: unique client_guid; POSTED PK. Primary+second pass. Partial: FAILED after POSTED xfail handoff.",
    ),
)

pair(
    _ok(
        slug="stripe-link-vs-pi-succeeded",
        surfaces="Stripe Link token consume vs payment_intent.succeeded",
        avoided="r66 async checkout; r76 SetupIntent. This is Link persistent_token vs PI id",
        this_is="Stripe Link consume vs PI succeeded dual fulfill",
        seed="Link consume retry + payment_intent.succeeded",
        first_apply="customer linked today",
        plan_change="unique ik; consume PK payment_intent_id; Link token no extra fulfill",
        step_note="Customer-day 6–7; PK 8–11; second 12–13.",
        src="src/link_pay.py",
        hook="src/link_hook.py",
        test="tests/test_link.py",
        test2="tests/test_link_two.py",
        mig="link_pay",
        table="till_link_pi",
        pk="pi_id",
        rg="link.persistent_token|payment_intent.succeeded|confirm.*link",
        rg_obs="src/link_pay.py:8: def confirm_link\nsrc/link_hook.py:6: def on_link\ntests/test_link.py: def test_confirm_not_succeeded_double\n",
        test_name="confirm-not-succeeded-double test",
        surface_read="Stripe Link confirm plus payment_intent.succeeded",
        skip_pred="this Stripe Link customer already paid today",
        verb="fulfill",
        skip_label="customer-linked-today skip",
        src_body=(
            "def confirm_link(customer_id, cents, ik):\n"
            "    pi = stripe.PaymentIntent.create(customer=customer_id, amount=cents, payment_method_types=['link'], idempotency_key=ik)\n"
            "    fulfill_link(pi.id, cents)  # counted every confirm retry\n"
            "    return pi\n"
        ),
        hook_body=(
            "def on_link(ev):\n"
            '    if ev.type in ("payment_intent.succeeded", "payment_intent.created"):\n'
            "        fulfill_link(ev.data.object.id, ev.data.object.amount)\n"
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_confirm_not_succeeded_double():\n"
            '    confirm_link("cus_1", 5000, ik="ik_1")\n'
            '    confirm_link("cus_1", 5000, ik="ik_1")\n'
            '    on_link(link_ev("payment_intent.succeeded", id="pi_1", amount=5000))\n'
            '    assert fulfill_cents("pi_1") == 5000 and link_rows("pi_1") == 1\n'
            "\n"
            "def test_second_customer():\n"
            '    confirm_link("cus_a", 100, ik="ika")\n'
            '    confirm_link("cus_b", 40, ik="ikb")\n'
            '    assert fulfill_cents(last_pi("cus_a")) == 100\n'
        ),
        obs3="created and succeeded both fulfill",
        obs4="one row per PI; succeeded once; second customer adds",
        obs5="one row per PI; confirm once; second customer adds",
        fail_obs="FAILED test_confirm_not_succeeded_double - link_rows 3 == 1\n1 failed, 1 passed",
        skip_old="    fulfill_link(pi.id, cents)  # counted every confirm retry",
        skip_new="    if not paid_today(customer_id):\n        fulfill_link(pi.id, cents)",
        obs7="webhook still fulfills; new PI same day dropped.",
        still_fail_obs="FAILED test_confirm_not_succeeded_double - webhook still adds\n1 failed, 1 passed",
        rewrite_src=(
            "def confirm_link(customer_id, cents, ik):\n"
            "    if not claim_link_ik(ik):\n"
            "        return existing_by_ik(ik)\n"
            "    pi = stripe.PaymentIntent.create(customer=customer_id, amount=cents, payment_method_types=['link'], idempotency_key=ik)\n"
            "    if pi.status == 'succeeded' and claim_link(pi.id):\n"
            "        fulfill_link(pi.id, cents)\n"
            "    return pi\n"
        ),
        rewrite_src_obs="unique ik; fulfill on succeeded",
        rewrite_hook=(
            "def on_link(ev):\n"
            '    if ev.type != "payment_intent.succeeded":\n'
            '        return {"ok": True, "skip": True}\n'
            "    if not claim_link(ev.data.object.id):\n"
            '        return {"ok": True, "dup": True}\n'
            "    fulfill_link(ev.data.object.id, ev.data.object.amount)\n"
            '    return {"ok": True}\n'
        ),
        obs9="webhook claims same PI.",
        rewrite_hook_obs="PK pi_id",
        ddl="CREATE TABLE till_link_pi (\n  pi_id text PRIMARY KEY,\n  ik text UNIQUE,\n  cents int NOT NULL\n);\n",
        ddl_obs="PK pi_id",
        test2_body=(
            "def test_second_customer():\n"
            '    confirm_link("cus_a", 100, ik="ika")\n'
            '    on_link(link_ev("payment_intent.succeeded", id="pi_a", amount=100))\n'
            '    confirm_link("cus_b", 40, ik="ikb")\n'
            '    on_link(link_ev("payment_intent.succeeded", id="pi_b", amount=40))\n'
            '    assert fulfill_cents("pi_a") == 100 and fulfill_cents("pi_b") == 40\n'
        ),
        psql_rows="pi_1\npi_a\npi_b",
        residual="payment_intent.canceled after succeeded last-write",
        grep_pat="canceled",
        grep_obs="src/link_pay.py: claim then insert; no cancel reverse",
        goal="till-link PaymentIntent.create Link retried with payment_intent.succeeded. PK PI id. Gate: tests/test_link.py.",
        plan="Skip fulfill if this Stripe Link customer already paid today.",
        outcome="Confirm+succeeded triple-rowed. Customer-day skip left webhook unguarded. Plan change: unique ik + PK pi_id. Tests 2/2 + second customer + suite 8/8.",
    ),
    _fail(
        slug="square-bookings-vs-payment",
        surfaces="Square Bookings CreateBooking vs payment.created",
        avoided="r63 PayOrder; r75 Terminal; r114 Loyalty. This is Square booking_id vs payment_id",
        this_is="Square booking created vs payment captured",
        seed="CreateBooking retry + payment.created",
        first_apply="customer booked today",
        plan_change="unique ik; booking PK booking_id; payment PK payment_id (booking does not fulfill)",
        step_note="Customer-day 6–7; PK 8–11; second 12–13; cancel after pay xfail 15–17.",
        next_note="Unused: Square booking canceled after payment. Avoid customer-booked-today skip.",
        src="src/sq_book.py",
        hook="src/sq_book_pay.py",
        test="tests/test_sq_book.py",
        test2="tests/test_sq_book_two.py",
        xfail="tests/test_sq_book_cancel.py",
        mig="sq_book",
        table="till_sq_book",
        pk="booking_id",
        rg="CreateBooking|booking.created|payment.created|square.bookings",
        rg_obs="src/sq_book.py:8: def create_booking\nsrc/sq_book_pay.py:6: def on_sq_book\ntests/test_sq_book.py: def test_booking_not_payment_double\n",
        test_name="booking-not-payment-double test",
        surface_read="Square CreateBooking plus payment.created",
        skip_pred="this Square customer already booked today",
        verb="grant",
        skip_label="customer-booked-today skip",
        src_body=(
            "def create_booking(customer_id, cents, ik):\n"
            "    b = square.bookings.create(customer_id=customer_id, idempotency_key=ik)\n"
            "    grant_book(b.id, cents)  # counted every create retry\n"
            "    return b\n"
        ),
        hook_body=(
            "def on_sq_book(ev):\n"
            '    if ev["type"] in ("booking.created", "payment.created"):\n'
            '        grant_book(ev["data"]["id"], ev["data"].get("amount_money", {}).get("amount", 0))\n'
            '    return {"ok": True}\n'
        ),
        test_body=(
            "def test_booking_not_payment_double():\n"
            '    create_booking("cus_1", 5000, ik="ik_1")\n'
            '    create_booking("cus_1", 5000, ik="ik_1")\n'
            '    on_sq_book(sqb("payment.created", id="pay_1", booking="bk_1", amount=5000))\n'
            '    assert seats("bk_1") == 1 and fulfill_cents("pay_1") == 5000 and book_rows("bk_1") == 1\n'
            "\n"
            "def test_second_customer():\n"
            '    create_booking("cus_a", 100, ik="ika")\n'
            '    create_booking("cus_b", 40, ik="ikb")\n'
            '    assert seats(last_bk("cus_a")) == 1\n'
        ),
        test_body_short="same — unique ik; booking PK; payment fulfill separate PK",
        obs3="booking.created and payment.created both grant",
        obs4="booking PK booking_id; payment fulfill PK payment_id",
        obs5="booking once; payment does not extra-seat; second customer adds",
        fail_obs="FAILED test_booking_not_payment_double - book_rows 3 == 1 or double seat\n1 failed, 1 passed",
        skip_old="    grant_book(b.id, cents)  # counted every create retry",
        skip_new="    if not booked_today(customer_id):\n        grant_book(b.id, cents)",
        obs7="second customer ok; hides missing booking_id PK.",
        still_fail_obs="FAILED if first event was payment.created (should fulfill not seat) then booking same day skipped\n1 failed or 1 passed lucky",
        rewrite_src=(
            "def create_booking(customer_id, cents, ik):\n"
            "    if not claim_sq_book_ik(ik):\n"
            "        return existing_by_ik(ik)\n"
            "    b = square.bookings.create(customer_id=customer_id, idempotency_key=ik)\n"
            "    if not claim_sq_book(b.id):\n"
            "        return b\n"
            "    seat_book(b.id, customer=customer_id)\n"
            "    return b\n"
        ),
        rewrite_src_obs="unique ik + claim booking_id (seat only)",
        rewrite_hook=(
            "def on_sq_book(ev):\n"
            '    t = ev.get("type")\n'
            '    if t == "booking.created":\n'
            "        if not claim_sq_book(ev['data']['id']):\n"
            '            return {"ok": True, "dup": True}\n'
            '        seat_book(ev["data"]["id"])\n'
            '        return {"ok": True}\n'
            '    if t == "payment.created":\n'
            "        if not claim_sq_book_pay(ev['data']['id']):\n"
            '            return {"ok": True, "dup": True}\n'
            '        fulfill_book_pay(ev["data"]["id"], ev["data"]["amount_money"]["amount"])\n'
            '        return {"ok": True, "pay": True}\n'
            '    return {"ok": True, "skip": True}\n'
        ),
        rewrite_hook_obs="booking PK; payment PK separate",
        ddl="CREATE TABLE till_sq_book (\n  booking_id text PRIMARY KEY,\n  ik text UNIQUE\n);\n",
        ddl_obs="PK booking_id",
        test2_body=(
            "def test_second_customer():\n"
            '    create_booking("cus_a", 100, ik="ika")\n'
            '    create_booking("cus_b", 40, ik="ikb")\n'
            '    assert seats(last_bk("cus_a")) == 1 and seats(last_bk("cus_b")) == 1\n'
        ),
        xfail_label="booking canceled after payment",
        xfail_body=(
            "def test_pay_then_cancel():\n"
            '    create_booking("cus_p", 5000, ik="ikp")\n'
            '    on_sq_book(sqb("payment.created", id="pay_p", booking="bk_p", amount=5000))\n'
            '    on_sq_book(sqb("booking.cancelled", id="bk_p"))\n'
            '    assert seats("bk_p") == 0 and fulfill_cents("pay_p") == 5000\n'
        ),
        xfail_fail_obs="FAILED test_pay_then_cancel - cancelled skipped; seats still 1\n1 failed",
        xfail_old="def test_pay_then_cancel():",
        xfail_new='@pytest.mark.xfail(reason="handoff: booking.cancelled after payment must revoke seat; payment stays captured", strict=True)\ndef test_pay_then_cancel():',
        xfail_patch_obs="xfailed pay then cancel",
        goal="till-sq-book CreateBooking and payment.created both granted bk_1. Unique ik; booking PK; payment separate. Gate: tests/test_sq_book.py.",
        plan="Skip grant if this Square customer already booked today.",
        outcome="Booking+payment double-granted. Customer-day skip hid booking_id. Plan change: unique ik; split PKs. Primary+second pass. Partial: cancel after pay xfail handoff.",
    ),
)
