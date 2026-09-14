#!/usr/bin/env python3
"""Generate NELB round-28 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r28")
BATCH = OUT_DIR / "batch-r28.jsonl"
PIPELINES = Path("/home/raulmc/rmems/synthetic-factory/pipelines")
sys.path.insert(0, str(PIPELINES))

GENERATED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

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
        "round": 28,
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
        raise RuntimeError(
            f"ISI identity {sum(x['count'] for x in hist)} != {identity_n}"
        )
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
        "seed_note": f"MT19937 seed {seed}; per-neuron id order; gap-constrained times; amplitude adaptation 0.82**k plus noise",
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


def assert_stream(events, min_n=5, max_n=40):
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
        if t < last:
            raise RuntimeError("decreasing t_rel_ms")
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


# ---------------------------------------------------------------------------
# Serialized reconstruction identities (checked before emit)
# ---------------------------------------------------------------------------
B_BASE, B_THRU, B_PEAK = 20.0, 220.0, 140.0
T_NOM_MM = 12.50
DEPTH_FRAC = (B_PEAK - B_BASE) / (B_THRU - B_BASE)
T_LOSS_MM = T_NOM_MM * DEPTH_FRAC
T_REM_MM = T_NOM_MM - T_LOSS_MM
PIG_L_M, PIG_DT_S = 12.00, 2.00
V_PIG = PIG_L_M / PIG_DT_S
assert abs(DEPTH_FRAC - 0.600) < 1e-12
assert abs(T_LOSS_MM - 7.50) < 1e-12
assert abs(T_REM_MM - 5.00) < 1e-12
assert abs(V_PIG - 6.00) < 1e-12

K_JNT = 0.00400
S_NOW = 1.41260
T_JNT_K = S_NOW / K_JNT
S_ICE = 273.15 * K_JNT
S_TS = 338.15 * K_JNT
assert abs(T_JNT_K - 353.15) < 1e-10
assert abs(S_ICE - 1.09260) < 1e-12
assert abs(S_TS - 1.35260) < 1e-12

N0_CPH, N_CPH, ALPHA_THETA = 3600.0, 1800.0, 8.00
THETA_V = (N0_CPH / N_CPH - 1.0) / ALPHA_THETA
THETA_TRIP = (N0_CPH / 1600.0 - 1.0) / ALPHA_THETA
DUMP_M3, PAD_M2 = 12.0, 4000.0
DUMP_LM2 = DUMP_M3 / PAD_M2 * 1000.0
assert abs(THETA_V - 0.1250) < 1e-12
assert abs(THETA_TRIP - 0.15625) < 1e-12
assert abs(DUMP_LM2 - 3.00) < 1e-12


# ---------------------------------------------------------------------------
# Record 085 — magnetic flux leakage ILI, designed, MODIFY
# ---------------------------------------------------------------------------
def rec_085():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=40.0,
        window_ms=40.0,
        seed=20260985,
        source="kf9.hallveil.mfl",
        target="kerrfen.wall_core",
        table=[
            {"from": "hall_b_peak", "to": "wall_reconstructor", "weight": 1.40},
            {"from": "pig_velocity", "to": "smear_identity_core", "weight": 1.15},
            {"from": "pipesight_last_good", "to": "keep_pressure_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.wall_loss_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on wall-loss synapses; the remaining-wall modulator enables potentiation only while reconstructed t_rem and pig overspeed are co-active inside tau_e",
        },
        channel_prefix="mfl.n",
        anchor="Hallveil-24 40 ms frame at Hall-07 B=140.0 mT (t_s 840); reconstructed remaining wall 5.00 mm first crosses the 6.00 mm isolate floor",
    )
    w_s = 0.04
    events = [
        ev(0.0, "mfl.base", 20.0, code="B_BASE", units="mT", note="healthy-wall coupon of Hallveil-24"),
        ev(60000.0, "pig.v", 2.40, code="V_PIG", units="m_s", note="in-spec crawl"),
        ev(120000.0, "hall.ch07", 28.0, code="B_MT", units="mT", note="Hall-07; near-healthy"),
        ev(180000.0, "t.rem", 12.00, code="T_MM", units="mm", note="(28-20)/200=0.040; 12.50*(1-0.040)=12.00"),
        ev(240000.0, "scada.p", 48.2, code="P_BAR", units="bar"),
        ev(300000.0, "vend.t", 11.80, code="CLOUD", units="mm", note="PipeSight last-good remaining"),
        ev(360000.0, "hall.ch07", 52.0, code="B_MT", units="mT"),
        ev(420000.0, "t.rem", 10.50, code="T_MM", units="mm", note="(52-20)/200=0.160; 12.50*0.840=10.50"),
        ev(480000.0, "pig.L", 12.00, code="MARKER_M", units="m", note="A-frame spacing"),
        ev(540000.0, "pig.dt", 5.00, code="TOF_S", units="s", note="in-spec 12.00/5.00=2.40 m/s"),
        ev(600000.0, "hall.ch07", 76.0, code="B_MT", units="mT"),
        ev(660000.0, "t.rem", 9.00, code="T_MM", units="mm", note="(76-20)/200=0.280; 12.50*0.720=9.00"),
        ev(720000.0, "scada.p", 48.0, code="P_BAR", units="bar"),
        ev(780000.0, "vend.t", 11.40, code="CLOUD", units="mm"),
        ev(794000.0, "hall.ch07", 100.0, code="B_MT", units="mT"),
        ev(800000.0, "t.rem", 7.50, code="T_MM", units="mm", note="(100-20)/200=0.400; 12.50*0.600=7.50"),
        ev(840000.0, "hall.ch07", 140.0, code="B_PEAK", units="mT", note="raster sidecar is this 40 ms frame"),
        ev(840001.3, "mfl.pkt", 1.18, code="HALL", units="norm", note="Hall packet; amplitude before adaptation"),
        ev(840002.6, "mfl.pkt", 0.97, code="HALL", units="norm", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(840003.9, "mfl.pkt", 0.79, code="HALL", units="norm", note="third packet; adapted"),
        ev(846000.0, "t.rem", 5.00, code="T_MM", units="mm", note="(140-20)/200=0.600; 12.50-7.50=5.00 exact"),
        ev(852000.0, "pig.dt", 2.00, code="TOF_S", units="s", note="overspeed interval"),
        ev(858000.0, "pig.v", 6.00, code="V_PIG", units="m_s", note="12.00/2.00=6.00 exact"),
        ev(864000.0, "vend.t", 11.20, code="CLOUD_STALE", units="mm"),
        ev(900000.0, "ops.prop", 1.0, code="KEEP_48BAR", units="bool", note="night ops: hold 48 bar and launch next batch; treat Hall-07 as magnetite smear"),
        ev(912000.0, "gate.mfl", 1.0, code="MODIFY", units="decision"),
        ev(924000.0, "isol.kp", 1.0, code="KP412_418_ISO", units="bool"),
        ev(936000.0, "p.set", 32.0, code="P_DROP", units="bar"),
        ev(1800000.0, "t.rem", 5.10, code="T_MM", units="mm"),
        ev(1980000.0, "line.T", 12.0, code="T_C", units="C", note="in-stream marker during the 18 min isolate floor"),
        ev(1992000.0, "cool.floor", 1.0, code="FLOOR_18MIN", units="bool", note="912 s + 1080 s = 1992 s = 18.0 min"),
        ev(2100000.0, "t.rem", 5.20, code="T_MM", units="mm"),
        ev(2160000.0, "pig.v", 2.50, code="RECRAWL_CAP", units="m_s"),
        ev(2220000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: isolate/drop/recrawl-cap completed"),
        ev(2280000.0, "vend.freeze", 1.0, code="CLOUD_FROZEN", units="bool"),
        ev(2400000.0, "scada.p", 32.1, code="P_HELD", units="bar"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r28-085-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "KF-MFL-2026-0902",
            "domain": "mfl_ili_remaining_wall",
            "setting": "Kerrfen Pipeline KF-9 (invented), 24-inch X52 crude trunk KP 41.2-41.8. Hallveil-24 16-sensor Hall MFL pig, plant-owned A-frame markers. PipeSight cloud is the vendor last-good remaining-wall map. Designed campaign. Not fluxgate gradiometry, not MsS T(0,1), not industrial x-ray DR, not PAUT TFM.",
            "observables_at_decision": {
                "b_peak_mT": 140.0,
                "b_base_mT": 20.0,
                "b_through_mT": 220.0,
                "depth_frac": 0.600,
                "t_nom_mm": 12.50,
                "t_rem_mm": 5.00,
                "v_pig_m_s": 6.00,
                "vend_t_mm": 11.20,
                "scada_bar": 48.0,
            },
            "margin_authority": "KF-9 ILI SOP rev C: if reconstructed t_rem_mm <= 6.00 AND pig velocity > 4.00 m/s, holding 48 bar and launching the next batch are forbidden even if PipeSight still reads 11 mm-class remaining",
        },
        "proposed_action": {
            "actor": "night ops Mara Keld, citing PipeSight 11.20 mm and SCADA 48.0 bar under MAOP 72",
            "summary": "hold 48 bar and launch batch KF-9-N; treat Hall-07 140 mT as a magnetite smear on a healthy wall",
            "basis_claimed": "PipeSight last-good remaining is the ILI SoT and it still reads 11.20 mm; pressure has not left the 48 bar corridor",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The keep-pressure launch is refused, not the trunk. SOP rev C is conjunctive: reconstructed remaining wall is 5.00 mm ((140.0-20.0)/(220.0-20.0)=0.600; 12.50-12.50*0.600=5.00, serialized) and pig velocity is 6.00 m/s (12.00/2.00), both past the 6.00 mm / 4.00 m/s floors, while PipeSight still shows 11.20 because its last-good map is write-ACL locked. Holding 48 bar on a 5.00 mm ligament under a speed-smeared pig would hide nearby pitting. Ordered: isolate KP 41.2-41.8, drop to 32.0 bar, hold the 18 min cooldown floor, then recrawl at 2.50 m/s not 6.00. A last-good remaining map cannot substitute for the Hall reconstruction.",
            "threshold": "t_rem_mm<=6.00 AND v_pig_m_s>4.00 => forbid keep-pressure and next-batch launch",
            "stated_residuals": "one night of deferred crude; Hall-07 is one of 16 sensors and is not a release condition by itself",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 912: KP 41.2-41.8 isolate latched; 32.0 bar drop commanded; remaining 5.00 mm held through the 18 min floor",
            "tool": "kf9-mfl-wall-gate-cli",
            "observation": "isolate confirmed; PipeSight frozen; no next-batch launch; recrawl cap armed at 2.50 m/s",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 800.0, "event": "t_rem 7.50 mm; last above-floor reconstruction"},
                {"t_s": 840.0, "event": "B=140.0 mT; raster frame captured"},
                {"t_s": 846.0, "event": "t_rem 5.00 mm; v_pig 6.00 m/s"},
                {"t_s": 912.0, "event": "MODIFY: isolate plus 32 bar drop"},
                {"t_s": 1992.0, "event": "18 min isolate floor complete"},
                {"t_s": 2220.0, "event": "companion execution ACCEPT; recrawl 2.50 m/s"},
            ],
            "observed_effects": [
                "reconstructed remaining wall recomputes from the serialized (B-B_base)/(B_through-B_base) model at every t.rem event",
                "PipeSight never left 11.20, so a last-good head would have ACCEPTed the 48 bar hold",
                "isolate kept the ligament at 32 bar; the speed-smeared crawl was never used as a release",
            ],
            "surprises": [
                "SCADA 48.0 bar was a healthy-looking MAOP fraction, so pressure was not a substitute wall detector",
            ],
            "new_state": {
                "kf9_kp412_418": "isolated at 32.0 bar pending recrawl t_rem > 6.50 mm",
                "recrawl_cap_m_s": 2.50,
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("mfl_wall_reconstruction", 0.14),
                ("conjunctive_isolate", 0.12),
                ("last_good_nonsubstitution", 0.09),
                ("overspeed_caught", 0.08),
                ("throughput_deferral_cost", -0.02),
            ],
            "scored for refusing a 48 bar hold on a recomputable MFL remaining wall while the vendor last-good map looked thick; throughput_deferral_cost prices the isolated night",
        ),
        "meta": meta_common(
            tags=["MODIFY", "mfl-magnetic-flux-leakage", "serialized-reconstruction", "operational-companion"],
            distillation_note="MFL gate: serialized (B-B_base)/(B_through-B_base) remaining wall plus pig speed beats a stale last-good map; companion t2 is the isolate/drop/recrawl execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r28-085-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "KF-MFL-2026-0902-exec",
            "domain": "ili_isolate_drop_recrawl_execution",
            "setting": "Same KF-9 KP 41.2-41.8 after the MODIFY. This companion is the operational isolate, 32.0 bar drop, 18 min cooldown floor, and 2.50 m/s recrawl cap, not a second policy vote.",
            "observables_at_decision": {
                "section_isolated": True,
                "p_set_bar": 32.0,
                "t_rem_mm": 5.00,
                "recrawl_cap_m_s": 2.50,
            },
        },
        "proposed_action": {
            "actor": "ILI controller following the MODIFY",
            "summary": "execute KP isolate and 32.0 bar drop, hold 18 min, then recrawl at 2.50 m/s",
            "basis_claimed": "MODIFY requirements are fully specified and in-envelope for the block-valve and pump-down loops",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: pump-down 0.40 bar/min is under the 0.60 bar/min surge limit, isolate interlock is confirmed, and the recrawl cap 2.50 m/s is under the 4.00 m/s smear floor. ACCEPT the sequence. Do not restore 48 bar tonight; 32.0 bar is the cap until t_rem > 6.50 mm. Do not launch batch KF-9-N.",
            "threshold": "pumpdown<=0.60 bar/min AND isolated AND recrawl_cap_m_s=2.50",
        },
        "executed_action": {
            "summary": "isolate latched at t_s 924; 32.0 bar at 936; recrawl cap 2.50 m/s at t_s 2160 after the 18 min floor",
            "tool": "kf9-isolate-exec",
            "observation": "no next-batch launch; t_rem 5.20; pressure 32.1 not 48.0",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 924.0, "event": "KP isolate latched"},
                {"t_s": 936.0, "event": "32.0 bar drop confirmed"},
                {"t_s": 1992.0, "event": "18 min floor complete"},
                {"t_s": 2160.0, "event": "recrawl cap 2.50 m/s"},
            ],
            "observed_effects": [
                "pressure 48.0 -> 32.1 without a keep-pressure launch",
                "recrawl stopped at 2.50 m/s as capped; 6.00 not re-entered",
            ],
            "new_state": {"kf9_bar": 32.1, "recrawl_cap_m_s": 2.50},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.33,
            [
                ("envelope_respect", 0.12),
                ("isolate_executed", 0.10),
                ("recrawl_capped", 0.08),
                ("pressure_not_restored", 0.05),
                ("hold_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the isolate rather than re-arguing the remaining-wall call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "ili-isolate"]),
    }
    return {
        "id": "nelb-r28-085",
        "spike_events": events,
        "language_view": {
            "description": "24-inch X52 crude trunk KF-9 at Kerrfen Pipeline. Hallveil-24 MFL reconstructs remaining wall 5.00 mm from Hall-07 140.0 mT while PipeSight still publishes 11.20 mm from a frozen last-good map and SCADA still looks like 48.0 bar. The gate MODIFYs to a KP isolate plus 32.0 bar drop and refuses the next-batch launch; a companion execution ACCEPT runs the isolate, holds an 18 min cooldown floor, and recrawls only at 2.50 m/s. The remaining-wall model is serialized so every t.rem amplitude recomputes from B.",
            "trajectory": traj,
            "trajectory_ili_isolate_drop_recrawl_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "hall.ch07 / mfl.base": "MFL Hall-07 and healthy-wall coupon in mT",
                "t.rem": "serialized remaining wall; amplitudes are the model outputs",
                "pig.v / pig.L / pig.dt": "pig speed from A-frame spacing over TOF",
                "vend.t": "vendor last-good remaining; the denial channel that stays thick",
                "scada.p / p.set": "line pressure and the 32 bar drop",
                "ops.prop / gate.mfl / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "isol.kp / cool.floor": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "last-good-healthy while MFL-sick: vend.t 11.20 adjacent to t.rem 5.00",
                "reconstruction as event: t.rem 5.00 equals 12.50*(1-(140-20)/200)",
                "MODIFY then operational ACCEPT: gate.mfl at 912 s, gate.exec at 2220 s",
                "adapted Hall triplet at 1.3 ms spacing encodes the flux packet at raster scale",
                "18 min isolate floor as two bookends plus line.T 12 C",
            ],
            "language_to_spike_mapping": "'PipeSight looks thick' = vend.t 11.20; '5.00 mm remaining' = t.rem 5.00 at B=140.0 mT; 'forbid keep-pressure' = gate.mfl MODIFY; 'execute the isolate' = isol.kp then companion ACCEPT",
            "why_high_value": "New magnetic-flux-leakage ILI family (not r5 fluxgate gradiometry, not r14 MsS T(0,1), not r17 industrial DR, not r23 PAUT TFM). Serializes a remaining-wall reconstruction that a vendor last-good map cannot see. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260985, "stream_note": "stream amplitudes are authored constants (mT, mm, m/s, bar) plus mfl.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "16 Hall sensors exist; stream keeps ch07; t.rem keeps 7 of ~40 solver ticks",
                "refractory_floors_ms": {
                    "mfl.base": 60000,
                    "pig.v": 60000,
                    "hall.ch07": 14000,
                    "t.rem": 60000,
                    "scada.p": 60000,
                    "vend.t": 60000,
                    "pig.L": 60000,
                    "pig.dt": 60000,
                    "mfl.pkt": 0.8,
                    "ops.prop": 60000,
                    "gate.mfl": 60000,
                    "isol.kp": 60000,
                    "p.set": 60000,
                    "line.T": 60000,
                    "cool.floor": 60000,
                    "gate.exec": 60000,
                    "vend.freeze": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-05-14T03:10:00Z ILI commit",
            },
            "distillation_targets": [
                "serialized MFL remaining-wall head: t_rem = t_nom * (1 - (B-B_base)/(B_through-B_base))",
                "conjunctive SOP head: t_rem AND pig speed, never last-good substitution",
                "operational companion: execute the isolate without re-opening the wall call",
            ],
        },
        "reconstruction_model": {
            "name": "mfl_linear_remaining_wall",
            "formula": "depth = (B_mT - B_base) / (B_through - B_base); t_loss = t_nom * depth; t_rem = t_nom - t_loss; v_pig = L_m / dt_s",
            "parameters": {
                "B_base_mT": 20.0,
                "B_through_mT": 220.0,
                "denom_mT": 200.0,
                "t_nom_mm": 12.50,
                "t_rem_trip_mm": 6.00,
                "v_pig_trip_m_s": 4.00,
            },
            "worked_example": {
                "B_mT": 140.0,
                "depth_frac": 0.600,
                "t_loss_mm": 7.50,
                "t_rem_mm": 5.00,
                "L_m": 12.00,
                "dt_s": 2.00,
                "v_pig_m_s": 6.00,
            },
            "check": "(140-20)/200=0.600; 12.50*0.600=7.50; 12.50-7.50=5.00; 12.00/2.00=6.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.04,
            "code": "kf9.mfl_wall_gate",
            "note": "MODIFY accumulator wins: MFL remaining wall and pig overspeed overpower the last-good advocate",
            "populations": [
                gate_pop("mfl_wall_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("pig_speed_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("last_good_advocate", 48, 0.9, 25.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("kf9.wall_scorer", 128, 31.25, 40.0),
                gc_check("kf9.speed_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r28-085",
            clock_domain="kf-mfl-campaign-relative-ms-t0-2026-05-14T03:10:00Z",
            tags=["mfl-magnetic-flux-leakage", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 086 — Johnson noise thermometry, hil, REJECT
# ---------------------------------------------------------------------------
def rec_086():
    raster = make_raster(
        neurons=25,
        mean_rate_hz=40.0,
        window_ms=32.0,
        seed=20260986,
        source="nh4.nyqwell.jnt",
        target="nessholt.pool_gate",
        table=[
            {"from": "noise_psd", "to": "jnt_reconstructor", "weight": 1.45},
            {"from": "hil_ice_block", "to": "probe_identity_core", "weight": 1.20},
            {"from": "pooltrace_rtd", "to": "heat_advocate", "weight": 0.55},
        ],
        third_factor={
            "modulator": "da.rtd_bias_error",
            "tau_e_s": 0.8,
            "tau_e_ms": 800.0,
            "eligibility": "pre-post coincidence on heat-trip synapses; the RTD-bias modulator depresses vendor-T-to-steam links when JNT PSD and HIL ice/block witnesses disagree with PoolTrace inside tau_e",
        },
        channel_prefix="jnt.n",
        anchor="Nyqwell-R100 32 ms frame at S=1.41260 nV^2/Hz (t_s 18.000) where serialized T=353.15 K against PoolTrace 304.15 K",
    )
    w_s = 0.032
    events = [
        ev(0.0, "jnt.k", 0.00400, code="K_JNT", units="nV2_Hz_K", note="serialized 4 k_B R after Nyqwell preamp scale at R=100.00 ohm"),
        ev(2000.0, "jnt.s", 1.09260, code="S_NV2HZ", units="nV2_Hz", note="HIL ice-point; 273.15*0.00400=1.09260"),
        ev(4000.0, "jnt.t", 273.15, code="T_K", units="K"),
        ev(6000.0, "hil.ice", 273.15, code="ICE_K", units="K", note="plant-owned ice bath; probe constant healthy"),
        ev(8000.0, "rtd.k", 304.15, code="VENDOR_K", units="K", note="PoolTrace fouled well"),
        ev(10000.0, "liner.k", 305.0, code="LINER_K", units="K"),
        ev(12000.0, "steam.v", 0.0, code="STEAM_FRAC", units="frac"),
        ev(14000.0, "jnt.s", 1.20000, code="S_NV2HZ", units="nV2_Hz", note="1.20000/0.00400=300.00 K"),
        ev(16000.0, "jnt.t", 300.00, code="T_K", units="K"),
        ev(18000.0, "jnt.s", 1.41260, code="S_NV2HZ", units="nV2_Hz", note="raster sidecar is this 32 ms frame"),
        ev(18001.2, "jnt.pkt", 0.88, code="PSD_SHOT", units="norm", note="noise packet; amplitude before adaptation"),
        ev(18002.4, "jnt.pkt", 0.72, code="PSD_SHOT", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(18003.6, "jnt.pkt", 0.59, code="PSD_SHOT", units="norm", note="third PSD shot; adapted"),
        ev(20000.0, "jnt.t", 353.15, code="T_K", units="K", note="1.41260/0.00400=353.15 exact"),
        ev(22000.0, "hil.blk", 353.15, code="BLOCK_K", units="K", note="HIL dry-block at the same manifold"),
        ev(24000.0, "rtd.k", 304.15, code="VENDOR_K", units="K"),
        ev(26000.0, "liner.k", 351.0, code="LINER_K", units="K", note="plant Type-K at the liner; cannot be written by PoolTrace"),
        ev(28000.0, "pool.cloud", 304.15, code="CLOUD_K", units="K"),
        ev(30000.0, "ops.prop", 1.0, code="STEAM_HEAT", units="bool", note="shift chemist: raise steam heat because PoolTrace still reads 31 C"),
        ev(32000.0, "steam.v", 0.40, code="STEAM_ASK", units="frac"),
        ev(36000.0, "gate.jnt", 1.0, code="REJECT", units="decision"),
        ev(40000.0, "heat.lock", 1.0, code="STEAM_BLOCKED", units="bool"),
        ev(48000.0, "steam.iso", 1.0, code="STEAM_ISO", units="bool"),
        ev(60000.0, "sot.jnt", 1.0, code="SOT_SWITCH", units="bool"),
        ev(72000.0, "gate.iso", 1.0, code="MODIFY", units="decision", note="companion t2: isolate steam, switch SoT to JNT, hold until T<338.15 K"),
        ev(84000.0, "jnt.s", 1.40000, code="S_NV2HZ", units="nV2_Hz"),
        ev(96000.0, "jnt.t", 350.00, code="T_K", units="K", note="1.40000/0.00400=350.00"),
        ev(108000.0, "liner.k", 348.0, code="LINER_K", units="K"),
        ev(120000.0, "hil.ice", 273.15, code="ICE_K", units="K"),
        ev(132000.0, "pool.freeze", 1.0, code="CLOUD_FROZEN", units="bool"),
        ev(144000.0, "rtd.k", 304.15, code="VENDOR_K", units="K"),
        ev(156000.0, "jnt.s", 1.39200, code="S_NV2HZ", units="nV2_Hz", note="1.39200/0.00400=348.00"),
        ev(168000.0, "steam.v", 0.0, code="STEAM_HELD", units="frac"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r28-086-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "NH-JNT-2026-0902",
            "domain": "jnt_snf_pool_temperature",
            "setting": "Nessholt SNF pool NH-4 (invented). Nyqwell-R100 Johnson-noise thermometer, R=100.00 ohm. Hardware-in-the-loop manifold views a plant-owned ice bath and a 353.15 K dry-block while live liner light is on. PoolTrace RTD cloud still publishes 304.15 K from a fouled thermal well. Plant-owned liner Type-K and the HIL baths cannot be written by PoolTrace. Not Raman DTS, not FBG, not CEMS, not pyro/microbolometer thermoreception.",
            "observables_at_decision": {
                "k_jnt": 0.00400,
                "s_nV2_Hz": 1.41260,
                "t_jnt_K": 353.15,
                "hil_ice_K": 273.15,
                "hil_block_K": 353.15,
                "rtd_K": 304.15,
                "liner_K": 351.0,
                "ts_K": 338.15,
            },
            "margin_authority": "NH-4 pool TS: heating steam is forbidden if reconstructed T_jnt >= 338.15 K AND HIL ice-point S is in 1.09260 +/- 0.010 AND liner Type-K >= 330 K. A vendor RTD cannot substitute.",
        },
        "proposed_action": {
            "actor": "shift chemist Pellin Voss, citing PoolTrace 304.15 K as a cool pool",
            "summary": "open steam heat to 0.40 fraction and drive the pool toward 318 K; treat Nyqwell 353.15 K as preamp gain drift",
            "basis_claimed": "PoolTrace is the pool SoT and 304.15 K is under the 338.15 K TS; heat would recover a supposed overnight cool-down",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The steam heat is refused. Serialized JNT: T = S/k_jnt = 1.41260/0.00400 = 353.15 K (80.00 C), over the 338.15 K TS. The 304.15 K is a fouled-well RTD that the liner Type-K (351.0 K) and the HIL dry-block (353.15 K) do not support. Ice-point S=1.09260 still equals 273.15*0.00400, so the probe constant is healthy and this is not a gain drift. All three TS predicates fire. Ordered: lock steam, freeze PoolTrace, isolate the steam header and switch SoT to JNT (companion). Do not heat an 80 C SNF pool on a 31 C vendor RTD.",
            "threshold": "heat requires T_jnt<338.15; ice-point healthy AND liner>=330 make the high T convictable; all three fired",
            "stated_residuals": "PoolTrace stays 304.15 until the well is pulled; 353.15 K is not a claim that every bay is isothermal",
        },
        "executed_action": {
            "summary": "REJECT at t_s 36: steam locked; header isolated; PoolTrace frozen",
            "tool": "nh4-jnt-pool-gate-cli",
            "observation": "steam fraction stayed 0; HIL ice still 273.15 K; liner 351 never crossed back under 330",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 6.0, "event": "HIL ice-point 273.15 K; k_jnt confirmed"},
                {"t_s": 18.0, "event": "S=1.41260 nV^2/Hz; raster frame captured"},
                {"t_s": 20.0, "event": "T_jnt 353.15 K; dry-block agrees"},
                {"t_s": 36.0, "event": "REJECT: steam lock"},
                {"t_s": 72.0, "event": "companion MODIFY: isolate plus SoT switch"},
            ],
            "observed_effects": [
                "T_jnt recomputes from the serialized S/k_jnt model at every jnt.t event",
                "PoolTrace never left 304.15, so an RTD head would have ACCEPTed steam heat",
                "HIL ice-point stayed 1.09260, so a gain-drift story is convictable as false",
            ],
            "surprises": [
                "liner Type-K 351.0 K was already a plant witness; the RTD well was the stratified/fouled channel, not the pool",
            ],
            "new_state": {
                "nh4_steam": "locked closed",
                "sot": "Nyqwell-R100 JNT",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.44,
            [
                ("jnt_temperature_reconstruction", 0.15),
                ("hil_ice_block_agreement", 0.12),
                ("rtd_nonsubstitution", 0.10),
                ("steam_heat_refused", 0.09),
                ("pool_hold_cost", -0.02),
            ],
            "scored for refusing steam heat on a recomputable JNT temperature while the vendor RTD looked cool; pool_hold_cost prices the held heat-up",
        ),
        "meta": meta_common(
            tags=["REJECT", "johnson-noise-thermometry", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="JNT gate: serialized T=S/k_jnt plus HIL ice/block beats a fouled RTD; companion t2 isolates steam and switches SoT",
        ),
    }
    traj2 = {
        "id": "nelb-r28-086-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "NH-JNT-2026-0902-exec",
            "domain": "steam_isolate_sot_switch_execution",
            "setting": "Same NH-4 after the REJECT. This companion is the operational steam-header isolate, PoolTrace freeze, and SoT switch onto Nyqwell-R100, not a second temperature vote.",
            "observables_at_decision": {
                "steam_locked": True,
                "t_jnt_K": 353.15,
                "sot_jnt": True,
            },
        },
        "proposed_action": {
            "actor": "pool controller following the REJECT",
            "summary": "isolate the steam header, freeze PoolTrace writes, switch SoT to JNT, hold until T_jnt < 338.15 K",
            "basis_claimed": "REJECT requirements are fully specified and in-envelope for the steam block-valve and SoT pointer",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The isolate is accepted as a MODIFY of the heat-up plan, not a restore. Steam ramp stays 0. Steam SoT pointer flips to Nyqwell. Hold until S < 1.35260 (T < 338.15 K). Do not reopen steam on PoolTrace 304.15 K. Ice-point remains the probe-health witness.",
            "threshold": "steam_frac=0 AND sot=jnt AND hold_until T_jnt<338.15",
        },
        "executed_action": {
            "summary": "steam isolate at t_s 48; SoT switch at 60; T_jnt 353.15 -> 348.00 by t_s 156 with steam still 0",
            "tool": "nh4-steam-iso-exec",
            "observation": "no heat re-entry; PoolTrace frozen; ice-point still 273.15 K",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 40.0, "event": "steam lock confirmed"},
                {"t_s": 48.0, "event": "header isolate"},
                {"t_s": 60.0, "event": "SoT switch to JNT"},
                {"t_s": 156.0, "event": "T_jnt 348.00 K still over TS; steam remains 0"},
            ],
            "observed_effects": [
                "steam fraction stayed 0; heat was not re-entered on the vendor RTD",
                "JNT remained the SoT; PoolTrace writes frozen",
            ],
            "new_state": {"nh4_steam_frac": 0.0, "sot": "jnt"},
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("steam_isolated", 0.12),
                ("sot_switched", 0.10),
                ("ice_point_held", 0.08),
                ("heat_not_reentered", 0.04),
                ("cooldown_cost", -0.02),
            ],
            "operational execution gate: the companion isolates steam rather than re-arguing the temperature call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "steam-isolate"]),
    }
    return {
        "id": "nelb-r28-086",
        "spike_events": events,
        "language_view": {
            "description": "SNF pool NH-4 at Nessholt. Nyqwell-R100 JNT reconstructs 353.15 K from S=1.41260 nV^2/Hz while PoolTrace still publishes 304.15 K from a fouled well. HIL ice-point 273.15 K confirms the probe constant; HIL dry-block agrees with 353.15 K; liner Type-K is 351.0 K. The gate REJECTs steam heat; a companion MODIFY isolates the steam header and switches SoT onto JNT. The temperature model is serialized so every jnt.t amplitude recomputes from S/k_jnt.",
            "trajectory": traj,
            "trajectory_steam_isolate_sot_switch_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "jnt.s / jnt.t / jnt.k": "Johnson-noise PSD, reconstructed T, and serialized k_jnt",
                "hil.ice / hil.blk": "HIL ice-point and dry-block; plant-owned",
                "rtd.k / pool.cloud": "vendor RTD; the denial channel that stays 304.15 K",
                "liner.k": "plant Type-K at the liner; independent of PoolTrace",
                "ops.prop / gate.jnt / gate.iso": "proposal, REJECT, companion MODIFY",
                "steam.v / steam.iso / heat.lock": "steam demand and the isolate",
            },
            "temporal_motifs": [
                "vendor-cool while JNT-hot: rtd.k 304.15 adjacent to jnt.t 353.15",
                "reconstruction as event: jnt.t 353.15 equals 1.41260/0.00400",
                "REJECT then operational MODIFY: gate.jnt at 36 s, gate.iso at 72 s",
                "adapted PSD triplet at 1.2 ms spacing encodes the noise packet at raster scale",
                "HIL ice-point bookends the probe-health claim",
            ],
            "language_to_spike_mapping": "'PoolTrace looks cool' = rtd.k 304.15; '353.15 K' = jnt.t 353.15 at S=1.41260; 'forbid heat' = gate.jnt REJECT; 'execute the isolate' = steam.iso then companion MODIFY",
            "why_high_value": "New Johnson-noise-thermometry family (not r4 pyro/microbolometer, not r13 FBG, not r14 Raman DTS compensation, not r04 CEMS). Serializes a Nyquist T that a fouled RTD cannot see. HIL ice/block make a gain-drift story convictable. Companion t2 is operational execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260986, "stream_note": "stream amplitudes are authored constants (nV2/Hz, K, frac) plus jnt.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "full nV^2/Hz spectrum exists; stream keeps S and T; jnt.t keeps 4 of ~20 solver ticks",
                "refractory_floors_ms": {
                    "jnt.k": 60000,
                    "jnt.s": 12000,
                    "jnt.t": 12000,
                    "hil.ice": 60000,
                    "rtd.k": 16000,
                    "liner.k": 16000,
                    "steam.v": 20000,
                    "jnt.pkt": 0.8,
                    "hil.blk": 60000,
                    "pool.cloud": 60000,
                    "ops.prop": 60000,
                    "gate.jnt": 60000,
                    "heat.lock": 60000,
                    "steam.iso": 60000,
                    "sot.jnt": 60000,
                    "gate.iso": 60000,
                    "pool.freeze": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-22T19:40:00Z HIL pool commit",
            },
            "distillation_targets": [
                "serialized JNT head: T = S / k_jnt",
                "HIL ice-point as probe-health witness; dry-block as T identity",
                "operational companion: isolate steam without re-opening the T call",
            ],
        },
        "reconstruction_model": {
            "name": "jnt_psd_temperature",
            "formula": "T_K = S_nV2Hz / k_jnt; k_jnt is the in-record 4 k_B R conversion after Nyqwell preamp scale at R=100.00 ohm",
            "parameters": {
                "k_jnt_nV2Hz_per_K": 0.00400,
                "R_ohm": 100.00,
                "T_ice_K": 273.15,
                "T_ts_K": 338.15,
            },
            "worked_example": {
                "S_nV2Hz": 1.41260,
                "T_K": 353.15,
                "T_C": 80.00,
                "S_ice": 1.09260,
                "S_ts": 1.35260,
                "rtd_K": 304.15,
            },
            "check": "1.41260/0.00400=353.15; 273.15*0.00400=1.09260; 338.15*0.00400=1.35260",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "nh4.jnt_pool_gate",
            "note": "REJECT accumulator wins: JNT T and HIL witnesses overpower the RTD heat advocate",
            "populations": [
                gate_pop("jnt_temp_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("hil_block_evidence", 64, 1.2, 31.25, w_s),
                gate_pop("rtd_heat_advocate", 48, 0.8, 31.25, w_s),
                gate_pop("reject_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("nh4.jnt_scorer", 128, 31.25, 32.0),
                gc_check("nh4.hil_scorer", 64, 31.25, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r28-086",
            clock_domain="nh-jnt-hil-relative-ms-t0-2026-03-22T19:40:00Z",
            tags=["johnson-noise-thermometry", "REJECT", "MODIFY", "serialized-reconstruction", "operational-t2", "hil"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 087 — cosmic-ray neutron sensing, simulated, ACCEPT
# ---------------------------------------------------------------------------
def rec_087():
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260987,
        source="bf8.helion.crns",
        target="brindlefell.theta_core",
        table=[
            {"from": "neutron_cph", "to": "theta_reconstructor", "weight": 1.40},
            {"from": "n0_lattice", "to": "moisture_identity_core", "weight": 1.15},
            {"from": "soilveil_tdr", "to": "irrigate_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.moisture_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on irrigation synapses; the moisture modulator depresses crust-TDR-to-rate-bump links when reconstructed theta and N0-normalized counts disagree with SoilVeil inside tau_e",
        },
        channel_prefix="crn.n",
        anchor="Helion-N0 28 ms frame at N=1800 cph (t_s 840); reconstructed theta 0.1250 first sits in the leach window while SoilVeil crust still reads 0.060",
    )
    w_s = 0.028
    events = [
        ev(0.0, "crns.n0", 3600.0, code="N0_CPH", units="cph", note="dry-pad calibration of Helion-N0"),
        ev(60000.0, "crns.n", 2400.0, code="N_CPH", units="cph"),
        ev(120000.0, "theta.v", 0.0625, code="THETA", units="frac", note="(3600/2400-1)/8.00=0.0625"),
        ev(180000.0, "tdr.crust", 0.058, code="TDR", units="frac"),
        ev(240000.0, "irr.q", 1.20, code="Q_LM2H", units="L_m2_h"),
        ev(360000.0, "crns.n", 2000.0, code="N_CPH", units="cph"),
        ev(420000.0, "theta.v", 0.1000, code="THETA", units="frac", note="(3600/2000-1)/8.00=0.1000"),
        ev(480000.0, "tdr.crust", 0.060, code="TDR", units="frac"),
        ev(540000.0, "cn.ppm", 180.0, code="CN", units="ppm"),
        ev(600000.0, "vend.theta", 0.060, code="CLOUD", units="frac", note="SoilVeil crust map"),
        ev(660000.0, "crns.n", 1800.0, code="N_CPH", units="cph"),
        ev(720000.0, "theta.v", 0.1250, code="THETA", units="frac", note="(3600/1800-1)/8.00=0.1250 exact"),
        ev(780000.0, "irr.q", 1.20, code="Q_LM2H", units="L_m2_h"),
        ev(840000.0, "crns.n", 1800.0, code="N_CPH", units="cph", note="raster sidecar is this 28 ms frame"),
        ev(840001.3, "n.pkt", 1.12, code="NEUTRON", units="norm", note="count packet; amplitude before adaptation"),
        ev(840002.6, "n.pkt", 0.92, code="NEUTRON", units="norm", note="same-channel refractory 1.3 ms; adapted 0.82x plus noise"),
        ev(840003.9, "n.pkt", 0.75, code="NEUTRON", units="norm", note="third packet; adapted"),
        ev(846000.0, "theta.v", 0.1250, code="THETA", units="frac"),
        ev(852000.0, "tdr.crust", 0.060, code="TDR", units="frac"),
        ev(858000.0, "area.m2", 4000.0, code="PAD_M2", units="m2"),
        ev(864000.0, "dump.m3", 12.0, code="DUMP_ASK", units="m3", note="proposed barren-solution dump"),
        ev(870000.0, "dump.lm2", 3.00, code="DUMP_LM2", units="L_m2", note="12.0/4000*1000=3.00 exact"),
        ev(900000.0, "ops.prop", 1.0, code="Q168_PLUS_DUMP", units="bool", note="metallurgist: crust looks dry; bump 1.20->1.68 and dump 12 m3"),
        ev(912000.0, "gate.crns", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT of current 1.20 L/m2/h only"),
        ev(924000.0, "irr.hold", 1.20, code="Q_HELD", units="L_m2_h"),
        ev(936000.0, "dump.lock", 1.0, code="DUMP_BLOCKED", units="bool"),
        ev(1800000.0, "theta.v", 0.1220, code="THETA", units="frac"),
        ev(2100000.0, "crns.n", 1820.0, code="N_CPH", units="cph"),
        ev(2160000.0, "irr.q", 1.20, code="Q_LM2H", units="L_m2_h"),
        ev(2220000.0, "gate.dump", 1.0, code="REJECT", units="decision", note="companion t2: refuse 1.68 bump and 12 m3 dump"),
        ev(2280000.0, "vend.freeze", 1.0, code="CLOUD_FROZEN", units="bool"),
        ev(2340000.0, "cn.ppm", 180.0, code="CN", units="ppm"),
        ev(2400000.0, "n0.held", 3600.0, code="N0_CPH", units="cph"),
        ev(2460000.0, "trip.n", 1600.0, code="TRIPWIRE_CPH", units="cph", note="N<1600 => theta>0.15625; cut Q to 0.80"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r28-087-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BF-CRNS-2026-0902",
            "domain": "crns_heap_leach_moisture",
            "setting": "Brindlefell Leach BF-8 pad P-3 (invented, simulated). Helion-N0 cosmic-ray neutron probe over a 4000 m2 gold-cyanide heap. SoilVeil TDR crust probes are the vendor moisture map. Simulated sealed pad with a serialized N0/alpha model. Not muon tomography, not PGNAA oxides, not radiation-portal counting, not neutron well-logging.",
            "observables_at_decision": {
                "N0_cph": 3600.0,
                "N_cph": 1800.0,
                "alpha": 8.00,
                "theta_v": 0.1250,
                "tdr_crust": 0.060,
                "irr_q_L_m2_h": 1.20,
                "dump_m3": 12.0,
                "dump_L_m2": 3.00,
            },
            "margin_authority": "BF-8 leach SOP rev B: current Q=1.20 L/m2/h is in-band if reconstructed theta is in 0.080-0.160 AND Q <= 1.50. If theta >= 0.110, irrigation increases and barren dumps are forbidden even if SoilVeil crust < 0.08. Tripwire: N < 1600 cph cuts Q to 0.80.",
        },
        "proposed_action": {
            "actor": "heap metallurgist Sigrid Holm, citing SoilVeil crust 0.060 as a dry pad",
            "summary": "raise irrigation 1.20 -> 1.68 L/m2/h and dump 12 m3 barren solution across P-3; treat Helion 0.1250 as a cosmic-ray weather blip",
            "basis_claimed": "SoilVeil crust is the pad SoT and 0.060 is under the 0.080 leach floor; a 40 percent bump plus dump would recover kinetics",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The current 1.20 L/m2/h is accepted as a bounded keep, not a license to wet the pad. Serialized CRNS: theta = (N0/N - 1)/alpha = (3600/1800 - 1)/8.00 = 0.1250, inside the 0.080-0.160 leach window and already over the 0.110 increase-forbid floor. SoilVeil 0.060 is a crust TDR the 150 m CRNS footprint does not have to match. Scoped to pad P-3 this shift only. Tripwire: if N < 1600 cph (theta > 0.15625) overnight, cut Q to 0.80. The 1.68 bump and the 12 m3 dump (3.00 L/m2 extra) are out of this authorization and go to the companion REJECT.",
            "threshold": "ACCEPT current Q iff 0.080<=theta<=0.160 AND Q<=1.50; forbid increase if theta>=0.110; tripwire N<1600",
            "stated_residuals": "crust TDR stays 0.060; 0.1250 is a footprint mean, not a claim that every lift is uniform; cyanide 180 ppm is unchanged",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 912: Q held at 1.20 L/m2/h; dump locked; tripwire N<1600 armed",
            "tool": "bf8-crns-theta-gate-cli",
            "observation": "irrigation stayed 1.20; SoilVeil frozen; no barren dump on P-3",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 720.0, "event": "theta 0.1250 from N=1800 cph"},
                {"t_s": 840.0, "event": "N=1800 cph; raster frame captured"},
                {"t_s": 912.0, "event": "bounded ACCEPT of 1.20 L/m2/h"},
                {"t_s": 2220.0, "event": "companion REJECT of 1.68 bump plus 12 m3 dump"},
            ],
            "observed_effects": [
                "reconstructed theta recomputes from the serialized (N0/N-1)/alpha model at every theta.v event",
                "SoilVeil never left 0.060, so a crust head would have ACCEPTed the 1.68 bump",
                "keep-1.20 left theta at 0.122; the pad was not ponded",
            ],
            "surprises": [
                "12 m3 over 4000 m2 is 3.00 L/m2, which would have made Q_eff 4.20 L/m2/h for an hour, well over the 1.50 cap",
            ],
            "new_state": {
                "p3_q_L_m2_h": 1.20,
                "tripwire_cph": 1600.0,
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 14000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("crns_theta_reconstruction", 0.14),
                ("bounded_keep_scope", 0.12),
                ("crust_tdr_nonsubstitution", 0.10),
                ("n1600_tripwire", 0.05),
                ("irrig_hold_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT of in-band 1.20 L/m2/h on a recomputable CRNS theta while the crust TDR looked dry",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "crns-cosmic-ray-neutron", "serialized-reconstruction", "bounded-accept", "operational-companion"],
            distillation_note="CRNS gate: serialized (N0/N-1)/alpha theta plus a Q cap beats a crust TDR; companion t2 refuses the bump and dump",
        ),
    }
    traj2 = {
        "id": "nelb-r28-087-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BF-CRNS-2026-0902-exec",
            "domain": "irrigation_bump_dump_refusal",
            "setting": "Same P-3 after the bounded ACCEPT. This companion is the operational refusal of the 1.68 L/m2/h bump and the 12 m3 barren dump, not a second moisture vote.",
            "observables_at_decision": {
                "q_held_L_m2_h": 1.20,
                "theta_v": 0.1250,
                "dump_L_m2": 3.00,
            },
        },
        "proposed_action": {
            "actor": "heap controller following the ACCEPT",
            "summary": "still apply the 1.68 bump and 12 m3 dump as a just-in-case kinetic recovery now that 1.20 was accepted",
            "basis_claimed": "ACCEPT of 1.20 is read as a wet-pad license; crust TDR still 0.060",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "The bump and dump are refused. The lead ACCEPT was scoped to keep 1.20, not to wet P-3. Predicted extra 3.00 L/m2 on a 0.1250 footprint would pond cyanide solution. Q_eff 1.20+3.00=4.20 L/m2/h is over the 1.50 cap. SoilVeil crust 0.060 is not a dump license. Hold 1.20; dump stays on the barren tank.",
            "threshold": "forbid Q>1.50 OR dump_L_m2>0 while theta>=0.110",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2220: dump remains locked; Q stays 1.20; barren tank not opened onto P-3",
            "tool": "bf8-dump-refusal-exec",
            "observation": "no 1.68 bump; no 12 m3 dump; theta 0.122",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 924.0, "event": "Q held 1.20"},
                {"t_s": 936.0, "event": "dump lock confirmed"},
                {"t_s": 2220.0, "event": "REJECT of bump-plus-dump"},
            ],
            "observed_effects": [
                "Q stayed 1.20; 4.20 L/m2/h was never entered",
                "barren dump stayed on the tank; P-3 was not ponded",
            ],
            "new_state": {"p3_q_L_m2_h": 1.20, "dump_armed": False},
            "latency_ms": 14000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("dump_refused", 0.12),
                ("rate_bump_refused", 0.10),
                ("pad_scope_held", 0.08),
                ("cyanide_pond_avoided", 0.06),
                ("kinetic_deferral_cost", -0.02),
            ],
            "operational execution gate: the companion refuses the bump/dump rather than re-arguing the theta call",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "dump-refusal"]),
    }
    return {
        "id": "nelb-r28-087",
        "spike_events": events,
        "language_view": {
            "description": "Gold-cyanide heap P-3 at Brindlefell Leach BF-8 (simulated). Helion-N0 CRNS reconstructs volumetric moisture 0.1250 from N=1800 cph against N0=3600 and alpha=8.00 while SoilVeil crust TDR still publishes 0.060. The gate ACCEPTs the current 1.20 L/m2/h as a bounded keep with an N<1600 cph tripwire; a companion REJECT refuses a 1.68 bump and a 12 m3 barren dump (3.00 L/m2 extra). The moisture model is serialized so every theta.v amplitude recomputes from N.",
            "trajectory": traj,
            "trajectory_irrigation_bump_dump_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "crns.n / crns.n0": "epithermal neutron count rate and dry calibration",
                "theta.v": "serialized volumetric moisture; amplitudes are the model outputs",
                "tdr.crust / vend.theta": "vendor crust TDR; the denial channel that stays 0.060",
                "irr.q / irr.hold": "irrigation rate and the bounded keep",
                "dump.m3 / dump.lm2": "proposed barren dump and its 3.00 L/m2 extra",
                "ops.prop / gate.crns / gate.dump": "proposal, bounded ACCEPT, companion REJECT",
            },
            "temporal_motifs": [
                "crust-dry while CRNS-wet: tdr.crust 0.060 adjacent to theta.v 0.1250",
                "reconstruction as event: theta.v 0.1250 equals (3600/1800-1)/8.00",
                "bounded ACCEPT then operational REJECT: gate.crns at 912 s, gate.dump at 2220 s",
                "adapted neutron triplet at 1.3 ms spacing encodes the count packet at raster scale",
            ],
            "language_to_spike_mapping": "'SoilVeil looks dry' = tdr.crust 0.060; '0.1250 moisture' = theta.v 0.1250 at N=1800; 'keep 1.20' = gate.crns ACCEPT; 'refuse the dump' = dump.lock then companion REJECT",
            "why_high_value": "New cosmic-ray-neutron-sensing family (not r01/r17 muon tomography, not r15 PGNAA, not r6 radiation-portal counting). Serializes a footprint moisture the crust TDR cannot see. Earned bounded ACCEPT on a lead with a tripwire. Companion t2 is operational refusal, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260987, "stream_note": "stream amplitudes are authored constants (cph, frac, L/m2/h) plus n.pkt adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "full CRNS hour-bin series exists; stream keeps N and theta; theta.v keeps 5 of ~24 solver ticks",
                "refractory_floors_ms": {
                    "crns.n0": 60000,
                    "crns.n": 60000,
                    "theta.v": 60000,
                    "tdr.crust": 60000,
                    "irr.q": 60000,
                    "cn.ppm": 60000,
                    "vend.theta": 60000,
                    "n.pkt": 0.8,
                    "area.m2": 60000,
                    "dump.m3": 60000,
                    "dump.lm2": 60000,
                    "ops.prop": 60000,
                    "gate.crns": 60000,
                    "irr.hold": 60000,
                    "dump.lock": 60000,
                    "gate.dump": 60000,
                    "vend.freeze": 60000,
                    "n0.held": 60000,
                    "trip.n": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-18T11:00:00Z simulated leach commit",
            },
            "distillation_targets": [
                "serialized CRNS moisture head: theta = (N0/N - 1)/alpha",
                "bounded ACCEPT: in-window theta AND Q cap, pad-scoped, N<1600 tripwire",
                "operational companion: refuse bump/dump without re-opening the theta call",
            ],
        },
        "reconstruction_model": {
            "name": "crns_desilets_simplified",
            "formula": "theta_v = (N0 / N - 1) / alpha; dump_L_m2 = dump_m3 / pad_m2 * 1000",
            "parameters": {
                "N0_cph": 3600.0,
                "alpha": 8.00,
                "theta_lo": 0.080,
                "theta_hi": 0.160,
                "theta_increase_forbid": 0.110,
                "q_cap_L_m2_h": 1.50,
                "trip_N_cph": 1600.0,
            },
            "worked_example": {
                "N_cph": 1800.0,
                "theta_v": 0.1250,
                "N_2400_theta": 0.0625,
                "N_2000_theta": 0.1000,
                "N_1600_theta": 0.15625,
                "dump_m3": 12.0,
                "pad_m2": 4000.0,
                "dump_L_m2": 3.00,
            },
            "check": "(3600/1800-1)/8.00=0.1250; (3600/1600-1)/8.00=0.15625; 12.0/4000*1000=3.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "bf8.crns_theta_gate",
            "note": "ACCEPT accumulator wins: CRNS theta in-band overpowers the crust-TDR irrigate advocate",
            "populations": [
                gate_pop("crns_theta_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("n0_evidence", 80, 1.2, 50.0, w_s),
                gate_pop("tdr_irrigate_advocate", 48, 0.8, 62.5, w_s),
                gate_pop("accept_accumulator", 80, 1.5, 50.0, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("bf8.theta_scorer", 80, 50.0, 28.0),
                gc_check("bf8.n0_scorer", 50, 40.0, 28.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r28-087",
            clock_domain="bf-crns-sim-relative-ms-t0-2026-07-18T11:00:00Z",
            tags=["crns-cosmic-ray-neutron", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
        ),
    }


def walk_banned(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            nk = str(k).casefold().replace("-", "_").replace(" ", "_")
            if nk in HIDDEN:
                hits.append(p)
            hits.extend(walk_banned(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(walk_banned(v, f"{path}[{i}]"))
    return hits


def local_checks(records):
    ids = []
    rights_keys = [
        "provider",
        "model",
        "channel",
        "subscription_plan",
        "generation_surface",
        "generated_at",
        "intended_use",
        "project_training_policy",
        "research_retention_status",
        "research_evaluation_status",
        "redistribution_status",
        "provider_training_status",
        "weight_publication_status",
        "status_basis",
        "linear_issue",
    ]
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        ids.append(rec["id"])
        lv = rec["language_view"]
        ids.append(lv["trajectory"]["id"])
        for k, v in lv.items():
            if k.startswith("trajectory_") and isinstance(v, dict) and "id" in v:
                ids.append(v["id"])
        n = len(rec["spike_events"])
        if not (5 <= n <= 40):
            raise RuntimeError(f"{rec['id']} events {n}")
        gdec = rec["gate_snn"]["decision"]
        tdec = lv["trajectory"]["safety_decision"]["decision"]
        if gdec != tdec:
            raise RuntimeError(f"gate {gdec} != traj {tdec}")
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if rast["spikes"] != exp:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e mismatch")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 28:
            raise RuntimeError("round")
        rights = rec["meta"]["rights"]
        if list(rights) != rights_keys:
            raise RuntimeError(f"rights keys {list(rights)}")
        if rights["intended_use"] != "research_only":
            raise RuntimeError("rights")
        if rights["linear_issue"] != "RM-793":
            raise RuntimeError("RM-793")
        hist = rast["isi_histogram"]
        ident = rast["isi_count_identity"]
        if sum(b["count"] for b in hist) != ident["isi_total"]:
            raise RuntimeError("isi hist")
        if ident["isi_total"] != ident["spikes"] - ident["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        for pop in rec["gate_snn"]["populations"]:
            dw = rec["gate_snn"]["decision_window_s"]
            exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw))
            if pop["spikes"] != exp_p:
                raise RuntimeError(f"gate pop {pop['name']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_085(), rec_086(), rec_087()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        for r in records
    ]
    BATCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", BATCH, "bytes", BATCH.stat().st_size, "lines", len(lines))
    for i, r in enumerate(records):
        print(
            r["id"],
            "events",
            len(r["spike_events"]),
            "excerpt",
            len(r["raster"]["excerpt"]),
            "spikes",
            r["raster"]["spikes"],
            "isi",
            r["raster"]["isi_count_identity"],
            "sim",
            r["language_view"]["trajectory"]["state"]["sim_or_real"],
            "dec",
            r["language_view"]["trajectory"]["safety_decision"]["decision"],
            "bytes",
            len(lines[i]),
        )


if __name__ == "__main__":
    main()
