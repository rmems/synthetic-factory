"""Every flat ``pipelines/`` module is one object under its bare and package names.

``python3 pipelines/x.py`` imports its siblings by bare name, while package
consumers import ``pipelines.x``. The binding prelude CLAUDE.md documents
(``_assert_direct_sibling``, ``_join_package_sibling``, and the
``_expose_package_sibling`` finalizer) keeps those two names one module object.
A module without it loads a second copy once a process has used both names, and
``except SomeError`` stops catching the other copy's class. ``preference_model``
did exactly that (#427) when the round-robin CI shards put
``test_compose_curated_facade_contract`` and ``test_curate_preferences_writer``
in one process. This contract imports every flat module under both names, in
both orders, in a fresh interpreter (``tests/pipelines_import_twin_probe.py``),
so the order the suite happens to run in cannot hide a split. It discovers the
modules from the directory, so a new module is covered without being listed;
``test_pipeline_split_module_identity`` keeps pinning class-level identity for
its curated split facades through the literal-bound import catalog.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pipelines_import_twin_probe as probe

# The only modules allowed to split, in three named sets. Converting one to the
# binding prelude makes it one object, and this contract then fails until its
# name is removed here, so the sets only shrink. The direct-execution-only set
# (CLAUDE.md, "Import conventions in pipelines/") is gone: #436 converted the
# ``tag_*`` modules and #441 the other eight.

# Byte-sealed modules that still lack the prelude. Adding it changes their bytes,
# and so a reviewed stamp: ``tag_jsonutil`` is in ``family_digest.SHARED_SOURCES``
# (the hardware-parity and NIR ``generator_version``), and the ``oracle_*_part*``
# modules are in ``source_policy.PROGRAM_NAMES`` (``programs_sha256`` in
# ``schemas/procedural-oracle-policy-v1.json``). Each needs an owner-reviewed
# parity or procedural-oracle re-seal before it can take the prelude.
# The oracle parts as {facade: number of _partN modules}.
_SEALED_ORACLE_PARTS = {
    "oracle_record_envelope": 2,
    "oracle_record_stages": 6,
    "oracle_validate_capture": 2,
    "oracle_validate_manifest": 4,
    "oracle_validate_manifest_records": 3,
    "oracle_validate_snapshot": 2,
}
SEALED_UNTIL_RESEAL = frozenset(
    {
        "tag_jsonutil",
        *(
            f"{facade}_part{index}"
            for facade, parts in _SEALED_ORACLE_PARTS.items()
            for index in range(1, parts + 1)
        ),
    }
)

# Modules left to open pull requests that change the same lines or pin them.
# ``verify_hf_release`` gains the prelude in #424, together with its rights
# import. ``tag_regex_domain`` is left for the tag family after #436, whose probe
# pins exactly which ``tag_*`` modules carry the finalizer.
LEFT_TO_OPEN_PRS = frozenset({"tag_regex_domain", "verify_hf_release"})

# Thin CLI shims, by the subpackage they front: each only re-exports its
# subpackage's ``cli`` module, which ``bind_import_twin`` already makes one object
# under both names, so a second shim copy carries nothing of its own.
# ``test_each_thin_shim_only_re_exports_its_one_cli`` pins that.
THIN_CLI_SHIMS = {"actf_cli": "actf", "code_repair_cli": "code_repair", "mill_cli": "mill"}
# Everything a thin shim may define: its import bootstrap and the ``cli`` it re-exports.
THIN_SHIM_NAMES = frozenset({"Path", "_PIPELINES", "annotations", "cli", "sys"})

ALLOWLISTS = (
    SEALED_UNTIL_RESEAL,
    LEFT_TO_OPEN_PRS,
    frozenset(THIN_CLI_SHIMS),
)
ALLOWED_TO_SPLIT = frozenset().union(*ALLOWLISTS)

_UNEXPECTED_SPLIT = (
    "these modules load a second copy when imported under both names; give each the "
    "binding prelude (_assert_direct_sibling / _join_package_sibling in the two prelude "
    "branches, _expose_package_sibling(__name__) as the finalizer)"
)
_STALE_ALLOWLIST = (
    "these modules are now one object under both names; remove them from "
    "SEALED_UNTIL_RESEAL, LEFT_TO_OPEN_PRS or THIN_CLI_SHIMS"
)
_THICK_SHIM = (
    "a thin CLI shim defines names beyond its bootstrap and cli; give it the binding "
    "prelude and remove it from THIN_CLI_SHIMS"
)


def assert_only_allowlisted_modules_split(case, report):
    """Fail ``case`` naming each unexpected split and each allowlisted module now one object."""

    case.assertEqual(report["modules"], len(probe.flat_modules()))
    split = set(report["split"])
    case.assertEqual(sorted(split - ALLOWED_TO_SPLIT), [], _UNEXPECTED_SPLIT)
    case.assertEqual(sorted(ALLOWED_TO_SPLIT - split), [], _STALE_ALLOWLIST)


class FreshInterpreter(unittest.TestCase):
    def test_the_allowlists_name_existing_flat_modules_once(self):
        modules = probe.flat_modules()
        self.assertEqual(sorted(ALLOWED_TO_SPLIT - set(modules)), [])
        self.assertEqual(sum(map(len, ALLOWLISTS)), len(ALLOWED_TO_SPLIT))
        self.assertIn("preference_model", modules)

    def test_only_allowlisted_modules_split_in_either_order(self):
        for order in probe.ORDERS:
            with self.subTest(order=order):
                report = probe.in_fresh_interpreter(
                    probe.isolated_report, order, probe.flat_modules()
                )
                assert_only_allowlisted_modules_split(self, report)

    def test_each_thin_shim_only_re_exports_its_one_cli(self):
        for order in probe.ORDERS:
            with self.subTest(order=order):
                report = probe.in_fresh_interpreter(
                    probe.isolated_shim_report, order, THIN_CLI_SHIMS
                )
                self.assertEqual(sorted(report), sorted(THIN_CLI_SHIMS))
                split_cli = sorted(shim for shim, facts in report.items() if not facts["one_cli"])
                self.assertEqual(split_cli, [], "these shims expose a second cli object")
                extra = {
                    shim: sorted(set(facts["names"]) - THIN_SHIM_NAMES)
                    for shim, facts in report.items()
                    if not THIN_SHIM_NAMES.issuperset(facts["names"])
                }
                self.assertEqual(extra, {}, _THICK_SHIM)


class InProcess(unittest.TestCase):
    """The same probe in this process, on a clean slate that is restored afterwards.

    The fresh interpreters above are the contract. Importing direct-first here also
    runs both branches of every prelude and each finalizer under the process the
    coverage report is taken from.
    """

    def test_only_allowlisted_modules_split_in_process(self):
        report = probe.isolated_report("direct_first", probe.flat_modules())
        assert_only_allowlisted_modules_split(self, report)


if __name__ == "__main__":
    unittest.main()
