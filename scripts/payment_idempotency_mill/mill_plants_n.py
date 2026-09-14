"""Plants r243+: leftover-already-skip scheme leftover presentment/advice.

Not leftover-token cartesian (leftover X and capture both fulfilled ch_1).
Not hotel/nacha cartesian. Not r124 ledger leftover. Not r211–r242 clones.
"""

from mill_plants_j import _ok_pair, _fail_pair

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def already(
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
):
    """Leftover already skip: leftover posts leftover_id; counterpart marks only."""
    fn = f"on_{stem}"
    fail_fn = f"late_{fail_stem}"
    hook_fn = f"mark_{stem}"
    fail_hook = f"already_{fail_stem}"
    test_fn = f"test_{stem}_not_mark_double"
    fail_test_fn = f"test_{fail_stem}_not_add"
    flag = f"leftover_flag_{stem}"
    fail_flag = f"leftover_flag_{fail_stem}"
    claim = f"claim_{stem}"
    claim_mark = f"claim_mark_{stem}"
    claim_late = f"claim_{fail_stem}"
    rows = f"{stem}_rows"
    fail_rows = f"{fail_stem}_rows"
    xfail_fn = f"test_late_{fail_stem}_posts"
    inner = f'post_left(ev["{pk}"], ev.get("cents", 0))'
    fail_inner = f'post_left(ev["{fail_pk}"], ev.get("cents", 0))'
    comment = f"counted every leftover {event}"
    fail_comment = f"counted every late leftover {fail_event}"
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
            first_apply=f"{event} leftover already posted today",
            plan_change=(
                f"{event} leftover already skip claims leftover_id; "
                f"{counterpart} marks only"
            ),
            step_note="Leftover-already 6–7; leftover_id PK 8–11; second leftover 12–13.",
            skip_pred=f"this leftover already posted today",
            verb="post leftover",
            skip_label=f"{event}-leftover-already skip",
            obs3=f"{event} leftover and {counterpart} both post leftover_id",
            obs4=f"{event} leftover posts leftover_id; {counterpart} marks",
            obs5="leftover posts once; counterpart no extra; second leftover adds",
            fail_obs=(
                f"FAILED {test_fn} - {rows} 3 == 1 or leftover posted twice\n"
                "1 failed, 1 passed"
            ),
            obs7=f"{counterpart} still posts leftover; new leftover same day dropped.",
            still_fail_obs=(
                f"FAILED {test_fn} - leftover still double-posts or {counterpart} adds\n"
                "1 failed, 1 passed"
            ),
            rewrite_src=rewrite_src,
            rewrite_src_obs=f"claim {pk}; {leftover_check} leftover-already skip",
            rewrite_hook=rewrite_hook,
            rewrite_hook_obs=f"{counterpart} marks leftover_id; no extra post",
            extra_ddl=extra_col,
            residual=f"{event} leftover last-write vs {counterpart} mark",
            grep_pat=claim_mark,
            grep_obs=f"src/{stem}.py: leftover {event} posts leftover_id; {counterpart} marks",
            goal=(
                f"till-{stem} leftover {event} already skip vs {counterpart}. "
                f"Leftover posts leftover_id; {counterpart} marks only. "
                f"Gate: tests/test_{stem}.py."
            ),
            plan="Skip leftover post if this leftover already posted today.",
            outcome=(
                f"{event} leftover + {counterpart} double-posted leftover_id. "
                "Leftover-already-today skip left counterpart unguarded. "
                "Plan change: leftover_id claim; counterpart marks only. "
                "Tests 2/2 + second leftover + suite 8/8."
            ),
            skip_new=(
                f'    if not {stem}_today(ev["{pk}"]):\n'
                f'        post_left(ev["{pk}"], ev.get("cents", 0))'
            ),
            psql_rows=f"{rid}_1\n{rid}_a\n{rid}_b",
            test_name=f"{stem}-not-mark-double test",
            surface_read=f"{event} leftover plus {counterpart}",
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
            first_apply=f"late {fail_event} leftover already posted today",
            plan_change=f"late {fail_event} leftover already skip flags; {counterpart} stays",
            step_note="Late leftover-already 6–7; PK 8–11; second 12–13; extra xfail 15–17.",
            next_note=(
                f"Unused: late {fail_event} leftover should extra-post leftover_id. "
                f"Avoid late-{fail_event}-leftover-already skip."
            ),
            skip_pred=f"this late leftover already posted today",
            verb="post leftover",
            skip_label=f"late-{fail_event}-leftover-already skip",
            obs3=f"late {fail_event} leftover extra-posts leftover_id",
            obs4=f"late {fail_event} leftover flags; {counterpart} stays",
            obs5="leftover 5000; flagged; second late adds",
            fail_obs=(
                f"FAILED {fail_test_fn} - leftover 10000 == 5000 or rows 3\n"
                "1 failed, 1 passed"
            ),
            obs7="second late ok; hides leftover flag.",
            still_fail_obs=(
                "FAILED if late leftover extra-posted leftover_id (10000)\n"
                "1 failed or 1 passed lucky"
            ),
            rewrite_src=fail_rewrite_src,
            rewrite_src_obs=f"claim {fail_pk} flags leftover",
            rewrite_hook=fail_rewrite_hook,
            rewrite_hook_obs=f"{counterpart} stays",
            extra_ddl=fail_extra,
            xfail_label=f"late {fail_event} leftover should extra-post leftover_id",
            xfail_body=xfail_body,
            xfail_fail_obs=(
                f"FAILED {xfail_fn} - flagged; leftover stayed 5000\n1 failed"
            ),
            xfail_fn=xfail_fn,
            xfail_reason=(
                f"late {fail_event} leftover extra-post vs flag-only is a policy fork"
            ),
            goal=(
                f"till-{fail_stem} late leftover {fail_event} extra-posted leftover_id. "
                f"Late leftover already skip flags. Gate: tests/test_{fail_stem}.py."
            ),
            plan="Skip leftover post if this late leftover already posted today.",
            outcome=(
                f"Late {fail_event} leftover extra-posted leftover_id. "
                "Late leftover-already skip hid flag. "
                "Plan change: late leftover_id flag. Primary+second pass. "
                "Partial: extra xfail handoff."
            ),
            skip_new=(
                f'    if not {fail_stem}_today(ev["{fail_pk}"]):\n'
                f'        post_left(ev["{fail_pk}"], ev.get("cents", 0))'
            ),
            test_name=f"{fail_stem}-not-add test",
            surface_read=f"late {fail_event} leftover plus already-settled leftover",
            test_body_short=(
                f"same — late {fail_event} leftover already skip flags; {counterpart} stays"
            ),
        ),
    )


# r243 leftover BASE II TC05 vs leftover TC06 credit
already(
    ok_slug="tc05-leftover-already-vs-tc06",
    fail_slug="tc05-after-tc06-cleared",
    stem="tc5_sk",
    fail_stem="tc5_lt",
    event="TC05 leftover",
    fail_event="TC05 leftover",
    pk="tc05_id",
    fail_pk="late_tc05_id",
    ctor="tc5",
    rid="b2",
    rg="tc05|sales_draft|base_ii_leftover",
    fail_rg="late_tc05|tc06_cleared|leftover_already",
    avoided="r211 leftover-token cartesian; r124 journal leftover. This is BASE II leftover already skip vs TC06",
    fail_avoided="r243 TC05 leftover already skip. This is late TC05 after TC06 leftover cleared flags only",
    token_col="tc05_code",
    result_val="TC05",
    leftover_check="tc05_leftover_open",
    extra_col="  tc05_code text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="TC05 leftover already skip vs TC06 credit leftover",
    fail_surfaces="late TC05 leftover after TC06 leftover cleared",
    this_is="leftover already skip; leftover posts leftover_id; TC06 marks only",
    fail_this="late leftover already skip flags; TC06 stays",
    seed="TC05 leftover already + TC06 mark same leftover_id",
    fail_seed="TC06 leftover cleared then late TC05 leftover",
    counterpart="TC06 credit leftover",
)

# r244 leftover Mastercard IPM first presentment vs leftover reversal
already(
    ok_slug="ipm-leftover-already-vs-reversal",
    fail_slug="ipm-after-reversal-cleared",
    stem="ipm_sk",
    fail_stem="ipm_lt",
    event="IPM leftover",
    fail_event="IPM leftover",
    pk="ipm_id",
    fail_pk="late_ipm_id",
    ctor="ipm",
    rid="ip",
    rg="ipm_first_presentment|mastercard_ipm|leftover_already",
    fail_rg="late_ipm|ipm_reversal_cleared|leftover_already",
    avoided="r243 TC05 leftover already skip; r139 representment. This is IPM leftover already skip vs reversal",
    fail_avoided="r244 IPM leftover already skip. This is late IPM after reversal leftover cleared flags only",
    token_col="ipm_de24",
    result_val="200",
    leftover_check="ipm_leftover_open",
    extra_col="  ipm_de24 text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="IPM leftover already skip vs IPM reversal leftover",
    fail_surfaces="late IPM leftover after reversal leftover cleared",
    this_is="leftover already skip; leftover posts leftover_id; reversal marks only",
    fail_this="late leftover already skip flags; reversal stays",
    seed="IPM leftover already + reversal mark same leftover_id",
    fail_seed="reversal leftover cleared then late IPM leftover",
    counterpart="IPM reversal leftover",
)

# r245 leftover ARN bind vs leftover clearing
already(
    ok_slug="arn-leftover-already-vs-clearing",
    fail_slug="arn-after-clearing-posted",
    stem="arn_sk",
    fail_stem="arn_lt",
    event="ARN leftover",
    fail_event="ARN leftover",
    pk="arn_id",
    fail_pk="late_arn_id",
    ctor="arn",
    rid="ar",
    rg="acquirer_ref|arn_leftover|clearing_file",
    fail_rg="late_arn|clearing_posted|leftover_already",
    avoided="r244 IPM leftover already skip; r124 settle window. This is ARN leftover already skip vs clearing",
    fail_avoided="r245 ARN leftover already skip. This is late ARN after clearing leftover posted flags only",
    token_col="arn",
    result_val="ARN01",
    leftover_check="arn_leftover_open",
    extra_col="  arn text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="ARN leftover already skip vs leftover clearing",
    fail_surfaces="late ARN leftover after leftover clearing posted",
    this_is="leftover already skip; leftover posts leftover_id; clearing marks only",
    fail_this="late leftover already skip flags; clearing stays",
    seed="ARN leftover already + clearing mark same leftover_id",
    fail_seed="clearing leftover posted then late ARN leftover",
    counterpart="leftover clearing",
)

# r246 leftover STAN vs leftover RRN
already(
    ok_slug="stan-leftover-already-vs-rrn",
    fail_slug="stan-after-rrn-bound",
    stem="stn_sk",
    fail_stem="stn_lt",
    event="STAN leftover",
    fail_event="STAN leftover",
    pk="stan_id",
    fail_pk="late_stan_id",
    ctor="stn",
    rid="st",
    rg="stan|systems_trace|leftover_already",
    fail_rg="late_stan|rrn_bound|leftover_already",
    avoided="r245 ARN leftover already skip; r211 leftover-token. This is STAN leftover already skip vs RRN",
    fail_avoided="r246 STAN leftover already skip. This is late STAN after RRN leftover bound flags only",
    token_col="stan",
    result_val="STN01",
    leftover_check="stan_leftover_open",
    extra_col="  stan text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="STAN leftover already skip vs leftover RRN",
    fail_surfaces="late STAN leftover after leftover RRN bound",
    this_is="leftover already skip; leftover posts leftover_id; RRN marks only",
    fail_this="late leftover already skip flags; RRN stays",
    seed="STAN leftover already + RRN mark same leftover_id",
    fail_seed="RRN leftover bound then late STAN leftover",
    counterpart="leftover RRN",
)

# r247 leftover ISO 0220 advice vs leftover 0200
already(
    ok_slug="iso0220-leftover-already-vs-0200",
    fail_slug="iso0220-after-0200-posted",
    stem="i22_sk",
    fail_stem="i22_lt",
    event="ISO 0220 leftover",
    fail_event="ISO 0220 leftover",
    pk="iso0220_id",
    fail_pk="late_iso0220_id",
    ctor="i22",
    rid="i2",
    rg="iso_0220|advice_leftover|mti_0220",
    fail_rg="late_0220|mti_0200_posted|leftover_already",
    avoided="r246 STAN leftover already skip; r59 PSP grid. This is ISO 0220 leftover already skip vs 0200",
    fail_avoided="r247 ISO 0220 leftover already skip. This is late 0220 after 0200 leftover posted flags only",
    token_col="mti",
    result_val="0220",
    leftover_check="iso0220_leftover_open",
    extra_col="  mti text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="ISO 0220 leftover already skip vs leftover 0200",
    fail_surfaces="late ISO 0220 leftover after leftover 0200 posted",
    this_is="leftover already skip; leftover posts leftover_id; 0200 marks only",
    fail_this="late leftover already skip flags; 0200 stays",
    seed="ISO 0220 leftover already + 0200 mark same leftover_id",
    fail_seed="0200 leftover posted then late 0220 leftover",
    counterpart="leftover 0200 financial",
)

# r248 leftover RDR alert vs leftover chargeback
already(
    ok_slug="rdr-leftover-already-vs-chargeback",
    fail_slug="rdr-after-chargeback-posted",
    stem="rdr_sk",
    fail_stem="rdr_lt",
    event="RDR leftover",
    fail_event="RDR leftover",
    pk="rdr_id",
    fail_pk="late_rdr_id",
    ctor="rdr",
    rid="rd",
    rg="rapid_dispute|rdr_leftover|visa_rdr",
    fail_rg="late_rdr|chargeback_posted|leftover_already",
    avoided="r126 chargeback vs refund; r167 ethoca hotel. This is RDR leftover already skip vs chargeback",
    fail_avoided="r248 RDR leftover already skip. This is late RDR after chargeback leftover posted flags only",
    token_col="rdr_case",
    result_val="RDR1",
    leftover_check="rdr_leftover_open",
    extra_col="  rdr_case text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="RDR leftover already skip vs leftover chargeback",
    fail_surfaces="late RDR leftover after leftover chargeback posted",
    this_is="leftover already skip; leftover posts leftover_id; chargeback marks only",
    fail_this="late leftover already skip flags; chargeback stays",
    seed="RDR leftover already + chargeback mark same leftover_id",
    fail_seed="chargeback leftover posted then late RDR leftover",
    counterpart="leftover chargeback",
)

# r249 leftover CDRN vs leftover representment
already(
    ok_slug="cdrn-leftover-already-vs-representment",
    fail_slug="cdrn-after-representment",
    stem="cdr_sk",
    fail_stem="cdr_lt",
    event="CDRN leftover",
    fail_event="CDRN leftover",
    pk="cdrn_id",
    fail_pk="late_cdrn_id",
    ctor="cdr",
    rid="cd",
    rg="cdrn|verifi_alert|leftover_already",
    fail_rg="late_cdrn|representment_posted|leftover_already",
    avoided="r248 RDR leftover already skip; r139 representment vs win. This is CDRN leftover already skip vs representment",
    fail_avoided="r249 CDRN leftover already skip. This is late CDRN after representment leftover posted flags only",
    token_col="cdrn_case",
    result_val="CDRN1",
    leftover_check="cdrn_leftover_open",
    extra_col="  cdrn_case text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="CDRN leftover already skip vs leftover representment",
    fail_surfaces="late CDRN leftover after leftover representment posted",
    this_is="leftover already skip; leftover posts leftover_id; representment marks only",
    fail_this="late leftover already skip flags; representment stays",
    seed="CDRN leftover already + representment mark same leftover_id",
    fail_seed="representment leftover posted then late CDRN leftover",
    counterpart="leftover representment",
)

# r250 leftover Order Insight vs leftover retrieval
already(
    ok_slug="order-insight-leftover-already-vs-retrieval",
    fail_slug="insight-after-retrieval",
    stem="oin_sk",
    fail_stem="oin_lt",
    event="Order Insight leftover",
    fail_event="Order Insight leftover",
    pk="insight_id",
    fail_pk="late_insight_id",
    ctor="oin",
    rid="oi",
    rg="order_insight|visa_oi|leftover_already",
    fail_rg="late_insight|retrieval_posted|leftover_already",
    avoided="r144 retrieval vs chargeback; r248 RDR leftover. This is Order Insight leftover already skip vs retrieval",
    fail_avoided="r250 Order Insight leftover already skip. This is late insight after retrieval leftover posted flags only",
    token_col="oi_case",
    result_val="OI01",
    leftover_check="insight_leftover_open",
    extra_col="  oi_case text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Order Insight leftover already skip vs leftover retrieval",
    fail_surfaces="late Order Insight leftover after leftover retrieval posted",
    this_is="leftover already skip; leftover posts leftover_id; retrieval marks only",
    fail_this="late leftover already skip flags; retrieval stays",
    seed="Order Insight leftover already + retrieval mark same leftover_id",
    fail_seed="retrieval leftover posted then late insight leftover",
    counterpart="leftover retrieval",
)

# r251 leftover PAR bind vs leftover PAN (not r155 network-token vs PAN auth)
already(
    ok_slug="par-leftover-already-vs-pan",
    fail_slug="par-after-pan-bound",
    stem="par_sk",
    fail_stem="par_lt",
    event="PAR leftover",
    fail_event="PAR leftover",
    pk="par_id",
    fail_pk="late_par_id",
    ctor="par",
    rid="pa",
    rg="payment_account_reference|par_leftover|leftover_already",
    fail_rg="late_par|pan_bound|leftover_already",
    avoided="r155 network token vs PAN auth; r211 leftover-token. This is PAR leftover already skip vs leftover PAN",
    fail_avoided="r251 PAR leftover already skip. This is late PAR after leftover PAN bound flags only",
    token_col="par",
    result_val="PAR01",
    leftover_check="par_leftover_open",
    extra_col="  par text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="PAR leftover already skip vs leftover PAN",
    fail_surfaces="late PAR leftover after leftover PAN bound",
    this_is="leftover already skip; leftover posts leftover_id; PAN marks only",
    fail_this="late leftover already skip flags; PAN stays",
    seed="PAR leftover already + PAN mark same leftover_id",
    fail_seed="PAN leftover bound then late PAR leftover",
    counterpart="leftover PAN",
)

# r252 leftover DTVV vs leftover token requestor
already(
    ok_slug="dtvv-leftover-already-vs-requestor",
    fail_slug="dtvv-after-requestor-bound",
    stem="dtv_sk",
    fail_stem="dtv_lt",
    event="DTVV leftover",
    fail_event="DTVV leftover",
    pk="dtvv_id",
    fail_pk="late_dtvv_id",
    ctor="dtv",
    rid="dv",
    rg="dtvv|dynamic_token_verification|leftover_already",
    fail_rg="late_dtvv|token_requestor_bound|leftover_already",
    avoided="r251 PAR leftover already skip; r174 apple DPAS. This is DTVV leftover already skip vs token requestor",
    fail_avoided="r252 DTVV leftover already skip. This is late DTVV after token requestor leftover bound flags only",
    token_col="dtvv",
    result_val="DTVV1",
    leftover_check="dtvv_leftover_open",
    extra_col="  dtvv text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="DTVV leftover already skip vs leftover token requestor",
    fail_surfaces="late DTVV leftover after leftover token requestor bound",
    this_is="leftover already skip; leftover posts leftover_id; requestor marks only",
    fail_this="late leftover already skip flags; requestor stays",
    seed="DTVV leftover already + requestor mark same leftover_id",
    fail_seed="token requestor leftover bound then late DTVV leftover",
    counterpart="leftover token requestor",
)

# r253 leftover EMV ARQC vs leftover ARPC
already(
    ok_slug="arqc-leftover-already-vs-arpc",
    fail_slug="arqc-after-arpc-bound",
    stem="arq_sk",
    fail_stem="arq_lt",
    event="ARQC leftover",
    fail_event="ARQC leftover",
    pk="arqc_id",
    fail_pk="late_arqc_id",
    ctor="arq",
    rid="aq",
    rg="arqc|application_cryptogram|leftover_already",
    fail_rg="late_arqc|arpc_bound|leftover_already",
    avoided="r252 DTVV leftover already skip; r218 iCVV leftover-token. This is ARQC leftover already skip vs ARPC",
    fail_avoided="r253 ARQC leftover already skip. This is late ARQC after ARPC leftover bound flags only",
    token_col="arqc",
    result_val="ARQC1",
    leftover_check="arqc_leftover_open",
    extra_col="  arqc text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="ARQC leftover already skip vs leftover ARPC",
    fail_surfaces="late ARQC leftover after leftover ARPC bound",
    this_is="leftover already skip; leftover posts leftover_id; ARPC marks only",
    fail_this="late leftover already skip flags; ARPC stays",
    seed="ARQC leftover already + ARPC mark same leftover_id",
    fail_seed="ARPC leftover bound then late ARQC leftover",
    counterpart="leftover ARPC",
)

# r254 leftover ATC increment vs leftover cryptogram replay
already(
    ok_slug="atc-leftover-already-vs-replay",
    fail_slug="atc-after-replay-blocked",
    stem="atc_sk",
    fail_stem="atc_lt",
    event="ATC leftover",
    fail_event="ATC leftover",
    pk="atc_id",
    fail_pk="late_atc_id",
    ctor="atc",
    rid="at",
    rg="application_transaction_counter|atc_leftover|leftover_already",
    fail_rg="late_atc|cryptogram_replay|leftover_already",
    avoided="r253 ARQC leftover already skip; r155 cryptogram replay. This is ATC leftover already skip vs replay",
    fail_avoided="r254 ATC leftover already skip. This is late ATC after leftover replay blocked flags only",
    token_col="atc",
    result_val="ATC09",
    leftover_check="atc_leftover_open",
    extra_col="  atc text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="ATC leftover already skip vs leftover cryptogram replay",
    fail_surfaces="late ATC leftover after leftover replay blocked",
    this_is="leftover already skip; leftover posts leftover_id; replay marks only",
    fail_this="late leftover already skip flags; replay stays",
    seed="ATC leftover already + replay mark same leftover_id",
    fail_seed="replay leftover blocked then late ATC leftover",
    counterpart="leftover cryptogram replay",
)

# r255 leftover SEPA SDD leftover vs leftover mandate
already(
    ok_slug="sepa-sdd-leftover-already-vs-mandate",
    fail_slug="sdd-after-mandate-bound",
    stem="sdd_sk",
    fail_stem="sdd_lt",
    event="SEPA SDD leftover",
    fail_event="SEPA SDD leftover",
    pk="sdd_id",
    fail_pk="late_sdd_id",
    ctor="sdd",
    rid="sd",
    rg="sepa_sdd|direct_debit_leftover|leftover_already",
    fail_rg="late_sdd|mandate_bound|leftover_already",
    avoided="r167 nacha hotel cartesian; r135 ACH settle. This is SEPA SDD leftover already skip vs mandate",
    fail_avoided="r255 SEPA SDD leftover already skip. This is late SDD after leftover mandate bound flags only",
    token_col="mandate_id",
    result_val="SDD01",
    leftover_check="sdd_leftover_open",
    extra_col="  mandate_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="SEPA SDD leftover already skip vs leftover mandate",
    fail_surfaces="late SEPA SDD leftover after leftover mandate bound",
    this_is="leftover already skip; leftover posts leftover_id; mandate marks only",
    fail_this="late leftover already skip flags; mandate stays",
    seed="SEPA SDD leftover already + mandate mark same leftover_id",
    fail_seed="mandate leftover bound then late SDD leftover",
    counterpart="leftover mandate",
)

# r256 leftover PIX leftover vs leftover E2E
already(
    ok_slug="pix-leftover-already-vs-e2e",
    fail_slug="pix-after-e2e-bound",
    stem="pix_sk",
    fail_stem="pix_lt",
    event="PIX leftover",
    fail_event="PIX leftover",
    pk="pix_id",
    fail_pk="late_pix_id",
    ctor="pix",
    rid="px",
    rg="pix_end_to_end|pix_leftover|leftover_already",
    fail_rg="late_pix|e2e_bound|leftover_already",
    avoided="r255 SEPA leftover already skip; r108 fednow. This is PIX leftover already skip vs E2E",
    fail_avoided="r256 PIX leftover already skip. This is late PIX after leftover E2E bound flags only",
    token_col="e2e",
    result_val="E2E01",
    leftover_check="pix_leftover_open",
    extra_col="  e2e text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="PIX leftover already skip vs leftover E2E",
    fail_surfaces="late PIX leftover after leftover E2E bound",
    this_is="leftover already skip; leftover posts leftover_id; E2E marks only",
    fail_this="late leftover already skip flags; E2E stays",
    seed="PIX leftover already + E2E mark same leftover_id",
    fail_seed="E2E leftover bound then late PIX leftover",
    counterpart="leftover E2E",
)

# r257 leftover UPI leftover vs leftover RRN
already(
    ok_slug="upi-leftover-already-vs-rrn",
    fail_slug="upi-after-rrn-bound",
    stem="upi_sk",
    fail_stem="upi_lt",
    event="UPI leftover",
    fail_event="UPI leftover",
    pk="upi_id",
    fail_pk="late_upi_id",
    ctor="upi",
    rid="up",
    rg="upi_rrn|npci_leftover|leftover_already",
    fail_rg="late_upi|upi_rrn_bound|leftover_already",
    avoided="r246 STAN leftover already skip; r256 PIX leftover. This is UPI leftover already skip vs leftover RRN",
    fail_avoided="r257 UPI leftover already skip. This is late UPI after leftover RRN bound flags only",
    token_col="upi_rrn",
    result_val="URRN1",
    leftover_check="upi_leftover_open",
    extra_col="  upi_rrn text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="UPI leftover already skip vs leftover RRN",
    fail_surfaces="late UPI leftover after leftover RRN bound",
    this_is="leftover already skip; leftover posts leftover_id; UPI RRN marks only",
    fail_this="late leftover already skip flags; UPI RRN stays",
    seed="UPI leftover already + RRN mark same leftover_id",
    fail_seed="UPI RRN leftover bound then late UPI leftover",
    counterpart="leftover UPI RRN",
)

# r258 leftover ISO 20022 pacs.008 leftover vs leftover camt.054
already(
    ok_slug="pacs008-leftover-already-vs-camt054",
    fail_slug="pacs008-after-camt054",
    stem="p08_sk",
    fail_stem="p08_lt",
    event="pacs.008 leftover",
    fail_event="pacs.008 leftover",
    pk="pacs008_id",
    fail_pk="late_pacs008_id",
    ctor="p08",
    rid="p8",
    rg="pacs_008|iso20022_leftover|leftover_already",
    fail_rg="late_pacs008|camt_054_posted|leftover_already",
    avoided="r247 ISO 0220 leftover already skip; r255 SEPA leftover. This is pacs.008 leftover already skip vs camt.054",
    fail_avoided="r258 pacs.008 leftover already skip. This is late pacs.008 after leftover camt.054 posted flags only",
    token_col="msg_id",
    result_val="P008",
    leftover_check="pacs008_leftover_open",
    extra_col="  msg_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="pacs.008 leftover already skip vs leftover camt.054",
    fail_surfaces="late pacs.008 leftover after leftover camt.054 posted",
    this_is="leftover already skip; leftover posts leftover_id; camt.054 marks only",
    fail_this="late leftover already skip flags; camt.054 stays",
    seed="pacs.008 leftover already + camt.054 mark same leftover_id",
    fail_seed="camt.054 leftover posted then late pacs.008 leftover",
    counterpart="leftover camt.054",
)

# r259 leftover SWIFT MT103 leftover vs leftover MT202
already(
    ok_slug="mt103-leftover-already-vs-mt202",
    fail_slug="mt103-after-mt202",
    stem="m13_sk",
    fail_stem="m13_lt",
    event="MT103 leftover",
    fail_event="MT103 leftover",
    pk="mt103_id",
    fail_pk="late_mt103_id",
    ctor="m13",
    rid="m1",
    rg="mt103|swift_leftover|leftover_already",
    fail_rg="late_mt103|mt202_posted|leftover_already",
    avoided="r258 pacs.008 leftover already skip; r124 journal leftover. This is MT103 leftover already skip vs MT202",
    fail_avoided="r259 MT103 leftover already skip. This is late MT103 after leftover MT202 posted flags only",
    token_col="uetr",
    result_val="UETR1",
    leftover_check="mt103_leftover_open",
    extra_col="  uetr text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="MT103 leftover already skip vs leftover MT202",
    fail_surfaces="late MT103 leftover after leftover MT202 posted",
    this_is="leftover already skip; leftover posts leftover_id; MT202 marks only",
    fail_this="late leftover already skip flags; MT202 stays",
    seed="MT103 leftover already + MT202 mark same leftover_id",
    fail_seed="MT202 leftover posted then late MT103 leftover",
    counterpart="leftover MT202",
)

# r260 leftover iDEAL leftover vs leftover SEPA credit
already(
    ok_slug="ideal-leftover-already-vs-sct",
    fail_slug="ideal-after-sct",
    stem="idl_sk",
    fail_stem="idl_lt",
    event="iDEAL leftover",
    fail_event="iDEAL leftover",
    pk="ideal_id",
    fail_pk="late_ideal_id",
    ctor="idl",
    rid="id",
    rg="ideal_trx|ideal_leftover|leftover_already",
    fail_rg="late_ideal|sct_posted|leftover_already",
    avoided="r255 SEPA leftover already skip; r256 PIX leftover. This is iDEAL leftover already skip vs SCT",
    fail_avoided="r260 iDEAL leftover already skip. This is late iDEAL after leftover SCT posted flags only",
    token_col="ideal_trx",
    result_val="IDL01",
    leftover_check="ideal_leftover_open",
    extra_col="  ideal_trx text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="iDEAL leftover already skip vs leftover SCT",
    fail_surfaces="late iDEAL leftover after leftover SCT posted",
    this_is="leftover already skip; leftover posts leftover_id; SCT marks only",
    fail_this="late leftover already skip flags; SCT stays",
    seed="iDEAL leftover already + SCT mark same leftover_id",
    fail_seed="SCT leftover posted then late iDEAL leftover",
    counterpart="leftover SCT",
)

# r261 leftover Boleto leftover vs leftover PIX
already(
    ok_slug="boleto-leftover-already-vs-pix",
    fail_slug="boleto-after-pix",
    stem="bol_sk",
    fail_stem="bol_lt",
    event="Boleto leftover",
    fail_event="Boleto leftover",
    pk="boleto_id",
    fail_pk="late_boleto_id",
    ctor="bol",
    rid="bo",
    rg="boleto_barcode|boleto_leftover|leftover_already",
    fail_rg="late_boleto|pix_posted|leftover_already",
    avoided="r256 PIX leftover already skip; r260 iDEAL leftover. This is Boleto leftover already skip vs PIX",
    fail_avoided="r261 Boleto leftover already skip. This is late Boleto after leftover PIX posted flags only",
    token_col="barcode",
    result_val="BOL01",
    leftover_check="boleto_leftover_open",
    extra_col="  barcode text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Boleto leftover already skip vs leftover PIX",
    fail_surfaces="late Boleto leftover after leftover PIX posted",
    this_is="leftover already skip; leftover posts leftover_id; PIX marks only",
    fail_this="late leftover already skip flags; PIX stays",
    seed="Boleto leftover already + PIX mark same leftover_id",
    fail_seed="PIX leftover posted then late Boleto leftover",
    counterpart="leftover PIX",
)

# r262 leftover Faster Payments leftover vs leftover CHAPS
already(
    ok_slug="fps-leftover-already-vs-chaps",
    fail_slug="fps-after-chaps",
    stem="fps_sk",
    fail_stem="fps_lt",
    event="FPS leftover",
    fail_event="FPS leftover",
    pk="fps_id",
    fail_pk="late_fps_id",
    ctor="fps",
    rid="fp",
    rg="faster_payments|fps_leftover|leftover_already",
    fail_rg="late_fps|chaps_posted|leftover_already",
    avoided="r259 MT103 leftover already skip; r108 fednow. This is FPS leftover already skip vs CHAPS",
    fail_avoided="r262 FPS leftover already skip. This is late FPS after leftover CHAPS posted flags only",
    token_col="fps_ref",
    result_val="FPS01",
    leftover_check="fps_leftover_open",
    extra_col="  fps_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="FPS leftover already skip vs leftover CHAPS",
    fail_surfaces="late FPS leftover after leftover CHAPS posted",
    this_is="leftover already skip; leftover posts leftover_id; CHAPS marks only",
    fail_this="late leftover already skip flags; CHAPS stays",
    seed="FPS leftover already + CHAPS mark same leftover_id",
    fail_seed="CHAPS leftover posted then late FPS leftover",
    counterpart="leftover CHAPS",
)

# r263 leftover TAVV leftover already skip vs leftover DPAN
already(
    ok_slug="tavv-leftover-already-vs-dpan",
    fail_slug="tavv-after-dpan-bound",
    stem="tav_sk",
    fail_stem="tav_lt",
    event="TAVV leftover",
    fail_event="TAVV leftover",
    pk="tavv_id",
    fail_pk="late_tavv_id",
    ctor="tav",
    rid="tv",
    rg="tavv|token_authentication_verification|leftover_already",
    fail_rg="late_tavv|dpan_bound|leftover_already",
    avoided="r174 apple DPAS vs token; r252 DTVV leftover. This is TAVV leftover already skip vs leftover DPAN",
    fail_avoided="r263 TAVV leftover already skip. This is late TAVV after leftover DPAN bound flags only",
    token_col="tavv",
    result_val="TAVV1",
    leftover_check="tavv_leftover_open",
    extra_col="  tavv text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="TAVV leftover already skip vs leftover DPAN",
    fail_surfaces="late TAVV leftover after leftover DPAN bound",
    this_is="leftover already skip; leftover posts leftover_id; DPAN marks only",
    fail_this="late leftover already skip flags; DPAN stays",
    seed="TAVV leftover already + DPAN mark same leftover_id",
    fail_seed="DPAN leftover bound then late TAVV leftover",
    counterpart="leftover DPAN",
)

# r264 leftover Google Pay leftover already skip vs leftover token
already(
    ok_slug="gpay-leftover-already-vs-token",
    fail_slug="gpay-after-token-bound",
    stem="gpy_sk",
    fail_stem="gpy_lt",
    event="Google Pay leftover",
    fail_event="Google Pay leftover",
    pk="gpay_id",
    fail_pk="late_gpay_id",
    ctor="gpy",
    rid="gp",
    rg="google_pay|gpay_cryptogram|leftover_already",
    fail_rg="late_gpay|token_bound|leftover_already",
    avoided="r263 TAVV leftover already skip; r174 apple DPAS. This is Google Pay leftover already skip vs leftover token",
    fail_avoided="r264 Google Pay leftover already skip. This is late GPay after leftover token bound flags only",
    token_col="gpay_crypto",
    result_val="GPY01",
    leftover_check="gpay_leftover_open",
    extra_col="  gpay_crypto text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Google Pay leftover already skip vs leftover token",
    fail_surfaces="late Google Pay leftover after leftover token bound",
    this_is="leftover already skip; leftover posts leftover_id; token marks only",
    fail_this="late leftover already skip flags; token stays",
    seed="Google Pay leftover already + token mark same leftover_id",
    fail_seed="token leftover bound then late Google Pay leftover",
    counterpart="leftover token",
)

# r265 leftover Visa VAU leftover already skip vs leftover PAN
already(
    ok_slug="vau-leftover-already-vs-pan",
    fail_slug="vau-after-pan-refreshed",
    stem="vau_sk",
    fail_stem="vau_lt",
    event="VAU leftover",
    fail_event="VAU leftover",
    pk="vau_id",
    fail_pk="late_vau_id",
    ctor="vau",
    rid="vu",
    rg="visa_account_updater|vau_leftover|leftover_already",
    fail_rg="late_vau|pan_refreshed|leftover_already",
    avoided="r150 account updater vs PAN; r251 PAR leftover. This is VAU leftover already skip vs leftover PAN",
    fail_avoided="r265 VAU leftover already skip. This is late VAU after leftover PAN refreshed flags only",
    token_col="vau_pan",
    result_val="VAU01",
    leftover_check="vau_leftover_open",
    extra_col="  vau_pan text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="VAU leftover already skip vs leftover PAN",
    fail_surfaces="late VAU leftover after leftover PAN refreshed",
    this_is="leftover already skip; leftover posts leftover_id; PAN marks only",
    fail_this="late leftover already skip flags; PAN stays",
    seed="VAU leftover already + PAN mark same leftover_id",
    fail_seed="PAN leftover refreshed then late VAU leftover",
    counterpart="leftover PAN refresh",
)

# r266 leftover Mastercard ABU leftover already skip vs leftover PAN
already(
    ok_slug="abu-leftover-already-vs-pan",
    fail_slug="abu-after-pan-refreshed",
    stem="abu_sk",
    fail_stem="abu_lt",
    event="ABU leftover",
    fail_event="ABU leftover",
    pk="abu_id",
    fail_pk="late_abu_id",
    ctor="abu",
    rid="ab",
    rg="automatic_billing_updater|abu_leftover|leftover_already",
    fail_rg="late_abu|pan_refreshed|leftover_already",
    avoided="r265 VAU leftover already skip; r150 account updater. This is ABU leftover already skip vs leftover PAN",
    fail_avoided="r266 ABU leftover already skip. This is late ABU after leftover PAN refreshed flags only",
    token_col="abu_pan",
    result_val="ABU01",
    leftover_check="abu_leftover_open",
    extra_col="  abu_pan text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="ABU leftover already skip vs leftover PAN",
    fail_surfaces="late ABU leftover after leftover PAN refreshed",
    this_is="leftover already skip; leftover posts leftover_id; PAN marks only",
    fail_this="late leftover already skip flags; PAN stays",
    seed="ABU leftover already + PAN mark same leftover_id",
    fail_seed="PAN leftover refreshed then late ABU leftover",
    counterpart="leftover PAN refresh",
)

# r267 leftover TARGET2 leftover already skip vs leftover T2S
already(
    ok_slug="target2-leftover-already-vs-t2s",
    fail_slug="target2-after-t2s",
    stem="tg2_sk",
    fail_stem="tg2_lt",
    event="TARGET2 leftover",
    fail_event="TARGET2 leftover",
    pk="t2_id",
    fail_pk="late_t2_id",
    ctor="tg2",
    rid="t2",
    rg="target2|clm_leftover|leftover_already",
    fail_rg="late_t2|t2s_posted|leftover_already",
    avoided="r258 pacs.008 leftover already skip; r259 MT103 leftover. This is TARGET2 leftover already skip vs T2S",
    fail_avoided="r267 TARGET2 leftover already skip. This is late TARGET2 after leftover T2S posted flags only",
    token_col="clm_id",
    result_val="T201",
    leftover_check="t2_leftover_open",
    extra_col="  clm_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="TARGET2 leftover already skip vs leftover T2S",
    fail_surfaces="late TARGET2 leftover after leftover T2S posted",
    this_is="leftover already skip; leftover posts leftover_id; T2S marks only",
    fail_this="late leftover already skip flags; T2S stays",
    seed="TARGET2 leftover already + T2S mark same leftover_id",
    fail_seed="T2S leftover posted then late TARGET2 leftover",
    counterpart="leftover T2S",
)

# r268 leftover SPEI leftover already skip vs leftover CoDi
already(
    ok_slug="spei-leftover-already-vs-codi",
    fail_slug="spei-after-codi",
    stem="spe_sk",
    fail_stem="spe_lt",
    event="SPEI leftover",
    fail_event="SPEI leftover",
    pk="spei_id",
    fail_pk="late_spei_id",
    ctor="spe",
    rid="sp",
    rg="spei_clave|spei_leftover|leftover_already",
    fail_rg="late_spei|codi_posted|leftover_already",
    avoided="r256 PIX leftover already skip; r261 Boleto leftover. This is SPEI leftover already skip vs CoDi",
    fail_avoided="r268 SPEI leftover already skip. This is late SPEI after leftover CoDi posted flags only",
    token_col="clave",
    result_val="SPEI1",
    leftover_check="spei_leftover_open",
    extra_col="  clave text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="SPEI leftover already skip vs leftover CoDi",
    fail_surfaces="late SPEI leftover after leftover CoDi posted",
    this_is="leftover already skip; leftover posts leftover_id; CoDi marks only",
    fail_this="late leftover already skip flags; CoDi stays",
    seed="SPEI leftover already + CoDi mark same leftover_id",
    fail_seed="CoDi leftover posted then late SPEI leftover",
    counterpart="leftover CoDi",
)

# r269 leftover Interac leftover already skip vs leftover EFT
already(
    ok_slug="interac-leftover-already-vs-eft",
    fail_slug="interac-after-eft",
    stem="itc_sk",
    fail_stem="itc_lt",
    event="Interac leftover",
    fail_event="Interac leftover",
    pk="interac_id",
    fail_pk="late_interac_id",
    ctor="itc",
    rid="ic",
    rg="interac_ref|interac_leftover|leftover_already",
    fail_rg="late_interac|eft_posted|leftover_already",
    avoided="r262 FPS leftover already skip; r135 ACH settle. This is Interac leftover already skip vs EFT",
    fail_avoided="r269 Interac leftover already skip. This is late Interac after leftover EFT posted flags only",
    token_col="interac_ref",
    result_val="ITC01",
    leftover_check="interac_leftover_open",
    extra_col="  interac_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Interac leftover already skip vs leftover EFT",
    fail_surfaces="late Interac leftover after leftover EFT posted",
    this_is="leftover already skip; leftover posts leftover_id; EFT marks only",
    fail_this="late leftover already skip flags; EFT stays",
    seed="Interac leftover already + EFT mark same leftover_id",
    fail_seed="EFT leftover posted then late Interac leftover",
    counterpart="leftover EFT",
)

# r270 leftover Bancontact leftover already skip vs leftover SCT
already(
    ok_slug="bancontact-leftover-already-vs-sct",
    fail_slug="bancontact-after-sct",
    stem="bnc_sk",
    fail_stem="bnc_lt",
    event="Bancontact leftover",
    fail_event="Bancontact leftover",
    pk="bnc_id",
    fail_pk="late_bnc_id",
    ctor="bnc",
    rid="bn",
    rg="bancontact|bcmc_leftover|leftover_already",
    fail_rg="late_bnc|sct_posted|leftover_already",
    avoided="r260 iDEAL leftover already skip; r255 SEPA leftover. This is Bancontact leftover already skip vs SCT",
    fail_avoided="r270 Bancontact leftover already skip. This is late Bancontact after leftover SCT posted flags only",
    token_col="bcmc",
    result_val="BNC01",
    leftover_check="bnc_leftover_open",
    extra_col="  bcmc text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Bancontact leftover already skip vs leftover SCT",
    fail_surfaces="late Bancontact leftover after leftover SCT posted",
    this_is="leftover already skip; leftover posts leftover_id; SCT marks only",
    fail_this="late leftover already skip flags; SCT stays",
    seed="Bancontact leftover already + SCT mark same leftover_id",
    fail_seed="SCT leftover posted then late Bancontact leftover",
    counterpart="leftover SCT",
)

# r271 leftover Sofort leftover already skip vs leftover SCT
already(
    ok_slug="sofort-leftover-already-vs-sct",
    fail_slug="sofort-after-sct",
    stem="sft_sk",
    fail_stem="sft_lt",
    event="Sofort leftover",
    fail_event="Sofort leftover",
    pk="sofort_id",
    fail_pk="late_sofort_id",
    ctor="sft",
    rid="sf",
    rg="sofort|klarna_paynow|leftover_already",
    fail_rg="late_sofort|sct_posted|leftover_already",
    avoided="r270 Bancontact leftover already skip; r260 iDEAL leftover. This is Sofort leftover already skip vs SCT",
    fail_avoided="r271 Sofort leftover already skip. This is late Sofort after leftover SCT posted flags only",
    token_col="sofort_trx",
    result_val="SFT01",
    leftover_check="sofort_leftover_open",
    extra_col="  sofort_trx text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Sofort leftover already skip vs leftover SCT",
    fail_surfaces="late Sofort leftover after leftover SCT posted",
    this_is="leftover already skip; leftover posts leftover_id; SCT marks only",
    fail_this="late leftover already skip flags; SCT stays",
    seed="Sofort leftover already + SCT mark same leftover_id",
    fail_seed="SCT leftover posted then late Sofort leftover",
    counterpart="leftover SCT",
)

# r272 leftover BLIK leftover already skip vs leftover P24
already(
    ok_slug="blik-leftover-already-vs-p24",
    fail_slug="blik-after-p24",
    stem="blk_sk",
    fail_stem="blk_lt",
    event="BLIK leftover",
    fail_event="BLIK leftover",
    pk="blik_id",
    fail_pk="late_blik_id",
    ctor="blk",
    rid="bl",
    rg="blik_code|blik_leftover|leftover_already",
    fail_rg="late_blik|p24_posted|leftover_already",
    avoided="r271 Sofort leftover already skip; r256 PIX leftover. This is BLIK leftover already skip vs P24",
    fail_avoided="r272 BLIK leftover already skip. This is late BLIK after leftover P24 posted flags only",
    token_col="blik_code",
    result_val="BLK01",
    leftover_check="blik_leftover_open",
    extra_col="  blik_code text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="BLIK leftover already skip vs leftover P24",
    fail_surfaces="late BLIK leftover after leftover P24 posted",
    this_is="leftover already skip; leftover posts leftover_id; P24 marks only",
    fail_this="late leftover already skip flags; P24 stays",
    seed="BLIK leftover already + P24 mark same leftover_id",
    fail_seed="P24 leftover posted then late BLIK leftover",
    counterpart="leftover P24",
)

# r273 leftover Konbini leftover already skip vs leftover PayPay
already(
    ok_slug="konbini-leftover-already-vs-paypay",
    fail_slug="konbini-after-paypay",
    stem="knb_sk",
    fail_stem="knb_lt",
    event="Konbini leftover",
    fail_event="Konbini leftover",
    pk="konbini_id",
    fail_pk="late_konbini_id",
    ctor="knb",
    rid="kn",
    rg="konbini|convenience_store_leftover|leftover_already",
    fail_rg="late_konbini|paypay_posted|leftover_already",
    avoided="r272 BLIK leftover already skip; r261 Boleto leftover. This is Konbini leftover already skip vs PayPay",
    fail_avoided="r273 Konbini leftover already skip. This is late Konbini after leftover PayPay posted flags only",
    token_col="konbini_ref",
    result_val="KNB01",
    leftover_check="konbini_leftover_open",
    extra_col="  konbini_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="Konbini leftover already skip vs leftover PayPay",
    fail_surfaces="late Konbini leftover after leftover PayPay posted",
    this_is="leftover already skip; leftover posts leftover_id; PayPay marks only",
    fail_this="late leftover already skip flags; PayPay stays",
    seed="Konbini leftover already + PayPay mark same leftover_id",
    fail_seed="PayPay leftover posted then late Konbini leftover",
    counterpart="leftover PayPay",
)

# r274 leftover PromptPay leftover already skip vs leftover Thai QR
already(
    ok_slug="promptpay-leftover-already-vs-thaiqr",
    fail_slug="promptpay-after-thaiqr",
    stem="pmp_sk",
    fail_stem="pmp_lt",
    event="PromptPay leftover",
    fail_event="PromptPay leftover",
    pk="promptpay_id",
    fail_pk="late_promptpay_id",
    ctor="pmp",
    rid="pm",
    rg="promptpay|thai_qr_leftover|leftover_already",
    fail_rg="late_promptpay|thaiqr_posted|leftover_already",
    avoided="r256 PIX leftover already skip; r268 SPEI leftover. This is PromptPay leftover already skip vs Thai QR",
    fail_avoided="r274 PromptPay leftover already skip. This is late PromptPay after leftover Thai QR posted flags only",
    token_col="pp_id",
    result_val="PMP01",
    leftover_check="promptpay_leftover_open",
    extra_col="  pp_id text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="PromptPay leftover already skip vs leftover Thai QR",
    fail_surfaces="late PromptPay leftover after leftover Thai QR posted",
    this_is="leftover already skip; leftover posts leftover_id; Thai QR marks only",
    fail_this="late leftover already skip flags; Thai QR stays",
    seed="PromptPay leftover already + Thai QR mark same leftover_id",
    fail_seed="Thai QR leftover posted then late PromptPay leftover",
    counterpart="leftover Thai QR",
)

# r275 leftover DuitNow leftover already skip vs leftover FPX
already(
    ok_slug="duitnow-leftover-already-vs-fpx",
    fail_slug="duitnow-after-fpx",
    stem="dnw_sk",
    fail_stem="dnw_lt",
    event="DuitNow leftover",
    fail_event="DuitNow leftover",
    pk="duitnow_id",
    fail_pk="late_duitnow_id",
    ctor="dnw",
    rid="dn",
    rg="duitnow|duitnow_qr|leftover_already",
    fail_rg="late_duitnow|fpx_posted|leftover_already",
    avoided="r274 PromptPay leftover already skip; r257 UPI leftover. This is DuitNow leftover already skip vs FPX",
    fail_avoided="r275 DuitNow leftover already skip. This is late DuitNow after leftover FPX posted flags only",
    token_col="duitnow_ref",
    result_val="DNW01",
    leftover_check="duitnow_leftover_open",
    extra_col="  duitnow_ref text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="DuitNow leftover already skip vs leftover FPX",
    fail_surfaces="late DuitNow leftover after leftover FPX posted",
    this_is="leftover already skip; leftover posts leftover_id; FPX marks only",
    fail_this="late leftover already skip flags; FPX stays",
    seed="DuitNow leftover already + FPX mark same leftover_id",
    fail_seed="FPX leftover posted then late DuitNow leftover",
    counterpart="leftover FPX",
)

# r276 leftover IMPS leftover already skip vs leftover NEFT
already(
    ok_slug="imps-leftover-already-vs-neft",
    fail_slug="imps-after-neft",
    stem="imp_sk",
    fail_stem="imp_lt",
    event="IMPS leftover",
    fail_event="IMPS leftover",
    pk="imps_id",
    fail_pk="late_imps_id",
    ctor="imp",
    rid="im",
    rg="imps_rrn|imps_leftover|leftover_already",
    fail_rg="late_imps|neft_posted|leftover_already",
    avoided="r257 UPI leftover already skip; r167 nacha cartesian. This is IMPS leftover already skip vs NEFT",
    fail_avoided="r276 IMPS leftover already skip. This is late IMPS after leftover NEFT posted flags only",
    token_col="imps_rrn",
    result_val="IMP01",
    leftover_check="imps_leftover_open",
    extra_col="  imps_rrn text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="IMPS leftover already skip vs leftover NEFT",
    fail_surfaces="late IMPS leftover after leftover NEFT posted",
    this_is="leftover already skip; leftover posts leftover_id; NEFT marks only",
    fail_this="late leftover already skip flags; NEFT stays",
    seed="IMPS leftover already + NEFT mark same leftover_id",
    fail_seed="NEFT leftover posted then late IMPS leftover",
    counterpart="leftover NEFT",
)

# r277 leftover RTGS leftover already skip vs leftover IMPS
already(
    ok_slug="rtgs-leftover-already-vs-imps",
    fail_slug="rtgs-after-imps",
    stem="rtg_sk",
    fail_stem="rtg_lt",
    event="RTGS leftover",
    fail_event="RTGS leftover",
    pk="rtgs_id",
    fail_pk="late_rtgs_id",
    ctor="rtg",
    rid="rg",
    rg="rtgs_utr|rtgs_leftover|leftover_already",
    fail_rg="late_rtgs|imps_posted|leftover_already",
    avoided="r276 IMPS leftover already skip; r259 MT103 leftover. This is RTGS leftover already skip vs IMPS",
    fail_avoided="r277 RTGS leftover already skip. This is late RTGS after leftover IMPS posted flags only",
    token_col="utr",
    result_val="RTG01",
    leftover_check="rtgs_leftover_open",
    extra_col="  utr text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="RTGS leftover already skip vs leftover IMPS",
    fail_surfaces="late RTGS leftover after leftover IMPS posted",
    this_is="leftover already skip; leftover posts leftover_id; IMPS marks only",
    fail_this="late leftover already skip flags; IMPS stays",
    seed="RTGS leftover already + IMPS mark same leftover_id",
    fail_seed="IMPS leftover posted then late RTGS leftover",
    counterpart="leftover IMPS",
)

# r278 leftover UnionPay leftover already skip vs leftover QR
already(
    ok_slug="unionpay-leftover-already-vs-qr",
    fail_slug="unionpay-after-qr",
    stem="unp_sk",
    fail_stem="unp_lt",
    event="UnionPay leftover",
    fail_event="UnionPay leftover",
    pk="unionpay_id",
    fail_pk="late_unionpay_id",
    ctor="unp",
    rid="un",
    rg="unionpay_qr|upqr_leftover|leftover_already",
    fail_rg="late_unionpay|qr_posted|leftover_already",
    avoided="r274 PromptPay leftover already skip; r109 wechat. This is UnionPay leftover already skip vs leftover QR",
    fail_avoided="r278 UnionPay leftover already skip. This is late UnionPay after leftover QR posted flags only",
    token_col="upqr",
    result_val="UNP01",
    leftover_check="unionpay_leftover_open",
    extra_col="  upqr text UNIQUE",
    fail_extra="  leftover_id text NOT NULL",
    surfaces="UnionPay leftover already skip vs leftover QR",
    fail_surfaces="late UnionPay leftover after leftover QR posted",
    this_is="leftover already skip; leftover posts leftover_id; QR marks only",
    fail_this="late leftover already skip flags; QR stays",
    seed="UnionPay leftover already + QR mark same leftover_id",
    fail_seed="QR leftover posted then late UnionPay leftover",
    counterpart="leftover QR",
)
