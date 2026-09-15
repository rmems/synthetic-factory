#!/usr/bin/env python3
"""Cleaned ``irc`` leftover3 family under ``pipelines/irc/``.

``irc_r3366_leftover3_mill`` was AST-extracted from ``origin/legacy-mill-lane``.
These tests pin identity, catalog fidelity, and episode shape without
publishing a raw round, without importing a ``*mill*.py`` module, and without
executing leftover mill source.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IRC_DIR = REPO / "pipelines" / "irc"
sys.path.insert(0, str(REPO / "pipelines"))

from irc import catalog  # noqa: E402
from irc import generate  # noqa: E402
from irc import pipe_catalog  # noqa: E402
from irc._contract import (  # noqa: E402
    BANNED_KEYS,
    CATALOG_FIRST,
    CATALOG_LAST,
    COMMITTED_MILL_CATALOGS,
    COMMITTED_SPEC_ROW_COUNT,
    DEFERRED_MILLS,
    FAMILY_LANE_COMMIT,
    FULL_MILL_CATALOGS,
    FULL_SPEC_ROW_COUNT,
    FACTORY,
    FAMILY_PREFIX,
    FAMILY_SOURCE_FILES,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PAIR_NOT_FOUND,
    FINDING_ROUND_INVALID,
    FINDING_VENDOR_PATH,
    GENERATOR,
    N_PAIRS,
    SOURCE_COMMIT,
    SOURCE_GENERATOR,
    SOURCE_MILL_ID,
    SOURCE_PATH,
    SOURCE_REF,
    SOURCE_SHA256,
    STEPS,
    IrcRefusal,
    refuse_vendor_paths,
)
from irc.cli import run as irc_run  # noqa: E402
from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from record_kind import classify_kind  # noqa: E402

EXPECTED_OK_SLUGS = (
    "networkd-ipv6acceptra-vs-dhcp",
    "chrony-makestep-vs-ntpd",
    "nft-set-vs-iptables",
    "podman-cgroup-vs-crun",
    "buildah-isolation-vs-docker",
    "skopeo-policy-vs-crane",
    "cosign-rekor-vs-notation",
    "syft-cataloger-vs-trivy",
    "grype-ignore-vs-osv",
    "opa-decision-logs-vs-kyverno",
    "cilium-hubble-vs-calico",
    "linkerd-proxy-vs-istio",
    "vault-transit-vs-sops",
    "age-recipients-vs-gpg",
    "restic-forget-vs-borg",
    "kopia-ignore-vs-duplicacy",
)
FIRST_OK_ID = "irc-r3366-networkd-ipv6acceptra-vs-dhcp-11265-78cf"
FIRST_BAD_ID = "irc-r3366-dhcpcd-iaid-vs-networkd-11266-902b"
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "generate.py",
    "pipe_catalog.py",
)
FORBIDDEN_CALLS = frozenset({"exec", "eval", "compile", "__import__"})


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = irc_run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_source():
    return subprocess.check_output(
        ["git", "show", f"{SOURCE_REF}:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )


def _package_calls():
    names = set()
    for path in IRC_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                names.add(node.func.id)
    return names


class IrcPackageLayout(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = tuple(sorted(path.name for path in IRC_DIR.iterdir() if path.suffix == ".py"))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))
        self.assertFalse(any("mill" in name for name in names))

    def test_no_vendored_mill_scripts(self):
        tracked = subprocess.check_output(["git", "ls-files"], text=True, cwd=REPO)
        for line in tracked.splitlines():
            name = Path(line).name
            self.assertFalse(name.startswith(("irc-mill-", "irc-loop-", "irc-chain-", "irc-pub-")))
            self.assertFalse(name.startswith("irc_r") and name.endswith("_mill.py"))
            self.assertNotIn("experiments/irc", line)

    def test_package_is_under_2500_lines(self):
        total = sum(path.read_text().count("\n") for path in IRC_DIR.glob("*.py"))
        total += (REPO / "tests" / "test_irc.py").read_text().count("\n")
        self.assertLessEqual(total, 2500)

    def test_extract_modules_do_not_exec_mill_source(self):
        self.assertTrue(FORBIDDEN_CALLS.isdisjoint(_package_calls()))


class IrcContract(unittest.TestCase):
    def test_factory_matches_reviewed_irc_prefix(self):
        self.assertEqual(FACTORY, "incident-response-oncall-factory")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(GENERATOR, "irc-mill")
        self.assertEqual(SOURCE_GENERATOR, "grok-4.6")
        self.assertEqual(SOURCE_MILL_ID, "irc_r3366_leftover3_mill")
        self.assertEqual(CATALOG_FIRST, 3366)
        self.assertEqual(CATALOG_LAST, 3381)
        self.assertEqual(N_PAIRS, 16)
        self.assertEqual(STEPS, 17)
        self.assertEqual(FAMILY_SOURCE_FILES, 141)
        self.assertEqual(DEFERRED_MILLS, 60)
        self.assertEqual(FAMILY_LANE_COMMIT[:8], "813f93f1")
        self.assertEqual(FULL_SPEC_ROW_COUNT, 2900)
        self.assertEqual(COMMITTED_SPEC_ROW_COUNT, 1848)
        self.assertEqual(COMMITTED_MILL_CATALOGS, 34)
        self.assertEqual(SOURCE_COMMIT[:8], "070f1697")
        self.assertEqual(SOURCE_SHA256[:8], "99608f5b")

    def test_vendor_paths_fail_closed(self):
        with self.assertRaises(IrcRefusal) as caught:
            refuse_vendor_paths(["experiments/irc-mill-r3577.py"])
        self.assertEqual(caught.exception.code, FINDING_VENDOR_PATH)
        with self.assertRaises(IrcRefusal):
            refuse_vendor_paths(["irc_r3366_leftover3_mill.py"])
        refuse_vendor_paths(["pipelines/irc/catalog.py"])


class IrcCatalog(unittest.TestCase):
    def test_sixteen_unique_pairs(self):
        self.assertEqual(len(catalog.PAIRS), 16)
        self.assertEqual(catalog.slugs(), EXPECTED_OK_SLUGS)
        self.assertEqual(len(set(catalog.slugs())), 16)
        self.assertEqual(len({pair["bad"]["slug"] for pair in catalog.PAIRS}), 16)

    def test_pair_lookup_and_refusals(self):
        self.assertEqual(catalog.pair_at(0)["ok"]["slug"], EXPECTED_OK_SLUGS[0])
        self.assertEqual(catalog.pair_for_round(3366)["ok"]["svc"], "gate-netd-svc")
        self.assertEqual(catalog.pair_by_ok_slug("kopia-ignore-vs-duplicacy")["ok"]["metric"], "kopia_ignore_star")
        with self.assertRaises(IrcRefusal) as missing:
            catalog.pair_at(-1)
        self.assertEqual(missing.exception.code, FINDING_PAIR_NOT_FOUND)
        with self.assertRaises(IrcRefusal) as bogus:
            catalog.pair_at(True)  # type: ignore[arg-type]
        self.assertEqual(bogus.exception.code, FINDING_PAIR_NOT_FOUND)
        with self.assertRaises(IrcRefusal):
            catalog.pair_by_ok_slug("not-a-pair")
        with self.assertRaises(IrcRefusal) as early:
            catalog.pair_for_round(3365)
        self.assertEqual(early.exception.code, FINDING_PAIR_NOT_FOUND)
        with self.assertRaises(IrcRefusal) as boolean:
            catalog.pair_for_round(True)  # type: ignore[arg-type]
        self.assertEqual(boolean.exception.code, FINDING_ROUND_INVALID)


class IrcGenerate(unittest.TestCase):
    def test_success_pair_is_irc_oncall_episode(self):
        ok, bad = generate.pair_records(3366)
        self.assertEqual(mill_prefix(ok), "irc")
        self.assertEqual(ok["id"], FIRST_OK_ID)
        self.assertEqual(bad["id"], FIRST_BAD_ID)
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(ok["kind"], "episode")
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["round"], 3366)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], SOURCE_GENERATOR)
        self.assertEqual(ok["meta"]["ticket"], "W2-11265")
        self.assertEqual(ok["remediate"], "rollback")
        self.assertEqual(bad["remediate"], "patch")
        self.assertTrue(ok["reward"]["success"])
        self.assertTrue(bad["reward"]["success"])
        self.assertEqual(len(ok["steps"]), STEPS)
        self.assertEqual(ok["false_lead"]["survived_steps"], [6, 7, 8])
        self.assertEqual(ok["false_lead"]["falsified_at"], 10)
        tools = [step["tool_call"]["name"] for step in ok["steps"]]
        self.assertEqual(tools[:5], ["read", "read", "fetch", "fetch", "fetch"])
        self.assertIn("429", ok["steps"][2]["observation"])
        self.assertIn("502", ok["steps"][3]["observation"])
        blob = json.dumps(ok["steps"])
        for banned in BANNED_KEYS:
            self.assertNotIn(f'"{banned}"', blob)
        self.assertFalse(any("reward" in step for step in ok["steps"]))
        self.assertIn("gate-netd-svc", ok["goal"])
        self.assertIn("Novel coverage: 97%", generate.notes_for(3366, ok, bad))

    def test_every_pair_validates(self):
        for rnd in range(CATALOG_FIRST, CATALOG_LAST + 1):
            ok, bad = generate.pair_records(rnd)
            self.assertEqual(mill_prefix(ok), "irc")
            self.assertEqual(mill_prefix(bad), "irc")
            self.assertEqual(ok["meta"]["round"], rnd)
            self.assertEqual(len(ok["steps"]), STEPS)
            self.assertEqual(len(bad["steps"]), STEPS)
            self.assertTrue(ok["reward"]["success"])
            self.assertTrue(bad["reward"]["success"])
            self.assertEqual({ok["remediate"], bad["remediate"]}, {"rollback", "patch"})

    def test_invalid_round_is_refused(self):
        with self.assertRaises(IrcRefusal):
            generate.pair_records(0)
        with self.assertRaises(IrcRefusal):
            generate.pair_records(True)  # type: ignore[arg-type]
        with self.assertRaises(IrcRefusal):
            generate.pair_records(3382)

    def test_generate_writes_new_dest_and_refuses_raw(self):
        root = Path(tempfile.mkdtemp(prefix="irc-gen-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "out"
        summary = generate.run(generate.GenerateRequest(out_dir=dest, round=3366))
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        records = [
            json.loads(line)
            for line in (dest / "records.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertEqual([record["id"] for record in records], [FIRST_OK_ID, FIRST_BAD_ID])
        with self.assertRaises(IrcRefusal) as exists:
            generate.run(generate.GenerateRequest(out_dir=dest, round=3366))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = REPO / "outputs" / "raw" / "irc-should-not-write"
        with self.assertRaises(IrcRefusal) as under:
            generate.run(generate.GenerateRequest(out_dir=raw, round=3366))
        self.assertEqual(under.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())


class IrcAstExtract(unittest.TestCase):
    def test_catalog_matches_legacy_literals_without_exec(self):
        try:
            source = _legacy_source()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        extracted = catalog.pairs_from_source(source)
        self.assertEqual(len(extracted), 16)
        self.assertEqual([pair["ok"]["slug"] for pair in extracted], list(EXPECTED_OK_SLUGS))
        for extracted_pair, pair in zip(extracted, catalog.PAIRS, strict=True):
            self.assertEqual(extracted_pair["ok"], pair["ok"])
            self.assertEqual(extracted_pair["bad"], pair["bad"])
        tree = ast.parse(source)
        names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        self.assertIn("episode", names)
        self.assertIn("reserve", names)
        self.assertIn("publish", names)
        self.assertNotIn("reserve", generate.__all__)
        self.assertNotIn("publish", generate.__all__)

    def test_r3577_specs_match_committed_jsonl_without_exec(self):
        try:
            source = subprocess.check_output(
                ["git", "show", f"{SOURCE_REF}:experiments/irc-mill-r3577.py"],
                text=True,
                cwd=REPO,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        field, rows = pipe_catalog.pipe_rows_from_source(source)
        self.assertEqual(field, "SPECS")
        self.assertEqual(len(rows), 80)
        self.assertEqual(rows[0].split("|", 1)[0], "debezium")
        self.assertEqual(rows[-1].split("|", 1)[0], "papermill")
        family = pipe_catalog.load_family_catalog()
        committed = [row for row in family.spec_rows if row.mill_round == 3577]
        self.assertEqual(len(committed), 80)
        self.assertEqual([row.pipe for row in committed], list(rows))


class IrcPipeCatalog(unittest.TestCase):
    def test_family_catalog_pins_and_row_count(self):
        family = pipe_catalog.catalog_family_check()
        self.assertEqual(family.committed_spec_rows, COMMITTED_SPEC_ROW_COUNT)
        self.assertEqual(len(family.sources), 141)
        deferred = [
            source
            for source in family.sources
            if source.get("path", "").startswith("experiments/irc-mill-r")
            and source.get("committed") is False
        ]
        self.assertEqual(len(deferred), FULL_MILL_CATALOGS - COMMITTED_MILL_CATALOGS)
        rounds = pipe_catalog.iter_committed_mill_rounds(family.sources)
        self.assertEqual(rounds[-1], 4481)
        self.assertNotIn(5001, rounds)

    def test_deferred_r5001_is_pinned_not_in_jsonl(self):
        family = pipe_catalog.load_family_catalog()
        deferred = next(
            source
            for source in family.sources
            if source.get("path") == "experiments/irc-mill-r5001.py"
        )
        self.assertFalse(deferred.get("committed"))
        self.assertEqual(deferred.get("n_rows_extracted"), 52)
        self.assertFalse(any(row.mill_round == 5001 for row in family.spec_rows))


class IrcCli(unittest.TestCase):
    def test_catalog_lists_pairs(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn(SOURCE_MILL_ID, out)
        self.assertIn(EXPECTED_OK_SLUGS[0], out)
        self.assertIn(EXPECTED_OK_SLUGS[-1], out)

    def test_catalog_json_is_exact(self):
        code, out, err = invoke(["catalog", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["source"], SOURCE_MILL_ID)
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(len(payload["plants"]), 16)

    def test_catalog_check_ok(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["plants"], 16)
        self.assertEqual(payload["committed_spec_rows"], COMMITTED_SPEC_ROW_COUNT)
        self.assertEqual(payload["full_spec_rows"], FULL_SPEC_ROW_COUNT)

    def test_generate_one_pair(self):
        root = Path(tempfile.mkdtemp(prefix="irc-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "out"
        code, out, err = invoke(["generate", "--out", str(dest), "--round", "3366"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("2 records", out)
        first = json.loads((dest / "records.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(first["id"], FIRST_OK_ID)

    def test_unknown_slug_is_exit_two(self):
        root = Path(tempfile.mkdtemp(prefix="irc-miss-"))
        self.addCleanup(shutil.rmtree, root, True)
        code, out, err = invoke(["generate", "--out", str(root / "out"), "--slug", "nope"])
        self.assertEqual(code, 2)
        self.assertIn("irc.pair_not_found", err)

    def test_notes_command(self):
        code, out, err = invoke(["notes", "--round", "3366"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Novel coverage: 97%", out)
        self.assertIn(FIRST_OK_ID, out)


class IrcImportTwin(unittest.TestCase):
    def test_both_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines import irc as packaged

        self.assertIs(packaged.catalog, catalog)
        self.assertIs(sys.modules["irc.catalog"], sys.modules["pipelines.irc.catalog"])
        self.assertIs(sys.modules["irc._contract"].IrcRefusal, IrcRefusal)


if __name__ == "__main__":
    unittest.main()
