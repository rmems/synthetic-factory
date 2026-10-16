# Written and run by Claude Fable 5.1 subagents during the 2026-09-04 Hub publication session
# (rmems/synthetic-factory). Kept as the harness for .claude/skills/publish-hub-research-run.
#!/usr/bin/env python3
"""Build the delta bundles that add the base-round batches omitted by the
mistaken "c supersedes base" selection of the 2026-09-02 SuperGrok Heavy
publication.

Reads: $HOME/tmp/publish-0902/current/<repo>/ (current Hub main, downloaded
today) and the immutable factory tree (byte source of every raw file).
Writes only: $HOME/tmp/publish-0902/fix/<repo>/ (delta bundle: changed or
added files only) and $HOME/tmp/publish-0902/run-fix/<factory>/ (gate tree
holding exactly the raw files that will be on the Hub after the PR).
"""

from __future__ import annotations

import collections
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, NamedTuple

REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import export_contract  # noqa: E402
import export_viewer  # noqa: E402
import rights_document  # noqa: E402
import strict_jsonl  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402  (verification only; not the writer)

ViewerRow = export_contract.ViewerRow

HOME = Path.home()
BASE = HOME / "tmp/publish-0902"
CURRENT = BASE / "current"
FIX = BASE / "fix"
RUN_FIX = BASE / "run-fix"
WORK = BASE / "work"
SOURCE = REPO / "outputs/raw/2026-09-02-final-heavy"
RUN_LABEL = "2026-09-02-final-heavy"

# (factory, repo, base files verified today to be missing from the Hub)
FACTORIES = [
    ("thalamic-trajectory-factory", "rmems/thalamic-relay-trajectories-grok46",
     ["batch-r02.jsonl", "batch-r22.jsonl", "batch-r23.jsonl", "batch-r63.jsonl"]),
    ("neuromorphic-event-language-bridge", "rmems/neuromorphic-event-language-bridge-grok46",
     ["batch-r01.jsonl", "batch-r02.jsonl", "batch-r22.jsonl"]),
    ("multi-agent-ouroboros-swarm", "rmems/multi-agent-ouroboros-swarm-grok46",
     ["batch-r02.jsonl", "batch-r23.jsonl", "batch-r63.jsonl"]),
    ("failure-as-fuel-preference-cascade", "rmems/failure-as-fuel-preference-cascade-grok46",
     ["batch-r63.jsonl"]),
    ("agentic-coding-trajectory-factory", "rmems/agentic-coding-trajectories-grok46",
     ["batch-r23.jsonl", "batch-r63.jsonl", "batch-r68.jsonl"]),
]
TRUE_DUPLICATES = {"failure-as-fuel-preference-cascade": ["batch-r21.jsonl"]}

RULE_PLAIN = (
    "batch-rNNc.jsonl files are additional batches of the same round; both are "
    "published. The only duplicate, batch-r21.jsonl of "
    "failure-as-fuel-preference-cascade (identical ids to batch-r21c.jsonl), is "
    "omitted."
)
RULE_MD = (
    "`batch-rNNc.jsonl` files are additional batches of the same round; both are "
    "published. The only duplicate, `batch-r21.jsonl` of "
    "failure-as-fuel-preference-cascade (identical ids to `batch-r21c.jsonl`), is "
    "omitted."
)
OLD_RIGHTS_SENTENCE = (
    "Rounds with a c suffix are corrected re-emissions that supersede the base round."
)
OLD_PROV_RULE = (
    "batch-rNNc.jsonl (corrected re-emission) supersedes batch-rNN.jsonl; the "
    "corrected file is published under its own name and the base file for that "
    "round is omitted; every NOTES-*.md is published verbatim"
)
NEW_PROV_RULE = RULE_PLAIN + " Every NOTES-*.md is published verbatim."


class FixBundleCheckError(Exception):
    """A delta-bundle check failed. Raised explicitly so the build refuses under ``python -O``."""


def _require(condition: object, message: object) -> None:
    """Refuse with ``message`` unless ``condition`` holds (never stripped by ``-O``)."""
    if not condition:
        raise FixBundleCheckError(message)


class _Target(NamedTuple):
    """One FACTORIES row resolved: current Hub download, delta bundle, gate tree."""

    factory: str
    repo: str
    cur: Path
    fix: Path
    run_fix: Path


class _Selection(NamedTuple):
    """Raw basenames on the Hub today, the base files to add, and the true duplicates."""

    existing: list[str]
    missing: list[str]
    duplicates: list[str]

    @property
    def names(self) -> list[str]:
        """Exactly the raw files that will be on the Hub after the PR, in round order."""
        return sorted(self.existing + self.missing, key=round_key)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def round_key(name: str) -> tuple[int, str]:
    m = re.fullmatch(r"(?:batch|NOTES)-r(\d+)([a-z]?)\.(?:jsonl|md)", name)
    _require(m, name)
    return int(m.group(1)), m.group(2)


def round_label(name: str) -> str:
    n, suffix = round_key(name)
    return f"r{n:02d}{suffix}"


def record_ids(path: Path) -> list[str]:
    return [json.loads(line)["id"] for line in path.read_bytes().decode("utf-8").split("\n") if line]


def derive_missing(factory: str, existing: list[str]) -> tuple[list[str], list[str]]:
    """Re-derive, from the immutable tree, which base files are missing and which
    are true duplicates of their c file (same record ids)."""
    src = SOURCE / factory
    missing, duplicates = [], []
    for c in sorted(src.glob("batch-r*c.jsonl")):
        base = c.name[: -len("c.jsonl")] + ".jsonl"
        _require((src / base).exists(), base)
        _require(c.name in existing, c.name)
        _require(base not in existing, base)
        c_ids, b_ids = record_ids(c), record_ids(src / base)
        _require(
            len(set(c_ids)) == len(c_ids) and len(set(b_ids)) == len(b_ids),
            f"repeated record ids inside {c.name} or {base}",
        )
        if set(c_ids) == set(b_ids):
            duplicates.append(base)
        else:
            _require(not (set(c_ids) & set(b_ids)), (factory, base, set(c_ids) & set(b_ids)))
            missing.append(base)
    return sorted(missing, key=round_key), sorted(duplicates, key=round_key)


def load_rows(factory: str, names: list[str]):
    """Same row construction as work/build_bundles.py: files in round_key order,
    one ViewerRow per physical line, verbatim line as record_json."""
    rows: list[ViewerRow] = []
    records, files_meta, raw_bytes = [], [], 0
    for name in names:
        payload = (SOURCE / factory / name).read_bytes()
        lines = strict_jsonl.strict_lf_jsonl_lines(payload, f"{factory}/{name}")
        source_file = f"data/raw/{name}"
        for line_number, line in enumerate(lines, 1):
            export_contract._loads_json(line, f"{name}:{line_number}")
            rows.append(ViewerRow(source_file=source_file, source_line=line_number, record_json=line))
            records.append(json.loads(line))
        _require("\n".join(lines).encode("utf-8") + b"\n" == payload, name)
        files_meta.append({"path": source_file, "sha256": sha256(payload), "records": len(lines)})
        raw_bytes += len(payload)
    return rows, records, files_meta, raw_bytes


def _decision_counts(records: list[dict]) -> collections.Counter[str]:
    decisions: collections.Counter[str] = collections.Counter()
    for r in records:
        sd = r.get("safety_decision")
        if isinstance(sd, dict) and isinstance(sd.get("decision"), str):
            decisions[sd["decision"]] += 1
    return decisions


def _surface_counts(records: list[dict]) -> collections.Counter[str]:
    return collections.Counter(
        str(r.get("meta", {}).get("rights", {}).get("generation_surface")) for r in records
    )


def _rights_status_rows(records: list[dict]) -> int:
    return sum(
        1 for r in records if "research_retention_status" in r.get("meta", {}).get("rights", {})
    )


def census(records: list[dict]) -> dict:
    ids = [r.get("id") for r in records]
    _require(len(ids) == len(set(ids)) and all(isinstance(i, str) for i in ids), "ids not unique")
    key_sets = [set(r.keys()) for r in records]
    common = sorted(set.intersection(*key_sets))
    optional = sorted(set.union(*key_sets) - set(common))
    decisions = _decision_counts(records)
    surface = _surface_counts(records)
    rights_status_rows = _rights_status_rows(records)
    return {
        "first_id": ids[0],
        "last_id": ids[-1],
        "common_keys_md": ", ".join(f"`{k}`" for k in common),
        "optional_keys": optional,
        "decisions": dict(decisions),
        "generation_surface": dict(surface),
        "rights_status_rows": rights_status_rows,
    }


def sub_once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    matches = list(re.finditer(pattern, text, flags))
    _require(len(matches) == 1, (label, len(matches)))
    return text[: matches[0].start()] + replacement + text[matches[0].end():]


def _patch_split_numbers(t: str, old: dict, new: dict) -> str:
    """Front matter: only the two split numbers change."""
    return sub_once(
        t,
        rf"    num_examples: {old['rows']}\n    num_bytes: {old['parquet_bytes']}\n",
        f"    num_examples: {new['rows']}\n    num_bytes: {new['parquet_bytes']}\n",
        "front matter split numbers",
    )


def _patch_release_counts(t: str, old: dict, new: dict) -> str:
    """Body: record / file counts and raw size."""
    m = re.search(
        rf"The release contains \*\*{old['records']} (.+?) across\n{old['file_count']} JSONL files\*\* "
        rf"\(~[\d.]+ MB of raw JSONL\)",
        t,
    )
    _require(m and len(re.findall(r"The release contains \*\*", t)) == 1, "release contains")
    kind_label = m.group(1)
    return (
        t[: m.start()]
        + f"The release contains **{new['records']} {kind_label} across\n{new['file_count']} JSONL files** "
        f"(~{new['raw_bytes'] / 1_000_000:.2f} MB of raw JSONL)"
        + t[m.end():]
    )


def _patch_census_paragraph(t: str, new: dict) -> str:
    """Id range, gate outcomes, key census."""
    decisions_md = ""
    if new["decisions"]:
        decisions_md = " Gate outcomes: " + " / ".join(
            f"{k} {v}" for k, v in sorted(new["decisions"].items())
        ) + "."
    optional_md = ""
    if new["optional_keys"]:
        optional_md = " Some rows add " + ", ".join(f"`{k}`" for k in new["optional_keys"]) + "."
    return sub_once(
        t,
        r"Record ids run `[^`]+` …\n`[^`]+` and are unique across the release\..*?\n\nThis is the \*\*Grok 4\.6 counterpart\*\*",
        f"Record ids run `{new['first_id']}` …\n`{new['last_id']}` and are unique across the release."
        f"{decisions_md} Every row\nshares the top-level keys {new['common_keys_md']}.{optional_md}"
        "\n\nThis is the **Grok 4.6 counterpart**",
        "id range / census paragraph",
        re.DOTALL,
    )


def _patch_rights_surface(t: str, old: dict, new: dict) -> str:
    """Rights-status rows and generation surface."""
    surface_md = "; ".join(
        f"`{k}`: {v}" for k, v in sorted(new["generation_surface"].items(), key=lambda kv: -kv[1])
    )
    return sub_once(
        t,
        rf"record-level policy fields \({old['rights_status_rows']} of\n  {old['records']} rows also carry the "
        r"individual research/redistribution\n  status fields\)\. Record-level `generation_surface` values in "
        r"this release:\n  .*?\.\n- \*\*Method:\*\*",
        f"record-level policy fields ({new['rights_status_rows']} of\n  {new['records']} rows also carry the "
        "individual research/redistribution\n  status fields). Record-level `generation_surface` values in "
        f"this release:\n  {surface_md}.\n- **Method:**",
        "rights status / surface",
        re.DOTALL,
    )


def _patch_rounds_bullets(t: str, names: list[str]) -> str:
    """Rounds list + selection rule (replaces the supersession bullet)."""
    rounds_md = ", ".join(f"`{round_label(n)}`" for n in names)
    selection = (
        f"- **Rounds published:** {rounds_md}.\n"
        "- **Selection rule:** `batch-rNNc.jsonl` files are additional batches of\n"
        "  the same round; both are published. The only duplicate,\n"
        "  `batch-r21.jsonl` of failure-as-fuel-preference-cascade (identical ids to\n"
        "  `batch-r21c.jsonl`), is omitted. Every `NOTES-r*.md` written by the\n"
        "  factory is published verbatim under `notes/`.\n"
        "- **Source:**"
    )
    _require("".join(selection.split()) .count("".join(RULE_MD.split())) == 1, "rule wording drift")
    return sub_once(
        t,
        r"- \*\*Rounds published:\*\* .*?\n- \*\*Supersession rule:\*\* .*?under `notes/`\.\n- \*\*Source:\*\*",
        selection,
        "rounds + supersession bullets",
        re.DOTALL,
    )


def _patch_file_table(t: str, files_meta: list[dict]) -> str:
    """Raw file table."""
    files_md = "\n".join(
        f"| `{f['path']}` | {f['records']} | `{f['sha256'][:12]}…` |" for f in files_meta
    )
    return sub_once(
        t,
        r"\| Raw file \| Records \| SHA-256 \(prefix\) \|\n\| --- \| ---: \| --- \|\n(?:\| `data/raw/[^\n]*\|\n)+",
        "| Raw file | Records | SHA-256 (prefix) |\n| --- | ---: | --- |\n" + files_md + "\n",
        "raw file table",
    )


def patch_readme(text: str, old: dict, new: dict, names: list[str], files_meta: list[dict]) -> str:
    t = _patch_split_numbers(text, old, new)
    t = _patch_release_counts(t, old, new)
    t = _patch_census_paragraph(t, new)
    t = _patch_rights_surface(t, old, new)
    t = _patch_rounds_bullets(t, names)
    t = _patch_file_table(t, files_meta)
    # viewer row count in "How to read"
    return sub_once(
        t, rf"indexes {old['rows']} rows\.", f"indexes {new['rows']} rows.", "viewer row count"
    )


def front_matter(text: str) -> list[str]:
    _require(text.startswith("---\n"), "README does not open with a front-matter fence")
    end = text.index("\n---\n", 4)
    return text[4:end].split("\n")


def _reset_output_dirs(target: _Target) -> None:
    for d in (target.fix, target.run_fix):
        if d.exists():
            shutil.rmtree(d)
    (target.fix / "data/raw").mkdir(parents=True)
    (target.fix / "data/viewer").mkdir(parents=True)
    target.run_fix.mkdir(parents=True)


def _current_raw_names(factory: str, cur: Path) -> list[str]:
    """Raw basenames on the Hub today, in round order."""
    existing = sorted((p.name for p in (cur / "data/raw").iterdir()), key=round_key)
    _require(all(re.fullmatch(r"batch-r\d+c?\.jsonl", b) for b in existing), existing)
    for b in existing:  # current Hub raw files are byte-identical to the immutable tree
        _require((cur / "data/raw" / b).read_bytes() == (SOURCE / factory / b).read_bytes(), b)
    _require(not (cur / "data/viewer/records.jsonl").exists(), "unexpected records.jsonl")
    return existing


def _selection(factory: str, existing: list[str], expected_missing: list[str]) -> _Selection:
    missing, duplicates = derive_missing(factory, existing)
    _require(missing == expected_missing, (factory, missing, expected_missing))
    _require(duplicates == TRUE_DUPLICATES.get(factory, []), (factory, duplicates))
    return _Selection(existing, missing, duplicates)


def _reproduce_hub_viewer(factory: str, existing: list[str], cur: Path):
    """Determinism: the predecessor's writer over the existing files must reproduce
    the parquet that is on the Hub today (same writer, same dialect, same order)."""
    old_rows, old_records, _, _ = load_rows(factory, existing)
    old_parquet_hub = (cur / "data/viewer/records.parquet").read_bytes()
    _require(export_viewer.write_viewer_parquet(old_rows) == old_parquet_hub, "writer drift")
    return old_rows, old_records, old_parquet_hub


def _copy_verbatim(factory: str, names: list[str], dest: Path) -> None:
    """Copy each named raw file from the immutable tree and prove the copy byte-identical."""
    for b in names:
        payload = (SOURCE / factory / b).read_bytes()
        (dest / b).write_bytes(payload)
        _require((dest / b).read_bytes() == payload, f"copy does not read back byte-identical: {b}")


def _verify_viewer_parquet(parquet: bytes, rows: list) -> None:
    """Prove the viewer projection lossless twice: the repo reader, then pyarrow."""
    _require(
        export_viewer.read_viewer_parquet(parquet) == rows,
        "viewer parquet does not read back to the source rows",
    )
    table = pq.read_table(io.BytesIO(parquet))
    _require(table.num_rows == len(rows), "viewer parquet row count differs from the source rows")
    for column in ("source_file", "source_line", "record_json"):
        _require(
            table.column(column).to_pylist() == [getattr(r, column) for r in rows],
            f"viewer parquet column {column} differs from the source rows",
        )
    _require(
        [f.name for f in table.schema] == ["source_file", "source_line", "record_json"],
        "viewer parquet columns are not source_file, source_line, record_json",
    )
    _require(
        str(table.schema.field("source_line").type) == "int64",
        "viewer parquet source_line is not int64",
    )


def _check_record_stamps(records: list[dict], factory: str) -> None:
    _require(
        all(r.get("meta", {}).get("generator") == "grok-4.6" for r in records),
        "a record is not stamped meta.generator grok-4.6",
    )
    _require(
        all(r.get("meta", {}).get("factory") == factory for r in records),
        f"a record is not stamped meta.factory {factory}",
    )
    _require(
        all(r.get("meta", {}).get("run_label") == RUN_LABEL for r in records),
        f"a record is not stamped meta.run_label {RUN_LABEL}",
    )


def _totals(records: list[dict], file_count: int, row_count: int, parquet: bytes) -> dict:
    """Card and provenance totals for one state of the repo (before or after the PR)."""
    return {
        **census(records), "records": len(records), "file_count": file_count, "rows": row_count,
        "parquet_bytes": len(parquet), "parquet_sha256": sha256(parquet),
    }


def _current_provenance(cur: Path) -> dict:
    prov_text = (cur / "provenance.json").read_text()
    prov = json.loads(prov_text)
    _require(
        json.dumps(prov, ensure_ascii=False, indent=2) + "\n" == prov_text,
        "provenance serialization",
    )
    return prov


def _check_old_snapshot(snap: dict, old: dict, omitted: list[str]) -> None:
    """The Hub's raw_snapshot must describe exactly the Hub files under the old rule."""
    _require(
        snap["selection_rule"] == OLD_PROV_RULE,
        "provenance selection_rule is not the old supersede rule",
    )
    _require(
        snap["records"] == old["records"] and len(snap["files"]) == old["file_count"],
        "provenance record or file totals differ from the Hub files",
    )
    _require(
        snap["viewer"]["bytes"] == old["parquet_bytes"]
        and snap["viewer"]["sha256"] == old["parquet_sha256"],
        "provenance viewer size or digest differs from the Hub parquet",
    )
    _require(
        snap["superseded_not_published"] == omitted,
        "provenance superseded_not_published differs from the derived omissions",
    )


def _check_existing_entries(snap: dict, files_meta: list[dict]) -> None:
    old_files = {f["path"]: f for f in snap["files"]}
    for f in files_meta:  # existing entries are reproduced exactly
        if f["path"] in old_files:
            _require(old_files[f["path"]] == f, f["path"])


def _rewritten_snapshot(snap: dict, new: dict, duplicates: list[str]) -> dict:
    """Additions to the raw snapshot, new totals, accurate rule; key order kept."""
    new_snap: dict[str, Any] = {}
    for key, value in snap.items():
        if key == "selection_rule":
            new_snap[key] = NEW_PROV_RULE
        elif key == "superseded_not_published":
            new_snap["omitted_not_published"] = duplicates
        elif key == "records":
            new_snap[key] = new["records"]
        elif key == "files":
            new_snap[key] = new["files"]
        elif key == "viewer":
            _require(
                value["writer"] == export_contract.CREATED_BY,
                "provenance viewer writer is not the factory's export writer",
            )
            new_snap[key] = {
                **value, "rows": new["rows"], "bytes": new["parquet_bytes"],
                "sha256": new["parquet_sha256"],
            }
        else:
            new_snap[key] = value
    return new_snap


def _write_provenance(target: _Target, sel: _Selection, old: dict, new: dict) -> dict:
    prov = _current_provenance(target.cur)
    snap = prov["raw_snapshot"]
    _check_old_snapshot(snap, old, sorted(sel.missing + sel.duplicates, key=round_key))
    _check_existing_entries(snap, new["files"])
    prov["raw_snapshot"] = _rewritten_snapshot(snap, new, sel.duplicates)
    (target.fix / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n")
    return prov


def _write_rights(target: _Target) -> str:
    """Only the sentence about c files changes (raw text edit, re-validated)."""
    rights_text = (target.cur / "rights.json").read_text()
    _require(
        rights_text.count(OLD_RIGHTS_SENTENCE) == 1,
        "rights.json does not carry the old c-file sentence exactly once",
    )
    new_rights_text = rights_text.replace(OLD_RIGHTS_SENTENCE, RULE_PLAIN)
    rights_document.load_rights_document_bytes(new_rights_text.encode("utf-8"))  # must not raise
    a, b = json.loads(rights_text), json.loads(new_rights_text)
    _require(
        {k: v for k, v in a.items() if k != "notes"} == {k: v for k, v in b.items() if k != "notes"},
        "rights.json changed outside notes",
    )
    (target.fix / "rights.json").write_text(new_rights_text)
    return new_rights_text


def _check_front_matter_delta(readme: str, new_readme: str, old: dict, new: dict) -> None:
    fm_old, fm_new = front_matter(readme), front_matter(new_readme)
    _require(len(fm_old) == len(fm_new), "README front matter line count changed")
    changed_fm = [(x, y) for x, y in zip(fm_old, fm_new) if x != y]
    _require(changed_fm == [
        (f"    num_examples: {old['rows']}", f"    num_examples: {new['rows']}"),
        (f"    num_bytes: {old['parquet_bytes']}", f"    num_bytes: {new['parquet_bytes']}"),
    ], changed_fm)


def _check_card_wording(new_readme: str, new_rights_text: str, prov: dict, missing: list) -> None:
    _require(
        "license: other\nlicense_name: synthetic-factory-research-only\nlicense_link: LICENSE\n"
        in new_readme,
        "README front matter does not declare the research-only license",
    )
    for stale in ("supersed", "Supersession", "corrected re-emission"):
        _require(stale not in new_readme, stale)
        _require(stale not in new_rights_text, stale)
        _require(stale not in json.dumps(prov), stale)
    for added in missing:
        _require(f"| `data/raw/{added}` |" in new_readme, added)


def _check_release_status(cur: Path) -> None:
    """release-status.json carries no record count: unchanged, not part of the delta."""
    status = json.loads((cur / "release-status.json").read_text())
    _require(
        not any(isinstance(v, int) and not isinstance(v, bool) for v in status.values()),
        "release-status.json carries a count",
    )


def build_one(factory: str, repo: str, expected_missing: list[str]) -> dict:
    name = repo.split("/")[1]
    target = _Target(factory, repo, CURRENT / name, FIX / name, RUN_FIX / factory)
    _reset_output_dirs(target)

    existing = _current_raw_names(factory, target.cur)
    sel = _selection(factory, existing, expected_missing)
    old_rows, old_records, old_parquet_hub = _reproduce_hub_viewer(factory, existing, target.cur)

    # raw additions, then the gate tree: exactly the raw files on the Hub after the PR
    _copy_verbatim(factory, sel.missing, target.fix / "data/raw")
    names = sel.names
    _copy_verbatim(factory, names, target.run_fix)

    # viewer projection over ALL raw files, proven lossless twice
    rows, records, files_meta, raw_bytes = load_rows(factory, names)
    parquet = export_viewer.write_viewer_parquet(rows)
    _verify_viewer_parquet(parquet, rows)
    (target.fix / "data/viewer/records.parquet").write_bytes(parquet)

    _check_record_stamps(records, factory)
    old = _totals(old_records, len(existing), len(old_rows), old_parquet_hub)
    new = {
        **_totals(records, len(names), len(rows), parquet),
        "raw_bytes": raw_bytes, "files": files_meta,
    }

    prov = _write_provenance(target, sel, old, new)
    new_rights_text = _write_rights(target)

    # README.md: targeted replacements on the current card; license front matter untouched
    readme = (target.cur / "README.md").read_text()
    new_readme = patch_readme(readme, old, new, names, files_meta)
    _check_front_matter_delta(readme, new_readme, old, new)
    _check_card_wording(new_readme, new_rights_text, prov, sel.missing)
    (target.fix / "README.md").write_text(new_readme)

    _check_release_status(target.cur)
    return _fix_summary(target, sel, old, new)


def _fix_summary(target: _Target, sel: _Selection, old: dict, new: dict) -> dict:
    fix = target.fix
    return {
        "repo": target.repo,
        "factory": target.factory,
        "fix_bundle": str(fix),
        "run_fix": str(target.run_fix),
        "added_files": [f"data/raw/{b}" for b in sel.missing],
        "added_records": sum(
            f["records"] for f in new["files"] if f["path"].split("/")[-1] in sel.missing
        ),
        "omitted_duplicates": sel.duplicates,
        "records_before": old["records"],
        "records_after": new["records"],
        "files_before": old["file_count"],
        "files_after": new["file_count"],
        "parquet_rows_before": old["rows"],
        "parquet_rows_after": new["rows"],
        "parquet_bytes_before": old["parquet_bytes"],
        "parquet_bytes_after": new["parquet_bytes"],
        "parquet_sha256_after": new["parquet_sha256"],
        "rounds_after": [round_label(n) for n in sel.names],
        "delta_files": sorted(str(p.relative_to(fix)) for p in fix.rglob("*") if p.is_file()),
    }


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    RUN_FIX.mkdir(parents=True, exist_ok=True)
    summaries = [build_one(*cfg) for cfg in FACTORIES]
    (WORK / "fix_summaries.json").write_text(json.dumps(summaries, indent=1))
    for s in summaries:
        print(json.dumps({k: s[k] for k in s if k not in ("rounds_after",)}, indent=None))


if __name__ == "__main__":
    main()
