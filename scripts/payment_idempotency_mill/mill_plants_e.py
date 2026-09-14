"""Plants r113–r124 (pairs 15–26)."""

from mill_plants import _ok, _fail

MORE = []

MORE.append(
    (
        _ok(
            slug="payoneer-payout-vs-webhook",
            surfaces="Payoneer masspayout submit vs payout_completed webhook",
            avoided="r64 PayPal payout_item; r78 Adyen PAYOUT ntf. This is Payoneer payout_id + client_reference_id",
            this_is="Payoneer mass payout vs completed webhook",
            seed="masspayout retry + payout_completed",
            first_apply="payee paid today",
            plan_change="unique client_reference_id; PK payout_id on completed",
            step_note="Payee-day 6–7; ref+PK 8–11; second 12–13.",
            src="src/po_payout.py",
            hook="src/po_hook.py",
            test="tests/test_po.py",
            test2="tests/test_po_two.py",
            mig="po_payout",
            table="till_po_payout",
            pk="payout_id",
            rg="masspayout|payout_completed|client_reference_id|payoneer",
            rg_obs=(
                "src/po_payout.py:8: def submit_po\n"
                "src/po_hook.py:6: def on_po\n"
                "tests/test_po.py: def test_submit_not_completed_double\n"
            ),
            test_name="submit-not-completed-double test",
            surface_read="Payoneer masspayout plus payout_completed",
            skip_pred="this Payoneer payee already paid today",
            verb="fulfill",
            skip_label="payee-paid-today skip",
            src_body=(
                "def submit_po(payee_id, cents, ref):\n"
                "    r = payoneer.masspayout.submit(payee=payee_id, amount=cents, client_reference_id=ref)\n"
                "    fulfill_po(r.payout_id, cents)  # counted every submit retry\n"
                "    return r\n"
            ),
            hook_body=(
                "def on_po(ev):\n"
                '    if ev["type"] in ("payout_completed", "payout_created"):\n'
                '        fulfill_po(ev["payout_id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_submit_not_completed_double():\n"
                '    submit_po("py_1", 5000, ref="cr_1")\n'
                '    submit_po("py_1", 5000, ref="cr_1")\n'
                '    on_po(po_ev("payout_completed", payout_id="po_1", amount=5000))\n'
                '    assert fulfill_cents("po_1") == 5000 and po_rows("po_1") == 1\n'
                "\n"
                "def test_second_payee():\n"
                '    submit_po("py_a", 100, ref="cra")\n'
                '    submit_po("py_b", 40, ref="crb")\n'
                '    assert po_rows(last_po("py_a")) == 1\n'
            ),
            obs3="created and completed both fulfill",
            obs4="one row per payout_id; completed once; second payee adds",
            obs5="one row per payout_id; submit once; second payee adds",
            fail_obs="FAILED test_submit_not_completed_double - po_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_po(r.payout_id, cents)  # counted every submit retry",
            skip_new=(
                "    if not paid_today(payee_id):\n"
                "        fulfill_po(r.payout_id, cents)"
            ),
            obs7="webhook still fulfills; new payout same day dropped.",
            still_fail_obs="FAILED test_submit_not_completed_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def submit_po(payee_id, cents, ref):\n"
                "    if not claim_po_ref(ref):\n"
                "        return existing_by_ref(ref)\n"
                "    r = payoneer.masspayout.submit(payee=payee_id, amount=cents, client_reference_id=ref)\n"
                "    return r\n"
            ),
            rewrite_src_obs="unique client_reference_id; submit does not fulfill",
            rewrite_hook=(
                "def on_po(ev):\n"
                '    if ev.get("type") != "payout_completed":\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["payout_id"]\n'
                "    if not claim_po(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_po(pid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same payout_id.",
            rewrite_hook_obs="PK payout_id",
            ddl=(
                "CREATE TABLE till_po_payout (\n"
                "  payout_id text PRIMARY KEY,\n"
                "  client_ref text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payout_id",
            test2_body=(
                "def test_second_payee():\n"
                '    submit_po("py_a", 100, ref="cra")\n'
                '    on_po(po_ev("payout_completed", payout_id="po_a", amount=100))\n'
                '    submit_po("py_b", 40, ref="crb")\n'
                '    on_po(po_ev("payout_completed", payout_id="po_b", amount=40))\n'
                '    assert fulfill_cents("po_a") == 100 and fulfill_cents("po_b") == 40\n'
            ),
            psql_rows="po_1\npo_a\npo_b",
            residual="payout_failed after completed last-write",
            grep_pat="failed",
            grep_obs="src/po_payout.py: claim then insert; no status CAS",
            goal=(
                "till-po masspayout submit retried with payout_completed. "
                "PK Payoneer payout_id. Gate: tests/test_po.py."
            ),
            plan="Skip fulfill if this Payoneer payee already paid today.",
            outcome=(
                "Submit+completed triple-rowed. Payee-day skip left webhook unguarded. "
                "Plan change: unique client_reference_id + PK payout_id. Tests 2/2 + second payee + suite 8/8."
            ),
        ),
        _fail(
            slug="tipalti-submitted-vs-completed",
            surfaces="Tipalti payment submitted vs PaymentCompleted IPA",
            avoided="r64 PayPal payout_item; r113 Payoneer payout. This is Tipalti refcode vs tipalti_id",
            this_is="Tipalti submit vs PaymentCompleted",
            seed="submit retry + PaymentCompleted",
            first_apply="payee tipped today",
            plan_change="unique refcode; PK tipalti_id on PaymentCompleted",
            step_note="Payee-day 6–7; PK 8–11; second 12–13; PaymentError xfail 15–17.",
            next_note="Unused: Tipalti PaymentError after completed. Avoid payee-tipped-today skip.",
            src="src/tp_pay.py",
            hook="src/tp_ipa.py",
            test="tests/test_tp.py",
            test2="tests/test_tp_two.py",
            xfail="tests/test_tp_err.py",
            mig="tp_pay",
            table="till_tp_pay",
            pk="tipalti_id",
            rg="PaymentCompleted|refcode|tipalti|IPA",
            rg_obs=(
                "src/tp_pay.py:8: def submit_tp\n"
                "src/tp_ipa.py:6: def on_tp\n"
                "tests/test_tp.py: def test_submit_not_completed_double\n"
            ),
            test_name="submit-not-completed-double test",
            surface_read="Tipalti payment submit plus PaymentCompleted IPA",
            skip_pred="this Tipalti payee already tipped today",
            verb="fulfill",
            skip_label="payee-tipped-today skip",
            src_body=(
                "def submit_tp(payee_id, cents, refcode):\n"
                "    r = tipalti.payments.submit(payee=payee_id, amount=cents, refcode=refcode)\n"
                "    fulfill_tp(r.tipalti_id, cents)  # counted every submit retry\n"
                "    return r\n"
            ),
            hook_body=(
                "def on_tp(ev):\n"
                '    if ev["event"] in ("PaymentCompleted", "PaymentSubmitted"):\n'
                '        fulfill_tp(ev["tipalti_id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_submit_not_completed_double():\n"
                '    submit_tp("id_1", 5000, refcode="rc_1")\n'
                '    submit_tp("id_1", 5000, refcode="rc_1")\n'
                '    on_tp(tp_ev("PaymentCompleted", tipalti_id="tp_1", amount=5000))\n'
                '    assert fulfill_cents("tp_1") == 5000 and tp_rows("tp_1") == 1\n'
                "\n"
                "def test_second_payee():\n"
                '    submit_tp("id_a", 100, refcode="rca")\n'
                '    submit_tp("id_b", 40, refcode="rcb")\n'
                '    assert tp_rows(last_tp("id_a")) == 1\n'
            ),
            test_body_short="same — unique refcode; PaymentCompleted PK tipalti_id",
            obs3="submitted and completed both fulfill",
            obs4="unique refcode; completed PK; submitted no-op",
            obs5="completed once; submit once; second payee adds",
            fail_obs="FAILED test_submit_not_completed_double - tp_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_tp(r.tipalti_id, cents)  # counted every submit retry",
            skip_new=(
                "    if not tipped_today(payee_id):\n"
                "        fulfill_tp(r.tipalti_id, cents)"
            ),
            obs7="webhook still fulfills; hides missing tipalti_id PK.",
            still_fail_obs=(
                "FAILED if first event was PaymentSubmitted (should not fulfill) then Completed same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def submit_tp(payee_id, cents, refcode):\n"
                "    if not claim_tp_ref(refcode):\n"
                "        return existing_by_ref(refcode)\n"
                "    r = tipalti.payments.submit(payee=payee_id, amount=cents, refcode=refcode)\n"
                "    return r\n"
            ),
            rewrite_src_obs="unique refcode; submit does not fulfill",
            rewrite_hook=(
                "def on_tp(ev):\n"
                '    if ev.get("event") != "PaymentCompleted":\n'
                '        return {"ok": True, "skip": True}\n'
                '    tid = ev["tipalti_id"]\n'
                "    if not claim_tp(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_tp(tid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            rewrite_hook_obs="PK tipalti_id",
            ddl=(
                "CREATE TABLE till_tp_pay (\n"
                "  tipalti_id text PRIMARY KEY,\n"
                "  refcode text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK tipalti_id",
            test2_body=(
                "def test_second_payee():\n"
                '    submit_tp("id_a", 100, refcode="rca")\n'
                '    on_tp(tp_ev("PaymentCompleted", tipalti_id="tp_a", amount=100))\n'
                '    submit_tp("id_b", 40, refcode="rcb")\n'
                '    on_tp(tp_ev("PaymentCompleted", tipalti_id="tp_b", amount=40))\n'
                '    assert fulfill_cents("tp_a") == 100 and fulfill_cents("tp_b") == 40\n'
            ),
            xfail_label="PaymentError after completed",
            xfail_body=(
                "def test_completed_then_error():\n"
                '    on_tp(tp_ev("PaymentCompleted", tipalti_id="tp_p", amount=5000))\n'
                '    on_tp(tp_ev("PaymentError", tipalti_id="tp_p", amount=5000))\n'
                '    assert fulfill_cents("tp_p") == 0 or tp_state("tp_p") == "error"\n'
            ),
            xfail_fail_obs="FAILED test_completed_then_error - PaymentError skipped; cents still 5000\n1 failed",
            xfail_old="def test_completed_then_error():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: PaymentError after completed must reverse claimed tipalti_id", strict=True)\n'
                "def test_completed_then_error():"
            ),
            xfail_patch_obs="xfailed completed then error",
            goal=(
                "till-tp payment submit and PaymentCompleted both fulfilled tp_1. "
                "Unique refcode; PK tipalti_id on completed. Gate: tests/test_tp.py."
            ),
            plan="Skip fulfill if this Tipalti payee already tipped today.",
            outcome=(
                "Submit+completed double-fulfilled. Payee-day skip hid tipalti_id. Plan change: "
                "unique refcode; completed PK. Primary+second pass. Partial: PaymentError xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="stripe-capital-offer-vs-financing-txn",
            surfaces="Stripe Capital financing_offer.accepted vs financing_transaction.created",
            avoided="r89 Treasury outbound; r92 Connect payout. This is Capital financing_transaction id",
            this_is="Capital offer accept vs financing_transaction disbursement",
            seed="financing_offer.accepted + financing_transaction.created",
            first_apply="account financed today",
            plan_change="offer records; disbursement PK financing_transaction_id",
            step_note="Account-day 6–7; PK 8–11; second 12–13.",
            src="src/cap_offer.py",
            hook="src/cap_txn.py",
            test="tests/test_capital.py",
            test2="tests/test_capital_two.py",
            mig="cap_offer",
            table="till_cap_txn",
            pk="fin_txn_id",
            rg="financing_offer.accepted|financing_transaction.created|capital",
            rg_obs=(
                "src/cap_offer.py:8: def on_cap\n"
                "src/cap_txn.py:6: def credit_cap\n"
                "tests/test_capital.py: def test_offer_not_txn_double\n"
            ),
            test_name="offer-not-txn-double test",
            surface_read="Stripe Capital financing_offer.accepted plus financing_transaction.created",
            skip_pred="this Connect account already financed today",
            verb="credit",
            skip_label="account-financed-today skip",
            src_body=(
                "def on_cap(ev):\n"
                '    if ev.type in ("capital.financing_offer.accepted", "capital.financing_transaction.created"):\n'
                "        credit_cap(ev.data.object.id, ev.data.object.amount)\n"
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def credit_cap(oid, cents):\n"
                "    ledger.credit(oid, cents)\n"
            ),
            test_body=(
                "def test_offer_not_txn_double():\n"
                '    on_cap(cap("capital.financing_offer.accepted", id="fo_1", amount=500000, account="acct_1"))\n'
                '    on_cap(cap("capital.financing_offer.accepted", id="fo_1", amount=500000, account="acct_1"))\n'
                '    on_cap(cap("capital.financing_transaction.created", id="ft_1", offer="fo_1", amount=500000))\n'
                '    assert offer_flag("fo_1") and credit_cents("ft_1") == 500000 and cap_rows("ft_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_cap(cap("capital.financing_transaction.created", id="ft_a", amount=100, account="acct_a"))\n'
                '    on_cap(cap("capital.financing_transaction.created", id="ft_b", amount=40, account="acct_b"))\n'
                '    assert credit_cents("ft_a") == 100 and credit_cents("ft_b") == 40\n'
            ),
            obs3="offer accepted and financing_transaction both credit",
            obs4="offer records; txn PK financing_transaction_id",
            obs5="txn once; offer no extra credit; second account adds",
            fail_obs="FAILED test_offer_not_txn_double - cap_rows 3 == 1 or credited fo_1\n1 failed, 1 passed",
            skip_old="        credit_cap(ev.data.object.id, ev.data.object.amount)",
            skip_new=(
                "        if not financed_today(ev.data.object.get('account') or ev.data.object.id):\n"
                "            credit_cap(ev.data.object.id, ev.data.object.amount)"
            ),
            obs7="financing_transaction still credits; new offer same day dropped.",
            still_fail_obs="FAILED test_offer_not_txn_double - txn still adds or offer credits\n1 failed, 1 passed",
            rewrite_src=(
                "def on_cap(ev):\n"
                "    t = ev.type\n"
                "    obj = ev.data.object\n"
                '    if t == "capital.financing_offer.accepted":\n'
                "        flag_offer(obj.id, account=obj.get('account'))\n"
                '        return {"ok": True, "offer": True}\n'
                '    if t == "capital.financing_transaction.created":\n'
                "        if not claim_cap(obj.id):\n"
                '            return {"ok": True, "dup": True}\n'
                "        credit_cap(obj.id, obj.amount, offer=obj.get('financing_offer'))\n"
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="offer records; txn PK fin_txn_id",
            rewrite_hook=(
                "def claim_cap(tid):\n"
                '    cur = db.execute("INSERT INTO till_cap_txn (fin_txn_id) VALUES (%s) ON CONFLICT DO NOTHING", [tid])\n'
                "    return cur.rowcount == 1\n"
            ),
            obs9="claim helper.",
            rewrite_hook_obs="PK fin_txn_id",
            ddl=(
                "CREATE TABLE till_cap_txn (\n"
                "  fin_txn_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK fin_txn_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_cap(cap("capital.financing_transaction.created", id="ft_a", amount=100, account="acct_a"))\n'
                '    on_cap(cap("capital.financing_transaction.created", id="ft_b", amount=40, account="acct_b"))\n'
                '    assert credit_cents("ft_a") == 100 and credit_cents("ft_b") == 40\n'
            ),
            psql_rows="ft_1\nft_a\nft_b",
            residual="financing_transaction.reversed after created last-write",
            grep_pat="reversed",
            grep_obs="src/cap_offer.py: claim then insert; no reverse",
            goal=(
                "till-cap financing_offer.accepted and financing_transaction.created both credited fo_1. "
                "Offer records; PK financing_transaction id. Gate: tests/test_capital.py."
            ),
            plan="Skip credit if this Connect account already financed today.",
            outcome=(
                "Offer+txn double-credited. Account-day skip left txn unguarded. "
                "Plan change: offer records; PK fin_txn_id. Tests 2/2 + second account + suite 8/8."
            ),
        ),
        _fail(
            slug="square-loyalty-accumulate-vs-webhook",
            surfaces="Square Loyalty AccumulatePoints vs loyalty.account.updated",
            avoided="r70 Square gift LOAD; r75 Terminal Checkout. This is loyalty account_id + idempotency_key",
            this_is="Square Loyalty accumulate vs account.updated",
            seed="AccumulatePoints retry + loyalty.account.updated",
            first_apply="buyer accumulated today",
            plan_change="unique ik; PK loyalty_event_id; account.updated no extra points",
            step_note="Buyer-day 6–7; PK 8–11; second 12–13; AdjustPoints xfail 15–17.",
            next_note="Unused: Square Loyalty AdjustPoints after accumulate. Avoid buyer-accumulated-today skip.",
            src="src/sq_loyal.py",
            hook="src/sq_loyal_hook.py",
            test="tests/test_sq_loyal.py",
            test2="tests/test_sq_loyal_two.py",
            xfail="tests/test_sq_loyal_adj.py",
            mig="sq_loyal",
            table="till_sq_loyal",
            pk="event_id",
            rg="AccumulatePoints|loyalty.account.updated|loyalty_event",
            rg_obs=(
                "src/sq_loyal.py:8: def accumulate_sq\n"
                "src/sq_loyal_hook.py:6: def on_sq_loyal\n"
                "tests/test_sq_loyal.py: def test_accumulate_not_updated_double\n"
            ),
            test_name="accumulate-not-updated-double test",
            surface_read="Square Loyalty AccumulatePoints plus loyalty.account.updated",
            skip_pred="this Square buyer already accumulated today",
            verb="grant",
            skip_label="buyer-accumulated-today skip",
            src_body=(
                "def accumulate_sq(account_id, points, ik):\n"
                "    ev = square.loyalty.accounts.accumulate_points(account_id, points=points, idempotency_key=ik)\n"
                "    grant_pts(account_id, points)  # counted every accumulate retry\n"
                "    return ev\n"
            ),
            hook_body=(
                "def on_sq_loyal(ev):\n"
                '    if ev["type"] == "loyalty.account.updated":\n'
                '        grant_pts(ev["data"]["object"]["loyalty_account"]["id"], ev["data"]["object"].get("points", 0))\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_accumulate_not_updated_double():\n"
                '    accumulate_sq("loy_1", 50, ik="ik_1")\n'
                '    accumulate_sq("loy_1", 50, ik="ik_1")\n'
                '    on_sq_loyal(sq_ev("loyalty.account.updated", account="loy_1", event_id="le_1", points=50))\n'
                '    assert pts("loy_1") == 50 and sq_loyal_rows("le_1") == 1\n'
                "\n"
                "def test_second_buyer():\n"
                '    accumulate_sq("loy_a", 10, ik="ika")\n'
                '    accumulate_sq("loy_b", 4, ik="ikb")\n'
                '    assert pts("loy_a") == 10 and pts("loy_b") == 4\n'
            ),
            test_body_short="same — unique ik; PK loyalty_event_id; updated no extra",
            obs3="account.updated grants again",
            obs4="unique ik; event PK; updated no extra points",
            obs5="accumulate once; updated no second; second buyer adds",
            fail_obs="FAILED test_accumulate_not_updated_double - pts 150 or rows 3\n1 failed, 1 passed",
            skip_old="    grant_pts(account_id, points)  # counted every accumulate retry",
            skip_new=(
                "    if not accumulated_today(account_id):\n"
                "        grant_pts(account_id, points)"
            ),
            obs7="webhook still grants; hides missing event_id PK.",
            still_fail_obs=(
                "FAILED if first event was account.updated without event id (should not grant)\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def accumulate_sq(account_id, points, ik):\n"
                "    if not claim_sq_loyal_ik(ik):\n"
                "        return existing_by_ik(ik)\n"
                "    ev = square.loyalty.accounts.accumulate_points(account_id, points=points, idempotency_key=ik)\n"
                "    if not claim_sq_loyal(ev.id):\n"
                "        return ev\n"
                "    grant_pts(account_id, points, event=ev.id)\n"
                "    return ev\n"
            ),
            rewrite_src_obs="unique ik + claim event_id",
            rewrite_hook=(
                "def on_sq_loyal(ev):\n"
                '    if ev.get("type") != "loyalty.account.updated":\n'
                '        return {"ok": True, "skip": True}\n'
                '    return {"ok": True, "projection": True}\n'
            ),
            rewrite_hook_obs="account.updated projection only",
            ddl=(
                "CREATE TABLE till_sq_loyal (\n"
                "  event_id text PRIMARY KEY,\n"
                "  ik text UNIQUE,\n"
                "  points int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK event_id",
            test2_body=(
                "def test_second_buyer():\n"
                '    accumulate_sq("loy_a", 10, ik="ika")\n'
                '    accumulate_sq("loy_b", 4, ik="ikb")\n'
                '    assert pts("loy_a") == 10 and pts("loy_b") == 4\n'
            ),
            xfail_label="AdjustPoints after accumulate",
            xfail_body=(
                "def test_adjust_after_accumulate():\n"
                '    accumulate_sq("loy_p", 50, ik="ikp")\n'
                '    square.loyalty.accounts.adjust_points("loy_p", points=-50, reason="correction")\n'
                '    assert pts("loy_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_adjust_after_accumulate - adjust not wired; pts still 50\n1 failed",
            xfail_old="def test_adjust_after_accumulate():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: AdjustPoints must apply after accumulate; not ignored", strict=True)\n'
                "def test_adjust_after_accumulate():"
            ),
            xfail_patch_obs="xfailed adjust after accumulate",
            goal=(
                "till-sq-loyal AccumulatePoints and loyalty.account.updated both granted loy_1. "
                "Unique ik; PK loyalty_event_id. Gate: tests/test_sq_loyal.py."
            ),
            plan="Skip grant if this Square buyer already accumulated today.",
            outcome=(
                "Accumulate+updated double-granted. Buyer-day skip hid event_id. Plan change: "
                "unique ik; event PK; updated projection. Primary+second pass. Partial: AdjustPoints xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="galileo-auth-vs-posted",
            surfaces="Galileo authorization vs posted transaction",
            avoided="r65 Issuing closed+txn; r102 Issuing request vs capture; r111 Bond. This is Galileo auth_id vs posted pmt_id",
            this_is="Galileo auth hold vs posted pmt",
            seed="auth event + posted event same cad",
            first_apply="card posted today",
            plan_change="auth hold; posted PK pmt_id",
            step_note="Card-day 6–7; PK 8–11; second 12–13.",
            src="src/gal_auth.py",
            hook="src/gal_posted.py",
            test="tests/test_gal.py",
            test2="tests/test_gal_two.py",
            mig="gal_auth",
            table="till_gal_pmt",
            pk="pmt_id",
            rg="auth_id|pmt_id|galileo|posted",
            rg_obs=(
                "src/gal_auth.py:8: def on_gal\n"
                "src/gal_posted.py:6: def debit_gal\n"
                "tests/test_gal.py: def test_auth_not_posted_double\n"
            ),
            test_name="auth-not-posted-double test",
            surface_read="Galileo authorization plus posted transaction",
            skip_pred="this Galileo card already posted today",
            verb="debit",
            skip_label="card-posted-today skip",
            src_body=(
                "def on_gal(ev):\n"
                '    if ev["type"] in ("auth", "posted", "setl"):\n'
                '        debit_gal(ev["id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_gal(oid, cents):\n"
                "    ledger.debit(oid, cents)\n"
            ),
            test_body=(
                "def test_auth_not_posted_double():\n"
                '    on_gal(gal("auth", id="a_1", amount=5000, cad="cad_1"))\n'
                '    on_gal(gal("auth", id="a_1", amount=5000, cad="cad_1"))\n'
                '    on_gal(gal("posted", id="p_1", auth="a_1", amount=5000, cad="cad_1"))\n'
                '    assert hold_cents("a_1") == 0 and posted_cents("p_1") == 5000 and gal_rows("p_1") == 1\n'
                "\n"
                "def test_second_cad():\n"
                '    on_gal(gal("posted", id="p_a", amount=100, cad="cad_a"))\n'
                '    on_gal(gal("posted", id="p_b", amount=40, cad="cad_b"))\n'
                '    assert posted_cents("p_a") == 100 and posted_cents("p_b") == 40\n'
            ),
            obs3="auth and posted both debit",
            obs4="auth hold; posted PK pmt_id",
            obs5="posted once; auth no extra debit; second cad adds",
            fail_obs="FAILED test_auth_not_posted_double - gal_rows 3 == 1 or posted on a_1\n1 failed, 1 passed",
            skip_old='        debit_gal(ev["id"], ev["amount"])',
            skip_new=(
                '        if not posted_today(ev.get("cad") or ev["id"]):\n'
                '            debit_gal(ev["id"], ev["amount"])'
            ),
            obs7="posted still debits; new cad same day dropped.",
            still_fail_obs="FAILED test_auth_not_posted_double - auth still debits or posted adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_gal(ev):\n"
                '    t = ev["type"]\n'
                '    if t == "auth":\n'
                '        hold_gal(ev["id"], ev["amount"], cad=ev.get("cad"))\n'
                '        return {"ok": True, "hold": True}\n'
                '    if t == "posted":\n'
                '        pid = ev["id"]\n'
                "        if not claim_gal(pid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        release_hold(ev.get("auth"))\n'
                '        debit_gal(pid, ev["amount"])\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="auth hold; posted PK pmt_id",
            rewrite_hook=(
                "def claim_gal(pid):\n"
                '    cur = db.execute("INSERT INTO till_gal_pmt (pmt_id) VALUES (%s) ON CONFLICT DO NOTHING", [pid])\n'
                "    return cur.rowcount == 1\n"
            ),
            obs9="claim helper.",
            rewrite_hook_obs="PK pmt_id",
            ddl=(
                "CREATE TABLE till_gal_pmt (\n"
                "  pmt_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK pmt_id",
            test2_body=(
                "def test_second_cad():\n"
                '    on_gal(gal("posted", id="p_a", amount=100, cad="cad_a"))\n'
                '    on_gal(gal("posted", id="p_b", amount=40, cad="cad_b"))\n'
                '    assert posted_cents("p_a") == 100 and posted_cents("p_b") == 40\n'
            ),
            psql_rows="p_1\np_a\np_b",
            residual="backout after posted last-write",
            grep_pat="backout",
            grep_obs="src/gal_auth.py: claim then insert; no backout reverse",
            goal=(
                "till-gal auth and posted both debited a_1. "
                "Auth hold; posted PK pmt_id. Gate: tests/test_gal.py."
            ),
            plan="Skip debit if this Galileo card already posted today.",
            outcome=(
                "Auth+posted double-debited. Card-day skip left posted unguarded. "
                "Plan change: auth hold; PK pmt_id. Tests 2/2 + second cad + suite 8/8."
            ),
        ),
        _fail(
            slug="tokenio-payment-vs-webhook",
            surfaces="Token.io payment create vs PAYMENT_STATUS_CHANGED_SUCCESS",
            avoided="r104 TrueLayer executed; r100 Plaid transfer. This is Token.io paymentId",
            this_is="Token.io create vs success webhook",
            seed="payment create retry + PAYMENT_STATUS_CHANGED SUCCESS",
            first_apply="user paid today",
            plan_change="unique refId; PK paymentId on SUCCESS",
            step_note="User-day 6–7; PK 8–11; second 12–13; FAILED after SUCCESS xfail 15–17.",
            next_note="Unused: Token.io FAILED after SUCCESS. Avoid user-paid-today skip.",
            src="src/tok_pay.py",
            hook="src/tok_hook.py",
            test="tests/test_tok.py",
            test2="tests/test_tok_two.py",
            xfail="tests/test_tok_fail.py",
            mig="tok_pay",
            table="till_tok_pay",
            pk="payment_id",
            rg="PAYMENT_STATUS_CHANGED|token.io|refId|paymentId",
            rg_obs=(
                "src/tok_pay.py:8: def create_tok\n"
                "src/tok_hook.py:6: def on_tok\n"
                "tests/test_tok.py: def test_create_not_success_double\n"
            ),
            test_name="create-not-success-double test",
            surface_read="Token.io payment create plus PAYMENT_STATUS_CHANGED SUCCESS",
            skip_pred="this Token.io user already paid today",
            verb="fulfill",
            skip_label="user-paid-today skip",
            src_body=(
                "def create_tok(user_id, cents, ref):\n"
                "    p = tokenio.payments.create(user=user_id, amount=cents, refId=ref)\n"
                "    fulfill_tok(p.paymentId, cents)  # counted every create retry\n"
                "    return p\n"
            ),
            hook_body=(
                "def on_tok(ev):\n"
                '    if ev["type"] == "PAYMENT_STATUS_CHANGED":\n'
                '        fulfill_tok(ev["paymentId"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_success_double():\n"
                '    create_tok("u_1", 5000, ref="r_1")\n'
                '    create_tok("u_1", 5000, ref="r_1")\n'
                '    on_tok(tok_ev("PAYMENT_STATUS_CHANGED", paymentId="tp_1", amount=5000, status="SUCCESS"))\n'
                '    assert fulfill_cents("tp_1") == 5000 and tok_rows("tp_1") == 1\n'
                "\n"
                "def test_second_user():\n"
                '    create_tok("u_a", 100, ref="ra")\n'
                '    create_tok("u_b", 40, ref="rb")\n'
                '    assert tok_rows(last_p("u_a")) == 1\n'
            ),
            test_body_short="same — unique refId; SUCCESS PK paymentId",
            obs3="status changed always fulfills",
            obs4="unique refId; SUCCESS PK; INITIATED no-op",
            obs5="SUCCESS once; create once; second user adds",
            fail_obs="FAILED test_create_not_success_double - tok_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_tok(p.paymentId, cents)  # counted every create retry",
            skip_new=(
                "    if not paid_today(user_id):\n"
                "        fulfill_tok(p.paymentId, cents)"
            ),
            obs7="webhook still fulfills; hides missing paymentId PK.",
            still_fail_obs=(
                "FAILED if first status was INITIATED (should not fulfill) then SUCCESS same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def create_tok(user_id, cents, ref):\n"
                "    if not claim_tok_ref(ref):\n"
                "        return existing_by_ref(ref)\n"
                "    p = tokenio.payments.create(user=user_id, amount=cents, refId=ref)\n"
                "    return p\n"
            ),
            rewrite_src_obs="unique refId; create does not fulfill",
            rewrite_hook=(
                "def on_tok(ev):\n"
                '    if ev.get("type") != "PAYMENT_STATUS_CHANGED" or ev.get("status") != "SUCCESS":\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["paymentId"]\n'
                "    if not claim_tok(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_tok(pid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            rewrite_hook_obs="PK payment_id on SUCCESS",
            ddl=(
                "CREATE TABLE till_tok_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  ref_id text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_user():\n"
                '    create_tok("u_a", 100, ref="ra")\n'
                '    on_tok(tok_ev("PAYMENT_STATUS_CHANGED", paymentId="tp_a", amount=100, status="SUCCESS"))\n'
                '    create_tok("u_b", 40, ref="rb")\n'
                '    on_tok(tok_ev("PAYMENT_STATUS_CHANGED", paymentId="tp_b", amount=40, status="SUCCESS"))\n'
                '    assert fulfill_cents("tp_a") == 100 and fulfill_cents("tp_b") == 40\n'
            ),
            xfail_label="FAILED after SUCCESS",
            xfail_body=(
                "def test_success_then_failed():\n"
                '    on_tok(tok_ev("PAYMENT_STATUS_CHANGED", paymentId="tp_p", amount=5000, status="SUCCESS"))\n'
                '    on_tok(tok_ev("PAYMENT_STATUS_CHANGED", paymentId="tp_p", amount=5000, status="FAILED"))\n'
                '    assert fulfill_cents("tp_p") == 0 or tok_state("tp_p") == "FAILED"\n'
            ),
            xfail_fail_obs="FAILED test_success_then_failed - FAILED skipped; cents still 5000\n1 failed",
            xfail_old="def test_success_then_failed():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: FAILED after SUCCESS must reverse claimed paymentId", strict=True)\n'
                "def test_success_then_failed():"
            ),
            xfail_patch_obs="xfailed SUCCESS then FAILED",
            goal=(
                "till-tok payment create and PAYMENT_STATUS_CHANGED SUCCESS both fulfilled tp_1. "
                "Unique refId; PK paymentId on SUCCESS. Gate: tests/test_tok.py."
            ),
            plan="Skip fulfill if this Token.io user already paid today.",
            outcome=(
                "Create+SUCCESS double-fulfilled. User-day skip hid paymentId. Plan change: "
                "unique refId; SUCCESS PK. Primary+second pass. Partial: FAILED after SUCCESS xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="billcom-pay-vs-webhook",
            surfaces="Bill.com PayBills vs vendorPayment.paid webhook",
            avoided="r64 PayPal payout_item; r113 Payoneer. This is Bill.com vendorPayment id",
            this_is="Bill.com PayBills vs vendorPayment.paid",
            seed="PayBills retry + vendorPayment.paid",
            first_apply="vendor paid today",
            plan_change="unique requestId; PK vendorPayment_id on paid",
            step_note="Vendor-day 6–7; PK 8–11; second 12–13.",
            src="src/bill_pay.py",
            hook="src/bill_hook.py",
            test="tests/test_bill.py",
            test2="tests/test_bill_two.py",
            mig="bill_pay",
            table="till_bill_vp",
            pk="vp_id",
            rg="PayBills|vendorPayment|bill.com|requestId",
            rg_obs=(
                "src/bill_pay.py:8: def pay_bills\n"
                "src/bill_hook.py:6: def on_bill\n"
                "tests/test_bill.py: def test_pay_not_webhook_double\n"
            ),
            test_name="pay-not-webhook-double test",
            surface_read="Bill.com PayBills plus vendorPayment.paid",
            skip_pred="this Bill.com vendor already paid today",
            verb="fulfill",
            skip_label="vendor-paid-today skip",
            src_body=(
                "def pay_bills(vendor_id, cents, rid):\n"
                "    r = billcom.PayBills(vendor=vendor_id, amount=cents, requestId=rid)\n"
                "    fulfill_bill(r.vendorPaymentId, cents)  # counted every pay retry\n"
                "    return r\n"
            ),
            hook_body=(
                "def on_bill(ev):\n"
                '    if ev["type"] in ("vendorPayment.paid", "vendorPayment.created"):\n'
                '        fulfill_bill(ev["id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_pay_not_webhook_double():\n"
                '    pay_bills("v_1", 5000, rid="rid_1")\n'
                '    pay_bills("v_1", 5000, rid="rid_1")\n'
                '    on_bill(bill_ev("vendorPayment.paid", id="vp_1", amount=5000))\n'
                '    assert fulfill_cents("vp_1") == 5000 and bill_rows("vp_1") == 1\n'
                "\n"
                "def test_second_vendor():\n"
                '    pay_bills("v_a", 100, rid="ra")\n'
                '    pay_bills("v_b", 40, rid="rb")\n'
                '    assert bill_rows(last_vp("v_a")) == 1\n'
            ),
            obs3="created and paid both fulfill",
            obs4="one row per vp_id; paid once; second vendor adds",
            obs5="one row per vp_id; pay once; second vendor adds",
            fail_obs="FAILED test_pay_not_webhook_double - bill_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_bill(r.vendorPaymentId, cents)  # counted every pay retry",
            skip_new=(
                "    if not paid_today(vendor_id):\n"
                "        fulfill_bill(r.vendorPaymentId, cents)"
            ),
            obs7="webhook still fulfills; new pay same day dropped.",
            still_fail_obs="FAILED test_pay_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def pay_bills(vendor_id, cents, rid):\n"
                "    if not claim_bill_rid(rid):\n"
                "        return existing_by_rid(rid)\n"
                "    r = billcom.PayBills(vendor=vendor_id, amount=cents, requestId=rid)\n"
                "    return r\n"
            ),
            rewrite_src_obs="unique requestId; PayBills does not fulfill",
            rewrite_hook=(
                "def on_bill(ev):\n"
                '    if ev.get("type") != "vendorPayment.paid":\n'
                '        return {"ok": True, "skip": True}\n'
                '    vid = ev["id"]\n'
                "    if not claim_bill(vid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_bill(vid, ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same vp_id.",
            rewrite_hook_obs="PK vp_id",
            ddl=(
                "CREATE TABLE till_bill_vp (\n"
                "  vp_id text PRIMARY KEY,\n"
                "  request_id text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK vp_id",
            test2_body=(
                "def test_second_vendor():\n"
                '    pay_bills("v_a", 100, rid="ra")\n'
                '    on_bill(bill_ev("vendorPayment.paid", id="vp_a", amount=100))\n'
                '    pay_bills("v_b", 40, rid="rb")\n'
                '    on_bill(bill_ev("vendorPayment.paid", id="vp_b", amount=40))\n'
                '    assert fulfill_cents("vp_a") == 100 and fulfill_cents("vp_b") == 40\n'
            ),
            psql_rows="vp_1\nvp_a\nvp_b",
            residual="vendorPayment.void after paid last-write",
            grep_pat="void",
            grep_obs="src/bill_pay.py: claim then insert; no void",
            goal=(
                "till-bill PayBills retried with vendorPayment.paid. "
                "PK Bill.com vendorPayment id. Gate: tests/test_bill.py."
            ),
            plan="Skip fulfill if this Bill.com vendor already paid today.",
            outcome=(
                "Pay+paid triple-rowed. Vendor-day skip left webhook unguarded. "
                "Plan change: unique requestId + PK vp_id. Tests 2/2 + second vendor + suite 8/8."
            ),
        ),
        _fail(
            slug="toast-order-vs-payment",
            surfaces="Toast POS order.updated vs payment.updated CAPTURED",
            avoided="r63 Square PayOrder; r75 Terminal Checkout. This is Toast paymentGuid",
            this_is="Toast order closed vs payment captured",
            seed="order CLOSED + payment CAPTURED both fulfill",
            first_apply="check closed today",
            plan_change="order records; fulfill PK paymentGuid on CAPTURED",
            step_note="Check-day 6–7; PK 8–11; second 12–13; VOIDED xfail 15–17.",
            next_note="Unused: Toast payment VOIDED after CAPTURED. Avoid check-closed-today skip.",
            src="src/toast_order.py",
            hook="src/toast_pay.py",
            test="tests/test_toast.py",
            test2="tests/test_toast_two.py",
            xfail="tests/test_toast_void.py",
            mig="toast_order",
            table="till_toast_pay",
            pk="payment_guid",
            rg="paymentGuid|order.updated|CAPTURED|toasttab",
            rg_obs=(
                "src/toast_order.py:8: def on_toast\n"
                "src/toast_pay.py:6: def fulfill_toast\n"
                "tests/test_toast.py: def test_order_not_payment_double\n"
            ),
            test_name="order-not-payment-double test",
            surface_read="Toast order.updated plus payment.updated CAPTURED",
            skip_pred="this Toast check already closed today",
            verb="fulfill",
            skip_label="check-closed-today skip",
            src_body=(
                "def on_toast(ev):\n"
                '    if ev["eventType"] in ("order_updated", "payment_updated"):\n'
                '        fulfill_toast(ev["guid"], ev.get("amount", 0))\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def fulfill_toast(guid, cents):\n"
                "    ledger.credit(guid, cents)\n"
            ),
            test_body=(
                "def test_order_not_payment_double():\n"
                '    on_toast(toast("order_updated", guid="ord_1", amount=5000, state="CLOSED"))\n'
                '    on_toast(toast("order_updated", guid="ord_1", amount=5000, state="CLOSED"))\n'
                '    on_toast(toast("payment_updated", guid="pay_1", order="ord_1", amount=5000, type="CAPTURED"))\n'
                '    assert closed("ord_1") and fulfill_cents("pay_1") == 5000 and toast_rows("pay_1") == 1\n'
                "\n"
                "def test_second_check():\n"
                '    on_toast(toast("payment_updated", guid="pay_a", amount=100, type="CAPTURED"))\n'
                '    on_toast(toast("payment_updated", guid="pay_b", amount=40, type="CAPTURED"))\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            test_body_short="same — order records; CAPTURED PK paymentGuid",
            obs3="order closed and payment captured both fulfill",
            obs4="order records; CAPTURED PK paymentGuid",
            obs5="payment once; order no extra; second check adds",
            fail_obs="FAILED test_order_not_payment_double - toast_rows 3 == 1 or credited ord_1\n1 failed, 1 passed",
            skip_old='        fulfill_toast(ev["guid"], ev.get("amount", 0))',
            skip_new=(
                '        if not closed_today(ev.get("checkGuid") or ev["guid"]):\n'
                '            fulfill_toast(ev["guid"], ev.get("amount", 0))'
            ),
            obs7="second check ok; hides missing paymentGuid PK.",
            still_fail_obs=(
                "FAILED if first event was order CLOSED (should record not fulfill) then CAPTURED same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_toast(ev):\n"
                '    t = ev["eventType"]\n'
                '    if t == "order_updated" and ev.get("state") == "CLOSED":\n'
                '        close_check(ev["guid"])\n'
                '        return {"ok": True, "closed": True}\n'
                '    if t == "payment_updated" and ev.get("type") == "CAPTURED":\n'
                '        gid = ev["guid"]\n'
                "        if not claim_toast(gid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        fulfill_toast(gid, ev.get("amount", 0), order=ev.get("order"))\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="order records; CAPTURED PK paymentGuid",
            rewrite_hook=(
                "def claim_toast(gid):\n"
                '    cur = db.execute("INSERT INTO till_toast_pay (payment_guid) VALUES (%s) ON CONFLICT DO NOTHING", [gid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK payment_guid",
            ddl=(
                "CREATE TABLE till_toast_pay (\n"
                "  payment_guid text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payment_guid",
            test2_body=(
                "def test_second_check():\n"
                '    on_toast(toast("payment_updated", guid="pay_a", amount=100, type="CAPTURED"))\n'
                '    on_toast(toast("payment_updated", guid="pay_b", amount=40, type="CAPTURED"))\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            xfail_label="VOIDED after CAPTURED",
            xfail_body=(
                "def test_captured_then_voided():\n"
                '    on_toast(toast("payment_updated", guid="pay_p", amount=5000, type="CAPTURED"))\n'
                '    on_toast(toast("payment_updated", guid="pay_p", amount=5000, type="VOIDED"))\n'
                '    assert fulfill_cents("pay_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_captured_then_voided - VOIDED skipped; cents still 5000\n1 failed",
            xfail_old="def test_captured_then_voided():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: VOIDED after CAPTURED must reverse claimed paymentGuid", strict=True)\n'
                "def test_captured_then_voided():"
            ),
            xfail_patch_obs="xfailed CAPTURED then VOIDED",
            goal=(
                "till-toast order CLOSED and payment CAPTURED both fulfilled ord_1. "
                "Order records; PK paymentGuid on CAPTURED. Gate: tests/test_toast.py."
            ),
            plan="Skip fulfill if this Toast check already closed today.",
            outcome=(
                "Order+payment double-fulfilled. Check-day skip hid paymentGuid. Plan change: "
                "order records; CAPTURED PK. Primary+second pass. Partial: VOIDED xfail handoff."
            ),
        ),
    )
)
