#!/usr/bin/env python3
"""Tiny leftover pair catalog used only as AST-extract input in tests."""


def _dynamic_plant() -> str:
    return "non-literal-prod"


def pair(**kwargs: str) -> dict:
    return kwargs


PAIRS = [
    pair(
        plant="fixture-prod",
        app="fixture-api",
        chart="1.0.0",
        slug="fixture-leftover-field",
        field="spec.fixtureField",
        fail_val="old",
        fix_val="new",
        hide_path="hideKnob",
        hide_old="hideKnob: false\n",
        hide_new="hideKnob: true\n",
        values_fail="fixtureField: old\nhideKnob: false\n",
        values_fix="fixtureField: new\nhideKnob: false\n",
        tpl="  fixtureField: {{ .Values.fixtureField }}\n",
        log="CrashLoop leftover spec.fixtureField old",
        live_ok="spec.fixtureField=new",
        hide_name="hideKnob true",
        new_vs="fixtureField leftover, not hideKnob leftover",
        seed="leftover spec.fixtureField old",
        n2="replica n2 still spec.fixtureField old after git new",
        ci="# spec.fixtureField must be new.",
        handoff="LEFTOVER: replica n2 still spec.fixtureField old.",
        pytest_ok="test_fix\ntest_not_hide\ntest_not_clone\ntest_pods_ready\ntest_no_force\ntest_field",
        pytest_fail="test_fix_all FAILED b==old",
        tmpl_test="test_template_matches_git",
        rs="k1",
    ),
    pair(
        plant=_dynamic_plant(),
        app="skip-api",
        chart="0.0.0",
        slug="non-literal-skipped",
        field="spec.skip",
        fail_val="old",
        fix_val="new",
        hide_path="hide",
        hide_old="hide: false\n",
        hide_new="hide: true\n",
        values_fail="skip: old\nhide: false\n",
        values_fix="skip: new\nhide: false\n",
        tpl="  skip: {{ .Values.skip }}\n",
        log="skip",
        live_ok="ok",
        hide_name="hide true",
        new_vs="skip",
        seed="skip",
        n2="skip n2",
        ci="# skip",
        handoff="skip",
        pytest_ok="test_skip",
        pytest_fail="test_skip FAILED",
        tmpl_test="test_skip",
        rs="k0",
    ),
]
