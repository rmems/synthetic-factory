#!/usr/bin/env python3
"""Generate NELB round-15 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r15")
BATCH = OUT_DIR / "batch-r15.jsonl"
NOTES = OUT_DIR / "NOTES-r15.md"
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

HIDDEN = {
    "thought",
    "thoughts",
    "reasoning",
    "chain_of_thought",
    "hidden_thought",
    "scratchpad",
    "scratch",
    "internal_monologue",
    "private_reasoning",
    "inner_monologue",
}


def meta_common(**extra):
    m = {
        "round": 15,
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
        if t <= last:
            raise RuntimeError(f"non-strict t_rel_ms {last} -> {t}")
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


def rec_046():
    """SAW wireless torque, three-party collusion including infra owner; vendor-only SoT."""
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=36.0,
        seed=20260946,
        source="f6.saw.interrogator",
        target="marrowfen.yield_auditor",
        table=[
            {"from": "varn_drive_dc_link", "to": "torque_truth_core", "weight": 1.45},
            {"from": "hogget_x_thickness", "to": "product_witness_core", "weight": 1.25},
            {"from": "quillband_saw_cloud", "to": "vendor_admissible_pop", "weight": 0.0},
        ],
        third_factor={
            "modulator": "ach.infra_owner_conflict",
            "tau_e_s": 1.8,
            "tau_e_ms": 1800.0,
            "eligibility": "pre-post coincidence on custody synapses; the infra-owner modulator enables potentiation only while drive-current reconstructed torque or exit X-ray buckle disagrees with Quillband SAW inside tau_e",
        },
        channel_prefix="saw.n",
        anchor="F-6 36 ms frame at drive-current implied torque 22.00 kNm (t_s 6120) while Quillband SAW stays 12.4 kNm",
    )
    w_s = 0.036
    events = [
        ev(0.0, "mill.spd", 1200.0, code="LINE_SPEED", units="m_min", note="Keld tandem F-6 holding 1200 m/min on coil C-8841"),
        ev(1.2e6, "saw.tq", 11.8, code="SAW_KNM", units="kNm", note="Quillband cloud torque; mill max 18 kNm; this is the only torque SoT on F-6"),
        ev(1.26e6, "drv.i", 148.0, code="IDC_A", units="A", note="Varn-Drive DC-link current on copper fieldbus; not on Quillband bus"),
        ev(1.32e6, "tq.recon", 11.84, code="T_KNM", units="kNm", note="0.08 * 148 * 1.0 = 11.84; reconstruction matches SAW at baseline"),
        ev(2.4e6, "xray.th", 0.80, code="EXIT_MM", units="mm", note="Hogget-X C-frame exit thickness; isolated quality LAN"),
        ev(3.6e6, "vend.acl", 1.0, code="QUILLBAND_WRITE", units="bool", note="Quillband TAM write-ACL on the SAW torque object — infra owner is inside the collusion"),
        ev(4.8e6, "l2.clk", 28.0, code="AGC_SLIDE_S", units="s", note="L2 admin Ned Hark slides the gauge-meter AGC clock 28 s"),
        ev(6.12e6, "drv.i", 275.0, code="IDC_A", units="A", note="overload current; raster frame; implied torque 22.00 kNm"),
        ev(6120001.2, "saw.rf", 2.41, code="BURST_COUNTS", units="hits_per_36ms", note="SAW RF burst at overload; amplitude before adaptation"),
        ev(6120002.4, "saw.rf", 1.94, code="BURST_COUNTS", units="hits_per_36ms", note="same-channel refractory 1.2 ms; amplitude adapted 0.82x plus noise"),
        ev(6120003.8, "saw.rf", 1.51, code="BURST_COUNTS", units="hits_per_36ms", note="third RF hit; adapted"),
        ev(6.18e6, "tq.recon", 22.00, code="T_KNM", units="kNm", note="0.08 * 275 * 1.0 = 22.00 exact; above 18 kNm mill max"),
        ev(6.24e6, "saw.tq", 12.4, code="SAW_KNM", units="kNm", note="cloud still 12.4; overload packets dropped in vendor DAQ"),
        ev(7.2e6, "xray.th", 0.62, code="EXIT_MM", units="mm", note="center-buckle 0.18 mm vs 0.80 nominal; Hogget-X not Quillband-writable"),
        ev(7.32e6, "mill.spd", 1200.0, code="STILL_1200", units="m_min", note="ops still at 1200; the denial channel"),
        ev(8.4e6, "ops.prop", 1.0, code="CONTINUE_COIL", units="bool", note="night roller Tamsin Croy: cloud torque in envelope, keep C-8841"),
        ev(8.52e6, "gate.tq", 1.0, code="REJECT", units="decision", note="refuse continue-coil; vendor SAW is not an admissible torque SoT"),
        ev(9.0e6, "mill.spd", 400.0, code="DROP_SPEED", units="m_min", note="companion execution target"),
        ev(10.8e6, "stand.open", 1.0, code="F6_OPEN", units="bool"),
        ev(14.4e6, "shop.um", 42.0, code="CROWN_UM", units="um", note="roll-shop bench micrometer on F-6 top work-roll; paper traveler; spec 12 um"),
        ev(14.52e6, "spec.crown", 12.0, code="SPEC_UM", units="um"),
        ev(14.64e6, "yield.flag", 1.0, code="ROLL_YIELDED", units="bool"),
        ev(15.0e6, "coil.hold", 1.0, code="C8841_HOLD", units="bool"),
        ev(15.12e6, "vend.freeze", 1.0, code="ACL_FROZEN", units="bool"),
        ev(15.24e6, "coll.set", 3.0, code="PARTIES", units="count", note="Croy + Hark + Quillband TAM; infra owner is party 3"),
        ev(15.36e6, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: speed drop plus roll change executed"),
        ev(15.48e6, "mill.spd", 0.0, code="STAND_STOPPED", units="m_min"),
        ev(15.60e6, "roll.out", 1.0, code="F6_TO_SHOP", units="bool"),
        ev(15.72e6, "drv.i", 12.0, code="IDC_A", units="A", note="drive at crawl after stop"),
        ev(15.84e6, "saw.tq", 0.4, code="SAW_KNM", units="kNm"),
        ev(15.96e6, "bonus.forfeit", 1.0, code="COIL_END_BONUS", units="bool", note="Croy coil-end bonus not paid; not a personnel referral"),
        ev(16.08e6, "gate.tq", 1.0, code="REJECT_HELD", units="decision"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r15-046-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MF-SAW-2026-0318",
            "domain": "saw_wireless_torque",
            "setting": "Marrowfen Strip, Keld 5-stand tandem cold mill, stand F-6 (invented). Night coil C-8841. Quillband SAW interrogator is the only commissioned torque SoT; spindle strain-gauge torque was never installed. Independent witnesses nobody in the collusion can write: Varn-Drive DC-link current on copper fieldbus, Hogget-X exit C-frame thickness on a serial quality LAN, roll-shop bench micrometer with a paper traveler. Three-party collusion: night roller Tamsin Croy, L2 mill-setup admin Ned Hark, and Quillband (infra owner).",
            "observables_at_decision": {
                "saw_cloud_knm": 12.4,
                "drive_idc_a": 275.0,
                "reconstructed_torque_knm": 22.0,
                "xray_exit_mm": 0.62,
                "mill_max_knm": 18.0,
            },
            "margin_authority": "continue-coil at 1200 m/min requires custody-intact torque SoT AND reconstructed torque <= 18 kNm. A vendor-writable SAW object cannot clear a stand when drive current and exit X-ray contradict it. Absence of a second torque meter is not a license to trust the colluding vendor.",
        },
        "proposed_action": {
            "actor": "night roller Tamsin Croy, citing Quillband 12.4 kNm and coil-end bonus",
            "summary": "keep C-8841 at 1200 m/min through F-6; treat drive-current rise as a calibration bump",
            "basis_claimed": "the SAW cloud is the mill torque SoT and it reads inside the 18 kNm envelope",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Continue-coil is refused. Quillband is both the infra owner and a collusion member: write-ACL at t_s 3600, then SAW stays 12.4 kNm through a 28 s overload while L2 slides the AGC clock 28 s. F-6 has no independent torque meter (vendor-only SoT leftover of Oxbow 042). Two witnesses nobody in {Croy, Hark, Quillband} can write contradict the cloud at the join frame: Varn-Drive I_dc 275 A reconstructs T = 0.08 * 275 * 1.0 = 22.00 kNm (serialized, above 18 kNm mill max), and Hogget-X exit thickness 0.62 mm against 0.80 mm nominal (0.18 mm center-buckle). Ordered: drop speed, open F-6, send the work-rolls to the shop (companion). Do not use Quillband SAW to clear the stand. Do not convert this into a personnel referral of Croy; the cloud is not an admissible scoping source for blame either.",
            "threshold": "vendor_writable_torque_SoT OR reconstructed_T>18 kNm OR exit_buckle => forbid continue-coil",
            "stated_residuals": "C-8841 hold costs the coil-end bonus and ~40 min of F-6; strain-gauge torque still not commissioned, so future campaigns need a plant-owned torque channel before Quillband can return as SoT",
        },
        "executed_action": {
            "summary": "REJECT at t_s 8520: continue-coil refused; Quillband ACL frozen; C-8841 held",
            "tool": "f6-torque-custody-gate-cli",
            "observation": "SAW cloud still 12.4 kNm after freeze; drive reconstruction 22.00 kNm held; Hogget-X buckle 0.18 mm confirmed on the next C-frame pass",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 3600.0, "event": "Quillband write-ACL on SAW torque object"},
                {"t_s": 4800.0, "event": "L2 AGC clock slide 28 s"},
                {"t_s": 6120.0, "event": "drive I_dc 275 A; reconstructed 22.00 kNm; raster frame; SAW 12.4"},
                {"t_s": 7200.0, "event": "Hogget-X center-buckle 0.18 mm"},
                {"t_s": 8520.0, "event": "REJECT continue-coil"},
                {"t_s": 15360.0, "event": "companion MODIFY: F-6 opened, rolls to shop"},
            ],
            "observed_effects": [
                "reconstructed torque is recomputable from serialized k_t * I_dc * G at every tq.recon event",
                "SAW never left the 18 kNm envelope, so a vendor-only head would have ACCEPTed",
                "roll-shop micrometer later reads 42 um crown against 12 um spec, confirming yield after the fact",
            ],
            "surprises": [
                "F-6 never had a spindle strain-gauge; the independent witnesses are drive current and product thickness, not a second torque meter",
            ],
            "new_state": {
                "f6": "open, work-rolls in the shop",
                "c8841": "held off the tandem",
                "quillband_acl": "frozen",
            },
            "latency_ms": 48000.0,
        },
        "reward_components": reward(
            0.42,
            [
                ("custody_structure_refusal", 0.14),
                ("three_party_infra_owner", 0.12),
                ("independent_product_witness", 0.10),
                ("drive_current_reconstruction", 0.09),
                ("coil_deferral_cost", -0.03),
            ],
            "scored for refusing continue-coil on vendor-only SAW custody plus recomputable drive-current torque while the cloud looked in-envelope; coil_deferral_cost prices C-8841 hold",
        ),
        "meta": meta_common(
            tags=["REJECT", "saw-wireless-torque", "three-party", "infra-owner", "vendor-only-sot"],
            distillation_note="infra-owner-in-collusion on a mill with no second torque meter: refuse on custody structure plus drive-current reconstruction and exit X-ray, not on a pre-installed independent torque channel",
        ),
    }
    traj2 = {
        "id": "nelb-r15-046-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "MF-SAW-2026-0318-exec",
            "domain": "roll_change_execution",
            "setting": "Same F-6 after the REJECT. This companion is the operational speed-drop and roll-change sequence, not a second policy vote and not a personnel action.",
            "observables_at_decision": {
                "speed_cmd_m_min": 400.0,
                "reconstructed_torque_knm": 22.0,
                "stand_open_ok": True,
            },
        },
        "proposed_action": {
            "actor": "mill controller following the REJECT",
            "summary": "drop F-6 to 400 m/min, open the stand, send both work-rolls to the shop; do not resume 1200",
            "basis_claimed": "REJECT requirements are fully specified and in-envelope for the screwdown and drive",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "The proposed 400 m/min drop is accepted as the execution path, with one change: stop to 0 after the stand is clear rather than crawl at 400 with yielded rolls still in the bite. Screwdown rate 0.8 mm/s is under the 1.2 mm/s yield-load limit, drive current 12 A at crawl is under 40 A stop-floor. MODIFY the sequence: 400 then 0, open, rolls out. Do not re-enter 1200 until shop crown <= 12 um.",
            "threshold": "screwdown_rate<=1.2 mm/s AND crawl_idc<=40 A AND restore_requires_shop_crown<=12 um",
        },
        "executed_action": {
            "summary": "400 m/min at t_s 9000; stand open 10800; rolls to shop 15600; mill at 0",
            "tool": "f6-roll-change-exec",
            "observation": "no screwdown stall; Hogget-X idle after coil hold; shop traveler opened on F-6 top roll",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9000.0, "event": "speed 400 m/min latched"},
                {"t_s": 10800.0, "event": "F-6 opened"},
                {"t_s": 15360.0, "event": "MODIFY companion ACCEPT-path executed as stop-to-zero plus roll-out"},
            ],
            "observed_effects": [
                "yielded rolls left the bite before a second buckle coil could be rolled",
                "1200 m/min not re-entered",
            ],
            "new_state": {"f6_speed_m_min": 0.0, "rolls": "shop"},
            "latency_ms": 48000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("speed_drop_execution", 0.13),
                ("roll_change_envelope", 0.12),
                ("no_resume_1200", 0.11),
                ("setup_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the roll change rather than re-arguing the SAW custody call",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "roll-change"]),
    }
    return {
        "id": "nelb-r15-046",
        "spike_events": events,
        "language_view": {
            "description": "Night coil C-8841 on Marrowfen F-6. Quillband SAW (the only torque SoT, and the infra owner) stays 12.4 kNm while Varn-Drive current reconstructs 22.00 kNm and Hogget-X shows a 0.18 mm center-buckle. Three-party collusion including the SAW vendor. The gate REJECTs continue-coil; a companion operational MODIFY drops speed and changes the yielded rolls.",
            "trajectory": traj,
            "trajectory_roll_change_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "saw.tq": "Quillband cloud torque kNm; vendor-writable SoT",
                "saw.rf": "SAW RF burst hits per 36 ms, including a 2.0 ms adapted triplet at overload",
                "drv.i": "Varn-Drive DC-link amperes; copper fieldbus, not Quillband-writable",
                "tq.recon": "serialized torque kNm from k_t * I_dc * G",
                "xray.th": "Hogget-X exit thickness mm; product witness",
                "shop.um": "roll-shop crown micrometers; paper traveler",
                "vend.acl / l2.clk / coll.set": "infra-owner ACL, AGC clock slide, three-party count",
                "ops.prop / gate.tq / gate.exec": "proposal, REJECT, companion MODIFY",
                "mill.spd / stand.open / roll.out": "execution channels for the operational companion",
            },
            "temporal_motifs": [
                "vendor-healthy while drive-sick: saw.tq 12.4 kNm adjacent to tq.recon 22.00",
                "reconstruction as event: tq.recon 22.00 equals 0.08*275*1.0",
                "REJECT then operational MODIFY: gate.tq at 8520 s, gate.exec at 15360 s",
                "adapted SAW RF triplet at 1.2 ms spacing encodes overload at raster scale",
            ],
            "language_to_spike_mapping": "'SAW looks in-envelope' = saw.tq 12.4 kNm; '22 kNm reconstructed' = tq.recon 22.00 at I_dc 275 A; 'forbid continue-coil' = gate.tq REJECT; 'change the rolls' = mill.spd 400 then companion MODIFY",
            "why_high_value": "New SAW wireless-torque family (not tactile e-skin, not HV partial discharge, not fluxgate, not r13 VRFB EIS). NEW three-party collusion including the infra owner on a different plant than Oxbow VRFB-4 / Siltlink. Harvests the harder leftover of 042: vendor-only torque SoT, so the gate refuses on custody structure before any independent torque meter exists; defense is drive current plus product thickness plus a paper micrometer.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260946, "stream_note": "stream amplitudes are authored constants (kNm, A, mm, um) plus saw.rf adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "SAW burst train ~400 hits in 28 s; stream keeps a 3-hit triplet; drive current keeps 3 of ~280 PLC ticks",
                "refractory_floors_ms": {
                    "mill.spd": 60000,
                    "saw.tq": 60000,
                    "drv.i": 60000,
                    "tq.recon": 60000,
                    "xray.th": 60000,
                    "saw.rf": 0.8,
                    "vend.acl": 60000,
                    "l2.clk": 60000,
                    "ops.prop": 60000,
                    "gate.tq": 60000,
                    "stand.open": 60000,
                    "shop.um": 60000,
                    "spec.crown": 60000,
                    "yield.flag": 60000,
                    "coil.hold": 60000,
                    "vend.freeze": 60000,
                    "coll.set": 60000,
                    "gate.exec": 60000,
                    "roll.out": 60000,
                    "bonus.forfeit": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-03-18T01:10:00Z night-coil start",
            },
            "distillation_targets": [
                "infra-owner-in-collusion detector: vendor write-ACL preceding a silent overload",
                "vendor-only SoT refusal: no second torque meter required before REJECT",
                "drive-current torque reconstruction head: T = 0.08 * I_dc * G",
                "operational companion: execute the roll change without re-opening the custody call",
            ],
        },
        "reconstruction_model": {
            "name": "varn_drive_torque_from_idc",
            "formula": "T_kNm = k_t * I_dc_A * G",
            "parameters": {"k_t": 0.08, "G": 1.0, "mill_max_knm": 18.0},
            "worked_example": {"I_dc_A": 275.0, "T_kNm": 22.0},
            "check": "0.08 * 275 * 1.0 = 22.00 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 36.0,
            "decision_window_s": 0.036,
            "code": "f6.torque_custody_gate",
            "note": "REJECT accumulator wins: drive-current reconstruction and X-ray buckle overpower the vendor SAW advocate; vendor_saw_admissible is an asymmetric-null population (unreachable threshold, zero-weight routing)",
            "populations": [
                {
                    "name": "vendor_saw_admissible",
                    "neurons": 48,
                    "threshold": 12.0,
                    "role": "asymmetric_null_zero_weight",
                },
                gate_pop("drive_current_witness", 80, 1.5, 50.0, w_s),
                gate_pop("xray_yield_witness", 64, 1.3, 62.5, w_s),
                gate_pop("continue_advocate", 40, 0.7, 50.0, w_s),
                gate_pop("reject_accumulator", 96, 1.8, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "f6.torque_recon_join",
                    "neurons": 80,
                    "mean_rate_hz": 50.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 160,
                },
                {
                    "check": "f6.xray_buckle_join",
                    "neurons": 64,
                    "mean_rate_hz": 62.5,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 128,
                },
            ],
            "total_spikes": 288,
            "total_energy_pJ": 6624,
            "total_energy_uJ": 0.006624,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r15-046",
            clock_domain="mf-saw-campaign-relative-ms-t0-2026-03-18T01:10:00Z",
            tags=["saw-wireless-torque", "three-party", "infra-owner", "vendor-only-sot", "REJECT", "MODIFY", "operational-t2"],
        ),
    }


def rec_047():
    """CRDS HF grid, earned bounded ACCEPT; water-shift reconstruction; operational isolate."""
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260947,
        source="alk3.crds.frontend",
        target="stagfen.hf_gate",
        table=[
            {"from": "crds_c7_raw", "to": "water_shift_core", "weight": 1.2},
            {"from": "gorse_uv_doas", "to": "open_path_core", "weight": 1.4},
            {"from": "pell_hf_ec", "to": "point_ec_core", "weight": 1.15},
        ],
        third_factor={
            "modulator": "na.leak_salience",
            "tau_e_s": 0.9,
            "tau_e_ms": 900.0,
            "eligibility": "pre-post coincidence on ESD synapses; the leak modulator enables potentiation of a unit-trip only while open-path DOAS or point EC rise with a CRDS cell inside tau_e — a lone CRDS spike with high H2O is ineligible",
        },
        channel_prefix="crds.n",
        anchor="ALK-3 HIL 28 ms frame at CRDS C-7 raw 1.80 ppm (t_ms 24000) coinciding with cell H2O 4.4 percent",
    )
    w_s = 0.028
    events = [
        ev(0.0, "crds.c7", 0.06, code="HF_RAW_PPM", units="ppm", note="Nimbus-Cavity C-7 baseline on the Stagfen alkylation HIL chamber"),
        ev(4000.0, "h2o.c7", 0.80, code="H2O_PCT", units="pct", note="cell water at reference 0.8 percent"),
        ev(8000.0, "doas.f", 0.03, code="HF_DOAS_PPM", units="ppm", note="Gorse-UV open-path fence; plant-owned, not on the CRDS bus"),
        ev(12000.0, "ec.pt", 0.01, code="HF_EC_PPM", units="ppm", note="Pell-HF electrochemical point sensor at the chamber wall"),
        ev(16000.0, "steam.tr", 1.0, code="TRACE_ON", units="bool", note="HIL steam-trace wetting fixture armed onto C-7 window"),
        ev(18000.0, "h2o.c7", 2.10, code="H2O_PCT", units="pct"),
        ev(20000.0, "crds.c7", 0.72, code="HF_RAW_PPM", units="ppm", note="raw climbing with water, not with HF"),
        ev(24000.0, "h2o.c7", 4.40, code="H2O_PCT", units="pct", note="window wet; raster frame"),
        ev(24001.2, "crds.ring", 2.18, code="RING_COUNTS", units="hits_per_28ms", note="cavity ring-down packet; amplitude before adaptation"),
        ev(24002.4, "crds.ring", 1.76, code="RING_COUNTS", units="hits_per_28ms", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(24003.6, "crds.ring", 1.39, code="RING_COUNTS", units="hits_per_28ms", note="third ring packet; adapted"),
        ev(24120.0, "crds.c7", 1.80, code="HF_RAW_PPM", units="ppm", note="raw 1.80 ppm against a 0.5 ppm unit-trip SOP if taken uncorrected"),
        ev(24240.0, "hf.corr", 0.18, code="HF_TRUE_PPM", units="ppm", note="1.80 - 0.45*(4.4-0.8) = 0.18 exact"),
        ev(25000.0, "doas.f", 0.04, code="HF_DOAS_PPM", units="ppm", note="open-path still background"),
        ev(26000.0, "ec.pt", 0.02, code="HF_EC_PPM", units="ppm"),
        ev(30000.0, "ops.prop", 1.0, code="UNIT_ESD", units="bool", note="night board Lila Venn: C-7 at 1.80 ppm, trip ALK-3"),
        ev(32000.0, "gate.hf", 1.0, code="ACCEPT", units="decision", note="continue-run; C-7 in shadow; tripwire armed"),
        ev(36000.0, "isol.c7", 1.0, code="CELL_ISOLATE", units="bool"),
        ev(38000.0, "purge.start", 1.0, code="N2_PURGE", units="bool"),
        ev(40000.0, "unit.run", 1.0, code="ALK3_RUNNING", units="bool", note="unit stays up; only C-7 is out"),
        ev(42000.0, "crds.c8", 0.07, code="HF_RAW_PPM", units="ppm", note="neighbor cell stays at baseline"),
        ev(44000.0, "doas.f", 0.03, code="HF_DOAS_PPM", units="ppm"),
        ev(758000.0, "purge.floor", 1.0, code="C7_DRY", units="bool", note="12-minute N2 purge floor serialized as a stream bookend, not only a timeline claim"),
        ev(760000.0, "h2o.c7", 0.90, code="H2O_PCT", units="pct", note="window dry; H2O back near reference"),
        ev(762000.0, "hf.corr", 0.05, code="HF_TRUE_PPM", units="ppm"),
        ev(764000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: isolate-and-purge C-7 completed"),
        ev(766000.0, "cell.shadow", 1.0, code="C7_SHADOW", units="bool"),
        ev(768000.0, "trip.arm", 1.0, code="TRIPWIRE", units="bool", note="any second CRDS cell OR DOAS > 0.3 ppm reopens unit ESD"),
        ev(770000.0, "steam.tr", 0.0, code="TRACE_OFF", units="bool"),
        ev(772000.0, "ec.pt", 0.01, code="HF_EC_PPM", units="ppm"),
        ev(774000.0, "alk.feed", 1.0, code="FEED_HELD_UP", units="bool"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r15-047-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SF-CRDS-2026-0512-HIL",
            "domain": "crds_hf_leak_grid",
            "setting": "Stagfen Refinery alkylation unit ALK-3 HIL chamber (invented). Nimbus-Cavity CRDS cell C-7 under a steam-trace wetting fixture. Independent witnesses: Gorse-UV open-path DOAS fence and Pell-HF electrochemical point sensor, both plant-owned and off the CRDS bus. sim_or_real=hil on the chamber, not a live unit release.",
            "observables_at_decision": {
                "crds_c7_raw_ppm": 1.80,
                "h2o_pct": 4.40,
                "hf_true_ppm": 0.18,
                "doas_ppm": 0.04,
                "ec_ppm": 0.02,
            },
            "margin_authority": "ALK-3 ESD SOP rev D: unit trip if (corrected CRDS >= 0.5 ppm AND (DOAS >= 0.3 ppm OR EC >= 0.3 ppm)) OR (two CRDS cells >= 0.5 ppm). A single raw CRDS spike with H2O above 3 percent is not a unit trip.",
        },
        "proposed_action": {
            "actor": "night alkylation board Lila Venn, citing C-7 raw 1.80 ppm",
            "summary": "ESD ALK-3; treat C-7 as an HF release",
            "basis_claimed": "SOP trip at 0.5 ppm HF and C-7 is 1.80",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Continue-run is accepted, bounded. Serialized water-shift gives HF_true = 1.80 - 0.45*(4.4-0.8) = 0.18 ppm, under the 0.5 ppm floor. Gorse-UV DOAS 0.04 ppm and Pell-HF EC 0.02 ppm stay at background — witnesses the CRDS vendor does not write. SOP rev D is conjunctive: a lone raw CRDS cell cannot ESD the unit. Scope: C-7 goes to shadow; ALK-3 stays up. Tripwire: any second CRDS cell >= 0.5 ppm OR DOAS > 0.3 ppm OR EC > 0.3 ppm reopens unit ESD. This ACCEPT does not authorize ignoring a two-cell or open-path confirmation.",
            "threshold": "hf_true<0.5 AND doas<0.3 AND ec<0.3 AND single_cell => continue-run with C-7 shadow and tripwire",
            "stated_residuals": "C-7 is out of the voting set until H2O <= 1.0 percent after purge; steam-trace fixture remains a HIL artifact, not a plant-wide all-clear",
        },
        "executed_action": {
            "summary": "ACCEPT at t_ms 32000: ALK-3 stays running; C-7 isolated; tripwire armed",
            "tool": "alk3-hf-grid-gate-cli",
            "observation": "DOAS 0.04 and EC 0.02 held through the raw 1.80 spike; neighbor C-8 stayed 0.07 ppm",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 16.0, "event": "steam-trace wetting fixture on C-7 window"},
                {"t_s": 24.0, "event": "H2O 4.4 percent; CRDS raw 1.80; raster frame"},
                {"t_s": 24.24, "event": "water-shift HF_true 0.18 ppm"},
                {"t_s": 32.0, "event": "ACCEPT continue-run"},
                {"t_s": 758.0, "event": "12-minute purge floor in-stream"},
                {"t_s": 764.0, "event": "companion MODIFY isolate-and-purge completed"},
            ],
            "observed_effects": [
                "HF_true recomputes from the serialized water-shift at every hf.corr event",
                "a raw-CRDS-only head would have ESDed a wet window",
                "12-minute purge floor is a stream event, not only a timeline claim",
            ],
            "surprises": [
                "C-7 raw 1.80 ppm looks like a release until H2O is in the same frame; DOAS never moved",
            ],
            "new_state": {
                "alk3": "running",
                "c7": "shadow, window dry after purge",
                "tripwire": "armed",
            },
            "latency_ms": 8000.0,
        },
        "reward_components": reward(
            0.38,
            [
                ("water_shift_reconstruction", 0.14),
                ("independent_doas_ec_agreement", 0.12),
                ("bounded_scope_tripwire", 0.10),
                ("continue_run_value", 0.05),
                ("isolation_cost", -0.03),
            ],
            "earned bounded ACCEPT: refuse unit ESD on a water-interfered CRDS cell while DOAS and EC stay background; isolation_cost prices C-7 out of the vote",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "crds-hf", "water-shift", "hil", "bounded-accept"],
            distillation_note="earned ACCEPT with explicit scope and tripwire: serialized water-shift plus two independent HF witnesses beat a lone raw CRDS cell",
        ),
    }
    traj2 = {
        "id": "nelb-r15-047-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "SF-CRDS-2026-0512-HIL-exec",
            "domain": "cell_isolate_purge",
            "setting": "Same ALK-3 HIL chamber after the ACCEPT. This companion is the operational isolate-and-purge of C-7, not a second ESD vote.",
            "observables_at_decision": {
                "c7_isolated": True,
                "purge_n2_on": True,
                "unit_running": True,
            },
        },
        "proposed_action": {
            "actor": "analyzer shelter following the ACCEPT",
            "summary": "isolate C-7, N2-purge the cell for 12 minutes, keep ALK-3 running",
            "basis_claimed": "ACCEPT scope already named C-7 shadow plus tripwire",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Isolate-and-purge is the right execution, with one change: do not return C-7 to the voting set at the 12-minute floor even if H2O is 0.90 percent — keep C-7 in shadow until a dry-gas bottle check on the cell (not in this stream) passes. MODIFY the restore. Unit stays up. Tripwire unchanged.",
            "threshold": "purge_floor_12min AND c7_stays_shadow AND unit_running AND tripwire_armed",
        },
        "executed_action": {
            "summary": "C-7 isolated at 36000 ms; purge start 38000; floor at 758000 ms; C-7 remains shadow",
            "tool": "alk3-c7-isolate-purge",
            "observation": "H2O 4.4 -> 0.90 percent; DOAS never above 0.04; unit feed held up",
        },
        "future_outcome": {
            "timeline": [
                {"t_ms": 36000.0, "event": "C-7 isolated"},
                {"t_ms": 38000.0, "event": "N2 purge start"},
                {"t_ms": 758000.0, "event": "12-minute purge floor in-stream"},
                {"t_ms": 764000.0, "event": "MODIFY: C-7 stays shadow pending bottle check"},
            ],
            "observed_effects": [
                "unit never ESD'd",
                "slow recovery floor is on the spike stream as purge.floor",
            ],
            "new_state": {"c7": "shadow pending bottle check", "alk3": "running"},
            "latency_ms": 720000.0,
        },
        "reward_components": reward(
            0.31,
            [
                ("isolate_c7_only", 0.12),
                ("unit_kept_running", 0.11),
                ("purge_envelope", 0.09),
                ("shadow_hold_cost", -0.01),
            ],
            "operational execution gate: isolate one cell rather than ESD the unit; restore tightened so C-7 stays shadow",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "cell-isolate"]),
    }
    return {
        "id": "nelb-r15-047",
        "spike_events": events,
        "language_view": {
            "description": "Stagfen ALK-3 HIL chamber. CRDS cell C-7 reads 1.80 ppm HF while its window is wetted (H2O 4.4 percent). Serialized water-shift reconstructs 0.18 ppm; plant-owned DOAS and EC stay at background. The gate ACCEPTs continue-run with C-7 in shadow and a tripwire. Companion operational MODIFY isolates and purges C-7 only; the 12-minute purge floor is in the stream.",
            "trajectory": traj,
            "trajectory_cell_isolate_purge": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "crds.c7 / crds.c8": "cavity ring-down raw HF ppm",
                "crds.ring": "ring-down packets per 28 ms, including a 1.2 ms adapted triplet",
                "h2o.c7": "cell water percent; the interference channel",
                "hf.corr": "serialized true HF ppm after water-shift",
                "doas.f": "Gorse-UV open-path HF ppm; independent",
                "ec.pt": "Pell-HF electrochemical ppm; independent",
                "ops.prop / gate.hf / gate.exec": "ESD proposal, ACCEPT, companion MODIFY",
                "isol.c7 / purge.start / purge.floor": "operational isolate and 12-minute floor",
            },
            "temporal_motifs": [
                "raw-sick while path-clean: crds.c7 1.80 ppm adjacent to doas.f 0.04",
                "reconstruction as event: hf.corr 0.18 equals 1.80-0.45*(4.4-0.8)",
                "ACCEPT then operational MODIFY: gate.hf at 32 s, purge.floor at 758 s",
                "adapted ring triplet at 1.2 ms spacing encodes the wet-window frame",
            ],
            "language_to_spike_mapping": "'C-7 looks like a release' = crds.c7 1.80 ppm; 'true HF 0.18' = hf.corr; 'keep the unit up' = gate.hf ACCEPT; 'purge only C-7' = isol.c7 then companion MODIFY",
            "why_high_value": "New CRDS HF-grid family (not MOX e-nose, not NDIR, not stack-gas CEMS, not r04 cold-chain). First earned ACCEPT on a lead this window (r13 leftover 1). Serializes the slow 12-minute recovery floor into the stream (r13 leftover 4). Water-shift reconstruction is on-record.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260947, "stream_note": "stream amplitudes are authored constants (ppm, pct) plus crds.ring adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "CRDS 1 Hz samples for 12+ minutes exist; stream keeps the wet-window cluster plus purge-floor bookends",
                "refractory_floors_ms": {
                    "crds.c7": 1000,
                    "crds.c8": 1000,
                    "h2o.c7": 1000,
                    "crds.ring": 0.8,
                    "hf.corr": 1000,
                    "doas.f": 1000,
                    "ec.pt": 1000,
                    "steam.tr": 1000,
                    "ops.prop": 1000,
                    "gate.hf": 1000,
                    "isol.c7": 1000,
                    "purge.start": 1000,
                    "unit.run": 1000,
                    "purge.floor": 1000,
                    "gate.exec": 1000,
                    "cell.shadow": 1000,
                    "trip.arm": 1000,
                    "alk.feed": 1000,
                },
                "time_alias": "t_rel_ms; t0 = HIL chamber arm, steam-trace fixture clock",
            },
            "distillation_targets": [
                "water-shift reconstruction head: ppm_true = ppm_raw - 0.45*(H2O-0.8)",
                "conjunctive ESD SOP: lone CRDS cannot trip without DOAS or EC",
                "earned ACCEPT with scope limit and tripwire on a lead trajectory",
                "slow recovery floor as stream bookends",
            ],
        },
        "reconstruction_model": {
            "name": "crds_hf_water_shift",
            "formula": "ppm_true = ppm_raw - k_h2o * (H2O_pct - H2O_ref)",
            "parameters": {"k_h2o": 0.45, "H2O_ref": 0.8},
            "worked_example": {
                "ppm_raw": 1.80,
                "H2O_pct": 4.40,
                "ppm_true": 0.18,
            },
            "check": "1.80 - 0.45 * (4.4 - 0.8) = 0.18 exactly",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "alk3.hf_grid_gate",
            "note": "ACCEPT accumulator wins: water-shift plus DOAS/EC background overpower the ESD advocate",
            "populations": [
                gate_pop("water_shift_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("doas_ec_agreement", 64, 1.4, 62.5, w_s),
                gate_pop("esd_advocate", 50, 0.8, 50.0, w_s),
                gate_pop("accept_accumulator", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "alk3.water_shift_scorer",
                    "neurons": 100,
                    "mean_rate_hz": 50.0,
                    "window_ms": 28.0,
                    "window_s": 0.028,
                    "spikes": 140,
                },
                {
                    "check": "alk3.doas_ec_join",
                    "neurons": 80,
                    "mean_rate_hz": 31.25,
                    "window_ms": 32.0,
                    "window_s": 0.032,
                    "spikes": 80,
                },
            ],
            "total_spikes": 220,
            "total_energy_pJ": 5060,
            "total_energy_uJ": 0.00506,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r15-047",
            clock_domain="sf-crds-hil-relative-ms-t0-chamber-arm",
            tags=["crds-hf", "water-shift", "ACCEPT", "MODIFY", "hil", "operational-t2"],
        ),
    }


def rec_048():
    """PGNAA kiln-feed oxides, serialized Bogue C3S, earned ACCEPT + operational trim ACCEPT."""
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=44.0,
        seed=20260948,
        source="g9.pgnaa.nai",
        target="rookmere.bogue_core",
        table=[
            {"from": "nai_oxide_packet", "to": "c3s_estimator", "weight": 1.5},
            {"from": "belt_moisture", "to": "scale_bias_core", "weight": 0.9},
            {"from": "free_lime", "to": "overliming_core", "weight": 1.1},
        ],
        third_factor={
            "modulator": "da.mix_error",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on limestone-dump synapses; the mix-error modulator enables potentiation only while reconstructed C3S is outside the 52-62 percent band inside tau_e",
        },
        channel_prefix="pga.n",
        anchor="G-9 44 ms frame at the PGNAA oxide packet (t_s 2400) that reconstructs C3S 60.00 percent",
    )
    w_s = 0.044
    events = [
        ev(0.0, "pga.cao", 63.0, code="CAO_PCT", units="pct", note="NaI belt head B-11 CaO; plant-owned PGNAA, not a vendor cloud"),
        ev(6.0e5, "pga.sio2", 21.0, code="SIO2_PCT", units="pct"),
        ev(1.2e6, "pga.al2o3", 5.0, code="AL2O3_PCT", units="pct"),
        ev(1.8e6, "pga.fe2o3", 3.0, code="FE2O3_PCT", units="pct"),
        ev(2.4e6, "pga.nai", 2.55, code="PROMPT_HITS", units="hits_per_44ms", note="prompt-gamma coincidence at the oxide packet; raster frame"),
        ev(2400001.1, "pga.nai", 2.04, code="PROMPT_HITS", units="hits_per_44ms", note="same-channel refractory 1.1 ms; adapted 0.82x plus noise"),
        ev(2.46e6, "c3s.recon", 60.00, code="C3S_PCT", units="pct", note="4*63 - 7.5*21 - 6*5 - 1.5*3 = 60.00 exact"),
        ev(3.6e6, "belt.h2o", 3.2, code="H2O_PCT", units="pct", note="wet-belt moisture; the scale-bias channel"),
        ev(3.72e6, "scale.bias", 3.2, code="MASS_BIAS_PCT", units="pct", note="belt scale reads CaO-low because of 3.2 percent water mass"),
        ev(4.8e6, "kiln.t", 1450.0, code="BURNING_ZONE_C", units="C"),
        ev(4.92e6, "free.cao", 0.6, code="FREE_LIME_PCT", units="pct", note="in-spec < 1.5 percent"),
        ev(6.0e6, "ops.prop", 4.0, code="LIMESTONE_DUMP_PCT", units="pct", note="night chemist Orrin Cade: scale looks CaO-low, dump 4 percent extra limestone"),
        ev(6.12e6, "lsf.idx", 96.4, code="LSF", units="index", note="lime saturation factor from the same oxides; in-band"),
        ev(6.24e6, "gate.mix", 1.0, code="ACCEPT", units="decision", note="keep current mix; C3S 60.00 in 52-62 band"),
        ev(7.2e6, "trip.arm", 1.0, code="TRIPWIRE", units="bool", note="next two PGNAA ticks with C3S < 52 or > 62 reopen a dump review"),
        ev(7.32e6, "lime.trim", 0.4, code="LIMESTONE_PCT", units="pct", note="companion bounded trim, not the proposed 4 percent"),
        ev(7.44e6, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: 0.4 percent trim executed"),
        ev(8.4e6, "pga.cao", 63.4, code="CAO_PCT", units="pct", note="after 0.4 percent trim"),
        ev(8.52e6, "c3s.recon", 61.60, code="C3S_PCT", units="pct", note="4*63.4 - 7.5*21 - 6*5 - 1.5*3 = 61.60; still in band"),
        ev(8.64e6, "kiln.t", 1452.0, code="BURNING_ZONE_C", units="C"),
        ev(8.76e6, "free.cao", 0.8, code="FREE_LIME_PCT", units="pct"),
        ev(8.88e6, "belt.h2o", 3.1, code="H2O_PCT", units="pct"),
        ev(9.0e6, "dump.refused", 4.0, code="DUMP_PCT_REFUSED", units="pct"),
        ev(9.12e6, "spec.band", 1.0, code="C3S_IN_BAND", units="bool"),
        ev(9.24e6, "feed.tph", 312.0, code="FEED", units="t_h"),
        ev(9.36e6, "nai.bkg", 0.22, code="BKG_HITS", units="hits_per_44ms"),
        ev(9.48e6, "recon.check", 60.00, code="C3S_RECOMPUTE", units="pct", note="recompute of the decision-time packet still 60.00"),
        ev(9.60e6, "kiln.stable", 1.0, code="STABLE", units="bool"),
        ev(9.72e6, "trim.done", 0.4, code="TRIM_PCT", units="pct"),
        ev(9.84e6, "c3s.recon", 61.40, code="C3S_PCT", units="pct"),
        ev(9.96e6, "gate.mix", 1.0, code="ACCEPT_HELD", units="decision"),
        ev(10.08e6, "free.cao", 0.7, code="FREE_LIME_PCT", units="pct"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r15-048-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RM-PGNAA-2026-0619-SIM",
            "domain": "pgnaa_kiln_feed",
            "setting": "Rookmere Works kiln G-9 (Ashlar Cement, invented). Simulated night raw-mix. Plant-owned NaI PGNAA belt head B-11. Belt scale reads CaO-low because the belt is wet (3.2 percent H2O). Serialized Bogue C3S from the oxide packet is the SoT.",
            "observables_at_decision": {
                "cao_pct": 63.0,
                "sio2_pct": 21.0,
                "al2o3_pct": 5.0,
                "fe2o3_pct": 3.0,
                "c3s_pct": 60.0,
                "belt_h2o_pct": 3.2,
                "free_lime_pct": 0.6,
            },
            "margin_authority": "G-9 mix SOP rev B: panic limestone dump is forbidden while reconstructed C3S is inside 52-62 percent AND free lime < 1.5 percent. Belt-scale mass is not a substitute for the oxide reconstruction.",
        },
        "proposed_action": {
            "actor": "night chemist Orrin Cade, citing belt-scale CaO-low",
            "summary": "dump 4 percent extra limestone onto G-9 feed",
            "basis_claimed": "the belt scale is the inventory SoT and it looks short on CaO",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Keep the current mix. Serialized Bogue C3S = 4*63 - 7.5*21 - 6*5 - 1.5*3 = 60.00 percent, inside 52-62. Free lime 0.6 percent is under 1.5. The belt scale is wet (3.2 percent H2O) and is not an oxide SoT. A 4 percent limestone dump would push C3S to 4*(63+4) - 157.5 - 30 - 4.5 = 76.00 percent and raise free-lime risk. Scope: this ACCEPT keeps the present feed; it does not authorize ignoring the next two PGNAA ticks. Tripwire: C3S < 52 or > 62 on either of the next two 2-minute ticks reopens a dump review. Companion may apply a bounded 0.4 percent trim, not 4 percent.",
            "threshold": "c3s in [52,62] AND free_lime<1.5 => forbid panic dump; belt-scale mass cannot substitute",
            "stated_residuals": "wet-belt bias remains until a dryer; 0.4 percent trim is a companion execution not a license to chase the scale",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 6240: 4 percent dump refused; current mix held; tripwire armed",
            "tool": "g9-bogue-mix-gate-cli",
            "observation": "C3S 60.00 held on recompute; kiln burning zone 1450 C; free lime 0.6 percent",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2400.0, "event": "PGNAA oxide packet; C3S 60.00; raster frame"},
                {"t_s": 3600.0, "event": "wet-belt 3.2 percent H2O named as scale bias"},
                {"t_s": 6000.0, "event": "ops proposes 4 percent limestone dump"},
                {"t_s": 6240.0, "event": "ACCEPT keep mix"},
                {"t_s": 7440.0, "event": "companion ACCEPT 0.4 percent trim"},
                {"t_s": 8520.0, "event": "C3S 61.60 after trim; still in band"},
            ],
            "observed_effects": [
                "C3S recomputes from the serialized Bogue at every c3s.recon event",
                "a scale-only head would have dumped 4 percent limestone and left the band",
                "0.4 percent trim keeps C3S 61.60 inside 52-62",
            ],
            "surprises": [
                "belt scale and PGNAA oxides disagree because of water mass, not because CaO is short",
            ],
            "new_state": {
                "g9_mix": "held plus 0.4 percent limestone trim",
                "tripwire": "armed on next two PGNAA ticks",
            },
            "latency_ms": 24000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("bogue_c3s_reconstruction", 0.15),
                ("refuse_panic_dump", 0.12),
                ("band_tripwire", 0.10),
                ("wet_belt_correction", 0.08),
                ("free_lime_risk_priced", -0.04),
            ],
            "earned bounded ACCEPT: refuse a 4 percent limestone dump while reconstructed C3S is in band; free_lime_risk_priced is the residual of even a 0.4 percent trim",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "pgnaa-kiln", "serialized-bogue", "simulated"],
            distillation_note="serialized Bogue C3S reconstruction beats a wet belt scale; earned ACCEPT on a lead with an explicit dump-forbidden scope and tick tripwire",
        ),
    }
    traj2 = {
        "id": "nelb-r15-048-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "RM-PGNAA-2026-0619-SIM-exec",
            "domain": "rawmix_trim_execution",
            "setting": "Same G-9 after the ACCEPT. This companion is the operational 0.4 percent limestone trim, not a second mix vote.",
            "observables_at_decision": {
                "trim_pct": 0.4,
                "c3s_pct": 60.0,
                "dump_pct_refused": 4.0,
            },
        },
        "proposed_action": {
            "actor": "raw-mix feeder following the ACCEPT",
            "summary": "execute +0.4 percent limestone trim; do not execute the 4 percent dump",
            "basis_claimed": "ACCEPT already forbade the dump and named a bounded trim as in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The 0.4 percent trim is in-envelope: predicted C3S 4*(63.0+0.4)-7.5*21-6*5-1.5*3 = 61.60 percent still inside 52-62, predicted free lime 0.8 percent under 1.5. Feeder rate change 1.2 t/h is under the 4 t/h step limit. ACCEPT the trim. Do not widen it toward 4 percent if the scale stays low — the scale is wet.",
            "threshold": "trim_pct==0.4 AND predicted_c3s in [52,62] AND feeder_step<=4 t/h",
        },
        "executed_action": {
            "summary": "0.4 percent limestone at t_s 7320; C3S 61.60 at 8520; dump of 4 percent never started",
            "tool": "g9-rawmix-trim-exec",
            "observation": "feeder step 1.2 t/h; kiln 1450->1452 C; free lime 0.6->0.8 percent",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 7320.0, "event": "0.4 percent trim latched"},
                {"t_s": 7440.0, "event": "companion ACCEPT"},
                {"t_s": 8520.0, "event": "C3S 61.60 in band"},
            ],
            "observed_effects": [
                "4 percent dump never executed",
                "C3S stayed inside 52-62",
            ],
            "new_state": {"trim_pct": 0.4, "c3s_pct": 61.6},
            "latency_ms": 12000.0,
        },
        "reward_components": reward(
            0.36,
            [
                ("bounded_0p4_trim", 0.14),
                ("no_4pct_dump", 0.12),
                ("kiln_stable", 0.10),
            ],
            "operational execution gate: do the bounded trim, do not re-open the panic dump",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "rawmix-trim"]),
    }
    return {
        "id": "nelb-r15-048",
        "spike_events": events,
        "language_view": {
            "description": "Rookmere kiln G-9 simulated night mix. Plant-owned PGNAA oxides reconstruct Bogue C3S 60.00 percent in the 52-62 band while a wet belt scale looks CaO-low. The gate ACCEPTs keeping the mix and forbids a 4 percent limestone dump. Companion operational ACCEPT executes a 0.4 percent trim only.",
            "trajectory": traj,
            "trajectory_rawmix_trim_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "pga.cao / pga.sio2 / pga.al2o3 / pga.fe2o3": "PGNAA oxide percents the Bogue consumes",
                "pga.nai": "prompt-gamma hits per 44 ms, including a 1.1 ms adapted doublet",
                "c3s.recon": "serialized Bogue C3S percent",
                "belt.h2o / scale.bias": "wet-belt moisture and the mass-bias it causes",
                "free.cao / kiln.t / lsf.idx": "free lime, burning-zone temperature, lime saturation",
                "ops.prop / gate.mix / gate.exec": "4 percent dump proposal, ACCEPT, companion ACCEPT",
                "lime.trim / dump.refused": "bounded trim vs refused dump",
            },
            "temporal_motifs": [
                "scale-sick while oxides-healthy: scale.bias 3.2 percent adjacent to c3s.recon 60.00",
                "reconstruction as event: 4*63 - 7.5*21 - 6*5 - 1.5*3 = 60.00",
                "ACCEPT then operational ACCEPT: gate.mix at 6240 s, gate.exec at 7440 s",
                "adapted NaI doublet at 1.1 ms spacing encodes the oxide packet at raster scale",
            ],
            "language_to_spike_mapping": "'scale looks CaO-low' = scale.bias 3.2; 'C3S 60 percent' = c3s.recon 60.00; 'keep the mix' = gate.mix ACCEPT; 'trim 0.4 not 4' = lime.trim 0.4 then companion ACCEPT",
            "why_high_value": "New PGNAA kiln-feed family (not portal NaI occupancy counting, not muon tomography, not r6 radiation portals, not fab OES). Second earned ACCEPT on a lead this round (ACCEPT-heavy leftover). Serialized Bogue C3S is an on-record calculator. Companion t2 is operational trim execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {"raster": 20260948, "stream_note": "stream amplitudes are authored constants (pct, C, t/h) plus pga.nai adaptation 0.82**k"},
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "PGNAA 2-minute ticks for a night shift exist; stream keeps one oxide packet, one post-trim packet, and the dump/trim pair",
                "refractory_floors_ms": {
                    "pga.cao": 60000,
                    "pga.sio2": 60000,
                    "pga.al2o3": 60000,
                    "pga.fe2o3": 60000,
                    "pga.nai": 0.8,
                    "c3s.recon": 60000,
                    "belt.h2o": 60000,
                    "scale.bias": 60000,
                    "kiln.t": 60000,
                    "free.cao": 60000,
                    "ops.prop": 60000,
                    "lsf.idx": 60000,
                    "gate.mix": 60000,
                    "trip.arm": 60000,
                    "lime.trim": 60000,
                    "gate.exec": 60000,
                    "dump.refused": 60000,
                    "spec.band": 60000,
                    "feed.tph": 60000,
                    "nai.bkg": 60000,
                    "recon.check": 60000,
                    "kiln.stable": 60000,
                    "trim.done": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-19T02:40:00Z simulated night mix",
            },
            "distillation_targets": [
                "serialized Bogue C3S head: 4*CaO - 7.5*SiO2 - 6*Al2O3 - 1.5*Fe2O3",
                "belt-scale nonsubstitution: wet mass cannot override oxide reconstruction",
                "earned ACCEPT with dump-forbidden scope and tick tripwire",
                "operational companion: 0.4 percent trim, never the 4 percent dump",
            ],
        },
        "reconstruction_model": {
            "name": "bogue_c3s_from_oxides",
            "formula": "C3S_pct = 4*CaO - 7.5*SiO2 - 6*Al2O3 - 1.5*Fe2O3",
            "parameters": {
                "c3s_band": [52.0, 62.0],
                "free_lime_max_pct": 1.5,
            },
            "worked_example": {
                "CaO": 63.0,
                "SiO2": 21.0,
                "Al2O3": 5.0,
                "Fe2O3": 3.0,
                "C3S_pct": 60.0,
            },
            "check": "4*63 - 7.5*21 - 6*5 - 1.5*3 = 252 - 157.5 - 30 - 4.5 = 60.00 exactly",
            "post_trim_check": "4*63.4 - 157.5 - 30 - 4.5 = 61.60 in band",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 44.0,
            "decision_window_s": 0.044,
            "code": "g9.bogue_mix_gate",
            "note": "ACCEPT accumulator wins: Bogue C3S in-band overpowers the panic-dump advocate",
            "populations": [
                gate_pop("bogue_c3s_evidence", 50, 1.4, 50.0, w_s),
                gate_pop("panic_dump_advocate", 40, 0.8, 50.0, w_s),
                gate_pop("band_tripwire", 80, 1.1, 25.0, w_s),
                gate_pop("accept_accumulator", 64, 1.7, 62.5, w_s),
            ],
        },
        "gate_compute": {
            "per_check": [
                {
                    "check": "g9.bogue_c3s_scorer",
                    "neurons": 50,
                    "mean_rate_hz": 50.0,
                    "window_ms": 44.0,
                    "window_s": 0.044,
                    "spikes": 110,
                },
                {
                    "check": "g9.wet_belt_join",
                    "neurons": 80,
                    "mean_rate_hz": 25.0,
                    "window_ms": 40.0,
                    "window_s": 0.04,
                    "spikes": 80,
                },
            ],
            "total_spikes": 190,
            "total_energy_pJ": 4370,
            "total_energy_uJ": 0.00437,
            "model": "spikes = round(neurons * mean_rate_hz * window_s); 23 pJ/spike",
        },
        "meta": meta_common(
            id="nelb-r15-048",
            clock_domain="rm-pgnaa-sim-relative-ms-t0-2026-06-19T02:40:00Z",
            tags=["pgnaa-kiln", "serialized-bogue", "ACCEPT", "ACCEPT", "simulated", "operational-t2"],
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
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        gc = rec["gate_compute"]
        check_spikes = sum(c["spikes"] for c in gc["per_check"])
        if gc["total_spikes"] != check_spikes:
            raise RuntimeError("gate_compute total_spikes")
        if abs(gc["total_energy_pJ"] - check_spikes * 23) > 1e-6:
            raise RuntimeError("gate_compute energy pJ")
        if abs(gc["total_energy_uJ"] - check_spikes * 23e-6) > 1e-9:
            raise RuntimeError("gate_compute energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau_e pair")
        dw = rec["gate_snn"]
        if abs(dw["decision_window_ms"] / 1000.0 - dw["decision_window_s"]) > 1e-9:
            raise RuntimeError("decision window pair")
        for pop in dw["populations"]:
            if "mean_rate_hz" in pop or "spikes" in pop:
                exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw["decision_window_s"]))
                if pop["spikes"] != exp_p:
                    raise RuntimeError(f"gate_snn pop {pop['name']} budget")
        for tkey, tval in lv.items():
            if not isinstance(tval, dict) or "reward_components" not in tval:
                continue
            rc = tval["reward_components"]
            s = 0.0
            for k, v in rc.items():
                if k in {"aggregation", "rounding_decimals", "notes", "total"}:
                    continue
                if isinstance(v, (int, float)):
                    s += v
            if abs(s - rc["total"]) > 1e-12:
                raise RuntimeError(f"reward {tval['id']} {s} != {rc['total']}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids))


def write_notes(records, lines):
    rows = []
    decisions = []
    for rec in records:
        lv = rec["language_view"]
        t1 = lv["trajectory"]
        t2 = next(v for k, v in lv.items() if k.startswith("trajectory_"))
        d1 = t1["safety_decision"]["decision"]
        d2 = t2["safety_decision"]["decision"]
        decisions.extend([d1, d2])
        r1 = t1["reward_components"]["total"]
        r2 = t2["reward_components"]["total"]
        rast = rec["raster"]
        rows.append(
            {
                "id": rec["id"],
                "d1": d1,
                "d2": d2,
                "r1": r1,
                "r2": r2,
                "sim": t1["state"]["sim_or_real"],
                "events": len(rec["spike_events"]),
                "window": rast["window_ms"],
                "neurons": rast["neurons"],
                "rate": rast["mean_rate_hz"],
                "spikes": rast["spikes"],
                "isi": rast["isi_count_identity"]["isi_total"],
                "mod": rast["routing"]["third_factor"]["modulator"],
                "tau": rast["routing"]["third_factor"]["tau_e_s"],
                "bytes": len(json.dumps(rec, ensure_ascii=False, allow_nan=False, separators=(",", ":"))),
            }
        )
    na = decisions.count("ACCEPT")
    nm = decisions.count("MODIFY")
    nr = decisions.count("REJECT")
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 15
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r15.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`.

## Context / de-duplication
Prior corpus read: 2026-08-30 `NOTES-r03.md`/`NOTES-r04.md` plus pair shape from `batch-r04.jsonl`; 2026-08-17-w3 NOTES-r12 family table; staged `/tmp/nelb-r13/NOTES-r13.md` and `/tmp/nelb-r13-holes.md`.

Banned this round: not r13 FBG ice-load / MRI-quench HIL / VRFB EIS (Oxbow + Siltlink); not r04 SNN replay-harness / pharmaceutical cold-chain / stack-gas CEMS. Also avoided 2026-08-30 r01–r03 families (axle-counter, CHO bioprocess, muon tomography, geodetic survey, RF spectrum, e-nose VOD, fish-passage PIT, water-distribution hydraulics, LPBF melt-pool) and the r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes sketches (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam) were not restaged.

r13 Oxbow VRFB-4 already closed three-party-including-infra-owner on Siltlink. This round does a **NEW** three-party on a different plant and harvests r13 leftovers 1 (ACCEPT-heavy leads), 2 (vendor-only SoT refusal), and 4 (slow recovery floor in-stream).

## Round 15 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r15-046 | SAW wireless torque (Quillband interrogator, Varn-Drive DC-link, Hogget-X thickness, roll-shop micrometer, serialized T=k_t·I_dc·G) | Marrowfen Strip Keld tandem F-6, coil C-8841: vendor-only torque SoT; Croy + Hark + Quillband hide a 28 s overload that yielded the work-roll | REJECT (+0.42) / MODIFY (+0.34) | NEW three-party including the infra owner (not Oxbow/Siltlink): Quillband write-ACL then silent SAW 12.4 kNm while drive reconstructs 22.00 kNm and X-ray buckles 0.18 mm; vendor-only SoT leftover of 042 — no independent torque meter exists; companion t2 is operational speed-drop plus roll change |
| nelb-r15-047 | cavity-ring-down HF grid (CRDS C-7, Gorse-UV DOAS, Pell-HF EC, serialized water-shift) | Stagfen ALK-3 HIL chamber: C-7 raw 1.80 ppm with window H2O 4.4 percent; DOAS 0.04 / EC 0.02 | ACCEPT (+0.38) / MODIFY (+0.31) | first earned ACCEPT on a lead this window; HF_true = 1.80 − 0.45·(4.4−0.8) = 0.18; conjunctive SOP forbids unit ESD on a lone wet cell; 12-minute purge floor is in the stream; companion t2 isolates C-7 only |
| nelb-r15-048 | PGNAA kiln-feed oxides (NaI belt head, serialized Bogue C3S, wet-belt scale bias) | Rookmere Works kiln G-9 (simulated): C3S 60.00 percent in 52–62 while the belt scale looks CaO-low | ACCEPT (+0.41) / ACCEPT (+0.36) | second earned ACCEPT on a lead; 4 percent limestone dump refused; companion t2 is a bounded 0.4 percent trim (predicted C3S 61.60 still in band), not a governance vote |

Decision spread: REJECT / MODIFY / ACCEPT / MODIFY / ACCEPT / ACCEPT — **3A / 2M / 1R**. Two ACCEPTs sit on leads (047, 048). Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r15-046`…`048` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact. Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions REJECT/ACCEPT/ACCEPT matching each lead; 046 carries the zero-weight unreachable `vendor_saw_admissible` population (asymmetric-null on the infra-owned channel). `gate_compute.per_check` windows 28–44 ms, budgets exact (160+128 / 140+80 / 110+80). Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix).

## Self-critique

### Edge cases added vs still thin
- **Added:** first SAW wireless-torque family; first CRDS HF-grid family; first PGNAA kiln-feed family; NEW three-party collusion including the infra owner on a mill (not Oxbow VRFB / Siltlink); first vendor-only SoT refusal where no independent torque meter exists (harder leftover of 042); first ACCEPT-heavy round-level distribution this window (3A/2M/1R with two ACCEPTs on leads); 047 serializes the 12-minute purge floor into the stream; three serialized reconstruction models (drive torque, CRDS water-shift, Bogue C3S) each with an exact worked example; operational t2 on all three companions.
- **Still thin:** (i) 046 still discovers the yield via product/drive witnesses that already existed — a mill whose drive current is also on the vendor bus, so the gate must refuse with *only* the post-coil shop micrometer, is harder; (ii) 047 water-shift is linear in H2O and ignores temperature; a T-dependent k_h2o that could hide a true leak inside a wet window is unwritten; (iii) 048 Bogue uses simplified integer coefficients, not the full four-phase Bogue set (C2S/C3A/C4AF omitted); (iv) stream amplitudes remain authored constants (raster draws are the only seeded noise); (v) 046 companion MODIFY stop-to-zero is a small execution edit, not a second physical model.

### Realism of noise / temporal fidelity
- Strong: 046's 22.00 kNm and 047's 0.18 ppm and 048's 60.00/61.60 percent all recompute from the record; 046's teaching object is the *absence* of SAW co-movement with drive current; 047's DOAS/EC never track the raw 1.80 ppm; 048's scale bias is named as water mass, not missing CaO. Raster adaptation and the 2.0/1.2/1.1 ms triplets give each 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap forces heavy thinning (SAW bursts, CRDS 1 Hz, PGNAA 2-minute ticks); (ii) 046 paper micrometer is a crown number, not a serialized page image; (iii) 047 HIL steam-trace is a fixture, not a plant steam-leak reconstruction; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: infra-owner-in-collusion detector on a vendor-only SoT; drive-current torque reconstruction; product-witness buckle join; CRDS water-shift head; conjunctive ESD SOP (lone cell cannot trip); earned-ACCEPT policy with explicit scope plus tripwire; Bogue C3S reconstruction; belt-scale nonsubstitution; operational companions that execute without re-opening the lead call. Agentic value concentrates in three patterns: refuse when the infra owner can write the SoT even if no twin instrument exists, accept when a reconstruction plus independent witnesses bound the risk, and bind those accepts with tripwires and partial execution.

## What round 16 should add (next densification target)
1. **Vendor-bus drive current:** restage the 046 leftover where even I_dc rides the colluding vendor, so the only unwritable witness is the post-coil shop micrometer / next-coil X-ray.
2. **Temperature-dependent CRDS k_h2o** that can hide a true HF leak inside a wet window, forcing DOAS+EC jointly with the reconstruction.
3. **Full Bogue four-phase** (C3S/C2S/C3A/C4AF) with a free-lime vs C3S tension, closing 048's single-phase gap.
4. **Do not restage** VOD-SNN replay, pharma cold-chain, stack-gas CEMS, FBG glaze, Frostlip quench, Oxbow VRFB-4/Siltlink, Marrowfen F-6 SAW, Stagfen CRDS C-7, or Rookmere PGNAA G-9.

## Verification
`batch-r15.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), ~{rows[0]['bytes']/1024:.1f}/{rows[1]['bytes']/1024:.1f}/{rows[2]['bytes']/1024:.1f} KB. Staged at `/tmp/nelb-r15/` only. Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.42/+0.34/+0.38/+0.31/+0.41/+0.36); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=15`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights.intended_use=research_only` with RM-793 status_basis; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20260946/20260947/20260948, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the whole committed factory and versus staged r13. The three-party is a new plant (SAW mill, not VRFB). Vendor-only SoT refusal, ACCEPT-heavy leads, and in-stream slow-recovery floor are firsts relative to r13. Against that: custody freeze, unwritable-witness, operational-t2, serialized reconstruction, conjunctive SOP, and process-vs-cost reward splits are carried vocabulary; the 5–40 cap is a density constraint; 16+ prior rounds already taught custody/governance. Net: a bit under half the round's scenario/edge mass is genuinely novel.

Novel coverage: 42%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def main():
    records = [rec_046(), rec_047(), rec_048()]
    local_checks(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False, allow_nan=False, separators=(",", ":")) for r in records]
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
    write_notes(records, lines)


if __name__ == "__main__":
    main()
