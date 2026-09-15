#!/usr/bin/env python3
"""AST-extracted r2535 proto2×WKT leftover catalog (legacy-mill-lane pbc-mill-r2535.py)."""

from __future__ import annotations

from .plant_type import ENUM_MODE, ty

MILL_ID = "pbc_r2535"
CATALOG_FIRST = 2535
START = 2535
N_ROUNDS = 90
NOTES_EXTRA = (
    ", not r1334 map-value-bool-to-sint32 / map-value-bool-to-sint64, "
    "not r987 enum-to-fixed64-mode / bytes-to-fixed64-hash, "
    "not r787–r2534 leftover clones, not r1335 bytesvalue-to-listvalue / "
    "bytesvalue-to-nullvalue wrapper leftovers"
)
NOTES_FOOTER = (
    "- Contract evidence: protobuf wire incompatibility on field tag; "
    "additive migration reserves the number; verify compatible check after "
    "restore.\n"
)

LANGC = {'Go': 'GO', 'Python': 'PY', 'Java': 'JAVA', 'Rust': 'RUST', 'Kotlin': 'KT', 'TypeScript': 'TS', 'C++': 'CXX', 'Swift': 'SWIFT', 'Dart': 'DART', 'C#': 'CS'}
LANGS = list(LANGC)

BANNED_SLUGS = {'map-key-fixed32', 'field-presence-implicit-override', 'map-key-i32-to-i64', 'map-key-bool-to-str', 'map4-str-to-u64', 'field-presence-explicit', 'ed2023-legacy-required', 'optional4-peak-hasfield', 'optional-bytes-drop', 'optional-enum-quench-drop', 'optional-msg-tuyere-drop', 'map-key-uint32-to-int32', 'enum-to-fixed64-mode', 'bytes-to-fixed64-hash', 'map-value-bool-to-sint32', 'map-value-bool-to-sint64', 'bytesvalue-to-listvalue', 'oneof-bytesvalue-to-listvalue', 'bytesvalue-to-nullvalue', 'oneof-bytesvalue-to-nullvalue'}
BANNED_NEEDLES = ('map-key-fixed32', 'field-presence-implicit', 'map-key-i32-to-i64', 'map-key-bool-to-str', 'map4-str-to-u64', 'field-presence-explicit', 'legacy-required', 'optional4-peak', 'optional-bytes-drop', 'optional-enum-quench', 'optional-msg-tuyere', 'enum-to-fixed64-mode', 'bytes-to-fixed64-hash', 'bytesvalue-to-listvalue', 'bytesvalue-to-nullvalue')

WKT_DESTS: list[tuple[str, str, str]] = [('timestamp', 'google.protobuf.Timestamp', 'LEN Timestamp seconds/nanos'), ('duration', 'google.protobuf.Duration', 'LEN Duration seconds/nanos'), ('empty', 'google.protobuf.Empty', 'LEN Empty 0-length'), ('any', 'google.protobuf.Any', 'LEN Any type_url+value'), ('struct', 'google.protobuf.Struct', 'LEN Struct fields map'), ('enum', 'Mode', 'VARINT enum Mode')]

P2_TYPES = [('int32', 'VARINT int32', 'tap_n'), ('int64', 'VARINT int64', 'seq'), ('uint32', 'unsigned VARINT 32', 'port'), ('uint64', 'unsigned VARINT 64', 'hash'), ('sint32', 'zigzag VARINT 32', 'delta'), ('sint64', 'zigzag VARINT 64', 'delta'), ('fixed32', 'FIXED32 unsigned', 'crc'), ('fixed64', 'FIXED64 unsigned', 'hash'), ('sfixed32', 'FIXED32 signed', 'crc'), ('sfixed64', 'FIXED64 signed', 'hash'), ('float', 'FIXED32 float', 'temp_c'), ('double', 'FIXED64 double', 'peak'), ('bool', 'VARINT 0/1', 'armed'), ('string', 'LEN utf8', 'sku'), ('bytes', 'LEN bytes', 'blob')]

def _guard(spec: dict) -> None:
    slug = spec['slug']
    if slug in BANNED_SLUGS:
        raise ValueError(f'banned slug {slug!r}')
    if slug.startswith('map-key-'):
        raise ValueError(f'map-key type swap banned this mill: {slug!r}')
    identity = ' '.join((str(spec.get(k, '')) for k in ('slug', 'short', 'decl_old', 'decl_new', 'buf_rule'))).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise ValueError(f'banned needle {needle!r} in {identity!r}')

def _extras_for(slug: str, told: str, tnew: str, field: str, num: int) -> dict:
    extra: dict = {'field_num': num}
    if 'Mode' in (told, tnew) or slug.endswith('-enum') or '-to-enum' in slug:
        extra['extra_msgs'] = ENUM_MODE
        extra.setdefault('grep_pat', f'{told} {field}|{tnew} {field}')
    if slug.startswith('proto2-required-'):
        extra['syntax'] = 'syntax = "proto2";'
        extra['decl_old'] = f'required {told} {field} = {num};'
        extra['decl_new'] = f'required {tnew} {field} = {num};'
        extra['grep_pat'] = f'required {told} {field}|required {tnew} {field}'
        extra['buf_rule'] = 'FIELD_TYPE / WIRE'
    if slug.startswith('proto2-optional-'):
        extra['syntax'] = 'syntax = "proto2";'
        extra['decl_old'] = f'optional {told} {field} = {num};'
        extra['decl_new'] = f'optional {tnew} {field} = {num};'
        extra['grep_pat'] = f'optional {told} {field}|optional {tnew} {field}'
        extra['buf_rule'] = 'FIELD_TYPE / WIRE'
    imports: list[str] = []

    def add(path: str) -> None:
        if path not in imports:
            imports.append(path)
    blob = f'{told} {tnew} {slug}'
    pairs = (('google.protobuf.Timestamp', 'google/protobuf/timestamp.proto'), ('google.protobuf.Duration', 'google/protobuf/duration.proto'), ('google.protobuf.Any', 'google/protobuf/any.proto'), ('google.protobuf.Empty', 'google/protobuf/empty.proto'))
    for needle, path in pairs:
        if needle in blob:
            add(path)
    if 'google.protobuf.Struct' in blob:
        add('google/protobuf/struct.proto')
    if imports:
        extra['imports'] = tuple(imports)
    return extra

def _mk(slug: str, short: str, told: str, tnew: str, field: str, num: int, wold: str, wnew: str, lang: str, vs: str, avoid: str) -> dict:
    extra = _extras_for(slug, told, tnew, field, num)
    ticket = f'{LANGC[lang]}-{short.upper()}-{num}'
    return ty(slug, short, told, tnew, field, num, wold, wnew, lang, ticket, vs, avoid, **extra)

def _build_plants() -> list[dict]:
    plants: list[dict] = []
    seen_slug: set[str] = set()
    n = 0
    num = 61

    def push(slug: str, told: str, tnew: str, field: str, wold: str, wnew: str, vs: str) -> None:
        nonlocal n, num
        if slug in seen_slug:
            return
        short = f'z{n:04d}'
        lang = LANGS[n % len(LANGS)]
        plant = _mk(slug, short, told, tnew, field, num, wold, wnew, lang, vs, 'map-key ban / r787 leftover / r1334 map-value-bool-to-sint32 / r1335 wrapper leftover')
        _guard(plant)
        plants.append(plant)
        seen_slug.add(slug)
        n += 1
        num += 1
    for told, wold, field in P2_TYPES:
        for dest_tag, tnew, wnew in WKT_DESTS:
            if told == tnew:
                continue
            vs = f'proto2 {told}→{dest_tag} TYPE (r1335 skipped WKT dest; not optional/required drop)'
            push(f'proto2-required-{told}-to-{dest_tag}', told, tnew, field, wold, wnew, vs)
            push(f'proto2-optional-{told}-to-{dest_tag}', told, tnew, field, wold, wnew, vs)
    if len(plants) % 2:
        plants.pop()
    if not plants:
        raise ValueError('no plants for r2535 mill')
    return plants

def stamp_envelope(rec: dict, plant: dict) -> None:
    """Ordered contract evidence: proto/wire → field/tag → additive/reserve → verify/check."""
    num = plant.get('field_num', '')
    by_n = {int(step['n']): step for step in rec['steps']}
    if 5 in by_n:
        by_n[5]['observation'] = str(by_n[5]['observation']).rstrip() + f' Semantic incompatibility: protobuf field tag {num} wire type changed.'
    restore_n = 12 if rec['reward'].get('success') else 11
    verify_n = restore_n + 1
    if restore_n in by_n:
        by_n[restore_n]['observation'] = str(by_n[restore_n]['observation']).rstrip() + f' Additive migration restores {plant['decl_old']} and reserve tag {num} (never reuse).'
    if verify_n in by_n:
        by_n[verify_n]['observation'] = str(by_n[verify_n]['observation']).rstrip() + ' verify compatible check: buf WIRE 0 after additive restore.'
    rec['outcome'] = str(rec.get('outcome') or '').rstrip() + ' Compatibility rule: FIELD_TYPE / WIRE; additive migration reserved the tag.'

_PLANTS = _build_plants()
if len(_PLANTS) % 2:
    raise ValueError(f"odd plant count {len(_PLANTS)}")
PAIRS: tuple[tuple[dict, dict], ...] = tuple(
    (_PLANTS[i], _PLANTS[i + 1]) for i in range(0, len(_PLANTS), 2)
)
if len(PAIRS) != N_ROUNDS:
    raise ValueError(f"r2535 pair count {len(PAIRS)} != {N_ROUNDS}")
