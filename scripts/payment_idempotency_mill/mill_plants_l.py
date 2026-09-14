"""Plants r167+: hotel/rental/rail/rtp/ethoca/escrow (not r148–r166 ledger twins)."""

from mill_plants_j import _ok_pair, _fail_pair

MORE = []


def pair(ok, bad):
    MORE.append((ok, bad))


def _tb(fn, ctor, hook, key, cents=5000, extra=0, rows_fn="rows"):
    total = cents + extra
    return (
        f"def {fn}():\n"
        f'    {ctor}({ctor[0:2] if False else ctor}("{key}_1", charge="ch_1", cents={cents if extra == 0 else extra}))\n'
        f'    {ctor}("{key}_1", charge="ch_1", cents={cents if extra == 0 else extra})\n'
        f'    {hook}("ch_1", {cents})\n'
        f'    assert merch_cents("m_1") == {total} and {rows_fn}("{key}_1") == 1\n'
        "\n"
        f"def test_second():\n"
        f'    {ctor}("{key}_a", charge="ch_a", cents=4)\n'
        f'    {hook}("ch_a", 100)\n'
        f'    {ctor}("{key}_b", charge="ch_b", cents=2)\n'
        f'    {hook}("ch_b", 40)\n'
        f'    assert merch_cents("m_a") == {100 + (0 if extra == 0 else 4)} and merch_cents("m_b") == {40 + (0 if extra == 0 else 2)}\n'
    )


def add(
    *,
    ok_slug,
    fail_slug,
    stem,
    fail_stem,
    fn,
    fail_fn,
    hook_fn,
    fail_hook,
    inner,
    fail_inner,
    comment,
    fail_comment,
    hook_body,
    fail_hook_body,
    test_fn,
    fail_test_fn,
    table,
    fail_table,
    pk,
    fail_pk,
    rg,
    fail_rg,
    surfaces,
    fail_surfaces,
    avoided,
    fail_avoided,
    this_is,
    fail_this,
    seed,
    fail_seed,
    first_apply,
    fail_first,
    plan_change,
    fail_plan,
    skip_pred,
    fail_skip_pred,
    verb,
    skip_label,
    fail_skip_label,
    obs3,
    fail_obs3,
    obs4,
    fail_obs4,
    obs5,
    fail_obs5,
    fail_obs,
    fail_fail_obs,
    obs7,
    fail_obs7,
    still_fail_obs,
    fail_still,
    rewrite_src,
    fail_rewrite_src,
    rewrite_src_obs,
    fail_rewrite_src_obs,
    rewrite_hook,
    fail_rewrite_hook,
    rewrite_hook_obs,
    fail_rewrite_hook_obs,
    extra_ddl,
    fail_extra_ddl,
    residual,
    grep_pat,
    grep_obs,
    goal,
    fail_goal,
    plan,
    fail_plan_txt,
    outcome,
    fail_outcome,
    skip_new,
    fail_skip_new,
    psql_rows,
    test_name,
    fail_test_name,
    surface_read,
    fail_surface,
    next_note,
    xfail_label,
    xfail_body,
    xfail_fail_obs,
    xfail_fn,
    xfail_reason,
    test_body,
    fail_test_body,
    test2_body,
    fail_test2,
    fail_test_short,
):
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
            table=table,
            pk=pk,
            rg=rg,
            surfaces=surfaces,
            avoided=avoided,
            this_is=this_is,
            seed=seed,
            first_apply=first_apply,
            plan_change=plan_change,
            step_note="Event-day 6–7; PK 8–11; second 12–13.",
            skip_pred=skip_pred,
            verb=verb,
            skip_label=skip_label,
            obs3=obs3,
            obs4=obs4,
            obs5=obs5,
            fail_obs=fail_obs,
            obs7=obs7,
            still_fail_obs=still_fail_obs,
            rewrite_src=rewrite_src,
            rewrite_src_obs=rewrite_src_obs,
            rewrite_hook=rewrite_hook,
            rewrite_hook_obs=rewrite_hook_obs,
            extra_ddl=extra_ddl,
            residual=residual,
            grep_pat=grep_pat,
            grep_obs=grep_obs,
            goal=goal,
            plan=plan,
            outcome=outcome,
            skip_new=skip_new,
            psql_rows=psql_rows,
            test_name=test_name,
            surface_read=surface_read,
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
            table=fail_table,
            pk=fail_pk,
            rg=fail_rg,
            surfaces=fail_surfaces,
            avoided=fail_avoided,
            this_is=fail_this,
            seed=fail_seed,
            first_apply=fail_first,
            plan_change=fail_plan,
            step_note="Late-day 6–7; PK 8–11; second 12–13; xfail 15–17.",
            next_note=next_note,
            skip_pred=fail_skip_pred,
            verb=verb,
            skip_label=fail_skip_label,
            obs3=fail_obs3,
            obs4=fail_obs4,
            obs5=fail_obs5,
            fail_obs=fail_fail_obs,
            obs7=fail_obs7,
            still_fail_obs=fail_still,
            rewrite_src=fail_rewrite_src,
            rewrite_src_obs=fail_rewrite_src_obs,
            rewrite_hook=fail_rewrite_hook,
            rewrite_hook_obs=fail_rewrite_hook_obs,
            extra_ddl=fail_extra_ddl,
            xfail_label=xfail_label,
            xfail_body=xfail_body,
            xfail_fail_obs=xfail_fail_obs,
            xfail_fn=xfail_fn,
            xfail_reason=xfail_reason,
            goal=fail_goal,
            plan=fail_plan_txt,
            outcome=fail_outcome,
            skip_new=fail_skip_new,
            test_name=fail_test_name,
            surface_read=fail_surface,
            test_body_short=fail_test_short,
        ),
    )


# r167 hotel no-show vs preauth / no-show after checkout
add(
    ok_slug="hotel-noshow-vs-preauth",
    fail_slug="noshow-after-checkout",
    stem="htl_ns",
    fail_stem="htl_late",
    fn="on_noshow",
    fail_fn="late_ns",
    hook_fn="capture_stay",
    fail_hook="already_stay",
    inner='credit_hotel(ev["stay_id"], ev["cents"])',
    fail_inner='credit_hotel(ev["stay_id"], ev["cents"])',
    comment="counted every no-show",
    fail_comment="counted every late no-show",
    hook_body="def capture_stay(stay_id, cents):\n    credit_hotel(stay_id, cents)\n",
    fail_hook_body="def already_stay(stay_id, cents):\n    credit_hotel(stay_id, cents)\n",
    test_fn="test_noshow_not_stay_double",
    fail_test_fn="test_late_ns_not_add",
    table="till_htl_ns",
    fail_table="till_htl_late",
    pk="stay_id",
    fail_pk="late_ns_id",
    rg="no_show|preauth|folio",
    fail_rg="late_noshow|checked_out|folio_closed",
    surfaces="hotel no-show fee vs stay preauth capture",
    fail_surfaces="no-show after checkout folio closed",
    avoided="r161 partial capture remainder; r156 3DS. This is stay_id no-show vs folio capture",
    fail_avoided="r167 no-show vs preauth. This is late no-show after checkout receivable",
    this_is="no-show records; stay capture PK folio",
    fail_this="late no-show opens receivable; stay stays",
    seed="no-show + stay capture same stay_id",
    fail_seed="checkout then late no-show",
    first_apply="stay no-showed today",
    fail_first="late no-show posted today",
    plan_change="no-show records; capture PK stay_id",
    fail_plan="late ns PK receivable; stay stays",
    skip_pred="this stay already no-showed today",
    fail_skip_pred="this late no-show already posted today",
    verb="capture",
    skip_label="stay-noshow-today skip",
    fail_skip_label="late-noshow-today skip",
    obs3="no-show and stay capture both credit",
    fail_obs3="late no-show extra-credits after checkout",
    obs4="no-show records; capture PK",
    fail_obs4="late ns receivable; stay stays",
    obs5="hotel 5000; no-show once; second stay adds",
    fail_obs5="hotel 2000; recv 3000; second late adds",
    fail_obs="FAILED test_noshow_not_stay_double - rows 3 or hotel 10000\n1 failed, 1 passed",
    fail_fail_obs="FAILED test_late_ns_not_add - hotel 5000 == 2000 or rows 3\n1 failed, 1 passed",
    obs7="stay capture still credits; new stay same day dropped.",
    fail_obs7="second late ok; hides receivable.",
    still_fail_obs="FAILED test_noshow_not_stay_double - no-show still credits or capture adds\n1 failed, 1 passed",
    fail_still="FAILED if late ns extra-credited\n1 failed or 1 passed lucky",
    rewrite_src=(
        "def on_noshow(ev):\n"
        "    if not claim_ns(ev['stay_id']):\n"
        '        return {"ok": True, "dup": True}\n'
        '    flag_ns(ev["stay_id"])\n'
        '    return {"ok": True, "ns": True}\n'
    ),
    fail_rewrite_src=(
        "def late_ns(ev):\n"
        "    if not claim_lns(ev.get('late_ns_id') or ev['stay_id']+'_ln'):\n"
        '        return {"ok": True, "dup": True}\n'
        '    open_recv(hotel_of(ev["stay_id"]), ev["cents"], ns=ev["stay_id"])\n'
        '    return {"ok": True, "recv": True}\n'
    ),
    rewrite_src_obs="claim stay_id flags no-show",
    fail_rewrite_src_obs="claim late_ns opens receivable",
    rewrite_hook=(
        "def capture_stay(stay_id, cents):\n"
        "    if not claim_stay(stay_id):\n"
        '        return {"ok": True, "dup": True}\n'
        "    credit_hotel(hotel_of(stay_id), cents)\n"
        '    return {"ok": True}\n'
    ),
    fail_rewrite_hook=(
        "def already_stay(stay_id, cents):\n"
        "    if not claim_stay2(stay_id):\n"
        "        return existing_stay(stay_id)\n"
        "    credit_hotel(hotel_of(stay_id), cents)\n"
        "    return stay_id\n"
    ),
    rewrite_hook_obs="PK stay capture",
    fail_rewrite_hook_obs="stay stays",
    extra_ddl="  folio_id text UNIQUE",
    fail_extra_ddl="  stay_id text NOT NULL",
    residual="folio reverse after checkout last-write",
    grep_pat="claim_stay",
    grep_obs="src/htl_ns.py: no-show flags; stay capture PK",
    goal="till-htl no-show and stay capture both credited. No-show flags; stay PK. Gate: tests/test_htl_ns.py.",
    fail_goal="till-htllate late no-show extra-credited after checkout. Late recv. Gate: tests/test_htl_late.py.",
    plan="Skip capture if this stay already no-showed today.",
    fail_plan_txt="Skip capture if this late no-show already posted today.",
    outcome="No-show+stay doubled. No-show-day skip left stay unguarded. Plan change: stay PK. Tests 2/2 + second stay + suite 8/8.",
    fail_outcome="Late ns extra-credited. Late-day skip hid receivable. Plan change: late PK recv. Primary+second pass. Partial: extra xfail handoff.",
    skip_new='    if not ns_today(ev["stay_id"]):\n        credit_hotel(ev["stay_id"], ev["cents"])',
    fail_skip_new='    if not lns_today(ev["stay_id"]):\n        credit_hotel(ev["stay_id"], ev["cents"])',
    psql_rows="st_1\nst_a\nst_b",
    test_name="noshow-not-stay-double test",
    fail_test_name="late-ns-not-add test",
    surface_read="hotel no-show plus stay preauth",
    fail_surface="late no-show plus checked-out folio",
    next_note="Unused: late no-show should still capture. Avoid late-noshow-today skip.",
    xfail_label="late no-show should still capture",
    xfail_body=(
        "def test_late_ns_captures():\n"
        '    already_stay("st_p", 2000)\n'
        '    late_ns(ns("ln_p", charge="ch_p", cents=3000))\n'
        '    assert hotel_cents("h_p") == 5000 and recv_cents("m_p") == 0\n'
    ),
    xfail_fail_obs="FAILED test_late_ns_captures - recv opened; hotel stayed 2000\n1 failed",
    xfail_fn="test_late_ns_captures",
    xfail_reason="late no-show capture vs receivable is a policy fork",
    test_body=(
        "def test_noshow_not_stay_double():\n"
        '    on_noshow(ns("st_1", charge="ch_1", cents=2000))\n'
        '    on_noshow(ns("st_1", charge="ch_1", cents=2000))\n'
        '    capture_stay("st_1", 3000)\n'
        '    assert hotel_cents("h_1") == 5000 and ns_rows("st_1") == 1\n'
        "\n"
        "def test_second():\n"
        '    on_noshow(ns("st_a", charge="ch_a", cents=40))\n'
        '    capture_stay("st_a", 60)\n'
        '    on_noshow(ns("st_b", charge="ch_b", cents=10))\n'
        '    capture_stay("st_b", 30)\n'
        '    assert hotel_cents("h_a") == 100 and hotel_cents("h_b") == 40\n'
    ),
    fail_test_body=(
        "def test_late_ns_not_add():\n"
        '    already_stay("st_1", 2000)\n'
        '    late_ns(ns("ln_1", charge="ch_1", cents=3000))\n'
        '    late_ns(ns("ln_1", charge="ch_1", cents=3000))\n'
        '    assert hotel_cents("h_1") == 2000 and recv_cents("m_1") == 3000 and lns_rows("ln_1") == 1\n'
        "\n"
        "def test_second_late():\n"
        '    already_stay("st_a", 40)\n'
        '    late_ns(ns("ln_a", charge="ch_a", cents=60))\n'
        '    already_stay("st_b", 10)\n'
        '    late_ns(ns("ln_b", charge="ch_b", cents=30))\n'
        '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
    ),
    test2_body=(
        "def test_second():\n"
        '    on_noshow(ns("st_a", charge="ch_a", cents=40))\n'
        '    capture_stay("st_a", 60)\n'
        '    on_noshow(ns("st_b", charge="ch_b", cents=10))\n'
        '    capture_stay("st_b", 30)\n'
        '    assert hotel_cents("h_a") == 100 and hotel_cents("h_b") == 40\n'
    ),
    fail_test2=(
        "def test_second_late():\n"
        '    already_stay("st_a", 40)\n'
        '    late_ns(ns("ln_a", charge="ch_a", cents=60))\n'
        '    already_stay("st_b", 10)\n'
        '    late_ns(ns("ln_b", charge="ch_b", cents=30))\n'
        '    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
    ),
    fail_test_short="same — late no-show receivable; stay stays",
)


def _pair_from(
    ok_slug,
    fail_slug,
    stem,
    fail_stem,
    domain,
    ok_event,
    fail_event,
    pk,
    fail_pk,
    rg,
    fail_rg,
    avoided,
    fail_avoided,
    ctor="ev",
):
    """Compact ledger pair: record event vs capture, late event opens receivable."""
    fn = f"on_{stem.split('_')[0]}"
    fail_fn = f"late_{fail_stem.split('_')[-1]}"
    hook_fn = f"cap_{stem}"
    fail_hook = f"already_{stem}"
    credit = f"credit_{domain}"
    add(
        ok_slug=ok_slug,
        fail_slug=fail_slug,
        stem=stem,
        fail_stem=fail_stem,
        fn=fn,
        fail_fn=fail_fn,
        hook_fn=hook_fn,
        fail_hook=fail_hook,
        inner=f'{credit}(ev["{pk}"], ev["cents"])',
        fail_inner=f'{credit}(ev["{pk}"], ev["cents"])',
        comment=f"counted every {ok_event}",
        fail_comment=f"counted every late {fail_event}",
        hook_body=f"def {hook_fn}(oid, cents):\n    {credit}(oid, cents)\n",
        fail_hook_body=f"def {fail_hook}(oid, cents):\n    {credit}(oid, cents)\n",
        test_fn=f"test_{stem}_not_double",
        fail_test_fn=f"test_{fail_stem}_not_add",
        table=f"till_{stem}",
        fail_table=f"till_{fail_stem}",
        pk=pk,
        fail_pk=fail_pk,
        rg=rg,
        fail_rg=fail_rg,
        surfaces=f"{ok_event} vs capture",
        fail_surfaces=f"late {fail_event} after already captured",
        avoided=avoided,
        fail_avoided=fail_avoided,
        this_is=f"{ok_event} records; capture PK {pk}",
        fail_this=f"late {fail_event} opens receivable; capture stays",
        seed=f"{ok_event} + capture same {pk}",
        fail_seed=f"capture then late {fail_event}",
        first_apply=f"{ok_event} today",
        fail_first=f"late {fail_event} posted today",
        plan_change=f"{ok_event} records; capture PK {pk}",
        fail_plan=f"late {fail_event} PK receivable; capture stays",
        skip_pred=f"this {ok_event} already posted today",
        fail_skip_pred=f"this late {fail_event} already posted today",
        verb="capture",
        skip_label=f"{ok_event}-today skip",
        fail_skip_label=f"late-{fail_event}-today skip",
        obs3=f"{ok_event} and capture both credit",
        fail_obs3=f"late {fail_event} extra-credits",
        obs4=f"{ok_event} records; capture PK",
        fail_obs4=f"late {fail_event} receivable; capture stays",
        obs5=f"{domain} 5000; {ok_event} once; second adds",
        fail_obs5=f"{domain} 2000; recv 3000; second late adds",
        fail_obs=f"FAILED test_{stem}_not_double - rows 3 or doubled credit\n1 failed, 1 passed",
        fail_fail_obs=f"FAILED test_{fail_stem}_not_add - doubled or rows 3\n1 failed, 1 passed",
        obs7=f"capture still credits; new {ok_event} same day dropped.",
        fail_obs7="second late ok; hides receivable.",
        still_fail_obs=f"FAILED test_{stem}_not_double - still double credit\n1 failed, 1 passed",
        fail_still="FAILED if late extra-credited\n1 failed or 1 passed lucky",
        rewrite_src=(
            f"def {fn}(ev):\n"
            f"    if not claim_{stem}(ev['{pk}']):\n"
            '        return {"ok": True, "dup": True}\n'
            f'    flag_{stem}(ev["{pk}"])\n'
            '    return {"ok": True, "flag": True}\n'
        ),
        fail_rewrite_src=(
            f"def {fail_fn}(ev):\n"
            f"    if not claim_{fail_stem}(ev.get('{fail_pk}') or ev['{pk}']+'_l'):\n"
            '        return {"ok": True, "dup": True}\n'
            f'    open_recv({domain}_of(ev["{pk}"]), ev["cents"])\n'
            '    return {"ok": True, "recv": True}\n'
        ),
        rewrite_src_obs=f"claim {pk} flags {ok_event}",
        fail_rewrite_src_obs=f"claim {fail_pk} opens receivable",
        rewrite_hook=(
            f"def {hook_fn}(oid, cents):\n"
            f"    if not claim_cap_{stem}(oid):\n"
            '        return {"ok": True, "dup": True}\n'
            f"    {credit}({domain}_of(oid), cents)\n"
            '    return {"ok": True}\n'
        ),
        fail_rewrite_hook=(
            f"def {fail_hook}(oid, cents):\n"
            f"    if not claim_cap2_{stem}(oid):\n"
            "        return existing_cap(oid)\n"
            f"    {credit}({domain}_of(oid), cents)\n"
            "    return oid\n"
        ),
        rewrite_hook_obs=f"PK {ok_event} capture",
        fail_rewrite_hook_obs="capture stays",
        extra_ddl=f"  {pk} text UNIQUE",
        fail_extra_ddl=f"  {pk} text NOT NULL",
        residual=f"{ok_event} last-write vs capture",
        grep_pat=f"claim_cap_{stem}",
        grep_obs=f"src/{stem}.py: {ok_event} flags; capture PK",
        goal=f"till-{stem} {ok_event} and capture both credited. Flag+PK. Gate: tests/test_{stem}.py.",
        fail_goal=f"till-{fail_stem} late {fail_event} extra-credited. Late recv. Gate: tests/test_{fail_stem}.py.",
        plan=f"Skip capture if this {ok_event} already posted today.",
        fail_plan_txt=f"Skip capture if this late {fail_event} already posted today.",
        outcome=f"{ok_event}+capture doubled. Day skip left capture unguarded. Plan change: {pk} PK. Tests 2/2 + second + suite 8/8.",
        fail_outcome=f"Late {fail_event} extra-credited. Skip hid receivable. Plan change: {fail_pk} recv. Partial: extra xfail handoff.",
        skip_new=f'    if not {stem}_today(ev["{pk}"]):\n        {credit}(ev["{pk}"], ev["cents"])',
        fail_skip_new=f'    if not {fail_stem}_today(ev["{pk}"]):\n        {credit}(ev["{pk}"], ev["cents"])',
        psql_rows=f"x_1\nx_a\nx_b",
        test_name=f"{stem}-not-double test",
        fail_test_name=f"{fail_stem}-not-add test",
        surface_read=f"{ok_event} plus capture",
        fail_surface=f"late {fail_event} plus prior capture",
        next_note=f"Unused: late {fail_event} should still capture. Avoid late-{fail_event}-today skip.",
        xfail_label=f"late {fail_event} should still capture",
        xfail_body=(
            f"def test_late_{fail_stem}_captures():\n"
            f'    {fail_hook}("x_p", 2000)\n'
            f'    {fail_fn}({ctor}("l_p", charge="ch_p", cents=3000))\n'
            f'    assert {domain}_cents("d_p") == 5000 and recv_cents("m_p") == 0\n'
        ),
        xfail_fail_obs=f"FAILED test_late_{fail_stem}_captures - recv opened\n1 failed",
        xfail_fn=f"test_late_{fail_stem}_captures",
        xfail_reason=f"late {fail_event} capture vs receivable is a policy fork",
        test_body=(
            f"def test_{stem}_not_double():\n"
            f'    {fn}({ctor}("x_1", charge="ch_1", cents=2000))\n'
            f'    {fn}({ctor}("x_1", charge="ch_1", cents=2000))\n'
            f'    {hook_fn}("x_1", 3000)\n'
            f'    assert {domain}_cents("d_1") == 5000 and {stem}_rows("x_1") == 1\n'
            "\n"
            f"def test_second():\n"
            f'    {fn}({ctor}("x_a", charge="ch_a", cents=40))\n'
            f'    {hook_fn}("x_a", 60)\n'
            f'    {fn}({ctor}("x_b", charge="ch_b", cents=10))\n'
            f'    {hook_fn}("x_b", 30)\n'
            f'    assert {domain}_cents("d_a") == 100 and {domain}_cents("d_b") == 40\n'
        ),
        fail_test_body=(
            f"def test_{fail_stem}_not_add():\n"
            f'    {fail_hook}("x_1", 2000)\n'
            f'    {fail_fn}({ctor}("l_1", charge="ch_1", cents=3000))\n'
            f'    {fail_fn}({ctor}("l_1", charge="ch_1", cents=3000))\n'
            f'    assert {domain}_cents("d_1") == 2000 and recv_cents("m_1") == 3000 and {fail_stem}_rows("l_1") == 1\n'
            "\n"
            f"def test_second_late():\n"
            f'    {fail_hook}("x_a", 40)\n'
            f'    {fail_fn}({ctor}("l_a", charge="ch_a", cents=60))\n'
            f'    {fail_hook}("x_b", 10)\n'
            f'    {fail_fn}({ctor}("l_b", charge="ch_b", cents=30))\n'
            f'    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        test2_body=(
            f"def test_second():\n"
            f'    {fn}({ctor}("x_a", charge="ch_a", cents=40))\n'
            f'    {hook_fn}("x_a", 60)\n'
            f'    {fn}({ctor}("x_b", charge="ch_b", cents=10))\n'
            f'    {hook_fn}("x_b", 30)\n'
            f'    assert {domain}_cents("d_a") == 100 and {domain}_cents("d_b") == 40\n'
        ),
        fail_test2=(
            f"def test_second_late():\n"
            f'    {fail_hook}("x_a", 40)\n'
            f'    {fail_fn}({ctor}("l_a", charge="ch_a", cents=60))\n'
            f'    {fail_hook}("x_b", 10)\n'
            f'    {fail_fn}({ctor}("l_b", charge="ch_b", cents=30))\n'
            f'    assert recv_cents("m_a") == 60 and recv_cents("m_b") == 30\n'
        ),
        fail_test_short=f"same — late {fail_event} receivable; capture stays",
    )


# r168+ compact unique verticals
_pair_from(
    "car-rental-delayed-vs-return",
    "delayed-after-return",
    "rent_dly",
    "rent_late",
    "rental",
    "delayed charge",
    "delayed charge",
    "rental_id",
    "delay_id",
    "delayed_charge|rental_return|ra_number",
    "late_delayed|returned_ra|recv_delay",
    "r167 hotel no-show; r161 remainder. This is rental_id delayed vs return capture",
    "r168 delayed vs return. This is late delayed after RA return receivable",
    ctor="ra",
)
_pair_from(
    "airline-emd-vs-ticket",
    "emd-after-void",
    "air_emd",
    "air_late",
    "airline",
    "EMD",
    "EMD",
    "ticket_id",
    "emd_id",
    "emd|e_ticket|conjunction",
    "late_emd|void_ticket|recv_emd",
    "r168 rental delayed; r156 3DS. This is ticket_id EMD vs e-ticket capture",
    "r169 EMD vs ticket. This is late EMD after void receivable",
    ctor="tk",
)
_pair_from(
    "transit-tapoff-vs-tapon",
    "tapoff-after-fare",
    "txn_tap",
    "txn_late",
    "transit",
    "tap-off",
    "tap-off",
    "trip_id",
    "tap_id",
    "tap_off|tap_on|fare_cap",
    "late_tapoff|fare_posted|recv_tap",
    "r169 airline EMD; r161 remainder. This is trip_id tap-off vs tap-on fare",
    "r170 tap-off vs tap-on. This is late tap-off after fare posted receivable",
    ctor="tr",
)
_pair_from(
    "ev-stop-vs-start",
    "stop-after-session",
    "ev_stop",
    "ev_late",
    "ev",
    "session stop",
    "session stop",
    "session_id",
    "stop_id",
    "ocpp_stop|session_kwh|evse",
    "late_stop|session_billed|recv_kwh",
    "r170 transit tap; r167 hotel. This is session_id OCPP stop vs start kWh",
    "r171 ev stop vs start. This is late stop after session billed receivable",
    ctor="ev",
)
_pair_from(
    "paypal-payout-item-vs-batch",
    "item-after-batch",
    "pp_item",
    "pp_late",
    "payout",
    "payout item",
    "payout item",
    "batch_id",
    "item_id",
    "payout_item|payout_batch|sender_batch",
    "late_item|batch_claimed|recv_item",
    "r117 clover; r109 wechat. This is batch_id item vs batch claimed",
    "r172 payout item vs batch. This is late item after batch claimed receivable",
    ctor="po",
)
_pair_from(
    "square-complete-vs-create",
    "complete-after-create",
    "sq_done",
    "sq_late",
    "square",
    "payment complete",
    "payment complete",
    "payment_id",
    "complete_id",
    "complete_payment|create_payment|sq_idem",
    "late_complete|already_created|recv_sq",
    "r117 clover payment vs refund. This is payment_id complete vs create",
    "r173 square complete vs create. This is late complete after create receivable",
    ctor="sq",
)
_pair_from(
    "apple-dpas-vs-token",
    "dpas-after-token",
    "ap_dpas",
    "ap_late",
    "wallet",
    "DPAN bind",
    "DPAN bind",
    "token_id",
    "dpas_id",
    "dpas|dpan|apple_pay_token",
    "late_dpas|token_bound|recv_dpan",
    "r155 network token vs PAN; r162 account updater. This is token_id DPAS vs device PAN",
    "r174 apple DPAS vs token. This is late DPAS after token bound receivable",
    ctor="ap",
)
_pair_from(
    "click-to-pay-vs-pan",
    "src-after-pan",
    "ctp_src",
    "ctp_late",
    "src",
    "SRC correlation",
    "SRC correlation",
    "src_id",
    "corr_id",
    "click_to_pay|src_correlation|visa_src",
    "late_src|pan_charged|recv_src",
    "r174 apple DPAS; r162 PAN after updater. This is src_id Click to Pay vs PAN",
    "r175 SRC vs PAN. This is late SRC after PAN charged receivable",
    ctor="sr",
)
_pair_from(
    "ethoca-alert-vs-refund",
    "alert-after-refund",
    "eth_al",
    "eth_late",
    "ethoca",
    "Ethoca alert",
    "Ethoca alert",
    "alert_id",
    "eth_id",
    "ethoca_alert|outcome_refund|case_id",
    "late_alert|already_refunded|recv_eth",
    "r144 retrieval vs chargeback. This is alert_id Ethoca vs refund",
    "r176 ethoca alert vs refund. This is late alert after refund receivable",
    ctor="et",
)
_pair_from(
    "dunning-retry-vs-invoice",
    "retry-after-invoice",
    "dun_try",
    "dun_late",
    "dunning",
    "dunning retry",
    "dunning retry",
    "invoice_id",
    "retry_id",
    "dunning_retry|past_due|invoice_open",
    "late_retry|invoice_paid|recv_dun",
    "r166 insurance premium; r164 store credit. This is invoice_id dunning retry vs invoice",
    "r177 dunning retry vs invoice. This is late retry after invoice paid receivable",
    ctor="dn",
)
_pair_from(
    "escrow-release-vs-fund",
    "release-after-fund",
    "esc_rel",
    "esc_late",
    "escrow",
    "escrow release",
    "escrow release",
    "escrow_id",
    "release_id",
    "escrow_release|escrow_fund|hold_id",
    "late_release|already_funded|recv_esc",
    "r164 store credit vs cash. This is escrow_id release vs fund",
    "r178 escrow release vs fund. This is late release after fund receivable",
    ctor="es",
)
_pair_from(
    "visa-oct-vs-original",
    "oct-after-original",
    "vis_oct",
    "vis_late",
    "oct",
    "OCT credit",
    "OCT credit",
    "oct_id",
    "push_id",
    "original_credit|oct_push|afd",
    "late_oct|original_posted|recv_oct",
    "r109 wechat notify; r98 worldpay. This is oct_id Original Credit vs original debit",
    "r179 visa OCT vs original. This is late OCT after original posted receivable",
    ctor="oc",
)
_pair_from(
    "sepa-r-txn-vs-sdd",
    "r-after-sdd",
    "sepa_r",
    "sepa_late",
    "sepa",
    "R-transaction",
    "R-transaction",
    "mandate_id",
    "rtx_id",
    "r_transaction|sdd_core|reason_code",
    "late_r|sdd_settled|recv_r",
    "r110 sepa? r123 link. This is mandate_id SEPA R-txn vs SDD",
    "r180 SEPA R vs SDD. This is late R after SDD settled receivable",
    ctor="sd",
)
_pair_from(
    "fednow-reject-vs-credit",
    "reject-after-credit",
    "fed_rej",
    "fed_late",
    "fednow",
    "FedNow reject",
    "FedNow reject",
    "msg_id",
    "rej_id",
    "fednow_reject|pacs008|uetr",
    "late_reject|credit_posted|recv_fed",
    "r179 visa OCT; r109 wechat. This is msg_id FedNow reject vs credit",
    "r181 FedNow reject vs credit. This is late reject after credit posted receivable",
    ctor="fn",
)
_pair_from(
    "pix-refund-vs-original",
    "refund-after-pix",
    "pix_rf",
    "pix_late",
    "pix",
    "PIX refund",
    "PIX refund",
    "end_to_end_id",
    "refund_id",
    "pix_refund|end_to_end|ispb",
    "late_pix_rf|pix_posted|recv_pix",
    "r181 FedNow; r118 ebanx. This is end_to_end_id PIX refund vs original",
    "r182 PIX refund vs original. This is late refund after PIX posted receivable",
    ctor="px",
)
_pair_from(
    "marketplace-hold-vs-release",
    "hold-after-release",
    "mkt_hld",
    "mkt_late",
    "market",
    "seller hold",
    "seller hold",
    "seller_id",
    "hold_id",
    "seller_hold|marketplace_release|kyc",
    "late_hold|already_released|recv_mkt",
    "r178 escrow; r164 store credit. This is seller_id hold vs release",
    "r183 marketplace hold vs release. This is late hold after release receivable",
    ctor="mk",
)
_pair_from(
    "usage-overage-vs-plan",
    "overage-after-plan",
    "use_ovg",
    "use_late",
    "usage",
    "usage overage",
    "usage overage",
    "sub_id",
    "overage_id",
    "usage_overage|plan_invoice|meter",
    "late_overage|plan_billed|recv_use",
    "r177 dunning; r166 insurance. This is sub_id usage overage vs plan invoice",
    "r184 usage overage vs plan. This is late overage after plan billed receivable",
    ctor="us",
)
_pair_from(
    "rfi-response-vs-deadline",
    "rfi-after-deadline",
    "rfi_rsp",
    "rfi_late",
    "rfi",
    "RFI response",
    "RFI response",
    "case_id",
    "rfi_id",
    "rfi_response|retrieval_deadline|case_open",
    "late_rfi|deadline_passed|recv_rfi",
    "r144 retrieval request; r176 ethoca. This is case_id RFI response vs deadline",
    "r185 RFI response vs deadline. This is late RFI after deadline receivable",
    ctor="rf",
)
_pair_from(
    "cdrn-alert-vs-refund",
    "cdrn-after-refund",
    "cdr_al",
    "cdr_late",
    "cdrn",
    "CDRN alert",
    "CDRN alert",
    "alert_id",
    "cdrn_id",
    "cdrn_alert|visa_cdrn|merchant_refund",
    "late_cdrn|already_refunded|recv_cdr",
    "r176 ethoca alert; r144 chargeback. This is alert_id CDRN vs refund",
    "r186 CDRN alert vs refund. This is late CDRN after refund receivable",
    ctor="cd",
)
_pair_from(
    "verifi-cancel-vs-refund",
    "verifi-after-refund",
    "ver_cn",
    "ver_late",
    "verifi",
    "Verifi cancel",
    "Verifi cancel",
    "order_id",
    "verifi_id",
    "verifi_cancel|order_insight|cancel_req",
    "late_verifi|already_refunded|recv_ver",
    "r186 CDRN; r176 ethoca. This is order_id Verifi cancel vs refund",
    "r187 Verifi cancel vs refund. This is late Verifi after refund receivable",
    ctor="vf",
)
_pair_from(
    "tc40-vs-chargeback",
    "tc40-after-cb",
    "tc40_fr",
    "tc40_late",
    "fraud",
    "TC40 fraud report",
    "TC40 fraud report",
    "arn",
    "tc40_id",
    "tc40|fraud_report|arn",
    "late_tc40|cb_posted|recv_tc40",
    "r144 chargeback debit; r154 representment. This is arn TC40 vs chargeback",
    "r188 TC40 vs chargeback. This is late TC40 after CB posted receivable",
    ctor="tc",
)
_pair_from(
    "nacha-return-vs-credit",
    "return-after-ach",
    "nach_ret",
    "nach_late",
    "ach",
    "NACHA return",
    "NACHA return",
    "trace_id",
    "return_id",
    "nacha_return|ach_credit|sec_code",
    "late_return|ach_posted|recv_nacha",
    "r180 SEPA R; r181 FedNow. This is trace_id NACHA return vs ACH credit",
    "r189 NACHA return vs credit. This is late return after ACH posted receivable",
    ctor="na",
)
_pair_from(
    "bacs-unpaid-vs-credit",
    "unpaid-after-bacs",
    "bacs_unp",
    "bacs_late",
    "bacs",
    "Bacs unpaid",
    "Bacs unpaid",
    "sun_id",
    "unpaid_id",
    "bacs_unpaid|auddis|sun",
    "late_unpaid|bacs_posted|recv_bacs",
    "r189 NACHA; r180 SEPA. This is sun_id Bacs unpaid vs credit",
    "r190 Bacs unpaid vs credit. This is late unpaid after Bacs posted receivable",
    ctor="ba",
)
_pair_from(
    "rtp-rfp-vs-credit",
    "rfp-after-rtp",
    "rtp_rfp",
    "rtp_late",
    "rtp",
    "RTP request-for-pay",
    "RTP request-for-pay",
    "rfp_id",
    "req_id",
    "rtp_rfp|request_for_pay|tchn",
    "late_rfp|rtp_posted|recv_rtp",
    "r181 FedNow; r179 visa OCT. This is rfp_id RTP RfP vs credit",
    "r191 RTP RfP vs credit. This is late RfP after RTP posted receivable",
    ctor="rt",
)
_pair_from(
    "grabpay-void-vs-capture",
    "void-after-grab",
    "grab_vd",
    "grab_late",
    "grab",
    "GrabPay void",
    "GrabPay void",
    "tx_id",
    "void_id",
    "grabpay_void|grab_capture|partner_tx",
    "late_void|grab_captured|recv_grab",
    "r173 square complete; r159 bnpl. This is tx_id GrabPay void vs capture",
    "r192 GrabPay void vs capture. This is late void after capture receivable",
    ctor="gr",
)
_pair_from(
    "gcash-refund-vs-pay",
    "refund-after-gcash",
    "gcash_rf",
    "gcash_late",
    "gcash",
    "GCash refund",
    "GCash refund",
    "ref_no",
    "gcash_id",
    "gcash_refund|gcash_pay|ref_no",
    "late_gcash|pay_posted|recv_gcash",
    "r182 PIX refund; r192 GrabPay. This is ref_no GCash refund vs pay",
    "r193 GCash refund vs pay. This is late refund after pay receivable",
    ctor="gc",
)
_pair_from(
    "alipay-close-vs-trade",
    "close-after-trade",
    "ali_cls",
    "ali_late",
    "alipay",
    "Alipay close",
    "Alipay close",
    "trade_no",
    "close_id",
    "alipay_close|trade_query|out_trade",
    "late_close|trade_posted|recv_ali",
    "r193 GCash; r109 wechat. This is trade_no Alipay close vs trade",
    "r194 Alipay close vs trade. This is late close after trade receivable",
    ctor="al",
)
_pair_from(
    "affirm-void-vs-auth",
    "void-after-affirm",
    "aff_vd",
    "aff_late",
    "affirm",
    "Affirm void",
    "Affirm void",
    "checkout_id",
    "void_id",
    "affirm_void|affirm_auth|checkout_token",
    "late_aff_void|auth_posted|recv_aff",
    "r159 bnpl fund; r192 GrabPay void. This is checkout_id Affirm void vs auth",
    "r195 Affirm void vs auth. This is late void after auth receivable",
    ctor="af",
)
_pair_from(
    "afterpay-void-vs-capture",
    "void-after-afterpay",
    "aft_vd",
    "aft_late",
    "afterpay",
    "Afterpay void",
    "Afterpay void",
    "order_token",
    "void_id",
    "afterpay_void|afterpay_capture|order_token",
    "late_aft|captured_ap|recv_aft",
    "r195 Affirm; r159 bnpl. This is order_token Afterpay void vs capture",
    "r196 Afterpay void vs capture. This is late void after capture receivable",
    ctor="at",
)
_pair_from(
    "zip-refund-vs-charge",
    "refund-after-zip",
    "zip_rf",
    "zip_late",
    "zip",
    "Zip refund",
    "Zip refund",
    "charge_id",
    "zip_id",
    "zip_refund|zip_charge|idempotency",
    "late_zip|charge_posted|recv_zip",
    "r196 Afterpay; r182 PIX. This is charge_id Zip refund vs charge",
    "r197 Zip refund vs charge. This is late refund after charge receivable",
    ctor="zp",
)
_pair_from(
    "samsung-pay-vs-pan",
    "spay-after-pan",
    "ss_pay",
    "ss_late",
    "spay",
    "Samsung Pay token",
    "Samsung Pay token",
    "dpan_id",
    "spay_id",
    "samsung_pay|dpan|mst",
    "late_spay|pan_charged|recv_ss",
    "r174 apple DPAS; r175 Click to Pay. This is dpan_id Samsung Pay vs PAN",
    "r198 Samsung Pay vs PAN. This is late token after PAN charged receivable",
    ctor="ss",
)
_pair_from(
    "amex-safekey-vs-charge",
    "safekey-after-charge",
    "amex_sk",
    "amex_late",
    "safekey",
    "SafeKey result",
    "SafeKey result",
    "xid",
    "sk_id",
    "amex_safekey|aav|xid",
    "late_safekey|charge_posted|recv_sk",
    "r156 3DS challenge; r174 DPAS. This is xid SafeKey vs charge",
    "r199 SafeKey vs charge. This is late SafeKey after charge receivable",
    ctor="sk",
)
_pair_from(
    "discover-protectbuy-vs-auth",
    "protectbuy-after-auth",
    "disc_pb",
    "disc_late",
    "protectbuy",
    "ProtectBuy result",
    "ProtectBuy result",
    "acq_id",
    "pb_id",
    "protectbuy|discover_3ds|acqbin",
    "late_pb|auth_posted|recv_pb",
    "r199 SafeKey; r156 3DS. This is acq_id ProtectBuy vs auth",
    "r200 ProtectBuy vs auth. This is late ProtectBuy after auth receivable",
    ctor="pb",
)
_pair_from(
    "mc-moneysend-vs-funding",
    "moneysend-after-fund",
    "mc_ms",
    "mc_late",
    "moneysend",
    "MoneySend credit",
    "MoneySend credit",
    "trace_id",
    "ms_id",
    "moneysend|funding_source|ica",
    "late_ms|funding_posted|recv_ms",
    "r179 visa OCT; r189 NACHA. This is trace_id MoneySend vs funding",
    "r201 MoneySend vs funding. This is late MoneySend after funding receivable",
    ctor="ms",
)
_pair_from(
    "visa-afd-vs-fuel",
    "afd-after-fuel",
    "afd_fl",
    "afd_late",
    "afd",
    "AFD completion",
    "AFD completion",
    "pump_id",
    "afd_id",
    "visa_afd|fuel_preauth|pump",
    "late_afd|fuel_posted|recv_afd",
    "r167 hotel preauth; r161 remainder. This is pump_id AFD vs fuel preauth",
    "r202 AFD vs fuel. This is late AFD after fuel posted receivable",
    ctor="fl",
)
_pair_from(
    "amex-inquiry-vs-cb",
    "inquiry-after-cb",
    "amex_iq",
    "ainq_late",
    "amexinq",
    "Amex inquiry",
    "Amex inquiry",
    "case_id",
    "inq_id",
    "amex_inquiry|chargeback|se_number",
    "late_inq|cb_posted|recv_inq",
    "r185 RFI; r188 TC40. This is case_id Amex inquiry vs chargeback",
    "r203 Amex inquiry vs CB. This is late inquiry after CB receivable",
    ctor="iq",
)
_pair_from(
    "safe-vs-dispute",
    "safe-after-dispute",
    "safe_ds",
    "safe_late",
    "safe",
    "SAFE report",
    "SAFE report",
    "ref_id",
    "safe_id",
    "mastercard_safe|fraud_report|ref_id",
    "late_safe|dispute_posted|recv_safe",
    "r188 TC40; r203 Amex inquiry. This is ref_id SAFE vs dispute",
    "r204 SAFE vs dispute. This is late SAFE after dispute receivable",
    ctor="sf",
)
_pair_from(
    "tab-close-vs-auth",
    "close-after-tab",
    "tab_cls",
    "tab_late",
    "tab",
    "tab close",
    "tab close",
    "tab_id",
    "close_id",
    "tab_close|open_tab|preauth",
    "late_tab|tab_authed|recv_tab",
    "r167 hotel folio; r202 AFD. This is tab_id close vs open-tab auth",
    "r205 tab close vs auth. This is late close after auth receivable",
    ctor="tb",
)
_pair_from(
    "parking-extend-vs-start",
    "extend-after-start",
    "park_ex",
    "park_late",
    "park",
    "parking extend",
    "parking extend",
    "session_id",
    "extend_id",
    "parking_extend|session_start|bay",
    "late_extend|start_billed|recv_park",
    "r171 ev stop vs start; r170 transit. This is session_id parking extend vs start",
    "r206 parking extend vs start. This is late extend after start billed receivable",
    ctor="pk",
)
_pair_from(
    "telecom-topup-vs-reverse",
    "topup-after-reverse",
    "tel_top",
    "tel_late",
    "telco",
    "airtime topup",
    "airtime topup",
    "msisdn_id",
    "topup_id",
    "airtime_topup|reverse|msisdn",
    "late_topup|reversed|recv_tel",
    "r164 store credit; r165 loyalty. This is msisdn_id topup vs reverse",
    "r207 telecom topup vs reverse. This is late topup after reverse receivable",
    ctor="tl",
)
_pair_from(
    "invoice-factor-vs-pay",
    "factor-after-pay",
    "inv_fac",
    "inv_late",
    "factor",
    "invoice factor",
    "invoice factor",
    "invoice_id",
    "factor_id",
    "invoice_factor|advance|debtor",
    "late_factor|paid_invoice|recv_fac",
    "r177 dunning; r184 usage. This is invoice_id factor vs pay",
    "r208 invoice factor vs pay. This is late factor after pay receivable",
    ctor="fc",
)
_pair_from(
    "trial-convert-vs-cancel",
    "convert-after-cancel",
    "trl_cv",
    "trl_late",
    "trial",
    "trial convert",
    "trial convert",
    "sub_id",
    "convert_id",
    "trial_convert|trial_cancel|sub_id",
    "late_convert|cancelled|recv_trl",
    "r184 usage overage; r177 dunning. This is sub_id trial convert vs cancel",
    "r209 trial convert vs cancel. This is late convert after cancel receivable",
    ctor="cv",
)
_pair_from(
    "subscription-prorate-vs-invoice",
    "prorate-after-invoice",
    "sub_pro",
    "sub_late",
    "prorate",
    "proration",
    "proration",
    "sub_id",
    "prorate_id",
    "subscription_prorate|plan_change|invoice",
    "late_prorate|invoice_posted|recv_pro",
    "r209 trial convert; r184 usage. This is sub_id prorate vs invoice",
    "r210 prorate vs invoice. This is late prorate after invoice receivable",
    ctor="pr",
)
