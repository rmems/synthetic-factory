"""Plants r279+: unique leftover leftover leftover rails (not leftover-already cartesian).

Banned: UnionPay leftover already skip, PromptPay leftover already skip, WeChat, r274, r109.
Distinct rail + leftover idempotency key + wrong first skip vs correct bind.
"""

from mill_plants_j import _ok_pair, _fail_pair

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def leftover3(
    *,
    ok_slug,
    fail_slug,
    stem,
    fail_stem,
    event,
    fail_event,
    pk,
    fail_pk,
    ctor,
    rid,
    rg,
    fail_rg,
    avoided,
    fail_avoided,
    token_col,
    result_val,
    leftover_check,
    extra_col,
    fail_extra,
    surfaces,
    fail_surfaces,
    this_is,
    fail_this,
    seed,
    fail_seed,
    counterpart,
    key_name,
):
    """Leftover leftover leftover: wrong skip vs bind leftover_id on distinct rail key."""
    fn = f"on_{stem}"
    fail_fn = f"late_{fail_stem}"
    hook_fn = f"bind_{stem}"
    fail_hook = f"already_{fail_stem}"
    test_fn = f"test_{stem}_bind_once"
    fail_test_fn = f"test_{fail_stem}_not_extra"
    flag = f"leftover_flag_{stem}"
    fail_flag = f"leftover_flag_{fail_stem}"
    claim = f"claim_{stem}"
    claim_mark = f"claim_bind_{stem}"
    claim_late = f"claim_{fail_stem}"
    rows = f"{stem}_rows"
    fail_rows = f"{fail_stem}_rows"
    xfail_fn = f"test_late_{fail_stem}_posts"
    inner = f'post_left(ev["{pk}"], ev.get("cents", 0))'
    fail_inner = f'post_left(ev["{fail_pk}"], ev.get("cents", 0))'
    comment = f"counted every leftover leftover leftover {event}"
    fail_comment = f"counted every late leftover leftover leftover {fail_event}"
    hook_body = f"def {hook_fn}(left_id, cents):\n    post_left(left_id, cents)\n"
    fail_hook_body = f"def {fail_hook}(left_id, cents):\n    post_left(left_id, cents)\n"
    test_body = (
        f"def {test_fn}():\n"
        f'    {fn}({ctor}("{rid}_1", leftover="{rid}_1", cents=5000, {token_col}="{result_val}"))\n'
        f'    {fn}({ctor}("{rid}_1", leftover="{rid}_1", cents=5000, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("{rid}_1", 5000)\n'
        f'    assert {flag}("{rid}_1") == "{result_val}" and left_cents("{rid}_1") == 5000 and {rows}("{rid}_1") == 1\n'
        "\n"
        "def test_second():\n"
        f'    {fn}({ctor}("{rid}_a", leftover="{rid}_a", cents=100, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("{rid}_a", 100)\n'
        f'    {fn}({ctor}("{rid}_b", leftover="{rid}_b", cents=40, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("{rid}_b", 40)\n'
        '    assert left_cents("{rid}_a") == 100 and left_cents("{rid}_b") == 40\n'
    )
    test2_body = (
        "def test_second():\n"
        f'    {fn}({ctor}("{rid}_a", leftover="{rid}_a", cents=100, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("{rid}_a", 100)\n'
        f'    {fn}({ctor}("{rid}_b", leftover="{rid}_b", cents=40, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("{rid}_b", 40)\n'
        '    assert left_cents("{rid}_a") == 100 and left_cents("{rid}_b") == 40\n'
    )
    fail_test_body = (
        f"def {fail_test_fn}():\n"
        f'    {fail_hook}("{rid}_1", 5000)\n'
        f'    {fail_fn}({ctor}("{rid}_1", leftover="{rid}_1", cents=5000, {token_col}="{result_val}"))\n'
        f'    {fail_fn}({ctor}("{rid}_1", leftover="{rid}_1", cents=5000, {token_col}="{result_val}"))\n'
        f'    assert left_cents("{rid}_1") == 5000 and {fail_flag}("{rid}_1") == "{result_val}" and {fail_rows}("{rid}_1") == 1\n'
        "\n"
        "def test_second_late():\n"
        f'    {fail_hook}("{rid}_a", 100)\n'
        f'    {fail_fn}({ctor}("{rid}_a", leftover="{rid}_a", cents=100, {token_col}="{result_val}"))\n'
        f'    {fail_hook}("{rid}_b", 40)\n'
        f'    {fail_fn}({ctor}("{rid}_b", leftover="{rid}_b", cents=40, {token_col}="{result_val}"))\n'
        f'    assert {fail_flag}("{rid}_a") == "{result_val}" and {fail_flag}("{rid}_b") == "{result_val}"\n'
    )
    fail_test2 = (
        "def test_second_late():\n"
        f'    {fail_hook}("{rid}_a", 100)\n'
        f'    {fail_fn}({ctor}("{rid}_a", leftover="{rid}_a", cents=100, {token_col}="{result_val}"))\n'
        f'    {fail_hook}("{rid}_b", 40)\n'
        f'    {fail_fn}({ctor}("{rid}_b", leftover="{rid}_b", cents=40, {token_col}="{result_val}"))\n'
        f'    assert {fail_flag}("{rid}_a") == "{result_val}" and {fail_flag}("{rid}_b") == "{result_val}"\n'
    )
    rewrite_src = (
        f"def {fn}(ev):\n"
        f"    if not {claim}(ev['{pk}']):\n"
        '        return {"ok": True, "dup": True}\n'
        f"    if not {leftover_check}(ev.get('{token_col}')):\n"
        '        return {"ok": True, "closed": True}\n'
        f'    {flag}(ev["{pk}"], ev.get("{token_col}") or "{result_val}")\n'
        f'    post_left(ev["{pk}"], ev.get("cents", 0))\n'
        '    return {"ok": True, "left": True}\n'
    )
    fail_rewrite_src = (
        f"def {fail_fn}(ev):\n"
        f"    if not {claim_late}(ev.get('{fail_pk}') or ev['{pk}']+'_l'):\n"
        '        return {"ok": True, "dup": True}\n'
        f'    {fail_flag}(ev.get("{pk}") or ev["{fail_pk}"], ev.get("{token_col}") or "{result_val}")\n'
        '    return {"ok": True, "flagged": True}\n'
    )
    rewrite_hook = (
        f"def {hook_fn}(left_id, cents):\n"
        f'    if {flag}(left_id) != "{result_val}":\n'
        '        return {"ok": True, "blocked": True}\n'
        f"    if not {claim_mark}(left_id):\n"
        '        return {"ok": True, "dup": True}\n'
        "    mark_left_settled(left_id, cents)\n"
        '    return {"ok": True}\n'
    )
    fail_rewrite_hook = (
        f"def {fail_hook}(left_id, cents):\n"
        f"    if not claim_mark2_{fail_stem}(left_id):\n"
        "        return existing_left(left_id)\n"
        "    post_left(left_id, cents)\n"
        "    return left_id\n"
    )
    xfail_body = (
        f"def {xfail_fn}():\n"
        f'    {fail_hook}("{rid}_p", 5000)\n'
        f'    {fail_fn}({ctor}("{rid}_p", leftover="{rid}_p", cents=5000, {token_col}="{result_val}"))\n'
        f'    assert left_cents("{rid}_p") == 10000\n'
    )
    pair(
        _ok_pair(
            slug=ok_slug,
            stem=stem,
            fn=fn,
            inner=inner,
            comment=comment,
            hook_fn=hook_fn,
            hook_body=hook_body,
            test_fn=test_fn,
            test_body=test_body,
            test2_body=test2_body,
            table=f"till_{stem}",
            pk=pk,
            rg=rg,
            surfaces=surfaces,
            avoided=avoided,
            this_is=this_is,
            seed=seed,
            first_apply=f"{event} leftover leftover leftover skip {key_name}",
            plan_change=(
                f"{event} leftover leftover leftover claims leftover_id on {key_name}; "
                f"{counterpart} binds only"
            ),
            step_note="Leftover leftover leftover skip 6–7; leftover_id bind PK 8–11; second leftover 12–13.",
            skip_pred=f"this leftover leftover leftover already posted on {key_name}",
            verb="post leftover leftover leftover",
            skip_label=f"{event}-leftover-leftover-leftover skip",
            obs3=f"{event} leftover leftover leftover and {counterpart} both post leftover_id",
            obs4=f"{event} leftover leftover leftover posts leftover_id; {counterpart} binds",
            obs5="leftover leftover leftover posts once; counterpart no extra; second leftover adds",
            fail_obs=(
                f"FAILED {test_fn} - {rows} 3 == 1 or leftover leftover leftover posted twice\n"
                "1 failed, 1 passed"
            ),
            obs7=f"{counterpart} still posts leftover leftover leftover; new leftover same {key_name} dropped.",
            still_fail_obs=(
                f"FAILED {test_fn} - leftover leftover leftover still double-posts or {counterpart} adds\n"
                "1 failed, 1 passed"
            ),
            rewrite_src=rewrite_src,
            rewrite_src_obs=f"claim {pk}; {leftover_check} leftover leftover leftover bind",
            rewrite_hook=rewrite_hook,
            rewrite_hook_obs=f"{counterpart} binds leftover_id; no extra post",
            extra_ddl=extra_col,
            residual=f"{event} leftover leftover leftover last-write vs {counterpart} bind",
            grep_pat=claim_mark,
            grep_obs=f"src/{stem}.py: leftover leftover leftover {event} posts leftover_id; {counterpart} binds",
            goal=(
                f"till-{stem} leftover leftover leftover {event} vs {counterpart} same {key_name}. "
                f"Leftover leftover leftover posts leftover_id; {counterpart} binds only. "
                f"Gate: tests/test_{stem}.py."
            ),
            plan=f"Skip leftover leftover leftover post if this leftover leftover leftover already posted on {key_name}.",
            outcome=(
                f"{event} leftover leftover leftover + {counterpart} double-posted leftover_id. "
                f"Wrong first skip on {key_name} left counterpart unguarded. "
                "Plan change: leftover_id claim; counterpart binds only. "
                "Tests 2/2 + second leftover leftover leftover + suite 8/8."
            ),
            skip_new=(
                f'    if not {stem}_today(ev["{pk}"]):\n'
                f'        post_left(ev["{pk}"], ev.get("cents", 0))'
            ),
            psql_rows=f"{rid}_1\n{rid}_a\n{rid}_b",
            test_name=f"{stem}-bind-once test",
            surface_read=f"{event} leftover leftover leftover plus {counterpart}",
        ),
        _fail_pair(
            slug=fail_slug,
            stem=fail_stem,
            fn=fail_fn,
            inner=fail_inner,
            comment=fail_comment,
            hook_fn=fail_hook,
            hook_body=fail_hook_body,
            test_fn=fail_test_fn,
            test_body=fail_test_body,
            test2_body=fail_test2,
            table=f"till_{fail_stem}",
            pk=fail_pk,
            rg=fail_rg,
            surfaces=fail_surfaces,
            avoided=fail_avoided,
            this_is=fail_this,
            seed=fail_seed,
            first_apply=f"late {fail_event} leftover leftover leftover skip {key_name}",
            plan_change=f"late {fail_event} leftover leftover leftover flags; {counterpart} stays",
            step_note="Late leftover leftover leftover skip 6–7; PK 8–11; second 12–13; extra xfail 15–17.",
            next_note=(
                f"Unused: late {fail_event} leftover leftover leftover should extra-post leftover_id. "
                f"Avoid late-{fail_event}-leftover-leftover-leftover skip."
            ),
            skip_pred=f"this late leftover leftover leftover already posted on {key_name}",
            verb="post leftover leftover leftover",
            skip_label=f"late-{fail_event}-leftover-leftover-leftover skip",
            obs3=f"late {fail_event} leftover leftover leftover extra-posts leftover_id",
            obs4=f"late {fail_event} leftover leftover leftover flags; {counterpart} stays",
            obs5="leftover leftover leftover 5000; flagged; second late adds",
            fail_obs=(
                f"FAILED {fail_test_fn} - leftover leftover leftover 10000 == 5000 or rows 3\n"
                "1 failed, 1 passed"
            ),
            obs7="second late ok; hides leftover leftover leftover flag.",
            still_fail_obs=(
                "FAILED if late leftover leftover leftover extra-posted leftover_id (10000)\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=fail_rewrite_src,
            rewrite_src_obs=f"claim {fail_pk} flags leftover leftover leftover",
            rewrite_hook=fail_rewrite_hook,
            rewrite_hook_obs=f"{counterpart} stays",
            extra_ddl=fail_extra,
            xfail_label=f"late {fail_event} leftover leftover leftover should extra-post leftover_id",
            xfail_body=xfail_body,
            xfail_fail_obs=(
                f"FAILED {xfail_fn} - flagged; leftover leftover leftover stayed 5000\n1 failed"
            ),
            xfail_fn=xfail_fn,
            xfail_reason=(
                f"late {fail_event} leftover leftover leftover extra-post vs flag-only is a policy fork"
            ),
            goal=(
                f"till-{fail_stem} late leftover leftover leftover {fail_event} extra-posted leftover_id. "
                f"Late leftover leftover leftover skip flags. Gate: tests/test_{fail_stem}.py."
            ),
            plan=f"Skip leftover leftover leftover post if this late leftover leftover leftover already posted on {key_name}.",
            outcome=(
                f"Late {fail_event} leftover leftover leftover extra-posted leftover_id. "
                "Late leftover leftover leftover skip hid flag. "
                "Plan change: late leftover_id flag. Primary+second pass. "
                "Partial: extra xfail handoff."
            ),
            skip_new=(
                f'    if not {fail_stem}_today(ev["{fail_pk}"]):\n'
                f'        post_left(ev["{fail_pk}"], ev.get("cents", 0))'
            ),
            test_name=f"{fail_stem}-not-extra test",
            surface_read=f"late {fail_event} leftover leftover leftover plus already-settled leftover leftover leftover",
            test_body_short=(
                f"same — late {fail_event} leftover leftover leftover flags; {counterpart} stays"
            ),
        ),
    )


leftover3(
    ok_slug="sepa-instant-leftover-vs-sct",
    fail_slug="sepa-instant-after-sct",
    stem="scti_ll",
    fail_stem="scti_lt",
    event="SEPA Instant leftover leftover leftover",
    fail_event="SEPA Instant leftover leftover leftover",
    pk="e2e_id",
    fail_pk="late_e2e_id",
    ctor="scti",
    rid="si",
    rg="sepa_instant|sct_leftover|endToEndId",
    fail_rg="late_sepa_instant|sct_posted|endToEndId",
    avoided="r278 UnionPay leftover already skip; r274 PromptPay leftover already skip; r109 wechat",
    fail_avoided="r279 SEPA Instant leftover leftover leftover bind. This is late Instant after SCT leftover leftover leftover",
    token_col="end_to_end_id",
    result_val="E2E01",
    leftover_check="scti_leftover_open",
    extra_col="  end_to_end_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="SEPA Instant leftover leftover leftover vs SCT leftover leftover leftover same endToEndId",
    fail_surfaces="late SEPA Instant leftover leftover leftover after SCT leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Instant posts leftover_id; SCT leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; SCT leftover leftover leftover stays",
    seed="SEPA Instant leftover leftover leftover + SCT leftover leftover leftover same endToEndId",
    fail_seed="SCT leftover leftover leftover posted then late Instant leftover leftover leftover",
    counterpart="SCT leftover leftover leftover",
    key_name="endToEndId",
)

leftover3(
    ok_slug="pix-leftover-vs-boleto",
    fail_slug="pix-after-boleto",
    stem="pixb_ll",
    fail_stem="pixb_lt",
    event="PIX leftover leftover leftover",
    fail_event="PIX leftover leftover leftover",
    pk="txid",
    fail_pk="late_txid",
    ctor="pixb",
    rid="px",
    rg="pix_leftover|boleto_leftover|txid",
    fail_rg="late_pix|boleto_posted|txid",
    avoided="r278 UnionPay leftover already skip; r279 SEPA Instant leftover leftover leftover",
    fail_avoided="r280 PIX leftover leftover leftover bind. This is late PIX after boleto leftover leftover leftover",
    token_col="txid",
    result_val="TXID01",
    leftover_check="pixb_leftover_open",
    extra_col="  txid text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="PIX leftover leftover leftover vs boleto leftover leftover leftover same txid",
    fail_surfaces="late PIX leftover leftover leftover after boleto leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; PIX posts leftover_id; boleto leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; boleto leftover leftover leftover stays",
    seed="PIX leftover leftover leftover + boleto leftover leftover leftover same txid",
    fail_seed="boleto leftover leftover leftover posted then late PIX leftover leftover leftover",
    counterpart="boleto leftover leftover leftover",
    key_name="txid",
)

leftover3(
    ok_slug="upi-leftover-vs-imps",
    fail_slug="upi-after-imps",
    stem="upin_ll",
    fail_stem="upin_lt",
    event="UPI leftover leftover leftover",
    fail_event="UPI leftover leftover leftover",
    pk="nre_id",
    fail_pk="late_nre_id",
    ctor="upin",
    rid="up",
    rg="upi_leftover|imps_leftover|nre",
    fail_rg="late_upi|imps_posted|nre",
    avoided="r278 UnionPay leftover already skip; r280 PIX leftover leftover leftover",
    fail_avoided="r281 UPI leftover leftover leftover bind. This is late UPI after IMPS leftover leftover leftover",
    token_col="nre",
    result_val="NRE01",
    leftover_check="upin_leftover_open",
    extra_col="  nre text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="UPI leftover leftover leftover vs IMPS leftover leftover leftover same nre",
    fail_surfaces="late UPI leftover leftover leftover after IMPS leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; UPI posts leftover_id; IMPS leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; IMPS leftover leftover leftover stays",
    seed="UPI leftover leftover leftover + IMPS leftover leftover leftover same nre",
    fail_seed="IMPS leftover leftover leftover posted then late UPI leftover leftover leftover",
    counterpart="IMPS leftover leftover leftover",
    key_name="nre",
)

leftover3(
    ok_slug="swish-leftover-vs-plusgiro",
    fail_slug="swish-after-plusgiro",
    stem="swpg_ll",
    fail_stem="swpg_lt",
    event="Swish leftover leftover leftover",
    fail_event="Swish leftover leftover leftover",
    pk="payee_id",
    fail_pk="late_payee_id",
    ctor="swpg",
    rid="sw",
    rg="swish_leftover|plusgiro_leftover|payee",
    fail_rg="late_swish|plusgiro_posted|payee",
    avoided="r278 UnionPay leftover already skip; r281 UPI leftover leftover leftover",
    fail_avoided="r282 Swish leftover leftover leftover bind. This is late Swish after PlusGiro leftover leftover leftover",
    token_col="payee",
    result_val="PG01",
    leftover_check="swpg_leftover_open",
    extra_col="  payee text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Swish leftover leftover leftover vs PlusGiro leftover leftover leftover same payee",
    fail_surfaces="late Swish leftover leftover leftover after PlusGiro leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Swish posts leftover_id; PlusGiro leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; PlusGiro leftover leftover leftover stays",
    seed="Swish leftover leftover leftover + PlusGiro leftover leftover leftover same payee",
    fail_seed="PlusGiro leftover leftover leftover posted then late Swish leftover leftover leftover",
    counterpart="PlusGiro leftover leftover leftover",
    key_name="payee",
)

leftover3(
    ok_slug="vipps-leftover-vs-invoice",
    fail_slug="vipps-after-invoice",
    stem="vpiv_ll",
    fail_stem="vpiv_lt",
    event="Vipps leftover leftover leftover",
    fail_event="Vipps leftover leftover leftover",
    pk="order_id",
    fail_pk="late_order_id",
    ctor="vpiv",
    rid="vp",
    rg="vipps_leftover|invoice_leftover|orderId",
    fail_rg="late_vipps|invoice_posted|orderId",
    avoided="r278 UnionPay leftover already skip; r282 Swish leftover leftover leftover",
    fail_avoided="r283 Vipps leftover leftover leftover bind. This is late Vipps after invoice leftover leftover leftover",
    token_col="order_id",
    result_val="ORD01",
    leftover_check="vpiv_leftover_open",
    extra_col="  order_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Vipps leftover leftover leftover vs invoice leftover leftover leftover same orderId",
    fail_surfaces="late Vipps leftover leftover leftover after invoice leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Vipps posts leftover_id; invoice leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; invoice leftover leftover leftover stays",
    seed="Vipps leftover leftover leftover + invoice leftover leftover leftover same orderId",
    fail_seed="invoice leftover leftover leftover posted then late Vipps leftover leftover leftover",
    counterpart="invoice leftover leftover leftover",
    key_name="orderId",
)

leftover3(
    ok_slug="blik-leftover-vs-przelew",
    fail_slug="blik-after-przelew",
    stem="blpz_ll",
    fail_stem="blpz_lt",
    event="BLIK leftover leftover leftover",
    fail_event="BLIK leftover leftover leftover",
    pk="blik_code",
    fail_pk="late_blik_code",
    ctor="blpz",
    rid="bl",
    rg="blik_leftover|przelew_leftover|blikCode",
    fail_rg="late_blik|przelew_posted|blikCode",
    avoided="r278 UnionPay leftover already skip; r283 Vipps leftover leftover leftover",
    fail_avoided="r284 BLIK leftover leftover leftover bind. This is late BLIK after przelew leftover leftover leftover",
    token_col="blik_code",
    result_val="BLIK01",
    leftover_check="blpz_leftover_open",
    extra_col="  blik_code text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="BLIK leftover leftover leftover vs przelew leftover leftover leftover same blikCode grain",
    fail_surfaces="late BLIK leftover leftover leftover after przelew leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; BLIK posts leftover_id; przelew leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; przelew leftover leftover leftover stays",
    seed="BLIK leftover leftover leftover + przelew leftover leftover leftover same blikCode grain",
    fail_seed="przelew leftover leftover leftover posted then late BLIK leftover leftover leftover",
    counterpart="przelew leftover leftover leftover",
    key_name="blikCode",
)

leftover3(
    ok_slug="ideal-leftover-vs-sofort",
    fail_slug="ideal-after-sofort",
    stem="idso_ll",
    fail_stem="idso_lt",
    event="iDEAL leftover leftover leftover",
    fail_event="iDEAL leftover leftover leftover",
    pk="transaction_id",
    fail_pk="late_transaction_id",
    ctor="idso",
    rid="id",
    rg="ideal_leftover|sofort_leftover|transactionId",
    fail_rg="late_ideal|sofort_posted|transactionId",
    avoided="r278 UnionPay leftover already skip; r284 BLIK leftover leftover leftover",
    fail_avoided="r285 iDEAL leftover leftover leftover bind. This is late iDEAL after Sofort leftover leftover leftover",
    token_col="transaction_id",
    result_val="TXN01",
    leftover_check="idso_leftover_open",
    extra_col="  transaction_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="iDEAL leftover leftover leftover vs Sofort leftover leftover leftover same transactionId",
    fail_surfaces="late iDEAL leftover leftover leftover after Sofort leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; iDEAL posts leftover_id; Sofort leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; Sofort leftover leftover leftover stays",
    seed="iDEAL leftover leftover leftover + Sofort leftover leftover leftover same transactionId",
    fail_seed="Sofort leftover leftover leftover posted then late iDEAL leftover leftover leftover",
    counterpart="Sofort leftover leftover leftover",
    key_name="transactionId",
)

leftover3(
    ok_slug="giropay-leftover-vs-eps",
    fail_slug="giropay-after-eps",
    stem="gpep_ll",
    fail_stem="gpep_lt",
    event="Giropay leftover leftover leftover",
    fail_event="Giropay leftover leftover leftover",
    pk="bic_ref",
    fail_pk="late_bic_ref",
    ctor="gpep",
    rid="gp",
    rg="giropay_leftover|eps_leftover|bic_ref",
    fail_rg="late_giropay|eps_posted|bic_ref",
    avoided="r278 UnionPay leftover already skip; r285 iDEAL leftover leftover leftover",
    fail_avoided="r286 Giropay leftover leftover leftover bind. This is late Giropay after EPS leftover leftover leftover",
    token_col="bic_ref",
    result_val="BICREF01",
    leftover_check="gpep_leftover_open",
    extra_col="  bic_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Giropay leftover leftover leftover vs EPS leftover leftover leftover same bic+ref",
    fail_surfaces="late Giropay leftover leftover leftover after EPS leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Giropay posts leftover_id; EPS leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; EPS leftover leftover leftover stays",
    seed="Giropay leftover leftover leftover + EPS leftover leftover leftover same bic+ref",
    fail_seed="EPS leftover leftover leftover posted then late Giropay leftover leftover leftover",
    counterpart="EPS leftover leftover leftover",
    key_name="bic+ref",
)

leftover3(
    ok_slug="bancontact-leftover-vs-merchant-ref",
    fail_slug="bancontact-after-merchant-ref",
    stem="bnmr_ll",
    fail_stem="bnmr_lt",
    event="Bancontact leftover leftover leftover",
    fail_event="Bancontact leftover leftover leftover",
    pk="merchant_ref",
    fail_pk="late_merchant_ref",
    ctor="bnmr",
    rid="bc",
    rg="bancontact_leftover|merchant_ref_leftover|mref",
    fail_rg="late_bancontact|merchant_ref_posted|mref",
    avoided="r278 UnionPay leftover already skip; r286 Giropay leftover leftover leftover",
    fail_avoided="r287 Bancontact leftover leftover leftover bind. This is late Bancontact after leftover leftover leftover merchant ref",
    token_col="merchant_ref",
    result_val="MREF01",
    leftover_check="bnmr_leftover_open",
    extra_col="  merchant_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Bancontact leftover leftover leftover vs leftover leftover leftover merchant ref",
    fail_surfaces="late Bancontact leftover leftover leftover after leftover leftover leftover merchant ref posted",
    this_is="leftover leftover leftover bind; Bancontact posts leftover_id; leftover leftover leftover merchant ref binds only",
    fail_this="late leftover leftover leftover flags; leftover leftover leftover merchant ref stays",
    seed="Bancontact leftover leftover leftover + leftover leftover leftover merchant ref",
    fail_seed="leftover leftover leftover merchant ref posted then late Bancontact leftover leftover leftover",
    counterpart="leftover leftover leftover merchant ref",
    key_name="merchant_ref",
)

leftover3(
    ok_slug="mbway-leftover-vs-multibanco",
    fail_slug="mbway-after-multibanco",
    stem="mbmb_ll",
    fail_stem="mbmb_lt",
    event="MB WAY leftover leftover leftover",
    fail_event="MB WAY leftover leftover leftover",
    pk="entity_id",
    fail_pk="late_entity_id",
    ctor="mbmb",
    rid="mw",
    rg="mbway_leftover|multibanco_leftover|entity",
    fail_rg="late_mbway|multibanco_posted|entity",
    avoided="r278 UnionPay leftover already skip; r287 Bancontact leftover leftover leftover",
    fail_avoided="r288 MB WAY leftover leftover leftover bind. This is late MB WAY after Multibanco leftover leftover leftover",
    token_col="entity",
    result_val="ENT01",
    leftover_check="mbmb_leftover_open",
    extra_col="  entity text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="MB WAY leftover leftover leftover vs Multibanco leftover leftover leftover same entity",
    fail_surfaces="late MB WAY leftover leftover leftover after Multibanco leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; MB WAY posts leftover_id; Multibanco leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; Multibanco leftover leftover leftover stays",
    seed="MB WAY leftover leftover leftover + Multibanco leftover leftover leftover same entity",
    fail_seed="Multibanco leftover leftover leftover posted then late MB WAY leftover leftover leftover",
    counterpart="Multibanco leftover leftover leftover",
    key_name="entity",
)

leftover3(
    ok_slug="paynow-leftover-vs-paylah",
    fail_slug="paynow-after-paylah",
    stem="pnpl_ll",
    fail_stem="pnpl_lt",
    event="PayNow leftover leftover leftover",
    fail_event="PayNow leftover leftover leftover",
    pk="proxy_id",
    fail_pk="late_proxy_id",
    ctor="pnpl",
    rid="pn",
    rg="paynow_leftover|paylah_leftover|proxy",
    fail_rg="late_paynow|paylah_posted|proxy",
    avoided="r278 UnionPay leftover already skip; r288 MB WAY leftover leftover leftover",
    fail_avoided="r289 PayNow leftover leftover leftover bind. This is late PayNow after PayLah leftover leftover leftover",
    token_col="proxy",
    result_val="PRX01",
    leftover_check="pnpl_leftover_open",
    extra_col="  proxy text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="PayNow leftover leftover leftover vs PayLah leftover leftover leftover same proxy",
    fail_surfaces="late PayNow leftover leftover leftover after PayLah leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; PayNow posts leftover_id; PayLah leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; PayLah leftover leftover leftover stays",
    seed="PayNow leftover leftover leftover + PayLah leftover leftover leftover same proxy",
    fail_seed="PayLah leftover leftover leftover posted then late PayNow leftover leftover leftover",
    counterpart="PayLah leftover leftover leftover",
    key_name="proxy",
)

leftover3(
    ok_slug="duitnow-leftover-vs-fpx",
    fail_slug="duitnow-leftover-after-fpx-e2e",
    stem="dnfx_ll",
    fail_stem="dnfx_lt",
    event="DuitNow leftover leftover leftover",
    fail_event="DuitNow leftover leftover leftover",
    pk="e2e_id",
    fail_pk="late_e2e_id",
    ctor="dnfx",
    rid="dn",
    rg="duitnow_leftover|fpx_leftover|endToEnd",
    fail_rg="late_duitnow|fpx_posted|endToEnd",
    avoided="r278 UnionPay leftover already skip; r289 PayNow leftover leftover leftover",
    fail_avoided="r290 DuitNow leftover leftover leftover bind. This is late DuitNow after FPX leftover leftover leftover",
    token_col="end_to_end",
    result_val="E2E02",
    leftover_check="dnfx_leftover_open",
    extra_col="  end_to_end text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="DuitNow leftover leftover leftover vs FPX leftover leftover leftover same endToEnd",
    fail_surfaces="late DuitNow leftover leftover leftover after FPX leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; DuitNow posts leftover_id; FPX leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; FPX leftover leftover leftover stays",
    seed="DuitNow leftover leftover leftover + FPX leftover leftover leftover same endToEnd",
    fail_seed="FPX leftover leftover leftover posted then late DuitNow leftover leftover leftover",
    counterpart="FPX leftover leftover leftover",
    key_name="endToEnd",
)

leftover3(
    ok_slug="afterpay-leftover-vs-zip",
    fail_slug="afterpay-after-zip",
    stem="afzp_ll",
    fail_stem="afzp_lt",
    event="Afterpay leftover leftover leftover",
    fail_event="Afterpay leftover leftover leftover",
    pk="order_token",
    fail_pk="late_order_token",
    ctor="afzp",
    rid="az",
    rg="afterpay_leftover|zip_leftover|order_token",
    fail_rg="late_afterpay|zip_posted|order_token",
    avoided="r278 UnionPay leftover already skip; r290 DuitNow leftover leftover leftover",
    fail_avoided="r291 Afterpay leftover leftover leftover bind. This is late Afterpay after Zip leftover leftover leftover",
    token_col="order_token",
    result_val="OTOK01",
    leftover_check="afzp_leftover_open",
    extra_col="  order_token text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Afterpay leftover leftover leftover vs Zip leftover leftover leftover same order token",
    fail_surfaces="late Afterpay leftover leftover leftover after Zip leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Afterpay posts leftover_id; Zip leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; Zip leftover leftover leftover stays",
    seed="Afterpay leftover leftover leftover + Zip leftover leftover leftover same order token",
    fail_seed="Zip leftover leftover leftover posted then late Afterpay leftover leftover leftover",
    counterpart="Zip leftover leftover leftover",
    key_name="order token",
)

leftover3(
    ok_slug="klarna-leftover-vs-invoice",
    fail_slug="klarna-after-invoice",
    stem="klin_ll",
    fail_stem="klin_lt",
    event="Klarna leftover leftover leftover",
    fail_event="Klarna leftover leftover leftover",
    pk="auth_token",
    fail_pk="late_auth_token",
    ctor="klin",
    rid="kl",
    rg="klarna_leftover|klarna_invoice_leftover|auth_token",
    fail_rg="late_klarna|klarna_invoice_posted|auth_token",
    avoided="r278 UnionPay leftover already skip; r291 Afterpay leftover leftover leftover",
    fail_avoided="r292 Klarna leftover leftover leftover bind. This is late Klarna after invoice leftover leftover leftover",
    token_col="auth_token",
    result_val="AUTH01",
    leftover_check="klin_leftover_open",
    extra_col="  auth_token text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Klarna leftover leftover leftover vs invoice leftover leftover leftover same auth token",
    fail_surfaces="late Klarna leftover leftover leftover after invoice leftover leftover leftover posted",
    this_is="leftover leftover leftover bind; Klarna posts leftover_id; invoice leftover leftover leftover binds only",
    fail_this="late leftover leftover leftover flags; invoice leftover leftover leftover stays",
    seed="Klarna leftover leftover leftover + invoice leftover leftover leftover same auth token",
    fail_seed="invoice leftover leftover leftover posted then late Klarna leftover leftover leftover",
    counterpart="invoice leftover leftover leftover",
    key_name="auth token",
)

leftover3(
    ok_slug="affirm-leftover-vs-capture",
    fail_slug="affirm-after-capture",
    stem="affc_ll",
    fail_stem="affc_lt",
    event="Affirm leftover leftover leftover",
    fail_event="Affirm leftover leftover leftover",
    pk="capture_id",
    fail_pk="late_capture_id",
    ctor="affc",
    rid="af",
    rg="affirm_leftover|affirm_capture_leftover|capture",
    fail_rg="late_affirm|affirm_capture_posted|capture",
    avoided="r278 UnionPay leftover already skip; r292 Klarna leftover leftover leftover",
    fail_avoided="r293 Affirm leftover leftover leftover bind. This is late Affirm after leftover leftover leftover capture",
    token_col="capture_id",
    result_val="CAP01",
    leftover_check="affc_leftover_open",
    extra_col="  capture_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Affirm leftover leftover leftover vs leftover leftover leftover capture",
    fail_surfaces="late Affirm leftover leftover leftover after leftover leftover leftover capture posted",
    this_is="leftover leftover leftover bind; Affirm posts leftover_id; leftover leftover leftover capture binds only",
    fail_this="late leftover leftover leftover flags; leftover leftover leftover capture stays",
    seed="Affirm leftover leftover leftover + leftover leftover leftover capture",
    fail_seed="leftover leftover leftover capture posted then late Affirm leftover leftover leftover",
    counterpart="leftover leftover leftover capture",
    key_name="capture",
)

leftover3(
    ok_slug="interac-leftover-vs-autodeposit",
    fail_slug="interac-after-autodeposit",
    stem="intad_ll",
    fail_stem="intad_lt",
    event="Interac leftover leftover leftover",
    fail_event="Interac leftover leftover leftover",
    pk="autodeposit_id",
    fail_pk="late_autodeposit_id",
    ctor="intad",
    rid="ir",
    rg="interac_leftover|etransfer_autodeposit|autoDeposit",
    fail_rg="late_interac|autodeposit_posted|autoDeposit",
    avoided="r278 UnionPay leftover already skip; r293 Affirm leftover leftover leftover; r109 wechat; r274 PromptPay leftover already skip",
    fail_avoided="r294 Interac leftover leftover leftover bind. This is late Interac after leftover leftover leftover e-Transfer autoDeposit",
    token_col="autodeposit",
    result_val="AD01",
    leftover_check="intad_leftover_open",
    extra_col="  autodeposit text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Interac leftover leftover leftover vs leftover leftover leftover e-Transfer autoDeposit",
    fail_surfaces="late Interac leftover leftover leftover after leftover leftover leftover e-Transfer autoDeposit posted",
    this_is="leftover leftover leftover bind; Interac posts leftover_id; leftover leftover leftover autoDeposit binds only",
    fail_this="late leftover leftover leftover flags; leftover leftover leftover autoDeposit stays",
    seed="Interac leftover leftover leftover + leftover leftover leftover e-Transfer autoDeposit",
    fail_seed="leftover leftover leftover autoDeposit posted then late Interac leftover leftover leftover",
    counterpart="leftover leftover leftover e-Transfer autoDeposit",
    key_name="autoDeposit",
)
