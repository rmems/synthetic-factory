"""Six-lane fixture backed by reviewed, executed procedural source bytes."""

import atexit
import copy
import functools
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from tests.gate_fixture import GateFixture, _INTEGRATION_PLAN, _lane_manifest_entry
from tests.test_curate_identity import identity
from tests.gate_fixture import _thalamic
import curate_rewards


class ProceduralGateFixture(GateFixture):
    """Pass-through lanes around the real identity transform and completed batch.

    The base constructor lays out the synthetic six-lane scenario, which this
    fixture replaces: instances come from :meth:`build` or :meth:`copy_template`.
    """

    @classmethod
    def _unconstructed(cls):
        """An instance that skips the base scenario constructor (neither class defines __new__)."""
        return object.__new__(cls)

    @classmethod
    def build(cls, root, published_factory):
        """Lay the six lanes over a private copy of the published procedural round."""
        fixture = cls._unconstructed()
        fixture.root = Path(root)
        fixture.source_run = fixture.root / "evidence/outputs/raw/2099-01-01"
        published_factory(fixture.source_run)
        excluded = fixture.source_run / "thalamic-trajectory-factory/excluded.jsonl"
        excluded.parent.mkdir()
        fixture.excluded_record = _thalamic("excluded-unreviewed")
        fixture.excluded_record["factory"] = "unreviewed-source"
        excluded.write_text(json.dumps(fixture.excluded_record) + "\n")
        fixture.excluded_path = excluded.relative_to(fixture.source_run).as_posix()
        fixture.cleaned = fixture.root / "cleaned-v1"
        fixture.curated = fixture.root / "curated-v1"
        plan = copy.deepcopy(_INTEGRATION_PLAN)
        plan["source_run"] = fixture.source_run.relative_to(fixture.root).as_posix()
        fixture.manifest_paths = []
        for lane in plan["lanes"]:
            fixture._write_lane(lane)
        fixture.plan_path = fixture.root / "plan.json"
        fixture.plan_path.write_text(json.dumps(plan))
        return fixture

    @classmethod
    def copy_template(cls, template, root):
        """Copy actual sealed publication evidence without re-running the oracle."""
        root = Path(root)
        shutil.copytree(template.root, root, dirs_exist_ok=True)
        fixture = cls._unconstructed()
        fixture.root = root
        for name in ("source_run", "cleaned", "curated", "plan_path"):
            setattr(fixture, name, root / getattr(template, name).relative_to(template.root))
        fixture.manifest_paths = [root / path.relative_to(template.root) for path in template.manifest_paths]
        return fixture

    def _write_lane(self, lane):
        destination = self.root / lane["outputs"]
        if lane["transform"] == "curate_identity":
            identity.write_run(self.source_run, destination)
            lane["version"] = identity.TRANSFORM_VERSION
            lane["manifest"] = f"{lane['outputs']}/IDENTITY-MANIFEST.json"
        else:
            destination.mkdir()
            entries = []
            for path in sorted(self.source_run.rglob("*.jsonl")):
                relative = path.relative_to(self.source_run)
                payload = path.read_bytes()
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if relative.as_posix() != self.excluded_path:
                    target.write_bytes(payload)
                entries.extend(self._entries(payload, relative.as_posix(), lane))
            (destination / "manifest.json").write_text(json.dumps(entries))
            if lane["transform"] == "reward_ontology":
                _, sidecar = curate_rewards.curate_record(
                    self.excluded_record, source_path=self.excluded_path, source_line=1,
                )
                (destination / "reward-sidecars.jsonl").write_text(json.dumps(sidecar) + "\n")
        self.manifest_paths.append(self.root / lane["manifest"])

    def _entries(self, payload, relative, lane):
        for line, physical in enumerate(payload.split(b"\n"), 1):
            if physical.strip():
                excluded = relative == self.excluded_path
                yield _lane_manifest_entry(
                    "excluded" if excluded else "retained", line,
                    ["UNREVIEWED_SOURCE"] if excluded else [], transform=lane["transform"], version=lane["version"],
                    source_path=relative, record=None if excluded else json.loads(physical),
                    source_hash=hashlib.sha256(physical).hexdigest(),
                )


class IntegratedGateTemplate:
    """One real integration per class; each test restores a private copy of it.

    The integration manifest binds the absolute cleaned and source-run paths,
    so an integrated tree is only valid where it was integrated. Each test gets
    a byte-identical private copy back at that path instead of re-integrating.
    """

    def __init__(self, template, scratch):
        self.workspace = Path(scratch) / "fixture"
        fixture = ProceduralGateFixture.copy_template(template, self.workspace)
        self.integrate_status = fixture.integrate()
        self.pristine = ProceduralGateFixture.copy_template(fixture, Path(scratch) / "integrated")
        shutil.rmtree(self.workspace)

    def restore(self, test_case):
        """The integrated fixture at its integration path, removed after the test."""
        test_case.addCleanup(shutil.rmtree, self.workspace, True)
        return ProceduralGateFixture.copy_template(self.pristine, self.workspace)


@functools.cache
def _sealed_gate_template():
    """One real immutable fixture per process, over the shared published round."""
    from tests.code_repair_admission_test_support import copy_published_factory
    scratch = Path(tempfile.mkdtemp(prefix="procedural-gate-template-"))
    atexit.register(shutil.rmtree, scratch, True)
    return ProceduralGateFixture.build(scratch, copy_published_factory)


def prepare_gate_template(test_case):
    """Attach the shared gate template; each test copies it before any write."""
    test_case.template = _sealed_gate_template()


def prepare_integrated_template(test_case):
    """Attach the shared gate template and one integration of it for the class."""
    prepare_gate_template(test_case)
    scratch = tempfile.TemporaryDirectory(prefix="curate-gate-")
    test_case.addClassCleanup(scratch.cleanup)
    test_case.integrated = IntegratedGateTemplate(test_case.template, scratch.name)
