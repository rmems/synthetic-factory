"""The vendored eval denylist / do-not-train policy loads strictly and matches whole values (#494)."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
import eval_exclusion_aliases as aliases  # noqa: E402
import eval_exclusion_lists as lists  # noqa: E402
import eval_exclusion_policy as policy  # noqa: E402
import repo_identity  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures" / "eval-exclusion"
FIXTURE_PATHS = (
    FIXTURES / "eval-denylist.json",
    FIXTURES / "do-not-train.json",
    FIXTURES / "repo-aliases.json",
)


def fixture_policy():
    return policy.load_policy(*FIXTURE_PATHS)


def _document(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RepoIdentityTests(unittest.TestCase):
    def test_canonical_form_is_the_lowercased_owner_and_name(self):
        self.assertEqual(repo_identity.canonical_repo("TheAlgorithms/Python"), "thealgorithms/python")
        self.assertEqual(repo_identity.canonical_repo("clap-rs/clap"), "clap-rs/clap")
        self.assertTrue(repo_identity.is_canonical_repo("rmems/thalamic-relay.v2_x"))
        self.assertFalse(repo_identity.is_canonical_repo("Rmems/thalamic-relay"))

    def test_malformed_names_are_refused_not_repaired(self):
        for value in (
            "", "rmems", "rmems/", "/name", " rmems/x", "rmems/x ", "rmems/x/y",
            "https://github.com/rmems/x", "-rmems/x", "rmems-/x", "rm--ems/x", "rmems/.",
            "rmems/..", "a--b/x", "a/.", "a/..", "rmems/x\n", "rm_ems/x", "rmems/x y", None, 7,
            ["rmems/x"],
        ):
            with self.subTest(value=value):
                with self.assertRaises(repo_identity.RepoNameError):
                    repo_identity.canonical_repo(value)
                self.assertFalse(repo_identity.is_canonical_repo(value))


class CommittedPolicyTests(unittest.TestCase):
    def test_committed_lists_load_at_import_as_empty_placeholders(self):
        active = policy.ACTIVE_POLICY
        for listed in active.lists():
            with self.subTest(slot=listed.slot):
                self.assertEqual(listed.status, lists.STATUS_PLACEHOLDER)
                self.assertEqual((listed.repos, listed.program_ids, listed.task_ids),
                                 (frozenset(), frozenset(), frozenset()))
        self.assertEqual(active.resolve_repo("TheAlgorithms/Python"), ("thealgorithms/python", None))

    def test_descriptor_binds_each_file_to_its_exact_bytes(self):
        descriptor = policy.ACTIVE_POLICY.descriptor()
        expected = {
            "eval_denylist": policy.DENYLIST_PATH,
            "do_not_train": policy.DO_NOT_TRAIN_PATH,
            "repo_aliases": policy.ALIAS_CACHE_PATH,
        }
        for key, path in expected.items():
            with self.subTest(key=key):
                self.assertEqual(descriptor[key]["sha256"], lists.sha256_hex(path.read_bytes()))
                self.assertEqual(descriptor[key]["path"], path.relative_to(REPO).as_posix())
        self.assertEqual(descriptor["eval_denylist"]["status"], "placeholder")
        self.assertEqual(descriptor["repo_aliases"]["updated_at"],
                         _document(policy.ALIAS_CACHE_PATH)["updated_at"])

    def test_committed_files_are_in_canonical_byte_form(self):
        for path in (policy.DENYLIST_PATH, policy.DO_NOT_TRAIN_PATH, policy.ALIAS_CACHE_PATH):
            with self.subTest(path=path.name):
                self.assertEqual(path.read_bytes(), lists.canonical_bytes(_document(path)))


class ListLoaderTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.base = _document(FIXTURES / "eval-denylist.json")

    def _load(self, document, slot=lists.LIST_EVAL_DENYLIST, raw=None):
        path = self.root / "list.json"
        path.write_bytes(raw if raw is not None else lists.canonical_bytes(document))
        return lists.load_list(path, slot)

    def _refused(self, document, pattern, **kwargs):
        with self.assertRaisesRegex(lists.ExclusionPolicyError, pattern):
            self._load(document, **kwargs)

    def test_fixture_list_loads_with_whole_values(self):
        listed = self._load(self.base)
        self.assertEqual(listed.repos, frozenset({"clap-rs/clap", "rmems/thalamic-relay"}))
        self.assertEqual(listed.values("task_ids"), frozenset({"clap-rs__clap-941"}))
        with self.assertRaises(lists.ExclusionPolicyError):
            listed.values("repo")

    def test_missing_file_and_non_strict_bytes_raise_at_load(self):
        with self.assertRaisesRegex(lists.ExclusionPolicyError, "unreadable"):
            lists.load_list(self.root / "absent.json", lists.LIST_EVAL_DENYLIST)
        self._refused(None, "not strict JSON", raw=b'{"a": 1, "a": 2}\n')
        self._refused(None, "not strict JSON", raw=b'{"a": 1.5}\n')
        # json.loads accepts NaN / Infinity / -Infinity by default and parse_float never
        # sees them; parse_constant is what refuses them (it is supported on 3.14).
        for constant in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(constant=constant):
                self._refused(None, "not strict JSON", raw=b'{"a": ' + constant + b"}\n")
        nan_list = dict(self.base, program_ids=["tap-1"])
        raw = lists.canonical_bytes(nan_list).replace(b'"tap-1"', b"NaN")
        self._refused(None, "non-integer number 'NaN'", raw=raw)
        self._refused(None, "not strict JSON", raw=b"\xff\n")
        self._refused(None, "canonical form", raw=json.dumps(self.base).encode())

    def test_an_oversized_file_is_refused_before_it_is_parsed(self):
        with (
            mock.patch.object(lists, "MAX_LIST_BYTES", 16),
            self.assertRaisesRegex(lists.ExclusionPolicyError, "exceeds 16 bytes"),
        ):
            self._load(self.base)

    def test_shape_and_identity_are_exact(self):
        cases = {
            "keys differ": lambda d: d.update(extra=[]),
            "schema_version": lambda d: d.update(schema_version="eval-exclusion-list-v2"),
            "list must be": lambda d: d.update(list="do_not_train"),
            "status must": lambda d: d.update(status="draft"),
            "note": lambda d: d.update(note=" "),
            "sorted and free": lambda d: d.update(repos=["rmems/thalamic-relay", "clap-rs/clap"]),
            "canonical lowercase": lambda d: d.update(repos=["Clap-rs/clap"]),
            "must be a list": lambda d: d.update(task_ids="clap-rs__clap-941"),
            "edge whitespace": lambda d: d.update(program_ids=[" tap-1"]),
        }
        for pattern, mutate in cases.items():
            with self.subTest(pattern=pattern):
                document = copy.deepcopy(self.base)
                mutate(document)
                self._refused(document, pattern)
        self._refused([], "JSON object")
        with self.assertRaisesRegex(lists.ExclusionPolicyError, "unknown exclusion list slot"):
            lists.load_list(FIXTURES / "eval-denylist.json", "eval")

    def test_a_placeholder_can_never_carry_entries(self):
        document = dict(self.base, status=lists.STATUS_PLACEHOLDER)
        self._refused(document, "placeholder list must not carry entries")
        self._load(dict(document, repos=[], program_ids=[], task_ids=[]))


class AliasCacheTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.path = Path(scratch.name) / "cache.json"
        self.base = _document(FIXTURES / "repo-aliases.json")

    def _refused(self, mutate, pattern):
        document = copy.deepcopy(self.base)
        mutate(document)
        self.path.write_bytes(lists.canonical_bytes(document))
        with self.assertRaisesRegex(lists.ExclusionPolicyError, pattern):
            aliases.load_cache(self.path)

    def _entry(self, document, name):
        return next(entry for entry in document["entries"] if entry["name"] == name)

    def test_fixture_cache_resolves_a_rename_in_one_lookup(self):
        cache = aliases.load_cache(FIXTURES / "repo-aliases.json")
        self.assertEqual(cache.resolve("kbknapp/clap-rs"), "clap-rs/clap")
        self.assertTrue(cache.is_alias("kbknapp/clap-rs"))
        self.assertFalse(cache.is_alias("clap-rs/clap"))
        self.assertIsNone(cache.resolve("unknown/repo"))

    def test_github_api_entries_need_a_positive_integer_id(self):
        def api(document, github_id):
            entry = self._entry(document, "thealgorithms/python")
            entry.pop("evidence")
            entry.update(method="github_api", github_id=github_id)

        self._refused(lambda d: api(d, True), "positive integer")
        self._refused(lambda d: api(d, 0), "positive integer")
        document = copy.deepcopy(self.base)
        api(document, 6000001)
        self.path.write_bytes(lists.canonical_bytes(document))
        self.assertEqual(aliases.load_cache(self.path).resolve("thealgorithms/python"),
                         "thealgorithms/python")

    def test_an_api_alias_must_name_the_same_repository_as_its_target(self):
        def api(document, name, github_id):
            entry = self._entry(document, name)
            entry.pop("evidence")
            entry.update(method="github_api", github_id=github_id)

        def mismatched(document):
            api(document, "kbknapp/clap-rs", 101)
            api(document, "clap-rs/clap", 202)

        self._refused(mismatched, "alias_cache.github_id_mismatch: 'kbknapp/clap-rs' "
                      "\\(github_id 101\\) resolves to 'clap-rs/clap' \\(github_id 202\\)")
        self._refused(lambda d: api(d, "kbknapp/clap-rs", 101),
                      "alias_cache.github_id_mismatch: .*github_id None")
        document = copy.deepcopy(self.base)
        api(document, "kbknapp/clap-rs", 101)
        api(document, "clap-rs/clap", 101)
        self.path.write_bytes(lists.canonical_bytes(document))
        self.assertEqual(aliases.load_cache(self.path).resolve("kbknapp/clap-rs"), "clap-rs/clap")

    def test_timestamps_render_in_the_cache_form(self):
        from datetime import UTC, datetime, timedelta, timezone

        moment = datetime(2026, 10, 18, 23, 14, 32, 999, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(aliases.format_timestamp(moment), "2026-10-19T04:14:32Z")
        self.assertEqual(aliases.parse_timestamp("2026-10-19T04:14:32Z", "t"),
                         datetime(2026, 10, 19, 4, 14, 32, tzinfo=UTC))

    def test_cache_shape_closure_and_timestamps_fail_closed(self):
        def chain(document):
            self._entry(document, "clap-rs/clap")["canonical"] = "rmems/thalamic-relay"

        def drop_target(document):
            document["entries"] = [e for e in document["entries"] if e["name"] != "clap-rs/clap"]

        cases = {
            "no self-entry": chain,
            "no self-entry ": drop_target,
            "sorted by unique name": lambda d: d["entries"].reverse(),
            "must match": lambda d: d.update(updated_at="2026-10-18"),
            "must match YYYY": lambda d: d.update(updated_at="2026-10-18T0:00:00Z"),
            "day 30 must be in range": lambda d: d.update(updated_at="2026-02-30T00:00:00Z"),
            "must be a UTC timestamp string": lambda d: d.update(updated_at=20261018),
            "postdates updated_at": lambda d: d.update(updated_at="2026-10-17T00:00:00Z"),
            "method is one of": lambda d: self._entry(d, "clap-rs/clap").update(method="guess"),
            "keys differ": lambda d: self._entry(d, "clap-rs/clap").update(github_id=1),
            "canonical lowercase": lambda d: self._entry(d, "kbknapp/clap-rs").update(
                canonical="Clap-rs/clap"),
            "schema_version": lambda d: d.update(schema_version="repo-alias-cache-v0"),
            "entries must be a list": lambda d: d.update(entries={}),
            "evidence": lambda d: self._entry(d, "clap-rs/clap").update(evidence=""),
        }
        for pattern, mutate in cases.items():
            with self.subTest(pattern=pattern):
                self._refused(mutate, pattern.strip())


class SchemaDriftTests(unittest.TestCase):
    """The documentation schemas must not disagree with the authoritative loaders."""

    def _schema(self, name):
        return _document(REPO / "schemas" / name)

    def test_list_schema_declares_exactly_the_loader_keys_and_vocabulary(self):
        schema = self._schema("eval-exclusion-list-v1.schema.json")
        self.assertEqual(set(schema["required"]), set(lists.LIST_KEYS))
        self.assertEqual(set(schema["properties"]), set(lists.LIST_KEYS))
        self.assertEqual(schema["properties"]["schema_version"]["const"],
                         lists.LIST_SCHEMA_VERSION)
        self.assertEqual(schema["properties"]["list"]["enum"], list(lists.LIST_SLOTS))
        self.assertEqual(set(schema["properties"]["status"]["enum"]), set(lists.LIST_STATUSES))
        self.assertEqual(schema["properties"]["repos"]["items"],
                         {"$ref": "actor-provenance-v1.schema.json#/$defs/canonicalRepo"})

    def test_alias_schema_declares_exactly_the_loader_keys_per_method(self):
        schema = self._schema("repo-alias-cache-v1.schema.json")
        self.assertEqual(schema["$defs"]["repo"],
                         {"$ref": "actor-provenance-v1.schema.json#/$defs/canonicalRepo"})
        self.assertEqual(set(schema["required"]), set(aliases.CACHE_KEYS))
        self.assertEqual(schema["properties"]["schema_version"]["const"],
                         aliases.CACHE_SCHEMA_VERSION)
        branches = schema["properties"]["entries"]["items"]["oneOf"]
        declared = {branch["properties"]["method"]["const"]: set(branch["required"])
                    for branch in branches}
        self.assertEqual(declared, {method: set(keys)
                                    for method, keys in aliases.ENTRY_KEYS_BY_METHOD.items()})


class PolicyMatchingTests(unittest.TestCase):
    def setUp(self):
        self.policy = fixture_policy()

    def _evaluate(self, repo, **ids):
        return self.policy.evaluate(policy.SourceIdentity(repo, **ids))

    def test_a_longer_repository_name_is_never_matched_by_a_listed_prefix(self):
        listed = self._evaluate("rmems/thalamic-relay")
        self.assertEqual(listed.reason_codes, (policy.REASON_EVAL_DENYLISTED,))
        longer = self._evaluate("rmems/thalamic-relay-trajectories")
        self.assertEqual(longer.reason_codes, ())
        self.assertEqual(longer.canonical_repo, "rmems/thalamic-relay-trajectories")
        self.assertEqual(longer.matches, ())

    def test_case_and_renames_canonicalize_before_matching(self):
        upper = self._evaluate("RMEMS/Thalamic-Relay")
        self.assertEqual(upper.canonical_repo, "rmems/thalamic-relay")
        self.assertTrue(upper.excluded)
        renamed = self._evaluate("kbknapp/clap-rs", task_id="clap-rs__clap-941")
        self.assertEqual(renamed.canonical_repo, "clap-rs/clap")
        self.assertEqual(renamed.reason_codes, (policy.REASON_EVAL_DENYLISTED,))
        self.assertEqual(
            renamed.matches,
            (
                {"list": "eval_denylist", "key": "repos", "value": "clap-rs/clap"},
                {"list": "eval_denylist", "key": "task_ids", "value": "clap-rs__clap-941"},
            ),
        )

    def test_both_lists_and_both_id_keys_are_checked(self):
        dnt = self._evaluate("fixture-owner/do-not-train")
        self.assertEqual(dnt.reason_codes, (policy.REASON_DO_NOT_TRAIN,))
        both = self._evaluate("clap-rs/clap", task_id="fixture-task-do-not-train")
        self.assertEqual(both.reason_codes,
                         (policy.REASON_EVAL_DENYLISTED, policy.REASON_DO_NOT_TRAIN))
        held_out = self._evaluate("thealgorithms/python", program_id="tap-fixture-held-out")
        self.assertEqual(held_out.reason_codes, (policy.REASON_EVAL_DENYLISTED,))
        clean = self._evaluate("thealgorithms/python", program_id="tap-fixture-held-out-2")
        self.assertFalse(clean.excluded)

    def test_unresolvable_sources_are_reported_never_passed(self):
        self.assertEqual(self._evaluate(None).reason_codes, (policy.REASON_REPO_UNRESOLVED,))
        self.assertEqual(self._evaluate("someone/unknown").reason_codes,
                         (policy.REASON_REPO_UNRESOLVED,))
        self.assertEqual(self._evaluate("not a repo").reason_codes, (policy.REASON_REPO_INVALID,))
        self.assertEqual(self._evaluate({"owner": "x"}).reason_codes,
                         (policy.REASON_REPO_INVALID,))
        unresolved_listed_id = self._evaluate(None, task_id="clap-rs__clap-941")
        self.assertEqual(unresolved_listed_id.reason_codes,
                         (policy.REASON_REPO_UNRESOLVED, policy.REASON_EVAL_DENYLISTED))

    def test_a_list_that_names_a_repository_by_its_old_name_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            document = _document(FIXTURES / "eval-denylist.json")
            document["repos"] = ["kbknapp/clap-rs"]
            stale = Path(temp) / "eval-denylist.json"
            stale.write_bytes(lists.canonical_bytes(document))
            with self.assertRaisesRegex(lists.ExclusionPolicyError, "old names"):
                policy.load_policy(stale, *FIXTURE_PATHS[1:])

    def test_descriptor_paths_outside_the_repository_stay_absolute(self):
        with tempfile.TemporaryDirectory() as temp:
            copies = []
            for path in FIXTURE_PATHS:
                target = Path(temp) / path.name
                target.write_bytes(path.read_bytes())
                copies.append(target)
            loaded = policy.load_policy(*copies)
            self.assertEqual(loaded.descriptor()["eval_denylist"]["path"],
                             str(copies[0].resolve()))
            self.assertEqual(loaded.descriptor(), {
                key: dict(value, path=loaded.descriptor()[key]["path"])
                for key, value in fixture_policy().descriptor().items()
            })


if __name__ == "__main__":
    unittest.main()
