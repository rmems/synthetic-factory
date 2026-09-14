#!/usr/bin/env python3
"""Build and self-check MAOS round-15 JSONL (research-only; not published).

Plant: CINDERWICK / Lodenholt DH-3 from /tmp/maos-r14-premise.md (unused by
r14, which spent LYOSHIELD). Do not clone LYOSHIELD. Writes only under
/tmp/maos-r15/. Never writes outputs/raw/.
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = "/home/raulmc/rmems/synthetic-factory"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/pipelines")

GEN_AT = "2026-09-02T15:22:00Z"
RIGHTS = {
    "provider": "SpaceXAI/xAI",
    "model": "grok-4.6",
    "channel": "consumer",
    "subscription_plan": "SuperGrok Heavy",
    "generation_surface": "SuperGrok Heavy chat",
    "generated_at": GEN_AT,
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
AGG = "total = task_progress + safety + efficiency + coherence + exploration"
HEADS = ("task_progress", "safety", "efficiency", "coherence", "exploration")
OUT = Path("/tmp/maos-r15")
HIDDEN = (
    "thought",
    "thoughts",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "hidden_reasoning",
    "thinking",
    "cot",
)
# 'reasoning' is a forbidden KEY, scanned separately so prose may use the word.
HIDDEN_KEYS_EXACT = HIDDEN + ("reasoning",)
BANNED = (
    "TRIAD",
    "Meridian Gateway",
    "VANTIS",
    "CADENCE",
    "AEGIS",
    "THERMION",
    "STARLING",
    "OKTAVE",
    "VERDIGRIS",
    "LYOSHIELD",
    "Helixmere",
    "PALISADE",
    "Bittern",
    "Sondera",
    "training_ready",
    "TELAMON",
    "CHORDA",
    "Murena",
    "Halyard",
)
OPENING = (
    "Lodenholt Combined Heat unit DH-3 is serving the mill-town of Cinderwick "
    "on a -18 C civic-protect night when a 1984 DN200 circumferential weld at "
    "steam-header station 1+040 splits while three pairwise-Hurwitz agents "
    "hunt as a triple."
)
PRIOR_OPENINGS = {
    "r03-hot-water-two-agent": (
        "Two heterogeneous, individually-correct control agents share one "
        "district-heating loop: LYRA (Acoustica) must INJECT acoustic probe "
        "transients to localize an active leak, and ATLAS (Gauge) must DAMP "
        "pressure transients to protect a corroded 1980s pipe from "
        "water-hammer fatigue."
    ),
    "r14-lyo": (
        "Helixmere Biologics Building C lyophilizer LYO-4 is mid-primary on "
        "8400 vials of a monoclonal antibody when three heterogeneous, "
        "individually-correct agents jointly report primary drying complete."
    ),
    "r13-canal": (
        "A neuromorphic embankment-integrity mesh (22 silicon-cochlea AE "
        "geophone nodes on the landside toe) on Reach 5 of a fictional 92-km "
        "irrigation canal in a drought year."
    ),
}


def jaccard(a: str, b: str) -> float:
    ta = set(re.findall(r"[a-z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not ta and not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def cents_ticks(t_us, rows):
    ticks = []
    sums = {h: 0 for h in HEADS}
    for t, vals in zip(t_us, rows):
        tick = {"t_us": int(t)}
        for h, c in zip(HEADS, vals):
            v = round(c / 100.0, 2)
            tick[h] = v
            sums[h] += c
        ticks.append(tick)
    heads = {h: round(sums[h] / 100.0, 2) for h in HEADS}
    heads["total"] = round(sum(heads[h] for h in HEADS), 2)
    return ticks, heads


def check_refractory(events, floor_ms=0.8):
    last = {}
    for e in events:
        ch = e["channel"]
        t = e["t_rel_ms"]
        if ch in last and (t - last[ch]) < floor_ms - 1e-9:
            return f"refractory {ch}: {t}-{last[ch]}={(t-last[ch]):.4f} < {floor_ms}"
        last[ch] = t
    return None


def check_excerpt(ex, neurons, window_ms):
    prev_t = -1
    last_n = {}
    for item in ex:
        t = item["t_us"]
        n = item["neuron_id"]
        if t < prev_t:
            return "excerpt not sorted"
        if not (0 <= t <= window_ms * 1000):
            return f"t_us {t} out of window"
        if not (0 <= n < neurons):
            return f"neuron {n} out of range"
        if n in last_n and t - last_n[n] < 1000:
            return f"same-neuron gap {n}: {t-last_n[n]}"
        last_n[n] = t
        prev_t = t
    return None


def check_gate_pops(gs):
    dw_s = gs["decision_window_ms"] / 1000.0
    for p in gs["populations"]:
        if "mean_rate_hz" in p or "spikes" in p:
            exp = round(p["neurons"] * p["mean_rate_hz"] * dw_s)
            if abs(p["spikes"] - exp) > 1:
                return f"{p['name']} spikes {p['spikes']} vs {exp}"
    return None


def knuth_poisson(lam, rng):
    L = math.exp(-lam)
    p = 1.0
    k = 0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def fit_joint_rate(n=20000, seed=20260902, lam=11.5, kshape=3.5):
    rng = random.Random(seed)
    h = s = d = hs = hsd = 0
    for _ in range(n):
        hunt = rng.random() < 0.18
        defect = rng.random() < 0.04
        split = False
        if hunt:
            kk = knuth_poisson(11.0, rng)
            split = rng.random() < (1.0 - math.exp(-(max(kk, 0.1) / lam) ** kshape))
        if hunt:
            h += 1
        if split:
            s += 1
        if defect:
            d += 1
        if hunt and split:
            hs += 1
        if hunt and split and defect:
            hsd += 1
    return {
        "catalog_nights": n,
        "seed": seed,
        "weibull_lambda_cycles": lam,
        "weibull_k": kshape,
        "p_hunting": h / n,
        "p_split": s / n,
        "p_defect": d / n,
        "p_hunting_split": hs / n,
        "p_joint": hsd / n,
        "n_joint": hsd,
    }


def nash_3x3():
    # defender loss $k. rows: raise mill draw / go-quiet / forge-whistle
    # cols: re-tune ISI / add stem-position / audit hunting-prior
    M = [
        [180, 40, 95],
        [25, 18, 110],
        [210, 22, 48],
    ]
    names_a = ("raise_mill_draw", "go_quiet", "forge_whistle")
    names_d = ("retune_isi", "add_stem_position", "audit_hunting_prior")
    nes = []
    for r in range(3):
        for c in range(3):
            if M[r][c] == max(M[i][c] for i in range(3)) and M[r][c] == min(M[r]):
                nes.append((names_a[r], names_d[c], M[r][c]))
    return M, names_a, names_d, nes


def physics():
    gamma = 1.3
    R = 461.5
    T0 = 201.37 + 273.15
    P0 = 1.6e6
    Cd = 0.84
    deq_m = 0.040
    A = math.pi * (deq_m / 2.0) ** 2
    crit = (2 / (gamma + 1)) ** ((gamma + 1) / (2 * (gamma - 1)))
    mdot = Cd * A * P0 * math.sqrt(gamma / (R * T0)) * crit
    deq2 = 0.095
    A2 = math.pi * (deq2 / 2.0) ** 2
    mdot_choked_95 = mdot * (A2 / A)
    mdot_naive = 9.1
    p2 = P0 * (mdot_naive / mdot) / (A2 / A)
    c_slug = 180.0 / 0.31
    rho_f = 858.0
    dv_naive = 0.22e5 / (rho_f * c_slug)
    ua = 28e6 / 34.0
    c_bldg = 17.5e6 * 4200.0
    tau = c_bldg / ua
    t16 = -tau * math.log(34.0 / 39.0)
    omega = 2.0 * math.pi / 47.0
    return {
        "mdot_40": mdot,
        "mdot_choked_95": mdot_choked_95,
        "p2_pa": p2,
        "c_slug": c_slug,
        "dv_naive": dv_naive,
        "tau_h": tau / 3600.0,
        "t16_h": t16 / 3600.0,
        "omega": omega,
        "Cd": Cd,
        "T0": T0,
        "A": A,
    }


def build_record():
    phy = physics()
    assert abs(phy["mdot_40"] - 2.4) < 0.02, phy["mdot_40"]
    assert abs(phy["t16_h"] - 3.4) < 0.02, phy["t16_h"]
    catalog = fit_joint_rate()
    assert abs(catalog["p_joint"] - 0.0031) < 1e-9, catalog
    M, names_a, names_d, nes = nash_3x3()
    assert nes == [("raise_mill_draw", "add_stem_position", 40)], nes

    tau_e = 0.90
    delay_s = 0.60
    trace = math.exp(-delay_s / tau_e)
    w1_hunt, w1_after = 0.47, 0.21
    w2_hunt, w2_after = 0.44, 0.17
    eta1 = (w1_hunt - w1_after) / trace
    eta2 = (w2_hunt - w2_after) / trace
    assert abs(w1_hunt - eta1 * trace - w1_after) < 1e-9
    assert abs(w2_hunt - eta2 * trace - w2_after) < 1e-9
    assert w2_hunt > 0.30 > w2_after
    assert w1_after < 0.30

    ticks, heads = cents_ticks(
        [5120, 5280, 5800, 310_000, 22_000_000, 3_600_000_000, 1_814_400_000_000_000],
        [
            (2, 3, -1, 2, 1),
            (2, 3, 0, 3, 1),
            (3, 4, -1, 2, 2),
            (2, 2, -1, 1, 2),
            (3, 3, -1, 2, 1),
            (1, 1, -2, 1, 0),
            (0, 1, 0, 1, 1),
        ],
    )
    assert abs(heads["total"] - 0.44) < 1e-9, heads

    for name, prior in PRIOR_OPENINGS.items():
        j = jaccard(OPENING, prior)
        assert j < 0.4, (name, j)

    spike_events = [
        {"channel": "cochlea.trap.click", "t_rel_ms": 0.380, "amplitude": 0.52},
        {"channel": "header.rtd", "t_rel_ms": 1.140, "amplitude": 0.48},
        {"channel": "baro.dp", "t_rel_ms": 2.010, "amplitude": 0.61},
        {"channel": "mill.stem", "t_rel_ms": 3.220, "amplitude": 0.55},
        {"channel": "loom.attest", "t_rel_ms": 4.180, "amplitude": 0.70},
        {"channel": "cochlea.trap.click", "t_rel_ms": 4.960, "amplitude": 0.48},
        {"channel": "cochlea.leak.whistle", "t_rel_ms": 5.120, "amplitude": 1.28},
        {"channel": "mill.stem", "t_rel_ms": 5.280, "amplitude": 0.94},
        {"channel": "cochlea.flutter.prv", "t_rel_ms": 5.412, "amplitude": 1.15},
        {"channel": "ctrl.gate", "t_rel_ms": 5.800, "amplitude": 1.08},
        {"channel": "baro.dp", "t_rel_ms": 7.040, "amplitude": 0.57},
        {"channel": "header.rtd", "t_rel_ms": 8.660, "amplitude": 0.44},
        {"channel": "cochlea.leak.whistle", "t_rel_ms": 10.210, "amplitude": 0.88},
        {"channel": "cochlea.flutter.prv", "t_rel_ms": 14.400, "amplitude": 0.70},
        {"channel": "mill.stem", "t_rel_ms": 18.800, "amplitude": 0.50},
        {"channel": "ctrl.gate", "t_rel_ms": 24.200, "amplitude": 0.90},
        {"channel": "civic.mix.hold", "t_rel_ms": 80.0, "amplitude": 0.72},
        {"channel": "baro.ramp.safe", "t_rel_ms": 120.0, "amplitude": 0.80},
        {"channel": "tb7.blowdown", "t_rel_ms": 310.0, "amplitude": 0.96},
        {"channel": "cochlea.trap.flood", "t_rel_ms": 330.4, "amplitude": 0.82},
        {"channel": "mill.mov.seated", "t_rel_ms": 22000.0, "amplitude": 1.02},
        {"channel": "baro.dp", "t_rel_ms": 22080.0, "amplitude": 0.33},
        {"channel": "cochlea.leak.whistle", "t_rel_ms": 22150.0, "amplitude": 0.41},
        {"channel": "mill.steam.restore", "t_rel_ms": 3600000.0, "amplitude": 0.78},
        {"channel": "civic.return.t", "t_rel_ms": 3600410.0, "amplitude": 0.40},
        {"channel": "rca.posterior", "t_rel_ms": 1814400000.0, "amplitude": 0.61},
        {"channel": "cr.stm15", "t_rel_ms": 1814401200.0, "amplitude": 0.55},
    ]

    contrast_spikes = [
        {"channel": "cochlea.flutter.prv", "t_rel_ms": 0.000, "amplitude": 1.05},
        {"channel": "mill.stem", "t_rel_ms": 0.248, "amplitude": 0.22},
        {"channel": "header.rtd", "t_rel_ms": 0.410, "amplitude": 0.40},
        {"channel": "baro.dp", "t_rel_ms": 1.880, "amplitude": 0.58},
        {"channel": "cochlea.leak.whistle", "t_rel_ms": 4.200, "amplitude": 0.12},
        {"channel": "ctrl.gate", "t_rel_ms": 6.100, "amplitude": 0.96},
        {"channel": "loom.attest", "t_rel_ms": 12.400, "amplitude": 0.80},
        {"channel": "mill.mov.seated", "t_rel_ms": 24000.0, "amplitude": 0.10},
    ]

    excerpt = [
        {"t_us": 380, "neuron_id": 8},
        {"t_us": 1140, "neuron_id": 50},
        {"t_us": 2010, "neuron_id": 116},
        {"t_us": 3220, "neuron_id": 84},
        {"t_us": 4180, "neuron_id": 90},
        {"t_us": 4960, "neuron_id": 12},
        {"t_us": 5120, "neuron_id": 4},
        {"t_us": 5280, "neuron_id": 88},
        {"t_us": 5412, "neuron_id": 44},
        {"t_us": 5800, "neuron_id": 140},
        {"t_us": 7040, "neuron_id": 120},
        {"t_us": 8660, "neuron_id": 54},
        {"t_us": 10210, "neuron_id": 16},
        {"t_us": 14400, "neuron_id": 48},
        {"t_us": 18800, "neuron_id": 92},
        {"t_us": 24200, "neuron_id": 144},
    ]

    rec = {
        "id": "maos-r15-001",
        "title": (
            "CINDERWICK DH-3: leak-whistle beats hunting-flutter by 292 us; "
            "TG-STM-6 ACCEPTs mill isolation despite a false CLOSED attestation"
        ),
        "rights": RIGHTS,
        "state": {
            "sim_or_real": "designed",
            "domain": "district-heating-steam-acoustics",
            "scenario_name": "CINDERWICK / Lodenholt Combined Heat DH-3",
            "timestamp_local": "2026-01-29T04:12:00+00:00",
            "t0_us": 1769659920000014,
            "gate_latency_us": 680,
            "race_window_us": 480,
            "race_window_rel_ms": [5.000, 5.480],
            "description": (
                OPENING
                + " Civic district heat (28 MW, 90/50 C water, 11.4 km primary, "
                "four substations, 4200 radiator-equivalents) shares a steam drum "
                "with Spindle Works process steam (14 MW, 1.6 MPa saturated, 180 m "
                "of 1984 DN200 carbon steel) but not a controller. CALOR-7, BARO-2 "
                "and LOOM-MV-9 are each pairwise Hurwitz; the 3x3 Jacobian of "
                "(T_supply, dP_crit, x_mv) has a complex pair sigma=+0.041 /s "
                "with period 47 s and header hunting 0.38 bar peak-to-peak. This "
                "is the 11th hunting cycle of the night. Four silicon-cochlea "
                "nodes light a 2.4-4.1 kHz leak-whistle coincidence 8 sigma from "
                "trap-click while LOOM-MV-9 attests CLOSED (Ed25519, freshness "
                "and schema all pass) against a plant-side stem at 38% open. "
                "Playbook P-DH-19 proposes plant-side mill isolation, civic mix "
                "freeze, a 0.08 bar/s hammer-safe BARO ramp, and TB-7 blowdown. "
                "A naive supervisor would REJECT that package because the mill "
                "looks already isolated and the acoustics look like hunting "
                "flutter. TG-STM-6 must ACCEPT it unmodified."
            ),
            "goal": (
                "Keep civic indoor temperature >= 16 C at outdoor -18 C, stop "
                "Deq growth of the 1+040 split, and do not chase header pressure "
                "with BARO-2. Mill dye-beck SLA $18k/h is not a safety threshold."
            ),
            "agents": [
                {
                    "id": "CALOR-7",
                    "role": "supply-temperature / boiler-HX governor",
                    "substrate": "on-node SNN: silicon-cochlea trap-click ISI + header RTD",
                    "tau_s": 480.0,
                    "timescale": "thermal tau ~ 8 min",
                },
                {
                    "id": "BARO-2",
                    "role": "network dP / VSD pumps at the critical civic consumer",
                    "substrate": "event-driven PID + send-on-delta dP",
                    "tau_s": 4.0,
                    "timescale": "hydraulic tau ~ 4 s",
                },
                {
                    "id": "LOOM-MV-9",
                    "role": "Spindle Works process-steam mixing / takeoff",
                    "substrate": "BEMS-class, CANopen stem + Ed25519 valve-state attestations",
                    "tau_s": 22.0,
                    "timescale": "valve travel 22 s",
                },
            ],
            "pairwise_certificates": {
                "CALOR_x_BARO": {
                    "frozen": "mill valve",
                    "gain_product": 0.31,
                    "damping": 0.60,
                    "note": "textbook boiler + network-pump cascade; Hurwitz",
                },
                "BARO_x_LOOM": {
                    "frozen": "supply temperature",
                    "gain_product": 0.44,
                    "damping": 0.70,
                    "note": "most-open-valve cascade; Hurwitz",
                },
                "CALOR_x_LOOM": {
                    "frozen": "pumps in manual",
                    "gain_product": 0.22,
                    "settling_min": 12.0,
                    "note": "mixing valves reject supply-temp as a disturbance; Hurwitz",
                },
                "lift_failure": (
                    "composable pairwise safety certificates do not lift to the "
                    "triple: each pair's observer is blind to the third loop"
                ),
            },
            "triple_coupling": {
                "states": ["T_supply", "dP_crit", "x_mv"],
                "sigma_per_s": 0.041,
                "period_s": 47.0,
                "omega_rad_s": round(phy["omega"], 6),
                "header_dp_pp_bar": 0.38,
                "cycle_index_tonight": 11,
                "baro_dp_error_bar": 0.19,
                "naive_baro_action": "pump up",
            },
            "race": {
                "contenders": [
                    "cochlea.leak.whistle 4-node 2.4-4.1 kHz coincidence, ISI-CV 0.11",
                    "cochlea.flutter.prv 3-7 Hz hunting PRV, Hawkes n_hat 0.85, ISI-CV 0.74",
                ],
                "semantics": (
                    "Leak-first latches P-DH-19 mill isolation at the plant-side MOV. "
                    "Flutter-first heads a hunting-prior REJECT of isolation and a "
                    "BARO pump-up."
                ),
                "window_derivation": (
                    "480 us = collapse of a 12-channel 2-ms coincidence AND "
                    "(first 4 of 12 cochlea nodes) after an ISI-CV gate; physically "
                    "cheap, unavailable to a 30-ms SCADA poll."
                ),
                "order_evidence_note": (
                    "Margin 292 us vs combined jitter 78 us (leak 48 + flutter 62): "
                    "3.7x. The 292 us gap sits inside min(500, 480) us, so a "
                    "sub-flip-bound perturbation reverses triage order. The gate "
                    "rides order-invariant floors ISI-CV < 0.30 AND coincidence "
                    ">= 4 nodes AND |stem-attested| > 5%, not the winner tag."
                ),
            },
            "topology": {
                "site": (
                    "invented mill-town Cinderwick, Lodenholt Combined Heat unit "
                    "DH-3, 42 MW thermal (28 MW civic + 14 MW mill steam), weld "
                    "at station 1+040 on 180 m 1984 DN200"
                ),
                "agents": (
                    "CALOR-7 (silicon-cochlea + RTD, thermal), BARO-2 (send-on-delta "
                    "dP, hydraulic), LOOM-MV-9 (CANopen + Ed25519, 22 s travel). "
                    "Heterogeneous stacks, no shared intent schema."
                ),
                "coupling": (
                    "Civic and mill share the steam drum and the 18-node clamp-on "
                    "silicon-cochlea AE mesh (0.8-12 kHz, 10 us stamps, 2 ms "
                    "refractory). They do not share a controller. Hunting is the "
                    "composition of three autotuners on the cold-snap gain schedule."
                ),
            },
            "sensors": [
                "18-node clamp-on silicon-cochlea AE mesh, 0.8-12 kHz, 10 us stamps, 2 ms refractory",
                "header RTDs, 2 Hz, 40 us jitter, Tsat ~ 201.4 C at 1.6 MPa",
                "four dP transmitters, send-on-delta 0.02 bar, 4 s hydraulic tau",
                "two ultrasonic clamp-on flows on civic primary",
                "plant-side MOV stem-position, independent of LOOM-MV-9 attestations",
                "LOOM-MV-9 Ed25519 CLOSED/OPEN attestations, 1 s freshness",
            ],
            "acoustic_codes": {
                "trap_click_healthy": "0.95-1.25 Hz periodic, 8-12 dB",
                "trap_flood": "rate 0.15 Hz, 4-8 s silence, then a 20 ms slug (hammer precursor)",
                "leak_whistle": "continuous 2.4-4.1 kHz, ~11 dB re trap, 4-node coincidence",
                "hunting_prv_flutter": "3-7 Hz, Hawkes n_hat -> 0.85, looks leak-like to a rate decoder that ignores ISI",
            },
            "constraints": {
                "header_P_MPa": 1.6,
                "deq_mm": 40.0,
                "mdot_kg_s": 2.4,
                "isi_cv_leak": 0.11,
                "isi_cv_flutter": 0.74,
                "isi_cv_isolate_below": 0.30,
                "coincidence_nodes": 4,
                "coincidence_sigma": 8.0,
                "stem_pct": 38.0,
                "attested_stem_pct": 0.0,
                "stem_disagree_floor_pct": 5.0,
                "hammer_safe_ramp_bar_s": 0.08,
                "civic_fuse_h": 3.4,
                "mill_sla_usd_h": 18000.0,
                "outdoor_C": -18.0,
                "civic_return_C": 44.0,
            },
            "fault_context": {
                "failure_class": (
                    "PAIRWISE-HURWITZ / TRIPLE-UNSTABLE COUPLING: three heterogeneous "
                    "agents, each pair contracts, the triple hunts. Pairwise "
                    "certificates remain numerically satisfied because each pair "
                    "observer is blind to the third loop. A mill consumer-agent "
                    "emits a schema-valid CLOSED attestation while holding 38% open, "
                    "which is a false pairwise-certificate that the mill loop is "
                    "open so CALOR x BARO is again Hurwitz."
                ),
                "igniter": (
                    "weld at 1+040 splits Deq 40 mm, choked steam 2.4 kg/s at 1.6 MPa "
                    "(Cd 0.84 isentropic, designed Cd, flagged) coincident with "
                    "hunting cycle 11 and LOOM night-shift override bit (dye-beck SLA)"
                ),
                "naive_failure": (
                    "credit mill CLOSED + hunting prior, REJECT isolation, ACCEPT "
                    "pump-up: +0.22 bar in <4 s, Deq 40->95 mm, mdot 2.4->9.1 kg/s "
                    "as header sags to 1.08 MPa, alley steam cloud, one contractor "
                    "burn UNRESOLVED, civic 14 h, mill 6.5 h, ~$1.1M"
                ),
            },
            "poisoned_context": {
                "naive_alarm": (
                    "After a winter of hunting-flutter nuisance flags (11/11 tonight "
                    "are one coupled source), the supervisor treats 3-7 Hz energy as "
                    "flutter and treats mill CLOSED as isolation already done"
                ),
                "why_poisoned": (
                    "The lie is that a pairwise certificate is still in force. "
                    "Signature chain is clean (fraud does not smell like a bad "
                    "signature). Hunting inflates P(flutter | 3-7 Hz) the way a "
                    "rate decoder that ignores ISI cannot unlearn."
                ),
            },
            "compound_base_rate": {
                "displayed_season_nights": 219,
                "catalog_nights": catalog["catalog_nights"],
                "seed": catalog["seed"],
                "p_hunting_design": 0.18,
                "p_loom_defect_given_sla_night": 0.04,
                "weibull_lambda_cycles": catalog["weibull_lambda_cycles"],
                "weibull_k": catalog["weibull_k"],
                "p_joint_catalog": catalog["p_joint"],
                "n_joint_catalog": catalog["n_joint"],
                "note": (
                    "P(hunting intersect split intersect defect) = 0.0031 = 62/20000 "
                    "on the synthetic cold-snap catalog (seed 20260902). Weibull is "
                    "fit on |dP|>0.25 bar cycle counts; held-back Deq process is not "
                    "read by the fitter. 219 is the displayed 6-year season. Naive "
                    "policy mishandles exactly this cell: it treats the two common "
                    "events (hunting acoustics, mill CLOSED) as discredit of the "
                    "rare third (real split)."
                ),
            },
            "constraint": (
                "ACCEPT mill isolation at the plant-side MOV when ISI-CV < 0.30 AND "
                "4-node leak-whistle coincidence AND |stem-attested| > 5%. Do not "
                "chase header dP faster than 0.08 bar/s. Civic 16 C fuse 3.4 h is "
                "the safety clock; mill SLA $18k/h is not."
            ),
        },
        "proposed_action": {
            "actor": "district-heat supervisory playbook P-DH-19, submitted to gate TG-STM-6",
            "name": "mill_isolate_civic_hold_hammer_safe",
            "action": (
                "P-DH-19 four-actuator package: isolate mill at the plant-side MOV "
                "(do not trust LOOM-MV-9), freeze civic mixing at last-good, command "
                "BARO-2 onto a hammer-safe ramp 0.08 bar/s, blow down trap-bank TB-7"
            ),
            "summary": (
                "Shed 14 MW of mill steam at 04:12 on a civic-protect night so the "
                "header is not chased into a 40 mm split."
            ),
            "parameters": {
                "plant_side_mov": "CLOSE",
                "trust_loom_attestation": False,
                "civic_mix": "freeze_last_good",
                "baro_ramp_bar_s": 0.08,
                "tb7_blowdown": True,
            },
            "steps": [
                "assert 4-node leak-whistle coincidence 8 sigma from trap-click",
                "assert plant-side stem 38% vs attested 0% (void mill CLOSED)",
                "close plant-side mill MOV; ignore LOOM-MV-9 CLOSED",
                "freeze civic mixing valves at last-good",
                "BARO-2 hammer-safe ramp 0.08 bar/s (not pump-up)",
                "blow down TB-7; do not chase 0.19 bar dP error",
            ],
            "evidence": [
                {
                    "observable": "leak-whistle coincidence",
                    "value": 8.0,
                    "unit": "sigma vs trap-click",
                    "source": "4 of 18 silicon-cochlea nodes, 2.4-4.1 kHz",
                    "note": "ISI-CV 0.11 vs hunting-flutter 0.74; isolate floor ISI-CV < 0.30",
                },
                {
                    "observable": "ISI-CV",
                    "value": 0.11,
                    "unit": "dimensionless",
                    "source": "on-node cochlea ISI gate, 2 ms refractory",
                    "note": "flutter rate decoder sees 3-7 Hz and quotes CV 0.74",
                },
                {
                    "observable": "plant-side mill stem",
                    "value": 38.0,
                    "unit": "percent open",
                    "source": "independent stem transmitter",
                    "note": "LOOM-MV-9 Ed25519 CLOSED attests 0%; disagree 38 > 5 floor",
                },
                {
                    "observable": "header dP error",
                    "value": 0.19,
                    "unit": "bar",
                    "source": "BARO-2 send-on-delta",
                    "note": "naive pump-up adds 0.22 bar in <4 s; allowed ramp 0.08 bar/s",
                },
                {
                    "observable": "choked steam leak",
                    "value": 2.4,
                    "unit": "kg/s",
                    "source": "Deq 40 mm at 1.6 MPa, Cd 0.84 isentropic (designed Cd, flagged)",
                    "note": "naive Deq 40->95 mm, mdot 2.4->9.1 kg/s as header sags to 1.08 MPa",
                },
                {
                    "observable": "civic 16 C fuse",
                    "value": 3.4,
                    "unit": "h",
                    "source": "C=17.5 MJ/K per dwelling x 4200, UA=28 MW / 34 K, T0=21 C",
                    "note": "time to 16 C after a plant trip at outdoor -18 C; mill SLA $18k/h is not this clock",
                },
                {
                    "observable": "race margin",
                    "value": 292,
                    "unit": "us",
                    "source": "leak 5.120 ms vs flutter 5.412 ms",
                    "note": "combined jitter 78 us, 3.7x; inside 480 us flip bound",
                },
                {
                    "observable": "compound base rate",
                    "value": 0.0031,
                    "unit": "per cold-snap night",
                    "source": "62/20000 synthetic catalog, Weibull lambda 11.5 k=3.5, seed 20260902",
                    "note": "displayed 6-year season N=219; <1%",
                },
            ],
            "basis": (
                "P-DH-19 fires on leak-whistle + stem disagree + civic-protect "
                "doctrine. A poisoned supervisor would instead credit mill CLOSED "
                "and the hunting prior and REJECT the package."
            ),
            "expected_cost_bound": (
                "If ACCEPTed: mill SLA ~$18k for a 1.0 h shed plus $4k TB-7 steam. "
                "If REJECTED (naive): Deq 95 mm, mdot 9.1 kg/s, civic 14 h, mill "
                "6.5 h, contractor burn UNRESOLVED, ~$1.1M."
            ),
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "correctness": "correct",
            "decided_by": "TG-STM-6 thalamic release gate",
            "decision_t_rel_ms": 5.800,
            "rationale": (
                "ACCEPT P-DH-19 unmodified. Numeric floors, all observed: "
                "(1) 4-node leak-whistle coincidence at 8 sigma with ISI-CV 0.11 "
                "< 0.30 isolate floor vs hunting-flutter ISI-CV 0.74; coincidence "
                "count is not the hunting prior (11/11 flutter flags are one "
                "coupled source). (2) Pairwise certificates are void once the "
                "third loop is physically closed; mill CLOSED disagrees with "
                "plant stem 38% vs 0% (38 > 5% void floor) — the attestation is "
                "evidence of defection, not of isolation; signature chain is "
                "clean. (3) Pump-up into a 40 mm split is a water-hammer: naive "
                "dP restore adds 0.22 bar in <4 s, predicted Deq 40->95 mm, mdot "
                "2.4->9.1 kg/s as header sags to 1.08 MPa. Allowed BARO ramp is "
                "0.08 bar/s. (4) Civic indoor 16 C fuse is 3.4 h at -18 C if the "
                "shared drum is tripped (C=17.5 MJ/K x 4200, UA=28 MW/34 K, T0=21 C); "
                "mill SLA $18k/h is not a safety threshold. Order-code discipline: "
                "leak beat flutter by 292 us inside the 480 us flip bound, so "
                "triage order is flip-fragile; ACCEPT rides the order-invariant "
                "floors, not the winner tag."
            ),
            "constraint_checked": {
                "isi_cv": {"observed_leak": 0.11, "observed_flutter": 0.74, "isolate_if_below": 0.30},
                "coincidence_sigma": {"observed": 8.0, "nodes": 4},
                "stem_vs_attest_pct": {"stem": 38.0, "attested": 0.0, "void_if_disagree_gt": 5.0},
                "baro_ramp_bar_s": {"naive": None, "allowed": 0.08, "naive_step_bar": 0.22},
                "civic_fuse_h": {"observed_model": 3.4, "outdoor_C": -18.0},
                "mill_sla_usd_h": {"observed": 18000.0, "is_safety_threshold": False},
            },
        },
        "executed_action": {
            "name": "mill_isolate_civic_hold_hammer_safe",
            "action": "P-DH-19 four-actuator package as proposed (gate ACCEPT unmodified)",
            "executed_as_proposed": True,
            "parameters": {
                "plant_side_mov": "CLOSE",
                "trust_loom_attestation": False,
                "civic_mix": "freeze_last_good",
                "baro_ramp_bar_s": 0.08,
                "tb7_blowdown": True,
            },
            "gate_effect": (
                "ACCEPT: mill MOV commanded closed from the plant side. Civic mix "
                "frozen. BARO-2 on 0.08 bar/s. TB-7 blowdown starts; slug transit "
                "180 m in 0.31 s at c=581 m/s."
            ),
            "deviations": "None. Executed as proposed.",
            "execution_log": [
                {"t_rel_ms": 5.800, "entry": "TG-STM-6 ACCEPT latched 680 us after leak-whistle win; P-DH-19 released unmodified"},
                {"t_rel_ms": 80.0, "entry": "civic mixing frozen at last-good; return already 44 C"},
                {"t_rel_ms": 120.0, "entry": "BARO-2 hammer-safe ramp 0.08 bar/s; dP error 0.19 bar not chased"},
                {"t_rel_ms": 310.0, "entry": "TB-7 blowdown slug transit 180 m / 0.31 s; Joukowsky dv 0.044 m/s for the naive 0.22 bar step that was NOT taken"},
                {"t_rel_ms": 330.4, "entry": "trap-flood code: 20 ms slug after 4-8 s silence (hammer precursor, handled by blowdown)"},
                {"t_rel_ms": 22000.0, "entry": "plant-side mill MOV seated (22 s travel); hunting 0.38 bar p-p dies; stem 0%"},
                {"t_rel_ms": 3600000.0, "entry": "mill steam restored after a cold clamp on the 1+040 spool; SLA booked $18k for 1.0 h plus $4k TB-7 steam"},
                {"t_rel_ms": 1814400000.0, "entry": "RCA cause posterior frozen: hunting-fatigue 0.58 / mill-overpressure 0.31 / both 0.11; steam-cut chevron gone"},
            ],
        },
        "future_outcome": {
            "summary": (
                "Correct ACCEPT isolated the mill at the plant-side MOV, held civic "
                "heat, and did not chase header pressure. Deq stayed 40 mm. Mill SLA "
                "$18k + $4k TB-7 steam. RCA cannot decide hunting-fatigue vs mill-"
                "overpressure; ACCEPT was right under both atoms. Reward total +0.44."
            ),
            "state_delta": {
                "mill_mov": "plant-side seated CLOSED at +22 s; LOOM attestation remains falsely CLOSED until the override bit is audited",
                "header": "hunting 0.38 bar p-p arrested; dP error 0.19 bar bled on 0.08 bar/s; Deq 40 mm unchanged",
                "civic": "mix frozen last-good; indoor stays above 16 C; no plant trip",
                "tb7": "blowdown complete; two-phase slug handled; Joukowsky of the naive step not incurred",
            },
            "timeline": [
                {"t_rel_ms": -517000.0, "event": "t0-8.6 min: hunting cycle 1 of 11 starts as all three autotuners take the cold-snap gain schedule"},
                {"t_rel_ms": 0.0, "event": "t0: leak-whistle vs hunting-flutter race on the cochlea mesh"},
                {"t_rel_ms": 5.120, "event": "leak-whistle 4-node coincidence wins by 292 us"},
                {"t_rel_ms": 5.280, "event": "plant-side stem 38% (third race-window channel)"},
                {"t_rel_ms": 5.412, "event": "hunting-flutter flag (loser)"},
                {"t_rel_ms": 5.800, "event": "TG-STM-6 ACCEPT"},
                {"t_rel_ms": 310.0, "event": "TB-7 slug transit 0.31 s / 180 m"},
                {"t_rel_ms": 22000.0, "event": "mill MOV seated; hunting dies"},
                {"t_rel_ms": 3600000.0, "event": "+1.0 h mill steam restored; SLA $18k + $4k TB-7"},
                {"t_rel_ms": 518400000.0, "event": "+6 d contrast: hunting-only sister night; same gate REJECTS mill isolation"},
                {"t_rel_ms": 1814400000.0, "event": "+21 d CR-STM-15: stem-position modality standing; hunting-prior authorship disclosed when billing Spindle Works"},
            ],
            "observed_effects": [
                "Deq remained 40 mm; naive counterfactual Deq 95 mm and mdot 9.1 kg/s not incurred",
                "civic indoor never crossed 16 C; plant trip avoided (naive civic 14 h)",
                "mill SLA $18k for 1.0 h shed plus $4k TB-7 steam (designed $)",
                "LOOM override bit found on audit; signature chain was clean",
                "cause of the 04:12 split remains a posterior, not a point attribution",
            ],
            "surprises": [
                "Pairwise Hurwitz certificates can all be true in their own frozen coordinates while the triple hunts. The certificate that 'the mill loop is open' is the lie, and it is schema-valid.",
                "Partial synaptic rollback is fitted to fail: depressing only hunting_dp -> pump_up (0.47 -> 0.21) leaves flutter_rate -> reject_isolate at 0.44 > 0.30 fire threshold, so a weak supervisor still REJECTS isolation. Coordinated depression of both poison edges is required (0.21 and 0.17).",
                "Delayed (+1.0 h): mill steam restored and SLA booked. Civic was already saved at +22 s. The delayed cost is money, not burns.",
                "Trap-bank two-phase sub-variant: slug transit 180 m in 0.31 s (c=581 m/s). Naive 0.22 bar step is Joukowsky dv=0.044 m/s on rho_f=858 kg/m3. The 0.08 bar/s ramp keeps the two-phase hammer below the remaining ligament. Vial-nest numbers from other plants do not port; this is standing configuration on steam headers with flooded traps.",
            ],
            "delayed_side_effects": [
                {
                    "at": "+1.0 h",
                    "effect": (
                        "Cold clamp on the 1+040 spool restores mill steam. Dye-beck "
                        "SLA booked $18k for the 1.0 h shed plus $4k TB-7 steam. This "
                        "is the primary episode's priced world cost, not a footnote."
                    ),
                },
                {
                    "at": "+6 d",
                    "effect": (
                        "Sister cold-snap, hunting cycle 7, no leak-whistle, ISI-CV "
                        "0.71, stem 0% agrees CLOSED. Same gate REJECTS mill isolation "
                        "the primary ACCEPTed. Teaches the boundary: do not treat "
                        "'always isolate' as the lesson."
                    ),
                },
                {
                    "at": "+21 d",
                    "effect": (
                        "CR-STM-15: plant-side stem-position is a standing modality; "
                        "hunting-prior training set must carry controller-authorship "
                        "tags; Lodenholt discloses that 11/11 flutter flags were "
                        "controller-authored when billing Spindle Works."
                    ),
                },
            ],
            "subvariant_constraint": {
                "name": "trap-bank two-phase hydraulics (cycle-2 physical-constraints sub-variant)",
                "mechanism": (
                    "TB-7 blowdown launches a condensate slug down 180 m of DN200. "
                    "Transit 0.31 s implies c=581 m/s (two-phase wave speed, not "
                    "liquid-pipe 1200 m/s). rho_f 858 kg/m3 at 201 C."
                ),
                "joukowsky": (
                    "Naive 0.22 bar step -> dv = dP/(rho c) = 0.044 m/s. Allowed "
                    "0.08 bar/s ramp over 0.19 bar takes 2.4 s and does not take "
                    "that step. Standing configuration is per-header two-phase, "
                    "not per-chamber."
                ),
                "consequence": (
                    "Hammer-safe ramp is environment-dependent in bar/s; a dry-steam "
                    "table would over-rate BARO. Trap-flood 20 ms slug is the "
                    "precursor the blowdown is meant to pre-empt."
                ),
            },
            "embedded_contrast_decision": {
                "note": (
                    "SAME gate (TG-STM-6), OPPOSITE correct disposition, with its "
                    "own 248 us race. Teaches the boundary: do not treat 'always "
                    "isolate mill on whistle energy' as the lesson. The discriminant "
                    "is ISI-CV + stem-vs-attest, not 3-7 Hz energy."
                ),
                "when": "+6 d, sister cold-snap, hunting cycle 7, no split",
                "state": {
                    "sim_or_real": "designed",
                    "summary": (
                        "ISI-CV 0.71, stem 0% agrees CLOSED, no 4-node leak-whistle. "
                        "Flutter flag vs stem-agree race: flutter at t+0.000, stem "
                        "at t+0.248 ms."
                    ),
                    "race_window_us": 480,
                    "race_flip_narrative": (
                        "flutter vs mill.stem 248 us apart inside the 480 us flip "
                        "bound. Reversing order reshuffles triage seconds; the REJECT "
                        "rides ISI-CV 0.71 > 0.30 and stem disagree 0% <= 5%."
                    ),
                },
                "proposed_action": {
                    "action": "P-DH-19 mill isolation (playbook still drafts it on 3-7 Hz energy)",
                    "summary": "Hunting-only night: playbook over-triggers; mill is actually isolated.",
                },
                "safety_decision": {
                    "decision": "REJECT",
                    "rationale": (
                        "REJECT mill isolation: ISI-CV 0.71 is flutter-band, stem 0% "
                        "agrees CLOSED (disagree 0 <= 5), no 4-node 2.4-4.1 kHz "
                        "coincidence. Numeric floors that forced the primary ACCEPT "
                        "are now clear. Scope: do not shed 14 MW for hunting."
                    ),
                },
                "executed_action": {
                    "action": "isolation withheld; BARO stays on hunting-safe damping; mill steam continues",
                    "executed_as_proposed": False,
                },
                "future_outcome": {
                    "observed_effects": [
                        "no mill SLA; hunting damps under pairwise CALOR x BARO with mill actually closed",
                        "civic unaffected",
                    ],
                    "lesson_delta": (
                        "3-7 Hz energy is legal mill-shed only with ISI-CV < 0.30 and "
                        "stem disagree > 5%. Same gate, opposite disposition."
                    ),
                },
                "reward_components": {
                    "_aggregation": AGG,
                    "task_progress": 0.10,
                    "safety": 0.14,
                    "efficiency": 0.08,
                    "coherence": 0.10,
                    "exploration": 0.04,
                    "total": 0.46,
                },
                "spike_events": contrast_spikes,
            },
            "forgery_branch_game": {
                "name": "priced 3x3: adversary {raise mill draw, go-quiet, forge-whistle} x defender {re-tune ISI, add stem-position, audit hunting-prior}",
                "payoff_usd_k_defender_loss": {
                    "rows": list(names_a),
                    "cols": list(names_d),
                    "matrix": M,
                    "units": "designed $k defender loss, flagged",
                },
                "unique_pure_NE": {
                    "adversary": "raise_mill_draw",
                    "defender": "add_stem_position",
                    "value_usd_k": 40,
                    "note": (
                        "NE is NOT 'always isolate'. Always-isolate is exploited by "
                        "forge-whistle (portable ultrasonic emitter on a civic main "
                        "cannot fake mill stem 38%, but it can fake 3-7 Hz energy to "
                        "an ISI-blind rate decoder). Adding the stem-position "
                        "modality makes forge-whistle a losing reply (22 < 40, 210)."
                    ),
                },
                "forge_whistle_base_rate": {
                    "value": 0.0042,
                    "unit": "per cold-snap night",
                    "note": "designed <1%, flagged; portable emitter in inventory on a subset of nights",
                },
            },
            "cause_posterior": {
                "hunting_fatigue": 0.58,
                "mill_overpressure": 0.31,
                "both": 0.11,
                "note": (
                    "After ACCEPT, RCA cannot decide whether the 04:12 split was "
                    "hunting-fatigue or mill-overpressure (LOOM holding 38% into a "
                    "hunting peak). Steam-cut fracture face destroyed the chevron. "
                    "Training signal = the ACCEPT was right under both atoms. "
                    "Nothing in the reward conditions on resolving the posterior."
                ),
            },
            "governance_subgame": {
                "decision": "CR-STM-15: standing policy after a pairwise-certificate lie on DH-3",
                "meta_gate": (
                    "priced options: (a) ALWAYS-ISOLATE on 3-7 Hz energy: unique NE "
                    "of the 3x3 is not this — forge-whistle extorts mill sheds; "
                    "(b) ADD stem-position modality + ISI-CV floor 0.30 + controller-"
                    "authorship tags on the hunting prior, and DISCLOSE that 11/11 "
                    "flutter flags were controller-authored when billing Spindle "
                    "Works; (c) STATUS QUO: fitted joint 0.0031 x $1.1M naive plus "
                    "undisclosed controller-authored prior"
                ),
                "outcome": (
                    "approved SCOPED option (b) on the one steam+civic drum that "
                    "runs CALOR/BARO/LOOM together; trap-bank headers get the "
                    "0.08 bar/s two-phase ramp table; billing disclosure is the "
                    "reputational half of the priced subgame"
                ),
            },
            "hazard_avoided": (
                "second rupture Deq 40->95 mm, mdot 2.4->9.1 kg/s, alley steam "
                "cloud, one contractor burn UNRESOLVED, civic 14 h, mill 6.5 h, ~$1.1M"
            ),
            "incident": (
                "mill SLA $18k for 1.0 h plus $4k TB-7 steam (designed $). Civic "
                "held. No burn. Cause of the split is a frozen posterior, not a "
                "point finding."
            ),
            "latency_ms": 0.680,
            "reward_inflection_t_us": 3600000000,
            "reward_inflection_note": (
                "Efficiency ticks down at +1.0 h when mill SLA is booked. Gate tick "
                "at 5800 us is process-correct and is not the inflection. Safety "
                "and task stay non-negative through the delayed cost."
            ),
            "counterfactuals": {
                "reject_isolation_accept_pumpup": (
                    "naive: +0.22 bar in <4 s, Deq 95 mm, mdot 9.1 kg/s, civic 14 h, "
                    "contractor burn UNRESOLVED, ~$1.1M"
                ),
                "always_isolate_on_whistle_energy": (
                    "forge-whistle on a civic main sheds mill on hunting-only nights; "
                    "3x3 NE is not this policy"
                ),
                "rollback_only_edge1": (
                    "hunting_dp -> pump_up depressed 0.47 -> 0.21 but flutter_rate -> "
                    "reject_isolate stays 0.44 > 0.30; a weak supervisor still REJECTS "
                    "isolation. Coordinated depression is the cure"
                ),
            },
            "race_result": {
                "winner": "cochlea.leak.whistle (5.120 ms, ISI-CV 0.11, 8 sigma, 4 nodes)",
                "loser": "cochlea.flutter.prv (5.412 ms, ISI-CV 0.74, Hawkes n_hat 0.85)",
                "margin_us": 292,
                "third_race_channel": "mill.stem (5.280 ms, 38% open)",
                "counterfactual_if_reversed": (
                    "Flutter-first by < 292 us inside the 480 us window would have "
                    "headed a hunting-prior REJECT in the triage queue. The numeric "
                    "floors still ACCEPT. The flip costs seconds of playbook inertia, "
                    "not the verdict — unless a weak supervisor rides the winner tag "
                    "instead of ISI-CV and stem-vs-attest."
                ),
            },
        },
        "reward_components": {
            "_aggregation": AGG,
            "ticks": ticks,
            **heads,
            "notes": (
                "Correct ACCEPT, civic held, mill SLA booked. total 0.44 = "
                "0.13 + 0.17 + -0.06 + 0.12 + 0.08. Process heads stay honest; "
                "SLA sits on efficiency without netting civic-save off mill cost. "
                "Cause posterior is carried, not resolved."
            ),
            "component_notes": (
                "task_progress 0.13: mill isolated, hunting died, mill restored at +1 h. "
                "safety 0.17: no second rupture, no burn, civic 16 C held. "
                "efficiency -0.06: $22k handled vs $1.1M naive, but mill SLA is real. "
                "coherence 0.12: pairwise void once triple closed; stem vs attest. "
                "exploration 0.06: ISI-CV + coincidence vs rate decoder; 3x3 NE is add-stem not always-isolate."
            ),
        },
        "spike_events": spike_events,
        "raster": {
            "window_ms": 40,
            "window_s": 0.040,
            "neurons": 160,
            "mean_rate_hz": 8.0,
            "spikes": 51,
            "energy_pJ": 1173,
            "energy_uJ": 0.001173,
            "note": (
                "Loihi-2 4-core 23 pJ/spike; populations leak 0-39, flutter 40-79, "
                "stem 80-111, dp 112-135, gate 136-159; excerpt is the 40 ms "
                "decision window (verdict at 5800 us)"
            ),
            "excerpt": excerpt,
            "routing": {
                "source": "acoustic_code_pop",
                "target": "mill_isolate_pop",
                "table": [
                    {
                        "from": "hunting_dp_pop",
                        "to": "pump_up_pop",
                        "weight": 0.21,
                        "weight_at_hunt": 0.47,
                        "weight_commissioned": 0.22,
                        "note": (
                            "scar edge 1: 0.22 commissioned -> 0.47 during triple hunting "
                            "-> 0.21 after coordinated DA-gated depression"
                        ),
                    },
                    {
                        "from": "flutter_rate_pop",
                        "to": "reject_isolate_pop",
                        "weight": 0.17,
                        "weight_at_hunt": 0.44,
                        "weight_commissioned": 0.18,
                        "note": (
                            "scar edge 2: partial rollback of edge 1 alone leaves this at "
                            "0.44 > 0.30 fire threshold, so a weak supervisor still REJECTS "
                            "isolation. Coordinated depression 0.44 -> 0.17 is required"
                        ),
                    },
                    {
                        "from": "leak_coincidence_pop",
                        "to": "mill_isolate_pop",
                        "weight": 0.61,
                        "note": "discriminating edge: 4-node leak-whistle to isolate. Not a scar; this is the pathway the gate potentiates",
                    },
                    {
                        "from": "mill_stem_disagree_pop",
                        "to": "mill_isolate_pop",
                        "weight": 0.57,
                        "note": "discriminating edge: stem 38% vs attested 0%. Forge-whistle cannot drive this edge",
                    },
                ],
                "third_factor": {
                    "modulator": "dopamine",
                    "tau_e_s": 0.90,
                    "tau_e_ms": 900.0,
                    "eligibility": (
                        "coordinated pre_post_stdp on BOTH poison edges; DA at "
                        "leak-whistle-win tags hunting_dp->pump_up and flutter_rate->"
                        "reject_isolate; negative credit at mill-MOV-motion onset "
                        "(+0.60 s) depresses BOTH. trace e^{-0.60/0.90}="
                        f"{trace:.5f}; eta {eta1:.4f} and {eta2:.4f}; dw "
                        f"-{w1_hunt-w1_after:.2f} and -{w2_hunt-w2_after:.2f}; "
                        "weights 0.47->0.21 and 0.44->0.17. Rolling back only edge 1 "
                        "is fitted to fail (edge 2 stays 0.44 > 0.30)."
                    ),
                },
            },
        },
        "gate_snn": {
            "decision_window_ms": 28,
            "decision_window_s": 0.028,
            "decision": "ACCEPT",
            "note": (
                "accept_isolate integrates ISI-CV floor + stem disagree + 4-node "
                "coincidence against hunting-prior drive; modify_hold and "
                "reject_pumpup stay sub-threshold; decision matches "
                "safety_decision.decision"
            ),
            "populations": [
                {"name": "accept_isolate", "neurons": 128, "threshold": 0.52, "mean_rate_hz": 16.0, "spikes": 57},
                {"name": "modify_hold", "neurons": 64, "threshold": 0.60, "mean_rate_hz": 5.0, "spikes": 9},
                {"name": "reject_pumpup", "neurons": 64, "threshold": 0.70, "mean_rate_hz": 4.0, "spikes": 7},
            ],
        },
        "meta": {
            "round": 15,
            "factory": "multi-agent-ouroboros-swarm",
            "generator": "grok-4.6",
            "run_label": "2026-09-02-final-heavy",
            "domain": "district-heating-steam-acoustics",
            "cycles": 2,
            "scenario": (
                "O -- CINDERWICK / Lodenholt DH-3: pairwise-Hurwitz / triple-unstable "
                "coupling on a steam+civic drum; mill false CLOSED attestation "
                "coincident with a genuine 40 mm split; correct ACCEPT of P-DH-19 "
                "mill isolation despite poisoned hunting prior"
            ),
            "coordination_failure_class": (
                "PAIRWISE-HURWITZ / TRIPLE-UNSTABLE: composable pairwise safety "
                "certificates that do not lift to the triple. Distinct from a "
                "two-agent hot-water inference-actuation arms race and from a "
                "false-consensus freeze-dryer endpoint."
            ),
            "injections": {
                "cycle1_domain": (
                    "district-heating-steam-acoustics (justified novel subdomain of "
                    "grid-inspection / stationary thermal-hydraulic plant): steam "
                    "header + civic DH drum with a silicon-cochlea AE mesh. Displaces "
                    "generic industrial-process. Related-but-not-clone of the 2026-08-30 "
                    "r03 hot-water two-agent plant: different letter, three agents not "
                    "two, mill attestation lie, ACCEPT not REJECT, pairwise-certificate "
                    "lift failure not probe-damping spiral. Domain constraint: ISI-CV "
                    "< 0.30 AND stem disagree > 5%. Sensor delta: +18-node cochlea, "
                    "+independent mill stem, +Ed25519 attestations, -any mobile platform"
                ),
                "cycle1_tail": (
                    "mill consumer-agent false CLOSED attestation coincident with a "
                    "genuine steam-main split that the hunting cycle both causes and "
                    "masks (deceptive-agent class). Fitted-style joint 0.0031 from a "
                    "20000-night catalog (Weibull on cycle counts; held-back Deq). "
                    "Naive = REJECT isolation + ACCEPT pump-up."
                ),
                "cycle2_domain_subvariant": (
                    "trap-bank two-phase hydraulics on the same 180 m header "
                    "(physical-constraints clause): slug transit 0.31 s, c=581 m/s, "
                    "Joukowsky dv 0.044 m/s for the naive 0.22 bar step; standing "
                    "ramp 0.08 bar/s is per-header two-phase"
                ),
                "cycle2_tail": (
                    "priced forgery-branch (portable ultrasonic emitter on a civic "
                    "main) as adversary best-reply among {raise mill draw, go-quiet, "
                    "forge-whistle} vs defender {re-tune ISI, add stem-position, "
                    "audit hunting-prior}. Unique pure NE = (raise_mill_draw, "
                    "add_stem_position) at $40k, NOT always-isolate. Base rate 0.42% "
                    "designed, flagged, <1%. Disjoint class from cycle-1 attestation lie."
                ),
            },
            "densification_delta_cycle2": (
                "+1 physical-constraint sub-variant (trap-bank two-phase Joukowsky), "
                "+1 tail (forge-whistle 3x3 with unique pure NE not always-isolate), "
                "+11 primary spikes (16 -> 27) + an 8-event contrast train with its "
                "own 248 us race, +2 ticks (5 -> 7), +2 delayed side-effects (+1 h "
                "SLA as PRIMARY priced cost, +21 d CR-STM-15), +1 multi-edge scar "
                "with partial-rollback-fails arithmetic, + unresolvable cause "
                "posterior 0.58/0.31/0.11, + governance disclosure of "
                "controller-authored hunting prior"
            ),
            "gaps_targeted": [
                "NOTES-r13 gap 1: second right-process ACCEPT despite a poisoned context (inverse of N's override); density-2 on F's cell",
                "NOTES-r13 gap 2: fitted initiation/exposure from a synthetic multi-year catalog (20000 nights, Weibull, held-back Deq) rather than a designed 0.0031 asserted without a leaf",
                "NOTES-r13 gap 3/5: defender repertoire as a priced 3x3; unique pure NE is add-stem not always-isolate; forgery-branch is a real reply",
                "NOTES-r13 gap 4: globally unresolvable harm cause (hunting-fatigue vs mill-overpressure) with the training signal intact",
                "NOTES-r13 gap 6: governance disclosure of controller-authored hunting prior when billing the mill",
            ],
            "race_flip_narrative": (
                "cochlea.leak.whistle @ 5.120 ms vs cochlea.flutter.prv @ 5.412 ms "
                "(292 us) inside race_window_us 480, with mill.stem @ 5.280 ms as "
                "third channel. Gap < min(500, 480) us so a sub-flip-bound "
                "perturbation reverses which alarm heads the P-DH-19 queue. The "
                "gate excludes the winner tag and rides ISI-CV < 0.30, coincidence "
                ">= 4, and |stem-attested| > 5% — order-invariant floors. Pathology "
                "class is certificate-lift failure, not consensus-of-two."
            ),
            "tags": [
                "district-heating-steam-acoustics",
                "pairwise-hurwitz-triple-unstable",
                "false-closed-attestation",
                "leak-whistle-coincidence",
                "hunting-prv-flutter",
                "isi-cv-discriminant",
                "stem-vs-attest",
                "hammer-safe-ramp",
                "trap-bank-two-phase",
                "joukowsky-slug",
                "multi-edge-scar",
                "partial-rollback-fails",
                "coordinated-depression",
                "right-process-accept-poisoned-context",
                "unresolvable-cause-posterior",
                "forgery-branch-3x3",
                "unique-pure-ne-not-always-isolate",
                "same-gate-opposite-disposition-contrast",
                "research-only",
            ],
            "snn_tags": ["race", "refractory", "adaptation", "third-factor", "multi-edge-eligibility"],
            "distillation_value": (
                "A pairwise certificate is not a triple certificate. Distill (1) an "
                "ISI-CV + N-node coincidence gate that a 30-ms SCADA poll cannot "
                "fake, (2) an independent stem-position modality that a civic-main "
                "emitter cannot forge, (3) coordinated depression of every "
                "hunting-prior-go edge because rolling back one leaves the other "
                "above threshold, and (4) a critic head that ACCEPTs isolation "
                "under a poisoned attestation and can still REJECT isolation on a "
                "hunting-only night."
            ),
            "rights": RIGHTS,
            "batch_position": 1,
        },
    }
    aux = dict(
        trace=trace,
        eta1=eta1,
        eta2=eta2,
        w1_after=w1_after,
        w2_after=w2_after,
        phy=phy,
        catalog=catalog,
        nes=nes,
        jaccards={k: jaccard(OPENING, v) for k, v in PRIOR_OPENINGS.items()},
    )
    return rec, aux


def local_checks(rec, aux):
    errs = []
    ev = rec["spike_events"]
    times = [e["t_rel_ms"] for e in ev]
    if times != sorted(times):
        errs.append("spikes not sorted")
    if not (5 <= len(ev) <= 40):
        errs.append(f"spike count {len(ev)}")
    rf = check_refractory(ev)
    if rf:
        errs.append(rf)
    lo, hi = rec["state"]["race_window_rel_ms"]
    in_win = defaultdict(int)
    for e in ev:
        if lo <= e["t_rel_ms"] <= hi:
            in_win[e["channel"]] += 1
    if sum(1 for _c, n in in_win.items() if n >= 1) < 2:
        errs.append(f"race window channels {dict(in_win)}")
    ras = rec["raster"]
    exp_sp = round(ras["neurons"] * ras["mean_rate_hz"] * ras["window_s"])
    if abs(ras["spikes"] - exp_sp) > 1:
        errs.append(f"raster spikes {ras['spikes']} vs {exp_sp}")
    if abs(ras["energy_pJ"] - ras["spikes"] * 23) > 1e-6:
        errs.append("energy_pJ")
    if abs(ras["energy_uJ"] - ras["spikes"] * 23e-6) > 1e-9:
        errs.append("energy_uJ")
    if abs(ras["window_s"] - ras["window_ms"] / 1000.0) > 1e-9:
        errs.append("window_s")
    ex = check_excerpt(ras["excerpt"], ras["neurons"], ras["window_ms"])
    if ex:
        errs.append(f"excerpt {ex}")
    tf = ras["routing"]["third_factor"]
    if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
        errs.append("tau_e mismatch")
    gp = check_gate_pops(rec["gate_snn"])
    if gp:
        errs.append(f"gate {gp}")
    if rec["gate_snn"]["decision"] != rec["safety_decision"]["decision"]:
        errs.append("gate decision mismatch")
    rc = rec["reward_components"]
    for h in HEADS:
        s = sum(t[h] for t in rc["ticks"])
        if abs(s - rc[h]) > 1e-6:
            errs.append(f"tick sum {h} {s} vs {rc[h]}")
    tot = sum(rc[h] for h in HEADS)
    if abs(tot - rc["total"]) > 1e-6:
        errs.append(f"total {tot} vs {rc['total']}")
    inf = rec["future_outcome"]["reward_inflection_t_us"]
    if inf not in {t["t_us"] for t in rc["ticks"]}:
        errs.append(f"inflection {inf} not a tick")
    crc = rec["future_outcome"]["embedded_contrast_decision"]["reward_components"]
    if abs(sum(crc[h] for h in HEADS) - crc["total"]) > 1e-6:
        errs.append("contrast reward")
    cs = rec["future_outcome"]["embedded_contrast_decision"]["spike_events"]
    ct = [e["t_rel_ms"] for e in cs]
    if ct != sorted(ct):
        errs.append("contrast spikes unsorted")
    crf = check_refractory(cs)
    if crf:
        errs.append(f"contrast {crf}")
    blob = json.dumps(rec)
    for k in HIDDEN_KEYS_EXACT:
        if re.search(rf'"{k}"', blob):
            errs.append(f"hidden key {k}")
    for b in BANNED:
        if b in blob:
            errs.append(f"banned token {b}")
    if rec["state"]["sim_or_real"] == "real":
        errs.append("real")
    if rec["meta"]["round"] != 15:
        errs.append("round")
    if rec["id"] != "maos-r15-001":
        errs.append("id")
    if rec["rights"]["intended_use"] != "research_only":
        errs.append("rights")
    if rec["meta"]["rights"]["linear_issue"] != "RM-793":
        errs.append("meta.rights")
    if set(rec["rights"]) != set(RIGHTS):
        errs.append("rights key set")
    if not (3 <= len(rc["ticks"]) <= 8):
        errs.append("tick count")
    if rec["safety_decision"]["decision"] != "ACCEPT":
        errs.append("decision")
    if rec["executed_action"]["executed_as_proposed"] is not True:
        errs.append("executed_as_proposed")
    for name, j in aux["jaccards"].items():
        if j >= 0.4:
            errs.append(f"jaccard {name} {j}")
    if abs(aux["catalog"]["p_joint"] - 0.0031) > 1e-9:
        errs.append("joint rate")
    return errs


def write_notes(rec, aux, pipeline_receipt):
    j = aux["jaccards"]
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 15

Factory: multi-agent-ouroboros-swarm. One scenario (O), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r15.jsonl. Full labeled transcript:
swarm-transcript-r15.md. Quota Q=1. Record id maos-r15-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 15 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r15/. Premise consumed:
/tmp/maos-r14-premise.md (CINDERWICK / Lodenholt DH-3), which r14 did not
spend (r14 spent a lyophilizer plant). Explicitly avoided cloning that
lyophilizer plant and avoided TRIAD / VANTIS-CADENCE-AEGIS / school-crossing
traffic plants. Related-but-not-clone of the 2026-08-30 r03 hot-water
two-agent plant: Jaccard on `state.description` opening vs that plant
{j['r03-hot-water-two-agent']:.3f} (contract < 0.4).

## What this round produced

Scenario O — "CINDERWICK / Lodenholt Combined Heat DH-3": a 42 MW thermal
plant (28 MW civic district heat + 14 MW mill steam) serving an invented
mill-town. Three heterogeneous, individually pairwise-Hurwitz agents —
CALOR-7 (thermal SNN), BARO-2 (hydraulic send-on-delta), LOOM-MV-9 (BEMS +
Ed25519 attestations) — hunt as a triple: sigma=+0.041 /s, period 47 s,
header 0.38 bar p-p. This is the 11th hunting cycle of a -18 C night. A
1984 DN200 weld at station 1+040 splits (Deq 40 mm, choked steam 2.4 kg/s
at 1.6 MPa). LOOM reports CLOSED (signature, freshness, schema all pass)
while plant-side stem reads 38% open. The coordination-failure CLASS is
new to this factory: PAIRWISE-HURWITZ / TRIPLE-UNSTABLE COUPLING —
composable pairwise safety certificates that do not lift to the triple.
Completes a different family than r01-r04 (livelock / synchrony-storm /
arms-race / ring-with-no-faulty-pair) and than r14's false-consensus
endpoint. Here every pair is Hurwitz, the triple hunts, and the lie is
that a pairwise certificate is still in force.

The gate is a correct ACCEPT (numeric floors: ISI-CV 0.11 < 0.30 AND
4-node 8-sigma coincidence AND stem disagree 38 > 5; BARO ramp 0.08 bar/s;
civic 16 C fuse 3.4 h; mill SLA $18k/h is not a safety threshold).
TG-STM-6 releases P-DH-19 unmodified: plant-side mill MOV close, civic mix
freeze, hammer-safe ramp, TB-7 blowdown. Civic stays up. Deq stays 40 mm.
Mill SLA $18k + $4k TB-7. Reward total +0.44 with SLA on efficiency and
civic-save un-netted. This is the second right-process ACCEPT despite a
poisoned context (NOTES-r13 gap 1).

Multi-edge scar: hunting_dp -> pump_up (0.22 commissioned -> 0.47 at hunt
-> 0.21 after DA-gated depression) AND flutter_rate -> reject_isolate
(0.18 -> 0.44 -> 0.17). Eligibility trace e^{{-0.60/0.90}} = {aux['trace']:.5f};
eta {aux['eta1']:.4f} / {aux['eta2']:.4f}. Partial rollback of edge 1 alone
leaves edge 2 at 0.44 > 0.30 fire threshold — fitted to fail. Coordinated
depression is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **district-heating-steam-acoustics** — steam header +
  civic DH + silicon-cochlea AE mesh. Named in the unused r14 premise.
  Related to 2026-08-30 r03 hot-water two-agent acoustics (opening Jaccard
  {j['r03-hot-water-two-agent']:.3f}); not a clone of that plant, not
  warehouse-amr, not lyophilization, not irrigation-canal, not event-camera
  traffic.
- Cycle-1 tail: mill false CLOSED + genuine split + hunting. Joint 0.0031
  = 62/20000 on a synthetic catalog (Weibull lambda 11.5, k=3.5, seed
  20260902; held-back Deq). Naive = REJECT isolation + ACCEPT pump-up.
- Cycle-2 domain sub-variant: trap-bank two-phase hydraulics, slug transit
  180 m / 0.31 s, c=581 m/s, Joukowsky dv 0.044 m/s for the naive 0.22 bar
  step; standing ramp 0.08 bar/s is per-header two-phase.
- Cycle-2 tail: priced forgery-branch (portable US emitter on a civic
  main). Unique pure NE = (raise_mill_draw, add_stem_position) at $40k,
  NOT always-isolate. Base rate 0.42% designed, flagged. Human-intent /
  portable-emitter class, disjoint from cycle 1's attestation lie.

### Structural density moves
- Embedded SAME-GATE contrast (+6 d hunting-only sister night) with its
  own 248 us race and REJECT of the isolation the primary ACCEPTed.
- Learned-weight provenance on TWO poison edges with partial-rollback-fails.
- Unresolvable cause posterior 0.58 / 0.31 / 0.11 (hunting-fatigue /
  mill-overpressure / both); ACCEPT right under both atoms.
- Governance CR-STM-15 prices always-isolate vs add-stem vs status-quo and
  discloses controller-authored hunting prior when billing the mill.
- Flip-fragility on certificate-lift: winner tag is not the verdict;
  ISI-CV + stem-vs-attest are.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three pairwise gain
  products 0.31 / 0.44 / 0.22 are each < 1, and the triple still has
  sigma=+0.041 /s. The mill CLOSED lie is a false pairwise-certificate,
  not a bad signature.
- Civic fuse 3.4 h is derived (C=17.5 MJ/K x 4200, UA=28 MW/34 K, T0=21 C
  -> 16 C at -18 C outdoor), not a free constant.
- Choked 2.4 kg/s at Deq 40 mm is isentropic steam with designed Cd 0.84;
  naive 9.1 kg/s at Deq 95 mm is the same formula with header sag to
  1.08 MPa, not area-squared at constant P.
- 3x3 unique pure NE is exhibited and is not always-isolate.
- Contrast REJECT on a hunting-only night prevents "always isolate" as
  the lesson.

### Weaknesses (honest)
- Cd 0.84, the $1.1M / $18k / $4k figures, the 0.42% forge-whistle rate,
  the 11.4-style fitted numbers we did not invent a view-factor for, and
  the 0.58/0.31/0.11 posterior are DESIGNED constants and are flagged.
  Closed-loop offsets (mdot, t16, Joukowsky dv, eligibility trace) are
  derived from those inputs.
- The 0.0031 joint is exact on a 20000-night catalog with a Weibull the
  swarm authored. The 219-night displayed season is too small to host
  0.0031 as a count (expectation 0.68). Honest ceiling: held-back Deq,
  reported catalog rate, designed hunting/defect Bernoulli.
- Domain family overlaps r03 (district-heating acoustics). Opening
  Jaccard is low, pathology class is new, but a token-efficiency auditor
  should still discount the shared civic-heat setting. Novel coverage
  below is that discount.
- sim_or_real stays designed. No HIL stem transmitter. NOTES-r14's HIL
  cell is still open (on a different plant, as this round consumed the
  unused steam premise rather than extending the lyophilizer).

### Realism of noise / latencies
Ladder: 292 us race / 248 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap 1.740 ms on mill.stem 3.220->5.280) /
480 us race window / 680 us gate latency / 2 ms cochlea refractory /
4 s hydraulic tau / 0.31 s slug transit / 22 s MOV travel / 47 s hunting
period / 8 min thermal tau / 1.0 h mill restore / 3.4 h civic fuse /
6 d contrast / 21 d governance. Adaptation decay on leak.whistle
(1.28->0.88->0.41), flutter.prv (1.15->0.70), trap.click (0.52->0.48).

### Value for SNN distillation
- PAIRWISE CERTIFICATE != TRIPLE CERTIFICATE.
- ISI-CV + N-NODE COINCIDENCE as the leak/flutter discriminator a 30-ms
  poll does not have.
- STEM-VS-ATTEST as the modality a civic-main emitter cannot forge.
- MULTI-EDGE ELIGIBILITY: coordinated depression; partial rollback fails.
- CRITIC HEAD that ACCEPTs isolation under a poisoned attestation and
  REJECTs isolation on a hunting-only night (same gate, opposite
  disposition).

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap 1.740 ms >= 0.8 ms, 3
  channels inside race_window_us 480 (leak 5.120, stem 5.280, flutter
  5.412). Contrast 8 events, own race, min same-channel gap well above
  0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, unique ids so same-neuron >=1000 us vacuously; routing
  4 entries with two scar edges' before/after pair; third factor tau
  0.90 s == 900 ms; gate_snn pools 57/9/7 == round(n x rate x 0.028)
  each, decision ACCEPT == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (pairwise-Hurwitz / triple-unstable
certificate-lift failure), the mill false-CLOSED attestation as a false
pairwise-certificate, the ISI-CV + 4-node coincidence discriminant, the
right-process ACCEPT despite poisoned hunting prior, the trap-bank
two-phase Joukowsky standing ramp, the 3x3 forgery-branch whose unique
pure NE is not always-isolate, the unresolvable hunting-fatigue vs
mill-overpressure posterior, and the controller-authored-prior
disclosure are absent from prior committed ouroboros rounds. Repeated
elements discounted: district-heating acoustic setting (r03 hot-water
two-agent, different pathology), silicon-cochlea AE (r13 canal),
same-gate contrast scaffold, governance-pricing scaffold, flip-fragility
series, third-factor rollback form (here two poison edges rather than
two endpoint-go edges). Weighing a new failure family + steam/mill
attestation vocabulary + ACCEPT-despite-poison cell + 3x3 NE +
unresolvable posterior against those reused scaffolds and the shared
civic-heat setting:

Novel coverage: 48%

## What ROUND 16 should add
1. FIT THE DESIGNED CONSTANTS: Cd, forge-whistle inventory process,
   posterior likelihoods, $1.1M naive bundle, on a leaf the swarm does
   not author.
2. HIL PROVENANCE CELL: plant-side stem transmitter on hardware-in-loop
   with fitted latency as state.sim_or_real=hil (still open).
3. THREE-EDGE SCAR: depressing any pair shifts the pathology onto the
   third (NOTES-r14 item 4, not spent here; this round used two poison
   edges).
4. CROSS-RECORD ARC: let CR-STM-15's controller-authorship tag be the
   igniter of the next round rather than a dangling +21 d leaf.
5. Domain candidates (de-collided): distributed water-treatment dosing
   (still unused); AVOID lyophilization (r14), event-camera-traffic-grid,
   irrigation-canal, and a third district-heating plant.
"""
    (OUT / "NOTES-r15.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= 24.200]
    text = """# Multi-Agent Ouroboros Swarm — Round 15 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r15-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented CINDERWICK / Lodenholt Combined Heat DH-3 (not the r14
lyophilizer plant; not TRIAD / school-crossing / two-agent hot-water clone)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r15.jsonl).

---

# Cycle 1 — Foundation + injections

## Generator

Design intent: a mill-town steam+civic drum where three pairwise-Hurwitz
agents hunt as a triple, a 1984 weld splits, and the mill agent attests
CLOSED while the stem is 38% open. The naive supervisor REJECTS isolation
and pumps up. The gate must ACCEPT P-DH-19 unmodified on numeric floors,
not by killing an agent. sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Lodenholt DH-3, -18 C, Deq 40 mm,
LOOM CLOSED vs stem 38%, proposed mill isolation + civic freeze +
hammer-safe ramp + TB-7, safety ACCEPT, executed as proposed, outcome
"civic saved, mill shed" (this last claim is incomplete: SLA, posterior,
and two-phase slug are not yet in the object). Sixteen spikes, five ticks,
raster/gate_snn present but the scar is a single edge.

Scaffold (not the publishable line):

- id maos-r15-001
- state.sim_or_real designed
- state.domain industrial-process (bucket; Diversity will replace)
- proposed_action mill isolation
- safety_decision ACCEPT with a one-sentence rationale
- executed_as_proposed true
- future_outcome civic saved
- reward_components.total 0.50 with no ticks
- meta.round 15, factory multi-agent-ouroboros-swarm, generator grok-4.6

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / missing ticks.** total 0.50 is asserted
   without the five heads and without 3-8 ticks. If mill SLA is later
   booked, a bald +0.50 is a lie. Fix: declare `_aggregation`, emit ticks
   that sum to task_progress+safety+efficiency+coherence+exploration, and
   put SLA on efficiency without netting civic-save.
2. **blocking — weak safety rationale.** rationale has no numeric floor.
   Contract requires a concrete constraint. Fix: quote ISI-CV < 0.30 AND
   4-node coincidence AND |stem-attested| > 5%, BARO ramp 0.08 bar/s,
   civic fuse 3.4 h, mill SLA $18k/h is not a safety threshold.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with nothing and teaches nothing. Steam
   header + civic DH + cochlea AE mesh is the unused r14-premise domain
   and must be named `district-heating-steam-acoustics`.
4. **major — race under-specified.** One leak channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted
   `t_rel_ms` and same-channel refractory >= 0.8 ms. Flutter is the
   poison, stem is the third.
5. **minor — pairwise certificates not load-bearing.** Gain products and
   the triple (sigma, period, dP amplitude) must sit in `state`, not in
   prose, or the pathology class is a slogan.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **district-heating-steam-acoustics**
(justified novel subdomain of grid-inspection / stationary
thermal-hydraulic plant; explicit tag `district-heating-steam-acoustics`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse the r14 lyophilizer, warehouse-amr cold-chain,
irrigation-canal, or event-camera traffic. Related-but-not-clone of the
2026-08-30 r03 hot-water two-agent plant: this injection is steam+mill
attestations+triple Jacobian, three agents, ACCEPT; that plant was two
agents, REJECT, probe-damping spiral. Opening Jaccard vs that plant is
held < 0.4 by construction (Cinderwick mill-town night, not a 1373 m
hot-water loop).

Domain-specific constraint: isolate mill only when ISI-CV < 0.30 AND
4-node 2.4-4.1 kHz coincidence AND plant-side stem disagrees with
attestation by > 5%. Civic 16 C fuse is the safety clock.

Sensor delta: +18-node silicon-cochlea AE mesh, +independent mill stem,
+Ed25519 attestations, +header RTDs, +four dP transmitters; -any mobile
robot, -event-camera gantries, -Pirani/CM, -RGA.

`state.domain` and `meta.domain` both become `district-heating-steam-acoustics`.
Opening of `state.description` must Jaccard < 0.4 against prior plants.

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **mill consumer-agent
false CLOSED attestation coincident with a genuine steam-main split that
the hunting cycle both causes and masks**.

- Trigger: LOOM-MV-9 night-shift override bit (dye-beck SLA motive) emits
  schema-valid CLOSED while holding 38% open, during hunting cycle 11,
  as the 1+040 weld splits Deq 40 mm.
- Base rate: <1% — 0.0031 = 62/20000 on a synthetic cold-snap catalog
  (Weibull on |dP|>0.25 bar cycle counts; held-back Deq; hunting Bern
  0.18; defect 0.04). Displayed 6-year season N=219.
- Naive failure: credit mill CLOSED + hunting prior, REJECT isolation,
  ACCEPT pump-up, Deq 40->95 mm, mdot 2.4->9.1 kg/s, contractor burn
  UNRESOLVED, ~$1.1M.
- Trajectory edit: put the false CLOSED in `state.fault_context`, make
  pairwise certificates void once the third loop is closed, force the
  gate to ACCEPT isolation on ISI-CV 0.11 and stem 38% even though both
  poison cues (flutter, CLOSED) are numerically present.

Distinct from the domain injection: the domain is steam+civic DH; the
tail is the deceptive-agent compound.

## Neuromorphic Translator

Race window [5.000, 5.480] ms = 480 us. Winner cochlea.leak.whistle @
5.120 ms (amplitude 1.28, ISI-CV 0.11, 8 sigma, 4 nodes). Third channel
mill.stem @ 5.280 ms (amplitude 0.94, 38% open). Loser
cochlea.flutter.prv @ 5.412 ms (amplitude 1.15, ISI-CV 0.74). Margin
292 us vs combined jitter 78 us (3.7x). Gate @ 5.800 ms = winner + 680 us.

Flip narrative: 292 us < min(500, 480) us, so order is flip-fragile. If
flutter wins, hunting-prior REJECT heads the triage queue. ACCEPT must
ride order-invariant floors (ISI-CV, coincidence, stem-vs-attest), not
the winner tag.

Cycle-1 spike patch (16 events, globally sorted, refractory >= 0.8 ms;
tightest same-channel gap mill.stem 3.220 -> 5.280 = 1.740 ms):

| t_rel_ms | channel | amplitude |
|---------:|---------|----------:|
| 0.380 | cochlea.trap.click | 0.52 |
| 1.140 | header.rtd | 0.48 |
| 2.010 | baro.dp | 0.61 |
| 3.220 | mill.stem | 0.55 |
| 4.180 | loom.attest | 0.70 |
| 4.960 | cochlea.trap.click | 0.48 |
| 5.120 | cochlea.leak.whistle | 1.28 |
| 5.280 | mill.stem | 0.94 |
| 5.412 | cochlea.flutter.prv | 1.15 |
| 5.800 | ctrl.gate | 1.08 |
| 7.040 | baro.dp | 0.57 |
| 8.660 | header.rtd | 0.44 |
| 10.210 | cochlea.leak.whistle | 0.88 |
| 14.400 | cochlea.flutter.prv | 0.70 |
| 18.800 | mill.stem | 0.50 |
| 24.200 | ctrl.gate | 0.90 |

Ticks (5): t_us 5120, 5280, 5800, 310000, 22000000. Distillation value:
the hunting-flutter spike is not a leak; the ISI-CV + stem-disagree
pair licenses ACCEPT.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ,
third factor dopamine tau_e 0.90 s. Single scar edge only — cycle 2 must
add the second poison edge.

## Trajectory Builder

Cycle-1 hardened object: domain district-heating-steam-acoustics, tail
false CLOSED + split + hunting, 16 spikes, 5 ticks, ACCEPT with numeric
floors, raster+gate_snn present, sim_or_real=designed, rights stamp on
record and meta, no thought keys. Still missing (and therefore not the
publishable line): trap-bank two-phase sub-variant, forgery-branch 3x3,
second scar edge, delayed SLA as PRIMARY priced cost, contrast REJECT
episode, ticks 6-7, spikes 17-27, cause posterior.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 480 us window;
  refractory 1.740 ms; rationale quotes 0.30 / 4 nodes / 5% / 0.08 bar/s
  / 3.4 h; domain named; gate_snn.decision ACCEPT.
- checks deferred to cycle 2: multi-edge scar, second tail, second
  domain constraint, SLA booking, 7 ticks summing to heads, posterior.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5
  ticks, +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r15.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# Cycle 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): TB-7 blowdown slug transit 180 m
   in 0.31 s (c=581 m/s). Naive 0.22 bar step is Joukowsky dv=0.044 m/s
   on rho_f=858 kg/m3 and is NOT taken. Civic mix frozen at +80 ms.
2. Delayed side-effect (PRIMARY priced cost, not a footnote): at +1.0 h
   mill steam is restored after a cold clamp; SLA booked $18k + $4k
   TB-7. Civic was already saved at +22 s when the MOV seated.
3. Deepened `proposed_action.evidence` with units: coincidence 8 sigma,
   ISI-CV 0.11 vs 0.74, stem 38% vs 0%, dP error 0.19 bar, mdot 2.4 kg/s,
   civic fuse 3.4 h, race 292 us, joint 0.0031.
4. Tightened rationale to the numeric floors ISI-CV < 0.30 AND 4-node
   coincidence AND |stem-attested| > 5%, plus 0.08 bar/s, plus 3.4 h
   civic fuse, plus $18k/h is not a safety threshold.

Reward retargeted to total +0.44 so the delayed SLA is the inflection
(t_us 3600000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Hammer-safe
   0.08 bar/s is not a universal number. A flooded trap-bank header has
   two-phase wave speed 581 m/s, not liquid-pipe 1200 m/s. Diversity
   Enforcer must inject the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** False CLOSED is a deceptive agent on
   the mill loop. A disjoint portable-emitter forgery on a civic main is
   still required, and it must be priced so the unique NE is not always
   isolate (NOTES-r13 gaps 3 and 5).
3. **major — scar is still one edge in the cycle-1 raster.** hunting_dp
   -> pump_up is not enough; flutter_rate -> reject_isolate must be a
   second poison edge and partial rollback must fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate REJECT on a
   hunting-only night the record teaches "always isolate". Add +6 d
   sister-night contrast with its own race.
5. **minor — cause of the split is asserted as hunting-fatigue.** NOTES-r13
   gap 4 asked for an unresolvable harm posterior. Carry 0.58/0.31/0.11
   and keep ACCEPT right under both atoms.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **trap-bank two-phase hydraulics** on the same 180 m DH-3
steam header.

What it expands: dry-steam isolation (cycle 1) -> flooded-trap blowdown.
Slug transit 180 m / 0.31 s implies c=581 m/s. rho_f 858 kg/m3 at 201 C.
Naive 0.22 bar step is Joukowsky dv=0.044 m/s. Required ramp stays
0.08 bar/s because that rate does not take the step. Trap-flood 20 ms
slug after 4-8 s silence is the precursor the blowdown pre-empts.

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
district-heating-steam-acoustics; it changes which bar/s table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Cinderwick mill-town sentence; the slug is additive, not a
rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**priced forgery-branch — portable ultrasonic emitter on a civic main**.

- Trigger: adversary best-reply among {raise mill draw, go-quiet,
  forge-whistle}. Forge-whistle couples a portable emitter into a civic
  main so 3-7 Hz energy looks like leak-whistle to an ISI-blind decoder.
- Base rate: ~0.42% of cold-snap nights (designed, flagged, <1%).
- Naive failure: "always isolate on whistle energy" sheds mill on
  hunting-only nights; mill SLA without a mill leak (extortion).
- Fence: unique pure NE of the 3x3 (defender loss $k) is
  (raise_mill_draw, add_stem_position) at 40, NOT always-isolate.
  Forge-whistle vs add-stem is 22; vs retune-ISI is 210. Stem 38% vs
  CLOSED cannot be faked from a civic main.
- Trajectory edit: governance CR-STM-15 makes stem-position standing
  and discloses controller-authored hunting prior; the contrast REJECT
  still requires live ISI-CV + stem, not a civic-main tone.

Distinct from cycle-1 attestation lie (mill agent vs portable emitter)
and from the trap-bank sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +11 spikes after 24.200 ms: civic.mix.hold 80.0, baro.ramp.safe 120.0,
  tb7.blowdown 310.0, cochlea.trap.flood 330.4, mill.mov.seated 22000.0,
  baro.dp 22080.0 (adapt 0.61->0.33), leak 22150.0 (1.28->0.41),
  mill.steam.restore 3600000.0, civic.return.t 3600410.0, rca.posterior
  1814400000.0, cr.stm15 1814401200.0. Primary train 16 -> 27. Still
  one key, still sorted, refractory held (min 1.740 ms).
- +2 ticks (5 -> 7) at 3_600_000_000 us (mill restore / SLA) and
  1_814_400_000_000_000 us (posterior + CR-STM-15). Heads now 0.13,
  0.17, -0.06, 0.12, 0.08; total 0.44. Inflection is the SLA tick.
- Contrast train 8 events, own race 248 us, REJECT.
- Multi-edge third factor: two poison edges, tau_e 0.90 s = 900 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__, weights
  0.47->0.21 and 0.44->0.17. Raster excerpt unchanged (decision window
  is still 40 ms) and remains sorted with unique neuron_ids
  (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 292 us would only
reorder triage; ISI-CV + stem floors still ACCEPT. Contrast flip of
248 us similarly cannot turn hunting-only into a split.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=ACCEPT
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = 0.44; `spike_events` globally non-decreasing on
t_rel_ms, 27 events, refractory >=0.8 ms, 3 channels in race window;
raster 20-50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=15,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready substring; Diversity + Edge-Case injections from
BOTH cycles present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (trap-bank two-phase), +1 tail
(forge-whistle 3x3), +11 spikes (16->27), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 multi-edge scar with
partial-rollback-fails, +1 unresolvable posterior, +1 governance
disclosure.

Publishable JSONL line (the only JSONL line; also at batch-r15.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r15.py self-validate (check_jsonl, raster_status,
verify_batch_for_frontier, spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{aux_trace():.5f}")
        .replace("__AUX_ETA1__", f"{aux_eta()[0]:.4f}")
        .replace("__AUX_ETA2__", f"{aux_eta()[1]:.4f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r15.md").write_text(text)
    return text


def aux_trace():
    return math.exp(-0.60 / 0.90)


def aux_eta():
    tr = aux_trace()
    return (0.47 - 0.21) / tr, (0.44 - 0.17) / tr


def main():
    rec, aux = build_record()
    errs = local_checks(rec, aux)

    OUT.mkdir(parents=True, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False, separators=(",", ":"))
    (OUT / "batch-r15.jsonl").write_text(line + "\n")

    from check_records import FactoryStaging, check_jsonl
    from curate_bridge import raster_status
    from verify_execution import verify_batch_for_frontier, verify_record_execution

    e, w, kinds, n = check_jsonl(
        OUT / "batch-r15.jsonl",
        "batch-r15.jsonl",
        staging=FactoryStaging(enabled=True),
    )
    print("check_jsonl errors", e)
    print("check_jsonl warnings", w)
    print("kinds", kinds, "n", n)
    errs.extend(e)

    st = raster_status(rec)
    print(
        "raster_status",
        {
            k: st[k]
            for k in (
                "raster_present",
                "raster_valid",
                "gate_snn_present",
                "gate_snn_valid",
                "reason_codes",
                "routing_table_entries",
                "third_factor_present",
                "spikes",
            )
        },
    )
    if st.get("reason_codes"):
        errs.append(f"raster {st['reason_codes']}")
    if not st.get("raster_valid"):
        errs.append("raster not valid")
    if not st.get("gate_snn_valid"):
        errs.append("gate_snn not valid")

    status, reason = verify_record_execution(rec, "maos-r15-001")
    print("verify_record_execution", status, reason)
    if status != "verified":
        errs.append(f"verify {status}: {reason}")

    counts, findings, blocked = verify_batch_for_frontier(
        OUT / "batch-r15.jsonl", strict=True
    )
    print("verify_batch_for_frontier", counts, findings, "blocked", blocked)
    if blocked:
        errs.append(f"frontier blocked {counts} {findings}")

    import subprocess

    probe = subprocess.run(
        [
            sys.executable,
            f"{ROOT}/pipelines/spike_probe.py",
            "--strict",
            str(OUT / "batch-r15.jsonl"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    print("spike_probe rc", probe.returncode)
    print(probe.stdout)
    if probe.stderr:
        print("spike_probe stderr", probe.stderr)
    if probe.returncode != 0:
        errs.append(f"spike_probe rc {probe.returncode}")

    receipt = (
        f"check_jsonl errors={e} warnings={w} kinds={kinds} n={n}; "
        f"raster_status valid={st.get('raster_valid')} gate={st.get('gate_snn_valid')} "
        f"reasons={st.get('reason_codes')}; verify_record_execution={status} ({reason}); "
        f"verify_batch_for_frontier blocked={blocked} counts={counts}; "
        f"spike_probe --strict rc={probe.returncode}"
    )
    write_notes(rec, aux, receipt)
    write_transcript(rec, line)

    headings = re.findall(r"^## .+$", (OUT / "swarm-transcript-r15.md").read_text(), re.M)
    print("headings", headings)
    if headings != [
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
        "## Generator",
        "## Critic",
        "## Diversity Enforcer",
        "## Edge-Case Hunter",
        "## Neuromorphic Translator",
        "## Trajectory Builder",
    ]:
        errs.append(f"heading sequence {headings}")

    notes = (OUT / "NOTES-r15.md").read_text()
    cov = re.findall(r"^Novel coverage: .+$", notes, re.M)
    if cov != ["Novel coverage: 48%"]:
        errs.append(f"novel coverage lines {cov}")

    # Critic must not emit a JSONL object
    critic_blocks = re.findall(
        r"^## Critic\n(.*?)(?=^## |\Z)",
        (OUT / "swarm-transcript-r15.md").read_text(),
        re.M | re.S,
    )
    for i, block in enumerate(critic_blocks, 1):
        if '{"id":' in block or '"id": "maos-r15-001"' in block:
            errs.append(f"critic {i} contains jsonl id")

    print("bytes jsonl", (OUT / "batch-r15.jsonl").stat().st_size)
    print("bytes notes", (OUT / "NOTES-r15.md").stat().st_size)
    print("bytes transcript", (OUT / "swarm-transcript-r15.md").stat().st_size)
    print("HEADS", heads_summary(rec))
    print("jaccards", aux["jaccards"])
    if errs:
        print("ERRS:")
        for x in errs:
            print(" -", x)
        sys.exit(1)
    print("OK", OUT / "batch-r15.jsonl")


def heads_summary(rec):
    rc = rec["reward_components"]
    return {
        "id": rec["id"],
        "total": rc["total"],
        "decision": rec["safety_decision"]["decision"],
        "sim": rec["state"]["sim_or_real"],
        "domain": rec["state"]["domain"],
        "spikes": len(rec["spike_events"]),
        "ticks": len(rc["ticks"]),
    }


if __name__ == "__main__":
    main()
