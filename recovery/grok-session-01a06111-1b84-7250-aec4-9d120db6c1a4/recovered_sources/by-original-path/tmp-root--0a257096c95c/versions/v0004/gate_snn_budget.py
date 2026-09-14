#!/usr/bin/env python3
"""Legal gate_snn spike budget: round(n * rate * dw_s) ± 1.

dw_s = decision_window_ms / 1000.

CLI:
  python3 /tmp/gate_snn_budget.py DECISION_WINDOW_MS NEURONS RATE
      prints legal spikes and the ±1 window

  python3 /tmp/gate_snn_budget.py
      scans the default staging JSONLs if present and writes
      /tmp/gate-snn-fuzz.md

Never reads or writes outputs/raw/.
"""

from __future__ import annotations

import json
import math
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCAN_PATHS = (
    Path("/tmp/batch-r12.jsonl"),
    Path("/tmp/ttf-r13/batch-r13.jsonl"),
    Path("/tmp/nelb-r13/batch-r13.jsonl"),
)
REPORT_PATH = Path("/tmp/gate-snn-fuzz.md")

GATE_CARRIERS = (
    ("gate_snn",),
    ("meta", "gate_snn"),
    ("language_view", "trajectory", "gate_snn"),
    ("language_view", "trajectory", "safety_decision", "gate_snn"),
)


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _dec(value):
    number = _num(value)
    if number is None:
        return None
    try:
        return Decimal(str(value if not isinstance(value, float) else number))
    except (InvalidOperation, ValueError):
        return None


def legal_spikes(decision_window_ms, neurons, rate):
    """Return (legal, lo, hi) for spikes = round(n * rate * dw_s) ± 1."""

    dw_ms = _num(decision_window_ms)
    n = _num(neurons)
    hz = _num(rate)
    if dw_ms is None or n is None or hz is None:
        raise ValueError("decision_window_ms, neurons, and rate must be finite numbers")
    dw_s = dw_ms / 1000.0
    legal = round(n * hz * dw_s)
    return legal, legal - 1, legal + 1


def legal_spikes_decimal(decision_window_ms, neurons, rate):
    dw_ms = _dec(decision_window_ms)
    n = _dec(neurons)
    hz = _dec(rate)
    if dw_ms is None or n is None or hz is None:
        return None
    dw_s = dw_ms / Decimal(1000)
    product = n * hz * dw_s
    legal = int(round(product))
    return legal, legal - 1, legal + 1, product


def print_budget(decision_window_ms, neurons, rate, *, file=sys.stdout):
    legal, lo, hi = legal_spikes(decision_window_ms, neurons, rate)
    dw_s = _dec(decision_window_ms) / Decimal(1000)
    print(f"legal spikes = {legal}", file=file)
    print(f"±1 window = [{lo}, {hi}]", file=file)
    print(f"dw_s = {dw_s.normalize()}", file=file)
    return legal, lo, hi


def _mapping(value):
    return value if isinstance(value, dict) else None


def _nested(container, keys):
    current = container
    for key in keys:
        current = _mapping(current)
        if current is None or key not in current:
            return None
        current = current[key]
    return current


def _record_id(record, line_no):
    ident = record.get("id") if isinstance(record, dict) else None
    if isinstance(ident, str) and ident.strip():
        return ident.strip()
    return f"line-{line_no}"


def _collect_gate_snn(record):
    seen = []
    found = []
    for keys in GATE_CARRIERS:
        spec = _nested(record, keys)
        if spec is None:
            continue
        marker = id(spec)
        if marker in seen:
            continue
        seen.append(marker)
        found.append((".".join(keys), spec))

    stack = [(record, "")]
    while stack:
        obj, path = stack.pop()
        if isinstance(obj, dict):
            if "gate_snn" in obj:
                spec = obj["gate_snn"]
                marker = id(spec)
                if marker not in seen:
                    seen.append(marker)
                    loc = f"{path}.gate_snn" if path else "gate_snn"
                    found.append((loc, spec))
            for key, value in obj.items():
                if key == "gate_snn":
                    continue
                next_path = f"{path}.{key}" if path else key
                if isinstance(value, (dict, list)):
                    stack.append((value, next_path))
        elif isinstance(obj, list):
            for index, value in enumerate(obj):
                if isinstance(value, (dict, list)):
                    stack.append((value, f"{path}[{index}]"))
    return found


def _decision_window(spec):
    if not isinstance(spec, dict):
        return None, None, "gate_snn is not an object"
    dw_ms = spec.get("decision_window_ms")
    dw_s = spec.get("decision_window_s")
    ms_n = _num(dw_ms)
    s_n = _num(dw_s)
    if ms_n is None and s_n is None:
        return None, None, "missing decision_window_ms/s"
    if ms_n is None:
        ms_n = s_n * 1000.0
    if s_n is None:
        s_n = ms_n / 1000.0
    if ms_n <= 0 or s_n <= 0:
        return None, None, "non-positive decision window"
    if abs(ms_n / 1000.0 - s_n) > 1e-9:
        return ms_n, s_n, "decision_window_ms/s disagree"
    return ms_n, s_n, None


def _pop_rate(population):
    if not isinstance(population, dict):
        return None, False
    if "mean_rate_hz" in population:
        return population.get("mean_rate_hz"), True
    if "rate_hz" in population:
        return population.get("rate_hz"), True
    return None, False


def _safety_decision(record):
    for keys in (
        ("safety_decision", "decision"),
        ("language_view", "trajectory", "safety_decision", "decision"),
    ):
        value = _nested(record, keys)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _classify_population(population, dw_ms):
    rate, rate_declared = _pop_rate(population)
    spikes_declared = isinstance(population, dict) and "spikes" in population
    name = population.get("name") if isinstance(population, dict) else None
    neurons = population.get("neurons") if isinstance(population, dict) else None
    spikes = population.get("spikes") if spikes_declared else None
    row = {
        "name": name if isinstance(name, str) else None,
        "neurons": neurons,
        "rate": rate,
        "spikes": spikes,
        "rate_declared": rate_declared,
        "spikes_declared": spikes_declared,
        "status": None,
        "legal": None,
        "lo": None,
        "hi": None,
        "delta": None,
        "product": None,
        "legal_dec": None,
        "float_vs_decimal": None,
        "wrong_unit_legal": None,
        "note": None,
    }
    if not rate_declared and not spikes_declared:
        row["status"] = "absent"
        row["note"] = "omit-both allowed"
        return row
    if not rate_declared or not spikes_declared:
        row["status"] = "mismatch"
        row["note"] = "rate XOR spikes (invalid budget shape)"
        return row
    n = _num(neurons)
    hz = _num(rate)
    sp = _num(spikes)
    if n is None or n <= 0 or hz is None or hz <= 0 or sp is None or sp < 0:
        row["status"] = "mismatch"
        row["note"] = "non-positive or non-numeric n/rate/spikes"
        return row
    if abs(sp - round(sp)) > 0:
        row["status"] = "mismatch"
        row["note"] = "spikes is not an integer"
        return row
    sp = int(round(sp))
    legal, lo, hi = legal_spikes(dw_ms, n, hz)
    dec = legal_spikes_decimal(dw_ms, n, hz)
    row["legal"] = legal
    row["lo"] = lo
    row["hi"] = hi
    row["delta"] = sp - legal
    row["spikes"] = sp
    if dec is not None:
        legal_dec, _, _, product = dec
        row["legal_dec"] = legal_dec
        row["product"] = product
        row["float_vs_decimal"] = legal != legal_dec
    wrong_unit = round(n * hz * _num(dw_ms))
    row["wrong_unit_legal"] = wrong_unit
    if lo <= sp <= hi:
        row["status"] = "ok"
    else:
        row["status"] = "mismatch"
        row["note"] = f"spikes {sp} outside [{lo}, {hi}] (legal={legal})"
    return row


def scan_record(record, line_no):
    rid = _record_id(record, line_no)
    gates = _collect_gate_snn(record)
    safety = _safety_decision(record)
    issues = []
    rows = []
    if not gates:
        issues.append("no gate_snn carrier")
        return {
            "id": rid,
            "line": line_no,
            "gates": 0,
            "rows": rows,
            "issues": issues,
            "decision_ok": None,
        }
    for loc, spec in gates:
        dw_ms, dw_s, dw_err = _decision_window(spec)
        decision = spec.get("decision") if isinstance(spec, dict) else None
        decision_ok = None
        if isinstance(decision, str) and safety:
            decision_ok = decision.strip().upper() == safety.strip().upper()
            if not decision_ok:
                issues.append(f"{loc}.decision {decision!r} != safety {safety!r}")
        if dw_err and dw_ms is None:
            issues.append(f"{loc}: {dw_err}")
            continue
        if dw_err:
            issues.append(f"{loc}: {dw_err}")
        populations = spec.get("populations") if isinstance(spec, dict) else None
        if not isinstance(populations, list) or not populations:
            issues.append(f"{loc}: empty or missing populations")
            continue
        for index, population in enumerate(populations):
            row = _classify_population(population, dw_ms)
            row.update(
                {
                    "loc": loc,
                    "index": index,
                    "dw_ms": dw_ms,
                    "dw_s": dw_s if dw_s is not None else (dw_ms / 1000.0 if dw_ms else None),
                    "decision": decision if isinstance(decision, str) else None,
                    "decision_ok": decision_ok,
                }
            )
            rows.append(row)
    return {
        "id": rid,
        "line": line_no,
        "gates": len(gates),
        "rows": rows,
        "issues": issues,
        "decision_ok": all(
            row["decision_ok"] for row in rows if row.get("decision_ok") is not None
        )
        if any(row.get("decision_ok") is not None for row in rows)
        else None,
    }


def iter_jsonl(path):
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                yield line_no, json.loads(raw), None
            except json.JSONDecodeError as exc:
                yield line_no, None, str(exc)


def scan_files(paths):
    results = []
    for path in paths:
        entry = {
            "path": str(path),
            "present": path.is_file(),
            "records": [],
            "parse_errors": [],
        }
        if not path.is_file():
            results.append(entry)
            continue
        for line_no, record, error in iter_jsonl(path):
            if error:
                entry["parse_errors"].append((line_no, error))
                continue
            entry["records"].append(scan_record(record, line_no))
        results.append(entry)
    return results


def _md_cell(value):
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Decimal):
        text = format(value, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    return str(value)


def render_report(results):
    lines = []
    lines.append("# gate_snn spike-budget fuzz")
    lines.append("")
    lines.append("Formula (fail-closed, same as `pipelines/curate_bridge_gate.py`):")
    lines.append("")
    lines.append("```")
    lines.append("dw_s = decision_window_ms / 1000")
    lines.append("legal spikes = round(n * rate * dw_s)")
    lines.append("±1 window    = [legal - 1, legal + 1]")
    lines.append("```")
    lines.append("")
    lines.append("A population that declares `mean_rate_hz`/`rate_hz` **and** `spikes`")
    lines.append("must land in the ±1 window. Omit-both is allowed (threshold-only veto")
    lines.append("pops). Rate XOR spikes is a mismatch. Calculator:")
    lines.append("`python3 /tmp/gate_snn_budget.py DECISION_WINDOW_MS NEURONS RATE`.")
    lines.append("")
    lines.append("Sources scanned only if present. Never read or wrote `outputs/raw/`.")
    lines.append("")

    present = [item for item in results if item["present"]]
    missing = [item for item in results if not item["present"]]
    lines.append("## Files")
    lines.append("")
    for item in present:
        nrec = len(item["records"])
        nerr = len(item["parse_errors"])
        lines.append(f"- present: `{item['path']}` ({nrec} records, {nerr} parse errors)")
    for item in missing:
        lines.append(f"- **missing:** `{item['path']}` (skipped)")
    if not present:
        lines.append("- no scan targets present")
    lines.append("")

    mismatches = []
    float_dec_disagreements = []
    unit_traps = []
    n_pops = 0
    n_ok = 0
    n_absent = 0
    n_budget = 0

    lines.append("## Scan")
    lines.append("")
    for item in present:
        lines.append(f"### `{item['path']}`")
        lines.append("")
        if item["parse_errors"]:
            for line_no, error in item["parse_errors"]:
                lines.append(f"- parse error line {line_no}: {error}")
                mismatches.append((item["path"], f"line-{line_no}", error))
            lines.append("")
        if not item["records"]:
            lines.append("No records.")
            lines.append("")
            continue
        for rec in item["records"]:
            lines.append(
                f"#### `{rec['id']}` (line {rec['line']}, gate_snn carriers={rec['gates']})"
            )
            lines.append("")
            if rec["issues"]:
                for issue in rec["issues"]:
                    lines.append(f"- flag: {issue}")
                    mismatches.append((item["path"], rec["id"], issue))
                lines.append("")
            if not rec["rows"]:
                lines.append("No populations classified.")
                lines.append("")
                continue
            lines.append(
                "| pop | n | rate Hz | dw_ms | dw_s | product | legal | ±1 window | spikes | Δ | status |"
            )
            lines.append("|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|")
            for row in rec["rows"]:
                n_pops += 1
                status = row["status"]
                if status == "ok":
                    n_ok += 1
                    n_budget += 1
                elif status == "absent":
                    n_absent += 1
                else:
                    n_budget += 1
                    mismatches.append(
                        (
                            item["path"],
                            rec["id"],
                            f"{row.get('name')} {row.get('note')}",
                        )
                    )
                if row.get("float_vs_decimal"):
                    float_dec_disagreements.append(
                        (
                            rec["id"],
                            row.get("name"),
                            row.get("legal"),
                            row.get("legal_dec"),
                        )
                    )
                if (
                    row.get("wrong_unit_legal") is not None
                    and row.get("legal") is not None
                    and row["wrong_unit_legal"] != row["legal"]
                    and row.get("spikes") == row["wrong_unit_legal"]
                    and row["status"] == "mismatch"
                ):
                    unit_traps.append((rec["id"], row.get("name")))
                window = (
                    f"[{row['lo']}, {row['hi']}]"
                    if row["lo"] is not None
                    else "—"
                )
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            _md_cell(row.get("name")),
                            _md_cell(row.get("neurons")),
                            _md_cell(row.get("rate")),
                            _md_cell(row.get("dw_ms")),
                            _md_cell(row.get("dw_s")),
                            _md_cell(row.get("product")),
                            _md_cell(row.get("legal")),
                            window,
                            _md_cell(row.get("spikes")),
                            _md_cell(row.get("delta")),
                            _md_cell(status),
                        ]
                    )
                    + " |"
                )
            lines.append("")
            dw_ms = rec["rows"][0].get("dw_ms")
            if dw_ms is not None and dw_ms < 1:
                lines.append(
                    f"Note: `decision_window_ms={dw_ms}` is sub-millisecond "
                    f"(race-scale, dw_s={dw_ms / 1000}). Treating that field as "
                    "seconds would inflate the budget by 1000×."
                )
                lines.append("")

    lines.append("## Mismatches")
    lines.append("")
    if not mismatches:
        lines.append("None. Every declared `(n, rate, dw_s)` budget is inside the ±1 window.")
        lines.append("")
    else:
        lines.append(f"{len(mismatches)} flag(s):")
        lines.append("")
        for path, rid, note in mismatches:
            lines.append(f"- `{path}` `{rid}`: {note}")
        lines.append("")

    lines.append("## Fuzz")
    lines.append("")
    lines.append("Two arithmetic interpretations of the same JSON numbers:")
    lines.append("")
    lines.append("- **float:** `round(n * rate * (dw_ms / 1000.0))` (CLI formula)")
    lines.append("- **decimal:** `round(Decimal(n) * Decimal(rate) * Decimal(dw_ms) / 1000)`")
    lines.append("  (JSON-token identity; production uses `Fraction` the same way)")
    lines.append("")
    if float_dec_disagreements:
        lines.append("Float vs decimal **disagreed** on:")
        lines.append("")
        for rid, name, fl, dec in float_dec_disagreements:
            lines.append(f"- `{rid}` `{name}`: float legal={fl}, decimal legal={dec}")
        lines.append("")
    else:
        lines.append(
            "Float vs decimal: **no disagreements** on any declared population in this scan."
        )
        lines.append("")
    lines.append("Unit trap: `round(n * rate * dw_ms)` (forgot `/1000`).")
    if unit_traps:
        lines.append("Declared spikes matched the *wrong-unit* legal count on:")
        for rid, name in unit_traps:
            lines.append(f"- `{rid}` `{name}`")
    else:
        lines.append(
            "No declared spike count equals the wrong-unit legal value while missing the canonical window."
        )
    lines.append("")
    lines.append("Worked CLI identities (not a scan of records):")
    lines.append("")
    lines.append("| dw_ms | n | rate | legal | ±1 window |")
    lines.append("|---:|---:|---:|---:|---|")
    demos = (
        (25, 64, 40),
        (40, 128, 25),
        (20, 32, 50),
        (32, 96, 30),
        (28, 48, 35),
        (0.42, 48, 250),
        (40, 80, 50),
        (32, 100, 31.25),
    )
    for dw_ms, n, rate in demos:
        legal, lo, hi = legal_spikes(dw_ms, n, rate)
        lines.append(f"| {dw_ms} | {n} | {rate} | {legal} | [{lo}, {hi}] |")
    lines.append("")
    lines.append("Banker's rounding at `.5` (Python 3 / production `round`):")
    lines.append("`round(2.5)=2`, `round(3.5)=4`. A product of `k+0.5` therefore")
    lines.append("lands on the even integer; the ±1 window still covers both")
    lines.append("neighbours, so a half-up author (`k+1`) remains legal.")
    lines.append("")

    lines.append("## Counts")
    lines.append("")
    lines.append(f"- files present: {len(present)} / {len(results)}")
    lines.append(f"- populations classified: {n_pops}")
    lines.append(f"- budget declared (rate+spikes): {n_budget}")
    lines.append(f"- omit-both (allowed): {n_absent}")
    lines.append(f"- declared budgets inside ±1: {n_ok}")
    lines.append(f"- flags: {len(mismatches)}")
    lines.append("")
    if mismatches:
        lines.append("**Verdict: FAIL** — see Mismatches.")
    else:
        lines.append("**Verdict: PASS** — no spike-budget mismatches.")
    lines.append("")
    lines.append("No writes under `outputs/raw/`.")
    lines.append("")
    return "\n".join(lines)


def scan_and_report(paths=SCAN_PATHS, report_path=REPORT_PATH):
    results = scan_files(paths)
    text = render_report(results)
    report_path.write_text(text, encoding="utf-8")
    mismatches = 0
    for item in results:
        if not item["present"]:
            print(f"SKIP missing {item['path']}")
            continue
        print(f"SCAN {item['path']} records={len(item['records'])}")
        for rec in item["records"]:
            n_mis = sum(1 for row in rec["rows"] if row["status"] == "mismatch")
            mismatches += n_mis + len(rec["issues"])
            status = "FAIL" if (n_mis or rec["issues"]) else "ok"
            print(
                f"  {rec['id']}: pops={len(rec['rows'])} mismatches={n_mis} {status}"
            )
            for issue in rec["issues"]:
                print(f"    FLAG {issue}")
            for row in rec["rows"]:
                if row["status"] == "mismatch":
                    print(
                        f"    FLAG pop[{row['index']}] {row.get('name')}: {row.get('note')}"
                    )
    print(f"report {report_path}")
    return 1 if mismatches else 0


def main(argv):
    args = [item for item in argv[1:] if item not in {"--scan", "--report"}]
    if len(args) == 3:
        dw_ms, neurons, rate = (float(args[0]), float(args[1]), float(args[2]))
        print_budget(dw_ms, neurons, rate)
        return 0
    if args:
        print(
            "usage: gate_snn_budget.py DECISION_WINDOW_MS NEURONS RATE\n"
            "       gate_snn_budget.py   # scan default JSONLs, write gate-snn-fuzz.md",
            file=sys.stderr,
        )
        return 2
    return scan_and_report()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
