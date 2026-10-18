"""Both import spellings of every tag-taxonomy module are one object, in any order.

``tag_io``, ``tag_jsonl``, ``tag_record``, ``tag_regex``, ``tag_taxonomy`` and
``tag_write`` once imported their siblings by bare name only, so
``import pipelines.tag_io`` raised ``ModuleNotFoundError``. They now open with
the package/direct prelude the other pipeline modules use, and
``tag_constants`` binds the same way so the ``TagTaxonomyError`` they all raise
keeps one class identity. Each form runs in a spawned interpreter
(``tests/tag_import_probe.py``) so nothing this process already imported can
mask a failure; ``InProcess`` then takes the package branch in this process,
after the CLI form, where the coverage report is taken.

None of these names is in ``pipelines._PACKAGE_SIBLING_NAMES``: the
``_expose_package_sibling`` finalizer binds both forms on its own, as it does
for ``preference_model``. ``pipelines/__init__.py`` is a sealed parity shared
source (``oracle_grounded/family_digest.SHARED_SOURCES``), so registering them
needs an owner-reviewed parity re-seal.
"""

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tag_import_probe as probe
from pipeline_import_test_support import clean_package_imports

_FINALIZER = re.compile(r"^    _expose_package_sibling\(__name__\)$", re.MULTILINE)

# What a paired probe report says when both forms bind one object per module.
ONE_OBJECT_REPORT = {
    "split_objects": [],
    "split_attributes": [],
    "cli_catches_package_error": True,
    "split_modules": [],
    "unbound_attributes": [],
}


def bound_tag_modules() -> frozenset[str]:
    """Every ``pipelines/tag_*.py`` that binds its two import forms to one object."""

    return frozenset(
        path.stem
        for path in probe.PIPELINES.glob("tag_*.py")
        if _FINALIZER.search(path.read_text(encoding="utf-8"))
    )


class FreshInterpreter(unittest.TestCase):
    def test_the_cli_form_alone(self):
        report = probe.in_fresh_interpreter("cli")
        flat = ("curate_tags", *probe.MODULES)
        self.assertEqual(report["names"], {name: name for name in flat})

    def test_the_package_form_alone_binds_every_module(self):
        report = probe.in_fresh_interpreter("package")
        packaged = {name: f"pipelines.{name}" for name in probe.MODULES}
        self.assertEqual(report["names"], packaged)
        self.assertFalse(report["pipelines_on_path"])
        self.assertEqual(report["split_modules"], [])
        self.assertEqual(report["unbound_attributes"], [])

    def test_either_order_is_one_object_and_one_error_class(self):
        for form in ("cli_then_package", "package_then_cli"):
            with self.subTest(form=form):
                self.assertEqual(probe.in_fresh_interpreter(form), ONE_OBJECT_REPORT)


class PreludeBranchesInProcess(unittest.TestCase):
    """Both preludes of every module, executed where coverage measures them.

    Coverage does not trace the spawned interpreters above.
    ``clean_package_imports`` unloads every repository module and restores
    them exactly on exit, so each direct branch and each package branch runs
    in this process without changing what later tests see.
    """

    def test_direct_then_package_preludes_bind_one_object_per_module(self):
        with clean_package_imports():
            report = probe.both_preludes_report()
        self.assertEqual(report, ONE_OBJECT_REPORT)


class InProcess(unittest.TestCase):
    """The package form taken after the CLI form, in this very process."""

    @classmethod
    def setUpClass(cls):
        if str(probe.REPO) not in sys.path:
            sys.path.append(str(probe.REPO))
        cls.bare = probe.cli_form()
        cls.packaged = probe.package_form()

    def test_the_probe_covers_every_bound_tag_module(self):
        self.assertEqual(frozenset(probe.MODULES), bound_tag_modules())

    def test_each_package_child_is_the_direct_module(self):
        # The package attribute (``pipelines.tag_io``) is checked only in the
        # fresh interpreters above. In a shared test process,
        # ``isolated_pipeline_modules`` can restore an older ``pipelines``
        # object after a temporary one registered ``pipelines.tag_*`` entries,
        # so that object lacks the attribute even though both names resolve to
        # one module.
        for name in probe.MODULES:
            with self.subTest(module=name):
                self.assertIs(self.packaged[name], self.bare[name])
                self.assertIs(sys.modules[f"pipelines.{name}"], self.bare[name])
                self.assertIs(sys.modules[name], self.bare[name])

    def test_shared_classes_and_functions_are_one_object(self):
        for attribute, left, right in probe.SHARED_ATTRIBUTES:
            with self.subTest(attribute=attribute, cli=left, package=right):
                self.assertIs(
                    getattr(self.bare[left], attribute),
                    getattr(self.packaged[right], attribute),
                )

    def test_the_cli_catches_an_error_the_package_form_raises(self):
        with self.assertRaises(self.bare["curate_tags"].TagTaxonomyError) as raised:
            self.packaged["tag_taxonomy"].Taxonomy({}, source="<in-process>")
        self.assertIn("version must be a nonempty string", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
