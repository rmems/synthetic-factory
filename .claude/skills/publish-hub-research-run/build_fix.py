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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def round_key(name: str) -> tuple[int, str]:
    m = re.fullmatch(r"(?:batch|NOTES)-r(\d+)([a-z]?)\.(?:jsonl|md)", name)
    assert m, name
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
        assert (src / base).exists(), base
        assert c.name in existing, c.name
        assert base not in existing, base
        c_ids, b_ids = record_ids(c), record_ids(src / base)
        assert len(set(c_ids)) == len(c_ids) and len(set(b_ids)) == len(b_ids)
        if set(c_ids) == set(b_ids):
            duplicates.append(base)
        else:
            assert not (set(c_ids) & set(b_ids)), (factory, base, set(c_ids) & set(b_ids))
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
        assert "\n".join(lines).encode("utf-8") + b"\n" == payload, name
        files_meta.append({"path": source_file, "sha256": sha256(payload), "records": len(lines)})
        raw_bytes += len(payload)
    return rows, records, files_meta, raw_bytes


def census(records: list[dict]) -> dict:
    ids = [r.get("id") for r in records]
    assert len(ids) == len(set(ids)) and all(isinstance(i, str) for i in ids), "ids not unique"
    key_sets = [set(r.keys()) for r in records]
    common = sorted(set.intersection(*key_sets))
    optional = sorted(set.union(*key_sets) - set(common))
    decisions = collections.Counter()
    for r in records:
        sd = r.get("safety_decision")
        if isinstance(sd, dict) and isinstance(sd.get("decision"), str):
            decisions[sd["decision"]] += 1
    surface = collections.Counter(
        str(r.get("meta", {}).get("rights", {}).get("generation_surface")) for r in records
    )
    rights_status_rows = sum(
        1 for r in records if "research_retention_status" in r.get("meta", {}).get("rights", {})
    )
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
    assert len(matches) == 1, (label, len(matches))
    return text[: matches[0].start()] + replacement + text[matches[0].end():]


def patch_readme(text: str, old: dict, new: dict, names: list[str], files_meta: list[dict]) -> str:
    t = text
    # front matter: only the two split numbers change
    t = sub_once(
        t,
        rf"    num_examples: {old['rows']}\n    num_bytes: {old['parquet_bytes']}\n",
        f"    num_examples: {new['rows']}\n    num_bytes: {new['parquet_bytes']}\n",
        "front matter split numbers",
    )
    # body: record / file counts and raw size
    m = re.search(
        rf"The release contains \*\*{old['records']} (.+?) across\n{old['file_count']} JSONL files\*\* "
        rf"\(~[\d.]+ MB of raw JSONL\)",
        t,
    )
    assert m and len(re.findall(r"The release contains \*\*", t)) == 1, "release contains"
    kind_label = m.group(1)
    t = (
        t[: m.start()]
        + f"The release contains **{new['records']} {kind_label} across\n{new['file_count']} JSONL files** "
        f"(~{new['raw_bytes'] / 1_000_000:.2f} MB of raw JSONL)"
        + t[m.end():]
    )
    # id range, gate outcomes, key census
    decisions_md = ""
    if new["decisions"]:
        decisions_md = " Gate outcomes: " + " / ".join(
            f"{k} {v}" for k, v in sorted(new["decisions"].items())
        ) + "."
    optional_md = ""
    if new["optional_keys"]:
        optional_md = " Some rows add " + ", ".join(f"`{k}`" for k in new["optional_keys"]) + "."
    t = sub_once(
        t,
        r"Record ids run `[^`]+` …\n`[^`]+` and are unique across the release\..*?\n\nThis is the \*\*Grok 4\.6 counterpart\*\*",
        f"Record ids run `{new['first_id']}` …\n`{new['last_id']}` and are unique across the release."
        f"{decisions_md} Every row\nshares the top-level keys {new['common_keys_md']}.{optional_md}"
        "\n\nThis is the **Grok 4.6 counterpart**",
        "id range / census paragraph",
        re.DOTALL,
    )
    # rights-status rows and generation surface
    surface_md = "; ".join(
        f"`{k}`: {v}" for k, v in sorted(new["generation_surface"].items(), key=lambda kv: -kv[1])
    )
    t = sub_once(
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
    # rounds list + selection rule (replaces the supersession bullet)
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
    assert "".join(selection.split()) .count("".join(RULE_MD.split())) == 1, "rule wording drift"
    t = sub_once(
        t,
        r"- \*\*Rounds published:\*\* .*?\n- \*\*Supersession rule:\*\* .*?under `notes/`\.\n- \*\*Source:\*\*",
        selection,
        "rounds + supersession bullets",
        re.DOTALL,
    )
    # raw file table
    files_md = "\n".join(
        f"| `{f['path']}` | {f['records']} | `{f['sha256'][:12]}…` |" for f in files_meta
    )
    t = sub_once(
        t,
        r"\| Raw file \| Records \| SHA-256 \(prefix\) \|\n\| --- \| ---: \| --- \|\n(?:\| `data/raw/[^\n]*\|\n)+",
        "| Raw file | Records | SHA-256 (prefix) |\n| --- | ---: | --- |\n" + files_md + "\n",
        "raw file table",
    )
    # viewer row count in "How to read"
    t = sub_once(
        t, rf"indexes {old['rows']} rows\.", f"indexes {new['rows']} rows.", "viewer row count"
    )
    return t


def front_matter(text: str) -> list[str]:
    assert text.startswith("---\n")
    end = text.index("\n---\n", 4)
    return text[4:end].split("\n")


def build_one(factory: str, repo: str, expected_missing: list[str]) -> dict:
    name = repo.split("/")[1]
    cur = CURRENT / name
    fix = FIX / name
    run_fix = RUN_FIX / factory
    for d in (fix, run_fix):
        if d.exists():
            shutil.rmtree(d)
    (fix / "data/raw").mkdir(parents=True)
    (fix / "data/viewer").mkdir(parents=True)
    run_fix.mkdir(parents=True)

    existing = sorted((p.name for p in (cur / "data/raw").iterdir()), key=round_key)
    assert all(re.fullmatch(r"batch-r\d+c?\.jsonl", b) for b in existing), existing
    for b in existing:  # current Hub raw files are byte-identical to the immutable tree
        assert (cur / "data/raw" / b).read_bytes() == (SOURCE / factory / b).read_bytes(), b
    assert not (cur / "data/viewer/records.jsonl").exists(), "unexpected records.jsonl"

    missing, duplicates = derive_missing(factory, existing)
    assert missing == expected_missing, (factory, missing, expected_missing)
    assert duplicates == TRUE_DUPLICATES.get(factory, []), (factory, duplicates)

    # determinism: the predecessor's writer over the existing files must reproduce
    # the parquet that is on the Hub today (same writer, same dialect, same order)
    old_rows, old_records, _, _ = load_rows(factory, existing)
    old_parquet_hub = (cur / "data/viewer/records.parquet").read_bytes()
    assert export_viewer.write_viewer_parquet(old_rows) == old_parquet_hub, "writer drift"

    # raw additions: verbatim bytes from the immutable tree
    for b in missing:
        payload = (SOURCE / factory / b).read_bytes()
        (fix / "data/raw" / b).write_bytes(payload)
        assert (fix / "data/raw" / b).read_bytes() == payload
    # gate tree: exactly the raw files that will be on the Hub after the PR
    names = sorted(existing + missing, key=round_key)
    for b in names:
        payload = (SOURCE / factory / b).read_bytes()
        (run_fix / b).write_bytes(payload)
        assert (run_fix / b).read_bytes() == payload

    # viewer projection over ALL raw files, proven lossless twice
    rows, records, files_meta, raw_bytes = load_rows(factory, names)
    parquet = export_viewer.write_viewer_parquet(rows)
    assert export_viewer.read_viewer_parquet(parquet) == rows
    table = pq.read_table(io.BytesIO(parquet))
    assert table.num_rows == len(rows)
    assert table.column("source_file").to_pylist() == [r.source_file for r in rows]
    assert table.column("source_line").to_pylist() == [r.source_line for r in rows]
    assert table.column("record_json").to_pylist() == [r.record_json for r in rows]
    assert [f.name for f in table.schema] == ["source_file", "source_line", "record_json"]
    assert str(table.schema.field("source_line").type) == "int64"
    (fix / "data/viewer/records.parquet").write_bytes(parquet)

    assert all(r.get("meta", {}).get("generator") == "grok-4.6" for r in records)
    assert all(r.get("meta", {}).get("factory") == factory for r in records)
    assert all(r.get("meta", {}).get("run_label") == RUN_LABEL for r in records)
    old_c = census(old_records)
    new_c = census(records)
    old = {
        **old_c, "records": len(old_records), "file_count": len(existing), "rows": len(old_rows),
        "parquet_bytes": len(old_parquet_hub),
    }
    new = {
        **new_c, "records": len(records), "file_count": len(names), "rows": len(rows),
        "parquet_bytes": len(parquet), "raw_bytes": raw_bytes,
    }

    # provenance.json: additions to the raw snapshot, new totals, accurate rule
    prov_text = (cur / "provenance.json").read_text()
    prov = json.loads(prov_text)
    assert json.dumps(prov, ensure_ascii=False, indent=2) + "\n" == prov_text, "provenance serialization"
    snap = prov["raw_snapshot"]
    assert snap["selection_rule"] == OLD_PROV_RULE
    assert snap["records"] == old["records"] and len(snap["files"]) == old["file_count"]
    assert snap["viewer"]["bytes"] == old["parquet_bytes"] and snap["viewer"]["sha256"] == sha256(old_parquet_hub)
    assert snap["superseded_not_published"] == sorted(missing + duplicates, key=round_key)
    old_files = {f["path"]: f for f in snap["files"]}
    for f in files_meta:  # existing entries are reproduced exactly
        if f["path"] in old_files:
            assert old_files[f["path"]] == f, f["path"]
    new_snap = {}
    for key, value in snap.items():
        if key == "selection_rule":
            new_snap[key] = NEW_PROV_RULE
        elif key == "superseded_not_published":
            new_snap["omitted_not_published"] = duplicates
        elif key == "records":
            new_snap[key] = new["records"]
        elif key == "files":
            new_snap[key] = files_meta
        elif key == "viewer":
            assert value["writer"] == export_contract.CREATED_BY
            new_snap[key] = {**value, "rows": new["rows"], "bytes": new["parquet_bytes"], "sha256": sha256(parquet)}
        else:
            new_snap[key] = value
    prov["raw_snapshot"] = new_snap
    (fix / "provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2) + "\n")

    # rights.json: only the sentence about c files changes (raw text edit, re-validated)
    rights_text = (cur / "rights.json").read_text()
    assert rights_text.count(OLD_RIGHTS_SENTENCE) == 1
    new_rights_text = rights_text.replace(OLD_RIGHTS_SENTENCE, RULE_PLAIN)
    rights_document.load_rights_document_bytes(new_rights_text.encode("utf-8"))  # must not raise
    a, b = json.loads(rights_text), json.loads(new_rights_text)
    assert {k: v for k, v in a.items() if k != "notes"} == {k: v for k, v in b.items() if k != "notes"}
    (fix / "rights.json").write_text(new_rights_text)

    # README.md: targeted replacements on the current card; license front matter untouched
    readme = (cur / "README.md").read_text()
    new_readme = patch_readme(readme, old, new, names, files_meta)
    fm_old, fm_new = front_matter(readme), front_matter(new_readme)
    assert len(fm_old) == len(fm_new)
    changed_fm = [(x, y) for x, y in zip(fm_old, fm_new) if x != y]
    assert changed_fm == [
        (f"    num_examples: {old['rows']}", f"    num_examples: {new['rows']}"),
        (f"    num_bytes: {old['parquet_bytes']}", f"    num_bytes: {new['parquet_bytes']}"),
    ], changed_fm
    assert "license: other\nlicense_name: synthetic-factory-research-only\nlicense_link: LICENSE\n" in new_readme
    for stale in ("supersed", "Supersession", "corrected re-emission"):
        assert stale not in new_readme, stale
        assert stale not in new_rights_text, stale
        assert stale not in json.dumps(prov), stale
    for added in missing:
        assert f"| `data/raw/{added}` |" in new_readme, added
    (fix / "README.md").write_text(new_readme)

    # release-status.json carries no record count: unchanged, not part of the delta
    status = json.loads((cur / "release-status.json").read_text())
    assert not any(isinstance(v, int) and not isinstance(v, bool) for v in status.values())

    return {
        "repo": repo,
        "factory": factory,
        "fix_bundle": str(fix),
        "run_fix": str(run_fix),
        "added_files": [f"data/raw/{b}" for b in missing],
        "added_records": sum(f["records"] for f in files_meta if f["path"].split("/")[-1] in missing),
        "omitted_duplicates": duplicates,
        "records_before": old["records"],
        "records_after": new["records"],
        "files_before": old["file_count"],
        "files_after": new["file_count"],
        "parquet_rows_before": old["rows"],
        "parquet_rows_after": new["rows"],
        "parquet_bytes_before": old["parquet_bytes"],
        "parquet_bytes_after": new["parquet_bytes"],
        "parquet_sha256_after": sha256(parquet),
        "rounds_after": [round_label(n) for n in names],
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
