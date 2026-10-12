#!/usr/bin/env python3
"""The JSON-schema subset that validates tool arguments and checks tool schemas."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))

from tool_world import schema_lite

TYPE_SAMPLES = {
    "object": {"k": 1},
    "string": "s",
    "integer": 3,
    "number": 2.5,
    "boolean": True,
    "array": [1],
    "null": None,
}


def foreign_samples(declared: str) -> list[tuple[str, object]]:
    """The sample values a ``declared`` type must refuse; a number also accepts an integer."""
    accepted = {declared, "integer"} if declared == "number" else {declared}
    return [(other, value) for other, value in TYPE_SAMPLES.items() if other not in accepted]


class SchemaLite(unittest.TestCase):
    def test_every_supported_type_accepts_its_values_and_refuses_the_others(self):
        for declared, value in TYPE_SAMPLES.items():
            with self.subTest(type=declared):
                self.assertEqual(schema_lite.validate_args({"type": declared}, value), [])
                for other, foreign in foreign_samples(declared):
                    findings = schema_lite.validate_args({"type": declared}, foreign)
                    self.assertEqual(len(findings), 1, (declared, other, findings))
                    self.assertTrue(findings[0].startswith(f"args: expected {declared}, got "))

    def test_a_bool_is_never_an_integer_or_a_number(self):
        self.assertEqual(
            schema_lite.validate_args({"type": "integer"}, True),
            ["args: expected integer, got bool"],
        )
        self.assertEqual(
            schema_lite.validate_args({"type": "number"}, False),
            ["args: expected number, got bool"],
        )
        self.assertEqual(schema_lite.validate_args({"type": "number"}, 7), [])
        self.assertEqual(
            schema_lite.validate_args({"type": "integer"}, 7.0),
            ["args: expected integer, got float"],
        )

    def test_required_properties_bounds_enum_and_min_length(self):
        schema = {
            "type": "object",
            "required": ["name", "count"],
            "properties": {
                "name": {"type": "string", "minLength": 2, "description": "ignored"},
                "count": {"type": "integer", "minimum": 1, "maximum": 5},
                "mode": {"enum": ["fast", "slow"]},
            },
        }
        self.assertEqual(
            schema_lite.validate_args(schema, {"name": "ok", "count": 3, "mode": "fast"}), []
        )
        self.assertEqual(
            schema_lite.validate_args(schema, {"name": "x", "count": 0, "mode": "warp"}),
            [
                "args.name: must be at least 2 characters",
                "args.count: must be at least 1",
                "args.mode: must be one of ['fast', 'slow']",
            ],
        )
        self.assertEqual(
            schema_lite.validate_args(schema, {"count": 9}),
            ["args: missing required property 'name'", "args.count: must be at most 5"],
        )

    def test_additional_properties_false_names_every_stray_key(self):
        schema = {"type": "object", "properties": {"path": {"type": "string"}}}
        self.assertEqual(schema_lite.validate_args(schema, {"path": "a", "extra": 1}), [])
        strict = dict(schema, additionalProperties=False)
        self.assertEqual(
            schema_lite.validate_args(strict, {"path": "a", "extra": 1, "more": 2}),
            ["args: unexpected property 'extra'", "args: unexpected property 'more'"],
        )

    def test_nested_items_are_validated_with_their_index_in_the_path(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["k"],
                "properties": {"k": {"type": "integer", "minimum": 1}},
                "additionalProperties": False,
            },
        }
        self.assertEqual(schema_lite.validate_args(schema, [{"k": 1}, {"k": 2}]), [])
        self.assertEqual(
            schema_lite.validate_args(schema, [{"k": 0}, {"x": 1}, "s"]),
            [
                "args[0].k: must be at least 1",
                "args[1]: missing required property 'k'",
                "args[1]: unexpected property 'x'",
                "args[2]: expected object, got str",
            ],
        )
        self.assertEqual(schema_lite.validate_args({"type": "array"}, ["anything"]), [])

    def test_a_type_mismatch_short_circuits_the_other_findings(self):
        schema = {"type": "object", "required": ["k"], "enum": [{"k": 1}]}
        self.assertEqual(schema_lite.validate_args(schema, 5), ["args: expected object, got int"])

    def test_check_schema_names_unsupported_keywords_and_types_by_path(self):
        schema = {
            "type": "object",
            "pattern": "x",
            "properties": {
                "a": {"type": "decimal"},
                "b": {"type": "array", "items": {"oneOf": []}},
            },
        }
        self.assertEqual(
            schema_lite.check_schema(schema),
            [
                "schema: unsupported keyword 'pattern'",
                "schema.a: unsupported type 'decimal'",
                "schema.b.items: unsupported keyword 'oneOf'",
            ],
        )
        self.assertEqual(schema_lite.check_schema([], "where"), ["where: schema must be an object"])
        self.assertEqual(
            schema_lite.check_schema({"properties": []}), ["schema: properties must be an object"]
        )
        self.assertEqual(
            schema_lite.check_schema(
                {
                    key: None
                    for key in schema_lite.SUPPORTED_KEYWORDS - {"properties", "items", "type"}
                }
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
