"""Harness checks that need a real interpreter or shell.

The bundle builders still refuse under ``python -O`` (their checks are not asserts),
and the shell scripts keep the shebang on line 1 and parse under the bash their
shebang names. These are the only harness tests that start a process; none of them
reaches the network or runs hf, gh or git.
"""

import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("skill_publish_test_support")

OPTIMIZED_PROBE = r"""
import importlib.util, json, sys, types
from pathlib import Path
repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "pipelines"))
parquet = types.ModuleType("pyarrow.parquet")
package = types.ModuleType("pyarrow")
package.parquet = parquet
sys.modules.update({"pyarrow": package, "pyarrow.parquet": parquet})

def load(name):
    path = repo / ".claude" / "skills" / "publish-hub-research-run" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

bb, bf = load("build_bundles"), load("build_fix")
probes = {
    "bare assert": lambda: exec("assert False"),
    "bb.round_key": lambda: bb.round_key("batch-final.jsonl"),
    "bb.census": lambda: bb._record_census([{"id": "a"}, {"id": "a"}]),
    "bf.census": lambda: bf.census([{"id": "a"}, {"id": "a"}]),
    "bf.sub_once": lambda: bf.sub_once("abc", "z", "y", "label"),
}
out = {"optimize": sys.flags.optimize}
for key, probe in probes.items():
    try:
        probe()
        out[key] = "accepted"
    except Exception as exc:
        out[key] = type(exc).__name__ + ": " + str(exc)
print(json.dumps(out))
"""
SHELL_SCRIPTS = (
    support.SKILL / "upload_prs.sh",
    support.LAND / "sf_land_child.sh",
    support.LAND / "sf_wait_green.sh",
    support.LAND / "sf_stack_status.sh",
)
ENV = Path("/usr/bin/env")


class OptimizedInterpreterTests(unittest.TestCase):
    """The checks are explicit raises, so ``python -O`` still refuses."""

    def test_checks_refuse_under_python_dash_o(self):
        with tempfile.TemporaryDirectory() as home:
            support.write_work_files(Path(home))
            env = {**os.environ, "HOME": home}
            completed = subprocess.run(
                [sys.executable, "-O", "-c", OPTIMIZED_PROBE, str(support.REPO)],
                capture_output=True, text=True, env=env, cwd=home, check=False, timeout=120,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        out = json.loads(completed.stdout)
        self.assertEqual(out["optimize"], 1)
        self.assertEqual(out["bare assert"], "accepted")  # proves -O really stripped asserts
        self.assertEqual(out["bb.round_key"], "BundleCheckError: batch-final.jsonl")
        self.assertEqual(out["bb.census"], "BundleCheckError: ids not unique")
        self.assertEqual(out["bf.census"], "FixBundleCheckError: ids not unique")
        self.assertEqual(out["bf.sub_once"], "FixBundleCheckError: ('label', 0)")


class ShellScriptTests(unittest.TestCase):
    def test_shebang_is_the_first_line(self):
        for script in SHELL_SCRIPTS:
            with self.subTest(script=script.name):
                first = script.read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first, "#!/usr/bin/env bash")

    @unittest.skipUnless(ENV.exists() and shutil.which("bash"), "no /usr/bin/env bash")
    def test_scripts_parse_under_their_shebang_interpreter(self):
        for script in SHELL_SCRIPTS:
            with self.subTest(script=script.name):
                parsed = subprocess.run(
                    ["/usr/bin/env", "bash", "-n", str(script)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(parsed.returncode, 0, parsed.stderr)


if __name__ == "__main__":
    unittest.main()
