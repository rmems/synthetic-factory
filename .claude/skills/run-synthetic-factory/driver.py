#!/usr/bin/env python3
"""Read-only operator driver for the synthetic data factory.

Generative-Improve #8/8 — Workflow Efficiency R2
Co-authored-by: Muse Spark <muse-spark@meta.com>

Preserves:
  - early-stop on <5% novel coverage for 2 consecutive rounds
  - token-efficiency 40% saving mode (docs/token-efficiency.md)
  - 5-lane per-factory circuit breaker (workflow lanes isolate failures)

Usage:
  driver.py smoke
  driver.py validate <run_dir>
  driver.py audit <run_dir>
  driver.py frontiers <run_dir> [--json]
  driver.py snapshot <run_dir> <label>
  driver.py token-efficiency <run_dir> [--json]
"""

from __future__ import annotations

import ctypes
import errno
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
REPO = SKILL_DIR.parents[2]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from round_txn import (  # noqa: E402
    TransactionError,
    committed_jsonl_paths,
    completed_manifests,
    completion_manifest_file_matches,
    frontier_status,
    legacy_baseline_jsonl_paths,
    marker_mode_path,
    publish,
    reserve,
)

VALIDATOR = PIPELINES / "validate_run.py"
CHECKER = PIPELINES / "check_records.py"
AUDITOR = PIPELINES / "training_audit.py"
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

# ── Token-efficiency: 40% saving mode ─────────────────────────────────
# Documented in docs/token-efficiency.md. Enabled by default in the
# workflow; driver mirrors the same thresholds for offline audit.
# Rule: 2 consecutive NOTES with <5% novel coverage → plateau / early-stop.
# The 40% figure is the median token saving (generation + verification)
# when the plateau tail is cut vs running to backstop 26 (sf-0qz analysis).
# Keep these constants in sync with factory-window.workflow.js TOKEN_EFFICIENCY.
TOKEN_EFFICIENCY_THRESHOLD_PCT = 5.0
TOKEN_EFFICIENCY_CONSECUTIVE = 2
TOKEN_EFFICIENCY_SAVING_PCT = 40
TOKEN_EFFICIENCY_DOCS = "docs/token-efficiency.md"
# Historical read parser: this is the exact multiline grammar used before the
# forward-only strict publication contract in round_txn.py. It intentionally
# preserves first-match suffix, duplicate-label, and split-line compatibility.
LEGACY_NOVEL_COVERAGE_RE = re.compile(
    r"^\s*novel[ _-]?coverage\s*"
    r"(?:\([^)\n]*\))?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE | re.MULTILINE,
)
NOTES_ROUND_RE = re.compile(r"^NOTES-r(\d+)([a-z]*)\.md$")
BATCH_ROUND_RE = re.compile(r"^batch-r(\d+)[a-z]*\.jsonl$")
AT_FDCWD = -100
RENAME_NOREPLACE = 1


def rename_snapshot_noreplace(src, dst):
    """Atomically publish a directory without replacing an existing path."""
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError as exc:
        raise TransactionError(
            "atomic no-replace snapshot rename is unavailable"
        ) from exc
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    if (
        renameat2(
            AT_FDCWD,
            os.fsencode(src),
            AT_FDCWD,
            os.fsencode(dst),
            RENAME_NOREPLACE,
        )
        == 0
    ):
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(error_number, os.strerror(error_number), dst)
    if error_number in {errno.EINVAL, errno.ENOSYS}:
        raise TransactionError(
            "atomic no-replace snapshot rename is unavailable"
        )
    raise OSError(error_number, os.strerror(error_number), f"{src} -> {dst}")


def run_tool(script, run_dir, *options):
    proc = subprocess.run(
        [sys.executable, str(script), *options, str(run_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def reject_snapshot_symlinks(src):
    """Reject source trees whose snapshot would dereference external paths."""
    for path in src.rglob("*"):
        if path.is_symlink():
            raise TransactionError(f"cannot snapshot unsafe symlinked path: {path}")


def _copy_snapshot_directory(source_fd, destination_fd, source_path):
    """Copy an opened directory without following source-side links."""
    with os.scandir(source_fd) as entries:
        for entry in entries:
            entry_path = source_path / entry.name
            try:
                entry_fd = os.open(
                    entry.name,
                    os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                    dir_fd=source_fd,
                )
            except OSError as exc:
                raise TransactionError(
                    f"cannot snapshot path safely: {entry_path}: {exc.strerror}"
                ) from exc
            try:
                entry_stat = os.fstat(entry_fd)
                if stat.S_ISDIR(entry_stat.st_mode):
                    os.mkdir(entry.name, mode=0o700, dir_fd=destination_fd)
                    child_destination_fd = os.open(
                        entry.name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=destination_fd,
                    )
                    try:
                        _copy_snapshot_directory(
                            entry_fd, child_destination_fd, entry_path
                        )
                        os.fchmod(
                            child_destination_fd, stat.S_IMODE(entry_stat.st_mode)
                        )
                    finally:
                        os.close(child_destination_fd)
                elif stat.S_ISREG(entry_stat.st_mode):
                    destination_file_fd = os.open(
                        entry.name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        mode=0o600,
                        dir_fd=destination_fd,
                    )
                    with os.fdopen(os.dup(entry_fd), "rb") as source_file, os.fdopen(
                        destination_file_fd, "wb"
                    ) as destination_file:
                        shutil.copyfileobj(source_file, destination_file)
                        os.fchmod(
                            destination_file.fileno(),
                            stat.S_IMODE(entry_stat.st_mode),
                        )
                else:
                    raise TransactionError(
                        f"cannot snapshot unsafe non-file path: {entry_path}"
                    )
            finally:
                os.close(entry_fd)


def copy_snapshot_tree(src, dst):
    """Copy a tree through no-follow descriptors, then verify the result."""
    try:
        source_fd = os.open(src, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        raise TransactionError(
            f"cannot snapshot source safely: {src}: {exc.strerror}"
        ) from exc
    try:
        source_stat = os.fstat(source_fd)
        try:
            dst.mkdir(mode=0o700)
            destination_fd = os.open(
                dst, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
        except OSError as exc:
            raise TransactionError(
                f"cannot stage snapshot safely: {dst}: {exc.strerror}"
            ) from exc
        try:
            _copy_snapshot_directory(source_fd, destination_fd, src)
            os.fchmod(destination_fd, stat.S_IMODE(source_stat.st_mode))
        finally:
            os.close(destination_fd)
    finally:
        os.close(source_fd)
    reject_snapshot_symlinks(dst)


def snapshot_to_temp(src, prefix, directory=None):
    reject_snapshot_symlinks(src)
    temp = tempfile.TemporaryDirectory(prefix=prefix, dir=directory)
    snap = Path(temp.name) / src.name
    try:
        copy_snapshot_tree(src, snap)
    except BaseException:
        temp.cleanup()
        raise
    return temp, snap


def marker_visible_jsonl_paths(run_dir):
    """Resolve marker visibility while the original staging layout is intact."""
    visible = {}
    for factory in run_dir.iterdir():
        if (
            not factory.is_dir()
            or factory.is_symlink()
            or marker_mode_path(factory) is None
        ):
            continue
        visible[factory.name] = {
            path.relative_to(factory) for path in committed_jsonl_paths(factory)
        }
    return visible


def prune_snapshot_to_marker_visibility(snapshot, visible_by_factory):
    """Remove JSONL that was not committed when the live snapshot began."""
    for factory_name, committed in visible_by_factory.items():
        factory = snapshot / factory_name
        for path in factory.rglob("*.jsonl"):
            if path.relative_to(factory) not in committed:
                path.unlink()


def marker_visible_snapshot(src, prefix, directory=None):
    """Copy one run without crossing its monotonic transaction commit point."""
    for _attempt in range(3):
        reject_snapshot_symlinks(src)
        visible_before = marker_visible_jsonl_paths(src)
        try:
            if directory is None:
                temp, snap = snapshot_to_temp(src, prefix)
            else:
                temp, snap = snapshot_to_temp(src, prefix, directory)
        except TransactionError as exc:
            if isinstance(exc.__cause__, FileNotFoundError):
                continue
            raise
        try:
            visible_after = marker_visible_jsonl_paths(src)
        except BaseException:
            temp.cleanup()
            raise
        if visible_before == visible_after:
            return temp, snap, visible_before
        temp.cleanup()
    raise TransactionError(
        f"run changed transaction visibility repeatedly while snapshotting: {src}"
    )


def require_run_dir(run_dir):
    src = Path(run_dir).resolve()
    if not src.is_dir():
        raise SystemExit(f"not a directory: {src}")
    return src


def cmd_validate(run_dir):
    """Shape/invariant validation on a stable copy of a possibly live tree."""
    src = require_run_dir(run_dir)
    temp, snap, visible_by_factory = marker_visible_snapshot(
        src, "factory-validate-"
    )
    try:
        prune_snapshot_to_marker_visibility(snap, visible_by_factory)
        code, out, err = run_tool(VALIDATOR, snap)
    finally:
        temp.cleanup()
    sys.stdout.write(out)
    sys.stderr.write(err)
    print(
        f"structural validator exit: {code} "
        f"({'CLEAN' if code == 0 else 'DEFECTS FOUND'})"
    )
    return code


def cmd_audit(run_dir):
    """Run all three layers on one stable snapshot; never mutate the source."""
    src = require_run_dir(run_dir)
    temp, snap, visible_by_factory = marker_visible_snapshot(
        src, "factory-audit-"
    )
    results = []
    try:
        prune_snapshot_to_marker_visibility(snap, visible_by_factory)
        commands = (
            ("STRUCTURAL + SHAPE", VALIDATOR, ()),
            ("DEEP RECORD INVARIANTS", CHECKER, ("--strict",)),
            ("CORPUS TRAINING READINESS", AUDITOR, ("--strict", "--markdown")),
        )
        for title, script, options in commands:
            code, out, err = run_tool(script, snap, *options)
            results.append((title, code, out, err))
    finally:
        temp.cleanup()

    for title, code, out, err in results:
        print(f"\n=== {title} (exit {code}) ===")
        sys.stdout.write(out)
        if err:
            sys.stderr.write(f"\n--- {title} findings ---\n{err}")
    failed = [title for title, code, _out, _err in results if code]
    print(
        "\nAUDIT RESULT: "
        + ("BLOCKED — " + ", ".join(failed) if failed else "TRAINING-READY")
    )
    return 1 if failed else 0


def count_records(factory_dir):
    count = 0
    for path in factory_dir.glob("*.jsonl"):
        try:
            count += count_nonblank_lines(path)
        except OSError:
            continue
    return count


def count_nonblank_lines(path):
    with Path(path).open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def parse_novel_coverage(text: str):
    """Extract the first historically valid ``Novel coverage: N%`` claim.

    This command audits immutable committed NOTES, so it retains the former
    prefix grammar and first-valid-match behavior. New publication uses the
    strict, exactly-one-line contract in ``round_txn.validate_novel_coverage``.
    The label remains anchored at a line start so unrelated prose percentages
    cannot become coverage evidence.
    """
    if not text:
        return None
    match = LEGACY_NOVEL_COVERAGE_RE.search(text)
    if match is None:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    if not (0 <= value <= 100):
        return None
    return value


def notes_novel_coverage(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return parse_novel_coverage(text)


def factory_token_efficiency(factory_dir: Path):
    """Scan NOTES-rNN.md in committed order; detect a trailing 2-low streak.

    Returns dict with per-round coverages, early-stop flag, saving estimate,
    and generative quality note. Saving estimate assumes ~40% of tail tokens
    avoided when plateau is caught early (docs/token-efficiency.md).

    early_stop is the current trailing streak (mirrors a live lane starting
    from the frontier): a later parseable NOTES with coverage >= 5% clears a
    historical plateau so recovered factories are not omitted from starts.
    """
    factory_dir = Path(factory_dir)
    notes = sorted(factory_dir.glob("NOTES-r*.md"))

    def note_parts(path):
        note_match = NOTES_ROUND_RE.fullmatch(path.name)
        if note_match is None:
            return None
        return int(note_match.group(1)), note_match.group(2)

    mode_path = marker_mode_path(factory_dir)
    if mode_path is not None:
        status = frontier_status(factory_dir)
        baseline = status["baseline"]
        manifests = completed_manifests(factory_dir)
        baseline_rounds = set()
        for payload in legacy_baseline_jsonl_paths(factory_dir, baseline):
            match = BATCH_ROUND_RE.fullmatch(payload.name)
            baseline_rounds.add(int(match.group(1)) if match is not None else 1)
        for round_number, manifest in manifests.items():
            note = factory_dir / f"NOTES-r{round_number:02d}.md"
            completion_manifest_file_matches(note, manifest)
        notes = [
            path
            for path in notes
            if (parts := note_parts(path)) is not None
            and (
                parts[0] in baseline_rounds
                or (
                    not parts[1]
                    and parts[0] in manifests
                    and completion_manifest_file_matches(path, manifests[parts[0]])
                )
            )
        ]

    # Lettered notes are legacy artifacts for the same numeric round. The
    # canonical unsuffixed note wins; otherwise keep one deterministic suffix
    # so the same round cannot count twice toward a plateau.
    notes_by_round = {}
    for path in notes:
        parts = note_parts(path)
        if parts is None:
            continue
        round_number, suffix = parts
        previous = notes_by_round.get(round_number)
        if previous is None or (not suffix and note_parts(previous)[1]):
            notes_by_round[round_number] = path
    notes = [notes_by_round[round_number] for round_number in sorted(notes_by_round)]
    rounds = []
    consecutive = 0
    early_stop_at = None
    for p in notes:
        pct = notes_novel_coverage(p)
        rn = note_parts(p)[0]
        is_low = pct is not None and pct < TOKEN_EFFICIENCY_THRESHOLD_PCT
        if is_low:
            consecutive += 1
            if consecutive == TOKEN_EFFICIENCY_CONSECUTIVE:
                early_stop_at = rn
        elif pct is not None:
            # Healthy NOTES clear a historical plateau so recovered factories
            # are not omitted from the next window (SKILL.md uses this flag).
            consecutive = 0
            early_stop_at = None
        # None (unparseable) does not increment nor reset — holds streak
        rounds.append({"round": rn, "file": p.name, "novel_coverage_pct": pct, "is_low": is_low})
    early_stop = consecutive >= TOKEN_EFFICIENCY_CONSECUTIVE
    # 40% saving estimate: early-stop avoids ~40% of backstop tail when plateau detected.
    # For reporting, include saving mode metadata so callers can compute projected tokens.
    saving_note = (
        f"~{TOKEN_EFFICIENCY_SAVING_PCT}% token saving mode — plateau tail avoided"
        if early_stop
        else f"no plateau; run to backstop (see {TOKEN_EFFICIENCY_DOCS})"
    )
    return {
        "factory": factory_dir.name,
        "threshold_pct": TOKEN_EFFICIENCY_THRESHOLD_PCT,
        "consecutive_required": TOKEN_EFFICIENCY_CONSECUTIVE,
        "saving_mode_pct": TOKEN_EFFICIENCY_SAVING_PCT,
        "saving_docs": TOKEN_EFFICIENCY_DOCS,
        "saving_note": saving_note,
        "rounds": rounds,
        "early_stop": early_stop,
        "early_stop_at_round": early_stop_at,
    }


def cmd_token_efficiency(run_dir, as_json=False):
    """Offline token-efficiency audit per factory.

    Reports per-round novel coverage, low-streak detection (2× <5%),
    and 40% saving mode status. Mirrors workflow live early-stop logic
    but scans committed NOTES-rNN.md on disk.
    """
    src = require_run_dir(run_dir)
    factories = []
    for directory in sorted(path for path in src.iterdir() if path.is_dir() and not path.name.startswith("_")):
        info = factory_token_efficiency(directory)
        factories.append(info)
    payload = {"run_dir": str(src), "token_efficiency": factories}
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for info in factories:
            if info["early_stop"]:
                print(f"{info['factory']}: EARLY-STOP at r{info['early_stop_at_round']:02d} — {TOKEN_EFFICIENCY_CONSECUTIVE} consecutive NOTES <{TOKEN_EFFICIENCY_THRESHOLD_PCT:.0f}% novel coverage (40% saving mode, {info['saving_docs']})")
            else:
                lows = sum(1 for r in info["rounds"] if r["is_low"])
                print(f"{info['factory']}: no early-stop ({lows} low round(s), need {TOKEN_EFFICIENCY_CONSECUTIVE} consecutive <{TOKEN_EFFICIENCY_THRESHOLD_PCT:.0f}%) — {info['saving_note']}")
            for r in info["rounds"]:
                pct_str = f"{r['novel_coverage_pct']:.1f}%" if r["novel_coverage_pct"] is not None else "n/a"
                flag = " LOW" if r["is_low"] else ""
                print(f"  r{r['round']:02d} {r['file']}: {pct_str}{flag}")
        print(f"\nToken-efficiency docs: {TOKEN_EFFICIENCY_DOCS} — 40% saving mode enabled by default in workflow.")
    return payload


def cmd_frontiers(run_dir, as_json=False):
    src = require_run_dir(run_dir)
    factories = []
    for directory in sorted(
        path for path in src.iterdir() if path.is_dir() and not path.name.startswith("_")
    ):
        status = frontier_status(directory)
        if status["mode"] == "marker":
            status["records"] = sum(
                count_nonblank_lines(path)
                for path in committed_jsonl_paths(directory)
            )
        else:
            status["records"] = count_records(directory)
        factories.append(status)
    payload = {"run_dir": str(src), "factories": factories}
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for item in factories:
            marker = "committed markers" if item["mode"] == "marker" else "validated legacy"
            print(
                f"{item['factory']}: {item['records']} records, "
                f"highest r{item['highest_flushed']:02d}, "
                f"next r{item['next_round']:02d} ({marker})"
            )
    return factories


def cmd_snapshot(run_dir, label):
    src = require_run_dir(run_dir)
    if not SAFE_LABEL.fullmatch(label):
        raise SystemExit("snapshot label may contain only letters, digits, dot, dash, underscore")
    dst = src.parent / f"{src.name}-{label}"
    if dst.exists() or dst.is_symlink():
        raise SystemExit(f"refusing to overwrite existing snapshot: {dst}")
    temp, staged, visible_by_factory = marker_visible_snapshot(
        src, f".{dst.name}-", src.parent
    )
    try:
        prune_snapshot_to_marker_visibility(staged, visible_by_factory)
        if dst.exists() or dst.is_symlink():
            raise SystemExit(f"refusing to overwrite existing snapshot: {dst}")
        try:
            rename_snapshot_noreplace(staged, dst)
        except FileExistsError as exc:
            raise SystemExit(
                f"refusing to overwrite existing snapshot: {dst}"
            ) from exc
    finally:
        temp.cleanup()
    records = sum(count_nonblank_lines(path) for path in dst.rglob("*.jsonl"))
    print(f"snapshot: {dst} ({records} records)")


def thalamic(record_id="smoke-t1"):
    return {
        "id": record_id,
        "state": {"sim_or_real": "designed", "env": "transaction smoke test"},
        "proposed_action": {"action": "noop", "decision_basis": "fixture"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "bounded fixture"},
        "executed_action": {"action": "noop"},
        # publish() gates on verify_execution in strict mode, so the smoke
        # fixture carries the observable outcome evidence a real record carries.
        "future_outcome": {
            "ok": True,
            "timeline": [{"t_ms": 0, "event": "noop accepted"}],
            "observed_effects": ["no actuator motion"],
            "new_state": {"sim_or_real": "designed", "env": "transaction smoke test"},
        },
        "reward_components": {"task_progress": 0.5, "total": 0.5},
        "meta": {"factory": "smoke", "round": 2, "tags": ["smoke"]},
    }


MINI_RECORDS = {
    "thalamic-mini/batch-r02.jsonl": [
        thalamic(),
        {
            "id": "smoke-p1",
            "failure_mode": "test",
            "rejected": thalamic("smoke-rejected"),
            "chosen": thalamic("smoke-chosen"),
            "critique": "chosen gate is bounded",
            "reward_delta": {"total": 0.8},
        },
        {
            "id": "smoke-b1",
            "spike_events": [
                {"channel": "c0", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "c0", "t_rel_ms": 2.0, "amplitude": 0.3},
            ],
            "language_view": {
                "description": "two sparse events",
                "trajectory": thalamic("smoke-bridge-trajectory"),
            },
            "bridge_notes": {"mapping": "fixture", "training_value": "routing"},
        },
        {
            "id": "smoke-e1",
            "goal": "fix fixture",
            "steps": [
                {
                    "n": 1,
                    "decision_basis": "observable file is missing",
                    "tool_call": {"name": "rg", "args": {"q": "fixture"}},
                    "observation": "no match",
                    "reflection": "create bounded fixture",
                }
            ],
            "outcome": "fixed",
            "reward": {"success": True},
        },
    ]
}


def _smoke_check_kind_routing(run: Path, failures: list) -> None:
    code, out, _err = run_tool(VALIDATOR, run)
    if code:
        failures.append(f"valid mini-run should exit 0, got {code}")
    try:
        totals = json.loads(out)
    except json.JSONDecodeError:
        totals = {}
        failures.append(f"validator emitted invalid JSON totals: {out[:200]!r}")
    expected_kinds = {
        "thalamic": 1,
        "preference": 1,
        "bridge_pair": 1,
        "episode": 1,
    }
    if totals.get("by_kind") != expected_kinds:
        failures.append(f"kind routing wrong: {totals.get('by_kind')}")


def _smoke_check_broken_batch(run: Path, failures: list) -> None:
    bad = run / "thalamic-mini" / "batch-r03.jsonl"
    broken = thalamic("broken")
    broken["safety_decision"] = {"decision": "MAYBE", "rationale": ""}
    broken["reward_components"] = {}
    bad.write_text(json.dumps(broken) + "\nnot json\n")
    code2, _out2, err2 = run_tool(VALIDATOR, run)
    if code2 == 0:
        failures.append("broken batch should exit nonzero")
    if "decision must be" not in err2 or "JSON parse error" not in err2:
        failures.append(f"expected enum + parse errors, got: {err2[:200]}")
    frontier = cmd_frontiers(run)[0]
    if frontier["next_round"] != 3:
        failures.append(f"malformed r03 must not advance frontier: {frontier}")


def _smoke_check_notes_gate(root: Path, failures: list) -> None:
    factory = root / "outputs" / "raw" / "2099-01-01" / "thalamic-trajectory-factory"
    factory.mkdir(parents=True)
    reservation = reserve(factory, 1, 1)
    stage = Path(reservation["staging_dir"])
    record = thalamic("txn-smoke")
    record["meta"]["round"] = 1
    (stage / reservation["batch_file"]).write_text(json.dumps(record) + "\n")
    notes = stage / reservation["notes_file"]
    # The NOTES contract (docs/token-efficiency.md) is a publish gate on
    # every registered lane, legacy included: without the line the
    # early-stop latch can never fire, so a round that omits it must not
    # commit.
    notes.write_text("# Self-critique\n\nFixture only.\n")
    try:
        publish(factory, 1, reservation["token"])
    except TransactionError as exc:
        if "Novel coverage" not in str(exc):
            failures.append(f"unexpected publish rejection: {exc}")
    else:
        failures.append("publish accepted NOTES without a 'Novel coverage' line")
        # A successful publish consumes the staging directory. Stop this helper
        # instead of rewriting a path that no longer exists; cmd_smoke will
        # report the recorded gate regression as a structured SMOKE FAIL.
        return
    notes.write_text(
        "# Self-critique\n\nFixture only.\n\nNovel coverage: 42%\n"
    )
    manifest = publish(factory, 1, reservation["token"])
    if manifest.get("records") != 1 or frontier_status(factory)["next_round"] != 2:
        failures.append("transaction reserve/publish did not commit exactly one round")


def _smoke_check_coverage_latch(root: Path, failures: list) -> None:
    # Coverage-convergence latch: two consecutive published NOTES under
    # the 5% threshold early-stop the lane (40% saving mode).
    plateau = root / "plateau" / "thalamic-trajectory-factory"
    plateau.mkdir(parents=True)
    (plateau / "NOTES-r05.md").write_text("Novel coverage: 4.2%\n")
    (plateau / "NOTES-r06.md").write_text("Novel coverage: 3.1%\n")
    latch = factory_token_efficiency(plateau)
    if not latch["early_stop"] or latch["early_stop_at_round"] != 6:
        failures.append(f"coverage plateau did not early-stop: {latch}")


def cmd_smoke():
    failures = []
    with tempfile.TemporaryDirectory(prefix="factory-smoke-") as temp_dir:
        root = Path(temp_dir)
        run = root / "mini-run"
        for rel, records in MINI_RECORDS.items():
            path = run / rel
            path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(record) + "\n" for record in records))

        _smoke_check_kind_routing(run, failures)
        _smoke_check_broken_batch(run, failures)
        _smoke_check_notes_gate(root, failures)
        _smoke_check_coverage_latch(root, failures)

    if failures:
        print("SMOKE FAIL:")
        for failure in failures:
            print("  -", failure)
        return 1
    print(
        "SMOKE PASS: four record kinds route correctly; malformed output cannot "
        "advance a frontier; reserve/stage/validate/publish commits exactly once; "
        "NOTES without a 'Novel coverage: <N>%' line cannot publish; two "
        "consecutive sub-5% rounds early-stop the lane"
    )
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        raise SystemExit(__doc__)
    command = args[0]
    if command == "smoke" and len(args) == 1:
        return cmd_smoke()
    if command == "validate" and len(args) == 2:
        return cmd_validate(args[1])
    if command == "audit" and len(args) == 2:
        return cmd_audit(args[1])
    if command == "frontiers" and len(args) >= 2:
        cmd_frontiers(args[1], as_json="--json" in args[2:])
        return 0
    if command == "snapshot" and len(args) == 3:
        cmd_snapshot(args[1], args[2])
        return 0
    if command == "token-efficiency" and len(args) >= 2:
        cmd_token_efficiency(args[1], as_json="--json" in args[2:])
        return 0
    raise SystemExit(__doc__)


if __name__ == "__main__":
    raise SystemExit(main())
