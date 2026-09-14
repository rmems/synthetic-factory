"""Plants r100–r105 (pairs 2–7)."""

from mill_plants import _ok, _fail

MORE = []

MORE.append(
    (
        _ok(
            slug="plaid-transfer-vs-webhook",
            surfaces="Plaid /transfer/create vs TRANSFER_EVENTS_UPDATE",
            avoided="r13 Treasury inbound; r85 Wise poll. This is Plaid transfer_id",
            this_is="Plaid transfer create vs webhook posted",
            seed="transfer create retry + TRANSFER_EVENTS_UPDATE posted",
            first_apply="account transferred today",
            plan_change="unique authorization_id; PK transfer_id on posted",
            step_note="Account-day 6–7; PK 8–11; second 12–13.",
            src="src/plaid_xfer.py",
            hook="src/plaid_hook.py",
            test="tests/test_plaid_xfer.py",
            test2="tests/test_plaid_xfer_two.py",
            mig="plaid_xfer",
            table="till_plaid_xfer",
            pk="transfer_id",
            rg="transfer/create|TRANSFER_EVENTS_UPDATE|authorization_id|plaid.transfer",
            rg_obs=(
                "src/plaid_xfer.py:8: def create_xfer\n"
                "src/plaid_hook.py:6: def on_plaid_xfer\n"
                "tests/test_plaid_xfer.py: def test_create_not_webhook_double\n"
            ),
            test_name="create-not-webhook-double test",
            surface_read="Plaid transfer create plus TRANSFER_EVENTS_UPDATE",
            skip_pred="this Plaid account already transferred today",
            verb="post",
            skip_label="account-transferred-today skip",
            src_body=(
                "def create_xfer(account_id, cents, auth_id):\n"
                "    t = plaid.Transfer.create(account_id=account_id, amount=cents, authorization_id=auth_id)\n"
                "    post_plaid(t.transfer_id, cents)  # counted every create retry\n"
                "    return t\n"
            ),
            hook_body=(
                "def on_plaid_xfer(ev):\n"
                '    if ev["webhook_code"] == "TRANSFER_EVENTS_UPDATE":\n'
                "        for e in ev.get('transfer_events') or [ev]:\n"
                "            post_plaid(e['transfer_id'], e.get('amount', 0))\n"
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_webhook_double():\n"
                '    create_xfer("acc_1", 5000, auth_id="auth_1")\n'
                '    create_xfer("acc_1", 5000, auth_id="auth_1")\n'
                '    on_plaid_xfer(px_ev("TRANSFER_EVENTS_UPDATE", transfer_id="tr_1", event="posted"))\n'
                '    assert posted_cents("tr_1") == 5000 and xfer_rows("tr_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    create_xfer("acc_a", 100, auth_id="aa")\n'
                '    create_xfer("acc_b", 40, auth_id="ab")\n'
                '    assert posted_cents(last_tr("acc_a")) == 100\n'
            ),
            obs3="webhook posts again",
            obs4="one row per transfer_id; webhook once; second account adds",
            obs5="one row per transfer_id; create once; second account adds",
            fail_obs="FAILED test_create_not_webhook_double - xfer_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    post_plaid(t.transfer_id, cents)  # counted every create retry",
            skip_new=(
                "    if not transferred_today(account_id):\n"
                "        post_plaid(t.transfer_id, cents)"
            ),
            obs7="webhook still posts; new transfer same day after first create dropped.",
            still_fail_obs="FAILED test_create_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def create_xfer(account_id, cents, auth_id):\n"
                "    if not claim_plaid_auth(auth_id):\n"
                "        return existing_by_auth(auth_id)\n"
                "    t = plaid.Transfer.create(account_id=account_id, amount=cents, authorization_id=auth_id)\n"
                "    if t.status != 'posted' and t.status != 'pending':\n"
                "        return t\n"
                "    if t.status == 'posted' and claim_plaid_xfer(t.transfer_id):\n"
                "        post_plaid(t.transfer_id, cents, account=account_id)\n"
                "    return t\n"
            ),
            rewrite_src_obs="unique auth + PK transfer_id on posted",
            rewrite_hook=(
                "def on_plaid_xfer(ev):\n"
                '    if ev.get("webhook_code") != "TRANSFER_EVENTS_UPDATE":\n'
                '        return {"ok": True, "skip": True}\n'
                "    for e in ev.get('transfer_events') or []:\n"
                "        if e.get('event_type') not in ('posted', 'settled'):\n"
                "            continue\n"
                "        if not claim_plaid_xfer(e['transfer_id']):\n"
                "            continue\n"
                "        post_plaid(e['transfer_id'], e.get('amount', 0))\n"
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same transfer_id.",
            rewrite_hook_obs="PK transfer_id",
            ddl=(
                "CREATE TABLE till_plaid_xfer (\n"
                "  transfer_id text PRIMARY KEY,\n"
                "  auth_id text UNIQUE,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK transfer_id",
            test2_body=(
                "def test_second_account():\n"
                '    create_xfer("acc_a", 100, auth_id="aa")\n'
                '    create_xfer("acc_b", 40, auth_id="ab")\n'
                '    assert posted_cents(last_tr("acc_a")) == 100 and posted_cents(last_tr("acc_b")) == 40\n'
            ),
            psql_rows="tr_1\ntr_a\ntr_b",
            residual="failed then posted same transfer_id last-write",
            grep_pat="failed",
            grep_obs="src/plaid_xfer.py: claim then insert; no status CAS",
            goal=(
                "till-plaid Transfer.create retried with TRANSFER_EVENTS_UPDATE posted. "
                "PK Plaid transfer_id. Gate: tests/test_plaid_xfer.py."
            ),
            plan="Skip post if this Plaid account already transferred today.",
            outcome=(
                "Create+webhook triple-rowed. Account-day skip left webhook unguarded. "
                "Plan change: unique auth + PK transfer_id. Tests 2/2 + second account + suite 8/8."
            ),
        ),
        _fail(
            slug="unit-book-vs-ach",
            surfaces="Unit.co BookPayment vs ReceivedAchTransaction",
            avoided="r13 inbound_transfer; r69 received_credit. This is Unit book vs ACH",
            this_is="Unit.co book payment vs inbound ACH",
            seed="BookPayment + ReceivedAch both credit deposit account",
            first_apply="account credited today",
            plan_change="PK transaction_id by type; book and ACH are distinct ids",
            step_note="Account-day 6–7; PK 8–11; second 12–13; ACH return xfail 15–17.",
            next_note="Unused: Unit ACH Returned after ReceivedAch. Avoid account-credited-today skip.",
            src="src/unit_pay.py",
            hook="src/unit_ach.py",
            test="tests/test_unit.py",
            test2="tests/test_unit_two.py",
            xfail="tests/test_unit_return.py",
            mig="unit_pay",
            table="till_unit_txn",
            pk="transaction_id",
            rg="BookPayment|ReceivedAch|originatingAch|unit.co",
            rg_obs=(
                "src/unit_pay.py:8: def on_unit\n"
                "src/unit_ach.py:6: def credit_unit\n"
                "tests/test_unit.py: def test_book_not_ach_double\n"
            ),
            test_name="book-not-ach-double test",
            surface_read="Unit.co BookPayment plus ReceivedAchTransaction",
            skip_pred="this deposit account already credited today",
            verb="credit",
            skip_label="account-credited-today skip",
            src_body=(
                "def on_unit(ev):\n"
                '    t = ev["data"]["type"]\n'
                '    if t in ("bookPayment", "receivedAchTransaction", "transaction"):\n'
                '        credit_unit(ev["data"]["id"], ev["data"]["attributes"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def credit_unit(tid, cents):\n"
                "    ledger.credit(tid, cents)\n"
            ),
            test_body=(
                "def test_book_not_ach_double():\n"
                '    on_unit(unit_ev("bookPayment", id="bk_1", amount=5000, account="dep_1"))\n'
                '    on_unit(unit_ev("bookPayment", id="bk_1", amount=5000, account="dep_1"))\n'
                '    on_unit(unit_ev("transaction", id="txn_1", related="bk_1", amount=5000))\n'
                '    assert credit_cents("dep_1") == 5000 and unit_rows("bk_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_unit(unit_ev("bookPayment", id="bk_a", amount=100, account="dep_a"))\n'
                '    on_unit(unit_ev("bookPayment", id="bk_b", amount=40, account="dep_b"))\n'
                '    assert credit_cents("dep_a") == 100 and credit_cents("dep_b") == 40\n'
            ),
            test_body_short="same — book PK id; related transaction is projection",
            obs3="related transaction.created credits again",
            obs4="credit PK book/ach id; transaction projection no-op",
            obs5="book once; related txn no second credit; second account adds",
            fail_obs="FAILED test_book_not_ach_double - unit_rows 3 == 1 or cents 10000\n1 failed, 1 passed",
            skip_old='        credit_unit(ev["data"]["id"], ev["data"]["attributes"]["amount"])',
            skip_new=(
                '        if not credited_today(ev["data"]["attributes"].get("accountId") or ev["data"]["id"]):\n'
                '            credit_unit(ev["data"]["id"], ev["data"]["attributes"]["amount"])'
            ),
            obs7="second account ok; hides missing transaction_id PK.",
            still_fail_obs=(
                "FAILED if first event was receivedAch then book same day skipped — or passes for the wrong reason\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_unit(ev):\n"
                '    t = ev["data"]["type"]\n'
                '    d = ev["data"]\n'
                '    if t in ("bookPayment", "receivedAchTransaction", "originatingAchPayment"):\n'
                '        tid = d["id"]\n'
                "        if not claim_unit(tid, t):\n"
                '            return {"ok": True, "dup": True}\n'
                '        credit_unit(tid, d["attributes"]["amount"], kind=t, account=d["attributes"].get("accountId"))\n'
                '        return {"ok": True}\n'
                '    if t == "transaction":\n'
                '        return {"ok": True, "projection": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="PK payment/ach id; transaction projection",
            rewrite_hook=(
                "def claim_unit(tid, kind):\n"
                '    cur = db.execute("INSERT INTO till_unit_txn (transaction_id, kind) VALUES (%s,%s) ON CONFLICT DO NOTHING", [tid, kind])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK transaction_id",
            ddl=(
                "CREATE TABLE till_unit_txn (\n"
                "  transaction_id text PRIMARY KEY,\n"
                "  kind text NOT NULL,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK transaction_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_unit(unit_ev("bookPayment", id="bk_a", amount=100, account="dep_a"))\n'
                '    on_unit(unit_ev("bookPayment", id="bk_b", amount=40, account="dep_b"))\n'
                '    assert credit_cents("dep_a") == 100 and credit_cents("dep_b") == 40\n'
            ),
            xfail_label="ReceivedAch then ACH return",
            xfail_body=(
                "def test_ach_then_return():\n"
                '    on_unit(unit_ev("receivedAchTransaction", id="ach_p", amount=5000, account="dep_p"))\n'
                '    on_unit(unit_ev("returnedAchTransaction", id="ret_p", related="ach_p", amount=5000, account="dep_p"))\n'
                '    assert credit_cents("dep_p") == 0 and unit_rows("ach_p") == 1\n'
            ),
            xfail_fail_obs="FAILED test_ach_then_return - returnedAch skipped; credit still 5000\n1 failed",
            xfail_old="def test_ach_then_return():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: ACH return must reverse claimed ReceivedAch; not skip as unknown type", strict=True)\n'
                "def test_ach_then_return():"
            ),
            xfail_patch_obs="xfailed ACH then return",
            goal=(
                "till-unit BookPayment and related transaction both credited dep_1. "
                "PK transaction_id; transaction is projection. Gate: tests/test_unit.py."
            ),
            plan="Skip credit if this deposit account already credited today.",
            outcome=(
                "Book+transaction double-credited. Account-day skip hid transaction_id. Plan change: "
                "PK by type; projection no-op. Primary+second pass. Partial: ACH return xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="increase-inbound-ach-vs-txn",
            surfaces="Increase inbound_ach_transfer.transfer vs transaction.created",
            avoided="r13 Stripe Treasury inbound; r69 received_credit. This is Increase inbound ACH id",
            this_is="Increase inbound ACH transfer vs transaction projection",
            seed="inbound_ach_transfer.transfer + transaction.created",
            first_apply="account inbound today",
            plan_change="PK inbound_ach_transfer_id; transaction.created projects",
            step_note="Account-day 6–7; PK 8–11; second 12–13.",
            src="src/inc_ach.py",
            hook="src/inc_txn.py",
            test="tests/test_inc.py",
            test2="tests/test_inc_two.py",
            mig="inc_ach",
            table="till_inc_ach",
            pk="inbound_id",
            rg="inbound_ach_transfer|transaction.created|increase",
            rg_obs=(
                "src/inc_ach.py:8: def on_inc\n"
                "src/inc_txn.py:6: def credit_inc\n"
                "tests/test_inc.py: def test_inbound_not_txn_double\n"
            ),
            test_name="inbound-not-txn-double test",
            surface_read="Increase inbound_ach_transfer.transfer plus transaction.created",
            skip_pred="this Increase account already inbound today",
            verb="credit",
            skip_label="account-inbound-today skip",
            src_body=(
                "def on_inc(ev):\n"
                '    if ev["category"] in ("inbound_ach_transfer.transfer", "transaction.created"):\n'
                '        credit_inc(ev["associated_object_id"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def credit_inc(oid, cents):\n"
                "    ledger.credit(oid, cents)\n"
            ),
            test_body=(
                "def test_inbound_not_txn_double():\n"
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_1", amount=5000, account="acc_1"))\n'
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_1", amount=5000, account="acc_1"))\n'
                '    on_inc(inc_ev("transaction.created", id="txn_1", associated="iat_1", amount=5000))\n'
                '    assert credit_cents("acc_1") == 5000 and inc_rows("iat_1") == 1\n'
                "\n"
                "def test_second_account():\n"
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_a", amount=100, account="acc_a"))\n'
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_b", amount=40, account="acc_b"))\n'
                '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
            ),
            obs3="transaction.created credits again",
            obs4="one row per inbound id; txn once; second account adds",
            obs5="one row per inbound id; transfer once; second account adds",
            fail_obs="FAILED test_inbound_not_txn_double - inc_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        credit_inc(ev["associated_object_id"], ev["amount"])',
            skip_new=(
                '        if not inbound_today(ev.get("account_id") or ev["associated_object_id"]):\n'
                '            credit_inc(ev["associated_object_id"], ev["amount"])'
            ),
            obs7="transaction.created still credits; new inbound same day dropped.",
            still_fail_obs="FAILED test_inbound_not_txn_double - txn still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_inc(ev):\n"
                '    cat = ev["category"]\n'
                '    if cat == "inbound_ach_transfer.transfer":\n'
                '        iid = ev["associated_object_id"]\n'
                "        if not claim_inc_ach(iid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        credit_inc(iid, ev["amount"], account=ev.get("account_id"))\n'
                '        return {"ok": True}\n'
                '    if cat == "transaction.created":\n'
                '        return {"ok": True, "projection": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="PK inbound_ach_transfer id; txn projects",
            rewrite_hook=(
                "def claim_inc_ach(iid):\n"
                '    cur = db.execute("INSERT INTO till_inc_ach (inbound_id) VALUES (%s) ON CONFLICT DO NOTHING", [iid])\n'
                "    return cur.rowcount == 1\n"
            ),
            obs9="claim helper.",
            rewrite_hook_obs="PK inbound_id",
            ddl=(
                "CREATE TABLE till_inc_ach (\n"
                "  inbound_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK inbound_id",
            test2_body=(
                "def test_second_account():\n"
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_a", amount=100, account="acc_a"))\n'
                '    on_inc(inc_ev("inbound_ach_transfer.transfer", id="iat_b", amount=40, account="acc_b"))\n'
                '    assert credit_cents("acc_a") == 100 and credit_cents("acc_b") == 40\n'
            ),
            psql_rows="iat_1\niat_a\niat_b",
            residual="inbound_ach_transfer.declined after transfer last-write",
            grep_pat="declined",
            grep_obs="src/inc_ach.py: claim then insert; no status CAS",
            goal=(
                "till-inc inbound_ach_transfer.transfer upserted iat_1 three times with "
                "transaction.created. PK inbound ACH id. Gate: tests/test_inc.py."
            ),
            plan="Skip credit if this Increase account already inbound today.",
            outcome=(
                "Transfer+txn triple-rowed. Account-day skip left txn unguarded. "
                "Plan change: PK inbound_id. Tests 2/2 + second account + suite 8/8."
            ),
        ),
        _fail(
            slug="marqeta-auth-vs-clearing",
            surfaces="Marqeta JIT authorization vs transaction.authorization.clearing",
            avoided="r65 Issuing auth.closed+txn; r102 will be Issuing request vs capture. This is Marqeta token transition",
            this_is="Marqeta JIT hold vs clearing transition",
            seed="JIT auth + authorization.clearing same token",
            first_apply="card cleared today",
            plan_change="JIT hold; clearing PK token; reversal CAS",
            step_note="Card-day 6–7; PK 8–11; second 12–13; reverse-after-partial xfail 15–17.",
            next_note="Unused: Marqeta reverse after partial clearing. Avoid card-cleared-today skip.",
            src="src/mq_jit.py",
            hook="src/mq_clear.py",
            test="tests/test_mq.py",
            test2="tests/test_mq_two.py",
            xfail="tests/test_mq_rev.py",
            mig="mq_jit",
            table="till_mq_txn",
            pk="token",
            rg="jit.gateway|authorization.clearing|marqeta|transitions",
            rg_obs=(
                "src/mq_jit.py:8: def on_mq\n"
                "src/mq_clear.py:6: def debit_mq\n"
                "tests/test_mq.py: def test_jit_not_clearing_double\n"
            ),
            test_name="jit-not-clearing-double test",
            surface_read="Marqeta JIT authorization plus authorization.clearing",
            skip_pred="this Marqeta card already cleared today",
            verb="debit",
            skip_label="card-cleared-today skip",
            src_body=(
                "def on_mq(ev):\n"
                '    if ev["type"] in ("authorization", "authorization.clearing", "gpa.credit"):\n'
                '        debit_mq(ev["token"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_mq(token, cents):\n"
                "    ledger.debit(token, cents)\n"
            ),
            test_body=(
                "def test_jit_not_clearing_double():\n"
                '    on_mq(mq("authorization", token="tok_1", amount=5000, card="c_1"))\n'
                '    on_mq(mq("authorization", token="tok_1", amount=5000, card="c_1"))\n'
                '    on_mq(mq("authorization.clearing", token="tok_1", amount=5000, card="c_1"))\n'
                '    assert hold_cents("tok_1") == 0 and posted_cents("tok_1") == 5000 and mq_rows("tok_1") == 1\n'
                "\n"
                "def test_second_card():\n"
                '    on_mq(mq("authorization.clearing", token="tok_a", amount=100, card="c_a"))\n'
                '    on_mq(mq("authorization.clearing", token="tok_b", amount=40, card="c_b"))\n'
                '    assert posted_cents("tok_a") == 100 and posted_cents("tok_b") == 40\n'
            ),
            test_body_short="same — JIT hold; clearing PK token posts once",
            obs3="authorization and clearing both debit",
            obs4="JIT hold; clearing PK token",
            obs5="clearing once; JIT no extra debit; second card adds",
            fail_obs="FAILED test_jit_not_clearing_double - mq_rows 3 == 1 or posted 10000\n1 failed, 1 passed",
            skip_old='        debit_mq(ev["token"], ev["amount"])',
            skip_new=(
                '        if not cleared_today(ev.get("card_token") or ev["token"]):\n'
                '            debit_mq(ev["token"], ev["amount"])'
            ),
            obs7="second card ok; hides missing token PK.",
            still_fail_obs=(
                "FAILED if first event was authorization (should hold not post) then clearing same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_mq(ev):\n"
                '    t = ev["type"]\n'
                '    tok = ev["token"]\n'
                '    if t == "authorization":\n'
                "        hold_mq(tok, ev['amount'])\n"
                '        return {"ok": True, "hold": True}\n'
                '    if t == "authorization.clearing":\n'
                "        if not claim_mq(tok, kind='clearing'):\n"
                '            return {"ok": True, "dup": True}\n'
                "        release_hold(tok)\n"
                "        debit_mq(tok, ev['amount'])\n"
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="JIT hold; clearing PK token",
            rewrite_hook=(
                "def claim_mq(tok, kind):\n"
                '    cur = db.execute("INSERT INTO till_mq_txn (token, kind) VALUES (%s,%s) ON CONFLICT DO NOTHING", [tok, kind])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK token",
            ddl=(
                "CREATE TABLE till_mq_txn (\n"
                "  token text PRIMARY KEY,\n"
                "  kind text NOT NULL,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK token",
            test2_body=(
                "def test_second_card():\n"
                '    on_mq(mq("authorization.clearing", token="tok_a", amount=100, card="c_a"))\n'
                '    on_mq(mq("authorization.clearing", token="tok_b", amount=40, card="c_b"))\n'
                '    assert posted_cents("tok_a") == 100 and posted_cents("tok_b") == 40\n'
            ),
            xfail_label="partial clearing then reversal",
            xfail_body=(
                "def test_partial_clear_then_reverse():\n"
                '    on_mq(mq("authorization", token="tok_p", amount=5000, card="c_p"))\n'
                '    on_mq(mq("authorization.clearing", token="tok_p", amount=1000, card="c_p"))\n'
                '    on_mq(mq("authorization.reversal", token="tok_p", amount=4000, card="c_p"))\n'
                '    assert posted_cents("tok_p") == 1000 and hold_cents("tok_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_partial_clear_then_reverse - reversal skipped because token already claimed clearing\n1 failed",
            xfail_old="def test_partial_clear_then_reverse():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: PK token blocks reversal after partial clearing; remaining hold must reverse", strict=True)\n'
                "def test_partial_clear_then_reverse():"
            ),
            xfail_patch_obs="xfailed partial clear then reverse",
            goal=(
                "till-mq JIT authorization and authorization.clearing both debited tok_1. "
                "JIT hold; clearing PK token. Gate: tests/test_mq.py."
            ),
            plan="Skip debit if this Marqeta card already cleared today.",
            outcome=(
                "Auth+clearing double-debited. Card-day skip hid token. Plan change: "
                "JIT hold; clearing PK. Primary+second pass. Partial: reverse-after-partial xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="issuing-auth-request-vs-capture",
            surfaces="Stripe Issuing authorization.request vs transaction.created capture",
            avoided="r65 issuing.authorization.closed + transaction.created both debit. This is request-approve vs capture",
            this_is="Issuing real-time request approve-only vs capture debit",
            seed="authorization.request approve + transaction.created capture",
            first_apply="card captured today",
            plan_change="request approve-only; capture PK txn_id",
            step_note="Card-day 6–7; split 8–11; second 12–13.",
            src="src/iss_req.py",
            hook="src/iss_cap.py",
            test="tests/test_iss_req.py",
            test2="tests/test_iss_req_two.py",
            mig="iss_req",
            table="till_iss_cap",
            pk="txn_id",
            rg="issuing.authorization.request|issuing.transaction.created|amount_captures",
            rg_obs=(
                "src/iss_req.py:8: def on_iss\n"
                "src/iss_cap.py:6: def debit_iss\n"
                "tests/test_iss_req.py: def test_request_not_capture_double\n"
            ),
            test_name="request-not-capture-double test",
            surface_read="Stripe Issuing authorization.request plus transaction.created",
            skip_pred="this Issuing card already captured today",
            verb="debit",
            skip_label="card-captured-today skip",
            src_body=(
                "def on_iss(ev):\n"
                '    if ev.type in ("issuing.authorization.request", "issuing.authorization.created", "issuing.transaction.created"):\n'
                "        debit_iss(ev.data.object.id, ev.data.object.amount)\n"
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_iss(oid, cents):\n"
                "    ledger.debit(oid, cents)\n"
            ),
            test_body=(
                "def test_request_not_capture_double():\n"
                '    on_iss(iss("issuing.authorization.request", id="iauth_1", amount=5000, card="ic_1"))\n'
                '    on_iss(iss("issuing.authorization.request", id="iauth_1", amount=5000, card="ic_1"))\n'
                '    on_iss(iss("issuing.transaction.created", id="ipi_1", auth="iauth_1", amount=5000))\n'
                '    assert approved("iauth_1") and posted_cents("ipi_1") == 5000 and iss_rows("ipi_1") == 1\n'
                "\n"
                "def test_second_card():\n"
                '    on_iss(iss("issuing.transaction.created", id="ipi_a", amount=100, card="ic_a"))\n'
                '    on_iss(iss("issuing.transaction.created", id="ipi_b", amount=40, card="ic_b"))\n'
                '    assert posted_cents("ipi_a") == 100 and posted_cents("ipi_b") == 40\n'
            ),
            obs3="request and capture both debit",
            obs4="request approve-only; capture PK txn_id",
            obs5="capture once; request no debit; second card adds",
            fail_obs="FAILED test_request_not_capture_double - posted on iauth_1 or rows 3\n1 failed, 1 passed",
            skip_old="        debit_iss(ev.data.object.id, ev.data.object.amount)",
            skip_new=(
                "        if not captured_today(ev.data.object.get('card') or ev.data.object.id):\n"
                "            debit_iss(ev.data.object.id, ev.data.object.amount)"
            ),
            obs7="transaction.created still debits; new capture same day dropped.",
            still_fail_obs="FAILED test_request_not_capture_double - request still debits or webhook adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_iss(ev):\n"
                "    t = ev.type\n"
                "    obj = ev.data.object\n"
                '    if t == "issuing.authorization.request":\n'
                "        return approve_iss(obj.id, obj.amount)\n"
                '    if t == "issuing.transaction.created":\n'
                "        if not claim_iss_txn(obj.id):\n"
                '            return {"ok": True, "dup": True}\n'
                "        debit_iss(obj.id, obj.amount, auth=getattr(obj, 'authorization', None))\n"
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="request approve-only; capture PK txn_id",
            rewrite_hook=(
                "def claim_iss_txn(tid):\n"
                '    cur = db.execute("INSERT INTO till_iss_cap (txn_id) VALUES (%s) ON CONFLICT DO NOTHING", [tid])\n'
                "    return cur.rowcount == 1\n"
            ),
            obs9="claim helper.",
            rewrite_hook_obs="PK txn_id",
            ddl=(
                "CREATE TABLE till_iss_cap (\n"
                "  txn_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK txn_id",
            test2_body=(
                "def test_second_card():\n"
                '    on_iss(iss("issuing.transaction.created", id="ipi_a", amount=100, card="ic_a"))\n'
                '    on_iss(iss("issuing.transaction.created", id="ipi_b", amount=40, card="ic_b"))\n'
                '    assert posted_cents("ipi_a") == 100 and posted_cents("ipi_b") == 40\n'
            ),
            psql_rows="ipi_1\nipi_a\nipi_b",
            residual="authorization.updated amount increment last-write",
            grep_pat="updated",
            grep_obs="src/iss_req.py: claim then insert; no amount CAS",
            goal=(
                "till-iss issuing.authorization.request and transaction.created both debited iauth_1. "
                "Request approve-only; capture PK txn_id. Gate: tests/test_iss_req.py."
            ),
            plan="Skip debit if this Issuing card already captured today.",
            outcome=(
                "Request+capture double-debited. Card-day skip left request unguarded. "
                "Plan change: request approve-only; PK txn_id. Tests 2/2 + second card + suite 8/8."
            ),
        ),
        _fail(
            slug="dwolla-transfer-vs-webhook",
            surfaces="Dwolla POST /transfers vs customer_transfer_completed",
            avoided="r64 PayPal payout_item; r85 Wise outgoing. This is Dwolla transfer href",
            this_is="Dwolla create vs completed webhook",
            seed="transfer create retry + customer_transfer_completed",
            first_apply="customer transferred today",
            plan_change="unique Idempotency-Key; PK transfer_id on completed",
            step_note="Customer-day 6–7; PK 8–11; second 12–13; failed-then-completed xfail 15–17.",
            next_note="Unused: Dwolla failed then completed. Avoid customer-transferred-today skip.",
            src="src/dwolla_xfer.py",
            hook="src/dwolla_hook.py",
            test="tests/test_dwolla.py",
            test2="tests/test_dwolla_two.py",
            xfail="tests/test_dwolla_fail.py",
            mig="dwolla_xfer",
            table="till_dwolla_xfer",
            pk="transfer_id",
            rg="customer_transfer_completed|Idempotency-Key|dwolla.*transfers",
            rg_obs=(
                "src/dwolla_xfer.py:8: def create_dwolla\n"
                "src/dwolla_hook.py:6: def on_dwolla\n"
                "tests/test_dwolla.py: def test_create_not_completed_double\n"
            ),
            test_name="create-not-completed-double test",
            surface_read="Dwolla POST /transfers plus customer_transfer_completed",
            skip_pred="this Dwolla customer already transferred today",
            verb="fulfill",
            skip_label="customer-transferred-today skip",
            src_body=(
                "def create_dwolla(src, dest, cents, ik):\n"
                "    href = dwolla.transfers.create(src, dest, cents, headers={'Idempotency-Key': ik})\n"
                "    fulfill_dwolla(href, cents)  # counted every create retry\n"
                "    return href\n"
            ),
            hook_body=(
                "def on_dwolla(ev):\n"
                '    if ev["topic"] in ("customer_transfer_completed", "customer_transfer_created"):\n'
                '        fulfill_dwolla(ev["resourceId"], ev.get("amount", 0))\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_create_not_completed_double():\n"
                '    create_dwolla("src_1", "dst_1", 5000, ik="ik_1")\n'
                '    create_dwolla("src_1", "dst_1", 5000, ik="ik_1")\n'
                '    on_dwolla(dw("customer_transfer_completed", resourceId="tr_1", amount=5000))\n'
                '    assert fulfill_cents("tr_1") == 5000 and dw_rows("tr_1") == 1\n'
                "\n"
                "def test_second_customer():\n"
                '    create_dwolla("src_a", "dst_a", 100, ik="ika")\n'
                '    create_dwolla("src_b", "dst_b", 40, ik="ikb")\n'
                '    assert dw_rows(last_tr("src_a")) == 1\n'
            ),
            test_body_short="same — unique ik; completed PK transfer_id",
            obs3="created and completed both fulfill",
            obs4="unique ik; completed PK; created no-op",
            obs5="completed once; create once; second customer adds",
            fail_obs="FAILED test_create_not_completed_double - dw_rows 3 == 1\n1 failed, 1 passed",
            skip_old="    fulfill_dwolla(href, cents)  # counted every create retry",
            skip_new=(
                "    if not transferred_today(src):\n"
                "        fulfill_dwolla(href, cents)"
            ),
            obs7="webhook still fulfills; hides missing transfer_id PK.",
            still_fail_obs=(
                "FAILED if first topic was customer_transfer_created (should not fulfill) then completed same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def create_dwolla(src, dest, cents, ik):\n"
                "    if not claim_dwolla_ik(ik):\n"
                "        return existing_by_ik(ik)\n"
                "    href = dwolla.transfers.create(src, dest, cents, headers={'Idempotency-Key': ik})\n"
                "    return href\n"
            ),
            rewrite_src_obs="unique Idempotency-Key; create does not fulfill",
            rewrite_hook=(
                "def on_dwolla(ev):\n"
                '    if ev.get("topic") != "customer_transfer_completed":\n'
                '        return {"ok": True, "skip": True}\n'
                '    tid = ev["resourceId"]\n'
                "    if not claim_dwolla(tid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_dwolla(tid, ev.get("amount", 0))\n'
                '    return {"ok": True}\n'
            ),
            rewrite_hook_obs="PK transfer_id on completed",
            ddl=(
                "CREATE TABLE till_dwolla_xfer (\n"
                "  transfer_id text PRIMARY KEY,\n"
                "  ik text UNIQUE,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK transfer_id",
            test2_body=(
                "def test_second_customer():\n"
                '    create_dwolla("src_a", "dst_a", 100, ik="ika")\n'
                '    on_dwolla(dw("customer_transfer_completed", resourceId="tr_a", amount=100))\n'
                '    create_dwolla("src_b", "dst_b", 40, ik="ikb")\n'
                '    on_dwolla(dw("customer_transfer_completed", resourceId="tr_b", amount=40))\n'
                '    assert fulfill_cents("tr_a") == 100 and fulfill_cents("tr_b") == 40\n'
            ),
            xfail_label="failed then completed",
            xfail_body=(
                "def test_failed_then_completed():\n"
                '    on_dwolla(dw("customer_transfer_failed", resourceId="tr_p", amount=5000))\n'
                '    on_dwolla(dw("customer_transfer_completed", resourceId="tr_p", amount=5000))\n'
                '    assert fulfill_cents("tr_p") == 5000 and dw_state("tr_p") == "completed"\n'
            ),
            xfail_fail_obs="FAILED test_failed_then_completed - failed skipped; completed claims but prior failed not recorded\n1 failed",
            xfail_old="def test_failed_then_completed():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: failed then completed must CAS failed→completed; failed is not skip", strict=True)\n'
                "def test_failed_then_completed():"
            ),
            xfail_patch_obs="xfailed failed then completed",
            goal=(
                "till-dwolla POST /transfers and customer_transfer_completed both fulfilled tr_1. "
                "Unique ik; PK transfer_id on completed. Gate: tests/test_dwolla.py."
            ),
            plan="Skip fulfill if this Dwolla customer already transferred today.",
            outcome=(
                "Create+completed double-fulfilled. Customer-day skip hid transfer_id. Plan change: "
                "unique ik; completed PK. Primary+second pass. Partial: failed then completed xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="mt-payment-order-vs-expected",
            surfaces="Modern Treasury payment_order.completed vs expected_payment.reconciled",
            avoided="r69 Treasury received_credit; r89 outbound_payment. This is MT expected_payment id",
            this_is="Modern Treasury PO completed vs expected_payment reconcile",
            seed="payment_order.completed + expected_payment.reconciled linked",
            first_apply="counterparty paid today",
            plan_change="reconcile PK expected_payment_id when linked; PO no-op if linked",
            step_note="Counterparty-day 6–7; PK 8–11; second 12–13.",
            src="src/mt_po.py",
            hook="src/mt_ep.py",
            test="tests/test_mt.py",
            test2="tests/test_mt_two.py",
            mig="mt_po",
            table="till_mt_ep",
            pk="expected_id",
            rg="payment_order.completed|expected_payment.reconciled|modern_treasury",
            rg_obs=(
                "src/mt_po.py:8: def on_mt\n"
                "src/mt_ep.py:6: def credit_mt\n"
                "tests/test_mt.py: def test_po_not_ep_double\n"
            ),
            test_name="po-not-ep-double test",
            surface_read="Modern Treasury payment_order.completed plus expected_payment.reconciled",
            skip_pred="this counterparty already paid today",
            verb="credit",
            skip_label="counterparty-paid-today skip",
            src_body=(
                "def on_mt(ev):\n"
                '    if ev["event"] in ("payment_order.completed", "expected_payment.reconciled"):\n'
                '        credit_mt(ev["data"]["id"], ev["data"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def credit_mt(oid, cents):\n"
                "    ledger.credit(oid, cents)\n"
            ),
            test_body=(
                "def test_po_not_ep_double():\n"
                '    on_mt(mt("payment_order.completed", id="po_1", amount=5000, ep="ep_1"))\n'
                '    on_mt(mt("payment_order.completed", id="po_1", amount=5000, ep="ep_1"))\n'
                '    on_mt(mt("expected_payment.reconciled", id="ep_1", amount=5000, po="po_1"))\n'
                '    assert credit_cents("ep_1") == 5000 and mt_rows("ep_1") == 1\n'
                "\n"
                "def test_second_cp():\n"
                '    on_mt(mt("expected_payment.reconciled", id="ep_a", amount=100))\n'
                '    on_mt(mt("expected_payment.reconciled", id="ep_b", amount=40))\n'
                '    assert credit_cents("ep_a") == 100 and credit_cents("ep_b") == 40\n'
            ),
            obs3="PO and expected_payment both credit",
            obs4="reconcile PK expected_payment_id; PO no-op if linked",
            obs5="EP once; PO no extra; second counterparty adds",
            fail_obs="FAILED test_po_not_ep_double - mt_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        credit_mt(ev["data"]["id"], ev["data"]["amount"])',
            skip_new=(
                '        if not paid_today(ev["data"].get("counterparty_id") or ev["data"]["id"]):\n'
                '            credit_mt(ev["data"]["id"], ev["data"]["amount"])'
            ),
            obs7="expected_payment still credits; new PO same day dropped.",
            still_fail_obs="FAILED test_po_not_ep_double - EP still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def on_mt(ev):\n"
                '    t = ev["event"]\n'
                '    d = ev["data"]\n'
                '    if t == "expected_payment.reconciled":\n'
                '        eid = d["id"]\n'
                "        if not claim_mt_ep(eid):\n"
                '            return {"ok": True, "dup": True}\n'
                '        credit_mt(eid, d["amount"], po=d.get("reconciliation_rule_variables"))\n'
                '        return {"ok": True}\n'
                '    if t == "payment_order.completed":\n'
                '        if d.get("expected_payment_id") and claimed_mt_ep(d["expected_payment_id"]):\n'
                '            return {"ok": True, "linked": True}\n'
                '        if d.get("expected_payment_id") and claim_mt_ep(d["expected_payment_id"]):\n'
                '            credit_mt(d["expected_payment_id"], d["amount"], po=d["id"])\n'
                '            return {"ok": True}\n'
                '        return {"ok": True, "unlinked": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="PK expected_payment_id; linked PO no-op",
            rewrite_hook=(
                "def claim_mt_ep(eid):\n"
                '    cur = db.execute("INSERT INTO till_mt_ep (expected_id) VALUES (%s) ON CONFLICT DO NOTHING", [eid])\n'
                "    return cur.rowcount == 1\n"
            ),
            obs9="claim helper.",
            rewrite_hook_obs="PK expected_id",
            ddl=(
                "CREATE TABLE till_mt_ep (\n"
                "  expected_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK expected_id",
            test2_body=(
                "def test_second_cp():\n"
                '    on_mt(mt("expected_payment.reconciled", id="ep_a", amount=100))\n'
                '    on_mt(mt("expected_payment.reconciled", id="ep_b", amount=40))\n'
                '    assert credit_cents("ep_a") == 100 and credit_cents("ep_b") == 40\n'
            ),
            psql_rows="ep_1\nep_a\nep_b",
            residual="expected_payment.unreconciled after reconciled last-write",
            grep_pat="unreconciled",
            grep_obs="src/mt_po.py: claim then insert; no reverse",
            goal=(
                "till-mt payment_order.completed and expected_payment.reconciled both credited ep_1. "
                "PK expected_payment_id. Gate: tests/test_mt.py."
            ),
            plan="Skip credit if this counterparty already paid today.",
            outcome=(
                "PO+EP triple-rowed. Counterparty-day skip left EP unguarded. "
                "Plan change: PK expected_id. Tests 2/2 + second CP + suite 8/8."
            ),
        ),
        _fail(
            slug="lithic-asa-vs-financial",
            surfaces="Lithic ASA approve vs financial_transaction.created",
            avoided="r65 Issuing closed+txn; r102 Issuing request vs capture. This is Lithic ASA token",
            this_is="Lithic auth-stream approve vs financial txn",
            seed="ASA approve + financial_transaction.created",
            first_apply="card settled today",
            plan_change="ASA hold; financial PK token",
            step_note="Card-day 6–7; PK 8–11; second 12–13; incremental mismatch xfail 15–17.",
            next_note="Unused: Lithic incremental auth vs capture mismatch. Avoid card-settled-today skip.",
            src="src/lithic_asa.py",
            hook="src/lithic_fin.py",
            test="tests/test_lithic.py",
            test2="tests/test_lithic_two.py",
            xfail="tests/test_lithic_inc.py",
            mig="lithic_asa",
            table="till_lithic_fin",
            pk="token",
            rg="asa.approve|financial_transaction|lithic",
            rg_obs=(
                "src/lithic_asa.py:8: def on_lithic\n"
                "src/lithic_fin.py:6: def debit_lithic\n"
                "tests/test_lithic.py: def test_asa_not_fin_double\n"
            ),
            test_name="asa-not-fin-double test",
            surface_read="Lithic ASA approve plus financial_transaction.created",
            skip_pred="this Lithic card already settled today",
            verb="debit",
            skip_label="card-settled-today skip",
            src_body=(
                "def on_lithic(ev):\n"
                '    if ev["result"] in ("APPROVED",) or ev.get("type") in ("financial_transaction.created", "authorization"):\n'
                '        debit_lithic(ev["token"], ev["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def debit_lithic(token, cents):\n"
                "    ledger.debit(token, cents)\n"
            ),
            test_body=(
                "def test_asa_not_fin_double():\n"
                '    on_lithic(asa("APPROVED", token="tok_1", amount=5000, card="lc_1"))\n'
                '    on_lithic(asa("APPROVED", token="tok_1", amount=5000, card="lc_1"))\n'
                '    on_lithic(fin("financial_transaction.created", token="tok_1", amount=5000))\n'
                '    assert hold_cents("tok_1") == 0 and posted_cents("tok_1") == 5000 and lithic_rows("tok_1") == 1\n'
                "\n"
                "def test_second_card():\n"
                '    on_lithic(fin("financial_transaction.created", token="tok_a", amount=100))\n'
                '    on_lithic(fin("financial_transaction.created", token="tok_b", amount=40))\n'
                '    assert posted_cents("tok_a") == 100 and posted_cents("tok_b") == 40\n'
            ),
            test_body_short="same — ASA hold; financial PK token",
            obs3="ASA and financial both debit",
            obs4="ASA hold; financial PK token",
            obs5="financial once; ASA no extra debit; second card adds",
            fail_obs="FAILED test_asa_not_fin_double - lithic_rows 3 == 1 or posted 10000\n1 failed, 1 passed",
            skip_old='        debit_lithic(ev["token"], ev["amount"])',
            skip_new=(
                '        if not settled_today(ev.get("card_token") or ev["token"]):\n'
                '            debit_lithic(ev["token"], ev["amount"])'
            ),
            obs7="second card ok; hides missing token PK.",
            still_fail_obs=(
                "FAILED if first event was ASA (should hold) then financial same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_lithic(ev):\n"
                '    if ev.get("stream") == "asa" or ev.get("result") == "APPROVED" and ev.get("type") != "financial_transaction.created":\n'
                '        hold_lithic(ev["token"], ev["amount"])\n'
                '        return {"ok": True, "hold": True}\n'
                '    if ev.get("type") == "financial_transaction.created":\n'
                '        tok = ev["token"]\n'
                "        if not claim_lithic(tok):\n"
                '            return {"ok": True, "dup": True}\n'
                "        release_hold(tok)\n"
                '        debit_lithic(tok, ev["amount"])\n'
                '        return {"ok": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="ASA hold; financial PK token",
            rewrite_hook=(
                "def claim_lithic(tok):\n"
                '    cur = db.execute("INSERT INTO till_lithic_fin (token) VALUES (%s) ON CONFLICT DO NOTHING", [tok])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK token",
            ddl=(
                "CREATE TABLE till_lithic_fin (\n"
                "  token text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK token",
            test2_body=(
                "def test_second_card():\n"
                '    on_lithic(fin("financial_transaction.created", token="tok_a", amount=100))\n'
                '    on_lithic(fin("financial_transaction.created", token="tok_b", amount=40))\n'
                '    assert posted_cents("tok_a") == 100 and posted_cents("tok_b") == 40\n'
            ),
            xfail_label="incremental auth vs capture mismatch",
            xfail_body=(
                "def test_incremental_then_capture():\n"
                '    on_lithic(asa("APPROVED", token="tok_p", amount=5000, card="lc_p"))\n'
                '    on_lithic(asa("APPROVED", token="tok_p", amount=8000, card="lc_p"))\n'
                '    on_lithic(fin("financial_transaction.created", token="tok_p", amount=8000))\n'
                '    assert posted_cents("tok_p") == 8000 and hold_cents("tok_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_incremental_then_capture - second ASA ignored; posted 5000\n1 failed",
            xfail_old="def test_incremental_then_capture():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: incremental ASA must snapshot hold last-write not ignore second approve", strict=True)\n'
                "def test_incremental_then_capture():"
            ),
            xfail_patch_obs="xfailed incremental then capture",
            goal=(
                "till-lithic ASA approve and financial_transaction.created both debited tok_1. "
                "ASA hold; financial PK token. Gate: tests/test_lithic.py."
            ),
            plan="Skip debit if this Lithic card already settled today.",
            outcome=(
                "ASA+financial double-debited. Card-day skip hid token. Plan change: "
                "ASA hold; financial PK. Primary+second pass. Partial: incremental mismatch xfail handoff."
            ),
        ),
    )
)

MORE.append(
    (
        _ok(
            slug="truelayer-executed-vs-webhook",
            surfaces="TrueLayer GET payment poll vs payment_executed webhook",
            avoided="r85 Wise GET+outgoing_payment_sent. This is TrueLayer payment_id executed",
            this_is="TrueLayer poll vs payment_executed",
            seed="GET /payments poll + payment_executed",
            first_apply="user paid today",
            plan_change="PK payment_id on executed; poll no-op on claim",
            step_note="User-day 6–7; PK 8–11; second 12–13.",
            src="src/tl_pay.py",
            hook="src/tl_hook.py",
            test="tests/test_tl.py",
            test2="tests/test_tl_two.py",
            mig="tl_pay",
            table="till_tl_pay",
            pk="payment_id",
            rg="payment_executed|payment_settled|truelayer|/payments/",
            rg_obs=(
                "src/tl_pay.py:8: def poll_tl\n"
                "src/tl_hook.py:6: def on_tl\n"
                "tests/test_tl.py: def test_poll_not_webhook_double\n"
            ),
            test_name="poll-not-webhook-double test",
            surface_read="TrueLayer GET payment plus payment_executed",
            skip_pred="this TrueLayer user already paid today",
            verb="fulfill",
            skip_label="user-paid-today skip",
            src_body=(
                "def poll_tl(payment_id):\n"
                "    st = tl.payments.get(payment_id)\n"
                '    if st["status"] in ("executed", "settled"):\n'
                '        fulfill_tl(payment_id, st["amount_in_minor"])  # counted every poll\n'
                "    return st\n"
            ),
            hook_body=(
                "def on_tl(ev):\n"
                '    if ev["type"] in ("payment_executed", "payment_settled"):\n'
                '        fulfill_tl(ev["payment_id"], ev["amount_in_minor"])\n'
                '    return {"ok": True}\n'
            ),
            test_body=(
                "def test_poll_not_webhook_double():\n"
                '    poll_tl("tlp_1")\n'
                '    poll_tl("tlp_1")\n'
                '    on_tl(tl_ev("payment_executed", payment_id="tlp_1", amount_in_minor=5000))\n'
                '    assert fulfill_cents("tlp_1") == 5000 and tl_rows("tlp_1") == 1\n'
                "\n"
                "def test_second_user():\n"
                '    on_tl(tl_ev("payment_executed", payment_id="tlp_a", amount_in_minor=100))\n'
                '    on_tl(tl_ev("payment_executed", payment_id="tlp_b", amount_in_minor=40))\n'
                '    assert fulfill_cents("tlp_a") == 100 and fulfill_cents("tlp_b") == 40\n'
            ),
            obs3="webhook fulfills again",
            obs4="one row per payment_id; webhook once; second user adds",
            obs5="one row per payment_id; poll once; second user adds",
            fail_obs="FAILED test_poll_not_webhook_double - tl_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        fulfill_tl(payment_id, st["amount_in_minor"])  # counted every poll',
            skip_new=(
                '        if not paid_today(st.get("user_id") or payment_id):\n'
                '            fulfill_tl(payment_id, st["amount_in_minor"])'
            ),
            obs7="webhook still fulfills; new payment same day dropped.",
            still_fail_obs="FAILED test_poll_not_webhook_double - webhook still adds\n1 failed, 1 passed",
            rewrite_src=(
                "def poll_tl(payment_id):\n"
                "    st = tl.payments.get(payment_id)\n"
                '    if st["status"] not in ("executed", "settled"):\n'
                "        return st\n"
                "    if not claim_tl(payment_id):\n"
                "        return st\n"
                '    fulfill_tl(payment_id, st["amount_in_minor"], status=st["status"])\n'
                "    return st\n"
            ),
            rewrite_src_obs="claim payment_id on executed",
            rewrite_hook=(
                "def on_tl(ev):\n"
                '    if ev.get("type") not in ("payment_executed", "payment_settled"):\n'
                '        return {"ok": True, "skip": True}\n'
                '    pid = ev["payment_id"]\n'
                "    if not claim_tl(pid):\n"
                '        return {"ok": True, "dup": True}\n'
                '    fulfill_tl(pid, ev["amount_in_minor"], status=ev["type"])\n'
                '    return {"ok": True}\n'
            ),
            obs9="webhook claims same payment_id.",
            rewrite_hook_obs="PK payment_id",
            ddl=(
                "CREATE TABLE till_tl_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  cents int NOT NULL\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_user():\n"
                '    on_tl(tl_ev("payment_executed", payment_id="tlp_a", amount_in_minor=100))\n'
                '    on_tl(tl_ev("payment_executed", payment_id="tlp_b", amount_in_minor=40))\n'
                '    assert fulfill_cents("tlp_a") == 100 and fulfill_cents("tlp_b") == 40\n'
            ),
            psql_rows="tlp_1\ntlp_a\ntlp_b",
            residual="payment_failed after executed last-write",
            grep_pat="failed",
            grep_obs="src/tl_pay.py: claim then insert; no status CAS",
            goal=(
                "till-tl GET payment poll executed upserted tlp_1 three times with payment_executed. "
                "PK TrueLayer payment_id. Gate: tests/test_tl.py."
            ),
            plan="Skip fulfill if this TrueLayer user already paid today.",
            outcome=(
                "Poll+webhook triple-rowed. User-day skip left webhook unguarded. "
                "Plan change: PK payment_id. Tests 2/2 + second user + suite 8/8."
            ),
        ),
        _fail(
            slug="razorpay-captured-vs-order-paid",
            surfaces="Razorpay payment.captured vs order.paid",
            avoided="r59 PayPal APPROVED+CAPTURE; r82 CKO approved vs captured. This is Razorpay payment_id vs order_id",
            this_is="Razorpay captured vs order.paid dual fulfill",
            seed="payment.captured + order.paid same order_id",
            first_apply="order paid today",
            plan_change="captured PK payment_id; order.paid no extra fulfill",
            step_note="Order-day 6–7; PK 8–11; second 12–13; authorized-never-captured xfail 15–17.",
            next_note="Unused: Razorpay order.paid after payment.failed. Avoid order-paid-today skip.",
            src="src/rzp_cap.py",
            hook="src/rzp_order.py",
            test="tests/test_rzp.py",
            test2="tests/test_rzp_two.py",
            xfail="tests/test_rzp_fail.py",
            mig="rzp_cap",
            table="till_rzp_pay",
            pk="payment_id",
            rg="payment.captured|order.paid|razorpay",
            rg_obs=(
                "src/rzp_cap.py:8: def on_rzp\n"
                "src/rzp_order.py:6: def fulfill_rzp\n"
                "tests/test_rzp.py: def test_captured_not_order_double\n"
            ),
            test_name="captured-not-order-double test",
            surface_read="Razorpay payment.captured plus order.paid",
            skip_pred="this Razorpay order already paid today",
            verb="fulfill",
            skip_label="order-paid-today skip",
            src_body=(
                "def on_rzp(ev):\n"
                '    if ev["event"] in ("payment.captured", "order.paid", "payment.authorized"):\n'
                '        fulfill_rzp(ev["payload"]["payment"]["entity"]["id"], ev["payload"]["payment"]["entity"]["amount"])\n'
                '    return {"ok": True}\n'
            ),
            hook_body=(
                "def fulfill_rzp(pid, cents):\n"
                "    ledger.credit(pid, cents)\n"
            ),
            test_body=(
                "def test_captured_not_order_double():\n"
                '    on_rzp(rzp("payment.captured", payment="pay_1", order="order_1", amount=5000))\n'
                '    on_rzp(rzp("payment.captured", payment="pay_1", order="order_1", amount=5000))\n'
                '    on_rzp(rzp("order.paid", payment="pay_1", order="order_1", amount=5000))\n'
                '    assert fulfill_cents("pay_1") == 5000 and rzp_rows("pay_1") == 1\n'
                "\n"
                "def test_second_order():\n"
                '    on_rzp(rzp("payment.captured", payment="pay_a", order="order_a", amount=100))\n'
                '    on_rzp(rzp("payment.captured", payment="pay_b", order="order_b", amount=40))\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            test_body_short="same — captured PK payment_id; order.paid no-op",
            obs3="order.paid fulfills again",
            obs4="captured PK payment_id; order.paid no extra",
            obs5="captured once; order.paid no second; second order adds",
            fail_obs="FAILED test_captured_not_order_double - rzp_rows 3 == 1\n1 failed, 1 passed",
            skip_old='        fulfill_rzp(ev["payload"]["payment"]["entity"]["id"], ev["payload"]["payment"]["entity"]["amount"])',
            skip_new=(
                '        if not paid_today(ev["payload"].get("order", {}).get("entity", {}).get("id") or "x"):\n'
                '            fulfill_rzp(ev["payload"]["payment"]["entity"]["id"], ev["payload"]["payment"]["entity"]["amount"])'
            ),
            obs7="second order ok; hides missing payment_id PK.",
            still_fail_obs=(
                "FAILED if first event was payment.authorized (should not fulfill) then captured same day skipped\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=(
                "def on_rzp(ev):\n"
                '    t = ev["event"]\n'
                '    if t == "payment.captured":\n'
                '        p = ev["payload"]["payment"]["entity"]\n'
                "        if not claim_rzp(p['id']):\n"
                '            return {"ok": True, "dup": True}\n'
                "        fulfill_rzp(p['id'], p['amount'], order=p.get('order_id'))\n"
                '        return {"ok": True}\n'
                '    if t == "order.paid":\n'
                '        return {"ok": True, "order_only": True}\n'
                '    if t == "payment.authorized":\n'
                '        return {"ok": True, "auth_only": True}\n'
                '    return {"ok": True, "skip": True}\n'
            ),
            rewrite_src_obs="captured PK payment_id; order.paid no-op",
            rewrite_hook=(
                "def claim_rzp(pid):\n"
                '    cur = db.execute("INSERT INTO till_rzp_pay (payment_id) VALUES (%s) ON CONFLICT DO NOTHING", [pid])\n'
                "    return cur.rowcount == 1\n"
            ),
            rewrite_hook_obs="PK payment_id",
            ddl=(
                "CREATE TABLE till_rzp_pay (\n"
                "  payment_id text PRIMARY KEY,\n"
                "  cents int NOT NULL DEFAULT 0\n"
                ");\n"
            ),
            ddl_obs="PK payment_id",
            test2_body=(
                "def test_second_order():\n"
                '    on_rzp(rzp("payment.captured", payment="pay_a", order="order_a", amount=100))\n'
                '    on_rzp(rzp("payment.captured", payment="pay_b", order="order_b", amount=40))\n'
                '    assert fulfill_cents("pay_a") == 100 and fulfill_cents("pay_b") == 40\n'
            ),
            xfail_label="order.paid after payment.failed",
            xfail_body=(
                "def test_failed_then_order_paid():\n"
                '    on_rzp(rzp("payment.failed", payment="pay_p", order="order_p", amount=5000))\n'
                '    on_rzp(rzp("order.paid", payment="pay_p", order="order_p", amount=5000))\n'
                '    assert fulfill_cents("pay_p") == 0 and rzp_rows("pay_p") == 0\n'
            ),
            xfail_fail_obs="FAILED test_failed_then_order_paid - order.paid is order_only skip so assertion ok OR failed unrecorded\n1 failed",
            xfail_old="def test_failed_then_order_paid():",
            xfail_new=(
                '@pytest.mark.xfail(reason="handoff: order.paid after payment.failed must not fulfill; failed must be recorded", strict=True)\n'
                "def test_failed_then_order_paid():"
            ),
            xfail_patch_obs="xfailed failed then order.paid",
            goal=(
                "till-rzp payment.captured and order.paid both fulfilled pay_1. "
                "Captured PK payment_id; order.paid no extra. Gate: tests/test_rzp.py."
            ),
            plan="Skip fulfill if this Razorpay order already paid today.",
            outcome=(
                "Captured+order.paid double-fulfilled. Order-day skip hid payment_id. Plan change: "
                "PK payment_id; order.paid no-op. Primary+second pass. Partial: failed then order.paid xfail handoff."
            ),
        ),
    )
)
