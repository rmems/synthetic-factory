#!/usr/bin/env python3
"""The cleaned ``srl`` family home under ``pipelines/srl/``.

``srl_r6110`` was AST-extracted from ``origin/legacy-mill-lane``. These tests
pin identity, catalog fidelity, and episode shape without publishing a raw
round and without importing a ``*mill*.py`` module.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRL_DIR = REPO / "pipelines" / "srl"
sys.path.insert(0, str(REPO / "pipelines"))

from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from srl import catalog  # noqa: E402
from srl import generate  # noqa: E402
from srl._contract import (  # noqa: E402
    BANNED,
    FACTORY,
    FAMILY_PREFIX,
    GEN,
    HOP,
    N_STEPS,
    SOURCE_MILL_ID,
    SOURCE_PATH,
    SOURCE_ROUND,
    SrlError,
)
from srl.cli import run as srl_run  # noqa: E402

EXPECTED_SLUGS = (
    "networkd-dhcp-ipv4-only",
    "chrony-maxslewrate-vs-ntpd",
    "nft-flowtable-timeout-vs-ipt",
    "podman-events-logger-journald",
    "buildah-format-oci-vs-docker",
    "skopeo-dest-tls-verify",
    "cosign-rekor-url-vs-notation",
    "syft-cataloger-file-vs-trivy",
    "grype-only-fixed-vs-trivy",
    "opa-decision-logs-vs-kyverno",
    "cilium-hubble-relay-tls",
    "linkerd-proxy-await-vs-istio",
    "vault-seal-wrap-vs-transit",
    "age-recipients-file-vs-sops",
    "restic-forget-keep-daily-vs-borg",
    "kopia-compression-zstd-vs-restic",
)
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "generate.py",
    "cli.py",
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = srl_run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_namespace():
    src = subprocess.check_output(
        ["git", "show", f"origin/legacy-mill-lane:{SOURCE_PATH}"],
        text=True,
        cwd=REPO,
        stderr=subprocess.DEVNULL,
    )
    tree = ast.parse(src)
    ns = {"hashlib": __import__("hashlib"), "json": json}
    for node in tree.body:
        keep = False
        if isinstance(node, ast.Assign):
            keep = any(
                isinstance(target, ast.Name)
                and target.id in ("FACTORY", "GEN", "N_STEPS", "BANNED", "HOP", "PLANTS")
                for target in node.targets
            )
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            keep = node.target.id in ("FACTORY", "GEN", "N_STEPS", "BANNED", "HOP", "PLANTS")
        if isinstance(node, ast.FunctionDef) and node.name in ("hid", "episode"):
            keep = True
        if keep:
            exec(compile(ast.Module([node], type_ignores=[]), "<legacy>", "exec"), ns)
    return ns


class SrlPackageLayout(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        names = tuple(sorted(path.name for path in SRL_DIR.iterdir() if path.suffix == ".py"))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))
        self.assertFalse(any("mill" in name for name in names))


class SrlContract(unittest.TestCase):
    def test_factory_matches_reviewed_srl_prefix(self):
        self.assertEqual(FACTORY, "sparse-reward-long-task-factory")
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(GEN, "grok-4.6")
        self.assertEqual(N_STEPS, 32)
        self.assertEqual(SOURCE_MILL_ID, "srl_r6110")
        self.assertEqual(SOURCE_ROUND, 6110)
        self.assertEqual(HOP[0], "incident-response-oncall-factory")
        self.assertEqual(len(HOP), 5)


class SrlCatalog(unittest.TestCase):
    def test_sixteen_unique_plants(self):
        self.assertEqual(len(catalog.PLANTS), 16)
        self.assertEqual(catalog.slugs(), EXPECTED_SLUGS)
        self.assertEqual(len(set(catalog.slugs())), 16)

    def test_plant_lookup_and_refusals(self):
        self.assertEqual(catalog.plant_at(0)["slug"], "networkd-dhcp-ipv4-only")
        self.assertEqual(
            catalog.plant_by_slug("kopia-compression-zstd-vs-restic")["issue"],
            1516,
        )
        with self.assertRaises(SrlError):
            catalog.plant_at(-1)
        with self.assertRaises(SrlError):
            catalog.plant_at(True)  # type: ignore[arg-type]
        with self.assertRaises(SrlError):
            catalog.plant_by_slug("not-a-plant")


class SrlGenerate(unittest.TestCase):
    def test_episode_is_srl_prefix_terminal_only(self):
        record = generate.episode(6110, catalog.plant_at(0))
        self.assertEqual(mill_prefix(record), "srl")
        self.assertEqual(record["id"], "srl-r6110-networkd-dhcp-ipv4-only-c67a")
        self.assertEqual(record["meta"]["factory"], FACTORY)
        self.assertEqual(record["meta"]["round"], 6110)
        self.assertEqual(len(record["steps"]), N_STEPS)
        self.assertEqual(
            record["reward"],
            {
                "success": True,
                "terminal_only": True,
                "horizon_steps": N_STEPS,
                "mid_reward_steps": 0,
            },
        )
        blob = str(record)
        for banned in BANNED:
            self.assertNotIn(banned, blob)
        self.assertFalse(any("reward" in step for step in record["steps"]))
        self.assertIn("Novel coverage: 42%", generate.notes(6110, catalog.plant_at(0)))

    def test_hid_is_sha1_prefix(self):
        self.assertEqual(generate.hid("networkd-dhcp-ipv4-only"), "c67a")
        first = generate.hid("networkd-dhcp-ipv4-only")
        self.assertEqual(first, "c67a")
        self.assertEqual(first, generate.hid("networkd-dhcp-ipv4-only"))

    def test_window_is_one_plant_per_round(self):
        records = generate.generate_window(6110)
        self.assertEqual(len(records), 16)
        self.assertEqual(records[0]["meta"]["round"], 6110)
        self.assertEqual(records[-1]["meta"]["round"], 6125)
        self.assertTrue(
            all(slug in record["id"] for record, slug in zip(records, EXPECTED_SLUGS, strict=True))
        )

    def test_invalid_round_is_refused(self):
        with self.assertRaises(SrlError):
            generate.episode(0, catalog.plant_at(0))
        with self.assertRaises(SrlError):
            generate.episode(True, catalog.plant_at(0))  # type: ignore[arg-type]


class SrlAstExtract(unittest.TestCase):
    def test_catalog_and_tool_calls_match_legacy_ast(self):
        try:
            legacy = _legacy_namespace()
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        self.assertEqual(legacy["FACTORY"], FACTORY)
        self.assertEqual(legacy["GEN"], GEN)
        self.assertEqual(legacy["N_STEPS"], N_STEPS)
        self.assertEqual(tuple(legacy["BANNED"]), BANNED)
        self.assertEqual([plant["slug"] for plant in legacy["PLANTS"]], list(EXPECTED_SLUGS))
        for extracted, plant in zip(legacy["PLANTS"], catalog.PLANTS, strict=True):
            self.assertEqual(extracted, dict(plant))
        legacy_rec = legacy["episode"](6110, legacy["PLANTS"][0])
        cleaned = generate.episode(6110, catalog.plant_at(0))
        self.assertEqual(
            [step["tool_call"] for step in cleaned["steps"]],
            [step["tool_call"] for step in legacy_rec["steps"]],
        )
        self.assertEqual(cleaned["id"], legacy_rec["id"])
        self.assertEqual(cleaned["reward"], legacy_rec["reward"])
        self.assertEqual(cleaned["meta"], legacy_rec["meta"])


class SrlCli(unittest.TestCase):
    def test_catalog_lists_plants(self):
        code, out, err = invoke(["catalog"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("srl_r6110", out)
        self.assertIn("networkd-dhcp-ipv4-only", out)
        self.assertIn("kopia", out)

    def test_catalog_json_is_exact(self):
        code, out, err = invoke(["catalog", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["source"], "srl_r6110")
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(len(payload["plants"]), 16)

    def test_generate_one_record(self):
        code, out, err = invoke(["generate", "--round", "6110", "--index", "0"])
        self.assertEqual((code, err), (0, ""))
        record = json.loads(out)
        self.assertEqual(record["id"], "srl-r6110-networkd-dhcp-ipv4-only-c67a")
        self.assertEqual(len(record["steps"]), 32)

    def test_generate_window(self):
        code, out, err = invoke(["generate", "--window", "--round", "6110"])
        self.assertEqual((code, err), (0, ""))
        lines = [line for line in out.splitlines() if line]
        self.assertEqual(len(lines), 16)
        self.assertEqual(json.loads(lines[-1])["meta"]["round"], 6125)

    def test_unknown_slug_is_exit_two(self):
        code, out, err = invoke(["generate", "--round", "6110", "--slug", "nope"])
        self.assertEqual((code, out), (2, ""))
        self.assertTrue(err.startswith("unknown_plant:"), err)

    def test_notes_command(self):
        code, out, err = invoke(["notes", "--round", "6110", "--slug", "networkd-dhcp-ipv4-only"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Novel coverage: 42%", out)


if __name__ == "__main__":
    unittest.main()
