#!/usr/bin/env python3
"""AST-extracted r787 ty() wrapper and enum/message fragments."""

from __future__ import annotations

from .record_builder import plant

ENUM_GRADE = 'enum Grade { GRADE_UNSPECIFIED = 0; GRADE_A = 1; GRADE_B = 2; }\n'
ENUM_MODE = 'enum Mode { MODE_UNSPECIFIED = 0; MODE_LIVE = 1; MODE_IDLE = 2; }\n'
ENUM_STATE = 'enum State { STATE_UNSPECIFIED = 0; STATE_HOT = 1; }\n'
MSG_NOTE = 'message Note { string text = 1; int32 pri = 2; }\n'
MSG_BLOB = 'message Blob { bytes raw = 1; }\n'
MSG_EVT = 'message Evt { string kind = 1; }\n'

def ty(slug: str, short: str, told: str, tnew: str, field: str, num: int, wold: str, wnew: str, lang: str, ticket: str, vs: str, avoid: str, **extra: object) -> dict:
    syntax = str(extra.pop('syntax', 'syntax = "proto3";'))
    buf_rule = str(extra.pop('buf_rule', 'FIELD_TYPE / WIRE'))
    freeze = str(extra.pop('freeze', f'{lang} freeze {told} vs {tnew} on {field}'))
    json_name = str(extra.pop('json_name', field + 'X'))
    debug = str(extra.pop('debug', 'debug_' + short))
    compat = str(extra.pop('compat', f'Dual-read {field} as {told} or {tnew}'))
    grep_pat = str(extra.pop('grep_pat', f'{told} {field}|{tnew} {field}'))
    goal_bit = str(extra.pop('goal_bit', f'{told} {field}={num} → {tnew} so freeze {wold} fails'))
    dead_desc = str(extra.pop('dead_desc', f'json_name {json_name} as a wire/type substitute'))
    decl_old = str(extra.pop('decl_old', f'{told} {field} = {num};'))
    decl_new = str(extra.pop('decl_new', f'{tnew} {field} = {num};'))
    return plant(slug=slug, short=short, decl_old=decl_old, decl_new=decl_new, syntax=syntax, buf_rule=buf_rule, wire_old=wold, wire_new=wnew, freeze=freeze, ticket=ticket, lang=lang, vs=vs, avoid=avoid, json_name=json_name, debug=debug, compat=compat, grep_pat=grep_pat, goal_bit=goal_bit, dead_desc=dead_desc, **extra)
