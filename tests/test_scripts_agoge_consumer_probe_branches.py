"""The Agoge consumer probe through its CLI, with Agoge-Forger, transformers and TRL faked.

None of the three is a dependency of this repository (the probe runs in
Agoge-Forger's own virtualenv), so each test installs minimal stand-ins in
``sys.modules`` for one ``main`` call. The stand-ins pin the probe's own work --
split agreement, label counting, revision pinning and the freeze gate -- not
Agoge's behaviour; ``tests/test_code_repair_probe.py`` covers the helpers.
"""

import contextlib
import hashlib
import io
import json
import runpy
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import agoge_consumer_probe as probe

PINNED = "a" * 40
CONFIG_PIN = "b" * 40
POLICY = {"seed": 7, "salt": "probe-test", "weights": {"train": 50, "validation": 50}}
UNPINNED = "ValueError: CONFIG_REVISION_PIN_REQUIRED_40_HEX: pass --tokenizer-revision"
PROMPTS = (("code-repair:one", "train", "fix"), ("code-repair:two", "validation", "repair"))
ROWS = tuple(
    {
        "canonical_id": canonical_id,
        "split": split,
        "text": prompt + probe.SEPARATOR + f"def {split}():\n    return 1\n",
        "completion_start_char": len(prompt + probe.SEPARATOR),
    }
    for canonical_id, split, prompt in PROMPTS
)
DECLARED_SPLITS = {row["canonical_id"]: row["split"] for row in ROWS}
GAPS = {k: v for k, v in probe.GAPS.items() if k != "NO_LOSS_MASKING_PROMPT_TOKENS_TRAINED"}


class _Mask(list):
    def sum(self):
        return sum(int(value) for value in self)


class _Labels(list):
    """A label row that compares elementwise, as the collator's tensor does."""

    def __ne__(self, other):
        return _Mask(value != other for value in self)


class _Collator:
    """Full-sequence labels as given; completion-only labels mask the prompt."""

    def __init__(self, pad_token_id, completion_only_loss):
        self.pad_token_id = pad_token_id
        self.completion_only_loss = completion_only_loss

    def __call__(self, samples):
        return {"labels": [self._labels(sample) for sample in samples]}

    def _labels(self, sample):
        if not self.completion_only_loss:
            return _Labels(sample["labels"])
        pairs = zip(sample["input_ids"], sample["completion_mask"], strict=True)
        return _Labels(token if active else -100 for token, active in pairs)


def _jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def _source_records(path, _identity, **_options):
    return (SimpleNamespace(member=SimpleNamespace(canonical_id=row["canonical_id"]))
            for row in _jsonl(path))


def _completion_tokens(row, _tokenizer, _max_length):
    """One token per character; the completion starts at the declared offset."""

    start, text = row["completion_start_char"], row["text"]
    return {
        "input_ids": [ord(char) for char in text],
        "completion_mask": [int(index >= start) for index in range(len(text))],
    }


def _module(name, **attributes):
    module = types.ModuleType(name)
    module.__dict__.update(attributes)
    return module


class _Manifest:
    """What ``materialize_split`` returns; the probe reports only its type name."""


class _FakeAgoge:
    """Stand-ins for the Agoge, transformers and TRL names the probe imports."""

    def __init__(self, assignment=None, config=None):
        self.assignment = DECLARED_SPLITS if assignment is None else assignment
        self.config = config
        self.materialized = []
        tokenizer = SimpleNamespace(pad_token_id=None, eos_token_id=0)
        self.from_pretrained = mock.Mock(return_value=tokenizer)

    def assign_records(self, records, _spec):
        splits = {}
        for index, record in enumerate(records):
            splits.setdefault(self.assignment[record.member.canonical_id], []).append(index)
        return splits

    def materialize_split(self, path, into, spec):
        self.materialized.append((path, into, vars(spec)))
        return _Manifest()

    def load_config(self, _path):
        return self.config

    def modules(self):
        """The fake modules by import name, ready for ``mock.patch.dict(sys.modules)``."""

        schema = dict.fromkeys(
            ("CanonicalIdentityPolicy", "SplitMaterializationSpec", "SplitPolicy"), SimpleNamespace
        )
        attributes = {
            "agoge_forger": {},
            "agoge_forger.config": {"load_config": self.load_config},
            "agoge_forger.datasets": {"iter_normalized_rows": _jsonl},
            "agoge_forger.split_materialize": {
                "iter_source_records": _source_records,
                "assign_records": self.assign_records,
                "materialize_split": self.materialize_split,
            },
            "agoge_forger.split_schema": schema,
            "agoge_forger.train": {},
            "agoge_forger.train.completion": {"completion_tokens": _completion_tokens},
            "agoge_forger.train.preflight": {
                "validate_dataset_text_field_in_source": mock.Mock(return_value=None),
            },
            "transformers": {
                "AutoTokenizer": SimpleNamespace(from_pretrained=self.from_pretrained),
            },
            "trl": {},
            "trl.trainer": {},
            "trl.trainer.sft_trainer": {"DataCollatorForLanguageModeling": _Collator},
        }
        return {name: _module(name, **values) for name, values in attributes.items()}


def _config(revision, completion_only_loss=False):
    training = SimpleNamespace(max_seq_length=64, completion_only_loss=completion_only_loss)
    return SimpleNamespace(model_id="local/model", revision=revision, training=training)


def _export(root, policy):
    """Write the two-row export and a manifest that binds its bytes and count."""

    records = root / "code_repair_v1.jsonl"
    records.write_text("".join(json.dumps(row) + "\n" for row in ROWS), encoding="utf-8")
    manifest = root / "MANIFEST.json"
    manifest.write_text(json.dumps({
        "files": {"agoge/code_repair_v1.jsonl": hashlib.sha256(records.read_bytes()).hexdigest()},
        "tables": {"dispositions": {"exported": len(ROWS)}},
        "run": {"split_policy": policy},
    }), encoding="utf-8")
    return [str(records), "--manifest", str(manifest)]


def _run(fake, argv):
    stdout = io.StringIO()
    with (
        mock.patch.dict(sys.modules, fake.modules()),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        code = probe.main(argv)
    return code, stdout.getvalue()


def _split_runs(policy, assignment):
    """The JSON report, its exit code, the human line, and the export's digest."""

    with tempfile.TemporaryDirectory() as td:
        argv = _export(Path(td), policy)
        digest = hashlib.sha256(Path(argv[0]).read_bytes()).hexdigest()
        code, stdout = _run(_FakeAgoge(assignment), [*argv, "--json"])
        human = _run(_FakeAgoge(assignment), argv)
    return json.loads(stdout), code, human, digest


def _labels_run(fake, extra):
    """Run the probe with ``--config`` plus ``extra``; return the exit code and report."""

    with tempfile.TemporaryDirectory() as td:
        argv = [*_export(Path(td), POLICY), "--config", str(Path(td) / "agoge.yaml")]
        code, stdout = _run(fake, [*argv, *extra, "--json"])
    return code, json.loads(stdout)


def _row_labels(row):
    start, total = row["completion_start_char"], len(row["text"])
    return {
        "canonical_id": row["canonical_id"], "prompt_tokens": start,
        "completion_tokens": total - start, "total_tokens": total,
        "completion_tokens_surviving_truncation": total - start, "completion_truncated": False,
        "loss_tokens_full_sequence": total, "loss_tokens_completion_only": total - start,
        "prompt_tokens_receiving_loss_full_sequence": start,
        "prompt_tokens_receiving_loss_completion_only": 0,
    }


class ProbeSplitAgreement(unittest.TestCase):
    def test_agoge_assignment_is_compared_record_by_record(self):
        cases = (
            ("agoge reproduces the splits", POLICY, None, [],
             {"agree": True, "disagree": [], "agoge_counts": {"train": 1, "validation": 1}}),
            ("agoge moves one record", POLICY, dict.fromkeys(DECLARED_SPLITS, "train"),
             ["split_agreement"],
             {"agree": False, "disagree": ["code-repair:two"], "agoge_counts": {"train": 2}}),
            ("no split policy to compare", None, None, [],
             {"status": "not evaluated: no split policy"}),
        )
        for label, policy, assignment, failed, agreement in cases:
            with self.subTest(label):
                report, code, human, digest = _split_runs(policy, assignment)
                self.assertEqual(report, {
                    "rows": 2, "gaps": GAPS, "manifest": {"sha256": digest, "rows": 2},
                    "load": {"normalized_rows": 2, "frozen_split_records": 2},
                    "split_agreement": agreement, "failed_steps": failed, "passed": not failed,
                })
                self.assertEqual(code, 1 if failed else 0)
                line = f"passed={not failed} rows=2 failed_steps={','.join(failed) or 'none'}\n"
                self.assertEqual(human, (code, line))


class ProbeLabels(unittest.TestCase):
    def test_labels_are_counted_with_the_pinned_revision_from_local_files_only(self):
        cases = (
            ("command-line pin wins", ["--tokenizer-revision", PINNED], False, PINNED),
            ("config pin is the fallback", [], True, CONFIG_PIN),
        )
        for label, extra, completion_only, used in cases:
            fake = _FakeAgoge(config=_config(CONFIG_PIN, completion_only))
            with self.subTest(label):
                code, report = _labels_run(fake, extra)
                self.assertEqual((code, report["failed_steps"]), (0, []))
                self.assertEqual(report["labels"], {
                    "tokenizer": "local/model", "max_seq_length": 64,
                    "rows": [_row_labels(row) for row in ROWS], "completion_truncated_rows": 0,
                    "loss_mode_in_agoge": "completion_only" if completion_only else "full_sequence",
                })
                self.assertEqual(report["config"], {
                    "model_id": "local/model", "revision": used, "max_seq_length": 64,
                    "completion_only_loss": completion_only,
                })
                fake.from_pretrained.assert_called_once_with(
                    "local/model", revision=used, local_files_only=True)

    def test_an_unpinned_revision_fails_the_labels_step_before_any_tokenizer_loads(self):
        cases = (
            ("no pin anywhere", [], None),
            ("a branch name in the config", [], "main"),
            ("upper-case hex on the command line", ["--tokenizer-revision", "A" * 40], None),
        )
        for label, extra, config_revision in cases:
            fake = _FakeAgoge(config=_config(config_revision))
            with self.subTest(label):
                code, report = _labels_run(fake, extra)
                self.assertEqual((code, report["failed_steps"]), (1, ["labels"]))
                self.assertEqual(report["labels"], {"error": UNPINNED, "agree": False})
                self.assertEqual(report["config"], {})
                fake.from_pretrained.assert_not_called()


class ProbeFreeze(unittest.TestCase):
    def test_real_provenance_materializes_once_into_the_named_destination(self):
        fake = _FakeAgoge()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            destination = root / "frozen"
            argv = [
                *_export(root, POLICY), "--freeze-into", str(destination),
                "--source-revision", PINNED, "--dataset-version", "v1", "--json",
            ]
            code, stdout = _run(fake, argv)

        report = json.loads(stdout)
        self.assertEqual((code, report["failed_steps"]), (0, []))
        self.assertEqual(
            report["freeze"], {"output_dir": str(destination), "manifest_type": "_Manifest"}
        )
        self.assertEqual(len(fake.materialized), 1)
        records, into, spec = fake.materialized[0]
        self.assertEqual((records, into), (root / "code_repair_v1.jsonl", destination))
        self.assertEqual(vars(spec.pop("split_policy")), POLICY)
        self.assertEqual(spec, {
            "source_repository": "rmems/synthetic-factory", "source_revision": PINNED,
            "dataset_version": "v1", "source_path": probe.SOURCE_PATH,
        })


class ProbeEntryPoint(unittest.TestCase):
    def test_script_entry_point_exits_with_the_report_verdict(self):
        stdout = io.StringIO()
        script = str(Path(probe.__file__))
        with tempfile.TemporaryDirectory() as td:
            argv = _export(Path(td), POLICY)
            Path(argv[0]).write_text("{}\n", encoding="utf-8")
            with (
                mock.patch.object(sys, "argv", [Path(script).name, *argv]),
                mock.patch.object(sys, "path", list(sys.path)),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as exited,
            ):
                runpy.run_path(script, run_name="__main__")

        self.assertEqual(exited.exception.code, 1)
        self.assertEqual(stdout.getvalue(), "passed=False rows=1 failed_steps=manifest\n")


if __name__ == "__main__":
    unittest.main()
