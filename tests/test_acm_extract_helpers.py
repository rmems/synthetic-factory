"""ACM AST-extract helpers: literal env, plant calls, PAIRS/MILLS tables, merge, row checks."""

from __future__ import annotations

import ast
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from pipelines.acm import catalog, generate


def _module(source: str) -> ast.Module:
    return ast.parse(textwrap.dedent(source))


def _expr(source: str) -> ast.expr:
    return ast.parse(source, mode="eval").body


def _extract(files: dict[str, str]) -> dict:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, source in files.items():
            (root / name).write_text(textwrap.dedent(source), encoding="utf-8")
        return generate.extract_tree(root)


class ModuleEnv(unittest.TestCase):
    def test_constants_then_resolved_names_in_source_order(self):
        env = generate.module_env(_module(
            """
            HOST = "api.example"
            PORT = 8443
            LIVE = True
            RATIO = 1.5
            URL = f"https://{HOST}:{PORT}/v1"
            LATE = PREFIX + "-x"
            PREFIX = "acm"
            AFTER = PREFIX + "-y"
            """
        ))
        self.assertEqual(
            env,
            {
                "HOST": "api.example", "PORT": 8443, "LIVE": True, "PREFIX": "acm",
                "URL": "https://api.example:8443/v1", "LATE": "acm-x", "AFTER": "acm-y",
            },
        )

    def test_a_constant_wins_over_a_later_computed_assignment(self):
        env = generate.module_env(_module('NAME = "first"\nNAME = OTHER + "x"\nOTHER = "o"\n'))
        self.assertEqual(env, {"NAME": "first", "OTHER": "o"})

    def test_last_constant_assignment_wins(self):
        self.assertEqual(generate.module_env(_module("A = 'x'\nA = 'y'\n")), {"A": "y"})

    def test_non_simple_and_unresolved_assignments_are_skipped(self):
        env = generate.module_env(_module(
            """
            A, B = "x", "y"
            C = D = "z"
            E: str
            F: str = "annotated"
            obj.attr = "nope"
            G = undefined_name
            H = "a" - "b"
            I = 3.5 + 1
            J = ("t",)
            """
        ))
        self.assertEqual(env, {"F": "annotated"})

    def test_a_tree_without_a_body_has_an_empty_env(self):
        self.assertEqual(generate.module_env(_expr("1")), {})


def _plant_kwargs_of(source: str, env: dict | None = None):
    return generate.plant_kwargs(_expr(source), env or {})


class PlantKwargs(unittest.TestCase):
    def test_non_plant_calls_are_none(self):
        for source in ("x", "plant", "mod.plant(slug='s')", "other(slug='s')", "(lambda: 1)()"):
            with self.subTest(source=source):
                self.assertIsNone(_plant_kwargs_of(source))

    def test_known_fields_resolve_and_unknown_or_unresolved_are_dropped(self):
        out = _plant_kwargs_of(
            "plant(slug=S, field='f', old=f'{V}1', extra='no', new=missing, **more)",
            {"S": "s-1", "V": "v"},
        )
        self.assertEqual(out, {"slug": "s-1", "field": "f", "old": "v1"})

    def test_ok_and_bad_imply_success_unless_given(self):
        cases = (
            ("ok(slug='a')", True),
            ("bad(slug='a')", False),
            ("ok(slug='a', success=False)", False),
            ("bad(slug='a', success=True)", True),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertIs(_plant_kwargs_of(source)["success"], expected)
        for source in ("p(slug='a')", "plant(slug='a')"):
            with self.subTest(source=source):
                self.assertNotIn("success", _plant_kwargs_of(source))

    def test_a_missing_empty_or_non_text_slug_is_none(self):
        for source in ("plant(field='f')", "plant(slug='')", "plant(slug=3)", "ok(slug=None)"):
            with self.subTest(source=source):
                self.assertIsNone(_plant_kwargs_of(source))

    def test_pair_elts_needs_a_two_tuple_of_plant_calls(self):
        self.assertEqual(
            generate.pair_elts(_expr("(ok(slug='a'), bad(slug='b'))"), {}),
            ({"slug": "a", "success": True}, {"slug": "b", "success": False}),
        )
        for source in ("[ok(slug='a'), bad(slug='b')]", "(ok(slug='a'),)",
                       "(ok(slug='a'), bad(field='f'))", "(ok(field='f'), bad(slug='b'))"):
            with self.subTest(source=source):
                self.assertIsNone(generate.pair_elts(_expr(source), {}))


class MillsTables(unittest.TestCase):
    def test_dict_literal_and_int_subscript_assignments(self):
        tables = generate._mills_tables(_module(
            """
            BASE = 7
            MILLS = {1: [("s1", "f1", "fld", "o", "n")], "x": [], 2: "nope", **extra}
            MILLS[3] = [P("s3", "f3", "fld", "o", "n", "E", "u1", "", "u2"), ("", "f", "a", "b", "c")]
            OTHER["k"] = [("s4", "f4", "fld", "o", "n")]
            OTHER[4] = ("s5", "f5")
            OTHER[5], X[6] = [("s6", "f6")], []
            MILLS[6] += [("s7", "f7")]
            X[7] = [("s7", "f7", "a", "b", "c"), Q("s9", "f9"), ["s10", "f10"]]
            """
        ), {"BASE": 7})
        self.assertEqual(
            tables,
            {
                1: [("s1", "f1", "fld", "o", "n")],
                3: [("s3", "f3", "fld", "o", "n", "E", "u1", "", "u2")],
                7: [("s7", "f7", "a", "b", "c")],
            },
        )

    def test_a_later_table_for_the_same_round_replaces_the_earlier_one(self):
        tables = generate._mills_tables(_module(
            'MILLS = {9: [("a", "b")]}\nMILLS[9] = [("c", "d")]\n'
        ), {})
        self.assertEqual(tables, {9: [("c", "d")]})


class ExtractTree(unittest.TestCase):
    def test_published_pairs_win_over_plant_gen_rows_and_rows_sort(self):
        payload = _extract({
            "acm-pairs-r10.py": """
                PAIRS = [
                    (ok(slug="pub-a", field="f", old="o", new="n"), bad(slug="pub-b")),
                    ("not", "a pair"),
                ]
                PAIRS = [(p(slug="pub-c", success=True), p(slug="pub-d"))]
                PAIRS = ("ignored",)
                BANNED_SLUG_NEEDLES = ("zz", NEEDLE)
                BANNED_BLOB = ["thought", 3]
                NEEDLE = "yy"
            """,
            "acm-pairs-g46-w2.py": "PAIRS = [(ok(slug='g-a'), bad(slug='g-b'))]\n",
            "acm-pairs-misc.py": "PAIRS = [(ok(slug='m-a'), bad(slug='m-b'))]\n",
            "_gen_acm_plants_r3.py": """
                MILLS = {
                    2: [("pub-a", "pub-b", "f", "o", "n"), ("gen-a", "gen-b", "f", "o", "n", "E")],
                    1: [("gen-c", "gen-d", "f", "o", "n", "E", "u1", "x", "u2")],
                }
            """,
            "acm-loop-r1.txt": "not python\n",
        })
        rows = [(row["catalog_id"], row["success_slug"], row["kind"]) for row in payload["rows"]]
        self.assertEqual(
            rows,
            [
                ("g46-w2", "g-a", "mill-pairs"),
                ("r1", "gen-c", "plant-gen"),
                ("r2", "gen-a", "plant-gen"),
                ("r10", "pub-a", "mill-pairs"),
                ("r10", "pub-c", "mill-pairs"),
                ("misc", "m-a", "mill-pairs"),
            ],
        )
        self.assertEqual(payload["bans"], {"blob_keys": ["thought"], "slug_needles": ["yy", "zz"]})
        gen_c = next((row for row in payload["rows"] if row["success_slug"] == "gen-c"), None)
        self.assertIsNotNone(gen_c)
        self.assertEqual(
            (gen_c["fail_err"], gen_c["fetch1"], gen_c["fetch2"]), ("E: leftover", "u1", "u2")
        )
        self.assertEqual(
            [(source["path"], source["kind"], source["pair_count"]) for source in payload["sources"]],
            [
                ("_gen_acm_plants_r3.py", "plant-gen", 3),
                ("acm-pairs-g46-w2.py", "mill", 1),
                ("acm-pairs-misc.py", "mill", 1),
                ("acm-pairs-r10.py", "mill", 2),
            ],
        )

    def test_short_mill_tuples_make_no_pair(self):
        payload = _extract({"_gen_acm_plants_r5.py": 'MILLS = {5: [("a", "b", "f", "o")]}\n'})
        self.assertEqual(payload["rows"], [])


class PlantFromMapping(unittest.TestCase):
    def test_falsy_values_become_empty_text(self):
        plant = catalog.plant_from_mapping(
            {"slug": 7, "domain": None, "success": 1, "field": 0, "old": "", "new": "n",
             "name": False, "fail_err": "e", "vs": [], "fetch1": "u1", "fetch2": 2}
        )
        self.assertEqual(
            plant,
            catalog.Plant(slug="7", domain="", success=True, field="", old="", new="n",
                          name="", fail_err="e", vs="", fetch1="u1", fetch2="2"),
        )

    def test_explicit_success_overrides_the_payload(self):
        overridden = catalog.plant_from_mapping({"slug": "s", "success": True}, success=False)
        self.assertIs(overridden.success, False)
        self.assertIs(catalog.plant_from_mapping({"slug": "s"}).success, False)

    def test_a_missing_slug_is_a_key_error(self):
        with self.assertRaises(KeyError):
            catalog.plant_from_mapping({"domain": "d"})


def _check_rows(rows):
    payload = {"factory": "api-contract-migration-factory", "family": "acm", "quota": 2,
               "steps": 16, "rows": rows}
    return catalog.check_catalog(payload)


class CheckRows(unittest.TestCase):
    def assert_refused(self, rows, message):
        with self.assertRaises(ValueError) as caught:
            _check_rows(rows)
        self.assertEqual(str(caught.exception), message)

    def test_valid_rows_pass(self):
        rows = [{"success_slug": "a", "fail_slug": "b"}, {"success_slug": "c", "fail_slug": "d"}]
        self.assertIsNone(_check_rows(rows))

    def test_each_row_refusal_in_check_order(self):
        cases = (
            (["row"], "catalog row is not an object"),
            ([{"success_slug": "a"}], "catalog row is missing slugs"),
            ([{"success_slug": 1, "fail_slug": "b"}], "catalog row is missing slugs"),
            ([{"success_slug": "a", "fail_slug": "a"}], "pair slugs are not distinct: a"),
            ([{"success_slug": "a", "fail_slug": "b"}, {"success_slug": "b", "fail_slug": "c"}],
             "duplicate slug b"),
            ([{"success_slug": "x-w131", "fail_slug": "b"}], "banned needle 'w131' in x-w131"),
            ([{"success_slug": "a", "fail_slug": "422-vs-400-207-multistatus"}],
             "banned needle '422-vs-400' in 422-vs-400-207-multistatus"),
            # The success slug is claimed (and its needles checked) before the fail slug.
            ([{"success_slug": "a-w131", "fail_slug": "a-w131-b"},
              {"success_slug": "a-w131", "fail_slug": "z"}], "banned needle 'w131' in a-w131"),
            ([{"success_slug": "a", "fail_slug": "b"}, {"success_slug": "a", "fail_slug": "x-w131"}],
             "duplicate slug a"),
        )
        for rows, message in cases:
            with self.subTest(message=message):
                self.assert_refused(rows, message)

    def test_dumps_rows_round_trips_through_load_rows(self):
        rows = [{"b": 1, "a": "é"}, {"c": [1, 2]}]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rows.jsonl"
            path.write_text(catalog.dumps_rows(rows), encoding="utf-8")
            self.assertEqual(catalog.load_rows(path), rows)
        self.assertEqual(catalog.dumps_rows([]), "")


def _stack_depth() -> int:
    depth, frame = 0, sys._getframe(1)
    while frame is not None:
        depth += 1
        frame = frame.f_back
    return depth


def _call_with_limit(headroom: int, call):
    """Run ``call`` with the recursion limit ``headroom`` frames above this frame."""
    previous = sys.getrecursionlimit()
    sys.setrecursionlimit(_stack_depth() + headroom)
    try:
        return call()
    finally:
        sys.setrecursionlimit(previous)


def _concat_chain(levels: int) -> ast.expr:
    node: ast.expr = ast.Constant("a")
    for _ in range(levels):
        node = ast.BinOp(left=node, op=ast.Add(), right=ast.Constant("a"))
    return node


def _fstring_chain(levels: int) -> ast.expr:
    node: ast.expr = ast.Constant("a")
    for _ in range(levels):
        node = ast.JoinedStr(values=[ast.FormattedValue(value=node, conversion=-1)])
    return node


class RecursionDepth(unittest.TestCase):
    """Nested ``+`` and f-string literals cost two frames per level, as on main.

    ``literal_value`` dispatches to ``_literal_add`` / ``_literal_joined``, which call
    ``literal_value`` again, so a 600-level literal needs ``2 * 600 + 2`` frames above the
    entry point. A refactor that adds or removes a frame per level moves the depth at which
    extraction raises ``RecursionError``; these tests pin it within a small slack.
    """

    LEVELS = 600
    FRAMES = 2 * LEVELS + 2
    SLACK = 50

    def assert_depth_pinned(self, call, expected):
        self.assertEqual(_call_with_limit(self.FRAMES + self.SLACK, call), expected)
        with self.assertRaises(RecursionError):
            _call_with_limit(self.FRAMES - self.SLACK, call)

    def test_module_env_resolves_a_600_level_concatenation(self):
        tree = ast.Module(
            body=[ast.Assign(targets=[ast.Name("DEEP")], value=_concat_chain(self.LEVELS))],
            type_ignores=[],
        )
        self.assert_depth_pinned(
            lambda: generate.module_env(tree), {"DEEP": "a" * (self.LEVELS + 1)}
        )

    def test_plant_kwargs_resolves_a_600_level_slug(self):
        call = ast.Call(
            func=ast.Name("plant"), args=[],
            keywords=[ast.keyword(arg="slug", value=_concat_chain(self.LEVELS))],
        )
        self.assert_depth_pinned(
            lambda: generate.plant_kwargs(call, {}), {"slug": "a" * (self.LEVELS + 1)}
        )

    def test_literal_value_resolves_a_600_level_fstring(self):
        node = _fstring_chain(self.LEVELS)
        self.assert_depth_pinned(lambda: generate.literal_value(node, {}), "a")


if __name__ == "__main__":
    unittest.main()
