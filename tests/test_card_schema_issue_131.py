#!/usr/bin/env python3
"""Issue #71 leaf tests for the per-dataset card schema declaration."""

import test_card_schema as _shared

unittest = _shared.unittest
io = _shared.io
json = _shared.json
tempfile = _shared.tempfile
redirect_stderr = _shared.redirect_stderr
redirect_stdout = _shared.redirect_stdout
Path = _shared.Path
mock = _shared.mock
REPO = _shared.REPO
card_schema = _shared.card_schema
publisher = _shared.publisher
LONG_HORIZON = _shared.LONG_HORIZON
MINIMAL = _shared.MINIMAL
write_declaration = _shared.write_declaration


RAG_RETRIEVAL_DEBUG = "rag-retrieval-debug-trajectories"
RAG_RETRIEVAL_DEBUG_MIRROR = (
    Path.home()
    / "rmems"
    / "hf"
    / "grok-4.6"
    / RAG_RETRIEVAL_DEBUG
    / "data"
    / "raw"
)


class RagRetrievalDebugDeclarationTests(unittest.TestCase):
    """Issue #71: episode-only top-level extras against an otherwise thin record."""

    EVH_IDS = [
        "evh-r21-cite-orphan-c3e8",
        "evh-r21-hybrid-sku-a91b",
        "evh-r22-rerank-pad-d7f2",
        "evh-r22-ragas-param-b4c1",
        "evh-r23-embed-mismatch-e5a0",
        "evh-r23-tenant-filter-f2c9",
        "evh-r24-table-split-a8d3",
        "evh-r24-mmr-drop-b7e1",
        "evh-r25-stale-alias-c4b2",
        "evh-r25-compress-numeral-d9aa",
        "evh-r26-parent-cite-e1f6",
        "evh-r26-hnsw-ef-f8c0",
        "evh-r27-cohere-topn-a6b8",
        "evh-r27-recency-bury-c2d4",
        "evh-r28-lost-middle-g3a1",
        "evh-r28-weaviate-cert-h4b2",
        "evh-r29-history-embed-j5c3",
        "evh-r29-pinecone-ns-k6d4",
    ]

    def setUp(self):
        self.declaration = card_schema.load(RAG_RETRIEVAL_DEBUG)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #71")
        slug = "rag-retrieval-debug-factory"
        blurb, extra_tags = publisher.META[slug]
        tags = [
            "synthetic-data",
            "agentic-workflows",
            "grok-4.6",
            "provenance",
            "trajectories",
            *extra_tags,
        ]
        self.item = {
            "slug": slug,
            "hub": publisher.hub_name(slug),
            "pretty": publisher.pretty_name(RAG_RETRIEVAL_DEBUG),
            "blurb": blurb,
            "tags": list(dict.fromkeys(tags)),
        }
        self.assertEqual(self.item["hub"], RAG_RETRIEVAL_DEBUG)
        self.card = publisher.render_card(
            self.item,
            records=1876,
            bytes_=10831457,
            first="r01",
            last="r938",
            payload_names=[f"batch-r{n:02d}.jsonl" for n in range(1, 939)],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        self.assertEqual(self.declaration["issues"], [71])
        self.assertEqual(
            [feature["name"] for feature in self.declaration["features"]],
            [
                "id",
                "goal",
                "plan",
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps",
                "outcome",
                "reward",
                "meta",
            ],
        )
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        # `plan` is a string on all 1876 records here, unlike issue #36's dataset.
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertNotIn("optional", names["plan"])
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        self.assertEqual(steps["n"]["dtype"], "int64")
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(
            card_schema.yaml_features(self.declaration["features"]),
            [
                {"name": "id", "dtype": "string"},
                {"name": "goal", "dtype": "string"},
                {"name": "plan", "dtype": "string"},
                {"name": "error_introduced", "dtype": "json"},
                {"name": "propagation", "dtype": "json"},
                {"name": "diagnosis", "dtype": "json"},
                {"name": "recovery", "dtype": "json"},
                {"name": "verification", "dtype": "json"},
                {
                    "name": "steps",
                    "list": [
                        {"name": "n", "dtype": "int64"},
                        {"name": "decision_basis", "dtype": "string"},
                        {
                            "name": "tool_call",
                            "struct": [
                                {"name": "name", "dtype": "string"},
                                {"name": "args", "dtype": "json"},
                            ],
                        },
                        {"name": "observation", "dtype": "string"},
                        {"name": "reflection", "dtype": "string"},
                    ],
                },
                {"name": "outcome", "dtype": "string"},
                {"name": "reward", "dtype": "json"},
                {"name": "meta", "dtype": "json"},
            ],
        )

    def test_episode_only_extras_are_optional_json_columns(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        expected = [
            "error_introduced",
            "propagation",
            "diagnosis",
            "recovery",
            "verification",
        ]
        for field in expected:
            with self.subTest(field=field):
                feature = names[field]
                self.assertTrue(feature["optional"])
                self.assertEqual(feature["dtype"], "json")
                self.assertRegex(
                    feature["note"],
                    r"observed snapshot through round 938: present on 76 of 1876 records",
                )
                self.assertRegex(feature["note"], r"(?:drift|cast failure)")

    def test_json_columns_include_episode_objects_and_key_bags(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            [
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
                "steps[].tool_call.args",
                "reward",
                "meta",
            ],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("  - name: error_introduced\n    dtype: json\n", front_matter)
        self.assertIn("  - name: propagation\n    dtype: json\n", front_matter)
        self.assertNotIn("optional", front_matter)
        self.assertNotIn("note:", front_matter)
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_eighteen_dest_stamped_mill_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        disclosure = self.declaration["disclosures"][0]
        self.assertEqual(disclosure["ids"], self.EVH_IDS)
        self.assertEqual(len(disclosure["ids"]), 18)
        for record_id in self.EVH_IDS:
            self.assertIn(f"`{record_id}`", self.card)
        self.assertIn("issues/43", self.card)
        self.assertIn("| `error_introduced` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        # The third, unowned `sir-*` class is absent here and says so.
        self.assertIn("No unowned third leftover class is present here.", self.card)

    @unittest.skipUnless(
        RAG_RETRIEVAL_DEBUG_MIRROR.is_dir(),
        "read-only published mirror is not available",
    )
    def test_published_mirror_matches_the_snapshot_claims(self):
        payloads = sorted(RAG_RETRIEVAL_DEBUG_MIRROR.glob("batch-*.jsonl"))
        self.assertEqual(len(payloads), 938)
        records = 0
        extra_counts = {
            name: 0
            for name in (
                "error_introduced",
                "propagation",
                "diagnosis",
                "recovery",
                "verification",
            )
        }
        evh_ids = set()
        for payload in payloads:
            with payload.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    plan = record.get("plan")
                    self.assertIsInstance(plan, str, f"{payload.name}:{line_number}")
                    self.assertTrue(plan.strip(), f"{payload.name}:{line_number}")
                    for name in extra_counts:
                        extra_counts[name] += name in record
                    if record["id"].startswith("evh-"):
                        evh_ids.add(record["id"])
                    records += 1

        self.assertEqual(records, 1876)
        self.assertEqual(set(extra_counts.values()), {76})
        self.assertEqual(evh_ids, set(self.EVH_IDS))


if __name__ == "__main__":
    unittest.main()
