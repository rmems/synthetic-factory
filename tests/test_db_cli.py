#!/usr/bin/env python3
"""CLI JSON smoke and leftover-mill import guard for the cleaned db mill."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB_DIR = REPO / "pipelines" / "db"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_BEFORE_DB = {name for name in sys.modules if "leftover_mill" in name}

from pipelines.db import check as _check  # noqa: E402,F401
from pipelines.db import cli as _cli  # noqa: E402,F401
from pipelines.db import config as cfg  # noqa: E402


class CliJsonSmoke(unittest.TestCase):
    def test_emit_prints_json_ids_into_a_fresh_temp_dir(self):
        with tempfile.TemporaryDirectory(prefix="dbm-cli-") as td:
            dest = Path(td)
            env = os.environ.copy()
            env["TMPDIR"] = td
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pipelines.db.cli",
                    "emit",
                    str(cfg.START_ROUND),
                    str(dest),
                ],
                cwd=str(REPO),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            ids = list(payload["ids"])
            self.assertEqual(len(ids), 2)
            prefix = f"dbm-r{cfg.START_ROUND}-"
            self.assertTrue(all(item.startswith(prefix) for item in ids))
            batch = dest / f"batch-r{cfg.START_ROUND:02d}.jsonl"
            notes = dest / f"NOTES-r{cfg.START_ROUND:02d}.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = [line for line in batch.read_text(encoding="utf-8").splitlines() if line]
            self.assertEqual(len(lines), 2)
            self.assertEqual([json.loads(line)["id"] for line in lines], ids)
            self.assertIn("Novel coverage:", notes.read_text(encoding="utf-8"))


class NoLeftoverMillImport(unittest.TestCase):
    def test_db_package_sources_do_not_import_leftover_mill(self):
        sources = sorted(DB_DIR.glob("*.py"))
        self.assertTrue(sources)
        for path in sources:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.append(node.module)
            for name in imported:
                self.assertNotIn("leftover_mill", name.split("."), path.name)

    def test_importing_the_package_does_not_load_leftover_mill(self):
        after = {name for name in sys.modules if "leftover_mill" in name}
        self.assertEqual(after, _BEFORE_DB)


if __name__ == "__main__":
    unittest.main()
