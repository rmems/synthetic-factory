#!/usr/bin/env python3
"""Generate NELB round-26 research-only bridge pairs (do not write outputs/raw/)."""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

OUT_DIR = Path("/tmp/nelb-r26")
BATCH = OUT_DIR / "batch-r26.jsonl"
NOTES = OUT_DIR / "NOTES-r26.md"
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
RIGHTS_KEYS = (
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
)
assert len(RIGHTS) == 15
assert tuple(RIGHTS.keys()) == RIGHTS_KEYS

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
        "round": 26,
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
            raise RuntimeError("non-strict t_rel_ms")
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
# Record 079 — SPR free-cyanide, designed, MODIFY / ACCEPT
# ---------------------------------------------------------------------------
def rec_079():
    k_theta = 0.012
    k_c = 2000.0
    dth = 0.50
    dn = k_theta * dth  # 0.00600
    cn = k_c * dn  # 12.00
    raster = make_raster(
        neurons=20,
        mean_rate_hz=50.0,
        window_ms=32.0,
        seed=20260979,
        source="px8.spr.kretschmann",
        target="pyrefen.cn_discharge_core",
        table=[
            {"from": "spr_dtheta", "to": "cn_estimator", "weight": 1.40},
            {"from": "spr_snr", "to": "angular_lock_core", "weight": 1.15},
            {"from": "ise_cn", "to": "detox_skip_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "na.cn_line_salience",
            "tau_e_s": 1.6,
            "tau_e_ms": 1600.0,
            "eligibility": "pre-post coincidence on cyanide-SPR synapses; the angular modulator enables potentiation only while dtheta and SNR are co-active inside tau_e so a sulfide-poisoned ISE corridor cannot hide a 12 ppm pregnant-liquor discharge",
        },
        channel_prefix="spr.n",
        anchor="Pyrefen PX-8 SPR 32 ms frame at dtheta 0.50 deg (t_s 1560) where reconstructed CN first clears the 8.00 ppm hold tripwire",
    )
    w_s = 0.032
    events = [
        ev(0.0, "ise.CN", 4.0, code="ISE_PPM", units="ppm", note="vendor ISE still 4.0; sulfide-poisoned denial channel"),
        ev(120000.0, "spr.dth", 0.12, code="DTHETA", units="deg", note="Kretschmann 670 nm SPR; not QCM-D mass, not e-nose MOX"),
        ev(240000.0, "spr.dn", 0.00144, code="DN_RIU", units="RIU", note="0.012*0.12=0.00144"),
        ev(360000.0, "recon.cn", 2.88, code="CN_PPM", units="ppm", note="2000*0.00144=2.88"),
        ev(480000.0, "ccd.flow", 180.0, code="CCD_M3H", units="m3_h"),
        ev(600000.0, "ise.CN", 4.0, code="ISE_PPM", units="ppm", note="ISE never left the 4 ppm corridor"),
        ev(720000.0, "spr.dth", 0.24, code="DTHETA", units="deg"),
        ev(840000.0, "recon.cn", 5.76, code="CN_PPM", units="ppm", note="2000*0.012*0.24=5.76"),
        ev(960000.0, "spr.snr", 14.0, code="SPR_SNR", units="1"),
        ev(1080000.0, "h2s.ppm", 18.0, code="H2S_PPM", units="ppm", note="sulfide that poisons the ISE; SPR gold film is not an ISE"),
        ev(1200000.0, "spr.dth", 0.36, code="DTHETA", units="deg"),
        ev(1320000.0, "recon.cn", 8.64, code="CN_PPM", units="ppm", note="2000*0.012*0.36=8.64; over 8.00 hold"),
        ev(1440000.0, "ise.CN", 4.1, code="ISE_PPM", units="ppm"),
        ev(1560000.0, "spr.dth", 0.50, code="DTHETA_TRIP", units="deg", note="0.50 deg; raster sidecar is this 32 ms frame"),
        ev(1560001.2, "spr.echo", 1.10, code="SPR_BURST", units="norm", note="angular lock burst; amplitude before adaptation"),
        ev(1560002.4, "spr.echo", 0.90, code="SPR_BURST", units="norm", note="same-channel refractory 1.2 ms; adapted 0.82x plus noise"),
        ev(1560003.6, "spr.echo", 0.74, code="SPR_BURST", units="norm", note="third echo; adapted"),
        ev(1680000.0, "spr.dn", 0.00600, code="DN_RIU", units="RIU", note="0.012*0.50=0.00600 exact"),
        ev(1800000.0, "recon.cn", 12.00, code="CN_PPM", units="ppm", note="2000*0.00600=12.00 exact; tripwire 8.00, isolate 25.00"),
        ev(1920000.0, "spr.snr", 18.0, code="SPR_SNR", units="1", note="18.0 >= 12.0 lock floor"),
        ev(2040000.0, "ops.prop", 1.0, code="SKIP_DETOX", units="bool", note="night leach lead Wren Callow: ISE 4.0, skip H2O2, discharge CCD"),
        ev(2160000.0, "gate.spr", 1.0, code="MODIFY", units="decision"),
        ev(2280000.0, "h2o2.cmd", 1.0, code="H2O2_ARM", units="bool"),
        ev(2400000.0, "hold.ccd", 1.0, code="HOLD", units="bool"),
        ev(3600000.0, "h2o2.start", 1.0, code="H2O2_START", units="bool"),
        ev(4800000.0, "h2o2.floor", 20.0, code="CONTACT_MIN", units="min", note="20.0 min H2O2 contact floor is in the stream"),
        ev(4920000.0, "h2o2.rate", 1.20, code="H2O2_KGH", units="kg_h", note="1.20 kg/h inside 1.00-1.40 envelope"),
        ev(5040000.0, "gate.exec", 1.0, code="ACCEPT", units="decision", note="companion t2: hold plus H2O2 executed"),
        ev(5160000.0, "ise.CN", 4.0, code="ISE_PPM", units="ppm", note="ISE still poisoned; not a discharge license"),
        ev(5280000.0, "recon.cn", 12.00, code="CN_PPM", units="ppm"),
        ev(5400000.0, "trip.hold", 0.0, code="ISOLATE", units="bool", note="peak 12.00 vs 25.00 isolate floor; isolate not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r26-079-t1",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PX-SPR-2026-0902",
            "domain": "spr_free_cyanide_ccd",
            "setting": "Pyrefen Gold PX-8, CCD overflow HV-17 (invented). Plant-owned Kretschmann SPR (670 nm, gold film, thiocyanate capture) is the free-cyanide SoT. Invented plant; designed liquor campaign. Not QCM-D Sauerbrey mass (r14 KW-6), not e-nose MOX (r02), not CRDS HF (r15), not CHO EWMA/DO lot disposition (r01-a2).",
            "observables_at_decision": {
                "dtheta_deg": 0.50,
                "k_theta": k_theta,
                "dn_riu": dn,
                "k_c": k_c,
                "cn_ppm": cn,
                "spr_snr": 18.0,
                "ise_ppm": 4.0,
            },
            "margin_authority": "PX-8 CCD SOP rev D: if reconstructed CN >= 8.00 ppm AND SPR SNR >= 12.0, detox-skip is forbidden even if the ISE stays inside 3.0-5.0 ppm",
        },
        "proposed_action": {
            "actor": "night leach lead Wren Callow, citing a 4.0 ppm ISE and a quiet detox skid",
            "summary": "skip H2O2 and discharge CCD HV-17; treat the 0.50 deg SPR walk as a bulk-index drift, not free cyanide",
            "basis_claimed": "ISE is 4.0 ppm and the detox skid amp draw is idle, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Discharge of HV-17 is refused, not the CCD circuit. SOP rev D is conjunctive: reconstructed CN is 12.00 ppm (2000*0.012*0.50, serialized) against an 8.00 ppm hold and a 25.00 ppm isolate, and SPR SNR is 18.0 >= 12.0, while an ISE-only head would still see 4.0 ppm on a sulfide-poisoned electrode (H2S 18 ppm in-stream). Ordered: hold CCD overflow, arm H2O2 at 1.20 kg/h, keep the ISE write-ACL frozen on this liquor. A quiet ISE cannot substitute for the SPR reconstruction.",
            "threshold": "cn_ppm>=8.00 AND spr_snr>=12.0 => forbid detox-skip",
            "stated_residuals": "H2O2 contact costs 20 min; isolate is not taken (12.00 vs 25.00); temperature/bulk-index compensation of k_theta is not a discharge condition tonight",
        },
        "executed_action": {
            "summary": "MODIFY at t_s 2160: CCD held; H2O2 armed; ISE not a discharge license",
            "tool": "px8-spr-cn-gate-cli",
            "observation": "ISE still 4.0 ppm; reconstructed 12.00 ppm never moved; H2O2 later 1.20 kg/h over 20 min contact",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early SPR reconstructs 2.88 ppm"},
                {"t_s": 1560.0, "event": "dtheta 0.50 deg; raster frame captured"},
                {"t_s": 1800.0, "event": "reconstructed CN 12.00 ppm vs 8.00 hold"},
                {"t_s": 2160.0, "event": "MODIFY: hold CCD plus H2O2 arm"},
                {"t_s": 5040.0, "event": "companion execution ACCEPT; 20 min contact floor observed"},
            ],
            "observed_effects": [
                "CN reconstruction recomputes from serialized k_theta, dtheta, and k_c at every recon.cn event",
                "ISE never left ~4 ppm, so an ISE-only head would have skipped detox",
                "H2O2 1.20 kg/h ran the hold without converting it into a pond isolate",
            ],
            "surprises": [
                "H2S 18 ppm stayed on the liquor while the ISE corridor never moved; SPR angular lock was the channel the sulfide could not write",
            ],
            "new_state": {
                "hv17": "held on H2O2 contact; not discharged",
                "ise_acl": "frozen on this liquor",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.41,
            [
                ("spr_reconstruction", 0.14),
                ("conjunctive_hold", 0.12),
                ("ise_nonsubstitution", 0.09),
                ("circuit_not_pond_scope", 0.08),
                ("contact_time_cost", -0.02),
            ],
            "scored for refusing detox-skip on a recomputable SPR CN while the ISE looked quiet; contact_time_cost prices the 20 min floor",
        ),
        "meta": meta_common(
            tags=["MODIFY", "spr-cyanide", "serialized-reconstruction", "operational-companion"],
            distillation_note="SPR gate: serialized dtheta-to-CN plus SNR lock beats a sulfide-poisoned ISE; companion t2 is the H2O2/hold execution, not a governance vote",
        ),
    }
    traj2 = {
        "id": "nelb-r26-079-t2",
        "state": {
            "sim_or_real": "designed",
            "episode_id": "PX-SPR-2026-0902-exec",
            "domain": "h2o2_hold_execution",
            "setting": "Same PX-8 after the MODIFY. This companion is the operational H2O2 contact and CCD hold, not a second policy vote.",
            "observables_at_decision": {
                "h2o2_cmd": True,
                "ccd_hold": True,
                "h2o2_kg_h": 1.20,
                "contact_min": 20.0,
            },
        },
        "proposed_action": {
            "actor": "leach cell following the MODIFY",
            "summary": "execute H2O2 at 1.20 kg/h on HV-17 only; keep the CCD circuit, do not isolate the pond",
            "basis_claimed": "MODIFY requirements are fully specified; H2O2 skid is in-envelope",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "The execution envelope is intact: H2O2 1.20 kg/h is inside 1.00-1.40, the 20.0 min contact floor is in the stream, HV-17 is the only held overflow, and isolate was not taken (12.00 vs 25.00). ACCEPT the sequence. Do not discharge on the ISE; do not convert the hold into a pond isolate.",
            "threshold": "h2o2_kg_h in [1.00,1.40] AND contact_min>=20 AND isolate==0",
        },
        "executed_action": {
            "summary": "H2O2 started t_s 3600; 20.0 min floor at t_s 4800; 1.20 kg/h; CCD remains held; ISE not re-licensed",
            "tool": "px8-h2o2-exec",
            "observation": "no pond isolate; detox-skip not re-entered on HV-17",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "H2O2 armed"},
                {"t_s": 3600.0, "event": "H2O2 start"},
                {"t_s": 4800.0, "event": "20.0 min contact floor in-stream"},
                {"t_s": 5040.0, "event": "companion ACCEPT"},
            ],
            "observed_effects": [
                "1.20 kg/h H2O2 confirmed the hold without a second SPR vote",
                "CCD remainder stayed; HV-17 discharge stamp not restored",
            ],
            "new_state": {"hv17_status": "held_on_h2o2", "pond_isolated": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("envelope_respect", 0.12),
                ("contact_floor_in_stream", 0.10),
                ("circuit_scope_held", 0.08),
                ("ise_not_relicensed", 0.06),
                ("skid_time_cost", -0.02),
            ],
            "operational execution gate: the companion does the H2O2 contact rather than re-arguing the SPR call",
        ),
        "meta": meta_common(tags=["ACCEPT", "operational-execution", "h2o2-hold"]),
    }
    return {
        "id": "nelb-r26-079",
        "spike_events": events,
        "language_view": {
            "description": "Kretschmann SPR on Pyrefen CCD overflow HV-17. Angular walk 0.50 deg reconstructs 12.00 ppm free cyanide against an 8.00 ppm hold while the ISE still reads 4.0 ppm. The gate MODIFYs to a CCD hold plus H2O2; a companion execution ACCEPT runs the 20 min contact floor. CN = k_c * k_theta * dtheta is serialized so every recon.cn amplitude recomputes from the angle.",
            "trajectory": traj,
            "trajectory_h2o2_hold_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "spr.dth / spr.echo / spr.dn / spr.snr": "SPR angle, burst, index shift, lock SNR",
                "recon.cn": "serialized free-cyanide ppm; amplitude is the model output",
                "ise.CN / h2s.ppm / ccd.flow": "ISE, sulfide poison, CCD flow; the denial channels that stay healthy or poisoned",
                "ops.prop / gate.spr / gate.exec": "proposal, MODIFY, companion ACCEPT",
                "h2o2.cmd / h2o2.start / h2o2.floor / h2o2.rate / hold.ccd": "execution channels for the operational companion",
                "trip.hold": "isolate not taken",
            },
            "temporal_motifs": [
                "ISE-quiet while SPR-sick: ise.CN 4.0 adjacent to spr.dth 0.50 and recon.cn 12.00",
                "reconstruction as event: recon.cn 12.00 equals 2000*0.012*0.50",
                "MODIFY then operational ACCEPT: gate.spr at 2160 s, gate.exec at 5040 s",
                "adapted SPR triplet at 1.2 ms spacing encodes the hold trip at raster scale",
                "20 min H2O2 contact floor in-stream: h2o2.start 3600 s to h2o2.floor 4800 s",
            ],
            "language_to_spike_mapping": "'ISE looks quiet' = ise.CN 4.0; '12 ppm cyanide' = recon.cn 12.00; 'forbid detox-skip' = gate.spr MODIFY; 'execute the hold' = h2o2.cmd then companion ACCEPT",
            "why_high_value": "New SPR free-cyanide family (not r14 QCM-D Sauerbrey, not r02 e-nose MOX, not r15 CRDS HF, not r01 CHO EWMA). Serializes an angle-to-ppm reconstruction that an ISE-only head cannot see. Companion t2 is operational H2O2 execution, not a governance vote.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20260979,
                    "stream_note": "stream amplitudes are authored constants (deg, RIU, ppm, kg/h) plus spr.echo adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "SPR angular scan is a millidegree trace; stream keeps dtheta, SNR, and three echo samples of ~400 waveform bins",
                "refractory_floors_ms": {
                    "ise.CN": 600000,
                    "spr.dth": 360000,
                    "spr.dn": 1440000,
                    "recon.cn": 480000,
                    "ccd.flow": 60000,
                    "spr.snr": 960000,
                    "h2s.ppm": 60000,
                    "spr.echo": 0.8,
                    "ops.prop": 60000,
                    "gate.spr": 60000,
                    "h2o2.cmd": 60000,
                    "hold.ccd": 60000,
                    "h2o2.start": 60000,
                    "h2o2.floor": 60000,
                    "h2o2.rate": 60000,
                    "gate.exec": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-07-14T03:10:00Z CCD overflow sample",
            },
            "distillation_targets": [
                "serialized SPR cyanide head: cn_ppm = k_c * k_theta * dtheta_deg",
                "conjunctive SOP head: CN AND SNR lock, never ISE substitution",
                "circuit-not-pond scope: hold one overflow, do not isolate the pond",
                "operational companion: execute H2O2 without re-opening the SPR call",
            ],
        },
        "reconstruction_model": {
            "name": "spr_kretschmann_free_cyanide",
            "formula": "cn_ppm = k_c * k_theta * dtheta_deg",
            "parameters": {
                "k_theta": k_theta,
                "k_c": k_c,
                "hold_ppm": 8.00,
                "isolate_ppm": 25.00,
                "snr_floor": 12.0,
            },
            "worked_example": {
                "dtheta_deg": 0.50,
                "dn_riu": dn,
                "cn_ppm": cn,
                "dtheta_early_deg": 0.12,
                "cn_early_ppm": 2.88,
            },
            "check": "0.012*0.50=0.00600; 2000*0.00600=12.00; 2000*0.012*0.12=2.88",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "MODIFY",
            "decision_window_ms": 32.0,
            "decision_window_s": 0.032,
            "code": "px8.spr_cn_gate",
            "note": "MODIFY accumulator wins: SPR angle plus SNR overpower the ISE detox-skip advocate",
            "populations": [
                gate_pop("spr_cn_evidence", 80, 1.4, 50.0, w_s),
                gate_pop("spr_snr_evidence", 64, 1.1, 31.25, w_s),
                gate_pop("ise_skip_advocate", 40, 0.9, 50.0, w_s),
                gate_pop("modify_accumulator", 96, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("px8.dtheta_scorer", 128, 31.25, 32.0),
                gc_check("px8.snr_scorer", 80, 25.0, 32.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r26-079",
            clock_domain="px-spr-campaign-relative-ms-t0-2026-07-14T03:10:00Z",
            tags=["spr-cyanide", "MODIFY", "ACCEPT", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 080 — vibrating-wire viscometer, hil, REJECT / MODIFY
# ---------------------------------------------------------------------------
def rec_080():
    k_eta = 12.50
    rho = 0.960
    p_ms = 4.00
    eta = k_eta * (p_ms**2) * rho  # 192.00
    raster = make_raster(
        neurons=16,
        mean_rate_hz=62.5,
        window_ms=40.0,
        seed=20260980,
        source="pb3.vw.viscometer",
        target="pitchfen.ship_blend_core",
        table=[
            {"from": "vw_period", "to": "eta_estimator", "weight": 1.45},
            {"from": "drive_gain", "to": "asphaltene_advocate", "weight": 1.20},
            {"from": "rot_eta", "to": "ship_advocate", "weight": 0.45},
        ],
        third_factor={
            "modulator": "da.asphaltene_crash",
            "tau_e_s": 1.2,
            "tau_e_ms": 1200.0,
            "eligibility": "pre-post coincidence on viscometer synapses; the period modulator enables potentiation only while drive-gain is co-active inside tau_e so a wall-slip rotational viscometer cannot hide a 192 cP asphaltene crash",
        },
        channel_prefix="vw.n",
        anchor="Pitchfen PB-3 VW 40 ms frame at period 4.00 ms (t_s 1560) where reconstructed eta first clears the 160 cP ship tripwire",
    )
    w_s = 0.040
    events = [
        ev(0.0, "rot.eta", 85.0, code="ROT_CP", units="cP", note="OEM rotational viscometer; wall-slip denial channel"),
        ev(120000.0, "vw.P", 2.00, code="P_MS", units="ms", note="vibrating-wire period; not SAW torque, not clamp-on flow, not LFV"),
        ev(240000.0, "vw.rho", 0.960, code="RHO", units="g_cm3"),
        ev(360000.0, "recon.eta", 48.00, code="ETA_CP", units="cP", note="12.50*2.00^2*0.960=48.00"),
        ev(480000.0, "blend.T", 324.0, code="T_K", units="K"),
        ev(600000.0, "rot.eta", 84.0, code="ROT_CP", units="cP"),
        ev(720000.0, "vw.P", 3.00, code="P_MS", units="ms"),
        ev(840000.0, "recon.eta", 108.00, code="ETA_CP", units="cP", note="12.50*3.00^2*0.960=108.00"),
        ev(960000.0, "vw.gain", 1.20, code="DRIVE_GAIN", units="1"),
        ev(1080000.0, "header.v", 1.40, code="V_MS", units="m_s"),
        ev(1200000.0, "vw.P", 3.50, code="P_MS", units="ms"),
        ev(1320000.0, "recon.eta", 147.00, code="ETA_CP", units="cP", note="12.50*3.50^2*0.960=147.00"),
        ev(1440000.0, "rot.eta", 85.0, code="ROT_CP", units="cP", note="OEM still 85; wall slip"),
        ev(1560000.0, "vw.P", 4.00, code="P_TRIP", units="ms", note="4.00 ms; raster sidecar is this 40 ms frame"),
        ev(1560001.2, "vw.ring", 1.10, code="VW_BURST", units="norm", note="wire ring-down; amplitude before adaptation"),
        ev(1560002.4, "vw.ring", 0.90, code="VW_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(1560003.6, "vw.ring", 0.74, code="VW_BURST", units="norm", note="third ring; adapted"),
        ev(1680000.0, "recon.eta", 192.00, code="ETA_CP", units="cP", note="12.50*4.00^2*0.960=192.00 exact; ship max 150, trip 160"),
        ev(1800000.0, "vw.gain", 1.60, code="DRIVE_GAIN", units="1", note="1.60 >= 1.40 asphaltene-gain floor"),
        ev(1920000.0, "spec.max", 150.0, code="SPEC_CP", units="cP"),
        ev(2040000.0, "ops.prop", 1.0, code="SHIP_BLEND", units="bool", note="blender lead Bram Sedge: OEM 85 cP, stamp the barge"),
        ev(2160000.0, "gate.vw", 1.0, code="REJECT", units="decision"),
        ev(2280000.0, "recyc.cmd", 1.0, code="RECYCLE_T4", units="bool"),
        ev(2400000.0, "ship.block", 1.0, code="BLOCK", units="bool"),
        ev(3600000.0, "recyc.start", 1.0, code="RECYCLE_START", units="bool"),
        ev(6300000.0, "recyc.floor", 45.0, code="SOAK_MIN", units="min", note="45.0 min heat-soak floor is in the stream"),
        ev(6420000.0, "tank.T4", 1.0, code="T4_HELD", units="bool"),
        ev(6540000.0, "gate.exec", 1.0, code="MODIFY", units="decision", note="companion t2: recycle rather than dump-cutter"),
        ev(6660000.0, "rot.eta", 86.0, code="ROT_CP", units="cP"),
        ev(6780000.0, "recon.eta", 192.00, code="ETA_CP", units="cP"),
        ev(6900000.0, "cutter.refused", 1.0, code="NO_DUMP_CUTTER", units="bool", note="dump-cutter would hide viscosity without solving asphaltene"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r26-080-t1",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PB-VW-2026-0902",
            "domain": "vw_viscometer_bitumen",
            "setting": "Pitchfen Blender PB-3, header H-9, 80 t cutter-stock (invented). Plant-owned vibrating-wire viscometer on a hardware-in-the-loop spare loop times the live-header ship stop. Rotveil OEM rotational viscometer is a corridor witness, not the ship SoT. Invented plant. Not SAW wireless torque (r15), not ultrasonic clamp-on custody (r18), not Lorentz-force velocimetry (r19), not ECT holdup (r20/r22).",
            "observables_at_decision": {
                "p_ms": p_ms,
                "rho": rho,
                "k_eta": k_eta,
                "eta_cP": eta,
                "drive_gain": 1.60,
                "rot_cP": 85.0,
                "spec_max_cP": 150.0,
            },
            "margin_authority": "PB-3 ship SOP rev B: if reconstructed eta >= 160 cP AND drive-gain >= 1.40, barge-stamp is forbidden even if the rotational viscometer stays under 100 cP",
        },
        "proposed_action": {
            "actor": "blender lead Bram Sedge, citing an 85 cP OEM viscometer and a quiet header velocity",
            "summary": "stamp the barge on H-9; treat the 4.00 ms wire period as a density-entry error, not an asphaltene crash",
            "basis_claimed": "Rotveil is 85 cP and header velocity is 1.40 m/s, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Ship-stamp of H-9 is refused. SOP rev B is conjunctive: reconstructed eta is 192.00 cP (12.50*4.00^2*0.960, serialized) against a 150 spec and a 160 trip, and drive-gain is 1.60 >= 1.40, while a rotational-only head would still see 85 cP on a wall-slip spindle. The HIL spare loop times the live-header stop; Rotveil cannot clear a barge. Ordered: block ship, recycle to tank T-4, refuse dump-cutter. An OEM viscometer cannot substitute for the wire reconstruction.",
            "threshold": "eta_cP>=160 AND drive_gain>=1.40 => forbid ship-stamp",
            "stated_residuals": "recycle soak costs 45 min; dump-cutter is out of scope (it would hide viscosity); density-from-tube vs assumed 0.960 is not a ship condition tonight",
        },
        "executed_action": {
            "summary": "REJECT at t_s 2160: ship blocked; recycle commanded; dump-cutter refused",
            "tool": "pb3-vw-visc-gate-cli",
            "observation": "Rotveil still 85-86 cP; reconstructed 192.00 cP never moved; T-4 later held through a 45 min soak",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 360.0, "event": "early VW reconstructs 48.00 cP"},
                {"t_s": 1560.0, "event": "period 4.00 ms; raster frame captured"},
                {"t_s": 1680.0, "event": "reconstructed eta 192.00 cP vs 150 spec"},
                {"t_s": 2160.0, "event": "REJECT: block ship plus recycle"},
                {"t_s": 6540.0, "event": "companion execution MODIFY; 45 min soak floor observed"},
            ],
            "observed_effects": [
                "eta reconstruction recomputes from serialized k, P, and rho at every recon.eta event",
                "Rotveil never left ~85 cP, so an OEM-only head would have stamped the barge",
                "HIL spare loop times the live-header stop; the live metal is not independently witnessed on a second wire",
            ],
            "surprises": [
                "header velocity stayed 1.40 m/s; a flow-only head would have missed the asphaltene crash the wire period caught",
            ],
            "new_state": {
                "h9": "ship-blocked pending T-4 soak",
                "barge": "unstamped",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.43,
            [
                ("vw_reconstruction", 0.15),
                ("conjunctive_ship_refuse", 0.12),
                ("rot_nonsubstitution", 0.10),
                ("hil_loop_timing", 0.08),
                ("soak_time_cost", -0.02),
            ],
            "scored for refusing a barge stamp on a recomputable wire viscosity while the OEM viscometer looked quiet",
        ),
        "meta": meta_common(
            tags=["REJECT", "vw-viscometer", "serialized-reconstruction", "hil", "operational-companion"],
            distillation_note="VW gate: serialized P^2 rho viscosity plus drive-gain beats a wall-slip OEM; companion t2 is recycle/soak, not a second ship vote",
        ),
    }
    traj2 = {
        "id": "nelb-r26-080-t2",
        "state": {
            "sim_or_real": "hil",
            "episode_id": "PB-VW-2026-0902-exec",
            "domain": "recycle_heatsoak_execution",
            "setting": "Same PB-3 after the REJECT. This companion is the operational T-4 recycle and 45 min heat-soak, not a dump-cutter and not a second ship vote.",
            "observables_at_decision": {
                "recycle_cmd": True,
                "ship_blocked": True,
                "soak_min": 45.0,
                "dump_cutter": False,
            },
        },
        "proposed_action": {
            "actor": "blend cell following the REJECT",
            "summary": "recycle H-9 into T-4 and soak 45 min; do not dump cutter-stock to hide the viscosity",
            "basis_claimed": "REJECT requirements are fully specified; T-4 is empty and in-envelope",
        },
        "safety_decision": {
            "decision": "MODIFY",
            "rationale": "Freeze-kill of the header is refused; recycle-and-soak is the operational path. The 45.0 min soak floor is in the stream, T-4 is the only receiving tank, ship remains blocked, and dump-cutter stays refused (it would hide the SoT). MODIFY freeze-kill into T-4 soak. Do not restore a barge stamp tonight.",
            "threshold": "soak_min>=45 AND ship_blocked AND dump_cutter==0",
        },
        "executed_action": {
            "summary": "recycle started t_s 3600; 45.0 min floor at t_s 6300; T-4 held; dump-cutter not opened",
            "tool": "pb3-recycle-exec",
            "observation": "no barge stamp; no dump-cutter; freeze-kill not taken",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 2280.0, "event": "recycle commanded"},
                {"t_s": 3600.0, "event": "recycle start"},
                {"t_s": 6300.0, "event": "45.0 min soak floor in-stream"},
                {"t_s": 6540.0, "event": "companion MODIFY"},
            ],
            "observed_effects": [
                "T-4 soak confirmed the REJECT without a second VW vote",
                "dump-cutter stayed closed so the viscosity SoT remained visible",
            ],
            "new_state": {"h9_status": "recycled_T4", "barge_stamped": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.32,
            [
                ("recycle_not_kill", 0.12),
                ("soak_floor_in_stream", 0.10),
                ("cutter_refused", 0.08),
                ("stamp_not_restored", 0.04),
                ("tank_time_cost", -0.02),
            ],
            "operational execution gate: the companion soaks rather than freeze-killing or hiding the viscosity with cutter",
        ),
        "meta": meta_common(tags=["MODIFY", "operational-execution", "recycle-soak", "hil"]),
    }
    return {
        "id": "nelb-r26-080",
        "spike_events": events,
        "language_view": {
            "description": "Vibrating-wire viscometer on Pitchfen header H-9 (HIL spare loop). Period 4.00 ms reconstructs 192.00 cP against a 150 cP ship spec while the OEM rotational viscometer still reads 85 cP. The gate REJECTs the barge stamp; a companion execution MODIFY recycles to T-4 through a 45 min soak and refuses dump-cutter. eta = k * P^2 * rho is serialized so every recon.eta amplitude recomputes from the period.",
            "trajectory": traj,
            "trajectory_recycle_heatsoak_execution": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "vw.P / vw.ring / vw.rho / vw.gain": "wire period, ring-down, density, drive-gain",
                "recon.eta": "serialized viscosity cP; amplitude is the model output",
                "rot.eta / header.v / blend.T": "OEM viscometer, header velocity, temperature; the denial channels that stay healthy",
                "ops.prop / gate.vw / gate.exec": "proposal, REJECT, companion MODIFY",
                "recyc.cmd / recyc.start / recyc.floor / tank.T4 / ship.block / cutter.refused": "execution channels for the operational companion",
                "spec.max": "ship spec",
            },
            "temporal_motifs": [
                "OEM-quiet while wire-sick: rot.eta 85 adjacent to vw.P 4.00 and recon.eta 192.00",
                "reconstruction as event: recon.eta 192.00 equals 12.50*4.00^2*0.960",
                "REJECT then operational MODIFY: gate.vw at 2160 s, gate.exec at 6540 s",
                "adapted wire triplet at 1.2 ms spacing encodes the ship trip at raster scale",
                "45 min soak floor in-stream: recyc.start 3600 s to recyc.floor 6300 s",
            ],
            "language_to_spike_mapping": "'OEM looks quiet' = rot.eta 85; '192 cP crash' = recon.eta 192.00; 'forbid ship' = gate.vw REJECT; 'recycle not dump' = recyc.cmd then companion MODIFY",
            "why_high_value": "New vibrating-wire viscometer family (not r15 SAW torque, not r18 clamp-on transit-time, not r19 LFV aluminum, not r20/r22 ECT). Serializes a P^2 rho viscosity that a wall-slip OEM cannot see. Companion t2 is operational recycle/soak, not a governance vote. sim_or_real=hil on a spare loop.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20260980,
                    "stream_note": "stream amplitudes are authored constants (ms, cP, gain) plus vw.ring adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "VW kHz carrier kept as envelope period; stream keeps P, gain, and three ring samples",
                "refractory_floors_ms": {
                    "rot.eta": 600000,
                    "vw.P": 360000,
                    "vw.rho": 60000,
                    "recon.eta": 480000,
                    "blend.T": 60000,
                    "vw.gain": 840000,
                    "header.v": 60000,
                    "vw.ring": 0.8,
                    "spec.max": 60000,
                    "ops.prop": 60000,
                    "gate.vw": 60000,
                    "recyc.cmd": 60000,
                    "ship.block": 60000,
                    "recyc.start": 60000,
                    "recyc.floor": 60000,
                    "tank.T4": 60000,
                    "gate.exec": 60000,
                    "cutter.refused": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-06-22T19:40:00Z HIL spare-loop ship window",
            },
            "distillation_targets": [
                "serialized VW viscosity head: eta_cP = k_eta * P_ms^2 * rho",
                "conjunctive SOP head: eta AND drive-gain, never rotational-viscometer substitution",
                "HIL spare times live-header stop",
                "operational companion: recycle/soak rather than freeze-kill or dump-cutter",
            ],
        },
        "reconstruction_model": {
            "name": "vibrating_wire_viscosity",
            "formula": "eta_cP = k_eta * P_ms**2 * rho",
            "parameters": {
                "k_eta": k_eta,
                "rho": rho,
                "spec_max_cP": 150.0,
                "trip_cP": 160.0,
                "gain_floor": 1.40,
            },
            "worked_example": {
                "p_ms": p_ms,
                "eta_cP": eta,
                "p_early_ms": 2.00,
                "eta_early_cP": 48.00,
            },
            "check": "12.50*4.00^2*0.960=192.00; 12.50*2.00^2*0.960=48.00; 12.50*3.50^2*0.960=147.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "REJECT",
            "decision_window_ms": 40.0,
            "decision_window_s": 0.040,
            "code": "pb3.vw_eta_gate",
            "note": "REJECT accumulator wins: wire period plus drive-gain overpower the OEM ship advocate",
            "populations": [
                gate_pop("vw_eta_evidence", 80, 1.5, 50.0, w_s),
                gate_pop("drive_gain_evidence", 64, 1.2, 50.0, w_s),
                gate_pop("rot_ship_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("reject_accumulator", 80, 1.6, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("pb3.period_scorer", 160, 25.0, 40.0),
                gc_check("pb3.gain_scorer", 80, 25.0, 40.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r26-080",
            clock_domain="pb-vw-hil-relative-ms-t0-2026-06-22T19:40:00Z",
            tags=["vw-viscometer", "REJECT", "MODIFY", "hil", "serialized-reconstruction", "operational-t2"],
        ),
    }


# ---------------------------------------------------------------------------
# Record 081 — microwave cavity moisture, simulated, ACCEPT / REJECT
# ---------------------------------------------------------------------------
def rec_081():
    k_f = 500.0
    f0 = 2450.0
    f = 2391.20
    df = f0 - f  # 58.80
    moist = k_f * df / f0  # 12.00
    raster = make_raster(
        neurons=25,
        mean_rate_hz=50.0,
        window_ms=28.0,
        seed=20260981,
        source="bk6.mw.cavity",
        target="brinekiln.floor_release_core",
        table=[
            {"from": "cavity_df", "to": "moisture_estimator", "weight": 1.35},
            {"from": "cavity_q", "to": "wet_load_advocate", "weight": 1.10},
            {"from": "nir_m", "to": "water_dump_advocate", "weight": 0.50},
        ],
        third_factor={
            "modulator": "ach.moisture_conflict",
            "tau_e_s": 2.0,
            "tau_e_ms": 2000.0,
            "eligibility": "pre-post coincidence on kiln-moisture synapses; the cavity modulator enables potentiation only while Q-drop is co-active inside tau_e so a surface-dry NIR crust cannot hide a 12 wt% floor",
        },
        channel_prefix="mw.n",
        anchor="Brinekiln BK-6 MW 28 ms frame at f 2391.20 MHz (t_s 6000) where reconstructed moisture first clears the 10.00 wt% hold-this-floor tripwire",
    )
    w_s = 0.028
    events = [
        ev(0.0, "nir.M", 4.80, code="NIR_WT", units="wt_pct", note="vendor NIR surface crust; denial channel"),
        ev(600000.0, "mw.f0", 2450.0, code="F0_MHZ", units="MHz", note="empty-cavity lock; not PGNAA oxides, not hyperspectral canopy, not TDLAS"),
        ev(1200000.0, "mw.f", 2430.40, code="F_MHZ", units="MHz", note="df 19.60 MHz"),
        ev(1800000.0, "recon.M", 4.00, code="M_WT", units="wt_pct", note="500*19.60/2450=4.00"),
        ev(2400000.0, "kiln.T", 68.0, code="T_C", units="C"),
        ev(3000000.0, "nir.M", 4.70, code="NIR_WT", units="wt_pct"),
        ev(3600000.0, "mw.f", 2410.80, code="F_MHZ", units="MHz", note="df 39.20 MHz"),
        ev(4200000.0, "recon.M", 8.00, code="M_WT", units="wt_pct", note="500*39.20/2450=8.00"),
        ev(4800000.0, "mw.Q", 2800.0, code="Q", units="1"),
        ev(5400000.0, "floor.id", 2.0, code="FLOOR_F2", units="1"),
        ev(6000000.0, "mw.f", 2391.20, code="F_TRIP", units="MHz", note="2391.20 MHz; raster sidecar is this 28 ms frame"),
        ev(6000001.2, "mw.ring", 1.10, code="MW_BURST", units="norm", note="cavity ring; amplitude before adaptation"),
        ev(6000002.4, "mw.ring", 0.90, code="MW_BURST", units="norm", note="same-channel refractory 1.2 ms"),
        ev(6000003.6, "mw.ring", 0.74, code="MW_BURST", units="norm", note="third ring; adapted"),
        ev(6600000.0, "recon.M", 12.00, code="M_WT", units="wt_pct", note="500*58.80/2450=12.00 exact; hold 10.00, isolate 16.00"),
        ev(7200000.0, "mw.Q", 1200.0, code="Q", units="1", note="1200 <= 1800 wet-Q floor"),
        ev(7800000.0, "nir.M", 4.80, code="NIR_WT", units="wt_pct", note="NIR still 4.8; surface dry"),
        ev(8400000.0, "ops.prop", 1.0, code="DUMP_WATER_ALL", units="bool", note="kiln lead Tansy Holt: NIR 4.8, dump water on all seven floors"),
        ev(9000000.0, "gate.mw", 1.0, code="ACCEPT", units="decision", note="bounded ACCEPT: this floor this kiln; water dump refused"),
        ev(9600000.0, "water.block", 1.0, code="NO_DUMP", units="bool"),
        ev(10800000.0, "rest.start", 1.0, code="REST_START", units="bool"),
        ev(39600000.0, "rest.floor", 8.0, code="REST_H", units="h", note="8.0 h rest floor is in the stream"),
        ev(40200000.0, "kiln.T", 66.0, code="T_C", units="C"),
        ev(40800000.0, "gate.exec", 1.0, code="REJECT", units="decision", note="companion t2: refuse NIR water dump of remaining 6 floors"),
        ev(41400000.0, "floors.held", 6.0, code="FLOORS_HELD", units="1"),
        ev(42000000.0, "nir.M", 4.90, code="NIR_WT", units="wt_pct"),
        ev(42600000.0, "recon.M", 12.00, code="M_WT", units="wt_pct"),
        ev(43200000.0, "trip.hold", 0.0, code="ISOLATE", units="bool", note="peak 12.00 vs 16.00 isolate; isolate not taken"),
    ]
    assert_stream(events)

    traj = {
        "id": "nelb-r26-081-t1",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BK-MW-2026-0902",
            "domain": "mw_cavity_malt_moisture",
            "setting": "Brinekiln Malt BK-6, floor F-2 (invented). Simulated sealed cup of a 12 m kiln floor. Plant-owned TM010 microwave cavity (2.45 GHz) is the bulk-moisture SoT. Grainveil NIR is a surface corridor, not a dump license. Invented plant. Not PGNAA kiln oxides (r15 G-9), not gantry hyperspectral pigment (r16 CL-3), not TDLAS NH3 (r22), not QEPAS (r19).",
            "observables_at_decision": {
                "f0_MHz": f0,
                "f_MHz": f,
                "df_MHz": df,
                "k_f": k_f,
                "moisture_wt": moist,
                "q": 1200.0,
                "nir_wt": 4.80,
            },
            "margin_authority": "BK-6 floor SOP rev A: if reconstructed moisture >= 10.00 wt% AND Q <= 1800, water-dump is forbidden even if NIR stays under 5.0 wt%; isolate only if moisture >= 16.00. ACCEPT of a rest is scoped to the measured floor.",
        },
        "proposed_action": {
            "actor": "kiln lead Tansy Holt, citing a 4.8 wt% NIR crust and a falling kiln temperature",
            "summary": "dump water on all seven floors; treat the 58.80 MHz cavity pull as a packing-factor drift, not bulk moisture",
            "basis_claimed": "NIR is 4.8 wt% and kiln T is 68 C, both inside housekeeping limits",
        },
        "safety_decision": {
            "decision": "ACCEPT",
            "rationale": "Rest of floor F-2 is accepted, not a kiln-wide water dump. SOP rev A is conjunctive: reconstructed moisture is 12.00 wt% (500*58.80/2450, serialized) against a 10.00 hold and a 16.00 isolate, and Q is 1200 <= 1800, while a NIR-only head would still see 4.8 wt% on a surface crust. Ordered: rest F-2 this kiln this floor, block water dump, hold the other six floors to their own cavity reads. A dry NIR cannot substitute for the cavity reconstruction. Isolate is not taken (12.00 vs 16.00).",
            "threshold": "moisture_wt>=10.00 AND Q<=1800 => forbid water-dump; ACCEPT rest scoped to F-2",
            "stated_residuals": "8.0 h rest floor is in the stream; remaining six floors are not licensed by this ACCEPT; packing-factor compensation of k_f is not a dump condition tonight",
        },
        "executed_action": {
            "summary": "ACCEPT at t_s 9000: F-2 rest; water dump blocked; other floors not licensed",
            "tool": "bk6-mw-moist-gate-cli",
            "observation": "NIR still 4.8-4.9 wt%; reconstructed 12.00 wt% never moved; 8.0 h rest later observed",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 1800.0, "event": "early cavity reconstructs 4.00 wt%"},
                {"t_s": 6000.0, "event": "f 2391.20 MHz; raster frame captured"},
                {"t_s": 6600.0, "event": "reconstructed moisture 12.00 wt% vs 10.00 hold"},
                {"t_s": 9000.0, "event": "ACCEPT: rest F-2; water dump blocked"},
                {"t_s": 40800.0, "event": "companion execution REJECT of remaining-floor dump; 8 h rest floor observed"},
            ],
            "observed_effects": [
                "moisture reconstruction recomputes from serialized k_f, f0, and f at every recon.M event",
                "NIR never left ~4.8 wt%, so a surface-only head would have dumped water",
                "ACCEPT residual is event-decodable: floor.id=2, floors.held=6, water.block=1",
            ],
            "surprises": [
                "kiln T stayed 66-68 C; a temperature-only head would have missed the bulk water the cavity pull caught",
            ],
            "new_state": {
                "f2": "resting; not water-dumped",
                "other_floors": "unlicensed by this ACCEPT",
                "reconstruction_model": "discharged as an on-record calculator, not a referenced envelope",
            },
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.39,
            [
                ("cavity_reconstruction", 0.14),
                ("bounded_floor_accept", 0.12),
                ("nir_nonsubstitution", 0.09),
                ("dump_blocked", 0.06),
                ("rest_time_cost", -0.02),
            ],
            "scored for an earned bounded ACCEPT of a rest on a recomputable cavity moisture while NIR looked dry; rest_time_cost prices the 8 h floor",
        ),
        "meta": meta_common(
            tags=["ACCEPT", "mw-cavity-moisture", "serialized-reconstruction", "simulated", "operational-companion"],
            distillation_note="MW cavity gate: serialized df-to-moisture plus Q-drop beats a dry NIR crust; companion t2 refuses a remaining-floor dump",
        ),
    }
    traj2 = {
        "id": "nelb-r26-081-t2",
        "state": {
            "sim_or_real": "simulated",
            "episode_id": "BK-MW-2026-0902-exec",
            "domain": "nir_dump_refusal",
            "setting": "Same BK-6 after the bounded ACCEPT. This companion is the operational refusal of a Grainveil NIR water dump of the remaining six floors, not a second moisture vote.",
            "observables_at_decision": {
                "water_blocked_f2": True,
                "floors_held": 6,
                "nir_wt": 4.90,
                "rest_h": 8.0,
            },
        },
        "proposed_action": {
            "actor": "kiln cell following the ACCEPT, citing Grainveil 4.90 wt% on the other floors",
            "summary": "dump water on the remaining six floors because NIR is dry and F-2 already has its rest",
            "basis_claimed": "ACCEPT scoped F-2; Grainveil is the only moisture SoT on floors F-1 and F-3..F-7",
        },
        "safety_decision": {
            "decision": "REJECT",
            "rationale": "Remaining-floor water dump is refused. The lead ACCEPT licensed F-2 only. Floors F-1 and F-3..F-7 have no plant-owned cavity read in this stream; Grainveil is vendor-writable and still a surface crust. Missing independent cavity on those floors is sufficient without a magnitude fight against 4.90 wt%. Ordered: leave the six floors held, do not dump water on a NIR plane. Do not convert the refusal into a kiln isolate.",
            "threshold": "no plant cavity on remaining floors => refuse dump; vendor NIR is not a substitute",
        },
        "executed_action": {
            "summary": "rest started t_s 10800; 8.0 h floor at t_s 39600; six floors held; dump not opened",
            "tool": "bk6-scope-refusal",
            "observation": "no remaining-floor dump; F-2 rest continues; isolate not taken",
        },
        "future_outcome": {
            "timeline": [
                {"t_s": 9600.0, "event": "water dump blocked on F-2"},
                {"t_s": 10800.0, "event": "rest start"},
                {"t_s": 39600.0, "event": "8.0 h rest floor in-stream"},
                {"t_s": 40800.0, "event": "companion REJECT of remaining-floor dump"},
            ],
            "observed_effects": [
                "scope held: F-2 rest did not leak onto six unmeasured floors",
                "vendor NIR 4.90 wt% did not become a dump license",
            ],
            "new_state": {"f2_status": "resting", "other_floors_dumped": False},
            "latency_ms": 15000.0,
        },
        "reward_components": reward(
            0.34,
            [
                ("scope_refusal", 0.12),
                ("rest_floor_in_stream", 0.10),
                ("vendor_nir_nonsubstitution", 0.08),
                ("isolate_not_taken", 0.06),
                ("hold_time_cost", -0.02),
            ],
            "operational execution gate: the companion refuses a remaining-floor dump rather than re-arguing F-2 moisture",
        ),
        "meta": meta_common(tags=["REJECT", "operational-execution", "scope-refusal", "simulated"]),
    }
    return {
        "id": "nelb-r26-081",
        "spike_events": events,
        "language_view": {
            "description": "TM010 microwave cavity on Brinekiln floor F-2 (simulated sealed cup). Cavity pull 58.80 MHz reconstructs 12.00 wt% bulk moisture against a 10.00 hold while NIR still reads 4.8 wt%. The gate ACCEPTs a rest scoped to F-2 and blocks water dump; a companion execution REJECT refuses a vendor-NIR dump of the remaining six floors. moisture = k_f*(f0-f)/f0 is serialized so every recon.M amplitude recomputes from the frequency.",
            "trajectory": traj,
            "trajectory_nir_dump_refusal": traj2,
        },
        "bridge_notes": {
            "channel_map": {
                "mw.f / mw.f0 / mw.ring / mw.Q": "cavity frequency, empty lock, ring, Q",
                "recon.M": "serialized moisture wt%; amplitude is the model output",
                "nir.M / kiln.T / floor.id": "NIR crust, kiln temperature, floor id; the denial and scope channels",
                "ops.prop / gate.mw / gate.exec": "proposal, ACCEPT, companion REJECT",
                "water.block / rest.start / rest.floor / floors.held": "execution channels for the operational companion",
                "trip.hold": "isolate not taken",
            },
            "temporal_motifs": [
                "NIR-dry while cavity-wet: nir.M 4.80 adjacent to mw.f 2391.20 and recon.M 12.00",
                "reconstruction as event: recon.M 12.00 equals 500*58.80/2450",
                "ACCEPT then operational REJECT: gate.mw at 9000 s, gate.exec at 40800 s",
                "adapted cavity triplet at 1.2 ms spacing encodes the hold trip at raster scale",
                "8 h rest floor in-stream: rest.start 10800 s to rest.floor 39600 s",
            ],
            "language_to_spike_mapping": "'NIR looks dry' = nir.M 4.80; '12 wt% bulk' = recon.M 12.00; 'rest this floor' = gate.mw ACCEPT; 'refuse remaining dump' = floors.held then companion REJECT",
            "why_high_value": "New microwave-cavity moisture family (not r15 PGNAA kiln oxides, not r16 hyperspectral canopy, not r22 TDLAS, not r19 QEPAS). Serializes a df-to-moisture reconstruction that a surface NIR cannot see. First earned bounded ACCEPT on a lead this round; companion t2 is operational scope-refusal, not a governance vote. sim_or_real=simulated on a sealed cup.",
            "encoder_spec": {
                "prng": "MT19937 via python random.Random",
                "seeds": {
                    "raster": 20260981,
                    "stream_note": "stream amplitudes are authored constants (MHz, wt%, Q) plus mw.ring adaptation 0.82**k",
                },
                "draw_order": "raster: per neuron id order, gap-constrained times, per-spike adaptation and noise",
                "thinning": "cavity GHz carrier kept as envelope f; stream keeps f, Q, and three ring samples",
                "refractory_floors_ms": {
                    "nir.M": 3000000,
                    "mw.f0": 60000,
                    "mw.f": 2400000,
                    "recon.M": 2400000,
                    "kiln.T": 37800000,
                    "mw.Q": 2400000,
                    "floor.id": 60000,
                    "mw.ring": 0.8,
                    "ops.prop": 60000,
                    "gate.mw": 60000,
                    "water.block": 60000,
                    "rest.start": 60000,
                    "rest.floor": 60000,
                    "gate.exec": 60000,
                    "floors.held": 60000,
                    "trip.hold": 60000,
                },
                "time_alias": "t_rel_ms; t0 = 2026-08-03T11:05:00Z simulated sealed-cup kiln rest",
            },
            "distillation_targets": [
                "serialized MW moisture head: moisture_wt = k_f * (f0 - f) / f0",
                "conjunctive SOP head: moisture AND Q-drop, never NIR substitution",
                "bounded ACCEPT with floor scope plus water-dump out of scope",
                "operational companion: refuse remaining-floor dump without re-opening F-2",
            ],
        },
        "reconstruction_model": {
            "name": "microwave_cavity_perturbation_moisture",
            "formula": "moisture_wt = k_f * (f0_MHz - f_MHz) / f0_MHz",
            "parameters": {
                "k_f": k_f,
                "f0_MHz": f0,
                "hold_wt": 10.00,
                "isolate_wt": 16.00,
                "q_floor": 1800.0,
            },
            "worked_example": {
                "f_MHz": f,
                "df_MHz": df,
                "moisture_wt": moist,
                "f_early_MHz": 2430.40,
                "moisture_early_wt": 4.00,
            },
            "check": "500*58.80/2450=12.00; 500*19.60/2450=4.00; 500*39.20/2450=8.00",
        },
        "raster": raster,
        "gate_snn": {
            "decision": "ACCEPT",
            "decision_window_ms": 28.0,
            "decision_window_s": 0.028,
            "code": "bk6.mw_moist_gate",
            "note": "ACCEPT accumulator wins: cavity df plus Q-drop overpower the NIR dump advocate; scope is F-2 only",
            "populations": [
                gate_pop("mw_moist_evidence", 80, 1.3, 50.0, w_s),
                gate_pop("q_drop_evidence", 64, 1.1, 62.5, w_s),
                gate_pop("nir_dump_advocate", 40, 0.8, 25.0, w_s),
                gate_pop("accept_accumulator", 96, 1.5, 62.5, w_s),
            ],
        },
        "gate_compute": gate_compute(
            [
                gc_check("bk6.df_scorer", 100, 50.0, 28.0),
                gc_check("bk6.q_scorer", 80, 25.0, 28.0),
            ]
        ),
        "meta": meta_common(
            id="nelb-r26-081",
            clock_domain="bk-mw-sim-relative-ms-t0-2026-08-03T11:05:00Z",
            tags=["mw-cavity-moisture", "ACCEPT", "REJECT", "bounded-accept", "serialized-reconstruction", "operational-t2"],
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
    if tuple(RIGHTS.keys()) != RIGHTS_KEYS:
        raise RuntimeError("RM-793 rights key set/order mismatch")
    ids = []
    sims = []
    decisions = []
    for rec in records:
        hits = walk_banned(rec)
        if hits:
            raise RuntimeError(f"banned keys {hits}")
        rights = rec["meta"]["rights"]
        if tuple(rights.keys()) != RIGHTS_KEYS:
            raise RuntimeError(f"{rec['id']} rights keys")
        if len(rights) != 15:
            raise RuntimeError("rights not 15")
        if rights["intended_use"] != "research_only" or rights["linear_issue"] != "RM-793":
            raise RuntimeError(f"{rec['id']} rights values")
        if "RM-793" not in rights["status_basis"]:
            raise RuntimeError("status_basis")
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
        decisions.append(tdec)
        for k, v in lv.items():
            if k.startswith("trajectory_") and isinstance(v, dict) and "safety_decision" in v:
                decisions.append(v["safety_decision"]["decision"])
        rast = rec["raster"]
        exp = int(round(rast["neurons"] * rast["mean_rate_hz"] * rast["window_s"]))
        if abs(rast["spikes"] - exp) > 0:
            raise RuntimeError("raster budget")
        if abs(rast["energy_pJ"] - rast["spikes"] * 23) > 1e-6:
            raise RuntimeError("energy pJ")
        if abs(rast["energy_uJ"] - rast["spikes"] * 23e-6) > 1e-9:
            raise RuntimeError("energy uJ")
        tf = rast["routing"]["third_factor"]
        if abs(tf["tau_e_ms"] / 1000.0 - tf["tau_e_s"]) > 1e-9:
            raise RuntimeError("tau pair")
        isi = rast["isi_count_identity"]
        if isi["isi_total"] != isi["spikes"] - isi["distinct_active_neurons"]:
            raise RuntimeError("isi identity")
        if sum(b["count"] for b in rast["isi_histogram"]) != isi["isi_total"]:
            raise RuntimeError("isi hist sum")
        if not rast["routing"]["table"]:
            raise RuntimeError("empty routing table")
        sim = lv["trajectory"]["state"]["sim_or_real"]
        if sim not in {"designed", "simulated", "hil"}:
            raise RuntimeError(sim)
        sims.append(sim)
        blob = json.dumps(rec)
        if "training_ready" in blob:
            raise RuntimeError("training_ready claimed")
        if '"real"' in blob:
            raise RuntimeError("quoted real token")
        if rec["meta"]["round"] != 26:
            raise RuntimeError("round")
        gc = rec["gate_compute"]
        if gc["total_spikes"] != sum(p["spikes"] for p in gc["per_check"]):
            raise RuntimeError("gate_compute total")
        if gc["total_energy_pJ"] != gc["total_spikes"] * 23:
            raise RuntimeError("gate_compute pJ")
        if abs(gc["total_energy_uJ"] - gc["total_spikes"] * 23e-6) > 1e-12:
            raise RuntimeError("gate_compute uJ")
        dw = rec["gate_snn"]
        if abs(dw["decision_window_ms"] / 1000.0 - dw["decision_window_s"]) > 1e-9:
            raise RuntimeError("decision window pair")
        for pop in dw["populations"]:
            if "mean_rate_hz" in pop or "spikes" in pop:
                exp_p = int(round(pop["neurons"] * pop["mean_rate_hz"] * dw["decision_window_s"]))
                if pop["spikes"] != exp_p:
                    raise RuntimeError(f"gate pop {pop['name']}")
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
        for e in rec["spike_events"]:
            if any(k in e for k in ("t_ms", "burst_id", "sequence_id", "event_order", "causal_group")):
                raise RuntimeError("forbidden event key")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"dup ids {ids}")
    if set(sims) != {"designed", "simulated", "hil"}:
        raise RuntimeError(f"provenance set {sims}")
    if set(decisions) != {"ACCEPT", "MODIFY", "REJECT"}:
        raise RuntimeError(f"decision mix {decisions}")
    print("local_checks ok", [r["id"] for r in records], "ids", len(ids), "sims", sims, "decisions", decisions)


def write_notes(records, lines, gate_lines):
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
    notes = f"""# Neuromorphic Event + Language Bridge — NOTES round 26
Run: 2026-09-02-final-heavy · Factory: neuromorphic-event-language-bridge · Generator: grok-4.6 · Output: `batch-r26.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)
Rights: RM-793 research-only (SpaceXAI/xAI grok-4.6, SuperGrok Heavy chat). Not training_ready. Do not publish into `outputs/raw/` from this generator; operator uses `pipelines/round_txn.py`. Staged only at `/tmp/nelb-r26/`.

## Context / de-duplication
Prior corpus read: 2026-08-17 r1–r12 family table; 2026-08-30 NOTES-r01–r04; staged `/tmp/nelb-r13`…`/tmp/nelb-r24` generators/NOTES (r16 IFOG / transmon / hyperspectral; r17 MEMS accel / muon ore-pass / industrial x-ray; r18 optogenetic stim / 905 nm LiDAR snow / clamp-on transit-time; r19 LIBS / QEPAS / LFV; r20 LDV / THz-TDS / ECT; r21 THz-TDS radome / ECA-FSW / LIBS-C; r22 ECT holdup / TDLAS / LIBS tap; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS porcelain / N-16 transit-time / helium RGA). Pair shape from r13–r20 (`language_view.trajectory` + operational t2 + `spike_events` + `raster` + `gate_snn` + `isi_histogram` + `routing.third_factor` + 15-key RM-793 `meta.rights`).

Banned this round: r13 FBG glaze / MRI-quench / VRFB EIS; r14 BOTDA / QCM-D / MsS T(0,1); r15 SAW torque / CRDS HF / PGNAA; r16 IFOG / transmon readout / hyperspectral crop; r17 MEMS array / muon tomography / industrial x-ray; r18 optogenetic photovoltaic comb / 905 nm LiDAR snow / ultrasonic clamp-on; r19 LIBS Cu-ratio / QEPAS C2H2 / Lorentz-force velocimetry; r20 fiber-LDV Kaplan / THz-TDS coupon / ECT CFB; r21 THz-TDS bondline / ECA-FSW / LIBS carbon; r22 ECT HDPE / TDLAS NH3 / LIBS tap C; r23 lock-in thermography / PAUT-TFM / ECN CUI; r24 RUS insulator / N-16 gamma transit-time / helium RGA; r04 VOD-SNN / pharma cold-chain / CEMS; 2026-08-30 r01–r03 including dry-cask muon, CHO EWMA, and LPBF melt-pool; r1–r12 table (DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, nanopore, VLF, QEC, GW, SOFAR, neutrino, fab OES, space weather, pulsar TOA, eddy covariance, flow cytometry). Unused r13-holes/premises sketches (cyclotron BPM/BLM, Co-60 alanine EPR, ADCP ice-jam, mud-pulse, Barkhausen, Lamb-wave) were not restaged.

Adjacencies declared in-pair then kept physically distinct: 079 SPR is a Kretschmann angular lock on a gold film, not r14 QCM-D dissipation mass and not r01 CHO EWMA/DO lot disposition; 080 vibrating-wire is a period-squared viscosity, not r15 SAW torque, not r18 clamp-on transit-time, not r19 LFV; 081 microwave cavity is a TM010 perturbation moisture, not r15 PGNAA kiln oxides and not r16 hyperspectral pigment.

## Round 26 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-r26-079 | Kretschmann SPR free-cyanide (670 nm gold film; serialized CN=k_c·k_θ·Δθ; ISE sulfide-poison denial) | Pyrefen Gold PX-8 CCD overflow HV-17 (invented): Δθ 0.50 deg reconstructs 12.00 ppm while ISE still reads 4.0 ppm | MODIFY (+0.41) / ACCEPT (+0.34) | serialized `0.012*0.50=0.00600`, `2000*0.00600=12.00`; conjunctive SOP (CN AND SNR) forbids detox-skip; companion t2 is operational H2O2 contact, 20 min floor in-stream |
| nelb-r26-080 | vibrating-wire viscometer of a bitumen header (serialized η=k·P²·ρ; wall-slip OEM rotational denial; HIL spare loop) | Pitchfen Blender PB-3 header H-9 (invented, HIL): P 4.00 ms reconstructs 192.00 cP while Rotveil still reads 85 cP | REJECT (+0.43) / MODIFY (+0.32) | serialized `12.50*4.00^2*0.960=192.00`; conjunctive SOP (η AND drive-gain) forbids barge-stamp; companion t2 MODIFYs freeze-kill into a 45 min T-4 soak and refuses dump-cutter; sim_or_real=hil |
| nelb-r26-081 | microwave cavity perturbation moisture of a malt kiln (serialized M=k_f·(f0−f)/f0; NIR surface-crust denial) | Brinekiln Malt BK-6 floor F-2 (invented, simulated sealed cup): f 2391.20 MHz reconstructs 12.00 wt% while NIR still reads 4.8 wt% | ACCEPT (+0.39) / REJECT (+0.34) | earned bounded ACCEPT on a lead: `500*58.80/2450=12.00`; F-2 rest only, water dump out of scope; 8.0 h rest floor in-stream; companion t2 REJECTS a vendor-NIR dump of the remaining six floors; sim_or_real=simulated |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / ACCEPT / REJECT — **{na}A/{nm}M/{nr}R**. All three enums used, and all three sit on **leads**. Provenance spread: designed / hil / simulated (one each; never real). IDs `nelb-r26-079`…`081` plus t1/t2 suffixes.

## Raster sidecar
Every record carries `raster` + top-level `gate_snn` + `gate_compute`. Windows {rows[0]['window']:.0f}/{rows[1]['window']:.0f}/{rows[2]['window']:.0f} ms; `window_s == window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack ({rows[0]['spikes']}/{rows[1]['spikes']}/{rows[2]['spikes']} at {rows[0]['rate']:.1f}/{rows[1]['rate']:.1f}/{rows[2]['rate']:.1f} Hz over {rows[0]['neurons']}/{rows[1]['neurons']}/{rows[2]['neurons']} neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact. Routing source/target + 3-entry tables + `third_factor` on all three (modulators {rows[0]['mod']} / {rows[1]['mod']} / {rows[2]['mod']}; τe {rows[0]['tau']}/{rows[1]['tau']}/{rows[2]['tau']} s as consistent `tau_e_s`+`tau_e_ms` pairs). Excerpts integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, per-spike amplitude with adaptation (0.82**k) plus noise. ISI histograms from the full window, bins ≥1 ms, counts sum to `spikes − distinct_active_neurons` ({rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}). Same-neuron gaps ≥1100 µs pre-round, ≥1000 µs serialized. `gate_snn` on all three: decisions MODIFY/REJECT/ACCEPT matching each lead. `gate_compute.per_check` windows 28–40 ms, budgets exact. Main streams: {rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']} events (inside the 5–40 cap), strictly increasing `t_rel_ms` only (no `t_ms` mix), same-channel refractory ≥0.8 ms (079 SPR triplet at 1.2 ms, 080 VW ring triplet, 081 cavity ring triplet).

## Self-critique

### Edge cases added vs still thin
- **Added:** first Kretschmann SPR free-cyanide family (not QCM-D, not e-nose, not CHO EWMA); first vibrating-wire viscometer family on bitumen (not SAW, not clamp-on, not LFV); first microwave-cavity moisture family on a malt kiln (not PGNAA oxides, not hyperspectral pigment, not TDLAS); ISE sulfide-poison as a denial channel; wall-slip OEM viscometer as a denial channel; NIR surface crust as a denial channel; earned bounded ACCEPT whose out-of-scope clause is a remaining-floor dump; 20 min / 45 min / 8 h recovery floors in-stream; provenance trio designed/hil/simulated; operational t2 on all three (H2O2 contact, T-4 soak, remaining-floor dump refusal).
- **Still thin:** (i) 079 k_θ is a calibrated constant, not a temperature/bulk-index compensated Fresnel stack — a Δn(T) that could hide 12 ppm inside a 4 ppm ISE corridor is unwritten; (ii) 080 assumes ρ=0.960 rather than a tube-density measurement, so a density-entry error that could fake 192 cP is unwritten; (iii) 081 packing-factor / bulk-density that can fake 12 wt% inside a dry NIR is unwritten; (iv) stream amplitudes remain authored constants (raster draws are the only seeded noise); (v) r04's 90-day poison-class audit close-out, FBG Δλ(T) on a non-TW-17 blade, and the unused r13-premises plants remain untouched; (vi) vendor-only as a lead REJECT with *no* independent witness is still harder than 080 (plant VW exists on the HIL loop) and 081's t2 NIR refusal (the lead already had a plant cavity).

### Realism of noise / temporal fidelity
- Strong: 079's 12.00 ppm recomputes `2000*0.012*0.50`; 080's 192.00 cP recomputes `12.50*16.00*0.960`; 081's 12.00 wt% recomputes `500*58.80/2450`. Raster adaptation (0.82**k plus 4 percent noise) and 1.2 ms triplets give each 5–40 stream a raster-scale motif without violating 0.8 ms same-channel refractory.
- **Gaps, honestly:** (i) 5–40 cap forces heavy thinning (SPR millidegree scan kept as envelope Δθ; VW kHz carrier kept as period; cavity GHz carrier kept as envelope f); (ii) 081's 8 h rest is two bookends plus one kiln-T, not a sampled night of drying; (iii) 080 HIL spare times a live-header stop that the stream does not independently witness on a second live wire; (iv) no gate_snn input→output volley pair at raster resolution this round (r04-a1 already staged that).

### Training value (SNN/LSM + agentic)
Distillation targets: serialized SPR CN=k_c·k_θ·Δθ; conjunctive SNR SOP that a quiet ISE cannot substitute for; serialized VW η=k·P²·ρ; drive-gain asphaltene conjunct; recycle-not-kill after REJECT; serialized MW M=k_f·(f0−f)/f0; Q-drop conjunct; bounded ACCEPT with floor scope + dump out of scope; operational companions that execute or refuse scope without re-opening the physics call. Agentic value concentrates in three patterns: reconstruction-as-SoT on a physical error the raw SCADA/OEM channel cannot see, REJECT that becomes a soak rather than a freeze-kill, and ACCEPT that does not license the unmeasured remainder.

## What round 27 should add (next densification target)
1. **SPR Δn(T) / bulk-index compensation** that can hide 12 ppm CN inside a 4 ppm ISE corridor, closing 079's calibrated-constant gap without restaging PX-8.
2. **VW tube-density** so 080's ρ is measured, not assumed 0.960, and a density-entry error can no longer be the unwritten fake.
3. **Microwave packing-factor** that can fake 12 wt% inside a dry NIR, closing 081's sealed-cup mean.
4. **Do not restage** VOD-SNN replay, pharma cold-chain, stack-gas CEMS, FBG glaze, Frostlip quench, Oxbow VRFB, IFOG, transmon, hyperspectral, MEMS array, muon ore-pass, industrial x-ray, optogenetic stim, 905 nm LiDAR snow, clamp-on transit-time, LIBS, QEPAS, LFV, Mossgill LDV, Thornwick THz, Polderwick ECT, Fernbrake THz-TDS, Tallowfen ECA, Peckholt LIBS-C, Brackfen ECT, Ashrill TDLAS, Forgeholt LIBS tap, lock-in thermography, PAUT-TFM, ECN CUI, RUS porcelain, N-16 transit-time, helium RGA, Pyrefen SPR PX-8, Pitchfen VW PB-3, or Brinekiln MW BK-6. Leave Rift-Caldera mud-pulse, Skarv-Naze Barkhausen, and Orinoco-Span Lamb-wave available.

## Verification
`batch-r26.jsonl`: 3 lines, `json.loads`-clean (allow_nan=False), ~{rows[0]['bytes']/1024:.1f}/{rows[1]['bytes']/1024:.1f}/{rows[2]['bytes']/1024:.1f} KB. Staged at `/tmp/nelb-r26/` only. {gate_lines} Build-time asserts: global strict time order; same-channel ≥0.8 ms; 5–40 events ({rows[0]['events']}/{rows[1]['events']}/{rows[2]['events']}); excerpt integer bounds, neuron bounds, sort, 1 ms per-neuron floor; ISI identity {rows[0]['isi']}/{rows[1]['isi']}/{rows[2]['isi']}; spike budgets exact; energy pJ/µJ exact; reward totals equal two-decimal component sums (+0.41/+0.34/+0.43/+0.32/+0.39/+0.34); gate_snn decisions match lead `safety_decision.decision`; `state.sim_or_real` ∈ {{designed, hil, simulated}}; `meta.round=26`, `meta.factory=neuromorphic-event-language-bridge`, `meta.generator=grok-4.6`, `meta.run_label=2026-09-02-final-heavy`; `meta.rights` 15-key RM-793 stamp, `intended_use=research_only`; no hidden-reasoning keys; no `provenance` objects; no 'real' claims; no `training_ready`; all 9 record/trajectory ids unique. Raster seeds 20260979/20260980/20260981, MT19937.

Honest novelty accounting: 3/3 modality families are new versus the committed factory and versus staged r13–r24. ISE-poison denial, wall-slip OEM denial, and NIR-crust denial are new edges applied to new physics. Against that: conjunctive SOP, operational t2, serialized reconstruction, bounded ACCEPT, and process-vs-cost reward splits are carried vocabulary; the 5–40 cap is a density constraint; 25 prior rounds already taught custody/governance. Net: a bit under two-fifths of the round's scenario/edge mass is genuinely novel.

Novel coverage: 38%
"""
    NOTES.write_text(notes, encoding="utf-8")
    print("wrote", NOTES, "bytes", NOTES.stat().st_size)


def repo_gates(records):
    chunks = []
    from check_records import FactoryStaging, check_jsonl

    errs, warns, kinds, n = check_jsonl(
        BATCH, "batch-r26.jsonl", staging=FactoryStaging(enabled=True)
    )
    chunks.append(
        f"`check_records.check_jsonl` with `FactoryStaging(enabled=True)` → {len(errs)} errors, {len(warns)} warnings, kinds `{kinds}` (n={n})"
    )
    if errs:
        raise RuntimeError(f"check_jsonl errors {errs[:5]}")

    import curate_bridge

    for rec in records:
        st = curate_bridge.raster_status(
            rec, require_raster=True, require_routing_table=True
        )
        if not st["raster_valid"] or not st["gate_snn_valid"] or st["reason_codes"]:
            raise RuntimeError(f"raster_status {rec['id']} {st}")
        if not st["third_factor_present"]:
            raise RuntimeError(f"third_factor missing {rec['id']}")
    chunks.append(
        "`curate_bridge.raster_status(..., require_raster=True, require_routing_table=True)` → raster_valid and gate_snn_valid true, empty reason codes, `third_factor_present` true on all three"
    )

    decisions = curate_bridge.curate_jsonl(
        BATCH, require_raster=True, require_routing_table=True
    )
    reasons = [
        (d.manifest.get("reason_codes") or [None])[0] for d in decisions
    ]
    if any(d.action != "retain" for d in decisions):
        raise RuntimeError(f"curate_jsonl {[d.action for d in decisions]} {reasons}")
    chunks.append(
        f"`curate_jsonl(...)` → {len(decisions)}× retain / `{reasons[0] if reasons else ''}`"
    )

    from verify_execution_shapes import verify_record_execution
    from verify_execution import verify_batch_for_frontier

    for rec in records:
        status, reason = verify_record_execution(rec, rec["id"])
        if status != "verified":
            raise RuntimeError(f"verify_record_execution {rec['id']} {status} {reason}")
    chunks.append("`verify_record_execution` → 3× verified")
    counts, findings, blocked = verify_batch_for_frontier(BATCH, strict=True)
    if blocked or counts.get("failed") or counts.get("inconclusive"):
        raise RuntimeError(f"frontier {counts} {findings}")
    chunks.append(
        f"`verify_batch_for_frontier(strict=True)` → {counts.get('verified')} verified, {counts.get('inconclusive')} inconclusive, {counts.get('failed')} failed, blocked {blocked}"
    )

    import spike_probe

    rasters, problems = spike_probe.load_rasters([str(BATCH)])
    summary = spike_probe.summarize(rasters, problems, [str(BATCH)])
    if problems:
        raise RuntimeError(f"spike_probe {problems}")
    chunks.append(
        f"`python3 pipelines/spike_probe.py --strict {BATCH}` → loaded {len(rasters)}, unloadable 0, problems [], gate_snn_records {summary.get('gate_snn_records')}, third_factor_routes {summary.get('third_factor_routes')}"
    )
    return "; ".join(chunks) + "."


def main():
    if "outputs/raw" in str(BATCH):
        raise RuntimeError("refusing to write outputs/raw")
    records = [rec_079(), rec_080(), rec_081()]
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
    gate_lines = repo_gates(records)
    write_notes(records, lines, gate_lines)


if __name__ == "__main__":
    main()
