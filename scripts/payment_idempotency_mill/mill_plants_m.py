"""Plants r189+: leftover 3DS/SCA/AVS/CVV/MIT/CIT/COF (not r156/r160 clones, not r167–r188 cartesian)."""

from mill_plants_j import _ok_pair, _fail_pair

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def leftover(
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
    spend_check,
    gate,
    extra_col,
    fail_extra,
    surfaces,
    fail_surfaces,
    this_is,
    fail_this,
    seed,
    fail_seed,
):
    """Single-use leftover token vs capture PK; late leftover flags only."""
    fn = f"on_{stem}"
    fail_fn = f"late_{fail_stem}"
    hook_fn = f"cap_{stem}"
    fail_hook = f"already_{fail_stem}"
    test_fn = f"test_{stem}_not_cap_double"
    fail_test_fn = f"test_{fail_stem}_not_add"
    flag = f"flag_{stem}"
    claim = f"claim_{stem}"
    claim_cap = f"claim_cap_{stem}"
    claim_late = f"claim_{fail_stem}"
    rows = f"{stem}_rows"
    fail_rows = f"{fail_stem}_rows"
    xfail_fn = f"test_late_{fail_stem}_credits"
    inner = 'fulfill_ch(ev["charge_id"], ev.get("amount", 0))'
    comment = f"counted every leftover {event}"
    fail_comment = f"counted every late leftover {fail_event}"
    hook_body = f"def {hook_fn}(charge_id, cents):\n    fulfill_ch(charge_id, cents)\n"
    fail_hook_body = f"def {fail_hook}(charge_id, cents):\n    fulfill_ch(charge_id, cents)\n"
    test_body = (
        f"def {test_fn}():\n"
        f'    {fn}({ctor}("{rid}_1", charge="ch_1", amount=5000, {token_col}="{result_val}"))\n'
        f'    {fn}({ctor}("{rid}_1", charge="ch_1", amount=5000, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("ch_1", 5000)\n'
        f'    assert {flag}("ch_1") == "{result_val}" and fulfill_cents("ch_1") == 5000 and {rows}("{rid}_1") == 1\n'
        "\n"
        "def test_second():\n"
        f'    {fn}({ctor}("{rid}_a", charge="ch_a", amount=100, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("ch_a", 100)\n'
        f'    {fn}({ctor}("{rid}_b", charge="ch_b", amount=40, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("ch_b", 40)\n'
        '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
    )
    test2_body = (
        "def test_second():\n"
        f'    {fn}({ctor}("{rid}_a", charge="ch_a", amount=100, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("ch_a", 100)\n'
        f'    {fn}({ctor}("{rid}_b", charge="ch_b", amount=40, {token_col}="{result_val}"))\n'
        f'    {hook_fn}("ch_b", 40)\n'
        '    assert fulfill_cents("ch_a") == 100 and fulfill_cents("ch_b") == 40\n'
    )
    fail_test_body = (
        f"def {fail_test_fn}():\n"
        f'    {fail_hook}("ch_1", 5000)\n'
        f'    {fail_fn}({ctor}("{rid}_1", charge="ch_1", amount=5000, {token_col}="{result_val}"))\n'
        f'    {fail_fn}({ctor}("{rid}_1", charge="ch_1", amount=5000, {token_col}="{result_val}"))\n'
        f'    assert fulfill_cents("ch_1") == 5000 and {flag}("ch_1") == "{result_val}" and {fail_rows}("{rid}_1") == 1\n'
        "\n"
        "def test_second_late():\n"
        f'    {fail_hook}("ch_a", 100)\n'
        f'    {fail_fn}({ctor}("{rid}_a", charge="ch_a", amount=100, {token_col}="{result_val}"))\n'
        f'    {fail_hook}("ch_b", 40)\n'
        f'    {fail_fn}({ctor}("{rid}_b", charge="ch_b", amount=40, {token_col}="{result_val}"))\n'
        f'    assert {flag}("ch_a") == "{result_val}" and {flag}("ch_b") == "{result_val}"\n'
    )
    fail_test2 = (
        "def test_second_late():\n"
        f'    {fail_hook}("ch_a", 100)\n'
        f'    {fail_fn}({ctor}("{rid}_a", charge="ch_a", amount=100, {token_col}="{result_val}"))\n'
        f'    {fail_hook}("ch_b", 40)\n'
        f'    {fail_fn}({ctor}("{rid}_b", charge="ch_b", amount=40, {token_col}="{result_val}"))\n'
        f'    assert {flag}("ch_a") == "{result_val}" and {flag}("ch_b") == "{result_val}"\n'
    )
    rewrite_src = (
        f"def {fn}(ev):\n"
        f"    if not {claim}(ev['{pk}']):\n"
        '        return {"ok": True, "dup": True}\n'
        f"    if not {spend_check}(ev.get('{token_col}')):\n"
        '        return {"ok": True, "spent": True}\n'
        f'    {flag}(ev["charge_id"], ev.get("{token_col}") or "{result_val}")\n'
        '    return {"ok": True, "left": True}\n'
    )
    fail_rewrite_src = (
        f"def {fail_fn}(ev):\n"
        f"    if not {claim_late}(ev.get('{fail_pk}') or ev['charge_id']+'_l'):\n"
        '        return {"ok": True, "dup": True}\n'
        f'    {flag}(ev["charge_id"], ev.get("{token_col}") or "{result_val}")\n'
        '    return {"ok": True, "flagged": True}\n'
    )
    rewrite_hook = (
        f"def {hook_fn}(charge_id, cents):\n"
        f"    if {gate}:\n"
        '        return {"ok": True, "blocked": True}\n'
        f"    if not {claim_cap}(charge_id):\n"
        '        return {"ok": True, "dup": True}\n'
        "    fulfill_ch(charge_id, cents)\n"
        '    return {"ok": True}\n'
    )
    fail_rewrite_hook = (
        f"def {fail_hook}(charge_id, cents):\n"
        f"    if not claim_cap2_{fail_stem}(charge_id):\n"
        "        return existing_cap(charge_id)\n"
        "    fulfill_ch(charge_id, cents)\n"
        "    return charge_id\n"
    )
    xfail_body = (
        f"def {xfail_fn}():\n"
        f'    {fail_hook}("ch_p", 5000)\n'
        f'    {fail_fn}({ctor}("{rid}_p", charge="ch_p", amount=5000, {token_col}="{result_val}"))\n'
        '    assert fulfill_cents("ch_p") == 10000\n'
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
            first_apply=f"{event} leftover today",
            plan_change=f"{event} leftover records; capture PK charge_id; spent token blocks",
            step_note="Leftover-day 6–7; PK 8–11; second charge 12–13.",
            skip_pred=f"this {event} leftover already spent today",
            verb="fulfill",
            skip_label=f"{event}-leftover-today skip",
            obs3=f"{event} leftover and capture both fulfill",
            obs4=f"{event} leftover records; capture PK",
            obs5="capture once; leftover no extra; second charge adds",
            fail_obs=(
                f"FAILED {test_fn} - {rows} 3 == 1 or credited on leftover\n"
                "1 failed, 1 passed"
            ),
            obs7="capture still fulfills; new leftover same day dropped.",
            still_fail_obs=(
                f"FAILED {test_fn} - leftover still fulfills or capture adds\n"
                "1 failed, 1 passed"
            ),
            rewrite_src=rewrite_src,
            rewrite_src_obs=f"claim {pk}; {spend_check} single-use",
            rewrite_hook=rewrite_hook,
            rewrite_hook_obs="PK charge_id after leftover pass",
            extra_ddl=extra_col,
            residual=f"{event} leftover last-write vs capture",
            grep_pat=claim_cap,
            grep_obs=f"src/{stem}.py: leftover {event} flags; capture PK",
            goal=(
                f"till-{stem} leftover {event} and capture both fulfilled ch_1. "
                f"Leftover records; capture PK. Gate: tests/test_{stem}.py."
            ),
            plan=f"Skip fulfill if this {event} leftover already spent today.",
            outcome=(
                f"{event}+capture double-fulfilled. Leftover-day skip left capture unguarded. "
                "Plan change: leftover records; PK charge_id. Tests 2/2 + second charge + suite 8/8."
            ),
            skip_new=(
                f'    if not {stem}_today(ev["{pk}"]):\n'
                '        fulfill_ch(ev["charge_id"], ev.get("amount", 0))'
            ),
            psql_rows=f"{rid}_1\n{rid}_a\n{rid}_b",
            test_name=f"{stem}-not-cap-double test",
            surface_read=f"{event} leftover plus capture",
        ),
        _fail_pair(
            slug=fail_slug,
            stem=fail_stem,
            fn=fail_fn,
            inner=inner,
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
            first_apply=f"late {fail_event} leftover posted today",
            plan_change=f"late {fail_event} leftover PK flags; capture stays",
            step_note="Late-leftover 6–7; PK 8–11; second 12–13; extra xfail 15–17.",
            next_note=(
                f"Unused: late {fail_event} leftover should extra-fulfill. "
                f"Avoid late-{fail_event}-leftover-today skip."
            ),
            skip_pred=f"this late {fail_event} leftover already posted today",
            verb="fulfill",
            skip_label=f"late-{fail_event}-leftover-today skip",
            obs3=f"late {fail_event} leftover extra-fulfills",
            obs4=f"late {fail_event} leftover flags; capture stays",
            obs5="fulfill 5000; flagged; second late adds",
            fail_obs=(
                f"FAILED {fail_test_fn} - fulfill 10000 == 5000 or rows 3\n"
                "1 failed, 1 passed"
            ),
            obs7="second late ok; hides leftover flag.",
            still_fail_obs=(
                "FAILED if late leftover extra-fulfilled (10000)\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=fail_rewrite_src,
            rewrite_src_obs=f"claim {fail_pk} flags leftover",
            rewrite_hook=fail_rewrite_hook,
            rewrite_hook_obs="capture stays",
            extra_ddl=fail_extra,
            xfail_label=f"late {fail_event} leftover should extra-fulfill",
            xfail_body=xfail_body,
            xfail_fail_obs=(
                f"FAILED {xfail_fn} - flagged; fulfill stayed 5000\n1 failed"
            ),
            xfail_fn=xfail_fn,
            xfail_reason=(
                f"late {fail_event} leftover extra-fulfill vs flag-only is a policy fork"
            ),
            goal=(
                f"till-{fail_stem} late leftover {fail_event} extra-fulfilled ch_1. "
                f"Late flags. Gate: tests/test_{fail_stem}.py."
            ),
            plan=f"Skip fulfill if this late {fail_event} leftover already posted today.",
            outcome=(
                f"Late {fail_event} leftover extra-fulfilled. Late-day skip hid flag. "
                "Plan change: late PK flag. Primary+second pass. Partial: extra xfail handoff."
            ),
            skip_new=(
                f'    if not {fail_stem}_today(ev["charge_id"]):\n'
                '        fulfill_ch(ev["charge_id"], ev.get("amount", 0))'
            ),
            test_name=f"{fail_stem}-not-add test",
            surface_read=f"late {fail_event} leftover plus captured charge",
            test_body_short=f"same — late {fail_event} leftover flags; capture stays",
        ),
    )


# r189 3DS CAVV leftover vs capture (not r156 transStatus Y)
leftover(
    ok_slug="cavv-leftover-vs-capture",
    fail_slug="cavv-after-captured",
    stem="cav_lv",
    fail_stem="cav_lt",
    event="CAVV",
    fail_event="CAVV",
    pk="cavv_id",
    fail_pk="late_cavv_id",
    ctor="cav",
    rid="cv",
    rg="cavv|authenticationValue|eci|dsTransID",
    fail_rg="late_cavv|spent_cryptogram|after_capture",
    avoided="r156 3DS transStatus vs capture; r167 hotel. This is single-use CAVV leftover vs capture",
    fail_avoided="r189 CAVV leftover vs capture. This is late CAVV after captured must not extra-fulfill",
    token_col="cavv",
    result_val="CAVV01",
    spend_check="single_use_cavv",
    gate='flag_cav_lv(charge_id) != "CAVV01"',
    extra_col="  cavv text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS CAVV leftover vs capture",
    fail_surfaces="late CAVV leftover after captured",
    this_is="CAVV leftover records; capture PK charge_id; spent cryptogram blocks",
    fail_this="late CAVV leftover flags; capture stays",
    seed="CAVV leftover + capture same charge_id",
    fail_seed="capture then late CAVV leftover",
)

# r190 3DS method-url leftover vs challenge
leftover(
    ok_slug="method-leftover-vs-challenge",
    fail_slug="method-after-challenge",
    stem="mth_lv",
    fail_stem="mth_lt",
    event="3DS method",
    fail_event="3DS method",
    pk="method_id",
    fail_pk="late_method_id",
    ctor="mth",
    rid="mh",
    rg="threeDSMethodData|threeDSServerTransID|methodNotificationURL",
    fail_rg="late_method|fingerprint_spent|after_challenge",
    avoided="r189 CAVV leftover; r156 transStatus Y. This is 3DS method URL leftover vs challenge",
    fail_avoided="r190 method leftover vs challenge. This is late method after challenge flags only",
    token_col="method_data",
    result_val="MTH01",
    spend_check="method_notified",
    gate='flag_mth_lv(charge_id) != "MTH01"',
    extra_col="  method_data text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS method-url leftover vs challenge capture",
    fail_surfaces="late 3DS method leftover after challenge",
    this_is="method leftover records; challenge capture PK; notified method blocks replay",
    fail_this="late method leftover flags; challenge stays",
    seed="3DS method leftover + challenge same charge_id",
    fail_seed="challenge then late method leftover",
)

# r191 SCA TRA exemption leftover vs step-up
leftover(
    ok_slug="tra-exemption-leftover-vs-stepup",
    fail_slug="tra-after-stepup",
    stem="tra_lv",
    fail_stem="tra_lt",
    event="TRA exemption",
    fail_event="TRA exemption",
    pk="tra_id",
    fail_pk="late_tra_id",
    ctor="tra",
    rid="tr",
    rg="sca_tra|exemption_indicator|transaction_risk_analysis",
    fail_rg="late_tra|exemption_spent|after_stepup",
    avoided="r156 3DS challenge; r160 MIT vs CIT. This is SCA TRA exemption leftover vs step-up",
    fail_avoided="r191 TRA leftover vs step-up. This is late TRA after step-up captured flags only",
    token_col="tra_score",
    result_val="TRA05",
    spend_check="tra_window_open",
    gate='flag_tra_lv(charge_id) != "TRA05"',
    extra_col="  tra_score text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="SCA TRA exemption leftover vs step-up capture",
    fail_surfaces="late TRA exemption leftover after step-up",
    this_is="TRA leftover records; step-up capture PK; spent exemption blocks",
    fail_this="late TRA leftover flags; step-up stays",
    seed="TRA exemption leftover + step-up same charge_id",
    fail_seed="step-up then late TRA leftover",
)

# r192 SCA LVP leftover vs cumulative cap
leftover(
    ok_slug="lvp-exemption-leftover-vs-cap",
    fail_slug="lvp-after-captured",
    stem="lvp_lv",
    fail_stem="lvp_lt",
    event="LVP exemption",
    fail_event="LVP exemption",
    pk="lvp_id",
    fail_pk="late_lvp_id",
    ctor="lvp",
    rid="lv",
    rg="low_value_exemption|lvp_cumulative|psd2_lvp",
    fail_rg="late_lvp|lvp_cap_spent|after_capture",
    avoided="r191 TRA leftover; r156 3DS. This is SCA low-value exemption leftover vs capture",
    fail_avoided="r192 LVP leftover vs capture. This is late LVP after captured flags only",
    token_col="lvp_token",
    result_val="LVP30",
    spend_check="lvp_under_cap",
    gate='flag_lvp_lv(charge_id) != "LVP30"',
    extra_col="  lvp_token text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="SCA LVP leftover vs capture",
    fail_surfaces="late LVP leftover after captured",
    this_is="LVP leftover records; capture PK; over-cap leftover blocks",
    fail_this="late LVP leftover flags; capture stays",
    seed="LVP leftover + capture same charge_id",
    fail_seed="capture then late LVP leftover",
)

# r193 AVS postal leftover vs capture
leftover(
    ok_slug="avs-postal-leftover-vs-capture",
    fail_slug="avs-after-captured",
    stem="avs_lv",
    fail_stem="avs_lt",
    event="AVS postal",
    fail_event="AVS postal",
    pk="avs_id",
    fail_pk="late_avs_id",
    ctor="avs",
    rid="az",
    rg="avs_result|postal_match|zip_check",
    fail_rg="late_avs|postal_spent|after_capture",
    avoided="r156 3DS; r160 MIT. This is AVS ZIP leftover vs capture",
    fail_avoided="r193 AVS postal leftover vs capture. This is late AVS after captured flags only",
    token_col="avs_code",
    result_val="Y",
    spend_check="avs_postal_ok",
    gate='flag_avs_lv(charge_id) not in ("Y", "A", "W", "X", "Z")',
    extra_col="  avs_code text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="AVS postal leftover vs capture",
    fail_surfaces="late AVS postal leftover after captured",
    this_is="AVS postal leftover records; capture PK; fail codes block",
    fail_this="late AVS leftover flags; capture stays",
    seed="AVS Y leftover + capture same charge_id",
    fail_seed="capture then late AVS leftover",
)

# r194 AVS street leftover vs ZIP
leftover(
    ok_slug="avs-street-leftover-vs-zip",
    fail_slug="street-after-zip",
    stem="str_lv",
    fail_stem="str_lt",
    event="AVS street",
    fail_event="AVS street",
    pk="street_id",
    fail_pk="late_street_id",
    ctor="strt",
    rid="as",
    rg="avs_street|address_match|street_check",
    fail_rg="late_street|street_spent|after_zip",
    avoided="r193 AVS postal leftover. This is AVS street leftover vs ZIP leftover",
    fail_avoided="r194 AVS street leftover vs ZIP. This is late street after ZIP captured flags only",
    token_col="street_code",
    result_val="A",
    spend_check="avs_street_ok",
    gate='flag_str_lv(charge_id) not in ("A", "Y", "X")',
    extra_col="  street_code text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="AVS street leftover vs ZIP capture",
    fail_surfaces="late AVS street leftover after ZIP",
    this_is="AVS street leftover records; ZIP capture PK; street fail blocks",
    fail_this="late street leftover flags; ZIP stays",
    seed="AVS street leftover + ZIP capture same charge_id",
    fail_seed="ZIP then late street leftover",
)

# r195 CVV match leftover vs capture
leftover(
    ok_slug="cvv-match-leftover-vs-capture",
    fail_slug="cvv-after-captured",
    stem="cvv_lv",
    fail_stem="cvv_lt",
    event="CVV match",
    fail_event="CVV match",
    pk="cvv_id",
    fail_pk="late_cvv_id",
    ctor="cvv",
    rid="cm",
    rg="cvv_result|cvv2_match|cvc_check",
    fail_rg="late_cvv|cvv_spent|after_capture",
    avoided="r193 AVS leftover; r156 3DS. This is CVV M leftover vs capture",
    fail_avoided="r195 CVV leftover vs capture. This is late CVV after captured flags only",
    token_col="cvv_code",
    result_val="M",
    spend_check="cvv_matched",
    gate='flag_cvv_lv(charge_id) != "M"',
    extra_col="  cvv_code text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="CVV match leftover vs capture",
    fail_surfaces="late CVV leftover after captured",
    this_is="CVV leftover records; capture PK; N/P/U block",
    fail_this="late CVV leftover flags; capture stays",
    seed="CVV M leftover + capture same charge_id",
    fail_seed="capture then late CVV leftover",
)

# r196 iCVV leftover vs typed CVV
leftover(
    ok_slug="icvv-leftover-vs-cvv",
    fail_slug="icvv-after-cvv",
    stem="icv_lv",
    fail_stem="icv_lt",
    event="iCVV",
    fail_event="iCVV",
    pk="icvv_id",
    fail_pk="late_icvv_id",
    ctor="icv",
    rid="ic",
    rg="icvv|contactless_cvc3|dcvv",
    fail_rg="late_icvv|icvv_spent|after_cvv",
    avoided="r195 CVV match leftover. This is contactless iCVV leftover vs typed CVV",
    fail_avoided="r196 iCVV leftover vs CVV. This is late iCVV after typed CVV captured flags only",
    token_col="icvv",
    result_val="ICV1",
    spend_check="icvv_ok",
    gate='flag_icv_lv(charge_id) != "ICV1"',
    extra_col="  icvv text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="iCVV leftover vs typed CVV capture",
    fail_surfaces="late iCVV leftover after typed CVV",
    this_is="iCVV leftover records; typed CVV capture PK; spent iCVV blocks",
    fail_this="late iCVV leftover flags; typed CVV stays",
    seed="iCVV leftover + typed CVV same charge_id",
    fail_seed="typed CVV then late iCVV leftover",
)

# r197 MIT leftover vs unscheduled COF (not r160 MIT vs CIT)
leftover(
    ok_slug="mit-ucof-leftover-vs-recurring",
    fail_slug="ucof-after-recurring",
    stem="uco_lv",
    fail_stem="uco_lt",
    event="UCOF MIT",
    fail_event="UCOF MIT",
    pk="ucof_id",
    fail_pk="late_ucof_id",
    ctor="uco",
    rid="uc",
    rg="unscheduled_cof|ucof|mit_indicator",
    fail_rg="late_ucof|ucof_spent|after_recurring",
    avoided="r160 MIT vs CIT capture. This is unscheduled MIT leftover vs recurring MIT",
    fail_avoided="r197 UCOF leftover vs recurring. This is late UCOF after recurring captured flags only",
    token_col="ucof_nti",
    result_val="UCOF1",
    spend_check="ucof_allowed",
    gate='flag_uco_lv(charge_id) != "UCOF1"',
    extra_col="  ucof_nti text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="MIT UCOF leftover vs recurring MIT",
    fail_surfaces="late UCOF leftover after recurring MIT",
    this_is="UCOF leftover records; recurring capture PK; spent UCOF blocks",
    fail_this="late UCOF leftover flags; recurring stays",
    seed="UCOF leftover + recurring MIT same charge_id",
    fail_seed="recurring then late UCOF leftover",
)

# r198 CIT leftover vs stored-credential first
leftover(
    ok_slug="cit-leftover-vs-cof",
    fail_slug="cit-after-cof",
    stem="cit_lv",
    fail_stem="cit_lt",
    event="CIT leftover",
    fail_event="CIT leftover",
    pk="cit_id",
    fail_pk="late_cit_id",
    ctor="cit",
    rid="ci",
    rg="customer_initiated|cit_indicator|stored_credential_first",
    fail_rg="late_cit|cit_spent|after_cof",
    avoided="r160 MIT vs CIT; r197 UCOF leftover. This is CIT leftover establishing COF vs first store",
    fail_avoided="r198 CIT leftover vs COF. This is late CIT after COF established flags only",
    token_col="cit_nti",
    result_val="CIT1",
    spend_check="cit_first_store",
    gate='flag_cit_lv(charge_id) != "CIT1"',
    extra_col="  cit_nti text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="CIT leftover vs COF first-store capture",
    fail_surfaces="late CIT leftover after COF established",
    this_is="CIT leftover records; COF capture PK; spent CIT blocks",
    fail_this="late CIT leftover flags; COF stays",
    seed="CIT leftover + COF first-store same charge_id",
    fail_seed="COF then late CIT leftover",
)

# r199 stored-credential NTI leftover vs subsequent MIT
leftover(
    ok_slug="nti-leftover-vs-mit",
    fail_slug="nti-after-mit",
    stem="nti_lv",
    fail_stem="nti_lt",
    event="NTI leftover",
    fail_event="NTI leftover",
    pk="nti_id",
    fail_pk="late_nti_id",
    ctor="nti",
    rid="nt",
    rg="network_transaction_id|stored_credential|original_network_id",
    fail_rg="late_nti|nti_spent|after_mit",
    avoided="r198 CIT leftover; r160 MIT vs CIT. This is stored-credential NTI leftover vs subsequent MIT",
    fail_avoided="r199 NTI leftover vs MIT. This is late NTI after MIT captured flags only",
    token_col="nti",
    result_val="NTI9",
    spend_check="nti_bound",
    gate='flag_nti_lv(charge_id) != "NTI9"',
    extra_col="  nti text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="stored-credential NTI leftover vs subsequent MIT",
    fail_surfaces="late NTI leftover after MIT",
    this_is="NTI leftover records; MIT capture PK; unbound NTI blocks",
    fail_this="late NTI leftover flags; MIT stays",
    seed="NTI leftover + subsequent MIT same charge_id",
    fail_seed="MIT then late NTI leftover",
)

# r200 COF leftover vs PAN refresh
leftover(
    ok_slug="cof-leftover-vs-pan",
    fail_slug="cof-after-pan",
    stem="cof_lv",
    fail_stem="cof_lt",
    event="COF leftover",
    fail_event="COF leftover",
    pk="cof_id",
    fail_pk="late_cof_id",
    ctor="cof",
    rid="cf",
    rg="card_on_file|cof_pan|credentials_on_file",
    fail_rg="late_cof|cof_spent|after_pan",
    avoided="r162 account updater vs PAN; r199 NTI leftover. This is COF leftover vs PAN refresh",
    fail_avoided="r200 COF leftover vs PAN. This is late COF after PAN refresh captured flags only",
    token_col="cof_pan",
    result_val="COF1",
    spend_check="cof_pan_current",
    gate='flag_cof_lv(charge_id) != "COF1"',
    extra_col="  cof_pan text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="COF leftover vs PAN refresh capture",
    fail_surfaces="late COF leftover after PAN refresh",
    this_is="COF leftover records; PAN capture PK; stale COF blocks",
    fail_this="late COF leftover flags; PAN stays",
    seed="COF leftover + PAN refresh same charge_id",
    fail_seed="PAN refresh then late COF leftover",
)

# r201 3DS frictionless leftover vs challenge
leftover(
    ok_slug="frictionless-leftover-vs-challenge",
    fail_slug="fric-after-challenge",
    stem="fri_lv",
    fail_stem="fri_lt",
    event="frictionless 3DS",
    fail_event="frictionless 3DS",
    pk="fric_id",
    fail_pk="late_fric_id",
    ctor="fri",
    rid="fr",
    rg="frictionless|transStatus_Y|eci05",
    fail_rg="late_fric|frictionless_spent|after_challenge",
    avoided="r156 challenge vs capture; r189 CAVV leftover. This is frictionless leftover vs challenge",
    fail_avoided="r201 frictionless leftover vs challenge. This is late frictionless after challenge flags only",
    token_col="fric_eci",
    result_val="ECI05",
    spend_check="frictionless_ok",
    gate='flag_fri_lv(charge_id) != "ECI05"',
    extra_col="  fric_eci text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS frictionless leftover vs challenge capture",
    fail_surfaces="late frictionless leftover after challenge",
    this_is="frictionless leftover records; challenge capture PK; spent ECI blocks",
    fail_this="late frictionless leftover flags; challenge stays",
    seed="frictionless leftover + challenge same charge_id",
    fail_seed="challenge then late frictionless leftover",
)

# r202 SCA delegated leftover vs issuer challenge
leftover(
    ok_slug="delegated-sca-leftover-vs-issuer",
    fail_slug="delg-after-issuer",
    stem="del_lv",
    fail_stem="del_lt",
    event="delegated SCA",
    fail_event="delegated SCA",
    pk="delg_id",
    fail_pk="late_delg_id",
    ctor="dlg",
    rid="dg",
    rg="delegated_authentication|out_of_band|wallet_sca",
    fail_rg="late_delg|delegated_spent|after_issuer",
    avoided="r191 TRA leftover; r156 3DS. This is delegated SCA leftover vs issuer challenge",
    fail_avoided="r202 delegated leftover vs issuer. This is late delegated after issuer captured flags only",
    token_col="delg_token",
    result_val="DELG1",
    spend_check="delegated_ok",
    gate='flag_del_lv(charge_id) != "DELG1"',
    extra_col="  delg_token text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="SCA delegated leftover vs issuer challenge",
    fail_surfaces="late delegated leftover after issuer challenge",
    this_is="delegated leftover records; issuer capture PK; spent delegated blocks",
    fail_this="late delegated leftover flags; issuer stays",
    seed="delegated leftover + issuer challenge same charge_id",
    fail_seed="issuer then late delegated leftover",
)

# r203 MIT series leftover vs mandate cancel
leftover(
    ok_slug="mit-series-leftover-vs-cancel",
    fail_slug="series-after-cancel",
    stem="ser_lv",
    fail_stem="ser_lt",
    event="MIT series",
    fail_event="MIT series",
    pk="series_id",
    fail_pk="late_series_id",
    ctor="ser",
    rid="se",
    rg="mit_series|recurring_mandate|series_nti",
    fail_rg="late_series|mandate_cancelled|after_cancel",
    avoided="r197 UCOF leftover; r160 MIT vs CIT. This is MIT series leftover vs mandate cancel",
    fail_avoided="r203 MIT series leftover vs cancel. This is late series after mandate cancelled flags only",
    token_col="series_nti",
    result_val="SER1",
    spend_check="series_active",
    gate='flag_ser_lv(charge_id) != "SER1"',
    extra_col="  series_nti text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="MIT series leftover vs mandate-cancel capture",
    fail_surfaces="late MIT series leftover after mandate cancel",
    this_is="series leftover records; cancel capture PK; cancelled series blocks",
    fail_this="late series leftover flags; cancel stays",
    seed="MIT series leftover + mandate cancel same charge_id",
    fail_seed="mandate cancel then late series leftover",
)

# r204 first-COF leftover vs 3DS
leftover(
    ok_slug="first-cof-leftover-vs-threeds",
    fail_slug="fcof-after-threeds",
    stem="fcf_lv",
    fail_stem="fcf_lt",
    event="first-COF",
    fail_event="first-COF",
    pk="fcof_id",
    fail_pk="late_fcof_id",
    ctor="fcf",
    rid="fc",
    rg="first_cof|initial_cit|three_ds_for_store",
    fail_rg="late_fcof|first_store_spent|after_threeds",
    avoided="r198 CIT leftover; r156 3DS challenge. This is first-COF leftover vs 3DS for store",
    fail_avoided="r204 first-COF leftover vs 3DS. This is late first-COF after 3DS captured flags only",
    token_col="fcof_ds",
    result_val="FCOF1",
    spend_check="fcof_challenged",
    gate='flag_fcf_lv(charge_id) != "FCOF1"',
    extra_col="  fcof_ds text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="first-COF leftover vs 3DS-for-store capture",
    fail_surfaces="late first-COF leftover after 3DS store",
    this_is="first-COF leftover records; 3DS store capture PK; unchallenged store blocks",
    fail_this="late first-COF leftover flags; 3DS store stays",
    seed="first-COF leftover + 3DS store same charge_id",
    fail_seed="3DS store then late first-COF leftover",
)

# r205 3DS challenge leftover vs ACS (not r156 transStatus vs capture)
leftover(
    ok_slug="threeds-challenge-leftover-vs-acs",
    fail_slug="challenge-after-acs",
    stem="acs_lv",
    fail_stem="acs_lt",
    event="3DS challenge leftover",
    fail_event="3DS challenge leftover",
    pk="acs_id",
    fail_pk="late_acs_id",
    ctor="acs",
    rid="ac",
    rg="acsTransID|challenge_result|transStatus_leftover",
    fail_rg="late_acs|challenge_spent|after_acs",
    avoided="r156 3DS Y vs capture; r189 CAVV leftover. This is ACS challenge leftover vs ACS session",
    fail_avoided="r205 challenge leftover vs ACS. This is late challenge after ACS captured flags only",
    token_col="acs_result",
    result_val="C",
    spend_check="acs_challenge_open",
    gate='flag_acs_lv(charge_id) != "C"',
    extra_col="  acs_result text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS challenge leftover vs ACS session capture",
    fail_surfaces="late 3DS challenge leftover after ACS",
    this_is="challenge leftover records; ACS capture PK; spent ACS blocks",
    fail_this="late challenge leftover flags; ACS stays",
    seed="3DS challenge leftover + ACS same charge_id",
    fail_seed="ACS then late challenge leftover",
)

# r206 SCA exemption leftover vs capture (not TRA/LVP)
leftover(
    ok_slug="sca-exemption-leftover-vs-capture",
    fail_slug="exemption-after-captured",
    stem="exa_lv",
    fail_stem="exa_lt",
    event="SCA exemption leftover",
    fail_event="SCA exemption leftover",
    pk="exa_id",
    fail_pk="late_exa_id",
    ctor="exa",
    rid="ex",
    rg="sca_exemption|exemption_leftover|one_leg_out",
    fail_rg="late_exa|exemption_spent|after_capture",
    avoided="r191 TRA leftover; r192 LVP leftover. This is generic SCA exemption leftover vs capture",
    fail_avoided="r206 SCA exemption leftover vs capture. This is late exemption after captured flags only",
    token_col="exa_code",
    result_val="OLO",
    spend_check="exemption_valid",
    gate='flag_exa_lv(charge_id) != "OLO"',
    extra_col="  exa_code text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="SCA exemption leftover vs capture",
    fail_surfaces="late SCA exemption leftover after captured",
    this_is="exemption leftover records; capture PK; spent exemption blocks",
    fail_this="late exemption leftover flags; capture stays",
    seed="SCA exemption leftover + capture same charge_id",
    fail_seed="capture then late exemption leftover",
)

# r207 trusted-beneficiary leftover vs SCA
leftover(
    ok_slug="trusted-beneficiary-leftover-vs-sca",
    fail_slug="tb-after-sca",
    stem="trb_lv",
    fail_stem="trb_lt",
    event="trusted-beneficiary",
    fail_event="trusted-beneficiary",
    pk="tb_id",
    fail_pk="late_tb_id",
    ctor="trb",
    rid="tb",
    rg="trusted_beneficiary|whitelist_exemption|tb_leftover",
    fail_rg="late_tb|tb_spent|after_sca",
    avoided="r206 SCA exemption leftover; r191 TRA. This is trusted-beneficiary leftover vs SCA capture",
    fail_avoided="r207 TB leftover vs SCA. This is late TB after SCA captured flags only",
    token_col="tb_token",
    result_val="TB1",
    spend_check="tb_whitelisted",
    gate='flag_trb_lv(charge_id) != "TB1"',
    extra_col="  tb_token text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="trusted-beneficiary leftover vs SCA capture",
    fail_surfaces="late TB leftover after SCA",
    this_is="TB leftover records; SCA capture PK; revoked TB blocks",
    fail_this="late TB leftover flags; SCA stays",
    seed="TB leftover + SCA capture same charge_id",
    fail_seed="SCA then late TB leftover",
)

# r208 stored-credential usage leftover vs CIT
leftover(
    ok_slug="stored-cred-usage-leftover-vs-cit",
    fail_slug="usage-after-cit",
    stem="scu_lv",
    fail_stem="scu_lt",
    event="stored-cred usage",
    fail_event="stored-cred usage",
    pk="usage_id",
    fail_pk="late_usage_id",
    ctor="scu",
    rid="su",
    rg="stored_credential_usage|usage_leftover|cit_reuse",
    fail_rg="late_usage|usage_spent|after_cit",
    avoided="r199 NTI leftover; r198 CIT leftover. This is stored-credential usage leftover vs CIT",
    fail_avoided="r208 usage leftover vs CIT. This is late usage after CIT captured flags only",
    token_col="usage_nti",
    result_val="USE1",
    spend_check="usage_allowed",
    gate='flag_scu_lv(charge_id) != "USE1"',
    extra_col="  usage_nti text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="stored-credential usage leftover vs CIT capture",
    fail_surfaces="late stored-cred usage leftover after CIT",
    this_is="usage leftover records; CIT capture PK; spent usage blocks",
    fail_this="late usage leftover flags; CIT stays",
    seed="stored-cred usage leftover + CIT same charge_id",
    fail_seed="CIT then late usage leftover",
)

# r231 3DS requestor challenge indicator leftover
leftover(
    ok_slug="requestor-challenge-leftover-vs-frictionless",
    fail_slug="requestor-after-frictionless",
    stem="rci_lv",
    fail_stem="rci_lt",
    event="requestor challenge",
    fail_event="requestor challenge",
    pk="rci_id",
    fail_pk="late_rci_id",
    ctor="rci",
    rid="rc",
    rg="threeDSRequestorChallengeInd|challenge_requested|rci_leftover",
    fail_rg="late_rci|rci_spent|after_frictionless",
    avoided="r223 frictionless leftover; r227 ACS challenge leftover. This is requestor challengeInd leftover vs frictionless",
    fail_avoided="r231 requestor leftover vs frictionless. This is late requestor after frictionless captured flags only",
    token_col="rci",
    result_val="04",
    spend_check="rci_challenge_requested",
    gate='flag_rci_lv(charge_id) != "04"',
    extra_col="  rci text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS requestor challenge leftover vs frictionless capture",
    fail_surfaces="late requestor challenge leftover after frictionless",
    this_is="requestor leftover records; frictionless capture PK; spent RCI blocks",
    fail_this="late requestor leftover flags; frictionless stays",
    seed="requestor challenge leftover + frictionless same charge_id",
    fail_seed="frictionless then late requestor leftover",
)

# r232 3DS dsTransID leftover vs CAVV
leftover(
    ok_slug="dstrans-leftover-vs-cavv",
    fail_slug="dstrans-after-cavv",
    stem="dst_lv",
    fail_stem="dst_lt",
    event="dsTransID leftover",
    fail_event="dsTransID leftover",
    pk="dst_id",
    fail_pk="late_dst_id",
    ctor="dst",
    rid="ds",
    rg="dsTransID|directory_server|dst_leftover",
    fail_rg="late_dst|dst_spent|after_cavv",
    avoided="r211 CAVV leftover; r227 ACS leftover. This is dsTransID leftover vs CAVV",
    fail_avoided="r232 dsTransID leftover vs CAVV. This is late dsTransID after CAVV captured flags only",
    token_col="ds_trans",
    result_val="DST1",
    spend_check="dst_bound",
    gate='flag_dst_lv(charge_id) != "DST1"',
    extra_col="  ds_trans text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS dsTransID leftover vs CAVV capture",
    fail_surfaces="late dsTransID leftover after CAVV",
    this_is="dsTransID leftover records; CAVV capture PK; unbound DS blocks",
    fail_this="late dsTransID leftover flags; CAVV stays",
    seed="dsTransID leftover + CAVV same charge_id",
    fail_seed="CAVV then late dsTransID leftover",
)

# r233 AVS international leftover vs domestic
leftover(
    ok_slug="avs-intl-leftover-vs-domestic",
    fail_slug="intl-after-domestic",
    stem="avi_lv",
    fail_stem="avi_lt",
    event="AVS international",
    fail_event="AVS international",
    pk="avi_id",
    fail_pk="late_avi_id",
    ctor="avi",
    rid="ai",
    rg="avs_international|intl_postal|g_code",
    fail_rg="late_avi|intl_spent|after_domestic",
    avoided="r215 AVS postal leftover; r216 AVS street. This is AVS international leftover vs domestic ZIP",
    fail_avoided="r233 AVS intl leftover vs domestic. This is late intl after domestic captured flags only",
    token_col="intl_code",
    result_val="G",
    spend_check="avs_intl_ok",
    gate='flag_avi_lv(charge_id) not in ("G", "D", "M")',
    extra_col="  intl_code text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="AVS international leftover vs domestic capture",
    fail_surfaces="late AVS international leftover after domestic",
    this_is="AVS intl leftover records; domestic capture PK; fail codes block",
    fail_this="late AVS intl leftover flags; domestic stays",
    seed="AVS G leftover + domestic same charge_id",
    fail_seed="domestic then late AVS intl leftover",
)

# r234 CVV retry leftover vs match
leftover(
    ok_slug="cvv-retry-leftover-vs-match",
    fail_slug="retry-after-match",
    stem="cvr_lv",
    fail_stem="cvr_lt",
    event="CVV retry",
    fail_event="CVV retry",
    pk="cvr_id",
    fail_pk="late_cvr_id",
    ctor="cvr",
    rid="cr",
    rg="cvv_retry|n_then_m|cvv_reenter",
    fail_rg="late_cvr|retry_spent|after_match",
    avoided="r217 CVV match leftover; r218 iCVV leftover. This is CVV retry leftover vs matched CVV",
    fail_avoided="r234 CVV retry leftover vs match. This is late retry after match captured flags only",
    token_col="retry_code",
    result_val="R1",
    spend_check="cvv_retry_ok",
    gate='flag_cvr_lv(charge_id) != "R1"',
    extra_col="  retry_code text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="CVV retry leftover vs match capture",
    fail_surfaces="late CVV retry leftover after match",
    this_is="CVV retry leftover records; match capture PK; spent retry blocks",
    fail_this="late CVV retry leftover flags; match stays",
    seed="CVV retry leftover + match same charge_id",
    fail_seed="match then late CVV retry leftover",
)

# r235 dCVV leftover vs static CVV
leftover(
    ok_slug="dcvv-leftover-vs-static",
    fail_slug="dcvv-after-static",
    stem="dcv_lv",
    fail_stem="dcv_lt",
    event="dCVV leftover",
    fail_event="dCVV leftover",
    pk="dcvv_id",
    fail_pk="late_dcvv_id",
    ctor="dcv",
    rid="dc",
    rg="dynamic_cvv|dcvv|d_cvc3",
    fail_rg="late_dcvv|dcvv_spent|after_static",
    avoided="r217 CVV leftover; r218 iCVV leftover. This is dynamic CVV leftover vs static CVV",
    fail_avoided="r235 dCVV leftover vs static. This is late dCVV after static captured flags only",
    token_col="dcvv",
    result_val="DCV1",
    spend_check="dcvv_fresh",
    gate='flag_dcv_lv(charge_id) != "DCV1"',
    extra_col="  dcvv text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="dCVV leftover vs static CVV capture",
    fail_surfaces="late dCVV leftover after static CVV",
    this_is="dCVV leftover records; static capture PK; stale dCVV blocks",
    fail_this="late dCVV leftover flags; static stays",
    seed="dCVV leftover + static CVV same charge_id",
    fail_seed="static CVV then late dCVV leftover",
)

# r236 MIT recurring-n leftover vs series
leftover(
    ok_slug="mit-recurring-n-leftover-vs-series",
    fail_slug="recurring-n-after-series",
    stem="rcn_lv",
    fail_stem="rcn_lt",
    event="recurring-n MIT",
    fail_event="recurring-n MIT",
    pk="rcn_id",
    fail_pk="late_rcn_id",
    ctor="rcn",
    rid="rn",
    rg="recurring_n|mit_sequence|recurring_n_leftover",
    fail_rg="late_rcn|seq_spent|after_series",
    avoided="r225 MIT series leftover; r219 UCOF leftover. This is recurring-n leftover vs series",
    fail_avoided="r236 recurring-n leftover vs series. This is late recurring-n after series captured flags only",
    token_col="seq_n",
    result_val="N03",
    spend_check="recurring_n_ok",
    gate='flag_rcn_lv(charge_id) != "N03"',
    extra_col="  seq_n text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="MIT recurring-n leftover vs series capture",
    fail_surfaces="late recurring-n leftover after series",
    this_is="recurring-n leftover records; series capture PK; spent sequence blocks",
    fail_this="late recurring-n leftover flags; series stays",
    seed="recurring-n leftover + series same charge_id",
    fail_seed="series then late recurring-n leftover",
)

# r237 CIT subsequent leftover vs first
leftover(
    ok_slug="cit-subsequent-leftover-vs-first",
    fail_slug="subsequent-after-first",
    stem="cis_lv",
    fail_stem="cis_lt",
    event="CIT subsequent",
    fail_event="CIT subsequent",
    pk="cis_id",
    fail_pk="late_cis_id",
    ctor="cis",
    rid="cs",
    rg="cit_subsequent|stored_credential_used|cit_n",
    fail_rg="late_cis|subsequent_spent|after_first",
    avoided="r220 CIT leftover vs COF; r230 usage leftover. This is CIT subsequent leftover vs first CIT",
    fail_avoided="r237 CIT subsequent leftover vs first. This is late subsequent after first captured flags only",
    token_col="cit_n",
    result_val="CITN",
    spend_check="cit_subsequent_ok",
    gate='flag_cis_lv(charge_id) != "CITN"',
    extra_col="  cit_n text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="CIT subsequent leftover vs first-CIT capture",
    fail_surfaces="late CIT subsequent leftover after first",
    this_is="CIT subsequent leftover records; first CIT capture PK; spent subsequent blocks",
    fail_this="late subsequent leftover flags; first stays",
    seed="CIT subsequent leftover + first CIT same charge_id",
    fail_seed="first CIT then late subsequent leftover",
)

# r238 stored-credential initiator leftover
leftover(
    ok_slug="initiator-leftover-vs-mit",
    fail_slug="initiator-after-mit",
    stem="ini_lv",
    fail_stem="ini_lt",
    event="initiator leftover",
    fail_event="initiator leftover",
    pk="ini_id",
    fail_pk="late_ini_id",
    ctor="ini",
    rid="in",
    rg="stored_credential_initiator|merchant|customer",
    fail_rg="late_ini|initiator_spent|after_mit",
    avoided="r230 usage leftover; r219 UCOF leftover. This is stored-credential initiator leftover vs MIT",
    fail_avoided="r238 initiator leftover vs MIT. This is late initiator after MIT captured flags only",
    token_col="initiator",
    result_val="merchant",
    spend_check="initiator_ok",
    gate='flag_ini_lv(charge_id) != "merchant"',
    extra_col="  initiator text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="stored-credential initiator leftover vs MIT capture",
    fail_surfaces="late initiator leftover after MIT",
    this_is="initiator leftover records; MIT capture PK; bad initiator blocks",
    fail_this="late initiator leftover flags; MIT stays",
    seed="initiator leftover + MIT same charge_id",
    fail_seed="MIT then late initiator leftover",
)

# r239 merchant-initiated COF leftover vs CIT
leftover(
    ok_slug="merchant-cof-leftover-vs-cit",
    fail_slug="mcof-after-cit",
    stem="mcf_lv",
    fail_stem="mcf_lt",
    event="merchant COF",
    fail_event="merchant COF",
    pk="mcof_id",
    fail_pk="late_mcof_id",
    ctor="mcf",
    rid="mf",
    rg="merchant_initiated|cof_mit|mcof_leftover",
    fail_rg="late_mcof|mcof_spent|after_cit",
    avoided="r222 COF leftover vs PAN; r220 CIT leftover. This is merchant-initiated COF leftover vs CIT",
    fail_avoided="r239 merchant COF leftover vs CIT. This is late mCOF after CIT captured flags only",
    token_col="mcof",
    result_val="MCOF1",
    spend_check="mcof_allowed",
    gate='flag_mcf_lv(charge_id) != "MCOF1"',
    extra_col="  mcof text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="merchant-initiated COF leftover vs CIT capture",
    fail_surfaces="late merchant COF leftover after CIT",
    this_is="mCOF leftover records; CIT capture PK; spent mCOF blocks",
    fail_this="late mCOF leftover flags; CIT stays",
    seed="merchant COF leftover + CIT same charge_id",
    fail_seed="CIT then late merchant COF leftover",
)

# r240 3DS2 browser fingerprint leftover vs method
leftover(
    ok_slug="browser-fp-leftover-vs-method",
    fail_slug="fp-after-method",
    stem="bfp_lv",
    fail_stem="bfp_lt",
    event="browser fingerprint",
    fail_event="browser fingerprint",
    pk="bfp_id",
    fail_pk="late_bfp_id",
    ctor="bfp",
    rid="bf",
    rg="browser_fingerprint|threeDSCompInd|sdk_app_id",
    fail_rg="late_bfp|fp_spent|after_method",
    avoided="r212 method leftover; r223 frictionless leftover. This is 3DS2 browser fingerprint leftover vs method",
    fail_avoided="r240 browser FP leftover vs method. This is late FP after method captured flags only",
    token_col="comp_ind",
    result_val="Y",
    spend_check="fingerprint_complete",
    gate='flag_bfp_lv(charge_id) != "Y"',
    extra_col="  comp_ind text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="3DS2 browser fingerprint leftover vs method capture",
    fail_surfaces="late browser fingerprint leftover after method",
    this_is="fingerprint leftover records; method capture PK; incomplete FP blocks",
    fail_this="late fingerprint leftover flags; method stays",
    seed="browser FP leftover + method same charge_id",
    fail_seed="method then late FP leftover",
)

# r241 SCA authentication-outage leftover
leftover(
    ok_slug="sca-outage-leftover-vs-capture",
    fail_slug="outage-after-captured",
    stem="out_lv",
    fail_stem="out_lt",
    event="SCA outage",
    fail_event="SCA outage",
    pk="out_id",
    fail_pk="late_out_id",
    ctor="out",
    rid="ou",
    rg="authentication_outage|exemption_outage|acs_unavailable",
    fail_rg="late_out|outage_spent|after_capture",
    avoided="r228 SCA exemption leftover; r213 TRA leftover. This is SCA outage exemption leftover vs capture",
    fail_avoided="r241 SCA outage leftover vs capture. This is late outage after captured flags only",
    token_col="outage",
    result_val="OUT1",
    spend_check="outage_valid",
    gate='flag_out_lv(charge_id) != "OUT1"',
    extra_col="  outage text UNIQUE",
    fail_extra="  charge_id text NOT NULL",
    surfaces="SCA outage leftover vs capture",
    fail_surfaces="late SCA outage leftover after captured",
    this_is="outage leftover records; capture PK; expired outage blocks",
    fail_this="late outage leftover flags; capture stays",
    seed="SCA outage leftover + capture same charge_id",
    fail_seed="capture then late outage leftover",
)

# r242 AVS name leftover vs postal
leftover(
    ok_slug="avs-name-leftover-vs-postal",
    fail_slug="name-after-postal",
    stem="avn_lv",
    fail_stem="avn_lt",
    event="AVS name",
    fail_event="AVS name",
    pk="avn_id",
    fail_pk="late_avn_id",
    ctor="avn",
    rid="an",
    rg="avs_name|name_match|cardholder_name",
    fail_rg="late_avn|name_spent|after_postal",
    avoided="r215 AVS postal leftover; r216 AVS street leftover. This is AVS name leftover vs postal",
    fail_avoided="r242 AVS name leftover vs postal. This is late name after postal captured flags only",
    token_col="name_code",
    result_val="N",
    spend_check="avs_name_ok",
    gate='flag_avn_lv(charge_id) not in ("N", "Y")',
    extra_col="  name_code text",
    fail_extra="  charge_id text NOT NULL",
    surfaces="AVS name leftover vs postal capture",
    fail_surfaces="late AVS name leftover after postal",
    this_is="AVS name leftover records; postal capture PK; name fail blocks",
    fail_this="late AVS name leftover flags; postal stays",
    seed="AVS name leftover + postal same charge_id",
    fail_seed="postal then late AVS name leftover",
)
