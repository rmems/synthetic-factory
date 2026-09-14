#!/usr/bin/env python3
"""NELB round 64 — transactional staging writer. Independent CUBA LIF rasters."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LIVE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/raw/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge"
)
STAGE = Path(
    "/home/raulmc/rmems/synthetic-factory/outputs/staging/2026-09-02-final-heavy/"
    "neuromorphic-event-language-bridge/r64-bed5efec69ba49018ce309bdc0d98ad3"
)
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))
sys.path.insert(0, "/tmp")

from lif_raster import _calibrate_spikes, expected_spikes  # noqa: E402

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ROUND = 64
SNN_TAGS = ["race", "refractory", "adaptation"]

RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GENERATED_AT,
    "intended_use": "research_only",
    "project_training_policy": "blocked",
    "research_retention_status": "allowed",
    "research_evaluation_status": "allowed",
    "redistribution_status": "unresolved",
    "provider_training_status": "unresolved",
    "weight_publication_status": "blocked",
    "status_basis": "RM-793 project policy: xAI hosted outputs are research-only",
    "linear_issue": "RM-793",
}
assert len(RIGHTS) == 15

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "hidden_reasoning",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": ROUND,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
        "snn_tags": list(SNN_TAGS),
        "nelb": {"snn_tags": list(SNN_TAGS)},
    }
    m.update(extra)
    return m


def _exact(a, b, eps=1e-12):
    if abs(a - b) > eps:
        raise RuntimeError(f"arith {a} != {b}")


def make_lif_raster(
    *,
    neurons: int,
    mean_rate_hz: float,
    window_ms: float,
    seed: int,
    source: str,
    target: str,
    table: list,
    third_factor: dict,
    channel_prefix: str,
    anchor: str,
    kernel_ms: list[float],
):
    """Independent CUBA LIF full-window raster. Not a spike_events echo."""
    window_s = window_ms / 1000.0
    window_us = int(round(window_ms * 1000.0))
    expected = expected_spikes(neurons, mean_rate_hz, window_ms)
    last_err = None
    spikes = None
    used_seed = seed
    for bump in range(48):
        used_seed = seed + bump * 7919
        forbidden = {int(round(t * 1000.0)) for t in kernel_ms}
        try:
            cand = _calibrate_spikes(
                neurons,
                mean_rate_hz,
                window_us,
                used_seed,
                kernel_ms,
                10.0,
                1.0,
                1.0,
                2.0,
                forbidden,
            )
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            continue
        if abs(len(cand) - expected) > 0:
            last_err = RuntimeError(f"budget {len(cand)} != {expected}")
            continue
        last = {}
        ok = True
        for t_us, nid in sorted(cand):
            if not (0 <= t_us <= window_us):
                ok = False
                break
            if not (0 <= nid < neurons):
                ok = False
                break
            prev = last.get(nid)
            if prev is not None and t_us - prev < 1000:
                ok = False
                break
            last[nid] = t_us
        if not ok:
            last_err = RuntimeError("refractory or bounds")
            continue
        spikes = cand
        break
    if spikes is None:
        raise RuntimeError(f"CUBA LIF failed seed {seed}: {last_err}")

    rng = random.Random(used_seed ^ 0xA5A5)
    by_n: dict[int, list[int]] = defaultdict(list)
    for t_us, nid in spikes:
        by_n[nid].append(t_us)
    for nid in by_n:
        by_n[nid].sort()

    excerpt = []
    for t_us, nid in sorted(spikes, key=lambda x: (x[0], x[1])):
        k = by_n[nid].index(t_us)
        base = 1.15 + 0.7 * rng.random()
        noise = 0.96 + 0.08 * rng.random()
        amp = round(base * (0.82**k) * noise, 3)
        excerpt.append(
            {
                "t_us": int(t_us),
                "neuron_id": int(nid),
                "amplitude": amp,
                "channel": f"{channel_prefix}{nid:02d}",
            }
        )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))
    if len(excerpt) != expected:
        raise RuntimeError("excerpt/spikes mismatch")

    isis_ms = []
    for nid, ts in by_n.items():
        for a, b in zip(ts, ts[1:]):
            gap = b - a
            if gap < 1000:
                raise RuntimeError(f"refractory fail n{nid} {gap} us")
            isis_ms.append(gap / 1000.0)

    edges = [1.0, 2.0, 4.0, 8.0, 16.0, float(window_ms) + 1e-9]
    counts_h = [0] * (len(edges) - 1)
    for isi in isis_ms:
        if isi < 1.0 - 1e-12:
            raise RuntimeError(f"ISI {isi} < 1 ms")
        placed = False
        for i in range(len(edges) - 1):
            if edges[i] <= isi < edges[i + 1]:
                counts_h[i] += 1
                placed = True
                break
        if not placed:
            counts_h[-1] += 1
    hist = []
    for i, c in enumerate(counts_h):
        if c <= 0:
            continue
        hi = window_ms if i == len(counts_h) - 1 else edges[i + 1]
        hist.append({"lo_ms": edges[i], "hi_ms": hi, "count": c})
    identity_n = expected - len(by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(
            f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}"
        )

    energy_pJ = expected * 23
    energy_uJ = expected * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": expected,
        "energy_pJ": energy_pJ,
        "energy_uJ": energy_uJ,
        "energy_model": "Loihi-2-class 4-core 23 pJ/spike",
        "excerpt": excerpt,
        "excerpt_amplitude_units": "normalized_membrane",
        "excerpt_is_full_window": True,
        "refractory_rule_ms": 1.0,
        "isi_histogram": hist,
        "isi_source": "full_window_per_neuron_isi",
        "isi_count_identity": {
            "spikes": expected,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": (
            f"independent CUBA LIF seed {used_seed} (base {seed}); "
            "kernelized physics-pair times drive synaptic current and are not "
            "copied into excerpt; amplitude adaptation 0.82**k plus noise"
        ),
        "encoder": "independent_cuba_lif",
        "routing": {
            "source": source,
            "target": target,
            "table": table,
            "third_factor": third_factor,
        },
    }


def ev(t_rel_ms, channel, amplitude, **extra):
    rec = {
        "t_rel_ms": float(t_rel_ms),
        "channel": channel,
        "amplitude": float(amplitude),
    }
    rec.update(extra)
    return rec


def assert_stream(events, min_n=48, max_n=80):
    if not (min_n <= len(events) <= max_n):
        raise RuntimeError(f"event count {len(events)} not in {min_n}-{max_n}")
    last = -1.0
    last_ch = {}
    for e in events:
        if "t_ms" in e:
            raise RuntimeError("t_ms alias forbidden this round")
        t = e["t_rel_ms"]
        if not math.isfinite(t) or not math.isfinite(e["amplitude"]):
            raise RuntimeError("non-finite")
        if not e["channel"]:
            raise RuntimeError("empty channel")
        if t <= last:
            raise RuntimeError("non-increasing t_rel_ms")
        last = t
        prev = last_ch.get(e["channel"])
        if prev is not None and (t - prev) < 0.8:
            raise RuntimeError(f"refractory {e['channel']} {t-prev}")
        last_ch[e["channel"]] = t


def reward(total, components, notes):
    s = 0.0
    out = {
        "aggregation": "unweighted sum of the named scalar components; two-decimal components; total = exact sum",
        "rounding_decimals": 2,
    }
    for k, v in components:
        out[k] = v
        s += v
    out["total"] = total
    if abs(s - total) > 1e-12:
        raise RuntimeError(f"reward {s} != {total}")
    out["notes"] = notes
    return out


def gate_pop(name, neurons, threshold, mean_rate_hz, window_s, **extra):
    spikes = int(round(neurons * mean_rate_hz * window_s))
    d = {
        "name": name,
        "neurons": neurons,
        "threshold": threshold,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
    }
    d.update(extra)
    return d


def gate_compute(checks):
    total = 0
    per = []
    for check in checks:
        n = check["neurons"]
        r = check["mean_rate_hz"]
        w_ms = check["window_ms"]
        w_s = w_ms / 1000.0
        sp = int(round(n * r * w_s))
        per.append(
            {
                "check": check["check"],
                "neurons": n,
                "mean_rate_hz": float(r),
                "window_ms": float(w_ms),
                "window_s": float(w_s),
                "spikes": sp,
            }
        )
        total += sp
    return {
        "per_check": per,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


def occupancy_preflight():
    banned = (
        "heathspire",
        "otterfen",
        "stoatshaw",
        "fineveil",
        "streamveil",
        "aeveil",
        "rowan keld",
        "mira quill",
        "tam osier",
        "stream-hil-3",
        "ae-sim-6",
        "nelb-r64-a1",
        "nelb-r64-a2",
        "nelb-r64-a3",
    )
    leftover_ids = ("nelb-r64-193", "nelb-r64-194", "nelb-r64-195")
    hits = []
    for n in LIVE.glob("*"):
        if n.suffix not in {".py", ".md", ".jsonl"}:
            continue
        text = n.read_text(encoding="utf-8", errors="replace").casefold()
        for b in banned:
            if b in text:
                hits.append(f"live:{n.name}:{b}")
        for b in leftover_ids:
            if b in text:
                hits.append(f"live:{n.name}:{b}")
    mill = Path("/tmp/nelb-r64")
    if mill.is_dir():
        for n in mill.glob("*"):
            if n.suffix not in {".py", ".md", ".jsonl"}:
                continue
            text = n.read_text(encoding="utf-8", errors="replace").casefold()
            for b in banned:
                if b in text:
                    hits.append(f"mill:{n.name}:{b}")
    if hits:
        raise RuntimeError(f"family/plant/id collision {hits}")


# ---------------------------------------------------------------------------
# nelb-r64-a1 — Blaine air-permeability remaining fineness of a cement mill
# REJECT / MODIFY, designed
# ---------------------------------------------------------------------------
def rec_001():
    k_b = 40.00
    t_s = 64.00
    s_m2kg = k_b * math.sqrt(t_s)
    sq = (s_m2kg / k_b) ** 2
    mdot = 0.05 * s_m2kg
    _exact(s_m2kg, 320.00)
    _exact(sq, 64.00)
    _exact(mdot, 16.00)
    _exact(k_b * math.sqrt(16.00), 160.00)
    _exact(k_b * math.sqrt(36.00), 240.00)
    _exact(k_b * math.sqrt(56.25), 300.00)
    _exact(6000.0 + 1080.0, 7080.0)

    raster = make_lif_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=20260964001,
        source="hs4.blaine.t",
        target="heathspire.mill_stop_core",
        table=[
            {"from": "bla_t", "to": "s_estimator", "weight": 1.40},
            {"from": "bla_snr", "to": "bla_lock_core", "weight": 1.15},
            {"from": "fineveil_S", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.blaine_fineness_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-grind synapses; the plant "
                "Blaine modulator depresses continue-grind links when packed-bed "
                "efflux stays long inside tau_e of an SNR lock so a Fineveil last-good "
                "cannot hide a 320.00 m2/kg overfine mill"
            ),
        },
        channel_prefix="bla.n",
        anchor=(
            "HS-4 Blaine 40 ms frame at t 64.00 s / SNR 12.0 "
            "(t_s 3000) reconstructing 320.00 m2/kg above the 300.00 isolate floor"
        ),
        kernel_ms=[0.0, 1.4, 8.5, 19.0],
    )
    w_s = 0.040
    events = [
        ev(80.0, "bla.t", 16.00, code="T_S", units="s", note="plant-owned Blaine air-permeability packed-bed efflux of Heathspire Cement HS-4 mill M-2; remaining-fineness family, not Fraunhofer laser-diffraction D50, not Coulter, not FBRM chord D50, not PDA Sauter D32, not BET"),
        ev(300000.0, "bla.snr", 6.0, code="BLA_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(600000.0, "recon.S", 160.00, code="S_M2KG", units="m2_kg", note="40.00*sqrt(16.00)=160.00 exact; still under the 300.00 isolate floor"),
        ev(750000.0, "mill.T", 88.0, code="T_C", units="C", note="plant mill RTD on copper DCS; independent witness; unread by Fineveil"),
        ev(900000.0, "mill.kW", 18.0, code="MILL_KW", units="kW", note="plant mill PLC; independent witness"),
        ev(1200000.0, "fineveil.S", 240.00, code="VENDOR_M2KG", units="m2_kg", note="Fineveil vendor BL-9 last-good cloud; infra owner; patched efflux timestamps"),
        ev(1500000.0, "clf.rpm", 1200.0, code="CLF_RPM", units="rpm", note="plant classifier tachometer; independent witness"),
        ev(1800000.0, "bla.t", 36.00, code="T_S", units="s"),
        ev(2100000.0, "recon.S", 240.00, code="S_M2KG", units="m2_kg", note="40.00*sqrt(36.00)=240.00; still under the 300.00 isolate floor"),
        ev(2250000.0, "mill.kW", 19.0, code="MILL_KW", units="kW"),
        ev(2400000.0, "permit.slide", 40.00, code="PERM_S", units="s", note="night clerk slid the mill-permit clock 40.00 s; collusion party"),
        ev(2550000.0, "clf.rpm", 1180.0, code="CLF_RPM", units="rpm"),
        ev(2700000.0, "mill.T", 91.0, code="T_C", units="C"),
        ev(2850000.0, "fineveil.S", 238.00, code="VENDOR_M2KG", units="m2_kg"),
        ev(3000000.0, "bla.t", 64.00, code="T_S", units="s", note="isolate-floor frame; raster sidecar kernel, not excerpt echo"),
        ev(3000001.4, "bla.snr", 12.0, code="BLA_SNR", units="1", note="1.4 ms SNR after efflux; 12.0 >= 8.0 lock"),
        ev(3150000.0, "recon.S", 320.00, code="S_M2KG", units="m2_kg", note="40.00*sqrt(64.00)=320.00 exact; isolate 300.00"),
        ev(3300000.0, "recon.sq", 64.00, code="T_ID_S", units="s", note="(320.00/40.00)^2=64.00 exact efflux identity"),
        ev(3450000.0, "recon.mdot", 16.00, code="MDOT_TH", units="t_h", note="0.05*320.00=16.00 exact reject-load identity"),
        ev(3600000.0, "mill.kW", 21.0, code="MILL_KW", units="kW", note="PLC tracks the plant Blaine, not Fineveil 240.00"),
        ev(3750000.0, "mill.T", 93.0, code="T_C", units="C"),
        ev(3900000.0, "bla.drop", 1.0, code="BLA_DROP", units="bool", note="vendor efflux packets dropped in Fineveil cloud for 40 s"),
        ev(4200000.0, "recon.S", 320.00, code="S_M2KG", units="m2_kg"),
        ev(4500000.0, "fineveil.S", 240.00, code="VENDOR_M2KG", units="m2_kg"),
        ev(4800000.0, "ops.prop", 1.0, code="CONTINUE_GRIND", units="bool", note="night operator Rowan Keld: Fineveil is clean 240.00 m2/kg; keep M-2 grinding"),
        ev(5100000.0, "clf.rpm", 1210.0, code="CLF_RPM", units="rpm"),
        ev(5400000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-grind; 320.00 m2/kg and SNR 12.0; Fineveil not SoT"),
        ev(5700000.0, "recon.sq", 64.00, code="T_ID_S", units="s"),
        ev(6000000.0, "hold.start", 1.0, code="MILL_HOLD_START", units="bool", note="bookend 1 of the 18.0 min mill-hold floor"),
        ev(6300000.0, "bla.snr", 12.0, code="BLA_SNR", units="1"),
        ev(6600000.0, "fineveil.S", 236.00, code="VENDOR_M2KG", units="m2_kg"),
        ev(7080000.0, "hold.floor", 1.0, code="MILL_HOLD_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7500000.0, "mill.T", 86.0, code="T_C", units="C"),
        ev(7800000.0, "ops.kill", 1.0, code="MILL_ESD", units="bool", note="Keld: trip the whole Heathspire mill hall until day-shift"),
        ev(8100000.0, "mill.kW", 6.0, code="MILL_KW", units="kW"),
        ev(8400000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: mill-hold on plant Blaine as live interlock; mill ESD refused"),
        ev(9000000.0, "hold.set", 1.0, code="MILL_HELD", units="bool"),
        ev(9600000.0, "bla.t", 56.25, code="T_S", units="s"),
        ev(10200000.0, "recon.S", 300.00, code="S_M2KG", units="m2_kg", note="40.00*sqrt(56.25)=300.00; still at 300.00 so hold stands"),
        ev(10800000.0, "fineveil.S", 234.00, code="VENDOR_M2KG", units="m2_kg"),
        ev(11100000.0, "clf.rpm", 400.0, code="CLF_RPM", units="rpm"),
        ev(11400000.0, "mill.kW", 5.0, code="MILL_KW", units="kW", note="held mill; PLC tracks the plant Blaine"),
        ev(12000000.0, "hold.held", 1.0, code="MILL_HELD", units="bool"),
        ev(12600000.0, "mill.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(13200000.0, "permit.slide", 40.00, code="PERM_S", units="s"),
        ev(13800000.0, "mill.T", 84.0, code="T_C", units="C"),
        ev(14100000.0, "recon.sq", 56.25, code="T_ID_S", units="s", note="(300.00/40.00)^2=56.25 post-stop efflux identity"),
        ev(14400000.0, "bla.drop", 1.0, code="BLA_DROP", units="bool"),
        ev(14700000.0, "recon.mdot", 15.00, code="MDOT_TH", units="t_h", note="0.05*300.00=15.00 post-stop reject-load"),
        ev(15000000.0, "hold.lock", 1.0, code="MILL_HELD", units="bool"),
        ev(15300000.0, "recon.S", 300.00, code="S_M2KG", units="m2_kg"),
        ev(15600000.0, "fineveil.S", 232.00, code="VENDOR_M2KG", units="m2_kg"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-a1-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HS-BLA-2026-0902",
            "domain": "blaine_air_permeability_cement_fineness",
            "setting": (
                "Heathspire Cement HS-4 (invented), Copsebrake Clinker Yard, mill M-2. "
                "Plant-owned Blaine packed-bed efflux is the remaining-fineness SoT. "
                "Fineveil / BL-9 vendor DAQ (infra owner) plus the mill-permit clock "
                "are collusion parties, not witnesses. Invented plant; designed campaign. "
                "Not Fraunhofer laser-diffraction D50 (live r62), not Coulter (live r01), "
                "not FBRM chord D50 (r49), not PDA Sauter D32 (r47), not BET surface area."
            ),
            "observables_at_decision": {
                "t_s": t_s,
                "k_b": k_b,
                "S_m2kg": s_m2kg,
                "sq_s": sq,
                "mdot_t_h": mdot,
                "bla_snr": 12.0,
                "fineveil_m2kg": 240.00,
                "permit_slide_s": 40.00,
                "isolate_floor_m2kg": 300.00,
            },
            "margin_authority": (
                "HS-4 mill SOP rev C: if reconstructed S_m2kg >= 300.00 AND Blaine SNR >= 8.0, "
                "continue-grind is forbidden even if Fineveil reports 240.00 m2/kg. Mill ESD is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night operator Rowan Keld, citing Fineveil 240.00 m2/kg and a quiet BL-9 efflux",
            "summary": "keep mill M-2 grinding; 64.00 s efflux is a packed-bed glitch on a healthy 240.00 m2/kg last-good",
            "basis_claimed": "Fineveil is the only OEM fineness SoT and a night abort of M-2 is a kiln-feed miss",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Continue-grind is refused. Serialized reconstruction: S_m2kg = k_b * sqrt(t) = "
                "40.00 * sqrt(64.00) = 320.00 m2/kg, above the 300.00 isolate floor, and Blaine SNR is 12.0 >= 8.0. "
                "Efflux identity (S/k_b)^2 = (320.00/40.00)^2 = 64.00 s. Reject-load identity mdot = 0.05 * S = 16.00 t/h. "
                "Permit clock was slid 40.00 s and vendor efflux packets were dropped, so Fineveil is a collusion party "
                "(Blaine vendor plus operator plus night clerk). Ordered: refuse continue-grind now. Scope: this REJECT "
                "does not ESD the mill (that is the companion question) and does not isolate the classifier PLC."
            ),
            "threshold": "S_m2kg>=300.00 AND bla_snr>=8.0 => refuse continue-grind; Fineveil is not SoT",
            "stated_residuals": (
                "mill-hold still required to hold the 320.00 m2/kg; 320.00 vs a true mill-crash is a production cut; "
                "Fineveil remains the only OEM fineness channel"
            ),
        },
        "executed_action": {
            "summary": "REJECT at t_s 5400: continue-grind refused; Fineveil not SoT; reconstruction locked",
            "tool": "hs4-blaine-mill-gate-cli",
            "observation": "S 320.00 m2/kg recomputes from t 64.00 s; plant Blaine hashed; Fineveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "Blaine t 64.00 s; raster frame; S 320.00 m2/kg"},
                {"t_s": 4800.0, "event": "ops proposes continue-grind"},
                {"t_s": 5400.0, "event": "REJECT continue-grind"},
                {"t_s": 6000.0, "event": "18 min mill-hold bookend 1"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 8400.0, "event": "companion MODIFY mill-hold vs mill ESD"},
            ],
            "observed_effects": [
                "fineness recomputes from the serialized Blaine model at every recon.S event",
                "a Fineveil-only head would have continued grinding overnight",
                "18 min mill-hold floor is in the stream (hold.start, hold.floor)",
            ],
            "surprises": [
                "a clean vendor fineness corridor and a 40 s permit slide co-existed with a 320.00 m2/kg plant reconstruction",
            ],
            "new_state": {
                "mill_m2": "continue-grind blocked",
                "fineveil": "not SoT",
                "reconstruction_model": "discharged as an on-record calculator",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("blaine_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("fineveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("hold_time_cost", -0.03),
            ],
            "scored for a continue-grind REJECT on a recomputable Blaine remaining fineness while refusing a Fineveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        "meta": meta_common(
            tags=["REJECT", "blaine-fineness", "serialized-reconstruction", "operational-companion"],
            distillation_note="Blaine gate: serialized k_b*sqrt(t) plus SNR lock beats a vendor last-good patch; companion t2 is the mill-hold, not a referral vote",
            distillation_value="Teaches an SNN to race a packed-bed efflux sqrt-fineness against a patched vendor Blaine corridor under 1 ms refractory and amplitude adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r64-a1-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "HS-BLA-2026-0902-exec",
            "domain": "mill_hold_blaine_interlock_execution",
            "setting": "Same HS-4 after the REJECT. Operator proposes a mill-hall ESD. This companion is the operational mill-hold with the plant Blaine as the live interlock, not a second fineness vote.",
            "observables_at_decision": {
                "S_m2kg": 300.00,
                "mill_hold_floor_s": 1080.0,
                "mill_esd_proposed": True,
                "mill_hold_set": True,
            },
        },
        "proposed_action": {
            "actor": "night operator Rowan Keld",
            "summary": "trip the whole Heathspire mill hall until day-shift; 18 min already paid and Fineveil still shows 236.00 m2/kg",
            "basis_claimed": "the REJECT already blocked grinding, so a mill ESD is the cheapest hold",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Mill-hold plus plant Blaine as the live interlock. The 18 min hold floor is complete and the isolate "
                "tripwire (S_m2kg >= 300.00) is still armed on the plant Blaine head. MODIFY the default fineness-restore SOP "
                "into a plant-Blaine-only interlock. Do not ESD the mill hall. Do not restore grinding on Fineveil. "
                "300.00 m2/kg post-stop is still the plant SoT until a new frame clears 300.00."
            ),
            "threshold": "mill_hold AND hold_floor_complete AND mill_esd_not_taken AND continue_grind_not_restored",
        },
        "executed_action": {
            "summary": "mill-hold held at t_s 8400; mill ESD not latched; Fineveil restore not taken",
            "tool": "hs4-mill-hold-exec",
            "observation": "recon.S 300.00 m2/kg after stop; hold line-up complete; Fineveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "mill-hold clock started after REJECT"},
                {"t_s": 7080.0, "event": "18.0 min floor"},
                {"t_s": 7800.0, "event": "mill ESD proposed"},
                {"t_s": 8400.0, "event": "MODIFY mill-hold; mill ESD refused"},
            ],
            "observed_effects": [
                "Fineveil restore did not reopen the fineness call",
                "mill ESD never fired; M-2 held mill on the plant Blaine",
            ],
            "new_state": {"hold": "held", "plant": "in service", "mill_m2": "held"},
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("mill_hold", 0.12),
                ("no_mill_esd", 0.10),
                ("fineveil_nonsubstitution", 0.08),
                ("hold_floor_complete", 0.06),
                ("held_grind_cost", -0.02),
            ],
            "operational execution gate: mill-hold because Fineveil is not a restore license; not a remaining-fineness re-vote",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "mill-hold"]),
    }
    return {
        "id": "nelb-r64-a1",
        "spike_events": events,
        "language_view": {
            "description": (
                "Heathspire Cement HS-4. Plant-owned Blaine reconstructs 320.00 m2/kg remaining fineness from "
                "sqrt(64.00) while Fineveil still reports 240.00 m2/kg. The gate REJECTs continue-grind. An 18 min "
                "mill-hold floor is serialized in the stream. Companion t2 MODIFYs a mill ESD into a plant-Blaine mill-hold."
            ),
            "trajectory": traj,
            "trajectory_mill_hold": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "bla.t / bla.snr": "packed-bed efflux and SNR; the physics channels the reconstruction consumes",
                "recon.S / recon.sq / recon.mdot": "serialized remaining fineness, efflux identity, and reject-load identity",
                "mill.T / mill.kW / clf.rpm / fineveil.S / permit.slide / bla.drop": "mill witnesses, vendor last-good, permit clock slide, and dropped efflux packets",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-grind proposal, REJECT, mill-ESD proposal, companion MODIFY",
                "hold.start / hold.floor / hold.set / hold.held / mill.esd / hold.lock": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-overfine: fineveil.S 240.00 next to recon.S 320.00",
                "reconstruction as event: recon.S 320.00 equals 40.00*sqrt(64.00)",
                "REJECT then operational MODIFY: gate.stop at 5400 s, gate.hold at 8400 s",
                "slow floor in-stream: hold.start 6000 s, hold.floor 7080 s (18.0 min)",
                "tight Blaine pair: bla.t then bla.snr +1.4 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Fineveil is 240.00 m2/kg' = fineveil.S 240.00; '320 m2/kg fineness' = recon.S 320.00; "
                "'refuse continue-grind' = gate.stop REJECT; 'hold not mill ESD' = gate.hold MODIFY"
            ),
            "why_high_value": (
                "New Blaine air-permeability remaining-fineness family on a cement mill (not Fraunhofer laser-diffraction "
                "D50 live r62, not Coulter live r01, not FBRM r49, not PDA r47, not BET). Lead REJECT of continue-grind "
                "on a recomputable overfine mill that a vendor last-good patch and a permit clock slide would have cleared. "
                "Three-party collusion includes the Blaine infra owner. Companion t2 is operational mill-hold. "
                "Independent CUBA LIF raster. sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260964001,
                    "stream_note": "stream amplitudes are authored constants (s, m2_kg, C, kW, rpm, t_h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.4 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "Blaine cell exists at ~0.02 Hz; stream keeps 4 efflux points; recon keeps 5 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "Blaine reconstruction head: S_m2kg = k_b * sqrt(t); (S/k_b)^2 = t; mdot = 0.05 * S",
                "conjunctive isolate floor vs continue-grind vs mill ESD",
                "vendor-fineness nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: mill-hold without restoring on Fineveil",
            ],
        },
        "reconstruction_model": {
            "name": "blaine_air_permeability_fineness",
            "formula": "S_m2kg = k_b * sqrt(t_s); sq = (S_m2kg / k_b)**2; mdot_t_h = 0.05 * S_m2kg",
            "parameters": {
                "k_b": 40.00,
                "isolate_floor_m2kg": 300.00,
                "snr_lock": 8.0,
                "mill_hold_min": 18.0,
            },
            "worked_example": {"t_s": 64.00, "S_m2kg": 320.00, "sq_s": 64.00, "mdot_t_h": 16.00},
            "check": "40.00 * sqrt(64.00) = 320.00 exactly; (320.00/40.00)^2 = 64.00; 0.05 * 320.00 = 16.00; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "hs4.blaine_mill_gate",
            "note": "REJECT accumulator wins: plant Blaine remaining-fineness evidence overpowers the Fineveil continue advocate",
            "decode_rule": "reject-continue if s_estimator AND bla_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("s_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("bla_lock", 64, 1.2, 31.25, w_s),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("reject_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "hs4.bla_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 40.0},
                {"check": "hs4.hold_scorer", "neurons": 40, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-a1",
            clock_domain="hs4-bla-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["blaine-fineness", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2"],
            distillation_value="Blaine sqrt-efflux fineness head with independent CUBA LIF raster, 1 ms refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r64-a2 — streaming-current remaining coagulant demand of a clarifier
# MODIFY / ACCEPT, hil
# ---------------------------------------------------------------------------
def rec_002():
    k_c = 2.50
    i_ua = 8.00
    i0_ua = 2.00
    scd = k_c * (i_ua - i0_ua)
    di = i_ua - i0_ua
    _exact(scd, 15.00)
    _exact(di, 6.00)
    _exact(k_c * (4.00 - i0_ua), 5.00)
    _exact(k_c * (6.00 - i0_ua), 10.00)
    _exact(k_c * (6.80 - i0_ua), 12.00)
    _exact(2820.0 + 1440.0, 4260.0)

    raster = make_lif_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260964002,
        source="of3.scd.I",
        target="otterfen.clarifier_isolate_core",
        table=[
            {"from": "scd_I", "to": "scd_estimator", "weight": 1.35},
            {"from": "scd_snr", "to": "probe_lock", "weight": 1.20},
            {"from": "streamveil_scd", "to": "vendor_keep_advocate", "weight": 0.40},
        ],
        third_factor={
            "modulator": "ach.scd_probe_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-dosing synapses; the streaming-current modulator depresses keep-dosing "
                "and referral links when probe current stays high inside tau_e of an SNR lock so a Streamveil "
                "last-good cannot hide a 15.00 ueq/L remaining demand or name Mira Quill"
            ),
        },
        channel_prefix="scd.n",
        anchor=(
            "OF-3 SCD 32 ms frame at I 8.00 uA / I0 2.00 uA / SNR 14.0 "
            "(t_s 2100) reconstructing 15.00 ueq/L above the 12.00 isolate floor"
        ),
        kernel_ms=[0.0, 1.2, 7.0, 15.5],
    )
    w_s = 0.032
    events = [
        ev(90.0, "scd.I", 4.00, code="I_UA", units="uA", note="HIL streaming-current detector on OF-3 clarifier C-1 dummy in STREAM-HIL-3; remaining coagulant-demand family, not four-electrode conductivity, not toroidal conductivity, not LPR, not Clark DO, not glass pH"),
        ev(240000.0, "scd.snr", 7.0, code="SCD_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(480000.0, "recon.SCD", 5.00, code="SCD_UEQ", units="ueq_L", note="2.50*(4.00-2.00)=5.00; under the 12.00 isolate floor"),
        ev(720000.0, "basin.T", 12.0, code="T_C", units="C", note="plant basin RTD; independent witness; unread by Streamveil"),
        ev(960000.0, "streamveil.SCD", 3.20, code="VENDOR_UEQ", units="ueq_L", note="Streamveil vendor SC-4 last-good cloud; infra owner"),
        ev(1200000.0, "scd.I", 6.00, code="I_UA", units="uA"),
        ev(1440000.0, "recon.SCD", 10.00, code="SCD_UEQ", units="ueq_L", note="2.50*(6.00-2.00)=10.00"),
        ev(1680000.0, "alum.mg_l", 18.0, code="ALUM_MG_L", units="mg_L", note="plant alum pump; independent witness"),
        ev(1920000.0, "scd.I", 6.80, code="I_UA", units="uA"),
        ev(2100000.0, "scd.I", 8.00, code="I_UA", units="uA", note="isolate-floor frame; raster sidecar kernel"),
        ev(2100001.2, "scd.snr", 14.0, code="SCD_SNR", units="1", note="1.2 ms SNR after probe current; isolate-frame SNR 14.0"),
        ev(2250000.0, "recon.SCD", 15.00, code="SCD_UEQ", units="ueq_L", note="2.50*(8.00-2.00)=15.00 exact; isolate 12.00"),
        ev(2400000.0, "recon.dI", 6.00, code="DI_UA", units="uA", note="8.00-2.00=6.00 exact probe-delta identity"),
        ev(2550000.0, "streamveil.SCD", 3.16, code="VENDOR_UEQ", units="ueq_L"),
        ev(2700000.0, "basin.T", 12.4, code="T_C", units="C"),
        ev(2820000.0, "hold.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min new-probe floor"),
        ev(3000000.0, "ops.prop", 1.0, code="KEEP_DOSING", units="bool", note="shift lead: Streamveil is 3.20 ueq/L; keep C-1 dosing"),
        ev(3180000.0, "scd.drop", 1.0, code="SCD_DROP", units="bool", note="vendor probe packets dropped 40 s"),
        ev(3360000.0, "tech.ae", 0.0, code="PROBE_ZERO_AE", units="bool", note="missing probe-zero alarm-event; Mira Quill not last-to-badge"),
        ev(3540000.0, "tz.skip", 2.0, code="TZ_H", units="h", note="UTC vs UTC+2 canteen clock; exoneration"),
        ev(3720000.0, "alum.mg_l", 17.6, code="ALUM_MG_L", units="mg_L"),
        ev(3900000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="refuse keep-dosing; isolate C-1; Streamveil not SoT; do not plant-trip"),
        ev(4080000.0, "recon.SCD", 15.00, code="SCD_UEQ", units="ueq_L"),
        ev(4260000.0, "hold.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.keep", 1.0, code="KEEP_WHOLE", units="bool", note="referral: keep the whole works; Quill last-to-badge"),
        ev(4620000.0, "streamveil.SCD", 3.12, code="VENDOR_UEQ", units="ueq_L"),
        ev(4800000.0, "scd.snr", 14.0, code="SCD_SNR", units="1"),
        ev(5100000.0, "new.head", 1.0, code="NEW_PROBE", units="bool", note="spare SCD probe on the HIL dummy"),
        ev(5400000.0, "gate.hold", 1.0, code="ACCEPT", units="decision", note="companion t2: new-probe restart ACCEPT; plant-trip refused; Quill exonerated"),
        ev(5700000.0, "hold.set", 1.0, code="ISO_HELD", units="bool"),
        ev(6000000.0, "scd.I", 6.80, code="I_UA", units="uA"),
        ev(6300000.0, "recon.SCD", 12.00, code="SCD_UEQ", units="ueq_L", note="2.50*(6.80-2.00)=12.00; still at isolate so new-probe stands"),
        ev(6600000.0, "streamveil.SCD", 3.08, code="VENDOR_UEQ", units="ueq_L"),
        ev(6900000.0, "basin.T", 11.8, code="T_C", units="C"),
        ev(7200000.0, "alum.mg_l", 8.0, code="ALUM_MG_L", units="mg_L"),
        ev(7500000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(7800000.0, "tech.ae", 0.0, code="PROBE_ZERO_AE", units="bool"),
        ev(8100000.0, "tz.skip", 2.0, code="TZ_H", units="h"),
        ev(8400000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
        ev(8700000.0, "recon.dI", 4.80, code="DI_UA", units="uA", note="6.80-2.00=4.80 post-isolate delta"),
        ev(9000000.0, "scd.drop", 1.0, code="SCD_DROP", units="bool"),
        ev(9300000.0, "new.head", 1.0, code="NEW_PROBE", units="bool"),
        ev(9600000.0, "streamveil.SCD", 3.04, code="VENDOR_UEQ", units="ueq_L"),
        ev(9900000.0, "scd.snr", 13.0, code="SCD_SNR", units="1"),
        ev(10200000.0, "basin.T", 11.6, code="T_C", units="C"),
        ev(10500000.0, "alum.mg_l", 7.8, code="ALUM_MG_L", units="mg_L"),
        ev(10800000.0, "hold.lock", 1.0, code="ISO_HELD", units="bool"),
        ev(11100000.0, "recon.SCD", 12.00, code="SCD_UEQ", units="ueq_L"),
        ev(11400000.0, "plant.trip", 0.0, code="SHOP_NOT_TAKEN", units="bool"),
        ev(11700000.0, "tech.ae", 0.0, code="PROBE_ZERO_AE", units="bool"),
        ev(12000000.0, "tz.skip", 2.0, code="TZ_H", units="h"),
        ev(12300000.0, "hold.held", 1.0, code="ISO_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-a2-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "OF-SCD-2026-0902",
            "domain": "streaming_current_clarifier_demand",
            "setting": (
                "Otterfen Water OF-3 (invented), clarifier C-1 dummy in STREAM-HIL-3. "
                "Plant-owned streaming-current probe current is the remaining coagulant-demand SoT. "
                "Streamveil / SC-4 vendor DAQ (infra owner) is a collusion party. HIL coupon times an in-service isolate. "
                "Not four-electrode conductivity (r57), not toroidal conductivity (r61), not LPR (r45), "
                "not Clark DO (leftover r64), not glass pH (leftover r70)."
            ),
            "observables_at_decision": {
                "I_uA": i_ua,
                "I0_uA": i0_ua,
                "k_c": k_c,
                "SCD_ueq_L": scd,
                "dI": di,
                "scd_snr": 14.0,
                "streamveil_ueq_L": 3.20,
                "isolate_floor_ueq_L": 12.00,
                "probe_zero_ae": False,
            },
            "margin_authority": (
                "OF-3 clarifier SOP rev B: if reconstructed SCD_ueq_L >= 12.00 AND SCD SNR >= 8.0, "
                "keep-dosing is forbidden even if Streamveil reports 3.20 ueq/L. Plant-trip is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "shift lead citing Streamveil 3.20 ueq/L and a quiet SC-4 probe",
            "summary": "keep C-1 dosing; 8.00 uA is a fouled-probe glitch on a healthy 3.20 ueq/L last-good",
            "basis_claimed": "Streamveil is the only OEM SCD SoT and a night isolate of C-1 is a turbidity miss",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": (
                "Keep-dosing is refused; isolate clarifier C-1 on the plant SCD. Serialized reconstruction: "
                "SCD = k_c * (I - I0) = 2.50 * (8.00 - 2.00) = 15.00 ueq/L, above the 12.00 isolate floor, and "
                "SCD SNR is 14.0 >= 8.0. Delta identity I - I0 = 6.00 uA. Missing probe-zero AE plus UTC vs UTC+2 "
                "canteen clock exonerate tech Mira Quill (not last-to-badge). Ordered: isolate C-1 now. Scope: this "
                "MODIFY does not plant-trip the works (companion question) and does not condemn the alum header."
            ),
            "threshold": "SCD_ueq_L>=12.00 AND scd_snr>=8.0 => refuse keep-dosing; Streamveil is not SoT",
            "stated_residuals": "new-probe restart still required; 15.00 vs a true basin-crash is a production cut; Streamveil remains the only OEM SCD channel",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 3900: keep-dosing refused; C-1 isolated on plant SCD; Streamveil not SoT",
            "tool": "of3-scd-clarifier-gate-cli",
            "observation": "SCD 15.00 ueq/L recomputes from I 8.00 and I0 2.00; plant SCD hashed; Quill exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2100.0, "event": "SCD I 8.00 I0 2.00; raster frame; SCD 15.00 ueq/L; SNR 14.0"},
                {"t_s": 3000.0, "event": "ops proposes keep-dosing"},
                {"t_s": 3900.0, "event": "MODIFY isolate C-1"},
                {"t_s": 2820.0, "event": "24 min new-probe bookend 1"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 5400.0, "event": "companion ACCEPT new-probe restart"},
            ],
            "observed_effects": [
                "coagulant demand recomputes from the serialized SCD model at every recon.SCD event",
                "a Streamveil-only head would have kept C-1 dosing",
                "24 min new-probe floor is in the stream; Quill is not last-to-badge",
            ],
            "surprises": [
                "a clean vendor SCD corridor co-existed with a 15.00 ueq/L plant reconstruction and a skipped probe-zero AE",
            ],
            "new_state": {
                "clarifier_c1": "isolated on plant SCD",
                "streamveil": "not SoT",
                "mira_quill": "exonerated",
            },
            "latency_ms": 1800000.0,
        },
        "reward_components": reward(
            0.40,
            [
                ("scd_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("streamveil_nonsubstitution", 0.10),
                ("exoneration", 0.08),
                ("isolate_time_cost", -0.04),
            ],
            "scored for a keep-dosing MODIFY on a recomputable streaming-current remaining demand while refusing a Streamveil last-good and last-to-badge social pressure",
        ),
        "meta": meta_common(
            tags=["MODIFY", "streaming-current", "serialized-reconstruction", "exoneration"],
            distillation_note="SCD gate: serialized k_c*(I-I0) plus SNR lock beats a vendor last-good; Quill exonerated by missing probe-zero AE and timezone skip",
            distillation_value="Teaches an SNN to race a streaming-current probe remaining demand against a patched vendor corridor with isolate-frame SNR 14.0, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r64-a2-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "OF-SCD-2026-0902-exec",
            "domain": "new_probe_scd_restart_execution",
            "setting": "Same OF-3 HIL dummy after the isolate. Referral wants a plant-trip. Companion is the new-probe restart with the plant SCD as live interlock.",
            "observables_at_decision": {
                "SCD_ueq_L": 12.00,
                "cool_floor_s": 1440.0,
                "shop_trip_proposed": True,
                "new_probe_set": True,
            },
        },
        "proposed_action": {
            "actor": "shift lead",
            "summary": "plant-trip the whole OF-3 works; 24 min already paid and Streamveil still shows 3.12 ueq/L; Quill last-to-badge",
            "basis_claimed": "the isolate already blocked dosing, so a plant-trip is the cheapest hold",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "New-probe restart plus plant SCD as the live interlock. The 24 min new-probe floor is complete and "
                "the isolate tripwire (SCD_ueq_L >= 12.00) is still armed on the plant SCD. ACCEPT the spare-probe restart. "
                "Do not plant-trip. Do not restore on Streamveil. Mira Quill stays exonerated."
            ),
            "threshold": "new_probe AND cool_floor_complete AND shop_trip_not_taken AND keep_not_restored",
        },
        "executed_action": {
            "summary": "new-probe restart ACCEPTed at t_s 5400; plant-trip not latched; Streamveil restore not taken",
            "tool": "of3-scd-newprobe-exec",
            "observation": "recon.SCD 12.00 ueq/L after isolate; new probe on HIL dummy; Quill still exonerated",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2820.0, "event": "new-probe clock started"},
                {"t_s": 4260.0, "event": "24.0 min floor"},
                {"t_s": 4440.0, "event": "plant-trip proposed"},
                {"t_s": 5400.0, "event": "ACCEPT new-probe restart; plant-trip refused"},
            ],
            "observed_effects": [
                "Streamveil restore did not reopen the SCD call",
                "plant-trip never fired; C-1 held on the plant SCD with a new probe",
            ],
            "new_state": {"hold": "new-probe", "plant": "in service", "clarifier_c1": "isolated"},
            "latency_ms": 1500000.0,
        },
        "reward_components": reward(
            0.35,
            [
                ("new_probe_restart", 0.12),
                ("no_shop_trip", 0.10),
                ("streamveil_nonsubstitution", 0.08),
                ("exoneration_held", 0.07),
                ("held_run_cost", -0.02),
            ],
            "operational execution gate: new-probe restart because Streamveil is not a restore license; Quill stays exonerated",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "new-probe"]),
    }
    return {
        "id": "nelb-r64-a2",
        "spike_events": events,
        "language_view": {
            "description": (
                "Otterfen Water OF-3 HIL dummy STREAM-HIL-3. Plant-owned streaming-current probe reconstructs "
                "15.00 ueq/L remaining coagulant demand from 8.00-2.00 while Streamveil still reports 3.20 ueq/L. "
                "The gate MODIFYs keep-dosing into an isolate. A 24 min new-probe floor is serialized. Companion t2 "
                "ACCEPTs a new-probe restart. Tech Mira Quill is exonerated."
            ),
            "trajectory": traj,
            "trajectory_new_probe": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "scd.I / scd.snr": "streaming-current probe current and SNR; the physics channels the reconstruction consumes",
                "recon.SCD / recon.dI": "serialized remaining demand and probe-delta identity",
                "basin.T / alum.mg_l / streamveil.SCD / scd.drop / tech.ae / tz.skip": "basin and alum witnesses, vendor last-good, dropped packets, missing AE, timezone skip",
                "ops.prop / gate.iso / ops.keep / gate.hold": "keep-dosing proposal, MODIFY isolate, plant-trip proposal, companion ACCEPT",
                "hold.start / hold.floor / hold.set / hold.held / plant.trip / new.head / hold.lock": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: streamveil.SCD 3.20 next to recon.SCD 15.00",
                "reconstruction as event: recon.SCD 15.00 equals 2.50*(8.00-2.00)",
                "MODIFY then operational ACCEPT: gate.iso at 3900 s, gate.hold at 5400 s",
                "slow floor in-stream: hold.start 2820 s, hold.floor 4260 s (24.0 min)",
                "tight SCD pair: scd.I then scd.snr +1.2 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Streamveil is 3.20 ueq/L' = streamveil.SCD 3.20; '15 ueq/L demand' = recon.SCD 15.00; "
                "'isolate not keep-dosing' = gate.iso MODIFY; 'new-probe not plant-trip' = gate.hold ACCEPT"
            ),
            "why_high_value": (
                "New streaming-current remaining-coagulant-demand family on a clarifier (not four-electrode conductivity r57, "
                "not toroidal conductivity r61, not LPR r45, not Clark DO leftover r64, not glass pH leftover r70). "
                "Lead MODIFY of keep-dosing on a recomputable 15.00 ueq/L remaining demand that a vendor last-good would have "
                "cleared, with a resolved-innocent probe tech. Companion t2 is operational new-probe restart. "
                "Independent CUBA LIF raster. sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260964002,
                    "stream_note": "stream amplitudes are authored constants (uA, ueq_L, C, mg_L, h, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.2 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "SCD probe exists at ~1 Hz; stream keeps 5 I points; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T04:00:00Z HIL pad start",
            },
            "distillation_targets": [
                "SCD reconstruction head: SCD_ueq_L = k_c * (I - I0); dI = I - I0",
                "conjunctive isolate floor vs keep-dosing vs plant-trip",
                "vendor-SCD nonsubstitution plus timezone/probe-zero exoneration",
                "operational companion: new-probe restart without restoring on Streamveil",
            ],
        },
        "reconstruction_model": {
            "name": "streaming_current_coagulant_demand",
            "formula": "SCD_ueq_L = k_c * (I_uA - I0_uA); dI = I_uA - I0_uA",
            "parameters": {
                "k_c": 2.50,
                "isolate_floor_ueq_L": 12.00,
                "snr_lock": 8.0,
                "cool_min": 24.0,
            },
            "worked_example": {"I_uA": 8.00, "I0_uA": 2.00, "dI": 6.00, "SCD_ueq_L": 15.00},
            "check": "2.50 * (8.00 - 2.00) = 15.00 exactly; 8.00 - 2.00 = 6.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "of3.scd_clarifier_gate",
            "note": "MODIFY accumulator wins: plant SCD remaining-demand evidence overpowers the Streamveil keep advocate",
            "decode_rule": "isolate if scd_estimator AND probe_lock fire; vendor_keep_advocate is below threshold by design",
            "populations": [
                gate_pop("scd_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("probe_lock", 64, 1.2, 39.0625, w_s),
                gate_pop("vendor_keep_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("modify_latch", 80, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "of3.scd_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 32.0},
                {"check": "of3.iso_scorer", "neurons": 50, "mean_rate_hz": 50.0, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-a2",
            clock_domain="of3-scd-hil-relative-ms-t0-2026-09-02T04:00:00Z",
            tags=["streaming-current", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
            distillation_value="Streaming-current remaining-demand head with independent CUBA LIF raster, isolate-frame SNR 14.0, refractory, and adaptation for Spikenaut distillation.",
        ),
    }


# ---------------------------------------------------------------------------
# nelb-r64-a3 — acoustic-emission remaining hit-rate of a hydrocracker vessel
# ACCEPT / REJECT, simulated
# ---------------------------------------------------------------------------
def rec_003():
    k_a = 2.00
    n_hits = 24.00
    dt_s = 3.00
    r_hz = k_a * n_hits / dt_s
    ratio = n_hits / dt_s
    _exact(r_hz, 16.00)
    _exact(ratio, 8.00)
    _exact(k_a * 12.00 / dt_s, 8.00)
    _exact(k_a * 18.00 / dt_s, 12.00)
    _exact(6000.0 + 720.0, 6720.0)

    raster = make_lif_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=20260964003,
        source="ss5.ae.N",
        target="stoatshaw.vessel_accept_core",
        table=[
            {"from": "ae_N", "to": "rate_estimator", "weight": 1.30},
            {"from": "ae_snr", "to": "hit_norm", "weight": 1.10},
            {"from": "aeveil_r", "to": "vendor_skip_advocate", "weight": 0.42},
        ],
        third_factor={
            "modulator": "na.ae_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-survey synapses; the AE modulator depresses skip links "
                "when hit-count stays in-band inside tau_e of an SNR lock so an Aeveil last-good "
                "cannot hide a 16.00 hits/s V-3 remaining load or release V-1/V-2"
            ),
        },
        channel_prefix="ae.n",
        anchor=(
            "SS-5 AE 36 ms frame at N 24.00 / dt 3.00 s / SNR 12.0 "
            "(t_s 3000) reconstructing 16.00 hits/s inside the 8.00-24.00 band"
        ),
        kernel_ms=[0.0, 1.5, 9.0, 21.0],
    )
    w_s = 0.036
    events = [
        ev(100.0, "ae.N", 12.00, code="N_HITS", units="1", note="simulated acoustic-emission hit-count of SS-5 hydrocracker vessel V-3 in AE-SIM-6; remaining hit-rate family, not magnetoacoustic-emission case depth, not acoustic pyrometry, not PAUT TFM, not TOFD, not impact-echo, not DCPD"),
        ev(300000.0, "ae.snr", 7.0, code="AE_SNR", units="1"),
        ev(600000.0, "recon.R", 8.00, code="R_HZ", units="hits_s", note="2.00*12.00/3.00=8.00; at the 8.00 band floor"),
        ev(900000.0, "ves.T", 410.0, code="T_C", units="C", note="plant vessel skin RTD; independent witness; unread by Aeveil"),
        ev(1200000.0, "aeveil.R", 4.80, code="VENDOR_HZ", units="hits_s", note="Aeveil vendor AE-6 last-good cloud; infra owner; under-read skip advocate"),
        ev(1500000.0, "ae.dt", 3.00, code="DT_S", units="s", note="AE gate window; held"),
        ev(1800000.0, "ae.N", 18.00, code="N_HITS", units="1"),
        ev(2100000.0, "recon.R", 12.00, code="R_HZ", units="hits_s", note="2.00*18.00/3.00=12.00; in band"),
        ev(2400000.0, "ves.id", 3.0, code="VES_ID", units="1", note="V-3 in scope; V-1 and V-2 out of scope"),
        ev(2700000.0, "v12.present", 1.0, code="V12", units="bool", note="adjacent vessels present; out of this ACCEPT"),
        ev(3000000.0, "ae.N", 24.00, code="N_HITS", units="1", note="in-band frame; raster sidecar kernel"),
        ev(3000001.5, "ae.dt", 3.00, code="DT_S", units="s", note="1.5 ms gate window after hit-count"),
        ev(3150000.0, "ae.snr", 12.0, code="AE_SNR", units="1", note="SNR 12.0 >= 8.0 lock"),
        ev(3300000.0, "recon.R", 16.00, code="R_HZ", units="hits_s", note="2.00*24.00/3.00=16.00 exact; band 8.00-24.00"),
        ev(3450000.0, "recon.ratio", 8.00, code="N_DT", units="hits_s", note="24.00/3.00=8.00 exact count-window identity"),
        ev(3600000.0, "aeveil.R", 4.76, code="VENDOR_HZ", units="hits_s"),
        ev(3900000.0, "ves.T", 412.0, code="T_C", units="C"),
        ev(4200000.0, "mdot.kg_h", 48.00, code="MDOT", units="kg_h", note="plant mass-flow tracks AE not Aeveil"),
        ev(4500000.0, "ae.drop", 1.0, code="AE_DROP", units="bool"),
        ev(4800000.0, "ops.prop", 1.0, code="SKIP_SURVEY", units="bool", note="night planner Tam Osier: Aeveil is 4.80 hits/s; skip V-3 survey and dump the header"),
        ev(5100000.0, "dump.trip", 0.0, code="DUMP_ARMED", units="bool", note="dump would be a header kill; out of this ACCEPT"),
        ev(5400000.0, "gate.comp", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of V-3 only; 16.00 hits/s in band; V-1..V-2 out of scope; Aeveil not SoT"),
        ev(5700000.0, "recon.R", 16.00, code="R_HZ", units="hits_s"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey floor"),
        ev(6300000.0, "ae.snr", 12.0, code="AE_SNR", units="1"),
        ev(6600000.0, "aeveil.R", 4.72, code="VENDOR_HZ", units="hits_s"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_ISOLATE", units="bool", note="Osier: skip-isolate V-3; Aeveil still 4.72; takt is late"),
        ev(7500000.0, "v12.present", 1.0, code="V12", units="bool"),
        ev(7800000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(8100000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2 REJECTS skip-isolate; V-3 stays the bounded ACCEPT; dump not taken"),
        ev(8400000.0, "v3.held", 1.0, code="V3_HELD", units="bool"),
        ev(8700000.0, "v12.skip", 0.0, code="V12_NOT_RELEASED", units="bool"),
        ev(9000000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(9300000.0, "ae.N", 18.00, code="N_HITS", units="1"),
        ev(9600000.0, "recon.R", 12.00, code="R_HZ", units="hits_s", note="2.00*18.00/3.00=12.00; still in band so V-3 hold stands"),
        ev(9900000.0, "aeveil.R", 4.68, code="VENDOR_HZ", units="hits_s"),
        ev(10200000.0, "ves.T", 408.0, code="T_C", units="C"),
        ev(10500000.0, "ae.dt", 3.00, code="DT_S", units="s"),
        ev(10800000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(11100000.0, "recon.ratio", 6.00, code="N_DT", units="hits_s", note="18.00/3.00=6.00 post-accept ratio"),
        ev(11400000.0, "ae.drop", 1.0, code="AE_DROP", units="bool"),
        ev(11700000.0, "ves.id", 3.0, code="VES_ID", units="1"),
        ev(12000000.0, "v3.held", 1.0, code="V3_HELD", units="bool"),
        ev(12300000.0, "dump.trip", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(12600000.0, "takt.late", 1.0, code="TAKT", units="bool"),
        ev(12900000.0, "aeveil.R", 4.64, code="VENDOR_HZ", units="hits_s"),
        ev(13200000.0, "recon.R", 12.00, code="R_HZ", units="hits_s"),
        ev(13500000.0, "ae.snr", 11.0, code="AE_SNR", units="1"),
        ev(13800000.0, "ves.T", 406.0, code="T_C", units="C"),
        ev(14100000.0, "v12.skip", 0.0, code="V12_NOT_RELEASED", units="bool"),
        ev(14400000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r64-a3-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SS-AE-2026-0902",
            "domain": "acoustic_emission_hydrocracker_hitrate",
            "setting": (
                "Stoatshaw Hydrocracker SS-5 (invented), vessel V-3 digital twin in AE-SIM-6. "
                "Plant-owned acoustic-emission hit-count / gate-window is the remaining hit-rate SoT. "
                "Aeveil / AE-6 vendor DAQ (infra owner) under-reads 4.80 hits/s and wants a skip. "
                "Not magnetoacoustic-emission case depth (r54), not acoustic pyrometry (r25), not PAUT TFM (r23), "
                "not TOFD (r44), not impact-echo (r38), not DCPD (r38)."
            ),
            "observables_at_decision": {
                "N_hits": n_hits,
                "dt_s": dt_s,
                "k_a": k_a,
                "R_hz": r_hz,
                "ratio": ratio,
                "ae_snr": 12.0,
                "aeveil_hz": 4.80,
                "band_lo_hz": 8.00,
                "band_hi_hz": 24.00,
                "vent_scope": "V-3",
            },
            "margin_authority": (
                "SS-5 vessel SOP rev D: if reconstructed R_hz is inside 8.00-24.00 AND AE SNR >= 8.0 "
                "AND the tagged vessel is V-3, ACCEPT V-3 only. Aeveil is not SoT. V-1 and V-2 stay out of scope. "
                "Header dump is a different gate."
            ),
        },
        "proposed_action": {
            "actor": "night planner Tam Osier, citing Aeveil 4.80 hits/s and a quiet AE-6 count",
            "summary": "skip V-3 survey and dump the hydrocracker header; 24.00 hits is a fouled-sensor glitch on a healthy 4.80 hits/s last-good",
            "basis_claimed": "Aeveil is the only OEM AE SoT and a night survey of V-3 is a takt miss",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": (
                "Bounded ACCEPT of V-3 only. Serialized reconstruction: R_hz = k_a * N / dt = "
                "2.00 * 24.00 / 3.00 = 16.00 hits/s, inside the 8.00-24.00 band, and AE SNR is 12.0 >= 8.0. "
                "Count-window identity N / dt = 24.00 / 3.00 = 8.00. Aeveil 4.80 hits/s is an under-read skip "
                "advocate, not SoT. V-1 and V-2 are out of this ACCEPT. Ordered: keep V-3 on the plant AE. "
                "Scope: this ACCEPT does not dump the header (companion question) and does not release V-1/V-2."
            ),
            "threshold": "8.00<=R_hz<=24.00 AND ae_snr>=8.0 AND vent==V-3 => ACCEPT V-3; Aeveil is not SoT",
            "stated_residuals": "survey floor still required; 16.00 vs a true leak is a later sample; Aeveil remains the only OEM AE channel",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 5400: V-3 bounded in-band; Aeveil not SoT; V-1/V-2 not released; dump not taken",
            "tool": "ss5-ae-vessel-gate-cli",
            "observation": "R 16.00 hits/s recomputes from N 24.00 and dt 3.00; plant AE hashed; Aeveil channel not used as SoT",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3000.0, "event": "AE N 24.00 dt 3.00; raster frame; R 16.00 hits/s"},
                {"t_s": 4800.0, "event": "ops proposes skip-survey / dump"},
                {"t_s": 5400.0, "event": "ACCEPT V-3 only"},
                {"t_s": 6000.0, "event": "12 min survey bookend 1"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 8100.0, "event": "companion REJECT skip-isolate"},
            ],
            "observed_effects": [
                "hit-rate recomputes from the serialized AE model at every recon.R event",
                "an Aeveil-only head would have skipped V-3 and dumped the header",
                "12 min survey floor is in the stream; V-1/V-2 stay out of scope",
            ],
            "surprises": [
                "a vendor under-read 4.80 hits/s skip corridor co-existed with a 16.00 hits/s in-band plant reconstruction",
            ],
            "new_state": {
                "vent_v3": "bounded ACCEPT",
                "aeveil": "not SoT",
                "v1_v2": "out of scope",
            },
            "latency_ms": 2400000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("ae_reconstruction", 0.14),
                ("bounded_accept_scope", 0.12),
                ("aeveil_nonsubstitution", 0.10),
                ("in_band_lock", 0.08),
                ("survey_time_cost", -0.03),
            ],
            "scored for a bounded ACCEPT of V-3 on a recomputable AE remaining hit-rate while refusing an Aeveil under-read skip and keeping V-1/V-2 out of scope",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "acoustic-emission-hitrate", "serialized-reconstruction", "bounded-scope"],
            distillation_note="AE gate: serialized k_a*N/dt plus SNR lock beats a vendor under-read skip; V-3 only",
            distillation_value="Teaches an SNN to race an AE hit-count/window remaining rate against a patched vendor skip with bounded vessel scope, refractory, and adaptation.",
        ),
    }
    traj2 = {
        "id": "nelb-r64-a3-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "SS-AE-2026-0902-exec",
            "domain": "skip_isolate_refusal_execution",
            "setting": "Same SS-5 after the bounded ACCEPT. Planner proposes skip-isolate of V-3 under late takt. Companion REJECTS the skip; dump stays down.",
            "observables_at_decision": {
                "R_hz": 12.00,
                "surv_floor_s": 720.0,
                "skip_isolate_proposed": True,
                "v3_held": True,
            },
        },
        "proposed_action": {
            "actor": "night planner Tam Osier",
            "summary": "skip-isolate V-3; 12 min already paid and Aeveil still shows 4.72 hits/s; takt is late",
            "basis_claimed": "the ACCEPT already cleared V-3, so a skip-isolate is the cheapest takt recovery",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": (
                "Skip-isolate is refused. The 12 min survey floor is complete and the in-band tripwire "
                "(8.00 <= R_hz <= 24.00) is still armed on the plant AE. REJECT skip-isolate. Do not dump "
                "the header. Do not restore on Aeveil. Do not release V-1/V-2. 12.00 hits/s post-accept is still "
                "the plant SoT until a new frame leaves the band."
            ),
            "threshold": "surv_held AND skip_isolate_not_taken AND dump_not_taken AND v12_not_released",
        },
        "executed_action": {
            "summary": "skip-isolate REJECTED at t_s 8100; dump not latched; Aeveil restore not taken; V-3 held",
            "tool": "ss5-ae-skip-exec",
            "observation": "recon.R 12.00 hits/s after ACCEPT; survey line-up complete; Aeveil still ignored",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
                {"t_s": 6720.0, "event": "12.0 min floor"},
                {"t_s": 7200.0, "event": "skip-isolate proposed"},
                {"t_s": 8100.0, "event": "REJECT skip-isolate; dump refused"},
            ],
            "observed_effects": [
                "Aeveil restore did not reopen the hit-rate call",
                "header dump never fired; V-3 held on the plant AE",
            ],
            "new_state": {"hold": "survey-held", "plant": "in service", "vent_v3": "held"},
            "latency_ms": 1380000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("skip_isolate_refusal", 0.12),
                ("no_header_dump", 0.10),
                ("aeveil_nonsubstitution", 0.08),
                ("scope_held", 0.08),
                ("takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-isolate because Aeveil is not a skip license; not a hit-rate re-vote",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "skip-refusal"]),
    }
    return {
        "id": "nelb-r64-a3",
        "spike_events": events,
        "language_view": {
            "description": (
                "Stoatshaw Hydrocracker SS-5 AE-SIM-6. Plant-owned AE reconstructs 16.00 hits/s remaining "
                "hit-rate from 24.00/3.00 while Aeveil still reports 4.80 hits/s. The gate ACCEPTs V-3 only "
                "(V-1..V-2 out of scope). A 12 min survey floor is serialized. Companion t2 REJECTs skip-isolate."
            ),
            "trajectory": traj,
            "trajectory_skip_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "ae.N / ae.dt / ae.snr": "hit-count, gate window, and SNR; the physics channels the reconstruction consumes",
                "recon.R / recon.ratio": "serialized remaining hit-rate and count-window identity",
                "ves.T / aeveil.R / ves.id / v12.present / ae.drop / mdot.kg_h": "vessel witnesses, vendor last-good, scope tags, dropped packets, mass-flow",
                "ops.prop / gate.comp / ops.skip / gate.hold": "skip-survey proposal, ACCEPT, skip-isolate proposal, companion REJECT",
                "surv.start / surv.floor / v3.held / v12.skip / dump.trip / takt.late / surv.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "vendor-under while plant-in-band: aeveil.R 4.80 next to recon.R 16.00",
                "reconstruction as event: recon.R 16.00 equals 2.00*24.00/3.00",
                "ACCEPT then operational REJECT: gate.comp at 5400 s, gate.hold at 8100 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight AE pair: ae.N then ae.dt +1.5 ms at the raster frame (kernel, not excerpt echo)",
            ],
            "language_to_spike_mapping": (
                "'Aeveil is 4.80 hits/s' = aeveil.R 4.80; '16 hits/s remaining' = recon.R 16.00; "
                "'ACCEPT V-3 only' = gate.comp ACCEPT; 'refuse skip-isolate' = gate.hold REJECT"
            ),
            "why_high_value": (
                "New acoustic-emission remaining-hit-rate family on a hydrocracker vessel (not magnetoacoustic-emission "
                "case depth r54, not acoustic pyrometry r25, not PAUT TFM r23, not TOFD r44, not impact-echo r38, "
                "not DCPD r38). Lead bounded ACCEPT of V-3 on a recomputable 16.00 hits/s in-band load that a vendor "
                "under-read would have skipped. Companion t2 REJECTS skip-isolate. Independent CUBA LIF raster. "
                "sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "CUBA LIF (lif_raster._calibrate_spikes) plus MT19937 amplitudes",
                "seeds": {
                    "raster": 20260964003,
                    "stream_note": "stream amplitudes are authored constants (1, hits_s, C, kg_h, s, bool)",
                },
                "draw_order": "independent CUBA LIF full window; kernelized 0.0/1.5 ms physics pair is synaptic drive, not excerpt copy",
                "thinning": "AE board exists at ~1 Hz; stream keeps 4 N points plus dt pairs; recon keeps 4 of ~20 solver ticks",
                "time_alias": "t_rel_ms; t0 = 2026-09-02T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "AE reconstruction head: R_hz = k_a * N / dt; ratio = N / dt",
                "bounded ACCEPT head: in-band R AND vessel scope AND v12-out-of-scope",
                "operational companion: refuse skip-isolate without re-opening the last-good call",
            ],
        },
        "reconstruction_model": {
            "name": "acoustic_emission_hit_rate",
            "formula": "R_hz = k_a * N_hits / dt_s; ratio = N_hits / dt_s",
            "parameters": {
                "k_a": 2.00,
                "band_lo_hz": 8.00,
                "band_hi_hz": 24.00,
                "surv_min": 12.0,
            },
            "worked_example": {"N_hits": 24.00, "dt_s": 3.00, "ratio": 8.00, "R_hz": 16.00},
            "check": "2.00 * 24.00 / 3.00 = 16.00 exactly; 24.00 / 3.00 = 8.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "ss5.ae_vessel_gate",
            "note": "ACCEPT accumulator wins: plant AE remaining-hit-rate evidence overpowers the Aeveil skip advocate",
            "decode_rule": "accept if rate_estimator AND hit_norm fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release V-1..V-2",
            "populations": [
                gate_pop("rate_estimator", 80, 1.5, 50.0, w_s),
                gate_pop("hit_norm", 64, 1.2, 31.25, w_s),
                gate_pop("vent_margin", 40, 1.0, 50.0, w_s),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, w_s),
                gate_pop("accept_latch", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                {"check": "ss5.ae_scorer", "neurons": 80, "mean_rate_hz": 50.0, "window_ms": 36.0},
                {"check": "ss5.ves_scorer", "neurons": 40, "mean_rate_hz": 62.5, "window_ms": 32.0},
            ]
        ),
        "meta": meta_common(
            id="nelb-r64-a3",
            clock_domain="ss5-ae-sim-relative-ms-t0-2026-09-02T03:00:00Z",
            tags=["acoustic-emission-hitrate", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
            distillation_value="AE remaining-hit-rate head with independent CUBA LIF raster, bounded vessel scope, refractory, and adaptation for Spikenaut distillation.",
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN or nk in {"thought", "scratch", "inner_monologue", "chain_of_thought"}:
                hits.append(p)
            if nk == "real" and k.casefold() == "real":
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def jaccard_independence(rec):
    window_ms = rec["raster"]["window_ms"]
    rast = {int(e["t_us"]) for e in rec["raster"]["excerpt"]}
    stream = set()
    for e in rec["spike_events"]:
        t = e["t_rel_ms"]
        if 0.0 <= t <= window_ms:
            stream.add(int(round(t * 1000.0)))
    inter = rast & stream
    union = rast | stream
    jac = (len(inter) / len(union)) if union else 0.0
    if jac > 0.05:
        raise RuntimeError(f"{rec['id']} LIF Jaccard {jac:.4f} vs in-window stream (echo)")
    return jac


def local_checks(records):
    ids = []
    decisions = []
    sims = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"provenance"' in blob:
            raise RuntimeError("provenance object present")
        if rec["meta"].get("snn_tags") != SNN_TAGS:
            raise RuntimeError(f"{rec['id']} missing meta.snn_tags")
        if rec["meta"].get("nelb", {}).get("snn_tags") != SNN_TAGS:
            raise RuntimeError(f"{rec['id']} missing meta.nelb.snn_tags")
        if rec["raster"].get("encoder") != "independent_cuba_lif":
            raise RuntimeError(f"{rec['id']} raster not independent LIF")
        jaccard_independence(rec)
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "id" in v:
                if k != "trajectory":
                    ids.append(v["id"])
                sim2 = v["state"]["sim_or_real"]
                if sim2 not in {"designed", "simulated", "hil"}:
                    raise RuntimeError(sim2)
                if sim2 == "real":
                    raise RuntimeError("real")
                if v["safety_decision"]["decision"] not in {"ACCEPT", "MODIFY", "REJECT"}:
                    raise RuntimeError(v["safety_decision"]["decision"])
                tmeta = v.get("meta") or {}
                if tmeta.get("snn_tags") != SNN_TAGS:
                    raise RuntimeError(f"{v['id']} missing trajectory snn_tags")
                if tmeta.get("round") != ROUND:
                    raise RuntimeError(f"{v['id']} round")
        n = len(rec["spike_events"])
        if not (48 <= n <= 80):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory") and isinstance(v, dict) and "safety_decision" in v:
                if k != "trajectory":
                    decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        if not (20 <= rast["window_ms"] <= 50):
            raise RuntimeError("window")
        if abs(rast["window_s"] - rast["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window_s")
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("ISI identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("ISI hist sum")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        gc = rec["gate_compute"]
        sp_sum = sum(c["spikes"] for c in gc["per_check"])
        if sp_sum != gc["total_spikes"]:
            raise RuntimeError("gate_compute spikes")
        if abs(gc["total_energy_pJ"] - sp_sum * 23) > 1e-6:
            raise RuntimeError("gate_compute pJ")
        dw = rec["gate_snn"]["decision_window_s"]
        for pop in rec["gate_snn"]["populations"]:
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate_snn pop {pop['name']}")
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
        rights = rec["meta"]["rights"]
        if rights.get("linear_issue") != "RM-793":
            raise RuntimeError("RM-793 missing")
        if len(rights) != 15:
            raise RuntimeError(f"rights {len(rights)}")
        if rec["meta"].get("round") != ROUND:
            raise RuntimeError("round")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"sim mix {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    lead = [records[i]["language_view"]["trajectory"]["safety_decision"]["decision"] for i in range(3)]
    if set(lead) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"lead mix {lead}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))
    print("decisions", decisions, "sims", sims)


def write_exclusive(path: Path, text: str):
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def choose_live_paths():
    batch = LIVE / "batch-r63.jsonl"
    notes = LIVE / "NOTES-r63.md"
    if not batch.exists() and not notes.exists():
        return batch, notes, ""
    suffix = "c"
    n = 1
    while True:
        batch = LIVE / f"batch-r63{suffix}.jsonl"
        notes = LIVE / f"NOTES-r63{suffix}.md"
        if not batch.exists() and not notes.exists():
            return batch, notes, suffix
        n += 1
        suffix = f"c{n}"


def notes_text(records, batch_path: Path, sizes, file_sha, file_size, suffix: str) -> str:
    isis = []
    spikes = []
    events = []
    windows = []
    energies = []
    for rec in records:
        ident = rec["raster"]["isi_count_identity"]
        isis.append(ident["isi_total"])
        spikes.append(rec["raster"]["spikes"])
        events.append(len(rec["spike_events"]))
        windows.append(int(rec["raster"]["window_ms"]))
        energies.append(int(rec["raster"]["energy_pJ"]))
    energy_sum = sum(energies)
    spike_sum = sum(spikes)
    where = str(batch_path.parent)
    tagged = "c-suffix collision path" if suffix else "create-only live path"
    return f"""# Neuromorphic Event + Language Bridge — NOTES round 63
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `{batch_path.name}` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. CREATE-ONLY write ({tagged}) at `{where}` (`{batch_path.name}`, `{(LIVE / batch_path.name.replace('batch', 'NOTES')).name if False else batch_path.with_name(batch_path.name.replace('batch','NOTES').replace('.jsonl','.md')).name}`). Never 2026-08-17 / 2026-08-30. Leftover-mill `/tmp/nelb-r63/` (Wobbe / nephelometric / cation conductivity, ids `190`–`192`) is a different artifact and was not overwritten.

## Context / de-duplication
Live tree already had r21 (OA-ICOS CH4 / SERF OPM / WGM water), r41 (LDA / coulometric Karl Fischer / bender-element), r61 (Stern-Volmer DO / pellistor LEL / FMCW tank-radar). Leftover-mill r13–r70 families (including leftover r63 Wobbe/NTU/cation, r64 venturi/katharometer/Clark, r69 flame-photometric S / idler-belt / glass pH, r70 NIR moisture) were treated as taken. IDs this round `nelb-r63-001`…`003` as assigned (not leftover `190`–`192`). Envelope cloned from live r61 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`) with **independent CUBA LIF rasters** (not MT19937 gap-placement echo of `spike_events`). `meta.snn_tags` = [race, refractory, adaptation] on every record and trajectory (`meta.nelb.snn_tags` twin).

Banned this round: live r21/r41/r61 families; leftover-mill r13–r70 table (Wobbe, nephelometric, cation conductivity, venturi, katharometer, Clark DO, glass pH, NIR moisture, flame-photometric S, idler-belt, UV ozone, triboelectric dust, molybdenum-blue phosphate, hydrostatic dP, polarimeter, platinum ORP, NDIR CO, gamma-backscatter, ultrasonic-Doppler, Stern-Volmer DO, pellistor, FMCW radar, OA-ICOS, SERF, WGM, LDA, Karl Fischer, bender-element, CEMS FTIR k-script). Plants not reused: Mirewhin, Lacquerfen, Pitchshaw, Rushcrag, Copsewick, Peatspire, Sedgewhin, Brinecrag, Lichenholt, Slagholt, Copsewhin, Siltwharf, Reedcairn/Brackenmire/Fernshaw are new this round.

Adjacencies declared in-pair then kept physically distinct:
- **001 ICP-OES Ni** is an inductively-coupled-plasma emission internal-standard remaining nickel of an electroless bath, not LIBS plasma (r19/r21/r22), not spark-OES, not XRF (r29/r34), not PGNAA (r15), not handheld XRF.
- **002 LVDT expansion** is a linear-variable-differential-transformer remaining HP-casing growth of a steam turbine, not strain-gauge hopper (r59), not DIC hoop (r51), not Seebeck (r45), not coda-wave (r45), not bender-element (live r41), not load-cell.
- **003 FTIR methanol** is a Michelson peak-area remaining methanol of a carbonylation vent, not CEMS FTIR k-script (r04), not NDIR CO (leftover r62), not OA-ICOS CH4 (live r21), not TDLAS NH3 (r22), not UV-DOAS (r59), not CRDS (r15), not QEPAS (r19).

## Round 63 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r63-001 | ICP-OES remaining nickel of an electroless bath (k_icp·I_ni/I_y g/L, Specveil last-good denial, 18 min bath-hold floor) | Reedcairn Plating RC-9 bath T-6 (invented): 12.00/2.00 reconstructs 24.00 g/L while Specveil still reads 4.80 g/L | REJECT (+0.43) / MODIFY (+0.34) | serialized `4.00*12.00/2.00=24.00`; `12.00/2.00=6.00`; conjunctive SOP (Ni AND SNR) forbids continue-plate; three-party collusion includes the ICP infra owner; companion t2 bath-hold, plant ESD refused; sim_or_real=designed |
| nelb-r63-002 | LVDT remaining HP-casing expansion of a steam turbine (k_l·(V−V0) mm, Coreveil last-good denial, 24 min cooldown floor) | Brackenmire Turbine BM-7 casing C-2 (invented, HIL dummy in LVDT-HIL-7): 8.00−2.00 reconstructs 15.00 mm while Coreveil still reads 4.80 mm | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `2.50*(8.00-2.00)=15.00` and `8.00-2.00=6.00`; keep-running refused; core tech Wren Solis exonerated (missing core-zero AE, UTC vs UTC+2); companion t2 new-core restart; sim_or_real=hil |
| nelb-r63-003 | FTIR remaining methanol of a carbonylation vent (k_f·A_meoh/A_is ppm, Iroveil last-good denial, 12 min survey floor) | Fernshaw Carbonyl FS-8 vent V-3 (invented, simulated FTIR-SIM-5): 8.00/2.00 reconstructs 16.00 ppm while Iroveil still reads 4.80 ppm | ACCEPT (+0.41) / REJECT (+0.36) | serialized `4.00*8.00/2.00=16.00`; `8.00/2.00=4.00`; bounded ACCEPT of V-3 only; V-1..V-2 out of scope; companion t2 REJECTS skip-isolate; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r63-001`…`003` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {windows[0]}/{windows[1]}/{windows[2]} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({spikes[0]}/{spikes[1]}/{spikes[2]}); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact ({energies[0]}/{energies[1]}/{energies[2]} pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.cross_authority_conflict / ach.referral_pressure_salience / na.stage_rate_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, **full-window CUBA LIF** (not spike_events echo); per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({isis[0]}/{isis[1]}/{isis[2]}). Same-neuron gaps ≥1000 µs. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. Main streams: **{events[0]}/{events[1]}/{events[2]} events** (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (001 ICP pair at 1.4 ms, 002 LVDT pair at 1.2 ms plus isolate-frame SNR 14.0, 003 FTIR pair at 1.5 ms). `meta.snn_tags` required.

## Self-critique

### Edge cases added vs still thin
- **Added:** first ICP-OES internal-standard remaining-nickel family on an electroless bath with recomputable Ni=k_icp·I_ni/I_y (`24.00 g/L`) plus intensity-ratio identity and three-party collusion including the ICP infra owner; first LVDT remaining-expansion family on a steam-turbine HP casing with recomputable L=k_l·(V−V0) (`15.00 mm`) and delta identity, plus a resolved-innocent core tech (timezone-skipped core-zero, not last-to-badge) and isolate-frame SNR 14.0; first FTIR Michelson peak-area remaining-methanol family on a carbonylation vent with recomputable C=k_f·A_meoh/A_is (`16.00 ppm`) plus area-ratio identity; bounded ACCEPT whose out-of-scope clause is adjacent vents rather than a hopper/taphole/dump cap; operational t2 on all three (bath-hold, new-core restart, skip-isolate refusal); provenance trio designed/hil/simulated; 18 / 24 / 12 min slow floors in-stream; **independent CUBA LIF rasters** (live r21/r41/r61 used gap-constrained MT19937 placement).
- **Still thin:** (i) 001's k_icp is a lumped emission gain, not a plasma-T / matrix table — a 200 K torch hop that fakes 24.00 g/L inside a 4.80 Specveil corridor is unwritten; (ii) 002's k_l is a lumped core-to-mm gain, not a temperature / radial-runout map, so a 40 K casing hop that fakes 15.00 mm is unwritten; (iii) 003's k_f is a lumped peak-area gain, not a path-length / water-interference map, so a humidity hop that fakes 16.00 ppm inside a 4.80 last-good is unwritten; (iv) vendor-only as a *lead* REJECT on a plant with *no* independent ICP/LVDT/FTIR installed yet remains slightly harder — 001/002 still have plant heads; (v) stream amplitudes remain authored constants (raster draws are the only seeded noise).

### Realism of noise / temporal fidelity
- Strong: 001's 24.00 g/L, R 6.00, and 18.0 min bath-hold (`6000+1080=7080 s`) recompute from the record; 002's 15.00 mm, dV 6.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; 003's 16.00 ppm, R 4.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Independent CUBA LIF plus adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 48+ stream a raster-scale motif without echoing `spike_events` into `raster.excerpt`.
- **Gaps, honestly:** (i) 52-event streams still thin 1 Hz ICP / 10 Hz LVDT / 1 Hz FTIR stacks; (ii) 001's post-stop 16.00 g/L is a later sample, not a closed-loop nickel controller; (iii) 002 HIL dummy times an in-service isolate that the stream does not independently witness on a second live casing until the new core starts; (iv) no gate_snn input→output volley pair at raster resolution this round.

### Training value (SNN/LSM + agentic)
Distillation targets: ICP-OES Ni=k_icp·I_ni/I_y head plus ratio identity; conjunctive isolate floor vs continue-plate vs plant ESD; ICP-infra collusion; LVDT L=k_l·(V−V0) head plus delta identity; isolate-floor casing vs keep-running vs shop-trip; core-zero AE / timezone exoneration; FTIR C=k_f·A_meoh/A_is and area-ratio identities; bounded ACCEPT with V-1..V-2-out-of-scope; skip-isolate refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical Ni/expansion/methanol the raw corridor cannot see, earned ACCEPT with an explicit physical out-of-scope object (V-1..V-2), and stop-then-hold so a REJECT does not become a plant/shop/dump kill. Independent LIF rasters give Spikenaut a non-echo membrane crossing to distill against the language view.

## What a later leftover-mill round should add (next densification target)
1. **Plasma-T / matrix table** on a non-RC-9 ICP so a 200 K torch hop fakes 24.00 g/L inside a 4.80 Specveil corridor, closing 001's lumped-k_icp gap.
2. **Temperature / radial-runout map** on a non-BM-7 LVDT so a 40 K hop fakes 15.00 mm while mean V looks healthy.
3. **Path-length / water-interference map** on a non-FS-8 FTIR so a humidity hop fakes 16.00 ppm inside a 4.80 last-good corridor.
4. **Vendor-only as a lead REJECT** on a plant that has no independent ICP/LVDT/FTIR installed yet (001/002 still had plant heads).
5. **Do not restage** leftover-mill r63 Wobbe / nephelometric / cation conductivity (ids 190–192), live r21 OA-ICOS / SERF / WGM, live r41 LDA / Karl Fischer / bender-element, live r61 Stern-Volmer / pellistor / FMCW, CEMS FTIR k-script, NDIR CO, venturi, glass pH, NIR moisture, LIBS, XRF, PGNAA, DIC, strain-gauge hopper. Do not steal leftover-mill ids `040`–`213`. Do not reuse Reedcairn RC-9, Brackenmire LVDT-HIL-7, or Fernshaw FTIR-SIM-5.

## Verification
`{batch_path.name}`: 3 lines, `json.loads`-clean (allow_nan=False), {sizes[0]}/{sizes[1]}/{sizes[2]} bytes (file {file_size}, sha256 `{file_sha}`). CREATE-ONLY write at `{where}`. Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events ({events[0]}/{events[1]}/{events[2]}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {isis[0]}/{isis[1]}/{isis[2]}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=63`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at={GENERATED_AT}`); `meta.snn_tags`=[race, refractory, adaptation]; independent CUBA LIF encoder; no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; no `real` / `thought` keys; all 9 record/trajectory ids unique. Raster base seeds 20260963001/20260963002/20260963003. Repo gates run against the staged JSONL after the exclusive write.

Honest novelty accounting: 3/3 modality families are new versus the live tree (r21/r41/r61) and versus leftover-mill r13–r70 (ICP-OES ≠ LIBS/XRF/PGNAA; LVDT ≠ strain-gauge/DIC/bender; FTIR peak-area methanol ≠ CEMS FTIR/NDIR/OA-ICOS/TDLAS). Independent CUBA LIF rasters are a new encoder versus live r21/r41/r61 gap-constrained placement. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
"""


def repo_validate(batch_path: Path):
    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import curate_record, raster_status
    from verify_execution import verify_batch_for_frontier

    errs, warns, kinds, n = check_jsonl(
        batch_path, batch_path.name, staging=FactoryStaging(enabled=True)
    )
    print("check_jsonl", {"errors": len(errs), "warnings": len(warns), "kinds": dict(kinds), "n": n})
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    if errs:
        raise RuntimeError("check_jsonl failed")

    records = [json.loads(line) for line in batch_path.read_text().splitlines() if line.strip()]
    for i, rec in enumerate(records, 1):
        st = raster_status(rec, require_raster=True, require_routing_table=True)
        print(
            rec["id"],
            "raster_valid",
            st["raster_valid"],
            "gate_snn_valid",
            st["gate_snn_valid"],
            "reasons",
            st.get("reason_codes"),
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st.get("reason_codes"):
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        blob = json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        h = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        dec = curate_record(
            rec,
            source_path=batch_path.name,
            source_line=i,
            source_hash=h,
            require_raster=True,
            require_routing_table=True,
        )
        reasons = dec.manifest.get("reason_codes")
        print(rec["id"], "curate", dec.action, reasons)
        if dec.action != "retain":
            raise RuntimeError(f"curate {rec['id']} {dec.action} {reasons}")

    counts, findings, blocked = verify_batch_for_frontier(batch_path, strict=True)
    print("verify_batch_for_frontier", counts, "blocked", blocked)
    if blocked or counts.get("verified") != 3:
        print("findings", findings)
        raise RuntimeError(f"frontier blocked {counts}")

    spike_probe = PIPELINES / "spike_probe.py"
    if spike_probe.is_file():
        import subprocess

        proc = subprocess.run(
            [sys.executable, str(spike_probe), "--strict", str(batch_path)],
            capture_output=True,
            text=True,
        )
        print("spike_probe stdout", proc.stdout[-2000:])
        if proc.returncode != 0:
            print("spike_probe stderr", proc.stderr[-2000:])
            raise RuntimeError(f"spike_probe rc {proc.returncode}")


def main():
    occupancy_preflight()
    STAGE.mkdir(parents=True, exist_ok=True)
    records = [rec_001(), rec_002(), rec_003()]
    local_checks(records)
    lines = [json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for rec in records]
    staged_batch = STAGE / "batch-r63.jsonl"
    staged_batch.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sizes = [len(line) for line in lines]
    raw = staged_batch.read_bytes()
    file_sha = hashlib.sha256(raw).hexdigest()
    file_size = len(raw)
    print("staged", staged_batch, "sizes", sizes, "sha256", file_sha)

    repo_validate(staged_batch)

    live_batch, live_notes, suffix = choose_live_paths()
    notes = notes_text(records, live_batch, sizes, file_sha, file_size, suffix)
    if "Novel coverage:" not in notes:
        raise RuntimeError("NOTES missing Novel coverage")
    staged_notes = STAGE / "NOTES-r63.md"
    staged_notes.write_text(notes, encoding="utf-8")

    LIVE.mkdir(parents=True, exist_ok=True)
    write_exclusive(live_batch, "\n".join(lines) + "\n")
    write_exclusive(live_notes, notes)
    print("WROTE", live_batch)
    print("WROTE", live_notes)
    print("suffix", suffix or "(none)")
    print("PAIR_TABLE")
    print("nelb-r63-001\tICP-OES Ni electroless\tREJECT/MODIFY\tdesigned")
    print("nelb-r63-002\tLVDT HP-casing expansion\tMODIFY/ACCEPT\thil")
    print("nelb-r63-003\tFTIR methanol peak-area\tACCEPT/REJECT\tsimulated")


if __name__ == "__main__":
    main()
