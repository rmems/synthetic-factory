"""Six-lane fixture backed by reviewed, executed procedural source bytes."""

import copy
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

from tests.gate_fixture import GateFixture, _INTEGRATION_PLAN, _lane_manifest_entry
from tests.test_curate_identity import identity
from tests.gate_fixture import _thalamic
import curate_rewards
from code_repair import publication


class ProceduralGateFixture(GateFixture):
    """Pass-through lanes around the real identity transform and completed batch."""

    def __init__(self, root, generated):
        self.root = Path(root)
        self.source_run = self.root / "evidence/outputs/raw/2099-01-01"
        factory = self.source_run / "python-function-repair-factory"
        factory.mkdir(parents=True)
        publication.publish_run(publication.PublishRequest(generated, factory, 1))
        excluded = self.source_run / "thalamic-trajectory-factory/excluded.jsonl"
        excluded.parent.mkdir()
        self.excluded_record = _thalamic("excluded-unreviewed")
        self.excluded_record["factory"] = "unreviewed-source"
        excluded.write_text(json.dumps(self.excluded_record) + "\n")
        self.excluded_path = excluded.relative_to(self.source_run).as_posix()
        self.cleaned = self.root / "cleaned-v1"
        self.curated = self.root / "curated-v1"
        plan = copy.deepcopy(_INTEGRATION_PLAN)
        plan["source_run"] = self.source_run.relative_to(self.root).as_posix()
        self.manifest_paths = []
        for lane in plan["lanes"]:
            self._write_lane(lane)
        self.plan_path = self.root / "plan.json"
        self.plan_path.write_text(json.dumps(plan))

    @classmethod
    def copy_template(cls, template, root):
        """Copy actual sealed publication evidence without re-running the oracle."""
        root = Path(root)
        shutil.copytree(template.root, root, dirs_exist_ok=True)
        fixture = cls.__new__(cls)
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


def prepare_gate_template(test_case):
    """Create one real immutable fixture per test class, then copy it per test."""
    from tests.code_repair_admission_test_support import build_generated_admission_evidence
    _, generated, _, _ = build_generated_admission_evidence(test_case)
    scratch = tempfile.TemporaryDirectory(prefix="procedural-gate-template-")
    test_case.addClassCleanup(scratch.cleanup)
    test_case.generated = generated
    test_case.template = ProceduralGateFixture(scratch.name, generated)
