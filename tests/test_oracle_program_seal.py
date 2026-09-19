"""Delegated oracle implementations are covered by the reviewed program seal."""

import ast
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import source_policy


def _import_names(node):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.module in (None, "pipelines"):
        return [alias.name for alias in node.names]
    return [node.module]


def _oracle_dependencies(path, pipelines):
    nodes = ast.walk(ast.parse(path.read_text(encoding="utf-8")))
    names = {name.removeprefix("pipelines.").split(".")[0]
             for node in nodes for name in _import_names(node)}
    candidates = {pipelines / f"{name}.py" for name in names if name.startswith("oracle_")}
    return {path for path in candidates if path.is_file()}


def oracle_program_closure(pipelines):
    """Follow static direct/package imports to every delegated oracle sibling."""
    pending = {pipelines / "oracle_generate.py", pipelines / "oracle_validate.py"}
    pending.update((pipelines / "oracle_grounded").glob("*.py"))
    visited = set()
    while pending:
        path = pending.pop()
        visited.add(path)
        pending.update(_oracle_dependencies(path, pipelines) - visited)
    return {path.name for path in visited if path.parent == pipelines}


class OracleProgramSealTests(unittest.TestCase):
    def test_dependency_guard_covers_direct_relative_and_package_imports(self):
        statements = (
            "import oracle_delegate",
            "from oracle_delegate import Validator",
            "from .oracle_delegate import Validator",
            "from . import oracle_delegate",
            "import pipelines.oracle_delegate",
            "from pipelines.oracle_delegate import Validator",
            "from pipelines import oracle_delegate",
        )
        with tempfile.TemporaryDirectory() as directory:
            pipelines = Path(directory)
            delegate = pipelines / "oracle_delegate.py"
            delegate.write_text("", encoding="utf-8")
            facade = pipelines / "oracle_facade.py"
            for statement in statements:
                with self.subTest(statement=statement):
                    facade.write_text(statement, encoding="utf-8")
                    self.assertEqual(_oracle_dependencies(facade, pipelines), {delegate})

    def test_every_transitively_delegated_oracle_source_is_sealed(self):
        delegated = oracle_program_closure(source_policy.ROOT / "pipelines")
        self.assertFalse(delegated - set(source_policy.PROGRAM_NAMES),
                         sorted(delegated - set(source_policy.PROGRAM_NAMES)))

    def test_modifying_each_delegated_program_invalidates_source_authority(self):
        original_root = source_policy.ROOT
        delegated = oracle_program_closure(original_root / "pipelines")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("pipelines/oracle_grounded", "schemas/oracle-grounded"):
                shutil.copytree(original_root / relative, root / relative)
            members = {"LICENSE", "schemas/oracle-grounded-v1.schema.json"}
            members.update(source_policy.NATIVE_SOURCE_NAMES)
            members.update(f"pipelines/{name}" for name in source_policy.PROGRAM_NAMES)
            members.update(f"pipelines/{name}" for name in delegated)
            for relative in members:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original_root / relative, destination)
            with mock.patch.object(source_policy, "ROOT", root):
                source_policy.verify_source_bytes()
                for name in sorted(delegated):
                    with self.subTest(program=name):
                        path = root / "pipelines" / name
                        original = path.read_bytes()
                        try:
                            path.write_bytes(original + b"\n# unreviewed validator implementation change\n")
                            with self.assertRaises(source_policy.SourcePolicyError):
                                source_policy.verify_source_bytes()
                        finally:
                            path.write_bytes(original)
                source_policy.verify_source_bytes()


if __name__ == "__main__":
    unittest.main()
