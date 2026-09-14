#!/usr/bin/env python3
"""NELB round-21 pairs for 2026-09-02-final-heavy (sf-window). Create-only."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

FACTORY = Path(
    "/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge"
)
PIPELINES = Path("/tmp/sf-window/pipelines")
sys.path.insert(0, str(PIPELINES))

GENERATED_AT = "2026-09-02T18:40:00Z"
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
        "round": 21,
        "factory": "neuromorphic-event-language-bridge",
        "generator": "grok-4.6",
        "run_label": "2026-09-02-final-heavy",
        "rights": dict(RIGHTS),
    }
    m.update(extra)
    return m


def make_raster(
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
):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    window_us = int(round(window_ms * 1000))
    rng = random.Random(seed)
    n_active = min(neurons, spikes)
    extra = spikes - n_active
    counts = [1] * n_active + [0] * (neurons - n_active)
    for i in range(extra):
        counts[i % n_active] += 1

    excerpt = []
    for nid, c in enumerate(counts):
        if c == 0:
            continue
        first_max = window_us - 1100 * (c - 1) - 250
        t = rng.randint(120, max(120, first_max))
        times = [t]
        for k in range(1, c):
            min_t = times[-1] + 1100
            slack = window_us - 1100 * (c - 1 - k) - 80
            hi = min(slack, times[-1] + rng.choice([1300, 1800, 2400, 3700, 5200, 7400]))
            if hi < min_t:
                hi = min_t
            if min_t > window_us:
                raise RuntimeError(f"placement overflow neuron {nid}")
            t2 = rng.randint(min_t, hi) if hi > min_t else min_t
            t2 = min(t2, window_us)
            times.append(t2)
        base = 1.15 + 0.7 * rng.random()
        for i, tu in enumerate(times):
            noise = 0.96 + 0.08 * rng.random()
            amp = round(base * (0.82**i) * noise, 3)
            excerpt.append(
                {
                    "t_us": int(tu),
                    "neuron_id": nid,
                    "amplitude": amp,
                    "channel": f"{channel_prefix}{nid:02d}",
                }
            )
    excerpt.sort(key=lambda e: (e["t_us"], e["neuron_id"]))

    by_n = defaultdict(list)
    for e in excerpt:
        by_n[e["neuron_id"]].append(e["t_us"])
    isis_ms = []
    for nid, ts in by_n.items():
        ts = sorted(ts)
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
    identity_n = spikes - len(by_n)
    if sum(x["count"] for x in hist) != identity_n:
        raise RuntimeError(f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}")
    if len(excerpt) != spikes:
        raise RuntimeError("excerpt/spikes mismatch")

    energy_pJ = spikes * 23
    energy_uJ = spikes * 23e-6
    return {
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
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
            "spikes": spikes,
            "distinct_active_neurons": len(by_n),
            "isi_total": identity_n,
        },
        "anchor": anchor,
        "seed_note": (
            f"MT19937 seed {seed}; per-neuron id order; gap-constrained times; "
            "amplitude adaptation 0.82**k plus noise"
        ),
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
        if not e["channel"] or not str(e["channel"]).strip():
            raise RuntimeError("empty channel")
        if t < last:
            raise RuntimeError("decreasing t_rel_ms")
        last = t
        prev = last_ch.get(e["channel"])
        if prev is not None and (t - prev) < 0.8:
            raise RuntimeError(f"refractory {e['channel']} {t - prev}")
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


def gate_pop(name, neurons, threshold, mean_rate_hz, window_s):
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "name": name,
        "neurons": neurons,
        "threshold": threshold,
        "mean_rate_hz": float(mean_rate_hz),
        "spikes": spikes,
    }


def gc_check(name, neurons, mean_rate_hz, window_ms):
    window_s = window_ms / 1000.0
    spikes = int(round(neurons * mean_rate_hz * window_s))
    return {
        "check": name,
        "neurons": neurons,
        "mean_rate_hz": float(mean_rate_hz),
        "window_ms": float(window_ms),
        "window_s": float(window_s),
        "spikes": spikes,
    }


def gate_compute(checks):
    total = sum(c["spikes"] for c in checks)
    return {
        "per_check": checks,
        "total_spikes": total,
        "total_energy_pJ": total * 23,
        "total_energy_uJ": total * 23e-6,
        "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
    }


def walk_hidden(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{path}.{k}" if path else k
            if k in HIDDEN:
                found.append(child)
            found.extend(walk_hidden(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(walk_hidden(v, f"{path}[{i}]"))
    return found


def traj_shell(
    *,
    tid,
    sim,
    episode_id,
    domain,
    setting,
    observables,
    margin,
    actor,
    prop_summary,
    basis,
    decision,
    rationale,
    threshold,
    residuals,
    exec_summary,
    tool,
    observation,
    timeline,
    effects,
    surprises,
    new_state,
    latency_ms,
    rc,
    tags,
    distillation_note,
):
    return {
        "id": tid,
        "state": {
            "sim_or_real": sim,
            "episode_id": episode_id,
            "domain": domain,
            "setting": setting,
            "observables_at_decision": observables,
            "margin_authority": margin,
        },
        "proposed_action": {
            "actor": actor,
            "summary": prop_summary,
            "basis_claimed": basis,
        },
        "safety_decision": {
            "decision": decision,
            "rationale": rationale,
            "threshold": threshold,
            "stated_residuals": residuals,
        },
        "executed_action": {
            "summary": exec_summary,
            "tool": tool,
            "observation": observation,
        },
        "future_outcome": {
            "timeline": timeline,
            "observed_effects": effects,
            "surprises": surprises,
            "new_state": new_state,
            "latency_ms": latency_ms,
        },
        "reward_components": rc,
        "meta": meta_common(tags=tags, distillation_note=distillation_note),
    }


# ---------------------------------------------------------------------------
# a1 — OA-ICOS remaining CH4, designed, REJECT + MODIFY
# ---------------------------------------------------------------------------
def rec_a1():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=40.0,
        seed=202609021,
        source="sw5.oai.icos",
        target="sedgewhin.header_stop_core",
        table=[
            {"from": "icos_I", "to": "ch4_estimator", "weight": 1.4},
            {"from": "icos_snr", "to": "icos_lock_core", "weight": 1.15},
            {"from": "icosveil_c", "to": "vendor_continue_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.oai_ch4_conflict",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": (
                "pre-post coincidence on continue-flare synapses; the plant OA-ICOS "
                "modulator depresses continue-flare links when transmitted intensity "
                "stays low inside tau_e of an SNR lock so an Icosveil last-good cannot "
                "hide an 11.00 ppm CH4 slip after the T/P table is applied"
            ),
        },
        channel_prefix="icos.n",
        anchor="SW-5 OA-ICOS 40 ms frame at I 4.00 / SNR 12.0 (t_s 2880) reconstructing 11.00 ppm CH4 over the 6.00 ppm isolate floor",
    )
    events = [
        ev(0.0, "icos.I", 16.0, code="I_AU", units="1", note="plant-owned OA-ICOS transmitted intensity on SW-5 landfill-gas header H-7; remaining-CH4 family, not CRDS HF, not TDLAS NH3, not QEPAS, not FID THC, not UV-DOAS SO2, not NDIR CO, not Wobbe"),
        ev(180000.0, "icos.snr", 6.0, code="ICOS_SNR", units="1", note="early SNR under the 8.0 lock floor"),
        ev(360000.0, "recon.C", 0.0, code="C_PPM", units="ppm", note="5.00*log2(16.00/16.00)*(300.00/300.00)*(100.00/100.00)=0.00 exact"),
        ev(540000.0, "path.T", 300.0, code="PATH_K", units="K", note="T0 row of the T/P table; serial-only path RTD unread by Icosveil"),
        ev(720000.0, "path.P", 100.0, code="PATH_KPA", units="kPa", note="P0 row of the T/P table"),
        ev(900000.0, "icosveil.C", 1.8, code="VENDOR_PPM", units="ppm", note="Icosveil vendor OA-ICOS cloud; infra owner; patched intensity timestamps"),
        ev(1080000.0, "rotam.Q", 2.0, code="Q_M3H", units="m3_h", note="mechanical rotameter on copper DCS; independent mass-flow witness"),
        ev(1260000.0, "icos.I", 8.0, code="I_AU", units="1"),
        ev(1440000.0, "recon.C", 5.0, code="C_PPM", units="ppm", note="5.00*log2(16.00/8.00)*(300.00/300.00)=5.00; still under the 6.00 isolate floor"),
        ev(1620000.0, "path.T", 300.0, code="PATH_K", units="K"),
        ev(1800000.0, "icos.snr", 8.0, code="ICOS_SNR", units="1"),
        ev(1980000.0, "icosveil.C", 1.8, code="VENDOR_PPM", units="ppm"),
        ev(2160000.0, "path.T", 315.0, code="PATH_K", units="K", note="T/T0=315/300=1.050; T-hop row of the table"),
        ev(2340000.0, "recon.C", 5.25, code="C_PPM", units="ppm", note="5.00*1.00*1.050=5.25; still under 6.00; lumped-k without T would still read 5.00"),
        ev(2520000.0, "path.P", 100.0, code="PATH_KPA", units="kPa"),
        ev(2700000.0, "rotam.Q", 2.0, code="Q_M3H", units="m3_h"),
        ev(2880000.0, "icos.I", 4.0, code="I_AU", units="1", note="isolate-floor frame; raster sidecar"),
        ev(2880001.4, "icos.snr", 12.0, code="ICOS_SNR", units="1", note="1.4 ms SNR lock after I; 12.0 >= 8.0"),
        ev(3060000.0, "recon.C", 11.0, code="C_PPM", units="ppm", note="5.00*log2(16.00/4.00)*(330.00/300.00)=11.00 exact; isolate 6.00, unit-kill 24.00"),
        ev(3240000.0, "recon.od", 2.0, code="OD", units="1", note="log2(16.00/4.00)=2.00 exact optical-depth identity"),
        ev(3420000.0, "recon.mdot", 22.0, code="MDOT_GH", units="g_h", note="2.00*11.00=22.00 exact carbon-mass identity"),
        ev(3600000.0, "path.T", 330.0, code="PATH_K", units="K", note="T/T0=330/300=1.100; isolate-row of the T/P table"),
        ev(3780000.0, "path.P", 100.0, code="PATH_KPA", units="kPa", note="P0/P=1.000; no pressure hop"),
        ev(3960000.0, "icosveil.drop", 1.0, code="ICOS_DROP", units="bool", note="vendor intensity packets dropped in Icosveil cloud for 40 s"),
        ev(4140000.0, "permit.slide", 40.0, code="PERM_S", units="s", note="permit clerk slid landfill-gas clock 40.00 s; collusion party"),
        ev(4320000.0, "icosveil.C", 1.8, code="VENDOR_PPM", units="ppm"),
        ev(4500000.0, "collude.clerk", 1.0, code="CLERK_PRESENT", units="bool", note="permit clerk Odel Varn is the third collusion party"),
        ev(4680000.0, "ops.prop", 1.0, code="CONTINUE_FLARE", units="bool", note="night operator Calder Wynn: Icosveil is clean 1.80 ppm; continue H-7 flare"),
        ev(4860000.0, "gate.stop", 1.0, code="REJECT", units="decision", note="refuse continue-flare; 11.00 ppm and SNR 12.0; Icosveil not SoT"),
        ev(5040000.0, "flare.held", 1.0, code="FLARE_HELD", units="bool"),
        ev(6000000.0, "filter.start", 1.0, code="FILTER_START", units="bool", note="bookend 1 of the 18.0 min carbon-filter floor"),
        ev(7080000.0, "filter.floor", 1.0, code="FILTER_FLOOR", units="bool", note="6000 s + 1080 s = 7080 s = 18.0 min"),
        ev(7260000.0, "ops.kill", 1.0, code="UNIT_ESD", units="bool", note="Wynn: ESD the whole Sedgewhin landfill-gas train until day-shift"),
        ev(7440000.0, "gate.hold", 1.0, code="MODIFY", units="decision", note="companion t2: carbon-filter hold on plant OA-ICOS as live interlock; unit ESD refused"),
        ev(7620000.0, "filterlock.set", 1.0, code="FILTER_HELD", units="bool"),
        ev(7800000.0, "icos.I", 2.0, code="I_AU", units="1"),
        ev(7980000.0, "recon.C", 16.5, code="C_PPM", units="ppm", note="5.00*log2(16.00/2.00)*(330.00/300.00)=16.50; still over 6.00 so filter holds"),
        ev(8160000.0, "icosveil.C", 1.7, code="VENDOR_PPM", units="ppm"),
        ev(8340000.0, "path.T", 330.0, code="PATH_K", units="K"),
        ev(8520000.0, "filter.held", 1.0, code="FILTER_HELD", units="bool"),
        ev(8700000.0, "unit.esd", 0.0, code="ESD_NOT_TAKEN", units="bool"),
        ev(8880000.0, "permit.slide", 40.0, code="PERM_S", units="s"),
        ev(9060000.0, "icosveil.drop", 1.0, code="ICOS_DROP", units="bool"),
        ev(9240000.0, "recon.od", 3.0, code="OD", units="1", note="log2(16.00/2.00)=3.00 on the post-stop frame"),
        ev(9420000.0, "recon.mdot", 33.0, code="MDOT_GH", units="g_h", note="2.00*16.50=33.00 identity holds post-stop"),
        ev(9600000.0, "rotam.Q", 2.0, code="Q_M3H", units="m3_h"),
        ev(9780000.0, "path.P", 100.0, code="PATH_KPA", units="kPa"),
        ev(9960000.0, "filterlock.held", 1.0, code="FILTER_HELD", units="bool"),
        ev(10140000.0, "icos.snr", 13.0, code="ICOS_SNR", units="1"),
        ev(10320000.0, "recon.C", 16.5, code="C_PPM", units="ppm"),
        ev(10500000.0, "flare.held", 1.0, code="FLARE_HELD", units="bool"),
        ev(10680000.0, "recon.Tratio", 1.1, code="T_RATIO", units="1", note="330.00/300.00=1.100 exact; the T/P table is load-bearing"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a1 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r21-a1-t1",
        sim="designed",
        episode_id="SW-OAI-2026-0902",
        domain="oai_icos_landfill_ch4",
        setting=(
            "Sedgewhin Landfill SW-5 (invented), Brineholt Recovery, header H-7. "
            "Plant-owned off-axis ICOS transmitted intensity plus a serialized T/P table "
            "is the CH4-slip SoT. Icosveil vendor OA-ICOS-cloud (infra owner) plus the "
            "landfill-gas permit clock are collusion parties, not witnesses. Invented plant; "
            "designed campaign. Not CRDS HF (r15), not TDLAS NH3 (r22), not QEPAS (r19), "
            "not FID THC (r55), not UV-DOAS SO2 (r59), not NDIR reformer CO (r62), not Wobbe (r63), "
            "not leftover-mill r21 THz-TDS bondline."
        ),
        observables={
            "I": 4.0,
            "I0": 16.0,
            "k_i": 5.0,
            "C_ppm": 11.0,
            "OD": 2.0,
            "T_K": 330.0,
            "T0_K": 300.0,
            "P_kPa": 100.0,
            "P0_kPa": 100.0,
            "T_ratio": 1.1,
            "mdot_gh": 22.0,
            "Q_m3h": 2.0,
            "icos_snr": 12.0,
            "icosveil_ppm": 1.8,
            "permit_slide_s": 40.0,
            "isolate_floor_ppm": 6.0,
        },
        margin=(
            "SW-5 landfill-gas SOP rev C: if reconstructed C_ppm >= 6.00 AND OA-ICOS SNR >= 8.0, "
            "continue-flare is forbidden even if Icosveil reports 1.80 ppm. Unit ESD is a different "
            "gate. Kill tripwire is 24.00 ppm. The T/P table is required: a lumped k_i that ignores "
            "T/T0 would under-read 11.00 as 10.00 and still trip, but the SoT is the tabled value."
        ),
        actor="night landfill-gas operator Calder Wynn, citing Icosveil 1.80 ppm and a quiet intensity channel",
        prop_summary="continue H-7 flare; 4.00 intensity is lamp noise on a healthy CH4 slip",
        basis="Icosveil is the only OEM OA-ICOS SoT and a night abort of H-7 is a nomination miss",
        decision="REJECT",
        rationale=(
            "Continue-flare is refused. Serialized reconstruction uses the T/P table: "
            "C_ppm = k_i * log2(I0/I) * (T/T0) * (P0/P) = 5.00 * log2(16.00/4.00) * (330.00/300.00) * (100.00/100.00) "
            "= 5.00 * 2.00 * 1.100 * 1.000 = 11.00, which is 5.00 ppm over the 6.00 isolate floor and 13.00 ppm "
            "under the 24.00 unit-kill tripwire, and OA-ICOS SNR is 12.0 >= 8.0. Optical-depth identity "
            "OD = log2(16.00/4.00) = 2.00. Carbon-mass identity mdot = Q * C = 2.00 * 11.00 = 22.00 g/h. "
            "A lumped k_i that drops T/T0 would report 10.00 ppm; the tabled 11.00 is the SoT. Permit clock "
            "was slid 40.00 s and vendor intensity packets were dropped, so Icosveil is a collusion party "
            "(OA-ICOS vendor plus operator plus permit clerk Odel Varn). Ordered: refuse continue-flare now. "
            "Scope: this REJECT does not ESD the landfill-gas train (that is the companion question) and does "
            "not isolate the path RTD."
        ),
        threshold="C_ppm>=6.00 AND icos_snr>=8.0 => refuse continue-flare; Icosveil is not SoT; unit-kill if C_ppm>=24.00",
        residuals="carbon-filter recycle still required to hold the 11.00 ppm; 11.00 vs a true 24.00 kill is a production cut; Icosveil remains the only OEM OA-ICOS channel",
        exec_summary="REJECT at t_s 4860: continue-flare refused; Icosveil not SoT; T/P-table reconstruction locked",
        tool="sw5-oai-header-gate-cli",
        observation="C 11.00 ppm recomputes from I 4.00 and T 330.00; plant OA-ICOS hashed; Icosveil channel not used as SoT",
        timeline=[
            {"t_s": 2880.0, "event": "icos I 4.00; raster frame; C 11.00 ppm with T/T0 1.100"},
            {"t_s": 4680.0, "event": "ops proposes continue-flare"},
            {"t_s": 4860.0, "event": "REJECT continue-flare"},
            {"t_s": 6000.0, "event": "18 min carbon-filter bookend 1"},
            {"t_s": 7080.0, "event": "18.0 min floor"},
            {"t_s": 7440.0, "event": "companion MODIFY carbon-filter hold vs unit ESD"},
        ],
        effects=[
            "CH4 slip recomputes from the serialized OA-ICOS T/P table at every recon.C event",
            "an Icosveil-only head would have continued the flare overnight",
            "18 min carbon-filter floor is in the stream (filter.start, filter.floor)",
        ],
        surprises=["a clean vendor 1.80 ppm corridor and a 40 s permit slide co-existed with an 11.00 ppm plant reconstruction that a lumped-k (no T) head would have under-read as 10.00"],
        new_state={"h7": "continue-flare blocked", "icosveil": "not SoT", "reconstruction_model": "discharged as an on-record T/P calculator"},
        latency_ms=1980000.0,
        rc=reward(
            0.43,
            [
                ("oai_reconstruction", 0.14),
                ("conjunctive_isolate_floor", 0.12),
                ("icosveil_nonsubstitution", 0.10),
                ("three_party_collusion", 0.10),
                ("filter_time_cost", -0.03),
            ],
            "scored for a continue-flare REJECT on a recomputable OA-ICOS CH4 slip with a load-bearing T/P table while refusing an Icosveil last-good patch and a permit clock slide; 18 min floor is priced as downtime not as a reason to wait",
        ),
        tags=["REJECT", "oai-icos-ch4", "serialized-reconstruction", "tp-table", "operational-companion"],
        distillation_note="OA-ICOS gate: serialized k_i*log2(I0/I)*(T/T0)*(P0/P) plus SNR lock beats a vendor last-good patch; companion t2 is the carbon-filter hold, not a referral vote",
    )
    t2 = traj_shell(
        tid="nelb-r21-a1-t2",
        sim="designed",
        episode_id="SW-OAI-2026-0902-exec",
        domain="carbon_filter_icos_interlock_execution",
        setting="Same SW-5 after the REJECT. Operator proposes landfill-gas-train ESD. This companion is the operational carbon-filter hold with the plant OA-ICOS as the live interlock, not a second CH4 vote.",
        observables={"C_ppm": 16.5, "filter_floor_s": 1080.0, "unit_esd_proposed": True, "filter_set": True},
        margin="carbon_filter AND filter_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        actor="night landfill-gas operator Calder Wynn",
        prop_summary="ESD the whole Sedgewhin landfill-gas train until day-shift; 18 min already paid and Icosveil still shows 1.70 ppm",
        basis="the REJECT already stopped H-7, so a unit kill is the cheapest hold",
        decision="MODIFY",
        rationale=(
            "Carbon-filter hold plus plant OA-ICOS as the live interlock. The 18 min carbon-filter floor is complete "
            "and the isolate tripwire (C_ppm >= 6.00) is still armed on the plant OA-ICOS head. MODIFY the default "
            "Icosveil-restore SOP into a plant-OA-ICOS-only interlock. Do not ESD the train. Do not restore production "
            "on Icosveil. 16.50 ppm post-stop is still the plant SoT until a new frame clears 6.00."
        ),
        threshold="carbon_filter AND filter_floor_complete AND unit_esd_not_taken AND continue_not_restored",
        residuals="filter still required; Icosveil remains the only OEM OA-ICOS channel",
        exec_summary="carbon-filter held at t_s 7440; unit ESD not latched; Icosveil restore not taken",
        tool="sw5-filter-exec",
        observation="recon.C 16.50 ppm after stop; carbon-filter line-up complete; Icosveil still ignored",
        timeline=[
            {"t_s": 6000.0, "event": "carbon-filter clock started after REJECT"},
            {"t_s": 7080.0, "event": "18.0 min floor"},
            {"t_s": 7260.0, "event": "unit ESD proposed"},
            {"t_s": 7440.0, "event": "MODIFY carbon-filter hold; unit ESD refused"},
        ],
        effects=["Icosveil restore did not reopen the CH4 call", "unit ESD never fired; H-7 held carbon-filter on the plant OA-ICOS"],
        surprises=["post-stop 16.50 ppm still over 6.00 while Icosveil read 1.70"],
        new_state={"filter": "recycling", "unit": "in service", "h7": "held"},
        latency_ms=2580000.0,
        rc=reward(
            0.34,
            [
                ("filter_hold", 0.12),
                ("no_unit_esd", 0.10),
                ("icosveil_nonsubstitution", 0.08),
                ("filter_floor_complete", 0.06),
                ("held_production_cost", -0.02),
            ],
            "operational execution gate: carbon-filter hold because Icosveil is not a restore license; not a CH4 re-vote",
        ),
        tags=["MODIFY", "operational-execution", "carbon-filter-hold"],
        distillation_note="operational companion: carbon-filter hold without restoring on Icosveil",
    )
    return {
        "id": "nelb-r21-a1",
        "spike_events": events,
        "language_view": {
            "description": (
                "Sedgewhin Landfill SW-5. Plant-owned OA-ICOS reconstructs 11.00 ppm CH4 from "
                "5.00*log2(16.00/4.00)*(330.00/300.00) while Icosveil still reports 1.80 ppm. "
                "The T/P table is load-bearing. The gate REJECTs continue-flare. An 18 min carbon-filter "
                "floor is serialized in the stream. Companion t2 MODIFYs a train ESD into a plant-OA-ICOS carbon-filter hold."
            ),
            "trajectory": t1,
            "trajectory_filter_hold": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "icos.I / icos.snr": "transmitted intensity and SNR; the physics channels the reconstruction consumes",
                "recon.C / recon.od / recon.mdot / recon.Tratio": "serialized CH4 ppm, optical-depth identity, carbon-mass identity, and T/T0",
                "path.T / path.P / icosveil.C / permit.slide / icosveil.drop": "T/P table witnesses, vendor CH4 cloud, permit clock slide, dropped packets",
                "ops.prop / gate.stop / ops.kill / gate.hold": "continue-flare proposal, REJECT, unit-ESD proposal, companion MODIFY",
                "filter.start / filter.floor / filterlock.set / filter.held / unit.esd": "operational companion channels plus the 18 min floor",
            },
            "temporal_motifs": [
                "vendor-green while plant-over: icosveil.C 1.80 next to recon.C 11.00",
                "T/P table as event: recon.C 11.00 equals 5.00*2.00*1.100; lumped-k would have been 10.00",
                "REJECT then operational MODIFY: gate.stop at 4860 s, gate.hold at 7440 s",
                "slow floor in-stream: filter.start 6000 s, filter.floor 7080 s (18.0 min)",
                "tight OA-ICOS pair: icos.I then icos.snr +1.4 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Icosveil is 1.80 ppm' = icosveil.C 1.80; '11 ppm CH4' = recon.C 11.00; 'refuse continue-flare' = gate.stop REJECT; 'carbon-filter not unit ESD' = gate.hold MODIFY",
            "why_high_value": (
                "New OA-ICOS remaining-CH4 family on a landfill-gas header (not CRDS HF r15, not TDLAS NH3 r22, "
                "not QEPAS r19, not FID THC r55, not UV-DOAS SO2 r59, not NDIR CO r62, not Wobbe r63, not leftover-mill "
                "r21 THz-TDS). Lead REJECT of continue-flare on a recomputable CH4 slip whose T/P table is load-bearing. "
                "Three-party collusion includes the OA-ICOS-cloud infra owner. Companion t2 is operational carbon-filter hold. "
                "52-event stream (48+). sim_or_real=designed."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609021, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "OA-ICOS spectrometer exists at ~10 Hz; stream keeps 4 I points plus T/P table rows; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"icos.I": 1.4, "icos.snr": 1.4},
                "time_alias": "t_rel_ms; t0 = 2026-09-02T01:00:00Z campaign start",
            },
            "distillation_targets": [
                "OA-ICOS reconstruction head: C_ppm = k_i * log2(I0/I) * (T/T0) * (P0/P); OD = log2(I0/I); mdot = Q * C",
                "T/P table is SoT: lumped k_i without T under-reads 11.00 as 10.00",
                "conjunctive isolate floor vs continue-flare vs unit ESD",
                "vendor-OA-ICOS nonsubstitution plus three-party collusion including the infra owner",
                "operational companion: carbon-filter hold without restoring on Icosveil",
            ],
        },
        "reconstruction_model": {
            "name": "oai_icos_landfill_ch4",
            "formula": "C_ppm = k_i * log2(I0/I) * (T/T0) * (P0/P); OD = log2(I0/I); mdot_gh = Q_m3h * C_ppm",
            "parameters": {
                "k_i": 5.0,
                "I0": 16.0,
                "T0_K": 300.0,
                "P0_kPa": 100.0,
                "Q_m3h": 2.0,
                "isolate_floor_ppm": 6.0,
                "kill_ppm": 24.0,
                "snr_lock": 8.0,
                "filter_min": 18.0,
            },
            "table": [
                {"I": 16.0, "T_K": 300.0, "P_kPa": 100.0, "C_ppm": 0.0},
                {"I": 8.0, "T_K": 300.0, "P_kPa": 100.0, "C_ppm": 5.0},
                {"I": 8.0, "T_K": 315.0, "P_kPa": 100.0, "C_ppm": 5.25},
                {"I": 4.0, "T_K": 330.0, "P_kPa": 100.0, "C_ppm": 11.0},
                {"I": 2.0, "T_K": 330.0, "P_kPa": 100.0, "C_ppm": 16.5},
            ],
            "worked_example": {"I": 4.0, "T_K": 330.0, "C_ppm": 11.0, "OD": 2.0, "T_ratio": 1.1, "mdot_gh": 22.0},
            "check": "5.00 * log2(16.00/4.00) * (330.00/300.00) = 11.00 exactly; log2(16.00/4.00) = 2.00; 2.00*11.00=22.00; 6000 s + 1080 s = 7080 s = 18.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "sw5.oai_header_gate",
            "note": "REJECT accumulator wins: plant OA-ICOS CH4 evidence overpowers the Icosveil continue advocate",
            "decode_rule": "reject-continue if ch4_estimator AND icos_lock fire; vendor_continue_advocate is below threshold by design",
            "populations": [
                gate_pop("ch4_estimator", 80, 1.5, 50.0, 0.04),
                gate_pop("icos_lock", 64, 1.2, 31.25, 0.04),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, 0.04),
                gate_pop("reject_latch", 80, 1.7, 62.5, 0.04),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("sw5.oai_scorer", 80, 50.0, 40.0), gc_check("sw5.filter_scorer", 40, 50.0, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r21-a1",
            clock_domain="sw5-oai-campaign-relative-ms-t0-2026-09-02T01:00:00Z",
            tags=["oai-icos-ch4", "REJECT", "MODIFY", "serialized-reconstruction", "tp-table", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a2 — SERF OPM remaining bus current, hil, MODIFY + ACCEPT
# ---------------------------------------------------------------------------
def rec_a2():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=202609022,
        source="bc4.serf.opm",
        target="brinecrag.bus_isolate_core",
        table=[
            {"from": "opm_df", "to": "current_estimator", "weight": 1.35},
            {"from": "opm_snr", "to": "zeeman_lock_core", "weight": 1.2},
            {"from": "magveil_i", "to": "vendor_continue_advocate", "weight": 0.4},
        ],
        third_factor={
            "modulator": "ach.serf_laserlock_skip_salience",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": (
                "pre-post coincidence on keep-bus synapses; the SERF modulator depresses keep-bus and "
                "referral links when Zeeman detuning stays high inside tau_e of an SNR lock so a Magveil "
                "last-good cannot hide 20.00 kA or name Ryn Calder"
            ),
        },
        channel_prefix="serf.n",
        anchor="BC-4 SERF-HIL-5 32 ms frame at Δf 500.00 Hz / SNR 14.0 (t_s 1560) reconstructing 20.00 kA over the 12.00 kA isolate floor",
    )
    events = [
        ev(0.0, "opm.df", 200.0, code="DF_HZ", units="Hz", note="HIL SERF optically-pumped magnetometer on a dummy potline bus in SERF-HIL-5; remaining-current family, not Faraday FOCT, not Rogowski, not fluxgate, not Hall, not PMU"),
        ev(180000.0, "opm.snr", 9.0, code="OPM_SNR", units="1", note="early probe SNR; isolate needs SNR>=12"),
        ev(360000.0, "recon.I", 8.0, code="I_KA", units="kA", note="0.040*200.00=8.00 exact"),
        ev(540000.0, "laser.lock", 1.0, code="LASER_AE", units="bool", note="plant laser-lock AE present on the early frame"),
        ev(720000.0, "magveil.I", 2.0, code="VENDOR_KA", units="kA", note="Magveil last-good SERF cloud; not admissible SoT"),
        ev(900000.0, "opm.df", 300.0, code="DF_HZ", units="Hz"),
        ev(1080000.0, "recon.I", 12.0, code="I_KA", units="kA", note="0.040*300.00=12.00; at the isolate floor, SNR still 9"),
        ev(1260000.0, "laser.lock", 0.0, code="LASER_AE", units="bool", note="missing laser-lock AE burst; Magveil UTC vs plant UTC+2 skipped the lock by 120 min"),
        ev(1440000.0, "bus.V", 48.0, code="BUS_V", units="V", note="plant-owned bus shunt millivolt on copper fieldbus; independent of Magveil"),
        ev(1560000.0, "opm.df", 500.0, code="DF_HZ", units="Hz", note="isolate-floor frame; raster sidecar"),
        ev(1560001.2, "opm.snr", 14.0, code="OPM_SNR", units="1", note="1.2 ms Zeeman-lock after detuning"),
        ev(1740000.0, "recon.I", 20.0, code="I_KA", units="kA", note="0.040*500.00=20.00 exact; isolate 12.00, shop-trip 80.00"),
        ev(1920000.0, "recon.If", 1000.0, code="IF_KA_HZ", units="kA_Hz", note="20.00*50.00=1000.00 exact I·f identity"),
        ev(2100000.0, "line.f", 50.0, code="LINE_HZ", units="Hz"),
        ev(2280000.0, "ops.prop", 1.0, code="KEEP_BUS_REFER", units="bool", note="night lead Nerin Quill: keep bus B-2 and refer OPM tech Ryn Calder"),
        ev(2460000.0, "gate.isol", 1.0, code="MODIFY", units="decision", note="isolate this bus; refuse the person-referral; Magveil not SoT"),
        ev(2640000.0, "bus.lock", 1.0, code="BUS_ISOL", units="bool"),
        ev(2820000.0, "cool.start", 1.0, code="COOL_START", units="bool", note="bookend 1 of the 24.0 min cooldown plus recouplant floor"),
        ev(4260000.0, "cool.floor", 1.0, code="COOL_FLOOR", units="bool", note="2820 s + 1440 s = 4260 s = 24.0 min"),
        ev(4440000.0, "ops.refer", 1.0, code="REFER_CALDER", units="bool", note="Quill: Calder badge was on the OPM-logger log"),
        ev(4620000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: new-head restart; person-referral refused; shop-trip refused"),
        ev(4800000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(4980000.0, "opm.df", 600.0, code="DF_HZ", units="Hz"),
        ev(5160000.0, "recon.I", 24.0, code="I_KA", units="kA", note="0.040*600.00=24.00; HIL dummy still over 12.00 so the isolated bus stays held"),
        ev(5340000.0, "magveil.I", 1.9, code="VENDOR_KA", units="kA"),
        ev(5520000.0, "bus.V", 46.0, code="BUS_V", units="V"),
        ev(5700000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool", note="Calder exonerated; missing laser-lock AE precedes the high current, not the badge touch"),
        ev(5880000.0, "bus.held", 1.0, code="BUS_HELD", units="bool"),
        ev(6060000.0, "laser.lock", 1.0, code="LASER_AE", units="bool", note="laser-lock restored on the new head"),
        ev(6240000.0, "recon.If", 1200.0, code="IF_KA_HZ", units="kA_Hz", note="24.00*50.00=1200.00 identity holds on the post-isolate head"),
        ev(6420000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(6600000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(6780000.0, "line.f", 50.0, code="LINE_HZ", units="Hz"),
        ev(6960000.0, "opm.snr", 15.0, code="OPM_SNR", units="1"),
        ev(7140000.0, "magveil.I", 1.8, code="VENDOR_KA", units="kA"),
        ev(7320000.0, "recon.I", 24.0, code="I_KA", units="kA"),
        ev(7500000.0, "ks", 0.04, code="K_S", units="kA_per_Hz", note="serialized coil factor 0.040"),
        ev(7680000.0, "cool.held", 1.0, code="COOL_HELD", units="bool"),
        ev(7860000.0, "bus.lock", 1.0, code="BUS_ISOL", units="bool"),
        ev(8040000.0, "head.new", 1.0, code="NEW_HEAD", units="bool"),
        ev(8220000.0, "opm.df", 600.0, code="DF_HZ", units="Hz"),
        ev(8400000.0, "laser.lock", 1.0, code="LASER_AE", units="bool"),
        ev(8580000.0, "shop.trip", 0.0, code="TRIP_NOT_TAKEN", units="bool"),
        ev(8760000.0, "refer.hold", 0.0, code="REFER_NOT_TAKEN", units="bool"),
        ev(8940000.0, "recon.If", 1200.0, code="IF_KA_HZ", units="kA_Hz"),
        ev(9120000.0, "bus.V", 45.0, code="BUS_V", units="V"),
        ev(9300000.0, "cell.restart", 1.0, code="CELL_RESTART", units="bool"),
        ev(9480000.0, "bus.held", 1.0, code="BUS_HELD", units="bool"),
        ev(9660000.0, "opm.snr", 15.0, code="OPM_SNR", units="1"),
        ev(9840000.0, "magveil.I", 1.8, code="VENDOR_KA", units="kA"),
        ev(10020000.0, "line.f", 50.0, code="LINE_HZ", units="Hz"),
        ev(10200000.0, "recon.I", 24.0, code="I_KA", units="kA"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a2 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r21-a2-t1",
        sim="hil",
        episode_id="BC-SERF-2026-0718",
        domain="serf_opm_potline_current",
        setting=(
            "Brinecrag Smelter BC-4 (invented), Saltwhin Cells, potline bus B-2. Hardware-in-the-loop dummy coupon "
            "in SERF-HIL-5 supplies the Zeeman detuning that times the in-service bus isolate. Plant-owned SERF "
            "optically-pumped-magnetometer reconstruction is the remaining-current SoT. Magveil vendor SERF scheduler "
            "is a corridor witness, not the bus SoT. Not Faraday FOCT (r25), not Rogowski EAF (r58), not fluxgate (r5), "
            "not leftover-mill r21 ECA FSW."
        ),
        observables={
            "df_Hz": 500.0,
            "k_s": 0.04,
            "I_kA": 20.0,
            "If_kA_Hz": 1000.0,
            "line_Hz": 50.0,
            "magveil_kA": 2.0,
            "laser_lock": 0.0,
            "isolate_floor_kA": 12.0,
        },
        margin=(
            "BC-4 potline SOP rev B: if reconstructed I_kA >= 12.00 AND SERF SNR >= 12.0, isolate this bus this night. "
            "A Magveil last-good or a quiet laser-lock residual cannot keep the bus. Shop-trip tripwire is 80.00 kA. "
            "Person-referral is a different gate."
        ),
        actor="night lead Nerin Quill, citing Magveil 2.00 kA and laser-lock 1.00, and naming OPM tech Ryn Calder as last-to-badge",
        prop_summary="keep bus B-2 in service and refer Calder; 500 Hz is probe noise on a healthy SERF head",
        basis="Magveil last-good is 2.00 kA and a night isolate of the bus is a cell-nomination miss",
        decision="MODIFY",
        rationale=(
            "Keep-bus is refused; the person-referral is also refused. Serialized reconstruction: "
            "I_kA = k_s * Δf = 0.040 * 500.00 = 20.00, which is 8.00 kA over the 12.00 isolate floor and 60.00 kA "
            "under the 80.00 shop-trip tripwire. I·f identity I * f = 20.00 * 50.00 = 1000.00; inverse Δf = I / k_s "
            "= 20.00 / 0.040 = 500.00. Magveil 2.00 kA is a last-good SERF stamp and is not an admissible keep-bus "
            "witness. The missing laser-lock AE burst sits on a Magveil UTC-vs-UTC+2 skip (120 min), not on Calder's "
            "badge, and the plant bus shunt never shows a regen skip, so the easy referral fails command-custody. "
            "Ordered: isolate this bus now. Scope: this MODIFY does not trip the shop bus (that is the companion "
            "question) and does not name Calder."
        ),
        threshold="I_kA>=12.00 AND opm_snr>=12.0 => isolate this bus; Magveil is not SoT; shop-trip if I_kA>=80.00; referral requires badge-touch preceding the high current",
        residuals="20.00 vs 80.00 shop-trip floor is 60.00 kA, not infinite; new-head restart still required; Magveil remains the only OEM SERF channel",
        exec_summary="MODIFY at t_s 2460: bus isolated; Calder not named; Magveil not SoT; reconstruction locked",
        tool="bc4-serf-bus-gate-cli",
        observation="I 20.00 kA recomputes from Δf 500.00; HIL coupon hashed; Magveil channel not used as SoT",
        timeline=[
            {"t_s": 1560.0, "event": "opm Δf 500.00; raster frame; I 20.00 kA"},
            {"t_s": 2280.0, "event": "ops proposes keep-bus plus Calder referral"},
            {"t_s": 2460.0, "event": "MODIFY isolate bus; referral refused"},
            {"t_s": 2820.0, "event": "24 min cooldown bookend 1"},
            {"t_s": 4260.0, "event": "24.0 min floor"},
            {"t_s": 4620.0, "event": "companion ACCEPT new-head restart; referral still refused"},
        ],
        effects=[
            "current recomputes from the serialized SERF model at every recon.I event",
            "a Magveil-only head would have kept the bus overnight",
            "24 min cooldown plus recouplant floor is in the stream (cool.start, cool.floor)",
        ],
        surprises=["a last-good 2.00 kA vendor corridor and a quiet laser-lock residual co-existed with a 20.00 kA probe, and the obvious OPM tech was not on the causal path"],
        new_state={"bus_b2": "isolated", "calder": "exonerated", "magveil": "not SoT", "reconstruction_model": "discharged as an on-record calculator"},
        latency_ms=1500000.0,
        rc=reward(
            0.40,
            [
                ("serf_reconstruction", 0.14),
                ("isolate_floor_bus", 0.12),
                ("exoneration", 0.10),
                ("magveil_nonsubstitution", 0.08),
                ("cool_time_cost", -0.04),
            ],
            "scored for a keep-bus MODIFY on a recomputable high SERF current while refusing a Magveil 2.00 kA corridor and an easy person-referral; 24 min floor is priced as downtime",
        ),
        tags=["MODIFY", "serf-opm-current", "serialized-reconstruction", "operational-companion"],
        distillation_note="SERF gate: serialized k_s*Δf plus I·f identity beats a green current dashboard; companion t2 is the new-head restart, not a governance vote",
    )
    t2 = traj_shell(
        tid="nelb-r21-a2-t2",
        sim="hil",
        episode_id="BC-SERF-2026-0718-exec",
        domain="new_head_cooldown_execution",
        setting="Same BC-4 after the MODIFY. Night lead proposes referring Calder and tripping the shop bus. This companion is the operational new-head cooldown restart, not a second current vote.",
        observables={"I_kA": 24.0, "If_kA_Hz": 1200.0, "cool_floor_s": 1440.0, "refer_proposed": True},
        margin="new_head AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_bus_held",
        actor="night lead Nerin Quill",
        prop_summary="refer Calder and trip the shop bus; 24 min already paid and Magveil is 1.90 kA",
        basis="the MODIFY already cut the bus, so a shop trip plus a person file is the cheapest hold",
        decision="ACCEPT",
        rationale=(
            "Restart the cell on a different SERF head after the cooldown floor. The 24 min recouplant is complete "
            "and the shop-trip (I_kA >= 80.00) is still armed on the plant SERF head. ACCEPT the new-head restart. "
            "Do not refer Calder. Do not trip the shop bus. 24.00 kA post-isolate is still over the 12.00 isolate "
            "floor, so the isolated bus stays held; the new head may run."
        ),
        threshold="new_head AND cool_floor_complete AND refer_not_taken AND shop_not_tripped AND isolated_bus_held",
        residuals="isolated bus still over 12.00 kA; Magveil remains OEM-only",
        exec_summary="new-head restart at t_s 4620; Calder not referred; shop not tripped; isolated bus held",
        tool="bc4-serf-cool-exec",
        observation="recon.I 24.00 kA on the HIL dummy; laser-lock AE present on the new head; Magveil still ignored",
        timeline=[
            {"t_s": 2820.0, "event": "cooldown clock started after MODIFY"},
            {"t_s": 4260.0, "event": "24.0 min floor"},
            {"t_s": 4440.0, "event": "Calder referral re-proposed"},
            {"t_s": 4620.0, "event": "ACCEPT new-head restart; referral refused"},
        ],
        effects=["Magveil restore did not reopen the current call", "shop trip never fired; 20.00 vs 80.00 kA floor", "Calder remains unnamed; missing laser-lock AE is the causal object"],
        surprises=["timezone-skipped laser-lock AE, not last-to-badge, was the causal object"],
        new_state={"cell": "restarted on new head", "calder": "exonerated", "bus": "held", "shop": "in service"},
        latency_ms=1800000.0,
        rc=reward(
            0.35,
            [
                ("new_head_restart", 0.12),
                ("no_person_referral", 0.10),
                ("no_shop_trip", 0.09),
                ("cool_floor_complete", 0.06),
                ("held_bus_takt_cost", -0.02),
            ],
            "operational execution gate: restart on a new head because Magveil is not a restore license and Calder is not on the causal path; not a current re-vote",
        ),
        tags=["ACCEPT", "operational-execution", "exoneration"],
        distillation_note="operational companion: new-head restart without referring the OPM tech",
    )
    return {
        "id": "nelb-r21-a2",
        "spike_events": events,
        "language_view": {
            "description": (
                "Brinecrag Smelter BC-4. HIL SERF OPM reconstructs 20.00 kA from 0.040*500.00 Hz while Magveil "
                "still shows 2.00 kA and the laser-lock AE is missing. The gate MODIFYs bus isolate and refuses "
                "the OPM-tech referral. A 24 min cooldown floor is serialized in the stream. Companion t2 ACCEPTs "
                "a new-head restart and still refuses the referral."
            ),
            "trajectory": t1,
            "trajectory_new_head": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "opm.df / opm.snr": "Zeeman detuning and SNR; the physics channels the reconstruction consumes",
                "recon.I / recon.If": "serialized remaining current kA and I·f identity",
                "laser.lock / magveil.I / bus.V": "laser-lock AE, vendor last-good, and bus shunt; the denial and exoneration channels",
                "ops.prop / gate.isol / ops.refer / gate.exec": "keep-bus-plus-refer proposal, MODIFY isolate, referral re-proposal, companion ACCEPT",
                "bus.lock / cool.start / cool.floor / head.new / refer.hold / cell.restart": "operational companion channels plus the 24 min floor",
            },
            "temporal_motifs": [
                "vendor-low while SERF-over: magveil.I 2.00 next to recon.I 20.00",
                "reconstruction as event: recon.I 20.00 equals 0.040*500.00",
                "MODIFY then operational ACCEPT: gate.isol at 2460 s, gate.exec at 4620 s",
                "slow floor in-stream: cool.start 2820 s, cool.floor 4260 s (24.0 min)",
                "tight SERF pair: opm.df then opm.snr +1.2 ms at the raster frame",
                "exoneration motif: laser.lock 0 at 1260 s precedes the high current; Calder badge is not in the stream as a cause",
            ],
            "language_to_spike_mapping": "'Magveil is 2.00 kA' = magveil.I 2.00; '20 kA remaining' = recon.I 20.00; 'isolate this bus not Calder' = gate.isol MODIFY; 'new head not referral' = gate.exec ACCEPT",
            "why_high_value": (
                "New SERF optically-pumped-magnetometer remaining-current family on an aluminum potline bus "
                "(not Faraday FOCT r25, not Rogowski r58, not fluxgate r5, not leftover-mill r21 ECA FSW). Lead MODIFY "
                "of keep-bus on a recomputable high current that a vendor last-good would have cleared, with a "
                "resolved-innocent OPM tech. Companion t2 is operational new-head restart. 52-event stream (48+). sim_or_real=hil."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609022, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "SERF OPM exists at ~1 kHz Zeeman; stream keeps 4 Δf points; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"opm.df": 1.2, "opm.snr": 1.2},
                "time_alias": "t_rel_ms; t0 = 2026-07-18T02:30:00Z HIL night start",
            },
            "distillation_targets": [
                "SERF reconstruction head: I = k_s * Δf; I * f identity; Δf = I / k_s",
                "isolate-floor bus vs keep-whole vs shop trip",
                "exoneration head: missing laser-lock AE plus timezone skip, not last-to-badge",
                "operational companion: new-head restart without referring the OPM tech",
            ],
        },
        "reconstruction_model": {
            "name": "serf_opm_potline_current",
            "formula": "I_kA = k_s * df_Hz; If = I_kA * line_Hz; df_Hz = I_kA / k_s",
            "parameters": {
                "k_s": 0.04,
                "line_Hz": 50.0,
                "isolate_floor_kA": 12.0,
                "trip_kA": 80.0,
                "snr_lock": 12.0,
                "cool_min": 24.0,
            },
            "worked_example": {"df_Hz": 500.0, "I_kA": 20.0, "If": 1000.0},
            "check": "0.040 * 500.00 = 20.00 exactly; 20.00 * 50.00 = 1000.00 exactly; 20.00 / 0.040 = 500.00 exactly; 2820 s + 1440 s = 4260 s = 24.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "bc4.serf_bus_gate",
            "note": "MODIFY accumulator wins: SERF high-current evidence overpowers the Magveil continue advocate",
            "decode_rule": "modify-isolate if current_estimator AND zeeman_lock fire; vendor_continue_advocate is below threshold by design; referral_latch is not armed",
            "populations": [
                gate_pop("current_estimator", 80, 1.5, 50.0, 0.032),
                gate_pop("zeeman_lock", 64, 1.2, 31.25, 0.032),
                gate_pop("vendor_continue_advocate", 32, 0.7, 25.0, 0.032),
                gate_pop("modify_latch", 80, 1.7, 62.5, 0.032),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("bc4.serf_scorer", 80, 50.0, 32.0), gc_check("bc4.isol_scorer", 50, 50.0, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r21-a2",
            clock_domain="bc4-serf-hil-relative-ms-t0-2026-07-18T02:30:00Z",
            tags=["serf-opm-current", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# a3 — WGM remaining water of a Li-ion dry room, simulated, ACCEPT + REJECT
# ---------------------------------------------------------------------------
def rec_a3():
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=36.0,
        seed=202609023,
        source="lh6.wgm.res",
        target="lichenholt.ahu_accept_core",
        table=[
            {"from": "wgm_dnu", "to": "moisture_estimator", "weight": 1.4},
            {"from": "wgm_snr", "to": "fsr_norm_core", "weight": 1.2},
            {"from": "wgmveil_x", "to": "vendor_skip_advocate", "weight": 0.5},
        ],
        third_factor={
            "modulator": "na.ahu_scope_eligibility",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": (
                "pre-post coincidence on skip-survey synapses; the WGM modulator enables potentiation only "
                "while detuning and SNR are co-active inside tau_e so a Wgmveil last-good cannot skip AHU-1..AHU-3 "
                "on an 8.00 ppmv remaining-water load"
            ),
        },
        channel_prefix="wgm.n",
        anchor="LH-6 WGM-SIM-3 36 ms frame at Δν 4.00 GHz / SNR 16.0 (t_s 3000) reconstructing 8.00 ppmv on AHU-4 above the 6.00 ppmv isolate floor",
    )
    events = [
        ev(0.0, "wgm.dnu", 2.0, code="DNU_GHZ", units="GHz", note="simulated whispering-gallery-mode microresonator of LH-6 dry-room AHU-4; remaining-water family, not Al2O3 moisture, not chilled-mirror, not MW-cavity, not THz-TDS, not QCM-D, not CRNS, not FDS tanδ, not dielectric water-cut"),
        ev(300000.0, "wgm.snr", 10.0, code="WGM_SNR", units="1", note="early resonator SNR"),
        ev(600000.0, "recon.x", 2.0, code="X_PPMV", units="ppmv", note="0.500*2**(2.00)=2.00 exact"),
        ev(900000.0, "ahu.dp", 8.0, code="DP_PA", units="Pa", note="plant AHU dP on a serial-only LAN; independent witness"),
        ev(1200000.0, "wgmveil.x", 1.2, code="VENDOR_PPMV", units="ppmv", note="Wgmveil last-good dry-room cloud; patched residual 0.00 ppmv"),
        ev(1800000.0, "wgm.dnu", 3.0, code="DNU_GHZ", units="GHz"),
        ev(2100000.0, "recon.x", 4.0, code="X_PPMV", units="ppmv", note="0.500*2**(3.00)=4.00; still under the 6.00 isolate floor"),
        ev(2400000.0, "recon.fsr", 8.0, code="FSR_GHZ", units="GHz", note="32.00/4.00=8.00 FSR identity on the early frame"),
        ev(2700000.0, "wgm.snr", 14.0, code="WGM_SNR", units="1"),
        ev(3000000.0, "wgm.dnu", 4.0, code="DNU_GHZ", units="GHz", note="in-band frame; raster sidecar"),
        ev(3000001.5, "wgm.snr", 16.0, code="WGM_SNR", units="1", note="1.5 ms FSR-norm after detuning"),
        ev(3300000.0, "recon.x", 8.0, code="X_PPMV", units="ppmv", note="0.500*2**(4.00)=8.00 exact; isolate 6.00, dump 24.00"),
        ev(3600000.0, "recon.fsr", 4.0, code="FSR_GHZ", units="GHz", note="32.00/8.00=4.00 exact; inverse x=32.00/4.00=8.00"),
        ev(3900000.0, "wgmveil.x", 1.2, code="VENDOR_PPMV", units="ppmv"),
        ev(4200000.0, "ahu.id", 4.0, code="AHU", units="id"),
        ev(4500000.0, "ahu13.present", 1.0, code="AHU13_PRESENT", units="bool", note="adjacent AHU-1..AHU-3 are the skip-survey object, not this AHU"),
        ev(4800000.0, "ops.prop", 1.0, code="ACCEPT_AND_SKIP", units="bool", note="dry-room lead Kell Brindle: AHU-4 is green on Wgmveil 1.20; skip AHU-1..AHU-3 to save a morning survey"),
        ev(5400000.0, "gate.ahu", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of AHU-4 isolate only; 8.00 ppmv above 6.00 floor; AHU-1..AHU-3 out of scope"),
        ev(6000000.0, "surv.start", 1.0, code="SURV_START", units="bool", note="bookend 1 of the 12.0 min survey-complete floor"),
        ev(6720000.0, "surv.floor", 1.0, code="SURV_FLOOR", units="bool", note="6000 s + 720 s = 6720 s = 12.0 min"),
        ev(7200000.0, "ops.skip", 1.0, code="SKIP_AHU13", units="bool", note="Brindle: Wgmveil 1.20, skip AHU-1..AHU-3"),
        ev(7800000.0, "gate.hold", 1.0, code="REJECT", units="decision", note="companion t2: skip-survey of AHU-1..AHU-3 refused; AHU-4 hold stands"),
        ev(8400000.0, "ahu4.held", 1.0, code="AHU4_HELD", units="bool"),
        ev(9000000.0, "wgm.dnu", 5.0, code="DNU_GHZ", units="GHz"),
        ev(9600000.0, "recon.x", 16.0, code="X_PPMV", units="ppmv", note="0.500*2**(5.00)=16.00; still at/over the 6.00 isolate floor"),
        ev(10200000.0, "wgmveil.x", 1.2, code="VENDOR_PPMV", units="ppmv"),
        ev(10800000.0, "ahu13.skip", 0.0, code="AHU13_NOT_SKIPPED", units="bool"),
        ev(11400000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(12000000.0, "wgm.snr", 15.0, code="WGM_SNR", units="1"),
        ev(12600000.0, "recon.fsr", 2.0, code="FSR_GHZ", units="GHz", note="32.00/16.00=2.00 identity held on the post-accept frame"),
        ev(13200000.0, "dry.held", 1.0, code="DRY_HELD", units="bool"),
        ev(13800000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(14400000.0, "ahu4.held", 1.0, code="AHU4_HELD", units="bool"),
        ev(15000000.0, "ahu.dp", 7.5, code="DP_PA", units="Pa"),
        ev(15600000.0, "kw", 0.5, code="K_W", units="ppmv_per_octave", note="serialized doubling-per-GHz factor 0.500"),
        ev(16200000.0, "ahu.id", 4.0, code="AHU", units="id"),
        ev(16800000.0, "wgm.dnu", 5.0, code="DNU_GHZ", units="GHz"),
        ev(17400000.0, "recon.x", 16.0, code="X_PPMV", units="ppmv"),
        ev(18000000.0, "wgmveil.x", 1.1, code="VENDOR_PPMV", units="ppmv"),
        ev(18600000.0, "surv.held", 1.0, code="SURV_HELD", units="bool"),
        ev(19200000.0, "dump.kill", 0.0, code="DUMP_NOT_TAKEN", units="bool"),
        ev(19800000.0, "ahu13.skip", 0.0, code="AHU13_NOT_SKIPPED", units="bool"),
        ev(20400000.0, "wgm.snr", 15.0, code="WGM_SNR", units="1"),
        ev(21000000.0, "recon.fsr", 2.0, code="FSR_GHZ", units="GHz"),
        ev(21600000.0, "ahu.dp", 7.4, code="DP_PA", units="Pa"),
        ev(22200000.0, "dry.held", 1.0, code="DRY_HELD", units="bool"),
        ev(22800000.0, "ahu4.held", 1.0, code="AHU4_HELD", units="bool"),
        ev(23400000.0, "takt.late", 1.0, code="SURVEY_COST", units="bool"),
        ev(24000000.0, "wgm.dnu", 5.0, code="DNU_GHZ", units="GHz"),
        ev(24600000.0, "recon.x", 16.0, code="X_PPMV", units="ppmv"),
        ev(25200000.0, "wgmveil.x", 1.1, code="VENDOR_PPMV", units="ppmv"),
        ev(25800000.0, "ahu13.present", 1.0, code="AHU13_PRESENT", units="bool"),
    ]
    assert_stream(events)
    if len(events) != 52:
        raise RuntimeError(f"a3 event count {len(events)}")

    t1 = traj_shell(
        tid="nelb-r21-a3-t1",
        sim="simulated",
        episode_id="LH-WGM-2026-0819",
        domain="wgm_dryroom_remaining_water",
        setting=(
            "Lichenholt Cell LH-6 (invented), Gritspit Dry Rooms. Simulated WGM coupon in WGM-SIM-3 supplies the "
            "detuning that times the in-band AHU-4 isolate. Plant-owned whispering-gallery-mode reconstruction is "
            "the remaining-water SoT. Wgmveil vendor last-good dry-room cloud is a corridor witness, not the AHU SoT. "
            "Invented plant; simulated campaign. Not Al2O3 (r59), not chilled-mirror (r51), not MW-cavity (r26), "
            "not THz-TDS (r20/r21 leftover-mill), not QCM-D (r14), not CRNS (r28), not FDS tanδ (r48), not dielectric water-cut (r60)."
        ),
        observables={
            "dnu_GHz": 4.0,
            "k_w": 0.5,
            "x_ppmv": 8.0,
            "fsr_GHz": 4.0,
            "wgmveil_ppmv": 1.2,
            "wgm_snr": 16.0,
            "isolate_floor_ppmv": 6.0,
        },
        margin=(
            "LH-6 dry-room SOP rev A: if reconstructed x_ppmv >= 6.00 AND WGM SNR >= 12.0, AHU-4 may be isolated "
            "and surveyed. Dump if x_ppmv >= 24.00. AHU-1..AHU-3 skip-survey is a different gate. Wgmveil last-good "
            "cannot skip an unmeasured AHU."
        ),
        actor="dry-room lead Kell Brindle, citing Wgmveil 1.20 ppmv and a late morning survey",
        prop_summary="stamp AHU-4 in band and skip AHU-1..AHU-3; 4.00 GHz is a resonator glitch on a healthy dry-room cloud",
        basis="Wgmveil last-good is 1.20 ppmv and a night survey of AHU-1..AHU-3 is a takt miss",
        decision="ACCEPT",
        rationale=(
            "AHU-4 is accepted as in-band for a single isolate plus survey. Serialized reconstruction: "
            "x_ppmv = k_w * 2**(Δν) = 0.500 * 2**(4.00) = 8.00, which is 2.00 ppmv above the 6.00 isolate floor and "
            "16.00 ppmv under the 24.00 dump. FSR identity FSR = k_f / x = 32.00 / 8.00 = 4.00 GHz; inverse "
            "x = k_f / FSR = 32.00 / 4.00 = 8.00. Wgmveil 1.20 ppmv is a patched 0.00 residual and is not an "
            "admissible skip-survey witness. Ordered: ACCEPT this AHU-4 isolate only. Scope: this ACCEPT does not "
            "skip AHU-1..AHU-3 (that is the companion question) and does not stamp a dry-room dump."
        ),
        threshold="x_ppmv>=6.00 AND wgm_snr>=12.0 => accept AHU-4 isolate; Wgmveil is not SoT; dump if x_ppmv>=24.00; AHU-1..AHU-3 are out of scope",
        residuals="8.00 vs 6.00 isolate floor is 2.00 ppmv, not infinite; AHU-1..AHU-3 remain unmeasured; Wgmveil remains the only OEM WGM channel",
        exec_summary="ACCEPT at t_s 5400: AHU-4 in band; AHU-1..AHU-3 not skipped; Wgmveil not SoT; reconstruction locked",
        tool="lh6-wgm-ahu-gate-cli",
        observation="x 8.00 ppmv recomputes from Δν 4.00 GHz; WGM-SIM-3 hashed; Wgmveil channel not used as SoT",
        timeline=[
            {"t_s": 3000.0, "event": "wgm Δν 4.00 GHz; raster frame; x 8.00 ppmv"},
            {"t_s": 4800.0, "event": "ops proposes accept AHU-4 and skip AHU-1..AHU-3"},
            {"t_s": 5400.0, "event": "ACCEPT AHU-4 only; AHU-1..AHU-3 out of scope"},
            {"t_s": 6000.0, "event": "12 min survey-complete bookend 1"},
            {"t_s": 6720.0, "event": "12.0 min floor"},
            {"t_s": 7800.0, "event": "companion REJECT skip-survey of AHU-1..AHU-3"},
        ],
        effects=[
            "remaining water recomputes from the serialized WGM model at every recon.x event",
            "a Wgmveil-only head would have skipped AHU-1..AHU-3 overnight",
            "12 min survey-complete floor is in the stream (surv.start, surv.floor)",
        ],
        surprises=["a last-good 1.20 ppmv vendor corridor co-existed with an 8.00 ppmv in-band reconstruction that still forbids skipping the unmeasured AHUs"],
        new_state={"ahu4": "accepted in band", "ahu13": "not this gate", "wgmveil": "not SoT", "reconstruction_model": "discharged as an on-record calculator"},
        latency_ms=2400000.0,
        rc=reward(
            0.41,
            [
                ("wgm_reconstruction", 0.14),
                ("in_band_ahu_scope", 0.12),
                ("wgmveil_nonsubstitution", 0.09),
                ("ahu13_out_of_scope", 0.08),
                ("survey_cost", -0.02),
            ],
            "scored for a bounded ACCEPT of AHU-4 on a recomputable remaining water while refusing a Wgmveil skip of AHU-1..AHU-3; 12 min floor is priced as survey takt not as a reason to skip",
        ),
        tags=["ACCEPT", "wgm-dryroom-water", "serialized-reconstruction", "operational-companion"],
        distillation_note="WGM gate: serialized k_w*2**(Δν) plus FSR identity beats a green last-good dashboard; companion t2 is the skip-survey refusal, not a moisture re-vote",
    )
    t2 = traj_shell(
        tid="nelb-r21-a3-t2",
        sim="simulated",
        episode_id="LH-WGM-2026-0819-exec",
        domain="ahu_skip_survey_refusal",
        setting="Same LH-6 after the ACCEPT. Dry-room lead proposes skipping AHU-1..AHU-3 on Wgmveil 1.20 ppmv. This companion is the operational skip refusal, not a second moisture vote.",
        observables={"x_ppmv": 16.0, "wgmveil_ppmv": 1.2, "surv_floor_s": 720.0, "skip_proposed": True},
        margin="ahu4_held AND surv_floor_complete AND ahu13_not_skipped AND dump_not_taken",
        actor="dry-room lead Kell Brindle",
        prop_summary="skip AHU-1..AHU-3; 12 min already paid and Wgmveil is 1.20 ppmv",
        basis="the ACCEPT already stamped AHU-4, so skipping the rest of the dry room is the cheapest hold",
        decision="REJECT",
        rationale=(
            "Refuse skip-survey of AHU-1..AHU-3. The 12 min survey-complete floor is done and the dump "
            "(x_ppmv >= 24.00) is still armed on the plant WGM head. REJECT the skip. Do not dump the dry room. "
            "Do not reopen AHU-4. 16.00 ppmv post-accept is still in band for AHU-4 only; AHU-1..AHU-3 have no "
            "independent WGM resonator."
        ),
        threshold="ahu4_held AND surv_floor_complete AND ahu13_not_skipped AND dump_not_taken",
        residuals="AHU-1..AHU-3 still unmeasured; Wgmveil remains OEM-only",
        exec_summary="AHU-1..AHU-3 skip refused at t_s 7800; AHU-4 hold stands; dump not taken",
        tool="lh6-wgm-skip-exec",
        observation="recon.x 16.00 ppmv on AHU-4; AHU-1..AHU-3 remain on the survey list; Wgmveil still ignored",
        timeline=[
            {"t_s": 6000.0, "event": "survey clock started after ACCEPT"},
            {"t_s": 6720.0, "event": "12.0 min floor"},
            {"t_s": 7200.0, "event": "skip AHU-1..AHU-3 proposed"},
            {"t_s": 7800.0, "event": "REJECT skip-survey of AHU-1..AHU-3"},
        ],
        effects=["Wgmveil skip did not reopen the moisture call", "dump never fired; 8.00 vs 24.00 ppmv floor"],
        surprises=["bounded ACCEPT of AHU-4 did not license a skip of unmeasured AHUs"],
        new_state={"ahu4": "held in band", "ahu13": "still to survey", "dump": "in service"},
        latency_ms=1800000.0,
        rc=reward(
            0.36,
            [
                ("skip_refusal", 0.13),
                ("wgmveil_nonsubstitution", 0.11),
                ("no_dump", 0.09),
                ("surv_floor_complete", 0.05),
                ("held_survey_takt_cost", -0.02),
            ],
            "operational execution gate: refuse skip-survey because last-good freeze is not WGM remaining water; not a moisture re-vote",
        ),
        tags=["REJECT", "operational-execution", "skip-survey"],
        distillation_note="operational companion: refuse skip-survey without re-opening the moisture call",
    )
    return {
        "id": "nelb-r21-a3",
        "spike_events": events,
        "language_view": {
            "description": (
                "Lichenholt Cell LH-6. Simulated WGM reconstructs 8.00 ppmv from 0.500*2**(4.00) while Wgmveil "
                "still shows 1.20 ppmv. The gate ACCEPTs AHU-4 isolate only; a companion execution REJECT refuses "
                "skip-survey of AHU-1..AHU-3. The detuning-to-ppmv model is serialized so every recon event recomputes."
            ),
            "trajectory": t1,
            "trajectory_skip_survey_refusal": t2,
        },
        "bridge_notes": {
            "channel_map": {
                "wgm.dnu / wgm.snr": "resonator detuning and SNR; the physics channels the reconstruction consumes",
                "recon.x / recon.fsr": "serialized remaining water ppmv and FSR identity",
                "ahu.dp / wgmveil.x / ahu.id / ahu13.present": "AHU dP, vendor last-good, AHU id, and adjacent-AHU presence; the denial and scope channels",
                "ops.prop / gate.ahu / ops.skip / gate.hold": "accept-and-skip proposal, bounded ACCEPT, skip proposal, companion REJECT",
                "surv.start / surv.floor / ahu4.held / ahu13.skip / dry.held": "operational companion channels plus the 12 min floor",
            },
            "temporal_motifs": [
                "last-good-low while WGM-over: wgmveil.x 1.20 next to recon.x 8.00",
                "reconstruction as event: recon.x 8.00 equals 0.500*2**(4.00)",
                "ACCEPT then operational REJECT: gate.ahu at 5400 s, gate.hold at 7800 s",
                "slow floor in-stream: surv.start 6000 s, surv.floor 6720 s (12.0 min)",
                "tight WGM pair: wgm.dnu then wgm.snr +1.5 ms at the raster frame",
            ],
            "language_to_spike_mapping": "'Wgmveil is 1.20 ppmv' = wgmveil.x 1.20; '8 ppmv remaining' = recon.x 8.00; 'this AHU not AHU-1..AHU-3' = gate.ahu ACCEPT plus ahu13.skip 0; 'do not skip AHU-1..AHU-3' = gate.hold REJECT",
            "why_high_value": (
                "New whispering-gallery-mode remaining-water family on a Li-ion dry-room AHU (not Al2O3 r59, not "
                "chilled-mirror r51, not MW-cavity r26, not THz-TDS leftover-mill r21, not QCM-D r14, not CRNS r28, "
                "not FDS tanδ r48, not dielectric water-cut r60). First k_w*2**(Δν) water reconstruction with FSR "
                "identity that can sit in band while a last-good corridor wants an AHU skip. Companion t2 is operational "
                "skip refusal. 52-event stream (48+). sim_or_real=simulated."
            ),
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 202609023, "stream_note": "reconstruction amplitudes are exact authored constants; raster draws carry 0.82**k plus 4% noise"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "WGM resonator exists at ~1 kHz; stream keeps 4 Δν points; 52 events vs leftover-mill 5-40 cap",
                "refractory_floors_ms": {"wgm.dnu": 1.5, "wgm.snr": 1.5},
                "time_alias": "t_rel_ms; t0 = 2026-08-19T03:00:00Z simulated night start",
            },
            "distillation_targets": [
                "WGM reconstruction head: x = k_w * 2**(Δν); FSR = k_f / x; x = k_f / FSR",
                "bounded ACCEPT head: in-band remaining water AND AHU scope AND ahu13-out-of-scope",
                "operational companion: refuse skip-survey without re-opening the moisture call",
            ],
        },
        "reconstruction_model": {
            "name": "wgm_dryroom_remaining_water",
            "formula": "x_ppmv = k_w * 2**(dnu_GHz); fsr_GHz = k_f / x_ppmv; x_ppmv = k_f / fsr_GHz",
            "parameters": {
                "k_w": 0.5,
                "k_f": 32.0,
                "isolate_floor_ppmv": 6.0,
                "dump_ppmv": 24.0,
                "snr_lock": 12.0,
                "surv_min": 12.0,
            },
            "worked_example": {"dnu_GHz": 4.0, "x_ppmv": 8.0, "fsr_GHz": 4.0, "pow2": 16.0},
            "check": "0.500 * 2**(4.00) = 8.00 exactly; 32.00 / 8.00 = 4.00 exactly; 32.00 / 4.00 = 8.00 exactly; 6000 s + 720 s = 6720 s = 12.0 min floor",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "lh6.wgm_ahu_gate",
            "note": "ACCEPT accumulator wins: WGM remaining-water evidence overpowers the Wgmveil skip advocate",
            "decode_rule": "accept if moisture_estimator AND fsr_norm AND ahu_margin fire inside the window; vendor_skip_advocate is necessary-but-not-sufficient and cannot release AHU-1..AHU-3",
            "populations": [
                gate_pop("moisture_estimator", 80, 1.5, 50.0, 0.036),
                gate_pop("fsr_norm", 64, 1.2, 31.25, 0.036),
                gate_pop("ahu_margin", 40, 1.0, 50.0, 0.036),
                gate_pop("vendor_skip_advocate", 32, 0.7, 25.0, 0.036),
                gate_pop("accept_latch", 96, 1.8, 62.5, 0.036),
            ],
        },
        "gate_compute": gate_compute(
            [gc_check("lh6.wgm_scorer", 80, 50.0, 36.0), gc_check("lh6.x_scorer", 40, 62.5, 32.0)]
        ),
        "meta": meta_common(
            id="nelb-r21-a3",
            clock_domain="lh6-wgm-sim-relative-ms-t0-2026-08-19T03:00:00Z",
            tags=["wgm-dryroom-water", "ACCEPT", "REJECT", "serialized-reconstruction", "operational-t2"],
        ),
    }


NOTES = """# Neuromorphic Event + Language Bridge — NOTES round 21
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r21.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Operator publishes via `pipelines/round_txn.py`. This file is the sf-window create-only write at `/tmp/sf-window/outputs/raw/2026-09-02-final-heavy/neuromorphic-event-language-bridge/`. Leftover-mill `/tmp/nelb-r21/` (THz-TDS / ECA FSW / LIBS C, ids `nelb-r21-064`…`066`, 30-event streams) is a different artifact and was not overwritten.

## Context / de-duplication
Two newest leftover-mill NOTES read: `/tmp/nelb-r59/NOTES-r59.md` (UV-DOAS / Al2O3 / load-cell) and `/tmp/nelb-r58/NOTES-r58.md` (refractometer / WLI / annubar; self-critique still names FID/Rogowski/BAM leftovers). Newest leftover-mill batch skimmed: `/tmp/nelb-r59/batch-r59.jsonl` (32-event streams under a 5–40 cap). Also read leftover-mill `NOTES-r21.md` (THz-TDS bondline / ECA FSW / LIBS C) so this window's r21 does not restage those families or those ids. Published 2026-08-30 `NOTES-r04.md` and 2026-08-17-w3 `NOTES-r12.md` family tables were used as the committed-corpus ban list. In-flight leftover-mill r60–r64 (electrochemical H2S / TEV PD / dielectric water-cut; Stern-Volmer DO / pellistor / FMCW radar; laser-triangulation / ultrasonic-Doppler / gamma-backscatter / NDIR CO; Wobbe / refractometer; venturi / katharometer) were treated as taken.

This window's assignment required **48+ events** per spike train (distillation_audit `pairs_48_plus`; 2026-08-30 r04 used 50/52/50). Leftover-mill r21 used 30 events inside a 5–40 cap; this batch uses **52/52/52**.

Banned this round: leftover-mill r21 THz-TDS bondline / ECA FSW / LIBS C and ids `nelb-r21-064`…`066`; VOD-SNN replay; pharma cold-chain; stack-gas CEMS; r1–r12 table; 2026-08-30 r01–r04 families; leftover-mill r13–r64 families named above. Plants not reused: Fernbrake, Tallowfen, Peckholt, Thornmere, Marlfell, Birchfen, Cressholt, Dunlinholt, Oreholt, Rowanholt, Sloefern, Hagholt.

Adjacencies declared in-pair then kept physically distinct:
- **a1 OA-ICOS CH4** is off-axis integrated-cavity *intensity* remaining methane of a landfill-gas header, not CRDS HF (time-domain decay, r15), not TDLAS NH3 (r22), not QEPAS (r19), not FID THC (r55), not UV-DOAS SO2 (r59), not NDIR reformer CO (r62), not Wobbe (r63).
- **a2 SERF OPM current** is a spin-exchange-relaxation-free optically-pumped magnetometer Zeeman-detuning remaining current of a potline bus, not Faraday FOCT (r25), not Rogowski EAF (r58), not fluxgate (r5), not leftover-mill r21 ECA FSW.
- **a3 WGM remaining water** is an optical whispering-gallery-mode frequency-shift remaining water of a Li-ion dry-room AHU, not Al2O3 (r59), not chilled-mirror (r51), not MW-cavity moisture (r26), not THz-TDS (leftover-mill r21), not QCM-D (r14), not dielectric water-cut (r60).

Flagged gaps closed this round (from leftover-mill r58/r59/r21 and 2026-08-30 r04): (i) 48+ event streams vs the leftover-mill 5–40 thinning; (ii) a **load-bearing T/P table** on a1 so a lumped k_i without T under-reads 11.00 as 10.00; (iii) operational t2 on all three; (iv) serialized reconstruction on all three; (v) provenance trio designed/hil/simulated; (vi) all three safety enums on leads.

## Round 21 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r21-a1 | OA-ICOS remaining CH4 of a landfill-gas header (k_i·log2(I0/I)·(T/T0)·(P0/P) ppm, Icosveil last-good denial, 18 min carbon-filter floor) | Sedgewhin Landfill SW-5 header H-7 (invented): 5.00*log2(16.00/4.00)*(330.00/300.00) reconstructs 11.00 ppm while Icosveil still reads 1.80 ppm | REJECT (+0.43) / MODIFY (+0.34) | serialized T/P table is SoT; lumped-k without T would read 10.00; conjunctive SOP forbids continue-flare; three-party collusion includes the OA-ICOS-cloud infra owner; companion t2 carbon-filter hold, unit ESD refused; sim_or_real=designed |
| nelb-r21-a2 | SERF OPM remaining current of a potline bus (k_s·Δf kA, Magveil last-good denial, 24 min cooldown floor) | Brinecrag Smelter BC-4 bus B-2 (invented, HIL dummy in SERF-HIL-5): 0.040*500.00 reconstructs 20.00 kA while Magveil still reads 2.00 kA | MODIFY (+0.40) / ACCEPT (+0.35) | serialized `0.040*500.00=20.00` and `20.00*50.00=1000.00`; keep-bus refused; OPM tech Ryn Calder exonerated (missing laser-lock AE, UTC vs UTC+2); companion t2 new-head restart; sim_or_real=hil |
| nelb-r21-a3 | WGM remaining water of a Li-ion dry-room AHU (k_w·2**(Δν) ppmv, Wgmveil last-good denial, 12 min survey floor) | Lichenholt Cell LH-6 AHU-4 (invented, simulated WGM-SIM-3): 0.500*2**(4.00) reconstructs 8.00 ppmv while Wgmveil still reads 1.20 ppmv | ACCEPT (+0.41) / REJECT (+0.36) | serialized `0.500*2**(4.00)=8.00`; `32.00/8.00=4.00`; bounded ACCEPT of AHU-4 only; AHU-1..AHU-3 out of scope; companion t2 REJECTS skip-survey; sim_or_real=simulated |

Decision spread: REJECT / MODIFY / MODIFY / ACCEPT / ACCEPT / REJECT — **2A/2M/2R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r21-a1`…`a3` plus t1/t2 suffixes (not leftover-mill `064`…`066`).

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows 40/32/36 ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (40/40/36 at 50.0/50.0/62.5 Hz over 20/25/16 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (920/920/828 pJ). Routing source/target + 3-entry tables + `third_factor` on all three (modulators da.oai_ch4_conflict / ach.serf_laserlock_skip_salience / na.ahu_scope_eligibility; τe 1.6/1.2/2.0 s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons`. Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/MODIFY/ACCEPT matching each lead trajectory; every rate-declaring population's budget exact against its decision window. `gate_compute.per_check` windows 32–40 ms, budgets exact. Main streams: **52/52/52 events** (48+), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (a1 OA-ICOS pair at 1.4 ms, a2 SERF pair at 1.2 ms, a3 WGM pair at 1.5 ms).

## Self-critique

### Edge cases added vs still thin
- **Added:** first OA-ICOS remaining-CH4 family with a recomputable T/P table (`11.00 ppm` vs lumped-k `10.00`); first SERF OPM remaining-current family with recomputable I=k_s·Δf (`20.00 kA`) plus I·f identity and a resolved-innocent OPM tech; first WGM remaining-water family with recomputable x=k_w·2**(Δν) (`8.00 ppmv`) plus FSR identity; 52-event streams (leftover-mill r21 was 30); operational t2 on all three; provenance trio; 18/24/12 min slow floors in-stream.
- **Still thin:** (i) a1's P column is constant (P0/P=1.000) — a pressure hop that fakes 11.00 ppm inside a 1.80 Icosveil corridor is unwritten; (ii) a2 still has a plant-owned bus shunt; a booth whose shunt rides the colluding Magveil bus, so the gate must refuse with *only* laser-lock AE plus pass log, is harder (vendor-only lead REJECT remains open); (iii) a3's k_w is a lumped doubling-per-GHz factor, not a temperature / Q-degradation map; (iv) stream reconstruction amplitudes remain authored constants (raster draws are the only seeded noise); (v) no gate_snn input→output volley pair at raster resolution this round (2026-08-30 r04-a1 already staged that).

### Realism of noise / temporal fidelity
- Strong: a1's 11.00 ppm, OD 2.00, mdot 22.00, T/T0 1.100, and 18.0 min filter (`6000+1080=7080 s`) recompute from the record; a2's 20.00 kA, I·f 1000.00, and 24.0 min cooldown (`2820+1440=4260 s`) recompute; a3's 8.00 ppmv, FSR 4.00, and 12.0 min survey (`6000+720=6720 s`) recompute. Raster adaptation (0.82**k plus 4% noise) and the 1.2–1.5 ms physics pairs give the 52-event stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 10 Hz OA-ICOS / kHz SERF / kHz WGM are still thinned to 4 physics points plus table rows, even at 52 events; (ii) a1's post-stop 16.50 ppm is a later sample, not a closed-loop carbon-filter controller; (iii) a2 HIL coupon times an in-service isolate that the stream does not independently witness on a second live bus until the new head starts.

### Training value (SNN/LSM + agentic)
Distillation targets: OA-ICOS C=k_i·log2(I0/I)·(T/T0)·(P0/P) plus T/P-table SoT; conjunctive isolate floor vs continue-flare vs unit ESD; Icosveil-infra collusion; SERF I=k_s·Δf plus I·f identity; isolate-floor bus vs keep-whole vs shop-trip; laser-lock AE / timezone exoneration; WGM x=k_w·2**(Δν) and FSR identities; bounded ACCEPT with AHU-out-of-scope; skip-survey refusal under survey takt. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical CH4/current/water load the raw corridor cannot see (with a table that makes lumped-k fail), earned ACCEPT with an explicit physical out-of-scope object (AHU-1..AHU-3), and stop-then-hold so a REJECT does not become a train/shop/dump kill.

## What round 22 should add (next densification target)
1. **Pressure-hop row** on a non-SW-5 OA-ICOS so P0/P ≠ 1 fakes 11.00 ppm inside a 1.80 Icosveil corridor, closing a1's constant-P leftover.
2. **Vendor-bus shunt:** restage the a2 leftover where even the bus millivolt rides Magveil, so the only unwritable witnesses are laser-lock AE and the pass log (vendor-only lead REJECT).
3. **Temperature / Q-degradation map** on a non-LH-6 WGM so a thermal hop fakes 8.00 ppmv while mean Δν looks healthy.
4. **Do not restage** leftover-mill r21 THz-TDS / ECA FSW / LIBS C, OA-ICOS SW-5, SERF-HIL-5, WGM-SIM-3, UV-DOAS, Al2O3, load-cell, electrochemical H2S, TEV PD, dielectric water-cut, Stern-Volmer DO, pellistor, FMCW radar, laser-triangulation, ultrasonic-Doppler, gamma-backscatter, NDIR CO, Wobbe, venturi, katharometer, VOD-SNN, pharma cold-chain, or stack-gas CEMS. Do not reuse ids `nelb-r21-064`…`066` or leftover-mill `040`…`195`.

## Verification
`batch-r21.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False). Written create-only to the sf-window factory dir. Build-time asserts: global time order; same-channel ≥0.8 ms; 48+ events (52/52/52); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.43/+0.34/+0.40/+0.35/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=21`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp (`intended_use=research_only`, `linear_issue=RM-793`, `generated_at=2026-09-02T18:40:00Z`); no hidden-reasoning keys; no `provenance` objects; no live-plant claims; no `training_ready`; all 9 record/trajectory ids unique vs leftover-mill r21. Raster seeds 202609021/202609022/202609023, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory, versus leftover-mill r13–r64, and versus leftover-mill r21's THz-TDS/ECA/LIBS. The 52-event streams and the load-bearing T/P table are new density/physics objects relative to leftover-mill r21. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded-accept-with-scope-limit, vendor-nonsubstitution, exoneration, and 2A/2M/2R are carried vocabulary; 48+ is a density constraint the leftover mill did not harvest. Net: a bit under half of the round's scenario/edge mass is genuinely novel.

Novel coverage: 44%
"""


def choose_paths():
    FACTORY.mkdir(parents=True, exist_ok=True)
    batch = FACTORY / "batch-r21.jsonl"
    notes = FACTORY / "NOTES-r21.md"
    if batch.exists():
        batch = FACTORY / "batch-r21c.jsonl"
        notes = FACTORY / "NOTES-r21c.md"
        if batch.exists():
            raise SystemExit(f"refuse: {batch} already exists")
    return batch, notes


def main():
    recs = [rec_a1(), rec_a2(), rec_a3()]
    ids = []
    for rec in recs:
        hid = walk_hidden(rec)
        if hid:
            raise RuntimeError(f"hidden keys {hid}")
        if rec["gate_snn"]["decision"] != rec["language_view"]["trajectory"]["safety_decision"]["decision"]:
            raise RuntimeError("gate_snn decision mismatch")
        if rec["language_view"]["trajectory"]["state"]["sim_or_real"] not in {"designed", "simulated", "hil"}:
            raise RuntimeError("bad sim_or_real")
        ids.append(rec["id"])
        ids.append(rec["language_view"]["trajectory"]["id"])
        for k, v in rec["language_view"].items():
            if k not in {"description", "trajectory"} and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
        n = len(rec["spike_events"])
        if n < 48:
            raise RuntimeError(f"{rec['id']} has {n} events")
        r = rec["raster"]
        expected = int(round(r["neurons"] * r["mean_rate_hz"] * r["window_s"]))
        if abs(r["spikes"] - expected) > 1:
            raise RuntimeError("spike budget")
        if abs(r["energy_pJ"] - r["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy_pJ")
        if abs(r["energy_uJ"] - r["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy_uJ")
        if abs(r["window_s"] - r["window_ms"] / 1000.0) > 1e-9:
            raise RuntimeError("window mismatch")
        tf = r["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau mismatch")
        gs = rec["gate_snn"]
        dw_s = gs["decision_window_ms"] / 1000.0
        if abs(gs["decision_window_s"] - dw_s) > 1e-9:
            raise RuntimeError("gate window")
        for pop in gs["populations"]:
            if "mean_rate_hz" in pop:
                exp = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw_s))
                if abs(pop["spikes"] - exp) > 1:
                    raise RuntimeError(f"gate pop budget {pop['name']}")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(c["spikes"] for c in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if abs(gc["total_energy_pJ"] - gc["total_spikes"] * 23) > 1e-6:
            raise RuntimeError("gate_compute energy")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"duplicate ids {ids}")
    banned = {"nelb-r21-064", "nelb-r21-065", "nelb-r21-066"}
    if set(ids) & banned:
        raise RuntimeError("collides leftover-mill r21 ids")

    batch, notes = choose_paths()
    lines = [json.dumps(rec, ensure_ascii=False, separators=(",", ":"), allow_nan=False) for rec in recs]
    batch.write_text("\n".join(lines) + "\n")
    notes.write_text(NOTES)
    print(json.dumps({"batch": str(batch), "notes": str(notes), "n": len(lines), "ids": ids, "events": [len(r["spike_events"]) for r in recs]}))


if __name__ == "__main__":
    main()
